import os
import tempfile
import unittest
import db
from kripto.blockchain import Blockchain


class TestBlockchain(unittest.TestCase):
    def buat(self):
        bc = Blockchain()
        bc.tambah("REG-001", "Budi Santoso", "a" * 64, "operator.sipaman")
        bc.tambah("REG-002", "Siti Aminah", "b" * 64, "operator.sipaman")
        return bc

    def test_rantai_valid(self):
        self.assertEqual(self.buat().valid(), (True, None))

    def test_data_diubah_terdeteksi(self):
        bc = self.buat()
        bc.chain[1].payload_hash = "c" * 64      # manipulasi
        self.assertEqual(bc.valid(), (False, 1))

    def test_simpan_dan_muat_dari_db(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "uji.db")
            db.init_db(path)
            bc = self.buat()
            for blok in bc.chain:
                db.simpan_blok(blok.to_dict(), path)
            muat = Blockchain(db.semua_blok(path))
            self.assertEqual(len(muat.chain), 3)
            self.assertEqual(muat.valid(), (True, None))

    def test_petugas(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "uji.db")
            db.init_db(path)
            db.tambah_petugas("andi", "hash", "salt", "operator", path=path)
            self.assertEqual(db.ambil_petugas("andi", path=path)["role"], "operator")
            self.assertIsNone(db.ambil_petugas("tidak_ada", path=path))


if __name__ == "__main__":
    unittest.main()
