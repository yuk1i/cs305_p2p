from __future__ import annotations

import threading
from typing import Tuple, Dict, List, Set

import conn
import Proxy
import controller
from torrent import Torrent
from utils import IPPort
from utils.bytes_utils import random_long, bytes_to_int


class PeerController(controller.Controller):
    def __init__(self, pxy: Proxy.Proxy, my_addr: IPPort, tracker_addr: IPPort):
        super(PeerController, self).__init__(pxy)
        self.active = True
        self.local_addr = my_addr
        self.active_torrents: Dict[str, controller.TorrentController] = dict()
        self.peer_conns: Dict[IPPort, conn.P2PConn] = dict()
        self.tracker_addr = tracker_addr
        self.tracker_conn: conn.PeerToTrackerConn = conn.PeerToTrackerConn(self.tracker_addr, self)
        self.tracker_status: int = controller.TrackerStatus.NOT_NOTIFIED
        self.tracker_uuid: int = 0
        self.keep_alive_timer: threading.Timer = None
        self.keep_alive_thread: threading.Thread = threading.Thread(target=self.keep_alive)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()

    def accept_conn(self, src_addr: IPPort) -> conn.Conn:
        con = conn.P2PConn(src_addr, self)
        self.peer_conns[src_addr] = con
        return con

    def notify_tracker(self):
        if self.tracker_status != controller.TrackerStatus.NOT_NOTIFIED:
            print("[P2T] tracker status: %s" % self.tracker_status)
            return
        self.tracker_conn.notify(self.local_addr)

    def register_torrent(self, torrent: Torrent, torrent_file_path: str, save_dir: str, tit_tat=False) -> controller.TorrentController:
        torrent_hash = torrent.torrent_hash
        if torrent_hash in self.active_torrents:
            return self.active_torrents[torrent_hash]
        self.active_torrents[torrent_hash] = controller.TorrentController(torrent, self, save_dir, torrent_file_path, tit_tat)
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

    def start_download(self, torrent_hash: str):
        self.active_torrents[torrent_hash].start_download()

    def stop_torrent(self, torrent_hash: str):
        self.active_torrents[torrent_hash].close()
        del self.active_torrents[torrent_hash]

    def create_peer_conn(self, peer_addr: IPPort):
        if peer_addr not in self.peer_conns:
            self.peer_conns[peer_addr] = conn.P2PConn(peer_addr, self)

    def get_peer_conn(self, peer_addr: IPPort) -> conn.P2PConn:
        if peer_addr in self.peer_conns:
            return self.peer_conns[peer_addr]
        else:
            return None

    def keep_alive(self):
        while self.active:
            while self.tracker_status == controller.TrackerStatus.NOTIFIED:
                self.keep_alive_timer = threading.Timer(interval=25, function=self.tracker_conn.notify,
                                                        args=(self.local_addr,))
                # self.keep_alive_timer.daemon = True
                self.keep_alive_timer.start()
                self.keep_alive_timer.join()

    def close(self):
        for active in self.active_torrents.values():
            active.close()
        self.tracker_conn.close()
        self.active = False
        if self.keep_alive_timer:
            self.keep_alive_timer.cancel()
        self.keep_alive_thread.join()
        for con in self.peer_conns.values():
            con.close()
        self.socket.close()
