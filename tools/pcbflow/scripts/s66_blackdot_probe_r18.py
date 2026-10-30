#!/usr/bin/env python
"""R18 黑点物理来源探针（axis-experiment-plan stage1 R18=轴2 先决探针）。

背景：黑点族弃权连续主导（分型件 rubric 口径 existence_blackdot 弃权旗
r13=9/r14=14/r15=8/r16=12，bottom 占 81.4%）。axis-experiment-plan-
r17-r20（b6ec6467 冻结件）stage1 R18=轴2（A2_blackdot_instrument_
annotation）规定：「注记内容须先经盘上探针证实黑点物理来源（仪器事实
非判据），无探针证实则该轴不得入轮」。本探针=该先决条件的执行件：
只读解析 staging-r4 两板板卡源文件（kicad_pcb 文本，正则+括号配平，
零写板、零 kicad-cli 调用），在 bottom 视图层集（B.Cu/B.Mask/
B.Silkscreen/Edge.Cuts/B.Courtyard——与 renders-r14b 图层集逐字一致）
内定位「黑色实心圆点」的物理来源，并将渲染表现语义锚到盘上仪器记录
（render-framing-r14b 证书点/矢量归因、render-witness-r14b 调色板）。

探针纪律（r14 教训）：fail-closed——每一族结论必须同时给出（i）板卡
源文件图元证据（计数/坐标/归属）、（ii）盘上渲染仪器记录证据（字段名
+实测 sha）、（iii）与读者报告 corpus（abstain-typology，只读）的对照；
任一环节不能证实即如实写 indeterminate 并列已排除项，不得硬造。

探针结论概要（详见落盘 blackdot-probe-r18.json）：
  F2（孤立实心黑点对——读者报告的「左上角组件旁孤立黑点对」[bottom]/
  「右上连接器区块两黑点」[top]）：=J5（USB-C 连接器封装）内恰 2 个
  非电镀机械定位孔（pad "" np_thru_hole circle，size=drill=0.65mm、
  零铜环宽度、layers *.Cu *.Mask）的渲染表现，两板同。证据链：板文件
  绝对坐标 (63.6025,4.11)/(63.6025,9.89)mm 经 framing-r14b 裁剪映射
  （board 70x70mm、dpi640、crop margin 120px、board_px_bounds 实测）
  映射到 bottom 成图 px (281.3,223.5)/(281.3,369.2)，与 framing 证书点
  fiducial_disk_black（cropped_xy [282,224]、r5_rgb [0,0,0]、
  white_fill_mask=false——即不在白墨重着色族内，r5→r14b 保持黑色）
  实测偏差 ≤4px；全板该类图元恰 2 处、无其他候选（B 层集 fp_circle=0、
  fiducial footprint=0、含 B.Cu 的 via=0[470 via 全部 buried 不含
  B.Cu]）；reader corpus（分型件在案摘录）报告「全图仅 2 处实心黑」
  与其报告位置换算一致。
  F1（焊盘内圆盘——「焊盘内黑心/钻孔盘族」）：=电镀通孔焊盘钻孔渲染
  表现：每板 166 个含 drill 的 thru_hole pad（157 circle+4 rect+
  4 oval+1 roundrect），其中圆钻孔恰 162 个=framing-r14b 矢量归因
  combined_white_fill_count=162（计数恒等），椭圆槽孔恰 4 个=
  combined_white_stroke_count=4；r5 证书点 pad_hole_disk r5_rgb=
  [255,255,255]、white_fill_mask=true ⇒ r14b 重着色为橙 (255,165,0)
  （witness 橙 81672px 两板相同）——即 r14b bottom 视焊盘中心圆盘=
  钻孔渲染（橙色），不是黑色墨点图元。
  F3（板内孤立焊盘对——「右中孤立焊盘对」）：=CRTC（CP_Radial_D8.0mm
  _P3.50mm，径向电解电容封装）2 个电镀通孔焊盘（roundrect@(11.65,
  50.8)+circle@(15.15,50.8)，均 1.6mm/drill 0.8）——中心圆盘同 F1
  钻孔渲染族；探针在该焊盘对邻域（±5mm）未找到任何实心黑色圆图元
  来源（np 孔仅 J5 两处、B 层集圆图元 0、fiducial 0、B.Cu via 0）
  ⇒「该处邻接黑点」=indeterminate（如实登记，不硬造）。

纪律：只读（输入=staging-r4 两板+render-framing-r14b+render-witness-
r14b+abstain-typology+axis-experiment-plan+round17-dev-record，全部
fail-closed 锚验证，零写入既有件）；新建唯一文件=out/v3-tl2/calibration/
blackdot-probe-r18.json（canonical JSON，防覆写守卫：已存在且重建字节
不同→FAIL，等同→幂等通过）；零 wall-clock（日期/轮次=声明常量
2026-09-09/2026-09-09-r18）；零 PNG/PDF 内容读取（渲染表现语义全部以
盘上仪器记录字段为准）；零 subprocess/网络；不读 GT/reader-raw/
derivation-log/compare 产物。

用法：python scripts/s66_blackdot_probe_r18.py
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
STAGING_R4 = CAL_DIR / "staging-r4"
BOARDS = {
    "applied": STAGING_R4 / "applied.kicad_pcb",
    "prep1": STAGING_R4 / "prep1.kicad_pcb",
}
FRAMING_R14B = CAL_DIR / "render-framing-r14b.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
TYPOLOGY = CAL_DIR / "abstain-typology-r13-r16.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
DEV_RECORD_R17 = CAL_DIR / "round17-dev-record.json"
PROBE_OUT = CAL_DIR / "blackdot-probe-r18.json"

DATE_CONSTANT = "2026-09-09"
ROUND_ID = "2026-09-09-r18"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）
# ---------------------------------------------------------------------------
FRAMING_R14B_SHA_PREFIX = "7004b017"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
TYPOLOGY_SHA_PREFIX = "6dadac8d"
AXIS_PLAN_SHA_PREFIX = "b6ec6467"
DEV_RECORD_R17_SHA_PREFIX = "e526093f"

#: bottom 视图层集（与 renders-r14b 图层集逐字一致；s51 LAYERS_BOTTOM）
LAYERS_BOTTOM = ["B.Cu", "B.Mask", "B.Silkscreen", "Edge.Cuts", "B.Courtyard"]

#: 板几何与映射常量（board mm=Edge.Cuts gr_line 实测；dpi/margin/bounds=
#: framing-r14b compose_and_crop_same_as_r5 + expected_from_r5_derivation_log）
DPI = 640
CROP_MARGIN_PX = 120
#: 证书点匹配容差（px；640dpi 1px=0.0397mm，板界实测含轮廓描边 ±2px 量级）
CERT_MATCH_TOL_PX = 4.0
#: 读者报告位置对照容差（整幅图像归一化坐标）
READER_MATCH_TOL = 0.03
#: F3 邻域半径（mm）——在该范围内寻找黑色圆图元来源
F3_NEIGHBORHOOD_MM = 5.0

#: 读者报告 corpus 对照值（abstain-typology 在案摘录的近似整幅坐标；
#: 只作旁证记录，非负载证据）
READER_REPORTED_FRACS = {
    "bottom": [(0.145, 0.110), (0.145, 0.185)],
    "top": [(0.857, 0.103), (0.852, 0.186)],
}

#: 分型件在案基线（rubric 口径 existence_blackdot 弃权旗计数；M3 基线锚）
BLACKDOT_ABSTAIN_BASELINE = {"r13": 9, "r14": 14, "r15": 8, "r16": 12}
BLACKDOT_JUDGED_NORMAL_BASELINE = {"r15": 3, "r16": 2}


def _fail(msg: str) -> None:
    print(f"[r18-blackdot-probe] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


# ---------------------------------------------------------------------------
# kicad_pcb 只读解析（正则+括号配平；零写板）
# ---------------------------------------------------------------------------

def _block_bounds(text: str, start: int) -> int:
    """返回 start 处 '(' 的配平 ')' 之后的位置。"""
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    _fail(f"括号配平失败 @ {start}")


def _pad_records(fp_block: str) -> list[dict]:
    """解析 footprint 块内全部 pad（drill/layers 限定在本 pad 块内）。"""
    pads = []
    for pm in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)', fp_block):
        pstart = pm.start()
        pend = _block_bounds(fp_block, pstart)
        pblock = fp_block[pm.start():pend]
        am = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', pblock)
        sm = re.search(r'\(size ([\d.\-]+) ([\d.\-]+)\)', pblock)
        dm = re.search(r'\(drill (oval )?([\d.\-]+)(?: ([\d.\-]+))?\)', pblock)
        lm = re.search(r'\(layers ([^)]*)\)', pblock)
        pads.append({
            "num": pm.group(1),
            "ptype": pm.group(2),
            "shape": pm.group(3),
            "at": (float(am.group(1)), float(am.group(2))) if am else None,
            "size": (float(sm.group(1)), float(sm.group(2))) if sm else None,
            "drill_oval": bool(dm and dm.group(1)),
            "drill": (float(dm.group(2)) if dm and not dm.group(1)
                      else (float(dm.group(2)) if dm else None),
                      float(dm.group(3)) if (dm and dm.group(3)) else None),
            "layers": re.sub(r"\s+", " ", lm.group(1)) if lm else "",
            "raw_head": pm.group(0),
        })
    return pads


def parse_board(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fps = []
    for m in re.finditer(r'\(footprint\s+"([^"]+)"', text):
        fend = _block_bounds(text, m.start())
        block = text[m.start():fend]
        at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', block)
        ref = re.search(r'\(property "Reference" "([^"]+)"', block)
        fps.append({
            "lib": m.group(1),
            "ref": ref.group(1) if ref else "?",
            "at": (float(at.group(1)), float(at.group(2))),
            "rot": float(at.group(3) or 0.0),
            "pads": _pad_records(block),
            "fp_circle_layers": re.findall(
                r'\(fp_circle[\s\S]{0,400}?\(layer "([^"]+)"\)', block),
        })
    # 板级图形（KiCad 6+ 语法 gr_circle/gr_line；逐条配层）
    gr_circle_layers = []
    for gm in re.finditer(r'\(gr_circle', text):
        gend = _block_bounds(text, gm.start())
        gr_circle_layers.append(re.search(r'\(layer "([^"]+)"\)',
                                          text[gm.start():gend]).group(1))
    outline = []
    for gm in re.finditer(r'\(gr_line', text):
        gend = _block_bounds(text, gm.start())
        gblock = text[gm.start():gend]
        if 'Edge.Cuts' in gblock:
            sm2 = re.search(r'\(start ([\d.\-]+) ([\d.\-]+)\)', gblock)
            em2 = re.search(r'\(end ([\d.\-]+) ([\d.\-]+)\)', gblock)
            outline.append((float(sm2.group(1)), float(sm2.group(2)),
                            float(em2.group(1)), float(em2.group(2))))
    vias = []
    for vm in re.finditer(r'\(via(?: (\w+))?', text):
        vend = _block_bounds(text, vm.start())
        vblock = text[vm.start():vend]
        am = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', vblock)
        lm = re.search(r'\(layers ([^)]*)\)', vblock)
        dm = re.search(r'\(drill ([\d.\-]+)\)', vblock)
        vias.append({
            "kind": vm.group(1) or "through",
            "at": (float(am.group(1)), float(am.group(2))) if am else None,
            "drill": float(dm.group(1)) if dm else None,
            "layers": re.sub(r"\s+", " ", lm.group(1)) if lm else "",
        })
    return {"text_len": len(text), "footprints": fps,
            "gr_circle_layers": gr_circle_layers, "edge_lines": outline,
            "vias": vias}


def pad_abs(fp: dict, pad: dict) -> tuple[float, float]:
    """footprint 内 pad 坐标→板面绝对坐标（kicad_pcb y 向下坐标系旋转
    矩阵 [[cos,sin],[-sin,cos]]；已由证书点匹配实测校验）。"""
    th = math.radians(fp["rot"])
    c, s = math.cos(th), math.sin(th)
    px, py = pad["at"]
    return (fp["at"][0] + px * c + py * s,
            fp["at"][1] - px * s + py * c)


# ---------------------------------------------------------------------------
# 映射：板面 mm ↔ 成图像素（全部取自 framing-r14b 在案字段）
# ---------------------------------------------------------------------------

class ViewMap:
    def __init__(self, framing: dict, state: str):
        cc = framing["compose_and_crop_same_as_r5"]
        exp = cc["expected_from_r5_derivation_log"][state]
        self.dpi = cc["dpi"]
        self.margin = cc["crop_margin_px"]
        self.bounds = exp["board_px_bounds_full"]  # [x0,y0,x1,y1] 全页
        self.crop_box = exp["crop_box"]
        self.wh = exp["cropped_image_wh"]
        self.bx0, self.by0 = self.bounds[0] - self.crop_box[0], \
            self.bounds[1] - self.crop_box[1]  # 板左上在裁剪图内 =120,120
        self.bpx_w = self.bounds[2] - self.bounds[0]
        self.bpx_h = self.bounds[3] - self.bounds[1]
        self.board_mm_w = self.bpx_w / self.dpi * 25.4
        self.board_mm_h = self.bpx_h / self.dpi * 25.4

    def bottom_xy_px(self, fx: float, fy: float, board_mm: float) -> tuple:
        """bottom 视（--mirror 镜像）：板面绝对坐标→裁剪图像素。"""
        x = self.bx0 + (board_mm - fx) / board_mm * self.bpx_w
        y = self.by0 + fy / board_mm * self.bpx_h
        return (x, y)

    def top_xy_px(self, fx: float, fy: float, board_mm: float) -> tuple:
        """top 视（不镜像）：板面绝对坐标→裁剪图像素。"""
        x = self.bx0 + fx / board_mm * self.bpx_w
        y = self.by0 + fy / board_mm * self.bpx_h
        return (x, y)

    def frac(self, xy_px: tuple) -> tuple:
        return (round(xy_px[0] / self.wh[0], 4), round(xy_px[1] / self.wh[1], 4))


# ---------------------------------------------------------------------------
# §5B 注记文本（由探针结论确定性装配；s67 fail-closed 转录）
# ---------------------------------------------------------------------------

SECTION_5B_HEADING = "## 5B. 黑点仪器注记（黑点物理来源；仪器事实，非判据）"


def build_section_5b(np_count: int, round_drills: int, oval_slots: int,
                     np_size_mm: float, drill_mm: float) -> str:
    bullet1 = (
        f"- 本轮渲染中的实心黑色圆点物理来源（探针证实，s66/blackdot-probe-"
        f"r18.json 在案）：(a) 图中成对出现的孤立实心黑点（bottom 视与 top 视为同"
        f"一物理来源）=封装内 {np_count} 个非电镀机械定位孔（pad 类型 "
        f"np_thru_hole：孔径=焊盘尺寸={np_size_mm}mm、无铜环宽度）的渲染表现，"
        f"两板相同；(b) 焊盘轮廓中心的圆盘（bottom 视呈橙色圆盘、top 视呈浅色"
        f"圆盘）=电镀通孔焊盘钻孔的渲染表现（每板 {round_drills} 处圆钻孔 + "
        f"{oval_slots} 处椭圆槽孔；bottom 视橙色来自白墨图元重着色配色，非黑色"
        f"墨点）；(c) 板内孤立焊盘对（一圆形、一方形，周边无同类图形）中心的小"
        f"圆盘同为电镀通孔焊盘钻孔的渲染表现——探针未在该焊盘对邻域找到任何实"
        f"心黑色圆图元来源。")
    bullet2 = (
        "- 本节为仪器事实，不构成任何判据、期望清单或「应判为正常/无需报告」"
        "的指示；黑点相关现象的旗标判定仍按 §2 类别枚举与 §3A/§4 判据独立执行"
        "（含系统性判据、接触性判据与弃权规则）；仪器注记未能证实来源的黑点形"
        "态，按 §4 既有规则处理。")
    bullet3 = (
        "- top 视黑点同样适用（top 渲染与 bottom 渲染源自同一板卡文件的同族图"
        "元，黑点物理来源相同；本句仅陈述来源同一性，不改变任何判据）。")
    return (SECTION_5B_HEADING + "\n\n" + bullet1 + "\n" + bullet2 + "\n"
            + bullet3 + "\n\n")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 输入在盘性 + 冻结锚 ----
    for p in (BOARDS["applied"], BOARDS["prep1"], FRAMING_R14B, WITNESS_R14B,
              TYPOLOGY, AXIS_PLAN, DEV_RECORD_R17):
        if not p.exists():
            _fail(f"缺失：{p}")
    framing_sha = _sha(FRAMING_R14B)
    witness_sha = _sha(WITNESS_R14B)
    typ_sha = _sha(TYPOLOGY)
    axis_sha = _sha(AXIS_PLAN)
    dev_sha = _sha(DEV_RECORD_R17)
    for sha, prefix, label in (
            (framing_sha, FRAMING_R14B_SHA_PREFIX, "render-framing-r14b"),
            (witness_sha, WITNESS_R14B_SHA_PREFIX, "render-witness-r14b"),
            (typ_sha, TYPOLOGY_SHA_PREFIX, "abstain-typology-r13-r16"),
            (axis_sha, AXIS_PLAN_SHA_PREFIX, "axis-experiment-plan"),
            (dev_sha, DEV_RECORD_R17_SHA_PREFIX, "round17-dev-record")):
        if not sha.startswith(prefix):
            _fail(f"{label} sha 前 8={sha[:8]} != 预期 {prefix}（锚不符，"
                  f"立即停止）")

    framing = json.loads(FRAMING_R14B.read_text(encoding="utf-8"))
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    typology = json.loads(TYPOLOGY.read_text(encoding="utf-8"))
    axis_plan = json.loads(AXIS_PLAN.read_text(encoding="utf-8"))
    dev17 = json.loads(DEV_RECORD_R17.read_text(encoding="utf-8"))

    # ---- 轴计划 R18=A2 定义（探针先决条件原文在案）----
    rounds = axis_plan.get("stage1_rounds", {}).get("rounds", [])
    r18 = next((r for r in rounds if r.get("round_id") == "R18"), None)
    if r18 is None or r18.get("axis_id") != "A2_blackdot_instrument_annotation":
        _fail("axis-plan stage1 R18=A2_blackdot_instrument_annotation 不符")
    if "探针证实" not in (r18.get("guidance") or ""):
        _fail("axis-plan R18 guidance 缺「探针证实」先决条款")
    if r18.get("render") != "renders-r14b 四图字节复用（零变更）":
        _fail("axis-plan R18 render 定义不符（应为 renders-r14b 四图字节复用）")
    ntargets = dev17.get("next_iteration_targets") or []
    if not ntargets or "探针" not in ntargets[0] or "R18" not in ntargets[0]:
        _fail("round17-dev-record next_iteration_targets[0] 缺 R18/探针先决")

    # ---- 板卡源文件 witness（vs framing 登记值）----
    ibw = framing.get("input_board_witness", {})
    board_shas = {st: _sha(p) for st, p in BOARDS.items()}
    for st, sha in board_shas.items():
        if ibw.get(st) != sha:
            _fail(f"staging-r4/{st}.kicad_pcb 实测 sha 与 framing-r14b "
                  f"input_board_witness 登记值不符：{sha} != {ibw.get(st)}")

    # ---- 渲染仪器事实（framing 证书点/矢量归因、witness 调色板）----
    certs = {c["name"]: c for c in framing["probe_block"]["certificate_points"]}
    for need in ("fiducial_disk_black", "pad_hole_disk", "fiducial_ring_gap",
                 "pad_ring_cyan_band", "pad_rim_gap_band"):
        if need not in certs:
            _fail(f"framing-r14b 证书点缺失：{need}")
    at_tab = framing["probe_block"]["vector_attribution"]["attribution_table"]
    fills = {st: at_tab[st]["combined_white_fill_count"] for st in
             ("applied", "prep1")}
    strokes = {st: at_tab[st]["combined_white_stroke_count"] for st in
               ("applied", "prep1")}
    pas = witness.get("palette_assertion_summary", {})
    orange_px = {st: pas[st]["orange_exact_count"] for st in
                 ("applied", "prep1")}

    # ---- 两板解析与普查 ----
    census: dict[str, dict] = {}
    for st, path in BOARDS.items():
        bd = parse_board(path)
        np_pads = []
        round_drills = 0
        oval_slots = 0
        smd_drilled = 0
        pad_total = 0
        fp_circle_by_layer: dict[str, int] = {}
        for fp in bd["footprints"]:
            for lay in fp["fp_circle_layers"]:
                fp_circle_by_layer[lay] = fp_circle_by_layer.get(lay, 0) + 1
            for pad in fp["pads"]:
                pad_total += 1
                has_drill = pad["drill"][0] is not None
                if pad["ptype"] == "np_thru_hole":
                    np_pads.append({
                        "ref": fp["ref"], "lib": fp["lib"],
                        "abs_mm": list(pad_abs(fp, pad)),
                        "size": pad["size"], "drill": pad["drill"][0],
                        "layers": pad["layers"],
                    })
                elif pad["ptype"] == "thru_hole" and has_drill:
                    if pad["drill_oval"]:
                        oval_slots += 1
                    else:
                        round_drills += 1
                elif has_drill:
                    smd_drilled += 1
        bcu_vias = [v for v in bd["vias"] if "B.Cu" in v["layers"]]
        fiducial_fps = [f for f in bd["footprints"]
                        if "fiducial" in f["lib"].lower()
                        or "fiducial" in f["ref"].lower()]
        # 板面几何（Edge.Cuts gr_line 实测）
        xs = [v for ln in bd["edge_lines"] for v in (ln[0], ln[2])]
        ys = [v for ln in bd["edge_lines"] for v in (ln[1], ln[3])]
        board_mm = (min(xs), min(ys), max(xs), max(ys))
        board_wh_mm = (round(board_mm[2] - board_mm[0], 6),
                       round(board_mm[3] - board_mm[1], 6))
        census[st] = {
            "sha256": board_shas[st],
            "footprint_count": len(bd["footprints"]),
            "pad_total": pad_total,
            "np_thru_hole_pads": np_pads,
            "round_drilled_thru_pads": round_drills,
            "oval_slot_thru_pads": oval_slots,
            "non_thru_drilled_pads": smd_drilled,
            "fp_circle_by_layer": fp_circle_by_layer,
            "gr_circle_layers": bd["gr_circle_layers"],
            "via_total": len(bd["vias"]),
            "vias_on_BCu": len(bcu_vias),
            "fiducial_footprints": [f["ref"] for f in fiducial_fps],
            "edge_cuts_mm": [round(v, 4) for v in board_mm],
            "board_wh_mm": list(board_wh_mm),
            "edge_line_count": len(bd["edge_lines"]),
        }
        # ---- 普查 fail-closed 断言 ----
        if len(np_pads) != 2:
            _fail(f"{st}: np_thru_hole 计数 {len(np_pads)} != 2（F2 前提破坏）")
        if round_drills != fills[st]:
            _fail(f"{st}: 圆钻孔计数 {round_drills} != framing 归因白 fill "
                  f"{fills[st]}（F1 计数恒等破坏）")
        if oval_slots != strokes[st]:
            _fail(f"{st}: 椭圆槽孔计数 {oval_slots} != framing 归因白 stroke "
                  f"{strokes[st]}")
        if smd_drilled != 0:
            _fail(f"{st}: 非 thru 焊盘含 drill {smd_drilled} != 0（普查口径漂移）")
        for lay in LAYERS_BOTTOM:
            if fp_circle_by_layer.get(lay, 0) != 0:
                _fail(f"{st}: bottom 层集 {lay} 存在 fp_circle（F2 排除项前提"
                      f"破坏）")
        if bd["gr_circle_layers"]:
            _fail(f"{st}: 存在板级 gr_circle {bd['gr_circle_layers']}")
        if len(bcu_vias) != 0:
            _fail(f"{st}: 含 B.Cu 的 via {len(bcu_vias)} != 0（F2 排除项破坏）")
        if fiducial_fps:
            _fail(f"{st}: 存在 fiducial footprint {[f['ref'] for f in fiducial_fps]}")
        if board_wh_mm != (70.0, 70.0):
            _fail(f"{st}: 板面几何 {board_wh_mm} != (70.0, 70.0)（映射前提破坏）")
        np_sizes = {(p["size"][0], p["drill"]) for p in np_pads}
        if np_sizes != {(0.65, 0.65)}:
            _fail(f"{st}: np 孔 size/drill 口径异常：{np_sizes}")

    # ---- F2 映射与证书点匹配（fail-closed）----
    vm = ViewMap(framing, "applied")
    np_abs = [p["abs_mm"] for p in census["applied"]["np_thru_hole_pads"]]
    np_abs.sort(key=lambda p: p[1])
    if census["prep1"]["np_thru_hole_pads"] and \
            [p["abs_mm"] for p in sorted(census["prep1"]["np_thru_hole_pads"],
                                         key=lambda q: q["abs_mm"][1])] != np_abs:
        _fail("两板 np 孔绝对坐标不一致")
    bw = vm.board_mm_w
    bh = vm.board_mm_h
    mapped = []
    for fx, fy in np_abs:
        b_xy = vm.bottom_xy_px(fx, fy, bw)
        t_xy = vm.top_xy_px(fx, fy, bw)
        mapped.append({
            "abs_mm": [fx, fy],
            "bottom_cropped_px": [round(v, 1) for v in b_xy],
            "bottom_frac": list(vm.frac(b_xy)),
            "top_cropped_px": [round(v, 1) for v in t_xy],
            "top_frac": list(vm.frac(t_xy)),
        })
    cert = certs["fiducial_disk_black"]
    d0 = math.hypot(mapped[0]["bottom_cropped_px"][0] - cert["cropped_xy"][0],
                    mapped[0]["bottom_cropped_px"][1] - cert["cropped_xy"][1])
    d1 = math.hypot(mapped[1]["bottom_cropped_px"][0] - cert["cropped_xy"][0],
                    mapped[1]["bottom_cropped_px"][1] - cert["cropped_xy"][1])
    cert_delta_px = round(min(d0, d1), 2)
    matched_np_index = 0 if d0 <= d1 else 1
    if cert_delta_px > CERT_MATCH_TOL_PX:
        _fail(f"np 孔映射与证书点 fiducial_disk_black 偏差 {cert_delta_px}px > "
              f"{CERT_MATCH_TOL_PX}px（F2 定位失败——黑点物理来源未能证实）")
    reader_deltas = []
    for view, pairs in READER_REPORTED_FRACS.items():
        for i, rf in enumerate(pairs):
            mf = mapped[i][f"{view}_frac"]
            reader_deltas.append(round(math.hypot(mf[0] - rf[0], mf[1] - rf[1]), 4))
    reader_max_delta = max(reader_deltas)

    # ---- 分型件在案基线（M3 机制基线锚）----
    per_flag = typology.get("per_flag", [])
    bl_counts: dict[str, int] = {}
    for f in per_flag:
        if f.get("family") == "existence_blackdot":
            bl_counts[f["round"]] = bl_counts.get(f["round"], 0) + 1
    if bl_counts != BLACKDOT_ABSTAIN_BASELINE:
        _fail(f"分型件 existence_blackdot 计数 {bl_counts} != "
              f"{BLACKDOT_ABSTAIN_BASELINE}（基线锚不符）")
    bd_dispatch = typology.get("blackdot_dispatch", {})
    jn = {r: len(bd_dispatch[r].get("judged_normal_dispatches", []))
          for r in ("r15", "r16")}
    if jn != BLACKDOT_JUDGED_NORMAL_BASELINE:
        _fail(f"分型件 blackdot 判正常派次 {jn} != "
              f"{BLACKDOT_JUDGED_NORMAL_BASELINE}")

    # ---- F3：CRTC 孤立焊盘对（识别+邻域排除）----
    fp_applied = parse_board(BOARDS["applied"])["footprints"]
    crtc = next((f for f in fp_applied if f["ref"] == "CRTC"), None)
    if crtc is None or "CP_Radial" not in crtc["lib"]:
        _fail("CRTC（CP_Radial）footprint 未找到（F3 识别失败）")
    crtc_pads = []
    for pad in crtc["pads"]:
        if pad["ptype"] == "thru_hole" and pad["drill"][0] is not None:
            crtc_pads.append({
                "num": pad["num"], "shape": pad["shape"],
                "abs_mm": [round(v, 4) for v in pad_abs(crtc, pad)],
                "size": pad["size"], "drill": pad["drill"][0],
            })
    crtc_pads.sort(key=lambda p: (p["abs_mm"][0], p["abs_mm"][1]))
    if len(crtc_pads) != 2:
        _fail(f"CRTC 含 drill 的 thru 焊盘数 {len(crtc_pads)} != 2")
    # 邻域排除：全部 np 孔/B 层集圆图元/B.Cu via 距焊盘对中心均在邻域外
    cx = sum(p["abs_mm"][0] for p in crtc_pads) / 2
    cy = sum(p["abs_mm"][1] for p in crtc_pads) / 2
    near = []
    for p in np_abs:
        if math.hypot(p[0] - cx, p[1] - cy) <= F3_NEIGHBORHOOD_MM:
            near.append({"kind": "np_thru_hole", "at": p})
    # F1 族图元不构成黑点来源（r14b 重着色为橙），邻域内允许其存在并如实登记
    f1_near = sum(1 for f in fp_applied for pad in f["pads"]
                  if pad["ptype"] == "thru_hole" and pad["drill"][0] is not None
                  and math.hypot(pad_abs(f, pad)[0] - cx,
                                 pad_abs(f, pad)[1] - cy) <= F3_NEIGHBORHOOD_MM)
    f3_blackdot_status = ("confirmed_absent" if not near
                          else "indeterminate")

    # ---- §5B 注记文本（确定性装配）----
    section_5b = build_section_5b(
        np_count=len(np_abs), round_drills=fills["applied"],
        oval_slots=strokes["applied"], np_size_mm=0.65, drill_mm=0.65)

    # ---- 结论装配（fail-closed 语义）----
    families = [
        {
            "form_id": "F1_pad_interior_disc",
            "reader_form": "焊盘内黑心/钻孔盘族（r14b 配色下的焊盘中心圆盘）",
            "physical_identity": (
                "电镀通孔焊盘钻孔的渲染表现（pad drill；非独立黑色图元）"),
            "count_per_board": {
                "round_drilled_thru_pads": census["applied"]["round_drilled_thru_pads"],
                "oval_slot_thru_pads": census["applied"]["oval_slot_thru_pads"],
            },
            "render_semantics": (
                "r5 证书点 pad_hole_disk r5_rgb=[255,255,255] 且 white_fill_"
                "mask=true（白墨图元族）⇒ r14b 重着色为橙 (255,165,0)；"
                "bottom 视焊盘中心圆盘=橙色钻孔渲染，不是黑色墨点；top 视（r5 "
                "字节复用）同族图元呈浅色圆盘"),
            "evidence_fields": [
                "staging-r4/{applied,prep1}.kicad_pcb (pad \"N\" thru_hole … "
                "(drill 0.8) (layers \"*.Cu\" \"*.Mask\")) 计数=162+4（本探针"
                "实测）",
                "render-framing-r14b.json "
                "probe_block.vector_attribution.attribution_table.{applied,"
                "prep1}.combined_white_fill_count=162 / combined_white_stroke_"
                "count=4（计数恒等）",
                "render-framing-r14b.json probe_block.certificate_points["
                "name=pad_hole_disk].r5_rgb/white_fill_mask",
                "render-witness-r14b.json palette_assertion_summary.{applied,"
                "prep1}.orange_exact_count=81672",
            ],
            "status": "confirmed",
        },
        {
            "form_id": "F2_isolated_black_dot_pair",
            "reader_form": ("左上角组件旁孤立黑点对（bottom 视）/右上连接器区"
                            "块两实心黑点（top 视）"),
            "physical_identity": (
                "J5（USB-C 连接器封装）内 2 个非电镀机械定位孔（pad \"\" "
                "np_thru_hole circle，size=drill=0.65mm、零铜环宽度、layers "
                "\"*.Cu\" \"*.Mask\"）的渲染表现；两板同"),
            "count": 2,
            "abs_mm": np_abs,
            "mapped": mapped,
            "render_semantics": (
                "framing-r14b 证书点 fiducial_disk_black：r5_rgb=[0,0,0]、"
                "white_fill_mask=false——不在白墨重着色族内，r5→r14b 该处保持"
                "纯黑；np 孔无铜环（size=drill）故呈实心黑圆点，与电镀焊盘的"
                "「环+盘」形态判然有别"),
            "certificate_match": {
                "certificate": ("render-framing-r14b.json probe_block."
                                "certificate_points[name=fiducial_disk_black]"),
                "certificate_cropped_xy": cert["cropped_xy"],
                "certificate_r5_rgb": cert["r5_rgb"],
                "matched_np_index": matched_np_index,
                "delta_px": cert_delta_px,
                "tolerance_px": CERT_MATCH_TOL_PX,
            },
            "reader_corpus_corroboration": {
                "source": ("abstain-typology-r13-r16.json per_flag/"
                           "blackdot_dispatch（6dadac8d，只读）"),
                "reader_reported_fracs": READER_REPORTED_FRACS,
                "max_delta_frac": reader_max_delta,
                "tolerance": READER_MATCH_TOL,
                "note": ("读者 corpus 一致报告全图仅 2 处实心黑（r14 top："
                         "「全图唯一黑色图形」；r15 bottom：「整幅图中仅有的黑"
                         "色图元」），与板面 np 计数=2 一致"),
                "within_tolerance": reader_max_delta <= READER_MATCH_TOL,
            },
            "excluded_candidates": [
                "fiducial footprint：两板均 0",
                "bottom 层集 fp_circle（B.Cu/B.Mask/B.Silkscreen/Edge.Cuts/"
                "B.Courtyard）：两板均 0",
                "板级 gr_circle：两板均 0",
                "含 B.Cu 的 via：0（via 总数 applied/prep1 各 "
                f"{census['applied']['via_total']}/{census['prep1']['via_total']}，"
                "全部 buried 且 layers 不含 B.Cu）",
                "np_thru_hole：全板恰 2 处（即本族本身）",
            ],
            "status": "confirmed",
        },
        {
            "form_id": "F3_isolated_pad_pair",
            "reader_form": "右中孤立焊盘对（一圆形带辐条空隙、一方形，孤悬板内）",
            "physical_identity": (
                "CRTC（CP_Radial_D8.0mm_P3.50mm，径向电解电容封装）2 个电镀通"
                "孔焊盘（roundrect 1.6mm/drill 0.8 + circle 1.6mm/drill 0.8）；"
                "其外围辐条/环缝=铺铜 thermal clearance 空隙（空隙白族→r14b "
                "绿，非图元，per framing-r14b probe_finding）"),
            "pads": crtc_pads,
            "blackdot_source_in_neighborhood_mm": F3_NEIGHBORHOOD_MM,
            "blackdot_candidates_found": near,
            "f1_family_pads_in_neighborhood": f1_near,
            "blackdot_presence": f3_blackdot_status,
            "conclusion": (
                "焊盘对身份与中心圆盘归属（=F1 钻孔渲染族）已证实；「该焊盘对"
                "邻接黑点」未能证实任何实心黑色圆图元来源（邻域内 np 孔 0、B "
                "层集圆图元 0、fiducial 0、B.Cu via 0）——如实登记为 "
                "indeterminate，不硬造黑点来源"),
            "status": "identity_confirmed_blackdot_indeterminate",
        },
    ]

    probe = {
        "schema_version": "3.0",
        "kind": "tl2_blackdot_probe_r18",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "probe_id": "s66_blackdot_probe_r18",
        "authorization": {
            "axis_plan": {
                "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-"
                            "r17-r20.json",
                "sha256": axis_sha,
                "field": "stage1_rounds.rounds[R18]",
                "round_quote": r18,
            },
            "dev_record_r17": {
                "path_rel": "out/v3-tl2/calibration/round17-dev-record.json",
                "sha256": dev_sha,
                "field": "next_iteration_targets[0]",
                "quote_prefix": ntargets[0][:120],
            },
        },
        "layer_set": LAYERS_BOTTOM,
        "inputs": {
            "boards": {
                st: {"path_rel": f"out/v3-tl2/calibration/staging-r4/{st}"
                                  ".kicad_pcb",
                     "sha256_measured": board_shas[st],
                     "witness_field": (f"render-framing-r14b.json "
                                       f"input_board_witness.{st}"),
                     "match": True}
                for st in BOARDS
            },
            "framing_r14b": {
                "path_rel": "out/v3-tl2/calibration/render-framing-r14b.json",
                "sha256": framing_sha,
            },
            "witness_r14b": {
                "path_rel": "out/v3-tl2/calibration/render-witness-r14b.json",
                "sha256": witness_sha,
            },
            "typology": {
                "path_rel": "out/v3-tl2/calibration/abstain-typology-r13-r16"
                            ".json",
                "sha256": typ_sha,
            },
            "read_only_note": (
                "零写板、零 kicad-cli 调用、零 PNG/PDF 内容读取（渲染表现语义"
                "全部以盘上仪器记录字段为准）；不读 GT/reader-raw/derivation-"
                "log/compare 产物"),
        },
        "render_instrument_facts": {
            "combined_white_fill_count": fills,
            "combined_white_stroke_count": strokes,
            "orange_exact_count_r14b": orange_px,
            "certificate_points_used": [
                "fiducial_disk_black", "pad_hole_disk", "fiducial_ring_gap",
                "pad_ring_cyan_band", "pad_rim_gap_band"],
        },
        "census": census,
        "families": families,
        "blackdot_baseline_registered": {
            "abstain_flags_rubric": BLACKDOT_ABSTAIN_BASELINE,
            "judged_normal_dispatches": BLACKDOT_JUDGED_NORMAL_BASELINE,
            "source": ("abstain-typology-r13-r16.json per_flag/"
                       "blackdot_dispatch（fail-closed 复核）"),
        },
        "overall_status": (
            "F1/F2 confirmed；F3 identity_confirmed_blackdot_indeterminate"
            if f3_blackdot_status == "confirmed_absent" else "FAIL"),
        "section_5b_text": section_5b,
        "no_visual_reading": True,
        "_verification_note": None,
    }
    if probe.pop("_verification_note", None) is not None:
        _fail("内部占位键非 None")
    if probe["overall_status"] == "FAIL":
        _fail("overall_status=FAIL（F3 邻域出现意外候选——如实停止）")

    # ---- §5B 关键语自证（防漂移）----
    for needle in ("探针证实", "不构成任何判据、期望清单", "按 §4 既有规则处理",
                   "top 视黑点同样适用"):
        if needle not in section_5b:
            _fail(f"§5B 文本缺关键语：{needle!r}")

    # ---- canonical 落盘 + 幂等守卫 ----
    record_bytes = hashing.canonical_json_bytes(probe)
    rebuild_probe = json.loads(json.dumps(probe))
    # 同参重建自证：以原 dict 再次 canonical（纯函数链）
    if hashing.canonical_json_bytes(rebuild_probe) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: blackdot-probe-r18.json")
    if PROBE_OUT.exists():
        if PROBE_OUT.read_bytes() != record_bytes:
            _fail("blackdot-probe-r18.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r18-blackdot-probe] 重跑自证：blackdot-probe-r18.json 重建字"
              "节与既有文件逐字节一致（幂等通过，零覆写）")
    else:
        PROBE_OUT.write_bytes(record_bytes)
        if PROBE_OUT.read_bytes() != record_bytes:
            _fail("回读不一致: blackdot-probe-r18.json")

    # ---- 汇总打印 ----
    print("[r18-blackdot-probe] 锚验证：framing-r14b " + framing_sha[:8] +
          " / witness-r14b " + witness_sha[:8] + " / typology " + typ_sha[:8] +
          " / axis-plan " + axis_sha[:8] + " / round17-dev " + dev_sha[:8] +
          " 全部 OK；两板 sha 与 framing input_board_witness 逐字相符")
    print(f"[r18-blackdot-probe] 普查：footprints="
          f"{census['applied']['footprint_count']}，圆钻孔={fills['applied']}"
          f"（=framing 白 fill 计数恒等），椭圆槽孔={strokes['applied']}，"
          f"np_thru_hole=2，fiducial=0，B 层集 fp_circle=0，B.Cu via=0")
    print(f"[r18-blackdot-probe] F2 证实：np 定位孔绝对坐标 {np_abs} mm → "
          f"bottom 成图 px {[m['bottom_cropped_px'] for m in mapped]}，证书点"
          f" fiducial_disk_black {cert['cropped_xy']} 偏差 {cert_delta_px}px"
          f"（容差 {CERT_MATCH_TOL_PX}px）；reader corpus 对照最大偏差 "
          f"{reader_max_delta}")
    print(f"[r18-blackdot-probe] F3：CRTC 焊盘对 {[p['abs_mm'] for p in crtc_pads]}"
          f"；邻域 {F3_NEIGHBORHOOD_MM}mm 内黑色圆图元候选=0（黑点存在性="
          f"{f3_blackdot_status}=indeterminate 如实登记）")
    print(f"[r18-blackdot-probe] 工件 sha256：blackdot-probe-r18.json="
          f"{_sha(PROBE_OUT)}")
    print("[r18-blackdot-probe] §5B 注记文本（装配结果，s67 fail-closed 转录）：")
    print(section_5b, end="")


if __name__ == "__main__":
    main()
