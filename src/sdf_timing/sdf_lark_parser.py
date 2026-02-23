"""Lark-based SDF file parser with thread-safe caching."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from lark import Lark, LarkError

from sdf_timing.sdf_transformers import SDFTransformer

if TYPE_CHECKING:
    from sdf_timing.model import SDFFile


class SDFLarkParser:
    """Lark-based SDF parser that replaces the PLY implementation."""

    def __init__(self) -> None:
        """Initialize the parser with the SDF grammar."""
        grammar_path = (Path(__file__).parent / "sdf.lark").resolve()

        try:
            with grammar_path.open() as f:
                grammar = f.read()
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Grammar file not found: {grammar_path}") from exc

        # Create the Lark parser with LALR(1) algorithm for performance
        # NOTE: We intentionally do NOT pass transformer= here. Passing it
        # would bind a single SDFTransformer instance whose mutable state
        # leaks between parse() calls. Instead, we apply a fresh transformer
        # in parse() so each invocation starts with clean state.
        self.parser = Lark(grammar, parser="lalr", start="start")

    def parse(self, input_text: str) -> SDFFile:
        """Parse SDF input text and return the timing data structure.

        Parameters
        ----------
        input_text : str
            The SDF file content as a string.

        Returns
        -------
        SDFFile
            Parsed timing data structure.

        Raises
        ------
        LarkError
            If parsing fails.
        """
        try:
            tree = self.parser.parse(input_text)
            return SDFTransformer().transform(tree)  # type: ignore[return-value]
        except LarkError as e:
            raise LarkError(
                f"SDF parsing failed at {getattr(e, 'line', 'unknown')}:"
                f"{getattr(e, 'column', 'unknown')} - {e!s}"
            ) from e
        except Exception as e:
            raise type(e)(f"Unexpected error during SDF parsing: {e!s}") from e

    def parse_file(self, filepath: Path | str) -> SDFFile:
        """Parse an SDF file directly.

        Parameters
        ----------
        filepath : Path | str
            Path to the SDF file.

        Returns
        -------
        SDFFile
            Parsed timing data structure.
        """
        try:
            with Path(filepath).open("r") as f:
                content = f.read()
            return self.parse(content)
        except OSError as e:
            raise OSError(f"Error reading SDF file {filepath}: {e!s}") from e


# Thread-local storage for parser instances to ensure thread safety

_local = threading.local()


def get_parser() -> SDFLarkParser:
    """Get or create a thread-local parser instance."""
    if not hasattr(_local, "parser"):
        _local.parser = SDFLarkParser()
    return _local.parser


def parse_sdf(input_text: str) -> SDFFile:
    """Parse SDF text using the Lark parser.

    This function provides the same interface as the original PLY-based parser.

    Parameters
    ----------
    input_text : str
        SDF content as string.

    Returns
    -------
    SDFFile
        Parsed timing data structure.
    """
    parser = get_parser()
    return parser.parse(input_text)


def parse_sdf_file(filepath: Path | str) -> SDFFile:
    """Parse an SDF file using the Lark parser.

    Parameters
    ----------
    filepath : Path | str
        Path to SDF file.

    Returns
    -------
    SDFFile
        Parsed timing data structure.
    """
    parser = get_parser()
    return parser.parse_file(filepath)
