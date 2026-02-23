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

        # NOTE: We intentionally do NOT pass transformer= here. Passing it
        # would bind a single SDFTransformer instance whose mutable state
        # leaks between parse() calls. Instead, we apply a fresh transformer
        # in parse() so each invocation starts with clean state.
        self.parser = Lark(grammar, parser="lalr", start="start")

    def parse(self, input_text: str) -> SDFFile:
        """Parse SDF input text and return an SDFFile."""
        try:
            tree = self.parser.parse(input_text)
            return SDFTransformer().transform(tree)
        except LarkError as e:
            raise LarkError(
                f"SDF parsing failed at {getattr(e, 'line', 'unknown')}:"
                f"{getattr(e, 'column', 'unknown')} - {e!s}"
            ) from e
        except Exception as e:
            raise type(e)(f"Unexpected error during SDF parsing: {e!s}") from e

    def parse_file(self, filepath: Path | str) -> SDFFile:
        """Read and parse an SDF file from disk."""
        try:
            content = Path(filepath).read_text()
        except OSError as e:
            raise OSError(f"Error reading SDF file {filepath}: {e!s}") from e
        return self.parse(content)


_local = threading.local()


def get_parser() -> SDFLarkParser:
    """Get or create a thread-local parser instance."""
    if not hasattr(_local, "parser"):
        _local.parser = SDFLarkParser()
    return _local.parser


def parse_sdf(input_text: str) -> SDFFile:
    """Parse SDF text using a thread-local Lark parser."""
    parser = get_parser()
    return parser.parse(input_text)


def parse_sdf_file(filepath: Path | str) -> SDFFile:
    """Parse an SDF file from disk using a thread-local Lark parser."""
    parser = get_parser()
    return parser.parse_file(filepath)
