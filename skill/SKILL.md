---
name: virelion-intelligence
description: Discover, verify, rank, and synthesize cardiovascular literature, datasets, translational signals, and software into provenance-backed Virelion research intelligence.
---

# Virelion Intelligence Agent Protocol

## Non-negotiable rules

1. Never write a scientific fact from model memory. Use retrieved source evidence.
2. Search results are leads, not evidence. Open the underlying source before citing a claim.
3. Never invent DOI, PMID, accession, NCT ID, figure number, sample count, date, or benchmark value.
4. Distinguish source fact, author interpretation, Virelion inference, and Virelion hypothesis.
5. Ambiguous dataset identity, donor/animal mapping, replicate mapping, condition labels, or anatomical-zone labels must remain unresolved rather than guessed.
6. Evidence strength and extraction confidence are separate fields.
7. Every published claim must resolve to an evidence record and source record.
8. Prefer primary literature, official datasets, trial registries, repository metadata, and original software releases.
9. Do not silently convert preprints or secondary reporting into established findings.
10. A failure to verify is preferable to a fabricated answer.

## Pipeline

### Phase 0 — Window

Record the exact start and end timestamps. For a weekly run, cover the preceding seven days. Read the previous run's selected sources to avoid recycled reporting unless a genuine update exists.

### Phase 1 — Discovery

Sweep cardiovascular regeneration, ischemic heart disease, cardiomyocyte maturation, regenerative engineering, cardiac omics, computational cardiology, datasets, clinical translation, and relevant software/models.

### Phase 2 — Normalize

Canonicalize title, identifiers, dates, URLs, authors and source type. Preserve raw payloads.

### Phase 3 — Deduplicate

Use exact DOI/PMID/accession matching first, normalized-title similarity second, semantic matching only as a candidate relationship. Never merge merely related studies.

### Phase 4 — Rank

Use transparent deterministic relevance scores before expensive deep reading. Store every component score.

### Phase 5 — Evidence extraction

For high-value records extract finding, experimental model, intervention, comparator, endpoint, effect, limitations, evidence depth, and supporting text/location.

### Phase 6 — Dataset analysis

Identify species, tissue, cell type, condition, control, assay, sample count, replicate structure, dataset accession and metadata quality. Any unresolved identity issue produces REVIEW_REQUIRED rather than acceptance.

### Phase 7 — Opportunity generation

Generate only evidence-linked opportunities. Each opportunity must state its underlying finding, limitation, available evidence/data, proposed Virelion action, expected deliverable, and score.

### Phase 8 — Virelion mapping

Map findings to CardiAtlas, CardiBench, CardiEval, ElectroTrace, MyoTrace, OptiCell, CardiLearn, CardiSim, CardiTrace, CardiBridge, and HeartTwin using configuration-backed domain overlap. Do not invent mappings outside the configured module ontology.

### Phase 9 — Reporting

Generate human-readable reports only from persisted structured records. Preserve source IDs and evidence IDs in the report context.

### Phase 10 — Validation

Before publication verify schema, provenance, identifiers, dataset status, placeholders, artifact existence, and secret exposure.
