#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live2s1_run.py — LIVE2B-S1 编排脚本（live 快照 6 目标网全窗重解）。

对象：live 板（stm32h743-coreboard-revc，冻结见证 sha 前缀 8029f5ff）上的
6 目标网（RIPUP-1/LIVE-1 权威行号 RPL-038/039/052/054/056/019）。RIPUP-1
只给了 A* 不可达 + 洪泛封堵归因（heuristic）；本实验把三态做实：
- SAT：Router witness + L1 终判全过（零拆线可直接收的行）；
- UNSAT：restricted 阻割证书（win1 渐进窗梯 + 板级强化梯，
  solve_cert 割 + verify_cert 独立复核 verified=true）；
- 其余如实 UNKNOWN（扩窗不自动改判）。

纪律（与 win1_run.py 同源）：
- live 板零写：快照副本进 out/coreboard-live2b-s1/workspace/live/，
  pre/post sha256 记账；全程内存 dry-run（无板写、无 kicad-cli → 无
  .kicad_prl 副作用）；
- cli.py 零依赖（copper-loop 外部并行改写中，已登记事件）；代码路径只走
  pcbflow.win1_window / pcbflow.route_grid / pcbflow.residual_cmd /
  pcbflow.live2s1_experiment；
- route_grid.py 零改动；win1_window.py 零改动；
- fail-closed：受保护 hash、live 板 hash、行号漂移任一不符 → 不落盘退出；
- 幂等续跑：rows/<row_id>_<net>.json 已存在 → 跳过；
- 核心产物 canonical JSON、无 wall-clock；时间戳只进 run-manifest 与
  PROGRESS.md。

用法（tools/pcbflow 下）：
  python scripts/live2s1_run.py snapshot  # 快照副本 + 开工账（幂等）
  python scripts/live2s1_run.py rows      # 6 网逐行全窗重解（增量落盘）
  python scripts/live2s1_run.py assemble  # 结果表 + 守卫 + 汇总 JSON + 报告
  python scripts/live2s1_run.py fails <raw.txt> <out.json>  # 失败集提取
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pcbflow import config, hashing, live2s1_experiment as L2  # noqa: E402
from pcbflow import residual_cmd, route_grid, win1_window  # noqa: E402

PCBFLOW_ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(PCBFLOW_ROOT, "out", L2.LIVE2S1_DATASET)
WS_DIR = os.path.join(OUT_DIR, "workspace")
SNAP_DIR = os.path.join(WS_DIR, "live")
ROWS_DIR = os.path.join(OUT_DIR, "rows")
PROGRESS = os.path.join(OUT_DIR, "PROGRESS.md")

REVC_DIR = config.REVC_DIR   # live 板目录（零写：只读 stat/copy 源）
BOARD_FILES = ("stm32h743-coreboard-revc.kicad_pcb",
               "stm32h743-coreboard-revc.kicad_pro")
RIPUP1_LEDGER = os.path.join(PCBFLOW_ROOT, "out", "coreboard-ripup1",
                             "campaign-ledger.json")


def _fail(msg):
    print("LIVE2S1-FAIL: %s" % msg)
    sys.exit(1)


def _write_canonical(path, obj):
    data = hashing.canonical_json_bytes(obj)
    with open(path, "wb") as f:
        f.write(data)
    return hashing.sha256_bytes(data)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds")


def progress(line):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write("- %s %s\n" % (_now(), line))
    print("progress: %s" % line, flush=True)


def preflight():
    """fail-closed 预检：受保护 hash + live 板冻结见证。"""
    for rel, prefix in L2.PROTECTED:
        p = os.path.join(PCBFLOW_ROOT, rel)
        sha = hashing.sha256_file(p)
        if not sha.startswith(prefix):
            _fail("受保护文件 %s sha=%s… 与期望前缀 %s 不符"
                  % (rel, sha[:8], prefix))
        print("protected ok: %s %s…" % (rel, sha[:8]))
    live_sha = hashing.sha256_file(os.path.join(REVC_DIR, BOARD_FILES[0]))
    if not live_sha.startswith(L2.LIVE_BOARD_SHA_PREFIX):
        _fail("live 板 sha=%s… 与冻结见证 %s 不符"
              % (live_sha[:8], L2.LIVE_BOARD_SHA_PREFIX))
    print("live witness ok: %s…（零写，只读 stat）" % live_sha[:8])
    return live_sha


def cmd_snapshot():
    live_sha = preflight()
    os.makedirs(SNAP_DIR, exist_ok=True)
    ledger_path = os.path.join(WS_DIR, "snapshot-copy-ledger.json")
    files = {}
    for name in BOARD_FILES:
        src = os.path.join(REVC_DIR, name)
        dst = os.path.join(SNAP_DIR, name)
        src_sha = hashing.sha256_file(src)
        if os.path.exists(dst):
            dst_sha = hashing.sha256_file(dst)
            if dst_sha != src_sha:
                _fail("副本已存在但 %s sha=%s… 与源 %s… 不符"
                      % (name, dst_sha[:12], src_sha[:12]))
            copied = False
        else:
            shutil.copy2(src, dst)
            dst_sha = hashing.sha256_file(dst)
            if dst_sha != src_sha:
                _fail("拷贝后 %s sha 不符：src=%s… dst=%s…"
                      % (name, src_sha[:12], dst_sha[:12]))
            copied = True
        files[name] = {"sha256": src_sha, "pre_sha256": src_sha,
                       "post_sha256": dst_sha,
                       "copy_performed": bool(copied)}
    board_sha = files[BOARD_FILES[0]]["sha256"]
    if board_sha != live_sha:
        _fail("快照板 sha 与 live 板见证不符")
    ledger = {
        "schema_version": L2.LIVE2S1_SCHEMA,
        "artifact_kind": "live2s1_snapshot_copy_ledger",
        "dataset": L2.LIVE2S1_DATASET,
        "date": L2.LIVE2S1_DATE,
        "source_dir": os.path.relpath(REVC_DIR, PCBFLOW_ROOT),
        "copy_dir": os.path.relpath(SNAP_DIR, PCBFLOW_ROOT),
        "files": files,
        "unchanged": all(v["pre_sha256"] == v["post_sha256"]
                         for v in files.values()),
        "note": "live 板快照副本；实验全程内存 dry-run 零板写；"
                "只拷 .kicad_pcb+.kicad_pro（镜像取与 .kicad_pro 同名板）",
    }
    _write_canonical(ledger_path, ledger)
    progress("snapshot ok: board=%s… copied=%s"
             % (board_sha[:8],
                any(v["copy_performed"] for v in files.values())))
    print("snapshot ledger sha=%s…" % hashing.sha256_file(ledger_path)[:8])


def _load_bm():
    if not os.path.exists(os.path.join(SNAP_DIR, BOARD_FILES[0])):
        _fail("快照副本缺失（先跑 snapshot）")
    bm = route_grid.board_model(SNAP_DIR)
    live_sha = hashing.sha256_file(os.path.join(REVC_DIR, BOARD_FILES[0]))
    if not live_sha.startswith(L2.LIVE_BOARD_SHA_PREFIX):
        _fail("live 板 sha 漂移")
    if bm["pcb_sha256"] != live_sha:
        _fail("快照板 sha=%s… 与 live 板 %s… 不符"
              % (bm["pcb_sha256"][:12], live_sha[:12]))
    return bm, live_sha


def _ripup1_blockers():
    """campaign-ledger → {net: {row_id, blocker_nets, blockers_gateB/C}}。"""
    with open(RIPUP1_LEDGER, encoding="utf-8") as f:
        o = json.load(f)
    out = {}
    for r in o["rows"]:
        desc = (r.get("blockers_gateB") or r.get("blockers_gateC") or [])
        out[r["net"]] = {
            "row_id": r["row_id"],
            "blocker_nets": L2.parse_blocker_nets(desc),
            "blockers_desc": desc,
            "live_status": r.get("live_status"),
            "ripup_estimate": r.get("ripup_estimate"),
        }
    if set(out) != set(L2.TARGETS):
        _fail("RIPUP-1 台账网集 %s 与目标 %s 不符"
              % (sorted(out), sorted(L2.TARGETS)))
    for net, e in out.items():
        if e["row_id"] != L2.EXPECT_ROW[net]:
            _fail("RIPUP-1 行号漂移：%s=%s（期望 %s）"
                  % (net, e["row_id"], L2.EXPECT_ROW[net]))
    return out


def _bbox_nets_index(bm, region_mm, extra=1.5):
    """证书区域 → {prim_bbox(round6): [net,…]}（归因索引；只读查询）。"""
    G = bm["pa"]["geometry"]
    m = bm["mirror"]
    idx = {}
    for L in bm["pa"]["LAYERS"]:
        for it in m.query_copper(L, region_mm[0] - extra, region_mm[1] - extra,
                                 region_mm[2] + extra, region_mm[3] + extra):
            if not it.net:
                continue
            for prim in it.prims:
                pb = tuple(round(v, 6) for v in G.prim_bbox(prim))
                nets = idx.setdefault(pb, [])
                if it.net not in nets:
                    nets.append(it.net)
    return idx


def _board_strengthen(bm, row, router_summary, board_bb):
    """板级强化梯步：走廊 scope 割 → 整板窗重解（范围强化；verified=true
    才升格最终证书）。复用 win1_window._cert_step（同一三态映射语义）。"""
    nodes = win1_window.region_nodes(board_bb, row["ax"], row["ay"],
                                     row["bx"], row["by"],
                                     win1_window.WIN1_BOARD_MARGIN_MM)
    step = win1_window._cert_step(bm, row, router_summary,
                                  win1_window.WIN1_BOARD_MARGIN_MM,
                                  nodes["nodes"])
    step.update({"tier": "board_strengthen", "window_nodes": nodes["nodes"],
                 "margin_mm": win1_window.WIN1_BOARD_MARGIN_MM,
                 "skipped": False})
    return step


def cmd_rows():
    bm, live_sha = _load_bm()
    rip = _ripup1_blockers()
    rows = residual_cmd._read_opens_rows(bm)
    by_net = L2.assign_target_rows(rows)   # 行漂移即 RowDrift → fail-closed
    print("targets: %s" % ", ".join(
        "%s=%s" % (n, by_net[n]["row_id"]) for n in sorted(by_net)),
        flush=True)
    bb = bm["mirror"].bbox()
    os.makedirs(ROWS_DIR, exist_ok=True)
    n = 0
    for net in sorted(by_net):
        row = by_net[net]
        out_path = os.path.join(ROWS_DIR,
                                "%s_%s.json" % (row["row_id"], net))
        if os.path.exists(out_path):
            print("%s %s: 已存在，跳过（幂等续跑）" % (row["row_id"], net),
                  flush=True)
            n += 1
            continue
        t0 = datetime.datetime.now(datetime.timezone.utc)
        result = win1_window.run_row(bm, row)
        # 板级强化：UNSAT 且最终证书 scope 未达整板窗时补一梯（verified
        # 才升格；其余如实记录，UNKNOWN 不因扩窗改判——verdict_row 语义）
        board_strengthen = None
        cert = result.get("certificate")
        if result["status"] == "UNSAT" and cert:
            board_reg = win1_window.region_nodes(
                bb, row["ax"], row["ay"], row["bx"], row["by"],
                win1_window.WIN1_BOARD_MARGIN_MM)["region_mm"]
            if (cert.get("scope") or {}).get("region_mm") != board_reg:
                board_strengthen = _board_strengthen(
                    bm, row, result["router"], bb)
        # 割元素网属归因（对最终生效证书）
        final_cert = result.get("certificate")
        if board_strengthen and board_strengthen.get("status") == "UNSAT":
            final_cert = board_strengthen.get("certificate")
        hist = {"nets": {}, "boundary_cuts": 0, "other_unattributed": 0}
        if final_cert and final_cert.get("cut_groups"):
            idx = _bbox_nets_index(bm, final_cert["scope"]["region_mm"])
            hist = L2.cert_net_histogram(final_cert["cut_groups"], idx)
        verdict = L2.verdict_row(row["row_id"], net, result,
                                 rip[net]["blocker_nets"], hist,
                                 board_strengthen=board_strengthen)
        verdict["ripup1_baseline"] = rip[net]
        sha = _write_canonical(out_path, verdict)
        n += 1
        print("%s %s: status=%s cut=%s hist=%s strengthen=%s elapsed=%.1fs "
              "sha=%s…" % (row["row_id"], net, verdict["live2s1_status"],
                           verdict["certificate_cut_count"],
                           hist["nets"] or "-",
                           (board_strengthen or {}).get("status", "-"),
                           (datetime.datetime.now(datetime.timezone.utc)
                            - t0).total_seconds(), sha[:8]), flush=True)
        progress("row %s %s = %s" % (row["row_id"], net,
                                     verdict["live2s1_status"]))
    if n != len(by_net):
        _fail("rows 未齐：%d/%d" % (n, len(by_net)))
    progress("rows done: %d/%d" % (n, len(by_net)))


def _walk(root):
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            yield os.path.join(dirpath, name)


def cmd_assemble():
    bm, live_sha = _load_bm()
    rip = _ripup1_blockers()
    by_net = L2.assign_target_rows(residual_cmd._read_opens_rows(bm))
    rows = []
    for net in sorted(by_net):
        row = by_net[net]
        p = os.path.join(ROWS_DIR, "%s_%s.json" % (row["row_id"], net))
        if not os.path.exists(p):
            _fail("缺行产物 %s（先跑 rows）" % p)
        with open(p, encoding="utf-8") as f:
            rows.append(json.load(f))
    counts = L2.summary_counts(rows)
    board_after = hashing.sha256_file(
        os.path.join(SNAP_DIR, BOARD_FILES[0]))
    if board_after != live_sha:
        _fail("收工核对：快照板 sha 变了")
    live_after = hashing.sha256_file(os.path.join(REVC_DIR, BOARD_FILES[0]))
    if live_after != live_sha:
        _fail("收工核对：live 板 sha 变了")
    prl = [os.path.relpath(f, OUT_DIR) for f in _walk(OUT_DIR)
           if f.endswith(".kicad_prl")]
    gates = {"failure_set_diff": None}
    fs_pre = os.path.join(OUT_DIR, "failure-set-startwork.json")
    fs_post = os.path.join(OUT_DIR, "failure-set-endwork.json")
    if os.path.exists(fs_pre) and os.path.exists(fs_post):
        with open(fs_pre, encoding="utf-8") as f:
            pre = json.load(f)
        with open(fs_post, encoding="utf-8") as f:
            post = json.load(f)
        gates["failure_set_diff"] = L2.failure_set_diff(pre["ids"],
                                                        post["ids"])
        gates["failure_set_diff"]["pre_count"] = pre["count"]
        gates["failure_set_diff"]["post_count"] = post["count"]
    obj = {
        "schema_version": L2.LIVE2S1_SCHEMA,
        "artifact_kind": L2.LIVE2S1_ARTIFACT_KIND,
        "dataset": L2.LIVE2S1_DATASET,
        "date": L2.LIVE2S1_DATE,
        "baseline": {
            "ripup1_ledger": os.path.relpath(RIPUP1_LEDGER, PCBFLOW_ROOT),
            "mode": "A* 不可达 + 洪泛封堵归因（heuristic，无证书语义）",
            "live_unconnected": 57,
        },
        "experiment": {
            "module": "pcbflow/live2s1_experiment.py + pcbflow/win1_window.py",
            "route_grid_change": "none（零改动；win1 已参数化窗口）",
            "ladder_tiers": ["frozen_600k", "corridor", "board",
                             "board_strengthen（编排侧补梯：走廊 scope 割"
                             "的范围强化，verified 才升格）"],
            "board": "live 快照副本（pre=post=%s…）" % live_sha[:8],
            "board_sha256": board_after,
            "contract": "SAT=witness+L1；UNSAT=solve_cert 割+verify_cert "
                        "verified；其余 UNKNOWN；扩窗不自动改判；无 ripup",
        },
        "counts_live2s1": counts,
        "rows": rows,
        "gates": gates,
        "guards": {
            "live_board_sha256": live_after,
            "live_board_unchanged": live_after == live_sha,
            "snapshot_unchanged": board_after == live_sha,
            "kicad_prl_files_in_out": prl,
            "kicad_cli_invocations": 0,
            "cli_py_dependency": "none（copper-loop 并行改写事件零触碰）",
            "copper_loop_out_dirs": "zero-touch（无任何代码路径引用）",
            "datasets_dir_writes": "none",
        },
        "note": "LIVE2B-S1 核心产物（canonical，无 wall-clock）；逐行证据见 "
                "rows/<row_id>_<net>.json；restricted 声明逐条随行",
    }
    sha = _write_canonical(os.path.join(OUT_DIR, "live2s1-results.json"), obj)
    print("live2s1-results.json sha=%s… counts=%s" % (sha[:8], counts),
          flush=True)
    manifest = {
        "assembled_at": _now(),
        "python_version": sys.version.split()[0],
        "command": "scripts/live2s1_run.py assemble",
        "out_dir": os.path.relpath(OUT_DIR, PCBFLOW_ROOT),
        "input_sha256": {
            "live_board": live_sha,
            "ripup1_ledger": hashing.sha256_file(RIPUP1_LEDGER),
        },
        "impl_sha256": {m: hashing.sha256_file(
            os.path.join(PCBFLOW_ROOT, "pcbflow", m))
            for m in ("route_grid.py", "win1_window.py",
                      "live2s1_experiment.py", "residual_cmd.py")},
        "script_sha256": hashing.sha256_file(os.path.join(
            HERE, "live2s1_run.py")),
        "pcbagent_adapter_lock": route_grid.pcbagent_fc2_lock(),
        "protected_files": {rel: hashing.sha256_file(
            os.path.join(PCBFLOW_ROOT, rel)) for rel, _p in L2.PROTECTED},
    }
    _write_canonical(os.path.join(OUT_DIR, "run-manifest.json"), manifest)
    _write_report(obj)
    progress("assemble done: counts=%s" % counts)


def _scope_label(row):
    """最终证书 scope 标签：仅当板级强化步 UNSAT（最终证书=强化步证书）
    时为 board；否则最终证书=win1 首个 UNSAT 梯步（frozen/corridor 区域
    窗），如实给 corridor(区域窗)。"""
    bs = row.get("board_strengthen") or {}
    if bs.get("status") == "UNSAT":
        return "board"
    scope = (row.get("certificate_scope") or {}).get("region_mm")
    return "corridor(%s)" % (scope,)


def _cut_kinds(row):
    fc = row.get("final_certificate") or {}
    kinds = {}
    for g in fc.get("cut_groups") or []:
        kinds[g["kind"]] = kinds.get(g["kind"], 0) + len(g["items"])
    return kinds


def _write_report(obj):
    lines = ["# LIVE2B-S1 汇总报告（live 快照 6 目标网全窗重解）", "",
             "- 日期：%s；基线：RIPUP-1 洪泛归因（heuristic，无证书语义）"
             % obj["date"],
             "- 板：live 快照副本 sha=%s…（pre=post，live 板零写）"
             % obj["experiment"]["board_sha256"][:8],
             "- 合同：SAT=witness+L1；UNSAT=verified 割证书；其余 UNKNOWN；"
             "无 ripup；route_grid 零改动；cli.py 零依赖", "",
             "## 6 网三态一览", "",
             "| 行 | 网 | LIVE2B-S1 | 割元素 | 最终 scope | 梯 | "
             "RIPUP-1 归因 | 对照 |",
             "|---|---|---|---|---|---|---|---|"]
    for r in obj["rows"]:
        tiers = [s["tier"] for s in r.get("steps", []) if not s["skipped"]]
        if r.get("board_strengthen"):
            tiers.append("board_strengthen")
        rel = r["ripup1_consistency"]["relation"]
        lines.append("| %s | %s | **%s** | %s | %s | %s | %s | %s |"
                     % (r["row_id"], r["net"], r["live2s1_status"],
                        r.get("certificate_cut_count") or "-",
                        _scope_label(r),
                        "→".join(tiers) or "-",
                        ",".join(r["ripup1_blocker_nets"]) or "-", rel))
    lines += ["", "## 逐网要点", ""]
    for r in obj["rows"]:
        lines.append("### %s %s — %s" % (r["row_id"], r["net"],
                                         r["live2s1_status"]))
        if r["live2s1_status"] == "SAT":
            w = r.get("witness") or {}
            lines.append("- witness：%d 段 + %d 过孔，长 %s mm（L1 全过）"
                         % (w.get("segments", 0), w.get("vias", 0),
                            w.get("length_mm")))
        elif r["live2s1_status"] == "UNSAT":
            lines.append("- verified 割证书：cut_count=%s，scope=%s"
                         % (r.get("certificate_cut_count"),
                            (r.get("certificate_scope") or {}).get("model")))
            kinds = _cut_kinds(r)
            lines.append("- 割构成：%s" % json.dumps(
                kinds, ensure_ascii=False))
            if set(kinds) == {"spoke"}:
                lines.append("- 机制：端点 8 邻辐条全层封闭（端点 PTH 焊盘"
                             "自身钻孔孔距硬锁，孔无网属 → 直方图如实为空；"
                             "与 WIN-1 在 f3-frozen 板同构语义）")
        else:
            lines.append("- UNKNOWN：`%s`" % (r.get("unknown_reason"),))
        bs = r.get("board_strengthen") or {}
        if bs and bs.get("status") != "UNSAT":
            lines.append("- 板级强化梯：%s（%s）——走廊 scope 割仍为最终"
                         "证书（restricted），板级候选通径如实记录"
                         % (bs.get("status"),
                            (bs.get("unknown_reason")
                             or "").split("（")[0]))
        hist = (r.get("cert_cut_net_histogram") or {}).get("nets") or {}
        if hist:
            lines.append("- 割元素网属直方图：%s" % json.dumps(
                hist, ensure_ascii=False))
        lines.append("- 与 RIPUP-1 对照：%s（共同=%s；RIPUP-1 独有=%s；"
                     "证书独有=%s）"
                     % (r["ripup1_consistency"]["relation"],
                        r["ripup1_consistency"]["shared"] or "无",
                        r["ripup1_consistency"]["ripup1_only"] or "无",
                        r["ripup1_consistency"]["cert_only"] or "无"))
        lines.append("")
    g = (obj.get("gates") or {}).get("failure_set_diff")
    lines += ["## 验收门", ""]
    if g:
        lines.append("- 测试失败集差集：new_failures=%s（gates_ok=%s；"
                     "pre=%s post=%s unchanged=%s）"
                     % (g["new_failures"] or "无", g["gates_ok"],
                        g.get("pre_count"), g.get("post_count"),
                        g["unchanged_count"]))
    else:
        lines.append("- 测试失败集差集：未收档（收工 pytest 快照缺失）")
    lines += ["- live 板 sha 收工复验：unchanged=%s"
              % obj["guards"]["live_board_unchanged"],
              "- .kicad_prl 副作用：%s" % (obj["guards"]
                                          ["kicad_prl_files_in_out"]
                                          or "无"),
              "", "## S2 输入", "",
              "S2（布局迭代提案）只对 UNSAT 证明的网开工：见 "
              "`rows/<row_id>_<net>.json` 的 final_certificate 与 "
              "restricted_declarations（证书语义=模型化路线空间内不可布，"
              "restricted 逐条随行）。", ""]
    with open(os.path.join(OUT_DIR, "REPORT.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("REPORT.md 落盘")


def cmd_fails(raw_path, out_path):
    """pytest -rEf 原始输出 → 失败集 JSON（test id 列表）。"""
    ids = []
    with open(raw_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^(FAILED|ERROR) (\S+)", line)
            if m:
                ids.append("%s %s" % (m.group(1), m.group(2)))
    obj = {"raw": os.path.relpath(raw_path, PCBFLOW_ROOT), "count": len(ids),
           "failed": sum(1 for i in ids if i.startswith("FAILED")),
           "errors": sum(1 for i in ids if i.startswith("ERROR")),
           "ids": ids}
    _write_canonical(out_path, obj)
    print("failure-set: n=%d failed=%d errors=%d → %s"
          % (len(ids), obj["failed"], obj["errors"],
             os.path.relpath(out_path, PCBFLOW_ROOT)))


def main():
    sel = sys.argv[1] if len(sys.argv) > 1 else ""
    if sel == "snapshot":
        cmd_snapshot()
    elif sel == "rows":
        cmd_rows()
    elif sel == "assemble":
        cmd_assemble()
    elif sel == "fails":
        cmd_fails(sys.argv[2], sys.argv[3])
    else:
        _fail("用法：live2s1_run.py snapshot|rows|assemble|fails")


if __name__ == "__main__":
    main()
