"""Blockchain sederhana (SHA-256). Kolom blok mengikuti tabel ledger di laporan."""
import hashlib
from datetime import datetime


class Block:
    def __init__(self, block_index=0, timestamp="", no_resi="", nama_pemohon="",
                 payload_hash="", id_petugas=1, previous_hash="", current_hash=None, **kwargs):
        # Tangani jika nama kolom di database memakai format berbeda
        self.block_index = block_index or kwargs.get("id_blok", 0)
        self.timestamp = str(timestamp or kwargs.get("created_at", ""))
        self.no_resi = str(no_resi or kwargs.get("no_registrasi", ""))
        self.nama_pemohon = str(nama_pemohon or kwargs.get("nama", ""))
        self.payload_hash = str(payload_hash or kwargs.get("hash_dokumen", ""))
        self.id_petugas = id_petugas or kwargs.get("id_user", 1)
        self.previous_hash = str(previous_hash or kwargs.get("prev_hash", ""))
        self.current_hash = current_hash or kwargs.get("curr_hash") or self.hitung_hash()

    def hitung_hash(self) -> str:
        isi = "|".join(str(x) for x in (
            self.block_index, self.timestamp, self.no_resi, self.nama_pemohon,
            self.payload_hash, self.id_petugas, self.previous_hash))
        return hashlib.sha256(isi.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return dict(self.__dict__)


class Blockchain:
    def __init__(self, blok_tersimpan=None):
        """blok_tersimpan: list of dict dari basis data (urut block_index)."""
        if blok_tersimpan:
            self.chain = [Block(**b) for b in blok_tersimpan]
        else:
            self.chain = [Block(0, datetime.now().isoformat(timespec="seconds"),
                                "GENESIS", "-", "0" * 64, "-", "0" * 64)]

    def tambah(self, no_resi, nama_pemohon, payload_hash, id_petugas) -> Block:
        prev = self.chain[-1]
        blok = Block(len(self.chain), datetime.now().isoformat(timespec="seconds"),
                     no_resi, nama_pemohon, payload_hash, id_petugas,
                     prev.current_hash)
        self.chain.append(blok)
        return blok

    def valid(self):
        """Kembalikan (True, None) atau (False, nomor_blok_bermasalah)."""
        for i, blok in enumerate(self.chain):
            if blok.current_hash != blok.hitung_hash():
                return False, blok.block_index
            if i > 0 and blok.previous_hash != self.chain[i - 1].current_hash:
                return False, blok.block_index
        return True, None

    # Alias agar cocok jika dipanggil sebagai validasi_rantai
    def validasi_rantai(self):
        sukses, idx = self.valid()
        if sukses:
            return True, "Rantai blok valid."
        return False, f"Blok nomor {idx} tidak valid/termanipulasi!"

    def cari(self, no_resi):
        for blok in self.chain:
            if blok.no_resi == no_resi:
                return blok
        return None