#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""win1_run.py — WIN-1 编排脚本（UNKNOWN 窗自适应渐进实验）。

实验对象：out/revc-fc2/residual-certs.json（target 1，8 SAT / 40 UNSAT /
13 UNKNOWN）中 13 条 region_over_window UNKNOWN。方法与合同见
pcbflow/win1_window.py 模块 docstring。

纪律（与 house 规则一致）：
- 板操作只在快照副本：把 FC2 靶 1 数据集板（f3-frozen，与 residual-certs
  pins.frozen_board_sha256 fail-closed 比对）拷贝到 out/coreboard-win1/
  workspace/f3-frozen/，pre/post sha256 记账；live 板零写（hash 见证）。
  注：任务书原文写"从 p3 冻结板拷贝"，但 13 行是靶 1 判定、数据集板为
  f3-frozen（p3 pristine=靶 2 重放板，换板即换数据集、行映射失效）——
  偏差已申报，拷贝源改为 residual-certs.json 钉死的 f3-frozen 板。
- 本实验全程内存 dry-run（无板写入、无 kicad-cli → 无 .kicad_prl 副作用；
  收工仍扫描副本目录确认）。
- fail-closed：受保护 hash、板 hash、counts、行匹配任一不符 → 不落盘退出。
- 幂等续跑：rows/<row_id>.json 已存在且 canonical 合法 → 跳过。
- 核心产物 canonical JSON、无 wall-clock；时间戳只进 run-manifest 与本
  stdout 日志。

用法（tools/pcbflow 下）：
  python scripts/win1_run.py rows      # 逐条渐进窗实验（增量落盘）
  python scripts/win1_run.py assemble  # 结果表 + run manifest + 汇总 JSON
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pcbflow import hashing, residual_cmd, route_grid, win1_window  # noqa: E402

PCBFLOW_ROOT = os.path.dirname(HERE)
WIN1_OUT = os.path.join(PCBFLOW_ROOT, "out", "coreboard-win1")
SRC_RESIDUAL = os.path.join(PCBFLOW_ROOT, "out", "revc-fc2",
                            "residual-certs.json")
SRC_WS = os.path.join(PCBFLOW_ROOT, "out", "revc-fc2", "workspace",
                      "f3-frozen")
LIVE_BOARD = os.path.join(PCBFLOW_ROOT, "..", "..", "design", "coreboard",
                          "kicad", "stm32h743-coreboard-revc",
                          "stm32h743-coreboard-revc.kicad_pcb")
BOARD_STEM = "stm32h743-coreboard-revc.kicad_pcb"

PROTECTED = [
    ("pcbflow/cli.py", "6ed4f3fd"),
    ("pcbflow/config.py", "f515c348"),
    ("toolchain_lock.json", "d43dad89"),
]


def _fail(msg):
    print("WIN1-FAIL: %s" % msg)
    sys.exit(1)


def preflight():
    """fail-closed 预检：受保护 hash + 输入 pin + live 板见证。"""
    for rel, prefix in PROTECTED:
        p = os.path.join(PCBFLOW_ROOT, rel)
        sha = hashing.sha256_file(p)
        if not sha.startswith(prefix):
            _fail("受保护文件 %s sha=%s… 与期望前缀 %s 不符"
                  % (rel, sha[:8], prefix))
        print("protected ok: %s %s…" % (rel, sha[:8]))
    if not os.path.exists(SRC_RESIDUAL):
        _fail("缺 %s" % SRC_RESIDUAL)
    with open(SRC_RESIDUAL, "rb") as f:
        resid_sha = hashing.sha256_bytes(f.read())
    with open(SRC_RESIDUAL, encoding="utf-8") as f:
        resid = json.load(f)
    counts = resid.get("counts") or {}
    if counts != {"SAT": 8, "UNKNOWN": 13, "UNSAT": 40}:
        _fail("counts=%r 与冻结基线 8/40/13 不符" % counts)
    unk = win1_window.unknown_rows_from(resid)
    print("residual ok: sha=%s… counts=8/40/13 unknown=%d"
          % (resid_sha[:8], len(unk)))
    src_board = os.path.join(SRC_WS, BOARD_STEM)
    src_sha = hashing.sha256_file(src_board)
    pin = (resid.get("pins") or {}).get("frozen_board_sha256")
    if src_sha != pin:
        _fail("f3-frozen 板 sha=%s… 与 residual pin %s… 不符"
              % (src_sha[:12], (pin or "")[:12]))
    live_sha = hashing.sha256_file(LIVE_BOARD)
    if not live_sha.startswith("8029f5ff"):
        _fail("live 板 sha=%s… 与冻结见证 8029f5ff 不符" % live_sha[:8])
    print("live witness ok: %s…（零写，只读 stat）" % live_sha[:8])
    return resid, unk, src_sha, live_sha


def snapshot_board():
    """f3-frozen → coreboard-win1/workspace 副本（pre/post sha256 记账）。"""
    dst_ws = os.path.join(WIN1_OUT, "workspace", "f3-frozen")
    os.makedirs(dst_ws, exist_ok=True)
    dst_board = os.path.join(dst_ws, BOARD_STEM)
    ledger_path = os.path.join(WIN1_OUT, "workspace",
                               "snapshot-copy-ledger.json")
    src_board = os.path.join(SRC_WS, BOARD_STEM)
    src_sha = hashing.sha256_file(src_board)
    if os.path.exists(dst_board):
        dst_sha = hashing.sha256_file(dst_board)
        if dst_sha != src_sha:
            _fail("副本已存在但 sha=%s… 与源 %s… 不符"
                  % (dst_sha[:12], src_sha[:12]))
        print("snapshot ok (existing): %s…" % dst_sha[:12])
        return dst_ws, {"pre_sha256": src_sha, "post_sha256": dst_sha,
                        "copy_performed": False}
    for name in os.listdir(SRC_WS):
        shutil.copy2(os.path.join(SRC_WS, name),
                     os.path.join(dst_ws, name))
    dst_sha = hashing.sha256_file(dst_board)
    if dst_sha != src_sha:
        _fail("拷贝后 sha 不符：src=%s… dst=%s…" % (src_sha[:12], dst_sha[:12]))
    ledger = {"source": os.path.relpath(src_board, PCBFLOW_ROOT),
              "source_sha256": src_sha,
              "copy": os.path.relpath(dst_board, PCBFLOW_ROOT),
              "pre_sha256": src_sha, "post_sha256": dst_sha,
              "unchanged": src_sha == dst_sha,
              "note": "靶 1 数据集板快照副本；实验全程内存 dry-run 零板写"}
    _write_canonical(ledger_path, ledger)
    print("snapshot ok: %s…（pre=post，账落 snapshot-copy-ledger.json）"
          % dst_sha[:12])
    return dst_ws, ledger


def _write_canonical(path, obj):
    data = hashing.canonical_json_bytes(obj)
    with open(path, "wb") as f:
        f.write(data)
    return hashing.sha256_bytes(data)


def match_layers(bm, unk_rows):
    """opens.csv（residual 同法解析）→ 13 行的端点层集（route_one 用）。"""
    opens_rows = residual_cmd._read_opens_rows(bm)
    by_key = {}
    for r in opens_rows:
        key = (r["net"], round(r["ax"], 4), round(r["ay"], 4),
               round(r["bx"], 4), round(r["by"], 4))
        by_key[key] = r
        key2 = (r["net"], round(r["bx"], 4), round(r["by"], 4),
                round(r["ax"], 4), round(r["ay"], 4))
        by_key[key2] = r
    out = []
    for row in unk_rows:
        ep = row["endpoints"]
        key = (row["net"], round(ep["A"][0], 4), round(ep["A"][1], 4),
               round(ep["B"][0], 4), round(ep["B"][1], 4))
        src = by_key.get(key)
        if src is None:
            _fail("行 %s（%s）无法回配 opens.csv 端点 %r"
                  % (row["row_id"], row["net"], key))
        merged = dict(row)
        merged.update({"ax": src["ax"], "ay": src["ay"], "bx": src["bx"],
                       "by": src["by"], "alayers": src["alayers"],
                       "blayers": src["blayers"],
                       "distance_mm": src["distance_mm"]})
        out.append(merged)
    if len(out) != len(unk_rows):
        _fail("层回配不全：%d/%d" % (len(out), len(unk_rows)))
    return out


def cmd_rows():
    resid, unk_rows, src_sha, live_sha = preflight()
    dst_ws, ledger = snapshot_board()
    bm = route_grid.board_model(dst_ws)
    if bm["pcb_sha256"] != src_sha:
        _fail("副本板 sha 与源不符")
    merged = match_layers(bm, unk_rows)
    bb = bm["mirror"].bbox()

    def nodes_of(row):
        ep = row["endpoints"]
        return win1_window.region_nodes(bb, ep["A"][0], ep["A"][1],
                                        ep["B"][0], ep["B"][1],
                                        route_grid.CERT_MARGIN_MM)["nodes"]

    rows_dir = os.path.join(WIN1_OUT, "rows")
    os.makedirs(rows_dir, exist_ok=True)
    ordered = sorted(merged, key=nodes_of)
    print("order: %s" % ",".join(r["row_id"] for r in ordered), flush=True)
    for row in ordered:
        out_path = os.path.join(rows_dir, row["row_id"] + ".json")
        if os.path.exists(out_path):
            print("%s: 已存在，跳过（幂等续跑）" % row["row_id"], flush=True)
            continue
        t0 = datetime.datetime.now(datetime.timezone.utc)
        result = win1_window.run_row(bm, row)
        t1 = datetime.datetime.now(datetime.timezone.utc)
        sha = _write_canonical(out_path, result)
        cert = result.get("certificate")
        print("%s: status=%s cert_cut=%s elapsed=%.1fs sha=%s…"
              % (row["row_id"], result["status"],
                 cert["cut_count"] if cert else "-",
                 (t1 - t0).total_seconds(), sha[:8]), flush=True)
    print("rows 完成：13/13" if len(os.listdir(rows_dir)) >= 13
          else "rows 未齐：%d" % len(os.listdir(rows_dir)), flush=True)


def cmd_assemble():
    resid, unk_rows, src_sha, live_sha = preflight()
    rows_dir = os.path.join(WIN1_OUT, "rows")
    results = []
    for row in sorted(unk_rows, key=lambda r: r["row_id"]):
        p = os.path.join(rows_dir, row["row_id"] + ".json")
        if not os.path.exists(p):
            _fail("缺行产物 %s（先跑 rows）" % p)
        with open(p, encoding="utf-8") as f:
            r = json.load(f)
        results.append({
            "row_id": row["row_id"], "net": row["net"],
            "net_id": row.get("net_id"), "distance_mm": row.get("distance_mm"),
            "endpoints": row["endpoints"], "s4_cross": row.get("s4_cross"),
            "frozen_status": "UNKNOWN",
            "frozen_unknown_reason": row.get("unknown_reason"),
            "win1_status": r["status"],
            "upgraded": r["status"] != "UNKNOWN",
            "win1_unknown_reason": r.get("unknown_reason"),
            "certificate_cut_count": ((r.get("certificate") or {})
                                      .get("cut_count")),
            "certificate_scope": ((r.get("certificate") or {})
                                  .get("scope")),
            "witness": r.get("witness"),
            "router_fail": r.get("router"),
            "ladder": r.get("ladder"),
            "steps": r.get("steps"),
            "result_json_sha256": hashing.sha256_file(p),
        })
    counts = {s: sum(1 for x in results if x["win1_status"] == s)
              for s in ("SAT", "UNSAT", "UNKNOWN")}
    board_after = hashing.sha256_file(
        os.path.join(WIN1_OUT, "workspace", "f3-frozen", BOARD_STEM))
    if board_after != src_sha:
        _fail("收工核对：副本板 sha 变了（%s… → %s…）"
              % (src_sha[:12], board_after[:12]))
    live_after = hashing.sha256_file(LIVE_BOARD)
    if live_after != live_sha:
        _fail("收工核对：live 板 sha 变了")
    prl = [f for f in _walk(WIN1_OUT) if f.endswith(".kicad_prl")]
    obj = {
        "schema_version": win1_window.WIN1_SCHEMA,
        "artifact_kind": win1_window.WIN1_ARTIFACT_KIND,
        "target": 1,
        "baseline": {
            "product": os.path.relpath(SRC_RESIDUAL, PCBFLOW_ROOT),
            "sha256": hashing.sha256_file(SRC_RESIDUAL),
            "counts": {"SAT": 8, "UNSAT": 40, "UNKNOWN": 13},
            "unknown_cause": "region_over_window（CERT_WINDOW_NODES=600_000）",
        },
        "experiment": {
            "module": "pcbflow/win1_window.py",
            "route_grid_change": "build_cert_model 新增可选参数 "
                                 "window_nodes（默认=CERT_WINDOW_NODES="
                                 "600_000，冻结链调用点零改动）",
            "ladder_tiers": ["frozen_600k", "corridor", "board"],
            "board_dataset": "f3-frozen（residual-certs pins 钉死的靶 1 "
                             "数据集板；快照副本，pre=post）",
            "board_sha256": board_after,
            "contract": "SAT=witness+L1；UNSAT=solve_cert 割+verify_cert "
                        "verified；其余 UNKNOWN；扩窗不自动改判",
        },
        "counts_win1": counts,
        "upgraded": sum(1 for x in results if x["upgraded"]),
        "rows": results,
        "guards": {
            "live_board_sha256": live_after,
            "live_board_unchanged": live_after == live_sha,
            "board_copy_unchanged": board_after == src_sha,
            "kicad_prl_files_in_win1_out": prl,
            "datasets_dir_writes": "none（本实验不触 datasets/）",
        },
        "zero_write": {
            "board_writes": 0, "kicad_cli_invocations": 0,
            "note": "全程内存 dry-run；唯一新板字节=快照副本本身",
        },
        "note": "WIN-1 核心产物（canonical，无 wall-clock）；逐行证据见 "
                "rows/<row_id>.json；时间戳只进 run-manifest",
    }
    sha = _write_canonical(os.path.join(WIN1_OUT, "win1-results.json"), obj)
    print("win1-results.json sha=%s… counts=%s upgraded=%d"
          % (sha[:8], counts, obj["upgraded"]))
    t0 = datetime.datetime.now(datetime.timezone.utc)
    manifest = {
        "started_note": "rows 阶段时间戳在编排 stdout 日志（行级 elapsed）",
        "assembled_at": t0.isoformat(),
        "python_version": sys.version.split()[0],
        "command": "scripts/win1_run.py assemble",
        "out_dir": "out/coreboard-win1",
        "input_sha256": {
            "residual_certs": hashing.sha256_file(SRC_RESIDUAL),
            "frozen_board": src_sha,
        },
        "route_impl_sha256": {
            m: hashing.sha256_file(os.path.join(PCBFLOW_ROOT, "pcbflow", m))
            for m in ("route_grid.py", "win1_window.py", "residual_cmd.py")
        },
        "script_sha256": hashing.sha256_file(os.path.join(HERE,
                                                          "win1_run.py")),
        "pcbagent_adapter_lock": route_grid.pcbagent_fc2_lock(),
        "protected_files": {rel: hashing.sha256_file(
            os.path.join(PCBFLOW_ROOT, rel)) for rel, _p in PROTECTED},
    }
    _write_canonical(os.path.join(WIN1_OUT, "run-manifest.json"), manifest)
    print("run-manifest.json 落盘（wall-clock 单列）")


def _walk(root):
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            yield os.path.join(dirpath, name)


if __name__ == "__main__":
    sel = sys.argv[1] if len(sys.argv) > 1 else "rows"
    if sel == "rows":
        cmd_rows()
    elif sel == "assemble":
        cmd_assemble()
    else:
        _fail("用法：win1_run.py rows|assemble")
