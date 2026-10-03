from pathlib import Path

import virelion_intelligence.pipeline as pipeline

class BrokenAdapter:
    def __init__(self, *args, **kwargs): self.http=type("H", (), {"close": lambda self: None})()
    def search(self, query): raise RuntimeError("upstream unavailable")

def test_all_sources_unavailable_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "PubMedAdapter", BrokenAdapter)
    monkeypatch.setattr(pipeline, "EuropePMCAdapter", BrokenAdapter)
    monkeypatch.setattr(pipeline, "GEOAdapter", BrokenAdapter)
    monkeypatch.setattr(pipeline, "ClinicalTrialsAdapter", BrokenAdapter)
    monkeypatch.setattr(pipeline, "GitHubAdapter", BrokenAdapter)
    manifest=pipeline.run(window_days=1, db_path=str(Path(tmp_path)/"run.sqlite3"), query_texts=["cardiac"])
    assert manifest.status == "FAILED"
    assert manifest.counts["adapter_successes"] == 0
    assert manifest.counts["adapter_failures"] == 5
