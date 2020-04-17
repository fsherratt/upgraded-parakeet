import threading
import queue
import sys
import time

class logging_interface:
    def __init__(self):
        self._loq_queue = queue.Queue()
        self._log_queue_event = threading.Event()

        self._loop_running = True

    # Called by message broker
    def message_callback(self, data):
        timestamp = time.time()

        if self._loop_running:
            self._queue_message(timestamp, data)
            self._set_message_event()

    def _queue_message(self, time, data):
        self._loq_queue.put((time, data))

    def log_loop(self):
        while self._loop_running:
            self._wait_for_message_event()

            msg = self._get_message()

            if msg is None:
                self._clear_message_event()
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
            return None

    # Interface method
    def save_to_file(self, msg):
        # Save message to file using abstracted save method
        print(msg, file=sys.stdout)


if __name__ == "__main__":
    logObj = logging_interface()
    logObj.start_logging_loop()

    for i in range(10):
        logObj.message_callback(i)
        time.sleep(1)

    logObj.stop_logging_loop()