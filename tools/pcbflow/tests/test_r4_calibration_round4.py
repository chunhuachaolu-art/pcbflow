"""R4 执行包测试：reader 判读迭代第四轮收口（CAL-R4-CLOSE）——
盲读解析与视角注入 + 双态 compare_v3 重投影比对 + development 域记录。

覆盖：
- 盲读原文（reader-raw-r4-{applied,prep1}-{top,bottom}.txt，冻结证据）：
  合法 JSON、结构（reader_id/per_image/reading_notes；flag 六键含
  location_evidence）、视角前缀一致（R4T→top 图、R4B→bottom 图）、
  拒收清单固化（全 8 旗标过 calibration fail-closed 校验，0 拒收）；
- 视角注入确定性：s30 的图像名→视角映射纯函数两次调用一致，
  run-r4 记录的 flag_views 与该规则逐旗标一致；
- calibration-run-r4.json：盘上 canonical byte 一致；两态 compare_v3
  用记录内嵌输入（reader_flags/gt_entries/flag_views）重算 byte-exact
  一致且 view_check=full；内嵌 gt_entries=源 GT 文件条目（frame_box_pct
  ←derivation-log-r4 的 frame_box_pct_r4，其余字段逐字段原样）；
  聚合算术显式复算一致；达标评估逐项复算一致（APR-0011 五项）、
  joint=not_met、critic_calibration_in_range=False、域=development；
  弃权计数与弃权单列（bottom 视 4/4 弃权）；
- derivation-log-r4.json：13 条 board_box_mm_verbatim 与 GT 文件逐字段
  float 相等；frame_box_pct_r4 全链纯函数重算一致（板文件 Edge.Cuts
  bbox + renders-r4 PNG 实测像素界 + box_mm_to_frame_pct，top 同向）；
- 预注册冻结顺序：staging-integrity-r4 记录的 framing/guidance sha 与
  落盘件一致、frozen_artifacts_check 全 match、framing 声明
  evaluation_split.declared=development；
- 两 bottom 渲染逐字节相同（仪器事实）+ 13 条 GT 全部 side=top；
- round4-dev-record.json：域声明、协议降级条款引用、仪器复合变更、
  方向性观察（无能力断言）、run-r4 sha 引用一致、is_gate=False；
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

ROUND_ID = "2026-09-06-r4"
DECLARED_DATE = "2026-09-06"
RAW_FILES = {
    "applied-top": "reader-raw-r4-applied-top.txt",
    "applied-bottom": "reader-raw-r4-applied-bottom.txt",
    "prep1-top": "reader-raw-r4-prep1-top.txt",
    "prep1-bottom": "reader-raw-r4-prep1-bottom.txt",
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
#: 受保护文件（R4-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
BOTTOM_PNG_SHA256 = (
    "ba0b7259d1c18950974edd28230ba34883a548f962f2b93e5b88da425f30d84e")
PNG_NAME = {"applied-top": "applied-top.png",
            "applied-bottom": "applied-bottom.png",
            "prep1-top": "prep1-top.png", "prep1-bottom": "prep1-bottom.png"}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s30():
    spec = importlib.util.spec_from_file_location(
        "s30_calibration_r4_compare",
        os.path.join(REPO, "scripts", "s30_calibration_r4_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r4.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r4_files_valid_structure_and_prefixes():
    seen_ids = {"top": [], "bottom": []}
    for key, name in RAW_FILES.items():
        d = _load(name)
        assert d["reader_id"] == "reader-r4-blind"
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        assert img["image"] == "%s.png" % key           # 图名=文件名对齐
        assert len(img["flags"]) == 2                   # 每图恰 2 旗标
        view = "top" if key.endswith("-top") else "bottom"
        prefix = {"top": "R4T-", "bottom": "R4B-"}[view]
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
            seen_ids[view].append(f["flag_id"])
    # top 视 R4T-001..004 跨两文件连续；bottom 视 R4B-001..004 连续
    assert seen_ids["top"] == ["R4T-001", "R4T-002", "R4T-003", "R4T-004"]
    assert seen_ids["bottom"] == ["R4B-001", "R4B-002", "R4B-003", "R4B-004"]


def test_parse_replay_no_rejections_and_view_injection_deterministic():
    s30 = _s30()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s30.RAW_FILES.items():
        parsed = s30.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s30.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则
    assert s30.view_for_image("applied-top.png") == "top"
    assert s30.view_for_image("prep1-bottom.png") == "bottom"
    assert s30.view_for_image("applied-top.png") == s30.view_for_image(
        "applied-top.png")
    try:
        s30.view_for_image("mystery.png")
    except ValueError:
        pass
    else:
        raise AssertionError("无视角后缀图像名应 ValueError（fail-closed）")
    # run-r4 记录的映射与重放一致（mapping=图像→视角，注入来自图像名）
    run, _ = _run_record()
    for key in RAW_FILES:
        want = {img["image"]: img["view"] for img in replay[key]["images"]}
        got = run["reader"]["view_injection"]["mapping"][key]
        assert got == want
    state = {"applied-top": "applied", "applied-bottom": "applied",
             "prep1-top": "prep1", "prep1-bottom": "prep1"}
    for key in RAW_FILES:
        replay_ids = {f["flag_id"] for img in replay[key]["images"]
                      for f in img["flags"]}
        view = "top" if key.endswith("-top") else "bottom"
        block = run["states"][state[key]]
        for fid in replay_ids:
            assert block["flag_views"][fid] == view
            assert fid in [f["flag_id"] for f in block["reader_flags"]]
    assert run["parse_rejections"] == []                # 拒收清单固化（空）


# ---------------------------------------------------------------------------
# run-r4：canonical、常量、域声明、受保护文件
# ---------------------------------------------------------------------------

def test_run_r4_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r4"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
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
    # 仪器复合变更声明在案
    assert rec["instrument_change"]["nature"].startswith("复合变更")
    assert len(rec["instrument_change"]["components"]) == 2
    assert "不能单一归因" in rec["instrument_change"]["attribution_note"]
    # 受保护三文件零改动（sha256 前 8）
    for rel, want in PROTECTED_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])


def test_run_r4_compare_v3_recompute_byte_exact():
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


def test_run_r4_gt_entries_source_plus_reprojection():
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
    # frame_box_pct 恰为 derivation-log-r4 的 frame_box_pct_r4（按 gt_id）
    deriv = {e["gt_id"]: e["frame_box_pct_r4"]
             for e in _load("derivation-log-r4.json")["entries"]}
    for st in ("prep1", "applied"):
        for e in rec["states"][st]["gt_entries"]:
            assert e["frame_box_pct"] == deriv[e["gt_id"]]
            assert 0.0 <= e["frame_box_pct"][0] < e["frame_box_pct"][2] <= 1.0
            assert 0.0 <= e["frame_box_pct"][1] < e["frame_box_pct"][3] <= 1.0


def test_derivation_log_r4_mm_equal_gt_and_pct_full_recompute():
    deriv = _load("derivation-log-r4.json")
    assert deriv["kind"] == "tl2_calibration_gt_reprojection_r4"
    assert deriv["round_id_constant"] == ROUND_ID
    assert len(deriv["entries"]) == 13
    gt_all = {}
    for name in ("ground-truth-v1.json", "ground-truth-v2.json"):
        for e in _load(name)["gt_entries"]:
            gt_all[e["gt_id"]] = e
    assert len(gt_all) == 13
    # 板 bbox 与 R4 渲染像素界全链重算基座（只读实测）
    bbox = cal.board_edge_bbox_mm(open(os.path.join(
        REPO, "out", "revc-asm", "board", "applied.kicad_pcb"),
        encoding="utf-8").read())
    assert bbox == {"x_min": 0.0, "y_min": 0.0, "x_max": 70.0, "y_max": 70.0}
    px_by_png = {}
    for key, name in PNG_NAME.items():
        px_by_png["%s.png" % key] = cal.png_board_pixel_bounds(open(
            os.path.join(CAL_DIR, "renders-r4", name), "rb").read())
    for e in deriv["entries"]:
        src = gt_all[e["gt_id"]]
        # mm 框与源 GT 条目逐字段 float 相等（零修改声明可复核）
        assert e["board_box_mm_verbatim"] == \
            [float(v) for v in src["board_box_mm"]], e["gt_id"]
        assert e["side"] == "top"                       # 13 条全部 top
        assert e["state"] == ("prep1" if e["gt_id"].startswith(
            "GT-REVC-P1-") else "applied")
        # frame_box_pct_r4 纯函数重算一致（px 界取条目声明的源渲染 PNG）
        src_png = os.path.basename(
            e["conversion_inputs"]["px_bounds"]["source_render"])
        pct = cal.box_mm_to_frame_pct(e["board_box_mm_verbatim"], bbox,
                                      px_by_png[src_png], side="top")
        assert e["frame_box_pct_r4"] == pct, e["gt_id"]
        # 旧基座 frame_box_pct_gt_file 与 GT 文件原值逐字段相等
        assert e["frame_box_pct_gt_file"] == src["frame_box_pct"], e["gt_id"]


# ---------------------------------------------------------------------------
# 聚合算术、达标评估、弃权记账
# ---------------------------------------------------------------------------

def test_run_r4_aggregation_arithmetic():
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
    assert agg["flag_count_total"] == n_fl == 8
    assert agg["gt_recall_total"] == round(n_gm / n_gt, 6)
    assert agg["seed_match_rate_total"] == round(n_match / n_sc, 6)
    assert agg["abstain_rate_total"] == round(n_ab / n_fl, 6)
    for f in ("gt_recall_arithmetic", "seed_match_rate_arithmetic",
              "abstain_rate_arithmetic"):
        assert f in agg and isinstance(agg[f], str) and agg[f].strip()
    assert "6/8" in agg["abstain_rate_arithmetic"] and n_ab == 6
    assert agg["abstain_rate_definition"] == cal.ABSTAIN_RATE_DEFINITION
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE


def test_run_r4_compliance_matches_recomputed():
    rec, _ = _run_record()
    agg = rec["aggregation"]
    comp = rec["compliance"]
    criteria = {c["id"]: c for c in comp["criteria"]}
    # 逐项复算（APR-0011 基线；阈值措辞与协议一致，禁改）
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
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4"}
    # 联合评价如实（任一不满足即未达标）
    all_met = all(c["met"] for c in comp["criteria"]) and consec["met"]
    assert comp["joint_evaluation"] == ("met" if all_met else "not_met")
    assert comp["joint_evaluation"] == "not_met"
    assert comp["critic_calibration_in_range"] is False   # 谓词恒 False
    assert "达标≠自动分流" in comp["critic_calibration_in_range_note"]
    assert "恒 False" in comp["critic_calibration_in_range_note"]


def test_run_r4_abstain_accounting_and_unmatched_semantics():
    rec, _ = _run_record()
    p = rec["states"]["prep1"]["compare_v3"]
    a = rec["states"]["applied"]["compare_v3"]
    bottom_ids = set()
    for st in ("prep1", "applied"):
        block = rec["states"][st]
        for fid, view in block["flag_views"].items():
            if view == "bottom":
                bottom_ids.add(fid)
    # bottom 视 4 旗标全部弃权 + top 各 1 弃权 → 每态 3 弃权、1 参评
    for r in (p, a):
        assert r["abstain"]["abstain_count"] == 3
        assert r["reader_flag_count"] == 4
        assert r["reader_scored_count"] == 1
        for m in r["matches"]:
            assert m["flag_id"] not in r["abstain"]["abstain_ids"]
        for fid in r["abstain"]["abstain_ids"]:
            assert fid not in r["reader_matched_ids"]
    # 弃权旗标 id 集与 bottom 全集 + top 弃权单一致（逐态精确）
    assert a["abstain"]["abstain_ids"] == [
        f for f in ("R4T-002", "R4B-001", "R4B-002")]
    assert p["abstain"]["abstain_ids"] == [
        f for f in ("R4T-004", "R4B-003", "R4B-004")]
    # 弃权率口径（单位=旗标条数、分母=全部旗标）
    assert a["abstain"]["abstain_rate"] == round(3 / 4, 6) == 0.75
    # unmatched 语义（无越界命名）
    for r in (p, a):
        assert "reader_false_positive_ids" not in r
        assert "reader_precision_vs_seed_gt" not in r
        assert "seed_match_rate" in r and "seed_metric_note" in r
        assert r["reader_unmatched_ids"] == ["R4T-001"] or \
            r["reader_unmatched_ids"] == ["R4T-003"] or \
            len(r["reader_unmatched_ids"]) == 1
    assert a["reader_unmatched_ids"] == ["R4T-001"]
    assert p["reader_unmatched_ids"] == ["R4T-003"]


# ---------------------------------------------------------------------------
# 预注册链、冻结顺序、仪器事实
# ---------------------------------------------------------------------------

def test_run_r4_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "render_framing_r4_preregistration",
            "observation_guidance_r4", "staging_integrity_r4",
            "render_witness_r4", "gt_reprojection_log_r4",
            "gt_seed_prep1", "gt_expansion_applied",
            "render_png_applied_top_r4", "render_png_applied_bottom_r4",
            "render_png_prep1_top_r4", "render_png_prep1_bottom_r4"} <= roles
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
    ref = rec["reference_rounds"]["r3_run"]
    assert ref["sha256"] == _sha(ref["path_rel"])


def test_staging_integrity_frozen_order_and_dev_declaration():
    integ = _load("staging-integrity-r4.json")
    # 预注册两件（framing/guidance）先于渲染落盘并固定 sha，与盘上一致
    for name, blk in integ["preregistration_hashes"].items():
        assert blk["sha256"] == _sha(blk["path_rel"]), name
    assert integ["preregistration_hashes"][
        "render-framing-r4.json"]["sha256"].startswith("7d411816")
    assert integ["preregistration_hashes"][
        "observation-guidance-r4.md"]["sha256"].startswith("c0706d0f")
    # R3 冻结链复核（frozen_artifacts_check 全 match 且逐条实测一致）
    assert integ["frozen_artifacts_check"]["all_match"] is True
    assert integ["frozen_artifacts_check"]["count"] == 10
    for r in integ["frozen_artifacts_check"]["results"]:
        assert r["match"] is True
        assert r["sha256_measured"] == r["sha256_frozen"] == _sha(
            r["path_rel"])
    # staging 拷贝零差异 + 活板见证
    for st, want in (("applied",
                      "45320fbe3296a0594a3678a30ad2c1bf775e6c7e9666158abb"
                      "82081fc2245d85"),
                     ("prep1",
                      "332c71d4362b732d0a9cdc4d82ea9f8308e4647f2e3cd2fde0b"
                      "c5497fc5a62c7")):
        assert integ["staged_copies"][st]["sha256"] == _sha(
            integ["staged_copies"][st]["path_rel"]) == want
        assert integ["staged_copies"][st]["byte_equal_to_source"] is True
        assert integ["sources"][st]["match"] is True
    # 仪器预注册声明 development 域（盲读前冻结）
    fr = _load("render-framing-r4.json")
    assert fr["evaluation_split"]["declared"] == "development"
    assert "降级为 development 证据" in fr["evaluation_split"]["basis"]
    assert fr["evaluation_split"]["protocol_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/evaluation-protocol-v1.md")
    assert fr["instrument"]["change_declaration"].startswith(
        "3D render → 2D PDF plot")
    assert "F.Courtyard" in fr["instrument"]["new_instrument"][
        "layer_lists"]["top"]
    assert fr["preregistration_order_note"]
    # 指引先于渲染冻结且无 GT 信息（无坐标/数量提示）
    guide = open(os.path.join(CAL_DIR, "observation-guidance-r4.md"),
                 encoding="utf-8").read()
    assert "GT-REVC" not in guide and "frame_box_pct_r4" not in guide
    assert "不得冒充未见留出" not in guide and "盲读纪律" in guide


def test_bottom_renders_byte_identical_and_gt_all_top():
    # 仪器事实：两态 B 面图层一致 → 两 bottom 渲染逐字节相同
    top_png = os.path.join(CAL_DIR, "renders-r4", "applied-top.png")
    bot_a = open(os.path.join(CAL_DIR, "renders-r4", "applied-bottom.png"),
                 "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r4", "prep1-bottom.png"),
                 "rb").read()
    assert hashlib.sha256(bot_a).hexdigest() == \
        hashlib.sha256(bot_p).hexdigest() == BOTTOM_PNG_SHA256
    assert bot_a != open(top_png, "rb").read()
    # witness 在案
    wit = _load("render-witness-r4.json")
    assert wit["live_board_witness"]["applied"]["unchanged"] is True
    assert wit["live_board_witness"]["applied"][
        "sha256_before_render"].startswith("45320fbe")
    recs = {r["file_rel"]: r for r in wit["renders"]}
    assert recs["out/v3-tl2/calibration/renders-r4/applied-bottom.png"][
        "sha256"] == BOTTOM_PNG_SHA256
    assert recs["out/v3-tl2/calibration/renders-r4/prep1-bottom.png"][
        "sha256"] == BOTTOM_PNG_SHA256
    for rel, r in recs.items():
        assert r["sha256"] == _sha(rel)                 # witness 全对账
    # 13 条 GT 全部 side=top（bottom 旗标无从命中，且全部弃权）
    deriv = _load("derivation-log-r4.json")
    assert all(e["side"] == "top" for e in deriv["entries"])
    rec, _ = _run_record()
    for st in ("prep1", "applied"):
        assert all(e["side"] == "top"
                   for e in rec["states"][st]["gt_entries"])
        assert rec["states"][st]["compare_v3"]["view_mismatch"] == []


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round4_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质与协议降级条款原文引用
    assert "development 域仪器迭代轮" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    # 仪器复合变更
    assert dev["instrument_change"]["nature"].startswith("复合变更")
    assert any("courtyard" in c for c in
               dev["instrument_change"]["components"])
    # 诊断结果与 run-r4 一致
    run, _ = _run_record()
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation"]["abstain_rate_total"] == 0.75
    assert dev["diagnostic_result"]["seed_metric_note"] == \
        cal.SEED_METRIC_NOTE
    # run-r4 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r4.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # 诚实结论：明确声明不做能力修复类断言；flag 产出事实在案
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.75" in hc and "development 域" in hc
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 6 and fp["non_abstain_count"] == 2
    assert fp["parse_rejections"] == []
    assert sum(fp["flag_count_by_file"].values()) == 8
    assert "冻结证据" in fp["note"]
    # 方向性观察（只描述）与下一迭代目标在案
    assert isinstance(dev["directional_observation_vs_r3"], list)
    assert len(dev["directional_observation_vs_r3"]) >= 3
    assert any("0.142857" in o or "R3" in o
               for o in dev["directional_observation_vs_r3"])
    assert dev["next_iteration_targets"]
    assert dev["is_gate"] is False


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round4-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


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
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert rec["deterministic_recompute_note"]
    assert "2026-09-06-r4" in rec["no_wallclock_note"]


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
