import threading
from pathlib import Path

from lark import Lark, LarkError

from .sdf_transformers import SDFTransformer


class SDFLarkParser:
    """Lark-based SDF parser that replaces the PLY implementation."""

    def __init__(self) -> None:
        """Initialize the parser with the SDF grammar."""
        # Get the path to the grammar file
        grammar_path = Path(__file__).parent / "sdf.lark"

        try:
            with open(grammar_path) as f:
                grammar = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Grammar file not found: {grammar_path}")

        # Create the Lark parser with LALR(1) algorithm for performance
        self.parser = Lark(
            grammar, parser="lalr", start="start", transformer=SDFTransformer()
        )

    def parse(self, input_text: str) -> object:
        """
        Parse SDF input text and return the timing data structure.

        Args:
            input_text (str): The SDF file content as a string

        Returns
        -------
            SDFFile: Parsed timing data object

        Raises
        ------
            LarkError: If parsing fails
        """
        try:
            # Parse the input and transform it using our transformer
            result = self.parser.parse(input_text)
            return result

        except LarkError as e:
            # Preserve original Lark error with better context
            raise LarkError(
                f"SDF parsing failed at {getattr(e, 'line', 'unknown')}:"
                f"{getattr(e, 'column', 'unknown')} - {str(e)}"
            )
        except Exception as e:
            # Re-raise with context but preserve original exception type
            raise type(e)(f"Unexpected error during SDF parsing: {str(e)}") from e

    def parse_file(self, filepath: Path | str) -> object:
        """
        Parse an SDF file directly.

        Args:
            filepath (str): Path to the SDF file

        Returns
        -------
            SDFFile: Parsed timing data object
        """
        try:
            with Path(filepath).open("r") as f:
                content = f.read()
            return self.parse(content)
        except OSError as e:
            raise Exception(f"Error reading SDF file {filepath}: {str(e)}")


# Thread-local storage for parser instances to ensure thread safety

_local = threading.local()


def get_parser() -> SDFLarkParser:
    """Get or create a thread-local parser instance."""
    if not hasattr(_local, "parser"):
        _local.parser = SDFLarkParser()
    return _local.parser


def parse_sdf(input_text: str) -> object:
    """
    Parse SDF text using the Lark parser.

    This function provides the same interface as the original PLY-based parser.

    Args:
        input_text (str): SDF content as string

    Returns
    -------
        SDFFile: Parsed timing data structure
    """
    # Create a fresh parser instance to avoid state contamination
    parser = SDFLarkParser()
    return parser.parse(input_text)


def parse_sdf_file(filepath: Path | str) -> object:
    """
    Parse an SDF file using the Lark parser.

    Args:
        filepath (str): Path to SDF file

    Returns
    -------
        SDFFile: Parsed timing data structure
    """
    parser = get_parser()
    return parser.parse_file(filepath)
