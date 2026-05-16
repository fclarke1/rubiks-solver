"""Property tests for the cube model.

Each test states an invariant that must hold for ANY cube state and ANY
well-formed move sequence. When a property fails, your move tables or
apply() logic are wrong — the test won't tell you which, but a failing
test on a single move usually points straight at that move's definition.
"""

import pytest
import random

from rubiks.cube.pack import pack_orientation, unpack_orientation


@pytest.mark.parametrize("seed", range(10))
def test_pack_unpack(seed: int):
    rng = random.Random(seed)
    corner_base = 3
    edge_base = 2
    corner_length = 4
    edge_length = 4

    co_state = tuple(rng.choice(range(corner_base)) for _ in range(corner_length))
    eo_state = tuple(rng.choice(range(edge_base)) for _ in range(edge_length))

    co_pack = pack_orientation(co_state, corner_base)
    co_unpack = unpack_orientation(co_pack, corner_length, corner_base)
    eo_pack = pack_orientation(eo_state, edge_base)
    eo_unpack = unpack_orientation(eo_pack, edge_length, edge_base)

    assert (eo_unpack == eo_state) and (co_unpack == co_state)