"""Heuristic implementations.

A heuristic returns a *lower bound* on the number of moves still required
to solve a given state. To remain admissible for IDA*:

    estimate(state) <= true distance to solved

A tighter bound = more aggressive pruning = faster search.

Currently:
  - ZeroHeuristic: trivially admissible, no pruning. Makes IDA* degenerate
    into pure iterative-deepening DFS. Use for phase 5 to prove the search
    plumbing works.

Future (phase 8):
  - CornerPDBHeuristic: precomputed exact distance to solve just the
    corners. Strong admissible bound on the full cube.
"""

from __future__ import annotations

from rubiks.cube.state import CubeState


class ZeroHeuristic:
    """The trivial heuristic. gives a naieve depth search
    """
    
    def estimate(self, state: CubeState) -> int:
        return 0
