"""R20 执行包测试（s74_calibration_r20_compare / calibration-run-r20）——
阶段2 组合轮（axis-experiment-plan-r17-r20 stage2 唯一组合轮=轴3+轴2 两
轴变更并施：渲染零变更=renders-r14b 四图字节复用；判读指引=
observation-guidance-r20.md 9cdac9ed=r19 基座 8633bda5 机械变换派生+
§5B 整节自 r18 指引 cadcb8f3 逐字转录插入+§6 前缀（§4(iii-a) 随基座逐字
承继）=指引合成（§5B+§4(iii-a) 并集）=唯一操纵因子；GT/阈值/协议零变更；
instrument_change.changed=false 已预注册）+ 预注册假设
（axis-plan-r20-combo-additivity）ordering 三分判据裁决=reject（唯一正式
裁决）：(s) R20 四元组 (0.636364, 0.285714, 6, 0.25) 在冻结
comparison_rule.ordering (M1 升序,M2 升序,M3 升序,M4 升序) 字典序下劣于
最优单轴 r19 (0.461538, 0.571429, 4, 0.211111)→不劣于=不成立；(r) G1
破坏命中（bottom courtyard 非弃权实测 2/0/0≠0/0/0 维持；bottom-i1 两板
R20B-003/R20B-006 经 (iii-a) 间隙支负责任报告路径产生=r14–r19 bottom
侧首现非弃权 courtyard 旗）→reject_guards 支（支序最高）；G2 维持
（几何门 R19=0→R20=0）；(r) M1 ≥0.771429 未命中；机制观察单列：rubric
族计数 contact 2/existence_blackdot 6/existence_other 10（r13–r16 132 条
重放对拍逐一相等；contact 链 8/15/5/10）+援引分记（旗级 §5B/(iii-a)/
分支( 全 0、notes 级 §5B=4/12、(iii-a)=4/12）+五轮对照账
（r16 0.771429/0.857143/12/0.261904、r17 0.88/0.75/8/0.333333、
r18 0.645161/0.684211/13/0.277778、r19 0.461538/0.571429/4/0.211111、
r20 0.636364/0.285714/6/0.25）+r20 资格门剔除不参与排序+阶段2 结论=
组合劣化采最优单轴 r19、R21 不做 + GT 双口径 union=agreement=0/13（全
轮零命中；r19 唯一命中未再现）+12 格全部≥1 旗（零旗标口径未触发）+
in_calibrated_range 恒 False + development 域。

覆盖（14 测试，只读 out/、零子进程/零网络/零写盘）：
- 输入核验 fail-closed：12 件 reader-raw-r20 合法解析+实例旗数/弃权
  记账；缺文件→OSError、_fail→SystemExit、视角后缀缺失→ValueError；
  12 件盘态钉死前缀；FROZEN_SHA256 全锚实测一致；
- rubric 链重放对拍：r13–r16 132 条弃权旗重放（per_flag_total=132、
  blackdot 9/14/8/12、contact 8/15/5/10）+classify 优先级单元+r20 家族
  计数（2/6/10/0/0 与登记一致）；
- M 元组：_m_tuple_6dp 定点键+构造小样例 round_view_aggregate/_median3/
  M4 极差+r16 基线双侧 live 复算（27/35、12/14、courtyard 0/0/0）；
- 裁决三支边界：adjudicate_main_channel 纯函数构造用例——supported
  （ordering 不劣于 r19）、marginal（未达 supported 且 M1 <0.771429）、
  reject_guards（守门破坏，支序最高）、reject_m1（M1 ≥0.771429）与
  supported∩reject_m1 同中 RuntimeError（自洽性守卫）；
- 守卫与确定性：overwrite_guard 三态+_commit 落盘语义；run-r20 盘上件
  canonical byte 与重建一致+轮次身份+verdict=reject+落支 reject_guards+
  M 元组+r19 基准元组+GT 双口径 0/13+援引分记+in_calibrated_range 恒
  False+五轮对照账+排序（资格门剔除 r20）+阶段2 结论；
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


def _load_s74():
    path = os.path.join(REPO, "scripts", "s74_calibration_r20_compare.py")
    spec = importlib.util.spec_from_file_location("s74_calibration_r20",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S74 = _load_s74()


@pytest.fixture(scope="module")
def run_doc():
    """run-r20 文档内存构建（纯函数；只读输入、零写盘）。"""
    return S74.build_run()


@pytest.fixture(scope="module")
def instances():
    """六实例主记录（逐实例两板合计口径；只读输入、零写盘）。"""
    parsed = {key: S74.parse_reader_raw(rel)
              for key, rel in S74.RAW_FILES.items()}
    deriv = S74._json_load(S74.REL_DERIV_R5)
    gt_applied = S74._gt_entries_with_r5_reprojection(S74.REL_GT_V2, deriv)
    gt_prep1 = S74._gt_entries_with_r5_reprojection(S74.REL_GT_V1, deriv)
    return {name: S74.build_instance_record(
        name, S74.INSTANCES[name], parsed, gt_applied, gt_prep1)
        for name in INSTANCE_ORDER}


# ---------------------------------------------------------------------------
# 输入核验（fail-closed）
# ---------------------------------------------------------------------------

def test_reader_raw_inputs_parse_and_flag_counts():
    """12 件 reader-raw-r20 全在盘、合法解析；实例旗数 8/8/6/6/4/4、
    弃权 4/6/4/0/0/4；拒收为零；R20T/R20B 前缀随指引 §6 落盘固化；6 实例
    全部同实例跨板连续（与 prep-record naming 声明全部相符）。"""
    parsed = {k: S74.parse_reader_raw(rel)
              for k, rel in S74.RAW_FILES.items()}
    assert sorted(parsed) == sorted(S74.RAW_FILES)
    for n in INSTANCE_ORDER:
        cnts = [len(parsed[p]["images"][0]["flags"])
                for p in S74.INSTANCES[n]["parts"]]
        # 两板合计与 run 实测一致（8/8/6/6/4/4）
        assert sum(cnts) == {"top-i1": 8, "top-i2": 8, "top-i3": 6,
                             "bottom-i1": 6, "bottom-i2": 4,
                             "bottom-i3": 4}[n]
    for k, p in parsed.items():
        assert p["reader_id"].startswith("reader-r20-")
        assert p["direct_json_parse"] is True
        assert p["repair"] == "no_repair"
        for img in p["images"]:
            for f in img["flags"]:
                assert f["flag_id"].startswith(("R20T-", "R20B-"))
    # 弃权记账（4/6/4/0/0/4；按实例两板合计）
    abst = {n: 0 for n in INSTANCE_ORDER}
    for n in INSTANCE_ORDER:
        for p in S74.INSTANCES[n]["parts"]:
            for img in parsed[p]["images"]:
                for f in img["flags"]:
                    if f["abstain"]:
                        abst[n] += 1
    assert abst == {"top-i1": 4, "top-i2": 6, "top-i3": 4,
                    "bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 4}


def test_parse_reader_raw_fail_closed_and_view_mapping():
    """fail-closed 语义：缺文件→OSError（不返回解析结果）；_fail→
    SystemExit；view_for_image 确定性映射（*-top.png→top、*-bottom.png→
    bottom、无后缀→ValueError）。"""
    with pytest.raises(OSError):
        S74.parse_reader_raw(
            "out/v3-tl2/calibration/reader-raw-r20-NO-SUCH-FILE.txt")
    with pytest.raises(SystemExit):
        S74._fail("输入缺失（fail-closed）: <构造缺件>")
    assert S74.view_for_image("board-applied-top.png") == "top"
    assert S74.view_for_image("board-prep1-bottom.png") == "bottom"
    with pytest.raises(ValueError):
        S74.view_for_image("board-side.png")


def test_pinned_raw_prefixes_and_frozen_anchor_hashes():
    """12 件盲读原始件盘态钉死前缀逐字命中+输入先验锚全集合（协议/GT/
     指引 r8–r20 五代/prep/axis-plan/12 reader 件/PNG/PDF/受保护链件）
    与盘上实测逐一相等（哈希不符即拒算前提）；guidance-r20=9cdac9ed、
    prep-r20=e29ee2a3、run-r16（M1 基线复算输入）在锚集。"""
    for key, prefix in S74.RAW_PINNED_PREFIXES.items():
        got = S74._sha(S74.RAW_FILES[key])
        assert got.startswith(prefix), (key, got[:8], prefix)
    assert S74.FROZEN_SHA256[S74.REL_GUIDANCE_R20].startswith("9cdac9ed")
    assert S74.FROZEN_SHA256[S74.REL_PREP_R20].startswith("e29ee2a3")
    assert S74.FROZEN_SHA256[S74.REL_GUIDANCE_R19].startswith("8633bda5")
    assert S74.FROZEN_SHA256[S74.REL_GUIDANCE_R18].startswith("cadcb8f3")
    assert len(S74.FROZEN_SHA256) > 40
    for rel, want in S74.FROZEN_SHA256.items():
        assert S74._sha(rel) == want, rel


# ---------------------------------------------------------------------------
# rubric 链重放对拍+优先级单元+r20 家族计数
# ---------------------------------------------------------------------------

def test_rubric_replay_r13_r16_chain_matches_frozen_counts():
    """r13–r16 132 条弃权旗 rubric 机械重放对拍：逐旗 family 与分型件
    在案记录逐一相等；contact 链 8/15/5/10、blackdot 链 9/14/8/12 与已
    冻结件（分型件 matrix+prep-record 锚）一致。"""
    typology_doc = S74.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    proof = S74.replay_typology_families(typology_doc, kt)
    assert proof["per_flag_total"] == 132
    assert proof["contact_counts"] == {"r13": 8, "r14": 15,
                                       "r15": 5, "r16": 10}
    assert proof["blackdot_counts"] == {"r13": 9, "r14": 14,
                                        "r15": 8, "r16": 12}
    assert typology_doc["matrix"]["round_totals"]["r16"]["families"][
        "contact"] == 10


def test_rubric_classify_and_r20_family_counts(run_doc, instances):
    """classify 优先级单元+r20 全部 18 条弃权旗逐旗 rubric 分类：
    contact=2（全视；top 2+bottom 0；r16 基线 10）、existence_blackdot=6、
    existence_other=10、semantic_confusion=0、other=0——与登记表/run
    机制观察口径逐一相等；黑点弃权旗 6 条全弃权、黑点转非弃权旗 6 条
    （全 bottom）。"""
    typology_doc = S74.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    # 优先级单元（blackdot 先于 contact；泛化兜底→existence_other）
    fam, _ = S74.rubric_classify(
        "一枚黑色钻孔圆点紧贴焊盘，无法分辨真实接触与视觉贴近", kt)
    assert fam == "existence_blackdot"
    fam, _ = S74.rubric_classify(
        "两 courtyard 轮廓看似相接，无法区分真实接触与视觉贴近", kt)
    assert fam == "contact"
    fam, _ = S74.rubric_classify("该形态无法负责任确认", kt)
    assert fam == "existence_other"
    # r20 全旗套用
    rows = S74.build_rubric_rows_r20(instances, kt)
    fam_counts = {fam: sum(1 for r in rows
                           if r["abstain"] and r["family"] == fam)
                  for fam in ("contact", "existence_blackdot",
                              "existence_other", "semantic_confusion",
                              "other")}
    assert fam_counts == S74.R20_FAMILY_COUNTS_REGISTERED
    assert fam_counts == {"contact": 2, "existence_blackdot": 6,
                          "existence_other": 10, "semantic_confusion": 0,
                          "other": 0}
    nonabstain_bd = [r for r in rows
                     if not r["abstain"] and r["matched_blackdot_terms"]]
    assert len(nonabstain_bd) == 6
    assert all(r["instance"].startswith("bottom") for r in nonabstain_bd)
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    assert mo["black_dot_tracking"]["rubric_families"]["counts"] == fam_counts


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
    M3 整数直接）；round_view_aggregate 三实例两板合计（14/22、4/14）；
    M4=top 逐实例弃权率先 6 位取率再取极差 0.75−0.5=0.25；median3 恰 3
    值取第 2。"""
    assert S74._m_tuple_6dp(0.636364, 0.285714, 6, 0.25) == \
        (636364, 285714, 6, 250000)
    assert S74._m_tuple_6dp(0.461538, 0.571429, 4, 0.211111) == \
        (461538, 571429, 4, 211111)
    inst = {
        "top-i1": _synthetic_instance("top-i1", "top", 8, 4, 0.5),
        "top-i2": _synthetic_instance("top-i2", "top", 8, 6, 0.75),
        "top-i3": _synthetic_instance("top-i3", "top", 6, 4, 0.666667),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 6, 0, 0.0),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 0, 0.0),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 4, 4, 1.0),
    }
    ab, fl = S74.round_view_aggregate(inst, ("top-i1", "top-i2", "top-i3"))
    assert (ab, fl) == (14, 22)
    assert S74.cal._ratio(ab, fl) == 0.636364
    ab_b, fl_b = S74.round_view_aggregate(
        inst, ("bottom-i1", "bottom-i2", "bottom-i3"))
    assert (ab_b, fl_b) == (4, 14)
    rates = [0.5, 0.75, 0.666667]
    assert S74.cal._round6(max(rates) - min(rates)) == 0.25
    assert S74._median3([8, 8, 6]) == 8
    assert S74._median3([6, 4, 4]) == 4
    assert S74._median3([5, 1, 9]) == 5


def test_view_layer_and_r16_baseline_live_replay():
    """r16 基线=同一聚合逻辑对 run-r16 内嵌输入双侧复算（不手工抄数）：
    top 27/35=0.771429、bottom 12/14=0.857143、G1 基线 courtyard 非弃权
    0/0/0；视角层构造小样例（12 格全部≥1 旗→中位数可计算、本轮零旗标
    口径未触发）。"""
    run16 = S74._json_load(S74.REL_RUN_R16)
    assert S74.r16_top_abstain_aggregate_live(run16) == (27, 35)
    assert S74.r16_bottom_abstain_aggregate_live(run16) == (12, 14)
    assert S74.r16_baseline_courtyard_live(run16) == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    layer = S74.build_view_layer({
        "top-i1": _synthetic_instance("top-i1", "top", 8, 4, 0.5),
        "top-i2": _synthetic_instance("top-i2", "top", 8, 6, 0.75),
        "top-i3": _synthetic_instance("top-i3", "top", 6, 4, 0.666667),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 6, 0, 0.0),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 0, 0.0),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 4, 4, 1.0),
    })
    assert layer["top"]["abstain_rate"]["median"] == 0.666667
    assert layer["top"]["abstain_rate_range"] == 0.25
    assert layer["bottom"]["abstain_rate"]["median"] == 0.0
    assert layer["bottom"]["abstain_rate_range"] == 1.0


# ---------------------------------------------------------------------------
# 裁决三支边界（adjudicate_main_channel 构造用例）
# ---------------------------------------------------------------------------

R19_TUPLE = (461538, 571429, 4, 211111)


def test_adjudicate_supported_and_marginal_boundaries():
    """(s)/(m) 边界：R20 四元组 ordering 字典序不劣于 r19（≤）且 G 维持
    →supported；劣于 r19 但 M1 <0.771429 且 G 维持→marginal；ordering
    首键 M1 相等时依次 M2→M3→M4 tie-break。"""
    # 实际 r20 元组 (636364,285714,6,250000) 劣于 r19（M1 首键即分胜负）
    # 且 M1=14/22=0.636364<0.771429、G 维持→marginal 支（reject_guards
    # 未命中前提下）
    verdict, key = S74.adjudicate_main_channel(
        abst_top=14, flags_top=22, m4=0.25,
        r20_tuple=(636364, 285714, 6, 250000), r19_tuple=R19_TUPLE,
        guards_ok=True)
    assert (verdict, key) == ("marginal", "marginal")
    # 四元组与 r19 全等→supported（M1 相等、其余键不劣）
    verdict, key = S74.adjudicate_main_channel(
        abst_top=14, flags_top=22, m4=0.25, r20_tuple=R19_TUPLE,
        r19_tuple=R19_TUPLE, guards_ok=True)
    assert (verdict, key) == ("supported", "supported")
    # M1 相等、M2 改善→supported（tie-break M2）
    verdict, key = S74.adjudicate_main_channel(
        abst_top=14, flags_top=22, m4=0.25,
        r20_tuple=(461538, 500000, 4, 211111), r19_tuple=R19_TUPLE,
        guards_ok=True)
    assert (verdict, key) == ("supported", "supported")
    # M1 相等、M2 劣化→非 supported（守门维持+M1<0.771429→marginal）
    verdict, key = S74.adjudicate_main_channel(
        abst_top=14, flags_top=22, m4=0.25,
        r20_tuple=(461538, 600000, 4, 211111), r19_tuple=R19_TUPLE,
        guards_ok=True)
    assert (verdict, key) == ("marginal", "marginal")


def test_adjudicate_reject_branches_and_mutual_exclusion():
    """(r) 两途径+支序：G 破坏→reject_guards（支序最高，即使 supported
    条件全真）；M1 ≥0.771429（6 位定点整数交叉相乘）→reject_m1；边界
    （恰=阈值入 reject）；supported∩reject_m1 同中→RuntimeError（自洽
    性守卫）。"""
    # G1 破坏（本轮实际）：即使 ordering 不劣于 r19 也落 reject_guards
    verdict, key = S74.adjudicate_main_channel(
        abst_top=14, flags_top=22, m4=0.25, r20_tuple=R19_TUPLE,
        r19_tuple=R19_TUPLE, guards_ok=False)
    assert (verdict, key) == ("reject", "reject_guards")
    # reject_m1：36/46=0.782608 ≥0.771429（36×10^6 ≥ 771429×46）
    verdict, key = S74.adjudicate_main_channel(
        abst_top=36, flags_top=46, m4=0.3,
        r20_tuple=(782608, 700000, 9, 0), r19_tuple=R19_TUPLE,
        guards_ok=True)
    assert (verdict, key) == ("reject", "reject_m1")
    # 恰在阈值下（0.771428<0.771429）→非 reject_m1→marginal
    verdict, key = S74.adjudicate_main_channel(
        abst_top=27, flags_top=35, m4=0.26, r20_tuple=(771428, 800000,
                                                       12, 0),
        r19_tuple=R19_TUPLE, guards_ok=True)
    assert (verdict, key) == ("marginal", "marginal")
    # 自洽性守卫：ordering 全真（tuple=(0,0,0,0)≤r19）且 M1 门同中
    # （8/10=0.8 ≥0.771429）→RuntimeError
    with pytest.raises(RuntimeError):
        S74.adjudicate_main_channel(
            abst_top=8, flags_top=10, m4=0.0, r20_tuple=(0, 0, 0, 0),
            r19_tuple=R19_TUPLE, guards_ok=True)


# ---------------------------------------------------------------------------
# G1 守门与援引分记（机制观察）
# ---------------------------------------------------------------------------

def test_g1_bottom_courtyard_guard_channel_and_citation(run_doc, instances):
    """G1 实测（操作化定义）：bottom courtyard 非弃权 2/0/0（bottom-i1
    两板 R20B-003/R20B-006）=G1 字面破坏；r16 基线 0/0/0 live 重放对照；
    G2 维持（几何门 R19=0→R20=0）；guard_channel g1_ok=False、g2=True、
    guards_ok=False；early_stop 触发（axis_early_stop_triggered=True）；
    判据布尔（reject_guards 命中/reject_m1 未中/supported 未落）；援引
    分记（旗级 §5B/(iii-a)/分支( 全 0、notes 级各 4/12、间隙支 2）。"""
    assert S74.bottom_courtyard_non_abstain(instances) == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
    m = run_doc["hypothesis_test"]["measurement"]
    gc = m["guard_channel"]
    assert gc["g1_ok"] is False
    assert gc["g2_guard_ok"] is True
    assert gc["guards_ok"] is False
    assert gc["g2_geometry_gate_r19"] == 0
    assert gc["g2_geometry_gate_r20"] == 0
    bso = m["bottom_side_observation"]
    assert bso["bottom_courtyard_non_abstain_by_instance_r20"] == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
    assert bso["bottom_courtyard_flags_total_r20"] == 2
    g12 = run_doc["hypothesis_test"]["mechanism_observation"]["guards_g1_g2"]
    assert g12["counts"]["axis_early_stop_triggered"] is True
    assert g12["counts"]["g1_bottom_courtyard_non_abstain_r20"] == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g1_r16_baseline_live"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    # 判据布尔（reject_guards 支命中、reject_m1 未命中、supported 未落）
    assert m["crit_reject_guards_broken"] is True
    assert m["crit_reject_m1_ge_0_771429"] is False
    assert m["crit_supported_ordering_not_worse_than_r19"] is False
    assert m["crit_marginal_m1_lt_0_771429"] is True
    # 援引分记（两条款分开记、互不合并；机制观察单列）：旗级零字面援引
    # +notes 级 4/12+4/12+间隙支落支与 G1 破坏直接构成
    cc = run_doc["hypothesis_test"]["mechanism_observation"][
        "criterion_citation_observation"]
    counts = cc["citation_counts"]
    assert counts["flag_level_s5b_literal"] == 0
    assert counts["flag_level_iiia_literal"] == 0
    assert counts["flag_level_branch_literal"] == 0
    assert counts["flag_level_s5b_sources"] == \
        S74.S5B_FLAG_CITE_REGISTERED == []
    assert counts["flag_level_iiia_sources"] == []
    assert counts["notes_level_s5b"] == 4
    assert counts["notes_level_iiia"] == 4
    assert counts["notes_level_s5b_sources"] == S74.S5B_NOTES_CITE_REGISTERED
    assert counts["notes_level_iiia_sources"] == \
        S74.IIIA_NOTES_CITE_REGISTERED
    assert cc["branch_counts_flag_level"] == {"branch1_gap_report": 2,
                                              "branch2_intrusion_report": 4,
                                              "branch3_residual_abstain": 7}
    assert cc["branch1_notes_level_dispatches"] == 2
    assert "r18" in counts["dual_baseline_r18_s5b"]
    assert "r19" in counts["dual_baseline_r19_iiia"]


# ---------------------------------------------------------------------------
# 守卫、run 记录身份与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；既有且
    不同→fail；_commit=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写；run-r20 盘上件不可覆写）。"""
    assert S74.overwrite_guard(None, b"abc") == "write"
    assert S74.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S74.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S74._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S74._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S74._commit(p, b"abc", "probe")


def test_run_record_canonical_identity_and_letter_verdict(run_doc):
    """run-r20 盘上件：同参重建两次 byte-exact+盘上件=canonical 重建+
    轮次身份（r20/2026-09-09/development 域）+verdict=reject（唯一正式
    裁决）+落支 reject_guards（G1 破坏）+四元组与 r19 基准元组+指引合成
    轮次性质+渲染零变更。"""
    b1 = hashing.canonical_json_bytes(S74.build_run())
    b2 = hashing.canonical_json_bytes(S74.build_run())
    assert b1 == b2  # 同参重建 byte-exact
    path = os.path.join(CAL_DIR, "calibration-run-r20.json")
    raw = open(path, "rb").read()
    assert raw == b1  # 盘上件=canonical 重建（byte-exact 可重跑）
    assert hashing.sha256_file(path).startswith("6573a59a")
    doc = json.loads(raw.decode("utf-8"))
    assert doc["kind"] == "tl2_calibration_run_r20"
    assert doc["round_id"] == ROUND_ID
    assert doc["round_label"] == ROUND_LABEL
    assert doc["declared_date"] == DECLARED_DATE
    assert doc["evaluation_domain"] == "development"
    assert doc["evaluation_domain_note"]["in_calibrated_range"] is False
    assert doc["instrument_change"]["changed"] is False
    assert doc["instrument_change"]["axis_id"] == \
        "A3_criterion_contact_clarification+A2_blackdot_instrument_annotation"
    hyp = doc["hypothesis_test"]
    m = hyp["measurement"]
    assert hyp["hypothesis_id"] == "axis-plan-r20-combo-additivity"
    assert hyp["verdict"] == "reject" and m["verdict"] == "reject"
    assert "G1/G2 任一破坏" in m["letter_branch"]
    assert "reject" in m["letter_branch"] or "(r)" in m["letter_branch"]
    assert "采最优单轴 r19" in m["letter_branch"]
    assert m["r20_m_tuple_6dp"] == {"M1": 0.636364, "M2": 0.285714,
                                    "M3": 6, "M4": 0.25}
    assert m["r19_reference_tuple"] == {"M1": 0.461538, "M2": 0.571429,
                                        "M3": 4, "M4": 0.211111}
    assert m["top_abstain_count_r20"] == 14
    assert m["top_abstain_flags_r20"] == 22
    assert "14/22" in m["top_abstain_rate_r20_arithmetic"]
    assert m["contact_family_abstain_flags_rubric_r20"] == 2
    # 指引合成轮次性质（§5B+(iii-a) 并集；渲染零变更）——instrument_
    # change 归因注记与变更变量登记（run-r20 无独立 round_nature 键，
    # 轮次性质以 instrument_change 归因节承载=盘上事实）
    ic = doc["instrument_change"]
    att = json.dumps(ic["attribution_note"], ensure_ascii=False)
    assert "判读指引合成" in att and "§5B" in att
    assert "(iii-a)" in att and "渲染零变更" in att
    var = ic["changed_variables_registered"][0]
    assert var["id"] == "guidance-combo-s5b-plus-s4-iiia-union"
    desc = json.dumps(var["description"], ensure_ascii=False)
    assert "§5B" in desc and "§4(iii-a)" in desc
    assert "renders-r14b" in desc and "字节复用" in desc
    assert var["target"].startswith("observation-guidance-r20.md")


def test_gt_dual_zero_hits_joint_gate_and_in_range_false(run_doc):
    """GT 双口径全轮零命中：union=0/13、agreement=0/13（r19 唯一命中
    R19T-009 未再现）；代表配置（top-i1+bottom-i2，双 tie）聚合
    12/4/0.333333、joint not_met、连续=0；in_calibrated_range 恒 False
    （run 与 compliance 双处）；12 格全部≥1 旗（零旗标派次=0）。"""
    doc = run_doc
    dual = doc["gt_match_dual"]
    assert (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) == (0, 0, 13)
    assert dual["union"]["gt_ids"] == []
    assert dual["union"]["gt_recall_union"] == 0.0
    comp = doc["compliance_representative"]
    agg = doc["aggregation_representative"]
    assert (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) == (12, 4, 0.333333, 0.0, 0.0)
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
        {"top": "top-i1", "bottom": "bottom-i2"}
    assert doc["representative_configuration"]["selection"]["top"][
        "tie"] is True
    assert doc["representative_configuration"]["selection"]["bottom"][
        "tie"] is True
    assert doc["reader"]["zero_flag_parts"]["parts"] == []
    assert doc["view_layer"]["bottom"]["abstain_rate"]["median"] == 0.0


def test_experiment_ledger_five_round_account_and_stage2(run_doc):
    """五轮对照账完整性：r16/r17/r18/r19/r20 五行并列（M 元组逐一相等）
    +r20 资格门剔除不参与排序（r20_eligibility=False）+排序（不含 r20）
    =r19 第一/r18 第二/r16 参照/r17 末位+显著收益 0.135065≥0.10 描述层
    命中+阶段2 结论=组合劣化（reject）采最优单轴 r19、R21 不做+M1/M2/M3
    降 M4 走阔方向账+in_calibrated_range 恒 False 收尾。"""
    ecl = run_doc["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]
    assert ecl["r20_measured"]["M1"] == 0.636364
    assert ecl["r20_measured"]["M2"] == 0.285714
    assert ecl["r20_measured"]["M3"] == 6
    assert ecl["r20_measured"]["M4"] == 0.25
    assert ecl["r20_measured"]["M1_arithmetic"] == "14/22"
    assert ecl["r20_measured"]["M2_arithmetic"] == "4/14"
    assert ecl["r16_baseline_registered"]["M1"] == 0.771429
    assert ecl["r16_baseline_registered"]["M4"] == 0.261904
    assert ecl["r17_axis1_row"] == {"M1": 0.88, "M2": 0.75, "M3": 8,
                                    "M4": 0.333333}
    assert ecl["r18_axis2_row"] == {"M1": 0.645161, "M2": 0.684211,
                                    "M3": 13, "M4": 0.277778}
    assert ecl["r19_axis3_row"] == {"M1": 0.461538, "M2": 0.571429,
                                    "M3": 4, "M4": 0.211111}
    rk = ecl["ranking_by_comparison_rule"]
    assert rk["ranking_order_best_first"] == ["r19_axis3", "r18_axis2",
                                              "r16_baseline", "r17_axis1"]
    assert rk["r20_eligibility"] is False
    assert set(rk["rows_registered"]) == {"r16_baseline", "r17_axis1",
                                          "r18_axis2", "r19_axis3",
                                          "r20_combo"}
    assert rk["rows_registered"]["r20_combo"] == {"M1": 0.636364,
                                                  "M2": 0.285714, "M3": 6,
                                                  "M4": 0.25}
    sb = ecl["significant_benefit_vs_r16"]
    assert sb["met"] is True
    assert sb["r20_m1_absolute_drop"] == 0.135065
    assert round(0.771429 - 0.636364, 6) == 0.135065
    sc = ecl["stage2_conclusion"]
    assert sc["verdict"] == "reject"
    assert "采最优单轴" in sc["conclusion"] and "r19" in sc["conclusion"]
    assert "R21 不做" in sc["conclusion"]
    assert sc["r21_full_combination_trigger_dev_r19"] is False
    fd = ecl["direction_vs_r16"]
    assert fd["M1"].startswith("down") and fd["M2"].startswith("down")
    assert fd["M3"].startswith("down") and fd["M4"].startswith("0.261904")
