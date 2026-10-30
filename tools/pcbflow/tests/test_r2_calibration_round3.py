"""R2 执行包测试：校准第三轮（r3）——GT 扩样冻结 + 按视图双盲读 +
度量 v3 两态比对 + 聚合与达标评估锚。

覆盖：
- ground-truth-v2.json（applied 态扩样 9 条 courtyards_overlap 判例）：
  全条 validate_gt_entries 通过、gt_id 唯一、与 derivation-log-r2 逐条
  对账（gt_id 集一致、gt_file hash 在案、拒收候选在案）、v1 四条零改动
  （hash 先验锚）；
- 两态 framing 确定性：board_edge_bbox_mm（板文本）+ png_board_pixel_bounds
  （PNG 字节）同输入重算两次同框；GT-v2 每条 board_box_mm→
  box_mm_to_frame_pct(top, applied framing) 重算=落盘 frame_box_pct；
  render-framing-r3 的板 hash=45320fbe 开头 + 渲染零写见证（前后一致）；
- 盲读原文（reader-raw-r3-top/bottom.txt）：存在、只读、合法 JSON、
  结构（reader_id/per_image/flags 五键+location_evidence）、视图前缀
  一致（R3T→top 图、R3B→bottom 图）、旗标数与 run 记录一致；
- calibration-run-r3.json：盘上 canonical byte 一致；两态 compare_v3
  用记录内嵌输入（reader_flags/gt_entries/flag_views）重算 byte-exact
  一致且 view_check=full；聚合算术显式复算一致（gt_recall_total/
  seed_match_rate_total/abstain_rate_total）；达标评估逐项复算一致
  （APR-0011 五项）、joint=not_met、critic_calibration_in_range=False、
  auto 分流语义在案；轮次标识=声明常量（无机器时间戳键）；
- 预注册块：冻结件 hash 与盘上实值一致；度量版本=calibration-metric-v3；
  比较器阈值声明常量零变化。

只读 out/（生成器模式）：零子进程/零写盘/零网络。
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import calibration as cal           # noqa: E402
from pcbflow import critic                       # noqa: E402
from pcbflow import hashing                      # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

#: 先验锚（R1 闭包时在案；本包零改动断言）
FROZEN_GT_V1_SHA256 = (
    "828b6b5fe2c03a5ae1c70e338b44dc32bc7c21179dc85019453d9236ece314ed")
APPLIED_BOARD_SHA256 = (
    "45320fbe3296a0594a3678a30ad2c1bf775e6c7e9666158abb82081fc2245d85")
GT_V2_IDS = [
    "GT-REVC-AP-1-R5U6", "GT-REVC-AP-2-Y1C35", "GT-REVC-AP-3-Y1C5",
    "GT-REVC-AP-4-Y1C36", "GT-REVC-AP-5-Y1C4", "GT-REVC-AP-6-R2LED2",
    "GT-REVC-AP-7-C31U4", "GT-REVC-AP-8-R1Q2", "GT-REVC-AP-9-Y2C3",
]
ROUND_ID = "2026-09-06-r3"
REJECTED_CANDIDATES = 6


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


# ---------------------------------------------------------------------------
# GT-v2：结构校验 + 唯一性 + 派生台账对账
# ---------------------------------------------------------------------------

def test_gt_v2_entries_valid_and_unique():
    gt = _load("ground-truth-v2.json")
    entries = gt["gt_entries"]
    assert len(entries) == 9
    cal.validate_gt_entries(entries)                      # 全条合法（含键集）
    ids = [e["gt_id"] for e in entries]
    assert ids == GT_V2_IDS                               # 唯一 + 命名约束
    assert len(set(ids)) == len(ids)
    for e in entries:
        assert e["category"] == "courtyard_crowding"      # 诚实映射
        assert e["side"] == "top"                         # 两封装均 F.Cu
        assert e["drc_types"] == ["courtyards_overlap"]
        assert len(e["cluster_refs"]) == 2
        assert e["category"] in critic.FLAG_CATEGORIES
        # 框=锚点 bbox±GT_MARGIN_MM 的可逆性：宽/高 ∈ [2*margin, 16]mm
        # （锚点可共线，如 R2-LED2 同 x → 宽恰为 2.0）
        w = e["board_box_mm"][2] - e["board_box_mm"][0]
        h = e["board_box_mm"][3] - e["board_box_mm"][1]
        assert 2.0 <= w <= 16.0 and 2.0 <= h <= 16.0
    assert gt["schema_version"] == "3.0"
    assert gt["kind"] == "tl2_calibration_ground_truth"
    assert gt["self_check"]["gt_count"] == 9
    assert gt["self_check"]["gt_matched_count"] == 9      # GT 自匹配 sanity
    assert gt["self_check"]["view_check"] == "full"


def test_gt_v2_derivation_log_consistent():
    log = _load("derivation-log-r2.json")
    gt = _load("ground-truth-v2.json")
    assert log["kind"] == "tl2_calibration_gt_derivation_log"
    assert log["entry_count"] == 9
    assert [e["gt_id"] for e in log["entries"]] == \
        [e["gt_id"] for e in gt["gt_entries"]]
    assert log["gt_file"]["sha256"] == \
        _sha("out/v3-tl2/calibration/ground-truth-v2.json")
    # 拒收候选如实记录（F4 等长/keepout/未连接/waiver/丝印）
    assert len(log["rejected_candidates"]) == REJECTED_CANDIDATES
    joined = json.dumps(log["rejected_candidates"], ensure_ascii=False)
    for needle in ("F4", "keepout", "112", "silk_over_copper", "不收"):
        assert needle in joined
    # 逐条证据链要素在案（来源+hash+定位器+派生步骤+可见性依据）
    for e in log["entries"]:
        assert e["evidence_sources"] and e["derivation_steps"]
        assert e["visibility_basis"] and e["category_mapping_note"]
        drc_src = [s for s in e["evidence_sources"]
                   if s["provenance_key"] == "drc7_final_all"]
        assert drc_src and drc_src[0]["sha256_first8"] == "4485e6c2"
        assert "violations" in drc_src[0]["locator"]
    # 台账自身 canonical 落盘
    path = os.path.join(CAL_DIR, "derivation-log-r2.json")
    disk = open(path, "rb").read()
    assert disk == hashing.canonical_json_bytes(json.loads(disk.decode("utf-8")))


def test_gt_v1_untouched():
    assert _sha("out/v3-tl2/calibration/ground-truth-v1.json") == \
        FROZEN_GT_V1_SHA256
    v1 = _load("ground-truth-v1.json")
    assert len(v1["gt_entries"]) == 4                     # 种子域四条原样
    assert v1["gt_entries"][0]["gt_id"] == "GT-REVC-P1-R4J3"


# ---------------------------------------------------------------------------
# 两态 framing 确定性（同输入同框）
# ---------------------------------------------------------------------------

def test_framing_deterministic_applied():
    board_text = open(os.path.join(REPO, "out", "revc-asm", "board",
                                   "applied.kicad_pcb"),
                      encoding="utf-8").read()
    top_png = os.path.join(CAL_DIR, "renders-r3", "applied-top.png")
    bot_png = os.path.join(CAL_DIR, "renders-r3", "applied-bottom.png")
    top_bytes = open(top_png, "rb").read()
    bot_bytes = open(bot_png, "rb").read()
    # 同输入重算两次同框（确定性）
    bbox1 = cal.board_edge_bbox_mm(board_text)
    bbox2 = cal.board_edge_bbox_mm(board_text)
    assert bbox1 == bbox2 == {"x_min": 0.0, "y_min": 0.0,
                              "x_max": 70.0, "y_max": 70.0}
    px1 = cal.png_board_pixel_bounds(top_bytes)
    px2 = cal.png_board_pixel_bounds(top_bytes)
    assert px1 == px2
    pxb1 = cal.png_board_pixel_bounds(bot_bytes)
    pxb2 = cal.png_board_pixel_bounds(bot_bytes)
    assert pxb1 == pxb2
    # framing 记录与重算一致
    fr = _load("render-framing-r3.json")
    assert fr["source_board"]["sha256"] == APPLIED_BOARD_SHA256
    assert fr["board_edge_bbox_mm"] == bbox1
    by_side = {r["side"]: r for r in fr["renders"]}
    assert by_side["top"]["sha256"] == _sha(
        "out/v3-tl2/calibration/renders-r3/applied-top.png")
    assert by_side["bottom"]["sha256"] == _sha(
        "out/v3-tl2/calibration/renders-r3/applied-bottom.png")
    for side, px in (("top", px1), ("bottom", pxb1)):
        rec = by_side[side]["board_pixel_bounds"]
        assert (rec["x0"], rec["y0"], rec["x1"], rec["y1"]) == \
            (px["x0"], px["y0"], px["x1"], px["y1"])
        assert rec["image_width"] == px["image_width"] == 1568
        assert rec["image_height"] == px["image_height"] == 872
    # 渲染零写见证（板 hash 前后一致=45320fbe 开头）
    zw = fr["zero_write_witness"]
    assert zw["board_sha256_before_render"] == \
        zw["board_sha256_after_render"] == APPLIED_BOARD_SHA256
    # prep1 既有渲染零重渲染（hash 引用在案）
    ref = fr["prep1_reuse_reference"]
    assert ref["framing_file"]["sha256"] == \
        _sha("out/v3-tl2/calibration/render-framing.json")
    assert ref["renders"]["out/v3-tl2/calibration/renders/revc-prep1-top.png"] \
        == _sha("out/v3-tl2/calibration/renders/revc-prep1-top.png")


def test_gt_v2_frame_pct_recomputes_from_framing():
    board_text = open(os.path.join(REPO, "out", "revc-asm", "board",
                                   "applied.kicad_pcb"),
                      encoding="utf-8").read()
    bbox = cal.board_edge_bbox_mm(board_text)
    px = cal.png_board_pixel_bounds(
        open(os.path.join(CAL_DIR, "renders-r3", "applied-top.png"),
             "rb").read())
    gt = _load("ground-truth-v2.json")
    for e in gt["gt_entries"]:
        assert e["frame_box_pct"] == cal.box_mm_to_frame_pct(
            e["board_box_mm"], bbox, px, side="top"), e["gt_id"]


# ---------------------------------------------------------------------------
# 盲读原文（只读）合法性与结构
# ---------------------------------------------------------------------------

READER_FLAG_KEYS = {"flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence"}


def test_reader_raw_files_valid_json_and_structure():
    for view in ("top", "bottom"):
        path = os.path.join(CAL_DIR, "reader-raw-r3-%s.txt" % view)
        assert os.path.isfile(path), path
        raw = open(path, encoding="utf-8").read()
        d = json.loads(raw)                               # 合法 JSON
        assert d["reader_id"] == "reader-r3-%s" % view
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 2
        images = [p["image"] for p in d["per_image"]]
        assert any("prep1" in i for i in images)          # 两态各一图
        assert any("applied" in i for i in images)
        for p in d["per_image"]:
            for f in p["flags"]:
                assert set(f) == READER_FLAG_KEYS         # 五键+位置证据
                assert f["category"] in critic.FLAG_CATEGORIES
                assert 0.0 <= float(f["confidence"]) <= 1.0
                assert isinstance(f["abstain"], bool)
                box = f["frame_box_pct"]
                assert len(box) == 4 and all(0.0 <= v <= 1.0 for v in box)
                assert box[0] < box[2] and box[1] < box[3]
                assert f["location_evidence"].strip()
                prefix = {"top": "R3T-", "bottom": "R3B-"}[view]
                assert f["flag_id"].startswith(prefix)    # 视图前缀一致
        assert "仅陈述可见现象" in d["reading_notes"] or \
            "不作" in d["reading_notes"]


def test_reader_flag_counts_match_run_record():
    run = _load("calibration-run-r3.json")
    for view, n in (("top", 8), ("bottom", 6)):
        d = json.loads(open(os.path.join(
            CAL_DIR, "reader-raw-r3-%s.txt" % view),
            encoding="utf-8").read())
        total = sum(len(p["flags"]) for p in d["per_image"])
        assert total == n == run["reader"]["flag_count"][view]
    assert run["reader"]["flag_count"]["total"] == 14
    assert run["reader"]["parse"] == {
        "top": {"direct_json_parse": True, "repair": "no_repair"},
        "bottom": {"direct_json_parse": True, "repair": "no_repair"}}


# ---------------------------------------------------------------------------
# run-r3：canonical、两态比对重算、聚合算术、达标评估
# ---------------------------------------------------------------------------

def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r3.json")
    disk = open(path, "rb").read()
    rec = json.loads(disk.decode("utf-8"))
    return rec, disk


def test_run_record_canonical_and_constants():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)      # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r3"
    assert rec["round_id"] == ROUND_ID                    # 声明常量
    assert rec["declared_date"] == "2026-09-06"
    assert rec["metric_version"] == "calibration-metric-v3"
    assert rec["preregistration"]["round_id_constant"] == ROUND_ID
    for key in rec:                                       # 无机器时间戳键
        assert "time" not in key.lower() and "date" not in key.lower() or \
            key in ("declared_date",)


def test_run_record_compare_v3_recompute_byte_exact():
    rec, _ = _run_record()
    gt_v1 = _load("ground-truth-v1.json")
    gt_v2 = _load("ground-truth-v2.json")
    for st, gt in (("prep1", gt_v1), ("applied", gt_v2)):
        block = rec["states"][st]
        rep = cal.compare_v3(block["reader_flags"], gt["gt_entries"],
                             flag_views=block["flag_views"])
        assert hashing.canonical_json_bytes(rep) == \
            hashing.canonical_json_bytes(block["compare_v3"])   # byte-exact
        assert block["view_check"] == rep["view_check"] == "full"
        assert block["flag_views"]                              # 视角已注入
        assert all(v in ("top", "bottom")
                   for v in block["flag_views"].values())


def test_run_record_aggregation_arithmetic():
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
    assert agg["matches_total"] == n_match
    assert agg["gt_matched_total"] == n_gm
    assert agg["scored_total"] == n_sc
    assert agg["abstain_count_total"] == n_ab
    assert agg["flag_count_total"] == n_fl
    assert agg["gt_recall_total"] == round(n_gm / n_gt, 6)
    assert agg["seed_match_rate_total"] == round(n_match / n_sc, 6)
    assert agg["abstain_rate_total"] == round(n_ab / n_fl, 6)
    for f in ("gt_recall_arithmetic", "seed_match_rate_arithmetic",
              "abstain_rate_arithmetic"):
        assert f in agg and isinstance(agg[f], str) and agg[f].strip()


def test_run_record_compliance_matches_recomputed():
    rec, _ = _run_record()
    agg = rec["aggregation"]
    comp = rec["compliance"]
    criteria = {c["id"]: c for c in comp["criteria"]}
    # 逐项复算（APR-0011 基线）
    assert criteria["gt_count_ge_12"]["actual"] == agg["gt_count_total"]
    assert criteria["gt_count_ge_12"]["met"] == \
        (agg["gt_count_total"] >= 12)
    assert criteria["gt_recall_ge_0.75"]["actual"] == agg["gt_recall_total"]
    assert criteria["gt_recall_ge_0.75"]["met"] == \
        (agg["gt_recall_total"] >= 0.75)
    assert criteria["seed_match_rate_ge_0.5"]["actual"] == \
        agg["seed_match_rate_total"]
    assert criteria["seed_match_rate_ge_0.5"]["met"] == \
        (agg["seed_match_rate_total"] >= 0.5)
    assert criteria["abstain_rate_le_0.5"]["actual"] == \
        agg["abstain_rate_total"]
    assert criteria["abstain_rate_le_0.5"]["met"] == \
        (agg["abstain_rate_total"] <= 0.5)
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3"}
    # 联合评价如实（任一不满足即未达标）
    all_met = all(c["met"] for c in comp["criteria"]) and consec["met"]
    assert comp["joint_evaluation"] == ("met" if all_met else "not_met")
    assert comp["joint_evaluation"] == "not_met"
    assert comp["critic_calibration_in_range"] is False   # 谓词恒 False
    assert "自动分流" in comp["critic_calibration_in_range_note"]
    assert "BL-4" in comp["critic_calibration_in_range_note"] or \
        "达标≠自动分流" in comp["critic_calibration_in_range_note"]


def test_run_record_preregistration_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in rec["preregistration"]["frozen_artifacts"]}
    assert {"gt_expansion", "gt_expansion_derivation_log",
            "evaluation_protocol", "render_framing_applied",
            "render_png_applied_top", "render_png_applied_bottom"} <= roles
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "无任何 GT" in rp["discipline"]
    assert rec["preregistration"]["metric_version"] == "calibration-metric-v3"
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    # 命名约束在案
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
