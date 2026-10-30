"""pcbflow.v4_1 G1.1 根因回归测试（本包核心；任务书 §3 E1）。

P3REVC-BATCH-01 原候选（LTDC_R7 倒角 vs U1.109）必须被 v4_1 预检预测为
违例；预测 clearance 对拍 kicad-cli 实测 0.1571mm（预注册容差 0.01mm）。
盘上证据件缺失时跳过盘上部分（内嵌冻结几何部分恒跑）。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcbflow.v4_1 import (G11_TOLERANCE_MM, P3REVC_BATCH01_MEASURED_MM)
from pcbflow.v4_1.regression import (EMBEDDED_BATCH01_CASE, G11Case,
                                     load_g11_context, run_g11)

REPO = Path(__file__).resolve().parent.parent
PERNET = REPO / "out/v4-exec/p3-revc/per-net-batch"
BATCH01 = PERNET / "batch-01"


def test_g11_embedded_root_cause_regression():
    r = run_g11()
    assert r["gate_verdict"] == "pass"
    pre = r["precheck"]
    # 1) 预测为违例（根因回归核心断言）
    assert pre["verdict"] == "violation"
    hit = [v for v in pre["full_violations"]
           if v["item_ref"] == "U1.109"]
    assert hit, "LTDC_R7 倒角 vs U1.109 未被预测为违例（根因回归失败）"
    assert hit[0]["flag_class"] == "hard_violation"
    # 2) 对拍：|预测 - 实测| <= 0.01mm
    assert pre["pred_clearance_mm_vs_U1_109"] == pytest.approx(
        0.157043, abs=1e-6)
    assert pre["abs_diff_vs_measured_mm"] <= G11_TOLERANCE_MM
    assert pre["tolerance_pass"] is True
    # 3) checker 交叉同判
    assert r["cross_check"]["precheck_vs_checker_agree_on_violation"] is True
    chk = r["checker"]
    assert chk["verdict"] == "violation"
    assert chk["pred_clearance_mm_vs_U1_109"] is not None
    assert chk["abs_diff_vs_measured_mm"] <= G11_TOLERANCE_MM
    # 4) 负对照（回归测试的牙齿）：旧 P3 模型 min(w,h)/2 对同几何放行
    old = r["negative_control_old_p3_model"]
    assert old["old_verdict_pass"] is True
    assert old["old_min_centerline_dist_mm"] == pytest.approx(
        0.673552, abs=1e-6)
    assert old["old_need_mm"] == pytest.approx(0.425)


def test_g11_embedded_case_matches_disk_evidence_constants():
    c = EMBEDDED_BATCH01_CASE
    assert c["kicad_measured_clearance_mm"] == P3REVC_BATCH01_MEASURED_MM
    assert c["kicad_required_clearance_mm"] == 0.2
    assert c["segment"] == [(48.1263, 23.15), (48.638432, 23.362132)]


@pytest.mark.skipif(not (BATCH01 / "candidates.json").is_file(),
                    reason="P3REVC-BATCH-01 evidence absent")
class TestDiskContext:
    def test_disk_measured_value_anchored(self):
        drc = json.loads((BATCH01 / "drc-all.json").read_text(encoding="utf-8"))
        hits = [v for v in drc["violations"]
                if v.get("type") == "clearance"
                and any("LTDC_R7" in str(i.get("description", ""))
                        for i in v.get("items", []))
                and any("U1" in str(i.get("description", ""))
                        for i in v.get("items", []))]
        assert len(hits) == 1
        assert "0.1571" in hits[0]["description"]
        assert "0.2000" in hits[0]["description"]

    def test_disk_context_full_board_regression(self):
        ctx = load_g11_context(REPO)
        assert ctx is not None
        assert ctx["measured_mm"] == pytest.approx(
            P3REVC_BATCH01_MEASURED_MM, abs=1e-9)
        # 双路径交叉解析一致（对拍不一致=blocked 纪律）
        a, b = ctx["board_parse_a"], ctx["board_parse_b"]
        assert a["stats"] == b["stats"]
        assert a["pads"] == b["pads"]
        assert a["segments"] == b["segments"]
        assert a["vias"] == b["vias"]
        # net class：盘上 kicad_pro 实测载入（缺则 fail-closed 登记
        # not_available；本盘在盘 -> 18 类）
        if ctx["netclass_status"].startswith("loaded_kicad_pro"):
            assert len(ctx["net_table"].classes) == 18
            assert ctx["net_table"].required_clearance(
                "LTDC_R7", "FMC_BA1") == pytest.approx(0.2)
        else:
            assert "not_available" in ctx["netclass_status"]

    def test_disk_context_all_six_patches(self):
        from pcbflow.v4_1.precheck import (AdvisoryPrecheckV41,
                                           build_geom_items)
        ctx = load_g11_context(REPO)
        a = ctx["board_parse_a"]
        pre = AdvisoryPrecheckV41(
            build_geom_items(a), ctx["net_table"],
            protected_nets=[p["net_id"] for p in
                            ctx["candidates"]["patches"]])
        verdicts = {}
        for patch in ctx["candidates"]["patches"]:
            r = pre.check_patch(a, patch)
            verdicts[patch["net_id"]] = r
            # 每网至少可预检（无 blocked）
            assert r["verdict"] in ("violation", "clean"), \
                "patch %s blocked: %r" % (patch["patch_id"], r)
        # 根因回归：LTDC_R7 = violation 且 U1.109 命中 0.157043
        r7 = verdicts["LTDC_R7"]
        assert r7["verdict"] == "violation"
        u109 = [v for seg in r7["per_segment"]
                for v in seg["violations"] if v["item_ref"] == "U1.109"]
        hard = [v for v in u109 if v["flag_class"] == "hard_violation"]
        assert hard, "U1.109 未被硬违例命中"
        assert hard[0]["pred_clearance_mm"] == pytest.approx(0.157043,
                                                             abs=1e-6)
        # kicad-cli ground truth：其余 5 网无新增违例 -> 无硬违例
        # （带内保守标记允许=误报台账素材，非漏报方向）
        for net in ("VBAT_CHG", "HSE_OUT", "CC1", "CC2", "FDCAN1_TX"):
            segs = verdicts[net]["per_segment"]
            hard_hits = [v for s in segs for v in s["violations"]
                         if v["flag_class"] == "hard_violation"]
            assert not hard_hits, \
                "net %s 硬违例误报（kicad-cli 判该批零新增）: %r" % (
                    net, hard_hits)
