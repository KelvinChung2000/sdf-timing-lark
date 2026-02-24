from __future__ import annotations

import json
from typing import TYPE_CHECKING

from conftest import DATA_DIR
from typer.testing import CliRunner

from sdf_timing.cli import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

SPEC_EXAMPLE1 = str(DATA_DIR / "spec-example1.sdf")


class TestParse:
    def test_parse_json(self) -> None:
        result = runner.invoke(app, ["parse", SPEC_EXAMPLE1])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "header" in data
        assert "cells" in data

    def test_parse_sdf(self) -> None:
        result = runner.invoke(app, ["parse", SPEC_EXAMPLE1, "--format", "sdf"])
        assert result.exit_code == 0
        assert "DELAYFILE" in result.output

    def test_parse_missing_file(self) -> None:
        result = runner.invoke(app, ["parse", "/nonexistent/file.sdf"])
        assert result.exit_code != 0


class TestEmit:
    def test_emit_roundtrip(self, tmp_path: Path) -> None:
        parse_result = runner.invoke(app, ["parse", SPEC_EXAMPLE1])
        assert parse_result.exit_code == 0

        json_file = tmp_path / "roundtrip.json"
        json_file.write_text(parse_result.output)

        emit_result = runner.invoke(app, ["emit", str(json_file)])
        assert emit_result.exit_code == 0
        assert "DELAYFILE" in emit_result.output


class TestInfo:
    def test_info(self) -> None:
        result = runner.invoke(app, ["info", SPEC_EXAMPLE1])
        assert result.exit_code == 0
        assert "SDF Header" in result.output
        assert "Cell Summary" in result.output


class TestCompose:
    def test_compose(self) -> None:
        result = runner.invoke(app, ["compose", SPEC_EXAMPLE1, "P1/z", "P2/i"])
        assert result.exit_code == 0
        assert "Path 1" in result.output

    def test_compose_verbose(self) -> None:
        result = runner.invoke(app, ["compose", SPEC_EXAMPLE1, "P1/z", "P2/i", "-v"])
        assert result.exit_code == 0
        assert "->" in result.output


class TestVerify:
    def test_verify_pass(self) -> None:
        expected = json.dumps(
            {
                "fast": {"min": 1.805, "avg": None, "max": 1.805},
                "slow": {"min": 1.795, "avg": None, "max": 1.795},
            }
        )
        result = runner.invoke(
            app,
            ["verify", SPEC_EXAMPLE1, "P1/z", "P2/i", "--expected", expected],
        )
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_verify_fail(self) -> None:
        expected = json.dumps(
            {
                "fast": {"min": 999.0, "avg": None, "max": 999.0},
                "slow": {"min": 999.0, "avg": None, "max": 999.0},
            }
        )
        result = runner.invoke(
            app,
            ["verify", SPEC_EXAMPLE1, "P1/z", "P2/i", "--expected", expected],
        )
        assert result.exit_code == 1
        assert "FAIL" in result.output


class TestDecompose:
    def test_decompose(self) -> None:
        total = json.dumps({"nominal": {"min": 3.0, "avg": None, "max": 3.0}})
        known = json.dumps({"nominal": {"min": 1.0, "avg": None, "max": 1.0}})
        result = runner.invoke(app, ["decompose", "--total", total, "--known", known])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["nominal"]["min"] == 2.0
        assert data["nominal"]["max"] == 2.0


class TestCriticalPathCmd:
    def test_critical_path(self) -> None:
        result = runner.invoke(app, ["critical-path", SPEC_EXAMPLE1, "P1/z", "P2/i"])
        assert result.exit_code == 0
        assert "Critical path scalar" in result.output
        assert "->" in result.output

    def test_critical_path_with_field(self) -> None:
        result = runner.invoke(
            app,
            ["critical-path", SPEC_EXAMPLE1, "P1/z", "P2/i", "--field", "fast"],
        )
        assert result.exit_code == 0
        assert "Critical path scalar" in result.output

    def test_critical_path_no_path(self) -> None:
        result = runner.invoke(app, ["critical-path", SPEC_EXAMPLE1, "P2/i", "P1/z"])
        assert result.exit_code == 1
        assert "No path found" in result.output


class TestRankPathsCmd:
    def test_rank_paths(self) -> None:
        result = runner.invoke(app, ["rank-paths", SPEC_EXAMPLE1, "P1/z", "P2/i"])
        assert result.exit_code == 0
        assert "#1" in result.output
        assert "#2" in result.output

    def test_rank_paths_limit(self) -> None:
        result = runner.invoke(
            app, ["rank-paths", SPEC_EXAMPLE1, "P1/z", "P2/i", "-n", "1"]
        )
        assert result.exit_code == 0
        assert "#1" in result.output
        assert "#2" not in result.output

    def test_rank_paths_ascending(self) -> None:
        result = runner.invoke(
            app, ["rank-paths", SPEC_EXAMPLE1, "P1/z", "P2/i", "--ascending"]
        )
        assert result.exit_code == 0

    def test_rank_paths_no_path(self) -> None:
        result = runner.invoke(app, ["rank-paths", SPEC_EXAMPLE1, "P2/i", "P1/z"])
        assert result.exit_code == 1
        assert "No paths found" in result.output


class TestSlackCmd:
    def test_slack_positive(self) -> None:
        result = runner.invoke(app, ["slack", SPEC_EXAMPLE1, "P1/z", "P2/i", "10.0"])
        assert result.exit_code == 0
        assert "Slack:" in result.output

    def test_slack_negative(self) -> None:
        result = runner.invoke(app, ["slack", SPEC_EXAMPLE1, "P1/z", "P2/i", "0.5"])
        assert result.exit_code == 0
        assert "TIMING VIOLATION" in result.output

    def test_slack_no_path(self) -> None:
        result = runner.invoke(app, ["slack", SPEC_EXAMPLE1, "P2/i", "P1/z", "10.0"])
        assert result.exit_code == 1


class TestDotCmd:
    def test_dot_stdout(self) -> None:
        result = runner.invoke(app, ["dot", SPEC_EXAMPLE1])
        assert result.exit_code == 0
        assert "digraph timing" in result.output
        assert "rankdir=LR" in result.output

    def test_dot_cluster(self) -> None:
        result = runner.invoke(app, ["dot", SPEC_EXAMPLE1, "--cluster"])
        assert result.exit_code == 0
        assert "subgraph cluster_" in result.output

    def test_dot_highlight(self) -> None:
        result = runner.invoke(
            app,
            [
                "dot",
                SPEC_EXAMPLE1,
                "--highlight-source",
                "P1/z",
                "--highlight-sink",
                "P2/i",
            ],
        )
        assert result.exit_code == 0
        assert 'color="red"' in result.output

    def test_dot_output_file(self, tmp_path: Path) -> None:
        out = tmp_path / "graph.dot"
        result = runner.invoke(app, ["dot", SPEC_EXAMPLE1, "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text()
        assert "digraph timing" in content


class TestNoArgs:
    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        assert "Usage" in result.output
