"""
Copyright 2022 [PT BOOKBOT INDONESIA](https://bookbot.id/)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pysrt


def srt2txt(srt_string: str) -> str:
    """Converts stream of srt subtitles to text format.

    Args:
        srt_string (str): String-representation of srt subtitles.

    Returns:
        str: Cleaned text format of subtitles concatenated with space.
    """
    subs = pysrt.from_string(srt_string)
    texts = [sub.text for sub in subs]
    # filter for empty strings
    texts = list(filter(lambda text: len(text) > 0, texts))
    # filter special tokens like [Music] and [Applause]
    texts = list(filter(lambda text: text[0] != "[" and text[-1] != "]", texts))
    texts = " ".join(texts)
    texts = texts.replace("\n", " ")
    return texts
