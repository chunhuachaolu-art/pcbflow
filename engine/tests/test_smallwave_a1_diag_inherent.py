# -*- coding: utf-8 -*-
"""V5-SMALLWAVE A1 钉值：tools/v5_diag_inherent.py（板固有不可布 witness
自动归因器）的判据冻结式、CLI 面、m2 端到端复算与本批 witness 一致性。

合同（route-v5/V5-SMALLWAVE-TASKBOOK-2026-09-23.md §1.A1/§2 门 1）：
- 判据（冻结）：fixed 类摘除解锁且 routes 类摘除仍锁→(a) 板固有；
  routes 摘除解锁→(b) 引擎；仅宽度规则面解锁→(c) 带值。
- 门 1 含「1 板端到端：m2 复算与本批 witness 一致」——对照件=
  out/v5-p5/diag-failed8/m2-pcie-adapter.diag.json（诊断批检查点）。
- 只读诊断：不写 boards/ 数据面、不产生记分牌主张。
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import v5_diag_inherent as D  # noqa: E402

M2 = os.path.join(ROOT, "out", "v5-p5", "boards", "m2-pcie-adapter")
DIAG_M2 = os.path.join(ROOT, "out", "v5-p5", "diag-failed8",
                       "m2-pcie-adapter.diag.json")
HAVE_M2 = os.path.isfile(os.path.join(M2, "board.json")) \
    and os.path.isfile(os.path.join(M2, "execute.json"))
HAVE_DIAG_M2 = os.path.isfile(DIAG_M2)

# ------------------------------------------------ 世界锚守卫（V5-R2 0.7.0）
# m2 存档=0.5.0 世界跑批产物（wave6）、诊断批检查点=0.6.1 引擎重放——重放
# faithful 是**同世界合同**。executor 0.7.0（rip-up 行为升级：轮 2→5/前缀
# 20→30/导引序池/联合重排）对 0.6.1 检查点的重放 faithful 跨世界不成立
# （exit 3 按设计拒分类）。m2 属 8 板 board-inherent 零漂移红线板（本批不
# 重跑），端到端钉值锚定检查点引擎版本；不一致时 skip 披露。


def _diag_checkpoint_engine():
    try:
        with open(DIAG_M2, encoding="utf-8") as f:
            return json.load(f).get("engine_version")
    except Exception:
        return None


def _require_world_anchor():
    from v5.executor import EXECUTOR_VERSION
    ck = _diag_checkpoint_engine()
    if ck != EXECUTOR_VERSION:
        pytest.skip("m2 检查点引擎=%s vs 现役 %s——重放 faithful 跨世界不成立"
                    "（0.7.0 行为升级披露；m2 属零漂移红线板不重跑，端到端钉"
                    "待下次 8 板重跑世界锚更新）" % (ck, EXECUTOR_VERSION))


def _row(klass, unlocked):
    return {"class": klass, "unlocked": unlocked, "attempts": 1,
            "reason": "x"}


def _witness(routes=False, vias=False, holes=False, edge=False, fixed=False,
             allgeo=False):
    rows = [_row("routes", routes), _row("vias", vias), _row("holes", holes),
            _row("edge", edge), _row("fixed", fixed),
            _row("all-geometric", allgeo)]
    return {"class_removal_unlock": rows}


# ------------------------------------------------ 判据冻结式（纯单元）

def test_classify_a_fixed_unlock_routes_locked():
    v = D.classify(_witness(fixed=True, allgeo=True), [])
    assert v["class"] == "(a) 板设计固有不可布"
    assert v["removal_unlock_classes"] == ["all-geometric", "fixed"]


def test_classify_b_routes_unlock_dominates():
    v = D.classify(_witness(routes=True, fixed=True), [])
    assert v["class"] == "(b) 引擎能力缺口"


def test_classify_c_width_only():
    probes = [{"width_mm": 0.25, "unlocked": False},
              {"width_mm": 0.2, "unlocked": True}]
    v = D.classify(_witness(), probes)
    assert v["class"] == "(c) 规则带值瓶颈"
    assert v["width_unlock_mm"] == [0.2]


def test_classify_c_not_when_fixed_also_unlocks():
    probes = [{"width_mm": 0.2, "unlocked": True}]
    v = D.classify(_witness(fixed=True), probes)
    assert v["class"] == "(a) 板设计固有不可布"   # (c) 要求「仅」宽度面


def test_classify_undetermined_when_nothing_unlocks():
    v = D.classify(_witness(), [])
    assert v["class"].startswith("undetermined")
    assert "不归类" in v["note"]


def test_classify_frozen_criteria_text_pinned():
    v = D.classify(_witness(), [])
    assert "(a) fixed 类摘除解锁且 routes" in v["frozen_criteria"]
    assert "(b) routes 类摘除解锁" in D.FROZEN_CRITERIA
    assert "(c) 仅宽度规则面解锁" in D.FROZEN_CRITERIA


# ------------------------------------------------ CLI 面（快路径）

def test_cli_requires_board_or_board_json():
    with pytest.raises(SystemExit):
        D.main([])


def test_cli_board_json_requires_execute_json(tmp_path):
    bj = tmp_path / "b.json"
    bj.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        D.main(["--board-json", str(bj)])


def test_cli_version_and_disclosure_fields(tmp_path):
    assert D.TOOL_VERSION == "v5.diag_inherent/1.1.1"   # W-1 对齐 1.1.0→
    # 判读修复轮 1.1.1（短路捕获态类摘除=密封域口径+探针态泄漏修复）


# ------------------------------------------------ m2 端到端（门 1 要件）

@pytest.mark.skipif(not HAVE_M2, reason="out/v5-p5/boards/m2-pcie-adapter 缺")
def test_a1_m2_end_to_end_verdict_and_replay():
    """m2 复算：重放 faithful（mod geom-secondary）、失败网/终判与诊断批一致。"""
    _require_world_anchor()
    doc, code = D.diagnose(os.path.join(M2, "board.json"),
                           os.path.join(M2, "execute.json"),
                           board_name="m2-pcie-adapter")
    assert code == 0
    assert doc["replay"]["verdict"] == "FAILED"
    assert doc["replay"]["faithful"] is True
    assert doc["replay"]["faithful_basis"].startswith(
        "equal-mod-geom-secondary")
    assert doc["replay"]["n_geom_secondary_lines"] == 1
    fn = doc["failed_net"]
    assert fn["net"] == "/PWRGD" and fn["attempts"] == 318
    assert fn["exhaustion_cause"].startswith("ripup-exhausted")
    assert doc["verdict"]["class"] == "(a) 板设计固有不可布"
    assert doc["disclosure"].startswith("只读诊断")


@pytest.mark.skipif(not (HAVE_M2 and HAVE_DIAG_M2),
                    reason="m2 板树或诊断批检查点缺")
def test_a1_m2_witness_matches_diag_batch():
    """witness 一致性：类摘除六行、密封普查（三档 pitch）、通道扫描、阻塞
    census 与诊断批检查点逐键同值（判据冻结式的移植忠实面）。"""
    _require_world_anchor()
    doc, code = D.diagnose(os.path.join(M2, "board.json"),
                           os.path.join(M2, "execute.json"),
                           board_name="m2-pcie-adapter")
    assert code == 0
    with open(DIAG_M2, encoding="utf-8") as f:
        diag = json.load(f)
    aw, dw = doc["witness"], diag["witness"]
    mine = {r["class"]: r["unlocked"] for r in aw["class_removal_unlock"]}
    theirs = {r["class"]: r["unlocked"]
              for r in dw["class_removal_unlock"]}
    assert mine == theirs
    assert mine == {"routes": False, "vias": False, "holes": False,
                    "edge": False, "fixed": True, "all-geometric": True}
    assert aw["minimal_removal_class_to_unlock"] == "fixed"
    for ep in ("start", "goal"):
        for k, dv in dw["endpoint_sealing"][ep].items():
            av = aw["endpoint_sealing"][ep][k]
            assert (av["n_edges"], av["n_open"], av["reasons"]) == \
                (dv["n_edges"], dv["n_open"], dv["reasons"]), (ep, k)
    ac, dc = aw["channel_scan"], dw["channel_scan"]
    assert ac["demand_2r5"] == dc["demand_2r5"]
    for lay in ac["per_layer"]:
        av = list(ac["per_layer"][lay]) if ac["per_layer"][lay] is not None \
            else None
        assert av == dc["per_layer"][lay]
    bc, dc2 = aw["blocker_census"], dw["blocker_census"]
    for key in ("fixed_coppers_in_zone", "other_via_points_in_zone",
                "holes_blocking_direct", "engine_ripup_blocker_set"):
        assert bc[key] == dc2[key], key
    # 宽度探针全仍锁（(c) 不成立的批内证据面）
    assert all(not p["unlocked"] for p in doc["width_probes"])


@pytest.mark.skipif(not HAVE_M2, reason="out/v5-p5/boards/m2-pcie-adapter 缺")
def test_a1_cli_json_output_and_net_check(tmp_path):
    """CLI：--json 落盘可解析、--net 预期核对通过；--net 不符=exit 4。"""
    _require_world_anchor()
    out = tmp_path / "m2.json"
    code = D.main(["--board", "m2-pcie-adapter",
                   "--boards-root", os.path.join(ROOT, "out", "v5-p5",
                                                 "boards"),
                   "--json", str(out), "--net", "/PWRGD"])
    assert code == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["verdict"]["class"] == "(a) 板设计固有不可布"
    assert doc["failed_net"]["net"] == "/PWRGD"
    code = D.main(["--board", "m2-pcie-adapter",
                   "--boards-root", os.path.join(ROOT, "out", "v5-p5",
                                                 "boards"),
                   "--net", "WRONG-NET"])
    assert code == 4


@pytest.mark.skipif(not HAVE_M2, reason="out/v5-p5/boards/m2-pcie-adapter 缺")
def test_a1_itemize_fixed_optional_section(tmp_path):
    """固定铜逐项指认可选段：--itemize-fixed 给出失败区固定铜逐枚 cid。"""
    _require_world_anchor()
    out = tmp_path / "m2f.json"
    code = D.main(["--board", "m2-pcie-adapter",
                   "--boards-root", os.path.join(ROOT, "out", "v5-p5",
                                                 "boards"),
                   "--json", str(out), "--itemize-fixed",
                   "--skip-width-probes"])
    assert code == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    it = doc["itemized_fixed"]
    assert it is not None and it["n_fixed_in_zone"] > 0
    assert all("cid" in r and "d_direct" in r for r in it["nearest_fixed"])
    assert doc["width_probes"] == []
