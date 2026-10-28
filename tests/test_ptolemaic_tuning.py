import pathlib

import pytest

from mousike import (Note, PtolemaicTuning, TuningMismatch, edition_to_midi,
                     midi_bytes, parse_notes)
from mousike.align import read_cex
from mousike.tuning import thetic_index

DATA = pathlib.Path(__file__).parents[1] / "editions"
SEIKILOS_SIGNS = ["gvn:8.1", "gvn:9.3", "gvn:10.1", "gvn:11.1", "gvn:12.1",
                  "gvn:13.3", "gvn:14.1", "gvn:15.1"]


def test_letter_gives_thetic_string():
    t = PtolemaicTuning("tense_diatonic", "dorian")
    assert t.string(Note("gvn:8.1")) == "hypate meson"
    assert t.string(Note("gvn:11.1")) == "mese"
    assert t.string(Note("gvn:15.1")) == "nete diezeugmenon"
    assert t.string(Note("gvn:4.1")) == "proslambanomenos"
    assert t.string(Note("gvn:13.3")) == t.string(Note("gvn:13.1"))


def test_dorian_frequencies():
    t = PtolemaicTuning("tense_diatonic", "dorian")
    assert t.frequency(Note("gvn:8.1")) == pytest.approx(165.0)
    assert t.frequency(Note("gvn:11.1")) == pytest.approx(220.0)
    assert t.frequency(Note("gvn:13.1")) == pytest.approx(165 * 8 / 5)   # c′


@pytest.mark.parametrize("division", ["tense_diatonic", "ditonic_diatonic",
                                      "soft_diatonic", "tonic_diatonic",
                                      "even_diatonic"])
def test_seikilos_signs_fit_phrygian(division):
    t = PtolemaicTuning(division, "phrygian")
    for urn in SEIKILOS_SIGNS:
        assert t.frequency(Note(urn)) > 0


def test_phrygian_sharpened_strings():
    t = PtolemaicTuning("tense_diatonic", "phrygian")
    assert t.frequency(Note("gvn:13.3")) == pytest.approx(275.0)     # c♯′
    assert t.frequency(Note("gvn:9.3")) == pytest.approx(165 * 10 / 9)  # f♯


def test_wrong_tonos_raises():
    # Seikilos's c♯′ doesn't fit Dorian, where that string is c′
    t = PtolemaicTuning("tense_diatonic", "dorian")
    with pytest.raises(TuningMismatch, match="trite diezeugmenon"):
        t.frequency(Note("gvn:13.3"))


def test_sign_not_in_tonos_raises():
    t = PtolemaicTuning("tense_diatonic", "phrygian")
    with pytest.raises(TuningMismatch):
        t.frequency(Note("gvn:13.1"))       # plain c′ where Phrygian has c♯′


def test_tolerance_is_adjustable():
    t = PtolemaicTuning("tense_diatonic", "dorian", tolerance_cents=100)
    assert t.frequency(Note("gvn:13.3")) == pytest.approx(264.0)


def test_rest():
    assert PtolemaicTuning("tense_diatonic", "dorian").frequency(Note("gcn:1")) is None


@pytest.mark.parametrize("division", ["enharmonic", "soft_chromatic", "tense_chromatic"])
def test_non_diatonic_rejected(division):
    with pytest.raises(ValueError, match="only diatonic"):
        PtolemaicTuning(division, "dorian")


def test_both_required():
    with pytest.raises(TypeError):
        PtolemaicTuning("tense_diatonic")


def test_outside_two_octaves():
    t = PtolemaicTuning("tense_diatonic", "dorian", tolerance_cents=60)
    # base 3 (G) is one step below proslambanomenos
    assert thetic_index(Note("gvn:3.1")) == -1
    assert t.frequency(Note("gvn:3.1")) == pytest.approx(110 * 9 / 10)   # G: 10/9 below A


def test_midi_error_leaves_no_file(tmp_path):
    p = tmp_path / "x.mid"
    from mousike import write_midi
    with pytest.raises(TuningMismatch):
        write_midi(p, [["gvn:13.3"]], PtolemaicTuning("tense_diatonic", "dorian"))
    assert not p.exists()


def test_seikilos_midi(tmp_path):
    mido = pytest.importorskip("mido")
    text, notes = DATA / "seikilos_text.cex", DATA / "seikilos_notation.cex"
    if not (text.exists() and notes.exists()):
        pytest.skip("Seikilos data not present")
    p = tmp_path / "s.mid"
    edition_to_midi(p, text, notes, PtolemaicTuning("tense_diatonic", "phrygian"))
    msgs = [m for m in mido.MidiFile(p, charset="utf-8").tracks[0]]
    keys = [m.note for m in msgs if m.type == "note_on"]
    bends = [m.pitch for m in msgs if m.type == "pitchwheel"]
    assert keys[:7] == [57, 64, 64, 61, 62, 64, 62]   # same melody as nominal
    # c♯′ is 275 Hz, about 14 cents flat of 12-TET C♯4
    assert -620 < bends[3] < -540
