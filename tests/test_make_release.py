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
    ed = tmp_path / "editions"
    write(ed / "a_text.cex", "urn|text\nurn:cts:m:a.text:1|ζης\n")
    write(ed / "b_text.cex", "urn|text\n\nurn:cts:m:b.text:1|συ")
    write(ed / "a_notation.cex", "urn|text\nurn:cts:m:a.notes:1|gvn:11.1.1.0.0\n")
    write(ed / "a_syllables.cex", "urn|text\nurn:cts:m:a.syllables:1.1|ζης\n")
    write(ed / "a_dse.cex", "image|text|surface\nurn:i@0,0,1,1|urn:cts:m:a.notes:1.1|urn:s\n\n")
    return tmp_path


def test_build_release(repo):
    vid, text = build_release(repo)
    assert vid == "2026a"
    assert text == (
        "#!version\n2026a\n\n"
        "#!images\npath|urn\nx.png|urn:cite2:m:img.v1:x\n\n"
        "#!surfaces\nurn|label\nurn:cite2:m:a.s|Stele\n\n"
        "#!audio\nfile|label\na.wav|A\n\n"
        "#!texts\nurn|text\nurn:cts:m:a.text:1|ζης\nurn:cts:m:b.text:1|συ\n\n"
        "#!notes\nurn|text\nurn:cts:m:a.notes:1|gvn:11.1.1.0.0\n\n"
        "#!syllables\nurn|text\nurn:cts:m:a.syllables:1.1|ζης\n\n"
        "#!dse\nimage|text|surface\nurn:i@0,0,1,1|urn:cts:m:a.notes:1.1|urn:s\n\n"
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
