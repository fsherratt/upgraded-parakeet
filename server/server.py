import logging
import os
import queue
import time
import threading
import sys
import select

from flask import Flask, render_template
from flask_socketio import SocketIO

from server.__context import definitions, modules
from definitions import enums, data_types

from modules.utils import message_broker, async_message


class server:
    def __init__(self):
        self._host = "0.0.0.0"
        self._port = 5000

        self._app = Flask(__name__)
        self._app.config["SECRET_KEY"] = "secret!"

        self._socketio = SocketIO(
            self._app,
            ping_timeout=5,
            ping_interval=1,
        )

        self._attach_pages()
        self._attach_events()

        self._recv_callback = None  # Web_app -> Interpreter
        self._socket_thread = None

    def _attach_pages(self):
        @self._app.route("/")
        def index(name=None):
            return render_template("index.html", name=name)

    def _attach_events(self):
        @self._socketio.on("button_click")
        def button_handler(data):
            self._recieve(msg=data)

    def _recieve(self, msg):
        if self._recv_callback is None:
            return

        self._recv_callback(msg)

    def set_recv_callback(self, recv_callback):
        self._recv_callback = recv_callback

    def emit(self, event: str, msg: dict):
        self._socketio.emit(event, msg)

    def start(self, debug=False):
        self._socketio.run(app=self._app, host=self._host, port=self._port, debug=debug)

    def start_as_thread(self):
        self._socket_thread = threading.Thread(
            target=self.start, kwargs={"debug": False}, name="Flask_Server", daemon=True
        )
        self._socket_thread.start()

    def stop(self):
        # Only use this if not run as a thread
        if self._socket_thread is not None:
            raise Warning("Trying to close socketio outside context")

        self._socketio.stop()


class telemtry_consumer:
    def __init__(
        self,
        exchange: str,
        route: str,
        hostname="localhost",
    ):
        self.message_callback = None

        self._listen_exchange = exchange
        self._listen_route = route
        self._rabbit_host = hostname

        self._consumer = None

    def set_recv_callback(self, recv_callback):
        self.message_callback = recv_callback

    def stop_listening(self):
        self._consumer.stop_consuming()

    def start_listenting(self):
        if self.message_callback is None:
            raise Warning("Message callback not yet set")

        self._consumer = message_broker.Consumer(
            callback=self.message_callback,
            routing_key=self._listen_route,
            exchange_key=self._listen_exchange,
            host=self._rabbit_host,
        )
        self._consumer.start_consuming_thread()


class telemetry_producer:
    def __init__(
        self,
        exchange: str,
        route: str,
        hostname="localhost",
    ):
        self._route = route
        self._exch = exchange
        self._host = hostname

        self._producer = None

    def start(self):
        self._setup_rabbitmq_producer()

    def stop(self):
        if self._producer is not None:
            self._producer.close_channel()

    def send_message(self, msg):
        self._producer.send_message(msg)

    def _setup_rabbitmq_producer(self):
        self._producer = message_broker.Producer(
            routing_key=self._route,
            exchange_key=self._exch,
            host=rbMQ_host,
        )
        self._producer.open_channel()


class Interpreter:
    def __init__(self, out_handle):
        self._out_handle = out_handle
        self._msg_queue = async_message.AsyncMessageCallback()

        self._running = True
        self._thread = None

    def stop(self):
        self._msg_queue.unblock_wait()

    def queue_command(self, command):
        self._msg_queue.queue_message(command)

    def start_thread(self):
        self._thread = threading.Thread(target=self.process_queue)
        self._thread.start()

    def stop_thead(self):
        self._running = False
        self._msg_queue.unblock_wait()

    def process_queue(self):
        while self._running:
            _, msg = self._msg_queue.wait_for_message()

            if msg is None:
                continue

            self.interpret_msg(msg)

    def interpret_msg(self, msg):
        return


class rabbit_to_web_app(Interpreter):
    """
    Recieve incoming telemetry data and send
    to the correct socket_io event
    """

    def interpret_msg(self, msg):
        print(msg, file=sys.stdout, flush=True)
        self._out_handle("A", msg)


class web_app_to_rabbit(Interpreter):
    """
    Forward commands from the webapp and send
    to the correct vehicle rabbitmq channel
    """

    def interpret_msg(self, msg):
        print(msg, file=sys.stdout, flush=True)

        rtn_msg = None

        if msg["id"] == "led_on-off_toggle":
            rtn_msg = data_types.Telemetry_Message(
                addr_exch="arduino", addr_route="all", data="On"
            )
        elif msg["id"] == "led_strobe_toggle":
            rtn_msg = data_types.Telemetry_Message(
                addr_exch="arduino", addr_route="all", data="Strobe"
            )
        elif msg["id"] == "led_nav_toggle":
            rtn_msg = data_types.Telemetry_Message(
                addr_exch="arduino", addr_route="all", data="Nav"
            )
        else:
            return

        self._out_handle(rtn_msg)


if __name__ == "__main__":
    # Setup input and output nodes
    rbMQ_host = os.environ.get("RABBITMQ_HOST")

    flask_server = server()
    telem_in = telemtry_consumer(
        exchange="telemetry", route="ground", hostname=rbMQ_host
    )
    telem_out = telemetry_producer(
        exchange="telemetry", route="copter", hostname=rbMQ_host
    )

    # Setup interpreters
    web_interpreter = web_app_to_rabbit(out_handle=telem_out.send_message)
    rabbit_interpreter = rabbit_to_web_app(out_handle=flask_server.emit)

    # Link end nodes to interperters
    flask_server.set_recv_callback(web_interpreter.queue_command)
    telem_in.set_recv_callback(rabbit_interpreter.queue_command)

    try:
        flask_server.start_as_thread()
        telem_in.start_listenting()
        telem_out.start()

        web_interpreter.start_thread()
        rabbit_interpreter.start_thread()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        telem_in.stop_listening()
        telem_out.stop()

        web_interpreter.stop_thead()
        rabbit_interpreter.stop_thead()

        print("Exiting")
