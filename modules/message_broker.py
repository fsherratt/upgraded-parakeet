import threading
import time

import pika


class consumer:
    def __init__(
        self,
        callback,
        routing_key,
        exchange_key,
        exchange_type="direct",
        host="localhost",
    ):
        self.callback = callback

        self.exchange_key = exchange_key
        self.routing_key = routing_key

        self.host = host
        self.exchange_type = exchange_type

        self._connection = None
        self._channel = None

        self._rabbit_thread = None

    def start_consuming_thread(self):
        print("Starting production")
        self._rabbit_thread = threading.Thread(
            target=self.consumer_loop, name="rabbit_mq_consumer"
        )
        self._rabbit_thread.start()

    def stop_consuming(self):
        print("Stopping production")
        try:
            if self._channel:
                self._channel.stop_consuming()
        except pika.exceptions.StreamLostError:
            print("Stream lost")

        # Delay gives time for stream to close
        time.sleep(0.1)

        try:
            if self._connection:
                self._connection.close()
        except pika.exceptions.ConnectionWrongStateError:
            print("Connection already closed")

    def consumer_loop(self):
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self.exchange_key, exchange_type=self.exchange_type
        )

        msg_queue = self._channel.queue_declare(queue="", exclusive=True)
        queue_name = msg_queue.method.queue

        # Specific setup
        self._channel.queue_bind(
            exchange=self.exchange_key, queue=queue_name, routing_key=self.routing_key,
        )
        self._channel.basic_consume(
            queue=queue_name, on_message_callback=self.message_callback, auto_ack=True,
        )

        try:
            self._channel.start_consuming()
        except pika.exceptions.StreamLostError:
            print("Stream Lost")

    def message_callback(self, channel, method, properties, data):
        self.callback(data)
