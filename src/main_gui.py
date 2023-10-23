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

        self.master = master
        # self.pack()
        self.grid(sticky="nsew")

        # self.columnconfigure(0, weight=2)
        # self.columnconfigure(1, weight=1)
        # self.rowconfigure(0, weight=1)
        # self.rowconfigure(1, weight=1)
        # self.master.columnconfigure(0, weight=4)
        # self.master.columnconfigure(1, weight=2)
        # self.master.columnconfigure(2, weight=1)
        # self.master.rowconfigure(0, weight=1)
        # self.master.rowconfigure(1, weight=1)

        # if we are server, we want to let user select a test script, click the button will
        # have file open dialog to select script
        self.open_file_button = tk.Button(self, text="Script to run", command=self.open_file)
        self.open_file_button.grid(row=0, column=0)

        # if we are client, we want to let user connect to server
        self.connect_to_server_button = tk.Button(self, text="Connect to Server", command=self.connect_to_server)
        self.connect_to_server_button.grid(row=0, column=0)

        # if we are server, we want to show the user the script filename they selected
        self.script_filename_textbox = tk.Entry(self, width=100)
        self.script_filename_textbox.grid(row=0, column=1, columnspan=4, sticky="ew")

        # we are the client, and letting user enter the server ip address
        self.connect_to_server_address = tk.Entry(self, width=20)
        self.connect_to_server_address.grid(row=0, column=1, sticky="ew")

        # we are the client, and letting user enter the server ip port
        self.connect_to_server_ip = tk.Entry(self, width=10)
        self.connect_to_server_ip.grid(row=0, column=2, sticky="ew")

        # if we are server, we want to let user start running the script
        self.run_button = tk.Button(self, text="Run", command=self.run_clicked)
        self.run_button.grid(row=0, column=5)

        # if we are the client, we want to send INIT to server to help debugging
        self.init_button = tk.Button(self, text="Send.INIT", command=self.send_init_clicked)
        self.init_button.grid(row=0, column=5)

        # if we are server, we want to let user pause running the script
        self.pause_button = tk.Button(self, text="Pause", command=self.pause_clicked)
        self.pause_button.grid(row=0, column=6)

        # let the user exit the software
        self.exit_button = tk.Button(self, text="Exit", command=exit_clicked)
        self.exit_button.grid(row=0, column=7)

        # show user current pass/fail stats
        # self.log_total_testcases = tk.Label(self, text="Total", justify=tk.RIGHT)
        # self.log_total_testcases.grid(row=1, column=1)
        #
        # self.log_total_testcases = tk.Label(self, text="Pass", justify=tk.RIGHT)
        # self.log_total_testcases.grid(row=1, column=2)
        #
        # self.log_total_testcases = tk.Label(self, text="Fail", justify=tk.RIGHT)
        # self.log_total_testcases.grid(row=1, column=3)

        # allow the user to clear the display
        self.clear_button = tk.Button(self, text="Clear Log", command=self.clear_log)
        self.clear_button.grid(row=1, column=5)

        # show the user log
        self.log_label = tk.Label(self, text="Log")
        self.log_label.grid(row=2, column=0)

        # show the user log
        # self.log_listbox = tk.Listbox(self, width=150, height=30)
        self.log_listbox = tk.Text(self, width=150, height=30, wrap=tk.WORD)  # change to text for word-wrap
        self.log_listbox.grid(row=3, column=0, columnspan=5)  # , sticky="nsew")
        self.log_listbox.tag_config("red", foreground="red")  # let's change the text to red on warnings and errors

        # show user current connection list
        self.connections_label = tk.Label(self, width=25, text="Connections")
        self.connections_label.grid(row=2, column=6)

        self.connections_listbox = tk.Listbox(self, width=25)
        self.connections_listbox.grid(row=3, column=6, columnspan=2)

        # create ParamMgr to allow everyone to talk with each other
        self.pm = ParameterMgr()
        self.pm.main_gui = self

        # self.pm.ConfigMgr.save()
        self.pm.Logger = Logger("ClickMyMouse.log", self)
        # self.pm.Logger.debug("Main_GUI()")
        self.pm.ConfigMgr = ConfigMgr()

        self.pm.ScriptEngine = ScriptEngine(self.pm)

        # self.pm.NetworkMgr = NetworkMgr(self.pm)
        # self.pm.NetworkMgr = NetworkMgr(self.pm)
        self.NetworkMgr_thread = threading.Thread(target=NetworkMgr, name='NetworkMgr', args=(self.pm,))
        self.NetworkMgr_thread.daemon = True
        self.NetworkMgr_thread.start()

        # if self.pm.ConfigMgr.get_isserver():

        # self.incoming_thread = threading.Thread(target=self.pm.NetworkMgr.run_incoming_message_queue)
        # self.incoming_thread.daemon = True
        # self.incoming_thread.start()
        #
        # self.outgoing_thread = threading.Thread(target=self.pm.NetworkMgr.run_outgoing_message_queue)
        # self.outgoing_thread.daemon = True
        # self.outgoing_thread.start()
        # #
        # self.receive_thread = threading.Thread(target=self.pm.NetworkMgr.receive_messages)
        # self.receive_thread.daemon = True
        # self.receive_thread.start()
        #
        # self.listener_thread = threading.Thread(target=self.pm.NetworkMgr.start_listener)
        # self.listener_thread.daemon = True
        # self.listener_thread.start()

        # default script to run, good for unattended clients
        file_path = "../ClickMyMouse.script"
        self.script_filename_textbox.delete(0, tk.END)
        self.script_filename_textbox.insert(0, file_path)  # (tk.END, file_path)
        self.pm.ScriptEngine.clear_script()
        # load new script
        self.pm.ScriptEngine.load_script(file_path)

        # change the buttons if we are server or client
        if self.pm.ConfigMgr.get_isserver():
            # we are server
            self.connect_to_server_button.grid_remove()
            self.init_button.grid_remove()
            self.connect_to_server_address.grid_remove()
            self.connect_to_server_ip.grid_remove()
        else:
            # we are client
            self.open_file_button.grid_remove()
            self.script_filename_textbox.grid_remove()
            self.run_button.grid_remove()
            self.pause_button.grid_remove()

        self.udp_messenger = None
        self.udp_messengerThread = None
        threading.Thread(target=self.init).start()

    def init(self):

        if self.pm.ConfigMgr.get_isserver():
            while self.pm.NetworkMgr.port == 0:
                print("main_gui.init, sleep")
                time.sleep(1)

        time.sleep(1)
        server_tcp_port = self.pm.NetworkMgr.my_port
        now = datetime.now()
        formatted_now = now.strftime("%M")
        udp_port = 6050  #  + int(formatted_now)

        server_add = self.pm.ConfigMgr.get_ip_address()
        self.connect_to_server_address.delete(0, tk.END)
        self.connect_to_server_address.insert(0, server_add)
        # self.udp_messenger = UDPPortHandler(udp_port=udp_port, server_tcp_port=server_tcp_port)
        # self.udp_messengerThread = threading.Thread(target=self.udp_messenger.receive_message)
        # self.udp_messengerThread.daemon = True
        # self.udp_messengerThread.start()

    def set_connections_label(self, new_text):
        self.connections_label.config(text=new_text)

    def open_file(self):
        file_path = filedialog.askopenfilename()
        print(f"Selected file: {file_path}")
        oldtext = self.script_filename_textbox.get()
        print(f"oldtext: {oldtext}")
        # remove the current script
        self.pm.ScriptEngine.clear_script()
        # load new script
        self.pm.ScriptEngine.load_script(file_path)
        # update textbox to show new script filename
        self.script_filename_textbox.delete(0, tk.END)
        self.script_filename_textbox.insert(tk.END, file_path)

    def run_clicked(self, text_wanted=""):
        oldtext = self.run_button.cget('text')
        if "Run" in oldtext and "Stop" not in text_wanted:
            self.run_button.config(text="Stop")
            self.pm.ScriptEngine.set_run(True)
            self.pm.ScriptEngine.set_pause(False)
            self.pm.stop_event.clear()  # = threading.Event()
            self.script_thread = threading.Thread(target=self.pm.ScriptEngine.run)
            # self.script_thread.daemon = True
            self.script_thread.start()
        elif "Stop" in oldtext:
            self.run_button.config(text="Run")
            self.pm.ScriptEngine.set_run(False)
            self.pm.ScriptEngine.set_pause(True)
            self.pm.stop_event.set()
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

    def send_init_clicked(self):
        self.pm.NetworkMgr.send_message(MessageType.INIT)


    def clear_log(self):
        # self.log_listbox.delete(0, 'end')  # listbox
        self.log_listbox.delete("1.0", 'end')  # text

    def add_log(self, entry):
        entry = entry + '\n'
        if 'error' in entry.lower():
            self.log_listbox.insert('end', entry, "red")
        elif 'warning' in entry.lower():
            self.log_listbox.insert('end', entry, "red")
        else:
            self.log_listbox.insert('end', entry)
        self.log_listbox.see("end")

    def add_connection(self, connection, connection_status):
        all_items = self.connections_listbox.get(0, tk.END)
        # first delete the existing entry, maybe it has a different status
        for item in all_items:
            index = all_items.index(item)
            self.connections_listbox.delete(index)

        abc = f"{connection} {connection_status}"
        self.pm.Logger.debug(f"main_gui.add_connection: {str(connection)}, status: {str(connection_status)}")
        try:
            self.connections_listbox.insert(tk.END, abc)
        except Exception as e:
            print(f"Exception {str(e)}")

    def del_connection(self, connection):
        all_items = self.connections_listbox.get(0, tk.END)

        for item in all_items:
            self.pm.Logger.debug(f"main_gui.del_connection: {str(connection)}")
            index = all_items.index(item)
            self.connections_listbox.delete(index)

    def connect_to_server(self):

        server_addr = self.pm.ConfigMgr.get_ip_address()
        server_port = self.pm.ConfigMgr.get_tcp_port()

        user_address = self.connect_to_server_address.get()
        user_ip = int(self.connect_to_server_ip.get())

        if user_address is not None and len(user_address) > 1:
            server_addr = user_address
            server_port = user_ip

        if len(server_addr) < 4:
            self.udp_messenger.send_message("PORT_REQUEST")

            while self.udp_messenger.server_tcp_port == 0:
                time.sleep(0.1)

            if self.udp_messenger.server_tcp_port > 0:
                self.pm.NetworkMgr.connect_to_server(self.udp_messenger.server_tcp_addr, self.udp_messenger.server_tcp_port)
        else:
            socket_connection_result = self.pm.NetworkMgr.connect_to_server(server_addr, server_port)

            if socket_connection_result is not None:
                self.pm.NetworkMgr.send_message(MessageType.INIT)






