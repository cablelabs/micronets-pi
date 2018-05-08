#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import time, os
from luma.core.virtual import viewport, snapshot
from PIL import ImageFont, Image, ImageDraw
from luma.core import cmdline, error
from lib.wpa_supplicant import *

#from utils.syslogger import SysLogger
#logger = SysLogger().logger()

# ignore PIL debug messages
#logging.getLogger("PIL").setLevel(logging.ERROR)

# This is only for the AdaFruit 128x128 display. 
class DeviceUI(object):

    def __init__(self):

        self.font1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
        self.font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
        self.font3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
        self.font4 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 8)

        self.wifiIcon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', '58-wifi.png'))
        self.wifiIcon = Image.open(self.wifiIcon_path).convert("RGBA")
        self.linkedIcon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', 'linked.png'))
        self.linkedIcon = Image.open(self.linkedIcon_path).convert("RGBA")

        self.showSSID = False 

        self.messages = []
        # set up the display widgets
        self.device = self.__get_device__()

        banner = snapshot(self.device.width, 22, self.render_banner, interval=1.0)
        messages = snapshot(self.device.width, 80, self.render_messages, interval=0.05)
        # Longer interval as it toggles SSID/IP
        status = snapshot(self.device.width, 25, self.render_status, interval=5.0)

        self.virtual = viewport(self.device, width=self.device.width, height=self.device.height)
        self.virtual.add_hotspot(banner, (0, 0))
        self.virtual.add_hotspot(messages, (0, 22))
        self.virtual.add_hotspot(status, (0, 102))
        self.start_time = None

        self.lowBattery = 0;

    # using luma library
    def __get_device__(self):
        parser = cmdline.create_parser(description='luma.examples arguments')
        config = []

        if True:
            config.append("--display=ssd1351")
            config.append("--interface=spi")
            config.append("--width=128")
            config.append("--height=128")
            config.append("--spi-bus-speed=16000000")
            config.append("--rotate=0")
        else:
            config.append("--display=st7735")
            config.append("--interface=spi")
            config.append("--spi-bus-speed=16000000")
            config.append("--gpio-reset=24")
            config.append("--gpio-data-command=23")
            config.append("--gpio-backlight=18")
            config.append("--width=128")
            config.append("--height=128")
            config.append("--bgr")
            config.append("--h-offset=1")
            config.append("--v-offset=2")
            config.append("--backlight-active=high")
            config.append("--rotate=0")

        args = parser.parse_args(config)

        try:
            device = cmdline.create_device(args)
        except error.Error as e:
            parser.error(e)

        return device

    def refresh(self):
        self.virtual.refresh()

    def render_banner(self, draw, width, height):
        l,t,r,b = self.device.bounding_box
        width = r-l
        if self.lowBattery > 0:
            title = "Low Battery"
            color = "red"
        else:
            title = "Micronets"
            color = "blue"
        tw, th = draw.textsize(title, font=self.font1)
        draw.rectangle((l,t,r,20), outline=color, fill=color)

        if wpa_subscriber_exists() and self.lowBattery == 0:
            draw.text((25, t +2 ), text=title, fill="white", font=self.font1)
            draw.bitmap((110,4),self.linkedIcon)
        else:
            draw.text((30, t +2 ), text=title, fill="white", font=self.font1)

    def render_status(self, draw, width, height):
        l,t,r,b = self.device.bounding_box
        self.showSSID = not self.showSSID
        draw.rectangle((l,t+3,r,25), outline="#004030", fill="#008030")
        if (self.showSSID):
            draw.text((1, t + 6), text=self.get_ssid(), fill="white", font=self.font2)
        else:
            draw.text((3, t + 8), text=self.get_ipaddress(), fill="white", font=self.font3)

        #draw.bitmap((104,5),self.wifiIcon)
        draw.bitmap((108,7),self.wifiIcon)

    def render_messages(self, draw, width, height):
        draw.rectangle((0, 0, width, height), fill="black")

        start = 0
        items = len(self.messages)
        if len(self.messages) > 6:
            start = len(self.messages) - 6
            items = 6

        for i in range(items):
            index = start + i
            text = u"\u2022 {}".format(self.messages[index])
            draw.text((0, (i*13)+1), text=text, fill="white", font=self.font2)

        if self.start_time != None:
            curr_time = time.time()
            if (curr_time - self.start_time) > 30:
                self.start_time = None
                self.clear_messages()

    def clear_messages(self):
        self.messages[:] = []

    def add_message(self, message):
        self.messages.append(message)
        self.start_time = time.time()

    # Replace last message instead of appending
    def update_message(self, message):
        self.messages[len(self.messages)-1] = message
        self.start_time = time.time()
        
    def setLowBattery(self, count):
        self.lowBattery = count

    def get_ipaddress(self):
        fields = os.popen("ifconfig wlan0 | grep 'inet '").read().strip().split(" ")
        ipaddress = "NO IP ADDRESS"
        if len(fields) >= 2:
            ipaddress = fields[1]
        return ipaddress

    def get_ssid(self):
        ssid = os.popen("iwconfig wlan0 | grep 'ESSID'| awk '{print $4}' | awk -F\\\" '{print $2}'").read()
        return ssid


if __name__ == '__main__':
    try:
        display = DeviceUI()

        i = 0
        while True:
            i = (i+1) % 7
            if i == 0:
                display.clear_messages()
            else:
                display.add_message("message {}".format(i))

            display.refresh()
            time.sleep(1)

    except KeyboardInterrupt:
        pass
