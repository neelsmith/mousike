"""Render notes directly to audio (WAV), at the exact frequencies of a tuning.

MIDI players approximate microtones with pitch bend, and browser MIDI players
often ignore bend entirely. This renders the same notes, with the same timing
as ``midi.py``, using a small wavetable synthesizer in pure Python, so what
you hear is exactly the tuning.
"""

import io
import math
import wave
from array import array

from .note import Note

_TABLE_SIZE = 4096
# Relative strengths of the first few harmonics: a soft, reed-like tone
_HARMONICS = (1.0, 0.5, 0.3, 0.15, 0.08)


def _wavetable():
    table = [sum(a * math.sin(2 * math.pi * (h + 1) * i / _TABLE_SIZE)
                 for h, a in enumerate(_HARMONICS))
             for i in range(_TABLE_SIZE)]
    peak = max(abs(x) for x in table)
    return [x / peak for x in table]


_TABLE = _wavetable()


def _tone(freq, seconds, rate, attack=0.02, release=0.08):
    n = int(seconds * rate)
    a, r = max(1, int(attack * rate)), max(1, int(release * rate))
    step = freq * _TABLE_SIZE / rate
    phase = 0.0
    out = [0.0] * n
    for i in range(n):
        env = min(1.0, i / a, (n - i) / r)
        out[i] = _TABLE[int(phase) % _TABLE_SIZE] * env
        phase += step
    return out


def render_samples(groups, tuning, chronos_seconds=0.3, rate=22050):
    """Mono samples in [-1, 1] for note groups (lists of ``Note``)."""
    samples = []
    for group in groups:
        for note in group:
            note = Note(note) if isinstance(note, str) else note
            seconds = note.length * chronos_seconds
            freq = tuning.frequency(note)
            if freq is None:
                samples.extend([0.0] * int(seconds * rate))
            else:
                samples.extend(_tone(freq, seconds, rate))
    return samples


def wav_bytes(groups, tuning, chronos_seconds=0.3, rate=22050, volume=0.6) -> bytes:
    """A 16-bit mono WAV file of the note groups, as bytes."""
    pcm = array("h", (int(s * volume * 32767)
                      for s in render_samples(groups, tuning, chronos_seconds, rate)))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()
