# -*- coding: utf-8 -*-
"""P3 L6 引擎终选门：A4 全测/滤除计数/tie-break、三态落盘（UNSAT 过独立复核器）、
run-02 撞带 J1 负向注入拦截、理念账本六问归类、双跑字节等、staging 无残留。

候选为内联 fixture（principle_id 夹具形态与 planner rule 留痕形态并存）+ demo-01
真实链一条（planner principle 臂，账本合同缝回归门）。板 = V2 场景（fixtures_v2）。
"""
import copy
import json
import os

import pytest

from v5 import canonical, failcert, staging
from v5.board import load_board_file
from v5.compiler import compile_board
from v5.planner import plan_candidates
from v5.selection import select_best

import fixtures_v2 as fx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO01_BOARD = os.path.join(ROOT, "boards", "d",
                            "demo-01-v2-corridor.board.v1.json")

# ---------------------------------------------------------------- 内联候选夹具

P3_B_ROUTE = [[16.0, 4.0], [34.85, 4.0], [34.85, 36.0], [16.0, 36.0]]
P3_F_ROUTE = [[16.0, 4.0], [34.85, 4.0], [34.85, 36.0], [16.0, 36.0]]
# V2 run-02 撞带 J1 路线（对抗样本）：F.Cu 三点折线，与 P4 铜带 x∈[30.95,34.25] 硬冲突
J1_ROUTE = [[31.0, 5.0], [31.0, 10.0], [45.0, 10.0]]


def _p5_route(slot_x):
    return [[37.0, 10.0], [slot_x, 10.0], [slot_x, 30.0], [37.0, 30.0]]


def _cand(cid, polylines, layers, arm="principle", trace=None, order=None):
    c = {"candidate_id": cid, "arm": arm,
         "provenance": {"generator": "test-fixture/0.1.0", "rules_consumed": [],
                        "compiled_sha256": "0" * 64},
         "route_order": order or sorted(polylines),
         "layer_assignment": layers, "polylines": polylines}
    if trace is not None:
        c["generation_trace"] = trace
    return c


def good_a(cid="C-001"):
    """可行候选 A：P3→B.Cu 槽 34.85 + P5→F.Cu 槽 34.85（实测 18.85+6.15=25.0）。"""
    return _cand(cid, {"P3": P3_B_ROUTE, "P5": _p5_route(34.85)},
                 {"P3": "B.Cu", "P5": "F.Cu"})


def good_b(cid="C-002"):
    """可行候选 B：P3→B.Cu 同 A，P5→F.Cu 槽 35.0（实测 18.85+6.0=24.85，更优）。"""
    return _cand(cid, {"P3": P3_B_ROUTE, "P5": _p5_route(35.0)},
                 {"P3": "B.Cu", "P5": "F.Cu"})


def unsat_pair():
    """双留 F.Cu 容量不可行对（V2 判分键：占用 4.7 > 4.3）。"""
    return [_cand("C-UNSAT-1", {"P3": P3_F_ROUTE, "P5": _p5_route(34.85)},
                  {"P3": "F.Cu", "P5": "F.Cu"}),
            _cand("C-UNSAT-2", {"P3": P3_F_ROUTE, "P5": _p5_route(35.0)},
                  {"P3": "F.Cu", "P5": "F.Cu"})]


def _read_cert(out_dir, board_id):
    path = os.path.join(out_dir, "%s.selection" % board_id, "%s.failcert.json" % board_id)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- A4 终选基本盘

def test_sat_selects_lowest_measured_objective(v2_board):
    """可行者按实测目标值升序取最优（24.85 < 25.0，后注册者凭实测值胜出）。"""
    r = select_best(v2_board, [good_a("C-001"), good_b("C-002")])
    assert r["verdict"] == "SAT"
    assert r["best"]["candidate_id"] == "C-002"
    objs = {pc["candidate_id"]: pc["objective"] for pc in r["per_candidate"]}
    assert objs["C-001"] == pytest.approx(25.0, abs=1e-9)
    assert objs["C-002"] == pytest.approx(24.85, abs=1e-9)
    assert r["ledger"]["measured"] == 2 and r["ledger"]["rejected"] == 0


def test_all_candidates_measured_full_scan_counted(v2_board):
    """A4/U8 全测无上限：好/坏/DRC 冲突/度量非法/宽度违例五候选全测并计数。"""
    cands = [good_a("C-001"), good_b("C-002"),
             _cand("C-DRCCONF", {"P5": _p5_route(33.0)}, {"P5": "F.Cu"}),
             _cand("C-MEASBAD", {"P99": [[0.0, 0.0], [1.0, 1.0]]}, {}),
             _cand("C-WIDTH", {"P8": [[44.0, 4.0], [48.0, 4.0]]}, {"P8": "F.Cu"})]
    r = select_best(v2_board, cands)
    assert r["ledger"]["measured"] == 5
    assert r["ledger"]["rejected"] == 3
    assert len(r["per_candidate"]) == 5
    assert r["verdict"] == "SAT" and r["best"]["candidate_id"] == "C-002"


def test_drc_conflict_rejection_recorded(v2_board):
    """DRC 冲突候选 fail-closed 滤除：违例条目键路径 + 规则 + 对象进台账。"""
    r = select_best(v2_board, [_cand("C-DRCCONF", {"P5": _p5_route(33.0)},
                                     {"P5": "F.Cu"})])
    pc = r["per_candidate"][0]
    assert pc["feasible"] is False and pc["drc_violations"] == 1
    reason = r["ledger"]["rejection_reasons"][0]
    assert reason["kind"] == "drc" and reason["rule"] == "R5"
    assert reason["path"] == "drc.violations[0]"
    assert "fixed:P4" in reason["detail"]          # 撞 P4 固定铜带
    assert r["verdict"] == "UNKNOWN" and r["best"] is None


def test_measure_infeasible_rejection_reasons(v2_board):
    """度量不可行逐条记录：未知分区/单点折线/plane 层/非有限坐标，全部 fail-closed。"""
    cands = [
        _cand("C-M1", {"P99": [[0.0, 0.0], [1.0, 1.0]]}, {}),
        _cand("C-M2", {"P5": [[37.0, 10.0]]}, {"P5": "F.Cu"}),
        _cand("C-M3", {"P5": [[37.0, 10.0], [34.85, 10.0]]}, {"P5": "In2.Cu"}),
        _cand("C-M4", {"P5": [[37.0, 10.0], [float("nan"), 10.0]]}, {"P5": "F.Cu"}),
    ]
    r = select_best(v2_board, cands)
    assert r["ledger"]["rejected"] == 4 and r["best"] is None
    reasons = r["ledger"]["rejection_reasons"]
    assert {x["kind"] for x in reasons} == {"measure"}
    paths = {x["path"] for x in reasons}
    assert "polylines/P99" in paths                  # 未知分区
    assert "polylines.P5" in paths                   # 单点折线 / 非有限坐标
    assert "layer_assignment.P5" in paths            # plane 层不可布线
    assert r["verdict"] == "UNKNOWN"                 # 无可机械复算算术 → 诚实降记


def test_tie_break_by_candidate_id_registration(v2_board):
    """同分 tie-break：候选注册序在前者胜（即 candidate_id 序），与列表给出序无关。"""
    c1 = _cand("C-010", {"P5": _p5_route(34.85)}, {"P5": "F.Cu"})
    c2 = _cand("C-002", {"P5": _p5_route(34.85)}, {"P5": "F.Cu"})
    r = select_best(v2_board, [c1, c2])
    assert r["verdict"] == "SAT"
    objs = [pc["objective"] for pc in r["per_candidate"]]
    assert objs[0] == pytest.approx(objs[1])         # 双双 6.15 同分
    assert r["best"]["candidate_id"] == "C-002"      # candidate_id 序在前者胜


def test_per_candidate_record_shape(v2_board):
    cands = [good_a("C-001"),
             _cand("C-DRCCONF", {"P5": _p5_route(33.0)}, {"P5": "F.Cu"}),
             _cand("C-MEASBAD", {"P99": [[0.0, 0.0], [1.0, 1.0]]}, {})]
    r = select_best(v2_board, cands)
    for pc in r["per_candidate"]:
        assert set(pc) == {"candidate_id", "feasible", "objective", "drc_violations"}
    by_id = {pc["candidate_id"]: pc for pc in r["per_candidate"]}
    assert by_id["C-001"]["feasible"] and by_id["C-001"]["drc_violations"] == 0
    assert by_id["C-DRCCONF"]["drc_violations"] == 1
    assert by_id["C-MEASBAD"]["drc_violations"] is None   # 未进 DRC，如实 None


def test_rejection_records_are_key_paths(v2_board):
    """台账滤除记录一律带具体键路径与规则（DRC 违例条目键路径/度量不可行）。"""
    cands = [good_a("C-001"),
             _cand("C-DRCCONF", {"P5": _p5_route(33.0)}, {"P5": "F.Cu"}),
             _cand("C-MEASBAD", {"P99": [[0.0, 0.0], [1.0, 1.0]]}, {})]
    r = select_best(v2_board, cands)
    for rec in r["ledger"]["rejection_reasons"]:
        assert set(("candidate_id", "kind", "path", "rule", "detail")) <= set(rec)
        assert rec["kind"] in ("drc", "measure")
        assert rec["path"] and rec["detail"]


# ---------------------------------------------------------------- 三态落盘

def test_sat_acceptance_written_with_sidecar_header_and_no_cert(v2_board, tmp_path):
    """SAT→验收件：best+ledger 经 staging 原子落盘，sidecar 合规 provenance 头，无证书。"""
    out = str(tmp_path / "out")
    r = select_best(v2_board, [good_a("C-001")], out_dir=out)
    assert r["verdict"] == "SAT"
    bid = v2_board["board_id"]
    final_dir = os.path.join(out, "%s.selection" % bid)
    with open(os.path.join(final_dir, "%s.selection.json" % bid), encoding="utf-8") as f:
        sel = json.load(f)
    with open(os.path.join(final_dir, "%s.selection-ledger.json" % bid),
              encoding="utf-8") as f:
        led = json.load(f)
    for doc in (sel, led):
        assert set(fx_sidecar_keys()) <= set(doc["provenance"])
    assert sel["verdict"] == "SAT" and sel["best"]["candidate_id"] == "C-001"
    assert led["ledger"]["measured"] == 1
    assert not os.path.exists(os.path.join(final_dir, "%s.failcert.json" % bid))
    assert staging.assert_no_residue(os.path.join(out, "_staging"))


def fx_sidecar_keys():
    from v5.sidecar import PROVENANCE_KEYS
    return PROVENANCE_KEYS


def test_unsat_capacity_cert_written_and_verified(v2_board, tmp_path):
    """UNSAT（容量）：unsat_core 由台账容量算术转出；读真实落盘文件过独立复核器。"""
    out = str(tmp_path / "out")
    r = select_best(v2_board, unsat_pair(), out_dir=out)
    assert r["verdict"] == "UNSAT" and r["best"] is None
    assert r["ledger"]["rejected"] == 2
    cert = _read_cert(out, v2_board["board_id"])
    assert cert["status"] == "UNSAT" and "unknown_boundary" not in cert
    assert failcert.verify(cert)["recheck"] == "PASS"       # 独立复核器 PASS
    entry = cert["unsat_core"][0]
    assert entry["constraint"] == "capacity"
    assert entry["data"]["occupancy_terms"] == pytest.approx([3.3, 0.2, 0.2])
    assert entry["data"]["capacity_mm"] == pytest.approx(4.3)
    assert "4.7" in entry["arithmetic"]                      # 4.7 > 4.3 判分键口径


def test_capacity_rejection_matches_v2_double_f_key(v2_board):
    """双留 F.Cu 的容量滤除记台账：走廊 C1/F.Cu，占用算术 = V2 判分键不可行口径。"""
    r = select_best(v2_board, unsat_pair())
    cap = [x for x in r["ledger"]["rejection_reasons"] if x["rule"] == "capacity"]
    assert cap and all(x["subject"] == "C1/F.Cu" for x in cap)
    assert all(x["path"].startswith("drc.violations[") for x in cap)


def test_unsat_width_cert_written_and_verified(v2_board, tmp_path):
    """UNSAT（宽度）：只布 P8（0.5 < R1 下限 0.8）→ 宽度算术条目过复核器。"""
    out = str(tmp_path / "out")
    r = select_best(v2_board, [_cand("C-W8", {"P8": [[44.0, 4.0], [48.0, 4.0]]},
                                     {"P8": "F.Cu"})], out_dir=out)
    assert r["verdict"] == "UNSAT"
    reasons = r["ledger"]["rejection_reasons"]
    assert len(reasons) == 1 and reasons[0]["rule"] == "R1"
    assert reasons[0]["partition"] == "P8"
    cert = _read_cert(out, v2_board["board_id"])
    assert failcert.verify(cert)["recheck"] == "PASS"
    entry = cert["unsat_core"][0]
    assert entry["constraint"] == "width"
    assert entry["data"] == {"planned_mm": 0.5, "required_min_mm": 0.8}


def test_unknown_drc_only_downgrade_cert_verified(v2_board, tmp_path):
    """UNKNOWN：纯 R5/R6 滤除不可机械复算 → 不虚报 UNSAT，降记 UNKNOWN 并如实报账。"""
    out = str(tmp_path / "out")
    cands = [
        _cand("C-UNK-1", {"P3": [[16.0, 4.0], [16.0, 36.0]]}, {"P3": "F.Cu"},
              arm="no-principle"),                       # 穿 K1 禁布区（R6）+ 贴 P9（R5）
        _cand("C-UNK-2", {"P5": _p5_route(34.0)}, {"P5": "F.Cu"},
              arm="no-principle"),                       # 撞 P4 铜带（R5）
    ]
    r = select_best(v2_board, cands, out_dir=out)
    assert r["verdict"] == "UNKNOWN" and r["best"] is None
    rules = {x["rule"] for x in r["ledger"]["rejection_reasons"]}
    assert rules == {"R5", "R6"}
    cert = _read_cert(out, v2_board["board_id"])
    assert cert["status"] == "UNKNOWN" and "unsat_core" not in cert
    assert failcert.verify(cert)["recheck"] == "PASS"
    ub = cert["unknown_boundary"]
    assert ub["achieved"]["nets_total"] == 9
    assert ub["achieved"]["nets_connected"] == 0
    assert ub["budget"]["consumed"] == {"candidates_measured": 2,
                                        "candidates_rejected": 2}
    assert "selection 测试注入占位" in ub["budget"]["limit"]["note"]


def test_unknown_empty_candidate_set(v2_board, tmp_path):
    """空候选集：measured=0，诚实 UNKNOWN，证书仍过复核器。"""
    out = str(tmp_path / "out")
    r = select_best(v2_board, [], out_dir=out)
    assert r["verdict"] == "UNKNOWN" and r["best"] is None
    assert r["ledger"]["measured"] == 0 and r["ledger"]["rejected"] == 0
    cert = _read_cert(out, v2_board["board_id"])
    assert failcert.verify(cert)["recheck"] == "PASS"


# ---------------------------------------------------------------- run-02 负向注入（P3 门硬项）

def test_run02_j1_injection_blocked(v2_board):
    """对抗注入：V2 run-02 撞带 J1 路线必须被滤除（DRC 违例入台账），绝不入选 best。"""
    adv = _cand("C-ADV-RUN02-J1", {"P5": J1_ROUTE}, {"P5": "F.Cu"},
                arm="no-principle")
    r = select_best(v2_board, [good_a("C-001"), adv])
    assert r["verdict"] == "SAT"
    assert r["best"]["candidate_id"] == "C-001"      # 对抗候选绝不成为 best
    pc = next(p for p in r["per_candidate"]
              if p["candidate_id"] == "C-ADV-RUN02-J1")
    assert pc["feasible"] is False and pc["drc_violations"] == 1
    reasons = [x for x in r["ledger"]["rejection_reasons"]
               if x["candidate_id"] == "C-ADV-RUN02-J1"]
    assert len(reasons) == 1
    assert reasons[0]["kind"] == "drc" and reasons[0]["rule"] == "R5"
    assert reasons[0]["path"] == "drc.violations[0]"
    assert "fixed:P4" in reasons[0]["detail"]        # 与 P4 铜带 R5 硬冲突被捕获


def test_run02_j1_alone_never_selected(v2_board):
    """对抗候选单独成批：整批无可行解（纯 R5 → UNKNOWN），best 恒为 None。"""
    adv = _cand("C-ADV-RUN02-J1", {"P5": J1_ROUTE}, {"P5": "F.Cu"},
                arm="no-principle")
    r = select_best(v2_board, [adv])
    assert r["best"] is None
    assert r["verdict"] in ("UNSAT", "UNKNOWN") and r["verdict"] == "UNKNOWN"
    assert r["ledger"]["rejected"] == 1


# ---------------------------------------------------------------- 理念账本骨架（§3.8 六问归类）

REGISTRY_SIX = ["PR-slot-right", "PR-layer-detour", "PR-aggressive-slot",
                "PR-low-prio", "PR-high-prio", "PR-idle"]


def test_principle_ledger_six_way_classification(v2_board):
    """生效/致淘汰/冲突裁决/无可观测影响四态：由 generation_trace 与滤除记录自动归类。"""
    board = copy.deepcopy(v2_board)
    board["principle_registry"] = [{"principle_id": pid} for pid in REGISTRY_SIX]
    c1 = _cand("C-001", {"P3": P3_B_ROUTE, "P5": _p5_route(35.0)},
               {"P3": "B.Cu", "P5": "F.Cu"},
               trace=[{"principle_id": "PR-slot-right", "priority": 30},
                      "PR-layer-detour"])                  # 可行最优 → 生效
    c2 = _cand("C-002", {"P5": _p5_route(33.0)}, {"P5": "F.Cu"},
               trace=["PR-aggressive-slot"])               # DRC 滤除单留痕 → 致淘汰
    c3 = _cand("C-003", {"P5": _p5_route(34.0)}, {"P5": "F.Cu"},
               trace=[{"principle_id": "PR-low-prio", "priority": 10},
                      {"principle_id": "PR-high-prio", "priority": 20}])
    r = select_best(board, [c1, c2, c3])
    assert r["verdict"] == "SAT"
    ledger = {e["principle_id"]: e for e in r["ledger"]["principle_ledger"]}
    for entry in ledger.values():
        assert set(entry) == {"principle_id", "status", "evidence"}
        assert entry["evidence"]
    assert ledger["PR-slot-right"]["status"] == "生效"
    assert ledger["PR-layer-detour"]["status"] == "生效"
    assert ledger["PR-aggressive-slot"]["status"] == "致淘汰"
    assert ledger["PR-high-prio"]["status"] == "致淘汰"
    assert ledger["PR-low-prio"]["status"] == "冲突裁决"
    assert "让位" in ledger["PR-low-prio"]["evidence"]      # priority loser 注记
    assert ledger["PR-idle"]["status"] == "无可观测影响"


def test_principle_ledger_ignored_empty_trace(v2_board):
    """被忽略：principle 臂候选留痕为空 → 注册表理念记「被忽略」。"""
    board = copy.deepcopy(v2_board)
    board["principle_registry"] = [{"principle_id": "PR-unused"}]
    c = good_a("C-001")                              # arm=principle 且无 generation_trace
    assert "generation_trace" not in c
    r = select_best(board, [c])
    assert r["verdict"] == "SAT"
    ledger = {e["principle_id"]: e for e in r["ledger"]["principle_ledger"]}
    assert ledger["PR-unused"]["status"] == "被忽略"
    assert "C-001" in ledger["PR-unused"]["evidence"]


def test_principle_ledger_insufficient_on_unknown_batch(v2_board):
    """依据不足：无可行候选、无 principle 臂对照、注册表理念无留痕。"""
    board = copy.deepcopy(v2_board)
    board["principle_registry"] = [{"principle_id": "PR-z"}]
    cands = [
        _cand("C-UNK-1", {"P3": [[16.0, 4.0], [16.0, 36.0]]}, {"P3": "F.Cu"},
              arm="no-principle"),
        _cand("C-UNK-2", {"P5": _p5_route(34.0)}, {"P5": "F.Cu"},
              arm="no-principle"),
    ]
    r = select_best(board, cands)
    assert r["verdict"] == "UNKNOWN"
    ledger = {e["principle_id"]: e for e in r["ledger"]["principle_ledger"]}
    assert ledger["PR-z"]["status"] == "依据不足"


def test_principle_ledger_real_planner_chain_not_all_ignored():
    """真实链合同缝回归门：load_board_file → compile_board → plan_candidates
    principle 臂 → select_best。planner 留痕形态（rule/freedom/effect，无 priority）
    必须被账本消费——注册表理念出现 生效/致淘汰 等真实归类，而非留痕解析失败全记
    「被忽略」（demo-01 principle 臂为容量不可行单候选 → 致淘汰/冲突裁决在案）。"""
    board = load_board_file(DEMO01_BOARD)
    artifact, _ = compile_board(board)
    cands = plan_candidates(board, artifact, arm="principle")
    assert cands
    r = select_best(board, cands)
    statuses = {e["principle_id"]: e["status"]
                for e in r["ledger"]["principle_ledger"]}
    assert set(statuses) == {p["principle_id"] for p in board["principle_registry"]}
    assert set(statuses.values()) != {"被忽略"}     # 缝修复前此处恒全「被忽略」
    assert ("生效" in statuses.values()) or ("致淘汰" in statuses.values())


def test_principle_ledger_priority_lookup_from_registry(v2_board):
    """priority 查表机制：planner 形态留痕（rule 键）不带 priority 时按板
    principle_registry 查 priority——在册取其值（loser 注记按查表值让位），条目缺
    priority 键或理念不在册 → 0 兜底不炸（同批全 0 时并列致淘汰）。"""
    board = copy.deepcopy(v2_board)
    board["principle_registry"] = [
        {"principle_id": "PR-hi", "priority": 20},
        {"principle_id": "PR-lo", "priority": 10},
        {"principle_id": "PR-noprio"},               # 在册但无 priority 键 → 0
    ]

    def planner_trace(*pids):
        return [{"rule": pid, "freedom": "ordering", "effect": "e"} for pid in pids]

    c_hi_lo = _cand("C-HILO", {"P5": _p5_route(33.0)}, {"P5": "F.Cu"},
                    trace=planner_trace("PR-hi", "PR-lo"))       # DRC 滤除批一
    c_nop = _cand("C-NOP", {"P5": _p5_route(33.0)}, {"P5": "F.Cu"},
                  trace=planner_trace("PR-noprio", "PR-ghost"))  # PR-ghost 不在册
    r = select_best(board, [c_hi_lo, c_nop])
    ledger = {e["principle_id"]: e for e in r["ledger"]["principle_ledger"]}
    assert ledger["PR-hi"]["status"] == "致淘汰"            # 查表 20 = 批内最高
    assert ledger["PR-lo"]["status"] == "冲突裁决"
    assert "让位" in ledger["PR-lo"]["evidence"]
    assert "10" in ledger["PR-lo"]["evidence"] \
        and "20" in ledger["PR-lo"]["evidence"]             # 注记用查表到的 priority
    assert ledger["PR-noprio"]["status"] == "致淘汰"        # 缺键 0 兜底（0 = 批内最高）
    assert ledger["PR-ghost"]["status"] == "致淘汰"         # 不在册 0 兜底不炸


# ---------------------------------------------------------------- 确定性与 staging 卫生

def test_double_run_byte_equality(v2_board, tmp_path):
    """确定性硬测试：同输入双跑结果字节等；落盘件双跑字节等（UNSAT 批含证书件）。"""
    cands = [good_a("C-001"), good_b("C-002"),
             _cand("C-ADV-RUN02-J1", {"P5": J1_ROUTE}, {"P5": "F.Cu"},
                   arm="no-principle")]
    r1 = select_best(v2_board, cands)
    r2 = select_best(v2_board, cands)
    assert canonical.canonical_json(r1) == canonical.canonical_json(r2)
    out1, out2 = str(tmp_path / "out1"), str(tmp_path / "out2")
    select_best(v2_board, unsat_pair(), out_dir=out1)
    select_best(v2_board, unsat_pair(), out_dir=out2)
    bid = v2_board["board_id"]
    for name in ("%s.selection.json" % bid, "%s.selection-ledger.json" % bid,
                 "%s.failcert.json" % bid):
        with open(os.path.join(out1, "%s.selection" % bid, name), "rb") as f:
            b1 = f.read()
        with open(os.path.join(out2, "%s.selection" % bid, name), "rb") as f:
            b2 = f.read()
        assert b1 == b2, name


def test_staging_recover_after_commit_no_residue(v2_board, tmp_path):
    """提交后 staging 无残留；recover 无事可清；final 产物 append-only 可列。"""
    out = str(tmp_path / "out")
    select_best(v2_board, [good_a("C-001"), good_b("C-002")], out_dir=out)
    staging_root = os.path.join(out, "_staging")
    assert staging.assert_no_residue(staging_root)
    assert staging.recover(staging_root, out) == []
    bid = v2_board["board_id"]
    files = staging.evidence_list(out)
    assert "%s.selection/%s.selection.json" % (bid, bid) in files
    assert "%s.selection/%s.selection-ledger.json" % (bid, bid) in files
    assert not any(f.endswith(".failcert.json") for f in files)   # SAT 无证书件
