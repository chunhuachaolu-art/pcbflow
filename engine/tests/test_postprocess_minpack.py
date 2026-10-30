# -*- coding: utf-8 -*-
"""V5-R8 布线后处理最小三件包钉值测试（v5.postprocess/2.1.0）。

任务书=V5-R8-POSTPROCESS-MINPACK-TB2-2026-10-04.md（§2 D-1..D-8）+09-24
原件验收门 1。钉值族：
  - P1 几何恒等：覆盖线段集逐位（区间并集恒等，含 45° 对角共线族）；
  - 保护集反面：[T,R,T] 回流桩折返与 via 附着点不被任何原语触（首末顶点/
    孔位坐标/桩三点原样），孔披露计数零变；
  - 幂等二遍零改（canonical 字节等+二遍零动作+changed=False 逐字节等）；
  - P2 正面（P2a 迹严格收缩/P2b 曼哈顿等价台阶压缩）+反面（P2b 真实
    R6 禁布违例回退留痕；P2a 复检失败回退=monkeypatch check_routes）；
  - P3 回流对守卫反面（单删回流孔/单删过渡孔/删量不配均抛
    PostprocessGuardError）+同位对检测（>MAX_LEGIT_DISCLOSURE 披露方报数）；
  - 违例回退留痕（revert_log 逐动作 reason 在场）；
  - 管线插入集成测试（tmp 沙箱+monkeypatch 板目录，禁写中央板目录
    out/v5-p5/boards/：postprocess 阶段双留+D-1 懒加载序 final 优先+
    回退 execute.json+run["postprocess"] 记账块+STAGE/版本钉）。

零渲染零读图、零网络、零 LLM API；不装不调 kicad-cli（外权威半边由
编排方统一跑）。全部自造夹具（hand board，load_board 落链）。
"""
import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "tools"))

from v5 import canonical  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5.postprocess import (  # noqa: E402
    ACTION_BUDGET,
    MAX_LEGIT_DISCLOSURE,
    MAX_ROUNDS,
    PASS_BUDGETS,
    POSTPROCESS_VERSION,
    PostprocessGuardError,
    PotentialMonotonicityError,
    _assert_lex_decrease,
    _assert_pass_monotonic,
    _pass_termination_status,
    assert_return_pair_guard,
    detect_colocated_via_pairs,
    enumerate_candidates,
    postprocess_routes,
)
from v5.route_check import RouteCheckError, check_routes  # noqa: E402

import run_p5_board as rp  # noqa: E402


# --------------------------------------------------------------- 夹具

def _hand_board(board_id="pp-minpack", workspace=None, zones=None,
                endpoints=None, ptype="MISC"):
    """自造合法 2 层板（synthetic provenance；load_board 落链）。单分区
    P1/net N1；endpoints 缺省 [[2,10],[30,10]]。"""
    ep = endpoints or [[2.0, 10.0], [30.0, 10.0]]
    bd = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": workspace or {"x_min": 0.0, "y_min": 0.0,
                                   "x_max": 40.0, "y_max": 30.0},
        "zones": zones or [],
        "partitions": [{
            "partition_id": "P1", "ptype": ptype,
            "geometry": {"endpoints": [list(p) for p in ep]},
            "layer_policy": "F.Cu",
            "width_prior": {"w_min": 0.2, "w_max": 0.2},
            "current_a": 0.0, "speed_class": "low_speed",
            "planned_width": 0.2}],
        "nets": [{"net_id": "N1", "net_class": "MISC",
                  "partitions": ["P1"]}],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic",
                       "source_uri": "synthetic://pp-minpack",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
    load_board(bd)
    return bd


def _doc(bd, entries, log=None):
    return {
        "schema_version": "v5.routes.v1",
        "board_id": bd["board_id"],
        "board_sha256": bd["provenance"]["board_sha256"],
        "routes": entries,
        "negotiation_log": list(log or []),
        "provenance": {"generator": "v5.executor/test-fixture",
                       "board_sha256": bd["provenance"]["board_sha256"]},
    }


def _entry(bd, polyline, layer="F.Cu", tv=None, rv=None, pid="P1", net="N1",
           width=0.2, **kw):
    e = {"partition_id": pid, "net_id": net, "layer": layer,
         "polyline": [list(p) for p in polyline], "width": width,
         "transition_vias": [list(p) for p in (tv or [])],
         "return_vias": [list(p) for p in (rv or [])]}
    e.update(kw)
    return e


def _seg_canon(a, b):
    a, b = tuple(a), tuple(b)
    return (a, b) if a <= b else (b, a)


def _cover_set(polyline):
    """覆盖线段集（逐位）：按线（单位方向、法向偏移）分组的投影区间并集。
    端点取原浮点值（幸存顶点浮点保真 ⇒ 同点同值，比较精确成立）。"""
    lines = {}
    for a, b in zip(polyline, polyline[1:]):
        a = (float(a[0]), float(a[1]))
        b = (float(b[0]), float(b[1]))
        if a == b:
            continue
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = (dx * dx + dy * dy) ** 0.5
        ux, uy = round(dx / n, 9), round(dy / n, 9)
        c = round(ux * a[1] - uy * a[0], 9)
        t0 = round(a[0] * ux + a[1] * uy, 9)
        t1 = round(b[0] * ux + b[1] * uy, 9)
        if t0 > t1:
            t0, t1 = t1, t0
        lines.setdefault((ux, uy, c), []).append((t0, t1))
    out = {}
    for key, ivs in lines.items():
        ivs.sort()
        merged = []
        for lo, hi in ivs:
            if merged and lo <= merged[-1][1] + 1e-12:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        out[key] = [tuple(iv) for iv in merged]
    return out


def _via_snapshot(doc):
    out = {}
    for e in doc["routes"]:
        for key in ("transition_vias", "return_vias"):
            for p in e.get(key) or []:
                k = (e["net_id"], round(float(p[0]), 9),
                     round(float(p[1]), 9), key)
                out[k] = out.get(k, 0) + 1
    return out


# ------------------------------------------------- P1 几何恒等

def test_p1_covered_segment_set_identity():
    """P1 钉值：共线中间点撤除后覆盖线段集逐位恒等（轴向+45° 对角族），
    顶点数钉值。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [20.0, 24.0]])
    # 轴向共线 + 45° 对角共线（0.25 步进栅格）混合路径
    poly = [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0], [10.0, 12.0],
            [10.0, 14.0], [12.25, 16.25], [14.5, 18.5], [16.75, 20.75],
            [20.0, 24.0]]
    doc = _doc(bd, [_entry(bd, poly)])
    nd, prov = postprocess_routes(bd, doc)
    assert prov["changed"] is True
    # 轴向 2 点 + 45° 对角 3 点 = 5 处共线中间点
    assert prov["actions"]["P1"]["applied"] == 5
    assert nd["routes"][0]["polyline"] == [[2.0, 10.0], [10.0, 10.0],
                                           [10.0, 14.0], [20.0, 24.0]]
    assert _cover_set(poly) == _cover_set(nd["routes"][0]["polyline"])
    assert prov["final_check"]["feasible"] is True


def test_p1_no_touch_when_no_colinear():
    """P1 反面：无共线中间点 → changed=False、new_doc 与输入逐字节等。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [10.0, 20.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [10.0, 10.0], [10.0, 20.0]])])
    nd, prov = postprocess_routes(bd, doc)
    assert prov["changed"] is False
    assert canonical.canonical_json(nd) == canonical.canonical_json(doc)


# ------------------------------------------------- 保护集反面

def _via_chain_doc(bd):
    """2 entry 换层网（F.Cu→B.Cu）：executor 原生形态桩=[T,R,T]（头桩
    poly[:3]/尾桩 poly[-3:]），P1 诱饵=共线中间点、P2a 诱饵=桩三点反平行
    共线、P2b 诱饵=四点台阶（含桩点）。"""
    t1, r1 = (20.0, 10.0), (20.0, 11.5)
    e1 = _entry(bd, [[2.0, 10.0], [10.0, 10.0], t1, r1, t1], layer="F.Cu",
                tv=[t1], rv=[r1])
    e2 = _entry(bd, [t1, r1, t1, [26.0, 10.0], [28.0, 10.0], [30.0, 10.0]],
                layer="B.Cu", tv=[t1], rv=[r1])
    return _doc(bd, [e1, e2]), t1, r1


def test_protection_set_stub_and_via_points_untouched():
    """保护集反面钉值：[T,R,T] 桩（含反平行共线 P2a 诱饵）与孔附着点、
    首末顶点不被任何原语触——孔披露计数零变、桩三点原样、衔接点不变。"""
    bd = _hand_board()
    doc, t1, r1 = _via_chain_doc(bd)
    raw_via = _via_snapshot(doc)
    nd, prov = postprocess_routes(bd, doc)
    assert prov["changed"] is True
    assert _via_snapshot(nd) == raw_via                 # 孔披露零变
    e1, e2 = nd["routes"]
    # 尾桩 [T,R,T] 原样（R 在索引 n−2、T 两护）
    assert e1["polyline"][-3:] == [[20.0, 10.0], [20.0, 11.5], [20.0, 10.0]]
    # 头桩 [T,R,T] 原样；仅共线中间点被 P1 撤除
    assert e2["polyline"][:3] == [[20.0, 10.0], [20.0, 11.5], [20.0, 10.0]]
    assert e1["polyline"][0] == [2.0, 10.0]             # 首顶点恒保护
    assert e2["polyline"][-1] == [30.0, 10.0]           # 末顶点恒保护
    assert e1["polyline"][-1] == e2["polyline"][0]      # 衔接点不变
    assert e1["polyline"] == [[2.0, 10.0], [20.0, 10.0], [20.0, 11.5],
                              [20.0, 10.0]]
    assert e2["polyline"] == [[20.0, 10.0], [20.0, 11.5], [20.0, 10.0],
                              [30.0, 10.0]]
    assert prov["actions"]["P2a"]["applied"] == 0       # 桩折返未被对消
    assert prov["actions"]["P2b"]["applied"] == 0
    assert prov["actions"]["P3"]["applied"] == 0        # 非零净换层链
    assert prov["final_check"]["feasible"] is True


# ------------------------------------------------- 幂等二遍零改

def test_idempotent_second_pass_zero_change():
    """幂等钉值：二遍 canonical 字节等+零动作；changed=False 输出与输入
    逐字节等（不加 log 行/不写 provenance 标记）。"""
    bd = _hand_board()
    doc, _t1, _r1 = _via_chain_doc(bd)
    nd1, prov1 = postprocess_routes(bd, doc)
    assert prov1["changed"] is True
    nd2, prov2 = postprocess_routes(bd, nd1)
    assert canonical.canonical_json(nd1) == canonical.canonical_json(nd2)
    assert prov2["changed"] is False
    assert all(v["applied"] == 0 for v in prov2["actions"].values())
    bd3 = _hand_board(endpoints=[[2.0, 10.0], [10.0, 20.0]])
    nd3_doc = _doc(bd3, [_entry(bd3, [[2.0, 10.0], [10.0, 10.0],
                                       [10.0, 20.0]])])
    nd3, prov3 = postprocess_routes(bd3, nd3_doc)
    assert prov3["changed"] is False
    assert canonical.canonical_json(nd3) == canonical.canonical_json(nd3_doc)
    assert "postprocess" not in nd3["provenance"]
    assert nd3["negotiation_log"] == []


# ------------------------------------------------- P2 正反面

def test_p2a_backtrack_cancel_positive():
    """P2a 正面：共线往返（中间点同侧）对消——迹严格收缩、留痕 applied。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [8.0, 10.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [14.0, 10.0], [8.0, 10.0]])])
    nd, prov = postprocess_routes(bd, doc)
    assert prov["actions"]["P2a"]["applied"] == 1
    assert nd["routes"][0]["polyline"] == [[2.0, 10.0], [8.0, 10.0]]
    assert prov["metrics"]["after"]["length_mm"] == 6.0
    assert prov["metrics"]["before"]["length_mm"] == 18.0
    assert prov["final_check"]["feasible"] is True


def test_p2a_collapse_guard_negative():
    """P2a 反面（结构）：对消致塌缩（整 entry 归零长/<2 点）→ 拒发留痕、
    几何零改。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [2.0, 10.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [10.0, 10.0], [2.0, 10.0]])])
    nd, prov = postprocess_routes(bd, doc)
    assert prov["actions"]["P2a"]["reverted"] == 1
    assert any(r["reason"].startswith("塌缩守卫")
               for r in prov["action_log"] if r["prim"] == "P2a")
    assert nd["routes"][0]["polyline"] == [[2.0, 10.0], [10.0, 10.0],
                                           [2.0, 10.0]]


def test_p2a_recheck_revert_leaves_trace(monkeypatch):
    """P2a 反面（复检）：monkeypatch check_routes 令动作复检不可行 → 回退
    该动作+action_log 留痕 reason；raw 几何零改。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [8.0, 10.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [14.0, 10.0], [8.0, 10.0]])])
    calls = {"n": 0}
    real = check_routes

    def fake(board, d):
        calls["n"] += 1
        if calls["n"] == 2:      # 基线(1)后首个动作复检(2)失败
            return {"feasible": False, "violations": [{"rule": "R5"}],
                    "attributed_violations": [{"rule": "R5"}]}
        return real(board, d)
    import v5.postprocess as pp
    monkeypatch.setattr(pp, "check_routes", fake)
    nd, prov = postprocess_routes(bd, doc)
    assert calls["n"] >= 2
    assert prov["actions"]["P2a"]["reverted"] == 1
    rows = [r for r in prov["action_log"] if r["prim"] == "P2a"]
    assert rows and rows[0]["status"] == "reverted" and rows[0]["reason"]
    assert nd["routes"][0]["polyline"] == [[2.0, 10.0], [14.0, 10.0],
                                           [8.0, 10.0]]


def test_p2b_stair_compress_positive():
    """P2b 正面：同向台阶 A,B,C,D → A,E,D（E=(D.x,A.y) 同向式）——曼哈顿
    长度不变、真拐角 2→1、留痕 applied。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [12.0, 14.0]])
    poly = [[2.0, 10.0], [6.0, 10.0], [6.0, 14.0], [12.0, 14.0]]
    doc = _doc(bd, [_entry(bd, poly)])
    nd, prov = postprocess_routes(bd, doc)
    assert prov["actions"]["P2b"]["applied"] == 1
    assert nd["routes"][0]["polyline"] == [[2.0, 10.0], [12.0, 10.0],
                                           [12.0, 14.0]]
    assert prov["metrics"]["before"]["length_mm"] == \
        prov["metrics"]["after"]["length_mm"] == 14.0
    assert prov["metrics"]["before"]["corners"] == 2
    assert prov["metrics"]["after"]["corners"] == 1
    assert prov["final_check"]["feasible"] is True


def test_p2b_keepout_revert_leaves_trace():
    """P2b 反面（真实 R6）：压缩腿穿禁布区 → check_routes 全量复检违例 →
    回退留痕、几何零改、changed=False。"""
    bd = _hand_board(
        zones=[{"zone_id": "K1", "kind": "keepout",
                "rect": {"x_min": 11.5, "y_min": 11.0, "x_max": 12.5,
                         "y_max": 13.0}, "layers": "all",
                "note": "封新竖腿 x=12"}],
        endpoints=[[2.0, 10.0], [12.0, 14.0]])
    poly = [[2.0, 10.0], [6.0, 10.0], [6.0, 14.0], [12.0, 14.0]]
    doc = _doc(bd, [_entry(bd, poly)])
    assert check_routes(bd, doc)["feasible"] is True     # raw 本身干净
    nd, prov = postprocess_routes(bd, doc)
    assert prov["actions"]["P2b"]["reverted"] == 1
    rows = [r for r in prov["action_log"] if r["prim"] == "P2b"]
    assert rows and rows[0]["status"] == "reverted" and rows[0]["reason"]
    assert nd["routes"][0]["polyline"] == [list(p) for p in poly]
    assert prov["changed"] is False
    assert prov["final_check"]["feasible"] is True


# ------------------------------------------------- P3 守卫+同位对

def _p3_chain_bd():
    return _hand_board(endpoints=[[2.0, 10.0], [20.0, 14.0]])


def _p3_chain_doc(bd):
    t1, r1 = (8.0, 10.0), (8.0, 11.5)
    t2, r2 = (14.0, 12.0), (14.0, 13.5)
    ek = _entry(bd, [[2.0, 10.0], t1, r1, t1], layer="F.Cu", tv=[t1], rv=[r1])
    e1 = _entry(bd, [t1, r1, t1, [14.0, 10.0], t2, r2, t2], layer="B.Cu",
                tv=[t1, t2], rv=[r1, r2])
    e2 = _entry(bd, [t2, r2, t2, [20.0, 12.0], [20.0, 14.0]], layer="F.Cu",
                tv=[t2], rv=[r2])
    return _doc(bd, [ek, e1, e2])


def test_p3_zero_net_layer_change_positive():
    """P3(b) 正面：A→B→A 零净换层链消除——三 entry 并一、T1/T2/R1/R2 全删、
    外层 L 形拼接（先 x 后 y）钉值。"""
    bd = _p3_chain_bd()
    doc = _p3_chain_doc(bd)
    nd, prov = postprocess_routes(bd, doc)
    assert prov["actions"]["P3"]["applied"] == 1
    assert len(nd["routes"]) == 1
    e = nd["routes"][0]
    assert e["layer"] == "F.Cu"
    assert e["transition_vias"] == [] and e["return_vias"] == []
    # e_k 剥尾桩 [T1,R1,T1] 后真实端点 X=(2,10)；e2 剥头桩后 W=(20,12)；
    # 先 x 后 y：(2,10)→(20,10)→W(20,12)→(20,14)；不动点二轮 P1 随手收拢
    # 共线拼接点 (20,12)（P3 产物交由 P1 清尾=处理序构造性）
    assert e["polyline"] == [[2.0, 10.0], [20.0, 10.0], [20.0, 14.0]]
    assert prov["metrics"]["after"]["vias_unique_net_scoped"] == 0
    assert prov["final_check"]["feasible"] is True
    assert prov["changed"] is True


def test_p3_guard_negative_single_return_via_removal():
    """回流对守卫反面①：单删回流孔（过渡孔留）→ PostprocessGuardError。"""
    bd = _p3_chain_bd()
    doc = _p3_chain_doc(bd)
    broken = copy.deepcopy(doc)
    broken["routes"][0]["return_vias"] = []          # 只删 e_k 的 R1 披露
    with pytest.raises(PostprocessGuardError):
        assert_return_pair_guard(doc, broken)


def test_p3_guard_negative_single_transition_removal():
    """回流对守卫反面②：删过渡孔未等量删其回流孔 → PostprocessGuardError。"""
    bd = _p3_chain_bd()
    doc = _p3_chain_doc(bd)
    broken = copy.deepcopy(doc)
    broken["routes"][0]["transition_vias"] = []      # 只删 e_k 的 T1 披露
    with pytest.raises(PostprocessGuardError):
        assert_return_pair_guard(doc, broken)


def test_p3_guard_negative_uneven_counts():
    """回流对守卫反面③：双侧披露删量不配（e_k 删 T1/R1、e1 只删 T1）→ 抛。"""
    bd = _p3_chain_bd()
    doc = _p3_chain_doc(bd)
    broken = copy.deepcopy(doc)
    del broken["routes"][1]["transition_vias"][0]    # e1.tv 只剩 T2
    with pytest.raises(PostprocessGuardError):
        assert_return_pair_guard(doc, broken)


def test_p3_guard_positive_paired_removal_passes():
    """回流对守卫正面：T1/R1、T2/R2 等量成对删（与 P3 动作同构）→ 通过。"""
    bd = _p3_chain_bd()
    doc = _p3_chain_doc(bd)
    nd, _prov = postprocess_routes(bd, doc)
    assert assert_return_pair_guard(doc, nd) is True


def test_colocated_via_pair_detection():
    """D-5(a) 同位对检测：同一 (net,孔位) 披露方 entry 数 > 结构上界 → 报数；
    上界内（=2，两侧衔接）→ 空单（防御面如实报 0）。"""
    pts = [[5.0, 5.0]]
    entries = [{"net_id": "N1", "polyline": [[0.0, 0.0], [1.0, 0.0]],
                "transition_vias": pts, "return_vias": []},
               {"net_id": "N1", "polyline": [[1.0, 0.0], [2.0, 0.0]],
                "transition_vias": pts, "return_vias": []},
               {"net_id": "N1", "polyline": [[2.0, 0.0], [3.0, 0.0]],
                "transition_vias": pts, "return_vias": []},
               {"net_id": "N1", "polyline": [[3.0, 0.0], [4.0, 0.0]],
                "transition_vias": pts, "return_vias": []}]
    assert len(detect_colocated_via_pairs({"routes": entries})) == 1
    assert len(entries[:MAX_LEGIT_DISCLOSURE]) == MAX_LEGIT_DISCLOSURE
    assert detect_colocated_via_pairs({"routes": entries[:2]}) == []
    bd = _p3_chain_bd()
    doc = _p3_chain_doc(bd)
    _nd, prov = postprocess_routes(bd, doc)
    assert prov["colocated_via_pairs_detected"] == 0


# ------------------------------------------------- 预算/轮上限/终检回退

def test_budget_cap_stops_and_terminal_check_still_runs():
    """预算钉值：budget=1 → 单动作即停、capped=True、终检仍全量跑
    （final_check 在场且 feasible）。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [10.0, 18.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0],
                                [10.0, 14.0], [10.0, 18.0]])])
    nd, prov = postprocess_routes(bd, doc, budget=1)
    assert prov["budget"]["capped"] is True
    assert prov["actions"]["P1"]["applied"] == 1
    assert prov["final_check"]["feasible"] is True     # 终检仍跑
    assert len(nd["routes"][0]["polyline"]) == 4      # 只撤了 1 点
    assert ACTION_BUDGET == 4000 and MAX_ROUNDS == 8


def test_rounds_cap_disclosed():
    """轮上限钉值：max_rounds=1 且有动作 → converged=False（fail-closed
    披露），动作与终检照常记账。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [10.0, 18.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0],
                                [10.0, 14.0], [10.0, 18.0]])])
    nd, prov = postprocess_routes(bd, doc, max_rounds=1)
    assert prov["fixpoint"] == {"converged": False, "rounds": 1,
                                "max_rounds": 1}
    assert prov["actions"]["P1"]["applied"] == 2   # (6,10) 与 (10,14) 两中间点


def test_terminal_gate_reverts_all(monkeypatch):
    """终检兜底：终局 check_routes 不可行（P1 免复检的 backstop 被打破）→
    整体回退 raw、reverted_all=True、changed=False。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [10.0, 10.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0]])])
    real = check_routes
    calls = {"n": 0}

    def fake(board, d):
        calls["n"] += 1
        if calls["n"] >= 2:      # 基线过、终检挂
            return {"feasible": False, "violations": [{"rule": "R5"}],
                    "attributed_violations": [{"rule": "R5"}]}
        return real(board, d)
    import v5.postprocess as pp
    monkeypatch.setattr(pp, "check_routes", fake)
    nd, prov = postprocess_routes(bd, doc)
    assert prov["reverted_all"] is True
    assert prov["changed"] is False
    assert canonical.canonical_json(nd) == canonical.canonical_json(doc)


# ------------------------------------------------- 管线插入集成（tmp 沙箱）

SANDBOX_BOARD = "pp-minpack-sandbox"


class _FakeLedger:
    A_LAYER_PREREG = {SANDBOX_BOARD: {"nets": 1, "layers": 2,
                                      "sha256": "0" * 64}}

    @staticmethod
    def source_path_for(board_id):
        return os.path.join("out", "_pp_sandbox", "fake-src.kicad_pcb")

    def __init__(self):
        self.events = []

    def append(self, *args, **kwargs):
        self.events.append(args[1] if len(args) > 1 else None)
        return None


_INTEGRATION_POLY = [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0], [10.0, 14.0]]


def _install_pipeline_stubs(monkeypatch, tmp_path):
    """打桩编译链/规划/选择/执行/台账；板目录 monkeypatch 到 tmp 沙箱
    （禁写中央板目录 out/v5-p5/boards/）。"""
    monkeypatch.setattr(rp, "build_partition_artifact",
                        lambda board: {"partitions": []})
    monkeypatch.setattr(rp, "compile_board",
                        lambda board: ({"rules": [],
                                        "coverage": {"coverage_pct": 100.0}},
                                       []))
    monkeypatch.setattr(rp, "build_conflicts", lambda board: {"conflicts": []})
    monkeypatch.setattr(rp, "validate_conflicts_artifact", lambda cf: None)
    monkeypatch.setattr(rp, "build_pkg", lambda board, p_art, cf:
                        {"entries": []})
    monkeypatch.setattr(rp, "validate_pkg", lambda pkg: None)
    cands = [{"route_order": ["P1"], "layer_assignment": {"P1": "F.Cu"},
              "idx": 0}]
    monkeypatch.setattr(rp, "plan_candidates",
                        lambda board, c_art, arm="principle":
                            [dict(c) for c in cands])
    monkeypatch.setattr(rp, "select_best",
                        lambda board, cs: {"verdict": "SAT", "best": cands[0],
                                           "per_candidate": []})
    bd = _hand_board(board_id=SANDBOX_BOARD,
                     endpoints=[[2.0, 10.0], [10.0, 14.0]])
    routes_doc = _doc(bd, [_entry(bd, _INTEGRATION_POLY)])

    def exec_stub(board, cand, out_dir=None):
        return {"verdict": "ROUTED", "routes": copy.deepcopy(routes_doc),
                "per_net": [{"partition_id": "P1", "net_id": "N1",
                             "status": "ribbon", "attempts": 1,
                             "negotiated": True, "vias": 0, "length_mm": 1.0,
                             "width_mm": 0.2, "layers": ["F.Cu"]}],
                "negotiation_log": ["stub routed"]}

    monkeypatch.setattr(rp, "execute_candidate", exec_stub)
    fake = _FakeLedger()
    monkeypatch.setattr(rp, "ledger", fake)
    monkeypatch.setattr(rp, "load_stage_board", lambda bid: bd)
    out_root = os.path.join(str(tmp_path), "out")
    monkeypatch.setattr(rp, "OUT", out_root)
    import v5.sidecar as sidecar_mod
    monkeypatch.setattr(sidecar_mod, "ALLOWED_ROOTS",
                        (out_root.replace("\\", "/"),))
    return bd, routes_doc, fake, out_root


def _run_full_pipeline(monkeypatch, tmp_path):
    """execute→postprocess→check→export 全链（真实 postprocess_routes/
    check_routes/kicad_pcb_bytes，仅桩编译/规划/执行/台账）：双留工件+
    记账块+check/export 输入=final 面（P1 已撤点）。返回 (板目录, out 根)。"""
    _bd, _rd, _fake, out_root = _install_pipeline_stubs(monkeypatch, tmp_path)
    rc = rp.main(["--board", SANDBOX_BOARD,
                  "--stages", "execute,postprocess,check,export"])
    assert rc == 0
    bdir = os.path.join(out_root, "boards", SANDBOX_BOARD)
    raw_p = os.path.join(bdir, "routes-raw.json")
    fin_p = os.path.join(bdir, "routes-final.json")
    assert os.path.isfile(raw_p) and os.path.isfile(fin_p)
    with open(raw_p, encoding="utf-8") as f:
        raw_doc = json.load(f)
    with open(fin_p, encoding="utf-8") as f:
        fin_doc = json.load(f)
    # D-1：routes-raw=execute.json 内嵌 routes_doc 原样拷贝（canonical 等值）
    with open(os.path.join(bdir, "execute.json"), encoding="utf-8") as f:
        ex_doc = json.load(f)
    assert canonical.canonical_json(raw_doc["routes_doc"]) == \
        canonical.canonical_json(ex_doc["routes_doc"])
    # 化简账在场+final 面已撤共线点
    pp = fin_doc["postprocess"]
    assert pp["module_version"] == POSTPROCESS_VERSION
    assert pp["actions"]["P1"]["applied"] == 1
    assert pp["final_check"]["feasible"] is True
    assert fin_doc["routes_doc"]["routes"][0]["polyline"] == \
        [[2.0, 10.0], [10.0, 10.0], [10.0, 14.0]]
    # 记账块
    with open(os.path.join(bdir, "run-result.json"), encoding="utf-8") as f:
        run = json.load(f)["run"]
    assert run["postprocess"]["module_version"] == POSTPROCESS_VERSION
    assert run["postprocess"]["actions_applied"]["P1"] == 1
    assert run["postprocess"]["routes_final"].endswith("routes-final.json")
    # check 阶段输入=final 面（check.json 落盘+导出段数=final 折线段数）
    assert run["check"]["feasible"] is True
    with open(os.path.join(bdir, SANDBOX_BOARD + ".kicad_pcb"), "rb") as f:
        pcb = f.read().decode("utf-8")
    assert pcb.count("(segment") == 2     # final 3 点=2 段（raw 4 点=3 段）
    # 禁写中央板目录：tmp 沙箱外无新板目录（中央 thatmicpre-v2 等零触碰）
    central = os.path.join(ROOT, "out", "v5-p5", "boards", SANDBOX_BOARD)
    assert not os.path.exists(central)
    return bdir, out_root


def test_pipeline_postprocess_stage_integration(monkeypatch, tmp_path):
    """管线插入集成（断言主体在 _run_full_pipeline，见该 helper docstring）。"""
    _run_full_pipeline(monkeypatch, tmp_path)


def test_lazy_load_prefers_final_then_falls_back(monkeypatch, tmp_path):
    """D-1 懒加载序钉值：routes-final.json 在场优先；删除后回退
    execute.json（导出段数 raw 面 3 段）。"""
    bdir, _out_root = _run_full_pipeline(monkeypatch, tmp_path)
    # 场景①：check/export 子集重跑（doc=None → 懒加载）→ final 优先
    rc = rp.main(["--board", SANDBOX_BOARD, "--stages", "export"])
    assert rc == 0
    with open(os.path.join(bdir, SANDBOX_BOARD + ".kicad_pcb"), "rb") as f:
        assert f.read().decode("utf-8").count("(segment") == 2
    # 场景②：删 routes-final.json → 回退 execute.json raw 面
    os.remove(os.path.join(bdir, "routes-final.json"))
    rc = rp.main(["--board", SANDBOX_BOARD, "--stages", "export"])
    assert rc == 0
    with open(os.path.join(bdir, SANDBOX_BOARD + ".kicad_pcb"), "rb") as f:
        assert f.read().decode("utf-8").count("(segment") == 3


def test_stage_order_and_version_pins():
    """D-8 版本钉：STAGE_ORDER/PIPELINE_STAGES 于 execute 后插入
    postprocess；runner 0.5.0→0.6.0；模块版本串 v5.postprocess/2.1.0
    （OPT-18 E2a 1.0.0→2.0.0→E2b 2.1.0 大板策略，版本钉同步=r8 F1 教训）。"""
    assert rp.STAGE_ORDER == ("convert", "compile", "execute", "postprocess",
                              "check", "export", "drc")
    assert rp.STAGE_ORDER.index("postprocess") == \
        rp.STAGE_ORDER.index("execute") + 1
    assert "postprocess" in rp.PIPELINE_STAGES
    assert rp.PIPELINE_STAGES.index("postprocess") == \
        rp.PIPELINE_STAGES.index("execute") + 1
    assert rp.VERSION == "0.6.0"
    assert POSTPROCESS_VERSION == "v5.postprocess/2.1.0"


def test_execute_failed_skips_postprocess_gracefully(monkeypatch, tmp_path):
    """FAILED 板无 routes：postprocess 与 check/export/drc 同款优雅跳过
    （skipped_stages 记账；终态口径零变化=构造性）。"""
    _bd, _rd, _fake, out_root = _install_pipeline_stubs(monkeypatch, tmp_path)

    def exec_fail(board, cand, out_dir=None):
        return {"verdict": "FAILED", "routes": None,
                "per_net": [{"partition_id": "P1", "net_id": "N1",
                             "status": "failed", "attempts": 1,
                             "negotiated": True, "vias": 0, "length_mm": 0.0,
                             "width_mm": 0.2, "layers": []}],
                "negotiation_log": ["stub failed"]}

    monkeypatch.setattr(rp, "execute_candidate", exec_fail)
    rc = rp.main(["--board", SANDBOX_BOARD,
                  "--stages", "execute,postprocess,check,export"])
    assert rc == 0
    bdir = os.path.join(out_root, "boards", SANDBOX_BOARD)
    with open(os.path.join(bdir, "run-result.json"), encoding="utf-8") as f:
        run = json.load(f)["run"]
    assert run["skipped_stages"] == ["postprocess", "check", "export"]
    assert "postprocess" not in run
    assert not os.path.exists(os.path.join(bdir, "routes-final.json"))


def test_purity_input_doc_untouched():
    """纯函数钉值：postprocess_routes 不改输入 doc/board（deepcopy 面）。"""
    bd = _p3_chain_bd()
    doc = _p3_chain_doc(bd)
    doc_snap = canonical.canonical_json(doc)
    bd_snap = canonical.canonical_json(bd)
    _nd, _prov = postprocess_routes(bd, doc)
    assert canonical.canonical_json(doc) == doc_snap
    assert canonical.canonical_json(bd) == bd_snap


def test_fail_closed_on_malformed_doc():
    """fail-closed：非 v5.routes.v1 形状 → check_routes 抛 RouteCheckError
    或入口 ValueError（不产出半成品）。"""
    bd = _hand_board()
    with pytest.raises((ValueError, RouteCheckError)):
        postprocess_routes(bd, {"routes": "not-a-list"})
    bad = _doc(bd, [_entry(bd, [[2.0, 10.0], [99.0, 10.0]])])
    bad["board_sha256"] = "0" * 64
    with pytest.raises(RouteCheckError):
        postprocess_routes(bd, bad)


# ------------------------------------------------- v2 最小核（OPT-18 E2a）
# T1/T2/T4/T5 面：per-pass delta/hash 链+单调势断言+termination 状态机+
# 四门分离（J1/J2/J4 机器可判性钉值）。

_PRIM_KEYS = ("P1", "P2a", "P2b", "P3")


def test_v2_pass_records_delta_hash_chain():
    """J1 钉值：passes.<P>.{delta,hash.in/out} 全非空；hash_chain=H_0..H_4
    五元组；P1/P2a/P2b delta.vertices==−applied；主势链点严格降
    （P1 正例 5 点撤除）。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [20.0, 24.0]])
    poly = [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0], [10.0, 12.0],
            [10.0, 14.0], [12.25, 16.25], [14.5, 18.5], [16.75, 20.75],
            [20.0, 24.0]]
    doc = _doc(bd, [_entry(bd, poly)])
    nd, prov = postprocess_routes(bd, doc)
    assert len(prov["hash_chain"]) == 5
    assert all(isinstance(h, str) and len(h) == 64
               for h in prov["hash_chain"])
    assert prov["hash_chain"][0] != prov["hash_chain"][4]   # changed 板
    for p in _PRIM_KEYS:
        rec = prov["passes"][p]
        assert rec["hash"]["in"] and rec["hash"]["out"]      # J1 非空
        assert rec["delta"]["applied"] >= 0
        assert rec["main_potential"] in ("vertices_interior", "entries")
    for p in ("P1", "P2a", "P2b"):                           # J1 机械核验位
        assert prov["passes"][p]["delta"]["vertices"] \
            == -prov["passes"][p]["delta"]["applied"]
    assert prov["passes"]["P1"]["delta"]["applied"] == 5
    assert prov["passes"]["P1"]["delta"]["vertices"] == -5
    # 主势（Φ_V 内部顶点）链点严格降：9 点（7 内部）→4 点（2 内部）
    assert prov["passes"]["P1"]["phi"]["vertices_interior"] == [7, 2]
    # 链式边界：P_k 的 in=上一 pass 的 out
    assert prov["passes"]["P1"]["hash"]["in"] == prov["hash_chain"][0]
    for i, p in enumerate(("P2a", "P2b", "P3")):
        assert prov["passes"][p]["hash"]["in"] \
            == prov["passes"][_PRIM_KEYS[i - 1]]["hash"]["out"]


def test_v2_termination_converged_negative():
    """J2 负例钉值：capped=False 收敛板——termination.status=CONVERGED、
    residual_candidates==0、不出现 NOT_CONVERGED 字；幂等主张前置在场。"""
    bd = _hand_board()
    doc, _t1, _r1 = _via_chain_doc(bd)
    _nd, prov = postprocess_routes(bd, doc)
    term = prov["termination"]
    assert term["status"] == "CONVERGED"
    assert term["residual_candidates"] == 0
    statuses = [term["status"]] + [v["status"] for v in term["by_pass"].values()]
    assert all("NOT_CONVERGED" not in s for s in statuses)  # J2 状态值面
    assert all(v["status"] == "CONVERGED" and v["residual_candidates"] == 0
               for v in term["by_pass"].values())
    # 幂等主张前置：idempotency 模块内 null（权威=工装）+前置标注
    assert prov["idempotency"] is None and prov["determinism"] is None
    assert prov["gates"]["idempotency"]["claim_precondition"] \
        == "termination.status==CONVERGED"


def test_v2_termination_budget_capped_positive():
    """J2 正例钉值：budget=1 封顶+残留候选 ⇒ termination.status=
    NOT_CONVERGED_BUDGET 且 residual_candidates>0（机器可判）。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [10.0, 18.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0],
                                [10.0, 14.0], [10.0, 18.0]])])
    _nd, prov = postprocess_routes(bd, doc, budget=1)
    term = prov["termination"]
    assert prov["budget"]["capped"] is True
    assert term["status"] == "NOT_CONVERGED_BUDGET"
    assert term["residual_candidates"] == 1
    assert term["by_pass"]["P1"] == {"status": "NOT_CONVERGED_BUDGET",
                                     "residual_candidates": 1}
    assert term["by_pass"]["P2a"]["status"] == "CONVERGED"
    assert prov["passes"]["P1"]["delta"]["vertices"] \
        == -prov["passes"]["P1"]["delta"]["applied"] == -1


def test_v2_termination_rounds_defensive_position():
    """T5 轮超限防御位钉值：max_rounds=1 有动作 ⇒ v1 fixpoint.converged=False
    披露保留；termination 以候选面为准=CONVERGED（四门分离：轮披露≠候选
    面状态，候选清空即收敛）。"""
    bd = _hand_board(endpoints=[[2.0, 10.0], [10.0, 18.0]])
    doc = _doc(bd, [_entry(bd, [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0],
                                [10.0, 14.0], [10.0, 18.0]])])
    _nd, prov = postprocess_routes(bd, doc, max_rounds=1)
    assert prov["fixpoint"]["converged"] is False
    assert prov["termination"]["status"] == "CONVERGED"
    assert prov["termination"]["residual_candidates"] == 0


def test_v2_state_machine_pure_pins():
    """T5 状态机纯函数钉值（E1 §3.4 全转移）：候选清空⇒CONVERGED（预算
    恰尽亦然）；候选>0：capped 优先（proximate break）⇒NOT_CONVERGED_BUDGET
    ＞轮超限防御位⇒NOT_CONVERGED_ROUNDS；收敛轮+残留=防御披露 CONVERGED。"""
    f = _pass_termination_status
    assert f(0, True, True) == "CONVERGED"          # 候选清空>预算余量
    assert f(0, False, False) == "CONVERGED"
    assert f(1, True, False) == "NOT_CONVERGED_BUDGET"
    assert f(1, True, True) == "NOT_CONVERGED_BUDGET"   # capped 优先
    assert f(1, False, True) == "NOT_CONVERGED_ROUNDS"
    assert f(1, False, False) == "CONVERGED"        # 收敛轮+残留=防御披露


def test_v2_potential_monotonicity_negative():
    """T4 反例钉值：构造假势（applied>0 而 ΔΦ_main≥0）⇒
    PotentialMonotonicityError（fail-closed）；正例零改通过。"""
    with pytest.raises(PotentialMonotonicityError):
        _assert_pass_monotonic("P1", {"vertices_interior": 0}, 1)
    with pytest.raises(PotentialMonotonicityError):
        _assert_pass_monotonic("P1", {"vertices_interior": 2}, 3)
    with pytest.raises(PotentialMonotonicityError):
        _assert_pass_monotonic("P3", {"entries": 0}, 1)
    _assert_pass_monotonic("P1", {"vertices_interior": -5}, 5)   # 正例
    _assert_pass_monotonic("P1", {"vertices_interior": 0}, 0)    # 零动作
    _assert_pass_monotonic("P3", {"entries": -2}, 1)
    phi = {"vertices_interior": 5, "entries": 3, "via_net_positions": 2}
    _assert_lex_decrease(phi, {"vertices_interior": 4, "entries": 3,
                               "via_net_positions": 2})           # Φ_V 降
    _assert_lex_decrease(phi, {"vertices_interior": 5, "entries": 2,
                               "via_net_positions": 9})           # 字典序
    with pytest.raises(PotentialMonotonicityError):               # 持平
        _assert_lex_decrease(phi, {"vertices_interior": 5, "entries": 3,
                                   "via_net_positions": 2})
    with pytest.raises(PotentialMonotonicityError):               # 回升
        _assert_lex_decrease(phi, {"vertices_interior": 6, "entries": 0,
                                   "via_net_positions": 0})


def test_v2_idempotent_second_pass_all_zero():
    """T2 钉值扩展：复调零改——二遍 hash_chain 五元全等（H_0'=H_4'）+全
    pass delta=0+termination=CONVERGED+changed=False。"""
    bd = _hand_board()
    doc, _t1, _r1 = _via_chain_doc(bd)
    nd1, _prov1 = postprocess_routes(bd, doc)
    nd2, prov2 = postprocess_routes(bd, nd1)
    assert prov2["changed"] is False
    assert len(set(prov2["hash_chain"])) == 1       # H_0=H_1=…=H_4
    for p in _PRIM_KEYS:
        d = prov2["passes"][p]["delta"]
        assert d["applied"] == 0 and d["reverted"] == 0
        assert d["vertices"] == 0 and d["entries"] == 0
    assert prov2["termination"]["status"] == "CONVERGED"
    assert prov2["termination"]["residual_candidates"] == 0


def test_v2_four_gates_separated_fields():
    """J4 钉值：termination/budget/feasibility/determinism+idempotency 分立
    字段+权威标注（module/runner/harness）；v1 兼容字段全保留。"""
    bd = _hand_board()
    doc, _t1, _r1 = _via_chain_doc(bd)
    _nd, prov = postprocess_routes(bd, doc)
    for key in ("termination", "budget", "feasibility", "determinism",
                "idempotency", "gates", "passes", "hash_chain"):
        assert key in prov
    assert prov["termination"]["authority"] == "module"
    assert "authority" in prov["budget"] and "authority" in \
        prov["feasibility"]
    assert prov["determinism"] is None and prov["idempotency"] is None
    gates = prov["gates"]
    assert set(gates) == {"termination", "budget", "feasibility",
                          "determinism", "idempotency"}
    assert gates["determinism"]["authority"] == "runner"
    assert gates["idempotency"]["authority"] == "harness"
    assert prov["feasibility"]["final_check_always_runs"] is True
    assert prov["feasibility"]["final_check"] == prov["final_check"]
    # v1 兼容面：fixpoint/actions/metrics/final_check 原样
    assert set(prov["fixpoint"]) == {"converged", "rounds", "max_rounds"}
    assert set(prov["actions"]) == set(_PRIM_KEYS)
    assert {"before", "after"} <= set(prov["metrics"])


def test_v2_p3_pass_records_main_potential_entries():
    """P3 主势钉值：Φ_E 每动作 −2（delta.entries==-2*applied）、Φ_T 净位
    下降、hash 链在场（P3 正例夹具三 entry 并一）。"""
    bd = _p3_chain_bd()
    doc = _p3_chain_doc(bd)
    _nd, prov = postprocess_routes(bd, doc)
    rec = prov["passes"]["P3"]
    assert rec["delta"]["applied"] == 1
    assert rec["delta"]["entries"] == -2
    assert rec["delta"]["via_net_positions"] < 0
    assert rec["main_potential"] == "entries"
    assert rec["hash"]["in"] and rec["hash"]["out"]
    # P1 主势：P3 拼接点交由 P1 清尾（处理序构造性）⇒ P1 有动作
    assert prov["passes"]["P1"]["delta"]["applied"] >= 1
    assert prov["passes"]["P1"]["delta"]["vertices"] \
        == -prov["passes"]["P1"]["delta"]["applied"]


# ------------------------------------------- v2.1 大板策略（OPT-18 E2b）
# R10E2B-A..F 钉值：枚举/执行分离+收益密度排序（组间序）+per-net 局部
# 固定点+断点续跑跳过+per-pass 分池+J3 幂等面口径。

def _two_net_bd():
    """双网手板（NA 分区 PA 端点 [2,10]..[10,10]、NB 分区 PB 端点
    [2,20]..[14,20]——entry 首末点须贴分区端点）。"""
    bd = {
        "schema_version": "v5.board.v1",
        "board_id": "pp-minpack-2net",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 40.0,
                      "y_max": 30.0},
        "zones": [],
        "partitions": [
            {"partition_id": "PA", "ptype": "MISC",
             "geometry": {"endpoints": [[2.0, 10.0], [10.0, 10.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2,
                                                     "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed",
             "planned_width": 0.2},
            {"partition_id": "PB", "ptype": "MISC",
             "geometry": {"endpoints": [[2.0, 20.0], [14.0, 20.0]]},
             "layer_policy": "F.Cu", "width_prior": {"w_min": 0.2,
                                                     "w_max": 0.2},
             "current_a": 0.0, "speed_class": "low_speed",
             "planned_width": 0.2},
        ],
        "nets": [
            {"net_id": "NA", "net_class": "MISC", "partitions": ["PA"]},
            {"net_id": "NB", "net_class": "MISC", "partitions": ["PB"]},
        ],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic",
                       "source_uri": "synthetic://pp-minpack-2net",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
    load_board(bd)
    return bd


def _two_net_doc(bd):
    """NA=1 个 P1 候选（benefit 1）、NB=2 个（benefit 2）——NB 字典序
    靠后但收益高 ⇒ 组间序=收益密度降序把 NB 排前。"""
    ea = _entry(bd, [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0]], pid="PA",
                net="NA")
    eb = _entry(bd, [[2.0, 20.0], [6.0, 20.0], [10.0, 20.0], [14.0, 20.0]],
                pid="PB", net="NB")
    return _doc(bd, [ea, eb])


def test_v21_pools_frozen_pins_and_budget_four_fields():
    """R10E2B-E 钉值：冻结分池 B_P1=2800/B_P2a=600/B_P2b=200/B_P3=400
    （总 4000 与 ACTION_BUDGET 对齐）；per-pass budget 四字段
    （cap/consumed/applied/remaining/capped）passes.<P>.budget 与
    budget.by_pass 全板非空、cap=冻结池值。"""
    assert PASS_BUDGETS == {"P1": 2800, "P2a": 600, "P2b": 200, "P3": 400}
    assert sum(PASS_BUDGETS.values()) == ACTION_BUDGET == 4000
    bd = _hand_board()
    doc, _t1, _r1 = _via_chain_doc(bd)
    _nd, prov = postprocess_routes(bd, doc)
    assert prov["budget"]["pools_frozen"] == PASS_BUDGETS
    assert prov["budget"]["cap"] == 4000 and prov["budget"]["remaining"] \
        == 4000 - prov["budget"]["consumed"]
    for p in _PRIM_KEYS:
        rec = prov["passes"][p]["budget"]
        assert set(rec) == {"cap", "consumed", "applied", "remaining",
                            "capped"}
        assert rec["cap"] == PASS_BUDGETS[p]
        assert rec["consumed"] == rec["cap"] - rec["remaining"]
        assert prov["budget"]["by_pass"][p] == rec
    # 标量 budget=顺序装填（P1 先——密度 ∞ 面）
    _nd2, prov2 = postprocess_routes(bd, doc, budget=1)
    assert prov2["budget"]["by_pass"]["P1"]["cap"] == 1
    assert prov2["budget"]["by_pass"]["P2a"]["cap"] == 0
    # 显式 per-pass 字典
    _nd3, prov3 = postprocess_routes(bd, doc,
                                     budget={"P1": 0, "P2a": 3, "P2b": 0,
                                             "P3": 0})
    assert prov3["budget"]["by_pass"]["P2a"]["cap"] == 3


def test_v21_group_order_benefit_descending_deterministic():
    """R10E2B-B 排序确定性钉值：组间序=组候选收益总量降序（NB benefit 2
    ＞NA 1 ⇒ [NB,NA]，虽 NB 字典序靠后）；并列收益按 net 字典序；两次独立
    调用 canonical 字节等+strategy 面（组序/枚举摘要）逐位等（排序键全部
    由输入决定——无时钟无随机）。"""
    bd = _two_net_bd()
    doc = _two_net_doc(bd)
    nd1, prov1 = postprocess_routes(bd, doc)
    nd2, prov2 = postprocess_routes(bd, doc)
    assert prov1["strategy"]["group_order"] \
        == [{"net": "NB", "benefit": 2}, {"net": "NA", "benefit": 1}]
    assert prov1["strategy"]["enumeration"]["by_net_benefit"] \
        == {"NA": 1, "NB": 2}
    assert prov1["strategy"]["groups_executed"] == ["NB", "NA"]
    assert canonical.canonical_json(nd1) == canonical.canonical_json(nd2)
    assert prov1["strategy"] == prov2["strategy"]
    assert prov1["hash_chain"] == prov2["hash_chain"]
    # 并列收益 ⇒ net 字典序（单候选双网等收益夹具）
    ea = _entry(bd, [[2.0, 10.0], [6.0, 10.0], [10.0, 10.0]], pid="PA",
                net="NA")
    eb = _entry(bd, [[2.0, 20.0], [6.0, 20.0], [10.0, 20.0], [14.0, 20.0]])
    eb["net_id"], eb["partition_id"] = "NB", "PB"
    eb["polyline"] = [[2.0, 20.0], [6.0, 20.0], [14.0, 20.0]]  # 1 候选=并列
    _nd, prov = postprocess_routes(bd, _doc(bd, [ea, eb]))
    assert prov["strategy"]["group_order"] \
        == [{"net": "NA", "benefit": 1}, {"net": "NB", "benefit": 1}]


def test_v21_pool_exhaustion_group_state_marking():
    """R10E2B-C/E 分池耗尽组态标钉值：budget={P1:2} ⇒ NB（先执行，恰耗尽
    且候选清空）CONVERGED 保持、NA（未及执行）整组 NOT_CONVERGED_BUDGET+
    组粒度残量披露（by_net.residual_by_pass）；P1 池耗尽 ⇒ by_pass.P1=
    NOT_CONVERGED_BUDGET。"""
    bd = _two_net_bd()
    doc = _two_net_doc(bd)
    nd1, prov1 = postprocess_routes(
        bd, doc, budget={"P1": 2, "P2a": 0, "P2b": 0, "P3": 0})
    term = prov1["termination"]
    assert prov1["budget"]["by_pass"]["P1"] \
        == {"cap": 2, "consumed": 2, "applied": 2, "remaining": 0,
            "capped": True}
    assert term["status"] == "NOT_CONVERGED_BUDGET"
    assert term["by_pass"]["P1"] == {"status": "NOT_CONVERGED_BUDGET",
                                     "residual_candidates": 1}
    assert term["by_net"]["NB"]["status"] == "CONVERGED"      # 已完成组保持
    assert term["by_net"]["NB"]["residual_candidates"] == 0
    assert term["by_net"]["NA"]["status"] == "NOT_CONVERGED_BUDGET"  # 整组
    assert term["by_net"]["NA"]["residual_candidates"] == 1
    assert term["by_net"]["NA"]["residual_by_pass"]["P1"] == 1
    assert nd1["routes"][0]["polyline"] == [[2.0, 10.0], [6.0, 10.0],
                                            [10.0, 10.0]]     # NA 未被触
    assert nd1["routes"][1]["polyline"] == [[2.0, 20.0], [14.0, 20.0]]


def test_v21_resume_skips_converged_groups():
    """R10E2B-D 断点续跑钉值：二次调用=续跑——入场枚举零候选组（NB）跳过
    不重扫（strategy.resume.skipped_groups+by_net.skipped），未收敛组（NA）
    残量被消费（applied>0）至 CONVERGED；三调零改（幂等面）。"""
    bd = _two_net_bd()
    doc = _two_net_doc(bd)
    nd1, prov1 = postprocess_routes(
        bd, doc, budget={"P1": 2, "P2a": 0, "P2b": 0, "P3": 0})
    assert prov1["termination"]["status"] == "NOT_CONVERGED_BUDGET"
    nd2, prov2 = postprocess_routes(bd, nd1)          # 断点续跑（新池）
    assert prov2["strategy"]["resume"]["skipped_groups"] == ["NB"]
    assert prov2["strategy"]["groups_executed"] == ["NA"]
    assert prov2["termination"]["by_net"]["NB"]["skipped"] is True
    assert prov2["termination"]["by_net"]["NB"]["status"] == "CONVERGED"
    assert prov2["actions"]["P1"]["applied"] == 1     # NA 残量被消费
    assert prov2["termination"]["status"] == "CONVERGED"
    assert nd2["routes"][0]["polyline"] == [[2.0, 10.0], [10.0, 10.0]]
    assert nd2["routes"][1] == nd1["routes"][1]       # NB 零改（跳过面）
    nd3, prov3 = postprocess_routes(bd, nd2)          # 三调零改
    assert prov3["changed"] is False
    assert prov3["strategy"]["resume"]["skipped_groups"] == ["NA", "NB"]
    assert prov3["actions"]["P1"]["applied"] == 0
    assert canonical.canonical_json(nd3) == canonical.canonical_json(nd2)


def test_v21_j3_idempotency_face():
    """R10E2B-F J3 幂等面口径钉值：CONVERGED 板复调零改（canonical 字节等+
    全 pass delta=0）才可标幂等（工装面判定=true）；not_converged 板幂等
    =null 如实（构造性不可主张）；模块内 idempotency 恒 null+主张前置标注
    （termination.status==CONVERGED）=状态机硬前置。"""
    bd = _two_net_bd()
    doc = _two_net_doc(bd)
    nd1, prov1 = postprocess_routes(
        bd, doc, budget={"P1": 2, "P2a": 0, "P2b": 0, "P3": 0})
    nd2, prov2 = postprocess_routes(bd, nd1)          # 续跑至 CONVERGED

    def j3_face(final_doc, prov):                     # 工装面 J3 判定
        if prov["termination"]["status"] != "CONVERGED":
            return None
        re_doc, re_prov = postprocess_routes(bd, final_doc)
        zero = (re_prov["changed"] is False
                and canonical.canonical_json(re_doc)
                == canonical.canonical_json(final_doc)
                and (all(re_prov["passes"][p]["delta"]["applied"] == 0
                         for p in _PRIM_KEYS)
                     or re_prov["reverted_all"] is True))
        return True if zero else False

    assert prov2["termination"]["status"] == "CONVERGED"
    assert j3_face(nd2, prov2) is True                # CONVERGED ⇒ 可标
    # not_converged 板（P1 池耗尽）：幂等面=null（不可主张）
    _nd_c, prov_c = postprocess_routes(
        bd, doc, budget={"P1": 2, "P2a": 0, "P2b": 0, "P3": 0})
    assert prov_c["termination"]["status"] == "NOT_CONVERGED_BUDGET"
    assert j3_face(nd1, prov_c) is None
    # 模块面：idempotency 恒 null+主张前置标注（两态同面）
    for prov in (prov_c, prov2):
        assert prov["idempotency"] is None
        assert prov["gates"]["idempotency"]["claim_precondition"] \
            == "termination.status==CONVERGED"


def test_v21_enumerate_candidates_descriptors():
    """R10E2B-A 公开枚举器钉值：描述子键面 (pass, net, entry_idx, pos,
    dphi, needs_recheck, self_rejecting)；P1 needs_recheck=False（免复检
    面）、P2a/P2b/P3=True；确定性（两次调用逐位等）+与 provenance 策略面
    摘要同源（无自拒形态夹具上 descriptors_sha256 相等）。"""
    bd = _two_net_bd()
    doc = _two_net_doc(bd)
    cands = enumerate_candidates(bd, doc)
    keys = {"pass", "net", "entry_idx", "pos", "dphi",
            "needs_recheck", "self_rejecting"}
    assert cands and all(set(c) == keys for c in cands)
    assert all(c["self_rejecting"] is False for c in cands)
    by_net = {}
    for c in cands:
        by_net.setdefault(c["net"], 0)
        by_net[c["net"]] += 1
    assert by_net == {"NA": 1, "NB": 2}
    for c in cands:
        if c["pass"] == "P1":
            assert c["needs_recheck"] is False and c["dphi"] == -1
    _nd, prov = postprocess_routes(bd, doc)
    assert prov["strategy"]["enumeration"]["candidates_total"] == 3
    assert prov["strategy"]["enumeration"]["descriptors_sha256"] \
        == canonical.canonical_sha256(cands)   # 无自拒形态 ⇒ 同源
    assert enumerate_candidates(bd, doc) == cands         # 确定性
    with pytest.raises(ValueError):
        enumerate_candidates(bd, {"routes": "not-a-list"})
