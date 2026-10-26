"""Write notes as a Standard MIDI File, with microtonal pitch bend.

Each note is played on the nearest MIDI key, with a pitch bend for the
difference in cents (so the output is monophonic, on one channel).
The bend range is set explicitly with RPN 0.

* duration: ``note.length`` chronoi; one chronos lasts ``chronos_seconds``
* the rest ``gcn:1`` is silent for its length (1 chronos)
* syllables, if given, become lyric meta events at their first note
* a tuning must be given (see ``tuning.py``)

The file is written directly (format 0, one track); no MIDI library needed.
"""

import struct

from .align import align_editions
from .note import Note, parse_note_groups
from .tuning import bend_value, midi_pitch

TICKS_PER_CHRONOS = 480
CHANNEL = 0


def _varlen(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def _meta(kind: int, data: bytes) -> bytes:
    return bytes([0xFF, kind]) + _varlen(len(data)) + data


def _cc(control: int, value: int) -> bytes:
    return bytes([0xB0 | CHANNEL, control, value])


def _events(groups, tuning, lyrics, chronos_seconds, program, velocity,
            bend_range):
    """Yield (delta_ticks, event_bytes)."""
    tempo = round(chronos_seconds * 1_000_000)  # microseconds per "beat"
    yield 0, _meta(0x51, tempo.to_bytes(3, "big"))
    if program is not None:
        yield 0, bytes([0xC0 | CHANNEL, program])
    # RPN 0 (pitch-bend sensitivity) = bend_range semitones, then RPN null
    for control, value in ((101, 0), (100, 0), (6, bend_range), (38, 0),
                           (101, 127), (100, 127)):
        yield 0, _cc(control, value)

    wait = 0
    for i, group in enumerate(groups):
        if lyrics is not None:
            yield wait, _meta(0x05, lyrics[i].encode("utf-8"))
            wait = 0
        for note in group:
            ticks = note.length * TICKS_PER_CHRONOS
            freq = tuning.frequency(note)
            if freq is None:  # rest or other unpitched sign
                wait += ticks
                continue
            key, offset = midi_pitch(freq)
            bend = bend_value(offset, bend_range)
            yield wait, bytes([0xE0 | CHANNEL, bend & 0x7F, bend >> 7])
            yield 0, bytes([0x90 | CHANNEL, key, velocity])
            yield ticks, bytes([0x80 | CHANNEL, key, 0])
            wait = 0
    yield wait, _meta(0x2F, b"")


def midi_bytes(groups, tuning, lyrics=None, chronos_seconds=0.3,
               program=52, velocity=80, bend_range=2) -> bytes:
    """Build a MIDI file from note groups (lists of ``Note``).

    ``tuning``: e.g. ``PtolemaicTuning("tense_diatonic", "phrygian")``,
    or ``NominalTuning()`` for the notation at face value.

    ``lyrics``: optional list of strings, one per group.
    ``program``: General MIDI program number, 0-based (52 = Choir Aahs);
    ``None`` to send no program change.
    """
    groups = [[Note(n) if isinstance(n, str) else n for n in g] for g in groups]
    if lyrics is not None and len(lyrics) != len(groups):
        raise ValueError(f"{len(lyrics)} lyrics for {len(groups)} note groups")
    track = b"".join(
        _varlen(delta) + data
        for delta, data in _events(groups, tuning, lyrics, chronos_seconds,
                                   program, velocity, bend_range)
    )
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TICKS_PER_CHRONOS)
    return header + b"MTrk" + struct.pack(">I", len(track)) + track


def write_midi(path, groups, tuning, **kwargs):
    """Write note groups to ``path``. Keyword arguments as for ``midi_bytes``."""
    data = midi_bytes(groups, tuning, **kwargs)   # build first: errors leave no file
    with open(path, "wb") as f:
        f.write(data)


def notes_to_midi(path, notes: str, tuning, **kwargs):
    """Write a notation-edition string (e.g. one passage) to ``path``."""
    write_midi(path, parse_note_groups(notes), tuning, **kwargs)


def edition_to_midi(path, text_path, notes_path, tuning, **kwargs):
    """Align a text and notation edition and write all passages, in order,
    to one MIDI file with the syllables as lyrics."""
    groups, lyrics = [], []
    for passage in align_editions(text_path, notes_path):
        for s in passage.syllables:
            groups.append(s.note_group)
            lyrics.append(s.syllable)
    write_midi(path, groups, tuning, lyrics=lyrics, **kwargs)
