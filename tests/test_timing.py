import json
import pathlib
import re

import pytest

from mousike import (NominalTuning, PtolemaicTuning, TuningMismatch, align_editions,
                     align_passage, lrc, midi_bytes, performance, performance_json,
                     syllable_timings, webvtt)
from mousike.audio import _schedule

DATA = pathlib.Path(__file__).parents[1] / "data"
TEXT, NOTES = DATA / "seikilos_text.cex", DATA / "seikilos_notation.cex"
PHRYGIAN = PtolemaicTuning("tense_diatonic", "phrygian")


@pytest.fixture
def seikilos():
    if not (TEXT.exists() and NOTES.exists()):
        pytest.skip("Seikilos data not present")
    return align_editions(TEXT, NOTES)


@pytest.fixture
def small():
    # two syllables: one note of length 1, then a 3-note group with lengths 2,1,1
    return [align_passage("οσον", "gvn:11.1.1.0.0 gvn:12.1.2.0.0~gvn:13.1.1.0.0~gvn:14.1.1.0.0", "1")]


def test_syllable_timings(small):
    t = syllable_timings(small, chronos_seconds=0.5)
    assert [(s.text, s.start, s.end) for s in t] == [("ο", 0.0, 0.5), ("σον", 0.5, 2.5)]
    assert [(n.start, n.duration) for n in t[1].notes] == [(0.5, 1.0), (1.5, 0.5), (2.0, 0.5)]
    assert t[0].word_final is False and t[1].word_final is True
    assert t[1].duration == 2.0


def test_seikilos_timings(seikilos):
    t = syllable_timings(seikilos)
    assert len(t) == 29
    assert [s.start for s in t[:5]] == [0.0, 0.3, 0.9, 1.8, 2.7]
    assert t[-1].end == pytest.approx(17.4)
    # contiguous: each syllable starts where the previous one ends
    assert all(a.end == pytest.approx(b.start) for a, b in zip(t, t[1:]))
    assert [s.ref for s in t].count("4") == 9


def test_tempo_scales(seikilos):
    a = syllable_timings(seikilos, 0.3)
    b = syllable_timings(seikilos, 0.6)
    assert all(y.start == pytest.approx(2 * x.start) for x, y in zip(a, b))


def test_matches_midi_lyrics(seikilos):
    """Syllable starts equal the times of the MIDI lyric events."""
    mido = pytest.importorskip("mido")
    import io
    groups = [s.note_group for p in seikilos for s in p.syllables]
    lyrics = [s.syllable for p in seikilos for s in p.syllables]
    data = midi_bytes(groups, PHRYGIAN, lyrics=lyrics, chronos_seconds=0.3)
    mid = mido.MidiFile(file=io.BytesIO(data), charset="utf-8")
    now, times = 0.0, []
    for msg in mid:                       # iterating a MidiFile gives seconds
        now += msg.time
        if msg.type == "lyrics":
            times.append(now)
    starts = [s.start for s in syllable_timings(seikilos, 0.3)]
    assert times == pytest.approx(starts, abs=1e-6)


def test_matches_audio_schedule(seikilos):
    """Audio note onsets are within a millisecond of the note timings."""
    groups = [s.note_group for p in seikilos for s in p.syllables]
    rate = 22050
    runs, _ = _schedule(groups, PHRYGIAN, 0.3, rate)
    onsets = []
    for start, notes in runs:
        for n, _ in notes:
            onsets.append(start / rate)
            start += n
    note_starts = [n.start for s in syllable_timings(seikilos, 0.3) for n in s.notes]
    assert onsets == pytest.approx(note_starts, abs=0.001)


def test_performance(seikilos):
    d = performance(seikilos, PHRYGIAN, source="seikilos", voice="lyre", audio="x.wav")
    assert (d["source"], d["voice"], d["audio"]) == ("seikilos", "lyre", "x.wav")
    assert (d["tuning"], d["tonos"], d["division"]) == ("ptolemaic", "Phrygian", "tense_diatonic")
    assert d["duration"] == pytest.approx(17.4)
    assert [p["ref"] for p in d["passages"]] == ["1", "2", "3", "4"]
    phai = d["passages"][0]["syllables"][3]
    assert phai["text"] == "φαι"
    assert [n["unicode"] for n in phai["notes"]] == ["Κ", "Ι", "Ζ"]
    assert phai["notes"][0]["hz"] == pytest.approx(275.0)
    nou = d["passages"][0]["syllables"][4]["notes"][0]          # gvn:14.1.3.1.1
    assert (nou["unicode"], nou["pitch_unicode"]) == ("Ι\U0001D242\u0307", "Ι")
    assert sum(len(s["notes"]) for p in d["passages"] for s in p["syllables"]) == 37


def test_performance_nominal(small):
    d = performance(small, NominalTuning())
    assert d["tuning"] == "nominal" and d["reference_hz"] == 220.0
    assert d["passages"][0]["syllables"][0]["notes"][0]["hz"] == pytest.approx(220.0)


def test_performance_mismatch(seikilos):
    with pytest.raises(TuningMismatch):
        performance(seikilos, PtolemaicTuning("tense_diatonic", "dorian"))


def test_performance_json_roundtrip(seikilos):
    s = performance_json(seikilos, PHRYGIAN)
    assert "φαι" in s                    # Greek not escaped
    assert json.loads(s) == performance(seikilos, PHRYGIAN)


VTT_TIME = r"\d\d:\d\d:\d\d\.\d{3}"


def test_webvtt(seikilos):
    v = webvtt(seikilos)
    assert v.startswith("WEBVTT\n\n")
    cues = v.strip().split("\n\n")[1:]
    assert len(cues) == 29
    ident, timing, text = cues[3].split("\n")
    assert (ident, timing, text) == ("1.4", "00:00:01.800 --> 00:00:02.700", "φαι-")
    assert all(re.fullmatch(f"{VTT_TIME} --> {VTT_TIME}", c.split("\n")[1]) for c in cues)
    assert cues[-1].split("\n")[1].endswith("00:00:17.400")


def test_webvtt_long_times(small):
    v = webvtt(small, chronos_seconds=3700)       # over an hour
    assert "01:01:40.000 --> 05:08:20.000" in v


def test_lrc(seikilos):
    text = lrc(seikilos, title="Seikilos")
    lines = text.splitlines()
    assert lines[0] == "[ti:Seikilos]"
    assert lines[1] == "[length:00:17]"
    assert len(lines) == 6
    assert lines[2] == ("[00:00.00]<00:00.00>ο<00:00.30>σον <00:00.90>ζης "
                        "<00:01.80>φαι<00:02.70>νου <00:03.60>")
    assert lines[-1].endswith("<00:15.90>τει <00:17.40>")
