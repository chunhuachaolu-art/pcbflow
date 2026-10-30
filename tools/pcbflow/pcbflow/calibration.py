"""Critic 校准域种子集与一致性比较器（S17；TL-2；APR-0008 线）。

calibration-domain-v1：用 Rev-C 判例（ASM 链已确证的缺陷与处置）做人工
标注 ground truth 的**小而可信种子集**。红线与语义边界：

- 标注属 pipeline 侧：GT 条目从 out/revc-asm/ 冻结证据（pose-revision-
  proof / ripup-reroute-ledger 等）的板坐标**确定性换算**得出，不混入
  reader 视野，不参与 raw-flags 校验或 ingest；
- 类别必须落在 ``critic.FLAG_CATEGORIES`` 枚举内（枚举零改动）；R4/F1
  簇映射放置类（courtyard_crowding），L1 簇按缺陷性质诚实映射（铜短路
  无专用类 → other_advisory catch-all，见 GT 描述）；
- 位置框=板坐标 mm → 渲染图幅百分比的确定性换算（board bbox 来自
  Edge.Cuts 解析；板像素界来自 PNG 背景差分扫描，纯函数）；
- **度量定义先写死后跑**（本文件常量即定义）：类别相等 + 空间包含度
  ≥ CONTAINMENT_MIN；abstain 单列不参与匹配。禁止为通过而调阈值；
- **度量版本化（S20）**：v1 首测暴露「整板大框平凡包含 GT 框」的度量
  观察（reader 框面积/GT 框面积可达数百倍仍计 containment=1.0）——
  度量 v2（calibration-metric-v2，compare_v2）在 v1 规则上增加面积比
  上限 AREA_RATIO_MAX（取值依据见其 rationale，先于本轮结果写死）；
  v1 度量与其产物（calibration-run-v1.json）原样保留，版本字段区分、
  不回写；
- **度量 v3（P3-A，compare_v3）**：在 v2 双条件之上修比较器正确性
  缺口——一对一确定性指派（每 GT/每 flag 至多一匹配，重复报告如实
  单列 duplicate_reports 不计入正确命中分母）、视角可比（flag_views
  由编排侧注入）、输出语义更名（未匹配=unmatched/unadjudicated，
  不再命名 false_positive；reader_precision_vs_seed_gt 更名
  seed_match_rate）；阈值沿用 v2 声明常量零变化，v1/v2 度量与产物
  原样保留；
- 比较器是 advisory 侧分析工具，**不是门**：其输出不进任何 gate 谓词、
  不翻转 critic_calibration_in_range（该谓词语义不变，v2 阈值属
  proposal_only，正式采纳须人工批准）；
- 种子 GT=部分覆盖（4 簇判例）：false_positive 计数只是「相对种子 GT
  未匹配」，不构成误报率结论（缺 basis 不虚构）。

生成器模式：纯函数、零子进程、零落盘、零网络、无 wall-clock；
仅标准库 + 包内 critic/hashing。CLI=stdin→stdout canonical JSON。
"""

from __future__ import annotations

import json
import re
import struct
import zlib

from . import critic, hashing

DOMAIN_ID = "calibration-domain-v1"
DOMAIN_VERSION = "1.0"
METRIC_VERSION = "calibration-metric-v1"
METRIC_VERSION_V2 = "calibration-metric-v2"
METRIC_VERSION_V3 = "calibration-metric-v3"

#: 比较器空间匹配阈值（**固定定义，先写死后跑；禁止为通过而调**）：
#: 读者框与 GT 框交集面积 / GT 框面积 ≥ 0.5（读者框须覆盖 GT 缺陷区
#: 一半以上——GT 框围绕判例缺陷紧密划定，读者框为目测百分比，用包含度
#: 而非 IoU 以免惩罚粗粒度目测）。
CONTAINMENT_MIN = 0.5

#: GT 位置框的板坐标外扩（mm）：围绕判例坐标 bbox 的固定外扩，消除
#: 焊盘/丝印尺寸级噪声；固定值，非调参对象。
GT_MARGIN_MM = 1.0

#: 度量 v2（calibration-metric-v2）面积比上限（**固定定义，先写死后跑；
#: 禁止为通过而调**）：读者框面积 / GT 框面积 ≤ AREA_RATIO_MAX。
#:
#: 取值依据（第一性原理，先于任何本轮运行结果写死，非结果反推）：
#: 1. GT 框=判例缺陷 bbox ± GT_MARGIN_MM(1.0mm) 管线固定外扩，本身即
#:    管线侧承认的「缺陷邻域」上界；
#: 2. 校准要度量的是读者对缺陷的**定位能力**——读者框是邻域声明：
#:    若读者框面积超出 GT 框一个数量级（>10×），则即使完全包含 GT，
#:    框内「非 GT 邻域」面积也占读者框 90% 以上，框不再携带缺陷位置
#:    信息，退化为区域/整板级声明（如整板大框）；
#: 3. 「读者框须与缺陷同量级邻域」的直接操作化=面积同数量级：取一个
#:    数量级（10×，线性当量 √10≈3.16×）为固定小倍数，取整十、与任何
#:    特定旗标的结果无关。整板大框（面积比数百倍）在该上限下被拒，
#:    紧邻域框（面积比约 1–3×）通过。
AREA_RATIO_MAX = 10.0

#: 度量 v2 面积比上限的取值依据（随比较器输出归档，proposal 语义见上）
AREA_RATIO_MAX_RATIONALE = (
    "AREA_RATIO_MAX=10.0：读者框面积/GT框面积 ≤ 一个数量级（线性当量 "
    "√10≈3.16×）。依据：GT 框=缺陷 bbox±1.0mm 管线外扩（管线承认的"
    "缺陷邻域上界）；读者框是邻域声明，面积超出 GT 一个数量级即不再"
    "携带缺陷位置信息（完全包含 GT 时非邻域部分已占 90%+）；取「同"
    "量级」的字面语义=面积同一数量级（10×），先于本轮运行写死，非"
    "结果反推。proposal_only：正式采纳须人工批准。")

#: GT 条目键集（additionalProperties=false 语义，fail-closed）
GT_ENTRY_KEYS = ("gt_id", "category", "side", "board_box_mm",
                 "frame_box_pct", "drc_types", "cluster_refs",
                 "basis_refs", "description")
READER_FLAG_KEYS = ("flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence")
REQUIRED_READER_KEYS = ("flag_id", "category", "confidence", "abstain")

COVERAGE_CAVEAT = (
    "种子 GT=Rev-C 判例 4 簇（部分覆盖，非全板枚举）：reader 未匹配旗标"
    "（false_positive_ids）只是相对种子 GT 的未匹配计数，不构成误报率"
    "结论；本比较器输出为 advisory 侧分析，不是门、不翻转任何谓词。")

# ---------------------------------------------------------------------------
# 度量 v3（P3-A）语义常量：一对一指派 + 视角可比 + 输出语义更名。
# 匹配阈值沿用上方 v2 声明常量（CONTAINMENT_MIN/AREA_RATIO_MAX）零变化；
# 本块只新增**语义声明文本**与结构规则，不引入任何新的可调阈值。
# ---------------------------------------------------------------------------

#: seed 匹配率的口径注（P3-A 语义更名：禁称 precision/FPR）。
SEED_METRIC_NOTE = (
    "seed 匹配率=相对种子 GT 的诊断值，不是完整 precision/FPR"
    "（种子为部分覆盖判例，框命中不证明电气事实）")

#: v3 弃权率的口径定义（单位与分母显式；不参评任何单一达标判断）。
ABSTAIN_RATE_DEFINITION = (
    "单位=旗标条数；分母=本次运行该板发出的全部旗标；弃权率与 "
    "recall/seed_match_rate 联合评价，单独优化弃权率无意义（不参评"
    "任何单一达标判断）")

#: v3 覆盖度警示：沿用 v1/v2 文本并追加「框命中≠电气事实」增补。
COVERAGE_CAVEAT_V3 = COVERAGE_CAVEAT + (
    " v3 增补：matches 与 seed_match_rate 只表示框级命中，"
    "框命中不构成电气事实结论。")

#: v3 度量定义全文（随比较器输出归档）。
V3_METRIC_DEFINITION = (
    "度量 v3=v2 双条件（containment(读者框∩GT框/GT框面积) ≥ "
    "containment_min 且 读者框面积/GT框面积 ≤ area_ratio_max，阈值"
    "沿用 v2 声明常量未变）+ 一对一确定性指派（候选对按 containment "
    "降序、面积比升序、flag_id/gt_id 字典序升序贪心扫描，flag 与 gt "
    "均未占用才成匹配；每个 GT 与每个 flag 至多一个匹配；因一对一"
    "落选的候选对如实计入 duplicate_reports，不计入任何正确命中"
    "分母）+ 视角可比（flag_views 由编排侧注入 {flag_id: top|bottom}，"
    "视角不符不入候选、记 view_mismatch；未提供映射=视角不设防，"
    "view_check 如实标注 not_applicable/partial，不冒充已检查）+ "
    "输出语义更名（未匹配旗标=unmatched/unadjudicated，不再命名 "
    "false_positive；reader_precision_vs_seed_gt 更名 seed_match_rate"
    "并附口径注）。abstain 单列不参与匹配。先写死后跑，阈值不后调；"
    "v1/v2 度量与产物原样保留（版本字段区分，不回写）。")



# ---------------------------------------------------------------------------
# 确定性几何换算（板坐标 mm → 渲染图幅百分比）
# ---------------------------------------------------------------------------

def board_edge_bbox_mm(board_text: str) -> dict:
    """从板文件文本解析 Edge.Cuts 层图元坐标 bbox（确定性；纯函数）。

    支持 gr_line/gr_rect/gr_arc/gr_circle/gr_poly 的 xy/start/end/mid/
    center 坐标；无 Edge.Cuts 图元即 ValueError（fail-closed）。
    """
    coords: list = []
    for m in _iter_sexprs(board_text, ("gr_line", "gr_rect", "gr_arc",
                                       "gr_circle", "gr_poly")):
        if "Edge.Cuts" not in m:
            continue
        for nm in _PT_RE.finditer(m):
            coords.append((float(nm.group(1)), float(nm.group(2))))
    if not coords:
        raise ValueError("board_edge_bbox_mm: Edge.Cuts 无图元（fail-closed）")
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return {"x_min": min(xs), "y_min": min(ys),
            "x_max": max(xs), "y_max": max(ys)}


def png_board_pixel_bounds(data: bytes) -> dict:
    """PNG 解码（8-bit RGB/RGBA、非隔行）→ 背景差分板像素界（纯函数）。

    kicad-cli ``--background opaque`` 的画布底为**垂直渐变**（顶部浅、
    底部深，逐行均匀）：逐行取左缘像素 (0,y) 为该行背景色，行内与其
    不同的像素判为板像素；板像素界=全部板像素 bbox（inclusive）。
    fail-closed：任一行与左缘同色像素占比 <10%（板触左缘/背景水平
    不均匀）即拒绝；抽样行左右缘色不一致（无法区分板与背景）即拒绝；
    板界触图像四边即拒绝（居中渲染应有边距）。确定性：同字节 ⇒ 同界。
    """
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("png_board_pixel_bounds: PNG magic 不符")
    pos, idat, ihdr = 8, b"", None
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length
    if ihdr is None or not idat:
        raise ValueError("png_board_pixel_bounds: IHDR/IDAT 缺失")
    w, h, depth, ctype_n, _, _, interlace = ihdr
    if depth != 8 or interlace != 0 or ctype_n not in (2, 6):
        raise ValueError(f"png_board_pixel_bounds: 不支持的 PNG 形态 "
                         f"depth={depth} color={ctype_n} interlace={interlace}"
                         "（仅 8-bit RGB/RGBA 非隔行）")
    bpp = 3 if ctype_n == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * bpp
    if len(raw) < h * (stride + 1):
        raise ValueError("png_board_pixel_bounds: 解压数据不足")
    pixels = _unfilter(raw, w, h, bpp)
    # 背景水平均匀性（抽样行）：左右缘色必须一致，否则无法区分板与背景
    for y in range(0, h, max(1, h // 16)):
        if pixels[y][:bpp] != pixels[y][(w - 1) * bpp:w * bpp]:
            raise ValueError("png_board_pixel_bounds: 背景水平不均匀"
                             "（抽样行左右缘色不一致；fail-closed）")
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        row = pixels[y]
        bg = row[:bpp]
        n_diff = 0
        for x in range(w):
            px = row[x * bpp:x * bpp + bpp]
            if px != bg:
                n_diff += 1
                if x < x0:
                    x0 = x
                if x > x1:
                    x1 = x
                if y < y0:
                    y0 = y
                if y > y1:
                    y1 = y
        if n_diff > w * 0.9:
            raise ValueError("png_board_pixel_bounds: 行内左缘背景取样"
                             f"失效（y={y} 差分像素 {n_diff}/{w}；板触左缘"
                             "或背景非逐行均匀；fail-closed）")
    if x1 < 0:
        raise ValueError("png_board_pixel_bounds: 全图同色（无板界）")
    if x0 <= 0 or y0 <= 0 or x1 >= w - 1 or y1 >= h - 1:
        raise ValueError("png_board_pixel_bounds: 板界触图像边缘"
                         "（居中渲染应有边距；fail-closed）")
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "image_width": w, "image_height": h,
            "background_rgb": list(pixels[0][:bpp]),
            "background_model": "vertical_gradient_row_sampled"}


def box_mm_to_frame_pct(box_mm, board_bbox_mm: dict, px_bounds: dict,
                        *, side: str) -> list:
    """板坐标 mm 框 [x0,y0,x1,y1] → 渲染图幅百分比框（确定性；纯函数）。

    线性映射：板 bbox（Edge.Cuts，mm）→ 板像素界（PNG 实测）；top 视
    x/y 同向，bottom 视 x 镜像（y 同向）。百分比相对**整幅图幅**（与
    reader 位置证据的图幅百分比口径一致）。side 非 top/bottom、框越界
    板 bbox 即 ValueError（fail-closed）。
    """
    if side not in ("top", "bottom"):
        raise ValueError(f"box_mm_to_frame_pct: side 非法 {side!r}")
    x0m, y0m, x1m, y1m = box_mm
    bx0, bx1 = board_bbox_mm["x_min"], board_bbox_mm["x_max"]
    by0, by1 = board_bbox_mm["y_min"], board_bbox_mm["y_max"]
    if not (bx0 <= x0m <= x1m <= bx1 and by0 <= y0m <= y1m <= by1):
        raise ValueError(f"box_mm_to_frame_pct: 框越板界 {box_mm}")
    bw = bx1 - bx0
    bh = by1 - by0
    pw = px_bounds["x1"] - px_bounds["x0"]
    ph = px_bounds["y1"] - px_bounds["y0"]
    iw, ih = px_bounds["image_width"], px_bounds["image_height"]
    if bw <= 0 or bh <= 0 or pw <= 0 or ph <= 0:
        raise ValueError("box_mm_to_frame_pct: bbox 退化")

    def _mx(xm: float) -> float:
        fx = (xm - bx0) / bw
        if side == "bottom":
            fx = 1.0 - fx
        return (px_bounds["x0"] + fx * pw) / iw

    def _my(ym: float) -> float:
        return (px_bounds["y0"] + (ym - by0) / bh * ph) / ih

    xa, xb = sorted((_mx(x0m), _mx(x1m)))
    ya, yb = sorted((_my(y0m), _my(y1m)))
    return [_round6(xa), _round6(ya), _round6(xb), _round6(yb)]


# ---------------------------------------------------------------------------
# GT 条目构造（fail-closed 校验；类别枚举= critic.FLAG_CATEGORIES 零改动）
# ---------------------------------------------------------------------------

def build_gt_entry(*, gt_id: str, category: str, side: str,
                   board_box_mm, frame_box_pct, drc_types, cluster_refs,
                   basis_refs, description: str) -> dict:
    """构造并校验一条 GT 标注（非法 ValueError；纯函数）。"""
    if not (isinstance(gt_id, str) and gt_id):
        raise ValueError("build_gt_entry: gt_id 必须为非空字符串")
    if category not in critic.FLAG_CATEGORIES:
        raise ValueError(f"build_gt_entry: category {category!r} 不在 "
                         f"advisory 类别集 {list(critic.FLAG_CATEGORIES)}")
    if side not in ("top", "bottom"):
        raise ValueError(f"build_gt_entry: side 非法 {side!r}")
    if not (isinstance(board_box_mm, (list, tuple)) and len(board_box_mm) == 4):
        raise ValueError("build_gt_entry: board_box_mm 必须为 4 元框")
    if not (isinstance(frame_box_pct, (list, tuple))
            and len(frame_box_pct) == 4):
        raise ValueError("build_gt_entry: frame_box_pct 必须为 4 元框")
    for v in frame_box_pct:
        if not (isinstance(v, (int, float)) and not isinstance(v, bool)
                and 0.0 <= float(v) <= 1.0):
            raise ValueError(f"build_gt_entry: frame_box_pct 越界 {v!r}")
    if (frame_box_pct[0] >= frame_box_pct[2]
            or frame_box_pct[1] >= frame_box_pct[3]):
        raise ValueError("build_gt_entry: frame_box_pct 退化（x0<x1、y0<y1）")
    if not (isinstance(drc_types, (list, tuple)) and drc_types):
        raise ValueError("build_gt_entry: drc_types 必须为非空列表")
    if not (isinstance(cluster_refs, (list, tuple)) and cluster_refs):
        raise ValueError("build_gt_entry: cluster_refs 必须为非空列表")
    if not (isinstance(basis_refs, (list, tuple)) and basis_refs):
        raise ValueError("build_gt_entry: basis_refs 必须为非空列表")
    if not (isinstance(description, str) and description.strip()):
        raise ValueError("build_gt_entry: description 必须为非空字符串")
    return {
        "gt_id": gt_id,
        "category": category,
        "side": side,
        "board_box_mm": [float(v) for v in board_box_mm],
        "frame_box_pct": [float(v) for v in frame_box_pct],
        "drc_types": list(drc_types),
        "cluster_refs": list(cluster_refs),
        "basis_refs": list(basis_refs),
        "description": description,
    }


def validate_gt_entries(entries) -> None:
    """GT 条目集校验：逐条合法 + gt_id 唯一（非法 ValueError）。"""
    if not isinstance(entries, list) or not entries:
        raise ValueError("validate_gt_entries: 条目集必须为非空列表")
    seen = set()
    for e in entries:
        if not isinstance(e, dict) or sorted(e) != sorted(GT_ENTRY_KEYS):
            raise ValueError(f"validate_gt_entries: 条目键集非法 {sorted(e)}")
        build_gt_entry(**e)
        if e["gt_id"] in seen:
            raise ValueError(f"validate_gt_entries: gt_id 重复 {e['gt_id']}")
        seen.add(e["gt_id"])


# ---------------------------------------------------------------------------
# 比较器（reader flags vs GT；度量定义=本文件常量，先写死后跑）
# ---------------------------------------------------------------------------

def compare(reader_flags, gt_entries, *,
            containment_min: float = CONTAINMENT_MIN) -> dict:
    """一致性度量 v1（纯函数；advisory 分析，不是门）。

    reader_flags 每项：{flag_id, category, confidence, abstain[,
    frame_box_pct]}（多余键 fail-closed）。匹配规则（固定）：
    abstain=False 且 category 相等且 frame_box_pct 存在且
    containment(∩/GT 面积) ≥ containment_min。abstain 单列不参与匹配。
    """
    validate_gt_entries(gt_entries)
    norm_flags = _normalize_reader_flags(reader_flags)

    matches = []
    gt_matched = {e["gt_id"]: None for e in gt_entries}
    fp_ids: list = []
    no_box_ids: list = []
    abstain_ids: list = []
    scored = 0
    for f in norm_flags:
        if f["abstain"]:
            abstain_ids.append(f["flag_id"])
            continue
        scored += 1
        if f["frame_box_pct"] is None:
            no_box_ids.append(f["flag_id"])
            continue
        best = None
        for e in gt_entries:
            if e["category"] != f["category"]:
                continue
            c = _containment(f["frame_box_pct"], e["frame_box_pct"])
            if c is not None and c >= containment_min \
                    and (best is None or c > best[1]):
                best = (e["gt_id"], c)
        if best is not None:
            matches.append({"gt_id": best[0], "flag_id": f["flag_id"],
                            "category": f["category"],
                            "containment": _round6(best[1])})
            if gt_matched[best[0]] is None:
                gt_matched[best[0]] = f["flag_id"]
        else:
            fp_ids.append(f["flag_id"])
    missed = [gid for gid, m in gt_matched.items() if m is None]
    gt_n = len(gt_entries)
    return {
        "metric_version": METRIC_VERSION,
        "containment_min": containment_min,
        "metric_definition": (
            "匹配=abstain=False 且类别相等且 containment(读者框∩GT框/"
            "GT框面积) ≥ containment_min；abstain 单列不参与匹配。"
            "度量定义先写死后跑（S17），阈值不后调。"),
        "gt_count": gt_n,
        "reader_flag_count": len(norm_flags),
        "reader_scored_count": scored,
        "reader_abstain_ids": abstain_ids,
        "matches": matches,
        "gt_matched": {gid: m for gid, m in gt_matched.items()},
        "gt_missed_ids": missed,
        "gt_matched_count": gt_n - len(missed),
        "gt_recall": _ratio(gt_n - len(missed), gt_n),
        "reader_matched_ids": [m["flag_id"] for m in matches],
        "reader_unmatched_no_box_ids": no_box_ids,
        "reader_false_positive_ids": fp_ids,
        "reader_precision_vs_seed_gt": _ratio(
            len([m for m in matches]), scored) if scored else None,
        "coverage_caveat": COVERAGE_CAVEAT,
    }


# ---------------------------------------------------------------------------
# 度量 v2（S20）：v1 规则 + 面积比上限（同量级邻域）
# ---------------------------------------------------------------------------

def _normalize_reader_flags(reader_flags) -> list:
    """reader flags 归一化与 fail-closed 校验（v1/v2 共用；纯函数）。"""
    norm_flags = []
    for i, f in enumerate(reader_flags):
        if not isinstance(f, dict):
            raise ValueError(f"compare: reader_flags[{i}] 不是对象")
        unknown = sorted(set(f) - set(READER_FLAG_KEYS))
        missing = [k for k in REQUIRED_READER_KEYS if k not in f]
        if unknown or missing:
            raise ValueError(f"compare: reader_flags[{i}] 键非法 "
                             f"unknown={unknown} missing={missing}")
        if f["category"] not in critic.FLAG_CATEGORIES:
            raise ValueError(f"compare: reader_flags[{i}].category "
                             f"{f['category']!r} 不在类别集")
        if not isinstance(f["abstain"], bool):
            raise ValueError(f"compare: reader_flags[{i}].abstain 须布尔")
        if isinstance(f["confidence"], bool) or \
                not isinstance(f["confidence"], (int, float)) or \
                not 0.0 <= float(f["confidence"]) <= 1.0:
            raise ValueError(f"compare: reader_flags[{i}].confidence 非法")
        box = f.get("frame_box_pct")
        if box is not None and (not isinstance(box, (list, tuple))
                                or len(box) != 4
                                or not all(isinstance(v, (int, float))
                                           and not isinstance(v, bool)
                                           and 0.0 <= float(v) <= 1.0
                                           for v in box)):
            raise ValueError(f"compare: reader_flags[{i}].frame_box_pct 非法")
        norm_flags.append({
            "flag_id": f["flag_id"], "category": f["category"],
            "confidence": float(f["confidence"]), "abstain": f["abstain"],
            "frame_box_pct": ([float(v) for v in box]
                              if box is not None else None),
        })
    return norm_flags


def compare_v2(reader_flags, gt_entries, *,
               containment_min: float = CONTAINMENT_MIN,
               area_ratio_max: float = AREA_RATIO_MAX) -> dict:
    """一致性度量 v2（纯函数；advisory 分析，不是门）。

    在 v1 匹配规则上增加**面积比上限**：候选 (reader, GT) 对须同时满足
    containment(∩/GT 面积) ≥ containment_min 且
    读者框面积/GT框面积 ≤ area_ratio_max（同量级邻域，取值依据见
    AREA_RATIO_MAX_RATIONALE）；同类别内取满足双条件的 containment
    最大者为匹配。仅过 containment 而被面积比拒掉的旗标如实单列
    （reader_ratio_rejected_ids，附其被拒配对明细）。v1 度量与其产物
    原样保留（版本字段区分，不回写）。
    """
    if (isinstance(area_ratio_max, bool)
            or not isinstance(area_ratio_max, (int, float))
            or not float(area_ratio_max) > 0):
        raise ValueError(
            f"compare_v2: area_ratio_max 非法 {area_ratio_max!r}（要求 >0）")
    validate_gt_entries(gt_entries)
    norm_flags = _normalize_reader_flags(reader_flags)

    matches = []
    ratio_rejected: list = []
    gt_matched = {e["gt_id"]: None for e in gt_entries}
    fp_ids: list = []
    no_box_ids: list = []
    abstain_ids: list = []
    scored = 0
    for f in norm_flags:
        if f["abstain"]:
            abstain_ids.append(f["flag_id"])
            continue
        scored += 1
        if f["frame_box_pct"] is None:
            no_box_ids.append(f["flag_id"])
            continue
        best = None            # (gt_id, containment, area_ratio) 双条件通过
        rejected = None        # containment 通过但面积比拒
        for e in gt_entries:
            if e["category"] != f["category"]:
                continue
            c = _containment(f["frame_box_pct"], e["frame_box_pct"])
            if c is None or c < containment_min:
                continue
            ar = _area_ratio(f["frame_box_pct"], e["frame_box_pct"])
            if ar is not None and ar <= area_ratio_max:
                if best is None or c > best[1]:
                    best = (e["gt_id"], c, ar)
            elif rejected is None or c > rejected[1]:
                rejected = (e["gt_id"], c, ar)
        if best is not None:
            matches.append({"gt_id": best[0], "flag_id": f["flag_id"],
                            "category": f["category"],
                            "containment": _round6(best[1]),
                            "area_ratio": _round6(best[2])})
            if gt_matched[best[0]] is None:
                gt_matched[best[0]] = f["flag_id"]
        else:
            if rejected is not None:
                ratio_rejected.append(
                    {"flag_id": f["flag_id"], "gt_id": rejected[0],
                     "containment": _round6(rejected[1]),
                     "area_ratio": _round6(rejected[2])})
            fp_ids.append(f["flag_id"])
    missed = [gid for gid, m in gt_matched.items() if m is None]
    gt_n = len(gt_entries)
    return {
        "metric_version": METRIC_VERSION_V2,
        "containment_min": containment_min,
        "area_ratio_max": float(area_ratio_max),
        "area_ratio_max_rationale": AREA_RATIO_MAX_RATIONALE,
        "metric_definition": (
            "匹配=abstain=False 且类别相等且 containment(读者框∩GT框/"
            "GT框面积) ≥ containment_min 且 读者框面积/GT框面积 ≤ "
            "area_ratio_max（同量级邻域上限）；abstain 单列不参与匹配。"
            "度量 v2 先写死后跑（S20），阈值不后调；v1 度量与产物原样"
            "保留（版本字段区分）。面积比上限属 proposal_only，正式"
            "采纳须人工批准。"),
        "gt_count": gt_n,
        "reader_flag_count": len(norm_flags),
        "reader_scored_count": scored,
        "reader_abstain_ids": abstain_ids,
        "matches": matches,
        "gt_matched": {gid: m for gid, m in gt_matched.items()},
        "gt_missed_ids": missed,
        "gt_matched_count": gt_n - len(missed),
        "gt_recall": _ratio(gt_n - len(missed), gt_n),
        "reader_matched_ids": [m["flag_id"] for m in matches],
        "reader_unmatched_no_box_ids": no_box_ids,
        "reader_ratio_rejected_ids": [r["flag_id"] for r in ratio_rejected],
        "reader_ratio_rejected_detail": ratio_rejected,
        "reader_false_positive_ids": fp_ids,
        "reader_precision_vs_seed_gt": _ratio(
            len([m for m in matches]), scored) if scored else None,
        "coverage_caveat": COVERAGE_CAVEAT,
    }


# ---------------------------------------------------------------------------
# 度量 v3（P3-A）：v2 双条件 + 一对一确定性指派 + 视角可比 + 语义更名
# ---------------------------------------------------------------------------

def _validate_flag_views(flag_views, norm_flags) -> dict:
    """flag_views 映射校验（{flag_id: "top"|"bottom"}；非法 ValueError）。

    键必须为本次输入中真实存在的 flag_id（编排侧注入拼写错误即拒绝，
    fail-closed）；值仅 top/bottom；None/缺省=未提供视角映射（视角
    不设防，由输出 view_check 如实标注）。纯函数。
    """
    if flag_views is None:
        return {}
    if not isinstance(flag_views, dict):
        raise ValueError("compare_v3: flag_views 须为 {flag_id: 视角} "
                         "映射或 None")
    known = {f["flag_id"] for f in norm_flags}
    out: dict = {}
    for k, v in flag_views.items():
        if not isinstance(k, str) or not k:
            raise ValueError(f"compare_v3: flag_views 键非法 {k!r}")
        if k not in known:
            raise ValueError(f"compare_v3: flag_views 引用不存在的 "
                             f"flag_id {k!r}（fail-closed）")
        if v not in ("top", "bottom"):
            raise ValueError(f"compare_v3: flag_views[{k!r}] 视角非法 "
                             f"{v!r}（仅 top/bottom）")
        out[k] = v
    return out


def compare_v3(reader_flags, gt_entries, *,
               containment_min: float = CONTAINMENT_MIN,
               area_ratio_max: float = AREA_RATIO_MAX,
               flag_views=None) -> dict:
    """一致性度量 v3（纯函数；advisory 分析，不是门）。

    在 v2 双条件（containment ≥ containment_min 且面积比 ≤
    area_ratio_max，阈值沿用声明常量）之上修正比较器正确性缺口：

    1. **一对一确定性指派**：全部候选对按 (containment 降序, 面积比
       升序, flag_id 字典序升序, gt_id 字典序升序) 排序后贪心扫描，
       flag 与 gt 均未占用才成匹配——同一 GT 至多被一个旗标命中，
       同一旗标至多命中一个 GT；因一对一落选但存在候选对的旗标如实
       计入 duplicate_reports（不计入任何正确命中分母）；
    2. **视角可比**：flag_views（编排侧注入的 {flag_id: top|bottom}）
       与 gt.side 不符的对不入候选、记 view_mismatch；未提供映射或
       该旗标无视角 → 视角不设防（view_check 如实标注
       not_applicable/partial，不冒充已检查）；
    3. **输出语义更名**：未匹配旗标=unmatched/unadjudicated（不再
       命名 false_positive）；reader_precision_vs_seed_gt 更名
       seed_match_rate 并附口径注；abstain 块显式给出弃权率定义。

    v1/v2 度量与产物原样保留（版本字段区分，不回写）。
    """
    if (isinstance(area_ratio_max, bool)
            or not isinstance(area_ratio_max, (int, float))
            or not float(area_ratio_max) > 0):
        raise ValueError(
            f"compare_v3: area_ratio_max 非法 {area_ratio_max!r}（要求 >0）")
    validate_gt_entries(gt_entries)
    norm_flags = _normalize_reader_flags(reader_flags)
    view_map = _validate_flag_views(flag_views, norm_flags)

    abstain_ids: list = []
    scored_flags: list = []
    for f in norm_flags:
        if f["abstain"]:
            abstain_ids.append(f["flag_id"])
        else:
            scored_flags.append(f)

    # 候选对收集：v2 双条件 + 视角入围（全部确定性；浮点原值参与排序）
    candidates: list = []
    view_mismatch: list = []
    eligible_for_view = 0     # 非 abstain 且有框（视角检查的实际作用域）
    with_view = 0
    for f in scored_flags:
        if f["frame_box_pct"] is None:
            continue
        eligible_for_view += 1
        fv = view_map.get(f["flag_id"])
        if fv is not None:
            with_view += 1
        for e in gt_entries:
            if e["category"] != f["category"]:
                continue
            if fv is not None and fv != e["side"]:
                view_mismatch.append(
                    {"flag_id": f["flag_id"], "gt_id": e["gt_id"],
                     "flag_view": fv, "gt_side": e["side"]})
                continue
            c = _containment(f["frame_box_pct"], e["frame_box_pct"])
            if c is None or c < containment_min:
                continue
            ar = _area_ratio(f["frame_box_pct"], e["frame_box_pct"])
            if ar is None or ar > area_ratio_max:
                continue
            candidates.append({"flag_id": f["flag_id"], "gt_id": e["gt_id"],
                               "containment": c, "area_ratio": ar})
    view_mismatch.sort(key=lambda x: (x["flag_id"], x["gt_id"]))

    # 一对一确定性贪心指派
    candidates.sort(key=lambda p: (-p["containment"], p["area_ratio"],
                                   p["flag_id"], p["gt_id"]))
    matched_pairs: set = set()
    matched_flags: set = set()
    matched_gts: set = set()
    matches: list = []
    for p in candidates:
        if p["flag_id"] in matched_flags or p["gt_id"] in matched_gts:
            continue
        matched_flags.add(p["flag_id"])
        matched_gts.add(p["gt_id"])
        matched_pairs.add((p["flag_id"], p["gt_id"]))
        matches.append({"flag_id": p["flag_id"], "gt_id": p["gt_id"],
                        "category": next(f["category"] for f in scored_flags
                                         if f["flag_id"] == p["flag_id"]),
                        "containment": _round6(p["containment"]),
                        "area_ratio": _round6(p["area_ratio"])})

    # 因一对一落选但存在候选对的旗标：duplicate_reports（不进正确分母）
    duplicate_reports: list = []
    for p in candidates:
        if (p["flag_id"], p["gt_id"]) in matched_pairs:
            continue
        if p["flag_id"] in matched_flags:
            reason = "flag_already_matched"
        else:
            reason = "gt_already_matched"
        duplicate_reports.append(
            {"flag_id": p["flag_id"], "gt_id": p["gt_id"],
             "containment": _round6(p["containment"]),
             "area_ratio": _round6(p["area_ratio"]), "reason": reason})
    duplicate_reports.sort(key=lambda d: (d["flag_id"], d["gt_id"],
                                          -d["containment"]))

    # 无任何候选对的旗标 → unmatched/unadjudicated（不命名 false_positive）
    reader_unmatched_ids: list = []
    reader_unmatched_no_box_ids: list = []
    for f in scored_flags:
        if f["frame_box_pct"] is None:
            reader_unmatched_ids.append(f["flag_id"])
            reader_unmatched_no_box_ids.append(f["flag_id"])
        elif not any(p["flag_id"] == f["flag_id"] for p in candidates):
            reader_unmatched_ids.append(f["flag_id"])

    gt_matched = {e["gt_id"]: next(
        (m["flag_id"] for m in matches if m["gt_id"] == e["gt_id"]), None)
        for e in gt_entries}
    missed = [gid for gid, m in gt_matched.items() if m is None]
    gt_n = len(gt_entries)
    scored = len(scored_flags)
    if not view_map:
        view_check = "not_applicable"
    elif with_view >= eligible_for_view:
        view_check = "full"
    else:
        view_check = "partial"
    return {
        "metric_version": METRIC_VERSION_V3,
        "containment_min": float(containment_min),
        "area_ratio_max": float(area_ratio_max),
        "area_ratio_max_rationale": AREA_RATIO_MAX_RATIONALE,
        "metric_definition": V3_METRIC_DEFINITION,
        "gt_count": gt_n,
        "reader_flag_count": len(norm_flags),
        "reader_scored_count": scored,
        "abstain": {
            "abstain_ids": abstain_ids,
            "abstain_count": len(abstain_ids),
            "reader_flag_count": len(norm_flags),
            "abstain_rate": _ratio(len(abstain_ids), len(norm_flags)),
            "abstain_rate_definition": ABSTAIN_RATE_DEFINITION,
        },
        "matches": matches,
        "reader_matched_ids": [m["flag_id"] for m in matches],
        "duplicate_reports": duplicate_reports,
        "view_mismatch": view_mismatch,
        "view_check": view_check,
        "view_mapped_flag_count": with_view,
        "view_eligible_flag_count": eligible_for_view,
        "reader_unmatched_ids": reader_unmatched_ids,
        "reader_unmatched_no_box_ids": reader_unmatched_no_box_ids,
        "gt_matched": gt_matched,
        "gt_missed_ids": missed,
        "gt_matched_count": gt_n - len(missed),
        "gt_recall": _ratio(gt_n - len(missed), gt_n),
        "seed_match_rate": _ratio(len(matches), scored) if scored else None,
        "seed_metric_note": SEED_METRIC_NOTE,
        "coverage_caveat": COVERAGE_CAVEAT_V3,
    }


# ---------------------------------------------------------------------------
# CLI（stdin→stdout canonical JSON；零落盘）
# ---------------------------------------------------------------------------

def main() -> None:
    """比较器 CLI：stdin={reader_flags, gt_entries[, containment_min]
    [, metric_version][, area_ratio_max][, flag_views]}，stdout=
    canonical JSON 报告。

    metric_version 缺省=v1；=calibration-metric-v2 时走 compare_v2
    （此时 area_ratio_max 可选，缺省=AREA_RATIO_MAX 声明常量）；
    =calibration-metric-v3 时走 compare_v3（area_ratio_max 可选；
    flag_views 仅 v3 可用，缺省=None=视角不设防并如实标注）。
    正式校准轮必须用声明常量，任何覆盖值须在运行记录中如实声明。
    """
    text = __import__("sys").stdin.read()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("calibration CLI: stdin 必须为 JSON 对象")
    unknown = sorted(set(payload) - {"reader_flags", "gt_entries",
                                     "containment_min", "metric_version",
                                     "area_ratio_max", "flag_views"})
    if unknown:
        raise ValueError(f"calibration CLI: 未知键 {unknown}")
    metric_version = payload.get("metric_version", METRIC_VERSION)
    if metric_version not in (METRIC_VERSION, METRIC_VERSION_V2,
                              METRIC_VERSION_V3):
        raise ValueError(f"calibration CLI: 未知 metric_version "
                         f"{metric_version!r}（合法集 "
                         f"[{METRIC_VERSION}, {METRIC_VERSION_V2}, "
                         f"{METRIC_VERSION_V3}]）")
    if "area_ratio_max" in payload \
            and metric_version not in (METRIC_VERSION_V2,
                                       METRIC_VERSION_V3):
        raise ValueError("calibration CLI: area_ratio_max 仅 metric "
                         "v2/v3 可用")
    if "flag_views" in payload and metric_version != METRIC_VERSION_V3:
        raise ValueError("calibration CLI: flag_views 仅 metric v3 可用")
    containment_min = float(payload.get("containment_min",
                                        CONTAINMENT_MIN))
    if metric_version == METRIC_VERSION_V3:
        report = compare_v3(payload["reader_flags"], payload["gt_entries"],
                            containment_min=containment_min,
                            area_ratio_max=float(payload.get(
                                "area_ratio_max", AREA_RATIO_MAX)),
                            flag_views=payload.get("flag_views"))
    elif metric_version == METRIC_VERSION_V2:
        report = compare_v2(payload["reader_flags"], payload["gt_entries"],
                            containment_min=containment_min,
                            area_ratio_max=float(payload.get(
                                "area_ratio_max", AREA_RATIO_MAX)))
    else:
        report = compare(payload["reader_flags"], payload["gt_entries"],
                         containment_min=containment_min)
    __import__("sys").stdout.write(
        hashing.canonical_json_bytes(report).decode("utf-8"))


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

_XY_RE = re.compile(r"\(xy (-?[\d.]+) (-?[\d.]+)\)")
_PT_RE = re.compile(
    r"\((?:start|end|mid|center|xy) (-?[\d.]+) (-?[\d.]+)(?: (?:angle|"
    r"-?[\d.]+))?\)")


def _iter_sexprs(text: str, heads: tuple):
    """浅层 s 表达式迭代：按括号配对切出以指定头开始的完整表达式。

    头名后允许可为换行/制表（KiCad 多行缩进格式）或空格（单行格式）。
    """
    for head in heads:
        start = 0
        while True:
            i = text.find(f"({head}", start)
            if i < 0:
                break
            nxt = text[i + 1 + len(head):i + 2 + len(head)]
            if nxt and not nxt.isspace():
                start = i + 1
                continue
            depth = 0
            j = i
            while j < len(text):
                if text[j] == "(":
                    depth += 1
                elif text[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            yield text[i:j + 1]
            start = j + 1


def _unfilter(raw: bytes, w: int, h: int, bpp: int) -> list:
    rows = []
    prev = bytearray(bpp * w)
    pos = 0
    for _ in range(h):
        ftype = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + bpp * w])
        pos += bpp * w
        if ftype == 0:
            pass
        elif ftype == 1:
            for i in range(bpp, len(line)):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(len(line)):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(len(line)):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + (left + prev[i]) // 2) & 0xFF
        elif ftype == 4:
            for i in range(len(line)):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (
                    b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        else:
            raise ValueError(f"png unfilter: 未知滤波 {ftype}")
        rows.append(bytes(line))
        prev = line
    return rows


def _containment(a, g) -> float | None:
    """交集面积 / g 面积；不相交返回 None。"""
    ax0, ay0, ax1, ay1 = a
    gx0, gy0, gx1, gy1 = g
    ix0, iy0 = max(ax0, gx0), max(ay0, gy0)
    ix1, iy1 = min(ax1, gx1), min(ay1, gy1)
    if ix1 <= ix0 or iy1 <= iy0:
        return None
    inter = (ix1 - ix0) * (iy1 - iy0)
    garea = (gx1 - gx0) * (gy1 - gy0)
    if garea <= 0:
        return None
    return inter / garea


def _area_ratio(a, g) -> float | None:
    """读者框面积 / GT 框面积（同图幅百分比口径下与物理面积比相等：
    两框同乘图幅宽高因子后相除，宽高因子相消）；GT 框退化返回 None。"""
    garea = (g[2] - g[0]) * (g[3] - g[1])
    if garea <= 0:
        return None
    return ((a[2] - a[0]) * (a[3] - a[1])) / garea


def _ratio(num: int, den: int):
    return _round6(num / den) if den else None


def _round6(v: float) -> float:
    return round(float(v), 6)


if __name__ == "__main__":
    main()
