"""
Utility functions for handling uncaught exceptions
"""

import sys
import threading


class Capture_Event:
    """
    This class overides the default uncaught exception behaviour. This allows us to capture
    uncaught exceptions in threaded activities and act on this information.
    """

    def __init__(self):
        # Event "Flag" to indicate an uncaught exception has occured
        self._exception_event = threading.Event()

        # Store the default exception hooks
        self._default_sys_excepthook = sys.excepthook
        self._default_thread_excepthook = threading.excepthook

        # Replace defaults with our overide
        sys.excepthook = self._excepthook
        threading.excepthook = self._thread_excepthook

    def _excepthook(self, exc_type, exc_value, exc_traceback):
        self._log_exception(exc_type, exc_value, exc_traceback)
        self._exception_event.set()

        self._default_sys_excepthook(exc_type, exc_value, exc_traceback)

    def _thread_excepthook(self, args):
        self._log_exception(args.exc_type, args.exc_value, args.exc_traceback)
        self._exception_event.set()

        self._default_thread_excepthook(args)

    def _log_exception(self, exc_type, exc_value, exc_traceback):
        """
        Overload this methods to log uncaught exceptions
        """
        pass

    def wait_for_exception(self):
        """
        Efficiently wait for an uncaught exception to occur
        """
        self._exception_event.wait()

    def reset_exception_flat(self):
        self._exception_event.clear()

    def has_exception_occured(self) -> bool:
        return self._exception_event.is_set()


    def exception_occured(self) -> bool:
        return self._event.is_set()
