#!/usr/bin/env python3
import traceback

import signal
import sys
import RPi.GPIO as GPIO

import sched
import time
import threading
from datetime import datetime
import rrdtool
import os

# Config variables
# number of GPIO pin geiger output si connected to
GEIGER_GPIO = 4

# interval of sending CPM update to MQTT. Can be 0-59. (10 means each 10th second) Set to None to disable
mqtt_interval = 10
mqtt_broker = '127.0.0.1'
mqtt_port = 1883
mqtt_topic = 'geiger/indoors/cpm'
mqtt_client_id = 'geiger-indoors'
mqtt_username = 'geiger'
mqtt_password = 'xTuGtQdASOqTWoQâ6MIevm05f5ɜCjtS8' # yeah, I know having passwords in repository is a bad practice
mqtt_retry = 30

# global variables
counter = 0
cps = 0
counter_lock = threading.Lock()
seconds = []
seconds_pos = -1
last = None
fd = None
entries = 0
cpm = 0
max_cpm = 0

mqtt_connected = False
mqtt_client = None
mqtt_lock = threading.Lock()
mqtt_connecting = False
mqtt_last_connect = None

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.stderr.flush()

eprint("Starting geiger.py...")
time.sleep(1)

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    eprint("Connected to mqtt broker with return code: "+str(rc))
    if rc == 0:
        mqtt_connected = True
    else:
        mqtt_connected = False

def on_disconnect(client, userdata, rc):
    eprint("Disconnected with return code: "+str(rc))
    mqtt_connected = False

def on_log(client, userdata, level, buf):
    eprint("Log message: "+str(level)+", "+userdata+", "+buf)

def mqtt_connect():
    global mqtt_last_connect
    global mqtt_client
    mqtt_lock.acquire()
    if mqtt_last_connect is not None and (datetime.now() - mqtt_last_connect).total_seconds() > mqtt_retry:
        mqtt_lock.release()
        return
    
    mqtt_last_connect = datetime.now()

    mqtt_client = mqtt.Client(mqtt_client_id)
    mqtt_client.username_pw_set(mqtt_username, mqtt_password)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_log = on_log
    eprint("Connecting to mqtt broker: "+mqtt_broker+":"+str(mqtt_port))
    mqtt_client.loop_start()
    mqtt_client.enable_logger()
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_lock.release()


if mqtt_interval is not None:
    from paho.mqtt import client as mqtt
else:
    eprint("Mqtt is disabled")

def send_mqtt(cpm):
    global mqtt_connected
    global mqtt_client
    if not mqtt_connected:
        if mqtt_interval is not None:
            mqtt_connect()
        return
    mqtt_client.publish(mqtt_topic, cpm)

def second_tick():
    global counter
    global scheduler
    global seconds
    global seconds_pos
    global last
    global fd
    global entries
    global cpm
    global max_cpm
    now = datetime.now()
    if last is not None:
        slippage = (now - last).total_seconds() - 1
    else:
        slippage = 0
    last = now

    scheduler.enter(1 - slippage/2, 1, second_tick)
    counter_lock.acquire()
    cps = counter
    counter = 0
    counter_lock.release()

    seconds_pos += 1
    if seconds_pos == 60:
        seconds_pos = 0
    
    if len(seconds) < 60:
        seconds.append(cps)
    else:
        seconds[seconds_pos] = cps

    cpm = sum(seconds)/len(seconds)*60
    max_cpm = max(seconds)*60

    if mqtt_interval is not None and seconds_pos % mqtt_interval == 0:
        send_mqtt(cpm)

    if fd is None:
        print(str(now)+","+str(slippage)+","+str(cps) + "," + str(cpm))
    else:
        if entries > 3600:
            fd.truncate(0)
            entries = 0
        entries += 1
        fd.write(str(now)+","+str(slippage)+","+str(cps) + "," + str(cpm)+"\n")
        fd.flush()

def minute_tick():
    global scheduler
    global cpm
    global rrd
    global max_cpm
    scheduler.enter(60, 2, minute_tick)
    try:
        rrdtool.update("/var/lib/geiger/geiger.rrd", "N:"+str(cpm)+":"+str(max_cpm))
    except Exception as e:
        eprint("RRD update failed: "+str(e))

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def geiger_pulse_callback(channel):
    global counter
    counter_lock.acquire()
    counter += 1
    counter_lock.release()

if __name__ == '__main__':
    if not os.path.exists("/run/geiger"):
        os.mkdir("/run/geiger")
    fd = open("/run/geiger/geiger.csv", "w")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GEIGER_GPIO, GPIO.IN)

    GPIO.add_event_detect(GEIGER_GPIO, GPIO.FALLING, 
            callback=geiger_pulse_callback, bouncetime=1)

    if not os.path.exists("/var/lib/geiger"):
        os.mkdir("/var/lib/geiger")
        os.mkdir("/var/lib/geiger/img")
        rrd = rrdtool.create("/var/lib/geiger/geiger.rrd", "--step", "60", "--start", '0',
         "DS:CPM:GAUGE:90:U:U",
         "DS:PeakCPM:GAUGE:90:U:U",
         "RRA:AVERAGE:0.5:1:43830",
         "RRA:AVERAGE:0.5:60:8766",
         "RRA:AVERAGE:0.5:24:3650",
         "RRA:MAX:0.5:1:43830",
         "RRA:MAX:0.5:60:8766",
         "RRA:MAX:0.5:24:3650")
    scheduler = sched.scheduler(time.time, time.sleep)
    second_tick()
    minute_tick()

    scheduler.run()
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()
