"""Move definitions and the 18-move move set.

A Move is a precomputed permutation + orientation delta that, when applied
to a CubeState, produces the state after the move. Moves are static, defined
ONCE at import time — never recomputed.

The 18 moves in the standard Rubik's move set:
    U, U', U2, D, D', D2, L, L', L2, R, R', R2, F, F', F2, B, B', B2

You only define the 6 clockwise quarter-turn base moves by hand. The doubles
(X2) and inverses (X') are derived by composing — once `compose()` is in.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from rubiks.cube.state import CORNER_COUNT, EDGE_COUNT


class Move(BaseModel):
    """A single move described as cubie permutations + orientation changes.

    Field shapes mirror CubeState's tuple shapes exactly.

        cp_perm[i] = index of the corner slot whose contents END UP in slot i
                     after the move (so the new state is a gather:
                     new[i] = old[perm[i]])
        co_delta[i] = orientation change to ADD (mod 3) at slot i after the gather
        ep_perm[i], eo_delta[i] — same idea for the 12 edges (mod 2)

    Convention check: this matches the gather formula in CubeState.apply().
    If you choose a "scatter" convention instead, document it and adjust apply().
    """

    model_config = ConfigDict(frozen=True)

    name: str
    cp_perm: tuple[int, ...]   # length 8
    co_delta: tuple[int, ...]  # length 8, values 0..2
    ep_perm: tuple[int, ...]   # length 12
    eo_delta: tuple[int, ...]  # length 12, values 0..1

    @model_validator(mode="after")
    def _validate_shapes(self) -> Self:
        # Allow empty tuples during scaffolding so the file imports while
        # you're still filling in the move tables. Remove this escape hatch
        # once all 6 base moves are defined.
        if not self.cp_perm and not self.ep_perm:
            return self
        if len(self.cp_perm) != CORNER_COUNT or len(self.co_delta) != CORNER_COUNT:
            raise ValueError("cp_perm and co_delta must have length 8")
        if len(self.ep_perm) != EDGE_COUNT or len(self.eo_delta) != EDGE_COUNT:
            raise ValueError("ep_perm and eo_delta must have length 12")
        if sorted(self.cp_perm) != list(range(CORNER_COUNT)):
            raise ValueError("cp_perm must be a permutation of 0..7")
        if sorted(self.ep_perm) != list(range(EDGE_COUNT)):
            raise ValueError("ep_perm must be a permutation of 0..11")
        if not all(0 <= v < 3 for v in self.co_delta):
            raise ValueError("co_delta values must be in 0..2")
        if not all(0 <= v < 2 for v in self.eo_delta):
            raise ValueError("eo_delta values must be in 0..1")
        return self


U: Move = Move(
    name="U",
    cp_perm=(3,2,1,0,4,5,6,7),
    co_delta=(0,0,0,0,0,0,0,0),
    ep_perm=(3,2,1,0,4,5,6,7,8,9,10,11),
    eo_delta=(0,0,0,0,0,0,0,0,0,0,0,0)
)
D: Move = Move(
    name="D",
    cp_perm=(0,1,2,3,7,4,5,6),
    co_delta=(0,0,0,0,0,0,0,0),
    ep_perm=(0,1,2,3,7,4,5,6,8,9,10,11),
    eo_delta=(0,0,0,0,0,0,0,0,0,0,0,0)
)
L: Move = Move(
    name="L",
    cp_perm=(0,2,5,3,4,6,1,7),
    co_delta=(0,1,2,0,0,1,2,0),
    ep_perm=(0,10,2,3,4,9,6,7,8,1,5,11),
    eo_delta=(0,0,0,0,0,0,0,0,0,0,0,0)
)
R: Move = Move(
    name="R",
    cp_perm=(7,1,2,0,3,5,6,4),
    co_delta=(2,0,0,1,2,0,0,1),
    ep_perm=(0,1,2,8,4,5,6,11,7,9,10,3),
    eo_delta=(0,0,0,0,0,0,0,0,0,0,0,0)
)
F: Move = Move(
    name="F",
    cp_perm=(1,6,2,3,4,5,7,0),
    co_delta=(1,2,0,0,0,0,1,2),
    ep_perm=(9,1,2,3,4,5,8,7,0,6,10,11),
    eo_delta=(1,0,0,0,0,0,1,0,1,1,0,0)
)
B: Move = Move(
    name="B",
    cp_perm=(0,1,3,4,5,2,6,7),
    co_delta=(0,0,1,2,1,2,0,0),
    ep_perm=(0,1,11,3,10,5,6,7,8,9,2,4),
    eo_delta=(0,0,1,0,1,0,0,0,0,0,1,1)
)


BASE_MOVES: tuple[Move, ...] = (U, D, L, R, F, B)
BASE_MOVES_DICT = {m.name: m for m in BASE_MOVES}


def compose(first: Move, second: Move, name: str) -> Move:
    """Return a move equivalent to applying `first` then `second`.

    Used to derive X2 (= compose(X, X, 'X2')) and X' (= compose(X, X2, "X'")).

    Composition rule (matches the gather convention in CubeState.apply):
        result.cp_perm[i]  = first.cp_perm[second.cp_perm[i]]
        result.co_delta[i] = (first.co_delta[second.cp_perm[i]] + second.co_delta[i]) % 3
        ... (and the analogous edges with mod 2)
    """
    result = Move(
        name = name,
        cp_perm =   tuple(first.cp_perm[second.cp_perm[i]] for i in range(CORNER_COUNT)),
        co_delta =  tuple((first.co_delta[second.cp_perm[i]] + second.co_delta[i]) % 3 for i in range(CORNER_COUNT)),
        ep_perm =   tuple(first.ep_perm[second.ep_perm[i]] for i in range(EDGE_COUNT)),
        eo_delta =  tuple((first.eo_delta[second.ep_perm[i]] + second.eo_delta[i]) % 2 for i in range(EDGE_COUNT))
    )
    return result


def inverse(move: Move) -> Move:
    """Return the move that undoes `move`.

    The inverse of a clockwise quarter-turn is the same face turned three
    times (equivalently, an anticlockwise quarter-turn). The inverse of a
    half-turn is itself.
    """
    name = move.name
    if name in list(BASE_MOVES_DICT.keys()):
        inverse_move = compose(compose(move, move, move.name + '2'), move, name + "'")
    elif name[-1] == "'":
        inverse_move = BASE_MOVES_DICT[name[0]]
    elif name[-1] == "2":
        inverse_move = move
    else:
        raise TypeError 
    return inverse_move


# Populate once compose() and inverse() are implemented. Convention: order is
# (X, X', X2) for each face, giving 18 moves total.
ALL_MOVES: tuple[Move, ...] = tuple(
    new_m
    for base_m in BASE_MOVES
    for new_m in (base_m, inverse(base_m), compose(base_m, base_m, base_m.name + '2'))
)