import time
from threading import Thread

from PClient import PClient

tracker_address = ("127.0.0.1", 10086)

times = 10

low = 40000
fast = 200000

tit_tat = True

if __name__ == '__main__':
    # A,B,C,D,E join the network
    print("test")
    A = PClient(tracker_address, upload_rate=200000, download_rate=400000, tit_tat=tit_tat)
    print("test")
    B = PClient(tracker_address, upload_rate=low, download_rate=fast, tit_tat=tit_tat)
    C = PClient(tracker_address, upload_rate=fast, download_rate=fast, tit_tat=tit_tat)
    D = PClient(tracker_address, upload_rate=low, download_rate=fast, tit_tat=tit_tat)
    E = PClient(tracker_address, upload_rate=fast, download_rate=fast, tit_tat=tit_tat)
    F = PClient(tracker_address, upload_rate=low, download_rate=fast, tit_tat=tit_tat)
    G = PClient(tracker_address, upload_rate=fast, download_rate=fast, tit_tat=tit_tat)
    H = PClient(tracker_address, upload_rate=low, download_rate=fast, tit_tat=tit_tat)
    I = PClient(tracker_address, upload_rate=fast, download_rate=fast, tit_tat=tit_tat)
    # J = PClient(tracker_address, upload_rate=low, download_rate=fast, tit_tat=tit_tat)
    # K = PClient(tracker_address, upload_rate=fast, download_rate=fast, tit_tat=tit_tat)

    # clients = [B, C, D, E, F, G, H, I, J, K]
    clients = [B, C, D, E, F, G, H, I]
    # A register a file and B download it
    fid = A.register("../test_files/bg.png")
    threads = []
    files = {}

    # function for download and save
    def download(node, index):
        files[index] = node.download(fid)

    time_start = time.time_ns()
    for i, client in enumerate(clients):
        threads.append(Thread(target=download, args=(client, i)))
    # start download in parallel
    for t in threads:
        t.start()
    # wait for finish
    for t in threads:
        t.join()
    # check the downloaded files
    with open("../test_files/bg.png", "rb") as bg:
        bs = bg.read()
        for i in files:
            if files[i] != bs:
                raise Exception("Downloaded file is different with the original one")

    threads.clear()

    print("SUCCESS")


    A.close()
    B.close()
    C.close()
    D.close()
    E.close()
    F.close()
    G.close()
    H.close()
    I.close()
    # J.close()
    # K.close()
    print((time.time_ns() - time_start) * 1e-9)
