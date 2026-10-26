import pathlib

import pytest

from mousike import AlignmentError, align_editions, align_passage

DATA = pathlib.Path(__file__).parents[1] / "data"


def test_align_passage():
    p = align_passage(
        "οσον ζης φαινου",
        "gvn:11.1.1.0.0 gvn:15.1.2.0.0 gvn:15.1.3.1.0 "
        "gvn:13.3.1.0.0~gvn:14.1.1.0.0~gvn:15.1.1.0.0 gvn:14.1.3.1.1",
    )
    assert [(s.syllable, s.notes) for s in p.syllables] == [
        ("ο", "Ϲ"), ("σον", "Ζ"), ("ζης", "Ζ"), ("φαι", "ΚΙΖ"), ("νου", "Ι"),
    ]
    assert [s.word_final for s in p.syllables] == [False, True, True, False, True]


def test_mismatch_raises():
    with pytest.raises(AlignmentError):
        align_passage("οσον", "gvn:11.1.1.0.0")


def test_seikilos():
    text, notes = DATA / "seikilos_text.cex", DATA / "seikilos_notation.cex"
    if not (text.exists() and notes.exists()):
        pytest.skip("Seikilos data not present")
    passages = align_editions(text, notes)
    assert [p.ref for p in passages] == ["1", "2", "3", "4"]
    assert [len(p.syllables) for p in passages] == [5, 7, 8, 9]
    assert passages[3].syllables[-1].syllable == "τει"
    assert passages[3].syllables[-1].notes == "ϹΧ𝈕"
