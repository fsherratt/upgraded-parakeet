"""
This module contains a abstraction for forming a UDP connection
"""
import threading
import socket
import traceback
import select
import time
import sys
import warnings
import os


class udp_socket:
    def __init__(self, listen_address=None, broadcast_address=None):
        """
        __init__
        param listenAddress - tuple(host, port)
        param broadcastAddress - tuple(host, port)
        return void
        """
        self._sRead = None
        self._sWrite = None

        self.buff_size = 65535
        self.AF_type = socket.AF_INET
        self.SOCK_type = socket.SOCK_DGRAM
        self.enable_broadcast = True

        if listen_address is None and broadcast_address is None:
            raise Exception(
                "A address for either listen, broadcast or both is required"
            )

        self._read_address = listen_address
        self._write_address = broadcast_address

        self._write_lock = threading.Lock()
        self._read_lock = threading.Lock()

        self._rConnected = False
        self._wConnected = False

    def openPort(self):
        self._openReadPort()
        self._openWritePort()

        return False

    def _openReadPort(self) -> bool:
        if self._rConnected:
            return True

        elif self._read_address is None:
            warnings.warn(
                "Read address not known",
                UserWarning,
                stacklevel=3,
            )
            return False

        self._sRead = socket.socket(self.AF_type, self.SOCK_type)

        self._sRead.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self._sRead.setblocking(0)

        self.set_close_on_exec(self._sRead.fileno())

        self._sRead.bind(self._read_address)
        self._rConnected = True

        return True

    def _openWritePort(self) -> bool:
        if self._wConnected:
            return True

        elif self._write_address is None:
            warnings.warn("Write address not yet known", UserWarning, stacklevel=3)
            return False

        self._sWrite = socket.socket(self.AF_type, self.SOCK_type)

        if self.enable_broadcast:
            self._sWrite.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self._sWrite.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sWrite.setblocking(0)

        self.set_close_on_exec(self._sWrite.fileno())

        self._sWrite.connect(self._write_address)

        # Retrun read port can be deterimened after UDP connect
        if self._read_address is None:
            self._read_address = self._sWrite.getsockname()

        self._wConnected = True

        return True

    def closePort(self):
        self._closeReadPort()
        self._closeWritePort()

    def _closeReadPort(self):
        if self._sRead is None:
            return

        try:
            self._sRead.close()
            self.removeUNIXFile(self._read_address)

            self._rConnected = False
        except:
            traceback.print_exc(file=sys.stdout)

    def _closeWritePort(self):
        if self._sWrite is None:
            return

        try:
            self._sWrite.close()
            self._wConnected = False
        except:
            traceback.print_exc(file=sys.stdout)

    def read(self, b=0):
        if not self._openReadPort():
            return None

        self._read_lock.acquire()

        try:
            # Efficiently wait for data on the socket
            # Timeout = 0.5 second
            r_list, _, _ = select.select([self._sRead], [], [], 0.5)
            if not r_list:
                raise BlockingIOError()

            # Read data
            m, _ = self._sRead.recvfrom(self.buff_size)

        except (socket.timeout, BlockingIOError):
            m = None

        finally:
            self._read_lock.release()

        return m

    def write(self, b):
        if not self._openWritePort():
            return

        self._write_lock.acquire()

        try:
            self._sWrite.send(b)

        except Exception:
            traceback.print_exc(file=sys.stdout)

        finally:
            self._write_lock.release()

    def isOpen(self):
        return self._rConnected and self._wConnected

    def set_close_on_exec(self, fd):
        try:
            import fcntl

            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(fd, fcntl.F_SETFD, flags)
        except:
            pass

    def removeUNIXFile(self, fileName):
        if self.AF_type == socket.AF_UNIX:
            try:
                os.remove(fileName)
            except OSError:
                pass


if __name__ == "__main__":
    listener = udp_socket(listen_address=("localhost", 4000))

    listener.openPort()

    try:
        while True:
            data = listener.read()

            if data is None:
                continue

            print(
                "Time: {}\tMsg: {}".format(
                    int(time.time() * 1000), data.decode("UTF-8")
                )
            )

    except KeyboardInterrupt:
        pass

    finally:
        listener.closePort()

# ------------------------------------ EOF -------------------------------------
