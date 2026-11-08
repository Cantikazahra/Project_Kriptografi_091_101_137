import os
import sys
import time
import random
import hashlib

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, 
    QFileDialog, QTextEdit, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget
)
from PyQt5.QtCore import Qt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
import config
import session
from kripto.keys import kunci_aes, kunci_vigenere
from kripto.aes_tool import super_encrypt
from kripto.rc4_tool import rc4_encrypt
from kripto.lsb import sisip_pesan
from kripto.blockchain import Blockchain


class OperatorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIPAMAN - Operator Portal")
        self.showMaximized()
        self.setStyleSheet("background-color: #090d16; color: #f8fafc;")

        self.dokumen_terpilih = {
            "KTP": None,
            "SHM": None,
            "DENAH": None
        }

        # Layout Utama
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------------- 1. SIDEBAR KIRI ----------------
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #0f172a; border-right: 1px solid #1e293b;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)

        logo = QLabel("🛡️ SIPAMAN")
        logo.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        sidebar_layout.addWidget(logo)

        sub_logo = QLabel(f"Operator: {session.Session.username or 'Petugas'}")
        sub_logo.setStyleSheet("font-size: 13px; color: #94a3b8; font-weight: bold; margin-bottom: 25px;")
        sidebar_layout.addWidget(sub_logo)

        self.btn_nav_form = QPushButton("  ➕ Pengajuan Izin Baru")
        self.btn_nav_form.setStyleSheet(self.nav_btn_style(active=True))
        self.btn_nav_form.clicked.connect(lambda: self.ganti_halaman(0))
        sidebar_layout.addWidget(self.btn_nav_form)

        self.btn_nav_status = QPushButton("  📋 Status & Riwayat Izin")
        self.btn_nav_status.setStyleSheet(self.nav_btn_style(active=False))
        self.btn_nav_status.clicked.connect(lambda: self.ganti_halaman(1))
        sidebar_layout.addWidget(self.btn_nav_status)

        btn_logout = QPushButton("  🚪 Logout / Keluar")
        btn_logout.setStyleSheet("""
            QPushButton {
                text-align: left; padding: 12px; border-radius: 6px; 
                background: transparent; color: #ef4444; font-size: 12px; font-weight: bold; border: 1px solid #7f1d1d; margin-top: 10px;
            }
            QPushButton:hover { background-color: #7f1d1d; color: white; }
        """)
        btn_logout.clicked.connect(self.proses_logout)
        sidebar_layout.addWidget(btn_logout)

        sidebar_layout.addStretch()

        sec_box = QFrame()
        sec_box.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 14px;")
        sec_layout = QVBoxLayout(sec_box)
        
        sec_title = QLabel("Security Protocol:")
        sec_title.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: bold; margin-bottom: 4px;")
        
        sec_info = QLabel("• AES-256 GCM\n• Vigenère Cipher\n• RC4 Stream Cipher\n• LSB Steganography\n• SHA-256 Blockchain")
        sec_info.setStyleSheet("color: #34d399; font-size: 11px; line-height: 1.5; font-weight: bold;")
        
        sec_layout.addWidget(sec_title)
        sec_layout.addWidget(sec_info)
        sidebar_layout.addWidget(sec_box)

        main_layout.addWidget(sidebar)

        # ---------------- 2. KONTEN (STACKED WIDGET) ----------------
        self.stack = QStackedWidget()
        self.page_form = self.init_form_page()
        self.page_status = self.init_status_page()

        self.stack.addWidget(self.page_form)    # Index 0: Formulir
        self.stack.addWidget(self.page_status)  # Index 1: Monitoring Status
        main_layout.addWidget(self.stack)

    def nav_btn_style(self, active=False):
        if active:
            return """
                QPushButton {
                    text-align: left; padding: 12px; border-radius: 6px; 
                    color: white; background-color: #0d9488; font-size: 13px; font-weight: bold; border: none; margin-bottom: 5px;
                }
            """
        return """
            QPushButton {
                text-align: left; padding: 12px; border-radius: 6px; 
                color: #94a3b8; background-color: transparent; font-size: 13px; font-weight: bold; border: none; margin-bottom: 5px;
            }
            QPushButton:hover { background-color: #1e293b; color: #38bdf8; }
        """

    def ganti_halaman(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btn_nav_form.setStyleSheet(self.nav_btn_style(active=True))
            self.btn_nav_status.setStyleSheet(self.nav_btn_style(active=False))
        else:
            self.btn_nav_form.setStyleSheet(self.nav_btn_style(active=False))
            self.btn_nav_status.setStyleSheet(self.nav_btn_style(active=True))
            self.muat_riwayat_pengajuan()

    # ================= FORMULIR PENGAJUAN =================
    def init_form_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: #0b1120;")

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #0b1120; color: #f8fafc;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setAlignment(Qt.AlignTop)

        header_title = QLabel("Formulir Permohonan Izin Baru")
        header_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #f8fafc;")
        content_layout.addWidget(header_title)

        header_desc = QLabel("Seluruh parameter identitas pemohon dan berkas pendukung akan dienkripsi secara multi-layer.")
        header_desc.setStyleSheet("font-size: 12px; color: #94a3b8; margin-bottom: 20px;")
        content_layout.addWidget(header_desc)

        # KARTU 1: DATA IDENTITAS
        card1, card1_layout = self.create_card("01. Identitas Pemohon (Super-Enkripsi: Vigenère + AES-256)", "#38bdf8")
        row1 = QHBoxLayout()
        self.inp_nik = self.create_input("NIK Pemohon (16 Digit Angka)")
        self.inp_nama = self.create_input("Nama Lengkap Pemohon Sesuai KTP")
        row1.addWidget(self.inp_nik)
        row1.addWidget(self.inp_nama)
        card1_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.inp_telepon = self.create_input("Nomor Telepon / WhatsApp")
        self.inp_alamat = self.create_input("Alamat Domisili Lengkap")
        row2.addWidget(self.inp_telepon)
        row2.addWidget(self.inp_alamat)
        card1_layout.addLayout(row2)
        content_layout.addWidget(card1)

        # KARTU 2: DETAIL BANGUNAN
        card2, card2_layout = self.create_card("02. Spesifikasi Teknis Infrastruktur", "#38bdf8")
        row3 = QHBoxLayout()
        self.inp_jenis = self.create_input("Jenis Bangunan (Contoh: Menara Telekomunikasi / Gedung Usaha)")
        self.inp_luas = self.create_input("Luas Bangunan (m²)")
        self.inp_koordinat = self.create_input("Titik Koordinat Lokasi (Lat, Long)")
        row3.addWidget(self.inp_jenis)
        row3.addWidget(self.inp_luas)
        row3.addWidget(self.inp_koordinat)
        card2_layout.addLayout(row3)

        self.inp_uraian = QTextEdit()
        self.inp_uraian.setPlaceholderText("Uraian Singkat Perizinan & Rencana Pembangunan...")
        self.inp_uraian.setFixedHeight(75)
        self.inp_uraian.setStyleSheet(self.textarea_style())
        card2_layout.addWidget(self.inp_uraian)
        content_layout.addWidget(card2)

        # KARTU 3: LAMPIRAN BERKAS
        card3, card3_layout = self.create_card("03. Berkas Pendukung (RC4 Stream Cipher & LSB Steganography)", "#38bdf8")
        row_btn = QHBoxLayout()
        self.btn_ktp = QPushButton("📁 Upload Scan KTP")
        self.btn_ktp.setFixedHeight(45)
        self.btn_ktp.setStyleSheet(self.upload_btn_style())
        self.btn_ktp.clicked.connect(lambda: self.pilih_berkas("KTP"))

        self.btn_shm = QPushButton("📁 Upload Sertifikat Tanah (SHM)")
        self.btn_shm.setFixedHeight(45)
        self.btn_shm.setStyleSheet(self.upload_btn_style())
        self.btn_shm.clicked.connect(lambda: self.pilih_berkas("SHM"))

        self.btn_denah = QPushButton("🖼️ Upload Denah LSB (.png)")
        self.btn_denah.setFixedHeight(45)
        self.btn_denah.setStyleSheet(self.upload_btn_style())
        self.btn_denah.clicked.connect(lambda: self.pilih_berkas("DENAH"))

        row_btn.addWidget(self.btn_ktp)
        row_btn.addWidget(self.btn_shm)
        row_btn.addWidget(self.btn_denah)
        card3_layout.addLayout(row_btn)
        content_layout.addWidget(card3)

        # TOMBOL SUBMIT
        self.btn_submit = QPushButton("🔒 Proses Enkripsi, Terbitkan Resi & Simpan ke Blockchain →")
        self.btn_submit.setFixedHeight(48)
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background-color: #0d9488; color: white; font-weight: bold; 
                border-radius: 8px; font-size: 14px; margin-top: 15px; border: none;
            }
            QPushButton:hover { background-color: #0f766e; }
        """)
        self.btn_submit.clicked.connect(self.proses_simpan_permohonan)
        content_layout.addWidget(self.btn_submit)

        scroll.setWidget(content_widget)
        return scroll

    # ================= TABEL MONITORING STATUS =================
    def init_status_page(self):
        page = QFrame()
        page.setStyleSheet("background-color: #0b1120;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)

        header = QLabel("Daftar & Status Permohonan Izin")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        desc = QLabel("Pantau status permohonan yang diajukan. Jika izin telah disetujui oleh Verifikator, SK dan Resi resmi dapat langsung dibuka.")
        desc.setStyleSheet("font-size: 12px; color: #94a3b8; margin-bottom: 15px;")
        layout.addWidget(desc)

        btn_refresh = QPushButton("🔄 Muat Ulang Status")
        btn_refresh.setFixedSize(160, 36)
        btn_refresh.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-weight: bold; border-radius: 6px; border: 1px solid #334155;")
        btn_refresh.clicked.connect(self.muat_riwayat_pengajuan)
        layout.addWidget(btn_refresh)

        self.table_status = QTableWidget()
        self.table_status.setColumnCount(6)
        self.table_status.setHorizontalHeaderLabels([
            "No Registrasi", "Nama Pemohon", "Jenis Bangunan", "Tanggal Masuk", "Status Izin", "Aksi Dokumen"
        ])
        self.table_status.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_status.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a; border: 1px solid #1e293b; 
                border-radius: 8px; color: #f8fafc; gridline-color: #1e293b; margin-top: 10px;
            }
            QHeaderView::section {
                background-color: #1e293b; color: #38bdf8; font-weight: bold; padding: 8px; border: none;
            }
        """)
        layout.addWidget(self.table_status)
        return page

    def muat_riwayat_pengajuan(self):
        daftar = db._jalankan(
            "SELECT no_registrasi, nama_pemohon, jenis_bangunan, tanggal_pengajuan, status_permohonan FROM permohonan ORDER BY id_permohonan DESC", 
            ambil="semua"
        ) or []
        self.table_status.setRowCount(len(daftar))
        
        for row, item in enumerate(daftar):
            no_reg = str(item["no_registrasi"])
            status_str = str(item["status_permohonan"])

            self.table_status.setItem(row, 0, QTableWidgetItem(no_reg))
            self.table_status.setItem(row, 1, QTableWidgetItem(str(item["nama_pemohon"])))
            self.table_status.setItem(row, 2, QTableWidgetItem(str(item["jenis_bangunan"])))
            self.table_status.setItem(row, 3, QTableWidgetItem(str(item["tanggal_pengajuan"])))

            item_status = QTableWidgetItem(status_str)
            if status_str == "Disetujui":
                item_status.setForeground(Qt.green)
            elif status_str == "Ditolak":
                item_status.setForeground(Qt.red)
            else:
                item_status.setForeground(Qt.yellow)
            self.table_status.setItem(row, 4, item_status)

            widget_aksi = QWidget()
            layout_aksi = QHBoxLayout(widget_aksi)
            layout_aksi.setContentsMargins(4, 2, 4, 2)
            layout_aksi.setSpacing(6)

            btn_buka_sk = QPushButton("📄 Buka SK")
            btn_buka_resi = QPushButton("🖨️ Resi")

            if status_str == "Disetujui":
                btn_buka_sk.setStyleSheet("background-color: #0d9488; color: white; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 4px;")
                btn_buka_sk.clicked.connect(lambda _, r=no_reg: self.buka_sk_file(r))

                btn_buka_resi.setStyleSheet("background-color: #3b82f6; color: white; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 4px;")
                btn_buka_resi.clicked.connect(lambda _, r=no_reg: self.buka_resi_file(r))
            else:
                btn_buka_sk.setEnabled(False)
                btn_buka_sk.setStyleSheet("background-color: #334155; color: #64748b; font-size: 11px; border-radius: 4px; padding: 4px;")
                btn_buka_sk.setText("Menunggu")

                btn_buka_resi.setStyleSheet("background-color: #475569; color: white; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 4px;")
                btn_buka_resi.clicked.connect(lambda _, r=no_reg: self.buka_resi_file(r))

            layout_aksi.addWidget(btn_buka_sk)
            layout_aksi.addWidget(btn_buka_resi)
            self.table_status.setCellWidget(row, 5, widget_aksi)

    def buka_sk_file(self, no_reg):
        """Membuka file Surat Keputusan (SK) resmi yang sudah diterbitkan."""
        path_sk = os.path.join(config.STORAGE_DIR, f"{no_reg}_SK_PERSETUJUAN.html")
        if os.path.exists(path_sk):
            os.startfile(path_sk)
        else:
            QMessageBox.information(self, "Berkas Belum Ada", f"File SK resmi belum diterbitkan untuk nomor registrasi:\n{no_reg}")

    def buka_resi_file(self, no_reg):
        """Membuka atau merakit otomatis file Resi jika belum tersedia di storage."""
        path_resi = os.path.join(config.STORAGE_DIR, f"{no_reg}_RESI_VERIFIKASI.html")
        
        # Jika file resi fisik sudah ada, langsung buka
        if os.path.exists(path_resi):
            os.startfile(path_resi)
            return

        # JIKA BELUM ADA (Kasus pendaftaran baru): Buat file HTML resinya secara otomatis
        data_permohonan = db._jalankan("SELECT * FROM permohonan WHERE no_registrasi = %s", (no_reg,), ambil="satu")
        if not data_permohonan:
            QMessageBox.warning(self, "Error", "Data permohonan tidak ditemukan di database.")
            return

        no_resi = f"RESI-SIPAMAN/{time.strftime('%Y%m%d')}/{data_permohonan['id_permohonan']:04d}"
        tgl_cetak = time.strftime("%d-%m-%Y %H:%M:%S WIB")
        status = data_permohonan.get("status_permohonan", "Menunggu Verifikasi")
        warna_status = "#ca8a04" if status == "Menunggu Verifikasi" else "#16a34a"

        html_resi = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Resi Pendaftaran - {no_reg}</title>
            <style>
                body {{ font-family: 'Courier New', Courier, monospace; padding: 30px; background: #fff; color: #111; max-width: 650px; margin: auto; border: 2px dashed #334155; }}
                .center {{ text-align: center; }}
                .line {{ border-top: 1px dashed #475569; margin: 12px 0; }}
                .double-line {{ border-top: 2px solid #000; margin: 14px 0; }}
                table {{ width: 100%; font-size: 13px; }}
                td {{ padding: 4px 0; vertical-align: top; }}
                .label {{ width: 42%; font-weight: bold; }}
                .badge {{ display: inline-block; padding: 4px 10px; font-weight: bold; color: white; background: {warna_status}; border-radius: 4px; }}
                .footer {{ text-align: center; font-size: 11px; margin-top: 20px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="center">
                <h3 style="margin: 0;">SIPAMAN - RESI PENDAFTARAN</h3>
                <p style="margin: 3px 0; font-size: 12px;">Sistem Perizinan Bangunan &amp; Infrastruktur Aman</p>
                <p style="margin: 0; font-size: 11px;">Pemerintah Daerah D.I. Yogyakarta</p>
            </div>
            <div class="double-line"></div>
            <table>
                <tr><td class="label">NO. TANDA TERIMA</td><td>: {no_resi}</td></tr>
                <tr><td class="label">NO. REGISTRASI</td><td>: <b>{no_reg}</b></td></tr>
                <tr><td class="label">WAKTU DAFTAR</td><td>: {tgl_cetak}</td></tr>
            </table>
            <div class="line"></div>
            <table>
                <tr><td class="label">NAMA PEMOHON</td><td>: {data_permohonan['nama_pemohon']}</td></tr>
                <tr><td class="label">JENIS INFRASTRUKTUR</td><td>: {data_permohonan['jenis_bangunan']}</td></tr>
                <tr><td class="label">LUAS BANGUNAN</td><td>: {data_permohonan['luas_bangunan']} m²</td></tr>
                <tr><td class="label">STATUS SAAT INI</td><td>: <span class="badge">{status.upper()}</span></td></tr>
            </table>
            <div class="footer">
                <p>Simpan resi ini sebagai tanda bukti pendaftaran perizinan.<br>
                Harap menunggu proses verifikasi dan audit oleh petugas dinas.</p>
            </div>
        </body>
        </html>
        """

        os.makedirs(config.STORAGE_DIR, exist_ok=True)
        with open(path_resi, "w", encoding="utf-8") as f:
            f.write(html_resi)

        os.startfile(path_resi)

    def create_card(self, title_text, accent_color):
        card = QFrame()
        card.setStyleSheet("background-color: #0f172a; border-radius: 10px; border: 1px solid #1e293b; margin-bottom: 12px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 18)
        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {accent_color}; margin-bottom: 8px; border: none;")
        layout.addWidget(title)
        return card, layout

    def create_input(self, placeholder):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(38)
        inp.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 5px 12px; color: #f8fafc; font-size: 13px;")
        return inp

    def textarea_style(self):
        return "QTextEdit { background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 8px; color: #f8fafc; font-size: 13px; }"

    def upload_btn_style(self):
        return "QPushButton { background-color: #1e293b; border: 2px dashed #475569; border-radius: 8px; color: #94a3b8; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #334155; border-color: #38bdf8; color: #38bdf8; }"

    def pilih_berkas(self, jenis):
        filter_file = "Image Files (*.png *.jpg *.jpeg)" if jenis == "DENAH" else "All Files (*);;PDF (*.pdf);;Images (*.png *.jpg)"
        path_file, _ = QFileDialog.getOpenFileName(self, f"Pilih Berkas {jenis}", "", filter_file)
        if path_file:
            self.dokumen_terpilih[jenis] = path_file
            nama = os.path.basename(path_file)
            if jenis == "KTP":
                self.btn_ktp.setText(f"✓ KTP: {nama[:15]}...")
            elif jenis == "SHM":
                self.btn_shm.setText(f"✓ SHM: {nama[:15]}...")
            elif jenis == "DENAH":
                self.btn_denah.setText(f"✓ Denah: {nama[:15]}...")

    def proses_simpan_permohonan(self):
        nik = self.inp_nik.text().strip()
        nama = self.inp_nama.text().strip()
        telepon = self.inp_telepon.text().strip()
        alamat = self.inp_alamat.text().strip()
        jenis_bangunan = self.inp_jenis.text().strip() or "Bangunan Gedung"
        luas_teks = self.inp_luas.text().strip() or "0"
        koordinat = self.inp_koordinat.text().strip()
        uraian = self.inp_uraian.toPlainText().strip()

        if not nik or not nama or not alamat:
            QMessageBox.warning(self, "Validasi Gagal", "NIK, Nama Pemohon, dan Alamat wajib diisi!")
            return

        try:
            luas_bangunan = float(luas_teks)
        except ValueError:
            QMessageBox.warning(self, "Validasi Gagal", "Luas bangunan harus berupa angka!")
            return

        kunci_rahasia = session.Session.dongle_rahasia or b"SIPAMAN_SECURE_DONGLE_MASTER_KEY_2026"
        kaes = kunci_aes(kunci_rahasia)
        kvig = kunci_vigenere(kunci_rahasia)
        krc4 = kunci_rahasia[:16]

        try:
            nik_enc = super_encrypt(nik, kvig, kaes)
            alamat_enc = super_encrypt(alamat, kvig, kaes)
            telepon_enc = super_encrypt(telepon, kvig, kaes) if telepon else ""
            koordinat_enc = super_encrypt(koordinat, kvig, kaes) if koordinat else ""
            uraian_enc = super_encrypt(uraian, kvig, kaes) if uraian else ""
        except Exception as e:
            QMessageBox.critical(self, "Error Enkripsi", f"Gagal menjalankan super-enkripsi data:\n{e}")
            return

        no_registrasi = f"REG-{time.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        kode_segel = f"SEAL-{random.randint(100000, 999999)}"
        os.makedirs(config.STORAGE_DIR, exist_ok=True)

        path_ktp_enc, hash_ktp = "", ""
        path_shm_enc, hash_shm = "", ""

        for tipe, path_asal in [("KTP", self.dokumen_terpilih["KTP"]), ("SHM", self.dokumen_terpilih["SHM"])]:
            if path_asal and os.path.exists(path_asal):
                with open(path_asal, "rb") as f:
                    data_bytes = f.read()

                hash_val = hashlib.sha256(data_bytes).hexdigest()
                encrypted_bytes = rc4_encrypt(data_bytes, krc4)
                
                nama_target = f"{no_registrasi}_{tipe}.enc"
                path_target = os.path.join(config.STORAGE_DIR, nama_target)
                with open(path_target, "wb") as f:
                    f.write(encrypted_bytes)

                if tipe == "KTP":
                    path_ktp_enc, hash_ktp = path_target, hash_val
                else:
                    path_shm_enc, hash_shm = path_target, hash_val

        path_denah_stego = ""
        path_denah_asal = self.dokumen_terpilih["DENAH"]
        if path_denah_asal and os.path.exists(path_denah_asal):
            pesan_rahasia = f"{no_registrasi}|{kode_segel}|{nama}"
            nama_denah_target = f"{no_registrasi}_DENAH_STEGO.png"
            path_denah_stego = os.path.join(config.STORAGE_DIR, nama_denah_target)
            try:
                sisip_pesan(path_denah_asal, pesan_rahasia, path_denah_stego)
            except Exception as e:
                print(f"[STEGO] Peringatan steganografi: {e}")
                path_denah_stego = ""

        id_petugas_aktif = session.Session.id_user or 1
        data_permohonan = {
            "no_registrasi": no_registrasi,
            "nama_pemohon": nama,
            "jenis_bangunan": jenis_bangunan,
            "luas_bangunan": luas_bangunan,
            "tanggal_pengajuan": time.strftime("%Y-%m-%d %H:%M:%S"),
            "nik_pemohon_enc": nik_enc,
            "alamat_enc": alamat_enc,
            "no_telepon_enc": telepon_enc,
            "koordinat_tanah_enc": koordinat_enc,
            "uraian_permohonan_enc": uraian_enc,
            "id_petugas": id_petugas_aktif
        }

        try:
            db.simpan_permohonan(data_permohonan)

            db.simpan_berkas(
                no_registrasi=no_registrasi,
                path_ktp_enc=path_ktp_enc,
                hash_ktp=hash_ktp,
                path_shm_enc=path_shm_enc,
                hash_shm=hash_shm,
                path_denah_lsb=path_denah_stego,
                kode_segel=kode_segel
            )

            riwayat_blok = db.semua_blok() or []
            bc = Blockchain(riwayat_blok)
            payload_dokumen = f"{no_registrasi}|{nama}|{hash_ktp}|{hash_shm}|{kode_segel}"
            hash_payload = hashlib.sha256(payload_dokumen.encode()).hexdigest()

            blok_baru = bc.tambah(no_registrasi, nama, hash_payload, id_petugas_aktif)
            
            data_blok_db = {
                "no_registrasi": no_registrasi,
                "id_user": id_petugas_aktif,
                "hash_dokumen": hash_payload,
                "prev_hash": getattr(blok_baru, 'prev_hash', '0' * 64),
                "curr_hash": getattr(blok_baru, 'curr_hash', hash_payload),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            db.simpan_blok(data_blok_db)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Gagal menyimpan data permohonan:\n{e}")
            return

        QMessageBox.information(
            self, "Registrasi Izin Berhasil",
            f"Permohonan infrastruktur berhasil diamankan!\n\n"
            f"Nomor Registrasi : {no_registrasi}\n"
            f"Kode Segel      : {kode_segel}\n"
            f"Nama Pemohon    : {nama}\n\n"
            f"✔ Super-Enkripsi (Vigenère + AES-256) aktif pada data NIK & Alamat.\n"
            f"✔ Berkas KTP & SHM terenkripsi RC4 Stream Cipher.\n"
            f"✔ Metadata tersemat ke Denah via Steganografi LSB.\n"
            f"✔ Blok baru berhasil ditambahkan ke Ledger Blockchain."
        )

        # Reset Formulir
        self.inp_nik.clear()
        self.inp_nama.clear()
        self.inp_telepon.clear()
        self.inp_alamat.clear()
        self.inp_jenis.clear()
        self.inp_luas.clear()
        self.inp_koordinat.clear()
        self.inp_uraian.clear()
        self.btn_ktp.setText("📁 Upload Scan KTP")
        self.btn_shm.setText("📁 Upload Sertifikat Tanah (SHM)")
        self.btn_denah.setText("🖼️ Upload Denah LSB (.png)")
        self.dokumen_terpilih = {"KTP": None, "SHM": None, "DENAH": None}

    def proses_logout(self):
        """Membersihkan sesi aktif dan menutup jendela operator."""
        session.Session.username = None
        session.Session.role = None
        session.Session.id_user = None
        session.Session.dongle_rahasia = None
        self.close()