#!/usr/bin/env python3
#
# Copyright 2020-2022 F4PGA Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
"""Public API for parsing and emitting SDF timing files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from sdf_timing import sdfwrite
from sdf_timing.sdf_lark_parser import parse_sdf

if TYPE_CHECKING:
    from sdf_timing.model import SDFFile


def emit(input: SDFFile, timescale: str = "1ps") -> str:  # noqa: A002
    """Emit SDF content from a parsed timing data structure."""
    return sdfwrite.emit_sdf(input, timescale, header=input.header)


def parse(input: str) -> SDFFile:  # noqa: A002
    """Parse SDF input text and return an SDFFile."""
    return parse_sdf(input)


def main() -> None:
    """Run the command line SDF parser."""
    if len(sys.argv) != 2:
        print("Usage: sdf_timing_parse <sdf_file>")  # noqa: T201
        sys.exit(1)

    sdf_file = sys.argv[1]

    try:
        content = Path(sdf_file).read_text()
        result = parse(content)
        print(json.dumps(result.to_dict(), indent=2))  # noqa: T201
    except Exception as e:  # noqa: BLE001
        print(f"Error parsing SDF file: {e}")  # noqa: T201
        sys.exit(1)
