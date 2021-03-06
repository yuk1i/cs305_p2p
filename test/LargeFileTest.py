import os
import sys
import time
from threading import Thread

from PClient import PClient

tracker_address = ("127.0.0.1", 10086)

FILE_PATH = "../test_files/20mb"

if not os.path.exists(FILE_PATH):
    print(f'generate file {FILE_PATH} first')

with open(FILE_PATH, "rb") as f:
    bdata = f.read()


def client_download(client):
    client.download(FILE_PATH)


if __name__ == '__main__':
    A = PClient(tracker_address, upload_rate=1000000, download_rate=1000000)
    B = PClient(tracker_address, upload_rate=1000000, download_rate=1000000)
    C = PClient(tracker_address, upload_rate=1000000, download_rate=1000000)
    D = PClient(tracker_address, upload_rate=1000000, download_rate=1000000)
    fid = A.register(FILE_PATH)
    files = {}
    clients = [B, C, D]
    threads = []

    # function for download and save
    def download(node, index):
        files[index] = node.download(fid)


    for i, client in enumerate(clients):
        threads.append(Thread(target=download, args=(clients[i], i)))

    time_start = time.time_ns()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Time of P2P model: {(time.time_ns() - time_start) * 1e-9}")
    with open(FILE_PATH, "rb") as bg:
        bdata = bg.read()
        for i in files:
            if files[i] != bdata:
                raise Exception()

    A.close()
    for c in clients:
        c.close()
    sys.exit(0)
