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
