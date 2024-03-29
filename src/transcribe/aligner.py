# Copyright 2022 [PT BOOKBOT INDONESIA](https://bookbot.id/)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from math import ceil
from typing import Any, Dict, List
from operator import itemgetter
from itertools import groupby
from src.transcribe.homophones import HOMOPHONES, match_sequence


def init_label_studio_annotation() -> List[Dict[str, Any]]:
    """Initializes a pair of dictionaries in Label Studio annotation format.

    Returns:
        List[Dict[str, Any]]: List containing pair of dictionaries in Label Studio JSON
        annotation format.
    """
    return [
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


def overlapping_segments(
    results: Dict[str, List], ground_truth: str, language: str, max_repeats: int = None
) -> List[Dict[str, Any]]:
    """Segments Amazon Transcribe raw output to individual sentences based on
    overlapping regions.

    Args:
        results (Dict[str, List]): Resultant output received from AWS Transcribe.
        ground_truth (str): Ground truth text for the corresponding annotation.
        language (str): Language of the transcript-ground truth pair.
        max_repeats (int, optional): Maximum number of repeats when detecting for
                                     overlaps. Defaults to None.

    Returns:
        List[Dict[str, Any]]: List of dictionaries with segment-wise annotations for
        Label Studio.
    """
    output = []
    sentence_counter = 0

    transcripts = [
        item["alternatives"][0]["content"].lower().strip() for item in results["items"]
    ]

    ground_truth = ground_truth.lower().strip().replace("-", " ").split(" ")

    # gets approximate number of repeats for case where
    # len(ground_truth) << len(transcripts)

    # multiplier also manually tweakable if needed, e.g. 3
    multiplier = (
        max_repeats if max_repeats else ceil(len(transcripts) / len(ground_truth))
    )
    ground_truth *= multiplier

    # find overlaps and mark as new sequence
    homophones = HOMOPHONES[language] if language in HOMOPHONES else None
    aligned_transcripts, *_ = match_sequence(transcripts, ground_truth, homophones)

    for _, g in groupby(enumerate(aligned_transcripts), lambda x: x[0] - x[1]):
        # add a newly initialized pair of lists if new sequence is detected
        seq = list(map(itemgetter(1), g))

        # first and last element of the sequence
        first, last = seq[0], seq[-1]

        # in case it overlaps only on punctuations, then skip
        if "start_time" not in results["items"][first]:
            continue

        output = output + init_label_studio_annotation()

        idx = sentence_counter * 3

        text_dict = output[idx]
        label_dict = output[idx + 1]
        ground_truth_dict = output[idx + 2]

        sentence_id = f"sentence_{sentence_counter}"
        text_dict["id"] = sentence_id
        label_dict["id"] = sentence_id
        ground_truth_dict["id"] = sentence_id

        text_values = text_dict["value"]
        label_values = label_dict["value"]
        ground_truth_values = ground_truth_dict["value"]

        # start time is at the first word of the sequence
        # end time is at the last word of the sequence
        for d in [text_values, label_values, ground_truth_values]:
            d["start"] = float(results["items"][first]["start_time"])
            d["end"] = float(results["items"][last]["end_time"])

        # concat words in a sequence with whitespace
        overlap = [" ".join(transcripts[first : last + 1])]
        # provide region-wise transcription and ground truth for convenience
        for d in [text_values, ground_truth_values]:
            d["text"] = overlap

        sentence_counter += 1

    return output
