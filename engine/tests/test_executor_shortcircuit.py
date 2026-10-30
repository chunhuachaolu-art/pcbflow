# -*- coding: utf-8 -*-
"""V5-EXECUTOR-ENG-R1 W-1 SC-1 短路正/反钉（executor 0.9.0）。

DESIGN-DECISION §5 测试计划 A 组：
  A1 手工最小密封板正钉（五行证据链+per_net 键集+attempts=0）；
  A2 syn-u01..u10 逐板首候选短路+sidecar witness 逐板吻合；
  A3 syn-r01..r10 判定器零触发 + syn-r01 全量 execute=ROUTED 且 log 零
     sealed-short-circuit + 零触发=零 log 增量（与不设判定器基线逐字节等）；
  A4 对抗板 fixture（V1 误杀实证=永久回归钉）：修后判据不触发+0.9.0 ROUTED
     +端点精确坐标折线（M3 机制保持）；
  A5 误杀边界五钉（子集层/小垫/本网/同网异分区/keepout+孔带无铜封）；
  A6 附着闭包构造恒等钉+阶梯常量值钉；
  A7 cross-check 弃权（mismatch → 不短路+披露行）；
  A8 syn-u01 双跑 canonical 字节等。

fixture 只读面：boards/synth-r1（A2/A3/A8）、out/v5-p5/exec-eng-r1/probe/
adv-board.json（A4）；最小板骨架的 hard_rules/principle_registry 自
syn-u09.board.v1.json 只读克隆（probe 同源）。
"""
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import load_board  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.executor import (  # noqa: E402
    _BoardView, _Context, _attachment_closure, _escape_anchor,
    _ladder_bound_partitions, _preflight_seal_shortcircuit,
    _seal_survey_rows, execute_candidate)
from v5 import executor as EX  # noqa: E402
from v5.planner import plan_candidates  # noqa: E402
from v5.selection import select_best  # noqa: E402

SYNTH = os.path.join(ROOT, "boards", "synth-r1")
ADV_FIXTURE = os.path.join(ROOT, "out", "v5-p5", "exec-eng-r1", "probe",
                           "adv-board.json")
# sidecar witness 端点定值（DESIGN §9 R2 读数锚：u01/03/05/06/08/10=e0、
# u02/04/07/09=e1）
U_ENDPOINT_PIN = {"syn-u01": 0, "syn-u02": 1, "syn-u03": 0, "syn-u04": 1,
                  "syn-u05": 0, "syn-u06": 0, "syn-u07": 1, "syn-u08": 0,
                  "syn-u09": 1, "syn-u10": 0}
_PER_NET_KEYS = {"partition_id", "net_id", "status", "attempts", "negotiated",
                 "vias", "length_mm", "width_mm", "layers"}


def _load_synth(bid):
    with open(os.path.join(SYNTH, "%s.board.v1.json" % bid),
              encoding="utf-8") as f:
        return load_board(json.load(f))


def _sidecar(bid):
    with open(os.path.join(SYNTH, "%s.sidecar.json" % bid),
              encoding="utf-8") as f:
        return json.load(f)


def _cand(board, layer=None):
    layer = layer or board["stackup"][0]["id"]
    return {"route_order": [p["partition_id"] for p in board["partitions"]],
            "layer_assignment": {p["partition_id"]: layer
                                 for p in board["partitions"]}}


def _first_candidate(board):
    """首候选（runner 轮换口径：selection best 优先，best=None 取注册序
    首个——A2 0.8.0 台账 tried 首位语义）。"""
    c_art, _fp = compile_board(board)
    cands = plan_candidates(board, c_art)
    res = select_best(board, cands)
    best = res.get("best")
    if best is not None:
        for i, c in enumerate(cands):
            if c == best:
                return cands[i]
    return cands[0]


def _skeleton(board_id):
    """最小板骨架（hard_rules/principle_registry 自 syn-u09 只读克隆；
    probe 对抗板同源）。工作区 8.0-12.0×8.5-12.0、2 信号层、无孔无 keepout。"""
    with open(os.path.join(SYNTH, "syn-u09.board.v1.json"),
              encoding="utf-8") as f:
        src = json.load(f)
    return {
        "schema_version": src["schema_version"],
        "board_id": board_id,
        "workspace": {"x_min": 8.0, "y_min": 8.5, "x_max": 12.0,
                      "y_max": 12.0},
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "available": True,
             "preferred_direction": "h"},
            {"id": "In1.Cu", "kind": "signal", "available": True,
             "preferred_direction": "v"}],
        "hard_rules": src["hard_rules"],
        "principle_registry": src["principle_registry"],
        "holes": [], "zones": [],
        "nets": [], "partitions": [],
    }


def _route_partition(board, pid, a, b, net="N1"):
    board["nets"].append({"net_id": net, "net_class": "MISC",
                          "partitions": [pid]})
    board["partitions"].append({
        "partition_id": pid, "ptype": "MISC", "net_id": None,
        "layer_policy": "F.Cu", "planned_width": 0.2, "current_a": 0.0,
        "speed_class": "low_speed",
        "width_prior": {"w_min": 0.2, "w_max": 0.4},
        "geometry": {"endpoints": [[float(a[0]), float(a[1])],
                                   [float(b[0]), float(b[1])]]}})


def _pad_partition(board, pid, center, size_mm=(2.6, 2.6), layers="all",
                   net="NSEAL"):
    """密封垫载体（退化分区+pad_terminals；probe 对抗板同款形态）。"""
    board["nets"].append({"net_id": net, "net_class": "MISC",
                          "partitions": [pid]})
    board["partitions"].append({
        "partition_id": pid, "ptype": "MISC", "net_id": None,
        "layer_policy": "F.Cu", "planned_width": 0.2, "current_a": 0.0,
        "speed_class": "low_speed",
        "width_prior": {"w_min": 0.2, "w_max": 0.4},
        "geometry": {"endpoints": [[float(center[0]), float(center[1])],
                                   [float(center[0]), float(center[1])]],
                     "pad_terminals": [{"endpoint": 0, "layers": layers,
                                        "shape": "rect",
                                        "size_mm": [size_mm[0],
                                                    size_mm[1]]}]}})


def _minimal_sealed_board():
    """A1 最小板：N1/P1 两端点 (9.0,10.0)→(11.0,10.0)；goal 端全层异网
    矩形垫（半宽 1.3mm > 最大栅格位移 0.75+R5 裕量）封死 S(b) 全点位；
    start 端精确点距垫 0.7mm 开放（单端点密封=SC-1 充分条件）。"""
    board = _skeleton("sc1-minimal")
    _route_partition(board, "P1", (9.0, 10.0), (11.0, 10.0), net="N1")
    _pad_partition(board, "PSEAL", (11.0, 10.0), size_mm=(2.6, 2.6),
                   layers="all", net="NSEAL")
    return board


def _survey(board, cand):
    view = _BoardView(board)
    route_order, _assign = EX._validate_candidate(board, cand)
    return _seal_survey_rows(_Context(board), route_order)


# ------------------------------------------------ A1 正钉（最小板）

def test_sc1_positive_minimal():
    board = _minimal_sealed_board()
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "FAILED"
    assert res["routes"] is None
    assert len(res["per_net"]) == 1
    pn = res["per_net"][0]
    assert pn["partition_id"] == "P1" and pn["net_id"] == "N1"
    assert pn["status"] == "failed" and pn["attempts"] == 0
    assert pn["negotiated"] is False and pn["vias"] == 0
    assert pn["length_mm"] == 0.0 and pn["layers"] == []
    assert set(pn) == _PER_NET_KEYS   # 键集与穷举失败条目（:2563-2567）同构
    log = res["negotiation_log"]
    assert len(log) == 5   # 五行证据链（零 attempt 行）
    assert log[0] == ("partition=P1 preflight-seal-survey: ladder_partitions=1"
                      "（fixed-only-world，零 route 铜/零孔带/零板边带/零 "
                      "keepout 计入；S=grid+exact）")
    assert log[1].startswith("net=N1 partition=P1 FAILED after 0 attempts: "
                             "constructive-unroutable（")
    assert log[2].startswith("net=N1 partition=P1 "
                             "exhaustion-cause=sealed-short-circuit（")
    assert log[3].startswith("net=N1 partition=P1 geom-secondary=")
    m = re.match(r"net=N1 partition=P1 short-circuit-basis: "
                 r"sealed_endpoint=e1 attachment_sealed=(\d+)/\1 "
                 r"points=grid:(\d+)\+exact:1 layers=all sealing_cids=.+ "
                 r"cross_check=edge_blocked_agree=(\d+)/\1 "
                 r"immutable=rip_net-scope-fixed-not-removable$", log[4])
    assert m, log[4]
    # 网格点数+精确 1 = 总点位；层数=2 → pairs=点位×2
    n_pts = int(m.group(2)) + 1
    assert int(m.group(1)) == n_pts * 2
    assert int(m.group(3)) == n_pts * 2


# ------------------------------------------------ A2 u 族正钉（10 板）

@pytest.mark.parametrize("bid", ["syn-u%02d" % i for i in range(1, 11)])
def test_sc1_u_boards_all10(bid):
    board = _load_synth(bid)
    w = _sidecar(bid)["witness"]
    res = execute_candidate(board, _first_candidate(board))
    assert res["verdict"] == "FAILED"
    assert res["per_net"][0]["attempts"] == 0
    text = "\n".join(res["negotiation_log"])
    assert "exhaustion-cause=sealed-short-circuit" in text
    # E-J2 读回口径：cause 行 net/partition 与 sidecar witness 逐板吻合
    m = re.search(r"net=(\S+) partition=(\S+) "
                  r"exhaustion-cause=sealed-short-circuit", text)
    assert m and m.group(1) == w["blocked_net"] \
        and m.group(2) == w["blocked_partition"]
    # basis 行 sealed_endpoint 与 sidecar blocked_endpoint_index 对照
    mb = re.search(r"short-circuit-basis: sealed_endpoint=e(\d) ", text)
    assert mb and int(mb.group(1)) == w["blocked_endpoint_index"] \
        == U_ENDPOINT_PIN[bid]


# ------------------------------------------------ A3 r 族反钉+零 log 增量

def test_sc1_negative_r_boards():
    for i in range(1, 11):
        bid = "syn-r%02d" % i
        board = _load_synth(bid)
        rows = _survey(board, _cand(board))
        assert rows, bid
        assert not [r for r in rows if r["sealed"]], bid
        assert min(r["n_pairs"] - r["sealed_pairs"] for r in rows) >= 2


def test_sc1_negative_r01_execute_zero_log_delta(monkeypatch):
    board = _load_synth("syn-r01")
    cand = _first_candidate(board)
    res = execute_candidate(board, cand)
    assert res["verdict"] == "ROUTED"
    assert not any("sealed-short-circuit" in ln
                   for ln in res["negotiation_log"])
    # 零触发=零 log 增量：与不设判定器的等价基线逐字节相等
    monkeypatch.setattr(EX, "_preflight_seal_shortcircuit",
                        lambda *a, **k: None)
    base = execute_candidate(board, cand)
    assert base["verdict"] == "ROUTED"
    assert canonical.canonical_json(res["negotiation_log"]) == \
        canonical.canonical_json(base["negotiation_log"])
    assert canonical.canonical_json(res["routes"]) == \
        canonical.canonical_json(base["routes"])


# ------------------------------------------------ A4 对抗板（永久回归钉）

def test_sc1_adversarial_fixture():
    """V1 误杀实证板（S_grid 全封而 0.8.0 ROUTED——M3 精确坐标附着）：
    修后判据（S 含端点精确坐标）不触发；0.9.0 保持 ROUTED 且 P1 折线=
    精确端点对（防闭包再退化/防误杀复发）。"""
    with open(ADV_FIXTURE, encoding="utf-8") as f:
        board = json.load(f)
    rows = _survey(board, _cand(board))
    assert not [r for r in rows if r["sealed"]]
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "ROUTED"
    assert not any("sealed-short-circuit" in ln
                   for ln in res["negotiation_log"])
    p1 = [e for e in res["routes"]["routes"] if e["partition_id"] == "P1"]
    assert p1 and p1[0]["polyline"] == [[10.73, 10.09], [10.04, 10.09]]
    pn = [r for r in res["per_net"] if r["partition_id"] == "P1"][0]
    assert pn["status"] == "routed"


# ------------------------------------------------ A5 误杀边界五钉

def test_sc1_boundary_guard_subset_layer():
    board = _skeleton("sc1-b-subset")
    _route_partition(board, "P1", (9.0, 10.0), (11.0, 10.0))
    _pad_partition(board, "PSEAL", (11.0, 10.0), layers=["F.Cu"])
    rows = _survey(board, _cand(board))
    assert not [r for r in rows if r["sealed"]]   # In1.Cu 侧开放 → 不触发


def test_sc1_boundary_guard_pad_too_small():
    board = _skeleton("sc1-b-small")
    _route_partition(board, "P1", (9.0, 10.0), (11.0, 10.0))
    # 半宽 0.25：r3 轴向逃逸锚（0.75mm 位移）距垫面恰 0.75−0.25=0.5=R5
    # → 不入 R5−EPS 封锁 → 逃逸锚出封 → 不触发（宁漏判不误杀）
    _pad_partition(board, "PSEAL", (11.0, 10.0), size_mm=(0.5, 0.5))
    rows = _survey(board, _cand(board))
    assert not [r for r in rows if r["sealed"]]
    goal = [r for r in rows if r["endpoint_index"] == 1][0]
    assert goal["n_pairs"] - goal["sealed_pairs"] > 0


def test_sc1_boundary_guard_own_partition_pad():
    """本网（同分区自带焊盘）all-layer 垫 → 铜跳过豁免 → 不触发。"""
    board = _skeleton("sc1-b-own")
    board["nets"].append({"net_id": "N1", "net_class": "MISC",
                          "partitions": ["P1"]})
    board["partitions"].append({
        "partition_id": "P1", "ptype": "MISC", "net_id": None,
        "layer_policy": "F.Cu", "planned_width": 0.2, "current_a": 0.0,
        "speed_class": "low_speed",
        "width_prior": {"w_min": 0.2, "w_max": 0.4},
        "geometry": {"endpoints": [[9.0, 10.0], [11.0, 10.0]],
                     "pad_terminals": [
                         {"endpoint": 0, "layers": "all", "shape": "rect",
                          "size_mm": [2.6, 2.6]},
                         {"endpoint": 1, "layers": "all", "shape": "rect",
                          "size_mm": [2.6, 2.6]}]}})
    rows = _survey(board, _cand(board))
    assert not [r for r in rows if r["sealed"]]


def test_sc1_boundary_guard_same_net_foreign_partition():
    """同网异分区 all-layer 垫 → net 过滤（ob.cu.net_id==分区网跳过）→
    不触发。"""
    board = _skeleton("sc1-b-samenet")
    _route_partition(board, "P1", (9.0, 10.0), (11.0, 10.0), net="N1")
    _pad_partition(board, "P2", (11.0, 10.0), layers="all", net="N1")
    rows = _survey(board, _cand(board))
    assert not [r for r in rows if r["sealed"]]


def test_sc1_boundary_guard_keepout_and_holes_only():
    """孔带/keepout 独立包围（无铜封）→ 判定器只计 fixed 铜 → 不触发。"""
    board = _skeleton("sc1-b-band")
    _route_partition(board, "P1", (9.0, 10.0), (11.0, 10.0))
    board["zones"] = [{"zone_id": "KO01", "kind": "keepout", "layers": "all",
                       "rect": {"x_min": 10.0, "y_min": 9.0, "x_max": 12.0,
                                "y_max": 11.0}}]
    board["holes"] = [{"pos_mm": [10.0, 10.0], "drill_mm": 0.6}]
    rows = _survey(board, _cand(board))
    assert not [r for r in rows if r["sealed"]]


# ------------------------------------------------ A6 闭包构造恒等钉

def test_sc1_closure_invariant():
    # 阶梯常量值钉（:295-321；阶梯扩容/附着机制新增未经闭包复审先红）
    assert EX._GRID_SCALES == (1.0, 0.5, 0.25)
    assert EX._ESCAPE_RADII == (1, 2, 3)
    assert EX._ESCAPE_DIRS == ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1))
    assert EX._FINE_SCALE == 0.25
    assert all(v["phase"] == 0.0 for v in EX._FINE_VARIANTS)
    assert EX._ESCAPE_VARIANT["phase"] == 0.0
    assert EX._FINE_ESCAPE_START_DIRS == EX._ESCAPE_DIRS
    assert EX._FINE_ESCAPE_GOAL_DIRS == EX._ESCAPE_DIRS[:4]
    # 构造恒等：closure == 全部计划吸附锚点集 ∪ {e 精确坐标}（消费同一
    # _attempt_plans/_escape_anchor/_snap_grid=单一事实源）
    board = _minimal_sealed_board()
    view = _BoardView(board)
    for pid, eps in _ladder_bound_partitions(
            view, [p["partition_id"] for p in board["partitions"]]):
        for e in eps:
            closure = _attachment_closure(view, e)
            expected = {(float(e[0]), float(e[1]))}
            x0, y0 = view.workspace[0], view.workspace[1]
            for variant, scale, escape in EX._attempt_plans():
                pitch = EX.GRID_PITCH * scale
                phase = variant["phase"] * 0.5 * pitch
                for side in ("start", "goal"):
                    anchor = _escape_anchor(e, escape, pitch, side)
                    key = EX._snap_grid(view, anchor, pitch, phase)
                    if key is not None:
                        expected.add((x0 + key[0] * pitch + phase,
                                      y0 + key[1] * pitch + phase))
            assert closure == sorted(expected)
            # S(e) ⊇ {e 精确坐标}（M3 项，V1 缺此即误杀）；两端点均 0.25 格
            # 对齐 → 基线吸附点=端点本身，由上一断言覆盖
            assert (float(e[0]), float(e[1])) in closure
    # 抽样位移点：e1=(11.0,10.0) 的 r3 轴向逃逸点（11.75,10.0) ∈ closure
    e1 = (11.0, 10.0)
    closure = _attachment_closure(view, e1)
    assert (11.75, 10.0) in closure and (10.25, 10.0) in closure
    # escape=None / side 不匹配 → 精确坐标原样（helper 纯等价语义）
    assert _escape_anchor(e1, None, 0.25, "start") == e1
    assert _escape_anchor(e1, ("goal", (1, 0), 3), 0.25, "start") == e1
    assert _escape_anchor(e1, ("goal", (1, 0), 3), 0.25, "goal") == \
        (11.75, 10.0)


# ------------------------------------------------ A7 cross-check 弃权

def test_sc1_crosscheck_abstain(monkeypatch):
    board = _minimal_sealed_board()
    # 注入 mismatch：edge_blocked 复核恒「开放」→ 判定器密封读数与之
    # 不同意 → 弃权不短路（宁漏判不误杀），回落正常阶梯
    monkeypatch.setattr(_Context, "edge_blocked",
                        lambda self, *a, **k: None)
    res = execute_candidate(board, _cand(board))
    text = "\n".join(res["negotiation_log"])
    assert "sealed-short-circuit" not in text
    assert "preflight-seal-abstain" in text
    assert any("cross_check mismatch" in ln for ln in res["negotiation_log"])
    # 回落正常阶梯路径：attempt 行仍在（穷举或布通），非 0 attempt 收口
    assert re.search(r"attempt=\d+ ", text)


# ------------------------------------------------ A8 确定性

def test_sc1_determinism():
    board = _load_synth("syn-u01")
    cand = _cand(board)
    r1 = execute_candidate(board, cand)
    r2 = execute_candidate(board, cand)
    key = lambda d: canonical.canonical_json(
        {k: d[k] for k in ("verdict", "per_net", "negotiation_log")})
    assert key(r1) == key(r2)
