from __future__ import annotations

from typing import Tuple
import threading
import queue

import controller
from packet.base_packet import BasePacket

EVTYPE_END = 1
EVTYPE_INCOMING_PACKET = 2
EVTYPE_SEND_REQ = 3


class Conn:
    """
    Manage a connection
    """

    def __init__(self, peer_addr: Tuple[str, int], ctrl: controller.Controller):
        self.peer_addr: Tuple[str, int] = peer_addr
        self.controller = ctrl
        self.__recv_queue__ = queue.Queue()
        self.__send_queue__ = queue.Queue()
        self.__recv_thread__ = threading.Thread(target=self.__run__)
        self.__recv_thread__.name = "Conn Recv Thread - Peer {}".format(self.peer_addr)
        self.__recv_thread__.start()
        self.__send_thread__ = threading.Thread(target=self.__send__)
        self.__send_thread__.name = "Conn Send Thread - Peer {}".format(self.peer_addr)
        self.__send_thread__.start()
        pass

    def close(self):
        self.__recv_queue__.put((EVTYPE_END, None))

    def __run__(self):
        while True:
            # Event Loop
            (ev_type, data) = self.__recv_queue__.get(block=True)
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

    def __send__(self):
        while True:
            pkt = self.__send_queue__.get(block=True)
            self.controller.socket.send_packet(pkt, self.peer_addr)

    def recv_packet(self, packet: BasePacket):
        event = (EVTYPE_INCOMING_PACKET, packet)
        self.__recv_queue__.put_nowait(event)

    def send_packet(self, packet: BasePacket):
        self.__send_queue__.put_nowait(packet)
