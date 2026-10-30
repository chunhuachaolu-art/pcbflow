#!/usr/bin/env python
"""S25：三类设计对象角色声明验证落盘（纠偏词 P2；proposal/非权威）。

职责（s24 装配模式同构；既有产物零覆写零删除；唯一新落盘件=
out/v3-tl5/artifact-roles-validation-r1.json，本包红线声明的唯一例外）：

从盘上实测装配 kicaddemo-complex_hierarchy-complex_hierarchy 一块样本的
三类角色声明（source/analysis/staging，pcbflow/artifact_roles.py 契约），
并跑 validate_executor_consumption 正例（staging+声明能力内=可消费）与
负例（analysis 被拒，错误码 analysis_model_not_executable——即使其
artifact_id 以 .kicad_pcb 结尾、format_id 伪装为 kicad_pcb）各一次，
连同链一致性检查结果落盘为验证记录。

只读输入（磁盘实读 fail-closed，先验 hash 锚不配即中止）：
  out/v3-tl5/dataset-manifest-kicad-demos-r2.json   （S18 r2 manifest）
  out/v3-tl5/k9-route-check-batch-r1/plan.json      （S21 批计划）
  .../boards/<pid>/verify-record.json               （S21 一致性记录）
  .../boards/<pid>/drc-baseline.json                （S21 DRC baseline）
  out/v3-tl5/conversion-log-kicad-demos-r2-<pid>.json（S18 损失记录）
  datasets/kicad-demos-r1/raw/complex_hierarchy/complex_hierarchy.kicad_pcb
  profiles/<pid>/inputs/board.kicad_pcb（S18 规范化分析板）
  .../staging/<pid>/reference.kicad_pcb（S21 staging 隔离拷贝）

事实纠偏（对下发提示词的一处如实修正）：staging/<pid>/reference.kicad_pcb
并非 kicad-cli 保存的产物——S21 refill_mode=not_refilled（未传
--refill-zones/--save-board），该文件=编排侧对 datasets 源板的逐字节
隔离拷贝（byte_identical_to_reference=true，sha256 与源相同），kicad-cli
10.0.5 仅对其执行 DRC 检查（exit 0=DRC JSON 在场可解析=可加载/可检查
证据）。staging 声明的 transform.saved_by 如实写「拷贝+检查」，不冒充
工具保存产物；check_scope=bare_board_default_rules 如实沿用 S8/S21
历史口径（staging 隔离、无项目规则文件），不改历史语义。

机制：canonical JSON；无 wall-clock（S25_DATE=声明常量）；零子进程；
零网络；同参重建逐字节比对（byte-exact 可重跑）；目标件已存在则重建
比对一致后退出不覆写（不一致=fail）。本记录不是门：不进任何 gate
谓词、零门翻转、零资格声明。

用法：python scripts/s25_artifact_roles_validate.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import artifact_roles as ar  # noqa: E402
from pcbflow import hashing  # noqa: E402

S25_DATE = "2026-09-05"  # 人工会话声明日期（非 wall-clock）
MODULE_NAME = "scripts.s25_artifact_roles_validate"
RECORD_ID = "artifact-roles-validation-r1"
OUT_REL = "out/v3-tl5/artifact-roles-validation-r1.json"

PROFILE_ID = "kicaddemo-complex_hierarchy-complex_hierarchy"
BOARD_ID = "complex_hierarchy/complex_hierarchy"

REL_R2 = "out/v3-tl5/dataset-manifest-kicad-demos-r2.json"
REL_PLAN = "out/v3-tl5/k9-route-check-batch-r1/plan.json"
REL_VERIFY = (f"out/v3-tl5/k9-route-check-batch-r1/boards/{PROFILE_ID}/"
              f"verify-record.json")
REL_BASELINE = (f"out/v3-tl5/k9-route-check-batch-r1/boards/{PROFILE_ID}/"
                f"drc-baseline.json")
REL_LOG = (f"out/v3-tl5/conversion-log-kicad-demos-r2-{PROFILE_ID}.json")
REL_SOURCE = "datasets/kicad-demos-r1/raw/complex_hierarchy/complex_hierarchy.kicad_pcb"
REL_NORM = f"profiles/{PROFILE_ID}/inputs/board.kicad_pcb"
REL_STAGING = (f"out/v3-tl5/k9-route-check-batch-r1/staging/{PROFILE_ID}/"
               f"reference.kicad_pcb")

# 输入先验锚（P2 开工时盘上实测入账；不配即中止——防篡改/防覆写）
FROZEN_SHA256 = {
    REL_R2: "2af5fdca111221a06ceebc40223bcaa0d61f8bc7e568b012db041ef2ed75d310",
    REL_PLAN: "2c8aca6a27d7309e36de4354f41b7b2942a9dfed8014d69290b38b73bb84e17e",
    REL_VERIFY: "9cf51829d0b40a290863cca1e6b48ab605f705274612a0f4e03b3ac23adbf573",
    REL_BASELINE: "49e4480c179967015f7eec965e0b9697897fb64e1735429a8b28a51aaa12bf47",
    REL_LOG: "1becaddb20f096f0657df6eaef903b635333a1224a96779bdfd6a69130948448",
    REL_SOURCE: "d5f4162d4c766448832723d139f9e0fcb88a17c82340f10f6f6dc6c2042f0d69",
    REL_NORM: "6b6986c46adb48415c2518728f1d25326ab161563ffc35a53c185ae47bb1d70b",
    REL_STAGING: "d5f4162d4c766448832723d139f9e0fcb88a17c82340f10f6f6dc6c2042f0d69",
}

KICAD_CLI_VERSION = "10.0.5"
EXECUTOR = {
    "backend": "kicad-cli",
    "version": KICAD_CLI_VERSION,
    "capabilities": [ar.CAP_TOOL_LOADABLE, ar.CAP_TOOL_CHECKABLE],
    "supported_formats": ["kicad_pcb"],
    "declared_in": "plan.kicad_cli_declared_version / "
                   "drc-baseline.drc_invocation.declared_version",
}


def _fail(msg: str) -> None:
    print(f"[s25-roles] FAIL: {msg}")
    sys.exit(1)


def _rel(rel: str) -> Path:
    if "\\" in rel or rel.startswith("/"):
        _fail(f"非仓库相对 POSIX 路径: {rel}")
    return REPO.joinpath(*rel.split("/"))


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _read_json(rel: str):
    p = _rel(rel)
    if not p.is_file():
        _fail(f"输入缺失（fail-closed）: {rel}")
    return json.loads(p.read_text(encoding="utf-8"))


def _binding(source_sha256: str) -> dict:
    return {"kind": ar.SBK_DATASET_MANIFEST_ENTRY,
            "manifest_ref": REL_R2,
            "entry_key": BOARD_ID,
            "source_sha256": source_sha256}


def build() -> dict:
    """全部产物内存构建（纯函数，可重入；同输入 ⇒ 同字节）。"""
    # ---- 盘上实测 + 先验锚 + 记录间 hash 链对账（fail-closed） ----
    sha = {rel: _sha(rel) for rel in FROZEN_SHA256}
    for rel, want in FROZEN_SHA256.items():
        if sha[rel] != want:
            _fail(f"输入 hash 与先验锚不符: {rel} {sha[rel][:8]}…"
                  f"≠{want[:8]}…")

    plan = _read_json(REL_PLAN)
    board = next((b for b in plan["boards"]
                  if b["profile_id"] == PROFILE_ID), None)
    if board is None:
        _fail(f"plan 中无该板: {PROFILE_ID}")
    if board["source_rel"] != REL_SOURCE or \
            board["source_sha256_before_drc"] != sha[REL_SOURCE]:
        _fail("plan 源绑定与实测不符")
    if board["normalized_rel"] != REL_NORM or \
            board["normalized_sha256"] != sha[REL_NORM]:
        _fail("plan 规范化板绑定与实测不符")
    if board["conversion_log_rel"] != REL_LOG or \
            board["conversion_log_sha256"] != sha[REL_LOG]:
        _fail("plan conversion log 绑定与实测不符")
    if board["staging_rel"] != REL_STAGING:
        _fail("plan staging 路径与声明不符")
    version_token = board["version_token"]
    split_role = board["split_role"]

    manifest = _read_json(REL_R2)
    if BOARD_ID not in manifest["board_ids"]:
        _fail(f"r2 manifest board_ids 无该板: {BOARD_ID}")
    norm_entries = [e for e in manifest["normalized_hash"]
                    if e["board_id"] == BOARD_ID]
    if not norm_entries or norm_entries[0]["path"] != REL_NORM or \
            norm_entries[0]["sha256"] != sha[REL_NORM]:
        _fail("r2 manifest normalized_hash 绑定与实测不符")
    log_entries = [e for e in manifest["conversion_log"]
                   if e["board_id"] == BOARD_ID]
    if not log_entries or log_entries[0]["path"] != REL_LOG or \
            log_entries[0]["sha256"] != sha[REL_LOG]:
        _fail("r2 manifest conversion_log 绑定与实测不符")

    log = _read_json(REL_LOG)
    if log["inputs"][0]["path"] != REL_SOURCE or \
            log["inputs"][0]["sha256"] != sha[REL_SOURCE]:
        _fail("conversion log 源绑定与实测不符")
    if log["version_gate"]["board_version"] != version_token:
        _fail("conversion log 版本 token 与 plan 不符")
    dropped = log.get("dropped")
    if not isinstance(dropped, dict) or not dropped:
        _fail("conversion log dropped（损失 field-level 记录）缺失")

    verify = _read_json(REL_VERIFY)
    if verify["result"] != "pass" or verify["fail_classes"]:
        _fail("S21 verify-record 非 pass")
    if not all(c["pass"] for c in verify["checks"]):
        _fail("S21 verify-record 存在未过检查")
    if verify["reference_state"]["sha256"] != sha[REL_SOURCE]:
        _fail("verify-record 参考态 hash 与实测不符")

    baseline = _read_json(REL_BASELINE)
    if baseline["integrity_result"] != "pass":
        _fail("S21 drc-baseline 非 pass")
    if baseline["staging"]["sha256"] != sha[REL_STAGING] or \
            baseline["staging"]["byte_identical_to_reference"] is not True:
        _fail("staging 拷贝绑定/逐字节断言与实测不符")
    if sha[REL_STAGING] != sha[REL_SOURCE]:
        _fail("staging 与 datasets 源非逐字节一致（违背 S21 事实）")
    if plan["kicad_cli_declared_version"] != KICAD_CLI_VERSION or \
            baseline["drc_invocation"]["declared_version"] != \
            KICAD_CLI_VERSION:
        _fail("kicad-cli 声明版本对账不符")

    # ---- 三类角色声明装配（全部字段来自盘上实测/既有记录） ----
    src_decl = ar.build_artifact_role_declaration(
        role=ar.ROLE_SOURCE,
        artifact_id=PROFILE_ID,
        format_id="kicad_pcb",
        format_version=version_token,
        capabilities=[ar.CAP_ANALYSIS_STATS, ar.CAP_ANALYSIS_TOPOLOGY,
                      ar.CAP_ANALYSIS_FEATURES,
                      ar.CAP_TOOL_LOADABLE, ar.CAP_TOOL_CHECKABLE],
        source_binding=_binding(sha[REL_SOURCE]),
        transform=None,
        output_sha256=sha[REL_SOURCE],
        rule_dependencies=[],
        check_scope=None,
        loss_notes=None)

    ana_decl = ar.build_artifact_role_declaration(
        role=ar.ROLE_ANALYSIS,
        artifact_id=PROFILE_ID,
        format_id="kicad_normalized_analysis_dialect",
        format_version=log["converter_version"],
        capabilities=[ar.CAP_ANALYSIS_STATS, ar.CAP_ANALYSIS_TOPOLOGY,
                      ar.CAP_ANALYSIS_FEATURES],
        source_binding=_binding(sha[REL_SOURCE]),
        transform={
            "description": ("S18 k9 文本级规范化→结构统计/拓扑/特征分析"
                            "方言（非完整可加载执行板）"),
            "tool": "pcbflow.corpus_convert",
            "tool_version": log["converter_version"],
            "saved_by": "scripts/s18_demo_convert.py（r2 版本化 manifest 链）"},
        output_sha256=sha[REL_NORM],
        rule_dependencies=[],
        check_scope=None,
        loss_notes=dropped)

    stg_decl = ar.build_artifact_role_declaration(
        role=ar.ROLE_STAGING,
        artifact_id=PROFILE_ID,
        format_id="kicad_pcb",
        format_version=version_token,
        capabilities=[ar.CAP_TOOL_LOADABLE, ar.CAP_TOOL_CHECKABLE],
        source_binding=_binding(sha[REL_SOURCE]),
        transform={
            "description": ("S21 staging 隔离逐字节拷贝"
                            "（byte_identical_to_reference=true）；kicad-cli"
                            " pcb drc 对其检查（refill_mode=not_refilled，"
                            "无 --save-board），未发生工具再保存"),
            "tool": "kicad-cli",
            "tool_version": KICAD_CLI_VERSION,
            "saved_by": ("scripts/s21_route_check.py 编排侧拷贝；kicad-cli "
                         "10.0.5 仅检查未保存（exit 0+DRC JSON 可解析="
                         "可加载/可检查证据）")},
        output_sha256=sha[REL_STAGING],
        rule_dependencies=[
            "kicad-cli-10.0.5 pcb drc 默认设计规则（裸板口径，无项目"
            "规则文件）",
            "staging/reference.kicad_prl（kicad-cli 在 staging 目录生成/"
            "更新）"],
        check_scope=ar.CHECK_SCOPE_BARE,
        loss_notes=None)

    # ---- 正例：staging 在执行器声明能力内=可消费（空列表） ----
    pos = ar.validate_executor_consumption(
        stg_decl,
        executor_backend=EXECUTOR["backend"],
        executor_version=EXECUTOR["version"],
        supported_formats=EXECUTOR["supported_formats"],
        capabilities=EXECUTOR["capabilities"])
    if pos:
        _fail(f"正例失败：staging 应可消费，错误={pos}")

    # ---- 负例：analysis 伪装（.kicad_pcb 后缀+kicad_pcb format）仍必拒 ----
    ana_mimic = ar.build_artifact_role_declaration(
        role=ar.ROLE_ANALYSIS,
        artifact_id=f"{PROFILE_ID}/board.kicad_pcb",
        format_id="kicad_pcb",
        format_version=version_token,
        capabilities=[ar.CAP_ANALYSIS_STATS, ar.CAP_ANALYSIS_TOPOLOGY,
                      ar.CAP_ANALYSIS_FEATURES],
        source_binding=_binding(sha[REL_SOURCE]),
        transform=ana_decl["transform"],
        output_sha256=sha[REL_NORM],
        rule_dependencies=[],
        check_scope=None,
        loss_notes=dropped)
    neg = ar.validate_executor_consumption(
        ana_mimic,
        executor_backend=EXECUTOR["backend"],
        executor_version=EXECUTOR["version"],
        supported_formats=EXECUTOR["supported_formats"],
        capabilities=EXECUTOR["capabilities"])
    neg_codes = [e["code"] for e in neg]
    if "analysis_model_not_executable" not in neg_codes:
        _fail(f"负例失败：analysis 应被拒，错误={neg}")

    # ---- 链一致性：三声明同链可追溯 → 空错误 ----
    cons = ar.validate_role_consistency([src_decl, ana_decl, stg_decl])
    if cons:
        _fail(f"链一致性失败：{cons}")

    chain_bindings = [
        {"id": "frozen_input_anchor_match", "pass": True,
         "detail": "8 输入盘上实测 sha256 与先验锚逐一相等"},
        {"id": "plan_binds_source_normalized_log_staging", "pass": True,
         "detail": f"plan 路径+hash 与实测逐一相符（version_token="
                   f"{version_token}，split_role={split_role}）"},
        {"id": "r2_manifest_binds_board_normalized_log", "pass": True,
         "detail": "board_ids/normalized_hash/conversion_log 三处绑定与"
                   "实测相符"},
        {"id": "log_input_binds_dataset_source", "pass": True,
         "detail": f"conversion log inputs[0]={REL_SOURCE}（"
                   f"{sha[REL_SOURCE][:8]}…）"},
        {"id": "verify_record_reference_state_matches_disk", "pass": True,
         "detail": f"verify-record result=pass（10/10 checks）；"
                   f"reference_state={sha[REL_SOURCE][:8]}…"},
        {"id": "staging_byte_identical_to_source", "pass": True,
         "detail": f"staging={sha[REL_STAGING][:8]}… == 源 "
                   f"{sha[REL_SOURCE][:8]}…（byte_identical_to_reference"
                   f"=true，kicad-cli 仅检查未保存）"},
    ]

    return {
        "schema_version": "3.0",
        "artifact_kind": "p2_artifact_roles_validation",
        "record_id": RECORD_ID,
        "declared_date": S25_DATE,
        "producer": MODULE_NAME,
        "contract": ar.CONTRACT_ID,
        "proposal_status": ar.PROPOSAL_STATUS,
        "proposal_note": (
            "纠偏词 P2 提案验证记录（非权威）：三类角色声明=接口设计与"
            "提案，不注册 schema registry；正式采纳（含 schema 注册演进"
            "与能力枚举定稿）须人工批准。本记录不是门：不进任何 gate 谓"
            "词、零门翻转、零资格声明。"),
        "sample": {
            "profile_id": PROFILE_ID,
            "board_id": BOARD_ID,
            "split_role": split_role,
            "version_token": version_token,
            "selection_rationale": (
                "r2 manifest 条目+S21 verify-record+S21 staging 齐全的"
                "既有样本（train 板，top_level net 声明）"),
        },
        "inputs": {rel: {"sha256": h, "sha256_8": h[:8]}
                   for rel, h in sha.items()},
        "chain_bindings": chain_bindings,
        "declarations": {"source": src_decl,
                         "analysis": ana_decl,
                         "staging": stg_decl},
        "role_consistency": {
            "artifact_ids": [PROFILE_ID],
            "errors": cons,
            "result": "pass",
            "semantics": "staging/analysis 的 source_binding 与 source "
                         "声明的 output_sha256 同链可追溯",
        },
        "executor_consumption": {
            "executor": EXECUTOR,
            "positive_staging": {
                "declaration_role": ar.ROLE_STAGING,
                "errors": pos,
                "result": "consumable",
            },
            "negative_analysis_mimicry": {
                "declaration_role": ar.ROLE_ANALYSIS,
                "artifact_id": ana_mimic["artifact_id"],
                "format_id": ana_mimic["format_id"],
                "errors": neg,
                "rejected_codes": neg_codes,
                "result": "rejected",
                "note": ("path/后缀与 format 伪装不参与判定：analysis 角"
                         "色即使 artifact_id 以 .kicad_pcb 结尾、format_id"
                         "=kicad_pcb 仍被拒（analysis_model_not_executable）"),
            },
        },
        "staging_fact_note": (
            "staging/<pid>/reference.kicad_pcb=S21 编排侧对 datasets 源板"
            "的逐字节隔离拷贝（byte_identical_to_reference=true）；"
            "kicad-cli 10.0.5 仅对其进行 DRC 检查（refill_mode="
            "not_refilled、无 --save-board），未发生工具再保存——"
            "transform.saved_by 如实声明，不冒充 kicad-cli 保存产物"),
        "check_scope_note": (
            "S8/S21 历史 staging=裸板默认规则口径（staging 隔离、无项目"
            "规则文件）→ 如实 CHECK_SCOPE_BARE，历史语义不变；新链项目"
            "规则必须显式 CHECK_SCOPE_PROJECT，禁混称"),
        "conclusions": {
            "roles_machine_distinguishable": True,
            "analysis_rejected_as_executable": True,
            "staging_consumable_within_declared_capabilities": True,
            "chain_consistent": True,
            "is_gate": False,
            "gate_state_change": "none（提案与验证，零门翻转）",
        },
    }


def main() -> None:
    for rel in FROZEN_SHA256:
        if not _rel(rel).is_file():
            _fail(f"输入缺失（fail-closed）: {rel}")

    out_path = _rel(OUT_REL)
    docs1 = build()
    docs2 = build()
    data = hashing.canonical_json_bytes(docs1)
    if hashing.canonical_json_bytes(docs2) != data:
        _fail("同参重建不一致（byte-exact 破坏）")

    if out_path.exists():
        if out_path.read_bytes() == data:
            print(f"[s25-roles] {OUT_REL} 已存在且与重建逐字节一致——"
                  f"不覆写，退出")
            print(f"[s25-roles] sha256[:8] artifact-roles-validation-r1"
                  f".json = {_sha(OUT_REL)[:8]}")
            return
        _fail("目标件已存在且与重建不一致（防覆写红线；人工核查）")

    out_path.write_bytes(data)
    if out_path.read_bytes() != data:
        _fail("回读不一致")

    print(f"[s25-roles] 三类角色声明装配完成（source/analysis/staging，"
          f"样本={PROFILE_ID}）；链一致性 pass（空错误）")
    print(f"[s25-roles] 正例：staging 消费=可消费（空错误）；负例："
          f"analysis 伪装 .kicad_pcb 后缀+kicad_pcb format 仍被拒"
          f"（analysis_model_not_executable）")
    print(f"[s25-roles] sha256[:8] artifact-roles-validation-r1.json = "
          f"{_sha(OUT_REL)[:8]}")
    print("[s25-roles] P2 提案验证落盘完成（proposal/非权威；不是门，"
          "零门翻转；既有 out/ 产物零覆写）")


if __name__ == "__main__":
    main()
