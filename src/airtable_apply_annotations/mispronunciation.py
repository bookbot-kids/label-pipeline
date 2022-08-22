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

from typing import List, Set
from homophones import HOMOPHONES, match_sequence


def detect_mispronunciation(
    ground_truth: List[str], transcript: List[str], homophones: List[Set[str]] = None
) -> str:
    """Detects if the pair of ground truth and transcript is considered as a
    mispronunciation.

    We define a mispronunciation to be either an addition (A) / substitution (S).
    Ignores deletion (D), 100% match (M) and single-word GT (X), returning `None`.
    Also handles homophones given a pre-defined list.

    Args:
        ground_truth (List[str]): List of ground truth words.
        transcript (List[str]): List of transcript words.
        homophones (List[Set[str]], optional): List of homophone families. Defaults to
        None.

    Returns:
        str: Type of mispronunciation present. Otherwise, None.
    """
    if homophones is None:
        homophones = HOMOPHONES["en"]

    if len(ground_truth) == 1 or len(transcript) == 0:
        return "DELETE"  # single word or filler-only transcript

    tsc_idx = set(range(len(transcript)))
    gt_idx = set(range(len(ground_truth)))

    aligned_tsc, aligned_gt, _ = match_sequence(transcript, ground_truth, homophones)

    if len(aligned_tsc) == 0 and len(aligned_gt) == 0:
        return "DELETE"  # zero matches/alignments, pretty much random

    tsc_diff = tsc_idx.difference(aligned_tsc)
    gt_diff = gt_idx.difference(aligned_gt)

    if len(gt_diff) == 0 and len(tsc_diff) == 0:
        return "DELETE"  # 100% match
    elif len(gt_diff) > 0 and len(tsc_diff) == 0:
        return "DELETE"  # deletion only
    elif len(gt_diff) == 0 and len(tsc_diff) > 0:
        return "ADDITION"
    elif len(tsc_diff) == len(gt_diff) and tsc_diff == gt_diff:
        return "SUBSTITUTION"
    elif len(tsc_diff) >= len(gt_diff):
        return "ADDITION_SUBSTITUTION"
    else:
        return "DELETE"
