"""Structural and semantic validation for SDF files."""

from __future__ import annotations

from dataclasses import dataclass

from sdf_timing.core.model import DelayPaths, EntryType, SDFFile, Values


@dataclass
class LintIssue:
    """A single validation issue found in an SDF file.

    Attributes
    ----------
    severity : str
        Either ``"error"`` or ``"warning"``.
    cell_type : str
        The cell type where the issue was found.
    instance : str
        The instance name where the issue was found.
    entry_name : str
        The entry name where the issue was found.
    message : str
        Human-readable description of the issue.
    """

    severity: str
    cell_type: str
    instance: str
    entry_name: str
    message: str


def _check_header(sdf: SDFFile) -> list[LintIssue]:
    """Check the SDF header for missing fields.

    Parameters
    ----------
    sdf : SDFFile
        The SDF file to validate.

    Returns
    -------
    list[LintIssue]
        Header-level issues found.
    """
    if sdf.header.timescale is None:
        return [
            LintIssue(
                severity="warning",
                cell_type="",
                instance="",
                entry_name="",
                message="Missing timescale in header",
            )
        ]
    return []


def _check_empty_cells(sdf: SDFFile) -> list[LintIssue]:
    """Check whether the SDF file has an empty cells dictionary.

    Parameters
    ----------
    sdf : SDFFile
        The SDF file to validate.

    Returns
    -------
    list[LintIssue]
        A single-element list if cells is empty, otherwise empty.
    """
    if not sdf.cells:
        return [
            LintIssue(
                severity="warning",
                cell_type="",
                instance="",
                entry_name="",
                message="SDF file contains no cells",
            )
        ]
    return []


def _check_delay_paths_values(
    delay_paths: DelayPaths,
    cell_type: str,
    instance: str,
    entry_name: str,
) -> list[LintIssue]:
    """Check delay path fields for all-None Values triples.

    Parameters
    ----------
    delay_paths : DelayPaths
        The delay paths to inspect.
    cell_type : str
        The cell type for issue reporting.
    instance : str
        The instance name for issue reporting.
    entry_name : str
        The entry name for issue reporting.

    Returns
    -------
    list[LintIssue]
        Warnings for any delay path field that is a Values with all-None
        components.
    """
    issues: list[LintIssue] = []
    for field_name in DelayPaths._FIELD_NAMES:  # noqa: SLF001
        values: Values | None = getattr(delay_paths, field_name)
        if (
            values is not None
            and values.min is None
            and values.avg is None
            and values.max is None
        ):
            issues.append(
                LintIssue(
                    severity="warning",
                    cell_type=cell_type,
                    instance=instance,
                    entry_name=entry_name,
                    message=(
                        f"Delay path '{field_name}' has all-None values "
                        f"(min=None, avg=None, max=None)"
                    ),
                )
            )
    return issues


def _check_cross_cell_type_instances(sdf: SDFFile) -> list[LintIssue]:
    """Detect instances that appear under multiple cell types.

    Parameters
    ----------
    sdf : SDFFile
        The SDF file to validate.

    Returns
    -------
    list[LintIssue]
        Warnings for instances found under more than one cell type.
    """
    issues: list[LintIssue] = []
    instance_to_cell_types: dict[str, list[str]] = {}

    for cell_type, instances in sdf.cells.items():
        for instance in instances:
            instance_to_cell_types.setdefault(instance, []).append(cell_type)

    for instance, cell_types in instance_to_cell_types.items():
        if len(cell_types) > 1:
            cell_types_str = ", ".join(sorted(cell_types))
            issues.append(
                LintIssue(
                    severity="warning",
                    cell_type="",
                    instance=instance,
                    entry_name="",
                    message=(
                        f"Instance '{instance}' appears under multiple "
                        f"cell types: {cell_types_str}"
                    ),
                )
            )
    return issues


def validate(sdf: SDFFile) -> list[LintIssue]:
    """Check an SDF file for structural and semantic issues.

    Parameters
    ----------
    sdf : SDFFile
        The SDF file to validate.

    Returns
    -------
    list[LintIssue]
        All issues found, ordered by severity (errors first).

    Examples
    --------
    >>> from sdf_timing.core.builder import SDFBuilder
    >>> from sdf_timing.analysis.validate import validate
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
    >>> issues = validate(sdf)
    >>> len(issues)
    0

    Missing timescale produces a warning:

    >>> sdf_no_ts = (
    ...     SDFBuilder()
    ...     .add_cell("BUF", "b0")
    ...         .add_iopath("A", "Y", {
    ...             "nominal": {"min": 1.0, "avg": 2.0, "max": 3.0},
    ...         })
    ...         .done()
    ...     .build()
    ... )
    >>> issues = validate(sdf_no_ts)
    >>> issues[0].message
    'Missing timescale in header'
    """
    issues: list[LintIssue] = []

    # 1. Header checks
    issues.extend(_check_header(sdf))

    # 2. Empty cells check
    issues.extend(_check_empty_cells(sdf))

    # 3-5. Per-entry checks
    for cell_type, instances in sdf.cells.items():
        for instance, entries in instances.items():
            for entry_name, entry in entries.items():
                # Check 3: Entry with None delay_paths
                if entry.delay_paths is None:
                    issues.append(
                        LintIssue(
                            severity="error",
                            cell_type=cell_type,
                            instance=instance,
                            entry_name=entry_name,
                            message="Entry has no delay paths (delay_paths is None)",
                        )
                    )
                    continue

                # Check 4: IOPATH/INTERCONNECT with missing pins
                if entry.type in (EntryType.IOPATH, EntryType.INTERCONNECT):
                    if entry.from_pin is None:
                        issues.append(
                            LintIssue(
                                severity="error",
                                cell_type=cell_type,
                                instance=instance,
                                entry_name=entry_name,
                                message=(
                                    f"{entry.type.value} entry is missing 'from_pin'"
                                ),
                            )
                        )
                    if entry.to_pin is None:
                        issues.append(
                            LintIssue(
                                severity="error",
                                cell_type=cell_type,
                                instance=instance,
                                entry_name=entry_name,
                                message=(
                                    f"{entry.type.value} entry is missing 'to_pin'"
                                ),
                            )
                        )

                # Check 5: Delay paths with all-None Values
                issues.extend(
                    _check_delay_paths_values(
                        entry.delay_paths,
                        cell_type,
                        instance,
                        entry_name,
                    )
                )

    # 6. Cross-cell-type instance reuse
    issues.extend(_check_cross_cell_type_instances(sdf))

    # Sort: errors first, then warnings
    severity_order = {"error": 0, "warning": 1}
    issues.sort(key=lambda issue: severity_order.get(issue.severity, 2))

    return issues
