"""R5 执行包测试：reader 判读迭代第五轮收口（CAL-R5-CLOSE）——
盲读解析与视角注入 + 双态 compare_v3 重投影比对 + development 域记录。

结构照 test_r4_calibration_round4.py 先例，仅输入与轮次常量不同
（R5=development 域单变量仪器迭代轮：有效分辨率 dpi 320→640+裁剪
板界+白边 120px；矢量内容/图层/判读指引与 R4 一致）。

覆盖：
- 盲读原文（reader-raw-r5-{applied,prep1}-{top,bottom}.txt，冻结证据）：
  合法 JSON、结构（reader_id/per_image/reading_notes；flag 六键含
  location_evidence）、视角前缀一致（R5T-001..017 top 跨两文件连续、
  R5B-001..002）、拒收清单固化（全 19 旗标过 calibration fail-closed
  校验，0 拒收）；
- 视角注入确定性：s31 的图像名→视角映射纯函数两次调用一致，
  run-r5 记录的 flag_views 与该规则逐旗标一致；
- calibration-run-r5.json：盘上 canonical byte 一致；两态 compare_v3
  用记录内嵌输入（reader_flags/gt_entries/flag_views）重算 byte-exact
  一致且 view_check=full；内嵌 gt_entries=源 GT 文件条目（frame_box_pct
  ←derivation-log-r5 的 frame_box_pct_r5，其余字段逐字段原样）；
  聚合算术显式复算一致；达标评估逐项复算一致（APR-0011）、
  joint=not_met、critic_calibration_in_range=False、域=development；
  弃权记账（bottom 2 旗标全弃权单列）；
- derivation-log-r5.json：13 条 board_box_mm_verbatim 与 GT 文件逐字段
  float 相等；frame_box_pct_r5 全链纯函数重算一致（板 Edge.Cuts bbox +
  renders-r5 PNG 实测像素界 + box_mm_to_frame_pct，top 同向；像素界
  与台账 conversion_base.px_bounds_by_state_side 逐字段相等）；
- 预注册链：framing-r5 引用的 guidance/protocol/r4 PDF/r4 PNG sha 与
  盘上一致；framing-r5/derivation-log-r5 互相锚定 sha 一致；单变量
  仪器变更声明在案；framing 声明 evaluation_split.declared=development；
- 两 bottom 渲染逐字节相同（仪器事实）+ 13 条 GT 全部 side=top；
- round5-dev-record.json：域声明、单变量轮性质、R4→R5 方向性观察
  （无能力断言、位置对照 containment 值可独立复算）、run-r5 sha 引用
  一致、is_gate=False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；受保护三文件 sha256 前 8 断言。

只读 out/（生成器模式）：零子进程/零写盘/零网络。
"""

import hashlib
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import calibration as cal           # noqa: E402
from pcbflow import critic                       # noqa: E402
from pcbflow import hashing                      # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

ROUND_ID = "2026-09-06-r5"
DECLARED_DATE = "2026-09-06"
RAW_FILES = {
    "applied-top": "reader-raw-r5-applied-top.txt",
    "applied-bottom": "reader-raw-r5-applied-bottom.txt",
    "prep1-top": "reader-raw-r5-prep1-top.txt",
    "prep1-bottom": "reader-raw-r5-prep1-bottom.txt",
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
#: 受保护文件（R5-CLOSE 红线：零改动）
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


def _s31():
    spec = importlib.util.spec_from_file_location(
        "s31_calibration_r5_compare",
        os.path.join(REPO, "scripts", "s31_calibration_r5_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r5.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round5-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r5_files_valid_structure_and_prefixes():
    seen_ids = {"top": [], "bottom": []}
    expect_counts = {"applied-top": 8, "applied-bottom": 1,
                     "prep1-top": 9, "prep1-bottom": 1}
    expect_abstain = {"applied-top": 3, "applied-bottom": 1,
                      "prep1-top": 3, "prep1-bottom": 1}
    for key, name in RAW_FILES.items():
        d = _load(name)
        assert d["reader_id"] == "reader-r5-blind"
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        assert img["image"] == "%s.png" % key           # 图名=文件名对齐
        assert len(img["flags"]) == expect_counts[key]
        view = VIEW_OF_KEY[key]
        prefix = {"top": "R5T-", "bottom": "R5B-"}[view]
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
    # top 视 R5T-001..017 跨两文件连续（applied-top→prep1-top）；
    # bottom 视 R5B-001..002 连续
    assert seen_ids["top"] == ["R5T-%03d" % i for i in range(1, 18)]
    assert seen_ids["bottom"] == ["R5B-001", "R5B-002"]


def test_parse_replay_no_rejections_and_view_injection_deterministic():
    s31 = _s31()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s31.RAW_FILES.items():
        parsed = s31.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s31.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则
    assert s31.view_for_image("applied-top.png") == "top"
    assert s31.view_for_image("prep1-bottom.png") == "bottom"
    assert s31.view_for_image("applied-top.png") == s31.view_for_image(
        "applied-top.png")
    try:
        s31.view_for_image("mystery.png")
    except ValueError:
        pass
    else:
        raise AssertionError("无视角后缀图像名应 ValueError（fail-closed）")
    # run-r5 记录的映射与重放一致（mapping=图像→视角，注入来自图像名）
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
    # 旗标计数（按视角拆分，逐态 9/10、总 19）
    fc = run["reader"]["flag_count"]
    assert fc == {"applied_top": 8, "applied_bottom": 1,
                  "prep1_top": 9, "prep1_bottom": 1,
                  "by_state": {"applied": 9, "prep1": 10}, "total": 19}


# ---------------------------------------------------------------------------
# run-r5：canonical、常量、域声明、受保护文件
# ---------------------------------------------------------------------------

def test_run_r5_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r5"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r5"
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
    # 单变量仪器变更声明在案（nature/components/unchanged/归因）
    ic = rec["instrument_change"]
    assert ic["nature"].startswith("单变量变更")
    assert len(ic["components"]) == 2
    assert len(ic["unchanged_components"]) == 5
    assert "恢复单变量归因" in ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/render-framing-r5.json")
    # 受保护三文件零改动（sha256 前 8）
    for rel, want in PROTECTED_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])


def test_run_r5_compare_v3_recompute_byte_exact():
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
        assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
        assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
    # 命中明细固化（本系列首个框级命中，位于 prep1 态）
    m = rec["states"]["prep1"]["compare_v3"]["matches"]
    assert len(m) == 1
    assert m[0]["flag_id"] == "R5T-013"
    assert m[0]["gt_id"] == "GT-REVC-P1-L1NB"
    assert m[0]["containment"] == 1.0
    assert rec["states"]["applied"]["compare_v3"]["matches"] == []


def test_run_r5_gt_entries_source_plus_reprojection():
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
    # frame_box_pct 恰为 derivation-log-r5 的 frame_box_pct_r5（按 gt_id）
    deriv = {e["gt_id"]: e["frame_box_pct_r5"]
             for e in _load("derivation-log-r5.json")["entries"]}
    for st in ("prep1", "applied"):
        for e in rec["states"][st]["gt_entries"]:
            assert e["frame_box_pct"] == deriv[e["gt_id"]]
            assert 0.0 <= e["frame_box_pct"][0] < e["frame_box_pct"][2] <= 1.0
            assert 0.0 <= e["frame_box_pct"][1] < e["frame_box_pct"][3] <= 1.0


def test_derivation_log_r5_mm_equal_gt_and_pct_full_recompute():
    deriv = _load("derivation-log-r5.json")
    assert deriv["kind"] == "tl2_calibration_gt_reprojection_r5"
    assert deriv["round_id_constant"] == ROUND_ID
    assert len(deriv["entries"]) == 13
    gt_all = {}
    for name in ("ground-truth-v1.json", "ground-truth-v2.json"):
        for e in _load(name)["gt_entries"]:
            gt_all[e["gt_id"]] = e
    assert len(gt_all) == 13
    # 板 bbox（只读实测）与台账 conversion_base 一致
    bbox = cal.board_edge_bbox_mm(open(os.path.join(
        REPO, "out", "revc-asm", "board", "applied.kicad_pcb"),
        encoding="utf-8").read())
    assert bbox == {"x_min": 0.0, "y_min": 0.0, "x_max": 70.0, "y_max": 70.0}
    assert bbox == deriv["conversion_base"]["board_edge_bbox_mm"]
    # px_bounds：对 renders-r5 PNG 实测并与台账声明逐字段相等
    px_by_side = {}
    for key, name in PNG_NAME.items():
        px = cal.png_board_pixel_bounds(open(
            os.path.join(CAL_DIR, "renders-r5", name), "rb").read())
        declared = deriv["conversion_base"]["px_bounds_by_state_side"][key]
        for k in ("x0", "y0", "x1", "y1", "image_width", "image_height"):
            assert px[k] == declared[k], (key, k)
        px_by_side["%s.png" % key] = px
    for e in deriv["entries"]:
        src = gt_all[e["gt_id"]]
        # mm 框与源 GT 条目逐字段 float 相等（零修改声明可复核）
        assert e["board_box_mm_verbatim"] == \
            [float(v) for v in src["board_box_mm"]], e["gt_id"]
        assert e["side"] == "top"                       # 13 条全部 top
        assert e["state"] == ("prep1" if e["gt_id"].startswith(
            "GT-REVC-P1-") else "applied")
        # frame_box_pct_r5 纯函数重算一致（px 界取条目声明的源渲染 PNG）
        src_png = os.path.basename(
            e["conversion_inputs"]["px_bounds"]["source_render"])
        pct = cal.box_mm_to_frame_pct(e["board_box_mm_verbatim"], bbox,
                                      px_by_side[src_png], side="top")
        assert e["frame_box_pct_r5"] == pct, e["gt_id"]
        # 旧基座 frame_box_pct_gt_file 与 GT 文件原值逐字段相等
        assert e["frame_box_pct_gt_file"] == src["frame_box_pct"], e["gt_id"]


# ---------------------------------------------------------------------------
# 聚合算术、达标评估、弃权记账
# ---------------------------------------------------------------------------

def test_run_r5_aggregation_arithmetic():
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
    assert agg["matches_total"] == n_match == 1
    assert agg["gt_matched_total"] == n_gm == 1
    assert agg["scored_total"] == n_sc == 11
    assert agg["abstain_count_total"] == n_ab == 8
    assert agg["flag_count_total"] == n_fl == 19
    assert agg["gt_recall_total"] == round(n_gm / n_gt, 6) == 0.076923
    assert agg["seed_match_rate_total"] == \
        round(n_match / n_sc, 6) == 0.090909
    assert agg["abstain_rate_total"] == round(n_ab / n_fl, 6) == 0.421053
    for f in ("gt_recall_arithmetic", "seed_match_rate_arithmetic",
              "abstain_rate_arithmetic"):
        assert f in agg and isinstance(agg[f], str) and agg[f].strip()
    assert "1/13" in agg["gt_recall_arithmetic"]
    assert "1/11" in agg["seed_match_rate_arithmetic"]
    assert "8/19" in agg["abstain_rate_arithmetic"]
    assert agg["abstain_rate_definition"] == cal.ABSTAIN_RATE_DEFINITION
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE


def test_run_r5_compliance_matches_recomputed():
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
    assert criteria["abstain_rate_le_0.5"]["actual"] == \
        agg["abstain_rate_total"]
    assert criteria["abstain_rate_le_0.5"]["met"] == \
        (agg["abstain_rate_total"] <= 0.5) is True
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5"}
    assert consec["rounds"]["r5"] == "not_met（本轮）"
    # 联合评价如实（任一不满足即未达标）
    all_met = all(c["met"] for c in comp["criteria"]) and consec["met"]
    assert comp["joint_evaluation"] == ("met" if all_met else "not_met")
    assert comp["joint_evaluation"] == "not_met"
    assert comp["critic_calibration_in_range"] is False   # 谓词恒 False
    assert "达标≠自动分流" in comp["critic_calibration_in_range_note"]
    assert "恒 False" in comp["critic_calibration_in_range_note"]


def test_run_r5_abstain_accounting_and_unmatched_semantics():
    rec, _ = _run_record()
    p = rec["states"]["prep1"]["compare_v3"]
    a = rec["states"]["applied"]["compare_v3"]
    # 弃权旗标 id 集与原文逐文件一致（top 各 3 + bottom 各 1）
    assert a["abstain"]["abstain_ids"] == [
        f for f in ("R5T-003", "R5T-007", "R5T-008", "R5B-001")]
    assert p["abstain"]["abstain_ids"] == [
        f for f in ("R5T-012", "R5T-016", "R5T-017", "R5B-002")]
    # bottom 视 2 旗标全部弃权 + top 各 3 弃权 → 每态 4 弃权
    for r in (p, a):
        assert r["abstain"]["abstain_count"] == 4
        for fid in r["abstain"]["abstain_ids"]:
            assert fid not in r["reader_matched_ids"]
        for m in r["matches"]:
            assert m["flag_id"] not in r["abstain"]["abstain_ids"]
    for st in ("prep1", "applied"):
        for fid, view in rec["states"][st]["flag_views"].items():
            if view == "bottom":
                assert fid in rec["states"][st]["compare_v3"]["abstain"][
                    "abstain_ids"]
    # 弃权率口径（单位=旗标条数、分母=全部旗标）
    assert a["abstain"]["abstain_rate"] == round(4 / 9, 6) == 0.444444
    assert p["abstain"]["abstain_rate"] == round(4 / 10, 6) == 0.4
    # unmatched 语义（无越界命名；unmatched=非弃权且未一对一命中）
    for r in (p, a):
        assert "reader_false_positive_ids" not in r
        assert "reader_precision_vs_seed_gt" not in r
        assert "seed_match_rate" in r and "seed_metric_note" in r
        assert r["reader_unmatched_ids"] and \
            len(r["reader_unmatched_ids"]) == 5
        assert r["duplicate_reports"] == []
        assert r["reader_unmatched_no_box_ids"] == []
    assert a["reader_unmatched_ids"] == ["R5T-001", "R5T-002", "R5T-004",
                                         "R5T-005", "R5T-006"]
    assert a["reader_matched_ids"] == []
    assert p["reader_unmatched_ids"] == ["R5T-009", "R5T-010", "R5T-011",
                                         "R5T-014", "R5T-015"]
    assert p["reader_matched_ids"] == ["R5T-013"]


# ---------------------------------------------------------------------------
# 预注册链、冻结顺序、仪器事实
# ---------------------------------------------------------------------------

def test_run_r5_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "render_framing_r5_preregistration",
            "observation_guidance_r4_reused", "gt_reprojection_log_r5",
            "gt_seed_prep1", "gt_expansion_applied",
            "source_image_pdf_applied_top_r4",
            "source_image_pdf_applied_bottom_r4",
            "source_image_pdf_prep1_top_r4",
            "source_image_pdf_prep1_bottom_r4",
            "render_png_applied_top_r5", "render_png_applied_bottom_r5",
            "render_png_prep1_top_r5", "render_png_prep1_bottom_r5"} <= roles
    for key, blk in rec["reader"]["raw_files"].items():
        assert blk["sha256"] == _sha(blk["path_rel"])
        assert os.path.basename(blk["path_rel"]) == RAW_FILES[key]
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    ref3 = rec["reference_rounds"]["r3_run"]
    ref4 = rec["reference_rounds"]["r4_run"]
    assert ref3["sha256"] == _sha(ref3["path_rel"])
    assert ref4["sha256"] == _sha(ref4["path_rel"])


def test_framing_r5_preregistration_chain_refs_match_disk():
    fr = _load("render-framing-r5.json")
    deriv = _load("derivation-log-r5.json")
    # framing-r5 自身常量与域声明
    assert fr["kind"] == "tl2_calibration_render_framing_r5_preregistration"
    assert fr["round_id_constant"] == ROUND_ID
    assert fr["round_label"] == "r5"
    assert fr["date_constant"] == DECLARED_DATE
    assert fr["evaluation_split"]["declared"] == "development"
    assert "降级为 development 证据" in fr["evaluation_split"]["basis"]
    assert fr["evaluation_split"]["protocol_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/evaluation-protocol-v1.md")
    # 单变量变更声明 + 指引逐字沿用锚
    assert fr["instrument"]["change_declaration"].startswith("单变量仪器变更")
    assert fr["instrument"]["new_in_r5"]["dpi"] == 640
    assert fr["instrument"]["rasterization"]["crop_margin_px"] == 120
    reuse = fr["frozen_inputs"]["guidance_reuse"]
    assert reuse["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r4.md")
    assert reuse["declaration"].startswith(
        "observation-guidance-r4.md 逐字沿用")
    # framing-r5 引用的 r4 冻结 PDF/PNG sha 与盘上一致
    for blk in fr["frozen_inputs"]["r4_frozen_pdfs"]:
        assert blk["sha256"] == _sha(blk["path_rel"]), blk["state_side"]
    for side, want in fr["frozen_inputs"][
            "r4_frozen_png_sha256_reference"].items():
        assert _sha("out/v3-tl2/calibration/renders-r4/%s.png" % side) == want
    # derivation-log-r5 ↔ framing-r5 互相锚定
    assert deriv["framing_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/render-framing-r5.json")
    assert deriv["framing_ref"]["sha256"].startswith("860aa910")
    for src in deriv["gt_sources"]:
        assert src["sha256"] == _sha(src["path_rel"])
    # 官方成图 sha 与台账 images[] 一致（先于盲读冻结的仪器事实）
    imgs = {i["state_side"]: i for i in deriv["renders_r5"]["images"]}
    for key, name in PNG_NAME.items():
        assert imgs[key]["sha256"] == _sha(
            "out/v3-tl2/calibration/renders-r5/" + name)
    assert deriv["renders_r5"]["bottom_pair_byte_identical"] is True
    # 预注册顺序声明（framing 先于任何官方成图落盘）
    assert "先于本轮任何官方渲染落盘" in fr["preregistration_order_note"]
    assert fr["no_visual_reading"] is True


def test_r5_renders_sanity_and_gt_all_top():
    # 仪器事实：两态 B 面图层一致 → 两 bottom 渲染逐字节相同
    top_png = os.path.join(CAL_DIR, "renders-r5", "applied-top.png")
    bot_a = open(os.path.join(CAL_DIR, "renders-r5", "applied-bottom.png"),
                 "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r5", "prep1-bottom.png"),
                 "rb").read()
    assert hashlib.sha256(bot_a).hexdigest() == \
        hashlib.sha256(bot_p).hexdigest() == BOTTOM_PNG_SHA256
    assert bot_a != open(top_png, "rb").read()
    # 13 条 GT 全部 side=top（bottom 旗标无从命中，且全部弃权）
    deriv = _load("derivation-log-r5.json")
    assert all(e["side"] == "top" for e in deriv["entries"])
    rec, _ = _run_record()
    for st in ("prep1", "applied"):
        assert all(e["side"] == "top"
                   for e in rec["states"][st]["gt_entries"])
        assert rec["states"][st]["compare_v3"]["view_mismatch"] == []
    # 有效分辨率对照（framing-r5 expected_geometry：板占比 0.8803 量级）
    fr = _load("render-framing-r5.json")
    eg = fr["expected_geometry"]
    assert eg["board_fraction_short_edge_top"] > 0.85
    assert eg["board_px_wh_top"] == [1765, 1765]
    assert eg["full_pixmap_wh_at_640"] == [8195, 6003]


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round5_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=单变量仪器迭代（有效分辨率）与协议降级条款原文引用
    assert "单变量仪器迭代轮" in dev["round_nature"]
    assert "有效分辨率" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert dev["instrument_change"]["nature"].startswith("单变量变更")
    # 诊断结果与 run-r5 一致
    run, _ = _run_record()
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation"]["abstain_rate_total"] == 0.421053
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation"]["gt_recall_total"] == 0.076923
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation"]["seed_match_rate_total"] == 0.090909
    assert dev["diagnostic_result"]["seed_metric_note"] == \
        cal.SEED_METRIC_NOTE
    # run-r5 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r5.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # 诚实结论：明确声明不做能力修复类断言；flag 产出事实在案
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.421053" in hc and "development 域" in hc
    assert "0.076923" in hc and "0.090909" in hc
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 8 and fp["non_abstain_count"] == 11
    assert fp["abstain_rate"] == 0.421053
    assert fp["parse_rejections"] == []
    assert fp["flag_count_by_file"] == {"applied-top": 8,
                                        "applied-bottom": 1,
                                        "prep1-top": 9, "prep1-bottom": 1}
    assert sum(fp["flag_count_by_file"].values()) == 19
    assert "冻结证据" in fp["note"]
    assert fp["reader_id"] == "reader-r5-blind"
    # 方向性观察（只描述）与下一迭代目标在案
    assert isinstance(dev["directional_observation_vs_r4"], list)
    assert len(dev["directional_observation_vs_r4"]) >= 5
    assert any("0.75" in o and "0.421053" in o
               for o in dev["directional_observation_vs_r4"])
    assert any("R5T-013" in o and "GT-REVC-P1-L1NB" in o
               for o in dev["directional_observation_vs_r4"])
    assert dev["next_iteration_targets"]
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r5 冻结工件一致
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles


def test_dev_record_r4_position_comparison_values_reproducible():
    """方向性观察中的位置对照 containment 值可独立复算（描述性，
    不入度量）：R5T-005/R5T-014 vs AP-7、R5T-010 vs P1-R4J3、
    R5T-004/R5T-013 完整覆盖 L1NB/L1SHORT；R4 非弃权旗标区与本轮
    非弃权旗标区板坐标零重叠。"""
    dev, _ = _run_dev_record()
    obs = "\n".join(dev["directional_observation_vs_r4"])
    deriv = _load("derivation-log-r5.json")
    r5 = {e["gt_id"]: e["frame_box_pct_r5"] for e in deriv["entries"]}
    c_005 = cal._containment([0.185, 0.46, 0.315, 0.63], r5[
        "GT-REVC-AP-7-C31U4"])
    c_010 = cal._containment([0.84, 0.225, 0.905, 0.265], r5[
        "GT-REVC-P1-R4J3"])
    c_013_nb = cal._containment([0.615, 0.585, 0.79, 0.8], r5[
        "GT-REVC-P1-L1NB"])
    c_013_sh = cal._containment([0.615, 0.585, 0.79, 0.8], r5[
        "GT-REVC-P1-L1SHORT"])
    assert round(c_005, 6) == 0.882465 and ("0.882465" in obs)
    assert round(c_010, 6) == 0.510336 and ("0.510336" in obs)
    assert c_013_nb == 1.0 and c_013_sh == 1.0
    # 面积比出局项数值（≈11.93 > AREA_RATIO_MAX=10）
    gt = r5["GT-REVC-AP-7-C31U4"]
    ratio = ((0.315 - 0.185) * (0.63 - 0.46)) / \
        ((gt[2] - gt[0]) * (gt[3] - gt[1]))
    assert ratio > cal.AREA_RATIO_MAX and "11.93" in obs
    assert "10.0" in obs and "AREA_RATIO_MAX" in obs
    # 匹配面积比 6.739726 与 run-r5 一致
    run, _ = _run_record()
    m = run["states"]["prep1"]["compare_v3"]["matches"][0]
    assert m["area_ratio"] == 6.739726 and "6.739726" in obs
    # R4 零重叠断言在观察文本中如实记录
    assert "零重叠" in obs


def test_naming_constraints_recursive_and_preregistration_note():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "无任何 GT" in rp["discipline"]
    assert rp["guidance_ref"]["frozen_before_render"] is True
    assert rp["guidance_ref"]["frozen_before_read"] is True
    assert rp["guidance_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r4.md")
    assert "逐字沿用" in rp["guidance_ref"]["reuse_note"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert rec["deterministic_recompute_note"]
    assert "2026-09-06-r5" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域单变量迭代，非留出）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "单变量" in dev["round_nature"] and "有效分辨率" in \
        dev["round_nature"]


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
