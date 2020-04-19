import threading
import queue
import sys
import time
import traceback

import logging

class logging_interface:
    def __init__(self):
        self._loq_queue = queue.Queue()
        self._log_queue_event = threading.Event()

        self._loop_running = True

    def __enter__(self):
        self.start_logging_loop()

    def __exit__(self, exception_type, exception_value, traceback):
        if traceback:
            print(traceback.tb_frame)

        self.stop_logging_loop()

    # Called by message broker
    def message_callback(self, data):
        timestamp = time.time()

        if self._loop_running:
            self._queue_message(timestamp, data)
            self._set_message_event()

    def _queue_message(self, timestamp, data):
        self._loq_queue.put((timestamp, data))

    def log_loop(self):
        while self._loop_running:
            self._wait_for_message_event()

            msg = self._get_message()

            if msg is None:
                continue

            self.save_to_file(msg)
    
    def _clear_message_event(self):
        self._log_queue_event.clear()

    def _set_message_event(self):
        self._log_queue_event.set()

    def _wait_for_message_event(self):
        self._log_queue_event.wait()

    def start_logging_loop(self):
        self._log_thread = threading.Thread(target=self.log_loop)
        self._log_thread.start()

    def stop_logging_loop(self):
        self._loop_running = False
        self._set_message_event()

    def _get_message(self):
        try:
            return self._loq_queue.get_nowait()
        except queue.Empty:
            self._clear_message_event()

        return None

    # Interface method
    def save_to_file(self, msg):
        # Save message to file using abstracted save method
        print(msg, file=sys.stdout)

class telemetry_log(logging_interface):
    def __init__(self, log_name, print_to_console=True):
        super().__init__()

        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.DEBUG) # log everything

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        log_directory = 'logs/'
        log_filename = log_directory+ log_name + '_' + time.strftime("%Y%m%d-%H%M%S") + '.log'

        fh = logging.FileHandler(log_filename)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        if print_to_console:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)  
            self.logger.addHandler(ch)

    def save_to_file(self, msg):
        self.logger.debug(msg[1])

if __name__ == "__main__":
    logObj = telemetry_log('telemetry')

    with logObj:
        for i in range(10):
            logObj.message_callback(i)
            time.sleep(1)