"""Penurunan kunci dari isi dongle (PBKDF2-HMAC-SHA256).

Satu rahasia (isi dongle_key.dat) menghasilkan kunci berbeda untuk tiap tujuan,
sehingga tanpa dongle data tidak bisa didekripsi.
"""
import hashlib

_SALT_DASAR = b"SIPAMAN-v1"
_ITERASI = 100_000


def turunkan_kunci(rahasia: bytes, tujuan: str, panjang: int = 32) -> bytes:
    salt = _SALT_DASAR + b":" + tujuan.encode()
    return hashlib.pbkdf2_hmac("sha256", rahasia, salt, _ITERASI, dklen=panjang)


def kunci_aes(rahasia: bytes) -> bytes:        # 32 byte = AES-256
    return turunkan_kunci(rahasia, "aes", 32)


def kunci_rc4(rahasia: bytes) -> bytes:        # 16 byte
    return turunkan_kunci(rahasia, "rc4", 16)


def kunci_vigenere(rahasia: bytes, panjang: int = 12) -> str:
    """Kunci Vigenere harus huruf saja: ubah tiap byte menjadi A-Z."""
    turunan = turunkan_kunci(rahasia, "vigenere", panjang)
    return "".join(chr(b % 26 + ord("A")) for b in turunan)
