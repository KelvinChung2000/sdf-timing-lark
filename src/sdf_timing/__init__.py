"""sdf_timing -- parse and emit Standard Delay Format (SDF) timing files."""

from sdf_timing.analysis import (
    DiffEntry,
    DiffResult,
    EndpointResult,
    LintIssue,
    RankedPath,
    SDFStats,
    TimingEdge,
    TimingGraph,
    VerificationResult,
    batch_endpoint_analysis,
    compute_slack,
    compute_stats,
    critical_path,
    decompose_delay,
    diff,
    generate_report,
    query,
    rank_paths,
    to_dot,
    validate,
    verify_path,
)
from sdf_timing.core import CellBuilder, SDFBuilder, SDFFile, SDFHeader
from sdf_timing.io import annotate_verilog, emit, emit_sdf, parse
from sdf_timing.parser import parse_sdf, parse_sdf_file
from sdf_timing.transform import ConflictStrategy, merge, normalize_delays

__all__ = [
    # core
    "CellBuilder",
    "SDFBuilder",
    "SDFFile",
    "SDFHeader",
    # parser
    "parse_sdf",
    "parse_sdf_file",
    # io
    "annotate_verilog",
    "emit",
    "emit_sdf",
    "parse",
    # analysis
    "DiffEntry",
    "DiffResult",
    "EndpointResult",
    "LintIssue",
    "RankedPath",
    "SDFStats",
    "TimingEdge",
    "TimingGraph",
    "VerificationResult",
    "batch_endpoint_analysis",
    "compute_slack",
    "compute_stats",
    "critical_path",
    "decompose_delay",
    "diff",
    "generate_report",
    "query",
    "rank_paths",
    "to_dot",
    "validate",
    "verify_path",
    # transform
    "ConflictStrategy",
    "merge",
    "normalize_delays",
]
