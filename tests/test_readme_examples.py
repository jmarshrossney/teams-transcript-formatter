"""Validate that README.md examples match actual formatter output."""

import re
import shlex
from collections.abc import Generator
from pathlib import Path

import pytest

from teams_transcript_formatter.formatter import format_transcript

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
EXAMPLE_VTT = ROOT / "example-transcript.vtt"


def _iter_readme_examples() -> Generator[tuple[str, str, int, str], None, None]:
    """Yield (title, command, head_lines, expected_output) for
    each sub-example under the ``## Examples`` heading."""
    content = README.read_text()

    m = re.search(r"## Examples\n(.*?)(?=\n## )", content, re.DOTALL)
    if not m:
        raise ValueError("Could not find '## Examples' section in README.md")
    section = m.group(1)

    # Each block starts with ``### Title`` and ends before the next ``###`` or EOF.
    # The regex captures the title line and everything up to (but not including)
    # the next ``###`` heading.
    blocks = re.findall(
        r"### (.+?)\n(.*?)(?=\n### |$)",
        section,
        re.DOTALL,
    )

    for title, body in blocks:
        title = title.strip()

        # Pull out the fenced code block
        code_match = re.search(r"```sh\n(.*?)\n```", body, re.DOTALL)
        if not code_match:
            raise ValueError(f"No code fence found in example: {title}")
        code = code_match.group(1)

        # Locate the ``$ head -N`` line (file-output examples)
        head_match = re.search(
            r"^\$ head -(\d+) transcript_formatted\.txt\n",
            code,
            re.MULTILINE,
        )

        if head_match:
            head_lines = int(head_match.group(1))
            header = code[: head_match.start()]
            expected_output = code[head_match.end() :].rstrip("\n")
            command = _join_command_lines(header)
        else:
            # Stdout output pattern: collect command lines, rest is output
            code_lines = code.strip().split("\n")
            cmd_end = 0
            i = 0
            while i < len(code_lines):
                stripped = code_lines[i].strip()
                if stripped.startswith("$ "):
                    cmd_end = i + 1
                    # Collect continuation lines (ending with backslash)
                    i += 1
                    while i < len(code_lines) and code_lines[i - 1].strip().endswith("\\"):
                        cmd_end = i + 1
                        i += 1
                else:
                    break
            header = "\n".join(code_lines[:cmd_end])
            command = _join_command_lines(header)
            expected_output = "\n".join(code_lines[cmd_end:]).rstrip("\n")
            head_lines = len(code_lines[cmd_end:])

        yield title, command, head_lines, expected_output


def _join_command_lines(header: str) -> str:
    """Join a multi-line shell command snippet into a single string."""
    parts: list[str] = []
    for line in header.strip().split("\n"):
        line = line.strip()
        if line.startswith("$ "):
            line = line[2:]
        if line.endswith("\\"):
            line = line[:-1].rstrip()
        parts.append(line)
    return " ".join(parts)


def _parse_flags(
    command: str,
) -> tuple[dict[str, str], dict[str, str], str | None]:
    """Extract --rename, --prefix, and --template flags from a command string."""
    args = shlex.split(command)

    renames: dict[str, str] = {}
    prefixes: dict[str, str] = {}
    template: str | None = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--rename":
            i += 1
            if i < len(args):
                k, v = args[i].split("=", 1)
                renames[k] = v
        elif arg == "--prefix":
            i += 1
            if i < len(args):
                k, v = args[i].split("=", 1)
                prefixes[k] = v
        elif arg == "--template":
            i += 1
            if i < len(args):
                template = args[i]
        i += 1

    return renames, prefixes, template


def _examples() -> list[dict]:
    """Collect all examples into a parametrize-able list."""
    result: list[dict] = []
    for title, command, head_lines, expected_output in _iter_readme_examples():
        renames, prefixes, template = _parse_flags(command)

        kwargs: dict = {}
        if renames:
            kwargs["rename"] = renames
        if prefixes:
            kwargs["prefix"] = prefixes
        if template is not None:
            kwargs["template"] = template

        result.append(
            {
                "title": title,
                "kwargs": kwargs,
                "head_lines": head_lines,
                "expected_output": expected_output,
            }
        )
    return result


def test_at_least_n_readme_examples():
    examples = _examples()
    assert len(examples) >= 6, (
        f"Expected at least 6 README examples, found {len(examples)}. "
        "Has the README format or regex changed?"
    )


@pytest.mark.parametrize(
    "example",
    _examples(),
    ids=lambda ex: ex["title"],
)
def test_readme_example_matches_output(example: dict) -> None:
    """Each example in README.md should produce the documented output."""
    vtt_content = EXAMPLE_VTT.read_text()
    result = format_transcript(vtt_content, **example["kwargs"])

    lines = result.split("\n")
    actual_head = "\n".join(lines[: example["head_lines"]])

    assert actual_head.rstrip("\n") == example["expected_output"], (
        f"Example '{example['title']}' output mismatch.\n"
        f"Expected:\n{example['expected_output']!r}\n\n"
        f"Got:\n{actual_head!r}"
    )
