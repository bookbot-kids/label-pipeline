from src.transcribe.homophones import HOMOPHONES, match_sequence
from src.transcribe.mispronunciation import (
    detect_mispronunciation,
    MispronunciationType,
)
from src.transcribe.aligner import overlapping_segments, init_label_studio_annotation
from src.transcribe.srt2txt import srt2txt


def test_aligner():
    test_text = {
        "items": [
            {
                "start_time": "0.14",
                "end_time": "1.55",
                "alternatives": [{"confidence": "1.0", "content": "Assalamualaikum"}],
                "type": "pronunciation",
            },
            {
                "alternatives": [{"confidence": "0.0", "content": "."}],
                "type": "punctuation",
            },
            {
                "start_time": "2.04",
                "end_time": "2.38",
                "alternatives": [{"confidence": "0.3072", "content": "Wow"}],
                "type": "pronunciation",
            },
            {
                "alternatives": [{"confidence": "0.0", "content": "!"}],
                "type": "punctuation",
            },
            {
                "start_time": "2.94",
                "end_time": "3.25",
                "alternatives": [{"confidence": "0.4046", "content": "Wow"}],
                "type": "pronunciation",
            },
            {
                "alternatives": [{"confidence": "0.0", "content": "!"}],
                "type": "punctuation",
            },
            {
                "start_time": "6.69",
                "end_time": "6.88",
                "alternatives": [{"confidence": "1.0", "content": "Saya"}],
                "type": "pronunciation",
            },
            {
                "start_time": "6.88",
                "end_time": "7.17",
                "alternatives": [{"confidence": "0.9461", "content": "enggak"}],
                "type": "pronunciation",
            },
        ],
    }

    # case 1: ground truth aligned with aws transcribe results
    assert overlapping_segments(
        test_text, "Assalamualaikum Wow Saya enggak", language="id"
    ) == [
        {
            "value": {"start": 0.14, "end": 1.55, "text": ["assalamualaikum"]},
            "id": "sentence_0",
            "from_name": "transcription",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": 0.14, "end": 1.55, "labels": ["Sentence"]},
            "id": "sentence_0",
            "from_name": "labels",
            "to_name": "audio",
            "type": "labels",
        },
        {
            "value": {"start": 0.14, "end": 1.55, "text": ["assalamualaikum"]},
            "id": "sentence_0",
            "from_name": "region-ground-truth",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": 2.04, "end": 2.38, "text": ["wow"]},
            "id": "sentence_1",
            "from_name": "transcription",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": 2.04, "end": 2.38, "labels": ["Sentence"]},
            "id": "sentence_1",
            "from_name": "labels",
            "to_name": "audio",
            "type": "labels",
        },
        {
            "value": {"start": 2.04, "end": 2.38, "text": ["wow"]},
            "id": "sentence_1",
            "from_name": "region-ground-truth",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": 6.69, "end": 7.17, "text": ["saya enggak"]},
            "id": "sentence_2",
            "from_name": "transcription",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": 6.69, "end": 7.17, "labels": ["Sentence"]},
            "id": "sentence_2",
            "from_name": "labels",
            "to_name": "audio",
            "type": "labels",
        },
        {
            "value": {"start": 6.69, "end": 7.17, "text": ["saya enggak"]},
            "id": "sentence_2",
            "from_name": "region-ground-truth",
            "to_name": "audio",
            "type": "textarea",
        },
    ]

    # case 2: slightly off alignment with ground truth
    assert overlapping_segments(test_text, "Wow Saya enggak mau", language="id") == [
        {
            "value": {"start": 2.04, "end": 2.38, "text": ["wow"]},
            "id": "sentence_0",
            "from_name": "transcription",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": 2.04, "end": 2.38, "labels": ["Sentence"]},
            "id": "sentence_0",
            "from_name": "labels",
            "to_name": "audio",
            "type": "labels",
        },
        {
            "value": {"start": 2.04, "end": 2.38, "text": ["wow"]},
            "id": "sentence_0",
            "from_name": "region-ground-truth",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": 6.69, "end": 7.17, "text": ["saya enggak"]},
            "id": "sentence_1",
            "from_name": "transcription",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": 6.69, "end": 7.17, "labels": ["Sentence"]},
            "id": "sentence_1",
            "from_name": "labels",
            "to_name": "audio",
            "type": "labels",
        },
        {
            "value": {"start": 6.69, "end": 7.17, "text": ["saya enggak"]},
            "id": "sentence_1",
            "from_name": "region-ground-truth",
            "to_name": "audio",
            "type": "textarea",
        },
    ]

    # case 3: alignments are totally off
    assert (
        overlapping_segments(test_text, "ini contoh alignment salah", language="id")
        == []
    )

    assert init_label_studio_annotation() == [
        {
            "value": {"start": -1, "end": -1, "text": []},
            "id": "",
            "from_name": "transcription",
            "to_name": "audio",
            "type": "textarea",
        },
        {
            "value": {"start": -1, "end": -1, "labels": ["Sentence"]},
            "id": "",
            "from_name": "labels",
            "to_name": "audio",
            "type": "labels",
        },
        {
            "value": {"start": -1, "end": -1, "text": []},
            "id": "",
            "from_name": "region-ground-truth",
            "to_name": "audio",
            "type": "textarea",
        },
    ]


def test_homophones():
    assert match_sequence(
        ["yo", "hi", "my", "name", "is", "bob"],
        ["hi", "my", "name", "is", "alice"],
        HOMOPHONES["en"],
    ) == (
        [1, 2, 3, 4],
        [0, 1, 2, 3],
        [("delete", 0, 1, 0, 0), ("equal", 1, 5, 0, 4), ("replace", 5, 6, 4, 5)],
    )
    assert match_sequence(
        ["please", "sign", "this", "paper"],
        ["please", "sine", "this", "paper"],
        HOMOPHONES["en"],
    ) == ([0, 1, 2, 3], [0, 1, 2, 3], [("equal", 0, 4, 0, 4)])

    assert match_sequence(
        ["whether", "or", "not", "this", "happens"],
        ["weather", "this", "happens"],
        HOMOPHONES["en"],
    ) == (
        [0, 3, 4],
        [0, 1, 2],
        [("equal", 0, 1, 0, 1), ("delete", 1, 3, 1, 1), ("equal", 3, 5, 1, 3)],
    )


def test_mispronunciation():
    assert (
        detect_mispronunciation(
            ["skel", "is", "a", "skeleton"],
            ["skel", "is", "a", "skeleton"],
            HOMOPHONES["en"],
        )
        is None
    )

    assert (
        detect_mispronunciation(
            ["skel", "is", "a", "skeleton"],
            ["skel", "is", "not", "a", "skeleton"],
            HOMOPHONES["en"],
        ).type
        == MispronunciationType.ADDITION
    )
    assert (
        detect_mispronunciation(
            ["skel", "is", "a", "skeleton"],
            ["skel", "is", "a", "zombie"],
            HOMOPHONES["en"],
        ).type
        == MispronunciationType.SUBSTITUTION
    )
    assert (
        detect_mispronunciation(
            ["skel", "is", "a", "skeleton"],
            ["skel", "is", "not", "a", "zombie"],
            HOMOPHONES["en"],
        ).type
        == MispronunciationType.ADDITION_SUBSTITUTION
    )

    assert (
        detect_mispronunciation(
            ["skel", "is", "a", "skeleton"],
            ["skel", "is", "skeleton"],
            HOMOPHONES["en"],
        )
        is None
    )

    assert (
        detect_mispronunciation(
            ["vain", "is", "a", "skeleton"],
            ["vein", "is", "a", "skeleton"],
        )
        is None
    )

    assert (
        detect_mispronunciation(
            ["skel"],
            ["skel", "is", "a", "skeleton"],
            HOMOPHONES["en"],
        )
        is None
    )

    assert (
        detect_mispronunciation(
            ["skel", "is"],
            ["bob", "are"],
            HOMOPHONES["en"],
        )
        is None
    )


def test_srt2txt():
    assert (
        srt2txt(
            """
1
00:05:00,400 --> 00:05:15,300
This is an example of
a subtitle.
    """
        )
        == "This is an example of a subtitle."
    )

    assert srt2txt("[Music]") == ""
