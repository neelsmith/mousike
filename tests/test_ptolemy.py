from fractions import Fraction as F

import pytest

from mousike import DIVISIONS, PtolemaicSystem, load_tonoi, system_ratios
from mousike.ptolemy import CENTRAL_OCTAVE, DEGREES, Division, step_ratio

FIXED = ("proslambanomenos", "hypate hypaton", "hypate meson", "mese",
         "paramese", "nete diezeugmenon", "nete hyperbolaion", "nete synemmenon")


def test_eight_divisions():
    assert len(DIVISIONS) == 8


@pytest.mark.parametrize("key", list(DIVISIONS))
def test_tetrachord_is_a_fourth(key):
    a, b, c = DIVISIONS[key].intervals
    assert a * b * c == F(4, 3)


def test_bad_division_rejected():
    with pytest.raises(ValueError):
        Division("x", "x", "x", (F(9, 8), F(9, 8), F(9, 8)))


def test_cents_computed():
    assert DIVISIONS["tonic_diatonic"].cents[0] == pytest.approx(62.96, abs=0.01)


def test_fixed_notes():
    r = system_ratios("tense_diatonic")
    assert [r[n] for n in FIXED] == [1, F(9, 8), F(3, 2), 2, F(9, 4), 3, 4, F(8, 3)]
    for key in DIVISIONS:   # fixed notes don't depend on the division
        assert all(system_ratios(key)[n] == r[n] for n in FIXED)


def test_movable_notes():
    r = system_ratios("tense_diatonic")
    assert r["parhypate hypaton"] == F(9, 8) * F(16, 15)
    assert r["lichanos meson"] == F(3, 2) * F(16, 15) * F(9, 8)
    assert r["trite synemmenon"] == 2 * F(16, 15)


def test_octave_periodicity():
    for i in range(-7, 15):
        assert step_ratio("soft_chromatic", i + 7) == 2 * step_ratio("soft_chromatic", i)


def test_seven_tonoi():
    tonoi = load_tonoi()
    assert [t.name for t in sorted(tonoi.values(), key=lambda t: t.order)] == [
        "Hypodorian", "Hypophrygian", "Hypolydian", "Dorian",
        "Phrygian", "Lydian", "Mixolydian"]


def test_dorian_thetic_equals_dynamic():
    s = PtolemaicSystem("tense_diatonic", "Dorian")
    for name in DEGREES:
        assert s.thetic_ratio(name) == s.dynamic_ratio(name)
        assert s.dynamic_name(name) == name


def test_dorian_central_octave():
    s = PtolemaicSystem("tense_diatonic", "dorian")
    assert list(s.central_octave().values()) == [
        1, F(16, 15), F(6, 5), F(4, 3), F(3, 2), F(8, 5), F(9, 5), 2]


@pytest.mark.parametrize("name", list(load_tonoi()))
def test_dynamic_mese_on_its_thetic_position(name):
    s = PtolemaicSystem("soft_diatonic", name)
    assert s.dynamic_name(s.tonos.thetic_mese) == "mese"
    assert s.thetic_ratio(s.tonos.thetic_mese) == s.dynamic_ratio("mese")


@pytest.mark.parametrize("name", list(load_tonoi()))
@pytest.mark.parametrize("division", list(DIVISIONS))
def test_central_octave_is_a_rotation(name, division):
    """Each tonos's central octave has the intervals of the Dorian system,
    rotated so the dynamic mese lands on its thetic position."""
    s = PtolemaicSystem(division, name)
    octave = list(s.central_octave().values())
    assert octave[0] == 1 and octave[-1] == 2
    steps = [b / a for a, b in zip(octave, octave[1:])]
    k = s.tonos.shift
    expected = [step_ratio(division, 4 + k + i + 1) / step_ratio(division, 4 + k + i)
                for i in range(7)]
    assert steps == expected


def test_mixolydian_species():
    # B-b: S T T S T T T in tense diatonic
    s = PtolemaicSystem("tense_diatonic", "mixolydian")
    assert s.dynamic_name("hypate meson") == "hypate hypaton"
    assert s.dynamic_name("paranete diezeugmenon") == "mese"


def test_tonoi_pitch_order():
    """Dynamic mese rises T T S T T S from Hypodorian to Mixolydian."""
    meses = [PtolemaicSystem("ditonic_diatonic", t).dynamic_ratio("mese")
             for t in sorted(load_tonoi(), key=lambda n: load_tonoi()[n].order)]
    steps = [b / a for a, b in zip(meses, meses[1:])]
    limma = F(256, 243)
    assert steps == [F(9, 8), F(9, 8), limma, F(9, 8), F(9, 8), limma]
    assert meses[-1] / meses[0] == F(16, 9)


def test_frequencies():
    s = PtolemaicSystem("tense_diatonic", "dorian")
    assert s.thetic_frequency("hypate meson") == pytest.approx(165.0)
    assert s.dynamic_frequency("mese") == pytest.approx(220.0)
    assert PtolemaicSystem("tense_diatonic", "hypodorian").dynamic_frequency(
        "mese") == pytest.approx(165.0)


def test_out_of_range_dynamic_name():
    s = PtolemaicSystem("tense_diatonic", "mixolydian")
    assert s.dynamic_name("proslambanomenos") is None


@pytest.mark.parametrize("bad", [("nope", "dorian"), ("tense_diatonic", "iastian")])
def test_unknown_names(bad):
    with pytest.raises(ValueError):
        PtolemaicSystem(*bad)
