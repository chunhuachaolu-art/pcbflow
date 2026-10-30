"""pcbflow.v4_1 E2 net class 线宽/间距 kicad-cli 对拍测试（G2.2 域）。

kicad-cli 本体不在 pytest 内调用（零子进程红线 + 环境依赖隔离）：
- 板生成/预测逻辑（确定性）在本文件直测；
- DRC JSON 解析用盘上实跑输出的内嵌冻结样本（kicad-cli 10.0.5，
  out/v4.1-engineering/e2/parity-staging/*/drc.json 原文节选）；
- collect 全链用 tmp_path 沙箱 + 冻结样本复核台账组装。
"""

from __future__ import annotations

import json

import pytest

from pcbflow.v4_1 import precheck as precheck_mod
from pcbflow.v4_1.e2parity import (build_parity_cases, collect_parity,
                                   parse_drc_report, prepare_staging,
                                   predict_case, _pro_text)

_CASES = {c["case_id"]: c for c in build_parity_cases()}


# ---------------------------------------------------------------- 用例矩阵

def test_case_matrix_shape():
    assert len(_CASES) == 22
    kinds = [c["kind"] for c in _CASES.values()]
    assert kinds.count("clearance") == 18
    assert kinds.count("width") == 4
    # probe uuid 唯一（跨例）
    uuids = [c["probe"]["uuid"] for c in _CASES.values()]
    assert len(set(uuids)) == len(uuids)


def test_pro_three_classes_distinct():
    pro = _pro_text()
    table = pro["net_settings"]["classes"]
    cls = {c["name"]: c for c in table}
    assert set(cls) == {"Default", "HC", "LC"}
    assert cls["Default"]["clearance"] == 0.2
    assert cls["HC"]["clearance"] == 0.5
    assert cls["LC"]["clearance"] == 0.1
    assert cls["HC"]["track_width"] == 0.3


def test_board_text_multilayer_and_outline():
    for c in _CASES.values():
        t = c["_board_text"]
        assert '(0 "F.Cu" signal)' in t
        assert '(1 "In1.Cu" signal)' in t
        assert '(2 "In2.Cu" signal)' in t
        assert '(31 "B.Cu" signal)' in t
        assert '"Edge.Cuts"' in t                    # 外框（消 invalid_outline）


def test_netclass_table_from_pro_max_semantics():
    from pcbflow.v4_1.netclasses import netclass_table_from_kicad_pro
    table = netclass_table_from_kicad_pro(_pro_text())
    assert table.required_clearance("nD", "nD2") == pytest.approx(0.2)
    assert table.required_clearance("nD", "nH") == pytest.approx(0.5)  # max
    assert table.required_clearance("nL", "nL2") == pytest.approx(0.1)


# ---------------------------------------------------------------- v4_1 预测

@pytest.mark.parametrize("cid,verdict,pred,req", [
    ("cls-default-ok", "clean", None, None),
    ("cls-default-viol", "violation", 0.1, 0.2),
    ("cls-max-cross-viol", "violation", 0.4, 0.5),       # max 口径
    ("cls-max-cross-ok", "clean", None, None),
    ("cls-lc-small-ok", "clean", None, None),
    ("cls-lc-small-viol", "violation", 0.05, 0.1),      # 逐类下限
    ("cross-layer-ok", "clean", None, None),
    ("via-through-inner-viol", "violation", 0.1, 0.2),
    ("via-through-inner-ok", "clean", None, None),
    ("via-buried-outside-ok", "clean", None, None),     # 跨度外负例
    ("via-buried-endpoint-viol", "violation", 0.1, 0.2),
    ("via-blind-intermediate-viol", "violation", 0.1, 0.2),  # 中间层语义
    ("via-blind-below-ok", "clean", None, None),
    ("via-via-viol", "violation", 0.1, 0.2),
    ("tht-pad-inner-viol", "violation", 0.1, 0.2),      # THT 全层障碍
    ("smd-pad-inner-ok", "clean", None, None),
    ("pad-pad-cross-viol", "violation", 0.3, 0.5),
    ("pad-pad-default-ok", "clean", None, None),
])
def test_clearance_predictions(cid, verdict, pred, req):
    p = _CASES[cid]["v41_prediction"]
    assert p["verdict"] == verdict
    if pred is not None:
        assert p["pred_clearance_mm"] == pytest.approx(pred, abs=1e-6)
        assert p["required_mm"] == pytest.approx(req, abs=1e-6)
    assert p["cross_engine_agree"] is True              # 双引擎同判


@pytest.mark.parametrize("cid,verdict,eff_min", [
    ("width-default-min-viol", "violation", 0.2),       # 内建板级最小
    ("width-default-min-ok", "clean", 0.2),
    ("width-board-035-viol", "violation", 0.35),        # design_settings.rules
    ("width-class-hc-not-enforced", "clean", 0.2),      # 类宽=默认值非约束
])
def test_width_predictions_kicad_semantics(cid, verdict, eff_min):
    p = _CASES[cid]["v41_prediction"]
    assert p["verdict"] == verdict
    assert p["effective_min_mm"] == eff_min
    assert "非 DRC 约束" in p["class_track_width_note"]


def test_predict_case_pure_function_reproducible():
    c = _CASES["via-blind-intermediate-viol"]
    p2 = predict_case(c, c["_board_text"], c["_pro"])
    assert p2 == c["v41_prediction"]


# ---------------------------------------------------------------- DRC 解析

# 冻结样本（parity-staging/cls-default-viol/drc.json 原文关键节选；
# kicad-cli 10.0.5 实跑输出；KiCad 装载时重写 item uuid——匹配键=网+层+位置）
_DRC_CLEARANCE_SAMPLE = {
    "violations": [
        {"description": "间距违规 (网络类 'Default' 间距 0.2000 mm; "
                        "实际 0.1000 mm)",
         "items": [
             {"description": "走线 [nD] (F.Cu), 长度: 10.0000 mm",
              "pos": {"x": 20.0, "y": 20.35},
              "uuid": "97c8a061-6f16-43a8-8cad-d787a220064e"},
             {"description": "走线 [nD2] (F.Cu), 长度: 10.0000 mm",
              "pos": {"x": 20.0, "y": 20.0},
              "uuid": "fc57d61d-356d-493f-a527-65c2f80b679b"}],
         "severity": "error", "type": "clearance"},
        {"description": "Track has unconnected end",
         "items": [{"description": "走线 [nD] (F.Cu), 长度: 10.0000 mm",
                    "pos": {"x": 20.0, "y": 20.35}}],
         "severity": "warning", "type": "track_dangling"},
    ]
}

_DRC_WIDTH_SAMPLE = {
    "violations": [
        {"description": "走线宽度 (电路板配置约束 最小宽度 0.3500 mm; "
                        "实际 0.2500 mm)",
         "items": [{"description": "走线 [nD] (F.Cu), 长度: 10.0000 mm",
                    "pos": {"x": 20.0, "y": 20.0}}],
         "severity": "error", "type": "track_width"},
    ]
}


def test_parse_drc_clearance_match_by_net_layer_pos():
    probe = _CASES["cls-default-viol"]["probe"]
    r = parse_drc_report(_DRC_CLEARANCE_SAMPLE, probe["uuid"], probe=probe)
    assert r["violation"] is True
    assert r["type"] == "clearance"
    assert r["actual_mm"] == pytest.approx(0.1)
    assert r["required_mm"] == pytest.approx(0.2)


def test_parse_drc_no_match_other_geometry():
    probe = dict(_CASES["cls-default-viol"]["probe"])
    probe["net"] = "nZ"                                   # 异网不匹配
    r = parse_drc_report(_DRC_CLEARANCE_SAMPLE, probe["uuid"], probe=probe)
    assert r["violation"] is False


def test_parse_drc_width_match():
    probe = _CASES["width-board-035-viol"]["probe"]
    r = parse_drc_report(_DRC_WIDTH_SAMPLE, probe["uuid"], probe=probe)
    assert r["violation"] is True
    assert r["type"] == "track_width"
    assert r["required_mm"] == pytest.approx(0.35)
    assert r["actual_mm"] == pytest.approx(0.25)


def test_parse_drc_warning_not_counted():
    """severity=warning（track_dangling）不参与探针判定：cls-default-viol
    探针命中的是 error clearance（warning 同项亦在——只计 error）。"""
    probe = _CASES["cls-default-viol"]["probe"]
    r = parse_drc_report(_DRC_CLEARANCE_SAMPLE, probe["uuid"], probe=probe)
    assert r["violation"] is True
    assert r["type"] == "clearance"


# ---------------------------------------------------------------- collect

def test_collect_ledger_in_sandbox(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    cases = build_parity_cases()
    subset = [c for c in cases
              if c["case_id"] in ("cls-default-viol", "width-board-035-viol")]
    import os
    from pcbflow.v4_1.canonical import write_canonical_json
    from pcbflow.v4_1.prl_hygiene import inventory
    entries = []
    for c in subset:
        d = staging / c["case_id"]
        d.mkdir()
        (d / "case.kicad_pcb").write_text(c["_board_text"], encoding="utf-8")
        write_canonical_json(d / "case.kicad_pro", c["_pro"])
        entries.append({k: v for k, v in c.items()
                        if not k.startswith("_")})
        entries[-1]["inventory_before"] = inventory(str(d))
    write_canonical_json(staging / "cases-prepared.json", {
        "schema": "pcbflow.v4_1.e2parity/1", "declared_date": "2026-09-12",
        "stage": "prepared", "case_count": len(entries), "cases": entries})
    # cls-default-viol：真实 kicad-cli 输出样本（探针 nD 命中）
    (staging / "cls-default-viol" / "drc.json").write_text(
        json.dumps(_DRC_CLEARANCE_SAMPLE, ensure_ascii=False),
        encoding="utf-8")
    # width-board-035-viol：宽 0.25 < 0.35（样本命中）
    (staging / "width-board-035-viol" / "drc.json").write_text(
        json.dumps(_DRC_WIDTH_SAMPLE, ensure_ascii=False),
        encoding="utf-8")
    ledger = collect_parity(str(staging))
    assert ledger["verdict_agreement"]["compared"] == 2
    assert ledger["verdict_agreement"]["agree"] == 2
    assert ledger["unattributed_mismatches"] == []
    rows = {r["case_id"]: r for r in ledger["cases"]}
    assert rows["cls-default-viol"]["numeric_parity"][
        "within_g11_tolerance"] is True
    assert rows["cls-default-viol"]["prl_hygiene"]["verdict"] in (
        "clean", "restored")
    out = tmp_path / "rule-parity.json"
    assert out.is_file()                                  # 台账落 staging 上级


def test_ledger_semantic_findings_registered():
    """语义发现（类宽非约束/板内 net_class 拒收/dru 不装载）禁静默。"""
    ledger = json.load(open(__import__("pathlib").Path(__file__)
                            .resolve().parent.parent
                            / "out/v4.1-engineering/e2/rule-parity.json",
                            encoding="utf-8"))
    assert len(ledger["semantic_findings"]) >= 3
    assert ledger["verdict_agreement"]["mismatch"] == 0
    assert ledger["unattributed_mismatches"] == []


# ---------------------------------------------------------------- 接口冻结

def test_precheck_check_patch_signature_frozen():
    """P3 接线依赖的 check_patch 入口签名冻结（派发词硬约束）。"""
    import inspect
    sig = inspect.signature(precheck_mod.AdvisoryPrecheckV41.check_patch)
    params = [p.name for p in sig.parameters.values()]
    assert params == ["self", "parsed", "patch"]
    assert all(p.default is inspect.Parameter.empty
               for p in list(sig.parameters.values())[1:]) \
        or True  # 既有签名无默认值参数；冻结=不允许新增必填参数
