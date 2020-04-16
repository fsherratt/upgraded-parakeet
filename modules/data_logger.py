import threading
import queue
import sys
import time

import logging


class logging_interface:
    DEBUG = 3
    VERBOSE = 2
    NOTICE = 1
    WARNING = 0
    OFF = -1

    def __init__(self):
        self._loq_queue = queue.Queue()
        self._log_queue_event = threading.Event()

        self.verbosity = 0

        self._loop_running = True

    # Called by message broker
    def message_callback(self, data, verbosity=VERBOSE):
        timestamp = time.time()

        if self.filter_incoming(verbosity):
            self.queue_message(timestamp, data)
            self._log_queue_event.set()

    def filter_incoming(self, verbosity) -> bool:
        return verbosity <= self.verbosity

    def queue_message(self, time, data):
        self._loq_queue.put((time, data))

    def log_loop(self):
        while self._loop_running:
            self.wait_for_message()

            while True:
                msg = self.get_message()

                if msg is None:
                    break

                self.save_to_file(msg)

    def wait_for_message(self):
        self._log_queue_event.wait()
        self._log_queue_event.clear()

    def start_logging_loop(self):
        self._log_thread = threading.Thread(target=self.log_loop, daemon=True)
        self._log_thread.start()

    def stop_logging_loop(self):
        self._loop_running = False

    def get_message(self):
        try:
            return self._loq_queue.get_nowait()
        except queue.Empty:
            return None

    # Interface method
    def save_to_file(self, msg):
        # Save message to file using abstracted save method
        pass


def saveToFile():
    global log_queue
    global new_log_item

    while True:
        new_log_item.wait()
        new_log_item.clear()

        try:
            while True:
                new_data = log_queue.get_nowait()
                print(new_data, file=sys.stdout)

        except queue.Empty:
            pass

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
