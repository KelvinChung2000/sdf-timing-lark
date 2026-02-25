from sdf_toolkit.analysis.export import to_dot
from sdf_toolkit.core.pathgraph import TimingGraph, critical_path


class TestToDot:
    def test_basic_dot(self, spec1_graph: TimingGraph) -> None:
        result = to_dot(spec1_graph)
        assert result.startswith("digraph timing {")
        assert "rankdir=LR;" in result
        assert result.endswith("}")

    def test_contains_nodes(self, spec1_graph: TimingGraph) -> None:
        result = to_dot(spec1_graph)
        assert '"P1/z"' in result
        assert '"P2/i"' in result

    def test_contains_edges(self, spec1_graph: TimingGraph) -> None:
        result = to_dot(spec1_graph)
        assert "->" in result
        assert "label=" in result


class TestToDotHighlight:
    def test_highlight_path(self, spec1_graph: TimingGraph) -> None:
        cp = critical_path(spec1_graph, "P1/z", "P2/i")
        assert cp is not None
        result = to_dot(spec1_graph, highlight_path=cp)
        assert 'color="red"' in result
        assert "penwidth=2.0" in result

    def test_no_highlight(self, spec1_graph: TimingGraph) -> None:
        result = to_dot(spec1_graph, highlight_path=None)
        assert 'color="red"' not in result


class TestToDotCluster:
    def test_cluster_by_instance(self, spec1_graph: TimingGraph) -> None:
        result = to_dot(spec1_graph, cluster_by_instance=True)
        assert "subgraph cluster_" in result
        assert "label=" in result

    def test_no_cluster(self, spec1_graph: TimingGraph) -> None:
        result = to_dot(spec1_graph, cluster_by_instance=False)
        assert "subgraph cluster_" not in result

    def test_cluster_with_highlight(self, spec1_graph: TimingGraph) -> None:
        cp = critical_path(spec1_graph, "P1/z", "P2/i")
        result = to_dot(spec1_graph, highlight_path=cp, cluster_by_instance=True)
        assert "subgraph cluster_" in result
        assert 'color="red"' in result
