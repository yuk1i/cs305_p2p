from __future__ import annotations

from typing import Tuple, Dict, List, Set

import conn
import proxy
import controller
from torrent import Torrent
from utils import IPPort
from utils.bytes_utils import random_long, bytes_to_int


class PeerController(controller.Controller):
    def __init__(self, pxy: proxy.Proxy, my_addr: IPPort, tracker_addr: IPPort):
        super(PeerController, self).__init__(pxy)
        self.local_addr = my_addr
        self.torrent_list: List[Torrent] = list()
        self.active_torrents: Dict[str, controller.TorrentController] = dict()
        self.peer_conns: List[conn.P2PConn] = list()
        self.tracker_addr = tracker_addr
        self.tracker_conn: conn.PeerToTrackerConn = conn.PeerToTrackerConn(self.tracker_addr, self)
        self.tracker_status: int = controller.TrackerStatus.NOT_NOTIFIED
        self.tracker_uuid: int = 0

    def notify_tracker(self):
        if self.tracker_status != controller.TrackerStatus.NOT_NOTIFIED:
            print("[P2T] tracker status: %s" % self.tracker_status)
            return
        self.tracker_conn.notify(self.local_addr)

    def add_torrent(self, torrent: Torrent):
        self.torrent_list.append(torrent)

    def register_torrent(self, torrent: Torrent):
        self.active_torrents[torrent.torrent_hash] = controller.TorrentController(torrent)
        self.tracker_conn.register(torrent)

    def retrieve_peer_list(self, torrent_hash: str):
        self.tracker_conn.retrieve_peer_lists(torrent_hash)

    def cancel(self, torrent_hash: str):
        if torrent_hash not in self.active_torrents:
            return
        self.active_torrents[torrent_hash].close()
        self.tracker_conn.cancel(torrent_hash)

    def close(self):
        self.tracker_conn.close()
        for con in self.peer_conns:
            self.socket.unregister(con.remote_addr)
        self.socket.close()
