from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from collections.abc import ItemsView, KeysView, ValuesView


class EntryType(StrEnum):
    """Types of SDF timing entries."""

    PORT = "port"
    INTERCONNECT = "interconnect"
    IOPATH = "iopath"
    DEVICE = "device"
    SETUP = "setup"
    HOLD = "hold"
    REMOVAL = "removal"
    RECOVERY = "recovery"
    WIDTH = "width"
    SETUPHOLD = "setuphold"
    PATHCONSTRAINT = "pathconstraint"


class EdgeType(StrEnum):
    """Port edge types in SDF timing specifications."""

    POSEDGE = "posedge"
    NEGEDGE = "negedge"


class PortSpec(TypedDict):
    """Port specification with name and optional edge."""

    port: str
    port_edge: EdgeType | None


class TimingPortSpec(TypedDict):
    """Port specification for timing checks, with condition info."""

    port: str
    port_edge: EdgeType | None
    cond: bool
    cond_equation: str | None


@dataclass
class SDFHeader:
    sdfversion: str | None = None
    design: str | None = None
    vendor: str | None = None
    program: str | None = None
    version: str | None = None
    divider: str | None = None
    date: str | None = None
    voltage: str | None = None
    process: str | None = None
    temperature: str | None = None
    timescale: str | None = None

    def to_dict(self) -> dict[str, str]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def __getitem__(self, key: str) -> str | None:
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        return getattr(self, key, None) is not None

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return the header field *key*, falling back to *default* via getattr."""
        return getattr(self, key, default)

    def keys(self) -> KeysView[str]:
        return self.to_dict().keys()

    def values(self) -> ValuesView[str]:
        return self.to_dict().values()

    def items(self) -> ItemsView[str, str]:
        return self.to_dict().items()


@dataclass
class Values:
    min: float | None = None
    avg: float | None = None
    max: float | None = None

    def to_dict(self) -> dict[str, float | None]:
        return {"min": self.min, "avg": self.avg, "max": self.max}


@dataclass
class DelayPaths:
    nominal: Values | None = None
    fast: Values | None = None
    slow: Values | None = None
    # For constraints like setuphold
    setup: Values | None = None
    hold: Values | None = None
    # For path constraints
    rise: Values | None = None
    fall: Values | None = None

    def to_dict(self) -> dict[str, dict[str, float | None]]:
        return {
            name: val.to_dict()
            for name in ("nominal", "fast", "slow", "setup", "hold", "rise", "fall")
            if (val := getattr(self, name)) is not None
        }

    def __contains__(self, key: str) -> bool:
        return getattr(self, key, None) is not None

    def __getitem__(self, key: str) -> Values | None:
        return getattr(self, key)


@dataclass
class BaseEntry:
    name: str = ""
    type: EntryType = EntryType.IOPATH
    from_pin: str | None = None
    to_pin: str | None = None
    from_pin_edge: EdgeType | None = None
    to_pin_edge: EdgeType | None = None
    delay_paths: DelayPaths | None = None
    cond_equation: str | None = None
    is_timing_check: bool = False
    is_timing_env: bool = False
    is_absolute: bool = False
    is_incremental: bool = False
    is_cond: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Delays
@dataclass
class Port(BaseEntry):
    def __post_init__(self) -> None:
        self.type = EntryType.PORT


@dataclass
class Interconnect(BaseEntry):
    def __post_init__(self) -> None:
        self.type = EntryType.INTERCONNECT


@dataclass
class Iopath(BaseEntry):
    def __post_init__(self) -> None:
        self.type = EntryType.IOPATH


@dataclass
class Device(BaseEntry):
    def __post_init__(self) -> None:
        self.type = EntryType.DEVICE


# Timing Checks
@dataclass
class TimingCheck(BaseEntry):
    is_timing_check: bool = True


@dataclass
class Setup(TimingCheck):
    def __post_init__(self) -> None:
        self.type = EntryType.SETUP


@dataclass
class Hold(TimingCheck):
    def __post_init__(self) -> None:
        self.type = EntryType.HOLD


@dataclass
class Removal(TimingCheck):
    def __post_init__(self) -> None:
        self.type = EntryType.REMOVAL


@dataclass
class Recovery(TimingCheck):
    def __post_init__(self) -> None:
        self.type = EntryType.RECOVERY


@dataclass
class Width(TimingCheck):
    def __post_init__(self) -> None:
        self.type = EntryType.WIDTH


@dataclass
class SetupHold(TimingCheck):
    def __post_init__(self) -> None:
        self.type = EntryType.SETUPHOLD


# Constraints
@dataclass
class PathConstraint(BaseEntry):
    is_timing_env: bool = True

    def __post_init__(self) -> None:
        self.type = EntryType.PATHCONSTRAINT


# Type alias for the cells dictionary structure
CellsDict = dict[str, dict[str, dict[str, BaseEntry]]]

# Type for SDFFile.get() and __getitem__ return values
SDFFileValue = SDFHeader | CellsDict


@dataclass
class SDFFile:
    header: SDFHeader = field(default_factory=SDFHeader)
    cells: CellsDict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cells_dict: dict[str, dict[str, dict[str, Any]]] = {}
        for cell_type, instances in self.cells.items():
            cells_dict[cell_type] = {}
            for instance_name, entries in instances.items():
                cells_dict[cell_type][instance_name] = {}
                for entry_name, entry in entries.items():
                    cells_dict[cell_type][instance_name][entry_name] = entry.to_dict()

        return {"header": self.header.to_dict(), "cells": cells_dict}

    def __getitem__(self, key: str) -> SDFFileValue:
        if key == "header":
            return self.header
        if key == "cells":
            return self.cells
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return key in ("header", "cells")

    def get(self, key: str, default: SDFFileValue | None = None) -> SDFFileValue | None:
        if key == "header":
            return self.header
        if key == "cells":
            return self.cells
        return default
