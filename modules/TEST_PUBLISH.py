#!/usr/local/bin/python3

import pika
import sys

class test_rabbitmq_publisher():
    """
    Set-up for default rabbit mq publisher
    """
    def __init__( self, exchange_name:str, routing_key:str):
        self._exchange_name = exchange_name
        self._routing_key = routing_key

        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters( host = 'localhost' ) )
        self._channel = self._connection.channel()

        self._channel.exchange_declare( exchange=self._exchange_name, exchange_type='direct' )


    """
    Begins reciving data from the queue and forwarding all data to the declared udp port
    """
    def SendMessage( self, message:str ):
        self._channel.basic_publish(
                exchange=self._exchange_name,
                routing_key=self._routing_key,
                body=message )


if __name__ == "__main__":
    if len( sys.argv ) < 2:
        print( "Usage: {sys.argv[0]} <exchange name> <routing key> <message>" )
    else:
        pub = test_rabbitmq_publisher( sys.argv[1], sys.argv[2] )
        pub.SendMessage( sys.argv[3] )
