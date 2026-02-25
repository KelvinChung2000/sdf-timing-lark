"""Programmatic builder for constructing SDFFile objects."""

from __future__ import annotations

from sdf_timing.core.model import (
    BaseEntry,
    CellsDict,
    DelayPaths,
    Device,
    Hold,
    Interconnect,
    Iopath,
    Port,
    Recovery,
    Removal,
    SDFFile,
    SDFHeader,
    Setup,
    SetupHold,
    Values,
    Width,
)
from sdf_timing.core.utils import store_entry


def _build_delay_paths(
    delays: dict[str, dict[str, float | None]],
) -> DelayPaths:
    """Convert a nested delays dict into a DelayPaths dataclass.

    Parameters
    ----------
    delays : dict[str, dict[str, float | None]]
        Mapping of delay field names (e.g. "nominal", "fast", "slow") to
        dicts with keys "min", "avg", "max".

    Returns
    -------
    DelayPaths
        A populated DelayPaths instance.
    """
    return DelayPaths(
        **{
            name: Values(**delays[name])
            for name in DelayPaths._FIELD_NAMES  # noqa: SLF001
            if name in delays
        }
    )


class SDFBuilder:
    """Fluent builder for constructing SDFFile objects from scratch.

    Examples
    --------
    >>> from sdf_timing.core.builder import SDFBuilder
    >>> sdf = (
    ...     SDFBuilder()
    ...     .set_header(sdfversion="3.0", design="top")
    ...     .add_cell("BUF", "buf0")
    ...         .add_iopath("A", "Y", {"nominal": {"min": 1.0, "avg": 2.0, "max": 3.0}})
    ...         .done()
    ...     .build()
    ... )
    >>> sdf.header.sdfversion
    '3.0'
    >>> "BUF" in sdf.cells
    True
    """

    def __init__(self) -> None:
        self._header_kwargs: dict[str, str] = {}
        self._cells: CellsDict = {}

    def set_header(self, **kwargs: str) -> SDFBuilder:
        """Set header fields on the SDF file.

        Parameters
        ----------
        **kwargs : str
            Keyword arguments corresponding to SDFHeader fields
            (e.g. sdfversion, design, vendor, timescale).

        Returns
        -------
        SDFBuilder
            This builder instance for method chaining.
        """
        self._header_kwargs.update(kwargs)
        return self

    def add_cell(self, cell_type: str, instance: str) -> CellBuilder:
        """Start building a cell and return a CellBuilder.

        Parameters
        ----------
        cell_type : str
            The cell type name (e.g. "BUF", "FDRE").
        instance : str
            The cell instance name (e.g. "buf0", "reg0").

        Returns
        -------
        CellBuilder
            A new CellBuilder bound to this SDFBuilder.
        """
        return CellBuilder(self, cell_type, instance)

    def _register_cell(
        self,
        cell_type: str,
        instance: str,
        entries: dict[str, BaseEntry],
    ) -> None:
        """Register a completed cell's entries.

        Called internally by ``CellBuilder.done()``.

        Parameters
        ----------
        cell_type : str
            The cell type name.
        instance : str
            The cell instance name.
        entries : dict[str, BaseEntry]
            The timing entries for this cell instance.
        """
        self._cells.setdefault(cell_type, {})[instance] = entries

    def build(self) -> SDFFile:
        """Build and return the completed SDFFile.

        Returns
        -------
        SDFFile
            The fully constructed SDF file object.
        """
        return SDFFile(
            header=SDFHeader(**self._header_kwargs),
            cells=self._cells,
        )


class CellBuilder:
    """Builder for a single cell's timing entries.

    Provides fluent methods to add delay and timing check entries,
    then call ``done()`` to return to the parent SDFBuilder.
    """

    def __init__(
        self,
        parent: SDFBuilder,
        cell_type: str,
        instance: str,
    ) -> None:
        self._parent = parent
        self._cell_type = cell_type
        self._instance = instance
        self._entries: dict[str, BaseEntry] = {}

    def _add_entry(self, entry: BaseEntry) -> CellBuilder:
        """Store an entry and return self for chaining.

        Parameters
        ----------
        entry : BaseEntry
            The entry to store.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        store_entry(self._entries, entry)
        return self

    def add_iopath(
        self,
        from_pin: str,
        to_pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add an IOPATH delay entry.

        Parameters
        ----------
        from_pin : str
            The input pin name.
        to_pin : str
            The output pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name (nominal, fast, slow, etc.).

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.

        Examples
        --------
        >>> from sdf_timing.core.builder import SDFBuilder
        >>> sdf = (
        ...     SDFBuilder()
        ...     .add_cell("INV", "i0")
        ...         .add_iopath("A", "Y", {
        ...             "nominal": {"min": 0.5, "avg": 1.0, "max": 1.5},
        ...         })
        ...         .done()
        ...     .build()
        ... )
        >>> entry = sdf.cells["INV"]["i0"]["iopath_A_Y"]
        >>> entry.delay_paths.nominal.max
        1.5
        """
        return self._add_entry(
            Iopath(
                name=f"iopath_{from_pin}_{to_pin}",
                from_pin=from_pin,
                to_pin=to_pin,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_interconnect(
        self,
        from_pin: str,
        to_pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add an interconnect delay entry.

        Parameters
        ----------
        from_pin : str
            The source pin name.
        to_pin : str
            The destination pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            Interconnect(
                name=f"interconnect_{from_pin}_{to_pin}",
                from_pin=from_pin,
                to_pin=to_pin,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_port(
        self,
        pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add a port delay entry.

        Parameters
        ----------
        pin : str
            The port pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            Port(
                name=f"port_{pin}",
                from_pin=pin,
                to_pin=pin,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_device(
        self,
        pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add a device delay entry.

        Parameters
        ----------
        pin : str
            The device pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            Device(
                name=f"device_{pin}",
                from_pin=pin,
                to_pin=pin,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_setup(
        self,
        from_pin: str,
        to_pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add a setup timing check entry.

        Parameters
        ----------
        from_pin : str
            The data pin name.
        to_pin : str
            The clock pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            Setup(
                name=f"setup_{from_pin}_{to_pin}",
                from_pin=from_pin,
                to_pin=to_pin,
                is_timing_check=True,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_hold(
        self,
        from_pin: str,
        to_pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add a hold timing check entry.

        Parameters
        ----------
        from_pin : str
            The data pin name.
        to_pin : str
            The clock pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            Hold(
                name=f"hold_{from_pin}_{to_pin}",
                from_pin=from_pin,
                to_pin=to_pin,
                is_timing_check=True,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_removal(
        self,
        from_pin: str,
        to_pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add a removal timing check entry.

        Parameters
        ----------
        from_pin : str
            The signal pin name.
        to_pin : str
            The clock pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            Removal(
                name=f"removal_{from_pin}_{to_pin}",
                from_pin=from_pin,
                to_pin=to_pin,
                is_timing_check=True,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_recovery(
        self,
        from_pin: str,
        to_pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add a recovery timing check entry.

        Parameters
        ----------
        from_pin : str
            The signal pin name.
        to_pin : str
            The clock pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            Recovery(
                name=f"recovery_{from_pin}_{to_pin}",
                from_pin=from_pin,
                to_pin=to_pin,
                is_timing_check=True,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_setuphold(
        self,
        from_pin: str,
        to_pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add a setuphold combined timing check entry.

        Parameters
        ----------
        from_pin : str
            The data pin name.
        to_pin : str
            The clock pin name.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            SetupHold(
                name=f"setuphold_{from_pin}_{to_pin}",
                from_pin=from_pin,
                to_pin=to_pin,
                is_timing_check=True,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def add_width(
        self,
        pin: str,
        delays: dict[str, dict[str, float | None]],
    ) -> CellBuilder:
        """Add a width timing check entry.

        Parameters
        ----------
        pin : str
            The pin name to check width on.
        delays : dict[str, dict[str, float | None]]
            Delay values keyed by field name.

        Returns
        -------
        CellBuilder
            This builder instance for method chaining.
        """
        return self._add_entry(
            Width(
                name=f"width_{pin}_{pin}",
                from_pin=pin,
                to_pin=pin,
                is_timing_check=True,
                delay_paths=_build_delay_paths(delays),
            )
        )

    def done(self) -> SDFBuilder:
        """Finalize this cell and return to the parent SDFBuilder.

        Registers all accumulated entries with the parent builder.

        Returns
        -------
        SDFBuilder
            The parent builder instance for continued chaining.
        """
        self._parent._register_cell(  # noqa: SLF001
            self._cell_type,
            self._instance,
            self._entries,
        )
        return self._parent
