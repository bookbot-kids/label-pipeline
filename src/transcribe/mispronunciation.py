from typing import List, Tuple
from homophones import HOMOPHONES, match_sequence
from enum import Enum, auto
import os
import json
import requests


class MispronunciationType(Enum):
    ADDITION = auto()
    SUBSTITUTION = auto()


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
    type : List[MispronunciationType]
        Type(s) of mispronunciation/disfluency present.
    lists : Tuple[List[str], List[str]]
        Input list of strings taken for comparison.
    differences : Tuple[List[str], List[str]]
        Differences of list of strings that resulted in the type verdict.
    _folder_mapping : Dict[MispronunciationType, List[str]]
        Mapping of mispronunciation type present to list of folder names.

    Methods
    -------
    get_folder_mapping() -> List[str]:
        Returns the list of folder mapping result.
    log_to_airtable() -> None:
        Logs mispronunciation to AirTable.
    """

    def __init__(
        self,
        type: List[MispronunciationType],
        lists: Tuple[List[str], List[str]],
        differences: Tuple[List[str], List[str]],
    ):
        """Constructor for the `Mispronunciation` class.

        Parameters
        ----------
        type : List[MispronunciationType]
            Type(s) of mispronunciation/disfluency present.
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
        self._folder_mapping = {
            MispronunciationType.ADDITION: ["addition"],
            MispronunciationType.SUBSTITUTION: ["substitution"],
        }

    def get_folder_mapping(self) -> List[str]:
        """Maps mispronunciation type present to the list of strings as foldernames.

        Returns
        -------
        List[str]
            List of string names of subfolders for saving.
        """
        return [self._folder_mapping[t] for t in self.type]

    def log_to_airtable(self):
        """Logs mispronunciation (`self`) to AirTable.
        """
        fields = {
            "Job Name": self.job_name,
            "Audio": [{"url": self.audio_url}],
            "Language": self.language,
            "Ground Truth": " ".join(self.lists[0]),
            "Transcript": " ".join(self.lists[1]),
            "Δ Ground Truth": str(self.differences[0]),
            "Δ Transcript": str(self.differences[1]),
            "Disfluency": [type.name for type in self.type],
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
        Object of mispronunciation present. Otherwise, None.
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

    tsc_diff_words = [transcript[idx] for idx in tsc_diff]
    gt_diff_words = [ground_truth[idx] for idx in gt_diff]

    mispronunciation = Mispronunciation(
        None, (ground_truth, transcript), (gt_diff_words, tsc_diff_words),
    )

    if len(gt_diff) == 0 and len(tsc_diff) == 0:
        return None  # 100% match
    elif len(gt_diff) > 0 and len(tsc_diff) == 0:
        return None  # deletion only
    elif len(gt_diff) == 0 and len(tsc_diff) > 0:
        mispronunciation.type = [MispronunciationType.ADDITION]
        return mispronunciation  # addition only
    elif len(tsc_diff) == len(gt_diff):
        mispronunciation.type = [MispronunciationType.SUBSTITUTION]
        return mispronunciation  # substitution only
    elif len(tsc_diff) > len(gt_diff):
        mispronunciation.type = [
            MispronunciationType.ADDITION,
            MispronunciationType.SUBSTITUTION,
        ]
        return mispronunciation  # addition & substitution
    else:
        return None


def main():
    cases = [
        ("skel is a skeleton", "skel is a skeleton", None),
        (
            "skel is a skeleton",
            "skel is not a skeleton",
            [MispronunciationType.ADDITION],
        ),
        ("skel is a skeleton", "skel is a zombie", [MispronunciationType.SUBSTITUTION]),
        (
            "skel is a skeleton",
            "skel is not a zombie",
            [MispronunciationType.ADDITION, MispronunciationType.SUBSTITUTION],
        ),
        ("skel is a skeleton", "skel is skeleton", None),
        ("skel is a skeleton", "skel is zombie", None),
        ("vain is a skeleton", "vein is a skeleton", None),
        ("skel is a skeleton", "skel is uh a skeleton", None),
        ("skel", "skel is a skeleton", None),
    ]

    for case in cases[1:2]:
        gt, tsc, verdict = case
        gt = gt.split()
        tsc = tsc.split()

        prediction = detect_mispronunciation(gt, tsc)
        url = "https://bookbot-speech.s3.ap-southeast-1.amazonaws.com/mispronunciations/addition/en-id/5b12d49c-e421-4c9b-9ee8-ad0469d69022_1637798323388.aac?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEF0aDmFwLXNvdXRoZWFzdC0xIkgwRgIhALfaWUpZNe2G3BnVtJW7d0oXPph1C55HAa4vRKKbXnIBAiEA15DRoiL1Mfw%2B%2BGSO88m4Q4ZaBj26hu59EJhO12CA7psqkgMIhv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARADGgwyODMwMzE4NTgzMTYiDGN3w2OkHgoZn8pBCSrmAg0zQ%2B%2FLxZteM6RKDZrRrtMX8uyks6o6tL19KnP%2FDPDV45A9i07BkdJVsD91JlZNxKFcug9f8bgs8S7mya04UfGw%2FB8SQUCqiEwxIGmesXJSY6gxXirTFBUendIkBESNfuqvBWh%2BFUj%2BaligsGUROTRotbHEgrkDOTHbVLVHkyUwBuEj8WZjUh99QrpMKzh2zv8Vh5DYo3M8aRn8DOnlAkwb%2FM0svEWqag0hek%2B4LxL8KVoOEbc3ZBXSMT3MkF1c4snFO6vEbJVdQA%2BYDphSSmCA3TW8I5U4ml0kcWYbkewit1r7wzDJ0sMRmLBrhckvJ3bAlDScx%2BuTHVhOampTB2QgGTor5XaFSNwZ221zpxjefVmPZsC9RXzLcSH5E%2BXnVJW0BUeXhl8ucF%2FKxbrkzKuEERaPsUw%2FxVmsUI%2FidEtMBzGAdKRQeOdzpW47C9qG3eDZnjRQv%2BOh6WlxwBKSiUkbub5Eencw%2BP29jwY6sgJa7tU3lduukHSZmIHKI1FhLcNc%2BvViyebFHAC0owb4C0ZY%2B2GX%2FUVwbON%2Bb0RjKoQ1tqYiQIhft3gxYC97HCh%2BgZmJ50H%2F0dnuR4GtiguYQeI0%2BDl3fqGeJyiVZ%2BNkOpUvgdpe0GkbmL4fP9yT7KlGrom9KyoZmfVyrL78yLkx%2BudrTh9D%2B22njylWRECabdBksXQGuHl2kIS%2Bq2LSAwPzYwgV9O1h7rDuiaw0rS15A2d%2FkjfZ5LpO7rJPT8ztBE3l51QjFQKvdKn2gNKXzOzQCk7dhM9SSElHUkAqqwwzvMg1v%2FUaEccn7MgO7Y4II5KEZn2dzyz4a0T1%2B%2BGC3KycRkHR4XdapVPJrgvr6NsbLF%2B9edM8nSjk1LAN0PwEVIc7SF6BQCiQsrWZU094yB3E2YI%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20220125T105619Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAUDZQDNSGFJH3TJXT%2F20220125%2Fap-southeast-1%2Fs3%2Faws4_request&X-Amz-Signature=3bbff872f9dd992d512bfdd05222788df01344112c239a529ff14ac6b297ca54"

        if prediction:
            prediction.audio_url = url
            prediction.log_to_airtable()
            prediction = prediction.type

        assert prediction == verdict


if __name__ == "__main__":
    main()

