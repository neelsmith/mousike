"""Read ancient Greek musical notation in Zach Sowerby's notational scheme."""

from .note import Note, load_table, parse_note_groups, parse_notes
from .unicode import (groups_to_unicode, load_pitch_table, note_to_unicode,
                      notes_to_unicode)
from .syllabify import syllabify, syllabify_word
from .align import (AlignedPassage, AlignedSyllable, AlignmentError,
                    align_editions, align_passage)

__all__ = [
    "Note", "load_table", "parse_note_groups", "parse_notes",
    "groups_to_unicode", "load_pitch_table", "note_to_unicode",
    "notes_to_unicode",
    "syllabify", "syllabify_word",
    "AlignedPassage", "AlignedSyllable", "AlignmentError",
    "align_editions", "align_passage",
]
