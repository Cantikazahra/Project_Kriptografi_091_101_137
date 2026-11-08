import os
import unittest
from kripto.rc4_tool import rc4, rc4_encrypt, rc4_decrypt


class TestRC4(unittest.TestCase):
    def test_vektor_standar(self):         # vektor uji RC4 yang umum dipakai
        self.assertEqual(rc4(b"Plaintext", b"Key").hex().upper(), "BBF316E8D940AF0AD3")

    def test_bolak_balik(self):
        data, key = os.urandom(5000), os.urandom(16)
        self.assertEqual(rc4_decrypt(rc4_encrypt(data, key), key), data)

    def test_nonce_membuat_hasil_beda(self):
        key = os.urandom(16)
        self.assertNotEqual(rc4_encrypt(b"sama", key), rc4_encrypt(b"sama", key))


if __name__ == "__main__":
    unittest.main()
