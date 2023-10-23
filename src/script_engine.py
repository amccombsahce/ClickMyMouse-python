import os
import time
import pyautogui
import subprocess
import hashlib
import vlc
import binascii
# my stuff
from file_mgr import FileMgr
from message_type import *  # MessageType, TestcaseType, TestcaseMessage, TestcaseTypeData, TestcaseVariableType, R
from point_type import Point
from wait_for_me import wait_for_me
import uu
import io


# ScriptEngine is used to store the script when it is read in from a flat file.


class ScriptEngine:

    def __init__(self, param_mgr):
        self.ParamMgr = param_mgr
        self.ParamMgr.Logger.debug("ScriptEngine.__init__")
        self.script = {}
        self.is_run = False
        self.is_paused = True  # pause will hold the ScriptMgr.run
        self.simon_says = False  # not enabled until START_TEST

    # move window from testcase command MoveWindow()
    def move_window_to_position(self, window_title, x, y):
        status = None
        if not self.ParamMgr.stop_event.is_set():
            try:
                # Use wmctrl to get the window ID by title
                window_id = subprocess.check_output(['wmctrl', '-l', '-x', '-G', '-p'], universal_newlines=True)
                for line in window_id.splitlines():
                    if window_title in line:
                        # Extract the window ID
                        window_id = line.split()[0]
                        print(f"window_id: {str(window_id)}")

                        # Use wmctrl to move the window to the specified position (1234, 567)
                        status = subprocess.call(['wmctrl', '-ir', window_id, '-e', f'0,{x},{y},-1,-1'])

                        print(f"Moved '{window_title}' to position ({x}, {y}).")
                print(f"Window with title '{window_title}' not found.")
                return status
            except Exception as e:
                print(f"An error occurred: {str(e)}")

    def set_run(self, to_run):  # True/False
        self.ParamMgr.Logger.debug(f"ScriptEngine.set_run {to_run}")
        self.is_run = to_run

    def set_pause(self, to_pause):  # True/False
        self.ParamMgr.Logger.debug(f"ScriptEngine.set_pause {to_pause}")
        self.is_paused = to_pause

    def is_pause(self):  # True/False
        self.ParamMgr.Logger.debug("ScriptEngine.is_pause")
        return self.is_paused

    def clear_script(self):
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
            for ii in command:  # script[step_number] = command
                self.script[len(self.script) + 1] = ii
        else:
            self.script[len(self.script) + 1] = command

    def run(self):
        self.ParamMgr.Logger.debug("ScriptEngine.run")

        # TODO put here if user selected Repeat test checkbox.
        self.send_maintenance_message_wait_response(MessageType.MAINTENANCE_REQUEST, TestcaseType.START_TEST)

        self.run_script()

        self.send_maintenance_message_wait_response(MessageType.MAINTENANCE_REQUEST, TestcaseType.STOP_TEST)
        # TODO put here endif Repeat is checked

        self.ParamMgr.Logger.debug("ScriptEngine.run, all-done")
        self.is_run = False
        self.is_paused = True
        self.ParamMgr.main_gui.run_clicked("Stop")  # reset the Stop button to Run button

    def run_script(self):
        self.ParamMgr.Logger.debug("ScriptEngine.run_script")
        if len(self.script) > 0:
            if self.is_run:
                for ii in self.script:

                    if self.ParamMgr.stop_event.is_set():
                        self.is_run = False
                        self.is_paused = True
                        return

                    while self.is_paused:
                        time.sleep(0.1)

                    self.server_runscript_cmd(ii, self.script[ii])
                    # self.send_script_client(ii, self.script[ii])

    # send_maintenance_message_wait_response
    # send a message type that is outside testcase
    def send_maintenance_message_wait_response(self, message_type: MessageType = MessageType.INIT,
                                               testcase_type: TestcaseType = TestcaseType.INIT, data=None):
        if not isinstance(testcase_type, TestcaseType):
            raise ValueError('ValueError, ScriptEngine.send_maintenance_message_wait_response, TestcaseType Enum')

        self.ParamMgr.Logger.debug(
            f"ScriptEngine.send_maintenance_message_wait_response: "  # ,{str(testcase_variable)},"
            f" with data: {str(data)}")

        self.ParamMgr.client_attendance.clear_client_response(MessageType.MAINTENANCE_RESPONSE, testcase_type)

        # if data is not None:
        #     abc = 2

        self.ParamMgr.NetworkMgr.send_maintenance_message(message_type=message_type, testcase_type=testcase_type,
                                                          data=data)

        client_response = self.ParamMgr.client_attendance.wait_for_client_response(MessageType.MAINTENANCE_RESPONSE,
                                                                                   testcase_type=testcase_type)

        if not client_response:
            self.ParamMgr.Logger.warning(
                f"Warning, ScriptEngine.send_maintenance_message_wait_response: timeout from no response")

    def send_testcase_message_wait_response(self, stepcount: int, testcase_type: TestcaseType, data=None):
        if not isinstance(testcase_type, TestcaseType):
            raise ValueError('ValueError, ScriptEngine.send_testcase_message_wait_response, TestcaseType Enum')

        self.ParamMgr.Logger.debug(f"ScriptEngine.send_testcase_message_wait_response: {str(testcase_type)},"
                                   f" with stepcount: {str(stepcount)}")

        # clear previous responses, wait for the correct message_type
        self.ParamMgr.client_attendance.clear_client_response(MessageType.TEST_CASE_RESPONSE, testcase_type)

        self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_REQEUST,
                                                       step_number=stepcount,
                                                       testcase_type=testcase_type,
                                                       data=data)

        client_response = self.ParamMgr.client_attendance.wait_for_client_response(MessageType.TEST_CASE_RESPONSE,
                                                                                   testcase_type)

        if not client_response:
            self.ParamMgr.Logger.warning(
                f"Warning, ScriptEngine.send_testcase_message_wait_response: timeout from no response")

    # send_variable_client
    # send a variable to the clients
    def send_variable_client_wait_response(self, testcase_variable_type: TestcaseVariableType = None, data=None):
        self.ParamMgr.Logger.debug(f"ScriptEngine.send_variable_client: "  # ,{str(testcase_variable)},"
                                   f" with data: {str(data)}")

        self.ParamMgr.client_attendance.clear_client_response(MessageType.TEST_CASE_VARIABLE_RESPONSE,
                                                              testcase_variable_type)

        self.ParamMgr.NetworkMgr.send_variable_message(MessageType.TEST_CASE_VARIABLE_REQUEST,
                                                       testcase_variable_type=testcase_variable_type, data=data)

        client_response = self.ParamMgr.client_attendance.wait_for_client_response(
            MessageType.TEST_CASE_VARIABLE_RESPONSE, testcase_variable_type)

        if not client_response:
            self.ParamMgr.Logger.warning(
                f"Warning, ScriptEngine.send_testcase_message_wait_response: timeout from no response")

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
        variable_value_x = None
        variable_value_y = None

        if 'static' in variable_data:
            is_static = variable_data['static']

        if 'variable_name' in variable_data:
            variable_name = variable_data['variable_name']

        if 'variable_value' in variable_data:
            variable_value = variable_data['variable_value']

        if testcase_variable_type == TestcaseVariableType.INT:
            self.ParamMgr.set_script_int(variable_name, int(variable_value), is_static)

        elif testcase_variable_type == TestcaseVariableType.STRING:
            self.ParamMgr.set_script_string(variable_name, str(variable_value), is_static)

        elif testcase_variable_type == TestcaseVariableType.POINT:

            if 'variable_value_x' in variable_data:
                variable_value_x = variable_data['variable_value_x']

            if 'variable_value_y' in variable_data:
                variable_value_y = variable_data['variable_value_y']

            self.ParamMgr.set_script_point(variable_name, Point(int(variable_value_x), int(variable_value_y)),
                                           is_static)

        self.ParamMgr.NetworkMgr.send_variable_message(MessageType.TEST_CASE_VARIABLE_RESPONSE,
                                                       testcase_variable_type=testcase_variable_type)

    # client_testcase_cmd
    # runs on client socket thread
    #
    def client_testcase_cmd(self, testcase_message: TestcaseMessage):  # client received command
        if not isinstance(testcase_message, TestcaseMessage):
            raise ValueError(
                'ValueError, ScriptEngine.client_testcase_cmd, TestcaseMessage Enum')

        step_number = testcase_message.step_number
        testcase_type = testcase_message.testcase_type
        data_object = testcase_message.data

        self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd")
        self.ParamMgr.Logger.info(f"stepcount: {str(step_number)}, command: {str(testcase_type)}")

        # TestcaseMessage has status for pass/fail, initialize as Fail
        status_is_pass = ResponseStatus.NONE

        # this is where should check for simon says
        did_simon_say_go = self.simon_says
        if not did_simon_say_go:
            # we did not get START_ message, reply with AWAY to indicate testcase not executed
            status_is_pass = ResponseStatus.AWAY
            self.ParamMgr.NetworkMgr.send_testcase_message_wait_response(MessageType.TEST_CASE_RESPONSE,
                                                                         step_number=step_number,
                                                                         testcase_type=testcase_type,
                                                                         status_is_pass=status_is_pass)

            return

        try:
            if testcase_type == TestcaseType.INIT:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.INIT")

            elif testcase_type == TestcaseType.SOUND:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.SOUND")

                # using pygame library,

                # pygame.mixer.init()

                # default file
                sound_filename = '../scripts/ding.wav'  # default

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
                    abc = p.is_playing()

                    if abc == 1:
                        status_is_pass = ResponseStatus.PASS
                    else:
                        status_is_pass = ResponseStatus.FAIL
                else:
                    self.ParamMgr.Logger.error(
                        f"ScriptEngine.client_testcase_cmd.SOUND, Error, file not found: {str(filepath)}")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message_wait_response(MessageType.TEST_CASE_RESPONSE,
                                                                             step_number=step_number,
                                                                             testcase_type=testcase_type,
                                                                             status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.PRINT_SCN:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.PRINT_SCN")

                log_dir = self.ParamMgr.get_log_path()

                filename = None
                abc_data = None

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
                self.ParamMgr.Logger.info(f"ScriptEngine.client_testcase_cmd.PRINT_SCN, saving to: {str(filepath)}")

                try:
                    pyautogui.screenshot(filepath)
                    status_is_pass = ResponseStatus.PASS
                    abc_data = {'filename': filepath}
                except AttributeError as e:
                    self.ParamMgr.Logger.error(
                        f"AttributeError: {str(e)}")
                    status_is_pass = ResponseStatus.EERR
                except ValueError as e:
                    self.ParamMgr.Logger.error(
                        f"ValueError Error: {str(e)}")
                    status_is_pass = ResponseStatus.EERR

                # send the path back to the server
                self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.TEST_CASE_RESPONSE,
                                                                  testcase_type=testcase_type,
                                                                  status_is_pass=status_is_pass,
                                                                  data=abc_data)
            elif testcase_type == TestcaseType.SLEEP:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.SLEEP")

                self.ParamMgr.Logger.info(f"sleeping")

                status_is_pass = ResponseStatus.PASS

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_MOVE:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOUSE_MOVE")

                x_pos = 0
                y_pos = 0
                new_x = None
                new_y = None
                point_name = None

                if data_object is not None:
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

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
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")

                    if new_x == x_pos and new_y == y_pos:
                        status_is_pass = ResponseStatus.PASS
                    else:
                        status_is_pass = ResponseStatus.FAIL
                        self.ParamMgr.Logger.warning(f"Warning, MouseMove to: x= {str(new_x)}, y= {str(new_y)}")

                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_SCROLL:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOUSE_SCROLL")
                # MouseScroll(amount, x, y), amount can be a negative number to scroll down, positive number scrolls up
                x_pos = 0
                y_pos = 0
                point_name = None
                amount_to_scroll = 1  # default is 1

                if data_object is not None:
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'amount_to_scroll' in data_object:
                        amount_to_scroll = int(data_object['amount_to_scroll'])
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseScroll:  x= {str(x_pos)}, y= {str(y_pos)},"
                                              f" amount_to_scroll= {str(amount_to_scroll)}")

                    try:
                        pyautogui.scroll(amount_to_scroll, x=x_pos, y=y_pos)
                        status_is_pass = ResponseStatus.PASS
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_GETPOS:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOUSE_GETPOS")
                # MouseGetPos()
                # MouseGetPos(Point)
                current_position = pyautogui.position()

                # send current_position back the pos to the server
                x_pos = current_position[0]
                y_pos = current_position[1]
                abc_data = {'x': str(x_pos), 'y': str(y_pos)}

                # show the user
                self.ParamMgr.Logger.info(f"MouseGetPos:  x= {str(x_pos)}, y= {str(y_pos)}")

                # if we got here, then it was successful
                status_is_pass = ResponseStatus.PASS

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
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOUSE_LEFT_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    if self.ParamMgr.is_script_point('Home'):
                        point_home = self.ParamMgr.is_script_point('Home')
                        x_pos += point_home.x
                        y_pos += point_home.y

                    self.ParamMgr.Logger.info(f"MouseLeftClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                    try:
                        pyautogui.click(x=x_pos, y=y_pos)
                        status_is_pass = ResponseStatus.PASS
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(
                            f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_RIGHT_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOUSE_RIGHT_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseRightClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    try:
                        pyautogui.rightClick(x=x_pos, y=y_pos)
                        status_is_pass = ResponseStatus.PASS
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_MIDDLE_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOUSE_MIDDLE_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseMiddleClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                    try:
                        pyautogui.middleClick(x=x_pos, y=y_pos)
                        status_is_pass = ResponseStatus.PASS
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_LEFT_DOUBLE_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOUSE_LEFT_DOUBLE_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseDoubleClick:  x= {str(x_pos)}, y= {str(y_pos)}")
                    try:
                        pyautogui.doubleClick(x=x_pos, y=y_pos)
                        status_is_pass = ResponseStatus.PASS
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOUSE_LEFT_TRIPLE_CLICK:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOUSE_LEFT_TRIPLE_CLICK")

                x_pos = 0
                y_pos = 0
                point_name = None

                if data_object is not None:
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

                    if point_name is not None:
                        if self.ParamMgr.is_script_point(point_name):
                            point_value = self.ParamMgr.get_script_point(point_name)
                            x_pos = point_value.x
                            y_pos = point_value.y

                    self.ParamMgr.Logger.info(f"MouseTripleClick:  x= {str(x_pos)}, y= {str(y_pos)}")

                    try:
                        pyautogui.tripleClick(x=x_pos, y=y_pos)
                        status_is_pass = ResponseStatus.PASS
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException:{str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.MOVE_WINDOW:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.MOVE_WINDOW")

                x_pos = 0
                y_pos = 0
                point_name = None
                window_name = None

                if data_object is not None:
                    if 'window_name' in data_object:
                        window_name = str(data_object['window_name'])
                    if 'point' in data_object:
                        point_name = data_object['point']
                    if 'x' in data_object:
                        x_pos = int(data_object['x'])
                    if 'y' in data_object:
                        y_pos = int(data_object['y'])

                    if point_name is not None:
                        point_a = self.ParamMgr.get_script_point(point_name)
                        x_pos = point_a.x
                        y_pos = point_a.y

                    self.ParamMgr.Logger.info(
                        f"MoveWindow: window= {str(window_name)}, x= {str(x_pos)}, y= {str(y_pos)}")

                    # window = pyautogui.getWindowsWithTitle(window_name)[0]
                    # window.move(x_pos, y_pos)

                    # hwnd = win32gui.FindWindow(None, window_name)
                    # win32gui.SetWindowPos(hwnd, ) (hwnd, x_pos, y_pos, 0, 0, 0, SWP_NOSIZE)

                    try:
                        self.move_window_to_position(window_name, x_pos, y_pos)
                        status_is_pass = ResponseStatus.PASS
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.KEYBOARD_PRESS:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.KEYBOARD_PRESS")

                keyboard_press = None

                if data_object is not None:
                    if 'keyboard_press' in data_object:
                        keyboard_press = str(data_object['keyboard_press'])

                    self.ParamMgr.Logger.info(
                        f"Keyboard press: key= {str(keyboard_press)}")

                    try:
                        # pyautogui.typewrite(keyboard_press, interval=0.25)
                        pyautogui.press(keyboard_press)
                        status_is_pass = ResponseStatus.PASS
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except ValueError as e:
                        self.ParamMgr.Logger.error(f"ValueError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.KEYBOARD_DOWN:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.KEYBOARD_DOWN")

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
                        # pyautogui.press(keyboard_press)
                        status_is_pass = ResponseStatus.PASS
                        abc01 = abc == keyboard_press
                        print(f"keydown: ctrl= {str(abc01)}")

                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except ValueError as e:
                        self.ParamMgr.Logger.error(f"ValueError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.KEYBOARD_UP:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.KEYBOARD_UP")

                keyboard_press = None

                if data_object is not None:
                    if 'keyboard_press' in data_object:
                        keyboard_press = str(data_object['keyboard_press'])

                    self.ParamMgr.Logger.info(
                        f"Keyboard press: key= {str(keyboard_press)}")

                    try:
                        abc = 'ctrl'
                        pyautogui.keyUp(abc)
                        # pyautogui.keyUp(keyboard_press)
                        status_is_pass = ResponseStatus.PASS
                        abc01 = abc == keyboard_press
                        print(f"keyup: ctrl= {str(abc01)}")
                    except ValueError as e:
                        self.ParamMgr.Logger.error(f"ValueError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.KEYBOARD_HOTPRESS:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.KEYBOARD_HOTPRESS")

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
                        status_is_pass = ResponseStatus.PASS

                    except ValueError as e:
                        self.ParamMgr.Logger.error(f"ValueError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except OSError as e:
                        self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(f"PyAutoGUIException: {str(e)}")
                        status_is_pass = ResponseStatus.EERR
                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.WAIT_FOR_IN_LOG_FILE:
                self.ParamMgr.Logger.debug("ScriptEngine.client_testcase_cmd.WAIT_FOR_IN_LOG_FILE")

                timeout = 60  # default
                filename = None
                wait_for_text = None

                if data_object is not None:
                    if 'filename' in data_object:
                        filename = data_object['filename']
                    else:
                        self.ParamMgr.Logger.error(f"Error, Script.Engine.client_testcase_cmd: missing filename")

                    if 'wait_for_text' in data_object:
                        wait_for_text = data_object['wait_for_text']
                    else:
                        self.ParamMgr.Logger.error(f"Error, Script.Engine.client_testcase_cmd: missing wait_for_text")

                    if data_object is not None:
                        if 'time_out' in data_object:
                            timeout = int(data_object['time_out'])

                    self.ParamMgr.Logger.info(
                        f"WaitForInFile: filename: {str(filename)}, wait_for_text: {str(wait_for_text)}")

                    waitforme = wait_for_me(filename, wait_for_text, timeout)
                    result = waitforme.run()

                    self.ParamMgr.Logger.debug(f"Script.Engine.client_testcase_cmd: competed: {str(result)}")

                    if result:
                        self.ParamMgr.Logger.info(f"WaitForInLogFile: found text: {str(wait_for_text)}")
                        status_is_pass = ResponseStatus.PASS
                    else:
                        self.ParamMgr.Logger.warning(
                            f"Warning, WaitForInLogFile: did not find text: {str(wait_for_text)}")
                        status_is_pass = ResponseStatus.FAIL

                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               step_number=step_number,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.EXECUTE_CMD:
                self.ParamMgr.Logger.info("ScriptEngine.client_testcase_cmd.EXECUTE_CMD")  # info logging se we know
                # TODO move this back to testcase test, starting an application is a testcase
                # ExecuteCmd will start a process
                # we need the filename of the process (fullpath is best), arguments to the process
                # we need to know if the user wants the process to complete before continuing or just start the process
                # we need to know if the user wants us to wait, what is the timeout for that max time to
                # wait for the process to complete

                if data_object is not None:
                    process = None
                    process_name = None
                    process_args = None
                    process_wait_for_exit = False
                    time_out = None

                    if 'process_name' in data_object:
                        process_name = data_object['process_name']
                    if 'process_args' in data_object:
                        process_args = data_object['process_args']
                    if 'process_wait_for_exit' in data_object:
                        process_wait_for_exit = bool(data_object['process_wait_for_exit'])
                    if 'time_out' in data_object:
                        time_out = int(data_object['time_out'])

                    process_path = None

                    # check if process was saved as a Sting
                    if self.ParamMgr.is_script_string(process_name):
                        process_path = self.ParamMgr.get_script_string(process_name)
                    else:
                        process_path = process_name.replace("'", "")  # '/usr/bin/gnome-calculator'

                    if os.path.exists(process_path):
                        self.ParamMgr.Logger.info(f"subprocess: {str(process_path)}")

                        try:

                            if process_args is not None:
                                # check if the args was saved as String
                                if self.ParamMgr.is_script_string(process_args):
                                    process_args = self.ParamMgr.get_script_string()

                                args = [process_path, process_args]

                                process = subprocess.Popen(args, stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
                            else:
                                # create the process
                                process = subprocess.Popen(process_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                            self.ParamMgr.Logger.info(f"pid: {str(process.pid)}")

                            if time_out is not None:
                                time.sleep(time_out)

                            # bring the window to top
                            # TODO this is a linux command, wont work in Windows
                            window_ids = subprocess.check_output(['wmctrl', '-l', '-x', '-p'],
                                                                 universal_newlines=True)

                            # move window for debugging
                            for line in window_ids.splitlines():
                                if str(process.pid) in line:
                                    print(f"line: {str(line)}")
                                    abc = line.split(' ')
                                    abc001 = abc[len(abc) - 1]  # get the app name
                                    self.ParamMgr.Logger.debug(f"subprocess name: {str(abc001)}")
                                    # self.move_window_to_position(abc001, 10, 10)

                            # bring to Top
                            # command = f"wmctrl -i -a {str(process.pid)}"
                            # the_subprocess = subprocess.Popen(["/bin/bash", "-c", command])
                            # the_return = the_subprocess.wait()
                            # print(f"wmctrl returned: {str(the_return)}")

                            if process_wait_for_exit:  # or time_out:
                                # communicate with the process: send input, read output and error
                                if time_out is not None:
                                    stdout, stderr = process.communicate(timeout=time_out)
                                else:
                                    stdout, stderr = process.communicate()

                                self.ParamMgr.Logger.debug(f"stdout: {str(stdout)}")
                                self.ParamMgr.Logger.error(f"stderr: {str(stderr)}")

                            self.ParamMgr.Logger.info(f"return code: {str(process.returncode)}")

                            if process_wait_for_exit is False or time_out is None or process.returncode == 0:
                                status_is_pass = ResponseStatus.PASS
                            elif process.returncode != 0:  # not zero it returned an error
                                status_is_pass = ResponseStatus.ERRR

                        except TimeoutError as e:  # BingAI says that communicate(timeout) will throw an exception, but
                            self.ParamMgr.Logger.error(f"TimeoutError, subprocess: {str(e)}")
                            status_is_pass = ResponseStatus.EERR
                        except Exception as e:  # Exception gets thrown not TimeoutError
                            self.ParamMgr.Logger.error(f"Exception, subprocess: {str(e)}")
                            status_is_pass = ResponseStatus.EERR


                    else:
                        self.ParamMgr.Logger.error(f"Error, Process not found: {str(process_path)}")
                        status_is_pass = ResponseStatus.ERRR

                else:
                    self.ParamMgr.Logger.error(f"Error, data_object is None")
                    status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            elif testcase_type == TestcaseType.IMG_GET_POS:
                self.ParamMgr.Logger.info("ScriptEngine.client_testcase_cmd.IMG_GET_POS")

                if data_object is not None:
                    filename = None
                    md5_hash = None
                    variable_name = None       # does the user want to store the location to a Point
                    have_correct_file = False  # if we don't have the file, we can request the file from the server

                    if 'filename' in data_object:
                        filename = data_object['filename']
                    if 'md5_hash' in data_object:
                        md5_hash = data_object['md5_hash']
                    if 'variable_name' in data_object:
                        variable_name = data_object['variable_name']

                    if os.path.exists(filename):
                        md5_hash_on_disk = self.ParamMgr.calculate_md5(filename)

                        if md5_hash == md5_hash_on_disk:
                            have_correct_file = True
                        else:
                            os.remove(filename)  # bad md5 sum, delete it and request new file

                    if not have_correct_file:
                        # don't have it, then get it
                        self.ParamMgr.Logger.warning(f"Warning: img file not found, requesting")
                        file_data = {'filename': filename}
                        self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_REQUEST,
                                                                          testcase_type=TestcaseType.FILE_TRANSFER_FROM_SERVER,
                                                                          data=file_data)

                    # we requested the file, not we wait until we get the correct file before we proceed
                    while not have_correct_file:
                        while not os.path.exists(filename):
                            time.sleep(0.1)

                        while not have_correct_file:
                            if os.path.exists(filename):
                                md5_hash_on_disk = self.ParamMgr.calculate_md5(filename)

                                if md5_hash == md5_hash_on_disk:
                                    have_correct_file = True
                                else:
                                    time.sleep(0.1)

                    # if we got here, then have_file should be True
                    if os.path.exists(filename):
                        md5_hash_on_disk = self.ParamMgr.calculate_md5(filename)

                        if md5_hash == md5_hash_on_disk:
                            # we have the correct file,
                            try:
                                # the_box = pyautogui.locateOnScreen(filename)
                                # point_a = pyautogui.center(the_box)
                                point_a = pyautogui.locateCenterOnScreen(filename, 1.1)
                                status_is_pass = ResponseStatus.PASS

                                # store the coordinates if user supplied variable
                                if variable_name is not None:
                                    self.ParamMgr.set_script_point(variable_name, point_a)

                            except pyautogui.ImageNotFoundException as e:
                                self.ParamMgr.Logger.error(
                                    f"ImageNotFoundException Error, ImageNotFoundException: {str(e)}")
                                status_is_pass = ResponseStatus.EERR
                            except pyautogui.PyAutoGUIException as e:
                                self.ParamMgr.Logger.error(f"PyAutoGUIException Error, PyAutoGUIException: {str(e)}")
                                status_is_pass = ResponseStatus.EERR

                        else:  # md5_hash mismatch
                            self.ParamMgr.Logger.error(
                                f"Error, MD5 mismatch: actual:{str(md5_hash_on_disk)}, expected: {str(md5_hash)}")
                            status_is_pass = ResponseStatus.ERRR
                            os.remove(filename)  # bad md5 sum, delete it and request new file

                    else:  # not os.path.exists(filename)
                        self.ParamMgr.Logger.error(
                            f"Error, img filename not found: {str(filename)}")
                        status_is_pass = ResponseStatus.ERRR

                self.ParamMgr.NetworkMgr.send_testcase_message(MessageType.TEST_CASE_RESPONSE,
                                                               testcase_type=testcase_type,
                                                               status_is_pass=status_is_pass)

            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.client_testcase_cmd: unknown testcase_message: {str(testcase_message)}")

        except TypeError as e:
            self.ParamMgr.Logger.error(f"TypeError, Script.Engine.client_testcase_cmd: TypeError: {str(e)}")
        except OSError as e:
            self.ParamMgr.Logger.error(f"OSError, Script.Engine.client_testcase_cmd: OSError: {str(e)}")
        except Exception as e:
            self.ParamMgr.Logger.error(f"Exception Error, Script.Engine.client_testcase_cmd: {str(e)}")

    # regular expressions didn't work
    # parse_string_to_list to split the command that was read from the .script file and turn it to a list
    def parse_string_to_list(self, text) -> list:
        in_quote = False

        result = []
        temp = ""

        for item in text:
            if item == '(':
                if in_quote:
                    temp += item
                else:
                    if len(temp) > 0:
                        result.append(temp)
                    temp = ""
            elif item == '"':
                if in_quote:
                    in_quote = False
                else:
                    in_quote = True
            elif item == '\'':
                if in_quote:
                    in_quote = False
                else:
                    in_quote = True
            elif item == ',':
                if in_quote:
                    temp += item
                else:
                    result.append(temp)
                    temp = ""
            elif item == ')':
                if len(temp) > 0:
                    result.append(temp)
                temp = ""
            elif item == ' ':
                if in_quote:
                    temp += item
                else:
                    if len(temp) > 0:
                        result.append(temp)
                    temp = ""
            else:
                temp += item
        return result

    # server_runscript_cmd
    # runs on server socket thread,
    #
    # server_runscript_cmd parses the .script file and sends codes to client
    def server_runscript_cmd(self, stepcount, command):
        self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd")

        words = self.parse_string_to_list(command)

        # Point, String, Int can be Static
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
            self.send_testcase_message_wait_response(stepcount, TestcaseType.SLEEP)

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
                if len(words[1]) > 1:  # filename of sound file to play, 'ding.wav' is default
                    sound_data = {TestcaseTypeData.DATA_SOUND: str(words[1])}

                    self.ParamMgr.Logger.info(
                        f"ScriptEngine.server_runscript_cmd: Sound, data= {str(sound_data.values())}")

            self.send_maintenance_message_wait_response(MessageType.MAINTENANCE_REQUEST,
                                                        testcase_type=TestcaseType.SOUND,
                                                        data=sound_data)

        elif opcode == "GetDateTime":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.GetDateTime")
            self.ParamMgr.Logger.error("not implemented")

        elif opcode == "Log":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.Log")
            self.ParamMgr.Logger.error("not implemented")

        elif opcode == "PrintScreen":
            # PrintScreen() # use default filename saving
            # PrintScreen(String) # save file in user specified filename
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.PrintScn")
            # default screenshot filename is "screenshot_<datetime>.png"

            print_screen_data = None

            if len(words) > 1:
                print_screen_data = {'filename': words[1]}

            self.send_maintenance_message_wait_response(MessageType.MAINTENANCE_REQUEST, TestcaseType.PRINT_SCN,
                                                        data=print_screen_data)

        elif opcode == "MouseMove":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseMove")

            if len(words) > 1:
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

                self.send_testcase_message_wait_response(stepcount=stepcount, testcase_type=TestcaseType.MOUSE_MOVE,
                                                         data=click_data)
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
                        amount_scroll = int(words[3])  # if MouseScroll(x, y, scroll_amount)
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MoveMouse: {command}")

                if amount_scroll > 1:  # default is 1, probably can't scroll zero
                    mouse_scroll_data = {'x': str(x_value), 'y': str(y_value), 'amount_to_scroll': amount_scroll}
                else:
                    mouse_scroll_data = {'x': str(x_value), 'y': str(y_value)}  # default MOUSE_SCROLL of 1

                self.send_testcase_message_wait_response(stepcount, TestcaseType.MOUSE_SCROLL, data=mouse_scroll_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MoveMouse missing parameters: {command}")

        elif opcode == "MouseDown":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseDown")
            self.ParamMgr.Logger.error("MouseDown not implemented")

        elif opcode == "MouseUp":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseUp")
            self.ParamMgr.Logger.error("MouseUp not implemented")

        elif opcode == "MouseGetPos":
            # MouseGetPos()  just log the position
            # MouseGetPos(Point) log the position and store it in a Point
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseGetPos")

            getpos_data = None

            if len(words) >= 2:
                variable_name = words[1]
                getpos_data = {'point': str(variable_name)}

            self.send_testcase_message_wait_response(stepcount, TestcaseType.MOUSE_GETPOS, data=getpos_data)

        elif opcode == "MouseLeftClick":
            # MouseLeftClick(Point)
            # MouseLeftClick(x, y)
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseLeftClick")

            if len(words) >= 2:
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

                self.send_testcase_message_wait_response(stepcount, TestcaseType.MOUSE_LEFT_CLICK, data=click_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseLeftClick missing parameters: {command}")

        elif opcode == "MouseRightClick":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseRightClick")

            if len(words) >= 2:
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

                self.send_testcase_message_wait_response(stepcount, TestcaseType.MOUSE_RIGHT_CLICK, data=click_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseRightClick missing parameters: {command}")

        elif opcode == "MouseMiddleClick":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseMiddleClick")

            if len(words) >= 2:
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

                self.send_testcase_message_wait_response(stepcount, TestcaseType.MOUSE_MIDDLE_CLICK, data=click_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseMiddleClick missing parameters: {command}")

        elif opcode == "MouseDoubleClick":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseDoubleClick")

            if len(words) >= 2:
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

                self.send_testcase_message_wait_response(stepcount, TestcaseType.MOUSE_LEFT_DOUBLE_CLICK,
                                                         data=click_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseDoubleClick missing parameters: {command}")

        elif opcode == "MouseTripleClick":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MouseTripleClick")

            if len(words) >= 2:
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

                self.send_testcase_message_wait_response(stepcount, TestcaseType.MOUSE_LEFT_TRIPLE_CLICK,
                                                         data=click_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseDoubleClick missing parameters: {command}")

        elif opcode == "MoveWindow":
            # MoveWindow(window_name, Point)
            # MoveWindow(window_name, x, y)
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.MoveWindow")

            if len(words) > 2:
                window_name = words[1]
                click_data = {'window_name': str(window_name)}

                # check if parameter is a Point, and if the Point has been previously defined
                point_name = self.ParamMgr.get_script_point(words[2])

                if point_name is not None:
                    click_data['point'] = words[2]
                elif len(words) > 3:
                    x_pos = words[1]  # ok, then maybe there are digits in the script file. MouseMove(100,200)
                    y_pos = words[2]  # send as string and
                    click_data['x'] = str(x_pos)
                    click_data['y'] = str(y_pos)
                else:
                    self.ParamMgr.Logger.error(
                        f"Error: ScriptEngine.server_runscript_cmd invalid points MoveWindow: {command}")

                self.send_testcase_message_wait_response(stepcount, TestcaseType.MOVE_WINDOW, data=click_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, MouseRightClick missing parameters: {command}")

        elif opcode == "KeyboardDown":
            # MoveWindow(character)

            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.KeyboardDown")
            keyboard_data = None

            if len(words) >= 2:
                keyboard_press = words[1].replace("'", "").replace('"', '')
                keyboard_data = {'keyboard_press': keyboard_press}
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, KeyboardDown missing parameters: {command}")

            self.send_testcase_message_wait_response(stepcount, TestcaseType.KEYBOARD_DOWN, data=keyboard_data)

        elif opcode == "KeyboardUp":
            # MoveWindow(character)

            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.KeyboardUp")
            keyboard_data = None

            if len(words) >= 2:
                # abc00 = 'ctrl'
                keyboard_press = words[1].replace("'", "").replace('"', '')
                keyboard_data = {'keyboard_press': keyboard_press}
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, KeyboardUp missing parameters: {command}")

            self.send_testcase_message_wait_response(stepcount, TestcaseType.KEYBOARD_UP, data=keyboard_data)

        elif opcode == "KeyboardPress":
            # MoveWindow(character)

            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.KeyboardPress")
            keyboard_data = None

            if len(words) >= 2:
                keyboard_data = {'keyboard_press': words[1]}
            else:
                self.ParamMgr.Logger.error(
                    f"Error: ScriptEngine.server_runscript_cmd, KeyboardPress missing parameters: {command}")

            self.send_testcase_message_wait_response(stepcount, TestcaseType.KEYBOARD_PRESS, data=keyboard_data)

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

            self.send_testcase_message_wait_response(stepcount, TestcaseType.KEYBOARD_HOTPRESS, data=keyboard_data)

        elif opcode == "WaitForInLogFile":
            # WaitForInLogFile(filename, texttofind)
            # WaitForInLogFile(filename, texttofind, timeout)
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.WaitForInLogFile")

            if len(words) > 2:

                time_out = None

                filename = words[1]
                wait_text = words[2]
                wait_data = {'filename': filename, 'wait_for_text': wait_text}

                if len(words) > 3:
                    time_out = words[3]
                    wait_data['time_out'] = time_out

                self.ParamMgr.Logger.info \
                    (f"ScriptEngine.runscript: WaitForInLogFile, Filename: {str(filename)},"
                     f" Text to wait: {str(wait_text)}, Time to wait: {str(time_out)}")

                self.send_testcase_message_wait_response(stepcount, TestcaseType.WAIT_FOR_IN_LOG_FILE, wait_data)
            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, invalid WaitForInLogFile: {str(command)}")

        elif opcode == "RunScript":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.RunScript")

            if len(words) > 1:
                filename = words[1]

                if os.path.exists(filename):
                    self.ParamMgr.Logger.info(
                        f"ScriptEngine.server_runscript_cmd.RunScript, RunScript: {str(filename)}")
                    se = ScriptEngine(self.ParamMgr)
                    se.load_script(filename)
                    # TODO move bool to parammgr so that multiple instances will only look
                    #  at one pause and one run, if the user clicks pause, wont have effect on subscripts
                    #  by hardcoding here
                    se.is_paused = False
                    se.is_run = True
                    se.run_script()

                else:
                    self.ParamMgr.Logger.error(
                        f"Error, ScriptEngine.server_runscript_cmd.RunScript, script not found: {str(command)}")
            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, RunScript missing parameters: {str(command)}")

        elif opcode == "ExecuteCmd":
            # creates a process and waits for the return value of the process to continue.
            # ExecuteCmd(String)              # String is path to the exe
            # ExecuteCmd(String, String_args) # String is path to the exe, String to arguments
            # ExecuteCmd(String, String_args, Int_timeout) # String is path to the exe, String to arguments
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.CreateProcess")

            abc_data = None

            if len(words) > 1:
                process_name = words[1]
                abc_data = {'process_name': str(process_name)}

            if len(words) > 2:
                process_args = words[2]
                if len(process_args.replace("'", "")) > 0:
                    abc_data['process_args'] = str(process_args)

            if len(words) > 3:
                time_out = words[3]
                if len(time_out) > 0:
                    abc_data['time_out'] = str(time_out)

            self.send_testcase_message_wait_response(stepcount=stepcount, testcase_type=TestcaseType.EXECUTE_CMD,
                                                     data=abc_data)

        elif opcode == "ImgGetPos":
            # Get Position on what is on the screen with the img supplied
            # ImgGetPos(String, Point)
            # using pyautogui.locateOnScreen
            # Box(left=1416, top=562, width=50, height=41)
            # store the center of the Box to the Point
            # ImgGetPos('scripts/gnome-calculator_btn_1.png' , btn_1)  # get the location of btn_1 and store in a point named btn_1
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.ImgGetPos")

            img_data = None

            if len(words) > 1:
                filename = words[1].replace("'", "").replace('"', '')
                if os.path.exists(filename):
                    # supply md5 sum, client will check it to see if they have the correct img

                    md5_hash = self.ParamMgr.calculate_md5(filename)
                    img_data = {'filename': str(filename), 'md5_hash': md5_hash}

            self.send_maintenance_message_wait_response(message_type=MessageType.MAINTENANCE_REQUEST,
                                                        testcase_type=TestcaseType.IMG_GET_POS, data=img_data)

            abc_break = 1

        elif opcode == "FileTransferFromServer":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.FileTransferFromServer")

            req_file_data = None

            if len(words) > 1:
                filename = words[1].replace("'", "").replace('"', '')
                req_file_data = {'filename': str(filename)}

                if os.path.exists(filename):
                    md5_filename_hash = self.ParamMgr.calculate_md5(filename)
                    req_file_data['md5'] = md5_filename_hash

            self.send_maintenance_message_wait_response(message_type=MessageType.MAINTENANCE_REQUEST,
                                                        testcase_type=TestcaseType.GET_FILE_FROM_SERVER,
                                                        data=req_file_data)

        elif opcode == "Int":
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.Int")

            is_static = False

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

                self.send_variable_client_wait_response(TestcaseVariableType.INT, data=int_data)

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

                str_data = {'variable_name': str(string_name), 'variable_value': str(string_value),
                            'static': is_static}
                self.send_variable_client_wait_response(TestcaseVariableType.STRING, data=str_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, String missing parameters: {str(command)}")

        elif opcode == "Point":
            # Point A(x, y)
            #
            self.ParamMgr.Logger.debug("ScriptEngine.server_runscript_cmd.Point")

            is_static = False

            if len(words) > 3:  # opcode, point_name, x_value, y_value
                if 'static' in words:
                    is_static = True
                point_name = words[1]

                point_value_x = words[2]
                point_value_y = words[3]

                point_value = Point(int(point_value_x), int(point_value_y))

                if is_static:  # if static, only insert if it does not already exist, change value is not allowed
                    if not self.ParamMgr.is_script_point(point_name):
                        self.ParamMgr.set_script_point(point_name, point_value)
                else:
                    self.ParamMgr.set_script_point(point_name, point_value)

                pnt_data = {'variable_name': str(point_name),
                            'variable_value_x': str(point_value_x),
                            'variable_value_y': str(point_value_y),
                            'static': is_static}
                self.send_variable_client_wait_response(TestcaseVariableType.POINT, data=pnt_data)

            else:
                self.ParamMgr.Logger.error(
                    f"Error, ScriptEngine.server_runscript_cmd.RunScript, Point missing parameters: {str(command)}")



        #   #####################
        else:
            self.ParamMgr.Logger.error(
                f"Error, ScriptEngine.server_runscript_cmd.RunScript, unknown opcode: {str(command)}")

    # run_maintenance_cmd
    # message to client
    # out of testcase actions like screenshots and roll client log files
    def run_maintenance_cmd(self, maintenance_message: MaintenanceMessage, peer_info=None):
        if not isinstance(maintenance_message, MaintenanceMessage):
            raise ValueError(
                'ValueError, ScriptEngine.run_maintenance_cmd, MaintenanceMessage Enum')

        message_type = maintenance_message.message_type
        testcase_type = maintenance_message.testcase_type
        is_pass = maintenance_message.status_is_pass
        data_object = maintenance_message.data

        self.ParamMgr.Logger.debug("ScriptEngine.run_maintenance_cmd")
        self.ParamMgr.Logger.info(f"command: {str(testcase_type)}, from: {str(peer_info)}")

        # TestcaseMessage has status for pass/fail, initialize as Fail
        status_is_pass = ResponseStatus.NONE

        if message_type == MessageType.MAINTENANCE_REQUEST:
            try:
                if testcase_type == TestcaseType.INIT:
                    # I received this message, that means I am the client
                    self.ParamMgr.Logger.debug("ScriptEngine.run_maintenance_cmd.INIT")
                    # TODO do stuff so that we know that the client has connected

                    self.ParamMgr.main_gui.add_connection(str(peer_info), "SERVER")
                    self.ParamMgr.client_attendance.add_client_attendance(peer_info)

                    # set client ledger for main req sent to server
                    self.ParamMgr.set_client_ledger(peer_info)

                    self.ParamMgr.Logger.info(f"INIT_REQUEST from peer_info:{str(peer_info)}")

                    status_is_pass = ResponseStatus.PASS

                    # self.ParamMgr.client_attendance.add_client_response(peer_info, message_type=message_type,
                    #                                                     testcase_type=testcase_type)

                    self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                      testcase_type=testcase_type,
                                                                      status_is_pass=status_is_pass)
                elif testcase_type == TestcaseType.SIMON_STOP:
                    self.ParamMgr.Logger.debug("ScriptEngine.run_maintenance_cmd.SIMON_STOP")

                    # did simon time you out ? >:)
                    self.ParamMgr.simon_says = False
                    status_is_pass = ResponseStatus.PASS
                    self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                      testcase_type=testcase_type,
                                                                      status_is_pass=status_is_pass)

                elif testcase_type == TestcaseType.PRINT_SCN:
                    self.ParamMgr.Logger.debug("ScriptEngine.run_maintenance_cmd.PRINT_SCN")

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
                    self.ParamMgr.Logger.info(f"ScriptEngine.run_maintenance_cmd.PRINT_SCN, saving to: {str(filepath)}")

                    try:
                        pyautogui.screenshot(filepath)
                        # send the filename back to the server
                        abc_data = {'filename': filepath}
                        status_is_pass = ResponseStatus.PASS

                    except pyautogui.PyAutoGUIException as e:
                        self.ParamMgr.Logger.error(
                            f"PyAutoGUIException: {str(e)}")

                    except AttributeError as e:
                        self.ParamMgr.Logger.error(
                            f"AttributeError: {str(e)}")
                    except ValueError as e:
                        self.ParamMgr.Logger.error(
                            f"ValueError Error: {str(e)}")
                    except Exception as e:
                        self.ParamMgr.Logger.error(
                            f"Exception Error: {str(e)}")

                    self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                      testcase_type=testcase_type,
                                                                      status_is_pass=status_is_pass,
                                                                      data=abc_data)

                elif testcase_type == TestcaseType.SOUND:
                    self.ParamMgr.Logger.debug("ScriptEngine.run_maintenance_cmd.SOUND")

                    # using pygame library,
                    # pygame.mixer.init()

                    # default file
                    sound_filename = '../scripts/ding.wav'  # default

                    # check if user wants a different filename
                    if data_object is not None:
                        if TestcaseTypeData.DATA_SOUND in data_object:
                            #  sound_filename = data_object[TestcaseTypeData.DATA_SOUND] # I think this worked,
                            #  but it doesn't for start process, had to strip the ' from the string
                            sound_filename = data_object[TestcaseTypeData.DATA_SOUND].replace("'", "")

                    self.ParamMgr.Logger.info(
                        f"ScriptEngine.run_maintenance_cmd.SOUND, filename: {str(sound_filename)}")

                    if os.path.exists(sound_filename):
                        # sound = pygame.mixer.Sound(filepath)
                        # sound = pygame.mixer.Sound('ding.wav')
                        # sound.play()
                        # p = vlc.MediaPlayer(filepath)
                        p = vlc.MediaPlayer(sound_filename)
                        status = p.play()
                        # play returns 0 when starts to play
                        # play returns -1 with error
                        if status != -1:
                            status_is_pass = ResponseStatus.PASS
                    else:
                        self.ParamMgr.Logger.error(f"Error, file not found: {str(sound_filename)}")

                    self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                      testcase_type=testcase_type,
                                                                      status_is_pass=status_is_pass)

                elif testcase_type == TestcaseType.START_TEST:
                    self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.START_TEST")  # info logging se we know

                    # TODO do stuff so that client will know when to start accepting commands
                    self.ParamMgr.simon_says = True  # when symon says
                    status_is_pass = ResponseStatus.PASS
                    self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                      testcase_type=testcase_type,
                                                                      status_is_pass=status_is_pass)

                elif testcase_type == TestcaseType.STOP_TEST:
                    # we are the client, aka SUT
                    self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.STOP_TEST")  # info logging se we know

                    # TODO do stuff so that client will know when to stop accepting commands
                    self.simon_says = False

                    self.ParamMgr.Logger.info(f"Test Results:")
                    self.ParamMgr.Logger.info(f"item count in Int: {str(self.ParamMgr.get_script_int_count())}")
                    self.ParamMgr.Logger.info(f"{str(self.ParamMgr.get_script_int_str())}")

                    self.ParamMgr.Logger.info(f"item count in String: {str(self.ParamMgr.get_script_string_count())}")
                    self.ParamMgr.Logger.info(f"{str(self.ParamMgr.get_script_string_str())}")

                    self.ParamMgr.Logger.info(f"item count in Point: {str(self.ParamMgr.get_script_point_count())}")
                    self.ParamMgr.Logger.info(f"{str(self.ParamMgr.get_script_point_str())}")

                    # get ledger to show the user the stats
                    abc = self.ParamMgr.get_client_ledger(peer_info)

                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_testcase_request_sent_count: {str(abc.test_statistics.total_testcase_request_sent_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_testcase_request_recv_count: {str(abc.test_statistics.total_testcase_request_recv_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_testcase_response_sent_count: {str(abc.test_statistics.total_testcase_response_sent_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_testcase_response_recv_count: {str(abc.test_statistics.total_testcase_response_recv_count)}")

                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_testcase_pass_count: {str(abc.test_statistics.total_testcase_pass_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_testcase_fail_count: {str(abc.test_statistics.total_testcase_fail_count)}")

                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_variable_request_sent_count: {str(abc.test_statistics.total_variable_request_sent_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_variable_request_recv_count: {str(abc.test_statistics.total_variable_request_recv_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_variable_response_sent_count: {str(abc.test_statistics.total_variable_response_sent_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_variable_response_recv_count: {str(abc.test_statistics.total_variable_response_recv_count)}")

                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_maintenance_request_sent_count: {str(abc.test_statistics.total_maintenance_request_sent_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_maintenance_request_recv_count: {str(abc.test_statistics.total_maintenance_request_recv_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_maintenance_response_sent_count: {str(abc.test_statistics.total_maintenance_response_sent_count)}")
                    self.ParamMgr.Logger.info(
                        f"SUT: {peer_info}, total_maintenance_response_recv_count: {str(abc.test_statistics.total_maintenance_response_recv_count)}")

                    status_is_pass = ResponseStatus.PASS
                    self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                      testcase_type=testcase_type,
                                                                      status_is_pass=status_is_pass)

                elif testcase_type == TestcaseType.FILE_TRANSFER_FROM_SERVER:
                    self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.FILE_TRANSFER_FROM_SERVER")
                    # Request
                    if data_object is not None:
                        filename = None
                        have_bytes = 0
                        meow = None

                        if 'filename' in data_object:
                            filename = data_object['filename']
                        # so that we can give them back proper data, they tell us how much they have in have_bytes
                        # then we use seek command to skip over that part and send them the next part
                        if 'have_bytes' in data_object:
                            have_bytes = data_object['have_bytes']

                        if os.path.exists(filename):
                            # it would be bad if we got here and the file doesn't exist, typo in filename in script?
                            chunk_data = None

                            try:
                                md5_filename_hash = self.ParamMgr.calculate_md5(filename)
                                file_size_on_disk = os.path.getsize(filename)

                                with open(filename, 'rb') as file:
                                    if have_bytes > 0:
                                        file.seek(have_bytes)

                                    # lets try to use 1 tcp packet for each transfer
                                    filename_len = len(filename)
                                    # MTU is 1500 bytes
                                    # 1500 - tcp header = 1460 bytes for us to use
                                    # 40 bytes for key's in _data ('filename', 'md5_hash', 'data')
                                    # 32 bytes is size of md5
                                    buffer_size = 1460 - 40 - 32 - filename_len  # TODO make this a Parameter? # how big is mystuff?

                                    file_chunk = file.read(buffer_size)  # read in the file were we left off

                                    read_size = len(file_chunk)  # get the actual size read

                                    # convert binary to text
                                    text_chunk = binascii.b2a_base64(file_chunk).decode()
                                    md5_chunk = hashlib.md5(
                                        text_chunk.encode()).hexdigest()  # get md5 for packet checking

                                    md5_chunk_len = len(md5_chunk)  # don't need this, here just for fun

                                    is_done = False

                                    if file_size_on_disk <= have_bytes + read_size:
                                        # we sent them all of the file
                                        is_done = True
                                        self.ParamMgr.Logger.debug(f"file_size_on_disk is done")

                                    chunk_data = {'filename': str(filename), 'md5': md5_filename_hash,
                                                  'file_size': file_size_on_disk, 'md5_chunk': md5_chunk,
                                                  'file_chunk': text_chunk}

                                    chunk_data_len = len(chunk_data)  # don't need this, here just for fun
                                    self.ParamMgr.Logger.debug(  # don't need this, here just for fun
                                        f"chunk_data_len: {str(chunk_data_len)}, md5_chunk_len: {str(md5_chunk_len)}")

                            except Exception as e:
                                self.ParamMgr.Logger.error(f"Exception Error: {str(e)}")

                            self.ParamMgr.NetworkMgr.send_maintenance_message(
                                MessageType.MAINTENANCE_RESPONSE,
                                testcase_type=TestcaseType.FILE_TRANSFER_FROM_SERVER,
                                data=chunk_data)

                        else:
                            self.ParamMgr.Logger.error(f"Error, file not found: {str(filename)}")

                elif testcase_type == TestcaseType.IMG_GET_POS:
                    self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.IMG_GET_POS")
                    if data_object is not None:
                        have_correct_file = False
                        filename = None
                        md5_hash = None
                        variable_name = None

                        if 'filename' in data_object:
                            filename = data_object['filename']
                        if 'md5_hash' in data_object:
                            md5_hash = data_object['md5_hash']
                        if 'variable_name' in data_object:
                            variable_name = data_object['variable_name']

                        if os.path.exists(filename):
                            md5_hash_on_disk = self.ParamMgr.calculate_md5(filename)

                            if md5_hash == md5_hash_on_disk:
                                have_correct_file = True
                            else:
                                os.remove(filename)  # bad md5 sum, delete it and request new file

                        if not have_correct_file:
                            # don't have it, then get it
                            self.ParamMgr.Logger.warning(f"Warning: img file not found, requesting")
                            file_data = {'filename': filename}
                            status_is_pass = ResponseStatus.ERRR  # set as error for now
                            self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_REQUEST,
                                                                              testcase_type=TestcaseType.FILE_TRANSFER_FROM_SERVER,
                                                                              data=file_data)

                        # we requested the file, not we wait until we get the correct file before we proceed
                        while not have_correct_file:
                            while not os.path.exists(filename):
                                time.sleep(0.1)

                            while not have_correct_file:
                                if os.path.exists(filename):
                                    md5_hash_on_disk = self.ParamMgr.calculate_md5(filename)

                                    if md5_hash == md5_hash_on_disk:
                                        have_correct_file = True
                                    else:
                                        time.sleep(0.1)



                        # if we got here, then have_file should be True
                        if os.path.exists(filename):
                            md5_hash_on_disk = self.ParamMgr.calculate_md5(filename)

                            if md5_hash == md5_hash_on_disk:
                                # we have the correct file,
                                try:
                                    cwd = os.getcwd()
                                    haystack_image = os.path.join(cwd, '../scripts/gnome-calculator.png')
                                    # needle_image = os.path.join(cwd, 'scripts/gnome-calculator_btn_2.png')
                                    needle_image = filename
                                    point_a = None

                                    # the_box = pyautogui.locateOnScreen(filename)
                                    # point_a = pyautogui.center(the_box)
                                    self.ParamMgr.Logger.debug(f"point_a = pyautogui.locateAllOnScreen(filename)")
                                    screen_width, screen_height = pyautogui.size()

                                    # if you can have a screenshot of the screen and see everything, then it should work
                                    # however, if the screenshot shows black, then this won't work
                                    #  pyautogui.screenshot('screenshot.png', region=(200, 0, screen_width, screen_height))

                                    # found this while Google, it supposed to help locateOnScreen work
                                    pyautogui.FAILSAFE = True
                                    pyautogui.PAUSE = 1

                                    # make a timeout so were not looking forever
                                    start_time = datetime.now()
                                    # box_a = pyautogui.locateAllOnScreen(images_filename)
                                    box_a = None
                                    while box_a is None:
                                        box_a = pyautogui.locateOnScreen(haystack_image,
                                                                         region=(0, 0, screen_width, screen_height),
                                                                         confidence=0.8, grayscale=True)
                                        current_time = datetime.now()
                                        time_difference = current_time - start_time
                                        total_seconds = time_difference.total_seconds()
                                        if total_seconds > self.ParamMgr.client_response_timeout:
                                            break  # timeout occurred
                                        else:
                                            time.sleep(0.1)

                                    self.ParamMgr.Logger.debug(f"box_a: {str(box_a)}")

                                    # start_time = datetime.now()
                                    # box_c = None
                                    # while box_c is None:
                                    #     box_c = pyautogui.locateAll(needleImage, haystackImage, confidence=0.8, grayscale=False)
                                    #     current_time = datetime.now()
                                    #     time_difference = current_time - start_time
                                    #     total_seconds = time_difference.total_seconds()
                                    #     if total_seconds > self.ParamMgr.client_response_timeout:
                                    #         break  # timeout occurred
                                    #     else:
                                    #         time.sleep(0.1)
                                    #
                                    # if box_c is not None:
                                    #     for box in box_c:
                                    #         self.ParamMgr.Logger.debug(f"warning: box_c: {str(box.left)}, {str(box.top)}")

                                    if box_a is not None:
                                        # make a timeout so were not looking forever
                                        start_time = datetime.now()
                                        box_b = None
                                        while box_b is None:
                                            box_b = pyautogui.locateOnScreen(needle_image,
                                                                             region=(box_a.left, box_a.top, box_a.width,
                                                                                     box_a.height),
                                                                             confidence=0.9, grayscale=True)
                                            current_time = datetime.now()
                                            time_difference = current_time - start_time
                                            total_seconds = time_difference.total_seconds()
                                            if total_seconds > self.ParamMgr.client_response_timeout:
                                                break  # timeout occurred
                                            else:
                                                time.sleep(0.1)

                                        self.ParamMgr.Logger.debug(f"box_b: {str(box_b)}")

                                        if box_b is not None:
                                            self.ParamMgr.Logger.debug(f"location center: {str(box_b)}")

                                            point_a = pyautogui.center(box_b)
                                            self.ParamMgr.Logger.debug(f"location Point: {str(point_a)}")

                                            status_is_pass = ResponseStatus.PASS

                                            # TODO we don't want to click here, click is just during debug
                                            pyautogui.click(point_a.x, point_a.y)
                                    else:  # not box_a
                                        status_is_pass = ResponseStatus.ERRR

                                    if variable_name is not None and point_a is not None:
                                        self.ParamMgr.set_script_point(variable_name, point_a)
                                        status_is_pass = ResponseStatus.PASS

                                except pyautogui.ImageNotFoundException as e:
                                    status_is_pass = ResponseStatus.EERR
                                    self.ParamMgr.Logger.error(
                                        f"ImageNotFoundException Error, ImageNotFoundException: {str(e)}")

                                except pyautogui.PyAutoGUIException as e:
                                    status_is_pass = ResponseStatus.EERR
                                    self.ParamMgr.Logger.error(
                                        f"PyAutoGUIException Error, PyAutoGUIException: {str(e)}")

                                except Exception as e:
                                    status_is_pass = ResponseStatus.EERR
                                    self.ParamMgr.Logger.error(
                                        f"Exception Error, PyAutoGUIException: {str(e)}")

                            else:  # md5_hash mismatch
                                status_is_pass = ResponseStatus.ERRR
                                self.ParamMgr.Logger.error(
                                    f"Error, MD5 mismatch: actual:{str(md5_hash_on_disk)}, expected: {str(md5_hash)}")

                        else:  # not os.path.exists(filename)
                            status_is_pass = ResponseStatus.ERRR
                            self.ParamMgr.Logger.error(
                                f"Error, img file not found: {str(filename)}")

                    self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_RESPONSE,
                                                                      testcase_type=testcase_type,
                                                                      status_is_pass=status_is_pass)

                elif testcase_type == TestcaseType.GET_FILE_FROM_SERVER:
                    self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.GET_FILE_FROM_SERVER")
                    # Request

                    req_file_data = None

                    if data_object is not None:
                        filename = None
                        md5_filename_hash = None
                        have_file = False

                        if 'filename' in data_object:
                            filename = data_object['filename']
                        if 'md5' in data_object:
                            md5_filename_hash = data_object['md5']

                        if os.path.exists(filename):
                            md5_filename_received_hash = self.ParamMgr.calculate_md5(filename)
                            if md5_filename_received_hash == md5_filename_hash:
                                have_file = True

                        if not have_file:
                            if os.path.exists(filename):
                                os.remove(filename)

                            req_file_data = {'filename': str(filename)}

                            self.ParamMgr.NetworkMgr.send_maintenance_message(
                                MessageType.MAINTENANCE_REQUEST,
                                testcase_type=TestcaseType.FILE_TRANSFER_FROM_SERVER,
                                data=req_file_data)

                            start_time = datetime.now()
                            while not have_file:
                                if os.path.exists(filename):
                                    md5_filename_received_hash = self.ParamMgr.calculate_md5(filename)
                                    if md5_filename_received_hash == md5_filename_hash:
                                        have_file = True
                                    else:
                                        time.sleep(0.1)
                                else:
                                    time.sleep(0.1)
                                current_time = datetime.now()
                                time_difference = current_time - start_time
                                total_seconds = time_difference.total_seconds()
                                if total_seconds > self.ParamMgr.client_response_timeout:
                                    break  # timeout occurred


                    self.ParamMgr.NetworkMgr.send_maintenance_message(
                        MessageType.MAINTENANCE_RESPONSE,
                        testcase_type=TestcaseType.GET_FILE_FROM_SERVER,
                        data=None)


                else:
                    self.ParamMgr.Logger.warning(
                        f"Warning, run_maintenance_cmd, not implemented testcase_type: {str(testcase_type)}")

            except AttributeError as e:
                self.ParamMgr.Logger.error(f"AttributeError: {str(e)}")

            except ValueError as e:
                self.ParamMgr.Logger.error(f"ValueError Error: {str(e)}")

        # TODO do we want to move the self.ParamMgr.get_client_ledger(peer_info).test_statistics.total_maintenance_count += 1
        #  to here and count it before we send it or leave it in the maintenance_response?

        elif message_type == MessageType.MAINTENANCE_RESPONSE:

            self.ParamMgr.Logger.info(f"MaintenanceMessage Response from: {str(peer_info)},"
                                      f" TestcaseType: {str(maintenance_message.testcase_type)},"
                                      f" is_pass: {str(is_pass)},"
                                      f" data: {str(data_object)}")

            if data_object is not None:
                for key, value in data_object.items():
                    self.ParamMgr.Logger.info(f"Response data: {str(key)}, {str(value)}")

            if is_pass:
                self.ParamMgr.get_client_ledger(peer_info).test_statistics.total_maintenance_pass_count += 1
            else:
                self.ParamMgr.get_client_ledger(peer_info).test_statistics.total_maintenance_fail_count += 1

            if maintenance_message.testcase_type == TestcaseType.INIT:
                self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.INIT")
                client_count = self.ParamMgr.client_attendance.get_client_attendance_count()
                self.ParamMgr.Logger.debug(f"we have {str(client_count)} number of clients")
                # maybe we should add client attendence here for when we are client

            elif maintenance_message.testcase_type == TestcaseType.STOP_TEST:
                self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.STOP_TEST")

                # print out stats
                abc = self.ParamMgr.get_client_ledger(peer_info)
                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_testcase_count: {str(abc.test_statistics.total_testcase_count)}")
                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_testcase_pass_count: {str(abc.test_statistics.total_testcase_pass_count)}")
                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_testcase_fail_count: {str(abc.test_statistics.total_testcase_fail_count)}")

                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_variable_count: {str(abc.test_statistics.total_variable_count)}")
                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_variable_pass_count: {str(abc.test_statistics.total_variable_pass_count)}")
                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_variable_fail_count: {str(abc.test_statistics.total_variable_fail_count)}")

                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_maintenance_count: {str(abc.test_statistics.total_maintenance_count)}")
                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_maintenance_pass_count: {str(abc.test_statistics.total_maintenance_pass_count)}")
                self.ParamMgr.Logger.info(
                    f"SUT: {peer_info}, total_maintenance_fail_count: {str(abc.test_statistics.total_maintenance_fail_count)}")

            elif maintenance_message.testcase_type == TestcaseType.START_TEST:
                self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.START_TEST")

            elif testcase_type == TestcaseType.FILE_TRANSFER_FROM_SERVER:
                self.ParamMgr.Logger.info("ScriptEngine.run_maintenance_cmd.FILE_TRANSFER_FROM_SERVER")
                # Response

                # transfer file, we need to send little pieces of file to build it
                status_is_pass = ResponseStatus.NONE
                completed_file_transfer = False

                if data_object is not None:
                    filename = None
                    md5_filename_hash = None
                    file_size = None
                    md5_chunk = None
                    text_chunk = None
                    need_data = None
                    have_bytes = 0
                    meow = None

                    # filename of the file to transfer
                    if 'filename' in data_object:
                        filename = data_object['filename']
                    # the md5 sum of the whole file
                    if 'md5' in data_object:
                        md5_filename_hash = data_object['md5']
                    # the size of the file in bytes
                    if 'file_size' in data_object:
                        file_size = data_object['file_size']
                    # the md5 sum of the little part of the file that we are sharing
                    if 'md5_chunk' in data_object:
                        md5_chunk = data_object['md5_chunk']
                    # the little part of the file that we are sharing
                    if 'file_chunk' in data_object:
                        text_chunk = data_object['file_chunk']

                    if (filename is not None and
                            md5_filename_hash is not None and
                            file_size is not None and
                            md5_chunk is not None and
                            text_chunk is not None):

                        md5_received_chunk = hashlib.md5(text_chunk.encode()).hexdigest()

                        if md5_received_chunk == md5_chunk:

                            # convert text back to binary
                            file_chunk = binascii.a2b_base64(text_chunk.encode())

                            try:
                                file = open(filename, 'ab')  # append mode
                                file.write(file_chunk)
                                file.flush()
                                file.close()
                                status_is_pass = ResponseStatus.PASS  # if we got here, then we are good
                            except PermissionError as e:
                                self.ParamMgr.Logger.error(f"PermissionError: {str(e)}")
                            except IsADirectoryError as e:
                                self.ParamMgr.Logger.error(f"IsADirectoryError: {str(e)}")
                            except OSError as e:
                                self.ParamMgr.Logger.error(f"OSError: {str(e)}")
                            except TypeError as e:
                                self.ParamMgr.Logger.error(f"TypeError: {str(e)}")
                            except Exception as e:
                                self.ParamMgr.Logger.error(f"Exception Error: {str(e)}")

                        else:
                            # boo
                            self.ParamMgr.Logger.error(
                                f"Error, Received MD5 mismatch of chunk: actual:{str(md5_received_chunk)}, "
                                f" expected: {str(md5_chunk)}")
                            # TODO chunk data bad md5?? should we count the number of times?

                        if os.path.exists(filename):
                            have_bytes = os.path.getsize(filename)

                        if have_bytes < file_size:
                            # need more
                            self.ParamMgr.Logger.warning(
                                f"Warning, FILE_TRANSFER_FROM_SERVER, Need more file: filename: {str(filename)},"
                                f" current file size: {str(have_bytes)} "
                                f" of total file size:  {str(file_size)}")
                            need_data = {'filename': filename, 'have_bytes': have_bytes}

                        elif have_bytes == file_size:
                            # yay, we are done

                            md5_filename_received_hash = self.ParamMgr.calculate_md5(filename)
                            if md5_filename_received_hash == md5_filename_hash:
                                self.ParamMgr.Logger.debug(
                                    f"Successful FILE_TRANSFER_FROM_SERVER: filename: {str(filename)}")
                                status_is_pass = ResponseStatus.PASS  # might already be True, set it here again just to make sure
                                completed_file_transfer = True
                            else:
                                self.ParamMgr.Logger.error(f"Error, Saved MD5 mismatch: "
                                                           f" actual:{str(md5_filename_received_hash)},"
                                                           f" expected: {str(md5_filename_hash)}")
                        else:
                            self.ParamMgr.Logger.error(f"Error, Saved file larger than expected: "
                                                       f" actual:{str(have_bytes)},"
                                                       f" expected: {str(file_size)}")

                        if completed_file_transfer is not True:  # not true means we need more
                            self.ParamMgr.NetworkMgr.send_maintenance_message(MessageType.MAINTENANCE_REQUEST,
                                                                              testcase_type=TestcaseType.FILE_TRANSFER_FROM_SERVER,
                                                                              data=need_data)

            #######################################################
            # now that I am done processing the message, now I can trigger the response to go to the next step
            # this will response to all message_types
            self.ParamMgr.client_attendance.add_client_response(peer_info, message_type=message_type,
                                                                testcase_type=testcase_type)

    def print(self):
        print("Script dictionary contents:")
        print(self.script)
