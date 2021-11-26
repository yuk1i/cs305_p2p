from __future__ import annotations

from typing import Tuple, List
import threading
import queue

from packet.base_packet import BasePacket

EVTYPE_END = 1
EVTYPE_INCOMING_PACKET = 2
EVTYPE_SEND_REQ = 3


class ConnManager:
    """
    Manage Peer Connections
    """

    def __init__(self, peer_addr: Tuple[str, int]):
        self.peer: Tuple[str, int] = peer_addr
        self.thread = threading.Thread(target=self.__run__)
        self.queue = queue.Queue()
        pass

    def start(self):
        self.thread.start()

    def close(self):
        self.queue.put((EVTYPE_END, None))

    def __run__(self):
        while True:
            # Event Loop
            (ev_type, data) = self.queue.get(block=True)
            if ev_type == EVTYPE_END:
                break

            if ev_type == EVTYPE_INCOMING_PACKET:
                # New Packet, Handle Packet Now
                self.__handler__(data)
            elif ev_type == EVTYPE_SEND_REQ:
                pass
                # TODO: Send Request Here

    def __handler__(self, packet: BasePacket):
        pass

    def deliver(self, packet: BasePacket):
        event = (EVTYPE_INCOMING_PACKET, packet)
        self.queue.put_nowait(event)

    def last_active(self):
        """
        Return time passed after last communication
        :return:
        """
        pass

    def uplink_speed(self) -> int:
        """
        Get uplink speed in byte/s
        :return:
        """
        pass

    def downlink_speed(self) -> int:
        """
        Get download speed in byte/s
        :return:
        """
        pass
