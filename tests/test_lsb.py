import os
import tempfile
import unittest
from PIL import Image
from kripto.lsb import sisip_pesan, ekstrak_pesan


class TestLSB(unittest.TestCase):
    def test_sisip_dan_ekstrak(self):
        with tempfile.TemporaryDirectory() as d:
            asli, hasil = os.path.join(d, "a.png"), os.path.join(d, "b.png")
            Image.frombytes("RGB", (100, 100), os.urandom(100 * 100 * 3)).save(asli)
            pesan = "IZIN-2026-001|OP-07"
            sisip_pesan(asli, pesan, hasil)
            self.assertEqual(ekstrak_pesan(hasil), pesan)
            # perubahan tiap nilai warna paling banyak 1
            a, b = Image.open(asli).tobytes(), Image.open(hasil).tobytes()
            self.assertLessEqual(max(abs(x - y) for x, y in zip(a, b)), 1)

    def test_gambar_tanpa_pesan(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "polos.png")
            Image.new("RGB", (50, 50), (10, 20, 30)).save(p)
            self.assertIsNone(ekstrak_pesan(p))

    def test_pesan_terlalu_panjang(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "kecil.png")
            Image.new("RGB", (5, 5)).save(p)
            with self.assertRaises(ValueError):
                sisip_pesan(p, "x" * 100, os.path.join(d, "o.png"))


if __name__ == "__main__":
    unittest.main()
