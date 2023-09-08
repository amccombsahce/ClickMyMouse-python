import asyncio
import socket
import ConfigMgr
import threading
import time

import ParamMgr
from Logger import Logger

# creat a class
class NetworkMgr:

    #  def __init__(self, ip_address, udp_port, tcp_port):
    def __init__(self, pp: ParamMgr):
        self.ParamMgr = pp
        self.ip_address = pp.config.get_ip_address()
        self.udp_port = pp.config.get_udp_port()
        self.tcp_port = pp.config.get_tcp_port()
        self.logging = pp.logging
        self.tcp_socket = None
        self.tcp_server_thread = None
        self.tcp_client_thread = None
        self.connections = []
        self.sock = None

        self.my_udp_listening_thread = threading.Thread(target=self.listen_udp, args=()).start()

    def get_connections(self):
        return self.connections
    def send_udp_message(self, message: str):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send the message
        self.udp_sock.sendto(message.encode(), (self.ip_address, self.udp_port))
        # Close the socket
        self.udp_sock.close()

    def receive_udp_message(self):
        # Create a UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to the IP and port
        self.udp_sock.bind((self.ip_address, self.udp_port))
        # Receive the message
        data, addr = self.udp_sock.recvfrom(1024)
        # Close the socket
        self.udp_sock.close()
        # Return the received message
        return data.decode(), addr

    def listen_udp(self):
        while True:
            message, address = self.receive_udp_message()
            abc = 'received {} bytes from {} : {}'.format(len(message), address, message)
            logging = ParamMgr.logging
            logging.debug(abc)
            print(abc)
            time.sleep(0)

    def start_tcp_server_worker(self):
        while True:
            # establish a connection
            client_socket, addr = pm.NetworkMgr.tcp_socket.accept()

            pm.logging.debug("connection from: %s" % str(addr))

            msg = 'Thank you for connecting' + "\r\n"
            client_socket.send(msg.encode('ascii'))
            # client_socket.close()

    def start_tcp_server(pm: ParamMgr):
        pm.logging.debug("start_server")
        pm.network.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = str(socket.gethostname())
        pm.logging.debug("hostname: %s" % host)
        pm.network.tcp_socket.bind((pm.network.ip_address, pm.network.tcp_port))
        pm.network.tcp_socket.listen(10)

        pm.tcp_server_thread = threading.Thread(target=pm.network.start_tcp_server_worker).start()

    def start_tcp_client_worker(self):
        self.logging.debug("start_tcp_client_worker")
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = str(socket.gethostname())
        self.logging.debug("hostname: %s" % host)
        status = self.tcp_socket.connect_ex((host, self.tcp_port))
        if status != 0:
            while status != 0:
                status = self.tcp_socket.connect_ex((host, self.tcp_port))
                time.sleep(2)
        msg = "Hello"
        self.tcp_socket.send(msg.encode('ascii'))

    def start_tcp_client():
        self.logging.debug("start_tcp_client")
        # self.NetworkMgr.tcp_server_thread = threading.Thread(target=self.NetworkMgr.start_tcp_client_worker, args=self).start()
        self.logging.debug("start_tcp_client_worker")
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = str(socket.gethostname())
        self.logging.debug("hostname: %s" % host)
        status = self.tcp_socket.connect_ex((host, self.ConfigMgr.get_tcp_port()))
        if status != 0:
            while status != 0:
                status = self.tcp_socket.connect_ex((host, self.tcp_port))
                time.sleep(2)
        msg = "Hello"
        self.tcp_socket.send(msg.encode('ascii'))

    def close(self):
        for conn in self.get_connections():
            conn.close()

    def send_tcp_message(self, message):
        for connect in self.connections:
            connect.tcp_socket.send(message.encode())

#    def send_tcp_message_worker(self, message):

    def read_tcp_message(self):
        self.logging.debug("read_tcp_message")
        while True:
            conn, addr = self.tcp_socket.accept()
            print(f"Connection established with {addr}")
            self.connections.append(conn)
            read_thread = threading.Thread(target=self.read_data, args=(conn,))
            read_thread.start()
            data = self.tcp_socket.recv(1024)
            print('Received: %r' % data.decode())

        self.tcp_socket.close()

    def listen_tcp(self):

        self.logging.debug("listen_tcp")
        stop_event = self.mp.stop_event

        while not stop_event.is_set():
            message, address = self.mp.network.read_tcp_message()
            abc = 'Received {} bytes from {} : {}'.format(len(message), address, message)
            self.logging.debug(abc)
            time.sleep(0)
