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

import re
from typing import Optional, Dict, Any, Union

from .model import (
    Port, Interconnect, Iopath, Device,
    Setup, Hold, Removal, Recovery, Width, SetupHold,
    PathConstraint, BaseEntry
)


def get_scale_fs(timescale: str) -> int:
    """Convert sdf timescale to scale factor to femtoseconds as int

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
    """Convert sdf timescale to scale factor to floating point seconds

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


def add_port(portname: dict, paths: Any) -> Port:
    name = "port_" + portname["port"]
    return Port(
        name=name,
        from_pin=portname["port"],
        to_pin=portname["port"],
        delay_paths=paths,
    )


def add_interconnect(pfrom: dict, pto: dict, paths: Any) -> Interconnect:
    name = "interconnect_"
    name += pfrom["port"] + "_" + pto["port"]
    return Interconnect(
        name=name,
        from_pin=pfrom["port"],
        to_pin=pto["port"],
        from_pin_edge=pfrom["port_edge"],
        to_pin_edge=pto["port_edge"],
        delay_paths=paths,
    )


def add_iopath(pfrom: dict, pto: dict, paths: Any) -> Iopath:
    name = "iopath_"
    name += pfrom["port"] + "_" + pto["port"]
    return Iopath(
        name=name,
        from_pin=pfrom["port"],
        to_pin=pto["port"],
        from_pin_edge=pfrom["port_edge"],
        to_pin_edge=pto["port_edge"],
        delay_paths=paths,
    )


def add_device(port: dict, paths: Any) -> Device:
    name = "device_"
    name += port["port"]
    return Device(
        name=name,
        from_pin=port["port"],
        to_pin=port["port"],
        delay_paths=paths,
    )


def add_tcheck(type: str, pto: dict, pfrom: dict, paths: Any) -> BaseEntry:
    name = type + "_"
    name += pfrom["port"] + "_" + pto["port"]
    
    kwargs = {
        "name": name,
        "is_timing_check": True,
        "is_cond": pfrom.get("cond", False),
        "cond_equation": pfrom.get("cond_equation"),
        "from_pin": pfrom["port"],
        "to_pin": pto["port"],
        "from_pin_edge": pfrom["port_edge"],
        "to_pin_edge": pto["port_edge"],
        "delay_paths": paths,
    }

    if type == "setup":
        return Setup(**kwargs)
    elif type == "hold":
        return Hold(**kwargs)
    elif type == "removal":
        return Removal(**kwargs)
    elif type == "recovery":
        return Recovery(**kwargs)
    elif type == "width":
        # width check usually has only one port, but here it's reused
        # items[1] is ported to pto and pfrom in transformer
        return Width(**kwargs)
    elif type == "setuphold":
        return SetupHold(**kwargs)
    else:
        # Fallback
        entry = BaseEntry(**kwargs)
        entry.type = type
        return entry


def add_constraint(type: str, pto: dict, pfrom: dict, paths: Any) -> BaseEntry:
    name = type + "_"
    name += pfrom["port"] + "_" + pto["port"]
    
    kwargs = {
        "name": name,
        "is_timing_env": True,
        "from_pin": pfrom["port"],
        "to_pin": pto["port"],
        "from_pin_edge": pfrom["port_edge"],
        "to_pin_edge": pto["port_edge"],
        "delay_paths": paths,
    }
    
    if type == "pathconstraint":
        return PathConstraint(**kwargs)
    else:
        entry = BaseEntry(**kwargs)
        entry.type = type
        return entry
