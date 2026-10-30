"""P3-A 会话测试：校准比较器 v3（一对一匹配+语义更名+abstain 口径）。

覆盖（对照修正包 P3-A 实现要求，全部纯内存构造，不读盘）：
- 一对一去重：三旗标同指一 GT → matches=1、duplicate_reports=2、
  seed_match_rate 按 1 计（重复报告不进正确命中分母）；
- 一对一确定性：同分（containment/面积比全等）时 flag_id/gt_id 字典序
  决定归属，两次调用 canonical 字节一致；
- 视角：flag_views 提供且 side 不符 → view_mismatch 记录+不计匹配；
  映射缺键=该旗标视角不设防（仍可匹配）+view_check=partial；
  键/值非法 ValueError（fail-closed）；
- v3 输出键契约：无 reader_false_positive_ids（含嵌套递归查）、有
  reader_unmatched_ids/seed_match_rate/seed_metric_note/abstain 块
  （abstain_ids/abstain_count/reader_flag_count/abstain_rate/
  abstain_rate_definition）；
- 阈值沿用断言：compare_v3 默认 containment_min/area_ratio_max 与
  模块声明常量逐项相等（不引入新可调阈值）；
- CLI v3 round-trip（runpy 进程内 stdin→stdout 解析回读，canonical
  字节与直接调用一致；flag_views 透传生效）+ flag_views 传给
  v1/v2 报 ValueError；未知 metric_version 拒绝；
- v1/v2 行为不变冒烟：旧键仍在（reader_false_positive_ids/
  reader_precision_vs_seed_gt/reader_abstain_ids/…）、旧语义仍在
  （v1 同 GT 可重复计入 matches；v2 面积比 >10 拒绝）；
- abstain 率算术一致性：abstain_count/reader_flag_count ==
  abstain_rate（round6），abstain 不进 scored；
- 集成锚（只读 out/）：P3-A 四新件在盘、metric_version=v3、
  flag_views=None、view_check=not_applicable、阈值=声明常量、
  两轮 matches 与 v3 复算预期一致、既有 v1/v2 归档件 hash 未变。

生成器模式：纯内存构造、零子进程、零写盘、零网络；集成锚只读。
"""

import inspect
import io
import json
import os
import runpy
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import calibration as cal           # noqa: E402
from pcbflow import hashing                      # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")


# ---------------------------------------------------------------------------
# 合成用例构造（纯内存；框坐标自造，二进制精确小数优先）
# ---------------------------------------------------------------------------

def _gt(gt_id="GT-T1", side="top", category="courtyard_crowding",
        box=None):
    return cal.build_gt_entry(
        gt_id=gt_id, category=category, side=side,
        board_box_mm=[1.0, 2.0, 3.0, 4.0],
        frame_box_pct=box if box is not None else [0.4, 0.4, 0.5, 0.6],
        drc_types=["courtyards_overlap"], cluster_refs=["R4"],
        basis_refs=["synthetic"], description="合成用例 GT")


def _flag(fid, box=(0.4, 0.4, 0.5, 0.6), category="courtyard_crowding",
          abstain=False):
    return {"flag_id": fid, "category": category, "confidence": 0.9,
            "abstain": abstain,
            "frame_box_pct": (list(box) if box is not None else None)}


def _pairs(report):
    return [(m["flag_id"], m["gt_id"]) for m in report["matches"]]


def _run_cli(payload: dict) -> dict:
    buf = io.StringIO()
    old_out, old_in = sys.stdout, sys.stdin
    sys.stdout = buf
    sys.stdin = io.StringIO(json.dumps(payload))
    try:
        runpy.run_module("pcbflow.calibration", run_name="__main__",
                         alter_sys=False)
    finally:
        sys.stdout, sys.stdin = old_out, old_in
    return json.loads(buf.getvalue())


# ---------------------------------------------------------------------------
# 1) 一对一去重：三旗标同指一 GT
# ---------------------------------------------------------------------------

def test_v3_three_flags_one_gt_dedup():
    # GT [0.4,0.4,0.5,0.6]（面积 0.02）
    # F-BIG  containment=1.0 面积比=3.0；F-MID c=1.0 ar=1.68；
    # F-SMALL c=0.6 ar=0.6 —— 三者均为候选对（v2 双条件全过）
    flags = [
        _flag("F-BIG", [0.35, 0.35, 0.55, 0.65]),
        _flag("F-MID", [0.38, 0.38, 0.52, 0.62]),
        _flag("F-SMALL", [0.42, 0.4, 0.48, 0.6]),
    ]
    r = cal.compare_v3(flags, [_gt()])
    assert _pairs(r) == [("F-MID", "GT-T1")]      # 同分 c=1.0 取面积比小者
    assert len(r["matches"]) == 1
    assert len(r["duplicate_reports"]) == 2
    assert all(d["reason"] == "gt_already_matched"
               for d in r["duplicate_reports"])
    assert sorted(d["flag_id"] for d in r["duplicate_reports"]) == \
        ["F-BIG", "F-SMALL"]
    # seed 匹配率按 1 计：1/3（重复报告不进正确命中分母）
    assert r["seed_match_rate"] == 0.333333
    assert r["reader_matched_ids"] == ["F-MID"]
    assert r["gt_matched"] == {"GT-T1": "F-MID"}
    assert r["gt_recall"] == 1.0
    # 一对一落选旗标不在 reader_matched_ids，也不得再命名 false_positive；
    # 其语义处置在 duplicate_reports（有候选对而落选≠无候选 unmatched）
    assert "reader_false_positive_ids" not in r
    assert r["reader_unmatched_ids"] == []


# ---------------------------------------------------------------------------
# 2) 一对一确定性（同分字典序；两次调用 byte 一致）
# ---------------------------------------------------------------------------

def test_v3_assignment_determinism_tiebreak_and_bytes():
    # flag_id 字典序破同分：两旗标框与 GT 全等（c=1.0、ar=1.0）
    r = cal.compare_v3([_flag("F-B2"), _flag("F-A2")], [_gt()])
    assert _pairs(r) == [("F-A2", "GT-T1")]
    assert [(d["flag_id"], d["reason"]) for d in r["duplicate_reports"]] == \
        [("F-B2", "gt_already_matched")]
    # gt_id 字典序破同分：一旗标对两个全等 GT
    gts = [_gt("GT-A2"), _gt("GT-A1")]
    r2 = cal.compare_v3([_flag("F-1")], gts)
    assert _pairs(r2) == [("F-1", "GT-A1")]
    assert r2["gt_missed_ids"] == ["GT-A2"]
    # 混合场景两次调用 canonical 字节一致（纯函数确定性）
    mixed_flags = [_flag("F-BIG", [0.35, 0.35, 0.55, 0.65]),
                   _flag("F-MID", [0.38, 0.38, 0.52, 0.62]),
                   _flag("F-A", abstain=True),
                   _flag("F-NB", [0.7, 0.7, 0.75, 0.75])]
    mixed_gts = [_gt("GT-T2"), _gt("GT-T1")]
    b1 = hashing.canonical_json_bytes(
        cal.compare_v3(mixed_flags, mixed_gts))
    b2 = hashing.canonical_json_bytes(
        cal.compare_v3(mixed_flags, mixed_gts))
    assert b1 == b2
    r3 = json.loads(b1.decode("utf-8"))
    assert _pairs(r3) == [("F-MID", "GT-T1"), ("F-BIG", "GT-T2")]
    # 落选候选（F-BIG 对 GT-T1）计入 duplicate_reports，原因=flag 已匹配
    dup = [d for d in r3["duplicate_reports"]
           if d["flag_id"] == "F-BIG" and d["gt_id"] == "GT-T1"]
    assert dup and dup[0]["reason"] == "flag_already_matched"


# ---------------------------------------------------------------------------
# 3) 视角：不符→view_mismatch+不匹配；缺键→不设防+partial
# ---------------------------------------------------------------------------

def test_v3_view_mismatch_blocks_match():
    flags = [_flag("F-V")]
    r = cal.compare_v3(flags, [_gt(side="top")],
                       flag_views={"F-V": "bottom"})
    assert r["matches"] == []
    assert r["view_mismatch"] == [
        {"flag_id": "F-V", "gt_id": "GT-T1", "flag_view": "bottom",
         "gt_side": "top"}]
    assert r["reader_unmatched_ids"] == ["F-V"]
    assert r["view_check"] == "full"       # 检查覆盖了全部可评旗标
    assert r["seed_match_rate"] == 0.0
    # 视角相符则正常匹配
    r_ok = cal.compare_v3(flags, [_gt(side="top")],
                          flag_views={"F-V": "top"})
    assert _pairs(r_ok) == [("F-V", "GT-T1")]
    assert r_ok["view_mismatch"] == []
    # bottom 视角旗标不得命中 top GT：跨视角不可比对（同类别才入围比较）
    gts = [_gt("GT-TOP", side="top", category="other_advisory"),
           _gt("GT-BOT", side="bottom", category="other_advisory")]
    r2 = cal.compare_v3([_flag("F-T", category="other_advisory")], gts,
                        flag_views={"F-T": "bottom"})
    assert _pairs(r2) == [("F-T", "GT-BOT")]


def test_v3_view_partial_unenforced():
    # 映射缺键的旗标视角不设防（如实 partial，不冒充已检查），仍可匹配
    flags = [_flag("F-V", [0.4, 0.4, 0.5, 0.6]),      # 无视角条目
             _flag("F-W", [0.4, 0.4, 0.45, 0.6])]     # 有视角条目
    r = cal.compare_v3(flags, [_gt(side="top")],
                       flag_views={"F-W": "top"})
    assert _pairs(r) == [("F-V", "GT-T1")]
    assert r["view_check"] == "partial"
    assert r["view_mapped_flag_count"] == 1
    assert r["view_eligible_flag_count"] == 2
    # 未提供映射 → not_applicable（视角不设防，如实标注）
    r_none = cal.compare_v3(flags, [_gt(side="top")])
    assert r_none["view_check"] == "not_applicable"
    r_empty = cal.compare_v3(flags, [_gt(side="top")], flag_views={})
    assert r_empty["view_check"] == "not_applicable"


def test_v3_flag_views_fail_closed():
    with pytest.raises(ValueError):
        cal.compare_v3([_flag("F-V")], [_gt()], flag_views={"F-V": "left"})
    with pytest.raises(ValueError):
        cal.compare_v3([_flag("F-V")], [_gt()], flag_views={"NOPE": "top"})
    with pytest.raises(ValueError):
        cal.compare_v3([_flag("F-V")], [_gt()], flag_views="top")
    with pytest.raises(ValueError):
        cal.compare_v3([_flag("F-V")], [_gt()], flag_views={1: "top"})


# ---------------------------------------------------------------------------
# 4) v3 输出键契约
# ---------------------------------------------------------------------------

def _assert_no_fp_key(obj, path="report"):
    if isinstance(obj, dict):
        assert "reader_false_positive_ids" not in obj, path
        assert "reader_precision_vs_seed_gt" not in obj, path
        for k, v in obj.items():
            _assert_no_fp_key(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _assert_no_fp_key(v, f"{path}[{i}]")


def test_v3_output_key_contract():
    flags = [_flag("F-M"), _flag("F-U", [0.7, 0.7, 0.75, 0.75]),
             _flag("F-NB", None), _flag("F-AB", abstain=True)]
    r = cal.compare_v3(flags, [_gt()])
    _assert_no_fp_key(r)
    assert r["metric_version"] == "calibration-metric-v3"
    assert r["reader_unmatched_ids"] == ["F-U", "F-NB"]
    assert r["reader_unmatched_no_box_ids"] == ["F-NB"]
    assert "seed_match_rate" in r and "seed_metric_note" in r
    assert "不是完整 precision/FPR" in r["seed_metric_note"]
    abst = r["abstain"]
    for k in ("abstain_ids", "abstain_count", "reader_flag_count",
              "abstain_rate", "abstain_rate_definition"):
        assert k in abst, k
    assert "单位=旗标条数" in abst["abstain_rate_definition"]
    assert "框命中不构成电气事实结论" in r["coverage_caveat"]
    for k in ("gt_recall", "gt_matched", "gt_missed_ids", "matches",
              "duplicate_reports", "view_mismatch", "view_check",
              "metric_definition", "containment_min", "area_ratio_max"):
        assert k in r, k


# ---------------------------------------------------------------------------
# 5) 阈值沿用断言（不引入新可调阈值）
# ---------------------------------------------------------------------------

def test_v3_thresholds_reuse_declared_constants():
    sig = inspect.signature(cal.compare_v3)
    assert sig.parameters["containment_min"].default == cal.CONTAINMENT_MIN
    assert sig.parameters["area_ratio_max"].default == cal.AREA_RATIO_MAX
    assert cal.CONTAINMENT_MIN == 0.5
    assert cal.AREA_RATIO_MAX == 10.0
    # v3 报告回显阈值=声明常量；v3 不新增任何阈值常量
    r = cal.compare_v3([_flag("F-M")], [_gt()])
    assert r["containment_min"] == cal.CONTAINMENT_MIN
    assert r["area_ratio_max"] == cal.AREA_RATIO_MAX
    assert "沿用 v2 声明常量未变" in r["metric_definition"]


# ---------------------------------------------------------------------------
# 6) CLI v3 round-trip + flag_views 版本守卫
# ---------------------------------------------------------------------------

_GT_CLI = _gt("GT-X-1")
_FLAGS_CLI = [_flag("F1"), _flag("F2", [0.42, 0.4, 0.48, 0.6])]


def test_cli_v3_roundtrip_and_view_passthrough():
    payload = {"reader_flags": _FLAGS_CLI, "gt_entries": [_GT_CLI],
               "metric_version": "calibration-metric-v3"}
    report = _run_cli(payload)
    assert report["metric_version"] == "calibration-metric-v3"
    # stdout 解析回读与直接调用 canonical 字节一致
    direct = cal.compare_v3(payload["reader_flags"], payload["gt_entries"])
    assert hashing.canonical_json_bytes(report) == \
        hashing.canonical_json_bytes(direct)
    # flag_views 透传生效：不符视角阻止匹配
    views = {"F1": "bottom", "F2": "bottom"}
    report_v = _run_cli(dict(payload, flag_views=views))
    assert report_v["matches"] == []
    assert len(report_v["view_mismatch"]) == 2
    assert report_v["view_check"] == "full"
    direct_v = cal.compare_v3(payload["reader_flags"],
                              payload["gt_entries"], flag_views=views)
    assert hashing.canonical_json_bytes(report_v) == \
        hashing.canonical_json_bytes(direct_v)


def test_cli_flag_views_rejected_on_v1_v2():
    base = {"reader_flags": _FLAGS_CLI, "gt_entries": [_GT_CLI],
            "flag_views": {"F1": "top"}}
    for version in ("calibration-metric-v1", "calibration-metric-v2",
                    "calibration-metric-v9"):
        old_in = sys.stdin
        sys.stdin = io.StringIO(json.dumps(dict(base,
                                                metric_version=version)))
        try:
            with pytest.raises(ValueError):
                cal.main()
        finally:
            sys.stdin = old_in
    with pytest.raises(ValueError):
        cal.compare_v3([_flag("F1")], [_GT_CLI], area_ratio_max=0)


# ---------------------------------------------------------------------------
# 7) v1/v2 行为不变冒烟（旧键仍在、旧语义仍在）
# ---------------------------------------------------------------------------

def test_v1_v2_smoke_unchanged():
    gts = [_gt()]
    two_same = [_flag("F-P1"), _flag("F-P2")]
    r1 = cal.compare(two_same, gts)
    assert r1["metric_version"] == "calibration-metric-v1"
    assert len(r1["matches"]) == 2          # v1 语义：同 GT 可重复命中
    assert {m["flag_id"] for m in r1["matches"]} == {"F-P1", "F-P2"}
    for k in ("reader_false_positive_ids", "reader_precision_vs_seed_gt",
              "reader_abstain_ids", "reader_matched_ids",
              "reader_unmatched_no_box_ids", "gt_recall", "gt_matched"):
        assert k in r1, k
    assert "seed_match_rate" not in r1
    # v2：面积比 ≤10 过、>10 拒（整板大框型），旧键仍在
    r2 = cal.compare_v2([_flag("F-NB", [0.4, 0.4, 0.45, 0.6]),
                         _flag("F-WHOLE", [0.2, 0.2, 0.7, 0.7])], gts)
    assert r2["metric_version"] == "calibration-metric-v2"
    assert _pairs(r2) == [("F-NB", "GT-T1")]
    assert r2["reader_ratio_rejected_ids"] == ["F-WHOLE"]
    for k in ("reader_false_positive_ids", "reader_precision_vs_seed_gt",
              "area_ratio_max", "area_ratio_max_rationale"):
        assert k in r2, k
    assert "seed_match_rate" not in r2


# ---------------------------------------------------------------------------
# 8) abstain 率算术一致性
# ---------------------------------------------------------------------------

def test_v3_abstain_rate_arithmetic():
    flags = [_flag("F-M"), _flag("F-A1", abstain=True),
             _flag("F-A2", abstain=True),
             _flag("F-U", [0.7, 0.7, 0.8, 0.8]),
             _flag("F-M2", [0.41, 0.41, 0.49, 0.59])]
    r = cal.compare_v3(flags, [_gt()])
    abst = r["abstain"]
    assert abst["abstain_ids"] == ["F-A1", "F-A2"]
    assert abst["abstain_count"] == 2
    assert abst["reader_flag_count"] == 5
    assert abst["abstain_rate"] == round(2 / 5, 6) == 0.4
    assert r["reader_scored_count"] == 3
    assert r["seed_match_rate"] == round(
        len(r["matches"]) / r["reader_scored_count"], 6)
    # abstain 旗标不参与匹配、不入 unmatched
    assert "F-A1" not in r["reader_unmatched_ids"]
    assert r["reader_unmatched_ids"] == ["F-U"]


def test_v3_abstain_zero_denominator():
    r = cal.compare_v3([], [_gt()])
    assert r["abstain"]["reader_flag_count"] == 0
    assert r["abstain"]["abstain_rate"] is None
    assert r["seed_match_rate"] is None
    assert r["gt_recall"] == 0.0


# ---------------------------------------------------------------------------
# 集成锚（只读 out/）：P3-A 落盘件与既有归档件
# ---------------------------------------------------------------------------

def test_p3a_artifacts_on_disk():
    cal_dir = os.path.join(REPO, "out", "v3-tl2", "calibration")

    def _load(name):
        with open(os.path.join(cal_dir, name), encoding="utf-8") as f:
            return json.load(f)

    on_r1 = _load("calibration-run-v3-on-r1-inputs.json")
    on_r2 = _load("calibration-run-v3-on-r2-inputs.json")
    selfchk = _load("calibration-metric-v3-selfcheck.json")
    for doc in (on_r1, on_r2):
        assert doc["metric_version"] == "calibration-metric-v3"
        assert doc["flag_views"] is None
        assert doc["view_check"] == "not_applicable"
        assert doc["report"]["containment_min"] == cal.CONTAINMENT_MIN
        assert doc["report"]["area_ratio_max"] == cal.AREA_RATIO_MAX
        _assert_no_fp_key(doc)
    assert _pairs(on_r1["report"]) == [("F-012", "GT-REVC-P1-L1SHORT")]
    assert on_r1["report"]["gt_recall"] == 0.25
    assert on_r1["report"]["seed_match_rate"] == 0.1
    assert _pairs(on_r2["report"]) == [("F-009", "GT-REVC-P1-R4J3")]
    assert on_r2["report"]["gt_recall"] == 0.25
    assert on_r2["report"]["seed_match_rate"] == 0.142857
    assert selfchk["kind"] == "tl2_calibration_metric_v3_selfcheck"
    assert selfchk["thresholds_unchanged_from_v2"] is True
    # 既有 v1/v2 归档件 hash 未变（零覆写）
    sha_run1 = hashing.sha256_file(os.path.join(
        cal_dir, "calibration-run-v1.json"))
    sha_run2 = hashing.sha256_file(os.path.join(
        cal_dir, "calibration-run-v2.json"))
    sha_gt = hashing.sha256_file(os.path.join(
        cal_dir, "ground-truth-v1.json"))
    assert sha_run1.startswith("ff60a7bb")
    assert sha_run2.startswith("c3ea9a2e")
    assert sha_gt.startswith("828b6b5f")
