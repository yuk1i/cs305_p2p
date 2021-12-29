import os
import sys
import time
from threading import Thread

from PClient import PClient

tracker_address = ("127.0.0.1", 10086)

FILE_PATH = "tests/test_files/alice.txt"

print(os.system("pwd"))

with open(FILE_PATH, "rb") as bg:
    bs = bg.read()


def client_download(client):
    client.download(FILE_PATH)


if __name__ == '__main__':
    # A, B, C, D, E join the network
    # 理论最小时间： 20*1024*1024 / 500000 = 40 s
    # 150 * 1024 / 5000 = 30.7 real: 38ms
    A = PClient(tracker_address, upload_rate=5000, download_rate=100000)
    B = PClient(tracker_address, upload_rate=500000, download_rate=100000)
    C = PClient(tracker_address, upload_rate=500000, download_rate=100000)
    D = PClient(tracker_address, upload_rate=500000, download_rate=100000)
    E = PClient(tracker_address, upload_rate=500000, download_rate=100000)
    fid = A.register(FILE_PATH)
    files = {}
    clients = [B, C, D, E]
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
        bs = bg.read()
        for i in files:
            if files[i] != bs:
                raise Exception()

    A.close()
    for c in clients:
        c.close()
    sys.exit(0)
