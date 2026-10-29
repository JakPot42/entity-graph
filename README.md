# Unified Entity Graph

## Scope

A federation layer, not a new intelligence tool. GhostTrace, FriendShore,
Litigation Network, Debt Exposure Monitor, Emerging Tech Horizon Scanner,
and the Pre-Acquisition Intelligence Brief
each independently resolve entities within their own demo data, but none of
them know the others exist. This project ingests each tool's structured
entity output, assigns stable cross-project entity IDs, and answers a
question no single tool can: *"show me every mention of this entity across
all portfolio tools."*

It reuses a fuzzy entity-resolution engine, extended
with a `mentions` list per entity (one per source-project sighting) and a
small curated alias table for known corporate subsidiaries that plain fuzzy
matching cannot bridge (see "A real, disclosed gap" below).

```
py cli.py build              # ingest all 6 source projects, resolve, save the graph
py cli.py bridges             # list every entity recognized across 2+ projects
py cli.py query "Goldman"     # every mention of an entity, across every tool
py cli.py stats               # portfolio-wide federation counts
py cli.py list-projects       # federated projects + entity counts contributed
py cli.py render              # matplotlib PNG, bridge entities highlighted in red
```

---

## Ingestion design decision: static transcription, not live import

Each source adapter in `sources/` is a direct, cited transcription of that
project's real `seed_data.py` constants — not a live `import` of the source
project's runtime. This was a deliberate choice, not a shortcut: GhostTrace
and FriendShore pull in FastAPI, SQLAlchemy, and (for GhostTrace) ChromaDB
just to reach a handful of module-level list-of-dict constants; importing
all six source projects' full dependency stacks into one federation layer
would mean maintaining six different requirements.txt files' worth of
transitive dependencies just to read data that never changes at runtime in
any of them (these are `DEMO_MODE` seed datasets, not live feeds).

This mirrors the realistic production shape better than it might first
appear: a real federation layer consumes each tool's *exported* records
(an API response, a JSON export) — it does not reach into another service's
internal database. None of these six tools expose a live entity-export
API today, so the closest honest stand-in is a transcription of their
demo/seed data, cited back to the source file it came from in every
adapter's docstring.

**Real limitation this creates:** if a source project's `seed_data.py`
changes, its `sources/<project>.py` adapter here goes stale silently — there
is no automated sync. Acceptable for a demo of the federation mechanism
itself; a production version would ingest a real exported feed instead.

---

## What it actually found: 1 real cross-project bridge

Built by ingesting the six source projects' actual seed data (60 raw
sightings resolve to 52 entities; 1 is recognized across more than one
project), not constructed or invented to make a good demo:

| Entity | Seen in | How |
|---|---|---|
| **Goldman Sachs Group, Inc.** | `debt_exposure_monitor`, `litigation_network` | Real underwriter on a fictional demo supplier's bond issuance *and* real securities-litigation defendant (1MDB, $215M settlement) |

An earlier version also ingested a seventh source, a list of DOJ
trade-secret cases. It was removed on 29 October 2026, together with the
three bridges it produced.

`py cli.py bridges` reproduces this table live from the graph; `output/entity_graph.png`
renders it visually (red nodes = bridge entities, blue squares = the 6 source
projects).

---

## A real, disclosed gap: fuzzy matching alone misses "GE Power"

Before assuming the existing three-band fuzzy engine (auto-merge / adjudicate
/ distinct — unchanged since GhostTrace) would be enough, the actual
similarity score was computed against the seed data as it then stood (the
case-list source removed on 29 October 2026 named "GE Power"):

```
similarity("GE Power", "General Electric Company")  ->  33.3
```

33.3 is well below `FUZZY_ADJUDICATE_THRESHOLD` (75), so this pair never
even reaches the adjudicator — a Claude-backed adjudicator would never be
asked about it, because the fuzzy engine's own gate closes first. The two
strings share zero normalized tokens ("ge power" vs "general electric"), so
no amount of tuning the *existing* similarity measures closes the gap; they
are fundamentally token-overlap-based.

The fix is `config.KNOWN_ALIASES`: a small, curated table of subsidiary/DBA
names that maps `"ge power"` and `"ge aviation"` directly to `"General
Electric Company"`, checked *before* fuzzy scoring runs. It is deliberately
narrow — it resolves the specific gaps this build's real seed data exposed,
not a general corporate-family-resolution system. `tests/test_entity_resolver.py::test_real_gap_fuzzy_matching_cannot_bridge_ge_power_to_parent`
asserts the actual score, so this isn't a claim that goes unverified.

**A correctly-avoided false merge, for contrast:** FriendShore's fictional
demo supplier "Raytheon Components Group" scores 70.0 against tech-scanner's
real "Raytheon Technologies" — close, but still under the adjudicate
threshold, so they correctly stay distinct. Merging a fictional demo entity
into a real company by name-similarity alone would have been a worse bug
than missing a real link.

---

## Architecture

| File | Purpose |
|---|---|
| `config.py` | Thresholds, corporate-suffix list, `KNOWN_ALIASES`, output paths |
| `entity_resolver.py` | Fourth deployment: three-band fuzzy resolution + known-alias pre-pass + stable ID assignment |
| `sources/*.py` | One adapter per federated project: `get_entities()`, `get_relationships()` |
| `graph_store.py` | NetworkX `MultiDiGraph` build/save/load, query, bridge-detection, stats |
| `ingest.py` | Orchestrates: pull all sources -> resolve -> rewrite relationships onto canonical IDs -> build graph |
| `cli.py` | Click + Rich (`box.ASCII2`) CLI |

**Stable IDs, not sequence numbers.** `stable_id()` hashes the *normalized*
canonical name (`ENT-` + 8 hex chars of SHA-256), so re-running `build`
never reshuffles an ID another tool might already be citing — the same
entity always gets the same ID regardless of which source happened to
introduce it first.

**Mentions vs. relationships — two different edge types, same graph.**
Every raw entity sighting becomes a `mentioned_in` edge from the entity to
its source project (bipartite half, same pattern as citegraph's
citation<->project graph). Separately, four of the six source projects
also carry real *structural* relationships in their own seed data
(GhostTrace's ownership chain, FriendShore's supply chain, Debt Exposure
Monitor's lending, Pre-Acquisition Brief's litigation/corporate-family
links) — `ingest.py` rewrites each of those onto canonical entity IDs using
the same `alias_map` the resolver produces, so e.g. Goldman Sachs's lending
relationship to the demo supplier and its unrelated litigation-defendant
mention both resolve onto the *same* node.

**Adjudicator is wired but unexercised by the demo data.** `resolve_entities()`
accepts the same `Adjudicator` callable signature as every prior deployment
(`(name_a, name_b) -> bool`), for consistency and future extension — but no
pair in this build's actual 60 raw entities lands in the [75, 90) adjudicate
band without also being caught by the known-alias table first. Verified with
a real Northrop Grumman example in the test suite, not asserted.

---

## Test suite

48 tests, all passing (`py -m pytest tests/`):
- `test_entity_resolver.py` — normalization, stable IDs, the real GE-Power
  similarity gap, known-alias merging, correct non-merges (Raytheon,
  Parsons), adjudicator wiring
- `test_sources.py` — every adapter's shape, relationship referential
  integrity, source-data-derived counts (not hardcoded guesses)
- `test_graph_store.py` — graph construction, bridge detection, fuzzy
  query, save/load round-trip
- `test_ingest.py`: full end-to-end build, asserts the real documented
  bridge by name and project set
- `test_cli.py` — every command via `click.testing.CliRunner`

One real bug caught while building this, the same way every other build
this session caught its bugs — by actually running the tool, not by
inspection: `sources/friendshore.py`'s node dicts only set `is_focal: True`
on the one focal node (mirroring the real seed data, which omits the key
entirely on non-focal nodes) — a first-pass `n["is_focal"]` lookup crashed
with `KeyError` on the very first `py -m pytest` run. Fixed to `n.get("is_focal")`.
A second issue caught the same way: several context strings used a real
em-dash (`—`), which renders as `?` on the Windows console — the identical
Unicode/cp1252 issue citegraph documented and fixed with `_ascii_safe()`.
Fixed here by keeping all displayed text plain ASCII (`--`) at the source,
since every string in this project is self-authored rather than ingested
from arbitrary external text.

---

## Known limitations

- Static transcription of source seed data (see "Ingestion design decision"
  above) — adapters go stale if a source project's `seed_data.py` changes.
- `KNOWN_ALIASES` is a curated fix for the specific gaps this build's real
  data exposed, not a general corporate-family resolver.
- No live Claude adjudicator is wired into the CLI `build` command (the
  parameter exists in `ingest.build()` for parity with every prior
  `entity_resolver.py` deployment, but the demo doesn't need one — see
  Architecture above).
- Entity resolution here spans companies, institutions, and lenders, but
  intentionally does NOT include the individual people, judges, or law
  firms present in the source data (e.g. Litigation Network's judges and
  plaintiff firms) — scoped to the "same company/institution across tools"
  question this tool is scoped to, not full person-level resolution.
