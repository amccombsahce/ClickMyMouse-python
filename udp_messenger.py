import re
import socket
import threading
import time


class UDPPortHandler:
    def __init__(self, udp_port=6050, server_tcp_port=0):
        self.udp_port = udp_port
        # self.tcp_port = tcp_port  # if I am server, this is my port
        self.server_tcp_port = server_tcp_port  # if I am client, I need to find the server port
        self.server_tcp_addr = None

        self.receive_thread = threading.Thread(target=self.receive_message)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        # udp send
        # self.host = '192.168.1.255'  # 127.0.0.1'  # host
        self.host = '255.255.255.255'  # 127.0.0.1'  # host

        self.sockSender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sockSender.bind(('192.168.1.255', self.port))
        self.sockSender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.sockReceiver = None
        self.my_address = None

        print(f"udp_port: {str(self.udp_port)}, server_tcp_port: {str(server_tcp_port)}")

        # if tcp_port > 0 or True:
        #     # udp receive, bind to port when server
        #     self.sockReceiver.bind(('0.0.0.0', self.udp_port))

    def send_message(self, message):
        sock_info = self.sockSender.getsockname()
        self.my_address = str(sock_info)
        sent_bytes = self.sockSender.sendto(message.encode(), (self.host, self.udp_port))
        print(f"udp sent {str(message)}, {str(sent_bytes)} bytes, {str(self.sockSender.getsockname())}\n")

    def receive_message(self):
        self.sockReceiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.sockReceiver is None:
            print(f"Error with socket()")

        is_connected = False
        while not is_connected:
            try:
                self.sockReceiver.bind(('0.0.0.0', self.udp_port))
                is_connected = True
                print(f"Successful Bind to udp port: {str(self.udp_port)}")
            except Exception as e:
                print(f"Exception Error, bind: {str(e)}")
                time.sleep(1)

        while True:
            try:
                data, addr = self.sockReceiver.recvfrom(1024)
                response = data.decode()
                print(f"receive_message from: {str(addr)}, message: {str(response)}\n")

                if "PORT_REQUEST" in response:
                    if self.server_tcp_port != 0:
                        print(f"port response is: {str(self.server_tcp_port)}")
                        response_message = f"PORT_RESPONSE: ({str(self.server_tcp_port)})"
                        self.send_message(response_message)
                    else:
                        print(f"port is zero, not replying")
                elif "PORT_RESPONSE" in response:
                    # port response is the tcp port number that the server is listening on
                    abc001 = re.search(r'\((\d+)\)', response)
                    if abc001:
                        self.server_tcp_port = int(abc001.group(1))
                        self.server_tcp_addr = addr[0]

            except Exception as e:
                print(f"Exception Error: udp_messenger.receive_message {str(e)}")

# if __name__ == "__main__":
#    udp_handler = UDPPortHandler()
#    udp_handler.receive_message("PORT_REQUEST")
