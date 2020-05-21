import threading
import time
import copy

def test_func():
    print('running')
    time.sleep(1)

if __name__ == "__main__":
    threads = threading.enumerate()
    
    for i in range(10):
        new_thread = threading.Thread(target=test_func, name='thread_{}'.format(i))
        new_thread.start()
        time.sleep(0.5)

        current_threads = threading.enumerate()
        threading.active_count()
        # check difference between current threads and _threads
        threads_closed = set(threads) - set(current_threads)
        threads_opened = set(current_threads) - set(threads)
        
        for t in threads_opened:
            print('Thread {} created'.format(t.name))

        for t in threads_closed:
            print('Thread {} closed'.format(t.name))

        print('Active theads: {}'.format(threading.active_count()))

        threads = current_threads
    