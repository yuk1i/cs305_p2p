import time
from socket import *
from threading import Thread
from queue import SimpleQueue
import random


def get_socket(port):
    i = port if port else random.randint(20000, 65536)
    while True:
        try:
            soc = socket(AF_INET, SOCK_DGRAM)
            soc.bind(("127.0.0.1", i))
            break
        except Exception:
            i = random.randint(20000, 65536)
    soc.settimeout(1)
    return soc, i


class Proxy:
    def __init__(self, upload_rate, download_rate, port=None):
        self.upload_rate = upload_rate
        self.download_rate = download_rate
        self.socket, self.port = get_socket(port)
        self.recv_buffer, self.recv_queue, self.send_queue = SimpleQueue(), SimpleQueue(), SimpleQueue()

        self.active = True
        Thread(target=self.__send_thread__).start()
        Thread(target=self.__buffer_thread__).start()
        Thread(target=self.__recv_thread__).start()

    def __send_thread__(self):
        while self.active:
            if not self.send_queue.empty():
                (packet, dst) = self.send_queue.get()
                if self.upload_rate:
                    time.sleep(len(packet) / self.upload_rate)
                self.socket.sendto(packet, dst)
            else:
                time.sleep(0.000001)

    def __buffer_thread__(self):
        while self.active:
            try:
                msg, frm = self.socket.recvfrom(65536)
                self.recv_buffer.put((msg, frm))
            except Exception:
                time.sleep(0.000001)

    def __recv_thread__(self):
        while self.active or not self.recv_buffer.empty():
            if not self.recv_buffer.empty():
                msg, frm = self.recv_buffer.get()
                if self.download_rate:
                    time.sleep(len(msg) / self.download_rate)
                self.recv_queue.put((msg, frm))
            else:
                time.sleep(0.000001)

    def sendto(self, data, address):
        self.send_queue.put((data, address))

    def recvfrom(self, timeout=None) -> (bytes, (str, int)):
        t = time.time()
        while not timeout or time.time() - t < timeout:
            if not self.recv_queue.empty():
                return self.recv_queue.get()
            time.sleep(0.000001)
        raise TimeoutError

    def close(self):
        self.active = False
