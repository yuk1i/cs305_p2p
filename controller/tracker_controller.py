from typing import Tuple, Dict, List, Set

import conn
import proxy
import controller
from utils.bytes_utils import random_long, bytes_to_int


class TrackerController(controller.Controller):
    def __init__(self, pxy: proxy.Proxy):
        super(TrackerController, self).__init__(pxy)
        self.peer_list: Dict[int, Tuple[str, int]] = dict()
        # peer_list maps a UUID to peer_addr
        self.rev_peer_list: Dict[Tuple[str, int], int] = dict()
        # rev_peer_list maps a peer_addr to a UUID
        self.torrents: Dict[str, Set[Tuple[str, int]]] = dict()
        # torrents maps a torrent_hash to a peer_addr list indicating who has this torrent_hash

    def accept_conn(self, src_addr: Tuple[str, int]) -> conn.Conn:
        super(TrackerController, self).accept_conn(src_addr)
        con = conn.TrackerConn(src_addr, self)
        return con

    def create_conn(self, target_addr: Tuple[str, int]) -> conn.Conn:
        return super().create_conn(target_addr)

    def get_peer(self, uuid: int) -> Tuple[str, int]:
        return self.peer_list[uuid]

    def new_peer(self, peer_addr: Tuple[str, int]) -> int:
        if self.rev_peer_list[peer_addr]:
            return self.rev_peer_list[peer_addr]
        uuid = bytes_to_int(random_long())
        self.peer_list[uuid] = peer_addr
        self.rev_peer_list[peer_addr] = uuid
        return uuid

    def remove_peer(self, uuid):
        addr = self.peer_list[uuid]
        del self.rev_peer_list[addr]
        del self.peer_list[uuid]

    def peer_exist(self, uuid: int) -> bool:
        return self.peer_list[uuid] is not None

    def register_torrent(self, uuid: int, torrent_hash: str) -> bool:
        if not self.peer_exist(uuid):
            return False
        if not self.torrents[torrent_hash]:
            self.torrents[torrent_hash] = set()
            print("[Tracker] New Torrent %s" % torrent_hash)
        if self.get_peer(uuid) in self.torrents[torrent_hash]:
            return True
        self.torrents[torrent_hash].add(self.get_peer(uuid))
        print("[Tracker] Peer {} join torrent {}".format(self.get_peer(uuid), torrent_hash))
        return True
