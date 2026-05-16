"""Cube state: the data model.

A 3x3 cube state is encoded as four small tuples — one per cubie property.
Cubie-based representation is dramatically smaller than facelet-based
(54 stickers) and makes move application a sequence of array gathers.
See plan section "Moves as lookup tables".

Conventions you need to nail down BEFORE filling in moves.py:
    - Numbering of the 8 corners (0..7). Pick an order and write it here.
        0 - UFR
        1 - UFL
        2 - UBL
        3 - UBR
        4 - DBR
        5 - DBL
        6 - DFL
        7 - DFR
    - Numbering of the 12 edges (0..11). Same.
        0 - UF
        1 - UL
        2 - UB
        3 - UR
        4 - DB
        5 - DL
        6 - DF
        7 - DR
        8 - FR
        9 - FL
        10 - BL
        11 - BR
    - Orientation reference for corners (which sticker counts as "up", giving
      a twist of 0) and edges (which way counts as "good", giving a flip of 0).
        Corners:
            Cube Orientation:
                U - White
                D - Yellow
                F - Red
                B - Orange
                L - Green
                R - Blue
            Corner Orientation:
                Note: U/D rotations presere orientation of corners
                - 0: U/D face is in U/D position
                - 1: U/D face is rotated clockwise once
                - 2: U/D face is rotated clockwise twice
            Edge Orientation:
                Note: U/D/L/R/F2/B2 preserve edge orientation
                - 0: U/F/B/D face is in U/F/B/D position

Once chosen, document them in this docstring — moves.py must agree.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, model_validator

if TYPE_CHECKING:
    from rubiks.cube.moves import Move

CORNER_COUNT = 8
EDGE_COUNT = 12


class CubeState(BaseModel):
    """Immutable 3x3 Rubik's cube state.

    `frozen=True` makes instances immutable and hashable (free dict/set keys).
    Pydantic validates fields on every construction, which catches malformed
    states immediately — useful during move-table development. The cost is
    real on the hot search path; profile before committing to this for IDA*.

    Field semantics:
        cp[i] = id of the corner cubie currently sitting in slot i
        co[i] = orientation (0..2) of the corner in slot i
        ep[i] = id of the edge cubie currently sitting in slot i
        eo[i] = orientation (0..1) of the edge in slot i
    """

    model_config = ConfigDict(frozen=True)

    cp: tuple[int, ...]   # length 8, values 0..7
    co: tuple[int, ...]   # length 8, values 0..2
    ep: tuple[int, ...]   # length 12, values 0..11
    eo: tuple[int, ...]   # length 12, values 0..1

    @model_validator(mode="after")
    def _validate_shapes(self) -> Self:
        if len(self.cp) != CORNER_COUNT or len(self.co) != CORNER_COUNT:
            raise ValueError(f"cp and co must both have length {CORNER_COUNT}")
        if len(self.ep) != EDGE_COUNT or len(self.eo) != EDGE_COUNT:
            raise ValueError(f"ep and eo must both have length {EDGE_COUNT}")
        if not all(0 <= v < CORNER_COUNT for v in self.cp):
            raise ValueError("cp values must be in 0..7")
        if not all(0 <= v < 3 for v in self.co):
            raise ValueError("co values must be in 0..2")
        if not all(0 <= v < EDGE_COUNT for v in self.ep):
            raise ValueError("ep values must be in 0..11")
        if not all(0 <= v < 2 for v in self.eo):
            raise ValueError("eo values must be in 0..1")
        return self

    @classmethod
    def solved(cls) -> CubeState:
        """The identity state: each cubie in its home slot, oriented."""
        return cls(
            cp=tuple(range(CORNER_COUNT)),
            co=(0,) * CORNER_COUNT,
            ep=tuple(range(EDGE_COUNT)),
            eo=(0,) * EDGE_COUNT,
        )

    def is_solved(self) -> bool:
        return self == CubeState.solved()

    def apply(self, move: Move) -> CubeState:
        """Apply a single move, returning a new CubeState.
        Return a NEW CubeState (the model is frozen — never mutate self).
        """
        return CubeState(
            cp = tuple(self.cp[move.cp_perm[i]] for i in range(CORNER_COUNT)),
            co = tuple((self.co[move.cp_perm[i]] + move.co_delta[i]) % 3 for i in range(CORNER_COUNT)),
            ep = tuple(self.ep[move.ep_perm[i]] for i in range(EDGE_COUNT)),
            eo = tuple((self.eo[move.ep_perm[i]] + move.eo_delta[i]) % 2 for i in range(EDGE_COUNT))
        )
