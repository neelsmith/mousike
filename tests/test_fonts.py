import pathlib

import pytest

from mousike import (CSS_CLASS, FONT_FAMILY, Note, align_editions, alignment_html,
                     font_css, font_path, load_table)
from mousike.note import ARSIS_MARK, LENGTH_MARKS

ttLib = pytest.importorskip("fontTools.ttLib")
DATA = pathlib.Path(__file__).parents[1] / "editions"


@pytest.fixture(scope="module")
def font():
    return ttLib.TTFont(font_path("ttf"))


def test_files_present():
    for fmt in ("woff2", "ttf"):
        assert font_path(fmt).exists()
        assert font_path(fmt).stat().st_size < 50_000
    assert (font_path("ttf").parent / "OFL.txt").exists()


def test_font_path_bad_format():
    with pytest.raises(ValueError):
        font_path("otf")


def test_names(font):
    assert font["name"].getDebugName(1) == FONT_FAMILY == "Mousike Notation"
    assert font["OS/2"].fsType == 0
    assert "Open Font License" in font["name"].getDebugName(13)


def every_rendering():
    """Note.unicode for every sign in the table, with every length and arsis."""
    for key in load_table():
        if key.startswith("gcn:"):
            yield Note(key).unicode
            continue
        for length in range(1, 6):
            for arsis in (0, 1):
                yield Note(f"{key}.{length}.{arsis}.0").unicode


def test_covers_everything_mousike_writes(font):
    cmap = font.getBestCmap()
    missing = {f"U+{ord(c):04X}" for s in every_rendering() for c in s if ord(c) not in cmap}
    assert not missing


def test_marks_are_zero_width_mark_glyphs(font):
    cmap, gdef = font.getBestCmap(), font["GDEF"].table.GlyphClassDef.classDefs
    for ch in list(LENGTH_MARKS.values()) + [ARSIS_MARK]:
        g = cmap[ord(ch)]
        assert font["hmtx"][g][0] == 0
        assert gdef[g] == 3                       # mark


def _lookups(font, lookup_type):
    gpos = font["GPOS"].table
    return [st for lk in gpos.LookupList.Lookup if lk.LookupType == lookup_type
            for st in lk.SubTable]


def test_every_sign_has_a_mark_anchor(font):
    cmap = font.getBestCmap()
    bases = {g for st in _lookups(font, 4) for g in st.BaseCoverage.glyphs}
    marks = {g for st in _lookups(font, 4) for g in st.MarkCoverage.glyphs}
    signs = {c for k, (sym, _) in load_table().items() for c in sym if c != "′"}
    assert {cmap[ord(c)] for c in signs} <= bases
    assert {cmap[ord(c)] for c in list(LENGTH_MARKS.values()) + [ARSIS_MARK]} <= marks


def test_dot_stacks_on_length_marks(font):
    cmap = font.getBestCmap()
    mkmk = _lookups(font, 6)
    lower = {g for st in mkmk for g in st.Mark2Coverage.glyphs}
    upper = {g for st in mkmk for g in st.Mark1Coverage.glyphs}
    assert {cmap[ord(c)] for c in LENGTH_MARKS.values()} <= lower
    assert cmap[ord(ARSIS_MARK)] in upper


def test_font_css_embedded():
    css = font_css()
    assert f"font-family: '{FONT_FAMILY}'" in css
    assert "data:font/woff2;base64," in css
    assert f".{CSS_CLASS} " in css


def test_font_css_linked():
    css = font_css(embed=False, url="fonts/MousikeNotation.woff2")
    assert "url('fonts/MousikeNotation.woff2')" in css and "base64" not in css
    with pytest.raises(ValueError):
        font_css(embed=False)


def test_alignment_html():
    if not (DATA / "seikilos_text.cex").exists():
        pytest.skip("Seikilos data not present")
    passages = align_editions(DATA / "seikilos_text.cex", DATA / "seikilos_notation.cex")
    h = alignment_html(passages)
    assert h.startswith("<style>@font-face")
    assert h.count('<div class="mousike-passage">') == 4
    assert h.count('<span class="mousike-syl">') == 29
    assert f'<span class="notes {CSS_CLASS}">Ζ\u0305</span>' in h
    assert '<span class="text">φαι-</span>' in h
    assert "@font-face" not in alignment_html(passages, include_css=False)


def test_alignment_html_escapes():
    from mousike import align_passage
    p = align_passage("ο", "gvn:11.1.1.0.0", "<1>")
    assert "&lt;1&gt;" in alignment_html([p], include_css=False)
