import paho.mqtt.client as mqtt
from config import MQTT_SERVER_URL, MQTT_SERVER_PORT 

class ClientMQTT():

    def __init__(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        print("connecting to MQTT broker...")
        self.clientMQTT.connect(
            MQTT_SERVER_URL,
            MQTT_SERVER_PORT,
            60)

        self.clientMQTT.loop_start()


    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
    
    def publishMQTT(self, msg, idTotem):
        self.clientMQTT.publish("TOTEMS/"+idTotem, msg)