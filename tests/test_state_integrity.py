from virelion_intelligence.state import DiscoveryState


def test_buffered_checkpoint_is_not_durable_before_commit(tmp_path):
    path = tmp_path / "checkpoint.json"
    state = DiscoveryState(path, autocommit=False)
    checkpoint = state.snapshot()
    state.set("source", "query", cursor="next")
    assert DiscoveryState(path).get("source", "query") == {}
    state.restore(checkpoint)
    state.commit()
    assert DiscoveryState(path).get("source", "query") == {}
    state.set("source", "query", cursor="durable")
    state.commit()
    assert DiscoveryState(path).get("source", "query")["cursor"] == "durable"


def test_partial_discovery_does_not_advance_failed_adapter(tmp_path, monkeypatch):
    import virelion_intelligence.pipeline as pipeline

    class EmptyAdapter:
        def __init__(self, state):
            self.state = state
            self.http = self
        def search(self, query):
            return []
        def close(self):
            pass

    class FailedAdapter(EmptyAdapter):
        def search(self, query):
            self.state.set("failed", query.state_key, cursor="lost-page")
            raise RuntimeError("response failed after advancing cursor")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pipeline.LLMClient, "from_env", lambda: None)
    monkeypatch.setattr(pipeline, "load_module_config", lambda path: [])
    for name in ("EuropePMCAdapter", "GEOAdapter", "ClinicalTrialsAdapter", "GitHubAdapter"):
        monkeypatch.setattr(pipeline, name, EmptyAdapter)
    monkeypatch.setattr(pipeline, "PubMedAdapter", FailedAdapter)
    result = pipeline.run(db_path=str(tmp_path / "data.sqlite"), query_texts=["fixture"])
    assert result.status == "PARTIAL"
    assert result.counts["adapter_failures"] == 1
    assert DiscoveryState(tmp_path / "data.discovery.json").data == {}
