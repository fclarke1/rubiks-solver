from itertools import permutations
import pytest
import random
import math

from rubiks.cube.moves import ALL_MOVES
from rubiks.cube.pack import pack_orientation, unpack_orientation, rank_permutation, unrank_permutation, pack_state, unpack_state, rank_corners, unrank_corners, unrank_slice, rank_slice, SLICE_RANK_COUNT
from rubiks.cube.state import CubeState, EDGE_COUNT, EDGE_BASE, CORNER_BASE, CORNER_COUNT, IS_SLICE_EDGE


@pytest.mark.parametrize("seed", range(10))
def test_pack_orientation(seed: int):
    rng = random.Random(seed)

    co_state = tuple(rng.choice(range(CORNER_BASE)) for _ in range(CORNER_COUNT))
    eo_state = tuple(rng.choice(range(EDGE_BASE)) for _ in range(EDGE_COUNT))

    co_pack = pack_orientation(co_state, CORNER_BASE)
    co_unpack = unpack_orientation(co_pack, CORNER_COUNT, CORNER_BASE)
    eo_pack = pack_orientation(eo_state, EDGE_BASE)
    eo_unpack = unpack_orientation(eo_pack, EDGE_COUNT, EDGE_BASE)

    assert (eo_unpack == eo_state) and (co_unpack == co_state)


@pytest.mark.parametrize("n", range(10))
def test_rank_permutation(n:int):
    seen_ranks = set()
    for p in permutations(range(n)):
        r = rank_permutation(p)
        seen_ranks.add(r)
        assert (r >= 0) and (r < math.factorial(n))
        assert p == unrank_permutation(r, n)
    assert len(seen_ranks) == math.factorial(n)


@pytest.mark.parametrize("seed", range(10))
def test_cubestate_pack(seed:int):
    rng = random.Random(seed)
    moves = (rng.choice(ALL_MOVES) for _ in range(10))
    state = CubeState.solved()
    for m in moves:
        state = state.apply(m)
    packed_state = pack_state(state)
    unpacked_state = unpack_state(packed_state)
    assert unpacked_state == state


@pytest.mark.parametrize("seed", range(50))
def test_pack_corners(seed:int):
    rng = random.Random(seed)
    moves = (rng.choice(ALL_MOVES) for _ in range(10))
    state = CubeState.solved()
    for m in moves:
        state = state.apply(m)
    ranked_corners = rank_corners(state)
    unranked_cp, unranked_co = unrank_corners(ranked_corners)
    assert (state.cp == unranked_cp) and (state.co == unranked_co)


@pytest.mark.parametrize("seed",range(50))
def test_unpack_corners(seed:int):
    rng = random.Random(seed)
    i = rng.randint(0,math.factorial(8))
    cp, co = unrank_corners(i)
    state = CubeState(
        cp = cp,
        co = co,
        ep = tuple(range(12)),
        eo = (0,) * 12
    )
    ranked_corners = rank_corners(state)
    assert ranked_corners == i


def _random_state(seed: int, length: int = 10) -> CubeState:
    rng = random.Random(seed)
    moves = [rng.choice(ALL_MOVES) for _ in range(length)]
    return CubeState.solved().apply_moves(moves)


def _slice_slots(ep: tuple[int, ...]) -> tuple[int, ...]:
    """The slots holding slice edges — the only thing rank_slice looks at."""
    return tuple(slot for slot, cubie in enumerate(ep) if IS_SLICE_EDGE[cubie])


@pytest.mark.parametrize("rank", range(SLICE_RANK_COUNT))
def test_slice_unranking(rank: int):
    """Exhaustive: every one of the 495 ranks survives a round trip.
    """
    assert rank == rank_slice(unrank_slice(rank))


@pytest.mark.parametrize("seed", range(50))
def test_slice_ranking(seed: int):
    """A real state ranks in range, and unranking recovers its slice slots.
    """
    state = _random_state(seed)
    rank = rank_slice(state.ep)

    assert 0 <= rank < SLICE_RANK_COUNT
    assert _slice_slots(state.ep) == _slice_slots(unrank_slice(rank))


def test_solved_rank_slice():
    """Slice edges in slots 8..11 is the LAST 4-subset in colex order."""
    assert rank_slice(CubeState.solved().ep) == SLICE_RANK_COUNT - 1 == 494


@pytest.mark.parametrize("seed", range(50))
def test_slice_rank_ignores_order(seed: int):
    """Shuffling cubies within their own group must not change the rank.
    """
    rng = random.Random(seed)
    state = _random_state(seed)

    slice_slots = list(_slice_slots(state.ep))
    other_slots = [s for s in range(EDGE_COUNT) if s not in set(slice_slots)]

    shuffled = list(state.ep)
    for slots in (slice_slots, other_slots):
        cubies = [state.ep[s] for s in slots]
        rng.shuffle(cubies)
        for slot, cubie in zip(slots, cubies):
            shuffled[slot] = cubie

    assert rank_slice(tuple(shuffled)) == rank_slice(state.ep)