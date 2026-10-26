# Using mousike

## Install

`mousike` is not yet on PyPI. Install from GitHub:

```bash
pip install git+https://github.com/neelsmith/mousike
```

or from a local clone:

```bash
git clone https://github.com/neelsmith/mousike
pip install ./mousike
```

Requires Python 3.9+. No other dependencies.

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
pip install -e ".[notebook]"
marimo edit marimo/diatonic.py     # or: marimo run marimo/diatonic.py
```

If a matching `*_text.cex` file exists, the syllables become MIDI lyrics, and the notebook shows the alignment.

The notebook plays a WAV rendering at the exact Ptolemaic frequencies, made by `wav_bytes(groups, tuning, voice=...)`. The voice can be `"lyre"` (plucked gut string), `"aulos"` (reed pipe; notes joined with `~` are slurred in one breath) or `"simple"`. The `.mid` file uses a General MIDI stand-in: harp for the lyre, oboe for the aulos. Browsers can't play MIDI directly, and in-browser MIDI players usually ignore pitch bend.

## Other functions

- `notes_to_unicode("gvn:11.1.1.0.0 gvn:12.1.1.0.0")` returns `'Ϲ Ο'`
- `note_to_unicode("gvn:11.1.1.0.0")` returns `'Ϲ'`
- `syllabify("οσον ζης φαινου")` returns `[['ο', 'σον'], ['ζης'], ['φαι', 'νου']]`
