# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "marimo",
#     "mousike>=0.1.4",
# ]
# ///
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import marimo as mo

    ROOT = mo.notebook_dir().parent   # repo root: editions in data/, results in output/

    from mousike import (DIVISIONS, PtolemaicTuning, TuningMismatch,
                         align_editions, load_tonoi, midi_bytes,
                         parse_note_groups, wav_bytes)
    from mousike.align import read_cex

    return (
        DIVISIONS,
        Path,
        PtolemaicTuning,
        ROOT,
        TuningMismatch,
        align_editions,
        load_tonoi,
        midi_bytes,
        mo,
        parse_note_groups,
        read_cex,
        wav_bytes,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Greek notation to MIDI: Ptolemy's diatonic tunings

    Choose a notation edition, one of Ptolemy's seven tonoi, one of his
    diatonic divisions of the tetrachord and a voice, set the tempo of the
    chronos (the base time unit), then press **Generate MIDI**.
    Each note is played on the string named by its letter; the tonos and
    division decide how that string is tuned. If a sign doesn't fit the
    tonos and division you chose, you'll see which note and why.

    Playback is rendered directly at the exact frequencies of the tuning.
    The saved MIDI file uses a General MIDI stand-in (harp for lyre, oboe
    for aulos) with pitch bend for the microtones.
    """)
    return


@app.cell(hide_code=True)
def _(DIVISIONS, ROOT, load_tonoi, mo):
    _editions = {p.name: p for p in sorted((ROOT / "data").glob("*_notation.cex"))}
    document = mo.ui.dropdown(
        options=_editions,
        value="seikilos_notation.cex" if "seikilos_notation.cex" in _editions else None,
        label="Notation edition",
    )
    tonos = mo.ui.dropdown(
        options=[t.name for t in sorted(load_tonoi().values(), key=lambda t: t.order)],
        label="Tonos",
    )
    division = mo.ui.dropdown(
        options={d.name: d.key for d in DIVISIONS.values() if d.genus == "diatonic"},
        label="Division",
    )
    voice = mo.ui.dropdown(
        options={"Lyre": "lyre", "Aulos": "aulos", "Simple tone": "simple"},
        value="Lyre",
        label="Voice",
    )
    tempo = mo.ui.slider(
        start=60, stop=360, step=10, value=200, show_value=True,
        label="Tempo (chronoi per minute)",
    )
    generate = mo.ui.run_button(label="Generate MIDI", kind="success")
    mo.vstack([document, mo.hstack([tonos, division, voice], justify="start"),
               tempo, generate])
    return division, document, generate, tempo, tonos, voice


@app.cell(hide_code=True)
def _(
    Path,
    PtolemaicTuning,
    ROOT,
    TuningMismatch,
    align_editions,
    division,
    document,
    generate,
    midi_bytes,
    mo,
    parse_note_groups,
    read_cex,
    tempo,
    tonos,
    voice,
    wav_bytes,
):
    mo.stop(
        document.value is None or tonos.value is None or division.value is None,
        mo.md("*Select a notation edition, a tonos and a division.*"),
    )
    mo.stop(not generate.value, mo.md("*Press **Generate MIDI** to build and play.*"))

    _notes_path = Path(document.value)
    _text_path = _notes_path.with_name(_notes_path.name.replace("_notation", "_text"))

    # Note groups (one per syllable), with lyrics when a text edition exists
    if _text_path.exists():
        _passages = align_editions(_text_path, _notes_path)
        _groups = [s.note_group for p in _passages for s in p.syllables]
        _lyrics = [s.syllable for p in _passages for s in p.syllables]
        _display = "\n\n".join(f"{p.ref}\n{p}" for p in _passages)
    else:
        _groups = [g for n in read_cex(_notes_path).values()
                   for g in parse_note_groups(n)]
        _lyrics, _display = None, ""

    # General MIDI stand-ins for the MIDI file (0-based program numbers)
    _program = {"lyre": 46, "aulos": 68, "simple": 52}[voice.value]  # harp, oboe, choir

    _chronos = 60 / tempo.value     # seconds per chronos (base time unit)

    _tuning = PtolemaicTuning(division.value, tonos.value)
    try:
        _midi = midi_bytes(_groups, _tuning, lyrics=_lyrics, program=_program,
                           chronos_seconds=_chronos)
        _wav = wav_bytes(_groups, _tuning, voice=voice.value, chronos_seconds=_chronos)
    except TuningMismatch as _err:
        mo.stop(True, mo.callout(mo.md(f"**Doesn't fit:** {_err}"), kind="danger"))

    _out_dir = ROOT / "output"
    _out_dir.mkdir(exist_ok=True)
    _stem = f"{_notes_path.stem.replace('_notation', '')}-{tonos.value.lower()}-{division.value}"
    _midi_path = _out_dir / f"{_stem}.mid"
    _wav_path = _out_dir / f"{_stem}-{voice.value}.wav"
    _midi_path.write_bytes(_midi)
    _wav_path.write_bytes(_wav)

    mo.vstack([
        mo.md(f"**{tonos.value}, {_tuning.system.division.name.lower()}, "
              f"{voice.value}, {tempo.value} chronoi/min**"),
        mo.audio(_wav),
        mo.md(f"Saved `{_midi_path.relative_to(ROOT)}` and `{_wav_path.relative_to(ROOT)}`"),
        mo.plain_text(_display) if _display else mo.md(""),
    ])
    return


if __name__ == "__main__":
    app.run()
