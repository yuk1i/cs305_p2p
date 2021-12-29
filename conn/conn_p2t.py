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
            req_type = pkt.reserved & MASK_RESERVED
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
            elif req_type == TYPE_REQUEST_PEERS:
                pkt: ACKRequestPeerPacket
                torrent_hash: str = state
                if torrent_hash in self.controller.active_torrents and pkt.status == STATUS_OK:
                    self.controller.active_torrents[torrent_hash].on_peer_list_update(pkt.addresses)
            elif req_type == TYPE_CANCEL:
                pkt: ACKCancelPacket
                torrent_hash: str = state
                if torrent_hash in self.controller.active_torrents:
                    self.controller.active_torrents[
                        torrent_hash].status = controller.TorrentStatus.TORRENT_STATUS_CANCELED
            elif req_type == TYPE_CLOSE:
                self.controller.tracker_status = controller.TrackerStatus.NOT_NOTIFIED
            self.notify_lock(req_type)

    def close(self):
        self.close_from_tracker()
        super(PeerToTrackerConn, self).close()
        # self.active = False
        # super(PeerToTrackerConn).close()

    def notify(self, my_addr: IPPort):
        notify_req = NotifyPacket()
        notify_req.ipv4_address = ipv4_to_int(my_addr[0])
        notify_req.udp_port = my_addr[1]
        self.controller.tracker_status = controller.TrackerStatus.NOTIFYING
        self.send_request(notify_req, None, True)
        self.wait(notify_req.type)

    def register(self, torrent_hash: str):
        self.controller: controller.PeerController
        req = RegisterPacket()
        req.torrent_hash = hexstr_to_bytes(torrent_hash)
        req.uuid = self.controller.tracker_uuid
        self.send_request(req, torrent_hash, True)
        self.wait(req.type)

    def retrieve_peer_lists(self, torrent_hash: str):
        # Blocking wait for peer lists
        self.controller: controller.PeerController
        req = RequestPeerPacket()
        req.torrent_hash = hexstr_to_bytes(torrent_hash)
        self.send_request(req, torrent_hash, True)
        self.wait(req.type)

    def cancel(self, torrent_hash: str):
        self.controller: controller.PeerController
        req = CancelPacket()
        req.uuid = self.controller.tracker_uuid
        req.torrent_hash = hexstr_to_bytes(torrent_hash)
        self.send_request(req, torrent_hash, True)
        self.wait(req.type)

    def close_from_tracker(self):
        self.controller: controller.PeerController
        req = ClosePacket()
        req.uuid = self.controller.tracker_uuid
        self.send_request(req, None, True)
        self.wait(req.type)
