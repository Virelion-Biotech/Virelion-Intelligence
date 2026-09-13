# Virelion Intelligence

Evidence-first cardiovascular research intelligence pipeline.

Virelion Intelligence discovers literature, datasets, clinical/translational signals and research software; normalizes and deduplicates records; ranks relevance; extracts evidence with provenance; evaluates dataset metadata integrity; scores research opportunities; maps findings to Virelion systems; and generates auditable reports and structured run artifacts.

## Architecture

```text
sources -> normalization -> identifier resolution -> deduplication
        -> relevance ranking -> evidence extraction
        -> dataset integrity -> opportunity scoring
        -> Virelion mapping -> SQLite corpus -> reports
```

Deterministic Python code owns identifiers, dates, persistence, validation and scoring. The optional LLM backend is used for semantic extraction and synthesis and is never required for basic discovery.

## V0.2 capabilities

- PubMed discovery via NCBI E-utilities
- Europe PMC discovery
- GEO study discovery
- ClinicalTrials.gov discovery
- GitHub repository discovery
- canonical source and paper models
- DOI/PMID normalization and duplicate detection
- transparent relevance and opportunity scoring
- evidence and claim objects with provenance links
- dataset identity and metadata-integrity gates
- configurable Virelion module mapping
- SQLite persistent corpus and run manifests
- Markdown report generation
- optional OpenAI-compatible LLM provider
- local dry-run path without an LLM
- pytest regression suite
- GitHub Actions tests and scheduled discovery

## Local installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Optional LLM configuration:

```bash
cp .env.example .env
export VIRELION_LLM_API_KEY="..."
export VIRELION_LLM_BASE_URL="https://api.openai.com/v1"
export VIRELION_LLM_MODEL="gpt-5"
```

Without an LLM key, the system uses a deterministic evidence fallback so discovery, storage, scoring and report generation remain testable.

## Run

```bash
virelion-intel version
virelion-intel status
virelion-intel run --window-days 7
virelion-intel report --output reports/latest/intelligence.md
```

Or use the operator script:

```bash
bash scripts/run_intelligence.sh
```

Custom query:

```bash
virelion-intel run --window-days 14 --query "human myocardial infarction single nucleus transcriptomics"
```

## Data safety

Dataset records with unresolved donor/animal identity, replicate structure, or condition metadata are retained as review items and are not automatically accepted as ingestion targets. The pipeline does not infer missing study identity from weak context.

Claims should not be published until they have a source-backed evidence record. Evidence level and extraction confidence are stored separately.

## Runtime artifacts

Local runtime state is intentionally ignored by Git:

```text
data/virelion_intelligence.sqlite3
data/raw/
data/runs/
logs/
.env
```

GitHub Actions uploads report/run artifacts through the workflow artifact store instead of committing mutable runtime databases.

## Research protocol

The agent protocol lives in `skill/SKILL.md`. It defines source-first verification, evidence boundaries, metadata safety, opportunity generation and Virelion mapping.

## Development checks

```bash
pytest
python scripts/check_integrity.py
```

## License

GPL-3.0-or-later. See `LICENSE`.
