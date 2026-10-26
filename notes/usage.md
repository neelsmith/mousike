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

## Other functions

- `notes_to_unicode("gvn:11.1.1.0.0 gvn:12.1.1.0.0")` returns `'Ϲ Ο'`
- `note_to_unicode("gvn:11.1.1.0.0")` returns `'Ϲ'`
- `syllabify("οσον ζης φαινου")` returns `[['ο', 'σον'], ['ζης'], ['φαι', 'νου']]`
