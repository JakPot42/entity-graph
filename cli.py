"""
Unified Entity Graph -- Portfolio Bridge (P71) CLI.

Federation layer that assigns stable, cross-project entity IDs so the same
company/institution appearing across GhostTrace, FriendShore, Litigation
Network, Debt Exposure Monitor, Tech Scanner, and Pre-Acquisition Brief is
recognized as one node instead of six isolated sightings.

Every Table AND Panel must use box.ASCII2 -- Windows cp1252 terminal
compatibility, same discipline used across the rest of the portfolio.
"""
from __future__ import annotations

import os
import sys

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import graph_store
from config import GRAPH_JSON_PATH, GRAPH_PNG_PATH, OUTPUT_DIR
from ingest import build

console = Console(width=110)


def _load_or_error() -> graph_store.nx.MultiDiGraph | None:
    if not os.path.exists(GRAPH_JSON_PATH):
        console.print(
            f"[bold red]No graph found at {GRAPH_JSON_PATH}.[/bold red] "
            "Run `entity-graph build` first."
        )
        return None
    return graph_store.load_graph(GRAPH_JSON_PATH)


@click.group()
def cli() -> None:
    """
    Unified Entity Graph (P71) -- the federation layer Arbor's eventual
    Phase 6 merger would otherwise need to invent under pressure. Reuses
    entity_resolver.py (fourth deployment: GhostTrace -> tech-scanner ->
    PatientFusion -> here) to give six independently-built portfolio tools
    a shared notion of "the same company."
    """


@cli.command(name="build")
def build_cmd() -> None:
    """Ingest every source project's seed data, resolve entities, save the graph."""
    graph, resolved, relationships = build()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    graph_store.save_graph(graph, GRAPH_JSON_PATH)

    stats = graph_store.portfolio_stats(graph)
    t = Table(box=box.ASCII2, title="Unified Entity Graph -- build complete")
    t.add_column("Metric")
    t.add_column("Value", justify="right")
    t.add_row("Source projects", str(stats["total_projects"]))
    t.add_row("Canonical entities", str(stats["total_entities"]))
    t.add_row("Mentions (entity <-> project)", str(stats["total_mentions"]))
    t.add_row("Structural relationships", str(stats["total_relationships"]))
    t.add_row("Cross-project bridge entities", str(stats["bridge_entity_count"]))
    console.print(t)
    console.print(f"Saved to [bold]{GRAPH_JSON_PATH}[/bold]. Run `entity-graph bridges` to see the connections.")


@cli.command()
def bridges() -> None:
    """List every entity recognized across 2+ source projects."""
    graph = _load_or_error()
    if graph is None:
        return
    bridge_list = graph_store.bridge_entities(graph)
    if not bridge_list:
        console.print("No cross-project entities found.")
        return
    t = Table(box=box.ASCII2, title=f"Cross-Project Bridge Entities ({len(bridge_list)})")
    t.add_column("Entity ID")
    t.add_column("Canonical Name")
    t.add_column("Type")
    t.add_column("Projects", overflow="fold")
    t.add_column("Mentions", justify="right")
    for b in bridge_list:
        t.add_row(
            b["entity_id"],
            b["canonical_name"],
            b["entity_type"] or "-",
            ", ".join(b["projects"]),
            str(b["mention_count"]),
        )
    console.print(t)


@cli.command()
def stats() -> None:
    """Portfolio-wide federation counts."""
    graph = _load_or_error()
    if graph is None:
        return
    s = graph_store.portfolio_stats(graph)
    t = Table(box=box.ASCII2, title="Portfolio Federation Stats")
    t.add_column("Metric")
    t.add_column("Value", justify="right")
    t.add_row("Source projects", str(s["total_projects"]))
    t.add_row("Canonical entities", str(s["total_entities"]))
    t.add_row("Mentions", str(s["total_mentions"]))
    t.add_row("Structural relationships", str(s["total_relationships"]))
    t.add_row("Cross-project bridge entities", str(s["bridge_entity_count"]))
    console.print(t)


@cli.command(name="list-projects")
def list_projects() -> None:
    """Show every federated source project and how many entities it contributed."""
    graph = _load_or_error()
    if graph is None:
        return
    t = Table(box=box.ASCII2, title="Federated Source Projects")
    t.add_column("Project Key")
    t.add_column("Label")
    t.add_column("Entities Contributed", justify="right")
    for project_key in graph_store.project_nodes(graph):
        count = sum(
            1 for u, v, d in graph.in_edges(project_key, data=True) if d.get("kind") == "mentioned_in"
        )
        t.add_row(project_key, graph.nodes[project_key].get("label", ""), str(count))
    console.print(t)


@cli.command()
@click.argument("name")
def query(name: str) -> None:
    """Show every mention of an entity across all federated portfolio tools."""
    graph = _load_or_error()
    if graph is None:
        return
    match = graph_store.find_entity(graph, name)
    if match is None:
        console.print(f"[bold red]No entity found matching '{name}'.[/bold red]")
        return
    entity_id, score = match
    data = graph.nodes[entity_id]
    mentions = graph_store.mentions_for(graph, entity_id)
    relationships = graph_store.relationships_for(graph, entity_id)
    projects = sorted({m["source_project"] for m in mentions})

    header = f"{data['canonical_name']}  [{entity_id}]"
    if len(projects) >= 2:
        header += "  -- CROSS-PROJECT BRIDGE"
    console.print(Panel(header, box=box.ASCII2, style="bold cyan"))

    meta = Table(box=box.ASCII2, show_header=False)
    meta.add_row("Entity type", data.get("entity_type") or "-")
    meta.add_row("Match confidence", f"{score:.1f}/100")
    meta.add_row("Aliases", ", ".join(data.get("aliases") or []) or "-")
    meta.add_row("Seen in", ", ".join(projects))
    console.print(meta)

    if mentions:
        t = Table(box=box.ASCII2, title="Mentions")
        t.add_column("Project")
        t.add_column("Name Used")
        t.add_column("Context", overflow="fold")
        t.add_column("Reference", overflow="fold")
        for m in sorted(mentions, key=lambda m: m["source_project"]):
            t.add_row(m["source_project"], m["name_used"], m.get("context") or "-", m.get("reference") or "-")
        console.print(t)

    if relationships:
        t = Table(box=box.ASCII2, title="Structural Relationships")
        t.add_column("Direction")
        t.add_column("Other Entity")
        t.add_column("Type")
        t.add_column("Source Project")
        t.add_column("Detail", overflow="fold")
        for r in relationships:
            t.add_row(
                r["direction"], r["other_entity_name"], r["rel_type"], r["source_project"], r.get("detail") or "-"
            )
        console.print(t)


@cli.command()
def render() -> None:
    """Render a matplotlib PNG of the federation graph, bridge entities highlighted."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx

    graph = _load_or_error()
    if graph is None:
        return

    bridge_ids = {b["entity_id"] for b in graph_store.bridge_entities(graph)}
    pos = nx.spring_layout(graph, seed=42, k=0.6)

    fig, ax = plt.subplots(figsize=(14, 10))
    project_ids = graph_store.project_nodes(graph)
    entity_ids = graph_store.entity_nodes(graph)
    bridge_entity_ids = [e for e in entity_ids if e in bridge_ids]
    plain_entity_ids = [e for e in entity_ids if e not in bridge_ids]

    nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="#cccccc", width=0.6, arrows=False)
    nx.draw_networkx_nodes(graph, pos, nodelist=project_ids, node_color="#2b6cb0", node_shape="s", node_size=900, ax=ax)
    nx.draw_networkx_nodes(graph, pos, nodelist=plain_entity_ids, node_color="#a0aec0", node_size=180, ax=ax)
    nx.draw_networkx_nodes(graph, pos, nodelist=bridge_entity_ids, node_color="#e53e3e", node_size=420, ax=ax)

    project_labels = {p: graph.nodes[p]["label"].split(" --")[0] for p in project_ids}
    bridge_labels = {e: graph.nodes[e]["canonical_name"] for e in bridge_entity_ids}
    nx.draw_networkx_labels(graph, pos, labels=project_labels, font_size=9, font_weight="bold", ax=ax)
    nx.draw_networkx_labels(graph, pos, labels=bridge_labels, font_size=8, ax=ax)

    ax.set_title("Unified Entity Graph -- cross-project bridge entities in red")
    ax.axis("off")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig.savefig(GRAPH_PNG_PATH, dpi=150, bbox_inches="tight")
    console.print(f"Saved to [bold]{GRAPH_PNG_PATH}[/bold]")


if __name__ == "__main__":
    cli()
