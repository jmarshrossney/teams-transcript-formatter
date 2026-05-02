"""
CLI entry point using Typer.

Provides the `teams-transcript-formatter` command with --help/-h,
interactive prompting, shell completion, and rich-formatted output.
"""

import os
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from teams_transcript_formatter.formatter import (
    BadInterviewerNameError,
    InterviewerNotFoundError,
    _format_transcript,
    main,
)

err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        from importlib.metadata import version

        print(version("teams-transcript-formatter"))
        raise typer.Exit()


app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(
    help="Turn `.vtt` audio transcripts from Microsoft Teams/Stream "
    "into human-readable plain text files.",
)
def format_transcript(
    files: Annotated[
        list[Path] | None,
        typer.Argument(
            help="One or more `.vtt` files downloaded from Microsoft Teams/Stream.",
        ),
    ] = None,
    interviewer: Annotated[
        str | None,
        typer.Option(
            "-i",
            "--interviewer",
            help="Name of the interviewer as it appears in the transcript.",
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
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Print additional progress information.",
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
    no_interactive: Annotated[
        bool,
        typer.Option(
            "--no-interactive",
            help="Disable interactive prompts; fail on missing arguments.",
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
    """Format Microsoft Teams interview transcripts into readable text files."""

    # --- Resolve interviewer ---
    _interviewer: str
    if interviewer:
        _interviewer = interviewer
    elif no_interactive:
        err_console.print(
            "[bold red]Error:[/bold red] "
            "An interviewer name is required (use [cyan]-i/--interviewer[/cyan] "
            "or run without [cyan]--no-interactive[/cyan] to be prompted)."
        )
        raise typer.Exit(code=1)
    else:
        _interviewer = typer.prompt("Enter the interviewer's name as it appears in the transcript")
        if not _interviewer.strip():
            err_console.print("[bold red]Error:[/bold red] Interviewer name cannot be empty.")
            raise typer.Exit(code=1)

    # --- Resolve input files ---
    _files: list[Path]
    if files:
        _files = files
    elif no_interactive:
        err_console.print("[bold red]Error:[/bold red] At least one `.vtt` file path is required.")
        raise typer.Exit(code=1)
    else:
        raw = typer.prompt("Enter one or more .vtt file paths (space or comma separated)")
        _files = [Path(p.strip()) for p in raw.replace(",", " ").split() if p.strip()]
        if not _files:
            err_console.print("[bold red]Error:[/bold red] No valid file paths provided.")
            raise typer.Exit(code=1)

    # --- Validate input files exist ---
    missing = [f for f in _files if not f.exists()]
    if missing:
        for f in missing:
            err_console.print(f"[bold red]Error:[/bold red] File not found: [yellow]{f}[/yellow]")
        raise typer.Exit(code=1)

    # --- Warn about non-.vtt files ---
    non_vtt = [f for f in _files if f.suffix.lower() != ".vtt"]
    if non_vtt and verbose:
        names = ", ".join(str(f) for f in non_vtt)
        err_console.print(f"[yellow]Warning:[/yellow] Non-.vtt extension(s): {names}")

    # --- Run ---
    try:
        if output_dir is not None:
            # Write to files in output directory
            if quiet:
                with open(os.devnull, "w") as devnull:
                    old_stdout = sys.stdout
                    sys.stdout = devnull
                    try:
                        main(_files, output_dir, _interviewer, force=force)
                    finally:
                        sys.stdout = old_stdout
            else:
                if verbose:
                    err_console.print(
                        f"[dim]Processing {len(_files)} file(s), "
                        f"interviewer: [cyan]{_interviewer}[/cyan], "
                        f"output: [cyan]{output_dir}[/cyan][/dim]"
                    )
                main(_files, output_dir, _interviewer, force=force)
        else:
            # Print to stdout
            if not quiet:
                for i, infile in enumerate(_files):
                    if verbose:
                        err_console.print(f"[dim]Processing: [cyan]{infile}[/cyan][/dim]")
                    raw = infile.read_text()
                    formatted = _format_transcript(raw, _interviewer)
                    if len(_files) > 1:
                        print(f"--- {infile} ---")
                    print(formatted)
                    if i < len(_files) - 1:
                        print()
    except ValueError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except TypeError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except BadInterviewerNameError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except InterviewerNotFoundError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except FileExistsError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
