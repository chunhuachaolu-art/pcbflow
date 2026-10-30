"""④ FC2 产物组装（SPEC v1.3 §10.5/§10.6 两靶、§15 FC2、§16.4）。

靶 1 残网证书化回测（residual）：冻结布局（F3 终态=b3/snapshot-01，与 S4
上界同一板态）上 61 信号断点逐网 描线（pcbagent 锁定 adapter）+ 受限阻塞
证书（route_grid），三态分类 + S4 上界独立对照（dataset/mode/definition
分列，不混入 ② 的 61 断点主集读数）。

靶 2 ③ 重放板实战（replay）：③ layout.json（NEXT.md #5 已批重放靶）
经 board_writer 重放 placement（7 refs 真实移位）到快照副本 → 逐网描线 →
§10.4 提交纪律批落板（≤10 网/批 + kicad-cli DRC severity-error，新增违规
整批回滚）→ ≥40/61 零新增 error。DRC 由编排侧执行、结果 JSON 按 hash
作为本命令输入（pcbflow 保持零子进程）。

生成器模式：零落盘（板副本文本经 stdout 重定向由编排侧落盘）、零子进程；
live 板零写（hash 见证）。核心产物禁 wall-clock/主机路径（run_manifest
单列元数据）。
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import socket
import sys

from . import board_writer, config, hashing, route_grid

# ---- 常量（内聚本模块） ------------------------------------------------------
FC2_OUT_DEFAULT = config.load_project_manifest().out_dirs["residual"]  # G1+ W-2：值不变来源集中
WORKSPACE_SUB = "workspace"
F3_SUB = "f3-frozen"
P3_SUB = "p3-replay"
PRISTINE_NAME = "pristine.kicad_pcb"
BOARD_STEM = "stm32h743-coreboard-revc"
BATCH_SIZE = 10                     # §10.4：每 ≤10 网 DRC 一批
REPLAY_PLACEMENT_CSV = os.path.join(config.OUT_DIR, "revc-b1", "placement.csv")
REPLAY_LAYOUT_JSON = os.path.join(config.OUT_DIR, "revc-b1", "layout.json")
OPENS_CSV = config.AUDIT_OPENS_CSV

# S4 独立参考（dataset=F3 终态；tools/pcbagent/PHASE-REPORT-4 §3-§4；
# residual-report.md 落板明细）。dataset/mode 与 pcbflow FC2 分列。
S4_REFERENCE = {
    "source": "tools/pcbagent/PHASE-REPORT-4.md §3/§4 + b3/residual-report.md",
    "dataset": "F3_final_state",
    "mode": "L3 A* dry-run v1-v4（分段+ripup+净空中继）",
    "collectible": 9,
    "not_collectible": 52,
    "definition": "A* 不可达=启发式证据（无证书语义）",
    "committed_3v3_pairs": [
        ((26.75, 10.225), (26.25, 10.225)),
        ((20.5, 30.225), (22.325, 29.65)),
        ((25.725, 8.3), (26.25, 10.225)),
        ((37.75, 10.225), (37.025, 8.3)),
        ((22.325, 19.15), (20.5, 18.125)),
        ((43.425, 8.3), (44.25, 10.225)),
        ((47.675, 32.65), (50.2, 33.775)),
        ((51.095, 47.05), (53.0454, 50.5683)),
    ],
    "sw_node_note": "第 9 条可收=SW_NODE（5V-ripup 后 dry-run 可达；commit 因"
                    "信号铺铜重灌语义两次回滚，未落板）",
}
T1_DATASET = "F3_final_state"
T1_MODE = "fc2_certified_dry_run（direct A*+cert，ripup=False，无分段）"
T2_DATASET = "p3_replay_board（③ layout.json 重放）"
T2_MODE = "fc2_replay_commit（§10.4 批落板 ≤10 网/批 + DRC 整批回滚）"


# ---- 输入读取 ----------------------------------------------------------------
def _workspace_dirs(out_dir_rel):
    root = os.path.join(config.PCBFLOW_ROOT, out_dir_rel)
    return {"root": root,
            "f3": os.path.join(root, WORKSPACE_SUB, F3_SUB),
            "p3": os.path.join(root, WORKSPACE_SUB, P3_SUB)}


def _read_opens_rows(bm):
    """opens.csv → 61 信号断点行（GND 不入分母）；端点按镜像焊盘解析。"""
    mpads = {(p.ref, p.number): p for p in bm["mirror"].pads}
    rows = []
    with open(OPENS_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["net"] == "GND":
                continue
            rows.append({
                "net": r["net"],
                "desc_from": r["from"], "desc_to": r["to"],
                "ax": float(r["from_x_mm"]), "ay": float(r["from_y_mm"]),
                "bx": float(r["to_x_mm"]), "by": float(r["to_y_mm"]),
                "distance_mm": float(r["distance_mm"]),
            })
    for row in rows:
        for end, desc_key, xk, yk, lk in (
                ("A", "desc_from", "ax", "ay", "alayers"),
                ("B", "desc_to", "bx", "by", "blayers")):
            desc = row[desc_key]
            pad = _match_pad(desc)
            if pad and (pad[0], pad[1]) in mpads:
                p = mpads[(pad[0], pad[1])]
                row[xk], row[yk] = round(p.x, 6), round(p.y, 6)
                row[lk] = list(p.layers)
                row["kind_" + end] = "pad:%s.%s" % (p.ref, p.number)
            else:
                row[lk] = route_grid.layer_ids_of(
                    _desc_layers(desc), bm["pa"]["LAYERS"])
                row["kind_" + end] = "pt"
    return rows


def _match_pad(desc):
    import re
    m = re.search(r"([A-Z]+\d+) 的焊盘 (\d+)", desc)
    return (m.group(1), m.group(2)) if m else None


def _desc_layers(desc):
    return [k for k in ("F.Cu", "In2.Cu", "In1.Cu", "B.Cu") if k in desc]


def _read_placement_rows():
    with open(REPLAY_PLACEMENT_CSV, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    out = []
    for r in rows:
        out.append({"ref": r["ref"], "x": r["x"], "y": r["y"],
                    "rot": r["rot"], "side": r["side"], "zone": r["zone"]})
    return out


def _s4_cross(row):
    """单行 S4 对照（dataset=F3 终态；坐标匹配 ±0.02mm 无序对）。"""
    tol = 0.02
    pair_a = (row["ax"], row["ay"])
    pair_b = (row["bx"], row["by"])
    for (a, b) in S4_REFERENCE["committed_3v3_pairs"]:
        if _close(pair_a, a, tol) and _close(pair_b, b, tol) \
                or _close(pair_a, b, tol) and _close(pair_b, a, tol):
            return "s4_committed"
    if row["net"] == "SW_NODE":
        return "s4_dry_run_collectible"
    return "s4_not_collectible"


def _close(p, q, tol):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol


# ---- 靶 1：残网证书化回测 ----------------------------------------------------
def _classify(bm, row, net_id):
    """单断点：描线 → 三态 + 证书/归因。返回 (status, router, cert,
    unknown_reason, attribution)。"""
    if net_id is None:
        return ("UNKNOWN", None, None, "missing_basis:net_not_in_registry",
                None)
    router = route_grid.route_one(
        bm, row["net"], row["ax"], row["ay"], row["alayers"],
        row["bx"], row["by"], row["blayers"])
    attribution = {
        "net_id": net_id, "net_name": row["net"],
        "bus_id": row.get("bus_id"),
        "blocked_by": [b for b in router["blocks"][:3]] or None,
        "resource_type": "route_space_saturation" if not router["ok"]
                         else None,
        "constraint_refs": ["C-0036(0.35 pitch)", "class_clearance=0.2",
                            "min_copper_edge_clearance=0.5"],
        "suggested_rollback": "③ 布局/走廊重优化（锚件不动）；干道饱和升 "
                              "② 架构裁决" if not router["ok"] else None,
    }
    if router["ok"]:
        return ("SAT", router, None, None, attribution)
    model, unk = route_grid.build_cert_model(
        bm, row["net"], router["width"], router["via_size"],
        router["via_drill"], row["ax"], row["ay"], row["bx"], row["by"])
    if model is None:
        return ("UNKNOWN", router, None,
                "unknown:%s(%s)" % (unk[0], unk[1]), attribution)
    cert = route_grid.solve_cert(model)
    if cert.get("reachable_b") is not False:
        return ("UNKNOWN", router, None,
                "unknown:no_certificate(model 内存在候选通径，模型开放≠合法)",
                attribution)
    if cert.get("cert_broken"):
        return ("UNKNOWN", router, None, "unknown:cert_broken_closure",
                attribution)
    verified = route_grid.verify_cert(model, cert)
    cert = {k: v for k, v in cert.items()
            if k not in ("s_side_nodes",)}
    cert["verified"] = bool(verified)
    if not verified:
        return ("UNKNOWN", router, None, "unknown:cert_verify_failed",
                attribution)
    attribution["resource_type"] = _cert_resource_type(cert)
    return ("UNSAT", router, cert, None, attribution)


def _cert_resource_type(cert):
    rules = sorted({g.get("why", {}).get("rule", "?")
                    for g in cert.get("cut_groups", [])})
    if any("edge" in r for r in rules):
        return "board_edge_constraint"
    if any("hole" in r for r in rules):
        return "hole_clearance_constraint"
    return "route_space_saturation"


def build_residual(out_dir_rel=FC2_OUT_DEFAULT):
    """靶 1 产物：residual-certs.json 对象。"""
    ws = _workspace_dirs(out_dir_rel)
    bm = route_grid.board_model(ws["f3"])
    before = bm["pcb_sha256"]
    with open(OPENS_CSV, "rb") as f:
        opens_sha = hashing.sha256_bytes(f.read())

    reg = _registry_maps(out_dir_rel)
    net_id_of, bus_of = reg["net_id_of"], reg["bus_of"]

    rows = _read_opens_rows(bm)
    out_rows, runs = [], []
    for i, row in enumerate(sorted(rows, key=lambda r: (r["net"],
                                                        r["distance_mm"]))):
        nid = net_id_of.get(row["net"])
        row["bus_id"] = bus_of.get(row["net"])
        status, router, cert, unk, attribution = _classify(bm, row, nid)
        run = {"run_id": "RES-%03d" % i, "kind": "residual_net",
               "scope": {"net_id": nid, "net": row["net"]},
               "solver": "pcbagent_locked_A*(描线)+restricted_blocking_"
                         "certificate(残网)",
               "status": status,
               "witness": ({"segments": len(router["segments"]),
                            "vias": len(router["vias"]),
                            "length_mm": router["length_mm"],
                            "uuid": board_writer.route_uuid(router)}
                           if status == "SAT" else None),
               "unknown_reason": unk,
               "certificate": ({"kind": "restricted_blocking_certificate",
                                "verified": cert["verified"],
                                "cut_count": cert["cut_count"],
                                "cut_groups": cert["cut_groups"],
                                "scope": cert["scope"]}
                               if cert else None),
               "s4_cross": _s4_cross(row),
               "attribution": attribution,
               "router_fail": None if router is None or router["ok"]
                              else {"fail": router["fail"],
                                    "blocks": router["blocks"][:3],
                                    "refine_rounds": router["refine_rounds"]},
               }
        out_rows.append({
            "row_id": run["run_id"], "net": row["net"], "net_id": nid,
            "bus_id": row["bus_id"],
            "distance_mm": row["distance_mm"],
            "endpoints": {"A": [row["ax"], row["ay"], row["kind_A"]],
                          "B": [row["bx"], row["by"], row["kind_B"]]},
            "solver_status": status,
            "unknown_reason": unk,
            "certificate": run["certificate"],
            "witness": run["witness"],
            "s4_cross": run["s4_cross"],
            "attribution": attribution,
            "router_fail": run["router_fail"],
        })
        runs.append(run)

    after = hashing.sha256_file(bm["pcb_path"])
    counts = {s: sum(1 for r in out_rows if r["solver_status"] == s)
              for s in ("SAT", "UNSAT", "UNKNOWN")}
    unsat_nocert = sum(1 for r in out_rows
                       if r["solver_status"] == "UNSAT"
                       and not (r["certificate"] or {}).get("verified"))
    cross = {}
    for r in out_rows:
        key = (r["s4_cross"], r["solver_status"])
        cross["%s/%s" % key] = cross.get("%s/%s" % key, 0) + 1
    obj = {
        "schema_version": route_grid.FC2_SCHEMA,
        "artifact_kind": "residual_certs",
        "target": 1,
        "dataset": T1_DATASET, "mode": T1_MODE,
        "definition": {
            "denominator": len(out_rows),
            "denominator_note": route_grid.OPENS_TRUTH_NOTE,
            "SAT": "Router witness + L1 终判全过",
            "UNSAT": "受限阻塞证书（verified=true）；restricted scope 随行",
            "UNKNOWN": "缺档/超窗/无 witness 且无证书/复核失败",
            "strict_vs_derived": "strict=三态计数与证书 verified；"
                                 "derived=s4 交叉表（口径不同源，仅对照）",
        },
        "frozen_layout": {
            "board": os.path.relpath(bm["pcb_path"], config.PCBFLOW_ROOT),
            "sha256": before,
            "same_state_as_s4": before == hashing.sha256_file(
                route_grid.F3_FROZEN_BOARD),
        },
        "counts": counts,
        "unsat_without_certificate": unsat_nocert,
        "s4_reference": S4_REFERENCE,
        "s4_cross_table": dict(sorted(cross.items())),
        "rows": out_rows,
        "solver_runs": runs,
        "registry_snapshot_hash": reg["registry_snapshot_hash"],
        "pins": {"opens_csv_sha256": opens_sha,
                 "frozen_board_sha256": before},
        "zero_write": {"board_sha256_after_build": after,
                       "unchanged": before == after,
                       "note": "靶 1 全程内存 dry-run；副本文件仅读"},
        "note": "§10.6 靶 1：冻结布局残网逐网三态+证书，对照 S4 上界 "
                "(9/52)；pcbflow UNSAT 带 verified 证书（S4 的不可达为启发"
                "式证据，两者 dataset/mode/definition 分列不互替）",
    }
    return {"obj": obj, "bytes": hashing.canonical_json_bytes(obj),
            "sha256": None}


# ---- 靶 2：③ 重放板实战 ------------------------------------------------------
def _replay_pristine_text(ws):
    """读 FC2 pristine 板副本 → 文本（**通用换行模式：CRLF 被归一成 LF**）。

    ⚠ 这是**有意为之**的既有口径，不是疏漏；改动前请先读完：

    1. 本函数**故意不带** `newline=""`，让 Python 通用换行把 `\\r\\n` 归一成
       `\\n`。下游 `build_replay` 的 `pristine_sha256` / `replayed_sha256`
       正是**归一化文本**的 sha256（同函数 `text_hash_note`："本节 sha256=
       换行归一化文本（CRLF→LF）口径；板副本经 writer 链统一 LF 落盘"），
       `board_writer.apply_placement` / `_placement_deltas` /
       `route_grid.board_model` 也都在这一口径上比对。真实 FC2 workspace 的
       `pristine.kicad_pcb` 是**纯 CRLF**（382528 B，17986 个 `\\r\\n`、
       0 个裸 `\\n`）：改成 `newline=""` 会让 `replay-plan.json` 的
       `pristine_sha256` 由 `13e5d933…`（归一化）变成 `1ba6b259…`（原始字节），
       即改写既有 hash 台账。R5 已实测该差异，不采用改读取的做法。
    2. 因此**不要**为了把 `board_writer` 的 `eol="auto"`（见
       `board_writer.dominant_eol`）接进这条链而改这里的读取方式：CRLF 板在
       这里已被归一，`dominant_eol` 只会看到 LF，`eol="auto"` 会**静默**退化
       成 `"\\n"`（无异常、无告警）。要走 CRLF 保真链，请另开一条显式
       `newline=""` 的读取路径并单独记账。

    契约由 tests/test_residual_pristine_newline_guard.py 钉死（含真实 FC2
    台账 `pristine_sha256` 的逐字节交叉核对 + 源码口径字面量检查）。
    """
    with open(os.path.join(ws["p3"], PRISTINE_NAME), encoding="utf-8") as f:
        return f.read()


def build_replay(out_dir_rel=FC2_OUT_DEFAULT, drc_dir=None,
                 batches_dir=False):
    """靶 2 产物：replay-plan.json 对象（规划 + 可选执行台账）。

    batches_dir=True：执行证据升级——routes 取 batches/batch-k.json 的
    实际顺序感知规划 routes，accepted 批计入 committed（批构成仍以
    replay-plan.json 的冻结划分为准）。"""
    ws = _workspace_dirs(out_dir_rel)
    pristine = _replay_pristine_text(ws)
    pristine_sha = hashing.sha256_bytes(pristine.encode("utf-8"))
    placement = _read_placement_rows()
    replayed = board_writer.apply_placement(pristine, placement)
    replayed_sha = hashing.sha256_bytes(replayed.encode("utf-8"))

    reg = _registry_maps(out_dir_rel)
    net_id_of, bus_of = reg["net_id_of"], reg["bus_of"]

    deltas = _placement_deltas(pristine, replayed, placement)
    moved = [d for d in deltas
             if abs(d["dx_mm"]) > 0 or abs(d["dy_mm"]) > 0
             or d["drot_deg"] > 0]
    bm = route_grid.board_model(ws["p3"])
    if not batches_dir and bm["pcb_sha256"] != replayed_sha:
        return {"error": "workspace 板与 pristine+placement 重放不一致"
                "（先以 --select replay_board --stage placement 重放）",
                "workspace_sha": bm["pcb_sha256"],
                "expected_sha": replayed_sha}
    before = bm["pcb_sha256"]
    if batches_dir:
        # 执行证据模式：规划面复用盘上 plan-of-record（终态板已含落板铜，
        # 不得在其上重规划）；本函数只回填执行证据。
        prev = _read_product(out_dir_rel, "replay-plan.json")
        if prev is None or "definition" not in prev:
            return {"error": "replay-plan.json 缺失或无规划面（先跑无 "
                             "--batches-dir 的 --select replay）"}
        obj_prev = prev
        rows_count = obj_prev["definition"]["denominator"]
        routes = obj_prev["routes"]
        runs = obj_prev["solver_runs"]
        batch_index = obj_prev["batches"]
    else:
        rows = _read_opens_rows(bm)
        rows_count = len(rows)
        routes, runs = [], []
        for i, row in enumerate(sorted(rows, key=lambda r: (r["net"],
                                                            r["distance_mm"]))):
            nid = net_id_of.get(row["net"])
            router = route_grid.route_one(
                bm, row["net"], row["ax"], row["ay"], row["alayers"],
                row["bx"], row["by"], row["blayers"])
            # 三态（§10.3）：无 witness 且无证书 → UNKNOWN（无证书不写 UNSAT）
            status = "SAT" if router["ok"] else "UNKNOWN"
            unk = None if router["ok"] else \
                "unknown:no_witness_no_certificate（靶 2 实战语义：失败网" \
                "不作证书尝试，即弃）"
            if router["ok"]:
                routes.append({
                    "row_id": "RPL-%03d" % i, "net_id": nid,
                    "net": row["net"],
                    "bus_id": bus_of.get(row["net"]),
                    "width": router["width"], "via_size": router["via_size"],
                    "via_drill": router["via_drill"],
                    "segments": router["segments"], "vias": router["vias"],
                    "uuid": board_writer.route_uuid(router),
                })
            runs.append({"run_id": "RPL-%03d" % i, "kind": "replay_route",
                         "scope": {"net_id": nid, "net": row["net"]},
                         "solver": "pcbagent_locked_A*+L1 终判",
                         "status": status,
                         "unknown_reason": unk,
                         "fail": None if router["ok"] else router["fail"],
                         "witness": ({"segments": len(router["segments"]),
                                      "vias": len(router["vias"]),
                                      "length_mm": router["length_mm"]}
                                     if router["ok"] else None)})
        batches = [routes[k:k + BATCH_SIZE]
                   for k in range(0, len(routes), BATCH_SIZE)]
        batch_index = [{"batch": bi + 1,
                        "row_ids": [r["row_id"] for r in b],
                        "net_ids": [r["net_id"] for r in b],
                        "nets": [r["net"] for r in b]}
                       for bi, b in enumerate(batches)]

    after = hashing.sha256_file(bm["pcb_path"])
    obj = {
        "schema_version": route_grid.FC2_SCHEMA,
        "artifact_kind": "replay_plan",
        "target": 2,
        "dataset": T2_DATASET, "mode": T2_MODE,
        "replay": {
            "approved_target": "out/revc-b1/layout.json（NEXT.md #5，"
                               "2026-08-29 批）",
            "layout_json_sha256": hashing.sha256_file(REPLAY_LAYOUT_JSON),
            "placement_csv": os.path.relpath(REPLAY_PLACEMENT_CSV,
                                             config.PCBFLOW_ROOT),
            "placement_csv_sha256": hashing.sha256_file(
                REPLAY_PLACEMENT_CSV),
            "moved_refs": sorted(d["ref"] for d in moved),
            "moved_count": len(moved),
            "position_deltas": deltas,
            "pristine_sha256": pristine_sha,
            "replayed_sha256": replayed_sha,
            "text_hash_note":
                "本节 sha256=换行归一化文本（CRLF→LF）口径；板副本经"
                " writer 链统一 LF 落盘，kicad-cli 已验证可解析",
        },
        "definition": {
            "denominator": rows_count,
            "planned_sat": len(routes),
            "committed": None,
            "zero_new_error": None,
            "strict_vs_derived": "strict=planned SAT/L1 与批 DRC diff；"
                                 "committed 由 DRC 台账导出（derived）",
        },
        "batches": batch_index,
        "routes": routes,
        "solver_runs": runs,
        "execution_ledger": _drc_ledger(drc_dir) if drc_dir else None,
        "registry_snapshot_hash": reg["registry_snapshot_hash"],
        "zero_write": {
            "live_board_sha256": hashing.sha256_file(config.REVC_BOARD),
            "workspace_board_sha256_after_build": after,
            "unchanged_this_build": before == after,
            "final_routed_board_sha256": _final_routed_sha(out_dir_rel),
            "save_board_scope": "snapshot_copy_only（pre/post hash 编排侧记账）",
            "live_commit_called": False,
        },
        "note": "§10.6 靶 2：③ 重放快照副本 ≥40/61 零新增 error；批 DRC"
                "=kicad-cli（severity-error），终检 severity-all；pcbflow "
                "零子进程，DRC JSON 为 hash 输入",
    }
    if batches_dir:
        executed, n_batches = _batches_dir_routes(out_dir_rel,
                                                  len(batch_index))
        obj["executed_routes"] = executed
        obj["executed_batches"] = n_batches
        obj["definition"]["executed_sat"] = len(executed)
    if drc_dir:
        led = obj["execution_ledger"] or {}
        # 台账批与批划分按批号对齐：accepted 批的实际 routes 数计入 committed
        accepted_batches = {b["batch"] for b in led.get("batches", [])
                            if b["accepted"]}
        if batches_dir:
            per_batch = {}
            for k in range(1, len(batch_index) + 1):
                p = os.path.join(config.PCBFLOW_ROOT, out_dir_rel, "batches",
                                 "batch-%d.json" % k)
                if os.path.exists(p):
                    with open(p, encoding="utf-8") as f:
                        per_batch[k] = len(json.load(f)["routes"])
            committed = sum(per_batch.get(k, 0) for k in accepted_batches)
        else:
            committed = sum(len(b["net_ids"]) for b in batch_index
                            if b["batch"] in accepted_batches)
        for b in led.get("batches", []):
            bi = next((x for x in batch_index
                       if x["batch"] == b["batch"]), None)
            if bi:
                b["net_ids"] = bi["net_ids"]
                b["nets"] = bi["nets"]
        led["committed_nets"] = committed
        obj["definition"]["committed"] = committed
        obj["definition"]["zero_new_error"] = led.get("zero_new_errors")
    return {"obj": obj, "bytes": hashing.canonical_json_bytes(obj),
            "sha256": None}


def _final_routed_sha(out_dir_rel):
    """终态板副本（编排侧保全的 final-routed.kicad_pcb）文件字节 hash。"""
    p = os.path.join(config.PCBFLOW_ROOT, out_dir_rel, WORKSPACE_SUB,
                     P3_SUB, "final-routed.kicad_pcb")
    if os.path.exists(p):
        return hashing.sha256_file(p)
    return None


def _placement_deltas(pristine_text, replayed_text, placement):
    """重放前后的封装位形差（sexpr 解析；量化对齐语义的实测证据）。"""
    from . import sexpr_min

    def positions(text):
        root = sexpr_min.parse(text)[0]
        pos = {}
        for fp in sexpr_min.find_all(root, "footprint"):
            ref = None
            for prop in sexpr_min.find_all(fp, "property"):
                if sexpr_min.get_str(prop, 1) == "Reference":
                    ref = sexpr_min.get_str(prop, 2)
            at = sexpr_min.find_first(fp, "at")
            if ref and at:
                pos[ref] = (float(at[1]), float(at[2]),
                            float(at[3]) if len(at) > 3 else 0.0)
        return pos
    a = positions(pristine_text)
    b = positions(replayed_text)
    rows = []
    for r in sorted({p["ref"] for p in placement}):
        pa, pb = a.get(r), b.get(r)
        if not pa or not pb:
            continue
        drot = (pb[2] - pa[2]) % 360.0
        drot = min(drot, 360.0 - drot)
        rows.append({"ref": r, "dx_mm": round(pb[0] - pa[0], 4),
                     "dy_mm": round(pb[1] - pa[1], 4),
                     "drot_deg": round(drot, 3)})
    return rows


def _drc_ledger(drc_dir):
    """解析编排侧 kicad-cli DRC JSON（hash 输入）→ 执行台账。"""
    if not os.path.isdir(drc_dir):
        return None
    entries = sorted(f for f in os.listdir(drc_dir) if f.endswith(".json"))
    ledger = {"drc_dir": os.path.relpath(drc_dir, config.PCBFLOW_ROOT),
              "files": {}, "batches": [], "zero_new_errors": None,
              "committed_nets": None}
    base_viol = None
    base_unconn = None
    for name in entries:
        path = os.path.join(drc_dir, name)
        with open(path, "rb") as f:
            data = json.loads(f.read().decode("utf-8"))
        sha = hashing.sha256_file(path)
        viol = _viol_keyset(data)
        viol_err = {k for k in viol if k[1] == "error"}
        viol_warn = viol - viol_err
        unconn = _unconn_count(data)
        ledger["files"][name] = {
            "sha256": sha, "violations": len(viol), "unconnected": unconn,
            "severity_scope": data.get("severity_scope") or
            ("all" if "all" in name else "error"),
        }
        if name.startswith("baseline"):
            base_viol, base_unconn = viol_err | viol_warn, unconn
        elif name.startswith("batch"):
            k = int(name.split("-")[1].split(".")[0])
            base_all = base_viol or set()
            new_all = viol - base_all
            new_err = viol_err - {k2 for k2 in base_all if k2[1] == "error"}
            ledger["batches"].append({
                "batch": k, "file": name, "sha256": sha,
                "violations": len(viol),
                "new_vs_baseline": len(new_all),
                "new_errors_vs_baseline": len(new_err),
                "new_detail": sorted(v[0] + ":" + v[2][:60]
                                     for v in new_all),
                "accepted": len(new_err) == 0,
            })
        elif name.startswith("final"):
            base_all = base_viol or set()
            new_all = viol - base_all
            new_err = viol_err - {k2 for k2 in base_all if k2[1] == "error"}
            ledger["final_all"] = {
                "file": name, "sha256": sha, "violations": len(viol),
                "unconnected": unconn,
                "new_vs_baseline": len(new_all),
                "new_errors_vs_baseline": len(new_err),
                "new_warnings_vs_baseline": len(new_all) - len(new_err),
                "new_warning_detail": sorted(
                    v[0] + ":" + v[2][:60] for v in new_all
                    if v not in viol_err or v[1] != "error"),
            }
    if ledger["batches"]:
        # §10.6 分列：零新增 error=门；新增 warning 单列不否决
        ledger["zero_new_errors"] = all(b["new_errors_vs_baseline"] == 0
                                        for b in ledger["batches"]) and \
            (ledger.get("final_all") or {}).get("new_errors_vs_baseline",
                                                None) == 0
    return ledger


def _viol_keyset(data):
    out = set()
    for v in data.get("violations") or []:
        desc = ";".join((it.get("description") or "")
                        for it in (v.get("items") or []))
        out.add((v.get("type"), v.get("severity"), desc))
    return out


def _unconn_count(data):
    u = data.get("unconnected_items")
    if isinstance(u, list):
        return len(u)
    return u


# ---- replay_board（板文本输出；stdout 重定向落盘） ---------------------------
def build_replay_batch(out_dir_rel=FC2_OUT_DEFAULT, batch=1):
    """顺序感知批规划（§10.4 执行环）：在当前副本板态上重规划第 k 批。

    批构成取自 replay-plan.json 的 row_ids（行级——同网多断点如 3V3×22
    各自成行，不得按网名折叠）；同批网按序规划，已规划兄弟网经
    route_one_added 的 added_prims 进入障碍（同网兄弟豁免——同电位；
    L1 终判口径仍为静态铜，互检由批 DRC 裁决）。规划基线=当前副本板
    （已含批 1..k-1）。"""
    ws = _workspace_dirs(out_dir_rel)
    plan = _read_product(out_dir_rel, "replay-plan.json")
    if plan is None:
        return {"error": "replay-plan.json 缺失（先跑 --select replay）"}
    bi = next((b for b in plan["batches"] if b["batch"] == batch), None)
    if bi is None:
        return {"error": "批 %s 不在 replay-plan.json" % batch}
    bm = route_grid.board_model(ws["p3"])
    rows = _read_opens_rows(bm)
    ordered = sorted(rows, key=lambda r: (r["net"], r["distance_mm"]))
    by_row = {}
    for i, row in enumerate(ordered):
        by_row["RPL-%03d" % i] = row
    plan_rows = {x["row_id"]: x for x in plan["routes"]}
    routes, runs = [], []
    for row_id in bi["row_ids"]:
        row = by_row.get(row_id)
        if row is None:
            runs.append({"row_id": row_id, "status": "UNKNOWN",
                         "unknown_reason": "missing_basis:opens_row_missing"})
            continue
        r = route_grid.route_one_added(
            bm, row["net"], row["ax"], row["ay"], row["alayers"],
            row["bx"], row["by"], row["blayers"], added_routes=routes)
        if r["ok"]:
            src = plan_rows.get(row_id, {})
            routes.append({
                "row_id": row_id, "net_id": src.get("net_id"),
                "bus_id": src.get("bus_id"), "net": row["net"],
                "width": r["width"], "via_size": r["via_size"],
                "via_drill": r["via_drill"],
                "segments": r["segments"], "vias": r["vias"],
                "uuid": board_writer.route_uuid(r),
            })
        runs.append({"row_id": row_id, "net": row["net"],
                     "status": "SAT" if r["ok"] else "UNKNOWN",
                     "unknown_reason": None if r["ok"] else
                     "unknown:no_witness(批内顺序规划失败)",
                     "fail": None if r["ok"] else r["fail"]})
    return {"obj": {
        "schema_version": route_grid.FC2_SCHEMA,
        "artifact_kind": "replay_batch",
        "batch": batch,
        "planned_on_board_sha256": bm["pcb_sha256"],
        "routes": routes,
        "runs": runs,
    }}


def _batches_dir_routes(out_dir_rel, up_to):
    """读批执行目录中 1..up_to 批的实际 routes（展开为列表）。"""
    seen = 0
    out = []
    for k in range(1, up_to + 1):
        p = os.path.join(config.PCBFLOW_ROOT, out_dir_rel, "batches",
                         "batch-%d.json" % k)
        if not os.path.exists(p):
            break
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        out.extend(data["routes"])
        seen += 1
    return out, seen


def build_replay_board(out_dir_rel=FC2_OUT_DEFAULT, stage=None,
                       max_batch=None, batches_dir=False):
    """stage=placement：pristine+③ 重放；max_batch=k：再叠加 1..k 批路由
    （batches_dir=False 读 replay-plan.json 的规划 routes；
    True 读 batches/batch-k.json 的实际执行 routes）。"""
    ws = _workspace_dirs(out_dir_rel)
    text = board_writer.apply_placement(_replay_pristine_text(ws),
                                        _read_placement_rows())
    if max_batch is not None:
        if batches_dir:
            applied, _n = _batches_dir_routes(out_dir_rel, max_batch)
        else:
            plan = _read_product(out_dir_rel, "replay-plan.json")
            if plan is None:
                raise FileNotFoundError("replay-plan.json 缺失（先跑 --select "
                                        "replay）")
            by_batch = {b["batch"]: b for b in plan["batches"]}
            routes_by_id = {r["row_id"]: r for r in plan["routes"]}
            applied = []
            for bi in range(1, max_batch + 1):
                if bi not in by_batch:
                    break
                applied.extend(routes_by_id[x]
                               for x in by_batch[bi]["row_ids"])
        text = board_writer.apply_routes(text, applied)
    return text.encode("utf-8")


def _read_product(out_dir_rel, name):
    p = os.path.join(config.PCBFLOW_ROOT, out_dir_rel, name)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return None


# ---- 注册表（与 FC1 同链，registry 绑定） ------------------------------------
def _registry_maps(out_dir_rel):
    from . import route_view
    ctx = route_view.build_route_view(out_dir_rel)
    view = ctx["view"]
    net_id_of = {n["net_name"]: n["net_id"] for n in view["nets"]}
    bus_of = {}
    for b in ctx["structures"]["buses"]:
        for m in b["members"]:
            bus_of[m] = b["bus_id"]
    return {"net_id_of": net_id_of, "bus_of": bus_of,
            "registry_snapshot_hash": view["registry_snapshot_hash"],
            "view": view}


# ---- envelope / run_manifest / report ----------------------------------------
def build_envelope(out_dir_rel=FC2_OUT_DEFAULT):
    """FC2 门封装：读盘上两靶核心产物 + live 板零写见证。"""
    certs = _read_product(out_dir_rel, "residual-certs.json")
    replay = _read_product(out_dir_rel, "replay-plan.json")
    live_sha = hashing.sha256_file(config.REVC_BOARD)
    live_unchanged = live_sha == _live_pin_sha()

    gate = {"spec_ref": "SPEC v1.3 §10.6/§15-FC2/§16.4"}
    diagnostics = []
    if certs:
        gate["residual_certified"] = certs["unsat_without_certificate"] == 0
        gate["residual_three_state"] = certs["counts"]
        gate["s4_comparison_present"] = bool(certs.get("s4_cross_table"))
    else:
        gate["residual_certified"] = None
        diagnostics.append({"id": "residual_missing",
                            "title": "residual-certs.json 缺失（先跑 "
                                     "--select residual）"})
    if replay:
        led = replay.get("execution_ledger")
        gate["replay_planned_sat"] = replay["definition"]["planned_sat"]
        gate["replay_committed"] = replay["definition"]["committed"]
        gate["replay_zero_new_errors"] = replay["definition"][
            "zero_new_error"]
        gate["replay_ge_40"] = (None if
                                replay["definition"]["committed"] is None
                                else replay["definition"]["committed"] >= 40)
        gate["board_write_scope"] = "snapshot_copy_only"
        gate["live_board_unchanged"] = live_unchanged
        if led is None:
            diagnostics.append({"id": "drc_ledger_pending",
                                "title": "执行台账未接入（--drc-dir 待"
                                         "批 DRC 完成后重跑 replay）"})
    else:
        gate["replay_planned_sat"] = None
        gate["replay_committed"] = None
        gate["replay_zero_new_errors"] = None
        gate["replay_ge_40"] = None
        diagnostics.append({"id": "replay_missing",
                            "title": "replay-plan.json 缺失（先跑 "
                                     "--select replay）"})
    core_ok = (gate.get("residual_certified") is True
               and gate.get("s4_comparison_present") is True)
    replay_ok = (gate.get("replay_planned_sat") is not None
                 and gate.get("replay_zero_new_errors") is True
                 and gate.get("replay_ge_40") is True)
    status = "ok" if (core_ok and replay_ok) else (
        "unknown" if None in (gate.get("replay_zero_new_errors"),
                              gate.get("residual_certified")) else "failed")
    verdict = ("pass" if status == "ok" else
               "yellow" if core_ok else "fail")
    inputs = []
    for rel, role in ((os.path.join(out_dir_rel, "residual-certs.json"),
                       "target1"), (os.path.join(out_dir_rel,
                                                 "replay-plan.json"),
                                    "target2")):
        p = os.path.join(config.PCBFLOW_ROOT, rel)
        if os.path.exists(p):
            inputs.append({"path": rel, "sha256": hashing.sha256_file(p),
                           "role": role})
    inputs.append({"path": "design/coreboard/kicad/stm32h743-coreboard-revc/"
                           "stm32h743-coreboard-revc.kicad_pcb",
                   "sha256": live_sha, "role": "zero_write_witness"})
    env = {
        "schema_version": route_grid.FC2_SCHEMA,
        "tool": "pcbflow", "tool_version": config.TOOL_VERSION,
        "command": "route", "command_kind": "fc2_two_targets",
        "status": status, "verdict": verdict,
        "deterministic": True, "determinism_claim": "byte_exact",
        "inputs": inputs, "config_sha256": None,
        "spec_refs": ["tools/pcbflow/SPEC.md#§10.6",
                      "tools/pcbflow/SPEC.md#§15-FC2",
                      "tools/pcbflow/SPEC.md#§16.4"],
        "artifacts": [
            {"path": out_dir_rel + "/residual-certs.json", "role": "core"},
            {"path": out_dir_rel + "/replay-plan.json", "role": "core"},
            {"path": out_dir_rel + "/route-fc2-report.md",
             "role": "human_report"},
        ],
        "metrics": {
            "target1": (certs or {}).get("counts"),
            "target1_unsat_without_certificate":
                (certs or {}).get("unsat_without_certificate"),
            "target2_planned_sat":
                (replay or {}).get("definition", {}).get("planned_sat"),
            "target2_committed":
                (replay or {}).get("definition", {}).get("committed"),
            "board_write": False,
        },
        "diagnostics": diagnostics + [
            {"id": "fc2_synthetic_30",
             "title": "合成 30 网全布测试板 100% 布通=tests/test_fc2.py::"
                      "test_synthetic_30_nets_full_route 强制"},
            {"id": "fc2_control_binding",
             "title": "④ 控制未绑计划（NEXT.md #7：控制升级 consumer gate "
                      "另批，不默认捆绑）；本会话 planning_advisory 维持"},
        ],
        "waivers": [],
        "solver": {"certificates": "restricted_blocking_certificate"
                                   "（独立复核器 verified）",
                   "unsat_without_certificate":
                       (certs or {}).get("unsat_without_certificate")},
        "run_metadata": {},
        "data": {"gate": gate},
    }
    return env


def _live_pin_sha():
    """FC1 route-view pins 里的 live 板零写见证 sha（跨会话钉值）。"""
    from . import route_view as _rv
    pins_path = os.path.join(config.OUT_DIR, "revc-fc1", "route-view.json")
    with open(pins_path, encoding="utf-8") as f:
        pins = json.load(f).get("pins", {})
    return (pins.get("live_board_zero_write_witness") or {}).get("sha256")


def build_report_md(env, certs, replay):
    g = env["data"]["gate"]
    lines = ["# PCBFlow ④ FC2 两靶报告（残网证书化 + ③ 重放板实战）", "",
             "- 门 verdict：%s；status：%s" % (env["verdict"], env["status"]),
             ""]
    if certs:
        c = certs["counts"]
        lines += [
            "## 靶 1：冻结布局残网证书化（%s）" % certs["dataset"], "",
            "- 分母 %d（61 信号断点；GND 不入）；mode=%s"
            % (certs["definition"]["denominator"], certs["mode"]),
            "- 三态：SAT %d / UNSAT %d / UNKNOWN %d；无证书 UNSAT %d"
            % (c["SAT"], c["UNSAT"], c["UNKNOWN"],
               certs["unsat_without_certificate"]),
            "- S4 上界对照（dataset/mode/definition 分列）：%s"
            % json.dumps(certs["s4_cross_table"], ensure_ascii=False,
                         sort_keys=True),
            "",
            "| 断点 | net | 距离mm | 三态 | S4 对照 | 证书 |",
            "|---|---|---|---|---|---|",
        ]
        for r in certs["rows"]:
            lines.append("| %s | %s | %.1f | %s | %s | %s |"
                         % (r["row_id"], r["net"], r["distance_mm"],
                            r["solver_status"], r["s4_cross"],
                            ("verified(%d 割元素)" % r["certificate"][
                                "cut_count"])
                            if r["certificate"] else
                            (r["unknown_reason"] or "-")))
        lines.append("")
    if replay:
        d = replay["definition"]
        lines += [
            "## 靶 2：③ 重放板实战（%s）" % replay["dataset"], "",
            "- 重放：%d refs 移位（%s）；pristine %s…"
            % (replay["replay"]["moved_count"],
               ",".join(replay["replay"]["moved_refs"]),
               replay["replay"]["pristine_sha256"][:12]),
            "- 规划 SAT %d/%d；批数 %d；committed=%s；零新增 error=%s"
            % (d["planned_sat"], d["denominator"],
               len(replay["batches"]), d["committed"], d["zero_new_error"]),
            "",
        ]
        for b in replay["batches"]:
            lines.append("- 批 %d：%s" % (b["batch"], "，".join(
                r["net"] for r in replay["routes"]
                if r["row_id"] in b.get("row_ids", [])) or
                "，".join(b["nets"])))
        led = replay.get("execution_ledger")
        if led:
            lines += ["", "### 执行台账（DRC=hash 输入）", ""]
            for b in led["batches"]:
                lines.append("- 批 %d：violations=%d 新增=%d accepted=%s"
                             % (b["batch"], b["violations"],
                                b["new_vs_baseline"], b["accepted"]))
            if led.get("final_all"):
                lines.append("- 终检 severity-all：violations=%d 新增=%s"
                             " unconnected %s→%s"
                             % (led["final_all"]["violations"],
                                led["final_all"]["new_vs_baseline"],
                                led["files"].get("baseline-all.json", {})
                                .get("unconnected"),
                                led["final_all"]["unconnected"]))
        lines.append("")
    lines += ["", "## 门", ""]
    for k, v in sorted(g.items()):
        lines.append("- %s：`%s`" % (k, v))
    lines += ["", "人读视图非事实源；核心产物见 residual-certs.json / "
              "replay-plan.json。", ""]
    return "\n".join(lines)


# ---- 顶层组装 ----------------------------------------------------------------
def build_products(out_dir_rel=FC2_OUT_DEFAULT, select="summary",
                   drc_dir=None, max_batch=None, stage=None,
                   batch=None, batches_dir=False):
    t0 = datetime.datetime.now(datetime.timezone.utc)
    if select == "residual":
        prod = build_residual(out_dir_rel)
        prod["sha256"] = hashing.sha256_bytes(prod["bytes"])
        return {"payload": prod, "kind": "json"}
    if select == "replay":
        prod = build_replay(out_dir_rel, drc_dir=drc_dir,
                            batches_dir=batches_dir)
        if "error" in prod:
            return {"payload": {"error": prod["error"]}, "kind": "error"}
        prod["sha256"] = hashing.sha256_bytes(prod["bytes"])
        return {"payload": prod, "kind": "json"}
    if select == "replay_batch":
        prod = build_replay_batch(out_dir_rel, batch=batch or 1)
        if "error" in prod:
            return {"payload": {"error": prod["error"]}, "kind": "error"}
        prod["bytes"] = hashing.canonical_json_bytes(prod["obj"])
        return {"payload": prod, "kind": "json"}
    if select == "replay_board":
        text = build_replay_board(out_dir_rel, stage=stage,
                                  max_batch=max_batch,
                                  batches_dir=batches_dir)
        return {"payload": text, "kind": "bytes"}
    if select == "envelope":
        env = build_envelope(out_dir_rel)
        data = hashing.canonical_json_bytes(env)
        return {"payload": {"obj": env, "bytes": data,
                            "sha256": hashing.sha256_bytes(data)},
                "kind": "json"}
    if select == "run_manifest":
        return {"payload": {"obj": _run_manifest(out_dir_rel, t0)},
                "kind": "json"}
    if select == "report":
        env = build_envelope(out_dir_rel)
        certs = _read_product(out_dir_rel, "residual-certs.json")
        replay = _read_product(out_dir_rel, "replay-plan.json")
        md = build_report_md(env, certs, replay)
        return {"payload": md.encode("utf-8"), "kind": "bytes"}
    # summary
    env = build_envelope(out_dir_rel)
    return {"payload": {"obj": {
        "command": "residual", "status": env["status"],
        "verdict": env["verdict"], "metrics": env["metrics"],
        "gate": env["data"]["gate"], "diagnostics": env["diagnostics"],
        "note": "人读视图非事实源；核心产物见 residual-certs/"
                "replay-plan",
    }}, "kind": "json"}


def _run_manifest(out_dir_rel, t0):
    t1 = datetime.datetime.now(datetime.timezone.utc)
    inputs = {}
    ws = _workspace_dirs(out_dir_rel)
    for label, p in (
            ("opens_csv", OPENS_CSV),
            ("f3_frozen_board", os.path.join(ws["f3"],
                                             BOARD_STEM + ".kicad_pcb")),
            ("p3_pristine", os.path.join(ws["p3"], PRISTINE_NAME)),
            ("replay_placement_csv", REPLAY_PLACEMENT_CSV),
            ("replay_layout_json", REPLAY_LAYOUT_JSON)):
        if os.path.exists(p):
            inputs[label] = hashing.sha256_file(p)
    for label, name in (("residual_certs", "residual-certs.json"),
                        ("replay_plan", "replay-plan.json")):
        p = os.path.join(config.PCBFLOW_ROOT, out_dir_rel, name)
        if os.path.exists(p):
            inputs[label] = hashing.sha256_file(p)
    return {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(),
        "python_version": sys.version.split()[0],
        "tool_version": config.TOOL_VERSION,
        "command": "residual", "out_dir": out_dir_rel,
        "input_sha256": inputs,
        "spec_sha256": hashing.sha256_file(
            os.path.join(config.PCBFLOW_ROOT, "SPEC.md")),
        "route_impl_sha256": _impl_hashes(),
        "pcbagent_adapter_lock": route_grid.pcbagent_fc2_lock(),
        "schema_version": route_grid.FC2_SCHEMA,
    }


def _impl_hashes():
    here = os.path.dirname(os.path.abspath(__file__))
    out = {}
    for m in ("route_grid.py", "residual_cmd.py", "board_writer.py"):
        with open(os.path.join(here, m), "rb") as f:
            out[m] = hashing.sha256_bytes(f.read())
    return out
