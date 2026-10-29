import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from click.testing import CliRunner

import cli as cli_module


def _redirect_output_paths(monkeypatch, tmp_path):
    graph_path = str(tmp_path / "entity_graph.json")
    png_path = str(tmp_path / "entity_graph.png")
    monkeypatch.setattr(cli_module, "GRAPH_JSON_PATH", graph_path)
    monkeypatch.setattr(cli_module, "GRAPH_PNG_PATH", png_path)
    monkeypatch.setattr(cli_module, "OUTPUT_DIR", str(tmp_path))
    return graph_path, png_path


def test_query_before_build_reports_missing_graph(monkeypatch, tmp_path):
    _redirect_output_paths(monkeypatch, tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["query", "Boeing"])
    assert result.exit_code == 0
    assert "No graph found" in result.output


def test_build_then_bridges_shows_goldman_sachs(monkeypatch, tmp_path):
    _redirect_output_paths(monkeypatch, tmp_path)
    runner = CliRunner()

    build_result = runner.invoke(cli_module.cli, ["build"])
    assert build_result.exit_code == 0, build_result.output
    assert "build complete" in build_result.output

    bridges_result = runner.invoke(cli_module.cli, ["bridges"])
    assert bridges_result.exit_code == 0, bridges_result.output
    assert "Goldman Sachs Group, Inc." in bridges_result.output


def test_build_then_query_shows_cross_project_mentions(monkeypatch, tmp_path):
    _redirect_output_paths(monkeypatch, tmp_path)
    runner = CliRunner()
    runner.invoke(cli_module.cli, ["build"])

    result = runner.invoke(cli_module.cli, ["query", "Goldman Sachs"])
    assert result.exit_code == 0, result.output
    assert "CROSS-PROJECT BRIDGE" in result.output
    assert "litigation_network" in result.output
    assert "debt_exposure_monitor" in result.output


def test_build_then_stats_and_list_projects(monkeypatch, tmp_path):
    _redirect_output_paths(monkeypatch, tmp_path)
    runner = CliRunner()
    runner.invoke(cli_module.cli, ["build"])

    stats_result = runner.invoke(cli_module.cli, ["stats"])
    assert stats_result.exit_code == 0, stats_result.output
    assert "Canonical entities" in stats_result.output

    projects_result = runner.invoke(cli_module.cli, ["list-projects"])
    assert projects_result.exit_code == 0, projects_result.output
    assert "ghosttrace" in projects_result.output
    assert "acquisition_brief" in projects_result.output


def test_build_then_render_writes_png(monkeypatch, tmp_path):
    graph_path, png_path = _redirect_output_paths(monkeypatch, tmp_path)
    runner = CliRunner()
    runner.invoke(cli_module.cli, ["build"])

    result = runner.invoke(cli_module.cli, ["render"])
    assert result.exit_code == 0, result.output
    assert os.path.exists(png_path)


def test_query_no_match_reports_clearly(monkeypatch, tmp_path):
    _redirect_output_paths(monkeypatch, tmp_path)
    runner = CliRunner()
    runner.invoke(cli_module.cli, ["build"])

    result = runner.invoke(cli_module.cli, ["query", "zzz_not_a_real_entity_zzz"])
    assert result.exit_code == 0
    assert "No entity found" in result.output
