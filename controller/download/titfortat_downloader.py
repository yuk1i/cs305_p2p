import random
import threading
from typing import List, Dict, Set, Tuple

import controller
import statistics
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
        self.peer_sim_numbers_reseter.daemon = True
        self.peer_sim_numbers_reseter.start()
        self.last_time = current_time_ms() + random.randint(-3000, 3000)
        self.times = 0
        self.unchoking_peers: Set[IPPort] = set()
        self.enable_log = True
        self.choked_by_peers: Set[IPPort] = set()
        self.stamp = current_time_ms()
        self.speed_test:  Dict[IPPort, List[int]] = dict()

    def reseter(self):
        try:
            for p in self.peer_list:
                self.peer_sim_numbers[p] = min(self.MAX_SIMULTANEOUS_REQ, self.peer_sim_numbers[p] + 1)
                self.peer_sim_numbers_reseter = threading.Timer(10, function=self.reseter)
                self.peer_sim_numbers_reseter.daemon = True
                self.peer_sim_numbers_reseter.start()
        except KeyError:
            pass

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

    def on_peer_choke_status_change(self, peer: IPPort, choke_status: bool):

        log: str = ("before " + str(self.choked_by_peers)) + '\n'
        if choke_status:
            self.choked_by_peers.add(peer)
            statistics.get_instance().set_peer_status2(self.controller.controller.local_addr[1], peer[1], "Choking")
        else:
            if peer in self.choked_by_peers:
                self.choked_by_peers.remove(peer)
            statistics.get_instance().set_peer_status2(self.controller.controller.local_addr[1], peer[1], "Unchoking")

        log += ("after " + str(self.choked_by_peers)) + '\n'
        self._log("choked by peers updating ", log)

    def on_peer_timeout(self, peer_addr: IPPort, chunk_seq_id: int):
        print(f"[ALG] block {chunk_seq_id} timeout from {peer_addr}")
        self.peer_sim_numbers[peer_addr] = 1
        self.on_peer_respond_failed(peer_addr, chunk_seq_id)
        # self.pending_peer[peer_addr].remove(chunk_seq_id)
        # self.timeouting_blocks[chunk_seq_id] = current_time_ms()
        # self.pending_blocks.remove(chunk_seq_id)
        # Don't remove them from pending_blocks
        # lower down peer_addr's level? but should be done in random alg

    def _set_choking_status(self, peer: IPPort, status: bool):
        # print("peer ", peer, " choking status to ", status)
        conn: P2PConn = self.controller.controller.get_peer_conn(peer)
        conn.notify_choke_status(self.controller.torrent_hash, status)
        if status:
            statistics.get_instance().set_peer_status(self.controller.controller.local_addr[1], peer[1], "Choked")
        else:
            statistics.get_instance().set_peer_status(self.controller.controller.local_addr[1], peer[1], "Unchoked")

    def _log(self, event: str, s: str):
        # with open('choking_event.log','w') as f:
        #     f.write(s+'\n')
        log: str = ("[CP2P, {}] {} ".format(self.controller.controller.local_addr, event)) + '\n'
        log += s
        if self.enable_log:
            print(log)

    def evaluate(self):
        peers = list(self.peer_list)
        aval_peers: List[Tuple[IPPort, int]] = []

        for peer in peers:
            if peer not in self.choked_by_peers:
                speed: int
                if peer in self.speed_test and len(self.speed_test[peer]) > 0:
                    speed = int(sum(self.speed_test[peer])/len(self.speed_test[peer]))
                    self.speed_test.clear()
                else:
                    speed = self.controller.controller.get_peer_conn(peer).traffic_monitor.get_downlink_rate()
                aval_peers.append(
                    (peer, speed))

        aval_peers.sort(key=lambda x: x[1], reverse=True)

        new_unchoking_peers: Set[IPPort] = set()
        length = len(aval_peers)

        for i in range(0, min(4, length)):
            new_unchoking_peers.add(aval_peers[i][0])

        peers_on_choking = list(self.unchoking_peers.difference(new_unchoking_peers))
        peers_on_unchoking = list(new_unchoking_peers.difference(self.unchoking_peers))

        log: str = ''
        log += ("old unchoking list: " + str(list(self.unchoking_peers))) + '\n'
        log += ("new unchoking list: " + str(list(new_unchoking_peers))) + '\n'
        for peer in peers_on_unchoking:
            log += ("unchoke " + str(peer)) + '\n'
            self._set_choking_status(peer, False)

        for peer in peers_on_choking:
            log += ("choke " + str(peer)) + '\n'
            self._set_choking_status(peer, True)

        self._log(" update unchoking list ", log)

        self.unchoking_peers = new_unchoking_peers

    def optimistic_unchoke(self):
        peers = list(self.peer_list)
        choking_peers = [peer for peer in peers if peer not in self.unchoking_peers]
        if not choking_peers:
            return
        peer = random.choice(choking_peers)
        self.unchoking_peers.add(peer)

        log: str = ("new unchoking list: " + str(list(self.unchoking_peers))) + '\n'
        log += ("optimistic unchoke " + str(peer))
        self._log(" optimistic unchoke", log)

        self._set_choking_status(peer, False)

    def get_next_download_task(self) -> List[Tuple[IPPort, List[int]]]:
        wanted = set(range(1, 1 + self.controller.dir_controller.torrent_block_count)) \
            .difference(self.controller.dir_controller.get_local_blocks())
        all_peers = list(self.alive_peer_list)

        # print("time = ", current_time_ms() - self.last_time)

        if (current_time_ms() - self.last_time >= 8000):
            self.evaluate()
            self.last_time = current_time_ms()
            self.times += 1
            pass

        if (current_time_ms() - self.stamp >= 1000):
            for peer in all_peers:
                if peer not in self.speed_test:
                    self.speed_test[peer] = []
                self.speed_test[peer].append(self.controller.controller.get_peer_conn(peer).traffic_monitor.get_downlink_rate())
            self.stamp = current_time_ms()

        if (self.times >= 3):
            self.optimistic_unchoke()
            self.times = 0
            pass

        peers = [peer for peer in all_peers if peer not in self.choked_by_peers]

        tasks = list()
        start_time = current_time_ms()
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

            #print("n%s peer_chunk_info = %s want_chunks = %s wants = %s pending = %s\n" % (
            #peer, self.peer_chunk_info[peer].chunks, list(want_chunks), list(wants), self.pending_peer[peer]))

        if tasks:
            # for task in tasks:
            #     _, w = task
            #     l += len(w)
            print("tasks ", tasks)
        return tasks

    def on_new_peer(self, peer_addr: IPPort):
        self.pending_peer[peer_addr] = set()
        self.peer_sim_numbers[peer_addr] = self.MAX_SIMULTANEOUS_REQ
        self.unchoking_peers.add(peer_addr)
        statistics.get_instance().set_peer_status(self.controller.controller.local_addr[1], peer_addr[1], "Unchoked")
        statistics.get_instance().set_peer_status2(self.controller.controller.local_addr[1], peer_addr[1], "Unchoking")

    def close(self):
        self.peer_sim_numbers_reseter.cancel()
