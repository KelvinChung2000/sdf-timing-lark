"""Tests for sdf_lark_parser.py -- error handling and public API."""

from unittest.mock import patch

import pytest
from conftest import DATA_DIR
from lark import LarkError

from sdf_timing.sdf_lark_parser import (
    SDFLarkParser,
    _local,
    get_parser,
    parse_sdf,
    parse_sdf_file,
)


class TestSDFLarkParserErrors:
    def test_malformed_sdf_raises_lark_error(self):
        parser = SDFLarkParser()
        with pytest.raises(LarkError, match="SDF parsing failed"):
            parser.parse("THIS IS NOT VALID SDF")

    def test_generic_exception_path(self):
        parser = SDFLarkParser()
        with (
            patch.object(parser.parser, "parse", side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError, match="Unexpected error during SDF parsing"),
        ):
            parser.parse("(DELAYFILE)")

    def test_grammar_file_missing(self):
        with (
            patch("pathlib.Path.open", side_effect=FileNotFoundError("not found")),
            pytest.raises(FileNotFoundError, match="Grammar file not found"),
        ):
            SDFLarkParser()


class TestParseFile:
    def test_parse_file_success(self):
        parser = SDFLarkParser()
        result = parser.parse_file(DATA_DIR / "test1.sdf")
        assert result is not None
        assert hasattr(result, "cells")

    def test_parse_file_nonexistent(self):
        parser = SDFLarkParser()
        with pytest.raises(Exception, match="Error reading SDF file"):
            parser.parse_file("/nonexistent/path/file.sdf")


class TestModuleLevelFunctions:
    def test_parse_sdf_file(self):
        result = parse_sdf_file(DATA_DIR / "test1.sdf")
        assert result is not None
        assert hasattr(result, "cells")

    def test_get_parser_caching(self):
        if hasattr(_local, "parser"):
            del _local.parser
        p1 = get_parser()
        p2 = get_parser()
        assert p1 is p2

    def test_parse_sdf(self):
        sdf_content = (DATA_DIR / "test1.sdf").read_text()
        result = parse_sdf(sdf_content)
        assert result is not None
