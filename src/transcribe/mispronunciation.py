from homophones import HOMOPHONES, match_sequence


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
    We define a mispronunciation to be either an addition/substitution. Ignores deletion.
    Also handles homophones given a pre-defined list.

    Examples:
    ---------------------------------------------------------
    |    Ground Truth    |       Transcript       | Verdict |
    |--------------------|------------------------|---------|
    | skel is a skeleton | skel is a skeleton     |    F    |
    | skel is a skeleton | skel is not a skeleton |    T    |
    | skel is a skeleton | skel is a zombie       |    T    |
    | skel is a skeleton | skel is not a zombie   |    T    |
    | skel is a skeleton | skel is skeleton       |    F    |
    | skel is a skeleton | skel is zombie         |    T    |
    | vain is a skeleton | vein is a skeleton     |    F    |
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
    bool
        True if there is a mispronunciation. False otherwise.
    """
    if homophones == None:
        homophones = HOMOPHONES["en"]

    transcript = list(filter(remove_fillers, transcript))

    print(f"Transcript: {transcript}")
    print(f"Ground Truth: {ground_truth}")

    tsc_idx = set(range(len(transcript)))
    gt_idx = set(range(len(ground_truth)))

    aligned_tsc, aligned_gt = match_sequence(transcript, ground_truth, homophones)

    tsc_diff = tsc_idx.difference(aligned_tsc)
    gt_diff = gt_idx.difference(aligned_gt)

    if len(gt_diff) == 0 and len(tsc_diff) == 0:
        return False  # 100% match
    elif len(gt_diff) > 0 and len(tsc_diff) == 0:
        return False  # deletion only
    else:
        return True


def main():
    cases = [
        ("skel is a skeleton", "skel is a skeleton", False),
        ("skel is a skeleton", "skel is not a skeleton", True),
        ("skel is a skeleton", "skel is a zombie", True),
        ("skel is a skeleton", "skel is not a zombie", True),
        ("skel is a skeleton", "skel is skeleton", False),
        ("skel is a skeleton", "skel is zombie", True),
        ("vain is a skeleton", "vein is a skeleton", False),
        ("skel is a skeleton", "skel is uh a skeleton", False),
    ]

    for case in cases:
        gt, tsc, verdict = case
        gt = gt.split()
        tsc = tsc.split()

        assert detect_mispronunciation(gt, tsc) == verdict


if __name__ == "__main__":
    main()

