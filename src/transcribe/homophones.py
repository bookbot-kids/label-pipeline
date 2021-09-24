import collections
from difflib import SequenceMatcher

"""
English Homophones: 
- https://www.englishclub.com/pronunciation/homophones-list.htm

Indonesian Homophones:
- https://masteringbahasa.com/indonesian-homophone
- https://www.learnindonesian.education/single-post/indonesia-homophones
"""
HOMOPHONES = {
    "en": {
        "air": ["heir"],
        "aisle": ["isle"],
        "eye": ["I"],
        "bare": ["bear"],
        "be": ["bee"],
        "brake": ["break"],
        "buy": ["by"],
        "cell": ["sell"],
        "cent": ["scent"],
        "cereal": ["serial"],
        "coarse": ["course"],
        "complement": ["compliment"],
        "dam": ["damn"],
        "dear": ["deer"],
        "die": ["dye"],
        "fair": ["fare"],
        "fir": ["fur"],
        "flour": ["flower"],
        "for": ["four"],
        "hair": ["hare"],
        "heal": ["heel"],
        "hear": ["here"],
        "him": ["hymn"],
        "hole": ["whole"],
        "hour": ["our"],
        "idle": ["idol"],
        "in": ["inn"],
        "knight": ["night"],
        "knot": ["not"],
        "know": ["no"],
        "made": ["maid"],
        "mail": ["male"],
        "meat": ["meet"],
        "morning": ["mourning"],
        "none": ["nun"],
        "oar": ["or"],
        "one": ["won"],
        "pair": ["pear"],
        "peace": ["piece"],
        "plain": ["plane"],
        "poor": ["pour"],
        "pray": ["prey"],
        "principal": ["principle"],
        "profit": ["prophet"],
        "real": ["reel"],
        "right": ["write"],
        "root": ["route"],
        "sail": ["sale"],
        "sea": ["see"],
        "seam": ["seem"],
        "sight": ["site"],
        "sew": ["so"],
        "shore": ["sure"],
        "sole": ["soul"],
        "some": ["sum"],
        "son": ["sun"],
        "stair": ["stare"],
        "stationary": ["stationery"],
        "steal": ["steel"],
        "suite": ["sweet"],
        "tail": ["tale"],
        "their": ["there"],
        "to": ["too", "two"],
        "toe": ["tow"],
        "waist": ["waste"],
        "wait": ["weight"],
        "way": ["weigh"],
        "weak": ["week"],
        "wear": ["where"],
    },
    "id": {
        "masa": ["massa"],
        "rok": ["rock"],
        "bank": ["bang"],
        "tuju": ["tujuh"],
        "tank": ["tang"],
        "sanksi": ["sangsi"],
        "syarat": ["sarat"],
        "khas": ["kas"],
        "babat": ["babad"],
    },
}


class HomophoneString(collections.UserString):
    """
    String that treats homophones as equals.

    ...

    Attributes
    ----------
    data : str
        Plain string-value of string.
    homophones : Dict[str, List[str]]
        Dictionary of list of homophones given a word.
    inverse_homophones : Dict[str, List[str]]
        Inverse dictionary of `homophones`.
    """

    def __init__(self, seq, homophones, inverse_homophones):
        """Constructor for HomophoneString.

        Parameters
        ----------
        seq : str
            Value of string for self.
        homophones : Dict[str, List[str]]
            Dictionary of list of homophones given a word.
        inverse_homophones : Dict[str, List[str]]
            Inverse dictionary of `homophones`.
        """
        super().__init__(seq)

        self.homophones = homophones
        self.inverse_homophones = inverse_homophones

    def __eq__(self, other):
        """Overrides equal operator for strings with option for homophones.

        Parameters
        ----------
        other : str
            String to be compared with self.

        Returns
        -------
        bool
            Whether the strings are equal or homophones with each other.
        """
        if self.homophones.get(other) and self.data in self.homophones.get(other):
            return True
        return self.data == other

    def __hash__(self):
        """Hashing method for HomophoneString.

        Returns
        -------
        int
            Hashes self string value if no homophones are found, else hash the homophone equivalent.
        """
        if str(self.data) in self.inverse_homophones:
            return hash(self.inverse_homophones[self.data])
        return hash(self.data)


def match_sequence_homophones(list1, list2, homophones):
    """Finds index of overlaps between two lists given a homophone mapping.

    Parameters
    ----------
    list1 : List[str]
        List of words in a sequence.
    list2 : List[str]
        List of words in another sequence for matching/comparison.
    homophones : Dict[str, List[str]]
        Dictionary of list of homophones given a word.

    Returns
    -------
    List[List[int], List[int]]
        Pair of lists containing list of indices of overlap.
    """
    inverse_homophones = {
        string: key for key, value in homophones.items() for string in value
    }

    # promotes all plain Python string to HomophoneString for matching
    list1 = [HomophoneString(s, homophones, inverse_homophones) for s in list1]
    list2 = [HomophoneString(s, homophones, inverse_homophones) for s in list2]

    output1, output2 = [], []
    s = SequenceMatcher(None, list1, list2)
    # find all matching sequences between two sentences
    blocks = s.get_matching_blocks()

    for bl in blocks:
        for bi in range(bl.size):
            # index of word in sequence 1
            cur_a = bl.a + bi
            # index of word in sequence 2
            cur_b = bl.b + bi
            output1.append(cur_a)
            output2.append(cur_b)

    assert len(output1) == len(output2)

    return [output1, output2]
