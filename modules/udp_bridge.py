"""
This module acts as a UDP bridge between rabbit mq networks
"""
import pickle
import time
import threading

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


class Message_Producer:
    def __init__(self, rbmq_host):
        self._host = rbmq_host

        self._msg_queue = async_message.AsyncMessageCallback()
        self._running = True
        self._producer = None

    def queue_command(self, msg):
        if not isinstance(msg, data_types.Telemetry_Message):
            return  # TODO: Err here

        self._msg_queue.queue_message(msg)

    def loop(self):
        while self._running:
            _, msg = self._msg_queue.wait_for_message()

            if msg is None:
                continue

            self.send_msg(msg)

    def stop_thread(self):
        self._running = False
        self._msg_queue.unblock_wait()

    def start_thread(self):
        self._loop_thread = threading.Thread(target=self.loop, name="RabbitMq_Producer")
        self._loop_thread.start()

    def send_msg(self, msg):
        print("Producer: {}".format(msg), flush=True)
        producer = message_broker.Producer(
            host=self._host, exchange_key=msg.addr_exch, routing_key=msg.addr_route
        )
        producer.open_channel()
        producer.send_message(msg.data)
        producer.close_channel()


class Message_Consumer:
    def __init__(self, out_callback, rbmq_exchange, rbmq_route, rbmq_host):
        self._out_callback = out_callback

        self.host = rbmq_host
        self.exchange = rbmq_exchange
        self.route = rbmq_route

        self._consumer = None

    def start_thread(self):
        self._consumer = message_broker.Consumer(
            callback=self._out_callback,
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
            # TODO: decode back from bytes
            msg = pickle.loads(msg)

            print("UDP Listener: {}".format(msg), flush=True)
            self._out_callback(msg)


class Udp_Broadcaster:
    def __init__(self, udp_host, udp_port):
        self._running = True
        self._loop_thread = None

        self._msg_queue = async_message.AsyncMessageCallback()

        self._udp = udp.udp_socket(broadcast_address=(udp_host, udp_port))

    def queue_command(self, msg):
        self._msg_queue.queue_message(msg)

    def stop_thread(self):
        self._running = False
        self._msg_queue.unblock_wait()

    def start_thread(self):
        self._loop_thread = threading.Thread(target=self.loop, name="UDP_Listener")
        self._loop_thread.start()

    def loop(self):
        while self._running:
            _, msg = self._msg_queue.wait_for_message()

            if msg is None:
                continue

            print("UDP Broadcast: {}".format(msg), flush=True)

            # TODO: Ensure msg is in format bytes
            msg = pickle.dumps(msg)
            self._udp.write(msg)


if __name__ == "__main__":
    except_hook = excepthook.Capture_Event()

    print("Starting", flush=True)
    cli_args = cli_parser.parse_cli_input(multiple_processes=True)
    conf = load_config.from_file(cli_args.config)

    rbmq_host = message_broker.getHostName()

    if cli_args.process == "udp_listen":
        rmq_obj = Message_Producer(rbmq_host=rbmq_host)
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
            out_callback=udp_obj.queue_command,
            rbmq_exchange=conf.udp_bridge.listen_exchange.exchange,
            rbmq_route=conf.udp_bridge.listen_exchange.route,
            rbmq_host=rbmq_host,
        )

    else:
        raise Warning("Unknown process `{}`".format(cli_args.process))

    try:
        udp_obj.start_thread()
        rmq_obj.start_thread()

        print("Running", flush=True)

        except_hook.wait_for_exception()

    except KeyboardInterrupt:
        pass

    finally:
        print("Exiting", flush=True)
        udp_obj.stop_thread()
        rmq_obj.stop_thread()
