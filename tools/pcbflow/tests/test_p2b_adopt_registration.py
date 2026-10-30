"""P2-B 采纳包测试（P2-ADOPT-R1）：schema 注册 + 能力/命名/口径定稿 +
staging 绑定政策 + S21 历史补声明工件 + r5 批准工件（APR-0012..0016）。

覆盖：
- 注册表追加式注册：artifact-role-declaration-v1 在 registry；REGISTRY_VERSION
  保持 3.0；既有 disposition_record schema_hash 与 r4 账本 schema_validation
  钉值相等（追加不改既有哈希）；合法声明（source/analysis/staging，test_p2
  同款夹具）过 schemas.validate 零错误；非法变体（analysis 带 check_scope、
  staging 缺/None transform、坏哈希、未知 role、非法 capability、source
  loss_notes 非空、多余键）各自报错；jsonschema 交叉验证对拍（库缺席 skip）；
- 六能力枚举冻结断言（集合恰等；无 tool_export_target）；
- STAGING_BINDING_POLICY 常量断言（status/date/rule/enforcement）；
- 三角色名冻结 + source check_scope 可空常量断言；
- s27 工件 byte-exact 重跑（脚本 build() 两次一致且与落盘件逐字节一致）+
  17 板声明逐链复验（registry schema/一致性/消费合同零错误）；
- s28 r5 工件 byte-exact 重跑 + ledger 链校验（6 条；r4 head 330d6392 续链
  锚定自证）+ 处置记录 schema 合法 + user_decisions 原文在场；
- 既有 r4 及更早台账文件、S21 批次核心件、受保护三文件 sha256 与开工实测
  记录逐一比对（零改动断言）。

生成器模式：纯内存构造+磁盘实读复验、零子进程、零写盘、零网络、无
wall-clock（断言值均来自落盘件/脚本常量）。
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import artifact_roles as ar, hashing, ledger, schemas  # noqa: E402

jsonschema = pytest.importorskip("jsonschema", reason="库缺席仅跳过对拍")

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(REPO, "scripts", f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s27 = _load_script("s27_s21_historical_declarations")
s28 = _load_script("s28_p2_adoption_approvals")

REL_DECL = "out/v3-tl5/s21-historical-staging-declarations-r1.json"
REL_VALID = "out/v3-tl5/s21-historical-declarations-validation-r1.json"
REL_R5_BUNDLE = "out/v3-approvals/approvals-bundle-r5.json"
REL_R5_LEDGER = "out/v3-approvals/decision-ledger-r5.jsonl"

R4_HEAD = ("330d6392ea7f6edadd83cbdcc663d7efd2de14585fea46b7da55b46d7b77d4d9")
R4_LEDGER_DISPOSITION_SCHEMA_SHA = (
    "09dd31fdeabb6656a0236dfd44e81bcd3013c9ded9463a7f93a66c0315fca71d")

LEGACY_SCHEMA_NAMES = ("gate_record", "disposition_record", "judge_pre_record",
                       "judge_post_record", "decision_ledger_entry",
                       "critic_run_record", "queue_event", "physics_report",
                       "physics_coverage", "bring_up_report",
                       "external_execution_record", "proposal_patch",
                       "search_space", "project_manifest", "profile")

# 开工实测入账（收尾零改动断言依据；含受保护三文件与 S21/S25 核心件）
UNCHANGED_FILES = {
    "pcbflow/cli.py":
        "3bfc940701d1be82029877583a0a41f49741228f2e89a321b7dafa98d179aae8",  # M1 refresh: accept copper-loop baseline 6ed4f3fd...->0a738047...; value source = measured sha256(pcbflow/cli.py) (2026-09-11)
    "pcbflow/config.py":
        "8ad12b3fab12f19546034b5421aa77053f4115b91b36b87b9dfabc9075fdcf82",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json":
        "d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd896d9301690b3d",
    "out/v3-approvals/approvals-bundle.json":
        "96013156e32ab1227f51917c5d811a0aefafbf90bb281779c6fbb6a65bb8b36d",
    "out/v3-approvals/approvals-bundle-r2.json":
        "6d35b70f64753404df32edeb3b2f697bdf06f916fc36da34a45f3c65a9fcfa2b",
    "out/v3-approvals/approvals-bundle-r3.json":
        "7696c5d88c4086094394e2160aa170805dbe0bf7d2e6c8237bfd47bbd1c49042",
    "out/v3-approvals/approvals-bundle-r4.json":
        "a9e74e8b1efbd72979e9295ae6971ceed43c39803ed126a5c3d10b25c7ad8bb2",
    "out/v3-approvals/checkpoint-verify.json":
        "6f291b2a819139b4b18ae9d444fc41dff74992257347112be42712117625e06b",
    "out/v3-approvals/decision-ledger.jsonl":
        "12db3b031c8b5f0a71ea9a85ff1ee0e576f7be02f8f0d57695de736085cdd1df",
    "out/v3-approvals/decision-ledger-r2.jsonl":
        "b33964d0de8bb67a3a567a3333640f7b99abf7fae1f1a49efe500a704f7abe48",
    "out/v3-approvals/decision-ledger-r3.jsonl":
        "27a4a3fb9097f63831215ea416738e280aef75b6141867d9f4d070be3bf481ac",
    "out/v3-approvals/decision-ledger-r4.jsonl":
        "c7420b9e98fcacc31ba93130fe27551cfd5fe1fec61be763a42d2094190b712e",
    "out/v3-approvals/ledger-checkpoint.json":
        "468fe858542c13fb21be1fd40be3f9947d4ed0b2691fec477a39da1580c5ea7c",
    "out/v3-approvals/ledger-checkpoint-r2.json":
        "47fef204a817cf792c7cbeb0ba33b9d78f8f5daab32604dd7b3987ce0b0beca3",
    "out/v3-approvals/ledger-checkpoint-r3.json":
        "6361b4909439a9ed88e856547a18c261cfebe61e9c51b78bd1ffa2cdd3317137",
    "out/v3-approvals/ledger-verify.json":
        "4db7991f96d9ed61bfb5d6866a0354ad28ce140bef49d81e00fd2cf06424a9ee",
    "out/v3-approvals/ledger-verify-r2.json":
        "c5cf4920d0cda52c1b14e375a1e1abf88df03d095fdaf6b3e808c92b2fb69af4",
    "out/v3-approvals/ledger-verify-r3.json":
        "516cae89d2e2b0120ae889ff5871eaea56b5238f44e0276fb618856aac3bf0e3",
    "out/v3-approvals/disposition-APR-0001-tl0-gate-scope.json":
        "cc76e5451948e9c207c5284f9a439dcf9d4d5cce810b2657835dfcba09a8c840",
    "out/v3-approvals/disposition-APR-0002-tl1-schema-baseline.json":
        "4c122e0ee8dad91e05449611cf76b505ea61f30ab8ac938bb21e18a2f536bb96",
    "out/v3-approvals/disposition-APR-0003-tl3-required-scope.json":
        "5aa7c5876fa8a6a6733f6504e1c7e4f9a26eca66680a379d33ac9978e04f64ba",
    "out/v3-approvals/disposition-APR-0004-tl4-adoption-disposition.json":
        "d983e2f6983d77a7054c6e878f7b17e4b739178d8da192516d1c78dd499a77d7",
    "out/v3-approvals/disposition-APR-0005-critic-duty-level.json":
        "c1ce1b601d125338f64da5bb4ff8b66dd978b91c50a1a2e1d66b2f923e29ee52",
    "out/v3-approvals/disposition-APR-0006-tl5-corpus-authorization.json":
        "c15174fb27574fff1d2e495bc26434c6fd01f72e602d814be1c835e4974c53df",
    "out/v3-approvals/disposition-APR-0007-item-run-r1-disposition.json":
        "2a3b985a300c72fcfd7fea232422f26c272b2b269752a454c1574e7ca74284a3",
    "out/v3-approvals/disposition-APR-0008-calibration-domain-seed.json":
        "3a3c8d58549ba134b84496b06e150dbd87031c33f41b77fccc9c46db80766690",
    "out/v3-approvals/disposition-APR-0009-verification-roadmap-tiers.json":
        "7f6561e45e14b27802236510cb4e7f931a17a1fba271448ce1efe4d9280734ca",
    "out/v3-approvals/disposition-APR-0010-item-run-r2-disposition.json":
        "4eb45dc44bb11bd7696cc51b840bac0f499f160e8a5c449d6ab1c6facba67883",
    "out/v3-approvals/disposition-APR-0011-calibration-threshold-"
    "provisional-adoption.json":
        "47a52b4576f38fcb036286d13381a49d93b91741520a96fdb415acbf81db0d1f",
    "out/v3-tl5/k9-route-check-batch-r1/plan.json":
        "2c8aca6a27d7309e36de4354f41b7b2942a9dfed8014d69290b38b73bb84e17e",
    "out/v3-tl5/k9-route-check-batch-r1/batch-summary.json":
        "a683137eb279292e5e1265618993f279e4e5648715f1757f4e551f2c770a1202",
    "out/v3-tl5/artifact-roles-validation-r1.json":
        "d88945d2957870fc93f27fa2efdd953fdaa6be31c93ef8ffb92f6ca4b4745ede",
    "out/v3-tl5/dataset-manifest-kicad-demos-r2.json":
        "2af5fdca111221a06ceebc40223bcaa0d61f8bc7e568b012db041ef2ed75d310",
}

SHA_A, SHA_B, SHA_C = "a" * 64, "b" * 64, "c" * 64


# ---------------------------------------------------------------------------
# 夹具构造器（test_p2 同款；纯内存）
# ---------------------------------------------------------------------------

def _manifest_binding(source_sha256=SHA_A, entry_key="demo/board_a"):
    return {"kind": ar.SBK_DATASET_MANIFEST_ENTRY,
            "manifest_ref": "out/v3-tl5/dataset-manifest-r2.json",
            "entry_key": entry_key,
            "source_sha256": source_sha256}


def _source_decl(**kw):
    params = dict(
        role=ar.ROLE_SOURCE, artifact_id="board-a", format_id="kicad_pcb",
        format_version="20171130",
        capabilities=[ar.CAP_ANALYSIS_STATS, ar.CAP_TOOL_LOADABLE],
        source_binding=_manifest_binding(), transform=None,
        output_sha256=SHA_A, rule_dependencies=[],
        check_scope=None, loss_notes=None)
    params.update(kw)
    return ar.build_artifact_role_declaration(**params)


def _analysis_decl(**kw):
    params = dict(
        role=ar.ROLE_ANALYSIS, artifact_id="board-a", format_id="analysis",
        format_version="k9-path-r1",
        capabilities=[ar.CAP_ANALYSIS_STATS, ar.CAP_ANALYSIS_TOPOLOGY,
                      ar.CAP_ANALYSIS_FEATURES],
        source_binding=_manifest_binding(),
        transform={"description": "text-level normalization to analysis "
                                  "dialect",
                   "tool": "pcbflow.corpus_convert",
                   "tool_version": "k9-path-r1",
                   "saved_by": "scripts/s18 (r2)"},
        output_sha256=SHA_B, rule_dependencies=[],
        check_scope=None,
        loss_notes={"graphics_and_text": "not in normalized board",
                    "zones": "not in normalized board"})
    params.update(kw)
    return ar.build_artifact_role_declaration(**params)


def _staging_decl(**kw):
    params = dict(
        role=ar.ROLE_STAGING, artifact_id="board-a", format_id="kicad_pcb",
        format_version="20171130",
        capabilities=[ar.CAP_TOOL_LOADABLE, ar.CAP_TOOL_CHECKABLE],
        source_binding=_manifest_binding(),
        transform={"description": "tool-saved staging package",
                   "tool": "kicad-cli", "tool_version": "10.0.5",
                   "saved_by": "kicad-cli pcb drc --save-board"},
        output_sha256=SHA_C, rule_dependencies=["kicad-cli default drc"],
        check_scope=ar.CHECK_SCOPE_BARE, loss_notes=None)
    params.update(kw)
    return ar.build_artifact_role_declaration(**params)


def _repo_rel(rel: str) -> str:
    return os.path.join(REPO, *rel.split("/"))


def _read_bytes(rel: str) -> bytes:
    with open(_repo_rel(rel), "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# ① 注册表追加式注册
# ---------------------------------------------------------------------------

def test_registry_appends_artifact_role_declaration_additively():
    assert "artifact-role-declaration-v1" in schemas.SCHEMAS
    # 注册表快照同步（schemas.py 注册表注释程序）：22=18（16 legacy+P2-7
    # critic-flag-verdict-v1 @2026-09-10+observation-row-v1 @2026-09-12）
    # +REPAIR-P3 W-5 追加的 toolchain_lock 四孤儿名（constraints/coverage/
    # envelope/impedance_targets-v1，@2026-09-22，追加式既有条目零改动；
    # 计数随追加演进更新=快照同步断言的设计行为，哈希断言不受影响）
    assert len(schemas.SCHEMAS) == 22
    for name in LEGACY_SCHEMA_NAMES:
        assert name in schemas.SCHEMAS
    assert schemas.REGISTRY_VERSION == "3.0"          # 升版被禁止
    # 既有条目哈希零变化（与 r4 账本 schema_validation 钉值相等）
    assert schemas.schema_hash("disposition_record") == \
        R4_LEDGER_DISPOSITION_SCHEMA_SHA
    hs = {n: schemas.schema_hash(n) for n in schemas.SCHEMAS}
    assert len(set(hs.values())) == len(hs)           # 互异
    assert schemas.schema_hash("artifact-role-declaration-v1") == \
        hs["artifact-role-declaration-v1"]            # 重算稳定


def test_legal_declarations_pass_registry_schema():
    src, ana, stg = _source_decl(), _analysis_decl(), _staging_decl()
    for d in (src, ana, stg):
        assert schemas.validate("artifact-role-declaration-v1", d) == []
        assert jsonschema.validate(
            d, schemas.SCHEMAS["artifact-role-declaration-v1"]) is None
    # S25 落盘三声明（真实产物形状）同样零错误
    s25 = json.loads(_read_bytes("out/v3-tl5/artifact-roles-validation-r1.json")
                     .decode("utf-8"))
    for d in s25["declarations"].values():
        assert schemas.validate("artifact-role-declaration-v1", d) == []


@pytest.mark.parametrize("label,mutate", [
    ("analysis_with_check_scope",
     lambda d: d.update(check_scope=ar.CHECK_SCOPE_BARE)),
    ("source_loss_notes_not_null",
     lambda d: d.update(loss_notes={"x": "y"})),
    ("staging_transform_none",
     lambda d: d.update(transform=None)),
    ("staging_transform_key_missing",
     lambda d: d.pop("transform")),
    ("staging_check_scope_null",
     lambda d: d.update(check_scope=None)),
    ("bad_output_hash",
     lambda d: d.update(output_sha256="zz")),
    ("bad_binding_hash",
     lambda d: d.update(source_binding=dict(
         d["source_binding"], source_sha256="not-a-hash"))),
    ("unknown_role",
     lambda d: d.update(role="weird_role")),
    ("unknown_capability",
     lambda d: d.update(capabilities=[ar.CAP_TOOL_LOADABLE, "made_up"])),
    ("binding_kind_not_manifest",
     lambda d: d.update(source_binding=dict(
         d["source_binding"], kind="raw_file_direct"))),
    ("extra_key",
     lambda d: d.update(unexpected=1)),
    ("contract_mismatch",
     lambda d: d.update(contract="other#contract")),
])
def test_illegal_variants_rejected_by_schema(label, mutate):
    base = {"analysis_with_check_scope": _analysis_decl,
            "source_loss_notes_not_null": _source_decl}.get(
        label, _staging_decl)
    obj = base()
    mutate(obj)
    assert schemas.validate("artifact-role-declaration-v1", obj), label
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(obj, schemas.SCHEMAS["artifact-role-declaration-v1"])


# ---------------------------------------------------------------------------
# ②③④⑤ 定稿常量
# ---------------------------------------------------------------------------

def test_capability_enum_frozen_six():
    assert ar.CAPABILITY_ENUM_FROZEN is True
    assert ar.CAPABILITY_ENUM_FROZEN_APPROVAL == "APR-0013"
    assert ar.CAPABILITY_ENUM_FROZEN_DATE == "2026-09-06"
    assert set(ar.ALL_CAPABILITIES) == {
        "analysis_stats", "analysis_topology", "analysis_features",
        "tool_loadable", "tool_checkable", "tool_transform_target"}
    assert len(ar.ALL_CAPABILITIES) == 6
    assert "tool_export_target" not in ar.ALL_CAPABILITIES   # 明确不增补
    assert set(ar.ANALYSIS_CAPABILITIES) | \
        set(ar.EXECUTION_CAPABILITIES) == set(ar.ALL_CAPABILITIES)
    assert not set(ar.ANALYSIS_CAPABILITIES) & set(ar.EXECUTION_CAPABILITIES)
    # loss_notes 为空 = staging 声明分析能力子集的唯一判据（判据成立登记）
    assert ar.STAGING_ANALYSIS_CAP_CRITERION == "loss_notes_empty"
    assert ar.STAGING_ANALYSIS_CAP_CRITERION_APPROVAL == "APR-0013"


def test_staging_binding_policy_adopted():
    p = ar.STAGING_BINDING_POLICY
    assert p["status"] == "adopted"
    assert p["adopted_date"] == "2026-09-06"
    assert p["approval_ref"] == "APR-0014"
    assert "artifact-role-declaration-v1" in p["rule"]
    assert "validate_executor_consumption" in p["rule"]
    assert "TL-5" in p["enforcement"]
    assert "未接线" in p["enforcement"]   # 本批准包不接线生产链


def test_role_naming_frozen_and_source_check_scope_nullable():
    assert ar.ROLE_NAMING_FROZEN is True
    assert ar.ROLE_NAMING_FROZEN_APPROVAL == "APR-0015"
    assert ar.ROLES == ("source_design_package",
                        "normalized_analysis_model",
                        "staging_execution_package")
    assert ar.SOURCE_CHECK_SCOPE_NULLABLE is True
    assert ar.SOURCE_CHECK_SCOPE_APPROVAL == "APR-0016"
    # 行为零改动自证：source 可声明口径；analysis 恒 None；staging 必填
    src = _source_decl(check_scope=ar.CHECK_SCOPE_BARE)
    assert src["check_scope"] == ar.CHECK_SCOPE_BARE
    with pytest.raises(ValueError, match="check_scope"):
        _analysis_decl(check_scope=ar.CHECK_SCOPE_BARE)
    with pytest.raises(ValueError, match="check_scope"):
        _staging_decl(check_scope=None)


# ---------------------------------------------------------------------------
# ④（任务 T4）s27 S21 历史补声明工件
# ---------------------------------------------------------------------------

def test_s21_historical_declarations_byte_exact_rerun():
    doc1, valid1 = s27.build()
    doc2, valid2 = s27.build()
    assert hashing.canonical_json_bytes(doc1) == \
        hashing.canonical_json_bytes(doc2)
    assert hashing.canonical_json_bytes(valid1) == \
        hashing.canonical_json_bytes(valid2)
    assert _read_bytes(REL_DECL) == hashing.canonical_json_bytes(doc1)
    assert _read_bytes(REL_VALID) == hashing.canonical_json_bytes(valid1)
    # 验证件绑定声明件 canonical sha256
    assert valid1["subject"]["sha256"] == \
        hashing.sha256_bytes(hashing.canonical_json_bytes(doc1))
    assert valid1["subject"]["path_rel"] == REL_DECL


def test_s21_historical_declarations_all_chains_valid():
    doc = json.loads(_read_bytes(REL_DECL).decode("utf-8"))
    s = doc["summary"]
    assert s["boards_total"] == 17
    assert s["byte_identical_to_source"] == 17
    assert s["consistency_pass"] == 17
    assert s["consumption_pass"] == 17
    assert s["schema_validation_pass"] == 17
    assert len(doc["boards"]) == 17
    # 声明层逐板复验（与工件内记录独立重算）
    for b in doc["boards"]:
        src = b["declarations"]["source"]
        stg = b["declarations"]["staging"]
        assert schemas.validate("artifact-role-declaration-v1", src) == []
        assert schemas.validate("artifact-role-declaration-v1", stg) == []
        assert ar.validate_role_consistency([src, stg]) == []
        assert ar.validate_executor_consumption(
            stg, executor_backend=s27.EXECUTOR["backend"],
            executor_version=s27.EXECUTOR["version"],
            supported_formats=s27.EXECUTOR["supported_formats"],
            capabilities=s27.EXECUTOR["capabilities"]) == []
        assert stg["check_scope"] == ar.CHECK_SCOPE_BARE
        assert stg["loss_notes"] is None and src["loss_notes"] is None
        assert stg["output_sha256"] == b["staging_sha256"]
        assert src["output_sha256"] == b["source_sha256"]
    # DRC 证据分态如实：11 pass + 5 dual-run 不稳 + 1 拒绝加载（不冒称）
    assert s["drc_evidence_present"] == 11
    assert s["drc_evidence_present_dual_run_unstable"] == 5
    assert s["drc_evidence_absent_executor_refused_load"] == 1
    refused = s["executor_load_refused_boards"]
    assert refused == ["kicaddemo-constraints-constraints"]
    refused_board = next(b for b in doc["boards"]
                         if b["profile_id"] in refused)
    assert refused_board["drc_evidence"]["evidence_state"] == \
        "absent_executor_refused_load"
    assert "拒绝加载" in refused_board["declarations"]["staging"][
        "transform"]["description"]
    assert refused_board["executor_consumption"]["evidence_caveat"]
    # S25 样本板声明与 S25 记录逐字段相等（跨记录交叉验证）
    s25 = json.loads(_read_bytes("out/v3-tl5/artifact-roles-validation-r1.json")
                     .decode("utf-8"))
    sample = next(b for b in doc["boards"]
                  if b["profile_id"] == s27.S25_SAMPLE_PID)
    assert sample["declarations"]["source"] == s25["declarations"]["source"]
    assert sample["declarations"]["staging"] == s25["declarations"]["staging"]
    # 采纳与历史边界声明在场
    assert doc["adoption"]["approval_ref"] == "APR-0014"
    assert doc["historical_boundary"]["original_records_untouched"] is True


# ---------------------------------------------------------------------------
# ⑤（任务 T6）r5 批准工件 + 台账零改动
# ---------------------------------------------------------------------------

def _collect_evidence_hashes() -> dict:
    hashes = {name: hashing.sha256_file(str(_repo_rel(rel)))
              for name, rel in s28.EVIDENCE_FILES_R5}
    hashes["_r4_ledger_file"] = hashing.sha256_file(
        str(_repo_rel("out/v3-approvals/decision-ledger-r4.jsonl")))
    return hashes


def test_r5_approvals_bundle_byte_exact_rerun():
    bundle = s28.build_approvals_bundle_r5(_collect_evidence_hashes())
    disk = _read_bytes(REL_R5_BUNDLE)
    assert disk == hashing.canonical_json_bytes(bundle)
    assert hashing.sha256_bytes(
        s28._ledger_bytes(bundle["ledger_entries"])) == \
        bundle["ledger_file_sha256"]
    assert _read_bytes(REL_R5_LEDGER) == s28._ledger_bytes(
        bundle["ledger_entries"])
    assert bundle["approval_count"] == 5
    assert bundle["revision"] == "v3-approvals-r5"
    assert bundle["approval_date"] == "2026-09-06"
    assert bundle["gate_write_scan"] == {
        f"APR-00{i}": [] for i in range(12, 17)}   # 零门写


def test_r5_ledger_chain_and_r4_head_continuation():
    entries = [json.loads(line) for line in _read_bytes(
        REL_R5_LEDGER).decode("utf-8").splitlines()]
    assert len(entries) == 6
    assert ledger.verify_chain(entries) == []
    assert ledger.verify_supersedes(entries) == []
    r4_entry = json.loads(_read_bytes(
        "out/v3-approvals/decision-ledger-r4.jsonl").decode("utf-8")
        .splitlines()[0])
    # 续链锚定：首条=r4 末条原样续入；第二条 prev 锚 r4 末条 entry，
    # head 以 r4 head 330d6392 为 prev_head 计算（跨文件续链）
    assert entries[0] == r4_entry
    assert entries[0]["ledger_head_sha256"] == R4_HEAD
    first_new = entries[1]
    assert first_new["prev_entry_sha256"] == r4_entry["entry_sha256"]
    assert first_new["ledger_head_sha256"] == hashing.sha256_text(
        R4_HEAD + ":" + first_new["entry_sha256"])
    assert first_new["disposition_refs"] == ["APR-0012"]
    assert first_new["snapshot_revision"] == "v3-approvals-r5"
    assert first_new["authority"] == "human"
    assert first_new["trust_level"] == "untrusted"
    assert [e["disposition_refs"][0] for e in entries[1:]] == \
        [f"APR-00{i}" for i in range(12, 17)]
    # checkpoint 一致
    bundle = json.loads(_read_bytes(REL_R5_BUNDLE).decode("utf-8"))
    ckpt = bundle["ledger_checkpoint"]
    assert ckpt["checkpoint_id"] == "CKPT-V3-APPROVALS-R5"
    assert ledger.verify_against_checkpoint(entries, ckpt) == []
    assert ckpt["entry_count"] == 6


def test_r5_dispositions_schema_valid_with_user_decisions():
    bundle = json.loads(_read_bytes(REL_R5_BUNDLE).decode("utf-8"))
    codes = {"APR-0012": "schema_registration_additive_approved",
             "APR-0013": "capability_enum_finalized_six",
             "APR-0014":
                 "staging_binding_adopted_s21_retroactive_declared",
             "APR-0015": "role_naming_frozen_asis",
             "APR-0016": "source_check_scope_nullable_approved"}
    labels = {"APR-0012": "批准注册", "APR-0013": "六项定稿",
              "APR-0014": "强制+S21补声明", "APR-0015": "按现值定稿",
              "APR-0016": "允许source可空声明"}
    for rec in bundle["dispositions"]:
        assert schemas.validate("disposition_record", rec) == []
        assert rec["kind"] == "accept"
        assert rec["scope"] == "adoption"
        assert rec["approver"] == "user"
        assert rec["approver_role"] == "human_authority"
        apr = rec["disposition_id"]
        assert rec["rationale_code"] == codes[apr]
        ud = bundle["user_decisions"][apr]
        assert ud["decision_label"] == labels[apr]
        assert ud["decided_date"] == "2026-09-06"
        assert ud["decision_label"] in rec["rationale_text"]
        assert "supersedes" in rec["rationale_text"]   # 追加式演进限定在场
    # 语义限定要点抽查
    by_id = {r["disposition_id"]: r["rationale_text"] for r
             in bundle["dispositions"]}
    assert "REGISTRY_VERSION 保持" in by_id["APR-0012"]
    assert "disposition-APR-0002" in by_id["APR-0012"]
    assert "tool_export_target" in by_id["APR-0013"]
    assert "零改动" in by_id["APR-0014"]
    assert "下一轮 TL-5 staging 生产恢复时" in by_id["APR-0014"]
    assert "按现值" in by_id["APR-0015"]
    assert "analysis 侧" in by_id["APR-0016"]


def test_prior_ledgers_s21_batch_and_protected_files_unchanged():
    """既有 r4 及更早台账/S21 核心件/受保护三文件：与开工实测逐一比对。"""
    for rel, want in UNCHANGED_FILES.items():
        assert hashing.sha256_file(_repo_rel(rel)) == want, rel
