# python-sdf-timing

A Python library for parsing, writing, and analyzing Standard Delay Format (SDF) Timing Annotation files. Built using [Lark](https://github.com/lark-parser/lark) parser generator for robust and efficient SDF processing.

## Features

- **Parse SDF files** into Python data structures
- **Write SDF files** from Python objects using Jinja2 templates
- **Timing path graph** built on NetworkX for path finding and delay composition
- **Delay arithmetic** on Values and DelayPaths (add, subtract, negate, scale, approximate equality)
- **Path composition** to sum delays along multi-hop timing paths
- **Path verification** to check composed delays against expected values
- **Delay decomposition** to extract unknown segments from total and known delays
- **Modern Typer CLI** with commands for parsing, emitting, inspection, composition, verification, and decomposition
- **Comprehensive timing support** including:
  - IOPATH delays
  - INTERCONNECT delays
  - PORT delays
  - DEVICE delays
  - Timing checks (SETUP, HOLD, RECOVERY, REMOVAL, WIDTH, SETUPHOLD)
  - PATH constraints
- **Header metadata** support (design, vendor, timescale, etc.)
- **Edge specifications** (posedge/negedge)
- **Conditional timing** support
- **Type-safe data models** using Python dataclasses

## About This Project

This is a modernized rewrite of the original [f4pga-sdf-timing](https://github.com/chipsalliance/f4pga-sdf-timing) project, which is no longer actively maintained. This project represents a complete rebuild using a Lark-based parser for more robust and maintainable SDF processing. It incorporates fixes, improvements, and enhancements beyond the original codebase while maintaining compatibility with standard SDF formats.

## Installation

```bash
uv pip install sdf_timing
```

For development:

```bash
git clone https://github.com/chipsalliance/python-sdf-timing.git
cd python-sdf-timing
uv pip install -e '.[dev]'
```

## Usage

### Command Line Interface

The `sdf-timing` CLI provides several commands for working with SDF files.

#### Parse an SDF file

```bash
# Output as JSON (default)
sdf-timing parse design.sdf

# Output as SDF
sdf-timing parse design.sdf --format sdf

# With custom timescale
sdf-timing parse design.sdf --format sdf --timescale 1ns
```

#### Inspect an SDF file

```bash
sdf-timing info design.sdf
```

Displays Rich-formatted tables showing header fields, cell count, entry type breakdown, and instance list.

#### Compose path delays

```bash
# Find all paths from source to sink and sum their delays
sdf-timing compose design.sdf P1/z P2/i

# Verbose mode shows full edge-by-edge path details
sdf-timing compose design.sdf P1/z P2/i --verbose
```

#### Verify a path delay

```bash
sdf-timing verify design.sdf P1/z P2/i \
    --expected '{"fast": {"min": 1.805, "avg": null, "max": 1.805}}'
```

#### Decompose a delay

```bash
sdf-timing decompose \
    --total '{"nominal": {"min": 3.0, "avg": null, "max": 3.0}}' \
    --known '{"nominal": {"min": 1.0, "avg": null, "max": 1.0}}'
```

#### Convert JSON back to SDF

```bash
sdf-timing parse design.sdf > design.json
sdf-timing emit design.json
```

### Python API

#### Parse and emit SDF files

```python
from sdf_timing import parse, emit

# Parse SDF text into an SDFFile object
with open("design.sdf") as f:
    sdf = parse(f.read())

# Access header information
print(sdf.header.design)
print(sdf.header.timescale)

# Iterate through cells and their timing entries
for cell_type, instances in sdf.cells.items():
    for instance, entries in instances.items():
        for name, entry in entries.items():
            print(f"{cell_type}/{instance}: {entry.type} {entry.from_pin} -> {entry.to_pin}")

# Emit back to SDF text
sdf_output = emit(sdf, timescale="1ns")
```

#### Build a timing graph and compose delays

```python
from sdf_timing import parse, TimingGraph

with open("design.sdf") as f:
    sdf = parse(f.read())

graph = TimingGraph(sdf)

# List all nodes (pin names)
print(graph.nodes())

# Find all paths between two pins
paths = graph.find_paths("P1/z", "P2/i")
for path in paths:
    total_delay = graph.compose_delay(path)
    print(total_delay.to_dict())

# Or compose directly (returns list of delays for all paths found)
delays = graph.compose("P1/z", "P2/i")
```

#### Verify and decompose delays

```python
from sdf_timing import verify_path, decompose_delay
from sdf_timing.model import DelayPaths, Values

# Verify a path's delay matches expected
result = verify_path(graph, "P1/z", "P2/i",
    expected=DelayPaths(fast=Values(min=1.805, avg=None, max=1.805)),
    tolerance=1e-6)
print(result.passed)  # True or False

# Decompose: compute unknown = total - known
unknown = decompose_delay(
    total=DelayPaths(nominal=Values(min=3.0, avg=None, max=3.0)),
    known=DelayPaths(nominal=Values(min=1.0, avg=None, max=1.0)),
)
```

#### Delay arithmetic

```python
from sdf_timing.model import Values, DelayPaths

a = Values(min=1.0, avg=2.0, max=3.0)
b = Values(min=0.5, avg=1.0, max=1.5)

c = a + b         # Values(min=1.5, avg=3.0, max=4.5)
d = a - b         # Values(min=0.5, avg=1.0, max=1.5)
e = -a            # Values(min=-1.0, avg=-2.0, max=-3.0)
f = a * 2.0       # Values(min=2.0, avg=4.0, max=6.0)
g = 2.0 * a       # same as above

a.approx_eq(b)    # False
a.approx_eq(a)    # True
```

None propagates through all operations -- if either operand is None for a field, the result is None.

## Requirements

- Python 3.11 or higher
- [Lark](https://github.com/lark-parser/lark) parser
- [Jinja2](https://jinja.palletsprojects.com/) templating engine
- [Typer](https://typer.tiangolo.com/) CLI framework
- [Rich](https://rich.readthedocs.io/) terminal formatting
- [NetworkX](https://networkx.org/) graph library

## Development

Install development dependencies:

```bash
uv pip install -e '.[dev]'
```

Run tests:

```bash
uv run pytest
```

Code formatting and linting:

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## About Standard Delay Format

From Wikipedia:

> Standard Delay Format (SDF) is an IEEE standard for the representation and
> interpretation of timing data for use at any stage of an electronic design
> process. It finds wide applicability in design flows, and forms an efficient
> bridge between
> [Dynamic timing verification](https://en.wikipedia.org/wiki/Dynamic_timing_verification) and
> [Static timing analysis](https://en.wikipedia.org/wiki/Static_timing_analysis).
>
> It is an ASCII format that is represented in a tool and language independent
> way and includes path delays, timing constraint values, interconnect delays
> and high level technology parameters.
>
> SDF format can be used for back-annotation as well as forward-annotation.

## Links

- [python-sdf-timing GitHub Repository](https://github.com/chipsalliance/python-sdf-timing)
- [Standard Delay Format (Wikipedia)](https://en.wikipedia.org/wiki/Standard_Delay_Format)
- [Lark Parser](https://github.com/lark-parser/lark)
- [Verilog To Routing SDF Generation](https://docs.verilogtorouting.org/en/latest/tutorials/timing_simulation/#post-imp-sdf)

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## Contributing

This project is part of the [F4PGA](https://f4pga.org/) initiative under [CHIPS Alliance](https://chipsalliance.org/).

Contributions are welcome! Please submit issues and pull requests on GitHub.
