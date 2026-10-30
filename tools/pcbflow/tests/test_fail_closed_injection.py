"""REPAIR-P2 W-2：fail-closed 故障注入测试（审计矩阵守卫）。

接口合同（REPAIR-P2-FAIL-CLOSED-AUDIT-TASKBOOK-2026-09-13 §3 W-2）：
- 参数化注入器，注入形态枚举 = 输入缺失 / None / 超时模拟（对纯函数门
  以"文件损坏/半截 JSON"等价表达编排侧中断）/ 依赖文件缺失 / 异常吞掉；
  对 W-1 矩阵（out/repair-p2/audit-matrix-r1.json）每个可注入门位断言
  输出 ∈ {blocked, UNKNOWN/not_executed/not_available, fail（证据在而不过）}，
  绝不允许 ok/pass/True。
- 每门至少一条负向断言：注入后若得到通过即 fail（写明门名与注入形态）。
- 注入一律在测试内构造（tmp_path / monkeypatch），不碰 out/、datasets/
  真实冻结件。

已修复门位（本批 W-3 行为变更，负向断言全部生效）：
fill_gate 缺台账（REPAIR-P2 W-3）、signoff 包缺节/structures 双缺
（SEC-A-01/02）、copper_loop DRC 缺 source（SEC-A-03）、check_cmd 台账
形状漂移（SEC-A-04）。

已知漏洞登记（SEC-A-05/06/07）已于 REPAIR-P3S W-A（2026-09-23）全修：
SEC-A-06（placement.csv 缺失/坏列 → (refs, not_available reason) 显式
上标）、SEC-A-07（net 表解析异常 → E4RevcError + 批 blocked，不回退
0.2mm）、SEC-A-05（zone 填充模型复核不可得 → unverifiable fail-closed，
守卫函数 _zone_fill_model_audit 抽出后本文件直接注入钉住）。原
xfail(strict) 登记已转正 must-pass（TestKnownHolesFixed）。
"""

import json
import os

import pytest

from pcbflow import (actual_ext, check_cmd, check_stage, copper_loop,
                     copper_patch, critic, corpus_convert_ext, disposition,
                     gate, health_projection, schemas, signoff_cmd)

cp = copper_patch

# ---------------------------------------------------------------- 门 1：gate
_EVAL = {"name": "t", "version": "1", "code_sha256": "a" * 64}
_GK = dict(gate_id="g1", gate_kind="training_loop", project_id="p",
           profile_id="pf", snapshot_revision="r1", predicate_version="v1",
           evaluator=dict(_EVAL))
_OK_INPUT = {"artifact_id": "a", "sha256": "b" * 64, "status": "present"}
_OK_PRED = {"id": "p1", "value": True, "evidence": "evidence-string"}


class TestGateEvaluateGate:
    """门=gate.evaluate_gate（缺证据闭门律 L7：blocked 严格优先于 fail）。"""

    @pytest.mark.parametrize("inject,expect_code", [
        ("输入缺失（status=missing）", "missing_input"),
        ("输入过期（status=stale）", "stale_input"),
        ("present 但 sha256=None（无绑定）", "missing_input"),
    ], ids=["missing-status", "stale-status", "no-hash"])
    def test_input_injection_blocks(self, inject, expect_code):
        bad = {"输入缺失（status=missing）": {**_OK_INPUT, "status": "missing"},
               "输入过期（status=stale）": {**_OK_INPUT, "status": "stale"},
               "present 但 sha256=None（无绑定）":
                   {"artifact_id": "a", "sha256": None,
                    "status": "present"}}[inject]
        rec = gate.evaluate_gate(inputs=[bad],
                                 required_predicates=[dict(_OK_PRED)], **_GK)
        assert rec["result"] == gate.RESULT_BLOCKED, inject
        assert expect_code in rec["failure_codes"], inject

    def test_predicate_without_evidence_blocks(self):
        rec = gate.evaluate_gate(
            inputs=[dict(_OK_INPUT)],
            required_predicates=[{"id": "p1", "value": True}], **_GK)
        assert rec["result"] == gate.RESULT_BLOCKED
        assert "evidence_missing:p1" in rec["failure_codes"]

    def test_predicate_false_is_fail_never_pass(self):
        rec = gate.evaluate_gate(
            inputs=[dict(_OK_INPUT)],
            required_predicates=[{"id": "p1", "value": False,
                                  "evidence": "e"}], **_GK)
        assert rec["result"] == gate.RESULT_FAIL

    def test_product_gate_without_graph_blocks(self):
        rec = gate.evaluate_gate(
            gate_kind="product", inputs=[dict(_OK_INPUT)],
            required_predicates=[dict(_OK_PRED)], **{k: v for k, v in _GK.items()
                                                     if k != "gate_kind"})
        assert rec["result"] == gate.RESULT_BLOCKED
        assert "graph_report_missing" in rec["failure_codes"]

    def test_negtive_no_injection_yields_pass(self):
        """负向对照（健康输入唯一可得 pass；任何注入形态不得 pass）。"""
        rec = gate.evaluate_gate(inputs=[dict(_OK_INPUT)],
                                 required_predicates=[dict(_OK_PRED)], **_GK)
        assert rec["result"] == gate.RESULT_PASS


class TestGateVerifyGateRecord:
    """门=gate.verify_gate_record（防人工直写 pass）。"""

    def test_human_pass_without_evidence_detected(self):
        rec = gate.evaluate_gate(inputs=[dict(_OK_INPUT)],
                                 required_predicates=[dict(_OK_PRED)], **_GK)
        rec["required_predicates"][0]["evidence"] = ""  # 人工抹掉证据
        errs = gate.verify_gate_record(rec)
        assert errs  # 负向：不得 errors==[]

    def test_missing_code_sha256_detected(self):
        rec = gate.evaluate_gate(inputs=[dict(_OK_INPUT)],
                                 required_predicates=[dict(_OK_PRED)], **_GK)
        rec["evaluator"]["code_sha256"] = "short"
        errs = gate.verify_gate_record(rec)
        assert errs

    def test_forged_pass_recompute_mismatch(self):
        rec = gate.evaluate_gate(
            inputs=[{"artifact_id": "a", "sha256": "b" * 64,
                     "status": "missing"}],  # 注入缺证据
            required_predicates=[dict(_OK_PRED)], **_GK)
        rec["result"] = gate.RESULT_PASS  # 人工直写 pass
        errs = gate.verify_gate_record(rec)
        assert any("重算不一致" in e for e in errs)


# ------------------------------------------------------- 门 2：critic 分流
class TestCriticTriageAndSemantics:
    """门=critic.triage / flags_empty_semantics / promotion_gate。"""

    @pytest.mark.parametrize("inject", [
        {"judge_gate_pass": False},
        {"required_checkers_executed": False},
        {"no_stale_or_unknown": False},
        {"whitelist_item": True},
    ], ids=["judge-fail", "checkers-not-executed", "stale-unknown",
            "whitelist"])
    def test_any_missing_condition_blocks_auto_route(self, inject):
        kw = dict(judge_gate_pass=True, required_checkers_executed=True,
                  no_stale_or_unknown=True, whitelist_item=False)
        kw.update(inject)
        d = critic.triage({}, **kw)
        assert d["eligible"] is False, inject  # 负向：不得 eligible=True
        assert d["status"] == "critic_auto_route_blocked"

    def test_run_missing_fields_blocks(self):
        d = critic.triage({}, judge_gate_pass=True,
                          required_checkers_executed=True,
                          no_stale_or_unknown=True, whitelist_item=False)
        assert d["eligible"] is False
        assert d["failed_conditions"]  # 缺字段全部显式列出

    def test_flags_empty_semantics_requires_preconditions(self):
        s = critic.flags_empty_semantics({})
        assert s["means_no_flags"] is False
        assert s["reason"]

    def test_promotion_gate_missing_fields_fail_closed(self):
        pg = critic.promotion_gate({})
        assert pg["promotion_state"] == "not_promoted"  # 负向：不得 candidate
        assert any(c.startswith("missing:") for c in pg["failed"])


# --------------------------------------------------- 门 3：disposition 豁免
class TestDispositionWaiverPolicy:
    """门=disposition.check_waiver_policy（无 policy 即无豁免权）。"""

    def _waive(self):
        return {"kind": "waive", "rationale_code": "R1", "approver_role":
                "eng", "fact_refs": ["CHK-1"], "waiver_policy_ref": "p",
                "expiry": "2027-01-01"}

    def test_empty_policy_rejects_all_waives(self):
        errs = disposition.check_waiver_policy(self._waive(), {})
        assert errs  # 负向：不得 []

    def test_none_policy_rejects_all_waives(self):
        errs = disposition.check_waiver_policy(self._waive(), None)
        assert errs

    def test_policy_missing_list_keys_reject_each_dimension(self):
        errs = disposition.check_waiver_policy(
            self._waive(), {"unrelated": 1})  # 三清单键全缺=各维度全拒
        assert len(errs) >= 3

    def test_non_waivable_fact_ref_rejected(self):
        policy = {"waivable_check_ids": ["CHK-2"],
                  "allowed_reason_codes": ["R1"],
                  "allowed_approver_roles": ["eng"]}
        errs = disposition.check_waiver_policy(self._waive(), policy)
        assert any("不可豁免" in e for e in errs)

    def test_valid_waive_in_policy_passes(self):
        policy = {"waivable_check_ids": ["CHK-1"],
                  "allowed_reason_codes": ["R1"],
                  "allowed_approver_roles": ["eng"]}
        assert disposition.check_waiver_policy(self._waive(), policy) == []


class TestDispositionNoGateWrite:
    """门=disposition.validate_no_gate_write（处置无门写权）。"""

    @pytest.mark.parametrize("payload", [
        {"gate": {"result": "pass"}},
        {"nested": {"production_signoff_ready": True}},
        [{"signoff_pass": True}],
    ], ids=["gate-key", "nested", "in-list"])
    def test_forbidden_keys_detected_recursively(self, payload):
        errs = disposition.validate_no_gate_write(payload)
        assert errs  # 负向：不得 []


# --------------------------------------------- 门 4：health_projection 信任
class TestHealthProjectionTrust:
    """门=health_projection.project_manual_queue（trust invalid → blocked）。"""

    def test_invalid_ledger_structure_blocks(self):
        rec = health_projection.project_manual_queue(
            "garbage-not-a-list", ledger_path="out/repair-p2/injection-ledger.json",
            ledger_sha256="a" * 64)
        assert rec["status"] == "blocked"
        assert rec["reason"].startswith("trust_invalid")

    def test_none_events_blocks(self):
        rec = health_projection.project_manual_queue(
            None, ledger_path="out/repair-p2/injection-ledger.json", ledger_sha256="a" * 64)
        assert rec["status"] == "blocked"

    def test_blocked_carries_no_value(self):
        """blocked/not_available 一律不携带 value/numerator 实值（键为
        占位 None=不冒充数值；_metric_base 预置 None，_finish_blocked
        不填值）。"""
        rec = health_projection.project_manual_queue(
            {"bad": "shape"}, ledger_path="out/repair-p2/injection-ledger.json",
            ledger_sha256="a" * 64)
        assert rec["status"] == "blocked"
        assert rec["value"] is None and rec["numerator"] is None


# -------------------------------------------------------- 门 5：schema 注册
class TestSchemasValidate:
    """门=schemas.validate（未知 schema 名 / 非法对象拒绝）。"""

    def test_unknown_schema_name_rejected(self):
        errs = schemas.validate("no_such_schema_v999", {})
        assert errs and "未知 schema 名" in errs[0]

    def test_gate_record_empty_object_rejected(self):
        errs = schemas.validate("gate_record", {})
        assert errs  # 负向：不得 []


# ------------------------------------------------- 门 6：check_stage DRC 摘要
class TestCheckStageSummarizeDrc:
    """门=check_stage.summarize_drc（缺键 ValueError，同仓 fail-closed 口径
    对照源；SEC-A-04 修复即仿此门）。"""

    @pytest.mark.parametrize("drc_all,drc_err", [
        ({"violations": []}, {"violations": [], "unconnected_items": []}),
        ({"unconnected_items": []},
         {"violations": [], "unconnected_items": []}),
        ("not-a-dict", {"violations": [], "unconnected_items": []}),
    ], ids=["drc-all-missing-unconn", "drc-all-missing-violations",
            "not-dict"])
    def test_missing_keys_raise(self, drc_all, drc_err):
        with pytest.raises(ValueError):
            check_stage.summarize_drc(drc_all, drc_err)

    def test_healthy_inputs_do_not_raise(self):
        s = check_stage.summarize_drc(
            {"violations": [], "unconnected_items": []},
            {"violations": [], "unconnected_items": []})
        assert s is not None


# ------------------------------ 门 7：check_cmd kicad 检查器（SEC-A-04 修复）
class TestCheckCmdKicadAuthoritative:
    """门=check_cmd.run_kicad_authoritative。

    形状门（REPAIR-P2 W-3 / SEC-A-04）：ledger 在但 violations/
    unconnected_items 缺/非法（kicad-cli 升级改字段名/文件被裁剪）⇒ 全部
    kicad 检查器 not_executed，不得 executed+pass。
    """

    def _write_ledger(self, fc2, *, final, baseline=None):
        d = fc2 / "drc"
        d.mkdir(parents=True, exist_ok=True)
        (d / "final-all.json").write_text(json.dumps(final), encoding="utf-8")
        if baseline is not None:
            (d / "baseline-all.json").write_text(
                json.dumps(baseline), encoding="utf-8")

    def _kicad_rows(self, fc2):
        return check_cmd.run_kicad_authoritative([], out_dir_rel=str(fc2))

    @pytest.mark.parametrize("final", [
        {},                                     # 两键全缺
        {"violations": []},                     # 缺 unconnected_items
        {"unconnected_items": []},              # 缺 violations
        {"violations": "oops", "unconnected_items": []},   # 键非列表
    ], ids=["both-missing", "no-unconn", "no-violations", "violations-str"])
    def test_final_shape_drift_not_executed(self, tmp_path, final):
        fc2 = tmp_path / "fc2"
        self._write_ledger(fc2, final=final, baseline={
            "violations": [], "unconnected_items": []})
        rows = self._kicad_rows(fc2)
        assert rows
        for r in rows:
            assert r["checker_status"] == "not_executed", r
            assert r["verdict"] is None, r            # 负向：不得 pass
            assert "形状漂移" in r["reason"]

    def test_baseline_shape_drift_not_executed(self, tmp_path):
        fc2 = tmp_path / "fc2"
        self._write_ledger(fc2, final={
            "violations": [], "unconnected_items": []},
            baseline={"violations": []})   # baseline 在场但缺 unconn 键
        rows = self._kicad_rows(fc2)
        assert all(r["checker_status"] == "not_executed" for r in rows)

    def test_ledger_file_missing_not_executed(self, tmp_path):
        rows = self._kicad_rows(tmp_path / "absent")
        assert rows and all(r["checker_status"] == "not_executed"
                            for r in rows)

    def test_ledger_corrupt_json_raises_never_passes(self, tmp_path):
        """超时/中断等价形态：半截 JSON（编排侧写盘中断）⇒ _load_json
        解析异常上抛（fail-closed 的硬拒绝形态——不产出任何 checker 行，
        绝无 executed+pass）。"""
        import json as _json
        fc2 = tmp_path / "fc2"
        (fc2 / "drc").mkdir(parents=True)
        (fc2 / "drc" / "final-all.json").write_text(
            '{"violations": [', encoding="utf-8")
        with pytest.raises(_json.JSONDecodeError):
            self._kicad_rows(fc2)

    def test_healthy_shape_executes(self, tmp_path):
        """对照：形状合法（violations=[] 零违例）⇒ executed+pass 合法。"""
        fc2 = tmp_path / "fc2-healthy"
        (fc2 / "drc").mkdir(parents=True)
        (fc2 / "drc" / "final-all.json").write_text(
            json.dumps({"violations": [], "unconnected_items": []}),
            encoding="utf-8")
        rows = check_cmd.run_kicad_authoritative([], out_dir_rel=str(fc2))
        assert rows and all(r["checker_status"] == "executed"
                            and r["verdict"] == "pass" for r in rows)


# --------------------- 门 8：signoff 签核包（SEC-A-01/02 修复，tmp 树注入）
def _signoff_tree(tmp_path, monkeypatch, *, structures_approved,
                  drop=()):
    """测试内构造 §12 签核包最小树（_p 重定向 → 全部路径进 tmp，
    零触碰真实 out/ 冻结件）；drop 制造缺件注入。"""

    def write(rel, payload):
        if rel in drop:
            return
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload), encoding="utf-8")

    # A3 权威 8 件
    a3 = "out/test-a3"
    for n in ("constraints.json", "coverage.json",
              "impedance_targets.json", "structures.json",
              "net-registry.json", "net-identity-map.json",
              "coverage-structures.json", "audit.json"):
        write("%s/%s" % (a3, n), {})
    # FF 计划（转正/未批由用例控制）
    snap = {"registry_snapshot_hash": "R"}
    if structures_approved:
        snap["structures_override_sha256"] = "0" * 64
    write("out/test-ff1/feedforward-plan.json",
          {"plan_id": "FF-T", "snapshot": snap})
    write("out/test-ff2/ff-consumption.json", {})
    write("out/test-fc1/route-consumption.json", {})
    # out_dir（check/waiver/replay 同目录）
    fd1 = "out/test-fd1"
    write("%s/check-report.json" % fd1, {"results": []})
    write("%s/ff-residuals.json" % fd1, {})
    write("%s/waiver-ledger.json" % fd1, {"approved": [], "candidates": []})
    write("%s/signoff-replay.json" % fd1, {})
    write("%s/impedance-targets.json" % fd1, {})
    # FC2 drc 台账 8 件 + ⑤ 消费件
    fc2 = "out/test-fc2"
    for n in ("baseline-all.json", "batch-1.json", "batch-2.json",
              "batch-3.json", "batch-4.json", "batch-5.json", "batch-6.json",
              "final-all.json"):
        write("%s/drc/%s" % (fc2, n),
              {"violations": [], "unconnected_items": []})
    write("%s/replay-plan.json" % fc2,
          {"definition": {"committed": 1, "denominator": 1, "planned_sat": 0},
           "execution_ledger": {"final_all": {"new_warning_detail": []}}})
    write("%s/residual-certs.json" % fc2, {"counts": {}})
    # 转正批准件（硬编码 out/revc-fd1/approvals/ 经 _p 重定向进 tmp）
    write("out/revc-fd1/approvals/structures.override.json", {})
    write("toolchain_lock.json", {})

    monkeypatch.setattr(signoff_cmd, "_p",
                        lambda rel: os.path.join(str(tmp_path), rel))
    for name, val in (("A3_DIR", a3), ("FF1_DIR", "out/test-ff1"),
                      ("FF2_DIR", "out/test-ff2"),
                      ("FC1_DIR", "out/test-fc1"), ("FC2_DIR", fc2)):
        monkeypatch.setattr(signoff_cmd, name, val)
    # 重放腿注入为固定 byte-exact（本门只审 §12 包节状态，不审重放）
    monkeypatch.setattr(
        signoff_cmd, "build_replay",
        lambda *a, **k: {"all_byte_exact": True, "regenerated": [],
                         "double_send_pins": []})

    def build():
        pkg = signoff_cmd.build_package(
            out_dir_rel=fd1, fc2_dir=fc2, ff_plan_dir="out/test-ff1",
            check_dir=fd1)
        env = signoff_cmd.build_envelope(
            out_dir_rel=fd1, fc2_dir=fc2, ff_plan_dir="out/test-ff1",
            check_dir=fd1)
        return pkg, env

    return build


class TestSignoffPackageCompleteness:
    """门=signoff build_package/build_envelope（SEC-A-01：缺任何文件型节
    ⇒ 该节 missing ⇒ package_complete=False；SEC-A-02：structures 双缺/
    override 缺失 ⇒ structures_approved=False）。"""

    def test_healthy_tree_package_complete(self, tmp_path, monkeypatch):
        build = _signoff_tree(tmp_path, monkeypatch,
                              structures_approved=True)
        pkg, env = build()
        assert pkg["sections"] and all(
            s["status"] != "missing" for s in pkg["sections"])
        g = env["data"]["gate"]
        assert g["package_complete"] is True
        assert g["structures_approved"] is True

    @pytest.mark.parametrize("drop_file,section", [
        ("out/test-fc2/drc/final-all.json", "ERC/DRC raw reports and diffs"),
        ("out/test-a3/constraints.json", "constraints final snapshot"),
        ("out/test-fd1/signoff-replay.json", "replay result"),
        ("out/test-a3/coverage-structures.json", "coverage"),
        ("toolchain_lock.json", "toolchain lock and hashes"),
        ("out/test-a3/audit.json", "consumer evidence"),
    ], ids=["drc-final", "constraints", "replay", "coverage-structures",
            "toolchain-lock", "audit"])
    def test_any_missing_file_breaks_package(self, tmp_path, monkeypatch,
                                             drop_file, section):
        build = _signoff_tree(tmp_path, monkeypatch,
                              structures_approved=True, drop=(drop_file,))
        pkg, env = build()
        items = {s["item"]: s for s in pkg["sections"]}
        assert items[section]["status"] == "missing", drop_file
        g = env["data"]["gate"]
        assert g["package_complete"] is False, drop_file   # 负向：不得 True
        assert section in g["missing_sections"]
        assert g["dry_run_package_ok"] is False
        assert env["verdict"] != "pass"                    # 负向：不得 pass

    def test_partial_drc_ledger_is_missing_not_present(self, tmp_path,
                                                       monkeypatch):
        """SEC-A-01 加重项证伪：8 件 drc 台账在场 7 件（部分在场），
        旧版 any-present 掩盖缺件 ⇒ 现须 missing。"""
        build = _signoff_tree(
            tmp_path, monkeypatch, structures_approved=True,
            drop=("out/test-fc2/drc/batch-3.json",))
        pkg, env = build()
        items = {s["item"]: s for s in pkg["sections"]}
        assert items["ERC/DRC raw reports and diffs"]["status"] == "missing"
        assert env["data"]["gate"]["package_complete"] is False

    def test_override_missing_kills_structures_approved(self, tmp_path,
                                                        monkeypatch):
        """SEC-A-02 证伪：转正计划 + override.json 缺失 ⇒ 旧行
        status=present 掩盖 ⇒ 现 missing 且 structures_approved=False。"""
        build = _signoff_tree(
            tmp_path, monkeypatch, structures_approved=True,
            drop=("out/revc-fd1/approvals/structures.override.json",))
        pkg, env = build()
        items = {s["item"]: s for s in pkg["sections"]}
        assert items["structures snapshot"]["status"] == "missing"
        assert env["data"]["gate"]["structures_approved"] is False

    def test_unapproved_plan_structures_not_approved(self, tmp_path,
                                                     monkeypatch):
        build = _signoff_tree(tmp_path, monkeypatch,
                              structures_approved=False)
        pkg, env = build()
        items = {s["item"]: s for s in pkg["sections"]}
        assert items["structures snapshot"]["status"] == "present_unapproved"
        assert env["data"]["gate"]["structures_approved"] is False


# --------------------------- 门 9：copper_patch.fill_gate（W-3 修复守卫）
class TestFillGateFailClosed:
    """门=copper_patch.fill_gate（守卫双条之一：缺 ledger 必拒；证伪旧
    fail-open 路径——铜环裁决 2026-09-11 §8 P1-2）。"""

    @pytest.mark.parametrize("ledger", [
        None,                                   # 完全无台账
        {"events": []},                         # 台账无 patch_ledger
        {"patch_ledger": {"zone_fill": []}},    # patch_ledger 无 summary
        {"patch_ledger": {"zone_fill_summary": "corrupt"}},  # summary 非 dict
    ], ids=["none", "no-patch-ledger", "no-summary", "summary-not-dict"])
    def test_missing_ledger_refused(self, ledger):
        g = cp.fill_gate({"patch": {"staging_sha256": "a" * 64}},
                         ledger=ledger)
        assert g["ok"] is False, ledger          # 负向：不得 ok=True
        assert g["reason_code"] == "ledger_missing"
        assert g["status_label"] == "unverifiable"

    def test_ledger_via_record_fallback_still_required(self):
        """record 内联兜底也无 summary ⇒ 同判 fail-closed。"""
        g = cp.fill_gate({"patch": {"staging_sha256": "a" * 64}})
        assert g["ok"] is False and g["reason_code"] == "ledger_missing"

    def test_explicit_override_false_passes(self):
        """显式覆盖口：调用方显式担责断言未触及 zone ⇒ 放行。"""
        g = cp.fill_gate({"patch": {"staging_sha256": "a" * 64}},
                         required_override=False)
        assert g["ok"] is True and g["required"] is False

    def test_explicit_override_true_requires_evidence(self):
        g = cp.fill_gate({"patch": {"staging_sha256": "a" * 64}},
                         required_override=True)
        assert g["ok"] is False and g["required"] is True

    def test_valid_ledger_no_zone_ops_passes(self):
        """守卫双条之二（纯函数腿）：合法 ledger 且无 zone 编辑 ⇒ 放行，
        在树路径零回归。"""
        g = cp.fill_gate(
            {"patch": {"staging_sha256": "a" * 64}},
            ledger={"patch_ledger": {
                "zone_fill": [],
                "zone_fill_summary": cp._zone_fill_summary([])}})
        assert g["ok"] is True and g["required"] is False


class TestCopperLoopFillGateRefusalIntegration:
    """守卫双条之二（集成腿）：copper_loop._fill_gate_refusal 在树调用方
    行为零回归 + 台账文件级缺/坏注入。"""

    def _revision(self, tmp_path, ledger):
        rd = tmp_path / "rev"
        rd.mkdir()
        if ledger is not None:
            (rd / "ledger.json").write_text(
                json.dumps(ledger), encoding="utf-8")
        return str(rd), {"revision_id": "r1", "base_label": "b",
                         "rev": 1, "status": "awaiting_drc",
                         "patch": {"staging_sha256": "a" * 64}}

    def test_valid_ledger_no_zone_ops_returns_none(self, tmp_path):
        """合法台账（patch 阶段写入、无 zone 编辑）⇒ 放行（None）。"""
        rd, rec = self._revision(
            tmp_path, {"schema": copper_loop.LEDGER_SCHEMA,
                       "events": [],
                       "patch_ledger": {"zone_fill": [],
                                        "zone_fill_summary":
                                        cp._zone_fill_summary([])}})
        assert copper_loop._fill_gate_refusal(rec, rd, "accept") is None

    def test_ledger_file_absent_now_refuses(self, tmp_path):
        """台账文件缺失（patch 阶段未落账）⇒ 旧版空台账放行 ⇒ 现拒绝
        （REPAIR-P2 W-3 行为变更）。"""
        rd, rec = self._revision(tmp_path, None)
        res = copper_loop._fill_gate_refusal(rec, rd, "accept")
        assert res is not None and res["ok"] is False
        assert res["status"] == copper_loop.STATUS_BLOCKED

    def test_ledger_unparseable_blocks(self, tmp_path):
        rd = tmp_path / "rev"
        rd.mkdir()
        (rd / "ledger.json").write_text("{broken",
                                              encoding="utf-8")
        res = copper_loop._fill_gate_refusal(
            {"revision_id": "r1", "base_label": "b", "rev": 1,
             "status": "awaiting_drc",
             "patch": {"staging_sha256": "a" * 64}}, str(rd), "accept")
        assert res["status"] == copper_loop.STATUS_BLOCKED
        assert res["ok"] is False


# --------------------- 门 10：copper_loop DRC 报告校验（SEC-A-03 修复）
class TestCopperLoopDrcReportBinding:
    """门=copper_loop._validate_drc_report（板绑定证据缺失即拒）。"""

    def _report(self, **over):
        r = {"$schema": "x-drc-1", "violations": [], "kicad_version": "9.0.1",
             "source": "board-x.kicad_pcb"}
        r.update(over)
        return r

    def _lock(self):
        return {"kicad_cli": {"version": "9.0.1"}}

    @pytest.mark.parametrize("src", [None, "", 123, ["a"]],
                             ids=["none", "empty", "int", "list"])
    def test_missing_source_refused(self, src):
        errs = copper_loop._validate_drc_report(
            self._report(source=src), "board-x.kicad_pcb", self._lock())
        assert any(e.startswith("drc_report_source_missing")
                   for e in errs)   # 负向：不得空 errs

    def test_source_absent_key_refused(self):
        r = self._report()
        del r["source"]
        errs = copper_loop._validate_drc_report(
            r, "board-x.kicad_pcb", self._lock())
        assert any(e.startswith("drc_report_source_missing") for e in errs)

    def test_source_mismatch_refused(self):
        errs = copper_loop._validate_drc_report(
            self._report(source="other-board.kicad_pcb"),
            "board-x.kicad_pcb", self._lock())
        assert any(e.startswith("drc_report_source_mismatch") for e in errs)

    def test_lock_missing_refused(self):
        errs = copper_loop._validate_drc_report(
            self._report(), "board-x.kicad_pcb", None)
        assert any(e.startswith("toolchain_lock_missing") for e in errs)

    def test_healthy_report_clean(self):
        assert copper_loop._validate_drc_report(
            self._report(), "board-x.kicad_pcb", self._lock()) == []


# ------------------------------------------------ 门 11：语料版本门
class TestVersionGates:
    """门=corpus_convert_ext.detect_binding / actual_ext._check_version_gate
    （未知格式 fail-closed，不猜绑定档）。"""

    def test_detect_binding_missing_version_rejected(self):
        with pytest.raises(corpus_convert_ext.CorpusExtError):
            corpus_convert_ext.detect_binding("(kicad_pcb)")

    def test_detect_binding_unknown_version_rejected(self):
        with pytest.raises(corpus_convert_ext.CorpusExtError):
            corpus_convert_ext.detect_binding(
                '(kicad_pcb (version "19990101"))')

    def test_detect_binding_known_version_routes(self):
        assert corpus_convert_ext.detect_binding(
            '(kicad_pcb (version "20171130"))') == "net_id_bound"

    def test_actual_version_gate_unknown_rejected(self):
        with pytest.raises(actual_ext.ActualExtError):
            actual_ext._check_version_gate("19990101", "net_id_bound")

    def test_actual_binding_invalid_rejected(self):
        with pytest.raises(actual_ext.ActualExtError):
            actual_ext._check_binding("no_such_binding")

    def test_actual_version_gate_known_passes(self):
        assert actual_ext._check_version_gate(
            "20171130", "net_id_bound") == "20171130"


# ---------------- 已知漏洞修复验证（REPAIR-P3S W-A，2026-09-23 转正）
class TestKnownHolesFixed:
    """SEC-A-06/07：原 xfail(strict) 登记已修复（REPAIR-P3S W-A），转
    must-pass。再退化（静默空集/静默回退 0.2mm）即本类失败。"""

    def test_sec_a06_placement_missing_explicit_not_available(self):
        """SEC-A-06 修复：placement.csv 缺失 → (空集, not_available 原因)，
        不再静默空集（检查空转有标注）。"""
        from pcbflow import audit_cmd
        refs, reason = audit_cmd._analog_zone_refs(
            path="Z:/definitely/absent.csv")
        assert refs == set()
        assert reason is not None and reason.startswith("not_available")

    def test_sec_a06_placement_bad_columns_explicit_not_available(
            self, tmp_path):
        """SEC-A-06 修复（坏列形态）：csv 在场但缺 ref 列 → (空集,
        not_available)，不再吞 KeyError 静默空集。"""
        import csv as _csv
        from pcbflow import audit_cmd
        p = tmp_path / "placement-bad-columns.csv"
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=["zone"])  # 故意缺 ref 列
            w.writeheader()
            w.writerow({"zone": "ANLG"})
        refs, reason = audit_cmd._analog_zone_refs(path=str(p))
        assert refs == set()
        assert reason is not None and reason.startswith("not_available")

    def test_sec_a07_net_table_failure_no_default_fallback(self):
        """SEC-A-07 修复：net 表解析异常 → 记 default_clearance_error 返回
        None（不回退 0.2mm 放行方向）。"""
        from pcbflow.v4_1 import e4revc

        class _Boom:
            def resolve(self, *_a, **_k):
                raise RuntimeError("net table corrupt")

        obj = e4revc.RevCProjection.__new__(e4revc.RevCProjection)
        obj.net_table = _Boom()
        val = obj._default_clearance()
        assert val is None
        assert getattr(obj, "default_clearance_error", "")

    def test_sec_a07_projection_construction_refuses_bad_table(self):
        """SEC-A-07 修复（构造拒绝路径）：Default clearance 不可解析时
        RevCProjection 构造显式 E4RevcError，不产出回退 0.2 的投影。"""
        from pcbflow.v4_1 import e4revc
        import test_v4_1_e4_revc

        class _Boom:
            def resolve(self, *_a, **_k):
                raise RuntimeError("net table corrupt")

        with pytest.raises(e4revc.E4RevcError):
            e4revc.RevCProjection(test_v4_1_e4_revc._mini_board(),
                                  net_table=_Boom())


# ------------- SEC-A-05 守卫（REPAIR-P3S W-A：3d 段抽出后直接注入钉住）
class TestSecA05ZoneFillModelAudit:
    """SEC-A-05 修复守卫：_zone_fill_model_audit 对复核不可得的 modify
    记录 fail-closed（unverifiable），聚合缺席键不再视 True。"""

    @staticmethod
    def _model(zones):
        return {"zones": [dict(z) for z in zones]}

    @staticmethod
    def _zone(zid="z-1", points=5, sha="ab"):
        return {"uuid": zid, "fill_points": points, "fill_sha256": sha}

    def test_modify_identical_passes_and_records_evidence(self):
        rec = {"op": "modify", "zone_id": "z-1"}
        assert cp._zone_fill_model_audit(
            self._model([self._zone()]), self._model([self._zone()]),
            [rec]) is None
        assert rec["copper_model_fill_identical"] is True
        assert rec["copper_model_fill_before"]["fill_points"] == 5
        assert "copper_model_fill_unverifiable" not in rec

    def test_modify_without_zone_id_blocked_unverifiable(self):
        """核心钉（SEC-A-05 缺口形态）：无 zone_id 的 modify 记录不再被
        continue 静默放行——显式置 False + unverifiable 上标 + guard 失败。"""
        rec = {"op": "modify", "zone_id": None}
        reason = cp._zone_fill_model_audit(
            self._model([self._zone()]), self._model([self._zone()]), [rec])
        assert reason is not None and "不可复核" in reason
        assert rec["copper_model_fill_identical"] is False
        assert rec["copper_model_fill_unverifiable"] is True

    def test_modify_zone_missing_from_model_blocked_unverifiable(self):
        rec = {"op": "modify", "zone_id": "z-1"}
        reason = cp._zone_fill_model_audit(
            self._model([self._zone()]), self._model([]), [rec])
        assert reason is not None and "不可复核" in reason
        assert rec["copper_model_fill_identical"] is False

    def test_modify_fingerprint_changed_blocked(self):
        rec = {"op": "modify", "zone_id": "z-1"}
        reason = cp._zone_fill_model_audit(
            self._model([self._zone()]),
            self._model([self._zone(points=9, sha="cd")]), [rec])
        assert reason is not None and "被改动" in reason
        assert rec["copper_model_fill_identical"] is False

    def test_add_without_zone_id_not_flagged(self):
        """add 记录不参与 identical 聚合（原语义保持：只钉 modify 缺口）。"""
        rec = {"op": "add", "zone_id": None}
        assert cp._zone_fill_model_audit(
            self._model([]), self._model([]), [rec]) is None

    def test_empty_records_pass(self):
        assert cp._zone_fill_model_audit({"zones": []}, {"zones": []},
                                         []) is None


# ------------- route_one C1 端点闭合防御断言（REPAIR-P3S W-B）
class TestRouteOneEndpointClosure:
    """_endpoint_closure_fail 单测：合法路径零误伤（返回 None），端点层
    违例/断链/坐标不符 → 违例细目（调用侧 ok=False 诚实失败）。"""

    @staticmethod
    def _plan(ok=True, segments=(), vias=()):
        class _P:
            pass
        p = _P()
        p.ok = ok
        p.segments = list(segments)
        p.vias = list(vias)
        return p

    def test_legal_witness_shaped_route_passes(self):
        """witness 同形合法路径（a 起 L6 → via → b 止 L0，层均在允许集）：
        断言零误伤。"""
        from pcbflow import route_grid as rg
        segs = [(6, 23.3941, 32.3995, 23.0, 34.35),
                (0, 23.0, 34.35, 17.5343, 34.1198)]
        assert rg._endpoint_closure_fail(
            self._plan(segments=segs, vias=[(23.0, 34.35)]),
            23.3941, 32.3995, [6, 0], 17.5343, 34.1198, [6, 0]) is None

    def test_via_at_endpoint_on_other_layer_passes(self):
        """合法形态（消费方实证，test_fb1_ripup_accounting 同形）：端点处
        打 via 下内层走线——via 提供层过渡，端点允许集仍闭合。"""
        from pcbflow import route_grid as rg
        segs = [(6, 5.0, 5.0, 9.0, 5.0)]
        assert rg._endpoint_closure_fail(
            self._plan(segments=segs, vias=[(5.0, 5.0), (9.0, 5.0)]),
            5.0, 5.0, [0], 9.0, 5.0, [0]) is None

    def test_endpoint_layer_outside_allowed_no_via_flagged(self):
        """VERIFY-1 根因主假设形态：端点坐标命中但层 ∉ 允许集且无 via
        过渡（a/b 两端各验一条）。"""
        from pcbflow import route_grid as rg
        segs = [(0, 0.0, 0.0, 1.0, 0.0), (4, 1.0, 0.0, 2.0, 0.0)]
        d = rg._endpoint_closure_fail(
            self._plan(segments=segs), 0.0, 0.0, [0, 4], 2.0, 0.0, [0])
        assert d and any("b 端" in s for s in d)
        segs2 = [(4, 0.0, 0.0, 1.0, 0.0), (0, 1.0, 0.0, 2.0, 0.0)]
        d2 = rg._endpoint_closure_fail(
            self._plan(segments=segs2), 0.0, 0.0, [0], 2.0, 0.0, [0, 4])
        assert d2 and any("a 端" in s for s in d2)

    def test_broken_chain_two_components_flagged(self):
        """分量口径防御：两段同层互不相连且无 via —— 假闭合被抓。"""
        from pcbflow import route_grid as rg
        segs = [(0, 0.0, 0.0, 1.0, 0.0), (0, 5.0, 5.0, 6.0, 5.0)]
        d = rg._endpoint_closure_fail(
            self._plan(segments=segs), 0.0, 0.0, [0], 6.0, 5.0, [0])
        assert d and any("连通分量" in s for s in d)

    def test_endpoint_coordinate_mismatch_flagged(self):
        from pcbflow import route_grid as rg
        segs = [(0, 0.5, 0.0, 1.0, 0.0)]
        d = rg._endpoint_closure_fail(
            self._plan(segments=segs), 0.0, 0.0, [0], 1.0, 0.0, [0])
        assert d and any("a 端" in s for s in d)

    def test_empty_path_distinct_endpoints_flagged(self):
        from pcbflow import route_grid as rg
        d = rg._endpoint_closure_fail(
            self._plan(segments=[]), 0.0, 0.0, [0], 1.0, 1.0, [0])
        assert d and any("空路径" in s for s in d)

    def test_failed_plan_skipped(self):
        """已失败 plan 不做终态断言（输出保持旧形态，零漂移）。"""
        from pcbflow import route_grid as rg
        assert rg._endpoint_closure_fail(
            self._plan(ok=False), 0.0, 0.0, [0], 1.0, 1.0, [0]) is None
