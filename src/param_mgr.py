import time
import os
from datetime import datetime
import hashlib
from network_mgr import *
from config_mgr import ConfigMgr
from script_engine import ScriptEngine
from logger import Logger
from message_type import MessageType, TestcaseType
from point_type import Point


class ClientLedger:
    def __init__(self, peer_info):
        self.peer_info = peer_info
        self.test_statistics = TestStatistics()


class TestStatistics:
    def __init__(self):
        self.total_testcase_request_sent_count = 0  # keep track the number to compare at the end for missing messages
        self.total_testcase_request_recv_count = 0
        self.total_testcase_response_sent_count = 0
        self.total_testcase_response_recv_count = 0

        self.total_variable_request_sent_count = 0
        self.total_variable_request_recv_count = 0
        self.total_variable_response_sent_count = 0
        self.total_variable_response_recv_count = 0

        self.total_maintenance_request_sent_count = 0
        self.total_maintenance_request_recv_count = 0
        self.total_maintenance_response_sent_count = 0
        self.total_maintenance_response_recv_count = 0

        self.total_unknown_sent_count = 0
        self.total_unknown_recv_count = 0

        self.total_testcase_pass_count = 0
        self.total_testcase_fail_count = 0
        self.total_testcase_error_count = 0

        self.total_variable_pass_count = 0
        self.total_variable_fail_count = 0
        self.total_variable_error_count = 0

        self.total_maintenance_pass_count = 0
        self.total_maintenance_fail_count = 0
        self.total_maintenance_error_count = 0

    # def get_total_count(self):
    #     return self._total_count
    # def get_pass_count(self):
    #     return self._pass_count
    # def get_fail_count(self):
    #     return self._fail_count
    # def get_error_count(self):
    #     return self._error_count


class ClientAttendance:
    def __init__(self, param_mgr):
        self.ParamMgr = param_mgr
        self.MasterClientList = []
        self.WorkingClientList = {}

    def add_client_attendance(self, client):
        if client not in self.MasterClientList:
            self.MasterClientList.insert(0, client)

    def del_client_attendance(self, client):
        if client in self.MasterClientList:
            self.MasterClientList.remove(client)

    def get_client_attendance_count(self) -> int:
        return len(self.MasterClientList)

    # clear_client_response will make sure that we only want to wait for a specific message_type to reply, possible testcase type too
    def clear_client_response(self, message_type: MessageType, testcase_type: TestcaseType):

        if message_type in self.WorkingClientList:
            abc_message_type = self.WorkingClientList[message_type]
            if testcase_type in abc_message_type:
                abc = abc_message_type[testcase_type]
                abc.clear()
            else:
                abc = []
                abc_message_type[testcase_type] = abc
        else:
            # not here, then add it
            # abc is a list of clients that have replied to this message_type
            abc = []
            abc_message_type = {testcase_type: abc}
            self.WorkingClientList[message_type] = abc_message_type

        abc = 1

    def add_client_response(self, client: str, message_type: MessageType, testcase_type: TestcaseType):
        # client is peer_info
        self.ParamMgr.Logger.debug(
            f"ParamMgr.add_client_response, message_type: {str(message_type)}, testcase_type: {str(testcase_type)}")

        if message_type in self.WorkingClientList:
            abc_message_type = self.WorkingClientList[message_type]
            if testcase_type in abc_message_type:
                abc = abc_message_type[testcase_type]
                abc.append(client)
            else:
                abc = [client]
                abc_message_type[testcase_type] = abc
        else:
            # not here, then add it
            # abc is a list of clients that have replied to this message_type
            abc = [client]
            abc_message_type = {testcase_type: abc}
            self.WorkingClientList[message_type] = abc_message_type

            aaa = 1

        # if client not in self.WorkingClientList:
        #     self.WorkingClientList.insert(0, client)

    # wait_for_client_response
    # this is how to make sure that all replies come from clients before going to the next step in the testcase
    def wait_for_client_response(self, message_type: MessageType, testcase_type: TestcaseType):

        start_time = datetime.now()
        if self.ParamMgr.stop_event.is_set():
            return

        if message_type in self.WorkingClientList:
            abc_message_type = self.WorkingClientList[message_type]
            if testcase_type in abc_message_type:
                abc = abc_message_type[testcase_type]

                # not self.ParamMgr.stop_event.is_set()
                # while not equal because a connection might drop and then the
                # masterclientclist will decrement on the socketclose
                while (len(self.MasterClientList) != len(self.WorkingClientList[message_type][testcase_type])
                       and not self.ParamMgr.stop_event.is_set()):  # did user click stop?
                    current_time = datetime.now()
                    time_difference = current_time - start_time
                    total_seconds = time_difference.total_seconds()
                    if total_seconds > self.ParamMgr.client_response_timeout:
                        break  # timeout occurred
                    else:
                        time.sleep(0.1)

                master_count = len(self.MasterClientList)
                abcde_count = len(abc)
                self.ParamMgr.Logger.debug(
                    f"ParamMgr.wait_for_client_response, master_count: {str(master_count)}, abc_count: {str(abcde_count)}")
                if len(self.MasterClientList) == len(abc):
                    return True
                else:
                    # subtract the reply list from the master list to get a list of who did not reply
                    abc_client_list = set(self.MasterClientList)-set(self.WorkingClientList[message_type][testcase_type])
                    for client in abc_client_list:
                        self.ParamMgr.Logger.error(f"Error: this client did not reply: {str(client)}")

                    self.ParamMgr.Logger.debug(
                        f"Warning, client failed response, message_type: {str(message_type)}, testcase_type: {str(testcase_type)}")
                    return False


# when we need to pass more classes around, well just add it to the class
class ParameterMgr:
    def __init__(self):
        self.is_server: bool = True

        # everybody needs to talk with eachother
        # we'll use ParamMgr to allow us to talk with each other
        self.NetworkMgr: NetworkMgr = None
        self.ConfigMgr: ConfigMgr = None
        self.ScriptEngine: ScriptEngine = None
        self.Logger: Logger = None
        # self.main_gui = None
        # self.main_connections = None
        # client_attendance is the list of clients
        self.client_attendance: ClientAttendance = ClientAttendance(self)  # to support multiple clients
        self.client_response_timeout = (60 * 1)  # 1 minute timeout, not long
        self.stop_event = threading.Event()

        # we can keep test statistics here
        self._client_ledger = {}

        # we can use variables in script to store point, int and string values
        self.script_items_point = {}
        self.script_items_int = {}
        self.script_items_string = {}



    # set_client_ledger will create a ledger for each client test_statistics
    # key is peer_info
    # value is test_statistics
    def set_client_ledger(self, key, value: ClientLedger = None):

        if key in self._client_ledger:
            abc = self._client_ledger[key]
            self.Logger.error(f"Warning, set_client_ledger already exists, key: {str(key)}, value: {str(abc)}")

        if value is not None:
            self.Logger.debug(f"set_client_ledger, key: {str(key)}, value: {str(value.test_statistics)}")
        else:
            value = ClientLedger(key)  # create a new ClientLedger

        self._client_ledger[key] = value

    # client_ledger to keep track of pass/fail responses
    # get_client_ledger
    def get_client_ledger(self, key):
        if key in self._client_ledger:
            abc = self._client_ledger[key]
            self.Logger.debug(f"get_client_ledger, key: {str(key)}, value: {str(abc.test_statistics)}")
            return abc
        else:
            self.Logger.error(f"Warning, get_client_ledger, ledger not found, key: {str(key)}")
            return None

    def del_client_ledger(self, key):
        if key in self._client_ledger:
            self._client_ledger.pop(key)

    def get_date_time(self):
        now = datetime.now()
        formatted_now = now.strftime("%Y.%m.%d %H:%M:%S")
        return formatted_now

    def get_log_path(self):
        a = self.simon_says  # mute not a static member
        cwd = os.getcwd()
        log_dir = os.path.join(cwd, '../logs')
        return log_dir

    def get_scripts_path(self):
        a = self.simon_says  # mute not a static member
        cwd = os.getcwd()
        script_dir = os.path.join(cwd, '../scripts')
        return script_dir

    def calculate_md5(self, filename):
        a = self.simon_says  # mute not a static member
        # Create an MD5 hash object
        md5_hash = hashlib.md5()
        md5_hexdigest = None

        try:
            # Open the file for reading in binary mode
            with open(filename, 'rb') as file:
                while True:
                    data = file.read(4096)  # Read data in 4KB chunks
                    if not data:
                        break
                    md5_hash.update(data)

            # Get the hexadecimal representation of the MD5 hash
            md5_hexdigest = md5_hash.hexdigest()

        except FileNotFoundError:
            self.Logger.error(f"FileNotFoundError, ParamMgr.calculate_md5, The file {filename} does not exist.")
        except IsADirectoryError:
            self.Logger.error(f"IsADirectoryError, ParamMgr.calculate_md5, {filename} is a directory.")
        except PermissionError:
            self.Logger.error(f"PermissionError, ParamMgr.calculate_md5, You do not have permission to read: {filename}.")
        except OSError as e:
            self.Logger.error(f"OSError, ParamMgr.calculate_md5: {e}")

        return md5_hexdigest

    # the scripts can have String, Int and Point
    # store these types of values in dictionaries
    # aaa[0] is value
    # aaa[1] is is_read_only
    def set_script_string(self, key, value, is_read_only=False):
        if key in self.script_items_string:
            aaa = self.script_items_string[key]
            if aaa[1] == False:
                aaa[0] = value
            else:
                raise ValueError('Error, value is static')
        else:
            aaa = [value, is_read_only]
            self.script_items_string[key] = aaa

    def get_script_string(self, key) -> str:
        if key in self.script_items_string:
            aaa = self.script_items_string[key]
            return aaa[0]
        else:
            return None

        # does the string exist

    def is_script_string(self, key) -> bool:
        if key in self.script_items_string:
            return True
        else:
            return False

    def get_script_string_str(self):
        result = ""
        for key, value in self.script_items_string:
            aaa = value
            result += f"key: {str(key)}, value: {str(aaa[0])}, is_read_only: {str(aaa[1])}; "
        return result

    def get_script_string_count(self) -> int:
        return len(self.script_items_string)

    def set_script_point(self, key, value, is_read_only=False):
        if key in self.script_items_point:
            aaa = self.script_items_point[key]
            if aaa[1] == False:
                aaa[0] = value
            else:
                raise ValueError('Error, value is static')
        else:
            aaa = [value, is_read_only]
            self.script_items_point[key] = aaa

    def get_script_point(self, key) -> Point:
        if key in self.script_items_point:
            aaa = self.script_items_point[key]
            return aaa[0]
        else:
            return None

        # does the string exist

    def is_script_point(self, key) -> bool:
        if key in self.script_items_point:
            return True
        else:
            return False

    def get_script_point_count(self):
        return len(self.script_items_point)

    def get_script_point_str(self):
        result = ""
        for key in self.script_items_point:
            aaa = self.script_items_point[key]
            point_b = aaa[0]
            result += f"key: {str(key)}, value: x={str(point_b.x)}, y={str(point_b.y)}, is_read_only: {str(aaa[1])}; "
        return result

    def set_script_int(self, key, value, is_read_only=False):
        if key in self.script_items_int:
            aaa = self.script_items_int[key]
            if aaa[1] == False:
                aaa[0] = value
            else:
                raise ValueError('Error, value is static')
        else:
            aaa = [value, is_read_only]
            self.script_items_int[key] = aaa

    def get_script_int(self, key) -> int:
        if key in self.script_items_int:
            aaa = self.script_items_int[key]
            return aaa[0]
        else:
            return None

        # does the string exist

    def is_script_int(self, key) -> bool:
        if key in self.script_items_int:
            return True
        else:
            return False

    def get_script_int_count(self) -> int:
        return len(self.script_items_int)

    def get_script_int_str(self):
        result = ""
        for key, value in self.script_items_int:
            aaa = value
            result += f"key: {str(key)}, value: {str(aaa[0])}, is_read_only: {str(aaa[1])}; "
        return result
