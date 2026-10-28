"""Build the "Mousike Notation" font shipped with mousike.

Merges the glyphs mousike needs from two SIL OFL fonts:

* Noto Serif (Greek letters, lunate sigma, Ʊ, prime, combining overline
  U+0305 and dot above U+0307), and
* Noto Music (the Greek Musical Notation block U+1D200-U+1D245, including
  the combining triseme/tetraseme/pentaseme U+1D242-U+1D244),

then adds mark positioning (GPOS ``mark`` and ``mkmk``) so that length
signs sit centred above any sign, and an arsis dot stacks above a length
sign. Anchors are computed from glyph outlines.

Sources are pinned Fontsource packages from the npm registry, checked by
SHA-256. Output (written to ``src/mousike/data/fonts/``):

* ``MousikeNotation.woff2`` (web), ``MousikeNotation.ttf`` (desktop install)
* ``OFL.txt`` (licence, with both sources' copyright notices)

Usage (needs ``pip install "fonttools[woff]"``)::

    python fonts/build.py
"""

import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.merge import Merger
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".cache"
OUT = ROOT / "src" / "mousike" / "data" / "fonts"
TABLE = ROOT / "src" / "mousike" / "data" / "sowerby_system.cex"

FAMILY = "Mousike Notation"
PS_NAME = "MousikeNotation-Regular"
VERSION = "1.000"

PACKAGES = {
    "noto-serif": ("https://registry.npmjs.org/@fontsource/noto-serif/-/noto-serif-5.3.0.tgz",
                   "846d219c2c9c668ebe2b5ca0e76c403a35f847d83c4c441c107f9bdc152830df"),
    "noto-music": ("https://registry.npmjs.org/@fontsource/noto-music/-/noto-music-5.3.0.tgz",
                   "cf49eff45964e7f3fa8d26c28fde18f50137d5b7b3964e43b5520c6a5f06f888"),
}

# Which subset file each character comes from (first match wins).
SOURCES = [
    ("noto-serif", "files/noto-serif-greek-400-normal.woff2"),
    ("noto-serif", "files/noto-serif-latin-400-normal.woff2"),
    ("noto-serif", "files/noto-serif-latin-ext-400-normal.woff2"),
    ("noto-serif", "files/noto-serif-math-400-normal.woff2"),
    ("noto-music", "files/noto-music-music-400-normal.woff2"),
]

MUSIC_BLOCK = set(range(0x1D200, 0x1D246))          # assigned Greek Musical Notation
LENGTH_MARKS = [0x0305, 0x1D242, 0x1D243, 0x1D244]   # attach to a sign
ARSIS_MARK = 0x0307                                  # attaches to a sign or a length mark
EXTRA = {0x0020, 0x00A0, 0x2032}                     # space, no-break space, prime

# head.created/modified, in seconds since 1904-01-01 (= 2026-10-27 00:00 UTC)
TIMESTAMP = 3875904000

GAP_BASE = 60     # font units between the top of a sign and a mark
GAP_MARK = 40     # between a length mark and the dot above it


def needed_codepoints() -> set:
    cps = set(MUSIC_BLOCK) | set(LENGTH_MARKS) | {ARSIS_MARK} | EXTRA
    for line in TABLE.read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            cps |= {ord(c) for c in line.split("|")[1].strip()}
    return cps


def package_files(name):
    """Fetch (or reuse cached) package tarball; return {member path: bytes}."""
    url, sha = PACKAGES[name]
    CACHE.mkdir(exist_ok=True)
    tgz = CACHE / url.rsplit("/", 1)[1]
    if not tgz.exists():
        print(f"downloading {url}")
        tgz.write_bytes(urllib.request.urlopen(url).read())
    digest = hashlib.sha256(tgz.read_bytes()).hexdigest()
    if digest != sha:
        raise SystemExit(f"{tgz.name}: SHA-256 {digest} doesn't match pinned {sha}")
    with tarfile.open(tgz) as tar:
        return {m.name.removeprefix("package/"): tar.extractfile(m).read()
                for m in tar.getmembers() if m.isfile()}


def subset_font(data: bytes, codepoints: set) -> TTFont:
    font = TTFont(io.BytesIO(data))
    opts = subset.Options()
    opts.layout_features = []          # we write our own GPOS
    opts.drop_tables += ["GSUB", "GPOS", "GDEF", "STAT", "fvar", "gvar", "avar", "HVAR", "MVAR"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.glyph_names = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=codepoints)
    sub.subset(font)
    font.flavor = None
    return font


def bbox(font, glyph):
    g = font["glyf"][glyph]
    g.recalcBounds(font["glyf"])
    if not hasattr(g, "xMin") or g.numberOfContours == 0:
        return None
    return g.xMin, g.yMin, g.xMax, g.yMax


def mark_features(font) -> str:
    cmap = font.getBestCmap()
    name = lambda cp: cmap[cp]
    length_marks = [name(cp) for cp in LENGTH_MARKS]
    dot = name(ARSIS_MARK)
    marks = set(length_marks) | {dot}
    skip = {name(cp) for cp in EXTRA if cp in cmap}
    bases = sorted({g for cp, g in cmap.items()} - marks - skip)

    lines = ["languagesystem DFLT dflt;", "languagesystem grek dflt;",
             "languagesystem latn dflt;", ""]
    # Each mark's own attachment point: centre of its bottom edge.
    for g in length_marks:
        x0, y0, x1, y1 = bbox(font, g)
        lines.append(f"markClass {g} <anchor {round((x0 + x1) / 2)} {y0}> @ABOVE;")
    x0, y0, x1, y1 = bbox(font, dot)
    dot_anchor = f"<anchor {round((x0 + x1) / 2)} {y0}>"
    lines.append(f"markClass {dot} {dot_anchor} @ABOVE;")
    lines.append(f"markClass {dot} {dot_anchor} @DOT_ON_MARK;")

    lines.append("\nfeature mark {")
    for g in bases:
        b = bbox(font, g)
        if b is None:
            continue
        x0, y0, x1, y1 = b
        lines.append(f"  pos base {g} <anchor {round((x0 + x1) / 2)} {y1 + GAP_BASE}> mark @ABOVE;")
    lines.append("} mark;\n")

    lines.append("feature mkmk {")
    for g in length_marks:
        x0, y0, x1, y1 = bbox(font, g)
        lines.append(f"  pos mark {g} <anchor {round((x0 + x1) / 2)} {y1 + GAP_MARK}> mark @DOT_ON_MARK;")
    lines.append("} mkmk;\n")

    lines.append("table GDEF {")
    lines.append(f"  GlyphClassDef [{' '.join(bases)}], , [{' '.join(sorted(marks))}], ;")
    lines.append("} GDEF;")
    return "\n".join(lines)


def set_names(font, copyrights):
    name = font["name"]
    name.names = []
    records = {
        0: "; ".join(copyrights),
        1: FAMILY, 2: "Regular",
        3: f"{VERSION};MOUSIKE;{PS_NAME}",
        4: f"{FAMILY} Regular",
        5: f"Version {VERSION}",
        6: PS_NAME,
        10: ("Greek musical notation signs with length and arsis marks, merged from "
             "Noto Serif and Noto Music for the mousike Python package."),
        13: ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
             "This license is available with a FAQ at: https://openfontlicense.org"),
        14: "https://openfontlicense.org",
    }
    for nid, text in records.items():
        name.setName(text, nid, 3, 1, 0x409)
    font["OS/2"].fsType = 0              # installable embedding
    font["head"].fontRevision = float(VERSION)
    # Fixed timestamps so the same sources always give identical files
    font["head"].created = font["head"].modified = TIMESTAMP
    font.recalcTimestamp = False


def build():
    want = needed_codepoints()
    pkgs = {n: package_files(n) for n in PACKAGES}
    remaining, parts = set(want), []
    for pkg, path in SOURCES:
        font = TTFont(io.BytesIO(pkgs[pkg][path]))
        take = remaining & set(font.getBestCmap())
        if take:
            parts.append(subset_font(pkgs[pkg][path], take))
            remaining -= take
    if remaining:
        raise SystemExit(f"no source for {[f'U+{c:04X}' for c in sorted(remaining)]}")

    tmp = []
    for i, f in enumerate(parts):
        buf = io.BytesIO(); f.save(buf); buf.seek(0); tmp.append(buf)
    merged = Merger().merge(tmp)

    addOpenTypeFeaturesFromString(merged, mark_features(merged))
    copyrights = ["Copyright 2022 The Noto Project Authors (https://github.com/notofonts/latin-greek-cyrillic)",
                  "Copyright 2022 The Noto Project Authors (https://github.com/notofonts/music)"]
    set_names(merged, copyrights)

    OUT.mkdir(parents=True, exist_ok=True)
    merged.flavor = None
    merged.save(OUT / "MousikeNotation.ttf")
    merged.flavor = "woff2"
    merged.save(OUT / "MousikeNotation.woff2")

    licence = pkgs["noto-music"]["LICENSE"].decode("utf-8")
    body = licence[licence.index("This Font Software"):]
    header = ("Mousike Notation is derived from Noto Serif and Noto Music.\n\n"
              + "\n".join(copyrights) + "\n\n")
    (OUT / "OFL.txt").write_text(header + body, encoding="utf-8")

    cmap = TTFont(OUT / "MousikeNotation.ttf").getBestCmap()
    print(f"{len(cmap)} characters, "
          f"{(OUT / 'MousikeNotation.woff2').stat().st_size // 1024} KB woff2, "
          f"{(OUT / 'MousikeNotation.ttf').stat().st_size // 1024} KB ttf -> {OUT}")


if __name__ == "__main__":
    build()
