from __future__ import annotations

import copy
import lzma
import json
import os
import pprint
from typing import List, Dict
from utils.MyDict import MyDict
from utils import hash_utils
from utils import path_utils


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
    def __init__(self, is_school_torrent: bool = False):
        super().__init__()
        self.name: str = ""
        self.torrent_hash: str = ""
        self.block_size: int = 4096
        self.files: List[FileObject] = list()
        self.__json_str__: str = ''
        self.__binary__: bytes = b''
        self.__dummy__ = False
        self.__bseq2bo__: Dict[int, BlockObject] = dict()
        self.__fseq2fo__: Dict[int, FileObject] = dict()
        self.__is_school_torrent__ = is_school_torrent

    @property
    def is_school_torrent(self) -> bool:
        return self.__is_school_torrent__

    @property
    def dummy(self):
        return self.__dummy__

    @property
    def binary(self) -> bytes:
        if self.__dummy__:
            raise Exception("not download yet")
        if not self.__binary__:
            self.__json_str__ = json.dumps(self, sort_keys=True)
            self.__binary__ = lzma.compress(self.__json_str__.encode(encoding='utf-8'))
        return self.__binary__

    def check_torrent_hash(self) -> bool:
        current_hash = self.torrent_hash
        self.torrent_hash = ""
        # print("old hash: %s" % current_hash)
        new_hash = hash_utils.hash_json_object(self)
        # print("old hash: %s, new hash: %s" % (current_hash, new_hash))
        self.torrent_hash = current_hash
        return current_hash == new_hash

    def generate_hash(self) -> str:
        self.torrent_hash = ""
        self.torrent_hash = hash_utils.hash_json_object(self)
        return self.torrent_hash

    def save_to_file(self, file_path: str) -> None:
        with open(file_path, "w") as f:
            f.write(json.dumps(self))

    def try_decode_from_binary(self, binary: bytes):
        self.__json_str__ = lzma.decompress(binary).decode(encoding='utf-8')
        tt = Torrent.load_from_content(self.__json_str__)
        if tt.torrent_hash != self.torrent_hash:
            raise Exception("Not the same torrent")
        self.name = tt.name
        self.files = tt.files
        self.block_size = tt.block_size

    @staticmethod
    def load_from_file(file_path: str) -> Torrent:
        with open(file_path, "r") as f:
            return Torrent.load_from_content(f.read())

    @staticmethod
    def load_from_content(content: str) -> Torrent:
        """
        :param content: torrent content str, should be decompressed first
        :return:
        """
        t = Torrent()
        j = json.loads(content)
        t.name = j["name"]
        t.torrent_hash = j["torrent_hash"]
        t.block_size = int(j["block_size"])
        for ff in j["files"]:
            f = FileObject(int(ff["seq"]), ff["name"], ff["dir"])
            f.size = int(ff["size"])
            f.hash = ff["hash"]
            for bb in ff["blocks"]:
                b = BlockObject()
                b.seq = int(bb["seq"])
                b.size = int(bb["size"])
                b.hash = bb["hash"]
                f.blocks.append(b)
            t.files.append(f)
        if not t.check_torrent_hash():  # check integrity
            raise AssertionError("Corrupt Torrent, hash mismatched")
        return t

    @staticmethod
    def generate_torrent(path: str, name: str, block_size: int = 4096) -> Torrent:
        """
        Generate A Torrent Object according to the `path` folder
        cannot save empty dir
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
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in path_utils.pathwalk(path):
                relative = os.path.relpath(dirpath, path)
                print("get relative path %s for path %s" % (relative, dirpath))
                for file in filenames:
                    abs_dir = path_utils.pathjoin(dirpath, file)
                    fo = FileObject(file_seq.increment_and_get(), file, relative)
                    fo.calculate_blocks(abs_dir, tt.block_size, block_seq)
                    tt.files.append(fo)
        else:
            # Single file
            print("Generate Torrent file for the single file")
            fo = FileObject(file_seq.increment_and_get(), os.path.basename(path), '.')
            fo.calculate_blocks(path, tt.block_size, block_seq)
            tt.files.append(fo)
        tt.generate_hash()
        return tt

    def generate_index(self) -> None:
        """
        generate indexes for blocks and files, provide O(1)'s access to a File Object and Block Object
        :return:
        """
        if self.dummy:
            raise Exception("Torrent data not available")
        for f in self.files:
            for b in f.blocks:
                self.__bseq2bo__[b.seq] = b
            self.__fseq2fo__[f.seq] = f

    def get_block(self, bseq: int) -> BlockObject:
        if self.dummy:
            raise Exception("Torrent data not available")
        if len(self.__bseq2bo__) == 0:
            self.generate_index()
        if bseq in self.__bseq2bo__:
            return self.__bseq2bo__[bseq]
        return None

    def get_file(self, fseq: int) -> FileObject:
        if self.dummy:
            raise Exception("Torrent data not available")
        if len(self.__fseq2fo__) == 0:
            self.generate_index()
        if fseq in self.__fseq2fo__:
            return self.__fseq2fo__[fseq]
        return None

    # def build_directory_structure(self, save_dir: str = ''):
    #     save_dir =
    #
    # @staticmethod
    # def build_directory(base_dir, dfiles: list):

    @staticmethod
    def create_dummy_torrent(torrent_hash: str) -> Torrent:
        t = Torrent()
        t.torrent_hash = torrent_hash
        t.__dummy__ = True
        return t

