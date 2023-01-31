"""
    BRIDGE TOTEM - GESTISCE LA COMUNICAZIONE MQTT TRA TOTEM E SERVER E GESTISCE LA COMUNICAZIONE SERIALE CON IL MICROCONTROLLORE

    1.  RIMANE IN ASCOLTO SUL TOPIC TOTEMS/IDTOTEM, DOVE IL SERVER INDICA IL LIBRO PRENOTATO
        COMUNICA IN SERIALE AL MICROCONTROLLORE CHE BISOGNA ACCENDERE IL LED CORRISPONDENTE
    2.  RIMANE IN ASCOLTO SULLA SERIALE, DOVE IL MICROCONTROLLORE COMUNICA UN AGGIORNAMENTO SULLO STATO DI UN LIBRO
		(CONSEGNATO, RITIRATO...) E INVIA UNA RICHIESTA HTTP AL SERVER PER AGGIORNARE LO STATO SUL DB
"""
import serial
import serial.tools.list_ports
import requests
import configparser
import pathlib
import paho.mqtt.client as paho
from paho import mqtt
import json
import ssl

#INTERO
LIBRO_RITIRATO = 1
LIBRO_RICONSEGNATO = 2
RICHIESTA_UPDATE = 3

#CODICE
LIBRO_PRENOTATO = 1
LIBRO_PRONTO_PER_RITIRO = 2
NUM_SCOMPARTIMENTO = 3

class Bridge():

	def __init__(self):
		self.config_path = pathlib.Path(__file__).parent.absolute() / "config.ini"
		self.config = configparser.ConfigParser()
		self.config.read(self.config_path)
		self.setupTotem()
		self.setupSerial()
		self.setupHTTP()
		self.setupMQTT()
    
	def setupTotem(self):
		self.id = self.config.get("TOTEM","ID")
		self.topic = "TOTEMS/" + self.id
		self.elenco_prenotazioni = dict()

	def setupSerial(self):
		# open serial port
		self.ser = None

		if self.config.get("Serial","UseDescription", fallback=False):
			self.portname = self.config.get("Serial","PortName", fallback="COM4")
		else:
			print("list of available ports: ")
			ports = serial.tools.list_ports.comports()

			for port in ports:
				print (port.device)
				print (port.description)
				if self.config.get("Serial","PortDescription", fallback="arduino").lower() \
						in port.description.lower():
					self.portname = port.device

		try:
			if self.portname is not None:
				print ("connecting to " + self.portname)
				self.ser = serial.Serial(self.portname, 9600, timeout=0)
		except:
			self.ser = None

		# self.ser.open()

		# internal input buffer from serial
		self.inbuffer = []

	def setupMQTT(self):
		self.clientMQTT = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
		MQTT_USER = self.config.get("MQTT", "MQTT_USERNAME")
		MQTT_PWD = self.config.get("MQTT", "MQTT_PASSWORD")
		self.clientMQTT.username_pw_set(MQTT_USER, MQTT_PWD)
		self.clientMQTT.tls_set(tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_NONE)
		self.clientMQTT.on_connect = self.on_connect
		self.clientMQTT.on_message = self.on_message
		print("connecting to MQTT broker...")
		self.clientMQTT.connect(
			self.config.get("MQTT","MQTT_BROKER"),
			self.config.getint("MQTT","Port"),
			60)
		self.clientMQTT.loop_start()

	def setupHTTP(self):
		self.APIURL = self.config.get("SERVER", "URL")

	def on_connect(self, client, userdata, flags, rc, properties=None):
		print("Connected with result code " + str(rc))

		# Subscribing in on_connect() means that if we lose the connection and
		# reconnect then subscriptions will be renewed.
		self.clientMQTT.subscribe(self.topic)


	# The callback for when a PUBLISH message is received from the server.
	# COMUNICAZIONE SERVER->BRIDGE->ARDUINO
	def on_message(self, client, userdata, msg):
		print(msg.topic + " " + str(msg.payload))

		if msg.topic == self.topic:
			#gestisci il messaggio e scrivi sulla seriale
			#In msg c'è IDScompartimento/CODICE/IDPRENOTAZIONE
			msg = msg.payload.decode('utf-8')
			msg = msg.split('/')
			idscompartimento = int(msg[0])
			codice = int(msg[1])
			idprenotazione = int(msg[2])
			self.outSeriale(idscompartimento, codice)

			if codice == NUM_SCOMPARTIMENTO:
				self.elenco_prenotazioni[idscompartimento] = idprenotazione
				self.httpRequest(idprenotazione, idscompartimento, 'consegnato')
		
	def outSeriale(self, idscompartimento, codice):
		"""
		PACCHETTO
		---------
		FF|idscompartimento|codice|FE
		"""
		idscompartimento = idscompartimento.to_bytes(2, 'little')
		codice = codice.to_bytes(1, 'little')
		pacchetto = list()
		pacchetto.append(b'\xff')
		pacchetto.append(idscompartimento[0].to_bytes(1, 'little'))
		pacchetto.append(idscompartimento[1].to_bytes(1, 'little'))
		pacchetto.append(codice)
		pacchetto.append(b'\xfe')
		print("BRIDGE -> ARDUINO")
		print(pacchetto)
		self.ser.write(pacchetto)
	
	def outSerialeUpdate(self, stato_scompartimenti):
		"""
		PACCHETTO
		---------
		FF|statoScomp1|statoScomp2|...|FE
		"""
		pacchetto = list()
		pacchetto.append(b'\xff')
		for stato in stato_scompartimenti:
			pacchetto.append(stato.to_bytes(1, 'little'))
		pacchetto.append(b'\xfe')
		print("BRIDGE -> ARDUINO")
		print(pacchetto)
		self.ser.write(pacchetto)

	def loop(self):
		# infinite loop for serial managing
		# COMUNICAZIONE ARDUINO->BRIDGE
		while (True):
			#look for a byte from serial
			if not self.ser is None:

				if self.ser.in_waiting>0:
					# data available from the serial port
					lastchar=self.ser.read(1)
					self.inbuffer.append(lastchar)

					if lastchar==b'\xfe' and len(self.inbuffer) == 5: #EOL
						print("\nValue received")
						self.useData()
						self.inbuffer = []
					elif lastchar==b'\xfe' and self.inbuffer[0] != b'\xff':
						# append
						self.inbuffer = []

	def useData(self):
		# I have received a packet from the serial port. I can use it
		# split parts
		if self.inbuffer[0] != b'\xff':
			return False
		print(self.inbuffer)
		idscompartimento = int.from_bytes(self.inbuffer[1], byteorder='little')
		idscompartimento += (int.from_bytes(self.inbuffer[2], byteorder='little') << 8)
		intero = int.from_bytes(self.inbuffer[3], byteorder='little')

		if idscompartimento == 0 and intero == RICHIESTA_UPDATE:
			#UPDATE RICHIESTO DALL'ARDUINO
			self.httpRequestUpdate()

		if intero == LIBRO_RICONSEGNATO:
			#risali al codice prenotazione associato e conferma al server il ritiro
			if idscompartimento in self.elenco_prenotazioni:
				idprenotazione = self.elenco_prenotazioni[idscompartimento]

				self.httpRequest(idprenotazione, idscompartimento, 'consegnato')

				del self.elenco_prenotazioni[idscompartimento]
			else:
				print("Codice prenotazione non trovato!")

	#COMUNICAZIONE BRIDGE->SERVER
	def httpRequest(self, idprenotazione, idscompartimento, codice):
		d = {'totem_id': self.id, 'scompartimento_id': idscompartimento, 'stato': codice}
		url = "{}/prenotazioni/{}".format(self.APIURL, idprenotazione)
		print(url)
		r = requests.put(url = url, json = d)
		print(r.text)
	
	def httpRequestUpdate(self):
		url = "{}/totems/{}".format(self.APIURL, self.id)
		r = requests.get(url = url)
		print(r.text)
		r = json.loads(r.text)
		scompartimenti = list()
		for totem in r:
			scompartimenti.append(totem['stato_scompartimento'])

		for i, s in enumerate(scompartimenti):
			if s == 'occupato':
				scompartimenti[i] = 1
			if s == 'prenotato':
				scompartimenti[i] = 2
			if s == 'libero':
				scompartimenti[i] = 3

		self.outSerialeUpdate(scompartimenti)

if __name__ == '__main__':
	br=Bridge()
	br.loop()