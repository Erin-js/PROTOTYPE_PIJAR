# PIJAR

Kenali Kebutuhan, Dampingi Perjalanan.

Dashboard Streamlit untuk mendemonstrasikan pendampingan mahasiswa generasi pertama kuliah melalui CERITA, JEJAK, AKSES, dan KAWAL. Data mahasiswa adalah data fiktif CDW 2026. Direktori layanan adalah contoh. Manfaat intervensi belum diuji.

## Menjalankan

Python 3.12 direkomendasikan. Semua data dan aset aplikasi sudah berada di folder ini; tidak memerlukan notebook, folder induk, atau API eksternal saat dijalankan.

Pada Windows, klik dua kali `Jalankan_PIJAR.cmd`, lalu buka http://localhost:8501. Pemasangan dependensi memerlukan internet pada komputer baru. Lingkungan lokal `.venv` sudah disiapkan pada komputer ini.

Alternatif dari terminal di folder ini:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Pada macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Hentikan server dengan Ctrl+C pada terminal yang menjalankannya. Port 8501 dapat diganti jika dipakai aplikasi lain.

## Alur demonstrasi 5 menit

1. Pilih peran **Mahasiswa**. Profil awal dipilih dari generasi pertama ekonomi rendah yang bekerja. Pemilih profil memakai ID fiktif, bukan nama mahasiswa nyata.
2. Buka **CERITA**, pilih dukungan yang ingin dibicarakan, centang persetujuan, lalu simpan. Perubahan tidak menimpa sumber CSV. Persetujuan boleh tidak diberikan atau ditarik.
3. Buka **JEJAK** untuk melihat IP semester dan IPK kumulatif. Simulasi hanya memperkirakan IP4 dari IP1–3; garis putus-putus dan interval individu membedakannya dari nilai tercatat. Gunakan angka latihan manual untuk mencoba input lain.
4. Buka **AKSES**, pilih kebutuhan dan layanan contoh yang tersedia, centang konfirmasi pengajuan, lalu ajukan rujukan. Tanpa persetujuan, kebutuhan cocok, atau kapasitas, pengajuan ditolak. Rujukan aktif ganda untuk layanan yang sama tidak dibuat.
5. Ganti peran ke **Pendamping**. Buka rujukan, jadwalkan pendampingan, dan tulis catatan. Pengaturan dapat menutup layanan atau mengubah kapasitas contoh.
6. Kembali ke **Mahasiswa**, buka **KAWAL**. Jadwal dan catatan tampil; unduh pengingat kalender jika diperlukan. Pengingat hanya di aplikasi, bukan SMS/WhatsApp/email.
7. Pendamping dapat menandai layanan selesai. Mahasiswa lalu memberikan rating dan umpan balik. Mahasiswa juga dapat membatalkan rujukan aktif miliknya.
8. Ruang pendamping menampilkan konteks agregat, audit prediksi, serta metrik interaksi lokal. Rujukan selesai tidak membuktikan dampak pada IPK.

## Fitur yang benar-benar berjalan

| Fitur | Fungsi |
| --- | --- |
| CERITA | Form kondisi dan kebutuhan, koreksi data konfirmasi, persetujuan berbagi, penarikan persetujuan, penyimpanan SQLite. |
| JEJAK | Grafik interaktif dan tabel IP/IPK, catatan kegiatan per mahasiswa, Ridge IP4, interval split-conformal, simulasi input manual. |
| AKSES | Direktori contoh, filter kebutuhan, cek ketersediaan/kapasitas, konfirmasi pengajuan, pencegahan rujukan aktif ganda. |
| KAWAL | Status dan riwayat tindak lanjut, jadwal, catatan pendamping, pembatalan, unduhan CSV/kalender, rating dan umpan balik. |
| Ruang pendamping | Pengelolaan rujukan, ketersediaan layanan, konteks CSV berfilter, profil cluster agregat, audit prediksi antarkelompok. |

Tidak ada pengambilan keputusan bantuan otomatis, skor risiko DO, autentikasi produksi, integrasi sistem kampus, atau komunikasi eksternal.

## Data, model, dan interpretasi

- Lima CSV dibaca dengan `sep=';'` dan dihubungkan melalui `ID_Mahasiswa`. Prestasi dihitung pada tingkat mahasiswa; peserta, finalis, dan juara sama-sama termasuk catatan kegiatan. Mahasiswa tanpa catatan tetap masuk penyebut.
- Sumber pembiayaan adalah sumber terbesar, bukan satu-satunya. UKT adalah kelompok biaya, bukan jumlah rupiah. Dukungan keluarga adalah persepsi 1–5. Kendala utama bukan satu-satunya kendala.
- Konteks lintasan memakai mahasiswa yang sama pada semester 1–4 (n=3.603 sebelum filter). Filter dapat mengubah n; nilainya ditampilkan.
- Model Ridge alpha 0,01 mengacu pada kandidat terpilih di notebook, bukan menjalankan seleksi ulang dengan data uji. Latih ulang pada 2019–2022, kalibrasi 2023, uji 2024 (n=1.213). Fitur hanya IP1–3; target IP4. Generasi pertama dan ekonomi hanya untuk audit.
- MAE uji sekitar 0,229 poin; baseline IP3 sekitar 0,272 poin. Cakupan interval nominal 90% teramati sekitar 91,1% pada uji. Rentang individu bukan CI rata-rata kelompok atau jaminan nilai setiap mahasiswa.
- Bagi mahasiswa dengan IP4 sudah tercatat, tampilan prediksi bersifat retrospektif. Bagi angkatan lain atau input manual, hasil adalah demonstrasi model dan tidak mendapat klaim akurasi tersendiri.
- Tiga profil cluster ditampilkan dari tabel hasil notebook dan tidak berubah dengan filter dashboard atau formulir CERITA. Cluster bukan identitas/risiko individu dan tidak dipakai untuk pemilihan bantuan. Fitur utamanya ekonomi, bekerja, dukungan keluarga, tanggungan, kendala utama; bukan generasi pertama atau capaian.
- Kondisi akademik cuti/nonaktif/DO adalah snapshot sumber, bukan outcome prospektif atau ramalan.

## Penyimpanan dan batas keamanan

Default aplikasi memakai database sementara yang terpisah untuk setiap sesi browser. Perubahan CERITA, rujukan, log status, jadwal, umpan balik, dan pengaturan layanan tetap tersedia saat berpindah halaman atau peran dalam sesi yang sama, tetapi dapat hilang setelah sesi berakhir, koneksi tersambung ulang, atau server dimulai ulang. Demo online tidak menyediakan percakapan lintas pengunjung atau akun pendamping nyata.

Peluncur Windows `Jalankan_PIJAR.cmd` mengaktifkan mode lokal melalui `PIJAR_STORAGE_MODE=local`. Dalam mode ini, `storage/pijar.sqlite3` dibuat otomatis dan menyimpan interaksi lintas sesi di komputer yang sama. `PIJAR_DB_PATH` juga dapat menentukan lokasi database lokal. Jangan mengaktifkan kedua pengaturan tersebut pada demo publik tanpa autentikasi. Angka waktu respons/umpan balik bersumber dari tindakan pengguna demo, bukan rekayasa hasil pilot. Nilai belum tersedia ditampilkan sebagai belum tersedia.

Pemilih peran adalah demonstrasi, **bukan autentikasi**. Pengunjung bisa berpindah peran/profil contoh dalam sesi demo mereka. SQLite tidak dienkripsi. Gunakan data fiktif saja; jangan unggah atau masukkan data pribadi nyata. Peluncur lokal mendengarkan `127.0.0.1`. Deployment publik hanya untuk demonstrasi dengan data simulasi, bukan layanan kampus operasional.

Penarikan persetujuan membuat rujukan dan ringkasan kebutuhan tidak tampil di ruang pendamping. Riwayat tetap ada di penyimpanan lokal dan masih terlihat oleh mahasiswa. Ini bukan implementasi lengkap kebijakan retensi/penghapusan data. Pembatalan rujukan tetap tersedia bagi mahasiswa.

Untuk pilot nyata dibutuhkan autentikasi/otorisasi server, kontrol peran dan penugasan pendamping, pengelolaan persetujuan dan retensi, enkripsi, audit keamanan, layanan terverifikasi, validasi model dengan data nyata, dan evaluasi dampak. Pergantian peran demo tidak dapat menggantikan kebutuhan tersebut.

## Deploy ke Streamlit Community Cloud

1. Buka https://share.streamlit.io dan pilih **Create app**.
2. Pilih repository **Erin-js/PROTOTYPE_PIJAR**, branch **main**, main file path **app.py**.
3. Buka **Advanced settings**, pilih **Python 3.12**. Tidak perlu mengisi secrets untuk demo ini.
4. Klik **Deploy** dan tunggu pemasangan `requirements.txt` selesai.

Semua CSV fiktif, referensi, dan aset yang diperlukan sudah ada di repository. Database lokal, lingkungan `.venv`, secrets, dan keluaran pengujian tidak diunggah. Jangan mengatur `PIJAR_STORAGE_MODE=local` atau `PIJAR_DB_PATH` di Cloud: pertahankan penyimpanan terpisah per sesi untuk demo publik.

Panduan platform: [Deploy your app on Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Struktur folder

```text
PROTOTYPE_PIJAR/
  app.py
  pijar/                 logika data, prediksi, grafik, penyimpanan
  assets/style.css       tampilan hijau-biru PIJAR
  data/raw/              salinan lima CSV CDW, tidak diubah
  data/reference/        tabel notebook dan rekonsiliasi hasil
  docs/                  keputusan rancangan final dan hasil pemeriksaan
  storage/               SQLite lokal, dibuat saat berjalan
  tests/                 pengujian data, alur rujukan, dan antarmuka
  scripts/               pemeriksaan referensi untuk pengembangan
  requirements.txt
  requirements-dev.txt
  .streamlit/config.toml
  run.ps1
  Jalankan_PIJAR.cmd
```

## Pengujian

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

Tests memakai database sementara dan tidak menghapus atau mencampuri interaksi aplikasi pengguna. `scripts/prepare_reference.py` hanya untuk memperbarui referensi saat pengembangan, memerlukan ekspor notebook pada folder induk, dan tidak perlu dijalankan untuk memakai aplikasi.

Dasar pengujian antarmuka: [dokumentasi resmi Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
