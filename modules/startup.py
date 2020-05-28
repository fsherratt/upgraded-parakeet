import threading
import time

from modules import data_types


class Startup:
    def __init__(self, process_name):
        self.main_thread = None
        self.process_name = process_name
        self.active_threads = threading.enumerate()

        self.module_running = True
        self.health_loop_delay_event = threading.Event()
        self.heartbeat_period = 0.5

        self.process_close_delay = 1

    def __enter__(self):
        self.module_startup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.module_shutdown()

    def run(self):
        self.module_startup()
        self.main_thread = threading.Thread(target=self._main_loop, name="main_thread")
        self.main_thread.start()

        # TODO: Setup close listener

        self.health_loop()

    def module_loop(self):
        """
        Module main loop
        """
        assert NotImplementedError

    def module_startup(self):
        """
        Module startup routine
        """
        assert NotImplementedError

    def module_shutdown(self):
        """
        Used to elegantly shut down the module code
        """
        assert NotImplementedError

    def stop_callback(self, *args):
        self.module_shutdown()
        # This could be a daemon thread that closes when the process finishes?
        self._stop_health_loop()

    # TODO: Exception handling decorator
    def _main_loop(self):
        while self.module_running:
            self.module_loop()

    def _stop_health_loop(self):
        self.module_running = False
        self.health_loop_delay_event.set()

    # TODO: Exception handling decorator
    def health_loop(self):
        while self.module_running:
            if not self.main_thread.is_alive():
                print("Oh No!!!! Bad things!")
                # TODO: Log main thread closed and shutdown process
                self.stop_callback()
                continue

            self.thread_health()

            self.health_loop_delay_event.wait(timeout=self.heartbeat_period)

        time.sleep(self.process_close_delay)

    def thread_health(self):
        current_threads = threading.enumerate()

        self._log_thread_closure(current_threads)
        self._log_thread_started(current_threads)
        self._send_heartbeat()

        self.active_threads = current_threads

    def _log_thread_closure(self, thread_list: list):
        threads = set(self.active_threads) - set(thread_list)

        for thread in threads:
            # TODO: add logging mechanism
            print("Thread {} closed".format(thread.name))

    def _log_thread_started(self, thread_list: list):
        threads = set(thread_list) - set(self.active_threads)

        for thread in threads:
            # TODO: add logging mechanism
            print("Thread {} created".format(thread.name))

    def _send_heartbeat(self):
        heartbeat = data_types.ProcessHeartbeat(
            timestamp=time.time(),
            process_name=self.process_name,
            process_alive=self.main_thread.is_alive(),
            thread_count=threading.active_count(),
        )
        # TODO: add publisher mechanism
        print(heartbeat)
