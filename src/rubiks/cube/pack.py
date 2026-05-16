"""Bijective encoders between cube states (or sub-states) and integers.

Two jobs:

1. Whole-state packing (pack_state / unpack_state)
   Used as a fast hash key in IDA*'s visited set. Must be lossless —
   `unpack_state(pack_state(s)) == s` for every reachable state.

2. Corner-only ranking (rank_corners / unrank_corners)
   Used as the index into the corner pattern database. Must be a tight
   bijection: every corner configuration maps to a unique integer in
   0 .. 8!·3**7 - 1 = 0 .. 88_179_839, and the inverse recovers it exactly.

Both jobs share two primitives:

  - Orientation packing: each tuple of base-N digits is one mixed-radix integer.
  - Permutation ranking: the Lehmer code / factorial number system maps any
    permutation of range(n) to an integer in 0..n!-1 and back.

If a function here is buggy, EVERYTHING downstream is wrong (visited sets miss
duplicates, PDB lookups return random values). Test ruthlessly:
    for s in random_states():
        assert unpack_state(pack_state(s)) == s
"""

from __future__ import annotations

from math import factorial

from rubiks.cube.state import CORNER_COUNT, EDGE_COUNT, CORNER_BASE, EDGE_BASE, CubeState


_3_POW_7 = 3**7
_12_FACTORIAL = factorial(12)
_2_POW_11 = 2**11

# ----- orientation packing (base-N digits ↔ integer) -----


def pack_orientation(values: tuple[int, ...], base: int) -> int:
    """Treat `values` as the digits of a number written in `base`, low-order first.

    Examples:
        pack_orientation((0, 2, 1), base=3) == 0 + 2*3 + 1*9 == 15
        pack_orientation((1, 0, 1, 1), base=2) == 1 + 0 + 4 + 8 == 13

    Used for corner orientations (base=3) and edge orientations (base=2).
    """
    result = 0
    for i, v in enumerate(values):
        result += v * (base ** i)
    return result


def unpack_orientation(packed: int, length: int, base: int) -> tuple[int, ...]:
    """Inverse of pack_orientation. Returns a tuple of `length` base-N digits."""
    result = tuple(int((packed % (base ** i)) / base ** (i-1)) for i in range(1, length + 1))
    return result


# ----- permutation ranking (Lehmer code) -----


def rank_permutation(perm: tuple[int, ...]) -> int:
    """Lehmer-rank a permutation of range(len(perm)) into 0..n!-1.
    Naive complexity is O(n^2) because of the .index lookup. For n=8 or n=12
    that's negligible; for larger n you'd use a Fenwick tree to get O(n log n).
    """
    rank = 0
    n = len(perm)
    available = list(range(n))
    for i in range(n):
        idx = available.index(perm[i])
        rank = rank * (n - i) + idx
        available.pop(idx)
    return rank


def unrank_permutation(rank: int, n: int) -> tuple[int, ...]:
    """Inverse of rank_permutation. Recover the unique permutation of range(n)
    whose Lehmer rank is `rank`
    """
    available = list(range(n))
    result: list[int] = []
    for i in range(n):
        idx, rank = divmod(rank, factorial(n - 1 - i))
        result.append(available.pop(idx))
    return tuple(result)


# ----- whole-state pack / unpack -----


def pack_state(state: CubeState) -> int:
    """Encode a full CubeState as a single non-negative integer.

    Combine the four pieces (cp, co, ep, eo) into one big int by multiplying
    by each component's size in turn. The conservation laws let you drop the
    last corner orientation (determined by the other 7) and the last edge
    orientation (determined by the other 11) — saving a few bits.
    """

    result = rank_permutation(state.cp)
    result = result * _3_POW_7 + pack_orientation(state.co[:7], 3) 
    result = result * _12_FACTORIAL + rank_permutation(state.ep)
    result = result * _2_POW_11 + pack_orientation(state.eo[:11], 2)
    return result


def unpack_state(packed: int) -> CubeState:
    """Inverse of pack_state. Recovers cp, co, ep, eo by peeling off each
    component in reverse order (// and % the corresponding base, then unrank).
    """
    result, eo_packed = divmod(packed, _2_POW_11)
    result, ep_ranked = divmod(result, _12_FACTORIAL)
    cp_ranked, co_packed = divmod(result, _3_POW_7)

    co_short = unpack_orientation(co_packed, CORNER_COUNT - 1, CORNER_BASE)
    eo_short = unpack_orientation(eo_packed, EDGE_COUNT - 1, EDGE_BASE)
    co_last = -sum(co_short) % CORNER_BASE
    eo_last = -sum(eo_short) % EDGE_BASE

    result_state = CubeState(
        cp = unrank_permutation(cp_ranked, CORNER_COUNT),
        co = co_short + (co_last,),
        ep = unrank_permutation(ep_ranked, EDGE_COUNT),
        eo = eo_short + (eo_last,)
    )
    return result_state


# ----- corner-only ranking (PDB index) -----


def rank_corners(state: CubeState) -> int:
    """Map (cp, co) → an integer in 0..8!·3^7 - 1 = 0..88_179_839.

    This is the index into the corner pattern database. Edges are ignored.
    Combine cp rank (8! choices) with the 7 free corner-orientation digits
    (3^7 choices) using the same scheme as pack_state — just the corner half.
    """
    raise NotImplementedError


def unrank_corners(index: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Inverse of rank_corners. Returns (cp, co) — orientation length 8 with
    the conservation law applied to recover the 8th digit.
    """
    raise NotImplementedError
