"""SHA-256: kata sandi (+ salt) dan hash berkas."""
import hashlib
import hmac
import os


def hash_password(password: str):
    """Kembalikan (salt_hex, hash_hex); keduanya disimpan di tabel petugas."""
    salt = os.urandom(16)
    h = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return salt.hex(), h


def cek_password(password: str, salt_hex: str, hash_tersimpan: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    h = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(h, hash_tersimpan)


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: str) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for potongan in iter(lambda: f.read(8192), b""):
            sha.update(potongan)
    return sha.hexdigest()
