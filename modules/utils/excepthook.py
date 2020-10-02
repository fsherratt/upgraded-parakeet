import sys
import threading

class Capture_Event:
    def __init__(self):
        self._default_sys_excepthook = sys.excepthook
        self._default_thread_excepthook = threading.excepthook

        self._event = threading.Event()

        sys.excepthook = self._excepthook
        threading.excepthook = self._thread_excepthook

    def _excepthook(self, exc_type, exc_value, exc_traceback):
        self._log_exception(exc_type, exc_value, exc_traceback)
        self._event.set()

        self._default_sys_excepthook(exc_type, exc_value, exc_traceback)

    def _thread_excepthook(self, args, /):
        self._log_exception(args.exc_type, args.exc_value, args.exc_traceback)
        self._event.set()

        self._default_thread_excepthook(args)

    def _log_exception(self, exc_type, exc_value, exc_traceback):
        print('Exception: {}'.format(exc_type), flush=True)
        #TODO: log exception

    def wait_for_exception(self):
        self._event.wait()

    def exception_occured(self) -> bool:
        return self._event.is_set()


def thread_monitoring(self):
    created_threads = [i for i in threading.enumerate() if type(i) is threading.Thread]