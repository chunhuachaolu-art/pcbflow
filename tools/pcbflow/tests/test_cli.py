"""CLI exit-code 契约：compile/enum=blocked(2)，未实现命令=4。"""

import json
import os

import pytest

from pcbflow import cli, config, hashing, signoff_cmd

# ---- R28 板锚参数化（铜环案 R4 三步法；2026-09-12 重设计批） ---------------------
# 真实板 2026-09-11 被并行工作流 ripup1 改写（8029f5ff→dbfea089，铜环案裁定书
# 事实 C）；route_cmd 把实测板 sha 嵌进 route_plan（锚），冻结 out/revc-fc3 件
# 记旧板锚 → signoff 重放门 byte-exact 失败 → exit 1。冻结口径参数化（R4 三步
# 法②）：板输入钉仓库在案冻结快照板（裁定书 §3，三份快照逐字节相同），只读引用。
FROZEN_BOARD_SHA = \
    "8029f5ff6948f4abeda9cd04f78b6eaf481a462e97d3ce85ecbc024573111849"
FROZEN_BOARD_SNAPSHOT = os.path.join(
    config.PCBFLOW_ROOT, os.pardir, os.pardir, "design/coreboard/kicad/"
    "stm32h743-coreboard-revc/snapshots/live-ripup1-pre/"
    "stm32h743-coreboard-revc.kicad_pcb")
FC3_ROUTE_PLAN = "out/revc-fc3/route-plan.json"


def _fc3_disk_plan():
    with open(os.path.join(config.PCBFLOW_ROOT, FC3_ROUTE_PLAN),
              encoding="utf-8") as f:
        return json.load(f)


def _frozen_board_abs():
    """冻结夹具板绝对路径（fail-closed：sha 必须=登记锚=冻结 fc3 件所记锚）。"""
    p = os.path.normpath(FROZEN_BOARD_SNAPSHOT)
    assert hashing.sha256_file(p) == FROZEN_BOARD_SHA, "冻结夹具板自身漂移"
    assert _fc3_disk_plan()["zero_write"]["live_board_sha256"] == \
        FROZEN_BOARD_SHA, "冻结 fc3 件板锚与登记锚不符"
    return p


def _patch_replay_fc3_product(monkeypatch, product_path):
    """负对照注入通道：重放集 fc3 行指向 tmp 副本（冻结件本体零接触）。"""
    newset = tuple(
        dict(r, product=product_path) if r["product"] == FC3_ROUTE_PLAN else r
        for r in signoff_cmd.REPLAY_SET)
    monkeypatch.setattr(signoff_cmd, "REPLAY_SET", newset)


def test_compile_exit_blocked(capsys):
    rc = cli.main(["compile", "--select", "summary"])
    out = capsys.readouterr().out
    assert rc == 2  # 缺失源阻签核 → blocked（SPEC §0.2；歧义已全部裁决闭环）
    assert '"status": "blocked"' in out


def test_compile_emit_constraints(capsys):
    rc = cli.main(["compile", "--select", "constraints"])
    out = capsys.readouterr().out
    assert rc == 2
    assert '"schema_version": "1.1"' in out
    assert '"constraints"' in out


def test_enum_exit_blocked_and_payload(capsys):
    """① 草案：候选覆盖全 → 但结构权威确认待人工（确认点 #1）→ blocked。"""
    rc = cli.main(["enum", "--select", "summary"])
    out = capsys.readouterr().out
    assert rc == 2
    assert '"command": "enum"' in out
    assert '"status": "blocked"' in out
    assert "pending_user" in out


def test_stub_commands_not_implemented(capsys):
    """audit/co-place/route/residual 已分别于 FA3/FB1/FC1/FC2 实现；check/signoff
    已于 FD1 实现；其余未实现命令如实回 specified。"""
    for name in ("db",):
        rc = cli.main([name])
        out = capsys.readouterr().out
        assert rc == 4, name
        assert "specified_not_implemented" in out, name


def test_check_signoff_exit_ok_and_payload(capsys, monkeypatch):
    """FD1：⑤/⑥ 已实现 → exit 0；探针电池/包完整性入 summary。

    R28 板锚参数化：signoff 重放链的板输入钉冻结夹具板（8029f5ff=冻结 fc3
    件的构建输入板）→ exit 0 契约在冻结口径下原样成立（断言零改动）；
    live 板行为由 test_signoff_exit_live_board_anchor_state_registered
    另行登记（exit 契约随板锚状态参数化）。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    rc = cli.main(["check", "--select", "summary"])
    out = capsys.readouterr().out
    assert rc == 0
    assert '"command": "check"' in out
    assert '"battery_100": true' in out
    rc = cli.main(["signoff", "--select", "summary"])
    out = capsys.readouterr().out
    assert rc == 0
    assert '"command": "signoff"' in out
    assert '"production_signoff_ready": false' in out


def test_signoff_exit_live_board_anchor_state_registered(capsys):
    """R4 三步法③ live 板集成用例：signoff exit 契约随板锚状态参数化。

    live 板≠冻结锚（铜环案事实 C 漂移态）→ rc=EXIT_FAILED 且唯一非
    byte-exact 重放行恰={fc3 route-plan}（板锚行，别无其他失败源）；
    板回锚（live==冻结锚）→ rc=0（fail-closed，豁免不固化）。"""
    anchor = _fc3_disk_plan()["zero_write"]["live_board_sha256"]
    live = hashing.sha256_file(config.REVC_BOARD)
    rc = cli.main(["signoff", "--select", "summary"])
    out = capsys.readouterr().out
    if live == anchor:
        assert rc == 0
        return
    assert rc == config.EXIT_FAILED
    assert '"command": "signoff"' in out
    assert '"production_signoff_ready": false' in out
    replay = signoff_cmd.build_replay()
    assert {r["product"] for r in replay["regenerated"]
            if not r["byte_exact"]} == {FC3_ROUTE_PLAN}


def test_negative_control_non_anchor_replay_tamper_detected(
        monkeypatch, tmp_path):
    """负对照（R28 硬约束）：钉板全 byte-exact 前提下注入差异必须仍被检出。

    对照组：tmp 逐字节副本 → all_byte_exact=True（钉板口径自证）；
    注入①（非锚）：删副本 via_accounting 字段 → False 且失败行恰=该副本；
    注入②（锚值篡改，非登记配对）：zero_write.live_board_sha256 改伪值
    → 同样 False。冻结件本体零接触（tmp 副本注入，REPLAY_SET 定向改指）。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    copy_path = tmp_path / "route-plan.json"
    with open(os.path.join(config.PCBFLOW_ROOT, FC3_ROUTE_PLAN), "rb") as f:
        copy_path.write_bytes(f.read())
    _patch_replay_fc3_product(monkeypatch, str(copy_path))
    assert signoff_cmd.build_replay()["all_byte_exact"] is True
    obj = json.loads(copy_path.read_text(encoding="utf-8"))
    del obj["via_accounting"]  # 非锚差异注入
    copy_path.write_text(json.dumps(obj), encoding="utf-8")
    replay = signoff_cmd.build_replay()
    assert replay["all_byte_exact"] is False
    assert {r["product"] for r in replay["regenerated"]
            if not r["byte_exact"]} == {str(copy_path)}
    pristine = _fc3_disk_plan()
    pristine["zero_write"]["live_board_sha256"] = "ff" * 32  # 锚值篡改
    copy_path.write_text(json.dumps(pristine), encoding="utf-8")
    assert signoff_cmd.build_replay()["all_byte_exact"] is False


@pytest.mark.xfail(strict=True, reason="负对照：非锚差异（删 via_accounting）"
                                       "必须使重放门 fail（R28）")
def test_negative_control_replay_green_must_fire_on_tamper(
        monkeypatch, tmp_path):
    """以原始断言形态直证「注入非锚差异→仍然 fail」（红即预期，xfail）。"""
    monkeypatch.setattr(config, "REVC_BOARD", _frozen_board_abs())
    copy_path = tmp_path / "route-plan.json"
    obj = _fc3_disk_plan()
    del obj["via_accounting"]
    copy_path.write_text(json.dumps(obj), encoding="utf-8")
    _patch_replay_fc3_product(monkeypatch, str(copy_path))
    assert signoff_cmd.build_replay()["all_byte_exact"] is True


def test_route_exit_ok_and_payload(capsys):
    """FC1：route dry-run 已实现 → exit 0；planning_advisory、零写板。"""
    rc = cli.main(["route", "--select", "summary"])
    out = capsys.readouterr().out
    assert rc == 0
    assert '"command": "route"' in out
    assert '"status": "ok"' in out
    assert '"board_write": false' in out


def test_audit_exit_ok_and_payload(capsys):
    """FA3：audit 已实现 → exit 0（检查执行完成），verdict 独立（板上确有问题=red）。"""
    rc = cli.main(["audit", "--select", "summary"])
    out = capsys.readouterr().out
    assert rc == 0
    assert '"command": "audit"' in out
    assert '"status": "ok"' in out
    assert '"gates_pass": 3' in out


def test_coplace_exit_ok_and_payload(capsys):
    """FB1：co-place 已实现（冻结基线 sanity）→ exit 0；优化未执行如实记录。"""
    rc = cli.main(["co-place", "--select", "summary"])
    out = capsys.readouterr().out
    assert rc == 0
    assert '"command": "co-place"' in out
    assert '"status": "ok"' in out
    assert '"optimization_applied": false' in out
    assert "pending" in out or "批准" in out


def test_coplace_converter_roundtrip_proof(capsys):
    """转换器可重放：p3 CSV 导入副本→转换→与源文件 byte-exact（转换证明内载）。"""
    import hashlib
    rc = cli.main(["co-place", "--select", "conversion"])
    out = capsys.readouterr().out
    assert rc == 0
    src = open(config.AUDIT_P3_PLACEMENT_CSV, "rb").read()
    assert '"byte_exact_vs_source": true' in out
    assert hashlib.sha256(src).hexdigest() in out


from pcbflow import config  # noqa: E402  （供上方 round-trip 用；置尾避免顶部噪音）
