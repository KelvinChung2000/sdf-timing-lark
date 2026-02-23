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


from pathlib import Path

from sdf_timing import sdfparse

__path__ = Path(__file__).parent

datafiles_path = __path__ / "data"
goldenfiles_path = __path__ / "data" / "golden"
parsed_sdfs = list()
generated_sdfs = list()


def test_parse() -> None:
    files = sorted(datafiles_path.glob("*.sdf"))
    for f in files:
        with f.open("r") as sdffile:
            parsed_sdfs.append(sdfparse.parse(sdffile.read()))


def test_emit() -> None:
    for s in parsed_sdfs:
        generated_sdfs.append(sdfparse.emit(s))


def test_output_stability() -> None:
    """ Checks if the generated SDF are identical with golden files"""

    parsed_sdfs_check = list()
    # read the golden files
    files = sorted(goldenfiles_path.glob("*.sdf"))
    for f in files:
        with f.open("r") as sdffile:
            parsed_sdfs_check.append(sdffile.read())

    for s0, s1 in zip(parsed_sdfs, parsed_sdfs_check, strict=False):
        sdf0 = sdfparse.emit(s0)
        assert sdf0 == s1


def test_parse_generated() -> None:
    for s in generated_sdfs:
        sdfparse.parse(s)
