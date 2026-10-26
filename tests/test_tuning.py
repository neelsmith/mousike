import pytest

from mousike import NominalTuning, Note, bend_value, cents, midi_pitch

t = NominalTuning()


def f(urn):
    return t.frequency(Note(urn))


def test_reference():
    assert f("gvn:11.1") == pytest.approx(220.0)
    assert NominalTuning(440).frequency(Note("gvn:11.1")) == pytest.approx(440.0)


def test_grid():
    assert f("gvn:1.1") == pytest.approx(82.4069, abs=1e-3)       # E2
    assert f("gvn:8.1") == pytest.approx(2 * f("gvn:1.1"))        # octave
    assert f("gvn:13.1") == pytest.approx(261.6256, abs=1e-3)     # c′ = C4


def test_sharpenings():
    assert cents(f("gvn:11.2") / f("gvn:11.1")) == pytest.approx(50)
    assert cents(f("gvn:11.3") / f("gvn:11.1")) == pytest.approx(100)
    # second sharp of E sounds as F; second sharp of B as c
    assert f("gvn:1.3") == pytest.approx(f("gvn:2.1"))
    assert f("gvn:5.3") == pytest.approx(f("gvn:6.1"))


def test_instrumental_same_grid():
    assert f("gin:11.1") == pytest.approx(f("gvn:11.1"))


def test_rest_has_no_pitch():
    assert f("gcn:1") is None


def test_midi_pitch():
    assert midi_pitch(440.0) == (69, 0.0)
    key, off = midi_pitch(f("gvn:11.2"))   # a quarter-tone sharp
    assert abs(off) == pytest.approx(50)


@pytest.mark.parametrize("offset, value", [
    (0, 8192), (50, 10240), (-50, 6144), (200, 16383), (-200, 0), (500, 16383),
])
def test_bend_value(offset, value):
    assert bend_value(offset) == value
