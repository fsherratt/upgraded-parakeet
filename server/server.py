import logging
import os
import queue
import time
import threading
import sys

from flask import Flask, render_template
from flask_socketio import SocketIO

from modules import message_broker, data_types
from modules.led_interface import Commands as LED_Commands


class server:
    def __init__(self, recv_callback):
        self._host = "0.0.0.0"
        self._port = 5000
        self._recv_callback = recv_callback

        self._socket_thread = None

        self._app = Flask(__name__)
        self._app.config["SECRET_KEY"] = "secret!"

        self._socketio = SocketIO(
            self._app,
            ping_timeout=5,
            ping_interval=1,
        )

        self._attach_pages()
        self._attach_events()

    def _attach_pages(self):
        @self._app.route("/")
        def index(name=None):
            return render_template("index.html", name=name)

    def _attach_events(self):
        @self._socketio.on("button_click")
        def button_handler(data):
            self._recieve(msg=data)

    def _recieve(self, msg):
        self._recv_callback(msg)

    def emit(self, event: str, msg: dict):
        self._socketio.emit(event, msg)
        time.sleep(1)

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
        recv_callback,
        listen_route: str,
        listen_exchange: str,
        rabbit_host="localhost",
    ):
        self.message_callback = recv_callback

        self._listen_route = listen_route
        self._listen_exchange = listen_exchange
        self._rabbit_host = rabbit_host

        self._consumer = None

    def stop_listening(self):
        self._consumer.stop_consuming()

    def start_listenting(self):
        self._consumer = message_broker.Consumer(
            callback=self.message_callback,
            routing_key=self._listen_route,
            exchange_key=self._listen_exchange,
            host=self._rabbit_host,
        )
        self._consumer.start_consuming_thread()


class telemetry_udp_to_web_app:
    """
    Recieve incoming telemetry data and send
    to the correct socket_io event
    """

    def __init__(self, emit_handler, route: str, exch: str, host: str):
        self._consumer = None
        self._route = route
        self._exch = exch
        self._host = host

    def start(self):
        self._setup_rabbitmq_consumer()

    def stop(self):
        if self._consumer is not None:
            self._consumer.stop_consuming()

    def _setup_rabbitmq_consumer(self):
        self._consumer = telemtry_consumer(
            recv_callback=self.recv_handler,
            listen_route=self._route,
            listen_exchange=self._exch,
            rabbit_host=self._host,
        )
        self._consumer.start_listenting()

    def recv_handler(self, msg):
        print("Msg: {}".format(msg))


class telemetry_web_app_to_udp:
    """
    Forward commands from the webapp and send
    to the correct vehicle rabbitmq channel
    """

    def __init__(self, route: str, exch: str, host: str):
        self._producer = None
        self._route = route
        self._exch = exch
        self._host = host

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

    def _send_test_data(self):
        data = data_types.Telemetry_Message(
            addr_route="test_route", addr_exch="test_exch", data="Hello, World!"
        )
        self.send_message(data)

    def recv_handler(self, msg):
        if msg["id"] == "led_on-off_toggle":
            cmd = data_types.Arduino_Command(
                cmd=LED_Commands.SET_LED_MODE,
                action=LED_Commands.MODE_INITIALISING,
            )
            data = data_types.Telemetry_Message(
                addr_route="all", addr_exch="led", data=cmd
            )
            self.send_message(data)

        elif msg["id"] == "led_strobe_toggle":
            cmd = data_types.Arduino_Command(
                cmd=LED_Commands.SET_LED_MODE,
                action=LED_Commands.MODE_OFF,
            )
            data = data_types.Telemetry_Message(
                addr_route="all", addr_exch="led", data=cmd
            )
            self.send_message(data)

        elif msg["id"] == "led_nav_toggle":
            data = data_types.Telemetry_Message(
                addr_route="test_route", addr_exch="test_exch", data="Toggle Nav"
            )
            self.send_message(data)

        else:
            print("Msg: {}".format(msg))


if __name__ == "__main__":
    rbMQ_host = os.environ.get("RABBITMQ_HOST")

    telem_out = telemetry_web_app_to_udp(
        exch="telemetry", route="copter", host=rbMQ_host
    )

    flask_server = server(recv_callback=telem_out.recv_handler)
    flask_server.start_as_thread()

    telem_in = telemetry_udp_to_web_app(
        emit_handler=flask_server.emit, exch="telemetry", route="ground", host=rbMQ_host
    )

    try:
        telem_in.start()
        telem_out.start()

        while True:
            time.sleep(1)
            # telem_out._send_test_data()

    except KeyboardInterrupt:
        pass

    finally:
        telem_in.stop()
        telem_out.stop()
        print("Exiting")
