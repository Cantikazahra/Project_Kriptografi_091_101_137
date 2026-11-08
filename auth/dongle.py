
import base64
import ctypes
import hashlib
import hmac
import json
import os

NAMA_FILE_DONGLE = "SIPAMAN_DONGLE.key"
NAMA_REGISTRY = "dongle_registry.json"
DRIVE_REMOVABLE = 2


def daftar_drive_usb():
    """Mendeteksi seluruh drive flashdisk/removable di sistem Windows."""
    if os.name != "nt":
        return []
    hasil = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            root = f"{chr(65 + i)}:\\"
            if ctypes.windll.kernel32.GetDriveTypeW(root) == DRIVE_REMOVABLE:
                hasil.append(root)
    return hasil


def _sidik_jari(kunci: bytes) -> str:
    return hashlib.sha256(kunci).hexdigest()


def _tanda_tangan(kunci: bytes, key_id: str, dibuat: str) -> str:
    pesan = f"{key_id}|{dibuat}".encode()
    return hmac.new(kunci, pesan, hashlib.sha256).hexdigest()


def muat_kunci_dongle(path_registry: str = None) -> bytes | None:
    """Membaca dongle fisik, mencocokkan signature & hash registry, lalu mengembalikan master key (bytes).

    Mengembalikan None jika dongle tidak sah / tidak tertancap.
    """
    if path_registry is None:
        # Menyesuaikan letak root project (1 tingkat di atas folder auth)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path_registry = os.path.join(root_dir, NAMA_REGISTRY)

    if not os.path.exists(path_registry):
        return None

    try:
        with open(path_registry, encoding="utf-8") as f:
            registry = json.load(f)
    except Exception:
        return None

    for drive in daftar_drive_usb():
        path = os.path.join(drive, NAMA_FILE_DONGLE)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            kunci = base64.b64decode(data["master_key"])
            ok_ttd = hmac.compare_digest(
                data["tanda_tangan"],
                _tanda_tangan(kunci, data["key_id"], data["dibuat"]),
            )
            ok_hash = hmac.compare_digest(
                _sidik_jari(kunci), registry["sidik_jari_sha256"]
            )
            if data.get("magic") == "SIPAMAN-DONGLE" and ok_ttd and ok_hash:
                return kunci
        except (ValueError, KeyError, OSError):
            continue

    return None


def cek_keberadaan_dongle() -> bool:
    """Helper boolean cepat untuk pengecekan status di UI/Login."""
    return muat_kunci_dongle() is not None