#!/usr/local/bin/python3

from udp_proxy import udp_proxy
import pika
import sys

class udp_subscriber():
    """
    Set-up for listening to the server and forwarding onto the local rabbit mq queues.
    """
    def __init__( self, ip_addr:str, port:int ):
        self._proxy = udp_proxy( ip_addr, port )
        # Setup RabbitMQ
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters( host = 'localhost' ) )
        self._channel = self._connection.channel()

        self._channel.exchange_declare( exchange='udp_message', exchange_type='direct' )

    """
    Route the message recieved from the server to rabbit mq
    """
    def _routeMessageFromServer( self, message:str ):
        #FIXME probably need to work out routing key.
        self._channel.basic_publish(
                exchange='udp_message',
                routing_key='recieved',
                body=message )

    """
    Begin listening on the server and forwarding messages to rabbit mq
    """
    def BeginSubscribing( self ):
        # Consume from proxy, publish to udp_message queue with recieved route.
        while True:
            data = self._proxy.RecieveData()
            # If we have data, publish it, otherwise drop the event
            if data is not None:
                self._routeMessageFromServer( str( data ) )
        
if __name__ == "__main__":
    pub = udp_subscriber( '127.0.0.1', 5005 )
    pub.BeginSubscribing()
