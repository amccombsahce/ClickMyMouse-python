# This is a sample Python script.
from tkinter import *
import tkinter as tk
from main_gui import MainGUI
import threading


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

def gui_thread():
    root = tk.Tk()
    root.title("ClickMyMouse")
    root.grid_columnconfigure(0, weight=1)  # Allow column 0 to stretch
    root.grid_columnconfigure(1, weight=1)  # Allow column 1 to stretch
    root.grid_columnconfigure(2, weight=1)  # Allow column 0 to stretch
    root.grid_columnconfigure(3, weight=1)  # Allow column 1 to stretch
    root.grid_columnconfigure(4, weight=1)  # Allow column 1 to stretch
    root.grid_columnconfigure(5, weight=1)  # Allow column 1 to stretch
    root.grid_columnconfigure(6, weight=1)  # Allow column 1 to stretch
    root.grid_columnconfigure(7, weight=1)  # Allow column 1 to stretch
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_rowconfigure(3, weight=1)
    app = MainGUI(master=root)
    app.mainloop()


if __name__ == '__main__':
    # my_main_gui_thread = threading.Thread(target=gui_thread()).start()
    gui_thread()
