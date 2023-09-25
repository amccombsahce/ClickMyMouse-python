import logging
import socket
from threading import Thread, Event
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import signal

# my stuff
from config_mgr import ConfigMgr
from param_mgr import Param_Mgr
from network_mgr import *
from logger import Logger
from script_engine import ScriptEngine
from udp_messenger import UDPPortHandler

class Main_GUI(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.ScriptEngine_stop_event = None
        self.master = master
        # self.pack()
        self.grid(sticky="nsew")
        self.create_widgets()
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.pm = Param_Mgr()
        self.pm.main_gui = self

        # self.pm.ConfigMgr.save()
        # self.pm.stop_event = threading.Event()
        self.pm.Logger = Logger("ClickMyMouse.log", self)
        self.pm.Logger.debug("Main_GUI()")
        self.pm.ConfigMgr = ConfigMgr()

        self.pm.ScriptEngine = ScriptEngine(self.pm)
        self.pm.NetworkMgr = NetworkMgr(self.pm)



        if self.pm.ConfigMgr.get_isserver():

            self.pm.NetworkMgr_stop_event = threading.Event()
            self.sender_thread = threading.Thread(target=self.pm.NetworkMgr.run, args=(self.pm.NetworkMgr_stop_event,))
            self.sender_thread.daemon = True
            self.sender_thread.start()

            self.receive_thread = threading.Thread(target=self.pm.NetworkMgr.receive_messages, args=(self.pm.NetworkMgr_stop_event,))
            self.receive_thread.daemon = True
            self.receive_thread.start()

        # for debugging
        file_path = "/home/amccombs/Documents/Projects/ClickMyMouse-python/ClickMyMouse.script"
        self.scriptfilename_textbox.delete(0, tk.END)
        self.scriptfilename_textbox.insert(tk.END, file_path)
        self.pm.ScriptEngine.clearscript()
        # load new script
        self.pm.ScriptEngine.loadscript(file_path)

        #signal.signal(signal.SIGINT, self.on_exit)
        #signal.signal(signal.SIGTERM, self.on_exit)
        # self.mp.networkmgr = NetworkMgr(self.mp.configmgr.get_ip_address(), self.mp.configmgr.get_udp_port(), self.mp.configmgr.get_tcp_port())
        # self.mp.networkmgr.init_tcp_socket()


        self.udp_messenger = UDPPortHandler(tcp_port=self.pm.NetworkMgr.port)
        self.udp_messengerThread = threading.Thread(target=self.udp_messenger.receive_response)
        self.udp_messengerThread.daemon = True
        self.udp_messengerThread.start()


    def on_exit(self, a, b):
        print("Exiting...")
        print(f"NetworkMgr.on_exit, a: {str(a)}, b: {str(b)}")
        # Close sockets
        for client_socket in self.pm.NetworkMgr.connections:
            client_socket.close()

        self.pm.NetworkMgr.server_socket.close()

        # Wait for threads to finish
        self.receive_thread.join()

        sys.exit(0)
    def create_widgets(self):
        self.master.columnconfigure(0, weight=4)
        self.master.columnconfigure(1, weight=2)
        self.master.columnconfigure(2, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.open_file_button = tk.Button(self, text="Script to run", command=self.open_file)
        self.open_file_button.grid(row=0, column=0)

        self.scriptfilename_textbox = tk.Entry(self, width=100)
        self.scriptfilename_textbox.grid(row=0, column=1, columnspan=4, sticky="ew")

        self.run_button = tk.Button(self, text="Run", command=self.run_clicked)
        self.run_button.grid(row=0, column=5)

        self.pause_button = tk.Button(self, text="Pause", command=self.pause_clicked)
        self.pause_button.grid(row=0, column=6)

        self.exit_button = tk.Button(self, text="Exit", command=self.exit_clicked)
        self.exit_button.grid(row=0, column=7)

        self.log_label = tk.Label(self, text="Log")
        self.log_label.grid(row=1, column=0)

        # Create a scrollbar
        # scrollbar = tk.Scrollbar(self)
        # scrollbar.grid(row=2, column=5, sticky='ns')

        self.log_listbox = tk.Listbox(self, width=200, height=30)  # , yscrollcommand=scrollbar.set)
        self.log_listbox.grid(row=2, column=0, columnspan=5)  # , sticky="nsew")

        self.connections_label = tk.Label(self, text="Connections")
        self.connections_label.grid(row=1, column=5)

        self.connections_listbox = tk.Listbox(self)
        self.connections_listbox.grid(row=2, column=5, columnspan=2)

        self.clear_button = tk.Button(self, text="Clear Log", command=self.clear_log)
        self.clear_button.grid(row=3, column=0)

    def set_connections_label(self, newtext):
        self.connections_label.config(text=newtext)
    def open_file(self):
        file_path = filedialog.askopenfilename()
        print(f"Selected file: {file_path}")
        oldtext = self.scriptfilename_textbox.get()
        print(f"oldtext: {oldtext}")
        # remove the current script
        self.pm.ScriptEngine.clearscript()
        # load new script
        self.pm.ScriptEngine.loadscript(file_path)
        # update textbox to show new script filename
        self.scriptfilename_textbox.delete(0, tk.END)
        self.scriptfilename_textbox.insert(tk.END, file_path)

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
            is_sender_alive = self.sender_thread.is_alive()
            print(f"NetworkMgr.run is_alive: {str(is_sender_alive)}")
            is_receive_alive = self.receive_thread.is_alive()
            print(f"NetworkMgr.receive_thread is_alive: {str(is_receive_alive)}")


    def pause_clicked(self):
        if not self.pm.ScriptEngine.is_pause():
            self.pause_button.config(text="Resume")
            self.pm.ScriptEngine.set_pause(True)
        else:
            self.pause_button.config(text="Pause")
            self.pm.ScriptEngine.set_pause(False)

    def exit_clicked(self):
        self.ScriptEngine_stop_event.set()
        self.pm.NetworkMgr_stop_event.set()

        if self.pm.NetworkMgr.server_socket is not None:
            self.pm.NetworkMgr.server_socket.close()

        for abc_socket in self.pm.NetworkMgr.connections:
            try:
                self.pm.NetworkMgr.del_connections(abc_socket)
                abc_socket.shutdown(socket.SHUT_RDWR)
                abc_socket.close()

            except socket.error as e:
                print(f"main_gui.receive_messages: Socket error: {str(e)}")
                abc = 1

        sys.exit(0)

    def clear_log(self):
        self.log_listbox.delete(0, 'end')

    def add_log(self, entry):
        self.log_listbox.insert('end', entry)
        self.log_listbox.see("end")

    def add_connection(self, item):
        all_items = self.connections_listbox.get(0, tk.END)
        if item not in all_items:
            try:
                self.connections_listbox.insert(tk.END, item)
            except Exception as e:
                print(f"Exception {str(e)}")
                abc = 1



    def del_connection(self, item):

        all_items = self.connections_listbox.get(0, tk.END)

        for item in all_items:
            index = all_items.index(item)
            self.connections_listbox.delete(index)

        abc = 1

    def send_udp(self):
        self.pm.Logger.debug("send_udp clicked")

        self.pm.NetworkMgr.send_udp_message("hello")

    def send_tcp(self):
        self.pm.Logger.debug("send_tcp clicked")
        self.pm.NetworkMgr.start_tcp_client()
        msg = "HellowWorld"
        self.pm.NetworkMgr.send_tcp_message(self.pm, msg)

    def button3clicked(self):
        self.send_udp()

    def button4clicked(self):  # "Send tcp"
        # self.send_tcp()
        self.pm.NetworkMgr.send_message("Hellow")

    #        self.pm.NetworkMgr.client_thread = threading.Thread(target=self.pm.NetworkMgr.start_client).start()

    # self.pm.NetworkMgr.start_client()
    # self.pm.NetworkMgr.run()

    def button5clicked(self):  # "listen tcp"
        # self.pm.NetworkMgr.start_tcp_server()
        # self.pm.NetworkMgr.server_thread = threading.Thread(target=self.pm.NetworkMgr.start_server).start()
        # self.pm.NetworkMgr.server_thread = threading.Thread(target=self.pm.NetworkMgr.start_listener).start()
        self.connections_add("hello")
        poop = threading.Thread(target=self.pm.NetworkMgr.start_run)
        poop.daemon = True
        poop.start()

    #        self.pm.Sender_thread = threading.Thread(target=NetworkMgr.run(self), args=self)
    #        self.pm.Sender_thread.daemon = True
    #        self.pm.Sender_thread.start()

    def button6clicked(self):  # "connect to client"
        self.pm.NetworkMgr.connect_to_client(self.pm.ConfigMgr.get_ip_address(), self.pm.ConfigMgr.get_tcp_port())

    def pauseclicked(self):
        self.pm.Logger.debug("Pause clicked")

    #        m = messagebox.showinfo("pauseclicked", "paused")

    def test_log_add(self):
        text = "Hello World: " + str(datetime.now())
        self.log_add(text)

    def ShowWindow(self):
        # btn = tkinter.Button(self.window, text="Pause", bg="gray", fg="black", command=self.pauseclicked)
        # btn.grid(column=4, row=4)

        textbox1_lbl = tk.Label(self.window, text="Script to Run:")
        textbox1_lbl.place(x=self.xpadding, y=self.ypadding)
        # text box to allow user to specify a script to run
        textbox1 = tk.Text(self.window, width=30, height=1)
        textbox1.place(x=textbox1_lbl.winfo_reqwidth() + self.xpadding, y=self.ypadding)
        # button to run/top script
        button1 = tk.Button(self.window, text="Run", command=self.test_log_add)
        button1.place(x=textbox1_lbl.winfo_reqwidth() + textbox1.winfo_reqwidth() + self.xpadding, y=self.ypadding)

        button2 = tk.Button(self.window, text="PAuse", command=self.pauseclicked)
        button2.place(
            x=button1.winfo_reqwidth() + textbox1_lbl.winfo_reqwidth() + textbox1.winfo_reqwidth() + self.xpadding,
            y=self.ypadding)

        # server/client mode
        xx = textbox1_lbl.winfo_reqwidth() + textbox1.winfo_reqwidth() + button1.winfo_reqwidth() + (self.xpadding * 3)
        yy = button1.winfo_reqheight() + self.ypadding

        # show log to user
        listbox1_lbl = tk.Label(self.window, text="Log:")
        listbox1_lbl.place(x=self.xpadding, y=yy)
        self.listbox1 = tk.Listbox(self.window, width=100, height=10)
        yy = button1.winfo_reqheight() + self.ypadding
        self.listbox1.place(x=20, y=button1.winfo_reqheight() + listbox1_lbl.winfo_reqheight() + self.ypadding)
        # self.listbox1.pack(expand=True, x=20, y=button1.winfo_reqheight() + listbox1_lbl.winfo_reqheight() + self.ypadding)

        scrollbar = Scrollbar(self.listbox1, orient="vertical")
        scrollbar.config(command=self.listbox1.yview)

        scrollbar.place(x=self.listbox1.winfo_reqwidth() - 10, y=10, rely=0.45, width=15,
                        height=self.listbox1.winfo_reqheight(), anchor="center")
        self.listbox1.config(yscrollcommand=scrollbar.set)

        button2 = tk.Button(self.window, text="Clear Log", command=self.test_log_clear)
        button2.place(x=self.listbox1.winfo_reqwidth(),
                      y=textbox1.winfo_reqheight() + button1.winfo_reqheight() + self.listbox1.winfo_reqheight() + self.ypadding)

        # server/client mode
        mode_lbl = tk.Label(self.window, text="Server Mode")
        mode_lbl.place(x=xx, y=yy)

        # server/client connection list

        self.listbox2 = tk.Listbox(self.window, width=10, height=10)
        # listbox2.pack(side="left", fill="both", expand=False)
        self.listbox2.place(x=xx + self.listbox1.winfo_reqwidth(), y=yy + mode_lbl.winfo_reqheight())

        # Create the buttons
        # button_frame = tkinter.Frame(self.window)
        # button_frame.pack(side="right", fill="both", expand=True)

        # button2 = tkinter.Button(button_frame, text="Button 2")
        # button2.pack(fill="x")

        button3 = tk.Button(self.window, text="Send udp", command=self.button3clicked)
        button3.place(x=self.xpadding,
                      y=yy + button2.winfo_reqheight() + self.listbox2.winfo_reqheight() + mode_lbl.winfo_reqheight())

        button4 = tk.Button(self.window, text="Send tcp", command=self.button4clicked)
        button4.place(x=button3.winfo_reqwidth() + self.xpadding,
                      y=yy + button2.winfo_reqheight() + self.listbox2.winfo_reqheight() + mode_lbl.winfo_reqheight())

        button5 = tk.Button(self.window, text="listen tcp", command=self.button5clicked)
        button5.place(x=button4.winfo_reqwidth() + button3.winfo_reqwidth() + self.xpadding,
                      y=yy + button2.winfo_reqheight() + self.listbox2.winfo_reqheight() + mode_lbl.winfo_reqheight())

        button6 = tk.Button(self.window, text="connect to client", command=self.button6clicked)
        button6.place(x=self.xpadding,
                      y=yy + button4.winfo_reqheight() + button2.winfo_reqheight() + self.listbox2.winfo_reqheight() + mode_lbl.winfo_reqheight())

        self.window.mainloop()
