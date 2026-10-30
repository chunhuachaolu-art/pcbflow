# -*- coding: utf-8 -*-
"""升级件④测试（2026-09-14；D 层复现夹具三件 + 零长缝专项）。

覆盖（对照 DISPATCH-LOG P5② 三类 exec FAILED 失败模式，失败模式只从任务书
描述经 D 层夹具复现，零 A 层接触）：
- 模式A「端点退化重合」：d4-degenerate.kicad_pcb（两单 pad unconnected 占位网
  + SIG 直连线穿过退化点）——改造前 FAILED after 5 attempts: 端点退化重合
  （低层 _entries_from_runs 行为钉死）；改造后 trivially satisfied 零长条目、
  全链 feasible；零长缝的「零铜展宽=无间距交互」专项（缝摘除即 R5 infeasible，
  证明测试承重）；
- 模式B「A* 搜索空间耗尽（栅格分辨率）」：d4-tight-door（1.15mm 门、中心线
  窗口 (10.83,10.98) 避开 0.25/0.0625 两种相位栅格）——改造前 5 变体全耗尽
  （FAILED，日志留痕=改造前行为）；改造后尝试 6（pitch=0.125）解封；
- 模式C「焊盘逃逸被封」：d4-escape-seal（端点邻域封坏环 + 1.1mm 薄门）——
  改造前同上全耗尽；改造后细化阶梯解封；尝试阶梯形状/确定性单测；
- 耗尽根因分类（exhaustion-cause）endpoint-sealed 分支（双盒全封板，全尝试
  瞬时失败，套件零负担）；
- 双跑 canonical 字节等（三夹具全量）。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.adapters.kicad_adapter import convert_bytes_with_report  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5 import executor as _executor_mod  # noqa: E402  (V5-EXECUTOR-ENG-R1 翻新：SC-1 判定器关停注入面)
from v5.executor import (  # noqa: E402
    _ATTEMPT_VARIANTS, _attempt_label, _attempt_plans, _entries_from_runs,
    _Context, execute_candidate)
from v5.route_check import (ROUTES_SCHEMA_VERSION,  # noqa: E402
                            RouteCheckError, check_routes, validate_routes)

BOARDS = os.path.join(ROOT, "boards", "d")

_CACHE = {}


def _load_board_json(bid):
    if bid not in _CACHE:
        with open(os.path.join(BOARDS, "%s.board.v1.json" % bid),
                  encoding="utf-8") as f:
            _CACHE[bid] = load_board(json.load(f))
    return _CACHE[bid]


def _load_degenerate_board():
    key = ("kicad", "d4-degenerate")
    if key not in _CACHE:
        with open(os.path.join(BOARDS, "d4-degenerate.kicad_pcb"),
                  "rb") as f:
            data = f.read()
        board, report = convert_bytes_with_report(
            data, "d4-degenerate", "synthetic://d4-degenerate")
        _CACHE[key] = (board, report)
    return _CACHE[key]


def _cand_for(board, layers=None):
    parts = [p["partition_id"] for p in board["partitions"]]
    lay = layers or {p["partition_id"]: p["layer_policy"]
                     for p in board["partitions"]}
    return {"candidate_id": "C-T4", "arm": "no-principle",
            "provenance": {"generator": "hand", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": parts, "layer_assignment": lay,
            "polylines": {}, "generation_trace": []}


def _exec(board, layers=None):
    return execute_candidate(board, _cand_for(board, layers))


# ---------------------------------------------------------------- 模式A

def test_mode_a_degenerate_trivially_satisfied():
    """退化分区 = trivially satisfied：零长条目 + 全链 feasible（改造后行为）。"""
    board, report = _load_degenerate_board()
    assert report["degenerate_partitions"] == 2   # adapter 增计披露
    res = _exec(board, layers={p["partition_id"]: "F.Cu"
                               for p in board["partitions"]})
    assert res["verdict"] == "ROUTED" and res["routes"] is not None
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["unconnected-(U2-Pad11)"]["status"] == "degenerate"
    assert by_net["unconnected-(U3-Pad2)"]["status"] == "degenerate"
    assert by_net["SIG"]["status"] == "routed"
    degenerate_logs = [l for l in res["negotiation_log"]
                       if "degenerate: zero-length partition trivially satisfied" in l]
    assert len(degenerate_logs) == 2
    # 零长条目合同：polyline=[pt,pt]、层=候选指派层、无孔、宽=planned_width
    zero = [e for e in res["routes"]["routes"]
            if e["net_id"] == "unconnected-(U2-Pad11)"]
    assert len(zero) == 1
    entry = zero[0]
    assert entry["polyline"] == [[10.0, 10.0], [10.0, 10.0]]
    assert entry["layer"] == "F.Cu"
    assert entry["transition_vias"] == [] and entry["return_vias"] == []
    assert entry["width"] == 0.2
    validate_routes(board, res["routes"])   # 工件校验（fail-closed）不拒零长
    assert check_routes(board, res["routes"])["feasible"] is True


def test_mode_a_low_level_degenerate_reason_preserved():
    """改造前行为钉死：低层 _entries_from_runs 对重合端点仍返回
    「端点退化重合」（模式A 处置只发生在 execute_candidate 编排层）。"""
    board, _report = _load_degenerate_board()
    ctx = _Context(board)
    packed, reason = _entries_from_runs(
        ctx, "PT-unconnected-_U2-Pad11_", "unconnected-(U2-Pad11)", 0.2,
        [10.0, 10.0], [10.0, 10.0], [((10.0, 10.0), "F.Cu")], [])
    assert packed is None and reason == "端点退化重合"


def test_mode_a_zero_copper_seam_is_load_bearing():
    """零长缝专项（零铜展宽=无间距交互）：同一物理格局下——退化点 (10,12) 上
   有一条直连路线 SIG（gap=0）——零长 entry 判 feasible（不构造铜）；把该分区
    改成 0.01mm 微段（非退化、链审计通过）即 R5 违例 infeasible，证明可行判定
    确实依赖本缝而非巧合。"""
    def board_with(endpoint_pair, entry_pts):
        board = {
            "schema_version": "v5.board.v1",
            "board_id": "d4-seam-probe",
            "stackup": [{"id": "F.Cu", "kind": "signal",
                         "preferred_direction": "any", "available": True}],
            "workspace": {"x_min": 0.0, "y_min": 0.0,
                          "x_max": 20.0, "y_max": 20.0},
            "zones": [],
            "partitions": [
                _part("PT-DEG", endpoint_pair[0], endpoint_pair[1]),
                _part("PT-ROUTE", (2.0, 12.0), (18.0, 12.0)),
            ],
            "nets": [
                {"net_id": "DEG", "net_class": "MISC",
                 "partitions": ["PT-DEG"]},
                {"net_id": "ROUTE", "net_class": "MISC",
                 "partitions": ["PT-ROUTE"]},
            ],
            "hard_rules": {
                "R1": {"floor_mm": 0.3, "k_a": 0.4},
                "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
                "R3": {"unsplittable": True},
                "R4": {"max_distance_mm": 2.0, "return_via_required": True},
                "R5": {"min_clearance_mm": 0.5},
                "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
            },
            "principle_registry": [],
            "provenance": {"source_type": "synthetic", "adapter": "hand",
                           "source_uri": "tests/test_upgrade4_robustness.py#seam",
                           "source_sha256": "0" * 64},
        }
        board["provenance"]["board_sha256"] = compute_board_sha256(board)
        board = load_board(board)
        sha = board["provenance"]["board_sha256"]
        doc = {"schema_version": ROUTES_SCHEMA_VERSION,
               "board_id": "d4-seam-probe", "board_sha256": sha,
               "routes": [
                   {"partition_id": "PT-DEG", "net_id": "DEG", "layer": "F.Cu",
                    "polyline": [list(p) for p in entry_pts], "width": 0.2,
                    "transition_vias": [], "return_vias": []},
                   {"partition_id": "PT-ROUTE", "net_id": "ROUTE",
                    "layer": "F.Cu",
                    "polyline": [[2.0, 12.0], [18.0, 12.0]], "width": 0.2,
                    "transition_vias": [], "return_vias": []},
               ],
               "negotiation_log": ["t"],
               "provenance": {"generator": "v5.executor/0.1.0",
                              "board_sha256": sha}}
        return board, doc

    # 零长：退化分区 trivially satisfied，SIG 直连线穿过 (10,12) 仍 feasible
    board0, doc0 = board_with([[10.0, 12.0], [10.0, 12.0]],
                              [[10.0, 12.0], [10.0, 12.0]])
    validate_routes(board0, doc0)
    assert check_routes(board0, doc0)["feasible"] is True
    # 对照：0.01mm 微段（非退化、链审计通过）→ R5 违例 infeasible
    board1, doc1 = board_with([[10.0, 12.0], [10.01, 12.0]],
                              [[10.0, 12.0], [10.01, 12.0]])
    validate_routes(board1, doc1)
    rep = check_routes(board1, doc1)
    assert rep["feasible"] is False
    assert any(v["rule"] == "R5" for v in rep["attributed_violations"])


def test_mode_a_double_run_byte_equal():
    """确定性红线：模式A 板同输入双跑 canonical 字节等。"""
    board, _report = _load_degenerate_board()
    layers = {p["partition_id"]: "F.Cu" for p in board["partitions"]}
    a = canonical.canonical_json(_exec(board, layers))
    b = canonical.canonical_json(_exec(board, layers))
    assert a == b


# ---------------------------------------------------------------- 模式B

def test_mode_b_tight_door_before_and_after():
    """模式B：改造前 5 变体全耗尽（日志留痕=改造前行为字符串），改造后
    细化栅格阶段（pitch=0.125）解封且全链 feasible。"""
    board = _load_board_json("d4-tight-door")
    res = _exec(board)
    assert res["verdict"] == "ROUTED" and res["routes"] is not None
    log = res["negotiation_log"]
    # 改造前行为留痕：基线阶段前两尝试的失败串（含旧格式逐字节兼容）
    assert log[0] == ("net=SIG partition=PT-SIG attempt=1 "
                      "variant=prefer+r2-near+via-priced failed: "
                      "A* 搜索空间耗尽（障碍/容量/敏感约束下无路）")
    assert log[1] == ("net=SIG partition=PT-SIG attempt=2 "
                      "variant=prefer+r2-overlap_free+via-priced failed: "
                      "A* 搜索空间耗尽（障碍/容量/敏感约束下无路）")
    assert sum(1 for l in log if l.endswith("A* 搜索空间耗尽（障碍/容量/敏感约束下无路）")
               and "pitch=" not in l and "escape=" not in l) == 5
    # 改造后：细化栅格解封
    committed = [l for l in log if "committed attempt" in l]
    assert any("pitch=0.125" in l for l in committed)
    assert res["per_net"][0]["attempts"] == 6
    assert check_routes(board, res["routes"])["feasible"] is True
    # 双跑字节等
    a = canonical.canonical_json(res)
    b = canonical.canonical_json(_exec(board))
    assert a == b


# ---------------------------------------------------------------- 模式C

def test_mode_c_escape_seal_before_and_after():
    """模式C：焊盘邻域封坏环 + 1.1mm 薄门——改造前 5 变体全耗尽（FAILED），
    改造后细化阶梯从门中解封，全链 feasible。"""
    board = _load_board_json("d4-escape-seal")
    res = _exec(board)
    assert res["verdict"] == "ROUTED" and res["routes"] is not None
    log = res["negotiation_log"]
    assert log[0] == ("net=SIG partition=PT-SIG attempt=1 "
                      "variant=prefer+r2-near+via-priced failed: "
                      "A* 搜索空间耗尽（障碍/容量/敏感约束下无路）")
    base_fail = [l for l in log
                 if "failed: A* 搜索空间耗尽" in l and "pitch=" not in l
                 and "escape=" not in l]
    assert len(base_fail) == 5   # 基线 5 变体全灭 = 改造前行为
    committed = [l for l in log if "committed attempt" in l]
    assert any("pitch=0.125" in l for l in committed)
    assert check_routes(board, res["routes"])["feasible"] is True
    a = canonical.canonical_json(res)
    b = canonical.canonical_json(_exec(board))
    assert a == b


def test_attempt_ladder_shape_and_determinism():
    """尝试阶梯合同（升级件⑤ F4a/F4b 再分配后；既有 ④ 形状钉的更新版，
    披露见任务汇报）：计划数 = 106（5 基线 + 5 细化@0.125 + 40+40 逃逸 +
    4 细化@0.0625 + 12 逃逸@0.0625）；位 1..10 与 0.3.0 逐位不动；阶段序
    追加在既有阶段之后；逃逸块 r3 仅 4 轴向（8→4 修剪）、保留计划相对序
    不变；细档逃逸起点侧 r1×8 向、终点侧 r1×4 轴向；重复生成逐项相等。"""
    plans = _attempt_plans()
    assert len(plans) == 106
    assert [p[2] for p in plans[:10]] == [None] * 10
    assert [p[1] for p in plans[:5]] == [1.0] * 5
    assert [p[1] for p in plans[5:10]] == [0.5] * 5
    dirs8 = [(1, 0), (-1, 0), (0, 1), (0, -1),
             (1, 1), (1, -1), (-1, 1), (-1, -1)]
    dirs4 = dirs8[:4]
    # 逃逸@0.25mm 块（位 11-50）与逃逸@0.125mm 块（位 51-90）：先起点后
    # 终点；每侧 r1×8、r2×8、r3×4（F4a 修剪）
    for block in (plans[10:50], plans[50:90]):
        starts, goals = block[:20], block[20:]
        for side_block, side in ((starts, "start"), (goals, "goal")):
            for k, (_v, sc, esc) in enumerate(side_block):
                rad = k // 8 + 1
                dirs = dirs8 if rad < 3 else dirs4
                dx, dy = dirs[k % 8]
                assert sc == block[0][1]
                assert esc == (side, (dx, dy), rad)
    # F4a 细化@0.0625（位 91-94）：escape=None、前 4 变体（无 lane-shift）
    fine_refine = plans[90:94]
    assert all(p[1] == 0.25 and p[2] is None for p in fine_refine)
    assert [p[0] for p in fine_refine] == list(_ATTEMPT_VARIANTS[:4])
    # F4b 细档逃逸（位 95-106）：起点侧 r1×8 向全、终点侧 r1×4 轴向
    fine_esc = plans[94:]
    assert [p[2] for p in fine_esc] == \
        [("start", d, 1) for d in dirs8] + [("goal", d, 1) for d in dirs4]
    assert all(p[1] == 0.25 for p in fine_esc)
    assert plans == _attempt_plans()
    # 逃逸计划固定用最宽容变体（no-prefer/overlap_free/via-free）；
    # 细化档（位 91-94）用前 4 变体（非逃逸变体）
    esc_positions = list(range(10, 90)) + list(range(94, 106))
    assert all(plans[i][0] == {"prefer": False, "r2": "overlap_free",
                               "via_cost": 0.0, "phase": 0.0}
               for i in esc_positions)
    assert _attempt_label(plans[10][0]) == "no-prefer+r2-overlap_free+via-free"


def test_exhaustion_cause_endpoint_sealed_logged(monkeypatch):
    """耗尽根因分类：双盒全封板（两端点吸附节点出边全封）所有尝试瞬时失败，
    FAILED 日志追加 exhaustion-cause=endpoint-sealed。

    V5-EXECUTOR-ENG-R1 翻新披露（2026-10-02）：本板两端点被四面
    ptype=ROUTED 固定铜墙盒封（0.35/0.45mm < R5），属 W-1 SC-1 可证明
    构造无解面——默认路径已事前短路（sealed-short-circuit、attempts=0、
    五行证据链，见 tests/test_executor_shortcircuit.py）；endpoint-sealed
    事后归因类钉值改以判定器关停（_preflight_seal_shortcircuit no-op）
    跑原断言（该归因类继续服务非密封类穷举失败板）。"""
    board = _double_sealed_board()
    # 默认路径（0.9.0）：SC-1 事前短路收口
    res = _exec(board)
    assert res["verdict"] == "FAILED" and res["routes"] is None
    log = res["negotiation_log"]
    assert any("exhaustion-cause=sealed-short-circuit" in l for l in log)
    assert res["per_net"][0]["attempts"] == 0
    assert not [l for l in log if "escape=" in l]
    # 判定器关停（0.8.0 穷举路径）：原钉值逐字保留
    monkeypatch.setattr(_executor_mod, "_preflight_seal_shortcircuit",
                        lambda *a, **k: None)
    res = _exec(board)
    assert res["verdict"] == "FAILED" and res["routes"] is None
    log = res["negotiation_log"]
    causes = [l for l in log if "exhaustion-cause=" in l]
    assert len(causes) == 1
    assert "exhaustion-cause=endpoint-sealed" in causes[0]
    # 阶梯全量执行：attempts=106（F4 再分配后仍 106：5 基线 + 5 细化 + 40+40
    # 逃逸 + 4 细化@0.0625 + 12 逃逸@0.0625，零吸附去重）；
    # 92 条逃逸尝试行逐条入日志（策略标签 escape=start|goal:(dx,dy)r<k>；
    # F4a 修剪：r3 大位移档 8 向→4 轴向、细档逃逸 12 计划，96→92）
    assert res["per_net"][0]["attempts"] == 106
    esc = [l for l in log if "escape=" in l]
    assert len(esc) == 92
    assert "escape=start:(+1,+0)r1" in esc[0]
    assert "escape=goal:(+0,-1)r1" in esc[-1]
    assert all("failed: A* 搜索空间耗尽（障碍/容量/敏感约束下无路）" in l
               for l in esc)


def _part(pid, a, b, ptype="MISC", width=0.2, note=None):
    p = {"partition_id": pid, "ptype": ptype, "layer_policy": "F.Cu",
         "planned_width": width, "current_a": 0,
         "geometry": {"endpoints": [list(a), list(b)]},
         "speed_class": "low_speed",
         "width_prior": {"w_min": width, "w_max": 1.0}}
    if note is not None:
        p["note"] = note
    return p


def _double_sealed_board():
    """两端点各自被 0.45 距离四墙盒封死（吸附节点 8 出边全封）——所有尝试
    从首个节点即耗尽（套件零负担），专供 exhaustion-cause 分类断言。"""
    walls = [
        ("PT-AL", (0.55, 0.55), (0.55, 1.45)),
        ("PT-AR", (1.45, 0.55), (1.45, 1.45)),
        ("PT-AB", (0.55, 0.55), (1.45, 0.55)),
        ("PT-AT", (0.55, 1.45), (1.45, 1.45)),
        ("PT-BL", (4.55, 4.55), (4.55, 5.45)),
        ("PT-BR", (5.45, 4.55), (5.45, 5.45)),
        ("PT-BB", (4.55, 4.55), (5.45, 4.55)),
        ("PT-BT", (4.55, 5.45), (5.45, 5.45)),
    ]
    partitions = [_part("PT-SIG", (1.0, 1.1), (5.0, 5.0))]
    nets = [{"net_id": "SIG", "net_class": "MISC", "partitions": ["PT-SIG"]}]
    for k, (pid, p1, p2) in enumerate(walls):
        partitions.append(_part(pid, p1, p2, ptype="ROUTED",
                                note="fixture: seal box wall"))
        nets.append({"net_id": "W%d" % k, "net_class": "MISC",
                     "partitions": [pid]})
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "d4-double-sealed",
        "stackup": [{"id": "F.Cu", "kind": "signal",
                     "preferred_direction": "any", "available": True}],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 6.0, "y_max": 6.0},
        "zones": [],
        "partitions": partitions,
        "nets": nets,
        "hard_rules": {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri": "tests/test_upgrade4_robustness.py#double-sealed",
                       "source_sha256": "0" * 64},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return load_board(board)


# ---------------------------------------------------------------- 零长缝

def test_zero_length_entry_rejected_for_non_degenerate_partition():
    """零长缝边界：非退化分区（两端点不同）的零长 entry 仍被 validate_routes
    链审计拒绝（首末点须恰为分区两端点）——缝不放松既有 fail-closed。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "d4-seam-guard",
        "stackup": [{"id": "F.Cu", "kind": "signal",
                     "preferred_direction": "any", "available": True}],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 20.0},
        "zones": [],
        "partitions": [_part("PT-N", (2.0, 5.0), (18.0, 5.0))],
        "nets": [{"net_id": "N", "net_class": "MISC", "partitions": ["PT-N"]}],
        "hard_rules": {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri": "tests/test_upgrade4_robustness.py#seam-guard",
                       "source_sha256": "0" * 64},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    board = load_board(board)
    sha = board["provenance"]["board_sha256"]
    doc = {"schema_version": ROUTES_SCHEMA_VERSION, "board_id": "d4-seam-guard",
           "board_sha256": sha,
           "routes": [{"partition_id": "PT-N", "net_id": "N", "layer": "F.Cu",
                       "polyline": [[10.0, 5.0], [10.0, 5.0]], "width": 0.2,
                       "transition_vias": [], "return_vias": []}],
           "negotiation_log": ["t"],
           "provenance": {"generator": "v5.executor/0.1.0", "board_sha256": sha}}
    with pytest.raises(RouteCheckError):
        validate_routes(board, doc)
