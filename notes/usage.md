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
n.unicode                       # 'Ι𝉂̇': sign + triseme + arsis dot
n.pitch_unicode                 # 'Ι': bare pitch sign
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

### Notation editor

`marimo/editor.py` is a scratchpad for writing notation. Type or paste text in the text area; the formatted panel beside it shows the same text with every note URN (full `urn:cite2:zst:gvn:11.1.1.0.0` or short `gvn:11.1.1.0.0`, with `~` joining notes) replaced by its Unicode sign in the bundled font. URNs that aren't in Sowerby's table are underlined in red; hover to see why.

Choose **Vocal** or **Instrumental** notation; then type in **Search** (e.g. `vocal G`, `first sharp of e''`, `gvn:11`). The **Sign** menu shows only matching signs of that notation (plus the rest sign), best match first and already selected. Note names are case-sensitive (`G` is not `g`, `e` is not `e′`), `'` or `"` stand for one or two primes, other words match the start of a description word in any case, and a word with `:` matches the start of the URN. Next to it, pick a **Length** (1-5, default 1) and tick **Arsis** if needed (default off). The panel below previews the note with its marks, its URN with all five tiers (hyphen always 0) and its code points. **OK: copy URN** puts that URN (e.g. `gvn:11.1.3.1.0`) on the clipboard; **Copy sign** copies the Unicode sign with its marks. The rest (`gcn:1`) takes no length or arsis.

```bash
marimo edit marimo/editor.py
```

Under **Listen**, choose a tonos, a diatonic division, a voice and a tempo (the same controls as `diatonic.py`) and press **Play** to hear every note URN in the text, in order; `~`-joined notes form one group. URNs not in the table are skipped with a warning, and a note that doesn't fit the tonos and division stops playback with an explanation. The WAV and MIDI can be downloaded; nothing is written to `output/`.

The notebook uses `note_urn_spans`, which is not yet in a PyPI release, so it imports mousike from the repo's `src/`. Its script header asks only for `mousike>=0.2.0` so that `marimo edit --sandbox` can resolve it.

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

## Unicode rendering of length and arsis

`Note.unicode` adds combining marks after the pitch sign:

| Tier | Value | Mark |
|---|---|---|
| length | 2 (diseme) | U+0305 COMBINING OVERLINE |
| length | 3 (triseme) | U+1D242 COMBINING GREEK MUSICAL TRISEME |
| length | 4 (tetraseme) | U+1D243 COMBINING GREEK MUSICAL TETRASEME |
| length | 5 (pentaseme) | U+1D244 COMBINING GREEK MUSICAL PENTASEME |
| arsis | 1 | U+0307 COMBINING DOT ABOVE |

The length mark comes first and the dot second, so the dot stacks above the length mark. For signs written with a prime (e.g. `Ο′`), the marks go on the letter, before the prime. The hyphen tier isn't rendered. `Note.pitch_unicode` gives the bare sign. In JSON exports, each note has both `unicode` and `pitch_unicode`.

**Fonts:** to display these strings, a single font needs Greek letters, the Greek Musical Notation block and U+0305/U+0307, because browsers pick one font for a letter together with its marks. mousike bundles such a font, **Mousike Notation**:

```python
from mousike import font_css, font_path, alignment_html

font_path("woff2")      # for web pages
font_path("ttf")        # install it on your computer to see notation in any app
font_css()              # @font-face (font embedded) + a .mousike-notation class
alignment_html(passages)  # notes-over-syllables display using the font
```

Use the font only for notation. It has the capital Greek letters the signs use, but no lower-case Greek or Latin text. It's under the SIL Open Font License (`src/mousike/data/fonts/OFL.txt`), and it's merged from Noto Serif and Noto Music by `fonts/build.py`. To rebuild it, run `pip install "fonttools[woff]"` and then `python fonts/build.py`. The sources are pinned and checked, and the output is byte-identical on rebuild.

**Downloading the font without Python:** every GitHub release has `MousikeNotation.zip` attached. It contains the TTF, the WOFF2, the licence, the specimen PDF and a README with install instructions. The latest version is always at https://github.com/neelsmith/mousike/releases/latest/download/MousikeNotation.zip. To make the zip yourself, run `python fonts/package.py`, which writes `fonts/dist/MousikeNotation.zip`.

A printable specimen of the font (every sign in four forms, with its URN and name, and a key to the marks) is in `fonts/MousikeNotation-specimen.pdf`, with an HTML version alongside. To regenerate them, run `python fonts/specimen.py`. Making the PDF needs Playwright (`pip install playwright && playwright install chromium`); without it, the script writes only the HTML, which you can print to PDF from a browser.

## Other functions

- `notes_to_unicode("gvn:11.1.1.0.0 gvn:12.1.1.0.0")` returns `'Ϲ Ο'`
- `note_to_unicode("gvn:11.1.1.0.0")` returns `'Ϲ'`
- `find_signs("vocal G")` returns `['gvn:3.1', 'gvn:3.2', 'gvn:3.3']`: signs found by description, best first; `collections=("gin",)` limits the search
- `urns_to_unicode("Notes: gvn:11.1 gvn:13.3~gvn:14.1.")` returns `'Notes: Ϲ ΚΙ.'`: note URNs in running text become signs, other text is unchanged. `note_urn_spans(text)` gives the same as `(source, unicode, error)` triples, with an error message for URNs not in the table.
- `syllabify("οσον ζης φαινου")` returns `[['ο', 'σον'], ['ζης'], ['φαι', 'νου']]`
