"""R7 执行包测试：reader 判读迭代第七轮收口（CAL-R7-CLOSE）——
盲读解析与视角注入 + 双态 compare_v3 重投影比对 + 分视角弃权分层 +
预注册假设 (a) 裁决（聚合判据执行）+ 逐旗失败通道归因（vs R6）+
development 域记录。

结构照 test_r6_calibration_round6.py 先例，仅输入与轮次常量不同
（R7=development 域单变量指引侧变更轮：零仪器变更、复用 R5 冻结渲染
件；唯一变更=判读指引 §4 弃权适用性再校准，预注册于 r7-prep-record.
json / observation-guidance-r7.md；检验 R6 预注册候选假设 (a)）。

覆盖：
- 盲读原文（reader-raw-r7-{applied,prep1}-{top,bottom}.txt，冻结证据）：
  合法 JSON、结构（reader_id/per_image/reading_notes；flag 六键含
  location_evidence）、视角前缀一致（R7T-001..013 top 跨两文件连续、
  R7B-001..012 bottom 跨两文件连续）、拒收清单固化（全 25 旗标过
  calibration fail-closed 校验，0 拒收）、哈希与 run-r7 登记一致；
- 视角注入确定性：s36 的图像名→视角映射纯函数两次调用一致，
  run-r7 记录的 flag_views 与该规则逐旗标一致；两波并行派发记录
  （波 1=applied-top∥applied-bottom；波 2=prep1-top∥prep1-bottom；
  视角内 applied→prep1 串行顺序保持）与分视角旗标/弃权计数；
- calibration-run-r7.json：盘上 canonical byte 一致；两态 compare_v3
  用记录内嵌输入（reader_flags/gt_entries/flag_views）重算 byte-exact
  一致且 view_check=full；内嵌 gt_entries=源 GT 文件条目（frame_box_pct
  ←derivation-log-r5 的 frame_box_pct_r5——渲染未变零新派生，其余
  字段逐字段原样）；聚合算术显式复算一致（0/13、0/10、15/25=0.6）；
  分视角弃权率 top 3/13=0.230769、bottom 12/12=1.0、分态
  applied 7/13=0.538462、prep1 8/12=0.666667；达标评估逐项复算一致
  （APR-0011，弃权率 0.6>0.5 not met）、joint=not_met、连续达标计数
  0→0、critic_calibration_in_range=False、域=development；
- 预注册假设 (a) 裁决：判据引用=r7-prep-record.json hypothesis_test
  原文（support/reject 原样）；聚合弃权率 0.529412→0.6 未回落⇒
  verdict=not_supported（判据复算一致）；守门通道观察不影响裁决；
  分层观察（top 回落/bottom 全弃权）如实附录且带混杂声明
  （跨轮 reader 实例不同、n=1、不构成已证因果关系）与聚合优先声明；
- 通道归因（channel_attribution）：对 run-r6 内嵌输入与 run-r7 内嵌
  输入重放通道分类与登记一致；重放 candidate 对与两轮 compare_v3
  matches∪duplicate_reports 对拍（R6 geo=1/cat=1 → R7 geo=0/cat=0，
  零近邻对）；跨轮 flag_id 非同旗配对声明在案；R7 特有观察
  （R7T-012↔R6T-009 同区域弃权、suspicious_reroute 非弃权首现 3 条、
  R7T-005 弃权框双条件数值）可独立复算；
- 预注册链：r7-prep-record/guidance-r7/guidance-r6（基线）/framing-r5/
  derivation-log-r5/GT/协议/复用 PNG/冻结 PDF sha 与盘上一致
  （锚 9e7a7b13/e48c37fe/1accadbd/860aa910/62343380）；阈值常量零覆盖
  （containment 0.5 / area_ratio_max 10.0 与 r6 相同）；
- round7-dev-record.json：域声明、单变量指引侧变更轮性质、假设 (a)
  裁决节与 run-r7 一致、R6→R7 方向性观察（无能力断言、通道数值可
  独立复算）、联合评价趋势（连续计数 0→0，正式采纳门槛未达成）、
  run-r7 sha 引用一致、is_gate=False、in_calibrated_range 恒 False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；受保护三文件 sha256 前 8 断言；
- s36 重跑：同参重建 byte-exact 一致 + 防覆写守卫（目标已存在即
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

ROUND_ID = "2026-09-06-r7"
DECLARED_DATE = "2026-09-06"
RAW_FILES = {
    "applied-top": "reader-raw-r7-applied-top.txt",
    "applied-bottom": "reader-raw-r7-applied-bottom.txt",
    "prep1-top": "reader-raw-r7-prep1-top.txt",
    "prep1-bottom": "reader-raw-r7-prep1-bottom.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top": "96a906a6", "applied-bottom": "fa23aa51",
    "prep1-top": "e6164449", "prep1-bottom": "bb54cefe",
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
#: 受保护文件（R7-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: 预注册件哈希锚（派发词给定的前 8）
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r7.md": "9e7a7b13",
    "out/v3-tl2/calibration/r7-prep-record.json": "e48c37fe",
    "out/v3-tl2/calibration/observation-guidance-r6.md": "1accadbd",
    "out/v3-tl2/calibration/render-framing-r5.json": "860aa910",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
}
BOTTOM_PNG_SHA256 = (
    "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9")
STATE_OF_KEY = {"applied-top": "applied", "applied-bottom": "applied",
                "prep1-top": "prep1", "prep1-bottom": "prep1"}
VIEW_OF_KEY = {"applied-top": "top", "applied-bottom": "bottom",
               "prep1-top": "top", "prep1-bottom": "bottom"}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s36():
    spec = importlib.util.spec_from_file_location(
        "s36_calibration_r7_compare",
        os.path.join(REPO, "scripts", "s36_calibration_r7_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r7.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round7-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r7_files_valid_structure_and_prefixes():
    seen_ids = {"top": [], "bottom": []}
    expect_counts = {"applied-top": 7, "applied-bottom": 6,
                     "prep1-top": 6, "prep1-bottom": 6}
    expect_abstain = {"applied-top": 1, "applied-bottom": 6,
                      "prep1-top": 2, "prep1-bottom": 6}
    for key, name in RAW_FILES.items():
        assert _sha("out/v3-tl2/calibration/" + name).startswith(
            RAW_SHA256_FIRST8[key])                  # 与派发哈希锚一致
        d = _load(name)
        assert d["reader_id"] == "reader-r7-blind"
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        assert img["image"] == "%s.png" % key           # 图名=文件名对齐
        assert len(img["flags"]) == expect_counts[key]
        view = VIEW_OF_KEY[key]
        prefix = {"top": "R7T-", "bottom": "R7B-"}[view]
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
    # top 视 R7T-001..013 跨两文件连续（applied-top 001..007→prep1-top
    # 008..013）；bottom 视 R7B-001..012 连续（001..006→007..012）
    assert seen_ids["top"] == ["R7T-%03d" % i for i in range(1, 14)]
    assert seen_ids["bottom"] == ["R7B-%03d" % i for i in range(1, 13)]


def test_parse_replay_no_rejections_view_injection_and_parallel_dispatch():
    s36 = _s36()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s36.RAW_FILES.items():
        parsed = s36.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s36.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则
    assert s36.view_for_image("applied-top.png") == "top"
    assert s36.view_for_image("prep1-bottom.png") == "bottom"
    assert s36.view_for_image("applied-top.png") == s36.view_for_image(
        "applied-top.png")
    try:
        s36.view_for_image("mystery.png")
    except ValueError:
        pass
    else:
        raise AssertionError("无视角后缀图像名应 ValueError（fail-closed）")
    run, _ = _run_record()
    for key in RAW_FILES:
        want = {img["image"]: img["view"] for img in replay[key]["images"]}
        got = run["reader"]["view_injection"]["mapping"][key]
        assert got == want == {("%s.png" % key): VIEW_OF_KEY[key]}
        replay_ids = [f["flag_id"] for img in replay[key]["images"]
                      for f in img["flags"]]
        block = run["states"][STATE_OF_KEY[key]]
        for fid in replay_ids:
            assert block["flag_views"][fid] == VIEW_OF_KEY[key]
            assert fid in [f["flag_id"] for f in block["reader_flags"]]
    assert run["parse_rejections"] == []                # 拒收清单固化（空）
    # 旗标计数（按 image / by_state / by_view 分层；总 25）
    fc = run["reader"]["flag_count"]
    assert fc == {"applied_top": 7, "applied_bottom": 6,
                  "prep1_top": 6, "prep1_bottom": 6,
                  "by_state": {"applied": 13, "prep1": 12},
                  "by_view": {"top": 13, "bottom": 12},
                  "abstain_by_view": {"top": 3, "bottom": 12},
                  "total": 25}
    # 两波并行派发记录（与 R6 全串行不同，如实记录）+ 零 GT 派发词
    pd = run["reader"]["parallel_dispatch"]
    assert pd["mode"] == "two_wave_parallel"
    assert pd["wave_1_parallel"] == ["applied-top", "applied-bottom"]
    assert pd["wave_2_parallel"] == ["prep1-top", "prep1-bottom"]
    assert pd["within_view_serial_order"] == {
        "top": ["applied-top", "prep1-top"],
        "bottom": ["applied-bottom", "prep1-bottom"]}
    assert "R6=四图独立全串行" in pd["diff_note"]
    assert "两波并行" in run["reader"]["dispatch_discipline"]
    assert "R7T-001..013" in run["reader"]["dispatch_discipline"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r7.md" in \
        run["reader"]["dispatch_discipline"]


# ---------------------------------------------------------------------------
# run-r7：canonical、常量、域声明、零仪器变更、受保护文件
# ---------------------------------------------------------------------------

def test_run_r7_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r7"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r7"
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
    # 零仪器变更声明（单变量指引侧变更轮：nature/components/unchanged）
    ic = rec["instrument_change"]
    assert ic["nature"].startswith("零仪器变更")
    assert len(ic["components"]) == 1                   # 恰一项 §4 变更
    assert "弃权适用性再校准" in ic["components"][0]
    # unchanged 与 r7-prep-record.json 登记逐字一致（锚 e48c37fe）
    prep = _load("r7-prep-record.json")
    assert ic["unchanged_components"] == prep["unchanged_components"]
    assert prep["no_instrument_change"] is True
    assert prep["renders_reuse"]["no_instrument_change"] is True
    assert "弃权率" in ic["attribution_note"]
    assert "几何门" in ic["attribution_note"]
    assert "通道级不是旗级" in ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r7-prep-record.json")
    # 复用 R5 渲染：零重渲染声明与四 PNG 见证（盘上 sha=prep-record 实测）
    for w in prep["renders_reuse"]["png_witness"]:
        assert w["match_to_witness_constant"] is True
        assert _sha(w["path_rel"]) == w["sha256_measured"]
    # 受保护三文件零改动（sha256 前 8）
    for rel, want in PROTECTED_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])


def test_run_r7_compare_v3_recompute_byte_exact():
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
        # 阈值常量零覆盖（与 r6 相同的声明常量）
        assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
        assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
        assert r["metric_version"] == "calibration-metric-v3"
    # 本轮两态均零匹配（连续第二轮 matches 为空，固化明细）
    for st in ("prep1", "applied"):
        r = rec["states"][st]["compare_v3"]
        assert r["matches"] == []
        assert r["reader_matched_ids"] == []
        assert r["gt_matched_count"] == 0
        assert r["duplicate_reports"] == []
        assert "reader_false_positive_ids" not in r
    assert rec["states"]["applied"]["compare_v3"]["reader_unmatched_ids"] \
        == ["R7T-001", "R7T-002", "R7T-003", "R7T-004", "R7T-006",
            "R7T-007"]
    assert rec["states"]["prep1"]["compare_v3"]["reader_unmatched_ids"] \
        == ["R7T-008", "R7T-009", "R7T-010", "R7T-011"]


def test_run_r7_gt_entries_source_plus_reprojection():
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
# 聚合算术、分视角分层、达标评估
# ---------------------------------------------------------------------------

def test_run_r7_aggregation_and_stratified_abstain():
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
    assert agg["scored_total"] == n_sc == 10
    assert agg["abstain_count_total"] == n_ab == 15
    assert agg["flag_count_total"] == n_fl == 25
    assert agg["gt_recall_total"] == round(n_gm / n_gt, 6) == 0.0
    assert agg["seed_match_rate_total"] == round(n_match / n_sc, 6) == 0.0
    assert agg["abstain_rate_total"] == round(n_ab / n_fl, 6) == 0.6
    for f in ("gt_recall_arithmetic", "seed_match_rate_arithmetic",
              "abstain_rate_arithmetic"):
        assert f in agg and isinstance(agg[f], str) and agg[f].strip()
    assert "0/13" in agg["gt_recall_arithmetic"]
    assert "0/10" in agg["seed_match_rate_arithmetic"]
    assert "15/25" in agg["abstain_rate_arithmetic"]
    assert agg["abstain_rate_definition"] == cal.ABSTAIN_RATE_DEFINITION
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE
    # 分态弃权率（applied 7/13、prep1 8/12）
    bvs = agg["abstain_rate_by_state"]
    assert bvs["applied"] == round(7 / 13, 6) == 0.538462
    assert bvs["applied_fraction"] == "7/13"
    assert bvs["prep1"] == round(8 / 12, 6) == 0.666667
    assert bvs["prep1_fraction"] == "8/12"
    # 分视角弃权率（top 3/13、bottom 12/12；分层记账如实单列）
    bvv = agg["abstain_rate_by_view"]
    assert bvv["top"] == round(3 / 13, 6) == 0.230769
    assert bvv["top_fraction"] == "3/13"
    assert bvv["bottom"] == round(12 / 12, 6) == 1.0
    assert bvv["bottom_fraction"] == "12/12"
    assert "3/13" in agg["abstain_rate_by_view_arithmetic"]
    assert "12/12" in agg["abstain_rate_by_view_arithmetic"]


def test_run_r7_compliance_matches_recomputed():
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
    # 弃权率高于暂行线（0.6 > 0.5）：如实记 not met
    assert criteria["abstain_rate_le_0.5"]["actual"] == \
        agg["abstain_rate_total"] == 0.6
    assert criteria["abstain_rate_le_0.5"]["met"] == \
        (agg["abstain_rate_total"] <= 0.5) is False
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5", "r6",
                                     "r7"}
    assert consec["rounds"]["r6"] == "not_met（在案）"
    assert consec["rounds"]["r7"] == "not_met（本轮）"
    # 联合评价如实（任一不满足即未达标）
    all_met = all(c["met"] for c in comp["criteria"]) and consec["met"]
    assert comp["joint_evaluation"] == ("met" if all_met else "not_met")
    assert comp["joint_evaluation"] == "not_met"
    assert comp["critic_calibration_in_range"] is False   # 谓词恒 False
    assert "达标≠自动分流" in comp["critic_calibration_in_range_note"]
    assert "恒 False" in comp["critic_calibration_in_range_note"]


# ---------------------------------------------------------------------------
# 预注册假设 (a) 裁决（判据引用 + 聚合裁决 + 分层观察）
# ---------------------------------------------------------------------------

def test_run_r7_hypothesis_a_verdict_preregistered():
    rec, _ = _run_record()
    prep = _load("r7-prep-record.json")
    ht = rec["hypothesis_test"]
    assert ht["kind"] == "preregistered_hypothesis_test"
    assert ht["hypothesis_id"] == "r6-dev-record-candidate-a"
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r7-prep-record.json")
    # 判据引用=r7-prep-record.json hypothesis_test 原文（逐字一致）
    want = {k: prep["hypothesis_test"][k]
            for k in ("hypothesis", "support_condition", "reject_condition",
                      "test_design", "null_result_note")}
    assert ht["preregistered_criteria_quote"] == want
    assert "不获支持" in want["reject_condition"]
    # 实测：聚合弃权率 0.529412（R6）→0.6（R7），未回落
    m = ht["measurement"]
    assert m["abstain_rate_r6"] == 0.529412
    assert m["abstain_r6_fraction"] == "9/17"
    assert m["abstain_rate_r7"] == 0.6
    assert m["abstain_r7_fraction"] == "15/25"
    assert m["abstain_rate_fell"] is (0.6 < 0.529412) is False
    assert m["abstain_rate_delta"] == round(0.6 - 0.529412, 6)
    # 守门通道观察在案且不影响裁决（主通道判据单独决定）
    g = m["guard_channel"]
    assert g["guard_ok"] is True
    assert "不改变裁决" in g["note"]
    # 聚合裁决=不获支持（预注册判据复算一致）
    assert ht["verdict"] == "not_supported"
    assert "reject_condition" in ht["verdict_rule"] or \
        "不降" in ht["verdict_rule"]
    assert "不获支持" in ht["verdict_text"]
    assert "reject_condition 命中" in ht["verdict_text"]
    # 分层观察如实附录（top 回落 / bottom 全弃权反向）+ 混杂与优先声明
    st = ht["stratified_observation"]
    assert st["top"]["r6_rate"] == 0.7 and st["top"]["r6_fraction"] == "7/10"
    assert st["top"]["r7_rate"] == 0.230769
    assert st["top"]["r7_fraction"] == "3/13"
    assert "相容" in st["top"]["direction"]
    assert st["bottom"]["r6_rate"] == 0.285714
    assert st["bottom"]["r6_fraction"] == "2/7"
    assert st["bottom"]["r7_rate"] == 1.0
    assert st["bottom"]["r7_fraction"] == "12/12"
    assert "反向" in st["bottom"]["direction"]
    assert "热隔离盘" in st["bottom_interpretation"]
    assert "跨轮 reader 实例不同=混杂因素" in st["confounder_note"]
    assert "n=1 无统计效力" in st["confounder_note"]
    assert "不得凌驾聚合裁决" in st["precedence_note"]
    assert "已证因果关系" in st["precedence_note"] or \
        "不构成已证因果关系" in ht["verdict_text"]


# ---------------------------------------------------------------------------
# 通道归因（vs R6；重放可复核）
# ---------------------------------------------------------------------------

def test_run_r7_channel_attribution_replay_reproducible():
    s36 = _s36()
    rec, _ = _run_record()
    run6 = _load("calibration-run-r6.json")
    run5 = _load("calibration-run-r5.json")
    ca = rec["channel_attribution"]
    # 方法声明：照抄 run-r6 重放口径（同源几何原语）
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r6.json" in ca["method"]["source_of_r6_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] \
        is True
    # 重放复算（R6/R7 均用内嵌输入）与登记一致 + 对拍 compare_v3
    gt = {"prep1": rec["states"]["prep1"]["gt_entries"],
          "applied": rec["states"]["applied"]["gt_entries"]}
    for run_doc, tag in ((run6, "r6"), (rec, "r7")):
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            rp = s36.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    gt[st])
            assert s36.replay_matches_agree(rp, blk["compare_v3"])
            pairs = ca["method"]["replay_cross_check"][
                f"{tag}_{st}_candidate_pairs"]
            assert pairs == [list(p) for p in rp["candidate_pairs"]] == []
    # 通道分组条目（几何门 R6 1→R7 0；类别门 R6 1→R7 0）与重放一致
    def _entries(run_doc, failure):
        rows = []
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            rp = s36.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    gt[st])
            rows += [dict(e, state=st) for e in rp["entries"]
                     if e["failure"] == failure]
        return rows
    for gate, failure in (("channel_1_geometry_gate",
                           "area_ratio_rejected"),
                          ("channel_2_category_gate", "category_mismatch")):
        got6 = ca[gate][f"r6_{failure}_entries"]
        got7 = ca[gate][f"r7_{failure}_entries"]
        want6 = _entries(run6, failure)
        want7 = _entries(rec, failure)
        assert [(e["flag_id"], e["gt_id"], e["containment"],
                 e["area_ratio"]) for e in got6] == \
            [(e["flag_id"], e["gt_id"], e["containment"],
              e["area_ratio"]) for e in want6]
        assert got7 == want7 == []
    g6 = ca["channel_1_geometry_gate"]["r6_area_ratio_rejected_entries"]
    c6 = ca["channel_2_category_gate"]["r6_category_mismatch_entries"]
    assert (g6[0]["flag_id"], g6[0]["area_ratio"]) == ("R6T-007", 12.706428)
    assert (c6[0]["flag_id"], c6[0]["containment"]) == ("R6T-007", 0.882169)
    assert "12.706428" in ca["channel_1_geometry_gate"]["change"]
    assert "0.882169" in ca["channel_2_category_gate"]["change"]
    assert "通道级归因，不是旗" in ca["pairing_caveat"]
    assert "不同 reader 实例" in ca["pairing_caveat"]
    # 视角门：两轮均空（R7 bottom 12/12 全弃权、无非弃权样本）
    assert ca["view_gate_observations"]["r6_entries"] == []
    assert ca["view_gate_observations"]["r7_entries"] == []
    assert "12/12" in ca["view_gate_observations"]["note"]
    # R7 特有观察：R7T-012↔R6T-009 同区域弃权 + reroute 首现 + R7T-005
    spec = "\n".join(ca["r7_specific_observations"])
    assert "R7T-012" in spec and "R6T-009" in spec
    assert "0.839393" in spec and "0.415663" in spec
    assert "suspicious_reroute" in spec and "R7T-002" in spec
    assert "3.537565" in spec and "R7T-005" in spec
    # reroute 声明独立复算：R5/R6 非弃权类别无 reroute、R7 恰 3 条
    def _nonabstain_cats(run_doc):
        cats = set()
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
            cats |= {f["category"] for f in blk["reader_flags"]
                     if f["flag_id"] not in abst}
        return cats
    assert "suspicious_reroute" not in _nonabstain_cats(run5)
    assert "suspicious_reroute" not in _nonabstain_cats(run6)
    r7_reroute = [f["flag_id"] for st in ("prep1", "applied")
                  for f in rec["states"][st]["reader_flags"]
                  if f["category"] == "suspicious_reroute" and not f["abstain"]]
    assert sorted(r7_reroute) == ["R7T-002", "R7T-004", "R7T-009"]


# ---------------------------------------------------------------------------
# 预注册链、冻结哈希、阈值零覆盖
# ---------------------------------------------------------------------------

def test_run_r7_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r7_prep_record_preregistration",
            "observation_guidance_r7_preregistration",
            "observation_guidance_r6_baseline",
            "render_framing_r5_preregistration", "gt_reprojection_log_r5",
            "gt_seed_prep1", "gt_expansion_applied",
            "r6_prep_record_witness_source",
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
        assert blk["sha256"].startswith(RAW_SHA256_FIRST8[key])
        assert os.path.basename(blk["path_rel"]) == RAW_FILES[key]
    # 预注册件哈希锚（派发词给定的前 8）
    for rel, want in PREREG_ANCHORS.items():
        assert _sha(rel).startswith(want), rel
    # 阈值常量零覆盖（与 r6 相同；比较器本体零改动）
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "本轮零覆盖" in \
        rec["preregistration"]["comparator"]["thresholds_note"]
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    # 指引锚：本轮=guidance-r7（预注册），基线=guidance-r6
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r7.md")
    assert gp["frozen_before_render"] is True
    assert gp["frozen_before_read"] is True
    assert gp["baseline_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r6.md")
    assert "弃权适用性再校准" in gp["change_note"]
    # 指引内容锚：r7 指引声明恰一项变更 + 归因计划（假设检验声明）在案
    g7 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                           "observation-guidance-r7.md"),
              encoding="utf-8").read()
    assert "弃权适用性再校准" in g7 and "归因计划" in g7
    assert "2026-09-06-r7" in g7 and "非判据放宽" in g7
    # 参照轮哈希在案（r6=上一轮基线）
    ref6 = rec["reference_rounds"]["r6_run"]
    assert ref6["sha256"] == _sha(ref6["path_rel"])
    assert ref6["sha256"].startswith("6e6ffdf7")
    ref5 = rec["reference_rounds"]["r5_run"]
    assert ref5["sha256"].startswith("2ed5a128")
    # 复用渲染见证：两 bottom 渲染逐字节相同（R5 仪器事实沿用）
    bot_a = open(os.path.join(CAL_DIR, "renders-r5",
                              "applied-bottom.png"), "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r5",
                              "prep1-bottom.png"), "rb").read()
    assert hashlib.sha256(bot_a).hexdigest() == \
        hashlib.sha256(bot_p).hexdigest() == BOTTOM_PNG_SHA256


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round7_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=单变量指引侧变更轮（零仪器变更）与协议降级条款原文引用
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert "零仪器变更" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert dev["instrument_change"]["nature"].startswith("零仪器变更")
    # 诊断结果与 run-r7 一致
    run, _ = _run_record()
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation"]["abstain_rate_total"] == 0.6
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
    # 假设 (a) 裁决节与 run-r7 一致
    assert dev["hypothesis_test_a"] == run["hypothesis_test"]
    assert dev["hypothesis_test_a"]["verdict"] == "not_supported"
    # 联合评价趋势：连续达标计数 0（R6 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["after_r6"]["consecutive_met_count"] == 0
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"]
    assert "不得写成已达成" in trend["note"]
    # run-r7 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r7.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # 诚实结论：明确声明不做能力修复类断言；flag 产出事实在案
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.6" in hc and "development 域" in hc
    assert "0.0" in hc and "matches=0" in hc
    assert "不获支持" in hc and "混杂" in hc
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 15 and fp["non_abstain_count"] == 10
    assert fp["abstain_rate"] == 0.6
    assert fp["abstain_rate_by_view"]["top"] == 0.230769
    assert fp["abstain_rate_by_view"]["top_fraction"] == "3/13"
    assert fp["abstain_rate_by_view"]["bottom"] == 1.0
    assert fp["abstain_rate_by_view"]["bottom_fraction"] == "12/12"
    assert fp["parse_rejections"] == []
    assert fp["flag_count_by_file"] == {"applied-top": 7,
                                        "applied-bottom": 6,
                                        "prep1-top": 6, "prep1-bottom": 6}
    assert sum(fp["flag_count_by_file"].values()) == 25
    assert "冻结证据" in fp["note"]
    assert "两波并行" in fp["note"]
    assert fp["reader_id"] == "reader-r7-blind"
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r7 冻结工件一致
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles


def test_dev_record_observations_and_next_targets_reproducible():
    """方向性观察与下一迭代目标中的通道数值可独立复算（描述性，
    不入度量）；假设 (a) 分层数字如实；不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    run, _ = _run_record()
    run6 = _load("calibration-run-r6.json")
    obs = "\n".join(dev["directional_observation_vs_r6"])
    deriv = {e["gt_id"]: e["frame_box_pct_r5"]
             for e in _load("derivation-log-r5.json")["entries"]}
    nb = deriv["GT-REVC-P1-L1NB"]
    # R7T-005 弃权框 vs GT-REVC-AP-2-Y1C35（双条件数值复算）
    blk = run["states"]["applied"]
    f005 = next(f for f in blk["reader_flags"]
                if f["flag_id"] == "R7T-005")
    g = next(e for e in blk["gt_entries"]
             if e["gt_id"] == "GT-REVC-AP-2-Y1C35")
    assert round(cal._containment(f005["frame_box_pct"],
                                  g["frame_box_pct"]), 6) == 1.0
    assert round(cal._area_ratio(f005["frame_box_pct"],
                                 g["frame_box_pct"]), 6) == 3.537565
    assert "3.537565" in obs
    # R7T-012（R7）与 R6T-009（R6）对 L1NB 的 containment 复算
    f012 = next(f for f in run["states"]["prep1"]["reader_flags"]
                if f["flag_id"] == "R7T-012")
    f009 = next(f for f in run6["states"]["prep1"]["reader_flags"]
                if f["flag_id"] == "R6T-009")
    assert round(cal._containment(f012["frame_box_pct"], nb), 6) == 0.415663
    assert round(cal._containment(f009["frame_box_pct"], nb), 6) == 0.839393
    assert "0.415663" in obs and "0.839393" in obs
    # R6 通道基线数字与分层/聚合数字在观察中如实引用
    for need in ("12.706428", "0.882169", "0.529412", "0.230769",
                 "0.538462", "0.666667", "12/12", "suspicious_reroute"):
        assert need in obs, need
    nxt = "\n".join(dev["next_iteration_targets"])
    # bottom 存在性歧义专题处置=协议/GT 侧候选（须预注册+人工批准）
    assert "bottom" in nxt and "热隔离盘" in nxt
    assert "预注册+人工批准" in nxt
    # reroute 非弃权旗几何近邻性观察在候选目标中
    assert "suspicious_reroute" in nxt and "GT 扩充" in nxt
    # L1NB 邻域连续两轮弃权观察在候选目标中
    assert "L1NB" in nxt and "0.839393" in nxt and "0.415663" in nxt
    # 不得把正式采纳门槛达成写成已达成；in_calibrated_range 恒 False
    assert "in_calibrated_range 恒 False" in nxt
    assert "不得" in nxt
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r7-prep-record.json")


def test_s36_rerun_byte_identical_and_overwrite_guard():
    """s36 重跑语义：同参重建 byte-exact 一致；防覆写守卫（目标已
    存在即 fail-closed 退出，零覆写）。"""
    s36 = _s36()
    rec, disk = _run_record()
    dev, dev_disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    run_rebuilt = s36.build_run()
    assert hashing.canonical_json_bytes(run_rebuilt) == disk
    run_sha = _sha("out/v3-tl2/calibration/calibration-run-r7.json")
    dev_rebuilt = s36.build_dev_record(run_rebuilt, run_sha)
    assert hashing.canonical_json_bytes(dev_rebuilt) == dev_disk
    # 声明常量（无 wall-clock）
    assert s36.DECLARED_DATE == "2026-09-06"
    assert s36.ROUND_ID == "2026-09-06-r7"
    # 防覆写：目标两件已存在 → main 必须 fail-closed 退出（零覆写）
    before = open(os.path.join(CAL_DIR, "calibration-run-r7.json"),
                  "rb").read()
    with pytest.raises(SystemExit) as ei:
        s36.main()
    assert ei.value.code == 1
    after = open(os.path.join(CAL_DIR, "calibration-run-r7.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    dev_after = open(os.path.join(CAL_DIR, "round7-dev-record.json"),
                     "rb").read()
    assert dev_after == dev_disk                 # 字节零改动
    # run_record_ref 仍指向 run-r7 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r7.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "弃权适用侧" in rp["abstain_semantics"]
    assert "无任何 GT" in rp["discipline"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r7-prep-record.json 先于本轮盲读落盘" in \
        rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "2026-09-06-r7" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域单变量指引侧变更轮，非留出；
    # advisory 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "单变量指引侧变更轮" in dev["round_nature"]
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
