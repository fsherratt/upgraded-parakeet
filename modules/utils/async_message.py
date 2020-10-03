"""
This module contains classes for aiding in processing incoming and outgoing asyncronous messages
"""
import threading
import queue
import time


class AsyncMessageCallback:
    """
    This class provides an asyncronous interface for recieving and queue messages
    """

    def __init__(self, wait_timeout=None, queue_size=-1):
        self._wait_timeout = wait_timeout

        self._message_queue = queue.Queue(maxsize=queue_size)
        self._new_message_event = threading.Event()

    def wait_for_message(self):
        """
        Blocking message retrieval
        """
        self._new_message_event.wait(timeout=self._wait_timeout)
        time = 0
        msg = None

        try:
            time, msg = self._message_queue.get_nowait()
        except queue.Empty:
            self._clear_message_event()

        return time, msg

    def queue_message(self, data):
        """
        Add an incoming message to the queue and flag
        """
        try:
            self._message_queue.put_nowait((time.time(), data))
            self._set_message_event()
        except queue.Full:
            # TODO: Add in logging for dropped messages
            pass  # Silently drop message for the moment

    def unblock_wait(self):
        """
        Unblock wait_for_message - useful for cleanly exiting threads
        """
        self._set_message_event()

    def _clear_message_event(self):
        """
        Clear message event - indicates all messages processed
        """
        self._new_message_event.clear()

    def _set_message_event(self):
        """
        Set message event - indicates new message available
        """
        self._new_message_event.set()


class Async_Threaded_Queue:
    def __init__(self):
        self._msg_queue = AsyncMessageCallback()

        self._running = None
        self._thread = None

    def queue_command(self, command):
        self._msg_queue.queue_message(command)

    def start_thread(self):
        self._running = True

        self._thread = threading.Thread(
            target=self._process_queue, name=self.__class__.__name__, daemon=True
        )
        self._thread.start()

    def stop_thread(self):
        self._running = False
        self._msg_queue.unblock_wait()

        if self._thread:
            self._thread.join(timeout=1)

            if self._thread.is_alive():
                print(
                    "{}: Failed to close thread {}".format(
                        self.__class__.__name__, self._thread.name
                    ),
                    flush=True,
                )
                # TODO: Log error
                return

        print("{}: Succesfully closed thread".format(self.__class__.__name__))

    def _process_queue(self):
        while self._running:
            timestamp, msg = self._msg_queue.wait_for_message()

            if msg is None:
                continue

            msg = self.interpret_msg(timestamp, msg)
        print("{}: Exited thread loop".format(self.__class__.__name__), flush=True)

    def interpret_msg(self, timestamp, msg):
        raise NotImplementedError