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
        msg = None

        try:
            msg = self._message_queue.get_nowait()
        except queue.Empty:
            self._clear_message_event()

        return msg

    def queue_message(self, data):
        """
        Add an incoming message to the queue and flag
        """
        try:
            self._message_queue.put_nowait((time.time(), data))
            self._set_message_event()
        except queue.Full:
            #TODO: Add in logging for dropped messages
            pass # Silently drop message for the moment

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
