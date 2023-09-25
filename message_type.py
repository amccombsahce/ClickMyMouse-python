import json
from enum import Enum
import struct
import enum
from datetime import datetime


class MessageType(enum.Enum):
    INIT = 0x05
    KEEP_ALIVE = 0x10

    MAINTENANCE_REQUEST = 0x100
    MAINTENANCE_RESPONSE = 0x101

    TEST_CASE_REQEUST = 0x200  # execute test case step
    TEST_CASE_RESPONSE = 0x201

    TEST_CASE_VARIABLE_REQUEST = 0x202
    TEST_CASE_VARIABLE_RESPONSE = 0x203


class TestcaseType(enum.Enum):
    INIT = 0x5

    START_TEST = 0x10
    STOP_TEST = 0x11
    ROLL_LOGS = 0x12  # server and client rolls log files
    PRINT_SCN = 0x13  # take a screenshot
    GET_DATETIME = 0x14
    SOUND = 0x15  # have the computer go ding
    LOG = 0x16  # clients will log
    SLEEP = 0x17  # seconds to sleep, need to send to client??
    MEM_USAGE = 0x18

    RUN_SCRIPT = 0x40  # runs a subscript, need to send to client??
    #    RETURN = 22  # return from script after complete , need to send to client??

    EXECUTE_CMD = 0x41  # execute an os command (CreateProcess)
    KILL_CMD = 0x42

    HOME = 0x45  # set (x,y) coordinates as home
    MOVE_WINDOW = 0x46
    RESIZE_WINDOW = 0x47

    WAIT_FOR_IN_LOG_FILE = 0x50  # WaitForInLogFile
    WAIT_FOR_CREATE_FILE = 0x51  # used to wait for windows crash.dmp file

    MOUSE_MOVE = 0x55
    MOUSE_GETPOS = 0x56  # get (x,y) position of mouse  a.k.a. GetCursorPos
    MOUSE_SCROLL = 0x57
    MOUSE_RIGHT_CLICK = 0x58
    MOUSE_MIDDLE_CLICK = 0x59
    MOUSE_LEFT_CLICK = 0x60
    MOUSE_LEFT_DOUBLE_CLICK = 0x61
    MOUSE_LEFT_TRIPLE_CLICK = 0x62
    MOUSE_CLICK_LEFT_DOWN = 0x63
    MOUSE_CLICK_LEFT_UP = 0x64
    MOUSE_CLICK_RIGHT_DOWN = 0x65
    MOUSE_CLICK_RIGHT_UP = 0x66

    KEYBOARD_PRESS = 0x70
    KEYBOARD_DOWN = 0x71
    KEYBOARD_UP = 0x72
    KEYBOARD_HOTPRESS = 0x73  # Alt, Ctrl, Shift

    FIND_NEWEST_FILE = 0x100
    FIND_NEWEST_FOLDER = 0x101
    CREATE_FILE = 0x102
    APPEND_FILE = 0x103
    COPY_FILE = 0x104
    MOVE_FILE = 0x105
    DEL_FILE = 0x106

    VALIDATE_XML_FILE = 0x300
    UNINSTALL_WINDOWS_APPLICATION = 0x400
    CREATE_SHORTCUT_FILE = 0x401  # create windows .lnk file


class TestcaseVariableType(enum.Enum):
    INIT = 1
    INT = 10
    STRING = 11
    POINT = 12


class TestcaseTypeData(enum.Enum):
    debug = 1

    @property
    def DATA_SOUND(self):
        return 'filename' if self.debug else '12'  # using same numbers as TestcaseType

    @property
    def MOUSE_SCROLL(self):
        return 'amount_to_scroll' if self.debug else '43'  # using same numbers as TestcaseType


class Message:
    def __init__(self, message_type: MessageType):
        # message_type: for type of message to unpack
        if not isinstance(message_type, MessageType):
            raise ValueError('message_type must be an instance of MessageType Enum')
        self.message_type = message_type

    def encode(self):
        try:
            # return json.dumps(self.__dict__, default=lambda x: x.value).encode('utf-8')
            return json.dumps(self.__dict__, default=lambda x: x.value).encode('utf-8')
        except KeyError as e:
            print(f"Error, Message.encode : {str(e)}")

    @classmethod
    def decode(cls, json_bytes):
        json_decode = json.loads(json_bytes.decode('utf-8'))
        return cls(MessageType(json_decode['message_type']))


class KeepAliveMessage(Message):
    def __init__(self):
        super().__init__(MessageType.KEEP_ALIVE)
        self.time = datetime.now().strftime('%Y.%m.%d %H:%M:%S')

    def encode(self):
        try:
            # return json.dumps(self.__dict__, default=lambda x: x.value).encode('utf-8')
            return json.dumps(self.__dict__, default=lambda x: x.value).encode('utf-8')
        except KeyError as e:
            print(f"Error, Message.encode : {str(e)}")

    @classmethod
    def decode(cls, json_bytes):
        data_object = json.loads(json_bytes.decode('utf-8'))
        return data_object


class TestcaseVariableTypeMessage(Message):
    def __init__(self, message_type: MessageType = MessageType.TEST_CASE_VARIABLE_REQUEST,
                 testcase_variable_type: TestcaseVariableType = None, data=None):
        super().__init__(message_type)
        if not isinstance(testcase_variable_type, TestcaseVariableType):
            raise ValueError(
                'ValueError, MessageType.TestcaseVariableTypeMessage, testcase_variable_type TestcaseVariableType Enum')

        self.testcase_variable_type = testcase_variable_type
        self.data = data

    @classmethod
    def decode(cls, json_bytes):
        data_object = json.loads(json_bytes.decode('utf-8'))
        message_type = MessageType(data_object['message_type'])
        testcase_variable_type = TestcaseVariableType(data_object['testcase_variable_type'])
        abc_data = data_object['data']

        return cls(message_type=message_type, testcase_variable_type=testcase_variable_type, data=abc_data)


class MaintenanceMessage(Message):
    def __init__(self, message_type: MessageType = MessageType.INIT, step_number=0,
                 testcase_type: TestcaseType = TestcaseType.INIT, status_is_pass=False, data=None):
        super().__init__(message_type)
        if not isinstance(testcase_type, TestcaseType):
            raise ValueError(
                'ValueError, MaintenanceMessage, MessageType.TestcaseMessage, TestcaseType Enum')
        self.testcase_type = testcase_type
        self.status_is_pass = status_is_pass
        self.data = data  # for extra information, such as filename for PrintScreen

    @classmethod
    def decode(cls, json_bytes):
        data_object = json.loads(json_bytes.decode('utf-8'))
        message_type = MessageType(data_object['message_type'])
        testcase_type = TestcaseType(data_object['testcase_type'])
        data = data_object['data']
        status_is_pass = data_object['status_is_pass']

        return cls(message_type=message_type, testcase_type=testcase_type, data=data, status_is_pass=status_is_pass)


class TestcaseMessage(Message):  # stepnumber=0, stepaction=0)
    def __init__(self, message_type: MessageType = MessageType.INIT, step_number=0,
                 testcase_type: TestcaseType = TestcaseType.INIT, data=None, status_is_pass=False):
        super().__init__(message_type)
        if not isinstance(testcase_type, TestcaseType):
            raise ValueError(
                'ValueError, TestcaseMessage, MessageType.TestcaseMessage, TestcaseType Enum')
        self.step_number = step_number
        self.testcase_type = testcase_type
        self.data = data  # for extra information, such as x,y for movemouse, or return codes from clients
        self.status_is_pass = status_is_pass  # testcase fail, or error

    def encode(self):
        try:
            return json.dumps(self.__dict__, default=lambda x: x.value).encode('utf-8')
        except KeyError as e:
            print(f"Error, Message.encode : {str(e)}")

    @classmethod
    def decode(cls, json_bytes):

        data_object = json.loads(json_bytes.decode('utf-8'))
        message_type = MessageType(data_object['message_type'])
        testcase_type = TestcaseType(data_object['testcase_type'])
        step_number = data_object['step_number']
        data = data_object['data']
        status_is_pass = data_object['status_is_pass']

        print(
            f"step_number: {str(step_number)}, testcase_type: {str(testcase_type)}, data: {str(data)}, status_is_pass: {str(status_is_pass)}")
        # return TestcaseMessage(step_number=step_number, testcase_type=testcase_type, data=data)
        return cls(message_type=message_type, step_number=step_number, testcase_type=testcase_type, data=data,
                   status_is_pass=status_is_pass)
