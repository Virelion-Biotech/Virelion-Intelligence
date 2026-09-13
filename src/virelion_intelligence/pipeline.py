from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .db import IntelligenceDB
from .dedupe import dedupe_against
from .ingest import ClinicalTrialsAdapter, EuropePMCAdapter, GEOAdapter, GitHubAdapter, PubMedAdapter, Query
from .models import PaperRecord, RunManifest, SourceRecord
from .normalize import content_hash, normalize_doi, normalize_pmid, utc_now
from .scoring import relevance_score


DEFAULT_QUERIES = [
    "cardiac regeneration",
    "myocardial infarction AND cardiomyocyte",
    "cardiomyocyte maturation",
    "cardiac tissue engineering",
    "cardiac single-cell transcriptomics",
    "cardiac spatial transcriptomics",
    "cardiac digital twin",
]


def source_to_paper(source: SourceRecord, domains: list[str] | None = None) -> PaperRecord:
    return PaperRecord(
        paper_id=f"P-{uuid.uuid4().hex[:12]}",
        title=source.title,
        abstract=source.abstract,
        url=source.url,
        doi=normalize_doi(source.doi),
        pmid=normalize_pmid(source.pmid),
        pmcid=source.pmcid,
        publisher=source.publisher,
        authors=source.authors,
        published_at=source.published_at,
        domains=domains or [],
        content_hash=source.content_hash or content_hash(source.title, source.doi, source.pmid),
    )


def classify_domains(title: str, abstract: str | None = None) -> list[str]:
    text = f"{title} {abstract or ''}".lower()
    rules = {
        "cardiac_regeneration": ("regeneration", "regenerative", "proliferation", "reprogramming"),
        "ischemic_heart": ("myocardial infarction", "ischemia", "ischemic", "infarct"),
        "cardiomyocyte_maturation": ("cardiomyocyte maturation", "maturation", "iPSC-cM", "ipsc-cm"),
        "cardiac_engineering": ("tissue engineering", "hydrogel", "biomaterial", "engineered heart", "scaffold"),
        "cardiac_omics": ("single-cell", "single cell", "single-nucleus", "transcriptomics", "spatial transcriptomics", "proteomics"),
        "computational_cardiology": ("machine learning", "deep learning", "digital twin", "artificial intelligence", "ecg"),
    }
    return [domain for domain, terms in rules.items() if any(term in text for term in terms)]


def score_paper(paper: PaperRecord) -> float:
    text = f"{paper.title} {paper.abstract or ''}".lower()
    cardiovascular = 100 if any(x in text for x in ("cardiac", "heart", "cardiomyocyte", "myocardial")) else 20
    scientific = min(100, 55 + 8 * len(paper.domains))
    virelion = min(100, 45 + 10 * len(set(paper.domains) & {"cardiac_omics", "cardiac_regeneration", "computational_cardiology", "cardiomyocyte_maturation"}))
    novelty = 60 if paper.published_at else 45
    dataset = 75 if any(x in text for x in ("single-cell", "single nucleus", "dataset", "transcriptomic")) else 35
    translation = 70 if any(x in text for x in ("clinical", "therapy", "therapeutic", "trial")) else 30
    reproducibility = 60 if any(x in text for x in ("code", "github", "benchmark", "dataset")) else 35
    return relevance_score({
        "cardiovascular": cardiovascular,
        "scientific": scientific,
        "virelion": virelion,
        "novelty": novelty,
        "dataset": dataset,
        "translation": translation,
        "reproducibility": reproducibility,
    })


def run(window_days: int = 7, db_path: str = "data/virelion_intelligence.sqlite3", query_texts: list[str] | None = None) -> RunManifest:
    end = utc_now()
    start = end - timedelta(days=window_days)
    run_id = f"R-{end.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    manifest = RunManifest(run_id=run_id, pipeline_version="0.2.0", window_start=start, window_end=end, status="DISCOVERING")

    db = IntelligenceDB(db_path)
    try:
        db.upsert_run(manifest)
        http_adapters = [PubMedAdapter(), EuropePMCAdapter(), GEOAdapter(), ClinicalTrialsAdapter(), GitHubAdapter()]
        queries = query_texts or DEFAULT_QUERIES
        counts = {"raw_records": 0, "papers": 0, "duplicates": 0, "datasets": 0, "errors": 0}
        existing_papers = db.list_papers(limit=5000)
        normalized_seen: list[PaperRecord] = list(existing_papers)

        for text in queries:
            q = Query(text=text, start=start, end=end, limit=50)
            for adapter in http_adapters:
                try:
                    records = adapter.search(q)
                    counts["raw_records"] += len(records)
                    if isinstance(adapter, GEOAdapter):
                        for dataset in records:
                            db.upsert_dataset(dataset)
                            counts["datasets"] += 1
                        continue
                    for source in records:
                        db.upsert_source(source)
                        if source.source_type not in {"literature", "clinical"}:
                            continue
                        paper = source_to_paper(source)
                        paper.domains = classify_domains(paper.title, paper.abstract)
                        paper.relevance_score = score_paper(paper)
                        decision = dedupe_against(paper, normalized_seen)
                        if decision.duplicate:
                            counts["duplicates"] += 1
                            continue
                        db.upsert_paper(paper)
                        normalized_seen.append(paper)
                        counts["papers"] += 1
                except Exception:
                    counts["errors"] += 1
        manifest.status = "COMPLETE"
        manifest.finished_at = utc_now()
        manifest.counts = counts
        db.upsert_run(manifest)
        db.commit()
        Path("data/runs").mkdir(parents=True, exist_ok=True)
        Path(f"data/runs/{run_id}.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        return manifest
    except Exception:
        manifest.status = "FAILED"
        manifest.finished_at = utc_now()
        db.upsert_run(manifest)
        db.commit()
        raise
    finally:
        db.close()
