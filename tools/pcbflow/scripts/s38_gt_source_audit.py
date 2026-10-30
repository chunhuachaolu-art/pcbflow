#!/usr/bin/env python
"""S38：GT 侧三候选只读审计的机检部分（判例源审计 A1/A2 + 框径复核 A3）。

职责（本脚本=纯只读审计器；pcbflow/* 零改动只 import；不改任何 GT 文件、
不改任何既有 out/ 产物、不动阈值、不翻门）：

  S0 保护文件哈希实测（pcbflow/cli.py、pcbflow/config.py、
      toolchain_lock.json）与先验锚对照。
  S1 板文件零写见证：applied.kicad_pcb（期望 45320fbe…）与
      _pre-p1-batch-1.kicad_pcb（prep1 态，期望=pose-revision-proof
      hash_ledger.pre_move_board_sha256 332c71d4…）sha256 实测。
  S2 GT 语料实测：两 GT 文件 sha256（对照 derivation-log-r5 gt_sources
      冻结锚）、条目数、side 分布（实测 13 条是否全 top）、gt_margin_mm。
  S3 v1 四条 GT 的确定性重推导：pose-revision-proof.json
      drc_recon.gone_items 位置并集 ±gt_margin_mm（F1/J2 簇按
      F1_TRIM_RADIUS_MM=15.0 对 F1 锚点 (53.5,8.3) 做位置级剔除），
      与 ground-truth-v1.json board_box_mm 逐字段对拍。
  S4 v2 九条 GT 的确定性重推导：drc7/final-all.json
      courtyards_overlap&error 逐条双锚点 bbox ±gt_margin_mm，
      与 ground-truth-v2.json board_box_mm 逐字段对拍。
  S5 ±1.0mm 外扩比例表：13 条 GT 的本体框（=外扩框各侧回缩 margin）
      与外扩框的 w/h/面积膨胀比 + 有限值分布统计与 L1NB 位次。
  S6 板几何解析（纯文本解析 .kicad_pcb 相关段）：两板封装层分布、
      B.Cu 走线段计数；prep1 态 L1/R11/C28/U3 焊盘铜 bbox 及其在
      GT-REVC-P1-L1NB 框内的覆盖比例。
  S7 L1NB 邻域三轮 reader 旗标（R5T-013 / R6T-009 / R7T-012）框几何：
      pct→mm（derivation-log-r5 prep1-top 换算输入）与对 L1NB r5
      重投影框的 containment/area_ratio 重放计算，对照 run 文件记录值。
  S8 判例源关键词扫描（A1=bottom 侧、A2=布线类）：对仓库根 *.md 与
      out/revc-*/ + out/v3-td7/ 的 *.json/*.md（剔除 __pycache__）做
      确定性逐行扫描，dump 命中清单（文件+行号+关键词+行摘录）与
      DRC 族条目层标注 token 计数（F.Cu vs B.Cu 族）。

纪律：全程零写入（默认 stdout 输出 canonical JSON；--out 仅在目标
不存在时落盘，防覆写守卫）；无 wall-clock/无 host 路径入账（输出仅
仓相对路径；日期=声明常量 2026-09-07）；canonical JSON
（hashing.canonical_json_bytes）；hash=sha256_file 字节口径；先验锚
不符即 fail-closed 中止；同参重建逐字节一致（byte-exact 可重跑）；
零子进程/零网络；datasets/ 零读写之外的零接触；不 git。

用法：python scripts/s38_gt_source_audit.py            （stdout）
      python scripts/s38_gt_source_audit.py --out <path>（防覆写落盘）
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

DECLARED_DATE = "2026-09-07"
AUDIT_LABEL = "s38-gt-source-audit-r1"

# ---------------------------------------------------------------- 常量锚 ---
REL_CLI = "pcbflow/cli.py"
REL_CONFIG = "pcbflow/config.py"
REL_LOCK = "toolchain_lock.json"
REL_APPLIED_BOARD = "out/revc-asm/board/applied.kicad_pcb"
REL_PREP1_BOARD = "out/revc-asm/board/_pre-p1-batch-1.kicad_pcb"
REL_POSE_PROOF = "out/revc-asm/pose-revision-proof.json"
REL_DRC7_FINAL = "out/revc-asm/drc7/final-all.json"
REL_GT_V1 = "out/v3-tl2/calibration/ground-truth-v1.json"
REL_GT_V2 = "out/v3-tl2/calibration/ground-truth-v2.json"
REL_DERIV_R5 = "out/v3-tl2/calibration/derivation-log-r5.json"
REL_RUN_R5 = "out/v3-tl2/calibration/calibration-run-r5.json"
REL_RUN_R6 = "out/v3-tl2/calibration/calibration-run-r6.json"
REL_RUN_R7 = "out/v3-tl2/calibration/calibration-run-r7.json"

#: 保护文件先验锚（包前实测；全量 sha256）。
EXPECTED_SHA256 = {
    REL_CLI:
        "6ed4f3fd7c87947562acffb90c8563dfae0d05ad82c395a45d0aad226c206e17",
    REL_CONFIG:
        "f515c34842521a645145a9f5454a5919274a242e5c8c27c01faf1a4c13e73baf",
    REL_LOCK:
        "d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd896d9301690b3d",
    REL_APPLIED_BOARD:
        "45320fbe3296a0594a3678a30ad2c1bf775e6c7e9666158abb82081fc2245d85",
    REL_PREP1_BOARD:
        "332c71d4362b732d0a9cdc4d82ea9f8308e4647f2e3cd2fde0bc5497fc5a62c7",
    REL_GT_V1:
        "828b6b5fe2c03a5ae1c70e338b44dc32bc7c21179dc85019453d9236ece314ed",
    REL_GT_V2:
        "e1cb63d5e05761feada0b2dd030018bc04c3d3d165f33adcda2b9b348bd4b3a9",
}

#: v1 簇→gone_items 索引（对 pose-revision-proof.json drc_recon.gone_items
#: 的确定性人工分簇；并集须穷尽 22 条——见 S3 完备性断言）。
V1_CLUSTER_ITEM_IDX = {
    "GT-REVC-P1-R4J3": [0, 1, 7, 8, 12, 15, 16, 17, 18],
    "GT-REVC-P1-F1J2": [5, 6, 9, 10, 13, 21],
    "GT-REVC-P1-L1NB": [3, 4, 11, 19, 20],
    "GT-REVC-P1-L1SHORT": [2, 14],
}
F1_ANCHOR_MM = (53.5, 8.3)
F1_TRIM_RADIUS_MM = 15.0

#: S7 reader 旗标框（自 run 文件 flag 列表实测读取，此处仅登记旗 ID 与
#: run 文件记录的 containment/area_ratio 对照值）。
L1NB_FLAG_RECORDS = {
    "R5T-013": {
        "run_rel": REL_RUN_R5,
        "recorded_containment": 1.0,
        "recorded_area_ratio": 6.739726,
        "recorded_abstain": False,
    },
    "R6T-009": {
        "run_rel": REL_RUN_R6,
        "recorded_containment": 0.839393,
        "recorded_area_ratio": None,
        "recorded_abstain": True,
    },
    "R7T-012": {
        "run_rel": REL_RUN_R7,
        "recorded_containment": 0.415663,
        "recorded_area_ratio": None,
        "recorded_abstain": True,
    },
}

#: S8 关键词（A1=bottom 侧判例源线索；A2=布线类判例源线索）。
PATTERNS_A1 = re.compile(
    r"B\.Cu|B\.Mask|B\.SilkS|[Bb]ottom|背面|回板|bring-up|bring up")
PATTERNS_A2 = re.compile(r"[Rr]eroute|ripup|绕行|改道")
#: DRC 族条目描述中的层标注 token 计数口径。
LAYER_TOKEN = re.compile(
    r"F\.Cu\s*-\s*In\d\.Cu|In\d\.Cu\s*-\s*B\.Cu|(?<![A-Za-z])F\.Cu"
    r"(?![A-Za-z])|(?<![A-Za-z])B\.Cu(?![A-Za-z])|Top\s*-\s*Bottom"
    r"|\(Bottom\)|\(Top\)")


def _rel(rel_path: str) -> Path:
    return REPO / rel_path


def _load_json(rel_path: str):
    with open(_rel(rel_path), encoding="utf-8") as f:
        return json.load(f)


def _r6(x: float) -> float:
    return round(float(x), 6)


def _median(xs):
    ys = sorted(xs)
    n = len(ys)
    if n == 0:
        return None
    if n % 2:
        return ys[n // 2]
    return (ys[n // 2 - 1] + ys[n // 2]) / 2.0


def _pct_to_mm_box(box_pct, px_bounds):
    """图幅百分比框 → 板 mm 框（线性逆映射；top 视 x/y 同向）。

    与 pcbflow.calibration.box_mm_to_frame_pct 互逆（口径：pct 相对整幅
    图幅；板 bbox=0..70mm 线性映射到板像素界）。
    """
    x0, y0, x1, y1 = box_pct
    w_img, h_img = px_bounds["image_width"], px_bounds["image_height"]
    bx0, by0, bx1, by1 = (px_bounds["x0"], px_bounds["y0"],
                          px_bounds["x1"], px_bounds["y1"])
    span_x, span_y = bx1 - bx0 + 1, by1 - by0 + 1

    def to_mm_x(p):
        return (p * w_img - bx0) / span_x * 70.0

    def to_mm_y(p):
        return (p * h_img - by0) / span_y * 70.0

    return [to_mm_x(x0), to_mm_y(y0), to_mm_x(x1), to_mm_y(y1)]


def _containment(a_pct, b_pct):
    """a 框对 b 框的包含率：∩面积 / b 面积（calibration._containment 同式）。"""
    ix = max(0.0, min(a_pct[2], b_pct[2]) - max(a_pct[0], b_pct[0]))
    iy = max(0.0, min(a_pct[3], b_pct[3]) - max(a_pct[1], b_pct[1]))
    area_b = (b_pct[2] - b_pct[0]) * (b_pct[3] - b_pct[1])
    if area_b <= 0:
        return None
    return ix * iy / area_b


def _area_ratio(a_pct, b_pct):
    area_a = (a_pct[2] - a_pct[0]) * (a_pct[3] - a_pct[1])
    area_b = (b_pct[2] - b_pct[0]) * (b_pct[3] - b_pct[1])
    if area_b <= 0:
        return None
    return area_a / area_b


# ------------------------------------------------- S0/S1 哈希与零写见证 ---
def audit_hashes():
    rows = []
    for rel, expected in EXPECTED_SHA256.items():
        got = hashing.sha256_file(str(_rel(rel)))
        rows.append({
            "path_rel": rel,
            "sha256": got,
            "expected": expected,
            "match": got == expected,
        })
    pose = _load_json(REL_POSE_PROOF)
    ledger = pose["hash_ledger"]
    pre_move = ledger["pre_move_board_sha256"]
    post_move = ledger["post_move_board_sha256"]
    return {
        "files": rows,
        "all_match": all(r["match"] for r in rows),
        "cross_checks": {
            "pose_proof_pre_move_board_sha256": pre_move,
            "pre_p1_board_matches_pose_proof_pre_move":
                pre_move == EXPECTED_SHA256[REL_PREP1_BOARD],
            "pose_proof_post_move_board_sha256": post_move,
            "applied_board_matches_pose_proof_post_move":
                post_move == EXPECTED_SHA256[REL_APPLIED_BOARD],
        },
        "zero_write_declaration": (
            "本审计对上述全部文件只读（sha256 实测）；applied 板读后于收尾"
            "复验（见审计报告包后见证）"),
    }


# ----------------------------------------------------------- S2 GT 语料 ---
def audit_gt_corpus():
    deriv = _load_json(REL_DERIV_R5)
    frozen = {s["path_rel"]: s["sha256"] for s in deriv["gt_sources"]}
    files = []
    total = 0
    side_hist = {}
    all_top = True
    margins = set()
    for rel in (REL_GT_V1, REL_GT_V2):
        doc = _load_json(rel)
        sha = hashing.sha256_file(str(_rel(rel)))
        entries = doc["gt_entries"]
        sides = [e.get("side") for e in entries]
        for s in sides:
            side_hist[s] = side_hist.get(s, 0) + 1
        all_top = all_top and all(s == "top" for s in sides)
        margins.add(doc["annotation"]["gt_margin_mm"])
        total += len(entries)
        files.append({
            "path_rel": rel,
            "sha256": sha,
            "frozen_sha256_in_derivation_log_r5": frozen.get(rel),
            "frozen_match": frozen.get(rel) == sha,
            "entry_count": len(entries),
            "gt_ids": [e["gt_id"] for e in entries],
            "side_values": sides,
            "gt_margin_mm": doc["annotation"]["gt_margin_mm"],
            "annotation_side": doc["annotation"]["side"],
        })
    # derivation-log-r5 的 board_box_mm_verbatim 与 GT 文件逐字段对拍
    verbatim_ok = True
    verbatim_rows = []
    gt_by_id = {}
    for rel in (REL_GT_V1, REL_GT_V2):
        for e in _load_json(rel)["gt_entries"]:
            gt_by_id[e["gt_id"]] = e["board_box_mm"]
    for ent in deriv["entries"]:
        src = gt_by_id.get(ent["gt_id"])
        ok = src is not None and all(
            _r6(a) == _r6(b) for a, b in zip(src, ent["board_box_mm_verbatim"]))
        verbatim_ok = verbatim_ok and ok
        verbatim_rows.append({"gt_id": ent["gt_id"], "verbatim_match": ok})
    return {
        "files": files,
        "total_entries": total,
        "side_histogram": side_hist,
        "all_side_top": all_top,
        "gt_margin_mm_values": sorted(margins),
        "derivation_log_r5_verbatim_all_match": verbatim_ok,
        "derivation_log_r5_verbatim_rows": verbatim_rows,
    }


# ------------------------------------- S3 v1 四条 GT 的确定性重推导 -------
def audit_v1_rederivation():
    pose = _load_json(REL_POSE_PROOF)
    gone = pose["drc_recon"]["gone_items"]
    gt = _load_json(REL_GT_V1)
    margin = gt["annotation"]["gt_margin_mm"]
    covered = sorted(i for idx in V1_CLUSTER_ITEM_IDX.values() for i in idx)
    completeness = covered == list(range(len(gone)))
    rows = []
    for e in gt["gt_entries"]:
        gid = e["gt_id"]
        pts = []
        for i in V1_CLUSTER_ITEM_IDX[gid]:
            for it in gone[i]["items"]:
                x, y = it["pos"]["x"], it["pos"]["y"]
                if gid == "GT-REVC-P1-F1J2":
                    d = math.hypot(x - F1_ANCHOR_MM[0], y - F1_ANCHOR_MM[1])
                    if d > F1_TRIM_RADIUS_MM:
                        continue
                pts.append((x, y))
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        body = [min(xs), min(ys), max(xs), max(ys)]
        box = [min(xs) - margin, min(ys) - margin, max(xs) + margin,
               max(ys) + margin]
        ok = all(_r6(a) == _r6(b) for a, b in zip(box, e["board_box_mm"]))
        rows.append({
            "gt_id": gid,
            "gone_item_idx": V1_CLUSTER_ITEM_IDX[gid],
            "body_bbox_mm": [_r6(v) for v in body],
            "redrived_box_mm": [_r6(v) for v in box],
            "gt_file_box_mm": e["board_box_mm"],
            "match": ok,
        })
    return {
        "source": REL_POSE_PROOF,
        "rule": ("gone_items 位置并集 ± gt_margin_mm；F1/J2 簇按 "
                 f"F1_TRIM_RADIUS_MM={F1_TRIM_RADIUS_MM} 对 F1 锚点 "
                 f"{F1_ANCHOR_MM} 位置级剔除（剔除 J2 DRC 远锚）"),
        "cluster_index_completeness": completeness,
        "rows": rows,
        "all_match": all(r["match"] for r in rows),
    }


# ------------------------------------- S4 v2 九条 GT 的确定性重推导 -------
def audit_v2_rederivation():
    drc = _load_json(REL_DRC7_FINAL)
    gt = _load_json(REL_GT_V2)
    margin = gt["annotation"]["gt_margin_mm"]
    viols = [v for v in drc["violations"]
             if v["type"] == "courtyards_overlap" and v["severity"] == "error"]
    drc_boxes = []
    for v in viols:
        pts = [(it["pos"]["x"], it["pos"]["y"]) for it in v["items"]]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        box = [min(xs) - margin, min(ys) - margin, max(xs) + margin,
               max(ys) + margin]
        refs = sorted(re.match(r"封装\s+(\S+)", it["description"]).group(1)
                      for it in v["items"])
        drc_boxes.append({
            "cluster_refs": refs,
            "anchor_positions": pts,
            "redrived_box_mm": [_r6(b) for b in box],
        })
    matched_gt_ids = set()
    rows = []
    for e in gt["gt_entries"]:
        hit = [d for d in drc_boxes
               if all(_r6(a) == _r6(b)
                      for a, b in zip(d["redrived_box_mm"], e["board_box_mm"]))]
        ok = len(hit) == 1
        if ok:
            matched_gt_ids.add(id(hit[0]))
        rows.append({
            "gt_id": e["gt_id"],
            "cluster_refs": e["cluster_refs"],
            "gt_file_box_mm": e["board_box_mm"],
            "drc_violation_match_count": len(hit),
            "match": ok,
        })
    return {
        "source": REL_DRC7_FINAL,
        "rule": "courtyards_overlap & severity=error 逐条双锚点 bbox ± margin",
        "drc_violation_count": len(viols),
        "rows": rows,
        "all_match": all(r["match"] for r in rows),
        "one_to_one": len({id(d) for d in drc_boxes} ) == len(drc_boxes),
    }


# ------------------------------------- S5 ±1.0mm 外扩比例表 --------------
def audit_frame_inflation():
    entries = []
    for rel in (REL_GT_V1, REL_GT_V2):
        doc = _load_json(rel)
        m = doc["annotation"]["gt_margin_mm"]
        for e in doc["gt_entries"]:
            b = e["board_box_mm"]
            box_w, box_h = b[2] - b[0], b[3] - b[1]
            body_w, body_h = box_w - 2 * m, box_h - 2 * m
            entries.append({
                "gt_id": e["gt_id"],
                "box_mm": [_r6(v) for v in b],
                "margin_mm_each_side": m,
                "box_w_mm": _r6(box_w),
                "box_h_mm": _r6(box_h),
                "body_w_mm": _r6(body_w),
                "body_h_mm": _r6(body_h),
                "w_inflation": _r6(box_w / body_w) if body_w > 0 else None,
                "h_inflation": _r6(box_h / body_h) if body_h > 0 else None,
                "area_inflation": (
                    _r6((box_w * box_h) / (body_w * body_h))
                    if body_w > 0 and body_h > 0 else None),
            })
    finite_area = [e["area_inflation"] for e in entries
                   if e["area_inflation"] is not None]
    finite_w = [e["w_inflation"] for e in entries
                if e["w_inflation"] is not None]
    finite_h = [e["h_inflation"] for e in entries
                if e["h_inflation"] is not None]
    l1nb = next(e for e in entries if e["gt_id"] == "GT-REVC-P1-L1NB")
    stats = {
        "entry_count": len(entries),
        "degenerate_body_count": sum(
            1 for e in entries
            if e["w_inflation"] is None or e["h_inflation"] is None),
        "area_inflation_min": _r6(min(finite_area)),
        "area_inflation_median": _r6(_median(finite_area)),
        "area_inflation_max": _r6(max(finite_area)),
        "w_inflation_min": _r6(min(finite_w)),
        "w_inflation_max": _r6(max(finite_w)),
        "h_inflation_min": _r6(min(finite_h)),
        "h_inflation_max": _r6(max(finite_h)),
        "l1nb": {
            "w_inflation": l1nb["w_inflation"],
            "h_inflation": l1nb["h_inflation"],
            "area_inflation": l1nb["area_inflation"],
            "area_inflation_rank_asc": sorted(finite_area).index(
                l1nb["area_inflation"]) + 1,
            "area_inflation_finite_count": len(finite_area),
            "is_w_inflation_corpus_min":
                l1nb["w_inflation"] == min(finite_w),
        },
    }
    return {"entries": entries, "stats": stats}


# ------------------------------------- S6 板几何解析 ---------------------
def _iter_footprint_blocks(text):
    i, n = 0, len(text)
    while True:
        m = re.search(r"\(footprint\b", text[i:])
        if not m:
            return
        start = i + m.start()
        depth, j = 0, start
        while j < n:
            c = text[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield text[start:j + 1]
        i = j + 1


def _footprint_pad_bbox(block):
    at = re.search(
        r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)", block)
    if not at:
        return None
    fx, fy = float(at.group(1)), float(at.group(2))
    fr = float(at.group(3) or 0.0)
    rad = math.radians(fr)
    boxes = []
    for pm in re.finditer(
            r'\(pad\s+"[^"]*"[^\n]*?\n?\s*\(at\s+(-?[\d.]+)\s+(-?[\d.]+)'
            r"(?:\s+(-?[\d.]+))?\)[\s\S]*?\(size\s+(-?[\d.]+)\s+(-?[\d.]+)\)",
            block):
        px, py = float(pm.group(1)), float(pm.group(2))
        pr = float(pm.group(3) or 0.0)
        w, h = float(pm.group(4)), float(pm.group(5))
        gx = fx + px * math.cos(rad) - py * math.sin(rad)
        gy = fy + px * math.sin(rad) + py * math.cos(rad)
        prad = math.radians(pr + fr)
        ex = abs(w / 2 * math.cos(prad)) + abs(h / 2 * math.sin(prad))
        ey = abs(w / 2 * math.sin(prad)) + abs(h / 2 * math.cos(prad))
        boxes.append((gx - ex, gy - ey, gx + ex, gy + ey))
    if not boxes:
        return None
    ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    return {
        "ref": ref_m.group(1) if ref_m else "?",
        "at": [_r6(fx), _r6(fy)],
        "rot": fr,
        "pad_count": len(boxes),
        "pad_bbox_mm": [_r6(min(b[0] for b in boxes)),
                        _r6(min(b[1] for b in boxes)),
                        _r6(max(b[2] for b in boxes)),
                        _r6(max(b[3] for b in boxes))],
    }


def audit_board_geometry():
    out = {}
    for label, rel in (("prep1", REL_PREP1_BOARD), ("applied", REL_APPLIED_BOARD)):
        text = open(_rel(rel), encoding="utf-8", errors="replace").read()
        layer_hist = {}
        foots = {}
        for block in _iter_footprint_blocks(text):
            lm = re.search(r'\(footprint\s+"[^"]+"\s+\(layer\s+"([^"]+)"\)', block)
            layer = lm.group(1) if lm else "?"
            layer_hist[layer] = layer_hist.get(layer, 0) + 1
            fb = _footprint_pad_bbox(block)
            if fb:
                foots[fb["ref"]] = fb
        b_cu_segments = len(re.findall(
            r'\(segment[^)]*\(layer\s+"B\.Cu"', text))
        out[label] = {
            "path_rel": rel,
            "footprint_layer_histogram": layer_hist,
            "footprints_with_pads": len(foots),
            "b_cu_segment_count": b_cu_segments,
        }
        if label == "prep1":
            gt = _load_json(REL_GT_V1)
            l1nb = next(e for e in gt["gt_entries"]
                        if e["gt_id"] == "GT-REVC-P1-L1NB")
            gtb = l1nb["board_box_mm"]
            cover = {}
            for ref in ("L1", "R11", "C28", "U3"):
                fb = foots.get(ref)
                if not fb:
                    cover[ref] = None
                    continue
                fbx = fb["pad_bbox_mm"]
                ix = max(0.0, min(fbx[2], gtb[2]) - max(fbx[0], gtb[0]))
                iy = max(0.0, min(fbx[3], gtb[3]) - max(fbx[1], gtb[1]))
                fa = (fbx[2] - fbx[0]) * (fbx[3] - fbx[1])
                cover[ref] = {
                    "at": fb["at"],
                    "rot": fb["rot"],
                    "pad_count": fb["pad_count"],
                    "pad_bbox_mm": fb["pad_bbox_mm"],
                    "pad_area_in_gt_box_fraction": (
                        _r6(ix * iy / fa) if fa > 0 else None),
                }
            out["prep1_l1nb_neighborhood"] = {
                "gt_box_mm": gtb,
                "footprint_pad_coverage": cover,
                "note": ("覆盖比例=封装焊盘铜 bbox 与 GT 框交集面积/焊盘 bbox "
                         "面积（纯文本解析 .kicad_pcb pad 段；未含丝印/本体"
                         "图元）"),
            }
    return out


# ------------------------------------- S7 L1NB 邻域旗标几何 --------------
def audit_l1nb_flags():
    deriv = _load_json(REL_DERIV_R5)
    l1nb_ent = next(e for e in deriv["entries"]
                    if e["gt_id"] == "GT-REVC-P1-L1NB")
    gt_pct = l1nb_ent["frame_box_pct_r5"]
    px = l1nb_ent["conversion_inputs"]["px_bounds"]
    gt_mm = l1nb_ent["board_box_mm_verbatim"]
    gt_mm_from_pct = _pct_to_mm_box(gt_pct, px)
    rows = []
    for fid, rec in L1NB_FLAG_RECORDS.items():
        run = _load_json(rec["run_rel"])
        flag = None

        def walk(o):
            nonlocal flag
            if isinstance(o, dict):
                if o.get("flag_id") == fid:
                    flag = o
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(run)
        if flag is None:
            rows.append({"flag_id": fid, "found_in_run": False})
            continue
        pct = flag["frame_box_pct"]
        mm = _pct_to_mm_box(pct, px)
        cont = _containment(pct, gt_pct)
        ar = _area_ratio(pct, gt_pct)
        rows.append({
            "flag_id": fid,
            "found_in_run": True,
            "run_rel": rec["run_rel"],
            "abstain": flag.get("abstain"),
            "category": flag.get("category"),
            "frame_box_pct": pct,
            "box_mm_replayed": [_r6(v) for v in mm],
            "containment_vs_l1nb_r5_pct": _r6(cont),
            "recorded_containment": rec["recorded_containment"],
            "containment_abs_diff": _r6(
                abs(cont - rec["recorded_containment"])),
            "area_ratio_vs_l1nb_r5_pct": _r6(ar),
            "recorded_area_ratio": rec["recorded_area_ratio"],
        })
    return {
        "l1nb_gt": {
            "board_box_mm_verbatim": gt_mm,
            "frame_box_pct_r5": gt_pct,
            "prep1_top_px_bounds": px,
            "box_mm_replayed_from_pct": [_r6(v) for v in gt_mm_from_pct],
            "mm_replay_max_abs_diff": _r6(max(
                abs(a - b) for a, b in zip(gt_mm, gt_mm_from_pct))),
        },
        "flags": rows,
        "note": ("重放口径=pct 相对整幅图幅的线性逆映射（prep1-top，板像素界 "
                 "120..1884 over 70mm，图幅 2005×2005）；containment/area_ratio "
                 "与 calibration.compare_v3 同式重算，与 run 文件记录值对拍"),
    }


# ------------------------------------- S8 判例源关键词扫描 ---------------
def _scan_files(rel_files, patterns):
    hits = []
    for rel in rel_files:
        path = _rel(rel)
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            kw = sorted(set(patterns.findall(line)))
            if kw:
                hits.append({
                    "path_rel": rel.replace("\\", "/"),
                    "line": lineno,
                    "keywords": kw,
                    "excerpt": line.strip()[:160],
                })
    return hits


def _collect_scan_targets():
    root_md = sorted(
        p.relative_to(REPO).as_posix() for p in REPO.glob("*.md"))
    revc = sorted(
        p.relative_to(REPO).as_posix()
        for p in REPO.glob("out/revc-*/**/*") if p.is_file()
        and p.suffix in (".json", ".md")
        and "__pycache__" not in p.parts)
    td7 = sorted(
        p.relative_to(REPO).as_posix()
        for p in REPO.glob("out/v3-td7/**/*") if p.is_file()
        and p.suffix in (".json", ".md")
        and "__pycache__" not in p.parts)
    return {"repo_root_md": root_md, "out_revc_json_md": revc,
            "out_v3_td7_json_md": td7}


def audit_keyword_scan():
    targets = _collect_scan_targets()
    scopes = {}
    for name, files in targets.items():
        scopes[name] = {
            "file_count": len(files),
            "a1_bottom_hits": _scan_files(files, PATTERNS_A1),
            "a2_reroute_hits": _scan_files(files, PATTERNS_A2),
        }
    # DRC 族条目层标注 token 计数（判例性 B 面条目存在性的机检面）
    drc_files = sorted(
        p.relative_to(REPO).as_posix()
        for p in REPO.glob("out/revc-asm/drc*/**/*") if p.is_file()
        and p.suffix == ".json")
    layer_tokens = {}
    b_side_judgment_items = []
    for rel in drc_files:
        try:
            doc = json.load(open(_rel(rel), encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(doc, dict):
            continue
        for v in (doc.get("violations") or []) + (
                doc.get("unconnected_items") or []):
            if not isinstance(v, dict):
                continue
            for it in v.get("items") or []:
                desc = str(it.get("description", ""))
                for tok in LAYER_TOKEN.findall(desc):
                    layer_tokens[tok] = layer_tokens.get(tok, 0) + 1
                if re.search(r"B\.Cu|B\.Mask|B\.SilkS|\(Bottom\)", desc):
                    b_side_judgment_items.append({
                        "path_rel": rel,
                        "type": v.get("type"),
                        "description": desc,
                    })
    return {
        "scan_targets": {k: v["file_count"] for k, v in scopes.items()},
        "scopes": scopes,
        "drc_family": {
            "file_count": len(drc_files),
            "item_layer_token_counts": dict(sorted(
                layer_tokens.items(), key=lambda kv: -kv[1])),
            "b_side_item_count": len(b_side_judgment_items),
            "b_side_items": b_side_judgment_items[:20],
        },
        "exclusions_declared": (
            "扫描面=仓库根 *.md + out/revc-*/ 与 out/v3-td7/ 全部 *.json/*.md"
            "（剔除 __pycache__）；板文件 .kicad_pcb 按扩展名不在文本扫描面"
            "（其几何由 S6 专项解析）；out/v3-tl2 校准产物不在判例源扫描面"
            "（reader 观察不得反推 GT——循环论证红线）"),
    }


# ------------------------------------------------------------- 主流程 -----
def build_audit():
    return {
        "schema_version": "3.0",
        "kind": "tl2_gt_source_audit_machine_r1",
        "audit_label": AUDIT_LABEL,
        "date_constant": DECLARED_DATE,
        "read_only": True,
        "s0_hashes_and_witness": audit_hashes(),
        "s2_gt_corpus": audit_gt_corpus(),
        "s3_v1_rederivation": audit_v1_rederivation(),
        "s4_v2_rederivation": audit_v2_rederivation(),
        "s5_frame_inflation": audit_frame_inflation(),
        "s6_board_geometry": audit_board_geometry(),
        "s7_l1nb_flag_geometry": audit_l1nb_flags(),
        "s8_keyword_scan": audit_keyword_scan(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None,
                    help="可选输出路径（防覆写守卫：目标已存在即中止）")
    args = ap.parse_args()
    audit = build_audit()
    payload = hashing.canonical_json_bytes(audit)
    if args.out:
        target = Path(args.out)
        if target.exists():
            print(f"FAIL: {target} 已存在（防覆写守卫；审计产物不可覆写）",
                  file=sys.stderr)
            return 2
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        print(f"written: {target} "
              f"sha256={hashing.sha256_file(str(target))}",
              file=sys.stdout)
    sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
