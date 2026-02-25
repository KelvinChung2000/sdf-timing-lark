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

"""Utility functions for SDF entry storage and timescale conversion."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sdf_timing.core.model import BaseEntry


def store_entry(cell_dict: dict[str, BaseEntry], entry: BaseEntry) -> str:
    """Store entry in cell dict, appending _N suffix on name collision.

    The first entry keeps its base name. Subsequent collisions get _1, _2, etc.
    """
    base_name = entry.name
    key = base_name
    if key in cell_dict:
        counter = 1
        while f"{base_name}_{counter}" in cell_dict:
            counter += 1
        key = f"{base_name}_{counter}"
        entry.name = key
    cell_dict[key] = entry
    return key


def get_scale_fs(timescale: str) -> int:
    """Convert sdf timescale to scale factor to femtoseconds as int.

    >>> get_scale_fs('1.0 fs')
    1

    >>> get_scale_fs('1ps')
    1000

    >>> get_scale_fs('10 ns')
    10000000

    >>> get_scale_fs('10.0 us')
    10000000000

    >>> get_scale_fs('100.0ms')
    100000000000000

    >>> get_scale_fs('100 s')
    100000000000000000

    >>> try:
    ...     get_scale_fs('2s')
    ... except ValueError as e:
    ...     print(e)
    Invalid SDF timescale 2s

    """
    mm = re.match(r"(10{0,2})(\.0)? *([munpf]?s)", timescale)
    sc_lut = {
        "s": 1e15,
        "ms": 1e12,
        "us": 1e9,
        "ns": 1e6,
        "ps": 1e3,
        "fs": 1,
    }
    if mm is None:
        msg = f"Invalid SDF timescale {timescale}"
        raise ValueError(msg)

    base, _, sc = mm.groups()
    return int(base) * int(sc_lut[sc])


def get_scale_seconds(timescale: str) -> float:
    """Convert sdf timescale to scale factor to floating point seconds.

    >>> get_scale_seconds('1.0 fs')
    1e-15

    >>> get_scale_seconds('1ps')
    1e-12

    >>> get_scale_seconds('10 ns')
    1e-08

    >>> get_scale_seconds('10.0 us')
    1e-05

    >>> get_scale_seconds('100.0ms')
    0.1

    >>> round(get_scale_seconds('100 s'), 6)
    100.0
    """
    return 1e-15 * get_scale_fs(timescale)
