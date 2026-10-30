"""R1：`pcbflow/copper_loop.py`（回路驱动）+ `copper` CLI 的验收测试。

覆盖任务书 §2 的五类：
1) 端到端（Rev-C 只读基准 + 临时 out）：目录结构、三向违规数=0、patch verdict、
   staging 计数、awaiting_drc；
2) accept 三条路径（坏报告 → blocked；有新增违例 → rejected；无违例 → accepted）
   —— 另加"基线 keyset 只算新增"的反证；
3) adopt 两条路径（先改设计目标 → stale blocked；正常 → 通过 + 备份存在）；
4) 追加式（同 base 连两轮 → rev-1/rev-2 并存且 rev-1 字节未变；重复同一 N →
   fail-closed）；
5) KiCad5（datasets/pcbench-r1/raw 任一板 → 镜像可用、patch 被
   edit_unsupported_identity_basis 拒绝）。

临时目录纪律（**本会话沙箱实测**，勿改）：
* **不用 `tempfile.mkdtemp()`**：本沙箱下 mkdtemp 建出的目录既不可写
  （`PermissionError`）也不可删；pytest 的 `tmp_path`/`tmp_path_factory`
  因此在本环境整体 ERROR（151 errors 环境噪声），本文件一个都不用。
* 一律 `os.makedirs()` 在 `<repo>/out/copper-loop-r1-tests/<run>/` 下建
  scratch（实测可写、可 rmtree），module teardown 清理。
* 读板/读 svg 一律 `open(..., encoding="utf-8", newline="")`（CRLF 保真）。
* **不写 design/**：adopt 类测试的"设计侧目标"一律是 scratch 里的副本。
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import time

import pytest

import revc_board_fixture
from pcbflow import cli, config, copper_loop, copper_model

# REPAIR-P1 W-5（铜环案 R4 三步法②）：真实板基准钉仓内冻结夹具板
# tests/fixtures/revc-live-dbfea089/（与 2026-09-11 live 板逐字节同，sha 锚
# fail-closed 校验；文件名保留 stm32h743-coreboard-revc.kicad_pcb，DRC
# source/文件清单断言不变）。全文件 M1 精确计数/字节口径原样保留，仅与
# live 板演进解耦；live 板不变量另见 test_revc_live_invariants_only。
REVC = revc_board_fixture.fixture_board()
PCBFLOW_ROOT = config.PCBFLOW_ROOT
SCRATCH_ROOT = os.path.join(PCBFLOW_ROOT, "out", "copper-loop-r1-tests")
_RUN_TAG = "run-%d-%d" % (os.getpid(), int(time.time()) % 100000)
#: KiCad5 语料（R1 判据 g）：任取一板（`(module …)` 板，无 kicad_uuid）
K5_BOARDS = sorted(__import__("glob").glob(os.path.join(
    PCBFLOW_ROOT, "datasets", "pcbench-r1", "raw", "*", "*.kicad_pcb")))
#: 仓库历史 DRC 产物（真实 kicad-cli 报告；只读，用其形状/版本做校验输入）
REAL_DRC = os.path.join(PCBFLOW_ROOT, "out", "coreboard-pa1", "baseline-copy",
                        "drc-error.json")


# --------------------------------------------------------------- 基础设施

def _scratch(*parts: str) -> str:
    """scratch 目录（`os.makedirs`，见模块 docstring：mkdtemp 在本沙箱不可用）。"""
    d = os.path.join(SCRATCH_ROOT, _RUN_TAG, *parts)
    os.makedirs(d, exist_ok=True)
    return d


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8", newline="") as f:      # CRLF 保真
        return f.read()


def _sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree(root: str) -> dict:
    """{相对路径(POSIX): sha256} 全量快照（追加式/不覆写证据用）。"""
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            out[rel] = _sha_file(p)
    return out


def _bare_lf(text: str) -> int:
    """裸 LF 计数（CRLF 板应为 0；任务书 §8.2 的陷阱）。"""
    return text.count("\n") - text.count("\r\n")


def _rel_files(root: str) -> list:
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            out.append(os.path.relpath(os.path.join(dirpath, name), root)
                       .replace(os.sep, "/"))
    return sorted(out)


def _lock_version() -> str:
    with open(os.path.join(PCBFLOW_ROOT, "toolchain_lock.json"),
              encoding="utf-8") as f:
        return (json.load(f).get("kicad_cli") or {}).get("version")


def _violation(vtype, desc, x=1.0, y=2.0, uuid=None):
    """kicad-cli DRC JSON 的 violation 条目形状（同真实报告字段集）。"""
    if uuid is None:
        seed = hashlib.sha256(("%s|%s" % (vtype, desc)).encode("utf-8"))
        uuid = "%s-0000-0000-0000-000000000000" % seed.hexdigest()[:8]
    return {"description": desc,
            "items": [{"description": desc, "pos": {"x": x, "y": y},
                       "uuid": uuid}],
            "severity": "error", "type": vtype}


def _drc_report(source_basename: str, violations=(), unconnected=(),
                version=None, schema="https://schemas.kicad.org/drc.v1.json"):
    """构造 DRC 报告（字段集与 out/coreboard-pa1/**/drc-error.json 实测一致）。"""
    return {"$schema": schema, "coordinate_units": "mm",
            "date": "2026-09-11T00:00:00", "ignored_checks": [],
            "included_severities": ["error"],
            "kicad_version": _lock_version() if version is None else version,
            "schematic_parity": [], "source": source_basename,
            "violations": list(violations),
            "unconnected_items": list(unconnected)}


def _write_json(path: str, obj) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return path


def _write_raw(path: str, text: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return path


@pytest.fixture(scope="module", autouse=True)
def _scratch_lifecycle():
    """本模块 scratch 的收尾清理（失败也不留垃圾）。"""
    os.makedirs(os.path.join(SCRATCH_ROOT, _RUN_TAG), exist_ok=True)
    yield
    shutil.rmtree(os.path.join(SCRATCH_ROOT, _RUN_TAG), ignore_errors=True)


# ------------------------------------------------------------------- fixtures

@pytest.fixture(scope="module")
def revc():
    """Rev-C 事实（只读基准；一次 parse_copper 供全模块复用）。"""
    assert os.path.isfile(REVC), "Rev-C 基准板不存在"
    text = _read_text(REVC)
    copper = copper_model.parse_copper(text)
    return {"path": REVC, "text": text, "copper": copper,
            "sha256": _sha_file(REVC), "bytes": len(text.encode("utf-8"))}


@pytest.fixture(scope="module")
def modify_op(revc):
    """对 Rev-C 一条 In2.Cu 走线改线宽的 modify op（expect 抄自 copper_model）。"""
    seg = next(e for e in revc["copper"]["segments"] if e["layer"] == "In2.Cu")
    expect = {k: seg[k] for k in ("net", "layer", "width", "start", "end")}
    return {"op": "modify", "kind": "segment", "key": seg["key"],
            "expect": expect, "new": {"width": 0.25}}, seg


@pytest.fixture(scope="module")
def revc_e2e(revc, modify_op):
    """端到端一轮 `revision()`（Rev-C 只读基准 + 临时 out）—— 共享只读。"""
    out_dir = _scratch("revc-e2e")
    patch_set = {"patch_set_id": "r1-e2e", "ops": [modify_op[0]]}
    sha_before = _sha_file(REVC)
    started = time.time()
    rec = copper_loop.revision(REVC, patch_set, out_dir, base_label="e2e")
    elapsed = time.time() - started
    rev_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "e2e", "rev-1")
    return {"out_dir": out_dir, "rev_dir": rev_dir, "record": rec,
            "elapsed_s": elapsed, "sha_before": sha_before,
            "sha_after": _sha_file(REVC), "patch_set": patch_set}


@pytest.fixture(scope="module")
def revc_rejected(revc, modify_op):
    """一轮 patch + accept：基线有 3 条违例、staging 报告多出第 4 条 → rejected。

    用于同时证明：(a) 有新增违例 ⇒ rejected；(b) 基线 keyset 只算**新增**
    （3 条旧违例被宽免，violations_new == 1 而非 4）；(c) rollback 路径。
    """
    out_dir = _scratch("revc-rejected")
    text = revc["text"]
    rec = copper_loop.revision(REVC, {"ops": [modify_op[0]]}, out_dir,
                               base_label="rej")
    assert rec["status"] == copper_loop.STATUS_AWAITING_DRC, rec["reasons"]
    rev_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "rej", "rev-1")
    staging_base = os.path.basename(REVC)
    old = [_violation("copper_edge_clearance", "旧违例 A", 1.0, 1.0),
           _violation("clearance", "旧违例 B", 2.0, 2.0),
           _violation("track_dangling", "旧违例 C", 3.0, 3.0)]
    new = _violation("shorting_items", "新违例 D（staging 引入）", 4.0, 4.0)
    _write_json(os.path.join(rev_dir, "drc", "baseline.json"),
                _drc_report(staging_base, violations=old))
    report = _write_json(os.path.join(_scratch("revc-rejected-in"),
                                      "staging-report.json"),
                         _drc_report(staging_base, violations=old + [new]))
    # 供后续 verify 测试用的 staging 板副本（脱离版本目录，rollback 删不到）
    staging_copy = os.path.join(_scratch("revc-rejected-in"), "staging.kicad_pcb")
    shutil.copyfile(os.path.join(rev_dir, "patched", staging_base), staging_copy)
    decision = copper_loop.accept_revision(rev_dir, report)
    with open(os.path.join(rev_dir, "drc", "accept-record.json"),
              encoding="utf-8") as f:
        accept_record = json.load(f)
    return {"out_dir": out_dir, "rev_dir": rev_dir, "decision": decision,
            "accept_record": accept_record, "staging_copy": staging_copy,
            "staging_base": staging_base}


@pytest.fixture(scope="module")
def revc_accepted(revc, modify_op):
    """一轮 patch + accept（无基线 + 0 违例报告）→ accepted（供 adopt 测试）。"""
    out_dir = _scratch("revc-accepted")
    rec = copper_loop.revision(REVC, {"ops": [modify_op[0]]}, out_dir,
                               base_label="acc")
    assert rec["status"] == copper_loop.STATUS_AWAITING_DRC, rec["reasons"]
    rev_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "acc", "rev-1")
    report = _write_json(os.path.join(_scratch("revc-accepted-in"),
                                      "drc-clean.json"),
                         _drc_report(os.path.basename(REVC)))
    decision = copper_loop.accept_revision(rev_dir, report)
    return {"out_dir": out_dir, "rev_dir": rev_dir, "decision": decision,
            "report": report}


# ------------------------------------------------------------------ 1) 合同

def test_module_contract_and_exports():
    """R1 审计基线：模块暴露任务书点名的常量/入口，状态串与文档一致。"""
    assert copper_loop.SCHEMA == "pcbflow.copper-loop/1"
    assert copper_loop.LOOP_DIRNAME == "copper-loop"
    assert copper_loop.REASON_EDIT_UNSUPPORTED_IDENTITY == \
        "edit_unsupported_identity_basis"
    assert copper_loop.MIRROR_MODE_DEGRADED == "copper_only_degraded"
    assert copper_loop.MIRROR_MODE_ADAPTER == "adapter"
    assert (copper_loop.STATUS_MIRROR_ONLY, copper_loop.STATUS_AWAITING_DRC,
            copper_loop.STATUS_ACCEPTED, copper_loop.STATUS_REJECTED,
            copper_loop.STATUS_BLOCKED, copper_loop.STATUS_ROLLED_BACK) == (
        "mirror_only", "awaiting_drc", "accepted", "rejected", "blocked",
        "rolled_back")
    for name in ("identity_registry_from_board", "core_fact_sha256",
                 "mirror_revision", "patch_revision", "revision",
                 "accept_revision", "rollback_revision", "adopt"):
        assert name in copper_loop.__all__ and callable(
            getattr(copper_loop, name)), name
    # 签名（R3 挂钩点不得漂移）：参数名与 kind 逐一钉死（注解文本不钉）
    import inspect

    def _params(fn):
        return [(p.name, p.kind.name)
                for p in inspect.signature(fn).parameters.values()]

    assert _params(copper_loop.revision) == [
        ("base_board_path", "POSITIONAL_OR_KEYWORD"),
        ("patch_set", "POSITIONAL_OR_KEYWORD"),
        ("out_dir", "POSITIONAL_OR_KEYWORD"),
        ("registry", "KEYWORD_ONLY"),
        ("scenario_id", "KEYWORD_ONLY"),
        ("base_label", "KEYWORD_ONLY")]
    assert _params(copper_loop.mirror_revision) == [
        ("base_board_path", "POSITIONAL_OR_KEYWORD"),
        ("out_dir", "POSITIONAL_OR_KEYWORD"),
        ("registry", "KEYWORD_ONLY"),
        ("scenario_id", "KEYWORD_ONLY"),
        ("base_label", "KEYWORD_ONLY")]
    assert _params(copper_loop.accept_revision) == [
        ("revision_dir", "POSITIONAL_OR_KEYWORD"),
        ("drc_report_path", "POSITIONAL_OR_KEYWORD")]
    assert _params(copper_loop.adopt) == [
        ("revision_dir", "POSITIONAL_OR_KEYWORD"),
        ("design_board_path", "POSITIONAL_OR_KEYWORD")]
    assert _params(copper_loop.rollback_revision) == [
        ("revision_dir", "POSITIONAL_OR_KEYWORD")]
    assert _params(copper_loop.patch_revision) == [
        ("revision_dir", "POSITIONAL_OR_KEYWORD"),
        ("patch_set", "POSITIONAL_OR_KEYWORD")]


def test_zero_subprocess_and_network_in_package():
    """红线：pcbflow 内零子进程、零网络（AST 级：import/调用都不许有）。

    注：任务书给的文本型 grep 口径（`subprocess|socket|urllib|requests|
    os.system|popen`）在 copper_loop.py 上会命中 1 行 —— 那是 DRC 请求
    产物的 JSON 键名 `"requests"`（drc/request.json 的请求列表，纯数据，
    非 HTTP 库）。此处以 AST 为准（import 与调用级零命中），文本级改为
    查"import 形态"，避免把该数据键误判成网络依赖。
    """
    forbidden_imports = {"subprocess", "socket", "urllib", "urllib2",
                         "requests", "httpx", "http.client", "asyncio"}
    forbidden_calls = {("os", "system"), ("os", "popen"), ("os", "spawnv"),
                       ("os", "execv"), ("subprocess", "run"),
                       ("subprocess", "Popen")}
    for name in ("copper_loop.py", "cli.py"):
        src = open(os.path.join(PCBFLOW_ROOT, "pcbflow", name),
                   encoding="utf-8").read()
        tree = ast.parse(src, name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    assert a.name.split(".")[0] not in forbidden_imports, \
                        "%s:%d import %s" % (name, node.lineno, a.name)
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                assert root not in forbidden_imports, \
                    "%s:%d from %s" % (name, node.lineno, node.module)
            elif isinstance(node, ast.Call) and \
                    isinstance(node.func, ast.Attribute) and \
                    isinstance(node.func.value, ast.Name):
                pair = (node.func.value.id, node.func.attr)
                assert pair not in forbidden_calls, \
                    "%s:%d 调用 %s.%s" % (name, node.lineno, *pair)
        for token in ("import subprocess", "import socket", "import urllib",
                      "import requests", "from subprocess", "from socket",
                      "from urllib", "from requests", "os.system", "os.popen",
                      "os.spawn", "os.exec"):
            assert token not in src, "%s 含 %r" % (name, token)


def test_cli_registers_all_six_copper_subcommands():
    """CLI 可达性：6 个子命令都在 parser 里（不是只被测试调用的死代码）。"""
    assert cli.COPPER_SUBCOMMANDS == ("mirror", "patch", "verify", "accept",
                                      "rollback", "adopt")
    # 通过 --help 真实走一遍 argparse（每个子命令独立 subparser）
    for sub in cli.COPPER_SUBCOMMANDS:
        with pytest.raises(SystemExit) as ei:
            cli.main(["copper", sub, "--help"])
        assert ei.value.code == 0, sub
    # exit-code 契约表（config 常量对照）
    assert cli.COPPER_STATUS_EXIT["mirror_only"] == config.EXIT_OK
    assert cli.COPPER_STATUS_EXIT["awaiting_drc"] == config.EXIT_OK
    assert cli.COPPER_STATUS_EXIT["accepted"] == config.EXIT_OK
    assert cli.COPPER_STATUS_EXIT["rolled_back"] == config.EXIT_OK
    assert cli.COPPER_STATUS_EXIT["clean"] == config.EXIT_OK
    assert cli.COPPER_STATUS_EXIT["rejected"] == config.EXIT_FAILED
    assert cli.COPPER_STATUS_EXIT["blocked"] == config.EXIT_BLOCKED
    assert cli.COPPER_STATUS_EXIT["violations"] == config.EXIT_BLOCKED
    assert cli._copper_exit({"status": "???"}) == config.EXIT_UNKNOWN
    assert cli._copper_exit({"verdict": "blocked"}) == config.EXIT_BLOCKED


# --------------------------------------------------- 1) 端到端（Rev-C 只读）

def test_revc_base_readonly_and_identity_facts(revc, revc_e2e):
    """基准板只读：整轮 revision() 前后 Rev-C 字节未变；摄取事实与 §0 一致。"""
    assert revc_e2e["sha_before"] == revc_e2e["sha_after"] == revc["sha256"]
    base = revc_e2e["record"]["base"]
    # M1 刷新：APPLY-1 落线后 dbfea089 板实测口径（REPAIR-P1 W-5 钉夹具板，仅解耦）
    assert base["bytes"] == revc["bytes"] == 1445179
    assert base["copper_counts"] == {"segments": 2372, "vias": 358, "zones": 2}
    assert base["identity_basis"] == copper_model.IDENTITY_KICAD_UUID
    assert base["copper_sha256"].startswith("c4a46878")
    assert base["eol"] == "crlf"                    # 纯 CRLF 板
    assert base["unrepresentable"] == []
    assert base["read_only"] is True
    # 基准副本逐字节等于源板
    copy = os.path.join(revc_e2e["rev_dir"], base["copy"])
    assert _sha_file(copy) == revc["sha256"]
    assert _read_text(copy) == revc["text"]


def test_e2e_revision_status_and_directory_structure(revc_e2e):
    """判据 a/e：流程完整、状态 awaiting_drc、版本目录形状与文档一致。"""
    rec = revc_e2e["record"]
    assert rec["schema"] == copper_loop.SCHEMA
    assert rec["revision_id"] == "e2e/rev-1" and rec["rev"] == 1
    assert rec["status"] == "awaiting_drc" and rec["verdict"] == "awaiting_drc"
    assert rec["ok"] is True and rec["usable"] is False
    assert rec["persisted"] is True and rec["reasons"] == []
    assert rec["rollback"] == "armed"                # 判据 c：armed 台账
    assert rec["adopted"] is False
    assert rec["stage"] == "drc" and rec["blocked_at"] is None
    assert rec["base_label"] == "e2e"
    assert rec["registry"]["basis"] == "derived_identity_from_board"
    assert rec["registry"]["nets"] == 192
    assert rec["mirror"]["mode"] == copper_loop.MIRROR_MODE_ADAPTER
    assert rec["mirror"]["degraded"] is False
    # M1 刷新：mirror counts=dbfea089 夹具板实测（2372/358/2/564，仅钉板）
    assert rec["mirror"]["counts"] == {"routes": 2372, "vias": 358,
                                       "zones": 2, "pads": 564}
    assert _rel_files(revc_e2e["rev_dir"]) == [
        "base/reference.json", "base/stm32h743-coreboard-revc.kicad_pcb",
        "drc/request.json", "ledger.json", "mirror/adapter-report.json",
        "mirror/binding-report.json", "mirror/board.svg",
        "mirror/route-manifest.json", "mirror/three-way.json",
        "patch-set.json", "patched/stm32h743-coreboard-revc.kicad_pcb",
        "revision-record.json"]
    # 事务：staging 已入批、未执行 DRC、live_board_touched 恒 false
    txn = rec["transaction"]
    assert txn["live_board_touched"] is False
    assert txn["rollback"] == "none" and txn["final_board_sha256"] is None
    assert txn["write_scope"] == {"rows": 0, "segments": 1, "vias": 0,
                                  "footprints": 0}
    assert txn["batches"] == [{"batch_id": "rev-1",
                               "staging_sha256": rec["patch"]["staging_sha256"],
                               "drc_batch_status": "not_executed"}]
    assert revc_e2e["elapsed_s"] > 0


def test_e2e_three_way_zero_violations_and_leg_equivalence(revc_e2e):
    """判据 a：三向校验两条腿都跑且违规数=0；binding_report 与
    verify_board_binding 同口径（同一 `_bind`）—— 实测等价。"""
    from pcbflow import board_binding, svg_route_package
    rd = revc_e2e["rev_dir"]
    three = json.load(open(os.path.join(rd, "mirror", "three-way.json"),
                           encoding="utf-8"))
    assert three["violations_total"] == 0 and three["verdict"] == "clean"
    assert three["board_binding"]["violations"] == []
    assert three["svg_manifest"]["violations"] == []
    assert three["net_map_keys"] == 192
    manifest = json.load(open(os.path.join(rd, "mirror",
                                           "route-manifest.json"),
                              encoding="utf-8"))
    svg = _read_text(os.path.join(rd, "mirror", "board.svg"))
    assert len(svg_route_package.verify_consistency(svg, manifest)) == 0
    net_map = copper_loop._net_map_from_registry(
        copper_loop.identity_registry_from_board(REVC))
    board_text = _read_text(os.path.join(rd, "base", os.path.basename(REVC)))
    report = board_binding.binding_report(board_text, manifest, net_map)
    assert report["violations"] == []
    assert board_binding.verify_board_binding(board_text, manifest, net_map) \
        == report["violations"] == []
    # M1 刷新：binding counts=dbfea089 夹具板实测（2372/358，仅钉板）
    assert report["counts"]["paired_segments"] == 2372
    assert report["counts"]["paired_vias"] == 358
    assert report["counts"]["paired_zones"] == 2
    assert report["counts"]["board_segments"] == 2372
    assert "zone_fill_derived_not_a_violation_basis" in report["pending"]
    # 快照 hash 绑定：镜像用的 board 快照 hash 与 manifest 一致
    assert manifest["board_snapshot_sha256"] == \
        revc_e2e["record"]["mirror"]["board_snapshot_sha256"]
    assert manifest["schema_version"] == "v4-route-manifest-2"


def test_three_way_fails_closed_on_manifest_tamper(revc_e2e):
    """防 fail-open 反证：篡改 manifest 几何 ⇒ 两条腿都报违例（非静默通过）。"""
    import copy as _copy
    from pcbflow import board_binding, svg_route_package
    rd = revc_e2e["rev_dir"]
    manifest = json.load(open(os.path.join(rd, "mirror",
                                           "route-manifest.json"),
                              encoding="utf-8"))
    svg = _read_text(os.path.join(rd, "mirror", "board.svg"))
    bad = _copy.deepcopy(manifest)
    bad["routes"][0]["width_mm"] = round(bad["routes"][0]["width_mm"] + 0.5, 3)
    svg_viol = svg_route_package.verify_consistency(svg, bad)
    assert svg_viol, "篡改 manifest 后 SVG 腿必须报违例（不得静默通过）"
    assert any("manifest_payload_sha256" in v for v in svg_viol)
    board_text = _read_text(os.path.join(rd, "base", os.path.basename(REVC)))
    net_map = copper_loop._net_map_from_registry(
        copper_loop.identity_registry_from_board(REVC))
    bind_viol = board_binding.verify_board_binding(board_text, bad, net_map)
    assert any("route_width_mismatch" in v for v in bind_viol), bind_viol


def test_e2e_patch_verdict_counts_and_line_endings(revc_e2e):
    """判据 a：patch verdict/结构守卫/字节保真/CRLF 零劣化/staging 计数。"""
    rec = revc_e2e["record"]
    patch = rec["patch"]
    assert patch["verdict"] == "accepted"
    assert (patch["ops_total"], patch["ops_applied"]) == (1, 1)
    assert (patch["adds"], patch["modifies"], patch["deletes"]) == (0, 1, 0)
    assert patch["structural_guard_ok"] is True
    assert patch["unchanged_bytes_outside_targets"] is True
    assert patch["eol"] == "\r\n"                    # 继承板主导行尾
    # M1 刷新：counts=dbfea089 夹具板实测（2372/358；modify 不改计数，仅钉板）
    assert patch["counts_before"] == patch["counts_after"] == \
        {"segments": 2372, "vias": 358, "zones": 2}
    assert patch["kind_counts"] == {"segments": 1, "vias": 0}
    staging = os.path.join(revc_e2e["rev_dir"], patch["staging"])
    assert os.path.isfile(staging)
    assert _sha_file(staging) == patch["staging_sha256"]
    base_text = _read_text(os.path.join(revc_e2e["rev_dir"], "base",
                                        os.path.basename(REVC)))
    staging_text = _read_text(staging)
    assert _bare_lf(base_text) == 0 and _bare_lf(staging_text) == 0
    assert staging_text.count("\r\n") == base_text.count("\r\n")
    assert staging_text != base_text                 # 确实改了目标节点
    # 唯一文本增量 = 目标节点里 `(width 1)` → `(width 0.25)`（+3 字节）；
    # 目标节点外的字节保真由 patch.unchanged_bytes_outside_targets 实证
    assert len(staging_text) - len(base_text) == 3
    assert "(width 0.25)" in staging_text
    assert staging_text.count("(width 0.25)") == 1
    # DRC 请求：只产请求、绝不自调 kicad-cli
    req = json.load(open(os.path.join(revc_e2e["rev_dir"], "drc",
                                      "request.json"), encoding="utf-8"))
    assert req["schema"] == copper_loop.DRC_REQUEST_SCHEMA
    assert req["refill_zones"] is True
    assert req["severity_scope"] == ["error"]
    assert [r["request_id"] for r in req["requests"]] == ["staging", "baseline"]
    assert all(r["kicad_cli_command"].startswith("kicad-cli pcb drc")
               for r in req["requests"])
    assert req["requests"][0]["board_sha256"] == patch["staging_sha256"]
    assert req["requests"][1]["board_sha256"] == rec["base"]["sha256"]
    assert req["toolchain"]["kicad_cli_version"] == _lock_version()
    # 台账：mirror_written → staging_written 事件流 + 完整 patch_ledger
    led = json.load(open(os.path.join(revc_e2e["rev_dir"], "ledger.json"),
                         encoding="utf-8"))
    assert [e["event"] for e in led["events"]][:2] == ["mirror_written",
                                                     "staging_written"]
    assert [e["seq"] for e in led["events"]] == list(range(len(led["events"])))
    assert led["patch_ledger"]["unchanged_bytes_outside_targets"] is True
    assert led["patch_ledger"]["structural_guard"]["ok"] is True


def test_e2e_core_fact_sha256_and_canonical_no_host_paths(revc_e2e):
    """判据 f：core_fact_sha256 可独立重算；核心事实无 wall-clock/主机路径。"""
    import re
    rec = revc_e2e["record"]
    assert copper_loop.core_fact_sha256(rec) == rec["core_fact_sha256"]
    body = {k: v for k, v in rec.items() if k != "evaluation_metadata"}
    abs_re = re.compile(r"[A-Za-z]:[\\/]|^/|^\\\\")
    hits = []

    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, path + "." + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + "[%d]" % i)
        elif isinstance(o, str) and abs_re.search(o):
            hits.append((path, o[:80]))

    walk(body)
    assert hits == [], "核心事实含主机绝对路径: %s" % hits[:3]
    blob = json.dumps(body, ensure_ascii=False)
    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", blob), \
        "核心事实含 wall-clock"
    meta = rec["evaluation_metadata"]
    assert meta["excluded_from_core_fact_sha256"] is True
    assert meta["evaluated_at"] is None and meta["host"] is None
    assert meta["elapsed_s"] is None
    assert meta["observed"]["elapsed_s"] > 0
    assert meta["observed"]["wall_clock_utc"].endswith("Z")
    assert abs_re.search(meta["resolved_paths"]["revision_dir"])
    # 核心产物的 canonical 落盘：stdout 同构 + 逐字节含结尾换行
    raw = open(os.path.join(revc_e2e["rev_dir"], "revision-record.json"),
               "rb").read()
    assert raw.endswith(b"\n")
    assert b"\r\n" not in raw
    assert json.loads(raw.decode("utf-8"))["core_fact_sha256"] == \
        rec["core_fact_sha256"]


def test_patch_set_canonical_guard_and_evaluation_metadata_exclusion(revc_e2e):
    """判据 f：补丁集禁宿主绝对路径；evaluation_metadata 不进 core_fact_sha256。"""
    clean, reason = copper_loop._sanitize_patch_set(
        {"ops": [{"op": "modify", "kind": "segment", "key": "k",
                  "note": r"C:\Users\x\board.kicad_pcb"}]})
    assert clean is None and "absolute_path_forbidden" in reason
    clean, reason = copper_loop._sanitize_patch_set({"ops": []})
    assert reason is None and clean == {"schema": copper_loop.PATCH_SET_SCHEMA,
                                        "ops": []}
    clean, _ = copper_loop._sanitize_patch_set(
        {"ops": [], "patch_set_id": "x", "note": "n",
         "baseline_drc_report": "out/drc/baseline.json"})
    assert clean["baseline_drc_declared"] is True
    assert clean["baseline_drc_basename"] == "baseline.json"
    assert "baseline_drc_report" not in clean          # 只留基名，不留路径
    # evaluation_metadata 任意变化不影响核心事实 hash
    rec = revc_e2e["record"]
    h = rec["core_fact_sha256"]
    mutated = dict(rec)
    mutated["evaluation_metadata"] = {"evaluated_at": "2026-01-01T00:00:00Z",
                                      "host": "OTHER-HOST", "elapsed_s": 999}
    assert copper_loop.core_fact_sha256(mutated) == h
    mutated2 = dict(rec)
    mutated2["status"] = "tampered"
    assert copper_loop.core_fact_sha256(mutated2) != h


def test_determinism_two_mirrors_same_core_fact(revc):
    a = _scratch("det-a")
    b = _scratch("det-b")
    ra = copper_loop.mirror_revision(REVC, a, base_label="same")
    rb = copper_loop.mirror_revision(REVC, b, base_label="same")
    assert ra["core_fact_sha256"] == rb["core_fact_sha256"]
    ra_dir = os.path.join(a, copper_loop.LOOP_DIRNAME, "same", "rev-1")
    rb_dir = os.path.join(b, copper_loop.LOOP_DIRNAME, "same", "rev-1")
    for rel in ("base/reference.json", "mirror/route-manifest.json",
                "mirror/three-way.json", "mirror/binding-report.json",
                "mirror/board.svg"):
        assert _sha_file(os.path.join(ra_dir, rel)) == \
            _sha_file(os.path.join(rb_dir, rel)), rel
    assert ra["evaluation_metadata"]["resolved_paths"]["revision_dir"] != \
        rb["evaluation_metadata"]["resolved_paths"]["revision_dir"]


# ------------------------------------------------------------- 2) accept

def test_accept_blocked_paths_keep_round_awaiting(revc_e2e):
    """判据 b 前半：报告缺失/不可解析/结构不符/版本不符/来源不符 ⇒ blocked，
    且**不改轮次状态**（仍是 awaiting_drc；修好报告可重试）。"""
    rd = revc_e2e["rev_dir"]
    staging_base = os.path.basename(REVC)
    cases = [
        ("missing", os.path.join(_scratch("acc-bad"), "nope.json"),
         "drc_report_missing"),
        ("unparseable", _write_raw(os.path.join(_scratch("acc-bad"),
                                                "bad.json"), "{not json"),
         "drc_report_unparseable"),
        ("structure", _write_json(os.path.join(_scratch("acc-bad"), "s.json"),
                                  {"violations": []}),
         "drc_report_structure_invalid"),
        ("version", _write_json(os.path.join(_scratch("acc-bad"), "v.json"),
                                _drc_report(staging_base, version="9.0.0")),
         "kicad_version_mismatch"),
        ("source", _write_json(os.path.join(_scratch("acc-bad"), "src.json"),
                               _drc_report("other-board.kicad_pcb")),
         "drc_report_source_mismatch"),
    ]
    for name, path, token in cases:
        res = copper_loop.accept_revision(rd, path)
        assert res["status"] == copper_loop.STATUS_BLOCKED, name
        assert res["persisted"] is False, name
        assert res["revision_status"] == "awaiting_drc", name
        assert any(token in r for r in res["reasons"]), (name, res["reasons"])
        on_disk = json.load(open(os.path.join(rd, "revision-record.json"),
                                 encoding="utf-8"))
        assert on_disk["status"] == "awaiting_drc", name
        assert on_disk["usable"] is False
    # 拒绝事实进台账（可审计），且不改轮次记录
    led = json.load(open(os.path.join(rd, "ledger.json"), encoding="utf-8"))
    assert sum(1 for e in led["events"] if e["event"] == "accept_refused") == 5


def test_accept_not_awaiting_is_refused_without_pollution(revc_accepted):
    """已 accepted 的轮次再 accept ⇒ blocked（拒绝尝试，不改轮次状态）。"""
    rd = revc_accepted["rev_dir"]
    before = _sha_file(os.path.join(rd, "revision-record.json"))
    res = copper_loop.accept_revision(rd, revc_accepted["report"])
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert res["persisted"] is False
    assert res["revision_status"] == "accepted"
    assert any("accept_requires_awaiting_drc" in r for r in res["reasons"])
    assert _sha_file(os.path.join(rd, "revision-record.json")) == before


def test_accept_rejected_counts_only_new_violations(revc_rejected):
    """判据 b 中段：对基线 keyset 有新增 ⇒ rejected（只算新增：1 而非 4）。"""
    rec = revc_rejected["decision"]
    ar = revc_rejected["accept_record"]
    assert rec["status"] == copper_loop.STATUS_REJECTED
    assert rec["verdict"] == "rejected" and rec["ok"] is False
    assert rec["usable"] is False and rec["rollback"] == "executed"
    assert rec["staging_removed"] is None
    assert ar["verdict"] == "rejected"
    assert ar["baseline_used"] is True
    assert ar["baseline_note"] is None
    assert ar["violations_total"] == 4 and ar["violations_new"] == 1
    assert len(ar["violations_new_keys"]) == 1
    assert ar["kicad_version"] == ar["toolchain_lock_version"] == _lock_version()
    assert ar["staging_sha256"] == \
        json.load(open(os.path.join(revc_rejected["rev_dir"],
                                    "revision-record.json"),
                       encoding="utf-8"))["patch"]["staging_sha256"]
    assert rec["drc_decision"]["violations_new"] == 1
    # staging 保留供排查（rejected 不删证据）
    assert os.path.isfile(os.path.join(revc_rejected["rev_dir"], "patched",
                                       revc_rejected["staging_base"]))
    txn = json.load(open(os.path.join(revc_rejected["rev_dir"],
                                      "revision-record.json"),
                         encoding="utf-8"))["transaction"]
    assert txn["rollback"] == "executed" and txn["final_board_sha256"] is None
    assert txn["batches"][0]["drc_batch_status"] == "fail"


def test_accept_accepted_path_commits_transaction(revc_accepted):
    """判据 b 后半：无违例 ⇒ accepted（事务 commit、报告留档、usable=True）。"""
    rec = revc_accepted["decision"]
    rd = revc_accepted["rev_dir"]
    assert rec["status"] == copper_loop.STATUS_ACCEPTED
    assert rec["ok"] is True and rec["usable"] is True
    assert rec["rollback"] == "none" and rec["reasons"] == []
    ar = json.load(open(os.path.join(rd, "drc", "accept-record.json"),
                        encoding="utf-8"))
    assert ar["verdict"] == "accepted" and ar["violations_new"] == 0
    assert ar["baseline_used"] is False
    assert "baseline_missing" in (ar["baseline_note"] or "")
    assert ar["drc_report_copied_to"] == "drc/received-drc-clean.json"
    assert os.path.isfile(os.path.join(rd, "drc", "received-drc-clean.json"))
    txn = json.load(open(os.path.join(rd, "revision-record.json"),
                         encoding="utf-8"))["transaction"]
    assert txn["final_board_sha256"] == ar["staging_sha256"]
    assert txn["batches"][0]["drc_batch_status"] == "pass"
    assert txn["rollback"] == "none" and txn["live_board_touched"] is False
    led = json.load(open(os.path.join(rd, "ledger.json"), encoding="utf-8"))
    decided = [e for e in led["events"] if e["event"] == "drc_accepted"]
    assert len(decided) == 1 and decided[0]["violations_new"] == 0
    assert decided[0]["violations_total"] == 0 and decided[0]["baseline_used"] is False


@pytest.mark.skipif(not os.path.isfile(REAL_DRC),
                    reason="仓库真实 kicad-cli DRC 报告不在位")
def test_accept_validates_real_kicad_cli_report_shape():
    """真实 kicad-cli 10.0.5 报告可通过结构/来源/工具链校验（实数据反证）。"""
    with open(REAL_DRC, encoding="utf-8") as f:
        report = json.load(f)
    lock = copper_loop._toolchain_lock()
    assert lock is not None
    errs = copper_loop._validate_drc_report(report,
                                            os.path.basename(REVC), lock)
    assert errs == [], errs
    assert len(copper_loop._violation_keyset(report, "violations")) == 10
    assert report["source"] == os.path.basename(REVC)


# ------------------------------------------------------------- 3) adopt

def test_adopt_stale_then_ok_then_locked(revc_accepted):
    """判据 d：stale（设计侧被改）⇒ blocked 且不改轮次；正常 ⇒ 通过 + 备份
    存在 + 前后 sha 台账；adopt 后再 adopt/rollback 均被拒且不改轮次。"""
    rd = revc_accepted["rev_dir"]
    design_dir = _scratch("revc-accepted-design")
    design = os.path.join(design_dir, os.path.basename(REVC))
    shutil.copyfile(REVC, design)
    assert not design.startswith(os.path.join(config.WORKSPACE_ROOT, "design"))

    # (1) stale：先动设计目标一个字节
    with open(design, "a", encoding="utf-8", newline="") as f:
        f.write("\n")
    stale_sha = _sha_file(design)
    stem = os.path.splitext(os.path.basename(REVC))[0]
    res = copper_loop.adopt(rd, design)
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert res["persisted"] is False
    assert res["revision_status"] == "accepted"
    assert any("adopt_stale_design_board" in r for r in res["reasons"])
    assert _sha_file(design) == stale_sha            # 目标未被写
    assert not os.path.isfile(os.path.join(design_dir,
                                           "%s_pre-adopt-rev-1.kicad_pcb"
                                           % stem))
    on_disk = json.load(open(os.path.join(rd, "revision-record.json"),
                             encoding="utf-8"))
    assert on_disk["status"] == "accepted" and on_disk["adopted"] is False

    # (2) 复原设计目标 → adopt 通过
    shutil.copyfile(REVC, design)
    res = copper_loop.adopt(rd, design)
    assert res["status"] == copper_loop.STATUS_ACCEPTED
    assert res["adopted"] is True
    ar = json.load(open(os.path.join(rd, "adopt-record.json"),
                        encoding="utf-8"))
    staging_sha = on_disk["patch"]["staging_sha256"]
    assert ar["design_board_sha256_pre"] == _sha_file(REVC)
    assert ar["design_board_sha256_post"] == staging_sha
    assert ar["backup_basename"] == "%s_pre-adopt-rev-1.kicad_pcb" % stem
    assert ar["source"] == on_disk["patch"]["staging"] and \
        ar["source_kind"] == "staging"
    assert ar["design_board_written"] is True
    assert ar["live_board_touched"] is False and ar["transaction_untouched"] is True
    assert ar["identity_degradation"] is None
    assert _sha_file(design) == staging_sha          # 设计侧写成 staging 内容
    backup = os.path.join(design_dir, ar["backup_basename"])
    assert os.path.isfile(backup) and _sha_file(backup) == _sha_file(REVC)
    assert ar["backup_sha256"] == _sha_file(REVC)
    # 设计侧写入不混进 staging 事务
    txn = json.load(open(os.path.join(rd, "revision-record.json"),
                         encoding="utf-8"))["transaction"]
    assert txn["live_board_touched"] is False

    # (3) adopt 已发生 ⇒ 再 adopt（设计侧已变）/ rollback 都被拒且不改轮次
    before = _sha_file(os.path.join(rd, "revision-record.json"))
    again = copper_loop.adopt(rd, design)
    assert again["status"] == copper_loop.STATUS_BLOCKED
    assert again["persisted"] is False
    assert any("adopt_stale_design_board" in r for r in again["reasons"])
    rb = copper_loop.rollback_revision(rd)
    assert rb["status"] == copper_loop.STATUS_BLOCKED
    assert rb["persisted"] is False
    assert any("rollback_after_adopt_not_supported" in r for r in rb["reasons"])
    assert _sha_file(os.path.join(rd, "revision-record.json")) == before


def test_adopt_refused_when_not_accepted(revc_e2e):
    """判据 d 前置：awaiting_drc 轮次不得 adopt（拒绝不改轮次状态）。"""
    rd = revc_e2e["rev_dir"]
    res = copper_loop.adopt(rd, REVC)
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert res["persisted"] is False
    assert any("adopt_requires_accepted_revision" in r for r in res["reasons"])
    assert json.load(open(os.path.join(rd, "revision-record.json"),
                          encoding="utf-8"))["status"] == "awaiting_drc"


def test_cli_adopt_requires_explicit_design_board(revc_accepted, capsys):
    """CLI 安全取舍：`copper adopt` 缺 --design-board ⇒ failed(1)，绝不猜目标。"""
    rd = revc_accepted["rev_dir"]
    before = _sha_file(os.path.join(rd, "revision-record.json"))
    rc = cli.main(["copper", "adopt", "--revision-dir", rd])
    out = capsys.readouterr().out
    assert rc == config.EXIT_FAILED
    assert '"status": "failed"' in out and "--design-board" in out
    # 轮次未被触碰（与是否已 adopt 无关）
    assert _sha_file(os.path.join(rd, "revision-record.json")) == before
    assert json.load(open(os.path.join(rd, "revision-record.json"),
                          encoding="utf-8"))["status"] == "accepted"


# ------------------------------------------------------- 4) 追加式 rev-N

def test_append_only_revisions_and_duplicate_fail_closed(revc_e2e, modify_op):
    """判据 e：同 base 连两轮 ⇒ rev-1/rev-2 并存且 rev-1 字节未变；
    不完整既有轮次 / 目标目录已存在 ⇒ fail-closed（绝不静默覆盖）。"""
    out_dir = revc_e2e["out_dir"]
    label_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "e2e")
    before = _tree(os.path.join(label_dir, "rev-1"))
    assert sorted(os.listdir(label_dir)) == ["rev-1"]
    rec2 = copper_loop.mirror_revision(REVC, out_dir, base_label="e2e")
    assert rec2["rev"] == 2 and rec2["status"] == copper_loop.STATUS_MIRROR_ONLY
    assert sorted(os.listdir(label_dir)) == ["rev-1", "rev-2"]
    assert _tree(os.path.join(label_dir, "rev-1")) == before, "rev-1 被覆写"

    # 不完整既有轮次（无 revision-record.json）⇒ fail-closed，且不写该目录
    os.makedirs(os.path.join(label_dir, "rev-4"))
    res = copper_loop.mirror_revision(REVC, out_dir, base_label="e2e")
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert res["persisted"] is False
    assert any("incomplete_existing_revision" in r for r in res["reasons"])
    assert os.listdir(os.path.join(label_dir, "rev-4")) == []
    assert _tree(os.path.join(label_dir, "rev-1")) == before
    shutil.rmtree(os.path.join(label_dir, "rev-4"))

    # 目标目录已被占（并发/重复调同一 N）⇒ FileExistsError 分支 fail-closed
    orig = copper_loop._next_rev
    copper_loop._next_rev = lambda _d: (1, None)      # 模拟并发抢跑
    try:
        res = copper_loop.mirror_revision(REVC, out_dir, base_label="e2e")
    finally:
        copper_loop._next_rev = orig
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert any("revision_dir_exists" in r for r in res["reasons"])
    assert _tree(os.path.join(label_dir, "rev-1")) == before
    assert rec2["rev"] == 2


def test_revision_missing_base_and_bad_args(revc_e2e):
    """失败关闭：基准板不存在 ⇒ blocked（不抛）；out_dir 非法 ⇒ 参数错误。"""
    res = copper_loop.mirror_revision(os.path.join(_scratch("nope"), "x.kicad_pcb"),
                                      _scratch("nope-out"))
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert any("base_board_missing" in r for r in res["reasons"])
    with pytest.raises(copper_loop.CopperLoopError):
        copper_loop.mirror_revision("", _scratch("nope-out"))
    with pytest.raises(copper_loop.CopperLoopError):
        copper_loop.revision(REVC, {"ops": []}, "")


# ------------------------------------------------------------- 5) KiCad5

@pytest.mark.skipif(not K5_BOARDS, reason="pcbench-r1 语料不在位")
def test_kicad5_degraded_mirror_ok_patch_refused_via_cli(capsys):
    """判据 g：KiCad5（geometric_fallback）镜像可用（copper_only_degraded），
    patch 以 edit_unsupported_identity_basis 拒绝（blocked，轮次仍 mirror_only）。"""
    board = K5_BOARDS[0]
    out_dir = _scratch("k5-cli")
    rec = copper_loop.mirror_revision(board, out_dir, base_label="k5")
    assert rec["status"] == copper_loop.STATUS_MIRROR_ONLY, rec["reasons"]
    assert rec["base"]["identity_basis"] == \
        copper_model.IDENTITY_GEOMETRIC_FALLBACK
    assert rec["mirror"]["mode"] == copper_loop.MIRROR_MODE_DEGRADED
    assert rec["mirror"]["degraded"] is True
    assert rec["three_way"]["violations_total"] == 0
    assert rec["mirror"]["counts"]["routes"] == 71
    assert rec["mirror"]["counts"]["pads"] == 0       # 降级：不产焊盘事实
    assert rec["mirror"]["notes"]
    rev_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "k5", "rev-1")
    assert "mirror/adapter-report.json" not in _rel_files(rev_dir)
    # patch 阶段：一律 edit_unsupported_identity_basis（走 CLI，证明可达）
    seg = copper_model.parse_copper_file(board)["segments"][0]
    ps = _write_json(os.path.join(_scratch("k5-cli-in"), "ps.json"),
                     {"ops": [{"op": "modify", "kind": "segment",
                               "key": seg["key"],
                               "expect": {k: seg[k] for k in
                                          ("net", "layer", "width", "start",
                                           "end")},
                               "new": {"width": 0.4}}]})
    rc = cli.main(["copper", "patch", "--revision-dir", rev_dir,
                   "--patch-set", ps])
    out = capsys.readouterr().out
    assert rc == config.EXIT_BLOCKED
    assert copper_loop.REASON_EDIT_UNSUPPORTED_IDENTITY in out
    on_disk = json.load(open(os.path.join(rev_dir, "revision-record.json"),
                             encoding="utf-8"))
    assert on_disk["status"] == "mirror_only"         # 拒绝不改轮次状态
    assert not os.path.exists(os.path.join(rev_dir, "patched"))


@pytest.mark.skipif(not K5_BOARDS, reason="pcbench-r1 语料不在位")
def test_kicad5_cli_rollback_stdout_is_record_bytes(capsysbinary):
    """CLI 生成器纪律：记录类子命令 stdout **逐字节等于**轮次记录文件。"""
    board = K5_BOARDS[1] if len(K5_BOARDS) > 1 else K5_BOARDS[0]
    out_dir = _scratch("k5-cli-bytes")
    copper_loop.mirror_revision(board, out_dir, base_label="k5b")
    rev_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "k5b", "rev-1")
    rc = cli.main(["copper", "rollback", "--revision-dir", rev_dir])
    out = capsysbinary.readouterr().out
    assert rc == config.EXIT_OK
    raw = open(os.path.join(rev_dir, "revision-record.json"), "rb").read()
    assert out == raw
    assert json.loads(out.decode("utf-8"))["status"] == "rolled_back"


# ------------------------------------------------------------ CLI（verify）

def test_cli_verify_clean_exit0_and_violations_exit2(revc_e2e, revc_rejected,
                                                    capsys):
    """CLI verify 实测：干净板 exit 0；被改动板 exit 2（第三条腿真的在核）。"""
    rd = revc_e2e["rev_dir"]
    manifest = os.path.join(rd, "mirror", "route-manifest.json")
    svg = os.path.join(rd, "mirror", "board.svg")
    clean_board = os.path.join(rd, "base", os.path.basename(REVC))
    rc = cli.main(["copper", "verify", "--manifest", manifest, "--svg", svg,
                   "--board", clean_board])
    out = json.loads(capsys.readouterr().out)
    assert rc == config.EXIT_OK
    assert out["verdict"] == "clean" and out["violations_total"] == 0
    assert out["board_binding_violations"] == []
    assert out["snapshot_rebuilt"] is True
    # M1 刷新：paired_segments=dbfea089 夹具板实测 2372（仅钉板）
    assert out["board_binding_counts"]["paired_segments"] == 2372
    # 把板换成被改过线宽的 staging（同 base 板的另一个 mirror 的 manifest）⇒
    # 必报违例（fail-closed；证明第三条腿真的在逐对象核，不是走过场）
    rc = cli.main(["copper", "verify", "--manifest", manifest, "--svg", svg,
                   "--board", revc_rejected["staging_copy"]])
    out = json.loads(capsys.readouterr().out)
    assert rc == config.EXIT_BLOCKED
    assert out["verdict"] == "violations"
    assert out["violations_total"] >= 1
    assert any("route_width_mismatch" in v
               for v in out["board_binding_violations"]), out


def test_cli_mirror_and_verify_roundtrip_cheap(revc, capsys):
    """CLI mirror 真实可达：镜像 → verify 两条腿（含 --registry 省略=派生）。"""
    out_dir = _scratch("cli-mirror")
    rc = cli.main(["copper", "mirror", "--base", REVC, "--out", out_dir,
                   "--base-label", "cli"])
    out = json.loads(capsys.readouterr().out)
    assert rc == config.EXIT_OK
    assert out["status"] == "mirror_only"
    assert out["three_way"]["violations_total"] == 0
    # M1 刷新：mirror vias=dbfea089 夹具板实测 358（仅钉板）
    assert out["mirror"]["counts"]["vias"] == 358
    rev_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "cli", "rev-1")
    rc = cli.main(["copper", "verify",
                   "--manifest", os.path.join(rev_dir, "mirror",
                                              "route-manifest.json"),
                   "--svg", os.path.join(rev_dir, "mirror", "board.svg")])
    out = json.loads(capsys.readouterr().out)
    assert rc == config.EXIT_OK and out["verdict"] == "clean"
    assert out["snapshot_rebuilt"] is None            # 未给 --board：不做快照腿


# ------------------------------------- R4③ live 板不变量 + 负对照（W-5）

def test_revc_live_invariants_only():
    """R4③ live 板不变量用例（REPAIR-P1 W-5）：live 板演进不破坏回路摄取合同。

    只断板无关不变量——registry 净表非空、铜箔计数自洽、零不可表示、
    CRLF 纯净；精确计数/字节口径由钉夹具板的 e2e 用例守护；板变更登记
    走 design1_proposal 前缀与 R28 live 登记用例，不由本用例承担。
    """
    text = _read_text(config.REVC_BOARD)
    reg = copper_loop.identity_registry_from_board(config.REVC_BOARD)
    assert len(reg["nets"]) >= 1
    model = copper_model.parse_copper(text)
    assert model["unrepresentable"] == []
    assert len(model["identity_map"]) == sum(model["counts"].values())
    assert text.count("\n") == text.count("\r\n")


def test_negative_control_board_tamper_moves_counts():
    """负对照（R28「不得弱化」硬约束检出证明）：注入一个新 uuid 的 segment
    后回路摄取计数随之 +1（2372→2373）——e2e 精确断言的输入确实跟踪板
    字节，钉板没有把它们变成恒真。"""
    tampered = revc_board_fixture.duplicate_first_segment(
        revc_board_fixture.fixture_board_text())
    model = copper_model.parse_copper(tampered)
    assert model["counts"]["segments"] == 2373
    assert model["unrepresentable"] == []
    assert model["counts"]["segments"] != 2372    # M1 精确值在此板内容下不成立
