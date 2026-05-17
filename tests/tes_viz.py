from rubiks.viz.ansi_net import CROSS_ROW_CORNER_MAPPING, CROSS_ROW_EDGE_MAPPING

def test_cross_row_mapping():
    assert CROSS_ROW_EDGE_MAPPING.keys().isdisjoint(CROSS_ROW_CORNER_MAPPING.keys())
    assert CROSS_ROW_CORNER_MAPPING.keys() | CROSS_ROW_EDGE_MAPPING.keys() == set(range(54))
    assert len(set(CROSS_ROW_EDGE_MAPPING.values())) == len(CROSS_ROW_EDGE_MAPPING.values())
    assert len(set(CROSS_ROW_CORNER_MAPPING.values())) == len(CROSS_ROW_CORNER_MAPPING.values())