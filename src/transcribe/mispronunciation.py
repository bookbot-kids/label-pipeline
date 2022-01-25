from homophones import HOMOPHONES, match_sequence
from enum import Enum, auto


class Mispronunciation(Enum):
    ADDITION = auto()
    SUBSTITUTION = auto()
    ADDITION_SUBSTITUTION = auto()


MISPRONUNCIATION_FOLDER_MAPPING = {
    Mispronunciation.ADDITION: ["addition"],
    Mispronunciation.SUBSTITUTION: ["substitution"],
    Mispronunciation.ADDITION_SUBSTITUTION: ["addition", "substitution"],
}


def remove_fillers(word):
    """Manually checks if a word is a filler word

    Parameters
    ----------
    word : str
        Any word (sequence of characters).

    Returns
    -------
    bool
        True if word is not a filler. False otherwise.
    """
    fillers = ("", "uh", "huh", "mm", "yeah", "mhm", "hmm", "hm")
    return word not in fillers


def detect_mispronunciation(ground_truth, transcript, homophones=None):
    """Detects if the pair of ground truth and transcript is considered as a mispronunciation.
    We define a mispronunciation to be either an addition (A) / substitution (S).
    Ignores deletion (D), 100% match (M) and single-word GT (X).
    Also handles homophones given a pre-defined list.

    Examples:
    ---------------------------------------------------------
    |    Ground Truth    |       Transcript       | Verdict |
    |--------------------|------------------------|---------|
    | skel is a skeleton | skel is a skeleton     |    M    |
    | skel is a skeleton | skel is not a skeleton |    A    |
    | skel is a skeleton | skel is a zombie       |    S    |
    | skel is a skeleton | skel is not a zombie   |   A&S   |
    | skel is a skeleton | skel is skeleton       |    D    |
    | skel is a skeleton | skel is zombie         |    D    |
    | vain is a skeleton | vein is a skeleton     |    M    |
    | skel               | skel is a skeleton     |    X    |
    ---------------------------------------------------------

    Parameters
    ----------
    ground_truth : List[str]
        List of ground truth words.
    transcript : List[str]
        List of transcript words.
    homophones : List[Set(str)]
        List of homophone families, by default None.

    Returns
    -------
    Mispronunciation
        Type of mispronunciation present. Otherwise, None.
    """
    if homophones == None:
        homophones = HOMOPHONES["en"]

    transcript = list(filter(remove_fillers, transcript))

    if len(ground_truth) == 1 or len(transcript) == 0:
        return None  # single word or filler-only transcript

    tsc_idx = set(range(len(transcript)))
    gt_idx = set(range(len(ground_truth)))

    aligned_tsc, aligned_gt = match_sequence(transcript, ground_truth, homophones)

    tsc_diff = tsc_idx.difference(aligned_tsc)
    gt_diff = gt_idx.difference(aligned_gt)

    if len(gt_diff) == 0 and len(tsc_diff) == 0:
        return None  # 100% match
    elif len(gt_diff) > 0 and len(tsc_diff) == 0:
        return None  # deletion only
    elif len(gt_diff) == 0 and len(tsc_diff) > 0:
        return Mispronunciation.ADDITION  # addition only
    elif len(tsc_diff) == len(gt_diff):
        return Mispronunciation.SUBSTITUTION  # substitution only
    elif len(tsc_diff) > len(gt_diff):
        return Mispronunciation.ADDITION_SUBSTITUTION  # A & S
    else:
        return None


def main():
    cases = [
        ("skel is a skeleton", "skel is a skeleton", None),
        ("skel is a skeleton", "skel is not a skeleton", Mispronunciation.ADDITION),
        ("skel is a skeleton", "skel is a zombie", Mispronunciation.SUBSTITUTION),
        (
            "skel is a skeleton",
            "skel is not a zombie",
            Mispronunciation.ADDITION_SUBSTITUTION,
        ),
        ("skel is a skeleton", "skel is skeleton", None),
        ("skel is a skeleton", "skel is zombie", None),
        ("vain is a skeleton", "vein is a skeleton", None),
        ("skel is a skeleton", "skel is uh a skeleton", None),
        ("skel", "skel is a skeleton", None),
    ]

    for case in cases:
        gt, tsc, verdict = case
        gt = gt.split()
        tsc = tsc.split()

        assert detect_mispronunciation(gt, tsc) == verdict


if __name__ == "__main__":
    main()

