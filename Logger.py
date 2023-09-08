# from log4python.Log4python import log
import logging
import inspect

from datetime import datetime
# lets log what we do

from datetime import datetime


class Logger:

    def __init__(self, logfilename):
        # self.LogFile = log("CallMeBack")
        self.logger = logging.getLogger(__name__)

        # Set the level of severity that should be logged
        self.logger.setLevel(logging.DEBUG)

        # Create a handler for the logger
        # self.handler = logging.StreamHandler()
        # Create a file handler for the logger
        self.handler = logging.FileHandler(logfilename)

        # Create a formatter and add it to the handler
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)

        # Add the handler to the logger
        self.logger.addHandler(self.handler)

    def info(self, text):
        # self.LogFile.info(str(datetime.now()) + ": " + text)
        self.logger.info(str(datetime.now()) + ": " + text)

    def debug(self, text):
        # self.LogFile.debug(str(datetime.now()) + ": " + text)
        self.logger.debug(str(datetime.now()) + ": " + text)



    def warning(self, text):
        # self.LogFile.warning(str(datetime.now()) + ": " + text)
        self.logger.warning(str(datetime.now()) + ": " + text)

    def error(self, text):
        # self.LogFile.error(str(datetime.now()) + ": " + text)
        self.logger.error(str(datetime.now()) + ": " + text)

    def critical(self, text):
        # self.LogFile.critical(str(datetime.now()) + ": " + text)
        self.logger.critical(str(datetime.now()) + ": " + text)
