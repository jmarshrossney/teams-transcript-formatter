"""Make Microsoft Teams meeting transcripts human-readable."""

from teams_transcript_formatter.formatter import (
    DEFAULT_TEMPLATE,
    extract_timestamp,
    format_transcript,
    process_files,
)

__all__ = [
    "DEFAULT_TEMPLATE",
    "extract_timestamp",
    "format_transcript",
    "process_files",
]
