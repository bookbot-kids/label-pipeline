import sys
import os

sys.path.append(
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    )
)
from src.transcribe.homophones import *
from src.transcribe.mispronunciation import (
    MispronunciationType,
    detect_mispronunciation,
)


def main():
    cases = [
        ("skel is a skeleton", "skel is a skeleton", None),
        (
            "skel is a skeleton",
            "skel is not a skeleton",
            [MispronunciationType.ADDITION],
        ),
        (
            "skel is a skeleton dog",
            "skel is a zombie cat",
            [MispronunciationType.SUBSTITUTION],
        ),
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

    for case in cases:
        gt, tsc, verdict = case
        gt = gt.split()
        tsc = tsc.split()

        prediction = detect_mispronunciation(gt, tsc)
        url = "https://bookbot-speech.s3.ap-southeast-1.amazonaws.com/mispronunciations/addition/en-id/5b12d49c-e421-4c9b-9ee8-ad0469d69022_1637798323388.aac?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEF0aDmFwLXNvdXRoZWFzdC0xIkgwRgIhALfaWUpZNe2G3BnVtJW7d0oXPph1C55HAa4vRKKbXnIBAiEA15DRoiL1Mfw%2B%2BGSO88m4Q4ZaBj26hu59EJhO12CA7psqkgMIhv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARADGgwyODMwMzE4NTgzMTYiDGN3w2OkHgoZn8pBCSrmAg0zQ%2B%2FLxZteM6RKDZrRrtMX8uyks6o6tL19KnP%2FDPDV45A9i07BkdJVsD91JlZNxKFcug9f8bgs8S7mya04UfGw%2FB8SQUCqiEwxIGmesXJSY6gxXirTFBUendIkBESNfuqvBWh%2BFUj%2BaligsGUROTRotbHEgrkDOTHbVLVHkyUwBuEj8WZjUh99QrpMKzh2zv8Vh5DYo3M8aRn8DOnlAkwb%2FM0svEWqag0hek%2B4LxL8KVoOEbc3ZBXSMT3MkF1c4snFO6vEbJVdQA%2BYDphSSmCA3TW8I5U4ml0kcWYbkewit1r7wzDJ0sMRmLBrhckvJ3bAlDScx%2BuTHVhOampTB2QgGTor5XaFSNwZ221zpxjefVmPZsC9RXzLcSH5E%2BXnVJW0BUeXhl8ucF%2FKxbrkzKuEERaPsUw%2FxVmsUI%2FidEtMBzGAdKRQeOdzpW47C9qG3eDZnjRQv%2BOh6WlxwBKSiUkbub5Eencw%2BP29jwY6sgJa7tU3lduukHSZmIHKI1FhLcNc%2BvViyebFHAC0owb4C0ZY%2B2GX%2FUVwbON%2Bb0RjKoQ1tqYiQIhft3gxYC97HCh%2BgZmJ50H%2F0dnuR4GtiguYQeI0%2BDl3fqGeJyiVZ%2BNkOpUvgdpe0GkbmL4fP9yT7KlGrom9KyoZmfVyrL78yLkx%2BudrTh9D%2B22njylWRECabdBksXQGuHl2kIS%2Bq2LSAwPzYwgV9O1h7rDuiaw0rS15A2d%2FkjfZ5LpO7rJPT8ztBE3l51QjFQKvdKn2gNKXzOzQCk7dhM9SSElHUkAqqwwzvMg1v%2FUaEccn7MgO7Y4II5KEZn2dzyz4a0T1%2B%2BGC3KycRkHR4XdapVPJrgvr6NsbLF%2B9edM8nSjk1LAN0PwEVIc7SF6BQCiQsrWZU094yB3E2YI%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20220125T105619Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAUDZQDNSGFJH3TJXT%2F20220125%2Fap-southeast-1%2Fs3%2Faws4_request&X-Amz-Signature=3bbff872f9dd992d512bfdd05222788df01344112c239a529ff14ac6b297ca54"

        if prediction:
            prediction.audio_url = ""
            prediction.log_to_airtable()
            prediction = prediction.type

        assert prediction == verdict


if __name__ == "__main__":
    main()
