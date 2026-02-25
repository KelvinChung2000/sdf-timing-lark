"""Compare two SDF files and report differences."""

from dataclasses import dataclass, field

from sdf_toolkit.core.model import DelayPaths, SDFFile, Values
from sdf_toolkit.transform.normalize import normalize_delays

_HEADER_FIELDS: tuple[str, ...] = (
    "sdfversion",
    "design",
    "vendor",
    "program",
    "version",
    "divider",
    "date",
    "voltage",
    "process",
    "temperature",
    "timescale",
)

_VALUES_FIELDS: tuple[str, ...] = ("min", "avg", "max")


@dataclass
class DiffEntry:
    """A single value difference between two SDF files.

    Attributes
    ----------
    cell_type : str
        The cell type name.
    instance : str
        The cell instance name.
    entry_name : str
        The timing entry name within the cell.
    field : str
        The dotted field path, e.g. ``"nominal.min"`` or ``"slow.max"``.
    value_a : float | None
        The value from the first SDF file.
    value_b : float | None
        The value from the second SDF file.
    delta : float | None
        ``value_b - value_a`` when both are present, else None.
    """

    cell_type: str
    instance: str
    entry_name: str
    field: str
    value_a: float | None
    value_b: float | None
    delta: float | None


@dataclass
class DiffResult:
    """Complete comparison result between two SDF files.

    Attributes
    ----------
    only_in_a : list[tuple[str, str, str]]
        Entries present only in the first file, as
        ``(cell_type, instance, entry_name)`` tuples.
    only_in_b : list[tuple[str, str, str]]
        Entries present only in the second file, as
        ``(cell_type, instance, entry_name)`` tuples.
    value_diffs : list[DiffEntry]
        Per-field value differences for entries present in both files.
    header_diffs : dict[str, tuple[str | None, str | None]]
        Header field differences, mapping field name to
        ``(value_in_a, value_in_b)``.
    """

    only_in_a: list[tuple[str, str, str]] = field(default_factory=list)
    only_in_b: list[tuple[str, str, str]] = field(default_factory=list)
    value_diffs: list[DiffEntry] = field(default_factory=list)
    header_diffs: dict[str, tuple[str | None, str | None]] = field(
        default_factory=dict,
    )


def _build_entry_keys(sdf: SDFFile) -> set[tuple[str, str, str]]:
    """Build the set of ``(cell_type, instance, entry_name)`` keys from an SDF file.

    Parameters
    ----------
    sdf : SDFFile
        The SDF file to extract keys from.

    Returns
    -------
    set[tuple[str, str, str]]
        All entry keys present in the file.
    """
    keys: set[tuple[str, str, str]] = set()
    for cell_type, instances in sdf.cells.items():
        for instance, entries in instances.items():
            for entry_name in entries:
                keys.add((cell_type, instance, entry_name))
    return keys


def _compare_values(
    values_a: Values | None,
    values_b: Values | None,
    cell_type: str,
    instance: str,
    entry_name: str,
    field_name: str,
    tolerance: float,
) -> list[DiffEntry]:
    """Compare two Values triples and return diff entries for any differences.

    Parameters
    ----------
    values_a : Values | None
        Values from the first SDF file.
    values_b : Values | None
        Values from the second SDF file.
    cell_type : str
        The cell type name for context.
    instance : str
        The cell instance name for context.
    entry_name : str
        The timing entry name for context.
    field_name : str
        The delay path field name (e.g. ``"nominal"``, ``"slow"``).
    tolerance : float
        Absolute tolerance for floating-point comparison.

    Returns
    -------
    list[DiffEntry]
        A list of diff entries, one per metric that differs.
    """
    diffs: list[DiffEntry] = []

    for metric in _VALUES_FIELDS:
        val_a: float | None = (
            getattr(values_a, metric) if values_a is not None else None
        )
        val_b: float | None = (
            getattr(values_b, metric) if values_b is not None else None
        )

        if val_a is None and val_b is None:
            continue

        delta: float | None = None
        if val_a is not None and val_b is not None:
            delta = val_b - val_a
            if abs(delta) <= tolerance:
                continue

        diffs.append(
            DiffEntry(
                cell_type=cell_type,
                instance=instance,
                entry_name=entry_name,
                field=f"{field_name}.{metric}",
                value_a=val_a,
                value_b=val_b,
                delta=delta,
            ),
        )

    return diffs


def _compare_delay_paths(
    dp_a: DelayPaths | None,
    dp_b: DelayPaths | None,
    cell_type: str,
    instance: str,
    entry_name: str,
    tolerance: float,
) -> list[DiffEntry]:
    """Compare two DelayPaths and return diff entries for all differences.

    Parameters
    ----------
    dp_a : DelayPaths | None
        Delay paths from the first SDF file.
    dp_b : DelayPaths | None
        Delay paths from the second SDF file.
    cell_type : str
        The cell type name for context.
    instance : str
        The cell instance name for context.
    entry_name : str
        The timing entry name for context.
    tolerance : float
        Absolute tolerance for floating-point comparison.

    Returns
    -------
    list[DiffEntry]
        A list of diff entries for each metric that differs.
    """
    diffs: list[DiffEntry] = []

    for field_name in DelayPaths._FIELD_NAMES:  # noqa: SLF001
        values_a: Values | None = (
            getattr(dp_a, field_name) if dp_a is not None else None
        )
        values_b: Values | None = (
            getattr(dp_b, field_name) if dp_b is not None else None
        )
        diffs.extend(
            _compare_values(
                values_a,
                values_b,
                cell_type,
                instance,
                entry_name,
                field_name,
                tolerance,
            ),
        )

    return diffs


def diff(
    a: SDFFile,
    b: SDFFile,
    tolerance: float = 1e-9,
    normalize_first: bool = False,
    target_timescale: str = "1ps",
) -> DiffResult:
    """Compare two SDF files and return a structured diff result.

    Parameters
    ----------
    a : SDFFile
        The first (reference) SDF file.
    b : SDFFile
        The second (comparison) SDF file.
    tolerance : float, optional
        Absolute tolerance for floating-point value comparison, by default
        1e-9.
    normalize_first : bool, optional
        If True, normalize both files to ``target_timescale`` before
        comparing, by default False.
    target_timescale : str, optional
        The timescale to normalize to when ``normalize_first`` is True,
        by default ``"1ps"``.

    Returns
    -------
    DiffResult
        The complete comparison result including header diffs, entries
        only in one file, and per-field value differences.

    Examples
    --------
    >>> from sdf_toolkit.core.builder import SDFBuilder
    >>> from sdf_toolkit.analysis.diff import diff
    >>> a = (
    ...     SDFBuilder()
    ...     .set_header(timescale="1ps")
    ...     .add_cell("BUF", "b0")
    ...         .add_iopath("A", "Y", {
    ...             "nominal": {"min": 1.0, "avg": 2.0, "max": 3.0},
    ...         })
    ...     .build()
    ... )
    >>> b = (
    ...     SDFBuilder()
    ...     .set_header(timescale="1ps")
    ...     .add_cell("BUF", "b0")
    ...         .add_iopath("A", "Y", {
    ...             "nominal": {"min": 1.0, "avg": 2.0, "max": 5.0},
    ...         })
    ...     .add_cell("INV", "i0")
    ...         .add_iopath("A", "Y", {
    ...             "nominal": {"min": 1.0, "avg": 2.0, "max": 3.0},
    ...         })
    ...     .build()
    ... )
    >>> result = diff(a, b)
    >>> len(result.only_in_b)
    1
    >>> result.value_diffs[0].field
    'nominal.max'
    >>> result.value_diffs[0].delta
    2.0
    """
    if normalize_first:
        a = normalize_delays(a, target_timescale)
        b = normalize_delays(b, target_timescale)

    result = DiffResult()

    # Compare headers
    for hdr_field in _HEADER_FIELDS:
        val_a: str | None = getattr(a.header, hdr_field)
        val_b: str | None = getattr(b.header, hdr_field)
        if val_a != val_b:
            result.header_diffs[hdr_field] = (val_a, val_b)

    # Build entry key sets
    keys_a = _build_entry_keys(a)
    keys_b = _build_entry_keys(b)

    result.only_in_a = sorted(keys_a - keys_b)
    result.only_in_b = sorted(keys_b - keys_a)

    # Compare shared entries
    common_keys = keys_a & keys_b
    for cell_type, instance, entry_name in sorted(common_keys):
        entry_a = a.cells[cell_type][instance][entry_name]
        entry_b = b.cells[cell_type][instance][entry_name]

        result.value_diffs.extend(
            _compare_delay_paths(
                entry_a.delay_paths,
                entry_b.delay_paths,
                cell_type,
                instance,
                entry_name,
                tolerance,
            ),
        )

    return result
