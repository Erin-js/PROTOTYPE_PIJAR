import json
import os
import sqlite3
from datetime import datetime, date
from zoneinfo import ZoneInfo
from pathlib import Path
from contextlib import contextmanager
from .data import ROOT, NEEDS

ACTIVE = ["Diajukan", "Dijadwalkan", "Perlu tindak lanjut"]
TRANSITIONS = {"Diajukan": ["Dijadwalkan", "Perlu tindak lanjut"],
               "Dijadwalkan": ["Selesai", "Perlu tindak lanjut"],
               "Perlu tindak lanjut": ["Dijadwalkan", "Selesai"],
               "Selesai": [], "Dibatalkan": []}


def now():
    return datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")


class Store:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv("PIJAR_DB_PATH", ROOT / "storage" / "pijar.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS stories(student_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS services(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS referrals(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL,
                    service_id TEXT NOT NULL, need TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL,
                    updated TEXT NOT NULL, appointment TEXT, note TEXT NOT NULL DEFAULT '', rating INTEGER,
                    feedback TEXT NOT NULL DEFAULT '', first_response TEXT);
                CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, referral_id INTEGER NOT NULL,
                    actor TEXT NOT NULL, action TEXT NOT NULL, created TEXT NOT NULL);
            """)
            for service in json.loads((ROOT / "data" / "services.json").read_text(encoding="utf-8")):
                db.execute("INSERT OR IGNORE INTO services VALUES (?,?)", (service["id"], json.dumps(service)))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def story(self, student_id):
        with self.connect() as db:
            row = db.execute("SELECT payload,updated FROM stories WHERE student_id=?", (student_id,)).fetchone()
        return (json.loads(row["payload"]), row["updated"]) if row else (None, None)

    def save_story(self, student_id, payload):
        if not set(payload["kebutuhan"]).issubset(NEEDS):
            raise ValueError("Jenis kebutuhan tidak dikenali.")
        if payload["ekonomi"] not in ["Rendah", "Menengah", "Tinggi"] or not 1 <= payload["dukungan"] <= 5:
            raise ValueError("Kondisi mahasiswa tidak valid.")
        if len(payload.get("catatan", "")) > 1000:
            raise ValueError("Catatan maksimal 1.000 karakter.")
        with self.connect() as db:
            db.execute("INSERT INTO stories VALUES (?,?,?) ON CONFLICT(student_id) DO UPDATE SET payload=excluded.payload,updated=excluded.updated",
                       (student_id, json.dumps(payload, ensure_ascii=False), now()))

    def services(self):
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM services ORDER BY rowid").fetchall()
            counts = dict(db.execute("SELECT service_id,COUNT(*) FROM referrals WHERE status IN (?,?,?) GROUP BY service_id", ACTIVE).fetchall())
        result = [json.loads(r["payload"]) for r in rows]
        for s in result:
            s["active"] = counts.get(s["id"], 0)
            s["remaining"] = max(0, s["capacity"] - s["active"])
        return result

    def set_service(self, service_id, available, capacity, role):
        if role != "Pendamping" or not 0 <= capacity <= 100:
            raise ValueError("Pengaturan layanan tidak diizinkan.")
        with self.connect() as db:
            row = db.execute("SELECT payload FROM services WHERE id=?", (service_id,)).fetchone()
            if row is None:
                raise ValueError("Layanan tidak ditemukan.")
            p = json.loads(row["payload"])
            p.update(available=bool(available), capacity=int(capacity))
            db.execute("UPDATE services SET payload=? WHERE id=?", (json.dumps(p), service_id))

    def refer(self, student_id, service_id, need, confirmed):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            story_row = db.execute("SELECT payload FROM stories WHERE student_id=?", (student_id,)).fetchone()
            story = json.loads(story_row["payload"]) if story_row else None
            if not story or not story["consent"] or need not in story["kebutuhan"] or not confirmed:
                raise ValueError("Konfirmasi kebutuhan dan persetujuan mahasiswa diperlukan.")
            row = db.execute("SELECT payload FROM services WHERE id=?", (service_id,)).fetchone()
            service = json.loads(row["payload"]) if row else None
            if not service or not service["available"] or need not in service["needs"]:
                raise ValueError("Layanan tidak tersedia atau tidak sesuai kebutuhan yang dipilih.")
            if db.execute("SELECT 1 FROM referrals WHERE student_id=? AND service_id=? AND status IN (?,?,?)", [student_id, service_id, *ACTIVE]).fetchone():
                raise ValueError("Rujukan aktif untuk layanan ini sudah ada. Lanjutkan melalui KAWAL.")
            count = db.execute("SELECT COUNT(*) FROM referrals WHERE service_id=? AND status IN (?,?,?)", [service_id, *ACTIVE]).fetchone()[0]
            if count >= service["capacity"]:
                raise ValueError("Kapasitas contoh sedang penuh. Hubungi pendamping melalui jalur non-digital.")
            stamp = now()
            cur = db.execute("INSERT INTO referrals(student_id,service_id,need,status,created,updated) VALUES (?,?,?,?,?,?)",
                             (student_id, service_id, need, "Diajukan", stamp, stamp))
            db.execute("INSERT INTO events(referral_id,actor,action,created) VALUES (?,?,?,?)", (cur.lastrowid, "Mahasiswa", "Rujukan diajukan", stamp))
            return cur.lastrowid

    def referrals(self, student_id=None, role="Mahasiswa"):
        with self.connect() as db:
            if role == "Pendamping":
                rows = db.execute("SELECT r.*,s.payload AS story FROM referrals r JOIN stories s ON r.student_id=s.student_id ORDER BY r.created DESC,r.id DESC").fetchall()
                return [dict(r) for r in rows if json.loads(r["story"])["consent"]]
            if not student_id:
                raise ValueError("ID mahasiswa wajib untuk tampilan mahasiswa.")
            return [dict(r) for r in db.execute("SELECT * FROM referrals WHERE student_id=? ORDER BY created DESC,id DESC", (student_id,))]

    def update_referral(self, referral_id, status, appointment, note, role):
        if role != "Pendamping":
            raise ValueError("Perubahan status hanya untuk pendamping demo.")
        if len(note) > 1000:
            raise ValueError("Catatan terlalu panjang.")
        if status == "Dijadwalkan" and (not appointment or date.fromisoformat(appointment) < datetime.now(ZoneInfo("Asia/Jakarta")).date()):
            raise ValueError("Jadwal wajib diisi dan tidak boleh sebelum hari ini.")
        with self.connect() as db:
            row = db.execute("SELECT * FROM referrals WHERE id=?", (referral_id,)).fetchone()
            if not row or status not in TRANSITIONS[row["status"]]:
                raise ValueError("Perpindahan status tidak diizinkan.")
            consent = json.loads(db.execute("SELECT payload FROM stories WHERE student_id=?", (row["student_id"],)).fetchone()[0])["consent"]
            if not consent:
                raise ValueError("Persetujuan berbagi kebutuhan sudah ditarik.")
            stamp = now()
            db.execute("UPDATE referrals SET status=?,appointment=?,note=?,updated=?,first_response=COALESCE(first_response,?) WHERE id=?",
                       (status, appointment if status == "Dijadwalkan" else row["appointment"], note, stamp, stamp, referral_id))
            db.execute("INSERT INTO events(referral_id,actor,action,created) VALUES (?,?,?,?)", (referral_id, role, status, stamp))

    def cancel(self, referral_id, student_id):
        with self.connect() as db:
            row = db.execute("SELECT status FROM referrals WHERE id=? AND student_id=?", (referral_id, student_id)).fetchone()
            if not row or row["status"] not in ACTIVE:
                raise ValueError("Rujukan tidak dapat dibatalkan.")
            stamp = now()
            db.execute("UPDATE referrals SET status='Dibatalkan',updated=? WHERE id=?", (stamp, referral_id))
            db.execute("INSERT INTO events(referral_id,actor,action,created) VALUES (?,?,?,?)", (referral_id, "Mahasiswa", "Dibatalkan", stamp))

    def feedback(self, referral_id, student_id, rating, text):
        if not 1 <= rating <= 5 or len(text) > 1000:
            raise ValueError("Umpan balik tidak valid.")
        with self.connect() as db:
            row = db.execute("SELECT status FROM referrals WHERE id=? AND student_id=?", (referral_id, student_id)).fetchone()
            if not row or row["status"] != "Selesai":
                raise ValueError("Umpan balik hanya untuk rujukan sendiri yang selesai.")
            db.execute("UPDATE referrals SET rating=?,feedback=? WHERE id=?", (rating, text, referral_id))

    def events(self, referral_id, student_id=None, role="Mahasiswa"):
        allowed = {r["id"] for r in self.referrals(student_id, role)}
        if referral_id not in allowed:
            raise ValueError("Riwayat tidak tersedia untuk pengguna ini.")
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT actor,action,created FROM events WHERE referral_id=? ORDER BY id", (referral_id,))]
