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

from difflib import SequenceMatcher
from typing import List, Set, Tuple

"""
English Homophones:
- http://www.singularis.ltd.uk/bifroest/misc/homophones-list.html

Indonesian Homophones:
- https://masteringbahasa.com/indonesian-homophone
- https://www.learnindonesian.education/single-post/indonesia-homophones
"""
HOMOPHONES = {
    "en": [
        {"accessary", "accessory"},
        {"ad", "add"},
        {"ail", "ale"},
        {"air", "heir"},
        {"aisle", "I'll", "isle"},
        {"alf", "elf"},
        {"all", "awl"},
        {"allowed", "aloud"},
        {"alms", "arms"},
        {"altar", "alter"},
        {"arc", "ark"},
        {"aren't", "aunt"},
        {"ate", "eight"},
        {"auger", "augur"},
        {"auk", "orc"},
        {"aural", "oral"},
        {"away", "aweigh"},
        {"awe", "oar", "or", "ore"},
        {"axel", "axle"},
        {"aye", "eye", "I"},
        {"bail", "bale"},
        {"bait", "bate"},
        {"baize", "bays"},
        {"bald", "bawled"},
        {"ball", "bawl"},
        {"band", "banned"},
        {"bard", "barred"},
        {"bare", "bear"},
        {"bark", "barque"},
        {"baron", "barren"},
        {"base", "bass"},
        {"bay", "bey"},
        {"bazaar", "bizarre"},
        {"be", "bee", "b"},
        {"beach", "beech"},
        {"bean", "been"},
        {"beat", "beet"},
        {"beau", "bow"},
        {"beer", "bier"},
        {"bel", "bell", "belle"},
        {"berry", "bury"},
        {"berth", "birth"},
        {"bight", "bite", "byte"},
        {"billed", "build"},
        {"bitten", "bittern"},
        {"blew", "blue"},
        {"bloc", "block"},
        {"boar", "bore"},
        {"board", "bored"},
        {"boarder", "border"},
        {"bold", "bowled"},
        {"boos", "booze"},
        {"born", "borne"},
        {"bough", "bow"},
        {"boy", "buoy"},
        {"brae", "bray"},
        {"braid", "brayed"},
        {"braise", "brays", "braze"},
        {"brake", "break"},
        {"bread", "bred"},
        {"brews", "bruise"},
        {"bridal", "bridle"},
        {"broach", "brooch"},
        {"bur", "burr"},
        {"but", "butt"},
        {"buy", "by", "bye"},
        {"buyer", "byre"},
        {"calendar", "calender"},
        {"call", "caul"},
        {"canvas", "canvass"},
        {"cast", "caste"},
        {"caster", "castor"},
        {"caught", "court"},
        {"caw", "core", "corps"},
        {"cede", "seed"},
        {"ceiling", "sealing"},
        {"cell", "sell"},
        {"censer", "censor", "sensor"},
        {"cent", "scent", "sent"},
        {"cereal", "serial"},
        {"cheap", "cheep"},
        {"check", "cheque"},
        {"choir", "quire"},
        {"chord", "cord"},
        {"cite", "sight", "site"},
        {"clack", "claque"},
        {"clew", "clue"},
        {"climb", "clime"},
        {"close", "cloze"},
        {"coal", "kohl"},
        {"coarse", "course"},
        {"coign", "coin"},
        {"colonel", "kernel"},
        {"complacent", "complaisant"},
        {"complement", "compliment"},
        {"coo", "coup"},
        {"cops", "copse"},
        {"council", "counsel"},
        {"cousin", "cozen"},
        {"creak", "creek"},
        {"crews", "cruise"},
        {"cue", "kyu", "queue"},
        {"curb", "kerb"},
        {"currant", "current"},
        {"cymbol", "symbol"},
        {"dam", "damn"},
        {"days", "daze"},
        {"dear", "deer"},
        {"descent", "dissent"},
        {"desert", "dessert"},
        {"deviser", "divisor"},
        {"dew", "due"},
        {"die", "dye"},
        {"discreet", "discrete"},
        {"doe", "doh", "dough"},
        {"done", "dun"},
        {"douse", "dowse"},
        {"draft", "draught"},
        {"dual", "duel"},
        {"earn", "urn"},
        {"eery", "eyrie"},
        {"ewe", "yew", "you"},
        {"faint", "feint"},
        {"fah", "far"},
        {"fair", "fare"},
        {"farther", "father"},
        {"fate", "fÃªte"},
        {"faun", "fawn"},
        {"fay", "fey"},
        {"faze", "phase"},
        {"feat", "feet"},
        {"ferrule", "ferule"},
        {"few", "phew"},
        {"fie", "phi"},
        {"file", "phial"},
        {"find", "fined"},
        {"fir", "fur"},
        {"first", "1st"},
        {"fizz", "phiz"},
        {"flair", "flare"},
        {"flaw", "floor"},
        {"flea", "flee"},
        {"flex", "flecks"},
        {"flew", "flu", "flue"},
        {"floe", "flow"},
        {"flour", "flower"},
        {"foaled", "fold"},
        {"for", "fore", "four"},
        {"foreword", "forward"},
        {"fort", "fought"},
        {"forth", "fourth"},
        {"foul", "fowl"},
        {"franc", "frank"},
        {"freeze", "frieze"},
        {"friar", "fryer"},
        {"furs", "furze"},
        {"gait", "gate"},
        {"galipot", "gallipot"},
        {"gallop", "galop"},
        {"gamble", "gambol"},
        {"gays", "gaze"},
        {"genes", "jeans"},
        {"gild", "guild"},
        {"gilt", "guilt"},
        {"giro", "gyro"},
        {"gnaw", "nor"},
        {"gneiss", "nice"},
        {"gorilla", "guerilla"},
        {"grate", "great"},
        {"greave", "grieve"},
        {"greys", "graze"},
        {"grisly", "grizzly"},
        {"groan", "grown"},
        {"guessed", "guest"},
        {"hail", "hale"},
        {"hair", "hare"},
        {"hall", "haul"},
        {"hangar", "hanger"},
        {"hart", "heart"},
        {"haw", "hoar", "whore"},
        {"hay", "hey"},
        {"heal", "heel", "he'll"},
        {"hear", "here"},
        {"heard", "herd"},
        {"he'd", "heed"},
        {"heroin", "heroine"},
        {"hew", "hue"},
        {"hi", "high"},
        {"higher", "hire"},
        {"him", "hymn"},
        {"ho", "hoe"},
        {"hoard", "horde"},
        {"hoarse", "horse"},
        {"holey", "holy", "wholly"},
        {"hour", "our"},
        {"idle", "idol"},
        {"in", "inn"},
        {"indict", "indite"},
        {"it's", "its"},
        {"jewel", "joule"},
        {"key", "quay"},
        {"knave", "nave"},
        {"knead", "need"},
        {"knew", "new"},
        {"knight", "night"},
        {"knit", "nit"},
        {"knob", "nob"},
        {"knock", "nock"},
        {"knot", "not"},
        {"know", "no"},
        {"knows", "nose"},
        {"laager", "lager"},
        {"lac", "lack"},
        {"lade", "laid"},
        {"lain", "lane"},
        {"lam", "lamb"},
        {"laps", "lapse"},
        {"larva", "lava"},
        {"lase", "laze"},
        {"law", "lore"},
        {"lay", "ley"},
        {"lea", "lee"},
        {"leach", "leech"},
        {"lead", "led"},
        {"leak", "leek"},
        {"lean", "lien"},
        {"lessen", "lesson"},
        {"levee", "levy"},
        {"liar", "lyre"},
        {"licence", "license"},
        {"licker", "liquor"},
        {"lie", "lye"},
        {"lieu", "loo"},
        {"links", "lynx"},
        {"lo", "low"},
        {"load", "lode"},
        {"loan", "lone"},
        {"locks", "lox"},
        {"loop", "loupe"},
        {"loot", "lute"},
        {"made", "maid"},
        {"mail", "male"},
        {"main", "mane"},
        {"maize", "maze"},
        {"mall", "maul"},
        {"manna", "manner"},
        {"mantel", "mantle"},
        {"mare", "mayor"},
        {"mark", "marque"},
        {"marshal", "martial"},
        {"marten", "martin"},
        {"mask", "masque"},
        {"maw", "more"},
        {"me", "mi"},
        {"mean", "mien"},
        {"meat", "meet", "mete"},
        {"medal", "meddle"},
        {"metal", "mettle"},
        {"meter", "metre"},
        {"might", "mite"},
        {"miner", "minor", "mynah"},
        {"mind", "mined"},
        {"missed", "mist"},
        {"moat", "mote"},
        {"mode", "mowed"},
        {"moor", "more"},
        {"moose", "mousse"},
        {"morning", "mourning"},
        {"muscle", "mussel"},
        {"naval", "navel"},
        {"nay", "neigh"},
        {"nigh", "nye"},
        {"none", "nun"},
        {"od", "odd"},
        {"ode", "owed"},
        {"oh", "owe"},
        {"one", "won"},
        {"packed", "pact"},
        {"packs", "pax"},
        {"pail", "pale"},
        {"pain", "pane"},
        {"pair", "pare", "pear"},
        {"palate", "palette", "pallet"},
        {"pascal", "paschal"},
        {"paten", "patten", "pattern"},
        {"pause", "paws", "pores", "pours"},
        {"pawn", "porn"},
        {"pea", "pee"},
        {"peace", "piece"},
        {"peak", "peek", "peke", "pique"},
        {"peal", "peel"},
        {"pearl", "purl"},
        {"pedal", "peddle"},
        {"peer", "pier"},
        {"pi", "pie"},
        {"pica", "pika"},
        {"place", "plaice"},
        {"plain", "plane"},
        {"pleas", "please"},
        {"plum", "plumb"},
        {"pole", "poll"},
        {"poof", "pouffe"},
        {"practice", "practise"},
        {"praise", "prays", "preys"},
        {"principal", "principle"},
        {"profit", "prophet"},
        {"quarts", "quartz"},
        {"quean", "queen"},
        {"rain", "reign", "rein"},
        {"raise", "rays", "raze"},
        {"rap", "wrap"},
        {"raw", "roar"},
        {"read", "reed"},
        {"read", "red"},
        {"real", "reel"},
        {"reek", "wreak"},
        {"rest", "wrest"},
        {"retch", "wretch"},
        {"review", "revue"},
        {"rheum", "room"},
        {"right", "rite", "wright", "write"},
        {"ring", "wring"},
        {"road", "rode"},
        {"roe", "row"},
        {"role", "roll"},
        {"roo", "roux", "rue"},
        {"rood", "rude"},
        {"root", "route"},
        {"rose", "rows"},
        {"rota", "rotor"},
        {"rote", "wrote"},
        {"rough", "ruff"},
        {"rouse", "rows"},
        {"rung", "wrung"},
        {"rye", "wry"},
        {"saver", "savour"},
        {"spade", "spayed"},
        {"sale", "sail"},
        {"sane", "seine"},
        {"satire", "satyr"},
        {"sauce", "source"},
        {"saw", "soar", "sore"},
        {"scene", "seen"},
        {"scull", "skull"},
        {"sea", "see"},
        {"seam", "seem"},
        {"sear", "seer", "sere"},
        {"seas", "sees", "seize"},
        {"second", "2nd"},
        {"sew", "so", "sow"},
        {"shake", "sheikh"},
        {"shear", "sheer"},
        {"shoe", "shoo"},
        {"sic", "sick"},
        {"side", "sighed"},
        {"sign", "sine"},
        {"sink", "synch"},
        {"slay", "sleigh"},
        {"sloe", "slow"},
        {"sole", "soul"},
        {"some", "sum"},
        {"son", "sun"},
        {"sort", "sought"},
        {"spa", "spar"},
        {"staid", "stayed"},
        {"stair", "stare"},
        {"stake", "steak"},
        {"stalk", "stork"},
        {"stationary", "stationery"},
        {"steal", "steel"},
        {"stile", "style"},
        {"storey", "story"},
        {"straight", "strait"},
        {"sweet", "suite"},
        {"swat", "swot"},
        {"tacks", "tax"},
        {"tale", "tail"},
        {"talk", "torque"},
        {"tare", "tear"},
        {"taught", "taut", "tort"},
        {"te", "tea", "tee"},
        {"team", "teem"},
        {"tear", "tier"},
        {"teas", "tease"},
        {"terce", "terse"},
        {"tern", "turn"},
        {"there", "their", "they're"},
        {"third", "3rd"},
        {"threw", "through"},
        {"throes", "throws"},
        {"throne", "thrown"},
        {"thyme", "time"},
        {"tic", "tick"},
        {"tide", "tied"},
        {"tire", "tyre"},
        {"to", "too", "two"},
        {"toad", "toed", "towed"},
        {"told", "tolled"},
        {"tole", "toll"},
        {"ton", "tun"},
        {"tor", "tore"},
        {"tough", "tuff"},
        {"troop", "troupe"},
        {"tuba", "tuber"},
        {"vain", "vane", "vein"},
        {"vale", "veil"},
        {"vial", "vile"},
        {"wail", "wale", "whale"},
        {"wain", "wane"},
        {"waist", "waste"},
        {"wait", "weight"},
        {"waive", "wave"},
        {"wall", "waul"},
        {"war", "wore"},
        {"ware", "wear", "where"},
        {"warn", "worn"},
        {"wart", "wort"},
        {"watt", "what"},
        {"wax", "whacks"},
        {"way", "weigh", "whey"},
        {"we", "wee", "whee"},
        {"weak", "week"},
        {"we'd", "weed"},
        {"weal", "we'll", "wheel"},
        {"wean", "ween"},
        {"weather", "whether"},
        {"weaver", "weever"},
        {"weir", "we're"},
        {"were", "whirr"},
        {"wet", "whet"},
        {"wheald", "wheeled"},
        {"which", "witch"},
        {"whig", "wig"},
        {"while", "wile"},
        {"whine", "wine"},
        {"whirl", "whorl"},
        {"whirled", "world"},
        {"whit", "wit"},
        {"white", "wight"},
        {"who's", "whose"},
        {"woe", "whoa"},
        {"wood", "would"},
        {"yaw", "yore", "your", "you're"},
        {"yoke", "yolk"},
        {"you'll", "yule"},
    ],
    "id": [
        {"masa", "massa"},
        {"rok", "rock"},
        {"bank", "bang"},
        {"tuju", "tujuh"},
        {"tank", "tang"},
        {"sanksi", "sangsi"},
        {"syarat", "sarat"},
        {"khas", "kas"},
        {"babat", "babad"},
    ],
}


def create_convert(*families: List[Set[str]]) -> List[List[str]]:
    """Return a converter function that converts a list to the same list with
    only main words

    Arguments:
        families (List[Set[str]]): List of homophone families.

    Returns:
        List[List[str]]: True if all paths exist in `files`
    """
    d = {w: main for main, *alternatives in map(list, families) for w in alternatives}
    return lambda L: [d.get(w, w) for w in L]


def match_sequence(
    list1: List[str], list2: List[str], homophones: List[Set[str]]
) -> Tuple[List[int], List[int], List[Tuple[str, int, int, int, int]]]:
    """Finds index of overlaps between two lists given a homophone mapping.

    Args:
        list1 (List[str]): List of words in a sequence.
        list2 (List[str]): List of words in another sequence for matching/comparison.
        homophones (List[Set[str]]): List of homophone families.

    Returns:
        Tuple[List[int], List[int], List[Tuple[str, int, int, int, int]]]:
            Pair of lists containing list of indices of overlap.
    """
    convert = create_convert(*homophones)
    output1, output2 = [], []
    s = SequenceMatcher(None, convert(list1), convert(list2))
    opcodes = s.get_opcodes()
    for block in s.get_matching_blocks():
        for i in range(block.size):
            output1.append(block.a + i)
            output2.append(block.b + i)

    assert len(output1) == len(output2)

    return output1, output2, opcodes
