"""Protocols that define the seam between the cube and the brain.

These are STRUCTURAL types (typing.Protocol) — any class that implements
the listed methods satisfies the protocol. No inheritance needed.

That's the architectural point: a future Kociemba solver, a Thistlethwaite
solver, or your own hand-rolled algorithm only has to satisfy `Solver`. The
cube model and the CLI don't know which is in use.

Same goes for heuristics: ZeroHeuristic, CornerPDBHeuristic, or some weighted
combination all share one interface.
"""

from __future__ import annotations

from typing import Protocol

from rubiks.cube.moves import Move
from rubiks.cube.state import CubeState


class Heuristic(Protocol):
    """Lower-bound estimator on remaining moves to solve.

    `estimate(state)` MUST be admissible (never over-estimates), otherwise
    IDA* loses its optimality guarantee. Returning 0 is always admissible
    but provides no pruning.
    """

    def estimate(self, state: CubeState) -> int: ...


class Solver(Protocol):
    """Maps a scrambled state to a sequence of moves that solves it.

    Returns None if the solver gives up (e.g. depth bound exceeded).
    """

    def solve(self, state: CubeState) -> list[Move] | None: ...
