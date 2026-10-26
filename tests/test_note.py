import pytest

from mousike import Note, parse_note_groups, parse_notes


def test_tiers():
    n = Note("gvn:14.1.3.1.1")
    assert (n.collection, n.base, n.sharpening) == ("gvn", 14, 1)
    assert (n.length, n.arsis, n.hyphen) == (3, True, True)


def test_unicode_and_name():
    n = Note("gvn:1.1.1.0.0")
    assert n.unicode == "\U0001D200"
    assert n.name == "vocal E"
    assert Note("gvn:1.2.1.0.0").name == "vocal first sharp of E"
    assert Note("gin:1.1.1.0.0").name == "instrumental E"


def test_flags_false():
    n = Note("gvn:11.1.1.0.0")
    assert n.arsis is False and n.hyphen is False and n.length == 1


def test_defaults_for_short_urn():
    n = Note("gvn:11.1")
    assert (n.length, n.arsis, n.hyphen) == (1, False, False)
    assert n.urn == "gvn:11.1.1.0.0"


def test_full_urn_roundtrip():
    n = Note("urn:cite2:zst:gvn:11.1.2.0.0")
    assert n.urn == "gvn:11.1.2.0.0"
    assert n.full_urn == "urn:cite2:zst:gvn:11.1.2.0.0"
    assert Note(n.full_urn) == n
    assert str(n) == "gvn:11.1.2.0.0"
    assert repr(n) == "Note('gvn:11.1.2.0.0')"


def test_rest():
    r = Note("gcn:1")
    assert r.sharpening is None and r.name == "rest" and r.unicode == "\U0001D245"


def test_equality_and_hash():
    assert Note("gvn:11.1.1.0.0") == Note("gvn:11.1")
    assert Note("gvn:11.1.1.0.0") != Note("gvn:11.1.1.1.0")
    assert len({Note("gvn:11.1.1.0.0"), Note("gvn:11.1")}) == 1


def test_vocal_instrumental():
    assert Note("gvn:1.1").vocal and not Note("gvn:1.1").instrumental
    assert Note("gin:1.1").instrumental


def test_immutable():
    with pytest.raises(AttributeError):
        Note("gvn:1.1").length = 2


@pytest.mark.parametrize("bad", [
    "gvn", "gvn:", "gvn:99.1", "gvn:1.4", "xyz:1.1", "gvn:1.1.6.0.0",
    "gvn:1.1.1.2.0", "gvn:1.1.1.0.x", "gvn:1.1.1.0.0.0", "gvn:1",
])
def test_invalid(bad):
    with pytest.raises(ValueError):
        Note(bad)


def test_parse_notes():
    s = ("gvn:11.1.1.0.0 gvn:15.1.2.0.0 gvn:15.1.3.1.0 "
         "gvn:13.3.1.0.0~gvn:14.1.1.0.0~gvn:15.1.1.0.0 gvn:14.1.3.1.1")
    notes = parse_notes(s)
    assert len(notes) == 7
    assert all(isinstance(n, Note) for n in notes)
    assert [n.length for n in notes] == [1, 2, 3, 1, 1, 1, 3]
    assert "".join(n.unicode for n in notes) == "ϹΖΖΚΙΖΙ"


def test_parse_note_groups():
    groups = parse_note_groups("gvn:11.1.1.0.0 gvn:13.3.1.0.0~gvn:14.1.1.0.0")
    assert [[n.urn for n in g] for g in groups] == [
        ["gvn:11.1.1.0.0"], ["gvn:13.3.1.0.0", "gvn:14.1.1.0.0"],
    ]
