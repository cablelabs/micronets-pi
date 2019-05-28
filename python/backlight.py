import RPi.GPIO as GPIO
import sys
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
backlight = GPIO.PWM(18, 1000)

if (len(sys.argv) == 2) and (sys.argv[1] == "off"):
    print 'off'
    backlight.start(0)
else:
    print 'on'
    backlight.start(100)

time.sleep(.5)
#GPIO.cleanup()

