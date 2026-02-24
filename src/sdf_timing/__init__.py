"""sdf_timing -- parse and emit Standard Delay Format (SDF) timing files."""

from sdf_timing.annotate import annotate_verilog
from sdf_timing.export import to_dot
from sdf_timing.model import SDFFile, SDFHeader
from sdf_timing.pathgraph import (
    RankedPath,
    TimingEdge,
    TimingGraph,
    VerificationResult,
    compute_slack,
    critical_path,
    decompose_delay,
    rank_paths,
    verify_path,
)
from sdf_timing.sdf_lark_parser import parse_sdf, parse_sdf_file
from sdf_timing.sdfparse import emit, parse

__all__ = [
    "annotate_verilog",
    "RankedPath",
    "SDFFile",
    "SDFHeader",
    "TimingEdge",
    "TimingGraph",
    "VerificationResult",
    "compute_slack",
    "critical_path",
    "decompose_delay",
    "emit",
    "parse",
    "parse_sdf",
    "parse_sdf_file",
    "rank_paths",
    "to_dot",
    "verify_path",
]
