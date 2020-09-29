class Arduino_Commands:
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
