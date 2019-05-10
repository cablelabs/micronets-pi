#!/usr/bin/env python

import sys, time, argparse, logging, atexit
from subprocess import call

from utils.syslogger import SysLogger
logger = SysLogger().logger()

from pio.gbutton import GButton
#from pio.gled import GLed
import threading
from threading import Timer

import RPi.GPIO as GPIO
from PIL import ImageFont
#from device_ui import DeviceUI
#from screensaver import ScreenSaver

#buttonMode = GButton(9)
#DPP = buttonMode.is_set()
#if DPP:
#    from onboard_dpp import *
#else:
#    from onboard import *

############################################################
# GPIO 
############################################################

GPIO.setmode(GPIO.BCM)
#restoring = False
#onboarding = False
#batteryLow = 0

#display = DeviceUI(DPP)

#screenSaver = ScreenSaver(display.device, 60)

# Demented python scoping.
#context = {'restoring':False, 'onboarding':False, 'restarting': False}

def clickOnboard():
    print "click onboard"
'''    
    if not screenSaver.isActive():
        if context['onboarding']:
            display.clear_messages()
            display.add_message("Canceling..")
            display.refresh()

            cancel_onboard()
        else: 
            begin_onboard()
            context['onboarding'] = True
'''


'''
def clickReset():
    restore_defaults()

def shutdown():
    if not screenSaver.isActive():
        print "click shutdown"

        count = 0
        kill = False

        while buttonShutdown.is_set():
            time.sleep(1)
            count = count + 1
            if count == 5:
                kill = True
                break

        if kill:
            display.add_message("Shutting Down..")
            display.refresh()
            time.sleep(1)
            call("sudo shutdown -h now", shell=True)
        else:
            display.clear_messages()
            display.add_message("Restart Requested.")
            display.refresh()
            time.sleep(1)

            # Cancel if in progress
            if context['onboarding']:
                display.add_message("Canceling Onboard..")
                display.refresh()
                thr = threading.Thread(target=cancelOnboard, args=(no_message,)).start()
                time.sleep(1)

            # We also might press restart just to bring wifi down/up. 
            display.add_message("Cycling Wifi..")
            display.refresh()
            time.sleep(1)
            restartWifi()

            display.add_message("Restarting..")
            display.refresh()
            time.sleep(1)
            display.clear()

            call("sudo systemctl restart protomed", shell=True)
'''

#buttonOnboard = GButton(17, False)
# GPIO17 == BCM11
buttonOnboard = GButton(11, False)
buttonOnboard.set_callback(clickOnboard)

'''
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

def cancel_onboard():
    thr = threading.Thread(target=cancelOnboard, args=(display,onboard_canceled,)).start()
    context['onboarding'] = False
    set_state()

def begin_onboard():
    print "begin onboard"
    display.clear_messages()
    display.add_message("Begin Onboard")
    ledOnboard.blink(.1)
    context['onboarding'] = True

    newKey = False
    thr = threading.Thread(target=onboardDevice, args=(newKey, end_onboard, display,)).start()

def onboard_canceled():
    display.add_message("Onboard Canceled")
#def status_message(message):
#    display.add_message(message)

def no_message(message):
    return

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
'''
def cleanup():
    print("Cleaning up")

    # Clear display
    #display.clear_messages()

    #display.clear()

    # Release GPIO
    GPIO.cleanup()


atexit.register(cleanup)

while True:

    #display.refresh()
    time.sleep(1)



