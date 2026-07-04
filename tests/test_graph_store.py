import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import graph_store
from entity_resolver import resolve_entities


def _sample_graph():
    raw = [
        {"name": "Boeing Company", "source_project": "litigation_network", "entity_type": "company",
         "context": "defendant", "reference": "case-1"},
        {"name": "Boeing", "source_project": "ip_theft", "entity_type": "company",
         "context": "victim", "reference": "case-2"},
        {"name": "Meridian Holdings Ltd", "source_project": "ghosttrace", "entity_type": "company",
         "context": "owner", "reference": "DEMO-13D-001"},
        {"name": "Harborview Capital Partners LP", "source_project": "ghosttrace", "entity_type": "fund",
         "context": "focal", "reference": "DEMO-13D-001"},
    ]
    resolved, alias_map = resolve_entities(raw)
    relationships = [{
        "from_entity_id": alias_map[("ghosttrace", "Meridian Holdings Ltd")],
        "to_entity_id": alias_map[("ghosttrace", "Harborview Capital Partners LP")],
        "rel_type": "ownership",
        "source_project": "ghosttrace",
        "detail": "64% ownership",
    }]
    labels = {"litigation_network": "Litigation Network", "ip_theft": "IP Theft DB", "ghosttrace": "GhostTrace"}
    return graph_store.build_graph(resolved, relationships, labels), alias_map


def test_build_graph_node_and_edge_counts():
    graph, _ = _sample_graph()
    assert len(graph_store.project_nodes(graph)) == 3
    assert len(graph_store.entity_nodes(graph)) == 3  # Boeing merged, Meridian, Harborview
    stats = graph_store.portfolio_stats(graph)
    assert stats["total_mentions"] == 4
    assert stats["total_relationships"] == 1


def test_bridge_entities_finds_boeing_only():
    graph, _ = _sample_graph()
    bridges = graph_store.bridge_entities(graph)
    assert len(bridges) == 1
    assert bridges[0]["canonical_name"] == "Boeing Company"
    assert bridges[0]["projects"] == ["ip_theft", "litigation_network"]


def test_find_entity_fuzzy_matches_query():
    graph, _ = _sample_graph()
    match = graph_store.find_entity(graph, "boeing")
    assert match is not None
    entity_id, score = match
    assert graph.nodes[entity_id]["canonical_name"] == "Boeing Company"
    assert score > 90


def test_find_entity_returns_none_for_nonsense_query():
    graph, _ = _sample_graph()
    assert graph_store.find_entity(graph, "zzz_not_a_real_entity_zzz") is None


def test_relationships_for_reports_both_directions():
    graph, alias_map = _sample_graph()
    meridian_id = alias_map[("ghosttrace", "Meridian Holdings Ltd")]
    harborview_id = alias_map[("ghosttrace", "Harborview Capital Partners LP")]

    out_rels = graph_store.relationships_for(graph, meridian_id)
    assert len(out_rels) == 1
    assert out_rels[0]["direction"] == "outgoing"
    assert out_rels[0]["other_entity_name"] == "Harborview Capital Partners LP"

    in_rels = graph_store.relationships_for(graph, harborview_id)
    assert len(in_rels) == 1
    assert in_rels[0]["direction"] == "incoming"
    assert in_rels[0]["other_entity_name"] == "Meridian Holdings Ltd"


def test_save_and_load_round_trip(tmp_path):
    graph, _ = _sample_graph()
    path = str(tmp_path / "graph.json")
    graph_store.save_graph(graph, path)
    loaded = graph_store.load_graph(path)

    assert set(graph_store.entity_nodes(loaded)) == set(graph_store.entity_nodes(graph))
    assert set(graph_store.project_nodes(loaded)) == set(graph_store.project_nodes(graph))
    assert graph_store.portfolio_stats(loaded) == graph_store.portfolio_stats(graph)
