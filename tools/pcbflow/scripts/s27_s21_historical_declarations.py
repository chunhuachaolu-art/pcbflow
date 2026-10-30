#!/usr/bin/env python
"""S27-R1：S21 历史 staging 追溯补声明（17 板；APR-0014 批准的补声明层）。

用户 2026-09-06 批准（APR-0014，「强制+S21补声明」）：未来 staging 产物
强制携带声明+通过 consumption 合同才可进 executor；S21 历史 staging 按
盘上实测 hash+DRC 证据追溯补构造声明（用户明确选择补声明，而非只读
历史登记），并重跑一致性验证。**历史边界：原 S21 批次文件
（out/v3-tl5/k9-route-check-batch-r1/ 下全部）零改动——本脚本产出的
声明是引用只读历史件的新增只读层**（plan/verify-record/drc-baseline/
batch-summary/staging reference 全部按盘上实测 hash 对账，不回写）。

逐板（17 pid，plan.json 为准）：实测 staging reference.kicad_pcb 与
datasets 源板 sha256，逐板验证逐字节一致性（S25 样本先验=逐字节拷贝；
实测不符即 fail-closed 中止——声明不得照抄模板断言）；交叉核对
plan 源绑定 / verify-record（result=pass、reference_state）/ drc-baseline
（integrity=pass、staging 绑定+byte_identical、declared_version=10.0.5、
DRC JSON 工件在场）/ r2 manifest（board_ids+conversion_log 绑定）；
构造每板 source+staging 两声明（pcbflow/artifact_roles.py 契约，与 S25
同款字段口径）；逐链跑 validate_role_consistency +
validate_executor_consumption（executor=kicad-cli/10.0.5/
["kicad_pcb"]/["tool_loadable","tool_checkable"]）+ 注册表 schema 校验
（artifact-role-declaration-v1，APR-0012），预期全部零错误，结果逐板
入工件；对 S25 样本板（complex_hierarchy）额外断言新声明与 S25 落盘
声明逐字段相等（跨记录一致性，fail-closed）。

落盘（byte-exact 可重跑；已存在则重建比对一致后退出不覆写，不一致=
fail；两件均为 out/ 只读红线的本包声明例外）：
- out/v3-tl5/s21-historical-staging-declarations-r1.json（17 套声明+
  逐链验证结果+S25 样本/源 sha 交叉引用）
- out/v3-tl5/s21-historical-declarations-validation-r1.json（运行摘要；
  绑定上一件的 canonical sha256）

机制：canonical JSON；无 wall-clock（S27_DATE=声明常量 2026-09-06）；
零子进程；零网络；同参重建逐字节比对（byte-exact 可重跑）。本记录
不是门：不进任何 gate 谓词、零门翻转、零资格声明；datasets/ 只读。

用法：python scripts/s27_s21_historical_declarations.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import artifact_roles as ar  # noqa: E402
from pcbflow import hashing, schemas  # noqa: E402

S27_DATE = "2026-09-06"  # 人工会话声明日期（非 wall-clock；=APR-0014 决定日）
MODULE_NAME = "scripts.s27_s21_historical_declarations"

REL_PLAN = "out/v3-tl5/k9-route-check-batch-r1/plan.json"
REL_SUMMARY = "out/v3-tl5/k9-route-check-batch-r1/batch-summary.json"
REL_R2 = "out/v3-tl5/dataset-manifest-kicad-demos-r2.json"
REL_S25 = "out/v3-tl5/artifact-roles-validation-r1.json"

# 输入先验锚（盘上实测入账；不配即中止——防篡改/防覆写，fail-closed）
FROZEN_SHA256 = {
    REL_PLAN: "2c8aca6a27d7309e36de4354f41b7b2942a9dfed8014d69290b38b73bb84e17e",
    REL_SUMMARY: "a683137eb279292e5e1265618993f279e4e5648715f1757f4e551f2c770a1202",
    REL_R2: "2af5fdca111221a06ceebc40223bcaa0d61f8bc7e568b012db041ef2ed75d310",
    REL_S25: "d88945d2957870fc93f27fa2efdd953fdaa6be31c93ef8ffb92f6ca4b4745ede",
}

REL_DECL = "out/v3-tl5/s21-historical-staging-declarations-r1.json"
REL_VALID = "out/v3-tl5/s21-historical-declarations-validation-r1.json"

S25_SAMPLE_PID = "kicaddemo-complex_hierarchy-complex_hierarchy"

KICAD_CLI_VERSION = "10.0.5"
EXECUTOR = {
    "backend": "kicad-cli",
    "version": KICAD_CLI_VERSION,
    "capabilities": [ar.CAP_TOOL_LOADABLE, ar.CAP_TOOL_CHECKABLE],
    "supported_formats": ["kicad_pcb"],
    "declared_in": ("plan.kicad_cli_declared_version / drc-baseline."
                    "drc_invocation.declared_version / APR-0014 消费合同"),
}

# staging transform 如实口径（与 S25 落盘声明逐字同串：S21 编排侧逐字节
# 拷贝+kicad-cli 10.0.5 DRC 检查未保存；不冒充工具保存产物）。适用=
# DRC 已执行且 JSON 在场的板（实测 16/17）。
STAGING_TRANSFORM = {
    "description": ("S21 staging 隔离逐字节拷贝"
                    "（byte_identical_to_reference=true）；kicad-cli"
                    " pcb drc 对其检查（refill_mode=not_refilled，"
                    "无 --save-board），未发生工具再保存"),
    "tool": "kicad-cli",
    "tool_version": KICAD_CLI_VERSION,
    "saved_by": ("scripts/s21_route_check.py 编排侧拷贝；kicad-cli "
                 "10.0.5 仅检查未保存（exit 0+DRC JSON 可解析="
                 "可加载/可检查证据）"),
}
# constraints 板（版本 token 20260624）如实变体：kicad-cli 10.0.5 拒绝
# 加载（文件格式高于执行器支持，工具自述需 ≥10.99），DRC JSON 未产出
# （S21 drc-baseline integrity=fail，fail_classes=[drc_json_wellformed]，
# exit 3）——transform 必须反映实际，不得照抄「可加载/可检查证据」模板。
STAGING_TRANSFORM_LOAD_REFUSED = {
    "description": ("S21 staging 隔离逐字节拷贝"
                    "（byte_identical_to_reference=true）；kicad-cli"
                    " pcb drc 检查未产出可解析 JSON（refill_mode="
                    "not_refilled，无 --save-board；kicad-cli 10.0.5 "
                    "拒绝加载：文件格式 20260624 高于执行器支持，工具"
                    "自述需 ≥10.99）"),
    "tool": "kicad-cli",
    "tool_version": KICAD_CLI_VERSION,
    "saved_by": ("scripts/s21_route_check.py 编排侧拷贝；kicad-cli "
                 "10.0.5 加载被拒（exit 3；S21 drc-baseline integrity="
                 "fail，fail_classes=[drc_json_wellformed]）——可加载/"
                 "可检查证据对该执行器版本不成立，须由更高版本真实工具"
                 "承载；逐字节拷贝事实不变（byte_identical_to_reference"
                 "=true，参考态 pre/post hash 分记一致）"),
}
# staging rule_dependencies（按 batch-summary/boards 记录的实际引用：
# kicad-cli 默认设计规则+staging 目录内 .prl，与 S25 同款两条）
STAGING_RULE_DEPENDENCIES = [
    "kicad-cli-10.0.5 pcb drc 默认设计规则（裸板口径，无项目规则文件）",
    "staging/reference.kicad_prl（kicad-cli 在 staging 目录生成/更新）",
]

HISTORICAL_BOUNDARY_NOTE = (
    "追溯补声明经用户 2026-09-06 批准（APR-0014，「强制+S21补声明」）。"
    "原 S21 批次文件（out/v3-tl5/k9-route-check-batch-r1/ 下全部）零改动："
    "plan/verify-record/drc-baseline/batch-summary/staging reference 全部"
    "按盘上实测 sha256 只读对账引用，本声明层不回写、不改名、不删增任何"
    "既有文件；声明是引用只读历史件的新增层。用户明确选择补声明（按盘上"
    "实测 hash+DRC 证据追溯构造），而非只读历史登记。")


def _fail(msg: str) -> None:
    print(f"[s27-s21decl] FAIL: {msg}")
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


def _binding(source_sha256: str, entry_key: str) -> dict:
    return {"kind": ar.SBK_DATASET_MANIFEST_ENTRY,
            "manifest_ref": REL_R2,
            "entry_key": entry_key,
            "source_sha256": source_sha256}


def _build_board(board: dict, s25_decls: dict) -> dict:
    """单板：实测+交叉核对+两声明+逐链校验（纯函数；不符即 _fail）。"""
    pid = board["profile_id"]
    board_id = board["board_id"]
    rel_source = board["source_rel"]
    rel_staging = board["staging_rel"]
    rel_log = board["conversion_log_rel"]

    sha_source = _sha(rel_source)
    sha_staging = _sha(rel_staging)
    sha_log = _sha(rel_log)
    byte_identical = sha_staging == sha_source
    if not byte_identical:
        _fail(f"{pid}: staging 与源实测不一致（staging={sha_staging[:8]}… "
              f"源={sha_source[:8]}…）——声明须如实反映实际 transform，"
              f"禁止照抄模板断言；人工核查后另行处置")

    checks: list = []

    def _chk(cid: str, ok: bool, detail: str) -> None:
        checks.append({"id": cid, "pass": bool(ok), "detail": detail})
        if not ok:
            _fail(f"{pid}: 交叉核对失败 {cid}: {detail}")

    # 1) plan 源/staging/log 绑定与实测相符
    _chk("plan_source_binding",
         board["source_sha256_before_drc"] == sha_source
         and rel_staging.endswith(f"{pid}/reference.kicad_pcb"),
         f"plan source_sha256_before_drc={sha_source[:8]}… 与实测相等；"
         f"staging_rel 指向本板 staging reference")
    _chk("plan_log_binding", board["conversion_log_sha256"] == sha_log,
         f"plan conversion_log_sha256={sha_log[:8]}… 与实测相等")

    # 2) verify-record：result=pass、全检查过、reference_state=实测源
    verify = _read_json(REL_PLAN.replace("plan.json",
                                         f"boards/{pid}/verify-record.json"))
    _chk("verify_record_pass",
         verify["result"] == "pass" and not verify["fail_classes"]
         and all(c["pass"] for c in verify["checks"])
         and verify["reference_state"]["sha256"] == sha_source,
         f"verify-record result=pass（{len(verify['checks'])}/"
         f"{len(verify['checks'])} checks）；reference_state="
         f"{sha_source[:8]}… 与实测源相等")

    # 3) drc-baseline：integrity 分态（pass / dual-run 不稳定 / 拒绝加载）
    #    如实分层；staging 绑定+逐字节断言对全部 17 板一律强制
    baseline = _read_json(REL_PLAN.replace(
        "plan.json", f"boards/{pid}/drc-baseline.json"))
    stg_dir = _rel(rel_staging).parent
    json_present = ((stg_dir / "drc-error.json").is_file()
                    and (stg_dir / "drc-all.json").is_file())
    _chk("drc_baseline_staging_binding",
         baseline["integrity_result"] in ("pass", "fail")
         and baseline["staging"]["path"] == rel_staging
         and baseline["staging"]["sha256"] == sha_staging
         and baseline["staging"]["byte_identical_to_reference"] is True,
         f"drc-baseline staging 绑定={sha_staging[:8]}… 与实测相等；"
         f"byte_identical_to_reference=true（integrity="
         f"{baseline['integrity_result']}，S21 既有分态如实引用）")
    _chk("drc_invocation_version",
         baseline["drc_invocation"]["declared_version"] == KICAD_CLI_VERSION
         and baseline["drc_invocation"]["refill_mode"].startswith(
             "not_refilled")
         and (baseline["drc_invocation"]["observed_version"] ==
              KICAD_CLI_VERSION
              or (baseline["drc_invocation"]["observed_version"] is None
                  and not json_present)),
         f"kicad-cli 声明版本={KICAD_CLI_VERSION}；refill_mode="
         f"not_refilled（无 --save-board，未发生工具再保存）；观测版本="
         f"{baseline['drc_invocation']['observed_version']!r}"
         f"（DRC JSON 在场时=10.0.5；constraints 板加载被拒无 JSON → "
         f"如实 null）")
    _chk("drc_evidence_files_match_integrity",
         (stg_dir / "reference.kicad_prl").is_file()
         and json_present == (baseline["integrity_result"] == "pass"
                              or baseline["fail_classes"] ==
                              ["dual_run_error_count_stable"]),
         f"staging/reference.kicad_prl 在场（规则依赖文件）；DRC JSON 在场="
         f"{json_present} 与 S21 integrity 分态相符")
    if baseline["integrity_result"] == "pass":
        evidence_state = "present"
        evidence_note = ("DRC exit 0+双 severity JSON 可解析且双运行计数"
                         "稳定（integrity=pass）——可加载/可检查证据成立")
    elif baseline["fail_classes"] == ["dual_run_error_count_stable"]:
        evidence_state = "present_dual_run_unstable"
        evidence_note = ("DRC exit 0+双 severity JSON 可解析=可加载/可检查"
                         "证据成立；仅双运行 error 计数不稳（D19(b) 类工具"
                         "实况如实登记，S21 非判罚口径），不影响可加载/"
                         "可检查证据")
    else:
        evidence_state = "absent_executor_refused_load"
        evidence_note = ("kicad-cli 10.0.5 拒绝加载（exit 3；文件格式高于"
                         "执行器支持）——可加载/可检查证据对该执行器版本"
                         "不成立；本声明如实记录该证据缺席，不冒称")
    drc_evidence = {
        "integrity_result": baseline["integrity_result"],
        "fail_classes": baseline["fail_classes"],
        "exit_codes": baseline["exit_codes"],
        "drc_json_present": json_present,
        "evidence_state": evidence_state,
        "note": evidence_note,
    }
    if evidence_state == "absent_executor_refused_load":
        transform = dict(STAGING_TRANSFORM_LOAD_REFUSED)
    else:
        transform = dict(STAGING_TRANSFORM)
    evidence_caveat = (None if evidence_state == "present"
                       else evidence_note)

    # 4) r2 manifest：board_ids 成员+conversion_log 绑定
    manifest = _read_json(REL_R2)
    log_entries = [e for e in manifest["conversion_log"]
                   if e["board_id"] == board_id]
    _chk("r2_manifest_board_and_log",
         board_id in manifest["board_ids"]
         and bool(log_entries)
         and log_entries[0]["path"] == rel_log
         and log_entries[0]["sha256"] == sha_log,
         f"r2 manifest board_ids 含 {board_id}；conversion_log 绑定="
         f"{sha_log[:8]}… 与实测相等")

    # 5) 声明构造（source 可空 check_scope=缺省未声明，APR-0016）
    src_decl = ar.build_artifact_role_declaration(
        role=ar.ROLE_SOURCE,
        artifact_id=pid,
        format_id="kicad_pcb",
        format_version=board["version_token"],
        capabilities=[ar.CAP_ANALYSIS_STATS, ar.CAP_ANALYSIS_TOPOLOGY,
                      ar.CAP_ANALYSIS_FEATURES,
                      ar.CAP_TOOL_LOADABLE, ar.CAP_TOOL_CHECKABLE],
        source_binding=_binding(sha_source, board_id),
        transform=None,
        output_sha256=sha_source,
        rule_dependencies=[],
        check_scope=None,
        loss_notes=None)
    stg_decl = ar.build_artifact_role_declaration(
        role=ar.ROLE_STAGING,
        artifact_id=pid,
        format_id="kicad_pcb",
        format_version=board["version_token"],
        capabilities=[ar.CAP_TOOL_LOADABLE, ar.CAP_TOOL_CHECKABLE],
        source_binding=_binding(sha_source, board_id),
        transform=transform,
        output_sha256=sha_staging,
        rule_dependencies=list(STAGING_RULE_DEPENDENCIES),
        check_scope=ar.CHECK_SCOPE_BARE,
        loss_notes=None)

    # 6) S25 样本板：新声明必须与 S25 落盘声明逐字段相等（跨记录一致）
    s25_equal = None
    if pid == S25_SAMPLE_PID:
        s25_equal = (src_decl == s25_decls["source"]
                     and stg_decl == s25_decls["staging"])
        _chk("s25_sample_declaration_equality", s25_equal,
             f"本板 source/staging 声明与 S25 记录（{REL_S25}）declarations"
             f" 逐字段相等（同源同口径交叉验证）")

    # 7) 逐链校验：一致性+消费合同+注册表 schema（预期全部零错误）
    consistency = ar.validate_role_consistency([src_decl, stg_decl])
    if consistency:
        _fail(f"{pid}: 链一致性失败：{consistency}")
    consumption = ar.validate_executor_consumption(
        stg_decl,
        executor_backend=EXECUTOR["backend"],
        executor_version=EXECUTOR["version"],
        supported_formats=EXECUTOR["supported_formats"],
        capabilities=EXECUTOR["capabilities"])
    if consumption:
        _fail(f"{pid}: staging 消费合同失败：{consumption}")
    schema_src = schemas.validate("artifact-role-declaration-v1", src_decl)
    schema_stg = schemas.validate("artifact-role-declaration-v1", stg_decl)
    if schema_src or schema_stg:
        _fail(f"{pid}: 注册表 schema 校验失败：{schema_src + schema_stg}")

    return {
        "profile_id": pid,
        "board_id": board_id,
        "split_role": board["split_role"],
        "version_token": board["version_token"],
        "source_rel": rel_source,
        "source_sha256": sha_source,
        "staging_rel": rel_staging,
        "staging_sha256": sha_staging,
        "byte_identical_to_source": byte_identical,
        "conversion_log_rel": rel_log,
        "conversion_log_sha256": sha_log,
        "cross_checks": checks,
        "drc_evidence": drc_evidence,
        "declarations": {"source": src_decl, "staging": stg_decl},
        "role_consistency": {
            "chain": [ar.ROLE_SOURCE, ar.ROLE_STAGING],
            "errors": consistency,
            "result": "pass",
            "semantics": ("staging.source_binding.source_sha256 == "
                          "source.output_sha256（同链可追溯）"),
        },
        "executor_consumption": {
            "declaration_role": ar.ROLE_STAGING,
            "errors": consumption,
            "result": "consumable",
            "evidence_caveat": evidence_caveat,
        },
        "schema_validation": {
            "schema_name": "artifact-role-declaration-v1",
            "registry_version": schemas.REGISTRY_VERSION,
            "approval_ref": "APR-0012",
            "source_errors": schema_src,
            "staging_errors": schema_stg,
            "result": "pass",
        },
    }


def build() -> tuple:
    """全部产物内存构建（纯函数；同输入 ⇒ 同字节）。返回 (decl, valid)。"""
    sha = {rel: _sha(rel) for rel in FROZEN_SHA256}
    for rel, want in FROZEN_SHA256.items():
        if sha[rel] != want:
            _fail(f"输入 hash 与先验锚不符: {rel} "
                  f"{sha[rel][:8]}…≠{want[:8]}…")

    plan = _read_json(REL_PLAN)
    if len(plan["boards"]) != 17:
        _fail(f"plan 板数非 17: {len(plan['boards'])}")
    if plan["batch_id"] != "k9-route-check-batch-r1" or \
            plan["kicad_cli_declared_version"] != KICAD_CLI_VERSION:
        _fail("plan batch_id/kicad-cli 版本与声明口径不符")

    s25 = _read_json(REL_S25)
    s25_decls = s25["declarations"]
    if s25["sample"]["profile_id"] != S25_SAMPLE_PID:
        _fail("S25 记录样本板非 complex_hierarchy")

    boards = [_build_board(b, s25_decls) for b in plan["boards"]]

    decl_doc = {
        "schema_version": "3.0",
        "artifact_kind": "s21_historical_staging_declarations",
        "record_id": "s21-historical-staging-declarations-r1",
        "declared_date": S27_DATE,
        "producer": MODULE_NAME,
        "contract": ar.CONTRACT_ID,
        "adoption": {
            "status": "adopted_by_user",
            "approval_ref": "APR-0014",
            "decided_date": S27_DATE,
            "decision_quote": "「强制+S21补声明」",
            "decision_note": ("未来 staging 产物强制携带声明+通过 "
                              "consumption 合同才可进 executor；S21 历史 "
                              "staging 按盘上实测 hash+DRC 证据追溯补构造"
                              "声明（用户明确选择补声明，而非只读历史登"
                              "记），需重跑一致性验证——本件即该重跑结果。"),
            "registry_entry": "artifact-role-declaration-v1（APR-0012）",
            "binding_policy": "pcbflow.artifact_roles.STAGING_BINDING_POLICY",
        },
        "historical_boundary": {
            "original_records_untouched": True,
            "original_batch_dir": "out/v3-tl5/k9-route-check-batch-r1/",
            "layer_kind": "retroactive_declaration_readonly_reference_layer",
            "note": HISTORICAL_BOUNDARY_NOTE,
        },
        "inputs": {rel: {"sha256": h, "sha256_8": h[:8]}
                   for rel, h in sha.items()},
        "executor": EXECUTOR,
        "cross_reference": {
            "s25_record": {
                "path_rel": REL_S25,
                "sha256": sha[REL_S25],
                "sample_profile_id": S25_SAMPLE_PID,
                "sample_source_sha256_8":
                    s25_decls["source"]["output_sha256"][:8],
                "sample_staging_sha256_8":
                    s25_decls["staging"]["output_sha256"][:8],
            },
            "equality_check": (
                f"样本板 {S25_SAMPLE_PID} 的 source/staging 声明与 S25 落盘"
                f"声明逐字段相等（fail-closed 断言，见该板 cross_checks）"),
        },
        "boards": boards,
        "summary": {
            "boards_total": len(boards),
            "byte_identical_to_source": sum(
                1 for b in boards if b["byte_identical_to_source"]),
            "consistency_pass": sum(
                1 for b in boards if b["role_consistency"]["result"] ==
                "pass"),
            "consumption_pass": sum(
                1 for b in boards
                if b["executor_consumption"]["result"] == "consumable"),
            "schema_validation_pass": sum(
                1 for b in boards
                if b["schema_validation"]["result"] == "pass"),
            "drc_evidence_present": sum(
                1 for b in boards
                if b["drc_evidence"]["evidence_state"] == "present"),
            "drc_evidence_present_dual_run_unstable": sum(
                1 for b in boards
                if b["drc_evidence"]["evidence_state"] ==
                "present_dual_run_unstable"),
            "drc_evidence_absent_executor_refused_load": sum(
                1 for b in boards
                if b["drc_evidence"]["evidence_state"] ==
                "absent_executor_refused_load"),
            "executor_load_refused_boards": [
                b["profile_id"] for b in boards
                if b["drc_evidence"]["evidence_state"] ==
                "absent_executor_refused_load"],
        },
        "drc_evidence_note": (
            "S21 drc-baseline integrity 分态如实入声明（batch-summary "
            "baseline_integrity_distribution={fail: 6, pass: 11}）：11 板 "
            "DRC exit 0+JSON 可解析+双运行稳定=可加载/可检查证据成立；"
            "5 板 JSON 在场仅双运行 error 计数不稳（kicad-cli 跨运行不稳"
            "定=D19(b) 类工具实况如实登记，非判罚），证据仍成立；1 板 "
            "（kicaddemo-constraints-constraints，格式 20260624）kicad-cli "
            "10.0.5 拒绝加载（exit 3，无 DRC JSON）——该板声明 transform "
            "如实写明拒绝加载与证据缺席，不冒称可加载/可检查；其能力声明 "
            "为工件类断言（真实工具域板文件，可加载性由 ≥10.99 版本真实"
            "工具承载），消费合同按声明集合机械判定并在 evidence_caveat "
            "中明示证据缺席。S21 一致性验证（verify-record，D17 参考态"
            "口径）17/17 pass 与本分层不冲突：consistency=参考态一致，"
            "integrity=DRC 证据质量。"),
        "check_scope_note": (
            "S8/S21 历史 staging=裸板默认规则口径（staging 隔离、无项目"
            "规则文件）→ 如实 CHECK_SCOPE_BARE，历史语义不变（APR-0016："
            "source 侧 check_scope 可空声明，本批 source 声明缺省=None"
            "=未声明）；新链项目规则必须显式 CHECK_SCOPE_PROJECT，禁混称"),
        "loss_notes_note": (
            "staging 声明 loss_notes=None：staging 与源逐字节一致（17/17"
            " 实测）=零信息损失，如实声明；分析能力未声明，不触发「loss "
            "为空」判据（APR-0013）的反向约束"),
        "conclusions": {
            "retroactive_declarations_consistent": True,
            "staging_consumable_within_declared_capabilities": True,
            "is_gate": False,
            "gate_state_change": "none（追溯补声明层，零门翻转）",
        },
    }

    decl_bytes = hashing.canonical_json_bytes(decl_doc)
    valid_doc = {
        "schema_version": "3.0",
        "artifact_kind": "s21_historical_declarations_validation",
        "record_id": "s21-historical-declarations-validation-r1",
        "declared_date": S27_DATE,
        "producer": MODULE_NAME,
        "subject": {
            "path_rel": REL_DECL,
            "sha256": hashing.sha256_bytes(decl_bytes),
            "boards_total": len(boards),
        },
        "adoption_ref": "APR-0014",
        "historical_boundary_note": HISTORICAL_BOUNDARY_NOTE,
        "executor": EXECUTOR,
        "summary": dict(decl_doc["summary"],
                        mismatches=[b["profile_id"] for b in boards
                                    if not b["byte_identical_to_source"]]),
        "boards_index": [
            {"profile_id": b["profile_id"],
             "board_id": b["board_id"],
             "source_sha256_8": b["source_sha256"][:8],
             "staging_sha256_8": b["staging_sha256"][:8],
             "byte_identical": b["byte_identical_to_source"],
             "drc_evidence_state": b["drc_evidence"]["evidence_state"],
             "role_consistency": b["role_consistency"]["result"],
             "executor_consumption": b["executor_consumption"]["result"],
             "evidence_caveat": b["executor_consumption"]["evidence_caveat"]
             is not None,
             "schema_validation": b["schema_validation"]["result"]}
            for b in boards],
        "cross_check_ids": sorted(
            {c["id"] for b in boards for c in b["cross_checks"]}),
        "s25_cross_reference": decl_doc["cross_reference"]["s25_record"],
        "conclusions": dict(decl_doc["conclusions"]),
    }
    return decl_doc, valid_doc


def _write_if_absent_or_equal(path: Path, expected: bytes) -> str:
    """byte-exact 可重跑：已存在则逐字节校验一致（不一致 fail），否则落盘。

    任何路径都**不覆写**既有字节。返回文件 sha256（十六进制全串）。
    """
    if path.exists():
        actual = path.read_bytes()
        if actual != expected:
            _fail(f"{path.name} 已存在且字节与本次构造不一致"
                  f"（byte-exact 校验失败；不覆写）")
        print(f"[s27-s21decl] 已存在且一致（不覆写）：{path.name}")
    else:
        path.write_bytes(expected)
        print(f"[s27-s21decl] 新增落盘：{path.name}")
    return hashing.sha256_bytes(expected)


def main() -> None:
    for rel in FROZEN_SHA256:
        if not _rel(rel).is_file():
            _fail(f"输入缺失（fail-closed）: {rel}")

    doc1, valid1 = build()
    doc2, valid2 = build()
    decl_bytes = hashing.canonical_json_bytes(doc1)
    valid_bytes = hashing.canonical_json_bytes(valid1)
    if decl_bytes != hashing.canonical_json_bytes(doc2) or \
            valid_bytes != hashing.canonical_json_bytes(valid2):
        _fail("同参重建不一致（byte-exact 破坏）")

    written: dict = {}
    written[_rel(REL_DECL)] = _write_if_absent_or_equal(
        _rel(REL_DECL), decl_bytes)
    written[_rel(REL_VALID)] = _write_if_absent_or_equal(
        _rel(REL_VALID), valid_bytes)

    s = doc1["summary"]
    print(f"[s27-s21decl] 17 板追溯补声明完成：byte_identical="
          f"{s['byte_identical_to_source']}/17；一致性 pass="
          f"{s['consistency_pass']}/17；消费合同 pass={s['consumption_pass']}"
          f"/17；注册表 schema pass={s['schema_validation_pass']}/17")
    print(f"[s27-s21decl] S25 样本板（{S25_SAMPLE_PID}）声明与 S25 记录逐"
          f"字段相等（跨记录交叉验证 pass）")
    print("[s27-s21decl] --- 新件 sha256（前 8）---")
    for path in sorted(written):
        print(f"[s27-s21decl]   {path.relative_to(REPO).as_posix()}: "
              f"{written[path][:8]}")
    print("[s27-s21decl] 原 S21 批次文件零改动（只读引用层）| APR-0014 | "
          "不是门，零门翻转")


if __name__ == "__main__":
    main()
