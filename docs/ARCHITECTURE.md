# Virelion Intelligence Architecture

## Pipeline contract

```text
source -> raw record -> normalized record -> canonical identity -> deduplicated record
       -> relevance ranking -> deep review -> claim -> evidence -> opportunity
       -> Virelion mapping -> persistent corpus -> report/API/dashboard
```

## V0.2 implementation status

Implemented: PubMed, Europe PMC, GEO study discovery, ClinicalTrials.gov, GitHub repository discovery; canonical Pydantic models; SQLite persistence; DOI/PMID/text normalization; exact/fuzzy deduplication; deterministic relevance and opportunity scoring; evidence/claim records; dataset metadata integrity rules; Virelion module mapping; Markdown reporting; CLI; local runner; CI and scheduled GitHub Actions workflow.

Next expansion: full-text acquisition, semantic retrieval, citation graph relationships, cross-study contradiction analysis, richer sample-level GEO metadata, human feedback calibration, and dashboard/API layers.

## Trust boundaries

Deterministic code is authoritative for identifiers, dates, state transitions, schema validation, database persistence, deduplication, arithmetic scoring, and publication checks.

LLM output is advisory for semantic classification, evidence extraction, synthesis, contradiction analysis, research-gap identification, opportunity generation, and Virelion relevance reasoning. LLM output must satisfy schema and provenance checks before publication.

## Dataset safety

Dataset acceptance is blocked when sample identity, donor/animal linkage, replicate structure, condition, or anatomical zone is unresolved or ambiguous. Candidates remain visible as review items rather than being silently inferred.

## Persistence

SQLite is the V0.2 operational system of record. Raw external payloads and run manifests are local runtime artifacts and are excluded from Git. The domain model and adapter interfaces are designed so persistence can move to PostgreSQL/object storage later.

## Research loop

Discovery is recall-oriented. Screening/ranking is precision-oriented. High-value records enter deeper evidence processing. Evidence is persisted before prose is generated. Reports are materialized from structured records rather than directly from search responses.
