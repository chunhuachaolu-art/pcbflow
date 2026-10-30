# -*- coding: utf-8 -*-
"""L0.5 理念编译器测试（V5.0-DEV-TASKBOOK §3.8 编译协议 + compiled_rules.v1 round-trip）。

夹具内联构造：bare 条目形状照 schemas/principle_registry.v1.schema.json#/definitions/principle，
source_hash 按 sha256(canonical(剔除该字段后的条目)) 现算（make_entry/hash_entry）。
"""
import copy
import hashlib
import json
import os

import pytest

from fixtures_v2 import build_v2_board
from v5 import canonical, schema_loader
from v5.board import compute_board_sha256, load_board_file
from v5.compiler import (
    PAIR_TEMPLATES,
    CompilerError,
    build_conflict_graph,
    build_full_conflict_graph,
    compile_board,
    compile_rules,
    coverage_report,
    detect_principle_pairs,
    resolve_scope,
    semantic_checks,
)

COMPILED = schema_loader.load_schema("compiled_rules.v1.schema.json")
REG = schema_loader.default_registry()  # glob 自动收编 compiled_rules.v1.schema.json


# ---------------------------------------------------------------- 夹具构造

def hash_entry(entry):
    """source_hash = sha256(canonical(剔除 source_hash 后的条目))。"""
    view = {k: v for k, v in entry.items() if k != "source_hash"}
    return hashlib.sha256(canonical.canonical_json(view)).hexdigest()


def make_entry(pid="P-TEST", *, scope="partitioning", target="ordering", priority=10,
               hard=False, overridable=None, compiled_rule=None, enforcement="generation",
               conflicts_with=None, yields_to=None, evidence=None, version="1.0.0"):
    """构造一条 schema 合法的 15 字段 principle 条目（source_hash 现算）。"""
    if compiled_rule is None:
        compiled_rule = {"kind": "order_by_priority"}
    if overridable is None:
        overridable = not hard
    entry = {
        "principle_id": pid,
        "name": "测试理念 %s" % pid,
        "intent": {"protects": "保护资源 X", "sacrifices": "牺牲普通网 Y 的短路径"},
        "scope": scope,
        "protected_resources": ["资源 X"],
        "target_freedom": target,
        "priority": priority,
        "hard_or_soft": "hard" if hard else "soft",
        "overridable": overridable,
        "compiled_rule": compiled_rule,
        "enforcement": enforcement,
        "conflict_policy": {"conflicts_with": list(conflicts_with or []),
                            "yields_to": list(yields_to or [])},
        "evidence_refs": list(evidence) if evidence is not None else ["V2 run-03 观察"],
        "version": version,
    }
    entry["source_hash"] = hash_entry(entry)
    return entry


def make_board(v2_board, entries):
    """在 v2 板上替换注册表并复算 board_sha256（load_board 哈希链要求）。"""
    board = copy.deepcopy(v2_board)
    board["principle_registry"] = copy.deepcopy(entries)
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


# ---------------------------------------------------------------- 全管线绿路

def test_full_pipeline_green_with_check_only(v2_board):
    """覆盖率 100% 绿（含 1 条 check_only）；工件过新 schema；冲突图 yields_to 覆盖 priority。"""
    entries = [
        make_entry("P-WIDE", scope="ptype:PWR", target="allocation", priority=40,
                   compiled_rule={"kind": "min_width_floor", "floor_mm": 0.8}),
        make_entry("P-CLK", scope="ptype:CLK", target="ordering", priority=30,
                   conflicts_with=["P-COST"]),
        make_entry("P-COST", scope="net_class:MISC", target="corridor", priority=10,
                   yields_to=["P-CLK"]),
        make_entry("P-AUDIT", target="layer_plan", compiled_rule="check_only",
                   enforcement="check"),
    ]
    board = make_board(v2_board, entries)
    artifact, fp = compile_board(board)
    assert artifact["artifact"] == "v5.compiled_rules.v1"
    assert artifact["board_id"] == "v2-scenario-golden"
    assert artifact["board_sha256"] == board["provenance"]["board_sha256"]
    cov = artifact["coverage"]
    assert cov == {"total": 4, "compiled": 3, "check_only": 1,
                   "coverage_pct": 100.0, "evidence_insufficient": []}
    assert [r["principle_id"] for r in artifact["rules"]] == ["P-WIDE", "P-CLK", "P-COST"]
    assert artifact["check_only"] == [{"principle_id": "P-AUDIT", "reason": "explicit check_only"}]
    g = artifact["conflict_graph"]
    assert g["nodes"] == ["P-AUDIT", "P-CLK", "P-COST", "P-WIDE"]
    assert len(g["edges"]) == 1
    assert g["edges"][0]["winner"] == "P-CLK"
    assert g["edges"][0]["resolution"] == "yields_to"
    schema_loader.validate_file(artifact, "compiled_rules.v1.schema.json")
    assert isinstance(fp, bytes)


def test_rule_entry_shape_and_predicate_merge():
    """规则条目形状：id=pid#version、generator_target 透传、predicate 合并（kind 改名 rule_kind）。"""
    entry = make_entry("P-LAYER", target="layer_plan", priority=25, version="2.0.0",
                       compiled_rule={"kind": "prefer_layer", "layer": "F.Cu",
                                      "proof_obligations": ["ob-1"]},
                       enforcement="both", conflicts_with=["P-X"], yields_to=["P-Y"])
    rules, check_only = compile_rules([entry])
    assert check_only == []
    rule = rules[0]
    assert rule["compiled_rule_id"] == "P-LAYER#2.0.0"
    assert rule["principle_id"] == "P-LAYER"
    assert rule["generator_target"] == "layer_plan"
    # 其余键全部并入 predicate（proof_obligations 同时上提为顶层字段）
    assert rule["predicate"] == {"rule_kind": "prefer_layer", "layer": "F.Cu",
                                 "proof_obligations": ["ob-1"]}
    assert rule["action"] == {"strategy": "prefer_layer", "priority": 25}
    assert rule["priority"] == 25
    assert rule["conflicts_with"] == ["P-X"]
    assert "P-Y" in rule["fallback"] and "yields_to" not in rule["fallback"]
    assert rule["proof_obligations"] == ["ob-1"]
    assert rule["enforcement"] == "both"
    schema_loader.validate({"rules": [rule], "check_only": [],
                            "conflict_graph": {"nodes": ["P-LAYER"], "edges": []},
                            "coverage": {"total": 1, "compiled": 1, "check_only": 0,
                                         "coverage_pct": 100.0, "evidence_insufficient": []},
                            "artifact": "v5.compiled_rules.v1", "board_id": "b",
                            "board_sha256": "0" * 64},
                           COMPILED, REG, "")


def test_check_only_disclosure_entry():
    rules, check_only = compile_rules([make_entry("P-CHK", compiled_rule="check_only")])
    assert rules == []
    assert check_only == [{"principle_id": "P-CHK", "reason": "explicit check_only"}]


# ---------------------------------------------------------------- 第 4 问 fail-closed

def test_compiled_rule_object_without_kind_fails_closed():
    with pytest.raises(CompilerError) as ei:
        compile_rules([make_entry("P-BAD", compiled_rule={"predicate": {"ptype": "HS"}})])
    assert "compiled_rule" in str(ei.value)
    assert "kind" in str(ei.value)


def test_compiled_rule_non_check_only_string_fails_closed():
    with pytest.raises(CompilerError) as ei:
        compile_rules([make_entry("P-BAD", compiled_rule="prefer_f_cu_slot")])
    assert "compiled_rule" in str(ei.value)
    assert "check_only" in str(ei.value)


def test_compiled_rule_wrong_type_fails_closed():
    with pytest.raises(CompilerError) as ei:
        compile_rules([make_entry("P-BAD", compiled_rule=42)])
    assert "compiled_rule" in str(ei.value)


# ---------------------------------------------------------------- 第 5/6 问冲突图

def test_conflicts_with_unknown_id_reports_key_path(v2_board):
    entries = [make_entry("P-A", conflicts_with=["P-NOPE"])]
    with pytest.raises(CompilerError) as ei:
        compile_board(make_board(v2_board, entries))
    assert "conflict_policy.conflicts_with[0]" in str(ei.value)
    assert "P-NOPE" in str(ei.value)


def test_yields_to_unknown_id_reports_key_path(v2_board):
    entries = [make_entry("P-A", yields_to=["P-GHOST"])]
    with pytest.raises(CompilerError) as ei:
        compile_board(make_board(v2_board, entries))
    assert "conflict_policy.yields_to[0]" in str(ei.value)
    assert "P-GHOST" in str(ei.value)


def test_conflict_graph_priority_winner():
    """winner 预解析：priority 高者胜（30 > 10 → P-A 胜）。"""
    graph = build_conflict_graph([make_entry("P-A", priority=30, conflicts_with=["P-B"]),
                                  make_entry("P-B", priority=10)])
    assert graph["nodes"] == ["P-A", "P-B"]
    assert graph["edges"] == [{"a": "P-A", "b": "P-B", "basis": "declared",
                               "winner": "P-A", "loser": "P-B", "resolution": "priority"}]


def test_conflict_graph_yields_to_overrides_priority():
    """yields_to 显式让位覆盖 priority：P-A priority 高但让位 → P-B 胜。"""
    graph = build_conflict_graph([make_entry("P-A", priority=30, conflicts_with=["P-B"],
                                             yields_to=["P-B"]),
                                  make_entry("P-B", priority=10)])
    assert len(graph["edges"]) == 1
    edge = graph["edges"][0]
    assert (edge["winner"], edge["loser"], edge["resolution"]) == ("P-B", "P-A", "yields_to")


def test_conflict_graph_priority_tie_breaks_deterministically():
    graph = build_conflict_graph([make_entry("P-ZZ", priority=10, conflicts_with=["P-AA"]),
                                  make_entry("P-AA", priority=10)])
    assert graph["edges"][0]["winner"] == "P-AA"  # 同 priority → id 字典序小者胜


def test_conflict_graph_dedup_and_sorted_deterministic():
    """边去重（双向声明+重复声明 → 单边）且按 (a,b) 排序。"""
    graph = build_conflict_graph([
        make_entry("P-A", conflicts_with=["P-B", "P-C", "P-B"]),
        make_entry("P-B", conflicts_with=["P-A", "P-C"]),
        make_entry("P-C"),
    ])
    pairs = [(e["a"], e["b"]) for e in graph["edges"]]
    assert pairs == [("P-A", "P-B"), ("P-A", "P-C"), ("P-B", "P-C")]
    assert pairs == sorted(pairs) and len(pairs) == len(set(pairs))


def test_mutual_yields_to_fails_closed():
    """双向 yields_to 无确定 winner → CompilerError。"""
    with pytest.raises(CompilerError) as ei:
        build_conflict_graph([make_entry("P-A", yields_to=["P-B"]),
                              make_entry("P-B", yields_to=["P-A"])])
    assert "yields_to" in str(ei.value)


def test_self_conflict_fails_closed():
    with pytest.raises(CompilerError) as ei:
        build_conflict_graph([make_entry("P-A", conflicts_with=["P-A"])])
    assert "conflicts_with[0]" in str(ei.value)


def test_duplicate_principle_id_fails_closed():
    with pytest.raises(CompilerError) as ei:
        build_conflict_graph([make_entry("P-A"), make_entry("P-A")])
    assert "重复" in str(ei.value)


# ---------------------------------------------------------------- 七问语义校验

def test_hard_overridable_true_fails_closed(v2_board):
    entries = [make_entry("P-HARD", hard=True, overridable=True)]
    with pytest.raises(CompilerError) as ei:
        compile_board(make_board(v2_board, entries))
    assert "overridable" in str(ei.value)


def test_hard_overridable_false_passes(v2_board):
    entries = [make_entry("P-HARD", hard=True, overridable=False,
                          compiled_rule={"kind": "keepout_absolute"})]
    artifact, _ = compile_board(make_board(v2_board, entries))
    assert artifact["coverage"]["compiled"] == 1
    assert artifact["rules"][0]["principle_id"] == "P-HARD"


def test_source_hash_tamper_fails_closed(v2_board):
    entry = make_entry("P-TAMPER")
    entry["priority"] = 99  # 哈希之后篡改
    with pytest.raises(CompilerError) as ei:
        compile_board(make_board(v2_board, [entry]))
    assert "source_hash" in str(ei.value)
    assert "principle_registry[0]" in str(ei.value)


def test_source_hash_correct_passes():
    entry = make_entry("P-OK")
    view = {k: v for k, v in entry.items() if k != "source_hash"}
    assert entry["source_hash"] == canonical.canonical_sha256(view)
    assert semantic_checks([entry]) == []


def test_empty_evidence_refs_annotated_not_error(v2_board):
    """evidence_refs 空数组不报错 → coverage.evidence_insufficient（七问第 7 问口径）。"""
    entries = [make_entry("P-NOEV", evidence=[]), make_entry("P-EV")]
    artifact, _ = compile_board(make_board(v2_board, entries))
    assert artifact["coverage"]["evidence_insufficient"] == ["P-NOEV"]


# ---------------------------------------------------------------- scope 解析

def test_scope_zone_form():
    res = resolve_scope([make_entry("P-Z", scope="zone:C1")], build_v2_board())
    assert res["P-Z"]["zones"] == ["C1"]
    assert res["P-Z"]["partitions"] == [] and res["P-Z"]["nets"] == []
    assert res["P-Z"]["warnings"] == []


def test_scope_ptype_form():
    res = resolve_scope([make_entry("P-P", scope="ptype:PWR")], build_v2_board())
    assert res["P-P"]["partitions"] == ["P1", "P8"]  # V2 板仅 P1/P8 为 PWR
    assert res["P-P"]["zones"] == [] and res["P-P"]["nets"] == []


def test_scope_net_class_form():
    res = resolve_scope([make_entry("P-N", scope="net_class:CLK")], build_v2_board())
    assert res["P-N"]["nets"] == ["P2"]
    assert res["P-N"]["partitions"] == [] and res["P-N"]["zones"] == []


def test_scope_partition_form_hits_partition_and_referencing_nets():
    """partition:<id>：精确命中分区 + 连带命中引用它的 net（v2 板 net P3 引用分区 P3）。"""
    res = resolve_scope([make_entry("P-DF", scope="partition:P3")], build_v2_board())
    r = res["P-DF"]
    assert r["partitions"] == ["P3"]
    assert r["nets"] == ["P3"]
    assert r["zones"] == []
    assert r["warnings"] == []


def test_scope_partition_form_multi_net_referencing():
    """多个网引用同一分区时全部连带命中（demo-02 DF1 双差分网形态）。"""
    board = {"partitions": [{"partition_id": "DF1", "ptype": "DIFF"}],
             "zones": [],
             "nets": [{"net_id": "DIFF-P", "partitions": ["DF1"]},
                      {"net_id": "DIFF-N", "partitions": ["DF1"]},
                      {"net_id": "OTHER", "partitions": ["MS1"]}]}
    res = resolve_scope([make_entry("P-EQ", scope="partition:DF1")], board)
    assert res["P-EQ"]["partitions"] == ["DF1"]
    assert res["P-EQ"]["nets"] == ["DIFF-N", "DIFF-P"]  # 排序确定
    assert res["P-EQ"]["warnings"] == []


def test_scope_partition_unknown_id_fails_closed(v2_board):
    """partition:<不存在> → 未知引用 fail-closed，带键路径（直调 + compile_board 两路）。"""
    with pytest.raises(CompilerError) as ei:
        resolve_scope([make_entry("P-BAD", scope="partition:NOPE")], v2_board)
    assert "principle_registry[0].scope" in str(ei.value)
    assert "NOPE" in str(ei.value)
    with pytest.raises(CompilerError) as ei:
        compile_board(make_board(v2_board, [make_entry("P-BAD", scope="partition:NOPE")]))
    assert "principle_registry[0].scope" in str(ei.value)


def test_scope_partition_multi_token_mix():
    """partition: 与 zone:/ptype: 混用：命中并集。"""
    res = resolve_scope([make_entry("P-MIX", scope="zone:C1, partition:P3, ptype:PWR")],
                        build_v2_board())
    r = res["P-MIX"]
    assert r["zones"] == ["C1"]
    assert r["partitions"] == ["P1", "P3", "P8"]  # P3（精确）∪ P1/P8（ptype:PWR）
    assert r["nets"] == ["P3"]  # 仅 partition:P3 连带的引用网
    assert r["warnings"] == []


def test_scope_partitioning_hits_all_partitions():
    res = resolve_scope([make_entry("P-ALL", scope="partitioning")], build_v2_board())
    assert res["P-ALL"]["partitions"] == ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]


def test_scope_multi_token_merges_hits():
    res = resolve_scope([make_entry("P-M", scope="zone:C1, ptype:PWR")], build_v2_board())
    assert res["P-M"]["zones"] == ["C1"]
    assert res["P-M"]["partitions"] == ["P1", "P8"]


def test_scope_miss_records_warning_not_error():
    """匹配不到任何对象 → 记 warning 不报错。"""
    res = resolve_scope([make_entry("P-MISS", scope="zone:NOPE, net_class:GHOST")],
                        build_v2_board())
    r = res["P-MISS"]
    assert r["partitions"] == [] and r["zones"] == [] and r["nets"] == []
    assert len(r["warnings"]) == 1


def test_scope_illegal_token_fails_closed():
    with pytest.raises(CompilerError) as ei:
        resolve_scope([make_entry("P-BAD", scope="favor:everything")], build_v2_board())
    assert "scope" in str(ei.value)


def test_scope_illegal_token_aborts_compile_board(v2_board):
    with pytest.raises(CompilerError) as ei:
        compile_board(make_board(v2_board, [make_entry("P-BAD", scope="zone:")]))
    assert "principle_registry[0].scope" in str(ei.value)


# ---------------------------------------------------------------- 覆盖率门

def test_coverage_gate_breaks_on_pipeline_bug():
    """compiled+check_only != total → 覆盖率 100% 门断言失败。"""
    entries = [make_entry("P-A"), make_entry("P-B")]
    with pytest.raises(CompilerError) as ei:
        coverage_report(entries, [], [], [])
    assert "覆盖率" in str(ei.value)


def test_coverage_report_full_counts():
    entries = [make_entry("P-A"), make_entry("P-B", compiled_rule="check_only")]
    rules, check_only = compile_rules(entries)
    report = coverage_report(entries, rules, check_only, [])
    assert report == {"total": 2, "compiled": 1, "check_only": 1,
                      "coverage_pct": 100.0, "evidence_insufficient": []}


# ---------------------------------------------------------------- 工件 schema round-trip

def test_broken_artifact_schema_reports_path(v2_board):
    """故意拆坏工件字段 → schema 报具体键路径（非法样例 fail-closed）。"""
    artifact, _ = compile_board(make_board(v2_board, [make_entry("P-A")]))

    bad = copy.deepcopy(artifact)
    bad["rules"][0]["generator_target"] = "magic"  # 枚举外
    with pytest.raises(schema_loader.SchemaViolation) as ei:
        schema_loader.validate(bad, COMPILED, REG, "")
    assert "rules[0].generator_target" in str(ei.value)

    bad = copy.deepcopy(artifact)
    del bad["coverage"]  # 必填缺失
    with pytest.raises(schema_loader.SchemaViolation) as ei:
        schema_loader.validate(bad, COMPILED, REG, "")
    assert "coverage" in str(ei.value)

    bad = copy.deepcopy(artifact)
    bad["bonus"] = 1  # additionalProperties 禁止
    with pytest.raises(schema_loader.SchemaViolation) as ei:
        schema_loader.validate(bad, COMPILED, REG, "")
    assert "bonus" in str(ei.value)

    bad = copy.deepcopy(artifact)
    bad["check_only"] = [{"principle_id": "P-X", "reason": "自由发挥"}]  # reason const 锁定
    with pytest.raises(schema_loader.SchemaViolation) as ei:
        schema_loader.validate(bad, COMPILED, REG, "")
    assert "reason" in str(ei.value)


def test_artifact_disk_roundtrip(v2_board, tmp_path):
    """canonical 字节落盘 → 重读 → 仍过 schema 且字节稳定。"""
    artifact, fp = compile_board(make_board(v2_board, [make_entry("P-A")]))
    p = tmp_path / "compiled_rules.json"
    p.write_bytes(fp)
    loaded = json.loads(p.read_text(encoding="utf-8"))
    schema_loader.validate(loaded, COMPILED, REG, "")
    assert canonical.canonical_json(loaded) == fp


# ---------------------------------------------------------------- 确定性与空表

def test_double_run_bytes_equal():
    """同 board 两次 compile_board → canonical 字节全等。"""
    def entries():
        return [make_entry("P-WIDE", scope="ptype:PWR", priority=40),
                make_entry("P-CLK", scope="ptype:CLK", conflicts_with=["P-WIDE"]),
                make_entry("P-CHK", compiled_rule="check_only")]

    a1, fp1 = compile_board(make_board(build_v2_board(), entries()))
    a2, fp2 = compile_board(make_board(build_v2_board(), entries()))
    assert a1 == a2
    assert fp1 == fp2
    assert fp1 == canonical.canonical_json(a1)


def test_fingerprint_is_canonical_bytes(v2_board):
    artifact, fp = compile_board(make_board(v2_board, [make_entry("P-A")]))
    assert isinstance(fp, bytes)
    assert fp == canonical.canonical_json(artifact)
    assert hashlib.sha256(fp).hexdigest() == canonical.canonical_sha256(artifact)


def test_empty_registry_compiles_to_valid_empty_artifact(v2_board):
    """空注册表 → 合法空工件，coverage_pct=100.0。"""
    artifact, fp = compile_board(make_board(v2_board, []))
    assert artifact["rules"] == [] and artifact["check_only"] == []
    assert artifact["conflict_graph"] == {"nodes": [], "edges": []}
    assert artifact["coverage"] == {"total": 0, "compiled": 0, "check_only": 0,
                                    "coverage_pct": 100.0, "evidence_insufficient": []}
    assert artifact["board_sha256"] == v2_board["provenance"]["board_sha256"]
    schema_loader.validate(artifact, COMPILED, REG, "")
    assert canonical.canonical_json(artifact) == fp


# ---------------------------------------------------------------- P2 七对冲突图完整化（§5.1 冲突电池）

# 七块对抗板 → (期望唯一 present 的 pair_id, (winner, loser))；
# winner/loser 与板内 priority/yields_to 一致（loser yields_to winner，见板 note）。
ADV_EXPECT = {
    "adv-01-pwr-vs-bus": ("pwr-vs-bus", ("P-PWR-PRIORITY", "P-BUS-INTEGRITY")),
    "adv-02-clk-vs-short": ("clk-vs-short", ("P-CLK-ISOLATE", "P-SHORT-RUN")),
    "adv-03-diff-vs-capacity": ("diff-vs-capacity", ("P-DIFF-PAIRING", "P-CORRIDOR-BUDGET")),
    "adv-04-xtalk-vs-vias": ("xtalk-vs-vias", ("P-XTALK-BUDGET", "P-VIA-FRUGAL")),
    "adv-05-eqlen-vs-layerpref": ("eqlen-vs-layerpref", ("P-EQLEN-GROUP", "P-LAYER-PREF")),
    # adv-06 方向：新网络完成性赢，既有铜保护让位
    "adv-06-copper-vs-completion": ("copper-vs-completion", ("P-COMPLETION", "P-COPPER-GUARD")),
    # adv-07 方向：硬地板赢，软先验 objection 让位
    "adv-07-objection-vs-floor": ("objection-vs-floor", ("P-R1-FLOOR", "P-WIDTH-SLIM")),
}


def _adv_registry(board_id):
    """只读载入对抗板注册表（板文件本身零改动）。"""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "boards", "d", board_id + ".board.v1.json")
    return load_board_file(path)["principle_registry"]


def test_pair_templates_cover_seven_pairs():
    """PAIR_TEMPLATES 覆盖断言：pair_id 恰 7 个、每对双侧 rule_kinds 非空且 basis 带 §5.1 引文。"""
    pair_ids = [t["pair_id"] for t in PAIR_TEMPLATES]
    assert len(pair_ids) == 7
    assert len(set(pair_ids)) == 7
    assert set(pair_ids) == set(exp[0] for exp in ADV_EXPECT.values())
    for tpl in PAIR_TEMPLATES:
        assert len(tpl["sides"]) == 2
        for side in tpl["sides"]:
            assert side["role"]
            assert side["rule_kinds"] and all(
                isinstance(k, str) and k for k in side["rule_kinds"])
        assert "§5.1" in tpl["basis"]


@pytest.mark.parametrize("board_id", sorted(ADV_EXPECT))
def test_detect_adversarial_board_exactly_one_pair_present(board_id):
    """七对全枚举：每块对抗板恰命中 1 对，其余 6 对 present=False。"""
    expected_pair, _ = ADV_EXPECT[board_id]
    results = detect_principle_pairs(_adv_registry(board_id))
    assert len(results) == 7
    present = [r for r in results if r["present"]]
    assert len(present) == 1
    assert present[0]["pair_id"] == expected_pair
    for r in results:
        if not r["present"]:
            assert r == {"pair_id": r["pair_id"], "present": False}


def test_detect_union_covers_all_seven_pairs():
    """七板并集 == 7/7 对（电池全覆盖，无遗漏对）。"""
    union = set()
    for board_id in ADV_EXPECT:
        results = detect_principle_pairs(_adv_registry(board_id))
        union.update(r["pair_id"] for r in results if r["present"])
    assert union == set(t["pair_id"] for t in PAIR_TEMPLATES)


@pytest.mark.parametrize("board_id", sorted(ADV_EXPECT))
def test_detect_winner_loser_matches_board_declaration(board_id):
    """winner/loser 与板内 priority/yields_to 一致（含 adv-06 完成性赢、adv-07 硬地板赢）。"""
    expected_pair, (winner, loser) = ADV_EXPECT[board_id]
    results = detect_principle_pairs(_adv_registry(board_id))
    block = next(r for r in results if r["present"])
    assert block["pair_id"] == expected_pair
    assert (block["winner"], block["loser"]) == (winner, loser)
    assert set(block["principles"].values()) == {winner, loser}


def test_yield_scope_nonempty_and_double_run_identical():
    """yield_scope 非空且确定性：七板双跑同字节（canonical json 全等）。"""
    runs = []
    for _ in range(2):
        results = {bid: detect_principle_pairs(_adv_registry(bid))
                   for bid in sorted(ADV_EXPECT)}
        runs.append(canonical.canonical_json(results))
    assert runs[0] == runs[1]
    for bid, results in results.items():
        block = next(r for r in results if r["present"])
        assert isinstance(block["yield_scope"], str) and block["yield_scope"]
        # 预案点名谁让位：winner 与 loser 都在预案句中
        assert block["winner"] in block["yield_scope"]
        assert block["loser"] in block["yield_scope"]


def test_yield_scope_cites_loser_yields_chain():
    """让位范围=loser 的 yields_to 让位链描述：adv-01 loser 声明链在场。"""
    results = detect_principle_pairs(_adv_registry("adv-01-pwr-vs-bus"))
    block = next(r for r in results if r["present"])
    assert block["loser"] == "P-BUS-INTEGRITY"
    assert "yields_to" in block["yield_scope"]
    assert "P-PWR-PRIORITY" in block["yield_scope"]


def test_detect_block_shapes_exact_and_sorted():
    """块形状精确：present 块键集恰 6 键、absent 块恰 2 键；整体按 pair_id 排序。"""
    results = detect_principle_pairs(_adv_registry("adv-01-pwr-vs-bus"))
    assert [r["pair_id"] for r in results] == sorted(r["pair_id"] for r in results)
    for r in results:
        if r["present"]:
            assert set(r) == {"pair_id", "present", "principles", "winner", "loser",
                              "yield_scope"}
        else:
            assert set(r) == {"pair_id", "present"}


def test_detect_empty_and_unrelated_registry_all_absent():
    """空 registry（及纯无关条目 registry）→ 7 对全 present=False 不崩。"""
    for registry in ([], [make_entry("P-NOISE"), make_entry("P-NOISE2", priority=99)]):
        results = detect_principle_pairs(registry)
        assert len(results) == 7
        assert all(r == {"pair_id": r["pair_id"], "present": False} for r in results)


def test_detect_multi_candidate_side_picks_deterministically():
    """同侧多命中 → 取 (priority 降序, principle_id 升序) 首位，与声明序无关。"""
    entries = [
        make_entry("P-LOW", priority=10, compiled_rule={"kind": "power_corridor_priority"}),
        make_entry("P-ZHIGH", priority=70, compiled_rule={"kind": "power_corridor_priority"}),
        make_entry("P-AHIGH", priority=70, compiled_rule={"kind": "power_corridor_priority"}),
        make_entry("P-BUS", priority=40, compiled_rule={"kind": "ribbon_whole_route"}),
    ]
    block = next(r for r in detect_principle_pairs(entries) if r["present"])
    assert block["pair_id"] == "pwr-vs-bus"
    assert block["principles"]["a"] == "P-AHIGH"  # 同 priority → id 字典序小者
    assert block["winner"] == "P-AHIGH"           # priority 裁决 70 > 40


def test_detect_mutual_yields_in_pair_fails_closed():
    """模板对内互相 yields_to 无确定 winner → CompilerError（与声明式协议同口径）。"""
    entries = [
        make_entry("P-A", priority=80, compiled_rule={"kind": "power_corridor_priority"},
                   yields_to=["P-B"]),
        make_entry("P-B", priority=40, compiled_rule={"kind": "ribbon_whole_route"},
                   yields_to=["P-A"]),
    ]
    with pytest.raises(CompilerError) as ei:
        detect_principle_pairs(entries)
    assert "yields_to" in str(ei.value)


def test_build_full_conflict_graph_on_demo01():
    """组合工件在 demo-01（只读）上不崩：节点=全部 principle_id，7 对全枚举在场。

    demo-01 现状：无声明式冲突边，且仅有单侧 kind 命中（existing_copper_guard 无
    completion_first 对侧）→ edges 空、7 对全 present=False。
    """
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "boards", "d", "demo-01-v2-corridor.board.v1.json")
    board = load_board_file(path)
    graph = build_full_conflict_graph(board)
    assert set(graph) == {"nodes", "edges", "pairs"}
    assert graph["nodes"] == sorted(p["principle_id"] for p in board["principle_registry"])
    assert graph["nodes"] == ["P-CHECK-WIDTHPRIOR-DEMO01", "P-COR-CAP-C1-DEMO01",
                              "P-PART-GRAN-DEMO01", "P-XCOPPER-GUARD-DEMO01"]
    assert graph["edges"] == []
    assert len(graph["pairs"]) == 7
    assert all(not p["present"] for p in graph["pairs"])


def test_full_graph_merges_declared_and_template_to_single_edge():
    """同一对 principle 既有声明边又命中模板 → 恰一条，basis="declared+template"（inline 构造）。"""
    entries = [
        make_entry("P-PWR-PRIORITY", priority=80,
                   compiled_rule={"kind": "power_corridor_priority"},
                   conflicts_with=["P-BUS-INTEGRITY"]),
        make_entry("P-BUS-INTEGRITY", priority=40,
                   compiled_rule={"kind": "ribbon_whole_route"},
                   conflicts_with=["P-PWR-PRIORITY"], yields_to=["P-PWR-PRIORITY"]),
    ]
    graph = build_full_conflict_graph({"principle_registry": entries})
    assert graph["nodes"] == ["P-BUS-INTEGRITY", "P-PWR-PRIORITY"]
    assert len(graph["edges"]) == 1  # 去重：声明边与模板对合并为一条
    edge = graph["edges"][0]
    assert edge == {"a": "P-BUS-INTEGRITY", "b": "P-PWR-PRIORITY",
                    "basis": "declared+template", "winner": "P-PWR-PRIORITY",
                    "loser": "P-BUS-INTEGRITY", "resolution": "yields_to"}
    assert sum(1 for p in graph["pairs"] if p["present"]) == 1


def test_full_graph_adds_template_only_edge_without_declaration():
    """仅模板命中（无任何声明边）→ 新增 basis="template" 边，winner 按 priority 裁决。"""
    entries = [
        make_entry("P-OBJ", priority=20, compiled_rule={"kind": "power_corridor_priority"}),
        make_entry("P-BUS2", priority=90, compiled_rule={"kind": "ribbon_whole_route"}),
    ]
    graph = build_full_conflict_graph({"principle_registry": entries})
    assert graph["edges"] == [{"a": "P-BUS2", "b": "P-OBJ", "basis": "template",
                               "winner": "P-BUS2", "loser": "P-OBJ",
                               "resolution": "priority"}]
    block = next(p for p in graph["pairs"] if p["present"])
    assert block["principles"] == {"a": "P-OBJ", "b": "P-BUS2"}


def test_full_graph_shape_nodes_edges_pairs_sorted():
    """组合工件整体形状：nodes 全量排序、edges 按 (a,b) 排序、pairs 恰 7 块按 pair_id 排序。"""
    entries = [
        make_entry("P-EXTRA"),  # 无关条目也须进 nodes
        make_entry("P-PWR-PRIORITY", priority=80,
                   compiled_rule={"kind": "power_corridor_priority"},
                   conflicts_with=["P-BUS-INTEGRITY"]),
        make_entry("P-BUS-INTEGRITY", priority=40,
                   compiled_rule={"kind": "ribbon_whole_route"},
                   conflicts_with=["P-PWR-PRIORITY"], yields_to=["P-PWR-PRIORITY"]),
    ]
    graph = build_full_conflict_graph({"principle_registry": entries})
    assert graph["nodes"] == ["P-BUS-INTEGRITY", "P-EXTRA", "P-PWR-PRIORITY"]
    assert [(e["a"], e["b"]) for e in graph["edges"]] == \
        sorted((e["a"], e["b"]) for e in graph["edges"])
    assert len(graph["pairs"]) == 7
    assert [p["pair_id"] for p in graph["pairs"]] == sorted(p["pair_id"] for p in graph["pairs"])
