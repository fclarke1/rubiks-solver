"""Property tests for the cube model.

Each test states an invariant that must hold for ANY cube state and ANY
well-formed move sequence. When a property fails, your move tables or
apply() logic are wrong — the test won't tell you which, but a failing
test on a single move usually points straight at that move's definition.
"""

import pytest
import random

from rubiks.cube.moves import ALL_MOVES, BASE_MOVES_DICT, G1_MOVES, inverse, compose
from rubiks.cube.pack import rank_slice, SLICE_RANK_COUNT
from rubiks.cube.state import CORNER_COUNT, EDGE_COUNT, CubeState


@pytest.mark.parametrize("move", ALL_MOVES, ids=lambda m: m.name)
def test_move_then_inverse_returns_to_solved(move):
    """Applying a move, then its inverse, must return the solved state.
    """
    solved = CubeState.solved()
    after_move = solved.apply(move)
    after_inverse = after_move.apply(inverse(move))
    assert after_inverse == solved


def test_sexy_move_test():
    """Famous combination of moves R U R' U' applied 6 times is the identity
    """
    R = BASE_MOVES_DICT['R']
    U = BASE_MOVES_DICT['U']
    R_inverse = inverse(R)
    U_inverse = inverse(U)
    sexy_move = compose(compose(R, U, 'first_combo'), compose(R_inverse, U_inverse, 'second_combo'), 'sexy')
    result = CubeState.solved()
    for _ in range(6):
        result = result.apply(sexy_move)
    assert result == CubeState.solved()


@pytest.mark.parametrize("seed", range(20))
def test_random_walk_reverse(seed:int):
    rng = random.Random(seed)
    walk_moves = tuple(rng.choice(ALL_MOVES) for i in range(50))
    state = CubeState.solved()
    for m in walk_moves:
        state = state.apply(m)
    for m in reversed(walk_moves):
        state = state.apply(inverse(m))
    assert state == CubeState.solved()