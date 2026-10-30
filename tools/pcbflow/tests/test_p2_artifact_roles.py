"""P2 会话测试：三类设计对象角色声明契约（artifact_roles，proposal）。

覆盖（对照纠偏词 P2 实现要求，全部纯内存构造，不读盘；脚本级验证由
scripts/s25_artifact_roles_validate.py 落盘件承载）：
- 三角色合法构造路径各一（最小合法参数；声明自带 contract+proposal
  标注；capabilities 排序输出）；
- analysis 角色尝试带执行能力 → ValueError（结构不可能：分析方言不是
  可加载执行板）；
- analysis 缺 loss_notes → ValueError；staging 缺 check_scope → ValueError；
- source_binding.kind 非 manifest 白名单 → ValueError（防静默绕过
  manifest 直读 datasets raw 板）；
- validate_executor_consumption：analysis 消费必拒（错误码含
  analysis_model_not_executable），即使 artifact_id 以 .kicad_pcb 结尾
  （path/后缀不参与判定的负向语义）；
- staging 消费：能力超执行器支持集 → 拒（capability_not_supported）；
  check_scope 缺 → 拒（check_scope_missing）；全匹配 → []；
- validate_role_consistency：analysis 与 staging 的 source 不一致 →
  错误（source_binding_inconsistent）；一致且 hash 链闭合 → []；
- hash 格式非法（output_sha256 / source_binding.source_sha256）→
  ValueError（fail-closed，错误消息明确到字段）。

生成器模式：纯内存构造、零子进程、零写盘、零网络、无 wall-clock。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import artifact_roles as ar  # noqa: E402

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


# ---------------------------------------------------------------------------
# 最小合法参数构造器（纯内存）
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


def _executor(**kw):
    params = dict(executor_backend="kicad-cli", executor_version="10.0.5",
                  supported_formats=["kicad_pcb"],
                  capabilities=list(ar.EXECUTION_CAPABILITIES))
    params.update(kw)
    return params


# ---------------------------------------------------------------------------
# 1) 三角色合法构造路径
# ---------------------------------------------------------------------------

def test_three_roles_build_ok_minimal_params():
    src = _source_decl()
    ana = _analysis_decl()
    stg = _staging_decl()
    assert src["role"] == ar.ROLE_SOURCE
    assert ana["role"] == ar.ROLE_ANALYSIS
    assert stg["role"] == ar.ROLE_STAGING
    for d in (src, ana, stg):
        assert d["contract"] == ar.CONTRACT_ID
        assert d["proposal_status"] == ar.PROPOSAL_STATUS
        assert d["capabilities"] == sorted(d["capabilities"])
    assert src["transform"] is None
    assert ana["loss_notes"] and stg["check_scope"] == ar.CHECK_SCOPE_BARE
    assert stg["rule_dependencies"] == ["kicad-cli default drc"]


# ---------------------------------------------------------------------------
# 2) analysis 带执行能力 → ValueError（结构不可能）
# ---------------------------------------------------------------------------

def test_analysis_cannot_carry_execution_capability():
    with pytest.raises(ValueError, match="structurally cannot carry"):
        _analysis_decl(capabilities=[ar.CAP_ANALYSIS_STATS,
                                     ar.CAP_TOOL_LOADABLE])


# ---------------------------------------------------------------------------
# 3) analysis 缺 loss_notes / staging 缺 check_scope → ValueError
# ---------------------------------------------------------------------------

def test_analysis_requires_loss_notes():
    with pytest.raises(ValueError, match="loss_notes"):
        _analysis_decl(loss_notes=None)
    with pytest.raises(ValueError, match="loss_notes"):
        _analysis_decl(loss_notes={})


def test_staging_requires_check_scope():
    with pytest.raises(ValueError, match="check_scope"):
        _staging_decl(check_scope=None)
    with pytest.raises(ValueError, match="check_scope"):
        _staging_decl(check_scope="whatever_rules")


def test_staging_requires_rule_dependencies_and_transform():
    with pytest.raises(ValueError, match="rule_dependencies"):
        _staging_decl(rule_dependencies=[])
    with pytest.raises(ValueError, match="transform"):
        _staging_decl(transform=None)


# ---------------------------------------------------------------------------
# 4) source_binding.kind 非 manifest 白名单 → ValueError
# ---------------------------------------------------------------------------

def test_source_binding_kind_whitelist_rejects_direct_read():
    with pytest.raises(ValueError, match="dataset_manifest_entry"):
        _source_decl(source_binding=_manifest_binding() |
                     {"kind": "raw_file_direct"})
    with pytest.raises(ValueError, match="dataset_manifest_entry"):
        _analysis_decl(source_binding={"kind": "filesystem_path",
                                       "manifest_ref": "x", "entry_key": "y",
                                       "source_sha256": SHA_A})


# ---------------------------------------------------------------------------
# 5) analysis 消费必拒，即使 artifact_id 以 .kicad_pcb 结尾
# ---------------------------------------------------------------------------

def test_executor_rejects_analysis_even_with_kicad_pcb_suffix():
    ana = _analysis_decl(artifact_id="profiles/board-a/board.kicad_pcb",
                         format_id="kicad_pcb")
    errs = ar.validate_executor_consumption(ana, **_executor())
    codes = [e["code"] for e in errs]
    assert "analysis_model_not_executable" in codes


def test_executor_rejects_source_role_too():
    errs = ar.validate_executor_consumption(_source_decl(), **_executor())
    assert [e["code"] for e in errs] == ["source_package_read_only"]


# ---------------------------------------------------------------------------
# 6) staging 消费：能力超集拒 / check_scope 缺拒 / 全匹配空
# ---------------------------------------------------------------------------

def test_executor_staging_capability_superset_rejected():
    stg = _staging_decl(capabilities=[ar.CAP_TOOL_LOADABLE,
                                      ar.CAP_TOOL_CHECKABLE,
                                      ar.CAP_TOOL_TRANSFORM_TARGET])
    errs = ar.validate_executor_consumption(
        stg, **_executor(capabilities=[ar.CAP_TOOL_LOADABLE,
                                       ar.CAP_TOOL_CHECKABLE]))
    assert [e["code"] for e in errs] == ["capability_not_supported"]
    assert "tool_transform_target" in errs[0]["detail"]


def test_executor_staging_format_unsupported_rejected():
    stg = _staging_decl(format_id="kicad_pcb")
    errs = ar.validate_executor_consumption(
        stg, **_executor(supported_formats=["kicad_sch"]))
    assert [e["code"] for e in errs] == ["format_not_supported"]


def test_executor_staging_missing_check_scope_rejected():
    stg = _staging_decl()
    malformed = dict(stg, check_scope=None)
    errs = ar.validate_executor_consumption(malformed, **_executor())
    codes = [e["code"] for e in errs]
    assert "check_scope_missing" in codes
    assert "declaration_invalid" in codes


def test_executor_staging_full_match_consumable():
    stg = _staging_decl()
    assert ar.validate_executor_consumption(stg, **_executor()) == []


def test_executor_support_sets_must_be_explicit():
    stg = _staging_decl()
    errs = ar.validate_executor_consumption(
        stg, executor_backend="kicad-cli", executor_version="10.0.5",
        supported_formats=[], capabilities=[])
    codes = [e["code"] for e in errs]
    assert codes == ["executor_support_missing", "executor_support_missing"]


# ---------------------------------------------------------------------------
# 7) 链一致性
# ---------------------------------------------------------------------------

def test_consistency_chain_ok():
    errs = ar.validate_role_consistency(
        [_source_decl(), _analysis_decl(), _staging_decl()])
    assert errs == []


def test_consistency_source_mismatch_between_analysis_and_staging():
    # 同链内 analysis 与 staging 的 source_binding 不一致 → 一致性错误
    ana = _analysis_decl(source_binding=_manifest_binding(
        source_sha256=SHA_B, entry_key="demo/board_a"))
    errs = ar.validate_role_consistency(
        [_source_decl(), ana, _staging_decl()])
    assert [e["code"] for e in errs] == ["source_binding_inconsistent"]


def test_consistency_hash_chain_broken_vs_source_output():
    # 绑定一致，但 source 声明的 output_sha256 与绑定 source_sha256 不符
    # → 下游 analysis/staging 全部报 hash 链断裂
    src = _source_decl(output_sha256=SHA_C)
    errs = ar.validate_role_consistency(
        [src, _analysis_decl(), _staging_decl()])
    broken = [e for e in errs if e["code"] == "source_hash_chain_broken"]
    assert {e["role"] for e in broken} == {ar.ROLE_ANALYSIS,
                                           ar.ROLE_STAGING}


def test_consistency_staging_source_binding_differs():
    stg = _staging_decl(source_binding=_manifest_binding(
        source_sha256=SHA_A, entry_key="demo/other_board"))
    errs = ar.validate_role_consistency(
        [_source_decl(), _analysis_decl(), stg])
    assert [e["code"] for e in errs] == ["source_binding_inconsistent"]


def test_consistency_staging_without_source_declaration():
    errs = ar.validate_role_consistency([_staging_decl()])
    assert [e["code"] for e in errs] == ["source_declaration_missing"]


# ---------------------------------------------------------------------------
# 8) hash 格式非法 → ValueError
# ---------------------------------------------------------------------------

def test_invalid_hash_fail_closed():
    with pytest.raises(ValueError, match="output_sha256"):
        _source_decl(output_sha256="d5f4162d")
    with pytest.raises(ValueError, match="source_sha256"):
        _source_decl(source_binding=_manifest_binding(
            source_sha256="D5F4162D" * 8))
    with pytest.raises(ValueError, match="source_sha256"):
        _staging_decl(source_binding=_manifest_binding(
            source_sha256="not-a-hash"))


# ---------------------------------------------------------------------------
# 补充：validate_declaration 结构校验（不抛异常，收集错误）
# ---------------------------------------------------------------------------

def test_validate_declaration_collects_errors_without_raising():
    stg = _staging_decl()
    malformed = dict(stg, output_sha256="zz", check_scope=None)
    errs = ar.validate_declaration(malformed)
    details = " | ".join(e["detail"] for e in errs)
    assert "output_sha256" in details and "check_scope" in details
    assert ar.validate_declaration(stg) == []
    assert ar.validate_declaration("not-a-dict")[0]["code"] == \
        "declaration_invalid"
