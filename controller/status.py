import random
import time
from typing import Set

import utils.bytes_utils


class TrackerStatus:
    NOT_NOTIFIED = 1
    NOTIFYING = 2
    NOTIFIED = 3


class TorrentStatus:
    TORRENT_STATUS_CANCELED = -1
    TORRENT_STATUS_NOT_STARTED = 0
    TORRENT_STATUS_REGISTERED = 1
    TORRENT_STATUS_METADATA = 2
    TORRENT_STATUS_DOWNLOADING = 3
    TORRENT_STATUS_FINISHED = 4


class RemoteChunkInfo:
    UPDATE_INTERVAL = 10

    # Update Interval for remote peers -> 5s
    def __init__(self):
        self.last_update: int = 0  # in ms
        self.chunks: Set[int] = set()
        self.pending = False

    def update(self, chunk_info: Set[int]):
        self.chunks.update(chunk_info)
        self.last_update = utils.bytes_utils.current_time_ms() + random.randint(0, 1000)
        self.pending = False

    def remove(self, element):
        if element in self.chunks:
            self.chunks.remove(element)

    def should_update(self, percentage):
        if percentage > 40:
            percentage = 100
        percentage = (percentage*2 / 100)
        return utils.bytes_utils.current_time_ms() - self.last_update >= self.UPDATE_INTERVAL * \
               percentage * 1000 and not self.pending

    def mark_pending(self):
        self.pending = True
