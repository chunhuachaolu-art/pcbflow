"""observation 行构造器（包 c 物化批；ADJUDICATION-2026-09-12 R9–R19）测试。

覆盖：observation-row-v1 注册表追加式注册（REGISTRY_VERSION 不动 + 既有
条目零改动）、三行种（rails/padload/sixkind）构造正例与 schema 零错误、
R10 observation_id 确定性拼接与典序、label 残差公式（E/e、actual=0 →
e=null）、D-OBS-6 显式 null+reason（blocked 行/R6② fail-closed 板转记，
不中断批次）、fail-closed 四类（缺字段/非法枚举/非有限数/账本自洽）、
features 白名单（R17 收窄面）、row_core_sha256 独立重算、确定性
byte-exact、jsonschema 交叉验证。
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import jsonschema
import pytest

from pcbflow import hashing, observation as obs, schemas

_H64 = ("a" * 31 + "b" * 31 + "c" * 2)


def _record(**over):
    rec = {
        "profile_id": "pcbench-demo-board",
        "board_id": "demo_board/One-Air",
        "dataset_id": "kicad-demos-r1",
        "board_path_rel": "datasets/kicad-demos-r1/raw/demo_board/x.kicad_pcb",
        "ff_plan_rel": "profiles/pcbench-demo-board/derived/feedforward-plan.json",
    }
    rec.update(over)
    return rec


def _registry(**over):
    nets = [
        {"net_id": 0, "name": "", "classification": "empty",
         "pad_count": 0, "member_refs": []},
        {"net_id": 1, "name": "GND", "classification": "signal",
         "pad_count": 4, "member_refs": ["U1.1", "U1.2", "C1.1", "C1.2"]},
        {"net_id": 2, "name": "+3V3", "classification": "signal",
         "pad_count": 2, "member_refs": ["U1.3", "C2.1"]},
        {"net_id": 3, "name": "SIG_A", "classification": "signal",
         "pad_count": 2, "member_refs": ["U2.1", "U2.2"]},
        {"net_id": 4, "name": "", "classification": "unnamed",
         "pad_count": 1, "member_refs": ["U3.1"]},
    ]
    reg = {
        "net_count": 5, "named_net_count": 3, "unnamed_net_count": 1,
        "nets": nets, "_pad_count": 12, "_footprint_count": 3,
    }
    reg.update(over)
    return reg


def _ff_plan():
    return {
        "rails": [
            {"net": "+3V3", "pad_count": 4,
             "member_refs": ["U1.1", "C1.1", "C1.1", "J5.2"]},
            {"net": "GND", "pad_count": 3, "member_refs": ["U1.2", "C2.1", "X1.1"]},
        ],
        "signal_layer_pad_load": [
            {"layer": "F.Cu", "pad_count": 10},
            {"layer": "B.Cu", "pad_count": 2},
        ],
        "not_modelled": ["via 预算（无路由器执行）"],
    }


def _ext_plan():
    return {
        "resources": [
            {"kind": "via_budget", "resource_id": "via_budget:board",
             "demand": None, "demand_model": "③ layer-plan via_count_total",
             "basis": ["feedforward_config.DEMAND_MODELS"],
             "not_available_reason": "语料板无路由器执行",
             "not_modelled_verbatim": "via 预算（无路由器执行）"},
            {"kind": "escape_slots", "resource_id": "escape_slots:U1|N",
             "demand": {"value": 1, "unit": "channels",
                        "basis": ["transit 网数（需离场网）"]},
             "demand_model": "② C2 同源模型", "basis": ["audit escape_check"]},
            {"kind": "layer_capacity", "resource_id": "layer_capacity:board",
             "demand": {"value": 12.5, "unit": "mm2",
                        "basis": ["链式直连长×pitch"]},
             "demand_model": "② C3 层预算", "basis": ["C3"]},
            {"kind": "corridor", "resource_id": "corridor:board",
             "demand": None, "demand_model": "D1", "basis": ["无源"],
             "not_available_reason": "语料板域无 structures.buses 源"},
        ],
    }


def _routed_counts():
    return {
        "per_net_by_name": [
            {"name": "+3V3", "pad_count": 3},
            {"name": "GND", "pad_count": 3},
        ],
        "geometry_counts": {"segments": 10, "arcs": 0, "vias": 7, "zones": 1},
        "parser": "net_id_bound（check_stage.parse_routed_geometry）",
    }


def _kwargs(**over):
    kw = dict(
        record=_record(),
        board_sha256=_H64,
        registry_sha256=_H64,
        constraints_sha256=_H64,
        registry_obj=_registry(),
        leakage_group="https://gitlab.example/demo_board",
        split_role="train",
        manifest_ref={"path": "out/v3-tl5/dataset-manifest-kicad-demos-r1.json",
                      "sha256": _H64},
        ff_corpus_plan=_ff_plan(),
        ext_plan=_ext_plan(),
        routed_counts=_routed_counts(),
        r62={"ok": True,
             "per_layer": [{"layer": "F.Cu", "pad_count": 10},
                           {"layer": "B.Cu", "pad_count": 2}]},
    )
    kw.update(over)
    return kw


def _build(**over):
    return obs.build_board_rows(**_kwargs(**over))


# ---------------------------------------------------------------------------
# ① 注册表追加式注册（D-OBS-4；REGISTRY_VERSION 不动 + 既有条目零改动）
# ---------------------------------------------------------------------------

def test_schema_additive_registration():
    assert obs.SCHEMA_NAME in schemas.SCHEMAS
    assert schemas.REGISTRY_VERSION == "3.0"          # 升版被禁止
    assert len(schemas.SCHEMAS) == 22                 # 17+1（追加式）+REPAIR-P3 W-5 四孤儿名 @2026-09-22（快照同步随追加演进；哈希断言不受影响）
    for name in ("gate_record", "disposition_record", "judge_pre_record",
                 "judge_post_record", "decision_ledger_entry",
                 "critic_run_record", "queue_event", "physics_report",
                 "physics_coverage", "bring_up_report",
                 "external_execution_record", "proposal_patch",
                 "search_space", "project_manifest", "profile",
                 "artifact-role-declaration-v1", "critic-flag-verdict-v1"):
        assert name in schemas.SCHEMAS, name
    h1 = schemas.schema_hash(obs.SCHEMA_NAME)
    h2 = schemas.schema_hash(obs.SCHEMA_NAME)
    assert h1 == h2 and len(h1) == 64
    hs = {n: schemas.schema_hash(n) for n in schemas.SCHEMAS}
    assert len(set(hs.values())) == len(hs)           # 互异
    jsonschema.Draft7Validator.check_schema(
        schemas.SCHEMAS[obs.SCHEMA_NAME])             # jsonschema 引擎侧合法


# ---------------------------------------------------------------------------
# ② 三行种正例：行数/行种/schema 零错误/id 确定性
# ---------------------------------------------------------------------------

def test_build_rows_kinds_and_schema_valid():
    rows = _build()
    dims = [r["row_id"].split(":")[0] if ":" in r["row_id"] else r["row_id"]
            for r in rows]
    assert dims.count("rails") == 2 and dims.count("signal_layer_pad_load") == 2
    assert dims.count("via_budget") == 1 and dims.count("escape_slots") == 1
    assert dims.count("layer_capacity") == 1 and dims.count("corridor") == 1
    assert len(rows) == 8
    for row in rows:
        assert schemas.validate("observation-row-v1", row) == []
        assert jsonschema.validate(
            row, schemas.SCHEMAS["observation-row-v1"]) is None
    ids = [r["observation_id"] for r in rows]
    assert ids == sorted(ids)                          # observation_id 典序
    assert len(set(ids)) == len(ids)                   # 唯一
    assert all(i.startswith("obs-kicad-demos-r1-demo_board_One_Air-"
                            "feedforward-") for i in ids)
    assert all(r["stage"] == "feedforward" and r["run_id"] == "obs-rows-r1"
               for r in rows)
    assert all(r["action"] is None for r in rows)      # FF-CORPUS/ffext 无控制
    assert all(r["policy_hash"] is None
               and r["missing_basis_reason"] == obs.MISSING_BASIS_REASON
               for r in rows)                          # R11


def test_rails_row_pairing_and_label():
    rows = {r["row_id"]: r for r in _build() if r["row_id"].startswith("rails:")}
    r = rows["rails:+3V3"]
    # 计划侧=4（含 C1.1 重复引用）；实际侧=板文件 pad 元素计 3
    assert r["prediction"]["value"] == 4 and r["actual"]["value"] == 3
    assert r["label"] == {"residual": -1, "relative_residual": round(-1 / 3, 9)}
    g = rows["rails:GND"]
    assert g["prediction"]["value"] == 3 and g["actual"]["value"] == 3
    assert g["label"] == {"residual": 0, "relative_residual": 0.0}
    assert "M4/R12" in r["measurement_convention"]


def test_padload_row_and_r62_failclosed_passthrough():
    rows = {r["row_id"]: r for r in _build()
            if r["row_id"].startswith("signal_layer_pad_load:")}
    assert rows["signal_layer_pad_load:F.Cu"]["actual"]["value"] == 10
    # R6② 板级 fail-closed → actual=null+reason，行仍出（不中断批次）
    rows2 = {r["row_id"]: r for r in _build(
        r62={"ok": False, "error": "ActualExtError: arc 缺 layer"})}
    bad = [r for r in rows2.values()
           if r["row_id"].startswith("signal_layer_pad_load:")]
    assert len(bad) == 2
    for r in bad:
        assert r["actual"]["value"] is None
        assert "R6② 板级 fail-closed" in r["actual"]["not_available_reason"]
        assert "ActualExtError" in r["actual"]["not_available_reason"]
        assert r["label"] is None
        assert schemas.validate("observation-row-v1", r) == []


def test_via_budget_actual_only_ledger_row():
    row = [r for r in _build() if r["row_id"] == "via_budget:board"][0]
    assert row["prediction"]["value"] is None
    assert "via 预算（无路由器执行）" in row["prediction"]["not_available_reason"]
    assert row["actual"] == {"value": 7, "unit": "count"}
    assert row["label"] is None                        # prediction 侧空不配对
    assert schemas.validate("observation-row-v1", row) == []


def test_blocked_and_semantic_mismatch_actuals():
    rows = {r["row_id"]: r for r in _build()}
    lc = rows["layer_capacity:board"]
    assert lc["prediction"]["value"] == 12.5 and lc["actual"]["value"] is None
    assert "语义不齐" in lc["actual"]["not_available_reason"]
    esc = rows["escape_slots:U1|N"]
    assert esc["actual"]["value"] is None
    assert "粒度不齐" in esc["actual"]["not_available_reason"]
    co = rows["corridor:board"]
    assert co["prediction"]["value"] is None and co["actual"]["value"] is None
    assert co["prediction"]["not_available_reason"] == \
        "语料板域无 structures.buses 源"
    for r in (lc, esc, co):
        assert r["label"] is None
        assert schemas.validate("observation-row-v1", r) == []


def test_label_zero_actual_relative_null():
    routed = _routed_counts()
    routed["per_net_by_name"] = [{"name": "+3V3", "pad_count": 0},
                                 {"name": "GND", "pad_count": 3}]
    rows = {r["row_id"]: r for r in _build(routed_counts=routed)}
    r = rows["rails:+3V3"]
    assert r["actual"]["value"] == 0 and r["prediction"]["value"] == 4
    assert r["label"] == {"residual": -4, "relative_residual": None}


# ---------------------------------------------------------------------------
# ③ D-OBS-5/R17：features 白名单（多余键=additionalProperties 拒绝）
# ---------------------------------------------------------------------------

def test_features_whitelist_and_no_routed_leakage():
    row = _build()[0]
    assert set(row["features"]) == {"footprint_count", "named_net_count",
                                    "net_count", "pad_count",
                                    "unnamed_net_count"}
    assert row["features"] == {"footprint_count": 3, "named_net_count": 3,
                               "net_count": 5, "pad_count": 12,
                               "unnamed_net_count": 1}
    bad = dict(row["features"])
    bad["segment_count"] = 10                          # routed 派生计数禁止入 features
    bad_row = dict(row)
    bad_row["features"] = bad
    assert schemas.validate("observation-row-v1", bad_row) != []


# ---------------------------------------------------------------------------
# ④ row_core_sha256 独立重算（evaluation_metadata 不进 core hash）
# ---------------------------------------------------------------------------

def test_row_core_sha256_recomputable():
    for row in _build():
        body = {k: v for k, v in row.items()
                if k not in ("evaluation_metadata", "row_core_sha256")}
        expect = hashing.sha256_bytes(hashing.canonical_json_bytes(body))
        assert row["row_core_sha256"] == expect
    mutated = dict(_build()[0])
    mutated["evaluation_metadata"] = {"evaluated_at": None, "host": "x",
                                      "elapsed_s": None}
    body = {k: v for k, v in mutated.items()
            if k not in ("evaluation_metadata", "row_core_sha256")}
    assert hashing.sha256_bytes(hashing.canonical_json_bytes(body)) == \
        _build()[0]["row_core_sha256"]                 # host 变动不影响 core


# ---------------------------------------------------------------------------
# ⑤ 确定性：同输入双跑 byte-exact
# ---------------------------------------------------------------------------

def test_determinism_byte_exact():
    a = hashing.canonical_json_bytes(_build())
    b = hashing.canonical_json_bytes(_build())
    assert a == b


# ---------------------------------------------------------------------------
# ⑥ fail-closed 四类（缺字段/非法枚举/非有限数/账本自洽）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mutate,frag", [
    (lambda kw: kw["record"].pop("board_id"), "board_id"),
    (lambda kw: kw["ff_corpus_plan"]["rails"][0].pop("pad_count"),
     "pad_count"),
    (lambda kw: kw["ext_plan"]["resources"][1].update(
        kind="warp_drive"), "非法枚举"),
    (lambda kw: kw["ext_plan"]["resources"][2]["demand"].update(
        value=float("nan")), "非有限数"),
    (lambda kw: kw["routed_counts"].pop("geometry_counts"), "geometry_counts"),
    (lambda kw: kw.update(split_role="tuning"), "非法枚举"),
    (lambda kw: kw["registry_obj"].update(named_net_count=9), "对账 fail-closed"),
])
def test_failclosed(mutate, frag):
    kw = _kwargs()
    mutate(kw)
    with pytest.raises(obs.ObservationRowError, match=frag):
        obs.build_board_rows(**kw)


def test_member_refs_ledger_consistency_failclosed():
    ff = _ff_plan()
    ff["rails"][0]["pad_count"] = 5                    # member_refs 只有 4 条
    with pytest.raises(obs.ObservationRowError, match="自洽"):
        _build(ff_corpus_plan=ff)


def test_rail_net_missing_in_routed_book_null_not_zero():
    routed = _routed_counts()
    routed["per_net_by_name"] = [{"name": "GND", "pad_count": 3}]
    rows = {r["row_id"]: r for r in _build(routed_counts=routed)}
    r = rows["rails:+3V3"]
    assert r["actual"]["value"] is None
    assert "无 net 名全等条目" in r["actual"]["not_available_reason"]
    assert r["label"] is None
    assert schemas.validate("observation-row-v1", r) == []


# ---------------------------------------------------------------------------
# ⑦ 治理组继承（split/leakage/manifest_ref 原样；role 枚举 schema 侧拒绝）
# ---------------------------------------------------------------------------

def test_split_and_leakage_inherited():
    rows = _build(split_role="holdout",
                  leakage_group="https://gitlab.example/ecc83")
    for r in rows:
        assert r["split"] == {
            "dataset_id": "kicad-demos-r1", "role": "holdout",
            "board_id": "demo_board/One-Air",
            "manifest_ref": {
                "path": "out/v3-tl5/dataset-manifest-kicad-demos-r1.json",
                "sha256": _H64}}
        assert r["leakage_group"] == "https://gitlab.example/ecc83"
        assert r["board_revision"] == "kicad-demos-r1"
        assert r["project_id"] == "pcbench-demo-board"
    bad = dict(rows[0])
    bad["split"] = dict(bad["split"], role="tuning")
    assert schemas.validate("observation-row-v1", bad) != []
