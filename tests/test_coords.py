"""Tests for the two-phase coordinates and their move tables.

Every test is parametrised over the coordinate registry, so all six get the
same treatment and a new coordinate is covered the moment it is registered.

Order to make them pass: the coordinate functions first (test_solved_*), then
the representatives (test_representative_round_trip), then build_move_table —
the table tests can't say anything useful until the first two are right.
"""

import random

import pytest

from rubiks.cube.moves import G1_MOVES, inverse
from rubiks.cube.state import CubeState
from rubiks.solver.coords import (
    ALL_COORDS,
    PHASE1_COORDS,
    PHASE1_GOAL,
    PHASE2_COORDS,
    PHASE2_GOAL,
    Coordinate,
    move_table,
)

_IDS = lambda c: c.name


def _random_state(coordinate: Coordinate, seed: int, length: int = 15) -> CubeState:
    """A random state that the coordinate is actually defined on.
    """
    rng = random.Random(seed)
    return CubeState.solved().apply_moves(
        [rng.choice(coordinate.moves) for _ in range(length)]
    )


# ----- coordinate functions -----


def test_solved_phase1_coords():
    """Phase 1 aims here. Note the slice goal is 494, not 0."""
    solved = CubeState.solved()
    assert tuple(c.coord(solved) for c in PHASE1_COORDS) == PHASE1_GOAL


def test_solved_phase2_coords():
    """Phase 2 aims here, and reaching it means genuinely solved."""
    solved = CubeState.solved()
    assert tuple(c.coord(solved) for c in PHASE2_COORDS) == PHASE2_GOAL


@pytest.mark.parametrize("coordinate", ALL_COORDS, ids=_IDS)
@pytest.mark.parametrize("seed", range(20))
def test_coord_in_range(coordinate: Coordinate, seed: int):
    state = _random_state(coordinate, seed)
    assert 0 <= coordinate.coord(state) < coordinate.size


@pytest.mark.parametrize("coordinate", ALL_COORDS, ids=_IDS)
def test_representative_round_trip(coordinate: Coordinate):
    """coord(representative(i)) == i for every i.
    """
    if coordinate.size <= 2_200:
        values = range(coordinate.size)
    else:
        rng = random.Random(coordinate.size)
        values = [0, coordinate.size - 1] + [
            rng.randrange(coordinate.size) for _ in range(300)
        ]

    for i in values:
        assert coordinate.coord(coordinate.representative(i)) == i


# ----- move tables -----


@pytest.mark.parametrize("coordinate", ALL_COORDS, ids=_IDS)
def test_table_shape_and_range(coordinate: Coordinate):
    table = move_table(coordinate)
    assert len(table) == coordinate.size
    for row in table:
        assert len(row) == len(coordinate.moves)
        assert all(0 <= v < coordinate.size for v in row)


@pytest.mark.parametrize("coordinate", ALL_COORDS, ids=_IDS)
@pytest.mark.parametrize("seed", range(20))
def test_table_matches_the_real_cube(coordinate: Coordinate, seed: int):
    """The test that actually validates the table.
    """
    state = _random_state(coordinate, seed)
    table = move_table(coordinate)
    before = coordinate.coord(state)

    for move_index, move in enumerate(coordinate.moves):
        assert table[before][move_index] == coordinate.coord(state.apply(move))


@pytest.mark.parametrize("coordinate", ALL_COORDS, ids=_IDS)
def test_each_move_column_is_a_permutation(coordinate: Coordinate):
    """A move is invertible, so its column must hit every coordinate exactly once.
    """
    table = move_table(coordinate)
    for move_index in range(len(coordinate.moves)):
        column = sorted(row[move_index] for row in table)
        assert column == list(range(coordinate.size))


@pytest.mark.parametrize("coordinate", ALL_COORDS, ids=_IDS)
@pytest.mark.parametrize("seed", range(20))
def test_move_then_inverse_returns_to_start(coordinate: Coordinate, seed: int):
    """table[table[c][m]][inv(m)] == c — the same invariant as the cube-level
    test, one level of abstraction up.
    """
    inverse_index = {
        move.name: coordinate.moves.index(inverse(move)) for move in coordinate.moves
    }
    table = move_table(coordinate)
    rng = random.Random(seed)
    start = rng.randrange(coordinate.size)

    for move_index, move in enumerate(coordinate.moves):
        after = table[start][move_index]
        assert table[after][inverse_index[move.name]] == start