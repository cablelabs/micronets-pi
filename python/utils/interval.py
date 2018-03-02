#!/usr/bin/env python

import sys, traceback
import time
from threading import Event, Thread

timer = 0

class IntervalTimer:

    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, *args, **kwargs):

        global timer

        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.begin = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.enabled = False
        self.timerID = timer
        timer = timer + 1
        #print "- create timer: {}".format(self.timerID)

    def _target(self):
        while self.enabled and not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)
        #print "_target return"
        return False

    @property
    def _time(self):
        return self.interval - ((time.time() - self.begin) % self.interval)

    def stop(self):
        #print "- stop timer: {}".format(self.timerID)
        self.enabled = False;
        self.event.set()
        self.thread.stopped = True
        return self

    def start(self):
        #print "- start timer: {}".format(self.timerID)
        #traceback.print_stack(None, 4)
        self.enabled = True;
        self.thread.start()
        return self
 