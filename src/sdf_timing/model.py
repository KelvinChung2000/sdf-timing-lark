from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union


@dataclass
class SDFHeader:
    sdfversion: Optional[str] = None
    design: Optional[str] = None
    vendor: Optional[str] = None
    program: Optional[str] = None
    version: Optional[str] = None
    divider: Optional[str] = None
    date: Optional[str] = None
    voltage: Optional[str] = None
    process: Optional[str] = None
    temperature: Optional[str] = None
    timescale: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        return getattr(self, key, None) is not None
    
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)
    
    def keys(self):
        return self.to_dict().keys()
        
    def values(self):
        return self.to_dict().values()

    def items(self):
        return self.to_dict().items()


@dataclass
class Values:
    min: Optional[float] = None
    avg: Optional[float] = None
    max: Optional[float] = None

    def to_dict(self) -> Dict[str, Optional[float]]:
        return {"min": self.min, "avg": self.avg, "max": self.max}


@dataclass
class DelayPaths:
    nominal: Optional[Values] = None
    fast: Optional[Values] = None
    slow: Optional[Values] = None
    # For constraints like setuphold
    setup: Optional[Values] = None
    hold: Optional[Values] = None
    # For path constraints
    rise: Optional[Values] = None
    fall: Optional[Values] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        if self.nominal:
            d["nominal"] = self.nominal.to_dict()
        if self.fast:
            d["fast"] = self.fast.to_dict()
        if self.slow:
            d["slow"] = self.slow.to_dict()
        if self.setup:
            d["setup"] = self.setup.to_dict()
        if self.hold:
            d["hold"] = self.hold.to_dict()
        if self.rise:
            d["rise"] = self.rise.to_dict()
        if self.fall:
            d["fall"] = self.fall.to_dict()
        return d

    def __contains__(self, key: str) -> bool:
        return getattr(self, key, None) is not None

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


@dataclass
class BaseEntry:
    name: str = ""
    type: str = ""
    from_pin: Optional[str] = None
    to_pin: Optional[str] = None
    from_pin_edge: Optional[str] = None
    to_pin_edge: Optional[str] = None
    delay_paths: Optional[Dict[str, Any]] = None  # Using Dict to match original structure
    cond_equation: Optional[str] = None
    is_timing_check: bool = False
    is_timing_env: bool = False
    is_absolute: bool = False
    is_incremental: bool = False
    is_cond: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# Delays
@dataclass
class Port(BaseEntry):
    def __post_init__(self):
        self.type = "port"

@dataclass
class Interconnect(BaseEntry):
    def __post_init__(self):
        self.type = "interconnect"

@dataclass
class Iopath(BaseEntry):
    def __post_init__(self):
        self.type = "iopath"

@dataclass
class Device(BaseEntry):
    def __post_init__(self):
        self.type = "device"

# Timing Checks
@dataclass
class TimingCheck(BaseEntry):
    is_timing_check: bool = True

@dataclass
class Setup(TimingCheck):
    def __post_init__(self):
        self.type = "setup"

@dataclass
class Hold(TimingCheck):
    def __post_init__(self):
        self.type = "hold"

@dataclass
class Removal(TimingCheck):
    def __post_init__(self):
        self.type = "removal"

@dataclass
class Recovery(TimingCheck):
    def __post_init__(self):
        self.type = "recovery"

@dataclass
class Width(TimingCheck):
    def __post_init__(self):
        self.type = "width"

@dataclass
class SetupHold(TimingCheck):
    def __post_init__(self):
        self.type = "setuphold"

# Constraints
@dataclass
class PathConstraint(BaseEntry):
    is_timing_env: bool = True
    def __post_init__(self):
        self.type = "pathconstraint"


@dataclass
class SDFFile:
    header: SDFHeader = field(default_factory=SDFHeader)
    cells: Dict[str, Dict[str, Dict[str, BaseEntry]]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        cells_dict = {}
        for cell_type, instances in self.cells.items():
            cells_dict[cell_type] = {}
            for instance_name, entries in instances.items():
                cells_dict[cell_type][instance_name] = {}
                for entry_name, entry in entries.items():
                    cells_dict[cell_type][instance_name][entry_name] = entry.to_dict()
        
        return {
            "header": self.header.to_dict(),
            "cells": cells_dict
        }

    def __getitem__(self, key: str) -> Any:
        if key == "header":
            return self.header
        if key == "cells":
            return self.cells
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return key in ["header", "cells"]
    
    def get(self, key: str, default: Any = None) -> Any:
        if key == "header": return self.header
        if key == "cells": return self.cells
        return default
