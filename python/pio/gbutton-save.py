#!/usr/bin/env python
# TODO: Update RPi.GPIO to map pins based on hardware/revision. For now, this is meant to work on the Pi Zero W

import platform, sys, time
import RPi.GPIO as GPIO

if __name__ == '__main__':
    from interval import IntervalTimer
    from syslogger import SysLogger
else:
    from utils.interval import IntervalTimer
    from utils.syslogger import SysLogger

logger = SysLogger().logger()

class GButton(object):

    # class constants for callbacks
    DOWN = 0
    UP = 1
    CLICK = 2
    LONGPRESS = 3

    def __init__(self, pin):

        ## Instance Variables
        self.pin = pin
        self.longDelay = 5.0
        self.timer = None
        self.timer_incr = .2
        self.count = 0
        self.canclick = False
        self.user_callbacks = [None, None, None, None]

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        #GPIO.add_event_detect(self.pin, GPIO.BOTH)
        #GPIO.add_event_callback(self.pin, self.button_callback)
        GPIO.add_event_detect(self.pin, GPIO.BOTH, self.button_callback, bouncetime=50)

    # timer callback for LONGPRESS
    def timer_callback(self):
        self.count += self.timer_incr;
        if self.count >= self.longDelay:
            self.count = 0
            self.canclick = False
            self.timer.stop()
            self.user_callbacks[GButton.LONGPRESS]()
        #else: 
            #print "Timer: {}".format(self.count)

    def set_callback(self, callback_type, func, delay=None):
        self.user_callbacks[callback_type] = func
        if (callback_type == GButton.LONGPRESS and delay != None):
            self.longDelay = delay

    # local callback for button primitives
    def button_callback(self, channel):
        pressed = GPIO.input(self.pin)
        if (pressed):
            self.canclick = True
            if self.user_callbacks[GButton.DOWN]:
                self.user_callbacks[GButton.DOWN]()

            if self.user_callbacks[GButton.LONGPRESS]:
                self.count = 0
                self.timer = IntervalTimer(self.timer_incr, self.timer_callback).start()

        else:
            if self.user_callbacks[GButton.UP]:
                self.user_callbacks[GButton.UP]()
                
            if self.user_callbacks[GButton.CLICK] and self.canclick:
                self.user_callbacks[GButton.CLICK]()
                    
            if self.user_callbacks[GButton.LONGPRESS]:
                self.count = 0
                self.timer.stop()

if __name__ == '__main__':
    def callback_down():
        print "button down"
    def callback_up():
        print "button up"
    def callback_click():
        print "button click"
    def callback_longpress():
        print "button longpress"

    button = GButton(4)
    button.set_callback(GButton.DOWN, callback_down)
    button.set_callback(GButton.UP, callback_up)
    button.set_callback(GButton.CLICK, callback_click)
    button.set_callback(GButton.LONGPRESS, callback_longpress)

    i = 0

    # Loop forever, doing something useful hopefully:
    while True:
        i += 1
        logger.info("Running: " + str(i))
        time.sleep(2)



