from rubiks.cube.state import CubeState
from rubiks.cube.scramble import scramble
from rubiks.solver.ida_star import IDAStar
from rubiks.solver.heuristic import ZeroHeuristic
from rubiks.viz.ansi_net import render


def main():
    state = CubeState.solved()
    state = state.apply_moves(scramble(4, seed=362))
    print(f"{render(state)}\n\n")


    solver = IDAStar(ZeroHeuristic())
    solve_moves = solver.solve(state)
    print(render(state.apply_moves(solve_moves)))


if __name__=="__main__":
    main()
