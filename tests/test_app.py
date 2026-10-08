from pathlib import Path
from streamlit.testing.v1 import AppTest
from pijar.store import Store

APP = Path(__file__).resolve().parents[1] / "app.py"


def check(at):
    assert not at.exception, [e.message for e in at.exception]


def test_pages_and_home_navigation(monkeypatch, tmp_path):
    monkeypatch.setenv("PIJAR_DB_PATH",str(tmp_path / "ui.sqlite3"))
    at = AppTest.from_file(APP,default_timeout=90).run()
    check(at)
    at.button(key="home_JEJAK").click().run()
    check(at)
    assert at.radio(key="page").value == "JEJAK"
    for page in ["CERITA", "AKSES", "KAWAL", "Tentang", "Beranda"]:
        at.radio(key="page").set_value(page).run()
        check(at)
    at.selectbox(key="role").set_value("Pendamping").run()
    check(at)
    at.radio(key="page").set_value("Tentang").run()
    check(at)


def test_public_demo_sessions_are_isolated(monkeypatch):
    monkeypatch.delenv("PIJAR_DB_PATH", raising=False)
    monkeypatch.delenv("PIJAR_STORAGE_MODE", raising=False)
    first = AppTest.from_file(APP, default_timeout=90).run()
    second = AppTest.from_file(APP, default_timeout=90).run()
    check(first)
    check(second)
    first_path = Path(first.session_state.demo_storage.name) / "pijar.sqlite3"
    second_path = Path(second.session_state.demo_storage.name) / "pijar.sqlite3"
    assert first_path != second_path
    sid = first.selectbox(key="student_id").value
    first.radio(key="page").set_value("CERITA").run()
    first.multiselect(key=f"story_needs_{sid}").set_value(["Biaya kuliah"])
    first.checkbox(key=f"story_consent_{sid}").check()
    first.button(key="save_story").click().run()
    check(first)
    assert Store(first_path).story(sid)[0] is not None
    assert Store(second_path).story(sid)[0] is None
    first.selectbox(key="role").set_value("Pendamping").run()
    check(first)
    assert Path(first.session_state.demo_storage.name) / "pijar.sqlite3" == first_path


def test_student_to_mentor_to_feedback(monkeypatch, tmp_path):
    db = tmp_path / "flow_ui.sqlite3"
    monkeypatch.setenv("PIJAR_DB_PATH",str(db))
    at = AppTest.from_file(APP,default_timeout=90).run()
    check(at)
    sid = at.selectbox(key="student_id").value
    at.radio(key="page").set_value("CERITA").run()
    at.multiselect(key=f"story_needs_{sid}").set_value(["Biaya kuliah"])
    at.checkbox(key=f"story_consent_{sid}").check()
    at.button(key="save_story").click().run()
    check(at)
    at.radio(key="page").set_value("AKSES").run()
    at.checkbox(key="agree_biaya").check()
    at.button(key="submit_biaya").click().run()
    check(at)
    records = Store(db).referrals(sid)
    assert len(records) == 1
    rid = records[0]["id"]
    at.selectbox(key="role").set_value("Pendamping").run()
    check(at)
    at.button(key=f"update_save_{rid}").click().run()
    check(at)
    assert Store(db).referrals(sid)[0]["status"] == "Dijadwalkan"
    at.button(key=f"update_save_{rid}").click().run()
    check(at)
    assert Store(db).referrals(sid)[0]["status"] == "Selesai"
    at.selectbox(key="role").set_value("Mahasiswa").run()
    at.radio(key="page").set_value("KAWAL").run()
    check(at)
    at.button(key=f"feedback_save_{rid}").click().run()
    check(at)
    assert Store(db).referrals(sid)[0]["rating"] == 3


def test_no_referral_without_confirmation(monkeypatch, tmp_path):
    monkeypatch.setenv("PIJAR_DB_PATH",str(tmp_path / "no_consent.sqlite3"))
    at = AppTest.from_file(APP,default_timeout=90).run()
    at.radio(key="page").set_value("AKSES").run()
    check(at)
    assert all(b.disabled for b in at.button if b.label == "Ajukan rujukan")
