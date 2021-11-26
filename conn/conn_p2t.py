from __future__ import annotations

from typing import Tuple, Dict, Set, List

import conn
import controller
from packet.p2t_packet import *
from torrent import Torrent
from utils.bytes_utils import int_to_ipv4, random_long, bytes_to_int, bytes_to_hexstr, ipv4_to_int


class PeerToTrackerConn(conn.Conn):
    def __init__(self, tracker_addr: Tuple[str, int], ctrl: controller.PeerController):
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

    def notify(self, my_addr: Tuple[str, int]):
        notify_req = NotifyPacket()
        notify_req.ipv4_address = ipv4_to_int(my_addr[0])
        notify_req.udp_port = my_addr[1]
        self.controller.tracker_status = controller.TrackerStatus.NOTIFYING
        self.send_request(notify_req, None)

    def register(self, torrent: Torrent):
        pass
