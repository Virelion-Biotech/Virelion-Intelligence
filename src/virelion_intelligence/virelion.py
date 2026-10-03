from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml


def load_module_config(path: str | Path) -> dict[str, dict[str, list[str]]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    modules = data.get("modules", {})
    if not isinstance(modules, dict):
        raise ValueError("virelion module config must contain a mapping under 'modules'")
    return modules


def map_domains(domains: Iterable[str], modules: dict[str, dict[str, list[str]]], threshold: float = 0.0) -> list[dict[str, object]]:
    requested = {d.strip().lower() for d in domains if d and d.strip()}
    if not requested:
        return []

    results: list[dict[str, object]] = []
    for name, cfg in modules.items():
        module_domains = {str(d).lower() for d in cfg.get("domains", [])}
        overlap = requested & module_domains
        score = len(overlap) / max(1, len(requested))
        if score > threshold:
            results.append({
                "module": name,
                "score": round(score, 3),
                "matched_domains": sorted(overlap),
            })
    return sorted(results, key=lambda x: (-float(x["score"]), str(x["module"])))
