import sys
from pathlib import Path
import os

directory = Path(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(str(directory.parent))

from transcribe.homophones import HOMOPHONES, match_sequence
from transcribe.mispronunciation import detect_mispronunciation, MispronunciationType


# def test_aligner():

#     pass


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
            HOMOPHONES["en"],
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


if __name__ == "__main__":
    test_mispronunciation()
    test_homophones()
    # test_aligner()
