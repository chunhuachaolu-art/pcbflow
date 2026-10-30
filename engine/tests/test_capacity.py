# -*- coding: utf-8 -*-
"""capacity 容量账本：V2 口径 占用=铜宽+0.5×相邻对；ribbon 声明占用。"""
import pytest

from v5.metrics import capacity as cap
from v5.metrics.capacity import CapacityEntry, check_fits, corridor_occupancy


def e(nid, w, declared=None):
    return CapacityEntry(nid, w, declared_occupancy=declared)


def test_empty_corridor():
    assert corridor_occupancy([]) == 0.0


def test_single_entry_no_spacing():
    assert corridor_occupancy([e("A", 0.2)]) == pytest.approx(0.2)


def test_two_entries_one_gap():
    assert corridor_occupancy([e("A", 0.2), e("B", 0.2)]) == pytest.approx(0.9)


def test_v2_j2_occupancy_p4_plus_p3():
    """黄金口径：P4(3.3)+0.5+P3(0.2) = 4.0/4.3。"""
    occ = corridor_occupancy([e("P4", 0.0, declared=3.3), e("P3", 0.2)])
    assert occ == pytest.approx(4.0)
    assert check_fits([e("P4", 0.0, declared=3.3), e("P3", 0.2)], 4.3)["fits"]


def test_v2_double_f_infeasible():
    """双留F.Cu：3.3+0.2+0.2+0.5×2 = 4.7 > 4.3 不可行。"""
    occ = corridor_occupancy([e("P4", 0.0, declared=3.3), e("P3", 0.2), e("P5", 0.2)])
    assert occ == pytest.approx(4.7)
    fits = check_fits([e("P4", 0.0, declared=3.3), e("P3", 0.2), e("P5", 0.2)], 4.3)
    assert not fits["fits"]
    assert fits["slack_mm"] == pytest.approx(-0.4)


def test_exact_capacity_edge_fits():
    """对抗：占用恰等于容量（擦边）→ fits。"""
    assert check_fits([e("A", 4.3)], 4.3)["fits"]


def test_epsilon_over_capacity_fails():
    assert not check_fits([e("A", 4.3 + 1e-6)], 4.3)["fits"]


def test_remaining_capacity():
    entries = [e("P4", 0.0, declared=3.3), e("P3", 0.2)]
    assert cap.remaining_capacity(entries, 4.3) == pytest.approx(0.3)


def test_ribbon_declared_occupancy_used():
    entry = CapacityEntry("P4", 0.15, declared_occupancy=3.3)
    assert entry.occupancy == 3.3


def test_slack_positive_after_p3_only():
    fits = check_fits([e("P4", 0.0, declared=3.3), e("P5", 0.2)], 4.3)
    assert fits["fits"] and fits["slack_mm"] == pytest.approx(0.3)


def test_ledger_deterministic_key_order():
    entries_by = {
        "C1": [e("P4", 0.0, declared=3.3), e("P3", 0.2)],
        "A2": [e("X", 0.3)],
    }
    caps = {"C1": 4.3, "A2": 1.0}
    b1 = cap.ledger_bytes(entries_by, caps)
    b2 = cap.ledger_bytes(entries_by, caps)
    assert b1 == b2
    assert b1.index(b'"A2"') < b1.index(b'"C1"')


def test_ledger_content():
    ledger = cap.ledger_for_layer({"C1": [e("P4", 0.0, declared=3.3)]}, {"C1": 4.3})
    assert ledger["C1"]["occupancy_mm"] == 3.3
    assert ledger["C1"]["entries"][0]["net_id"] == "P4"


def test_entry_order_matters_for_sum_symmetry():
    """加法交换——顺序不影响总和（相邻对数不变）。"""
    a = corridor_occupancy([e("A", 0.2), e("B", 0.3), e("C", 0.4)])
    b = corridor_occupancy([e("C", 0.4), e("A", 0.2), e("B", 0.3)])
    assert a == pytest.approx(b)


def test_as_dict_roundtrip():
    entry = CapacityEntry("P4", 0.0, declared_occupancy=3.3, span=(30.95, 34.25))
    d = entry.as_dict()
    assert d["span"] == [30.95, 34.25]
    assert d["declared_occupancy"] == 3.3
