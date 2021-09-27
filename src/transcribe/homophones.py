import collections
from difflib import SequenceMatcher
from metaphone import doublemetaphone

"""
English Homophones: 
- https://www.englishclub.com/pronunciation/homophones-list.htm

Indonesian Homophones:
- https://masteringbahasa.com/indonesian-homophone
- https://www.learnindonesian.education/single-post/indonesia-homophones
"""
HOMOPHONES = {
    "en": {
        "AR": ["air", "oar", "wear", "where"],
        "HRR": ["heir"],
        "AL": ["aisle", "isle", "whole"],
        "A": ["eye", "way", "weigh"],
        "AA": ["I"],
        "PR": ["bare", "pair", "poor", "pray", "prey"],
        "PRR": ["bear", "pear", "pour"],
        "P": ["be", "bee", "buy", "by"],
        "PRK": ["brake"],
        "PRKK": ["break"],
        "SL": ["cell", "sail", "sale", "sole"],
        "SLL": ["sell", "soul"],
        "SNT": ["cent"],
        "SNTT": ["scent"],
        "SRL": ["cereal"],
        "SRLL": ["serial"],
        "KRS": ["coarse", "course"],
        "KMPLMNT": ["complement"],
        "KMPLMNTT": ["compliment"],
        "TM": ["dam"],
        "TMNN": ["damn"],
        "TR": ["dear"],
        "TRR": ["deer"],
        "T": ["die", "dye", "to", "too", "toe", "tow"],
        "FR": ["fair", "fare", "fir", "for"],
        "FRR": ["fur", "four"],
        "FLR": ["flour"],
        "FLRR": ["flower"],
        "HR": ["hair", "hare", "hear", "here", "hour"],
        "HL": ["heal", "hole"],
        "HLL": ["heel"],
        "HM": ["him"],
        "HMNN": ["hymn"],
        "ARR": ["our", "or"],
        "ATL": ["idle"],
        "ATLL": ["idol"],
        "AN": ["in", "one"],
        "ANN": ["inn", "won"],
        "NT": ["knight", "knot"],
        "NTT": ["night", "not"],
        "N": ["know", "no"],
        "MT": ["made", "meat"],
        "MTT": ["maid", "meet"],
        "ML": ["mail", "male"],
        "MRNNK": ["morning"],
        "MRNNKK": ["mourning"],
        "NN": ["none"],
        "NNN": ["nun"],
        "PS": ["peace"],
        "PSS": ["piece"],
        "PLN": ["plain", "plane"],
        "PRNSPL": ["principal", "principle"],
        "PRFT": ["profit"],
        "PRFTT": ["prophet"],
        "RL": ["real"],
        "RLL": ["reel"],
        "RT": ["right", "write", "root", "route"],
        "S": ["sea", "see", "sew", "so"],
        "SM": ["seam", "some"],
        "SMM": ["seem", "sum"],
        "ST": ["sight", "site", "suite"],
        "XR": ["shore"],
        "SR": ["sure"],
        "SN": ["son"],
        "SNN": ["sun"],
        "STR": ["stair", "stare"],
        "STXNR": ["stationary", "stationery"],
        "STL": ["steal"],
        "STLL": ["steel"],
        "STT": ["sweet"],
        "TL": ["tail", "tale"],
        "0R": ["their", "there"],
        "AST": ["waist", "waste"],
        "AT": ["wait"],
        "ATT": ["weight"],
        "AK": ["weak"],
        "AKK": ["week"],
    },
    "id": {
        "MS": ["masa", "massa"],
        "RK": ["rok"],
        "RKK": ["rock"],
        "PNK": ["bank"],
        "PNKK": ["bang"],
        "TJ": ["tuju", "tujuh"],
        "TNK": ["tank"],
        "TNKK": ["tang"],
        "SNKS": ["sanksi", "sangsi"],
        "SRT": ["syarat"],
        "SRTT": ["sarat"],
        "KS": ["khas"],
        "KSS": ["kas"],
        "PPT": ["babat", "babad"],
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

        self.metaphone, _ = doublemetaphone(str(seq))
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
        if self.homophones.get(self.metaphone) and other in self.homophones.get(
            self.metaphone
        ):
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


def match_sequence(list1, list2, homophones):
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
    for _list in [list1, list2]:
        for word in _list:
            metaphone, _ = doublemetaphone(word)
            if (
                metaphone in homophones
                and word not in homophones[metaphone]
                and metaphone != ""
            ):
                homophones[metaphone] += [word]
            elif metaphone not in homophones and metaphone != "":
                homophones[metaphone] = [word]

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
