"""LIVE2B-S1 纯函数测试（账本/行号/差集/归因对照/restricted 声明）。

只测 pcbflow/live2s1_experiment.py 的纯函数；零板输入、零落盘、零子进程
（live 板与快照副本不出现在测试里，编排侧纪律不受本文件影响）。"""

import pytest

from pcbflow import live2s1_experiment as L2


# ---- 行号钉死 ----------------------------------------------------------------
def _mkrow(net, dist, **kw):
    r = {"net": net, "distance_mm": dist, "ax": 0.0, "ay": 0.0,
         "bx": 1.0, "by": 1.0, "alayers": [0], "blayers": [0]}
    r.update(kw)
    return r


def test_live2s1_expect_row_table_matches_authority():
    # 行号权威表（与 RIPUP-1 / LIVE-1 gateA 权威逐项一致，漂移即失守）
    assert L2.EXPECT_ROW == {"FMC_SDNE0": "RPL-038", "GNDA": "RPL-039",
                             "LTDC_VSYNC": "RPL-052", "SWDIO": "RPL-054",
                             "VBAT": "RPL-056", "3V3": "RPL-019"}
    assert set(L2.TARGETS) == set(L2.EXPECT_ROW)


def test_live2s1_assign_target_rows_picks_pinned_rows(monkeypatch):
    # 合成 61 单行网 T00..T60 + 3V3 两条多余断点行；"3V3"（数字开头）排最前，
    # 3 行占 idx 0-2，全体 T 网行号后移 3 → 期望表按实际 index 注入
    monkeypatch.setattr(L2, "EXPECT_ROW",
                        {"T10": "RPL-013", "3V3": "RPL-002",
                         "T38": "RPL-041", "T39": "RPL-042",
                         "T52": "RPL-055", "T56": "RPL-059"})
    rows = [_mkrow("T%02d" % k, 10.0 + k * 0.1) for k in range(61)]
    rows += [_mkrow("3V3", 1.0), _mkrow("3V3", 2.0), _mkrow("3V3", 10.2)]
    by_net = L2.assign_target_rows(rows)
    assert set(by_net) == set(L2.EXPECT_ROW)
    for net, rid in L2.EXPECT_ROW.items():
        assert by_net[net]["row_id"] == rid
    # 钉位=index 语义：钉住行≠该网 distance 最小行（多断点各自成行）
    assert by_net["3V3"]["distance_mm"] == 10.2


def test_live2s1_assign_target_rows_drift_raises(monkeypatch):
    expect = {"T10": "RPL-010", "T19": "RPL-019"}
    rows = [_mkrow("T%02d" % k, 10.0 + k * 0.1) for k in range(61)]
    rows.insert(0, _mkrow("AAA", 0.5))    # 全体行号 +1 → 漂移
    monkeypatch.setattr(L2, "EXPECT_ROW", expect)
    with pytest.raises(L2.RowDrift):
        L2.assign_target_rows(rows)


def test_live2s1_assign_target_rows_missing_raises(monkeypatch):
    expect = {"T10": "RPL-010", "T19": "RPL-019"}
    rows = [_mkrow("T%02d" % k, 10.0 + k * 0.1) for k in range(61)
            if k != 19]
    monkeypatch.setattr(L2, "EXPECT_ROW", expect)
    with pytest.raises(L2.RowDrift):
        L2.assign_target_rows(rows)


# ---- RIPUP-1 封堵归因解析 -----------------------------------------------------
def test_live2s1_parse_blocker_nets_ordered_dedup():
    desc = ["[ADC_A3] 走线 (1.4,36.7)-(1.4,24.7) w=0.2",
            "[GND] J4 焊盘 3 circle",
            "[ADC_A3] 走线 (2.6,23.5)-(2.6,23.5) w=0.2",
            "无前缀条目"]
    assert L2.parse_blocker_nets(desc) == ["ADC_A3", "GND"]
    assert L2.parse_blocker_nets([]) == []
    assert L2.parse_blocker_nets(None) == []


# ---- 失败集差集（验收门） ------------------------------------------------------
def test_live2s1_failure_set_diff_no_new_failures():
    pre = ["tests/a.py::t1", "tests/a.py::t2", "tests/b.py::t3"]
    post = ["tests/a.py::t1", "tests/b.py::t3"]
    d = L2.failure_set_diff(pre, post)
    assert d["gates_ok"] is True
    assert d["new_failures"] == []
    assert d["fixed"] == ["tests/a.py::t2"]
    assert d["unchanged_count"] == 2


def test_live2s1_failure_set_diff_new_failure_fails_gate():
    d = L2.failure_set_diff(["a::t1"], ["a::t1", "a::t9"])
    assert d["gates_ok"] is False
    assert d["new_failures"] == ["a::t9"]


def test_live2s1_failure_set_diff_identical():
    d = L2.failure_set_diff(["a::t1"], ["a::t1"])
    assert d["gates_ok"] is True and d["new_failures"] == [] \
        and d["fixed"] == []


# ---- 割元素网属直方图 ----------------------------------------------------------
def test_live2s1_collect_prim_bboxes_nested():
    why = {"rule": "clearance", "prim_bbox": [1.0, 2.0, 3.0, 4.0],
           "per_layer": [{"why": {"prim_bbox": [5, 6, 7, 8.5]}},
                         {"why": None}]}
    assert L2.collect_prim_bboxes(why) == [(1.0, 2.0, 3.0, 4.0),
                                           (5.0, 6.0, 7.0, 8.5)]
    assert L2.collect_prim_bboxes({"rule": "cert_scope_window"}) == []


def test_live2s1_cert_net_histogram_groups_and_boundary():
    groups = [
        {"kind": "cell", "layer": 0,
         "why": {"prim_bbox": [1.0, 1.0, 1.5, 1.5]}, "items": [[1, 1], [1, 2]]},
        {"kind": "edge", "layer": 6,
         "why": {"prim_bbox": [2.0, 2.0, 2.5, 2.5]}, "items": [[0, 1, 1, 1]]},
        {"kind": "via", "layer": None,
         "why": {"rule": "hole_clearance(via_drill)"}, "items": [[3, 3]]},
        {"kind": "boundary", "layer": None,
         "why": {"rule": "cert_scope_window"}, "items": [[0, 1, 1, 0]]},
    ]
    idx = {(1.0, 1.0, 1.5, 1.5): ["GND"],
           (2.0, 2.0, 2.5, 2.5): ["ETH_REF_CLK", "FMC_SDCKE0"]}
    h = L2.cert_net_histogram(groups, idx)
    assert h["nets"] == {"ETH_REF_CLK": 1, "FMC_SDCKE0": 1, "GND": 2}
    assert h["boundary_cuts"] == 1
    assert h["other_unattributed"] == 1


def test_live2s1_cert_net_histogram_empty():
    h = L2.cert_net_histogram(None, {})
    assert h == {"nets": {}, "boundary_cuts": 0, "other_unattributed": 0}


# ---- 与 RIPUP-1 归因的一致性对照 ------------------------------------------------
def test_live2s1_consistency_compare_relations():
    assert L2.consistency_compare(["GND", "ADC_A3"],
                                  ["GND"])["relation"] \
        == "cert_subset_of_ripup1"
    assert L2.consistency_compare(["GND"],
                                  ["GND", "ADC_A3"])["relation"] \
        == "ripup1_subset_of_cert"
    assert L2.consistency_compare(["GND", "ADC_A3"],
                                  ["ADC_A3", "VDDA"])["relation"] == "overlap"
    assert L2.consistency_compare(["GND"], ["ADC_A3"])["relation"] \
        == "disjoint"
    assert L2.consistency_compare(["GND"], ["ADC_A3"])["shared"] == []
    assert L2.consistency_compare(["GND"], [])["relation"] \
        == "no_cert_attribution"
    assert L2.consistency_compare([], ["GND"])["relation"] \
        == "no_ripup1_blockers"


# ---- restricted 声明 -----------------------------------------------------------
def test_live2s1_restricted_declarations_unknown():
    d = L2.restricted_declarations("UNKNOWN", None)
    assert any("no-ripup" in x for x in d)
    assert any("不自动改判" in x for x in d)


def test_live2s1_restricted_declarations_unsat():
    cert = {"cut_count": 8, "scope": {"model": "restricted_lattice",
                                      "region_mm": [0, 0, 1, 1],
                                      "res_mm": 0.05}}
    d = L2.restricted_declarations("UNSAT", cert)
    assert any("restricted_lattice" in x for x in d)
    assert any("割元素=8" in x for x in d)
    assert any("verified=true" in x for x in d)
    assert any("不等价于" in x for x in d)


def test_live2s1_restricted_declarations_sat():
    d = L2.restricted_declarations("SAT", None)
    assert any("L1 终判全过" in x for x in d)


# ---- verdict 行装配与汇总 -------------------------------------------------------
def test_live2s1_steps_summary_shape():
    steps = [{"tier": "frozen_600k", "status": "UNKNOWN",
              "unknown_reason": "unknown:region_over_window(x)",
              "window_nodes": 600000, "margin_mm": 1.0, "skipped": False},
             {"tier": "board", "skipped": True,
              "skip_reason": "corridor_not_certified"}]
    s = L2.steps_summary(steps)
    assert s[0]["cut_count"] is None and s[0]["verified"] is None
    assert s[1]["skipped"] is True and s[1]["status"] is None


def test_live2s1_verdict_row_assembly_and_strengthen_upgrade():
    win1 = {"row_id": "RPL-054", "net": "SWDIO", "status": "UNSAT",
            "unknown_reason": None, "witness": None, "router": {"ok": False},
            "ladder": [], "steps": [],
            "certificate": {"cut_count": 8, "verified": True,
                            "scope": {"model": "restricted"}}}
    bs = {"tier": "board_strengthen", "status": "UNSAT",
          "certificate": {"cut_count": 4242, "verified": True,
                          "scope": {"model": "restricted_board"}}}
    row = L2.verdict_row("RPL-054", "SWDIO", win1, ["GND", "ADC_A3"],
                         {"nets": {"GND": 8}, "boundary_cuts": 0,
                          "other_unattributed": 0},
                         board_strengthen=bs)
    assert row["live2s1_status"] == "UNSAT"
    assert row["certificate_cut_count"] == 4242      # 板级强化割升为最终证书
    assert row["ripup1_consistency"]["relation"] == "cert_subset_of_ripup1"
    assert row["restricted_declarations"]
    # 无强化步 → 保留 win1 证书
    row2 = L2.verdict_row("RPL-054", "SWDIO", win1, [], {})
    assert row2["certificate_cut_count"] == 8
    assert row2["ripup1_consistency"]["relation"] == "no_cert_attribution"


def test_live2s1_verdict_row_unknown_keeps_status():
    win1 = {"row_id": "RPL-056", "net": "VBAT", "status": "UNKNOWN",
            "unknown_reason": "unknown:no_certificate(候选通径)",
            "witness": None, "router": {"ok": False}, "ladder": [],
            "steps": [], "certificate": None}
    row = L2.verdict_row("RPL-056", "VBAT", win1, ["LSE_OUT"], {})
    assert row["live2s1_status"] == "UNKNOWN"
    assert row["certificate_cut_count"] is None


def test_live2s1_summary_counts_fail_closed():
    rows = [{"live2s1_status": "UNSAT"}, {"live2s1_status": "UNKNOWN"},
            {"live2s1_status": "UNSAT"}]
    assert L2.summary_counts(rows) == {"SAT": 0, "UNSAT": 2, "UNKNOWN": 1}
    with pytest.raises(RuntimeError):
        L2.summary_counts([{"live2s1_status": "MAYBE"}])
