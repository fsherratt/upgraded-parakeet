#!/usr/local/bin/python3

from udp_proxy import udp_proxy
import pika
import sys

class udp_publisher():
    """
    Set-up for recievining from rabbit mq and publishing to the udp port
    """
    def __init__( self, ip_addr:str, port:int ):
        self._proxy = udp_proxy( ip_addr, port )
        # Setup RabbitMQ
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters( host = 'localhost' ) )
        self._channel = self._connection.channel()

        self._channel.exchange_declare( exchange='udp_message', exchange_type='direct' )
        result = self._channel.queue_declare( queue='', exclusive=True )
        self._queue_name = result.method.queue

        self._channel.queue_bind( exchange="udp_message", queue=self._queue_name, routing_key="message" )

    """
    Callback function for routing message to the proxy server
    """
    def _routeMessageToServer( self, ch, method, properties, body ):
        self._proxy.SendMessage( body )

    """
    Begins reciving data from the queue and forwarding all data to the declared udp port
    """
    def BeginPublishing( self ):
        self._channel.basic_consume(
            queue=self._queue_name, on_message_callback=self._routeMessageToServer, auto_ack=True )
        self._channel.start_consuming()

if __name__ == "__main__":
    pub = udp_publisher( '127.0.0.1', 5005 )
    pub.BeginPublishing()
