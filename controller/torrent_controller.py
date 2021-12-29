from __future__ import annotations

import math
import queue
import random
import threading
import time
from typing import List, Tuple, Dict, Set

import controller
import statistics
import utils.bytes_utils
from torrent import Torrent
from utils import IPPort

EV_QUIT = 0
EV_PEER_CHUNK_INFO_UPDATED = 1
EV_PEER_RESPOND = 2
EV_CHUNK_TIMEOUT = 3
EV_CHOKE_STATUS_CHANGE = 4

MODE_DONT_REPEAT = 1
MODE_FULL = 0

PEER_RSPD_SUCCEED = 0x01
PEER_RSPD_FAILED = 0x02
PEER_RSPD_NO_UPLOAD_BANDWITH = 0x03


class TorrentController:
    def __init__(self, torrent: Torrent, ctrl: controller.PeerController,
                 save_dir: str, torrent_file_path: str, use_tit_for_tat: False):
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
        self.download_controller: controller.download.AbstractDownloadController
        if use_tit_for_tat:
            self.download_controller = controller.download.TitfortatDownloadController(self)
        else:
            self.download_controller = controller.download.RandomDownloadController(self)
        # self.tracker_addr: IPPort = ("", 0)
        self.thread = threading.Thread(target=self.__run__)
        self.events = queue.Queue()
        self.torrent_binary = bytearray()
        if self.torrent.is_school_torrent:
            self.dir_controller = controller.DummyDirectoryController(torrent, save_dir)
        else:
            self.dir_controller = controller.DirectoryController(torrent, torrent_file_path, save_dir)
        if not self.torrent.dummy:
            self.dir_controller.check_all_hash()
        self.upload_mode = MODE_FULL
        self.slow_mode = False
        if not self.torrent.dummy and self.controller.socket.proxy.upload_rate <= 10000:
            self.slow_mode = True
            self.upload_mode = MODE_DONT_REPEAT
        if self.torrent.dummy and self.controller.socket.proxy.upload_rate <= 40000:
            self.slow_mode = True
        if self.slow_mode:
            self.controller.socket.timeout_ms *= 2.5
        self.uploaded = set()
        if self.slow_mode:
            print(f"[TC{self.controller.local_addr}] Enter SLOW MODE!!!!")
        # if self.

    @property
    def alive_peer_list(self) -> List[IPPort]:
        return list(filter(lambda addr: self.is_peer_alive(addr), self.peer_list))

    def is_peer_alive(self, addr: IPPort) -> bool:
        return self.controller.get_peer_conn(addr).active

    def __run__(self):
        statistics.get_instance().on_peer_status_changed(self.controller.local_addr[1], "Downloading Metadata")
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
            self.peer_chunk_info[peer] = controller.RemoteChunkInfo(self.slow_mode)
        # Then, Request chunks for torrent files, download them, try to decode torrent files
        # If decoded successfully, save torrent file,
        #       create directory structure
        #       and start downloading every data block
        # TODO: Improvement here: Load torrent from self.torrent_save_path and check its hash
        tested_peers = set()
        while self.torrent.dummy:
            print("start downloading")
            # Download torrent files from peers
            if len(tested_peers) == len(self.alive_peer_list):
                self.controller.retrieve_peer_list(self.torrent_hash)
                tested_peers.clear()
                continue
            peer_addr = random.choice(list(set(self.alive_peer_list).difference(tested_peers)))
            tested_peers.add(peer_addr)
            p2p_conn = self.controller.get_peer_conn(peer_addr)
            # TODO: Improvements here
            ready = p2p_conn.request_torrent_chunk(self.torrent_hash)
            # Blocking wait for reply, on_torrent_chunk_received is called, return whether reply is received
            if not ready:
                continue
            # TODO: combine binary data, call Torrent.
            try:
                self.torrent.try_decode_from_binary(self.torrent_binary)
                self.torrent.__dummy__ = False
                self.torrent.save_to_file(self.torrent_file_path)
            except Exception as e:
                print("[TC] Errored when trying to decode torrent from binary")
        print("[TC] Successfully obtain torrent file, size: %s" % (len(self.torrent.__json_str__)))
        self.dir_controller.on_torrent_filled()
        statistics.get_instance().on_peer_torrent_downloaded(self.controller.local_addr[1],
                                                             self.dir_controller.torrent_block_count)
        self.update_peers_chunks(0)
        # Start polling
        self.status = controller.TorrentStatus.TORRENT_STATUS_DOWNLOADING
        statistics.get_instance().on_peer_status_changed(self.controller.local_addr[1], "Downloading")
        if self.dir_controller.is_download_completed():
            # Am the uploader!
            statistics.get_instance().on_peer_fill_chunk_uploader(self.controller.local_addr[1],
                                                                  self.dir_controller.torrent_block_count)
        ev_type = 0
        data = None
        # pending_blocks: Set[int] = set()
        # pending_peer: Dict[IPPort, Tuple[int, int]] = dict()
        # TIMEOUT = 15
        while not self.dir_controller.is_download_completed():
            try:
                (ev_type, data) = self.events.get(block=True, timeout=0.05)
                timeout = False
            except queue.Empty:
                timeout = True
            if not timeout:
                if ev_type == EV_QUIT:
                    break
                elif ev_type == EV_PEER_CHUNK_INFO_UPDATED:
                    pass
                    # ignored, do in async
                elif ev_type == EV_PEER_RESPOND:
                    (peer_addr, status, chunk_seq_id) = data
                    if status == PEER_RSPD_SUCCEED:
                        self.download_controller.on_peer_respond_succeed(peer_addr, chunk_seq_id)
                    elif status == PEER_RSPD_NO_UPLOAD_BANDWITH:
                        self.download_controller.on_peer_timeout(peer_addr, chunk_seq_id)
                    else:
                        self.download_controller.on_peer_respond_failed(peer_addr, chunk_seq_id)
                elif ev_type == EV_CHUNK_TIMEOUT:
                    (remote_addr, block_seq) = data
                    self.download_controller.on_peer_timeout(remote_addr, block_seq)
                elif ev_type == EV_CHOKE_STATUS_CHANGE:
                    (remote_addr, choke_status) = data
                    self.download_controller.on_peer_choke_status_change(remote_addr, choke_status)
            if not self.events.empty():
                continue
            if timeout:
                self.update_peers_chunks(
                    len(self.dir_controller.get_local_blocks()) / self.dir_controller.torrent_block_count * 100)
                speed: Dict[int, Tuple[str, str]] = dict()  # TODO: Use IPPort here
            if self.dir_controller.is_download_completed():
                continue
            # 抽象的下载规划算法
            tasks: List[Tuple[IPPort, List[int]]] = self.download_controller.get_next_download_task()
            for task in tasks:
                task: Tuple[IPPort, List[int]]
                for want_chunk_id in task[1]:
                    self.controller.get_peer_conn(task[0]).async_request_chunk(self.torrent_hash, want_chunk_id)
        statistics.get_instance().on_peer_status_changed(self.controller.local_addr[1], "Uploading")
        self.status = controller.TorrentStatus.TORRENT_STATUS_FINISHED
        self.dir_controller.flush_all()

    def on_peer_choke_status_change(self, peer: IPPort, status: bool):
        self.events.put_nowait((EV_CHOKE_STATUS_CHANGE, (peer, status)))

    def on_peer_respond_chunk_req(self, peer_addr: IPPort, status: int, block_id: int):
        self.events.put_nowait((EV_PEER_RESPOND, (peer_addr, status, block_id)))

    def on_chunk_timeout(self, remote_addr, block_seq):
        self.events.put_nowait((EV_CHUNK_TIMEOUT, (remote_addr, block_seq)))

    def on_peer_chunk_updated(self, peer: IPPort, chunk_info: Set[int]):
        print("[TC] peer (%s:%s) chunk info updated" % peer)
        if peer not in self.peer_chunk_info:
            self.on_new_income_peer(peer)
        self.peer_chunk_info[peer].update(chunk_info)
        pass

    def on_peer_list_update(self, peers: List[IPPort]):
        peers.remove(self.controller.local_addr)
        self.peer_list.clear()
        self.peer_list.extend(peers)
        print("[TorrentCtrl] {} Peer List updated: {}".format(self.torrent_hash, peers))

    def on_torrent_chunk_received(self, bdata: bytes, start: int, end: int, total_length: int):
        if not self.torrent_binary:
            self.torrent_binary = bytearray(total_length)
        if len(self.torrent_binary) < total_length:
            self.torrent_binary.extend(b'\x00' * (total_length - len(self.torrent_binary)))
        self.torrent_binary[start: start + end] = bdata

    def on_new_income_peer(self, remote_addr: IPPort):
        """
        通过 RequestForTorrent / ChunkInfoUpdate 来学习到的新peer, 立即设置 peer_chunk_info
        :param remote_addr:
        :param chunk_list:
        :return:
        """
        print("[TC] New Income Peer %s:%s" % remote_addr)
        if remote_addr in self.peer_list:
            return
        self.peer_list.append(remote_addr)
        if remote_addr not in self.peer_chunk_info:
            self.peer_chunk_info[remote_addr] = controller.RemoteChunkInfo(self.slow_mode)
        self.download_controller.on_new_peer(remote_addr)

    def update_peers_chunks(self, percentage):
        """
        Send Update chunk info Request to peers, and send mine
        :return:
        """
        # Update Chunk Info
        my_block = self.dir_controller.get_local_blocks().copy()
        for peer_addr in self.peer_list:
            if self.is_peer_alive(peer_addr) \
                    and self.peer_chunk_info[peer_addr].should_update(percentage):
                self.peer_chunk_info[peer_addr].mark_pending()
                p2p_conn = self.controller.get_peer_conn(peer_addr)
                p2p_conn.async_update_chunk_info(self.torrent_hash, my_block)

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

    def close(self):
        self.events.put_nowait((EV_QUIT, None))
        statistics.get_instance().on_peer_status_changed(self.controller.local_addr[1], "Closing...")
        if self.thread.is_alive():
            self.thread.join()
        self.download_controller.close()
        if self.dir_controller:
            self.dir_controller.close()
        statistics.get_instance().on_peer_status_changed(self.controller.local_addr[1], "Closed")
        # TODO: Exit
