"""
sources/friendshore.py -- adapter for FriendShore (Tier 1-3 supply chain risk).

Transcribed from friendshore/seed_data.py's DEMO_ANALYSES[0] (the fictional
"DefenseTech Solutions" AESA radar supply chain). See README.md's ingestion
design note for why this is a static transcription rather than a live import
(FriendShore pulls in FastAPI/SQLAlchemy/matplotlib just to reach these
module-level constants).
"""
from __future__ import annotations

PROJECT_KEY = "friendshore"
PROJECT_LABEL = "FriendShore -- Supply Chain Risk Mapping"

_NODES = [
    {"name": "DefenseTech Solutions", "country": "USA", "tier": 0, "component": None, "is_focal": True},
    {"name": "Raytheon Components Group", "country": "USA", "tier": 1, "component": "RF/microwave modules"},
    {"name": "BAE Systems Electronics", "country": "UK", "tier": 1, "component": "Antenna arrays"},
    {"name": "Shimadzu Defense", "country": "Japan", "tier": 1, "component": "Signal processors"},
    {"name": "Longhua Microelectronics", "country": "China", "tier": 2, "component": "GaAs wafers"},
    {"name": "Texas Instruments Defense", "country": "USA", "tier": 2, "component": "FPGAs"},
    {"name": "Infineon Technologies", "country": "Germany", "tier": 2, "component": "Power modules"},
    {"name": "Samsung Electro-Mechanics", "country": "South Korea", "tier": 2, "component": "MLCC capacitors"},
    {"name": "Yangtze Memory Technologies", "country": "China", "tier": 2, "component": "NAND flash"},
    {"name": "MP Materials", "country": "USA", "tier": 3, "component": "Rare earth metals"},
    {"name": "CMOC International", "country": "China", "tier": 3, "component": "Cobalt"},
]

_EDGES = [
    ("Raytheon Components Group", "DefenseTech Solutions", "RF/microwave modules"),
    ("BAE Systems Electronics", "DefenseTech Solutions", "Antenna arrays"),
    ("Shimadzu Defense", "DefenseTech Solutions", "Signal processors"),
    ("Longhua Microelectronics", "Raytheon Components Group", "GaAs wafers"),
    ("Texas Instruments Defense", "Raytheon Components Group", "FPGAs"),
    ("Infineon Technologies", "BAE Systems Electronics", "Power modules"),
    ("Samsung Electro-Mechanics", "BAE Systems Electronics", "MLCC capacitors"),
    ("Samsung Electro-Mechanics", "Shimadzu Defense", "MLCC capacitors"),
    ("Yangtze Memory Technologies", "Shimadzu Defense", "NAND flash"),
    ("MP Materials", "Longhua Microelectronics", "Rare earth metals"),
    ("CMOC International", "Longhua Microelectronics", "Cobalt"),
]


def get_entities() -> list[dict]:
    entities = []
    for n in _NODES:
        tier_label = "Tier 0 (focal contractor)" if n.get("is_focal") else f"Tier {n['tier']} supplier"
        component = f", supplies {n['component']}" if n["component"] else ""
        entities.append({
            "name": n["name"],
            "entity_type": "company",
            "source_project": PROJECT_KEY,
            "context": f"{tier_label} -- country: {n['country']}{component} (AESA radar BOM demo)",
            "reference": "DefenseTech Solutions BOM Analysis",
        })
    return entities


def get_relationships() -> list[dict]:
    return [
        {"from": supplier, "to": customer, "rel_type": "supply_chain", "detail": f"Supplies {component}"}
        for supplier, customer, component in _EDGES
    ]
