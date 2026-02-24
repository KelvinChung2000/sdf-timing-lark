"""Typer CLI for parsing, emitting, and analyzing SDF timing files.

Provides commands to parse SDF files to JSON, emit JSON back to SDF,
display file summaries, compose path delays, verify expected delays,
and decompose delay segments.
"""

from __future__ import annotations

import json
from collections import Counter
from enum import StrEnum
from pathlib import Path  # noqa: TC003 - required at runtime by Typer
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from sdf_timing.export import to_dot
from sdf_timing.model import (
    BaseEntry,
    DelayPaths,
    EntryType,
    SDFFile,
    SDFHeader,
    Values,
)
from sdf_timing.pathgraph import (
    TimingGraph,
    compute_slack,
    critical_path,
    decompose_delay,
    rank_paths,
    verify_path,
)
from sdf_timing.sdf_lark_parser import parse_sdf
from sdf_timing.sdfparse import emit as sdf_emit

app = typer.Typer(no_args_is_help=True)
console = Console()


def _load_graph(sdf_file: Path) -> tuple[SDFFile, TimingGraph]:
    """Parse an SDF file and return the SDFFile and its TimingGraph.

    Parameters
    ----------
    sdf_file : Path
        Path to the SDF file.

    Returns
    -------
    tuple[SDFFile, TimingGraph]
        The parsed SDF file and its timing graph.
    """
    sdf = parse_sdf(sdf_file.read_text())
    return sdf, TimingGraph(sdf)


class OutputFormat(StrEnum):
    """Output format for the parse command."""

    json = "json"
    sdf = "sdf"


def _sdffile_from_dict(data: dict[str, object]) -> SDFFile:
    """Reconstruct an SDFFile from a dictionary produced by ``SDFFile.to_dict``.

    Parameters
    ----------
    data : dict[str, object]
        The dictionary representation of an SDF file.

    Returns
    -------
    SDFFile
        The reconstructed SDFFile object.
    """
    header = SDFHeader(**data.get("header", {}))  # type: ignore[arg-type]
    cells: dict[str, dict[str, dict[str, BaseEntry]]] = {}
    for cell_type, instances in data.get("cells", {}).items():  # type: ignore[union-attr]
        cells[cell_type] = {}
        for instance, entries in instances.items():
            cells[cell_type][instance] = {}
            for name, entry_dict in entries.items():
                entry_dict = dict(entry_dict)  # noqa: PLW2901
                # Convert delay_paths back to DelayPaths
                dp_dict = entry_dict.pop("delay_paths", None)
                delay_paths = None
                if dp_dict is not None:
                    delay_paths = DelayPaths(
                        **{
                            k: Values(**v) if v is not None else None
                            for k, v in dp_dict.items()
                        }
                    )
                # Convert type string back to EntryType
                entry_type = entry_dict.pop("type", "iopath")
                entry = BaseEntry(
                    **entry_dict,
                    type=EntryType(entry_type),
                    delay_paths=delay_paths,
                )
                cells[cell_type][instance][name] = entry
    return SDFFile(header=header, cells=cells)


def _delay_paths_from_json(json_str: str) -> DelayPaths:
    """Parse a JSON string into a DelayPaths object.

    Parameters
    ----------
    json_str : str
        JSON string representing delay path values, e.g.
        ``'{"nominal": {"min": 1.0, "avg": null, "max": 1.0}}'``.

    Returns
    -------
    DelayPaths
        The reconstructed DelayPaths object.
    """
    data: dict[str, dict[str, float | None] | None] = json.loads(json_str)
    return DelayPaths(
        **{k: Values(**v) if v is not None else None for k, v in data.items()}
    )


@app.command()
def parse(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF file to parse."),
    ],
    fmt: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format."),
    ] = OutputFormat.json,
    timescale: Annotated[
        str,
        typer.Option("--timescale", "-t", help="Timescale for SDF output."),
    ] = "1ps",
) -> None:
    """Parse an SDF file and output as JSON or SDF."""
    content = sdf_file.read_text()
    sdf = parse_sdf(content)

    if fmt == OutputFormat.json:
        typer.echo(json.dumps(sdf.to_dict(), indent=2))
    else:
        typer.echo(sdf_emit(sdf, timescale=timescale))


@app.command()
def emit(
    json_file: Annotated[
        Path,
        typer.Argument(help="Path to the JSON file to convert."),
    ],
    timescale: Annotated[
        str,
        typer.Option("--timescale", "-t", help="Timescale for SDF output."),
    ] = "1ps",
) -> None:
    """Convert a JSON file (produced by ``parse --format json``) back to SDF."""
    data = json.loads(json_file.read_text())
    sdf = _sdffile_from_dict(data)
    typer.echo(sdf_emit(sdf, timescale=timescale))


@app.command()
def info(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF file to inspect."),
    ],
) -> None:
    """Show a summary of an SDF file (header, cell count, entry types)."""
    content = sdf_file.read_text()
    sdf = parse_sdf(content)

    # Header table
    header_table = Table(title="SDF Header")
    header_table.add_column("Field", style="cyan")
    header_table.add_column("Value", style="green")
    for key, value in sdf.header.items():
        header_table.add_row(key, str(value))
    console.print(header_table)

    # Cell summary
    instances: list[str] = []
    entry_type_counts: Counter[str] = Counter()

    for _cell_type, cell_instances in sdf.cells.items():
        for instance_name, entries in cell_instances.items():
            instances.append(instance_name)
            for _entry_name, entry in entries.items():
                entry_type_counts[str(entry.type)] += 1

    summary_table = Table(title="Cell Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    summary_table.add_row("Total cells", str(len(instances)))
    console.print(summary_table)

    # Entry type breakdown
    type_table = Table(title="Entry Types")
    type_table.add_column("Type", style="cyan")
    type_table.add_column("Count", style="green")
    for entry_type, count in sorted(entry_type_counts.items()):
        type_table.add_row(entry_type, str(count))
    console.print(type_table)

    # Instance list
    instance_table = Table(title="Instances")
    instance_table.add_column("Instance", style="cyan")
    for inst in instances:
        instance_table.add_row(inst)
    console.print(instance_table)


@app.command()
def compose(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF file."),
    ],
    source: Annotated[
        str,
        typer.Argument(help="Source pin name."),
    ],
    sink: Annotated[
        str,
        typer.Argument(help="Sink pin name."),
    ],
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show full path details."),
    ] = False,
) -> None:
    """Compose delays along all paths from source to sink."""
    _sdf, graph = _load_graph(sdf_file)

    if verbose:
        paths = graph.find_paths(source, sink)
        for i, path in enumerate(paths):
            typer.echo(f"Path {i + 1}:")
            for edge in path:
                typer.echo(
                    f"  {edge.source} -> {edge.sink}"
                    f" ({edge.entry_type}, {edge.cell_type})"
                )
            composed = graph.compose_delay(path)
            typer.echo(f"  Composed: {json.dumps(composed.to_dict(), indent=2)}")
    else:
        delays = graph.compose(source, sink)
        for i, delay in enumerate(delays):
            typer.echo(f"Path {i + 1}: {json.dumps(delay.to_dict(), indent=2)}")


@app.command()
def verify(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF file."),
    ],
    source: Annotated[
        str,
        typer.Argument(help="Source pin name."),
    ],
    sink: Annotated[
        str,
        typer.Argument(help="Sink pin name."),
    ],
    expected: Annotated[
        str,
        typer.Option(
            "--expected",
            help=(
                "Expected delay as a JSON string, e.g. "
                '\'{"nominal": {"min": 1.0, "avg": null, "max": 1.0}}\''
            ),
        ),
    ],
    tolerance: Annotated[
        float,
        typer.Option("--tolerance", help="Absolute tolerance for comparison."),
    ] = 1e-9,
) -> None:
    """Verify that composed path delay matches an expected value."""
    _sdf, graph = _load_graph(sdf_file)

    expected_delay = _delay_paths_from_json(expected)
    result = verify_path(graph, source, sink, expected_delay, tolerance=tolerance)

    if result.passed:
        typer.echo("PASS")
    else:
        typer.echo("FAIL")

    typer.echo(f"Expected: {json.dumps(expected_delay.to_dict(), indent=2)}")
    for i, actual in enumerate(result.actual):
        typer.echo(f"Actual path {i + 1}: {json.dumps(actual.to_dict(), indent=2)}")

    raise typer.Exit(code=0 if result.passed else 1)


@app.command()
def decompose(
    total: Annotated[
        str,
        typer.Option(
            "--total",
            help=(
                "Total delay as a JSON string, e.g. "
                '\'{"nominal": {"min": 2.0, "avg": null, "max": 2.0}}\''
            ),
        ),
    ],
    known: Annotated[
        str,
        typer.Option(
            "--known",
            help=(
                "Known delay segment as a JSON string, e.g. "
                '\'{"nominal": {"min": 1.0, "avg": null, "max": 1.0}}\''
            ),
        ),
    ],
) -> None:
    """Compute the unknown delay segment from total and known delays."""
    total_delay = _delay_paths_from_json(total)
    known_delay = _delay_paths_from_json(known)
    result = decompose_delay(total_delay, known_delay)
    typer.echo(json.dumps(result.to_dict(), indent=2))


@app.command(name="critical-path")
def critical_path_cmd(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF file."),
    ],
    source: Annotated[
        str,
        typer.Argument(help="Source pin name."),
    ],
    sink: Annotated[
        str,
        typer.Argument(help="Sink pin name."),
    ],
    field: Annotated[
        str,
        typer.Option("--field", help="Delay field (nominal, fast, slow, …)."),
    ] = "slow",
    metric: Annotated[
        str,
        typer.Option("--metric", help="Metric (min, avg, max)."),
    ] = "max",
) -> None:
    """Find the critical (slowest) path from source to sink."""
    _sdf, graph = _load_graph(sdf_file)

    cp = critical_path(graph, source, sink, field, metric)
    if cp is None:
        typer.echo("No path found.")
        raise typer.Exit(code=1)

    typer.echo(f"Critical path scalar ({field}.{metric}): {cp.scalar}")
    for edge in cp.edges:
        scalar = edge.delay.get_scalar(field, metric)
        typer.echo(f"  {edge.source} -> {edge.sink}  {scalar}")
    typer.echo(f"Delay: {json.dumps(cp.delay.to_dict(), indent=2)}")


@app.command(name="rank-paths")
def rank_paths_cmd(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF file."),
    ],
    source: Annotated[
        str,
        typer.Argument(help="Source pin name."),
    ],
    sink: Annotated[
        str,
        typer.Argument(help="Sink pin name."),
    ],
    field: Annotated[
        str,
        typer.Option("--field", help="Delay field (nominal, fast, slow, …)."),
    ] = "slow",
    metric: Annotated[
        str,
        typer.Option("--metric", help="Metric (min, avg, max)."),
    ] = "max",
    descending: Annotated[
        bool,
        typer.Option("--descending/--ascending", help="Sort order."),
    ] = True,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of paths to show."),
    ] = 0,
) -> None:
    """Rank all paths from source to sink by scalar delay."""
    _sdf, graph = _load_graph(sdf_file)

    ranked = rank_paths(graph, source, sink, field, metric, descending)
    if limit > 0:
        ranked = ranked[:limit]

    if not ranked:
        typer.echo("No paths found.")
        raise typer.Exit(code=1)

    for i, rp in enumerate(ranked):
        hops = " -> ".join([rp.edges[0].source] + [e.sink for e in rp.edges])
        typer.echo(f"#{i + 1}  scalar={rp.scalar}  {hops}")


@app.command()
def slack(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF file."),
    ],
    source: Annotated[
        str,
        typer.Argument(help="Source pin name."),
    ],
    sink: Annotated[
        str,
        typer.Argument(help="Sink pin name."),
    ],
    period: Annotated[
        float,
        typer.Argument(help="Clock period or timing constraint."),
    ],
    field: Annotated[
        str,
        typer.Option("--field", help="Delay field (nominal, fast, slow, …)."),
    ] = "slow",
    metric: Annotated[
        str,
        typer.Option("--metric", help="Metric (min, avg, max)."),
    ] = "max",
) -> None:
    """Compute slack for the critical path: period - critical_delay."""
    _sdf, graph = _load_graph(sdf_file)

    result = compute_slack(graph, source, sink, period, field, metric)
    if result is None:
        typer.echo("No path found or scalar is None.")
        raise typer.Exit(code=1)

    typer.echo(f"Slack: {result}")
    if result < 0:
        typer.echo("TIMING VIOLATION")


@app.command()
def dot(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF file."),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file (default: stdout)."),
    ] = None,
    highlight_source: Annotated[
        str | None,
        typer.Option("--highlight-source", help="Source pin for highlight."),
    ] = None,
    highlight_sink: Annotated[
        str | None,
        typer.Option("--highlight-sink", help="Sink pin for critical path highlight."),
    ] = None,
    cluster: Annotated[
        bool,
        typer.Option("--cluster/--no-cluster", help="Cluster nodes by instance."),
    ] = False,
    field: Annotated[
        str,
        typer.Option("--field", help="Delay field (nominal, fast, slow, …)."),
    ] = "slow",
    metric: Annotated[
        str,
        typer.Option("--metric", help="Metric (min, avg, max)."),
    ] = "max",
) -> None:
    """Export the timing graph as DOT (Graphviz) format."""
    _sdf, graph = _load_graph(sdf_file)

    highlight = None
    if highlight_source is not None and highlight_sink is not None:
        highlight = critical_path(
            graph, highlight_source, highlight_sink, field, metric
        )

    dot_str = to_dot(
        graph,
        highlight_path=highlight,
        cluster_by_instance=cluster,
        field=field,
        metric=metric,
    )

    if output is not None:
        output.write_text(dot_str)
        typer.echo(f"Written to {output}")
    else:
        typer.echo(dot_str)


@app.command()
def annotate(
    sdf_file: Annotated[
        Path,
        typer.Argument(help="Path to the SDF timing file."),
    ],
    verilog_file: Annotated[
        Path,
        typer.Argument(help="Path to the Verilog cell library file."),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file (default: stdout)."),
    ] = None,
    field: Annotated[
        str,
        typer.Option("--field", help="Delay field (nominal, fast, slow, ...)."),
    ] = "slow",
    metric: Annotated[
        str,
        typer.Option("--metric", help="Metric (min, avg, max)."),
    ] = "max",
) -> None:
    """Annotate a Verilog cell library with SDF timing specify blocks."""
    from sdf_timing.annotate import annotate_verilog

    result = annotate_verilog(
        sdf_path=sdf_file,
        verilog_path=verilog_file,
        output_path=output,
        field_name=field,
        metric=metric,
    )

    if output is None:
        typer.echo(result)
    else:
        typer.echo(f"Written to {output}")


def main() -> None:
    """Entry point for the SDF timing CLI."""
    app()
