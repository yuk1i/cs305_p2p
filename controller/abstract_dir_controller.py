from typing import Set

from torrent import Torrent


class AbstractDirectoryController:
    def __init__(self, torrent: Torrent):
        self.torrent = torrent
        self.torrent_block_count = 0

    def get_tested_binary(self) -> bytes:
        pass

    def check_chunk_hash(self, bseq: int, data: bytes) -> bool:
        pass

    def get_local_blocks(self) -> Set[int]:
        pass

    def retrieve_block(self, bseq: int) -> bytes:
        pass

    def save_block(self, block_seq: int, data: bytes) -> bool:
        pass

    def check_all_hash(self) -> bool:
        pass

    def on_torrent_filled(self):
        pass

    def is_download_completed(self) -> bool:
        pass

    def flush_all(self):
        pass

    def close(self):
        pass