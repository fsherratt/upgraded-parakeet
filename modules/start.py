import threading
import time

from modules import data_types


class Startup():
    def __init__(self):
        self.process_name = 'test'
        self.active_threads = threading.enumerate()

        self.health_loop_running = True
        self.health_loop_delay_event = threading.Event()
        self.heartbeat_period = 0.5

        self.process_close_delay = 1

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        self.stop()

    def run(self):
        main_thread = threading.Thread(target=self.start, name='main_thread')
        main_thread.start()

        # Setup close listener

        self.health_loop()

    def start(self):
        """
        Module startup routine
        """
        def test_func():
            print('running')
            time.sleep(3)

        for i in range(10):
            new_thread = threading.Thread(target=test_func,
                                          name='thread_{}'.format(i),
                                          daemon=True)

            new_thread.start()
            time.sleep(0.5)

        time.sleep(10)

        self.stop_callback()
        # assert NotImplementedError       

    def stop(self):
        """
        Used to elegantly shut down the module code
        """
        # assert NotImplementedError

    def stop_callback(self):
        self.stop()
        self._stop_health_loop()   

    def _stop_health_loop(self):
        self.health_loop_running = False
        self.health_loop_delay_event.set()
    
    def health_loop(self):
        while self.health_loop_running:
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
            #TODO: add logging mechanism
            print('Thread {} closed'.format(thread.name))

    def _log_thread_started(self, thread_list: list):
        threads = set(thread_list) - set(self.active_threads)

        for thread in threads:
            #TODO: add logging mechanism
            print('Thread {} created'.format(thread.name))

    def _send_heartbeat(self):
        heartbeat = data_types.ProcessHeartbeat(self.process_name,
                                                threading.active_count())
        #TODO: add publisher mechanism
        print(heartbeat)



if __name__ == "__main__":

    tHealth = Startup()

    tHealth.run()

    # with tHealth:
    #     time.sleep(10)
    # tHealth.run() # Run does not return
