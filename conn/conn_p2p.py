from __future__ import annotations

from typing import Tuple

import controller
from conn import Conn
from packet.p2p_packet import *
from utils import IPPort, hexstr_to_bytes, bytes_to_hexstr


class P2PConn(Conn):
    """
    A peer to peer Connection
    """

    def __init__(self, peer_addr: IPPort, ctrl: controller.PeerController):
        super(P2PConn, self).__init__(peer_addr, ctrl)

    def __handler__(self, pkt: BasePacket):
        self.controller: controller.PeerController
        # TODO: Handle requests and replies here
        if pkt.type == TYPE_ACK:
            req_type = pkt.reversed & MASK_REVERSED
            state = self.retrieve_state(pkt.identifier)
            if req_type == TYPE_REQUEST_TORRENT:
                print("[CP2P] Torrent data available")
                pkt: ACKRequestForTorrent
                torrent_hash: str = state
                if pkt.status == STATUS_OK and torrent_hash in self.controller.active_torrents:
                    self.controller.active_torrents[torrent_hash]. \
                        on_torrent_chunk_received(pkt.data, pkt.start_at, pkt.length, pkt.total_length)
            self.notify_lock(req_type)
        else:
            # Request
            # Receive other peers' request
            req_type = pkt.type
            if req_type == TYPE_REQUEST_TORRENT:
                print("[CP2P] Other is requesting torrent data")
                pkt: RequestForTorrent
                str_hash = bytes_to_hexstr(pkt.torrent_hash)
                ack = ACKRequestForTorrent()
                ack.set_request(pkt)
                if str_hash not in self.controller.active_torrents:
                    ack.status = STATUS_NOT_FOUND
                    self.send_packet(ack)
                    return
                if self.remote_addr not in self.controller.active_torrents[str_hash].peer_list:
                    self.controller.active_torrents[str_hash].peer_list.append(self.remote_addr)
                    self.controller.active_torrents[str_hash].on_new_income_peer(self.remote_addr)
                if not self.controller.active_torrents[str_hash].__torrent_content_filled__:
                    ack.status = STATUS_NOT_READY
                    self.send_packet(ack)
                    return
                # I have this torrent
                ack.status = STATUS_OK
                bdata = self.controller.active_torrents[str_hash].torrent.__binary__
                start = min(len(bdata), pkt.since)
                end = min(len(bdata), pkt.since + pkt.expectedLength)
                bdata = bdata[start:end]
                ack.data = bdata
                ack.start_at = start
                ack.length = end - start
                ack.total_length = len(bdata)
                self.send_packet(ack)
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

    def request_torrent_chunk(self, torrent_hash: str, start: int = 0, end: int = 0xFFFFFFFF) -> bool:
        req = RequestForTorrent()
        req.torrent_hash = hexstr_to_bytes(torrent_hash)
        req.since = start
        req.expectedLength = end
        self.send_request(req, torrent_hash, True)
        return self.wait(req.type, 3)
        # Wait 3 seconds for reply
