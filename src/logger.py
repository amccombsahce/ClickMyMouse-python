import logging
import os
from datetime import datetime


def get_date_time():
    now = datetime.now()
    formatted_now = now.strftime("%Y.%m.%d %H:%M:%S")
    return formatted_now


class Logger:

    def __init__(self, logfilename, logwindow):
        # self.LogFile = log("CallMeBack")
        self.logger = logging.getLogger(__name__)

        # Set the level of severity that should be logged
        self.logger.setLevel(logging.DEBUG)

        # create a logs folder for logs
        cwd = os.getcwd()
        log_dir = os.path.join(cwd, '../logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # have our log files get logged in logs folder
        filepath = os.path.join(log_dir, logfilename)

        # Create a handler for the logger
        # self.handler = logging.StreamHandler()
        # Create a file handler for the logger
        self.handler = logging.FileHandler(filepath)

        # Create a formatter and add it to the handler
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)

        # Add the handler to the logger
        self.logger.addHandler(self.handler)

        self.logwindow = logwindow

    def info(self, text):
        self.logger.info(str(get_date_time()) + ": " + text)
        self.logwindow.add_log(str(get_date_time()) + ": " + text)
        print(f"{str(text)}")

    def debug(self, text):
        self.logger.debug(str(get_date_time()) + ": " + text)
        self.logwindow.add_log(str(get_date_time()) + ": " + text)
        print(f"{str(text)}")

    def warning(self, text):
        self.logger.warning(str(get_date_time()) + ": " + text)
        self.logwindow.add_log(str(get_date_time()) + ": " + text)
        print(f"{str(text)}")

    def error(self, text):
        # self.LogFile.error(str(datetime.now()) + ": " + text)
        self.logger.error(str(get_date_time()) + ": " + text)
        self.logwindow.add_log(str(get_date_time()) + ": " + text)
        print(f"{str(text)}")

    def critical(self, text):
        # self.LogFile.critical(str(datetime.now()) + ": " + text)
        self.logger.critical(str(get_date_time()) + ": " + text)
        self.logwindow.add_log(str(get_date_time()) + ": " + text)
        print(f"{str(text)}")
        sb = 1
