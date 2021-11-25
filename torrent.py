import copy
import json
from typing import List

from utils.MyDict import MyDict

from utils.hash_utils import hash_str, hash_file, hash_bytes, hash_json_object, hash_json_array


class BlockObject(MyDict):
    def __init__(self):
        super().__init__()
        self.seq: int = 0
        self.size: int = 0
        self.hash: str = ""


class FileObject(MyDict):
    TYPE_FILE = "file"
    TYPE_FOLDER = "folder"

    def __init__(self, name: str, ftype: str):
        super().__init__()
        self.type: str = ftype
        self.name: str = name
        self.size: int = 0
        self.hash: str = ""
        self.blocks: List[BlockObject] = list()
        self.subfiles: List[FileObject] = list()


class Torrent(MyDict):
    def __init__(self):
        super().__init__()
        self.name: str = ""
        self.hash: str = ""
        self.files: List[FileObject] = list()

    def load_from_file(self, file_path: str) -> None:
        pass

    def check_torrent_hash(self) -> bool:
        current_hash = copy.deepcopy(self.hash)
        self.hash = ""
        print("old hash: %s" % current_hash)
        new_hash = hash_json_object(self)
        print("old hash: %s, new hash: %s" % (current_hash, new_hash))
        self.hash = current_hash
        return current_hash == new_hash

    def generate_hash(self) -> str:
        self.hash = ""
        self.hash = hash_json_object(self)
        return self.hash


if __name__ == '__main__':
    fo = FileObject("test", FileObject.TYPE_FILE)
    print(fo)
    print(json.dumps(fo))
    print(hash_json_object(fo))
    t = Torrent()
    t.name = "114514"
    t.generate_hash()
    print(t.check_torrent_hash())
