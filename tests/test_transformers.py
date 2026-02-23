"""Tests for sdf_transformers.py -- transformer coverage for edge cases."""

from conftest import DATA_DIR

from sdf_timing.model import EntryType
from sdf_timing.sdf_lark_parser import parse_sdf


class TestIncrementDelays:
    def test_increment_delays(self):
        sdf_content = (DATA_DIR / "spec-example3.sdf").read_text()
        result = parse_sdf(sdf_content)
        cells = result.cells
        assert "XOR2" in cells
        instance = cells["XOR2"]["top.x1"]
        for entry in instance.values():
            assert entry.is_incremental is True
            assert entry.is_absolute is False


class TestCondTimingChecks:
    def test_cond_timing_checks(self):
        sdf_content = (DATA_DIR / "spec-example2.sdf").read_text()
        result = parse_sdf(sdf_content)
        cells = result.cells
        assert "CDS_GEN_FD_P_SD_RB_SB_NO" in cells
        instance = cells["CDS_GEN_FD_P_SD_RB_SB_NO"]["top.ff1"]

        setup_entries = [e for e in instance.values() if e.type == EntryType.SETUP]
        hold_entries = [e for e in instance.values() if e.type == EntryType.HOLD]
        recovery_entries = [
            e for e in instance.values() if e.type == EntryType.RECOVERY
        ]
        width_entries = [e for e in instance.values() if e.type == EntryType.WIDTH]
        setuphold_entries = [
            e for e in instance.values() if e.type == EntryType.SETUPHOLD
        ]

        assert len(setup_entries) == 1
        assert len(hold_entries) == 1
        assert len(recovery_entries) == 2
        assert len(setuphold_entries) == 1

        for entry in setup_entries + hold_entries:
            assert entry.is_cond is True
            assert entry.cond_equation is not None

        # Entries are keyed by name (width_PORT_PORT), so name collisions
        # mean fewer entries than in the SDF source.
        cond_widths = [w for w in width_entries if w.is_cond]
        plain_widths = [w for w in width_entries if not w.is_cond]
        assert len(cond_widths) >= 1
        assert len(plain_widths) >= 1


class TestSingleFloatRvalue:
    def test_single_float_value(self):
        sdf_content = (DATA_DIR / "spec-example1.sdf").read_text()
        result = parse_sdf(sdf_content)
        assert result is not None
        assert len(result.cells) > 0


class TestConditionalDelays:
    def test_cond_iopath_with_equation(self):
        sdf_content = (DATA_DIR / "fixpoint.sdf").read_text()
        result = parse_sdf(sdf_content)
        cells = result.cells
        assert "routing_bel" in cells
        instance = cells["routing_bel"]["slicem/lut_c"]

        for entry in instance.values():
            assert entry.is_cond is True
            assert entry.cond_equation is not None
            assert len(entry.cond_equation) > 0

    def test_cond_increment_with_equation(self):
        sdf_content = (DATA_DIR / "spec-example3.sdf").read_text()
        result = parse_sdf(sdf_content)
        cells = result.cells
        instance = cells["XOR2"]["top.x1"]

        cond_entries = [e for e in instance.values() if e.is_cond]
        assert len(cond_entries) > 0
        for entry in cond_entries:
            assert entry.cond_equation is not None


class TestPathConstraints:
    def test_pathconstraint(self):
        sdf_content = (DATA_DIR / "spec-example4.sdf").read_text()
        result = parse_sdf(sdf_content)
        cells = result.cells
        assert "XOR" in cells
        for _instance_name, instance in cells["XOR"].items():
            for entry in instance.values():
                assert entry.type == EntryType.PATHCONSTRAINT
                assert entry.is_timing_env is True
                assert entry.delay_paths is not None
                assert entry.delay_paths.rise is not None
                assert entry.delay_paths.fall is not None


class TestPortDelays:
    def test_port_delays(self):
        sdf_content = (DATA_DIR / "spec-example2.sdf").read_text()
        result = parse_sdf(sdf_content)
        cells = result.cells
        instance = cells["CDS_GEN_FD_P_SD_RB_SB_NO"]["top.ff1"]

        port_entries = [e for e in instance.values() if e.type == EntryType.PORT]
        assert len(port_entries) > 0
        for entry in port_entries:
            assert entry.from_pin == entry.to_pin


class TestDeviceDelays:
    def test_device_delays(self):
        sdf_content = (DATA_DIR / "test-device.sdf").read_text()
        result = parse_sdf(sdf_content)
        cells = result.cells
        for _celltype, instances in cells.items():
            for _inst_name, entries in instances.items():
                for entry in entries.values():
                    assert entry.type == EntryType.DEVICE
                    assert entry.from_pin == entry.to_pin
