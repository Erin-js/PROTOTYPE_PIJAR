# Pemeriksaan PIJAR

Tanggal: 8 Oktober 2026, WIB.

## Hasil

- **14 tests lulus**, pemeriksaan persiapan deployment 15,11 detik. Mencakup seluruh halaman, navigasi kartu beranda, alur mahasiswa ke pendamping hingga umpan balik, persetujuan, kapasitas penuh, layanan tertutup, rujukan ganda, perpindahan status, tanggal jadwal, akses riwayat sendiri, penarikan persetujuan, dan pemisahan database antar-sesi demo publik.
- Rekonsiliasi sumber: 5.000 mahasiswa, 1.924 generasi pertama, 1.111 ekonomi rendah, 808 generasi pertama ekonomi rendah, dan 377 anggota kelompok tersebut bekerja. Catatan kegiatan 6.414 baris dan riwayat 25.099 baris.
- Kohort tetap semester 1–4: 3.603 mahasiswa, termasuk 1.345 generasi pertama dan 2.258 pembanding.
- Model Ridge cocok dengan notebook: MAE 0,2288133825; RMSE 0,2898798608; R² 0,5807524791; q interval 0,4845317453; cakupan 0,9109645507. Uji 1.213 mahasiswa (448 generasi pertama, 765 pembanding). Prediksi juga cocok dengan perhitungan independen melalui aljabar linear hingga toleransi 1e-10.
- Tabel cluster: C1 663, C2 1.648, C3 2.689. Total 5.000; agregat generasi pertama cocok dengan sumber.
- Hash SHA-256 semua salinan CSV cocok dengan lima sumber pada folder proyek. Sumber tidak diubah.
- Dependensi diperiksa: tidak ada kebutuhan paket yang rusak.
- Browser lokal menampilkan beranda dan JEJAK tanpa error. Grafik riwayat serta prediksi dibaca secara visual. Screenshot beranda disimpan sebagai `preview_beranda.png`.

## Lingkungan

Python 3.12.14; Streamlit 1.65.0; Plotly 7.1.0; pandas 3.0.1; NumPy 2.3.5; scikit-learn 1.9.1; SciPy 1.18.1. Server pemeriksaan hanya pada 127.0.0.1:8501. Tests menggunakan database terpisah pada `tests/output`, bukan penyimpanan pengguna.

## Batas pemeriksaan

Persiapan Cloud: penyimpanan default terpisah per sesi, konfigurasi tidak mengunci alamat server localhost, dependensi ada pada root repository, dan instruksi deployment tersedia di README. Deployment di Streamlit Community Cloud belum dijalankan atau diverifikasi.

Ini pengujian fungsi lokal, bukan audit keamanan produksi, validasi model dengan data nyata, atau evaluasi dampak pendampingan. Layanan, kapasitas, dan akun merupakan contoh. Integrasi kampus, autentikasi, notifikasi eksternal, dan pilot nyata belum dilakukan. Responsif mengikuti layout Streamlit dan CSS; pemeriksaan visual dilakukan pada desktop, bukan seluruh ukuran perangkat.

Pustaka pengujian mengikuti [dokumentasi resmi Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
