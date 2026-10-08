from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FILES = ["1_profil_mahasiswa_umum.csv", "2_prestasi_mahasiswa.csv",
         "3_generasi_pertama_kuliah.csv", "4_status_sosial_ekonomi.csv",
         "5_riwayat_ipk_semester.csv"]
NEEDS = ["Biaya kuliah", "Waktu kuliah dan kerja", "Belajar dan akademik",
         "Adaptasi dan dukungan", "Kegiatan dan prestasi"]


def load_data():
    profile, achievements, family, economy, history = [
        pd.read_csv(RAW / name, sep=";", encoding="utf-8-sig") for name in FILES]
    for frame in [profile, family, economy]:
        if not frame.ID_Mahasiswa.is_unique:
            raise ValueError("ID mahasiswa tidak unik pada tabel profil.")
    if history.duplicated(["ID_Mahasiswa", "Semester_Ke"]).any():
        raise ValueError("Riwayat memiliki semester ganda.")
    for frame in [achievements, family, economy, history]:
        if not set(frame.ID_Mahasiswa).issubset(set(profile.ID_Mahasiswa)):
            raise ValueError("Ada ID sumber yang tidak tercatat pada profil.")
    d = profile.merge(family, on="ID_Mahasiswa", validate="one_to_one").merge(
        economy.drop(columns="Sumber_Pembiayaan"), on="ID_Mahasiswa", validate="one_to_one")
    counts = achievements.groupby("ID_Mahasiswa").size().rename("catatan_kegiatan")
    d = d.merge(counts, left_on="ID_Mahasiswa", right_index=True, how="left", validate="one_to_one")
    d["catatan_kegiatan"] = d.catatan_kegiatan.fillna(0).astype(int)
    d["fg"] = d.Status_Generasi_Pertama.eq("Ya")
    d["work"] = d.Bekerja_Sambil_Kuliah.eq("Ya")
    d["sch"] = d.Status_Penerima_Beasiswa.eq("Ya")
    d["achievement"] = d.catatan_kegiatan.gt(0)
    d["interrupted"] = d.Status_Mahasiswa.isin(["Cuti", "Non-Aktif/DO"])
    for col in ["IP_Semester", "IPK_Kumulatif"]:
        if not history[col].between(0, 4).all():
            raise ValueError("Nilai harus berada pada skala 0 sampai 4.")
    return d, history, achievements


def initial_story(row):
    return {"ekonomi": row.Kategori_Ekonomi, "bekerja": bool(row.work),
            "beasiswa": bool(row.sch), "dukungan": int(row.Tingkat_Dukungan_Keluarga),
            "ukt": int(row.Kategori_UKT), "kendala": row.Kendala_Utama,
            "kebutuhan": [], "catatan": "", "consent": False}


def student_history(history, student_id):
    return history.loc[history.ID_Mahasiswa.eq(student_id)].sort_values("Semester_Ke").copy()


def cohort_history(d, history):
    wide = history.pivot(index="ID_Mahasiswa", columns="Semester_Ke", values="IPK_Kumulatif")
    ids = wide[[1, 2, 3, 4]].dropna().index
    joined = history.loc[history.ID_Mahasiswa.isin(ids) & history.Semester_Ke.le(4)].merge(
        d[["ID_Mahasiswa", "fg"]], on="ID_Mahasiswa", validate="many_to_one")
    result = joined.groupby(["fg", "Semester_Ke"]).IPK_Kumulatif.agg(["mean", "size"]).reset_index()
    return result, len(ids)


def context_metrics(d):
    low = d.loc[d.Kategori_Ekonomi.eq("Rendah")]
    fg_low = low.loc[low.fg]
    return {"n": len(d), "fg_n": int(d.fg.sum()),
            "fg_rate": float(d.fg.mean()) if len(d) else None,
            "fg_low_n": int(low.fg.sum()), "low_n": len(low),
            "fg_low_rate": float(low.fg.mean()) if len(low) else None,
            "work_fg_low_n": int(fg_low.work.sum()),
            "work_fg_low_rate": float(fg_low.work.mean()) if len(fg_low) else None}
