import threading
from typing import List, Dict, Set, Tuple

import controller
from utils import IPPort


class AbstractDownloadController:
    def __init__(self, torrent_ctrl: controller.TorrentController):
        self.peer_locks = threading.Lock()
        self.controller: controller.TorrentController = torrent_ctrl
        pass

    def on_peer_respond_succeed(self, peer_addr: IPPort, chunk_seq_id: int):
        pass

    def on_peer_respond_failed(self, peer_addr: IPPort, chunk_seq_id: int):
        pass

    def on_peer_timeout(self, peer_addr: IPPort, chunk_seq_id: int):
        pass

    def get_next_download_task(self) -> List[Tuple[IPPort, List[int]]]:
        """
        Get Next Download Tasks
        :return: A list of tasks. For each task, it contains peer addr and wanting chunks seq id
        """
        pass
