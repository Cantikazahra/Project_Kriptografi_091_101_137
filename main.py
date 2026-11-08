import os
import sys

print("[1/5] Memulai SIPAMAN...")

from PyQt5.QtWidgets import QApplication, QMessageBox, QStackedWidget

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("[2/5] Memuat konfigurasi & modul...")
import config
import db
import session
from auth import dongle
from ui.login_page import LoginPage
from ui.signup_page import SignUpPage


class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()

        try:
            db.init_db()
            print("[INFO] Database terhubung dan siap.")
        except Exception as e:
            print(f"[WARNING] Inisialisasi database: {e}")

        # Menyimpan referensi daftar jendela aktif agar tidak tertutup otomatis oleh garbage collector
        self.active_windows = []

        self.login_page = LoginPage(self.show_signup_page, self.show_dashboard)
        self.signup_page = SignUpPage(self.show_login_page)

        self.addWidget(self.login_page)     # Index 0: Login
        self.addWidget(self.signup_page)    # Index 1: Sign Up
        self.setCurrentIndex(0)
        self.setWindowTitle("SIPAMAN - Role-Based Secure Access")
        self.resize(500, 620)

    def show_signup_page(self):
        self.setCurrentIndex(1)

    def show_login_page(self):
        self.setCurrentIndex(0)

    def show_dashboard(self, username, role):
        session.Session.username = username
        session.Session.role = role

        try:
            if role == "operator":
                from ui.operator_page import OperatorWindow
                window_portal = OperatorWindow()
            else:
                from ui.verifikator import VerifikatorWindow
                window_portal = VerifikatorWindow()

            # Buka portal sebagai jendela mandiri baru
            window_portal.show()
            self.active_windows.append(window_portal)
            print(f"[INFO] Portal {role} berhasil dibuka untuk pengguna: {username}")

            # Kembalikan jendela login ke form awal agar bisa dipakai login role lain
            self.setCurrentIndex(0)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error Portal", f"Gagal membuka portal {role}:\n{e}")

    def logout(self):
        session.Session.username = None
        session.Session.role = None
        self.setCurrentIndex(0)
        self.resize(500, 620)


if __name__ == "__main__":
    print("[3/5] Menginisialisasi QApplication...")
    app = QApplication(sys.argv)
    
    print("[4/5] Membuka jendela antarmuka...")
    window = MainApp()
    window.show()
    
    print("[5/5] Aplikasi siap digunakan!")
    sys.exit(app.exec_())