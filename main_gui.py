import time
import tkinter as tk
import sys
from tkinter import filedialog
# my stuff
from config_mgr import ConfigMgr
from network_mgr import *
from logger import Logger
from script_engine import ScriptEngine
from udp_messenger import UDPPortHandler
from param_mgr import ParameterMgr


def exit_clicked():
    sys.exit(0)


class MainGUI(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.ScriptEngine_stop_event = None
        self.master = master
        # self.pack()
        self.grid(sticky="nsew")

        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=4)
        self.master.columnconfigure(1, weight=2)
        self.master.columnconfigure(2, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.open_file_button = tk.Button(self, text="Script to run", command=self.open_file)
        self.open_file_button.grid(row=0, column=0)

        self.connect_to_server_button = tk.Button(self, text="Connect to Server", command=self.connect_to_server)
        self.connect_to_server_button.grid(row=0, column=0)

        self.script_filename_textbox = tk.Entry(self, width=100)
        self.script_filename_textbox.grid(row=0, column=1, columnspan=4, sticky="ew")

        self.run_button = tk.Button(self, text="Run", command=self.run_clicked)
        self.run_button.grid(row=0, column=5)

        self.pause_button = tk.Button(self, text="Pause", command=self.pause_clicked)
        self.pause_button.grid(row=0, column=6)

        self.exit_button = tk.Button(self, text="Exit", command=exit_clicked)
        self.exit_button.grid(row=0, column=7)

        self.log_label = tk.Label(self, text="Log")
        self.log_label.grid(row=1, column=0)

        self.log_listbox = tk.Listbox(self, width=100, height=30)  # , yscrollcommand=scrollbar.set)
        self.log_listbox.grid(row=2, column=0, columnspan=5)  # , sticky="nsew")

        self.connections_label = tk.Label(self, text="Connections")
        self.connections_label.grid(row=1, column=5)

        self.connections_listbox = tk.Listbox(self)
        self.connections_listbox.grid(row=2, column=5, columnspan=2)

        self.clear_button = tk.Button(self, text="Clear Log", command=self.clear_log)
        self.clear_button.grid(row=3, column=0)

        self.pm = ParameterMgr()
        self.pm.main_gui = self

        # self.pm.ConfigMgr.save()
        # self.pm.stop_event = threading.Event()
        self.pm.Logger = Logger("ClickMyMouse.log", self)
        # self.pm.Logger.debug("Main_GUI()")
        self.pm.ConfigMgr = ConfigMgr()

        self.pm.ScriptEngine = ScriptEngine(self.pm)
        self.pm.NetworkMgr = NetworkMgr(self.pm)

        # if self.pm.ConfigMgr.get_isserver():
        #
        #     self.pm.NetworkMgr_stop_event = threading.Event()
        #     self.sender_thread = threading.Thread(target=self.pm.NetworkMgr.run, args=(self.pm.NetworkMgr_stop_event,))
        #     self.sender_thread.daemon = True
        #     self.sender_thread.start()
        #
        #     self.receive_thread = threading.Thread(target=self.pm.NetworkMgr.receive_messages, args=(self.pm.NetworkMgr_stop_event,))
        #     self.receive_thread.daemon = True
        #     self.receive_thread.start()

        # for debugging
        file_path = "ClickMyMouse.script"
        self.script_filename_textbox.delete(0, tk.END)
        self.script_filename_textbox.insert(0, file_path)  # (tk.END, file_path)
        self.pm.ScriptEngine.clearscript()
        # load new script
        self.pm.ScriptEngine.load_script(file_path)

        if self.pm.ConfigMgr.get_isserver():
            self.connect_to_server_button.grid_remove()
        else:
            self.open_file_button.grid_remove()

        self.udp_messenger = None
        self.udp_messengerThread = None
        threading.Thread(target=self.init).start()

    def init(self):
        if self.pm.ConfigMgr.get_isserver():
            while self.pm.NetworkMgr.port == 0:
                print("main_gui.init, sleep")
                time.sleep(1)

        time.sleep(1)
        server_tcp_port = self.pm.NetworkMgr.port
        now = datetime.now()
        formatted_now = now.strftime("%M")
        udp_port = 6050 + int(formatted_now)

        self.udp_messenger = UDPPortHandler(udp_port=udp_port, server_tcp_port=server_tcp_port)
        self.udp_messengerThread = threading.Thread(target=self.udp_messenger.receive_message)
        self.udp_messengerThread.daemon = True
        self.udp_messengerThread.start()

    def set_connections_label(self, new_text):
        self.connections_label.config(text=new_text)

    def open_file(self):
        file_path = filedialog.askopenfilename()
        print(f"Selected file: {file_path}")
        oldtext = self.script_filename_textbox.get()
        print(f"oldtext: {oldtext}")
        # remove the current script
        self.pm.ScriptEngine.clearscript()
        # load new script
        self.pm.ScriptEngine.load_script(file_path)
        # update textbox to show new script filename
        self.script_filename_textbox.delete(0, tk.END)
        self.script_filename_textbox.insert(tk.END, file_path)

    def run_clicked(self):
        oldtext = self.run_button.cget('text')
        if "Run" in oldtext:
            self.run_button.config(text="Stop")
            self.pm.ScriptEngine.set_run(True)
            self.pm.ScriptEngine.set_pause(False)
            self.ScriptEngine_stop_event = threading.Event()
            self.pm.ScriptEngine.set_stop_event(self.ScriptEngine_stop_event)
            self.script_thread = threading.Thread(target=self.pm.ScriptEngine.run)
            # self.script_thread.daemon = True
            self.script_thread.start()
        elif "Stop" in oldtext:
            self.run_button.config(text="Run")
            self.pm.ScriptEngine.set_run(False)
            self.pm.ScriptEngine.set_pause(True)
            self.ScriptEngine_stop_event.set()
            is_script_alive = self.script_thread.is_alive()
            print(f"ScriptEngine thread is_alive: {str(is_script_alive)}")
            # is_sender_alive = self.sender_thread.is_alive()
            # print(f"NetworkMgr.run is_alive: {str(is_sender_alive)}")
            # is_receive_alive = self.receive_thread.is_alive()
            # print(f"NetworkMgr.receive_thread is_alive: {str(is_receive_alive)}")

    def pause_clicked(self):
        if not self.pm.ScriptEngine.is_pause():
            self.pause_button.config(text="Resume")
            self.pm.ScriptEngine.set_pause(True)
        else:
            self.pause_button.config(text="Pause")
            self.pm.ScriptEngine.set_pause(False)

    def clear_log(self):
        self.log_listbox.delete(0, 'end')

    def add_log(self, entry):
        self.log_listbox.insert('end', entry)
        self.log_listbox.see("end")

    def add_connection(self, connection, connection_status):
        all_items = self.connections_listbox.get(0, tk.END)
        # first delete the existing entry, maybe it has a different status
        # for item in all_items:
        #     index = all_items.index(item)
        #     self.connections_listbox.delete(index)

        if connection not in all_items:
            abc = f"{connection} {connection_status}"
            try:
                self.connections_listbox.insert(tk.END, abc)
            except Exception as e:
                print(f"Exception {str(e)}")
                abc = 1

    def del_connection(self, item):

        all_items = self.connections_listbox.get(0, tk.END)

        for item in all_items:
            index = all_items.index(item)
            self.connections_listbox.delete(index)

        abc = 1

    def connect_to_server(self):
        self.udp_messenger.send_message("PORT_REQUEST")

        while self.udp_messenger.server_tcp_port == 0:
            time.sleep(0)

        if self.udp_messenger.server_tcp_port > 0:
            self.pm.NetworkMgr.connect_to_server(self.udp_messenger.server_tcp_addr, self.udp_messenger.server_tcp_port)

            self.pm.NetworkMgr.send_message(MessageType.INIT_REQUEST)






