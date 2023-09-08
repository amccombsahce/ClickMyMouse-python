import logging
from threading import Thread, Event
import threading
import time
from datetime import datetime
import tkinter
from tkinter import *
from tkinter import messagebox

# my stuff
from ParamMgr import *
from NetworkMgr import *
from ConfigMgr import ConfigMgr
from Logger import Logger

class Main_GUI:

    def __init__(self):
        self.logging = Logger("ClickMyMouse.log")
        self.logging.debug("Main_GUI()")

        self.listbox1 = None  # Log list
        self.listbox2 = None  # Connection list
        self.name = __name__
        self.window = tkinter.Tk()
        self.window.title("ClickMyMouse")
        self.window.geometry('500x400')
        self.ypadding = 4
        self.xpadding = 2

        self.pm = ParamMgr
        self.pm.config = ConfigMgr()
        self.pm.stop_event = threading.Event()
        self.pm.logging = self.logging
        self.pm.network = NetworkMgr(self.pm)
        self.pm.logging = self.logging

        #self.mp.networkmgr = NetworkMgr(self.mp.configmgr.get_ip_address(), self.mp.configmgr.get_udp_port(), self.mp.configmgr.get_tcp_port())
        #self.mp.networkmgr.init_tcp_socket()




    def send_udp(self):
        logging.debug("send_udp clicked")

        self.pm.NetworkMgr.send_udp_message("hello")

    def send_tcp(self):
        logging.debug("send_tcp clicked")
        self.pm.NetworkMgr.start_tcp_client()
        msg = "HellowWorld"
        self.pm.NetworkMgr.send_tcp_message(self.pm, msg)

    def button3clicked(self):
        self.send_udp()

    def button4clicked(self):
        self.send_tcp()

    def button5clicked(self): # "listen tcp"
        self.mp.NetworkMgr.start_tcp_server(self.mp)
    def pauseclicked(self):
        logging.debug("Pause clicked")
        m = messagebox.showinfo("pauseclicked", "paused")

    def runclicked(self):
        logging.debug("Run clicked")
        m = messagebox.showinfo("runclicked", "Run")

    def log_add(self, text):
        self.listbox1.insert(tkinter.END, text)
        self.listbox1.yview(tkinter.END)

    def test_log_add(self):
        text = "Hello World: " + str(datetime.now())
        self.log_add(text)

    def test_log_clear(self):
        self.listbox1.delete(0, tkinter.END)

    def ShowWindow(self):
        # btn = tkinter.Button(self.window, text="Pause", bg="gray", fg="black", command=self.pauseclicked)
        # btn.grid(column=4, row=4)

        textbox1_lbl = tkinter.Label(self.window, text="Script to Run:")
        textbox1_lbl.place(x=self.xpadding, y=self.ypadding)
        # text box to allow user to specify a script to run
        textbox1 = tkinter.Text(self.window, width=30, height=1)
        textbox1.place(x=textbox1_lbl.winfo_reqwidth() + self.xpadding, y=self.ypadding)
        # button to run/top script
        button1 = tkinter.Button(self.window, text="Run", command=self.test_log_add)
        button1.place(x=textbox1_lbl.winfo_reqwidth() + textbox1.winfo_reqwidth() + self.xpadding, y=self.ypadding)

        button2 = tkinter.Button(self.window, text="PAuse", command=self.pauseclicked)
        button2.place(x=button1.winfo_reqwidth() + textbox1_lbl.winfo_reqwidth() + textbox1.winfo_reqwidth() + self.xpadding, y=self.ypadding)

        # server/client mode
        xx = textbox1_lbl.winfo_reqwidth() + textbox1.winfo_reqwidth() + button1.winfo_reqwidth() + (self.xpadding * 3)
        yy = button1.winfo_reqheight() + self.ypadding

        # show log to user
        listbox1_lbl = tkinter.Label(self.window, text="Log:")
        listbox1_lbl.place(x=self.xpadding, y=yy)
        self.listbox1 = tkinter.Listbox(self.window, width=40, height=10)
        yy = button1.winfo_reqheight() + self.ypadding
        self.listbox1.place(x=20, y=button1.winfo_reqheight() + listbox1_lbl.winfo_reqheight() + self.ypadding)
        # self.listbox1.pack(expand=True, x=20, y=button1.winfo_reqheight() + listbox1_lbl.winfo_reqheight() + self.ypadding)

        scrollbar = Scrollbar(self.listbox1, orient="vertical")
        scrollbar.config(command=self.listbox1.yview)

        scrollbar.place(x=self.listbox1.winfo_reqwidth() - 10, y=10, rely=0.45, width=15,
                        height=self.listbox1.winfo_reqheight(), anchor="center")
        self.listbox1.config(yscrollcommand=scrollbar.set)

        button2 = tkinter.Button(self.window, text="Clear Log", command=self.test_log_clear)
        button2.place(x=self.listbox1.winfo_reqwidth(),
                      y=textbox1.winfo_reqheight() + button1.winfo_reqheight() + self.listbox1.winfo_reqheight() + self.ypadding)

        # server/client mode
        mode_lbl = tkinter.Label(self.window, text="Server Mode")
        mode_lbl.place(x=xx, y=yy)

        # server/client connection list

        self.listbox2 = tkinter.Listbox(self.window, width=10, height=10)
        # listbox2.pack(side="left", fill="both", expand=False)
        self.listbox2.place(x=xx, y=yy + mode_lbl.winfo_reqheight())

        # Create the buttons
        # button_frame = tkinter.Frame(self.window)
        # button_frame.pack(side="right", fill="both", expand=True)

        # button2 = tkinter.Button(button_frame, text="Button 2")
        # button2.pack(fill="x")

        button3 = tkinter.Button(self.window, text="Send udp", command=self.button3clicked)
        button3.place(x=self.xpadding, y=yy + button2.winfo_reqheight() + self.listbox2.winfo_reqheight() + mode_lbl.winfo_reqheight())

        button4 = tkinter.Button(self.window, text="Send tcp", command=self.button4clicked)
        button4.place(x=button3.winfo_reqwidth() + self.xpadding, y=yy + button2.winfo_reqheight() + self.listbox2.winfo_reqheight() + mode_lbl.winfo_reqheight())

        button5 = tkinter.Button(self.window, text="listen tcp", command=self.button5clicked)
        button5.place(x=button4.winfo_reqwidth() + button3.winfo_reqwidth() + self.xpadding, y=yy + button2.winfo_reqheight() + self.listbox2.winfo_reqheight() + mode_lbl.winfo_reqheight())

        self.window.mainloop()
