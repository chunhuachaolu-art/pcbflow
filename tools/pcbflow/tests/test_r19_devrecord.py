"""R19 收口包 B 测试（s72_calibration_r19_devrecord /
round19-dev-record.json）——轮次开发记录生成器（s69 底稿同构）：
轴3 判据侧单变量轮（§4(iii-a) 可操作分辨条款增补=判据节首次变更先例：
增补式+反放宽条款逐字保留+锚断言[content_sha256 97bb4c0f]；渲染零变更
=renders-r14b 四图字节复用；判读指引=observation-guidance-r19.md
8633bda5=r15 基座 d5babc93 机械变换派生；GT/阈值/协议零变更）+ 预注册
假设（axis-plan-r19-criterion-operational）三分判据裁决=marginal（唯一
正式裁决；记录为部分收益、轴3 不判定为胜出）：(s) contact=4≤5 ✓ 且
M1=18/39=0.461538≤0.85 ✓ 且 G1/G2 维持 ✓、唯 M4=0.211111>0.20 未过⇒
supported 未成立；(r) 未落；(m) 两途径均满足（contact ≤7、M4 ≤0.26）
⇒ marginal + 机制观察单列：(iii-a) 落支=残余弃权 8+侵入 6+间隙 0（间
隙支 notes 级判正常路径 4 派次）+援引计数（旗级 (iii-a) 6、分支( 2、
notes 级 10/12）+黑点族 4 vs r18=13 显著回落+黑点转非弃权旗 6+判正常
派次 3+存在性其他 14 vs r18=12（+2 未显著）+ GT 双口径 union 1/13（唯
一命中=prep1-top-i3 R19T-009↔GT-REVC-P1-L1SHORT、containment 1.0、
(iii-a) 侵入支产物）、agreement 0/13 + 类别门 2 条近失（R19T-004×
AP-6-R2LED2、R19T-009×P1-L1NB）+ 代表配置 joint not_met +
in_calibrated_range 恒 False + 派发事故记录（如实、单列：wave-3 重派
重复智能体；4 件 i3 哈希钉死 7941cb00/5591ce98/f4069303/fcc69fb5）+
对照账与下一候选（M 元组四轮并列；comparison_rule 排序 r19 第一、r18
第二、r17 M1=0.88 负向居末；显著收益 0.309891≥0.10 命中；R20=轴3+轴2
组合轮、R21 全组合触发=否、early_stop 快捷通道命中→组合轮仅一个）。

覆盖（14 测试，只读 out/、零子进程/零网络；s72 幂等重跑例外=护栏语义
在案、字节零改动）：
- 防覆盖守卫：overwrite_guard 三态+_commit 写入/幂等/不同字节 FAIL；
- s72 常量与引用件哈希清单（run=e5755a11/guidance=8633bda5/
  prep=e4cf2d3c/axis-plan=b6ec6467/typology=6dadac8d 盘上实测）；
- canonical 确定性（盘上件=同参重建 byte-exact）+轮次身份；
- 字母裁决=marginal 落支与命中途径（crit 布尔/部分收益/M4 门未过）；
- M 元组与 run 记录一致性（构造对照：逐实例重算 M1/M2/M4、rubric 族
  M3、M1 绝对降幅整数交叉相乘）；
- 机制观察（(iii-a) 落支/援引/黑点族/分型）；
- GT 双口径唯一命中与类别门近失；
- 联合门 not_met 与 in_calibrated_range 恒 False；
- 事故记录字段存在+4 件 i3 盘态钉死；
- 下一候选=组合轮判定逻辑（构造：轴序/守门变更时建议跟随变化）；
- R20 建议/R21 触发核对/early_stop 快捷通道；
- 趋势行与预注册链（49 冻结工件逐件实测）；
- 观察/教训/下一目标关键锚；
- s72 幂等重跑+s71 零 dev-record 写入分包边界。
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

ROUND_ID = "2026-09-09-r19"
ROUND_LABEL = "r19"
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


S72 = _load(os.path.join("scripts", "s72_calibration_r19_devrecord.py"),
            "s72_calibration_r19_devrecord")


@pytest.fixture(scope="module")
def dev_record():
    """round19-dev-record 盘上文档（只读）。"""
    path = os.path.join(CAL_DIR, "round19-dev-record.json")
    return json.loads(open(path, encoding="utf-8").read())


@pytest.fixture(scope="module")
def run_doc():
    """calibration-run-r19 盘上文档（唯一事实源；只读）。"""
    return json.loads(open(os.path.join(
        CAL_DIR, "calibration-run-r19.json"), encoding="utf-8").read())


@pytest.fixture(scope="module")
def disk_bytes():
    path = os.path.join(CAL_DIR, "round19-dev-record.json")
    return open(path, "rb").read()


# ---------------------------------------------------------------------------
# 防覆盖守卫（纯函数三态+_commit 落盘语义）
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫：无既有→write；字节等同→idempotent_skip；既有且不同
    →fail；_commit 落盘=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写）。"""
    assert S72.overwrite_guard(None, b"abc") == "write"
    assert S72.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S72.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S72._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"                      # 回读自证
    assert S72._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S72._commit(p, b"abc", "probe")                  # 不同字节→FAIL


# ---------------------------------------------------------------------------
# 常量与引用件哈希清单（fail-closed 实测）
# ---------------------------------------------------------------------------

def test_s72_constants_and_reference_hash_manifest(dev_record):
    """s72 声明常量（无 wall-clock）+三分判据实测锚+引用件哈希清单五件
    （run=e5755a11、guidance=8633bda5、prep=e4cf2d3c、axis-plan=b6ec6467、
    typology=6dadac8d）与盘上实测逐一相等。"""
    assert S72.DECLARED_DATE == DECLARED_DATE
    assert S72.ROUND_ID == ROUND_ID
    assert S72.ROUND_LABEL == ROUND_LABEL
    assert S72.KIND == "tl2_calibration_round19_dev_record"
    assert S72.EVALUATION_DOMAIN == "development"
    # 三分判据实测锚（操作化定义）
    assert (S72.EXPECT_TOP_ABSTAIN_R19, S72.EXPECT_TOP_FLAGS_R19) == (18, 39)
    assert S72.EXPECT_TOP_RATE_R19 == 0.461538
    assert (S72.EXPECT_BOTTOM_ABSTAIN_R19,
            S72.EXPECT_BOTTOM_FLAGS_R19) == (4, 7)
    assert S72.EXPECT_BOTTOM_RATE_R19 == 0.571429
    assert (S72.EXPECT_TOP_R16_BASELINE_LIVE,
            S72.EXPECT_TOP_R16_BASELINE_VALUE) == ("27/35", 0.771429)
    assert (S72.EXPECT_BOTTOM_R16_BASELINE_LIVE,
            S72.EXPECT_BOTTOM_R16_BASELINE_VALUE) == ("12/14", 0.857143)
    assert (S72.EXPECT_CONTACT_R19, S72.EXPECT_CONTACT_R16_BASELINE) == \
        (4, 10)
    assert S72.EXPECT_CONTACT_CHAIN_R13_R16 == {"r13": 8, "r14": 15,
                                                "r15": 5, "r16": 10}
    assert (S72.EXPECT_M1, S72.EXPECT_M2, S72.EXPECT_M3, S72.EXPECT_M4) == \
        (0.461538, 0.571429, 4, 0.211111)
    assert S72.EXPECT_R16_BASELINE_M1_M2_M3_M4 == \
        [0.771429, 0.857143, 12, 0.261904]
    assert S72.EXPECT_R17_MEASURED == {"M1": 0.88, "M2": 0.75, "M3": 8,
                                       "M4": 0.333333}
    assert S72.EXPECT_R18_MEASURED == {"M1": 0.645161, "M2": 0.684211,
                                       "M3": 13, "M4": 0.277778}
    assert S72.EXPECT_TYPE_COUNTS == {"contact": 5, "existence": 13,
                                      "other_layer": 0}
    assert S72.EXPECT_RUBRIC_COUNTS == {"contact": 4,
                                        "existence_blackdot": 4,
                                        "existence_other": 14, "other": 0,
                                        "semantic_confusion": 0}
    assert S72.EXPECT_BRANCH_COUNTS == {"branch1_gap_report": 0,
                                        "branch2_intrusion_report": 6,
                                        "branch3_residual_abstain": 8}
    # 引用件哈希清单：盘上实测逐一命中在案前缀
    entries = dev_record["reference_hash_manifest"]["entries"]
    assert set(entries) == {"run_r19", "guidance_r19", "prep_r19",
                            "axis_experiment_plan",
                            "abstain_typology_r13_r16"}
    for name, (rel, prefix) in S72.REFERENCE_HASH_EXPECTED.items():
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
    轮次身份（r19/2026-09-09/development 域/非门）+run_record_ref 实测
    sha（e5755a11）。"""
    assert hashing.canonical_json_bytes(S72.build_dev_record()) == disk_bytes
    dev = dev_record
    assert dev["kind"] == "tl2_calibration_round19_dev_record"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["evaluation_domain"] == "development"
    assert dev["is_gate"] is False
    # 本轮性质=轴3 判据侧单变量轮+判据节首次变更先例+字节复用双锚
    assert "轴3 判据侧单变量轮" in dev["round_nature"]
    assert "8633bda5" in dev["round_nature"]
    assert "renders-r14b" in dev["round_nature"] and "字节复用" in \
        dev["round_nature"]
    assert "判据节首次变更先例" in dev["round_nature"]
    assert "增补式+反放宽条款逐字保留+锚" in dev["round_nature"]
    assert "in_calibrated_range 恒 False" in dev["round_nature"]
    assert "第十九轮" in dev["round_nature"]
    # run_record_ref=run-r19 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["path_rel"] == \
        "out/v3-tl2/calibration/calibration-run-r19.json"
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r19.json")
    assert dev["run_record_ref"]["sha256"].startswith("e5755a11")


# ---------------------------------------------------------------------------
# 字母裁决=marginal（落支与命中途径）
# ---------------------------------------------------------------------------

def test_dev_record_letter_marginal_branches_and_partial_benefit(
        dev_record, run_doc):
    """字母裁决节与 run-r19 逐字镜像（唯一正式裁决=marginal）：(s) 三真
    一假（M4 门未过）；(r) 假；(m) 两途径真；部分收益/不判胜出锚；守门
    G1/G2 维持。"""
    dev, run = dev_record, run_doc
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    ht = dev["hypothesis_test_i"]
    m = ht["measurement"]
    assert ht["hypothesis_id"] == "axis-plan-r19-criterion-operational"
    assert ht["verdict"] == "marginal"
    assert m["verdict"] == "marginal"
    # (s) supported：contact ≤5 ✓、M1 ≤0.85 ✓、G1/G2 ✓、唯 M4 ≤0.20 ✗
    assert m["crit_supported_contact_le_5"] is True
    assert m["crit_supported_m1_le_0_85"] is True
    assert m["crit_supported_m4_le_0_20"] is False
    # (r) reject：未落
    assert m["crit_reject_contact_ge_8_and_m4_above_0_26"] is False
    # (m) marginal：两途径均满足
    assert m["crit_marginal_contact_le_7"] is True
    assert m["crit_marginal_m4_le_0_26"] is True
    assert m["letter_branch"].startswith("(m)")
    assert "contact ≤7（实测 4）" in m["letter_branch"]
    assert "M4 ≤0.26（实测 0.211111）" in m["letter_branch"]
    assert "记录为部分收益" in m["letter_branch"]
    # 实测主度量与附加门
    assert m["contact_family_abstain_flags_rubric_r19"] == 4
    assert m["contact_r16_baseline_registered"] == 10
    assert m["contact_r16_baseline_live_replay"] == {"r13": 8, "r14": 15,
                                                     "r15": 5, "r16": 10}
    assert m["top_abstain_rate_r19"] == 0.461538
    assert m["m4_top_rate_range_r19"] == 0.211111
    assert "18/39" in m["top_abstain_rate_r19_arithmetic"]
    # 描述性结论非因果证明（verdict_text 锚）
    vt = ht["verdict_text"]
    assert "唯一正式裁决" in vt and "不判定为胜出" in vt
    assert "只描述不断言" in vt and "不凌驾、不改写字母裁决" in vt
    # 守门独立单列（均维持、不触发出局）
    assert m["guard_channel"]["g1_ok"] is True
    assert m["guard_channel"]["g2_guard_ok"] is True
    assert m["guard_channel"]["guards_ok"] is True
    g12 = ht["mechanism_observation"]["guards_g1_g2"]["counts"]
    assert g12["axis_early_stop_triggered"] is False
    assert g12["g2_geometry_gate_r18"] == 0
    assert g12["g2_geometry_gate_r19"] == 0


# ---------------------------------------------------------------------------
# M 元组与 run 记录一致性（构造对照）
# ---------------------------------------------------------------------------

def test_dev_record_m_tuple_consistency_constructed(dev_record, run_doc):
    """M 元组构造对照：从 run-r19 内嵌实例记录重算 M1（18/39）/M2（4/7）/
    M4（极差）/M3（rubric 族），与 s72 锚、run 对照账、dev 对照账逐一相
    等；M1 绝对降幅 0.309891 与 r18 参照 0.126268 整数复算一致。"""
    dev, run = dev_record, run_doc
    inst = run["instances"]
    top = ("top-i1", "top-i2", "top-i3")
    bottom = ("bottom-i1", "bottom-i2", "bottom-i3")
    tf = sum(inst[n]["combined"]["flag_count"] for n in top)
    ta = sum(inst[n]["combined"]["abstain_count"] for n in top)
    bf = sum(inst[n]["combined"]["flag_count"] for n in bottom)
    ba = sum(inst[n]["combined"]["abstain_count"] for n in bottom)
    assert (ta, tf) == (18, 39)
    assert (ba, bf) == (4, 7)
    assert round(ta / tf, 6) == 0.461538
    assert round(ba / bf, 6) == 0.571429
    # M4=top 逐实例弃权率先 6 位取率再取极差（构造复算）
    rates = [inst[n]["combined"]["abstain_rate"] for n in top]
    assert round(max(rates) - min(rates), 6) == 0.211111
    assert (max(rates), min(rates)) == (0.6, 0.388889)
    # M3 槽位=冻结件黑点族 rubric 口径（构造：族计数表重取）
    counts = run["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]["rubric_families"]["counts"]
    assert counts["existence_blackdot"] == 4 == S72.EXPECT_M3
    # run 对照账与 dev 对照账与 s72 锚三方一致
    ledger = run["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]
    want = {"M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111}
    assert ledger["r19_measured"]["M1"] == want["M1"]
    assert ledger["r19_measured"]["M2"] == want["M2"]
    assert ledger["r19_measured"]["M3"] == want["M3"]
    assert ledger["r19_measured"]["M4"] == want["M4"]
    assert dev["axis_experiment_ledger"]["this_round_measured"] == want
    assert (S72.EXPECT_M1, S72.EXPECT_M2, S72.EXPECT_M3, S72.EXPECT_M4) == \
        (want["M1"], want["M2"], want["M3"], want["M4"])
    # 四轮并列（r16 基线/r17 轴1/r18 轴2/r19 轴3）与在案行一致
    rows = dev["axis_experiment_ledger"]["cross_round_status"]["measured_rows"]
    assert rows["r16_baseline"] == {"M1": 0.771429, "M2": 0.857143,
                                    "M3": 12, "M4": 0.261904}
    assert rows["r17_axis1"] == S72.EXPECT_R17_MEASURED == \
        ledger["r17_axis1_row"]
    assert rows["r18_axis2"] == S72.EXPECT_R18_MEASURED == \
        ledger["r18_axis2_row"]
    assert rows["r19_axis3"] == want
    # M1 绝对降幅（6 位取率后作差，构造复算）与整数交叉相乘方向
    assert round(0.771429 - 0.461538, 6) == 0.309891
    assert ledger["significant_benefit_vs_r16"]["r19_m1_absolute_drop"] == \
        0.309891
    assert ledger["significant_benefit_vs_r16"]["r18_drop_reference"] == \
        0.126268
    assert (27 * 39 - 18 * 35) * 1_000_000 >= 100_000 * 35 * 39  # ≥0.10
    # r16 基线 live 重放（同一聚合逻辑对 run-r16 内嵌输入）
    run16 = json.loads(open(os.path.join(
        CAL_DIR, "calibration-run-r16.json"), encoding="utf-8").read())
    i16 = run16["instances"]
    assert (sum(i16[n]["combined"]["abstain_count"] for n in top),
            sum(i16[n]["combined"]["flag_count"] for n in top)) == (27, 35)
    assert (sum(i16[n]["combined"]["abstain_count"] for n in bottom),
            sum(i16[n]["combined"]["flag_count"] for n in bottom)) == (12, 14)


# ---------------------------------------------------------------------------
# 机制观察（(iii-a) 落支/援引/黑点族/分型）
# ---------------------------------------------------------------------------

def test_dev_record_mechanism_observations_iiia_blackdot_typology(
        dev_record, run_doc):
    """机制观察单列：(iii-a) 旗级落支=残余弃权 8+侵入 6+间隙 0（间隙支
    notes 级判正常 4 派次）；援引计数（旗级 (iii-a) 6、分支( 2、notes 级
    10/12、未援引 2 派次）；黑点族 4 vs r18=13+转非弃权 6+判正常 3；存
    在性其他 14 vs r18=12（+2 未显著）；top 分型 5/13/0。"""
    dev, run = dev_record, run_doc
    mo = run["hypothesis_test"]["mechanism_observation"]
    # 镜像完整（dev 不复制 mo、但 directional/honest 转述锚在案）
    assert dev["hypothesis_test_i"]["mechanism_observation"] == mo
    iiia = mo["iiia_branch_observation"]
    assert iiia["branch_counts_flag_level"] == S72.EXPECT_BRANCH_COUNTS
    assert iiia["branch1_notes_level_dispatches"] == 4
    cc = iiia["citation_counts"]
    assert cc["flag_level_iiia_literal"] == 6
    assert cc["flag_level_branch_literal"] == 2
    assert cc["notes_level_iiia"] == 10
    assert len(cc["notes_level_iiia_sources"]) == 10
    assert cc["notes_level_non_citing"] == ["applied-bottom-i1",
                                            "applied-top-i3"]
    bdt = mo["black_dot_tracking"]
    assert bdt["all_abstain"] is True
    assert bdt["by_instance"] == S72.EXPECT_BLACK_DOT_BY_INSTANCE
    assert len(bdt["black_dot_flags"]) == 4
    assert bdt["blackdot_to_non_abstain_count"] == 6
    assert len(bdt["black_dot_non_abstain_flags"]) == 6
    assert bdt["judged_normal_dispatches"]["count"] == 3
    # 显著回落对照（r18=13）与弃权转移对照（存在性其他 14 vs 12）转述锚
    obs_text = "\n".join(dev["directional_observation_vs_r16"])
    assert "黑点族（rubric 口径）=4 vs r18=13" in obs_text
    assert "存在性其他=14 vs r18=12" in obs_text
    ecl = mo["experiment_comparison_ledger"]
    assert ecl["family_counts_vs_r18"]["existence_blackdot"] == \
        {"r18_registered": 13, "r19_measured": 4}
    assert ecl["family_counts_vs_r18"]["existence_other"]["note"].startswith(
        "对照 r18 在案存在性其他 12")
    # top 弃权构成分型（18 旗；r16/r17/r18 参照）
    ty = mo["top_abstain_typology"]
    assert ty["type_counts"] == S72.EXPECT_TYPE_COUNTS
    assert ty["top_abstain_flags_total"] == 18 and len(ty["rows"]) == 18
    assert ty["r18_reference_counts_live"] == {"contact": 8, "existence": 12,
                                               "other_layer": 0}
    # 机制方向转述：侵入支产物旗命中 GT（唯一命中）
    assert "R19T-009↔GT-REVC-P1-L1SHORT" in obs_text
    assert "侵入支" in obs_text


# ---------------------------------------------------------------------------
# GT 双口径唯一命中+类别门近失
# ---------------------------------------------------------------------------

def test_dev_record_gt_dual_unique_hit_and_category_near_misses(
        dev_record, run_doc):
    """GT 双口径：union 1/13（唯一命中=prep1-top-i3 R19T-009↔GT-REVC-
    P1-L1SHORT、containment 1.0、(iii-a) 侵入支产物）、agreement 0/13；
    类别门 2 条近失如实（R19T-004×AP-6-R2LED2、R19T-009×P1-L1NB 近邻交
    叠类别不符）；courtyard 追踪 r19=0；诊断结果镜像代表配置口径。"""
    dev, run = dev_record, run_doc
    dual = run["gt_match_dual"]
    assert (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) == (1, 0, 13)
    assert dual["union"]["gt_ids"] == ["GT-REVC-P1-L1SHORT"]
    assert dual["union"]["gt_recall_union"] == 0.076923
    hit_gt = [p for p in dual["per_gt"]
              if p["gt_id"] == "GT-REVC-P1-L1SHORT"][0]
    hit = hit_gt["hits"][0]
    assert (hit["flag_id"], hit["instance"], hit["state"]) == \
        ("R19T-009", "top-i3", "prep1")
    assert hit["containment"] == 1.0
    # 诊断结果镜像（代表配置口径）
    dr = dev["diagnostic_result"]
    assert dr["gt_match_dual"] == {"union": dict(dual["union"]),
                                   "agreement": dict(dual["agreement"])}
    assert dr["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dr["abstain_rate_total"] == 0.428571
    assert dr["gt_recall_total"] == 0.0
    assert dr["seed_match_rate_total"] == 0.0
    # 类别门 2 条近失（几何门 0→0 延续；通道链 r19=2）
    ca = run["channel_attribution"]
    near = ca["channel_2_category_gate"]["r19_category_mismatch_entries"]
    assert {(e["flag_id"], e["gt_id"]) for e in near} == \
        {("R19T-004", "GT-REVC-AP-6-R2LED2"),
         ("R19T-009", "GT-REVC-P1-L1NB")}
    assert len(ca["channel_1_geometry_gate"][
        "r19_area_ratio_rejected_entries"]) == 0
    chain = ca["gate_chain_since_r6"][
        "category_gate_category_mismatch_by_round"]
    assert chain["r18"] == 0 and chain["r19"] == 2
    assert run["courtyard_tracking"]["courtyard_matches_r19"] == 0
    # 转述锚（directional 观察如实引用近失条目）
    obs_text = "\n".join(dev["directional_observation_vs_r16"])
    assert "R19T-004×GT-REVC-AP-6-R2LED2" in obs_text
    assert "R19T-009×GT-REVC-P1-L1NB" in obs_text
    assert "近邻交叠类别" in obs_text


# ---------------------------------------------------------------------------
# 联合门与 in_calibrated_range 恒 False
# ---------------------------------------------------------------------------

def test_dev_record_joint_gate_and_in_calibrated_range_false(
        dev_record, run_doc):
    """联合门：代表配置（top-i1+bottom-i2 双唯一）joint not_met、连续=0、
    criteria 分项（gt_recall/seed 未达、gt_count/abstain 入线）；
    in_calibrated_range 恒 False（run 与 compliance 双处）；零旗标派次=2
    （bottom-i3 两板）。"""
    dev, run = dev_record, run_doc
    comp = run["compliance_representative"]
    assert run["representative_configuration"]["members"] == \
        {"top": "top-i1", "bottom": "bottom-i2"}
    assert run["representative_configuration"]["selection"]["top"][
        "tie"] is False
    assert run["representative_configuration"]["selection"]["bottom"][
        "tie"] is False
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
    # 趋势行本轮节点与连续计数
    trend = dev["joint_evaluation_trend"]
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert trend["consecutive_met_count_now"] == 0
    assert "不得写成已达成" in trend["note"]
    # 零旗标派次=2（bottom-i3 两板；item 5 None 口径）
    assert run["reader"]["zero_flag_parts"]["parts"] == \
        S72.EXPECT_ZERO_FLAG_PARTS
    assert run["view_layer"]["bottom"]["abstain_rate"]["by_instance"][
        "bottom-i3"] is None
    assert run["view_layer"]["bottom"]["abstain_rate"]["median"] is None
    # honest_conclusion 恒 False 锚与不冒充留出
    assert "in_calibrated_range 恒 False" in dev["honest_conclusion"]
    assert "不得冒充留出" in dev["honest_conclusion"]


# ---------------------------------------------------------------------------
# 派发事故记录（如实、单列）
# ---------------------------------------------------------------------------

def test_dispatch_incident_record_fields_and_pinned_i3(dev_record, run_doc):
    """事故记录字段存在：事件（wave-3 重派重复智能体 2×top-i3+2×bottom-i3
    并发同实例 ID）、处置（后完成者未读取旧文件内容前提下删除重写、先完
    成者重复输出废弃）、盘上终态（一套自洽 i3 输出：top 跨板连续
    R19T-001..010、bottom 0 旗标）、4 件 i3 哈希钉死（盘上实测逐一命中）、
    教训（重派前必须核对目标实例唯一性）、单列角色。"""
    dev, run = dev_record, run_doc
    inc = dev["dispatch_incident_record"]
    assert inc["declared_date"] == DECLARED_DATE
    assert "wave-3" in inc["event"] and "重复智能体" in inc["event"]
    assert "2×top-i3+2×bottom-i3" in inc["event"]
    assert "并发同实例 ID" in inc["event"]
    assert "未读取旧文件内容前提下删除重写" in inc["resolution"]
    assert "先完成" in inc["resolution"] and "废弃" in inc["resolution"]
    assert "一套完整自洽 i3 输出" in inc["final_disk_state"]
    assert "R19T-001..010" in inc["final_disk_state"]
    assert "bottom 0 旗标" in inc["final_disk_state"]
    assert inc["lesson"] == ("重派前必须核对目标实例唯一性（编排侧纪律；"
                             "后续轮次重派/替换操作须先核对该实例无并发任"
                             "务）")
    assert inc["lesson"].startswith("重派前必须核对目标实例唯一性")
    # 4 件 i3 盘态钉死（记录值=盘上实测=run 登记，三方逐一相等）
    assert inc["pinned_i3_prefixes"] == S72.I3_PINNED_PREFIXES
    for key, prefix in S72.I3_PINNED_PREFIXES.items():
        live = _sha(S72.REL_RAW_I3[key])
        assert live.startswith(prefix)
        assert inc["pinned_i3_full_sha256"][key] == live
        assert run["reader"]["raw_files"][key]["sha256"].startswith(prefix)
    # top-i3 跨板连续编号（终态实测指纹）与 bottom-i3 零旗标
    cont = run["reader"]["dispatch_mode"]["flag_id_continuity"]
    assert "R19T-001..004" in cont["top-i3"]
    assert "R19T-005..010" in cont["top-i3"]
    assert "跨板连续" in cont["top-i3"]
    assert "applied 0 旗；prep1 0 旗" in cont["bottom-i3"]
    # 单列角色（不改判读/不改字母/不进度量）
    assert "不改判读产" in inc["role"] and "不改字母裁决" in inc["role"]
    assert "不进任何度量" in inc["role"]
    # flag_production note 转述事故（如实入账）
    assert "dispatch_incident_record" in dev["flag_production"]["note"]


# ---------------------------------------------------------------------------
# 下一候选=组合轮判定逻辑（冻结规则应用）
# ---------------------------------------------------------------------------

def test_combination_decision_application_r20_r21_early_stop(
        dev_record, run_doc):
    """组合决策应用节：R20 建议=轴3+轴2 组合轮（guidance=§5B+§4(iii-a)
    合成、renders-r14b 零仪器变更、12 派次、须预注册）；R21 全组合触发
    核对=否（轴1 M1=0.88 负向）；early_stop 快捷通道命中（0.461538≤0.60
    →组合轮仅一个）；冻结规则原文引用在案。"""
    dev, run = dev_record, run_doc
    app = dev["combination_decision_application"]
    # R20 建议
    r20 = app["r20_recommendation"]
    assert r20["axes"] == ["r19_axis3", "r18_axis2"]
    assert r20["round"] == "R20"
    assert "轴3+轴2 组合轮" in r20["combination"]
    assert "§5B+§4(iii-a) 合成" in r20["guidance"]
    assert "renders-r14b" in r20["render"] and "零仪器变更" in r20["render"]
    assert r20["blind_reads"] == 12
    assert r20["preregistration_required"] is True
    assert "不预写结果" in r20["note"] or "不预写结论" in r20["note"]
    # R21 全组合触发核对=否（三轴皆正不成立：轴1 负向）
    r21 = app["r21_full_combination_trigger"]
    assert r21["met"] is False
    assert r21["per_axis_positive"] == {"r17_axis1": False,
                                        "r18_axis2": True,
                                        "r19_axis3": True}
    assert "三轴均各自正收益" in r21["check"]
    assert "不劣于 r16 基线 0.771429" in r21["check"]
    assert "三轴均各自正收益" in r21["rule_quote"]
    # early_stop 快捷通道命中（组合轮仅一个、R21 不做）
    sc = app["early_stop_shortcut"]
    assert sc["triggered"] is True
    assert sc["best_single_axis_m1"] == 0.461538
    assert "0.60" in sc["check"] and "R21 不做" in sc["check"]
    assert "0.60" in sc["rule_quote"] and "不铺全组合" in sc["rule_quote"]
    # 排序应用与 run 对照账逐一相等（r19 第一、r18 第二、r17 末位）
    rk = run["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]["ranking_by_comparison_rule"]
    assert app["ranking_application"]["eligible_sorted"] == \
        ["r19_axis3", "r18_axis2", "r17_axis1"]
    assert rk["ranking_order_best_first"] == ["r19_axis3", "r18_axis2",
                                              "r16_baseline", "r17_axis1"]
    assert rk["r19_rank"] == 1
    assert "非守门出局" in app["ranking_application"]["note"]
    assert "非惩罚性操作" in \
        app["ranking_application"]["r17_last_note"]
    # 冻结件引用与不预写结论锚
    assert app["frozen_plan_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json")
    assert app["frozen_plan_ref"]["sha256"].startswith("b6ec6467")
    assert "不预写结论" in app["status"]
    assert app["inputs"]["r16_baseline_m1"] == 0.771429
    assert app["inputs"]["guards"] == {"r17_axis1": True, "r18_axis2": True,
                                       "r19_axis3": True}


def test_next_candidate_pure_function_constructed_orderings():
    """下一候选纯函数构造对照：实际轴序→r19+r18；轴序变更（r17 最优）
    →建议跟随变化为 r19+r17；r19 守门破坏→r18+r17；过守门轴不足两轴→
    ValueError；R21 触发构造（全正=True）与快捷通道 0.60 边界（6 位定点
    整数交叉相乘）；排序键 M2→M3→M4 逐级 tie-break。"""
    rows = {"r17_axis1": S72.EXPECT_R17_MEASURED,
            "r18_axis2": S72.EXPECT_R18_MEASURED,
            "r19_axis3": {"M1": S72.EXPECT_M1, "M2": S72.EXPECT_M2,
                          "M3": S72.EXPECT_M3, "M4": S72.EXPECT_M4}}
    guards = {"r17_axis1": True, "r18_axis2": True, "r19_axis3": True}
    # 实际数据：r19 最优、r18 次之（与 dev-record 在案建议一致）
    assert S72.next_stage2_candidate(rows, guards)["r20_axes"] == \
        ["r19_axis3", "r18_axis2"]
    # 构造：轴序变更（r17 M1 变为最优）→建议跟随变化（r19+r17）
    rows_swapped = dict(rows)
    rows_swapped["r17_axis1"] = {"M1": 0.30, "M2": 0.10, "M3": 1,
                                 "M4": 0.05}
    assert S72.next_stage2_candidate(rows_swapped, guards)["r20_axes"] == \
        ["r17_axis1", "r19_axis3"]
    # 构造：r19 守门破坏→只从过守门轴取（r18+r17）
    guards_broken = dict(guards)
    guards_broken["r19_axis3"] = False
    assert S72.next_stage2_candidate(rows, guards_broken)["r20_axes"] == \
        ["r18_axis2", "r17_axis1"]
    # 过守门轴不足两轴→ValueError（组合轮前提不成立）
    with pytest.raises(ValueError):
        S72.next_stage2_candidate(rows, {"r19_axis3": True,
                                         "r17_axis1": False,
                                         "r18_axis2": False})
    # R21 全组合触发：实际（轴1 负向）=False；构造全正=True
    assert S72.full_combination_trigger(rows, 0.771429) is False
    rows_positive = {k: dict(v) for k, v in rows.items()}
    rows_positive["r17_axis1"] = {"M1": 0.70, "M2": 0.75, "M3": 8,
                                  "M4": 0.333333}
    assert S72.full_combination_trigger(rows_positive, 0.771429) is True
    # 快捷通道边界：M1 恰 0.60 命中、0.600001 未命中（整数交叉相乘）
    assert S72.strong_single_axis_shortcut(0.6) is True
    assert S72.strong_single_axis_shortcut(0.461538) is True
    assert S72.strong_single_axis_shortcut(0.600001) is False
    # 排序键字典序 tie-break（M1 同值依次比 M2→M3→M4）
    assert S72.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3,
                                    "M4": 0.1}) < \
        S72.comparison_sort_key({"M1": 0.5, "M2": 0.3, "M3": 3, "M4": 0.1})
    assert S72.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3,
                                    "M4": 0.1}) < \
        S72.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 4, "M4": 0.1})
    assert S72.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3,
                                    "M4": 0.1}) < \
        S72.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3, "M4": 0.2})
    # 四元组输入兼容（tuple/dict 同键）
    assert S72.comparison_sort_key((0.5, 0.2, 3, 0.1)) == \
        S72.comparison_sort_key({"M1": 0.5, "M2": 0.2, "M3": 3, "M4": 0.1})


# ---------------------------------------------------------------------------
# 趋势行与预注册链
# ---------------------------------------------------------------------------

def test_dev_record_trend_and_preregistration_chain(dev_record, run_doc,
                                                    disk_bytes):
    """联合评价趋势 r5–r19 逐轮表（r19 行=本轮实测+source sha e5755a11）
    +预注册链=run-r19 冻结工件逐件实测（与 run 登记一致）+链注锚+引用实
    测一致（canonical 链件哈希复核）。"""
    dev, run = dev_record, run_doc
    trend = dev["joint_evaluation_trend"]
    rounds = [r["round"] for r in trend["by_round"]]
    assert rounds == ["r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12",
                      "r13", "r14", "r15", "r16", "r17", "r18", "r19"]
    last = trend["by_round"][-1]
    assert last["flag_count_total"] == 14
    assert last["abstain_count_total"] == 6
    assert last["abstain_rate_total"] == 0.428571
    assert last["joint_evaluation"] == "not_met"
    assert last["gt_recall_total"] == 0.0
    assert last["seed_match_rate_total"] == 0.0
    assert last["source"]["path_rel"].endswith("calibration-run-r19.json")
    assert last["source"]["sha256"].startswith("e5755a11")
    assert trend["consecutive_met_count_now"] == 0
    assert "22/46=0.478261" in trend["aggregation_scope_note"]
    # 预注册链=run 冻结工件逐件实测（fail-closed 与登记一致）
    chain = dev["preregistration_chain"]
    for item in run["preregistration"]["frozen_artifacts"]:
        assert chain[item["role"]] == {"path_rel": item["path_rel"],
                                       "sha256": item["sha256"]}
        assert chain[item["role"]]["sha256"] == _sha(item["path_rel"])
    note = dev["preregistration_chain_note"]
    for anchor in ("b6ec6467", "e4cf2d3c", "8633bda5", "d5babc93",
                   "97bb4c0f", "298bc620", "d7284259", "b63771f9",
                   "e5755a11", "62343380", "1f20554a", "选择收益最大的继续",
                   "7941cb00", "R19T-001..010", "判据侧"):
        assert anchor in note, anchor


# ---------------------------------------------------------------------------
# 观察/教训/下一目标关键锚
# ---------------------------------------------------------------------------

def test_dev_record_observations_notes_and_next_targets(dev_record):
    """方向性观察（视角层三分列/聚合落点/零旗标对照/通道链）、notes（判
    据收窄非放松/度量教训/事故单列）、honest_conclusion（marginal 部分收
    益/四元组/排序/显著收益/R20/R21/非因果）、next_iteration_targets（R20
    组合轮/R21 触发核对/轴1 登记/先例归档/留出时机）关键锚。"""
    dev = dev_record
    obs = "\n".join(dev["directional_observation_vs_r16"])
    for need in ("12→12", "49→50→46", "18/39=0.461538", "4/7=0.571429",
                 "0.211111", "0.309891", "0.09064",
                 "marginal", "记录为部分收益", "27/35=0.771429",
                 "0.454545/0.388889/0.6", "0.75/0.333333/None",
                 "0.416667", "bottom-i3 两板", "improved",
                 "GT-REVC-P1-L1SHORT", "containment 1.0", "侵入支",
                 "agreement=0/13", "单实例命中不稳定", "几何门",
                 "类别门 0→2", "残余弃权支（第三支）=8", "间隙支",
                 "notes 级 4 派次", "旗级 location_evidence 含「(iii-a)」",
                 "10/12", "applied-bottom-i1/applied-top-i3",
                 "存在性其他=14 vs r18=12", "接触性 11→8",
                 "存在性 15→14", "§4(i)", "§5A 显式援引 4/6",
                 "重派重复智能体", "7941cb00/5591ce98/f4069303/fcc69fb5",
                 "courtyard 类旗标 6 条", "reroute 类 3 条",
                 "等长|蛇形"):
        assert need in obs, need
    # notes：判据收窄非放松+反放宽条款+度量教训+事故单列+裁决纪律
    notes = "\n".join(dev["notes"])
    for need in ("收窄而非放松", "反放宽条款原文一字不松", "可辨认证据",
                 "M3 槽位", "rubric 机械套用", "增补式+反放宽逐字保留+锚断言",
                 "dispatch_incident_record", "重派前必须核对目标实例唯一性",
                 "唯一正式裁决", "不得回溯改判既往轮次", "非因果证明",
                 "drift_confound_note", "precision/FPR"):
        assert need in notes, need
    # honest_conclusion：marginal 部分收益+对照账+下一候选+双口径
    hc = dev["honest_conclusion"]
    for need in ("marginal", "记录为部分收益", "轴3 不判定为胜出",
                 "contact ≤7（实测 4）", "M4 ≤0.26（实测 0.211111）",
                 "=0.211111>0.20", "(0.461538, 0.571429, 4, 0.211111)",
                 "0.461538 < R18", "0.309891≥0.10",
                 "R20=轴3+轴2 组合轮", "§5B+§4(iii-a) 合成",
                 "三轴皆正不成立", "0.461538≤0.60", "R21 不做",
                 "非因果证明", "not_met", "0.428571", "in_calibrated_range "
                 "恒 False", "gt-audit-r1", "黑点族=4 vs r18=13",
                 "判正常派次 3", "wave-3", "判据节首次变更先例",
                 "0.126268"):
        assert need in hc, need
    # next_iteration_targets：R20/R21/轴1/先例/留出
    nxt = "\n".join(dev["next_iteration_targets"])
    assert len(dev["next_iteration_targets"]) == 5
    for need in ("R20=轴3+轴2 组合轮", "§5B+§4(iii-a) 合成",
                 "renders-r14b", "零仪器变更", "12 派次", "prep-record 预注"
                 "册", "不预写结论", "R21 全组合触发条件核对=否",
                 "轴1 r17 M1=0.88", "0.771429", "strong_single_axis_"
                 "shortcut", "0.461538≤0.60", "非守门出局",
                 "增补式+反放宽条款逐字保留+锚断言", "97bb4c0f",
                 "留出集时机", "须用户拍板", "收敛未宣告",
                 "连续 2 轮达标+人工批准", "in_calibrated_range 恒 False",
                 "gt-audit-r1", "HOLDOUT-PLAN.md", "a4b80193",
                 "holdout-candidates-r1"):
        assert need in nxt, need
    assert "R19T-009↔GT-REVC-P1-L1SHORT" in nxt
    # 域声明引用（run basis_quote 承接+dev 附加句）
    assert "第 19 轮迭代" in dev["domain_basis_quote"]
    assert "不得冒充留出证据" in dev["domain_basis_quote"]
    assert dev["gt_audit_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/gt-audit-r1.json")


# ---------------------------------------------------------------------------
# s72 幂等重跑与分包边界
# ---------------------------------------------------------------------------

def test_s72_rerun_idempotent_and_package_boundary(dev_record, disk_bytes):
    """s72 重跑语义：build_dev_record 同参重建 byte-exact；main 幂等重跑
    （round19-dev-record 已存在且字节等同→零覆写、字节零改动）；s71 零
    dev-record 写入分包边界（只产 run-r19）。"""
    # 同参重建（纯函数）与盘上产物逐字节一致
    assert hashing.canonical_json_bytes(S72.build_dev_record()) == disk_bytes
    # 分包边界：s71 零 dev-record 写入（round19-dev-record 由 s72 落盘；
    # s71 只产 run-r19）
    s71 = _load(os.path.join("scripts", "s71_calibration_r19_compare.py"),
                "s71_calibration_r19_compare_probe")
    assert not hasattr(s71, "build_dev_record")
    assert hasattr(s71, "build_run")
    # 幂等重跑：main 正常完成（不抛异常）且盘上字节零改动
    path = os.path.join(CAL_DIR, "round19-dev-record.json")
    before = open(path, "rb").read()
    S72.main()
    after = open(path, "rb").read()
    assert before == after
    assert hashing.sha256_file(path).startswith("0e2fdd69")
    # 轮次身份常量（无 wall-clock）
    assert S72.DECLARED_DATE == "2026-09-09"
    assert S72.ROUND_ID == "2026-09-09-r19"
    assert S72.ROUND_LABEL == "r19"
    assert dev_record["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r19.json")
