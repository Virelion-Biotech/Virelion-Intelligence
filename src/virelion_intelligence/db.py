from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import Claim, DatasetRecord, Evidence, Opportunity, PaperRecord, RunManifest, SourceRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  content_hash TEXT,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS papers (
  paper_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  canonical_title TEXT NOT NULL,
  doi TEXT,
  pmid TEXT,
  pmcid TEXT,
  content_hash TEXT,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi) WHERE doi IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_pmid ON papers(pmid) WHERE pmid IS NOT NULL;
CREATE TABLE IF NOT EXISTS claims (
  claim_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  source_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  claim_id TEXT NOT NULL,
  source_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS datasets (
  dataset_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  accession TEXT,
  identity_status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_datasets_accession ON datasets(accession);
CREATE TABLE IF NOT EXISTS opportunities (
  opportunity_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  overall_score REAL NOT NULL,
  recommended_action TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT
);
"""


class IntelligenceDB:
    def __init__(self, path: str | Path = "data/virelion_intelligence.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "IntelligenceDB":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def upsert_source(self, item: SourceRecord) -> None:
        payload = item.model_dump_json()
        now = item.accessed_at.isoformat()
        self.conn.execute(
            """INSERT INTO sources(source_id,payload,content_hash,first_seen,last_seen)
               VALUES(?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET payload=excluded.payload, content_hash=excluded.content_hash, last_seen=excluded.last_seen""",
            (item.source_id, payload, item.content_hash, now, now),
        )

    def upsert_paper(self, item: PaperRecord) -> None:
        payload = item.model_dump_json()
        now = item.last_seen_at.isoformat()
        self.conn.execute(
            """INSERT INTO papers(paper_id,payload,canonical_title,doi,pmid,pmcid,content_hash,first_seen,last_seen)
               VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(paper_id) DO UPDATE SET payload=excluded.payload, last_seen=excluded.last_seen,
                 relevance_score=json_extract(excluded.payload,'$.relevance_score')""",
            (item.paper_id, payload, item.title.strip().lower(), item.doi, item.pmid, item.pmcid,
             item.content_hash, item.first_seen_at.isoformat(), now),
        )

    def upsert_claim(self, item: Claim) -> None:
        self.conn.execute("INSERT OR REPLACE INTO claims VALUES(?,?,?)", (item.claim_id, item.model_dump_json(), item.source_id))

    def upsert_evidence(self, item: Evidence) -> None:
        self.conn.execute("INSERT OR REPLACE INTO evidence VALUES(?,?,?,?)", (item.evidence_id, item.model_dump_json(), item.claim_id, item.source_id))

    def upsert_dataset(self, item: DatasetRecord) -> None:
        self.conn.execute("INSERT OR REPLACE INTO datasets VALUES(?,?,?,?)", (item.dataset_id, item.model_dump_json(), item.accession, item.identity_status))

    def upsert_opportunity(self, item: Opportunity) -> None:
        self.conn.execute("INSERT OR REPLACE INTO opportunities VALUES(?,?,?,?)", (item.opportunity_id, item.model_dump_json(), item.overall_score, item.recommended_action))

    def upsert_run(self, item: RunManifest) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO runs(run_id,payload,status,started_at,finished_at) VALUES(?,?,?,?,?)",
            (item.run_id, item.model_dump_json(), item.status, item.started_at.isoformat(), item.finished_at.isoformat() if item.finished_at else None),
        )

    def commit(self) -> None:
        self.conn.commit()

    def count(self, table: str) -> int:
        if table not in {"sources", "papers", "claims", "evidence", "datasets", "opportunities", "runs"}:
            raise ValueError("unsupported table")
        return int(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def list_papers(self, limit: int = 50) -> list[PaperRecord]:
        rows = self.conn.execute("SELECT payload FROM papers ORDER BY last_seen DESC LIMIT ?", (limit,)).fetchall()
        return [PaperRecord.model_validate_json(r[0]) for r in rows]

    def list_datasets(self, limit: int = 50) -> list[DatasetRecord]:
        rows = self.conn.execute("SELECT payload FROM datasets ORDER BY suitability_score DESC LIMIT ?", (limit,)).fetchall()
        return [DatasetRecord.model_validate_json(r[0]) for r in rows]

    def list_opportunities(self, limit: int = 50) -> list[Opportunity]:
        rows = self.conn.execute("SELECT payload FROM opportunities ORDER BY overall_score DESC LIMIT ?", (limit,)).fetchall()
        return [Opportunity.model_validate_json(r[0]) for r in rows]
