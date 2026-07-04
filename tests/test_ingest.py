import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import graph_store
from ingest import build


def test_build_produces_a_graph_with_all_seven_projects():
    graph, resolved, relationships = build()
    assert len(graph_store.project_nodes(graph)) == 7
    assert len(resolved) > 30
    assert relationships  # ghosttrace, friendshore, debt_exposure, acquisition_brief all contribute edges


def test_build_finds_the_four_documented_cross_project_bridges():
    """The real, naturally-occurring overlaps found while researching this
    build: Boeing, General Electric, Goldman Sachs, and Northrop Grumman each
    appear in two independently-built portfolio tools' real seed data."""
    graph, _, _ = build()
    bridges = {b["canonical_name"]: set(b["projects"]) for b in graph_store.bridge_entities(graph)}

    assert bridges["Boeing Company"] == {"ip_theft", "litigation_network"}
    assert bridges["General Electric Company"] == {"ip_theft", "litigation_network"}
    assert bridges["Goldman Sachs Group, Inc."] == {"debt_exposure_monitor", "litigation_network"}
    assert bridges["Northrop Grumman"] == {"ip_theft", "tech_scanner"}


def test_build_does_not_incorrectly_merge_fictional_and_real_raytheon():
    graph, _, _ = build()
    match = graph_store.find_entity(graph, "Raytheon Components Group")
    assert match is not None
    entity_id, _ = match
    mentions = graph_store.mentions_for(graph, entity_id)
    assert {m["source_project"] for m in mentions} == {"friendshore"}


def test_relationships_rewritten_onto_canonical_ids_for_bridge_entities():
    """Goldman Sachs is a debt_exposure_monitor lender (structural edge) AND a
    litigation_network defendant (mention-only) -- confirm the lending edge
    lands on the SAME canonical entity id the bridge report uses."""
    graph, _, _ = build()
    match = graph_store.find_entity(graph, "Goldman Sachs")
    assert match is not None
    entity_id, _ = match
    rels = graph_store.relationships_for(graph, entity_id)
    assert any(r["rel_type"] == "lending" for r in rels)
