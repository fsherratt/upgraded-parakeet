import threading
import queue
import sys
import time

def saveToFile():
    global log_queue
    global new_log_item

    while True:
        new_log_item.wait()

        try:
            while True:
                new_data = log_queue.get_nowait()
                print(new_data, file=sys.stdout)

        except queue.Empty:
            new_log_item.clear()

if __name__ == "__main__":
    global log_queue
    global new_log_item

    new_log_item = threading.Event()
    log_queue = queue.Queue()

    log_thread = threading.Thread(target=saveToFile, daemon=True)
    log_thread.start()

    for i in range(10):
        log_queue.put(i)
        new_log_item.set()

        time.sleep(1)
