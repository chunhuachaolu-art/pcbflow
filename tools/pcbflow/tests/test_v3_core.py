"""TL-0 出口门 E2E：两个非 Rev-C smoke profile 可替换 manifest 运行 +
负向测试覆盖 stale/path/lease/transaction（SPEC-v3.0 §3 TL-0 机器门）。

依赖 cwd=pcbflow 根（既有测试约定，无 conftest）。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import artifact_graph, config, hashing, lease, manifest
from pcbflow import v3cli

PROFILES = os.path.join("profiles", "smoke-2l"), os.path.join(
    "profiles", "smoke-4l")


def _run(capsys, argv):
    rc = v3cli.main(argv)
    out = capsys.readouterr().out
    return rc, json.loads(out)


# ---------------------------------------------------------------------------
# 正向：两 profile 可替换 manifest 运行（TL-0 出口门主句）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prof", PROFILES)
def test_manifest_ok(capsys, prof):
    rc, d = _run(capsys, ["manifest", "--manifest",
                          os.path.join(prof, "manifest.json")])
    assert rc == 0 and d["status"] == "ok"
    assert d["errors"] == []
    assert len(d["manifest_sha256"]) == 64
    assert d["profile_sha256"]


@pytest.mark.parametrize("prof", PROFILES)
def test_context_ok_and_hash_bound(capsys, prof):
    rc, d = _run(capsys, ["context", "--manifest",
                          os.path.join(prof, "manifest.json")])
    assert rc == 0 and d["status"] == "ok"
    # null=缺失输入永不回退：absent 项 present=false 且 sha=null
    for ent in d["inputs"].values():
        if not ent["present"]:
            assert ent["sha256"] is None
    # toolchain lock 哈希绑定成功（两 profile 都指向工具根 lock）
    assert d["toolchain_lock_sha256"]
    assert d["profile_snapshot"]


@pytest.mark.parametrize("prof", PROFILES)
def test_graph_ok(capsys, prof):
    rc, d = _run(capsys, ["graph", "--graph",
                          os.path.join(prof, "graph.json")])
    assert rc == 0 and d["status"] == "ok"
    r = d["report"]
    assert r["acyclic"] and r["stale_nodes"] == []
    assert r["unresolved_inputs"] == []
    assert r["future_label_violations"] == []
    assert set(d["disk_status"].values()) == {"present"}


def test_graph_deterministic_sha(capsys):
    _, a = _run(capsys, ["graph", "--graph",
                         os.path.join("profiles", "smoke-2l", "graph.json")])
    _, b = _run(capsys, ["graph", "--graph",
                         os.path.join("profiles", "smoke-2l", "graph.json")])
    assert a["graph_sha256"] == b["graph_sha256"]


# ---------------------------------------------------------------------------
# 负向：path（绝对路径/越界逃逸）
# ---------------------------------------------------------------------------

def test_manifest_rejects_abs_path(tmp_path):
    mf = json.load(open(os.path.join("profiles", "smoke-2l", "manifest.json"),
                        encoding="utf-8"))
    mf["inputs"]["board"] = "E:/evil/board.kicad_pcb"
    errs = manifest.validate_manifest(mf)
    assert errs and any("inputs.board" in e for e in errs)


def test_resolve_blocks_escape(tmp_path):
    """path_base=manifest_dir 时逃出工具根的 '..' 路径必须被 resolve 拒绝。"""
    mf, _ = manifest.load_manifest(
        os.path.join("profiles", "smoke-2l", "manifest.json"))
    assert manifest.resolve_path(
        mf, os.path.abspath(os.path.join("profiles", "smoke-2l",
                                         "manifest.json")),
        "../../../../Windows/System32/config.sys") is None
    # 合法向上的 ../..（仍在工具根内）必须可用
    got = manifest.resolve_path(
        mf, os.path.abspath(os.path.join("profiles", "smoke-2l",
                                         "manifest.json")),
        "../../toolchain_lock.json")
    assert got and os.path.isfile(got)


def test_context_absent_input_no_fallback(capsys, tmp_path):
    mf = json.load(open(os.path.join("profiles", "smoke-2l", "manifest.json"),
                        encoding="utf-8"))
    mf["inputs"]["board"] = "inputs/nonexistent.kicad_pcb"
    p = tmp_path / "m.json"
    p.write_text(hashing.json_dumps(mf), encoding="utf-8")
    rc, d = _run(capsys, ["context", "--manifest", str(p)])
    assert rc == 0  # 缺输入不是命令失败
    ent = d["inputs"]["inputs.board"]
    assert ent["present"] is False and ent["sha256"] is None


# ---------------------------------------------------------------------------
# 负向：stale 传播（改输入 → 下游 stale → graph blocked）
# ---------------------------------------------------------------------------

def test_stale_propagation_via_cli(capsys, tmp_path):
    src = os.path.join("profiles", "smoke-2l")
    dst = tmp_path / "prof"
    dst.mkdir()
    for rel in ("manifest.json", "profile.json", "graph.json"):
        (dst / rel).write_text(
            open(os.path.join(src, rel), encoding="utf-8").read(),
            encoding="utf-8")
    inputs_dir = dst / "inputs"
    inputs_dir.mkdir()
    inputs_dir.joinpath("board.kicad_pcb").write_text(
        open(os.path.join(src, "inputs", "board.kicad_pcb"),
             encoding="utf-8").read(), encoding="utf-8")
    inputs_dir.joinpath("constraints.json").write_text(
        open(os.path.join(src, "inputs", "constraints.json"),
             encoding="utf-8").read(), encoding="utf-8")
    rc, d = _run(capsys, ["graph", "--graph", str(dst / "graph.json")])
    assert rc == 0
    # 篡改 constraints 后：节点哈希仍为旧声明 → disk 对账 stale
    inputs_dir.joinpath("constraints.json").write_text(
        '{"schema_version": "3.0", "tampered": true}', encoding="utf-8")
    spec = json.loads((dst / "graph.json").read_text(encoding="utf-8"))
    for n in spec["nodes"]:
        if n["artifact_id"] == "constraints":
            n["sha256"] = d["disk_status"] and _hash_of(
                os.path.join(src, "inputs", "constraints.json"))
    (dst / "graph.json").write_text(hashing.json_dumps(spec),
                                    encoding="utf-8")
    rc2, d2 = _run(capsys, ["graph", "--graph", str(dst / "graph.json")])
    assert rc2 == 2 and d2["status"] == "blocked"
    assert d2["disk_status"]["constraints"] == "stale"


def _hash_of(path):
    return hashing.sha256_file(path)


def test_stale_closure_by_expected_hash():
    a = artifact_graph.make_node("a", "x", sha256="0" * 64,
                                 stage_label="compile", revision="r1")
    b = artifact_graph.make_node("b", "y", inputs=["a"], stage_label="enum",
                                 revision="r1",
                                 expected_input_hashes={"a": "1" * 64})
    report = artifact_graph.validate_graph(
        artifact_graph.build_graph([a, b]))
    assert report["stale_nodes"] == ["b"]  # 期望 hash 不符 → 下游 stale


def test_cycle_detected():
    a = artifact_graph.make_node("a", "x", inputs=["c"], stage_label="enum",
                                 revision="r")
    b = artifact_graph.make_node("b", "y", inputs=["a"], stage_label="route",
                                 revision="r")
    c = artifact_graph.make_node("c", "z", inputs=["b"],
                                 stage_label="feedforward", revision="r")
    report = artifact_graph.validate_graph(
        artifact_graph.build_graph([a, b, c]))
    assert not report["acyclic"]
    assert set(report["cycle_nodes"]) == {"a", "b", "c"}


def test_future_label_violation():
    a = artifact_graph.make_node("a", "x", sha256="0" * 64,
                                 stage_label="signoff", revision="r")
    b = artifact_graph.make_node("b", "y", inputs=["a"], stage_label="enum",
                                 revision="r")
    report = artifact_graph.validate_graph(
        artifact_graph.build_graph([a, b]))
    assert report["future_label_violations"]


# ---------------------------------------------------------------------------
# 负向：lease（冲突/非持有者/journal 校验）
# ---------------------------------------------------------------------------

def test_lease_conflict_and_release_lifecycle(capsys, tmp_path):
    state_file = tmp_path / "lease.json"
    rc, d = _run(capsys, ["lease", "--state", "-", "--select", "acquire",
                          "--scope", "s/x", "--holder", "alice"])
    assert rc == 0
    state_file.write_text(hashing.json_dumps(d), encoding="utf-8")
    rc2, _ = _run(capsys, ["lease", "--state", str(state_file),
                           "--select", "acquire", "--scope", "s/x",
                           "--holder", "bob"])
    assert rc2 == config.EXIT_BLOCKED
    capsys.readouterr()
    rc3, _ = _run(capsys, ["lease", "--state", str(state_file),
                           "--select", "release", "--lease-id", "LEASE-0001",
                           "--holder", "bob"])
    assert rc3 == config.EXIT_BLOCKED  # 非持有者不可释放
    capsys.readouterr()
    rc4, _ = _run(capsys, ["lease", "--state", str(state_file),
                           "--select", "release", "--lease-id", "LEASE-0001",
                           "--holder", "alice"])
    assert rc4 == 0


def test_lease_journal_replay_recovers_state():
    s = lease.empty_state()
    s, rec, err = lease.acquire(s, "p/pf/out", "alice")
    assert err is None and rec["lease_id"] == "LEASE-0001"
    s, _, _ = lease.extend(s, "LEASE-0001", "alice")
    recovered = lease.replay_journal(s["journal"])
    assert lease.lease_status(recovered, "p/pf/out") == {
        "scope": "p/pf/out", "held": True, "holder": "alice",
        "lease_id": "LEASE-0001"}
    assert lease.verify_journal(s["journal"]) == []


def test_lease_journal_gap_detected():
    s = lease.empty_state()
    s, _, _ = lease.acquire(s, "a", "h")
    journal = [dict(e) for e in s["journal"]]
    journal[0]["entry_seq"] = 7  # 篡改序号
    assert lease.verify_journal(journal)


# ---------------------------------------------------------------------------
# 负向：transaction（DRC 未过不可 commit / 回滚后禁 commit / 零写见证）
# ---------------------------------------------------------------------------

def _open_txn():
    return lease.open_transaction(
        "TXN-1", "smoke-2l", "a" * 64,
        {"rows": 10, "segments": 0, "vias": 4, "footprints": 0})


def test_transaction_requires_drc_pass_before_commit():
    txn = _open_txn()
    lease.stage_batch(txn, "B1", "b" * 64, drc_batch_status="not_executed")
    with pytest.raises(ValueError, match="批 DRC"):
        lease.commit_transaction(txn, "c" * 64)


def test_transaction_empty_cannot_commit():
    with pytest.raises(ValueError, match="空事务"):
        lease.commit_transaction(_open_txn(), "c" * 64)


def test_transaction_rollback_then_no_staging_no_commit():
    txn = _open_txn()
    lease.rollback_transaction(txn, "drc_regression")
    assert txn["rollback"] == "executed"
    with pytest.raises(ValueError):
        lease.stage_batch(txn, "B2", "d" * 64)
    with pytest.raises(ValueError):
        lease.commit_transaction(txn, "c" * 64)


def test_transaction_live_board_zero_write_invariant():
    txn = _open_txn()
    lease.stage_batch(txn, "B1", "b" * 64, drc_batch_status="pass")
    lease.commit_transaction(txn, "c" * 64)
    txn["live_board_touched"] = True  # 模拟越权写
    assert any("live_board_touched" in e
               for e in lease.verify_transaction(txn))


# ---------------------------------------------------------------------------
# CLI 挂载边界：v3 命令面全部已接线（TL-0..TL-2）；未实现能力由各模块
# 的 not_implemented 状态如实报告（envelope 红线），不再有挂载桩。
# ---------------------------------------------------------------------------
