# -*- coding: utf-8 -*-
"""APPLY-1 纯函数/账本测试（不碰 live 板；几何用合成数据，账本只读 evidence）。

覆盖：
- board_writer.route_uuid 内容派生确定性 + 与 batch-plan 账本一致；
- batch-routes 账本与两网 witness 证据链一致（段/孔数、宽、层）；
- route_interference 互扰判定（同层近距报警 / 远距放行 / 跨层放行）；
- fb1_experiment.batch_verdict 批门语义（零新增 error 接受，新增拒绝）；
- apply_routes + extract_net_nodes + witness_vs_board 合成板闭环对账。
"""

import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pcbflow import board_writer, fb1_experiment  # noqa: E402

_APPLY1_DIR = os.path.join(os.path.dirname(HERE), "out", "coreboard-apply1")
_EVIDENCE = os.path.join(_APPLY1_DIR, "evidence")


def _load_apply1_module():
    spec = importlib.util.spec_from_file_location(
        "apply1_orchestrate",
        os.path.join(_APPLY1_DIR, "apply1_orchestrate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evidence(name):
    with open(os.path.join(_EVIDENCE, name), encoding="utf-8") as f:
        return json.load(f)


def _batch_routes():
    with open(os.path.join(_EVIDENCE, "batch-routes.json"),
              encoding="utf-8") as f:
        return json.load(f)


# ---- uuid 内容派生与账本一致 --------------------------------------------------
def test_apply1_route_uuid_content_derivation_matches_ledger():
    A1 = _load_apply1_module()
    routes = _batch_routes()
    assert len(routes) == 2
    for route in routes:
        derived = board_writer.route_uuid(route)
        assert derived == route["uuid"]
    plan = _evidence("batch-plan.json")
    assert plan["prims"]["3V3"]["uuid"] == routes[0]["uuid"]
    assert plan["prims"]["GPIO_PE2"]["uuid"] == routes[1]["uuid"]
    # 确定性：同内容重复派生同 uuid
    assert board_writer.route_uuid(routes[0]) == \
        board_writer.route_uuid(dict(routes[0]))


def test_apply1_batch_routes_match_witness_ledger():
    routes = _batch_routes()
    plan = _evidence("batch-plan.json")
    w3 = _evidence("witness-3v3.json")
    wp = _evidence("witness-gpio_pe2.json")
    r3v3, rpe2 = routes
    assert r3v3["net"] == "3V3" and rpe2["net"] == "GPIO_PE2"
    # 3V3：S2 witness 复验账（44 段 0 孔 F.Cu w=0.2）
    assert w3["verdict"] == "SAT-RECONFIRMED"
    assert w3["independent_check"]["all_ok"] is True
    assert len(r3v3["segments"]) == 44 and len(r3v3["vias"]) == 0
    assert plan["prims"]["3V3"]["segments"] == 44
    assert plan["prims"]["3V3"]["layers"] == [0]
    assert abs(r3v3["width"] - 0.2) < 1e-9
    # GPIO_PE2：本包求解账（66 段 3 孔 w=0.15，层 0/6）
    assert wp["verdict"] == "SAT"
    assert wp["plain_solve"]["sweep_length_match"] is True
    assert wp["independent_check"]["all_ok"] is True
    assert wp["interference_3v3_vs_plain"]["pairs"] == 0
    assert len(rpe2["segments"]) == 66 and len(rpe2["vias"]) == 3
    assert plan["prims"]["GPIO_PE2"]["segments"] == 66
    assert sorted(plan["prims"]["GPIO_PE2"]["layers"]) == [0, 6]
    assert abs(rpe2["width"] - 0.15) < 1e-9
    assert abs(rpe2["via_size"] - 0.6) < 1e-9
    assert abs(rpe2["via_drill"] - 0.3) < 1e-9
    # 批纪律：单批 2 网 ≤10 网
    assert len(routes) <= 10


# ---- 互扰判定（合成几何，纯函数） --------------------------------------------
def _mk_route(net, segs, width=0.2):
    return {"net": net, "width": width, "via_size": 0.6, "via_drill": 0.3,
            "segments": segs, "vias": []}


def test_apply1_interference_near_same_layer_flags():
    A1 = _load_apply1_module()
    a = _mk_route("A", [[0, 10.0, 10.0, 20.0, 10.0]])
    b = _mk_route("B", [[0, 10.0, 10.3, 20.0, 10.3]])
    hits = A1.route_interference(a, b)
    assert len(hits) == 1
    assert hits[0]["kind"] == "seg-seg"
    assert abs(hits[0]["dist_mm"] - 0.3) < 1e-6
    # 阈值 = (0.2+0.2)/2 + 0.2 = 0.4 > 0.3 → 互扰
    assert hits[0]["thr_mm"] > hits[0]["dist_mm"]


def test_apply1_interference_far_or_cross_layer_clears():
    A1 = _load_apply1_module()
    a = _mk_route("A", [[0, 10.0, 10.0, 20.0, 10.0]])
    far = _mk_route("B", [[0, 10.0, 11.0, 20.0, 11.0]])
    assert A1.route_interference(a, far) == []
    cross = _mk_route("B", [[6, 10.0, 10.0, 20.0, 10.0]])  # In2.Cu vs F.Cu
    assert A1.route_interference(a, cross) == []
    segv = _mk_route("B", [], width=0.2)
    segv["vias"] = [[15.0, 11.2]]
    assert A1.route_interference(a, segv) == []  # via 半径 0.3+0.1+0.2=0.6>1.2? 否：
    # 1.2mm 间距 > (0.6/2 + 0.2/2 + 0.2) = 0.6 → 放行
    nearv = _mk_route("C", [])
    nearv["vias"] = [[15.0, 10.4]]
    hits = A1.route_interference(a, nearv)
    assert len(hits) == 1 and hits[0]["kind"] == "via-seg"


# ---- 批门语义（合成 DRC 账，纯函数） -----------------------------------------
def _viol(drc, typ, sev, desc):
    return {"type": typ, "severity": sev, "description": desc,
            "items": [{"description": desc, "pos": {"x": 0, "y": 0}}]}


def test_apply1_batch_verdict_accepts_zero_new_error():
    base = {"violations": [_viol(0, "copper_edge_clearance", "error", "e1"),
                           _viol(1, "silk_over_copper", "warning", "w1")],
            "unconnected_items": [1, 2]}
    cand = {"violations": [_viol(0, "copper_edge_clearance", "error", "e1")],
            "unconnected_items": [1]}
    v = fb1_experiment.batch_verdict(base, cand)
    assert v["accepted"] is True
    assert v["new_errors_vs_baseline"] == 0


def test_apply1_batch_verdict_rejects_new_error():
    base = {"violations": [_viol(0, "copper_edge_clearance", "error", "e1")],
            "unconnected_items": []}
    cand = {"violations": [_viol(0, "copper_edge_clearance", "error", "e1"),
                           _viol(1, "clearance", "error", "new-short")],
            "unconnected_items": []}
    v = fb1_experiment.batch_verdict(base, cand)
    assert v["accepted"] is False
    assert v["new_errors_vs_baseline"] == 1
    assert any("new-short" in d for d in v["new_detail"])


# ---- apply_routes → 抽取 → 对账闭环（合成板文本） ----------------------------
def test_apply1_apply_routes_extract_roundtrip():
    A1 = _load_apply1_module()
    routes = _batch_routes()
    pristine = ('(kicad_pcb (version 20221018)\n'
                '\t(layers)\n'
                '\t(segment\n'
                '\t\t(start 0.0 0.0)\n'
                '\t\t(end 1.0 0.0)\n'
                '\t\t(width 0.2)\n'
                '\t\t(layer "F.Cu")\n'
                '\t\t(net "GND")\n'
                '\t\t(uuid "00000000-0000-0000-0000-000000000000")\n'
                '\t)\n'
                ')\n')
    new_text = board_writer.apply_routes(pristine, routes, eol="auto")
    # 既有节点字节保留（首段仍在，且 pristine 前缀不变）
    assert '(net "GND")' in new_text
    assert new_text.startswith(pristine[:pristine.index("\t(segment")])
    for route in routes:
        acct = A1.extract_net_nodes(new_text, route["uuid"])
        assert A1.witness_vs_board(route, acct) == []
        assert len(acct["segments"]) == len(route["segments"])
        assert len(acct["vias"]) == len(route["vias"])
    # 破坏一段 → 对账必须报错（负例）
    first_uuid = routes[0]["uuid"]
    broken = new_text.replace('(start 41.4000 56.3500)', '(start 41.4000 56.3501)', 1)
    acct = A1.extract_net_nodes(broken, first_uuid)
    assert A1.witness_vs_board(routes[0], acct) != []
