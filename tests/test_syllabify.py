import pytest

from mousike import syllabify, syllabify_word


@pytest.mark.parametrize("word, expected", [
    ("οσον", ["ο", "σον"]),
    ("φαινου", ["φαι", "νου"]),         # diphthongs
    ("απαιτει", ["α", "παι", "τει"]),
    ("εστι", ["ε", "στι"]),             # στ can begin a word
    ("χρονος", ["χρο", "νος"]),
    ("ολιγον", ["ο", "λι", "γον"]),
    ("ἄλλος", ["ἄλ", "λος"]),           # double consonant splits
    ("ἄγγελος", ["ἄγ", "γε", "λος"]),
    ("ἀνθρώπου", ["ἀν", "θρώ", "που"]),
    ("ἀΐδιος", ["ἀ", "ΐ", "δι", "ος"]),  # diaeresis breaks diphthong
    ("ζην", ["ζην"]),
    ("ἐκ", ["ἐκ"]),
    ("οὐρανοῦ,", ["οὐ", "ρα", "νοῦ,"]),  # punctuation kept on last syllable
])
def test_syllabify_word(word, expected):
    assert syllabify_word(word) == expected


def test_syllabify_passage():
    assert syllabify("οσον ζης φαινου") == [["ο", "σον"], ["ζης"], ["φαι", "νου"]]
