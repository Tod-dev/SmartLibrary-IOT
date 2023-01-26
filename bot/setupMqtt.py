import paho.mqtt.client as paho
from paho import mqtt
import ssl
from config import MQTT_SERVER_URL, MQTT_SERVER_PORT, MQTT_USER, MQTT_PWD

class ClientMQTT():

    def __init__(self):
        self.clientMQTT = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        self.clientMQTT.username_pw_set(MQTT_USER, MQTT_PWD)
        self.clientMQTT.tls_set(tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_NONE)
        self.clientMQTT.on_connect = self.on_connect
        print("connecting to MQTT broker...")
        self.clientMQTT.connect(
            MQTT_SERVER_URL,
            MQTT_SERVER_PORT,
            60)

        self.clientMQTT.loop_start()


    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
    
    def publishMQTT(self, msg, idTotem):
        topic = "TOTEMS/{}".format(idTotem)
        self.clientMQTT.publish(topic, msg)