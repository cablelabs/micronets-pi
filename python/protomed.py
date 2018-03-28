#!/usr/bin/env python

import sys, time, argparse, logging, atexit

from utils.syslogger import SysLogger
logger = SysLogger().logger()

from pio.gbutton import GButton
from pio.gled import GLed
#from pio.gdisp_5110 import GDisp_5110
from pio.gdisp_st7735 import GDisp_st7735
from onboard import *
import threading
from threading import Timer

import RPi.GPIO as GPIO
from PIL import ImageFont


############################################################
# GPIO 
############################################################

GPIO.setmode(GPIO.BCM)
restoring = False
onboarding = False

# Demented python scoping.
context = {'restoring':False, 'onboarding':False}

def clickOnboard():
    print "click onboard"
    if context['onboarding']:
        #end_onboard()
        #context['onboarding'] = False
        cancelOnboard()
    else: 
        begin_onboard()
        context['onboarding'] = True

def clickReset():
    restore_defaults()


buttonOnboard = GButton(22)
buttonOnboard.set_callback(clickOnboard)

buttonReset = GButton(7)
buttonReset.set_callback(clickReset)

# LED pin 25

ledOnboard = GLed(25)

def restore_defaults():
    print "restore defaults"
    ledOnboard.blink(.05, 10, restore_complete)
    restoring = True
    resetDevice()

def restore_complete():
    print "end restore"
    restoring = False

def begin_onboard():
    print "begin onboard"
    #disp.textOut(10, 0, "MICRONETS")
    #disp.textOut(10, 30, "Onboarding...")
    ledOnboard.blink(.1)
    context['onboarding'] = True

    # TODO: Read clear private key switch
    thr = threading.Thread(target=onboardDevice, args=(False, end_onboard,)).start()
    #onboardDevice(False)

def end_onboard(status):
    print "end onboard: {}".format(status)
    #disp.textOut(10, 0, "MICRONETS")
    #disp.textOut(10, 30, "Complete!")
    context['onboarding'] = False
    ledOnboard.off()

############################################################
# LED Display
############################################################

disp = GDisp_st7735()

def cleanup():
    print("Cleaning up")

    # Clear display
    disp.clear()

    # Release GPIO
    GPIO.cleanup()


atexit.register(cleanup)

# use display loop for screensaver
#disp.sprite_loop()

# test the display
#disp.clear()
#disp.setFont("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16, "white")
#disp.textOut(20, 0, "Micronets")

# Loop forever, doing something useful hopefully:
while True:
    time.sleep(2)
