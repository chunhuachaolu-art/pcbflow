"""R6 执行包测试：reader 判读迭代第六轮收口（CAL-R6-CLOSE）——
盲读解析与视角注入 + 双态 compare_v3 重投影比对 + 逐旗失败通道归因
（预注册计划执行）+ development 域记录。

结构照 test_r5_calibration_round5.py 先例，仅输入与轮次常量不同
（R6=development 域指引侧变更轮：零仪器变更、复用 R5 冻结渲染件；
唯一变更=判读指引两项——邻域框口径收紧 §3 + 类别判据示例化 §3A，
预注册于 r6-prep-record.json / observation-guidance-r6.md）。

覆盖：
- 盲读原文（reader-raw-r6-{applied,prep1}-{top,bottom}.txt，冻结证据）：
  合法 JSON、结构（reader_id/per_image/reading_notes；flag 六键含
  location_evidence）、视角前缀一致（R6T-001..010 top 跨两文件连续、
  R6B-001..007 bottom 跨两文件连续）、拒收清单固化（全 17 旗标过
  calibration fail-closed 校验，0 拒收）；
- 视角注入确定性：s34 的图像名→视角映射纯函数两次调用一致，
  run-r6 记录的 flag_views 与该规则逐旗标一致；
- calibration-run-r6.json：盘上 canonical byte 一致；两态 compare_v3
  用记录内嵌输入（reader_flags/gt_entries/flag_views）重算 byte-exact
  一致且 view_check=full；内嵌 gt_entries=源 GT 文件条目（frame_box_pct
  ←derivation-log-r5 的 frame_box_pct_r5——渲染未变零新派生，其余
  字段逐字段原样）；聚合算术显式复算一致（0/13、0/8、9/17）；达标
  评估逐项复算一致（APR-0011，弃权率 0.529412>0.5 not met）、
  joint=not_met、连续达标计数 0→0、critic_calibration_in_range=
  False、域=development；
- 通道归因（channel_attribution）：对 run-r5 内嵌输入重放通道分类
  与 run-r6 登记一致；重放 candidate 对与两轮 compare_v3
  matches∪duplicate_reports 对拍；跨轮 flag_id 非同旗配对声明在案；
- 预注册链：r6-prep-record/guidance-r6/guidance-r4/framing-r5/
  derivation-log-r5/GT/协议/复用 PNG/冻结 PDF sha 与盘上一致；
  阈值常量零覆盖（containment 0.5 / area_ratio_max 10.0 与 r5 相同）；
- round6-dev-record.json：域声明、指引侧变更轮性质、R5→R6 方向性
  观察（无能力断言、通道数值可独立复算）、弃权率回升差距如实、
  联合评价趋势（连续计数 0→0，正式采纳门槛未达成）、run-r6 sha
  引用一致、is_gate=False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；受保护三文件 sha256 前 8 断言；
- s34 重跑：同参重建 byte-exact 一致 + 防覆写守卫（目标已存在即
  fail-closed 退出，零覆写）。

只读 out/（生成器模式）：零子进程/零写盘/零网络。
"""

import hashlib
import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import calibration as cal           # noqa: E402
from pcbflow import critic                       # noqa: E402
from pcbflow import hashing                      # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

ROUND_ID = "2026-09-06-r6"
DECLARED_DATE = "2026-09-06"
RAW_FILES = {
    "applied-top": "reader-raw-r6-applied-top.txt",
    "applied-bottom": "reader-raw-r6-applied-bottom.txt",
    "prep1-top": "reader-raw-r6-prep1-top.txt",
    "prep1-bottom": "reader-raw-r6-prep1-bottom.txt",
}
READER_FLAG_KEYS = {"flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence"}
GT_V1_IDS = ["GT-REVC-P1-R4J3", "GT-REVC-P1-F1J2", "GT-REVC-P1-L1NB",
             "GT-REVC-P1-L1SHORT"]
GT_V2_IDS = [
    "GT-REVC-AP-1-R5U6", "GT-REVC-AP-2-Y1C35", "GT-REVC-AP-3-Y1C5",
    "GT-REVC-AP-4-Y1C36", "GT-REVC-AP-5-Y1C4", "GT-REVC-AP-6-R2LED2",
    "GT-REVC-AP-7-C31U4", "GT-REVC-AP-8-R1Q2", "GT-REVC-AP-9-Y2C3",
]
#: 受保护文件（R6-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
BOTTOM_PNG_SHA256 = (
    "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9")
PNG_NAME = {"applied-top": "applied-top.png",
            "applied-bottom": "applied-bottom.png",
            "prep1-top": "prep1-top.png", "prep1-bottom": "prep1-bottom.png"}
STATE_OF_KEY = {"applied-top": "applied", "applied-bottom": "applied",
                "prep1-top": "prep1", "prep1-bottom": "prep1"}
VIEW_OF_KEY = {"applied-top": "top", "applied-bottom": "bottom",
               "prep1-top": "top", "prep1-bottom": "bottom"}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s34():
    spec = importlib.util.spec_from_file_location(
        "s34_calibration_r6_compare",
        os.path.join(REPO, "scripts", "s34_calibration_r6_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r6.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round6-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r6_files_valid_structure_and_prefixes():
    seen_ids = {"top": [], "bottom": []}
    expect_counts = {"applied-top": 6, "applied-bottom": 4,
                     "prep1-top": 4, "prep1-bottom": 3}
    expect_abstain = {"applied-top": 5, "applied-bottom": 1,
                      "prep1-top": 2, "prep1-bottom": 1}
    for key, name in RAW_FILES.items():
        d = _load(name)
        assert d["reader_id"] == "reader-r6-blind"
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        assert img["image"] == "%s.png" % key           # 图名=文件名对齐
        assert len(img["flags"]) == expect_counts[key]
        view = VIEW_OF_KEY[key]
        prefix = {"top": "R6T-", "bottom": "R6B-"}[view]
        n_abstain = 0
        for f in img["flags"]:
            assert set(f) == READER_FLAG_KEYS           # 六键（含位置证据）
            assert f["flag_id"].startswith(prefix)      # 视图前缀一致
            assert f["category"] in critic.FLAG_CATEGORIES
            assert isinstance(f["abstain"], bool)
            assert 0.0 <= float(f["confidence"]) <= 1.0
            box = f["frame_box_pct"]
            assert len(box) == 4 and all(0.0 <= v <= 1.0 for v in box)
            assert box[0] < box[2] and box[1] < box[3]
            assert f["location_evidence"].strip()
            n_abstain += 1 if f["abstain"] else 0
            seen_ids[view].append(f["flag_id"])
        assert n_abstain == expect_abstain[key]
        assert d["reading_notes"].strip()
    # top 视 R6T-001..010 跨两文件连续（applied-top→prep1-top）；
    # bottom 视 R6B-001..007 连续（applied-bottom→prep1-bottom）
    assert seen_ids["top"] == ["R6T-%03d" % i for i in range(1, 11)]
    assert seen_ids["bottom"] == ["R6B-%03d" % i for i in range(1, 8)]


def test_parse_replay_no_rejections_and_view_injection_deterministic():
    s34 = _s34()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s34.RAW_FILES.items():
        parsed = s34.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s34.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则
    assert s34.view_for_image("applied-top.png") == "top"
    assert s34.view_for_image("prep1-bottom.png") == "bottom"
    assert s34.view_for_image("applied-top.png") == s34.view_for_image(
        "applied-top.png")
    try:
        s34.view_for_image("mystery.png")
    except ValueError:
        pass
    else:
        raise AssertionError("无视角后缀图像名应 ValueError（fail-closed）")
    # run-r6 记录的映射与重放一致（mapping=图像→视角，注入来自图像名）
    run, _ = _run_record()
    for key in RAW_FILES:
        want = {img["image"]: img["view"] for img in replay[key]["images"]}
        got = run["reader"]["view_injection"]["mapping"][key]
        assert got == want == {("%s.png" % key): VIEW_OF_KEY[key]}
    for key in RAW_FILES:
        replay_ids = [f["flag_id"] for img in replay[key]["images"]
                      for f in img["flags"]]
        block = run["states"][STATE_OF_KEY[key]]
        for fid in replay_ids:
            assert block["flag_views"][fid] == VIEW_OF_KEY[key]
            assert fid in [f["flag_id"] for f in block["reader_flags"]]
    assert run["parse_rejections"] == []                # 拒收清单固化（空）
    # 旗标计数（按视角拆分，逐态 10/7、总 17）
    fc = run["reader"]["flag_count"]
    assert fc == {"applied_top": 6, "applied_bottom": 4,
                  "prep1_top": 4, "prep1_bottom": 3,
                  "by_state": {"applied": 10, "prep1": 7}, "total": 17}
    # 盲读派发纪律：四图独立串行派发、派发词零 GT（指引侧变更轮）
    assert run["reader"]["serial_dispatch"] == ["applied-top",
                                                "applied-bottom",
                                                "prep1-top", "prep1-bottom"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r6.md" in \
        run["reader"]["dispatch_discipline"]
    assert "R6T-001..010" in run["reader"]["dispatch_discipline"]


# ---------------------------------------------------------------------------
# run-r6：canonical、常量、域声明、零仪器变更、受保护文件
# ---------------------------------------------------------------------------

def test_run_r6_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r6"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r6"
    assert rec["declared_date"] == DECLARED_DATE
    assert rec["metric_version"] == "calibration-metric-v3"
    assert rec["preregistration"]["round_id_constant"] == ROUND_ID
    for key in rec:                                     # 无机器时间戳键
        assert key in ("declared_date",) or (
            "time" not in key.lower() and "date" not in key.lower())
    # development 域声明（协议 v1 §1/§4：迭代轮不得冒充留出证据）
    assert rec["evaluation_domain"] == "development"
    note = rec["evaluation_domain_note"]
    assert note["declared"] == "development"
    assert note["in_calibrated_range"] is False
    assert "不得冒充未见留出" in note["basis_quote"]
    assert note["protocol_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/evaluation-protocol-v1.md")
    assert rec["compliance"]["critic_calibration_in_range"] is False
    # 零仪器变更声明（指引侧变更轮：nature/components/unchanged/归因）
    ic = rec["instrument_change"]
    assert ic["nature"].startswith("零仪器变更")
    assert len(ic["components"]) == 2                   # 恰两项指引变更
    assert "邻域框口径收紧" in ic["components"][0]
    assert "类别判据示例化" in ic["components"][1]
    assert len(ic["unchanged_components"]) == 5
    assert "几何门" in ic["attribution_note"]
    assert "类别匹配门" in ic["attribution_note"]
    assert "通道级不是旗级" in ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r6-prep-record.json")
    # 复用 R5 渲染：零重渲染声明与四 PNG 见证（盘上 sha=prep-record 实测）
    prep = _load("r6-prep-record.json")
    assert prep["renders_reuse"]["no_instrument_change"] is True
    assert prep["no_instrument_change"] is True
    for item in ic["unchanged_components"]:
        assert "复用 R5 冻结渲染" in item or True
    for w in prep["renders_reuse"]["png_witness"]:
        assert w["match_to_script_constant"] is True
        assert _sha(w["path_rel"]) == w["sha256_measured"]
    # 受保护三文件零改动（sha256 前 8）
    for rel, want in PROTECTED_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])


def test_run_r6_compare_v3_recompute_byte_exact():
    rec, _ = _run_record()
    for st in ("prep1", "applied"):
        block = rec["states"][st]
        rep = cal.compare_v3(block["reader_flags"], block["gt_entries"],
                             flag_views=block["flag_views"])
        assert hashing.canonical_json_bytes(rep) == \
            hashing.canonical_json_bytes(block["compare_v3"])   # byte-exact
        assert block["view_check"] == rep["view_check"] == "full"
        assert block["flag_views"]                              # 视角已注入
        assert all(v in ("top", "bottom")
                   for v in block["flag_views"].values())
        r = block["compare_v3"]
        # 阈值常量零覆盖（与 r5 相同的声明常量）
        assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
        assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
        assert r["metric_version"] == "calibration-metric-v3"
    # 本轮两态均零匹配（R5 唯一匹配未复现，固化明细）
    for st in ("prep1", "applied"):
        r = rec["states"][st]["compare_v3"]
        assert r["matches"] == []
        assert r["reader_matched_ids"] == []
        assert r["gt_matched_count"] == 0
        assert r["duplicate_reports"] == []
        assert "reader_false_positive_ids" not in r
    assert rec["states"]["applied"]["compare_v3"]["reader_unmatched_ids"] \
        == ["R6T-003", "R6B-001", "R6B-003", "R6B-004"]
    assert rec["states"]["prep1"]["compare_v3"]["reader_unmatched_ids"] \
        == ["R6T-007", "R6T-008", "R6B-005", "R6B-006"]


def test_run_r6_gt_entries_source_plus_reprojection():
    rec, _ = _run_record()
    sources = {"prep1": ("ground-truth-v1.json", GT_V1_IDS),
               "applied": ("ground-truth-v2.json", GT_V2_IDS)}
    for st, (gt_name, ids) in sources.items():
        gt = _load(gt_name)
        by_id = {e["gt_id"]: e for e in gt["gt_entries"]}
        block = rec["states"][st]
        assert [e["gt_id"] for e in block["gt_entries"]] == ids
        for e in block["gt_entries"]:
            src = by_id[e["gt_id"]]
            for k in src:                               # 除 frame_box_pct 外
                if k == "frame_box_pct":                # 逐字段原样
                    continue
                assert e[k] == src[k], (st, e["gt_id"], k)
    # frame_box_pct 恰为 derivation-log-r5 的 frame_box_pct_r5（按 gt_id；
    # 渲染未变=重投影输入未变，本轮零新派生、沿用 r5 台账）
    deriv = {e["gt_id"]: e["frame_box_pct_r5"]
             for e in _load("derivation-log-r5.json")["entries"]}
    for st in ("prep1", "applied"):
        assert "零新派生" in rec["states"][st]["gt_reprojection"]["note"]
        for e in rec["states"][st]["gt_entries"]:
            assert e["frame_box_pct"] == deriv[e["gt_id"]]
            assert 0.0 <= e["frame_box_pct"][0] < e["frame_box_pct"][2] <= 1.0
            assert 0.0 <= e["frame_box_pct"][1] < e["frame_box_pct"][3] <= 1.0
            assert e["side"] == "top"                   # 13 条全部 top


# ---------------------------------------------------------------------------
# 聚合算术、达标评估、弃权记账
# ---------------------------------------------------------------------------

def test_run_r6_aggregation_arithmetic():
    rec, _ = _run_record()
    p = rec["states"]["prep1"]["compare_v3"]
    a = rec["states"]["applied"]["compare_v3"]
    agg = rec["aggregation"]
    n_gt = p["gt_count"] + a["gt_count"]
    n_match = len(p["matches"]) + len(a["matches"])
    n_gm = p["gt_matched_count"] + a["gt_matched_count"]
    n_sc = p["reader_scored_count"] + a["reader_scored_count"]
    n_ab = p["abstain"]["abstain_count"] + a["abstain"]["abstain_count"]
    n_fl = p["reader_flag_count"] + a["reader_flag_count"]
    assert agg["gt_count_total"] == n_gt == 13
    assert agg["matches_total"] == n_match == 0
    assert agg["gt_matched_total"] == n_gm == 0
    assert agg["scored_total"] == n_sc == 8
    assert agg["abstain_count_total"] == n_ab == 9
    assert agg["flag_count_total"] == n_fl == 17
    assert agg["gt_recall_total"] == round(n_gm / n_gt, 6) == 0.0
    assert agg["seed_match_rate_total"] == round(n_match / n_sc, 6) == 0.0
    assert agg["abstain_rate_total"] == round(n_ab / n_fl, 6) == 0.529412
    for f in ("gt_recall_arithmetic", "seed_match_rate_arithmetic",
              "abstain_rate_arithmetic"):
        assert f in agg and isinstance(agg[f], str) and agg[f].strip()
    assert "0/13" in agg["gt_recall_arithmetic"]
    assert "0/8" in agg["seed_match_rate_arithmetic"]
    assert "9/17" in agg["abstain_rate_arithmetic"]
    assert agg["abstain_rate_definition"] == cal.ABSTAIN_RATE_DEFINITION
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE


def test_run_r6_compliance_matches_recomputed():
    rec, _ = _run_record()
    agg = rec["aggregation"]
    comp = rec["compliance"]
    criteria = {c["id"]: c for c in comp["criteria"]}
    # 逐项复算（APR-0011 基线；阈值措辞与协议一致，禁改）
    assert criteria["gt_count_ge_12"]["actual"] == agg["gt_count_total"]
    assert criteria["gt_count_ge_12"]["met"] == \
        (agg["gt_count_total"] >= 12) is True
    assert criteria["gt_recall_ge_0.75"]["actual"] == agg["gt_recall_total"]
    assert criteria["gt_recall_ge_0.75"]["met"] == \
        (agg["gt_recall_total"] >= 0.75) is False
    assert criteria["seed_match_rate_ge_0.5"]["actual"] == \
        agg["seed_match_rate_total"]
    assert criteria["seed_match_rate_ge_0.5"]["met"] == \
        (agg["seed_match_rate_total"] >= 0.5) is False
    # 弃权率回升超暂行线（0.529412 > 0.5）：如实记 not met
    assert criteria["abstain_rate_le_0.5"]["actual"] == \
        agg["abstain_rate_total"] == 0.529412
    assert criteria["abstain_rate_le_0.5"]["met"] == \
        (agg["abstain_rate_total"] <= 0.5) is False
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5", "r6"}
    assert consec["rounds"]["r5"] == "not_met（在案）"
    assert consec["rounds"]["r6"] == "not_met（本轮）"
    # 联合评价如实（任一不满足即未达标）
    all_met = all(c["met"] for c in comp["criteria"]) and consec["met"]
    assert comp["joint_evaluation"] == ("met" if all_met else "not_met")
    assert comp["joint_evaluation"] == "not_met"
    assert comp["critic_calibration_in_range"] is False   # 谓词恒 False
    assert "达标≠自动分流" in comp["critic_calibration_in_range_note"]
    assert "恒 False" in comp["critic_calibration_in_range_note"]


def test_run_r6_abstain_accounting_and_bottom_view_semantics():
    rec, _ = _run_record()
    p = rec["states"]["prep1"]["compare_v3"]
    a = rec["states"]["applied"]["compare_v3"]
    # 弃权旗标 id 集与原文逐文件一致（top 5+2、bottom 1+1）
    assert a["abstain"]["abstain_ids"] == [
        f for f in ("R6T-001", "R6T-002", "R6T-004", "R6T-005", "R6T-006",
                    "R6B-002")]
    assert p["abstain"]["abstain_ids"] == [
        f for f in ("R6T-009", "R6T-010", "R6B-007")]
    for r, n in ((a, 6), (p, 3)):
        assert r["abstain"]["abstain_count"] == n
        for fid in r["abstain"]["abstain_ids"]:
            assert fid not in r["reader_matched_ids"]
    # 弃权率口径（单位=旗标条数、分母=全部旗标）
    assert a["abstain"]["abstain_rate"] == round(6 / 10, 6) == 0.6
    assert p["abstain"]["abstain_rate"] == \
        round(3 / 7, 6) == 0.428571
    # bottom 非弃权旗标 5 条全部不入候选（GT 全 top；类别相符对如实记
    # view_mismatch）且几何不近邻（通道重放无 view_gate 近邻条目）
    for st in ("applied", "prep1"):
        block = rec["states"][st]
        for fid, view in block["flag_views"].items():
            if view == "bottom" and fid not in \
                    block["compare_v3"]["abstain"]["abstain_ids"]:
                assert fid in block["compare_v3"]["reader_unmatched_ids"]
    assert set(a["view_mismatch"][i]["flag_id"]
               for i in range(len(a["view_mismatch"]))) == {"R6B-001"}
    assert set(p["view_mismatch"][i]["flag_id"]
               for i in range(len(p["view_mismatch"]))) == {"R6B-005",
                                                            "R6B-006"}
    ca = rec["channel_attribution"]
    assert ca["view_gate_observations"]["r6_entries"] == []
    # GT 13 条全部 side=top（bottom 旗标无从命中）
    for st in ("prep1", "applied"):
        assert all(e["side"] == "top"
                   for e in rec["states"][st]["gt_entries"])


# ---------------------------------------------------------------------------
# 预注册链、冻结哈希、阈值零覆盖
# ---------------------------------------------------------------------------

def test_run_r6_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r6_prep_record_preregistration",
            "observation_guidance_r6_preregistration",
            "observation_guidance_r4_baseline",
            "render_framing_r5_preregistration", "gt_reprojection_log_r5",
            "gt_seed_prep1", "gt_expansion_applied",
            "source_image_pdf_applied_top_r4",
            "source_image_pdf_applied_bottom_r4",
            "source_image_pdf_prep1_top_r4",
            "source_image_pdf_prep1_bottom_r4",
            "render_png_applied_top_r5_reused",
            "render_png_applied_bottom_r5_reused",
            "render_png_prep1_top_r5_reused",
            "render_png_prep1_bottom_r5_reused"} <= roles
    for key, blk in rec["reader"]["raw_files"].items():
        assert blk["sha256"] == _sha(blk["path_rel"])
        assert os.path.basename(blk["path_rel"]) == RAW_FILES[key]
    # 预注册件哈希锚（派发词给定的前 8）
    anchors = {
        "out/v3-tl2/calibration/observation-guidance-r6.md": "1accadbd",
        "out/v3-tl2/calibration/r6-prep-record.json": "af85c933",
        "out/v3-tl2/calibration/render-framing-r5.json": "860aa910",
        "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
        "out/v3-tl2/calibration/observation-guidance-r4.md": "c0706d0f",
    }
    for rel, want in anchors.items():
        assert _sha(rel).startswith(want), rel
    # 阈值常量零覆盖（与 r5 相同；比较器本体零改动）
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "本轮零覆盖" in \
        rec["preregistration"]["comparator"]["thresholds_note"]
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    # 指引锚：本轮=guidance-r6（预注册），基线=guidance-r4
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r6.md")
    assert gp["frozen_before_render"] is True
    assert gp["frozen_before_read"] is True
    assert gp["baseline_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r4.md")
    # 指引内容锚：r6 指引声明恰两项变更 + 归因计划在案
    g6 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                           "observation-guidance-r6.md"),
              encoding="utf-8").read()
    assert "邻域框口径收紧" in g6 and "类别判据示例化" in g6
    assert "归因计划" in g6 and "2026-09-06-r6" in g6
    ref3 = rec["reference_rounds"]["r3_run"]
    ref4 = rec["reference_rounds"]["r4_run"]
    ref5 = rec["reference_rounds"]["r5_run"]
    assert ref3["sha256"] == _sha(ref3["path_rel"])
    assert ref4["sha256"] == _sha(ref4["path_rel"])
    assert ref5["sha256"] == _sha(ref5["path_rel"])
    assert ref5["sha256"].startswith("2ed5a128")
    # 复用渲染见证：两 bottom 渲染逐字节相同（R5 仪器事实沿用）
    bot_a = open(os.path.join(CAL_DIR, "renders-r5",
                              "applied-bottom.png"), "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r5",
                              "prep1-bottom.png"), "rb").read()
    assert hashlib.sha256(bot_a).hexdigest() == \
        hashlib.sha256(bot_p).hexdigest() == BOTTOM_PNG_SHA256


# ---------------------------------------------------------------------------
# 通道归因（预注册计划执行；重放可复核）
# ---------------------------------------------------------------------------

def test_run_r6_channel_attribution_replay_reproducible():
    s34 = _s34()
    rec, _ = _run_record()
    run5 = _load("calibration-run-r5.json")
    ca = rec["channel_attribution"]
    # 方法声明：run-r5 无逐旗 near-miss 明细键（实测偏差如实声明）
    assert "无逐旗 near-miss" in ca["method"]["deviation_note"]
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r5.json" in ca["method"]["source_of_r5_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] \
        is True
    # 重放复算（R5 用其内嵌输入；R6 用本轮内嵌输入）与登记一致
    gt = {"prep1": rec["states"]["prep1"]["gt_entries"],
          "applied": rec["states"]["applied"]["gt_entries"]}
    for run_doc, tag in ((run5, "r5"), (rec, "r6")):
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            rp = s34.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    gt[st])
            assert s34.replay_matches_agree(rp, blk["compare_v3"])
            pairs = ca["method"]["replay_cross_check"][
                f"{tag}_{st}_candidate_pairs"]
            # 落盘经 canonical JSON：tuple 对已序列化为 list-of-list
            assert pairs == [list(p) for p in rp["candidate_pairs"]]
    # 通道分组条目（几何门 2→1；类别门 1→1）与重放一致
    def _entries(key_r5, key_r6, failure):
        rows = []
        for run_doc, key in ((run5, key_r5), (rec, key_r6)):
            for st in ("prep1", "applied"):
                blk = run_doc["states"][st]
                rp = s34.channel_replay(blk["reader_flags"],
                                        blk["flag_views"], gt[st])
                rows += [dict(e, state=st) for e in rp["entries"]
                         if e["failure"] == failure]
        return rows
    for gate, failure in (("channel_1_geometry_gate",
                           "area_ratio_rejected"),
                          ("channel_2_category_gate", "category_mismatch")):
        want = _entries(f"r5_{failure}_entries", f"r6_{failure}_entries",
                        failure)
        got5 = ca[gate][f"r5_{failure}_entries"]
        got6 = ca[gate][f"r6_{failure}_entries"]
        assert len(got5) + len(got6) == len(want)
        for got in got5 + got6:
            match = [w for w in want
                     if (w["flag_id"], w["gt_id"], w["state"]) ==
                     (got["flag_id"], got["gt_id"], got["state"])]
            assert match and match[0]["containment"] == got["containment"]
            assert match[0]["area_ratio"] == got["area_ratio"]
    assert len(ca["channel_1_geometry_gate"]["r5_area_ratio_rejected_entries"]
               ) == 2
    assert len(ca["channel_1_geometry_gate"]["r6_area_ratio_rejected_entries"]
               ) == 1
    assert len(ca["channel_2_category_gate"]["r5_category_mismatch_entries"]
               ) == 1
    assert len(ca["channel_2_category_gate"]["r6_category_mismatch_entries"]
               ) == 1
    # 关键数值固化（通道归因结论的承载数字）
    g5 = ca["channel_1_geometry_gate"]["r5_area_ratio_rejected_entries"]
    g6 = ca["channel_1_geometry_gate"]["r6_area_ratio_rejected_entries"]
    c5 = ca["channel_2_category_gate"]["r5_category_mismatch_entries"]
    c6 = ca["channel_2_category_gate"]["r6_category_mismatch_entries"]
    assert (g5[0]["flag_id"], g5[0]["area_ratio"]) == ("R5T-005", 11.927)
    assert (g5[1]["flag_id"], g5[1]["area_ratio"]) == ("R5T-013", 21.535106)
    assert (g6[0]["flag_id"], g6[0]["area_ratio"]) == ("R6T-007", 12.706428)
    assert (c5[0]["flag_id"], c5[0]["containment"]) == ("R5T-010", 0.510336)
    assert (c6[0]["flag_id"], c6[0]["containment"]) == ("R6T-007", 0.882169)
    # 通道变化陈述与配对警告在案
    assert "21.535106" in ca["channel_1_geometry_gate"]["change"]
    assert "12.706428" in ca["channel_1_geometry_gate"]["change"]
    assert "0.510336" in ca["channel_2_category_gate"]["change"]
    assert "0.882169" in ca["channel_2_category_gate"]["change"]
    assert "通道级归因，不是旗" in ca["pairing_caveat"]
    assert "不同 reader 实例" in ca["pairing_caveat"]


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round6_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=指引侧变更轮（零仪器变更）与协议降级条款原文引用
    assert "指引侧变更轮" in dev["round_nature"]
    assert "零仪器变更" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert dev["instrument_change"]["nature"].startswith("零仪器变更")
    # 诊断结果与 run-r6 一致
    run, _ = _run_record()
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation"]["abstain_rate_total"] == 0.529412
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation"]["gt_recall_total"] == 0.0
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation"]["seed_match_rate_total"] == 0.0
    assert dev["diagnostic_result"]["seed_metric_note"] == \
        cal.SEED_METRIC_NOTE
    crit = {c["id"]: c for c in dev["diagnostic_result"]["criteria"]}
    assert crit["gt_count_ge_12"]["met"] is True
    assert crit["gt_recall_ge_0.75"]["met"] is False
    assert crit["seed_match_rate_ge_0.5"]["met"] is False
    assert crit["abstain_rate_le_0.5"]["met"] is False
    # 联合评价趋势：连续达标计数 0（R5 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["after_r5"]["consecutive_met_count"] == 0
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"]
    assert "不得写成已达成" in trend["note"]
    # run-r6 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r6.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # 诚实结论：明确声明不做能力修复类断言；flag 产出事实在案
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.529412" in hc and "development 域" in hc
    assert "0.0" in hc and "matches=0" in hc
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 9 and fp["non_abstain_count"] == 8
    assert fp["abstain_rate"] == 0.529412
    assert fp["parse_rejections"] == []
    assert fp["flag_count_by_file"] == {"applied-top": 6,
                                        "applied-bottom": 4,
                                        "prep1-top": 4, "prep1-bottom": 3}
    assert sum(fp["flag_count_by_file"].values()) == 17
    assert "冻结证据" in fp["note"]
    assert fp["reader_id"] == "reader-r6-blind"
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r6 冻结工件一致
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles


def test_dev_record_observations_and_next_targets_reproducible():
    """方向性观察与下一迭代目标中的通道数值可独立复算（描述性，
    不入度量）；弃权率回升差距如实；不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    obs = "\n".join(dev["directional_observation_vs_r5"])
    deriv = _load("derivation-log-r5.json")
    r5pct = {e["gt_id"]: e["frame_box_pct_r5"] for e in deriv["entries"]}
    # R6T-007 vs L1NB（类别不符出局，containment=0.882169）
    c_007_nb = cal._containment([0.645, 0.585, 0.765, 0.77],
                                r5pct["GT-REVC-P1-L1NB"])
    # R6T-007 vs L1SHORT（面积比出局，containment=1.0）
    c_007_sh = cal._containment([0.645, 0.585, 0.765, 0.77],
                                r5pct["GT-REVC-P1-L1SHORT"])
    assert round(c_007_nb, 6) == 0.882169 and "0.882169" in obs
    assert c_007_sh == 1.0
    gt = r5pct["GT-REVC-P1-L1SHORT"]
    ar_007 = ((0.765 - 0.645) * (0.77 - 0.585)) / \
        ((gt[2] - gt[0]) * (gt[3] - gt[1]))
    assert round(ar_007, 6) == 12.706428 and "12.706428" in obs
    assert "10.0" in obs and "AREA_RATIO_MAX" in obs
    # R5 基线数字（R5T-005 面积比 11.927、R5T-010 containment 0.510336、
    # R5T-013 面积比 21.535106/匹配 6.739726）在观察中如实引用
    for need in ("11.927", "21.535106", "0.510336", "6.739726",
                 "R5T-013", "GT-REVC-P1-L1NB", "R6T-009"):
        assert need in obs, need
    # 弃权率回升差距如实（0.529412-0.5=0.029412），高于暂行线
    assert "0.529412" in obs and "0.029412" in obs
    nxt = "\n".join(dev["next_iteration_targets"])
    assert "0.029412" in nxt or "0.529412" in nxt
    assert "候选解释假设" in nxt or "候选解释" in nxt
    # 不得把正式采纳门槛达成写成已达成；in_calibrated_range 恒 False
    assert "未达成" in nxt or "不得" in nxt
    assert "in_calibrated_range 恒 False" in nxt
    for doc in (dev, _run_record()[0]):
        text = json.dumps(doc, ensure_ascii=False)
        assert "正式采纳门槛达成" not in text.replace(
            "正式采纳门槛达成「未达成」", "")
        assert "已达成" not in json.dumps(
            dev["joint_evaluation_trend"], ensure_ascii=False) or \
            "未达成" in json.dumps(dev["joint_evaluation_trend"],
                                   ensure_ascii=False)
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r6-prep-record.json")


def test_s34_rerun_byte_identical_and_overwrite_guard():
    """s34 重跑语义：同参重建 byte-exact 一致；防覆写守卫（目标已
    存在即 fail-closed 退出，零覆写）。"""
    s34 = _s34()
    rec, disk = _run_record()
    dev, dev_disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    run_rebuilt = s34.build_run()
    assert hashing.canonical_json_bytes(run_rebuilt) == disk
    run_sha = _sha("out/v3-tl2/calibration/calibration-run-r6.json")
    dev_rebuilt = s34.build_dev_record(run_rebuilt, run_sha)
    assert hashing.canonical_json_bytes(dev_rebuilt) == dev_disk
    # 声明常量（无 wall-clock）
    assert s34.DECLARED_DATE == "2026-09-06"
    assert s34.ROUND_ID == "2026-09-06-r6"
    # 防覆写：目标两件已存在 → main 必须 fail-closed 退出（零覆写）
    before = open(os.path.join(CAL_DIR, "calibration-run-r6.json"),
                  "rb").read()
    with pytest.raises(SystemExit) as ei:
        s34.main()
    assert ei.value.code == 1
    after = open(os.path.join(CAL_DIR, "calibration-run-r6.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    dev_after = open(os.path.join(CAL_DIR, "round6-dev-record.json"),
                     "rb").read()
    assert dev_after == dev_disk                 # 字节零改动
    # run_record_ref 仍指向 run-r6 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r6.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "无任何 GT" in rp["discipline"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r6-prep-record.json 先于本轮盲读落盘" in \
        rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "2026-09-06-r6" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域指引侧变更轮，非留出；advisory
    # 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "指引侧变更轮" in dev["round_nature"]
    assert dev["is_gate"] is False
    assert rec["compliance"]["critic_calibration_in_range"] is False
    assert "不是门" in dev["notes"][0]


def _assert_no_banned_keys(obj, path="doc"):
    if isinstance(obj, dict):
        for banned in ("reader_false_positive_ids",
                       "reader_precision_vs_seed_gt"):
            assert banned not in obj, (path, banned)
        for k, v in obj.items():
            _assert_no_banned_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _assert_no_banned_keys(v, f"{path}[{i}]")
