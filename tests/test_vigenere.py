import unittest
from kripto.vigenere import vigenere_encrypt, vigenere_decrypt


class TestVigenere(unittest.TestCase):
    def test_contoh_manual(self):          # contoh di laporan: PBG + KUNCI -> ZVT
        self.assertEqual(vigenere_encrypt("PBG", "KUNCI"), "ZVT")

    def test_bolak_balik(self):
        teks = "Luas bangunan 245 m2, Jl. Melati No. 12!"
        self.assertEqual(vigenere_decrypt(vigenere_encrypt(teks, "RAHASIA"), "RAHASIA"), teks)

    def test_kunci_tidak_valid(self):
        with self.assertRaises(ValueError):
            vigenere_encrypt("abc", "K3NCI")


if __name__ == "__main__":
    unittest.main()
