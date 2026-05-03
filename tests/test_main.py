from pathlib import Path

import pytest

from teams_transcript_formatter.formatter import (
    extract_timestamp,
    format_transcript,
    process_files,
)


class TestExtractTimestamp:
    @pytest.mark.parametrize(
        ("interval", "expected"),
        [
            ("00:00:10.087 --> 00:00:13.130", "00:00:10"),
            ("00:01:05.500 --> 00:01:08.200", "00:01:05"),
            ("23:59:59.999 --> 00:00:00.000", "23:59:59"),
            ("00:00:00.000 --> 00:00:05.000", "00:00:00"),
        ],
    )
    def test_extracts_mm_ss_from_interval(self, interval: str, expected: str) -> None:
        assert extract_timestamp(interval) == expected


class TestFormatTranscriptHappyPath:
    def test_produces_correct_output(
        self,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
        expected_output: str,
    ) -> None:
        result = format_transcript(
            sample_vtt,
            rename=interview_rename,
            prefix=interview_prefix,
        )
        assert result == expected_output

    def test_handles_crlf_line_endings(
        self,
        sample_vtt_crlf: str,
        interview_rename: dict,
        interview_prefix: dict,
        expected_output: str,
    ) -> None:
        result = format_transcript(
            sample_vtt_crlf,
            rename=interview_rename,
            prefix=interview_prefix,
        )
        assert result == expected_output

    def test_adjacent_same_speaker_blocks_are_merged(
        self,
        sample_vtt_adjacent: str,
        interview_rename: dict,
        interview_prefix: dict,
        sample_vtt_adjacent_expected: str,
    ) -> None:
        result = format_transcript(
            sample_vtt_adjacent,
            rename=interview_rename,
            prefix=interview_prefix,
        )
        assert result == sample_vtt_adjacent_expected

    def test_multiline_speech_is_joined_with_spaces(
        self,
        sample_vtt_multiline: str,
        interview_rename: dict,
        interview_prefix: dict,
        sample_vtt_multiline_expected: str,
    ) -> None:
        result = format_transcript(
            sample_vtt_multiline,
            rename=interview_rename,
            prefix=interview_prefix,
        )
        assert result == sample_vtt_multiline_expected

    def test_lines_have_expected_prefixes(
        self,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
    ) -> None:
        result = format_transcript(
            sample_vtt,
            rename=interview_rename,
            prefix=interview_prefix,
        )
        lines = [line for line in result.split("\n") if line]
        assert all(line.startswith(("> Interviewer |", "< Student |")) for line in lines)

    def test_blocks_separated_by_double_newline(
        self,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
    ) -> None:
        result = format_transcript(
            sample_vtt,
            rename=interview_rename,
            prefix=interview_prefix,
        )
        blocks = result.split("\n\n")
        assert len(blocks) == 4
        for block in blocks:
            assert block.startswith((">", "<"))

    def test_single_speaker_is_valid(self) -> None:
        """A single-speaker transcript should no longer raise an error."""
        vtt = (
            "WEBVTT\n\n"
            "hash/0\n"
            "00:00:10.000 --> 00:00:12.000\n"
            "<v Alice>Hello.</v>\n\n"
            "hash/1\n"
            "00:00:12.000 --> 00:00:14.000\n"
            "<v Alice>Hi again.</v>\n"
        )
        result = format_transcript(vtt)
        assert result.startswith("Alice | Hello. Hi again. | 00:00:10")

    def test_three_speakers_is_valid(self) -> None:
        """A transcript with 3+ speakers should work fine."""
        vtt = (
            "WEBVTT\n\n"
            "hash/0\n"
            "00:00:10.000 --> 00:00:12.000\n"
            "<v Alice>Hello.</v>\n\n"
            "hash/1\n"
            "00:00:12.000 --> 00:00:14.000\n"
            "<v Bob>Hi.</v>\n\n"
            "hash/2\n"
            "00:00:14.000 --> 00:00:16.000\n"
            "<v Carol>Hey.</v>\n"
        )
        result = format_transcript(vtt)
        assert "Alice | Hello." in result
        assert "Bob | Hi." in result
        assert "Carol | Hey." in result

    def test_no_rename_keeps_original_names(self, sample_vtt_no_rename: str) -> None:
        result = format_transcript(sample_vtt_no_rename)
        assert "Alice | Hello." in result
        assert "Bob | Hi." in result

    def test_partial_rename_preserves_unmatched(
        self,
        sample_vtt_partial_rename: str,
    ) -> None:
        result = format_transcript(
            sample_vtt_partial_rename,
            rename={"Alice": "Moderator"},
        )
        assert "Moderator | Hello." in result
        assert "Bob | Hi there." in result
        assert "Carol | Greetings." in result

    def test_custom_template(self, sample_vtt_custom_template: str) -> None:
        result = format_transcript(
            sample_vtt_custom_template,
            rename={"Alice": "A", "Bob": "B"},
            template="{speaker}: {speech} [{timestamp}]",
        )
        assert result == ("A: Hello. [00:00:10]\n\nB: Hi. [00:00:12]")

    def test_prefix_with_empty_value(self) -> None:
        vtt = "WEBVTT\n\nhash/0\n00:00:10.000 --> 00:00:12.000\n<v Alice>Hello.</v>\n"
        result = format_transcript(
            vtt,
            rename={"Alice": "A"},
            prefix={"A": ""},
        )
        assert result == "A | Hello. | 00:00:10"

    def test_no_prefixes_given(self, sample_vtt_no_rename: str) -> None:
        result = format_transcript(sample_vtt_no_rename, rename={"Alice": "A"})
        assert result.startswith("A | Hello.")

    def test_speaker_name_with_special_characters(self) -> None:
        vtt = (
            "WEBVTT\n\n"
            "hash/0\n"
            "00:00:10.000 --> 00:00:12.000\n"
            "<v Dr. Smith-Jones>Hello.</v>\n\n"
            "hash/1\n"
            "00:00:12.000 --> 00:00:14.000\n"
            "<v Dr. Smith-Jones>How are you?</v>\n"
        )
        result = format_transcript(
            vtt,
            rename={"Dr. Smith-Jones": "Doctor"},
            prefix={"Doctor": "> "},
        )
        assert result == ("> Doctor | Hello. How are you? | 00:00:10")

    def test_vtt_with_header_metadata(self) -> None:
        vtt = (
            "WEBVTT\n"
            "Kind: captions\n"
            "Language: en\n"
            "\n"
            "hash/0\n"
            "00:00:10.000 --> 00:00:12.000\n"
            "<v Alice>Hello.</v>\n"
        )
        result = format_transcript(vtt)
        assert "Alice | Hello. | 00:00:10" in result

    def test_vtt_with_note_block(self) -> None:
        vtt = (
            "WEBVTT\n"
            "\n"
            "NOTE This is a comment\n"
            "\n"
            "hash/0\n"
            "00:00:10.000 --> 00:00:12.000\n"
            "<v Alice>Hello.</v>\n"
        )
        result = format_transcript(vtt)
        assert "Alice | Hello. | 00:00:10" in result

    def test_empty_speech_is_skipped(self) -> None:
        vtt = (
            "WEBVTT\n\n"
            "hash/0\n"
            "00:00:10.000 --> 00:00:12.000\n"
            "<v Alice></v>\n\n"
            "hash/1\n"
            "00:00:12.000 --> 00:00:14.000\n"
            "<v Alice>Hello.</v>\n"
        )
        result = format_transcript(vtt)
        assert result == "Alice | Hello. | 00:00:12"

    def test_whitespace_only_speech_is_skipped(self) -> None:
        vtt = (
            "WEBVTT\n\n"
            "hash/0\n"
            "00:00:10.000 --> 00:00:12.000\n"
            "<v Alice>   </v>\n\n"
            "hash/1\n"
            "00:00:12.000 --> 00:00:14.000\n"
            "<v Alice>Hello.</v>\n"
        )
        result = format_transcript(vtt)
        assert result == "Alice | Hello. | 00:00:12"

    def test_missing_v_closing_tag(self) -> None:
        vtt = "WEBVTT\n\nhash/0\n00:00:10.000 --> 00:00:12.000\n<v Alice>Hello.\n"
        result = format_transcript(vtt)
        assert result == "Alice | Hello. | 00:00:10"

    def test_closing_v_tag_on_separate_line(self) -> None:
        vtt = "WEBVTT\n\nhash/0\n00:00:10.000 --> 00:00:12.000\n<v Alice>Hello.\n</v>\n"
        result = format_transcript(vtt)
        assert result == "Alice | Hello. | 00:00:10"


class TestFormatTranscriptErrors:
    def test_missing_webvtt_header_raises_value_error(
        self,
        sample_vtt_no_webvtt: str,
    ) -> None:
        with pytest.raises(ValueError, match="expected the first line to contain 'WEBVTT'"):
            format_transcript(sample_vtt_no_webvtt)

    def test_empty_string_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="expected the first line to contain 'WEBVTT'"):
            format_transcript("")

    def test_webvtt_only_no_chunks_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="No speech chunks found"):
            format_transcript("WEBVTT")

    def test_invalid_template_placeholder_raises_value_error(self) -> None:
        vtt = "WEBVTT\n\nhash/0\n00:00:10.000 --> 00:00:12.000\n<v Alice>Hello.</v>\n"
        with pytest.raises(ValueError, match=r"Invalid template placeholder"):
            format_transcript(vtt, template="{speaker} | {speech} | {bad_placeholder}")


class TestMain:
    def test_writes_output_file(
        self,
        tmp_path: Path,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
    ) -> None:
        infile = tmp_path / "transcript.vtt"
        infile.write_text(sample_vtt)
        outdir = tmp_path / "output"
        outfile = outdir / "transcript_formatted.txt"

        process_files([infile], outdir, rename=interview_rename, prefix=interview_prefix)

        assert outfile.is_file()
        content = outfile.read_text()
        assert content.startswith("> Interviewer |")

    def test_raises_file_exists_error_if_output_exists(
        self,
        tmp_path: Path,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
    ) -> None:
        infile = tmp_path / "transcript.vtt"
        infile.write_text(sample_vtt)
        outdir = tmp_path / "output"
        outdir.mkdir()
        outfile = outdir / "transcript_formatted.txt"
        outfile.write_text("existing content")

        with pytest.raises(FileExistsError, match="already exists"):
            process_files(
                [infile],
                outdir,
                rename=interview_rename,
                prefix=interview_prefix,
            )

    def test_processes_multiple_files(
        self,
        tmp_path: Path,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
    ) -> None:
        infile1 = tmp_path / "transcript1.vtt"
        infile2 = tmp_path / "transcript2.vtt"
        infile1.write_text(sample_vtt)
        infile2.write_text(sample_vtt)
        outdir = tmp_path / "output"

        process_files(
            [infile1, infile2],
            outdir,
            rename=interview_rename,
            prefix=interview_prefix,
        )

        assert (outdir / "transcript1_formatted.txt").is_file()
        assert (outdir / "transcript2_formatted.txt").is_file()

    def test_empty_files_list_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="at least one file path"):
            process_files([], Path("."))

    def test_non_path_in_files_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Each file must be a Path"):
            process_files(["/not/a/path"], Path("."))  # type: ignore[list-item]

    def test_non_iterable_files_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="must be an iterable"):
            process_files(None, Path("."))  # type: ignore[arg-type]

    def test_output_directory_is_created(
        self,
        tmp_path: Path,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
    ) -> None:
        infile = tmp_path / "transcript.vtt"
        infile.write_text(sample_vtt)
        outdir = tmp_path / "nested" / "output"

        process_files(
            [infile],
            outdir,
            rename=interview_rename,
            prefix=interview_prefix,
        )

        assert outdir.is_dir()
        assert (outdir / "transcript_formatted.txt").is_file()

    def test_returns_infile_outfile_pairs(
        self,
        tmp_path: Path,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
    ) -> None:
        infile1 = tmp_path / "transcript1.vtt"
        infile2 = tmp_path / "transcript2.vtt"
        infile1.write_text(sample_vtt)
        infile2.write_text(sample_vtt)
        outdir = tmp_path / "output"

        results = process_files(
            [infile1, infile2],
            outdir,
            rename=interview_rename,
            prefix=interview_prefix,
        )

        assert len(results) == 2
        assert results[0] == (infile1, outdir / "transcript1_formatted.txt")
        assert results[1] == (infile2, outdir / "transcript2_formatted.txt")


class TestIntegration:
    def test_end_to_end_roundtrip(
        self,
        tmp_path: Path,
        sample_vtt: str,
        interview_rename: dict,
        interview_prefix: dict,
        expected_output: str,
    ) -> None:
        infile = tmp_path / "interview.vtt"
        infile.write_text(sample_vtt)
        outdir = tmp_path / "formatted"

        process_files(
            [infile],
            outdir,
            rename=interview_rename,
            prefix=interview_prefix,
        )

        outfile = outdir / "interview_formatted.txt"
        assert outfile.read_text() == expected_output

    def test_end_to_end_with_crlf_input(
        self,
        tmp_path: Path,
        sample_vtt_crlf: str,
        interview_rename: dict,
        interview_prefix: dict,
        expected_output: str,
    ) -> None:
        infile = tmp_path / "interview.vtt"
        infile.write_text(sample_vtt_crlf)
        outdir = tmp_path / "formatted"

        process_files(
            [infile],
            outdir,
            rename=interview_rename,
            prefix=interview_prefix,
        )

        outfile = outdir / "interview_formatted.txt"
        assert outfile.read_text() == expected_output
