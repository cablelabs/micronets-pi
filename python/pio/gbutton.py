#!/usr/bin/env python
# TODO: Update RPi.GPIO to map pins based on hardware/revision. For now, this is meant to work on the Pi Zero W

import platform, sys, time
import RPi.GPIO as GPIO

from utils.interval import IntervalTimer
from utils.syslogger import SysLogger

logger = SysLogger().logger()

class GButton(object):

    def __init__(self, pin):

        ## Instance Variables
        self.pin = pin
        self.user_callback = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.RISING, self.button_callback, bouncetime=50)

    def set_callback(self, func):
        self.user_callback = func

    # local callback for button primitives
    def button_callback(self, channel):

        pressed = GPIO.input(self.pin)
        if (pressed):
            if self.user_callback:
                self.user_callback()
                    
if __name__ == '__main__':
    count7 = 0
    count22 = 0

    def callback_click7():
        global count7
        count7 = count7+1
        print "button7 click: {} Mode: {}".format(count7, GPIO.input(9))

    def callback_click22():
        global count22
        count22 = count22+1
        print "button22 click: {}".format(count22)

    button7 = GButton(7)
    button7.set_callback(callback_click7)

    button22 = GButton(22)
    button22.set_callback(callback_click22)

    # Mode switch
    button9 = GButton(9)

    i = 0

    # Loop forever, doing something useful hopefully:
    while True:
        i += 1
        time.sleep(.05)


