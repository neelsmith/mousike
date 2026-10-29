import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utilities"))

from make_syllables import (main, output_name, syllabify_edition,  # noqa: E402
                            syllabify_line, syllable_urn)


def test_syllable_urn():
    assert (syllable_urn("urn:cts:mousike:epigraphic.seikilos.text:1", 3)
            == "urn:cts:mousike:epigraphic.seikilos.syllables:1.3")


def test_syllable_urn_rejects_non_text_version():
    with pytest.raises(ValueError):
        syllable_urn("urn:cts:mousike:epigraphic.seikilos.notation:1", 1)


def test_syllabify_line():
    assert syllabify_line("urn:cts:mousike:epigraphic.seikilos.text:1|οσον ζης φαινου") == [
        "urn:cts:mousike:epigraphic.seikilos.syllables:1.1|ο-",
        "urn:cts:mousike:epigraphic.seikilos.syllables:1.2|σον",
        "urn:cts:mousike:epigraphic.seikilos.syllables:1.3|ζης",
        "urn:cts:mousike:epigraphic.seikilos.syllables:1.4|φαι-",
        "urn:cts:mousike:epigraphic.seikilos.syllables:1.5|νου",
    ]


def test_syllabify_edition_skips_header_and_blanks():
    lines = ["urn|text", "", "urn:cts:mousike:epigraphic.seikilos.text:3|το ζην", ""]
    assert syllabify_edition(lines) == [
        "urn|text",
        "urn:cts:mousike:epigraphic.seikilos.syllables:3.1|το",
        "urn:cts:mousike:epigraphic.seikilos.syllables:3.2|ζην",
    ]


def test_output_name():
    assert output_name(Path("editions/seikilos_text.cex")) == "seikilos_syllables.cex"


def test_main_writes_files(tmp_path):
    editions = tmp_path / "editions"
    editions.mkdir()
    (editions / "demo_text.cex").write_text(
        "urn|text\nurn:cts:mousike:x.demo.text:1|ζης\n", encoding="utf-8")
    out = tmp_path / "out"
    main([str(out), "--editions-dir", str(editions)])
    assert (out / "demo_syllables.cex").read_text(encoding="utf-8") == (
        "urn|text\nurn:cts:mousike:x.demo.syllables:1.1|ζης\n")
