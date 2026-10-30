"""R22 执行包测试（s77_calibration_r22_compare / calibration-run-r22）——
同指引重复轮（r16 先例：r15→r16 同指引重复、渲染零变更、仅实例重抽；
本轮=第二十二轮）：判读指引=observation-guidance-r19.md 字节复用
（8633bda5 锚、零新建指引文件、§6 前缀差异=R19T- 落盘原文 vs R22T/R22B
派发层覆盖）、渲染零变更=renders-r14b 四图字节复用、GT/阈值/协议零变更、
changed_variables=0（唯一操作=reader 实例群重抽 12 派次）+【跳号声明】
r21=axis-plan 冻结件预留的全组合条件位（R20 G1 破坏→条件未命中→未执行）。
预注册假设（r20-dev-record-candidate-r19-config-same-guidance-repeat）
复制性三分判据轮后裁决=regressed（唯一正式裁决）：(g) 支命中
regressed_guards（G2 top 几何门面积比出局条目 R19=0→R22=2 破坏；支序
先行）——而 M1=0.390244 实际落在复制带 [0.361538, 0.561538] 内（甚至
优于 r19 的 0.461538）、contact=2≤7、G1=bottom courtyard 非弃权 0/0/0
维持——分岔如实登记（字母=regressed 与 M1 带内复制两账分列、不合并）；
(g) 支 M1 ≥0.771429 未命中（r16 基线 27/35 live 复算交叉核对）；
(d) 支 M1 <0.771429 真但守门破坏→不落。R22 四元组
(0.390244, 0.2, 4, 0.104545)（M1=top 16/41、M2=bottom 2/10、M3=黑点族
rubric 口径 4、M4=top 极差 0.104545）；机制观察单列：rubric 三族
contact 2/existence_blackdot 4/existence_other 12（r13–r16 132 条重放
对拍逐一相等；contact 链 8/15/5/10）对照 r19（4/4/14）与 r20（2/6/10）；
黑点 4=与 r19 持平（guidance-r19 无 §5B 节、bottom 黑点仍存在性弃权
——bottom-i2 两条）+黑点转非弃权旗 6 条+黑点判正常派次 2；援引分记
（旗级 §5B/(iii-a)/分支( 全 0、notes 级 §5B=0/12、(iii-a)=6/12；r19
基线=旗级 6+2、notes 10/12 在案）+六行对照账（r16
0.771429/0.857143/12/0.261904、r17 0.88/0.75/8/0.333333、r18
0.645161/0.684211/13/0.277778、r19 0.461538/0.571429/4/0.211111、r20
0.636364/0.285714/6/0.25、r22 0.390244/0.2/4/0.104545）——r22 与 r20
均 G 守门破坏不入排序（资格门剔除）、排序不变=r19_axis3 第一；
M4 双样本单列（0.104545 vs 0.211111，均 ≤0.20 门=第二次样本过门、不进
字母、不合并分布）+ GT 双口径 union=agreement=1/13
（GT-REVC-P1-L1SHORT，prep1-top-i2 R22T-007+prep1-top-i3 R22T-017 双
实例命中=agreement 口径自 r12 引入以来首次计入——r12 以来第二次逐实例
命中、且首次两实例一致命中，如实登记）+ 2 格零旗标（bottom-i1 两板、
bottom 中位数=None 口径触发）+ in_calibrated_range 恒 False +
development 域。

覆盖（14 测试，只读 out/、零子进程/零网络/零写盘）：
- 输入核验 fail-closed：12 件 reader-raw-r22 合法解析+实例旗数/弃权
  记账；缺文件→OSError、_fail→SystemExit、视角后缀缺失→ValueError；
  12 件盘态钉死前缀；FROZEN_SHA256 全锚实测一致；
- rubric 链重放对拍：r13–r16 132 条弃权旗重放（per_flag_total=132、
  blackdot 9/14/8/12、contact 8/15/5/10）+classify 优先级单元+r22 家族
  计数（2/4/12/0/0 与登记一致）；
- M 元组：_m_tuple_6dp 定点键+构造小样例 round_view_aggregate/_median3/
  M4 极差+r16 基线双侧 live 复算（27/35、12/14、courtyard 0/0/0）；
- 复制性三支边界：adjudicate_replication 纯函数构造用例——replicated
  （带内+contact≤7+守门全维持）、regressed_guards（带内但 G2 破坏=
  本轮实况）、regressed_m1（M1 ≥0.771429）、drifted（带外但 M1<基线且
  守门维持）与支序/互斥 RuntimeError（自洽性守卫）；
- 守卫与确定性：overwrite_guard 三态+_commit 落盘语义；run-r22 盘上件
  canonical byte 与重建一致+轮次身份+verdict=regressed+落支
  regressed_guards+M 元组+r19 基准元组+changed_variables=0；GT 双口径
  1/13 双实例命中+joint not_met+in_calibrated_range 恒 False+六行对照
  账+排序（r20/r22 资格门剔除、r19_axis3 第一）+M4 双样本单列。
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
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")


def _load_s77():
    path = os.path.join(REPO, "scripts", "s77_calibration_r22_compare.py")
    spec = importlib.util.spec_from_file_location("s77_calibration_r22",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S77 = _load_s77()


@pytest.fixture(scope="module")
def run_doc():
    """run-r22 文档内存构建（纯函数；只读输入、零写盘）。"""
    return S77.build_run()


@pytest.fixture(scope="module")
def instances():
    """六实例主记录（逐实例两板合计口径；只读输入、零写盘）。"""
    parsed = {key: S77.parse_reader_raw(rel)
              for key, rel in S77.RAW_FILES.items()}
    deriv = S77._json_load(S77.REL_DERIV_R5)
    gt_applied = S77._gt_entries_with_r5_reprojection(S77.REL_GT_V2, deriv)
    gt_prep1 = S77._gt_entries_with_r5_reprojection(S77.REL_GT_V1, deriv)
    return {name: S77.build_instance_record(
        name, S77.INSTANCES[name], parsed, gt_applied, gt_prep1)
        for name in INSTANCE_ORDER}


# ---------------------------------------------------------------------------
# 输入核验（fail-closed）
# ---------------------------------------------------------------------------

def test_reader_raw_inputs_parse_and_flag_counts():
    """12 件 reader-raw-r22 全在盘、合法解析；实例旗数 11/10/20/0/4/6、
    弃权 5/4/7/0/2/0；拒收为零；R22T/R22B 前缀随派发层覆盖落盘（指引
    §6 落盘原文仍=R19T-/R19B-=字节复用前缀差异登记）；5 个有旗实例全部
    同实例跨板连续+bottom-i1 两板零旗标（与 prep-record naming 声明相
    符）。"""
    parsed = {k: S77.parse_reader_raw(rel)
              for k, rel in S77.RAW_FILES.items()}
    assert sorted(parsed) == sorted(S77.RAW_FILES)
    for n in INSTANCE_ORDER:
        cnts = [len(parsed[p]["images"][0]["flags"])
                for p in S77.INSTANCES[n]["parts"]]
        # 两板合计与 run 实测一致（11/10/20/0/4/6）
        assert sum(cnts) == {"top-i1": 11, "top-i2": 10, "top-i3": 20,
                             "bottom-i1": 0, "bottom-i2": 4,
                             "bottom-i3": 6}[n]
    for k, p in parsed.items():
        assert p["reader_id"].startswith("reader-r22-")
        assert p["direct_json_parse"] is True
        assert p["repair"] == "no_repair"
        for img in p["images"]:
            assert img["rejected"] == []
            for f in img["flags"]:
                assert f["flag_id"].startswith(("R22T-", "R22B-"))
    # 弃权记账（5/4/7/0/2/0；按实例两板合计）
    abst = {n: 0 for n in INSTANCE_ORDER}
    for n in INSTANCE_ORDER:
        for p in S77.INSTANCES[n]["parts"]:
            for img in parsed[p]["images"]:
                for f in img["flags"]:
                    assert f["abstain"] is not None
                    if f["abstain"]:
                        abst[n] += 1
    assert abst == {"top-i1": 5, "top-i2": 4, "top-i3": 7,
                    "bottom-i1": 0, "bottom-i2": 2, "bottom-i3": 0}


def test_parse_reader_raw_fail_closed_and_view_mapping():
    """fail-closed 语义：缺文件→OSError（不返回解析结果）；_fail→
    SystemExit；view_for_image 确定性映射（*-top.png→top、*-bottom.png→
    bottom、无后缀→ValueError）。"""
    with pytest.raises(OSError):
        S77.parse_reader_raw(
            "out/v3-tl2/calibration/reader-raw-r22-NO-SUCH-FILE.txt")
    with pytest.raises(SystemExit):
        S77._fail("输入缺失（fail-closed）: <构造缺件>")
    assert S77.view_for_image("board-applied-top.png") == "top"
    assert S77.view_for_image("board-prep1-bottom.png") == "bottom"
    with pytest.raises(ValueError):
        S77.view_for_image("board-side.png")


def test_pinned_raw_prefixes_and_frozen_anchor_hashes():
    """12 件盲读原始件盘态钉死前缀逐字命中+输入先验锚全集合（协议/GT/
     指引 r8–r20/prep/axis-plan/12 reader 件/PNG/PDF/受保护链件）与盘上
    实测逐一相等（哈希不符即拒算前提）；本轮指引锚=guidance-r19
    8633bda5（字节复用本体）、prep-r22=63346ee6、run-r16（M1 基线复算
    输入）在锚集；run-r22=本包唯一新建输出、不在 FROZEN 锚集。"""
    for key, prefix in S77.RAW_PINNED_PREFIXES.items():
        got = S77._sha(S77.RAW_FILES[key])
        assert got.startswith(prefix), (key, got[:8], prefix)
    assert S77.FROZEN_SHA256[S77.REL_GUIDANCE_R19].startswith("8633bda5")
    assert S77.FROZEN_SHA256[S77.REL_PREP_R22].startswith("63346ee6")
    assert S77.FROZEN_SHA256[S77.REL_GUIDANCE_R20].startswith("9cdac9ed")
    assert S77.FROZEN_SHA256[S77.REL_RUN_R16].startswith(
        hashing.sha256_file(os.path.join(REPO, S77.REL_RUN_R16))[:8])
    assert len(S77.FROZEN_SHA256) > 40
    for rel, want in S77.FROZEN_SHA256.items():
        assert S77._sha(rel) == want, rel
    assert S77.REL_RUN_R22 not in S77.FROZEN_SHA256


# ---------------------------------------------------------------------------
# rubric 链重放对拍+优先级单元+r22 家族计数
# ---------------------------------------------------------------------------

def test_rubric_replay_r13_r16_chain_matches_frozen_counts():
    """r13–r16 132 条弃权旗 rubric 机械重放对拍：逐旗 family 与分型件
    在案记录逐一相等；contact 链 8/15/5/10、blackdot 链 9/14/8/12 与已
    冻结件（分型件 matrix+prep-record 锚）一致。"""
    typology_doc = S77.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    proof = S77.replay_typology_families(typology_doc, kt)
    assert proof["per_flag_total"] == 132
    assert proof["contact_counts"] == {"r13": 8, "r14": 15,
                                       "r15": 5, "r16": 10}
    assert proof["blackdot_counts"] == {"r13": 9, "r14": 14,
                                        "r15": 8, "r16": 12}
    assert typology_doc["matrix"]["round_totals"]["r16"]["families"][
        "contact"] == 10


def test_rubric_classify_and_r22_family_counts(run_doc, instances):
    """classify 优先级单元+r22 全部 18 条弃权旗逐旗 rubric 分类：
    contact=2（全视；top 2+bottom 0；r16 基线 10）、existence_blackdot=4
    （与 r19 持平）、existence_other=12、semantic_confusion=0、other=0
    ——与登记表/run 机制观察口径逐一相等；黑点弃权旗 4 条全弃权、黑点
    转非弃权旗 6 条。"""
    typology_doc = S77.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    # 优先级单元（blackdot 先于 contact；泛化兜底→existence_other）
    fam, _ = S77.rubric_classify(
        "一枚黑色钻孔圆点紧贴焊盘，无法分辨真实接触与视觉贴近", kt)
    assert fam == "existence_blackdot"
    fam, _ = S77.rubric_classify(
        "两 courtyard 轮廓看似相接，无法区分真实接触与视觉贴近", kt)
    assert fam == "contact"
    fam, _ = S77.rubric_classify("该形态无法负责任确认", kt)
    assert fam == "existence_other"
    # r22 全旗套用
    rows = S77.build_rubric_rows_r22(instances, kt)
    fam_counts = {fam: sum(1 for r in rows
                           if r["abstain"] and r["family"] == fam)
                  for fam in ("contact", "existence_blackdot",
                              "existence_other", "semantic_confusion",
                              "other")}
    assert fam_counts == S77.R22_FAMILY_COUNTS_REGISTERED
    assert fam_counts == {"contact": 2, "existence_blackdot": 4,
                          "existence_other": 12, "semantic_confusion": 0,
                          "other": 0}
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    assert mo["black_dot_tracking"]["rubric_families"]["counts"] == \
        fam_counts
    assert len(rows) == 51  # 51 旗逐旗入账（弃权 18+非弃权 33）
    assert sum(1 for r in rows if r["abstain"]) == 18


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
    M3 整数直接）；round_view_aggregate 三实例两板合计（16/41、2/10）；
    M4=top 逐实例弃权率先 6 位取率再取极差 0.454545−0.35=0.104545；
    median3 恰 3 值取第 2。"""
    assert S77._m_tuple_6dp(0.390244, 0.2, 4, 0.104545) == \
        (390244, 200000, 4, 104545)
    assert S77._m_tuple_6dp(0.461538, 0.571429, 4, 0.211111) == \
        (461538, 571429, 4, 211111)
    inst = {
        "top-i1": _synthetic_instance("top-i1", "top", 11, 5, 0.454545),
        "top-i2": _synthetic_instance("top-i2", "top", 10, 4, 0.4),
        "top-i3": _synthetic_instance("top-i3", "top", 20, 7, 0.35),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 0, 0, 0.0),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 2, 0.5),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 6, 0, 0.0),
    }
    ab, fl = S77.round_view_aggregate(inst, ("top-i1", "top-i2", "top-i3"))
    assert (ab, fl) == (16, 41)
    assert S77.cal._ratio(ab, fl) == 0.390244
    ab_b, fl_b = S77.round_view_aggregate(
        inst, ("bottom-i1", "bottom-i2", "bottom-i3"))
    assert (ab_b, fl_b) == (2, 10)
    assert S77.cal._ratio(ab_b, fl_b) == 0.2
    rates = [0.454545, 0.4, 0.35]
    assert S77.cal._round6(max(rates) - min(rates)) == 0.104545
    assert S77._median3([11, 10, 20]) == 11
    assert S77._median3([0, 4, 6]) == 4
    assert S77._median3([5, 1, 9]) == 5


def test_view_layer_and_r16_baseline_live_replay():
    """r16 基线=同一聚合逻辑对 run-r16 内嵌输入双侧复算（不手工抄数）：
    top 27/35=0.771429、bottom 12/14=0.857143、G1 基线 courtyard 非弃权
    0/0/0；视角层构造小样例（bottom-i1 零旗→None 分母口径触发）。"""
    run16 = S77._json_load(S77.REL_RUN_R16)
    assert S77.r16_top_abstain_aggregate_live(run16) == (27, 35)
    assert S77.r16_bottom_abstain_aggregate_live(run16) == (12, 14)
    assert S77.r16_baseline_courtyard_live(run16) == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    layer = S77.build_view_layer({
        "top-i1": _synthetic_instance("top-i1", "top", 11, 5, 0.454545),
        "top-i2": _synthetic_instance("top-i2", "top", 10, 4, 0.4),
        "top-i3": _synthetic_instance("top-i3", "top", 20, 7, 0.35),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 0, 0, None),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 2, 0.5),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 6, 0, 0.0),
    })
    assert layer["top"]["abstain_rate"]["median"] == 0.4
    assert layer["top"]["abstain_rate_range"] == 0.104545
    assert layer["bottom"]["abstain_rate"]["median"] is None
    assert layer["bottom"]["abstain_rate_range"] == 0.5


# ---------------------------------------------------------------------------
# 复制性三支边界（adjudicate_replication 构造用例）
# ---------------------------------------------------------------------------

def test_adjudicate_replicated_branch_and_band_boundaries():
    """(p) 支：M1 带内（6 位定点整数交叉相乘）+contact≤7+守门全维持→
    replicated；带宽端点边界（恰=带下沿 361538 与带上沿 561538 入带、
    带外 361537/561539 出带）；contact 恰=7 入、8 出。"""
    # 带中心附近（r19 实际 0.461538）：replicated
    assert S77.adjudicate_replication(6, 13, 2, True) == \
        ("replicated", "replicated")
    # 恰=带下沿（361538×35 ≤ 12553830）→入带
    assert S77.adjudicate_replication(361538, 1000000, 2, True) == \
        ("replicated", "replicated")
    # 恰=带上沿（561538×10^6 ≤ 561538×10^6）→入带
    assert S77.adjudicate_replication(561538, 1000000, 2, True) == \
        ("replicated", "replicated")
    # 带下沿之下（361537×10^6 < 361538×10^6）→出带→drifted（守门维持、
    # M1<0.771429）
    assert S77.adjudicate_replication(361537, 1000000, 2, True) == \
        ("drifted", "drifted")
    # 带上沿之上（561539×10^6 > 561538×10^6）→出带→drifted
    assert S77.adjudicate_replication(561539, 1000000, 2, True) == \
        ("drifted", "drifted")
    # contact 恰=7 入门、8 出门（出门→drifted，守门维持、M1<0.771429）
    assert S77.adjudicate_replication(6, 13, 7, True) == \
        ("replicated", "replicated")
    assert S77.adjudicate_replication(6, 13, 8, True) == \
        ("drifted", "drifted")


def test_adjudicate_regressed_branches_and_mutual_exclusion():
    """(g) 两途径+支序：G1/G2 任一破坏→regressed_guards（支序最高，
    即使 replicated 条件全真=本轮实况：带内+G2 破坏）；M1 ≥0.771429
    （6 位定点整数交叉相乘）→regressed_m1；边界（恰=阈值入 regressed）；
    (d) drifted=未达 replicated 且 M1<0.771429 且守门维持；带内
    replicated∩regressed_m1 互斥由判据字面保证、同中 RuntimeError。"""
    # 本轮实际落支：M1=16/41 带内、contact=2≤7、但 G2 破坏→regressed_
    # guards（支序 regressed 在 replicated 之前）
    assert S77.adjudicate_replication(16, 41, 2, False) == \
        ("regressed", "regressed_guards")
    # 守门维持时同输入=replicated（分岔两侧构造）
    assert S77.adjudicate_replication(16, 41, 2, True) == \
        ("replicated", "replicated")
    # G1 破坏同走 regressed_guards（guards_ok=False 为任一守门破坏）
    assert S77.adjudicate_replication(16, 41, 2, False) == \
        ("regressed", "regressed_guards")
    # regressed_m1：36/46=0.782609 ≥0.771429（36×10^6 ≥ 771429×46）
    assert S77.adjudicate_replication(36, 46, 2, True) == \
        ("regressed", "regressed_m1")
    # 恰在阈值（771429/10^6=0.771429，6 位定点整数交叉相乘恰等）→
    # regressed_m1（守门维持、支序 regressed 在 replicated 前——带内与
    # 阈值不相交，此处为带外高端点）
    assert S77.adjudicate_replication(771429, 1000000, 2, True) == \
        ("regressed", "regressed_m1")
    # 阈值之下且带外（26/35=0.742857<0.771429、>0.561538）→drifted
    assert S77.adjudicate_replication(26, 35, 2, True) == \
        ("drifted", "drifted")
    # 支序：G 破坏+M1≥0.771429 同中→regressed_guards 优先
    assert S77.adjudicate_replication(36, 46, 2, False) == \
        ("regressed", "regressed_guards")
    # 自洽性守卫：带内且 M1≥0.771429 两支互斥被同时命中→RuntimeError
    # （构造：band 上沿=reject 下沿交叠不存在——带内上沿 561538<771429，
    # 互斥由字面保证；此处以守卫分支直测：band 内→非 regressed_m1）
    verdict, key = S77.adjudicate_replication(561538, 1000000, 2, True)
    assert (verdict, key) == ("replicated", "replicated")


# ---------------------------------------------------------------------------
# G1/G2 守门与援引分记（机制观察）
# ---------------------------------------------------------------------------

def test_guards_g1_g2_and_citation_observation(run_doc, instances):
    """G1 实测（操作化定义）：bottom courtyard 非弃权 0/0/0=G1 维持
    （r16 基线 live 重放对照、r20 破坏 2/0/0 在案=分岔记录）；G2 破坏
    （几何门 R19=0→R22=2）；guard_channel g1_ok=True、g2=False、
    guards_ok=False；判据布尔（regressed_guards 命中/regressed_m1 未中/
    replicated 两项命中/drifted 前提真）；援引分记（旗级 §5B/(iii-a)/
    分支( 全 0、notes 级 §5B=0/12、(iii-a)=6/12；r19 基线=旗级 6+2、
    notes 10/12 在案；落支 间隙 6+侵入 1+残余弃权 2）。"""
    assert S77.bottom_courtyard_non_abstain(instances) == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    m = run_doc["hypothesis_test"]["measurement"]
    gc = m["guard_channel"]
    assert gc["g1_ok"] is True
    assert gc["g2_guard_ok"] is False
    assert gc["guards_ok"] is False
    assert gc["g2_geometry_gate_r19"] == 0
    assert gc["g2_geometry_gate_r22"] == 2
    g12 = run_doc["hypothesis_test"]["mechanism_observation"]["guards_g1_g2"]
    assert g12["counts"]["guards_ok"] is False
    assert g12["counts"]["g1_ok"] is True
    assert g12["counts"]["g2_guard_ok"] is False
    assert g12["counts"]["g1_bottom_courtyard_non_abstain_r22"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g1_r16_baseline_live"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g1_r20_broken_registered"] == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g2_geometry_gate_r19"] == 0
    assert g12["counts"]["g2_geometry_gate_r22"] == 2
    # 判据布尔（regressed_guards 支命中、regressed_m1 未命中、
    # replicated 两判据命中、drifted 前提真但不落=支序）
    assert m["crit_regressed_guards_broken"] is True
    assert m["crit_regressed_m1_ge_0_771429"] is False
    assert m["crit_replicated_m1_in_band"] is True
    assert m["crit_replicated_contact_le_7"] is True
    assert m["crit_drifted_m1_lt_0_771429"] is True
    # M1 复制带与阈值（6 位定点；与盘上登记逐一相等）
    assert m["replication_band_6dp"] == [S77.REPL_BAND_LO_6DP,
                                         S77.REPL_BAND_HI_6DP]
    assert m["reject_m1_threshold_6dp"] == S77.REJECT_M1_MIN_6DP
    # 援引分记（两条款分开记、互不合并；机制观察单列）：旗级零字面援引
    # +notes 级 §5B=0（指引字节复用无 §5B 节）+notes 级 (iii-a)=6/12
    cc = run_doc["hypothesis_test"]["mechanism_observation"][
        "criterion_citation_observation"]
    counts = cc["citation_counts"]
    assert counts["flag_level_s5b_literal"] == 0
    assert counts["flag_level_iiia_literal"] == 0
    assert counts["flag_level_branch_literal"] == 0
    assert counts["flag_level_s5b_sources"] == \
        S77.S5B_FLAG_CITE_REGISTERED == []
    assert counts["flag_level_iiia_sources"] == []
    assert counts["notes_level_s5b"] == 0
    assert counts["notes_level_s5b_sources"] == S77.S5B_NOTES_CITE_REGISTERED
    assert counts["notes_level_iiia"] == 6
    assert counts["notes_level_iiia_sources"] == \
        S77.IIIA_NOTES_CITE_REGISTERED
    # r19 基线对照（在案登记：旗级 (iii-a) 6 旗+分支( 2 旗、notes 10/12）
    assert "6" in counts["baseline_r19_iiia"]
    assert "10/12" in counts["baseline_r19_iiia"]
    assert "1/12" in counts["baseline_r18_s5b"]
    # (iii-a) 逐旗落支：间隙 6+侵入 1+残余弃权 2；间隙支 notes 级 2 派次
    assert cc["branch_counts_flag_level"] == {"branch1_gap_report": 6,
                                              "branch2_intrusion_report": 1,
                                              "branch3_residual_abstain": 2}
    assert cc["branch1_notes_level_dispatches"] == 2


# ---------------------------------------------------------------------------
# 守卫、run 记录身份与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；既有且
    不同→fail；_commit=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写；run-r22 盘上件不可覆写）。"""
    assert S77.overwrite_guard(None, b"abc") == "write"
    assert S77.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S77.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S77._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S77._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S77._commit(p, b"abc", "probe")


def test_run_record_canonical_identity_and_letter_verdict(run_doc):
    """run-r22 盘上件：同参重建两次 byte-exact+盘上件=canonical 重建+
    轮次身份（r22/2026-09-09/development 域）+verdict=regressed（唯一
    正式裁决）+落支 regressed_guards（G2 破坏）+四元组与 r19 参照元组+
    同指引重复轮轮次性质（指引字节复用/渲染零变更/changed_variables=0/
    轴位=none_zero_change_repeat_round）+判据原文摘录与 prep-record 逐
    字一致。"""
    b1 = hashing.canonical_json_bytes(S77.build_run())
    b2 = hashing.canonical_json_bytes(S77.build_run())
    assert b1 == b2  # 同参重建 byte-exact
    path = os.path.join(CAL_DIR, "calibration-run-r22.json")
    raw = open(path, "rb").read()
    assert raw == b1  # 盘上件=canonical 重建（byte-exact 可重跑）
    assert hashing.sha256_file(path).startswith("80a12c05")
    doc = json.loads(raw.decode("utf-8"))
    assert doc["kind"] == "tl2_calibration_run_r22"
    assert doc["round_id"] == ROUND_ID
    assert doc["round_label"] == ROUND_LABEL
    assert doc["declared_date"] == DECLARED_DATE
    assert doc["evaluation_domain"] == "development"
    assert doc["evaluation_domain_note"]["in_calibrated_range"] is False
    assert doc["instrument_change"]["changed"] is False
    assert doc["instrument_change"]["axis_id"].startswith(
        "none_zero_change_repeat_round")
    assert doc["instrument_change"]["changed_variables_registered"] == []
    hyp = doc["hypothesis_test"]
    m = hyp["measurement"]
    assert hyp["hypothesis_id"] == \
        "r20-dev-record-candidate-r19-config-same-guidance-repeat"
    assert hyp["verdict"] == "regressed" and m["verdict"] == "regressed"
    assert "(g)" in m["letter_branch"]
    assert "G1/G2 任一破坏" in m["letter_branch"]
    assert "regressed" in m["letter_branch"]
    assert m["r22_m_tuple_6dp"] == {"M1": 0.390244, "M2": 0.2,
                                    "M3": 4, "M4": 0.104545}
    assert m["r19_reference_tuple"] == {"M1": 0.461538, "M2": 0.571429,
                                        "M3": 4, "M4": 0.211111}
    assert m["top_abstain_count_r22"] == 16
    assert m["top_abstain_flags_r22"] == 41
    assert "16/41" in m["top_abstain_rate_r22_arithmetic"]
    assert m["contact_family_abstain_flags_rubric_r22"] == 2
    # 预注册判据摘录=prep-record adjudication 原文（逐字一致；7 键）
    prep = S77._json_load(S77.REL_PREP_R22)
    adj = prep["hypothesis_test"]["adjudication"]
    q = hyp["preregistered_criteria_quote"]
    for k in ("descriptive_boundary_note", "drifted",
              "mechanism_observation_separate", "metric_lesson_separate",
              "m4_second_sample_separate", "regressed", "replicated"):
        assert q[k] == adj[k], k
    assert prep["hypothesis_test"]["hypothesis_id"] == hyp["hypothesis_id"]
    # changed_variables=0（prep 侧同为空=指引/渲染字节复用+GT/阈值/协议
    # 零变更；唯一操作=实例群重抽）
    assert prep["changed_variables"] == []
    assert prep["no_instrument_change"] is True
    assert prep["guidance_reuse"]["mode"] == "byte_reuse_zero_change"
    assert prep["guidance_reuse"]["base_sha256"].startswith("8633bda5")


def test_gt_dual_first_agreement_hit_joint_gate_in_range_false(run_doc):
    """GT 双口径 union=agreement=1/13：GT-REVC-P1-L1SHORT 双实例命中
    （prep1-top-i2 R22T-007+prep1-top-i3 R22T-017）=agreement 口径首次
    计入（r12 以来第二次逐实例命中、首次两实例一致命中）；代表配置
    （top-i1+bottom-i2，双双非 tie）聚合 15/7/0.466667、joint not_met、
    连续=0；in_calibrated_range 恒 False（run 与 compliance 双处）；
    2 格零旗标（bottom-i1 两板、bottom 中位数=None 口径触发）。"""
    doc = run_doc
    dual = doc["gt_match_dual"]
    assert (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) == (1, 1, 13)
    assert dual["union"]["gt_ids"] == ["GT-REVC-P1-L1SHORT"]
    assert dual["agreement"]["gt_ids"] == ["GT-REVC-P1-L1SHORT"]
    assert dual["union"]["gt_recall_union"] == 0.076923
    assert dual["agreement"]["gt_recall_agreement"] == 0.076923
    hit = [pg for pg in dual["per_gt"] if pg.get("hits")]
    assert len(hit) == 1
    assert hit[0]["gt_id"] == "GT-REVC-P1-L1SHORT"
    assert hit[0]["matched_by_count"] == 2
    got = {(h["flag_id"], h["instance"], h["state"])
           for h in hit[0]["hits"]}
    assert got == {("R22T-007", "top-i2", "prep1"),
                   ("R22T-017", "top-i3", "prep1")}
    comp = doc["compliance_representative"]
    agg = doc["aggregation_representative"]
    assert (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) == (15, 7, 0.466667, 0.0, 0.0)
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
        "tie"] is False
    assert doc["representative_configuration"]["selection"]["bottom"][
        "tie"] is False
    parts = doc["reader"]["zero_flag_parts"]["parts"]
    assert [(p["instance"], p["state"]) for p in parts] == \
        [("bottom-i1", "applied"), ("bottom-i1", "prep1")]
    assert doc["view_layer"]["bottom"]["abstain_rate"]["median"] is None
    assert doc["view_layer"]["bottom"]["abstain_rate_range"] == 0.5
    assert doc["view_layer"]["top"]["abstain_rate_range"] == 0.104545


def test_experiment_ledger_six_round_account_and_axis3_first(run_doc):
    """六行对照账完整性：r16/r17/r18/r19/r20/r22 六行并列（M 元组逐一
    相等）+r22/r20 均 G 守门破坏不入排序（资格门剔除；排序不变=r19_
    axis3 第一/r18 第二/r16 参照/r17 末位）+三族计数对照 r19（4/4/14）
    与 r20（2/6/10）+M4 双样本单列（0.104545 vs 0.211111 均过 ≤0.20、
    不进字母不合并）+复制性结论=regressed（r19 量级不可复制、轴3 收益
    降级单轮现象）+显著收益 0.381185≥0.10 描述层命中+in_calibrated_
    range 恒 False 收尾。"""
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    ecl = mo["experiment_comparison_ledger"]
    assert ecl["r22_measured"]["M1"] == 0.390244
    assert ecl["r22_measured"]["M2"] == 0.2
    assert ecl["r22_measured"]["M3"] == 4
    assert ecl["r22_measured"]["M4"] == 0.104545
    assert ecl["r22_measured"]["M1_arithmetic"] == "16/41"
    assert ecl["r22_measured"]["M2_arithmetic"] == "2/10"
    assert ecl["r22_measured"]["contact_family_abstain_flags_rubric"] == 2
    assert ecl["r22_measured"]["contact_family_by_view"] == \
        {"bottom": 0, "top": 2}
    assert ecl["r22_measured"]["existence_other_family"] == 12
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
    fc = ecl["family_counts_vs_r19_r20"]
    assert (fc["contact"]["r19_registered"], fc["contact"]["r20_registered"],
            fc["contact"]["r22_measured"]) == (4, 2, 2)
    assert (fc["existence_blackdot"]["r19_registered"],
            fc["existence_blackdot"]["r20_registered"],
            fc["existence_blackdot"]["r22_measured"]) == (4, 6, 4)
    assert (fc["existence_other"]["r19_registered"],
            fc["existence_other"]["r20_registered"],
            fc["existence_other"]["r22_measured"]) == (14, 10, 12)
    rk = ecl["ranking_by_comparison_rule"]
    # r22 不入排序（G2 破坏）；comparison_rule 排序不变（r19_axis3 第一）
    assert rk["r22_eligibility"] is False
    assert rk["r20_eligibility"] is False
    assert "G2" in rk["r22_eligibility_note"] or "几何门" in \
        rk["r22_eligibility_note"]
    assert rk["ranking_order_best_first"] == ["r19_axis3", "r18_axis2",
                                              "r16_baseline", "r17_axis1"]
    assert rk["eligible_rows"] == ["r16_baseline", "r17_axis1",
                                   "r18_axis2", "r19_axis3"]
    assert set(rk["rows_registered"]) == {"r16_baseline", "r17_axis1",
                                          "r18_axis2", "r19_axis3",
                                          "r20_combo_registered",
                                          "r22_repeat"}
    assert rk["rows_registered"]["r22_repeat"]["M1"] == 0.390244
    assert rk["rows_registered"]["r22_repeat"]["M4"] == 0.104545
    # M4 双样本单列（不进字母、不合并分布、不挑优）：两样本均 ≤0.20
    rc = ecl["replication_conclusion"]
    assert rc["verdict"] == "regressed"
    assert "不可复制" in rc["conclusion"] and "单轮现象" in rc["conclusion"]
    assert "0.211111" in rc["m4_second_sample_note"]
    assert "0.104545" in json.dumps(ecl, ensure_ascii=False)
    assert S77.cal._round6(0.211111 - 0.104545) == 0.106566
    sb = ecl["significant_benefit_vs_r16"]
    assert sb["met"] is True
    assert sb["r22_m1_absolute_drop"] == 0.381185
    assert round(0.771429 - 0.390244, 6) == 0.381185
    fd = ecl["direction_vs_r16"]
    assert fd["M1"].startswith("down") and fd["M2"].startswith("down")
    assert fd["M3"].startswith("down")
