from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pijar.data import FILES, load_data, context_metrics, cohort_history
from pijar.forecast import fit_forecast


def main():
    reference = ROOT / "data" / "reference"
    reference.mkdir(parents=True, exist_ok=True)
    source = ROOT.parent / "output_visualisasi_cdw" / "analisis_lanjutan"
    for name in ["profil_cluster.csv", "validasi_cluster.csv", "audit_prediksi_per_kelompok.csv", "kinerja_prediksi_holdout.csv", "pemisahan_angkatan.csv"]:
        shutil.copy2(source / "tabel" / name, reference / name)
    d, history, achievements = load_data()
    _, metrics, test = fit_forecast(d, history)
    trajectory, cohort_n = cohort_history(d, history)
    hashes = {f: hashlib.sha256((ROOT / "data" / "raw" / f).read_bytes()).hexdigest() for f in FILES}
    summary = {"source": "CDW 2026 / Real World Fake Data", "metrics": context_metrics(d),
               "achievement_rows": len(achievements), "history_rows": len(history),
               "cohort_1_4_n": cohort_n, "forecast": metrics, "sha256": hashes,
               "source_priority": "Frame 8.png dan keputusan terakhir pengguna mengungguli nama serta rancangan lama."}
    (reference / "verification.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    test.groupby("fg")[["ip1", "ip2", "ip3", "pred", "target"]].mean().to_csv(reference / "group_forecast.csv")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
