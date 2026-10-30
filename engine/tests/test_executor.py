# -*- coding: utf-8 -*-
"""L7 走廊执行器与 routes 判定编排测试（V5.0 P4 第⑤路交付；stdlib+pytest）。

覆盖：
- demo 验收锚（P4-G1 压力口径）：demo-02/03 ROUTED 且 route_check feasible；
  demo-01 **如实 FAILED**（C1/F.Cu 固定铜容量溢出 4.7 > 4.3 的口径缝，见
  test_demo01_fixed_only_capacity_seam）——不造假 ROUTED；
- 确定性：同输入双跑 routes canonical 字节相等（硬测试）；
- v5.routes.v1 工件校验器 fail-closed 键路径（合同逐条）；
- route_check 判定编排（R5/R2/R6/capacity/R1/R4/结构/同分区豁免/ribbon 去重）；
- 执行器单元（ribbon/DIFF/宽度保守下限/R4 配孔/事务语义/落盘/候选校验/pour 接口位）。
板只读；落盘只进 pytest tmp_path。

已知合同缝（测试即文档，汇报不修）：v5.board.v1 schema（P0 冻结件）的 geometry
additionalProperties:false 且无 pour 字段——pour 分区无法经 L0 载入；pour 接口位
按前向兼容键 geometry.pour 实现，专项测试以未过 L0 校验的构造 dict 驱动。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5 import executor as ex_mod  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5.executor import (EXECUTOR_VERSION, ExecutorError, _NetTransaction,  # noqa: E402
                         _Context, execute_candidate)
from v5.route_check import (ROUTES_SCHEMA_VERSION, ROUTE_CHECK_VERSION,  # noqa: E402
                            RouteCheckError, check_routes, validate_routes)

BOARDS = os.path.join(ROOT, "boards", "d")


# ---------------------------------------------------------------- 夹具与助手

_CACHE = {}


def _load(bid):
    if bid not in _CACHE:
        with open(os.path.join(BOARDS, "%s.board.v1.json" % bid),
                  encoding="utf-8") as f:
            _CACHE[bid] = load_board(json.load(f))
    return _CACHE[bid]


def _exec(bid):
    """每板只跑一次执行器（模块级缓存；demo-02 ~20s 为最贵用例）。"""
    key = ("exec", bid)
    if key not in _CACHE:
        board = _load(bid)
        from v5.compiler import compile_board
        from v5.planner import plan_candidates
        art, _ = compile_board(board)
        cand = plan_candidates(board, art, arm="principle")[0]
        _CACHE[key] = (board, execute_candidate(board, cand))
    return _CACHE[key]


def make_board(*, workspace, stackup, partitions, nets, zones=None,
               hard_rules=None, board_id="t", validate=True):
    """构造板 + provenance 落链（默认过 v5.board.load_board fail-closed）。"""
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": stackup,
        "workspace": workspace,
        "zones": zones or [],
        "partitions": partitions,
        "nets": nets,
        "hard_rules": hard_rules or {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "hand",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    if validate:
        return load_board(board)
    return board


SIG = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
       {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True}]
WS = {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 20.0}


def part(pid, a, b, ptype="MISC", layer="F.Cu", width=0.2, current=0.0,
         wmin=None, wmax=None, **geo):
    g = {"endpoints": [list(a), list(b)]}
    g.update(geo)
    return {"partition_id": pid, "ptype": ptype, "layer_policy": layer,
            "planned_width": width, "current_a": current, "geometry": g,
            "speed_class": "low_speed",
            "width_prior": {"w_min": width if wmin is None else wmin,
                            "w_max": width if wmax is None else wmax}}


def net(nid, pids):
    return {"net_id": nid, "net_class": "MISC", "partitions": list(pids)}


def cand_for(board, order=None, layers=None, cid="C-001"):
    parts = [p["partition_id"] for p in board["partitions"]]
    order = order or parts
    layers = layers or {p["partition_id"]: p["layer_policy"]
                        for p in board["partitions"]}
    return {"candidate_id": cid, "arm": "no-principle",
            "provenance": {"generator": "v5.planner/0.1.0", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": order, "layer_assignment": layers,
            "polylines": {}, "generation_trace": []}


def routes_doc(board, entries, **extra):
    sha = compute_board_sha256(board)
    doc = {"schema_version": ROUTES_SCHEMA_VERSION, "board_id": board["board_id"],
           "board_sha256": sha, "routes": entries, "negotiation_log": ["t"],
           "provenance": {"generator": "v5.executor/0.1.0", "board_sha256": sha}}
    doc.update(extra)
    return doc


def entry(pid, nid, layer, pts, width=0.2, tv=None, rv=None):
    return {"partition_id": pid, "net_id": nid, "layer": layer,
            "polyline": [list(p) for p in pts], "width": width,
            "transition_vias": [list(v) for v in (tv or [])],
            "return_vias": [list(v) for v in (rv or [])]}


# ---------------------------------------------------------------- 1. demo 验收锚

def test_demo03_executor_routed_and_feasible():
    """P4-G1 锚：demo-03 ROUTED 且全 routes 过 route_check（A9 口径）。"""
    board, res = _exec("demo-03-small-mixed")
    assert res["verdict"] == "ROUTED" and res["routes"] is not None
    assert check_routes(board, res["routes"])["feasible"] is True
    assert all(pn["status"] in ("routed", "fixed", "ribbon")
               for pn in res["per_net"])


def test_demo02_executor_routed_and_feasible():
    """P4-G1 锚：demo-02 ROUTED（含协商兜底网）且 route_check feasible。"""
    board, res = _exec("demo-02-mixed-types")
    assert res["verdict"] == "ROUTED"
    assert check_routes(board, res["routes"])["feasible"] is True
    assert res["routes"]["ribbon_groups"]["BS1"]["net_ids"] == \
        ["BUS-D0", "BUS-D1", "BUS-D2", "BUS-D3"]


def test_demo01_executor_honest_failed():
    """P4-G1 压力锚：demo-01 如实 FAILED、routes=None（不造假 ROUTED）。"""
    board, res = _exec("demo-01-v2-corridor")
    assert res["verdict"] == "FAILED" and res["routes"] is None
    # 逐网其实全部布通（失败不在布线能力，在板数据口径——见下一条缝测试）
    assert all(pn["status"] in ("routed", "fixed", "ribbon")
               for pn in res["per_net"])
    assert any("capacity" in line and "C1/F.Cu" in line
               for line in res["negotiation_log"])


def test_demo01_fixed_only_capacity_seam():
    """口径缝文档化（汇报不修）：C1/F.Cu 固定铜（ribbon 3.3 + P7 0.2 + P9 0.2 +
    2×0.5 间距 = 4.7）在**零 routes** 时已溢出声明容量 4.3；归责口径（capacity 恒
    归责 routes，镜像 selection._candidate_attribution）使其必然 infeasible——
    demo-01 的阻塞点是板数据/容量核算缝，不是布线搜索失败。"""
    board = _load("demo-01-v2-corridor")
    empty = routes_doc(board, [])
    report = check_routes(board, empty)
    assert report["feasible"] is False
    cap = [v for v in report["attributed_violations"] if v["rule"] == "capacity"]
    assert len(cap) == 1 and cap[0]["subjects"][0] == "C1/F.Cu"
    terms = report["capacity_meta"]["C1/F.Cu"]["terms"]
    assert terms == [3.3, 0.2, 0.2]          # 全部固定铜，无任何 route 铜
    occ = round(sum(terms) + 0.5 * (len(terms) - 1), 10)
    assert occ == 4.7 > 4.3


def test_p4g1_gate_two_of_three():
    """P4-G1 门算术：三板 ROUTED ≥ 2/3（demo-01 如实 FAILED 计入分母）。"""
    verdicts = [_exec(b)[1]["verdict"] for b in
                ("demo-01-v2-corridor", "demo-02-mixed-types", "demo-03-small-mixed")]
    assert verdicts == ["FAILED", "ROUTED", "ROUTED"]
    assert verdicts.count("ROUTED") >= 2


def test_demo02_negotiation_fallback_triggered():
    """协商兜底实证：demo-02 PW1 首选档路径被网级 v5.drc 门（R2 整线累计）拒绝后，
    兜底切 overlap_free 档提交——negotiated=True + 尝试阶梯留痕。"""
    board, res = _exec("demo-02-mixed-types")
    pw1 = next(pn for pn in res["per_net"] if pn["partition_id"] == "PW1")
    assert pw1["status"] == "routed" and pw1["negotiated"] is True
    assert pw1["attempts"] >= 2
    assert any("attempt=1" in ln and "failed" in ln and "R2" in ln
               for ln in res["negotiation_log"])


# ---------------------------------------------------------------- 2. 确定性

def test_double_run_byte_equal_demo03():
    """同输入双跑 routes canonical 字节相等（硬测试；任务书 P4 要求）。"""
    board = _load("demo-03-small-mixed")
    from v5.compiler import compile_board
    from v5.planner import plan_candidates
    art, _ = compile_board(board)
    cand = plan_candidates(board, art, arm="principle")[0]
    r1 = execute_candidate(board, cand)
    r2 = execute_candidate(board, cand)
    assert canonical.canonical_json(r1["routes"]) == \
        canonical.canonical_json(r2["routes"])
    assert r1["negotiation_log"] == r2["negotiation_log"]
    assert r1["per_net"] == r2["per_net"]


def test_double_run_byte_equal_demo02():
    """确定性（含协商路径）：demo-02 双跑字节等（协商阶梯本身确定性）。"""
    board, res1 = _exec("demo-02-mixed-types")
    from v5.compiler import compile_board
    from v5.planner import plan_candidates
    art, _ = compile_board(board)
    cand = plan_candidates(board, art, arm="principle")[0]
    res2 = execute_candidate(board, cand)
    assert canonical.canonical_json(res1["routes"]) == \
        canonical.canonical_json(res2["routes"])


def test_check_routes_pure_function():
    """check_routes 纯函数：同输入双跑结果字典相等。"""
    board, res = _exec("demo-03-small-mixed")
    assert check_routes(board, res["routes"]) == check_routes(board, res["routes"])


# ---------------------------------------------------------------- 3. 工件校验

def test_validate_routes_accepts_executor_output():
    """执行器产物过 validate_routes（含披露附加键与 provenance 头）。"""
    board, res = _exec("demo-03-small-mixed")
    assert validate_routes(board, res["routes"]) is True
    doc = res["routes"]
    assert doc["schema_version"] == ROUTES_SCHEMA_VERSION
    assert doc["provenance"]["generator"] == EXECUTOR_VERSION
    assert doc["board_sha256"] == board["provenance"]["board_sha256"]
    assert doc["provenance"]["board_sha256"] == doc["board_sha256"]
    assert doc["fixed_partitions"] == ["RT1"]


_BASE_ENTRY = {"demo-03-small-mixed": ("MS1", "MISC-A", "F.Cu",
                                       [[2.0, 8.0], [10.0, 8.0]]),
               "demo-02-mixed-types": ("CK1", "CLK-SYS", "F.Cu",
                                       [[4.0, 4.0], [56.0, 4.0]])}


def _assert_key_path_error(board, mutate, key_frag):
    pid, nid, layer, pts = _BASE_ENTRY[board["board_id"]]
    base = routes_doc(board, [entry(pid, nid, layer, pts)])
    mutate(base)
    with pytest.raises(RouteCheckError) as ei:
        validate_routes(board, base)
    assert key_frag in str(ei.value)


def test_validate_rejects_wrong_schema_version():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["schema_version"] = "v5.routes.v0"
    _assert_key_path_error(board, m, "schema_version")


def test_validate_rejects_board_id_mismatch():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["board_id"] = "other-board"
    _assert_key_path_error(board, m, "board_id")


def test_validate_rejects_bad_board_sha():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["board_sha256"] = "zz" * 32
    _assert_key_path_error(board, m, "board_sha256")


def test_validate_rejects_sha_chain_mismatch():
    """board_sha256 与板 provenance 哈希链不复算（错板错件配对）→ 拒。"""
    board = _load("demo-03-small-mixed")

    def m(d):
        d["board_sha256"] = "ab" * 32
        d["provenance"]["board_sha256"] = "ab" * 32
    _assert_key_path_error(board, m, "哈希链")


def test_validate_rejects_degenerate_polyline():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["routes"][0]["polyline"] = [[2.0, 8.0]]
    _assert_key_path_error(board, m, "routes[0].polyline")


def test_validate_rejects_nonfinite_coord():
    board = _load("demo-03-small-mixed")
    doc = routes_doc(board, [entry("MS1", "MISC-A", "F.Cu",
                                   [[2.0, 8.0], [10.0, None]])])
    with pytest.raises(RouteCheckError) as ei:
        validate_routes(board, doc)
    assert "routes[0].polyline" in str(ei.value)


def test_validate_rejects_nonpositive_width():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["routes"][0]["width"] = 0.0
    _assert_key_path_error(board, m, "routes[0].width")


def test_validate_rejects_unavailable_layer():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["routes"][0]["layer"] = "In2.Cu"   # plane 层，available=false
    _assert_key_path_error(board, m, "routes[0].layer")


def test_validate_rejects_unknown_layer():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["routes"][0]["layer"] = "Top.Gold"
    _assert_key_path_error(board, m, "routes[0].layer")


def test_validate_rejects_extra_entry_key():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["routes"][0]["note"] = "hello"
    _assert_key_path_error(board, m, "合同外键")


def test_validate_rejects_unknown_top_key():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["surprise"] = 1
    _assert_key_path_error(board, m, "合同外顶层键")


def test_validate_rejects_endpoint_violation():
    """首末点=分区端点（合同）。"""
    board = _load("demo-03-small-mixed")

    def m(d):
        d["routes"][0]["polyline"][0] = [5.0, 5.0]
    _assert_key_path_error(board, m, "首末点")


def test_validate_rejects_net_partition_mismatch():
    board = _load("demo-03-small-mixed")
    doc = routes_doc(board, [entry("MS1", "MISC-B", "F.Cu",
                                   [[2.0, 8.0], [10.0, 8.0]])])
    with pytest.raises(RouteCheckError) as ei:
        validate_routes(board, doc)
    assert "不引用分区" in str(ei.value)


def test_validate_rejects_unknown_net():
    board = _load("demo-03-small-mixed")
    doc = routes_doc(board, [entry("MS1", "NOPE", "F.Cu", [[2.0, 8.0], [10.0, 8.0]])])
    with pytest.raises(RouteCheckError):
        validate_routes(board, doc)


def test_validate_rejects_broken_multi_run_chain():
    """多段网：衔接点未在双方 transition_vias 披露 → 拒（键路径 routes）。"""
    board = _load("demo-03-small-mixed")
    doc = routes_doc(board, [
        entry("MS1", "MISC-A", "F.Cu", [[2.0, 8.0], [6.0, 8.0]], tv=[[6.0, 8.0]]),
        entry("MS1", "MISC-A", "B.Cu", [[6.0, 8.0], [10.0, 8.0]], tv=[]),
    ])
    with pytest.raises(RouteCheckError) as ei:
        validate_routes(board, doc)
    assert "transition_vias" in str(ei.value)


def test_validate_accepts_multi_run_chain():
    board = _load("demo-03-small-mixed")
    doc = routes_doc(board, [
        entry("MS1", "MISC-A", "F.Cu", [[2.0, 8.0], [6.0, 8.0]], tv=[[6.0, 8.0]]),
        entry("MS1", "MISC-A", "B.Cu", [[6.0, 8.0], [10.0, 8.0]], tv=[[6.0, 8.0]]),
    ])
    assert validate_routes(board, doc) is True


def test_validate_rejects_bad_ribbon_groups():
    board = _load("demo-02-mixed-types")

    def m(d):
        d["ribbon_groups"] = {"NOPE": {"net_ids": [], "occupancy_mm": 1.0,
                                       "route_index": 0}}
    _assert_key_path_error(board, m, "ribbon_groups")


def test_validate_rejects_bad_negotiation_log():
    board = _load("demo-03-small-mixed")

    def m(d):
        d["negotiation_log"] = [1, 2]
    _assert_key_path_error(board, m, "negotiation_log")


# ---------------------------------------------------------------- 4. route_check 判定

def test_check_routes_feasible_simple():
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (1, 1), (19, 1))],
                       nets=[net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu", [[1.0, 1.0], [19.0, 1.0]])])
    rep = check_routes(board, doc)
    assert rep["feasible"] is True and rep["violations"] == []
    assert rep["drc_version"].startswith("v5.drc/")
    assert rep["route_check_version"] == ROUTE_CHECK_VERSION


def test_check_routes_r5_attributed():
    """R5：route 距既布铜 < 0.5 → 归责 routes → infeasible。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("PX", (1, 5), (19, 5), ptype="ROUTED"),
                                   part("P1", (1, 5.3), (19, 5.3))],
                       nets=[net("NX", ["PX"]), net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu", [[1.0, 5.3], [19.0, 5.3]])])
    rep = check_routes(board, doc)
    assert rep["feasible"] is False
    assert any(v["rule"] == "R5" for v in rep["attributed_violations"])


def test_check_routes_fixed_fixed_not_attributed():
    """固定铜互扰 = 板内固有缺陷，不归责 routes → feasible 保持 True。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("PA", (1, 5), (19, 5), ptype="ROUTED"),
                                   part("PB", (1, 5.4), (19, 5.4), ptype="ROUTED")],
                       nets=[net("NA", ["PA"]), net("NB", ["PB"])])
    doc = routes_doc(board, [])     # 零 routes：纯板内缺陷
    rep = check_routes(board, doc)
    assert rep["feasible"] is True
    assert any(v["rule"] == "R5" for v in rep["violations"])


def test_check_routes_r6_keepout_attributed():
    """R6：route 入禁布区 → 违例；绕行（逐段 bbox 间隙 >0）→ 合规。"""
    zones = [{"zone_id": "K1", "kind": "keepout", "layers": "all",
              "rect": {"x_min": 8.0, "y_min": 0.0, "x_max": 12.0, "y_max": 12.0}}]
    board = make_board(workspace=WS, stackup=SIG, zones=zones,
                       partitions=[part("P1", (1, 1), (19, 1))],
                       nets=[net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu", [[1.0, 1.0], [19.0, 1.0]])])
    rep = check_routes(board, doc)
    assert rep["feasible"] is False
    assert any(v["rule"] == "R6" for v in rep["attributed_violations"])
    doc2 = routes_doc(board, [entry("P1", "N1", "F.Cu",
                                    [[1.0, 1.0], [7.75, 1.0], [7.75, 12.25],
                                     [12.25, 12.25], [12.25, 1.0], [19.0, 1.0]])])
    assert check_routes(board, doc2)["feasible"] is True


def test_check_routes_r2_attributed_and_far_clean():
    """R2：近距平行 > max_parallel → 违例；远距平行同布局 → 合规（整线近距门）。"""
    zones = [{"zone_id": "S1", "kind": "sensitive", "layers": "signal",
              "rect": {"x_min": 6.0, "y_min": 8.0, "x_max": 14.0, "y_max": 12.0}}]
    board_near = make_board(workspace=WS, stackup=SIG, zones=zones,
                            partitions=[part("P1", (1, 10), (19, 10))],
                            nets=[net("N1", ["P1"])])
    near = routes_doc(board_near, [entry("P1", "N1", "F.Cu",
                                         [[1.0, 10.0], [19.0, 10.0]])])
    rep = check_routes(board_near, near)
    assert rep["feasible"] is False
    r2 = [v for v in rep["attributed_violations"] if v["rule"] == "R2"]
    assert r2 and r2[0]["data"]["parallel_mm"] > 5.0
    board_far = make_board(workspace=WS, stackup=SIG, zones=zones,
                           partitions=[part("P1", (1, 16), (19, 16))],
                           nets=[net("N1", ["P1"])])
    far = routes_doc(board_far, [entry("P1", "N1", "F.Cu",
                                       [[1.0, 16.0], [19.0, 16.0]])])
    assert check_routes(board_far, far)["feasible"] is True


def test_check_routes_capacity_attributed():
    zones = [{"zone_id": "C1", "kind": "corridor", "layers": "signal",
              "rect": {"x_min": 9.0, "y_min": 0.0, "x_max": 11.0, "y_max": 20.0},
              "capacity": 0.5}]
    board = make_board(workspace=WS, stackup=SIG, zones=zones,
                       partitions=[part("P1", (1, 1), (19, 1))],
                       nets=[net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu", [[1.0, 1.0], [19.0, 1.0]],
                                   width=0.6)])
    rep = check_routes(board, doc)
    assert rep["feasible"] is False
    cap = [v for v in rep["attributed_violations"] if v["rule"] == "capacity"]
    assert cap and cap[0]["subjects"][0] == "C1/F.Cu"
    assert rep["capacity_meta"]["C1/F.Cu"]["terms"] == [0.6]


def test_check_routes_r1_width_attributed():
    """R1：电流分区路线宽 < 保守下限 → 违例（判定口径锚定；执行器侧已杜绝）。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (1, 1), (19, 1), current=2.0,
                                        width=0.5, wmin=0.5, wmax=1.0)],
                       nets=[net("N1", ["P1"])])
    doc = routes_doc(board, [entry("P1", "N1", "F.Cu", [[1.0, 1.0], [19.0, 1.0]],
                                   width=0.5)])
    rep = check_routes(board, doc)
    assert rep["feasible"] is False
    r1 = [v for v in rep["attributed_violations"] if v["rule"] == "R1"]
    assert r1 and r1[0]["data"]["required_min_mm"] == pytest.approx(0.8)
    doc2 = routes_doc(board, [entry("P1", "N1", "F.Cu", [[1.0, 1.0], [19.0, 1.0]],
                                    width=0.8)])
    assert check_routes(board, doc2)["feasible"] is True


def test_check_routes_r4_pairing_audit():
    """R4 结构对账：过渡孔无配对回流孔 / 配对超距 → 违例；合规配对 → 过。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (1, 1), (19, 1))],
                       nets=[net("N1", ["P1"])])
    pts_f = [[1.0, 1.0], [10.0, 1.0]]
    pts_b = [[10.0, 1.0], [19.0, 1.0]]
    good = routes_doc(board, [
        entry("P1", "N1", "F.Cu", pts_f, tv=[[10.0, 1.0]], rv=[[10.75, 1.0]]),
        entry("P1", "N1", "B.Cu", pts_b, tv=[[10.0, 1.0]], rv=[[10.75, 1.0]])])
    assert check_routes(board, good)["feasible"] is True
    missing = routes_doc(board, [
        entry("P1", "N1", "F.Cu", pts_f, tv=[[10.0, 1.0]], rv=[]),
        entry("P1", "N1", "B.Cu", pts_b, tv=[[10.0, 1.0]], rv=[])])
    rep = check_routes(board, missing)
    assert rep["feasible"] is False
    assert any(v["rule"] == "R4" for v in rep["attributed_violations"])
    toofar = routes_doc(board, [
        entry("P1", "N1", "F.Cu", pts_f, tv=[[10.0, 1.0]], rv=[[10.0, 19.0]]),
        entry("P1", "N1", "B.Cu", pts_b, tv=[[10.0, 1.0]], rv=[[10.0, 19.0]])])
    assert check_routes(board, toofar)["feasible"] is False


def test_check_routes_same_partition_r5_exempt():
    """同分区双网（DIFF 对）共享端点：R5 同分区对豁免（pad 级分离在板合同不可
    表达，见 route_check docstring）；不同分区同几何贴行仍判违例。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("DF", (10, 18), (10, 2), ptype="DIFF")],
                       nets=[net("DP", ["DF"]), net("DN", ["DF"])])
    doc = routes_doc(board, [
        entry("DF", "DP", "F.Cu", [[10.0, 18.0], [9.0, 10.0], [10.0, 2.0]]),
        entry("DF", "DN", "F.Cu", [[10.0, 18.0], [11.0, 10.0], [10.0, 2.0]])])
    rep = check_routes(board, doc)
    assert rep["feasible"] is True
    board2 = make_board(workspace=WS, stackup=SIG,
                        partitions=[part("PA", (10, 18), (10, 2)),
                                    part("PB", (10.3, 18), (10.3, 2))],
                        nets=[net("NA", ["PA"]), net("NB", ["PB"])])
    doc2 = routes_doc(board2, [
        entry("PA", "NA", "F.Cu", [[10.0, 18.0], [10.0, 2.0]]),
        entry("PB", "NB", "F.Cu", [[10.3, 18.0], [10.3, 2.0]])])
    rep2 = check_routes(board2, doc2)
    assert rep2["feasible"] is False
    assert any(v["rule"] == "R5" for v in rep2["attributed_violations"])


def test_check_routes_ribbon_dedup_no_double_count():
    """ribbon 去重：铜带分区在容量中只计一次（固定铜声明占用），entry 是声明
    不再构造 route 铜；宽度声明不符 → structure 违例。"""
    zones = [{"zone_id": "C1", "kind": "corridor", "layers": "signal",
              "rect": {"x_min": 9.0, "y_min": 0.0, "x_max": 11.0, "y_max": 20.0},
              "capacity": 2.0}]
    band = part("BS", (10.0, 2.0), (10.0, 18.0), ptype="BUS", width=0.15,
                copper_band=[9.2, 10.8], occupancy_mm=1.6)
    board = make_board(workspace=WS, stackup=SIG, zones=zones,
                       partitions=[band], nets=[net("B0", ["BS"]), net("B1", ["BS"])])
    doc = routes_doc(board, [entry("BS", "B0", "F.Cu",
                                   [[10.0, 2.0], [10.0, 18.0]], width=1.6)],
                     ribbon_groups={"BS": {"net_ids": ["B0", "B1"],
                                           "occupancy_mm": 1.6, "route_index": 0}})
    rep = check_routes(board, doc)
    assert rep["feasible"] is True
    assert rep["capacity_meta"]["C1/F.Cu"]["terms"] == [1.6]   # 只计一次
    bad = routes_doc(board, [entry("BS", "B0", "F.Cu",
                                   [[10.0, 2.0], [10.0, 18.0]], width=0.15)])
    rep2 = check_routes(board, bad)
    assert rep2["feasible"] is False
    assert any(v["rule"] == "structure" for v in rep2["attributed_violations"])


# ---------------------------------------------------------------- 5. 执行器单元

def test_executor_ribbon_group_disclosure():
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("BS", (10, 2), (10, 18), ptype="BUS",
                                        width=0.15, copper_band=[9.2, 10.8],
                                        occupancy_mm=1.6)],
                       nets=[net("B0", ["BS"]), net("B1", ["BS"])])
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "ROUTED"
    doc = res["routes"]
    assert len(doc["routes"]) == 1
    e = doc["routes"][0]
    assert e["net_id"] == "B0" and e["width"] == 1.6
    assert doc["ribbon_groups"]["BS"]["net_ids"] == ["B0", "B1"]
    pn = res["per_net"][0]
    assert pn["status"] == "ribbon" and pn["attempts"] == 0


def test_executor_routed_partition_passthrough():
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("RT", (2, 5), (18, 5), ptype="ROUTED")],
                       nets=[net("NR", ["RT"])])
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "ROUTED"
    assert res["routes"]["routes"][0]["polyline"] == [[2.0, 5.0], [18.0, 5.0]]
    assert res["routes"]["fixed_partitions"] == ["RT"]


def test_executor_diff_pair_two_routes_same_endpoints():
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("DF", (10, 18), (10, 2), ptype="DIFF")],
                       nets=[net("DP", ["DF"]), net("DN", ["DF"])])
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "ROUTED"
    entries = [e for e in res["routes"]["routes"] if e["partition_id"] == "DF"]
    assert len(entries) == 2
    assert {e["net_id"] for e in entries} == {"DP", "DN"}
    for e in entries:
        assert e["polyline"][0] == [10.0, 18.0] and e["polyline"][-1] == [10.0, 2.0]
    assert check_routes(board, res["routes"])["feasible"] is True


def test_executor_r1_conservative_width():
    """电流分区宽度取 R1 保守下限（0.4×2A=0.8），不为 planned 0.5 所骗。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P8", (2, 5), (18, 5), current=2.0,
                                        width=0.5, wmin=0.5, wmax=1.0)],
                       nets=[net("N8", ["P8"])])
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "ROUTED"
    assert res["routes"]["routes"][0]["width"] == pytest.approx(0.8)
    assert check_routes(board, res["routes"])["feasible"] is True


def test_executor_r1_width_prior_contradiction_fail_closed():
    """width_prior.w_max 低于 R1 保守下限 → 板数据矛盾 fail-closed 键路径。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P8", (2, 5), (18, 5), current=2.0,
                                        width=0.5, wmin=0.5, wmax=0.5)],
                       nets=[net("N8", ["P8"])])
    with pytest.raises(ExecutorError) as ei:
        execute_candidate(board, cand_for(board))
    assert "width_prior" in str(ei.value)


def test_executor_layer_hop_via_and_r4_pairing():
    """换层网：过渡孔 + 回流孔配对（≤R4.max_distance），容量/最终检全过。"""
    board, res = _exec("demo-03-small-mixed")
    pw1 = next(pn for pn in res["per_net"] if pn["partition_id"] == "PW1")
    assert pw1["vias"] >= 1
    entries = [e for e in res["routes"]["routes"] if e["net_id"] == "PWR-MAIN"]
    tvs = [tuple(v) for e in entries for v in e["transition_vias"]]
    rvs = [tuple(v) for e in entries for v in e["return_vias"]]
    assert len(tvs) == len(rvs) >= 1
    max_d = board["hard_rules"]["R4"]["max_distance_mm"]
    from v5.metrics import clearance as clr
    for tv in sorted(set(tvs)):
        assert min(clr.point_point(tv, rv) for rv in rvs) <= max_d + 1e-9


def test_executor_corridor_capacity_forces_layer_hop():
    """容量封道：F.Cu 走廊被 ribbon 占满 → 执行器换层穿越；容量账本可审计。"""
    zones = [{"zone_id": "C1", "kind": "corridor", "layers": "signal",
              "rect": {"x_min": 9.0, "y_min": 0.0, "x_max": 11.0, "y_max": 20.0},
              "capacity": 1.6}]
    board = make_board(workspace=WS, stackup=SIG, zones=zones,
                       partitions=[part("PB", (10, 2), (10, 18), ptype="BUS",
                                        width=0.15, copper_band=[9.2, 10.8],
                                        occupancy_mm=1.6),
                                   part("P1", (1, 10), (19, 10))],
                       nets=[net("B0", ["PB"]), net("B1", ["PB"]), net("N1", ["P1"])])
    res = execute_candidate(board, cand_for(board, order=["PB", "P1"]))
    assert res["verdict"] == "ROUTED"
    rep = check_routes(board, res["routes"])
    assert rep["feasible"] is True
    # F.Cu 走廊条目只有 ribbon 本身；P1 在 B.Cu 穿越
    assert rep["capacity_meta"]["C1/F.Cu"]["terms"] == [1.6]
    assert rep["capacity_meta"]["C1/B.Cu"]["terms"] == [0.2]


def test_executor_failed_verdict_no_residue(tmp_path):
    """整体 FAILED：routes=None；out_dir 不落任何工件（sidecar 卫生）。"""
    zones = [{"zone_id": "C1", "kind": "corridor", "layers": "signal",
              "rect": {"x_min": 9.0, "y_min": 0.0, "x_max": 11.0, "y_max": 20.0},
              "capacity": 0.1}]
    board = make_board(workspace=WS, stackup=SIG, zones=zones,
                       partitions=[part("P1", (1, 10), (19, 10))],
                       nets=[net("N1", ["P1"])])
    res = execute_candidate(board, cand_for(board), out_dir=str(tmp_path))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    assert res["per_net"][0]["status"] == "failed"
    assert list(tmp_path.iterdir()) == []          # 无任何落盘
    assert any("FAILED after" in ln for ln in res["negotiation_log"])


def test_executor_out_dir_staging_atomic(tmp_path):
    """ROUTED：工件经 StagingTransaction 原子落盘；staging 无残留；FAILED 不落盘。"""
    from v5 import staging
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (1, 1), (19, 1))],
                       nets=[net("N1", ["P1"])])
    res = execute_candidate(board, cand_for(board), out_dir=str(tmp_path))
    assert res["verdict"] == "ROUTED"
    path = tmp_path / "t.routes" / "t.routes.json"
    assert path.exists()
    raw = path.read_bytes()
    assert raw == canonical.canonical_json(json.loads(raw.decode("utf-8")))
    staging.assert_no_residue(str(tmp_path / "_staging"))
    b1, r1 = _exec("demo-01-v2-corridor")
    assert r1["routes"] is None


def test_executor_rollback_state_fingerprint():
    """_NetTransaction 语义（镜像 StagingTransaction）：commit 生效；rollback
    无残留（状态指纹与快照前逐字节一致）；提交后不可变；空事务不可提交。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (1, 1), (19, 1))],
                       nets=[net("N1", ["P1"])])
    ctx = _Context(board)
    tx = _NetTransaction(ctx, "N1", "P1")
    before = ctx.state_key()
    tx.stage([entry("P1", "N1", "F.Cu", [[1.0, 1.0], [19.0, 1.0]])], [])
    tx.rollback()
    assert ctx.state_key() == before
    assert tx.rolled_back and not tx.committed
    with pytest.raises(ExecutorError):
        tx.stage([], [])
    tx2 = _NetTransaction(ctx, "N1", "P1")
    with pytest.raises(ExecutorError):
        tx2.commit()
    tx3 = _NetTransaction(ctx, "N1", "P1")
    e1 = entry("P1", "N1", "F.Cu", [[1.0, 1.0], [19.0, 1.0]])
    cu1 = ex_mod._RouteCopper("N1", "route:N1:P1#0", "F.Cu", "P1",
                              e1["polyline"], 0.2)
    tx3.stage([e1], [cu1])
    tx3.commit()
    assert tx3.committed and len(ctx.entries) == 1
    with pytest.raises(ExecutorError):
        tx3.rollback()
    with pytest.raises(ExecutorError):
        tx3.stage([], [])


def test_executor_gate_rejection_rolls_back(tmp_path, monkeypatch):
    """中断注入：网级门在第 2 个网抛异常 → 异常传播、无落盘残留（P0 语义移植）。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (1, 10), (19, 10)),
                                   part("P2", (1, 15), (19, 15))],
                       nets=[net("N1", ["P1"]), net("N2", ["P2"])])
    orig = ex_mod._net_gate

    def flaky(ctx, pid, net_id, coppers):
        if net_id == "N2":
            raise RuntimeError("inject")
        return orig(ctx, pid, net_id, coppers)
    monkeypatch.setattr(ex_mod, "_net_gate", flaky)
    with pytest.raises(RuntimeError, match="inject"):
        execute_candidate(board, cand_for(board), out_dir=str(tmp_path))
    assert list(tmp_path.iterdir()) == []   # 中断无半成品工件
    monkeypatch.setattr(ex_mod, "_net_gate", orig)


def test_executor_candidate_fail_closed():
    """候选合同违约 fail-closed 键路径。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("P1", (1, 1), (19, 1))],
                       nets=[net("N1", ["P1"])])
    c = cand_for(board)
    del c["layer_assignment"]["P1"]
    with pytest.raises(ExecutorError) as ei:
        execute_candidate(board, c)
    assert "layer_assignment.P1" in str(ei.value)
    c2 = cand_for(board, order=["P1", "P2"])
    with pytest.raises(ExecutorError) as ei2:
        execute_candidate(board, c2)
    assert "route_order" in str(ei2.value)
    c3 = cand_for(board, layers={"P1": "In9.Cu"})
    with pytest.raises(ExecutorError) as ei3:
        execute_candidate(board, c3)
    assert "layer_assignment.P1" in str(ei3.value)


def test_executor_pour_interface_stub():
    """pour 接口位：geometry.pour 分区照常布端点连线 + pour_regions 披露 +
    工件校验可过（board.v1 schema 无 pour 字段——合同缝见模块 docstring——
    故本测试以未过 L0 的构造 dict 驱动，汇报项）。"""
    board = make_board(workspace=WS, stackup=SIG,
                       partitions=[part("PW", (2, 2), (18, 2), current=1.0,
                                        width=0.6, pour={"x_min": 2.0, "y_min": 0.0,
                                                         "x_max": 18.0, "y_max": 4.0})],
                       nets=[net("NP", ["PW"])], validate=False)
    res = execute_candidate(board, cand_for(board))
    assert res["verdict"] == "ROUTED"
    doc = res["routes"]
    assert doc["pour_regions"]["PW"] == {"x_min": 2.0, "y_min": 0.0,
                                         "x_max": 18.0, "y_max": 4.0}
    assert validate_routes(board, doc) is True


def test_executor_multi_run_endpoint_contract():
    """多段网合同（demo-02 CK1）：首 entry 首点=端点 A、末 entry 末点=端点 B，
    衔接孔在双方 transition_vias 披露。"""
    board, res = _exec("demo-02-mixed-types")
    doc = res["routes"]
    entries = [e for e in doc["routes"] if e["net_id"] == "CLK-SYS"]
    assert len(entries) >= 1
    eps = [list(p) for p in next(
        p["geometry"]["endpoints"] for p in board["partitions"]
        if p["partition_id"] == "CK1")]
    first, last = entries[0], entries[-1]
    assert first["polyline"][0] in eps and last["polyline"][-1] in eps
    for k in range(len(entries) - 1):
        joint = entries[k]["polyline"][-1]
        assert joint in entries[k]["transition_vias"]
        assert joint in entries[k + 1]["transition_vias"]
        assert joint == entries[k + 1]["polyline"][0]


def test_executor_per_net_shape():
    """per_net 形状合同：status/attempts/negotiated/vias/length_mm/layers 齐。"""
    _, res = _exec("demo-03-small-mixed")
    for pn in res["per_net"]:
        assert set(pn) == {"partition_id", "net_id", "status", "attempts",
                           "negotiated", "vias", "length_mm", "width_mm", "layers"}
        assert pn["status"] in ("routed", "failed", "fixed", "ribbon")
        assert pn["negotiated"] == (pn["attempts"] > 1)
        assert pn["length_mm"] >= 0.0 and pn["width_mm"] > 0.0


def test_versions():
    # 升级件⑤-F4 版本升格：executor 0.3.0→0.4.0（F4a/F4b 细档阶梯 + F4c
    # rip-up-and-retry）；⑥波 D6-3 版本升格：executor 0.4.0→0.5.0（板边禁布
    # 带入障碍栅格 + exhaustion 归因 edge-clearance 类）、route_check
    # 0.2.0→0.3.0（edge_violations 消费接口键）；V5-D8 版本升格
    # （2026-09-22 翻转披露）：executor 0.5.0→0.6.0（板固孔禁布带入障碍
    # 栅格 + 归因 hole-keep-out 类）、route_check 0.3.0→0.4.0
    # （hole_violations 消费接口键）；V5-SMALLWAVE 版本升格（2026-09-23
    # 翻转披露）：executor 0.6.0→0.6.1（exhaustion-cause 后补 geom-secondary
    # 几何二级归因 log 行，log-only 非行为改动）
    # V5-R2 翻转披露（2026-09-24）：executor 0.6.1→0.7.0（rip-up 有界深化
    # 2/8/20→5/12/30+W-2 联合重排+W-3 波次/档位导引+W-4 victim 定向探针）
    # V5-EXECUTOR-ENG-R1 翻转披露（2026-10-02）：executor 0.8.0→0.9.0
    # （W-1 SC-1 构造性无解事前短路 sealed-short-circuit+W-2
    # verdict_provenance 出口读数面；详见 executor 模块 docstring 与
    # tests/test_executor_shortcircuit.py、tests/test_verdict_provenance.py）
    assert EXECUTOR_VERSION == "v5.executor/0.13.0"  # 0.13.0 同步（engine-fix-r1 阶段一：FX-1 梯内 memo＋FX-2 微优化，纯等价提速；0.11.0=EXEC-R8-B）  # EXEC-R8-B 同步（候选出口事件接线）
    assert ROUTES_SCHEMA_VERSION == "v5.routes.v1"
    # W-6 ED-2 修复翻新披露（2026-09-26）：route_check 0.4.0→0.4.1（③ 层
    # 连通审计补 PTH 孔筒全信号层 union；用户四裁 R-A）
    assert ROUTE_CHECK_VERSION == "v5.route_check/0.5.0"  # V5-R7 同步
