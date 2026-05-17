import random
from rubiks.cube.moves import ALL_MOVES, Move
from rubiks.cube.state import CubeState


def scramble(length:int, seed:int|None = 42) -> list[Move]:
    if length <= 0:
        raise ValueError(f"scramble length must be positive integer, got {length}")
    rng = random.Random(seed)
    scramble_moves = [rng.choice(ALL_MOVES)]
    for i in range(length-1):
        prev_move = scramble_moves[-1]
        next_move = rng.choice(ALL_MOVES)
        # Don't allow applying the same type of move, eg. X and then X' or X2
        while next_move.name[0]==prev_move.name[0]:
            next_move = rng.choice(ALL_MOVES)
        scramble_moves.append(next_move)
    return scramble_moves