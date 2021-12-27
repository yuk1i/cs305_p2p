import os.path
import multiprocessing as mp
from typing import Tuple

import controller
import statistics
from utils.bytes_utils import random_bytes, bytes_to_hexstr
from Proxy import Proxy
from torrent import Torrent
from utils import IPPort

save_dir = "temp/"


class PClient:
    EV_REGISTER = 1
    EV_DOWNLOAD = 2
    EV_CANCEL = 3
    EV_CLOSE = 4

    def __init__(self, tracker_addr: Tuple[str, int], proxy=None, port=None, upload_rate=0, download_rate=0):
        self.use_mp = False
        if self.use_mp:
            # For myself: read in pipe_me, write in pipe_me
            # For mp:     read in pipe_mp, write in pipe_mp
            self.pipe_me, self.pipe_mp = mp.Pipe()
            self.process = mp.Process(target=self.__start__,
                                      args=(tracker_addr, proxy, port, upload_rate, download_rate,))
            self.process.start()
            self.pipe_me.recv()
        else:
            self.__start__(tracker_addr, proxy, port, upload_rate, download_rate)

    def __start__(self, tracker_addr: Tuple[str, int], proxy, port, upload_rate, download_rate):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        # school codes
        self.my_addr: IPPort = ('127.0.0.1', self.proxy.port)
        if self.use_mp:
            print(f"Peer Process started, name {self.process.name}")
            self.process.name = f"Peer: {self.proxy.port}"
        self.mtu = 65500
        self.tracker_addr = tracker_addr
        self.peerController = controller.PeerController(self.proxy, self.my_addr, self.tracker_addr)
        self.peerController.socket.mtu = self.mtu
        self.peerController.notify_tracker()
        statistics.get_instance().on_new_client(self.my_addr[1])
        statistics.get_instance().start()
        if not self.use_mp:
            return
        self.pipe_mp.send(123123)
        while True:
            (ev_type, data) = self.pipe_mp.recv()
            if ev_type == PClient.EV_REGISTER:
                self.pipe_mp.send(self.__register__(data))
            elif ev_type == PClient.EV_DOWNLOAD:
                self.pipe_mp.send(self.__download__(data))
            elif ev_type == PClient.EV_CANCEL:
                self.__cancel__(data)
                self.pipe_mp.send(None)
            elif ev_type == PClient.EV_CLOSE:
                self.__close__()
                self.pipe_mp.send(None)
                break

    def __register__(self, file_path):
        random_name = bytes_to_hexstr(random_bytes(32))
        t = Torrent.generate_torrent(file_path, random_name, 10000)
        t.__is_school_torrent__ = True
        self.peerController.register_torrent(t, save_dir + random_name + ".torrent", os.path.dirname(file_path))
        self.peerController.start_download(t.torrent_hash)
        return t.torrent_hash

    def __download__(self, fid):
        dummy_t = Torrent.create_dummy_torrent(fid)
        dummy_t.__is_school_torrent__ = True
        random_name = bytes_to_hexstr(random_bytes(16))
        self.peerController.register_torrent(dummy_t, save_dir + random_name + ".torrent", save_dir + random_name)
        self.peerController.start_download(dummy_t.torrent_hash)
        self.peerController.active_torrents[fid].wait_downloaded()
        return self.peerController.active_torrents[fid].dir_controller.get_tested_binary()

    def __cancel__(self, fid):
        self.peerController.stop_torrent(fid)

    def __close__(self):
        self.peerController.close()

    def register(self, file_path: str) -> str:
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        if self.use_mp:
            self.pipe_me.send((PClient.EV_REGISTER, file_path))
            return self.pipe_me.recv()  # read fid back
        else:
            return self.__register__(file_path)

    def download(self, fid) -> bytes:
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        if self.use_mp:
            self.pipe_me.send((PClient.EV_DOWNLOAD, fid))
            return self.pipe_me.recv()  # read binary back
        else:
            return self.__download__(fid)

    def cancel(self, fid):
        if self.use_mp:
            self.pipe_me.send((PClient.EV_CANCEL, fid))
            self.pipe_me.recv()  # wait cancel
        else:
            return self.__cancel__(fid)

    def close(self):
        if self.use_mp:
            self.pipe_me.send((PClient.EV_CLOSE, None))
            self.pipe_me.recv()  # wait close
        else:
            return self.__close__()
