"""R24 执行包测试（s86_calibration_r24_compare / calibration-run-r24）——
实例群扩容归因轮（多实例协议 v1.3：每视图实例数 3→6；本轮=第二十四轮；
执行 round23-dev-record 下一候选建议 (b)+用户 2026-09-10 拍板）：判读指引
=observation-guidance-r23.md 字节复用（866b0157 锚、零改写零派生、派发层
前缀覆盖 R23T/R23B→R24T/R24B=r16/r22 先例）、渲染零变更=renders-r14b 四
图字节复用、GT/阈值/协议正文零变更、changed_variables=1（实例数 n 单变量
=实例群抽样规模轴）。预注册假设（r23-confounded-residual-confound-
instance-axis-attribution）归因三支判据轮后裁决=not_instance_dominated
（唯一正式裁决）：(nid) 支命中 not_instance_dominated_m4_exceeds（G1=
六 bottom 实例 courtyard 非弃权全 0 维持；M4(n=6)=0.888889≥0.261904
[12 个（态,实例）格率极差、6 位定点 888889≥261904]、split_half_M1_diff=
0.018640≤0.09064[6 位定点 18640≤90640]）——离散超出抽样尺度、下一归因
轴=判据内容（判据内容/其他输出侧）。R24 五键 (M1,M2,M3,M4,split_half)=
(0.552381, 0.692308, 28, 0.888889, 0.018640)（M1=top 58/105、M2=bottom
18/26、M3=黑点族 rubric 口径 28、M4=12 格极差）；机制观察单列：逐实例双
峰结构（top-i1=1.0 vs top-i2/top-i6≈0.11–0.13；n=6 首次可看轮内分布形态）
+split-half 稳 vs 极差爆拉并存=聚合稳/个体散分解+rubric 三族 contact 4/
existence_blackdot 28/existence_other 44（r13–r16 132 条重放对拍逐一相等；
contact 链 8/15/5/10）对照 r19（4/4/14）/r22（2/4/12）/r23（8/8/7）三基
线+援引分记（旗级 §5B=0/(iii-a)=7/分支(=0；notes 级 §5B=0/24、(iii-a)=
8/24、§6=20/24）+八行对照账（r16 0.771429/0.857143/12/0.261904、r17
0.88/0.75/8/0.333333、r18 0.645161/0.684211/13/0.277778、r19 0.461538/
0.571429/4/0.211111、r20 0.636364/0.285714/6/0.25、r22 0.390244/0.2/4/
0.104545、r23 0.484848/0.571429/8/0.520833、r24 五键）——r20/r22/r23 资
格门剔除不入排序、r24 入排序居 r19 之后第二（G1/G2 满足、排序不变=r19_
axis3 第一）+G2 链 0→2→1→0 清零=观察项非字母支+GT 双口径 union=agreement
=1/13=0.076923（GT-REVC-P1-L1SHORT 四实例一致命中[top-i2 R24T-015/top-i4
R24T-019/top-i5 R24T-009/top-i6 R24T-015，全部 prep1]；agreement≥4/6=
v1.1「≥2/3 过半数」语义 n=6 推广首次计入）+24 派次无零旗格（24 格全部
≥1 旗、None 口径未触发）+in_calibrated_range 恒 False+development 域。

覆盖（14 测试，只读 out/、零子进程/零网络/零写盘）：
- 输入核验 fail-closed：24 件 reader-raw-r24 合法解析+实例旗数/弃权
  记账；缺文件→OSError、_fail→SystemExit、视角后缀缺失→ValueError；
  24 件盘态钉死前缀；FROZEN_SHA256 全锚实测一致；
- rubric 链重放对拍：r13–r16 132 条弃权旗重放（per_flag_total=132、
  blackdot 9/14/8/12、contact 8/15/5/10）+classify 优先级单元+r24 家族
  计数（4/28/44/0/0 与登记一致）；
- M 元组/定点键：_m_tuple_6dp+构造小样例 round_view_aggregate/_median6/
  M4 12 格极差+split_half 定点复算+r16 基线双侧 live 复算（27/35、
  12/14、courtyard 0/0/0）；
- 归因三支边界：adjudicate_attribution 纯函数构造用例——instance_
  dominated（双条件内）、not_instance_dominated（M4 超出=本轮实况/仅
  split 超出/双超出）、guard_interrupted（G1 破坏=支序最高）与端点
  （261903/261904、90640/90641）；
- 守卫与确定性：overwrite_guard 三态+_commit 落盘语义；run-r24 盘上件
  canonical byte 与重建一致+轮次身份+verdict=not_instance_dominated+
  落支 not_instance_dominated_m4_exceeds+五键+比较集四行 live 值+
  changed_variables=1；GT 双口径 union=agreement=1/13+joint not_met+
  in_calibrated_range 恒 False+八行对照账+排序（r20/r22/r23 资格门剔
  除、r24 入排序=r19 第一）+split-half 分解+逐实例分布。
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

ROUND_ID = "2026-09-10-r24"
ROUND_LABEL = "r24"
DECLARED_DATE = "2026-09-10"
INSTANCE_ORDER = tuple(
    [f"top-i{i}" for i in range(1, 7)]
    + [f"bottom-i{i}" for i in range(1, 7)])


def _load_s86():
    path = os.path.join(REPO, "scripts", "s86_calibration_r24_compare.py")
    spec = importlib.util.spec_from_file_location("s86_calibration_r24",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S86 = _load_s86()

# REPAIR-P4 W-1（G0）：config.py 授权变更（f515c348→acdfac49，登记=
# out/repair-p4/anchor-hashes-post-g0.json）。s8x 基座冻结不动；build_run 的
# prep-record 保护锚校验与 run-record protected 段按登记件 before 值历史
# 语境回放（重建=盘上冻结件 byte-exact；其余文件透传实测）。
_orig_sha_s86 = S86._sha


def _sha_g0_legacy_s86(rel, _orig=_orig_sha_s86):
    if str(rel).replace("\\", "/").endswith("pcbflow/config.py"):
        return ("f515c34842521a645145a9f5454a5919274a242e5c8c27c01fa"
                "f1a4c13e73baf")
    if str(rel).replace("\\", "/").endswith("pcbflow/cli.py"):
        # REPAIR-G1+ W-1/W-2（2026-09-24）：cli.py 授权变更 0a738047->
        # 3bfc9407（登记=out/repair-g1plus-r1/anchor-hashes-post-g1plus.
        # json）；冻结语境回放补 cli 腿（与 config 同构）
        return "0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e"
    return _orig(rel)


S86._sha = _sha_g0_legacy_s86


@pytest.fixture(scope="module")
def run_doc():
    """run-r24 文档内存构建（纯函数；只读输入、零写盘）。"""
    return S86.build_run()


@pytest.fixture(scope="module")
def instances():
    """十二实例主记录（逐实例两板合计口径；只读输入、零写盘）。"""
    parsed = {key: S86.parse_reader_raw(rel)
              for key, rel in S86.RAW_FILES.items()}
    deriv = S86._json_load(S86.REL_DERIV_R5)
    gt_applied = S86._gt_entries_with_r5_reprojection(S86.REL_GT_V2, deriv)
    gt_prep1 = S86._gt_entries_with_r5_reprojection(S86.REL_GT_V1, deriv)
    return {name: S86.build_instance_record(
        name, S86.INSTANCES[name], parsed, gt_applied, gt_prep1)
        for name in INSTANCE_ORDER}


# ---------------------------------------------------------------------------
# 输入核验（fail-closed）
# ---------------------------------------------------------------------------

def test_reader_raw_inputs_parse_and_flag_counts():
    """24 件 reader-raw-r24 全在盘、合法解析；实例旗数 24/17/16/22/11/15/
    4/4/4/6/4/4、弃权 24/2/5/19/6/2/0/0/4/6/4/4；拒收为零；R24T/R24B 前
    置=派发层覆盖（指引字节复用）；12/12 有旗实例跨板连续+24 格全部≥1 旗
    =零零旗格（与 prep-record naming 声明相符）。"""
    parsed = {k: S86.parse_reader_raw(rel)
              for k, rel in S86.RAW_FILES.items()}
    assert sorted(parsed) == sorted(S86.RAW_FILES)
    assert len(parsed) == 24
    for n in INSTANCE_ORDER:
        cnts = [len(parsed[p]["images"][0]["flags"])
                for p in S86.INSTANCES[n]["parts"]]
        assert sum(cnts) == {"top-i1": 24, "top-i2": 17, "top-i3": 16,
                             "top-i4": 22, "top-i5": 11, "top-i6": 15,
                             "bottom-i1": 4, "bottom-i2": 4, "bottom-i3": 4,
                             "bottom-i4": 6, "bottom-i5": 4,
                             "bottom-i6": 4}[n]
    for k, p in parsed.items():
        assert p["reader_id"].startswith("reader-r24-")
        assert p["direct_json_parse"] is True
        assert p["repair"] == "no_repair"
        for img in p["images"]:
            assert img["rejected"] == []
            for f in img["flags"]:
                assert f["flag_id"].startswith(("R24T-", "R24B-"))
    abst = {n: 0 for n in INSTANCE_ORDER}
    for n in INSTANCE_ORDER:
        for p in S86.INSTANCES[n]["parts"]:
            for img in parsed[p]["images"]:
                for f in img["flags"]:
                    assert f["abstain"] is not None
                    if f["abstain"]:
                        abst[n] += 1
    assert abst == {"top-i1": 24, "top-i2": 2, "top-i3": 5, "top-i4": 19,
                    "top-i5": 6, "top-i6": 2, "bottom-i1": 0, "bottom-i2": 0,
                    "bottom-i3": 4, "bottom-i4": 6, "bottom-i5": 4,
                    "bottom-i6": 4}


def test_parse_reader_raw_fail_closed_and_view_mapping():
    """fail-closed 语义：缺文件→OSError（不返回解析结果）；_fail→
    SystemExit；view_for_image 确定性映射（*-top.png→top、*-bottom.png→
    bottom、无后缀→ValueError）。"""
    with pytest.raises(OSError):
        S86.parse_reader_raw(
            "out/v3-tl2/calibration/reader-raw-r24-NO-SUCH-FILE.txt")
    with pytest.raises(SystemExit):
        S86._fail("输入缺失（fail-closed）: <构造缺件>")
    assert S86.view_for_image("board-applied-top.png") == "top"
    assert S86.view_for_image("board-prep1-bottom.png") == "bottom"
    with pytest.raises(ValueError):
        S86.view_for_image("board-side.png")


def test_pinned_raw_prefixes_and_frozen_anchor_hashes():
    """24 件盲读原始件盘态钉死前缀逐字命中+输入先验锚全集合（协议/GT/
    指引 r8–r20+本轮 r24/prep/axis-plan/dev-r22/dev-r23/run-r22/run-r23/
    24 reader 件/PNG/PDF）与盘上实测逐一相等（哈希不符即拒算前提）；本轮
    指引锚=guidance-r23 866b0157（字节复用零改写）、prep-r24=760af49f、
    run-r16（M1 基线复算输入）在锚集；run-r24=本包唯一新建输出、不在
    FROZEN 锚集。"""
    assert len(S86.RAW_PINNED_PREFIXES) == 24
    for key, prefix in S86.RAW_PINNED_PREFIXES.items():
        got = S86._sha(S86.RAW_FILES[key])
        assert got.startswith(prefix), (key, got[:8], prefix)
    assert S86.FROZEN_SHA256[S86.REL_GUIDANCE_R23].startswith("866b0157")
    assert S86.FROZEN_SHA256[S86.REL_PREP_R24].startswith("760af49f")
    assert S86.FROZEN_SHA256[S86.REL_DEV_R23].startswith("343a6747")
    assert S86.FROZEN_SHA256[S86.REL_RUN_R23P].startswith("15f58350")
    assert S86.FROZEN_SHA256[S86.REL_RUN_R16].startswith(
        hashing.sha256_file(os.path.join(REPO, S86.REL_RUN_R16))[:8])
    assert len(S86.FROZEN_SHA256) > 60
    for rel, want in S86.FROZEN_SHA256.items():
        assert S86._sha(rel) == want, rel
    assert S86.REL_RUN_R24 not in S86.FROZEN_SHA256


# ---------------------------------------------------------------------------
# rubric 链重放对拍+优先级单元+r24 家族计数
# ---------------------------------------------------------------------------

def test_rubric_replay_r13_r16_chain_matches_frozen_counts():
    """r13–r16 132 条弃权旗 rubric 机械重放对拍：逐旗 family 与分型件
    在案记录逐一相等；contact 链 8/15/5/10、blackdot 链 9/14/8/12 与已
    冻结件（分型件 matrix+prep-record 锚）一致——链式回放先核对一致才可
    应用 r24 分型。"""
    typology_doc = S86.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    proof = S86.replay_typology_families(typology_doc, kt)
    assert proof["per_flag_total"] == 132
    assert proof["contact_counts"] == {"r13": 8, "r14": 15,
                                       "r15": 5, "r16": 10}
    assert proof["blackdot_counts"] == {"r13": 9, "r14": 14,
                                        "r15": 8, "r16": 12}
    assert typology_doc["matrix"]["round_totals"]["r16"]["families"][
        "contact"] == 10


def test_rubric_classify_and_r24_family_counts(run_doc, instances):
    """classify 优先级单元+r24 全部 131 条旗逐旗 rubric 分类：
    contact=4（全视；top 2+bottom 2；r16 基线 10）、existence_blackdot=28
    （远高于 r19/r22/r23 三基线=n 扩容+实例异质性）、existence_other=44、
    semantic_confusion=0、other=0——与登记表/run 机制观察口径逐一相等；
    黑点弃权旗 28 条全弃权（逐实例分旗）、黑点转非弃权旗 16 条；exit_type
    主出口分型=接触 26+存在 30+其他 2（两套口径分列）。"""
    typology_doc = S86.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    # 优先级单元（blackdot 先于 contact；泛化兜底→existence_other）
    fam, _ = S86.rubric_classify(
        "一枚黑色钻孔圆点紧贴焊盘，无法分辨真实接触与视觉贴近", kt)
    assert fam == "existence_blackdot"
    fam, _ = S86.rubric_classify(
        "两 courtyard 轮廓看似相接，无法区分真实接触与视觉贴近", kt)
    assert fam == "contact"
    fam, _ = S86.rubric_classify("该形态无法负责任确认", kt)
    assert fam == "existence_other"
    # r24 全旗套用
    rows = S86.build_rubric_rows_r24(instances, kt)
    fam_counts = {fam: sum(1 for r in rows
                           if r["abstain"] and r["family"] == fam)
                  for fam in ("contact", "existence_blackdot",
                              "existence_other", "semantic_confusion",
                              "other")}
    assert fam_counts == S86.R24_FAMILY_COUNTS_REGISTERED
    assert fam_counts == {"contact": 4, "existence_blackdot": 28,
                          "existence_other": 44, "semantic_confusion": 0,
                          "other": 0}
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    assert mo["black_dot_tracking"]["rubric_families"]["counts"] == \
        fam_counts
    assert len(rows) == 131  # 131 旗逐旗入账（弃权 76+非弃权 55）
    assert sum(1 for r in rows if r["abstain"]) == 76
    exit_counts = {"contact": 0, "existence": 0, "other_layer": 0}
    for r in rows:
        if r["abstain"] and r["instance"].startswith("top"):
            exit_counts[r["exit_type"]] += 1
    assert exit_counts == S86.R24_TOP_EXIT_TYPOLOGY_REGISTERED


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
    M3 整数直接）；round_view_aggregate 六实例两板合计（58/105、18/26）；
    M4(n=6)=12 格率先 6 位定点取率再取极差 1.0−0.111111=0.888889；
    split_half=|0.543860−0.562500|=0.018640（6 位定点 18640）；median6
    恰 6 值取第 3/4 序位均值。"""
    assert S86._m_tuple_6dp(0.552381, 0.692308, 28, 0.888889) == \
        (552381, 692308, 28, 888889)
    assert S86._m_tuple_6dp(0.461538, 0.571429, 4, 0.211111) == \
        (461538, 571429, 4, 211111)
    inst = {
        "top-i1": _synthetic_instance("top-i1", "top", 24, 24, 1.0),
        "top-i2": _synthetic_instance("top-i2", "top", 17, 2, 0.117647),
        "top-i3": _synthetic_instance("top-i3", "top", 16, 5, 0.3125),
        "top-i4": _synthetic_instance("top-i4", "top", 22, 19, 0.863636),
        "top-i5": _synthetic_instance("top-i5", "top", 11, 6, 0.545455),
        "top-i6": _synthetic_instance("top-i6", "top", 15, 2, 0.133333),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 4, 0, 0.0),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 0, 0.0),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 4, 4, 1.0),
        "bottom-i4": _synthetic_instance("bottom-i4", "bottom", 6, 6, 1.0),
        "bottom-i5": _synthetic_instance("bottom-i5", "bottom", 4, 4, 1.0),
        "bottom-i6": _synthetic_instance("bottom-i6", "bottom", 4, 4, 1.0),
    }
    ab, fl = S86.round_view_aggregate(
        inst, tuple(f"top-i{i}" for i in range(1, 7)))
    assert (ab, fl) == (58, 105)
    assert S86.cal._ratio(ab, fl) == 0.552381
    ab_b, fl_b = S86.round_view_aggregate(
        inst, tuple(f"bottom-i{i}" for i in range(1, 7)))
    assert (ab_b, fl_b) == (18, 26)
    assert S86.cal._ratio(ab_b, fl_b) == 0.692308
    # M4(n=6)：12 格率定点化后取极差
    cells = [(24, 24), (8, 1), (7, 2), (9, 8), (5, 3), (6, 1),
             (13, 13), (9, 1), (9, 3), (13, 11), (6, 3), (9, 1)]
    vals = [int(round(S86.cal._ratio(a, n) * 1000000)) for n, a in cells]
    assert max(vals) - min(vals) == 888889
    # split-half（6 位定点整数交叉相乘口径）
    a6 = round(31 * 1000000 / 57)
    b6 = round(27 * 1000000 / 48)
    assert (a6, b6, abs(a6 - b6)) == (543860, 562500, 18640)
    assert S86.cal._round6(18640 / 1000000) == 0.01864
    # median6=第 3/4 序位均值
    assert S86._median6([24, 17, 16, 22, 11, 15]) == 16.5
    assert S86._median6([4, 4, 4, 6, 4, 4]) == 4.0
    assert S86._median6([1.0, 0.117647, 0.3125, 0.863636, 0.545455,
                         0.133333]) == 0.4289775


def test_view_layer_and_r16_baseline_live_replay():
    """r16 基线=同一聚合逻辑对 run-r16 内嵌输入双侧复算（不手工抄数）：
    top 27/35=0.771429、bottom 12/14=0.857143、G1 基线 courtyard 非弃权
    0/0/0；视角层构造小样例（r24 六实例弃权率全部有定义、top 中位数=
    0.4289775、bottom 中位数=1.0）。"""
    run16 = S86._json_load(S86.REL_RUN_R16)
    assert S86.r16_top_abstain_aggregate_live(run16) == (27, 35)
    assert S86.r16_bottom_abstain_aggregate_live(run16) == (12, 14)
    assert S86.r16_baseline_courtyard_live(run16) == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    layer = S86.build_view_layer({
        "top-i1": _synthetic_instance("top-i1", "top", 24, 24, 1.0),
        "top-i2": _synthetic_instance("top-i2", "top", 17, 2, 0.117647),
        "top-i3": _synthetic_instance("top-i3", "top", 16, 5, 0.3125),
        "top-i4": _synthetic_instance("top-i4", "top", 22, 19, 0.863636),
        "top-i5": _synthetic_instance("top-i5", "top", 11, 6, 0.545455),
        "top-i6": _synthetic_instance("top-i6", "top", 15, 2, 0.133333),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 4, 0, 0.0),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 0, 0.0),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 4, 4, 1.0),
        "bottom-i4": _synthetic_instance("bottom-i4", "bottom", 6, 6, 1.0),
        "bottom-i5": _synthetic_instance("bottom-i5", "bottom", 4, 4, 1.0),
        "bottom-i6": _synthetic_instance("bottom-i6", "bottom", 4, 4, 1.0),
    })
    assert layer["top"]["abstain_rate"]["median"] == 0.4289775
    assert layer["top"]["abstain_rate_range"] == 0.882353
    assert layer["bottom"]["abstain_rate"]["median"] == 1.0
    assert layer["bottom"]["abstain_rate_range"] == 1.0
    assert layer["top"]["flag_count"]["median"] == 16.5


# ---------------------------------------------------------------------------
# 归因三支边界（adjudicate_attribution 构造用例）
# ---------------------------------------------------------------------------

def test_adjudicate_instance_dominated_branch_and_thresholds():
    """(id) 支：G1 维持+M4<261904+split_half≤90640（双条件同时成立）→
    instance_dominated；端点（恰 261903/90640 双内→instance_dominated）；
    阈值常量与判据原文同锚；M4 自证=928571−666667=261904 整数复算。"""
    assert S86.adjudicate_attribution(200_000, 18_640, True) == \
        ("instance_dominated", "instance_dominated_both_within")
    assert S86.adjudicate_attribution(261_903, 90_640, True) == \
        ("instance_dominated", "instance_dominated_both_within")
    assert S86.adjudicate_attribution(0, 0, True) == \
        ("instance_dominated", "instance_dominated_both_within")
    # 阈值常量与 s87/判据原文同锚
    assert S86.M4_THRESHOLD_6DP == 261_904
    assert S86.SPLIT_HALF_THRESHOLD_6DP == 90_640
    # M4 自证（prep-record fixed_point_comparison_note 原文）
    assert 928571 - 666667 == 261904
    assert S86.SPLIT_HALF_THRESHOLD_6DP == abs(862069 - 771429)


def test_adjudicate_not_instance_dominated_and_guard_branches():
    """(nid)/(gi) 支+支序：G1 维持且 M4≥261904→not_instance_dominated
    （本轮实况：M4=888889、split=18640=仅 M4 超出）；反事实构造：仅
    split 超出→split_half_exceeds、双超出→both_exceed、双内→instance_
    dominated（分岔两侧）；G1 破坏→guard_interrupted（支序最高，即使
    双条件均内）；M4 恰=261904=超出端点、split 恰 90641=超出端点。"""
    # 本轮实际落支：M4=888889 超出、split=18640 内、G1 维持
    assert S86.adjudicate_attribution(888_889, 18_640, True) == \
        ("not_instance_dominated", "not_instance_dominated_m4_exceeds")
    # 反事实构造：仅 split 超出（M4 内）
    assert S86.adjudicate_attribution(200_000, 90_641, True) == \
        ("not_instance_dominated",
         "not_instance_dominated_split_half_exceeds")
    # 反事实构造：双超出
    assert S86.adjudicate_attribution(888_889, 90_641, True) == \
        ("not_instance_dominated", "not_instance_dominated_both_exceed")
    # 反事实构造：双内=instance_dominated（分岔另一侧）
    assert S86.adjudicate_attribution(261_903, 18_640, True) == \
        ("instance_dominated", "instance_dominated_both_within")
    # 端点：M4 恰=261904=超出；split 恰 90640=内
    assert S86.adjudicate_attribution(261_904, 90_640, True) == \
        ("not_instance_dominated", "not_instance_dominated_m4_exceeds")
    # G1 破坏→guard_interrupted（支序最高：三支字母口径均不命中、不新增
    # 字母支；即使双条件均内）
    assert S86.adjudicate_attribution(200_000, 18_640, False) == \
        ("guard_interrupted", "guard_interrupted_g1")
    assert S86.adjudicate_attribution(888_889, 18_640, False) == \
        ("guard_interrupted", "guard_interrupted_g1")


# ---------------------------------------------------------------------------
# G1/G2 守门与援引分记（机制观察）
# ---------------------------------------------------------------------------

def test_guards_g1_g2_and_citation_observation(run_doc, instances):
    """G1 实测（n=6 操作化定义）：bottom courtyard 非弃权六实例全 0=G1
    维持（r16 基线 live 重放对照、r20 破坏 2/0/0 在案）；G2 清零（几何门
    R19=0→R22=2→R23=1→R24=0）；guard_channel g1_ok=True、g2=True、
    guards_ok=True；判据布尔（not_instance_dominated 命中/其余两支不命
    中）；援引分记（旗级 §5B=0/(iii-a)=7/分支(=0；notes 级 §5B=0/24、
    (iii-a)=8/24、§6=20/24；(iii-a) 7 旗逐旗摘录在案）。"""
    assert S86.bottom_courtyard_non_abstain(instances) == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0, "bottom-i4": 0,
         "bottom-i5": 0, "bottom-i6": 0}
    m = run_doc["hypothesis_test"]["measurement"]
    gc = m["guard_channel"]
    assert gc["g1_ok"] is True
    assert gc["g2_guard_ok"] is True
    assert gc["guards_ok"] is True
    assert gc["g2_geometry_gate_r19"] == 0
    assert gc["g2_geometry_gate_r22"] == 2
    assert gc["g2_geometry_gate_r23"] == 1
    assert gc["g2_geometry_gate_r24"] == 0
    g12 = run_doc["hypothesis_test"]["mechanism_observation"]["guards_g1_g2"]
    assert g12["counts"]["guards_ok"] is True
    assert g12["counts"]["g1_ok"] is True
    assert g12["counts"]["g2_guard_ok_axis_plan_semantics"] is True
    assert g12["counts"]["g1_bottom_courtyard_non_abstain_r24"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0, "bottom-i4": 0,
         "bottom-i5": 0, "bottom-i6": 0}
    assert g12["counts"]["g1_r16_baseline_live"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g1_r20_broken_registered"] == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
    # 判据布尔（not_instance_dominated 支命中、其余两支不命中）
    assert m["crit_not_instance_dominated"] is True
    assert m["crit_guard_interrupted"] is False
    assert m["crit_instance_dominated"] is False
    # 双判据定点锚（与盘上登记逐一相等）
    assert m["m4_threshold_6dp"] == 261904
    assert m["split_half_threshold_6dp"] == 90640
    assert m["r24_m_tuple_6dp"]["M4"] == 0.888889
    assert m["r24_m_tuple_6dp"]["split_half_M1_diff"] == 0.01864
    # 援引分记（三条款分开记、互不合并；机制观察单列）
    cc = run_doc["hypothesis_test"]["mechanism_observation"][
        "criterion_citation_observation"]
    counts = cc["citation_counts"]
    assert counts["flag_level_s5b_literal"] == 0
    assert counts["flag_level_iiia_literal"] == 7
    assert counts["flag_level_branch_literal"] == 0
    assert counts["flag_level_s5b_sources"] == \
        S86.S5B_FLAG_CITE_REGISTERED == []
    assert counts["flag_level_iiia_sources"] == \
        S86.IIIA_FLAG_CITE_REGISTERED
    assert len(cc["iiia_flag_rows"]) == 7
    assert all("(iii-a)" in r["location_evidence_excerpt"]
               for r in cc["iiia_flag_rows"])
    assert counts["notes_level_s5b"] == 0
    assert counts["notes_level_s5b_sources"] == S86.S5B_NOTES_CITE_REGISTERED
    assert counts["notes_level_iiia"] == 8
    assert counts["notes_level_iiia_sources"] == \
        S86.IIIA_NOTES_CITE_REGISTERED
    assert counts["notes_level_s6_clause"] == 20
    assert counts["notes_level_s6_clause_sources"] == \
        S86.S6_NOTES_CITE_REGISTERED
    # r19/r22/r23 基线对照（在案登记）
    assert "10/12" in counts["baseline_r19_iiia"]
    assert "旗级全 0" in counts["baseline_r22_iiia"]
    assert "4/12" in counts["baseline_r23_iiia"]


# ---------------------------------------------------------------------------
# 守卫、run 记录身份与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；既有且
    不同→fail；_commit=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写；run-r24 盘上件不可覆写）。"""
    assert S86.overwrite_guard(None, b"abc") == "write"
    assert S86.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S86.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S86._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S86._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S86._commit(p, b"abc", "probe")


def test_run_record_canonical_identity_and_letter_verdict(run_doc):
    """run-r24 盘上件：同参重建两次 byte-exact+盘上件=canonical 重建+
    轮次身份（r24/2026-09-10/development 域）+verdict=not_instance_
    dominated（唯一正式裁决）+落支 not_instance_dominated_m4_exceeds（M4
    条件超出）+五键与比较集四行+实例群扩容归因轮轮次性质（指引字节复用/
    渲染零变更/changed_variables=1/axis=instance_sampling_scale）+判据原
    文摘录与 prep-record 逐字一致。"""
    b1 = hashing.canonical_json_bytes(S86.build_run())
    b2 = hashing.canonical_json_bytes(S86.build_run())
    assert b1 == b2  # 同参重建 byte-exact
    path = os.path.join(CAL_DIR, "calibration-run-r24.json")
    raw = open(path, "rb").read()
    assert raw == b1  # 盘上件=canonical 重建（byte-exact 可重跑）
    assert hashing.sha256_file(path).startswith("8a9bdb7d")
    doc = json.loads(raw.decode("utf-8"))
    assert doc["kind"] == "tl2_calibration_run_r24"
    assert doc["round_id"] == ROUND_ID
    assert doc["round_label"] == ROUND_LABEL
    assert doc["declared_date"] == DECLARED_DATE
    assert doc["evaluation_domain"] == "development"
    assert doc["evaluation_domain_note"]["in_calibrated_range"] is False
    assert doc["instrument_change"]["changed"] is False
    assert doc["instrument_change"]["axis_id"].startswith(
        "instance_sampling_scale")
    hyp = doc["hypothesis_test"]
    m = hyp["measurement"]
    assert hyp["hypothesis_id"] == \
        "r23-confounded-residual-confound-instance-axis-attribution"
    assert hyp["verdict"] == "not_instance_dominated"
    assert m["verdict"] == "not_instance_dominated"
    assert "(nid)" in m["letter_branch"]
    assert "0.261904" in m["letter_branch"]
    assert "下一归因轴=判据内容" in m["letter_branch"]
    assert m["r24_m_tuple_6dp"] == {"M1": 0.552381, "M2": 0.692308,
                                    "M3": 28, "M4": 0.888889,
                                    "split_half_M1_diff": 0.01864}
    assert m["comparison_rows_live"]["r16_baseline"] == \
        {"M1": 0.771429, "M2": 0.857143, "M3": 12, "M4": 0.261904}
    assert m["comparison_rows_live"]["r19_axis3"] == \
        {"M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111}
    assert m["comparison_rows_live"]["r22_repeat_live"] == \
        {"M1": 0.390244, "M2": 0.2, "M3": 4, "M4": 0.104545}
    assert m["comparison_rows_live"]["r23_repeat_live"] == \
        {"M1": 0.484848, "M2": 0.571429, "M3": 8, "M4": 0.520833}
    assert m["top_abstain_count_r24"] == 58
    assert m["top_abstain_flags_r24"] == 105
    assert "58/105" in m["top_abstain_rate_r24_arithmetic"]
    assert m["contact_family_abstain_flags_rubric_r24"] == 4
    assert m["split_half_M1_diff_r24"] == 0.01864
    # 预注册判据摘录=prep-record adjudication 原文（逐字一致；10 键）
    prep = S86._json_load(S86.REL_PREP_R24)
    adj = prep["hypothesis_test"]["adjudication"]
    q = hyp["preregistered_criteria_quote"]
    for k in ("instance_dominated", "not_instance_dominated",
              "guard_interrupted", "letter_branch_map",
              "fixed_point_comparison_note", "g2_observation_separate",
              "descriptive_boundary_note", "mechanism_observation_separate",
              "metric_lesson_separate", "three_way_bookkeeping"):
        assert q[k] == adj[k], k
    assert prep["hypothesis_test"]["hypothesis_id"] == hyp["hypothesis_id"]
    # changed_variables=1（实例数 n 扩容单变量；指引=字节复用、基座即派生；
    # 渲染/GT/阈值/协议正文零变更）
    assert len(prep["changed_variables"]) == 1
    assert prep["no_instrument_change"] is True
    assert prep["guidance_reuse"]["mode"] == "byte_reuse_dispatch_override"
    assert prep["guidance_reuse"]["base_sha256"].startswith("866b0157")
    assert prep["guidance_reuse"]["derived_sha256"].startswith("866b0157")
    assert prep["guidance_reuse"]["byte_size"] == {
        "base": 23125, "delta": 0, "derived": 23125}


def test_gt_dual_union_joint_gate_in_range_false(run_doc):
    """GT 双口径 union=agreement=1/13=0.076923（GT-REVC-P1-L1SHORT 四实
    例一致命中：top-i2 R24T-015+top-i4 R24T-019+top-i5 R24T-009+top-i6
    R24T-015，全部 prep1；agreement≥4/6=v1.1 ≥2/3 语义 n=6 推广首次计
    入）；代表配置（top-i3+bottom-i3；top 第 3 序位唯一、bottom tie 按
    实例编号先序）聚合 20/9/0.45、joint not_met、连续=0；in_calibrated_
    range 恒 False（run 与 compliance 双处）；本轮无零旗格（None 口径未
    触发）。"""
    doc = run_doc
    dual = doc["gt_match_dual"]
    assert (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) == (1, 1, 13)
    assert dual["union"]["gt_ids"] == ["GT-REVC-P1-L1SHORT"]
    assert dual["agreement"]["gt_ids"] == ["GT-REVC-P1-L1SHORT"]
    assert dual["union"]["gt_recall_union"] == 0.076923
    assert dual["agreement"]["gt_recall_agreement"] == 0.076923
    hits = [pg for pg in dual["per_gt"] if pg.get("hits")]
    assert len(hits) == 1
    assert hits[0]["matched_by_count"] == 4
    got = {(h["flag_id"], h["instance"], h["state"])
           for h in hits[0]["hits"]}
    assert got == {("R24T-015", "top-i2", "prep1"),
                   ("R24T-019", "top-i4", "prep1"),
                   ("R24T-009", "top-i5", "prep1"),
                   ("R24T-015", "top-i6", "prep1")}
    comp = doc["compliance_representative"]
    agg = doc["aggregation_representative"]
    assert (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) == (20, 9, 0.45, 0.0, 0.0)
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
        {"top": "top-i3", "bottom": "bottom-i3"}
    assert doc["representative_configuration"]["selection"]["top"][
        "tie"] is False
    assert doc["representative_configuration"]["selection"]["bottom"][
        "tie"] is True  # bottom-i1/i2/i3/i5/i6 同为 4→按实例编号先序
    assert doc["reader"]["zero_flag_parts"]["parts"] == []
    assert doc["view_layer"]["bottom"]["abstain_rate"]["median"] == 1.0
    assert doc["view_layer"]["bottom"]["abstain_rate_range"] == 1.0
    assert doc["view_layer"]["top"]["abstain_rate_range"] == 0.882353


def test_experiment_ledger_eight_round_account_and_ranking(run_doc):
    """八行对照账完整性：r16/r17/r18/r19/r20/r22/r23/r24 八行并列（M 元
    组逐一相等）+r24 入排序居 r19 之后第二（G1/G2 满足；排序=r19_axis3
    第一/r18/r16 参照/r17 末位）+r20/r22/r23 资格门剔除+三族计数对照三
    基线+split-half 分解+逐实例分布观察+归因结论位=not_instance_"
    "dominated/0.261904/判据内容+显著收益 0.219048≥0.10 描述层命中+
    in_calibrated_range 恒 False 收尾。"""
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    ecl = mo["experiment_comparison_ledger"]
    assert ecl["r24_measured"]["M1"] == 0.552381
    assert ecl["r24_measured"]["M2"] == 0.692308
    assert ecl["r24_measured"]["M3"] == 28
    assert ecl["r24_measured"]["M4"] == 0.888889
    assert ecl["r24_measured"]["split_half_M1_diff"] == 0.01864
    assert ecl["r24_measured"]["M1_arithmetic"] == "58/105"
    assert ecl["r24_measured"]["M2_arithmetic"] == "18/26"
    assert ecl["r24_measured"]["contact_family_abstain_flags_rubric"] == 4
    assert ecl["r24_measured"]["existence_other_family"] == 44
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
    assert ecl["r23_repeat_registered_row"] == {"M1": 0.484848,
                                                "M2": 0.571429, "M3": 8,
                                                "M4": 0.520833}
    fc = ecl["family_counts_vs_r19_r22_r23"]
    assert (fc["contact"]["r19_registered"], fc["contact"]["r22_registered"],
            fc["contact"]["r23_registered"],
            fc["contact"]["r24_measured"]) == (4, 2, 8, 4)
    assert (fc["existence_blackdot"]["r19_registered"],
            fc["existence_blackdot"]["r22_registered"],
            fc["existence_blackdot"]["r23_registered"],
            fc["existence_blackdot"]["r24_measured"]) == (4, 4, 8, 28)
    assert (fc["existence_other"]["r19_registered"],
            fc["existence_other"]["r22_registered"],
            fc["existence_other"]["r23_registered"],
            fc["existence_other"]["r24_measured"]) == (14, 12, 7, 44)
    rk = ecl["ranking_by_comparison_rule"]
    # r24 入排序（G1/G2 满足）；排序=r19 第一、r24 第二
    assert rk["r24_eligibility"] is True
    assert rk["r22_eligibility"] is False
    assert rk["r20_eligibility"] is False
    assert rk["r23_eligibility"] is False
    assert rk["ranking_order_best_first"] == ["r19_axis3", "r24_expansion",
                                              "r18_axis2", "r16_baseline",
                                              "r17_axis1"]
    assert rk["eligible_rows"] == ["r16_baseline", "r17_axis1",
                                   "r18_axis2", "r19_axis3", "r24_expansion"]
    assert set(rk["rows_registered"]) == {"r16_baseline", "r17_axis1",
                                          "r18_axis2", "r19_axis3",
                                          "r20_combo_registered",
                                          "r22_repeat_registered",
                                          "r23_repeat_registered",
                                          "r24_expansion"}
    assert rk["rows_registered"]["r24_expansion"]["M1"] == 0.552381
    assert rk["rows_registered"]["r24_expansion"]["M4"] == 0.888889
    # split-half 分解与逐实例分布单列
    sh = mo["split_half_decomposition"]
    assert (sh["half_A"]["rate_6dp"], sh["half_B"]["rate_6dp"],
            sh["split_half_6dp"]) == (543860, 562500, 18640)
    assert sh["threshold_6dp"] == 90640
    assert "聚合稳" in sh["observation"]
    ido = mo["instance_distribution_observation"]
    assert ido["top_rates_by_instance"]["top-i1"] == 1.0
    assert ido["top_rates_by_instance"]["top-i2"] == 0.117647
    assert ido["m4_12_cell_range"] == 0.888889
    assert "双峰" in ido["observation"]
    att = ecl["attribution_conclusion"]["conclusion"]
    assert "not_instance_dominated" in att
    assert "0.261904" in att
    assert "判据内容" in att
    assert "confounded" in att  # r23 字母维持不改写
    assert S86.cal._round6(0.888889 - 0.261904) == 0.626985
    sb = ecl["significant_benefit_vs_r16"]
    assert sb["met"] is True
    assert sb["r24_m1_absolute_drop"] == 0.219048
    assert round(0.771429 - 0.552381, 6) == 0.219048
    fd = ecl["direction_vs_r16"]
    assert fd["M1"].startswith("down") and fd["M2"].startswith("down")
    assert fd["M3"].startswith("up")
    # G2 出局条目本轮=0（空摘录）+r23 对照=1 条装载
    grej = mo["g2_rejected_entries_r24"]
    assert grej["count"] == 0 and grej["entries"] == []
    assert [e["flag_id"] for e in grej["comparison_to_r23"]["r23_entries"]] \
        == ["R23T-004"]
