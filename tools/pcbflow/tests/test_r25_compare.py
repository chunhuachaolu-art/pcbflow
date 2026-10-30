"""R25 执行包测试（s89_calibration_r25_compare / calibration-run-r25）——
判据内容轴归因轮（三混杂轴归因链第三轴执行轮：r23 框宽排除→r24 实例群
排除→r25 判据内容；本轮=第二十五轮；执行 round24-dev-record 下一候选
建议选项(b)+用户 2026-09-10 拍板选项(b)定向判据内容轴）：判读指引
=observation-guidance-r25.md（86af24dd=observation-guidance-r23.md
866b0157 机械变换派生落盘新件、byte delta=+937、唯一语义变量=§4 末尾
弃权边界操作化条款[s70/s80 先例同型]）、渲染零变更=renders-r14b 四图
字节复用、GT/阈值/协议正文零变更、changed_variables=1（判据内容单变量；
n=6 口径与 r24 完全同构、实例群重抽=轮际固有混杂）。预注册假设
（r24-not-instance-dominated-criterion-boundary-operationalization-
attribution）归因三支判据轮后裁决=not_criterion_dominated（唯一正式
裁决）：(ncd) 支命中 not_criterion_dominated_m4_exceeds（G1=六 bottom
实例 courtyard 非弃权全 0 维持；M4(n=6)=1.0≥0.261904[12 个（态,实例）
格率极差、6 位定点 1000000≥261904]；split_half_M1_diff=0.260377>
0.09064=聚合亦移动[与 r24 反转、机制观察单列不进分支]）——边界操作化
未收敛个体散=判据内容非主因（残余归因=其他输出侧/模型侧固有）。R25
五键 (M1,M2,M3,M4,split_half)=(0.433735, 0.916667, 22, 1.0, 0.260377)
（M1=top 36/83、M2=bottom 22/24、M3=黑点族 rubric 口径 22、M4=12 格
极差 1.0−0.0）；机制观察单列：逐实例个体散（top-i5=1.0 vs top-i6=
0.142857）+split-half 聚合移动+rubric 三族 contact 3/existence_blackdot
22/existence_other 20+other 13（r13–r16 132 条重放对拍逐一相等；contact
链 8/15/5/10）对照 r19（4/4/14）/r22（2/4/12）/r23（8/8/7）/r24
（4/28/44）四基线+援引分记（旗级 §5B=0/(iii-a)=11/分支(=0/条款=16+
三问=13；notes 级 §5B=0/24、(iii-a)=12/24、§6=9/24、弃权边界条款=
24/24[三问 22/24]）+条款行为观察（弃权理由候选解释列举率 58/58）+
M1 降/M2 升分解单列+九行对照账（r16 0.771429/0.857143/12/0.261904、
r17 0.88/0.75/8/0.333333、r18 0.645161/0.684211/13/0.277778、r19
0.461538/0.571429/4/0.211111、r20 0.636364/0.285714/6/0.25、r22
0.390244/0.2/4/0.104545、r23 0.484848/0.571429/8/0.520833、r24
0.552381/0.692308/28/0.888889、r25 五键）——r20/r22/r23 资格门剔除
不入排序、r25 入排序居首（G1/G2 满足；r24 在案入排序）+G2 链
0→2→1→0→0 清零维持=观察项非字母支+GT 双口径 union=1/13=0.076923
（GT-REVC-AP-1-R5U6 单实例命中）、agreement=0/13+零旗格=2 格
（bottom-i1 两板合法零旗输出、None 口径触发）+in_calibrated_range 恒
False+development 域。

覆盖（14 测试，只读 out/、零子进程/零网络/零写盘）：
- 输入核验 fail-closed：24 件 reader-raw-r25 合法解析+实例旗数/弃权
  记账；缺文件→OSError、_fail→SystemExit、视角后缀缺失→ValueError；
  24 件盘态钉死前缀；FROZEN_SHA256 全锚实测一致；
- rubric 链重放对拍：r13–r16 132 条弃权旗重放（per_flag_total=132、
  blackdot 9/14/8/12、contact 8/15/5/10）+classify 优先级单元+r25 家族
  计数（3/22/20/0/13 与登记一致）；
- M 元组/定点键：_m_tuple_6dp+构造小样例 round_view_aggregate/_median6/
  M4 12 格极差+split_half 定点复算+r16 基线双侧 live 复算（27/35、
  12/14、courtyard 0/0/0）；
- 归因三支边界：adjudicate_attribution 纯函数构造用例——criterion_
  dominated（M4 内）、not_criterion_dominated（M4 超出=本轮实况）、
  guard_interrupted（G1 破坏=支序最高）与端点（261903/261904）；
- 守卫与确定性：overwrite_guard 三态+_commit 落盘语义；run-r25 盘上件
  canonical byte 与重建一致+轮次身份+verdict=not_criterion_dominated+
  落支 not_criterion_dominated_m4_exceeds+五键+比较集五行 live 值+
  changed_variables=1；GT 双口径 union=1/agreement=0+joint not_met+
  in_calibrated_range 恒 False+九行对照账+排序（r20/r22/r23 资格门剔
  除、r25 入排序居首）+split-half 分解+逐实例分布。
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

ROUND_ID = "2026-09-10-r25"
ROUND_LABEL = "r25"
DECLARED_DATE = "2026-09-10"
INSTANCE_ORDER = tuple(
    [f"top-i{i}" for i in range(1, 7)]
    + [f"bottom-i{i}" for i in range(1, 7)])


def _load_s89():
    path = os.path.join(REPO, "scripts", "s89_calibration_r25_compare.py")
    spec = importlib.util.spec_from_file_location("s89_calibration_r25",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S89 = _load_s89()

# REPAIR-P4 W-1（G0）：config.py 授权变更（f515c348→acdfac49，登记=
# out/repair-p4/anchor-hashes-post-g0.json）。s8x 基座冻结不动；build_run 的
# prep-record 保护锚校验与 run-record protected 段按登记件 before 值历史
# 语境回放（重建=盘上冻结件 byte-exact；其余文件透传实测）。
_orig_sha_s89 = S89._sha


def _sha_g0_legacy_s89(rel, _orig=_orig_sha_s89):
    if str(rel).replace("\\", "/").endswith("pcbflow/config.py"):
        return ("f515c34842521a645145a9f5454a5919274a242e5c8c27c01fa"
                "f1a4c13e73baf")
    if str(rel).replace("\\", "/").endswith("pcbflow/cli.py"):
        # REPAIR-G1+ W-1/W-2（2026-09-24）：cli.py 授权变更 0a738047->
        # 3bfc9407（登记=out/repair-g1plus-r1/anchor-hashes-post-g1plus.
        # json）；冻结语境回放补 cli 腿（与 config 同构）
        return "0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e"
    return _orig(rel)


S89._sha = _sha_g0_legacy_s89


@pytest.fixture(scope="module")
def run_doc():
    """run-r25 文档内存构建（纯函数；只读输入、零写盘）。"""
    return S89.build_run()


@pytest.fixture(scope="module")
def instances():
    """十二实例主记录（逐实例两板合计口径；只读输入、零写盘）。"""
    parsed = {key: S89.parse_reader_raw(rel)
              for key, rel in S89.RAW_FILES.items()}
    deriv = S89._json_load(S89.REL_DERIV_R5)
    gt_applied = S89._gt_entries_with_r5_reprojection(S89.REL_GT_V2, deriv)
    gt_prep1 = S89._gt_entries_with_r5_reprojection(S89.REL_GT_V1, deriv)
    return {name: S89.build_instance_record(
        name, S89.INSTANCES[name], parsed, gt_applied, gt_prep1)
        for name in INSTANCE_ORDER}


# ---------------------------------------------------------------------------
# 输入核验（fail-closed）
# ---------------------------------------------------------------------------

def test_reader_raw_inputs_parse_and_flag_counts():
    """24 件 reader-raw-r25 全在盘、合法解析；实例旗数 10/15/28/17/6/7/
    0/4/6/4/6/4、弃权 3/7/8/11/6/1/0/4/4/4/6/4；拒收为零；R25T/R25B 前
    置=指引 §6 落盘固化（机械派生新件）；11/11 有旗实例跨板连续+2 格零旗
    标=bottom-i1 两板合法零旗输出（与 prep-record naming 声明相符）。"""
    parsed = {k: S89.parse_reader_raw(rel)
              for k, rel in S89.RAW_FILES.items()}
    assert sorted(parsed) == sorted(S89.RAW_FILES)
    assert len(parsed) == 24
    for n in INSTANCE_ORDER:
        cnts = [len(parsed[p]["images"][0]["flags"])
                for p in S89.INSTANCES[n]["parts"]]
        assert sum(cnts) == {"top-i1": 10, "top-i2": 15, "top-i3": 28,
                             "top-i4": 17, "top-i5": 6, "top-i6": 7,
                             "bottom-i1": 0, "bottom-i2": 4, "bottom-i3": 6,
                             "bottom-i4": 4, "bottom-i5": 6,
                             "bottom-i6": 4}[n]
    for k, p in parsed.items():
        assert p["reader_id"].startswith("reader-r25-")
        assert p["direct_json_parse"] is True
        assert p["repair"] == "no_repair"
        for img in p["images"]:
            assert img["rejected"] == []
            for f in img["flags"]:
                assert f["flag_id"].startswith(("R25T-", "R25B-"))
    abst = {n: 0 for n in INSTANCE_ORDER}
    for n in INSTANCE_ORDER:
        for p in S89.INSTANCES[n]["parts"]:
            for img in parsed[p]["images"]:
                for f in img["flags"]:
                    assert f["abstain"] is not None
                    if f["abstain"]:
                        abst[n] += 1
    assert abst == {"top-i1": 3, "top-i2": 7, "top-i3": 8, "top-i4": 11,
                    "top-i5": 6, "top-i6": 1, "bottom-i1": 0, "bottom-i2": 4,
                    "bottom-i3": 4, "bottom-i4": 4, "bottom-i5": 6,
                    "bottom-i6": 4}


def test_parse_reader_raw_fail_closed_and_view_mapping():
    """fail-closed 语义：缺文件→OSError（不返回解析结果）；_fail→
    SystemExit；view_for_image 确定性映射（*-top.png→top、*-bottom.png→
    bottom、无后缀→ValueError）。"""
    with pytest.raises(OSError):
        S89.parse_reader_raw(
            "out/v3-tl2/calibration/reader-raw-r25-NO-SUCH-FILE.txt")
    with pytest.raises(SystemExit):
        S89._fail("输入缺失（fail-closed）: <构造缺件>")
    assert S89.view_for_image("board-applied-top.png") == "top"
    assert S89.view_for_image("board-prep1-bottom.png") == "bottom"
    with pytest.raises(ValueError):
        S89.view_for_image("board-side.png")


def test_pinned_raw_prefixes_and_frozen_anchor_hashes():
    """24 件盲读原始件盘态钉死前缀逐字命中+输入先验锚全集合（协议/GT/
    指引 r8–r23+本轮 r25/prep/axis-plan/dev-r22/dev-r23/dev-r24/run-r22/
    run-r23/run-r24/24 reader 件/PNG/PDF）与盘上实测逐一相等（哈希不符即
    拒算前提）；本轮指引锚=guidance-r25 86af24dd（机械派生新件）、
    prep-r25=0943a8ec、run-r16（M1 基线复算输入）在锚集；run-r25=本包
    唯一新建输出、不在 FROZEN 锚集。"""
    assert len(S89.RAW_PINNED_PREFIXES) == 24
    for key, prefix in S89.RAW_PINNED_PREFIXES.items():
        got = S89._sha(S89.RAW_FILES[key])
        assert got.startswith(prefix), (key, got[:8], prefix)
    assert S89.FROZEN_SHA256[S89.REL_GUIDANCE_R25].startswith("86af24dd")
    assert S89.FROZEN_SHA256[S89.REL_GUIDANCE_R23].startswith("866b0157")
    assert S89.FROZEN_SHA256[S89.REL_PREP_R25].startswith("0943a8ec")
    assert S89.FROZEN_SHA256[S89.REL_DEV_R24].startswith("1a344edf")
    assert S89.FROZEN_SHA256[S89.REL_RUN_R24P].startswith("8a9bdb7d")
    assert S89.FROZEN_SHA256[S89.REL_RUN_R16].startswith(
        hashing.sha256_file(os.path.join(REPO, S89.REL_RUN_R16))[:8])
    assert len(S89.FROZEN_SHA256) > 60
    for rel, want in S89.FROZEN_SHA256.items():
        assert S89._sha(rel) == want, rel
    assert S89.REL_RUN_R25 not in S89.FROZEN_SHA256


# ---------------------------------------------------------------------------
# rubric 链重放对拍+优先级单元+r25 家族计数
# ---------------------------------------------------------------------------

def test_rubric_replay_r13_r16_chain_matches_frozen_counts():
    """r13–r16 132 条弃权旗 rubric 机械重放对拍：逐旗 family 与分型件
    在案记录逐一相等；contact 链 8/15/5/10、blackdot 链 9/14/8/12 与已
    冻结件（分型件 matrix+prep-record 锚）一致——链式回放先核对一致才可
    应用 r25 分型。"""
    typology_doc = S89.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    proof = S89.replay_typology_families(typology_doc, kt)
    assert proof["per_flag_total"] == 132
    assert proof["contact_counts"] == {"r13": 8, "r14": 15,
                                       "r15": 5, "r16": 10}
    assert proof["blackdot_counts"] == {"r13": 9, "r14": 14,
                                        "r15": 8, "r16": 12}
    assert typology_doc["matrix"]["round_totals"]["r16"]["families"][
        "contact"] == 10


def test_rubric_classify_and_r25_family_counts(run_doc, instances):
    """classify 优先级单元+r25 全部 107 条旗逐旗 rubric 分类：
    contact=3（全视；top 3+bottom 0；r16 基线 10）、existence_blackdot=22
    （低于 r24 的 28、高于 r19/r22/r23 三基线）、existence_other=20、
    semantic_confusion=0、other=13（n=6 口径新高）——与登记表/run 机制
    观察口径逐一相等；黑点弃权旗 22 条全弃权（逐实例分旗）、黑点转非弃权
    旗 4 条；exit_type 主出口分型=接触 5+存在 20+其他 11（两套口径分列）。"""
    typology_doc = S89.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    # 优先级单元（blackdot 先于 contact；泛化兜底→existence_other）
    fam, _ = S89.rubric_classify(
        "一枚黑色钻孔圆点紧贴焊盘，无法分辨真实接触与视觉贴近", kt)
    assert fam == "existence_blackdot"
    fam, _ = S89.rubric_classify(
        "两 courtyard 轮廓看似相接，无法区分真实接触与视觉贴近", kt)
    assert fam == "contact"
    fam, _ = S89.rubric_classify("该形态无法负责任确认", kt)
    assert fam == "existence_other"
    # r25 全旗套用
    rows = S89.build_rubric_rows_r24(instances, kt)
    fam_counts = {fam: sum(1 for r in rows
                           if r["abstain"] and r["family"] == fam)
                  for fam in ("contact", "existence_blackdot",
                              "existence_other", "semantic_confusion",
                              "other")}
    assert fam_counts == S89.R25_FAMILY_COUNTS_REGISTERED
    assert fam_counts == {"contact": 3, "existence_blackdot": 22,
                          "existence_other": 20, "semantic_confusion": 0,
                          "other": 13}
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    assert mo["black_dot_tracking"]["rubric_families"]["counts"] == \
        fam_counts
    assert len(rows) == 107  # 107 旗逐旗入账（弃权 58+非弃权 49）
    assert sum(1 for r in rows if r["abstain"]) == 58
    exit_counts = {"contact": 0, "existence": 0, "other_layer": 0}
    for r in rows:
        if r["abstain"] and r["instance"].startswith("top"):
            exit_counts[r["exit_type"]] += 1
    assert exit_counts == S89.R25_TOP_EXIT_TYPOLOGY_REGISTERED


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
    M3 整数直接）；round_view_aggregate 六实例两板合计（36/83、22/24）；
    M4(n=6)=12 格率先 6 位定点取率再取极差 1.0−0.0=1.0；
    split_half=|0.339623−0.600000|=0.260377（6 位定点 260377）；median6
    恰 6 值取第 3/4 序位均值。"""
    assert S89._m_tuple_6dp(0.433735, 0.916667, 22, 1.0) == \
        (433735, 916667, 22, 1000000)
    assert S89._m_tuple_6dp(0.461538, 0.571429, 4, 0.211111) == \
        (461538, 571429, 4, 211111)
    inst = {
        "top-i1": _synthetic_instance("top-i1", "top", 10, 3, 0.3),
        "top-i2": _synthetic_instance("top-i2", "top", 15, 7, 0.466667),
        "top-i3": _synthetic_instance("top-i3", "top", 28, 8, 0.285714),
        "top-i4": _synthetic_instance("top-i4", "top", 17, 11, 0.647059),
        "top-i5": _synthetic_instance("top-i5", "top", 6, 6, 1.0),
        "top-i6": _synthetic_instance("top-i6", "top", 7, 1, 0.142857),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 0, 0, None),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 4, 1.0),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 6, 4,
                                         0.666667),
        "bottom-i4": _synthetic_instance("bottom-i4", "bottom", 4, 4, 1.0),
        "bottom-i5": _synthetic_instance("bottom-i5", "bottom", 6, 6, 1.0),
        "bottom-i6": _synthetic_instance("bottom-i6", "bottom", 4, 4, 1.0),
    }
    ab, fl = S89.round_view_aggregate(
        inst, tuple(f"top-i{i}" for i in range(1, 7)))
    assert (ab, fl) == (36, 83)
    assert S89.cal._ratio(ab, fl) == 0.433735
    ab_b, fl_b = S89.round_view_aggregate(
        inst, tuple(f"bottom-i{i}" for i in range(1, 7)))
    assert (ab_b, fl_b) == (22, 24)
    assert S89.cal._ratio(ab_b, fl_b) == 0.916667
    # M4(n=6)：12 格率定点化后取极差（top 12 格实测构成）
    cells = [(4, 1), (6, 2), (7, 3), (8, 4), (14, 4), (14, 4),
             (8, 5), (9, 6), (2, 2), (4, 4), (3, 0), (4, 1)]
    vals = [int(round(S89.cal._ratio(a, n) * 1000000)) for n, a in cells]
    assert max(vals) - min(vals) == 1000000
    assert min(vals) == 0  # top-i6/applied=0/3（最小格）
    # split-half（6 位定点整数交叉相乘口径；本轮=机制观察单列）
    a6 = round(18 * 1000000 / 53)
    b6 = round(18 * 1000000 / 30)
    assert (a6, b6, abs(a6 - b6)) == (339623, 600000, 260377)
    assert S89.cal._round6(260377 / 1000000) == 0.260377
    # median6=第 3/4 序位均值
    assert S89._median6([10, 15, 28, 17, 6, 7]) == 12.5
    assert S89._median6([0, 4, 6, 4, 6, 4]) == 4.0
    assert S89._median6([0.3, 0.466667, 0.285714, 0.647059, 1.0,
                         0.142857]) == 0.3833335


def test_view_layer_and_r16_baseline_live_replay():
    """r16 基线=同一聚合逻辑对 run-r16 内嵌输入双侧复算（不手工抄数）：
    top 27/35=0.771429、bottom 12/14=0.857143、G1 基线 courtyard 非弃权
    0/0/0；视角层构造小样例（r25 top 六实例弃权率全部有定义、中位数=
    0.3833335；bottom 含 bottom-i1 零旗格 None→中位数 None+min/max 按可
    计算实例=item 5 None 口径触发）。"""
    run16 = S89._json_load(S89.REL_RUN_R16)
    assert S89.r16_top_abstain_aggregate_live(run16) == (27, 35)
    assert S89.r16_bottom_abstain_aggregate_live(run16) == (12, 14)
    assert S89.r16_baseline_courtyard_live(run16) == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    layer = S89.build_view_layer({
        "top-i1": _synthetic_instance("top-i1", "top", 10, 3, 0.3),
        "top-i2": _synthetic_instance("top-i2", "top", 15, 7, 0.466667),
        "top-i3": _synthetic_instance("top-i3", "top", 28, 8, 0.285714),
        "top-i4": _synthetic_instance("top-i4", "top", 17, 11, 0.647059),
        "top-i5": _synthetic_instance("top-i5", "top", 6, 6, 1.0),
        "top-i6": _synthetic_instance("top-i6", "top", 7, 1, 0.142857),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 0, 0, None),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 4, 4, 1.0),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 6, 4,
                                         0.666667),
        "bottom-i4": _synthetic_instance("bottom-i4", "bottom", 4, 4, 1.0),
        "bottom-i5": _synthetic_instance("bottom-i5", "bottom", 6, 6, 1.0),
        "bottom-i6": _synthetic_instance("bottom-i6", "bottom", 4, 4, 1.0),
    })
    assert layer["top"]["abstain_rate"]["median"] == 0.3833335
    assert layer["top"]["abstain_rate_range"] == 0.857143
    assert layer["bottom"]["abstain_rate"]["median"] is None  # None 口径
    assert layer["bottom"]["abstain_rate"]["min"] == 0.666667
    assert layer["bottom"]["abstain_rate"]["max"] == 1.0
    assert layer["bottom"]["abstain_rate_range"] == 0.333333
    assert layer["top"]["flag_count"]["median"] == 12.5


# ---------------------------------------------------------------------------
# 归因三支边界（adjudicate_attribution 构造用例）
# ---------------------------------------------------------------------------

def test_adjudicate_criterion_dominated_branch_and_thresholds():
    """(cd) 支：G1 维持+M4<261904→criterion_dominated；端点（恰
    261903→criterion_dominated、0→criterion_dominated）；阈值常量与判据
    原文同锚；M4 自证=928571−666667=261904 整数复算。"""
    assert S89.adjudicate_attribution(200_000, True) == \
        ("criterion_dominated", "criterion_dominated_m4_within")
    assert S89.adjudicate_attribution(261_903, True) == \
        ("criterion_dominated", "criterion_dominated_m4_within")
    assert S89.adjudicate_attribution(0, True) == \
        ("criterion_dominated", "criterion_dominated_m4_within")
    # 阈值常量与 s90/判据原文同锚
    assert S89.M4_THRESHOLD_6DP == 261_904
    assert S89.SPLIT_HALF_THRESHOLD_6DP == 90_640
    # M4 自证（prep-record fixed_point_comparison_note 原文）
    assert 928571 - 666667 == 261904
    assert S89.SPLIT_HALF_THRESHOLD_6DP == abs(862069 - 771429)


def test_adjudicate_not_criterion_dominated_and_guard_branches():
    """(ncd)/(gi) 支+支序：G1 维持且 M4≥261904→not_criterion_dominated
    （本轮实况：M4=1000000）；反事实构造：M4 内→criterion_dominated（分
    岔另一侧）；G1 破坏→guard_interrupted（支序最高，即使 M4 条件内）；
    M4 恰=261904=超出端点。"""
    # 本轮实际落支：M4=1000000 超出、G1 维持
    assert S89.adjudicate_attribution(1_000_000, True) == \
        ("not_criterion_dominated", "not_criterion_dominated_m4_exceeds")
    # 反事实构造：M4 内=criterion_dominated（分岔另一侧）
    assert S89.adjudicate_attribution(261_903, True) == \
        ("criterion_dominated", "criterion_dominated_m4_within")
    # 端点：M4 恰=261904=超出
    assert S89.adjudicate_attribution(261_904, True) == \
        ("not_criterion_dominated", "not_criterion_dominated_m4_exceeds")
    # G1 破坏→guard_interrupted（支序最高：三支字母口径均不命中、不新增
    # 字母支；即使 M4 条件内）
    assert S89.adjudicate_attribution(200_000, False) == \
        ("guard_interrupted", "guard_interrupted_g1")
    assert S89.adjudicate_attribution(1_000_000, False) == \
        ("guard_interrupted", "guard_interrupted_g1")


# ---------------------------------------------------------------------------
# G1/G2 守门与援引分记（机制观察）
# ---------------------------------------------------------------------------

def test_guards_g1_g2_and_citation_observation(run_doc, instances):
    """G1 实测（n=6 操作化定义）：bottom courtyard 非弃权六实例全 0=G1
    维持（r16 基线 live 重放对照、r20 破坏 2/0/0 在案）；G2 清零维持（几何门
    R19=0→R22=2→R23=1→R24=0→R25=0）；guard_channel g1_ok=True、g2=True、
    guards_ok=True；判据布尔（not_criterion_dominated 命中/其余两支不命
    中）；援引分记（旗级 §5B=0/(iii-a)=11/分支(=0/弃权边界条款=16+三问=13；
    notes 级 §5B=0/24、(iii-a)=12/24、§6=9/24、弃权边界条款=24/24[三问
    22/24]；候选解释列举 58/58；(iii-a) 11 旗逐旗摘录在案）。"""
    assert S89.bottom_courtyard_non_abstain(instances) == \
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
    assert gc["g2_geometry_gate_r25"] == 0
    g12 = run_doc["hypothesis_test"]["mechanism_observation"]["guards_g1_g2"]
    assert g12["counts"]["guards_ok"] is True
    assert g12["counts"]["g1_ok"] is True
    assert g12["counts"]["g2_guard_ok_axis_plan_semantics"] is True
    assert g12["counts"]["g1_bottom_courtyard_non_abstain_r25"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0, "bottom-i4": 0,
         "bottom-i5": 0, "bottom-i6": 0}
    assert g12["counts"]["g1_r16_baseline_live"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert g12["counts"]["g1_r20_broken_registered"] == \
        {"bottom-i1": 2, "bottom-i2": 0, "bottom-i3": 0}
    # 判据布尔（not_criterion_dominated 支命中、其余两支不命中）
    assert m["crit_not_criterion_dominated"] is True
    assert m["crit_guard_interrupted"] is False
    assert m["crit_criterion_dominated"] is False
    # 单判据定点锚（与盘上登记逐一相等；split_half=机制观察单列）
    assert m["m4_threshold_6dp"] == 261904
    assert m["split_half_threshold_6dp"] == 90640
    assert m["r25_m_tuple_6dp"]["M4"] == 1.0
    assert m["r25_m_tuple_6dp"]["split_half_M1_diff"] == 0.260377
    # 援引分记（多条款分开记、互不合并；机制观察单列）
    cc = run_doc["hypothesis_test"]["mechanism_observation"][
        "criterion_citation_observation"]
    counts = cc["citation_counts"]
    assert counts["flag_level_s5b_literal"] == 0
    assert counts["flag_level_iiia_literal"] == 11
    assert counts["flag_level_branch_literal"] == 0
    assert counts["flag_level_clause_literal"] == 16
    assert counts["flag_level_sanwen_literal"] == 13
    assert counts["flag_level_s5b_sources"] == \
        S89.S5B_FLAG_CITE_REGISTERED == []
    assert counts["flag_level_iiia_sources"] == \
        S89.IIIA_FLAG_CITE_REGISTERED
    assert counts["flag_level_clause_sources"] == \
        S89.CLAUSE_FLAG_CITE_REGISTERED
    assert counts["flag_level_sanwen_sources"] == \
        S89.SANWEN_FLAG_CITE_REGISTERED
    assert len(cc["iiia_flag_rows"]) == 11
    assert all("(iii-a)" in r["location_evidence_excerpt"]
               for r in cc["iiia_flag_rows"])
    assert counts["notes_level_s5b"] == 0
    assert counts["notes_level_s5b_sources"] == S89.S5B_NOTES_CITE_REGISTERED
    assert counts["notes_level_iiia"] == 12
    assert counts["notes_level_iiia_sources"] == \
        S89.IIIA_NOTES_CITE_REGISTERED
    assert counts["notes_level_s6_clause"] == 9
    assert counts["notes_level_s6_clause_sources"] == \
        S89.S6_NOTES_CITE_REGISTERED
    assert counts["notes_level_clause"] == 24
    assert counts["notes_level_clause_sources"] == \
        S89.CLAUSE_NOTES_CITE_REGISTERED
    assert counts["notes_level_sanwen"] == 22
    assert counts["notes_level_sanwen_sources"] == \
        S89.SANWEN_NOTES_CITE_REGISTERED
    # 条款行为观察（三问援引率+候选解释列举率）
    assert counts["abstain_flags_with_cand_explain"] == 58
    assert counts["abstain_flags_total"] == 58
    assert "22/24" in counts["clause_behavior_observation"]
    # r19/r22/r23/r24 基线对照（在案登记）
    assert "10/12" in counts["baseline_r19_iiia"]
    assert "旗级全 0" in counts["baseline_r22_iiia"]
    assert "4/12" in counts["baseline_r23_iiia"]
    assert "8/24" in counts["baseline_r24_iiia"]


# ---------------------------------------------------------------------------
# 守卫、run 记录身份与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；既有且
    不同→fail；_commit=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写；run-r25 盘上件不可覆写）。"""
    assert S89.overwrite_guard(None, b"abc") == "write"
    assert S89.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S89.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S89._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S89._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S89._commit(p, b"abc", "probe")


def test_run_record_canonical_identity_and_letter_verdict(run_doc):
    """run-r25 盘上件：同参重建两次 byte-exact+盘上件=canonical 重建+
    轮次身份（r25/2026-09-10/development 域）+verdict=not_criterion_
    dominated（唯一正式裁决）+落支 not_criterion_dominated_m4_exceeds（M4
    条件超出）+五键与比较集五行+判据内容轴归因轮轮次性质（指引机械派生/
    渲染零变更/changed_variables=1/axis=criterion_content）+判据原文
    摘录与 prep-record 逐字一致。"""
    b1 = hashing.canonical_json_bytes(S89.build_run())
    b2 = hashing.canonical_json_bytes(S89.build_run())
    assert b1 == b2  # 同参重建 byte-exact
    path = os.path.join(CAL_DIR, "calibration-run-r25.json")
    raw = open(path, "rb").read()
    assert raw == b1  # 盘上件=canonical 重建（byte-exact 可重跑）
    assert hashing.sha256_file(path).startswith("251102e8")
    doc = json.loads(raw.decode("utf-8"))
    assert doc["kind"] == "tl2_calibration_run_r25"
    assert doc["round_id"] == ROUND_ID
    assert doc["round_label"] == ROUND_LABEL
    assert doc["declared_date"] == DECLARED_DATE
    assert doc["evaluation_domain"] == "development"
    assert doc["evaluation_domain_note"]["in_calibrated_range"] is False
    assert doc["instrument_change"]["changed"] is False
    assert doc["instrument_change"]["axis_id"].startswith("criterion_content")
    hyp = doc["hypothesis_test"]
    m = hyp["measurement"]
    assert hyp["hypothesis_id"] == \
        "r24-not-instance-dominated-criterion-boundary-" \
        "operationalization-attribution"
    assert hyp["verdict"] == "not_criterion_dominated"
    assert m["verdict"] == "not_criterion_dominated"
    assert "(ncd)" in m["letter_branch"]
    assert "0.261904" in m["letter_branch"]
    assert "判据内容非主因" in m["letter_branch"]
    assert m["r25_m_tuple_6dp"] == {"M1": 0.433735, "M2": 0.916667,
                                    "M3": 22, "M4": 1.0,
                                    "split_half_M1_diff": 0.260377}
    assert m["comparison_rows_live"]["r16_baseline"] == \
        {"M1": 0.771429, "M2": 0.857143, "M3": 12, "M4": 0.261904}
    assert m["comparison_rows_live"]["r19_axis3"] == \
        {"M1": 0.461538, "M2": 0.571429, "M3": 4, "M4": 0.211111}
    assert m["comparison_rows_live"]["r22_repeat_live"] == \
        {"M1": 0.390244, "M2": 0.2, "M3": 4, "M4": 0.104545}
    assert m["comparison_rows_live"]["r23_repeat_live"] == \
        {"M1": 0.484848, "M2": 0.571429, "M3": 8, "M4": 0.520833}
    assert m["comparison_rows_live"]["r24_expansion_live"] == \
        {"M1": 0.552381, "M2": 0.692308, "M3": 28, "M4": 0.888889}
    assert m["top_abstain_count_r25"] == 36
    assert m["top_abstain_flags_r25"] == 83
    assert "36/83" in m["top_abstain_rate_r25_arithmetic"]
    assert m["contact_family_abstain_flags_rubric_r25"] == 3
    assert m["split_half_M1_diff_r25"] == 0.260377
    # 预注册判据摘录=prep-record adjudication 原文（逐字一致；11 键）
    prep = S89._json_load(S89.REL_PREP_R25)
    adj = prep["hypothesis_test"]["adjudication"]
    q = hyp["preregistered_criteria_quote"]
    for k in ("criterion_dominated", "not_criterion_dominated",
              "guard_interrupted", "letter_branch_map",
              "fixed_point_comparison_note", "g2_observation_separate",
              "m1_m2_gate_separate", "descriptive_boundary_note",
              "mechanism_observation_separate", "metric_lesson_separate",
              "three_way_bookkeeping"):
        assert q[k] == adj[k], k
    assert prep["hypothesis_test"]["hypothesis_id"] == hyp["hypothesis_id"]
    # changed_variables=1（§4 末尾弃权边界操作化条款单变量；指引=机械派生
    # 新件[基座 866b0157→产物 86af24dd]；渲染/GT/阈值/协议正文零变更）
    assert len(prep["changed_variables"]) == 1
    assert prep["no_instrument_change"] is True
    assert prep["guidance_reuse"]["mode"] == "mechanical_transform_derive"
    assert prep["guidance_reuse"]["base_sha256"].startswith("866b0157")
    assert prep["guidance_reuse"]["derived_sha256"].startswith("86af24dd")
    assert prep["guidance_reuse"]["byte_size"] == {
        "base": 23125, "delta": 937, "derived": 24062}
    # 条款在件断言（唯一变量逐字在盘上 r25 指引内）
    clause = prep["guidance_reuse"]["edit_list"][5]["text_full"]
    g25 = open(os.path.join(REPO, S89.REL_GUIDANCE_R25),
               encoding="utf-8").read()
    assert clause and clause in g25
    assert "把握不足本身不构成弃权理由" in g25
    assert "三问顺序不得颠倒" in g25


def test_gt_dual_union_joint_gate_in_range_false(run_doc):
    """GT 双口径 union=1/13=0.076923、agreement=0/13（GT-REVC-AP-1-R5U6
    由 applied-top-i4 R25T-005 单实例命中[<4/6 不计入 agreement]）；代表
    配置（top-i1+bottom-i4；top 第 3 序位唯一、bottom tie 按实例编号先序）
    聚合 14/7/0.5、joint not_met、连续=0；in_calibrated_range 恒 False
    （run 与 compliance 双处）；本轮零旗格=2 格（bottom-i1 两板、None 口径
    触发=bottom 中位数 None）。"""
    doc = run_doc
    dual = doc["gt_match_dual"]
    assert (dual["union"]["count"], dual["agreement"]["count"],
            dual["denominator"]) == (1, 0, 13)
    assert dual["union"]["gt_ids"] == ["GT-REVC-AP-1-R5U6"]
    assert dual["agreement"]["gt_ids"] == []
    assert dual["union"]["gt_recall_union"] == 0.076923
    assert dual["agreement"]["gt_recall_agreement"] == 0.0
    hits = [pg for pg in dual["per_gt"] if pg.get("hits")]
    assert len(hits) == 1
    assert hits[0]["matched_by_count"] == 1
    got = {(h["flag_id"], h["instance"], h["state"])
           for h in hits[0]["hits"]}
    assert got == {("R25T-005", "top-i4", "applied")}
    comp = doc["compliance_representative"]
    agg = doc["aggregation_representative"]
    assert (agg["flag_count_total"], agg["abstain_count_total"],
            agg["abstain_rate_total"], agg["gt_recall_total"],
            agg["seed_match_rate_total"]) == (14, 7, 0.5, 0.0, 0.0)
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
        {"top": "top-i1", "bottom": "bottom-i4"}
    assert doc["representative_configuration"]["selection"]["top"][
        "tie"] is False
    assert doc["representative_configuration"]["selection"]["bottom"][
        "tie"] is True  # bottom-i2/i4/i6 同为 4→按实例编号先序
    assert [(z["instance"], z["state"])
            for z in doc["reader"]["zero_flag_parts"]["parts"]] == \
        [("bottom-i1", "applied"), ("bottom-i1", "prep1")]
    assert doc["view_layer"]["bottom"]["abstain_rate"]["median"] is None
    assert doc["view_layer"]["bottom"]["abstain_rate_range"] == 0.333333
    assert doc["view_layer"]["top"]["abstain_rate_range"] == 0.857143


def test_experiment_ledger_nine_round_account_and_ranking(run_doc):
    """九行对照账完整性：r16/r17/r18/r19/r20/r22/r23/r24/r25 九行并列（M
    元组逐一相等）+r25 入排序居首（G1/G2 满足；排序=r19 第二/r24 第三/
    r18/r16 参照/r17 末位）+r20/r22/r23 资格门剔除+r24 在案入排序+三族
    计数对照四基线+split-half 分解+逐实例分布观察+归因结论位=not_criterion_
    dominated/0.261904/残余归因+显著收益 0.337694≥0.10 描述层命中+M1 降/
    M2 升分解单列+in_calibrated_range 恒 False 收尾。"""
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    ecl = mo["experiment_comparison_ledger"]
    assert ecl["r25_measured"]["M1"] == 0.433735
    assert ecl["r25_measured"]["M2"] == 0.916667
    assert ecl["r25_measured"]["M3"] == 22
    assert ecl["r25_measured"]["M4"] == 1.0
    assert ecl["r25_measured"]["split_half_M1_diff"] == 0.260377
    assert ecl["r25_measured"]["M1_arithmetic"] == "36/83"
    assert ecl["r25_measured"]["M2_arithmetic"] == "22/24"
    assert ecl["r25_measured"]["contact_family_abstain_flags_rubric"] == 3
    assert ecl["r25_measured"]["existence_other_family"] == 20
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
    assert ecl["r24_expansion_registered_row"] == {"M1": 0.552381,
                                                   "M2": 0.692308,
                                                   "M3": 28,
                                                   "M4": 0.888889}
    fc = ecl["family_counts_vs_r19_r22_r23_r24"]
    assert (fc["contact"]["r19_registered"], fc["contact"]["r22_registered"],
            fc["contact"]["r23_registered"], fc["contact"]["r24_registered"],
            fc["contact"]["r25_measured"]) == (4, 2, 8, 4, 3)
    assert (fc["existence_blackdot"]["r19_registered"],
            fc["existence_blackdot"]["r22_registered"],
            fc["existence_blackdot"]["r23_registered"],
            fc["existence_blackdot"]["r24_registered"],
            fc["existence_blackdot"]["r25_measured"]) == (4, 4, 8, 28, 22)
    assert (fc["existence_other"]["r19_registered"],
            fc["existence_other"]["r22_registered"],
            fc["existence_other"]["r23_registered"],
            fc["existence_other"]["r24_registered"],
            fc["existence_other"]["r25_measured"]) == (14, 12, 7, 44, 20)
    rk = ecl["ranking_by_comparison_rule"]
    # r25 入排序（G1/G2 满足）居首；r24 在案入排序；排序=r19 第二、r24 第三
    assert rk["r25_eligibility"] is True
    assert rk["r24_eligibility"] is True
    assert rk["r22_eligibility"] is False
    assert rk["r20_eligibility"] is False
    assert rk["r23_eligibility"] is False
    assert rk["ranking_order_best_first"] == ["r25_this_round", "r19_axis3",
                                              "r24_expansion", "r18_axis2",
                                              "r16_baseline", "r17_axis1"]
    assert rk["eligible_rows"] == ["r16_baseline", "r17_axis1",
                                   "r18_axis2", "r19_axis3",
                                   "r24_expansion", "r25_this_round"]
    assert set(rk["rows_registered"]) == {"r16_baseline", "r17_axis1",
                                          "r18_axis2", "r19_axis3",
                                          "r20_combo_registered",
                                          "r22_repeat_registered",
                                          "r23_repeat_registered",
                                          "r24_expansion",
                                          "r25_this_round"}
    assert rk["rows_registered"]["r25_this_round"]["M1"] == 0.433735
    assert rk["rows_registered"]["r25_this_round"]["M4"] == 1.0
    # split-half 分解与逐实例分布单列
    sh = mo["split_half_decomposition"]
    assert (sh["half_A"]["rate_6dp"], sh["half_B"]["rate_6dp"],
            sh["split_half_6dp"]) == (339623, 600000, 260377)
    assert sh["threshold_6dp"] == 90640
    assert "聚合移动" in sh["observation"]
    ido = mo["instance_distribution_observation"]
    assert ido["top_rates_by_instance"]["top-i5"] == 1.0
    assert ido["top_rates_by_instance"]["top-i6"] == 0.142857
    assert ido["m4_12_cell_range"] == 1.0
    att = ecl["attribution_conclusion"]["conclusion"]
    assert "not_criterion_dominated" in att
    assert "0.261904" in att
    assert "残余归因" in att
    assert "not_instance_dominated" in att  # r24 字母维持不改写
    assert S89.cal._round6(1.0 - 0.261904) == 0.738096
    sb = ecl["significant_benefit_vs_r16"]
    assert sb["met"] is True
    assert sb["r25_m1_absolute_drop"] == 0.337694
    assert round(0.771429 - 0.433735, 6) == 0.337694
    assert sb["r24_drop_reference"] == 0.219048
    # M1 降/M2 升分解单列（机制观察；两向均不进字母）
    shift = ecl["m1_m2_shift_observation"]
    assert "0.118646" in shift["m1"]
    assert "0.224359" in shift["m2"]
    assert "机制观察单列" in shift["status"]
    assert "m1_m2_gate_separate" in shift["role"]
    fd = ecl["direction_vs_r16"]
    assert fd["M1"].startswith("down") and fd["M2"].startswith("up")
    assert fd["M3"].startswith("up")
    # G2 出局条目本轮=0（空摘录）+r23 对照=1 条装载
    grej = mo["g2_rejected_entries_r25"]
    assert grej["count"] == 0 and grej["entries"] == []
    assert [e["flag_id"] for e in grej["comparison_to_r23"]["r23_entries"]] \
        == ["R23T-004"]
