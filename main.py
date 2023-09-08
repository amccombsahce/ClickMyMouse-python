# This is a sample Python script.

from main_gui import Main_GUI
import threading
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.



def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

def gui_thread():
    main_gui = Main_GUI()
    main_gui.ShowWindow()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #print_hi('PyCharm')

    my_main_gui_thread = threading.Thread(target=gui_thread()).start()



