"""
Modul Verifikasi Wajah Biometrik SIPAMAN.
Mencocokkan wajah dari webcam dengan face_encoding pengguna di MySQL.
"""
import json
import time
import cv2
import face_recognition
import numpy as np
import db


def verifikasi_wajah(username: str) -> bool:
    user = db.ambil_pengguna(username)
    if not user:
        print("[FACE] User tidak ditemukan di database.")
        return False

    raw_encoding = user.get("face_encoding")
    if not raw_encoding:
        print("[FACE] Pengguna belum memiliki data biometrik wajah terdaftar.")
        return False

    try:
        daftar_fitur = json.loads(raw_encoding)
        vektor_terdaftar = np.array(daftar_fitur, dtype=np.float64)
    except Exception as e:
        print(f"[FACE] Gagal memuat data vektor wajah user: {e}")
        return False

    # cv2.CAP_DSHOW wajib di Windows agar kamera tidak freeze / not responding
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[FACE] Kamera tidak dapat diakses.")
        return False

    terverifikasi = False
    pesan_status = "Arahkan wajah ke kamera..."
    warna_status = (0, 255, 255)
    waktu_mulai = time.time()
    batas_waktu_detik = 15  # Timeout 15 detik

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        # Cek batas waktu (timeout)
        if time.time() - waktu_mulai > batas_waktu_detik:
            pesan_status = "Waktu verifikasi habis!"
            warna_status = (0, 0, 255)
            break

        # Resize frame 0.5x agar komputasi pengenalan wajah ringan & lancar
        frame_kecil = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_kecil = cv2.cvtColor(frame_kecil, cv2.COLOR_BGR2RGB)

        lokasi_wajah = face_recognition.face_locations(rgb_kecil)

        if len(lokasi_wajah) == 1:
            encodings = face_recognition.face_encodings(rgb_kecil, lokasi_wajah)
            if len(encodings) > 0:
                vektor_sekarang = encodings[0]
                jarak = face_recognition.face_distance([vektor_terdaftar], vektor_sekarang)[0]
                cocok = face_recognition.compare_faces([vektor_terdaftar], vektor_sekarang, tolerance=0.50)[0]

                top, right, bottom, left = [coord * 2 for coord in lokasi_wajah[0]]

                if cocok:
                    terverifikasi = True
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, f"Wajah Cocok! (Dist: {jarak:.2f})", (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow("SIPAMAN - Verifikasi Wajah", frame)
                    cv2.waitKey(1000)
                    break
                else:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, "Wajah Tidak Cocok!", (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        elif len(lokasi_wajah) > 1:
            pesan_status = "Peringatan: Lebih dari 1 wajah terdeteksi!"
            warna_status = (0, 165, 255)

        cv2.putText(frame, pesan_status, (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, warna_status, 2)
        cv2.putText(frame, "Tekan 'Q' untuk membatalkan", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        cv2.imshow("SIPAMAN - Verifikasi Wajah", frame)

        # Tombol 'q' untuk keluar
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return terverifikasi