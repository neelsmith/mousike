import io
import math
import wave

import pytest

from mousike import NominalTuning, PtolemaicTuning, TuningMismatch, render_samples, wav_bytes

RATE = 22050


def test_duration_matches_lengths():
    s = render_samples([["gvn:11.1.1.0.0"], ["gvn:11.1.3.0.0"], ["gcn:1"]],
                       NominalTuning(), chronos_seconds=0.2, rate=RATE)
    assert len(s) == pytest.approx(5 * 0.2 * RATE, abs=3)


def test_rest_is_silent():
    s = render_samples([["gcn:1"]], NominalTuning(), 0.1, RATE)
    assert all(x == 0.0 for x in s)


def _pitch(samples, rate):
    # count upward zero crossings of the fundamental-dominated signal
    crossings = sum(1 for a, b in zip(samples, samples[1:]) if a < 0 <= b)
    return crossings / (len(samples) / rate)


def test_frequency():
    t = PtolemaicTuning("tense_diatonic", "phrygian")
    s = render_samples([["gvn:13.3"]], t, 1.0, RATE)     # 275 Hz
    assert _pitch(s, RATE) == pytest.approx(275, rel=0.01)


def test_wav_file():
    data = wav_bytes([["gvn:11.1"]], NominalTuning(), 0.5)
    with wave.open(io.BytesIO(data)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, RATE)
        assert w.getnframes() == int(0.5 * RATE)


def test_mismatch_propagates():
    with pytest.raises(TuningMismatch):
        wav_bytes([["gvn:13.3"]], PtolemaicTuning("tense_diatonic", "dorian"))
