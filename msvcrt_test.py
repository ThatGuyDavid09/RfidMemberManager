import msvcrt
from queue import Empty, Queue
from threading import Thread


def read_keys(queue):
    for key in iter(msvcrt.getwch, '\x03'):  # until `q`
        queue.put(key)
    queue.put(None)  # signal the end


q = Queue()
t = Thread(target=read_keys, args=[q])
t.daemon = True  # die if the program exits
t.start()

buffer = ""
while True:
    try:
        key = q.get_nowait()  # doesn't block
    except Empty:
        key = Empty
    else:
        if key is None:  # end
            break
    # do stuff
    if key != Empty:
        if key == b'\x03':
            break

        if key.isdigit():
            buffer += key
        elif key.isalpha():
            print(f"{key} is not difit")
            buffer = ""

        if key == "\r":
            if len(buffer) < 10:
                buffer = ""
                continue
            print("return lol")
            card_number = buffer[-10:]
            print(card_number)
            buffer = ""

        print(key)
