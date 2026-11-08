"""RC4 (stream cipher) untuk enkripsi berkas lampiran.

Catatan: RC4 punya kelemahan jika kunci yang sama dipakai berulang. Karena itu
tiap berkas diberi nonce acak 16 byte; kunci RC4 = kunci + nonce.
RC4 tidak punya autentikasi, jadi keaslian berkas dicek lewat hash di blockchain.
"""
import os


def ksa(key: bytes) -> list:
    """Key Scheduling Algorithm: permutasi awal array S."""
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    return s


def prga(s: list, panjang: int) -> bytearray:
    """Pseudo-Random Generation Algorithm: hasilkan keystream."""
    i = j = 0
    keluar = bytearray(panjang)
    for n in range(panjang):
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        keluar[n] = s[(s[i] + s[j]) % 256]
    return keluar


def rc4(data: bytes, key: bytes) -> bytes:
    """Enkripsi = dekripsi (XOR dengan keystream)."""
    ks = prga(ksa(key), len(data))
    return bytes(a ^ b for a, b in zip(data, ks))


def rc4_encrypt(data: bytes, key: bytes) -> bytes:
    nonce = os.urandom(16)
    return nonce + rc4(data, key + nonce)


def rc4_decrypt(blob: bytes, key: bytes) -> bytes:
    nonce, isi = blob[:16], blob[16:]
    return rc4(isi, key + nonce)


def enkripsi_berkas(path_asli: str, path_enc: str, key: bytes) -> None:
    with open(path_asli, "rb") as f:
        data = f.read()
    with open(path_enc, "wb") as f:
        f.write(rc4_encrypt(data, key))


def dekripsi_berkas(path_enc: str, path_hasil: str, key: bytes) -> None:
    with open(path_enc, "rb") as f:
        blob = f.read()
    with open(path_hasil, "wb") as f:
        f.write(rc4_decrypt(blob, key))
