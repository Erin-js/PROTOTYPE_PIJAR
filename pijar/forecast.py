import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def fit_forecast(d, history):
    wide = history.pivot(index="ID_Mahasiswa", columns="Semester_Ke", values="IP_Semester")
    frame = d[["ID_Mahasiswa", "Angkatan", "fg", "Kategori_Ekonomi"]].merge(
        wide[[1, 2, 3, 4]].rename(columns={1: "ip1", 2: "ip2", 3: "ip3", 4: "target"}),
        left_on="ID_Mahasiswa", right_index=True, validate="one_to_one").dropna()
    features = ["ip1", "ip2", "ip3"]
    train = frame.Angkatan.le(2022)
    cal = frame.Angkatan.eq(2023)
    test = frame.Angkatan.eq(2024)
    if min(train.sum(), cal.sum(), test.sum()) == 0:
        raise ValueError("Kohort latih, kalibrasi, dan uji belum lengkap.")
    model = make_pipeline(StandardScaler(), Ridge(alpha=0.01))
    model.fit(frame.loc[train, features], frame.loc[train, "target"])
    residual = np.abs(frame.loc[cal, "target"] - np.clip(model.predict(frame.loc[cal, features]), 0, 4))
    rank = min(int(np.ceil((len(residual) + 1) * 0.9)), len(residual))
    q = float(np.sort(residual)[rank - 1])
    out = frame.loc[test].copy()
    out["pred"] = np.clip(model.predict(out[features]), 0, 4)
    out["low"], out["high"] = (out.pred - q).clip(0, 4), (out.pred + q).clip(0, 4)
    out["error"] = (out.target - out.pred).abs()
    out["covered"] = out.target.between(out.low, out.high)
    metrics = {"n": len(out), "mae": float(mean_absolute_error(out.target, out.pred)),
               "rmse": float(np.sqrt(mean_squared_error(out.target, out.pred))),
               "r2": float(r2_score(out.target, out.pred)), "coverage": float(out.covered.mean()),
               "baseline_mae": float(mean_absolute_error(out.target, out.ip3)), "q": q}
    return model, metrics, out


def predict_ip4(model, q, values):
    if len(values) != 3 or not all(np.isfinite(v) and 0 <= v <= 4 for v in values):
        raise ValueError("Masukkan tepat tiga IP semester pada skala 0 sampai 4.")
    pred = float(np.clip(model.predict(pd.DataFrame([values], columns=["ip1", "ip2", "ip3"]))[0], 0, 4))
    return {"pred": pred, "low": max(0, pred - q), "high": min(4, pred + q)}
