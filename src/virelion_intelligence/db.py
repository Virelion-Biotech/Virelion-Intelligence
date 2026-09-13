from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    pipeline_version TEXT NOT NULL,
    started_at TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    status TEXT NOT NULL,
    counts_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    doi TEXT,
    pmid TEXT,
    accession TEXT,
    published_at TEXT,
    accessed_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    text TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    evidence_level TEXT NOT NULL,
    extraction_confidence REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    supporting_text TEXT NOT NULL,
    evidence_level TEXT NOT NULL,
    evidence_depth TEXT NOT NULL,
    confidence REAL NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    accession TEXT NOT NULL,
    identity_status TEXT NOT NULL,
    suitability_score REAL NOT NULL,
    suitability_status TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS opportunities (
    opportunity_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    opportunity_type TEXT NOT NULL,
    overall_score REAL NOT NULL,
    recommended_action TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def upsert_json(self, table: str, key: str, record_id: str, payload: dict[str, Any], columns: dict[str, Any]) -> None:
        keys = [key, *columns.keys(), "payload_json"]
        values = [record_id, *columns.values(), json.dumps(payload, sort_keys=True)]
        placeholders = ",".join("?" for _ in values)
        updates = ",".join(f"{name}=excluded.{name}" for name in [*columns.keys(), "payload_json"])
        sql = f"INSERT INTO {table} ({','.join(keys)}) VALUES ({placeholders}) ON CONFLICT({key}) DO UPDATE SET {updates}"
        self.conn.execute(sql, values)
        self.conn.commit()

    def count(self, table: str) -> int:
        row = self.conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        return int(row["n"])
