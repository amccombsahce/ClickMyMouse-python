import queue
import socket
import threading
import time

import param_mgr as ParameterMgr
from message_type import *


# NetworkPacketMetaData
# both packet and meta data
class NetworkPacketMetaData:
    def __init__(self, packet, client_address):
        self.packet = packet
        self.client_address = client_address

    @classmethod
    def decode(cls, buffer):
        packet = buffer.packet
        client_address = buffer.client_address
        return cls(packet, client_address)


class NetworkMgr:

    def __init__(self, pp: ParameterMgr):
        self.ParamMgr = pp
        self.ip_address = pp.ConfigMgr.get_ip_address()
        self.tcp_port = pp.ConfigMgr.get_tcp_port()
        self.port = 0

        self._connections = []
        self._outgoing_message_queue = queue.Queue()
        self._incoming_message_queue = queue.Queue()

        # run_incoming_message_queue
        # Start a thread to listen for incoming connections
        # self.listener_thread = threading.Thread(target=self.start_listener)
        # self.listener_thread.start()

        # Start a thread to receive incoming messages
        # self.receive_thread = threading.Thread(target=self.receive_messages)
        # self.receive_thread.start()

        # Start a thread to send outgoing messages
        # self.incoming_thread = threading.Thread(target=self.run_incoming_message_queue)
        # self.incoming_thread.start()

        # Start a thread to send outgoing messages
        # self.outgoing_thread = threading.Thread(target=self.run_outgoing_message_queue)
        # self.outgoing_thread.start()

        self._exit_event = threading.Event()  # Event to signal thread exit

        self.my_address = None
        self.my_port = 0

        # self.buffer = b''
        # self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #
        #

        # # self.server_socket.bind(('0.0.0.0', self.port))
        # self.server_socket.bind(('0.0.0.0', 0))
        #

        # my_address, my_port = self.server_socket.getsockname()
        # self.port = my_port

        #
        # self.server_socket.listen(5)
        #
        # print(f"my_address: {str(my_address)}, my_port: {str(my_port)}")
        # self.ParamMgr.Logger.debug(f"NetworkMgr.init, my_address: {str(my_address)}, my_port: {str(my_port)}")
        #
        # self.ParamMgr.main_gui.set_connections_label(str(my_port))
        # # Create a thread for receiving messages
        # # self.receive_thread = threading.Thread(target=self.ParamMgr.NetworkMgr.receive_messages)
        # # self.receive_thread.daemon = True
        # # self.receive_thread.start()

    def add_connections(self, connection):
        if connection not in self._connections:
            self._connections.append(connection)

    def del_connections(self, connection):
        if connection in self._connections:
            self._connections.remove(connection)

    def start_listener(self):
        time.sleep(1)
        self.ParamMgr.Logger.debug(f"NetworkMgr.start_listener")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # #  TODO change back to self.port
        # #  TODO do we want to use the port in the .configfile?
        port = self.ParamMgr.ConfigMgr.get_tcp_port()
        # server_socket.bind(('0.0.0.0', port))
        server_socket.bind(('0.0.0.0', 0))
        server_socket.listen(5)

        self.my_address, self.port = server_socket.getsockname()
        # self.port = my_port

        print(f"port: {str(self.port)}")

        self.ParamMgr.Logger.info(f"port: {str(self.port)}")

        while not self._exit_event.is_set():
            try:
                client_socket, addr = server_socket.accept()
                self.add_connections(client_socket)
                peer_info = client_socket.getpeername()
                self.ParamMgr.main_gui.add_connection(peer_info, "ACCEPT")

                self.ParamMgr.Logger.info(
                    f"NetworkMgr.start_listener, Connected to {str(addr)}, peer_info:{str(peer_info)}")
                #            self.ParamMgr.main_gui.add_connection(str(addr))
                print(f"start_listener.Connected to {str(addr)}")

            except Exception as e:
                print(f"Error accepting connection: {e.with_traceback()}")

    def receive_messages(self):
        self.ParamMgr.Logger.debug(f"NetworkMgr.receive_messages")
        while not self._exit_event.is_set():
            for abc_socket in self._connections:
                try:
                    # message_type_data = client_socket.recv(4)  # 4 bytes for the integer message type
                    # message_type_value = struct.unpack('!I', message_type_data)[0]
                    # message_type = MessageType(message_type_value)
                    # data = client_socket.recv(1024).decode()
                    peer_info = None
                    packet = None

                    if abc_socket is not None:
                        if abc_socket.fileno != -1:  # not closed
                            packet = abc_socket.recv(1024)
                            peer_info = abc_socket.getpeername()
                        # try to glue fragmented packets together?
                        # self.buffer = packet  #  self.buffer += packet

                    buffer_length = len(packet)
                    if buffer_length > 0:  # zero length means socket closed

                        # if user clicks stop then we should trash messages by not putting them into _incoming_message_queue
                        if self.ParamMgr.stop_event.is_set():
                            continue

                        self.ParamMgr.Logger.debug(f"NetworkMgr.receive_messages, received: {buffer_length} bytes")

                        npmd = NetworkPacketMetaData(packet, peer_info)

                        self._incoming_message_queue.put(npmd)

                    else:  # buffer_length is 0
                        self.ParamMgr.Logger.warning(f"Warning, NetworkMgr.receive_messages, "
                                                   f"received zero bytes, disconnecting socket: {str(peer_info)}")

                        abc_socket.close()
                        self.del_connections(abc_socket)  # remove from private list
                        self.ParamMgr.main_gui.del_connection(peer_info)  # remove from gui list
                        self.ParamMgr.client_attendance.del_client_attendance(
                            peer_info)  # remove from master list for checking replies
                        abc_socket = None

                except socket.error as e:
                    self.ParamMgr.Logger.error(f"Socket Exception, NetworkMgr.receive_messages: {str(e)}")
                    peer_info = abc_socket.getpeername()
                    abc_socket.close()
                    self.del_connections(abc_socket)  # remove from private list
                    self.ParamMgr.main_gui.del_connection(peer_info)  # remove from gui list
                    abc_socket = None
                except Exception as e:
                    self.ParamMgr.Logger.error(
                        f"Exception Error, NetworkMgr.receive_messages, receiving message: {str(e)}")

        self.ParamMgr.Logger.debug(f"NetworkMgr.receive_messages, exit")

    def send_message_to_client(self, abc_socket, message):
        try:
            python_is_trash = message.to_str()

            self.ParamMgr.Logger.debug(f"NetworkMgr.send_message_to_client, message: {python_is_trash}")
            number_of_byes_sent = abc_socket.send(message.encode())
            self.ParamMgr.Logger.debug(f"NetworkMgr.send_message_to_client, "
                                       f"sent {str(number_of_byes_sent)} bytes")

        except Exception as e:
            print(f"Error sending message: {str(e)}")
            self.ParamMgr.Logger.error(f"Exception Error, NetworkMgr.send_message_to_client: {str(e)}")
        # client_socket.close()

    # run_incoming_message_queue gets messages from _incoming_message_queue that was put here by socket
    def run_incoming_message_queue(self):
        while not self._exit_event.is_set():
            try:

                print(f"run_incoming_message_queue")

                peer_info = None
                buffer = self._incoming_message_queue.get()
                npmd = NetworkPacketMetaData.decode(buffer)
                packet = npmd.packet
                peer_info = npmd.client_address

                print(f"Message: {str(packet)}")

                abc001 = Message.decode(packet)
                message_type = abc001.message_type

                # if user clicks stop then we should trash messages
                if self.ParamMgr.stop_event.is_set():
                    continue

                # this might not be needed, use this if script_engine will get packets from queue
                # self._incoming_message_queue.put(packet)

                if abc001:
                    self.ParamMgr.Logger.debug(f"NetworkMgr.run_incoming_message_queue, Received: {packet},"
                                               f" MessageType: {message_type}, From: {str(peer_info)}")

                # if self.ParamMgr.is_server:
                # I am the server, this message is from the client
                if message_type == MessageType.TEST_CASE_RESPONSE:
                    self.ParamMgr.Logger.debug(f"NetworkMgr.run_incoming_message_queue MessageType.TEST_CASE_RESPONSE")

                    received_message = TestcaseMessage.decode(packet)
                    self.ParamMgr.client_attendance.add_client_response(peer_info, message_type=message_type,
                                                                        testcase_type=received_message.testcase_type)

                    is_pass = received_message.status_is_pass
                    abc_data = received_message.data
                    self.ParamMgr.Logger.info(f"Testcase Response from: {str(peer_info)},"
                                              f" TestcaseType: {str(received_message.testcase_type)},"
                                              f" is_pass: {str(is_pass)},"
                                              f" data: {str(abc_data)}")

                    if abc_data is not None:
                        for key, value in abc_data:
                            self.ParamMgr.Logger.info(f"Response data: {str(key)}, {str(value)}")

                    self.ParamMgr.get_client_ledger(peer_info).test_statistics.total_testcase_count += 1
                    if is_pass:
                        self.ParamMgr.get_client_ledger(peer_info).test_statistics.total_testcase_pass_count += 1
                    else:
                        self.ParamMgr.get_client_ledger(peer_info).test_statistics.total_testcase_fail_count += 1

                elif message_type == MessageType.TEST_CASE_VARIABLE_RESPONSE:
                    self.ParamMgr.Logger.debug(f"NetworkMgr.run_incoming_message_queue MessageType.TEST_CASE_VARIABLE_RESPONSE")
                    received_variable_message = TestcaseVariableTypeMessage.decode(packet)
                    self.ParamMgr.client_attendance.add_client_response(peer_info, message_type=message_type,
                                                                        testcase_type=received_variable_message.testcase_variable_type)

                    abc_data = received_variable_message.data

                    self.ParamMgr.Logger.info(f"Testcase Variable Response from: {str(peer_info)},"
                                              f" TestcaseVariableType: {str(received_variable_message.testcase_variable_type)},"
                                              f" data: {str(abc_data)}")

                    if abc_data is not None:
                        for key, value in abc_data.items():
                            self.ParamMgr.Logger.info(f"Response data: {str(key)}, {str(value)}")

                    self.ParamMgr.get_client_ledger(peer_info).test_statistics.total_variable_count += 1

                elif message_type == MessageType.MAINTENANCE_RESPONSE:
                    self.ParamMgr.Logger.debug(
                        f"NetworkMgr.run_incoming_message_queue MessageType.MAINTENANCE_RESPONSE")
                    received_maintenance_message = MaintenanceMessage.decode(packet)

                    self.ParamMgr.ScriptEngine.run_maintenance_cmd(received_maintenance_message, peer_info=peer_info)

                elif message_type == MessageType.INIT_RESPONSE:
                    self.ParamMgr.Logger.debug(
                        f"NetworkMgr.run_incoming_message_queue MessageType.INIT_RESPONSE")

                    received_init_message = MaintenanceMessage.decode(packet)
                    self.ParamMgr.client_attendance.add_client_response(peer_info, message_type=message_type,
                                                                        testcase_type=received_init_message.testcase_type)
                    is_pass = received_init_message.status_is_pass
                    abc_data = received_init_message.data
                    self.ParamMgr.Logger.info(f"Init Response from: {str(peer_info)},"
                                              f" TestcaseType: {str(received_init_message.testcase_type)},"
                                              f" is_pass: {str(is_pass)},"
                                              f" data: {str(abc_data)}")

                    if abc_data is not None:
                        for key, value in abc_data.items():
                            self.ParamMgr.Logger.info(f"Response data: {str(key)}, {str(value)}")

                elif message_type == MessageType.INIT:
                    self.ParamMgr.Logger.debug(
                        f"NetworkMgr.run_incoming_message_queue MessageType.INIT")

                    self.ParamMgr.main_gui.add_connection(str(peer_info), "INIT")
                    self.ParamMgr.client_attendance.add_client_attendance(peer_info)

                    # set client ledger
                    self.ParamMgr.set_client_ledger(peer_info)

                    # tell the client to add me to their add_client_attendance, so that wait_for_client_response
                    # will work both ways
                    self.ParamMgr.NetworkMgr.send_maintenance_message(message_type=MessageType.MAINTENANCE_REQUEST,
                                                                      testcase_type=TestcaseType.INIT)

                elif message_type == MessageType.KEEP_ALIVE:
                    self.ParamMgr.Logger.debug(
                        f"NetworkMgr.run_incoming_message_queue MessageType.KEEP_ALIVE")
                    received_message = KeepAliveMessage.decode(packet)

                    # self.ParamMgr.NetworkMgr.send_message(MessageType.KEEP_ALIVE)

                # else:
                # I am the client, this message is from the server
                elif message_type == MessageType.TEST_CASE_REQEUST:
                    received_message = TestcaseMessage.decode(packet)
                    self.ParamMgr.ScriptEngine.client_testcase_cmd(received_message)

                elif message_type == MessageType.TEST_CASE_VARIABLE_REQUEST:
                    received_message = TestcaseVariableTypeMessage.decode(packet)
                    self.ParamMgr.ScriptEngine.client_variable_cmd(received_message)

                elif message_type == MessageType.MAINTENANCE_REQUEST:
                    received_message = MaintenanceMessage.decode(packet)

                    self.ParamMgr.ScriptEngine.run_maintenance_cmd(received_message, peer_info=peer_info)

                elif message_type == MessageType.INIT_REQUEST:
                    received_init_message = MaintenanceMessage.decode(packet)
                    is_pass = received_init_message.status_is_pass
                    abc_data = received_init_message.data

                    self.ParamMgr.Logger.debug(
                        f"Init Request from: {str(peer_info)}, TestcaseType: {str(received_init_message.testcase_type)},"
                        f" is_pass: {str(is_pass)}, data: {str(abc_data)}")

                    if abc_data is not None:
                        for key, value in abc_data.items():
                            self.ParamMgr.Logger.info(f"Request data: {str(key)}, {str(value)}")

                    self.ParamMgr.client_attendance.add_client_attendance(peer_info)

                    self.ParamMgr.ScriptEngine.run_maintenance_cmd(maintenance_message=received_init_message, peer_info=peer_info)

                else:
                    self.ParamMgr.Logger.error(f"Error, unknown MsgType {str(message_type)}")

            except Exception as e:
                self.ParamMgr.Logger.error(f"Exception Error, NetworkMgr.run_incoming_message_queue, {str(e)}")

    def run_outgoing_message_queue(self):
        while not self._exit_event.is_set():
            print(f"run_outgoing_message_queue")
            abc_socket = None
            peer_info = None
            message = self._outgoing_message_queue.get()
            print(f"Message: {str(message)}")

            for abc_socket in self._connections:
                try:
                    file_no = abc_socket.fileno()
                    sock_name = abc_socket.getsockname()
                    peer_info = abc_socket.getpeername()
                    if file_no > 0:
                        self.send_message_to_client(abc_socket, message)
                    else:
                        self.ParamMgr.Logger.debug(f"Dead socket, removing: {str(peer_info)}")
                        self._connections.remove(abc_socket)
                        self.ParamMgr.main_gui.del_connection(peer_info)

                except Exception as e:
                    self.ParamMgr.Logger.error(f"Error in run: {str(e)}")
                    self.ParamMgr.Logger.debug(f"Dead socket, removing: {str(peer_info)}")
                    self._connections.remove(abc_socket)
                    self.ParamMgr.main_gui.del_connection(peer_info)

    #               listener_thread.join()

    def send_maintenance_message(self, message_type: MessageType = MessageType.INIT,
                                 testcase_type: TestcaseType = TestcaseType.INIT, status_is_pass=False, data=None):
        self.ParamMgr.Logger.debug(f"NetworkMgr.send_maintenance_message, adding maintenance message to queue")

        message = None

        if message_type == MessageType.MAINTENANCE_REQUEST:  # assuming test cases are the most popular
            message = MaintenanceMessage(MessageType.MAINTENANCE_REQUEST, testcase_type=testcase_type,
                                         status_is_pass=status_is_pass, data=data)

        elif message_type == MessageType.MAINTENANCE_RESPONSE:  # assuming test cases are the most popular
            message = MaintenanceMessage(MessageType.MAINTENANCE_RESPONSE, testcase_type=testcase_type,
                                         status_is_pass=status_is_pass, data=data)

        elif message_type == MessageType.INIT_REQUEST:  # assuming test cases are the most popular
            message = MaintenanceMessage(MessageType.INIT_REQUEST, testcase_type=testcase_type,
                                         status_is_pass=status_is_pass, data=data)

        elif message_type == MessageType.INIT_RESPONSE:  # assuming test cases are the most popular
            message = MaintenanceMessage(MessageType.INIT_RESPONSE, testcase_type=testcase_type,
                                         status_is_pass=status_is_pass, data=data)
        else:
            self.ParamMgr.Logger.error(f"Error, NetworkMgr.send_maintenance_message,"
                                       f" unknown MessageType {message_type.value:x}")

        self._outgoing_message_queue.put(message)

    #
    # send_variable_message
    # send Int, String, Point as a separate type of message
    def send_variable_message(self, message_type: MessageType = MessageType.TEST_CASE_VARIABLE_REQUEST,
                              testcase_variable_type=TestcaseVariableType.INIT, data=None):
        self.ParamMgr.Logger.debug(f"NetworkMgr.send_variable_message, adding variable message to queue")

        message = None

        if message_type == MessageType.TEST_CASE_VARIABLE_REQUEST:  # assuming test cases are the most popular
            message = TestcaseVariableTypeMessage(MessageType.TEST_CASE_VARIABLE_REQUEST,
                                                  testcase_variable_type=testcase_variable_type, data=data)

        elif message_type == MessageType.TEST_CASE_VARIABLE_RESPONSE:  # assuming test cases are the most popular
            message = TestcaseVariableTypeMessage(MessageType.TEST_CASE_VARIABLE_RESPONSE,
                                                  testcase_variable_type=testcase_variable_type, data=data)

        else:
            self.ParamMgr.Logger.error(f"Error, NetworkMgr.send_variable_message, unknown MessageType")

        self._outgoing_message_queue.put(message)

    def send_testcase_message(self, message_type: MessageType = MessageType.INIT, step_number: int = 0,
                              testcase_type: TestcaseType = TestcaseType.INIT, data=None, status_is_pass=False):
        # abc = self.ParamMgr.get_date_time()
        self.ParamMgr.Logger.debug(f"NetworkMgr.send_testcase_message, adding message to queue")
        message = None

        if message_type == MessageType.TEST_CASE_REQEUST:  # assuming test cases are the most popular
            message = TestcaseMessage(MessageType.TEST_CASE_REQEUST, step_number=step_number,
                                      testcase_type=testcase_type, data=data,
                                      status_is_pass=status_is_pass)

        elif message_type == MessageType.TEST_CASE_RESPONSE:  # assuming test cases are the most popular
            message = TestcaseMessage(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                      testcase_type=testcase_type, data=data, status_is_pass=status_is_pass)

        else:
            self.ParamMgr.Logger.error(f"Error, NetworkMgr.send_testcase_message, unknown MessageType")

        self._outgoing_message_queue.put(message)

    def send_message(self, message_type: MessageType = MessageType.INIT, step_number: int = 0,
                     testcase_type: TestcaseType = TestcaseType.INIT, data=None, status_is_pass=False):
        # abc = self.ParamMgr.get_date_time()
        self.ParamMgr.Logger.debug(f"NetworkMgr.send_message, adding message to queue")
        message = None

        if message_type == MessageType.TEST_CASE_REQEUST:  # assuming test cases are the most popular
            message = TestcaseMessage(step_number=step_number, testcase_type=testcase_type, data=data,
                                      status_is_pass=status_is_pass)

        elif message_type == MessageType.TEST_CASE_RESPONSE:  # assuming test cases are the most popular
            message = TestcaseMessage(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                      testcase_type=testcase_type, data=data, status_is_pass=status_is_pass)

        elif message_type == MessageType.INIT:
            message = Message(MessageType.INIT)

        elif message_type == MessageType.KEEP_ALIVE:
            message = KeepAliveMessage()

        self._outgoing_message_queue.put(message)

    def connect_to_server(self, address, port):
        try:
            self.ParamMgr.Logger.debug(f"NetworkMgr.connect_to_server")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = client_socket.connect_ex((address, port))
            if result == 0:
                peer_info = client_socket.getpeername()
                self.add_connections(client_socket)
                self.ParamMgr.Logger.debug(f"Connected to {address}:{port}")
                self.ParamMgr.Logger.debug(f"connections count: {len(self._connections)}")
                self.ParamMgr.main_gui.add_connection(peer_info, "connect_to_server")
                return client_socket
            else:
                self.ParamMgr.Logger.error(f"Error, NetworkMgr.connect_to_server")
        except Exception as e:
            print(f"Error connecting to {address}:{port}: {str(e)}")

        return None



