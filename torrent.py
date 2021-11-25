from __future__ import annotations

import copy
import json
import os
import pprint
from typing import List
from utils.MyDict import MyDict
from utils import hash_utils


class SeqGenerator:
    def __init__(self):
        self.value: int = 0

    def get(self):
        return self.value

    def increment_and_get(self):
        self.value += 1
        return self.value


class BlockObject(MyDict):
    def __init__(self):
        super().__init__()
        self.seq: int = 0
        self.size: int = 0
        self.hash: str = ""

    def check_block(self, data: bytes) -> bool:
        return len(data) == self.size and hash_utils.hash_bytes(data) == self.hash


class FileObject(MyDict):
    def __init__(self, seq: int, name: str, sdir: str):
        super().__init__()
        self.seq: int = seq
        self.name: str = name
        self.dir: str = sdir
        self.size: int = 0
        self.hash: str = ""
        self.blocks: List[BlockObject] = list()

    def calculate_blocks(self, abs_path: str, block_size: int, seq: SeqGenerator):
        with open(abs_path, "rb") as f:
            self.size = 0
            hasher = hash_utils.__get_hasher__()
            while True:
                chunk = f.read(block_size)
                if chunk == b'':
                    break
                hasher.update(chunk)
                self.size += len(chunk)
                b = BlockObject()
                b.size = len(chunk)
                b.seq = seq.increment_and_get()
                b.hash = hash_utils.hash_bytes(chunk)
                self.blocks.append(b)
            self.hash = hasher.hexdigest()

    def check_file(self, abs_path: str):
        pass


class Torrent(MyDict):
    def __init__(self):
        super().__init__()
        self.name: str = ""
        self.torrent_hash: str = ""
        self.block_size: int = 4096
        self.files: List[FileObject] = list()

    def check_torrent_hash(self) -> bool:
        current_hash = copy.deepcopy(self.torrent_hash)
        self.torrent_hash = ""
        print("old hash: %s" % current_hash)
        new_hash = hash_utils.hash_json_object(self)
        print("old hash: %s, new hash: %s" % (current_hash, new_hash))
        self.torrent_hash = current_hash
        return current_hash == new_hash

    def generate_hash(self) -> str:
        self.torrent_hash = ""
        self.torrent_hash = hash_utils.hash_json_object(self)
        return self.torrent_hash

    @staticmethod
    def load_from_file(file_path: str) -> Torrent:
        pass

    @staticmethod
    def generate_torrent(path: str, name: str, block_size: int = 4096) -> Torrent:
        """
        Generate A Torrent Object according to the `path` folder
        :param path: must be a folder, support both relative path and absolute path
        :param name: torrent name
        :param block_size: block size in bytes, default value: 4096 bytes
        :return: A Torrent Object
        """
        tt = Torrent()
        tt.name = name
        tt.block_size = block_size
        file_seq = SeqGenerator()
        block_seq = SeqGenerator()
        # recursively traverse directory
        for dirpath, dirnames, filenames in os.walk(path):
            relative = os.path.relpath(dirpath, path)
            print("get relative path %s for path %s" % (relative, dirpath))
            for file in filenames:
                abs_dir = os.path.join(dirpath, file)
                fo = FileObject(file_seq.increment_and_get(), file, relative)
                fo.calculate_blocks(abs_dir, tt.block_size, block_seq)
                tt.files.append(fo)
        tt.generate_hash()
        return tt

    def generate_index(self) -> None:
        """
        generate indexes for blocks and files, provide O(1)'s access to a File Object and Block Object
        :return:
        """
        pass

    def get_block(self, seq_number: int) -> BlockObject:
        pass

    def get_file(self, seq_number: int) -> FileObject:
        pass


if __name__ == '__main__':
    # fo = FileObject(1, "test", "test_dir")
    # print(fo)
    # print(json.dumps(fo))
    # print(hash_json_object(fo))
    # t = Torrent()
    # t.name = "114514"
    # t.generate_hash()
    # print(t.check_torrent_hash())

    tt = Torrent.generate_torrent("tests/test_torrent", "A Test Torrent")

    pprint.pprint(tt)
    print(tt.check_torrent_hash())
