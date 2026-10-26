# Plan: MIDI generation

Pipeline: notation edition -> `Note` objects -> tuning (`frequency(note)`) -> MIDI file.

## Review of `scratch/midi-generation.md`

- Tetrachord ratios for Ptolemy's eight divisions are correct (low to high).
- **Greater Perfect System table is wrong from hypate meson up.** Measured from
  proslambanomenos: hypate hypaton 9:8, hypate meson 3:2, mese 2:1,
  paramese 9:4. Hypate hypaton is not a "disjunction step".
- 28:27 = 62.96 cents, not 62.57. Compute cents from `Fraction`s, don't store them.
- Says "seven" divisions, lists eight.
- Synemmenon tetrachord missing.
- Pitch-bend method is fine for monophony. Set the bend range explicitly
  (RPN 0), clamp to 16383, and use one channel per overlapping voice.

## Key design point

A "tuning system" = **tonos** (which sign is which scale degree) + **division**
(Ptolemy's genus/shade) + **reference pitch**. The scratch notes cover only the
last two. The tonos mapping needs a data table (tonos, sign) -> degree,
from an authoritative source.

## Steps

1. [done] Nominal baseline tuning: notation read at face value
   (natural / +quarter tone / +semitone), vocal a = 220 Hz.
2. [done] `midi.py`: hand-written Standard MIDI File writer (no dependency).
   Pitch bend per note, length tier -> duration, `gcn:1` -> rest,
   aligned syllables -> lyric meta events.
3. [done] `ptolemy.py`: 8 divisions as `Fraction`s (validated = 4:3); Perfect
   System + synemmenon; Ptolemy's 7 tonoi (`data/ptolemy_tonoi.cex`) as octave
   species of a fixed thetic central octave; `PtolemaicSystem(division, tonos,
   hypate_meson_hz=165)` with thetic/dynamic ratios and frequencies.
4. [done, diatonic only] `PtolemaicTuning(division, tonos)` (both required): base
   letter -> thetic string (e = hypate meson, a = mese); tonos/division tune it;
   sharpening only checked (`TuningMismatch` if > 60 cents from face value).
   MIDI functions now require a tuning argument.
   Next: chromatic/enharmonic (sharpening k -> string k-1 above? verify).
   Full solution needs Alypian tables (notated key + genus -> sign).
   Note: Seikilos is notated in a key Ptolemy lacks (Iastian, per Pöhlmann &
   West - verify); its octave species is Phrygian.
5. Optional Scala `.scl` export.

## Open decisions (Neel)

1. Authoritative source for tonos tables (Alypius, West, Sowerby?).
2. Tonos/genus specified by user vs inferred from signs used (start: specified).
3. Default tempo of the chronos; should arsis affect velocity; does hyphen
   mean legato?
4. Default reference pitch for vocal a (currently 220 Hz).
5. Use `mido` at runtime? (Currently only a test dependency.)
