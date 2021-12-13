import time
from typing import Set


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
    UPDATE_INTERVAL = 5

    # Update Interval for remote peers -> 5s
    def __init__(self):
        self.last_update: int = 0  # in ms
        self.chunks: Set[int] = set()

    def update(self, chunk_info: Set[int]):
        self.chunks.update(chunk_info)
        self.last_update = round(time.time() * 1000)

    def should_update(self):
        return round(time.time() * 1000) - self.last_update >= self.UPDATE_INTERVAL

