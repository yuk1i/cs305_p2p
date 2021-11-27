from __future__ import annotations

from typing import Tuple, Dict, List, Set

import conn
import proxy
import controller
from utils import IPPort
from utils.bytes_utils import random_long, bytes_to_int


class TrackerController(controller.Controller):
    def __init__(self, pxy: proxy.Proxy):
        super(TrackerController, self).__init__(pxy)
        self.peers: List[Tuple[int, IPPort]] = list()
        # peer_list maps a UUID to peer_addr
        self.torrents: Dict[str, Set[IPPort]] = dict()
        self.conns: List[conn.Conn] = list()
        # torrents maps a torrent_hash to a peer_addr list indicating who has this torrent_hash

    def accept_conn(self, src_addr: IPPort) -> conn.Conn:
        super(TrackerController, self).accept_conn(src_addr)
        con = conn.TrackerConn(src_addr, self)
        self.conns.append(con)
        return con

    def create_conn(self, target_addr: IPPort) -> conn.Conn:
        return super().create_conn(target_addr)

    def peer_exist(self, uuid: int) -> bool:
        return self.get_peer(uuid=uuid) is not None

    def get_peer(self, uuid: int = -1, addr: IPPort = None) -> Tuple[int, IPPort]:
        """
        get peer addr
        :param uuid: peer uuid
        :param addr: peer addr
        :return:
        """
        for tp in self.peers:
            if tp[0] == uuid or tp[1] == addr:
                return tp[0], tp[1]
        return None, None

    def new_peer(self, peer_addr: IPPort) -> int:
        """
        create or retrieve an existing peer, return uuid
        :param peer_addr: peer addr
        :return: peer uuid
        """
        uuid, existing = self.get_peer(addr=peer_addr)
        if uuid:
            return uuid
        uuid = bytes_to_int(random_long())
        self.peers.append((uuid, peer_addr))
        return uuid

    def remove_peer(self, uuid):
        _, addr = self.get_peer(uuid=uuid)
        self.peers.remove((uuid, addr))

    def register_torrent(self, uuid: int, torrent_hash: str) -> bool:
        if not self.peer_exist(uuid):
            return False
        if torrent_hash not in self.torrents.keys():
            self.torrents[torrent_hash] = set()
            print("[Tracker] New Torrent %s" % torrent_hash)
        if self.get_peer(uuid) in self.torrents[torrent_hash]:
            return True
        self.torrents[torrent_hash].add(self.get_peer(uuid)[1])
        print("[Tracker] Peer {} join torrent {}".format(self.get_peer(uuid), torrent_hash))
        return True

    def cancel_torrent(self, uuid: int, torrent_hash: str) -> bool:
        if not self.peer_exist(uuid):
            return False
        if torrent_hash not in self.torrents.keys():
            return True
        _, addr = self.get_peer(uuid)
        if addr not in self.torrents[torrent_hash]:
            return True
        self.torrents[torrent_hash].remove(addr)
        print("[Tracker] Peer {} cancel torrent {}".format(addr, torrent_hash))

    def close(self):
        for con in self.conns:
            con.close()
        self.socket.close()
