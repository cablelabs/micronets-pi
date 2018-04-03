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
from device_ui import DeviceUI


############################################################
# GPIO 
############################################################

GPIO.setmode(GPIO.BCM)
restoring = False
onboarding = False

display = DeviceUI()

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

buttonMode = GButton(9)

# LED pin 25

ledOnboard = GLed(25)

def restore_defaults():
    print "restore defaults"
    display.clear_messages()
    display.add_message("Restore Defaults")

    ledOnboard.blink(.05, 10, restore_complete)
    restoring = True
    resetDevice()

def restore_complete():
    print "end restore"
    display.add_message("Restore Complete")
    restoring = False
    set_state()

def begin_onboard():
    print "begin onboard"
    display.clear_messages()
    display.add_message("Begin Onboard")
    ledOnboard.blink(.1)
    context['onboarding'] = True

    # Read clear private key switch
    newKey = GPIO.input(9)
    thr = threading.Thread(target=onboardDevice, args=(newKey, end_onboard, status_message,)).start()

def status_message(message):
    display.add_message(message)

def end_onboard(status):
    print "end onboard: {}".format(status)
    display.add_message(status)
    context['onboarding'] = False
    set_state()

def set_state():
    if wpa_subscriber_exists():
        ledOnboard.on()
    else:
        ledOnboard.off()

############################################################
# LED Display
############################################################

def cleanup():
    print("Cleaning up")

    # Clear display
    display.clear_messages()

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

# Have green LED reflect subscriber configured status
set_state()
while True:
    display.refresh()
    time.sleep(1)
