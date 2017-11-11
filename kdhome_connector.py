#!/usr/bin/env python3

import paho.mqtt.client as mqtt


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):

	print('Connected with result code ' + str(rc))

	client.publish('kdhome/_sys', 'input->output bridge connected')

	client.subscribe('kdhome/input/+')

	# spam_frame(client)
	# spam_show(client)

def on_message(client, userdata, msg):
	channel, state = msg.topic.split('/')[-1], msg.payload

	client.publish('kdhome/output/{}'.format(channel), state)


client = mqtt.Client()
client.will_set('kdhome/_sys', 'input->output bridge disconnected')
client.on_connect = on_connect
client.on_message = on_message

client.connect("rudy.at.hskrk.pl", 1883, 60)

client.loop_forever()
