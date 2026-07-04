"""
ingest.py -- orchestrates the federation build: pull raw entities from every
source adapter, resolve them to canonical cross-project entities, rewrite
each source's own structural relationships onto canonical entity IDs, and
assemble the NetworkX graph.
"""
from __future__ import annotations

import graph_store
from entity_resolver import Adjudicator, resolve_entities
from sources import ALL_SOURCES


def build(adjudicator: Adjudicator | None = None):
    """Returns (graph, resolved_entities, relationships)."""
    raw_entities: list[dict] = []
    relationships_by_project: dict[str, list[dict]] = {}
    project_labels: dict[str, str] = {}

    for module in ALL_SOURCES:
        project_labels[module.PROJECT_KEY] = module.PROJECT_LABEL
        raw_entities.extend(module.get_entities())
        relationships_by_project[module.PROJECT_KEY] = (
            module.get_relationships() if hasattr(module, "get_relationships") else []
        )

    resolved, alias_map = resolve_entities(raw_entities, adjudicator=adjudicator)

    relationships: list[dict] = []
    for project_key, rels in relationships_by_project.items():
        for rel in rels:
            from_id = alias_map.get((project_key, rel["from"]))
            to_id = alias_map.get((project_key, rel["to"]))
            if not from_id or not to_id or from_id == to_id:
                continue
            relationships.append({
                "from_entity_id": from_id,
                "to_entity_id": to_id,
                "rel_type": rel["rel_type"],
                "source_project": project_key,
                "detail": rel.get("detail"),
            })

    graph = graph_store.build_graph(resolved, relationships, project_labels)
    return graph, resolved, relationships
