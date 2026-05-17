"""ANSI-colored 2D net renderer for cube states.

Reads only CubeState — no imports from solver or moves. Produces a printable
string of the unfolded cube in the standard cross layout:

            U U U
            U U U
            U U U
    L L L F F F R R R B B B
    L L L F F F R R R B B B
    L L L F F F R R R B B B
            D D D
            D D D
            D D D

Run as a script to verify ANSI colors work in your terminal:
    uv run python -m rubiks.viz.ansi_net
"""

from __future__ import annotations

from rubiks.cube.state import CubeState

# ----- ANSI primitives -----

# 256-color background codes for each face, per state.py's color convention:
#   U = White   D = Yellow   F = Red   B = Orange   L = Green   R = Blue

RESET = "\x1b[0m"
ANSI_BG: dict[str, str] = {
    "W": "\x1b[48;5;231m",   # white
    "Y": "\x1b[48;5;226m",   # yellow
    "R": "\x1b[48;5;196m",   # red
    "O": "\x1b[48;5;208m",   # orange
    "G": "\x1b[48;5;46m",    # green
    "B": "\x1b[48;5;21m",    # blue
    "D": "\x1b[48;5;238m"    # gray placeholder
}


def block(color: str) -> str:
    """One sticker: two spaces of colored background, then reset.

    Two characters wide because terminal cells are about half as wide as
    tall, so two spaces give a roughly-square colored block.
    """
    return f"{ANSI_BG[color]}  {RESET}"

FACE_RANGES = {
    "U": (0, 9),
    "R": (9, 18),
    "F": (18, 27),
    "D": (27, 36),
    "L": (36, 45),
    "B": (45, 54),
}

# marked facelet first
EDGE_COLOURS = {
    0: ("W", "R"),  # UF
    1: ("W", "G"),  # UL
    2: ("W", "O"),  # UB
    3: ("W", "B"),  # UR
    4: ("Y", "O"),  # DB
    5: ("Y", "G"),  # DL
    6: ("Y", "R"),  # DF
    7: ("Y", "B"),  # DR
    8: ("R", "B"),  # FR
    9: ("R", "G"),  # FL
    10: ("O", "G"), # BL
    11: ("O", "B")  # BR
}

# marked facelet first, then what is ontop if rotated once, then twice
CORNER_COLOURS = {
    0: ("W", "R", "B"),  # UFR
    1: ("W", "G", "R"),  # UFL
    2: ("W", "O", "G"),  # UBL
    3: ("W", "B", "O"),  # UBR
    4: ("Y", "O", "B"),  # DBR
    5: ("Y", "G", "O"),  # DBL
    6: ("Y", "R", "G"),  # DFL
    7: ("Y", "B", "R"),  # DFR
}

CROSS_ROW_EDGE_MAPPING = {
    1: (2,0),   # UB
    3: (1,0),   # UL
    5: (3,0),   # UR
    7: (0,0),   # UF
    10: (3,1),  # UR
    12: (8,1),  # FR
    14: (11,1), # BR
    16: (7,1),  # DR
    19: (0,1),  # UF
    21: (9,0),  # FL
    23: (8,0),  # FR
    25: (6,1),  # DF
    28: (6,0),  # DF
    30: (5,0),  # DL
    32: (7,0),  # DR
    34: (4,0),  # DB
    37: (1,1),  # UL
    39: (10,1), # BL
    41: (9,1),  # FL
    43: (5,1),  # DL
    46: (2,1),  # UB
    48: (11,0), # BR
    50: (10,0), # BL
    52: (4,1),  # DB
}

CROSS_ROW_CORNER_MAPPING = {
    0: (2, 0),  # UBL
    2: (3, 0),  # UBR
    6: (1, 0),  # UFL
    8: (0, 0),  # UFR
    9: (0, 2),  # UFR
    11: (3, 1), # UBR
    15: (7, 1), # DFR
    17: (4, 2), # DBR
    18: (1, 2), # UFL
    20: (0, 1), # UFR
    24: (6, 1), # DFL
    26: (7, 2), # DFR
    27: (6, 0), # DFL
    29: (7, 0), # DFR
    33: (5, 0), # DBL
    35: (4, 0), # DBR
    36: (2, 2), # UBL
    38: (1, 1), # UFL
    42: (5, 1), # DBL
    44: (6, 2), # DFL
    45: (3, 2), # UBR
    47: (2, 1), # UBL
    51: (4, 1), # DBR
    53: (5, 2), # DBL
}



def state_to_facelets(state: CubeState) -> list[str]:
    """Translate a CubeState into 54 sticker colors in the canonical order above.

    For each sticker position you need a lookup:
      - Which cubie slot (corner 0..7, edge 0..11, or a fixed center) shows here.
      - For non-center cubies: which of the cubie's stickers shows here, given
        the cubie's current orientation.

    Build the lookup once as a module-level table; this function is then
    pure indexing into that table.

    Suggested incremental approach (don't try the full table at once):
      1. Centers only (indices 4, 13, 22, 31, 40, 49). Centers never move.
      2. Add U face: 4 corner stickers + 4 edge stickers. Apply U/U'/U2 and
         visually verify.
      3. One side face at a time after that, eyeballing after each.
    """
    cp = state.cp
    co = state.co
    ep = state.ep
    eo = state.eo


    facelets = ["D"] * 54
    # Centres:
    facelets[4] = "W"
    facelets[22] = "R"
    facelets[40] = "G"
    facelets[13] = "B"
    facelets[49] = "O"
    facelets[31] = "Y"

    # Edges
    for facelet_idx, edge_mapping in CROSS_ROW_EDGE_MAPPING.items():
        state_edge_id, edge_side_id = edge_mapping
        edge_colour_id = ep[state_edge_id]
        edge_rotation = eo[state_edge_id]

        cubelet = EDGE_COLOURS[edge_colour_id]
        facelet_colour = cubelet[(edge_side_id + edge_rotation) % 2]
        facelets[facelet_idx] = facelet_colour
    
    # Corners
    for facelet_idx, corner_mapping in CROSS_ROW_CORNER_MAPPING.items():
        state_corner_id, corner_side_id = corner_mapping
        corner_colour_id = cp[state_corner_id]
        corner_rotation = co[state_corner_id]

        cubelet = CORNER_COLOURS[corner_colour_id]
        facelet_colour = cubelet[(corner_side_id + corner_rotation) % 3]
        facelets[facelet_idx] = facelet_colour
    
    return facelets




def render(state: CubeState) -> str:
    """The cross-shaped net as a printable string. Just glue between
    state_to_facelets() and the layout below; nothing interesting happens here."""
    return _layout_cross(state_to_facelets(state))

# Each integer is a facelet index; each None is an empty gap in the cross.
_CROSS_ROWS: list[list[int | None]] = [
    [None, None, None,  0,  1,  2, None, None, None, None, None, None],
    [None, None, None,  3,  4,  5, None, None, None, None, None, None],
    [None, None, None,  6,  7,  8, None, None, None, None, None, None],
    [  36,   37,   38, 18, 19, 20,    9,   10,   11,   45,   46,   47],
    [  39,   40,   41, 21, 22, 23,   12,   13,   14,   48,   49,   50],
    [  42,   43,   44, 24, 25, 26,   15,   16,   17,   51,   52,   53],
    [None, None, None, 27, 28, 29, None, None, None, None, None, None],
    [None, None, None, 30, 31, 32, None, None, None, None, None, None],
    [None, None, None, 33, 34, 35, None, None, None, None, None, None],
]


def _layout_cross(facelets: list[str]) -> str:
    lines: list[str] = []
    for row in _CROSS_ROWS:
        line = "".join("  " if c is None else block(facelets[c]) for c in row)
        lines.append(line)
    return "\n".join(lines)


# ----- demo: prints a solved cube using a hand-built facelet list -----

_DEMO_SOLVED_FACELETS: list[str] = (
    ["W"] * 9 +   # U face
    ["B"] * 9 +   # R face (blue, per state.py convention)
    ["R"] * 9 +   # F face
    ["Y"] * 9 +   # D face
    ["G"] * 9 +   # L face
    ["O"] * 9     # B face (orange)
)


if __name__ == "__main__":
    import random
    from rubiks.cube.moves import ALL_MOVES

    solved = CubeState.solved()
    print(render(solved))

    rng = random.Random(3)
    moves = (rng.choice(ALL_MOVES) for _ in range(5))

    # # show all moves
    # for m in ALL_MOVES:
    #     print(f"\n\n*********\n{m.name}:")
    #     state = solved.apply(m)
    #     print(render(state))

    # random walk
    state = solved
    for m in moves:
        print(f"\n\n*********\n{m.name}:")
        state = state.apply(m)
        print(render(state))
