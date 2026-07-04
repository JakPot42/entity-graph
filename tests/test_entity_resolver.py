import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FUZZY_ADJUDICATE_THRESHOLD, FUZZY_AUTO_MERGE_THRESHOLD
from entity_resolver import (
    normalize_name,
    resolve_entities,
    resolve_known_alias,
    similarity,
    stable_id,
)


def _raw(name, source_project, **kw):
    return {"name": name, "source_project": source_project, **kw}


def test_normalize_name_strips_suffixes_and_articles():
    assert normalize_name("Boeing Company") == "boeing"
    assert normalize_name("The Boeing Company") == "boeing"
    assert normalize_name("Goldman Sachs Group, Inc.") == "goldman sachs"
    assert normalize_name("Goldman Sachs & Co. LLC") == "goldman sachs"


def test_stable_id_is_deterministic_and_case_insensitive():
    assert stable_id("Boeing Company") == stable_id("boeing company")
    assert stable_id("Boeing Company") == stable_id("Boeing")  # both normalize to "boeing"
    assert stable_id("Boeing Company") != stable_id("Northrop Grumman")
    assert stable_id("X").startswith("ENT-")


def test_real_gap_fuzzy_matching_cannot_bridge_ge_power_to_parent():
    """The documented reason KNOWN_ALIASES exists: confirm the actual similarity
    score, don't assume it. "GE Power" and "General Electric Company" share zero
    normalized tokens, so they never even reach the adjudicate band."""
    score = similarity("GE Power", "General Electric Company")
    assert score < FUZZY_ADJUDICATE_THRESHOLD


def test_known_alias_table_resolves_ge_subsidiaries():
    assert resolve_known_alias("GE Power") == "General Electric Company"
    assert resolve_known_alias("ge aviation") == "General Electric Company"
    assert resolve_known_alias("Boeing") is None


def test_resolve_entities_auto_merges_suffix_variants():
    raw = [
        _raw("Boeing Company", "litigation_network", entity_type="company"),
        _raw("Boeing", "ip_theft", entity_type="company"),
    ]
    resolved, alias_map = resolve_entities(raw)
    assert len(resolved) == 1
    assert resolved[0]["canonical_name"] == "Boeing Company"
    assert set(resolved[0]["aliases"]) == {"Boeing"}
    assert {m["source_project"] for m in resolved[0]["mentions"]} == {"litigation_network", "ip_theft"}
    assert alias_map[("litigation_network", "Boeing Company")] == resolved[0]["entity_id"]
    assert alias_map[("ip_theft", "Boeing")] == resolved[0]["entity_id"]


def test_resolve_entities_merges_via_known_alias_across_three_projects():
    raw = [
        _raw("General Electric Company", "litigation_network", entity_type="company"),
        _raw("GE Power", "ip_theft", entity_type="company"),
        _raw("GE Aviation", "ip_theft", entity_type="company"),
    ]
    resolved, alias_map = resolve_entities(raw)
    assert len(resolved) == 1
    entity = resolved[0]
    assert entity["canonical_name"] == "General Electric Company"
    assert set(entity["aliases"]) == {"GE Power", "GE Aviation"}
    assert len(entity["mentions"]) == 3


def test_resolve_entities_does_not_merge_unrelated_similar_looking_names():
    """Fictional 'Raytheon Components Group' (FriendShore demo supplier) must
    NOT merge with the real 'Raytheon Technologies' (tech_scanner) -- they are
    deliberately different entities and a false merge would poison the graph."""
    raw = [
        _raw("Raytheon Components Group", "friendshore", entity_type="company"),
        _raw("Raytheon Technologies", "tech_scanner", entity_type="institution"),
    ]
    resolved, _ = resolve_entities(raw)
    assert len(resolved) == 2


def test_resolve_entities_keeps_same_corporate_family_distinct_when_legally_separate():
    """Parsons Corporation and Parsons Federal Services Inc. are related but
    legally distinct entities in the real acquisition_brief demo data -- token
    overlap is partial, not enough to auto-merge, which is correct."""
    raw = [
        _raw("Parsons Corporation", "acquisition_brief", entity_type="company"),
        _raw("Parsons Federal Services Inc.", "acquisition_brief", entity_type="company"),
    ]
    resolved, _ = resolve_entities(raw)
    assert len(resolved) == 2


def test_resolve_entities_ignores_blank_or_unsourced_entries():
    raw = [
        _raw("", "ghosttrace"),
        {"name": "No Project"},
        _raw("Valid Co", "ghosttrace"),
    ]
    resolved, _ = resolve_entities(raw)
    assert len(resolved) == 1
    assert resolved[0]["canonical_name"] == "Valid Co"


def test_adjudicate_band_uses_injected_adjudicator():
    calls = []

    def adjudicator(a, b):
        calls.append((a, b))
        return True

    # "Meta Platforms Inc" vs "Meta Platforms" land in the adjudicate band
    # (not an exact suffix-strip match, but close): construct a case that
    # actually falls in [ADJUDICATE, AUTO_MERGE) rather than assuming one.
    a, b = "Northrop Grumman Systems Corporation", "Northrop Grumman"
    score = similarity(a, b)
    assert FUZZY_ADJUDICATE_THRESHOLD <= score < FUZZY_AUTO_MERGE_THRESHOLD

    raw = [
        _raw(b, "tech_scanner", entity_type="institution"),
        _raw(a, "friendshore", entity_type="institution"),
    ]
    resolved, _ = resolve_entities(raw, adjudicator=adjudicator)
    assert len(resolved) == 1
    assert calls  # adjudicator was actually consulted


def test_adjudicate_band_without_adjudicator_stays_distinct():
    a, b = "Northrop Grumman Systems Corporation", "Northrop Grumman"
    raw = [_raw(b, "tech_scanner"), _raw(a, "friendshore")]
    resolved, _ = resolve_entities(raw, adjudicator=None)
    assert len(resolved) == 2
