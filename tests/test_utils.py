"""Tests for utils.py -- store_entry collision handling."""

from sdf_timing.core.model import (
    BaseEntry,
    Hold,
    Iopath,
)
from sdf_timing.core.utils import store_entry


class TestStoreEntry:
    def test_no_collision(self):
        cell_dict: dict[str, BaseEntry] = {}
        entry = Iopath(name="iopath_A_B", from_pin="A", to_pin="B")
        key = store_entry(cell_dict, entry)
        assert key == "iopath_A_B"
        assert entry.name == "iopath_A_B"
        assert "iopath_A_B" in cell_dict

    def test_with_collisions(self):
        cell_dict: dict[str, BaseEntry] = {}
        e1 = Iopath(name="iopath_CP_Q", from_pin="CP", to_pin="Q")
        e2 = Iopath(name="iopath_CP_Q", from_pin="CP", to_pin="Q")
        e3 = Iopath(name="iopath_CP_Q", from_pin="CP", to_pin="Q")

        k1 = store_entry(cell_dict, e1)
        k2 = store_entry(cell_dict, e2)
        k3 = store_entry(cell_dict, e3)

        assert k1 == "iopath_CP_Q"
        assert k2 == "iopath_CP_Q_1"
        assert k3 == "iopath_CP_Q_2"
        assert e1.name == "iopath_CP_Q"
        assert e2.name == "iopath_CP_Q_1"
        assert e3.name == "iopath_CP_Q_2"
        assert len(cell_dict) == 3

    def test_mixed_entries(self):
        cell_dict: dict[str, BaseEntry] = {}
        e1 = Iopath(name="iopath_A_B", from_pin="A", to_pin="B")
        e2 = Hold(name="hold_A_B", from_pin="A", to_pin="B")
        e3 = Iopath(name="iopath_A_B", from_pin="A", to_pin="B")

        store_entry(cell_dict, e1)
        store_entry(cell_dict, e2)
        k3 = store_entry(cell_dict, e3)

        assert k3 == "iopath_A_B_1"
        assert len(cell_dict) == 3
