# This is a sample Python script.
from tkinter import *
import tkinter as tk
from main_gui import Main_GUI
import threading
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.



def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

def gui_thread():
#    main_gui = Main_GUI()
#    main_gui.ShowWindow()
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
    app = Main_GUI(master=root)
    app.mainloop()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #print_hi('PyCharm')

    my_main_gui_thread = threading.Thread(target=gui_thread()).start()



