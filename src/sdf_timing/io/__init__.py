"""I/O modules for writing, annotating, and emitting SDF timing files.

Parsing has moved to :mod:`sdf_timing.parser`.  The ``parse_sdf`` and
``parse_sdf_file`` names are re-exported here for backward compatibility.
"""

from sdf_timing.io.annotate import annotate_verilog
from sdf_timing.io.sdfparse import emit, parse
from sdf_timing.io.writer import emit_sdf
from sdf_timing.parser import parse_sdf, parse_sdf_file

__all__ = [
    # annotate
    "annotate_verilog",
    # parser (re-exported for backward compatibility)
    "parse_sdf",
    "parse_sdf_file",
    # sdfparse (legacy API)
    "emit",
    "parse",
    # writer
    "emit_sdf",
]
