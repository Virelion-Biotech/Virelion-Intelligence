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


def test_paper_update_and_dataset_ranking_use_existing_schema(tmp_path):
    from virelion_intelligence.models import PaperRecord, DatasetRecord
    db = IntelligenceDB(tmp_path / "db.sqlite")
    try:
        paper = PaperRecord(paper_id="P1", title="Initial", url="https://example.org", relevance_score=10)
        db.upsert_paper(paper)
        paper.title = "Updated"
        paper.relevance_score = 90
        db.upsert_paper(paper)
        assert db.list_papers()[0].title == "Updated"
        for identifier, score in (("low", 10), ("high", 90)):
            db.upsert_dataset(DatasetRecord(dataset_id=identifier, source="GEO", accession="GSE123", title=identifier, suitability_score=score))
        assert [row.dataset_id for row in db.list_datasets()] == ["high", "low"]
    finally:
        db.close()
