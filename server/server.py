import logging
import functools
import os
import queue
import time
import threading
import sys
import select

from flask import Flask, render_template
from flask_socketio import SocketIO

from server.__context import definitions, modules
from definitions import data_types

from modules.utils import (
    load_config,
    cli_parser,
    async_message,
    message_broker,
    excepthook,
)


class Server:
    def __init__(
        self,
        flask_port=5000,
        flask_host="0.0.0.0",
        flask_secret_key="secret!",
        socketio_ping_timeout=5,
        socketio_ping_interval=1,
    ):
        self._host = flask_host
        self._port = flask_port

        self._app = Flask(__name__)
        self._app.config["SECRET_KEY"] = flask_secret_key

        self._socketio = SocketIO(
            self._app,
            ping_timeout=socketio_ping_timeout,
            ping_interval=socketio_ping_interval,
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

    def emit(self, msg: dict, event: str):
        self._socketio.emit(event, msg)

    def start(self, debug=False):
        self._socketio.run(app=self._app, host=self._host, port=self._port, debug=debug)

    def start_as_thread(self, debug=False):
        self._socket_thread = threading.Thread(
            target=self.start, kwargs={"debug": debug}, name="Flask_Server", daemon=True
        )
        self._socket_thread.start()

    def stop(self):
        # Only use this if not run as a thread
        if self._socket_thread is not None:
            raise Warning("Trying to close socketio outside context")

        self._socketio.stop()


class Rabbit_To_Web_App(async_message.Async_Threaded_Queue):
    """
    Recieve incoming telemetry data and send
    to the correct socket_io event
    """

    def __init__(self, callable):
        super().__init__()
        self._callable = callable

    def interpret_msg(self, timestamp, msg):
        print(msg, file=sys.stdout, flush=True)
        self._callable(msg)


class Web_App_To_Rabbit(async_message.Async_Threaded_Queue):
    """
    Forward commands from the webapp and send
    to the correct vehicle rabbitmq channel
    """

    def __init__(self, callable):
        super().__init__()
        self._callable = callable

    def interpret_msg(self, timestamp, msg):
        print(msg, file=sys.stdout, flush=True)

        rtn_msg = None

        if msg["id"] == "led_on-off_toggle":
            rtn_msg = data_types.Telemetry_Message(
                addr_exch="telemetry", addr_route="ground", data="On"
            )
        elif msg["id"] == "led_strobe_toggle":
            rtn_msg = data_types.Telemetry_Message(
                addr_exch="telemetry", addr_route="ground", data="Strobe"
            )
        elif msg["id"] == "led_nav_toggle":
            rtn_msg = data_types.Telemetry_Message(
                addr_exch="telemetry", addr_route="ground", data="Nav"
            )

        self._callable(rtn_msg)


if __name__ == "__main__":
    print("Starting", flush=True)
    except_hold = excepthook.Capture_Event()

    cli_args = cli_parser.parse_cli_input(multiple_processes=False)
    conf = load_config.from_file(cli_args.config)

    # Setup server
    flask_server = Server(
        flask_port=conf.server.flask.port,
        flask_host=conf.server.flask.host,
        flask_secret_key=conf.server.flask.secret_key,
        socketio_ping_timeout=conf.server.socket_io.ping_timeout,
        socketio_ping_interval=conf.server.socket_io.ping_interval,
    )

    # Setup input path
    rabbit_interpreter = Rabbit_To_Web_App(
        callable=functools.partial(
            flask_server.emit,
            event=conf.server.socket_io.emit_label,
        )
    )
    telem_in = message_broker.Consumer(
        callback=rabbit_interpreter.queue_command,
        routing_key=conf.message_broker.consume.route,
        exchange_key=conf.message_broker.consume.exchange,
        host=message_broker.getHostName(),
    )

    # Setup output path
    telem_out = message_broker.Producer(
        routing_key=conf.message_broker.produce.route,
        exchange_key=conf.message_broker.produce.exchange,
        host=message_broker.getHostName(),
    )
    web_interpreter = Web_App_To_Rabbit(callable=telem_out.send_message)
    flask_server.set_recv_callback(web_interpreter.queue_command)

    # Start up everything
    try:
        telem_in.start_consuming_thread()
        telem_out.open_channel()

        web_interpreter.start_thread()
        rabbit_interpreter.start_thread()

        flask_server.start_as_thread(debug=conf.server.flask.debug)

        print("Running", flush=True)

        # Wait here unless an exception occurs
        except_hold.wait_for_exception()

    except KeyboardInterrupt:
        pass

    finally:
        print("Exiting", flush=True)

        # Gracefully shutdown
        telem_in.stop_consuming()
        telem_out.close_channel()

        web_interpreter.stop_thread()
        rabbit_interpreter.stop_thread()

        time.sleep(5)
        print("Closed", flush=True)
