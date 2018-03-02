############################################################
# AdaFruit st7735 LCD 
############################################################

import time, atexit, sys, random, logging
import luma.core.render
from luma.core.sprite_system import framerate_regulator
from luma.core import cmdline, error

if __name__ == '__main__':
    from syslogger import SysLogger
else:
    from utils.syslogger import SysLogger
logger = SysLogger().logger()

# ignore PIL debug messages
logging.getLogger("PIL").setLevel(logging.ERROR)

# This is only for the AdaFruit 128x128 display. 
class GDisp_st7735(object):

    # using luma library
    def get_device(self):
        parser = cmdline.create_parser(description='luma.examples arguments')

        #config = cmdline.load_config(args.config)
        config = []
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

        args = parser.parse_args(config)

        try:
            device = cmdline.create_device(args)
        except error.Error as e:
            parser.error(e)

        return device

    def __init__(self):
        self.device = self.get_device()

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


    def clear(self):
        self.device.cleanup()

    # Just a screen saver until we layout the UI
    def sprite_loop(self, num_iterations=sys.maxsize):
        colors = ["red", "orange", "yellow", "green", "blue", "magenta"]
        balls = [GDisp_st7735.Ball(self.device.width, self.device.height, i * 1.5, colors[i % 6]) for i in range(10)]

        frame_count = 0
        fps = ""
        canvas = luma.core.render.canvas(self.device)

        regulator = framerate_regulator(fps=10)

        while num_iterations > 0:
            with regulator:
                num_iterations -= 1

                frame_count += 1
                with canvas as c:
                    c.rectangle(self.device.bounding_box, outline="white", fill="black")
                    for b in balls:
                        b.update_pos()
                        b.draw(c)
                    c.text((2, 0), fps, fill="white")

                #if frame_count % 20 == 0:
                #    fps = "FPS: {0:0.3f}".format(regulator.effective_FPS())

if __name__ == '__main__':
    try:
        display = GDisp_st7735()
        display.sprite_loop()
    except KeyboardInterrupt:
        pass
