"""
sources/litigation_network.py -- adapter for Litigation Network (securities
class actions).

Transcribed from litigation_network/seed_data.py's _DEMO_CASES -- 12 real
securities class action cases drawn from public court records. See
README.md's ingestion design note for why this is a static transcription
rather than a live import (Litigation Network pulls in FastAPI/SQLAlchemy
just to reach these module-level constants).
"""
from __future__ import annotations

PROJECT_KEY = "litigation_network"
PROJECT_LABEL = "Litigation Network -- Securities Class Action Database"

_CASES = [
    {
        "case_name": "In re Tesla, Inc. Securities Litigation",
        "defendant_company": "Tesla, Inc.",
        "status": "dismissed (jury verdict for defendants, Jan 2023)",
        "settlement_amount_usd": None,
        "date_filed": "2018-08-10",
    },
    {
        "case_name": "In re Facebook, Inc. Securities Litigation",
        "defendant_company": "Meta Platforms, Inc.",
        "status": "settled",
        "settlement_amount_usd": 100_000_000.0,
        "date_filed": "2018-03-20",
    },
    {
        "case_name": "In re Boeing Co. Securities Litigation",
        "defendant_company": "Boeing Company",
        "status": "settled",
        "settlement_amount_usd": 234_500_000.0,
        "date_filed": "2019-12-11",
    },
    {
        "case_name": "In re Luckin Coffee Inc. Securities Litigation",
        "defendant_company": "Luckin Coffee Inc.",
        "status": "settled",
        "settlement_amount_usd": 175_000_000.0,
        "date_filed": "2020-02-13",
    },
    {
        "case_name": "In re Snap Inc. Securities Litigation",
        "defendant_company": "Snap Inc.",
        "status": "settled",
        "settlement_amount_usd": 187_500_000.0,
        "date_filed": "2017-05-12",
    },
    {
        "case_name": "City of Providence v. Uber Technologies, Inc.",
        "defendant_company": "Uber Technologies, Inc.",
        "status": "settled",
        "settlement_amount_usd": 200_000_000.0,
        "date_filed": "2019-10-07",
    },
    {
        "case_name": "In re Zynga Inc. Securities Litigation",
        "defendant_company": "Zynga Inc.",
        "status": "settled",
        "settlement_amount_usd": 23_400_000.0,
        "date_filed": "2012-08-02",
    },
    {
        "case_name": "In re Lumber Liquidators Holdings Securities Litigation",
        "defendant_company": "Lumber Liquidators Holdings",
        "status": "settled",
        "settlement_amount_usd": 36_000_000.0,
        "date_filed": "2016-01-05",
    },
    {
        "case_name": "In re Valeant Pharmaceuticals International Securities Litigation",
        "defendant_company": "Valeant Pharmaceuticals International",
        "status": "settled",
        "settlement_amount_usd": 1_210_000_000.0,
        "date_filed": "2015-10-22",
    },
    {
        "case_name": "In re Kraft Heinz Securities Litigation",
        "defendant_company": "Kraft Heinz Company",
        "status": "settled",
        "settlement_amount_usd": 62_000_000.0,
        "date_filed": "2019-02-25",
    },
    {
        "case_name": "In re General Electric Company Securities Litigation",
        "defendant_company": "General Electric Company",
        "status": "settled",
        "settlement_amount_usd": 200_000_000.0,
        "date_filed": "2019-01-31",
    },
    {
        "case_name": "Sjunde AP-Fonden v. Goldman Sachs Group, Inc.",
        "defendant_company": "Goldman Sachs Group, Inc.",
        "status": "settled",
        "settlement_amount_usd": 215_000_000.0,
        "date_filed": "2018-12-20",
    },
]


def _context(case: dict) -> str:
    if case["settlement_amount_usd"]:
        money = f"${case['settlement_amount_usd'] / 1_000_000:.1f}M settlement"
    else:
        money = "no settlement"
    return f"Securities class action defendant -- {case['status']}, {money} (filed {case['date_filed']})"


def get_entities() -> list[dict]:
    return [
        {
            "name": case["defendant_company"],
            "entity_type": "company",
            "source_project": PROJECT_KEY,
            "context": _context(case),
            "reference": case["case_name"],
        }
        for case in _CASES
    ]


def get_relationships() -> list[dict]:
    return []
