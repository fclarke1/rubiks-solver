"""Command-line interface for the rubiks package.

Three subcommands:
    rubiks scramble [-n N] [--seed S]
    rubiks show "<move sequence>"
    rubiks solve "<move sequence>"

Run with:
    uv run python -m rubiks scramble -n 10 --show
    uv run python -m rubiks show "R U R' U'"
"""

from __future__ import annotations

import argparse
import sys

from rubiks.cube.moves import ALL_MOVES, Move
from rubiks.cube.scramble import scramble
from rubiks.cube.state import CubeState
from rubiks.viz.ansi_net import render
from rubiks.solver.ida_star import IDAStar
from rubiks.solver.heuristic import ZeroHeuristic, PoorCornerEdgeHeuristic

_MOVES_BY_NAME: dict[str, Move] = {m.name: m for m in ALL_MOVES}


def parse_moves(s: str) -> list[Move]:
    """Parse a comma/space-separated move sequence like "R,U,R',U',F2".
    """
    s = s.replace(" ", ",")
    tokens = s.split(',')
    moves: list[Move] = []
    for tok in tokens:
        if tok not in _MOVES_BY_NAME:
            raise ValueError(
                f"Unknown move {tok!r}. Valid moves are: "
                f"{', '.join(sorted(_MOVES_BY_NAME))}"
            )
        moves.append(_MOVES_BY_NAME[tok])
    return moves

# ----- subcommand handlers -----
#
# Each handler takes the parsed argparse.Namespace and either prints to stdout
# or raises SystemExit on user error


def cmd_scramble(args: argparse.Namespace) -> None:
    """Generate a random scramble. Print the move sequence; optionally render
    the resulting cube state if --show was passed.
    """
    scramble_moves = scramble(args.n, seed=args.seed)
    solved = CubeState.solved()
    scramble_state = solved.apply_moves(scramble_moves)
    
    move_list = (m.name for m in scramble_moves)
    move_string = " ".join(move_list)
    print(f"Moves: {move_string}")
    print(render(scramble_state))



def cmd_show(args: argparse.Namespace) -> None:
    """Apply a move sequence to a solved cube and render the result."""
    moves = parse_moves(args.moves)
    solved = CubeState.solved()
    scramble_state = solved.apply_moves(moves)
    moves_string = args.moves.replace(",", " ")
    print(f"Moves: {moves_string}")
    print(render(scramble_state))


def cmd_solve(args: argparse.Namespace) -> None:
    """Solve a cube produced by applying a move sequence to a solved cube.
    Placeholder until the solver lands."""
    moves = parse_moves(args.moves)
    solved = CubeState.solved()
    scramble_state = solved.apply_moves(moves)
    moves_string = args.moves.replace(",", " ")
    print(f"Scrambled Cube: {moves_string}")
    print(render(scramble_state))

    if args.heuristic == "zero":
        heuristic = ZeroHeuristic
    elif args.heuristic == "poor":
        heuristic = PoorCornerEdgeHeuristic
    else:
        raise TypeError(f"heuristic {args.heuristic} not recognized")

    solver = IDAStar(heuristic())
    unscramble_moves = solver.solve(scramble_state)
    unscramble_move_list = (m.name for m in unscramble_moves)
    unscramble_move_string = " ".join(unscramble_move_list)
    unscramble_state = scramble_state.apply_moves(unscramble_moves)
    print(f"\n\n\nUnscramble Moves: {unscramble_move_string}")
    print(render(unscramble_state))


# ----- argparse setup -----


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubiks",
        description="A 3x3 Rubik's cube solver and toolkit",
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    p_scramble = sub.add_parser("scramble", help="Generate a random scramble")
    p_scramble.add_argument("-n", type=int, default=20, help="Number of moves (default: 20).")
    p_scramble.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility.")
    p_scramble.set_defaults(func=cmd_scramble)

    p_show = sub.add_parser("show", help="Render the cube after a move sequence")
    p_show.add_argument("moves", help='comma-separated, e.g. "R,U,R\',U\',F2"')
    p_show.set_defaults(func=cmd_show)

    p_solve = sub.add_parser("solve", help="Solve a scrambled cube")
    p_solve.add_argument("moves", type=str, help='comma-seperated moves to solve, e.g. "R,U,R\',U\'"')
    p_solve.add_argument("--heuristic", type=str, help='heuristic used to complete solve, default=poor', choices=("zero", "poor"), default="zero")
    p_solve.set_defaults(func=cmd_solve)

    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse args and dispatch to the right handler. Catches user-facing errors
    (ValueError) and exits with a useful message instead of a stack trace."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
