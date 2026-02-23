# python-sdf-timing

A Python library for parsing and writing Standard Delay Format (SDF) Timing Annotation files. Built using [Lark](https://github.com/lark-parser/lark) parser generator for robust and efficient SDF processing.

## Features

- **Parse SDF files** into Python data structures
- **Write SDF files** from Python objects using Jinja2 templates
- **Command-line interface** for quick SDF parsing and validation
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

### Python API

#### Parse an SDF file

```python
from sdf_timing.sdfparse import parse

with open("design.sdf", "r") as f:
    sdf_content = f.read()

# Parse the SDF file
timing_data = parse(sdf_content)

# Access header information
print(timing_data.header.design)
print(timing_data.header.timescale)

# Iterate through cells and their timing entries
for cell_name, cell_data in timing_data.cells.items():
    print(f"Cell: {cell_name}")
    for entry in cell_data.entries:
        print(f"  Type: {entry.type}")
        print(f"  Delays: {entry.delays}")
```

#### Write an SDF file

```python
from sdf_timing.sdfparse import emit
from sdf_timing.model import SDFFile, SDFHeader, Cell

# Create or modify timing data
timing_data = SDFFile(
    header=SDFHeader(
        design="my_design",
        timescale="1ns"
    ),
    cells={...}
)

# Emit SDF content
sdf_output = emit(timing_data, timescale="1ns")

with open("output.sdf", "w") as f:
    f.write(sdf_output)
```

### Command Line Interface

Parse an SDF file and output JSON:

```bash
sdf_timing_parse design.sdf
```

The JSON output includes the complete timing hierarchy and can be used for further processing or analysis.

## Requirements

- Python 3.11 or higher
- [Lark](https://github.com/lark-parser/lark) parser
- [Jinja2](https://jinja.palletsprojects.com/) templating engine

## Development

Install development dependencies:

```bash
uv pip install -e '.[dev]'
```

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=sdf_timing --cov-report=term-missing
```

Code formatting and linting:

```bash
ruff check src/ tests/
ruff format src/ tests/
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
