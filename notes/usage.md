# Using mousike

## Install

```bash
pip install mousike
```

Requires Python 3.9+. No other dependencies. The package is on PyPI at https://pypi.org/project/mousike/.

For development, install from a clone in editable mode with the test extras:

```bash
git clone https://github.com/neelsmith/mousike
cd mousike
pip install -e ".[test]"
```

## Align a text with its notation

You need two parallel files, each with a header line followed by `urn|content` lines. Passages are paired by the last part of the URN (`...:1`, `...:2`, …).

**Text edition**

```
urn|text
urn:cts:mousike:epigraphic.seikilos.text:1|οσον ζης φαινου
```

**Notational edition**: one whitespace-separated group per syllable. Join notes sung on a single syllable with `~`.

```
urn|text
urn:cts:mousike:epigraphic.seikilos.notes:1|gvn:11.1.1.0.0 gvn:15.1.2.0.0 gvn:15.1.3.1.0 gvn:13.3.1.0.0~gvn:14.1.1.0.0~gvn:15.1.1.0.0 gvn:14.1.3.1.1
```

```python
from mousike import align_editions

for passage in align_editions("seikilos_text.cex", "seikilos_notation.cex"):
    print(passage)
```

```
Ϲ   Ζ    Ζ    ΚΙΖ   Ι
ο-  σον  ζης  φαι-  νου
```

Each passage holds a list of syllables. Each syllable has `syllable`, `notes` (in Unicode), `word_index` and `word_final`:

```python
for s in passage.syllables:
    print(s.syllable, s.notes)
```

To align a single passage from strings, use `align_passage(text, notes)`. If the number of syllables and note groups differ, it raises `AlignmentError`, and the message lists the syllables it found.

## Notes as objects

```python
from mousike import Note, parse_notes, parse_note_groups

n = Note("gvn:14.1.3.1.1")      # full urn:cite2:zst:... URNs also work
n.length                        # 3
n.arsis, n.hyphen               # (True, True)
n.unicode                       # 'Ι'
n.name                          # "vocal d′"
n.urn                           # 'gvn:14.1.3.1.1'
```

Tiers 3–5 can be left out. They default to length 1, no arsis and no hyphen. Notes can be compared and used in sets. An invalid URN raises `ValueError`.

Parse a line from a notation edition:

```python
parse_notes(s)          # flat list of Note objects
parse_note_groups(s)    # list of groups (one per syllable); ~-joined notes share a group
```

In an alignment, each syllable's `note_group` holds its `Note` objects.

## MIDI

You must choose a tuning. To use Ptolemy's, specify a division and a tonos:

```python
from mousike import PtolemaicTuning, NominalTuning, edition_to_midi

tuning = PtolemaicTuning("tense_diatonic", "phrygian")
edition_to_midi("seikilos.mid", "seikilos_text.cex", "seikilos_notation.cex", tuning)
```

- Divisions: `tense_diatonic`, `ditonic_diatonic`, `soft_diatonic`, `tonic_diatonic`, `even_diatonic`. Chromatic and enharmonic divisions aren't supported yet.
- Tonoi: Hypodorian, Hypophrygian, Hypolydian, Dorian, Phrygian, Lydian, Mixolydian.
- If a sign doesn't fit the chosen tonos and division, you get `TuningMismatch`. It names the note and the string it would have been played on.
- `NominalTuning()` reads the notation at face value, in equal temperament with quarter tones.
- Options: `chronos_seconds` (default 0.3), `program` (General MIDI, default 52 Choir Aahs), `velocity`.

## Notebook

`marimo/diatonic.py` has menus for the notation edition, tonos, division and voice, a tempo slider (chronoi per minute, 60–360, default 200, i.e. 0.3 s per chronos), and a **Generate MIDI** button. It plays the result and saves the `.mid` and `.wav` files to `output/`, which is ignored by git.

```bash
pip install mousike marimo
marimo edit marimo/diatonic.py     # or: marimo run marimo/diatonic.py
```

Or let marimo install the notebook's dependencies (declared at the top of the file) into an isolated environment from PyPI:

```bash
marimo edit --sandbox marimo/diatonic.py
```

If a matching `*_text.cex` file exists, the syllables become MIDI lyrics, and the notebook shows the alignment.

The notebook plays a WAV rendering at the exact Ptolemaic frequencies, made by `wav_bytes(groups, tuning, voice=...)`. The voice can be `"lyre"` (plucked gut string), `"aulos"` (reed pipe; notes joined with `~` are slurred in one breath) or `"simple"`. The `.mid` file uses a General MIDI stand-in: harp for the lyre, oboe for the aulos. Browsers can't play MIDI directly, and in-browser MIDI players usually ignore pitch bend.

### Development notebook

`marimo/diatonic-dev.py` is the same notebook, but it imports mousike from the repo's `src/` folder, even if a released mousike is installed. Use it to try unreleased changes:

```bash
marimo edit marimo/diatonic-dev.py
```

A banner shows which mousike file is in use. Results go to `output/dev/`. When the edition has a text, the notebook also saves the timing exports (`.json`, `.vtt`, `.lrc`). To pick up source edits without restarting, turn on module autoreload in marimo's settings (Runtime → On module change).

## Timings and lyric files

Syllable and note timings follow the same schedule as the MIDI and audio output. For a tempo of `chronos_seconds` per chronos:

```python
from mousike import align_editions, syllable_timings, performance_json, webvtt, lrc, PtolemaicTuning

passages = align_editions("seikilos_text.cex", "seikilos_notation.cex")

for t in syllable_timings(passages, chronos_seconds=0.3):
    print(t.ref, t.text, t.start, t.end)          # e.g. 1 φαι 1.8 2.7

tuning = PtolemaicTuning("tense_diatonic", "phrygian")
open("seikilos.json", "w").write(performance_json(passages, tuning, 0.3,
                                                  source="seikilos", voice="lyre",
                                                  audio="seikilos.wav"))
open("seikilos.vtt", "w").write(webvtt(passages, 0.3))
open("seikilos.lrc", "w").write(lrc(passages, 0.3, title="Seikilos"))
```

- `performance` / `performance_json`: the format for players. It has the passages, and each passage's syllables with `start`/`end`. Each syllable lists its notes with `urn`, `unicode`, `name`, `length`, `arsis`, `hyphen`, `hz`, `start` and `duration`. The tuning and any keyword metadata you pass go at the top level.
- `webvtt`: one cue per syllable (identified `1.4` = passage 1, syllable 4). Syllables that don't end a word get a hyphen.
- `lrc`: enhanced LRC, one line per passage, with a timestamp before each syllable.

## Other functions

- `notes_to_unicode("gvn:11.1.1.0.0 gvn:12.1.1.0.0")` returns `'Ϲ Ο'`
- `note_to_unicode("gvn:11.1.1.0.0")` returns `'Ϲ'`
- `syllabify("οσον ζης φαινου")` returns `[['ο', 'σον'], ['ζης'], ['φαι', 'νου']]`
