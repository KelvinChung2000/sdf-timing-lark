"""Analysis modules for SDF timing data."""

from sdf_timing.analysis.diff import DiffEntry, DiffResult, diff
from sdf_timing.analysis.export import to_dot
from sdf_timing.analysis.pathgraph import (
    EndpointResult,
    RankedPath,
    TimingEdge,
    TimingGraph,
    VerificationResult,
    batch_endpoint_analysis,
    compute_slack,
    critical_path,
    decompose_delay,
    rank_paths,
    verify_path,
)
from sdf_timing.analysis.query import query
from sdf_timing.analysis.report import generate_report
from sdf_timing.analysis.stats import SDFStats, compute_stats
from sdf_timing.analysis.validate import LintIssue, validate

__all__ = [
    # diff
    "DiffEntry",
    "DiffResult",
    "diff",
    # export
    "to_dot",
    # pathgraph
    "EndpointResult",
    "RankedPath",
    "TimingEdge",
    "TimingGraph",
    "VerificationResult",
    "batch_endpoint_analysis",
    "compute_slack",
    "critical_path",
    "decompose_delay",
    "rank_paths",
    "verify_path",
    # query
    "query",
    # report
    "generate_report",
    # stats
    "SDFStats",
    "compute_stats",
    # validate
    "LintIssue",
    "validate",
]
