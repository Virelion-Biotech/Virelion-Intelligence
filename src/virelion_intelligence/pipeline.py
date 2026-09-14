from __future__ import annotations

import uuid
from datetime import timedelta
from pathlib import Path

from .datasets import assess_dataset
from .db import IntelligenceDB
from .dedupe import dedupe_against
from .evidence import extract_from_source
from .ingest import (
    ClinicalTrialsAdapter,
    EuropePMCAdapter,
    GEOAdapter,
    GitHubAdapter,
    PubMedAdapter,
    Query,
)
from .llm import LLMClient
from .models import PaperRecord, RunManifest, SourceRecord
from .normalize import content_hash, normalize_doi, normalize_pmid, utc_now
from .opportunities import make_opportunity
from .scoring import relevance_score
from .state import DiscoveryState
from .validation import validate_claim_evidence
from .virelion import load_module_config, map_domains

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
        "cardiomyocyte_maturation": ("cardiomyocyte maturation", "maturation", "ipsc-cm", "ipsc cardiomyocyte"),
        "cardiac_engineering": ("tissue engineering", "hydrogel", "biomaterial", "engineered heart", "scaffold", "bioprint"),
        "cardiac_omics": ("single-cell", "single cell", "single-nucleus", "single nucleus", "transcriptomic", "spatial transcriptomic", "proteomic", "multiomic"),
        "computational_cardiology": ("machine learning", "deep learning", "digital twin", "artificial intelligence", "ecg"),
    }
    return [domain for domain, terms in rules.items() if any(term in text for term in terms)]


def score_paper(paper: PaperRecord) -> float:
    text = f"{paper.title} {paper.abstract or ''}".lower()
    values = {
        "cardiovascular": 100 if any(x in text for x in ("cardiac", "heart", "cardiomyocyte", "myocardial")) else 20,
        "scientific": min(100, 55 + 8 * len(paper.domains)),
        "virelion": min(100, 45 + 10 * len(set(paper.domains) & {"cardiac_omics", "cardiac_regeneration", "computational_cardiology", "cardiomyocyte_maturation"})),
        "novelty": 65 if paper.published_at else 45,
        "dataset": 75 if any(x in text for x in ("single-cell", "single nucleus", "dataset", "transcriptom")) else 35,
        "translation": 70 if any(x in text for x in ("clinical", "therapy", "therapeutic", "trial")) else 30,
        "reproducibility": 60 if any(x in text for x in ("code", "github", "benchmark", "dataset")) else 35,
    }
    return relevance_score(values)


def run(window_days: int = 7, db_path: str = "data/virelion_intelligence.sqlite3", query_texts: list[str] | None = None) -> RunManifest:
    end = utc_now()
    start = end - timedelta(days=window_days)
    run_id = f"R-{end.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    manifest = RunManifest(
        run_id=run_id,
        pipeline_version="0.3.0",
        window_start=start,
        window_end=end,
        status="DISCOVERING",
    )
    db = IntelligenceDB(db_path)
    llm = LLMClient.from_env()
    state = DiscoveryState()
    adapters = [
        PubMedAdapter(state=state),
        EuropePMCAdapter(state=state),
        GEOAdapter(state=state),
        ClinicalTrialsAdapter(state=state),
        GitHubAdapter(state=state),
    ]
    try:
        db.upsert_run(manifest)
        queries = query_texts or DEFAULT_QUERIES
        counts = {
            "raw_records": 0,
            "papers": 0,
            "duplicates": 0,
            "datasets": 0,
            "claims": 0,
            "evidence": 0,
            "opportunities": 0,
            "errors": 0,
            "adapter_successes": 0,
            "adapter_failures": 0,
        }
        seen = db.list_papers(limit=5000)
        source_cache: list[SourceRecord] = []
        for text in queries:
            q = Query(text=text, start=start, end=end, limit=50)
            for adapter in adapters:
                try:
                    records = adapter.search(q)
                    counts["adapter_successes"] += 1
                    counts["raw_records"] += len(records)
                    if isinstance(adapter, GEOAdapter):
                        for dataset in records:
                            db.upsert_dataset(assess_dataset(dataset))
                            counts["datasets"] += 1
                        continue
                    for source in records:
                        db.upsert_source(source)
                        source_cache.append(source)
                        if source.source_type not in {"literature", "clinical"}:
                            continue
                        paper = source_to_paper(source, classify_domains(source.title, source.abstract))
                        paper.relevance_score = score_paper(paper)
                        decision = dedupe_against(paper, seen)
                        if decision.duplicate:
                            counts["duplicates"] += 1
                            continue
                        db.upsert_paper(paper)
                        seen.append(paper)
                        counts["papers"] += 1
                except Exception:
                    counts["errors"] += 1
                    counts["adapter_failures"] += 1
        if counts["adapter_successes"] == 0:
            manifest.status = "FAILED"
        elif counts["adapter_successes"] < len(queries) * len(adapters) and counts["raw_records"] == 0:
            manifest.status = "PARTIAL"
        else:
            manifest.status = "COMPLETE"
        if manifest.status == "FAILED":
            counts["errors"] += 1
            manifest.counts = counts
            manifest.finished_at = utc_now()
            db.upsert_run(manifest)
            db.commit()
            return manifest
        modules = load_module_config("config/virelion_modules.yaml")
        top = sorted(
            [p for p in seen if p.relevance_score >= 60],
            key=lambda p: p.relevance_score,
            reverse=True,
        )[:20]
        lookup = {s.source_id: s for s in source_cache}
        for paper in top:
            source = lookup.get(f"pubmed:{paper.pmid}") if paper.pmid else None
            if source is None and paper.doi:
                source = next((s for s in source_cache if normalize_doi(s.doi) == paper.doi), None)
            if source is None:
                source = SourceRecord(
                    source_id=paper.paper_id,
                    source_type="literature",
                    title=paper.title,
                    url=paper.url,
                    abstract=paper.abstract,
                    doi=paper.doi,
                    pmid=paper.pmid,
                    authority="primary",
                )
            try:
                claim, evidence = extract_from_source(source, llm)
                errors = validate_claim_evidence(claim, evidence, source)
                if errors:
                    counts["errors"] += 1
                    continue
                db.upsert_claim(claim)
                db.upsert_evidence(evidence)
                counts["claims"] += 1
                counts["evidence"] += 1
                names = [
                    str(m["module"])
                    for m in map_domains(paper.domains, modules, threshold=0.0)[:5]
                ]
                if names:
                    db.upsert_opportunity(
                        make_opportunity(
                            title=f"Investigate: {paper.title[:120]}",
                            description=f"Assess whether this finding merits reproduction, benchmark construction, curation, or integration into Virelion. Primary record: {paper.url}",
                            opportunity_type="INVESTIGATION",
                            evidence_ids=[evidence.evidence_id],
                            virelion_modules=names,
                            scientific_importance=min(5, 2.5 + 0.5 * len(paper.domains)),
                            evidence_strength=4 if claim.evidence_level.value in {"E2", "E3", "E4", "E5"} else 2,
                            reproducibility=3 if paper.relevance_score >= 80 else 2,
                            data_availability=3 if "cardiac_omics" in paper.domains else 2,
                            computational_feasibility=4 if "computational_cardiology" in paper.domains or "cardiac_omics" in paper.domains else 2.5,
                            virelion_relevance=min(5, 2.5 + 0.5 * len(names)),
                            differentiation=3,
                            translational_potential=3 if "ischemic_heart" in paper.domains else 2,
                        )
                    )
                    counts["opportunities"] += 1
            except Exception:
                counts["errors"] += 1
        manifest.finished_at = utc_now()
        manifest.counts = counts
        db.upsert_run(manifest)
        db.commit()
        Path("data/runs").mkdir(parents=True, exist_ok=True)
        Path(f"data/runs/{run_id}.json").write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return manifest
    finally:
        for adapter in adapters:
            close = getattr(adapter.http, "close", None)
            if close:
                close()
        state.close() if hasattr(state, "close") else None
        db.close()
