"""
sources/debt_exposure_monitor.py -- adapter for the Defense Supplier Debt
Exposure Monitor.

Transcribed from debt_exposure_monitor/seed_data.py's DEMO_LENDERS (the
fictional "Meridian Defense Systems, Inc." demo supplier profile; the lenders
themselves -- JPMorgan, Bank of America, Goldman Sachs, Wells Fargo, China
Development Bank, VTB Bank -- are real institutions). See README.md's
ingestion design note for why this is a static transcription rather than a
live import.
"""
from __future__ import annotations

PROJECT_KEY = "debt_exposure_monitor"
PROJECT_LABEL = "Defense Supplier Debt Exposure Monitor"

DEMO_COMPANY = "Meridian Defense Systems, Inc."

_LENDERS = [
    {
        "name": "JPMorgan Chase Bank, N.A.",
        "role": "administrative_agent",
        "detail": "$150,000,000 senior secured revolving credit facility, maturing 2028",
    },
    {
        "name": "Bank of America, N.A.",
        "role": "lender",
        "detail": "$50,000,000 syndicate commitment under the revolving credit facility",
    },
    {
        "name": "Goldman Sachs & Co. LLC",
        "role": "underwriter",
        "detail": "$100,000,000 aggregate principal, 5.75% senior notes due 2031",
    },
    {
        "name": "Wells Fargo Bank, N.A.",
        "role": "lender",
        "detail": "$50,000,000 incremental term loan",
    },
    {
        "name": "China Development Bank",
        "role": "lender",
        "detail": "$75,000,000 term loan funding Southeast Asia manufacturing expansion -- foreign-state-connected lender flag",
    },
    {
        "name": "VTB Bank",
        "role": "trustee",
        "detail": "$40,000,000 note purchase agreement -- sanctioned-institution screening flag",
    },
]


def get_entities() -> list[dict]:
    entities = [
        {
            "name": DEMO_COMPANY,
            "entity_type": "company",
            "source_project": PROJECT_KEY,
            "context": "Demo defense supplier debt profile (fictional demo entity, same convention as GhostTrace's Harborview)",
            "reference": "10-K filed 2025-02-14",
        }
    ]
    for lender in _LENDERS:
        entities.append({
            "name": lender["name"],
            "entity_type": "lender",
            "source_project": PROJECT_KEY,
            "context": f"{lender['role'].replace('_', ' ').title()} -- {lender['detail']}",
            "reference": "SupplierDebtProfile demo (Meridian Defense Systems)",
        })
    return entities


def get_relationships() -> list[dict]:
    return [
        {"from": lender["name"], "to": DEMO_COMPANY, "rel_type": "lending", "detail": lender["detail"]}
        for lender in _LENDERS
    ]
