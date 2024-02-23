import time
import multiprocessing


# # Function to run in the subprocess
# def timer_func():
#     # Count time in background
#     count = 0
#     while True:
#         print(f"Time elapsed in subprocess: {count} seconds")
#         count += 1
#         time.sleep(1)
#
#
# if __name__ == "__main__":
#     # Create a subprocess for the timer
#     timer_process = multiprocessing.Process(target=timer_func)
#     timer_process.start()
#
#     # Main process doing some work
#     for i in range(5):
#         print(f"Main process: Doing work {i}")
#         time.sleep(2)  # Simulate some work
#
#     # Terminate the subprocess after the main process is done
#     # timer_process.terminate()
#     print("Main process: Finished")

import multiprocessing
import random

FIND = 50
MAX_COUNT = 1000


def find(process, initial, return_dict, run):
    while run.is_set():
        start = initial
        while start <= MAX_COUNT:
            if FIND == start:
                return_dict[process] = f"Found: {process}, start: {initial}"
                run.clear() # Stop running.
                break
            start += random.randrange(0, 10)
            print(start)


if __name__ == "__main__":
    processes = []
    manager = multiprocessing.Manager()
    return_code = manager.dict()
    run = manager.Event()
    run.set()  # We should keep running.
    for i in range(5):
        process = multiprocessing.Process(
            target=find, args=(f"computer_{i}", i, return_code, run)
        )
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print(return_code.values())