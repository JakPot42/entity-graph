"""
sources/acquisition_brief.py -- adapter for the Pre-Acquisition Intelligence
Brief Generator.

Transcribed from acquisition_brief/seed_data.py's DEMO_CASES (Parsons
Corporation, NYSE: PSN, the demo M&A due-diligence subject) and its related
litigation. See README.md's ingestion design note for why this is a static
transcription rather than a live import.
"""
from __future__ import annotations

PROJECT_KEY = "acquisition_brief"
PROJECT_LABEL = "Pre-Acquisition Intelligence Brief -- Parsons Corporation"

_ENTITIES = [
    {
        "name": "Parsons Corporation",
        "entity_type": "company",
        "context": "Demo acquisition-brief subject (NYSE: PSN, mid-size defense IT/cyber contractor)",
        "reference": "Pre-Acquisition Intelligence Brief demo",
    },
    {
        "name": "Parsons Federal Services Inc.",
        "entity_type": "company",
        "context": "Litigation defendant -- Axiom Technical Services LLC v. Parsons Federal Services Inc. (contract dispute, active)",
        "reference": "cl-10297461",
    },
    {
        "name": "Parsons Government Services Inc.",
        "entity_type": "company",
        "context": "Litigation plaintiff -- Parsons Government Services Inc. v. Centinel Defense Systems LLC (patent infringement, settled 2021)",
        "reference": "cl-6891047",
    },
    {
        "name": "Axiom Technical Services LLC",
        "entity_type": "company",
        "context": "Subcontractor litigation plaintiff -- $14.2M cybersecurity engineering task-order dispute (active)",
        "reference": "cl-10297461",
    },
    {
        "name": "Centinel Defense Systems LLC",
        "entity_type": "company",
        "context": "Patent-infringement counterparty -- cross-licensed and settled June 2021",
        "reference": "cl-6891047",
    },
]

_RELATIONSHIPS = [
    ("Parsons Federal Services Inc.", "Parsons Corporation", "corporate_family", "Parsons operating subsidiary"),
    ("Parsons Government Services Inc.", "Parsons Corporation", "corporate_family", "Parsons operating subsidiary"),
    ("Axiom Technical Services LLC", "Parsons Federal Services Inc.", "litigation_counterparty", "Breach of contract claim, $14.2M task order"),
    ("Parsons Government Services Inc.", "Centinel Defense Systems LLC", "litigation_counterparty", "Patent infringement, US 10,637,881"),
]


def get_entities() -> list[dict]:
    return [{**e, "source_project": PROJECT_KEY} for e in _ENTITIES]


def get_relationships() -> list[dict]:
    return [
        {"from": frm, "to": to, "rel_type": rel_type, "detail": detail}
        for frm, to, rel_type, detail in _RELATIONSHIPS
    ]
