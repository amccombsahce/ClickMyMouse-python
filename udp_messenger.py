import socket
import threading


class UDPPortHandler:
    def __init__(self, tcp_port=0):
        self.host = '127.0.0.1'  # You can change this to your desired IP address
        self.port = 6050
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))

        self.response_thread = threading.Thread(target=self.receive_response)
        self.response_thread.daemon = True
        self.response_thread.start()
        self.tcp_port = tcp_port

    def send_request(self, message):
        self.sock.sendto(message.encode(), (self.host, self.port))

    def receive_response(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            response = data.decode()
            if response == "PORT_REQUEST":
                self.send_response(addr, self.tcp_port)

    def send_response(self, addr, tcp_port):
        response_message = f"PORT_RESPONSE: ({str(tcp_port)})"  # You can replace 12345 with your desired integer
        self.sock.sendto(response_message.encode(), addr)


if __name__ == "__main__":
    udp_handler = UDPPortHandler()
    udp_handler.send_request("PORT_REQUEST")

    # Do something else in your program
    # You can retrieve the response integer when needed from the PORT_RESPONSE message.
