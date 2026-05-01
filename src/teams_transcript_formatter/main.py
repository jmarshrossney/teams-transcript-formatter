"""
Make Microsoft Teams interview transcripts human-readable.
"""

import re
import sys
from argparse import ArgumentParser
from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pandas as pd


class BadInterviewerNameError(Exception):
    pass


class InterviewerNotFoundError(Exception):
    pass


def _extract_timestamp(interval: str) -> str:
    start_time = interval.split(" ")[0]
    parts = re.split(r"[:.]", start_time)
    return f"{parts[1]}:{parts[2]}"


parser = ArgumentParser(
    prog="format_transcript",
    description=(
        "Turn a `.vtt` audio transcript from Microsoft Teams/Stream "
        "into a human-readable plain text file."
    ),
)

parser.add_argument(
    "files",
    type=Path,
    nargs="+",  # at least one file must be provided
    help="one or more `.vtt` files downloaded from Microsoft Teams/Stream",
)
parser.add_argument(
    "-o",
    "--output",
    type=Path,
    help="directory in which to save the formatted `.txt` files",
    default=".",
)
parser.add_argument(
    "-i",
    "--interviewer",
    type=str,
    help="name of interviewer as it appears in the transcript",
)


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
    array = [chunk.split("\n", maxsplit=2) for chunk in chunks]

    df = pd.DataFrame(array, columns=["hash", "interval", "raw"])

    # Replace hh:mm:ss.ff timestamp with mm:ss
    df["timestamp"] = df["interval"].apply(_extract_timestamp)

    # Strip html tags and separate speaker/speech
    df["raw"] = df["raw"].apply(lambda s: re.sub("<v |</v>", "", s))
    df[["speaker", "speech"]] = df["raw"].str.split(">", n=1, expand=True)

    # Replace newlines with spaces and drop rows containing no speech
    df["speech"] = df["speech"].str.replace("\n", " ").str.strip()
    df = df[df["speech"].astype(bool)]

    df.drop(columns=["hash", "interval", "raw"], inplace=True)

    # Merge adjacent blocks with the same speaker using a Boolean flag
    # to indicate that the speaker has changed, then convert flag to
    # integer increment using cumsum trick
    speaker = cast(pd.Series, df["speaker"])
    df["block"] = (speaker != speaker.shift()).cumsum()
    df = df.groupby("block").agg(
        {"timestamp": "first", "speaker": "first", "speech": lambda x: " ".join(x)}
    )

    # Check that there are 2 speakers, one of which is INTERVIEWER
    speakers_after_groupby = cast(pd.Series, df["speaker"])
    speakers = speakers_after_groupby.unique()
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

    # Replace names with 'Interviewer' and 'Student'
    df.loc[:, "speaker"] = speakers_after_groupby.apply(
        lambda name: "Interviewer" if name == interviewer else "Student"
    )

    # Add '<' or '>' prefix
    renamed_speaker = cast(pd.Series, df["speaker"])
    df.loc[:, "prefix"] = renamed_speaker.apply(lambda name: ">" if name == "Interviewer" else "<")

    # Format in human-readable way, appropriate for annotation
    # TODO: replace hard-coded f-string with template file
    formatted_transcript = "\n\n".join(
        [
            f"{prefix} {speaker} | {speech} | {time}"
            for (time, speaker, speech, prefix) in df.itertuples(index=False, name=None)
        ]
    )

    return formatted_transcript


def main(files: list[Path], output_dir: Path, interviewer: str) -> None:
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
        if outfile.exists():
            raise FileExistsError(f"Output file '{outfile}' already exists; refusing to overwrite")

        with outfile.open("w") as file:
            file.write(formatted_transcript)

        print(f"{infile} -> {outfile}")


def cli():
    """Wrapper around `main` that parses arguments from the command-line."""
    args = parser.parse_args()
    try:
        main(args.files, args.output, args.interviewer)
    except (BadInterviewerNameError, InterviewerNotFoundError, FileExistsError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli()
