import json
import os
import unittest
from utils.hash_utils import hash_str, hash_bytes, hash_file, hash_json_object, hash_json_array


class TestHash(unittest.TestCase):

    def test_str(self):
        s = "asdasdasd"
        SHA256 = hash_str(s)
        result = "d8a928b2043db77e340b523547bf16cb4aa483f0645fe0a290ed1f20aab76257"
        self.assertEqual(SHA256, result)

    def test_byte(self):
        s = "asdasdasd".encode(encoding="ascii")
        SHA256 = hash_bytes(s)
        result = "d8a928b2043db77e340b523547bf16cb4aa483f0645fe0a290ed1f20aab76257"
        self.assertEqual(SHA256, result)

    def test_file(self):
        with open("test", "wb") as f:
            f.write("asdasdasd".encode(encoding="ascii"))
        SHA256 = hash_file("test")
        result = "d8a928b2043db77e340b523547bf16cb4aa483f0645fe0a290ed1f20aab76257"
        self.assertEqual(SHA256, result)
        os.remove("test")

    def test_empty_file(self):
        open('empty_file', 'wb').close()
        hash = hash_file('empty_file')
        expected = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        self.assertEqual(hash, expected)
        os.remove('empty_file')

    def test_json_object(self):
        d = dict()
        d["test"] = "qwqwq"
        d["test2"] = 5
        d2 = dict()
        d2["test2"] = 5
        d2["test"] = "qwqwq"
        self.assertEqual(hash_json_object(d), hash_json_object(d2))

    def test_json_array(self):
        d = ["114514", 1123, "asdfhajsgajklsfh"]

        d2 = list()
        d2.append("114514")
        d2.append(1123)
        d2.append("asdfhajsgajklsfh")
        self.assertEqual(hash_json_array(d), hash_json_array(d2))

if __name__ == '__main__':
    unittest.main()
