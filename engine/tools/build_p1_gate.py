# -*- coding: utf-8 -*-
"""P1 门构建器（任务书 §5 P1）：生成工件/视图/门证据，staging 原子提交，程序化对账。

产出（全部 E:/ZCodeData/ZCodeProject/route-v5/out/v5-p1/ 之下，sidecar 卫生）：
  artifacts/  10 块 D 层板 x {partition, envelope, compiled} 工件 JSON（provenance 头包装）
  views/      3 块 demo 板 x {l1 全层 SVG, l1 单层(F.Cu) SVG, 交互 HTML}
  gate/       gate-summary.json + p1.evidence.json + spot-check-sheet.json（人工抽检单）

门项对账（脚本内断言，不过即整体 rollback 并退出码 1）：
  1 全量 pytest 绿；2 两静态检查 GREEN；3 demo 板分区表+宽度先验齐；
  4 容量账本手算一致（demo-01 C1）；5 D 层 10 板 round-trip 字节等；
  6 provenance 链复算（C2 vga 板双跑同 hash+源哈希对账）；
  7 视图三模式渲染+双跑字节等；8 L0.5 编译覆盖率 100%+编译产物 schema round-trip。

确定性：工件/证据 JSON 无时间戳无随机，重跑同字节（gate-summary 内含全件 sha256）。
注意：静态检查须在本脚本创建 staging 之前跑（脚本已保证顺序：先检查后建事务）。
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import canonical, schema_loader, sidecar, staging  # noqa: E402
from v5.board import load_board, load_board_file  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.envelope_plan import (build_envelope_artifact,  # noqa: E402
                              validate_envelope_artifact)
from v5.partition import (build_partition_artifact,  # noqa: E402
                          validate_partition_artifact)
from v5.view import GENERATOR as VIEW_GEN  # noqa: E402
from v5.view import VERSION as VIEW_VER  # noqa: E402
from v5.view import render_l1_html, render_l1_view  # noqa: E402

OUT = os.path.join(ROOT, "out", "v5-p1")
BOARD_DIR = os.path.join(ROOT, "boards", "d")
DEMO_BOARDS = ("demo-01-v2-corridor", "demo-02-mixed-types", "demo-03-small-mixed")
SINGLE_LAYER = "F.Cu"
PCB = "E:/ZCodeData/.zcode/workspace/default/tools/pcbflow/datasets/corpus-r2-r1"

# demo-01 分区的 V2 权威参照（prompt-v2-template.md §分区表，人工抽检对照基准）
V2_REF = {
    "P1": [[2.0, 38.0], [44.0, 38.0]], "P2": [[5.0, 10.0], [45.0, 10.0]],
    "P3": [[16.0, 4.0], [16.0, 36.0]], "P4": [[32.6, 4.0], [32.6, 36.0]],
    "P5": [[37.0, 10.0], [37.0, 30.0]], "P6": [[46.0, 32.0], [46.0, 38.0]],
    "P7": [[2.0, 36.7], [44.0, 36.7]], "P8": [[44.0, 4.0], [48.0, 4.0]],
    "P9": [[2.0, 36.1], [44.0, 36.1]],
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    tail = (r.stdout or "").strip().splitlines()
    return (r.stdout or "") + (r.stderr or ""), tail[-1] if tail else ""


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

    # ---- 门项 1/2：全量测试 + 静态检查（须在 staging 创建前跑）----
    import re
    _, tail = run([sys.executable, "-m", "pytest", "tests/", "-q", "--no-header"])
    tail = re.sub(r"\s+in\s+[\d.]+s\s*$", "", tail)  # 剥墙钟时长，保确定性
    checks["full_test_suite"] = {"result": "GREEN" if ("passed" in tail and
                                                       "failed" not in tail and "error" not in tail)
                                 else "RED", "pytest_tail": tail}
    assert checks["full_test_suite"]["result"] == "GREEN", tail
    _, s1 = run([sys.executable, "tools/check_sidecar.py"])
    _, s2 = run([sys.executable, "tools/check_drc_mono.py"])
    s1 = re.sub(r"\([^)]*\)", "", s1).strip()  # 剥文件计数（首跑/复跑态不同），保确定性
    s2 = re.sub(r"\([^)]*\)", "", s2).strip()
    checks["static_sidecar"] = s1.strip()
    checks["static_drc_mono"] = s2.strip()
    assert "GREEN" in s1 and "GREEN" in s2, (s1, s2)

    # 残留清理（上次中断防护）
    cleaned = staging.recover(os.path.join(OUT, "_staging"), OUT)

    boards = []
    for name in sorted(os.listdir(BOARD_DIR)):
        if name.endswith(".board.v1.json"):
            boards.append(name[: -len(".board.v1.json")])
    assert len(boards) == 10, boards

    # ---- 工件生成 + 门项 3/4/8 ----
    tx_art = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "artifacts")
    spot_entries = []
    try:
        for bid in boards:
            path = os.path.join(BOARD_DIR, bid + ".board.v1.json")
            raw = open(path, "rb").read()
            # 门项 5：D 层 round-trip（读入→canonical→重读→再 canonical 字节等）
            b0 = load_board_file(path)
            rt = canonical.canonical_json(b0)
            b1 = load_board(json.loads(rt.decode("utf-8")))
            assert canonical.canonical_json(b1) == rt, bid
            bsha = b0["provenance"]["board_sha256"]

            p_art = build_partition_artifact(b0)
            validate_partition_artifact(p_art)
            e_art = build_envelope_artifact(b0, p_art)
            validate_envelope_artifact(e_art)
            c_art, _fp = compile_board(b0)
            assert c_art["coverage"]["coverage_pct"] == 100.0, bid
            schema_loader.validate(c_art, schema_loader.load_schema("compiled_rules.v1.schema.json"),
                                   schema_loader.default_registry(), "")

            for kind, payload in (("partition", p_art), ("envelope", e_art), ("compiled", c_art)):
                data = wrap_json(payload, "v5.%s" % kind, "0.1.0", bsha)
                rel = "%s.%s.json" % (bid, kind)  # tx final 目录=artifacts/，rel 不再带前缀
                tx_art.write_bytes(rel, data)
                files[rel] = sha256_bytes(data)

            if bid in DEMO_BOARDS:
                assert p_art["partitions"], bid
                for entry in p_art["partitions"]:
                    assert entry.get("width_prior", {}).get("w_min") is not None, (bid, entry)

            # 门项 4：demo-01 C1 容量账本手算一致
            if bid == "demo-01-v2-corridor":
                c1 = e_art["corridor_ledger"]["C1"]
                expect = 1.2 + 0.15 + 3.3 + 0.2 + 0.2 + 0.5 * 4  # P1+P2+P4(声明)+P7+P9 + 0.5x相邻对
                assert abs(c1["occupancy_mm"] - expect) < 1e-9, c1
                assert c1["capacity_mm"] == 4.3 and c1["fits"] is False, c1
                checks["capacity_ledger_handcalc"] = {
                    "zone": "C1", "occupancy_mm": c1["occupancy_mm"], "capacity_mm": 4.3,
                    "fits": c1["fits"], "handcalc": "1.2+0.15+3.3+0.2+0.2+0.5*4=7.05>4.3",
                    "note": "C1 全高带声明（builder 偏离已披露）下全部横穿者计入；"
                            "V2 黄金口径 4.0 仍钉在 tests/fixtures_v2.py 不变"}

        # 门项 3：抽检单（demo-01 全部 L1 分区 + demo-02 DF1/PW1）
        d1 = build_partition_artifact(load_board_file(
            os.path.join(BOARD_DIR, "demo-01-v2-corridor.board.v1.json")))
        for entry in d1["partitions"]:
            ref = {}
            for src in entry["source_partitions"]:
                if src in V2_REF:
                    ref[src] = V2_REF[src]
            spot_entries.append({
                "board_id": "demo-01-v2-corridor", "partition_id": entry["partition_id"],
                "ptype": entry["ptype"], "endpoints": entry["geometry"]["endpoints"],
                "layer_policy": entry["layer_policy"], "width_prior": entry["width_prior"],
                "source_partitions": entry["source_partitions"],
                "merged": len(entry["source_partitions"]) > 1,
                "v2_reference_endpoints": ref,
                "check_hint": "对照 V2 分区表（prompt-v2-template.md）与渲染视图逐点核对坐标"})
        d2 = build_partition_artifact(load_board_file(
            os.path.join(BOARD_DIR, "demo-02-mixed-types.board.v1.json")))
        want = {"DF1", "PW1"}
        for entry in d2["partitions"]:
            if entry["partition_id"] in want:
                spot_entries.append({
                    "board_id": "demo-02-mixed-types", "partition_id": entry["partition_id"],
                    "ptype": entry["ptype"], "endpoints": entry["geometry"]["endpoints"],
                    "layer_policy": entry["layer_policy"], "width_prior": entry["width_prior"],
                    "source_partitions": entry["source_partitions"], "merged": False,
                    "v2_reference_endpoints": {},
                    "check_hint": "对照 boards/d/demo-02-mixed-types.board.v1.json 原始分区声明"})
        assert len(spot_entries) == 10, len(spot_entries)
        tx_art.commit()
    except BaseException:
        tx_art.rollback()
        raise

    # ---- 门项 7：视图（3 demo 板 x 三形态）----
    tx_view = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "views")
    try:
        for bid in DEMO_BOARDS:
            b0 = load_board_file(os.path.join(BOARD_DIR, bid + ".board.v1.json"))
            p_art = build_partition_artifact(b0)
            bsha = b0["provenance"]["board_sha256"]
            svg_all = render_l1_view(b0, p_art, mode="all")
            svg_one = render_l1_view(b0, p_art, mode=SINGLE_LAYER)
            html = render_l1_html(b0, p_art)
            assert render_l1_view(b0, p_art, mode="all") == svg_all
            assert render_l1_html(b0, p_art) == html
            for kind, payload in (("l1-all", svg_all), ("l1-fcu", svg_one), ("l1-html", html)):
                data = view_bytes(payload, kind, bid, bsha)
                ext = "html" if payload.lstrip().lower().startswith(("<!doctype", "<html")) else "svg"
                rel = "%s.%s.%s" % (bid, kind, ext)  # tx final 目录=views/
                tx_view.write_bytes(rel, data)
                files[rel] = sha256_bytes(data)
        tx_view.commit()
    except BaseException:
        tx_view.rollback()
        raise

    # ---- 门项 6：provenance 链复算（C2 vga 板 live 复核；全量 10 板在测试套件）----
    sys.path.insert(0, PCB.rsplit("/datasets", 1)[0])
    from v5.adapters.kicad_adapter import convert_file
    mpath = os.path.join(PCB, "manifest.json")
    manifest = json.load(open(mpath, encoding="utf-8"))
    ent = [b for b in manifest["boards"] if b["board_id"] == "vga-panel-breakout"][0]
    src = os.path.join(PCB, ent["dir"], [f for f in ent["files"] if f.endswith(".kicad_pcb")][0])
    bd1 = convert_file(src, "vga-panel-breakout")
    bd2 = convert_file(src, "vga-panel-breakout")
    assert bd1["provenance"]["board_sha256"] == bd2["provenance"]["board_sha256"]
    assert bd1["provenance"]["source_sha256"] == ent["board_file_sha256"]
    checks["provenance_chain"] = {
        "board": "vga-panel-breakout", "double_run_same_hash": True,
        "source_sha256_matches_manifest": True,
        "full_10_board_coverage": "tests/test_kicad_adapter.py（86 例）"}

    # ---- 证据落盘（tx3）----
    summary = {"gate": "P1", "checks": checks, "boards": boards,
               "cleaned_staging_residue": cleaned, "artifact_files_sha256": files,
               "artifact_form_note": "JSON 工件落盘形态=payload+provenance 头包装；"
                                     "schema/形状校验均在包装前对 payload 执行（视图为文本头注释）",
               "manual_spot_check": "PENDING（10 个分区抽检单=gate/spot-check-sheet.json，须用户在场）"}
    tx_gate = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "gate")
    try:
        rel = "gate-summary.json"  # tx final 目录=gate/
        data = wrap_json(summary, "v5.p1-gate", "0.1.0",
                         "0" * 64)  # 门件无单一输入板；占位 hash 由构建器职责披露
        tx_gate.write_bytes(rel, data)
        ev = {"gate": "P1", "taskbook": "V5.0-DEV-TASKBOOK-2026-09-13.md v3.2 (sha256 643c94e3...)",
              "scope": "L1 分区器+L2 包络+L0.5 编译器+KiCad adapter+7 冲突对抗板+视图骨架",
              "dispatch": "6 子智能体并行派发（adapter/L1L2/compiler/demo 板/对抗板/视图），"
                          "交叉冒烟修复 2 处 scope 语法合同缝隙（partition:<id> 形态补齐；对抗板自由标签改选择器）",
              "checks": checks, "files": files}
        rel2 = "p1.evidence.json"
        data2 = wrap_json(ev, "v5.p1-gate", "0.1.0", "0" * 64)
        tx_gate.write_bytes(rel2, data2)
        rel3 = "spot-check-sheet.json"
        sheet = {"purpose": "P1 门人工抽检：10 个分区几何（用户在场执行）",
                 "views_dir": "out/v5-p1/views/（.l1.svg 全层 / .l1-fcu.svg 单层 / .l1-html.html 交互）",
                 "entries": spot_entries}
        data3 = wrap_json(sheet, "v5.p1-gate", "0.1.0", "0" * 64)
        tx_gate.write_bytes(rel3, data3)
        tx_gate.commit()
    except BaseException:
        tx_gate.rollback()
        raise

    print("P1 gate artifacts committed:")
    for rel in sorted(files):
        print("  %s  %s" % (files[rel][:12], rel))
    print("gate-summary: %d checks green; spot-check entries=%d" % (len(checks), len(spot_entries)))


if __name__ == "__main__":
    main()
