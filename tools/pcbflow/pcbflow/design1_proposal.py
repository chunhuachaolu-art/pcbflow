"""DESIGN-1：剩余 5 行的设计级出路提案（纯函数核，零写 live）。

背景（证据链，全部在盘）：
- S1（out/coreboard-live2b-s1）：5 目标网 UNSAT(verified)——FMC_SDNE0(RPL-038
  board 割 591)/GNDA(RPL-039 board 割 301004)/LTDC_VSYNC(RPL-052 board 割
  3088)/SWDIO(RPL-054 端点自锁割 8)/VBAT(RPL-056 board 割 300864)。
- S2（out/coreboard-live2b-s2）：口袋分析——FMC_SDNE0 口袋=A 端 pad U1.44、
  GNDA 口袋=B 端 pad U1.37（被 U1 锚件引脚场围死）；≤2mm 非锚件微移位候选
  0/5 全负；SWDIO/LTDC_VSYNC/VBAT 为 B(A) 端 PTH 8 邻辐条 hole_clearance
  全锁（J3/J4 排针焊盘，drill d=1.0）。
- APPLY-1（live 板 sha 前缀 dbfea089）：3V3+GPIO_PE2 已落，unconnected 57→55。

本模块只放纯函数（零落盘、零子进程、无 wall-clock；驱动与 kicad-cli 留编排
侧 scripts/design1_run.py 与 Bash）。三类出路：
- 类 A（U1 锚件位姿/引脚场变更）：U1 整体移位候选生成+邻件间隙核算、
  pad 附着铜账单（复用 live2s2_proposal.disturbance_bill）、口袋墙 census
  （端点 R 邻域他网铜段/孔，含受保护网豁免）；
- 类 B（端点侧变更）：PTH 焊盘环带几何（drill/hole_clearance/halfwidth →
  可落铜环带）、环带端点变体生成、同网连通分量备选落点（复用
  live2s2_proposal.landing_points）；
- 类 C（接受现状+waiver 台账）：waiver 登记行装配。

合同红线（继承 S1/S2）：SAT 必带 witness（Router plan.ok=L1 终判全过+端点
落铜）；UNSAT 必须 verify=true 证书；其余 UNKNOWN；禁自动改判；
route_grid.py/cli.py/config.py 零改动。
"""

from __future__ import annotations

import math
import re

from . import board_writer
from . import live2s2_proposal as P2

DESIGN1_SCHEMA = "1.0"
DESIGN1_ARTIFACT_KIND = "design1_proposal_matrix"
DESIGN1_DATASET = "coreboard-design1"
DESIGN1_DATE = "2026-09-11"

# live 板冻结见证（APPLY-1 后；开工/收工双验，不符即停）
LIVE_BOARD_SHA_PREFIX = "dbfea089"
PROTECTED = (("pcbflow/config.py", "f515c348"),
             ("toolchain_lock.json", "d43dad89"))

# 5 目标行（S1/RIPUP-1 权威行号；漂移即停）
TARGET_ROWS = {
    "FMC_SDNE0": "RPL-038", "GNDA": "RPL-039", "LTDC_VSYNC": "RPL-052",
    "SWDIO": "RPL-054", "VBAT": "RPL-056",
}
# 已收行（APPLY-1 落板；设计变更不得使其退化——账单受保护网）
APPLIED_NETS = ("3V3", "GPIO_PE2")

# .kicad_pro rules（route_grid 同源）
PTH_HOLE_CLEARANCE = 0.25     # min_hole_clearance
EDGE_CLEARANCE = 0.5
ROUTE_WIDTH = 0.2             # 目标网 class 线宽（S1 rows router.width 同值）

# 端点变体搜索窗梯（margin 仅搜索参数，合法性 Router L1 终判；S2 先例）
VARIANT_MARGIN_LADDER_SHORT = (3.0, 5.0, 8.0)   # 端点跨距 ≤20mm
VARIANT_MARGIN_LADDER_LONG = (3.0, 5.0)         # 端点跨距 >20mm（区域体积受控）

# 口袋墙 census 半径（surgical strip 候选）
WALL_RADII = (1.5, 2.5)

# U1 整移候选（方向单位向量 × 幅度；west=远离 U2 且增大 U1↔U2 间隙）
U1_SHIFT_DIRECTIONS = ((-1.0, 0.0),)          # west
U1_SHIFT_MAGNITUDES = (1.0, 2.0)


# ---- 类 B：PTH 环带几何（纯数学） -------------------------------------------
def pth_rim_band(r_pad, r_drill, hole_clearance=PTH_HOLE_CLEARANCE,
                 halfwidth=ROUTE_WIDTH / 2.0, eps=1e-9):
    """PTH 焊盘（pad 半径 r_pad、钻孔半径 r_drill）上的可落铜环带。

    环带内半径 d_min：点到孔圆距离 ≥ hole_clearance + halfwidth（硬封闭判据
    取严格 <，等号开放——route_grid._seg_closed/_cell_why 同式）。
    返回 {d_min, r_pad, on_pad_open, zero_margin, note}；d_min ≤ r_pad 才存在
    可落铜环带（落点须在焊盘铜上）。"""
    d_min = r_drill + hole_clearance + halfwidth
    on_pad_open = d_min <= r_pad + eps
    return {"d_min": round(d_min, 6), "r_pad": r_pad, "r_drill": r_drill,
            "on_pad_open": bool(on_pad_open),
            "zero_margin": bool(abs(d_min - r_pad) <= 1e-6),
            "note": "落点 d∈[d_min, r_pad]；dist(点,孔圆)=d-r_drill ≥ "
                    "hole_clearance+halfwidth（等号开放）"}


def rim_endpoints(cx, cy, r_pad, r_drill, angles_deg,
                  hole_clearance=PTH_HOLE_CLEARANCE,
                  halfwidth=ROUTE_WIDTH / 2.0, d=None):
    """锁定 PTH 焊盘的环带端点变体（角度制，0°=+x 即东）。

    d=None 时取环带内缘 d_min（可能零裕量退化）；d 给定时须落在可落铜环带
    [d_min, r_pad] 内（如 pad 加大后的中带点）。全部为焊盘铜上的数据级端点
    变体。返回 [{x, y, angle_deg, d, zero_margin}]。"""
    band = pth_rim_band(r_pad, r_drill, hole_clearance, halfwidth)
    out = []
    if not band["on_pad_open"]:
        return out
    dd = band["d_min"] if d is None else float(d)
    if not (band["d_min"] - 1e-9 <= dd <= r_pad + 1e-9):
        raise ValueError("d=%s 不在可落铜环带 [%s, %s] 内"
                         % (dd, band["d_min"], r_pad))
    for ang in angles_deg:
        a = math.radians(ang)
        out.append({"x": round(cx + dd * math.cos(a), 4),
                    "y": round(cy + dd * math.sin(a), 4),
                    "angle_deg": ang, "d": round(dd, 6),
                    "zero_margin": band["zero_margin"] and dd == band["d_min"]})
    return out


# ---- 类 B：焊盘几何变体（pad 加大；板级/封装编辑的数据级描述） -----------------
_ENLARGE_TOL = 0.05


def enlarge_pth_pad(board_text, ref, number, new_size):
    """ref.number PTH 焊盘 size (s s) → (new_size new_size)（其余零改动）。

    返回 (新板文本, {old_size, new_size})；焊盘未命中/size 不唯一即报错
    （fail-closed）。封装库同步义务由调用方在账单里申报。"""
    hit = []
    for (s, e) in board_writer._top_level_nodes(board_text, "footprint"):
        node = board_text[s:e]
        m = re.search(r'\(property "Reference" "([^"]+)"', node)
        if not m or m.group(1) != ref:
            continue
        for pm in re.finditer(r'\(pad "%s" [^\n]*?\n' % re.escape(number),
                              node):
            pad_start = s + pm.start()
            seg = board_text[pad_start:s + e]
            sm = re.search(r"\(size ([\d.]+) ([\d.]+)\)", seg)
            if not sm:
                continue
            old = float(sm.group(1))
            if abs(old - float(sm.group(2))) > _ENLARGE_TOL:
                raise ValueError("pad %s.%s 非方形 size (%s %s)"
                                 % (ref, number, sm.group(1), sm.group(2)))
            hit.append((pad_start, sm.start() + pad_start,
                        sm.end() + pad_start, old))
    if len(hit) != 1:
        raise ValueError("pad %s.%s 命中 %d 处（期望 1）" % (ref, number,
                                                          len(hit)))
    start, rs, re_, old = hit[0]
    new_text = (board_text[:rs] + "(size %.4f %.4f)" % (new_size, new_size)
                + board_text[re_:])
    return new_text, {"old_size": old, "new_size": new_size}


def smd_endpoint_offsets(cx, cy, w, h, offsets_mm):
    """SMD 焊盘上的端点偏移变体（纯数据级；offsets 相对焊盘中心）。

    返回 [{x, y, dx, dy}]（限定在焊盘矩形内；出界项剔除）。"""
    out = []
    for (dx, dy) in offsets_mm:
        if abs(dx) > w / 2.0 + 1e-9 or abs(dy) > h / 2.0 + 1e-9:
            continue
        out.append({"x": round(cx + dx, 4), "y": round(cy + dy, 4),
                    "dx": dx, "dy": dy})
    return out


def pad_lock_mechanism(r_pad, r_drill, hole_clearance=PTH_HOLE_CLEARANCE,
                       halfwidth=ROUTE_WIDTH / 2.0, spoke_len=0.05):
    """端点自锁机制量化：中心 8 邻辐条格为何全闭（钻孔盘语义）。

    邻格心距焊盘中心 spoke_len（0.05mm 格）< r_drill → 格心落在钻孔盘内，
    pt_prim_dist=0 < hole_clearance+halfwidth → 全层格堵（S2 直方图
    cell:hole_clearance 同机制）。"""
    inside = spoke_len < r_drill
    dist = 0.0 if inside else spoke_len - r_drill
    need = hole_clearance + halfwidth
    return {"spoke_len_mm": spoke_len, "spoke_cell_inside_hole_disk": inside,
            "dist_spoke_to_hole": round(dist, 6), "required_min": need,
            "locked": dist < need,
            "open_annulus": pth_rim_band(r_pad, r_drill, hole_clearance,
                                         halfwidth)}


# ---- 类 B：同网备选落点（连通分量） -----------------------------------------
def same_net_landings(component_descs_layers, home_xy, exclude_xy,
                      top_k=P2.LANDING_TOP_K):
    """同网连通分量 → 备选落点清单（live2s2_proposal.landing_points 同式）。

    exclude_xy：锁定端点本体（含 0.2mm 近邻去重）。"""
    return P2.landing_points(component_descs_layers, home_xy[0], home_xy[1],
                             top_k=top_k, exclude_xy=exclude_xy)


# ---- 类 A：口袋墙 census / 移位候选 ------------------------------------------
def pocket_wall(tracks, vias, cx, cy, radius, exclude_nets=(),
                protect_nets=()):
    """口袋端点 (cx,cy) 半径 R 邻域的他网铜 census（strip 候选账单）。

    段命中判据=任一端点落 R 内（走线端点=逃逸锚点）；孔=中心落 R 内。
    exclude_nets：目标网自身（其铜不入账）；protect_nets：已收/受保护网
    （APPLIED_NETS 等）——命中计入 protected_hits 不入剥除账（防已收行退化）。
    tracks/vias 形状=live2s2_proposal.strip_copper 输入（layer_name 齐备）。"""
    segs, vias_hit, protected = [], [], []
    nets = {}
    for t in tracks or []:
        net = t.get("net")
        if net in exclude_nets:
            continue
        for (x, y) in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
            if math.hypot(x - cx, y - cy) <= radius:
                if net in protect_nets:
                    protected.append(t)
                else:
                    segs.append(t)
                    nets[net] = nets.get(net, 0) + 1
                break
    for v in vias or []:
        net = v.get("net")
        if net in exclude_nets:
            continue
        if math.hypot(v["x"] - cx, v["y"] - cy) <= radius:
            if net in protect_nets:
                protected.append(v)
            else:
                vias_hit.append(v)
                nets[net] = nets.get(net, 0) + 1
    return {
        "cx": cx, "cy": cy, "radius_mm": radius,
        "segments": segs, "vias": vias_hit,
        "counts": {"segments": len(segs), "vias": len(vias_hit),
                   "nets": len(nets)},
        "net_histogram": dict(sorted(nets.items(), key=lambda kv: (-kv[1],
                                                                   kv[0]))),
        "protected_hits": len(protected),
        "protected_items": protected,
        "rule": "走线端点/过孔中心距口袋端点 ≤ %g mm（protect_nets 豁免）"
                % radius,
    }


def shift_gap_after(bbox_a, bbox_b, dx, dy, tol=1e-9):
    """A 平移 (dx,dy) 后与 B 的 pad-bbox 双轴间隙。

    正=该轴分离距离，负=该轴重叠量；gap_mm 取 max(gx,gy)（约束性间隙/最小
    重叠），axis 即其所属轴。"""
    a = (bbox_a[0] + dx, bbox_a[1] + dy, bbox_a[2] + dx, bbox_a[3] + dy)
    gx = max(a[0] - bbox_b[2], bbox_b[0] - a[2])
    gy = max(a[1] - bbox_b[3], bbox_b[1] - a[3])
    if gx >= gy - tol:
        return {"axis": "x", "gx": round(gx, 4), "gy": round(gy, 4),
                "gap_mm": round(gx, 4)}
    return {"axis": "y", "gx": round(gx, 4), "gy": round(gy, 4),
            "gap_mm": round(gy, 4)}


def u1_shift_candidates(u1_xy, magnitudes=U1_SHIFT_MAGNITUDES,
                        directions=U1_SHIFT_DIRECTIONS):
    """U1 整移候选（方向 × 幅度；确定性顺序）。"""
    out = []
    for (ux, uy) in directions:
        for mag in magnitudes:
            out.append({"dx": round(ux * mag, 4), "dy": round(uy * mag, 4),
                        "label": "u1_shift_%s_%s" % (
                            "W" if ux < 0 else "E" if ux > 0 else
                            "N" if uy < 0 else "S", ("%gmm" % mag))})
    return out


def blast_radius_summary(bill, moved_ref="U1"):
    """disturbance_bill → 爆炸半径摘要（段/网/孔计数；重布义务声明）。"""
    nets = sorted({it["net"] for it in
                   (bill.get("segments") or []) + (bill.get("vias") or [])})
    return {
        "moved_ref": moved_ref,
        "segments": bill.get("counts", {}).get("segments_total", 0),
        "vias": bill.get("counts", {}).get("vias_total", 0),
        "nets": len(nets), "net_list": nets,
        "obligation": "被移 ref 焊盘附着铜全部失效：%d 段（%d 网）需重布"
                      % (bill.get("counts", {}).get("segments_total", 0),
                         len(nets)),
    }


# ---- 工程量级分类 -------------------------------------------------------------
ENGINEERING_DATA = "数据级（opens 行端点坐标变体；板铜零改动即可求解落线）"
ENGINEERING_BOARD = "板级编辑（封装库/板文本：剥铜+重布+复验，KiCad 手工可及）"
ENGINEERING_LAYOUT = "布局级（锚件位姿/引脚场重排：③ 编译器重布局或整链重跑）"


def engineering_magnitude(klass, detail):
    return {"class": klass, "magnitude": detail}


# ---- verdict 行装配（账本纯函数） ---------------------------------------------
def endpoint_variant_row(row_id, net, side, variant, ladder_steps,
                         independent_check, baseline_cert_cut,
                         board_change=None):
    """类 B 端点变体 verdict 行（纯装配；witness 语义=S2 closure_verdict 同源）。

    ladder_steps：[{margin_mm, route(normalize_plan 形)}]；SAT ⟺ 存在 ok 步且
    independent_check.all_ok（否则如实 UNKNOWN，禁自动改判）。
    board_change：板级几何变体（如 pad 加大）描述 dict 或 None——非 None 时
    工程量级升为板级编辑并逐项申报改动点。"""
    witness_step = next((s for s in ladder_steps if s["route"]["ok"]), None)
    status = "SAT" if witness_step else "UNKNOWN"
    if status == "SAT" and not (independent_check
                                and independent_check.get("all_ok")):
        # 合同红线：SAT 必须独立复核全过（复核缺失/不过 = 如实降 UNKNOWN）
        status = "UNKNOWN"
    w = witness_step["route"] if witness_step else None
    engineering = engineering_magnitude(
        "B", ENGINEERING_BOARD if board_change else ENGINEERING_DATA)
    return {
        "row_id": row_id, "net": net,
        "design1_class": "B", "design1_status": status,
        "candidate_kind": "endpoint_variant",
        "variant_side": side, "variant": variant,
        "board_change": board_change,
        "baseline": "S1 UNSAT(verified cert cut=%d)" % baseline_cert_cut,
        "witness": None if not w else {
            "margin_mm": witness_step["margin_mm"],
            "segments": len(w["segments"]), "vias": len(w["vias"]),
            "length_mm": w["length_mm"], "refine_rounds":
                w["refine_rounds"],
        },
        "route_plan": None if not w else {
            "net": net, "width": w["width"], "via_size": w["via_size"],
            "via_drill": w["via_drill"], "segments": w["segments"],
            "vias": w["vias"],
            "uuid": board_writer.route_uuid(
                {"net": net, "segments": w["segments"], "vias": w["vias"]}),
        },
        "ladder": [{"margin_mm": s["margin_mm"], "ok": s["route"]["ok"],
                    "fail": s["route"]["fail"],
                    "segments": len(s["route"]["segments"])}
                   for s in ladder_steps],
        "independent_check": independent_check,
        "unknown_reason": None if status == "SAT" else
            ("unknown:no_witness_within_ladder(端点变体窗梯内无 witness；"
             "不自动改判)" if not witness_step
             else "unknown:independent_check_failed"),
        "engineering": engineering,
        "restricted_declarations": [
            "端点变体=opens 行端点坐标数据级修改（同网既有铜上的落点/锁定 "
            "PTH 焊盘环带落点），板铜零改动、零拆线；margin 仅搜索参数，"
            "合法性=Router L1 终判（ripup1_campaign 先例）"
            + ("；板级几何变体（pad 加大）另逐项申报，验证板=staging 副本"
               if board_change else ""),
            "SAT=witness + 独立复核全过（fresh Legality 逐段/逐孔+两端落铜+"
            "变体端在既有同网铜上）；复核不过即如实降 UNKNOWN",
            "witness 是提案（route_plan），本包零写 live；应用与否由用户拍板",
        ],
    }


def shift_or_strip_row(row_id, net, candidate_kind, change_desc, ladder_steps,
                       independent_check, baseline_cert_cut, bill_summary,
                       engineering):
    """类 A 移位/剥除 verdict 行（纯装配；语义同 endpoint_variant_row）。"""
    witness_step = next((s for s in ladder_steps if s["route"]["ok"]), None)
    status = "SAT" if witness_step else "UNKNOWN"
    if status == "SAT" and not (independent_check
                                and independent_check.get("all_ok")):
        status = "UNKNOWN"
    w = witness_step["route"] if witness_step else None
    return {
        "row_id": row_id, "net": net,
        "design1_class": "A", "design1_status": status,
        "candidate_kind": candidate_kind, "change": change_desc,
        "baseline": "S1 UNSAT(verified cert cut=%d)" % baseline_cert_cut,
        "witness": None if not w else {
            "margin_mm": witness_step["margin_mm"],
            "segments": len(w["segments"]), "vias": len(w["vias"]),
            "length_mm": w["length_mm"],
        },
        "route_plan": None if not w else {
            "net": net, "width": w["width"], "via_size": w["via_size"],
            "via_drill": w["via_drill"], "segments": w["segments"],
            "vias": w["vias"],
            "uuid": board_writer.route_uuid(
                {"net": net, "segments": w["segments"], "vias": w["vias"]}),
        },
        "ladder": [{"margin_mm": s["margin_mm"], "ok": s["route"]["ok"],
                    "fail": s["route"]["fail"],
                    "segments": len(s["route"]["segments"])}
                   for s in ladder_steps],
        "independent_check": independent_check,
        "blast_radius": bill_summary,
        "engineering": engineering_magnitude("A", engineering),
        "unknown_reason": None if status == "SAT" else
            ("unknown:no_witness_within_ladder(设计变更后窗梯内仍无 "
             "witness；不自动改判)" if not witness_step
             else "unknown:independent_check_failed"),
        "restricted_declarations": [
            "验证板=快照副本的 staging 变体（live 板零写）；变更只入 staging "
            "板文本，账单逐项落 ledger",
            "剥除他网铜=设计级拆线前提（RIPUP-1 同前提）；被剥网重布可行性"
            "未在本包验证，逐项如实申报",
            "SAT=witness + 独立复核全过；复核不过或窗梯无 witness 即如实 "
            "UNKNOWN，禁自动改判",
        ],
    }


# ---- 类 C：waiver 台账 ---------------------------------------------------------
def waiver_row(row_id, net, cert_ref, accept_conditions, manufacturing_impact,
               functional_impact, reopen_trigger):
    """接受现状的 known-open 登记行（模板；供用户逐字段拍板）。"""
    return {
        "row_id": row_id, "net": net, "status": "KNOWN-OPEN(waive 候选)",
        "certificate_ref": cert_ref,
        "accept_conditions": accept_conditions,
        "manufacturing_impact": manufacturing_impact,
        "functional_impact": functional_impact,
        "reopen_trigger": reopen_trigger,
        "waive_statement_template":
            "RPL 行 %s（网 %s）：在 %s 所证受限模型内不可布；接受现状的条件="
            "%s；制造影响=%s；功能影响=%s；重开条件=%s"
            % (row_id, net, cert_ref, accept_conditions,
               manufacturing_impact, functional_impact, reopen_trigger),
    }


# ---- 汇总：排序决策矩阵 ---------------------------------------------------------
_STATUS_RANK = {"SAT": 0, "UNKNOWN": 1, "UNSAT": 2}


def decision_matrix(rows):
    """候选 verdict 行 → 排序决策矩阵（可收行↓、类内成本↑、row_id 字典序）。

    排序键：design1_status（SAT 优先）→ 爆炸半径（剥除段数+账单段数）→
    engineering 类别（数据级 < 板级 < 布局级）→ row_id。"""
    def eng_rank(r):
        m = (r.get("engineering") or {}).get("magnitude") or ""
        if m.startswith("数据级"):
            return 0
        if m.startswith("板级"):
            return 1
        return 2

    def blast(r):
        b = r.get("blast_radius") or {}
        stripped = b.get("stripped") or {}
        if isinstance(stripped, dict):
            stripped_n = int(stripped.get("segments", 0)) \
                + int(stripped.get("vias", 0))
        else:
            stripped_n = 0
        return (int(b.get("segments", 0)) + int(b.get("vias", 0))
                + stripped_n)

    return sorted(rows, key=lambda r: (_STATUS_RANK.get(r.get(
        "design1_status"), 3), eng_rank(r), blast(r),
        str(r.get("row_id")), str(r.get("candidate_kind"))))


def matrix_view(rows):
    """决策矩阵 → 用户可读形态（列裁剪；纯装配）。"""
    def _blast(r):
        b = r.get("blast_radius") or {}
        st = b.get("stripped") or {}
        n = int(b.get("segments", 0)) + int(b.get("vias", 0))
        if isinstance(st, dict):
            n += int(st.get("segments", 0)) + int(st.get("vias", 0))
        return n

    return [{
        "rank": i + 1,
        "row": r.get("row_id"), "net": r.get("net"),
        "class": r.get("design1_class"),
        "candidate": r.get("candidate_kind"),
        "status": r.get("design1_status"),
        "witness": None if not r.get("witness") else
            "%s 段+%s 孔/长 %smm" % (r["witness"]["segments"],
                                    r["witness"]["vias"],
                                    r["witness"]["length_mm"]),
        "blast_radius": _blast(r),
        "engineering": (r.get("engineering") or {}).get("magnitude"),
        "premise": "用户批准 + （剥铜类）被剥网重布义务" if _blast(r)
            else "用户批准（数据级）",
    } for i, r in enumerate(rows)]
