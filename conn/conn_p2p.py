from __future__ import annotations

from typing import Tuple

import controller
from conn import Conn
from packet.p2p_packet import *
from utils import IPPort, hexstr_to_bytes, bytes_to_hexstr
from torrent_local_state import TorrentLocalState


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
            elif req_type == TYPE_UPDATE_CHUNK_INFO:
                print("[CP2P] ACKED Chunk Info")
                pkt: ACKUpdateChunkInfo
                torrent_hash: str = state
                if pkt.status == STATUS_OK and torrent_hash in self.controller.active_torrents:
                    tc = self.controller.active_torrents[torrent_hash]
                    tc.on_peer_chunk_updated(self.remote_addr, TorrentLocalState.unpack_seq_ids(pkt.packed_seq_ids))
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
                    self.controller.active_torrents[str_hash].on_new_income_peer(self.remote_addr)
                if not self.controller.active_torrents[str_hash].torrent_binary_filled:
                    ack.status = STATUS_NOT_READY
                    self.send_packet(ack)
                    return
                # I have this torrent
                ack.status = STATUS_OK
                bdata = self.controller.active_torrents[str_hash].torrent.generate_binary()
                start = min(len(bdata), pkt.since)
                end = min(len(bdata), pkt.since + pkt.expectedLength)
                bdata = bdata[start:end]
                ack.data = bdata
                ack.start_at = start
                ack.length = end - start
                ack.total_length = len(bdata)
                self.send_packet(ack)
            elif req_type == TYPE_UPDATE_CHUNK_INFO:
                print("[CP2P] Other is requesting chunk info")
                pkt: UpdateChunkInfo
                str_hash = bytes_to_hexstr(pkt.torrent_hash)
                ack = ACKUpdateChunkInfo()
                ack.set_request(pkt)
                if str_hash not in self.controller.active_torrents:
                    ack.status = STATUS_NOT_FOUND
                    self.send_packet(ack)
                    return
                remote_chunks = TorrentLocalState.unpack_seq_ids(pkt.packed_seq_ids)
                tc = self.controller.active_torrents[str_hash]
                if self.remote_addr not in tc.peer_list:
                    tc.on_new_income_peer(self.remote_addr)
                tc.on_peer_chunk_updated(self.remote_addr, remote_chunks)
                if tc.dir_controller is None:
                    ack.status = STATUS_NOT_READY
                    self.send_packet(ack)
                    return
                ack.status = STATUS_OK
                ack.packed_seq_ids = TorrentLocalState.pack_seq_ids(tc.dir_controller.local_state.local_block)
                self.send_packet(ack)

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

    def async_update_chunk_info(self, torrent_hash: str, my_block: Set[int]):
        req = UpdateChunkInfo()
        req.torrent_hash = hexstr_to_bytes(torrent_hash)
        req.packed_seq_ids = TorrentLocalState.pack_seq_ids(my_block)
        self.send_request(req, torrent_hash, False)
