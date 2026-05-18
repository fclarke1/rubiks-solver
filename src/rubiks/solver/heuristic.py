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

from rubiks.cube.state import CORNER_COUNT, EDGE_COUNT, CubeState


class ZeroHeuristic:
    """The trivial heuristic. gives a naieve depth search
    """
    
    def estimate(self, state: CubeState) -> int:
        return 0


class PoorCornerEdgeHeuristic:
    """ Can move at most 4 corners or edges into the correct
    place with 1 move
    """
    def estimate(self, state: CubeState) -> int:
        corner_k = 0
        edge_k = 0
        for i in range(CORNER_COUNT):
            if (
                state.cp[i]!=i
                or state.co[i]!=0
            ): corner_k += 1
        for i in range(EDGE_COUNT):
            if (
                state.ep[i]!=i
                or state.eo[i]!=0
            ): edge_k += 1
        k = max(corner_k, edge_k) // 4
        return k