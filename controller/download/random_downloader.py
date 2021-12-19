import random
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
        self.MAX_SIMULTANEOUS_REQ = 1

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
        self.on_peer_respond_failed(peer_addr, chunk_seq_id)
        # self.pending_peer[peer_addr].remove(chunk_seq_id)
        # self.timeouting_blocks[chunk_seq_id] = current_time_ms()
        # self.pending_blocks.remove(chunk_seq_id)
        # Don't remove them from pending_blocks
        # lower down peer_addr's level? but should be done in random alg

    def get_next_download_task(self) -> List[Tuple[IPPort, List[int]]]:
        wanted = set(range(1, 1 + self.controller.dir_controller.torrent_block_count)) \
            .difference(self.controller.dir_controller.get_local_blocks())
        peers = list(self.peer_list)
        random.shuffle(peers)
        tasks = list()
        for peer in peers:
            if peer not in self.pending_peer:
                self.on_new_peer(peer)
            if len(self.pending_peer[peer]) >= self.MAX_SIMULTANEOUS_REQ:
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
