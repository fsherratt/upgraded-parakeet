import queue
import time
import threading

from flask import Flask, render_template
from flask_socketio import SocketIO


class server:
    def __init__(self, recv_callback):
        self._host = "0.0.0.0"
        self._port = 5000
        self._recv_callback = recv_callback

        self._socket_thread = None

        self._app = Flask(__name__)
        self._app.config["SECRET_KEY"] = "secret!"

        self._socketio = SocketIO(self._app, ping_timeout=5, ping_interval=1)

        self._attach_pages()
        self._attach_events()

    def _attach_pages(self):
        @self._app.route("/")
        def hello(name=None):
            return render_template("index.html", name=name)

    def _attach_events(self):
        @self._socketio.on("button_click")
        def test_click(data):
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


class commands_handler:
    def __init__(self):
        self._running = True
        self._new_cmd_event = threading.Event()
        self._cmd_queue = queue.Queue()

        self._cmd_thread = None

    def start(self):
        self._cmd_thread = threading.Thread(target=self.cmd_loop, name="cmd_handler")
        self._cmd_thread.start()

    def stop(self):
        self._running = False
        self._new_cmd_event.set()

    def cmd_loop(self):
        while self._running:
            self._new_cmd_event.wait(timeout=1)

            while True:
                try:
                    cmd = self._cmd_queue.get_nowait()
                except queue.Empty:
                    break

                print(cmd, flush=True)

    def incoming_callback(self, msg):
        self._cmd_queue.put_nowait(msg)
        self._new_cmd_event.set()


if __name__ == "__main__":
    cmd_handler = commands_handler()
    cmd_handler.start()

    flask_server = server(recv_callback=cmd_handler.incoming_callback)
    flask_server.start_as_thread()

    try:
        while True:
            # msg = udp_reciever.read()
            msg = ""
            # flask_server.emit(
            #     event="incoming_message",
            #     msg={"timestamp": int(time.time() * 1000), "msg": msg},
            # )

            time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        cmd_handler.stop()
        print("Exiting")
