---
name: virelion-intelligence
description: Evidence-first research workflow for discovering, verifying, ranking, and synthesizing cardiovascular literature, datasets, software, and translational signals for Virelion.
---

# Virelion Intelligence research protocol

## Non-negotiable rules

1. Search results are leads, not evidence.
2. Do not state an external fact until its source has been fetched.
3. Never invent DOI, PMID, accession, NCT, version, date, number, or URL.
4. Distinguish source fact, author interpretation, Virelion inference, and hypothesis.
5. Every substantive claim must have a traceable source and evidence record.
6. Do not silently infer donor, animal, replicate, condition, or anatomical-zone identity in ambiguous datasets.
7. Preserve raw source material and normalized records separately.
8. Prefer primary sources and authoritative registries over secondary summaries.

## Pipeline

### Phase 0 — Define the window

Record UTC start/end timestamps. Record pipeline version, configuration revision, and model identifiers.

### Phase 1 — Discover

Sweep configured literature, dataset, software, and translational sources. Bias toward recall during discovery.

### Phase 2 — Normalize

Canonicalize identifiers, dates, titles, authors, source types, and source authority. Preserve raw payloads.

### Phase 3 — Deduplicate

Use exact DOI/PMID/accession matching, normalized-title matching, then optional semantic similarity. Do not merge follow-up, replication, extension, or contradiction records as duplicates.

### Phase 4 — Rank

Score cardiovascular relevance, scientific relevance, Virelion relevance, novelty, dataset value, translation, and reproducibility. Store component scores, not only a final score.

### Phase 5 — Deep review

Read the strongest available source: structured full text when available, then accessible HTML/PDF, then abstract. Record evidence depth explicitly.

### Phase 6 — Extract evidence

Capture the claim, supporting passage, section/figure when available, model, intervention, comparator, outcome, sample/design details, limitations, evidence level, and extraction confidence.

### Phase 7 — Dataset integrity

Validate sample-level identity, condition, replicate structure, tissue/zone, and study design. Ambiguous fields become REVIEW_REQUIRED or UNRESOLVED rather than guessed.

### Phase 8 — Opportunity analysis

Identify reproducibility opportunities, dataset gaps, benchmark opportunities, model/evaluation opportunities, mechanistic gaps, and translational signals. Every proposed opportunity must point back to evidence.

### Phase 9 — Virelion mapping

Map findings to CardiAtlas, CardiBench, CardiEval, ElectroTrace, MyoTrace, OptiCell, CardiLearn, CardiSim, CardiTrace, CardiBridge, and HeartTwin. Give each mapping a rationale and score.

### Phase 10 — Report

Generate human-readable reports from persisted records. Never make the report the source of truth.

### Phase 11 — Validate

Run schema validation, provenance checks, identifier checks, dataset-integrity checks, placeholder checks, and security checks before publication.

## Output hierarchy

```text
raw source
  -> normalized source
  -> claim
  -> evidence
  -> finding
  -> opportunity
  -> Virelion mapping
  -> report
```

The report must be reproducible from the records above it.
