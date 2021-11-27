from __future__ import annotations

from typing import Tuple, Dict, Set, List

import conn
import controller
from packet.p2t_packet import *
from torrent import Torrent
from utils.bytes_utils import int_to_ipv4, random_long, bytes_to_int, bytes_to_hexstr, ipv4_to_int, hexstr_to_bytes


class PeerToTrackerConn(conn.Conn):
    def __init__(self, tracker_addr: IPPort, ctrl: controller.PeerController):
        super(PeerToTrackerConn, self).__init__(tracker_addr, ctrl)
        pass

    def __handler__(self, pkt: BasePacket):
        self.controller: controller.PeerController
        if pkt.type == TYPE_ACK:
            req_type = pkt.reversed & MASK_REVERSED
            state = self.retrieve_state(pkt.identifier)
            if req_type == TYPE_NOTIFY:
                pkt: ACKNotifyPacket
                self.controller.tracker_status = controller.TrackerStatus.NOTIFIED
                self.controller.tracker_uuid = pkt.uuid
            elif req_type == TYPE_REGISTER:
                pkt: ACKRegisterPacket
                torrent_hash: str = state
                print("[Conn P2T] Recv ACK for Reg")
                if pkt.status == STATUS_OK and torrent_hash in self.controller.active_torrents.keys():
                    self.controller.active_torrents[
                        torrent_hash].status = controller.TorrentStatus.TORRENT_STATUS_REGISTERED

    def notify(self, my_addr: IPPort):
        notify_req = NotifyPacket()
        notify_req.ipv4_address = ipv4_to_int(my_addr[0])
        notify_req.udp_port = my_addr[1]
        self.controller.tracker_status = controller.TrackerStatus.NOTIFYING
        self.send_request(notify_req, None)

    def register(self, torrent: Torrent):
        self.controller: controller.PeerController
        req = RegisterPacket()
        req.torrent_hash = hexstr_to_bytes(torrent.torrent_hash)
        req.uuid = self.controller.tracker_uuid
        self.send_request(req, torrent.torrent_hash)
