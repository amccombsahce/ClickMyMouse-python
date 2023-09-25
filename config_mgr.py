import xml.etree.ElementTree as ET
import os
import os.path
import configparser


class ConfigMgr:

    def __init__(self, filename='ClickMyMouse.config'):
        self.filename = filename
        self.__app_config = 'app.config'
        self.__is_server = False
        self.__udp_port = 5005
        self.__tcp_port = 5000
        self.__ip_address = "127.0.0.1"

        self.read()

    def read(self):
        config = configparser.ConfigParser()
        config.read(self.filename)
        if 'ClickMyMouse' in config:
            self.__is_server = config.getboolean('ClickMyMouse', 'is_server', fallback=False)
            self.__ip_address = config.get('ClickMyMouse', 'ip_address', fallback='')
            self.__udp_port = config.getint('ClickMyMouse', 'udp_port', fallback=5005)
            self.__tcp_port = config.getint('ClickMyMouse', 'tcp_port', fallback=5000)

    def save(self):
        config = configparser.ConfigParser()
        config['ClickMyMouse'] = {
            'is_server': str(self.__is_server),
            'ip_address': self.__ip_address,
            'udp_port': str(self.__udp_port),
            'tcp_port': str(self.__tcp_port)
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
