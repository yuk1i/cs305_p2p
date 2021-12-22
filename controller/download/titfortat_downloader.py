import random
import threading
from typing import List, Dict, Set, Tuple

import controller
from conn import P2PConn
from packet.p2p_packet import SetChokeStatus
from utils import IPPort, current_time_ms
from . import AbstractDownloadController


class TitfortatDownloadController(AbstractDownloadController):
    def __init__(self, torrent_ctrl: controller.TorrentController):
        super().__init__(torrent_ctrl)
        self.pending_blocks: Set[int] = set()
        self.pending_peer: Dict[IPPort, Set[int]] = dict()
        self.timeouting_blocks: Dict[int, int] = dict()
        self.MAX_SIMULTANEOUS_REQ = 3
        self.peer_sim_numbers: Dict[IPPort, int] = dict()
        self.peer_sim_numbers_reseter = threading.Timer(10, function=self.reseter)
        self.peer_sim_numbers_reseter.start()
        self.last_time = current_time_ms()
        self.times = 0
        self.unchoking_peers: Set[IPPort] = set()
        self.enable_log = True

    def reseter(self):
        for p in self.peer_list:
            self.peer_sim_numbers[p] = self.MAX_SIMULTANEOUS_REQ

    def on_peer_respond_succeed(self, peer_addr: IPPort, chunk_seq_id: int):
        print(f"[ALG] block {chunk_seq_id} success from {peer_addr}")
        if chunk_seq_id in self.timeouting_blocks:
            del self.timeouting_blocks[chunk_seq_id]
        if chunk_seq_id in self.pending_peer[peer_addr]:
            self.pending_peer[peer_addr].remove(chunk_seq_id)
        if chunk_seq_id in self.pending_blocks:
            self.pending_blocks.remove(chunk_seq_id)

    def on_peer_respond_failed(self, peer_addr: IPPort, chunk_seq_id: int):
        print(f"[ALG] block {chunk_seq_id} failed from {peer_addr}")
        if peer_addr in self.controller.peer_chunk_info:
            self.controller.peer_chunk_info[peer_addr].remove(chunk_seq_id)
        if chunk_seq_id in self.timeouting_blocks:
            del self.timeouting_blocks[chunk_seq_id]
        if chunk_seq_id in self.pending_peer[peer_addr]:
            self.pending_peer[peer_addr].remove(chunk_seq_id)
        if chunk_seq_id in self.pending_blocks:
            self.pending_blocks.remove(chunk_seq_id)

    def on_peer_timeout(self, peer_addr: IPPort, chunk_seq_id: int):
        print(f"[ALG] block {chunk_seq_id} timeout from {peer_addr}")
        self.peer_sim_numbers[peer_addr] = self.MAX_SIMULTANEOUS_REQ - 1
        self.on_peer_respond_failed(peer_addr, chunk_seq_id)
        # self.pending_peer[peer_addr].remove(chunk_seq_id)
        # self.timeouting_blocks[chunk_seq_id] = current_time_ms()
        # self.pending_blocks.remove(chunk_seq_id)
        # Don't remove them from pending_blocks
        # lower down peer_addr's level? but should be done in random alg

    def _set_choking_status(self, peer: IPPort, status: bool):
        # print("peer ", peer, " choking status to ", status)
        conn: P2PConn = self.controller.controller.get_peer_conn(peer)
        conn.notify_choke_status(status)

    def _log(self, s: str):
        # with open('choking_event.log','w') as f:
        #     f.write(s+'\n')
        if self.enable_log:
            print(s)

    def evaluate(self):
        peers = list(self.peer_list)
        aval_peers: List[Tuple[IPPort, int]] = []

        for peer in peers:
            conn: P2PConn = self.controller.controller.get_peer_conn(peer)
            if not conn.choke_status:
                aval_peers.append((peer, conn.traffic_monitor.get_downlink_rate()))

        aval_peers.sort(key=lambda x:x[1], reverse=True)

        new_unchoking_peers: Set[IPPort] = set()
        length = len(aval_peers)

        for i in range(0,min(4, length)):
            new_unchoking_peers.add(aval_peers[i][0])

        peers_on_choking = list(self.unchoking_peers.difference(new_unchoking_peers))
        peers_on_unchoking = list(new_unchoking_peers.difference(self.unchoking_peers))

        self._log("[CP2P, {}] update unchoking list ".format(self.controller.controller.local_addr))
        self._log("old unchoking list: "+ str(list(self.unchoking_peers)))
        self._log("new unchoking list: " + str(list(new_unchoking_peers)))
        for peer in peers_on_unchoking:
            self._log("unchoke "+str(peer))
            self._set_choking_status(peer, False)

        for peer in peers_on_choking:
            self._log("choke "+str(peer))
            self._set_choking_status(peer, True)

        self.unchoking_peers = new_unchoking_peers

    def optimistic_unchoke(self):
        peers = list(self.peer_list)
        choking_peers = [peer for peer in peers if peer not in self.unchoking_peers]
        if not choking_peers:
            return
        peer = random.choice(choking_peers)
        self._set_choking_status(peer, False)

    def get_next_download_task(self) -> List[Tuple[IPPort, List[int]]]:
        wanted = set(range(1, 1 + self.controller.dir_controller.torrent_block_count)) \
            .difference(self.controller.dir_controller.get_local_blocks())
        peers = list(self.peer_list)

        #print("time = ", current_time_ms() - self.last_time)

        if(current_time_ms() - self.last_time >= 10000):
            self.evaluate()
            self.last_time = current_time_ms()
            self.times += 1
            pass

        if(self.times >= 3):
            self.optimistic_unchoke()
            self.times = 0
            pass

        for i in range(len(peers)):
            conn: P2PConn = self.controller.controller.get_peer_conn(peers[i])
            if conn.choke_status:
                del peers[i]

        tasks = list()
        for peer in peers:
            if peer not in self.pending_peer:
                self.on_new_peer(peer)
            if peer not in self.peer_sim_numbers:
                self.peer_sim_numbers[peer] = self.MAX_SIMULTANEOUS_REQ
            if len(self.pending_peer[peer]) >= self.peer_sim_numbers[peer]:
                continue
            want_chunks = wanted.intersection(self.peer_chunk_info[peer].chunks).difference(self.pending_blocks)
            if len(want_chunks) == 0:
                continue
            wants = list()
            for _ in range(self.MAX_SIMULTANEOUS_REQ - len(self.pending_peer[peer])):
                if len(want_chunks) == 0:
                    break
                want_chunk_id = random.choice(list(want_chunks))
                want_chunks.remove(want_chunk_id)
                wanted.remove(want_chunk_id)
                wants.append(want_chunk_id)
                self.pending_blocks.add(want_chunk_id)
                self.pending_peer[peer].add(want_chunk_id)
            tasks.append((peer, wants))
        if tasks:
            print(tasks)
        return tasks

    def on_new_peer(self, peer_addr: IPPort):
        self.pending_peer[peer_addr] = set()
        self.peer_sim_numbers[peer_addr] = self.MAX_SIMULTANEOUS_REQ

    def close(self):
        self.peer_sim_numbers_reseter.cancel()
