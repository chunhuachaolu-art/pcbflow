"""R19 执行包测试（s71_calibration_r19_compare / calibration-run-r19）——
轴3 判据侧单变量轮（§4(iii-a) 可操作分辨条款，axis-experiment-plan-
r17-r20 stage1 R19=A3_criterion_contact_clarification；渲染零变更=
renders-r14b 四图字节复用；判读指引=observation-guidance-r19.md
8633bda5=r15 基座 d5babc93 机械变换派生+(iii-a) 增补，判据节首次变更、
反放宽条款逐字保留；GT/阈值/协议零变更）+ 预注册假设
（axis-plan-r19-criterion-operational）三分判据裁决：主度量=contact 族
弃权旗数（分型件 rubric 口径；r13–r16 链 8/15/5/10 重放对拍逐一相等；
r19 实测 4 vs r16 基线 10），(s) contact ≤5 成立但附加门 M4=top 逐实例
弃权率极差 0.211111>0.20 不成立（M1=18/39=0.461538≤0.85 成立、G1/G2
维持）⇒ supported 未成立；(r) contact ≥8 且 M4 >0.26 不成立；
(m) 未达 supported 且（contact ≤7 或 M4 ≤0.26）且 G1/G2 维持成立⇒
字母=marginal（部分收益；命中途径=contact ≤7 与 M4 ≤0.26 两支均满足）
+ 机制观察单列：(iii-a) 逐旗落支=残余弃权 8+侵入 6+间隙 0（间隙支全部
在 notes 级判正常路径 4 派次）+援引计数（旗级 (iii-a) 6、分支( 2、
notes 级 10/12）+家族计数 contact 4/existence_blackdot 4/
existence_other 14（对照 r18：黑点 13/存在性其他 12）+黑点转非弃权旗
6+判正常派次 3+top 弃权分型 contact 5/existence 13/other_layer 0 +
实验对照账 (M1,M2,M3,M4)=(0.461538, 0.571429, 4, 0.211111) vs r16
(0.771429, 0.857143, 12, 0.261904)/r17 (0.88, 0.75, 8, 0.333333)/
r18 (0.645161, 0.684211, 13, 0.277778)；comparison_rule 排序（含 r19）
=r19_axis3 第一；显著收益定义（M1 降幅 ≥0.10）命中 0.309891 + 守门
G1/G2 均 True 维持 + GT 双口径 union 1/13（唯一命中=prep1-top-i3
R19T-009↔GT-REVC-P1-L1SHORT）、agreement 0/13 + 零旗标派次=2
（bottom-i3 两板，item 5 None 口径触发） + in_calibrated_range 恒
False + development 域。

覆盖（14 测试，只读 out/、零子进程/零网络/零写盘）：
- 输入核验 fail-closed：12 件 reader-raw-r19 合法解析+实例旗数/弃权
  记账；缺文件→parse_reader_raw SystemExit；4 个 i3 件盘态钉死前缀
  （7941cb00/5591ce98/f4069303/fcc69fb5）；FROZEN_SHA256 全锚实测一致；
- contact 族 rubric：r13–r16 132 条弃权旗重放对拍（per_flag_total=132、
  blackdot 9/14/8/12、contact 8/15/5/10）+classify 优先级单元
  （blackdot 先于 contact/文本主因抑制/泛化兜底）+r19 家族计数
  （4/4/14/0/0 与登记一致）；
- M 元组：构造小样例验证 round_view_aggregate/_median3/M4 极差与
  build_view_layer 零旗标 None 语义（item 5）；
- 裁决四支边界：adjudicate_main_channel 纯函数构造用例——supported
  （M4 门内）、reject_contact（contact ≥8 且 M4 >0.26）、reject_guards
  （守门破坏）、marginal（r19 实测数 4/211111/18/39；两途径）与未覆盖
  组合 RuntimeError；
- 守卫与确定性：overwrite_guard 三态（write/idempotent_skip/fail）；
  run-r19 盘上件 canonical byte 与重建一致+轮次身份+verdict=marginal+
  M 元组+in_calibrated_range=False；
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


def _load_s71():
    path = os.path.join(REPO, "scripts", "s71_calibration_r19_compare.py")
    spec = importlib.util.spec_from_file_location("s71_calibration_r19",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S71 = _load_s71()


@pytest.fixture(scope="module")
def run_doc():
    """run-r19 文档内存构建（纯函数；只读输入、零写盘）。"""
    return S71.build_run()


# ---------------------------------------------------------------------------
# 输入核验（fail-closed）
# ---------------------------------------------------------------------------

def test_reader_raw_inputs_parse_and_flag_counts():
    """12 件 reader-raw-r19 全在盘、合法解析；实例旗数 11/18/10/4/3/0、
    弃权 5/7/6/3/1/0；拒收清单为空；R19T/R19B 前缀随指引落盘固化。"""
    parsed = {k: S71.parse_reader_raw(rel)
              for k, rel in S71.RAW_FILES.items()}
    assert sorted(parsed) == sorted(S71.RAW_FILES)
    counts = {n: (sum(len(i["flags"]) for i in parsed[p]["images"])
                  for p in S71.INSTANCES[n]["parts"])
              for n in INSTANCE_ORDER}
    flag_counts = {n: sum(c) for n, c in counts.items()}
    assert flag_counts == {"top-i1": 11, "top-i2": 18, "top-i3": 10,
                           "bottom-i1": 4, "bottom-i2": 3, "bottom-i3": 0}
    for k, p in parsed.items():
        assert p["reader_id"].startswith("reader-r19-")
        assert p["direct_json_parse"] is True
        assert p["repair"] == "no_repair"
        for img in p["images"]:
            for f in img["flags"]:
                assert f["flag_id"].startswith(("R19T-", "R19B-"))
    # 编号行为混合（top-i3 两板连续；top-i1 两板各自从头编号）
    doc_i3_prep = json.loads(open(
        os.path.join(CAL_DIR,
                     "reader-raw-r19-prep1-top-i3.txt"),
        encoding="utf-8").read())
    prep_ids = [f["flag_id"]
                for img in doc_i3_prep["per_image"]
                for f in img["flags"]]
    assert prep_ids[0] == "R19T-005"  # 接 applied 侧 R19T-001..004 连续
    doc_i1_prep = json.loads(open(
        os.path.join(CAL_DIR, "reader-raw-r19-prep1-top-i1.txt"),
        encoding="utf-8").read())
    prep_i1_ids = [f["flag_id"]
                   for img in doc_i1_prep["per_image"]
                   for f in img["flags"]]
    assert prep_i1_ids[0] == "R19T-001"  # 两板各自从头编号


def test_parse_reader_raw_missing_file_fails_closed():
    """缺文件→拒算（parse_reader_raw 直接抛 OSError 不返回解析结果；
    _fail=SystemExit fail-closed 语义在位，main 输入锚循环对缺件/错
    哈希即中止）。"""
    with pytest.raises(OSError):
        S71.parse_reader_raw(
            "out/v3-tl2/calibration/reader-raw-r19-NO-SUCH-FILE.txt")
    with pytest.raises(SystemExit):
        S71._fail("输入缺失（fail-closed）: <构造缺件>")


def test_i3_pin_prefixes_match_disk():
    """派发事故后盘态钉死：4 个 i3 件 sha256 前缀逐字命中
    （applied-top-i3=7941cb00、applied-bottom-i3=5591ce98、
    prep1-top-i3=f4069303、prep1-bottom-i3=fcc69fb5）。"""
    for key, prefix in S71.I3_PINNED_PREFIXES.items():
        got = S71._sha(S71.RAW_FILES[key])
        assert got.startswith(prefix), (key, got[:8], prefix)


def test_frozen_anchor_hashes_match_disk():
    """FROZEN_SHA256 全部输入锚（协议/GT/指引/prep/axis-plan/12 reader
    件/PNG/PDF/受保护链件）与盘上实测逐一相等（哈希不符即拒算前提）。"""
    assert len(S71.FROZEN_SHA256) == 76
    assert S71.FROZEN_SHA256[
        S71.REL_GUIDANCE_R19].startswith("8633bda5")
    assert S71.FROZEN_SHA256[S71.REL_PREP_R19].startswith("e4cf2d3c")
    for rel, want in S71.FROZEN_SHA256.items():
        assert S71._sha(rel) == want, rel


# ---------------------------------------------------------------------------
# contact 族 rubric（重放对拍+优先级单元+r19 家族计数）
# ---------------------------------------------------------------------------

def test_rubric_replay_r13_r16_chain_matches_frozen_counts():
    """r13–r16 132 条弃权旗 rubric 机械重放对拍：逐旗 family 与分型件
    在案记录逐一相等；blackdot 链 9/14/8/12、contact 链 8/15/5/10 与
    已冻结件（分型件 matrix+prep-record 锚）一致。"""
    typology_doc = S71.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    proof = S71.replay_typology_families(typology_doc, kt)
    assert proof["per_flag_total"] == 132
    assert proof["blackdot_counts"] == {"r13": 9, "r14": 14,
                                        "r15": 8, "r16": 12}
    assert proof["contact_counts"] == {"r13": 8, "r14": 15,
                                       "r15": 5, "r16": 10}
    assert typology_doc["matrix"]["round_totals"]["r16"]["families"][
        "contact"] == 10
    assert typology_doc["matrix"]["grand"]["families"]["contact"] == 38


def test_rubric_classify_priority_rules():
    """classify 优先级单元（词表=分型件装载）：blackdot 先于 contact、
    文本主因抑制 contact、显式存在性先于泛化兜底、残余=other。"""
    typology_doc = S71.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    # blackdot 先于 contact（黑点+贴近+无法分辨 → existence_blackdot）
    fam, _ = S71.rubric_classify(
        "一枚黑色钻孔圆点紧贴焊盘，无法分辨真实接触与视觉贴近", kt)
    assert fam == "existence_blackdot"
    # contact（结构间接触词+怀疑模式、无文本主因词）
    fam, _ = S71.rubric_classify(
        "两 courtyard 轮廓看似相接，无法区分真实接触与视觉贴近", kt)
    assert fam == "contact"
    # 文本主因抑制 contact（位号/连印语境 → 非contact 路径）
    fam, _ = S71.rubric_classify(
        "位号文字与焊盘交叠，无法确认位号笔画是否被遮断", kt)
    assert fam != "contact"
    # 泛化兜底（无显式存在性语言 → existence_other）
    fam, _ = S71.rubric_classify("该形态无法负责任确认", kt)
    assert fam == "existence_other"
    # 残余类
    fam, _ = S71.rubric_classify("普通描述文本", kt)
    assert fam == "other"


def test_r19_abstain_family_counts(run_doc):
    """r19 全部 22 条弃权旗逐旗 rubric 分类：contact=4（主度量，r16 基线
    10 的一半门槛内）、existence_blackdot=4、existence_other=14、
    semantic_confusion=0、other=0；黑点弃权旗集合/黑点转非弃权旗集合与
    登记表逐一相等。"""
    typology_doc = S71.load_typology_rubric()
    kt = typology_doc["rubric"]["keyword_tables"]
    instances = {}
    parsed = {key: S71.parse_reader_raw(rel)
              for key, rel in S71.RAW_FILES.items()}
    deriv = S71._json_load(S71.REL_DERIV_R5)
    gt_applied = S71._gt_entries_with_r5_reprojection(S71.REL_GT_V2, deriv)
    gt_prep1 = S71._gt_entries_with_r5_reprojection(S71.REL_GT_V1, deriv)
    instances = {name: S71.build_instance_record(
        name, S71.INSTANCES[name], parsed, gt_applied, gt_prep1)
        for name in INSTANCE_ORDER}
    rows = S71.build_rubric_rows_r19(instances, kt)
    fam_counts = {fam: sum(1 for r in rows
                           if r["abstain"] and r["family"] == fam)
                  for fam in ("contact", "existence_blackdot",
                              "existence_other", "semantic_confusion",
                              "other")}
    assert fam_counts == S71.R19_FAMILY_COUNTS_REGISTERED
    assert fam_counts == {"contact": 4, "existence_blackdot": 4,
                          "existence_other": 14, "semantic_confusion": 0,
                          "other": 0}
    bd = {(r["instance"], r["state"], r["flag_id"]) for r in rows
          if r["abstain"] and r["family"] == "existence_blackdot"}
    assert bd == {(i, s, f) for i, s, f, _ in S71.BLACK_DOT_FLAGS}
    nonabstain_bd = {(r["instance"], r["state"], r["flag_id"]) for r in rows
                     if not r["abstain"] and r["matched_blackdot_terms"]}
    assert nonabstain_bd == {(i, s, f) for i, s, f, _ in
                             S71.BLACK_DOT_NON_ABSTAIN_FLAGS}
    # run-doc 机制观察口径一致
    mo = run_doc["hypothesis_test"]["mechanism_observation"]
    assert mo["black_dot_tracking"]["rubric_families"]["counts"] == fam_counts
    assert mo["experiment_comparison_ledger"]["r19_measured"][
        "contact_family_abstain_flags_rubric"] == 4


# ---------------------------------------------------------------------------
# M 元组与视角层（构造小样例）
# ---------------------------------------------------------------------------

def _synthetic_instance(name, view, flag_count, abstain_count, rate):
    return {"instance": name, "view": view,
            "combined": {"flag_count": flag_count,
                         "abstain_count": abstain_count,
                         "abstain_rate": rate,
                         "matches_total": 0}}


def test_m_tuple_synthetic_computation(run_doc):
    """M 元组口径（构造小样例）：M1/M2=视角全旗聚合弃权率（三实例两板
    合计）、M4=top 逐实例弃权率先 6 位取率再取极差；与 r19 实测同法
    复算一致（18/39=0.461538、0.6−0.388889=0.211111）。"""
    # 构造：top 三实例 (5,11)、(7,18)、(6,10)
    inst = {
        "top-i1": _synthetic_instance("top-i1", "top", 11, 5, 0.454545),
        "top-i2": _synthetic_instance("top-i2", "top", 18, 7, 0.388889),
        "top-i3": _synthetic_instance("top-i3", "top", 10, 6, 0.6),
    }
    ab, fl = S71.round_view_aggregate(inst, ("top-i1", "top-i2", "top-i3"))
    assert (ab, fl) == (18, 39)
    assert S71.cal._ratio(ab, fl) == 0.461538
    rates = [0.454545, 0.388889, 0.6]
    assert S71.cal._round6(max(rates) - min(rates)) == 0.211111
    # median3（恰 3 值取第 2）
    assert S71._median3([11, 18, 10]) == 11
    assert S71._median3([4, 3, 0]) == 3
    assert S71._median3([5, 1, 9]) == 5
    # r19 实测 M 元组（run-doc 对照账）
    ledger = run_doc["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]
    assert ledger["r19_measured"]["M1"] == 0.461538
    assert ledger["r19_measured"]["M2"] == 0.571429
    assert ledger["r19_measured"]["M3"] == 4
    assert ledger["r19_measured"]["M4"] == 0.211111
    # 链上各行并列（r16 基线/r17 轴1/r18 轴2）
    assert ledger["r16_baseline_registered"]["M1"] == 0.771429
    assert ledger["r16_baseline_registered"]["M4"] == 0.261904
    assert ledger["r17_axis1_row"] == {"M1": 0.88, "M2": 0.75, "M3": 8,
                                       "M4": 0.333333}
    assert ledger["r18_axis2_row"] == {"M1": 0.645161, "M2": 0.684211,
                                       "M3": 13, "M4": 0.277778}


def test_view_layer_zero_flag_none_semantics():
    """measurement_design item 5（构造小样例）：零旗标实例弃权率=None、
    视角层中位数含 None→None（不编造数值）、min/max 按可计算实例。"""
    inst = {
        "top-i1": _synthetic_instance("top-i1", "top", 11, 5, 0.454545),
        "top-i2": _synthetic_instance("top-i2", "top", 18, 7, 0.388889),
        "top-i3": _synthetic_instance("top-i3", "top", 10, 6, 0.6),
        "bottom-i1": _synthetic_instance("bottom-i1", "bottom", 4, 3,
                                         0.75),
        "bottom-i2": _synthetic_instance("bottom-i2", "bottom", 3, 1,
                                         0.333333),
        "bottom-i3": _synthetic_instance("bottom-i3", "bottom", 0, 0,
                                         None),
    }
    layer = S71.build_view_layer(inst)
    bottom = layer["bottom"]
    assert bottom["abstain_rate"]["by_instance"]["bottom-i3"] is None
    assert bottom["abstain_rate"]["median"] is None
    assert bottom["abstain_rate"]["min"] == 0.333333
    assert bottom["abstain_rate"]["max"] == 0.75
    assert bottom["abstain_rate_range"] == 0.416667
    assert "None" in bottom["abstain_rate"]["median_note"]
    assert bottom["flag_count"]["median"] == 3
    # 全可计算实例：中位数=排序后第 2；极差=0.6−0.388889
    assert layer["top"]["abstain_rate"]["median"] == 0.454545
    assert layer["top"]["abstain_rate_range"] == 0.211111


# ---------------------------------------------------------------------------
# 裁决四支边界（adjudicate_main_channel 构造用例）
# ---------------------------------------------------------------------------

def test_adjudicate_supported_boundary():
    """(s) supported 边界：contact ≤5 且 M4 ≤0.20（6dp）且 M1 ≤0.85 且
    G 维持 → supported；M4 恰 0.20 在门内、0.20+1e-6 出门。"""
    verdict, key = S71.adjudicate_main_channel(
        contact=4, m4_6dp=200000, abst_top=18, flags_top=39, guards_ok=True)
    assert (verdict, key) == ("supported", "supported")
    # contact 恰 5、M1 恰 0.85（38×10^6=850000×44.7…→ 用整除样例
    # 17/20=0.85 恰在门内）
    verdict, key = S71.adjudicate_main_channel(
        contact=5, m4_6dp=200000, abst_top=17, flags_top=20, guards_ok=True)
    assert (verdict, key) == ("supported", "supported")
    # M4 门破坏（0.200001>0.20）→ 不再 supported（同组数落 marginal）
    verdict, key = S71.adjudicate_main_channel(
        contact=4, m4_6dp=200001, abst_top=18, flags_top=39, guards_ok=True)
    assert verdict == "marginal"
    # M1 门破坏（0.86>0.85）→ 非 supported
    verdict, _ = S71.adjudicate_main_channel(
        contact=4, m4_6dp=200000, abst_top=43, flags_top=50, guards_ok=True)
    assert verdict == "marginal"


def test_adjudicate_reject_branches():
    """(r) reject 两途径：contact ≥8 且 M4 >0.26 → reject_contact；
    G 破坏 → reject_guards（无论 contact/M4 落点）。"""
    verdict, key = S71.adjudicate_main_channel(
        contact=9, m4_6dp=280000, abst_top=30, flags_top=39, guards_ok=True)
    assert (verdict, key) == ("reject", "reject_contact")
    # contact ≥8 但 M4 ≤0.26 → 不构成 reject 字面（M4 门未过）→落
    # marginal（M4 ≤0.26 途径）
    verdict, key = S71.adjudicate_main_channel(
        contact=9, m4_6dp=260000, abst_top=30, flags_top=39, guards_ok=True)
    assert (verdict, key) == ("marginal", "marginal")
    # 守门破坏 → reject_guards（支序最高）
    verdict, key = S71.adjudicate_main_channel(
        contact=0, m4_6dp=0, abst_top=0, flags_top=1, guards_ok=False)
    assert (verdict, key) == ("reject", "reject_guards")


def test_adjudicate_marginal_r19_actual_and_uncovered(monkeypatch):
    """(m) marginal：r19 实测数（contact=4、M4=211111、M1=18/39、G 维持）
    → marginal；未达 supported 但（contact ≤7 或 M4 ≤0.26）两途径均
    计入；支序=守门破坏时即使 supported 条件全真也落 reject；
    reject∩supported 同中（monkeypatch 阈值构造）→RuntimeError
    （自洽性守卫）。"""
    verdict, key = S71.adjudicate_main_channel(
        contact=4, m4_6dp=211111, abst_top=18, flags_top=39, guards_ok=True)
    assert (verdict, key) == ("marginal", "marginal")
    # contact=6（>5 出 supported、≤7 入 marginal 途径一）、M4=0.30
    #（>0.26 途径二不成立）→ marginal 经 contact ≤7
    verdict, key = S71.adjudicate_main_channel(
        contact=6, m4_6dp=300000, abst_top=18, flags_top=39, guards_ok=True)
    assert (verdict, key) == ("marginal", "marginal")
    # contact=8、M4=0.25：reject 需 M4 >0.26 不成立；supported 需
    # contact ≤5 不成立；marginal 经 M4 ≤0.26 → marginal
    verdict, key = S71.adjudicate_main_channel(
        contact=8, m4_6dp=250000, abst_top=18, flags_top=39, guards_ok=True)
    assert (verdict, key) == ("marginal", "marginal")
    # 支序：守门破坏时即使 supported 条件全真也落 reject_guards
    verdict, key = S71.adjudicate_main_channel(
        contact=4, m4_6dp=200000, abst_top=18, flags_top=39,
        guards_ok=False)
    assert (verdict, key) == ("reject", "reject_guards")
    # 互斥自检：monkeypatch supported 阈值使 reject 与 supported 同中
    # （contact=9、M4=280000 同时满足两支字面）→ RuntimeError
    monkeypatch.setattr(S71, "SUPPORTED_CONTACT_MAX", 9)
    monkeypatch.setattr(S71, "SUPPORTED_M4_MAX_6DP", 280000)
    with pytest.raises(RuntimeError):
        S71.adjudicate_main_channel(
            contact=9, m4_6dp=280000, abst_top=18, flags_top=39,
            guards_ok=True)


# ---------------------------------------------------------------------------
# 守卫、域声明与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_semantics():
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；
    既有且不同→fail（绝不覆写）。"""
    assert S71.overwrite_guard(None, b"abc") == "write"
    assert S71.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S71.overwrite_guard(b"abc", b"xyz") == "fail"


def test_run_record_canonical_identity_and_domain(run_doc):
    """run-r19 盘上件：轮次身份（r19/2026-09-09/2026-09-09-r19）+
    development 域 in_calibrated_range 恒 False + verdict=marginal+
    字母落支含命中途径 + GT 双口径（union 1/13、agreement 0/13）+
    零旗标派次=2（bottom-i3 两板）+ canonical 重建 byte 一致
    （确定性；与盘上 sha e5755a11… 同源）+ 守门 G1/G2 均 True+
    early_stop 未触发。"""
    path = os.path.join(CAL_DIR, "calibration-run-r19.json")
    raw = open(path, "rb").read()
    canonical = hashing.canonical_json_bytes(run_doc)
    assert raw == canonical  # 盘上件=canonical 重建（byte-exact 可重跑）
    doc = json.loads(raw.decode("utf-8"))
    assert doc["kind"] == "tl2_calibration_run_r19"
    assert doc["round_id"] == ROUND_ID
    assert doc["round_label"] == ROUND_LABEL
    assert doc["declared_date"] == DECLARED_DATE
    assert doc["evaluation_domain"] == "development"
    assert doc["evaluation_domain_note"]["in_calibrated_range"] is False
    assert doc["instrument_change"]["changed"] is False
    assert doc["instrument_change"]["axis_id"] == \
        "A3_criterion_contact_clarification"
    hyp = doc["hypothesis_test"]
    m = hyp["measurement"]
    assert hyp["hypothesis_id"] == "axis-plan-r19-criterion-operational"
    assert hyp["verdict"] == "marginal"
    assert "contact ≤7" in m["letter_branch"]
    assert "M4 ≤0.26" in m["letter_branch"]
    assert hyp["preregistration_ref"]["path_rel"].endswith(
        "r19-prep-record.json")
    m = hyp["measurement"]
    assert m["contact_family_abstain_flags_rubric_r19"] == 4
    assert m["top_abstain_rate_r19"] == 0.461538
    assert m["m4_top_rate_range_r19"] == 0.211111
    assert m["guard_channel"]["g1_ok"] is True
    assert m["guard_channel"]["g2_guard_ok"] is True
    assert m["guard_channel"]["guards_ok"] is True
    assert doc["gt_match_dual"]["union"]["count"] == 1
    assert doc["gt_match_dual"]["union"]["gt_ids"] == ["GT-REVC-P1-L1SHORT"]
    assert doc["gt_match_dual"]["agreement"]["count"] == 0
    zf = doc["reader"]["zero_flag_parts"]["parts"]
    assert zf == [{"instance": "bottom-i3", "state": "applied",
                   "flag_count": 0},
                  {"instance": "bottom-i3", "state": "prep1",
                   "flag_count": 0}]
    assert doc["view_layer"]["bottom"]["abstain_rate"]["median"] is None
    iiia = hyp["mechanism_observation"]["iiia_branch_observation"]
    assert iiia["branch_counts_flag_level"] == {
        "branch1_gap_report": 0, "branch2_intrusion_report": 6,
        "branch3_residual_abstain": 8}
    assert iiia["citation_counts"]["flag_level_iiia_literal"] == 6
    assert iiia["citation_counts"]["notes_level_iiia"] == 10
    ledger = hyp["mechanism_observation"]["experiment_comparison_ledger"]
    ranking = ledger["ranking_by_comparison_rule"]
    assert ranking["ranking_order_best_first"][0] == "r19_axis3"
    assert ledger["significant_benefit_vs_r16"]["met"] is True
    assert ledger["significant_benefit_vs_r16"]["r19_m1_absolute_drop"] == \
        0.309891
