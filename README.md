# Virelion Intelligence

Evidence-first cardiovascular research intelligence pipeline.

Virelion Intelligence discovers literature, datasets, clinical/translational signals, and research software; normalizes and deduplicates records; ranks relevance; extracts evidence with provenance; evaluates dataset metadata integrity; scores research opportunities; maps findings to Virelion systems; and produces auditable machine-readable and human-readable outputs.

## Design principles

1. Evidence is stored before prose is generated.
2. Deterministic code handles identifiers, dates, state, schemas, deduplication, and validation.
3. LLMs handle semantic classification, evidence extraction, synthesis, and opportunity reasoning.
4. Unsupported claims must fail validation.
5. Ambiguous dataset identity/replicate metadata is never silently inferred.
6. Every run is reproducible through configuration, pipeline version, model version, and source snapshots.

## V0.1 foundation

The initial implementation establishes the canonical data model, configuration system, SQLite persistence layer, deterministic relevance/opportunity scoring, provenance validation, Virelion-module mapping, and CLI orchestration. Source adapters and LLM providers are added behind stable interfaces in subsequent milestones.

## Repository layout

```text
config/       domain, source, scoring, and Virelion configuration
schemas/      JSON schemas for persisted objects
src/          Python package
scripts/      runnable entry points
skill/        research-agent protocol and references
data/        local runtime artifacts (raw/normalized/evidence/runs)
reports/      dated human-readable reports
tests/        unit and integration tests
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
pytest
python -m virelion_intelligence --help
```

## Provenance

Every claim must link to evidence, every evidence record must link to a source, and every source must carry the strongest available identifier and access metadata. The report layer is downstream of these records.

## License

This repository is GPL-3.0-or-later. See `LICENSE`.
