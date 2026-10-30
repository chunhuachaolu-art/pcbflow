"""参数化校准工具守卫（REPAIR-P4 W-2 常驻套件）。

守卫四面：
1. round 配置 fail-closed（坏 JSON/缺键/版本/kind 白名单）。
2. 三轮历史重放对账常驻（r23/r24/r25 compare 整树 canonical match +
   devrecord 整树 match——授权变更语境回放按登记件 before 值）。
3. live_sha_context_overrides 纪律：必须 guards.historical_context_only，
   否则 RoundConfigError（新轮次配置禁用历史语境覆写）。
4. 历史脚本冻结面：53 个 calibration 脚本（scripts/sNN_calibration_*）
   在本工具路径下零写盘（工具只 importlib 装载+纯函数调用）。
"""

from __future__ import annotations

import json
import os

import pytest

from pcbflow import calibration_cli as cc

ROUNDS_DIR = os.path.join(os.path.dirname(cc.__file__), "calibration_rounds")
REPO = cc.repo_root()


def _cfg_path(name):
    return os.path.join(ROUNDS_DIR, name)


# ---- 1. 配置 fail-closed ------------------------------------------------------

def test_round_config_ok_all_seven():
    for name in ("r23-compare.json", "r24-compare.json", "r25-compare.json",
                 "r23-devrecord.json", "r24-devrecord.json",
                 "r25-devrecord.json", "r25-prep.json"):
        cfg = cc.load_round_config(_cfg_path(name))
        assert cfg["round_id"] in ("r23", "r24", "r25")
        assert cfg["kind"] in ("prep", "compare", "devrecord")


def test_round_config_bad_json_fails_closed(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(cc.RoundConfigError, match="round_config_load_failed"):
        cc.load_round_config(str(p))


def test_round_config_missing_keys_fails_closed(tmp_path):
    p = tmp_path / "partial.json"
    p.write_text(json.dumps({"schema_version":
                             cc.CALIBRATION_ROUND_SCHEMA_VERSION,
                             "round_id": "r99"}), encoding="utf-8")
    with pytest.raises(cc.RoundConfigError,
                       match="round_config_missing_keys"):
        cc.load_round_config(str(p))


def test_round_config_version_and_kind_fails_closed(tmp_path):
    base = json.load(open(_cfg_path("r23-compare.json"), encoding="utf-8"))
    bad = dict(base, schema_version="9.9")
    p = tmp_path / "v.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(cc.RoundConfigError,
                       match="schema_version_mismatch"):
        cc.load_round_config(str(p))
    bad = dict(base, kind="aggregate")
    p = tmp_path / "k.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(cc.RoundConfigError, match="kind_invalid"):
        cc.load_round_config(str(p))


def test_live_sha_overrides_require_historical_guard(tmp_path):
    base = json.load(open(_cfg_path("r24-compare.json"), encoding="utf-8"))
    bad = dict(base)
    bad["guards"] = {k: v for k, v in base["guards"].items()
                     if k != "historical_context_only"}
    p = tmp_path / "guard.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    cfg = cc.load_round_config(str(p))
    with pytest.raises(cc.RoundConfigError,
                       match="historical_context_only"):
        cc.load_source_engine(cfg)


# ---- 2. 三轮历史重放对账（W-2 验收门） -----------------------------------------

@pytest.mark.parametrize("round_id", ["r23", "r24", "r25"])
def test_compare_replay_matches_frozen_run_record(round_id):
    """compare 整树重放=历史冻结 run-record canonical 逐位一致。"""
    cfg = cc.load_round_config(_cfg_path(f"{round_id}-compare.json"))
    run = cc.build_record(cfg)
    hist = json.load(open(os.path.join(REPO, cfg["record_rel"]),
                          encoding="utf-8"))
    report = cc.reconcile(run, hist, cfg)
    assert report["all_match"], report["subtrees"]
    assert run["round_id"] == hist["round_id"]
    assert run["hypothesis_test"]["verdict"] == \
        hist["hypothesis_test"]["verdict"]


@pytest.mark.parametrize("round_id", ["r23", "r24", "r25"])
def test_devrecord_replay_matches_frozen_dev_record(round_id):
    """devrecord 整树重建=历史冻结 dev-record（G0 语境回放按登记件
    before 值；其余子树全实测复算）。"""
    cfg = cc.load_round_config(_cfg_path(f"{round_id}-devrecord.json"))
    doc = cc.build_record(cfg)
    hist = json.load(open(os.path.join(REPO, cfg["record_rel"]),
                          encoding="utf-8"))
    report = cc.reconcile(doc, hist, cfg)
    assert report["all_match"], report["subtrees"]


def test_prep_skeleton_validates():
    cfg = cc.load_round_config(_cfg_path("r25-prep.json"))
    assert cc.load_source_engine(cfg) is None  # 骨架级：装载校验、无构建入口
    with pytest.raises(cc.EngineError, match="engine_entry_absistent"):
        cc.build_record(cfg)


# ---- 3. 关键聚合钉值（r25 数字面对账抽样） --------------------------------------

def test_r25_aggregate_numbers_pinned():
    """r25 聚合数字面钉值（与冻结 run-r25 record 逐值一致的抽样守卫；
    整树对账在 test_compare_replay_matches_frozen_run_record）。"""
    cfg = cc.load_round_config(_cfg_path("r25-compare.json"))
    run = cc.build_record(cfg)
    m = run["hypothesis_test"]["measurement"]
    mt = m["r25_m_tuple_6dp"]
    assert mt["M1"] == 0.433735
    assert mt["M2"] == 0.916667
    assert mt["M3"] == 22
    assert mt["M4"] == 1.0
    assert mt["split_half_M1_diff"] == 0.260377
    assert m["m4_top_rate_range_r25"] == 1.0
    assert run["gt_match_dual"]["union"]["count"] == 1
    assert run["hypothesis_test"]["verdict"] == "not_criterion_dominated"


# ---- 4. 历史脚本冻结面（零写盘；W-2 红线） --------------------------------------

def test_calibration_scripts_untouched_by_tool_runs():
    """历史 calibration 脚本族冻结复验：mtime/size/sha 与 P4 开工基线
    （out/repair-p4/scripts-mtime-baseline.json，56 件）逐件一致——
    工具路径（importlib 装载+纯函数调用）零写盘。"""
    import glob
    import hashlib
    baseline = json.load(open(os.path.join(
        REPO, "out/repair-p4/scripts-mtime-baseline.json"),
        encoding="utf-8"))["files"]
    assert len(baseline) >= 50
    for rel, want in baseline.items():
        st = os.stat(os.path.join(REPO, rel))
        assert st.st_mtime_ns == want["mtime_ns"], rel
        assert st.st_size == want["size"], rel
        got_sha = hashlib.sha256(
            open(os.path.join(REPO, rel), "rb").read()).hexdigest()
        assert got_sha == want["sha256"], rel
