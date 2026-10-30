"""R22 收口包 B 测试（s78_calibration_r22_devrecord /
round22-dev-record.json）——轮次开发记录生成器（s75 底稿同构）：
同指引重复轮（收敛归因；r16 先例；第二十二轮）：判读指引=
observation-guidance-r19.md 字节复用（8633bda5 本体零字节不动、零新建
指引文件；§6 前缀差异=R19T-/R19B- 落盘原文 vs R22T/R22B 派发层覆盖、
r16 先例在案）+渲染零变更=renders-r14b 四图字节复用+GT/阈值/协议零变
更；changed_variables=0（唯一操作=reader 实例群重抽 12 派次）；【跳号
声明】r21=axis-plan 冻结件预留的 R21 全组合条件位（early_stop_rule.
strong_single_axis_shortcut 未触发、槽位永久留空、dev-r20 已登记「R21
不做」、r22 与该位无涉）。预注册假设（r20-dev-record-candidate-r19-
config-same-guidance-repeat）复制性三分判据轮后裁决=regressed（字母口
径，唯一正式裁决，轮后不改写）：(g) 支命中=regressed_guards（G2=top
几何门面积比出局条目 R19=0→R22=2 破坏；支序先行）——而 M1=0.390244
（16/41）落复制带 [0.361538, 0.561538] 内（甚至优于 r19 的 0.461538）、
contact=2≤7、G1=bottom courtyard 非弃权 0/0/0 维持——分岔如实登记
（g2_bifurcation_record 单列，照 r20 g1_bifurcation_record 先例）：冻
结支文把 G1/G2 破坏与「r19 量级不可复制」捆绑为同一结论文本、本轮 M1
分量与该解释相悖——两账分列：字母=regressed 与 M1 复制事实=机制观察，
不合并、不改写（反事实构造：守门维持⇒replicated）；G2 破坏 2 条出局
条目逐条摘录（R22T-002 16.406371+R22T-013 16.369542，均 silk_
readability 负责任报告、现象=报告框过大形态）。(g) 支 M1 ≥0.771429 未
命中；(d) 不落。机制观察单列：M4 双样本（r19=0.211111 未过 0.20 门
[差 0.011111 在案] vs r22=0.104545 过门=第二次样本过门；不进字母、不
合并分布、不挑优）；rubric 三族 contact 2/existence_blackdot 4/
existence_other 12 对照 r19（4/4/14）与 r20（2/6/10）——黑点 4=与
r19 持平（guidance-r19 无 §5B 节、bottom 黑点仍存在性弃权[bottom-i2
两板]）；援引计数对照 r19 基线（r19=旗级「(iii-a)」6 旗+「分支(」2 旗、
notes 级 10/12 在案；r22=旗级全 0、notes 级 §5B=0/12、(iii-a)=6/12）；
落支=间隙 6+侵入 1+残余弃权 2。GT：union=agreement=1/13
（GT-REVC-P1-L1SHORT，prep1-top-i2 R22T-007+prep1-top-i3 R22T-017 双实
例命中=agreement 口径自 r12 引入以来首次计入——r12 以来第二次逐实例命
中、首次两实例一致命中，如实登记）；通道门 几何 2/类别 4/视角 1 对照
r19（0/2/0）与 r20（0/0/0）。联合门 not_met、连续=0、in_calibrated_
range 恒 False 照常。三轴实验总收束位：comparison_rule 排序不变
（r19_axis3 第一）；r22 不入排序（G2 破坏）；轴3 收益的归因状态=「M1
量级在新鲜实例群复现（机制方向支持）但守门字面降级（预注册字母=
regressed）」两账并列、不合并、不改写；发展域证据不得冒充留出。下一候
选建议三选项（由用户拍板、本包不预写决策）：(a) 接受发展域现状收束训
练环+留出集时机用户判断；(b) G2 两条出局条目机制归因（报告框 hygiene
核实→派发层框收敛指引、须新预注册轮）；(c) 再一轮同指引重复轮（三样
本）。

覆盖（14 测试，只读 out/、零子进程/零网络；s78 幂等重跑例外=护栏语义
在案、字节零改动）：
- 防覆盖守卫：overwrite_guard 三态+_commit 写入/幂等/不同字节 FAIL；
- canonical 确定性（盘上件=同参重建 byte-exact）+轮次身份+is_gate
  False；
- 引用件哈希清单 7 件（run-r22=80a12c05/prep-r22=63346ee6/
  guidance-r19=8633bda5/run-r19=e5755a11/dev-r19=0e2fdd69/dev-r20=
  80e3e9e2/run-r20=6573a59a 盘上实测）+预注册链冻结工件逐件实测；
- 字母裁决=regressed 落支与判据布尔（M1 带内=True、contact≤7=True、
  G2 破坏=True、M1 ≥0.771429=False）与预注册判据摘录逐字一致；
- 复制性结论逻辑纯函数构造（G2 维持时=replicated；regressed_guards/
  regressed_m1/drifted/带端点/contact 边界）；
- M 元组与 run 一致（构造对照：六行并列、M1 交叉相乘带内、M4 极差、
  M3=rubric 计数、显著收益降幅、r19 参照元组）；
- g2_bifurcation_record 字段存在且含双账分列（letter_vs_fact/反事实
  构造/2 条出局条目逐条摘录与 run 通道归因逐一相等）；
- 三轴实验总收束位（排序不变=r19 第一、r22/r20 资格门剔除、归因状态
  两账并列、发展域不得冒充留出）；
- 下一候选建议（三选项/用户拍板/预注册要求）；
- GT agreement 里程碑+双口径 1/13+联合门+in_calibrated_range 恒
  False+通道门 2/4/1 对照；
- 机制观察（M4 双样本过门事实/三族对照/援引对照 r19 基线/top 分型/
  黑点）；
- 轮次身份声明（changed_variables=0/§6 前缀差异/唯一操作）+跳号声明
  （r21 冻结槽位原文）；
- 趋势行 r5–r22（dev-r20 冻结转录+r22 实测行）；
- honest 结论/下一目标关键锚+s78 幂等重跑+s77 分包边界。
"""

import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing  # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

ROUND_ID = "2026-09-09-r22"
ROUND_LABEL = "r22"
DECLARED_DATE = "2026-09-09"

DEV_PATH = os.path.join(CAL_DIR, "round22-dev-record.json")


def _load_s78():
    path = os.path.join(REPO, "scripts", "s78_calibration_r22_devrecord.py")
    spec = importlib.util.spec_from_file_location("s78_calibration_r22_dev",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S78 = _load_s78()


@pytest.fixture(scope="module")
def dev():
    """round22-dev-record 内存重建（纯函数；只读输入、零写盘）。"""
    return S78.build_dev_record()


@pytest.fixture(scope="module")
def run_doc():
    """run-r22 盘上件装载（只读）。"""
    return S78._json_load(S78.REL_RUN_R22)


# ---------------------------------------------------------------------------
# 守卫与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；既有且
    不同→fail；_commit=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写）。"""
    assert S78.overwrite_guard(None, b"abc") == "write"
    assert S78.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S78.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S78._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S78._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S78._commit(p, b"abc", "probe")


def test_devrecord_canonical_determinism_and_disk_identity(dev):
    """round22-dev-record 盘上件：同参重建两次 byte-exact+盘上件=
    canonical 重建+kind/轮次身份（r22/2026-09-09/development 域）+
    schema_version+is_gate=False+run_record_ref=80a12c05+
    hypothesis_test_i=run 内嵌件原样。"""
    b1 = hashing.canonical_json_bytes(S78.build_dev_record())
    b2 = hashing.canonical_json_bytes(S78.build_dev_record())
    assert b1 == b2  # 同参重建 byte-exact
    raw = open(DEV_PATH, "rb").read()
    assert raw == b1  # 盘上件=canonical 重建
    assert hashing.sha256_file(DEV_PATH).startswith("b4b8fbe9")
    assert dev["kind"] == "tl2_calibration_round22_dev_record"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["evaluation_domain"] == "development"
    assert dev["is_gate"] is False
    assert dev["run_record_ref"]["path_rel"] == \
        "out/v3-tl2/calibration/calibration-run-r22.json"
    assert dev["run_record_ref"]["sha256"] == S78._sha(S78.REL_RUN_R22)
    assert dev["run_record_ref"]["sha256"].startswith("80a12c05")
    assert dev["hypothesis_test_i"]["verdict"] == "regressed"
    assert dev["hypothesis_test_i"]["hypothesis_id"] == \
        "r20-dev-record-candidate-r19-config-same-guidance-repeat"


def test_reference_hash_manifest_and_preregistration_chain(dev):
    """引用件哈希清单 7 件（run-r22=80a12c05/prep-r22=63346ee6/
    guidance-r19=8633bda5/run-r19=e5755a11/dev-r19=0e2fdd69/dev-r20=
    80e3e9e2/run-r20=6573a59a）逐件 live sha256_file 实测与前缀逐一相
    等；预注册链（run 冻结工件）逐件实测 sha 与登记逐一相等（协议/
    prep-r22/axis-plan/dev-r19/dev-r20/guidance-r19 字节复用锚/GT 两
    代/gt-audit 在链）。"""
    entries = dev["reference_hash_manifest"]["entries"]
    expected = {
        "run_r22": "80a12c05",
        "prep_r22": "63346ee6",
        "guidance_r19": "8633bda5",
        "run_r19": "e5755a11",
        "dev_r19": "0e2fdd69",
        "dev_r20": "80e3e9e2",
        "run_r20": "6573a59a",
    }
    assert set(entries) == set(expected)
    for name, prefix in expected.items():
        e = entries[name]
        assert e["sha256_prefix_expected"] == prefix
        assert e["sha256"].startswith(prefix)
        assert hashing.sha256_file(
            os.path.join(REPO, e["path_rel"])).startswith(prefix)
    assert "全部 live sha256_file 实测" in \
        dev["reference_hash_manifest"]["role"]
    # 预注册链（含哈希）：逐件实测与登记一致
    chain = dev["preregistration_chain"]
    for role in ("evaluation_protocol",
                 "r22_prep_record_preregistration",
                 "axis_experiment_plan_r17_r20_frozen",
                 "r20_dev_record_authorization_next_iteration_targets",
                 "observation_guidance_r19_active_byte_reuse",
                 "gt_seed_prep1", "gt_expansion_applied",
                 "gt_audit_r1_closed"):
        assert role in chain, role
        item = chain[role]
        assert hashing.sha256_file(
            os.path.join(REPO, item["path_rel"])) == item["sha256"], role
    assert chain["observation_guidance_r19_active_byte_reuse"][
        "sha256"].startswith("8633bda5")
    note = dev["preregistration_chain_note"]
    assert "字节复用" in note and "80a12c05" in note
    assert "63346ee6" in note and "80e3e9e2" in note


# ---------------------------------------------------------------------------
# 字母裁决与复制性结论逻辑（纯函数构造）
# ---------------------------------------------------------------------------

def test_letter_verdict_branch_and_criteria_booleans(dev, run_doc):
    """字母裁决=regressed（唯一正式裁决）：落支=(g) regressed_guards
    （G2 破坏；支序先行）；判据布尔（M1 带内=True、contact≤7=True、
    G2 破坏=True、M1 ≥0.771429=False）与 run 盘上件逐一相等；预注册判
    据摘录=prep-record 原文（7 键逐字一致）。"""
    ht = dev["hypothesis_test_i"]
    m = ht["measurement"]
    assert ht["verdict"] == "regressed"
    assert m["verdict"] == "regressed"
    assert m["letter_branch"].startswith("(g)")
    assert "G1/G2 任一破坏" in m["letter_branch"]
    assert "不可复制" in m["letter_branch"]
    assert m["crit_regressed_guards_broken"] is True
    assert m["crit_regressed_m1_ge_0_771429"] is False
    assert m["crit_replicated_m1_in_band"] is True
    assert m["crit_replicated_contact_le_7"] is True
    assert m["crit_drifted_m1_lt_0_771429"] is True
    # 与 run 盘上件逐一相等（dev-record 内嵌=run 原文）
    rm = run_doc["hypothesis_test"]["measurement"]
    assert m["letter_branch"] == rm["letter_branch"]
    assert ht["verdict_text"] == run_doc["hypothesis_test"]["verdict_text"]
    # 判据原文摘录=prep-record adjudication 逐字一致
    prep = S78._json_load(S78.REL_PREP_R22)
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "drifted",
              "mechanism_observation_separate", "metric_lesson_separate",
              "m4_second_sample_separate", "regressed", "replicated"):
        assert q[k] == adj[k], k


def test_replication_conclusion_logic_pure_function(dev):
    """复制性结论逻辑纯函数（构造）：实际输入 (16,41,2,guards=False)=
    regressed_guards=登记裁决；反事实构造：G2 维持时同一输入=
    replicated（分岔两侧）；(g) M1 ≥0.771429（771429/10^6 恰等）=
    regressed_m1；带外+守门维持+M1<基线=drifted；带端点与 contact 边
    界；6 位定点常量与判据原文同锚。"""
    assert S78.replication_verdict_fixed_point(16, 41, 2, False) == \
        ("regressed", "regressed_guards")
    assert S78.replication_verdict_fixed_point(16, 41, 2, True) == \
        ("replicated", "replicated")
    assert S78.replication_verdict_fixed_point(36, 46, 2, True) == \
        ("regressed", "regressed_m1")
    assert S78.replication_verdict_fixed_point(771429, 1000000, 2, True) == \
        ("regressed", "regressed_m1")
    assert S78.replication_verdict_fixed_point(26, 35, 2, True) == \
        ("drifted", "drifted")
    # 带端点（恰=下沿/上沿入带）与 contact 边界（恰=7 入、8 出）
    assert S78.replication_verdict_fixed_point(361538, 1000000, 2, True) == \
        ("replicated", "replicated")
    assert S78.replication_verdict_fixed_point(561538, 1000000, 2, True) == \
        ("replicated", "replicated")
    assert S78.replication_verdict_fixed_point(6, 13, 7, True) == \
        ("replicated", "replicated")
    assert S78.replication_verdict_fixed_point(6, 13, 8, True) == \
        ("drifted", "drifted")
    # 6 位定点常量与 s77/判据原文同锚
    assert S78.REJECT_M1_MIN_6DP == 771_429
    assert (S78.REPL_BAND_LO_6DP, S78.REPL_BAND_HI_6DP) == \
        (361_538, 561_538)
    assert S78.CONTACT_MAX_REPL == 7
    # dev-record 反事实构造注记与纯函数一致
    cf = dev["g2_bifurcation_record"]["counterfactual_check"]
    assert cf["guards_ok_false"] == ["regressed", "regressed_guards"]
    assert cf["guards_ok_true"] == ["replicated", "replicated"]


# ---------------------------------------------------------------------------
# M 元组与 run 一致（构造对照）
# ---------------------------------------------------------------------------

def test_m_tuple_matches_run_constructed_cross_check(dev, run_doc):
    """M 元组与 run 一致（构造对照）：axis ledger 本轮行=(0.390244, 0.2,
    4, 0.104545)=run r22_m_tuple_6dp；构造交叉相乘带内判定（16×10^6 ∈
    [361538×41, 561538×41]、<771429×41）、M4=0.454545−0.35、M3=4=run 黑
    点族 rubric 计数；六行并列完整（r16 基线/r17/r18/r19/r20/r22）；
    r19 参照元组=run 登记值；显著收益降幅 0.381185 整数交叉相乘复核。"""
    rows = dev["axis_experiment_ledger"]["cross_round_status"][
        "measured_rows"]
    this = dev["axis_experiment_ledger"]["this_round_measured"]
    run_m = run_doc["hypothesis_test"]["measurement"]["r22_m_tuple_6dp"]
    assert this == {"M1": 0.390244, "M2": 0.2, "M3": 4, "M4": 0.104545}
    assert rows["r22_repeat"] == run_m
    assert rows["r22_repeat"]["M1"] == 0.390244
    # 构造对照：6 位定点整数交叉相乘
    assert S78.REPL_BAND_LO_6DP * 41 <= 16 * 1_000_000
    assert 16 * 1_000_000 <= S78.REPL_BAND_HI_6DP * 41
    assert 16 * 1_000_000 < S78.REJECT_M1_MIN_6DP * 41
    assert round(0.454545 - 0.35, 6) == 0.104545
    bdt = run_doc["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]
    assert bdt["rubric_families"]["counts"]["existence_blackdot"] == \
        rows["r22_repeat"]["M3"] == 4
    assert rows["r16_baseline"] == {"M1": 0.771429, "M2": 0.857143,
                                    "M3": 12, "M4": 0.261904}
    assert rows["r17_axis1"] == {"M1": 0.88, "M2": 0.75, "M3": 8,
                                 "M4": 0.333333}
    assert rows["r18_axis2"] == {"M1": 0.645161, "M2": 0.684211,
                                 "M3": 13, "M4": 0.277778}
    assert rows["r19_axis3"] == {"M1": 0.461538, "M2": 0.571429,
                                 "M3": 4, "M4": 0.211111}
    assert rows["r20_combo"] == {"M1": 0.636364, "M2": 0.285714,
                                 "M3": 6, "M4": 0.25}
    assert run_doc["hypothesis_test"]["measurement"][
        "r19_reference_tuple"] == rows["r19_axis3"]
    sb = dev["axis_experiment_ledger"]["significant_benefit_vs_r16"]
    assert sb["r22_m1_absolute_drop"] == 0.381185
    assert round(0.771429 - 0.390244, 6) == 0.381185
    assert (27 * 41 - 16 * 35) * 1_000_000 >= 100_000 * 35 * 41


# ---------------------------------------------------------------------------
# G2 分岔专节（双账分列+出局条目摘录）
# ---------------------------------------------------------------------------

def test_g2_bifurcation_record_dual_account_and_entries(dev, run_doc):
    """g2_bifurcation_record 字段存在且含双账分列：letter_vs_fact（字
    母=regressed 唯一正式裁决不改写 vs M1 复制事实=机制观察单列）+counts
    （M1 带内/contact≤7/G1 维持/G2 0→2）+2 条出局条目逐条摘录（旗 id/
    类别/area_ratio/对应现象）与 run 通道归因实测逐一相等；照 r20
    g1_bifurcation_record 先例命名（dev-r20 在案）。"""
    g2 = dev["g2_bifurcation_record"]
    assert "g2_bifurcation_record" in dev
    lvf = g2["letter_vs_fact"]
    assert "regressed" in lvf["letter"] and "不改写" in lvf["status"]
    assert "0.390244" in lvf["m1_replication_fact"]
    assert "两账分列" in lvf["status"]
    counts = g2["counts"]
    assert counts["g2_geometry_gate_r19"] == 0
    assert counts["g2_geometry_gate_r22"] == 2
    assert counts["m1_in_replication_band"] is True
    assert counts["contact_le_7"] is True
    assert counts["contact_family_abstain_flags_rubric_r22"] == 2
    assert counts["g1_bottom_courtyard_non_abstain_r22"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert counts["replication_band"] == "[0.361538, 0.561538]（r19±0.10）"
    assert "捆绑" in g2["bifurcation"] or "相悖" in g2["bifurcation"]
    assert "单列" in g2["role"] and "不改写" in g2["role"]
    # 2 条出局条目逐条摘录与 run 通道归因逐一相等（含对应现象）
    gate_entries = run_doc["channel_attribution"]["channel_1_geometry_gate"][
        "r22_area_ratio_rejected_entries"]
    excerpt = g2["rejected_entries_excerpt"]
    assert [e["flag_id"] for e in excerpt] == ["R22T-002", "R22T-013"]
    for want, expect_e, run_e in zip(excerpt, S78.EXPECT_G2_REJECTED_ENTRIES,
                                     gate_entries):
        assert want["flag_id"] == run_e["flag_id"]
        assert want["category"] == run_e["category"] == "silk_readability"
        assert want["area_ratio"] == run_e["area_ratio"]
        assert want["area_ratio"] > 10
        assert want["gt_id"] == run_e["gt_id"]
        assert want["instance"] == run_e["instance"]
        assert want["state"] == run_e["state"]
        assert want["corresponding_phenomenon"] == expect_e["phenomenon"]
        assert len(want["corresponding_phenomenon"]) > 10
        assert "location_evidence" in want["phenomenon_source"]
    # 先例血统：run-r20 的 g1_bifurcation_record 同型（dev-r20 在案）
    dev20 = S78._json_load(S78.REL_DEV_R20)
    assert "g1_bifurcation_record" in dev20


def test_three_axis_closeout_ranking_unchanged_and_dual_account(dev, run_doc):
    """三轴实验总收束位：comparison_rule 排序不变（r19_axis3 第一/r18/
    r16 参照/r17 末位）；r22 不入排序（G2 破坏=资格门剔除、行仅如实入
    账）与 r20（G1 破坏）并列排除位；轴3 收益归因状态=「M1 量级在新鲜
    实例群复现（机制方向支持）但守门字面降级（预注册字母=regressed）」
    两账并列、不合并、不改写；发展域证据不得冒充留出；最终结论维持=
    guidance-r19（轴3 单变量）。"""
    closeout = dev["three_axis_experiment_closeout"]
    rk = closeout["ranking"]
    assert rk["ranking_order_best_first"] == ["r19_axis3", "r18_axis2",
                                              "r16_baseline", "r17_axis1"]
    assert rk["eligible_rows"] == ["r16_baseline", "r17_axis1",
                                   "r18_axis2", "r19_axis3"]
    assert "G2 破坏" in rk["excluded_rows"]["r22_repeat"]
    assert "G1 破坏" in rk["excluded_rows"]["r20_combo"]
    assert "排序不变" in rk["status"] and "不入排序" in rk["status"]
    att = closeout["attribution_status_axis3_benefit"]
    assert "复现" in att and "regressed" in att
    assert "两账并列" in att and "不合并" in att and "不改写" in att
    assert "不得冒充" in closeout["development_domain_discipline"]
    assert "恒 False" in closeout["development_domain_discipline"]
    assert "轴3 单变量" in closeout["final_conclusion_unchanged"]
    assert "guidance-r19" in closeout["final_conclusion_unchanged"]
    # 与 run 盘上对照账排序一致（fail-closed）
    rk_run = run_doc["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]["ranking_by_comparison_rule"]
    assert rk_run["ranking_order_best_first"] == \
        rk["ranking_order_best_first"]
    assert rk_run["r22_eligibility"] is False


# ---------------------------------------------------------------------------
# 下一候选建议（三选项、用户拍板）
# ---------------------------------------------------------------------------

def test_next_candidate_suggestion_three_options(dev):
    """下一候选建议：恰三选项（(a) 接受发展域现状收束训练环+留出集时机
    由用户判断；(b) G2 两条出局条目机制归因→报告框 hygiene 核实→派发层
    框收敛指引须新预注册轮；(c) 再一轮同指引重复轮三样本）；决策权=用
    户拍板、本包不预写决策；(b)(c) 须预注册、(a) 不须。"""
    sug = dev["next_candidate_suggestion"]
    options = sug["options"]
    assert len(options) == 3
    a, b, c = options
    assert "收束训练环" in a["option"] and "留出集" in a["option"]
    assert a["preregistration_required"] is False
    assert "机制归因" in b["option"] and "frame_box_pct" in b["option"]
    assert "hygiene" in b["option"] and "派发层" in b["option"]
    assert "预注册轮" in b["option"]
    assert b["preregistration_required"] is True
    assert "同指引重复轮" in c["option"] and "三样本" in c["option"]
    assert c["preregistration_required"] is True
    assert "用户拍板" in sug["decision_authority"]
    assert "不预写决策" in sug["decision_authority"]
    assert "HOLDOUT" in json.dumps(sug, ensure_ascii=False)
    assert "负责任报告" in b["option"]  # 无「负责责任」类笔误
    # 由用户拍板语义在下一目标节复现
    assert any("由用户拍板" in t for t in dev["next_iteration_targets"])


# ---------------------------------------------------------------------------
# GT/联合门/in_calibrated_range 恒 False
# ---------------------------------------------------------------------------

def test_gt_agreement_milestone_joint_gate_and_in_range_false(dev, run_doc):
    """GT agreement 里程碑+联合门+in_calibrated_range 恒 False：union=
    agreement=1/13（GT-REVC-P1-L1SHORT，R22T-007+R22T-017 双实例命中=
    agreement 口径自 r12 引入以来首次计入）；代表配置聚合 0.466667、
    joint not_met、连续=0；criteria 四门布尔与 run 一致；in_calibrated_
    range 恒 False 多处一致+不得冒充留出；通道门 几何 2/类别 4/视角 1
    对照在案。"""
    mile = dev["gt_agreement_milestone"]
    assert mile["gt_id"] == "GT-REVC-P1-L1SHORT"
    assert sorted(mile["hit_flags"]) == ["top-i2:R22T-007:prep1",
                                         "top-i3:R22T-017:prep1"]
    assert mile["recall"] == {"agreement": 0.076923, "union": 0.076923}
    assert "首次计入" in mile["agreement_first_counted"]
    assert "结构性" in mile["structural_note"]
    assert dev["gt_audit_ref"] == run_doc["gt_audit_reference"]
    # 联合门与代表配置聚合
    diag = dev["diagnostic_result"]
    assert diag["abstain_rate_total"] == 0.466667
    assert diag["gt_recall_total"] == 0.0
    assert diag["seed_match_rate_total"] == 0.0
    assert diag["joint_evaluation"] == "not_met"
    assert diag["gt_match_dual"]["union"]["count"] == 1
    assert diag["gt_match_dual"]["agreement"]["count"] == 1
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 18 and fp["non_abstain_count"] == 33
    trend = dev["joint_evaluation_trend"]
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    # criteria 与 run 盘上件一致
    criteria = {c["id"]: c["met"] for c in diag["criteria"]}
    assert criteria == {"gt_count_ge_12": True, "gt_recall_ge_0.75": False,
                        "seed_match_rate_ge_0.5": False,
                        "abstain_rate_le_0.5": True}
    # in_calibrated_range 恒 False（总收束位+域基注记）与通道门对照
    closeout = dev["three_axis_experiment_closeout"]
    assert "恒 False" in closeout["development_domain_discipline"]
    assert "不得冒充留出" in dev["domain_basis_quote"]
    text = json.dumps(dev["directional_observation_vs_r16"],
                      ensure_ascii=False).replace("\n", "")
    assert "0→0→2" in text
    assert "视角门 0→0→1" in text
    assert "→4（r22" in text
    g2run = run_doc["channel_attribution"]["channel_2_category_gate"]
    assert len(g2run["r22_category_mismatch_entries"]) == 4
    assert len(run_doc["channel_attribution"]["view_gate_observations"][
        "r22_entries"]) == 1


# ---------------------------------------------------------------------------
# 机制观察（M4 双样本/三族对照/援引对照）
# ---------------------------------------------------------------------------

def test_mechanism_observation_m4_families_and_citations(dev):
    """机制观察单列：M4 双样本（r19=0.211111 未过 0.20 门[差 0.011111
    在案] vs r22=0.104545 过门=第二次样本过门；不进字母、不合并分布、不
    挑优）；rubric 三族 r22（2/4/12）对照 r19（4/4/14）与 r20（2/6/10）
    ——黑点 4=与 r19 持平；top 分型 2/14/0；黑点 bottom 仍存在性弃权
    （bottom-i2 两板）；援引计数对照 r19 基线（旗级 6+2/notes 10/12 在
    案；r22=旗级全 0、notes §5B=0/12、(iii-a)=6/12；落支 间隙 6+侵入 1+
    残余弃权 2）。"""
    mo = dev["mechanism_observation_r22"]
    m4 = mo["m4_second_sample"]
    assert (m4["r19"], m4["r22"]) == (0.211111, 0.104545)
    assert m4["r19_pass_gate"] is False
    assert m4["r22_pass_gate"] is True
    assert m4["supported_gate"] == 0.2
    assert "0.011111" in m4["note"]
    assert "不进字母" in m4["note"] and "不合并分布" in m4["note"]
    fam = mo["rubric_families_vs_baselines"]
    assert fam["r22_measured"] == {"contact": 2, "existence_blackdot": 4,
                                   "existence_other": 12}
    assert fam["r19_registered"] == {"contact": 4, "existence_blackdot": 4,
                                     "existence_other": 14}
    assert fam["r20_registered"] == {"contact": 2, "existence_blackdot": 6,
                                     "existence_other": 10}
    assert "与 r19 持平" in fam["status"]
    assert mo["top_abstain_typology_r22"]["counts"] == \
        {"contact": 2, "existence": 14, "other_layer": 0}
    bd = mo["black_dot_observation"]
    assert bd["by_instance"] == {"bottom-i1": 0, "bottom-i2": 2,
                                 "bottom-i3": 0, "top-i1": 0,
                                 "top-i2": 2, "top-i3": 0}
    assert "存在性弃权" in bd["bottom_blackdot_still_existence_abstain"]
    assert "§5B" in bd["bottom_blackdot_still_existence_abstain"]
    # 援引计数对照 r19 基线（如实登记）
    cc = mo["citation_counts_vs_r19"]
    r19 = cc["r19_baseline_registered"]
    assert "6 旗" in r19["flag_level"] and "2 旗" in r19["flag_level"]
    assert "10/12" in r19["notes_level"]
    r22 = cc["r22_measured"]
    assert r22["flag_level_s5b_literal"] == 0
    assert r22["flag_level_iiia_literal"] == 0
    assert r22["flag_level_branch_literal"] == 0
    assert r22["notes_level_s5b"] == "0/12 派次（指引字节复用无 §5B 节=任何" \
        "援引为零上下文）"
    assert r22["notes_level_iiia"] == "6/12 派次"
    assert r22["branch_counts_flag_level"] == \
        {"branch1_gap_report": 6, "branch2_intrusion_report": 1,
         "branch3_residual_abstain": 2}
    assert "分开记" in cc["status"]


# ---------------------------------------------------------------------------
# 轮次身份/跳号声明/趋势行/结论锚/分包边界
# ---------------------------------------------------------------------------

def test_round_identity_skip_declaration_and_prefix_difference(dev):
    """轮次身份声明：同指引重复轮（r16 先例）、changed_variables=0（指
    引/渲染字节复用、唯一操作=实例群重抽）、§6 前缀差异登记（R19T-/R19B-
    落盘原文 vs R22T/R22B 派发层覆盖、r16 先例在案）、零新建指引文件；
    跳号声明：r21=冻结计划未执行位（axis-plan 预留条件位、槽位永久留
    空、r22 与该位无涉）；冻结原文引用与 prep-record 链锚逐字一致。"""
    rid = dev["round_identity_declaration"]
    assert rid["changed_variables"] == 0
    assert rid["guidance_reuse"]["mode"] == "byte_reuse_zero_change"
    assert rid["guidance_reuse"]["base_sha256_prefix"] == "8633bda5"
    assert rid["guidance_reuse"]["byte_delta"] == 0
    assert rid["guidance_reuse"]["zero_new_guidance_file"] is True
    assert rid["sole_operation"] == "reader 实例群重抽（12 派次）"
    assert "r16 先例" in rid["precedent"]
    assert "R19T-" in rid["section6_prefix_difference"]
    assert "R22T" in rid["section6_prefix_difference"]
    assert "派发指令层覆盖" in rid["section6_prefix_difference"]
    assert "r16 先例" in rid["section6_prefix_difference"]
    assert "changed_variables=[]" in rid["changed_variables_note"]
    assert dev["round_nature"].startswith("development 域同指引重复轮")
    # 跳号声明
    skip = dev["r21_skip_declaration"]
    assert skip["r21_status"] == "冻结计划未执行位（槽位永久留空）"
    assert "跳号" in skip["declaration"]
    assert "R21 不做" in skip["declaration"]
    assert "永久留空" in skip["declaration"]
    quotes = skip["frozen_quotes"]
    prep = S78._json_load(S78.REL_PREP_R22)
    frozen = prep["guidance_reuse"]["chain_anchors"][
        "axis_experiment_plan_frozen_r21_slot"]["r21_slot_frozen_quotes"]
    assert quotes == frozen  # 与 prep-record 链锚逐字一致
    assert "R21（三轴全组合）" in quotes[
        "combination_decision_rule.ii_full_combination"]
    assert "R21 不做" in quotes["early_stop_rule."
                                "strong_single_axis_shortcut"]


def test_joint_trend_rows_r5_to_r22(dev):
    """联合评价趋势行：r5–r20 行=dev-r20 在案行冻结转录逐一相等+追加
    r22 行（代表配置口径实测：15/7/0.466667、not_met、source=run-r22
    80a12c05）；连续达标=0；聚合口径分列注记在案。"""
    trend = dev["joint_evaluation_trend"]["by_round"]
    assert [r["round"] for r in trend] == [
        "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13", "r14",
        "r15", "r16", "r17", "r18", "r19", "r20", "r22"]
    dev20 = S78._json_load(S78.REL_DEV_R20)
    prior = dev20["joint_evaluation_trend"]["by_round"]
    assert trend[:-1] == prior  # r5–r20 冻结转录
    row22 = trend[-1]
    assert (row22["flag_count_total"], row22["abstain_count_total"],
            row22["abstain_rate_total"]) == (15, 7, 0.466667)
    assert row22["joint_evaluation"] == "not_met"
    assert row22["gt_recall_total"] == 0.0
    assert row22["matches_total"] == 0
    assert row22["source"]["sha256"].startswith("80a12c05")
    assert row22["round_id"] == ROUND_ID
    assert "r11–r22 行=代表配置口径" in \
        dev["joint_evaluation_trend"]["aggregation_scope_note"]


def test_honest_conclusion_next_targets_anchors_and_rerun_idempotent(dev):
    """honest 结论/下一目标关键锚+重跑语义：honest_conclusion 含字母裁
    决（regressed 唯一正式）、G2 分岔两账分列、M4 双样本过门事实、GT
    agreement 首次计入、三轴收束两账并列、跳号、不得冒充留出、
    in_calibrated_range 恒 False；next_iteration_targets 五件组；s78
    main 幂等重跑（盘上字节零改动）+s77 分包边界（无 dev-record 构建
    函数、只产 run-r22；s78 只写 round22-dev-record.json 一件）。"""
    hc = dev["honest_conclusion"]
    for anchor in ("regressed", "唯一正式裁决", "regressed_guards",
                   "0.390244", "[0.361538, 0.561538]", "0.461538",
                   "g2_bifurcation_record", "两账分列",
                   "0.104545", "第二次样本过门", "0.011111",
                   "首次计入", "r19_axis3 第一", "不合并、不改写",
                   "不得冒充留出", "in_calibrated_range 恒 False",
                   "跳号"):
        assert anchor in hc, anchor
    nxt = dev["next_iteration_targets"]
    assert len(nxt) == 5
    assert "排序不变" in nxt[0] and "两账并列" in nxt[0]
    assert "(a)" in nxt[1] and "(b)" in nxt[1] and "(c)" in nxt[1]
    assert "机制归因" in nxt[1] and "三样本" in nxt[1]
    assert "不得事后改判" in nxt[2]
    assert "留出集时机" in nxt[3] and "连续 2 轮达标" in nxt[3]
    assert "零旗标" in nxt[4] and "存在性" in nxt[4]
    # 重跑语义：main 幂等重跑（不抛异常）且盘上字节零改动
    before = open(DEV_PATH, "rb").read()
    S78.main()
    assert open(DEV_PATH, "rb").read() == before
    assert hashing.sha256_file(DEV_PATH).startswith("b4b8fbe9")
    # 分包边界：s77 零 dev-record 写入（只产 run-r22）；s78 只写本件
    path77 = os.path.join(REPO, "scripts", "s77_calibration_r22_compare.py")
    spec = importlib.util.spec_from_file_location(
        "s77_probe_pkg", path77)
    s77 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s77)
    assert not hasattr(s77, "build_dev_record")
    assert hasattr(s77, "build_run")
    assert hasattr(S78, "build_dev_record")
