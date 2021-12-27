import os
import threading
from typing import Set

import controller
from torrent import Torrent, FileObject
from utils import hash_bytes
from .abstract_dir_controller import AbstractDirectoryController


class DummyDirectoryController(AbstractDirectoryController):
    def __init__(self, torrent: Torrent, save_dir: str):
        super().__init__(torrent)
        self.torrent = torrent
        self.write_lock = threading.Lock()
        self.data = bytearray()
        self.local_state: Set[int] = set()
        self.save_dir = save_dir
        if not self.torrent.dummy:
            self.on_torrent_filled()
            self.read_file()

    def get_tested_binary(self) -> bytes:
        return self.data

    def check_chunk_hash(self, bseq: int, data: bytes) -> bool:
        return hash_bytes(data) == self.torrent.get_block(bseq).hash

    def get_local_blocks(self) -> Set[int]:
        return self.local_state

    def retrieve_block(self, bseq: int) -> bytes:
        if bseq not in self.local_state or bseq > self.torrent_block_count:
            return b''
        with self.write_lock:
            start = (bseq - 1) * self.torrent.block_size
            bdata = self.data[start: start + self.torrent.block_size]
            assert self.check_chunk_hash(bseq, bdata)
            return bdata

    def save_block(self, block_seq: int, data: bytes) -> bool:
        if block_seq in self.local_state:
            return False
        offset = self.torrent.block_size * (block_seq - 1)
        with self.write_lock:
            self.data[offset: offset + self.torrent.block_size] = data
            self.local_state.add(block_seq)

    def check_all_hash(self) -> bool:
        if self.torrent.dummy:
            raise Exception("Torrent data not available")
        with self.write_lock:
            data_hash = hash_bytes(self.data)
            assert self.torrent.get_file(1).hash == data_hash
            for bi in range(1, self.torrent_block_count + 1):
                b = self.torrent.get_block(bi)
                start_offset = (bi - 1) * self.torrent.block_size
                bdata = self.data[start_offset: start_offset + self.torrent.block_size]
                if not hash_bytes(bdata) == b.hash:
                    return False
                self.local_state.add(bi)
            return True

    def on_torrent_filled(self):
        self.torrent_block_count = len(self.torrent.get_file(1).blocks)
        if len(self.data) == self.torrent.get_file(1).size:
            return
        self.data = bytearray(self.torrent_block_count * self.torrent.block_size)

    def is_download_completed(self) -> bool:
        return self.torrent_block_count == len(self.local_state)

    def flush_all(self):
        pass

    def close(self):
        pass

    def read_file(self):
        with self.write_lock:
            with open(os.path.join(self.save_dir, os.path.normpath(self.torrent.get_file(1).name)), "rb") as f:
                self.data.clear()
                self.data.extend(f.read())
        assert self.check_all_hash()
