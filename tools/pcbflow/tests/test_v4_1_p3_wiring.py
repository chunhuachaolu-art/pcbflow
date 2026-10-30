"""P3 候选链预检接线回归测试（R27 / DEV-E1-003 wiring_release）。

接线对象：pcbflow/p3_revc_staging.py 候选链预检点——旧
_precheck_segments（pad=min(w,h)/2 中心距近似，P3REVC-BATCH-01 漏报
根因）已删除，链上预检改为 pcbflow.v4_1.precheck.check_patch 终态全段
精确预检（Minkowski 核焊盘几何+逐网 net class clearance+保守带 0.01）。

三组用例（任务书接线小包 §2）：

1. G1.1 场景在 P3 链路径上被拦截（LTDC_R7 patch 输入 → 链上预检门判违例，
   不只 v4_1 直调；含全链重生成时 k1 候选不再被接受）；
2. 负对照=已知合法 patch 不被硬拦（E1 g1-1-disk-context.json 全板六 patch
   复检数据复用：kicad-cli 判零新增的 5 网无 hard_violation）；
3. 旧近似路径（已删除）与新路径判定差异逐例登记（旧口径用保留的几何
   助手 _point_seg_dist/_seg_seg_dist 在测试内复算——与被删 L491 实现
   同式，防复制品漂移由断言锚定）。

盘上证据件缺失时跳过盘上组（fail-closed 纪律同 test_v4_1_regression_g11）。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pcbflow import p3_revc_staging as pr
from pcbflow.v4_1 import G11_TOLERANCE_MM, P3REVC_BATCH01_MEASURED_MM
from pcbflow.v4_1.regression import (EMBEDDED_BATCH01_CASE, G11Case)

REPO = Path(__file__).resolve().parent.parent
PERNET = REPO / "out/v4-exec/p3-revc/per-net-batch"
SNAPSHOT = PERNET / "snapshot-pristine.kicad_pcb"
BATCH01 = PERNET / "batch-01"
DISK_CTX = REPO / "out/v4.1-engineering/e1/g1-1-disk-context.json"
KICAD_PRO = REPO.parent.parent / (
    "design/coreboard/kicad/stm32h743-coreboard-revc/"
    "stm32h743-coreboard-revc.kicad_pro")

DISK_PRESENT = (SNAPSHOT.is_file()
                and (BATCH01 / "candidates.json").is_file())
DISK_CTX_PRESENT = DISK_PRESENT and DISK_CTX.is_file()


def _load_pro():
    if not KICAD_PRO.is_file():
        return None
    return json.loads(KICAD_PRO.read_text(encoding="utf-8"))


def _chain_state():
    """盘上真链状态（快照文本 → staging 解析 → 链 → 冻结批次）。"""
    text = SNAPSHOT.read_text(encoding="utf-8")
    sha = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
    parsed = pr.parse_board_text(text)
    chains = pr.build_chains(parsed)
    _rows, batches = pr.plan_pool(parsed, chains)
    return text, sha, parsed, chains, batches


def _chain_engine(text, parsed, nets):
    """链上同源引擎（generate_batch_candidates 内部同款构建）。"""
    return pr._build_v41_precheck(parsed, text, _load_pro(), set(nets))


# ================================================================ 组 0：
# 接线牙齿（零盘上依赖）

def test_old_approximation_precheck_removed():
    """旧近似预检函数已删除（R27：无引用即删；防回退）。"""
    assert not hasattr(pr, "_precheck_segments")
    # 通用几何助手保留（组 3 差异登记复用；非近似专用）
    assert hasattr(pr, "_point_seg_dist")
    assert hasattr(pr, "_seg_seg_dist")


def test_missing_board_text_fail_closed():
    """board_text 缺失 → ValueError fail-closed（旧近似不得静默回退）。"""
    empty = {"segments": [], "vias": [], "pads": [], "zone_nets": [],
             "copper_layers": ["F.Cu"], "edge_points": []}
    with pytest.raises(ValueError, match="v4_1 预检资产缺失"):
        pr.generate_batch_candidates(empty, [], ["X"], "sha0")


def test_engine_declared_defaults_fallback_and_embedded_g11():
    """无 net class 源时回退协议冻结 CLEARANCE_MM；内嵌 G1.1 几何经链上
    引擎构建路径判违例（0.157043 锚，kicad-cli 实测 0.1571 对拍）。"""
    text = G11Case.BOARD_TEXT
    parsed = pr.parse_board_text(text)
    pre = pr._build_v41_precheck(parsed, text, None,
                                 set(("LTDC_R7",)))
    (ax, ay), (bx, by) = EMBEDDED_BATCH01_CASE["segment"]
    r = pre.check_segment("LTDC_R7", "F.Cu",
                          EMBEDDED_BATCH01_CASE["width_mm"],
                          ax, ay, bx, by)
    assert r["verdict"] == "violation"
    hit = [v for v in r["violations"] if v["item_ref"] == "U1.109"]
    assert hit and hit[0]["flag_class"] == "hard_violation"
    assert hit[0]["pred_clearance_mm"] == pytest.approx(0.157043, abs=1e-6)
    assert abs(hit[0]["pred_clearance_mm"]
               - P3REVC_BATCH01_MEASURED_MM) <= G11_TOLERANCE_MM


def test_rejection_reason_class_mapping_compatible():
    """新 reason 前缀保持 _dominant_class → keepout_or_collision 映射。"""
    assert pr._dominant_class(
        ["clearance_fail:v41:hard_violation:pad:U1.109:d=0.1570<0.2000"]) \
        == "keepout_or_collision"
    assert pr._dominant_class(
        ["clearance_fail:move:clearance_fail:v41:conservative_band:track:x"]) \
        == "keepout_or_collision"


# ================================================================ 组 1：
# G1.1 在链路径上被拦截（盘上）

@pytest.mark.skipif(not DISK_PRESENT, reason="P3REVC-BATCH-01 证据不在场")
class TestG11OnChainInterception:
    def test_historical_k1_patch_intercepted_by_chain_gate(self):
        """LTDC_R7 历史 patch（k1 倒角）输入 → 链上预检门判违例。"""
        text, _sha, parsed, _chains, batches = _chain_state()
        hist = json.loads((BATCH01 / "candidates.json").read_text(
            encoding="utf-8"))
        k1 = [p for p in hist["patches"]
              if p["patch_id"] == "P#LTDC_R7#F#S444#ch#S444#k1"]
        assert k1, "历史 k1 候选不在盘上证据内"
        engine = _chain_engine(text, parsed, batches["batch-01"])
        ok, why, r = pr._v41_gate(parsed, k1[0], engine)
        assert not ok
        assert "hard_violation" in why and "U1.109" in why
        u109 = [v for seg in r["per_segment"] for v in seg["violations"]
                if v["item_ref"] == "U1.109"
                and v["flag_class"] == "hard_violation"]
        assert u109, "U1.109 未被链上引擎硬违例命中"
        assert u109[0]["pred_clearance_mm"] == pytest.approx(0.157043,
                                                             abs=1e-6)
        assert abs(u109[0]["pred_clearance_mm"]
                   - P3REVC_BATCH01_MEASURED_MM) <= G11_TOLERANCE_MM

    def test_full_regeneration_intercepts_k1(self):
        """全链重生成：k1 几何不再被接受；LTDC_R7 若出候选必为其他角落；
        全清网复现历史冻结候选几何（确定性对拍）。"""
        text, sha, parsed, chains, batches = _chain_state()
        out = pr.generate_batch_candidates(parsed, chains,
                                           batches["batch-01"], sha,
                                           board_text=text,
                                           kicad_pro_obj=_load_pro())
        accepted_ids = {p["patch_id"] for p in out["patches"]}
        assert "P#LTDC_R7#F#S444#ch#S444#k1" not in accepted_ids
        hist = json.loads((BATCH01 / "candidates.json").read_text(
            encoding="utf-8"))
        hist_by_id = {p["patch_id"]: p for p in hist["patches"]}
        # 确定性守恒：历史全清三网的候选几何逐字节复现
        for net in ("VBAT_CHG", "HSE_OUT", "CC2"):
            hid = [i for i in hist_by_id if i.startswith("P#%s#" % net)]
            assert len(hid) == 1
            assert hid[0] in accepted_ids, "全清网 %s 候选意外被拦" % net
            new_p = [p for p in out["patches"] if p["patch_id"] == hid[0]][0]
            assert new_p["polyline_mm"] == hist_by_id[hid[0]]["polyline_mm"]
            assert new_p["text_ops"] == hist_by_id[hid[0]]["text_ops"]
        # 接受的候选必带 v4_1 预检记录（结构兼容：legacy 键保留）
        for p in out["patches"]:
            rec = p["precheck"]
            assert rec["engine"] == "v4_1_exact_minkowski_core"
            assert rec["v41_verdict"] == "clean"
            assert "min_foreign_centerline_dist_mm" in rec  # legacy 键位
            assert rec["min_foreign_centerline_dist_mm"] is None
            assert rec["min_foreign_clearance_mm"] is not None
            assert rec["corner_region_obstacle_free"] is True
        # band 方向诚实弃权：CC1/FDCAN1_TX（kicad-cli 判合法但带内保守）
        rej_nets = {r["route_id"].split("#")[0] for r in out["rejections"]}
        assert {"CC1", "FDCAN1_TX"} <= rej_nets
        for rej in out["rejections"]:
            if rej["route_id"].startswith(("CC1#", "FDCAN1_TX#")):
                assert rej["reason_class"] == "keepout_or_collision"
                assert any("conservative_band" in r
                           for r in rej["reasons"])


# ================================================================ 组 2：
# 负对照=已知合法 patch 不被硬拦（盘上，E1 disk-context 复用）

@pytest.mark.skipif(not DISK_CTX_PRESENT, reason="E1 disk-context 不在场")
class TestNegativeControlKnownLegal:
    def test_six_patches_no_hard_false_block(self):
        """kicad-cli 判零新增的 5 网经链上引擎无 hard_violation；
        判定与 E1 g1-1-disk-context.json 逐网一致（band 计数对拍）。"""
        text, _sha, parsed, _chains, batches = _chain_state()
        hist = json.loads((BATCH01 / "candidates.json").read_text(
            encoding="utf-8"))
        engine = _chain_engine(text, parsed, batches["batch-01"])
        ctx = json.loads(DISK_CTX.read_text(encoding="utf-8"))
        ctx_by_net = {p["net_id"]: p for p in ctx["patches"]}
        for p in hist["patches"]:
            r = engine.check_patch(parsed, p)
            viol = [v for seg in r["per_segment"] for v in seg["violations"]]
            hard = [v for v in viol if v["flag_class"] == "hard_violation"]
            band = [v for v in viol if v["flag_class"] != "hard_violation"]
            ref = ctx_by_net[p["net_id"]]
            if p["net_id"] == "LTDC_R7":
                assert hard, "G1.1 根因网未判硬违例"
            else:
                # 负对照：已知合法（kicad-cli 零新增）不得被硬拦
                assert not hard, "已知合法网 %s 被硬拦（误报方向违规）" \
                    % p["net_id"]
            assert len(band) == len(ref.get("band_flags") or []), \
                "band 计数与 E1 盘上复检不一致: %s" % p["net_id"]
            assert r["verdict"] == ref["verdict"], \
                "verdict 与 E1 盘上复检不一致: %s" % p["net_id"]

    def test_fully_clean_nets_pass_chain_gate(self):
        """全清三网（零 band 零 hard）经链上预检门完全放行。"""
        text, _sha, parsed, _chains, batches = _chain_state()
        hist = json.loads((BATCH01 / "candidates.json").read_text(
            encoding="utf-8"))
        engine = _chain_engine(text, parsed, batches["batch-01"])
        for p in hist["patches"]:
            if p["net_id"] in ("VBAT_CHG", "HSE_OUT", "CC2"):
                ok, why, _r = pr._v41_gate(parsed, p, engine)
                assert ok and why is None


# ================================================================ 组 3：
# 旧近似（已删）vs 新路径判定差异逐例登记（盘上）

@pytest.mark.skipif(not DISK_PRESENT, reason="P3REVC-BATCH-01 证据不在场")
class TestOldVsNewDivergenceLedger:
    @staticmethod
    def _old_approx_verdict(parsed, patch, fidx):
        """旧近似口径复算（与被删 _precheck_segments/L491 同式，复用保留
        助手 _seg_seg_dist/_point_seg_dist）：仅查新插入段中心距。

        返回 (old_pass, worst)——worst=(kind, ref, d, need) 最紧对。
        """
        ins = patch["text_ops"].get("insert_segment")
        assert ins is not None, "历史六候选均为倒角（insert 段在案）"
        ax, ay = ins["start"]
        bx, by = ins["end"]
        layer, width = ins["layer"], ins["width"]
        need_self = pr.CLEARANCE_MM + width / 2.0
        worst = None
        worst_margin = None
        for (s, _) in fidx["segs"].get(layer, []):
            if s["net"] in fidx["protected"]:
                continue
            need = need_self + s["width"] / 2.0
            d = pr._seg_seg_dist(((ax, ay), (bx, by)),
                                 ((s["x1"], s["y1"]), (s["x2"], s["y2"])))
            margin = d - need
            if worst_margin is None or margin < worst_margin:
                worst_margin, worst = margin, ("segment", s["uuid"], d, need)
        for v in fidx["vias"]:
            if v["net"] in fidx["protected"]:
                continue
            need = need_self + v["size"] / 2.0
            d = pr._point_seg_dist(v["x"], v["y"], ax, ay, bx, by)
            margin = d - need
            if worst_margin is None or margin < worst_margin:
                worst_margin, worst = margin, ("via", v["uuid"], d, need)
        for (layer_p, plist) in fidx["pads"].items():
            for p in plist:
                if p["net_id"] in fidx["protected"] or layer_p != layer:
                    continue
                half = min(p["w_mm"], p["h_mm"]) / 2.0
                need = pr.CLEARANCE_MM + width / 2.0 + half
                d = pr._point_seg_dist(p["x_mm"], p["y_mm"], ax, ay, bx, by)
                margin = d - need
                if worst_margin is None or margin < worst_margin:
                    worst_margin, worst = margin, ("pad", p["pad_id"], d, need)
        return (worst_margin is None or worst_margin >= -1e-9), worst

    def test_divergence_ledger_six_patches(self):
        """六历史候选逐例登记旧/新判定差异。

        - LTDC_R7：旧=放行（漏报）新=硬违例拦截——根因修复分歧；
        - 其余五网：旧=放行，新=clean 或保守带（无旧拦新放的反向松弛）。
        """
        text, _sha, parsed, _chains, batches = _chain_state()
        hist = json.loads((BATCH01 / "candidates.json").read_text(
            encoding="utf-8"))
        fidx = pr.build_foreign_index(parsed, set(batches["batch-01"]))
        engine = _chain_engine(text, parsed, batches["batch-01"])
        ledger = []
        for p in hist["patches"]:
            old_pass, worst = self._old_approx_verdict(parsed, p, fidx)
            r = engine.check_patch(parsed, p)
            viol = [v for seg in r["per_segment"] for v in seg["violations"]]
            hard = any(v["flag_class"] == "hard_violation" for v in viol)
            new_class = ("hard_violation" if hard
                         else ("conservative_band" if viol else "clean"))
            ledger.append({"net": p["net_id"], "old_pass": old_pass,
                           "new_class": new_class})
            # 反向松弛禁止：旧近似拦的，新路径不得放行（本六例旧全放行，
            # 该断言为恒真守恒式，防未来复算口径漂移）
            if not old_pass:
                assert new_class != "clean"
        by_net = {row["net"]: row for row in ledger}
        assert by_net["LTDC_R7"] == {"net": "LTDC_R7", "old_pass": True,
                                     "new_class": "hard_violation"}, \
            "G1.1 根因分歧（旧放行/新硬拦）未复现"
        for net in ("VBAT_CHG", "HSE_OUT", "CC2"):
            assert by_net[net]["old_pass"] is True
            assert by_net[net]["new_class"] == "clean"
        for net in ("CC1", "FDCAN1_TX"):
            assert by_net[net]["old_pass"] is True
            assert by_net[net]["new_class"] == "conservative_band"

    def test_old_approx_pad_root_cause_anchored(self):
        """旧口径对 U1.109 长条焊盘的半程低估锚定：min(w,h)/2=0.15 vs
        长轴半程 0.75；旧 need=0.425、中心距 0.673552 → 放行（E1 负对照
        同值）。"""
        text, _sha, parsed, _chains, batches = _chain_state()
        hist = json.loads((BATCH01 / "candidates.json").read_text(
            encoding="utf-8"))
        k1 = [p for p in hist["patches"]
              if p["patch_id"] == "P#LTDC_R7#F#S444#ch#S444#k1"][0]
        fidx = pr.build_foreign_index(parsed, set(batches["batch-01"]))
        ins = k1["text_ops"]["insert_segment"]
        ax, ay = ins["start"]
        bx, by = ins["end"]
        u109 = [p for plist in fidx["pads"].values() for p in plist
                if p["pad_id"] == "U1.109"]
        assert u109, "U1.109 不在 staging 解析 pad 集"
        p = u109[0]
        half = min(p["w_mm"], p["h_mm"]) / 2.0
        need = pr.CLEARANCE_MM + ins["width"] / 2.0 + half
        d = pr._point_seg_dist(p["x_mm"], p["y_mm"], ax, ay, bx, by)
        assert half == pytest.approx(0.15, abs=1e-12)   # min(w,h)/2 低估
        assert p["w_mm"] / 2.0 == pytest.approx(0.75)   # 长轴半程实值
        assert d == pytest.approx(0.673552, abs=1e-6)   # E1 负对照同值
        assert need == pytest.approx(0.425, abs=1e-9)
        assert d >= need - 1e-9                          # 旧口径放行（漏报）
