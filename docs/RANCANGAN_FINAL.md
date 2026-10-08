# Rancangan final solusi PIJAR

## Acuan dan keputusan

Prioritas: gambar infografis **Frame 8.png** dan keputusan terbaru pada chat **Analisis dataset dan ide infografis**, kemudian naskah versi diperluas dan notebook visualisasi yang telah memuat clustering serta prediksi. Nama lama JEMBATAN pada mockup dan naskah lama tidak menjadi nama aplikasi.

Riwayat lain yang diperiksa: **Revisi narasi infografis CDW2026** (bahasa awam, tanpa em dash, OR bukan persentase peluang) dan **Jelaskan alur rancangan infografis** (diagnosis lebih dahulu, data dictionary, perubahan pie chart beasiswa). Blueprint/naskah lama yang berhenti pada diagnosis merupakan tahap rancangan terdahulu, bukan pembatas bagi solusi final yang diminta pengguna sekarang.

Berkas kerja yang ditelaah: naskah versi diperluas, naskah final terdahulu, rekomendasi rancangan, pengembangan analisis inti, penjelasan rancangan, penjelasan lomba dan kamus data, lima CSV, notebook visualisasi, serta ekspor model/cluster. Notebook eksplorasi dan notebook awal merupakan sumber pengembangan sebelumnya; model operasional demo mengikuti spesifikasi tervalidasi pada notebook visualisasi terbaru, bukan model klasifikasi prestasi lama. Gambar terbaru menjadi acuan identitas dan empat fitur, bukan sumber angka yang mengalahkan CSV.

## Masalah yang ingin ditangani

Mahasiswa generasi pertama bukan kelompok dengan kondisi seragam. Kategori ekonomi, aktivitas bekerja, dukungan keluarga, dan perkembangan nilai perlu dibaca bersama. IPK terakhir saja tidak cukup; menerima beasiswa juga tidak berarti seluruh kebutuhan terselesaikan. Data fiktif memberi landasan konsep, bukan bukti masalah pada kampus tertentu.

## Bentuk solusi

PIJAR merupakan alat pendampingan lokal dengan PETA sebagai alur kerja:

1. **Petakan / CERITA:** mahasiswa mengonfirmasi kondisi dan kebutuhan, dapat memperbarui atau menarik persetujuan berbagi.
2. **Evaluasi / JEJAK:** riwayat IP dan IPK dibedakan; simulasi IP4 dan ketidakpastian merupakan bahan percakapan.
3. **Tautkan / AKSES:** kebutuhan terkonfirmasi dicocokkan secara transparan ke kategori layanan contoh. Pilihan bukan skor otomatis atau keputusan kelayakan.
4. **Audit / KAWAL:** rujukan, jadwal, catatan, penyelesaian, serta umpan balik dapat dicatat dan dipantau.

Ruang pendamping mengelola rujukan yang mendapat persetujuan aktif. Konteks mahasiswa hanya berupa agregat; prediksi dan clustering tidak menentukan antrian, bantuan, maupun label risiko.

## Ruang lingkup yang disepakati melalui rancangan

- Semua dependensi aplikasi, salinan data, aset, dokumentasi, dan tests berada di folder PROTOTYPE_PIJAR.
- SQLite sementara terpisah per sesi untuk demo online. Peluncur Windows mengaktifkan persistensi lokal. Tidak ada data nyata, akun kampus, API eksternal, atau notifikasi otomatis.
- Data layanan dan kapasitas adalah contoh eksplisit, bukan hasil inventarisasi kampus.
- Peran mahasiswa/pendamping dapat dipilih untuk demo, bukan autentikasi atau keamanan produksi.
- Metrik akses/tindak lanjut dimulai kosong lalu berubah dari aksi demo; tidak ditambah hasil pilot rekaan.
- Prediksi IP4 dipakai sesuai validasi notebook; tidak diperluas ke IP semester lain tanpa data/model yang sesuai.
- Gambar referensi menginspirasi warna hijau-biru dan gaya ramah mahasiswa. Dashboard menggunakan grafik interaktif, label jelas, dan whitespace; bukan menyalin poster menjadi halaman panjang.

## Ukuran keberhasilan demo

Form tersimpan selama navigasi dan perpindahan peran dalam sesi demo yang sama; sesi pengunjung lain terpisah. Mode lokal mempertahankan interaksi setelah reload. Pengajuan sebelum persetujuan ditolak; kebutuhan/layanan yang tidak cocok ditolak; kapasitas penuh dan rujukan aktif ganda ditangani; pendamping dapat memperbarui status; mahasiswa melihat jadwal dan memberi umpan balik sesudah selesai; angka sumber dan model dapat direkonsiliasi. Ini pengujian fungsi, bukan bukti efektivitas intervensi.

## SWOT ringkas

| Aspek | Isi |
| --- | --- |
| Kekuatan | Kebutuhan, perkembangan, dan pendampingan terhubung. |
| Kelemahan | Data simulasi; manfaat belum teruji. |
| Peluang | Kolaborasi dengan layanan kampus. |
| Ancaman | Kebocoran data, stigma, dan keterbatasan layanan. |
