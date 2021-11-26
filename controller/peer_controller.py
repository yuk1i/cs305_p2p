from __future__ import annotations

from typing import Tuple, Dict, List, Set

import conn
import proxy
import controller
from torrent import Torrent
from utils.bytes_utils import random_long, bytes_to_int


class TrackerStatus:
    NOT_NOTIFIED = 1
    NOTIFYING = 2
    NOTIFIED = 3


class PeerController(controller.Controller):
    def __init__(self, pxy: proxy.Proxy, tracker_addr: Tuple[str, int]):
        super(PeerController, self).__init__(pxy)
        self.torrent_list: List[Torrent] = list()
        self.active_torrents: Dict[str, controller.TorrentController] = dict()
        self.peer_conns: List[conn.P2PConn] = list()
        self.tracker_addr = tracker_addr
        self.tracker_conn: conn.PeerToTrackerConn = conn.PeerToTrackerConn(self.tracker_addr, self)
        self.tracker_status: int = TrackerStatus.NOT_NOTIFIED
        self.tracker_uuid: int = 0

    def notify_tracker(self, my_addr: Tuple[str, int]):
        if self.tracker_status != TrackerStatus.NOT_NOTIFIED:
            print("[P2T] tracker status: %s" % self.tracker_status)
            return
        self.tracker_conn.notify(my_addr)

    def register_torrent(self, torrent: Torrent):
        self.tracker_conn.register(torrent)

