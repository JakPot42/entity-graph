"""
entity_resolver.py -- cross-project entity deduplication.

Fourth deployment of the same three-band fuzzy-match engine first built for
GhostTrace (jurisdiction-conflict gate for shell-company ownership chains),
then adapted for tech-scanner (institution names, no conflict gate needed)
and PatientFusion (DOB gate instead of jurisdiction). This deployment merges
companies, institutions, and lenders arriving from seven different portfolio
tools, so entities carry a `mentions` list (one entry per source_project
sighting) instead of the single-project `sources` list the earlier versions
used -- the whole point of this build is to see when the SAME entity was
mentioned by MORE THAN ONE tool.

Three bands (thresholds in config), unchanged from every prior deployment:
  similarity >= FUZZY_AUTO_MERGE_THRESHOLD  -> merge automatically
  similarity >= FUZZY_ADJUDICATE_THRESHOLD  -> ask the adjudicator
  below                                     -> distinct entities

One addition specific to this deployment: `resolve_known_alias()`, a small
curated table (config.KNOWN_ALIASES) checked before fuzzy scoring. It exists
because fuzzy matching alone cannot bridge a subsidiary name to its parent
when the two share no normalized tokens (e.g. "GE Power" vs "General Electric
Company") -- see config.py's comment and tests/test_entity_resolver.py for the
real similarity score that proves this gap, rather than assuming it.
"""

from __future__ import annotations

import hashlib
from difflib import SequenceMatcher
from typing import Callable

from config import (
    FUZZY_ADJUDICATE_THRESHOLD,
    FUZZY_AUTO_MERGE_THRESHOLD,
    KNOWN_ALIASES,
    NORMALIZE_SUFFIXES,
)

# Adjudicator signature: (name_a, name_b) -> bool (same entity?)
Adjudicator = Callable[[str, str], bool]

_SUFFIX_SET = {s.replace(".", "") for s in NORMALIZE_SUFFIXES}
_KNOWN_ALIASES = {k.lower().strip(): v for k, v in KNOWN_ALIASES.items()}


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, drop leading 'the' and corporate suffixes."""
    cleaned = "".join(ch if ch.isalnum() or ch == " " else " " for ch in name.lower())
    tokens = cleaned.split()
    if tokens and tokens[0] == "the":
        tokens = tokens[1:]
    while tokens and tokens[-1] in _SUFFIX_SET:
        tokens = tokens[:-1]
    for n in (3, 2):
        if len(tokens) >= n and "".join(tokens[-n:]) in _SUFFIX_SET:
            tokens = tokens[:-n]
            break
    return " ".join(tokens)


def resolve_known_alias(name: str) -> str | None:
    """Look up a curated subsidiary/DBA alias (config.KNOWN_ALIASES).

    Returns the parent entity's canonical display name if `name` (normalized)
    is a known alias, else None. Runs BEFORE fuzzy matching -- see module
    docstring for why fuzzy matching alone isn't enough for these cases.
    """
    return _KNOWN_ALIASES.get(normalize_name(name))


def similarity(a: str, b: str) -> float:
    """0-100 similarity between two normalized names.

    Max of three measures so word order and partial overlap don't defeat the
    match: direct ratio, token-sort ratio, and token-set Jaccard overlap.
    """
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 100.0
    direct = SequenceMatcher(None, na, nb).ratio()
    ta, tb = na.split(), nb.split()
    token_sort = SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    sa, sb = set(ta), set(tb)
    token_set = len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0
    return max(direct, token_sort, token_set) * 100


def stable_id(canonical_name: str) -> str:
    """Deterministic cross-run entity ID.

    The same canonical name always produces the same ID, so re-running
    `entity_graph build` doesn't reshuffle IDs a saved query or another
    tool might already be citing.
    """
    digest = hashlib.sha256(normalize_name(canonical_name).encode("utf-8")).hexdigest()
    return f"ENT-{digest[:8].upper()}"


def _mention(raw: dict) -> dict:
    return {
        "source_project": raw["source_project"],
        "name_used": raw["name"],
        "entity_type": raw.get("entity_type"),
        "context": raw.get("context"),
        "reference": raw.get("reference"),
        "url": raw.get("url"),
    }


def _merge_into(canonical: dict, raw: dict) -> None:
    """Fold a new sighting into an existing canonical entity."""
    if raw["name"] not in canonical["aliases"] and raw["name"] != canonical["canonical_name"]:
        canonical["aliases"].append(raw["name"])
    if not canonical.get("entity_type") and raw.get("entity_type"):
        canonical["entity_type"] = raw["entity_type"]
    canonical["mentions"].append(_mention(raw))


def _new_canonical(raw: dict, canonical_name: str | None = None) -> dict:
    name = canonical_name or raw["name"]
    return {
        "entity_id": stable_id(name),
        "canonical_name": name,
        "aliases": [] if name == raw["name"] else [raw["name"]],
        "entity_type": raw.get("entity_type"),
        "mentions": [_mention(raw)],
    }


def resolve_entities(
    raw_entities: list[dict],
    adjudicator: Adjudicator | None = None,
) -> tuple[list[dict], dict[tuple[str, str], str]]:
    """Collapse name variants (from any number of source projects) into
    canonical entities with a stable cross-run entity_id.

    Each raw entity dict must have at least {"name": str, "source_project":
    str}. Optional: entity_type, context, reference, url.

    Returns (resolved_entities, alias_map) where alias_map maps
    (source_project, raw_name) -> entity_id -- used by ingest.py to rewrite
    each source project's own structural relationships (ownership, supply
    chain, lending) onto canonical entity IDs.

    With no adjudicator, the ambiguous band stays unmerged: a missed merge
    is recoverable, a wrong merge poisons the graph.
    """
    resolved: list[dict] = []
    by_canonical: dict[str, dict] = {}
    alias_map: dict[tuple[str, str], str] = {}
    verdict_cache: dict[frozenset[str], bool] = {}

    def _ask(name_a: str, name_b: str) -> bool:
        if adjudicator is None:
            return False
        key = frozenset((name_a, name_b))
        if key not in verdict_cache:
            verdict_cache[key] = adjudicator(name_a, name_b)
        return verdict_cache[key]

    for raw in raw_entities:
        name = (raw.get("name") or "").strip()
        source_project = raw.get("source_project")
        if not name or not source_project:
            continue
        raw = {**raw, "name": name}

        known_parent = resolve_known_alias(name)
        if known_parent is not None:
            canonical = by_canonical.get(known_parent)
            if canonical is None:
                canonical = _new_canonical(raw, canonical_name=known_parent)
                resolved.append(canonical)
                by_canonical[known_parent] = canonical
            else:
                _merge_into(canonical, raw)
            alias_map[(source_project, name)] = canonical["entity_id"]
            continue

        best: dict | None = None
        best_score = 0.0
        for canonical in resolved:
            for variant in [canonical["canonical_name"], *canonical["aliases"]]:
                score = similarity(name, variant)
                if score > best_score:
                    best_score = score
                    best = canonical

        merged = False
        if best is not None:
            if best_score >= FUZZY_AUTO_MERGE_THRESHOLD:
                merged = True
            elif best_score >= FUZZY_ADJUDICATE_THRESHOLD:
                merged = _ask(name, best["canonical_name"])

        if merged and best is not None:
            _merge_into(best, raw)
            alias_map[(source_project, name)] = best["entity_id"]
        else:
            entity = _new_canonical(raw)
            resolved.append(entity)
            by_canonical[entity["canonical_name"]] = entity
            alias_map[(source_project, name)] = entity["entity_id"]

    return resolved, alias_map
