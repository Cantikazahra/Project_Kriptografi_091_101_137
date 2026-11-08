import os
import sys
import json
import cv2
import numpy as np
import face_recognition

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt

# Menambahkan root path untuk impor modul database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db
from kripto.hashing import hash_password


class SignUpPage(QWidget):
    def __init__(self, switch_to_login_callback=None):
        super().__init__()
        self.switch_to_login = switch_to_login_callback
        self.face_encoding = None

        # Layout Utama
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(40, 20, 40, 20)

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
        title = QLabel("🛡️ SIPAMAN Register")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8; border: none;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("Create secure credentials with Face Biometrics.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; margin-bottom: 10px; border: none;")
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        # Input Username
        lbl_user = QLabel("Username")
        lbl_user.setStyleSheet("font-size: 12px; color: #cbd5e1; border: none; font-weight: bold;")
        card_layout.addWidget(lbl_user)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. operator.baru")
        self.username_input.setFixedHeight(38)
        self.username_input.setStyleSheet(self.input_style())
        card_layout.addWidget(self.username_input)

        # Input Password
        card_layout.addSpacing(8)
        lbl_pass = QLabel("Password")
        lbl_pass.setStyleSheet("font-size: 12px; color: #cbd5e1; border: none; font-weight: bold;")
        card_layout.addWidget(lbl_pass)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter secure password (min. 8 chars)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(38)
        self.password_input.setStyleSheet(self.input_style())
        card_layout.addWidget(self.password_input)

        # Pilihan Role
        card_layout.addSpacing(8)
        lbl_role = QLabel("System Role")
        lbl_role.setStyleSheet("font-size: 12px; color: #cbd5e1; border: none; font-weight: bold;")
        card_layout.addWidget(lbl_role)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["operator", "verifikator"])
        self.role_combo.setFixedHeight(38)
        self.role_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b; border: 1px solid #334155; 
                border-radius: 6px; padding: 5px 10px; color: white; font-size: 13px;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView {
                background-color: #1e293b; color: white; selection-background-color: #0d9488;
            }
        """)
        card_layout.addWidget(self.role_combo)

        # Modul Scan Biometrik Wajah
        card_layout.addSpacing(12)
        lbl_face = QLabel("Biometrik Wajah")
        lbl_face.setStyleSheet("font-size: 12px; color: #cbd5e1; border: none; font-weight: bold;")
        card_layout.addWidget(lbl_face)

        self.btn_capture_face = QPushButton("📷 Pindai & Daftarkan Wajah")
        self.btn_capture_face.setFixedHeight(38)
        self.btn_capture_face.setStyleSheet("""
            QPushButton {
                background-color: #1e293b; color: #38bdf8; font-weight: bold; 
                border: 1px solid #38bdf8; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background-color: #0c4a6e; }
        """)
        self.btn_capture_face.clicked.connect(self.capture_face_data)
        card_layout.addWidget(self.btn_capture_face)

        self.lbl_face_status = QLabel("Status: Wajah belum didaftarkan")
        self.lbl_face_status.setStyleSheet("font-size: 11px; color: #ef4444; border: none; margin-top: 2px;")
        card_layout.addWidget(self.lbl_face_status)

        # Tombol Register
        card_layout.addSpacing(18)
        self.btn_register = QPushButton("Register Account →")
        self.btn_register.setFixedHeight(42)
        self.btn_register.setStyleSheet("""
            QPushButton {
                background-color: #0d9488; color: white; font-weight: bold; 
                border-radius: 6px; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #0f766e; }
        """)
        self.btn_register.clicked.connect(self.handle_register)
        card_layout.addWidget(self.btn_register)

        # Tombol Kembali ke Login
        if self.switch_to_login:
            self.btn_back = QPushButton("Already have an account? Sign In")
            self.btn_back.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #38bdf8; font-size: 12px; border: none; margin-top: 10px;
                }
                QPushButton:hover { color: #7dd3fc; text-decoration: underline; }
            """)
            self.btn_back.clicked.connect(self.switch_to_login)
            card_layout.addWidget(self.btn_back)

        main_layout.addWidget(card)

    def input_style(self):
        return """
            QLineEdit {
                background-color: #1e293b; border: 1px solid #334155; 
                border-radius: 6px; padding: 5px 10px; color: white; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #0d9488; }
        """

    def capture_face_data(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            QMessageBox.critical(self, "Error Kamera", "Gagal membuka webcam. Periksa izin atau penutup fisik kamera!")
            return

        QMessageBox.information(
            self,
            "Instruksi Perekaman Wajah",
            "Jendela kamera akan terbuka.\n\n"
            "- Arahkan wajah lurus ke webcam dengan pencahayaan cukup.\n"
            "- Tekan tombol SPASI untuk memindai wajah.\n"
            "- Tekan Q untuk membatalkan."
        )

        captured_encoding = None

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            display_frame = frame.copy()
            cv2.putText(
                display_frame,
                "Tekan SPASI: Simpan Wajah | Q: Batal",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )
            cv2.imshow("SIPAMAN - Pendaftaran Wajah", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Tombol SPASI ditekan
                # Normalisasi frame ke RGB 8-bit murni
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_clean = np.ascontiguousarray(rgb_frame, dtype=np.uint8)

                boxes = face_recognition.face_locations(rgb_clean, model="hog")

                if len(boxes) == 0:
                    QMessageBox.warning(self, "Peringatan", "Wajah tidak terdeteksi! Pastikan pencahayaan cukup dan wajah menghadap ke kamera.")
                    continue
                elif len(boxes) > 1:
                    QMessageBox.warning(self, "Peringatan", "Terdeteksi lebih dari 1 wajah di frame! Pastikan hanya ada 1 orang.")
                    continue
                else:
                    encodings = face_recognition.face_encodings(rgb_clean, boxes)
                    if len(encodings) > 0:
                        captured_encoding = encodings[0].tolist()
                        break
            elif key == ord('q') or key == 27:
                break

        cap.release()
        cv2.destroyAllWindows()

        if captured_encoding is not None:
            self.face_encoding = captured_encoding
            self.lbl_face_status.setText("Status: ✓ Wajah berhasil direkam")
            self.lbl_face_status.setStyleSheet("font-size: 11px; color: #10b981; border: none; margin-top: 2px;")
            QMessageBox.information(self, "Sukses", "Data biometrik wajah berhasil direkam!")

    def handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Peringatan", "Username dan Password tidak boleh kosong!")
            return
        if len(password) < 8:
            QMessageBox.warning(self, "Peringatan", "Password minimal 8 karakter!")
            return
        if self.face_encoding is None:
            QMessageBox.warning(self, "Peringatan", "Wajib merekam data wajah terlebih dahulu untuk Multi-Factor Authentication!")
            return

        try:
            salt, password_hash = hash_password(password)   # SHA-256 + salt
            face_json = json.dumps(self.face_encoding)       # Serialisasi vektor wajah ke JSON string
            
            try:
                db.tambah_pengguna(username, password_hash, salt, role, face_json)
            except TypeError:
                db.tambah_pengguna(username, password_hash, salt, role)
                if hasattr(db, 'simpan_face_encoding'):
                    db.simpan_face_encoding(username, face_json)

        except Exception as e:
            if "Duplicate" in str(e) or "1062" in str(e):
                QMessageBox.warning(self, "Gagal", "Username sudah dipakai.")
            else:
                QMessageBox.critical(self, "Error Database", f"Gagal mendaftarkan akun:\n{e}")
            return

        QMessageBox.information(self, "Sukses", f"Akun '{username}' berhasil didaftarkan lengkap dengan data biometrik wajah!")
        self.username_input.clear()
        self.password_input.clear()
        self.face_encoding = None
        self.lbl_face_status.setText("Status: Wajah belum didaftarkan")
        self.lbl_face_status.setStyleSheet("font-size: 11px; color: #ef4444; border: none; margin-top: 2px;")
        
        if self.switch_to_login:
            self.switch_to_login()