# Teams transcript formatter

The purpose of this package is to make Microsoft Teams meeting transcripts easier to read and analyse using tools such as [QualCoder](https://github.com/ccbogel/QualCoder).

It processes `.vtt` transcripts downloaded from Microsoft Teams/Stream, merges adjacent blocks from the same speaker, and outputs a clean, formatted text file. Speaker names can optionally be renamed and assigned prefixes, and the output format is customisable via a template.


## Installation

This package is not yet on PyPI, so you must install directly from the GitHub repository.

### Run with `uvx`

No installation required — run it once-off with [`uvx`](https://docs.astral.sh/uv/guides/tools/#running-tools):

```sh
uvx --from git+https://github.com/jmarshrossney/teams-transcript-formatter teams-transcript-formatter transcript.vtt
```

### Install as a tool with `uv`

Install globally with `uv tool install`:

```sh
uv tool install git+https://github.com/jmarshrossney/teams-transcript-formatter
```

After installation, `teams-transcript-formatter` will be available on your PATH:

```sh
teams-transcript-formatter transcript.vtt
```

### Install with pip

```sh
python -m pip install git+https://github.com/jmarshrossney/teams-transcript-formatter
```

### From source

If you want to make changes to the source code you can clone the repository and install in editable mode:

```sh
git clone https://github.com/jmarshrossney/teams-transcript-formatter
cd teams-transcript-formatter
python -m pip install -e .
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
| `-v`, `--verbose` | Print additional progress information |
| `-q`, `--quiet` | Suppress all non-error output |
| `--version` | Show the version and exit |
| `-h`, `--help` | Show the help message and exit |


## Example

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

Run the script with rename and prefix options:

```
$ teams-transcript-formatter \
    --rename "John Smith=Interviewer" --rename "Jane Doe=Student" \
    --prefix "Interviewer=> " --prefix "Student=< " \
    transcript.vtt
$ head -6 transcript_formatted.txt
> Interviewer | Hello, I am the interviewer. | 00:10

< Student | Nice. I am the student being interviewed, and I have many things to say. | 00:13

```

## Privacy

Speaker names can be replaced using the `--rename` flag. All other redactions of sensitive and identifiable information must be performed before running this script.

Tip: the auto-generated transcripts can be edited in-situ using the Microsoft Stream app.

Remember to delete the original transcripts after running this script!


## Roadmap & contributing

This is just something I threw together in a couple of hours because I needed it immediately and couldn't find anything similar elsewhere.

There are some fairly simple additions that would make this more generally useful:

- [x] Handle meetings with >2 participants
- [x] User can configure how names are handled
- [x] Configure the output format, e.g. using a template
- [ ] Handle Zoom meetings


However, it's going to remain quite a low priority unless I can see it becoming useful to myself or colleagues.
