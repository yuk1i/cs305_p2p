import os.path
from typing import Tuple

import controller
from utils.bytes_utils import random_bytes, bytes_to_hexstr
from proxy import Proxy
from torrent import Torrent
from utils import IPPort

save_dir = "temp/"


class PClient:
    def __init__(self, tracker_addr: Tuple[str, int], proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        # school codes
        self.my_addr: IPPort = ('127.0.0.1', self.proxy.port)
        self.peerController = controller.PeerController(self.proxy, self.my_addr, tracker_addr)
        self.mtu = 65500
        self.peerController.socket.mtu = self.mtu
        self.peerController.notify_tracker()

    def register(self, file_path: str) -> str:
        random_name = bytes_to_hexstr(random_bytes(32))
        t = Torrent.generate_torrent(file_path, random_name, 65450)
        t.__is_school_torrent__ = True
        self.peerController.register_torrent(t, save_dir + random_name + ".torrent", os.path.dirname(file_path))
        # self.peerController.start_download(t.torrent_hash)
        return t.torrent_hash

    def download(self, fid) -> bytes:
        dummy_t = Torrent.create_dummy_torrent(fid)
        dummy_t.__is_school_torrent__ = True
        random_name = bytes_to_hexstr(random_bytes(16))
        self.peerController.register_torrent(dummy_t, save_dir + random_name + ".torrent", save_dir + random_name)
        self.peerController.start_download(dummy_t.torrent_hash)
        self.peerController.active_torrents[fid].wait_downloaded()
        return self.peerController.active_torrents[fid].dir_controller.get_tested_binary()

    def cancel(self, fid):
        self.peerController.stop_torrent(fid)

    def close(self):
        self.peerController.close_from_tracker()
        self.peerController.close()
