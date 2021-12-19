from __future__ import annotations

import time
from pathlib import Path

from torrent import Torrent, FileObject
from torrent_local_state import TorrentLocalState
import os
import pickle
import threading

from utils import hash_utils
from utils.path_utils import *

from typing import Dict, Set, List, BinaryIO

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
        self.torrent_block_count: int = 0
        self.fseq2file: Dict[int, FileObject] = {}
        self.fseq2fpath: Dict[int, str] = {}
        self.bseq2fseq: Dict[int, int] = {}  # map block to file relative path
        self.local_state_path = torrent_file_path + FILE_POSTFIX
        self.local_state: TorrentLocalState = None
        self.opened_files: Dict[int, BinaryIO] = dict()
        # if os.path.exists(self.local_state_path):
        #     try:
        #         self.local_state = self._init_local_state()
        #     except Exception:
        #         pass
        if not self.local_state:
            self.local_state = TorrentLocalState()
        if not self.torrent.dummy:
            self.update()
            self.check_all_hash()
            self.calc_all_downloaded_blocks()
        self.local_state_lock = threading.Lock()
        self.write_lock = threading.Lock()
        # self.loop_save_thread: threading.Thread = threading.Thread(target=self._loop_save_local_state)
        # self.loop_save_thread_waiter = threading.Condition()
        # self.loop_save_thread.start()
        # self.auto_save_interval = 30
        # self.auto_save_thread: threading.Thread = threading.Thread(target=self._auto_save_local_state)
        # self.auto_save_thread.daemon = True
        # self.auto_save_thread.start()

    def update(self):
        self.torrent_block_count = 0
        for file in self.torrent.files:
            self.torrent_block_count += len(file.blocks)
            self.fseq2file[file.seq] = file
            self.fseq2fpath[file.seq] = os.path.normpath(pathjoin(file.dir, file.name))
            for block in file.blocks:
                self.bseq2fseq[block.seq] = file.seq

    def calc_all_downloaded_blocks(self):
        for file in self.torrent.files:
            save_path = self._get_save_file_path(self.fseq2fpath[file.seq])
            if not os.path.exists(save_path):
                continue
            with open(save_path, "rb") as f:
                for b in file.blocks:
                    chunk = f.read(self.torrent.block_size)
                    if chunk == b'':
                        break
                    if hash_utils.hash_bytes(chunk) == b.hash:
                        self.local_state.local_block.add(b.seq)

    def build_torrent_directory_structure(self):
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        for file in self.torrent.files:
            rel_dir = file.dir
            if not os.path.exists(os.path.normpath(os.path.join(self.save_dir, file.dir))):
                os.makedirs(os.path.normpath(os.path.join(self.save_dir, file.dir)))
            rel_path = pathjoin(rel_dir, file.name)
            self._allocate_file(file.seq, rel_path, file.size)

    def check_file_hash(self, fseq: int) -> bool:
        if self.torrent.dummy:
            raise Exception("Torrent data not available")
        fo: FileObject = self.torrent.get_file(fseq)
        if fo is None:
            return False
        save_path = self._get_save_file_path(self.fseq2fpath[fseq])
        if not os.path.exists(save_path):
            return False
        return hash_utils.hash_file(save_path) == fo.hash

    def check_chunk_hash(self, bseq: int, bdata: bytes) -> bool:
        if self.torrent.dummy:
            raise Exception("Torrent data not available")
        bo = self.torrent.get_block(bseq)
        return hash_utils.hash_bytes(bdata) == bo.hash

    def check_all_hash(self) -> bool:
        if self.torrent.dummy:
            raise Exception("Torrent data not available")
        for f in self.torrent.files:
            if not self.check_file_hash(f.seq):
                print("file %s not matched" % f.name)
                fpath = self._get_save_file_path(self.fseq2fpath[f.seq])
                if not os.path.exists(fpath):
                    print("file %s not created" % fpath)
                    continue
                with open(fpath, "rb") as ff:
                    for b in f.blocks:
                        chunk = ff.read(self.torrent.block_size)
                        if chunk == b'':
                            break
                        if hash_utils.hash_bytes(chunk) != b.hash:
                            print("chunk seq %s not matched" % b.seq)
                return False
        return True

    def retrieve_block(self, block_seq: int) -> bytes:
        if block_seq not in self.local_state.local_block or block_seq > self.torrent_block_count:
            return b''
        offset = self.torrent.block_size * (block_seq - self.fseq2file[self.bseq2fseq[block_seq]].blocks[0].seq)
        if self.bseq2fseq[block_seq] not in self.opened_files:
            self.open_files()
        with self.write_lock:
            f = self.opened_files[self.bseq2fseq[block_seq]]
            f.seek(offset)
            data = f.read(self.torrent.block_size)
        return data

    def save_block(self, block_seq: int, data: bytes) -> bool:
        """
        Save binary data for a block and save to local state, please check its hash first!!!
        :param block_seq:
        :param data:
        :return:
        """
        if block_seq in self.local_state.local_block or block_seq > self.torrent_block_count:
            print("block skipped for %s" % block_seq)
            return False
        offset = self.torrent.block_size * (block_seq - self.torrent.get_file(self.bseq2fseq[block_seq]).blocks[0].seq)
        with self.write_lock:
            f = self.opened_files[self.bseq2fseq[block_seq]]
            f.seek(offset, 0)
            f.write(data)
            self._update_local_state(block_seq)
        return True

    @property
    def download_completed(self):
        return len(self.local_state.local_block) == self.torrent_block_count

    def _init_local_state(self):
        with open(self.local_state_path, 'rb') as fp:
            return pickle.load(fp)

    # def _save_local_state(self):
    #     with self.loop_save_thread_waiter:
    #         self.loop_save_thread_waiter.notify()
    #     pass
    #
    # def _loop_save_local_state(self):
    #     while self._active:
    #         with self.loop_save_thread_waiter:
    #             self.loop_save_thread_waiter.wait()
    #         with self.local_state_lock:
    #             with open(self.local_state_path, 'wb') as fp:
    #                 pickle.dump(self.local_state, fp)

    def _update_local_state(self, block_seq: int):
        with self.local_state_lock:
            self.local_state.local_block.add(block_seq)

    # def _auto_save_local_state(self):
    #     while self._active:
    #         timer = threading.Timer(self.auto_save_interval, self._save_local_state)
    #         timer.daemon = True
    #         timer.start()
    #         timer.join()

    def _allocate_file(self, fseq: int, rel_path: str, size: int):
        if fseq in self.opened_files:
            self.opened_files[fseq].close()
        save_path = self._get_save_file_path(rel_path)
        Path(save_path).touch()
        self.opened_files[fseq] = open(save_path, "rb+")

    def close(self):
        self._active = False
        for f in self.opened_files.values():
            f.flush()
            # f.close()
        # self.auto_save_thread.join()
        # self._save_local_state()
        # self.loop_save_thread.join()

    def _get_save_file_path(self, file_path):
        """
        :param file_path: file path relative to save path (torrent files base path)
        :return: file path to save to
        """
        return os.path.normpath(pathjoin(self.save_dir, file_path))
        # Fix excluded/dummy/./qwq.txt

    def flush_all(self):
        with self.write_lock:
            for ff in self.opened_files.values():
                ff.flush()
        pass

    def open_files(self):
        for file in self.torrent.files:
            rel_dir = file.dir
            rel_path = pathjoin(rel_dir, file.name)
            save_path = self._get_save_file_path(rel_path)
            self.opened_files[file.seq] = open(save_path, "rb+")

    def get_tested_binary(self):
        # This function should only be used to work with School tests: one file, return binary direct
        with self.write_lock:
            self.opened_files[1].seek(0)
            return self.opened_files[1].read()
