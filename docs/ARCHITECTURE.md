# Virelion Intelligence Architecture

## Pipeline contract

```text
source -> raw record -> normalized record -> canonical identity -> deduplicated record
       -> relevance ranking -> deep review -> claim -> evidence -> opportunity
       -> Virelion mapping -> report/API/dashboard
```

## Trust boundaries

Deterministic code is authoritative for identifiers, dates, state transitions, schema validation, database persistence, deduplication, arithmetic scoring, and publication checks.

LLM output is advisory for semantic classification, evidence extraction, synthesis, contradiction analysis, research-gap identification, opportunity generation, and Virelion relevance reasoning. LLM output must satisfy schema and provenance checks before persistence or publication.

## Dataset safety

Dataset acceptance is blocked when sample identity, donor/animal linkage, replicate structure, condition, or anatomical zone is unresolved or ambiguous. A review queue may preserve the candidate without accepting it for downstream analysis.

## Persistence

SQLite is the V0.1 system of record for operational development. Raw source payloads are retained separately from normalized records. A later PostgreSQL/object-storage deployment can replace SQLite without changing the domain models or source-adapter contracts.

## Research loop

Discovery is recall-oriented. Screening is precision-oriented. High-value records enter deep review. Evidence is stored before prose is generated. Reports are materialized from persisted evidence and opportunities rather than directly from search responses.

## Planned stages

1. Foundation and contracts
2. PubMed/Europe PMC/GEO/GitHub/ClinicalTrials adapters
3. Normalization and identifier resolution
4. Exact/fuzzy/semantic deduplication
5. Two-pass relevance ranking
6. Full-text evidence extraction
7. Dataset metadata and identity validation
8. Opportunity scoring
9. Virelion module mapping
10. Report generation and publication
11. Human feedback and active-learning prioritization
12. Semantic retrieval, trend analysis, and relationship graphs
