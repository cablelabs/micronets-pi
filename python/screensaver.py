#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-17 Richard Hull and contributors
# See LICENSE.rst for details.
# PYTHON_ARGCOMPLETE_OK

"""
Display a bouncing ball animation and frames per second.

Attribution: https://github.com/rogerdahl/ssd1306/blob/master/examples/bounce.py

CableLabs - modified to use ScreenSaver class.
"""

import sys, time
import random
from luma.core import cmdline, error

import luma.core.render
from luma.core.sprite_system import framerate_regulator


class Ball(object):
    def __init__(self, w, h, radius, color):
        self._w = w
        self._h = h
        self._radius = radius
        self._color = color
        self._x_speed = (random.random() - 0.5) * 10
        self._y_speed = (random.random() - 0.5) * 10
        self._x_pos = self._w / 2.0
        self._y_pos = self._h / 2.0

    def update_pos(self):
        if self._x_pos + self._radius > self._w:
            self._x_speed = -abs(self._x_speed)
        elif self._x_pos - self._radius < 0.0:
            self._x_speed = abs(self._x_speed)

        if self._y_pos + self._radius > self._h:
            self._y_speed = -abs(self._y_speed)
        elif self._y_pos - self._radius < 0.0:
            self._y_speed = abs(self._y_speed)

        self._x_pos += self._x_speed
        self._y_pos += self._y_speed

    def draw(self, canvas):
        canvas.ellipse((self._x_pos - self._radius, self._y_pos - self._radius,
                       self._x_pos + self._radius, self._y_pos + self._radius), fill=self._color)


class ScreenSaver(object):
    def __init__(self, device, timeout=300):
        self.device = device
        self.lastInput = time.time()
        self.active = False
        self.timeout = timeout

    # See if we need to start the screensaver. If so, start it and this call won't return until stopped
    def checkIdle(self):
        if not self.active:
            curr_time = time.time()
            if (curr_time - self.lastInput) > self.timeout:
                self.start()
                

    # Called when a button is pressed. Reset the activity timer and stop the screensaver if active.
    def isActive(self):
        self.lastInput = time.time()
        if self.active == True:
            # was active, disable it.
            self.active = False
            return True
        else:
            return False

    def start(self):
        self.active = True
        colors = ["red", "orange", "yellow", "green", "blue", "magenta"]
        balls = [Ball(self.device.width, self.device.height, i * 1.5, colors[i % 6]) for i in range(10)]

        frame_count = 0
        fps = ""
        canvas = luma.core.render.canvas(self.device)

        regulator = framerate_regulator(fps=0)

        self.device.contrast(80)

        while self.active == True:
            with regulator:

                frame_count += 1
                with canvas as c:
                    #c.rectangle(self.device.bounding_box, outline="white", fill="black")
                    c.rectangle(self.device.bounding_box, outline="black", fill="black")
                    for b in balls:
                        b.update_pos()
                        b.draw(c)
        self.device.contrast(255)


def local_get_device():
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


if __name__ == '__main__':
    try:
        device = local_get_device()
        screenSaver = ScreenSaver(device)
        screenSaver.start()

    except KeyboardInterrupt:
        pass
