from __future__ import annotations

import threading
from typing import Tuple, Any

import controller
import statistics
from conn import Conn
from packet.p2p_packet import *
from utils import IPPort, hexstr_to_bytes, bytes_to_hexstr
from torrent_local_state import TorrentLocalState


CHECK_ALIVE_INTERVAL = 25


class P2PConn(Conn):
    """
    A peer to peer Connection
    """

    def __init__(self, peer_addr: IPPort, ctrl: controller.PeerController):
        super(P2PConn, self).__init__(peer_addr, ctrl)
        self.remote_keep_alive = True
        self.remote_keep_alive_signal = False
        self.remote_keep_alive_timer = threading.Timer(interval=CHECK_ALIVE_INTERVAL, function=self.check_alive)
        self.remote_keep_alive_timer.daemon = True
        self.remote_keep_alive_timer.start()

    def __handler__(self, pkt: BasePacket):
        self.controller: controller.PeerController
        # TODO: Handle requests and replies here
        if pkt.type == TYPE_ACK:
            req_type = pkt.reserved & MASK_RESERVED
            state = self.retrieve_state(pkt.identifier)
            if req_type == TYPE_REQUEST_TORRENT:
                print("[CP2P, {}] Torrent data available, from {}".format(self.controller.local_addr, self.remote_addr))
                pkt: ACKRequestForTorrent
                torrent_hash: str = state
                if pkt.status == STATUS_OK and torrent_hash in self.controller.active_torrents:
                    self.remote_keep_alive_signal = True
                    self.controller.active_torrents[torrent_hash]. \
                        on_torrent_chunk_received(pkt.data, pkt.start_at, pkt.length, pkt.total_length)
            elif req_type == TYPE_UPDATE_CHUNK_INFO:
                print("[CP2P] ACKED Chunk Info")
                pkt: ACKUpdateChunkInfo
                torrent_hash: str = state
                if pkt.status == STATUS_OK and torrent_hash in self.controller.active_torrents:
                    self.remote_keep_alive_signal = True
                    tc = self.controller.active_torrents[torrent_hash]
                    tc.on_peer_chunk_updated(self.remote_addr, TorrentLocalState.unpack_seq_ids(pkt.packed_seq_ids))
            elif req_type == TYPE_REQUEST_CHUNK:
                pkt: ACKRequestChunk
                if not state:
                    print("ERROR!!!!!! WHY state is None!!!!!!")
                    state = ('1')
                torrent_hash: str = state[0]
                return_status = controller.torrent_controller.PEER_RSPD_SUCCEED
                if torrent_hash in self.controller.active_torrents:
                    tc = self.controller.active_torrents[torrent_hash]
                    if pkt.status == STATUS_OK:
                        if tc.dir_controller.check_chunk_hash(pkt.chunk_seq_id, pkt.data):
                            self.remote_keep_alive_signal = True
                            print(
                                "[CP2P, {}] Save Block {} from {}".format(self.controller.local_addr, pkt.chunk_seq_id,
                                                                          self.remote_addr))
                            tc.dir_controller.save_block(pkt.chunk_seq_id, pkt.data)
                            statistics.get_instance().on_peer_new_chunk(self.controller.local_addr[1], pkt.chunk_seq_id,
                                                                        self.remote_addr[1])
                        else:
                            print("chunk hash failed for id %s" % pkt.chunk_seq_id)
                            return_status = controller.torrent_controller.PEER_RSPD_FAILED
                    elif pkt.status == STATUS_NOT_READY:
                        tc.peer_chunk_info[self.remote_addr].remove(pkt.chunk_seq_id)
                        print("[CP2P, {}] Remote {} declares not ready for part {}".format(self.controller.local_addr,
                                                                                           self.remote_addr,
                                                                                           pkt.chunk_seq_id))
                        return_status = controller.torrent_controller.PEER_RSPD_FAILED
                    elif pkt.status == STATUS_NOT_ENOUGH_UPLOAD:
                        return_status = controller.torrent_controller.PEER_RSPD_NO_UPLOAD_BANDWITH
                    tc.on_peer_respond_chunk_req(self.remote_addr, return_status, pkt.chunk_seq_id)
            self.notify_lock(req_type)
        else:
            # Request
            # Receive other peers' request
            req_type = pkt.type
            if req_type == TYPE_REQUEST_TORRENT:
                print("[CP2P, {}] {} is requesting torrent data".format(self.controller.local_addr, self.remote_addr))
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
                if self.controller.active_torrents[str_hash].torrent.dummy:
                    ack.status = STATUS_NOT_READY
                    self.send_packet(ack)
                    return
                # I have this torrent
                ack.status = STATUS_OK
                bdata = self.controller.active_torrents[str_hash].torrent.binary
                start = min(len(bdata), pkt.since)
                end = min(len(bdata), pkt.since + pkt.expectedLength)
                bdata = bdata[start:end]
                ack.data = bdata
                ack.start_at = start
                ack.length = end - start
                ack.total_length = len(bdata)
                self.send_packet(ack)
            elif req_type == TYPE_UPDATE_CHUNK_INFO:
                print("[CP2P, {}] {} is requesting chunk info".format(self.controller.local_addr, self.remote_addr))
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
                my_set = tc.dir_controller.get_local_blocks()
                if tc.upload_mode == controller.MODE_DONT_REPEAT:
                    my_set = my_set.difference(tc.uploaded)
                ack.packed_seq_ids = TorrentLocalState.pack_seq_ids(my_set)
                self.send_packet(ack)
            elif req_type == TYPE_REQUEST_CHUNK:
                pkt: RequestChunk
                str_hash = bytes_to_hexstr(pkt.torrent_hash)
                ack = ACKRequestChunk()
                ack.set_request(pkt)
                ack.chunk_seq_id = pkt.chunk_seq_id
                if str_hash not in self.controller.active_torrents:
                    ack.status = STATUS_NOT_FOUND
                    self.send_packet(ack)
                    return
                tc = self.controller.active_torrents[str_hash]
                if self.remote_addr not in tc.peer_list:
                    tc.on_new_income_peer(self.remote_addr)
                if tc.slow_mode and self.controller.socket.traffic_monitor.get_uplink_rate() >= self.controller.socket.proxy.upload_rate * 0.97:
                    ack.status = STATUS_NOT_ENOUGH_UPLOAD
                    print(f"[CP2P, {self.controller.local_addr}] Not Enough Bandwidth for {self.remote_addr}")
                    self.send_packet(ack)
                    return
                if tc.upload_mode == controller.MODE_DONT_REPEAT:
                    if pkt.chunk_seq_id in tc.uploaded:
                        print("[CP2P, {}] Bdata Not Ready for {}, from {}, since uploaded already".format(
                            self.controller.local_addr, pkt.chunk_seq_id, self.remote_addr))
                        ack.status = STATUS_NOT_READY
                        self.send_packet(ack)
                        return
                    else:
                        tc.uploaded.add(pkt.chunk_seq_id)
                bdata = tc.dir_controller.retrieve_block(pkt.chunk_seq_id)
                if not bdata:
                    print("[CP2P, {}] Bdata Not Ready for {}, from {}".format(self.controller.local_addr,
                                                                              pkt.chunk_seq_id, self.remote_addr))
                    ack.status = STATUS_NOT_READY
                    self.send_packet(ack)
                    return
                ack.status = STATUS_OK
                ack.data = bdata
                self.send_packet(ack)
            elif req_type == TYPE_SET_CHOKE_STATUS:
                pkt: SetChokeStatus
                str_hash = bytes_to_hexstr(pkt.torrent_hash)
                tc: controller.TorrentController = self.controller.active_torrents[str_hash]
                tc.on_peer_choke_status_change(self.remote_addr, pkt.choke_status)

    def __on_timeout__(self, itype: int, identifier: int, state: Any):
        if itype == TYPE_REQUEST_CHUNK:
            torrent_hash, block_seq = state
            self.controller: controller.PeerController
            if torrent_hash in self.controller.active_torrents:
                self.controller.active_torrents[torrent_hash].on_chunk_timeout(self.remote_addr, block_seq)

    def close(self):
        self.active = False
        self.remote_keep_alive_timer.cancel()
        super(P2PConn, self).close()

    def check_alive(self):
        if self.active:
            print(f'check {self.remote_keep_alive} {self.remote_keep_alive_signal}')
            if self.remote_keep_alive and not self.remote_keep_alive_signal:
                self.remote_keep_alive = False
                print(f'peer {self.remote_addr} kept quiet for too long')
            if not self.remote_keep_alive and self.remote_keep_alive_signal:
                self.remote_keep_alive = True
                print(f'peer {self.remote_addr} comes back')
        self.remote_keep_alive_signal = False
        self.remote_keep_alive_timer = threading.Timer(interval=25, function=self.check_alive)
        self.remote_keep_alive_timer.daemon = True
        self.remote_keep_alive_timer.start()

    def last_active(self):
        """
        Return time passed after last communication
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

    def async_request_chunk(self, torrent_hash: str, block_seq: int):
        req = RequestChunk()
        req.torrent_hash = hexstr_to_bytes(torrent_hash)
        req.chunk_seq_id = block_seq
        self.send_request(req, (torrent_hash, block_seq), False)

    def notify_choke_status(self, torrent_hash: str, status: bool):
        pkt: SetChokeStatus = SetChokeStatus()
        pkt.torrent_hash = hexstr_to_bytes(torrent_hash)
        pkt.choke_status = status
        self.send_packet(pkt)
