"""
Make Microsoft Teams interview transcripts human-readable.

Core formatting logic — no CLI dependency.
"""

import re
from collections.abc import Iterable
from pathlib import Path


class BadInterviewerNameError(Exception):
    pass


class InterviewerNotFoundError(Exception):
    pass


def _extract_timestamp(interval: str) -> str:
    start_time = interval.split(" ")[0]
    parts = re.split(r"[:.]", start_time)
    return f"{parts[1]}:{parts[2]}"


def _format_transcript(transcript: str, interviewer: str) -> str:
    # Normalize Windows-style line endings
    transcript = transcript.replace("\r\n", "\n").replace("\r", "\n")

    # Strip first line which should just contain `WEBVTT`, then
    # split the transcript into chunks of speech
    chunks = transcript.split("\n\n")
    if not chunks or not chunks[0].startswith("WEBVTT"):
        raise ValueError("Malformed or empty VTT file: expected the first line to contain 'WEBVTT'")
    chunks = chunks[1:]
    if not chunks:
        raise ValueError("No speech chunks found after WEBVTT header")

    # Parse each chunk into a record in a single pass
    records = []
    for chunk in chunks:
        _hash, interval, raw = chunk.split("\n", maxsplit=2)
        timestamp = _extract_timestamp(interval)
        raw = re.sub("<v |</v>", "", raw)
        speaker, speech = raw.split(">", 1)
        speech = speech.replace("\n", " ").strip()
        if speech:
            records.append({"timestamp": timestamp, "speaker": speaker, "speech": speech})

    # Assign contiguous block IDs: increment whenever the speaker changes
    if not records:
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

    # Check that there are 2 speakers, one of which is INTERVIEWER
    speakers = {m["speaker"] for m in merged}
    if len(speakers) != 2:
        raise InterviewerNotFoundError(
            "Expected exactly 2 speakers in the transcript, "
            f"but found {len(speakers)}: {', '.join(speakers)}. "
            "This tool only supports one-to-one (2-person) meetings."
        )
    if interviewer not in speakers:
        raise BadInterviewerNameError(
            f"Interviewer '{interviewer}' is not present in this transcript. "
            f"Available speakers: {', '.join(speakers)}"
        )

    # Replace names with 'Interviewer' and 'Student', and add prefix
    for m in merged:
        m["speaker"] = "Interviewer" if m["speaker"] == interviewer else "Student"
        m["prefix"] = ">" if m["speaker"] == "Interviewer" else "<"

    # Format in human-readable way, appropriate for annotation
    # TODO: replace hard-coded f-string with template file
    formatted_transcript = "\n\n".join(
        f"{m['prefix']} {m['speaker']} | {m['speech']} | {m['timestamp']}" for m in merged
    )

    return formatted_transcript


def main(files: list[Path], output_dir: Path, interviewer: str, force: bool = False) -> None:
    """Format a given list of `.vtt` transcript files and save the results."""

    if not isinstance(files, Iterable):
        raise TypeError(f"'files' must be an iterable, got {type(files)}")
    if not files:
        raise ValueError("'files' must contain at least one file path")
    for file in files:
        if not isinstance(file, Path):
            raise TypeError(f"Each file must be a Path, got {type(file)}")
    if not isinstance(output_dir, Path):
        raise TypeError(f"'output_dir' must be a Path, got {type(output_dir)}")
    if not interviewer or not isinstance(interviewer, str):
        raise TypeError(f"'interviewer' must be a non-empty str, got {interviewer!r}")

    output_dir.mkdir(parents=True, exist_ok=True)

    for infile in files:
        # Read file as single string (assume it's sufficiently small)
        with infile.open("r") as f:
            raw_transcript = f.read()

        formatted_transcript = _format_transcript(raw_transcript, interviewer)

        outfile = (output_dir / (infile.stem + "_formatted")).with_suffix(".txt")
        if outfile.exists() and not force:
            raise FileExistsError(
                f"Output file '{outfile}' already exists; pass --force to overwrite"
            )

        with outfile.open("w") as file:
            file.write(formatted_transcript)

        print(f"{infile} -> {outfile}")
