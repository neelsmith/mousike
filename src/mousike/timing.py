"""Timings of aligned syllables and notes, and exports for players.

Times follow exactly the same schedule as ``midi.py`` and ``audio.py``: a
note lasts ``note.length`` chronoi, a chronos lasts ``chronos_seconds``,
notes follow each other without gaps, and passages follow each other in
order. Times are computed from whole numbers of chronoi, so they don't
drift.

Exports:

* ``performance`` / ``performance_json``: everything a player needs:
  passages, syllables (with start/end), and each syllable's notes with
  their URN, Unicode sign, frequency and timing.
* ``webvtt``: one WebVTT cue per syllable (for ``<track>`` elements).
* ``lrc``: enhanced LRC, one line per passage, with a timestamp before
  every syllable.
"""

import json
from dataclasses import dataclass, field
from typing import Optional

from .tuning import NominalTuning, PtolemaicTuning


@dataclass(frozen=True)
class NoteTiming:
    note: object            # Note
    start: float            # seconds
    duration: float         # seconds


@dataclass(frozen=True)
class SyllableTiming:
    ref: str                # passage reference
    index: int              # syllable number within the passage (0-based)
    text: str
    word_final: bool
    start: float
    end: float
    notes: tuple = field(default_factory=tuple)   # NoteTiming, in order

    @property
    def duration(self) -> float:
        return self.end - self.start


def syllable_timings(passages, chronos_seconds: float = 0.3) -> list:
    """Timing of every syllable (and its notes) in aligned passages.

    ``passages``: ``AlignedPassage`` objects, e.g. from ``align_editions``.
    """
    timings, chronoi = [], 0
    for passage in passages:
        for i, syl in enumerate(passage.syllables):
            start = chronoi
            notes = []
            for note in syl.note_group:
                notes.append(NoteTiming(note, round(chronoi * chronos_seconds, 6),
                                        round(note.length * chronos_seconds, 6)))
                chronoi += note.length
            timings.append(SyllableTiming(
                passage.ref, i, syl.syllable, syl.word_final,
                round(start * chronos_seconds, 6),
                round(chronoi * chronos_seconds, 6), tuple(notes)))
    return timings


def _tuning_metadata(tuning) -> dict:
    if isinstance(tuning, PtolemaicTuning):
        s = tuning.system
        return {"tuning": "ptolemaic", "tonos": s.tonos.name,
                "division": s.division.key, "hypate_meson_hz": s.hypate_meson_hz}
    if isinstance(tuning, NominalTuning):
        return {"tuning": "nominal", "reference_hz": tuning.reference_hz}
    return {"tuning": type(tuning).__name__}


def performance(passages, tuning, chronos_seconds: float = 0.3, **metadata) -> dict:
    """A JSON-ready description of a performance, for players.

    Extra keyword arguments (e.g. ``source="seikilos"``, ``voice="lyre"``,
    ``audio="seikilos.wav"``) are added to the top level.
    Raises ``TuningMismatch`` if a note doesn't fit the tuning.
    """
    timings = syllable_timings(passages, chronos_seconds)
    out = dict(metadata)
    out.update(_tuning_metadata(tuning))
    out["chronos_seconds"] = chronos_seconds
    out["duration"] = timings[-1].end if timings else 0.0
    by_ref = {}
    for t in timings:
        by_ref.setdefault(t.ref, []).append({
            "text": t.text,
            "word_final": t.word_final,
            "start": t.start,
            "end": t.end,
            "notes": [_note_dict(n, tuning) for n in t.notes],
        })
    out["passages"] = [{"ref": ref, "syllables": syls} for ref, syls in by_ref.items()]
    return out


def _note_dict(nt: NoteTiming, tuning) -> dict:
    n = nt.note
    hz = tuning.frequency(n)
    return {
        "urn": n.urn,
        "unicode": n.unicode,
        "name": n.name,
        "length": n.length,
        "arsis": n.arsis,
        "hyphen": n.hyphen,
        "hz": None if hz is None else round(hz, 4),
        "start": nt.start,
        "duration": nt.duration,
    }


def performance_json(passages, tuning, chronos_seconds: float = 0.3,
                     indent: Optional[int] = 2, **metadata) -> str:
    """``performance`` as a JSON string (UTF-8 text, Greek kept as is)."""
    return json.dumps(performance(passages, tuning, chronos_seconds, **metadata),
                      ensure_ascii=False, indent=indent)


# --- WebVTT --------------------------------------------------------------------

def _vtt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def webvtt(passages, chronos_seconds: float = 0.3) -> str:
    """WebVTT captions: one cue per syllable, identified ``<ref>.<n>``
    (1-based). Non-final syllables of a word end with a hyphen."""
    lines = ["WEBVTT", ""]
    for t in syllable_timings(passages, chronos_seconds):
        lines += [f"{t.ref}.{t.index + 1}",
                  f"{_vtt_time(t.start)} --> {_vtt_time(t.end)}",
                  t.text + ("" if t.word_final else "-"),
                  ""]
    return "\n".join(lines)


# --- LRC -----------------------------------------------------------------------

def _lrc_time(seconds: float) -> str:
    cs = round(seconds * 100)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{m:02d}:{s:02d}.{cs:02d}"


def lrc(passages, chronos_seconds: float = 0.3, title: Optional[str] = None) -> str:
    """Enhanced LRC: one line per passage, ``<mm:ss.xx>`` before each
    syllable and at the end of the line. Syllables of a word are joined;
    words are separated by spaces."""
    timings = syllable_timings(passages, chronos_seconds)
    lines = []
    if title:
        lines.append(f"[ti:{title}]")
    if timings:
        lines.append(f"[length:{_lrc_time(timings[-1].end)[:5]}]")
    by_ref = {}
    for t in timings:
        by_ref.setdefault(t.ref, []).append(t)
    for syls in by_ref.values():
        parts = [f"[{_lrc_time(syls[0].start)}]"]
        for t in syls:
            parts.append(f"<{_lrc_time(t.start)}>{t.text}" + (" " if t.word_final else ""))
        line = "".join(parts).rstrip() + f" <{_lrc_time(syls[-1].end)}>"
        lines.append(line)
    return "\n".join(lines) + "\n"
