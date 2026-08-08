"""Coordinates and move tables for the two-phase (Kociemba) solver.

A COORDINATE is a lossy projection of a CubeState onto a small integer. A MOVE
TABLE says how each move acts on that integer:

    table[coordinate][move_index] -> new coordinate

Once the tables exist the search never touches a CubeState again. A phase-1
node is three ints, and generating a successor is three array lookups instead
of allocating a new 40-element state. That is where the speed comes from.

Why a table can exist at all
----------------------------
For every coordinate below, the new value depends ONLY on the old value and
the move — never on the rest of the cube. Check each against CubeState.apply
before you trust it:

    corner orientation  new_co[i] = (co[cp_perm[i]] + co_delta[i]) % 3
                        reads co and the move; the state's cp never appears
    edge orientation    same argument with eo and ep_perm
    slice               a move permutes SLOTS, so the set of slice-occupied
                        slots afterwards depends only on the set before
    corner permutation  new_cp[i] = cp[cp_perm[i]] — pure composition
    ud / slice perm     G1 moves never carry an edge across the slice
                        boundary, so slots 0..7 and 8..11 evolve separately

That independence is what lets the builder pick ANY representative state with
the right coordinate, apply the move with the well-tested CubeState.apply, and
re-rank the result.

The two phases
--------------
Phase 1 (all 18 moves) drives (corner_ori, edge_ori, slice) to PHASE1_GOAL.
Reaching it means the cube is in G1 — NOT that it is nearly solved. Every
cubie may still be misplaced; only orientations and slice membership are
fixed.

Phase 2 (10 G1 moves) drives (corner_perm, ud_edge_perm, slice_perm) to
PHASE2_GOAL. These three are a complete description of a G1 state, so reaching
(0, 0, 0) means genuinely solved.

Note the asymmetry: phase 1's coordinates are lossy (2.2 billion classes over
4.3e19 states — each class is one coset of G1), phase 2's are lossless within
G1. You cannot compute phase-2 coordinates from phase-1 coordinates: apply the
phase-1 solution to the real CubeState and project that instead.

THE TRAP: never index a phase-2 table with a non-G1 move. ud_edge_perm_coord
assumes the eight non-slice edges sit in slots 0..7; an F breaks that and the
number you get back is meaningless rather than merely wrong. Coordinate.moves
records which move set each table was built against — use it.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import factorial
from typing import Callable

from rubiks.cube.moves import ALL_MOVES, G1_MOVES, Move
from rubiks.cube.pack import (
    SLICE_RANK_COUNT,
    pack_orientation,
    rank_corners,
    rank_permutation,
    rank_slice,
    unpack_orientation,
    unrank_permutation,
    unrank_slice,
)
from rubiks.cube.state import (
    CORNER_BASE,
    CORNER_COUNT,
    EDGE_BASE,
    EDGE_COUNT,
    SLICE_COUNT,
    SLICE_EDGES,
    CubeState,
)

# Move ordering is load-bearing: a table cell means "move at THIS index", so
# reordering either tuple silently invalidates every table ever built.
PHASE1_MOVES: tuple[Move, ...] = ALL_MOVES
PHASE2_MOVES: tuple[Move, ...] = G1_MOVES

# Coordinate space sizes.
CORNER_ORI_SIZE = CORNER_BASE ** (CORNER_COUNT - 1)      # 2_187
EDGE_ORI_SIZE = EDGE_BASE ** (EDGE_COUNT - 1)            # 2_048
SLICE_SIZE = SLICE_RANK_COUNT                            # 495
CORNER_PERM_SIZE = factorial(CORNER_COUNT)               # 40_320
UD_EDGE_PERM_SIZE = factorial(EDGE_COUNT - SLICE_COUNT)  # 40_320
SLICE_PERM_SIZE = factorial(SLICE_COUNT)                 # 24


# ----- coordinate functions: CubeState -> int -----


def corner_ori_coord(state: CubeState) -> int:
    """Corner orientation, 0..2186.

    The 8th twist is implied by the other 7 (they sum to 0 mod 3), so this is
    just the first seven digits packed in base 3. pack_orientation does it.
    """
    return pack_orientation(state.co[:-1], 3)


def edge_ori_coord(state: CubeState) -> int:
    """Edge orientation, 0..2047. Same idea, 11 digits in base 2."""
    return pack_orientation(state.eo[:-1], 2)


def slice_coord(state: CubeState) -> int:
    """Which slots hold the four slice edges, 0..494. rank_slice does it."""
    return rank_slice(state.ep)


def corner_perm_coord(state: CubeState) -> int:
    """Corner permutation, 0..40319. A plain Lehmer rank of cp."""
    return rank_permutation(state.cp)


def ud_edge_perm_coord(state: CubeState) -> int:
    """Order of the eight non-slice edges, 0..40319.

    ONLY meaningful for a G1 state, where cubies 0..7 are guaranteed to occupy
    slots 0..7. Lehmer-rank that eight-element slice of ep.
    """
    return rank_permutation(state.ep[:SLICE_EDGES[0]])


def slice_perm_coord(state: CubeState) -> int:
    """Order of the four slice edges among themselves, 0..23.

    Also G1-only. The cubies are numbered 8..11, so subtract SLICE_EDGES[0] to
    get a permutation of range(4) before ranking.
    """
    return rank_permutation(tuple(c - SLICE_EDGES[0] for c in state.ep[SLICE_EDGES[0]:]))



# ----- representatives: int -> some CubeState with that coordinate -----
#
# Each builds the canonical member of the coordinate's equivalence class: the
# projected component carries the information, every other component is left
# solved. Any representative would do (see the module docstring), so pick the
# one that is easiest to check by eye.


def corner_ori_representative(coord: int) -> CubeState:
    """Unpack 7 base-3 digits, recover the 8th from -sum % 3, rest solved."""
    raise NotImplementedError


def edge_ori_representative(coord: int) -> CubeState:
    """Unpack 11 base-2 digits, recover the 12th from -sum % 2, rest solved."""
    raise NotImplementedError


def slice_representative(coord: int) -> CubeState:
    """unrank_slice already returns a representative ep. Rest solved."""
    raise NotImplementedError


def corner_perm_representative(coord: int) -> CubeState:
    """unrank_permutation into cp. Rest solved."""
    raise NotImplementedError


def ud_edge_perm_representative(coord: int) -> CubeState:
    """Unrank a permutation of range(8) into ep[:8]; slice edges stay home."""
    raise NotImplementedError


def slice_perm_representative(coord: int) -> CubeState:
    """Unrank a permutation of range(4), add SLICE_EDGES[0], put it in ep[8:].

    Non-slice edges stay in slots 0..7 in order.
    """
    raise NotImplementedError


# ----- the registry -----


@dataclass(frozen=True, slots=True)
class Coordinate:
    """Everything needed to build and use one move table.

    Bundling these means the builder and the tests are written once and
    parametrised over six coordinates, rather than copy-pasted six times.
    """

    name: str
    size: int
    moves: tuple[Move, ...]
    coord: Callable[[CubeState], int]
    representative: Callable[[int], CubeState]


CORNER_ORI = Coordinate(
    "corner_ori", CORNER_ORI_SIZE, PHASE1_MOVES, corner_ori_coord, corner_ori_representative
)
EDGE_ORI = Coordinate(
    "edge_ori", EDGE_ORI_SIZE, PHASE1_MOVES, edge_ori_coord, edge_ori_representative
)
SLICE = Coordinate(
    "slice", SLICE_SIZE, PHASE1_MOVES, slice_coord, slice_representative
)
CORNER_PERM = Coordinate(
    "corner_perm", CORNER_PERM_SIZE, PHASE2_MOVES, corner_perm_coord, corner_perm_representative
)
UD_EDGE_PERM = Coordinate(
    "ud_edge_perm", UD_EDGE_PERM_SIZE, PHASE2_MOVES, ud_edge_perm_coord, ud_edge_perm_representative
)
SLICE_PERM = Coordinate(
    "slice_perm", SLICE_PERM_SIZE, PHASE2_MOVES, slice_perm_coord, slice_perm_representative
)

PHASE1_COORDS: tuple[Coordinate, ...] = (CORNER_ORI, EDGE_ORI, SLICE)
PHASE2_COORDS: tuple[Coordinate, ...] = (CORNER_PERM, UD_EDGE_PERM, SLICE_PERM)
ALL_COORDS: tuple[Coordinate, ...] = PHASE1_COORDS + PHASE2_COORDS

# The targets each phase searches towards. Phase 1's slice goal is the LAST
# combination index, not 0 — the slice edges sit in the highest four slots.
PHASE1_GOAL: tuple[int, ...] = (0, 0, SLICE_SIZE - 1)
PHASE2_GOAL: tuple[int, ...] = (0, 0, 0)


# ----- table construction -----


def build_move_table(coordinate: Coordinate) -> tuple[tuple[int, ...], ...]:
    """Build one move table: rows are coordinates, columns are moves.

    For each coordinate value, build its representative ONCE, then apply every
    move to it and re-project. Coordinate outer, move inner — the other way
    round means unranking 18 times as often for no reason.

    Roughly 84_000 cells across all six tables, so a few seconds total. Measure
    before optimising; if it becomes annoying, cache to data/ the way the
    pruning tables will be.
    """
    raise NotImplementedError


_TABLE_CACHE: dict[str, tuple[tuple[int, ...], ...]] = {}


def move_table(coordinate: Coordinate) -> tuple[tuple[int, ...], ...]:
    """Return the move table for `coordinate`, building it on first use.

    Lazy rather than built at import so that importing this module stays cheap
    and a half-finished coordinate doesn't break collection of every test.
    """
    if coordinate.name not in _TABLE_CACHE:
        _TABLE_CACHE[coordinate.name] = build_move_table(coordinate)
    return _TABLE_CACHE[coordinate.name]
