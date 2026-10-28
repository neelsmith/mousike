import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utilities"))

from make_tokens import (main, output_name, token_urn,  # noqa: E402
                         tokenize_edition, tokenize_line)


def test_token_urn():
    assert (token_urn("urn:cts:mousike:epigraphic.seikilos.text:1", 3)
            == "urn:cts:mousike:epigraphic.seikilos.tokens:1.3")


def test_token_urn_rejects_non_text_version():
    with pytest.raises(ValueError):
        token_urn("urn:cts:mousike:epigraphic.seikilos.notation:1", 1)


def test_tokenize_line():
    assert tokenize_line("urn:cts:mousike:epigraphic.seikilos.text:1|οσον ζης φαινου") == [
        "urn:cts:mousike:epigraphic.seikilos.tokens:1.1|ο-",
        "urn:cts:mousike:epigraphic.seikilos.tokens:1.2|σον",
        "urn:cts:mousike:epigraphic.seikilos.tokens:1.3|ζης",
        "urn:cts:mousike:epigraphic.seikilos.tokens:1.4|φαι-",
        "urn:cts:mousike:epigraphic.seikilos.tokens:1.5|νου",
    ]


def test_tokenize_edition_skips_header_and_blanks():
    lines = ["urn|text", "", "urn:cts:mousike:epigraphic.seikilos.text:3|το ζην", ""]
    assert tokenize_edition(lines) == [
        "urn|text",
        "urn:cts:mousike:epigraphic.seikilos.tokens:3.1|το",
        "urn:cts:mousike:epigraphic.seikilos.tokens:3.2|ζην",
    ]


def test_output_name():
    assert output_name(Path("editions/seikilos_text.cex")) == "seikilos_tokens.cex"


def test_main_writes_files(tmp_path):
    data = tmp_path / "editions"
    data.mkdir()
    (data / "demo_text.cex").write_text(
        "urn|text\nurn:cts:mousike:x.demo.text:1|ζης\n", encoding="utf-8")
    out = tmp_path / "out"
    main([str(out), "--editions-dir", str(data)])
    assert (out / "demo_tokens.cex").read_text(encoding="utf-8") == (
        "urn|text\nurn:cts:mousike:x.demo.tokens:1.1|ζης\n")
