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
import paho.mqtt.client as mqtt

RITIRO = 1
RICONSEGNA = 2
CHECKPRENOTAZIONE = 3

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
		self.id = self.config.get("Totem","ID")
		self.topic = "TOTEMS/" + self.id

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
		self.clientMQTT = mqtt.Client()
		self.clientMQTT.on_connect = self.on_connect
		self.clientMQTT.on_message = self.on_message
		print("connecting to MQTT broker...")
		self.clientMQTT.connect(
			self.config.get("MQTT","Server", fallback= "broker.hivemq.com"),
			self.config.getint("MQTT","Port", fallback= 1883),
			60)

		self.clientMQTT.loop_start()

	def setupHTTP(self):
		self._APIURL = "https://www.url.com/prenotazioni/"
		self._APIKEY = "aio_sTtf00jBu12ileE6HCoBl23KZ7MK"
		self._HEADERS = {"X-AIO-Key": self._APIKEY}

	def on_connect(self, client, userdata, flags, rc):
		print("Connected with result code " + str(rc))

		# Subscribing in on_connect() means that if we lose the connection and
		# reconnect then subscriptions will be renewed.
		self.clientMQTT.subscribe(self.topic)


	# The callback for when a PUBLISH message is received from the server.
	# COMUNICAZIONE SERVER->BRIDGE->ARDUINO
	def on_message(self, client, userdata, msg):
		print(msg.topic + " " + str(msg.payload))
		if msg.topic==self.topic:
			#gestisci il messaggio e scrivi sulla seriale
			#In msg c'è IDScompartimento
			self.outSeriale(4, int(msg))

	def outSeriale(self, nbytes, val):
		"""
		Params:
		-------
		nbytes: numero di bytes da inviare (intero)
		val: intero da inviare

		Output:
		-------
		Costruisce un pacchetto ff|nbytes|byte1|byte2|...|fe e lo manda sulla seriale
		"""
		val = val.to_bytes(nbytes, 'little')
		nbytes = nbytes.to_bytes(1, 'little')
		pacchetto = bytearray(b'\xff'+nbytes+val+b'\xfe')
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

					if lastchar==b'\xfe': #EOL
						print("\nValue received")
						self.useData()
						self.inbuffer = []
					else:
						# append
						self.inbuffer.append(lastchar)

	def useData(self):
		# I have received a packet from the serial port. I can use it
		if len(self.inbuffer)<3:   # at least header, size, footer
			return False
		# split parts
		if self.inbuffer[0] != b'\xff':
			return False

		numval = int.from_bytes(self.inbuffer[1], byteorder='little')	#NUMERO CAMPI
	
		strval = ""
		for i in range (numval):
			val = int.from_bytes(self.inbuffer[i+2], byteorder='little')
			strval += "%d" % (val)
			if i < numval - 1:
				strval += "/"
			#print(strval)
			#self.clientMQTT.publish('MYsensor/{:d}'.format(i),'{:d}'.format(val))

		self.httpRequest(strval)

	#COMUNICAZIONE BRIDGE->SERVER
	def httpRequest(self, val):
		val = val.split('/')
		idprenotazione = val[0]
		azione = val[1]
		d = {'value': azione}
		r = requests.put(url = self._APIURL+idprenotazione, data = d, headers=self._HEADERS)
		print(r.text)

		if azione == CHECKPRENOTAZIONE:
			#elabora risposta
			#RESPONSE: 1 = CODICE VALIDO, 2 = CODICE NON VALIDO
			response = 1 #CODICE VALIDO
			self.outSeriale(1, response)




if __name__ == '__main__':
	br=Bridge()
	br.loop()