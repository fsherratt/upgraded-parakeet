"""
This module handles all startup classes
"""
import threading
import time
import argparse
from modules import data_types

# TODO: Add a listener for close rabbit mq that matcehs the process_tag variable
class Startup:
    """
    Startup and monitoring thread class for modules
    """

    def __init__(self, process_tag):
        self.main_thread = None
        self.process_tag = process_tag
        self.active_threads = threading.enumerate()

        self.module_running = True
        self.health_loop_delay_event = threading.Event()
        self.heartbeat_period = 0.5

        self.process_close_delay = 1

    def __enter__(self):
        """
        With functionality can be used to run without health monitoring
        """
        self.module_startup()
        self._main_loop()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.module_shutdown()

    def run(self):
        """
        Launch the encapsulated module on the main_thread
        """
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
        """
        Callback for elegant stop of module
        """
        self.module_running = False
        self._stop_health_loop()

    # TODO: Exception handling decorator
    def _main_loop(self):
        while self.module_running:
            self.module_loop()

        self.module_shutdown()

    def _stop_health_loop(self):
        self.health_loop_delay_event.set()

    # TODO: Exception handling decorator
    def health_loop(self):
        """
        Interal process health monitoring and reporting
        """
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
        """
        Determine the health of the internal threads
        """
        current_threads = threading.enumerate()

        self._log_thread_closure(current_threads)
        self._log_thread_started(current_threads)
        self._send_heartbeat()

        self.active_threads = current_threads

    def _log_thread_closure(self, thread_list: list):
        threads = set(self.active_threads) - set(thread_list)

        for thread in threads:
            # TODO: Can we get a callback how how the thread exited?
            # TODO: add logging mechanism
            print("Thread {} closed".format(thread.name))

        return threads

    def _log_thread_started(self, thread_list: list):
        threads = set(thread_list) - set(self.active_threads)

        for thread in threads:
            # TODO: add logging mechanism
            print("Thread {} created".format(thread.name))

        return threads

    def _send_heartbeat(self):
        heartbeat = data_types.ProcessHeartbeat(
            timestamp=time.time(),
            process_tag=self.process_tag,
            process_alive=self.main_thread.is_alive(),
            thread_count=threading.active_count(),
        )
        # TODO: add publisher mechanism
        print(heartbeat)

    @staticmethod
    def parse_cli_input() -> argparse.Namespace:
        """
        Parse standard command line inputs for launchable module
        """
        parser = argparse.ArgumentParser(description="Launch Modules")
        parser.add_argument(
            "-o",
            "-O",
            "--options",
            type=str,
            nargs="+",
            required=True,
            help="Realsense stream type to launch",
        )
        parser.add_argument(
            "-c",
            "-C",
            "--config",
            type=str,
            required=False,
            default=None,
            help="Configuration file",
        )
        parser.add_argument(
            "-d",
            "-D",
            "--debug",
            action="store_true",
            required=False,
            default=False,
            help="Enable debug output",
        )
        parser.add_argument(
            "-pt",
            "-PT",
            "--process_tag",
            type=str,
            default=None,
            required=False,
            help="Process identification tag",
        )
        return parser.parse_known_args()[0]
