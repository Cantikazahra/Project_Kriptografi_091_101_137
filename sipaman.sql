-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 07 Nov 2026 pada 07.32
-- Versi server: 10.4.32-MariaDB
-- Versi PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `sipaman`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `berkas`
--

CREATE TABLE `berkas` (
  `id_berkas` int(11) NOT NULL,
  `no_registrasi` varchar(50) NOT NULL,
  `path_ktp_enc` text NOT NULL,
  `hash_ktp` varchar(64) NOT NULL,
  `path_shm_enc` text NOT NULL,
  `hash_shm` varchar(64) NOT NULL,
  `path_sk_enc` text DEFAULT NULL,
  `path_denah_lsb` varchar(255) NOT NULL,
  `kode_segel` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `blockchain_log`
--

CREATE TABLE `blockchain_log` (
  `id_blok` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  `no_registrasi` varchar(50) NOT NULL,
  `id_user` int(11) NOT NULL,
  `hash_dokumen` varchar(64) NOT NULL,
  `prev_hash` varchar(64) NOT NULL,
  `curr_hash` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `pengguna`
--

CREATE TABLE `pengguna` (
  `id_user` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(64) NOT NULL,
  `salt_key` varchar(50) NOT NULL,
  `face_encoding` text NOT NULL,
  `role_akses` enum('Petugas Lapangan','Verifikator') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `permohonan`
--

CREATE TABLE `permohonan` (
  `id_permohonan` int(11) NOT NULL,
  `no_registrasi` varchar(50) NOT NULL,
  `nama_pemohon` varchar(150) NOT NULL,
  `jenis_bangunan` varchar(100) NOT NULL,
  `luas_bangunan` decimal(10,2) NOT NULL,
  `status_permohonan` varchar(50) NOT NULL,
  `tanggal_pengajuan` datetime NOT NULL,
  `nik_pemohon_enc` text NOT NULL,
  `alamat_enc` text NOT NULL,
  `no_telepon_enc` text NOT NULL,
  `koordinat_tanah_enc` text NOT NULL,
  `uraian_permohonan_enc` text DEFAULT NULL,
  `catatan_verifikasi_enc` text DEFAULT NULL,
  `alasan_revisi_enc` text DEFAULT NULL,
  `id_petugas` int(11) NOT NULL,
  `id_verifikator` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `berkas`
--
ALTER TABLE `berkas`
  ADD PRIMARY KEY (`id_berkas`),
  ADD KEY `no_registrasi` (`no_registrasi`);

--
-- Indeks untuk tabel `blockchain_log`
--
ALTER TABLE `blockchain_log`
  ADD PRIMARY KEY (`id_blok`),
  ADD KEY `no_registrasi` (`no_registrasi`),
  ADD KEY `id_user` (`id_user`);

--
-- Indeks untuk tabel `pengguna`
--
ALTER TABLE `pengguna`
  ADD PRIMARY KEY (`id_user`);

--
-- Indeks untuk tabel `permohonan`
--
ALTER TABLE `permohonan`
  ADD PRIMARY KEY (`id_permohonan`),
  ADD UNIQUE KEY `no_registrasi` (`no_registrasi`),
  ADD KEY `id_petugas` (`id_petugas`),
  ADD KEY `id_verifikator` (`id_verifikator`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `berkas`
--
ALTER TABLE `berkas`
  MODIFY `id_berkas` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `blockchain_log`
--
ALTER TABLE `blockchain_log`
  MODIFY `id_blok` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `pengguna`
--
ALTER TABLE `pengguna`
  MODIFY `id_user` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `permohonan`
--
ALTER TABLE `permohonan`
  MODIFY `id_permohonan` int(11) NOT NULL AUTO_INCREMENT;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `berkas`
--
ALTER TABLE `berkas`
  ADD CONSTRAINT `berkas_ibfk_1` FOREIGN KEY (`no_registrasi`) REFERENCES `permohonan` (`no_registrasi`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Ketidakleluasaan untuk tabel `blockchain_log`
--
ALTER TABLE `blockchain_log`
  ADD CONSTRAINT `blockchain_log_ibfk_1` FOREIGN KEY (`no_registrasi`) REFERENCES `permohonan` (`no_registrasi`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `blockchain_log_ibfk_2` FOREIGN KEY (`id_user`) REFERENCES `pengguna` (`id_user`) ON UPDATE CASCADE;

--
-- Ketidakleluasaan untuk tabel `permohonan`
--
ALTER TABLE `permohonan`
  ADD CONSTRAINT `permohonan_ibfk_1` FOREIGN KEY (`id_petugas`) REFERENCES `pengguna` (`id_user`) ON UPDATE CASCADE,
  ADD CONSTRAINT `permohonan_ibfk_2` FOREIGN KEY (`id_verifikator`) REFERENCES `pengguna` (`id_user`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
