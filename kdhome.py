#!/usr/bin/env python2.7
import os
import smbus
import mosquitto
from twisted.internet import reactor, task

MQTT_SERVER = os.environ['MQTT_SERVER']
TOPIC_PREFIX = 'kdhome'

smbus_bus = int(os.environ['I2C_BUS'])
input_expanders = (0x38, 0x3b)
output_expanders = (0x39, 0x3a)

mqttc = mosquitto.Mosquitto("kdhome")
mqttc.will_set("%s/dropped" % TOPIC_PREFIX, "Sorry, I seem to have died.")
mqttc.connect(MQTT_SERVER, 1883, 60, True)

bus = smbus.SMBus(smbus_bus)


def kdconvert(data):
    return data[:4] + data[4:][::-1]


def read_expander(address):
    data = bus.read_byte(address)
    data = format(data, '08b')
    return kdconvert(data)


def write_expander(address, data):
    data = kdconvert(data)
    data = int(data, 2)
    bus.write_byte(address, data)


def get_inputs_state():
    ports = map(
        read_expander,
        input_expanders
    )
    inputs = ''.join(ports)
    return inputs


def set_inputs_state(state):
    print "desired state %s" % state
    write_expander(output_expanders[0], state[:8])
    write_expander(output_expanders[1], state[8:])


def inputs_callback():
    new_state = get_inputs_state()
    if new_state != inputs_callback.last_state:
        for i in range(0, len(new_state)):
            if new_state[i] != inputs_callback.last_state[i]:
                state = int(new_state[i])
                print '%d is now %d' % (i, state)
                mqttc.publish("%s/input/%d" % (TOPIC_PREFIX, 15-i), state)
        inputs_callback.last_state = new_state
inputs_callback.last_state = '1' * 16


def output_callback(client, userdata, message):
    try:
        output = 15-int(message.topic.split('/')[TOPIC_PREFIX.count('/')+2])
        state = int(message.payload)
        if state not in [0, 1] or output not in range(0, 16):
            raise ValueError
        print 'switching %d to %d' % (output, state)
        output_callback.last_state[output] = int(state)
        set_inputs_state(
            reduce(
               lambda carry, item: carry + str(item),
               output_callback.last_state,
               ''
            )
        )
    except ValueError as e:
        print 'przyszly jakies rzygi'
    except:
        pass
output_callback.last_state = [1, 1, 1, 1,    1, 1, 1, 1,    1, 1, 1, 1,   1, 1, 1, 1]


mqttc.subscribe('%s/output/+' % TOPIC_PREFIX, qos=0)
mqttc.on_message = output_callback

task.LoopingCall(mqttc.loop_read).start(0.1)
task.LoopingCall(mqttc.loop_write).start(0.1)
task.LoopingCall(mqttc.loop_misc).start(5)
task.LoopingCall(inputs_callback).start(0.1)

reactor.run()
