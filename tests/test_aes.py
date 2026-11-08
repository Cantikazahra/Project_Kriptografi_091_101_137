import os
import unittest
from kripto.aes_tool import (aes_encrypt, aes_decrypt, enkripsi_atribut,
                             dekripsi_atribut, super_encrypt, super_decrypt)
from kripto.keys import kunci_aes, kunci_vigenere


class TestAES(unittest.TestCase):
    def setUp(self):
        self.rahasia = b"isi-dongle-contoh"
        self.key = kunci_aes(self.rahasia)

    def test_panjang_kunci(self):
        self.assertEqual(len(self.key), 32)

    def test_bolak_balik(self):
        data = os.urandom(1000)
        self.assertEqual(aes_decrypt(aes_encrypt(data, self.key), self.key), data)

    def test_data_diubah_terdeteksi(self):
        blob = bytearray(aes_encrypt(b"rahasia", self.key))
        blob[-1] ^= 1
        with self.assertRaises(ValueError):
            aes_decrypt(bytes(blob), self.key)

    def test_kunci_salah(self):
        blob = aes_encrypt(b"rahasia", self.key)
        with self.assertRaises(ValueError):
            aes_decrypt(blob, kunci_aes(b"dongle-lain"))

    def test_atribut_db(self):
        self.assertEqual(dekripsi_atribut(enkripsi_atribut("3174090889000001", self.key), self.key),
                         "3174090889000001")

    def test_super_enkripsi(self):
        kv = kunci_vigenere(self.rahasia)
        teks = "Pembangunan rumah dua lantai, luas 245 m2."
        c = super_encrypt(teks, kv, self.key)
        self.assertNotIn("rumah", c)
        self.assertEqual(super_decrypt(c, kv, self.key), teks)


if __name__ == "__main__":
    unittest.main()
