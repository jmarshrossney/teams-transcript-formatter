"""
Make Microsoft Teams meeting transcripts human-readable.

Core formatting logic.
"""

import re
from collections.abc import Iterable
from pathlib import Path
from string import Formatter

DEFAULT_TEMPLATE = "{prefix}{speaker} | {speech} | {timestamp}"

_template_formatter = Formatter()


def _extract_timestamp(interval: str) -> str:
    start_time = interval.split(" ")[0]
    parts = re.split(r"[:.]", start_time)
    return f"{parts[0]}:{parts[1]}:{parts[2]}"


def _format_transcript(
    transcript: str,
    rename: dict[str, str] | None = None,
    prefix: dict[str, str] | None = None,
    template: str = DEFAULT_TEMPLATE,
) -> str:
    # Validate template placeholders
    try:
        _template_formatter.format(template, prefix="", speaker="", speech="", timestamp="")
    except KeyError as exc:
        raise ValueError(
            f"Invalid template placeholder {exc} in template: '{template}'. "
            f"Allowed placeholders: {{prefix}}, {{speaker}}, {{speech}}, {{timestamp}}"
        ) from exc

    # Normalize Windows-style line endings
    transcript = transcript.replace("\r\n", "\n").replace("\r", "\n")

    lines = transcript.split("\n")

    # Validate WEBVTT header
    if not lines or not lines[0].startswith("WEBVTT"):
        raise ValueError("Malformed or empty VTT file: expected the first line to contain 'WEBVTT'")

    # Parse cues: a cue starts when a line contains " --> "
    # (the timestamp interval separator), which is the reliable identifier.
    # This approach handles NOTE blocks, Style blocks, header metadata,
    # and arbitrary blank lines between cues.
    records = []
    has_cues = False
    i = 1  # skip WEBVTT line
    while i < len(lines):
        line = lines[i].strip()
        if " --> " in line:
            has_cues = True
            interval = line
            # Collect payload lines until blank line or EOF
            i += 1
            payload_lines = []
            while i < len(lines) and lines[i].strip():
                payload_lines.append(lines[i])
                i += 1
            raw = "\n".join(payload_lines)
            timestamp = _extract_timestamp(interval)

            # Extract speaker name from the opening <v> tag.
            # Assumption: speaker names never contain ">", which holds for
            # Microsoft Teams display names derived from Azure AD.
            speaker_match = re.match(r"<v ([^>]+)>", raw)
            if not speaker_match:
                continue
            speaker = speaker_match.group(1)

            # Strip all voice tags to get the speech text
            speech = re.sub(r"</?v[^>]*>", "", raw)
            speech = speech.replace("\n", " ").strip()
            if speech:
                records.append({"timestamp": timestamp, "speaker": speaker, "speech": speech})
        else:
            i += 1

    # Assign contiguous block IDs: increment whenever the speaker changes
    if not records:
        if not has_cues:
            raise ValueError("No speech chunks found after WEBVTT header")
        return ""
    block = 1
    records[0]["block"] = block
    for i in range(1, len(records)):
        if records[i]["speaker"] != records[i - 1]["speaker"]:
            block += 1
        records[i]["block"] = block

    # Merge adjacent records that belong to the same block
    merged = []
    current_block = None
    for r in records:
        if r["block"] != current_block:
            current_block = r["block"]
            merged.append(
                {"timestamp": r["timestamp"], "speaker": r["speaker"], "speech": r["speech"]}
            )
        else:
            merged[-1]["speech"] += " " + r["speech"]

    # Apply rename and prefix mappings
    _rename = rename or {}
    _prefix = prefix or {}
    for m in merged:
        m["speaker"] = _rename.get(m["speaker"], m["speaker"])
        m["prefix"] = _prefix.get(m["speaker"], "")

    # Format in human-readable way
    formatted_transcript = "\n\n".join(
        template.format(
            prefix=m["prefix"],
            speaker=m["speaker"],
            speech=m["speech"],
            timestamp=m["timestamp"],
        )
        for m in merged
    )

    return formatted_transcript


def main(
    files: list[Path],
    output_dir: Path,
    rename: dict[str, str] | None = None,
    prefix: dict[str, str] | None = None,
    template: str = DEFAULT_TEMPLATE,
    force: bool = False,
) -> list[tuple[Path, Path]]:
    """Format a given list of `.vtt` transcript files and save the results.

    Returns a list of ``(infile, outfile)`` pairs for each processed file.
    """

    if not isinstance(files, Iterable):
        raise TypeError(f"'files' must be an iterable, got {type(files)}")
    if not files:
        raise ValueError("'files' must contain at least one file path")
    for file in files:
        if not isinstance(file, Path):
            raise TypeError(f"Each file must be a Path, got {type(file)}")
    if not isinstance(output_dir, Path):
        raise TypeError(f"'output_dir' must be a Path, got {type(output_dir)}")

    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[tuple[Path, Path]] = []
    for infile in files:
        with infile.open("r") as f:
            raw_transcript = f.read()

        formatted_transcript = _format_transcript(
            raw_transcript, rename=rename, prefix=prefix, template=template
        )

        outfile = (output_dir / (infile.stem + "_formatted")).with_suffix(".txt")
        if outfile.exists() and not force:
            raise FileExistsError(
                f"Output file '{outfile}' already exists; pass --force to overwrite"
            )

        with outfile.open("w") as file:
            file.write(formatted_transcript)

        results.append((infile, outfile))

    return results
