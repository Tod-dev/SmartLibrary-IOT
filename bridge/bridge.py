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
import wx
import threading

class Bridge():

	def __init__(self, frame):
		self.ui = frame
		#INTERO
		self.LIBRO_RITIRATO = 1
		self.LIBRO_RICONSEGNATO = 2
		self.RICHIESTA_UPDATE = 3

		#CODICE
		self.LIBRO_PRENOTATO = 1
		self.LIBRO_PRONTO_PER_RITIRO = 2
		self.LIBRO_IN_CONSEGNA = 3

		self.BYTE_INIZIO = 255
		self.BYTE_FINE = 254

		self.setupTotem()
		self.setupSerial()
		self.setupHTTP()
		self.setupMQTT()
		serial_thread = threading.Thread(target=self.loop)
		serial_thread.start()
    
	def setupTotem(self):
		self.id = config.get("TOTEM","ID")
		self.topic = "TOTEMS/" + self.id
		self.elenco_prenotazioni = dict()

	def setupSerial(self):
		# open serial port
		self.ser = None

		if config.get("Serial","UseDescription", fallback=False):
			self.portname = config.get("Serial","PortName", fallback="COM4")
		else:
			print("list of available ports: ")
			ports = serial.tools.list_ports.comports()

			for port in ports:
				print (port.device)
				print (port.description)
				if config.get("Serial","PortDescription", fallback="arduino").lower() \
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
		MQTT_USER = config.get("MQTT", "MQTT_USERNAME")
		MQTT_PWD = config.get("MQTT", "MQTT_PASSWORD")
		self.clientMQTT.username_pw_set(MQTT_USER, MQTT_PWD)
		self.clientMQTT.tls_set(tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_NONE)
		self.clientMQTT.on_connect = self.on_connect
		self.clientMQTT.on_message = self.on_message
		print("connecting to MQTT broker...")
		self.clientMQTT.connect(
			config.get("MQTT","MQTT_BROKER"),
			config.getint("MQTT","Port"),
			60)
		self.clientMQTT.loop_start()

	def setupHTTP(self):
		self.APIURL = config.get("SERVER", "URL")

	def on_connect(self, client, userdata, flags, rc, properties=None):
		print("Connected with result code " + str(rc))

		# Subscribing in on_connect() means that if we lose the connection and
		# reconnect then subscriptions will be renewed.
		self.clientMQTT.subscribe(self.topic)
		self.topic_prenotazioni = 'TOTEMS/PRENOTAZIONI'

	# The callback for when a PUBLISH message is received from the server.
	# COMUNICAZIONE SERVER->BRIDGE->ARDUINO
	def on_message(self, client, userdata, msg):
		print(msg.topic + " " + str(msg.payload))

		if msg.topic == self.topic:
			#gestisci il messaggio e scrivi sulla seriale
			#In msg c'è NFC_LIBRO/IDSCOMPARTIMENTO/CODICE/IDPRENOTAZIONE
			msg = msg.payload.decode('utf-8')
			msg = msg.split('/')

			if msg[0] == '-1':
				#ERRORE
				self.ui.setLabelMsg(msg[1])
				return
			
			nfc_id = str(msg[0])
			idscompartimento = int(msg[1])
			codice = int(msg[2])
			idprenotazione = int(msg[3])
			
			if codice == self.LIBRO_PRONTO_PER_RITIRO or codice == self.LIBRO_IN_CONSEGNA:
				self.elenco_prenotazioni[idscompartimento] = idprenotazione
				self.outSeriale(idscompartimento, codice, nfc_id)
			else:
				self.outSeriale(idscompartimento, codice)
		
	def outSeriale(self, idscompartimento, codice, nfc_id='00000000'):
		"""
		PACCHETTO
		---------
		FF|idscompartimento|codice|nfc_id|FE
		"""
		print("BRIDGE -> ARDUINO | {}|{}|{}".format(idscompartimento, codice, nfc_id))
		nfc_id = bytearray.fromhex(nfc_id)
		idscompartimento = idscompartimento.to_bytes(2, 'little')

		
		self.ser.write(self.BYTE_INIZIO.to_bytes(1, 'little'))
		self.ser.write(idscompartimento[1].to_bytes(1, 'little'))
		self.ser.write(idscompartimento[0].to_bytes(1, 'little'))
		self.ser.write(codice.to_bytes(1, 'little'))
		self.ser.write(nfc_id[0].to_bytes(1,'little'))
		self.ser.write(nfc_id[1].to_bytes(1,'little'))
		self.ser.write(nfc_id[2].to_bytes(1,'little'))
		self.ser.write(nfc_id[3].to_bytes(1,'little'))
		self.ser.write(self.BYTE_FINE.to_bytes(1, 'little'))
	
	def outSerialeUpdate(self, stato_scompartimenti):
		"""
		PACCHETTO
		---------
		FF|statoScomp1|statoScomp2|...|FE
		"""
		print("BRIDGE -> ARDUINO, UPDATE")
		self.ser.write(self.BYTE_INIZIO.to_bytes(1, 'little'))
		for stato in stato_scompartimenti:
			self.ser.write(stato.to_bytes(1, 'little'))
		self.ser.write(self.BYTE_FINE.to_bytes(1, 'little'))

	def loop(self):
		# infinite loop for serial managing
		# COMUNICAZIONE ARDUINO->BRIDGE
		
		while (True):
			#look for a byte from serial
			if not self.ser is None:

				if self.ser.in_waiting>0:
					# data available from the serial port
					lastchar=self.ser.read(1)
					#print("CARATTERE: {}".format(lastchar))
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
		idscompartimento = int.from_bytes(self.inbuffer[2], byteorder='little')
		idscompartimento += (int.from_bytes(self.inbuffer[1], byteorder='little') << 8)
		intero = int.from_bytes(self.inbuffer[3], byteorder='little')

		# nfc_id = str(self.inbuffer[4].decode('utf-8'))
		# nfc_id += str(self.inbuffer[5].decode('utf-8'))
		# nfc_id += str(self.inbuffer[6].decode('utf-8'))
		# nfc_id += str(self.inbuffer[7].decode('utf-8'))

		if idscompartimento == 0 and intero == 0:
			#ERRORE
			self.ui.setLabelMsg('Errore nella lettura dell\'nfc del libro, per favore ripetere la procedura')
			return

		if idscompartimento == 0 and intero == self.RICHIESTA_UPDATE:
			#UPDATE RICHIESTO DALL'ARDUINO
			self.httpRequestUpdate()

		if intero == self.LIBRO_RICONSEGNATO or intero == self.LIBRO_RITIRATO:
			#risali al codice prenotazione associato e conferma al server il ritiro
			if idscompartimento in self.elenco_prenotazioni:
				idprenotazione = self.elenco_prenotazioni[idscompartimento]

				if intero == self.LIBRO_RICONSEGNATO:
					self.clientMQTT.publish(self.topic_prenotazioni, '{}/{}/{}/{}'.format(self.id, idprenotazione, 'consegnato', idscompartimento))
					self.ui.setLabelMsg('Libro consegnato con successo!')
				else:
					self.clientMQTT.publish(self.topic_prenotazioni, '{}/{}/{}/{}'.format(self.id, idprenotazione, 'ritirato', idscompartimento))
					self.ui.setLabelMsg('Libro ritirato con successo, buona lettura!')

				del self.elenco_prenotazioni[idscompartimento]
			else:
				print("Codice prenotazione non trovato!")
	
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

#INTERFACCIA GRAFICA
class TotemApp(wx.Frame):    
	def __init__(self):
		super().__init__(parent=None, title='TOTEM {}'.format(config.get("TOTEM","ID")))
        
		panel = wx.Panel(self)        
		my_sizer = wx.BoxSizer(wx.VERTICAL)   

        #ELEMENTI A VIDEO   
		self.text_ctrl = wx.TextCtrl(panel)
		self.text_ctrl.SetHint('Inserisci l\'id della tua prenotazione')    
		ritira_btn = wx.Button(panel, label='Ritira')
		consegna_btn = wx.Button(panel, label='Consegna')
		self.msg = wx.StaticText(panel,-1,'')

        #PREMO UN BOTTONE
		ritira_btn.Bind(wx.EVT_BUTTON, self.ritira)
		consegna_btn.Bind(wx.EVT_BUTTON, self.consegna)

        #AGGIUNGO GLI ELEMENTI A VIDEO AL PANNELLO PRINCIPALE
		my_sizer.Add(self.text_ctrl, 0, wx.ALL | wx.EXPAND, 5)
		my_sizer.Add(ritira_btn, 0, wx.ALL | wx.CENTER, 5)
		my_sizer.Add(consegna_btn, 0, wx.ALL | wx.CENTER, 5)
		my_sizer.Add(self.msg, 0, wx.ALL | wx.CENTER, 5)              
		panel.SetSizer(my_sizer)        
		self.Show()
		self.br = Bridge(self)

	def ritira(self, event):
		idprenotazione = self.text_ctrl.GetValue()
		if not idprenotazione.isnumeric():
			self.msg.LabelText = 'ID Prenotazione non valido!'
			return
        
		self.br.clientMQTT.publish(self.br.topic_prenotazioni, '{}/{}/{}'.format(self.br.id, idprenotazione, 'ritiro'))

	def consegna(self, event):
		idprenotazione = self.text_ctrl.GetValue()
		if not idprenotazione.isnumeric():
			self.msg.LabelText = 'ID Prenotazione non valido!'
			return
        
		self.br.clientMQTT.publish(self.br.topic_prenotazioni, '{}/{}/{}'.format(self.br.id, idprenotazione, 'consegna'))

	def setLabelMsg(self, msg):
		self.msg.LabelText = msg


if __name__ == '__main__':
	config_path = pathlib.Path(__file__).parent.absolute() / "config.ini"
	config = configparser.ConfigParser()
	config.read(config_path)
	app = wx.App()
	frame = TotemApp()
	app.MainLoop()