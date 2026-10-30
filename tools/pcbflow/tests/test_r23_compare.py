"""R23 执行包测试（s82_calibration_r23_compare / calibration-run-r23）——
单变量报告框收敛归因轮（输出格式/报告纪律轴；r20「随指引落盘固化」先例
同型；本轮=第二十三轮；执行 round22-dev-record 下一候选建议 (b)+用户
2026-09-10 拍板）：判读指引=observation-guidance-r23.md（866b0157 锚、
由 r19 基座 8633bda5 机械变换派生[s48/s54/s63/s67/s70 先例同型]、§6 增
补报告框收敛条款随指引落盘固化、§6 示例前缀 R23T-/R23B- 即落盘原文=派
发命名与指引一致）、渲染零变更=renders-r14b 四图字节复用、GT/阈值/协议
零变更、changed_variables=1（§6 条款单变量=报告框几何纪律、非判据收紧
亦非放宽；实例群重抽=轮际固有混杂非实验操作）+【跳号声明延续】r21=冻结
预留全组合条件位永久留空（r22 跳号声明在案）。预注册假设（r22-g2-
bifurcation-frame-box-hygiene-attribution）归因三支判据轮后裁决=
confounded（唯一正式裁决）：(c) 支命中 confounded_g2_positive_in_band
（G2=top 几何门面积比出局条目 r19=0→r22=2→r23=1 仍>0 未清零；且 M1=
0.484848（16/33）落复制带 [0.361538, 0.561538] 内）——框宽非（唯一）主
因，归因转向（判据内容/实例群/其他输出侧因素混杂主导）；机制侧如实分
列：r22 型 silk 宽框出局条目（R22T-002/013，area_ratio≈16.4）未再现=
条款对目标起效、但新出局条目 R23T-004=other_advisory 合并铜块（11.
458680>10、机制不同）=几何门未全局清零；G1=bottom courtyard 非弃权
0/0/0 维持；guidance-r19 胜出记录维持 conditional/double-entry 现状、
复制未达成不升级；r22 字母=regressed 维持不改写。R23 四元组
(0.484848, 0.571429, 8, 0.520833)（M1=top 16/33、M2=bottom 8/14、M3=
黑点族 rubric 口径 8、M4=top 极差 0.520833）；机制观察单列：rubric 三族
contact 8/existence_blackdot 8/existence_other 7（+semantic_confusion 1；
r13–r16 132 条重放对拍逐一相等；contact 链 8/15/5/10）对照 r19（4/4/14）
与 r22（2/4/12）；黑点弃权 8（top-i1 4+bottom-i1 4、逐实例分旗）+黑点
转非弃权旗 8+判正常派次 2；援引分记（旗级 §5B/(iii-a)/分支( 全 0、
notes 级 §5B=0/12、(iii-a)=4/12、§6 条款=6/12；r19 基线=旗级 6+2、
notes 10/12 在案；r22=旗级全 0、notes 6/12 在案）+七行对照账（r16
0.771429/0.857143/12/0.261904、r17 0.88/0.75/8/0.333333、r18
0.645161/0.684211/13/0.277778、r19 0.461538/0.571429/4/0.211111、r20
0.636364/0.285714/6/0.25、r22 0.390244/0.2/4/0.104545、r23 0.484848/
0.571429/8/0.520833）——r23 与 r20/r22 均 G 守门破坏不入排序（资格门剔
除）、排序不变=r19_axis3 第一；M4 三样本单列（0.211111/0.104545/
0.520833，不进字母、不合并分布）+ GT 双口径 union=2/13=0.153846（两 GT
条目均单实例命中：GT-REVC-P1-R4J3 R23T-002+GT-REVC-P1-L1SHORT R23T-011；
agreement=0/13——r22 双实例一致命中未复现、里程碑维持）+ 本轮无零旗格
（12 格全部≥1 旗、None 口径未触发）+ in_calibrated_range 恒 False +
development 域。

覆盖（14 测试，只读 out/、零子进程/零网络/零写盘）：
- 输入核验 fail-closed：12 件 reader-raw-r23 合法解析+实例旗数/弃权
  记账；缺文件→OSError、_fail→SystemExit、视角后缀缺失→ValueError；
  12 件盘态钉死前缀；FROZEN_SHA256 全锚实测一致；
- rubric 链重放对拍：r13–r16 132 条弃权旗重放（per_flag_total=132、
  blackdot 9/14/8/12、contact 8/15/5/10）+classify 优先级单元+r23 家族
  计数（8/8/7/1/0 与登记一致）；
- M 元组：_m_tuple_6dp 定点键+构造小样例 round_view_aggregate/_median3/
  M4 极差+r16 基线双侧 live 复算（27/35、12/14、courtyard 0/0/0）；
- 归因三支边界：adjudicate_attribution 纯函数构造用例——replicated_
  hygiene（G2=0+带内+G1 维持）、confounded（带内但 G2>0=本轮实况）、
  perturbed（M1 出带）、guard_violation（G1 破坏=支序最高）与带宽端点；
- 守卫与确定性：overwrite_guard 三态+_commit 落盘语义；run-r23 盘上件
  canonical byte 与重建一致+轮次身份+verdict=confounded+落支
  confounded_g2_positive_in_band+M 元组+r19/r22 基准元组+
  changed_variables=1；GT 双口径 union=2/13+agreement=0+joint not_met+
  in_calibrated_range 恒 False+七行对照账+排序（r20/r22/r23 资格门剔
  除、r19_axis3 第一）+M4 三样本单列。
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

ROUND_ID = "2026-09-10-r23"
ROUND_LABEL = "r23"
DECLARED_DATE = "2026-09-10"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")


def _load_s82():
    path = os.path.join(REPO, "scripts", "s82_calibration_r23_compare.py")
    spec = importlib.util.spec_from_file_location("s82_calibration_r23",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S82 = _load_s82()


@pytest.fixture(scope="module")
def run_doc():
    """run-r23 文档内存构建（纯函数；只读输入、零写盘）。"""
    return S82.build_run()


@pytest.fixture(scope="module")
def instances():
    """六实例主记录（逐实例两板合计口径；只读输入、零写盘）。"""
    parsed = {key: S82.parse_reader_raw(rel)
              for key, rel in S82.RAW_FILES.items()}
    deriv = S82._json_load(S82.REL_DERIV_R5)
    gt_applied = S82._gt_entries_with_r5_reprojection(S82.REL_GT_V2, deriv)
    gt_prep1 = S82._gt_entries_with_r5_reprojection(S82.REL_GT_V1, deriv)
    return {name: S82.build_instance_record(
        name, S82.INSTANCES[name], parsed, gt_applied, gt_prep1)
        for name in INSTANCE_ORDER}


# ---------------------------------------------------------------------------
# 输入核验（fail-closed）
# ---------------------------------------------------------------------------

def test_reader_raw_inputs_parse_and_flag_counts():
    """12 件 reader-raw-r23 全在盘、合法解析；实例旗数 16/12/5/6/4/4、
    弃权 11/2/3/4/0/4；拒收为零；R23T/R23B 前缀=指引 §6 示例旗 ID 前缀
    落盘原文（派发命名与指引一致、无前缀差异登记需求）；6 个有旗实例全
    部同实例跨板连续+本轮零零旗格（与 prep-record naming 声明相符）。"""
    parsed = {k: S82.parse_reader_raw(rel)
              for k, rel in S82.RAW_FILES.items()}
    assert sorted(parsed) == sorted(S82.RAW_FILES)
    for n in INSTANCE_ORDER:
        cnts = [len(parsed[p]["images"][0]["flags"])
                for p in S82.INSTANCES[n]["parts"]]
        # 两板合计与 run 实测一致（16/12/5/6/4/4）
        assert sum(cnts) == {"top-i1": 16, "top-i2": 12, "top-i3": 5,
                             "bottom-i1": 6, "bottom-i2": 4,
                             "bottom-i3": 4}[n]
    for k, p in parsed.items():
        assert p["reader_id"].startswith("reader-r23-")
        assert p["direct_json_parse"] is True
        assert p["repair"] == "no_repair"
        for img in p["images"]:
            assert img["rejected"] == []
            for f in img["flags"]:
                assert f["flag_id"].startswith(("R23T-", "R23B-"))
    # 弃权记账（11/2/3/4/0/4；按实例两板合计）
    abst = {n: 0 for n in INSTANCE_ORDER}
    for n in INSTANCE_ORDER:
        for p in S82.INSTANCES[n]["parts"]:
            for img in parsed[p]["images"]:
                for f in img["flags"]:
                    assert f["abstain"] is not None
                    if f["abstain"]:
                        abst[n] += 1
    assert abst == {"top-i1": 11, "top-i2": 2, "top-i3": 3,
                    "bottom-i1": 4, "bottom-i2": 0, "bottom-i3": 4}


def test_parse_reader_raw_fail_closed_and_view_mapping():
    """fail-closed 语义：缺文件→OSError（不返回解析结果）；_fail→
    SystemExit；view_for_image 确定性映射（*-top.png→top、*-bottom.png→
    bottom、无后缀→ValueError）。"""
    with pytest.raises(OSError):
        S82.parse_reader_raw(
            "out/v3-tl2/calibration/reader-raw-r23-NO-SUCH-FILE.txt")
    with pytest.raises(SystemExit):
        S82._fail("输入缺失（fail-closed）: <构造缺件>")
    assert S82.view_for_image("board-applied-top.png") == "top"
    assert S82.view_for_image("board-prep1-bottom.png") == "bottom"
    with pytest.raises(ValueError):
        S82.view_for_image("board-side.png")


def test_pinned_raw_prefixes_and_frozen_anchor_hashes():
    """12 件盲读原始件盘态钉死前缀逐字命中+输入先验锚全集合（协议/GT/
     指引 r8–r20+本轮 r23/prep/axis-plan/12 reader 件/PNG/PDF/受保护链
    件）与盘上实测逐一相等（哈希不符即拒算前提）；本轮指引锚=
    guidance-r23 866b0157（本轮落盘新指引=机械变换派生）、基座
    guidance-r19=8633bda5（零字节不动）、prep-r23=3c42ace7、run-r16
    （M1 基线复算输入）在锚集；run-r23=本包唯一新建输出、不在 FROZEN
    锚集。"""
    for key, prefix in S82.RAW_PINNED_PREFIXES.items():
        got = S82._sha(S82.RAW_FILES[key])
        assert got.startswith(prefix), (key, got[:8], prefix)
    assert S82.FROZEN_SHA256[S82.REL_GUIDANCE_R23].startswith("866b0157")
    assert S82.FROZEN_SHA256[S82.REL_PREP_R23].startswith("3c42ace7")
    assert S82.FROZEN_SHA256[S82.REL_GUIDANCE_R19].startswith("8633bda5")
    assert S82.FROZEN_SHA256[S82.REL_GUIDANCE_R20].startswith("9cdac9ed")
    assert S82.FROZEN_SHA256[S82.REL_RUN_R16].startswith(
        hashing.sha256_file(os.path.join(REPO, S82.REL_RUN_R16))[:8])
    assert len(S82.FROZEN_SHA256) > 40
    for rel, want in S82.FROZEN_SHA256.items():
        assert S82._sha(rel) == want, rel
    assert S82.REL_RUN_R23 not in S82.FROZEN_SHA256


# ---------------------------------------------------------------------------
# rubric 链重放对拍+优先级单元+r23 家族计数
# ---------------------------------------------------------------------------

def test_rubric_replay_r13_r16_chain_matches_frozen_counts():
    """r13–r16 132 条弃权旗 rubric 机械重放对拍：逐旗 family 与分型件
    在案记录逐一相等；contact 链 8/15/5/10、blackdot 链 9/14/8/12 与已
    冻结件（分型件 matrix+prep-record 锚）一致——链式回放先核对一致才可
    应用 r23 分型。"""
    typology_doc = S82.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    proof = S82.replay_typology_families(typology_doc, kt)
    assert proof["per_flag_total"] == 132
    assert proof["contact_counts"] == {"r13": 8, "r14": 15,
                                       "r15": 5, "r16": 10}
    assert proof["blackdot_counts"] == {"r13": 9, "r14": 14,
                                        "r15": 8, "r16": 12}
    assert typology_doc["matrix"]["round_totals"]["r16"]["families"][
        "contact"] == 10


def test_rubric_classify_and_r23_family_counts(run_doc, instances):
    """classify 优先级单元+r23 全部 47 条旗逐旗 rubric 分类：
    contact=8（全视；top 4+bottom 4；r16 基线 10）、existence_blackdot=8
    （高于 r19/r22 双基线）、existence_other=7、semantic_confusion=1、
    other=0——与登记表/run 机制观察口径逐一相等；黑点弃权旗 8 条全弃权
    （逐实例分旗）、黑点转非弃权旗 8 条。"""
    typology_doc = S82.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    # 优先级单元（blackdot 先于 contact；泛化兜底→existence_other）
    fam, _ = S82.rubric_classify(
        "一枚黑色钻孔圆点紧贴焊盘，无法分辨真实接触与视觉贴近", kt)
    assert fam == "existence_blackdot"
    fam, _ = S82.rubric_classify(
        "两 courtyard 轮廓看似相接，无法区分真实接触与视觉贴近", kt)
    assert fam == "contact"
    fam, _ = S82.rubric_classify("该形态无法负责任确认", kt)
    assert fam == "existence_other"
    # r23 全旗套用
    rows = S82.build_rubric_rows_r23(instances, kt)
    fam_counts = {fam: sum(1 for r in rows
                           if r["abstain"] and r["family"] == fam)
                  for fam in ("contact", "existence_blackdot",
                              "existence_other", "semantic_confusion",
                              "other")}
    assert fam_counts == S82.R23_FAMILY_COUNTS_REGISTERED
    assert fam_counts == {"contact": 8, "existence_blackdot": 8,
                          "existence_other": 7, "semantic_confusion": 1,
                          "other": 0}
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    assert mo["black_dot_tracking"]["rubric_families"]["counts"] == \
        fam_counts
    assert len(rows) == 47  # 47 旗逐旗入账（弃权 24+非弃权 23）
    assert sum(1 for r in rows if r["abstain"]) == 24


# ---------------------------------------------------------------------------
# M 元组与基线重放（构造小样例）
# ---------------------------------------------------------------------------

def _synthetic_instance(name, view, flag_count, abstain_count, rate):
    return {"instance": name, "view": view,
            "combined": {"flag_count": flag_count,
                         "abstain_count": abstain_count,
                         "abstain_rate": rate,
                         "matches_total": 0}}


def test_m_tuple_6dp_and_view_aggregate_synthetic():
    """M 元组口径（构造小样例）：_m_tuple_6dp 定点比较键（率×10^6 取整、
    M3 整数直接）；round_view_aggregate 三实例两板合计（16/33、8/14）；
    M4=top 逐实例弃权率先 6 位取率再取极差 0.6875−0.166667=0.520833；
    median3 恰 3 值取第 2。"""
    assert S82._m_tuple_6dp(0.484848, 0.571429, 8, 0.520833) == \
        (484848, 571429, 8, 520833)
    assert S82._m_tuple_6dp(0.461538, 0.571429, 4, 0.211111) == \
        (461538, 571429, 4, 211111)
    inst = {
        "top-i1": _synthetic_instance("top-i1", "top", 16, 11, 0.6875),
        "top-i2": _synthetic_instance("top-i2", "top", 12, 2, 0.166667),
        "top-i3": _synthetic_instance("top-i3", "top", 5, 3, 0.6),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 6, 4,
                                         0.666667),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 0, 0.0),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 4, 4, 1.0),
    }
    ab, fl = S82.round_view_aggregate(inst, ("top-i1", "top-i2", "top-i3"))
    assert (ab, fl) == (16, 33)
    assert S82.cal._ratio(ab, fl) == 0.484848
    ab_b, fl_b = S82.round_view_aggregate(
        inst, ("bottom-i1", "bottom-i2", "bottom-i3"))
    assert (ab_b, fl_b) == (8, 14)
    assert S82.cal._ratio(ab_b, fl_b) == 0.571429
    rates = [0.6875, 0.166667, 0.6]
    assert S82.cal._round6(max(rates) - min(rates)) == 0.520833
    assert S82._median3([16, 12, 5]) == 12
    assert S82._median3([6, 4, 4]) == 4
    assert S82._median3([5, 1, 9]) == 5


def test_view_layer_and_r16_baseline_live_replay():
    """r16 基线=同一聚合逻辑对 run-r16 内嵌输入双侧复算（不手工抄数）：
    top 27/35=0.771429、bottom 12/14=0.857143、G1 基线 courtyard 非弃权
    0/0/0；视角层构造小样例（r23 三实例弃权率全部有定义、bottom 中位数
    =0.666667、极差 1.0）。"""
    run16 = S82._json_load(S82.REL_RUN_R16)
    assert S82.r16_top_abstain_aggregate_live(run16) == (27, 35)
    assert S82.r16_bottom_abstain_aggregate_live(run16) == (12, 14)
    assert S82.r16_baseline_courtyard_live(run16) == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    layer = S82.build_view_layer({
        "top-i1": _synthetic_instance("top-i1", "top", 16, 11, 0.6875),
        "top-i2": _synthetic_instance("top-i2", "top", 12, 2, 0.166667),
        "top-i3": _synthetic_instance("top-i3", "top", 5, 3, 0.6),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 6, 4,
                                         0.666667),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 0, 0.0),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 4, 4, 1.0),
    })
    assert layer["top"]["abstain_rate"]["median"] == 0.6
    assert layer["top"]["abstain_rate_range"] == 0.520833
    assert layer["bottom"]["abstain_rate"]["median"] == 0.666667
    assert layer["bottom"]["abstain_rate_range"] == 1.0


# ---------------------------------------------------------------------------
# 归因三支边界（adjudicate_attribution 构造用例）
# ---------------------------------------------------------------------------

def test_adjudicate_replicated_hygiene_branch_and_band_boundaries():
    """(rh) 支：G2=0+M1 带内（6 位定点整数交叉相乘）+G1 维持→
    replicated_hygiene；带宽端点边界（恰=带下沿 361538 与带上沿 561538
    入带）。"""
    # 带中心附近（r19 实际 0.461538）：G2=0→replicated_hygiene
    assert S82.adjudicate_attribution(0, True, 6, 13) == \
        ("replicated_hygiene", "replicated_hygiene")
    # 恰=带下沿（361538×10^6 = 361538×10^6）→入带
    assert S82.adjudicate_attribution(0, True, 361538, 1000000) == \
        ("replicated_hygiene", "replicated_hygiene")
    # 恰=带上沿（561538×10^6 ≤ 561538×10^6）→入带
    assert S82.adjudicate_attribution(0, True, 561538, 1000000) == \
        ("replicated_hygiene", "replicated_hygiene")


def test_adjudicate_confounded_perturbed_and_guard_branches():
    """(c)/(p)/(gv) 三支+支序：G2 仍>0 且 M1 带内→confounded（本轮实况：
    G2=1、16/33 带内）；反事实构造 G2=0 同输入→replicated_hygiene（分岔
    两侧）；M1 出带→perturbed（带下沿之下/带上沿之上）；G1 破坏→
    guard_violation（支序最高，即使带内）；边界（恰=端点入带→
    confounded）；带宽常量与判据原文同锚。"""
    # 本轮实际落支：M1=16/33 带内、G2=1>0→confounded
    assert S82.adjudicate_attribution(1, True, 16, 33) == \
        ("confounded", "confounded_g2_positive_in_band")
    # 反事实构造：G2=0 时同输入=replicated_hygiene（分岔两侧）
    assert S82.adjudicate_attribution(0, True, 16, 33) == \
        ("replicated_hygiene", "replicated_hygiene")
    # 带端点（恰=下沿/上沿入带，G2>0→confounded）
    assert S82.adjudicate_attribution(2, True, 361538, 1000000) == \
        ("confounded", "confounded_g2_positive_in_band")
    assert S82.adjudicate_attribution(2, True, 561538, 1000000) == \
        ("confounded", "confounded_g2_positive_in_band")
    # 带下沿之下（361537×10^6 < 361538×10^6）→出带→perturbed
    assert S82.adjudicate_attribution(1, True, 361537, 1000000) == \
        ("perturbed", "perturbed_m1_out_of_band")
    # 带上沿之上（561539×10^6 > 561538×10^6）→出带→perturbed
    assert S82.adjudicate_attribution(1, True, 561539, 1000000) == \
        ("perturbed", "perturbed_m1_out_of_band")
    # G1 破坏→guard_violation（支序最高：三支字母口径均不命中、不新增
    # 字母支；即使 G2=0 且带内）
    assert S82.adjudicate_attribution(0, False, 16, 33) == \
        ("guard_violation", "guard_violation_g1")
    assert S82.adjudicate_attribution(1, False, 16, 33) == \
        ("guard_violation", "guard_violation_g1")
    # 6 位定点常量与 s83/判据原文同锚（r19±0.10 带宽）
    assert (S82.REPL_BAND_LO_6DP, S82.REPL_BAND_HI_6DP) == \
        (361_538, 561_538)


# ---------------------------------------------------------------------------
# G1/G2 守门与援引分记（机制观察）
# ---------------------------------------------------------------------------

def test_guards_g1_g2_and_citation_observation(run_doc, instances):
    """G1 实测（操作化定义）：bottom courtyard 非弃权 0/0/0=G1 维持
    （r16 基线 live 重放对照、r20 破坏 2/0/0 与 r22 维持 0/0/0 在案）；
    G2 未清零（几何门 R19=0→R22=2→R23=1）；guard_channel g1_ok=True、
    g2=False、guards_ok=False；判据布尔（confounded 命中/其余三支不命
    中）；援引分记（旗级 §5B/(iii-a)/分支( 全 0、notes 级 §5B=0/12、
    (iii-a)=4/12、§6 条款=6/12；r19 基线=旗级 6+2、notes 10/12 在案；
    r22=旗级全 0、notes 6/12 在案；落支 间隙 4+侵入 5+残余弃权 14、侵入
    支 notes 级 2 派次）。"""
    assert S82.bottom_courtyard_non_abstain(instances) == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    m = run_doc["hypothesis_test"]["measurement"]
    gc = m["guard_channel"]
    assert gc["g1_ok"] is True
    assert gc["g2_guard_ok"] is False
    assert gc["guards_ok"] is False
    assert gc["g2_geometry_gate_r19"] == 0
    assert gc["g2_geometry_gate_r22"] == 2
    assert gc["g2_geometry_gate_r23"] == 1
    g12 = run_doc["hypothesis_test"]["mechanism_observation"]["guards_g1_g2"]
    assert g12["counts"]["guards_ok"] is False
    assert g12["counts"]["g1_ok"] is True
    assert g12["counts"]["g2_guard_ok_axis_plan_semantics"] is False
    assert g12["counts"]["g1_bottom_courtyard_non_abstain_r23"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g1_r16_baseline_live"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g1_r20_broken_registered"] == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g1_r22_maintained_registered"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g2_geometry_gate_r19"] == 0
    assert g12["counts"]["g2_geometry_gate_r22"] == 2
    assert g12["counts"]["g2_geometry_gate_r23"] == 1
    # 判据布尔（confounded 支命中、其余三支不命中）
    assert m["crit_confounded"] is True
    assert m["crit_guard_violation"] is False
    assert m["crit_perturbed"] is False
    assert m["crit_replicated_hygiene"] is False
    # M1 复制带（6 位定点；与盘上登记逐一相等）
    assert m["replication_band_6dp"] == [S82.REPL_BAND_LO_6DP,
                                         S82.REPL_BAND_HI_6DP]
    # 援引分记（三条款分开记、互不合并；机制观察单列）：旗级零字面援引
    # +notes 级 §5B=0（本轮指引含 §6 新条款、仍无 §5B 节）+notes 级
    # (iii-a)=4/12+§6 报告框收敛条款=6/12
    cc = run_doc["hypothesis_test"]["mechanism_observation"][
        "criterion_citation_observation"]
    counts = cc["citation_counts"]
    assert counts["flag_level_s5b_literal"] == 0
    assert counts["flag_level_iiia_literal"] == 0
    assert counts["flag_level_branch_literal"] == 0
    assert counts["flag_level_s5b_sources"] == \
        S82.S5B_FLAG_CITE_REGISTERED == []
    assert counts["flag_level_iiia_sources"] == []
    assert counts["notes_level_s5b"] == 0
    assert counts["notes_level_s5b_sources"] == S82.S5B_NOTES_CITE_REGISTERED
    assert counts["notes_level_iiia"] == 4
    assert counts["notes_level_iiia_sources"] == \
        S82.IIIA_NOTES_CITE_REGISTERED
    assert counts["notes_level_s6_clause"] == 6
    assert counts["notes_level_s6_clause_sources"] == \
        S82.S6_NOTES_CITE_REGISTERED
    # r19/r22 基线对照（在案登记：r19 旗级 (iii-a) 6 旗+分支( 2 旗、
    # notes 10/12；r22 旗级全 0、notes 6/12）
    assert "6" in counts["baseline_r19_iiia"]
    assert "10/12" in counts["baseline_r19_iiia"]
    assert "旗级全 0" in counts["baseline_r22_iiia"]
    assert "6/12" in counts["baseline_r22_iiia"]
    assert "1/12" in counts["baseline_r18_s5b"]
    # (iii-a) 逐旗落支：间隙 4+侵入 5+残余弃权 14；侵入支 notes 级 2 派次
    assert cc["branch_counts_flag_level"] == {"branch1_gap_report": 4,
                                              "branch2_intrusion_report": 5,
                                              "branch3_residual_abstain": 14}
    assert cc["branch2_notes_level_dispatches"] == 2


# ---------------------------------------------------------------------------
# 守卫、run 记录身份与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；既有且
    不同→fail；_commit=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写；run-r23 盘上件不可覆写）。"""
    assert S82.overwrite_guard(None, b"abc") == "write"
    assert S82.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S82.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S82._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S82._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S82._commit(p, b"abc", "probe")


def test_run_record_canonical_identity_and_letter_verdict(run_doc):
    """run-r23 盘上件：同参重建两次 byte-exact+盘上件=canonical 重建+
    轮次身份（r23/2026-09-10/development 域）+verdict=confounded（唯一
    正式裁决）+落支 confounded_g2_positive_in_band（G2 未清零且 M1 带内）
    +四元组与 r19/r22 参照元组+单变量报告框收敛归因轮轮次性质（指引机械
    变换派生/渲染零变更/changed_variables=1/axis=output_format_report_
    discipline）+判据原文摘录与 prep-record 逐字一致。"""
    b1 = hashing.canonical_json_bytes(S82.build_run())
    b2 = hashing.canonical_json_bytes(S82.build_run())
    assert b1 == b2  # 同参重建 byte-exact
    path = os.path.join(CAL_DIR, "calibration-run-r23.json")
    raw = open(path, "rb").read()
    assert raw == b1  # 盘上件=canonical 重建（byte-exact 可重跑）
    assert hashing.sha256_file(path).startswith("15f58350")
    doc = json.loads(raw.decode("utf-8"))
    assert doc["kind"] == "tl2_calibration_run_r23"
    assert doc["round_id"] == ROUND_ID
    assert doc["round_label"] == ROUND_LABEL
    assert doc["declared_date"] == DECLARED_DATE
    assert doc["evaluation_domain"] == "development"
    assert doc["evaluation_domain_note"]["in_calibrated_range"] is False
    assert doc["instrument_change"]["changed"] is False
    assert doc["instrument_change"]["axis_id"].startswith(
        "output_format_report_discipline")
    hyp = doc["hypothesis_test"]
    m = hyp["measurement"]
    assert hyp["hypothesis_id"] == \
        "r22-g2-bifurcation-frame-box-hygiene-attribution"
    assert hyp["verdict"] == "confounded" and m["verdict"] == "confounded"
    assert "(c)" in m["letter_branch"]
    assert "G2 出局条目仍 >0" in m["letter_branch"]
    assert "框宽非（唯一）主因" in m["letter_branch"]
    assert m["r23_m_tuple_6dp"] == {"M1": 0.484848, "M2": 0.571429,
                                    "M3": 8, "M4": 0.520833}
    assert m["r19_reference_tuple"] == {"M1": 0.461538, "M2": 0.571429,
                                        "M3": 4, "M4": 0.211111}
    assert m["r22_reference_tuple_live"] == {"M1": 0.390244, "M2": 0.2,
                                             "M3": 4, "M4": 0.104545}
    assert m["top_abstain_count_r23"] == 16
    assert m["top_abstain_flags_r23"] == 33
    assert "16/33" in m["top_abstain_rate_r23_arithmetic"]
    assert m["contact_family_abstain_flags_rubric_r23"] == 8
    # 预注册判据摘录=prep-record adjudication 原文（逐字一致；6 键）
    prep = S82._json_load(S82.REL_PREP_R23)
    adj = prep["hypothesis_test"]["adjudication"]
    q = hyp["preregistered_criteria_quote"]
    for k in ("confounded", "descriptive_boundary_note",
              "mechanism_observation_separate", "metric_lesson_separate",
              "perturbed", "replicated_hygiene"):
        assert q[k] == adj[k], k
    assert prep["hypothesis_test"]["hypothesis_id"] == hyp["hypothesis_id"]
    # changed_variables=1（§6 报告框收敛条款单变量；指引=机械变换派生、
    # 基座零字节不动；渲染/GT/阈值/协议零变更）
    assert len(prep["changed_variables"]) == 1
    assert prep["no_instrument_change"] is True
    assert prep["guidance_reuse"]["mode"] == "mechanical_transform_derive"
    assert prep["guidance_reuse"]["base_sha256"].startswith("8633bda5")
    assert prep["guidance_reuse"]["derived_sha256"].startswith("866b0157")
    assert prep["guidance_reuse"]["byte_size"] == {
        "base": 21435, "delta": 1690, "derived": 23125}


def test_gt_dual_union_joint_gate_in_range_false(run_doc):
    """GT 双口径 union=2/13=0.153846（两 GT 条目均单实例命中：
    GT-REVC-P1-R4J3 R23T-002+GT-REVC-P1-L1SHORT R23T-011）、agreement=
    0/13（r22 双实例一致命中未复现、里程碑维持）；代表配置（top-i2+
    bottom-i2；top 非 tie、bottom tie 按先序）聚合 16/2/0.125、joint
    not_met、连续=0；in_calibrated_range 恒 False（run 与 compliance 双
    处）；本轮无零旗格（None 口径未触发）。"""
    doc = run_doc
    dual = doc["gt_match_dual"]
    assert (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) == (2, 0, 13)
    assert dual["union"]["gt_ids"] == ["GT-REVC-P1-R4J3",
                                       "GT-REVC-P1-L1SHORT"]
    assert dual["agreement"]["gt_ids"] == []
    assert dual["union"]["gt_recall_union"] == 0.153846
    assert dual["agreement"]["gt_recall_agreement"] == 0.0
    hits = [pg for pg in dual["per_gt"] if pg.get("hits")]
    assert len(hits) == 2
    assert all(pg["matched_by_count"] == 1 for pg in hits)
    got = {(h["flag_id"], h["instance"], h["state"])
           for pg in hits for h in pg["hits"]}
    assert got == {("R23T-002", "top-i3", "prep1"),
                   ("R23T-011", "top-i2", "prep1")}
    comp = doc["compliance_representative"]
    agg = doc["aggregation_representative"]
    assert (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) == (16, 2, 0.125, 0.076923,
                                              0.071429)
    assert comp["joint_evaluation"] == "not_met"
    assert comp["consecutive_rounds"]["consecutive_met_count"] == 0
    assert comp["critic_calibration_in_range"] is False
    assert "恒 False" in comp["critic_calibration_in_range_note"]
    assert doc["evaluation_domain_note"]["in_calibrated_range"] is False
    criteria = {c["id"]: c["met"] for c in comp["criteria"]}
    assert criteria == {"gt_count_ge_12": True, "gt_recall_ge_0.75": False,
                        "seed_match_rate_ge_0.5": False,
                        "abstain_rate_le_0.5": True}
    assert doc["representative_configuration"]["members"] == \
        {"top": "top-i2", "bottom": "bottom-i2"}
    assert doc["representative_configuration"]["selection"]["top"][
        "tie"] is False
    assert doc["representative_configuration"]["selection"]["bottom"][
        "tie"] is True  # bottom-i2/bottom-i3 同为 4→按先序规则
    assert doc["reader"]["zero_flag_parts"]["parts"] == []
    assert doc["view_layer"]["bottom"]["abstain_rate"]["median"] == 0.666667
    assert doc["view_layer"]["bottom"]["abstain_rate_range"] == 1.0
    assert doc["view_layer"]["top"]["abstain_rate_range"] == 0.520833


def test_experiment_ledger_seven_round_account_and_axis3_first(run_doc):
    """七行对照账完整性：r16/r17/r18/r19/r20/r22/r23 七行并列（M 元组逐
    一相等）+r23/r22/r20 均 G 守门破坏不入排序（资格门剔除；排序不变=
    r19_axis3 第一/r18 第二/r16 参照/r17 末位）+三族计数对照 r19（4/4/14）
    与 r22（2/4/12）+M4 三样本单列（0.211111/0.104545/0.520833、不进字
    母不合并）+归因结论位=框宽非（唯一）主因/归因转向/r22 字母维持+显著
    收益 0.286581≥0.10 描述层命中+in_calibrated_range 恒 False 收尾。"""
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    ecl = mo["experiment_comparison_ledger"]
    assert ecl["r23_measured"]["M1"] == 0.484848
    assert ecl["r23_measured"]["M2"] == 0.571429
    assert ecl["r23_measured"]["M3"] == 8
    assert ecl["r23_measured"]["M4"] == 0.520833
    assert ecl["r23_measured"]["M1_arithmetic"] == "16/33"
    assert ecl["r23_measured"]["M2_arithmetic"] == "8/14"
    assert ecl["r23_measured"]["contact_family_abstain_flags_rubric"] == 8
    assert ecl["r23_measured"]["contact_family_by_view"] == \
        {"bottom": 4, "top": 4}
    assert ecl["r23_measured"]["existence_other_family"] == 7
    assert ecl["r16_baseline_registered"]["M1"] == 0.771429
    assert ecl["r16_baseline_registered"]["M4"] == 0.261904
    assert ecl["r17_axis1_row"] == {"M1": 0.88, "M2": 0.75, "M3": 8,
                                    "M4": 0.333333}
    assert ecl["r18_axis2_row"] == {"M1": 0.645161, "M2": 0.684211,
                                    "M3": 13, "M4": 0.277778}
    assert ecl["r19_axis3_row"] == {"M1": 0.461538, "M2": 0.571429,
                                    "M3": 4, "M4": 0.211111}
    assert ecl["r20_combo_registered_row"] == {"M1": 0.636364,
                                               "M2": 0.285714, "M3": 6,
                                               "M4": 0.25}
    assert ecl["r22_repeat_registered_row"] == {"M1": 0.390244, "M2": 0.2,
                                                "M3": 4, "M4": 0.104545}
    fc = ecl["family_counts_vs_r19_r22"]
    assert (fc["contact"]["r19_registered"], fc["contact"]["r22_registered"],
            fc["contact"]["r23_measured"]) == (4, 2, 8)
    assert (fc["existence_blackdot"]["r19_registered"],
            fc["existence_blackdot"]["r22_registered"],
            fc["existence_blackdot"]["r23_measured"]) == (4, 4, 8)
    assert (fc["existence_other"]["r19_registered"],
            fc["existence_other"]["r22_registered"],
            fc["existence_other"]["r23_measured"]) == (14, 12, 7)
    rk = ecl["ranking_by_comparison_rule"]
    # r23 不入排序（G2 破坏）；comparison_rule 排序不变（r19_axis3 第一）
    assert rk["r23_eligibility"] is False
    assert rk["r22_eligibility"] is False
    assert rk["r20_eligibility"] is False
    assert "G2" in rk["r23_eligibility_note"] or "几何门" in \
        rk["r23_eligibility_note"]
    assert rk["ranking_order_best_first"] == ["r19_axis3", "r18_axis2",
                                              "r16_baseline", "r17_axis1"]
    assert rk["eligible_rows"] == ["r16_baseline", "r17_axis1",
                                   "r18_axis2", "r19_axis3"]
    assert set(rk["rows_registered"]) == {"r16_baseline", "r17_axis1",
                                          "r18_axis2", "r19_axis3",
                                          "r20_combo_registered",
                                          "r22_repeat_registered",
                                          "r23_attribution"}
    assert rk["rows_registered"]["r23_attribution"]["M1"] == 0.484848
    assert rk["rows_registered"]["r23_attribution"]["M4"] == 0.520833
    # M4 三样本单列（不进字母、不合并分布、不挑优）
    att = ecl["attribution_conclusion"]["conclusion"]
    assert "框宽非（唯一）主因" in att
    assert "归因转向" in att
    assert "维持不改写" in att
    assert "11.458680" in json.dumps(ecl, ensure_ascii=False)
    assert S82.cal._round6(0.520833 - 0.104545) == 0.416288
    sb = ecl["significant_benefit_vs_r16"]
    assert sb["met"] is True
    assert sb["r23_m1_absolute_drop"] == 0.286581
    assert round(0.771429 - 0.484848, 6) == 0.286581
    fd = ecl["direction_vs_r16"]
    assert fd["M1"].startswith("down") and fd["M2"].startswith("down")
