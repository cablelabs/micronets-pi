#!/usr/bin/env python
# TODO: Update RPi.GPIO to map pins based on hardware/revision. For now, this is meant to work on the Pi Zero W

import platform
import sys
import time
import RPi.GPIO as GPIO

from utils.interval import IntervalTimer
from utils.syslogger import SysLogger

logger = SysLogger().logger()

class GLed(object):

    def __init__(self, pin):

        ## Instance Variables
        self.pin = pin
        self.timer = None
        self.isBlink = False
        self.countDown = 0
        self.callback = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)

    # timer callback for LED blink
    def timer_callback(self):
        self.isBlink = not self.isBlink
        #print "blink {}".format(self.isBlink)

        GPIO.output(self.pin, self.isBlink)

        if self.countDown > 0:
            self.countDown = self.countDown - 1
            if self.countDown == 0:
                self.off()
                if self.callback != None:
                    self.callback()

    def blink(self, interval, count = 0, callback = None):
        if self.timer != None:
            self.timer.stop()
        #print "starting blink timer {}: {}".format(self.pin, interval)
        self.countDown = count * 2
        self.callback = callback
        self.timer = IntervalTimer(interval, self.timer_callback).start()

    def on(self):
        if self.timer != None:
            self.timer.stop()
        GPIO.output(self.pin, True)

    def off(self):
        if self.timer != None:
            self.timer.stop()
        GPIO.output(self.pin, False)

if __name__ == '__main__':
    
    led = GLed(25)

    i = 0
    i = -1
    led.on()

    while True:
        #i = (i + 1) % 4
        
        if i == 0 or i == 2:
            led.off()
        elif i == 1:
            led.on()
        elif i == 3:
            led.blink(.1)

        time.sleep(2)



