import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

class wait_for_me:
    def __init__(self, filename, text_to_wait, timeout_seconds=60):
        self.filename = filename
        self.text_to_wait = text_to_wait
        self.timeout_seconds = timeout_seconds

        cwd = os.getcwd()
        print(f"current directory: {str(cwd)}")

    def run(self):

        start_time = time.time()
        file_modified_event = threading.Event()

        cwd = os.getcwd()
        full_path = os.path.join(cwd, self.filename)

        abs_path_001 = os.path.abspath(self.filename)
        abs_path_002 = os.path.abspath(full_path)

        folder_path = os.path.dirname(full_path)

        print(f"current directory: {str(cwd)}")

        exist = os.path.exists(full_path)
        if not exist:
            print(f"Error, wait_for_me.run, file not found: {str(self.filename)}, full path: {str(full_path)}")

        def on_modified(event):
            if not event.is_directory and event.src_path == self.filename:
                file_modified_event.set()

        event_handler = FileSystemEventHandler()
        event_handler.on_modified = on_modified

        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(folder_path), recursive=False)
        observer.start()

        try:
            while not file_modified_event.wait(1):
                if time.time() - start_time > self.timeout_seconds:
                    return None

            with open(self.filename, 'r') as file:
                content = file.read()
                if self.text_to_wait in content:
                    return True

        except OSError as e:
            print(f"OSError, {str(e)}")
        except FileNotFoundError as e:
            print(f"Error, File not found {str(self.filename)}, {str(e)}")
        finally:
            observer.stop()
            observer.join()

# Example usage:
if __name__ == "__main__":
    watcher = wait_for_me("example.txt", "target_text", 60)  # Wait for 60 seconds
    result = watcher.run()
    if result is True:
        print("Text found in the file.")
    elif result is None:
        print("File not updated or text not found within the specified timeout.")
