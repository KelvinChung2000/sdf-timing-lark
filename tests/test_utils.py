"""Tests for utils.py -- factory functions."""

import pytest

from sdf_timing.model import (
    BaseEntry,
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
    Setup,
    SetupHold,
    TimingPortSpec,
    Values,
    Width,
)
from sdf_timing.utils import (
    add_constraint,
    add_device,
    add_interconnect,
    add_iopath,
    add_port,
    add_tcheck,
    store_entry,
)


def _make_port_spec(name, edge=None):
    return PortSpec(port=name, port_edge=edge)


def _make_timing_port(name, edge=None, *, cond=False, cond_equation=None):
    return TimingPortSpec(
        port=name, port_edge=edge, cond=cond, cond_equation=cond_equation
    )


def _make_paths():
    return DelayPaths(nominal=Values(avg=1.0))


class TestAddPort:
    def test_creates_port(self):
        port = add_port(_make_port_spec("A"), _make_paths())
        assert isinstance(port, Port)
        assert port.name == "port_A"
        assert port.from_pin == "A"
        assert port.to_pin == "A"
        assert port.type == EntryType.PORT


class TestAddInterconnect:
    def test_creates_interconnect(self):
        ic = add_interconnect(
            _make_port_spec("X", EdgeType.POSEDGE),
            _make_port_spec("Y", EdgeType.NEGEDGE),
            _make_paths(),
        )
        assert isinstance(ic, Interconnect)
        assert ic.name == "interconnect_X_Y"
        assert ic.from_pin == "X"
        assert ic.to_pin == "Y"
        assert ic.from_pin_edge == EdgeType.POSEDGE
        assert ic.to_pin_edge == EdgeType.NEGEDGE
        assert ic.type == EntryType.INTERCONNECT


class TestAddIopath:
    def test_creates_iopath(self):
        io = add_iopath(
            _make_port_spec("IN", EdgeType.POSEDGE),
            _make_port_spec("OUT"),
            _make_paths(),
        )
        assert isinstance(io, Iopath)
        assert io.name == "iopath_IN_OUT"
        assert io.from_pin == "IN"
        assert io.to_pin == "OUT"
        assert io.type == EntryType.IOPATH


class TestAddDevice:
    def test_creates_device(self):
        dev = add_device(_make_port_spec("mux"), _make_paths())
        assert isinstance(dev, Device)
        assert dev.name == "device_mux"
        assert dev.from_pin == "mux"
        assert dev.to_pin == "mux"
        assert dev.type == EntryType.DEVICE


class TestAddTcheck:
    def test_setup(self):
        tc = add_tcheck(
            EntryType.SETUP,
            _make_timing_port("D"),
            _make_timing_port("CLK", EdgeType.POSEDGE),
            _make_paths(),
        )
        assert isinstance(tc, Setup)
        assert tc.type == EntryType.SETUP
        assert tc.is_timing_check is True

    def test_hold(self):
        tc = add_tcheck(
            EntryType.HOLD,
            _make_timing_port("D"),
            _make_timing_port("CLK", EdgeType.POSEDGE),
            _make_paths(),
        )
        assert isinstance(tc, Hold)
        assert tc.type == EntryType.HOLD

    def test_removal(self):
        tc = add_tcheck(
            EntryType.REMOVAL,
            _make_timing_port("RST"),
            _make_timing_port("CLK"),
            _make_paths(),
        )
        assert isinstance(tc, Removal)
        assert tc.type == EntryType.REMOVAL

    def test_recovery(self):
        tc = add_tcheck(
            EntryType.RECOVERY,
            _make_timing_port("RST"),
            _make_timing_port("CLK"),
            _make_paths(),
        )
        assert isinstance(tc, Recovery)
        assert tc.type == EntryType.RECOVERY

    def test_width(self):
        tc = add_tcheck(
            EntryType.WIDTH,
            _make_timing_port("CLK"),
            _make_timing_port("CLK", EdgeType.POSEDGE),
            _make_paths(),
        )
        assert isinstance(tc, Width)
        assert tc.type == EntryType.WIDTH

    def test_setuphold(self):
        tc = add_tcheck(
            EntryType.SETUPHOLD,
            _make_timing_port("D"),
            _make_timing_port("CLK", EdgeType.POSEDGE),
            _make_paths(),
        )
        assert isinstance(tc, SetupHold)
        assert tc.type == EntryType.SETUPHOLD

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown timing check type"):
            add_tcheck(
                EntryType.PORT,
                _make_timing_port("A"),
                _make_timing_port("B"),
                _make_paths(),
            )

    def test_with_cond(self):
        tc = add_tcheck(
            EntryType.SETUP,
            _make_timing_port("D"),
            _make_timing_port(
                "CLK", EdgeType.POSEDGE, cond=True, cond_equation="EN==1"
            ),
            _make_paths(),
        )
        assert tc.is_cond is True
        assert tc.cond_equation == "EN==1"


class TestAddConstraint:
    def test_pathconstraint(self):
        c = add_constraint(
            EntryType.PATHCONSTRAINT,
            _make_port_spec("A"),
            _make_port_spec("B"),
            _make_paths(),
        )
        assert isinstance(c, PathConstraint)
        assert c.type == EntryType.PATHCONSTRAINT
        assert c.is_timing_env is True

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown constraint type"):
            add_constraint(
                EntryType.PORT,
                _make_port_spec("A"),
                _make_port_spec("B"),
                _make_paths(),
            )


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
