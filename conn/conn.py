from __future__ import annotations

import time
from math import floor
from typing import Tuple, Dict, Any
import threading
import queue

import controller
from packet.base_packet import BasePacket
from utils import IPPort
from utils.bytes_utils import random_short, bytes_to_int

EVTYPE_END = 1
EVTYPE_INCOMING_PACKET = 2

ALIVE_INTERVAL = 60

class Conn:
    """
    Manage a connection
    """

    def __init__(self, remote_addr: IPPort, ctrl: controller.Controller):
        self.remote_addr: IPPort = remote_addr
        self.controller: controller.Controller = ctrl
        self.__request_data__: Dict[int, Any] = dict()
        # __request_data__ is used to save status between send and recv
        self.controller.socket.register(remote_addr, self)
        self.__recv_queue__ = queue.Queue()
        self.__recv_thread__ = threading.Thread(target=self.__run__)
        self.__recv_thread__.name = "Conn Recv Thread - Peer {}".format(self.remote_addr)
        self.__recv_thread__.start()
        self.waiter: Dict[int, threading.Condition] = dict()
        self.last_active: int = floor(time.time())
        pass

    def close(self):
        self.controller.socket.unregister(self.remote_addr)
        # unregister itself and quit
        self.__recv_queue__.put((EVTYPE_END, None))
        if self.__recv_thread__ is not threading.current_thread():
            self.__recv_thread__.join()

    def __run__(self):
        while True:
            # Event Loop
            try:
                (ev_type, data) = self.__recv_queue__.get(block=True, timeout=1)
                self.last_active = floor(time.time())
                timeout = False
            except queue.Empty as e:
                timeout = True
                # print(e)
            if not timeout:
                if ev_type == EVTYPE_END:
                    break
                if ev_type == EVTYPE_INCOMING_PACKET:
                    # New Packet, Handle Packet Now
                    self.__handler__(data)

    def __handler__(self, packet: BasePacket):
        pass

    def recv_packet(self, packet: BasePacket):
        event = (EVTYPE_INCOMING_PACKET, packet)
        self.__recv_queue__.put_nowait(event)

    def send_packet(self, packet: BasePacket):
        self.controller.socket.send_packet(packet, self.remote_addr)

    def new_identifier(self) -> int:
        ident = bytes_to_int(random_short())
        while ident in self.__request_data__.keys():
            ident = bytes_to_int(random_short())
        return ident

    def put_state(self, identifier: int, state: Any):
        self.__request_data__[identifier] = state

    def retrieve_state(self, identifier: int) -> Any:
        if identifier not in self.__request_data__.keys():
            return None
        data = self.__request_data__[identifier]
        del self.__request_data__[identifier]
        return data

    def send_request(self, packet: BasePacket, state: Any, waiter: bool = False) -> int:
        packet.identifier = self.new_identifier()
        self.put_state(packet.identifier, state)
        if waiter:
            if packet.type not in self.waiter:
                self.waiter[packet.type] = threading.Condition()
        self.send_packet(packet)
        return packet.identifier

    def wait(self, itype: int, timeout: int = None) -> bool:
        '''
        Wait for a response
        :param itype: packet type
        :param timeout: timeout in second
        :return: True if Succeed, False if timeout
        '''
        if itype in self.waiter:
            with self.waiter[itype]:
                return self.waiter[itype].wait(timeout)

    def notify_lock(self, itype: int):
        if itype in self.waiter:
            with self.waiter[itype]:
                self.waiter[itype].notify()
            # del self.waiter[itype]
            # Dont delete it

    @property
    def is_alive(self) -> bool:
        return floor(time.time()) - self.last_active < ALIVE_INTERVAL
