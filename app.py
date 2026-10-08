from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from html import escape
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from pijar.data import load_data, initial_story, student_history, cohort_history, context_metrics, NEEDS
from pijar.forecast import fit_forecast, predict_ip4
from pijar.store import Store, ACTIVE, TRANSITIONS
from pijar.charts import personal_history, individual_prediction, group_prediction, cohort_chart, polish, GREEN, BLUE, ORANGE

st.set_page_config(page_title="PIJAR | Dampingi Perjalanan", page_icon="🌱", layout="wide")
st.markdown(f"<style>{(ROOT / 'assets' / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_data
def datasets():
    return load_data()


@st.cache_resource
def prediction_model():
    return fit_forecast(*datasets()[:2])


def runtime_store():
    if os.getenv("PIJAR_DB_PATH") or os.getenv("PIJAR_STORAGE_MODE") == "local":
        return Store()
    if "demo_storage" not in st.session_state:
        st.session_state.demo_storage = tempfile.TemporaryDirectory(prefix="pijar_demo_")
    return Store(Path(st.session_state.demo_storage.name) / "pijar.sqlite3")


def fnum(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def count(value):
    return fnum(value, 0)


def csv_export(frame):
    safe = frame.copy()
    for col in safe.select_dtypes(include=["object", "str"]):
        safe[col] = safe[col].map(lambda value: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else value)
    return safe.to_csv(index=False).encode("utf-8-sig")


def hero(eyebrow, title, description):
    st.markdown(f'<div class="hero"><div class="eyebrow">{escape(eyebrow)}</div><h1>{escape(title)}</h1><p>{escape(description)}</p></div>', unsafe_allow_html=True)


def notice(text):
    st.markdown(f'<div class="notice">{escape(text)}</div>', unsafe_allow_html=True)


def chart(fig, key):
    st.plotly_chart(fig, width="stretch", key=key, config={"displayModeBar": False})


def act(fn, message):
    try:
        fn()
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.session_state.flash = message
        st.rerun()


def go_page(page):
    st.session_state.page = page


def home():
    hero("Kenali kebutuhan, dampingi perjalanan", "Setiap perjalanan punya kebutuhan.",
         "Mulai dari ceritamu. Lihat perkembangan, temukan dukungan, lalu lanjutkan langkah bersama pendamping.")
    if not confirmed:
        notice("Langkah pertama: isi CERITA dan konfirmasi kebutuhan sebelum mengajukan rujukan.")
    else:
        notice(f"Kebutuhanmu sudah dikonfirmasi. {len(story['kebutuhan'])} kebutuhan dipilih. Kamu dapat memperbaruinya kapan saja.")
    cols = st.columns(4)
    cards = [("CERITA", "Kenali kondisimu", "Konfirmasi kebutuhan ekonomi, aktivitas bekerja, beasiswa, dan dukungan keluarga."),
             ("JEJAK", "Baca perkembanganmu", "Lihat riwayat nilai dan simulasi IP semester 4 sebagai bahan percakapan."),
             ("AKSES", "Temukan dukunganmu", "Pilih layanan contoh yang cocok dengan kebutuhan yang kamu konfirmasi."),
             ("KAWAL", "Lanjutkan langkahmu", "Pantau rujukan, jadwal pendampingan, pengingat, dan umpan balik.")]
    for i, (name, title, body) in enumerate(cards):
        with cols[i]:
            st.markdown(f'<div class="feature-card"><div class="feature-number">0{i+1} / {name}</div><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
            st.button(f"Buka {name}", key=f"home_{name}", width="stretch", on_click=go_page, args=(name,))
    st.subheader("Perjalananmu saat ini")
    cols = st.columns(3)
    own = store.referrals(student_id)
    cols[0].metric("IPK terakhir tercatat", fnum(row.IPK_Mahasiswa))
    cols[1].metric("Rujukan aktif", sum(r["status"] in ACTIVE for r in own))
    cols[2].metric("Rujukan selesai", sum(r["status"] == "Selesai" for r in own))
    left, right = st.columns([1.7, 1])
    with left, st.container(border=True):
        st.subheader("Nilai berkembang, cerita berlanjut")
        chart(personal_history(history), "home_history")
    with right, st.container(border=True):
        st.subheader("Langkah berikutnya")
        scheduled = [r for r in own if r["status"] == "Dijadwalkan"]
        if scheduled:
            for r in scheduled[:3]:
                st.write(f"**{service_names[r['service_id']]}**")
                st.caption(f"Tanggal contoh: {r['appointment']}. Buka KAWAL untuk detail.")
        elif own:
            st.write("Rujukanmu sudah tercatat. Lihat status dan pesan pendamping di KAWAL.")
        else:
            st.write("Belum ada rujukan. Setelah CERITA dikonfirmasi, kamu dapat memilih dukungan di AKSES.")
        st.caption("Pengingat muncul di aplikasi. Tidak ada pengiriman email atau WhatsApp.")
        st.divider()
        st.write("**Butuh jalur non-digital?**")
        st.caption("Rancangan layanan menyediakan opsi bertemu dosen wali atau unit kemahasiswaan. Kontak nyata belum terhubung pada demo ini.")


def cerita():
    hero("01 / CERITA", "Kamu yang paling tahu kondisimu.", "Periksa informasi contoh, pilih kebutuhanmu, lalu tentukan apakah ingin membagikannya kepada pendamping demo.")
    st.caption("Data asli CDW tidak diubah. Pembaruan formulir tersimpan sebagai konfirmasi terpisah di perangkat ini.")
    with st.form(f"cerita_{student_id}"):
        left, right = st.columns(2)
        with left:
            ekonomi = st.selectbox("Kategori ekonomi", ["Rendah", "Menengah", "Tinggi"], index=["Rendah", "Menengah", "Tinggi"].index(story["ekonomi"]))
            bekerja = st.checkbox("Bekerja sambil kuliah", value=story["bekerja"])
            beasiswa = st.checkbox("Menerima beasiswa", value=story["beasiswa"])
            ukt = st.number_input("Kelompok UKT (bukan nilai rupiah)", 1, 8, value=story["ukt"])
        with right:
            dukungan = st.slider("Persepsi dukungan keluarga", 1, 5, value=story["dukungan"], help="1 sangat rendah, 5 sangat tinggi.")
            kendala = st.selectbox("Kendala utama", ["Akademik", "Finansial", "Sosial", "Adaptasi"], index=["Akademik", "Finansial", "Sosial", "Adaptasi"].index(story["kendala"]))
            kebutuhan = st.multiselect("Dukungan yang ingin dibicarakan", NEEDS, default=story["kebutuhan"], key=f"story_needs_{student_id}")
        catatan = st.text_area("Catatan singkat (opsional)", value=story["catatan"], max_chars=1000, placeholder="Jangan masukkan NIK, nomor rekening, diagnosis, atau informasi sensitif nyata.")
        consent = st.checkbox("Saya mengonfirmasi informasi ini dan setuju membagikan kebutuhan kepada pendamping demo.", value=story["consent"], key=f"story_consent_{student_id}")
        st.caption("Kosongkan persetujuan lalu simpan untuk menarik akses pendamping. Riwayat lokal tidak otomatis terhapus. Demo tanpa autentikasi: gunakan informasi fiktif saja.")
        if st.form_submit_button("Simpan CERITA", type="primary", key="save_story"):
            payload = dict(ekonomi=ekonomi, bekerja=bekerja, beasiswa=beasiswa, dukungan=dukungan,
                           ukt=ukt, kendala=kendala, kebutuhan=kebutuhan, catatan=catatan, consent=consent)
            act(lambda: store.save_story(student_id, payload), "CERITA tersimpan. Kamu dapat lanjut ke AKSES atau memperbaruinya lagi.")
    if updated:
        st.caption(f"Pembaruan terakhir: {updated[:16].replace('T', ' ')} WIB")


def jejak():
    hero("02 / JEJAK", "Nilai akhir tidak menceritakan semuanya.", "Baca perkembangan nilai dari semester ke semester. Prediksi digunakan untuk percakapan, bukan menilai kemampuan atau kelayakan bantuan.")
    c = st.columns(3)
    c[0].metric("IP semester terakhir", fnum(history.iloc[-1].IP_Semester))
    c[1].metric("IPK kumulatif terakhir", fnum(history.iloc[-1].IPK_Kumulatif))
    c[2].metric("Semester tercatat", int(history.iloc[-1].Semester_Ke))
    chart(personal_history(history), "jejak_history")
    st.caption("IP mengukur satu semester. IPK kumulatif merangkum semester yang sudah ditempuh. Keduanya bukan satu ukuran yang sama.")
    with st.expander("Lihat tabel nilai dan catatan kegiatan"):
        st.dataframe(history[["Semester_Ke", "IP_Semester", "IPK_Kumulatif"]], hide_index=True, width="stretch")
        own_achievements = achievements.loc[achievements.ID_Mahasiswa.eq(student_id)]
        if own_achievements.empty:
            st.info("Tidak ada catatan kegiatan pada sumber. Ini tidak berarti mahasiswa tidak memiliki kemampuan atau pengalaman lain.")
        else:
            st.dataframe(own_achievements[["Bidang_Kegiatan", "Tingkat_Kegiatan", "Capaian_Prestasi", "Tahun_Perolehan"]], hide_index=True, width="stretch")
            st.caption("Catatan mencakup peserta, finalis, dan juara, bukan hanya kemenangan.")
    st.subheader("Simulasi IP semester 4")
    notice("Model hanya diuji untuk IP semester 4 dari IP semester 1–3. Tidak digunakan untuk menebak semester 5–8, DO, atau penerima bantuan.")
    indexed = history.set_index("Semester_Ke")
    defaults = [float(indexed.loc[s, "IP_Semester"]) if s in indexed.index else 3.0 for s in [1, 2, 3]]
    complete = all(s in indexed.index for s in [1, 2, 3])
    source = st.radio("Riwayat untuk simulasi", ["Riwayat mahasiswa contoh", "Angka latihan manual"], horizontal=True, key="prediction_source")
    if source == "Riwayat mahasiswa contoh" and not complete:
        st.info("Riwayat semester 1–3 belum lengkap. Gunakan angka latihan manual untuk mencoba model; hasilnya bukan prediksi mahasiswa ini.")
        return
    inputs = st.columns(3)
    values = [inputs[i].number_input(f"IP semester {i+1}", 0.0, 4.0, defaults[i], 0.01,
                                   disabled=source == "Riwayat mahasiswa contoh", key=f"ip_{student_id}_{source}_{i}") for i in range(3)]
    model, metrics, _ = prediction_model()
    result = predict_ip4(model, metrics["q"], values)
    actual = float(indexed.loc[4, "IP_Semester"]) if 4 in indexed.index and source == "Riwayat mahasiswa contoh" else None
    chart(individual_prediction(values, result, actual), "jejak_pred")
    c = st.columns(2)
    c[0].metric("Perkiraan IP semester 4", fnum(result["pred"]))
    c[1].metric("Rentang prediksi individu", f"{fnum(result['low'])} sampai {fnum(result['high'])}")
    if actual is not None:
        st.caption("IP4 sudah tercatat. Ini perbandingan retrospektif, bukan ramalan nilai masa depan mahasiswa ini.")
    st.caption("Rentang split-conformal dengan target cakupan 90%. Pada uji 2024, cakupan aktual 91,1%; bukan kepastian per mahasiswa atau tahun berikutnya. Angka latihan manual belum memiliki validasi tersendiri.")


def akses():
    hero("03 / AKSES", "Temukan pintu dukungan yang sesuai.", "Pilih dukungan dari kebutuhan yang sudah kamu konfirmasi. Kamu tetap menentukan layanan yang ingin diajukan.")
    notice("Semua layanan di sini adalah contoh. Kapasitas merupakan batas rujukan aktif dalam demo, bukan kuota kampus atau jadwal nyata.")
    if not confirmed:
        st.warning("Simpan CERITA dengan persetujuan berbagi sebelum mengajukan rujukan.")
    elif not story["kebutuhan"]:
        st.info("Pilih setidaknya satu kebutuhan di CERITA agar rujukan dapat dicocokkan.")
    only_match = st.checkbox("Tampilkan layanan sesuai kebutuhan saya", value=bool(story["kebutuhan"]), key="only_match")
    services = store.services()
    if only_match:
        services = [s for s in services if set(s["needs"]) & set(story["kebutuhan"])]
    if not services:
        st.info("Belum ada layanan sesuai filter. Matikan filter untuk melihat direktori contoh.")
    columns = st.columns(2)
    for i, service in enumerate(services):
        with columns[i % 2], st.container(border=True):
            st.subheader(service["name"])
            st.caption(f"{service['unit']} · {service['mode']}")
            st.write(service["description"])
            st.caption(f"Kebutuhan: {', '.join(service['needs'])}")
            available = service["available"] and service["remaining"] > 0
            st.write(f"**{'Tersedia' if available else 'Belum tersedia'}** | {service['remaining']} kapasitas demo tersisa")
            matching = [n for n in story["kebutuhan"] if n in service["needs"]]
            duplicate = any(r["service_id"] == service["id"] and r["status"] in ACTIVE for r in store.referrals(student_id))
            if duplicate:
                st.caption("Rujukan aktif sudah ada. Lihat KAWAL.")
            with st.form(f"refer_{student_id}_{service['id']}"):
                need = st.selectbox("Kebutuhan yang ingin dirujuk", matching or ["Konfirmasi dahulu di CERITA"], disabled=not matching)
                agree = st.checkbox("Saya memilih layanan ini dan setuju mengajukan rujukan.", key=f"agree_{service['id']}")
                if st.form_submit_button("Ajukan rujukan", disabled=not(confirmed and matching and available and not duplicate), key=f"submit_{service['id']}", width="stretch"):
                    act(lambda: store.refer(student_id, service["id"], need, agree), "Rujukan diajukan. Pantau tanggapan pendamping di KAWAL.")
    st.caption("Jika layanan tidak tersedia, rancangan PIJAR menyediakan jalur tatap muka melalui pendamping. Kontak kampus nyata belum tersedia di prototipe.")


def kawal():
    hero("04 / KAWAL", "Dukungan tidak berhenti di layar.", "Ikuti perkembangan rujukanmu. Lihat jadwal, catatan pendamping, dan beri umpan balik setelah layanan selesai.")
    records = store.referrals(student_id)
    if not records:
        st.info("Belum ada rujukan. Mulai dari CERITA, lalu pilih layanan di AKSES.")
        return
    c = st.columns(3)
    c[0].metric("Diajukan", sum(r["status"] == "Diajukan" for r in records))
    c[1].metric("Dijadwalkan", sum(r["status"] == "Dijadwalkan" for r in records))
    c[2].metric("Selesai", sum(r["status"] == "Selesai" for r in records))
    today = datetime.now(ZoneInfo("Asia/Jakarta")).date()
    for r in records:
        with st.container(border=True):
            st.subheader(f"#{r['id']} · {service_names[r['service_id']]}")
            st.write(f"**{r['status']}** · {r['need']}")
            st.caption(f"Diajukan: {r['created'][:16].replace('T',' ')} WIB")
            if r["appointment"] and r["status"] == "Dijadwalkan":
                day = datetime.fromisoformat(r["appointment"]).date()
                st.info(f"Jadwal contoh: {r['appointment']}. " + ("Tanggal sudah lewat; hubungi pendamping untuk tindak lanjut." if day < today else "Pengingat tersedia di halaman ini, bukan notifikasi eksternal."))
                compact = day.strftime("%Y%m%d")
                end = (day + timedelta(days=1)).strftime("%Y%m%d")
                ics = f"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//PIJAR//Demo//ID\r\nBEGIN:VEVENT\r\nUID:pijar-{r['id']}@local\r\nDTSTAMP:{datetime.now(ZoneInfo('UTC')).strftime('%Y%m%dT%H%M%SZ')}\r\nDTSTART;VALUE=DATE:{compact}\r\nDTEND;VALUE=DATE:{end}\r\nSUMMARY:PIJAR - Jadwal pendampingan demo\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
                st.download_button("Simpan pengingat kalender (.ics)", ics, file_name=f"pijar-{r['id']}.ics", mime="text/calendar", key=f"ics_{r['id']}")
            if r["note"]:
                st.write("**Catatan pendamping**")
                st.text(r["note"])
            with st.expander("Riwayat tindak lanjut"):
                st.dataframe(pd.DataFrame(store.events(r["id"], student_id)), hide_index=True, width="stretch")
            if r["status"] in ACTIVE:
                confirm_cancel = st.checkbox("Saya ingin membatalkan rujukan ini.", key=f"cancel_agree_{r['id']}")
                if st.button("Batalkan rujukan", key=f"cancel_{r['id']}", disabled=not confirm_cancel):
                    act(lambda: store.cancel(r["id"], student_id), "Rujukan dibatalkan.")
            if r["status"] == "Selesai":
                with st.form(f"feedback_{r['id']}"):
                    rating = st.slider("Seberapa membantu layanan ini?", 1, 5, value=int(r["rating"] or 3))
                    text = st.text_area("Umpan balik (opsional)", value=r["feedback"], max_chars=1000)
                    if st.form_submit_button("Simpan umpan balik", key=f"feedback_save_{r['id']}"):
                        act(lambda: store.feedback(r["id"], student_id, rating, text), "Umpan balik tersimpan.")
    export = pd.DataFrame(records).drop(columns=["student_id"], errors="ignore")
    st.download_button("Unduh riwayat rujukan saya", csv_export(export), "rujukan_saya.csv", "text/csv")


def context_dashboard():
    st.caption("Konteks dari lima CSV CDW 2026, bukan hasil penggunaan PIJAR. Semua data fiktif; persentase memiliki penyebut masing-masing.")
    cols = st.columns(3)
    econ = cols[0].multiselect("Ekonomi", ["Rendah", "Menengah", "Tinggi"], default=["Rendah", "Menengah", "Tinggi"])
    fg = cols[1].selectbox("Generasi pertama", ["Semua", "Ya", "Tidak"])
    work = cols[2].selectbox("Bekerja sambil kuliah", ["Semua", "Ya", "Tidak"])
    filtered = d.loc[d.Kategori_Ekonomi.isin(econ)].copy()
    for col, value in [("Status_Generasi_Pertama", fg), ("Bekerja_Sambil_Kuliah", work)]:
        if value != "Semua":
            filtered = filtered.loc[filtered[col].eq(value)]
    if filtered.empty:
        st.info("Tidak ada mahasiswa pada filter ini. Nilai tidak diganti dengan nol.")
        return
    m = context_metrics(filtered)
    c = st.columns(3)
    c[0].metric("Mahasiswa pada filter", count(m["n"]))
    c[1].metric("Generasi pertama", f"{fnum(m['fg_rate']*100,1)}%", help=f"{m['fg_n']} dari {m['n']} mahasiswa pada filter")
    c[2].metric("Rata-rata IPK terakhir", fnum(filtered.IPK_Mahasiswa.mean()))
    left, right = st.columns(2)
    with left:
        st.subheader("Kondisi ekonomi menurut kelompok")
        comp = pd.crosstab(filtered.Status_Generasi_Pertama, filtered.Kategori_Ekonomi, normalize="index").reindex(columns=["Rendah", "Menengah", "Tinggi"], fill_value=0)
        fig = go.Figure()
        for cat, color in [("Rendah", ORANGE), ("Menengah", GREEN), ("Tinggi", BLUE)]:
            fig.add_bar(x=comp[cat]*100, y=["Generasi pertama" if x == "Ya" else "Bukan generasi pertama" for x in comp.index], name=cat, orientation="h", marker_color=color)
        fig.update_layout(barmode="stack")
        fig.update_xaxes(title="Proporsi dalam masing-masing kelompok (%)", range=[0,100])
        chart(polish(fig), "context_econ")
    with right:
        st.subheader("Perkembangan pada mahasiswa yang sama")
        trajectory, n = cohort_history(filtered, all_history)
        chart(cohort_chart(trajectory), "context_history")
        st.caption(f"Kohort tetap semester 1–4, n={count(n)}. IPK kumulatif, bukan IP semester.")
    st.subheader("Ekonomi rendah: irisan kondisi dan capaian")
    low = filtered.loc[filtered.Kategori_Ekonomi.eq("Rendah")]
    if low.empty:
        st.info("Filter tidak mencakup mahasiswa ekonomi rendah.")
    else:
        matrix = low.groupby(["Status_Generasi_Pertama", "Bekerja_Sambil_Kuliah"]).agg(
            Jumlah=("ID_Mahasiswa", "size"), IPK=("IPK_Mahasiswa", "mean"), Catatan_kegiatan=("achievement", "mean"), Cuti_nonaktif=("interrupted", "mean")).reset_index()
        matrix["Catatan_kegiatan"] *= 100
        matrix["Cuti_nonaktif"] *= 100
        st.dataframe(matrix.rename(columns={"IPK":"Rerata IPK terakhir", "Catatan_kegiatan":"Ada catatan kegiatan (%)", "Cuti_nonaktif":"Cuti/nonaktif (%)"}), hide_index=True, width="stretch")
        st.caption("Status tercatat, bukan prediksi DO. Catatan kegiatan mencakup peserta, finalis, dan juara.")
    st.subheader("Tiga profil kebutuhan eksploratif")
    profile = pd.read_csv(ROOT / "data" / "reference" / "profil_cluster.csv")
    titles = {"C1":"Bekerja, kendala selain finansial", "C2":"Kendala utama finansial", "C3":"Tidak bekerja, kendala selain finansial"}
    for col, record in zip(st.columns(3), profile.to_dict("records")):
        with col, st.container(border=True):
            st.write(f"**{titles[record['cluster']]}**")
            st.caption(f"{record['cluster']} · n={count(record['n'])}")
            st.write(f"Generasi pertama: **{fnum(record['generasi_pertama']*100,1)}%**")
            st.write(f"Bekerja: **{fnum(record['bekerja']*100,1)}%**")
            st.write(f"Kendala finansial: **{fnum(record['finansial']*100,1)}%**")
            st.write(f"Dukungan keluarga: **{fnum(record['dukungan'],1)}/5**")
    st.caption("Profil di atas tetap mengacu pada seluruh 5.000 mahasiswa, tidak mengikuti filter. Hierarchical average linkage dengan jarak Gower; silhouette 0,347. Generasi pertama dan capaian tidak membentuk cluster. Ini bukan label risiko individu.")


def audit_model():
    model, metrics, test = prediction_model()
    st.subheader("Membaca arah, bukan menentukan nasib")
    chart(group_prediction(test), "audit_group_forecast")
    st.caption("Angkatan uji 2024, mahasiswa yang sama pada semester 1–3. Garis putus-putus menuju rata-rata prediksi IP4. Tidak ada interval rata-rata kelompok dari penggabungan interval individu.")
    c = st.columns(3)
    c[0].metric("MAE Ridge pada data uji", fnum(metrics["mae"], 3))
    c[1].metric("MAE memakai IP3 saja", fnum(metrics["baseline_mae"], 3))
    c[2].metric("Cakupan interval individu", f"{fnum(metrics['coverage']*100,1)}%")
    audit = test.groupby("fg").agg(n=("ID_Mahasiswa", "size"), MAE=("error", "mean"), Cakupan=("covered", "mean")).reset_index()
    audit["Kelompok"] = audit.fg.map({True:"Generasi pertama",False:"Bukan generasi pertama"})
    audit["Cakupan"] *= 100
    st.dataframe(audit[["Kelompok", "n", "MAE", "Cakupan"]].rename(columns={"Cakupan":"Cakupan (%)"}), hide_index=True, width="stretch")
    st.caption("MAE adalah rata-rata besar kesalahan, bukan nilai yang diprediksi. Lebih kecil berarti kesalahan lebih kecil. Perbedaan kesalahan antarkelompok bersifat deskriptif, bukan bukti diskriminasi atau bebas bias.")
    st.info("Ridge alpha 0,01 dipilih pada validasi notebook 2022 dari kandidat Ridge dan Random Forest. Aplikasi melatih ulang model terpilih pada 2019–2022, kalibrasi 2023, uji 2024. Fitur hanya IP1–3. Tidak ada klaim validasi masa depan atau efektivitas intervensi.")


def pendamping():
    hero("Ruang pendamping / demo", "Dari kebutuhan ke tindak lanjut.", "Kelola rujukan yang disetujui mahasiswa, periksa kapasitas layanan contoh, lalu pantau apa yang benar-benar ditindaklanjuti.")
    notice("Pemilih peran hanya demonstrasi, bukan login atau autentikasi. Jangan memasukkan data nyata atau membuka aplikasi ini ke jaringan publik.")
    tabs = st.tabs(["Rujukan dan layanan", "Konteks mahasiswa", "Audit prediksi"])
    with tabs[0]:
        records = store.referrals(role="Pendamping")
        cols = st.columns(3)
        cols[0].metric("Rujukan dengan persetujuan aktif", len(records))
        cols[1].metric("Perlu tindak lanjut", sum(r["status"] == "Perlu tindak lanjut" for r in records))
        cols[2].metric("Selesai", sum(r["status"] == "Selesai" for r in records))
        if records:
            response = [(datetime.fromisoformat(r["first_response"]) - datetime.fromisoformat(r["created"])).total_seconds()/3600 for r in records if r["first_response"]]
            rated = [r["rating"] for r in records if r["rating"] is not None]
            st.caption(f"Waktu respons rata-rata: {fnum(sum(response)/len(response),1)+' jam' if response else 'belum tersedia'} (n={len(response)}). Umpan balik: {fnum(sum(rated)/len(rated),1)+'/5' if rated else 'belum tersedia'} (n={len(rated)}). Hanya interaksi demo lokal, bukan hasil pilot kampus.")
            status_filter = st.multiselect("Filter status rujukan", list(TRANSITIONS), default=list(ACTIVE))
            filtered_records = [r for r in records if r["status"] in status_filter]
            if not filtered_records:
                st.info("Tidak ada rujukan pada filter status ini.")
            for r in filtered_records:
                with st.expander(f"#{r['id']} · {r['student_id']} · {service_names[r['service_id']]} · {r['status']}"):
                    st.write(f"**Kebutuhan yang dipilih:** {r['need']}")
                    shared = json.loads(r["story"])
                    st.write(f"Ekonomi: {shared['ekonomi']}. Bekerja: {'Ya' if shared['bekerja'] else 'Tidak'}. Beasiswa: {'Ya' if shared['beasiswa'] else 'Tidak'}. Dukungan keluarga: {shared['dukungan']}/5.")
                    if shared["catatan"]:
                        st.text(shared["catatan"])
                    options = TRANSITIONS[r["status"]]
                    if options:
                        with st.form(f"update_{r['id']}"):
                            status = st.selectbox("Status berikutnya", options)
                            appointment = st.date_input("Tanggal pendampingan contoh", min_value=datetime.now(ZoneInfo("Asia/Jakarta")).date())
                            note = st.text_area("Catatan untuk mahasiswa", value=r["note"], max_chars=1000)
                            if st.form_submit_button("Simpan tindak lanjut", key=f"update_save_{r['id']}"):
                                act(lambda: store.update_referral(r["id"], status, appointment.isoformat(), note, role), "Tindak lanjut tersimpan dan tampil di KAWAL mahasiswa.")
                    st.dataframe(pd.DataFrame(store.events(r["id"], role="Pendamping")), hide_index=True, width="stretch")
            summary = pd.DataFrame(records).groupby(["service_id","status"]).size().reset_index(name="jumlah")
            st.download_button("Unduh ringkasan layanan tanpa ID", csv_export(summary), "ringkasan_layanan.csv", "text/csv")
        else:
            st.info("Belum ada rujukan dengan persetujuan aktif. Coba alur CERITA dan AKSES pada peran mahasiswa demo; angka hasil layanan tidak direka.")
        with st.expander("Kelola ketersediaan layanan contoh"):
            svc = st.selectbox("Layanan", [s["id"] for s in store.services()], format_func=lambda x: service_names[x], key="manage_service")
            current = next(s for s in store.services() if s["id"] == svc)
            with st.form(f"service_{svc}"):
                available = st.checkbox("Buka pengajuan rujukan", value=current["available"])
                capacity = st.number_input("Batas rujukan aktif (demo)", 0, 100, current["capacity"])
                if st.form_submit_button("Simpan pengaturan layanan", key="save_service"):
                    act(lambda: store.set_service(svc, available, capacity, role), "Pengaturan layanan contoh tersimpan.")
            st.caption("Menutup layanan menghentikan pengajuan baru, bukan menghapus rujukan yang sudah ada.")
    with tabs[1]:
        context_dashboard()
    with tabs[2]:
        audit_model()


def tentang():
    hero("Tentang PIJAR", "Kenali kebutuhan. Dampingi perjalanan.", "Prototipe berbasis rancangan infografis Campus Data Week 2026. Belum menjadi aplikasi kampus atau intervensi yang terbukti efektif.")
    st.subheader("PETA menjadi cara kerja")
    for col, title, body in zip(st.columns(4), ["Petakan", "Evaluasi", "Tautkan", "Audit"],
                               ["Konfirmasi kondisi dan kebutuhan bersama mahasiswa.", "Baca perkembangan nilai dari semester awal.", "Pilih dukungan yang tersedia dan disepakati.", "Pantau akses, tindak lanjut, dan kesalahan model."]):
        with col, st.container(border=True):
            st.write(f"**{title}**")
            st.caption(body)
    st.subheader("Potensi dan batasnya")
    for col, title, body in zip(st.columns(4), ["Kekuatan", "Kelemahan", "Peluang", "Ancaman"],
                               ["Kebutuhan, perkembangan, dan pendampingan terhubung.", "Data simulasi; manfaat belum teruji.", "Kolaborasi dengan layanan kampus.", "Kebocoran data, stigma, dan keterbatasan layanan."]):
        with col, st.container(border=True):
            st.write(f"**{title}**")
            st.caption(body)
    with st.expander("Sumber, metode, dan batas prototipe", expanded=True):
        st.write("Sumber: lima CSV CDW 2026 (Real World Fake Data). Satu mahasiswa memiliki satu profil, banyak catatan kegiatan, dan banyak baris semester. Catatan kegiatan dihitung per mahasiswa, termasuk yang tidak memiliki catatan.")
        st.write("Mahasiswa generasi pertama: kedua orang tua belum pernah menempuh pendidikan tinggi. Status tersebut tidak otomatis berarti ekonomi rendah atau tidak mendapat dukungan.")
        st.write("Model prediksi hanya IP4 dari IP1–3. Clustering hanya disajikan sebagai konteks agregat. Data konfirmasi CERITA tidak mengubah CSV, hasil cluster, atau model prediksi.")
        st.write("Demo online menyimpan interaksi di database sementara terpisah per sesi. Pergantian peran dalam sesi yang sama tetap dapat melihat tindak lanjut. Mode lokal melalui peluncur Windows memakai SQLite persisten. Persetujuan dapat ditarik melalui CERITA sehingga rujukan tidak tampil di ruang pendamping. Database tidak dienkripsi; pemilih peran bukan kontrol keamanan produksi.")
        st.write("Sebelum digunakan dengan data nyata: siapkan autentikasi, pembatasan akses server, enkripsi, kebijakan retensi, pengelola layanan, validasi model pada data nyata, dan evaluasi pilot. Tidak ada skor risiko, keputusan bantuan otomatis, integrasi kampus, atau notifikasi eksternal.")


d, all_history, achievements = datasets()
store = runtime_store()
service_names = {s["id"]:s["name"] for s in store.services()}
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">P</div><div><div class="brand-name">PIJAR</div><div class="brand-sub">Dampingi perjalanan</div></div></div>', unsafe_allow_html=True)
    st.caption("USULAN PROTOTIPE · DATA SIMULASI")
    role = st.selectbox("Peran demonstrasi", ["Mahasiswa", "Pendamping"], key="role")
    st.caption("Bukan login. Gunakan data fiktif saja, jangan masukkan data pribadi nyata.")
    if os.getenv("PIJAR_DB_PATH") or os.getenv("PIJAR_STORAGE_MODE") == "local":
        st.caption("Mode lokal: interaksi disimpan di komputer ini.")
    else:
        st.caption("Demo online: interaksi terpisah per sesi dan dapat hilang saat sesi berakhir. Pergantian peran tetap dalam sesi yang sama.")
    complete_ids = set(all_history.loc[all_history.Semester_Ke.eq(4), "ID_Mahasiswa"])
    candidates = d.loc[d.fg & d.work & d.Kategori_Ekonomi.eq("Rendah") & d.Angkatan.eq(2024)
                      & d.ID_Mahasiswa.isin(complete_ids)].ID_Mahasiswa.tolist()
    ids = candidates[:3] + [x for x in d.ID_Mahasiswa if x not in candidates[:3]]
    student_id = st.selectbox("Mahasiswa contoh", ids, format_func=lambda x: x, key="student_id")
    row = d.set_index("ID_Mahasiswa").loc[student_id]
    st.caption(f"{'Generasi pertama' if row.fg else 'Bukan generasi pertama'} · {row.Fakultas} · Angkatan {row.Angkatan}")
    pages = ["Beranda", "CERITA", "JEJAK", "AKSES", "KAWAL"] if role == "Mahasiswa" else ["Ruang Pendamping"]
    pages += ["Tentang"]
    if st.session_state.get("page") not in pages:
        st.session_state.page = pages[0]
    page = st.radio("Navigasi", pages, key="page", label_visibility="collapsed")
    st.divider()
    st.caption("Data memulai percakapan. Mahasiswa dan pendamping menentukan tindak lanjut.")
history = student_history(all_history, student_id)
saved_story, updated = store.story(student_id)
story = saved_story or initial_story(row)
confirmed = saved_story is not None and story["consent"]
if st.session_state.get("flash"):
    st.success(st.session_state.pop("flash"))
{"Beranda":home, "CERITA":cerita, "JEJAK":jejak, "AKSES":akses,
 "KAWAL":kawal, "Ruang Pendamping":pendamping, "Tentang":tentang}[page]()
st.markdown('<div class="footer">PIJAR · CDW 2026 · Data mahasiswa simulasi. Layanan contoh. Keputusan bantuan tidak ditentukan oleh cluster atau prediksi.</div>', unsafe_allow_html=True)
