import random
import threading
from typing import List, Dict, Set, Tuple

import controller
from utils import IPPort, current_time_ms
from . import AbstractDownloadController


class RandomDownloadController(AbstractDownloadController):
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

    @property
    def timeout_ms(self):
        return self.controller.controller.socket.timeout_ms

    def reseter(self):
        try:
            for p in self.peer_sim_numbers:
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

    def on_peer_timeout(self, peer_addr: IPPort, chunk_seq_id: int):
        print(f"[ALG] block {chunk_seq_id} timeout from {peer_addr}")
        self.peer_sim_numbers[peer_addr] = 1
        if chunk_seq_id in self.timeouting_blocks:
            del self.timeouting_blocks[chunk_seq_id]
        if chunk_seq_id in self.pending_peer[peer_addr]:
            self.pending_peer[peer_addr].remove(chunk_seq_id)
        if chunk_seq_id in self.pending_blocks:
            self.pending_blocks.remove(chunk_seq_id)

    def get_next_download_task(self) -> List[Tuple[IPPort, List[int]]]:
        wanted = set(range(1, 1 + self.controller.dir_controller.torrent_block_count)) \
            .difference(self.controller.dir_controller.get_local_blocks())
        peers = list(self.alive_peer_list)
        random.shuffle(peers)
        tasks = list()
        # check timeouts
        current = current_time_ms()
        for k in self.timeouting_blocks.keys():
            # k: chunk seq
            if current - self.timeouting_blocks[k] > self.timeout_ms + 2500:
                print(f"[RD] !!!!!!! Chunk {k} TIMEOUT IN Random Downloader !!!!!!")
                p = None  # IPPort
                for pp in self.pending_peer:
                    if k in self.pending_peer[pp]:
                        p = pp
                        break
                if p:
                    self.pending_peer[p].remove(k)
                self.pending_blocks.remove(k)
                del self.timeouting_blocks[k]
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
                self.timeouting_blocks[want_chunk_id] = current_time_ms()
            tasks.append((peer, wants))
        if tasks:
            print(tasks)
        return tasks

    def on_new_peer(self, peer_addr: IPPort):
        self.pending_peer[peer_addr] = set()
        self.peer_sim_numbers[peer_addr] = self.MAX_SIMULTANEOUS_REQ

    def close(self):
        self.peer_sim_numbers_reseter.cancel()
