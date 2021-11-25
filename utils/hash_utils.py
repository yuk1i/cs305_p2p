import hashlib
import json


def __get_hasher__():
    m = hashlib.sha256()
    return m


def hash_bytes(data: bytes) -> str:
    m = __get_hasher__()
    m.update(data)
    return m.hexdigest()


def hash_str(data: str) -> str:
    m = __get_hasher__()
    m.update(data.encode(encoding="utf8"))
    return m.hexdigest()


def hash_file(file_path: str) -> str:
    m = __get_hasher__()
    with open(file_path, "rb") as f:
        for byte in iter(lambda: f.read(4096), b''):
            m.update(byte)
    return m.hexdigest()


def hash_json_object(json_obj: dict) -> str:
    json_str = json.dumps(json_obj, sort_keys=True)
    # print(json_str)
    return hash_str(json_str)


def hash_json_array(json_array: list) -> str:
    json_str = json.dumps(json_array, sort_keys=True)
    return hash_str(json_str)
