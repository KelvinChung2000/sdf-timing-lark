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

"""Utility functions for creating SDF timing entries."""

from __future__ import annotations

import re

from sdf_timing.model import (
    BaseEntry,
    DelayPaths,
    Device,
    EntryType,
    Hold,
    Interconnect,
    Iopath,
    PathConstraint,
    Port,
    PortSpec,
    Recovery,
    Removal,
    Setup,
    SetupHold,
    TimingCheck,
    TimingPortSpec,
    Width,
)


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
    ... except AssertionError as e:
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
    assert mm is not None, f"Invalid SDF timescale {timescale}"

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


def add_port(portname: PortSpec, paths: DelayPaths) -> Port:
    """Create a Port entry."""
    port_name = portname["port"]
    return Port(
        name=f"port_{port_name}",
        from_pin=port_name,
        to_pin=port_name,
        delay_paths=paths,
    )


def add_interconnect(
    pfrom: PortSpec,
    pto: PortSpec,
    paths: DelayPaths,
) -> Interconnect:
    """Create an Interconnect entry."""
    from_port = pfrom["port"]
    to_port = pto["port"]
    return Interconnect(
        name=f"interconnect_{from_port}_{to_port}",
        from_pin=from_port,
        to_pin=to_port,
        from_pin_edge=pfrom["port_edge"],
        to_pin_edge=pto["port_edge"],
        delay_paths=paths,
    )


def add_iopath(
    pfrom: PortSpec,
    pto: PortSpec,
    paths: DelayPaths,
) -> Iopath:
    """Create an Iopath entry."""
    from_port = pfrom["port"]
    to_port = pto["port"]
    return Iopath(
        name=f"iopath_{from_port}_{to_port}",
        from_pin=from_port,
        to_pin=to_port,
        from_pin_edge=pfrom["port_edge"],
        to_pin_edge=pto["port_edge"],
        delay_paths=paths,
    )


def add_device(port: PortSpec, paths: DelayPaths) -> Device:
    """Create a Device entry."""
    port_name = port["port"]
    return Device(
        name=f"device_{port_name}",
        from_pin=port_name,
        to_pin=port_name,
        delay_paths=paths,
    )


def add_tcheck(
    check_type: EntryType,
    pto: TimingPortSpec,
    pfrom: TimingPortSpec,
    paths: DelayPaths,
) -> TimingCheck:
    """Create a timing check entry."""
    from_port = pfrom["port"]
    to_port = pto["port"]
    name = f"{check_type}_{from_port}_{to_port}"
    is_cond = pfrom["cond"]
    cond_equation = pfrom["cond_equation"]

    check_classes: dict[EntryType, type[TimingCheck]] = {
        EntryType.SETUP: Setup,
        EntryType.HOLD: Hold,
        EntryType.REMOVAL: Removal,
        EntryType.RECOVERY: Recovery,
        EntryType.WIDTH: Width,
        EntryType.SETUPHOLD: SetupHold,
    }

    cls = check_classes.get(check_type)
    if cls is None:
        raise ValueError(f"Unknown timing check type: {check_type}")

    return cls(
        name=name,
        is_timing_check=True,
        is_cond=is_cond,
        cond_equation=cond_equation,
        from_pin=from_port,
        to_pin=to_port,
        from_pin_edge=pfrom["port_edge"],
        to_pin_edge=pto["port_edge"],
        delay_paths=paths,
    )


def add_constraint(
    constraint_type: EntryType,
    pto: PortSpec,
    pfrom: PortSpec,
    paths: DelayPaths,
) -> PathConstraint:
    """Create a constraint entry."""
    from_port = pfrom["port"]
    to_port = pto["port"]
    name = f"{constraint_type}_{from_port}_{to_port}"

    if constraint_type != EntryType.PATHCONSTRAINT:
        raise ValueError(f"Unknown constraint type: {constraint_type}")

    return PathConstraint(
        name=name,
        is_timing_env=True,
        from_pin=from_port,
        to_pin=to_port,
        from_pin_edge=pfrom["port_edge"],
        to_pin_edge=pto["port_edge"],
        delay_paths=paths,
    )
