"""Tests for model.py -- dict protocol methods and to_dict."""

import pytest

from sdf_timing.core.model import (
    BaseEntry,
    DelayPaths,
    EntryType,
    Port,
    SDFFile,
    SDFHeader,
    Values,
)


class TestSDFHeader:
    def test_to_dict_filters_none(self):
        header = SDFHeader(sdfversion="2.1", design="top")
        d = header.to_dict()
        assert d == {"sdfversion": "2.1", "design": "top"}
        assert "vendor" not in d

    def test_getitem(self):
        header = SDFHeader(sdfversion="3.0")
        assert header["sdfversion"] == "3.0"

    def test_contains_present(self):
        header = SDFHeader(design="chip")
        assert "design" in header

    def test_contains_absent(self):
        header = SDFHeader()
        assert "design" not in header

    def test_get_existing(self):
        header = SDFHeader(vendor="ACME")
        assert header.get("vendor") == "ACME"

    def test_get_existing_none_attr(self):
        # vendor exists as an attribute (set to None),
        # so get() returns None, not the default
        header = SDFHeader()
        assert header.get("vendor", "default") is None

    def test_get_truly_missing_attr(self):
        header = SDFHeader()
        assert header.get("nonexistent", "default") == "default"

    def test_get_missing_no_default(self):
        header = SDFHeader()
        assert header.get("vendor") is None

    def test_keys(self):
        header = SDFHeader(sdfversion="1.0", divider="/")
        assert set(header.keys()) == {"sdfversion", "divider"}

    def test_values(self):
        header = SDFHeader(sdfversion="1.0", divider="/")
        assert set(header.values()) == {"1.0", "/"}

    def test_items(self):
        header = SDFHeader(sdfversion="1.0", divider="/")
        assert dict(header.items()) == {"sdfversion": "1.0", "divider": "/"}


class TestValues:
    def test_to_dict(self):
        v = Values(min=1.0, avg=2.0, max=3.0)
        assert v.to_dict() == {"min": 1.0, "avg": 2.0, "max": 3.0}

    def test_to_dict_with_nones(self):
        v = Values(avg=5.0)
        assert v.to_dict() == {"min": None, "avg": 5.0, "max": None}


class TestDelayPaths:
    def test_to_dict_nominal(self):
        dp = DelayPaths(nominal=Values(min=1.0, avg=2.0, max=3.0))
        d = dp.to_dict()
        assert "nominal" in d
        assert d["nominal"] == {"min": 1.0, "avg": 2.0, "max": 3.0}

    def test_to_dict_fast_slow(self):
        dp = DelayPaths(
            fast=Values(min=0.5, avg=1.0, max=1.5),
            slow=Values(min=2.0, avg=3.0, max=4.0),
        )
        d = dp.to_dict()
        assert "fast" in d
        assert "slow" in d
        assert "nominal" not in d

    def test_to_dict_setup_hold(self):
        dp = DelayPaths(
            setup=Values(avg=1.0),
            hold=Values(avg=2.0),
        )
        d = dp.to_dict()
        assert "setup" in d
        assert "hold" in d

    def test_to_dict_rise_fall(self):
        dp = DelayPaths(
            rise=Values(min=1.0, avg=2.0, max=3.0),
            fall=Values(min=0.5, avg=1.0, max=1.5),
        )
        d = dp.to_dict()
        assert "rise" in d
        assert "fall" in d

    def test_to_dict_empty(self):
        dp = DelayPaths()
        assert dp.to_dict() == {}

    def test_contains(self):
        dp = DelayPaths(nominal=Values(avg=1.0))
        assert "nominal" in dp
        assert "fast" not in dp

    def test_getitem(self):
        v = Values(avg=1.0)
        dp = DelayPaths(nominal=v)
        assert dp["nominal"] is v


class TestBaseEntry:
    def test_to_dict(self):
        entry = BaseEntry(name="test", type=EntryType.IOPATH)
        d = entry.to_dict()
        assert d["name"] == "test"
        assert d["type"] == EntryType.IOPATH

    def test_port_type(self):
        p = Port(name="port_A")
        assert p.type == EntryType.PORT
        d = p.to_dict()
        assert d["type"] == EntryType.PORT


class TestSDFFile:
    def setup_method(self):
        self.header = SDFHeader(sdfversion="2.1", design="top")
        entry = Port(
            name="port_A",
            from_pin="A",
            to_pin="A",
            delay_paths=DelayPaths(nominal=Values(avg=1.0)),
        )
        self.cells = {"INV": {"inst1": {"port_A": entry}}}
        self.sdf = SDFFile(header=self.header, cells=self.cells)

    def test_to_dict(self):
        d = self.sdf.to_dict()
        assert "header" in d
        assert "cells" in d
        assert d["header"]["sdfversion"] == "2.1"
        assert "INV" in d["cells"]
        assert "inst1" in d["cells"]["INV"]
        assert "port_A" in d["cells"]["INV"]["inst1"]

    def test_getitem_header(self):
        assert self.sdf["header"] is self.header

    def test_getitem_cells(self):
        assert self.sdf["cells"] is self.cells

    def test_getitem_invalid(self):
        with pytest.raises(KeyError):
            _ = self.sdf["invalid"]

    def test_contains(self):
        assert "header" in self.sdf
        assert "cells" in self.sdf
        assert "invalid" not in self.sdf

    def test_get_header(self):
        assert self.sdf.get("header") is self.header

    def test_get_cells(self):
        assert self.sdf.get("cells") is self.cells

    def test_get_missing_default(self):
        fallback = SDFHeader(sdfversion="fallback")
        assert self.sdf.get("missing", fallback) is fallback

    def test_get_missing_none(self):
        assert self.sdf.get("missing") is None
