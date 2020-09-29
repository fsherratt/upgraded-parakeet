import threading
import time
import sys
import threading

import pika
import pickle


class RabbitMQCommon:
    def __init__(
        self,
        routing_key: str,
        exchange_key: str,
        exchange_type="direct",
        host="localhost",
    ):
        self.exchange_key = exchange_key
        self.routing_key = routing_key

        self.host = host
        self.exchange_type = exchange_type

        self._connection = None
        self._channel = None

    def open_exchange(self):
        try:
            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
        except pika.exceptions.AMQPConnectionError:
            print("Connection failed: Is rabbitmq-server running", file=sys.stderr)
            raise ConnectionRefusedError

        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self.exchange_key, exchange_type=self.exchange_type
        )

    def close_exchange(self):
        print("Closing exchange")
        if self._channel:
            try:
                self._channel.stop_consuming()
            except pika.exceptions.AMQPConnectionError as error:
                print(error, file=sys.stderr)

        # Delay gives time for stream to close
        time.sleep(0.1)

        if self._connection:
            try:
                self._connection.close()
            except pika.exceptions.AMQPConnectionError as error:
                print(error, file=sys.stderr)


class Consumer(RabbitMQCommon):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)

        self.callback = callback
        self._rabbit_thread = None

    def start_consuming_thread(self):
        print("Starting production")
        self._rabbit_thread = threading.Thread(
            target=self.consumer_loop, name="rabbit_mq_consumer", daemon=True
        )
        self._rabbit_thread.start()

    def stop_consuming(self):
        self.close_exchange()

    def consumer_loop(self):
        self.open_exchange()

        msg_queue = self._channel.queue_declare(queue="", exclusive=True)
        queue_name = msg_queue.method.queue

        # Specific setup
        self._channel.queue_bind(
            exchange=self.exchange_key,
            queue=queue_name,
            routing_key=self.routing_key,
        )
        self._channel.basic_consume(
            queue=queue_name,
            on_message_callback=self.message_callback,
            auto_ack=True,
        )

        try:
            self._channel.start_consuming()
        except pika.exceptions.ConnectionClosed:
            print("Connection closed")
            # TODO: dp something with this information

        except pika.exceptions.StreamLostError:
            print("Stream Lost")

    def message_callback(self, channel, method, properties, data):
        data = pickle.loads(data)
        self.callback(data)


class Producer(RabbitMQCommon):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._write_lock = threading.Lock()

    def open_channel(self):
        self.open_exchange()

    def send_message(self, msg):
        msg = pickle.dumps(msg)
        try:
            self._write_lock.acquire()
            self._channel.basic_publish(
                exchange=self.exchange_key, routing_key=self.routing_key, body=msg
            )
        finally:
            self._write_lock.release()

    def close_channel(self):
        self.close_exchange()
