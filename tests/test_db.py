from pathlib import Path

from virelion_intelligence.db import IntelligenceDB
from virelion_intelligence.models import SourceRecord


def test_database_initializes_and_counts(tmp_path: Path):
    db = IntelligenceDB(tmp_path / "test.sqlite3")
    try:
        assert db.count("runs") == 0
        source = SourceRecord(source_id="S1", source_type="literature", title="Test", url="https://example.org")
        db.upsert_source(source)
        db.commit()
        assert db.count("sources") == 1
    finally:
        db.close()
