#!/usr/bin/env python3
"""Create a syllable-level token edition for each text edition.

For every ``editions/*_text.cex`` file, writes ``OUTPUT_DIR/*_tokens.cex`` with
one line per syllable. The URN's version ID ``text`` becomes ``tokens`` and
the passage reference gains one level; syllables that do not end a word are
marked with a trailing hyphen:

    urn:cts:mousike:epigraphic.seikilos.text:1|οσον ζης φαινου

becomes

    urn:cts:mousike:epigraphic.seikilos.tokens:1.1|ο-
    urn:cts:mousike:epigraphic.seikilos.tokens:1.2|σον
    urn:cts:mousike:epigraphic.seikilos.tokens:1.3|ζης
    ...

Usage:
    python utilities/make_tokens.py OUTPUT_DIR [--editions-dir EDITIONS_DIR]
"""

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from mousike import syllabify  # noqa: E402

HEADER = "urn|text"


def token_urn(urn, n):
    """Swap the version ID ``text`` for ``tokens`` and append ``.n`` to the
    passage reference."""
    parts = urn.split(":")
    if len(parts) != 5:
        raise ValueError(f"Not a passage-level CTS URN: {urn}")
    work = parts[3].split(".")
    if len(work) < 3 or work[-1] != "text":
        raise ValueError(f"Expected version ID 'text' in URN: {urn}")
    work[-1] = "tokens"
    parts[3] = ".".join(work)
    parts[4] = f"{parts[4]}.{n}"
    return ":".join(parts)


def tokenize_line(line):
    """Turn one ``urn|text`` data line into a list of token lines."""
    urn, text = line.split("|", 1)
    tokens = []
    for word in syllabify(text):
        for i, syll in enumerate(word):
            tokens.append(syll if i == len(word) - 1 else syll + "-")
    return [f"{token_urn(urn, n)}|{tok}" for n, tok in enumerate(tokens, 1)]


def tokenize_edition(lines):
    """Turn the lines of a text edition into the lines of a token edition
    (header included). Blank lines and the ``urn|text`` header are skipped."""
    out = [HEADER]
    for line in lines:
        line = line.strip()
        if not line or line == HEADER:
            continue
        out.extend(tokenize_line(line))
    return out


def output_name(path):
    """``seikilos_text.cex`` -> ``seikilos_tokens.cex``"""
    stem = path.stem
    if not stem.endswith("_text"):
        raise ValueError(f"Not a text edition file name: {path.name}")
    return stem[: -len("_text")] + "_tokens" + path.suffix


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("output_dir", type=Path, help="directory to write token editions to")
    ap.add_argument("--editions-dir", type=Path, default=REPO / "editions",
                    help="directory containing *_text.cex files (default: repo editions/)")
    args = ap.parse_args(argv)

    sources = sorted(args.editions_dir.glob("*_text.cex"))
    if not sources:
        sys.exit(f"No *_text.cex files found in {args.editions_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for src in sources:
        lines = tokenize_edition(src.read_text(encoding="utf-8").splitlines())
        dest = args.output_dir / output_name(src)
        dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{src.name} -> {dest} ({len(lines) - 1} tokens)")


if __name__ == "__main__":
    main()
