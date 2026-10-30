"""TD7 外部执行引擎 backend 合同测试（全合成数据；capability_claims 用例
只读引用仓库真实 toolchain_lock.json）。"""

import pytest

from pcbflow import external_backend, hashing, schemas, toolchain

_SHA_A = "ab" * 32
_SHA_B = "cd" * 32
_LOCK_SHA = "ef" * 32


# ---------------------------------------------------------------------------
# 合成数据工厂
# ---------------------------------------------------------------------------

def _cli_record(**overrides):
    kwargs = dict(
        execution_id="exec-cli-0001",
        project_id="proj-synth",
        profile_id="profile-synth",
        source_snapshot_sha256=_SHA_A,
        staging_path_sha256=_SHA_B,
        backend="freerouting-cli-jar",
        protocol="cli-argv",
        tool_version=None,
        toolchain_lock_sha256=_LOCK_SHA,
        started_by="pcbflow-route-cmd",
        timeout_s=600,
    )
    kwargs.update(overrides)
    return external_backend.build_execution_record(**kwargs)


def _mcp_record(**overrides):
    kwargs = dict(
        execution_id="exec-mcp-0001",
        project_id="proj-synth",
        profile_id="profile-synth",
        source_snapshot_sha256=_SHA_A,
        staging_path_sha256=_SHA_B,
        backend="freerouting-mcp",
        protocol="mcp-jsonrpc",
        tool_version=None,
        toolchain_lock_sha256=_LOCK_SHA,
        started_by="pcbflow-route-cmd",
        timeout_s=60,
        network_policy="loopback_only",
        peer_identity="freerouting-mcp-loopback@local",
        method_allowlist=["initialize", "route/autoroute"],
    )
    kwargs.update(overrides)
    return external_backend.build_execution_record(**kwargs)


CLI_DECL = {
    "backend": "freerouting-cli-jar",
    "protocol": "cli-argv",
    "executable_allowlist": ["java", "F:\\tools\\jre\\bin\\java.exe"],
    "method_allowlist": [],
    "path_allowlist": ["F:\\tools\\freerouting.jar", "staging/input.dsn",
                       "staging/output.ses", "F:\\tools\\jre\\bin\\java.exe"],
    "endpoint": None,
    "peer_identity": None,
}

MCP_DECL = {
    "backend": "freerouting-mcp",
    "protocol": "mcp-jsonrpc",
    "executable_allowlist": [],
    "method_allowlist": ["initialize", "route/autoroute"],
    "path_allowlist": [],
    "endpoint": "http://127.0.0.1:8765/mcp",
    "peer_identity": "freerouting-mcp-loopback@local",
}

CLI_ARGV_OK = ["java", "-jar", "F:\\tools\\freerouting.jar", "-de",
               "staging/input.dsn", "-do", "staging/output.ses"]


def _stages(*statuses):
    """按固定 STAGE_ORDER 生成 stage 序列（合成数据）。"""
    return [{"stage": s, "status": st}
            for s, st in zip(external_backend.STAGE_ORDER, statuses)]


# ---------------------------------------------------------------------------
# build_execution_record
# ---------------------------------------------------------------------------

def test_minimal_record_schema_valid():
    rec = _cli_record()
    assert schemas.validate("external_execution_record", rec) == []
    assert rec["schema_version"] == "3.0"
    assert rec["backend"] == "freerouting-cli-jar"
    assert rec["protocol"] == "cli-argv"


def test_record_default_isolation_fields():
    rec = _cli_record()
    assert rec["network_policy"] == "deny"
    assert rec["write_scope"] == "staging_only"
    assert rec["live_board_touched"] is False
    assert rec["resource_limits"] == {"max_threads": 1}


def test_missing_toolchain_lock_sha256_is_schema_error():
    # 形参缺失：合同参数必填
    with pytest.raises(TypeError):
        _cli_record_without = external_backend.build_execution_record(
            execution_id="x", project_id="p", profile_id="f",
            source_snapshot_sha256=_SHA_A, staging_path_sha256=_SHA_B,
            backend="freerouting-cli-jar", protocol="cli-argv",
            tool_version=None, started_by="pcbflow", timeout_s=60)
    # None 值：_SHA256_FIELD 不可空 → 构造自检抛 ValueError
    with pytest.raises(ValueError, match="toolchain_lock_sha256"):
        _cli_record(toolchain_lock_sha256=None)
    # 键缺失：schema required 直接报错
    rec = dict(_cli_record())
    del rec["toolchain_lock_sha256"]
    errors = schemas.validate("external_execution_record", rec)
    assert errors and any("toolchain_lock_sha256" in e for e in errors)


def test_builder_rejects_unknown_override_key():
    with pytest.raises(ValueError, match="多余键"):
        _cli_record(not_a_field=True)


def test_builder_hashes_and_strips_raw_argv():
    argv = ["java", "-jar", "freerouting.jar"]
    rec = _cli_record(argv_or_rpc=argv)
    assert "argv_or_rpc" not in rec
    assert rec["argv_or_rpc_hash"] == hashing.sha256_text(
        hashing.json_dumps(argv))
    assert schemas.validate("external_execution_record", rec) == []


def test_builder_rejects_shell_string_argv():
    with pytest.raises(ValueError, match="shell"):
        _cli_record(argv_or_rpc="java -jar freerouting.jar --evil")


# ---------------------------------------------------------------------------
# validate_policy：正向
# ---------------------------------------------------------------------------

def test_validate_policy_cli_ok():
    rec = {**_cli_record(), "argv_or_rpc": list(CLI_ARGV_OK)}
    assert external_backend.validate_policy(rec, CLI_DECL) == []


def test_validate_policy_cli_absolute_executable_ok():
    argv = ["F:\\tools\\jre\\bin\\java.exe", "-jar",
            "F:\\tools\\freerouting.jar"]
    rec = {**_cli_record(), "argv_or_rpc": argv}
    assert external_backend.validate_policy(rec, CLI_DECL) == []


def test_validate_policy_mcp_ok():
    rec = {**_mcp_record(), "rpc_method": "route/autoroute"}
    assert external_backend.validate_policy(rec, MCP_DECL) == []


# ---------------------------------------------------------------------------
# validate_policy：负向（fail-closed，返回所有违例）
# ---------------------------------------------------------------------------

def test_cli_network_loopback_rejected():
    rec = {**_cli_record(network_policy="loopback_only"),
           "argv_or_rpc": list(CLI_ARGV_OK)}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    assert any("network_policy" in e for e in errors)


def test_cli_executable_not_in_allowlist():
    rec = {**_cli_record(),
           "argv_or_rpc": ["evil-router.exe", "-de", "staging/input.dsn"]}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    assert any("executable_allowlist" in e for e in errors)


def test_cli_argv_parent_dir_traversal():
    rec = {**_cli_record(),
           "argv_or_rpc": ["java", "-jar", "staging\\..\\..\\evil\\evil.jar"]}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    assert any("'..' 路径段" in e for e in errors)


def test_cli_argv_posix_parent_traversal():
    rec = {**_cli_record(),
           "argv_or_rpc": ["java", "staging/../../evil/evil.jar"]}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    assert any("'..' 路径段" in e for e in errors)


def test_cli_argv_absolute_path_not_allowlisted():
    rec = {**_cli_record(),
           "argv_or_rpc": ["java", "-jar", "C:\\evil\\evil.jar",
                           "/etc/passwd"]}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    abs_errors = [e for e in errors if "绝对路径" in e]
    assert len(abs_errors) == 2


def test_cli_argv_shell_string_rejected():
    rec = {**_cli_record(),
           "argv_or_rpc": "java -jar freerouting.jar; rm -rf /"}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    assert any("shell" in e for e in errors)


def test_live_board_touched_rejected():
    rec = {**_cli_record(live_board_touched=True),
           "argv_or_rpc": list(CLI_ARGV_OK)}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    assert any("live_board_touched" in e for e in errors)


def test_write_scope_not_staging_rejected():
    rec = {**_cli_record(write_scope="none"), "argv_or_rpc": list(CLI_ARGV_OK)}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    assert any("write_scope" in e for e in errors)


def test_mcp_missing_endpoint():
    decl = dict(MCP_DECL, endpoint=None)
    rec = {**_mcp_record(), "rpc_method": "route/autoroute"}
    errors = external_backend.validate_policy(rec, decl)
    assert any("endpoint" in e for e in errors)


def test_mcp_missing_peer_identity():
    decl = dict(MCP_DECL, peer_identity=None)
    rec = {**_mcp_record(peer_identity=None),
           "rpc_method": "route/autoroute"}
    errors = external_backend.validate_policy(rec, decl)
    assert any("peer_identity" in e for e in errors)


def test_mcp_public_endpoint_rejected():
    decl = dict(MCP_DECL, endpoint="http://10.0.0.1:8765/mcp")
    rec = {**_mcp_record(), "rpc_method": "route/autoroute"}
    errors = external_backend.validate_policy(rec, decl)
    assert any("endpoint" in e for e in errors)


def test_mcp_endpoint_domain_prefix_spoof_rejected():
    # "http://localhost.evil.com" 以合法前缀开头但解析到公网域名 → 拒绝
    decl = dict(MCP_DECL, endpoint="http://localhost.evil.com/mcp")
    rec = {**_mcp_record(), "rpc_method": "route/autoroute"}
    errors = external_backend.validate_policy(rec, decl)
    assert any("endpoint" in e for e in errors)


def test_mcp_method_not_in_allowlist():
    rec = {**_mcp_record(), "rpc_method": "tools/execute_shell"}
    errors = external_backend.validate_policy(rec, MCP_DECL)
    assert any("method_allowlist" in e for e in errors)


def test_mcp_missing_rpc_method_fail_closed():
    errors = external_backend.validate_policy(_mcp_record(), MCP_DECL)
    assert any("rpc_method" in e for e in errors)


def test_mcp_network_deny_rejected():
    rec = {**_mcp_record(network_policy="deny"),
           "rpc_method": "route/autoroute"}
    errors = external_backend.validate_policy(rec, MCP_DECL)
    assert any("network_policy" in e for e in errors)


def test_backend_protocol_mismatch_rejected():
    rec = {**_mcp_record(), "rpc_method": "route/autoroute"}
    errors = external_backend.validate_policy(rec, CLI_DECL)
    assert any("backend 不一致" in e for e in errors)
    assert any("protocol 不一致" in e for e in errors)


# ---------------------------------------------------------------------------
# capability_claims
# ---------------------------------------------------------------------------

def test_capability_claims_real_toolchain_lock():
    lock = toolchain.load_lock()
    assert lock is not None, "仓库必须携带 toolchain_lock.json（只读引用）"
    claims = external_backend.capability_claims(lock)
    # 真实 lock：freerouting.optional=true / version=null → historical_only
    assert claims["freerouting_cli"] == "historical_only"
    assert claims["freerouting_mcp"] == "proposal_only"
    assert claims["kicad_cli"] == "locked"
    assert "derived_from" in claims
    assert claims["derived_from"]["freerouting_version"] is None


def test_capability_claims_note_forbids_transfer():
    claims = external_backend.capability_claims(
        {"freerouting": {"version": None, "optional": True}})
    assert "不得充当" in claims["claims_note"]


def test_capability_claims_synthetic_variants():
    claims = external_backend.capability_claims(
        {"freerouting": {"version": "2.3.0", "optional": True},
         "kicad_cli": {"version": None}})
    assert claims["freerouting_cli"] == "locked"
    assert claims["kicad_cli"] == "not_locked"
    assert claims["freerouting_mcp"] == "proposal_only"  # 与 lock 无关


# ---------------------------------------------------------------------------
# assess_output
# ---------------------------------------------------------------------------

def test_assess_output_all_pass():
    rec = _cli_record(exit_status=0)
    out = external_backend.assess_output(rec, _stages(*["pass"] * 5))
    assert out["pipeline_status"] == "verified_candidate"
    assert out["quarantine_staging"] is False
    assert out["failed_stages"] == []
    assert out["errors"] == []
    assert out["stage_order_valid"] is True


def test_assess_output_order_violation():
    rec = _cli_record(exit_status=0)
    stages = _stages("pass", "pass", "pass", "pass", "pass")
    stages[0], stages[1] = stages[1], stages[0]  # 乱序
    out = external_backend.assess_output(rec, stages)
    assert out["pipeline_status"] == "blocked"
    assert out["quarantine_staging"] is True
    assert out["stage_order_valid"] is False
    assert any("顺序违例" in e for e in out["errors"])


def test_assess_output_skipped_stage():
    rec = _cli_record(exit_status=0)
    stages = _stages("pass", "pass", "pass", "pass")  # 缺最后一级
    out = external_backend.assess_output(rec, stages)
    assert out["pipeline_status"] == "blocked"
    assert any("顺序违例" in e for e in out["errors"])


def test_assess_output_mid_fail_blocks_and_quarantines():
    rec = _cli_record(exit_status=0)
    stages = _stages("pass", "pass", "fail", "not_executed",
                     "not_executed")
    out = external_backend.assess_output(rec, stages)
    assert out["pipeline_status"] == "blocked"
    assert out["quarantine_staging"] is True
    assert out["failed_stages"] == [
        "drc_batch_severity_error", "drc_final_severity_all",
        "rollback_ledger_graph"]


def test_assess_output_missing_exit_status_blocks():
    # 无退出码见证 = crash_or_unknown：即便 stage 全 pass 也 blocked
    rec = _cli_record()
    out = external_backend.assess_output(rec, _stages(*["pass"] * 5))
    assert out["pipeline_status"] == "blocked"
    assert out["exit_classification"]["kind"] == "crash_or_unknown"


def test_assess_output_nonzero_exit_blocks():
    rec = _cli_record(exit_status=137)
    out = external_backend.assess_output(rec, _stages(*["pass"] * 5))
    assert out["pipeline_status"] == "blocked"
    assert out["quarantine_staging"] is True


def test_assess_output_engine_self_report_not_authoritative():
    rec = _cli_record(exit_status=0)
    out = external_backend.assess_output(rec, _stages(*["pass"] * 5))
    assert out["engine_self_report_included"] is False
    assert "authority" in out["engine_self_report_note"]


def test_assess_output_unknown_stage_rejected():
    rec = _cli_record(exit_status=0)
    stages = _stages(*["pass"] * 4) + [{"stage": "gui_eyeball",
                                        "status": "pass"}]
    out = external_backend.assess_output(rec, stages)
    assert out["pipeline_status"] == "blocked"
    assert any("固定 stage 集" in e for e in out["errors"])


# ---------------------------------------------------------------------------
# separate_evidence
# ---------------------------------------------------------------------------

def test_separate_evidence_partitions():
    cli = [_cli_record(execution_id="exec-cli-0001"),
           _cli_record(execution_id="exec-cli-0002")]
    mcp = [_mcp_record()]
    out = external_backend.separate_evidence(cli, mcp)
    assert len(out["cli_execution_hashes"]) == 2
    assert len(out["mcp_execution_hashes"]) == 1
    assert out["cli_record_count"] == 2 and out["mcp_record_count"] == 1
    assert not (set(out["cli_execution_hashes"])
                & set(out["mcp_execution_hashes"]))
    assert out["cross_backend_evidence_transfer"] is False
    assert out["errors"] == []


def test_separate_evidence_hash_is_canonical():
    rec = _cli_record()
    out = external_backend.separate_evidence([rec], [])
    assert out["cli_execution_hashes"] == [hashing.sha256_text(
        hashing.json_dumps(rec))]


def test_separate_evidence_misfiled_backend_flagged():
    # MCP record 误归入 CLI 侧 → 错误（fail-closed）
    out = external_backend.separate_evidence([_mcp_record()], [])
    assert out["errors"] and any("不属于" in e for e in out["errors"])


def test_separate_evidence_duplicate_in_both_sides_flagged():
    rec = _cli_record()
    out = external_backend.separate_evidence([rec], [rec])
    assert any("cross-backend transfer" in e for e in out["errors"])


# ---------------------------------------------------------------------------
# classify_exit
# ---------------------------------------------------------------------------

def test_classify_exit_variants():
    assert external_backend.classify_exit(
        None) == {"kind": "crash_or_unknown", "blocked": True,
                  "note": "无退出码见证：按崩溃/超时/未知处理（TD7 blocked）"}
    ok = external_backend.classify_exit(0)
    assert ok["kind"] == "ok" and ok["blocked"] is False
    nz = external_backend.classify_exit(2)
    assert nz["kind"] == "nonzero_exit" and nz["blocked"] is True
    # bool 是 int 子类：显式按非法见证处理（fail-closed）
    bad = external_backend.classify_exit(True)
    assert bad["kind"] == "crash_or_unknown" and bad["blocked"] is True
