import unittest
from torrent import Torrent, BlockObject, FileObject


class MyTestCase(unittest.TestCase):
    def test_check_torrent_hash(self):
        t = Torrent()
        t.name = "114514"
        t.generate_hash()
        self.assertTrue(t.check_torrent_hash())

    def test_check_generate(self):
        tt = Torrent.generate_torrent("test_torrent", "A Test Torrent")
        self.assertEqual(tt.torrent_hash, "4f764225a35635732db31948ce19f6d70c8ccddd66e6c120c06efc20a24c4423")

    def test_check_save_and_load(self):
        tt = Torrent.generate_torrent("test_torrent", "A Test Torrent")
        tt.save_to_file("excluded/my1.torrent")
        tt2 = Torrent.load_from_file("excluded/my1.torrent")
        self.assertEqual(tt2.torrent_hash, "4f764225a35635732db31948ce19f6d70c8ccddd66e6c120c06efc20a24c4423")


if __name__ == '__main__':
    unittest.main()
