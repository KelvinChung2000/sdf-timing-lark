import networkx as nx
import pytest

from sdf_toolkit.analysis.pathgraph import (
    TimingGraph,
    VerificationResult,
    decompose_delay,
    verify_path,
)
from sdf_toolkit.core.model import DelayPaths, SDFFile, SDFHeader, Values

EXPECTED_NODES = {
    "P1/z",
    "B1/C1/i",
    "B1/C1/z",
    "B1/C2/i1",
    "B1/C2/i2",
    "B1/C2/z",
    "B2/C1/i",
    "B2/C1/z",
    "B2/C2/i1",
    "B2/C2/i2",
    "B2/C2/z",
    "D1/i",
    "D1/z",
    "P2/i",
    "P3/i",
}


class TestTimingGraphBuild:
    def test_nodes(self, spec1_graph: TimingGraph) -> None:
        nodes = spec1_graph.nodes()
        assert nodes == EXPECTED_NODES

    def test_edge_count(self, spec1_graph: TimingGraph) -> None:
        edges = spec1_graph.edges()
        assert len(edges) == 16

    def test_successors(self, spec1_graph: TimingGraph) -> None:
        succs = spec1_graph.successors("P1/z")
        sink_names = {e.sink for e in succs}
        assert sink_names == {"B1/C1/i", "B1/C2/i2"}

    def test_predecessors(self, spec1_graph: TimingGraph) -> None:
        preds = spec1_graph.predecessors("P2/i")
        source_names = {e.source for e in preds}
        assert source_names == {"B2/C2/z"}

    def test_graph_property(self, spec1_graph: TimingGraph) -> None:
        assert isinstance(spec1_graph.graph, nx.MultiDiGraph)


class TestFindPaths:
    def test_find_paths_p1_to_p2(self, spec1_graph: TimingGraph) -> None:
        paths = spec1_graph.find_paths("P1/z", "P2/i")
        assert len(paths) == 2

    def test_find_paths_no_path(self, spec1_graph: TimingGraph) -> None:
        paths = spec1_graph.find_paths("P2/i", "P1/z")
        assert paths == []


class TestComposeDelay:
    def test_compose_single_edge(self, spec1_graph: TimingGraph) -> None:
        succs = spec1_graph.successors("P1/z")
        edge_to_c1 = [e for e in succs if e.sink == "B1/C1/i"][0]
        result = spec1_graph.compose_delay([edge_to_c1])
        assert result.approx_eq(edge_to_c1.delay)

    def test_compose_p1_to_p2(self, spec1_graph: TimingGraph) -> None:
        paths = spec1_graph.find_paths("P1/z", "P2/i")
        delays = [spec1_graph.compose_delay(p) for p in paths]

        expected_path1 = DelayPaths(
            fast=Values(min=1.805, avg=None, max=1.805),
            slow=Values(min=1.795, avg=None, max=1.795),
        )
        expected_path2 = DelayPaths(
            fast=Values(min=1.355, avg=None, max=1.355),
            slow=Values(min=1.380, avg=None, max=1.380),
        )

        assert any(expected_path1.approx_eq(d, tolerance=1e-6) for d in delays)
        assert any(expected_path2.approx_eq(d, tolerance=1e-6) for d in delays)

    def test_compose_empty_path(self, spec1_graph: TimingGraph) -> None:
        with pytest.raises(ValueError, match="empty path"):
            spec1_graph.compose_delay([])


class TestVerifyPath:
    def test_verify_pass(self, spec1_graph: TimingGraph) -> None:
        expected = DelayPaths(
            fast=Values(min=1.805, avg=None, max=1.805),
            slow=Values(min=1.795, avg=None, max=1.795),
        )
        result = verify_path(spec1_graph, "P1/z", "P2/i", expected, tolerance=1e-6)
        assert isinstance(result, VerificationResult)
        assert result.passed is True
        assert result.source == "P1/z"
        assert result.sink == "P2/i"

    def test_verify_fail(self, spec1_graph: TimingGraph) -> None:
        expected = DelayPaths(
            nominal=Values(min=999.0, avg=None, max=999.0),
            fast=Values(min=999.0, avg=None, max=999.0),
        )
        result = verify_path(spec1_graph, "P1/z", "P2/i", expected)
        assert result.passed is False


class TestDecomposeDelay:
    def test_decompose(self) -> None:
        total = DelayPaths(
            nominal=Values(min=1.805, avg=None, max=1.805),
            fast=Values(min=1.795, avg=None, max=1.795),
        )
        known = DelayPaths(
            nominal=Values(min=1.0, avg=None, max=1.0),
            fast=Values(min=1.0, avg=None, max=1.0),
        )
        unknown = decompose_delay(total, known)
        expected = DelayPaths(
            nominal=Values(min=0.805, avg=None, max=0.805),
            fast=Values(min=0.795, avg=None, max=0.795),
        )
        assert unknown.approx_eq(expected, tolerance=1e-9)


class TestEmptyGraph:
    def test_empty_sdf(self) -> None:
        sdf = SDFFile(header=SDFHeader(), cells={})
        graph = TimingGraph(sdf)
        assert graph.nodes() == set()
        assert graph.edges() == []
