#!/usr/bin/env python
"""S17-T3：校准域种子集 calibration-domain-v1（写 out/v3-tl2/calibration/）。

三步（库侧 pcbflow/calibration.py 保持纯函数零落盘零子进程）：

  render    源板 out/revc-asm/board/_pre-p1-batch-1.kicad_pcb（332c71d4，
            ASM-P1 批次 1 前态：R4↔J3、F1↔J2、L1 三簇已知缺陷态）staging
            逐字节拷贝 → kicad-cli pcb render 顶/底 PNG → renders/；
            板像素界由 PNG 背景差分扫描确定性测得（framing 记录）。
            **标注与 render 均不做任何视觉判读**（确定性换算，不亲读）。
  annotate  从 out/revc-asm/pose-revision-proof.json 的 drc_recon.gone_items
            （前态已确证缺陷；只读 gone、排除 new=后态引入项）按簇过滤
            规则提取判例坐标 → bbox+固定外扩 → 板坐标→图幅百分比确定性
            换算 → ground-truth-v1.json（带 provenance sha256_file）。
  manifest  calibration-domain-v1.json：版本化+provenance/split 声明。

纪律：既有 out/ 只读（新产物只进 out/v3-tl2/calibration/）；源板零写
（staging 渲染后清理）；无 wall-clock 无主机路径；防覆写。

用法：python scripts/s17_calibration.py render|annotate|manifest
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import calibration, critic, hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
RENDERS_DIR = CAL_DIR / "renders"
STAGING_DIR = CAL_DIR / "staging"
FRAMING = CAL_DIR / "render-framing.json"
GT_OUT = CAL_DIR / "ground-truth-v1.json"
MANIFEST_OUT = CAL_DIR / "calibration-domain-v1.json"

KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_VERSION = "10.0.5"
RENDER_SIZE = (1600, 900)
MIN_SIZE = (1200, 675)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

BOARD_REL = "out/revc-asm/board/_pre-p1-batch-1.kicad_pcb"
PROOF_REL = "out/revc-asm/pose-revision-proof.json"
RIPUP_REL = "out/revc-asm/ripup-reroute-ledger.json"
RESIDUAL_REL = "out/revc-asm/residual-ledger.json"
WARNING_REL = "out/revc-asm/warning-disposition.json"
PREFIX = "revc-prep1"

#: 判例证据源（GT 的 provenance；GT 条目 basis_refs 引用其逻辑名）
PROVENANCE_SOURCES = (
    ("pose_revision_proof", PROOF_REL),
    ("ripup_reroute_ledger", RIPUP_REL),
    ("residual_ledger", RESIDUAL_REL),
    ("warning_disposition", WARNING_REL),
)

#: 簇过滤规则（确定性；只取 drc_recon.gone_items=前态已确证缺陷）
PLACEMENT_TYPES = {"shorting_items", "clearance", "courtyards_overlap",
                   "pth_inside_courtyard", "solder_mask_bridge",
                   "silk_over_copper", "silk_overlap"}
F1_ANCHOR = (53.5, 8.3)      # F1 footprint 前态位姿（proof.moves.rows F1 from）
F1_TRIM_RADIUS_MM = 15.0     # J2 的 DRC 锚点（pad1/近端丝印，x≈6-8）远离
                             # 实际重叠区；超 15mm 位置剔除（确定性规则）


def _fail(msg: str) -> None:
    print(f"[s17-cal] FAIL: {msg}")
    sys.exit(1)


def _write_canonical(path: Path, obj) -> str:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def _png_size(path: Path) -> tuple:
    data = path.read_bytes()
    if not data.startswith(PNG_MAGIC):
        _fail(f"{path.name}: 不是 PNG（magic 不符）")
    w, h = struct.unpack(">II", data[16:24])
    return w, h


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def cmd_render() -> None:
    if FRAMING.exists():
        _fail("render-framing.json 已存在（防覆写）")
    if not KICAD_CLI.exists():
        _fail(f"kicad-cli 不存在：{KICAD_CLI}")
    src = REPO / BOARD_REL
    if not src.is_file():
        _fail(f"源板缺失：{BOARD_REL}")
    src_sha = hashing.sha256_file(str(src))
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    staged = STAGING_DIR / "revc-pre-p1.kicad_pcb"
    shutil.copyfile(src, staged)
    if hashing.sha256_file(str(staged)) != src_sha:
        _fail("staging 逐字节断言失败")

    # Edge.Cuts bbox（从 staging 文本解析；与源板同字节）
    board_bbox = calibration.board_edge_bbox_mm(
        staged.read_text(encoding="utf-8"))

    renders = []
    for side in ("top", "bottom"):
        name = f"{PREFIX}-{side}.png"
        out_png = RENDERS_DIR / name
        if out_png.exists():
            _fail(f"{name} 已存在（防覆写）")
        cmd = ["kicad-cli", "pcb", "render", "--side", side,
               "--width", str(RENDER_SIZE[0]), "--height", str(RENDER_SIZE[1]),
               "--background", "opaque", "--quality", "basic",
               "-o", f"renders/{name}", f"staging/{staged.name}"]
        proc = subprocess.run(
            [str(KICAD_CLI)] + cmd[1:], cwd=CAL_DIR,
            capture_output=True, text=True)
        if proc.returncode != 0 or not out_png.exists():
            _fail(f"kicad render 失败（{name}）：rc={proc.returncode} "
                  f"{(proc.stderr or proc.stdout)[-400:]}")
        w, h = _png_size(out_png)
        if w < MIN_SIZE[0] or h < MIN_SIZE[1]:
            _fail(f"{name}: 尺寸 {w}x{h} 低于可读下限 {MIN_SIZE}")
        bounds = calibration.png_board_pixel_bounds(out_png.read_bytes())
        px_w = bounds["x1"] - bounds["x0"]
        px_h = bounds["y1"] - bounds["y0"]
        aspect = px_w / px_h if px_h else 0.0
        if not 0.7 <= aspect <= 1.4:
            _fail(f"{name}: 板像素界纵横比 {aspect:.3f} 越出 [0.7,1.4]"
                  f"（70×70 方板；background={bounds['background_rgb']}）")
        renders.append({
            "file_rel": f"renders/{name}", "side": side,
            "sha256": hashing.sha256_file(str(out_png)),
            "bytes": out_png.stat().st_size,
            "width": w, "height": h,
            "tool": f"kicad-cli {KICAD_VERSION} pcb render",
            "command": cmd,
            "board_pixel_bounds": {
                "x0": bounds["x0"], "y0": bounds["y0"],
                "x1": bounds["x1"], "y1": bounds["y1"],
                "background_rgb": bounds["background_rgb"],
                "aspect_ratio": round(aspect, 6),
                "board_px_fraction_of_height": round(
                    px_h / h, 6),
            },
        })
        print(f"[s17-cal] render ok: {name} {out_png.stat().st_size}B "
              f"{w}x{h} 板界 px=({bounds['x0']},{bounds['y0']})-"
              f"({bounds['x1']},{bounds['y1']})")

    framing = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_render_framing",
        "domain_id": calibration.DOMAIN_ID,
        "source_board": {"path_rel": BOARD_REL, "sha256": src_sha},
        "board_edge_bbox_mm": board_bbox,
        "conversion_rule": (
            "板坐标 mm→图幅百分比：板 bbox（Edge.Cuts，mm）线性映射到板"
            "像素界（PNG 背景差分扫描实测，背景=左上角像素色）；top 视 "
            "x/y 同向，bottom 视 x 镜像；百分比相对整幅图幅（与 reader "
            "位置证据口径一致）。换算纯函数=pcbflow.calibration."
            "box_mm_to_frame_pct；无视觉判读参与。"),
        "renders": renders,
        "note": ("本包渲染只作校准域 GT 换算基底与后续 reader 输入；"
                 "未做任何人工视觉判读（GT 为确定性换算，非观感标注）。"),
    }
    sha = _write_canonical(FRAMING, framing)
    shutil.rmtree(STAGING_DIR)
    print(f"[s17-cal] framing 写出：render-framing.json sha256={sha[:16]}…"
          f"（staging 已清理）")


# ---------------------------------------------------------------------------
# annotate（判例坐标提取 → GT 条目；全部确定性）
# ---------------------------------------------------------------------------

def _cluster_positions(proof: dict, *, ref_any: tuple, types: frozenset,
                       trim_around=None) -> dict:
    """从 proof.drc_recon.gone_items 提取簇内判例坐标（确定性）。

    规则：条目 type ∈ types 且（description 或任一 item desc 含 ref_any
    之一）；trim_around=(锚点, 半径mm) 时剔除距锚点超半径的位置（F1/J2
    簇专用——J2 的 DRC 锚点=其 pad1，远离与 F1 的实际重叠区）。
    """
    positions: list = []
    matched: list = []
    for it in proof["drc_recon"]["gone_items"]:
        if it.get("type") not in types:
            continue
        descs = [it.get("description", "")] + \
                [i.get("desc", "") for i in it.get("items", [])]
        if not any(r in d for r in ref_any for d in descs):
            continue
        matched.append({"type": it["type"], "description":
                        it.get("description", "")})
        for item in it.get("items", []):
            pos = item.get("pos") or {}
            if "x" in pos and "y" in pos:
                if trim_around is not None:
                    ax, ay = trim_around[0]
                    d2 = (pos["x"] - ax) ** 2 + (pos["y"] - ay) ** 2
                    if d2 > trim_around[1] ** 2:
                        continue
                positions.append((float(pos["x"]), float(pos["y"])))
    if not positions:
        _fail(f"簇提取为空：refs={ref_any}（判例过滤规则与 proof 不符）")
    return {"positions": positions, "matched_items": matched}


def cmd_annotate() -> None:
    if GT_OUT.exists():
        _fail("ground-truth-v1.json 已存在（防覆写）")
    if not FRAMING.exists():
        _fail("render-framing.json 不存在（先跑 render）")
    framing = json.loads(FRAMING.read_text(encoding="utf-8"))
    proof = json.loads((REPO / PROOF_REL).read_text(encoding="utf-8"))
    if proof.get("hash_ledger", {}).get("pre_move_board_sha256", "") \
            [:8] != framing["source_board"]["sha256"][:8]:
        _fail("proof.pre_move_board_sha256 与渲染源板不符（判例-渲染错配）")

    top_px = next(r for r in framing["renders"] if r["side"] == "top")
    px_bounds = {"x0": top_px["board_pixel_bounds"]["x0"],
                 "y0": top_px["board_pixel_bounds"]["y0"],
                 "x1": top_px["board_pixel_bounds"]["x1"],
                 "y1": top_px["board_pixel_bounds"]["y1"],
                 "image_width": top_px["width"],
                 "image_height": top_px["height"]}
    bbox = framing["board_edge_bbox_mm"]

    def _entry(gt_id, category, cluster, refs, drc_types, desc):
        xs = [p[0] for p in cluster["positions"]]
        ys = [p[1] for p in cluster["positions"]]
        box_mm = [min(xs) - calibration.GT_MARGIN_MM,
                  min(ys) - calibration.GT_MARGIN_MM,
                  max(xs) + calibration.GT_MARGIN_MM,
                  max(ys) + calibration.GT_MARGIN_MM]
        box_pct = calibration.box_mm_to_frame_pct(
            box_mm, bbox, px_bounds, side="top")
        return calibration.build_gt_entry(
            gt_id=gt_id, category=category, side="top",
            board_box_mm=box_mm, frame_box_pct=box_pct,
            drc_types=drc_types, cluster_refs=refs,
            basis_refs=[name for name, _ in PROVENANCE_SOURCES]
            + ["render_framing"],
            description=desc)

    r4j3 = _cluster_positions(proof, ref_any=("R4", "J3"),
                              types=frozenset(PLACEMENT_TYPES))
    f1j2 = _cluster_positions(proof, ref_any=("F1", "J2"),
                              types=frozenset(PLACEMENT_TYPES),
                              trim_around=(F1_ANCHOR, F1_TRIM_RADIUS_MM))
    l1nb = _cluster_positions(proof, ref_any=("L1", "R11"),
                              types=frozenset(PLACEMENT_TYPES)
                              - {"shorting_items"})
    l1short = _cluster_positions(proof, ref_any=("L1",),
                                 types=frozenset({"shorting_items"}))

    entries = [
        _entry(
            "GT-REVC-P1-R4J3", "courtyard_crowding", r4j3, ["R4", "J3"],
            sorted(PLACEMENT_TYPES & {i["type"] for i in r4j3["matched_items"]}),
            "ASM-P1 批次 1 前态判例：R4 前态位姿 (63.8,15.8) 的 courtyard 与 "
            "J3 courtyard 重叠（courtyards_overlap）且 J3 PTH 焊盘 1 [3V3] 落入 "
            "R4 courtyard（pth_inside_courtyard），继而产生 3V3-GND 短路、"
            "间距违规与顶层阻焊桥及丝印压铜 warning。R4/F1 簇按人工决策映射"
            "放置类。"),
        _entry(
            "GT-REVC-P1-F1J2", "courtyard_crowding", f1j2, ["F1", "J2"],
            sorted(PLACEMENT_TYPES & {i["type"] for i in f1j2["matched_items"]}),
            "ASM-P1 批次 1 前态判例：F1 前态位姿 (53.5,8.3) 与 J2 courtyard "
            "重叠（courtyards_overlap/pth_inside_courtyard），F1 焊盘 2 "
            "[5V_USB] 与 J2 焊盘 39 短路、与焊盘 37 间距违规、顶层阻焊桥。"
            "J2 的 DRC 锚点（封装 J2=pad1 (6.37,5.57) 与近端丝印）远离实际"
            "重叠区，按 15mm 半径规则剔除（见脚本 F1_TRIM_RADIUS_MM）。"),
        _entry(
            "GT-REVC-P1-L1NB", "courtyard_crowding", l1nb, ["L1", "R11",
                                                            "C28"],
            sorted(PLACEMENT_TYPES & {i["type"] for i in l1nb["matched_items"]}),
            "ASM-P1 批次 1 前态判例：L1 前态位姿 (52.0,49.8) 的邻域放置冲突——"
            "courtyard 与 R11 (48.9,48.0) 重叠、与 C28 焊盘 1 [5V] 间距违规、"
            "U3 参考字段/C28 丝印压 L1 焊盘铜（silk_over_copper）。L1 簇的"
            "放置冲突面按其性质映射放置类。"),
        _entry(
            "GT-REVC-P1-L1SHORT", "other_advisory", l1short, ["L1"],
            ["shorting_items"],
            "ASM-P1 批次 1 前态判例：L1 两个焊盘（pad1 [SW_NODE] "
            "(53.765,49.8) 与 pad2 [3V3] (50.235,49.8)）之间被铜短路"
            "（shorting_items 3V3-SW_NODE）——敷铜把电感两焊盘桥接。类别"
            "枚举内无铜短路专用类，按 catch-all other_advisory 诚实映射"
            "（不用 suspicious_reroute：非改道现象）。"),
    ]
    calibration.validate_gt_entries(entries)

    # 自检（确定性箱体 sanity，非指标主张）：GT 与自身比较应全匹配
    self_flags = [{"flag_id": e["gt_id"], "category": e["category"],
                   "confidence": 1.0, "abstain": False,
                   "frame_box_pct": e["frame_box_pct"]} for e in entries]
    self_check = calibration.compare(self_flags, entries)
    if self_check["gt_matched_count"] != len(entries) \
            or self_check["reader_false_positive_ids"]:
        _fail(f"GT 自检失败（箱体/类别不一致）：{self_check}")

    provenance = {name: {"path_rel": rel,
                         "sha256": hashing.sha256_file(str(REPO / rel))}
                  for name, rel in PROVENANCE_SOURCES}
    gt = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_ground_truth",
        "domain_id": calibration.DOMAIN_ID,
        "annotation": {
            "method": (
                "人工标注 ground truth=ASM 链已确证判例的确定性提取："
                "坐标取 pose-revision-proof.json drc_recon.gone_items"
                "（前态已确证缺陷；new_items=后态引入项一律不用）；"
                "框=bbox+GT_MARGIN_MM(1.0mm) 固定外扩；板→图幅换算="
                "box_mm_to_frame_pct（top 视）。标注属 pipeline 侧，"
                "不得混入 reader 视野，不参与 raw-flags 校验或 ingest。"),
            "side": "top",
            "gt_margin_mm": calibration.GT_MARGIN_MM,
            "board_edge_bbox_mm": bbox,
            "board_pixel_bounds_top": px_bounds,
            "cluster_filter_rules": {
                "gone_items_only": True,
                "placement_types": sorted(PLACEMENT_TYPES),
                "f1j2_trim": f"剔除距 F1 锚点 {F1_ANCHOR} 超 "
                             f"{F1_TRIM_RADIUS_MM}mm 的位置（J2 DRC 锚点"
                             "远离实际重叠区）",
                "l1_split": "L1 簇按缺陷性质拆两条：放置冲突面"
                            "（courtyard_crowding）与焊盘铜短路"
                            "（other_advisory）",
            },
        },
        "gt_entries": entries,
        "self_check": {
            "rule": "compare(GT 视作 reader flags, GT) 应全匹配（箱体/类别"
                    "一致性 sanity，非校准指标主张）",
            "gt_matched_count": self_check["gt_matched_count"],
            "gt_count": self_check["gt_count"],
            "reader_false_positive_ids":
                self_check["reader_false_positive_ids"],
        },
        "provenance": provenance,
        "provenance_note": (
            "Rev-C 判例为内部板（仓库自有工程档案），无第三方 license "
            "负担；provenance 仍完整登记（证据文件+渲染源板 hash，"
            "sha256_file byte 口径）。"),
        "notes": [
            "人工决策（2026-09-05）：用 Rev-C 判例做种子——用 ASM 链已"
            "确证的缺陷与处置做人工标注 ground truth，先建小而可信的"
            "标注集。",
            "R4/F1 簇映射放置类；L1 簇按缺陷性质诚实映射（铜短路→"
            "other_advisory）。类别枚举=critic.FLAG_CATEGORIES 零改动。",
        ],
    }
    sha = _write_canonical(GT_OUT, gt)
    print(f"[s17-cal] GT 写出：ground-truth-v1.json sha256={sha[:16]}… "
          f"（{len(entries)} 条；自检全匹配）")


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------

def cmd_manifest() -> None:
    if MANIFEST_OUT.exists():
        _fail("calibration-domain-v1.json 已存在（防覆写）")
    if not GT_OUT.exists() or not FRAMING.exists():
        _fail("ground-truth-v1.json / render-framing.json 缺失")
    gt = json.loads(GT_OUT.read_text(encoding="utf-8"))
    framing = json.loads(FRAMING.read_text(encoding="utf-8"))
    categories = sorted({e["category"] for e in gt["gt_entries"]})
    for c in categories:
        if c not in critic.FLAG_CATEGORIES:
            _fail(f"GT 类别 {c} 越出 critic.FLAG_CATEGORIES")
    manifest = {
        "schema_version": "3.0",
        "kind": "tl2_calibration_domain",
        "domain_id": calibration.DOMAIN_ID,
        "domain_version": calibration.DOMAIN_VERSION,
        "status": "seed_annotation_only",
        "metric": {
            "metric_version": calibration.METRIC_VERSION,
            "containment_min": calibration.CONTAINMENT_MIN,
            "definition": (
                "匹配=abstain=False 且类别相等且 containment(读者框∩GT框/"
                "GT框面积) ≥ containment_min；abstain 单列。度量定义先写"
                "死后跑（pcbflow/calibration.py 常量），禁止为通过而调。"),
            "is_gate": False,
            "note": ("比较器输出为 advisory 侧分析；不进任何 gate 谓词，"
                     "不翻转 critic_calibration_in_range（谓词语义不变，"
                     "校准达标与否由后续正式校准流程裁决）。"),
        },
        "board": framing["source_board"],
        "renders": framing["renders"],
        "conversion_rule": framing["conversion_rule"],
        "ground_truth": {
            "path_rel": "out/v3-tl2/calibration/ground-truth-v1.json",
            "sha256": hashing.sha256_file(str(GT_OUT)),
            "entry_count": len(gt["gt_entries"]),
            "gt_ids": [e["gt_id"] for e in gt["gt_entries"]],
            "categories": categories,
        },
        "provenance": gt["provenance"],
        "split_declaration": {
            "role": "calibration_seed",
            "scope": ("Rev-C 判例种子集（4 簇），仅作 critic 校准建设"
                      "的人工标注起点；非训练/评测 split，不入 TL-5 语料"
                      "分母；reader 输出恒 untrusted。"),
            "board_count": 1,
        },
        "usage_policy": (
            "标注 pipeline 侧、不混入 reader 视野；校准域在正式校准流程"
            "建立并达标前，bundle 声明 domain_established 仍为 False，"
            "in_calibrated_range 恒 False、flags=[] 一律 blocked（"
            "fail-closed 语义零改动）。"),
        "notes": [
            "源板=ASM-P1 批次 1 前态（pre_move_board 332c71d4…，含 "
            "R4↔J3、F1↔J2、L1 三簇已知缺陷态）；源板零写（staging "
            "渲染后清理）。",
            "渲染与标注全程无人工视觉判读：GT 为判例坐标确定性换算。",
        ],
    }
    sha = _write_canonical(MANIFEST_OUT, manifest)
    print(f"[s17-cal] manifest 写出：calibration-domain-v1.json "
          f"sha256={sha[:16]}…")


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "render":
        cmd_render()
    elif step == "annotate":
        cmd_annotate()
    elif step == "manifest":
        cmd_manifest()
    else:
        _fail("用法：s17_calibration.py render|annotate|manifest")


if __name__ == "__main__":
    main()
