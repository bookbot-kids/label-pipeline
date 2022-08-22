import sys

sys.path.append("src")
from transcribe.homophones import HOMOPHONES, match_sequence


print(
    match_sequence(
        ["jancok", "hi", "my", "name", "is", "bob"],
        ["hi", "my", "name", "is", "alice"],
        HOMOPHONES["en"],
    )
)
