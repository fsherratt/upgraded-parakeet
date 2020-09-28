"""
This module acts as a go between for UDP telemetry and the rabbit mq network.
"""
import os
import pickle
import time
from typing import NamedTuple

from modules import message_broker, udp, data_types
from modules.data_types import *


class UdpSender:
    """
    Converts messages into packets that can be sent over UDP
    """

    def __init__(self, address: tuple, node="unspecified"):
        self._socket = udp.udp_socket(broadcast_address=address)
        self._socket.openPort()

        self._node = node
        self._seq = 0

    def closeSocket(self):
        self._socket.closePort()

    def send_udp_message(self, msg):
        if not isinstance(msg, Telemetry_Message):
            raise Warning(
                "Message must be of type Message_Wrapper not {}".format(type(msg))
            )

        wrapped_msg = Message_Wrapper(
            node_id=self._node,
            seq_id=self._seq,
            addr_route=msg.addr_route,
            addr_exch=msg.addr_exch,
            data=msg.data,
            data_size=len(msg.data),
        )
        self._seq += 1

        msg_bytes = pickle.dumps(wrapped_msg)

        self._socket.write(msg_bytes)


class UdpReciever:
    """
    Revieves messages from UDP and reasembles them into their original form
    """

    def __init__(self, address: tuple):
        self._socket = udp.udp_socket(listen_address=address)
        self._socket.openPort()

    def closeSocket(self):
        self._socket.closePort()

    def wait_for_message(self, output_type=Message_Wrapper):
        msg = self._socket.read()
        return self._decode_udp_message(msg)

    def _decode_udp_message(self, msg: bytes):
        msg = pickle.loads(msg)
        return msg


class OutgoingMessages:
    """
    Listens for incoming message on the specified message
    exchange and passes then to a UDP sender
    """

    def __init__(
        self,
        listen_route: str,
        listen_exchange: str,
        udp_port: int,
        udp_host="0.0.0.0",
        rabbit_host="localhost",
        node="unspecified",
    ):
        self._listen_route = listen_route
        self._listen_exchange = listen_exchange
        self._rabbit_host = rabbit_host

        self._udp_out = UdpSender(address=(udp_host, udp_port), node=node)

        self._consumer = None

    def stop_listening(self):
        self._udp_out.closeSocket()
        self._consumer.stop_consuming()

    def start_listenting(self):
        self._consumer = message_broker.Consumer(
            callback=self.message_callback,
            routing_key=self._listen_route,
            exchange_key=self._listen_exchange,
            host=self._rabbit_host,
        )
        self._consumer.start_consuming_thread()

    def message_callback(self, msg):
        print("Time: {}\t Msg: {}".format(int(time.time() * 1000), msg), flush=True)
        self._udp_out.send_udp_message(msg)


class IncomingMessages:
    """
    Waits for incoming message over UDP and pushes them onto
    the correct exchange
    """

    def __init__(self, udp_port: int, udp_host="0.0.0.0", rabbit_host="localhost"):
        self._udp_in = UdpReciever(address=(udp_host, udp_port))

        self._rabbit_host = rabbit_host

    def stop_listening(self):
        self._udp_in.closeSocket()

    def listen(self):
        incoming = self._udp_in.wait_for_message()
        return incoming

    def route(self, msg: Message_Wrapper):
        try:
            routing_key = msg.addr_route
            routing_exc = msg.addr_exch
            data = msg.data
        except AttributeError:
            return

        out = message_broker.Producer(
            routing_key=routing_key,
            exchange_key=routing_exc,
            host=self._rabbit_host,
        )

        out.open_channel()
        out.send_message(data)
        out.close_channel()


if __name__ == "__main__":
    print("Starting", flush=True)
    rbMQ_host = os.environ.get("RABBITMQ_HOST")
    # Incoming broker messages are in background thread

    telemtry_out = OutgoingMessages(
        listen_exchange="telemetry",
        listen_route="copter",
        udp_port=4005,
        udp_host="192.168.137.255",
        # udp_host="255.255.255.255",
        rabbit_host=rbMQ_host,
    )
    telemtry_out.start_listenting()

    # Incoming UDP messages are in main thread
    telemetry_in = IncomingMessages(udp_port=4006, rabbit_host=rbMQ_host)
    try:
        while True:
            msg = telemetry_in.listen()
            print(msg, flush=True)
            telemetry_in.route(msg)

    except KeyboardInterrupt:
        pass

    finally:
        telemtry_out.stop_listening()
        telemetry_in.stop_listening()
