# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "marimo",
#     "mousike>=0.2.0",
# ]
# ///
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import html
    import json
    import sys

    import marimo as mo

    # Prefer the repo's own source when the notebook is run from the repo:
    # note_urn_spans is newer than the latest mousike release on PyPI.
    _src = mo.notebook_dir().parent / "src"
    if (_src / "mousike").is_dir() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
        for _name in [m for m in sys.modules if m == "mousike" or m.startswith("mousike.")]:
            del sys.modules[_name]

    from mousike import (DIVISIONS, Note, PtolemaicTuning, TuningMismatch,
                         find_signs, load_table, load_tonoi, midi_bytes,
                         note_urn_spans, parse_note_groups, wav_bytes)
    from mousike.fonts import CSS_CLASS, font_css

    # Page styles: the bundled notation font, plus the formatted display.
    STYLE = font_css() + """
    .mk-display { white-space: pre-wrap; font-size: 1.35em; line-height: 1.8;
                  padding: 0.6em 0.8em; min-height: 12em;
                  border: 1px solid var(--gray-6, #ccc); border-radius: 6px; }
    .mk-display .mk-sign { font-size: 1.15em; }
    .mk-display .mk-bad { color: #c62828; text-decoration: underline wavy; }
    .mk-empty { color: var(--gray-9, #888); font-style: italic; }
    """
    return (
        CSS_CLASS,
        DIVISIONS,
        Note,
        PtolemaicTuning,
        STYLE,
        TuningMismatch,
        find_signs,
        font_css,
        html,
        json,
        load_table,
        load_tonoi,
        midi_bytes,
        mo,
        note_urn_spans,
        parse_note_groups,
        wav_bytes,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Notation editor

    Type or paste text on the left. Any note URN in it, full
    (`urn:cite2:zst:gvn:11.1.1.0.0`) or short (`gvn:11.1.1.0.0`), is shown
    as its Unicode sign on the right; notes joined with `~` are written
    together. A URN that isn't in Sowerby's table is underlined in red.

    To enter a sign directly, type part of its description in **Search**
    (`vocal G`, `first sharp of e''`): the best match is selected as you
    type. Note names are case-sensitive (`G` is not `g`), and `'` stands
    for a prime. Set the length and arsis, then press **OK** to copy its
    URN and paste it anywhere, including the text area.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    notation = mo.ui.radio(
        options={"Vocal": "gvn", "Instrumental": "gin"},
        value="Vocal",
        inline=True,
        label="**Notation**",
    )
    search = mo.ui.text(
        placeholder="e.g. vocal G, first sharp of e'', gvn:11",
        label="**Search**",
        debounce=150,
        full_width=True,
    )
    return notation, search


@app.cell(hide_code=True)
def _(find_signs, load_table, mo, notation, search):
    # Signs of the chosen notation (plus the rest, gcn, which belongs to
    # neither) that match the search, best match first. The best match is
    # selected, so typing alone is enough to choose a sign.
    _table = load_table()
    _matches = find_signs(search.value, collections=(notation.value, "gcn"))
    _options = {f"{_table[urn][1]}  ({urn})": urn for urn in _matches}
    picker = mo.ui.dropdown(
        options=_options,
        value=next(iter(_options)) if search.value.strip() and _options else None,
        searchable=True,
        label=f"**Sign** ({len(_options)} match{'' if len(_options) == 1 else 'es'})",
        full_width=True,
    )
    return (picker,)


@app.cell(hide_code=True)
def _(mo):
    # Length and arsis to add to the chosen sign. The hyphen tier is always 0.
    length = mo.ui.dropdown(
        options={"1 (no length sign)": 1, "2 diseme": 2, "3 triseme": 3,
                 "4 tetraseme": 4, "5 pentaseme": 5},
        value="1 (no length sign)",
        label="**Length**",
    )
    arsis = mo.ui.checkbox(value=False, label="**Arsis**")
    return arsis, length


@app.cell(hide_code=True)
def _(CSS_CLASS, Note, arsis, font_css, html, json, length, mo, notation, picker, search):
    def _note_for(key, length, arsis):
        """The note for a table entry with the chosen length and arsis.
        Signs with a single tier (the rest) take no length or arsis."""
        if len(key.split(":")[1].split(".")) < 2:
            return Note(key)
        return Note(f"{key}.{length}.{int(arsis)}.0")

    def _copy_panel(note):
        """The note, large, with an OK button that copies its full URN to the
        clipboard (and one that copies the sign itself). Rendered in an
        iframe so the buttons' script runs."""
        sign = note.unicode
        codes = " ".join(f"U+{ord(c):04X}" for c in sign)
        return mo.iframe(f"""
    <style>
    {font_css()}
    body {{ margin: 0; font-family: system-ui, sans-serif; font-size: 14px;
           display: flex; align-items: center; gap: 1.2em; }}
    .sign {{ font-size: 44px; line-height: 1.5; min-width: 1.3em; text-align: center; }}
    .meta div {{ margin: 0.15em 0; }}
    code {{ font-size: 13px; }}
    button {{ font: inherit; padding: 0.25em 0.8em; margin-right: 0.4em; cursor: pointer; }}
    #ok {{ font-weight: 600; }}
    #msg {{ color: #2e7d32; margin-left: 0.3em; }}
    </style>
    <div class="sign {CSS_CLASS}">{html.escape(sign)}</div>
    <div class="meta">
      <div><b>{html.escape(note.name)}</b> &nbsp; <code>{html.escape(note.urn)}</code> &nbsp; <code>{codes}</code></div>
      <div>
        <button id="ok">OK: copy URN</button>
        <button id="copy-sign">Copy sign</button>
        <span id="msg"></span>
      </div>
    </div>
    <script>
    async function copy(text, what) {{
      const msg = document.getElementById("msg");
      try {{
        await navigator.clipboard.writeText(text);
      }} catch (e) {{
        // Fallback for browsers that block the async clipboard API here.
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand("copy");
        ta.remove();
        if (!ok) {{ msg.style.color = "#c62828"; msg.textContent = "Couldn't copy: select the text and copy it by hand."; return; }}
      }}
      msg.style.color = "#2e7d32";
      msg.textContent = what + " copied";
      setTimeout(() => (msg.textContent = ""), 2000);
    }}
    document.getElementById("ok").onclick = () => copy({json.dumps(note.urn)}, {json.dumps(note.urn)});
    document.getElementById("copy-sign").onclick = () => copy({json.dumps(sign)}, "Sign");
    </script>
    """, height="90px")

    _panel = mo.md("")
    if search.value.strip() and not picker.value:
        _panel = mo.md("*No sign matches that search.* Note names are case-sensitive "
                       "(`G` is not `g`); type `'` for a prime.")
    if picker.value:
        _note = _note_for(picker.value, length.value, arsis.value)
        _panel = _copy_panel(_note)
        if _note.sharpening is None and (length.value != 1 or arsis.value):
            _panel = mo.vstack([_panel, mo.md("*The rest takes no length or arsis.*")])

    mo.vstack([
        notation,
        search,
        mo.hstack([picker, length, arsis], widths=[6, 2, 1], align="end", gap=1),
        _panel,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    editor = mo.ui.text_area(
        placeholder="e.g.  ὅσον ζῆς φαίνου: gvn:11.1.1.0.0 gvn:15.1.2.0.0 gvn:13.3.1.0.0~gvn:14.1.1.0.0",
        label="**Text**",
        rows=14,
        full_width=True,
        debounce=250,
    )
    return (editor,)


@app.cell(hide_code=True)
def _(CSS_CLASS, STYLE, editor, html, mo, note_urn_spans):
    def _formatted(text):
        """HTML for the text with note URNs shown as Unicode signs."""
        if not text.strip():
            return '<div class="mk-display"><span class="mk-empty">Formatted text appears here.</span></div>'
        parts = []
        for src, uni, err in note_urn_spans(text):
            if uni is not None:
                parts.append(f'<span class="mk-sign {CSS_CLASS}" title="{html.escape(src)}">'
                             f'{html.escape(uni)}</span>')
            elif err is not None:
                parts.append(f'<span class="mk-bad" title="{html.escape(err)}">{html.escape(src)}</span>')
            else:
                parts.append(html.escape(src))
        return f'<div class="mk-display">{"".join(parts)}</div>'

    mo.hstack(
        [
            editor,
            mo.vstack([mo.md("**Formatted**"),
                       mo.Html(f"<style>{STYLE}</style>{_formatted(editor.value)}")]),
        ],
        widths="equal",
        align="start",
        gap=1.5,
    )
    return


@app.cell(hide_code=True)
def _(DIVISIONS, load_tonoi, mo):
    # Playback controls, as in the diatonic notebook: diatonic divisions only.
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
    play = mo.ui.run_button(label="Play", kind="success")
    mo.vstack([
        mo.md("## Listen"),
        mo.md("Plays every note URN in the text, in order. Notes joined with "
              "`~` are sung on one syllable (slurred on the aulos)."),
        mo.hstack([tonos, division, voice], justify="start"),
        tempo,
        play,
    ])
    return division, play, tempo, tonos, voice


@app.cell(hide_code=True)
def _(
    PtolemaicTuning,
    TuningMismatch,
    division,
    editor,
    midi_bytes,
    mo,
    note_urn_spans,
    parse_note_groups,
    play,
    tempo,
    tonos,
    voice,
    wav_bytes,
):
    mo.stop(tonos.value is None or division.value is None,
            mo.md("*Select a tonos and a division.*"))
    mo.stop(not play.value, mo.md("*Press **Play** to hear the notes in the text.*"))

    # Note groups from the text, in order; URNs not in the table are skipped.
    _spans = note_urn_spans(editor.value)
    _groups = [g for src, uni, _err in _spans if uni is not None
               for g in parse_note_groups(src)]
    _bad = [src for src, _uni, err in _spans if err is not None]
    mo.stop(not _groups, mo.md("*The text has no note URNs to play.*"))

    _chronos = 60 / tempo.value     # seconds per chronos (base time unit)
    _program = {"lyre": 46, "aulos": 68, "simple": 52}[voice.value]  # harp, oboe, choir (GM)
    _tuning = PtolemaicTuning(division.value, tonos.value)
    try:
        _wav = wav_bytes(_groups, _tuning, voice=voice.value, chronos_seconds=_chronos)
        _midi = midi_bytes(_groups, _tuning, program=_program, chronos_seconds=_chronos)
    except TuningMismatch as _err:
        mo.stop(True, mo.callout(mo.md(f"**Doesn't fit:** {_err}"), kind="danger"))

    _stem = f"editor-{tonos.value.lower()}-{division.value}"
    _n = sum(len(g) for g in _groups)
    mo.vstack([
        mo.md(f"**{tonos.value}, {_tuning.system.division.name.lower()}, "
              f"{voice.value}, {tempo.value} chronoi/min**: {_n} note{'' if _n == 1 else 's'}"),
        mo.audio(_wav),
        mo.hstack([
            mo.download(_wav, filename=f"{_stem}-{voice.value}.wav", mimetype="audio/wav",
                        label="Download WAV"),
            mo.download(_midi, filename=f"{_stem}.mid", mimetype="audio/midi",
                        label="Download MIDI"),
        ], justify="start"),
        mo.callout(mo.md("Skipped URNs not in Sowerby's table: "
                         + ", ".join(f"`{b}`" for b in _bad)), kind="warn")
        if _bad else mo.md(""),
    ])
    return


if __name__ == "__main__":
    app.run()
