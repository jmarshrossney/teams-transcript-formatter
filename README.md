# Teams transcript formatter

The purpose of this package is to make Microsoft Teams inverview transcripts easier to read and analyse using tools such as [QualCoder](https://github.com/ccbogel/QualCoder).

Currently it is limited to one-to-one meetings with transcripts downloaded in the `.vtt` format.


## Installation

### From GitHub

```sh
$ python -m pip install git+https://github.com/jmarshrossney/teams-transcript-formatter
```

### From source

If you want to make changes to the source code you can clone the repository and install in 'editable' mode,

```sh
$ git clone https://github.com/jmarshrossney/teams-transcript-formatter
$ cd teams-transcript-formatter
$ python -m pip install -e .
```

## Usage

### Configuration

You first need to create a file called `.env` in the directory in which you
will be executing the script. This file should contain a single line with
the form

```sh
INTERVIEWER='Interviewer Name'
```

where `Interviewer Name` should be replaced by the name of the interviewer
*as it appears in the transcript*.

Tip: you can do this directly from the command line by running `dotenv set INTERVIEWER "Interviewer Name"`.


### Command-line tool

There is one command-line script called `format-transcripts` which takes one or more `.vtt` files and produces one or more formatted files with the naming convention `<original_stem>_formatted.txt`. Optionally, you may also specify a directory for the formatted files using the `-o` flag (the default is the current working directory).


You can also run `format-transcripts -h` (or `--help`) for guidance.


## Example

Say we have a Teams transcript file which we have downloaded and named `transcript.vtt` which looks something like this

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

We first need to set the interviewer name.

```sh
$ dotenv set INTERVIEWER "John Smith"
```

Now we can run the script and see what the formatted transcript looks like.

```
$ format-transcripts transcript.vtt
$ head -6 transcript_formatted.txt
Interviewer (00:10):
        Hello, I am the interviewer.

Student (00:13):
        Nice. I am the student being interviewed, and I have many things to say.

```

## Privacy

Although the names attached to the speakers are modified to read 'Interviewer'
and 'Student', all other redactions of sensitive and identifiable information
must be performed before running this script.

Tip: the auto-generated transcripts can be edited in-situ using the Microsoft
Stream app.

Remember to delete the original transcripts after running this script!


## Roadmap & contributing

This is just something I threw together in a couple of hours because I needed it immediately and couldn't find anything similar elsewhere.

There are some fairly simple additions that would make this more generally useful:

- [ ] Handle meetings with >2 participants
- [ ] User can configure how names are handled
- [ ] Configure the output format, e.g. using a template
- [ ] Handle Zoom meetings


However, it's going to remain quite a low priority unless I can see it becoming useful to myself or colleagues.


