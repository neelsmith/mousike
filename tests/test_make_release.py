import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utilities"))

from make_release import build_release, edition_block, main  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    write(tmp_path / "data-version.txt", "2026a\n")
    write(tmp_path / "images/catalog.cex", "path|urn\nx.png|urn:cite2:m:img.v1:x")
    write(tmp_path / "artifacts/catalog.cex", "urn|label\nurn:cite2:m:a.s|Stele\n\n")
    write(tmp_path / "audio/catalog.cex", "file|label\na.wav|A\n")
    write(tmp_path / "text-catalogs/ctscatalog-annotated.cex",
          "urn|citationScheme\nurn:cts:m:a.notes:|line\n\nurn:cts:m:a.syllables:|line/syllable\n")
    write(tmp_path / "text-catalogs/ctscatalog-embedded.cex",
          "urn|citationScheme\nurn:cts:m:c.v:|section/paragraph")
    ed = tmp_path / "editions"
    write(ed / "a_text.cex", "urn|text\nurn:cts:m:a.text:1|ζης\n")
    write(ed / "b_text.cex", "urn|text\n\nurn:cts:m:b.text:1|συ")
    write(ed / "a_notation.cex", "urn|text\nurn:cts:m:a.notes:1|gvn:11.1.1.0.0\n")
    write(ed / "a_syllables.cex", "urn|text\nurn:cts:m:a.syllables:1.1|ζης\n")
    write(ed / "a_dse.cex", "image|text|surface\nurn:i@0,0,1,1|urn:cts:m:a.notes:1.1|urn:s\n\n")
    cols = tmp_path / "editions_cols"
    write(cols / "c_mousike.cex",
          "#!ctsdata_cols\nurn:cts:m:c.v:1|1|title\n\nurn:cts:m:c.v:2|3|a | b | c \n   \n")
    write(cols / "c_dse.cex", "image|text|surface\nurn:j@0,0,1,1|urn:cts:m:c.v:1|urn:t\n")
    return tmp_path


def test_build_release(repo):
    vid, text = build_release(repo)
    assert vid == "2026a"
    assert text == (
        "#!version\n2026a\n\n"
        "#!images\npath|urn\nx.png|urn:cite2:m:img.v1:x\n\n"
        "#!surfaces\nurn|label\nurn:cite2:m:a.s|Stele\n\n"
        "#!audio\nfile|label\na.wav|A\n\n"
        "#!catalog_annotated\nurn|citationScheme\nurn:cts:m:a.notes:|line\nurn:cts:m:a.syllables:|line/syllable\n\n"
        "#!catalog_embedded\nurn|citationScheme\nurn:cts:m:c.v:|section/paragraph\n\n"
        "#!texts\nurn|text\nurn:cts:m:a.text:1|ζης\nurn:cts:m:b.text:1|συ\n\n"
        "#!texts_cols\nurn|columns|text\nurn:cts:m:c.v:1|1|title\nurn:cts:m:c.v:2|3|a | b | c\n\n"
        "#!notes\nurn|text\nurn:cts:m:a.notes:1|gvn:11.1.1.0.0\n\n"
        "#!syllables\nurn|text\nurn:cts:m:a.syllables:1.1|ζης\n\n"
        "#!dse\nimage|text|surface\nurn:i@0,0,1,1|urn:cts:m:a.notes:1.1|urn:s\n"
        "urn:j@0,0,1,1|urn:cts:m:c.v:1|urn:t\n\n"
    )


def test_edition_block_rejects_wrong_header(tmp_path):
    f = tmp_path / "x_dse.cex"
    write(f, "urn|text\nfoo|bar\n")
    with pytest.raises(ValueError):
        edition_block("dse", [f], "image|text|surface")


def test_main_writes_and_refuses_overwrite(repo, capsys):
    main(["--root", str(repo)])
    dest = repo / "releases" / "2026a.cex"
    assert dest.read_text(encoding="utf-8").startswith("#!version\n2026a\n\n")
    assert "no syllable edition for b_text.cex" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(["--root", str(repo)])
    main(["--root", str(repo), "--force"])


def test_cols_edition_needs_marker_line(tmp_path):
    f = tmp_path / "x_mousike.cex"
    write(f, "urn|columns|text\nurn:cts:m:x.v:1|1|t\n")
    with pytest.raises(ValueError):
        edition_block("texts_cols", [f], "urn|columns|text", "#!ctsdata_cols")


def test_no_editions_cols_directory(repo):
    import shutil
    shutil.rmtree(repo / "editions_cols")
    _, text = build_release(repo)
    assert "#!texts_cols\nurn|columns|text\n\n" in text


def test_missing_catalog_is_an_error(repo):
    (repo / "text-catalogs" / "ctscatalog-embedded.cex").unlink()
    with pytest.raises(FileNotFoundError):
        build_release(repo)
