import unittest
from kripto.hashing import hash_password, cek_password, hash_bytes


class TestHashing(unittest.TestCase):
    def test_password_benar_salah(self):
        salt, h = hash_password("rahasia123")
        self.assertTrue(cek_password("rahasia123", salt, h))
        self.assertFalse(cek_password("salah", salt, h))

    def test_salt_membuat_hash_beda(self):
        self.assertNotEqual(hash_password("sama")[1], hash_password("sama")[1])

    def test_sha256_standar(self):
        self.assertEqual(hash_bytes(b"abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


if __name__ == "__main__":
    unittest.main()
