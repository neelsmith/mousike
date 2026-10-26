"""Render notes directly to audio (WAV), at the exact frequencies of a tuning.

MIDI players approximate microtones with pitch bend, and browser MIDI players
often ignore bend entirely. This renders the same notes, with the same timing
as ``midi.py``, in pure Python, so what you hear is exactly the tuning.

Voices:

* ``"simple"``: a soft wavetable tone.
* ``"lyre"``: a plucked gut string (Karplus-Strong), with a fractional-delay
  allpass so the pitch is exact, a plectrum-bright attack, and strings that
  ring briefly into the next note.
* ``"aulos"``: a buzzy double-reed pipe: odd-heavy harmonic spectrum, breath
  noise, gentle delayed vibrato. Notes joined with ``~`` (one syllable) are
  played in one breath with a quick glide between them; each new syllable
  is tongued.

Output is deterministic (noise uses a fixed seed).
"""

import io
import math
import random
import wave
from array import array

from .note import Note

VOICES = ("simple", "lyre", "aulos")
_TABLE_SIZE = 4096


def _wavetable(harmonics):
    table = [sum(a * math.sin(2 * math.pi * (h + 1) * i / _TABLE_SIZE)
                 for h, a in enumerate(harmonics))
             for i in range(_TABLE_SIZE)]
    peak = max(abs(x) for x in table)
    return [x / peak for x in table]


_SIMPLE_TABLE = _wavetable((1.0, 0.5, 0.3, 0.15, 0.08))
# Reed-like: strong odd harmonics, weaker even ones, rolling off slowly
_AULOS_TABLE = _wavetable(tuple((1.0 if h % 2 else 0.45) / h ** 0.8
                                for h in range(1, 15)))


def _schedule(groups, tuning, chronos_seconds, rate):
    """Runs of consecutive sounding notes within each ``~`` group, as
    (start_sample, [(length_samples, freq), ...]), plus the total length.
    A rest ends a run."""
    runs, pos = [], 0
    for group in groups:
        current = None
        for note in group:
            note = Note(note) if isinstance(note, str) else note
            n = int(note.length * chronos_seconds * rate)
            freq = tuning.frequency(note)
            if freq is None:
                current = None
            elif current is None:
                current = (pos, [(n, freq)])
                runs.append(current)
            else:
                current[1].append((n, freq))
            pos += n
    return runs, pos


# --- simple ------------------------------------------------------------------

def _simple(freq, n, rate, attack=0.02, release=0.08, **_):
    a, r = max(1, int(attack * rate)), max(1, int(release * rate))
    step = freq * _TABLE_SIZE / rate
    phase, out = 0.0, [0.0] * n
    for i in range(n):
        out[i] = _SIMPLE_TABLE[int(phase) % _TABLE_SIZE] * min(1.0, i / a, (n - i) / r)
        phase += step
    return out


# --- lyre: Karplus-Strong with exact tuning ------------------------------------

LYRE_RING = 0.35   # seconds a string keeps sounding after the next note starts


def _lyre(freq, n, rate, rng, brightness=0.7, decay=0.996, **_):
    period = rate / freq
    # Loop delay = N (delay line) + 0.5 (averaging filter) + d (allpass)
    N = int(period - 0.5 - 0.1)
    d = period - 0.5 - N                     # in [0.1, 1.1)
    c = (1 - d) / (1 + d)                    # first-order allpass coefficient
    # Plectrum excitation: noise, smoothed a little (less = brighter)
    buf, prev = [], 0.0
    for _ in range(N):
        x = rng.uniform(-1, 1)
        prev = brightness * x + (1 - brightness) * prev
        buf.append(prev)
    mean = sum(buf) / N
    buf = [x - mean for x in buf]

    total = n + int(LYRE_RING * rate)
    out = [0.0] * total
    idx, last, ap_x, ap_y = 0, 0.0, 0.0, 0.0
    damp_start, damp_len = n, int(LYRE_RING * rate)
    for i in range(total):
        y = buf[idx]
        # averaging (lowpass) + loss, then fractional-delay allpass
        avg = decay * 0.5 * (y + last)
        last = y
        ap = c * avg + ap_x - c * ap_y
        ap_x, ap_y = avg, ap
        buf[idx] = ap
        idx = (idx + 1) % N
        env = 1.0 if i < damp_start else 1.0 - (i - damp_start) / damp_len
        out[i] = y * env
    return out


# --- aulos ---------------------------------------------------------------------

def _aulos(notes, rate, rng, vibrato_cents=6.0, breath=0.04, glide=0.015, **_):
    """One breath over a run of slurred notes [(length, freq), ...]: tongued
    attack at the start, a quick pitch glide between notes, release at the end."""
    total = sum(n for n, _ in notes)
    a, r = max(1, int(0.045 * rate)), max(1, int(0.04 * rate))
    vib_delay, vib_rate = int(0.25 * rate), 5.2
    g = 1 - math.exp(-1 / max(1.0, glide * rate))     # one-pole glide coefficient
    targets = [f for n, f in notes for _ in range(n)]
    freq, phase, noise_lp = targets[0], 0.0, 0.0
    out = [0.0] * total
    for i in range(total):
        freq += g * (targets[i] - freq)
        env = min(1.0, i / a, (total - i) / r)
        depth = vibrato_cents * min(1.0, max(0.0, (i - vib_delay) / rate / 0.3))
        cents = depth * math.sin(2 * math.pi * vib_rate * i / rate)
        phase += freq * _TABLE_SIZE / rate * 2 ** (cents / 1200)
        noise_lp = 0.85 * noise_lp + 0.15 * rng.uniform(-1, 1)
        # breath is strongest at the onset ("chiff"), then settles
        b = breath * (1.0 + 3.0 * max(0.0, 1 - i / (0.06 * rate)))
        out[i] = env * (_AULOS_TABLE[int(phase) % _TABLE_SIZE] + b * noise_lp)
    return out


_RENDERERS = {"simple": _simple, "lyre": _lyre, "aulos": _aulos}


def render_samples(groups, tuning, chronos_seconds=0.3, rate=22050,
                   voice="simple", seed=0, **voice_options):
    """Mono samples for note groups (lists of ``Note``), not normalized.

    ``voice``: one of ``VOICES``. Extra keyword arguments go to the voice
    (e.g. ``vibrato_cents=0`` for the aulos, ``brightness`` or ``decay``
    for the lyre).
    """
    if voice not in _RENDERERS:
        raise ValueError(f"Unknown voice {voice!r}; choose from {', '.join(VOICES)}")
    render = _RENDERERS[voice]
    rng = random.Random(seed)
    runs, total = _schedule(groups, tuning, chronos_seconds, rate)
    tail = int(LYRE_RING * rate) if voice == "lyre" else 0
    out = [0.0] * (total + tail)

    def mix(start, samples):
        for i, x in enumerate(samples):
            out[start + i] += x

    for start, notes in runs:
        if voice == "aulos":              # a slurred run is one breath
            mix(start, render(notes, rate, rng=rng, **voice_options))
        else:                             # every note plucked / struck anew
            for n, freq in notes:
                mix(start, render(freq, n, rate, rng=rng, **voice_options))
                start += n
    return out


def wav_bytes(groups, tuning, chronos_seconds=0.3, rate=22050, volume=0.8,
              voice="simple", **voice_options) -> bytes:
    """A 16-bit mono WAV file of the note groups, as bytes (peak-normalized
    to ``volume``)."""
    samples = render_samples(groups, tuning, chronos_seconds, rate, voice,
                             **voice_options)
    peak = max((abs(s) for s in samples), default=0.0) or 1.0
    scale = volume * 32767 / peak
    pcm = array("h", (int(s * scale) for s in samples))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()
