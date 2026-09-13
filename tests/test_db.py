from pathlib import Path

from virelion_intelligence.db import Database


def test_database_initializes_and_counts(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    try:
        assert db.count("runs") == 0
    finally:
        db.close()
