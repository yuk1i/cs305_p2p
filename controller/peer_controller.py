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
        self.active_torrents: Dict[str, controller.TorrentController] = dict()
        self.peer_conns: Dict[IPPort, conn.P2PConn] = dict()
        self.tracker_addr = tracker_addr
        self.tracker_conn: conn.PeerToTrackerConn = conn.PeerToTrackerConn(self.tracker_addr, self)
        self.tracker_status: int = controller.TrackerStatus.NOT_NOTIFIED
        self.tracker_uuid: int = 0

    def accept_conn(self, src_addr: IPPort) -> conn.Conn:
        con = conn.P2PConn(src_addr, self)
        self.peer_conns[src_addr] = con
        return con

    def notify_tracker(self):
        if self.tracker_status != controller.TrackerStatus.NOT_NOTIFIED:
            print("[P2T] tracker status: %s" % self.tracker_status)
            return
        self.tracker_conn.notify(self.local_addr)

    def register_torrent(self, torrent: Torrent, torrent_file_path: str, save_dir: str) -> controller.TorrentController:
        torrent_hash = torrent.torrent_hash
        if torrent_hash in self.active_torrents:
            return self.active_torrents[torrent_hash]
        self.active_torrents[torrent_hash] = controller.TorrentController(torrent, self, save_dir, torrent_file_path)
        self.tracker_conn.register(torrent_hash)
        return self.active_torrents[torrent_hash]

    def retrieve_peer_list(self, torrent_hash: str):
        self.tracker_conn.retrieve_peer_lists(torrent_hash)

    def cancel(self, torrent_hash: str):
        if torrent_hash not in self.active_torrents:
            return
        self.active_torrents[torrent_hash].close()
        self.tracker_conn.cancel(torrent_hash)
        del self.active_torrents[torrent_hash]

    def close_from_tracker(self):
        for active in self.active_torrents.values():
            active.close()
        self.tracker_conn.close_from_tracker()

    def start_download(self, torrent_hash: str, save_dir: str, torrent_file_path: str):
        self.active_torrents[torrent_hash].start_download(save_dir, torrent_file_path)

    def create_peer_conn(self, peer_addr: IPPort):
        if peer_addr not in self.peer_conns:
            self.peer_conns[peer_addr] = conn.P2PConn(peer_addr, self)

    def get_peer_conn(self, peer_addr: IPPort) -> conn.P2PConn:
        if peer_addr in self.peer_conns:
            return self.peer_conns[peer_addr]
        else:
            return None

    def close(self):
        self.tracker_conn.close()
        for con in self.peer_conns.values():
            con.close()
        self.socket.close()
