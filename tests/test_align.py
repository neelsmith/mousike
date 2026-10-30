import pathlib

import pytest

from mousike import (AlignmentError, align_editions, align_passage,
                     align_syllable_passage, align_syllables, parse_note_groups)
from mousike.align import group_syllables, read_cex

DATA = pathlib.Path(__file__).parents[1] / "editions"


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


def test_align_syllable_passage():
    p = align_syllable_passage(
        ["ο-", "σον", "ζης", "φαι-", "νου"],
        "gvn:11.1.1.0.0 gvn:15.1.2.0.0 gvn:15.1.3.1.0 "
        "gvn:13.3.1.0.0~gvn:14.1.1.0.0~gvn:15.1.1.0.0 gvn:14.1.3.1.1",
        "1",
    )
    assert [(s.syllable, s.notes) for s in p.syllables] == [
        ("ο", "Ϲ"), ("σον", "Ζ̅"), ("ζης", "Ζ\U0001D242̇"),
        ("φαι", "ΚΙΖ"), ("νου", "Ι\U0001D242̇"),
    ]
    assert [s.word_final for s in p.syllables] == [False, True, True, False, True]
    assert [s.word_index for s in p.syllables] == [0, 0, 1, 2, 2]


def test_syllable_mismatch_raises():
    with pytest.raises(AlignmentError):
        align_syllable_passage(["ο-", "σον"], "gvn:11.1.1.0.0")


def test_group_syllables():
    assert group_syllables({"1.1": "ο-", "1.2": "σον", "2.1": "ζης"}) == {
        "1": ["ο-", "σον"], "2": ["ζης"]}
    with pytest.raises(ValueError):
        group_syllables({"1": "οσον"})


def test_align_syllables_file(tmp_path):
    sylls = tmp_path / "demo_syllables.cex"
    sylls.write_text(
        "urn|text\n"
        "urn:cts:m:demo.syllables:1.1|ο-\n"
        "urn:cts:m:demo.syllables:1.2|σον\n"
        "urn:cts:m:demo.syllables:2.1|ζης\n"
        "urn:cts:m:demo.syllables:3.1|συ\n", encoding="utf-8")
    notes = tmp_path / "demo_notation.cex"
    notes.write_text(
        "urn|text\n"
        "urn:cts:m:demo.notes:1|gvn:11.1.1.0.0 gvn:15.1.2.0.0\n"
        "urn:cts:m:demo.notes:2|gvn:13.3.1.0.0~gvn:14.1.1.0.0\n", encoding="utf-8")
    passages = align_syllables(sylls, notes)
    assert [p.ref for p in passages] == ["1", "2"]   # 3 has no notation
    assert [s.syllable for p in passages for s in p.syllables] == ["ο", "σον", "ζης"]
    assert passages[1].syllables[0].notes == "ΚΙ"


def test_seikilos_syllables():
    sylls, notes = DATA / "seikilos_syllables.cex", DATA / "seikilos_notation.cex"
    if not (sylls.exists() and notes.exists()):
        pytest.skip("Seikilos data not present")
    passages = align_syllables(sylls, notes)
    assert [len(p.syllables) for p in passages] == [
        len(parse_note_groups(n)) for n in read_cex(notes).values()]
    assert passages[-1].syllables[-1].syllable == "τει"


def test_display_columns_ignore_combining_marks():
    from mousike import align_passage
    p = align_passage("οσον", "gvn:15.1.3.1.0 gvn:11.1.1.0.0", "1")
    top, bottom = str(p).split("\n")
    # the second column starts at the same visible position on both lines
    import unicodedata
    visible = lambda s: "".join(c for c in s if not unicodedata.combining(c))
    assert visible(top).index("Ϲ") == bottom.index("σον")
