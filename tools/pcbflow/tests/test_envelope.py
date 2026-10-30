"""envelope 契约与核心产物禁区扫描（SPEC §2.1/§2.2）。"""

from pcbflow import envelope


def test_envelope_required_fields():
    env = envelope.build_envelope(
        command="compile", status="ok", verdict="pass",
        inputs=[{"path": "x", "sha256": "0" * 64, "role": "spec"}],
        artifacts=[{"path": "a.json", "sha256": "0" * 64, "role": "core"}],
    )
    for key in ("schema_version", "tool", "tool_version", "command", "status",
                "verdict", "deterministic", "determinism_claim", "inputs",
                "config_sha256", "spec_refs", "artifacts", "metrics",
                "diagnostics", "waivers", "solver", "run_metadata", "data"):
        assert key in env, key
    assert env["tool"] == "pcbflow"
    assert env["status"] == "ok" and env["verdict"] == "pass"


def test_envelope_rejects_bad_status():
    import pytest
    with pytest.raises(AssertionError):
        envelope.build_envelope(command="c", status="specified", verdict="pass",
                                inputs=[], artifacts=[])
    with pytest.raises(AssertionError):
        envelope.build_envelope(command="c", status="ok", verdict="specified",
                                inputs=[], artifacts=[])


def test_forbidden_core_scan_keys():
    hits = envelope.scan_forbidden_core_fields({"a": {"date": "2026-01-01"}})
    assert hits and hits[0][1] == "key"


def test_forbidden_core_scan_host_path():
    hits = envelope.scan_forbidden_core_fields(
        {"nested": [{"p": "C:\\Users\\x\\y\\z.json"}]})
    assert hits and hits[0][1] == "abs_path"


def test_forbidden_core_scan_clean():
    assert envelope.scan_forbidden_core_fields(
        {"ok": [1, 2, {"s": "relative/path.json"}]}) == []


def test_forbidden_core_scan_host_path_forward_slash():
    """SEC-B-01 守卫：正斜杠盘符路径必须拦截（旧正则漏检形态）。"""
    hits = envelope.scan_forbidden_core_fields(
        {"board": "C:/Users/x/y/z.kicad_pcb"})
    assert hits and hits[0][1] == "abs_path"
    hits2 = envelope.scan_forbidden_core_fields(
        {"p": "E:/ZCodeData/x", "q": "f:\\kicad\\bin"})
    assert len([h for h in hits2 if h[1] == "abs_path"]) == 2


def test_forbidden_core_scan_url_not_flagged():
    """URL 非主机绝对路径，不得误拦（https:// 的 s:/ 陷阱）。"""
    assert envelope.scan_forbidden_core_fields(
        {"schema": "https://json-schema.org/draft/2020-12/schema",
         "doc": "see https://example.com/x for details"}) == []
