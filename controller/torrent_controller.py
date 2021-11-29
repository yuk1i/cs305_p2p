from __future__ import annotations

from typing import List, Tuple

import controller
from torrent import Torrent
from utils import IPPort


class TorrentController:
    def __init__(self, torrent: Torrent):
        self.torrent_hash: str = torrent.torrent_hash
        self.torrent = torrent
        self.status = controller.TorrentStatus.TORRENT_STATUS_NOT_STARTED
        self.chunk_status: List[bool] = list()
        self.peer_list: List[IPPort] = list()
        self.tracker_addr: IPPort = ("", 0)

    def on_peer_list_update(self, peers: List[IPPort]):
        print("[TorrentCtrl] {} Peer List updated: {}".format(self.torrent_hash, peers))
        self.peer_list = peers
        pass

    def close(self):
        pass
