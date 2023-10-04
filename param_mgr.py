import time
import os
from network_mgr import *
from config_mgr import ConfigMgr
from script_engine import ScriptEngine
from logger import Logger
from datetime import datetime


class ClientAttendance:
    def __init__(self, param_mgr):
        self.ParamMgr = param_mgr
        self.MasterClientList = []
        self.WorkingClientList = []

    def add_client_attendance(self, client):
        if client not in self.MasterClientList:
            self.MasterClientList.insert(0, client)

    def del_client_attendance(self, client):
        if client in self.MasterClientList:
            self.MasterClientList.remove(client)

    def clear_client_response(self):
        self.WorkingClientList.clear()

    def add_client_response(self, client):
        if client not in self.WorkingClientList:
            self.WorkingClientList.insert(0, client)

    def wait_for_client_response(self):
        start_time = datetime.now()

        while len(self.MasterClientList) != len(self.WorkingClientList):
            current_time = datetime.now()
            time_difference = current_time - start_time
            total_seconds = time_difference.total_seconds()
            if total_seconds > self.ParamMgr.client_response_timeout:
                break  # timeout occurred
            else:
                time.sleep(0)
                # check the sockets to see if they closed after we got in here
                # remove from attendance so that we are not waiting for dead clients
                for abc_socket in self.MasterClientList:
                    if abc_socket.fileno() < 0:
                        self.del_client_attendance(abc_socket)

        if len(self.MasterClientList) == len(self.WorkingClientList):
            return True
        else:
            return False


# when we need to pass more classes around, well just add it to the class
class ParameterMgr:
    def __init__(self):
        self.NetworkMgr_stop_event = None
        self.is_server: bool = True
        self.NetworkMgr: NetworkMgr = None
        self.ConfigMgr: ConfigMgr = None
        self.ScriptEngine: ScriptEngine = None
        self.Logger: Logger = None
        self.main_gui = None
        self.main_connections = None
        self.client_attendance: ClientAttendance = ClientAttendance(self)  # to support multiple clients
        self.client_response_timeout = (60 * 1)  # 1 minute timeout, not long

        # we can use variables in script to store int and string values
        self.script_items_point = {}
        self.script_items_int = {}
        self.script_items_string = {}

    def get_date_time(self):
        now = datetime.now()
        formatted_now = now.strftime("%Y.%m.%d %H:%M:%S")
        return formatted_now

    def get_log_path(self):
        cwd = os.getcwd()
        log_dir = os.path.join(cwd, 'logs')
        return log_dir

    def set_script_string(self, key, value):
        self.script_items_string[key] = value

    def get_script_string(self, key):
        if key in self.script_items_string:
            return self.script_items_string[key]
        else:
            return None

        # does the string exist

    def is_script_string(self, key):
        if key in self.script_items_string:
            return True
        else:
            return False

    def set_script_point(self, key, value):
        self.script_items_point[key] = value

    def get_script_point(self, key):
        if key in self.script_items_point:
            return self.script_items_point[key]
        else:
            return None

        # does the string exist

    def is_script_point(self, key):
        if key in self.script_items_point:
            return True
        else:
            return False

    def set_script_int(self, key, value):
        self.script_items_int[key] = value

    def get_script_int(self, key):
        if key in self.script_items_int:
            return self.script_items_int[key]
        else:
            return None

        # does the string exist

    def is_script_int(self, key):
        if key in self.script_items_int:
            return True
        else:
            return False
