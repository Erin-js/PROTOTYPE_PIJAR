import hashlib
import json
import numpy as np
import pandas as pd
import pytest
from pijar.data import ROOT, FILES, cohort_history, context_metrics
from pijar.forecast import fit_forecast, predict_ip4


def test_source_integrity(data):
    d, history, achievements = data
    assert len(d) == 5000 and d.ID_Mahasiswa.is_unique
    assert len(history) == 25099 and len(achievements) == 6414
    verification = json.loads((ROOT / "data/reference/verification.json").read_text(encoding="utf-8"))
    for f in FILES:
        assert hashlib.sha256((ROOT / "data/raw" / f).read_bytes()).hexdigest() == verification["sha256"][f]
    assert d.catatan_kegiatan.sum() == len(achievements)
    assert d.catatan_kegiatan.eq(0).any()


def test_headlines_and_fixed_cohort(data):
    d, history, _ = data
    m = context_metrics(d)
    assert (m["fg_n"], m["low_n"], m["fg_low_n"], m["work_fg_low_n"]) == (1924,1111,808,377)
    trajectory, n = cohort_history(d, history)
    assert n == 3603
    assert trajectory.groupby("fg")["size"].nunique().eq(1).all()
    assert trajectory.groupby("fg")["size"].first().to_dict() == {False:2258,True:1345}
    assert context_metrics(d.iloc[:0])["fg_rate"] is None


def test_prediction_matches_notebook_and_independent_linear_algebra(data):
    d, history, _ = data
    model, metrics, test = fit_forecast(d, history)
    assert metrics["n"] == 1213
    assert metrics["mae"] == pytest.approx(0.22881338252638558, abs=1e-8)
    assert metrics["q"] == pytest.approx(0.4845317453, abs=1e-8)
    assert test.groupby("fg").size().to_dict() == {False:765,True:448}
    wide = history.pivot(index="ID_Mahasiswa", columns="Semester_Ke", values="IP_Semester")
    joined = d.set_index("ID_Mahasiswa")[["Angkatan"]].join(wide[[1,2,3,4]]).dropna()
    train = joined.loc[joined.Angkatan.le(2022)]
    x = train[[1,2,3]].to_numpy()
    mean, scale = x.mean(axis=0), x.std(axis=0)
    z = (x - mean) / scale
    y = train[4].to_numpy()
    coefficients = np.linalg.solve(z.T @ z + np.eye(3)*0.01, z.T @ (y-y.mean()))
    independent = np.clip(((test[["ip1","ip2","ip3"]].to_numpy()-mean)/scale) @ coefficients+y.mean(),0,4)
    np.testing.assert_allclose(test.pred, independent, atol=1e-10)
    assert test.pred.between(0,4).all() and test.low.le(test.pred).all() and test.high.ge(test.pred).all()
    pred = predict_ip4(model, metrics["q"], [2.7,3.0,3.2])
    assert 0 <= pred["low"] <= pred["pred"] <= pred["high"] <= 4
    for values in [[1,2], [1,2,5], [np.nan,2,3]]:
        with pytest.raises(ValueError):
            predict_ip4(model, metrics["q"], values)


def test_cluster_profile_integrity():
    profile = pd.read_csv(ROOT / "data/reference/profil_cluster.csv")
    assert profile.set_index("cluster").n.to_dict() == {"C1":663,"C2":1648,"C3":2689}
    assert profile.n.sum() == 5000
    assert (profile.generasi_pertama * profile.n).round().sum() == 1924
