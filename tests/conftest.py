import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pijar.store import Store
from pijar.data import load_data


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "test.sqlite3")


@pytest.fixture(scope="session")
def data():
    return load_data()


@pytest.fixture
def payload():
    return dict(ekonomi="Rendah", bekerja=True, beasiswa=True, dukungan=3,
                ukt=2, kendala="Finansial", kebutuhan=["Biaya kuliah"], catatan="Contoh fiktif", consent=True)
