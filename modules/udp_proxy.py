#!/usr/local/bin/python3

import socket
import sys
import threading
import queue
import time

DEFAULT_IP_ADDR = "127.0.0.1"
DEFAULT_PORT = 5005

class udp_proxy:
    def __init__( self, ip_addr:str, port:int ):
        """
        IP address to listen on
        """
        self._ip_addr = ip_addr

        """
        Port to recieve on
        """
        self._port = port

        """
        Socket to be listened on
        """
        self.sock = socket.socket( 
                        socket.AF_INET,
                        socket.SOCK_DGRAM )

        """
        Queue and event handlers
        """
        self._message_queue_event = threading.Event()
        self._message_queue = queue.Queue()
        self.listening_started = False

    """
    Bind to the UDP port specified in init
    """
    def _bindToPort( self, ip_addr:str, port:int ):
        self._ip_addr = ip_addr
        self._port = port
        self.sock.bind( (ip_addr, port ) )

    """
    Add message to the queue
    """
    def _queueMessage( self, timestamp:float, message:str ):
        self._message_queue.put( (timestamp, message ));

    """
    Raise a message event
    """
    def _setMessageEvent( self ):
        self._message_queue_event.set()

    """
    Clear event handler for message recieved
    """
    def _clearMessageEvent( self ):
        self._message_queue_event.clear()

    """
    Wait forever for a message
    """
    def _waitForMessageEvent( self ):
        self._message_queue_event.wait()

    """
    Gets a message from the queue.
    If the queue is empty, clear the message event.
    """
    def _getMessage( self ):
        try:
            return self._message_queue.get_nowait()
        except queue.Empty:
            self._clearMessageEvent()
            return None
    
    """
    Start a thread for listening on the socket.
    This creates a self._message_thread object
    """
    def _startSocketThread( self ):
        self._message_thread = threading.Thread( target=self.ListenToSocket )
        self._message_thread.start()

    """
    Listen for data on the socket for the provided ip and port.
    When data is recieved into the buffer (1024), 
    put it into a queue and raise a message event
    """
    def ListenToSocket( self ):
        self._bindToPort( self._ip_addr, self._port )
        # FIXME should proably make a method to close this nicely.
        self.listening_started = True
        while self.listening_started:
            #FIXME should probably actually work out buffer size.
            data, addr = self.sock.recvfrom( 1024 )
            data = data.decode()
            timestamp = time.time()
            self._queueMessage( timestamp, data )
            self._setMessageEvent()

    """
    Recieve any data on the port
    """
    def RecieveData( self ) -> str:
        if not self.listening_started:
            self._startSocketThread()
        self._waitForMessageEvent()
         
        return self._getMessage()


    """
    Recieve data and print to the console forever
    """
    def RecieveForeverToConsole( self ):
        self._bindToPort( self._ip_addr, self._port )
        print( "[x] Recieving forever..." )
        while True:
            data, addr = self.sock.recvfrom( 1024 )
            data = data.decode()
            print( f"recieved message:{data}" )

    """
    Send a message to the supplied ip and port
    """
    def SendMessage( self, message:str ):
        #handling for bytes being passed in
        if isinstance( message, str ):
            message = message.encode()

        self.sock.sendto( message, ( self._ip_addr, self._port ) )

if __name__ == "__main__":
    proxy = udp_proxy( DEFAULT_IP_ADDR, DEFAULT_PORT )
    if len( sys.argv ) < 2:
        proxy.RecieveForeverToConsole()

    print( f"Current arguments" )
    print( f" length:{len(sys.argv)}, arg1:{sys.argv[1]}, arg2:{sys.argv[2]}")
    
    if sys.argv[ 1 ] == "send":
        print( "[x] Sending message..." )
        proxy.SendMessage( sys.argv[ 2 ] )
    else:
        print( "[x] Arguments not recognised. Argument: {sys.argv[1]}" )
        print( "[x] Valid argument: send" )
    print( "[x] EXITING" )

