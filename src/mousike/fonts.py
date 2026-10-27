"""The "Mousike Notation" font, bundled with mousike.

A small font (about 100 characters) that can display every sign in
Sowerby's table together with mousike's combining length and arsis marks
(see ``Note.unicode``). It merges glyphs from Noto Serif and Noto Music and
is licensed under the SIL Open Font License 1.1 (``data/fonts/OFL.txt``).
It's rebuilt by ``fonts/build.py`` in the source repository.

Use it only for notation: it has the capital Greek letters the signs use,
but not lower-case Greek or Latin text.

* ``font_path("woff2")`` / ``font_path("ttf")``: the font file (install the
  TTF on your computer to see notation in other apps).
* ``font_css()``: an ``@font-face`` rule with the font embedded, plus a
  ``.mousike-notation`` class, ready to put in a ``<style>`` element.
"""

import base64
from functools import lru_cache
from importlib import resources
from pathlib import Path

FONT_FAMILY = "Mousike Notation"
CSS_CLASS = "mousike-notation"
_FILES = {"woff2": "MousikeNotation.woff2", "ttf": "MousikeNotation.ttf"}
_MIME = {"woff2": "font/woff2", "ttf": "font/ttf"}
_CSS_FORMAT = {"woff2": "woff2", "ttf": "truetype"}


def font_path(fmt: str = "woff2") -> Path:
    """Path to the bundled font file, ``"woff2"`` (web) or ``"ttf"`` (desktop)."""
    try:
        name = _FILES[fmt]
    except KeyError:
        raise ValueError(f"fmt must be one of {', '.join(_FILES)}") from None
    return Path(str(resources.files("mousike").joinpath("data/fonts", name)))


@lru_cache(maxsize=None)
def _data_uri(fmt: str) -> str:
    data = font_path(fmt).read_bytes()
    return f"data:{_MIME[fmt]};base64,{base64.b64encode(data).decode('ascii')}"


def font_css(embed: bool = True, url: str = None, fmt: str = "woff2",
             fallback: str = "serif") -> str:
    """CSS defining the ``Mousike Notation`` font and a ``.mousike-notation``
    class that uses it.

    By default the font is embedded as a data URI, so the CSS works
    anywhere (marimo, saved HTML pages) with nothing else to copy. Pass
    ``embed=False`` and ``url`` (where you've put the font file) to link it
    instead.
    """
    if embed:
        src = _data_uri(fmt)
    elif url:
        src = url
    else:
        raise ValueError("give url= when embed=False")
    return (
        "@font-face {\n"
        f"  font-family: '{FONT_FAMILY}';\n"
        f"  src: url('{src}') format('{_CSS_FORMAT[fmt]}');\n"
        "  font-display: block;\n"
        "}\n"
        f".{CSS_CLASS} {{ font-family: '{FONT_FAMILY}', {fallback}; }}\n"
    )
