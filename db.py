import os
from datetime import datetime
import config
import mysql.connector


def get_connection():
  return mysql.connector.connect(
      host=config.DB_HOST,
      user=config.DB_USER,
      password=config.DB_PASSWORD,
      database=config.DB_NAME,
      use_pure=True,  # Menghindari fatal crash connection_cext di Windows
  )


connect_db = get_connection


def _jalankan(query, params=(), ambil=None, commit=False):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params)
        hasil = None
        if ambil == "satu":
            hasil = cur.fetchone()
        elif ambil == "semua":
            hasil = cur.fetchall()
        if commit:
            conn.commit()
        cur.close()
        return hasil
    finally:
        conn.close()


def init_db():
    """Membuat folder storage dan memastikan koneksi aman."""
    os.makedirs(config.STORAGE_DIR, exist_ok=True)
    conn = get_connection()
    conn.close()


def tambah_pengguna(username, password_hash, salt, role, face_encoding=""):
    """Menyimpan pengguna baru lengkap dengan face_encoding ke tabel `pengguna`."""
    role_enum = (
        "Petugas Lapangan"
        if role.lower() in ["operator", "petugas lapangan"]
        else "Verifikator"
    )
    query = """
        INSERT INTO pengguna (username, password_hash, salt_key, face_encoding, role_akses)
        VALUES (%s, %s, %s, %s, %s)
    """
    _jalankan(query, (username, password_hash, salt, face_encoding, role_enum), commit=True)


def ambil_pengguna(username):
    """Mengambil record data pengguna berdasarkan username."""
    user = _jalankan(
        "SELECT * FROM pengguna WHERE username = %s", (username,), ambil="satu"
    )
    if user:
        user["salt"] = user["salt_key"]
        user["role"] = (
            "operator"
            if user["role_akses"] == "Petugas Lapangan"
            else "verifikator"
        )
    return user


def simpan_permohonan(data: dict) -> int:
    """Menyimpan izin ke tabel `permohonan` dengan parameter tuple (aman untuk pure python)."""
    tgl = data.get("tanggal_pengajuan") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    query = """
        INSERT INTO permohonan (
            no_registrasi, nama_pemohon, jenis_bangunan, luas_bangunan,
            status_permohonan, tanggal_pengajuan, nik_pemohon_enc, alamat_enc,
            no_telepon_enc, koordinat_tanah_enc, uraian_permohonan_enc, id_petugas
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    params = (
        str(data["no_registrasi"]),
        str(data["nama_pemohon"]),
        str(data["jenis_bangunan"]),
        float(data["luas_bangunan"]),
        'Menunggu Verifikasi',
        tgl,
        str(data["nik_pemohon_enc"]),
        str(data["alamat_enc"]),
        str(data.get("no_telepon_enc", "")),
        str(data.get("koordinat_tanah_enc", "")),
        str(data.get("uraian_permohonan_enc", "")),
        int(data.get("id_petugas", 1))
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id
    finally:
        conn.close()


def simpan_berkas(no_registrasi: str, path_ktp_enc: str, hash_ktp: str,
                  path_shm_enc: str, hash_shm: str, path_denah_lsb: str,
                  kode_segel: str, path_sk_enc: str = None):
    """Menyimpan berkas lampiran ke tabel `berkas`."""
    query = """
        INSERT INTO berkas (
            no_registrasi, path_ktp_enc, hash_ktp, path_shm_enc, hash_shm,
            path_sk_enc, path_denah_lsb, kode_segel
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    _jalankan(query, (no_registrasi, path_ktp_enc, hash_ktp, path_shm_enc,
                      hash_shm, path_sk_enc, path_denah_lsb, kode_segel), commit=True)


def simpan_blok(blok: dict):
    """Menyimpan blok ke tabel `blockchain_log` menggunakan tuple parameter."""
    tgl = blok.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = """
        INSERT INTO blockchain_log (
            timestamp, no_registrasi, id_user, hash_dokumen, prev_hash, curr_hash
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        tgl,
        str(blok["no_registrasi"]),
        int(blok.get("id_user", 1)),
        str(blok["hash_dokumen"]),
        str(blok["prev_hash"]),
        str(blok["curr_hash"])
    )
    _jalankan(query, params, commit=True)


def semua_blok():
    """Mengambil riwayat blockchain dari tabel `blockchain_log`."""
    return _jalankan(
        "SELECT * FROM blockchain_log ORDER BY id_blok ASC", ambil="semua"
    )

def reset_semua_tabel():
    """
    Mengosongkan isi seluruh tabel utama (berkas, blockchain_log, permohonan)
    tanpa menghapus struktur tabelnya, serta mereset auto-increment ID.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        cur.execute("TRUNCATE TABLE berkas;")
        cur.execute("TRUNCATE TABLE blockchain_log;")
        cur.execute("TRUNCATE TABLE permohonan;")
        cur.execute("TRUNCATE TABLE pengguna;")

        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        conn.commit()
        cur.close()
        print("[INFO] Seluruh data tabel berhasil dikosongkan!")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Gagal mengosongkan tabel: {e}")
        raise e
    finally:
        conn.close()