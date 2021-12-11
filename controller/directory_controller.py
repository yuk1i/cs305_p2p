from __future__ import annotations

from torrent import Torrent, FileObject
import os
import pickle
import threading
from utils.path_utils import *

from typing import Dict

'''
考虑加指定torrent中要下载的文件功能，先摸了
'''

FILE_POSTFIX = '.ls'


class DirectoryController:
    """
    Extract and store all information about files in the torrent *locally* in this class
    """
    def __init__(self, torrent: Torrent, torrent_file_path: str, save_dir: str = '.'):
        self._active = True
        self.torrent = torrent
        self.save_dir = save_dir
        self.fseq2file: Dict[int, FileObject] = {}
        self.fseq2fpath: Dict[int, str] = {}
        self.bseq2fseq: Dict[int, int] = {}  # map block to file relative path
        for file in self.torrent.files:
            self.fseq2file[file.seq] = file
            self.fseq2fpath[file.seq] = pathjoin(file.dir, file.name)
            for block in file.blocks:
                self.bseq2fseq[block.seq] = file.seq
        self.build_torrent_directory_structure()
        self.local_state_path = torrent_file_path + FILE_POSTFIX
        self.local_state: TorrentLocalState = None
        if os.path.exists(self.local_state_path):
            try:
                self.local_state = self._init_local_state()
            except Exception:
                pass
        if not self.local_state:
            self.local_state = TorrentLocalState()
        self.local_state_lock = threading.Lock()
        self.loop_save_thread: threading.Thread = threading.Thread(target=self._loop_save_local_state)
        self.loop_save_thread_waiter = threading.Condition()
        self.loop_save_thread.start()
        self.auto_save_interval = 30
        self.auto_save_thread: threading.Thread = threading.Thread(target=self._auto_save_local_state)
        self.auto_save_thread.setDaemon(True)
        self.auto_save_thread.start()

    def build_torrent_directory_structure(self):
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        for file in self.torrent.files:
            rel_dir = file.dir
            if not os.path.exists(rel_dir):
                os.makedirs(rel_dir)
            rel_path = pathjoin(rel_dir, file.name)
            self._allocate_file(rel_path, file.size)

    def retrieve_block(self, block_seq: int) -> bytes:
        if block_seq not in self.local_state.local_block or block_seq > self.torrent.block_count:
            return b''
        save_file_path = self._get_save_file_path(self.fseq2fpath[self.bseq2fseq[block_seq]])
        offset = self.torrent.block_size * (block_seq - self.fseq2file[self.bseq2fseq[block_seq]].first_block_seq)
        with open(save_file_path, 'rb') as f:
            f.seek(offset)
            return f.read(self.torrent.block_size)

    def save_block(self, block_seq: int, data: bytes) -> bool:
        if block_seq in self.local_state.local_block or block_seq > self.torrent.block_count:
            return False
        save_file_path = self._get_save_file_path(self.fseq2fpath[self.bseq2fseq[block_seq]])
        offset = self.torrent.block_size * (block_seq - self.fseq2file[self.bseq2fseq[block_seq]].first_block_seq)
        with open(save_file_path, 'ab') as f:
            f.seek(offset)
            f.write(data)
            self._update_local_state(block_seq)
        return True

    def match_wanted_block(self, offered_block: set):
        return offered_block.difference(self.local_state.local_block)

    def _init_local_state(self):
        with open(self.local_state_path, 'rb') as fp:
            return pickle.load(fp)

    def _save_local_state(self):
        # self.loop_save_thread_waiter.acquire()
        with self.loop_save_thread_waiter:
            self.loop_save_thread_waiter.notify()
        pass

    def _loop_save_local_state(self):
        while self._active:
            # self.loop_save_thread_waiter.acquire()
            with self.loop_save_thread_waiter:
                self.loop_save_thread_waiter.wait()
            self.local_state_lock.acquire()
            with open(self.local_state_path, 'wb') as fp:
                pickle.dump(self.local_state, fp)
            self.local_state_lock.release()

    def _update_local_state(self, block_seq: int):
        self.local_state_lock.acquire()
        self.local_state.local_block.add(block_seq)
        self.local_state_lock.release()

    def _auto_save_local_state(self):
        while self._active:
            timer = threading.Timer(self.auto_save_interval, self._save_local_state)
            timer.setDaemon(True)
            timer.start()
            timer.join()

    def _allocate_file(self, rel_path: str, size: int):
        save_path = self._get_save_file_path(rel_path)
        if os.path.exists(save_path):
            pass
        else:
            with open(save_path, 'wb') as f:
                f.seek(size - 1)
                f.write(b'\x00')

    def close(self):
        self._active = False
        # self.auto_save_thread.join()
        self._save_local_state()
        self.loop_save_thread.join()

    def _get_save_file_path(self, file_path):
        """
        :param file_path: file path relative to save path (torrent files base path)
        :return: file path to save to
        """
        return pathjoin(self.save_dir, file_path)


class TorrentLocalState:

    local_block = set()
    # file_index = list()
