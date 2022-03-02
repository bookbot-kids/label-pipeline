from typing import List, Set, Tuple
from homophones import HOMOPHONES, match_sequence
from enum import Enum, auto
import os
import json
import requests


class MispronunciationType(Enum):
    ADDITION = auto()
    SUBSTITUTION = auto()
    ADDITION_SUBSTITUTION = auto()


class Mispronunciation:
    """
    A class to represent a Mispronunciation. 
    Contains attributes which holds the type and differences.

    Attributes
    ----------
    job_name : str
        Job name/id.
    audio_url : str
        URL to audio file.
    language : str
        Language of audio.
    type : MispronunciationType
        Type of mispronunciation/disfluency present.
    lists : Tuple[List[str], List[str]]
        Input list of strings taken for comparison.
    differences : Tuple[List[str], List[str]]
        Differences of list of strings that resulted in the type verdict.

    Methods
    -------
    log_to_airtable() -> None:
        Logs mispronunciation to AirTable.
    """

    def __init__(
        self,
        type: MispronunciationType,
        lists: Tuple[List[str], List[str]],
        differences: Tuple[List[str], List[str]],
        opcodes: List[Tuple[str, int, int, int, int]],
    ):
        """Constructor for the `Mispronunciation` class.

        Parameters
        ----------
        type : MispronunciationType
            Type of mispronunciation/disfluency present.
        lists : Tuple[List[str], List[str]]
            Input list of strings taken for comparison.
        differences : Tuple[List[str], List[str]]
            Differences of list of strings that resulted in the type verdict.
        """
        self.job_name = None
        self.audio_url = None
        self.language = None
        self.type = type
        self.lists = lists
        self.differences = differences
        self.opcodes = opcodes

    def log_to_airtable(self):
        """Logs mispronunciation (`self`) to AirTable.
        """

        def _pprint(list_: List) -> str:
            if len(list_) == 0:
                return " "
            return ", ".join(list_)

        def _get_changes(self: Mispronunciation) -> str:
            ground_truth, transcript = self.lists
            ground_truth_diff, transcript_diff = self.differences

            if self.type == MispronunciationType.ADDITION_SUBSTITUTION:  # A & S
                changes = [
                    f"[{_pprint(ground_truth[j1:j2])} → {_pprint(transcript[i1:i2])}]"
                    for tag, i1, i2, j1, j2 in self.opcodes
                    if tag == "replace" or tag == "delete"
                ]
                return _pprint(changes)
            elif self.type == MispronunciationType.ADDITION:  # A
                return f"[{_pprint(ground_truth_diff)} → {_pprint(transcript_diff)}]"
            else:  # S
                substitutions = [
                    f"[{ground_truth_diff[idx]} → {transcript_diff[idx]}]"
                    for idx in range(len(transcript_diff))
                ]
                return _pprint(substitutions)

        fields = {
            "Job Name": self.job_name,
            "Audio": [{"url": self.audio_url}],
            "Language": self.language,
            "Ground Truth": " ".join(self.lists[0]),
            "Transcript": " ".join(self.lists[1]),
            "Δ Ground Truth": _pprint(self.differences[0]),
            "Δ Transcript": _pprint(self.differences[1]),
            "Δ Changes": _get_changes(self),
            "Disfluency": self.type.name,
        }

        airtable_url = "https://api.airtable.com/v0/appufoncGJbOg7w4Z/Master"
        api_key = os.environ["AIRTABLE_API_KEY"]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({"records": [{"fields": fields}]})

        try:
            response = requests.post(airtable_url, headers=headers, data=payload)
        except Exception as exc:
            print(exc)
        else:
            if response.ok:
                print("Successfully logged to AirTable")
            else:
                print("Failed to log to AirTable")


def remove_fillers(word: str) -> bool:
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


def detect_mispronunciation(
    ground_truth: List[str], transcript: List[str], homophones: List[Set[str]] = None
) -> Mispronunciation:
    """Detects if the pair of ground truth and transcript is considered as a mispronunciation.
    We define a mispronunciation to be either an addition (A) / substitution (S).
    Ignores deletion (D), 100% match (M) and single-word GT (X), returning `None`.
    Also handles homophones given a pre-defined list.

    Parameters
    ----------
    ground_truth : List[str]
        List of ground truth words.
    transcript : List[str]
        List of transcript words.
    homophones : List[Set[str]]
        List of homophone families, by default None.

    Returns
    -------
    Mispronunciation
        Object of mispronunciation present. Otherwise, None.

    Examples
    -------------------------------------------------------------
    | # | Ground Truth       | Transcript             | Verdict |
    |:-:|--------------------|------------------------|:-------:|
    | 1 | skel is a skeleton | skel is a skeleton     |    M    |
    | 2 | skel is a skeleton | skel is not a skeleton |    A    |
    | 3 | skel is a skeleton | skel is a zombie       |    S    |
    | 4 | skel is a skeleton | skel is not a zombie   |  A & S  |
    | 5 | skel is a skeleton | skel is skeleton       |    D    |
    | 6 | skel is a skeleton | skel is zombie         |    D    |
    | 7 | vain is a skeleton | vein is a skeleton     |    M    |
    | 8 | skel               | skel is a skeleton     |    X    |
    -------------------------------------------------------------

    Algorithm
    ----------
    BASE CASES if:
    - single-word ground truth
    - empty transcript
    - zero alignment

    MATCH if:
    - both residues are empty (100% match)

    DELETION if:
    - zero transcript residue, >1 ground truth residue 
        - all spoken transcripts are correct, but some words are missing
    - more residue in ground truth than in transcript
        - less strict condition than above
        - may possibly contain substitution, but could be minimal

    ADDITION if:
    - zero ground truth residue, >1 transcript residue
        - all words in ground truth are perfectly spoken, but additional words are present

    SUBSTITUTION if:
    - same amounts of residue, at exact same positions
        - strict form of substitution, only 1-1 changes per position

    ADDITION & SUBSTITUTION if:
    - more residue in transcript than in ground truth
        - with at least 1 match
    """
    if homophones == None:
        homophones = HOMOPHONES["en"]

    transcript = list(filter(remove_fillers, transcript))

    if len(ground_truth) == 1 or len(transcript) == 0:
        return None  # single word or filler-only transcript

    tsc_idx = set(range(len(transcript)))
    gt_idx = set(range(len(ground_truth)))

    aligned_tsc, aligned_gt, opcodes = match_sequence(
        transcript, ground_truth, homophones
    )

    if len(aligned_tsc) == 0 and len(aligned_gt) == 0:
        return None  # zero matches/alignments, pretty much random

    tsc_diff = tsc_idx.difference(aligned_tsc)
    gt_diff = gt_idx.difference(aligned_gt)

    tsc_diff_words = [transcript[idx] for idx in tsc_diff]
    gt_diff_words = [ground_truth[idx] for idx in gt_diff]

    mispronunciation = Mispronunciation(
        None, (ground_truth, transcript), (gt_diff_words, tsc_diff_words), opcodes
    )

    if len(gt_diff) == 0 and len(tsc_diff) == 0:
        return None  # 100% match
    elif len(gt_diff) > 0 and len(tsc_diff) == 0:
        return None  # deletion only
    elif len(gt_diff) == 0 and len(tsc_diff) > 0:
        mispronunciation.type = MispronunciationType.ADDITION
        return mispronunciation  # addition only
    elif len(tsc_diff) == len(gt_diff) and tsc_diff == gt_diff:
        mispronunciation.type = MispronunciationType.SUBSTITUTION
        return mispronunciation  # strict substitution only
    elif len(tsc_diff) >= len(gt_diff):
        mispronunciation.type = MispronunciationType.ADDITION_SUBSTITUTION
        return mispronunciation  # addition & substitution
    else:
        # in cases where there is less spoken words (transcript) compared to GT,
        # we assume that there is mostly deletion, although it may possibly contain substitutions.
        # we think, the transcript thus contain little to no information that may be useful for training.
        return None
