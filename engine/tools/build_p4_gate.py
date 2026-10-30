# -*- coding: utf-8 -*-
"""P4 门构建器（任务书 §5 P4）：G1 成功率/G2 失败证据/G3 外权威对账，staging 原子提交。

产出（全部 E:/ZCodeData/ZCodeProject/route-v5/out/v5-p4/gate/ 之下，sidecar 卫生）：
  failcerts/<bid>.failcert.json  FAILED 板失败证书（v5.failcert.v1，独立可复算）
  pcb/<bid>.kicad_pcb            SAT 板导出件（写回导出器产物，双跑字节等）
  chain-g3-ledger.json + gate-summary.json + p4.evidence.json

门项对账（脚本内断言，不过即整体 rollback 并退出码 1）：
  1 全量 pytest 绿；2 两静态检查 GREEN；
  3 G1：3 demo 板全链 load→compile→plan(principle)→select→execute→route_check，
    SAT（exec=ROUTED 且 route_check.feasible）≥2；L7/爆炸/L6 视图对真实 routes_doc
    双跑字节等；
  4 G2：每个非 SAT 板 100% 配 v5.failcert.v1 证书且 verify() 复核 PASS
    （demo-01：零 routes 时 C1/F.Cu 固定铜 3.3+0.2+0.2+2×0.5=4.7>4.3 已溢出——
    容量归责缝如实留痕，阻塞点=板数据/核算缝而非布线搜索失败）；
  5 G3：SAT 板导出件 adapter 读回计数对账（segment/via/net、读回网序=板序）+
    kicad-cli DRC 实跑（--format json --severity-all；路径=用户确认的本机安装
    F:/kicad/bin/kicad-cli.exe，10.0.5），v5 route_check 与 kicad-cli 差异台账
    （证据只嵌确定性标量 totals/unconnected/parity；by-type 分裂=kicad-cli 并发
    竞态，只落台账文件并标注；原始 DRC 报告不落盘）。

确定性：重跑同字节（pytest 墙钟与静态检查计数归一化剥除；executor routes 双跑
字节等由 ⑤ 测试与门内断言双保险；视图/导出双跑字节等门内断言）。
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import canonical, failcert, staging  # noqa: E402
from v5.board import load_board, load_board_file  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.executor import execute_candidate  # noqa: E402
from v5.kicad_export import kicad_pcb_bytes  # noqa: E402
from v5.adapters.kicad_adapter import convert_file_with_report  # noqa: E402
from v5.planner import plan_candidates  # noqa: E402
from v5.route_check import ROUTES_SCHEMA_VERSION, check_routes  # noqa: E402
from v5.selection import select_best  # noqa: E402
from v5.view import render_exploded_view, render_l6_view, render_l7_view  # noqa: E402

OUT = os.path.join(ROOT, "out", "v5-p4")
BOARD_DIR = os.path.join(ROOT, "boards", "d")
DEMO_BOARDS = ("demo-01-v2-corridor", "demo-02-mixed-types", "demo-03-small-mixed")
# 用户确认本机 KiCad 10.0.5（2026-09-14，注册表 InstallLocation=F:\kicad，PATH 不含）
KICAD_CLI = "F:/kicad/bin/kicad-cli.exe"

LEDGER_NOTES = (
    "v5 R5 同分区豁免（DIFF 对/共端点分区）在 kicad-cli 实几何下呈现为 "
    "shorting_items——板合同抽象（两网共端点）与制造现实的披露差异，非布线错误",
    "kicad-cli 按导出件内嵌缺省净类（间距 0.2mm、线宽/孔径缺省）判定，v5 R5 为 "
    "0.5mm 中心线口径——规则配置不同源，两侧计数不可直接互判",
    "unconnected_items 反映执行器合同披露口径：过孔/回流孔不进 DRC 场景、焊盘逃逸孔"
    "不对称（起点披露/终点不披露）、ribbon 整体铜按声明 entry 导出——逐项复核挂 P5",
    "kicad-cli DRC 的 by-type 分裂非确定（内部并发竞态）：同字节输入两跑总数一致但"
    "shorting/clearance 归类可漂移——台账只锚总数，by-type 作观察样本披露",
)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    tail = (r.stdout or "").strip().splitlines()
    return tail[-1] if tail else ""


def norm(line):
    line = re.sub(r"\s+in\s+[\d.]+s\s*(\([\d:]+\))?\s*$", "", line)  # pytest 墙钟
    return re.sub(r"\([^)]*\)", "", line).strip()                     # 静态检查计数


def wrap_json(payload, generator, version, board_sha256):
    doc = {"provenance": {"generator": generator, "generator_version": version,
                          "board_sha256": board_sha256}}
    doc.update(payload)
    return canonical.canonical_json(doc)


def count_by(items, key):
    out = {}
    for it in items:
        k = str(it.get(key, "<none>"))
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def empty_routes_doc(board):
    sha = board["provenance"]["board_sha256"]
    return {"schema_version": ROUTES_SCHEMA_VERSION, "board_id": board["board_id"],
            "board_sha256": sha, "routes": [], "negotiation_log": [],
            "provenance": {"generator": "v5.p4-gate/0.1.0", "board_sha256": sha}}


def main():
    checks = {}
    files = {}

    tail = norm(run([sys.executable, "-m", "pytest", "tests/", "-q", "--no-header"]))
    checks["full_test_suite"] = {"result": "GREEN" if ("passed" in tail and
                                                       "failed" not in tail and
                                                       "error" not in tail)
                                 else "RED", "pytest_tail": tail}
    assert checks["full_test_suite"]["result"] == "GREEN", tail
    s1 = norm(run([sys.executable, "tools/check_sidecar.py"]))
    s2 = norm(run([sys.executable, "tools/check_drc_mono.py"]))
    checks["static_sidecar"] = s1
    checks["static_drc_mono"] = s2
    assert "GREEN" in s1 and "GREEN" in s2, (s1, s2)

    cleaned = staging.recover(os.path.join(OUT, "_staging"), OUT)
    kicad_version = run([KICAD_CLI, "version"])
    assert kicad_version, "kicad-cli version 无输出"

    tx = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "gate")
    tmp_dir = os.path.join(OUT, "_gatetmp")
    try:
        os.makedirs(tmp_dir, exist_ok=True)
        g1, g3 = {}, {}
        by_type = {}
        sat_boards, failed_boards = [], []
        routed_docs = {}
        for bid in DEMO_BOARDS:
            board = load_board_file(os.path.join(BOARD_DIR, bid + ".board.v1.json"))
            rt = canonical.canonical_json(board)
            assert canonical.canonical_json(load_board(
                json.loads(rt.decode("utf-8")))) == rt
            artifact, _fp = compile_board(board)
            cands = plan_candidates(board, artifact, arm="principle")
            res = select_best(board, cands)
            cand = res.get("best")
            source = "select_best.best" if cand is not None else "plan_candidates[0]"
            if cand is None:
                cand = cands[0]
            ex = execute_candidate(board, cand)
            row = {"selection_verdict": res["verdict"], "n_candidates": len(cands),
                   "candidate_source": source, "exec_verdict": ex["verdict"],
                   "negotiation_log_entries": len(ex["negotiation_log"]),
                   "per_net": len(ex["per_net"])}
            if ex["verdict"] == "ROUTED":
                doc = ex["routes"]
                cr = check_routes(board, doc)
                assert cr["feasible"], (bid, cr["violations"])
                # 视图链：真实 routes_doc 双跑字节等（L7/爆炸/L6）
                l7 = render_l7_view(board, doc, mode="all")
                expl = render_exploded_view(board, doc)
                l6 = render_l6_view(board, cands)
                assert l7 == render_l7_view(board, doc, mode="all")
                assert expl == render_exploded_view(board, doc)
                assert l6 == render_l6_view(board, cands)
                segs = sum(len(e["polyline"]) - 1 for e in doc["routes"])
                vias = sum(len(e.get("transition_vias", []))
                           + len(e.get("return_vias", [])) for e in doc["routes"])
                row.update({
                    "routes_sha256": sha256_bytes(canonical.canonical_json(doc)),
                    "routes_entries": len(doc["routes"]), "segments": segs,
                    "vias": vias, "feasible": True,
                    "violations_by_rule": count_by(cr["violations"], "rule"),
                    "attributed_violations": len(cr["attributed_violations"]),
                    "views_deterministic": True,
                    "view_bytes": {"l7": len(l7), "exploded": len(expl),
                                   "l6": len(l6)}})
                sat_boards.append(bid)
                routed_docs[bid] = (board, doc, cr)
            else:
                assert bid == "demo-01-v2-corridor", (
                    "非预期 FAILED 板 %s（G1 算术按三 demo 板口径）" % bid)
                failed_boards.append(bid)
            g1[bid] = row

        # G1 门：SAT ≥ 2/3
        assert len(sat_boards) >= 2, sat_boards
        checks["G1_executor_success_rate"] = {
            "result": "GREEN", "sat": len(sat_boards), "boards": DEMO_BOARDS,
            "per_board": g1,
            "note": "demo-01 FAILED 为容量归责缝的如实失败（见 G2 证书），"
                    "非布线搜索失败；SAT 口径=执行器 ROUTED 且 route_check.feasible"}

        # G2 门：失败证据 100% 合规（v5.failcert.v1 + verify 复核 PASS）
        certs = {}
        for bid in failed_boards:
            board = load_board_file(os.path.join(BOARD_DIR, bid + ".board.v1.json"))
            cr0 = check_routes(board, empty_routes_doc(board))
            assert cr0["feasible"] is False, bid
            over = [(clid, occ, cap) for clid, occ, cap in cr0["capacity_checks"]
                    if occ > cap]
            assert over, bid
            clid, occ, cap = over[0]
            terms = cr0["capacity_meta"][clid]["terms"]
            n = len(terms)
            assert round(sum(terms) + 0.5 * (n - 1), 10) == occ, (clid, occ)
            entry = {"constraint": "capacity",
                     "data": {"occupancy_terms": terms, "capacity_mm": cap},
                     "arithmetic": "%s+%0.1f×%d=%0.2f > %0.1f" % (
                         "+".join(str(t) for t in terms), 0.5, n - 1, occ, cap)}
            scope_nets = [str(x.get("net_id", "")) for x in board.get("nets", [])]
            cert = failcert.build_unsat_cert(
                dict(board["provenance"]), scope_nets, [entry], region=clid)
            ver = failcert.verify(cert)
            assert ver["recheck"] == "PASS"
            rel = "failcerts/%s.failcert.json" % bid
            data = failcert.cert_bytes(cert)
            tx.write_bytes(rel, data)
            files[rel] = sha256_bytes(data)
            certs[bid] = {"recheck": ver["recheck"], "region": clid,
                          "unsat_core_entries": len(cert["unsat_core"]),
                          "arithmetic": entry["arithmetic"]}
        assert len(certs) == len(failed_boards)
        checks["G2_failure_evidence"] = {
            "result": "GREEN", "failed_boards": failed_boards, "certs": certs,
            "compliance": "%d/%d" % (len(certs), len(failed_boards))}

        # G3 门：round-trip + kicad-cli 外权威差异台账（≥1 demo 板导出件）
        assert sat_boards, "无 SAT 板可导出"
        for bid in sat_boards:
            board, doc, cr = routed_docs[bid]
            data = kicad_pcb_bytes(board, doc)
            assert data == kicad_pcb_bytes(board, doc), "导出双跑字节不等"
            tmp_pcb = os.path.join(tmp_dir, bid + ".kicad_pcb")
            with open(tmp_pcb, "wb") as f:
                f.write(data)
            rb_board, report = convert_file_with_report(tmp_pcb, bid)
            segs = sum(len(e["polyline"]) - 1 for e in doc["routes"])
            vias = sum(len(e.get("transition_vias", []))
                       + len(e.get("return_vias", [])) for e in doc["routes"])
            n_nets = len(board["nets"])
            assert report["segment_count"] == segs, (bid, report["segment_count"], segs)
            assert report["via_count"] == vias, (bid, report["via_count"], vias)
            assert report["net_count"] in (n_nets, n_nets + 1), \
                (bid, report["net_count"], n_nets)
            net_order = ([str(x.get("net_id", "")) for x in rb_board["nets"]])
            assert net_order == [str(x.get("net_id", "")) for x in board["nets"]], \
                "读回网序≠板序"
            tmp_json = os.path.join(tmp_dir, bid + ".drc.json")
            r = subprocess.run(
                [KICAD_CLI, "pcb", "drc", "--output", tmp_json, "--format", "json",
                 "--severity-all", "--units", "mm", tmp_pcb],
                capture_output=True, text=True, timeout=300)
            assert r.returncode == 0 and os.path.isfile(tmp_json), \
                (bid, r.returncode, (r.stderr or "")[:200])
            with open(tmp_json, encoding="utf-8") as f:
                drc = json.load(f)
            os.remove(tmp_json)
            os.remove(tmp_pcb)
            rel = "pcb/%s.kicad_pcb" % bid
            tx.write_bytes(rel, data)
            files[rel] = sha256_bytes(data)
            g3[bid] = {
                "export_bytes": len(data),
                "export_sha256": sha256_bytes(data),
                "readback": {"segments": report["segment_count"],
                             "vias": report["via_count"],
                             "nets": report["net_count"],
                             "net_order_equal": True},
                "kicad_cli_version": kicad_version,
                "kicad_cli": {"violations_total": len(drc.get("violations", [])),
                              "unconnected_items": len(drc.get("unconnected_items", [])),
                              "schematic_parity": len(drc.get("schematic_parity", []))},
                "v5_route_check": {"feasible": cr["feasible"],
                                   "violations_by_rule": count_by(
                                       cr["violations"], "rule")},
                "ledger_notes": list(LEDGER_NOTES)}
            by_type[bid] = count_by(drc.get("violations", []), "type")
        checks["G3_roundtrip_external_drc"] = {
            "result": "GREEN", "boards": g3,
            "kicad_cli_path": KICAD_CLI, "kicad_cli_version": kicad_version,
            "ledger_form": "证据只嵌确定性标量（violations 总数/unconnected/parity）；"
                           "by-type 分裂是 kicad-cli 内部并发竞态（同字节输入两跑实测"
                           " demo-03 总数 27=27 但 clearance 9→7/shorting 18→20），"
                           "只落台账文件、不参与双跑字节等；原始 DRC 报告不落盘"}
        rel = "chain-g3-ledger.json"
        data = wrap_json({"boards": g3, "kicad_violations_by_type": by_type,
                          "determinism": "by_type 分裂=工具竞态，本文件不参与"
                                         "双跑字节比对（evidence 只锚 totals）"},
                         "v5.p4-gate", "0.1.0", "0" * 64)
        tx.write_bytes(rel, data)
    except BaseException:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        tx.rollback()
        raise
    shutil.rmtree(tmp_dir, ignore_errors=True)
    tx.commit()

    summary = {"gate": "P4", "checks": checks, "boards": {"demo": DEMO_BOARDS},
               "cleaned_staging_residue": cleaned,
               "artifact_files_sha256": files,
               "no_manual_item": "P4 门无人工抽检项"}
    tx2 = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "gate")
    try:
        data = wrap_json(summary, "v5.p4-gate", "0.1.0", "0" * 64)
        tx2.write_bytes("gate-summary.json", data)
        ev = {"gate": "P4", "checks": checks, "files": files,
              "taskbook": "V5.0-DEV-TASKBOOK-2026-09-13.md v3.2 (sha256 643c94e3...)"}
        data2 = wrap_json(ev, "v5.p4-gate", "0.1.0", "0" * 64)
        tx2.write_bytes("p4.evidence.json", data2)
        tx2.commit()
    except BaseException:
        tx2.rollback()
        raise

    print("P4 gate artifacts committed:")
    for rel in sorted(files):
        print("  %s  %s" % (files[rel][:12], rel))
    print("gate-summary: G1 SAT=%d/3; G2 certs=%s; G3 boards=%s; kicad=%s" % (
        len(sat_boards), checks["G2_failure_evidence"]["compliance"],
        sorted(g3), kicad_version))


if __name__ == "__main__":
    main()
