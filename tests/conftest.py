import pytest


@pytest.fixture
def interviewer() -> str:
    return "John Smith"


@pytest.fixture
def sample_vtt() -> str:
    return (
        "WEBVTT\n"
        "\n"
        "91b3f3c3-44c6-4a8b-8c0a-add105d816bd/32-0\n"
        "00:00:10.087 --> 00:00:13.130\n"
        "<v John Smith>Hello, I am the interviewer.</v>\n"
        "\n"
        "91b3f3c3-44c6-4a8b-8c0a-add105d816bd/32-1\n"
        "00:00:13.130 --> 00:00:16.270\n"
        "<v Jane Doe>Nice. I am the student being interviewed,\n"
        "and I have many things to say.</v>\n"
        "\n"
        "91b3f3c3-44c6-4a8b-8c0a-add105d816bd/32-2\n"
        "00:00:16.270 --> 00:00:20.000\n"
        "<v John Smith>Great, let me ask you another question.</v>\n"
        "\n"
        "91b3f3c3-44c6-4a8b-8c0a-add105d816bd/32-3\n"
        "00:00:20.000 --> 00:00:25.500\n"
        "<v Jane Doe>Sure, go ahead.</v>\n"
    )


@pytest.fixture
def sample_vtt_crlf(sample_vtt: str) -> str:
    return sample_vtt.replace("\n", "\r\n")


@pytest.fixture
def expected_output() -> str:
    lines = [
        "> Interviewer | Hello, I am the interviewer. | 00:10",
        "",
        (
            "< Student | Nice. I am the student being interviewed, "
            "and I have many things to say. | 00:13"
        ),
        "",
        "> Interviewer | Great, let me ask you another question. | 00:16",
        "",
        "< Student | Sure, go ahead. | 00:20",
    ]
    return "\n".join(lines)


@pytest.fixture
def sample_vtt_no_webvtt() -> str:
    return "\n".join(
        [
            "NOTWEBVTT",
            "",
            "hash/0",
            "00:00:10.000 --> 00:00:12.000",
            "<v John Smith>Hello.</v>",
            "",
            "hash/1",
            "00:00:12.000 --> 00:00:14.000",
            "<v Jane Doe>Hi.</v>",
        ]
    )


@pytest.fixture
def sample_vtt_single_speaker() -> str:
    return "\n".join(
        [
            "WEBVTT",
            "",
            "hash/0",
            "00:00:10.000 --> 00:00:12.000",
            "<v John Smith>First block.</v>",
            "",
            "hash/1",
            "00:00:12.000 --> 00:00:14.000",
            "<v John Smith>Second block.</v>",
        ]
    )


@pytest.fixture
def sample_vtt_wrong_interviewer() -> str:
    return "\n".join(
        [
            "WEBVTT",
            "",
            "hash/0",
            "00:00:10.000 --> 00:00:12.000",
            "<v Alice>Hello.</v>",
            "",
            "hash/1",
            "00:00:12.000 --> 00:00:14.000",
            "<v Bob>Hi.</v>",
        ]
    )


@pytest.fixture
def sample_vtt_adjacent() -> str:
    return "\n".join(
        [
            "WEBVTT",
            "",
            "hash-0",
            "00:00:10.000 --> 00:00:12.000",
            "<v John Smith>First sentence.</v>",
            "",
            "hash-1",
            "00:00:12.000 --> 00:00:14.000",
            "<v John Smith>Second sentence.</v>",
            "",
            "hash-2",
            "00:00:14.000 --> 00:00:16.000",
            "<v Jane Doe>Response.</v>",
        ]
    )


@pytest.fixture
def sample_vtt_adjacent_expected() -> str:
    lines = [
        "> Interviewer | First sentence. Second sentence. | 00:10",
        "",
        "< Student | Response. | 00:14",
    ]
    return "\n".join(lines)


@pytest.fixture
def sample_vtt_multiline() -> str:
    return "\n".join(
        [
            "WEBVTT",
            "",
            "hash-0",
            "00:00:10.000 --> 00:00:15.000",
            "<v John Smith>This speech",
            "spans multiple",
            "lines in the vtt.</v>",
            "",
            "hash-1",
            "00:00:15.000 --> 00:00:20.000",
            "<v Jane Doe>Response.</v>",
        ]
    )


@pytest.fixture
def sample_vtt_multiline_expected() -> str:
    lines = [
        "> Interviewer | This speech spans multiple lines in the vtt. | 00:10",
        "",
        "< Student | Response. | 00:15",
    ]
    return "\n".join(lines)
