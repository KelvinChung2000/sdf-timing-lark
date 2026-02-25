"""Core data models and utility functions for SDF timing."""

from sdf_timing.core.builder import CellBuilder, SDFBuilder
from sdf_timing.core.model import (
    BaseEntry,
    CellsDict,
    DelayPaths,
    Device,
    EdgeType,
    EntryType,
    Hold,
    Interconnect,
    Iopath,
    PathConstraint,
    Port,
    PortSpec,
    Recovery,
    Removal,
    SDFFile,
    SDFFileValue,
    SDFHeader,
    Setup,
    SetupHold,
    TimingCheck,
    TimingPortSpec,
    Values,
    Width,
)
from sdf_timing.core.utils import get_scale_fs, get_scale_seconds, store_entry

__all__ = [
    # model -- data classes and type aliases
    "BaseEntry",
    "CellsDict",
    "DelayPaths",
    "Device",
    "EdgeType",
    "EntryType",
    "Hold",
    "Interconnect",
    "Iopath",
    "PathConstraint",
    "Port",
    "PortSpec",
    "Recovery",
    "Removal",
    "SDFFile",
    "SDFFileValue",
    "SDFHeader",
    "Setup",
    "SetupHold",
    "TimingCheck",
    "TimingPortSpec",
    "Values",
    "Width",
    # builder
    "CellBuilder",
    "SDFBuilder",
    # utils
    "get_scale_fs",
    "get_scale_seconds",
    "store_entry",
]
