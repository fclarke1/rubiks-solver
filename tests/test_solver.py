import pytest
import random

from rubiks.solver.ida_star import IDAStar
from rubiks.solver.heuristic import ZeroHeuristic
from rubiks.cube.state import CubeState
from rubiks.cube.moves import ALL_MOVES

@pytest.mark.parametrize("depth", range(5))
def test_solver(depth:int, seed:int=105):
    rng = random.Random(seed)
    solved = CubeState.solved()
    moves = (rng.choice(ALL_MOVES) for _ in range(depth))
    scramble_state = solved.apply_moves(moves)
    solver = IDAStar(ZeroHeuristic())
    solve_moves = solver.solve(scramble_state)
    unscramble_state = scramble_state.apply_moves(solve_moves)
    assert unscramble_state == solved