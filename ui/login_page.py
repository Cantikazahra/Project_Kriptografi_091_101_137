import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt

# Menambahkan root path untuk impor modul
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db
import config
import session
from kripto.hashing import cek_password


class LoginPage(QWidget):
    def __init__(self, switch_to_signup_callback=None, on_login_success=None):
        super().__init__()
        self.switch_to_signup = switch_to_signup_callback
        self.on_login_success = on_login_success
        self.selected_role = "operator"  # Default role
        
        self.setWindowTitle("SIPAMAN - Login Portal")
        self.showMaximized()
        self.setStyleSheet("background-color: #090d16; color: #f8fafc;")

        # Layout Utama
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Container Kotak Kartu Tengah
        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QFrame {
                background-color: #0f172a; 
                border: 1px solid #1e293b; 
                border-radius: 12px;
                padding: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)

        # Header Judul
        title = QLabel("🛡️ SIPAMAN")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8; border: none;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("Sistem Perizinan Bangunan Aman - Secure Access")
        subtitle.setStyleSheet("font-size: 11px; color: #64748b; margin-bottom: 15px; border: none;")
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        role_layout = QHBoxLayout()
        self.btn_op_tab = QPushButton("Operator Portal")
        self.btn_ver_tab = QPushButton("Verificator Portal")
        
        self.btn_op_tab.setStyleSheet(self.tab_style_active())
        self.btn_ver_tab.setStyleSheet(self.tab_style_inactive())
        
        self.btn_op_tab.clicked.connect(lambda: self.set_role("operator"))
        self.btn_ver_tab.clicked.connect(lambda: self.set_role("verifikator"))
        
        role_layout.addWidget(self.btn_op_tab)
        role_layout.addWidget(self.btn_ver_tab)
        card_layout.addLayout(role_layout)

        card_layout.addSpacing(15)

        # Input Username
        lbl_user = QLabel("Username")
        lbl_user.setStyleSheet("font-size: 12px; color: #cbd5e1; border: none; font-weight: bold;")
        card_layout.addWidget(lbl_user)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("yaya cute")
        self.username_input.setFixedHeight(38)
        self.username_input.setStyleSheet(self.input_style())
        card_layout.addWidget(self.username_input)

        # Input Password
        card_layout.addSpacing(10)
        lbl_pass = QLabel("Password")
        lbl_pass.setStyleSheet("font-size: 12px; color: #cbd5e1; border: none; font-weight: bold;")
        card_layout.addWidget(lbl_pass)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter secure password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(38)
        self.password_input.setStyleSheet(self.input_style())
        card_layout.addWidget(self.password_input)

        # Tombol Login
        card_layout.addSpacing(20)
        self.btn_login = QPushButton("Masuk Sistem")
        self.btn_login.setFixedHeight(42)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #0d9488; color: white; font-weight: bold; 
                border-radius: 6px; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #0f766e; }
        """)
        self.btn_login.clicked.connect(self.handle_login)
        card_layout.addWidget(self.btn_login)

        # Tombol Navigasi ke Sign Up
        if self.switch_to_signup:
            self.btn_to_signup = QPushButton("Don't have an account? Register")
            self.btn_to_signup.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #38bdf8; font-size: 12px; border: none; margin-top: 10px;
                }
                QPushButton:hover { color: #7dd3fc; text-decoration: underline; }
            """)
            self.btn_to_signup.clicked.connect(self.switch_to_signup)
            card_layout.addWidget(self.btn_to_signup)

        main_layout.addWidget(card)

    def set_role(self, role):
        self.selected_role = role
        if role == "operator":
            self.btn_op_tab.setStyleSheet(self.tab_style_active())
            self.btn_ver_tab.setStyleSheet(self.tab_style_inactive())
        else:
            self.btn_op_tab.setStyleSheet(self.tab_style_inactive())
            self.btn_ver_tab.setStyleSheet(self.tab_style_active())

    def tab_style_active(self):
        return "background-color: #0d9488; color: white; font-weight: bold; border-radius: 6px; padding: 8px; font-size: 11px; border: none;"

    def tab_style_inactive(self):
        return "background-color: #1e293b; color: #94a3b8; font-weight: bold; border-radius: 6px; padding: 8px; font-size: 11px; border: 1px solid #334155;"

    def input_style(self):
        return """
            QLineEdit {
                background-color: #1e293b; border: 1px solid #334155; 
                border-radius: 6px; padding: 5px 10px; color: white; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #0d9488; }
        """

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Peringatan", "Username dan Password tidak boleh kosong!")
            return

        try:
            user = db.ambil_pengguna(username)
        except Exception as e:
            QMessageBox.critical(self, "Error Database", f"Gagal melakukan login:\n{e}")
            return

        # 1. Validasi spesifik jika username belum terdaftar di database
        if not user:
            QMessageBox.warning(
                self, 
                "Username Belum Terdaftar", 
                f"Maaf, username '{username}' belum terdaftar di sistem SIPAMAN.\n\n"
                "Silakan periksa kembali atau lakukan registrasi akun terlebih dahulu."
            )
            return

        # 2. Cek kecocokan password hash + salt jika username ditemukan
        if not cek_password(password, user["salt"], user["password_hash"]):
            QMessageBox.warning(
                self, 
                "Password Salah", 
                "Kata sandi (password) yang Anda masukkan salah.\n"
                "Silakan periksa kembali."
            )
            return

        # 3. Cek role portal yang dipilih
        if user["role"] != self.selected_role:
            QMessageBox.warning(
                self, "Akses Portal Salah",
                f"Akun ini terdaftar sebagai role '{user['role']}'. Silakan pilih tab portal yang sesuai."
            )
            return

        # 4. Pengecekan Kunci Fisik USB Dongle
        from auth import dongle
        kunci_usb = dongle.muat_kunci_dongle()
        if config.DONGLE_WAJIB and not kunci_usb:
            QMessageBox.critical(
                self, "Akses Ditolak",
                "USB Dongle Fisik tidak terdeteksi atau tidak sah!\nSilakan colokkan flashdisk kunci SIPAMAN."
            )
            return

        # 5. Pengecekan Face Recognition Biometrik
        if config.FACE_AKTIF:
            from auth import face
            if not face.verifikasi_wajah(username):
                QMessageBox.warning(
                    self, "Gagal Biometrik",
                    "Verifikasi wajah gagal atau dibatalkan!"
                )
                return

        # 6. Simpan seluruh state ke sesi aktif
        session.Session.username = user["username"]
        session.Session.id_user = user["id_user"]
        session.Session.role = user["role"]
        session.Session.dongle_key = kunci_usb
        session.Session.dongle_rahasia = kunci_usb

        self.password_input.clear()
        if self.on_login_success:
            self.on_login_success(username, user["role"])