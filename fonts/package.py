"""Package the Mousike Notation font for download.

Writes ``fonts/dist/MousikeNotation.zip`` containing the desktop font (TTF),
the web font (WOFF2), the licence, the specimen PDF and a README with
install instructions. Uses only the Python standard library, and the zip
is reproducible: the same files always give a byte-identical zip.

The publish-pypi GitHub workflow runs this and attaches the zip to each
GitHub release, so the latest version is always at
https://github.com/neelsmith/mousike/releases/latest/download/MousikeNotation.zip

Usage::

    python fonts/package.py
"""

import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FONTS = ROOT / "src" / "mousike" / "data" / "fonts"
OUT = HERE / "dist" / "MousikeNotation.zip"
DOWNLOAD_URL = "https://github.com/neelsmith/mousike/releases/latest/download/MousikeNotation.zip"
FIXED_TIME = (2026, 10, 27, 0, 0, 0)       # zip entry timestamps, for reproducibility


def font_version() -> str:
    return re.search(r'^VERSION\s*=\s*"([^"]+)"', (HERE / "build.py").read_text(), re.M).group(1)


def readme(version: str) -> str:
    return f"""Mousike Notation {version}
=======================

A font for ancient Greek musical notation as encoded in Zach Sowerby's URN
scheme, made for the mousike Python package (https://pypi.org/project/mousike/).
It covers every vocal and instrumental sign in the encoding's table, and
positions the combining length signs (diseme U+0305, triseme U+1D242,
tetraseme U+1D243, pentaseme U+1D244) and the arsis dot (U+0307) above them.
See MousikeNotation-specimen.pdf for every sign.

Use it for notation only: it contains the capital Greek letters the signs
use, but no lower-case Greek or Latin text.

Files
-----
MousikeNotation.ttf           desktop font (macOS, Windows, Linux)
MousikeNotation.woff2         web font
MousikeNotation-specimen.pdf  every sign, with its URN and name
OFL.txt                       licence

Installing on your computer
---------------------------
macOS:    double-click MousikeNotation.ttf, then click "Install".
Windows:  right-click MousikeNotation.ttf, then choose "Install".
Linux:    copy MousikeNotation.ttf to ~/.local/share/fonts/ and run fc-cache -f.

Using on a web page
-------------------
Put MousikeNotation.woff2 next to your page and add:

  @font-face {{
    font-family: 'Mousike Notation';
    src: url('MousikeNotation.woff2') format('woff2');
  }}
  .notation {{ font-family: 'Mousike Notation', serif; }}

then wrap notation in <span class="notation">...</span>.
(In Python, mousike.font_css() gives this CSS with the font embedded.)

Licence
-------
Mousike Notation is merged from Noto Serif and Noto Music,
Copyright 2022 The Noto Project Authors, and is licensed under the
SIL Open Font License, Version 1.1 (see OFL.txt).

Source, build script and latest version
---------------------------------------
https://github.com/neelsmith/mousike
{DOWNLOAD_URL}
"""


def main():
    version = font_version()
    files = {
        "MousikeNotation.ttf": (FONTS / "MousikeNotation.ttf").read_bytes(),
        "MousikeNotation.woff2": (FONTS / "MousikeNotation.woff2").read_bytes(),
        "OFL.txt": (FONTS / "OFL.txt").read_bytes(),
        "MousikeNotation-specimen.pdf": (HERE / "MousikeNotation-specimen.pdf").read_bytes(),
        "README.txt": readme(version).encode("utf-8"),
    }
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            info = zipfile.ZipInfo(f"MousikeNotation-{version}/{name}", date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, font version {version})")


if __name__ == "__main__":
    main()
