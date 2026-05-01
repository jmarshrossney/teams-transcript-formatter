"""
Make Microsoft Teams interview transcripts human-readable.

This module is kept for backwards compatibility. The core logic lives in
`teams_transcript_formatter.formatter` and the CLI in
`teams_transcript_formatter.cli`.
"""

from teams_transcript_formatter.formatter import (  # noqa: F401
    BadInterviewerNameError,
    InterviewerNotFoundError,
    _extract_timestamp,
    _format_transcript,
    main,
)
