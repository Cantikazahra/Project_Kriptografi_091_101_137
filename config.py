import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")

# MySQL (XAMPP)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "sipaman"

# Dongle: berkas kunci di flashdisk
DONGLE_WAJIB = True              # False jika saat testing tanpa flashdisk
DONGLE_HANYA_REMOVABLE = True
DONGLE_FILENAME = "SIPAMAN_DONGLE.key"
DONGLE_HASH = "c6e99952510f43c90cf0dd391238b258247448752036a8d0dd47d93bb94a5789"

# Wajah
FACE_AKTIF = True

ROLE_OPERATOR = "operator"
ROLE_VERIFIKATOR = "verifikator"