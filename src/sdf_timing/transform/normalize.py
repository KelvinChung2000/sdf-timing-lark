"""Timescale-aware delay normalization for SDF files."""

from __future__ import annotations

import copy

from sdf_timing.core.model import DelayPaths, SDFFile, Values
from sdf_timing.core.utils import get_scale_fs


def normalize_delays(sdf: SDFFile, target_timescale: str) -> SDFFile:
    """Return a deep copy of *sdf* with all delays scaled to *target_timescale*.

    Parameters
    ----------
    sdf : SDFFile
        The original SDF file.
    target_timescale : str
        The target timescale string (e.g. ``"1ns"``).

    Returns
    -------
    SDFFile
        A new SDFFile with delays scaled and header.timescale updated.

    Raises
    ------
    ValueError
        If the source SDF has no timescale set in the header.

    Examples
    --------
    >>> from sdf_timing.core.builder import SDFBuilder
    >>> from sdf_timing.transform.normalize import normalize_delays
    >>> sdf = (
    ...     SDFBuilder()
    ...     .set_header(timescale="1ps")
    ...     .add_cell("BUF", "b0")
    ...         .add_iopath("A", "Y", {
    ...             "nominal": {"min": 1.0, "avg": 2.0, "max": 3.0},
    ...         })
    ...         .done()
    ...     .build()
    ... )
    >>> result = normalize_delays(sdf, "1ns")
    >>> result.header.timescale
    '1ns'
    >>> result.cells["BUF"]["b0"]["iopath_A_Y"].delay_paths.nominal.max
    0.003
    """
    if sdf.header.timescale is None:
        msg = "Source SDF has no timescale set in header"
        raise ValueError(msg)

    source_fs = get_scale_fs(sdf.header.timescale)
    target_fs = get_scale_fs(target_timescale)
    ratio = source_fs / target_fs

    result = copy.deepcopy(sdf)
    result.header.timescale = target_timescale

    for instances in result.cells.values():
        for entries in instances.values():
            for entry in entries.values():
                _scale_delay_paths(entry.delay_paths, ratio)

    return result


def _scale_delay_paths(
    delay_paths: DelayPaths | None,
    ratio: float,
) -> None:
    """Scale all non-None fields of *delay_paths* in place by *ratio*.

    Parameters
    ----------
    delay_paths : DelayPaths | None
        The delay paths to scale. If None, this is a no-op.
    ratio : float
        The multiplicative scaling factor.
    """
    if delay_paths is None:
        return

    for field_name in DelayPaths._FIELD_NAMES:  # noqa: SLF001
        values: Values | None = getattr(delay_paths, field_name)
        if values is not None:
            setattr(
                delay_paths,
                field_name,
                values._map_fields(lambda v: v * ratio),  # noqa: SLF001
            )
