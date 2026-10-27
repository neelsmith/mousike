"""HTML displays of aligned editions, using the bundled notation font."""

import html

from .fonts import CSS_CLASS, font_css

_STYLE = (
    ".mousike-passage { margin: 0.3em 0 1em; }"
    ".mousike-passage .ref { font-weight: bold; margin-bottom: 0.2em; }"
    ".mousike-passage .syls { display: flex; flex-wrap: wrap; column-gap: 0.9em; row-gap: 0.5em; }"
    ".mousike-syl { display: inline-flex; flex-direction: column; align-items: flex-start; }"
    ".mousike-syl .notes { font-size: __SIZE__; line-height: 1.7; white-space: nowrap; }"
)


def alignment_html(passages, include_css: bool = True, font_size: str = "1.5em") -> str:
    """An HTML rendering of aligned passages: each syllable is a small block
    with its notes (with length and arsis marks) above the syllable.

    Notes and syllables line up in any font, unlike the plain-text
    ``str(passage)``, and long passages wrap. ``include_css`` embeds the
    notation font (about 8 KB); set it to False if the page already
    includes ``font_css()`` and the ``.mousike-*`` styles.
    """
    parts = []
    if include_css:
        style = _STYLE.replace("__SIZE__", font_size)
        parts.append(f"<style>{font_css()}{style}</style>")
    for p in passages:
        syls = "".join(
            '<span class="mousike-syl">'
            f'<span class="notes {CSS_CLASS}">{html.escape(s.notes)}</span>'
            f'<span class="text">{html.escape(s.syllable + ("" if s.word_final else "-"))}</span>'
            "</span>"
            for s in p.syllables)
        parts.append(f'<div class="mousike-passage"><div class="ref">{html.escape(str(p.ref))}</div>'
                     f'<div class="syls">{syls}</div></div>')
    return "\n".join(parts)
