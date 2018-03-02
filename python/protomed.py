#!/usr/bin/env python

import sys, time, argparse, logging, atexit

from utils.syslogger import SysLogger
logger = SysLogger().logger()

from utils.gbutton import GButton
from utils.gled import GLed
#from utils.gdisp_5110 import GDisp_5110
from utils.gdisp_st7735 import GDisp_st7735

import RPi.GPIO as GPIO

############################################################
# GPIO 
############################################################

restoring = False
onboarding = False

# Demented python scoping.
context = {'restoring':False, 'onboarding':False}

# Button pin 4
def btn4_longpress():
    print "Long Press"
    context['restoring'] = True
    restore_defaults()

def btn4_click():
    print "click"
    if context['onboarding']:
        end_onboard()
        context['onboarding'] = False
    else: 
        begin_onboard()
        context['onboarding'] = True

def btn4_up():
    if context['restoring']:
        restore_complete()
        context['restoring'] = False

button4 = GButton(4)
button4.set_callback(GButton.CLICK, btn4_click)
button4.set_callback(GButton.LONGPRESS, btn4_longpress)
button4.set_callback(GButton.UP, btn4_up)

button6 = GButton(6)
button6.set_callback(GButton.CLICK, btn4_click)
button6.set_callback(GButton.LONGPRESS, btn4_longpress)
button6.set_callback(GButton.UP, btn4_up)

# LED pin 25

led25 = GLed(25)

def restore_defaults():
    print "restore defaults"
    led25.on()
    restoring = True

def restore_complete():
    print "restore complete"
    led25.off()

def begin_onboard():
    print "begin onboard"
    led25.blink(.1)

def end_onboard():
    print "end onboard"
    led25.off()

############################################################
# LED Display
############################################################

#disp = GDisp_5110()
disp = GDisp_st7735()

def cleanup():
    print("Cleaning up")

    # Clear display
    disp.clear()

    # Release GPIO
    GPIO.cleanup()


atexit.register(cleanup)

# use display loop for screensaver
disp.sprite_loop()

# Loop forever, doing something useful hopefully:
#while True:
#        time.sleep(2)
