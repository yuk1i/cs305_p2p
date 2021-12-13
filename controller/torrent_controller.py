from __future__ import annotations

import math
import queue
import random
import threading
import time
from typing import List, Tuple, Dict, Set

import controller
import utils.bytes_utils
from torrent import Torrent
from utils import IPPort

EV_QUIT = 0
EV_PEER_CHUNK_INFO_UPDATED = 1
EV_PEER_RESPOND = 2


class TorrentController:
    def __init__(self, torrent: Torrent, ctrl: controller.PeerController,
                 save_dir: str, torrent_file_path: str):
        """
        A torrent controller must be inited by at least the hash of the torrent,
        which can be from the hash str, torrent file (path), or Torrent object.
        :param torrent_hash:
        :param ctrl:
        """
        self.torrent = torrent
        self.torrent_hash: str = torrent.torrent_hash
        self.controller: controller.PeerController = ctrl
        self.torrent_file_path: str = torrent_file_path
        self.status = controller.TorrentStatus.TORRENT_STATUS_NOT_STARTED
        # self.chunk_status: List[bool] = list()
        self.peer_list: List[IPPort] = list()
        self.peer_chunk_info: Dict[IPPort, controller.RemoteChunkInfo] = dict()
        # self.tracker_addr: IPPort = ("", 0)
        self.thread = threading.Thread(target=self.__run__)
        self.events = queue.Queue()
        self.torrent_binary = bytearray()
        self.dir_controller = controller.DirectoryController(torrent, torrent_file_path, save_dir)
        if not self.torrent.dummy:
            self.dir_controller.check_all_hash()
        # if self.

    def __run__(self):
        # Request peers first
        while len(self.peer_list) == 0:
            self.controller.retrieve_peer_list(self.torrent_hash)
            # it will call on_peer_list_updated, and it's blocking
            if len(self.peer_list) == 0:
                time.sleep(1)
        print("[TC] Get peer list %s" % self.torrent_hash)
        self.status = controller.TorrentStatus.TORRENT_STATUS_METADATA
        for peer in self.peer_list:
            self.controller.create_peer_conn(peer)
            self.peer_chunk_info[peer] = controller.RemoteChunkInfo()
        # Then, Request chunks for torrent files, download them, try to decode torrent files
        # If decoded successfully, save torrent file,
        #       create directory structure
        #       and start downloading every data block
        # TODO: Improvement here: Load torrent from self.torrent_save_path and check its hash
        peer_index = random.randrange(0, len(self.peer_list))
        while self.torrent.dummy:
            print("start downloading")
            # Download torrent files from peers
            if peer_index >= len(self.peer_list):
                self.controller.retrieve_peer_list(self.torrent_hash)
                peer_index = 0
                continue
            p2p_conn = self.controller.get_peer_conn(self.peer_list[peer_index])
            # TODO: Improvements here
            ready = p2p_conn.request_torrent_chunk(self.torrent_hash)
            if not ready:
                peer_index = peer_index + 1
                continue
            # TODO: combine binary data, call Torrent.
            try:
                self.torrent.try_decode_from_binary(self.torrent_binary)
                self.torrent.__dummy__ = False
                self.torrent.save_to_file(self.torrent_file_path)
            except Exception as e:
                print("[TC] Errored when trying to decode torrent from binary")
        print("[TC] Successfully obtain torrent file, size: %s" % (len(self.torrent.__json_str__)))
        self.dir_controller.update()
        self.dir_controller.build_torrent_directory_structure()
        self.update_peers_chunks()
        # Start polling
        self.status = controller.TorrentStatus.TORRENT_STATUS_DOWNLOADING
        ev_type = 0
        data = None
        pending_blocks: Set[int] = set()
        pending_peer: Dict[IPPort, int] = dict()
        while not self.dir_controller.download_completed:
            try:
                (ev_type, data) = self.events.get(block=True, timeout=1)
                timeout = False
            except queue.Empty as e:
                timeout = True
                print(e)
            if not timeout:
                if ev_type == EV_QUIT:
                    break
                elif ev_type == EV_PEER_CHUNK_INFO_UPDATED:
                    pass
                elif ev_type == EV_PEER_RESPOND:
                    peer_addr: IPPort = data
                    del pending_peer[peer_addr]
            else:
                pass
                self.update_peers_chunks()
            # TODO: check timeouts
            available_peers = set(self.peer_list).difference(pending_peer)
            for peer in available_peers:
                diff = self.peer_chunk_info[peer].chunks.difference(
                    self.dir_controller.local_state.local_block)
                want_chunks = diff.difference(pending_blocks)
                if len(want_chunks) == 0:
                    # TODO: pass
                    continue
                want_chunk_id = random.choice(list(want_chunks))
                pending_blocks.add(want_chunk_id)
                pending_peer[peer] = utils.bytes_utils.current_time_ms()
                self.controller.get_peer_conn(peer).async_request_chunk(self.torrent_hash, want_chunk_id)
        self.dir_controller.flush_all()

    def on_peer_chunk_updated(self, peer: IPPort, chunk_info: Set[int]):
        print("[TC] peer (%s:%s) chunk info updated" % peer)
        self.peer_chunk_info[peer].update(chunk_info)
        pass

    def on_peer_list_update(self, peers: List[IPPort]):
        print("[TorrentCtrl] {} Peer List updated: {}".format(self.torrent_hash, peers))
        self.peer_list.clear()
        self.peer_list.extend(peers)
        self.peer_list.remove(self.controller.local_addr)
        self.events.put_nowait((EV_PEER_CHUNK_INFO_UPDATED, None))

    def on_torrent_chunk_received(self, bdata: bytes, start: int, end: int, total_length: int):
        if not self.torrent_binary:
            self.torrent_binary = bytearray(total_length)
        self.torrent_binary[start: start + end] = bdata

    def update_peers_chunks(self):
        """
        Update Peers chunk info, and send mine
        :return:
        """
        # Update Chunk Info
        my_block = self.dir_controller.local_state.local_block.copy()
        for peer_addr in self.peer_list:
            if self.peer_chunk_info[peer_addr].should_update():
                self.peer_chunk_info[peer_addr].mark_pending()
                p2p_conn = self.controller.get_peer_conn(peer_addr)
                p2p_conn.async_update_chunk_info(self.torrent_hash, my_block)

    def close(self):
        if self.thread.is_alive():
            self.thread.join()
        if self.dir_controller:
            self.dir_controller.close()
        # TODO: Exit

    def start_download(self):
        if self.status != controller.TorrentStatus.TORRENT_STATUS_REGISTERED:
            raise Exception("Register torrent first")
        if self.controller.tracker_status != controller.TrackerStatus.NOTIFIED:
            raise Exception("Notify tracker first")
        self.status = controller.TorrentStatus.TORRENT_STATUS_DOWNLOADING
        self.thread.start()

    def wait_downloaded(self):
        self.thread.join()
        self.dir_controller.flush_all()

    def on_new_income_peer(self, remote_addr: IPPort):
        """
        通过 RequestForTorrent / ChunkInfoUpdate 来学习到的新peer
        :param remote_addr:
        :param chunk_list:
        :return:
        """
        print("[TC] New Income Peer %s:%s" % remote_addr)
        self.peer_list.append(remote_addr)
        if remote_addr not in self.peer_chunk_info:
            self.peer_chunk_info[remote_addr] = controller.RemoteChunkInfo()

    def on_peer_respond(self, peer_addr: IPPort):
        self.events.put_nowait((EV_PEER_RESPOND, peer_addr))
