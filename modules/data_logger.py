import threading
import sys
import time

import logging

from .async_message import AsyncMessageCallback

class LoggingInterface(AsyncMessageCallback):
    def __init__(self):
        super().__init__()

        self._loop_running = True
        self._log_thread = None

    def __enter__(self):
        self.start_logging_loop()

    def __exit__(self, exception_type, exception_value, traceback):
        if traceback:
            print(traceback.tb_frame)

        self.stop_logging_loop()

    def message_callback(self, channel, method, properties, data):
        if self._loop_running:
            self.queue_message(data)

    def log_loop(self):
        while self._loop_running:
            msg = self.wait_for_message()

            if msg is None:
                continue

            self.save_to_file(msg)

    def start_logging_loop(self):
        self._log_thread = threading.Thread(target=self.log_loop)
        self._log_thread.start()

    def stop_logging_loop(self):
        self._loop_running = False
        self._set_message_event()

    def save_to_file(self, msg):
        # Save message to file using abstracted save method
        print(msg, file=sys.stdout)

class FileLogger(LoggingInterface):
    def __init__(self, log_name, print_to_console=True):
        super().__init__()

        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.DEBUG) # log everything

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        log_directory = 'logs/'
        log_filename = log_directory+ log_name + '_' + time.strftime("%Y%m%d-%H%M%S") + '.log'

        file_handle = logging.FileHandler(log_filename)
        file_handle.setLevel(logging.DEBUG)
        file_handle.setFormatter(formatter)
        self.logger.addHandler(file_handle)

        if print_to_console:
            console_handle = logging.StreamHandler()
            console_handle.setLevel(logging.DEBUG)
            console_handle.setFormatter(formatter)
            self.logger.addHandler(console_handle)

    def save_to_file(self, msg):
        self.logger.debug(msg[1])

if __name__ == "__main__":
    file_log = FileLogger('telemetry')

    with file_log:
        for i in range(10):
            file_log.message_callback(None, None, None, i)
            time.sleep(1)
