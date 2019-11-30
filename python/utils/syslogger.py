#!/usr/bin/env python

import logging
import logging.handlers
import sys
# https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
from singleton import Singleton

# Usage
# logger = SysLogger().logger()
# logger = SysLogger("/var/log/mylogfile").logger()

#class SysLogger(object):
class SysLogger(Singleton):

    # Make a class we can use to capture stdout and sterr in the log
    class OStreamLogger(object):
            def __init__(self, logger, level):
                    """Per output stream logger object."""
                    self.logger = logger
                    self.level = level

            def write(self, message):
                    # Only log if there is a message (not just a new line)
                    if message.rstrip() != "":
                            self.logger.log(self.level, message.rstrip())
            def flush(self):
                pass


    def log_except_hook(*exc_info):
        text = "".join(traceback.format_exception(*exc_info))
        self._logger.error("Unhandled exception: %s", text)

    def __init__(self, filename='__default__', level=logging.INFO):

        if filename == '__default__':
            imgFile = sys.argv[0].rsplit('/',1)[-1] #may be filename or filename.py
            tokens = imgFile.rsplit('.',1)
            if len(tokens) == 2:
                imgFile = tokens[-2]
            filename = "/tmp/{}".format(imgFile) + ".log"

        # Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
        # Give the logger a unique name (good practice)
        self._logger = logging.getLogger(__name__)
        # Set the log level
        self._logger.setLevel(level)
        # Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
        handler = logging.handlers.TimedRotatingFileHandler(filename, when="midnight", backupCount=3)
        # Format each log message like this
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        # Attach the formatter to the handler
        handler.setFormatter(formatter)
        # Attach the handler to the logger
        self._logger.addHandler(handler)

        # Replace stdout with logging to file at INFO level
        sys.stdout = self.OStreamLogger(self._logger, logging.INFO)
        # Replace stderr with logging to file at ERROR level
        sys.stderr = self.OStreamLogger(self._logger, logging.ERROR)

        if __name__ != '__main__':
            script = sys.argv[0].rsplit('/',1)[-1]
            self._logger.info("   ")
            self._logger.info("------------------------ Executing {} -------------------------".format(script))

        # capture system errors too
        sys.excepthook = self.log_except_hook

    def logger(self):
        return self._logger;

if __name__ == '__main__':
    print "Testing SysLogger"
    logger = SysLogger('/tmp/SysLoggerTest.log').logger();
    #logger = SysLogger().logger();
    logger.info("Testing INFO logging")
    logger.error("Testing ERROR logging")
