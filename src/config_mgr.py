import xml.etree.ElementTree as ET
import os
import os.path
import configparser


class ConfigMgr:

    def __init__(self, filename='ClickMyMouse.config'):
        self.filename = filename
        self.__app_config = filename
        self.__ip_address = "ubuntu"
        self.__is_server = False
        self.__tcp_port = 5000
        self.__udp_port = 5005

        self.read()

    def read(self):
        config = configparser.ConfigParser()
        config.read(self.filename)
        if 'network' in config:
            self.__ip_address = config.get('network', 'ip_address', fallback=self.__ip_address)
            self.__is_server = config.getboolean('network', 'is_server', fallback=self.__is_server)
            self.__tcp_port = config.getint('network', 'tcp_port', fallback=self.__tcp_port)
            self.__udp_port = config.getint('network', 'udp_port', fallback=self.__udp_port)

    def save(self):
        config = configparser.ConfigParser()
        config['network'] = {
            'ip_address': self.__ip_address,
            'is_server': str(self.__is_server),
            'tcp_port': str(self.__tcp_port),
            'udp_port': str(self.__udp_port)
        }
        with open(self.filename, 'w') as f:
            config.write(f)

    def set_isserver(self, setting: bool):
        self.__is_server = setting

    def set_udp_port(self, setting: int):
        self.__udp_port = setting

    def set_tcp_port(self, setting: int):
        self.__tcp_port = setting

    def set_ip_address(self, setting: str):
        self.__ip_address = setting

    def get_isserver(self):
        return self.__is_server
    def get_udp_port(self):
        return self.__udp_port

    def get_tcp_port(self):
        return self.__tcp_port
    def get_ip_address(self):
        return self.__ip_address

    def del_isserver(self):
        del self.__is_server

    def del_udp_port(self):
        del self.__udp_port

    def del_tcp_port(self):
        del self.__tcp_port

    def del_ip_address(self):
        del self.__ip_address
