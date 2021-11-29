from __future__ import annotations

from typing import Tuple

import controller
from conn import Conn
from packet.p2p_packet import *
from utils import IPPort


class P2PConn(Conn):
    """
    A peer to peer Connection
    """

    def __init__(self, peer_addr: IPPort, ctrl: controller.PeerController):
        super(P2PConn, self).__init__(peer_addr, ctrl)

    def __handler__(self, pkt: BasePacket):
        self.controller: controller.PeerController
        if pkt.type == TYPE_ACK:
            pass
        else:
            # Request
            pass

    def last_active(self):
        """
        Return time passed after last communication
        :return:
        """
        pass

    def uplink_speed(self) -> int:
        """
        Get uplink speed in byte/s
        :return:
        """
        pass

    def downlink_speed(self) -> int:
        """
        Get download speed in byte/s
        :return:
        """
        pass
