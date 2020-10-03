"""
This module acts as a UDP bridge between rabbit mq networks
"""
import pickle
import time
import threading
import sys

from modules.utils import (
    udp,
    load_config,
    cli_parser,
    async_message,
    message_broker,
    excepthook,
)

from modules.__context import definitions
from definitions import data_types


class Message_Producer(async_message.Async_Threaded_Queue):
    def __init__(self, host):
        super().__init__()
        self._host = host

    def interpret_msg(self, timestanmp, msg):
        if not isinstance(msg, data_types.Telemetry_Message):
            return  # TODO: Err here

        print("Message_Producer: {}".format(msg), flush=True)
        producer = message_broker.Producer(
            host=self._host, exchange_key=msg.addr_exch, routing_key=msg.addr_route
        )
        producer.open_channel()
        producer.send_message(msg.data)
        producer.close_channel()


class Message_Consumer:
    def __init__(self, callback, exchange_key, routing_key, host):
        self._out_callback = callback

        self.host = host
        self.exchange = exchange_key
        self.route = routing_key

        self._consumer = None

    def check_type(self, msg):
        """
        If the message doesn't already have a destination,
        send it to the same as consumer
        """
        if not isinstance(msg, data_types.Telemetry_Message):
            msg = data_types.Telemetry_Message(
                addr_route=self.route, addr_exch=self.exchange, data=msg
            )

        self._out_callback(msg)

    def start_thread(self):
        self._consumer = message_broker.Consumer(
            callback=self.check_type,
            host=self.host,
            exchange_key=self.exchange,
            routing_key=self.route,
        )
        self._consumer.start_consuming_thread()

    def stop_thread(self):
        self._consumer.stop_consuming()


class Udp_Listener:
    def __init__(self, out_callback, udp_host, udp_port):
        self._out_callback = out_callback

        self._running = True
        self._loop_thread = None

        self._udp = udp.udp_socket(listen_address=(udp_host, udp_port))

    def stop_thread(self):
        self._running = False

    def start_thread(self):
        self._loop_thread = threading.Thread(target=self.loop, name="UDP_Listener")
        self._loop_thread.start()

    def loop(self):
        while self._running:
            msg = self._udp.read()

            if msg is None:
                continue

            try:
                msg = pickle.loads(msg)
            except pickle.UnpicklingError:
                # TODO: Log that meesage couldn't be decoded
                continue

            print("UDP Listener: {}".format(msg), flush=True)
            self._out_callback(msg)

        print("UDP_Listener: Exiting", flush=True)


class Udp_Broadcaster(async_message.Async_Threaded_Queue):
    def __init__(self, udp_host, udp_port):
        super().__init__()

        self._udp = udp.udp_socket(broadcast_address=(udp_host, udp_port))

    def interpret_msg(self, timestamp, msg):
        print("UDP Broadcast: {}".format(msg), flush=True)

        try:
            msg = pickle.dumps(msg)
        except pickle.PickleError:
            return
            # TODO: log error

        self._udp.write(msg)


if __name__ == "__main__":
    except_hook = excepthook.Capture_Event()

    print("Starting", flush=True)
    cli_args = cli_parser.parse_cli_input(multiple_processes=True)
    conf = load_config.from_file(cli_args.config)

    if cli_args.process == "udp_listen":
        rmq_obj = Message_Producer(host=message_broker.getHostName())
        udp_obj = Udp_Listener(
            out_callback=rmq_obj.queue_command,
            udp_host=conf.udp_bridge.udp.incoming_host,
            udp_port=conf.udp_bridge.udp.incoming_port,
        )

    elif cli_args.process == "udp_broadcast":
        udp_obj = Udp_Broadcaster(
            udp_host=conf.udp_bridge.udp.outgoing_host,
            udp_port=conf.udp_bridge.udp.outgoing_port,
        )
        rmq_obj = Message_Consumer(
            callback=udp_obj.queue_command,
            routing_key=conf.udp_bridge.listen_exchange.route,
            exchange_key=conf.udp_bridge.listen_exchange.exchange,
            host=message_broker.getHostName(),
        )

    else:
        raise Warning("Unknown process `{}`".format(cli_args.process))

    # Start up proxy
    try:
        udp_obj.start_thread()
        rmq_obj.start_thread()

        print("Running", flush=True)

        except_hook.wait_for_exception()

    except KeyboardInterrupt:
        pass

    finally:
        print("Exiting", flush=True)
        time.sleep(5)

        # Gracefully shutdown
        udp_obj.stop_thread()
        rmq_obj.stop_thread()

    print("Closed", flush=True)
