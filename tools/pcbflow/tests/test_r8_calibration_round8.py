"""R8 执行包测试：reader 判读迭代第八轮收口（CAL-R8-CLOSE）——
盲读解析与视角注入 + 双态 compare_v3 重投影比对 + 分视角弃权分层 +
预注册假设 (i) 三分裁决（字母裁决唯一正式+机制观察单列+度量设计教训）+
逐旗失败通道归因（vs R7）+ development 域记录（引用 gt-audit-r1 结论）。

结构照 test_r7_calibration_round7.py 先例，仅输入与轮次常量不同
（R8=development 域单变量指引侧变更轮：零仪器变更、复用 R5 冻结渲染
件；唯一变更=判读指引 §4 存在性判断一般判据增补（系统性重复 vs 孤立
不一致启发+三路出口显式化），预注册于 r8-prep-record.json /
observation-guidance-r8.md；检验 R7 预注册候选假设 (i)）。

覆盖：
- 盲读原文（reader-raw-r8-{applied,prep1}-{top,bottom}.txt，冻结证据）：
  合法 JSON、结构（reader_id/per_image/reading_notes；flag 六键含
  location_evidence）、视角前缀一致（R8T-001..015 top 跨两文件连续、
  R8B-001..003 bottom 跨两文件连续）、拒收清单固化（全 18 旗标过
  calibration fail-closed 校验，0 拒收）、哈希与 run-r8 登记一致
  （锚 145ef24c/6bea87f5/00bd8616/81ec7f4a）；
- 视角注入确定性：s39 的图像名→视角映射纯函数两次调用一致，
  run-r8 记录的 flag_views 与该规则逐旗标一致；两波并行派发记录
  （与 R7 同模式）；读者实例披露（reader_instance_note：三实例经
  外部视觉分析工具读图=混杂因素，如实入账不作废）与分视角旗标/
  弃权计数；
- calibration-run-r8.json：盘上 canonical byte 一致；两态 compare_v3
  用记录内嵌输入（reader_flags/gt_entries/flag_views）重算 byte-exact
  一致且 view_check=full；内嵌 gt_entries=源 GT 文件条目（frame_box_pct
  ←derivation-log-r5 的 frame_box_pct_r5——渲染未变零新派生，其余
  字段逐字段原样）；聚合算术显式复算一致（1/13、1/14、4/18=0.222222）；
  分视角弃权率 top 2/15=0.133333、bottom 2/3=0.666667、分态
  applied 1/11=0.090909、prep1 3/7=0.428571；达标评估逐项复算一致
  （APR-0011：abstain_rate 0.222222≤0.5 为 R5 后首次满足该单分项、
  recall/seed 仍未达→joint=not_met）、连续达标计数 0→0、
  critic_calibration_in_range=False、域=development；
- 预注册假设 (i) 三分裁决：判据引用=r8-prep-record.json
  hypothesis_test 原文（support/reject 原样）；实测 bottom 1.0
  （12/12）→0.666667（2/3）回落但未达预注册阈值 <0.5⇒verdict=
  not_supported（字母裁决，判据复算一致）；守门通道观察（top 几何门
  面积比出局 0→0 无回升，guard_ok=True）不影响裁决；机制观察单列
  （bottom 旗标产量 12→3，化解通道绕过旗标产量，不凌驾/不改写字母
  裁决）；度量设计教训单列（未来轮预注册须测量化解通道本身，不回溯
  改判本轮）；聚合 0.222222<0.5（R5 后首次入线）如实记录于
  aggregate_context 且不改变字母裁决；分层观察（top 连续回落/bottom
  回落未达阈值）带混杂与优先声明；
- 通道归因（channel_attribution）：对 run-r7 内嵌输入与 run-r8 内嵌
  输入重放通道分类与登记一致；重放 candidate 对与两轮 compare_v3
  matches∪duplicate_reports 对拍（R7 geo=0/cat=0 → R8 geo=0/cat=1：
  R8T-010↔GT-REVC-P1-R4J3 containment 1.0 面积比 4.961299）；matches
  明细（R8T-004↔GT-REVC-AP-8-R1Q2 containment 0.838782 面积比
  2.688288=R5 后首个）可独立复算；R8 特有观察（top 庭院类旗标激增
  6 条 vs R7 1 条、R8T-014 蛇形走线「可能等长匹配」弃权、R8B-003
  整板无丝印元层弃权、prep1-bottom 旗标产量 6→1、派发词 courtyard
  计数偏差如实入账）可独立复算；
- 预注册链：r8-prep-record/guidance-r8/guidance-r7（基线）/framing-r5/
  derivation-log-r5/GT/协议/复用 PNG/冻结 PDF sha 与盘上一致
  （锚 237920a5/aad43270/9e7a7b13/860aa910/62343380/22dc7337）；阈值
  常量零覆盖（containment 0.5 / area_ratio_max 10.0 与 r7 相同）；
  gt-audit-r1 引用（1f20554a）在案；
- round8-dev-record.json：域声明、单变量指引侧变更轮性质、假设 (i)
  三分裁决节与 run-r8 一致、R7→R8 方向性观察（无能力断言、通道数值
  可独立复算）、联合评价趋势（连续计数 0→0，正式采纳门槛未达成）、
  run-r8 sha 引用一致、next_iteration_targets 引用 gt-audit-r1 结论
  （bottom GT/reroute GT/L1NB 框径三候选关闭）、is_gate=False、
  in_calibrated_range 恒 False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；受保护三文件 sha256 前 8 断言；
- s39 重跑：同参重建 byte-exact 一致 + 防覆写守卫（目标已存在即
  fail-closed 退出，零覆写）。

只读 out/（生成器模式）：零子进程/零写盘/零网络。
"""

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

ROUND_ID = "2026-09-07-r8"
DECLARED_DATE = "2026-09-07"
RAW_FILES = {
    "applied-top": "reader-raw-r8-applied-top.txt",
    "applied-bottom": "reader-raw-r8-applied-bottom.txt",
    "prep1-top": "reader-raw-r8-prep1-top.txt",
    "prep1-bottom": "reader-raw-r8-prep1-bottom.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top": "145ef24c", "applied-bottom": "6bea87f5",
    "prep1-top": "00bd8616", "prep1-bottom": "81ec7f4a",
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
#: 受保护文件（R8-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: 预注册件哈希锚（派发词给定的前 8）
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r8.md": "aad43270",
    "out/v3-tl2/calibration/r8-prep-record.json": "237920a5",
    "out/v3-tl2/calibration/observation-guidance-r7.md": "9e7a7b13",
    "out/v3-tl2/calibration/render-framing-r5.json": "860aa910",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
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


def _s39():
    spec = importlib.util.spec_from_file_location(
        "s39_calibration_r8_compare",
        os.path.join(REPO, "scripts", "s39_calibration_r8_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r8.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round8-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r8_files_valid_structure_and_prefixes():
    seen_ids = {"top": [], "bottom": []}
    expect_counts = {"applied-top": 9, "applied-bottom": 2,
                     "prep1-top": 6, "prep1-bottom": 1}
    expect_abstain = {"applied-top": 0, "applied-bottom": 1,
                      "prep1-top": 2, "prep1-bottom": 1}
    for key, name in RAW_FILES.items():
        assert _sha("out/v3-tl2/calibration/" + name).startswith(
            RAW_SHA256_FIRST8[key])                  # 与派发哈希锚一致
        d = _load(name)
        assert d["reader_id"] == "reader-r8-blind"
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        assert img["image"] == "%s.png" % key           # 图名=文件名对齐
        assert len(img["flags"]) == expect_counts[key]
        view = VIEW_OF_KEY[key]
        prefix = {"top": "R8T-", "bottom": "R8B-"}[view]
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
    # top 视 R8T-001..015 跨两文件连续（applied-top 001..009→prep1-top
    # 010..015）；bottom 视 R8B-001..003 连续（001..002→003）
    assert seen_ids["top"] == ["R8T-%03d" % i for i in range(1, 16)]
    assert seen_ids["bottom"] == ["R8B-%03d" % i for i in range(1, 4)]
    # 合计 18 旗=14 非弃权+4 弃权（派发词口径与盘面一致）
    total = sum(expect_counts.values())
    abstain = sum(expect_abstain.values())
    assert total == 18 and abstain == 4 and total - abstain == 14


def test_parse_replay_no_rejections_view_injection_and_reader_instance_note():
    s39 = _s39()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s39.RAW_FILES.items():
        parsed = s39.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s39.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则
    assert s39.view_for_image("applied-top.png") == "top"
    assert s39.view_for_image("prep1-bottom.png") == "bottom"
    assert s39.view_for_image("applied-top.png") == s39.view_for_image(
        "applied-top.png")
    try:
        s39.view_for_image("mystery.png")
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
    # 旗标计数（按 image / by_state / by_view 分层；总 18）
    fc = run["reader"]["flag_count"]
    assert fc == {"applied_top": 9, "applied_bottom": 2,
                  "prep1_top": 6, "prep1_bottom": 1,
                  "by_state": {"applied": 11, "prep1": 7},
                  "by_view": {"top": 15, "bottom": 3},
                  "abstain_by_view": {"top": 2, "bottom": 2},
                  "total": 18}
    # 两波并行派发记录（与 R7 同模式）+ 零 GT 派发词 + 编号连续
    pd = run["reader"]["parallel_dispatch"]
    assert pd["mode"] == "two_wave_parallel"
    assert pd["wave_1_parallel"] == ["applied-top", "applied-bottom"]
    assert pd["wave_2_parallel"] == ["prep1-top", "prep1-bottom"]
    assert pd["flag_id_continuity"] == {
        "top": "R8T-001..015（applied 001..009→prep1 010..015）",
        "bottom": "R8B-001..003（applied 001..002→prep1 003）"}
    assert "R6=四图独立全串行" in pd["diff_note"]
    assert "R8 与 R7 派发模式相同" in pd["diff_note"]
    assert "两波并行" in run["reader"]["dispatch_discipline"]
    assert "R8T-001..015" in run["reader"]["dispatch_discipline"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r8.md" in \
        run["reader"]["dispatch_discipline"]
    # 读者实例披露（R8 特有，如实入账不作废）
    note = run["reader"]["reader_instance_note"]
    assert "三个" in note and "analyze_image" in note and "CDN" in note
    for inst in ("applied-bottom", "prep1-top", "prep1-bottom"):
        assert inst in note
    assert "本地逐区放大" in note
    assert "混杂因素" in note and "不作废" in note


# ---------------------------------------------------------------------------
# run-r8：canonical、常量、域声明、零仪器变更、受保护文件
# ---------------------------------------------------------------------------

def test_run_r8_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r8"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r8"
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
    assert len(ic["components"]) == 1                   # 恰一项 §4 增补
    assert "存在性判断一般判据增补" in ic["components"][0]
    assert "三路出口" in ic["components"][0]
    # unchanged 与 r8-prep-record.json 登记逐字一致（锚 237920a5）
    prep = _load("r8-prep-record.json")
    assert ic["unchanged_components"] == prep["unchanged_components"]
    assert prep["no_instrument_change"] is True
    assert prep["renders_reuse"]["no_instrument_change"] is True
    assert "bottom" in ic["attribution_note"] and "字母裁决" in \
        ic["attribution_note"]
    assert "reader_instance_note" in ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r8-prep-record.json")
    # 复用 R5 渲染：零重渲染声明与四 PNG 见证（盘上 sha=prep-record 实测）
    for w in prep["renders_reuse"]["png_witness"]:
        assert w["match_to_witness_constant"] is True
        assert _sha(w["path_rel"]) == w["sha256_measured"]
    # 同日只读 GT 审计引用（1f20554a；结论=GT 侧三候选关闭）
    ref = rec["gt_audit_reference"]
    assert ref["sha256"] == _sha("out/v3-tl2/calibration/gt-audit-r1.json")
    assert ref["sha256"].startswith("1f20554a")
    assert "bottom GT=无源已关闭" in ref["note"]
    assert "reroute GT=无源已关闭" in ref["note"]
    assert "L1NB 框径=合理维持现框" in ref["note"]
    assert "非本轮预注册件" in ref["note"]
    # 受保护三文件零改动（sha256 前 8）
    for rel, want in PROTECTED_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])


def test_run_r8_compare_v3_recompute_byte_exact():
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
        # 阈值常量零覆盖（与 r7 相同的声明常量）
        assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
        assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
        assert r["metric_version"] == "calibration-metric-v3"
    # applied 态恰 1 匹配（R5 后首个 matches），明细固化
    ra = rec["states"]["applied"]["compare_v3"]
    assert [(m["flag_id"], m["gt_id"], m["containment"], m["area_ratio"])
            for m in ra["matches"]] == [
        ("R8T-004", "GT-REVC-AP-8-R1Q2", 0.838782, 2.688288)]
    assert ra["reader_matched_ids"] == ["R8T-004"]
    assert ra["gt_matched_count"] == 1
    assert ra["gt_matched"]["GT-REVC-AP-8-R1Q2"] == "R8T-004"
    assert ra["duplicate_reports"] == []
    assert ra["reader_unmatched_ids"] == [
        "R8T-001", "R8T-002", "R8T-003", "R8T-005", "R8T-006", "R8T-007",
        "R8T-008", "R8T-009", "R8B-001"]
    assert ra["abstain"]["abstain_ids"] == ["R8B-002"]
    assert "reader_false_positive_ids" not in ra
    # prep1 态零匹配（弃权 3：R8T-014/R8T-015/R8B-003）
    rp = rec["states"]["prep1"]["compare_v3"]
    assert rp["matches"] == []
    assert rp["reader_matched_ids"] == []
    assert rp["gt_matched_count"] == 0
    assert rp["duplicate_reports"] == []
    assert rp["reader_unmatched_ids"] == ["R8T-010", "R8T-011",
                                          "R8T-012", "R8T-013"]
    assert rp["abstain"]["abstain_ids"] == ["R8T-014", "R8T-015", "R8B-003"]
    assert "reader_false_positive_ids" not in rp


def test_run_r8_gt_entries_source_plus_reprojection():
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

def test_run_r8_aggregation_and_stratified_abstain():
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
    assert agg["scored_total"] == n_sc == 14
    assert agg["abstain_count_total"] == n_ab == 4
    assert agg["flag_count_total"] == n_fl == 18
    assert agg["gt_recall_total"] == round(1 / 13, 6) == 0.076923
    assert agg["seed_match_rate_total"] == round(1 / 14, 6) == 0.071429
    assert agg["abstain_rate_total"] == round(4 / 18, 6) == 0.222222
    for f in ("gt_recall_arithmetic", "seed_match_rate_arithmetic",
              "abstain_rate_arithmetic"):
        assert f in agg and isinstance(agg[f], str) and agg[f].strip()
    assert "1/13" in agg["gt_recall_arithmetic"]
    assert "1/14" in agg["seed_match_rate_arithmetic"]
    assert "4/18" in agg["abstain_rate_arithmetic"]
    assert agg["abstain_rate_definition"] == cal.ABSTAIN_RATE_DEFINITION
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE
    # 分态弃权率（applied 1/11、prep1 3/7）
    bvs = agg["abstain_rate_by_state"]
    assert bvs["applied"] == round(1 / 11, 6) == 0.090909
    assert bvs["applied_fraction"] == "1/11"
    assert bvs["prep1"] == round(3 / 7, 6) == 0.428571
    assert bvs["prep1_fraction"] == "3/7"
    # 分视角弃权率（top 2/15、bottom 2/3；分层记账如实单列）
    bvv = agg["abstain_rate_by_view"]
    assert bvv["top"] == round(2 / 15, 6) == 0.133333
    assert bvv["top_fraction"] == "2/15"
    assert bvv["bottom"] == round(2 / 3, 6) == 0.666667
    assert bvv["bottom_fraction"] == "2/3"
    assert "2/15" in agg["abstain_rate_by_view_arithmetic"]
    assert "2/3" in agg["abstain_rate_by_view_arithmetic"]


def test_run_r8_compliance_matches_recomputed():
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
    # 弃权率入线（0.222222 ≤ 0.5）：R5 后首次满足该单分项，如实 met
    assert criteria["abstain_rate_le_0.5"]["actual"] == \
        agg["abstain_rate_total"] == 0.222222
    assert criteria["abstain_rate_le_0.5"]["met"] == \
        (agg["abstain_rate_total"] <= 0.5) is True
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5", "r6",
                                     "r7", "r8"}
    assert consec["rounds"]["r7"] == "not_met（在案）"
    assert consec["rounds"]["r8"] == "not_met（本轮）"
    assert "R5 后首次满足" in consec["note"]
    # 联合评价如实（任一不满足即未达标——recall/seed 两项未达）
    all_met = all(c["met"] for c in comp["criteria"]) and consec["met"]
    assert comp["joint_evaluation"] == ("met" if all_met else "not_met")
    assert comp["joint_evaluation"] == "not_met"
    assert comp["critic_calibration_in_range"] is False   # 谓词恒 False
    assert "达标≠自动分流" in comp["critic_calibration_in_range_note"]
    assert "恒 False" in comp["critic_calibration_in_range_note"]


# ---------------------------------------------------------------------------
# 预注册假设 (i) 三分裁决（字母裁决唯一正式+机制观察+度量设计教训）
# ---------------------------------------------------------------------------

def test_run_r8_hypothesis_three_part_verdict_preregistered():
    rec, _ = _run_record()
    prep = _load("r8-prep-record.json")
    ht = rec["hypothesis_test"]
    assert ht["kind"] == "preregistered_hypothesis_test"
    assert ht["hypothesis_id"] == "r7-dev-record-candidate-i"
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r8-prep-record.json")
    # 判据引用=r8-prep-record.json hypothesis_test 原文（逐字一致）
    want = {k: prep["hypothesis_test"][k]
            for k in ("hypothesis", "support_condition", "reject_condition",
                      "test_design", "null_result_note")}
    assert ht["preregistered_criteria_quote"] == want
    assert "bottom 层弃权率 < 0.5" in want["support_condition"]
    assert "不获支持" in want["reject_condition"]
    # 实测：bottom 1.0（12/12）→0.666667（2/3），回落但未达 <0.5
    m = ht["measurement"]
    assert m["bottom_abstain_rate_r7"] == 1.0
    assert m["bottom_r7_fraction"] == "12/12"
    assert m["bottom_abstain_rate_r8"] == 0.666667
    assert m["bottom_r8_fraction"] == "2/3"
    assert m["preregistered_threshold"] == 0.5
    assert m["bottom_below_threshold"] is (0.666667 < 0.5) is False
    assert m["bottom_rate_fell"] is (0.666667 < 1.0) is True
    assert m["bottom_rate_delta"] == round(0.666667 - 1.0, 6)
    # 守门通道观察在案且不影响裁决（主通道判据单独决定）
    g = m["guard_channel"]
    assert g["guard_ok"] is True
    assert "不改变裁决" in g["note"]
    assert "0→0" in g["observation"] or "R7=0→R8=0" in g["observation"]
    # 聚合入线上下文：0.222222<0.5（R5 后首次）如实记录且不改变字母裁决
    ctx = m["aggregate_context"]
    assert ctx["abstain_rate_r7"] == 0.6
    assert ctx["abstain_rate_r8"] == 0.222222
    assert "R5 后首次" in ctx["note"]
    assert "不改变字母裁决" in ctx["note"]
    # 字母裁决=不获支持（预注册判据复算一致；唯一正式裁决）
    assert ht["verdict"] == "not_supported"
    assert "reject_condition" in ht["verdict_rule"] or \
        "未回落至 <0.5" in ht["verdict_rule"]
    assert "不获支持" in ht["verdict_text"]
    assert "唯一正式裁决" in ht["verdict_text"]
    # 机制观察单列（不凌驾字母裁决）：bottom 旗标产量 12→3、化解通道
    mo = ht["mechanism_observation"]
    assert mo["bottom_flag_production"] == {
        "r7": 12, "r7_detail": "12/12 全弃权（applied-bottom 6+"
                               "prep1-bottom 6）",
        "r8": 3, "r8_detail": "1 非弃权报告（R8B-001）+2 弃权"
                              "（R8B-002/R8B-003）"}
    assert "不凌驾" in mo["role"]
    assert "绕过旗标产量" in mo["observation"]
    assert "正常设计特征→不报告" in mo["observation"]
    assert "≠ 启发无效" in mo["conclusion"]
    assert "混杂因素" in mo["confounder_note"]
    # 机制观察独立复算：R7 bottom 12 旗全弃权、R8 bottom 3 旗=1+2
    run7 = _load("calibration-run-r7.json")
    r7_bottom = [f for st in ("prep1", "applied")
                 for f in run7["states"][st]["reader_flags"]
                 if run7["states"][st]["flag_views"][f["flag_id"]] == "bottom"]
    r8_bottom = [f for st in ("prep1", "applied")
                 for f in rec["states"][st]["reader_flags"]
                 if rec["states"][st]["flag_views"][f["flag_id"]] == "bottom"]
    assert len(r7_bottom) == 12 and all(f["abstain"] for f in r7_bottom)
    assert len(r8_bottom) == 3
    assert sorted(f["flag_id"] for f in r8_bottom if not f["abstain"]) == \
        ["R8B-001"]
    assert sorted(f["flag_id"] for f in r8_bottom if f["abstain"]) == \
        ["R8B-002", "R8B-003"]
    # 度量设计教训单列：测量化解通道本身；本轮不追溯适用
    ml = ht["metric_design_lesson"]
    assert "测量化解通道本身" in ml["lesson"]
    assert "不得回溯改判本轮" in ml["status"]
    assert "not_supported 维持" in ml["status"]
    # 分层观察如实附录 + 混杂与优先声明（字母裁决不被机制/分层改写）
    st = ht["stratified_observation"]
    assert st["top"]["r7_rate"] == 0.230769
    assert st["top"]["r7_fraction"] == "3/13"
    assert st["top"]["r8_rate"] == 0.133333
    assert st["top"]["r8_fraction"] == "2/15"
    assert st["bottom"]["r7_rate"] == 1.0
    assert st["bottom"]["r7_fraction"] == "12/12"
    assert st["bottom"]["r8_rate"] == 0.666667
    assert st["bottom"]["r8_fraction"] == "2/3"
    assert "未达预注册阈值" in st["bottom"]["direction"]
    assert "混杂因素" in st["confounder_note"]
    assert "外部视觉分析工具" in st["confounder_note"]
    assert "不得凌驾字母裁决" in st["precedence_note"]
    assert "已证因果关系" in st["precedence_note"]


# ---------------------------------------------------------------------------
# 通道归因（vs R7；重放可复核）
# ---------------------------------------------------------------------------

def test_run_r8_channel_attribution_replay_reproducible():
    s39 = _s39()
    rec, _ = _run_record()
    run7 = _load("calibration-run-r7.json")
    ca = rec["channel_attribution"]
    # 方法声明：照抄 run-r7 重放口径（同源几何原语）
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r7.json" in ca["method"]["source_of_r7_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] \
        is True
    # 重放复算（R7/R8 均用内嵌输入）与登记一致 + 对拍 compare_v3
    gt = {"prep1": rec["states"]["prep1"]["gt_entries"],
          "applied": rec["states"]["applied"]["gt_entries"]}
    for run_doc, tag in ((run7, "r7"), (rec, "r8")):
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            rp = s39.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    gt[st])
            assert s39.replay_matches_agree(rp, blk["compare_v3"])
            pairs = ca["method"]["replay_cross_check"][
                f"{tag}_{st}_candidate_pairs"]
            assert pairs == [list(p) for p in rp["candidate_pairs"]]
    # R8 applied candidate 对恰 1 且=matches（R8T-004↔AP-8）；prep1 空
    assert ca["method"]["replay_cross_check"]["r8_applied_candidate_pairs"] \
        == [["R8T-004", "GT-REVC-AP-8-R1Q2"]]
    assert ca["method"]["replay_cross_check"]["r8_prep1_candidate_pairs"] \
        == []
    # 通道分组条目（几何门 R7 0→R8 0；类别门 R7 0→R8 1）与重放一致
    def _entries(run_doc, failure):
        rows = []
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            rp = s39.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    gt[st])
            rows += [dict(e, state=st) for e in rp["entries"]
                     if e["failure"] == failure]
        return rows
    for gate, failure in (("channel_1_geometry_gate",
                           "area_ratio_rejected"),
                          ("channel_2_category_gate",
                           "category_mismatch")):
        got7 = ca[gate][f"r7_{failure}_entries"]
        got8 = ca[gate][f"r8_{failure}_entries"]
        want7 = _entries(run7, failure)
        want8 = _entries(rec, failure)
        assert got7 == want7 == []
        assert [(e["flag_id"], e["gt_id"], e["containment"],
                 e["area_ratio"]) for e in got8] == \
            [(e["flag_id"], e["gt_id"], e["containment"],
              e["area_ratio"]) for e in want8]
    c8 = ca["channel_2_category_gate"]["r8_category_mismatch_entries"]
    assert (c8[0]["flag_id"], c8[0]["gt_id"], c8[0]["category"],
            c8[0]["gt_category"], c8[0]["containment"],
            c8[0]["area_ratio"]) == ("R8T-010", "GT-REVC-P1-R4J3",
                                     "silk_readability", "courtyard_crowding",
                                     1.0, 4.961299)
    assert "0→0" in ca["channel_1_geometry_gate"]["change"]
    assert "0→1" in ca["channel_2_category_gate"]["change"]
    assert "4.961299" in ca["channel_2_category_gate"]["change"]
    assert "通道级归因，不是旗" in ca["pairing_caveat"]
    assert "不同 reader 实例" in ca["pairing_caveat"]
    # 视角门：两轮重放均空（R8 bottom 首条非弃权旗零几何近邻）
    assert ca["view_gate_observations"]["r7_entries"] == []
    assert ca["view_gate_observations"]["r8_entries"] == []
    assert "R8B-001" in ca["view_gate_observations"]["note"]
    # R8 特有观察：庭院激增+首匹配、R8T-014 蛇形弃权、R8B-003 元层弃权、
    # prep1-bottom 6→1、派发词偏差如实入账
    spec = "\n".join(ca["r8_specific_observations"])
    assert "R8T-004" in spec and "0.838782" in spec
    assert "R8T-014" in spec and "等长匹配" in spec
    assert "R8B-003" in spec and "[0.07,0.06,0.94,0.94]" in spec
    assert "6→1" in spec and "12→3" in spec
    assert "以盘面为准" in spec                     # 派发词偏差入账
    # courtyard 激增声明独立复算：R8 top 非弃权 courtyard=6、R7=1
    def _top_nonabstain_courtyard(run_doc):
        out = []
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
            out += [f["flag_id"] for f in blk["reader_flags"]
                    if f["category"] == "courtyard_crowding"
                    and f["flag_id"] not in abst
                    and blk["flag_views"][f["flag_id"]] == "top"]
        return sorted(out)
    assert _top_nonabstain_courtyard(rec) == [
        "R8T-002", "R8T-004", "R8T-006", "R8T-007", "R8T-012", "R8T-013"]
    assert _top_nonabstain_courtyard(run7) == ["R7T-003"]
    # matches 明细双条件数值独立复算（R8T-004 vs AP-8）
    blk = rec["states"]["applied"]
    f004 = next(f for f in blk["reader_flags"] if f["flag_id"] == "R8T-004")
    g = next(e for e in blk["gt_entries"]
             if e["gt_id"] == "GT-REVC-AP-8-R1Q2")
    assert round(cal._containment(f004["frame_box_pct"],
                                  g["frame_box_pct"]), 6) == 0.838782
    assert round(cal._area_ratio(f004["frame_box_pct"],
                                 g["frame_box_pct"]), 6) == 2.688288


# ---------------------------------------------------------------------------
# 预注册链、冻结哈希、阈值零覆盖
# ---------------------------------------------------------------------------

def test_run_r8_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r8_prep_record_preregistration",
            "observation_guidance_r8_preregistration",
            "observation_guidance_r7_baseline",
            "render_framing_r5_preregistration", "gt_reprojection_log_r5",
            "gt_seed_prep1", "gt_expansion_applied",
            "r7_prep_record_witness_source",
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
    # 阈值常量零覆盖（与 r7 相同；比较器本体零改动）
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "本轮零覆盖" in \
        rec["preregistration"]["comparator"]["thresholds_note"]
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    # 指引锚：本轮=guidance-r8（预注册），基线=guidance-r7
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r8.md")
    assert gp["frozen_before_render"] is True
    assert gp["frozen_before_read"] is True
    assert gp["baseline_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r7.md")
    assert "存在性判断一般判据增补" in gp["change_note"]
    # 指引内容锚：r8 指引声明恰一项变更 + 非放宽 + 三路出口
    g8 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                           "observation-guidance-r8.md"),
              encoding="utf-8").read()
    assert "存在性判断一般判据" in g8 and "三路出口" in g8
    assert "2026-09-07-r8" in g8 and "非放宽" in g8
    assert "系统性重复" in g8
    # 参照轮哈希在案（r7=上一轮基线；r8 前 run 不含本轮）
    ref7 = rec["reference_rounds"]["r7_run"]
    assert ref7["sha256"] == _sha(ref7["path_rel"])
    assert ref7["sha256"].startswith("62b34b71")
    ref6 = rec["reference_rounds"]["r6_run"]
    assert ref6["sha256"].startswith("6e6ffdf7")
    assert "r8_run" not in rec["reference_rounds"]
    # 复用渲染见证：两 bottom 渲染逐字节相同（R5 仪器事实沿用）
    bot_a = open(os.path.join(CAL_DIR, "renders-r5",
                              "applied-bottom.png"), "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r5",
                              "prep1-bottom.png"), "rb").read()
    import hashlib
    assert hashlib.sha256(bot_a).hexdigest() == \
        hashlib.sha256(bot_p).hexdigest() == BOTTOM_PNG_SHA256


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round8_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=单变量指引侧变更轮（零仪器变更）与协议降级条款原文引用
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert "零仪器变更" in dev["round_nature"]
    assert "三分结构" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert dev["instrument_change"]["nature"].startswith("零仪器变更")
    # 诊断结果与 run-r8 一致
    run, _ = _run_record()
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation"]["abstain_rate_total"] == 0.222222
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation"]["gt_recall_total"] == 0.076923
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation"]["seed_match_rate_total"] == 0.071429
    assert dev["diagnostic_result"]["seed_metric_note"] == \
        cal.SEED_METRIC_NOTE
    crit = {c["id"]: c for c in dev["diagnostic_result"]["criteria"]}
    assert crit["gt_count_ge_12"]["met"] is True
    assert crit["gt_recall_ge_0.75"]["met"] is False
    assert crit["seed_match_rate_ge_0.5"]["met"] is False
    assert crit["abstain_rate_le_0.5"]["met"] is True    # 单分项入线
    # 假设 (i) 三分裁决节与 run-r8 一致
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "not_supported"
    # 联合评价趋势：连续达标计数 0（R7 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["after_r7"]["consecutive_met_count"] == 0
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"]
    assert "不得写成已达成" in trend["note"]
    # run-r8 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r8.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # gt-audit-r1 引用与 run 一致（1f20554a）
    assert dev["gt_audit_ref"] == run["gt_audit_reference"]
    assert dev["gt_audit_ref"]["sha256"].startswith("1f20554a")
    # 诚实结论：明确声明不做能力修复类断言；flag 产出事实在案
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.222222" in hc and "development 域" in hc
    assert "0.076923" in hc and "matches=1" in hc
    assert "不获支持" in hc and "混杂" in hc
    assert "机制观察单列" in hc and "不回溯改判" in hc
    assert "in_calibrated_range" in hc
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 4 and fp["non_abstain_count"] == 14
    assert fp["abstain_rate"] == 0.222222
    assert fp["abstain_rate_by_view"]["top"] == 0.133333
    assert fp["abstain_rate_by_view"]["top_fraction"] == "2/15"
    assert fp["abstain_rate_by_view"]["bottom"] == 0.666667
    assert fp["abstain_rate_by_view"]["bottom_fraction"] == "2/3"
    assert fp["parse_rejections"] == []
    assert fp["flag_count_by_file"] == {"applied-top": 9,
                                        "applied-bottom": 2,
                                        "prep1-top": 6, "prep1-bottom": 1}
    assert sum(fp["flag_count_by_file"].values()) == 18
    assert "冻结证据" in fp["note"]
    assert fp["reader_id"] == "reader-r8-blind"
    assert "analyze_image" in fp["reader_instance_note"]
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r8 冻结工件一致
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles


def test_dev_record_observations_and_next_targets_cite_gt_audit():
    """方向性观察与下一迭代目标：通道数值可独立复算（描述性，不入
    度量）；gt-audit-r1 结论被 next_iteration_targets 引用（GT 侧三
    候选关闭）；不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    run, _ = _run_record()
    obs = "\n".join(dev["directional_observation_vs_r7"])
    # matches 与通道数值复算（R8T-004 双条件、R8T-010 类别门）
    blk = run["states"]["applied"]
    f004 = next(f for f in blk["reader_flags"] if f["flag_id"] == "R8T-004")
    g8 = next(e for e in blk["gt_entries"]
              if e["gt_id"] == "GT-REVC-AP-8-R1Q2")
    assert round(cal._containment(f004["frame_box_pct"],
                                  g8["frame_box_pct"]), 6) == 0.838782
    assert round(cal._area_ratio(f004["frame_box_pct"],
                                 g8["frame_box_pct"]), 6) == 2.688288
    assert "0.838782" in obs and "2.688288" in obs and "R8T-004" in obs
    assert "R5 后首个" in obs
    # R7→R8 分层/聚合数字在观察中如实引用
    for need in ("0.222222", "0.090909", "0.428571", "0.133333",
                 "0.666667", "4.961299", "0.076923", "0.071429",
                 "6→1", "12→3", "suspicious_reroute", "R8B-003",
                 "reader_instance_note", "以盘面为准"):
        assert need in obs, need
    nxt = "\n".join(dev["next_iteration_targets"])
    # gt-audit-r1 三候选关闭结论被引用（下一轮目标锚定其结论）
    assert "gt-audit-r1" in nxt and "1f20554a" in nxt
    assert "bottom GT=无源已关闭" in nxt
    assert "reroute GT=无源已关闭" in nxt
    assert "L1NB 框径=合理维持现框" in nxt
    assert "三候选全部关闭" in nxt
    assert "回归指引侧/渲染侧" in nxt
    # 剩余候选如实列出
    assert "courtyard" in nxt and "追踪" in nxt
    assert "等长匹配" in nxt and "R8T-014" in nxt
    assert "图层清单" in nxt                     # 渲染侧 bottom 候选
    assert "留出集" in nxt and "TBD" in nxt
    # 度量设计教训（协议侧候选，不回溯改判）
    assert "测量化解通道本身" in nxt and "不得回溯改判本轮" in nxt
    # 不得把正式采纳门槛达成写成已达成；in_calibrated_range 恒 False
    assert "in_calibrated_range 恒 False" in nxt
    assert "不得" in nxt
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r8-prep-record.json")


def test_s39_rerun_byte_identical_and_overwrite_guard():
    """s39 重跑语义：同参重建 byte-exact 一致；防覆写守卫（目标已
    存在即 fail-closed 退出，零覆写）。"""
    s39 = _s39()
    rec, disk = _run_record()
    dev, dev_disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    run_rebuilt = s39.build_run()
    assert hashing.canonical_json_bytes(run_rebuilt) == disk
    run_sha = _sha("out/v3-tl2/calibration/calibration-run-r8.json")
    dev_rebuilt = s39.build_dev_record(run_rebuilt, run_sha)
    assert hashing.canonical_json_bytes(dev_rebuilt) == dev_disk
    # 声明常量（无 wall-clock）
    assert s39.DECLARED_DATE == "2026-09-07"
    assert s39.ROUND_ID == "2026-09-07-r8"
    # 防覆写：目标两件已存在 → main 必须 fail-closed 退出（零覆写）
    before = open(os.path.join(CAL_DIR, "calibration-run-r8.json"),
                  "rb").read()
    with pytest.raises(SystemExit) as ei:
        s39.main()
    assert ei.value.code == 1
    after = open(os.path.join(CAL_DIR, "calibration-run-r8.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    dev_after = open(os.path.join(CAL_DIR, "round8-dev-record.json"),
                     "rb").read()
    assert dev_after == dev_disk                 # 字节零改动
    # run_record_ref 仍指向 run-r8 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r8.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "三路出口" in rp["abstain_semantics"]
    assert "无任何 GT" in rp["discipline"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r8-prep-record.json 先于本轮盲读落盘" in \
        rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "2026-09-07-r8" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域单变量指引侧变更轮，非留出；
    # advisory 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert dev["is_gate"] is False
    assert rec["compliance"]["critic_calibration_in_range"] is False
    assert "不是门" in dev["notes"][0]
    # 三分裁决纪律声明在案（字母裁决不被机制观察改写）
    assert "不得凌驾或改写字母裁决" in dev["notes"][-1]


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
