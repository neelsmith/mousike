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


# --- voices -------------------------------------------------------------------

from mousike import VOICES, Note
from mousike.audio import LYRE_RING


def _autocorr_pitch(s, rate, expect):
    w = s[int(0.05 * rate):int(0.05 * rate) + 6000]
    period = rate / expect
    lags = range(int(period * 0.9), int(period * 1.1) + 2)
    ac = {L: sum(w[i] * w[i + L] for i in range(len(w) - L))
          for L in range(lags.start - 1, lags.stop + 1)}
    L = max(lags, key=lambda L: ac[L])
    a, b, c = ac[L - 1], ac[L], ac[L + 1]
    return rate / (L + 0.5 * (a - c) / (a - 2 * b + c))


@pytest.mark.parametrize("voice, opts", [("lyre", {}), ("aulos", {"vibrato_cents": 0}),
                                         ("simple", {})])
@pytest.mark.parametrize("urn", ["gvn:8.1.3.0.0", "gvn:13.3.3.0.0", "gvn:15.1.3.0.0"])
def test_voice_pitch_is_exact(voice, opts, urn):
    t = PtolemaicTuning("tense_diatonic", "phrygian")
    f = t.frequency(Note(urn))
    s = render_samples([[urn]], t, 0.4, RATE, voice=voice, **opts)
    assert abs(1200 * math.log2(_autocorr_pitch(s, RATE, f) / f)) < 2   # cents


def test_voices_listed():
    assert VOICES == ("simple", "lyre", "aulos")


def test_unknown_voice():
    with pytest.raises(ValueError):
        render_samples([["gvn:11.1"]], NominalTuning(), voice="kithara")


def test_lyre_rings_past_the_end():
    s = render_samples([["gvn:11.1"]], NominalTuning(), 0.2, RATE, voice="lyre")
    assert len(s) == int(0.2 * RATE) + int(LYRE_RING * RATE)
    assert abs(s[-1]) < 1e-4                      # damped to silence (< -80 dB)


def test_deterministic():
    g = [["gvn:11.1"], ["gvn:12.1"]]
    for v in ("lyre", "aulos"):
        assert (render_samples(g, NominalTuning(), voice=v)
                == render_samples(g, NominalTuning(), voice=v))


def test_aulos_slurs_within_a_syllable():
    """A ~-joined note starts nearly at full level; a new syllable re-attacks."""
    t, n = NominalTuning(), int(0.3 * RATE)
    slurred = render_samples([["gvn:11.1", "gvn:12.1"]], t, voice="aulos", breath=0)
    tongued = render_samples([["gvn:11.1"], ["gvn:12.1"]], t, voice="aulos", breath=0)
    window = slice(n + 50, n + 350)               # just after the second onset
    level = lambda s: max(abs(x) for x in s[window])
    assert level(slurred) > 1.5 * level(tongued)


def test_aulos_slur_has_no_dip():
    """Within a ~ group the level stays up across the note boundary."""
    t, n = NominalTuning(), int(0.3 * RATE)
    s = render_samples([["gvn:11.1", "gvn:12.1"]], t, voice="aulos", breath=0)
    w = int(0.01 * RATE)
    rms = lambda a, b: (sum(x * x for x in s[a:b]) / (b - a)) ** 0.5
    steady = rms(n - 4 * w, n - 2 * w)
    for k in range(-2, 2):          # 10 ms windows around the boundary
        assert rms(n + k * w, n + (k + 1) * w) > 0.8 * steady


def test_wav_is_peak_normalized():
    data = wav_bytes([["gvn:11.1"]], NominalTuning(), voice="lyre", volume=0.5)
    with wave.open(io.BytesIO(data)) as w:
        frames = w.readframes(w.getnframes())
    pcm = [int.from_bytes(frames[i:i + 2], "little", signed=True)
           for i in range(0, len(frames), 2)]
    assert max(abs(x) for x in pcm) == pytest.approx(0.5 * 32767, abs=2)
