############################################################
# Nokia 5110 LCD example
############################################################

import time, atexit
if __name__ == '__main__':
    from interval import IntervalTimer
    from syslogger import SysLogger
else:
    from utils.interval import IntervalTimer
    from utils.syslogger import SysLogger

logger = SysLogger().logger()

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

import Image
import ImageDraw
import ImageFont

class GDisp_5110(object):

    def __init__(self):

        # Raspberry Pi hardware SPI config:
        DC = 23
        RST = 24
        SPI_PORT = 0
        SPI_DEVICE = 0

        # Hardware SPI usage:
        self.disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
         
        # Initialize library.
        self.disp.begin(contrast=50)
         
        # Clear display.
        self.disp.clear()
        self.disp.display()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
         
        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)
         
        # Draw a white filled box to clear the image.
        self.draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
         
        # Draw some shapes.
        #self.draw.ellipse((2,2,22,22), outline=0, fill=255)
        #self.draw.rectangle((24,2,44,22), outline=0, fill=255)
        #self.draw.polygon([(46,22), (56,2), (66,22)], outline=0, fill=255)
        #self.draw.line((68,22,81,2), fill=0)
        #self.draw.line((68,2,81,22), fill=0)
         
        # Load default font.
        self.font = ImageFont.load_default()
         
        # Alternatively load a TTF font.
        # Some nice fonts to try: http://www.dafont.com/bitmap.php
        #self.font = ImageFont.truetype('Minecraftia.ttf', 8)
         
        # Write some text.
        #self.draw.text((8,30), 'ProtoMed V0.0', font=self.font)
        self.draw.text((2,8), 'ProtoMed V0.0', font=self.font)
         
        # Display image.
        self.disp.image(self.image)
        self.disp.display()

    def clear(self):
        self.disp.clear()
        self.disp.display()

    def set_font(self, font):
        self.font = font

if __name__ == '__main__':

    disp = GDisp_5110()

    def cleanup():
        print("Cleaning up")
        # Clear display
        disp.clear()

    atexit.register(cleanup)


    i = 0

    # Loop forever, doing something useful hopefully:
    while True:
        i += 1
        logger.info("Running: " + str(i))
        time.sleep(2)

