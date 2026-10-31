#!/usr/bin/env python3
"""Bundle mousike's data into a single release file for use by other programs.

The release ID is read from ``data-version.txt``; output is written to
``releases/ID.cex``. The file is a series of blocks, each introduced by a
``#!label`` line and followed by an empty line:

    #!version   the release ID
    #!images    images/catalog.cex, verbatim
    #!surfaces  artifacts/catalog.cex, verbatim
    #!audio     audio/catalog.cex, verbatim
    #!catalog_annotated  text-catalogs/ctscatalog-annotated.cex, verbatim
    #!catalog_embedded   text-catalogs/ctscatalog-embedded.cex, verbatim
    #!mss       text-catalogs/mss.cex, verbatim
    #!texts     urn|text, then data lines of every editions/*_text.cex
    #!texts_cols urn|columns|text, then data lines of every
                editions_cols/*_mousike.cex (whose first line is #!ctsdata_cols)
    #!notes     urn|text, then data lines of every editions/*_notation.cex
    #!syllables urn|text, then data lines of every editions/*_syllables.cex
    #!dse       image|text|surface, then data lines of every *_dse.cex in
                editions/ and editions_cols/

Usage:
    python utilities/make_release.py [--root REPO_ROOT] [--force]
"""

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

CATALOGS = [
    ("images", "images/catalog.cex"),
    ("surfaces", "artifacts/catalog.cex"),
    ("audio", "audio/catalog.cex"),
    ("catalog_annotated", "text-catalogs/ctscatalog-annotated.cex"),
    ("catalog_embedded", "text-catalogs/ctscatalog-embedded.cex"),
    ("mss", "text-catalogs/mss.cex"),
]

# (label, source directories, file pattern, block header, expected first
# line of each source file -- None means the same as the block header)
EDITIONS = [
    ("texts", ("editions",), "*_text.cex", "urn|text", None),
    ("texts_cols", ("editions_cols",), "*_mousike.cex", "urn|columns|text",
     "#!ctsdata_cols"),
    ("notes", ("editions",), "*_notation.cex", "urn|text", None),
    ("syllables", ("editions",), "*_syllables.cex", "urn|text", None),
    ("dse", ("editions", "editions_cols"), "*_dse.cex", "image|text|surface", None),
]


def read_lines(path):
    """Lines of a file, with trailing whitespace and trailing blank lines
    removed (source files may or may not end in a newline)."""
    lines = [ln.rstrip() for ln in path.read_text(encoding="utf-8").splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def catalog_block(label, path):
    """A block reproducing a catalog file in full, except for blank lines,
    which would end the block early for anyone reading the release."""
    if not path.exists():
        raise FileNotFoundError(f"Missing catalog for #!{label}: {path}")
    return [f"#!{label}"] + [ln for ln in read_lines(path) if ln]


def edition_block(label, files, header, first_line=None):
    """A block with one header line followed by the data lines of each file.
    Each file's first line must be ``first_line`` (by default, ``header``)
    and is dropped; so are blank lines."""
    first_line = first_line or header
    out = [f"#!{label}", header]
    for path in files:
        lines = [ln for ln in read_lines(path) if ln]
        if not lines:
            continue
        if lines[0] != first_line:
            raise ValueError(
                f"{path}: expected first line {first_line!r}, found {lines[0]!r}")
        out.extend(lines[1:])
    return out


def release_id(root):
    vid = (root / "data-version.txt").read_text(encoding="utf-8").strip()
    if not vid or any(c in vid for c in "/\\\n"):
        raise ValueError(f"Bad release ID in data-version.txt: {vid!r}")
    return vid


def build_release(root):
    """Return (release ID, full text of the release file)."""
    vid = release_id(root)
    blocks = [["#!version", vid]]
    blocks += [catalog_block(label, root / rel) for label, rel in CATALOGS]
    for label, dirs, pattern, header, first_line in EDITIONS:
        files = [f for d in dirs for f in sorted((root / d).glob(pattern))]
        blocks.append(edition_block(label, files, header, first_line))
    return vid, "".join("\n".join(b) + "\n\n" for b in blocks)


def missing_syllables(root):
    """Text editions with no matching syllable edition."""
    editions = root / "editions"
    return [p.name for p in sorted(editions.glob("*_text.cex"))
            if not (editions / p.name.replace("_text.cex", "_syllables.cex")).exists()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=REPO,
                    help="repository root (default: this repo)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing release file")
    args = ap.parse_args(argv)

    for name in missing_syllables(args.root):
        print(f"warning: no syllable edition for {name} "
              "(run utilities/make_syllables.py)", file=sys.stderr)

    vid, text = build_release(args.root)
    dest = args.root / "releases" / f"{vid}.cex"
    if dest.exists() and not args.force:
        sys.exit(f"{dest} already exists; use --force to overwrite")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
