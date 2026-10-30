"""R20 收口包 B 测试（s75_calibration_r20_devrecord /
round20-dev-record.json）——轮次开发记录生成器（s72 底稿同构）：
stage2 组合轮（axis-experiment-plan-r17-r20 stage2 唯一组合轮=轴3+轴2
两轴变更并施；变更=判读指引合成 observation-guidance-r20.md 9cdac9ed=
r19 基座 8633bda5 机械变换派生+§5B 整节自 r18 指引 cadcb8f3 逐字转录
[content_sha256 19ecdb42]+§6 前缀=§5B+§4(iii-a) 两增补并集；(iii-a) 随
基座逐字承继；渲染零变更=renders-r14b 字节复用；GT/阈值/协议零变更）+
预注册假设（axis-plan-r20-combo-additivity）ordering 三分判据裁决=
reject（唯一正式裁决）：(s) R20 四元组 (0.636364, 0.285714, 6, 0.25)
ordering 字典序劣于最优单轴 r19 (0.461538, 0.571429, 4, 0.211111)（M1
首键即分胜负）⇒未落；(r) G1 破坏命中（bottom courtyard 非弃权 2/0/0≠
0/0/0 维持；bottom-i1 两板 R20B-003/R20B-006 经 (iii-a) 间隙支负责任报
告路径产生）⇒reject_guards 支（支序最高）；G2 维持（R19=0→R20=0）；
(r) M1 ≥0.771429 未中；(m) 未落（支序 reject 在前）⇒reject——组合出局
（early_stop_rule.guard_failure_exit；处置=iii_non_additive_fallback 采
最优单轴 r19）+ G1 分岔记录单列（守门设计针对 courtyard 混淆弃权、本轮
触发源=负责任报告——(iii-a) 把弃权引导为有据报告；条款按设计工作但按
预注册字母仍=reject；守门条件与判据改良的方向冲突=机制教训）+ 援引分记
（旗级 §5B/(iii-a)/分支( 全 0；notes 级各 4/12=援引习惯集中在 notes 层）
+ rubric 族 contact 2/黑点 6/存在性其他 10 + M 元组五轮并列 + r20 资格门
剔除不入排序 + 显著收益 0.135065 描述层命中（与字母分列互不改写）+ GT
双口径 union=agreement=0/13 全轮零命中 + 联合门 not_met +
in_calibrated_range 恒 False + 阶段2 收束=combination_decision_rule 执行
完毕（supported 未落、marginal 未落、reject 落）⇒收益最大配置=轴3 单变
量（guidance-r19，M1=0.461538 历史最佳、contact 族 10→4、黑点族 13→4）；
R21 不做（early_stop+三轴不全正+G1 破坏三重依据）+ 下一候选建议如实单
列（r19 M4=0.211111 差 0.011111 未过 supported 门——同指引重复轮（r16
先例）或收束转入收敛评估；由用户拍板）。

覆盖（14 测试，只读 out/、零子进程/零网络；s75 幂等重跑例外=护栏语义
在案、字节零改动）：
- 防覆盖守卫：overwrite_guard 三态+_commit 写入/幂等/不同字节 FAIL；
- s75 常量与引用件哈希清单（run-r20=6573a59a/guidance-r20=9cdac9ed/
  prep-r20=e29ee2a3/axis-plan=b6ec6467/run-r19=e5755a11/dev-r19=0e2fdd69
  盘上实测）；
- canonical 确定性（盘上件=同参重建 byte-exact）+轮次身份；
- 字母裁决=reject 落支与判据布尔（ordering 不劣于=False、G1 破坏=True、
  M1 门未中、marginal 未落）；
- M 元组与 run 记录一致性（构造对照：逐实例重算 M1/M2/M4、rubric 族
  M3、五轮并列、M1 绝对降幅整数交叉相乘、r16 基线 live 重放）；
- G1 分岔记录字段存在（gate_design/trigger_source/bifurcation/lesson/
  counts 五件组）；
- 阶段2 收束（verdict_chain 三支+final_conclusion 锚+R21 三重依据+
  final_selection 应用与 run 排序逐一相等）；
- 阶段2 结论纯函数构造对照（轴序变化跟随/守门剔除/同分简约优先/
  ValueError/R21 触发构造/0.60 边界/排序键 tie-break）；
- GT 双口径零命中+联合门+in_calibrated_range 恒 False；
- 机制观察（援引分记/落支/黑点族/分型/rubric 族与 run 一致）；
- 下一候选建议（两选项/差值算术/用户拍板/预注册要求）；
- 趋势行与预注册链（run 冻结工件逐件实测）；
- 观察/教训/下一目标关键锚；
- s75 幂等重跑+s74 零 dev-record 写入分包边界。
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

ROUND_ID = "2026-09-09-r20"
ROUND_LABEL = "r20"
DECLARED_DATE = "2026-09-09"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")


def _load(rel_path, name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(REPO, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, rel))


S75 = _load(os.path.join("scripts", "s75_calibration_r20_devrecord.py"),
            "s75_calibration_r20_devrecord")


@pytest.fixture(scope="module")
def dev_record():
    """round20-dev-record 盘上文档（只读）。"""
    path = os.path.join(CAL_DIR, "round20-dev-record.json")
    return json.loads(open(path, encoding="utf-8").read())


@pytest.fixture(scope="module")
def run_doc():
    """calibration-run-r20 盘上文档（唯一事实源；只读）。"""
    return json.loads(open(os.path.join(
        CAL_DIR, "calibration-run-r20.json"), encoding="utf-8").read())


@pytest.fixture(scope="module")
def disk_bytes():
    path = os.path.join(CAL_DIR, "round20-dev-record.json")
    return open(path, "rb").read()


# ---------------------------------------------------------------------------
# 防覆盖守卫（纯函数三态+_commit 落盘语义）
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫：无既有→write；字节等同→idempotent_skip；既有且不同
    →fail；_commit 落盘=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写）。"""
    assert S75.overwrite_guard(None, b"abc") == "write"
    assert S75.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S75.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S75._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"                      # 回读自证
    assert S75._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S75._commit(p, b"abc", "probe")                  # 不同字节→FAIL


# ---------------------------------------------------------------------------
# 常量与引用件哈希清单（fail-closed 实测）
# ---------------------------------------------------------------------------

def test_s75_constants_and_reference_hash_manifest(dev_record):
    """s75 声明常量（无 wall-clock）+ordering 三分判据实测锚+引用件哈希
    清单六件（run-r20=6573a59a、guidance-r20=9cdac9ed、prep-r20=e29ee2a3、
    axis-plan=b6ec6467、run-r19=e5755a11、dev-r19=0e2fdd69）与盘上实测逐
    一相等。"""
    assert S75.DECLARED_DATE == DECLARED_DATE
    assert S75.ROUND_ID == ROUND_ID
    assert S75.ROUND_LABEL == ROUND_LABEL
    assert S75.KIND == "tl2_calibration_round20_dev_record"
    assert S75.EVALUATION_DOMAIN == "development"
    # 三分判据实测锚（操作化定义）
    assert (S75.EXPECT_TOP_ABSTAIN_R20, S75.EXPECT_TOP_FLAGS_R20) == (14, 22)
    assert S75.EXPECT_TOP_RATE_R20 == 0.636364
    assert (S75.EXPECT_BOTTOM_ABSTAIN_R20,
            S75.EXPECT_BOTTOM_FLAGS_R20) == (4, 14)
    assert S75.EXPECT_BOTTOM_RATE_R20 == 0.285714
    assert (S75.EXPECT_TOP_R16_BASELINE_LIVE,
            S75.EXPECT_TOP_R16_BASELINE_VALUE) == ("27/35", 0.771429)
    assert (S75.EXPECT_BOTTOM_R16_BASELINE_LIVE,
            S75.EXPECT_BOTTOM_R16_BASELINE_VALUE) == ("12/14", 0.857143)
    assert (S75.EXPECT_CONTACT_R20, S75.EXPECT_CONTACT_R16_BASELINE) == \
        (2, 10)
    assert S75.EXPECT_CONTACT_CHAIN_R13_R16 == {"r13": 8, "r14": 15,
                                                "r15": 5, "r16": 10}
    assert (S75.EXPECT_M1, S75.EXPECT_M2, S75.EXPECT_M3, S75.EXPECT_M4) == \
        (0.636364, 0.285714, 6, 0.25)
    assert S75.EXPECT_R16_BASELINE_M1_M2_M3_M4 == \
        [0.771429, 0.857143, 12, 0.261904]
    assert S75.EXPECT_R17_MEASURED == {"M1": 0.88, "M2": 0.75, "M3": 8,
                                       "M4": 0.333333}
    assert S75.EXPECT_R18_MEASURED == {"M1": 0.645161, "M2": 0.684211,
                                       "M3": 13, "M4": 0.277778}
    assert S75.EXPECT_R19_MEASURED == {"M1": 0.461538, "M2": 0.571429,
                                       "M3": 4, "M4": 0.211111}
    assert S75.EXPECT_M1_ABSOLUTE_DROP == 0.135065
    assert S75.REJECT_M1_MIN_6DP == 771_429
    assert (S75.EXPECT_TYPE_COUNTS, S75.EXPECT_RUBRIC_COUNTS) == \
        ({"contact": 4, "existence": 9, "other_layer": 1},
         {"contact": 2, "existence_blackdot": 6, "existence_other": 10,
          "other": 0, "semantic_confusion": 0})
    assert S75.EXPECT_BRANCH_COUNTS == {"branch1_gap_report": 2,
                                        "branch2_intrusion_report": 4,
                                        "branch3_residual_abstain": 7}
    assert S75.EXPECT_G1_R20 == {"bottom-i1": 2, "bottom-i2": 0,
                                 "bottom-i3": 0}
    assert S75.EXPECT_ZERO_FLAG_PARTS == []
    # 引用件哈希清单：盘上实测逐一命中在案前缀
    entries = dev_record["reference_hash_manifest"]["entries"]
    assert set(entries) == {"run_r20", "guidance_r20", "prep_r20",
                            "axis_experiment_plan", "run_r19", "dev_r19"}
    for name, (rel, prefix) in S75.REFERENCE_HASH_EXPECTED.items():
        entry = entries[name]
        assert entry["path_rel"] == rel
        assert entry["sha256_prefix_expected"] == prefix
        assert entry["sha256"] == _sha(rel)              # live 实测
        assert entry["sha256"].startswith(prefix)


# ---------------------------------------------------------------------------
# canonical 确定性+轮次身份
# ---------------------------------------------------------------------------

def test_dev_record_canonical_rebuild_and_identity(dev_record, disk_bytes):
    """盘上件=canonical 重建 byte-exact（确定性；同参纯函数可重跑）+
    轮次身份（r20/2026-09-09/development 域/非门）+run_record_ref 实测
    sha（6573a59a）+组合轮轮次性质锚。"""
    assert hashing.canonical_json_bytes(S75.build_dev_record()) == disk_bytes
    dev = dev_record
    assert dev["kind"] == "tl2_calibration_round20_dev_record"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["evaluation_domain"] == "development"
    assert dev["is_gate"] is False
    # 组合轮轮次性质（§5B+§4(iii-a) 并集+渲染零变更+阶段2）
    rn = dev["round_nature"]
    for need in ("§5B", "(iii-a)", "两增补并集", "9cdac9ed", "8633bda5",
                 "cadcb8f3", "renders-r14b", "字节复用", "第二十轮",
                 "axis-plan-r20-combo-additivity", "R20T-/R20B-",
                 "in_calibrated_range 恒 False",
                 "A3_criterion_contact_clarification+"
                 "A2_blackdot_instrument_annotation"):
        assert need in rn, need
    # run_record_ref=run-r20 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["path_rel"] == \
        "out/v3-tl2/calibration/calibration-run-r20.json"
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r20.json")
    assert dev["run_record_ref"]["sha256"].startswith("6573a59a")


# ---------------------------------------------------------------------------
# 字母裁决=reject（落支与判据布尔）
# ---------------------------------------------------------------------------

def test_dev_record_letter_reject_branches(dev_record, run_doc):
    """字母裁决节与 run-r20 逐字镜像（唯一正式裁决=reject）：(s) ordering
    不劣于=False；(r) G1 破坏=True、M1 门=False；(m) M1 <0.771429=True 但
    支序 reject 在前；落支=(r) reject_guards（G1 破坏+采最优单轴 r19 处
    置）；守门 G1=False/G2=True/early_stop 触发；描述性结论锚。"""
    dev, run = dev_record, run_doc
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    ht = dev["hypothesis_test_i"]
    m = ht["measurement"]
    assert ht["hypothesis_id"] == "axis-plan-r20-combo-additivity"
    assert ht["verdict"] == "reject"
    assert m["verdict"] == "reject"
    # (s) supported：ordering 字典序不劣于 r19=False
    assert m["crit_supported_ordering_not_worse_than_r19"] is False
    # (r) reject：G1 破坏=True（reject_guards 支）；M1 ≥0.771429=False
    assert m["crit_reject_guards_broken"] is True
    assert m["crit_reject_m1_ge_0_771429"] is False
    # (m) marginal：M1 <0.771429=True 但支序 reject 在前→未落
    assert m["crit_marginal_m1_lt_0_771429"] is True
    assert m["letter_branch"].startswith("(r)")
    assert "G1/G2 任一破坏" in m["letter_branch"]
    assert "bottom courtyard 非弃权实测 [2, 0, 0]" in m["letter_branch"]
    assert "采最优单轴 r19" in m["letter_branch"]
    # 实测主判据数
    assert m["r20_m_tuple_6dp"] == {"M1": 0.636364, "M2": 0.285714,
                                    "M3": 6, "M4": 0.25}
    assert m["r19_reference_tuple"] == {"M1": 0.461538, "M2": 0.571429,
                                        "M3": 4, "M4": 0.211111}
    assert m["contact_family_abstain_flags_rubric_r20"] == 2
    assert m["contact_r16_baseline_registered"] == 10
    assert m["top_abstain_rate_r20"] == 0.636364
    assert m["m4_top_rate_range_r20"] == 0.25
    assert "14/22" in m["top_abstain_rate_r20_arithmetic"]
    # 描述性结论非因果证明（verdict_text 锚）
    vt = ht["verdict_text"]
    assert "唯一正式裁决" in vt and "只描述不断言" in vt
    # 守门独立单列（G1 破坏/G2 维持/early_stop 触发）
    assert m["guard_channel"]["g1_ok"] is False
    assert m["guard_channel"]["g2_guard_ok"] is True
    assert m["guard_channel"]["guards_ok"] is False
    assert m["guard_channel"]["g2_geometry_gate_r19"] == 0
    assert m["guard_channel"]["g2_geometry_gate_r20"] == 0
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    assert g12["axis_early_stop_triggered"] is True
    assert g12["g1_bottom_courtyard_non_abstain_r20"] == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}


# ---------------------------------------------------------------------------
# M 元组与 run 记录一致性（构造对照）
# ---------------------------------------------------------------------------

def test_dev_record_m_tuple_consistency_constructed(dev_record, run_doc):
    """M 元组构造对照：从 run-r20 内嵌实例记录重算 M1（14/22）/M2（4/14）/
    M4（极差 0.25）/M3（rubric 族 6），与 s75 锚、run 对照账、dev 对照账
    逐一相等；五轮并列（r16 基线/r17 轴1/r18 轴2/r19 轴3/r20 组合）与
    dev-r19 在案行一致；M1 绝对降幅 0.135065 整数交叉相乘；r16 基线 live
    重放（27/35、12/14）。"""
    dev, run = dev_record, run_doc
    inst = run["instances"]
    top = ("top-i1", "top-i2", "top-i3")
    bottom = ("bottom-i1", "bottom-i2", "bottom-i3")
    tf = sum(inst[n]["combined"]["flag_count"] for n in top)
    ta = sum(inst[n]["combined"]["abstain_count"] for n in top)
    bf = sum(inst[n]["combined"]["flag_count"] for n in bottom)
    ba = sum(inst[n]["combined"]["abstain_count"] for n in bottom)
    assert (ta, tf) == (14, 22)
    assert (ba, bf) == (4, 14)
    assert round(ta / tf, 6) == 0.636364
    assert round(ba / bf, 6) == 0.285714
    # M4=top 逐实例弃权率先 6 位取率再取极差（构造复算）
    rates = [inst[n]["combined"]["abstain_rate"] for n in top]
    assert round(max(rates) - min(rates), 6) == 0.25
    assert (max(rates), min(rates)) == (0.75, 0.5)
    # M3 槽位=冻结件黑点族 rubric 口径（构造：族计数表重取）
    counts = run["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]["rubric_families"]["counts"]
    assert counts["existence_blackdot"] == 6 == S75.EXPECT_M3
    # run 对照账与 dev 对照账与 s75 锚三方一致
    ledger = run["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]
    want = {"M1": 0.636364, "M2": 0.285714, "M3": 6, "M4": 0.25}
    assert ledger["r20_measured"]["M1"] == want["M1"]
    assert ledger["r20_measured"]["M2"] == want["M2"]
    assert ledger["r20_measured"]["M3"] == want["M3"]
    assert ledger["r20_measured"]["M4"] == want["M4"]
    assert dev["axis_experiment_ledger"]["this_round_measured"] == want
    assert (S75.EXPECT_M1, S75.EXPECT_M2, S75.EXPECT_M3, S75.EXPECT_M4) == \
        (want["M1"], want["M2"], want["M3"], want["M4"])
    # 五轮并列（r16 基线/r17 轴1/r18 轴2/r19 轴3/r20 组合）
    rows = dev["axis_experiment_ledger"]["cross_round_status"]["measured_rows"]
    assert rows["r16_baseline"] == {"M1": 0.771429, "M2": 0.857143,
                                    "M3": 12, "M4": 0.261904}
    assert rows["r17_axis1"] == S75.EXPECT_R17_MEASURED == \
        ledger["r17_axis1_row"]
    assert rows["r18_axis2"] == S75.EXPECT_R18_MEASURED == \
        ledger["r18_axis2_row"]
    assert rows["r19_axis3"] == S75.EXPECT_R19_MEASURED == \
        ledger["r19_axis3_row"]
    assert rows["r20_combo"] == want
    # dev-r19 在案行与 dev-r20 装载一致（血统核对）
    dev19 = json.loads(open(os.path.join(
        CAL_DIR, "round19-dev-record.json"), encoding="utf-8").read())
    rows19 = dev19["axis_experiment_ledger"]["cross_round_status"][
        "measured_rows"]
    assert rows19["r19_axis3"] == rows["r19_axis3"]
    # M1 绝对降幅（6 位取率后作差，构造复算）与整数交叉相乘方向
    assert round(0.771429 - 0.636364, 6) == 0.135065
    assert ledger["significant_benefit_vs_r16"]["r20_m1_absolute_drop"] == \
        0.135065
    assert ledger["significant_benefit_vs_r16"]["r19_drop_reference"] == \
        0.309891
    assert ledger["significant_benefit_vs_r16"]["met"] is True
    assert (27 * 22 - 14 * 35) * 1_000_000 >= 100_000 * 35 * 22  # ≥0.10
    # r16 基线 live 重放（同一聚合逻辑对 run-r16 内嵌输入）
    run16 = json.loads(open(os.path.join(
        CAL_DIR, "calibration-run-r16.json"), encoding="utf-8").read())
    i16 = run16["instances"]
    assert (sum(i16[n]["combined"]["abstain_count"] for n in top),
            sum(i16[n]["combined"]["flag_count"] for n in top)) == (27, 35)
    assert (sum(i16[n]["combined"]["abstain_count"] for n in bottom),
            sum(i16[n]["combined"]["flag_count"] for n in bottom)) == (12, 14)


# ---------------------------------------------------------------------------
# G1 分岔记录（机制教训单列）
# ---------------------------------------------------------------------------

def test_dev_record_g1_bifurcation_record_fields(dev_record, run_doc):
    """G1 分岔记录字段存在（如实单列）：gate_design/trigger_source/
    bifurcation/mechanism_lesson/role+counts 五件组——守门设计针对
    courtyard 混淆弃权、触发源=负责任报告（(iii-a) 间隙支把弃权引导为有
    据报告）、条款按设计工作但字母仍=reject、方向冲突=机制教训、修订守门
    须预注册不得事后改判；计数与 run 一致（R20B-003/R20B-006、2/0/0、
    基线 0/0/0）。"""
    dev, run = dev_record, run_doc
    rec = dev["g1_bifurcation_record"]
    assert rec["declared_date"] == DECLARED_DATE
    obs = rec["observation"]
    assert "courtyard 混淆弃权" in obs
    assert "负责任报告" in obs and "(iii-a)" in obs
    assert "R20B-003/R20B-006" in obs
    assert "r14–r19 bottom 侧首现" in obs
    assert rec["trigger_source"].startswith("负责任报告")
    bif = rec["bifurcation"]
    assert "条款按设计工作" in bif and "仍=reject" in bif
    assert "守门条件与判据改良的方向冲突" in bif
    lesson = rec["mechanism_lesson"]
    assert "机制教训" in lesson and "预注册字母裁决优先" in lesson
    assert "prep-record 预注册修订" in lesson and "不得事后改判本轮" in lesson
    assert "不凌驾、不改写字母裁决" in rec["role"]
    assert rec["role"].endswith("描述性记录、非因果证明") or \
        "非因果证明" in rec["role"]
    # counts 与 run 实测一致
    c = rec["counts"]
    assert c["bottom_courtyard_non_abstain_r20"] == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
    assert c["g1_baseline_r16_live"] == {"bottom-i1": 0, "bottom-i2": 0,
                                         "bottom-i3": 0}
    assert c["bottom_courtyard_flags_total_r20"] == 2
    assert c["non_abstain_courtyard_flag_ids"] == ["R20B-003", "R20B-006"]
    assert "R20B-003" in c["trigger_flags"] and "R20B-006" in c["trigger_flags"]
    assert "间隙支" in c["trigger_flags"]
    # run 侧机制观察一致（marginal 支未落的原因=支序 reject 在前）
    m = run["hypothesis_test"]["measurement"]
    assert m["crit_reject_guards_broken"] is True
    assert m["crit_marginal_m1_lt_0_771429"] is True


# ---------------------------------------------------------------------------
# 阶段2 收束与最终结论
# ---------------------------------------------------------------------------

def test_dev_record_stage2_closure(dev_record, run_doc):
    """阶段2 收束：combination_decision_rule 执行完毕（supported 未落/
    marginal 未落/reject 落）；最终结论=收益最大配置=轴3 单变量（guidance-
    r19、M1=0.461538 历史最佳、contact 族 10→4、黑点族 13→4）；R21 不做
    三重依据（early_stop/三轴不全正/G1 破坏）；final_selection 应用与
    run-r20 排序逐一相等（r20 资格门剔除）；iv_final_selection/iii_non_
    additive_fallback 冻结原文引用在案。"""
    dev, run = dev_record, run_doc
    sc = dev["stage2_closure"]
    vc = sc["verdict_chain"]
    assert vc["supported"] == "未落（ordering 不劣于 r19=False）"
    assert vc["marginal"] == "未落（支序 reject 在前）"
    assert vc["reject"] == "落（reject_guards：G1 破坏）"
    fc = sc["final_conclusion"]
    for need in ("收益最大配置=轴3 单变量", "guidance-r19",
                 "M1=0.461538 历史最佳", "contact 族 10→4", "黑点族 13→4",
                 "iv_final_selection", "r19_axis3", "资格门剔除",
                 "0.636364"):
        assert need in fc, need
    assert sc["r21"].startswith("R21 不做")
    assert "strong_single_axis_shortcut" in sc["r21"]
    assert "三轴不全正" in sc["r21"] and "G1 破坏排除追加" in sc["r21"]
    assert "执行完毕" in sc["combination_decision_rule_execution"]
    assert "supported 未落" in sc["combination_decision_rule_execution"]
    es = sc["early_stop"]
    assert es["guard_failure_exit_triggered"] is True
    assert es["strong_single_axis_shortcut_triggered"] is True
    assert "出局" in es["rule_quote"]
    # final_selection 应用=run-r20 排序（r20 剔除；r19 第一）
    fsa = sc["final_selection_application"]
    assert fsa["final_config"] == "r19_axis3"
    assert fsa["final_row"] == {"M1": 0.461538, "M2": 0.571429, "M3": 4,
                                "M4": 0.211111}
    assert fsa["eligible_sorted"] == ["r19_axis3", "r18_axis2",
                                      "r16_baseline", "r17_axis1"]
    rk = run["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]["ranking_by_comparison_rule"]
    assert fsa["eligible_sorted"] == rk["ranking_order_best_first"]
    assert rk["r20_eligibility"] is False
    # axis_experiment_ledger 的 stage2_closure 镜像+next_candidate 结构位
    ael = dev["axis_experiment_ledger"]
    assert ael["stage2_closure"] == sc
    assert "阶段2 已收束" in ael["next_candidate_r20"]
    assert "R21 不做" in ael["status"]


def test_stage2_final_selection_pure_function_constructed():
    """阶段2 结论纯函数构造对照：实际轴序→r19_axis3；轴序变更（r20 行改
    善）→结论跟随变化为 r20_combo；r19 守门破坏→r18_axis2 递补；同分
    （四键全等）取变量更少者（简约优先：r19 变量 1<r20 变量 2）；过守门
    配置为空→ValueError；R21 触发构造（全正=True/轴1 负向=False）；快捷
    通道 0.60 边界（6 位定点整数交叉相乘）；排序键 M2→M3→M4 逐级
    tie-break。"""
    rows = {"r16_baseline": {"M1": 0.771429, "M2": 0.857143, "M3": 12,
                             "M4": 0.261904},
            "r17_axis1": S75.EXPECT_R17_MEASURED,
            "r18_axis2": S75.EXPECT_R18_MEASURED,
            "r19_axis3": S75.EXPECT_R19_MEASURED,
            "r20_combo": {"M1": S75.EXPECT_M1, "M2": S75.EXPECT_M2,
                          "M3": S75.EXPECT_M3, "M4": S75.EXPECT_M4}}
    guards = {"r16_baseline": True, "r17_axis1": True, "r18_axis2": True,
              "r19_axis3": True, "r20_combo": False}
    var_counts = {"r16_baseline": 0, "r17_axis1": 1, "r18_axis2": 1,
                  "r19_axis3": 1, "r20_combo": 2}
    # 实际数据：r20 资格门剔除→r19_axis3
    sel = S75.stage2_final_selection(rows, guards, var_counts)
    assert sel["final_config"] == "r19_axis3"
    assert sel["eligible_sorted"] == ["r19_axis3", "r18_axis2",
                                      "r16_baseline", "r17_axis1"]
    assert sel["tied_best"] == ["r19_axis3"]
    # 构造：轴序变更（r20 行成为最优）→结论跟随变化为 r20_combo
    rows_swapped = {k: dict(v) for k, v in rows.items()}
    rows_swapped["r20_combo"] = {"M1": 0.40, "M2": 0.20, "M3": 3, "M4": 0.15}
    guards_open = dict(guards)
    guards_open["r20_combo"] = True
    sel2 = S75.stage2_final_selection(rows_swapped, guards_open, var_counts)
    assert sel2["final_config"] == "r20_combo"
    # 构造：r19 守门破坏→r18_axis2 递补（r20 仍剔除）
    guards_broken = dict(guards)
    guards_broken["r19_axis3"] = False
    sel3 = S75.stage2_final_selection(rows, guards_broken, var_counts)
    assert sel3["final_config"] == "r18_axis2"
    # 同分（四键全等）取变量更少者（简约优先）：r19 与构造 r20 全等
    rows_tie = {k: dict(v) for k, v in rows.items()}
    rows_tie["r20_combo"] = dict(S75.EXPECT_R19_MEASURED)
    sel4 = S75.stage2_final_selection(rows_tie, guards_open, var_counts)
    assert sel4["tied_best"] == ["r19_axis3", "r20_combo"]
    assert sel4["final_config"] == "r19_axis3"  # 变量 1<2
    # 过守门配置为空→ValueError（最终选择前提不成立）
    with pytest.raises(ValueError):
        S75.stage2_final_selection(rows, {k: False for k in rows},
                                   var_counts)
    # R21 全组合触发：实际（轴1 负向）=False；构造全正=True
    three = {k: rows[k] for k in ("r17_axis1", "r18_axis2", "r19_axis3")}
    assert S75.full_combination_trigger(three, 0.771429) is False
    three_positive = {"r17_axis1": {"M1": 0.70, "M2": 0.75, "M3": 8,
                                    "M4": 0.333333},
                      "r18_axis2": rows["r18_axis2"],
                      "r19_axis3": rows["r19_axis3"]}
    assert S75.full_combination_trigger(three_positive, 0.771429) is True
    # 快捷通道边界：M1 恰 0.60 命中、0.600001 未命中（整数交叉相乘）
    assert S75.strong_single_axis_shortcut(0.6) is True
    assert S75.strong_single_axis_shortcut(0.461538) is True
    assert S75.strong_single_axis_shortcut(0.600001) is False
    # 排序键字典序 tie-break（M1 同值依次比 M2→M3→M4）
    assert S75.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3,
                                    "M4": 0.1}) < \
        S75.comparison_sort_key({"M1": 0.5, "M2": 0.3, "M3": 3, "M4": 0.1})
    assert S75.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3,
                                    "M4": 0.1}) < \
        S75.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 4, "M4": 0.1})
    assert S75.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3,
                                    "M4": 0.1}) < \
        S75.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3, "M4": 0.2})
    # 四元组输入兼容（tuple/dict 同键）
    assert S75.comparison_sort_key((0.5, 0.2, 3, 0.1)) == \
        S75.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3, "M4": 0.1})


# ---------------------------------------------------------------------------
# GT 双口径零命中+联合门+in_calibrated_range 恒 False
# ---------------------------------------------------------------------------

def test_dev_record_gt_dual_joint_gate_and_in_range_false(dev_record,
                                                          run_doc):
    """GT 双口径全轮零命中（union=agreement=0/13、candidate 对空集、r19
    唯一命中未再现）；联合门：代表配置（top-i1+bottom-i2 双 tie）joint
    not_met、连续=0、criteria 分项；in_calibrated_range 恒 False（run/
    compliance/honest_conclusion 三处）；零旗标派次=0；bottom 零匹配属
    结构性（gt-audit-r1）。"""
    dev, run = dev_record, run_doc
    dual = run["gt_match_dual"]
    assert (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) == (0, 0, 13)
    assert dual["union"]["gt_ids"] == []
    # 诊断结果镜像（代表配置口径）
    dr = dev["diagnostic_result"]
    assert dr["gt_match_dual"] == {"union": dict(dual["union"]),
                                   "agreement": dict(dual["agreement"])}
    assert dr["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dr["abstain_rate_total"] == 0.333333
    assert dr["gt_recall_total"] == 0.0
    assert dr["seed_match_rate_total"] == 0.0
    comp = run["compliance_representative"]
    assert run["representative_configuration"]["members"] == \
        {"top": "top-i1", "bottom": "bottom-i2"}
    assert run["representative_configuration"]["selection"]["top"][
        "tie"] is True
    assert run["representative_configuration"]["selection"]["bottom"][
        "tie"] is True
    assert comp["joint_evaluation"] == "not_met"
    assert comp["consecutive_rounds"]["consecutive_met_count"] == 0
    assert comp["consecutive_rounds"]["met"] is False
    assert comp["critic_calibration_in_range"] is False
    assert "恒 False" in comp["critic_calibration_in_range_note"]
    assert run["evaluation_domain_note"]["in_calibrated_range"] is False
    criteria = {c["id"]: c["met"] for c in comp["criteria"]}
    assert criteria == {"gt_count_ge_12": True, "gt_recall_ge_0.75": False,
                        "seed_match_rate_ge_0.5": False,
                        "abstain_rate_le_0.5": True}
    # in_calibrated_range 恒 False（honest_conclusion 锚）
    assert "in_calibrated_range 恒 False" in dev["honest_conclusion"]
    assert "不得冒充留出" in dev["honest_conclusion"]
    # 零旗标派次=0（12 格全部≥1 旗）
    assert run["reader"]["zero_flag_parts"]["parts"] == []
    assert run["view_layer"]["bottom"]["abstain_rate"]["median"] == 0.0
    # 趋势行本轮节点
    trend = dev["joint_evaluation_trend"]
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert trend["consecutive_met_count_now"] == 0
    assert "不得写成已达成" in trend["note"]
    # honest_conclusion 零命中转述锚
    assert "union=agreement=0/13" in dev["honest_conclusion"]
    assert "单实例命中不稳定" in dev["honest_conclusion"]


# ---------------------------------------------------------------------------
# 机制观察（援引分记/落支/黑点族/分型）
# ---------------------------------------------------------------------------

def test_dev_record_mechanism_observations(dev_record, run_doc):
    """机制观察单列（dev 镜像 run mo）：援引分记（旗级 §5B/(iii-a)/分支(
    全 0、notes 级各 4/12、来源集合=登记）；(iii-a) 落支=间隙 2+侵入 4+
    残余弃权 7、间隙支 notes 级 2 派次；黑点族 6 旗全弃权（top-i1 2+
    bottom-i3 4）+转非弃权 6（全 bottom）+判正常派次 4；rubric 族 2/6/
    10/0/0；top 分型 4/9/1（14 旗）。"""
    dev, run = dev_record, run_doc
    mo = run["hypothesis_test"]["mechanism_observation"]
    assert dev["hypothesis_test_i"]["mechanism_observation"] == mo
    cc = mo["criterion_citation_observation"]
    counts = cc["citation_counts"]
    assert counts["flag_level_s5b_literal"] == 0
    assert counts["flag_level_iiia_literal"] == 0
    assert counts["flag_level_branch_literal"] == 0
    assert counts["notes_level_s5b"] == 4
    assert counts["notes_level_iiia"] == 4
    assert len(counts["notes_level_s5b_sources"]) == 4
    assert len(counts["notes_level_iiia_sources"]) == 4
    assert "r18" in counts["dual_baseline_r18_s5b"]
    assert "r19" in counts["dual_baseline_r19_iiia"]
    assert cc["branch_counts_flag_level"] == S75.EXPECT_BRANCH_COUNTS
    assert cc["branch1_notes_level_dispatches"] == 2
    bdt = mo["black_dot_tracking"]
    assert bdt["all_abstain"] is True
    assert bdt["by_instance"] == S75.EXPECT_BLACK_DOT_BY_INSTANCE
    assert len(bdt["black_dot_flags"]) == 6
    assert bdt["blackdot_to_non_abstain_count"] == 6
    assert len(bdt["black_dot_non_abstain_flags"]) == 6
    assert all(f["instance"].startswith("bottom")
               for f in bdt["black_dot_non_abstain_flags"])
    assert bdt["judged_normal_dispatches"]["count"] == 4
    assert bdt["rubric_families"]["counts"] == S75.EXPECT_RUBRIC_COUNTS
    ty = mo["top_abstain_typology"]
    assert ty["type_counts"] == S75.EXPECT_TYPE_COUNTS
    assert ty["top_abstain_flags_total"] == 14 and len(ty["rows"]) == 14
    assert ty["top_abstain_rate_range"] == 0.25
    # G1 分岔转述锚（directional 观察如实引用）
    obs_text = "\n".join(dev["directional_observation_vs_r16"])
    assert "G1 分岔" in obs_text
    assert "R20B-003/R20B-006" in obs_text
    assert "notes 层" in obs_text


# ---------------------------------------------------------------------------
# 下一候选建议（如实单列、供主审/用户决策）
# ---------------------------------------------------------------------------

def test_dev_record_next_candidate_suggestion(dev_record):
    """下一候选建议节：上下文（阶段2 已收束+r19 M4=0.211111 差 0.011111
    未过 supported 门 0.20）；两选项（同指引重复轮[r16 先例、预注册要求
    True]／接受 marginal 收益收束转入收敛评估）；决策权=用户拍板；本包不
    预写决策。"""
    dev = dev_record
    ncs = dev["combination_decision_application"]["next_candidate_suggestion"]
    ctx = ncs["context"]
    assert "阶段2 已收束" in ctx
    assert "M4=0.211111" in ctx and "0.011111" in ctx
    assert "supported 门 0.20" in ctx
    assert round(0.211111 - 0.20, 6) == 0.011111  # 差值算术
    assert "供主审/用户决策" in ctx
    assert ncs["decision_authority"] == "由用户拍板（本包只列选项、不预写决策）"
    assert "如实登记的选项清单" in ncs["status"]
    opts = ncs["options"]
    assert len(opts) == 2
    o1, o2 = opts
    assert "同指引重复轮" in o1["option"] and "r16 先例" in o1["option"]
    assert o1["preregistration_required"] is True
    assert "0.09064" in o1["motivation"]
    assert "收敛评估" in o2["option"]
    assert "marginal" in o2["option"]
    assert o2["preregistration_required"] is False
    # 组合决策应用总状态
    cda = dev["combination_decision_application"]
    assert "执行完毕" in cda["status"]
    assert cda["r21_full_combination_trigger"]["met"] is False
    assert cda["r21_full_combination_trigger"]["per_axis_positive"] == \
        {"r17_axis1": False, "r18_axis2": True, "r19_axis3": True}
    assert "两轴变更同时施加" in cda["inputs"]["ranking_rule"] or \
        "M1 升序" in cda["inputs"]["ranking_rule"]
    assert cda["inputs"]["r16_baseline_m1"] == 0.771429
    assert cda["inputs"]["guards"]["r20_combo"] is False


# ---------------------------------------------------------------------------
# 趋势行与预注册链
# ---------------------------------------------------------------------------

def test_dev_record_trend_and_preregistration_chain(dev_record, run_doc,
                                                    disk_bytes):
    """联合评价趋势 r5–r20 逐轮表（r20 行=本轮实测+source sha 6573a59a）
    +预注册链=run-r20 冻结工件逐件实测（与 run 登记一致）+链注锚+引用实
    测一致（canonical 链件哈希复核）。"""
    dev, run = dev_record, run_doc
    trend = dev["joint_evaluation_trend"]
    rounds = [r["round"] for r in trend["by_round"]]
    assert rounds == ["r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12",
                      "r13", "r14", "r15", "r16", "r17", "r18", "r19",
                      "r20"]
    last = trend["by_round"][-1]
    assert last["flag_count_total"] == 12
    assert last["abstain_count_total"] == 4
    assert last["abstain_rate_total"] == 0.333333
    assert last["joint_evaluation"] == "not_met"
    assert last["gt_recall_total"] == 0.0
    assert last["seed_match_rate_total"] == 0.0
    assert last["matches_total"] == 0
    assert last["source"]["path_rel"].endswith("calibration-run-r20.json")
    assert last["source"]["sha256"].startswith("6573a59a")
    assert trend["consecutive_met_count_now"] == 0
    assert "18/36=0.5" in trend["aggregation_scope_note"]
    # 预注册链=run 冻结工件逐件实测（fail-closed 与登记一致）
    chain = dev["preregistration_chain"]
    for item in run["preregistration"]["frozen_artifacts"]:
        assert chain[item["role"]] == {"path_rel": item["path_rel"],
                                       "sha256": item["sha256"]}
        assert chain[item["role"]]["sha256"] == _sha(item["path_rel"])
    note = dev["preregistration_chain_note"]
    for anchor in ("b6ec6467", "e29ee2a3", "9cdac9ed", "8633bda5",
                   "cadcb8f3", "19ecdb42", "b63771f9", "6573a59a",
                   "e5755a11", "62343380", "1f20554a", "选择收益最大的继续",
                   "R20T-", "R20B-", "判读指引合成", "21435", "22893",
                   "delta 1458"):
        assert anchor in note, anchor


# ---------------------------------------------------------------------------
# 观察/教训/下一目标关键锚
# ---------------------------------------------------------------------------

def test_dev_record_observations_notes_and_next_targets(dev_record):
    """方向性观察（派发对照/视角层/GT 双口径/通道归因/字母裁决/机制观察/
    bottom 改善通道/工具行为/被动追踪）、notes（comparator 非门/命名约束/
    归因边界/G1 分岔教训/裁决纪律）、honest_conclusion（reject 组合出局+
    五轮并列+阶段2 收束+下一候选）、next_iteration_targets（阶段2 收束/
    下一候选/G1 分岔后续/留出时机/残余问题）关键锚。"""
    dev = dev_record
    obs_text = "\n".join(dev["directional_observation_vs_r16"])
    for need in ("14/22=0.636364", "4/14=0.285714", "0.25", "reject",
                 "reject_guards", "采最优单轴 r19 配置", "[2, 0, 0]",
                 "R19T-009↔GT-REVC-P1-L1SHORT", "单实例命中不稳定",
                 "0.135065", "0.09064", "improved", "0.333333",
                 "geometry" if False else "几何门", "类别门", "r20=0",
                 "§5B", "(iii-a)", "4/12", "notes 层", "间隙支",
                 "existence_blackdot 6", "existence_other 10",
                 "contact 2/", "同实例跨板连续", "零旗标派次=0",
                 "两轴并施", "无法分离", "§4(i)", "R20T/R20B"):
        assert need in obs_text, need
    # notes：裁决纪律+G1 分岔教训+度量教训
    notes = "\n".join(dev["notes"])
    for need in ("advisory 侧分析", "禁称 precision/FPR",
                 "无法分离两轴各自贡献", "不手工抄数", "drift_confound_note",
                 "唯一正式裁决", "不得回溯改判既往轮次", "M3 槽位",
                 "rubric 机械套用", "判据设计的机制教训",
                 "按改良方向工作却触发守门字面",
                 "prep-record 预注册", "不得事后改判本轮", "reject 维持",
                 "两账分列", "非因果证明"):
        assert need in notes, need
    # honest_conclusion：reject+阶段2 收束+下一候选+双口径
    hc = dev["honest_conclusion"]
    for need in ("reject", "唯一正式裁决", "G1 破坏", "ordering",
                 "(0.636364, 0.285714, 6, 0.25)",
                 "(0.461538, 0.571429, 4, 0.211111)", "采最优单轴 r19",
                 "0.135065", "五轮并列", "收益最大配置=轴3 单变量",
                 "guidance-r19", "M1=0.461538 历史最佳", "contact 族 10→4",
                 "黑点族 13→4", "R21 不做", "early_stop", "三轴不全正",
                 "M4=0.211111 差 0.011111", "同指引重复轮", "r16 先例",
                 "收敛评估", "由用户拍板", "G1 分岔", "非因果证明",
                 "not_met", "0.333333", "union=agreement=0/13",
                 "19ecdb42", "in_calibrated_range 恒 False", "gt-audit-r1",
                 "两轴并施"):
        assert need in hc, need
    # next_iteration_targets：五条（阶段2 收束/下一候选/G1 后续/留出/残余）
    nxt = "\n".join(dev["next_iteration_targets"])
    assert len(dev["next_iteration_targets"]) == 5
    for need in ("收益最大配置=轴3 单变量", "guidance-r19", "R21 不做",
                 "三重独立依据", "M4=0.211111", "0.011111", "同指引重复轮",
                 "r16 先例", "收敛评估", "由用户拍板", "不预写决策",
                 "G1 分岔", "prep-record 预注册修订守门操作化定义",
                 "不得事后改判", "留出集时机", "HOLDOUT-PLAN.md",
                 "a4b80193", "holdout-candidates-r1",
                 "in_calibrated_range 恒 False", "gt-audit-r1",
                 "bottom-i3", "实例两极分化"):
        assert need in nxt, need
    # 域声明引用（run basis_quote 承接+dev 附加句）
    assert "第 20 轮迭代" in dev["domain_basis_quote"]
    assert "不得冒充留出证据" in dev["domain_basis_quote"]
    assert dev["gt_audit_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/gt-audit-r1.json")


# ---------------------------------------------------------------------------
# s75 幂等重跑与分包边界
# ---------------------------------------------------------------------------

def test_s75_rerun_idempotent_and_package_boundary(dev_record, disk_bytes):
    """s75 重跑语义：build_dev_record 同参重建 byte-exact；main 幂等重跑
    （round20-dev-record 已存在且字节等同→零覆写、字节零改动）；s74 零
    dev-record 写入分包边界（只产 run-r20）。"""
    # 同参重建（纯函数）与盘上产物逐字节一致
    assert hashing.canonical_json_bytes(S75.build_dev_record()) == disk_bytes
    # 分包边界：s74 零 dev-record 写入（round20-dev-record 由 s75 落盘；
    # s74 只产 run-r20）
    s74 = _load(os.path.join("scripts", "s74_calibration_r20_compare.py"),
                "s74_calibration_r20_compare_probe")
    assert not hasattr(s74, "build_dev_record")
    assert hasattr(s74, "build_run")
    # 幂等重跑：main 正常完成（不抛异常）且盘上字节零改动
    path = os.path.join(CAL_DIR, "round20-dev-record.json")
    before = open(path, "rb").read()
    S75.main()
    after = open(path, "rb").read()
    assert before == after
    assert hashing.sha256_file(path).startswith("80e3e9e2")
    # 轮次身份常量（无 wall-clock）
    assert S75.DECLARED_DATE == "2026-09-09"
    assert S75.ROUND_ID == "2026-09-09-r20"
    assert S75.ROUND_LABEL == "r20"
    assert dev_record["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r20.json")
