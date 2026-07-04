"""
sources/ghosttrace.py -- adapter for GhostTrace (beneficial ownership tracing).

Transcribed directly from ghosttrace/seed_data.py's SEED_ENTITIES / SEED_LINKS
(the fictional Harborview Capital Partners ownership-chain demo). See
"Ingestion design decision" in README.md for why this is a static transcription
of that project's structured demo output rather than a live import of its
runtime (GhostTrace pulls in FastAPI, SQLAlchemy, and ChromaDB just to import
seed_data.py's module-level constants).
"""
from __future__ import annotations

PROJECT_KEY = "ghosttrace"
PROJECT_LABEL = "GhostTrace -- Beneficial Ownership Tracing"

_ROLE_BY_NAME = {
    "Harborview Capital Partners LP": "Focal entity of the demo ownership trace",
    "Meridian Holdings Ltd": "Owns 64.0% of Harborview Capital Partners LP (DEMO-13D-001)",
    "Pelican Trust Services Ltd": "Wholly owns Meridian Holdings Ltd (DEMO-13D-001)",
    "Calloway Nominee Services Ltd": "Holds Pelican Trust Services Ltd shares as nominee (DEMO-13D-002)",
    "Shenzhen Brightway Industrial Co Ltd": "Owns 11.0% of Harborview Capital Partners LP (DEMO-13G-001)",
    "Atlas Pension Partners LLC": "Owns 9.0% of Harborview Capital Partners LP (DEMO-13G-002)",
}

_ENTITIES = [
    {
        "name": "Harborview Capital Partners LP",
        "entity_type": "fund",
        "jurisdiction": "Delaware, United States",
        "reference": "DEMO-13D-001 / DEMO-10K-001",
    },
    {
        "name": "Meridian Holdings Ltd",
        "entity_type": "company",
        "jurisdiction": "Cayman Islands",
        "reference": "DEMO-13D-001",
    },
    {
        "name": "Pelican Trust Services Ltd",
        "entity_type": "trust",
        "jurisdiction": "British Virgin Islands",
        "reference": "DEMO-13D-001",
    },
    {
        "name": "Calloway Nominee Services Ltd",
        "entity_type": "company",
        "jurisdiction": "Cayman Islands",
        "reference": "DEMO-13D-002",
    },
    {
        "name": "Shenzhen Brightway Industrial Co Ltd",
        "entity_type": "company",
        "jurisdiction": "Shenzhen, China",
        "reference": "DEMO-13G-001",
    },
    {
        "name": "Atlas Pension Partners LLC",
        "entity_type": "fund",
        "jurisdiction": "New York, United States",
        "reference": "DEMO-13G-002",
    },
]

_LINKS = [
    ("Meridian Holdings Ltd", "Harborview Capital Partners LP", "ownership", "64.0% beneficial ownership"),
    ("Pelican Trust Services Ltd", "Meridian Holdings Ltd", "ownership", "100% (wholly owned subsidiary)"),
    ("Calloway Nominee Services Ltd", "Pelican Trust Services Ltd", "nominee_holding", "Shares held of record as nominee"),
    ("Shenzhen Brightway Industrial Co Ltd", "Harborview Capital Partners LP", "ownership", "11.0% beneficial ownership"),
    ("Atlas Pension Partners LLC", "Harborview Capital Partners LP", "ownership", "9.0% beneficial ownership"),
]


def get_entities() -> list[dict]:
    return [
        {
            "name": e["name"],
            "entity_type": e["entity_type"],
            "source_project": PROJECT_KEY,
            "context": _ROLE_BY_NAME[e["name"]] + f" -- jurisdiction: {e['jurisdiction']}",
            "reference": e["reference"],
        }
        for e in _ENTITIES
    ]


def get_relationships() -> list[dict]:
    return [
        {"from": owner, "to": owned, "rel_type": rel_type, "detail": detail}
        for owner, owned, rel_type, detail in _LINKS
    ]
