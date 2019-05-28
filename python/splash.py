import Image
import RPi.GPIO as GPIO 
import Adafruit_ILI9341 as TFT
import Adafruit_GPIO.SPI as SPI

# Raspberry Pi configuration.
DC = 18
RST = 24
SPI_PORT = 0
SPI_DEVICE = 1

# Create TFT LCD display class.
disp = TFT.ILI9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))
 
# Initialize display.
disp.begin()

# Load an image.
# Make sure the image is 320x240 pixels!
print 'Loading image...'
image = Image.open('/etc/micronets/splash.png')
 
# Resize the image and rotate it so it's 240x320 pixels.
image = image.rotate(90).resize((240, 320))

# Draw the image on the display hardware.
print 'Drawing image'
disp.display(image)

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
backlight = GPIO.PWM(18, 1000)
backlight.start(100)

GPIO.cleanup()

