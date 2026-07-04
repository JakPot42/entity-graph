"""
sources/tech_scanner.py -- adapter for the Emerging Tech Horizon Scanner.

Transcribed from tech_scanner/seed_data.py's DEMO_SEEDS (arXiv preprints,
USPTO patents, and DARPA solicitations, each already carrying a resolved
`canonical_institutions` list -- tech-scanner is itself the SECOND deployment
of entity_resolver.py, so its seed data already ran institution resolution
once). One raw entity is emitted per (item, institution) pair rather than
deduped here -- this project's own entity_resolver.resolve_entities() collapses
repeats into a single canonical entity's `mentions` list, so an institution
referenced across several scanner items shows every occurrence on query.
See README.md's ingestion design note for why this is a static transcription
rather than a live import.
"""
from __future__ import annotations

PROJECT_KEY = "tech_scanner"
PROJECT_LABEL = "Emerging Tech Horizon Scanner"

# (canonical_institutions, tech_domain, trend_label, dual_use_tier, external_id, url)
_ITEMS = [
    (["Massachusetts Institute of Technology", "Stanford University"],
     "Quantum Computing & Sensing", "Microwave-optical quantum transduction for distributed sensing",
     "HIGH", "2501.09871", "https://arxiv.org/abs/2501.09871"),
    (["Georgia Institute of Technology", "DARPA"],
     "AI/ML for Defense Applications", "Certified adversarial robustness for autonomous target acquisition",
     "CRITICAL", "2502.03412", "https://arxiv.org/abs/2502.03412"),
    (["California Institute of Technology", "NASA"],
     "Hypersonics & Advanced Propulsion", "High-fidelity boundary layer transition modeling for boost-glide vehicles",
     "HIGH", "2502.11045", "https://arxiv.org/abs/2502.11045"),
    (["Raytheon Technologies"],
     "Microelectronics & Semiconductors", "High-power GaN MMIC for AESA fire-control radar",
     "HIGH", "2503.00287", "https://arxiv.org/abs/2503.00287"),
    (["Massachusetts Institute of Technology", "Air Force Research Laboratory"],
     "Cyber & Electronic Warfare", "RL-driven cognitive jamming against agile radar at embedded latency",
     "CRITICAL", "2503.08864", "https://arxiv.org/abs/2503.08864"),
    (["Northrop Grumman"],
     "Autonomous Systems & Robotics", "GPS-denied swarm coordination for contested-environment UAV missions",
     "CRITICAL", "11928743", "https://patents.google.com/patent/US11928743"),
    (["Lockheed Martin"],
     "Directed Energy Weapons", "Megawatt-class HEL with adaptive optics for maritime counter-UAS",
     "CRITICAL", "11892311", "https://patents.google.com/patent/US11892311"),
    (["Massachusetts Institute of Technology", "DARPA"],
     "Quantum Computing & Sensing", "Quantum illumination radar with 6 dB SNR advantage over stealth targets",
     "HIGH", "11874052", "https://patents.google.com/patent/US11874052"),
    (["Aerojet Rocketdyne"],
     "Hypersonics & Advanced Propulsion", "Combined-cycle scramjet enabling Mach 5-12 sustained cruise for missiles",
     "CRITICAL", "11863987", "https://patents.google.com/patent/US11863987"),
    (["Johns Hopkins University", "DARPA"],
     "Microelectronics & Semiconductors", "Low-SWaP neuromorphic ELINT classification at 40 Gbps",
     "HIGH", "11849201", "https://patents.google.com/patent/US11849201"),
    (["DARPA"],
     "AI/ML for Defense Applications", "AI-enabled multi-domain command and control at machine speed",
     "CRITICAL", "BAA-DARPA-I2O-26-001", "https://sam.gov/opp/BAA-DARPA-I2O-26-001"),
    (["DARPA"],
     "Advanced Materials & Manufacturing", "Ultra-high-temp ceramics for Mach 10+ reentry survivability",
     "HIGH", "BAA-DARPA-DSO-26-002", "https://sam.gov/opp/BAA-DARPA-DSO-26-002"),
    (["DARPA"],
     "Quantum Computing & Sensing", "Quantum networking for tamper-evident tactical military communications",
     "HIGH", "BAA-DARPA-I2O-26-003", "https://sam.gov/opp/BAA-DARPA-I2O-26-003"),
]


def get_entities() -> list[dict]:
    entities = []
    for institutions, tech_domain, trend_label, dual_use_tier, external_id, url in _ITEMS:
        for institution in institutions:
            entities.append({
                "name": institution,
                "entity_type": "institution",
                "source_project": PROJECT_KEY,
                "context": f"{tech_domain} -- {trend_label} (dual-use tier: {dual_use_tier})",
                "reference": external_id,
                "url": url,
            })
    return entities


def get_relationships() -> list[dict]:
    return []
