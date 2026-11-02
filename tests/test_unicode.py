import pytest

from mousike import load_pitch_table, note_to_unicode, notes_to_unicode


def test_table_size():
    # 3 x 23 + 1 vocal, same instrumental, plus the rest
    assert len(load_pitch_table()) == 141


def test_examples_from_docs():
    assert note_to_unicode("gvn:1.1") == "\U0001D200"
    assert note_to_unicode("gvn:1.2") == "\U0001D201"
    assert note_to_unicode("gvn:11.1.1.0.0") == "Ϲ"


def test_full_urn_accepted():
    assert note_to_unicode("urn:cite2:zst:gvn:11.1.1.0.0") == "Ϲ"


def test_prime_symbols():
    assert note_to_unicode("gvn:19.1.1.0.0") == "Ο′"


def test_rest():
    assert note_to_unicode("gcn:1") == "\U0001D245"


def test_instrumental_distinct_from_vocal():
    assert note_to_unicode("gin:1.1") != note_to_unicode("gvn:1.1")


def test_spacing_and_joins():
    s = ("gvn:11.1.1.0.0 gvn:15.1.2.0.0 gvn:15.1.3.1.0 "
         "gvn:13.3.1.0.0~gvn:14.1.1.0.0~gvn:15.1.1.0.0 gvn:14.1.3.1.1")
    assert notes_to_unicode(s) == "Ϲ Ζ\u0305 Ζ\U0001D242\u0307 ΚΙΖ Ι\U0001D242\u0307"


def test_extra_whitespace_collapsed():
    assert notes_to_unicode("  gvn:11.1.1.0.0\n\tgvn:12.1.1.0.0 ") == "Ϲ Ο"


def test_unknown_note():
    with pytest.raises(ValueError):
        note_to_unicode("gvn:99.1.1.0.0")


def test_seikilos_passages():
    import pathlib
    data = pathlib.Path(__file__).parents[1] / "editions" / "seikilos_notation.cex"
    if not data.exists():
        pytest.skip("Seikilos data not present")
    for line in data.read_text(encoding="utf-8").splitlines()[1:]:
        _, notes = line.split("|", 1)
        out = notes_to_unicode(notes)
        assert len(out.split(" ")) == len(notes.split())


# --- note URNs in running text -------------------------------------------

from mousike import note_urn_spans, urns_to_unicode  # noqa: E402


def test_urns_to_unicode_short_and_full():
    assert urns_to_unicode("gvn:11.1 urn:cite2:zst:gvn:11.1") == "Ϲ Ϲ"


def test_urns_to_unicode_joined_group():
    assert urns_to_unicode("gvn:13.3~gvn:14.1") == "ΚΙ"


def test_urns_to_unicode_keeps_surrounding_text_and_punctuation():
    assert urns_to_unicode("ὅσον (gvn:11.1.1.0.0), ζῆς.\nNext: gcn:1.") == (
        "ὅσον (Ϲ), ζῆς.\nNext: \U0001D245.")


def test_urns_to_unicode_marks():
    assert urns_to_unicode("gvn:15.1.2.0.0") == "Ζ̅"


def test_unknown_urn_left_alone_and_reported():
    assert urns_to_unicode("gvn:99.1") == "gvn:99.1"
    [(src, uni, err)] = note_urn_spans("gvn:99.1")
    assert (src, uni) == ("gvn:99.1", None) and "gvn:99.1" in err


@pytest.mark.parametrize("text", [
    "xgvn:11.1",        # part of a longer word
    "gvn:11.1:x",       # part of a longer URN
    "abc.gvn:11.1",
    "gvx:11.1",         # not a note collection
])
def test_not_a_note_urn(text):
    assert note_urn_spans(text) == [(text, None, None)]


def test_spans_cover_whole_text():
    text = "a gvn:11.1 b gvn:99.9 c"
    spans = note_urn_spans(text)
    assert "".join(src for src, _, _ in spans) == text
    assert [uni is not None for _, uni, _ in spans] == [False, True, False, False, False]
    assert spans[3][2] is not None
