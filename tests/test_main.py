from pathlib import Path

import pytest

from teams_transcript_formatter.formatter import (
    BadInterviewerNameError,
    InterviewerNotFoundError,
    _extract_timestamp,
    _format_transcript,
    main,
)


class TestExtractTimestamp:
    @pytest.mark.parametrize(
        ("interval", "expected"),
        [
            ("00:00:10.087 --> 00:00:13.130", "00:10"),
            ("00:01:05.500 --> 00:01:08.200", "01:05"),
            ("23:59:59.999 --> 00:00:00.000", "59:59"),
            ("00:00:00.000 --> 00:00:05.000", "00:00"),
        ],
    )
    def test_extracts_mm_ss_from_interval(self, interval: str, expected: str) -> None:
        assert _extract_timestamp(interval) == expected


class TestFormatTranscriptHappyPath:
    def test_produces_correct_output(
        self, sample_vtt: str, interviewer: str, expected_output: str
    ) -> None:
        result = _format_transcript(sample_vtt, interviewer)
        assert result == expected_output

    def test_handles_crlf_line_endings(
        self, sample_vtt_crlf: str, interviewer: str, expected_output: str
    ) -> None:
        result = _format_transcript(sample_vtt_crlf, interviewer)
        assert result == expected_output

    def test_adjacent_same_speaker_blocks_are_merged(
        self, sample_vtt_adjacent: str, interviewer: str, sample_vtt_adjacent_expected: str
    ) -> None:
        result = _format_transcript(sample_vtt_adjacent, interviewer)
        assert result == sample_vtt_adjacent_expected

    def test_multiline_speech_is_joined_with_spaces(
        self, sample_vtt_multiline: str, interviewer: str, sample_vtt_multiline_expected: str
    ) -> None:
        result = _format_transcript(sample_vtt_multiline, interviewer)
        assert result == sample_vtt_multiline_expected

    def test_lines_have_expected_prefixes(self, sample_vtt: str, interviewer: str) -> None:
        result = _format_transcript(sample_vtt, interviewer)
        lines = [line for line in result.split("\n") if line]
        assert all(line.startswith(("> Interviewer |", "< Student |")) for line in lines)

    def test_blocks_separated_by_double_newline(self, sample_vtt: str, interviewer: str) -> None:
        result = _format_transcript(sample_vtt, interviewer)
        blocks = result.split("\n\n")
        assert len(blocks) == 4
        for block in blocks:
            assert block.startswith((">", "<"))


class TestFormatTranscriptErrors:
    def test_missing_webvtt_header_raises_value_error(
        self, sample_vtt_no_webvtt: str, interviewer: str
    ) -> None:
        with pytest.raises(ValueError, match="expected the first line to contain 'WEBVTT'"):
            _format_transcript(sample_vtt_no_webvtt, interviewer)

    def test_empty_string_raises_value_error(self, interviewer: str) -> None:
        with pytest.raises(ValueError, match="expected the first line to contain 'WEBVTT'"):
            _format_transcript("", interviewer)

    def test_webvtt_only_no_chunks_raises_value_error(self, interviewer: str) -> None:
        with pytest.raises(ValueError, match="No speech chunks found"):
            _format_transcript("WEBVTT", interviewer)

    def test_single_speaker_raises_interviewer_not_found_error(
        self, sample_vtt_single_speaker: str, interviewer: str
    ) -> None:
        with pytest.raises(InterviewerNotFoundError, match="Expected exactly 2 speakers"):
            _format_transcript(sample_vtt_single_speaker, interviewer)

    def test_wrong_interviewer_name_raises_bad_interviewer_name_error(
        self, sample_vtt_wrong_interviewer: str, interviewer: str
    ) -> None:
        with pytest.raises(
            BadInterviewerNameError, match="Interviewer 'John Smith' is not present"
        ):
            _format_transcript(sample_vtt_wrong_interviewer, interviewer)


class TestMain:
    def test_writes_output_file(self, tmp_path: Path, sample_vtt: str, interviewer: str) -> None:
        infile = tmp_path / "transcript.vtt"
        infile.write_text(sample_vtt)
        outdir = tmp_path / "output"
        outfile = outdir / "transcript_formatted.txt"

        main([infile], outdir, interviewer)

        assert outfile.is_file()
        content = outfile.read_text()
        assert content.startswith("> Interviewer |")

    def test_raises_file_exists_error_if_output_exists(
        self, tmp_path: Path, sample_vtt: str, interviewer: str
    ) -> None:
        infile = tmp_path / "transcript.vtt"
        infile.write_text(sample_vtt)
        outdir = tmp_path / "output"
        outdir.mkdir()
        outfile = outdir / "transcript_formatted.txt"
        outfile.write_text("existing content")

        with pytest.raises(FileExistsError, match="already exists"):
            main([infile], outdir, interviewer)

    def test_processes_multiple_files(
        self, tmp_path: Path, sample_vtt: str, interviewer: str
    ) -> None:
        infile1 = tmp_path / "transcript1.vtt"
        infile2 = tmp_path / "transcript2.vtt"
        infile1.write_text(sample_vtt)
        infile2.write_text(sample_vtt)
        outdir = tmp_path / "output"

        main([infile1, infile2], outdir, interviewer)

        assert (outdir / "transcript1_formatted.txt").is_file()
        assert (outdir / "transcript2_formatted.txt").is_file()

    def test_empty_files_list_raises_value_error(self, interviewer: str) -> None:
        with pytest.raises(ValueError, match="at least one file path"):
            main([], Path("."), interviewer)

    def test_non_path_in_files_raises_type_error(self, interviewer: str) -> None:
        with pytest.raises(TypeError, match="Each file must be a Path"):
            main(["/not/a/path"], Path("."), interviewer)  # type: ignore[list-item]

    def test_non_iterable_files_raises_type_error(self, interviewer: str) -> None:
        with pytest.raises(TypeError, match="must be an iterable"):
            main(None, Path("."), interviewer)  # type: ignore[arg-type]

    def test_empty_interviewer_raises_type_error(self, tmp_path: Path) -> None:
        infile = tmp_path / "transcript.vtt"
        infile.write_text("WEBVTT\n\n")

        with pytest.raises(TypeError, match="interviewer.*must be a non-empty str"):
            main([infile], Path("."), "")

    def test_output_directory_is_created(
        self, tmp_path: Path, sample_vtt: str, interviewer: str
    ) -> None:
        infile = tmp_path / "transcript.vtt"
        infile.write_text(sample_vtt)
        outdir = tmp_path / "nested" / "output"

        main([infile], outdir, interviewer)

        assert outdir.is_dir()
        assert (outdir / "transcript_formatted.txt").is_file()


class TestIntegration:
    def test_end_to_end_roundtrip(
        self, tmp_path: Path, sample_vtt: str, interviewer: str, expected_output: str
    ) -> None:
        """Write a real .vtt file, run main, and verify the .txt output matches."""
        infile = tmp_path / "interview.vtt"
        infile.write_text(sample_vtt)
        outdir = tmp_path / "formatted"

        main([infile], outdir, interviewer)

        outfile = outdir / "interview_formatted.txt"
        assert outfile.read_text() == expected_output

    def test_end_to_end_with_crlf_input(
        self, tmp_path: Path, sample_vtt_crlf: str, interviewer: str, expected_output: str
    ) -> None:
        """Write a CRLF .vtt file, run main, verify output matches Unix-style expected."""
        infile = tmp_path / "interview.vtt"
        infile.write_text(sample_vtt_crlf)
        outdir = tmp_path / "formatted"

        main([infile], outdir, interviewer)

        outfile = outdir / "interview_formatted.txt"
        assert outfile.read_text() == expected_output
