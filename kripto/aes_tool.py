"""AES-256 mode GCM dan super enkripsi (Vigenere -> AES-256)."""
import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from kripto.vigenere import vigenere_decrypt, vigenere_encrypt


def aes_encrypt(data: bytes, key: bytes) -> bytes:
    """key harus 32 byte. Hasil: nonce(12) + tag(16) + ciphertext."""
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return nonce + tag + ciphertext


def aes_decrypt(blob: bytes, key: bytes) -> bytes:
    """ValueError jika kunci salah atau data diubah."""
    nonce, tag, ciphertext = blob[:12], blob[12:28], blob[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


# --- Untuk kolom basis data (teks <-> Base64) ---
def enkripsi_atribut(teks: str, key: bytes) -> str:
    return base64.b64encode(aes_encrypt(teks.encode("utf-8"), key)).decode()


def dekripsi_atribut(b64: str, key: bytes) -> str:
    return aes_decrypt(base64.b64decode(b64), key).decode("utf-8")


# --- Super enkripsi: Vigenere (klasik) lalu AES-256 (modern) ---
def super_encrypt(teks: str, kunci_vigenere: str, kunci_aes: bytes) -> str:
    lapis1 = vigenere_encrypt(teks, kunci_vigenere)
    return enkripsi_atribut(lapis1, kunci_aes)


def super_decrypt(b64: str, kunci_vigenere: str, kunci_aes: bytes) -> str:
    lapis1 = dekripsi_atribut(b64, kunci_aes)
    return vigenere_decrypt(lapis1, kunci_vigenere)
