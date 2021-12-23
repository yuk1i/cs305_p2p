from __future__ import annotations

import threading
import warnings
from collections import namedtuple
from math import floor
from typing import List

from utils import IPPort
# from .socket_manager import SocketManager
# import socket_manager
from utils.bytes_utils import current_time_ms

SPEED_MONITOR_TIME = 5


OneContrib = namedtuple('OneContrib', ['size', 'time'])


class _BaseTrafficMonitor:

    def __init__(self):
        self.start_time = current_time_ms()
        self.last_active: int = self.start_time
        self._uplink_rate: int = 0
        self._uplink_list: List[OneContrib] = []
        self._downlink_rate: int = 0
        self._downlink_list: List[OneContrib] = []

    def feed_uplink(self, packet_size: int):
        self._uplink_list.append(OneContrib(packet_size, current_time_ms()))

    def get_uplink_rate(self) -> int:
        self._update_uplink_rate()
        self._uplink_rate = floor(sum(map(lambda x: x.size, self._uplink_list)) / self.total_time)
        return self._uplink_rate

    def _update_uplink_rate(self):
        valid_index: int = None
        cur_time_ms: int = current_time_ms()
        for i, record in enumerate(self._uplink_list):
            if cur_time_ms - record.time < SPEED_MONITOR_TIME:
                valid_index = i
                break
        if valid_index:
            self._uplink_list = self._uplink_list[valid_index:]

    def feed_downlink(self, packet_size: int):
        self.last_active = current_time_ms()
        self._downlink_list.append(OneContrib(packet_size, self.last_active))

    def get_downlink_rate(self):
        self._update_downlink_rate()
        self._downlink_rate = floor(sum(map(lambda x: x.size, self._downlink_list)) / self.total_time)
        return self._downlink_rate

    def _update_downlink_rate(self):
        valid_index: int = None
        cur_time_ms: int = current_time_ms()
        for i, record in enumerate(self._downlink_list):
            if cur_time_ms - record.time < SPEED_MONITOR_TIME*1000:
                valid_index = i
                break
        print(f'thread {threading.current_thread()} remain from: {valid_index}')
        # print(f'thread {threading.current_thread()} len: {len(self,)}')
        if valid_index:
            self._downlink_list = self._downlink_list[valid_index:]

    @property
    def total_time(self):
        return max(1, (current_time_ms() - self.start_time) // 1000) \
            if current_time_ms() - self.start_time < SPEED_MONITOR_TIME * 1000 \
            else SPEED_MONITOR_TIME


class SockManTrafficMonitor(_BaseTrafficMonitor):

    def __init__(self, sockman):
        super(SockManTrafficMonitor, self).__init__()
        self.sockman = sockman

    def hook_uplink(self, packet_size: int, remote_addr: IPPort):
        super(SockManTrafficMonitor, self).feed_uplink(packet_size)
        self.sockman.mapper[remote_addr].traffic_monitor.feed_uplink(packet_size)

    def hook_downlink(self, packet_size: int, remote_addr: IPPort):
        super(SockManTrafficMonitor, self).feed_downlink(packet_size)
        self.sockman.mapper[remote_addr].traffic_monitor.feed_downlink(packet_size)

    def feed_uplink(self, packet_size: int):
        """
        don't use this
        """
        warnings.warn("don't use SockManTrafficMonitor.feed_uplink, this method has been override to do nothing.")

    def feed_downlink(self, packet_size: int):
        """
        don't use this
        """
        warnings.warn("don't use SockManTrafficMonitor.feed_downlink, this method has been override to do nothing.")


class ConnectionTrafficMonitor(_BaseTrafficMonitor):

    pass
