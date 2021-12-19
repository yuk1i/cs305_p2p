from typing import List, Dict, Set, Tuple

import controller
from utils import IPPort
from . import AbstractDownloadController


class RandomDownloadController(AbstractDownloadController):
    def __init__(self, torrent_ctrl: controller.TorrentController):
        super().__init__(torrent_ctrl)
        self.pending_blocks: Set[int] = set()
        self.pending_peer: Dict[IPPort, Tuple[int, int]] = dict()

    def on_peer_respond_succeed(self, peer_addr: IPPort, chunk_seq_id: int):
        super().on_peer_respond_succeed(peer_addr, chunk_seq_id)

    def on_peer_respond_failed(self, peer_addr: IPPort, chunk_seq_id: int):
        super().on_peer_respond_failed(peer_addr, chunk_seq_id)

    def on_peer_timeout(self, peer_addr: IPPort, chunk_seq_id: int):
        pass

    def get_next_download_task(self) -> List[Tuple[IPPort, List[int]]]:
        return super().get_next_download_task()
