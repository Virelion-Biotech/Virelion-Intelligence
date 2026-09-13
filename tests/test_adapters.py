import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from virelion_intelligence.ingest import ClinicalTrialsAdapter, EuropePMCAdapter, GEOAdapter, GitHubAdapter, PubMedAdapter, Query
from virelion_intelligence.state import DiscoveryState

FIXTURE=json.loads((Path(__file__).parent/"fixtures"/"adapters.json").read_text())
START=datetime(2026,9,1,tzinfo=timezone.utc); END=datetime(2026,9,14,tzinfo=timezone.utc)
class FakeHTTP:
    def __init__(self,responses):self.responses=list(responses);self.calls=[]
    def get(self,url,**params):
        self.calls.append((url,params)); response=self.responses.pop(0)
        if isinstance(response,Exception):raise response
        return httpx.Response(200,json=response,request=httpx.Request("GET",url))
    def close(self):pass

def q(text="cardiac",limit=50):return Query(text=text,start=START,end=END,limit=limit)
def test_pubmed_window_filter():
    out=PubMedAdapter(http=FakeHTTP([FIXTURE["pubmed_search"],FIXTURE["pubmed_summary"]])).search(q(limit=2)); assert [x.pmid for x in out]==["101"]
def test_europe_pmc_window_filter():
    out=EuropePMCAdapter(http=FakeHTTP([FIXTURE["europe_pmc"]])).search(q(limit=2)); assert [x.pmid for x in out]==["101"]
def test_clinical_trials_window_filter():
    out=ClinicalTrialsAdapter(http=FakeHTTP([FIXTURE["clinicaltrials"]])).search(q(limit=2)); assert [x.accession for x in out]==["NCT000001"]
def test_github_pushed_window_filter():
    out=GitHubAdapter(http=FakeHTTP([FIXTURE["github"],{"items":[]}])).search(q(limit=2)); assert [x.source_id for x in out]==["github:Virelion-Biotech/example"]
def test_state_is_window_specific(tmp_path):
    state=DiscoveryState(tmp_path/"state.json"); state.set("pubmed",Query("cardiac",START,END).state_key,retstart=50); other=Query("cardiac",datetime(2026,9,8,tzinfo=timezone.utc),END).state_key; assert state.get("pubmed",other)=={}
def test_retry_after_rate_limit_error(monkeypatch):
    import virelion_intelligence.ingest as ingest
    sleeps=[]; monkeypatch.setattr(ingest.time,"sleep",lambda value:sleeps.append(value))
    class Client:
        def __init__(self):self.n=0
        def get(self,url,*a,**k):
            self.n+=1; request=httpx.Request("GET",url)
            if self.n<2:return httpx.Response(429,headers={"Retry-After":"3"},request=request)
            return httpx.Response(200,json={"ok":True},request=request)
        def close(self):pass
    http=ingest.HTTPClient(); http.client=Client(); assert http.get("https://example.org").json()["ok"] is True; assert sleeps and sleeps[0]==3; http.close()
@pytest.mark.parametrize("adapter",[PubMedAdapter,EuropePMCAdapter,GEOAdapter,ClinicalTrialsAdapter,GitHubAdapter])
def test_adapters_expose_close(adapter):assert callable(adapter(http=FakeHTTP([])).http.close)
