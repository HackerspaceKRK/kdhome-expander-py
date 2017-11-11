#!/usr/bin/env python2.7
import os
import smbus
import mosquitto
from twisted.internet import reactor, task

MQTT_SERVER = os.environ['MQTT_SERVER']
TOPIC_PREFIX = 'kdhome'


def output_callback(client, userdata, message):
    channel, state = message.topic.split('/')[-1], message.payload
    client.publish('kdhome/output/{}'.format(channel), state)

mqttc = mosquitto.Mosquitto("kdhome_connector")
mqttc.will_set("%s/dropped" % TOPIC_PREFIX, "Sorry, I seem to have died.")
mqttc.connect(MQTT_SERVER, 1883, 60, True)

mqttc.subscribe('%s/input/+' % TOPIC_PREFIX, qos=0)
mqttc.on_message = output_callback

task.LoopingCall(mqttc.loop_read).start(0.1)
task.LoopingCall(mqttc.loop_write).start(0.1)
task.LoopingCall(mqttc.loop_misc).start(5)

reactor.run()
