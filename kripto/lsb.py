"""Steganografi LSB pada gambar (hasil wajib PNG)."""
from PIL import Image

PENANDA = b"#END#"   # penanda akhir pesan


def kapasitas_byte(path_gambar: str) -> int:
    img = Image.open(path_gambar)
    return (img.width * img.height * 3) // 8 - len(PENANDA)


def sisip_pesan(path_gambar: str, pesan: str, path_hasil: str) -> None:
    img = Image.open(path_gambar).convert("RGB")
    muatan = pesan.encode("utf-8") + PENANDA
    bit = [(b >> (7 - k)) & 1 for b in muatan for k in range(8)]
    data = bytearray(img.tobytes())
    if len(bit) > len(data):
        raise ValueError("Pesan terlalu panjang untuk gambar ini")
    for i, b in enumerate(bit):
        data[i] = (data[i] & 0xFE) | b           # ganti bit terakhir
    Image.frombytes("RGB", img.size, bytes(data)).save(path_hasil, "PNG")


def ekstrak_pesan(path_gambar: str):
    """Kembalikan pesan, atau None jika tidak ada penanda."""
    data = Image.open(path_gambar).convert("RGB").tobytes()
    hasil = bytearray()
    for i in range(0, len(data) - 7, 8):
        nilai = 0
        for k in range(8):
            nilai = (nilai << 1) | (data[i + k] & 1)
        hasil.append(nilai)
        if hasil.endswith(PENANDA):
            return bytes(hasil[:-len(PENANDA)]).decode("utf-8", errors="replace")
    return None
