import re
import os
# from wait_for_in_Log_File import WaitForInLogFile
# from Logger import Logger
import time
# import pygame
# import json
import pyautogui
# from datetime import datetime
import vlc
from file_mgr import FileMgr
from message_type import *  # MessageType, TestcaseType, TestcaseMessage, TestcaseTypeData, TestcaseVariableType, R
from point_type import Point
from wait_for_me import wait_for_me
import subprocess


# from param_mgr import Param_Mgr

# from main import *

# ScriptEngine is used to store the script when it is read in from a flat file.


class ScriptEngine:

    def __init__(self, param_mgr):
        self.ParamMgr = param_mgr
        self.ParamMgr.Logger.debug("ScriptEngine.__init__")
        self.script = {}
        self.is_run = False
        self.is_paused = True  # pause will hold the ScriptMgr.run
        self.stop_event = None

    def move_window_to_position(self, window_title, x, y):
        try:
            # Use wmctrl to get the window ID by title
            window_id = subprocess.check_output(['wmctrl', '-l', '-x', '-G', '-p'], universal_newlines=True)
            for line in window_id.splitlines():
                if window_title in line:
                    # Extract the window ID
                    window_id = line.split()[0]

                    # Use wmctrl to move the window to the specified position (1234, 567)
                    subprocess.call(['wmctrl', '-ir', window_id, '-e', f'0,{x},{y},-1,-1'])

                    print(f"Moved '{window_title}' to position ({x}, {y}).")
                    return
            print(f"Window with title '{window_title}' not found.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def set_stop_event(self, stop_event):
        self.stop_event = stop_event

    def set_run(self, to_run):
        self.ParamMgr.Logger.debug(f"ScriptEngine.set_run {to_run}")
        self.is_run = to_run

    def set_pause(self, to_pause):
        self.ParamMgr.Logger.debug(f"ScriptEngine.set_pause {to_pause}")
        self.is_paused = to_pause

    def is_pause(self):
        self.ParamMgr.Logger.debug("ScriptEngine.is_pause")
        return self.is_paused

    def clearscript(self):
        self.ParamMgr.Logger.debug("ScriptEngine.clearscript")
        self.script.clear()

    def load_script(self, scriptfilename):
        self.ParamMgr.Logger.debug("ScriptEngine.loadscript")
        file_mgr = FileMgr()
        script = file_mgr.ParseScriptFile(scriptfilename)
        self.add(script)

    def add(self, command):
        self.ParamMgr.Logger.debug("ScriptEngine.add")
        # python is zero base but reading in files start at one, add one to the key
        # to keep line reporting to the same base as the script file
        if isinstance(command, list):
            for ii in command:
                self.script[len(self.script) + 1] = ii
        else:
            self.script[len(self.script) + 1] = command

    def run(self):
        self.ParamMgr.Logger.debug("ScriptEngine.run")

        # TODO put here if user selected Repeat test checkbox.
        self.send_maintenance_client(MessageType.MAINTENANCE_REQUEST, TestcaseType.START_TEST)

        self.run_script()

        self.send_maintenance_client(MessageType.MAINTENANCE_REQUEST, TestcaseType.STOP_TEST)
        # TODO put here endif Repeat is checked

        self.ParamMgr.Logger.debug("ScriptEngine.run, all-done")
        self.is_run = False
        self.is_paused = True
        self.ParamMgr.main_gui.run_clicked()  # reset the Stop button to Run button

    def run_script(self):
        self.ParamMgr.Logger.debug("ScriptEngine.run_script")
        if len(self.script) > 0:
            if self.is_run:
                for ii in self.script:
                    while self.is_paused:
                        time.sleep(0)
                    if self.stop_event is not None:
                        if self.stop_event.is_set():
                            break
                    self.server_runscript_cmd(ii, self.script[ii])
                    # self.send_script_client(ii, self.script[ii])

    # send_maintenance_client
    # send a message type that is outside testcase
    def send_maintenance_client(self, message_type: MessageType = MessageType.INIT,
                                testcase_type: TestcaseType = TestcaseType.INIT, data=None):
        if not isinstance(testcase_type, TestcaseType):
            raise ValueError('ValueError, ScriptEngine.send_maintenance_client, TestcaseType Enum')

        self.ParamMgr.Logger.debug(f"ScriptEngine.send_maintenance_client: "  # ,{str(testcase_variable)},"
                                   f" with data: {str(data)}")

        self.ParamMgr.client_attendance.clear_client_response()

        if data is not None:
            abc = 2

        self.ParamMgr.NetworkMgr.send_maintenance_message(message_type=message_type, testcase_type=testcase_type,
                                                          data=data)

        client_response = self.ParamMgr.client_attendance.wait_for_client_response()

        if not client_response:
            self.ParamMgr.Logger.warning(
                f"Warning, ScriptEngine.send_maintenance_client: timeout from no response")

    def send_testcase_client(self, stepcount: int, testcase_type: TestcaseType, data=None):
        if not isinstance(testcase_type, TestcaseType):
            raise ValueError('ValueError, ScriptEngine.send_testcase_client, TestcaseType Enum')

        self.ParamMgr.Logger.debug(f"ScriptEngine.send_testcase_client: ,{str(testcase_type)},"
                                   f" with stepcount: {str(stepcount)}")
        self.ParamMgr.client_attendance.clear_client_response()
        self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_REQEUST,
                                                       step_number=stepcount,
                                                       testcase_type=testcase_type,
                                                       data=data)

        client_response = self.ParamMgr.client_attendance.wait_for_client_response()

        if not client_response:
            self.ParamMgr.Logger.warning(
                f"Warning, ScriptEngine.send_testcase_client: timeout from no response")

    # send_variable_client
    # send a variable to the clients
    def send_variable_client(self, testcase_variable_type: TestcaseVariableType = None, data=None):
        self.ParamMgr.Logger.debug(f"ScriptEngine.send_variable_client: "  # ,{str(testcase_variable)},"
                                   f" with data: {str(data)}")
        self.ParamMgr.client_attendance.clear_client_response()

        self.ParamMgr.NetworkMgr.send_variable_message(MessageType.TEST_CASE_VARIABLE_REQUEST,
                                                       testcase_variable_type=testcase_variable_type, data=data)

        client_response = self.ParamMgr.client_attendance.wait_for_client_response()

        if not client_response:
            self.ParamMgr.Logger.warning(
                f"Warning, ScriptEngine.send_testcase_client: timeout from no response")

    # client_maintenance_cmd
    # message to client
    # out of testcase actions like screenshots and roll client log files
    def client_maintenance_cmd(self, maintenance_message: MaintenanceMessage, data=None):
        if not isinstance(maintenance_message, MaintenanceMessage):
            raise ValueError(
                'ValueError, ScriptEngine.client_maintenance_cmd, MaintenanceMessage Enum')

        testcase_type = maintenance_message.testcase_type
        data_object = maintenance_message.data

        self.ParamMgr.Logger.debug("ScriptEngine.client_maintenance_cmd")
        self.ParamMgr.Logger.info(f"command: {str(testcase_type)}")

        # TestcaseMessage has status for pass/fail, initialize as Fail
        status_is_pass = False

        try:
            if testcase_type == TestcaseType.INIT:
                self.ParamMgr.Logger.debug("ScriptEngine.client_maintenance_cmd.INIT")
                abc = 1
                # TODO do stuff so that we know that the client has connected
                #
                status_is_pass = True
                self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.INIT_RESPONSE,
                                                                  testcase_type=testcase_type,
                                                                  status_is_pass=status_is_pass)
            elif testcase_type == TestcaseType.PRINT_SCN:
                self.ParamMgr.Logger.debug("ScriptEngine.client_maintenance_cmd.PRINT_SCN")

                log_dir = self.ParamMgr.get_log_path()

                filename = None

                # check if user wants a different filename
                if data_object is not None:
                    if 'filename' in data_object:
                        filename = data_object['filename']
                        # check if a String was given instead of a quoted filename
                        if self.ParamMgr.is_script_string(filename):
                            filename = self.ParamMgr.get_script_string(filename)
                else:
                    # user did not specify filename, the default filename has timestamp as part of the name
                    abc = datetime.now().strftime('%y%m%d_%H%M%S')
                    filename = f"screenshot_{abc}.png"

                filepath = os.path.join(log_dir, filename)
                self.ParamMgr.Logger.info(f"ScriptEngine.client_maintenance_cmd.PRINT_SCN, saving to: {str(filepath)}")

                try:
                    pyautogui.screenshot(filepath)
                except AttributeError as e:
                    self.ParamMgr.Logger.error(
                        f"AttributeError, ScriptEngine.client_maintenance_cmd.PRINT_SCN, saving to: {str(filepath)}")
                except ValueError as e:
                    self.ParamMgr.Logger.error(
                        f"ValueError Error, ScriptEngine.client_maintenance_cmd.PRINT_SCN, saving to: {str(filepath)}")

                # Take screenshot
                # screenshot = pyautogui.screenshot(filepath)
                # Save the image
                # screenshot.save(filepath)

                # send the path back to the server
                abc_data = {'filename': filepath}

                status_is_pass = True

                self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                  testcase_type=testcase_type,
                                                                  status_is_pass=status_is_pass,
                                                                  data=abc_data)

            elif testcase_type == TestcaseType.SOUND:
                self.ParamMgr.Logger.debug("ScriptEngine.client_maintenance_cmd.SOUND")

                # using pygame library,
                # pygame.mixer.init()

                # default file
                sound_filename = 'ding.wav'  # default

                # check if user wants a different filename
                if data_object is not None:
                    if TestcaseTypeData.DATA_SOUND in data_object:
                        sound_filename = data_object[TestcaseTypeData.DATA_SOUND]

                self.ParamMgr.Logger.info(
                    f"ScriptEngine.client_maintenance_cmd.SOUND, filename: {str(sound_filename)}")

                if os.path.exists(sound_filename):
                    # sound = pygame.mixer.Sound(filepath)
                    # sound = pygame.mixer.Sound('ding.wav')
                    # sound.play()
                    # p = vlc.MediaPlayer(filepath)
                    p = vlc.MediaPlayer(sound_filename)
                    status = p.play()
                    # play returns 0 when started to play
                    # play returns -1 with error
                    if status != -1:
                        status_is_pass = True
                else:
                    self.ParamMgr.Logger.error(
                        f"ScriptEngine.client_maintenance_cmd.SOUND, Error, file not found: {str(sound_filename)}")

                self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                  testcase_type=testcase_type,
                                                                  status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.START_TEST:
                self.ParamMgr.Logger.info("ScriptEngine.client_maintenance_cmd.START_TEST")  # info logging se we know
                status_is_pass = True
                # TODO do stuff so that client will know when to start accepting commands
                self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                  testcase_type=testcase_type,
                                                                  status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.STOP_TEST:
                self.ParamMgr.Logger.info("ScriptEngine.client_maintenance_cmd.STOP_TEST")  # info logging se we know
                status_is_pass = True
                # TODO do stuff so that client will know when to stop accepting commands
                self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                  testcase_type=testcase_type,
                                                                  status_is_pass=status_is_pass)


            else:
                self.ParamMgr.Logger.error(f"Error, u=ScriptEngine.client_maintenance_cmd, unknown testcase_type: {str(testcase_type)}")

        except AttributeError as e:
            self.ParamMgr.Logger.error(
                f"AttributeError, ScriptEngine.client_maintenance_cmd")

        except ValueError as e:
            self.ParamMgr.Logger.error(
                f"ValueError Error, ScriptEngine.client_maintenance_cmd")

    # client_variable_cmd
    # messages to client
    # save variables on local client, incase system specific, keep is seperate from other systems under test
    def client_variable_cmd(self, testcase_variabletype_message: TestcaseVariableTypeMessage = None):
        if not isinstance(testcase_variabletype_message, TestcaseVariableTypeMessage):
            raise ValueError(
                'ValueError, ScriptEngine.client_variable_cmd, TestcaseVariableMessage Enum')

        testcase_variable_type = testcase_variabletype_message.testcase_variable_type
        variable_data = testcase_variabletype_message.data  # get data

        variable_name = None
        variable_value = None
        is_static = False

        if 'variable_name' in variable_data:
            variable_name = variable_data['variable_name']

        if 'variable_value' in variable_data:
            variable_value = variable_data['variable_value']

        if 'static' in variable_data:
            is_static = variable_data['static']

        if testcase_variable_type == TestcaseVariableType.INT:
            if is_static:  # if static, only insert if it does not already exist, change value is not allowed
                if not self.ParamMgr.is_script_int(variable_name):
                    self.ParamMgr.set_script_int(variable_name, int(variable_value))
            else:
                self.ParamMgr.set_script_int(variable_name, int(variable_value))

        if testcase_variable_type == TestcaseVariableType.STRING:
            if is_static:  # if static, only insert if it does not already exist, change value is not allowed
                if not self.ParamMgr.is_script_string(variable_name):
                    self.ParamMgr.set_script_string(variable_name, str(variable_value))
            else:
                self.ParamMgr.set_script_string(variable_name, str(variable_value))

        if testcase_variable_type == TestcaseVariableType.POINT:
            if is_static:  # if static, only insert if it does not already exist, change value is not allowed
                if not self.ParamMgr.is_script_point(variable_name):
                    self.ParamMgr.set_script_point(variable_name, Point(variable_value))
            else:
                self.ParamMgr.set_script_point(variable_name, Point(variable_value))

        self.ParamMgr.NetworkMgr.send_variable_message(MessageType.TEST_CASE_VARIABLE_RESPONSE,
                                                       testcase_variable_type=testcase_variable_type)

    # client_runscript_cmd
    # runs on client socket thread
    #
    def client_runscript_cmd(self, testcase_message: TestcaseMessage):  # client received command
        if not isinstance(testcase_message, TestcaseMessage):
            raise ValueError(
                'ValueError, ScriptEngine.client_runscript_cmd, TestcaseMessage Enum')

        step_number = testcase_message.step_number
        testcase_type = testcase_message.testcase_type
        data_object = testcase_message.data

        self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd")
        self.ParamMgr.Logger.info(f"stepcount: {str(step_number)}, command: {str(testcase_type)}")

        # TestcaseMessage has status for pass/fail, initialize as Fail
        status_is_pass = False

        try:
            if testcase_type == TestcaseType.INIT:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.INIT")
                abc = 1

            elif testcase_type == TestcaseType.SOUND:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.SOUND")

                # using pygame library,

                # pygame.mixer.init()

                # default file
                sound_filename = 'ding.wav'  # default

                # check if user wants a different filename
                if data_object is not None:
                    if TestcaseTypeData.DATA_SOUND in data_object:
                        sound_filename = data_object[TestcaseTypeData.DATA_SOUND]

                cwd = os.getcwd()
                filepath = os.path.join(cwd, sound_filename)

                if os.path.exists(filepath):
                    # sound = pygame.mixer.Sound(filepath)
                    # sound = pygame.mixer.Sound('ding.wav')
                    # sound.play()
                    # p = vlc.MediaPlayer(filepath)
                    p = vlc.MediaPlayer(sound_filename)
                    p.play()

                    status_is_pass = True
                else:
                    self.ParamMgr.Logger.error(
                        f"ScriptEngine.client_runscript_cmd.SOUND, Error, file not found: {str(filepath)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.PRINT_SCN:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.PRINT_SCN")

                log_dir = self.ParamMgr.get_log_path()

                filename = None

                # check if user wants a different filename
                if data_object is not None:
                    if 'filename' in data_object:
                        filename = data_object['filename']
                        # check if a String was given instead of a quoted filename
                        if self.ParamMgr.is_script_string(filename):
                            filename = self.ParamMgr.get_script_string(filename)
                else:
                    # user did not specify filename, the default filename has timestamp as part of the name
                    abc = datetime.now().strftime('%y%m%d_%H%M%S')
                    filename = f"screenshot_{abc}.png"

                filepath = os.path.join(log_dir, filename)
                self.ParamMgr.Logger.info(f"ScriptEngine.client_runscript_cmd.PRINT_SCN, saving to: {str(filepath)}")

                try:
                    pyautogui.screenshot(filepath)
                except AttributeError as e:
                    self.ParamMgr.Logger.error(
                        f"AttributeError, ScriptEngine.client_runscript_cmd.PRINT_SCN, saving to: {str(filepath)}")
                except ValueError as e:
                    self.ParamMgr.Logger.error(
                        f"ValueError Error, ScriptEngine.client_runscript_cmd.PRINT_SCN, saving to: {str(filepath)}")

                # Take screenshot
                # screenshot = pyautogui.screenshot(filepath)
                # Save the image
                # screenshot.save(filepath)

                # send the path back to the server
                abc_data = {'filename': filepath}

                status_is_pass = True

                self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.TEST_CASE_RESPONSE,
                                                                  testcase_type=testcase_type,
                                                                  status_is_pass=status_is_pass,
                                                                  data=abc_data)

            elif testcase_type == TestcaseType.SLEEP:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.SLEEP")

                self.ParamMgr.Logger.info(f"sleeping")

                status_is_pass = True

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_MOVE:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOUSE_MOVE")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])
                    if 'point' in data_object:
                        point_name = data_object['point']

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                self.ParamMgr.Logger.info(f"MouseMove: x= {str(x_pos)}, y= {str(y_pos)}")

                try:
                    x = x_pos
                    y = y_pos
                    pyautogui.moveTo(x, y)
                    pyautogui.sleep(0.1)  # allow time to get new
                    new_x, new_y = pyautogui.position()  # check the position that it moved to

                except OSError as e:
                    self.ParamMgr.Logger.error(f"OSError, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                except pyautogui.PyAutoGUIException as e:
                    self.ParamMgr.Logger.error(f"PyAutoGUIException, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                if new_x == x_pos and new_y == y_pos:
                    status_is_pass = True
                else:
                    self.ParamMgr.Logger.warning(f"Warning, MouseMove to: x= {str(new_x)}, y= {str(new_y)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_SCROLL:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOUSE_SCROLL")
                # MouseScroll(amount, x, y), amount can be a negative number to scroll down, positive number scrolls up
                x_pos = 0
                y_pos = 0
                point_name = None
                amount_to_scroll = 1  # default is 1

                if data_object is not None:
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'amount_to_scroll' in data_object:
                        amount_to_scroll = int(data_object['amount_to_scroll'])

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseScroll:  x= {str(x_pos)}, y= {str(y_pos)},"
                                              f" amount_to_scroll= {str(amount_to_scroll)}")

                    try:
                        pyautogui.scroll(amount_to_scroll, x=x_pos, y=y_pos)
                        status_is_pass = True
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_GETPOS:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOUSE_GETPOS")
                # MouseGetPos()
                # MouseGetPos(Point)
                current_position = pyautogui.position()

                # send current_position back the pos to the server
                x_pos = current_position[0]
                y_pos = current_position[1]
                abc_data = {'x': str(x_pos), 'y': str(y_pos)}

                # if we got here, then it was successful
                status_is_pass = True

                # show the user
                self.ParamMgr.Logger.info(f"MouseGetPos:  x= {str(x_pos)}, y= {str(y_pos)}")

                # store the value to the local variable, only if requested by supplying the point name
                if data_object is not None:
                    if 'point' in data_object:
                        variable_name = data_object['point']
                        point = Point(x_pos, y_pos)  # create the point

                        # if self.ParamMgr.is_script_point(variable_name): # TODO check if variable is static
                        self.ParamMgr.set_script_point(variable_name, point)  # store the value in variable_name Point

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               data=abc_data, testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_LEFT_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOUSE_LEFT_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])
                    if 'point' in data_object:
                        point_name = data_object['point']

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                    try:
                        pyautogui.click(x=x_pos, y=y_pos)
                        status_is_pass = True
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_RIGHT_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOUSE_RIGHT_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])
                    if 'point' in data_object:
                        point_name = data_object['point']

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseRightClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    try:
                        pyautogui.rightClick(x=x_pos, y=y_pos)
                        status_is_pass = True
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")


                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_MIDDLE_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOUSE_MIDDLE_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])
                    if 'point' in data_object:
                        point_name = data_object['point']

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseMiddleClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                    try:
                        pyautogui.middleClick(x=x_pos, y=y_pos)
                        status_is_pass = True
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_LEFT_DOUBLE_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOUSE_LEFT_DOUBLE_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])
                    if 'point' in data_object:
                        point_name = data_object['point']

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseDoubleClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    try:
                        pyautogui.doubleClick(x=x_pos, y=y_pos)
                        status_is_pass = True
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_LEFT_TRIPLE_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOUSE_LEFT_TRIPLE_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])
                    if 'point' in data_object:
                        point_name = data_object['point']

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseTripleClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                    try:
                        pyautogui.tripleClick(x=x_pos, y=y_pos)
                        status_is_pass = True
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOVE_WINDOW:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.MOVE_WINDOW")

                x_pos = 0
                y_pos = 0
                window_name = None

                if data_object is not None:
                    if 'window_name' in data_object:
                        window_name = str(data_object['window_name'])
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

                    self.ParamMgr.Logger.info(
                        f"MoveWindow: window= {str(window_name)}, x= {str(x_pos)}, y= {str(y_pos)}")

                    # window = pyautogui.getWindowsWithTitle(window_name)[0]
                    # window.move(x_pos, y_pos)

                    # hwnd = win32gui.FindWindow(None, window_name)
                    # win32gui.SetWindowPos(hwnd, ) (hwnd, x_pos, y_pos, 0, 0, 0, SWP_NOSIZE)

                    try:
                        self.move_window_to_position(window_name, x_pos, y_pos)
                        status_is_pass = True
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")


                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.KEYBOARD_PRESS:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.KEYBOARD_PRESS")

                keyboard_press = None

                if data_object is not None:
                    if 'keyboard_press' in data_object:
                        keyboard_press = str(data_object['keyboard_press'])

                    self.ParamMgr.Logger.info(
                        f"Keyboard press: key= {str(keyboard_press)}")

                    try:
                        #pyautogui.typewrite(keyboard_press, interval=0.25)
                        pyautogui.press(keyboard_press)
                        status_is_pass = True
                    except ValueError as e:
                        self.ParamMgr.Logger.error(f"ValueError, KeyboardPress, keyboard_press= {str(keyboard_press)}")
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, KeyboardPress, keyboard_press= {str(keyboard_press)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, keyboard_press= {str(keyboard_press)}")


                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.KEYBOARD_DOWN:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.KEYBOARD_DOWN")

                keyboard_press = None

                if data_object is not None:
                    if 'keyboard_press' in data_object:
                        keyboard_press = str(data_object['keyboard_press'])

                    self.ParamMgr.Logger.info(
                        f"Keyboard press: key= {str(keyboard_press)}")

                    try:
                        abc = 'ctrl'
                        pyautogui.keyDown(abc)
                        # pyautogui.keyDown(keyboard_press)
                        #pyautogui.press(keyboard_press)
                        status_is_pass = True
                        abc01 = abc == keyboard_press
                        print(f"keydown: ctrl= {str(abc01)}")

                    except ValueError as e:
                        self.ParamMgr.Logger.error(f"ValueError, KeyboardDown, keyboard_down= {str(keyboard_press)}")
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, KeyboardDown, keyboard_down= {str(keyboard_press)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, keyboard_down= {str(keyboard_press)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.KEYBOARD_UP:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.KEYBOARD_UP")

                keyboard_press = None

                if data_object is not None:
                    if 'keyboard_press' in data_object:
                        keyboard_press = str(data_object['keyboard_press'])

                    self.ParamMgr.Logger.info(
                        f"Keyboard press: key= {str(keyboard_press)}")

                    try:
                        abc = 'ctrl'
                        pyautogui.keyUp(abc)
                        #pyautogui.keyUp(keyboard_press)
                        status_is_pass = True
                        abc01 = abc == keyboard_press
                        print(f"keyup: ctrl= {str(abc01)}")
                    except ValueError as e:
                        self.ParamMgr.Logger.error(f"ValueError, KeyboardDown, keyboard_up= {str(keyboard_press)}")
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, KeyboardDown, keyboard_up= {str(keyboard_press)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, keyboard_up= {str(keyboard_press)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.KEYBOARD_HOTPRESS:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.KEYBOARD_HOTPRESS")

                keyboard_press = None
                keyboard_press_1 = None
                keyboard_press_2 = None
                keyboard_press_3 = None

                if data_object is not None:
                    if 'keyboard_press_1' in data_object:
                        keyboard_press_1 = str(data_object['keyboard_press_1'])
                    if 'keyboard_press_2' in data_object:
                        keyboard_press_2 = str(data_object['keyboard_press_2'])
                    if 'keyboard_press_3' in data_object:
                        keyboard_press_3 = str(data_object['keyboard_press_3'])

                    if keyboard_press_3 is not None:
                        self.ParamMgr.Logger.info(
                            f"Keyboard hotkey= {str(keyboard_press_1)} + {str(keyboard_press_2)} + {str(keyboard_press_3)}")
                    else:
                        self.ParamMgr.Logger.info(
                            f"Keyboard hotkey= {str(keyboard_press_1)} + {str(keyboard_press_2)}")

                    try:
                        if keyboard_press_3 is not None:
                            pyautogui.hotkey(keyboard_press_1, keyboard_press_2, keyboard_press_3)
                        else:
                            pyautogui.hotkey(keyboard_press_1, keyboard_press_2)
                        status_is_pass = True

                    except ValueError as e:
                        self.ParamMgr.Logger.error(f"ValueError, KeyboardDown, hotpress= {str(keyboard_press_1)} + {str(keyboard_press_2)}")
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError, KeyboardDown, hotpress= {str(keyboard_press_1)} + {str(keyboard_press_2)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException, hotpress= {str(keyboard_press_1)} + {str(keyboard_press_2)}")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.WAIT_FOR_IN_LOG_FILE:
                self.ParamMgr.Logger.debug("ScriptEngine.client_runscript_cmd.WAIT_FOR_IN_LOG_FILE")

                timeout = 60  # default

                if data_object is not None:
                    if 'filename' in data_object:
                        filename = data_object['filename']
                    else:
                        self.ParamMgr.Logger.error(f"Error, Script.Engine.client_runscript_cmd: missing filename")

                    if 'wait_for_text' in data_object:
                        waitfortext = data_object['wait_for_text']
                    else:
                        self.ParamMgr.Logger.error(f"Error, Script.Engine.client_runscript_cmd: missing wait_for_text")

                    if data_object is not None:
                        if 'time_out' in data_object:
                            timeout = int(data_object['time_out'])

                    self.ParamMgr.Logger.info(
                        f"WaitForInFile: filename: {str(filename)}, wait_for_text: {str(waitfortext)}")

                    waitforme = wait_for_me(filename, waitfortext, timeout)
                    result = waitforme.run()

                    self.ParamMgr.Logger.debug(f"Script.Engine.client_runscript_cmd: competed: {str(result)}")

                    if result:
                        self.ParamMgr.Logger.info(f"WaitForInLogFile: found text: {str(self.waitfortext)}")
                        status_is_pass = True
                    else:
                        self.ParamMgr.Logger.warning(
                            f"Warning, WaitForInLogFile: did not find text: {str(self.waitfortext)}")

                else:
                    self.ParamMgr.Logger.error(f"Error, Script.Engine.client_runscript_cmd: invalid  WaitForInLogFile")

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)


            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.client_runscript_cmd: unknown testcase_message: {str(testcase_message.value)}")

        except TypeError as e:
            self.ParamMgr.Logger.error(f"TypeError, Script.Engine.client_runscript_cmd: TypeError: {str(e)}")
            self.ParamMgr.Logger.error(
                f"Error, Script.Engine.client_runscript_cmd: step_number: {str(step_number)}, testcase_type: {str(testcase_type)}")
        except OSError as e:
            self.ParamMgr.Logger.error(f"OSError, Script.Engine.client_runscript_cmd: OSError: {str(e)}")
            self.ParamMgr.Logger.error(
                f"Error, Script.Engine.client_runscript_cmd: step_number: {str(step_number)}, testcase_type: {str(testcase_type)}")
        except Exception as e:
            self.ParamMgr.Logger.error(f"Exception Error, Script.Engine.client_runscript_cmd: {str(e)}")
            self.ParamMgr.Logger.error(
                f"Error, Script.Engine.client_runscript_cmd: step_number: {str(step_number)}, testcase_type: {str(testcase_type)}")

    # server_runscript_cmd
    # runs on server socket thread,
    #
    def server_runscript_cmd(self, stepcount, command):  # server parses the .script file and sends codes to client
        self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd")

        pattern = ['(', ')', '=', ' ', '"', ',']
        # convert the command to a list of words
        words = [str for str in re.split('|'.join(map(re.escape, pattern)), command) if str]

        # Point, String, INT can be Static
        if 'static' in words:
            words.remove('static')  # remove it from the first line so that the opcode is String and not Static
            words.append('static')  # move static to the last item so that it doesn't mess up opcode:

        # get the opcode
        opcode: object = words[0]

        # show the opecode to the user
        self.ParamMgr.Logger.info(f"ScriptEngine.server_runscript_cmd, opcode: {str(opcode)}")

        # sleep, we can sleep here, we don't need to send it to the clients
        if opcode == "Sleep":
            # sleep(x)
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.sleep")
            print("Sleep")

            # let the clients know we are sleeping
            self.send_testcase_client(stepcount, TestcaseType.SLEEP)

            if len(words) > 1:
                timer = int(words[1])
                self.ParamMgr.Logger.info(f"ScriptEngine.server_runscript_cmd: sleep: {str(timer)} seconds")
                time.sleep(timer)
            else:
                self.ParamMgr.Logger.error(f"Error: ScriptEngine.server_runscript_cmd invalid sleep: {str(command)}")

        elif opcode == "Sound":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.Sound")
            # Sound() # default sound is "ding.wav"
            # Sound(String)
            # Sound("dingding.wav")

            sound_data = None

            if len(words) > 1:  # 'filename'
                sound_data = {
                    TestcaseTypeData.DATA_SOUND: str(words[1])}  # filename of sound file to play 'ding.wav' is default

            self.ParamMgr.Logger.info(f"ScriptEngine.server_runscript_cmd: Sound, data= {str(sound_data)}")

            self.send_maintenance_client(MessageType.MAINTENANCE_REQUEST, testcase_type=TestcaseType.SOUND,
                                         data=sound_data)

        elif opcode == "GetDateTime":
            abc = 1
        elif opcode == "Log":
            abc = 1
        elif opcode == "PrintScreen":
            # PrintScreen() # use default filebame saving
            # PrintScreen(String) # save file in user specfied filename
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.PrintScn")
            # default screenshot filename is "screenshot_<datetime>.png"

            print_screen_data = None

            if len(words) > 1:
                print_screen_data = {'filename': words[1]}

            self.send_maintenance_client(MessageType.MAINTENANCE_REQUEST, TestcaseType.PRINT_SCN, data=print_screen_data)

        elif opcode == "MouseMove":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseMove")

            if len(words) > 1:
                x = 0
                y = 0
                click_data = None

                # check if parameter is a Point, and if the Point has been previously defined
                point_name = self.ParamMgr.get_script_point(words[1])
                if point_name is not None:
                    click_data = {'point': words[1]}
                elif len(words) > 2:
                    x = words[1]  # ok, then maybe there are digits in the script file. MouseMove(100,200)
                    y = words[2]  # send as string and
                    click_data = {'x': str(x), 'y': str(y)}
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MoveMouse: {command}")

                self.send_testcase_client(stepcount=stepcount, testcase_type=TestcaseType.MOUSE_MOVE, data=click_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MoveMouse missing parameters: {command}")

        elif opcode == "MouseScroll":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseScroll")
            # MouseScroll(Point, [amount to scroll, default 1])
            # MouseScroll(x, y, [amount to scroll, default 1])
            if len(words) > 1:
                x_value = 0
                y_value = 0
                amount_scroll = 0

                point_a = self.ParamMgr.get_script_point(words[1])
                if point_a is not None:  # check if parameter is a Point, and if the Point has been previously defined
                    x_value = point_a.x
                    y_value = point_a.y
                    amount_scroll = int(words[2])

                elif len(words) > 2:  # if MouseScroll(x, y)
                    x_value = int(words[1])  # ok, then maybe there are digits in the script file. MouseScroll(100,200)
                    y_value = int(words[2])
                    if len(words) > 3:
                        amount_scroll = int(words[3]) # if MouseScroll(x, y, scroll_amount)
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MoveMouse: {command}")

                if amount_scroll > 1:  # default is 1, probably can't scroll zero
                    mouse_scroll_data = {'x': str(x_value), 'y': str(y_value), 'amount_to_scroll': amount_scroll}
                else:
                    mouse_scroll_data = {'x': str(x_value), 'y': str(y_value)}  # default MOUSE_SCROLL of 1

                self.send_testcase_client(stepcount, TestcaseType.MOUSE_SCROLL, data=mouse_scroll_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MoveMouse missing parameters: {command}")

        elif opcode == "MouseDown":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseDown")
            self.ParamMgr.Logger.error("MouseDown not implemented")
            abc = 1
        elif opcode == "MouseUp":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseUp")
            self.ParamMgr.Logger.error("MouseUp not implemented")
            abc = 1
        elif opcode == "MouseGetPos":
            # MouseGetPos()  just log the position
            # MouseGetPos(Point) log the position and store it in a Point
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseGetPos")

            getpos_data = None

            if len(words) >= 2:
                variable_name = words[1]
                getpos_data = {'point': str(variable_name)}

            self.send_testcase_client(stepcount, TestcaseType.MOUSE_GETPOS, data=getpos_data)

        elif opcode == "MouseLeftClick":
            # MouseLeftClick(Point)
            # MouseLeftClick(x, y)
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseLeftClick")

            if len(words) >= 2:
                x = 0
                y = 0
                click_data = None

                # check if parameter is a Point, and if the Point has been previously defined
                point_a = self.ParamMgr.get_script_point(words[1])
                if point_a is not None:
                    click_data = {'point': words[1]}
                elif len(words) >= 3:
                    x = words[1]  # ok, then maybe there are digits in the script file. MouseMove(100,200)
                    y = words[2]
                    click_data = {'x': str(x), 'y': str(y)}
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MouseLeftClick: {command}")

                self.send_testcase_client(stepcount, TestcaseType.MOUSE_LEFT_CLICK, data=click_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseLeftClick missing parameters: {command}")

        elif opcode == "MouseRightClick":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseRightClick")

            if len(words) >= 2:
                x = 0
                y = 0
                click_data = None

                # check if parameter is a Point, and if the Point has been previously defined
                point_a = self.ParamMgr.get_script_point(words[1])
                if point_a is not None:
                    click_data = {'point': words[1]}
                elif len(words) >= 3:
                    x = words[1]  # ok, then maybe there are digits in the script file. MouseMove(100,200)
                    y = words[2]
                    click_data = {'x': str(x), 'y': str(y)}
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MouseRightClick: {command}")

                self.send_testcase_client(stepcount, TestcaseType.MOUSE_RIGHT_CLICK, data=click_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseRightClick missing parameters: {command}")

        elif opcode == "MouseMiddleClick":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseMiddleClick")

            if len(words) >= 2:
                x = 0
                y = 0
                click_data = None

                # check if parameter is a Point, and if the Point has been previously defined
                point_a = self.ParamMgr.get_script_point(words[1])
                if point_a is not None:
                    click_data = {'point': words[1]}
                elif len(words) >= 3:
                    x = words[1]  # ok, then maybe there are digits in the script file. MouseMove(100,200)
                    y = words[2]
                    click_data = {'x': str(x), 'y': str(y)}
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MouseMiddleClick: {command}")

                self.send_testcase_client(stepcount, TestcaseType.MOUSE_MIDDLE_CLICK, data=click_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseMiddleClick missing parameters: {command}")

        elif opcode == "MouseDoubleClick":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseDoubleClick")

            if len(words) >= 2:
                x = 0
                y = 0
                click_data = None

                # check if parameter is a Point, and if the Point has been previously defined
                point_a = self.ParamMgr.get_script_point(words[1])
                if point_a is not None:
                    click_data = {'point': words[1]}
                elif len(words) >= 3:
                    x = words[1]  # ok, then maybe there are digits in the script file. MouseMove(100,200)
                    y = words[2]
                    click_data = {'x': str(x), 'y': str(y)}
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MouseDoubleClick: {command}")

                self.send_testcase_client(stepcount, TestcaseType.MOUSE_LEFT_DOUBLE_CLICK, data=click_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseDoubleClick missing parameters: {command}")

        elif opcode == "MouseTripleClick":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseTripleClick")

            if len(words) >= 2:
                x = 0
                y = 0
                click_data = None

                # check if parameter is a Point, and if the Point has been previously defined
                point_a = self.ParamMgr.get_script_point(words[1])
                if point_a is not None:
                    click_data = {'point': words[1]}
                elif len(words) >= 3:
                    x = words[1]  # ok, then maybe there are digits in the script file. MouseMove(100,200)
                    y = words[2]
                    click_data = {'x': str(x), 'y': str(y)}
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MouseTripleClick: {command}")

                self.send_testcase_client(stepcount, TestcaseType.MOUSE_LEFT_TRIPLE_CLICK, data=click_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseDoubleClick missing parameters: {command}")

        elif opcode == "MoveWindow":
            # MoveWindow(window_name, Point)
            # MoveWindow(window_name, x, y)
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MoveWindow")

            if len(words) >= 2:
                x_pos = 0
                y_pos = 0
                window_name = None
                click_data = None

                # check if parameter is a Point, and if the Point has been previously defined
                point_name = self.ParamMgr.get_script_point(words[2])


                if point_name is not None:
                    click_data = {'point': words[1]}
                elif len(words) > 2:
                    x = words[1]  # ok, then maybe there are digits in the script file. MouseMove(100,200)
                    y = words[2]  # send as string and
                    click_data = {'x': str(x), 'y': str(y)}
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MoveWindow: {command}")

                abc_data = {'x': str(x_pos), 'y': str(y_pos), 'window_name': str(window_name)}

                self.send_testcase_client(stepcount, TestcaseType.MOVE_WINDOW, data=click_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseRightClick missing parameters: {command}")

        elif opcode == "KeyboardDown":
            # MoveWindow(character)

            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.KeyboardDown")
            keyboard_data = None

            if len(words) >= 2:
                abc00 = 'ctrl'
                keyboard_press = words[1].replace("'", "").replace('"', '')
                keyboard_data = {'keyboard_press': keyboard_press}
                abc01 = abc00 == keyboard_press

            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, KeyboardDown missing parameters: {command}")

            self.send_testcase_client(stepcount, TestcaseType.KEYBOARD_DOWN, data=keyboard_data)

        elif opcode == "KeyboardUp":
            # MoveWindow(character)

            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.KeyboardUp")
            keyboard_data = None

            if len(words) >= 2:
                abc00 = 'ctrl'
                keyboard_press = words[1].replace("'", "").replace('"', '')
                keyboard_data = {'keyboard_press': keyboard_press}
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, KeyboardUp missing parameters: {command}")

            self.send_testcase_client(stepcount, TestcaseType.KEYBOARD_UP, data=keyboard_data)

        elif opcode == "KeyboardPress":
            # MoveWindow(character)

            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.KeyboardPress")
            keyboard_data = None

            if len(words) >= 2:
                keyboard_data = {'keyboard_press': words[1]}
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, KeyboardPress missing parameters: {command}")

            self.send_testcase_client(stepcount, TestcaseType.KEYBOARD_PRESS, data=keyboard_data)

        elif opcode == "KeyboardHotPress":
            # MoveWindow(character)

            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.KeyboardHotPress")
            keyboard_data = None

            if len(words) > 2:
                keyboard_press_1 = words[1].replace("'", "").replace('"', '')  # remove all quotes
                keyboard_press_2 = words[2].replace("'", "").replace('"', '')
                keyboard_press_3 = None
                if len(words) > 3:
                    keyboard_press_3 = words[3].replace("'", "").replace('"', '')  # remove all quotes

                # keyboard_press_1 = words[1].replace('"', '')  # remove all quotes
                # keyboard_press_2 = words[2].replace('"', '')
                if keyboard_press_3 is not None:
                    keyboard_data = {'keyboard_press_1': keyboard_press_1, 'keyboard_press_2': keyboard_press_2,
                                     'keyboard_press_3': keyboard_press_3}
                else:
                    keyboard_data = {'keyboard_press_1': keyboard_press_1, 'keyboard_press_2': keyboard_press_2}
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, KeyboardHotPress missing parameters: {command}")


            self.send_testcase_client(stepcount, TestcaseType.KEYBOARD_HOTPRESS, data=keyboard_data)

        elif opcode == "WaitForInLogFile":
            # WaitForInLogFile(filename, texttofind)
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.WaitForInLogFile")

            filename = None
            texttofind = None
            timeout = None

            if len(words) > 2:

                filename = words[1]
                wait_text = words[2]
                if len(words) > 3:
                    timeout = words[3]

                # timeout = int(abc001.group())
                # filename = str("/home/amccombs/Documents/Projects/CallMeBack/junk.txt")
                self.ParamMgr.Logger.info \
                    (f"ScriptEngine.runscript: WaitForInLogFile, Filename: {str(filename)},"
                     f" Text to wait: {str(wait_text)}, Time to wait: {str(timeout)}")

                if timeout is not None:
                    wait_data = {'filename': filename, 'wait_for_text': wait_text, 'time_out': timeout}
                else:
                    wait_data = {'filename': filename, 'wait_for_text': wait_text}
                self.send_testcase_client(stepcount, TestcaseType.WAIT_FOR_IN_LOG_FILE, wait_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, invalid WaitForInLogFile: {str(command)}")

        elif opcode == "RunScript":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.RunScript")

            filename = None

            if len(words) > 1:
                filename = words[1]

                if os.path.exists(filename):
                    self.ParamMgr.Logger.info(
                        f"ScriptEngine.server_runscript_cmd.RunScript, RunScript: {str(filename)}")
                    se = ScriptEngine(self.ParamMgr)
                    se.loadscript(filename)
                    se.is_paused = False
                    se.is_run = True
                    se.run_script()

                else:
                    self.ParamMgr.Logger.error(
                        f"Error, ScriptEngine.server_runscript_cmd.RunScript, script not found: {str(command)}")
            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, RunScript missing parameters: {str(command)}")

        elif opcode == "Int":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.Int")

            is_static = False
            variable_name = None
            variable_value = None

            if len(words) > 2:
                if 'static' in words:
                    is_static = True
                variable_name = words[1]
                variable_value = words[2]

                if is_static:  # if static, only insert if it does not already exist, change value is not allowed
                    if not self.ParamMgr.is_script_int(variable_name):
                        self.ParamMgr.set_script_int(variable_name, int(variable_value))
                else:
                    self.ParamMgr.set_script_int(variable_name, int(variable_value))

                int_data = {'variable_name': str(variable_name), 'variable_value': str(variable_value),
                            'static': is_static}

                self.send_variable_client(TestcaseVariableType.INT, data=int_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, Int missing parameters: {str(command)}")

        elif opcode == "String":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.String")

            is_static = False

            if len(words) > 2:
                if 'static' in words:
                    is_static = True
                string_name = words[1]
                string_value = words[2]

                if is_static:  # if static, only insert if it does not already exist, change value is not allowed
                    if not self.ParamMgr.is_script_string(string_name):
                        self.ParamMgr.set_script_string(string_name, string_value)
                else:
                    self.ParamMgr.set_script_string(string_name, string_value)

            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, String missing parameters: {str(command)}")

        elif opcode == "Point":
            # Point A(x, y)
            #
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.Point")

            is_static = False
            point_name = None
            point_value = None

            if len(words) > 3:  # opcode, point_name, x_value, y_value
                if 'static' in words:
                    is_static = True
                point_name = words[1]
                point_value = Point(words[2], words[3])

            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, Point missing parameters: {str(command)}")

            if is_static:  # if static, only insert if it does not already exist, change value is not allowed
                if not self.ParamMgr.is_script_point(point_name):
                    self.ParamMgr.set_script_point(point_name, point_value)
            else:
                self.ParamMgr.set_script_point(point_name, point_value)

        #   #####################
        else:
            self.ParamMgr.Logger.error(
                f"Error, ScriptEngine.server_runscript_cmd.RunScript, unknown opcode: {str(command)}")

    def print(self):
        print("Script dictionary contents:")
        print(self.script)
