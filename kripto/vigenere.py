"""Vigenere Cipher (kriptografi klasik). Hanya huruf A-Z/a-z yang diubah."""


def _cek_kunci(key: str) -> str:
    key = key.upper()
    if not key or not key.isalpha() or not key.isascii():
        raise ValueError("Kunci Vigenere harus berupa huruf A-Z saja")
    return key


def _proses(teks: str, key: str, arah: int) -> str:
    key = _cek_kunci(key)
    hasil, k = [], 0
    for ch in teks:
        if ch.isascii() and ch.isalpha():
            dasar = ord("A") if ch.isupper() else ord("a")
            geser = ord(key[k % len(key)]) - ord("A")
            hasil.append(chr((ord(ch) - dasar + arah * geser) % 26 + dasar))
            k += 1
        else:
            hasil.append(ch)  # angka, spasi, simbol tidak diubah
    return "".join(hasil)


def vigenere_encrypt(plaintext: str, key: str) -> str:
    return _proses(plaintext, key, +1)


def vigenere_decrypt(ciphertext: str, key: str) -> str:
    return _proses(ciphertext, key, -1)
