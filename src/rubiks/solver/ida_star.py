"""Iterative-Deepening A* (IDA*) for cube solving.

Algorithm (Korf 1985):
    1. Compute initial bound = h(root).
    2. Run a depth-bounded DFS where a node is pruned if g(n) + h(n) > bound.
    3. If the DFS reaches a solved state, return the path.
    4. Otherwise, set the new bound to the smallest f-value that was pruned
       and repeat.

With ZeroHeuristic this reduces to pure iterative-deepening DFS — slow but
finds optimal solutions. With a strong heuristic (corner PDB, phase 8) the
same algorithm becomes orders of magnitude faster.

Memory cost is O(depth) — only the current DFS path is held in memory. That's
what makes IDA* feasible for cube where BFS would need O(branching^depth)
memory.
"""

from __future__ import annotations

from typing import Final
import math

from rubiks.cube.moves import ALL_MOVES, Move
from rubiks.cube.state import CubeState
from rubiks.solver.base import Heuristic


_FOUND: Final = object()
_MAX_BOUND: Final = 30


class IDAStar:
    """IDA* solver parameterised by a Heuristic.
    """

    def __init__(self, heuristic: Heuristic) -> None:
        self.heuristic = heuristic

    def solve(self, root: CubeState) -> list[Move] | None:
        """Outer loop: deepen the bound until the goal is found or capped.
        """
        bound = self.heuristic.estimate(root)
        path = []
        while True:
            t = self._search(root, path, g=0, bound=bound)
            if t is _FOUND:
                return path
            elif t is math.inf:
                return None
            bound = t
            if bound > _MAX_BOUND:
                return None

    def _search(
        self,
        state: CubeState,
        path: list[Move],
        g: int,
        bound: int,
    ) -> object:
        """Recursive depth-bounded DFS. Returns either _FOUND, infinity (no
        result this bound), or the smallest f-value that was pruned at this
        subtree (used as the next iteration's bound).
        """
        f = g + self.heuristic.estimate(state)
        if f > bound:
            return f
        elif state.is_solved():
            return _FOUND
        
        min_next = math.inf
        for move in ALL_MOVES:
            path.append(move)
            t = self._search(state.apply(move), path, g + 1, bound)
            if t is _FOUND:
                return _FOUND
            if t < min_next:
                min_next = t
            path.pop()
        return min_next