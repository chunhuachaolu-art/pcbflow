"""V4exp 编排入口：对指定 split 逐场景 ref_route -> svg_pkg -> render_png。

stdin 收 {"out_dir": "out/v4-experiment", "splits": ["development"]}；
读 out_dir/scenario-manifest.json 与 board-snapshot-<sid>.json，产物命名
严格用 <kind>-<scenario_id>.<ext>（§10 风格；PNG 带分辨率后缀）：
  ref-routes-<sid>.json / route-manifest-<sid>.json /
  route-preview-<sid>.svg / route-preview-<sid>-<WxH>.png
stdout 打印汇总 JSON（确定序）。零 argv、零子进程（直接进程内调函数）。
"""

from __future__ import annotations

import os

from . import model, ref_route, render_png, svg_pkg


def emit_scenario(board: Board, out_dir: str) -> dict:
    sid = board.scenario_id
    ref = ref_route.route_board(board)
    ref_path = os.path.join(out_dir, f"ref-routes-{sid}.json")
    model.write_json(ref_path, ref)
    manifest, svg = svg_pkg.build(board, ref)
    manifest_path = os.path.join(out_dir, f"route-manifest-{sid}.json")
    svg_path = os.path.join(out_dir, f"route-preview-{sid}.svg")
    model.write_json(manifest_path, manifest)
    with open(svg_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    pngs = render_png.render_all(board, ref, manifest, out_dir)
    return {"scenario_id": sid, "label": board.label,
            "reference_unrouted": ref["reference_unrouted"],
            "unrouted_net_ids": ref["unrouted_net_ids"],
            "routes": len(ref["routes"]), "vias": len(ref["vias"]),
            "files": [ref_path.replace("\\", "/"),
                      manifest_path.replace("\\", "/"),
                      svg_path.replace("\\", "/")] + pngs}


def run(out_dir: str, splits) -> dict:
    sm = model.read_json(os.path.join(out_dir, "scenario-manifest.json"))
    split_set = list(splits)
    unknown = [s for s in split_set if s not in model.SPLITS]
    if unknown:
        raise ValueError(f"未知 split: {unknown}")
    results = []
    for entry in sm["scenarios"]:
        if entry["split"] not in split_set:
            continue
        sid = entry["scenario_id"]
        board = model.board_from_obj(
            model.read_json(os.path.join(out_dir,
                                         f"board-snapshot-{sid}.json")))
        results.append(emit_scenario(board, out_dir))
    results.sort(key=lambda r: r["scenario_id"])
    return {"out_dir": out_dir, "splits": split_set,
            "scenarios": len(results),
            "files": 1 + sum(len(r["files"]) for r in results),
            "reference_unrouted": [r["scenario_id"] for r in results
                                   if r["reference_unrouted"]],
            "results": results}


def main() -> None:
    import json as _json
    import sys
    cfg = model.read_stdin_json()
    summary = run(cfg.get("out_dir") or "out/v4-experiment",
                  cfg.get("splits") or ["development"])
    sys.stdout.write(_json.dumps(summary, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
