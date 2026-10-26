"""Ptolemy's tunings: tetrachord divisions, the Perfect System, and the
seven tonoi of *Harmonics* Book II.

Ratios are exact ``Fraction``s; frequencies are derived from them.

**Divisions.** Each of Ptolemy's eight divisions of the tetrachord is three
superparticular (or Pythagorean) intervals, listed low to high, whose
product is 4:3.

**Perfect System.** Two octaves from proslambanomenos (A) to nete
hyperbolaion (a′), built from a tone plus two pairs of conjunct
tetrachords separated by the disjunctive tone, with the synemmenon
tetrachord (conjunct above mese) as an alternative. Degrees repeat at the
octave every 7 steps.

**Tonoi.** Ptolemy keeps the central octave of the instrument fixed
(thetic hypate meson to thetic nete diezeugmenon) and retunes its strings
so that each tonos gives it a different octave species. A tonos is
identified by where its dynamic mese falls in that octave (see
``data/ptolemy_tonoi.cex``). Dorian is the tonos in which thetic and
dynamic names coincide. Tonos ``order`` k (0 = Hypodorian ... 6 =
Mixolydian) shifts dynamic degrees by ``3 - k`` steps against thetic ones.
"""

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from importlib import resources
from math import log2

FOURTH = F(4, 3)
TONE = F(9, 8)


@dataclass(frozen=True)
class Division:
    """A division of the tetrachord: three intervals, low to high."""
    key: str
    name: str
    genus: str
    intervals: tuple

    def __post_init__(self):
        product = self.intervals[0] * self.intervals[1] * self.intervals[2]
        if product != FOURTH:
            raise ValueError(f"{self.key}: intervals multiply to {product}, not 4/3")

    @property
    def cents(self):
        return tuple(1200 * log2(i) for i in self.intervals)


DIVISIONS = {d.key: d for d in (
    Division("enharmonic", "Enharmonic", "enharmonic", (F(46, 45), F(24, 23), F(5, 4))),
    Division("soft_chromatic", "Soft chromatic", "chromatic", (F(28, 27), F(15, 14), F(6, 5))),
    Division("tense_chromatic", "Tense chromatic", "chromatic", (F(22, 21), F(12, 11), F(7, 6))),
    Division("soft_diatonic", "Soft diatonic", "diatonic", (F(21, 20), F(10, 9), F(8, 7))),
    Division("tonic_diatonic", "Tonic diatonic", "diatonic", (F(28, 27), F(8, 7), F(9, 8))),
    Division("ditonic_diatonic", "Ditonic diatonic", "diatonic", (F(256, 243), F(9, 8), F(9, 8))),
    Division("tense_diatonic", "Tense diatonic", "diatonic", (F(16, 15), F(9, 8), F(10, 9))),
    Division("even_diatonic", "Even diatonic", "diatonic", (F(12, 11), F(11, 10), F(10, 9))),
)}

# Perfect System degrees, low to high (index 0-14)
DEGREES = (
    "proslambanomenos",
    "hypate hypaton", "parhypate hypaton", "lichanos hypaton",
    "hypate meson", "parhypate meson", "lichanos meson",
    "mese",
    "paramese", "trite diezeugmenon", "paranete diezeugmenon", "nete diezeugmenon",
    "trite hyperbolaion", "paranete hyperbolaion", "nete hyperbolaion",
)
SYNEMMENON = ("trite synemmenon", "paranete synemmenon", "nete synemmenon")
CENTRAL_OCTAVE = DEGREES[4:12]          # thetic hypate meson .. nete diezeugmenon
_HYPATE_MESON = DEGREES.index("hypate meson")
_MESE = DEGREES.index("mese")


def _division(division):
    if isinstance(division, Division):
        return division
    try:
        return DIVISIONS[division]
    except KeyError:
        raise ValueError(f"Unknown division {division!r}; "
                         f"choose from {', '.join(DIVISIONS)}") from None


def _degree_index(name):
    try:
        return DEGREES.index(name)
    except ValueError:
        raise ValueError(f"Unknown degree {name!r}") from None


def step_ratio(division, index: int) -> F:
    """Ratio of Perfect System degree ``index`` to proslambanomenos.

    Any integer index is allowed; the system repeats at the octave every
    7 steps (index 7 = mese = 2/1, index 14 = nete hyperbolaion = 4/1).
    """
    a, b, c = _division(division).intervals
    octave, i = divmod(index, 7)
    base = (F(1), TONE, TONE * a, TONE * a * b,
            TONE * FOURTH, TONE * FOURTH * a, TONE * FOURTH * a * b)[i]
    return base * F(2) ** octave


def system_ratios(division) -> dict:
    """Ratios to proslambanomenos of every degree, including synemmenon."""
    d = _division(division)
    ratios = {name: step_ratio(d, i) for i, name in enumerate(DEGREES)}
    a, b, _ = d.intervals
    mese = ratios["mese"]
    ratios.update(zip(SYNEMMENON, (mese * a, mese * a * b, mese * FOURTH)))
    return ratios


@dataclass(frozen=True)
class Tonos:
    name: str
    order: int              # 0 = Hypodorian ... 6 = Mixolydian
    thetic_mese: str        # thetic degree on which the dynamic mese falls
    species: str

    @property
    def shift(self) -> int:
        """Dynamic degree index minus thetic degree index."""
        return 3 - self.order


@lru_cache(maxsize=None)
def load_tonoi() -> dict:
    """Ptolemy's seven tonoi, keyed by lower-case name."""
    text = (resources.files("mousike").joinpath("data/ptolemy_tonoi.cex")
            .read_text(encoding="utf-8"))
    tonoi = {}
    for line in text.splitlines()[1:]:
        if line.strip():
            name, order, mese, species = (c.strip() for c in line.split("|"))
            t = Tonos(name, int(order), mese, species)
            if _degree_index(mese) + t.shift != _MESE:
                raise ValueError(f"Inconsistent tonos table entry: {line}")
            tonoi[name.lower()] = t
    return tonoi


def tonos(name) -> Tonos:
    if isinstance(name, Tonos):
        return name
    try:
        return load_tonoi()[name.lower()]
    except KeyError:
        raise ValueError(f"Unknown tonos {name!r}; choose from "
                         f"{', '.join(t.name for t in load_tonoi().values())}") from None


class PtolemaicSystem:
    """A tonos in one of Ptolemy's divisions, at a fixed pitch.

    The thetic hypate meson (bottom of the fixed central octave) sounds at
    ``hypate_meson_hz``. The default, 165 Hz, puts Dorian mese at 220 Hz,
    matching ``NominalTuning``'s vocal a.

    >>> s = PtolemaicSystem("tense_diatonic", "dorian")
    >>> [str(r) for r in s.central_octave().values()]
    ['1', '16/15', '6/5', '4/3', '3/2', '8/5', '9/5', '2']
    """

    def __init__(self, division="tense_diatonic", tonos_name="dorian",
                 hypate_meson_hz: float = 165.0):
        self.division = _division(division)
        self.tonos = tonos(tonos_name)
        self.hypate_meson_hz = hypate_meson_hz
        # dynamic ratio sounding on the thetic hypate meson string
        self._anchor = step_ratio(self.division, _HYPATE_MESON + self.tonos.shift)

    # --- ratios relative to thetic hypate meson -------------------------

    def _dynamic_index_ratio(self, index: int) -> F:
        return step_ratio(self.division, index) / self._anchor

    def dynamic_ratio(self, name: str) -> F:
        """Ratio of a dynamic degree (incl. synemmenon) to thetic hypate meson."""
        if name in SYNEMMENON:
            return system_ratios(self.division)[name] / self._anchor
        return self._dynamic_index_ratio(_degree_index(name))

    def thetic_ratio(self, name: str) -> F:
        """Ratio of the string at thetic position ``name`` to thetic hypate meson."""
        return self.thetic_index_ratio(_degree_index(name))

    def thetic_index_ratio(self, index: int) -> F:
        """Like ``thetic_ratio``, by Perfect System index (0 = proslambanomenos).
        Indexes outside 0-14 continue the system by octaves."""
        return self._dynamic_index_ratio(index + self.tonos.shift)

    def dynamic_name(self, thetic_name: str):
        """Dynamic degree sounding at a thetic position (``None`` if it falls
        outside the two-octave system)."""
        i = _degree_index(thetic_name) + self.tonos.shift
        return DEGREES[i] if 0 <= i < len(DEGREES) else None

    def central_octave(self) -> dict:
        """Thetic degree name -> ratio, for the fixed central octave."""
        return {n: self.thetic_ratio(n) for n in CENTRAL_OCTAVE}

    # --- frequencies ----------------------------------------------------

    def dynamic_frequency(self, name: str) -> float:
        return self.hypate_meson_hz * float(self.dynamic_ratio(name))

    def thetic_frequency(self, name: str) -> float:
        return self.hypate_meson_hz * float(self.thetic_ratio(name))

    def __repr__(self):
        return (f"PtolemaicSystem({self.division.key!r}, {self.tonos.name!r}, "
                f"hypate_meson_hz={self.hypate_meson_hz})")
