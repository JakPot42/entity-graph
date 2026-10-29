"""Source adapters -- one module per federated portfolio tool.

Each module exposes:
  PROJECT_KEY    short slug used as the graph's project-node id
  PROJECT_LABEL  human-readable project name
  get_entities() -> list[dict]       raw entity sightings (name, entity_type,
                                      context, reference, url)
  get_relationships() -> list[dict]  optional intra-project structural links
                                      (owner/owned, supplier/customer, etc.),
                                      using the same raw names as get_entities()
"""
from __future__ import annotations

from . import (
    acquisition_brief,
    debt_exposure_monitor,
    friendshore,
    ghosttrace,
    litigation_network,
    tech_scanner,
)

ALL_SOURCES = [
    ghosttrace,
    friendshore,
    litigation_network,
    debt_exposure_monitor,
    tech_scanner,
    acquisition_brief,
]
