import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from sources import ALL_SOURCES


@pytest.mark.parametrize("module", ALL_SOURCES, ids=lambda m: m.PROJECT_KEY)
def test_adapter_has_required_attributes(module):
    assert module.PROJECT_KEY
    assert module.PROJECT_LABEL
    assert callable(module.get_entities)
    assert callable(module.get_relationships)


@pytest.mark.parametrize("module", ALL_SOURCES, ids=lambda m: m.PROJECT_KEY)
def test_adapter_entities_well_formed(module):
    entities = module.get_entities()
    assert entities, f"{module.PROJECT_KEY} produced no entities"
    for e in entities:
        assert e["name"].strip()
        assert e["source_project"] == module.PROJECT_KEY


@pytest.mark.parametrize("module", ALL_SOURCES, ids=lambda m: m.PROJECT_KEY)
def test_adapter_relationships_reference_known_entity_names(module):
    entities = module.get_entities()
    names = {e["name"] for e in entities}
    for rel in module.get_relationships():
        assert rel["from"] in names, f"{module.PROJECT_KEY}: relationship 'from' {rel['from']!r} has no matching entity"
        assert rel["to"] in names, f"{module.PROJECT_KEY}: relationship 'to' {rel['to']!r} has no matching entity"
        assert rel["rel_type"]


def test_friendshore_supply_chain_edge_count_matches_seed_data():
    from sources import friendshore
    assert len(friendshore.get_relationships()) == 11


def test_ghosttrace_ownership_chain_edge_count_matches_seed_data():
    from sources import ghosttrace
    assert len(ghosttrace.get_relationships()) == 5


def test_ip_theft_has_the_natural_cross_project_bridge_victims():
    from sources import ip_theft
    names = {e["name"] for e in ip_theft.get_entities()}
    assert {"Boeing", "Northrop Grumman", "GE Power", "GE Aviation"} <= names


def test_debt_exposure_monitor_lending_edges_all_point_at_demo_company():
    from sources import debt_exposure_monitor as dem
    rels = dem.get_relationships()
    assert len(rels) == 6
    assert all(r["to"] == dem.DEMO_COMPANY for r in rels)
