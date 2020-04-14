import threading
import queue
import sys
import time

class logging_interface:
    def __init__(self):
        self.loq_queue = queue.Queue
        self.new_log_flat = threading.Event

        self.verbosity = 0
        self.log_file_name = ''

    def config_file(self):
        # Deal with config file based setup
        pass

    # Called by message broker
    def message_callback(self):
        # Note timestamp
        # Filter by verbosity level
        # If valid 
            # put in message queue
        pass

    def filter_incoming(self):
        # Is verbosity >= self.verbosity
            # yes - return true
            # No - return false
        pass

    def queue_message(self):
        # put message and timestamp tuple to queue
        # Set event
        pass

    def log_loop(self):
        # While running is true
            # Wait for event
            # Clear event
            # Try and retrieve message from queue
            # Has a message been retrieved
                # Yes - Save_to_file
                # No - Wait for flag
        pass

    def get_message(self):
        # get message from queue
        # If empty queue exception
            # return None
        # else
            # return message
        pass

    # Interface method
    def save_to_file(self):
        # Save message to file using abstracted save method
        pass


def saveToFile():
    global log_queue
    global new_log_item

    while True:
        new_log_item.wait()

        try:
            while True:
                new_data = log_queue.get_nowait()
                print(new_data, file=sys.stdout)

        except queue.Empty:
            new_log_item.clear()

if __name__ == "__main__":
    global log_queue
    global new_log_item

    new_log_item = threading.Event()
    log_queue = queue.Queue()

    log_thread = threading.Thread(target=saveToFile, daemon=True)
    log_thread.start()

    for i in range(10):
        log_queue.put(i)
        new_log_item.set()

        time.sleep(1)
