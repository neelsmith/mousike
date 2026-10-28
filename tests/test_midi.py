import pathlib

import pytest

from mousike import NominalTuning, Note, edition_to_midi, midi_bytes, midi_pitch
from mousike.midi import TICKS_PER_CHRONOS

mido = pytest.importorskip("mido")
DATA = pathlib.Path(__file__).parents[1] / "editions"
NOMINAL = NominalTuning()


def read(path):
    return mido.MidiFile(path, charset="utf-8")


def played(mid):
    """List of (key, bend, start_tick, duration_ticks) from a MIDI file."""
    out, now, bend, starts = [], 0, 0, {}
    for msg in mid.tracks[0]:
        now += msg.time
        if msg.type == "pitchwheel":
            bend = msg.pitch          # mido: -8192..8191
        elif msg.type == "note_on" and msg.velocity > 0:
            starts[msg.note] = (now, bend)
        elif msg.type in ("note_off", "note_on"):
            start, b = starts.pop(msg.note)
            out.append((msg.note, b, start, now - start))
    return out


def test_pitches_and_durations(tmp_path):
    p = tmp_path / "x.mid"
    p.write_bytes(midi_bytes([["gvn:11.1.1.0.0"], ["gvn:15.1.2.0.0"],
                              ["gvn:11.2.3.0.0"]], NOMINAL))
    notes = played(read(p))
    assert [(k, b) for k, b, _, _ in notes][:2] == [(57, 0), (64, 0)]   # A3, E4
    key, bend, _, dur = notes[2]
    expected_key, _ = midi_pitch(NominalTuning().frequency(Note("gvn:11.2")))
    assert key == expected_key and abs(bend) == 2048     # ±50 cents
    assert [d for *_, d in notes] == [TICKS_PER_CHRONOS * n for n in (1, 2, 3)]


def test_rest_is_silent(tmp_path):
    p = tmp_path / "r.mid"
    p.write_bytes(midi_bytes([["gvn:11.1"], ["gcn:1"], ["gvn:11.1"]], NOMINAL))
    notes = played(read(p))
    assert len(notes) == 2
    assert notes[1][2] == 2 * TICKS_PER_CHRONOS          # starts after the rest


def test_setup_messages(tmp_path):
    p = tmp_path / "s.mid"
    p.write_bytes(midi_bytes([["gvn:11.1"]], NOMINAL, chronos_seconds=0.5, program=73))
    msgs = list(read(p).tracks[0])
    assert any(m.type == "set_tempo" and m.tempo == 500_000 for m in msgs)
    assert any(m.type == "program_change" and m.program == 73 for m in msgs)
    ccs = [(m.control, m.value) for m in msgs if m.type == "control_change"]
    assert ccs[:4] == [(101, 0), (100, 0), (6, 2), (38, 0)]


def test_lyrics_count_must_match():
    with pytest.raises(ValueError):
        midi_bytes([["gvn:11.1"]], NOMINAL, lyrics=["α", "β"])


def test_seikilos(tmp_path):
    text, notes = DATA / "seikilos_text.cex", DATA / "seikilos_notation.cex"
    if not (text.exists() and notes.exists()):
        pytest.skip("Seikilos data not present")
    p = tmp_path / "seikilos.mid"
    edition_to_midi(p, text, notes, NOMINAL)
    mid = read(p)
    lyrics = [m.text for m in mid.tracks[0] if m.type == "lyrics"]
    assert lyrics[:5] == ["ο", "σον", "ζης", "φαι", "νου"]
    assert len(lyrics) == 5 + 7 + 8 + 9
    keys = [k for k, *_ in played(mid)]
    # Standard transcription opens a e′ e′ c♯′ d′ e′ d′ ...
    assert keys[:7] == [57, 64, 64, 61, 62, 64, 62]
