# Release notes

`mousike` python package, current version: **0.2.0**


**0.2.0**, *Oct. 28, 2026*: 

- adds time stamps with lyrics to MIDI output
- adds combining Unicode code points to represent note length and *arsis* in string representation of notes
- adds openly-licensed custom font with all Unicode code points needed to represent Greek musical notation
- defines mechanism for independently versioned releases of code and data sets
- adds utilities for organizing data in published data releases for use by other programs


**0.1.4**, *Oct. 26, 2026*: fix typo.


**0.1.3**, *Oct. 26, 2026*: sync pypi publication with gh releases.


**0.1.1**, *Oct. 26, 2026*: adds gh action to publish on release.

**0.1.0**, *Oct. 26, 2026*: initial release.

- read ancient Greek musical notation from CEX source, and parse into `Note` objects
- align text syllables and musical notation in parallel editions
- generate MIDI files from Greek musical notation
- includes interactive marimo notebook