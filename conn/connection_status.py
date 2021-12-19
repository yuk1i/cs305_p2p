import time
from collections import namedtuple
from math import floor
from typing import List

from packet import BasePacket

SPEED_MONITOR_TIME = 5


OneContrib = namedtuple('OneContrib', ['size', 'time'])

class ConnectionStatus:

    def __init__(self):
        self.start_time = floor(time.time())
        self.last_active: int = self.start_time
        self._uplink_rate: int = 0
        self._uplink_list: List[OneContrib] = []
        self._downlink_rate: int = 0
        self._downlink_list: List[OneContrib] = []

    def feed_uplink(self, packet: bytes):
        self._uplink_list.append((len(packet), self.get_cur()))

    def get_uplink_rate(self) -> int:
        self._update_uplink_rate()
        total_time: int = self.get_cur() - self.start_time \
            if self.get_cur() - self.start_time < 5 \
            else SPEED_MONITOR_TIME
        self._uplink_rate = floor(sum(map(lambda x: x.size, self._uplink_list)) / total_time)
        return self._uplink_rate

    def _update_uplink_rate(self):
        valid_index: int = None
        for i, record in enumerate(self._uplink_list):
            if record.time - self.get_cur() < SPEED_MONITOR_TIME:
                valid_index = i
                break
        if valid_index:
            self._uplink_list = self._uplink_list[valid_index:]

    def feed_downlink(self, packet: bytes):
        self.last_active = self.get_cur()
        self._downlink_list.append((len(packet), self.last_active))

    def get_downlink_rate(self):
        self._update_downlink_rate()
        total_time: int = self.get_cur() - self.start_time \
            if self.get_cur() - self.start_time < 5 \
            else SPEED_MONITOR_TIME
        self._downlink_rate = floor(sum(map(lambda x: x.size, self._downlink_list)) / total_time)
        return self._downlink_rate

    def _update_downlink_rate(self):
        valid_index: int = None
        for i, record in enumerate(self._downlink_list):
            if record.time - self.get_cur() < SPEED_MONITOR_TIME:
                valid_index = i
                break
        if valid_index:
            self._uplink_list = self._uplink_list[valid_index:]

    @staticmethod
    def get_cur():
        return floor(time.time())
