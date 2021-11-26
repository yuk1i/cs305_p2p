from __future__ import annotations

from typing import List, Tuple

TORRENT_STATUS_NOT_STARTED = 0
TORRENT_STATUS_METADATA = 1
TORRENT_STATUS_DOWNLOADING = 2
TORRENT_STATUS_FINISHED = 3


class TorrentController:
    def __init__(self, torrent_hash: str):
        self.torrent_hash: str = torrent_hash
        self.status = TORRENT_STATUS_NOT_STARTED
        self.chunk_status: List[bool] = list()
        self.peer_list: List[Tuple[str, int]] = list()
        self.tracker_addr: Tuple[str, int] = ("", 0)

    def on_peer_list_update(self, peers: List[Tuple[str, int]]):
        print("[TorrentCtrl] {} Peer List updated: {}".format(self.torrent_hash, peers))
        self.peer_list = peers
        pass
