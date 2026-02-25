"""Tests for sdfparse.py -- CLI entry point."""

from unittest.mock import patch

import pytest
from conftest import DATA_DIR

from sdf_toolkit.io.sdfparse import main


class TestCLIMain:
    def test_valid_file(self, capsys):
        test_file = str(DATA_DIR / "empty.sdf")
        with patch("sys.argv", ["sdf-toolkit", test_file]):
            main()
        captured = capsys.readouterr()
        assert "header" in captured.out

    def test_no_arguments(self, capsys):
        with patch("sys.argv", ["sdf-toolkit"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_nonexistent_file(self, capsys):
        with patch("sys.argv", ["sdf-toolkit", "/nonexistent/file.sdf"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out
