#!/usr/bin/env python3

import signal
import sys
import RPi.GPIO as GPIO

import sched
import time
import threading
from datetime import datetime
import rrdtool
import os

GEIGER_GPIO = 4
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
    rrdtool.update("/var/lib/geiger/geiger.rrd", "N:"+str(cpm)+":"+str(max_cpm))

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
