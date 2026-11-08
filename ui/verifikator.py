import os
import sys
import time
import hashlib

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFrame, QMessageBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QTextEdit, QScrollArea
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
import config
import session
from kripto.keys import kunci_aes, kunci_vigenere
from kripto.aes_tool import super_decrypt
from kripto.rc4_tool import rc4_decrypt
from kripto.lsb import ekstrak_pesan, sisip_pesan
from kripto.blockchain import Blockchain


class VerifikatorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIPAMAN - Verificator Portal")
        self.showMaximized()
        self.setStyleSheet("background-color: #090d16; color: #f8fafc;")

        self.data_terpilih = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ================= 1. SIDEBAR KIRI =================
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #0f172a; border-right: 1px solid #1e293b;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(20, 30, 20, 20)

        title = QLabel("🛡️ SIPAMAN")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        sb_layout.addWidget(title)

        role_lbl = QLabel(f"Verificator: {session.Session.username or 'Verifikator'}")
        role_lbl.setStyleSheet("font-size: 13px; color: #94a3b8; font-weight: bold; margin-bottom: 20px;")
        sb_layout.addWidget(role_lbl)

        btn_audit = QPushButton("  🔗 Audit Blockchain")
        btn_audit.setStyleSheet("""
            QPushButton {
                text-align: left; padding: 12px; border-radius: 6px; 
                background-color: #1e293b; color: #38bdf8; font-size: 12px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #0c4a6e; }
        """)
        btn_audit.clicked.connect(self.audit_blockchain)
        sb_layout.addWidget(btn_audit)

        btn_refresh = QPushButton("  🔄 Muat Ulang Daftar")
        btn_refresh.setStyleSheet("""
            QPushButton {
                text-align: left; padding: 12px; border-radius: 6px; 
                background: transparent; color: #cbd5e1; font-size: 12px; border: none; margin-top: 5px;
            }
            QPushButton:hover { background-color: #1e293b; }
        """)
        btn_refresh.clicked.connect(self.muat_daftar_permohonan)
        sb_layout.addWidget(btn_refresh)

        btn_logout = QPushButton("  🚪 Logout / Keluar")
        btn_logout.setStyleSheet("""
            QPushButton {
                text-align: left; padding: 12px; border-radius: 6px; 
                background-color: transparent; color: #ef4444; font-size: 12px; font-weight: bold; 
                border: 1px solid #7f1d1d; margin-top: 10px;
            }
            QPushButton:hover { background-color: #7f1d1d; color: #ffffff; }
        """)
        btn_logout.clicked.connect(self.proses_logout)
        sb_layout.addWidget(btn_logout)

        sb_layout.addStretch()
        main_layout.addWidget(sidebar)

        # ================= 2. KONTEN KANAN (SCROLLABLE) =================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: #0b1120;")

        content = QWidget()
        content.setStyleSheet("background-color: #0b1120;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 25, 30, 25)

        h_title = QLabel("Daftar Pengajuan Izin Menunggu Verifikasi")
        h_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        content_layout.addWidget(h_title)

        # TABEL DAFTAR PERMOHONAN
        self.tabel = QTableWidget()
        self.tabel.setColumnCount(5)
        self.tabel.setHorizontalHeaderLabels(["No Registrasi", "Nama Pemohon", "Jenis Bangunan", "Tanggal Masuk", "Status"])
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabel.setFixedHeight(170)
        self.tabel.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a; border: 1px solid #1e293b; 
                border-radius: 8px; color: #f8fafc; gridline-color: #1e293b;
            }
            QHeaderView::section {
                background-color: #1e293b; color: #38bdf8; font-weight: bold; padding: 6px; border: none;
            }
            QTableWidget::item:selected { background-color: #0d9488; }
        """)
        self.tabel.itemClicked.connect(self.pilih_permohonan)
        content_layout.addWidget(self.tabel)

        # PANEL PRATINJAU DOKUMEN (KTP DEKRIPSI & DENAH LSB)
        preview_box = QFrame()
        preview_box.setStyleSheet("background-color: #0f172a; border-radius: 8px; border: 1px solid #1e293b; padding: 12px; margin-top: 10px;")
        preview_layout = QHBoxLayout(preview_box)

        # Kolom KTP
        ktp_col = QVBoxLayout()
        ktp_title = QLabel("📷 Pratinjau KTP (Hasil Dekripsi RC4)")
        ktp_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        self.lbl_preview_ktp = QLabel("Pilih permohonan & klik Dekripsi...")
        self.lbl_preview_ktp.setFixedSize(380, 210)
        self.lbl_preview_ktp.setAlignment(Qt.AlignCenter)
        self.lbl_preview_ktp.setStyleSheet("border: 1px dashed #334155; border-radius: 6px; background-color: #1e293b; color: #64748b;")
        ktp_col.addWidget(ktp_title)
        ktp_col.addWidget(self.lbl_preview_ktp)
        preview_layout.addLayout(ktp_col)

        # Kolom Denah
        denah_col = QVBoxLayout()
        denah_title = QLabel("🖼️ Pratinjau Denah (Steganografi LSB)")
        denah_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        self.lbl_preview_denah = QLabel("Pilih permohonan & klik Dekripsi...")
        self.lbl_preview_denah.setFixedSize(380, 210)
        self.lbl_preview_denah.setAlignment(Qt.AlignCenter)
        self.lbl_preview_denah.setStyleSheet("border: 1px dashed #334155; border-radius: 6px; background-color: #1e293b; color: #64748b;")
        denah_col.addWidget(denah_title)
        denah_col.addWidget(self.lbl_preview_denah)
        preview_layout.addLayout(denah_col)

        content_layout.addWidget(preview_box)

        # PANEL TEXT LOG AUDIT & SUPER-DEKRIPSI
        self.txt_hasil = QTextEdit()
        self.txt_hasil.setReadOnly(True)
        self.txt_hasil.setPlaceholderText("Hasil verifikasi kriptografi, NIK hasil super-dekripsi, dan ekstraksi segel denah akan tampil di sini...")
        self.txt_hasil.setStyleSheet("""
            background-color: #1e293b; 
            border: 1px solid #334155; 
            border-radius: 6px; 
            color: #f8fafc; 
            font-size: 14px; 
            font-family: 'Consolas', 'Courier New', monospace;
            margin-top: 10px;
            padding: 8px;
        """)
        content_layout.addWidget(self.txt_hasil)

        # TOMBOL AKSI VERIFIKATOR
        btn_layout = QHBoxLayout()
        self.btn_dekripsi = QPushButton("🔓 Verifikasi Integritas & Tampilkan Dokumen")
        self.btn_dekripsi.setFixedHeight(42)
        self.btn_dekripsi.setStyleSheet("background-color: #0d9488; color: white; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;")
        self.btn_dekripsi.clicked.connect(self.proses_verifikasi_kripto)

        self.btn_setuju = QPushButton("✔ Setujui Izin & Terbitkan SK")
        self.btn_setuju.setFixedHeight(42)
        self.btn_setuju.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;")
        self.btn_setuju.clicked.connect(lambda: self.update_status("Disetujui"))

        self.btn_tolak = QPushButton("✖ Tolak Izin")
        self.btn_tolak.setFixedHeight(42)
        self.btn_tolak.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;")
        self.btn_tolak.clicked.connect(lambda: self.update_status("Ditolak"))

        self.btn_resi = QPushButton("🖨️ Cetak Resi")
        self.btn_resi.setFixedHeight(42)
        self.btn_resi.setStyleSheet("background-color: #475569; color: white; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;")
        self.btn_resi.clicked.connect(self.cetak_resi_manual)

        btn_layout.addWidget(self.btn_dekripsi)
        btn_layout.addWidget(self.btn_setuju)
        btn_layout.addWidget(self.btn_tolak)
        btn_layout.addWidget(self.btn_resi)
        content_layout.addLayout(btn_layout)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        self.muat_daftar_permohonan()

    def muat_daftar_permohonan(self):
        daftar = db._jalankan("SELECT * FROM permohonan ORDER BY id_permohonan DESC", ambil="semua") or []
        self.tabel.setRowCount(len(daftar))
        self.raw_data = daftar

        for row, item in enumerate(daftar):
            self.tabel.setItem(row, 0, QTableWidgetItem(str(item["no_registrasi"])))
            self.tabel.setItem(row, 1, QTableWidgetItem(str(item["nama_pemohon"])))
            self.tabel.setItem(row, 2, QTableWidgetItem(str(item["jenis_bangunan"])))
            self.tabel.setItem(row, 3, QTableWidgetItem(str(item["tanggal_pengajuan"])))
            
            st_item = QTableWidgetItem(str(item["status_permohonan"]))
            if item["status_permohonan"] == "Disetujui":
                st_item.setForeground(Qt.green)
            elif item["status_permohonan"] == "Ditolak":
                st_item.setForeground(Qt.red)
            else:
                st_item.setForeground(Qt.yellow)
            self.tabel.setItem(row, 4, st_item)

    def pilih_permohonan(self, item):
        row = item.row()
        self.data_terpilih = self.raw_data[row]
        no_reg = self.data_terpilih["no_registrasi"]
        self.lbl_preview_ktp.clear()
        self.lbl_preview_ktp.setText("Klik tombol 'Verifikasi & Tampilkan Dokumen' di bawah...")
        self.lbl_preview_denah.clear()
        self.lbl_preview_denah.setText("Klik tombol 'Verifikasi & Tampilkan Dokumen' di bawah...")
        self.txt_hasil.setText(
            f"Permohonan Dipilih:\n"
            f"Nomor Registrasi : {no_reg}\n"
            f"Nama Pemohon     : {self.data_terpilih['nama_pemohon']}\n"
            f"Status Saat Ini  : {self.data_terpilih['status_permohonan']}\n\n"
            f"Silakan klik 'Verifikasi Integritas & Tampilkan Dokumen' untuk membuka berkas dan merender gambar."
        )

    def proses_verifikasi_kripto(self):
        if not self.data_terpilih:
            QMessageBox.warning(self, "Peringatan", "Pilih salah satu baris permohonan di tabel terlebih dahulu!")
            return

        no_reg = self.data_terpilih["no_registrasi"]
        berkas = db._jalankan("SELECT * FROM berkas WHERE no_registrasi = %s", (no_reg,), ambil="satu")
        if not berkas:
            QMessageBox.warning(self, "Data Tidak Ditemukan", "Data lampiran berkas tidak ditemukan di sistem!")
            return

        rahasia = session.Session.dongle_rahasia or b"SIPAMAN_SECURE_DONGLE_MASTER_KEY_2026"
        kaes = kunci_aes(rahasia)
        kvig = kunci_vigenere(rahasia)
        krc4 = rahasia[:16]

        hasil_log = []
        hasil_log.append(f"=== LAPORAN RESMI VERIFIKASI & KEAMANAN SISTEM [{no_reg}] ===")

        # 1. Super-Dekripsi Identitas Pemohon
        try:
            nik_asli = super_decrypt(self.data_terpilih["nik_pemohon_enc"], kvig, kaes)
            alamat_asli = super_decrypt(self.data_terpilih["alamat_enc"], kvig, kaes)
            hasil_log.append(f"✔ Super-Dekripsi Identitas Sukses:")
            hasil_log.append(f"   • NIK Pemohon : {nik_asli}")
            hasil_log.append(f"   • Alamat      : {alamat_asli}")
        except Exception as e:
            hasil_log.append(f"✖ Super-Dekripsi Gagal: {e}")

        # 2. Dekripsi RC4 & Render Pratinjau KTP
        path_ktp_enc = berkas.get("path_ktp_enc")
        if path_ktp_enc and os.path.exists(path_ktp_enc):
            with open(path_ktp_enc, "rb") as f:
                enc_bytes = f.read()
            dec_bytes = rc4_decrypt(enc_bytes, krc4)
            hash_cek = hashlib.sha256(dec_bytes).hexdigest()

            if hash_cek == berkas.get("hash_ktp"):
                hasil_log.append("✔ Dokumen KTP: Integritas Valid (Hash SHA-256 Sesuai)")
            else:
                hasil_log.append("✖ PERINGATAN: Hash KTP Tidak Cocok! Berkas termanipulasi.")

            img = QImage()
            if img.loadFromData(dec_bytes):
                pixmap = QPixmap.fromImage(img).scaled(380, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_preview_ktp.setPixmap(pixmap)
            else:
                self.lbl_preview_ktp.setText("Berkas KTP Format PDF/Dokumen.\nDekripsi RC4 Berhasil.")
        else:
            self.lbl_preview_ktp.setText("Tidak ada berkas KTP terlampir.")

        # 3. Pratinjau Denah & Ekstraksi Steganografi LSB
        path_denah = berkas.get("path_denah_lsb")
        if path_denah and os.path.exists(path_denah):
            pix_denah = QPixmap(path_denah).scaled(380, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_preview_denah.setPixmap(pix_denah)

            try:
                pesan_tersembunyi = ekstrak_pesan(path_denah)
                hasil_log.append(f"✔ Steganografi LSB Denah:")
                hasil_log.append(f"   • Pesan Tersembunyi: {pesan_tersembunyi}")
                if berkas.get("kode_segel") and berkas.get("kode_segel") in pesan_tersembunyi:
                    hasil_log.append("   • Segel Digital: VALID & RESMI")
            except Exception as e:
                hasil_log.append(f"✖ Ekstraksi LSB Gagal: {e}")
        else:
            self.lbl_preview_denah.setText("Tidak ada berkas denah terlampir.")

        self.txt_hasil.setText("\n".join(hasil_log))

    def audit_blockchain(self):
        semua_blok = db.semua_blok() or []
        bc = Blockchain(semua_blok)
        valid, pesan = bc.validasi_rantai()
        if valid:
            QMessageBox.information(self, "Audit Blockchain Sukses", f"Seluruh rantai blok utuh dan terverifikasi secara kriptografis.\nTotal Blok: {len(semua_blok)}")
        else:
            QMessageBox.critical(self, "Peringatan Keamanan", f"Integritas Ledger Blockchain Rusak!\n{pesan}")

    def buat_stempel_stego(self, no_reg, no_sk, nama_verifikator, curr_hash):
        """Membuat gambar stempel digital resmi dan menyisipkan metadata LSB."""
        size = (200, 200)
        img = Image.new("RGBA", size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        warna_tinta = (13, 71, 161, 230)  # Biru stempel dinas
        draw.ellipse([10, 10, 190, 190], outline=warna_tinta, width=4)
        draw.ellipse([18, 18, 182, 182], outline=warna_tinta, width=2)

        try:
            font_title = ImageFont.truetype("arial.ttf", 11)
            font_status = ImageFont.truetype("arialbd.ttf", 16)
        except Exception:
            font_title = ImageFont.load_default()
            font_status = ImageFont.load_default()

        draw.text((100, 42), "PEMDA DIY - DPMPTSP", fill=warna_tinta, font=font_title, anchor="mm")
        draw.text((100, 62), "SIPAMAN SECURE", fill=warna_tinta, font=font_title, anchor="mm")
        
        draw.line([30, 80, 170, 80], fill=warna_tinta, width=2)
        draw.text((100, 100), "TERVERIFIKASI", fill=(22, 163, 74, 255), font=font_status, anchor="mm")
        draw.text((100, 120), "DIGITAL SEAL", fill=warna_tinta, font=font_title, anchor="mm")
        draw.line([30, 135, 170, 135], fill=warna_tinta, width=2)

        draw.text((100, 155), time.strftime("%d/%m/%Y"), fill=warna_tinta, font=font_title, anchor="mm")

        # Simpan ke RGB untuk disisipi LSB
        stempel_rgb = Image.new("RGB", size, (255, 255, 255))
        stempel_rgb.paste(img, (0, 0), img)
        
        path_stempel_raw = os.path.join(config.STORAGE_DIR, f"{no_reg}_STEMPEL_RAW.png")
        path_stempel_stego = os.path.join(config.STORAGE_DIR, f"{no_reg}_STEMPEL_STEGO.png")
        stempel_rgb.save(path_stempel_raw, "PNG")

        pesan_stempel = f"SK:{no_sk}|REG:{no_reg}|VERIF:{nama_verifikator}|HASH:{curr_hash[:16]}"
        try:
            sisip_pesan(path_stempel_raw, pesan_stempel, path_stempel_stego)
        except Exception as e:
            print(f"[STEGO STEMPEL] Gagal menyisipkan pesan: {e}")
            path_stempel_stego = path_stempel_raw

        return path_stempel_stego

    def buat_sk_perizinan(self, data_permohonan, nik_asli):
        """Membuat berkas SK Izin resmi berkop Pemda DIY berstempel steganografi digital."""
        no_reg = data_permohonan["no_registrasi"]
        no_sk = f"SK-SIPAMAN/{time.strftime('%Y%m')}/{data_permohonan['id_permohonan']:04d}"
        tgl_terbit = time.strftime("%d %B %Y")
        verifikator = session.Session.username or "Verifikator Resmi"
        
        blok = db._jalankan("SELECT curr_hash FROM blockchain_log WHERE no_registrasi = %s", (no_reg,), ambil="satu")
        curr_hash = blok.get("curr_hash", "0" * 64) if blok else "SIPAMAN_VERIFIED_CHAIN"

        path_stempel = self.buat_stempel_stego(no_reg, no_sk, verifikator, curr_hash)
        uri_stempel = f"file:///{os.path.abspath(path_stempel).replace(os.sep, '/')}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Surat Keputusan Izin - {no_reg}</title>
            <style>
                body {{
                    font-family: 'Times New Roman', Times, serif;
                    padding: 40px 50px;
                    color: #0f172a;
                    background-color: #ffffff;
                    max-width: 820px;
                    margin: auto;
                    line-height: 1.6;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px double #000;
                    padding-bottom: 10px;
                    margin-bottom: 25px;
                }}
                .header h2 {{
                    margin: 0;
                    font-size: 19px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .header h3 {{
                    margin: 4px 0;
                    font-size: 15px;
                    font-weight: 600;
                }}
                .header p {{
                    margin: 0;
                    font-size: 12px;
                    color: #475569;
                }}
                .title {{
                    text-align: center;
                    margin: 25px 0 20px 0;
                }}
                .title h4 {{
                    margin: 0;
                    font-size: 16px;
                    text-decoration: underline;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .title p {{
                    margin: 4px 0 0;
                    font-size: 13px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 14px;
                }}
                td {{
                    padding: 6px 4px;
                    vertical-align: top;
                }}
                .label {{
                    width: 38%;
                    font-weight: bold;
                    color: #1e293b;
                }}
                .colon {{
                    width: 3%;
                }}
                .footer-box {{
                    margin-top: 35px;
                    display: flex;
                    justify-content: flex-end;
                    position: relative;
                }}
                .ttd-container {{
                    width: 300px;
                    text-align: center;
                    font-size: 13px;
                    position: relative;
                }}
                .stempel-img {{
                    position: absolute;
                    top: 25px;
                    left: -20px;
                    width: 140px;
                    opacity: 0.88;
                    z-index: 10;
                    pointer-events: none;
                }}
                .catatan-kaki {{
                    margin-top: 55px;
                    border-top: 1px solid #cbd5e1;
                    padding-top: 8px;
                    font-size: 10px;
                    color: #64748b;
                    font-style: italic;
                    line-height: 1.4;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>PEMERINTAH DAERAH DAERAH ISTIMEWA YOGYAKARTA</h2>
                <h3>DINAS PENANAMAN MODAL DAN PELAYANAN TERPADU SATU PINTU</h3>
                <p>Jl. Ring Road Barat, Somodaran, Banyuraden, Kec. Gamping, Kabupaten Sleman, D.I. Yogyakarta</p>
            </div>

            <div class="title">
                <h4>SURAT KEPUTUSAN PERSETUJUAN PERIZINAN INFRASTRUKTUR</h4>
                <p>Nomor: {no_sk}</p>
            </div>

            <p style="font-size: 13.5px; text-align: justify;">
                Berdasarkan hasil pemeriksaan kelengkapan administratif, validasi identitas pemohon, serta audit kepatuhan teknis tata ruang dan infrastruktur melalui <b>Sistem Informasi Perizinan Aman (SIPAMAN)</b>, Pemerintah Daerah Daerah Istimewa Yogyakarta dengan ini menetapkan:
            </p>

            <table>
                <tr>
                    <td class="label">Nomor Registrasi Permohonan</td>
                    <td class="colon">:</td>
                    <td><b>{no_reg}</b></td>
                </tr>
                <tr>
                    <td class="label">Nama Pemegang Izin</td>
                    <td class="colon">:</td>
                    <td>{data_permohonan['nama_pemohon']}</td>
                </tr>
                <tr>
                    <td class="label">Nomor Induk Kependudukan (NIK)</td>
                    <td class="colon">:</td>
                    <td>{nik_asli}</td>
                </tr>
                <tr>
                    <td class="label">Peruntukan / Jenis Bangunan</td>
                    <td class="colon">:</td>
                    <td>{data_permohonan['jenis_bangunan']}</td>
                </tr>
                <tr>
                    <td class="label">Luas Bangunan Infrastruktur</td>
                    <td class="colon">:</td>
                    <td>{data_permohonan['luas_bangunan']} m²</td>
                </tr>
                <tr>
                    <td class="label">Status Keputusan</td>
                    <td class="colon">:</td>
                    <td><b style="color: #16a34a;">DISETUJUI &amp; MEMENUHI KELAYAKAN TEKNIS</b></td>
                </tr>
            </table>

            <p style="font-size: 13.5px; text-align: justify;">
                Surat Keputusan ini berlaku sejak tanggal ditetapkan dengan ketentuan bahwa pemegang izin wajib mematuhi seluruh peraturan perundang-undangan tata ruang bangunan yang berlaku.
            </p>

            <div class="footer-box">
                <div class="ttd-container">
                    Ditetapkan di: Sleman, D.I. Yogyakarta<br>
                    Pada tanggal: {tgl_terbit}<br><br>
                    <b>Kepala Seksi Verifikasi &amp; Pelayanan Perizinan,</b><br>
                    
                    <img src="{uri_stempel}" class="stempel-img" alt="Stempel Steganografi">
                    
                    <br><br><br><br>
                    <u><b>{verifikator.title()}</b></u><br>
                    NIP. 19980312 202401 2 001
                </div>
            </div>

            <div class="catatan-kaki">
                * Dokumen ini diterbitkan secara elektronik dan sah tanpa tanda tangan basah fisik.<br>
                * Otentisitas surat ini dilindungi segel digital kriptografis (LSB Watermarking) pada stempel resmi dan terdaftar dalam buku besar transaksi ledger terdesentralisasi (Block #{data_permohonan['id_permohonan']}).
            </div>
        </body>
        </html>
        """

        os.makedirs(config.STORAGE_DIR, exist_ok=True)
        nama_file_sk = f"{no_reg}_SK_PERSETUJUAN.html"
        path_sk = os.path.join(config.STORAGE_DIR, nama_file_sk)
        with open(path_sk, "w", encoding="utf-8") as f:
            f.write(html_content)

        return path_sk

    def buat_resi_verifikasi(self, data_permohonan, nik_asli, status):
        """Menerbitkan Resi / Lembar Tanda Terima Verifikasi Resmi."""
        no_reg = data_permohonan["no_registrasi"]
        no_resi = f"RESI-SIPAMAN/{time.strftime('%Y%m%d')}/{data_permohonan['id_permohonan']:04d}"
        tgl_cetak = time.strftime("%d-%m-%Y %H:%M:%S WIB")

        berkas = db._jalankan("SELECT kode_segel FROM berkas WHERE no_registrasi = %s", (no_reg,), ambil="satu") or {}
        kode_segel = berkas.get("kode_segel", "SEAL-UNVERIFIED")

        blok = db._jalankan("SELECT curr_hash, prev_hash FROM blockchain_log WHERE no_registrasi = %s", (no_reg,), ambil="satu") or {}
        curr_hash = blok.get("curr_hash", "0" * 64)

        warna_status = "#16a34a" if status == "Disetujui" else ("#dc2626" if status == "Ditolak" else "#ca8a04")

        html_resi = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Resi Verifikasi - {no_reg}</title>
            <style>
                body {{ font-family: 'Courier New', Courier, monospace; padding: 30px; background: #fff; color: #111; max-width: 650px; margin: auto; border: 2px dashed #334155; }}
                .center {{ text-align: center; }}
                .line {{ border-top: 1px dashed #475569; margin: 12px 0; }}
                .double-line {{ border-top: 2px solid #000; margin: 14px 0; }}
                table {{ width: 100%; font-size: 13px; }}
                td {{ padding: 4px 0; vertical-align: top; }}
                .label {{ width: 42%; font-weight: bold; }}
                .badge {{ display: inline-block; padding: 4px 10px; font-weight: bold; color: white; background: {warna_status}; border-radius: 4px; }}
                .hash-box {{ word-break: break-all; background: #f1f5f9; padding: 8px; font-size: 11px; border: 1px solid #cbd5e1; }}
                .footer {{ text-align: center; font-size: 11px; margin-top: 20px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="center">
                <h3 style="margin: 0;">SIPAMAN - RESI RESMI VERIFIKASI</h3>
                <p style="margin: 3px 0; font-size: 12px;">Sistem Perizinan Bangunan &amp; Infrastruktur Aman</p>
                <p style="margin: 0; font-size: 11px;">Pemerintah Daerah D.I. Yogyakarta</p>
            </div>

            <div class="double-line"></div>

            <table>
                <tr>
                    <td class="label">NO. TANDA TERIMA</td>
                    <td>: {no_resi}</td>
                </tr>
                <tr>
                    <td class="label">NO. REGISTRASI</td>
                    <td>: <b>{no_reg}</b></td>
                </tr>
                <tr>
                    <td class="label">WAKTU AUDIT</td>
                    <td>: {tgl_cetak}</td>
                </tr>
                <tr>
                    <td class="label">PETUGAS VERIFIKATOR</td>
                    <td>: {session.Session.username or 'Verifikator Dinas'}</td>
                </tr>
            </table>

            <div class="line"></div>

            <table>
                <tr>
                    <td class="label">NAMA PEMOHON</td>
                    <td>: {data_permohonan['nama_pemohon']}</td>
                </tr>
                <tr>
                    <td class="label">NIK (DEKRIPSI AES)</td>
                    <td>: {nik_asli}</td>
                </tr>
                <tr>
                    <td class="label">JENIS INFRASTRUKTUR</td>
                    <td>: {data_permohonan['jenis_bangunan']}</td>
                </tr>
                <tr>
                    <td class="label">LUAS BANGUNAN</td>
                    <td>: {data_permohonan['luas_bangunan']} m²</td>
                </tr>
                <tr>
                    <td class="label">KODE SEGEL STEGO (LSB)</td>
                    <td>: <b>{kode_segel}</b></td>
                </tr>
                <tr>
                    <td class="label">STATUS KEPUTUSAN</td>
                    <td>: <span class="badge">{status.upper()}</span></td>
                </tr>
            </table>


            <div class="footer">
                <p>Simpan resi ini sebagai tanda bukti sah verifikasi perizinan.<br>
                Validitas transaksi dapat dicek melalui ledger audit SIPAMAN.</p>
            </div>
        </body>
        </html>
        """

        os.makedirs(config.STORAGE_DIR, exist_ok=True)
        path_resi = os.path.join(config.STORAGE_DIR, f"{no_reg}_RESI_VERIFIKASI.html")
        with open(path_resi, "w", encoding="utf-8") as f:
            f.write(html_resi)

        return path_resi

    def cetak_resi_manual(self):
        """Mencetak resi kapan pun tombol Cetak Resi diklik."""
        if not self.data_terpilih:
            QMessageBox.warning(self, "Peringatan", "Pilih salah satu permohonan terlebih dahulu!")
            return

        rahasia = session.Session.dongle_rahasia or b"SIPAMAN_SECURE_DONGLE_MASTER_KEY_2026"
        kaes = kunci_aes(rahasia)
        kvig = kunci_vigenere(rahasia)
        try:
            nik_asli = super_decrypt(self.data_terpilih["nik_pemohon_enc"], kvig, kaes)
        except Exception:
            nik_asli = "TERENKRIPSI"

        no_reg = self.data_terpilih["no_registrasi"]
        data_terbaru = db._jalankan("SELECT status_permohonan FROM permohonan WHERE no_registrasi = %s", (no_reg,), ambil="satu")
        status_terkini = data_terbaru["status_permohonan"] if data_terbaru else self.data_terpilih.get("status_permohonan", "Menunggu Verifikasi")

        path_resi = self.buat_resi_verifikasi(self.data_terpilih, nik_asli, status_terkini)

        if os.path.exists(path_resi):
            os.startfile(path_resi)
            QMessageBox.information(self, "Resi Berhasil Dicetak", f"Resi tanda bukti verifikasi tersimpan di:\n{path_resi}")

    def update_status(self, status_baru):
        if not self.data_terpilih:
            QMessageBox.warning(self, "Peringatan", "Pilih permohonan terlebih dahulu!")
            return

        no_reg = self.data_terpilih["no_registrasi"]
        id_verifikator_aktif = session.Session.id_user 
        
        # 1. Update status dan ID Verifikator di database
        db._jalankan(
            "UPDATE permohonan SET status_permohonan = %s, id_verifikator = %s WHERE no_registrasi = %s", 
            (status_baru, id_verifikator_aktif, no_reg), 
            commit=True
        )

        # Sinkronisasi data di memori aplikasi (Mencegah bug cetak resi basi)
        self.data_terpilih["status_permohonan"] = status_baru
        
        rahasia = session.Session.dongle_rahasia or b"SIPAMAN_SECURE_DONGLE_MASTER_KEY_2026"
        kaes = kunci_aes(rahasia)
        kvig = kunci_vigenere(rahasia)
        try:
            nik_asli = super_decrypt(self.data_terpilih["nik_pemohon_enc"], kvig, kaes)
        except Exception:
            nik_asli = "TERENKRIPSI"

        if status_baru == "Disetujui":
            # Buat Dokumen SK dan Resi
            path_sk = self.buat_sk_perizinan(self.data_terpilih, nik_asli)
            path_resi = self.buat_resi_verifikasi(self.data_terpilih, nik_asli, status_baru)

            # 2. Simpan Path SK ke tabel berkas
            db._jalankan(
                "UPDATE berkas SET path_sk_enc = %s WHERE no_registrasi = %s", 
                (path_sk, no_reg), 
                commit=True
            )

            # 3. PENAMBAHAN AUDIT BLOCKCHAIN UNTUK SK YANG TERBIT
            if os.path.exists(path_sk):
                # Hitung Hash Dokumen SK
                with open(path_sk, "rb") as f:
                    sk_hash = hashlib.sha256(f.read()).hexdigest()
                
                # Ambil prev_hash dari blok terakhir di database
                last_block = db._jalankan("SELECT curr_hash FROM blockchain_log ORDER BY id_blok DESC LIMIT 1", ambil="satu")
                prev_hash = last_block["curr_hash"] if last_block else "0"*64
                
                # Hitung curr_hash baru (Timestamp + No Reg + ID + Dokumen Hash + Prev Hash)
                waktu_sekarang = time.strftime('%Y-%m-%d %H:%M:%S')
                data_mentah = f"{waktu_sekarang}{no_reg}{id_verifikator_aktif}{sk_hash}{prev_hash}".encode('utf-8')
                curr_hash = hashlib.sha256(data_mentah).hexdigest()
                
                # Simpan ke Ledger
                db._jalankan(
                    "INSERT INTO blockchain_log (timestamp, no_registrasi, id_user, hash_dokumen, prev_hash, curr_hash) VALUES (%s, %s, %s, %s, %s, %s)",
                    (waktu_sekarang, no_reg, id_verifikator_aktif, sk_hash, prev_hash, curr_hash),
                    commit=True
                )

                os.startfile(path_sk)

            QMessageBox.information(
                self, "Izin Disetujui",
                f"Permohonan {no_reg} BERHASIL DISETUJUI!\n\n"
                f"✔ Surat Keputusan (SK) Resmi berstempel steganografi digital diterbitkan.\n"
                f"✔ Jejak Audit SK berhasil dikunci ke dalam Ledger Blockchain."
            )
        else:
            path_resi = self.buat_resi_verifikasi(self.data_terpilih, nik_asli, status_baru)
            if os.path.exists(path_resi):
                os.startfile(path_resi)
            QMessageBox.information(
                self, "Status Diperbarui",
                f"Permohonan {no_reg} telah diubah menjadi: {status_baru}\n"
                f"Resi pembaruan status telah dicetak."
            )

        # Refresh antarmuka tabel
        self.muat_daftar_permohonan()

    def proses_logout(self):
        """Menghapus data sesi dan menutup jendela portal verifikator."""
        session.Session.username = None
        session.Session.role = None
        session.Session.id_user = None
        session.Session.dongle_rahasia = None
        self.close()