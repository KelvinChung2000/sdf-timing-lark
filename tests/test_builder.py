"""Tests for CellBuilder.add_entry collision handling."""

from sdf_toolkit.core.builder import CellBuilder, SDFBuilder
from sdf_toolkit.core.model import (
    BaseEntry,
    EntryType,
    Hold,
    Iopath,
)


def _make_cell_builder() -> tuple[CellBuilder, dict[str, BaseEntry]]:
    """Create a CellBuilder with access to its internal entries dict."""
    builder = SDFBuilder().add_cell("cell", "inst")
    return builder, builder._entries  # noqa: SLF001


class TestAddEntry:
    def test_no_collision(self):
        cb, entries = _make_cell_builder()
        entry = Iopath(name="iopath_A_B", from_pin="A", to_pin="B")
        cb.add_entry(entry)
        assert entry.name == "iopath_A_B"
        assert "iopath_A_B" in entries

    def test_with_collisions(self):
        cb, entries = _make_cell_builder()
        e1 = Iopath(name="iopath_CP_Q", from_pin="CP", to_pin="Q")
        e2 = Iopath(name="iopath_CP_Q", from_pin="CP", to_pin="Q")
        e3 = Iopath(name="iopath_CP_Q", from_pin="CP", to_pin="Q")

        cb.add_entry(e1)
        cb.add_entry(e2)
        cb.add_entry(e3)

        assert e1.name == "iopath_CP_Q"
        assert e2.name == "iopath_CP_Q_1"
        assert e3.name == "iopath_CP_Q_2"
        assert len(entries) == 3

    def test_mixed_entries(self):
        cb, entries = _make_cell_builder()
        e1 = Iopath(name="iopath_A_B", from_pin="A", to_pin="B")
        e2 = Hold(name="hold_A_B", from_pin="A", to_pin="B")
        e3 = Iopath(name="iopath_A_B", from_pin="A", to_pin="B")

        cb.add_entry(e1)
        cb.add_entry(e2)
        cb.add_entry(e3)

        assert e3.name == "iopath_A_B_1"
        assert len(entries) == 3


class TestCellBuilderDelegation:
    def test_set_header_via_cell_builder(self):
        """CellBuilder.set_header should delegate to parent SDFBuilder."""
        sdf = (
            SDFBuilder()
            .add_cell("BUF", "b0")
            .add_iopath("A", "Y", {"nominal": {"min": 1.0, "avg": 1.0, "max": 1.0}})
            .set_header(sdfversion="4.0", timescale="1ns")
            .add_cell("INV", "i0")
            .add_iopath("A", "Z", {"nominal": {"min": 2.0, "avg": 2.0, "max": 2.0}})
            .build()
        )
        assert sdf.header.sdfversion == "4.0"
        assert sdf.header.timescale == "1ns"
        assert "BUF" in sdf.cells
        assert "INV" in sdf.cells

    def test_add_path_constraint(self):
        """CellBuilder.add_path_constraint creates a PATHCONSTRAINT entry."""
        sdf = (
            SDFBuilder()
            .add_cell("XOR", "x0")
            .add_path_constraint(
                "A",
                "B",
                {
                    "rise": {"min": 1.0, "avg": 2.0, "max": 3.0},
                    "fall": {"min": 0.5, "avg": 1.0, "max": 1.5},
                },
            )
            .build()
        )
        entries = sdf.cells["XOR"]["x0"]
        assert len(entries) == 1
        entry = next(iter(entries.values()))
        assert entry.type == EntryType.PATHCONSTRAINT
