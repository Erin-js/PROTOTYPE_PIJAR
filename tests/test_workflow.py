from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pytest
from pijar.store import Store


def test_story_persistence_and_raw_is_separate(store, payload):
    store.save_story("MHS00001", payload)
    assert Store(store.path).story("MHS00001")[0] == payload


def test_requires_consent_matching_need_and_confirmation(store, payload):
    with pytest.raises(ValueError):
        store.refer("MHS00001", "biaya", "Biaya kuliah", True)
    payload["consent"] = False
    store.save_story("MHS00001", payload)
    with pytest.raises(ValueError):
        store.refer("MHS00001", "biaya", "Biaya kuliah", True)
    payload["consent"] = True
    store.save_story("MHS00001", payload)
    for service, need, confirm in [("biaya","Biaya kuliah",False),("akademik","Biaya kuliah",True),("biaya","Adaptasi dan dukungan",True)]:
        with pytest.raises(ValueError):
            store.refer("MHS00001", service, need, confirm)


def test_closed_full_duplicate_services(store, payload):
    store.save_story("MHS00001", payload)
    store.set_service("biaya", False, 1, "Pendamping")
    with pytest.raises(ValueError):
        store.refer("MHS00001", "biaya", "Biaya kuliah", True)
    store.set_service("biaya", True, 1, "Pendamping")
    rid = store.refer("MHS00001", "biaya", "Biaya kuliah", True)
    with pytest.raises(ValueError, match="sudah ada"):
        store.refer("MHS00001", "biaya", "Biaya kuliah", True)
    store.save_story("MHS00002", payload)
    with pytest.raises(ValueError, match="penuh"):
        store.refer("MHS00002", "biaya", "Biaya kuliah", True)
    store.cancel(rid, "MHS00001")
    assert store.refer("MHS00002", "biaya", "Biaya kuliah", True) > rid


def test_status_dates_roles_ownership_and_feedback(store, payload):
    store.save_story("MHS00001", payload)
    rid = store.refer("MHS00001", "biaya", "Biaya kuliah", True)
    with pytest.raises(ValueError):
        store.update_referral(rid,"Selesai",None,"","Pendamping")
    with pytest.raises(ValueError):
        store.update_referral(rid,"Dijadwalkan","2000-01-01","","Pendamping")
    with pytest.raises(ValueError):
        store.update_referral(rid,"Dijadwalkan","2099-01-01","","Mahasiswa")
    with pytest.raises(ValueError):
        store.cancel(rid,"MHS00002")
    with pytest.raises(ValueError):
        store.feedback(rid,"MHS00001",5,"belum selesai")
    day = (datetime.now(ZoneInfo("Asia/Jakarta"))+timedelta(days=1)).date().isoformat()
    store.update_referral(rid,"Dijadwalkan",day,"Contoh jadwal","Pendamping")
    assert store.referrals("MHS00001")[0]["appointment"] == day
    store.update_referral(rid,"Selesai",None,"Contoh selesai","Pendamping")
    store.feedback(rid,"MHS00001",4,"Membantu")
    assert store.referrals("MHS00001")[0]["rating"] == 4
    assert len(store.events(rid,"MHS00001")) == 3
    assert store.referrals("MHS00002") == []
    with pytest.raises(ValueError):
        store.events(rid,"MHS00002")
    with pytest.raises(ValueError):
        store.feedback(rid,"MHS00002",5,"akses salah")


def test_withdrawal_hides_from_mentor_and_blocks_update(store, payload):
    store.save_story("MHS00001", payload)
    rid = store.refer("MHS00001", "biaya", "Biaya kuliah", True)
    assert len(store.referrals(role="Pendamping")) == 1
    payload["consent"] = False
    store.save_story("MHS00001", payload)
    assert store.referrals(role="Pendamping") == []
    assert len(store.referrals("MHS00001")) == 1
    with pytest.raises(ValueError):
        store.update_referral(rid,"Perlu tindak lanjut",None,"","Pendamping")
    store.cancel(rid,"MHS00001")


def test_invalid_payload_and_service_settings(store, payload):
    payload["kebutuhan"] = ["Skor bantuan"]
    with pytest.raises(ValueError):
        store.save_story("MHS00001",payload)
    with pytest.raises(ValueError):
        store.set_service("biaya",True,8,"Mahasiswa")
    with pytest.raises(ValueError):
        store.set_service("biaya",True,-1,"Pendamping")
