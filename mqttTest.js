var mqtt = require('mqtt')

var options = {
    host: '35a8c4bef0ee4ac1ae536458c29aa669.s2.eu.hivemq.cloud',
    port: 8883,
    protocol: 'mqtts',
    username: 'server',
    password: 'Server123'
}

// initialize the MQTT client
var client = mqtt.connect(options);

// setup the callbacks
client.on('connect', function () {
    console.log('Connected');
});

client.on('error', function (error) {
    console.log(error);
});

client.on('message', function (topic, message) {
    // called each time a message is received
    console.log('Received message:', topic, message.toString());
});

// subscribe to topic 'my/test/topic'
client.subscribe('my/test/topic');

// publish message 'Hello' to topic 'my/test/topic'
client.publish('my/test/topic', 'Hello');