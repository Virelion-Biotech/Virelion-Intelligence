from __future__ import annotations

from datetime import datetime, timezone

from .db import IntelligenceDB


def build_markdown_report(db: IntelligenceDB) -> str:
    papers = db.list_papers(20)
    datasets = db.list_datasets(20)
    opportunities = db.list_opportunities(10)
    now = datetime.now(timezone.utc)
    lines = [
        "# Virelion Cardiovascular Intelligence",
        "",
        f"Generated: {now.isoformat()}",
        "",
        "## Executive signal",
        "",
        f"The current corpus contains **{db.count('papers')} papers**, **{db.count('datasets')} datasets**, and **{db.count('opportunities')} opportunities**.",
        "",
        "## Highest-ranked research signals",
        "",
    ]
    for i, paper in enumerate(papers[:10], 1):
        domains = ", ".join(paper.domains) or "unclassified"
        lines.extend([
            f"### {i}. {paper.title}",
            f"- Relevance: **{paper.relevance_score:.1f}/100**",
            f"- Domains: {domains}",
            f"- Source: {paper.url}",
            "",
        ])
    lines.extend(["## Dataset watchlist", ""])
    for dataset in datasets[:10]:
        lines.extend([
            f"- **{dataset.accession}** — {dataset.title or 'Untitled dataset'} — status: `{dataset.suitability_status}`, identity: `{dataset.identity_status}`",
        ])
    lines.extend(["", "## Virelion opportunities", ""])
    if opportunities:
        for opportunity in opportunities:
            modules = ", ".join(opportunity.virelion_modules) or "unmapped"
            lines.extend([
                f"### {opportunity.title}",
                f"- Score: **{opportunity.overall_score:.2f}/10**",
                f"- Action: `{opportunity.recommended_action}`",
                f"- Type: `{opportunity.opportunity_type}`",
                f"- Virelion modules: {modules}",
                f"- {opportunity.description}",
                "",
            ])
    else:
        lines.append("No scored opportunities are stored yet.")
        lines.append("")
    lines.extend([
        "## Evidence policy",
        "",
        "This report is generated from persisted records. Claims should be tied to source-backed evidence before publication. Dataset records marked `UNRESOLVED` or `REVIEW_REQUIRED` are not considered validated ingestion targets.",
        "",
    ])
    return "\n".join(lines)
