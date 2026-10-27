"""Make a PDF specimen of the Mousike Notation font.

Shows every sign in Sowerby's table in four forms (plain; diseme; triseme
with arsis; pentaseme) with its URN and name, plus a key to the combining
marks. Uses the mousike source in this repository (src/), the bundled font,
and Noto Serif (from the same pinned source as fonts/build.py) for text.

Writes ``fonts/MousikeNotation-specimen.html`` and, if Playwright is
installed (``pip install playwright && playwright install chromium``),
``fonts/MousikeNotation-specimen.pdf``. Without Playwright, open the HTML
in a browser and print it to PDF.

Usage::

    python fonts/specimen.py
"""

import base64
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

import build                                   # noqa: E402  (fonts/build.py)
from mousike import Note, font_css, load_table  # noqa: E402
from mousike.note import ARSIS_MARK, LENGTH_MARKS  # noqa: E402

OUT_HTML = HERE / "MousikeNotation-specimen.html"
OUT_PDF = HERE / "MousikeNotation-specimen.pdf"

FORMS = [  # (label, length, arsis)
    ("plain", 1, 0),
    ("diseme", 2, 0),
    ("triseme + arsis", 3, 1),
    ("pentaseme", 5, 0),
]
SECTIONS = [("gvn", "Vocal notation"), ("gin", "Instrumental notation"), ("gcn", "Other signs")]


def text_font_css() -> str:
    """Noto Serif (Latin) for the specimen's text, embedded."""
    files = build.package_files("noto-serif")
    rules = []
    for weight in (400, 700):
        for style in ("normal", "italic"):
            for subset in ("latin", "latin-ext"):
                data = files[f"files/noto-serif-{subset}-{weight}-{style}.woff2"]
                uri = "data:font/woff2;base64," + base64.b64encode(data).decode("ascii")
                rules.append(f"@font-face {{ font-family: 'Specimen Text'; font-weight: {weight};"
                             f" font-style: {style}; src: url('{uri}') format('woff2'); }}")
    return "\n".join(rules)


def esc(s):
    return html.escape(s, quote=True)


def cell(key, name):
    if key.startswith("gcn:"):
        forms = [Note(key).unicode]
    else:
        forms = [Note(f"{key}.{length}.{arsis}.0").unicode for _, length, arsis in FORMS]
    glyphs = "".join(f'<span class="form">{esc(f)}</span>' for f in forms)
    return (f'<div class="cell"><div class="glyphs mousike-notation">{glyphs}</div>'
            f'<div class="urn">{esc(key)}</div><div class="name">{esc(name)}</div></div>')


def marks_key():
    rows = []
    entries = [("diseme", LENGTH_MARKS[2]), ("triseme", LENGTH_MARKS[3]),
               ("tetraseme", LENGTH_MARKS[4]), ("pentaseme", LENGTH_MARKS[5]),
               ("arsis (stigme)", ARSIS_MARK)]
    import unicodedata
    for label, mark in entries:
        rows.append(f"<tr><td>{label}</td><td class='mousike-notation big'>Ζ{mark}</td>"
                    f"<td>U+{ord(mark):04X}</td><td class='uname'>{unicodedata.name(mark)}</td></tr>")
    rows.append("<tr><td>length + arsis</td><td class='mousike-notation big'>"
                f"Ζ{LENGTH_MARKS[3]}{ARSIS_MARK}</td><td>e.g. U+1D242 U+0307</td>"
                "<td class='uname'>the dot stacks above the length sign</td></tr>")
    return "<table class='key'>" + "".join(rows) + "</table>"


def page() -> str:
    version = re.search(r'^version\s*=\s*"([^"]+)"',
                        (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    table = load_table()
    sections = []
    for prefix, title in SECTIONS:
        keys = [k for k in table if k.startswith(prefix + ":")]
        cells = "".join(cell(k, table[k][1]) for k in keys)
        sections.append(f'<section><h2>{title} <span class="count">({prefix}, {len(keys)} '
                        f'sign{"s" if len(keys) != 1 else ""})</span></h2>'
                        f'<div class="grid">{cells}</div></section>')
    legend = " · ".join(label for label, _, _ in FORMS)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Mousike Notation: font specimen</title>
<style>
{font_css()}
{text_font_css()}
@page {{ size: Letter; margin: 0.55in 0.55in 0.7in; }}
body {{ font-family: 'Specimen Text', serif; color: #1a1a1a; margin: 0; font-size: 10pt; }}
h1 {{ font-size: 24pt; margin: 0 0 4pt; font-weight: 700; }}
h2 {{ font-size: 14pt; margin: 18pt 0 8pt; break-after: avoid; }}
h2 .count {{ font-weight: 400; font-size: 10pt; color: #666; }}
.lede {{ font-size: 11pt; line-height: 1.45; max-width: 6.6in; margin: 6pt 0 10pt; }}
.grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 4pt; }}
.cell {{ border: 0.6pt solid #cfcfcf; border-radius: 3pt; padding: 4pt 4pt 4pt;
         text-align: center; break-inside: avoid; }}
.glyphs {{ font-size: 20pt; line-height: 1.6; white-space: nowrap; }}
.form {{ display: inline-block; min-width: 1.1em; margin: 0 0.08em; }}
.urn {{ font-family: 'DejaVu Sans Mono', monospace; font-size: 7.5pt; color: #555; margin-top: 2pt; }}
.name {{ font-size: 7.5pt; font-style: italic; color: #555; }}
.key {{ border-collapse: collapse; margin: 4pt 0 6pt; }}
.key td {{ padding: 2pt 10pt 2pt 0; vertical-align: middle; }}
.key .big {{ font-size: 20pt; line-height: 1.6; }}
.key .uname {{ font-size: 8pt; color: #555; }}
.legend {{ font-size: 9.5pt; color: #444; }}
.download {{ font-size: 9.5pt; background: #f3f3f3; border-radius: 3pt; padding: 5pt 8pt;
             margin: 0 0 4pt; max-width: 6.6in; }}
.about {{ font-size: 9pt; line-height: 1.45; color: #333; border-top: 0.6pt solid #ccc;
          margin-top: 14pt; padding-top: 8pt; break-inside: avoid; }}
a {{ color: inherit; }}
</style></head>
<body>
<h1>Mousike Notation</h1>
<div class="lede">A font for ancient Greek musical notation as encoded in Zach Sowerby's URN
scheme, made for the <a href="https://pypi.org/project/mousike/">mousike</a> Python package.
It covers every vocal and instrumental sign in the encoding's table, and positions the
combining length signs and arsis dot that mousike writes for each note.</div>
<div class="download"><b>Download</b> the font (desktop TTF, web WOFF2, licence and this specimen):
<a href="https://github.com/neelsmith/mousike/releases/latest/download/MousikeNotation.zip">github.com/neelsmith/mousike/releases/latest/download/MousikeNotation.zip</a></div>

<h2>Combining marks</h2>
{marks_key()}
<div class="legend">Each sign below is shown in four forms: {legend}.</div>

{''.join(sections)}

<div class="about">
<b>Mousike Notation {build.VERSION}</b>, distributed with mousike {version}.
Merged from <b>Noto Serif</b> (Greek letters, lunate sigma, prime, combining overline and dot)
and <b>Noto Music</b> (the Greek Musical Notation block), with mark positioning added for
mousike. Copyright 2022 The Noto Project Authors. Licensed under the SIL Open Font License,
Version 1.1 (<a href="https://openfontlicense.org">openfontlicense.org</a>).
The encoding table is taken from Zach Sowerby's Holy Cross thesis work (2019).
Source and build script: <a href="https://github.com/neelsmith/mousike">github.com/neelsmith/mousike</a>.
</div>
</body></html>
"""


def main():
    OUT_HTML.write_text(page(), encoding="utf-8")
    print(f"wrote {OUT_HTML}")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed: open the HTML in a browser and print to PDF.")
        return
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pg = browser.new_page()
        pg.goto(OUT_HTML.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.pdf(path=str(OUT_PDF), prefer_css_page_size=True, print_background=True,
               display_header_footer=True, header_template="<span></span>",
               footer_template=('<div style="font-size:7pt;color:#888;width:100%;'
                                'text-align:center;font-family:serif;">Mousike Notation · '
                                'page <span class="pageNumber"></span> of '
                                '<span class="totalPages"></span></div>'))
        browser.close()
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
