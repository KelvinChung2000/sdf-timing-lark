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


from conftest import DATA_DIR

from sdf_timing.core.model import SDFFile
from sdf_timing.io import sdfparse

GOLDEN_DIR = DATA_DIR / "golden"


def _parse_all_sdfs() -> list[SDFFile]:
    """Parse all SDF files in the data directory."""
    files = sorted(DATA_DIR.glob("*.sdf"))
    return [sdfparse.parse(f.read_text()) for f in files]


def test_parse() -> None:
    parsed_sdfs = _parse_all_sdfs()
    assert len(parsed_sdfs) > 0


def test_emit() -> None:
    parsed_sdfs = _parse_all_sdfs()
    generated_sdfs = [sdfparse.emit(s) for s in parsed_sdfs]
    assert len(generated_sdfs) == len(parsed_sdfs)


def test_output_stability() -> None:
    """Checks if the generated SDF are identical with golden files."""
    parsed_sdfs = _parse_all_sdfs()
    golden_files = sorted(GOLDEN_DIR.glob("*.sdf"))
    golden_contents = [f.read_text() for f in golden_files]

    for parsed, golden in zip(parsed_sdfs, golden_contents, strict=True):
        assert sdfparse.emit(parsed) == golden


def test_parse_generated() -> None:
    parsed_sdfs = _parse_all_sdfs()
    generated_sdfs = [sdfparse.emit(s) for s in parsed_sdfs]
    for s in generated_sdfs:
        sdfparse.parse(s)
