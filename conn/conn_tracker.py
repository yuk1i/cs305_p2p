from __future__ import annotations
from typing import Tuple, Dict, Set, List

import conn
import controller
from packet.p2t_packet import *
from utils.bytes_utils import int_to_ipv4, random_long, bytes_to_int, bytes_to_hexstr


class TrackerConn(conn.Conn):
    def __init__(self, peer_addr: IPPort, ctrl: controller.TrackerController):
        super(TrackerConn, self).__init__(peer_addr, ctrl)
        pass

    def __handler__(self, pkt: BasePacket):
        self.controller: controller.TrackerController
        if pkt.type == TYPE_NOTIFY:
            pkt: NotifyPacket  # make IDE happy
            peer_addr: IPPort = (int_to_ipv4(pkt.ipv4_address), pkt.udp_port)
            uuid = self.controller.new_peer(peer_addr)
            print("[Tracker] Recv Notify from {}, return uuid {}".format(peer_addr, uuid))
            ack = ACKNotifyPacket()
            ack.set_request(pkt)
            ack.uuid = uuid
            self.send_packet(ack)
        elif pkt.type == TYPE_REGISTER:
            pkt: RegisterPacket
            ack = ACKRegisterPacket()
            ack.set_request(pkt)
            if self.controller.register_torrent(pkt.uuid, bytes_to_hexstr(pkt.torrent_hash)):
                ack.status = STATUS_OK
            else:
                ack.status = STATUS_NO_AUTH
            self.send_packet(ack)
        elif pkt.type == TYPE_CANCEL:
            pkt: CancelPacket
            ack = ACKCancelPacket()
            ack.set_request(pkt)
            if self.controller.cancel_torrent(pkt.uuid, bytes_to_hexstr(pkt.torrent_hash)):
                ack.status = STATUS_OK
            else:
                ack.status = STATUS_NO_AUTH
            self.send_packet(ack)
        elif pkt.type == TYPE_CLOSE:
            pkt: ClosePacket
            ack = ACKClosePacket()
            ack.set_request(pkt)
            if self.controller.peer_exist(pkt.uuid):
                self.controller.remove_peer(pkt.uuid)
            ack.status = STATUS_OK
            self.send_packet(ack)
        elif pkt.type == TYPE_REQUEST_PEERS:
            pkt: RequestPeerPacket
            ack = ACKRequestPeerPacket()
            ack.set_request(pkt)
            ack.status = STATUS_OK
            ack.addresses.extend(self.controller.torrents[bytes_to_hexstr(pkt.torrent_hash)])
            ack.status = STATUS_OK
            self.send_packet(ack)
