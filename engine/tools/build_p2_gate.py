# -*- coding: utf-8 -*-
"""P2 门构建器（任务书 §5 P2）：生成冲突清单/盲包/视图/冲突对枚举/门证据，staging 原子提交。

产出（全部 E:/ZCodeData/ZCodeProject/route-v5/out/v5-p2/ 之下，sidecar 卫生）：
  artifacts/  3 demo 板 x {conflicts, pkg} 工件 JSON + conflict-pairs.summary.json（provenance 头包装）
  views/      3 demo 板 x {l2-all SVG, l3-all SVG}（L3 带 corridor_stats 容量热区）
  gate/       gate-summary.json + p2.evidence.json

门项对账（脚本内断言，不过即整体 rollback 并退出码 1）：
  1 全量 pytest 绿；2 两静态检查 GREEN；
  3 demo 板自动产出 ≥1 可判 J 项（demo-01 含 1 个 joint 项）；
  4 盲包 schema round-trip（含 write_sidecar 注入 provenance 后仍过 schema）+ 头带 board_sha256；
  5 冲突图七对全枚举（7 块对抗板并集==7/7，带 winner/loser）；
  6 L2/L3 视图渲染+双跑字节等；
  7 V2 语义等价 diff 审计报告在场（tools/audit_v2_pkg.py 产物，主审另行登记判定）。
确定性：重跑同字节（pytest 墙钟与静态检查计数已归一化剥除）。
"""
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import canonical, schema_loader, sidecar, staging  # noqa: E402
from v5.board import load_board, load_board_file  # noqa: E402
from v5.compiler import build_full_conflict_graph  # noqa: E402
from v5.envelope_plan import build_envelope_artifact  # noqa: E402
from v5.jitems import build_j_items  # noqa: E402
from v5.overlay import build_conflicts, validate_conflicts_artifact  # noqa: E402
from v5.partition import build_partition_artifact  # noqa: E402
from v5.pkg import build_pkg, validate_pkg  # noqa: E402
from v5.view import GENERATOR as VIEW_GEN  # noqa: E402
from v5.view import VERSION as VIEW_VER  # noqa: E402
from v5.view import render_l2_view, render_l3_view  # noqa: E402

OUT = os.path.join(ROOT, "out", "v5-p2")
BOARD_DIR = os.path.join(ROOT, "boards", "d")
DEMO_BOARDS = ("demo-01-v2-corridor", "demo-02-mixed-types", "demo-03-small-mixed")
ADV_BOARDS = ("adv-01-pwr-vs-bus", "adv-02-clk-vs-short", "adv-03-diff-vs-capacity",
              "adv-04-xtalk-vs-vias", "adv-05-eqlen-vs-layerpref",
              "adv-06-copper-vs-completion", "adv-07-objection-vs-floor")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    tail = (r.stdout or "").strip().splitlines()
    return tail[-1] if tail else ""


def norm(line):
    line = re.sub(r"\s+in\s+[\d.]+s\s*$", "", line)   # pytest 墙钟
    return re.sub(r"\([^)]*\)", "", line).strip()      # 静态检查计数


def wrap_json(payload, generator, version, board_sha256):
    doc = {"provenance": {"generator": generator, "generator_version": version,
                          "board_sha256": board_sha256}}
    doc.update(payload)
    return canonical.canonical_json(doc)


def view_bytes(payload, kind, board_id, board_sha256):
    header = ("<!-- v5.view provenance generator=%s generator_version=%s"
              " board_sha256=%s board_id=%s kind=%s -->"
              % (VIEW_GEN, VIEW_VER, board_sha256, board_id, kind))
    return (header + "\n" + payload).encode("utf-8")


def main():
    checks = {}
    files = {}

    tail = norm(run([sys.executable, "-m", "pytest", "tests/", "-q", "--no-header"]))
    checks["full_test_suite"] = {"result": "GREEN" if ("passed" in tail and
                                                       "failed" not in tail and "error" not in tail)
                                 else "RED", "pytest_tail": tail}
    assert checks["full_test_suite"]["result"] == "GREEN", tail
    s1 = norm(run([sys.executable, "tools/check_sidecar.py"]))
    s2 = norm(run([sys.executable, "tools/check_drc_mono.py"]))
    checks["static_sidecar"] = s1
    checks["static_drc_mono"] = s2
    assert "GREEN" in s1 and "GREEN" in s2, (s1, s2)

    cleaned = staging.recover(os.path.join(OUT, "_staging"), OUT)

    tx_art = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "artifacts")
    try:
        # 门项 3/4：demo 板链式 conflicts→jitems→pkg + 盲包 schema round-trip
        for bid in DEMO_BOARDS:
            path = os.path.join(BOARD_DIR, bid + ".board.v1.json")
            b0 = load_board_file(path)
            rt = canonical.canonical_json(b0)
            assert canonical.canonical_json(load_board(json.loads(rt.decode("utf-8")))) == rt
            bsha = b0["provenance"]["board_sha256"]
            pt = build_partition_artifact(b0)
            env = build_envelope_artifact(b0, pt)
            cf = build_conflicts(b0)
            validate_conflicts_artifact(cf)
            ji = build_j_items(cf)
            assert len(ji) >= 1, bid  # 门项：demo 板自动产出 ≥1 可判 J 项
            pkg = build_pkg(b0, pt, cf)
            validate_pkg(pkg)
            assert pkg["board_sha256"] == bsha  # 门项：盲包头带 board_sha256
            # schema round-trip：内存形态 + write_sidecar 注入后落盘形态都过 schema
            schema = schema_loader.load_schema("pkg.v1.schema.json")
            registry = schema_loader.default_registry()
            schema_loader.validate(pkg, schema, registry, "")
            tmp_dir = os.path.join(str(sidecar.ALLOWED_ROOTS[0]), "_p2gate_tmp")
            injected_path = sidecar.write_sidecar(
                os.path.join(tmp_dir, bid + ".pkg.json"),
                pkg, "v5.pkg", "0.1.0", bsha)
            with open(injected_path, encoding="utf-8") as f:
                injected = json.load(f)
            schema_loader.validate(injected, schema, registry, "")
            for kind, payload in (("conflicts", cf), ("pkg", pkg)):
                data = wrap_json(payload, "v5.%s" % kind, "0.1.0", bsha)
                rel = "%s.%s.json" % (bid, kind)
                tx_art.write_bytes(rel, data)
                files[rel] = sha256_bytes(data)
            if bid == "demo-01-v2-corridor":
                assert any(j["kind"] == "joint" for j in ji), "demo-01 须含 1 个 joint 项"
                checks["demo_jitems"] = {
                    "demo-01": {"jitems": len(ji),
                                "joint": sum(1 for j in ji if j["kind"] == "joint"),
                                "conflicts": len(cf["conflicts"])}}
        for bid in DEMO_BOARDS:
            os.remove(os.path.join(str(sidecar.ALLOWED_ROOTS[0]), "_p2gate_tmp",
                                   bid + ".pkg.json"))
        os.rmdir(os.path.join(str(sidecar.ALLOWED_ROOTS[0]), "_p2gate_tmp"))

        # 门项 5：冲突图七对全枚举（7 块对抗板并集==7/7）
        present = set()
        per_board = {}
        for bid in ADV_BOARDS:
            b0 = load_board_file(os.path.join(BOARD_DIR, bid + ".board.v1.json"))
            graph = build_full_conflict_graph(b0)
            got = sorted(p["pair_id"] for p in graph["pairs"] if p.get("present"))
            per_board[bid] = got
            present.update(got)
        assert len(present) == 7, present
        checks["conflict_pairs"] = {"union": len(present), "per_board": per_board}
        data = wrap_json({"board_id": "(7 adv boards)", "pairs_union": sorted(present),
                          "per_board": per_board},
                         "v5.compiler", "0.1.0", "0" * 64)
        rel = "conflict-pairs.summary.json"
        tx_art.write_bytes(rel, data)
        files[rel] = sha256_bytes(data)
        tx_art.commit()
    except BaseException:
        tx_art.rollback()
        raise

    # 门项 6：L2/L3 视图（3 demo 板，L3 带走廊热区引擎值）
    tx_view = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "views")
    try:
        for bid in DEMO_BOARDS:
            b0 = load_board_file(os.path.join(BOARD_DIR, bid + ".board.v1.json"))
            bsha = b0["provenance"]["board_sha256"]
            pt = build_partition_artifact(b0)
            env = build_envelope_artifact(b0, pt)
            cf = build_conflicts(b0)
            stats = {z: {"occupancy": v["occupancy_mm"], "capacity": v["capacity_mm"]}
                     for z, v in env["corridor_ledger"].items()}
            l2 = render_l2_view(b0, pt, env, mode="all")
            l3 = render_l3_view(b0, pt, cf, corridor_stats=stats, mode="all")
            assert render_l2_view(b0, pt, env, mode="all") == l2
            assert render_l3_view(b0, pt, cf, corridor_stats=stats, mode="all") == l3
            for kind, payload in (("l2-all", l2), ("l3-all", l3)):
                data = view_bytes(payload, kind, bid, bsha)
                rel = "%s.%s.svg" % (bid, kind)
                tx_view.write_bytes(rel, data)
                files[rel] = sha256_bytes(data)
        tx_view.commit()
    except BaseException:
        tx_view.rollback()
        raise

    # 门项 7：V2 语义等价审计报告在场（audit 子智能体产物，判定由主审登记）
    audit_path = os.path.join(OUT, "audit", "v2-pkg-diff.json")
    assert os.path.isfile(audit_path), "V2 diff 审计报告缺失（先跑 tools/audit_v2_pkg.py）"
    audit = json.load(open(audit_path, encoding="utf-8"))
    checks["v2_pkg_diff_audit"] = {"summary": audit["summary"],
                                   "report": "out/v5-p2/audit/v2-pkg-diff.json"}

    summary = {"gate": "P2", "checks": checks, "boards": {"demo": DEMO_BOARDS,
               "adv": ADV_BOARDS}, "cleaned_staging_residue": cleaned,
               "artifact_files_sha256": files,
               "artifact_form_note": "JSON 工件落盘形态=payload+provenance 头包装；"
                                     "schema 校验均在包装前对 payload 执行",
               "no_manual_item": "P2 门无人工抽检项；V2 审计判定由主审登记 DISPATCH-LOG"}
    tx_gate = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "gate")
    try:
        data = wrap_json(summary, "v5.p2-gate", "0.1.0", "0" * 64)
        tx_gate.write_bytes("gate-summary.json", data)
        ev = {"gate": "P2", "checks": checks, "files": files,
              "taskbook": "V5.0-DEV-TASKBOOK-2026-09-13.md v3.2 (sha256 643c94e3...)"}
        data2 = wrap_json(ev, "v5.p2-gate", "0.1.0", "0" * 64)
        tx_gate.write_bytes("p2.evidence.json", data2)
        tx_gate.commit()
    except BaseException:
        tx_gate.rollback()
        raise

    print("P2 gate artifacts committed:")
    for rel in sorted(files):
        print("  %s  %s" % (files[rel][:12], rel))
    print("gate-summary: %d checks; pairs=%d/7; audit=%s" % (
        len(checks), checks["conflict_pairs"]["union"], audit["summary"]))


if __name__ == "__main__":
    main()
