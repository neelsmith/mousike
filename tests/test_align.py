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
        ("ο", "Ϲ"), ("σον", "Ζ\u0305"), ("ζης", "Ζ\U0001D242\u0307"),
        ("φαι", "ΚΙΖ"), ("νου", "Ι\U0001D242\u0307"),
    ]
    assert ["".join(n.pitch_unicode for n in s.note_group) for s in p.syllables] == [
        "Ϲ", "Ζ", "Ζ", "ΚΙΖ", "Ι"]
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
    # gvn:11.1.1.1.1 ~ gvn:9.3.2.1.1 ~ gvn:8.1.2.1.1: arsis; diseme + arsis (x2)
    assert passages[3].syllables[-1].notes == "Ϲ\u0307Χ\u0305\u0307𝈕\u0305\u0307"


def test_display_columns_ignore_combining_marks():
    from mousike import align_passage
    p = align_passage("οσον", "gvn:15.1.3.1.0 gvn:11.1.1.0.0", "1")
    top, bottom = str(p).split("\n")
    # the second column starts at the same visible position on both lines
    import unicodedata
    visible = lambda s: "".join(c for c in s if not unicodedata.combining(c))
    assert visible(top).index("Ϲ") == bottom.index("σον")
