import time
import threading
import queue
import pickle
import os

import modules.udp_broker
import modules.message_broker
from smbus2 import SMBus

from modules.data_types import Arduino_Heartbeat, Arduino_Command


class Commands:
    MODE_OFF = ord("o")
    MODE_INITIALISING = ord("i")
    MODE_RUNNING = ord("r")
    MODE_ARMNED = ord("a")
    MODE_TAKEOFF = ord("t")
    MODE_LANDING = ord("l")
    MODE_COLLISION_AVOID = ord("c")
    MODE_ERROR = ord("e")
    MODE_MUCH_ERROR = ord("E")

    SET_LED_MODE = 1
    SET_BRIGHTNESS = 2
    SET_STROBES = 3
    SET_NAV_LIGHTS = 4
    READ_HEARTBEAT = 5


class ArduinoSlave:
    def __init__(self, address: int):
        self._Arduino_SMBus = None
        self._device = None

        self.set_address(address)

    def set_address(self, address: int):
        self._device = address

    def open_connection(self):
        """
        Open the i2c connection
        """
        self._Arduino_SMBus = SMBus(1)

    def close_connection(self):
        """
        Close the i2c connection
        """
        self._Arduino_SMBus.close()

    def read_from(self, mode: int, num_bytes: int) -> list:
        """
        read_from
        Read num_bytes from the mode register
        """
        try:
            self._Arduino_SMBus.write_byte_data(self._device, mode, 0)
            data = self._Arduino_SMBus.read_i2c_block_data(self._device, 0, num_bytes)
        except OSError:  # TODO: Err properly
            return None

        return data

    def write_to(self, mode: int, data_bytes):
        """
        write_to
        Write a list of ints to the mode register
        """
        try:
            self._Arduino_SMBus.write_byte_data(self._device, mode, 0)

            if isinstance(data_bytes, list):
                self._Arduino_SMBus.write_i2c_block_data(self._device, 0, data_bytes)
            else:
                self._Arduino_SMBus.write_byte_data(self._device, 0, data_bytes)
        except OSError:  # TODO: Err properly
            pass

    def set_led_mode(self, new_mode: int):
        self.write_to(Commands.SET_LED_MODE, new_mode)

    def set_brightness(self, brightness: int):
        if brightness < 0:
            brightness = 0
        elif brightness > 255:
            brightness = 255

        self.write_to(Commands.SET_BRIGHTNESS, brightness)

    def set_strobes(self, enable: bool):
        self.write_to(Commands.SET_STROBES, enable)

    def set_nav_lights(self, enable: bool):
        self.write_to(Commands.SET_NAV_LIGHTS, enable)

    def read_heartbeat(self):
        heartbeat = self.read_from(Commands.READ_HEARTBEAT, 12)

        if not isinstance(heartbeat, list) or len(heartbeat) != 12:
            return None

        timestamp = int.from_bytes(heartbeat[0:4], byteorder="little", signed=False)
        mode = chr(heartbeat[4])
        brightness = heartbeat[5]
        strobe_enable = heartbeat[6]
        nav_enable = heartbeat[7]

        return Arduino_Heartbeat(
            timestamp=timestamp,
            mode=mode,
            brightness=brightness,
            strobe_enable=strobe_enable,
            nav_enable=nav_enable,
        )


class ArduinoRunner:
    def __init__(self, address: int):
        self._arduino = ArduinoSlave(address)

        self._running = True

        self._heartbeat_event = threading.Event()
        self._heartbeat_period = 1

        self._action_queue = queue.Queue(maxsize=0)
        self._action_event = threading.Event()

        self._heartbeat_thread = None
        self._heartbeat_producer = None

        self._action_thread = None

    def start(self):
        self._arduino.open_connection()
        self._start_heartbeat_loop()
        self._start_action_loop()

    def stop(self):
        self._running = False
        self._heartbeat_event.set()
        self._action_event.set()

        self._arduino.close_connection()

    def recv_actions(self, action):
        print(action, flush=True)

        if not isinstance(action, Arduino_Command):
            print("Invalid command", flush=True)
            return

        self.set_action(action)

    def set_action(self, action):
        self._action_queue.put(action)
        self._action_event.set()

    def _start_heartbeat_loop(self):
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, name="arduino_heartbeat"
        )
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        self._heartbeat_producer = message_broker.Producer(
            routing_key="ground",
            exchange_key="telemetry",
            host=os.environ.get("RABBITMQ_HOST"),  # TODO: fix telemetry connection
        )
        self._heartbeat_producer.open_channel()

        while self._running:
            self.set_action(Arduino_Command(cmd=Commands.READ_HEARTBEAT, action=None))

            self._heartbeat_event.wait(timeout=self._heartbeat_period)
            self._heartbeat_event.clear()

        self._heartbeat_producer.close_channel()

    def _transmit_heartbeat(self, heartbeat):
        if not isinstance(heartbeat, Arduino_Heartbeat):
            return

        msg = udp_broker.Telemetry_Message(
            addr_route="route", addr_exch="exch", data=heartbeat
        )
        print(msg)
        self._heartbeat_producer.send_message(msg)

    def _action_loop(self):
        while self._running:
            self._action_event.wait()
            self._action_event.clear()

            try:
                action = self._action_queue.get_nowait()
            except queue.Empty:
                continue

            try:
                if action.cmd is Commands.SET_LED_MODE:
                    self._arduino.set_led_mode(action.action)

                elif action.cmd is Commands.SET_BRIGHTNESS:
                    self._arduino.set_brightness(action.action)

                elif action.cmd is Commands.SET_STROBES:
                    self._arduino.set_strobes(action.action)

                elif action.cmd is Commands.SET_NAV_LIGHTS:
                    self._arduino.set_nav_lights(action.action)

                elif action.cmd is Commands.READ_HEARTBEAT:
                    self._transmit_heartbeat(self._arduino.read_heartbeat())

                else:
                    print("Command unknown", flush=True)
            except AttributeError:
                pass

    def _start_action_loop(self):
        self._action_thread = threading.Thread(
            target=self._action_loop, name="arduino_actions"
        )
        self._action_thread.start()


if __name__ == "__main__":
    runner = ArduinoRunner(4)
    consumer = message_broker.Consumer(
        runner.recv_actions,
        routing_key="all",
        exchange_key="led",
        host=os.environ.get("RABBITMQ_HOST"),
    )
    consumer.open_exchange()

    try:
        consumer.start_consuming_thread()
        runner.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        consumer.stop_consuming()
        runner.stop()
        print("Exiting")
