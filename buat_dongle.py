import base64
import ctypes
import hashlib
import hmac
import json
import os
import secrets
import sys
from datetime import datetime, timezone

NAMA_FILE_DONGLE = "SIPAMAN_DONGLE.key"
NAMA_REGISTRY = "dongle_registry.json"  # simpan di project: hanya berisi sidik jari (hash), BUKAN kunci
DRIVE_REMOVABLE = 2

# ---------- Deteksi USB ----------
def daftar_drive_usb():
    """Kembalikan daftar drive removable (flashdisk) di Windows, mis. ['E:\\\\']."""
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


# ---------- Pembuatan kunci ----------
def _sidik_jari(kunci: bytes) -> str:
    return hashlib.sha256(kunci).hexdigest()


def _tanda_tangan(kunci: bytes, key_id: str, dibuat: str) -> str:
    pesan = f"{key_id}|{dibuat}".encode()
    return hmac.new(kunci, pesan, hashlib.sha256).hexdigest()


def buat_file_dongle(drive_root: str, simpan_registry_di: str = None):
    kunci = secrets.token_bytes(32)  # master key 256-bit untuk AES-256
    key_id = secrets.token_hex(8)
    dibuat = datetime.now(timezone.utc).isoformat()

    isi = {
        "magic": "SIPAMAN-DONGLE",
        "versi": 1,
        "key_id": key_id,
        "dibuat": dibuat,
        "master_key": base64.b64encode(kunci).decode(),
        "tanda_tangan": _tanda_tangan(kunci, key_id, dibuat),
    }

    path_dongle = os.path.join(drive_root, NAMA_FILE_DONGLE)
    if os.path.exists(path_dongle):
        raise FileExistsError(
            f"{path_dongle} sudah ada. Hapus manual jika memang ingin membuat ulang "
            "(data lama yang dienkripsi dengan kunci lama TIDAK bisa dibuka lagi)."
        )
    with open(path_dongle, "w", encoding="utf-8") as f:
        json.dump(isi, f, indent=2)

    # Sembunyikan file di Windows (opsional)
    if os.name == "nt":
        ctypes.windll.kernel32.SetFileAttributesW(path_dongle, 0x02)

    # Registry: server hanya menyimpan hash, bukan kunci
    folder = simpan_registry_di or os.path.dirname(os.path.abspath(__file__))
    path_registry = os.path.join(folder, NAMA_REGISTRY)
    with open(path_registry, "w", encoding="utf-8") as f:
        json.dump({"key_id": key_id, "sidik_jari_sha256": _sidik_jari(kunci)}, f, indent=2)

    return path_dongle, path_registry, key_id


# ---------- Pemeriksaan (dipakai juga oleh main.py saat login Verifikator) ----------
def muat_kunci_dongle(path_registry: str = None):
    """
    Cari dongle di semua drive USB, validasi, lalu kembalikan master key (bytes).
    Kembalikan None jika dongle tidak ada / tidak sah.
    """
    folder = os.path.dirname(os.path.abspath(__file__))
    path_registry = path_registry or os.path.join(folder, NAMA_REGISTRY)
    if not os.path.exists(path_registry):
        return None
    with open(path_registry, encoding="utf-8") as f:
        registry = json.load(f)

    for drive in daftar_drive_usb():
        path = os.path.join(drive, NAMA_FILE_DONGLE)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            kunci = base64.b64decode(data["master_key"])
            ok_ttd = hmac.compare_digest(
                data["tanda_tangan"], _tanda_tangan(kunci, data["key_id"], data["dibuat"])
            )
            ok_hash = hmac.compare_digest(_sidik_jari(kunci), registry["sidik_jari_sha256"])
            if data.get("magic") == "SIPAMAN-DONGLE" and ok_ttd and ok_hash:
                return kunci
        except (ValueError, KeyError, OSError):
            continue
    return None


# ---------- CLI ----------
def main():
    if "--verifikasi" in sys.argv:
        kunci = muat_kunci_dongle()
        if kunci:
            print("[✓] Dongle sah terdeteksi. Akses Verifikator diizinkan.")
        else:
            print("[!] Dongle tidak ditemukan / tidak sah. Akses ditolak.")
        return

    drives = daftar_drive_usb()
    if not drives:
        print("[!] Tidak ada flashdisk terdeteksi. Colokkan USB lalu jalankan ulang.")
        return

    print("Drive USB terdeteksi:")
    for i, d in enumerate(drives, 1):
        print(f"  {i}. {d}")
    pilih = input("Pilih nomor drive untuk dijadikan dongle: ").strip()
    try:
        drive = drives[int(pilih) - 1]
    except (ValueError, IndexError):
        print("[!] Pilihan tidak valid.")
        return

    try:
        p_dongle, p_reg, key_id = buat_file_dongle(drive)
    except FileExistsError as e:
        print(f"[!] {e}")
        return

    print(f"[✓] Dongle dibuat   : {p_dongle}")
    print(f"[✓] Registry server : {p_reg}")
    print(f"    Key ID          : {key_id}")
    print("\nPENTING: buat cadangan flashdisk ini di tempat aman. Jika kunci hilang,")
    print("semua berkas stego yang sudah terenkripsi tidak dapat dibuka lagi.")


if __name__ == "__main__":
    main()