# Teams transcript formatter

[![PyPI version](https://badge.fury.io/py/teams-transcript-formatter.svg)](https://pypi.org/project/teams-transcript-formatter/)

The purpose of this package is to make Microsoft Teams meeting transcripts easier to read and analyse using tools such as [QualCoder](https://github.com/ccbogel/QualCoder).

It processes `.vtt` transcripts downloaded from Microsoft Teams/Stream, merges adjacent blocks from the same speaker, and outputs a clean, formatted text file. Speaker names can optionally be renamed and assigned prefixes, and the output format is customisable via a template.


## Installation

This package is available on PyPI.

### Run with `uvx`

No installation required — run it once-off with [`uvx`](https://docs.astral.sh/uv/guides/tools/#running-tools):

```sh
uvx teams-transcript-formatter transcript.vtt
```

### Install with `pip` or `uv`

Install from PyPI:

```sh
pip install teams-transcript-formatter
# or
uv tool install teams-transcript-formatter
```

After installation, `teams-transcript-formatter` will be available on your PATH:

```sh
teams-transcript-formatter transcript.vtt
```

### From source

If you want to make changes to the source code you can clone the repository and install in editable mode:

```sh
git clone https://github.com/jmarshrossney/teams-transcript-formatter
cd teams-transcript-formatter
uv sync
```


## Usage

### Command-line tool

The `teams-transcript-formatter` script takes one or more `.vtt` files and produces formatted files with the naming convention `<original_stem>_formatted.txt`. Optionally, you may also specify a directory for the formatted files using the `-o` flag (the default is the current working directory).

```sh
# Basic: keep original speaker names, default formatting
teams-transcript-formatter transcript.vtt

# Rename speakers (e.g. for an interview)
teams-transcript-formatter \
    --rename "John Smith=Interviewer" --rename "Jane Doe=Student" \
    --prefix "Interviewer=> " --prefix "Student=< " \
    transcript.vtt

# Custom output format
teams-transcript-formatter \
    --rename "John Smith=JS" --rename "Jane Doe=JD" \
    --template "{speaker}: {speech} [{timestamp}]" \
    transcript.vtt
```

Run `teams-transcript-formatter -h` for full guidance, including shell completion.

### Flags

| Flag | Description |
|------|-------------|
| `--rename` | Map original speaker names to display names: `"OriginalName=DisplayName"`. Repeat for each speaker. |
| `--prefix` | Assign a prefix to each display name: `"DisplayName=>"`. Repeat for each speaker. |
| `--template` | Python format string for output. Placeholders: `{prefix}`, `{speaker}`, `{speech}`, `{timestamp}`. |
| `-o`, `--output` | Output directory for `.txt` files (default: `.`) |
| `--force` | Overwrite existing output files instead of refusing |
| `-q`, `--quiet` | Suppress all non-error output |
| `--version` | Show the version and exit |
| `-h`, `--help` | Show the help message and exit |



## Examples

Say we have a Teams transcript file named `transcript.vtt`:

```sh
$ head -11 transcript.vtt
WEBVTT

91b3f3c3-44c6-4a8b-8c0a-add105d816bd/32-0
00:00:10.087 --> 00:00:13.130
<v John Smith>Hello, I am the interviewer.</v>

91b3f3c3-44c6-4a8b-8c0a-add105d816bd/32-1
00:00:13.130 --> 00:00:16.270
<v Jane Doe>Nice. I am the student being interviewed,
and I have many things to say.</v>

```

### Default format

No flags — original speaker names and default template.

```sh
$ teams-transcript-formatter transcript.vtt
$ head -3 transcript_formatted.txt
John Smith | Hello, I am the interviewer. | 00:00:10

Jane Doe | Nice. I am the student being interviewed, and I have many things to say. | 00:00:13
```

### Rename speakers

Map original names to display names with `--rename`.

```sh
$ teams-transcript-formatter \
    --rename "John Smith=Interviewer" --rename "Jane Doe=Student" \
    transcript.vtt
$ head -3 transcript_formatted.txt
Interviewer | Hello, I am the interviewer. | 00:00:10

Student | Nice. I am the student being interviewed, and I have many things to say. | 00:00:13
```

### Add prefixes

Combine `--rename` with `--prefix` to visually distinguish speakers. Prefixes are keyed on the **display name** (after renaming).

```sh
$ teams-transcript-formatter \
    --rename "John Smith=Interviewer" --rename "Jane Doe=Student" \
    --prefix "Interviewer=> " --prefix "Student=< " \
    transcript.vtt
$ head -3 transcript_formatted.txt
> Interviewer | Hello, I am the interviewer. | 00:00:10

< Student | Nice. I am the student being interviewed, and I have many things to say. | 00:00:13
```

### Custom output template

Control the output format with `--template`. Available placeholders: `{prefix}`, `{speaker}`, `{speech}`, `{timestamp}`.

```sh
$ teams-transcript-formatter \
    --rename "John Smith=JS" --rename "Jane Doe=JD" \
    --template "[{timestamp}] {speaker}: {speech}" \
    transcript.vtt
$ head -3 transcript_formatted.txt
[00:00:10] JS: Hello, I am the interviewer.

[00:00:13] JD: Nice. I am the student being interviewed, and I have many things to say.
```

### Full customisation

All three flags together — rename, prefix, and template.

```sh
$ teams-transcript-formatter \
    --rename "John Smith=Interviewer" --rename "Jane Doe=Student" \
    --prefix "Interviewer=> " --prefix "Student=< " \
    --template "{prefix}{speaker}: {speech} [{timestamp}]" \
    transcript.vtt
$ head -3 transcript_formatted.txt
> Interviewer: Hello, I am the interviewer. [00:00:10]

< Student: Nice. I am the student being interviewed, and I have many things to say. [00:00:13]
```

### Selective prefixes

Pass an empty value to `--prefix` to suppress the prefix for a given speaker.

```sh
$ teams-transcript-formatter \
    --rename "John Smith=Interviewer" --rename "Jane Doe=Student" \
    --prefix "Interviewer=> " --prefix "Student=" \
    transcript.vtt
$ head -3 transcript_formatted.txt
> Interviewer | Hello, I am the interviewer. | 00:00:10

Student | Nice. I am the student being interviewed, and I have many things to say. | 00:00:13
```


## Privacy

Speaker names can be replaced using the `--rename` flag. All other redactions of sensitive and identifiable information must be performed before running this script.

Tip: the auto-generated transcripts can be edited in-situ using the Microsoft Stream app.

Remember to delete the original transcripts after running this script!


## Roadmap & contributing

There are some fairly simple additions that would make this more generally useful:

- [x] Handle meetings with >2 participants
- [x] User can configure how names are handled
- [x] Configure the output format, e.g. using a template
- [ ] Handle Zoom meetings
- [ ] Output to different file formats (realistically, `.docx` would probably be the most useful to folks.)

Suggestions for improvements are welcome.
Contributions even more so!
Just open an issue or pull request.
