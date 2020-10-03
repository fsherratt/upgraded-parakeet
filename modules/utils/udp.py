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
        self.timeout = None

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

    def _openReadPort(self):
        if self._rConnected:
            return

        elif self._read_address is None:
            # TODO: Do something more helpful
            print("Read address not known")
            return

        self._sRead = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sRead.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sRead.settimeout(self.timeout)

        self.set_close_on_exec(self._sRead.fileno())

        self._sRead.bind(self._read_address)

        self._rConnected = True

    def _openWritePort(self):
        if self._wConnected:
            return

        elif self._write_address is None:
            # TODO: Do something more helpful
            return

        self._sWrite = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._sWrite.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sWrite.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sWrite.settimeout(self.timeout)

        self.set_close_on_exec(self._sWrite.fileno())

        self._sWrite.connect(self._write_address)

        self._wConnected = True

        # Read address can be deterimened after write connected
        if self._read_address is None:
            self._read_address = self._sWrite.getsockname()

    def closePort(self):
        self._closeReadPort()
        self._closeWritePort()

    def _closeReadPort(self):
        if self._sRead is None:
            return

        self._sRead.close()
        self._rConnected = False

    def _closeWritePort(self):
        if self._sWrite is None:
            return

        self._sWrite.close()
        self._wConnected = False

    def read(self, b=0):
        if not self._rConnected:
            return

        m = None
        try:
            self._read_lock.acquire()

            r_list, _, _ = select.select([self._sRead], [], [], 0.5)

            if r_list:
                m, addr = self._sRead.recvfrom(self.buff_size)

                # Write address can be learnt from incoming packet
                if self._write_address is None:
                    self._write_address = addr

        except socket.timeout:
            # TODO: something more useful here
            pass

        finally:
            self._read_lock.release()
            return m

    def write(self, b):
        if not self._wConnected:
            return

        bytes_remaining = None

        try:
            self._write_lock.acquire()

            bytes_remaining = self._sWrite.send(b)

        except socket.timeout:
            # TODO: something more useful here
            pass

        finally:
            self._write_lock.release()
            return bytes_remaining

    def set_close_on_exec(self, fd):
        try:
            import fcntl

            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(fd, fcntl.F_SETFD, flags)
        except:
            pass
