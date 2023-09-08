from NetworkMgr import *
from ConfigMgr import ConfigMgr
from Logger import Logger


#when we need to pass more classes around, well just add it to the class
class ParamMgr:
    def __init__(self):
        self.stop_event = None
        self.is_server: bool = False
        self.NetworkMgr: NetworkMgr = None
        self.ConfigMgr: ConfigMgr = None
        self.logging: Logger = None

