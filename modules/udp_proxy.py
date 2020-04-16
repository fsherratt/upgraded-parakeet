#!/usr/local/bin/python3

import socket
import sys

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
        self.sock = socket.socket( socket.AF_INET,
                              socket.SOCK_DGRAM )

    def RecieveForever( self ):
        self.sock.bind( ( self._ip_addr, self._port )  )
        print( "[x] Recieving forever..." )

        while True:
            data, addr = self.sock.recvfrom( 1024 )
            data = data.decode()
            print( f"recieved message:{data}" )

    def SendMessage( self, message:str ):
        print( f"Sending message : {message} to addr : {self._ip_addr}, port : {self._port}" )
        self.sock.sendto( message.encode(), ( self._ip_addr, self._port ) )

if __name__ == "__main__":
    proxy = udp_proxy( DEFAULT_IP_ADDR, DEFAULT_PORT )
    if len( sys.argv ) < 2:
        proxy.RecieveForever()

    print( f"Current arguments" )
    print( f" length:{len(sys.argv)}, arg1:{sys.argv[1]}, arg2:{sys.argv[2]}")
    
    if sys.argv[ 1 ] == "send":
        print( "[x] Sending message..." )
        proxy.SendMessage( sys.argv[ 2 ] )
    else:
        print( "[x] Arguments not recognised. Argument: {sys.argv[1]}" )
        print( "[x] Valid argument: send" )
    print( "[x] EXITING" )

