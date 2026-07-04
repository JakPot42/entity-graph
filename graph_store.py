"""
graph_store.py -- NetworkX-backed federation graph.

Consistent with the NetworkX usage already established in FriendShore
(supply chain) and Cable Resilience (P19), and with the bipartite
citation<->project graph pattern from citegraph (P73). Here the bipartite
half is entity<->project "mentioned_in" edges; the graph also carries each
source project's own structural relationships (ownership, supply chain,
lending, litigation) rewritten onto canonical entity IDs.

A MultiDiGraph is used (not a plain Graph) because two entities can be
linked by more than one edge -- e.g. two source projects independently
describing a relationship between the same two canonical entities, or the
same project describing more than one kind of link.
"""
from __future__ import annotations

import json

import networkx as nx

from config import MIN_QUERY_SCORE
from entity_resolver import similarity


def build_graph(
    resolved_entities: list[dict],
    relationships: list[dict],
    project_labels: dict[str, str],
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    for project_key, label in project_labels.items():
        graph.add_node(project_key, kind="project", label=label)

    for entity in resolved_entities:
        graph.add_node(
            entity["entity_id"],
            kind="entity",
            canonical_name=entity["canonical_name"],
            entity_type=entity.get("entity_type"),
            aliases=list(entity.get("aliases", [])),
        )
        for mention in entity["mentions"]:
            graph.add_edge(
                entity["entity_id"],
                mention["source_project"],
                kind="mentioned_in",
                name_used=mention["name_used"],
                context=mention.get("context"),
                reference=mention.get("reference"),
                url=mention.get("url"),
            )

    for rel in relationships:
        graph.add_edge(
            rel["from_entity_id"],
            rel["to_entity_id"],
            kind=rel["rel_type"],
            source_project=rel["source_project"],
            detail=rel.get("detail"),
        )

    return graph


def save_graph(graph: nx.MultiDiGraph, path: str) -> None:
    data = nx.node_link_data(graph)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_graph(path: str) -> nx.MultiDiGraph:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return nx.node_link_graph(data, directed=True, multigraph=True)


def entity_nodes(graph: nx.MultiDiGraph) -> list[str]:
    return [n for n, d in graph.nodes(data=True) if d.get("kind") == "entity"]


def project_nodes(graph: nx.MultiDiGraph) -> list[str]:
    return [n for n, d in graph.nodes(data=True) if d.get("kind") == "project"]


def mentions_for(graph: nx.MultiDiGraph, entity_id: str) -> list[dict]:
    out = []
    for _, project_key, data in graph.out_edges(entity_id, data=True):
        if data.get("kind") == "mentioned_in":
            out.append({"source_project": project_key, **{k: v for k, v in data.items() if k != "kind"}})
    return out


def relationships_for(graph: nx.MultiDiGraph, entity_id: str) -> list[dict]:
    """Structural (non-mention) edges touching this entity, in both directions."""
    out = []
    for _, to_id, data in graph.out_edges(entity_id, data=True):
        if data.get("kind") != "mentioned_in" and graph.nodes[to_id].get("kind") == "entity":
            out.append({
                "direction": "outgoing",
                "other_entity_id": to_id,
                "other_entity_name": graph.nodes[to_id].get("canonical_name"),
                "rel_type": data.get("kind"),
                "source_project": data.get("source_project"),
                "detail": data.get("detail"),
            })
    for from_id, _, data in graph.in_edges(entity_id, data=True):
        if data.get("kind") != "mentioned_in" and graph.nodes[from_id].get("kind") == "entity":
            out.append({
                "direction": "incoming",
                "other_entity_id": from_id,
                "other_entity_name": graph.nodes[from_id].get("canonical_name"),
                "rel_type": data.get("kind"),
                "source_project": data.get("source_project"),
                "detail": data.get("detail"),
            })
    return out


def find_entity(graph: nx.MultiDiGraph, query: str) -> tuple[str, float] | None:
    """Fuzzy-resolve a free-text query to the best-matching entity node.

    Returns (entity_id, score) or None if nothing clears MIN_QUERY_SCORE.
    Matches against canonical_name AND every known alias. A low floor is
    needed because SequenceMatcher finds some overlapping characters even
    between unrelated strings, so "nothing scores above zero" is not a
    meaningful no-match condition on its own.
    """
    best_id: str | None = None
    best_score = 0.0
    for node_id in entity_nodes(graph):
        data = graph.nodes[node_id]
        for variant in [data.get("canonical_name", ""), *data.get("aliases", [])]:
            score = similarity(query, variant)
            if score > best_score:
                best_score = score
                best_id = node_id
    if best_id is None or best_score < MIN_QUERY_SCORE:
        return None
    return best_id, best_score


def bridge_entities(graph: nx.MultiDiGraph) -> list[dict]:
    """Entities mentioned by 2+ distinct source projects -- the whole point
    of building this graph: the same real-world entity, seen in isolation by
    each tool, now visibly connected."""
    out = []
    for node_id in entity_nodes(graph):
        mentions = mentions_for(graph, node_id)
        projects = sorted({m["source_project"] for m in mentions})
        if len(projects) >= 2:
            data = graph.nodes[node_id]
            out.append({
                "entity_id": node_id,
                "canonical_name": data.get("canonical_name"),
                "entity_type": data.get("entity_type"),
                "projects": projects,
                "mention_count": len(mentions),
            })
    out.sort(key=lambda e: (-len(e["projects"]), e["canonical_name"]))
    return out


def portfolio_stats(graph: nx.MultiDiGraph) -> dict:
    entities = entity_nodes(graph)
    projects = project_nodes(graph)
    bridges = bridge_entities(graph)
    mention_edges = sum(1 for *_ , d in graph.edges(data=True) if d.get("kind") == "mentioned_in")
    relationship_edges = sum(1 for *_ , d in graph.edges(data=True) if d.get("kind") != "mentioned_in")
    return {
        "total_entities": len(entities),
        "total_projects": len(projects),
        "total_mentions": mention_edges,
        "total_relationships": relationship_edges,
        "bridge_entity_count": len(bridges),
        "bridge_entities": bridges,
    }
