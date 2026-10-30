"""pcbflow.v4_1.regression -- G1.1 根因回归（本包核心；任务书 §3 E1）。

P3REVC-BATCH-01 事故原候选（LTDC_R7 倒角 vs U1.109 焊盘）必须被 v4_1
预检预测为违例，预测 clearance 与 kicad-cli 实测 0.1571mm 对拍（预注册
容差 |预测-实测| <= 0.01mm，如实登记）。

证据锚（盘上在案，只读）：

- out/v4-exec/p3-revc/per-net-batch/snapshot-pristine.kicad_pcb（板快照）；
- out/v4-exec/p3-revc/per-net-batch/batch-01/candidates.json（六网候选，
  LTDC_R7 patch=P#LTDC_R7#F#S444#ch#S444#k1）；
- out/v4-exec/p3-revc/per-net-batch/batch-01/drc-all.json（kicad-cli 判决：
  clearance 违例 U1.109 [FMC_BA1] vs LTDC_R7 段，间距 0.2000mm / 实际
  0.1571mm）；
- U1.109：roundrect 1.5x0.3 rratio 0.25（r=0.075），footprint U1 at
  (35, 22.9) 旋转 0，pad 局部 (12.675, 0.75) -> 板坐标 (47.675, 23.65)。

双路对拍：预检（路径 A+精确引擎）与 checker（路径 B+外切多边形）须同
判违例；交叉不一致=blocked 登记。

负对照（回归测试的牙齿）：P3 旧模型 pad=min(w,h)/2=0.15 对同一几何算出
中心距 0.360342-0.15-0.075=0.135... 实际旧预检放行是因为 0.360342 >=
0.2+0.15+0.075（中心距口径）；本模块复算旧模型判定=pass（证明旧模型漏
报、新模型拦截——同一几何、同 net class 口径）。
"""

from __future__ import annotations

from . import (CONSERVATIVE_BAND_MM, DECLARED_DATE, G11_TOLERANCE_MM,
               P3REVC_BATCH01_MEASURED_MM)
from .board_parse import parse_board_text
from .board_parse_alt import parse_board_text_alt
from .checker import (CheckerBlocked, IndependentGeometryChecker,
                      build_check_items)
from .netclasses import NetClassTable, netclass_table_from_kicad_pro
from .precheck import AdvisoryPrecheckV41, PrecheckBlocked, build_geom_items

__all__ = ["G11Case", "EMBEDDED_BATCH01_CASE", "run_g11", "load_g11_context"]

_G11_SCHEMA = "pcbflow.v4_1.g11-regression/1"

#: 冻结常量：P3REVC-BATCH-01 LTDC_R7 倒角候选（candidates.json 原值；
#: 盘上件缺失时以本常量运行——与盘上件对拍由 test 断言一致性）
EMBEDDED_BATCH01_CASE = {
    "patch_id": "P#LTDC_R7#F#S444#ch#S444#k1",
    "net": "LTDC_R7",
    "layer": "F.Cu",
    "width_mm": 0.15,
    "segment": [(48.1263, 23.15), (48.638432, 23.362132)],
    "obstacle_pad": {
        "pad_id": "U1.109", "shape": "roundrect",
        "net": "FMC_BA1", "x": 47.675, "y": 23.65, "w": 1.5, "h": 0.3,
        "rratio": 0.25, "rotation_deg": 0.0,
    },
    "kicad_measured_clearance_mm": P3REVC_BATCH01_MEASURED_MM,
    "kicad_required_clearance_mm": 0.2,
}


class G11Case:
    """G1.1 独立最小场景（不依赖盘上件：内嵌冻结几何 + 内嵌板文本）。"""

    BOARD_TEXT = """(kicad_pcb (version 20260206)
  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
  (footprint "LQFP-176_24x24mm_P0.5mm" (layer "F.Cu")
    (at 35 22.9)
    (property "Reference" "U1" (at 0 0) (layer "F.SilkS"))
    (pad "109" smd roundrect (at 12.675 0.75) (size 1.5 0.3)
      (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25)
      (net "FMC_BA1") (uuid "433d74c5-d012-47ff-a6b7-1005a6bafcfd"))
    (pad "110" smd roundrect (at 12.675 0.25) (size 1.5 0.3)
      (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25)
      (net "LTDC_R7") (uuid "c5fc7217-295d-4d5e-8930-c4dc35bbdfd7"))
  )
  (segment (start 46.925 23.4) (end 48.1263 23.15) (width 0.15)
    (layer "F.Cu") (net "LTDC_R7") (uuid "86d48edc-94a2-4c4f-bfe6-6c7474e1df69"))
  (segment (start 48.638432 23.362132) (end 49.9 23.89) (width 0.15)
    (layer "F.Cu") (net "LTDC_R7") (uuid "18118b74-63d9-448e-a853-5b8cc53c8c83"))
)
"""

    @classmethod
    def net_table(cls):
        from .netclasses import NetClass
        return NetClassTable(
            {"Default": NetClass("Default", 0.2, 0.15)},
            {}, [],
            "declared_defaults:G1.1 内嵌场景（对齐 Rev-C DRC 判决口径 "
            "0.2000mm；盘上 kicad_pro 实测载入见 load_g11_context）")

    @classmethod
    def run(cls, net_table=None):
        net_table = net_table or cls.net_table()
        parsed_a = parse_board_text(cls.BOARD_TEXT)
        parsed_b = parse_board_text_alt(cls.BOARD_TEXT)
        pre = AdvisoryPrecheckV41(build_geom_items(parsed_a), net_table)
        chk = IndependentGeometryChecker(build_check_items(parsed_b),
                                         net_table)
        (ax, ay), (bx, by) = EMBEDDED_BATCH01_CASE["segment"]
        w = EMBEDDED_BATCH01_CASE["width_mm"]
        net = EMBEDDED_BATCH01_CASE["net"]
        r_pre = pre.check_segment(net, EMBEDDED_BATCH01_CASE["layer"],
                                  w, ax, ay, bx, by)
        r_chk = chk.check_segment(net, EMBEDDED_BATCH01_CASE["layer"],
                                  w, ax, ay, bx, by)
        return {"precheck": r_pre, "checker": r_chk}


def _old_model_verdict(case):
    """负对照：P3 旧预检模型（pad=min(w,h)/2、中心距口径）复算。

    旧口径：中心线距 >= clearance + 双方半宽；pad 半宽=min(w,h)/2=0.15。
    返回 (old_pass, old_min_centerline_dist, old_need)。
    """
    import math
    (ax, ay), (bx, by) = case["segment"]
    px, py = case["obstacle_pad"]["x"], case["obstacle_pad"]["y"]
    half_pad = min(case["obstacle_pad"]["w"], case["obstacle_pad"]["h"]) / 2.0
    hw = case["width_mm"] / 2.0
    need = case["kicad_required_clearance_mm"] + hw + half_pad
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy
    t = ((px - ax) * vx + (py - ay) * vy) / l2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    d = math.hypot(px - (ax + t * vx), py - (ay + t * vy))
    return d >= need - 1e-9, round(d, 6), round(need, 6)


def run_g11(net_table=None, case=None, context_label="embedded"):
    """G1.1 回归主入口 -> canonical-ready 结果 dict。"""
    case = case or EMBEDDED_BATCH01_CASE
    res = G11Case.run(net_table) if case is EMBEDDED_BATCH01_CASE else None
    if res is None:
        raise ValueError("自定义 case 请经 load_g11_context 通道")
    r_pre, r_chk = res["precheck"], res["checker"]
    measured = case["kicad_measured_clearance_mm"]
    required = case["kicad_required_clearance_mm"]

    def _pick(viol_list, pad_id):
        for v in viol_list:
            if v["item_ref"] == pad_id:
                return v
        return None

    hit_pre = _pick(r_pre["violations"], "U1.109")
    hit_chk = _pick(r_chk["violations"], "U1.109")
    pred_pre = hit_pre["pred_clearance_mm"] if hit_pre else None
    pred_chk = hit_chk["pred_clearance_mm"] if hit_chk else None
    old_pass, old_d, old_need = _old_model_verdict(case)
    diff = None if pred_pre is None else round(abs(pred_pre - measured), 6)
    diff_chk = None if pred_chk is None else round(abs(pred_chk - measured), 6)
    cross_agree = (r_pre["verdict"] == r_chk["verdict"] == "violation")
    return {
        "schema": _G11_SCHEMA,
        "declared_date": DECLARED_DATE,
        "gate": "G1.1",
        "context": context_label,
        "case": {
            "patch_id": case["patch_id"],
            "net": case["net"],
            "layer": case["layer"],
            "segment_mm": [list(p) for p in case["segment"]],
            "width_mm": case["width_mm"],
            "obstacle": dict(case["obstacle_pad"]),
        },
        "authority": {
            "kicad_cli_measured_clearance_mm": measured,
            "kicad_cli_required_clearance_mm": required,
            "source": "out/v4-exec/p3-revc/per-net-batch/batch-01/drc-all."
                      "json violations[type=clearance]（LTDC_R7 段 vs "
                      "U1.109 [FMC_BA1]）+ rollback.json §diagnosis",
        },
        "precheck": {
            "engine": r_pre["engine"],
            "verdict": r_pre["verdict"],
            "pred_clearance_mm_vs_U1_109": pred_pre,
            "abs_diff_vs_measured_mm": diff,
            "tolerance_mm": G11_TOLERANCE_MM,
            "tolerance_pass": diff is not None and diff <= G11_TOLERANCE_MM,
            "full_violations": r_pre["violations"],
        },
        "checker": {
            "engine": r_chk["engine"],
            "verdict": r_chk["verdict"],
            "pred_clearance_mm_vs_U1_109": pred_chk,
            "abs_diff_vs_measured_mm": diff_chk,
            "note": "外切多边形超集：pred 系统性略低于精确值（超集偏差"
                    "上界 ~0.0004mm）",
        },
        "negative_control_old_p3_model": {
            "model": "pad=min(w,h)/2 中心距口径（pcbflow/p3_revc_staging."
                     "py L491 旧实现，只读参照）",
            "old_verdict_pass": old_pass,
            "old_min_centerline_dist_mm": old_d,
            "old_need_mm": old_need,
            "interpretation": "旧模型放行（漏报）与 kicad-cli 拦截冲突"
                             "= P3REVC-BATCH-01 事故；新模型拦截=根因回归"
                             " pass",
        },
        "cross_check": {
            "precheck_vs_checker_agree_on_violation": cross_agree,
            "disagreement": None if cross_agree else {
                "precheck": r_pre["verdict"], "checker": r_chk["verdict"],
                "status": "blocked",
            },
        },
        "conservative_band_mm": CONSERVATIVE_BAND_MM,
        "gate_verdict": "pass" if (
            hit_pre is not None and cross_agree and diff is not None
            and diff <= G11_TOLERANCE_MM and old_pass) else (
            "blocked" if not cross_agree else "fail"),
    }


def load_g11_context(repo_root):
    """盘上证据装载（只读）：快照板文本 + 候选 + DRC 实测值 + kicad_pro。

    返回 (board_text, candidates, measured_mm, required_mm, net_table)；
    盘上件缺失 -> (None, ...) 由调用方决定降级路径（测试侧 skipif）。
    """
    import json
    from pathlib import Path
    root = Path(repo_root).resolve()
    snap = root / "out/v4-exec/p3-revc/per-net-batch/snapshot-pristine.kicad_pcb"
    cand_p = root / "out/v4-exec/p3-revc/per-net-batch/batch-01/candidates.json"
    drc_p = root / "out/v4-exec/p3-revc/per-net-batch/batch-01/drc-all.json"
    pro_p = root.parent.parent / (
        "design/coreboard/kicad/stm32h743-coreboard-revc/"
        "stm32h743-coreboard-revc.kicad_pro")
    if not (snap.is_file() and cand_p.is_file() and drc_p.is_file()):
        return None
    board_text = snap.read_text(encoding="utf-8")
    candidates = json.loads(cand_p.read_text(encoding="utf-8"))
    drc = json.loads(drc_p.read_text(encoding="utf-8"))
    measured = None
    required = None
    for v in drc.get("violations", []):
        items = v.get("items", [])
        if v.get("type") == "clearance" and any(
                "LTDC_R7" in str(i.get("description", ""))
                for i in items) and any("U1" in str(i.get("description", ""))
                                        for i in items):
            txt = v.get("description", "")
            import re
            m_num = re.findall(r"([0-9.]+)\s*mm", txt)
            if len(m_num) >= 2:
                required = float(m_num[0])
                measured = float(m_num[1])
            break
    net_table = None
    netclass_status = "not_available"
    if pro_p.is_file():
        try:
            pro_obj = json.loads(pro_p.read_text(encoding="utf-8"))
            net_table = netclass_table_from_kicad_pro(pro_obj)
            if net_table is not None:
                netclass_status = "loaded_kicad_pro:%s" % pro_p.name
        except Exception as exc:  # noqa: BLE001 - fail-closed 登记不吞
            netclass_status = "kicad_pro_load_failed:%s" % exc
    if net_table is None:
        net_table = G11Case.net_table()
        netclass_status += ";fallback=declared_defaults(G1.1 内嵌口径 0.2)"
    return {
        "board_text": board_text,
        "candidates": candidates,
        "measured_mm": measured,
        "required_mm": required,
        "net_table": net_table,
        "netclass_status": netclass_status,
        "board_parse_a": parse_board_text(board_text),
        "board_parse_b": parse_board_text_alt(board_text),
    }
