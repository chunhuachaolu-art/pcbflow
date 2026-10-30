"""V4-EXEC-P10 r5-viewer 样本产物生成（MASTER D-9；纯代码，零模型 token）。

对既有冻结样本生成 route-viewer 交互 HTML（≥2 个，含一个多 state 对照）、
view-spec 样例与对应聚焦投影 PNG、双跑重放证，全部落
``out/v4-exec/r5-viewer/``。冻结域只读（out/v4-experiment / out/
v4-comparative-experiment / out/v4-exec/r4-review）。

生成器纪律（R10）：纯函数构建、canonical 序列化、无 wall-clock、无主机
绝对路径（记录一律相对路径）、零网络；脚本内对每件产物双跑构建并断言
字节一致（重放证 replay-proof-r5.json）。

样本来源（全部既有冻结件，零新实验）：

1. ``viewer-dev-f4-02.html``：v4-experiment dev-f4-02（双图层 + 6 via，
   图层叠加过滤演示）；经 vrd.enrich_geometry 标注 baseline 后由生产链
   srp.build 重建（v1 快照 -> v2 合同的 P09 同款入口）。
2. ``viewer-dev-f3-05.html``：v4-experiment dev-f3-05（signal/clock/
   bus_member 三类 line_type + bus/clock_group 两组 relation）。
3. ``viewer-RC-CAL-F1-13-diff.html``：**真实 P09 冻结复查包**
   RC-CAL-F1-13 的 diff 视图（多 state 对照：baseline+candidate 并存；
   推荐人工验开）。

用法：``python scripts/r5_viewer_samples.py``（零 argv；幂等重放）。
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pcbflow import hashing                      # noqa: E402
from pcbflow import svg_route_package as srp     # noqa: E402
from pcbflow import v4_review_dispatch as vrd    # noqa: E402
from pcbflow import v4_route_viewer as vrv       # noqa: E402

# REPAIR-G2/G3 W-G3 等价门副本：输出隔离到本批目录（历史 out/v4-exec/r5-viewer/ 零回写）。
# 与原件唯一差异=本行以下两行（其余逐字节同源；对照基准见 out/repair-g2g3/ 主报告）。
_phase = sys.argv[1] if len(sys.argv) > 1 else "pre"
OUT_DIR = os.path.join("out", "repair-g2g3", _phase, "r5-replay")

V4EXP = "out/v4-experiment"
V4CMP = "out/v4-comparative-experiment"
R4PKG = "out/v4-exec/r4-review/review-packages/RC-CAL-F1-13"


def _read_json(rel: str):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def _read_text(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8", newline="") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 素材构建（全部纯函数；冻结输入只读）
# ---------------------------------------------------------------------------

def _rebuild_v1_sample(sid: str):
    """v4-experiment v1 快照 + ref 路由 → 生产链 v2 (svg, manifest)。

    与 P09 ``enrich_geometry`` 同款入口：把 v1 的 source='generator' 标注
    为 v2 合同的 ('baseline','baseline')（视图标注，几何事实零改动）。
    """
    board = _read_json(f"{V4EXP}/board-snapshot-{sid}.json")
    ref = _read_json(f"{V4EXP}/ref-routes-{sid}.json")
    geom = vrd.enrich_geometry(board, {"routes": ref["routes"],
                                       "vias": ref["vias"]},
                               state="baseline", source="baseline")
    return board, srp.build(board, geom)


def _frozen_diff_sample():
    """P09 冻结复查包 RC-CAL-F1-13 的 diff 视图（只读原样消费）。"""
    board = _read_json(f"{V4CMP}/board-snapshot-cal-f1-13.json")
    man = _read_json(f"{R4PKG}/diff-manifest.json")
    svg = _read_text(f"{R4PKG}/diff-view.svg")
    pkg = _read_json(f"{R4PKG}/package.json")
    return board, man, svg, pkg.get("review_package_sha256")


def build_all() -> dict:
    """构建全部产物（纯函数集合；返回 {相对名: bytes}）。双跑字节一致由
    调用方断言。"""
    out: "dict[str, bytes]" = {}
    provenance = []

    # ---- 样本 1/2：v4-experiment 板 × 生产链重建 --------------------------
    for sid in ("dev-f4-02", "dev-f3-05"):
        board, (svg_text, man) = _rebuild_v1_sample(sid)
        html = vrv.build_route_viewer(board, man, svg_text)
        name = f"viewer-{sid}.html"
        out[name] = html.encode("utf-8")
        provenance.append({
            "file": name, "kind": "route-viewer-html",
            "scenario_id": man.get("scenario_id"),
            "source_inputs": [
                f"{V4EXP}/board-snapshot-{sid}.json",
                f"{V4EXP}/ref-routes-{sid}.json"],
            "rebuild_note": ("v1 快照经 vrd.enrich_geometry(baseline/"
                             "baseline) 标注后由生产链 srp.build 重建为 "
                             "v2 合同视图（几何事实零改动）"),
            "board_snapshot_sha256": man["board_snapshot_sha256"],
            "route_manifest_payload_sha256":
                man["manifest_payload_sha256"],
            "states": sorted({r["state"] for r in man["routes"]}),
            "layers": sorted({r["layer"] for r in man["routes"]}),
            "line_types": sorted({r["line_type"] for r in man["routes"]}),
            "vias": len(man["vias"]),
        })

    # ---- 样本 3：P09 冻结复查包 diff 视图（多 state 对照） ----------------
    board13, man13, svg13, rp_sha = _frozen_diff_sample()
    html13 = vrv.build_route_viewer(
        board13, man13, svg13,
        title="RC-CAL-F1-13 diff（P09 冻结复查包，多 state 对照）")
    out["viewer-RC-CAL-F1-13-diff.html"] = html13.encode("utf-8")
    provenance.append({
        "file": "viewer-RC-CAL-F1-13-diff.html",
        "kind": "route-viewer-html",
        "scenario_id": man13.get("scenario_id"),
        "source_inputs": [
            f"{V4CMP}/board-snapshot-cal-f1-13.json",
            f"{R4PKG}/diff-manifest.json",
            f"{R4PKG}/diff-view.svg"],
        "frozen_review_package_sha256": rp_sha,
        "board_snapshot_sha256": man13["board_snapshot_sha256"],
        "route_manifest_payload_sha256":
            man13["manifest_payload_sha256"],
        "states": sorted({r["state"] for r in man13["routes"]}),
        "layers": sorted({r["layer"] for r in man13["routes"]}),
        "line_types": sorted({r["line_type"] for r in man13["routes"]}),
        "vias": len(man13["vias"]),
    })

    # ---- T3：view-spec 样例 + 聚焦投影 PNG --------------------------------
    board_f402, (_, man_f402) = _rebuild_v1_sample("dev-f4-02")
    specs = [
        ("view-spec-rc13-candidate-net-n1.json",
         {"schema": vrv.VIEW_SPEC_SCHEMA,
          "states": ["candidate"],
          "focus": {"kind": "net", "id": "n1"},
          "resolution_px": [1200, 675]},
         board13, man13,
         "focused-candidate-net-n1-1200x675.png"),
        ("view-spec-devf402-layer-bcu.json",
         {"schema": vrv.VIEW_SPEC_SCHEMA,
          "layers": ["B.Cu"],
          "resolution_px": [1200, 675]},
         board_f402, man_f402,
         "focused-layer-bcu-1200x675.png"),
    ]

    spec_records = []
    for name, spec, board, man, png_name in specs:
        normalized = vrv.normalize_view_spec(spec, man, board)
        spec_text = json.dumps(normalized, sort_keys=True, indent=2,
                               ensure_ascii=False) + "\n"
        out[name] = spec_text.encode("utf-8")
        rendered = srp.render_png(board, man, view_spec=spec)
        if not rendered.get("available"):
            raise SystemExit(f"render_png(view_spec) 不可用: {name}")
        out[png_name] = rendered["png_bytes"]
        spec_records.append({
            "file": name, "kind": "view-spec",
            "view_spec_sha256": vrv.view_spec_sha256(normalized),
            "bindings": normalized["bindings"],
            "png": {"file": png_name,
                    "png_sha256": hashing.sha256_bytes(
                        rendered["png_bytes"]),
                    "width": rendered["width"],
                    "height": rendered["height"]},
            "note": ("render_png(view_spec=…) 聚焦投影（T3 能力交付；进"
                     "任何实验模型臂输入须新预注册 R4/R8）"),
        })

    manifest = {
        "schema": "pcbflow.v4exec.r5-viewer-samples/1",
        "package": "V4-EXEC-P10",
        "artifacts": provenance,
        "view_specs": spec_records,
        "frozen_domains_read_only": [V4EXP, V4CMP,
                                     "out/v4-exec/r4-review"],
        "generator": "scripts/r5_viewer_samples.py（纯代码，零模型 token）",
    }
    out["samples-manifest-r5.json"] = (
        json.dumps(manifest, sort_keys=True, indent=2,
                   ensure_ascii=False) + "\n").encode("utf-8")
    return out


def main() -> None:
    run1 = build_all()
    run2 = build_all()          # 同进程内双跑（重放证之一）

    proof_files = []
    for name in sorted(run1):
        b1, b2 = run1[name], run2[name]
        s1 = hashing.sha256_bytes(b1)
        proof_files.append({
            "file": name,
            "run1_sha256": s1,
            "run2_sha256": hashing.sha256_bytes(b2),
            "bytes": len(b1),
            "byte_identical": b1 == b2,
        })
        if b1 != b2:
            raise SystemExit(f"双跑不一致（fail-closed）: {name}")
    proof = {
        "schema": "pcbflow.v4exec.r5-viewer-replay-proof/1",
        "package": "V4-EXEC-P10",
        "method": ("脚本内对每件产物独立调用两次纯函数构建链并比对字节；"
                   "另由编排侧跨进程二次执行本脚本比对目录聚合 hash（见"
                   "report-r5-viewer.md）"),
        "files": proof_files,
        "all_byte_identical": all(f["byte_identical"]
                                  for f in proof_files),
    }
    out_abs = os.path.join(ROOT, OUT_DIR)
    os.makedirs(out_abs, exist_ok=True)
    for name, data in sorted(run1.items()):
        with open(os.path.join(out_abs, name), "wb") as f:
            f.write(data)
    with open(os.path.join(out_abs, "replay-proof-r5.json"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(proof, sort_keys=True, indent=2,
                           ensure_ascii=False) + "\n")
    summary = {"files": len(run1) + 1,
               "all_byte_identical": proof["all_byte_identical"],
               "out_dir": OUT_DIR}
    sys.stdout.write(json.dumps(summary, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
