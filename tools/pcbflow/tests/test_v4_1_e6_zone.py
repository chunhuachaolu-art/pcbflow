"""tests/test_v4_1_e6_zone -- G6.1 zone/铺铜重灌交互负向集测试。

依据：任务书 §3 E6 G6.1 + prereg-e6.json g61（判据先于运行冻结）；
SW_NODE 教训（pcbagent B3 r2/r3）+ apply1 awaiting-refill + DEV-E4-004。

离线部分（本文件主体）：audit 旗标逐场景命中/候选暴露/advisory 披露
（E1 limitation 边界如实呈现在案）/双口径差分函数。kicad-cli oracle
部分由编排侧 op_run_g61 执行（产物 g61-summary.json，盘上在案时
额外断言——负向集与实跑对账）。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow.v4_1 import e6zone
from pcbflow.v4_1.board_parse import parse_board_text
from pcbflow.v4_1.board_parse_alt import parse_board_text_alt
from pcbflow.v4_1.checker import (IndependentGeometryChecker,
                                  build_check_items)
from pcbflow.v4_1.e6g61 import _g61_candidate_defs
from pcbflow.v4_1.netclasses import netclass_table_from_kicad_pro
from pcbflow.v4_1.precheck import AdvisoryPrecheckV41, build_geom_items

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_E6 = os.path.join(_ROOT, "out", "v4.1-engineering", "e6")


# ---------------------------------------------------------------- 场景 audit

def test_scenario_audit_flags_match_prereg():
    """逐场景：audit 旗标类==prereg guard_expect；ZN-0 负对照零旗标。"""
    sc = e6zone.build_scenario_boards()
    for sid, s in sc.items():
        audit = e6zone.audit_zone_refill_interactions(s["board_text"])
        got = sorted({f["flag"] for f in audit["flags"]})
        assert got == sorted(s["guard_expect"]), (sid, got)
        assert audit["commit_blocked_without_refill_drc"] == bool(got)


def test_audit_fail_closed_blocks_all_flag_classes():
    """任一旗标类都使 commit_blocked_without_refill_drc=true（fail-closed）。"""
    sc = e6zone.build_scenario_boards()
    for cls in e6zone.zone_flag_classes():
        if cls == "zone_interaction_unverifiable_for_candidate":
            continue  # 候选域旗标走 candidate_zone_exposure 判
        hit = False
        for sid, s in sc.items():
            audit = e6zone.audit_zone_refill_interactions(s["board_text"])
            if cls in {f["flag"] for f in audit["flags"]}:
                assert audit["commit_blocked_without_refill_drc"] is True
                hit = True
        assert hit, "旗标类 %s 无场景覆盖（负向集缺口）" % cls


# ---------------------------------------------------------------- 候选暴露

def test_candidate_exposure_flags_zone_interaction():
    """zone 交互候选：暴露旗标置位+advisory clean 不可作终判。"""
    sc = e6zone.build_scenario_boards()
    cands = _g61_candidate_defs()
    res = e6zone.candidate_zone_exposure(
        "via", cands["ZN-1-stale-fill-foreign-via"]["net"],
        cands["ZN-1-stale-fill-foreign-via"]["layers"],
        cands["ZN-1-stale-fill-foreign-via"]["bbox"],
        sc["ZN-1-stale-fill-foreign-via"]["board_text"])
    assert res["flag"] == "zone_interaction_unverifiable_for_candidate"
    assert res["advisory_clean_usable_as_final_verdict"] is False


def test_candidate_exposure_negative_control():
    """无 zone 板：候选无暴露旗标，advisory clean 可作终判（零误报）。"""
    sc = e6zone.build_scenario_boards()
    cands = _g61_candidate_defs()
    res = e6zone.candidate_zone_exposure(
        "segment", cands["ZN-0-no-zone-negative-control"]["net"],
        [cands["ZN-0-no-zone-negative-control"]["layer"]],
        cands["ZN-0-no-zone-negative-control"]["bbox"],
        sc["ZN-0-no-zone-negative-control"]["board_text"])
    assert res["flag"] is None
    assert res["advisory_clean_usable_as_final_verdict"] is True


# ---------------------------------------------------------------- advisory 披露

def test_precheck_zone_limitation_disclosed_on_zone_interaction():
    """E1 边界如实呈现在案：zone 交互候选的 advisory 结果必携 zone
    limitation（不静默渲染无条件 clean）。"""
    sc = e6zone.build_scenario_boards()
    cands = _g61_candidate_defs()
    cand = cands["ZN-1-stale-fill-foreign-via"]
    text = sc["ZN-1-stale-fill-foreign-via"]["board_text"]
    table = netclass_table_from_kicad_pro(
        sc["ZN-1-stale-fill-foreign-via"]["pro_obj"])
    pre = AdvisoryPrecheckV41(build_geom_items(parse_board_text(text)),
                              table)
    chk = IndependentGeometryChecker(
        build_check_items(parse_board_text_alt(text)), table)
    x, y, size = cand["via"]
    r_pre = pre.check_via(cand["net"], cand["layers"], size, x, y)
    r_chk = chk.check_via(cand["net"], cand["layers"], size, x, y)
    # 双引擎对 zone 不可见 ⇒ clean 是其合同内结果；边界必须披露在案
    assert r_pre["verdict"] in ("clean", "violation")
    zone_lim = [l for l in r_pre["limitations"] if "zone" in l]
    assert zone_lim, "zone limitation 缺失=静默（牙齿失效）"
    assert [l for l in r_chk["limitations"] if "zone" in l]


# ---------------------------------------------------------------- 双口径差分

def _mk_drc(viol=(), unc=()):
    return {"violations": list(viol), "unconnected_items": list(unc)}


def test_refill_divergence_detection_all_dimensions():
    a = _mk_drc(
        viol=[{"type": "clearance", "severity": "error",
               "items": [{"description": "x"}, {"description": "y"}]}],
        unc=[{"items": [{"description": "u1"}]}])
    same = _mk_drc(
        viol=[{"type": "clearance", "severity": "error",
               "items": [{"description": "y"}, {"description": "x"}]}],
        unc=[{"items": [{"description": "u1"}]}])
    assert e6zone.refill_divergence(a, same)["verdict"] == "consistent"
    b_removed = _mk_drc(unc=[{"items": [{"description": "u1"}]}])
    r1 = e6zone.refill_divergence(a, b_removed)
    assert r1["verdict"] == "divergent" and r1["violation_removed_under_refill"]
    b_added = _mk_drc(
        viol=[{"type": "clearance", "severity": "error",
               "items": [{"description": "x"}, {"description": "y"}]},
              {"type": "shorting", "severity": "error",
               "items": [{"description": "z"}]}],
        unc=[{"items": [{"description": "u1"}]}])
    r2 = e6zone.refill_divergence(a, b_added)
    assert r2["violation_added_under_refill"]
    b_unc = _mk_drc(
        viol=[{"type": "clearance", "severity": "error",
               "items": [{"description": "x"}, {"description": "y"}]}],
        unc=[{"items": [{"description": "u1"}]},
             {"items": [{"description": "u2"}]}])
    r3 = e6zone.refill_divergence(a, b_unc)
    assert r3["unconnected_added_under_refill"]
    assert r3["divergent"] is True


def test_refill_divergence_fails_closed_on_divergence():
    a = _mk_drc(unc=[{"items": [{"description": "u"}]}])
    b = _mk_drc()
    r = e6zone.refill_divergence(a, b)
    assert r["divergent"] and "fail_closed_rule" in r


# ---------------------------------------------------------------- 实跑对账（盘上）

def _summary():
    p = os.path.join(_E6, "g61-refill", "g61-summary.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.skipif(_summary() is None, reason="G6.1 实跑产物未在盘")
def test_g61_summary_oracle_alignment():
    """实跑对账：全部场景 oracle=divergent（ZN-0=consistent）+guard 命中。"""
    s = _summary()
    by = {r["scenario_id"]: r for r in s["scenarios"]}
    assert by["ZN-0-no-zone-negative-control"]["divergence"][
        "verdict"] == "consistent"
    for sid in ["ZN-1-stale-fill-foreign-via", "ZN-2-unfilled-zone-pour",
                "ZN-3-awaiting-refill-same-net",
                "ZN-4-stale-fill-foreign-track",
                "ZN-5-revc-staging-real"]:
        r = by[sid]
        assert r["divergence"]["verdict"] == "divergent", sid
        assert set(r["audit"]["flag_classes_present"]) == set(
            r["guard_expect"]) if sid != "ZN-5-revc-staging-real" else True
        assert r["audit"]["commit_blocked_without_refill_drc"] is True


@pytest.mark.skipif(_summary() is None, reason="G6.1 实跑产物未在盘")
def test_g61_zn1_advisory_clean_not_final():
    """ZN-1：advisory clean（zone 不可见）+暴露旗标=clean 不可作终判
    （既有引擎边界如实登记非静默）。"""
    s = _summary()
    by = {r["scenario_id"]: r for r in s["scenarios"]}
    r = by["ZN-1-stale-fill-foreign-via"]
    assert r["advisory_disclosure"]["zone_limitation_disclosed"] is True
    assert r["candidate_exposure"][
        "advisory_clean_usable_as_final_verdict"] is False
