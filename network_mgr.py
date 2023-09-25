import queue
import socket
import sys
import threading
import struct

import param_mgr as ParamMgr
from message_type import *
from logger import Logger


class NetworkMgr:

    def receive_messages(self, stop_event):
        self.ParamMgr.Logger.debug(f"NetworkMgr.receive_messages")
        while not stop_event.is_set():
            for abc_socket in self.connections:
                try:
                    # message_type_data = client_socket.recv(4)  # 4 bytes for the integer message type
                    # message_type_value = struct.unpack('!I', message_type_data)[0]
                    # message_type = MessageType(message_type_value)
                    # data = client_socket.recv(1024).decode()
                    peer_info = None

                    if abc_socket is not None:
                        if abc_socket.fileno != -1:  # not closed
                            self.buffer = abc_socket.recv(1024)
                            peer_info = abc_socket.getpeername()
                        # try to glue fragmented packets together?
                        # self.buffer = packet  #  self.buffer += packet

                    buffer_length = len(self.buffer)
                    if buffer_length > 0:  # zero length means socket closed
                        self.ParamMgr.Logger.debug(f"NetworkMgr.receive_messages, received: {buffer_length} bytes")

                        # message_type_data = self.buffer[:4]  # first 4 bytes for the integer message type
                        # message_type_value = struct.unpack('!I', message_type_data)[0]
                        # message_type = MessageType(message_type_value)
                        # data = self.buffer[4:].decode()
                        packet = self.buffer
                        abc001 = Message.decode(packet)
                        message_type = abc001.message_type

                        if abc001:
                            self.ParamMgr.Logger.debug(f"NetworkMgr.receive_messages, Received: {packet},"
                                                       f" MessageType: {message_type}, From: {str(peer_info)}")

                        # if self.ParamMgr.is_server:
                        # I am the server, this message is from the client
                        if message_type == MessageType.TEST_CASE_RESPONSE:
                            self.ParamMgr.client_attendance.add_client_response(abc_socket)

                            received_message = TestcaseMessage.decode(packet)
                            is_pass = received_message.status_is_pass

                            abc_data = received_message.data

                            self.ParamMgr.Logger.info(f"Testcase Response from: {str(peer_info)},"
                                                      f" TestcaseType: {str(received_message.testcase_type)},"
                                                      f" is_pass: {str(is_pass)},"
                                                      f" data: {str(abc_data)}")

                        elif message_type == MessageType.TEST_CASE_VARIABLE_RESPONSE:
                            self.ParamMgr.client_attendance.add_client_response(abc_socket)
                            received_variable_message = TestcaseVariableTypeMessage.decode(packet)

                            abc_data = received_variable_message.data

                            self.ParamMgr.Logger.info(f"Testcase Variable Response from: {str(peer_info)},"
                                                      f" TestcaseVariableType: {str(received_variable_message.testcase_variable_type)},"
                                                      f" data: {str(abc_data)}")

                        elif message_type == MessageType.MAINTENANCE_RESPONSE:
                            self.ParamMgr.client_attendance.add_client_response(abc_socket)
                            received_maintenance_message = MaintenanceMessage.decode(packet)
                            is_pass = received_maintenance_message.status_is_pass
                            abc_data = received_maintenance_message.data

                            self.ParamMgr.Logger.info(f"MaintenanceMessage Response from: {str(peer_info)},"
                                                      f" TestcaseType: {str(received_maintenance_message.testcase_type)},"
                                                      f" is_pass: {str(is_pass)},"
                                                      f" data: {str(abc_data)}")





                        elif message_type == MessageType.INIT:
                            self.ParamMgr.main_gui.add_connection(str(peer_info))
                            self.ParamMgr.client_attendance.add_client_attendance(abc_socket)
                            self.add_connections(abc_socket)

                        elif message_type == MessageType.KEEP_ALIVE:
                            received_message = KeepAliveMessage.decode(packet)

                            # self.ParamMgr.NetworkMgr.send_message(MessageType.KEEP_ALIVE)

                        # else:
                        # I am the client, this message is from the server
                        if message_type == MessageType.TEST_CASE_REQEUST:
                            received_message = TestcaseMessage.decode(packet)
                            self.ParamMgr.ScriptEngine.client_runscript_cmd(received_message)

                        elif message_type == MessageType.TEST_CASE_VARIABLE_REQUEST:
                            received_message = TestcaseVariableTypeMessage.decode(packet)
                            self.ParamMgr.ScriptEngine.client_variable_cmd(received_message)

                        elif message_type == MessageType.MAINTENANCE_REQUEST:
                            received_message = MaintenanceMessage.decode(packet)
                            self.ParamMgr.ScriptEngine.client_maintenance_cmd(received_message)

                    else:  # buffer_length is 0
                        self.ParamMgr.Logger.debug(f"NetworkMgr.receive_messages, received zero bytes, disconnecting "
                                                   f"socket: {str(peer_info)}")

                        abc_socket.close()
                        self.del_connections(abc_socket)  # remove from private list
                        self.ParamMgr.main_gui.del_connection(peer_info)  # remove from gui list
                        abc_socket = None


                except socket.error as e:
                    print(f"NetworkMgr.receive_messages: Socket error: {str(e)}")
                    self.ParamMgr.Logger.error(f"NetworkMgr.receive_messages: Socket error: {str(e)}")
                    peer_info = abc_socket.getpeername()
                    abc_socket.close()
                    self.del_connections(abc_socket)  # remove from private list
                    self.ParamMgr.main_gui.del_connection(peer_info)  # remove from gui list
                    abc_socket = None
                except Exception as e:
                    self.ParamMgr.Logger.error(f"01 Error NetworkMgr.receive_messages, receiving message: {str(e)}")

        self.ParamMgr.Logger.debug(f"NetworkMgr.receive_messages, exit")

    def signal_handler(self, signal, frame):
        print('Interrupt received, closing socket...')
        sys.exit(0)

    def __init__(self, pp: ParamMgr):
        self.ParamMgr = pp
        self.ip_address = pp.ConfigMgr.get_ip_address()
        self.udp_port = pp.ConfigMgr.get_udp_port()
        self.tcp_port = pp.ConfigMgr.get_tcp_port()
        self.connections = []
        self.message_queue = queue.Queue()
        self.port: int = 5000
        self.buffer = b''
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #  TODO change back to self.port
        # self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.bind(('0.0.0.0', 0))

        # TODO do we want to use the port in the .configfile?
        my_address, my_port = self.server_socket.getsockname()
        self.port = my_port
        # TODO end

        self.server_socket.listen(5)

        print(f"my_address: {str(my_address)}, my_port: {str(my_port)}")
        self.ParamMgr.Logger.debug(f"NetworkMgr.init, my_address: {str(my_address)}, my_port: {str(my_port)}")

        self.ParamMgr.main_gui.set_connections_label(str(my_port))
        # Create a thread for receiving messages
        # self.receive_thread = threading.Thread(target=self.ParamMgr.NetworkMgr.receive_messages)
        # self.receive_thread.daemon = True
        # self.receive_thread.start()

    def add_connections(self, connection):
        if connection not in self.connections:
            self.connections.append(connection)

    def del_connections(self, connection):
        if connection in self.connections:
            self.connections.remove(connection)

    def start_listener(self, stop_event):
        self.ParamMgr.Logger.debug(f"NetworkMgr.start_listener")
        while not stop_event.is_set():
            client_socket, addr = self.server_socket.accept()

            self.connections.append(client_socket)
            self.ParamMgr.Logger.info(f"NetworkMgr.start_listener, Connected to {str(addr)}")
            #            self.ParamMgr.main_gui.add_connection(str(addr))
            print(f"start_listener.Connected to {str(addr)}")

        self.ParamMgr.Logger.debug(f"NetworkMgr.start_listener, exit")

    def send_message_to_client(self, abc_socket, message):
        try:
            number_of_byes_sent = abc_socket.send(message.encode())
            self.ParamMgr.Logger.debug(f"NetworkMgr.send_message_to_client, sent {str(number_of_byes_sent)} bytes")

        except Exception as e:
            print(f"Error sending message: {str(e)}")
            self.ParamMgr.Logger.error(f"Error, NetworkMgr.send_message_to_client: {str(e)}")
        # client_socket.close()

    def run(self, stop_event):
        listener_thread = threading.Thread(target=self.start_listener, args=(stop_event,))
        listener_thread.daemon = True
        listener_thread.start()

        while not stop_event.is_set():
            print(f"run")
            try:
                message = self.message_queue.get()
                print(f"Message: {str(message)}")
                for abc_socket in self.connections:
                    file_no = abc_socket.fileno()
                    peer_info = abc_socket.getpeername()
                    if file_no < 0:
                        self.ParamMgr.Logger.debug(f"Dead socket, removing: {str(peer_info)}")
                        self.connections.remove(abc_socket)
                        self.main_gui.del_connection(peer_info)
                        continue

                    self.send_message_to_client(abc_socket, message)


            except Exception as e:
                print(f"Error in run: {str(e)}")

    #               listener_thread.join()

    def send_maintenance_message(self, message_type: MessageType = MessageType.INIT,
                                 testcase_type: TestcaseType = TestcaseType.INIT, status_is_pass=False, data=None):
        self.ParamMgr.Logger.debug(f"NetworkMgr.send_variable_message, adding variable message to queue")

        message = None

        if message_type == MessageType.MAINTENANCE_REQUEST:  # assuming test cases are the most popular
            message = MaintenanceMessage(MessageType.MAINTENANCE_REQUEST, testcase_type=testcase_type,
                                         status_is_pass=status_is_pass, data=data)

        elif message_type == MessageType.MAINTENANCE_RESPONSE:  # assuming test cases are the most popular
            message = MaintenanceMessage(MessageType.MAINTENANCE_RESPONSE, testcase_type=testcase_type,
                                         status_is_pass=status_is_pass, data=data)

        else:
            self.ParamMgr.Logger.error(f"Error, NetworkMgr.send_maintenance_message, unknown MessageType")

        self.message_queue.put(message)

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

        self.message_queue.put(message)

    def send_testcase_message(self, message_type: MessageType = MessageType.INIT, step_number: int = 0,
                              testcase_type: TestcaseType = TestcaseType.INIT, data=None, status_is_pass=False):
        # abc = self.ParamMgr.get_date_time()
        self.ParamMgr.Logger.debug(f"NetworkMgr.send_testcase_message, adding message to queue")
        message = None

        if message_type == MessageType.TEST_CASE_REQEUST:  # assuming test cases are the most popular
            message = TestcaseMessage(MessageType.TEST_CASE_REQEUST, step_number=step_number, testcase_type=testcase_type, data=data,
                                      status_is_pass=status_is_pass)

        elif message_type == MessageType.TEST_CASE_RESPONSE:  # assuming test cases are the most popular
            message = TestcaseMessage(MessageType.TEST_CASE_RESPONSE, step_number=step_number,
                                      testcase_type=testcase_type, data=data, status_is_pass=status_is_pass)

        else:
            self.ParamMgr.Logger.error(f"Error, NetworkMgr.send_testcase_message, unknown MessageType")

        self.message_queue.put(message)

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

        self.message_queue.put(message)

    def connect_to_client(self, address, port):
        try:
            self.ParamMgr.main_gui.logger.debug(f"NetworkMgr.connect_to_client")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((address, port))
            self.connections.append(client_socket)
            print(f"Connected to {address}:{port}")
            print(f"connections count: {len(self.connections)}")
            self.ParamMgr.Logger.debug(f"connections count: {len(self.connections)}")
            return client_socket
        except Exception as e:
            print(f"Error connecting to {address}:{port}: {str(e)}")
