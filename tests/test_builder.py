"""Tests for CellBuilder.add_entry collision handling."""

from sdf_toolkit.core.builder import CellBuilder, SDFBuilder
from sdf_toolkit.core.model import (
    BaseEntry,
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
