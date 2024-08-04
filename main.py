"""
Make Microsoft Teams inverview transcripts human-readable.
"""

from argparse import ArgumentParser
from collections.abc import Iterable
from pathlib import Path
import re

from dotenv import dotenv_values
import pandas as pd


class BadInterviewerName(Exception):
    pass



parser = ArgumentParser(
    prog="format_transcript",
    description="Turns a `.vtt` audio transcript from Microsoft Teams/Stream into a human-readable plain text file.",
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


def _format_transcript(transcript: str, interviewer: str) -> str:

    # Strip first line which should just contain `WEBVTT`, then
    # split the transcript into chunks of speech
    chunks = transcript.split("\n\n")[1:]
    array = [chunk.split("\n", maxsplit=2) for chunk in chunks]

    df = pd.DataFrame(array, columns=["hash", "interval", "raw"])

    # Replace hh:mm:ss.ff timestamp with mm:ss
    df["timestamp"] = df["interval"].apply(
        lambda s: ":".join(re.split(r":|\.", re.split(" ", s)[0])[1:3])
    )

    # Strip html tags and separate speaker/speech
    df["raw"] = df["raw"].apply(lambda s: re.sub("<v |</v>", "", s))
    df[["speaker", "speech"]] = df["raw"].str.split(">", n=1, expand=True)

    # Replace newlines with spaces and drop rows containing no speech
    df["speech"] = df["speech"].str.replace("\n", " ")
    df = df[df["speech"].str.strip().astype(bool)]

    df.drop(columns=["hash", "interval", "raw"], inplace=True)

    # Merge adjacent blocks with the same speaker using a Boolean flag
    # to indicate that the speaker has changed, then convert flag to
    # integer increment using cumsum trick
    df["block"] = (df["speaker"] != df["speaker"].shift()).cumsum()
    df = df.groupby("block").agg(
        {"timestamp": "first", "speaker": "first", "speech": lambda x: " ".join(x)}
    )

    # Check that there are 2 speakers, one of which is INTERVIEWER
    speakers = df["speaker"].unique()
    assert len(speakers) == 2
    if interviewer not in speakers:
        raise BadInterviewerName(
            "Interviewer '{INTERVIEWER}' is not present in this transcript"
        )

    # Replace names with 'Interviewer' and 'Student'
    df["speaker"] = df["speaker"].apply(
        lambda name: "Interviewer" if name == interviewer else "Student"
    )

    # Format in human-readable way, appropriate for annotation
    formatted_transcript = "\n\n".join(
        [
            f"{speaker} ({time}):\n\t{speech}"
            for (time, speaker, speech) in df.itertuples(index=False, name=None)
        ]
    )

    return formatted_transcript


def main(files: list[Path], output_dir: Path) -> None:
    """Format a given list of `.vtt` transcript files and save the results."""

    assert isinstance(files, Iterable)
    assert len(files) > 0
    assert all([isinstance(file, Path) for file in files])
    assert isinstance(output_dir, Path)

    output_dir.mkdir(parents=True, exist_ok=True)

    config = dotenv_values(".env")
    try:
        interviewer = config["INTERVIEWER"]
    except KeyError as e:
        raise BadInterviewerName(
            "Please set `INTERVIEWER='Interviewer Name'` in `.env`"
        ) from e

    if not interviewer:
        raise BadInterviewerName(
            "Please set `INTERVIEWER` to the name of the interviewer as it appears in the transcript"
        )

    for infile in files:

        # Read file as single string (assume it's sufficiently small)
        with infile.open("r") as f:
            raw_transcript = f.read()

        formatted_transcript = _format_transcript(raw_transcript, interviewer)

        outfile = (output_dir / (infile.stem + "_formatted")).with_suffix(".txt")
        assert not outfile.exists()

        with outfile.open("w") as file:
            file.write(formatted_transcript)

        print(f"{infile} -> {outfile}")


def cli():
    """Wrapper around `main` that parses arguments from the command-line."""
    args = parser.parse_args()
    main(args.files, args.output)


if __name__ == "__main__":
    cli()
