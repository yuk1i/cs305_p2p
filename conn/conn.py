from __future__ import annotations

import time
from math import floor
from typing import Tuple, Dict, Any, Set
import threading
import queue

import controller
from .connection_status import ConnectionStatus
from packet.base_packet import BasePacket
from utils import IPPort
from utils.bytes_utils import random_short, bytes_to_int, current_time_ms

EVTYPE_END = 1
EVTYPE_INCOMING_PACKET = 2

ALIVE_INTERVAL = 60


class Conn:
    """
    Manage a connection
    """

    def __init__(self, remote_addr: IPPort, ctrl: controller.Controller, timeout_ms=5000):
        self.remote_addr: IPPort = remote_addr
        self.connectionStatus: ConnectionStatus = ConnectionStatus()
        self.controller: controller.Controller = ctrl
        self.saved_states: Dict[int, Any] = dict()
        # __request_data__ is used to save status between send and recv
        self.controller.socket.register(remote_addr, self)
        self.__recv_queue__ = queue.Queue()
        self.__recv_thread__ = threading.Thread(target=self.__run__)
        self.__recv_thread__.name = "Conn Recv Thread - Peer {}".format(self.remote_addr)
        self.__recv_thread__.start()
        self.waiter: Dict[int, threading.Condition] = dict()
        self.lock = threading.RLock()
        self.pending_packet: Dict[int, Tuple[int, int]] = dict()
        self.timeout_ms = timeout_ms
        # Pending packets, key: identifier, value: (itype, send_time) in ms
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
            (ev_type, data) = self.__recv_queue__.get(block=True)

            if ev_type == EVTYPE_END:
                break
            if ev_type == EVTYPE_INCOMING_PACKET:
                # New Packet, Handle Packet Now
                self.__handler__(data)

    def __handler__(self, packet: BasePacket):
        pass

    def __on_timeout__(self, itype: int, identifier: int, state: Any):
        pass

    def recv_packet(self, packet: BasePacket):
        with self.lock:
            if packet.identifier not in self.pending_packet:
                print("[Conn] Recv timeouted packet")
                # dropped packet
            else:
                del self.pending_packet[packet.identifier]
        event = (EVTYPE_INCOMING_PACKET, packet)
        self.__recv_queue__.put_nowait(event)

    def send_packet(self, packet: BasePacket):
        self.controller.socket.send_packet(packet, self.remote_addr)
        with self.lock:
            self.pending_packet[packet.identifier] = (packet.type, current_time_ms())

    def new_identifier(self) -> int:
        ident = bytes_to_int(random_short())
        with self.lock:
            while ident in self.saved_states.keys():
                ident = bytes_to_int(random_short())
        return ident

    def put_state(self, identifier: int, state: Any):
        with self.lock:
            self.saved_states[identifier] = state

    def retrieve_state(self, identifier: int) -> Any:
        with self.lock:
            if identifier not in self.saved_states.keys():
                return None
            data = self.saved_states[identifier]
            del self.saved_states[identifier]
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
        """
        Wait for a response
        :param itype: packet type
        :param timeout: timeout in second
        :return: True if Succeed, False if timeout
        """
        if itype in self.waiter:
            with self.waiter[itype]:
                return self.waiter[itype].wait(timeout)

    def notify_lock(self, itype: int):
        if itype in self.waiter:
            with self.waiter[itype]:
                self.waiter[itype].notify()
            # del self.waiter[itype]
            # Dont delete it

    def check_timeout(self):
        cur = current_time_ms()
        for identi in list(self.pending_packet.keys()):
            itype, send_time = self.pending_packet[identi]
            if cur - send_time >= self.timeout_ms:
                state = self.saved_states[identi] if identi in self.saved_states else None
                self.__on_timeout__(itype, identi, state)
                del self.pending_packet[identi]
