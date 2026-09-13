from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import DatasetRecord, PaperRecord, SourceRecord
from .normalize import canonical_title, content_hash, normalize_accession, normalize_doi, normalize_pmid, utc_now


@dataclass(frozen=True)
class Query:
    text: str
    start: datetime
    end: datetime
    limit: int = 50


class HTTPClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.client = httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "Virelion-Intelligence/0.2 (+https://github.com/Virelion-Biotech/Virelion-Intelligence)"})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    def get(self, url: str, **params: Any) -> httpx.Response:
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response

    def close(self) -> None:
        self.client.close()


class PubMedAdapter:
    source_id = "pubmed"

    def __init__(self, http: HTTPClient | None = None) -> None:
        self.http = http or HTTPClient()

    def search(self, query: Query) -> list[SourceRecord]:
        term = f"({query.text}) AND ({query.start.date().isoformat()}[PDAT] : {query.end.date().isoformat()}[PDAT])"
        search = self.http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", db="pubmed", term=term, retmode="json", retmax=query.limit)
        ids = search.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        fetch = self.http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", db="pubmed", id=",".join(ids), retmode="json")
        result = fetch.json().get("result", {})
        records: list[SourceRecord] = []
        for pmid in ids:
            item = result.get(str(pmid), {})
            if not item:
                continue
            title = item.get("title", "").strip()
            pubdate = _parse_pubdate(item.get("pubdate"))
            authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
            records.append(SourceRecord(
                source_id=f"pubmed:{pmid}", source_type="literature", title=title,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", published_at=pubdate,
                publisher=item.get("fulljournalname"), authors=authors, pmid=str(pmid), authority="primary",
                content_hash=content_hash(title, str(pmid)), tags=["pubmed"],
            ))
        return records


class EuropePMCAdapter:
    source_id = "europe_pmc"

    def __init__(self, http: HTTPClient | None = None) -> None:
        self.http = http or HTTPClient()

    def search(self, query: Query) -> list[SourceRecord]:
        q = f"({query.text}) AND FIRST_PDATE:[{query.start.date().isoformat()} TO {query.end.date().isoformat()}]"
        response = self.http.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", query=q, format="json", pageSize=query.limit)
        results = response.json().get("resultList", {}).get("result", [])
        records: list[SourceRecord] = []
        for item in results:
            pmid = normalize_pmid(item.get("pmid"))
            doi = normalize_doi(item.get("doi"))
            title = (item.get("title") or "").strip()
            source_id = f"europepmc:{pmid or doi or canonical_title(title)}"
            records.append(SourceRecord(
                source_id=source_id, source_type="literature", title=title,
                url=f"https://europepmc.org/article/MED/{pmid}" if pmid else (f"https://doi.org/{doi}" if doi else item.get("id", "https://europepmc.org/")),
                published_at=_parse_pubdate(item.get("firstPublicationDate")), publisher=item.get("journalTitle"),
                authors=[a for a in (item.get("authorString") or "").split(", ") if a], doi=doi, pmid=pmid,
                pmcid=item.get("pmcid"), abstract=item.get("abstractText"), authority="primary",
                content_hash=content_hash(title, doi, pmid), tags=["europepmc"],
            ))
        return records


class GEOAdapter:
    source_id = "geo"

    def __init__(self, http: HTTPClient | None = None) -> None:
        self.http = http or HTTPClient()

    def search(self, query: Query) -> list[DatasetRecord]:
        response = self.http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", db="gds", term=query.text, retmode="json", retmax=query.limit)
        ids = response.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        summary = self.http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", db="gds", id=",".join(ids), retmode="json")
        result = summary.json().get("result", {})
        datasets: list[DatasetRecord] = []
        for uid in ids:
            item = result.get(str(uid), {})
            accession = normalize_accession(item.get("accession")) or f"UID{uid}"
            title = (item.get("title") or "").strip()
            samples = _safe_int(item.get("n_samples"))
            datasets.append(DatasetRecord(
                dataset_id=f"geo:{accession}", source="GEO", accession=accession, title=title,
                url=f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
                sample_count=samples, metadata_quality=0.35, identity_status="UNRESOLVED",
                suitability_status="REVIEW_REQUIRED", metadata_notes=["Study-level discovery only; sample identity requires downstream GSM metadata retrieval."],
            ))
        return datasets


class ClinicalTrialsAdapter:
    source_id = "clinicaltrials"

    def __init__(self, http: HTTPClient | None = None) -> None:
        self.http = http or HTTPClient()

    def search(self, query: Query) -> list[SourceRecord]:
        response = self.http.get("https://clinicaltrials.gov/api/v2/studies", **{"query.term": query.text, "pageSize": query.limit, "format": "json"})
        studies = response.json().get("studies", [])
        records: list[SourceRecord] = []
        for study in studies:
            proto = study.get("protocolSection", {})
            idmods = proto.get("identificationModule", {})
            status = proto.get("statusModule", {})
            nct = idmods.get("nctId")
            if not nct:
                continue
            title = idmods.get("briefTitle") or idmods.get("officialTitle") or nct
            date = _parse_pubdate(status.get("studyFirstPostDateStruct", {}).get("date"))
            records.append(SourceRecord(
                source_id=f"clinicaltrials:{nct}", source_type="clinical", title=title,
                url=f"https://clinicaltrials.gov/study/{nct}", published_at=date,
                publisher="ClinicalTrials.gov", accession=nct, authority="primary",
                content_hash=content_hash(nct, title), tags=["clinical-trial"],
            ))
        return records


class GitHubAdapter:
    source_id = "github"

    def __init__(self, http: HTTPClient | None = None) -> None:
        self.http = http or HTTPClient()

    def search(self, query: Query) -> list[SourceRecord]:
        response = self.http.get("https://api.github.com/search/repositories", q=query.text, per_page=min(query.limit, 100), sort="updated", order="desc")
        records: list[SourceRecord] = []
        for item in response.json().get("items", []):
            full_name = item.get("full_name")
            if not full_name:
                continue
            records.append(SourceRecord(
                source_id=f"github:{full_name}", source_type="software", title=item.get("full_name", ""),
                url=item.get("html_url", ""), published_at=_parse_pubdate(item.get("created_at")),
                publisher="GitHub", authority="secondary", abstract=item.get("description"),
                content_hash=content_hash(full_name, item.get("pushed_at")), tags=["github", "software"],
            ))
        return records


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_pubdate(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=dt.tzinfo or timezone.utc)
        except ValueError:
            continue
    return None
