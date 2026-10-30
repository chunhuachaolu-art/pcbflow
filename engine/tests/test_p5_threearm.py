# -*- coding: utf-8 -*-
"""P5③ 三臂对照接线（P5-G4）+ L8 逐运行账本 + 终解 diff/复查旗标视图测试。

覆盖（任务书 §4 L5/L8、§5 P5-G4；纯引擎侧，零模型会话）：
- 三臂隔离性：arm1（no-principle）rules 留痕恒空、arm2（principle）正常、
  arm3 base=arm2 深拷贝隔离、注入位初始为空；
- inject_model_candidates 合同占位：形状错 fail-closed（逐键路径）、合法输入
  透传登记、事务式整批拒绝、登记深拷贝隔离、id 全局唯一；
- compute_g4 三数在合成板上的确定性预期值（principle_gain / model_increment /
  echo_rate 的操作化定义见 v5.threearm docstring）+ 重合率对称性；
- run_ledger 六问聚合对合成 trace 的精确断言 + 双跑字节等 + fail-closed；
- render_l8_diff_view 双跑字节等 + XML 良构 + 差异高亮/旗标角标 + fail-closed；
- review_flags advisory 不抛断（差异在案、形状违约才抛）；
- demo-02 三臂实跑冒烟（真实板在场才跑；执行器慢，模块级缓存只执行一次）。
板只读；零网络零 LLM API；不写 out/。
"""
import copy
import os
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import compute_board_sha256, load_board_file  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.planner import plan_candidates  # noqa: E402
from v5.selection import select_best  # noqa: E402
from v5.threearm import (  # noqa: E402
    DIFF_SCHEMA_VERSION,
    MODEL_ARM_TOKEN,
    ThreeArmError,
    arm3_candidates,
    compute_g4,
    diff_solutions,
    inject_model_candidates,
    review_flags,
    run_three_arms,
)
from v5.run_ledger import (  # noqa: E402
    RUN_LEDGER_SCHEMA,
    RunLedgerError,
    build_run_ledger,
    run_ledger_bytes,
)
from v5.view import render_l8_diff_view  # noqa: E402

DEMO02_PATH = os.path.join(ROOT, "boards", "d", "demo-02-mixed-types.board.v1.json")

HARD_RULES = {
    "R1": {"floor_mm": 0.3, "k_a": 0.4},
    "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
    "R3": {"unsplittable": True},
    "R4": {"max_distance_mm": 2.0, "return_via_required": True},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
}
STACKUP_2 = [
    {"id": "F.Cu", "kind": "signal", "preferred_direction": "h", "available": True},
    {"id": "B.Cu", "kind": "signal", "preferred_direction": "any", "available": True},
]


# ---------------------------------------------------------------- 夹具构造

def _hash_entry(entry):
    view = {k: v for k, v in entry.items() if k != "source_hash"}
    import hashlib
    return hashlib.sha256(canonical.canonical_json(view)).hexdigest()


def make_entry(pid, *, scope, target, priority, kind, params=None):
    entry = {
        "principle_id": pid,
        "name": "测试理念 %s" % pid,
        "intent": {"protects": "保护资源 X", "sacrifices": "牺牲普通网 Y 的短路径"},
        "scope": scope,
        "protected_resources": ["资源 X"],
        "target_freedom": target,
        "priority": priority,
        "hard_or_soft": "soft",
        "overridable": True,
        "compiled_rule": {"kind": kind, "params": dict(params or {})},
        "enforcement": "generation",
        "conflict_policy": {"conflicts_with": [], "yields_to": []},
        "evidence_refs": ["v5.threearm 测试夹具"],
        "version": "1.0.0",
    }
    entry["source_hash"] = _hash_entry(entry)
    return entry


def part(pid, ptype, e1, e2, policy="any"):
    return {"partition_id": pid, "ptype": ptype,
            "geometry": {"endpoints": [list(e1), list(e2)]},
            "layer_policy": policy,
            "width_prior": {"w_min": 0.1, "w_max": 0.3},
            "current_a": 0.0, "speed_class": "low_speed"}


def zone(zid, kind, x0, y0, x1, y1, layers="all", **extra):
    z = {"zone_id": zid, "kind": kind,
         "rect": {"x_min": x0, "y_min": y0, "x_max": x1, "y_max": y1},
         "layers": layers}
    z.update(extra)
    return z


def make_board(*, partitions, registry=(), stackup=None, zones=(),
               board_id="p5-threearm-inline"):
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": copy.deepcopy(stackup or STACKUP_2),
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 50.0, "y_max": 40.0},
        "zones": copy.deepcopy(list(zones)),
        "partitions": copy.deepcopy(list(partitions)),
        "nets": [{"net_id": "N-" + p["partition_id"], "net_class": "MISC",
                  "partitions": [p["partition_id"]]} for p in partitions],
        "hard_rules": copy.deepcopy(HARD_RULES),
        "principle_registry": copy.deepcopy(list(registry)),
        "provenance": {"source_type": "synthetic",
                       "source_uri": "inline://p5-threearm-test",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


def plan(board, arm="principle"):
    artifact, _fp = compile_board(board)
    return plan_candidates(board, artifact, arm=arm), artifact


def cand(cid, polylines, layers, arm="principle", trace=None):
    c = {"candidate_id": cid, "arm": arm,
         "provenance": {"generator": "test-fixture/0.1.0", "rules_consumed": [],
                        "compiled_sha256": "0" * 64},
         "route_order": sorted(polylines),
         "layer_assignment": dict(layers), "polylines": polylines}
    if trace is not None:
        c["generation_trace"] = trace
    return c


def model_cand(cid, board, artifact, polylines, layers, trace=None):
    """合法模型候选（合同决定 1：M-### id / model-shadow arm / v5.model_bridge 前缀）。"""
    return {"candidate_id": cid, "arm": MODEL_ARM_TOKEN,
            "provenance": {"generator": "v5.model_bridge/test/0.1.0",
                           "rules_consumed": [],
                           "compiled_sha256": canonical.canonical_sha256(artifact)},
            "route_order": sorted(polylines),
            "layer_assignment": dict(layers), "polylines": polylines,
            "generation_trace": list(trace or [])}


# ---------------------------------------------------------------- 合成板

# 板 A：双分区水平线，layer_plan 规则把 G1 偏好层 B.Cu 前置 → ②终选层指派异于①
def _board_gain(with_rule=True):
    parts = [part("G1", "CLK", (2, 2), (20, 2)),
             part("G2", "MISC", (2, 10), (20, 10))]
    registry = []
    if with_rule:
        registry.append(make_entry("P-PREF", scope="partition:G1",
                                   target="layer_plan", priority=40,
                                   kind="layer_preference", params={"layer": "B.Cu"}))
    return make_board(partitions=parts, registry=registry,
                      board_id="p5-gain-%s" % ("on" if with_rule else "off"))


# 板 B：单分区横穿禁布区 → 引擎臂全部直线候选被 R6 滤除（UNKNOWN）；
# 模型候选绕行 → 可行（SAT）。model_increment=True 的合成场景。
def _board_detour():
    parts = [part("G1", "CLK", (2, 20), (48, 20))]
    zones = [zone("K1", "keepout", 20, 15, 30, 25)]
    return make_board(partitions=parts, zones=zones,
                      board_id="p5-detour")


DETOUR_AROUND = [[2.0, 20.0], [14.0, 20.0], [14.0, 30.0],
                 [40.0, 30.0], [40.0, 20.0], [48.0, 20.0]]


# ---------------------------------------------------------------- 三臂隔离性

def test_three_arms_arm1_rules_empty_arm2_normal():
    """arm1 诊断臂：arm 恒 no-principle、trace/rules 双空；arm2 主路径正常留痕。"""
    board = _board_gain(with_rule=True)
    artifact, _ = compile_board(board)
    arms = run_three_arms(board, artifact)
    assert set(arms) == {"arm1", "arm2", "arm3"}
    for c in arms["arm1"]:
        assert c["arm"] == "no-principle"
        assert c["generation_trace"] == []
        assert c["provenance"]["rules_consumed"] == []
    assert arms["arm2"]
    for c in arms["arm2"]:
        assert c["arm"] == "principle"
    traced = {t["rule"] for t in arms["arm2"][0]["generation_trace"]}
    assert traced == {r["principle_id"] for r in artifact["rules"]} == {"P-PREF"}
    assert arms["arm2"][0]["provenance"]["rules_consumed"] == ["P-PREF"]


def test_arm3_base_is_deepcopy_of_arm2_and_slot_empty():
    """arm3 base_candidates = arm2 深拷贝（双向隔离）；注入位初始空。"""
    board = _board_gain(with_rule=True)
    artifact, _ = compile_board(board)
    arms = run_three_arms(board, artifact)
    assert arms["arm3"]["arm"] == "arm3"
    assert arms["arm3"]["base_candidates"] == arms["arm2"]
    assert arms["arm3"]["model_candidates"] == []
    arms["arm2"].pop()                      # arm2 侧变动不渗入 arm3
    assert len(arms["arm3"]["base_candidates"]) == len(arms["arm2"]) + 1
    arms["arm3"]["base_candidates"][0]["candidate_id"] = "C-XXX"
    assert arms["arm2"][0]["candidate_id"] != "C-XXX"


def test_three_arms_double_run_byte_equal():
    """确定性：run_three_arms 双跑 canonical 字节相等（注入位空槽同构）。"""
    board = _board_gain(with_rule=True)
    artifact, _ = compile_board(board)
    a = run_three_arms(board, artifact)
    b = run_three_arms(board, artifact)
    assert canonical.canonical_json(a) == canonical.canonical_json(b)


# ---------------------------------------------------------------- 注入合同占位

def _detour_arms():
    board = _board_detour()
    artifact, _ = compile_board(board)
    arms = run_three_arms(board, artifact)
    return board, artifact, arms


def test_inject_model_candidates_passthrough_registration():
    """合法模型候选透传登记：进注入位、arm3_candidates=base+model、输入深拷贝隔离。"""
    board, artifact, arms = _detour_arms()
    mc = model_cand("M-001", board, artifact,
                    {"G1": DETOUR_AROUND}, {"G1": "B.Cu"},
                    trace=[{"rule": "P-MOCK", "freedom": "corridor",
                            "effect": "模型绕行禁布区提案"}])
    mc_snapshot = copy.deepcopy(mc)
    out = inject_model_candidates(arms["arm3"], [mc])
    assert out is arms["arm3"]                      # 原地登记
    assert len(arms["arm3"]["model_candidates"]) == 1
    registered = arms["arm3"]["model_candidates"][0]
    assert registered == mc_snapshot
    mc["candidate_id"] = "M-999"                    # 注入后改输入不渗入登记件
    assert arms["arm3"]["model_candidates"][0]["candidate_id"] == "M-001"
    merged = arm3_candidates(arms["arm3"])
    assert [c["candidate_id"] for c in merged] == \
        ["C-001", "C-002", "M-001"]                 # base 在前、model 在后
    assert arms["arm3"]["model_candidates"][0]["arm"] == MODEL_ARM_TOKEN


def test_inject_empty_batch_is_noop():
    """空批次=合法 no-op（无模型候选的基线对照形态）。"""
    _, _, arms = _detour_arms()
    inject_model_candidates(arms["arm3"], [])
    assert arms["arm3"]["model_candidates"] == []


@pytest.mark.parametrize("mutate,path_frag", [
    # 形状违约逐类：id / arm / generator 前缀 / route_order 覆盖 / 层合法性 /
    # 折线形状 / 留痕形状
    (lambda mc: mc.update(candidate_id="C-001"), "candidate_id"),
    (lambda mc: mc.update(arm="principle"), "arm"),
    (lambda mc: mc["provenance"].update(generator="gpt/0.1"), "generator"),
    (lambda mc: mc.update(route_order=["G1", "GHOST"]), "route_order"),
    (lambda mc: mc["layer_assignment"].update(G1="X.Cu"), "layer_assignment"),
    (lambda mc: mc["polylines"].update(G1=[[0.0, 0.0]]), "polylines"),
    (lambda mc: mc["generation_trace"].append({"rule": "X", "freedom": "bad",
                                               "effect": "e"}), "freedom"),
])
def test_inject_model_candidates_fail_closed(mutate, path_frag):
    """合同占位 fail-closed：形状错逐键路径抛错（含 M-### 令牌/arm/generator 前缀）。"""
    board, artifact, arms = _detour_arms()
    mc = model_cand("M-001", board, artifact,
                    {"G1": DETOUR_AROUND}, {"G1": "B.Cu"})
    mutate(mc)
    with pytest.raises(ThreeArmError) as ei:
        inject_model_candidates(arms["arm3"], [mc])
    assert path_frag in str(ei.value)


def test_inject_rejects_duplicate_id_and_non_list():
    """id 在 arm3 内全局唯一（base+model）；非 list 输入 fail-closed。"""
    board, artifact, arms = _detour_arms()
    good = model_cand("M-001", board, artifact,
                      {"G1": DETOUR_AROUND}, {"G1": "B.Cu"})
    inject_model_candidates(arms["arm3"], [good])
    dup = model_cand("M-001", board, artifact,
                     {"G1": [[2.0, 20.0], [48.0, 20.0]]}, {"G1": "F.Cu"})
    with pytest.raises(ThreeArmError) as ei:
        inject_model_candidates(arms["arm3"], [dup])
    assert "重复" in str(ei.value)
    with pytest.raises(ThreeArmError):
        inject_model_candidates(arms["arm3"], {"M-001": dup})
    with pytest.raises(ThreeArmError):
        inject_model_candidates({"arm": "nope"}, [])


def test_inject_transactional_whole_batch_rejected():
    """事务式（决定 2）：整批 [好, 坏] 任一违约 → 整批拒绝、注入位保持原状。"""
    board, artifact, arms = _detour_arms()
    good = model_cand("M-001", board, artifact,
                      {"G1": DETOUR_AROUND}, {"G1": "B.Cu"})
    bad = model_cand("M-002", board, artifact,
                     {"G1": DETOUR_AROUND}, {"G1": "B.Cu"})
    bad["arm"] = "principle"                        # 坏件
    with pytest.raises(ThreeArmError):
        inject_model_candidates(arms["arm3"], [good, bad])
    assert arms["arm3"]["model_candidates"] == []   # 不半登记


# ---------------------------------------------------------------- G4 三数

def test_g4_principle_gain_on_synthetic_board():
    """板 A（有理念）：②层指派异于① → principle_gain=True；model_increment=False、
    echo_rate=1.0（未注入基线锚）。"""
    board = _board_gain(with_rule=True)
    artifact, _ = compile_board(board)
    arms = run_three_arms(board, artifact)
    sel1 = select_best(board, arms["arm1"])
    sel2 = select_best(board, arms["arm2"])
    sel3 = select_best(board, arm3_candidates(arms["arm3"]))
    assert sel1["verdict"] == sel2["verdict"] == "SAT"
    assert sel1["best"]["candidate_id"] == sel2["best"]["candidate_id"] == "C-001"
    assert sel2["best"]["layer_assignment"]["G1"] == "B.Cu"   # 理念偏好生效
    assert sel1["best"]["layer_assignment"]["G1"] == "F.Cu"   # 诊断臂无理念
    g4 = compute_g4(sel1, sel2, sel3)
    assert g4 == {"principle_gain": True, "model_increment": False, "echo_rate": 1.0}


def test_g4_principle_gain_off_control():
    """板 A 对照（无理念）：①②终选本体一致 → principle_gain=False（指纹机制
    不被 arm 令牌/留痕等按构造差异平庸化）。"""
    board = _board_gain(with_rule=False)
    artifact, _ = compile_board(board)
    arms = run_three_arms(board, artifact)
    sel1 = select_best(board, arms["arm1"])
    sel2 = select_best(board, arms["arm2"])
    sel3 = select_best(board, arm3_candidates(arms["arm3"]))
    g4 = compute_g4(sel1, sel2, sel3)
    assert g4 == {"principle_gain": False, "model_increment": False, "echo_rate": 1.0}


def test_g4_model_increment_and_echo_rate_on_detour_board():
    """板 B：②全滤除（UNKNOWN）而③模型绕行可行（SAT）→ model_increment=True；
    echo_rate = 2/3（{C-001,C-002} vs {C-001,C-002,M-001} 的 Jaccard）；①②同
    UNKNOWN → principle_gain=False。"""
    board, artifact, arms = _detour_arms()
    sel1 = select_best(board, arms["arm1"])
    sel2 = select_best(board, arms["arm2"])
    assert sel1["verdict"] == sel2["verdict"] == "UNKNOWN" and sel2["best"] is None
    inject_model_candidates(arms["arm3"], [
        model_cand("M-001", board, artifact,
                   {"G1": DETOUR_AROUND}, {"G1": "B.Cu"})])
    sel3 = select_best(board, arm3_candidates(arms["arm3"]))
    assert sel3["verdict"] == "SAT" and sel3["best"]["candidate_id"] == "M-001"
    g4 = compute_g4(sel1, sel2, sel3)
    assert g4["principle_gain"] is False
    assert g4["model_increment"] is True
    assert g4["echo_rate"] == round(2 / 3, 10)


def test_g4_echo_rate_symmetry():
    """重合率对称性：Jaccard 对定义域对称，②③互换数值不变（②③非对称指标只有
    model_increment，其互换后取值不断言）。"""
    board, artifact, arms = _detour_arms()
    sel1 = select_best(board, arms["arm1"])
    sel2 = select_best(board, arms["arm2"])
    inject_model_candidates(arms["arm3"], [
        model_cand("M-001", board, artifact,
                   {"G1": DETOUR_AROUND}, {"G1": "B.Cu"})])
    sel3 = select_best(board, arm3_candidates(arms["arm3"]))
    g4 = compute_g4(sel1, sel2, sel3)
    g4_swapped = compute_g4(sel1, sel3, sel2)
    assert g4["echo_rate"] == g4_swapped["echo_rate"] == round(2 / 3, 10)


def test_g4_fail_closed_on_malformed_selection():
    """非 select_best 形状输入 fail-closed（verdict/best/per_candidate 逐键）。"""
    board, artifact, arms = _detour_arms()
    sel = select_best(board, arms["arm2"])
    with pytest.raises(ThreeArmError):
        compute_g4({"verdict": 3}, sel, sel)
    with pytest.raises(ThreeArmError):
        compute_g4(sel, {"verdict": "SAT"}, sel)
    bad_pc = dict(sel)
    bad_pc["per_candidate"] = [{"no_id": 1}]
    with pytest.raises(ThreeArmError):
        compute_g4(sel, bad_pc, sel)
    bad_best = dict(sel)
    bad_best["best"] = {"candidate_id": "C-001"}      # 缺路由本体键
    with pytest.raises(ThreeArmError):
        compute_g4(sel, sel, bad_best)


# ---------------------------------------------------------------- 终解 diff 与复查旗标

def _routes_doc(board, entries):
    sha = board["provenance"]["board_sha256"]
    return {"schema_version": "v5.routes.v1", "board_id": board["board_id"],
            "board_sha256": sha, "routes": entries, "negotiation_log": [],
            "provenance": {"generator": "test-fixture/0.1.0", "board_sha256": sha}}


def _diff_board():
    return make_board(partitions=[part("G1", "CLK", (2, 2), (20, 2)),
                                  part("G2", "MISC", (2, 10), (20, 10))],
                      board_id="p5-diff")


def _sol_a():
    board = _diff_board()
    doc = _routes_doc(board, [
        {"partition_id": "G1", "net_id": "N-G1", "layer": "F.Cu",
         "polyline": [[2, 2], [20, 2]], "width": 0.2,
         "transition_vias": [], "return_vias": []},
        {"partition_id": "G2", "net_id": "N-G2", "layer": "F.Cu",
         "polyline": [[2, 10], [20, 10]], "width": 0.2,
         "transition_vias": [], "return_vias": []}])
    return board, doc


def _sol_b(layer=True, path=False, width=True):
    board = _diff_board()
    g1 = {"partition_id": "G1", "net_id": "N-G1",
          "layer": "B.Cu" if layer else "F.Cu",
          "polyline": [[2, 2], [20, 2]], "width": 0.4 if width else 0.2,
          "transition_vias": [], "return_vias": []}
    g2_poly = ([[2, 10], [10, 10], [10, 14], [20, 14], [20, 10]] if path
               else [[2, 10], [20, 10]])
    g2 = {"partition_id": "G2", "net_id": "N-G2", "layer": "F.Cu",
          "polyline": g2_poly, "width": 0.2,
          "transition_vias": [], "return_vias": []}
    return board, _routes_doc(board, [g1, g2])


def test_diff_solutions_structured_fields():
    """v5.soldiff.v1：逐键 layer/path/width 结构化差异、键字典序、零差异 identical。"""
    board, a = _sol_a()
    _, b = _sol_b(path=True)
    d = diff_solutions(board, a, b)
    assert d["schema_version"] == DIFF_SCHEMA_VERSION == "v5.soldiff.v1"
    assert d["identical"] is False
    assert [(x["partition_id"], x["net_id"], x["fields"]) for x in d["differences"]] == \
        [("G1", "N-G1", ["layer", "width"]), ("G2", "N-G2", ["path"])]
    same = diff_solutions(board, a, _routes_doc(board, copy.deepcopy(a["routes"])))
    assert same["identical"] is True and same["differences"] == []
    assert canonical.canonical_json(diff_solutions(board, a, b)) == \
        canonical.canonical_json(diff_solutions(board, a, b))   # 双跑字节等


def test_diff_solutions_fail_closed_on_mismatch():
    """错板错件配对 / 形状违约 fail-closed（validate_routes 键路径）。"""
    board, a = _sol_a()
    other = make_board(partitions=[part("G1", "CLK", (2, 2), (20, 2))],
                       board_id="p5-diff-other")
    bad = _routes_doc(other, a["routes"])
    with pytest.raises(ValueError):
        diff_solutions(board, a, bad)
    broken = copy.deepcopy(a)
    broken["schema_version"] = "v5.routes.v0"
    with pytest.raises(ValueError):
        diff_solutions(board, a, broken)


def test_review_flags_advisory_never_raises_on_differences():
    """席位 C 旗标：差异在案绝不抛错；每差异一旗、RF-### 连续、severity 恒
    advisory（不阻塞）、note 带键与字段。"""
    board, a = _sol_a()
    _, b = _sol_b(path=True)
    d = diff_solutions(board, a, b)
    flags = review_flags(d)
    assert [f["flag_id"] for f in flags] == ["RF-001", "RF-002"]
    for f in flags:
        assert f["severity"] == "advisory"
        assert f["partition_id"] and f["net_id"] and f["fields"] and f["note"]
    assert flags[0]["partition_id"] == "G1" and flags[0]["fields"] == ["layer", "width"]
    assert review_flags(diff_solutions(board, a, _routes_doc(board, a["routes"]))) == []


def test_review_flags_fail_closed_on_malformed_diff():
    """diff 形状违约才 fail-closed（非 dict / schema 版本错 / 缺差异表 / 差异条目
    缺键）；差异在案本身绝不抛错（见 advisory 测试）。"""
    with pytest.raises(ValueError):
        review_flags([])
    with pytest.raises(ValueError):
        review_flags({"schema_version": DIFF_SCHEMA_VERSION})   # 缺 differences
    with pytest.raises(ValueError):
        review_flags({"schema_version": "v1", "differences": []})
    with pytest.raises(ValueError):
        review_flags({"schema_version": DIFF_SCHEMA_VERSION,
                      "differences": [{"net_id": "N", "fields": ["path"]}]})


# ---------------------------------------------------------------- L8 diff 视图

def test_render_l8_diff_view_wellformed_and_deterministic():
    """双跑字节等 + XML 良构 + 差异/旗标要素在场。"""
    board, a = _sol_a()
    _, b = _sol_b(path=True)
    flags = review_flags(diff_solutions(board, a, b))
    svg1 = render_l8_diff_view(board, a, b, flags)
    svg2 = render_l8_diff_view(board, a, b, flags)
    assert svg1 == svg2
    root = ET.fromstring(svg1)
    assert root.attrib["id"] == "v5-l8-diff-view"
    assert root.attrib["data-diff-count"] == "2"
    assert root.attrib["data-flag-count"] == "2"
    ns = "{http://www.w3.org/2000/svg}"
    panels = [g for g in root.iter(ns + "g") if g.get("class") == "v5-l8-panel"]
    assert [g.get("data-panel") for g in panels] == ["A", "B"]
    diffs = [g for g in root.iter(ns + "g") if g.get("class") == "v5-l8-diff"]
    assert len(diffs) == 4                              # 2 差异键 × 双面板
    fields = sorted(g.get("data-diff-fields") for g in diffs)
    assert fields == ["layer,width", "layer,width", "path", "path"]
    assert svg1.count('data-flag-id="RF-001"') == 1
    assert "席位 C 复查旗标" in svg1
    assert "两终解结构一致" not in svg1


def test_render_l8_diff_view_identical_and_no_flags():
    """零差异 + 空 flags：一致性徽标在场、旗标盒单行「无」、data 双零。"""
    board, a = _sol_a()
    svg = render_l8_diff_view(board, a, _routes_doc(board, copy.deepcopy(a["routes"])))
    root = ET.fromstring(svg)
    assert root.attrib["data-diff-count"] == "0"
    assert root.attrib["data-flag-count"] == "0"
    assert "两终解结构一致（无差异点）" in svg
    assert ">无</text>" in svg


def test_render_l8_diff_view_fail_closed():
    """旗标形状/错板错件 fail-closed。"""
    board, a = _sol_a()
    _, b = _sol_b()
    with pytest.raises(ValueError):
        render_l8_diff_view(board, a, b, flags=[{"note": "缺 flag_id"}])
    with pytest.raises(ValueError):
        render_l8_diff_view(board, a, b, flags="RF-001")
    other = make_board(partitions=[part("G1", "CLK", (2, 2), (20, 2))],
                       board_id="p5-diff-other")
    with pytest.raises(ValueError):
        render_l8_diff_view(board, a, _routes_doc(other, a["routes"]))


def test_view_diff_semantics_locked_with_threearm():
    """视图与 threearm.diff_solutions 差异语义同锁：fields 逐键一致（追加节
    内联实现的漂移钉住）。"""
    board, a = _sol_a()
    _, b = _sol_b(path=True, width=False)
    d = diff_solutions(board, a, b)
    svg = render_l8_diff_view(board, a, b,
                              review_flags(d))
    for item in d["differences"]:
        assert ('data-partition-id="%s" data-net-id="%s" data-diff-fields="%s"'
                % (item["partition_id"], item["net_id"],
                   ",".join(item["fields"]))) in svg
    assert root_diff_count(svg) == len(d["differences"])


def root_diff_count(svg):
    root = ET.fromstring(svg)
    return int(root.attrib["data-diff-count"])


# ---------------------------------------------------------------- L8 逐运行账本

# 账本板：G1 水平线（避开禁布区）、G2 竖穿禁布区（直线候选被 R6 滤除）
def _ledger_board(registry):
    return make_board(
        partitions=[part("G1", "MISC", (2, 32), (48, 32)),
                    part("G2", "MISC", (25, 2), (25, 38))],
        zones=[zone("K1", "keepout", 20, 15, 30, 25)],
        registry=registry, board_id="p5-runledger")


def _ledger_candidates():
    return [
        cand("C-101", {"G1": [[2.0, 32.0], [48.0, 32.0]]}, {"G1": "F.Cu"},
             trace=[{"principle_id": "PR-OK", "priority": 30}]),        # 可行 → 生效
        cand("C-102", {"G2": [[25.0, 2.0], [25.0, 38.0]]}, {"G2": "F.Cu"},
             trace=[{"principle_id": "PR-HI", "priority": 20},
                    {"principle_id": "PR-LO", "priority": 10}]),        # R6 滤除 → 致淘汰+冲突裁决
        cand("C-103", {"P99": [[0.0, 0.0], [1.0, 1.0]]}, {},
             trace=[{"principle_id": "PR-BAD", "priority": 5}]),        # 度量非法 → 依据不足
        cand("C-104", {"G1": [[2.0, 32.0], [48.0, 32.0]]}, {"G1": "B.Cu"}),  # 空留痕 principle → 触发被忽略
    ]


def _fake_executor_result():
    return {
        "verdict": "ROUTED",
        "routes": {"schema_version": "v5.routes.v1"},
        "per_net": [
            {"partition_id": "G1", "net_id": "N-G1", "status": "routed",
             "attempts": 1, "negotiated": False},
            {"partition_id": "G2", "net_id": "N-G2", "status": "routed",
             "attempts": 2, "negotiated": True},
        ],
        "negotiation_log": [
            "net=N-G1 partition=G1 committed attempt=1 variant=prefer+r2-near",
            "net=N-G2 partition=G2 committed attempt=2 "
            "variant=no-prefer+r2-overlap_free+via-free（协商兜底生效）",
        ],
    }


def test_run_ledger_six_questions_exact_aggregation():
    """六问聚合精确断言：五态归位（无可观测影响本跑为空桶）、条目=原则+依据、
    trace 摘要按规则聚合、provenance 输入计数。"""
    board = _ledger_board([{"principle_id": "PR-OK"}, {"principle_id": "PR-HI"},
                           {"principle_id": "PR-LO"}, {"principle_id": "PR-BAD"},
                           {"principle_id": "PR-IGNORED"}])
    cands = _ledger_candidates()
    sel = select_best(board, cands)
    assert sel["verdict"] == "SAT"
    ledger = build_run_ledger(board, cands, sel, _fake_executor_result())

    assert ledger["schema_version"] == RUN_LEDGER_SCHEMA == "v5.runledger.v1"
    assert ledger["board_id"] == board["board_id"]
    assert ledger["board_sha256"] == board["provenance"]["board_sha256"]
    six = ledger["six_questions"]
    assert set(six) == {"生效", "被忽略", "冲突裁决", "致淘汰",
                        "无可观测影响", "依据不足"}
    assert six["生效"]["count"] == 1
    assert six["生效"]["principles"] == ["PR-OK"]
    assert six["致淘汰"]["principles"] == ["PR-HI"]
    assert six["冲突裁决"]["principles"] == ["PR-LO"]
    assert six["依据不足"]["principles"] == ["PR-BAD"]
    assert six["被忽略"]["principles"] == ["PR-IGNORED"]
    assert six["无可观测影响"] == {"count": 0, "principles": [], "entries": []}
    for status, bucket in six.items():
        for entry in bucket["entries"]:
            assert set(entry) == {"principle_id", "evidence"}
            assert entry["evidence"]
    assert "C-102" in six["致淘汰"]["entries"][0]["evidence"]

    # generation_trace 聚合：规则 → freedfs/candidates（sorted、含无 freedom 形态）
    summary = {row["rule"]: row for row in ledger["generation_trace_summary"]}
    assert set(summary) == {"PR-OK", "PR-HI", "PR-LO", "PR-BAD"}
    assert summary["PR-OK"]["candidate_ids"] == ["C-101"]
    assert summary["PR-OK"]["freedoms"] == []          # principle_id 夹具形态无 freedom
    assert summary["PR-HI"]["candidate_ids"] == ["C-102"]
    assert summary["PR-BAD"]["candidate_ids"] == ["C-103"]

    # negotiation 聚合：真实合同形状的协商账本全量入册
    assert ledger["negotiation"]["run"] is True
    assert ledger["negotiation"]["verdict"] == "ROUTED"
    assert ledger["negotiation"]["nets_total"] == 2
    assert ledger["negotiation"]["nets_negotiated"] == 1
    assert ledger["negotiation"]["nets_failed"] == 0
    assert ledger["negotiation"]["negotiation_log"] == _fake_executor_result()["negotiation_log"]

    assert ledger["provenance"]["generator"] == "v5.run_ledger/0.1.0"
    assert ledger["provenance"]["inputs"] == {
        "planner_candidates": 4, "selection_verdict": "SAT",
        "executor": "ROUTED", "ledger_entries": 5}


def test_run_ledger_no_observable_and_not_run_shapes():
    """无可观测影响态（可行批+注册表无痕理念+无空留痕 principle 臂）；
    executor_result=None → negotiation.run=False。"""
    board = _ledger_board([{"principle_id": "PR-OK"}, {"principle_id": "PR-IDLE"}])
    cands = [cand("C-201", {"G1": [[2.0, 32.0], [48.0, 32.0]]}, {"G1": "F.Cu"},
                  trace=[{"principle_id": "PR-OK", "priority": 30}]),
             cand("C-202", {"G1": [[2.0, 32.0], [48.0, 32.0]]}, {"G1": "B.Cu"},
                  arm="no-principle")]                  # no-principle 空留痕不触发被忽略
    sel = select_best(board, cands)
    ledger = build_run_ledger(board, cands, sel)
    six = ledger["six_questions"]
    assert six["生效"]["principles"] == ["PR-OK"]
    assert six["无可观测影响"]["principles"] == ["PR-IDLE"]
    assert six["被忽略"]["count"] == 0
    assert ledger["negotiation"] == {"run": False}
    assert ledger["provenance"]["inputs"]["executor"] == "not_run"


def test_run_ledger_double_run_byte_equal():
    """canonical 序列化稳定：同输入双跑字节相等。"""
    board = _ledger_board([{"principle_id": "PR-OK"}, {"principle_id": "PR-HI"},
                           {"principle_id": "PR-LO"}, {"principle_id": "PR-BAD"},
                           {"principle_id": "PR-IGNORED"}])
    cands = _ledger_candidates()
    sel = select_best(board, cands)
    b1 = run_ledger_bytes(build_run_ledger(board, cands, sel, _fake_executor_result()))
    b2 = run_ledger_bytes(build_run_ledger(board, cands, sel, _fake_executor_result()))
    assert b1 == b2
    assert run_ledger_bytes(build_run_ledger(board, cands, sel)) == \
        run_ledger_bytes(build_run_ledger(board, cands, sel))


def test_run_ledger_fail_closed():
    """上游合同违约 fail-closed：六态外 status / 缺 evidence / 候选非 list /
    字节化入口 schema 错。"""
    board = _ledger_board([])
    ok_sel = {"verdict": "SAT", "ledger": {"principle_ledger": []}}
    with pytest.raises(RunLedgerError):
        build_run_ledger(board, [], {"verdict": "SAT", "ledger": {
            "principle_ledger": [{"principle_id": "X", "status": "外星状态",
                                  "evidence": "e"}]}})
    with pytest.raises(RunLedgerError):
        build_run_ledger(board, [], {"verdict": "SAT", "ledger": {
            "principle_ledger": [{"principle_id": "X", "status": "生效"}]}})
    with pytest.raises(RunLedgerError):
        build_run_ledger(board, "not-a-list", ok_sel)
    with pytest.raises(RunLedgerError):
        build_run_ledger(board, [], {"verdict": "", "ledger": {"principle_ledger": []}})
    with pytest.raises(RunLedgerError):
        run_ledger_bytes({"schema_version": "v0"})
    with pytest.raises(RunLedgerError):
        build_run_ledger(board, [], ok_sel, {"verdict": ""})


# ---------------------------------------------------------------- demo-02 实跑冒烟

_SMOKE = {}


def _demo02_smoke():
    """demo-02 三臂实跑（模块级缓存只跑一次；执行器 ~20s 为最贵步）。"""
    if "all" not in _SMOKE:
        board = load_board_file(DEMO02_PATH)
        artifact, _fp = compile_board(board)
        arms = run_three_arms(board, artifact)
        sels = {
            "arm1": select_best(board, arms["arm1"]),
            "arm2": select_best(board, arms["arm2"]),
            "arm3": select_best(board, arm3_candidates(arms["arm3"])),
        }
        # 执行器实跑一次（主路径首候选）→ 真实协商账本进逐运行账本
        executed = None
        if arms["arm2"]:
            from v5.executor import execute_candidate
            executed = execute_candidate(board, arms["arm2"][0])
        run_ledger = build_run_ledger(board, arms["arm2"], sels["arm2"], executed)
        _SMOKE["all"] = (board, artifact, arms, sels, executed, run_ledger)
    return _SMOKE["all"]


@pytest.mark.skipif(not os.path.exists(DEMO02_PATH), reason="demo-02 不在场")
def test_demo02_three_arm_real_run_smoke():
    """demo-02 三臂实跑冒烟：臂合同在真实板上成立、G4 三数可算且双跑一致、
    执行器产物进逐运行账本。"""
    board, artifact, arms, sels, executed, run_ledger = _demo02_smoke()
    # 臂合同
    assert arms["arm1"] and arms["arm2"]
    for c in arms["arm1"]:
        assert c["arm"] == "no-principle" and c["generation_trace"] == []
        assert c["provenance"]["rules_consumed"] == []
    assert {t["rule"] for t in arms["arm2"][0]["generation_trace"]} == \
        {r["principle_id"] for r in artifact["rules"]}
    assert sels["arm1"]["verdict"] in ("SAT", "UNSAT", "UNKNOWN")
    assert sels["arm2"]["verdict"] == sels["arm3"]["verdict"]     # 未注入：③≡②
    # G4 三数（未注入基线：gain 可真可假如实给数，increment 恒 False、echo 恒 1.0）
    g4 = compute_g4(sels["arm1"], sels["arm2"], sels["arm3"])
    assert g4["model_increment"] is False and g4["echo_rate"] == 1.0
    assert isinstance(g4["principle_gain"], bool)
    # 逐运行账本：真实执行器协商留痕聚合在案
    assert run_ledger["schema_version"] == "v5.runledger.v1"
    assert executed is not None
    assert run_ledger["negotiation"]["run"] is True
    assert run_ledger["negotiation"]["verdict"] == executed["verdict"]
    assert run_ledger["negotiation"]["nets_total"] == len(executed["per_net"])
    assert run_ledger["generation_trace_summary"], "principle 臂留痕必须进账本"
    # 三臂双跑字节等（规划器纯函数；注入位空槽）
    artifact2, _fp = compile_board(board)
    arms2 = run_three_arms(board, artifact2)
    assert canonical.canonical_json(arms2["arm1"]) == canonical.canonical_json(arms["arm1"])
    assert canonical.canonical_json(arms2["arm2"]) == canonical.canonical_json(arms["arm2"])
