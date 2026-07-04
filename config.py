"""config.py -- all tunable constants for the Unified Entity Graph. No logic."""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Fuzzy resolution thresholds (same three-band design as every prior
# entity_resolver.py deployment: GhostTrace -> tech-scanner -> PatientFusion)
# ---------------------------------------------------------------------------
FUZZY_AUTO_MERGE_THRESHOLD = 90.0
FUZZY_ADJUDICATE_THRESHOLD = 75.0

# CLI query only: below this, a "best match" is noise, not a real hit -- a
# nonsense query still scores >0 against every candidate (SequenceMatcher
# finds some overlapping characters even between unrelated strings), so
# find_entity() needs its own floor separate from the merge/adjudicate bands.
MIN_QUERY_SCORE = 40.0

NORMALIZE_SUFFIXES = [
    "inc", "inc.", "incorporated",
    "llc", "l.l.c.",
    "lp", "l.p.", "llp", "l.l.p.",
    "ltd", "ltd.", "limited",
    "corp", "corp.", "corporation",
    "co", "co.", "company",
    "plc", "sa", "s.a.", "ag", "gmbh", "nv", "n.v.", "bv", "b.v.",
    "holdings", "holding", "group",
]

# ---------------------------------------------------------------------------
# Known subsidiary/DBA aliases.
#
# Real, disclosed gap found while building this project: fuzzy matching
# (direct/token-sort/token-set similarity) cannot bridge a subsidiary name to
# its parent when the two share no normalized tokens at all -- e.g. "GE Power"
# vs "General Electric Company" score well below FUZZY_ADJUDICATE_THRESHOLD,
# so neither auto-merge nor the adjudicator band ever fires. Confirmed by
# computing the actual similarity() value against the real seed data before
# assuming fuzzy matching would be sufficient (see tests/test_entity_resolver.py).
#
# This table is a small, curated fix for the highest-value known cases in the
# demo data -- not a general solution. It intentionally does not attempt to
# resolve every possible corporate-family relationship.
# ---------------------------------------------------------------------------
KNOWN_ALIASES: dict[str, str] = {
    "ge power": "General Electric Company",
    "ge aviation": "General Electric Company",
    "ge capital": "General Electric Company",
}

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
OUTPUT_DIR = "output"
GRAPH_JSON_PATH = "output/entity_graph.json"
GRAPH_PNG_PATH = "output/entity_graph.png"
