const mqtt = require('mqtt');

let mqttConnection;

class MqttHandler {
  constructor() {
    this.mqttClient = null;
    this.options = {
      host: process.env.MQTT_BROKER,
      port: 8883,
      protocol: 'mqtts',
      username: process.env.MQTT_USERNAME,
      password: process.env.MQTT_PASSWORD
    }
  }
  
  connect() {
    // Connect mqtt with credentials (in case of needed, otherwise we can omit 2nd param)
    this.mqttClient = mqtt.connect(this.options);

    // Mqtt error calback
    this.mqttClient.on('error', (err) => {
      console.log(err);
      this.mqttClient.end();
    });

    // Connection callback
    this.mqttClient.on('connect', () => {
      console.log(`mqtt client connected`);
    });

    // mqtt subscriptions
    this.mqttClient.subscribe('TOTEMS/*', {qos: 0});

    // When a message arrives, console.log it
    this.mqttClient.on('message', function (topic, message) {
      console.log(message.toString());
    });

    this.mqttClient.on('close', () => {
      console.log(`mqtt client disconnected`);
    });
  }

  // Sends a mqtt message to topic: mytopic
  sendMessage(topic,message) {
    this.mqttClient.publish('TOTEMS/'+topic, message);
  }
}

module.exports.connectMqtt =  async () => {
  mqttConnection = new MqttHandler();
  mqttConnection.connect();
}

module.exports.getMqttConnection = () => {
  return mqttConnection;
}


module.exports.sendMessage =  async (topic,message) => {
  mqttConnection.sendMessage(topic,message);
}