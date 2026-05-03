"""
CLI entry point using Typer.

Provides the `teams-transcript-formatter` command with --help/-h,
shell completion, and rich-formatted output.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from teams_transcript_formatter.formatter import (
    DEFAULT_TEMPLATE,
    process_files,
)
from teams_transcript_formatter.formatter import (
    format_transcript as fmt_transcript,
)

err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        from importlib.metadata import version

        print(version("teams-transcript-formatter"))
        raise typer.Exit()


def _parse_key_value(items: list[str], *, strip_value: bool = True) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Expected 'KEY=VALUE', got '{item}'")
        k, v = item.split("=", 1)
        k = k.strip()
        if k in mapping:
            raise ValueError(f"Duplicate key '{k}': each key must appear only once")
        mapping[k] = v.strip() if strip_value else v
    return mapping


app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(
    help="Turn `.vtt` audio transcripts from Microsoft Teams/Stream "
    "into human-readable plain text files.",
    no_args_is_help=True,
)
def format_transcript(
    files: Annotated[
        list[Path],
        typer.Argument(
            help="One or more `.vtt` files downloaded from Microsoft Teams/Stream.",
        ),
    ],
    rename: Annotated[
        list[str] | None,
        typer.Option(
            "--rename",
            help="Map original speaker names to display names: 'OriginalName=DisplayName'. "
            "Repeat for each speaker.",
        ),
    ] = None,
    prefix: Annotated[
        list[str] | None,
        typer.Option(
            "--prefix",
            help="Assign a prefix to each display name: 'DisplayName=>'. "
            "Use an empty value for no prefix: 'DisplayName='. "
            "Repeat for each speaker.",
        ),
    ] = None,
    template: Annotated[
        str | None,
        typer.Option(
            "--template",
            help="Python format string for output. "
            "Placeholders: {prefix}, {speaker}, {speech}, {timestamp}.",
        ),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "-o",
            "--output",
            help="Directory to save formatted `.txt` files. If not given, prints to stdout.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite existing output files instead of refusing.",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Suppress all non-error output.",
        ),
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = None,
) -> None:
    """Format Microsoft Teams meeting transcripts into readable text files."""

    # --- Resolve rename mapping ---
    _rename: dict[str, str] | None = None
    if rename:
        _rename = _parse_key_value(rename)

    # --- Resolve prefix mapping ---
    _prefix: dict[str, str] | None = None
    if prefix:
        _prefix = _parse_key_value(prefix, strip_value=False)

    # --- Resolve template ---
    _template: str = template or DEFAULT_TEMPLATE

    # --- Validate input files exist ---
    missing = [f for f in files if not f.exists()]
    if missing:
        for f in missing:
            err_console.print(f"[bold red]Error:[/bold red] File not found: [yellow]{f}[/yellow]")
        raise typer.Exit(code=1)

    # --- Warn about non-.vtt files ---
    non_vtt = [f for f in files if f.suffix.lower() != ".vtt"]
    if non_vtt:
        names = ", ".join(str(f) for f in non_vtt)
        err_console.print(f"[yellow]Warning:[/yellow] Non-.vtt extension(s): {names}")

    # --- Run ---
    try:
        if output_dir is not None:
            if not quiet:
                err_console.print(
                    f"[dim]Processing {len(files)} file(s), output: [cyan]{output_dir}[/cyan][/dim]"
                )
            results = process_files(
                files,
                output_dir,
                rename=_rename,
                prefix=_prefix,
                template=_template,
                force=force,
            )
            if not quiet:
                for infile, outfile in results:
                    err_console.print(f"{infile} -> {outfile}")
        else:
            if not quiet:
                for i, infile in enumerate(files):
                    err_console.print(f"[dim]Processing: [cyan]{infile}[/cyan][/dim]")
                    raw = infile.read_text()
                    formatted = fmt_transcript(
                        raw,
                        rename=_rename,
                        prefix=_prefix,
                        template=_template,
                    )
                    if len(files) > 1:
                        print(f"--- {infile} ---")
                    print(formatted)
                    if i < len(files) - 1:
                        print()
    except ValueError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except TypeError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except FileExistsError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
