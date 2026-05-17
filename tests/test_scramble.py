from typing import TYPE_CHECKING
from rubiks.cube.scramble import scramble
from rubiks.cube.moves import Move

def test_scramble_length():
    length = 20
    scramble_moves = scramble(length, 104)
    assert length == len(scramble_moves)
    assert all(isinstance(m, Move) for m in scramble_moves)