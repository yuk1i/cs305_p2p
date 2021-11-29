from __future__ import annotations

import threading
import time
from typing import List, Tuple

import controller
from torrent import Torrent
from utils import IPPort


class TorrentController:
    def __init__(self, torrent: Torrent, ctrl: controller.PeerController):
        self.torrent_hash: str = torrent.torrent_hash
        self.controller: controller.PeerController = ctrl
        self.torrent = torrent
        self.status = controller.TorrentStatus.TORRENT_STATUS_NOT_STARTED
        self.chunk_status: List[bool] = list()
        self.peer_list: List[IPPort] = list()
        self.tracker_addr: IPPort = ("", 0)
        self.save_dir: str = ""
        self.torrent_file_path: str = ""
        self.thread = threading.Thread(target=self.__run__)
        self.torrent_binary: bytearray = None

    def __run__(self):
        # Request peers first
        while len(self.peer_list) == 0:
            self.controller.retrieve_peer_list(self.torrent_hash)
            # it will call on_peer_list_updated, and it's blocking
            time.sleep(10)
        print("[TC] Get peer list %s" % self.torrent_hash)
        self.status = controller.TorrentStatus.TORRENT_STATUS_METADATA
        for peer in self.peer_list:
            self.controller.create_peer_conn(peer)
        # Then, Request chunks for torrent files, download them, try to decode torrent files
        # If decoded successfully, save torrent file,
        #       create directory structure
        #       and start downloading every data block
        # TODO: Improvement here: Load torrent from self.torrent_save_path and check its hash
        while not self.torrent.__torrent_file_downloaded__:
            print("start downloading")
            # Download torrent files from peers
            p2p_conn = self.controller.get_peer_conn(self.peer_list[0])
            # TODO: Improvements here
            p2p_conn.request_torrent_chunk(self.torrent_hash)
            # TODO: combine binary data, call Torrent.
            try:
                self.torrent.try_decode_from_binary(self.torrent_binary)
                self.torrent.save_to_file(self.torrent_file_path)
                self.torrent.__torrent_file_downloaded__ = True
            except Exception as e:
                print("[TC] Errored when trying to decode torrent from binary")
        print("[TC] Successfully download torrent file, size: %s" % (len(self.torrent_binary)))
        pass

    def on_peer_list_update(self, peers: List[IPPort]):
        print("[TorrentCtrl] {} Peer List updated: {}".format(self.torrent_hash, peers))
        self.peer_list.clear()
        self.peer_list.extend(peers)
        self.peer_list.remove(self.controller.local_addr)
        pass

    def on_torrent_chunk_received(self, bdata: bytes, start: int, end: int, total_length: int):
        if not self.torrent_binary:
            self.torrent_binary = bytearray(total_length)
        self.torrent_binary[start: start + end] = bdata

    def close(self):
        if self.thread.is_alive():
            self.thread.join()
        # TODO: Exit

    def start_download(self, save_dir: str, torrent_file_path: str):
        if self.torrent.__torrent_file_downloaded__:
            return
        if self.status != controller.TorrentStatus.TORRENT_STATUS_REGISTERED:
            raise Exception("Register torrent first")
        if self.controller.tracker_status != controller.TrackerStatus.NOTIFIED:
            raise Exception("Notify tracker first")
        self.status = controller.TorrentStatus.TORRENT_STATUS_DOWNLOADING
        self.save_dir = save_dir
        self.torrent_file_path = torrent_file_path
        self.thread.start()

    def wait_downloaded(self):
        self.thread.join()
