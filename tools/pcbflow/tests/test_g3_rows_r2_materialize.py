"""G3 rows-r2 物化批测试（包 G3；批产物级对账面）。

覆盖（G3 任务书⑫ 对应）：
- replay 字节一致：replay-check.json 全对 + 同进程单板内存重算抽查；
- rows-r1/metrics-r1 零触碰断言（合集 hash 锚 + batch-summary 锚）；
- 全量行 schema 校验（observation-row-v1，37 板逐行）；
- split-registry-r2 对账（datasets manifest tier 派生全等、validation=0
  如实、holdout=6、leakage 整组同侧、manifest_ref sha 锚）；
- 4 板教训型回退 null+reason 逐字断言（sidecar fail_closed 行 +
  主行 rails/padload facet）；
- H1–H6 holdout role 标签断言 + H6 亲和警示逐字携带；
- 保护三文件 sha256 零变化；
- run_id/schema_binding/守恒式/r2_pending 常量对账。

探针级用例只读（零写入/零网络/零 wall-clock）；内存重算抽查沿
pcbflow.observation 纯函数路径（与 batch-build 同构），不落盘。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import actual_ext as ae, check_stage, corpus_convert_ext as cce
from pcbflow import hashing, observation as obs
from pcbflow import observation_align_ext as oae, schemas

ROOT = os.path.join(os.path.dirname(__file__), "..")
R2 = os.path.join(ROOT, "out", "v3-obs", "rows-r2")
ROWS_MAIN = os.path.join(R2, "rows", "main")
ESCAPE_DIR = os.path.join(R2, "align", "escape-agreement")
LC_DIR = os.path.join(R2, "align", "lc-demand-fit")
DS_MANIFEST = os.path.join(ROOT, "datasets", "corpus-r2-r1", "manifest.json")

# ---- 冻结件锚（动工前实测；完工后由本测试钉住零变化） ----------------------
ROWS_R1_COLL_SHA = "40ab46b2e9745ea3742eacbb77f588c7ab61c3dba7c36a1f9539a0a9acced3a7"
METRICS_R1_COLL_SHA = "6e08040419007bd631f6845a8de48fc21ceec58b1c6f9a5f2af7d22c6f7f1719"
ROWS_R1_SUMMARY_SHA = ("eb7d68d0003d43dde05adbd04a8d845b82f5e96ae306872"
                       "2c114ad32e1fe6643")
FFEXT_R1_SUMMARY_SHA = ("7471bc6885eaa223ff52c7f6073b183f909edc9725e3ee"
                        "58117bc9a44ffc12df")

# ---- 保护三文件 -------------------------------------------------------------
PROTECTED = {
    "pcbflow/cli.py": "3bfc940701d1be82029877583a0a41f49741228f2e89a321b7dafa98d179aae8",
    "pcbflow/config.py": "8ad12b3fab12f19546034b5421aa77053f4115b91b36b87b9dfabc9075fdcf82",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd896d9301690b3d",
}

# ---- 4 板教训型 verbatim ActualExtError（动工前探针捕获；fail-closed 原文） --
FAIL_CLOSED_VERBATIM = {
    "corpusr2-om-flexgrid-v4-rigid-pcb":
        "pad[SW_RST1.2]: 名绑定档出现数字/非字符串 net token: '100'"
        "（绑定档错配 fail-closed——数字 id 形态属 id 档，请改用 "
        "binding='net_id_bound'）",
    "corpusr2-tinytapeout-demo":
        "segment: segment layer 'In1.Cu' 非铜层声明层（未知层 fail-closed）",
    "corpusr2-jetson-nano-baseboard":
        "segment: segment layer 'In5.Cu' 非铜层声明层（未知层 fail-closed）",
    "corpusr2-anthc":
        "segment: segment layer 'B.Cu' 非铜层声明层（未知层 fail-closed）",
}
FAIL_BOARDS = sorted(FAIL_CLOSED_VERBATIM)

# LC 行型专属 fail-closed（弧长求值面；escape 口径不涉弧长故该板 escape ok）
LC_FAIL_CLOSED_VERBATIM = dict(FAIL_CLOSED_VERBATIM) | {
    "corpusr2-thunderbolt-pcie-adapter":
        "arc[58]: arc 三点半径数值不自洽（超字面量噪声容差，fail-closed）",
}

# dual_form vs check_stage via 计数失配（net id 0 via 元素；定因锚）
VIAS_MISMATCH = {
    "corpusr2-dc-scm-rot-jumper-card":
        {"dual_vias": 47, "check_stage_vias": 48, "net_id_0_vias": 1},
    "corpusr2-thatmicpre-v2":
        {"dual_vias": 5, "check_stage_vias": 21, "net_id_0_vias": 16},
}

# ---- H6 亲和警示（R22/G1 ledger 逐字） --------------------------------------
H6_CAVEAT = ("与语料 kicaddemo-jetson-agx-thor-baseboard 同厂商同产品线"
             "（不同代际/repo）——采纳时接受厂商亲和性混杂")

HOLDOUT_POOL = [
    ("H1", "kria-k26-devboard"), ("H2", "sdi-mipi-bridge"),
    ("H3", "hackrf-one"), ("H4", "pslab-v6"),
    ("H5", "scalenode-cm4-baseboard"), ("H6", "jetson-nano-baseboard"),
]


def _coll_sha(root_abs):
    """目录合集 hash（排序 'sha256  relpath' 行连接；与动工前清单同构）。"""
    entries = []
    for dirpath, _dirnames, filenames in os.walk(root_abs):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, ROOT).replace(os.sep, "/")
            with open(fp, "rb") as f:
                entries.append(f"{hashlib.sha256(f.read()).hexdigest()} *{rel}")
    entries.sort()
    return hashlib.sha256(
        ("\n".join(entries) + "\n").encode("utf-8")).hexdigest()


def _load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def summary():
    return _load("out/v3-obs/rows-r2/batch-summary.json")


@pytest.fixture(scope="module")
def split_registry():
    return _load("out/v3-obs/rows-r2/split-registry-r2.json")


@pytest.fixture(scope="module")
def ds_manifest():
    return _load("datasets/corpus-r2-r1/manifest.json")


# ---- 保护面 / 冻结件零触碰 ---------------------------------------------------

@pytest.mark.parametrize("rel,expect", sorted(PROTECTED.items()))
def test_protected_three_files_unchanged(rel, expect):
    with open(os.path.join(ROOT, rel), "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == expect


def test_rows_r1_frozen_collection_unchanged():
    assert _coll_sha(os.path.join(ROOT, "out", "v3-obs", "rows-r1")) \
        == ROWS_R1_COLL_SHA


def test_metrics_r1_frozen_collection_unchanged():
    assert _coll_sha(os.path.join(ROOT, "out", "v3-obs", "metrics-r1")) \
        == METRICS_R1_COLL_SHA


def test_r1_batch_summary_anchors_unchanged():
    with open(os.path.join(ROOT, "out/v3-obs/rows-r1/batch-summary.json"),
              "rb") as f:
        assert hashing.sha256_file(
            "out/v3-obs/rows-r1/batch-summary.json") == ROWS_R1_SUMMARY_SHA
    assert hashing.sha256_file(
        "out/v3-ext-r1/ffext-r1/batch-summary.json") == FFEXT_R1_SUMMARY_SHA


# ---- 批台账 / split registry 对账 --------------------------------------------

def test_batch_summary_shape_and_counts(summary):
    assert summary["batch_id"] == "obs-rows-r2"
    assert summary["run_id"] == "obs-rows-r2"
    assert summary["declared_date"] == "2026-09-12"
    assert summary["boards_total"] == 37
    assert summary["boards_failed"] == []
    assert summary["pool_counts"] == {"main": 37}
    assert summary["split_counts"] == {"holdout": 6, "train": 31}
    assert summary["validation_r2"] == 0
    assert summary["schema_binding"]["schema_name"] == "observation-row-v1"
    assert summary["schema_binding"]["registry_version"] == "3.0"
    assert summary["schema_binding"]["schema_hash"] == \
        schemas.schema_hash("observation-row-v1")


def test_rows_schema_valid_all_boards(summary):
    total = 0
    for b in summary["boards"]:
        with open(b["rows_file"]["path"], encoding="utf-8") as f:
            rows = json.load(f)
        assert b["rows_file"]["rows_total"] == len(rows)
        for row in rows:
            errs = schemas.validate("observation-row-v1", row)
            assert not errs, (b["profile_id"], row["observation_id"], errs[:3])
            assert row["run_id"] == "obs-rows-r2"
        total += len(rows)
    assert total == summary["rows_total"]


def test_split_registry_matches_dataset_manifest(split_registry, ds_manifest):
    assert split_registry["artifact_kind"] == "observation_split_registry"
    assert split_registry["split_counts"] == {
        "train": 31, "validation": 0, "holdout": 6}
    assert split_registry["dataset_splits"]["validation"] == []
    # tier 派生全等（CORPUS_R2_TIER_ROLE 单一事实源）
    expect = {"train": [], "validation": [], "holdout": []}
    for b in ds_manifest["boards"]:
        expect[cce.CORPUS_R2_TIER_ROLE[b["tier_designation"]]].append(
            b["board_id"])
    for role in expect:
        assert sorted(expect[role]) == \
            split_registry["dataset_splits"][role]
    # manifest_ref 锚
    assert split_registry["manifest_ref"]["sha256"] == hashing.sha256_file(
        "datasets/corpus-r2-r1/manifest.json")
    # holdout 池 H1–H6 + H6 caveat 逐字
    pool = split_registry["holdout_pool"]
    assert [(h["pool_id"], h["board_id"]) for h in pool] == HOLDOUT_POOL
    h6 = next(h for h in pool if h["pool_id"] == "H6")
    assert h6["caveat"] == H6_CAVEAT
    # leakage 整组同侧 + project_group 原样
    assert split_registry["leakage_same_side_all"] is True
    groups = split_registry["leakage_groups"]
    by_board = {b["board_id"]: b["project_group"]
                for b in ds_manifest["boards"]}
    assert set(groups) == set(by_board.values())
    for g, entry in groups.items():
        assert all(by_board[b] == g for b in entry["boards"])
    fm4dd = groups["fm4dd-pmod-family"]
    assert sorted(fm4dd["boards"]) == ["pmod-bme280", "pmod-crypto",
                                       "pmod-i2c24io"]
    assert fm4dd["roles"] == ["train"] and fm4dd["same_side"] is True
    # disposition 计数与 manifest 对账
    assert split_registry["disposition_counts"] == {
        "optional": 22, "retain": 13, "retain-conditional": 2}


def test_holdout_role_labels_in_rows(summary):
    holdout_pids = {f"corpusr2-{bid}" for _h, bid in HOLDOUT_POOL}
    train_count = holdout_count = 0
    for b in summary["boards"]:
        rows = json.load(open(b["rows_file"]["path"], encoding="utf-8"))
        roles = {r["split"]["role"] for r in rows}
        assert len(roles) == 1
        role = roles.pop()
        assert role == b["split_role"]
        if b["profile_id"] in holdout_pids:
            assert role == "holdout" and b["pool"] == "main"
            assert b["holdout_pool_id"] in {"H1", "H2", "H3", "H4", "H5",
                                            "H6"}
            holdout_count += 1
        else:
            assert role == "train"
            train_count += 1
    assert (train_count, holdout_count) == (31, 6)


def test_holdout_governance_h6_caveat_verbatim(summary):
    pool = summary["governance"]["holdout_pool"]
    assert [(h["pool_id"], h["board_id"]) for h in pool] == HOLDOUT_POOL
    h6 = next(h for h in pool if h["pool_id"] == "H6")
    assert h6["caveat"] == H6_CAVEAT
    warns = "\n".join(summary["governance"]["cross_library_affinity_warnings"])
    assert "tinytapeout-demo" in warns and "ottercast-audio-v2" in warns \
        and "jetson-nano-baseboard" in warns


# ---- 4 板教训型回退：null+reason 逐字断言 ------------------------------------

# E-3（PREREG-RESOURCE-CALIBRATION-R2-frozen §5）合规变体：rows-r2 冻结件
# 内嵌 LC convention 缺句末「。」（单字节差、语义恒同），零重生成——冻结
# sidecar 与活库常量比对时按本变体对齐（=canonical 去句末句号）。
LC_SIDECAR_VERBATIM_E3_VARIANT = oae.CONVENTION_VERBATIM_LAYER_CAPACITY[:-1]


def _board_rows(pid):
    with open(os.path.join(ROWS_MAIN, f"{pid}.json"),
              encoding="utf-8") as f:
        return json.load(f)


def test_failclosed_sidecar_rows_null_reason_verbatim():
    for pid, msg in FAIL_CLOSED_VERBATIM.items():
        for sub, kind in ((ESCAPE_DIR, "pad_escape_agreement"),
                          (LC_DIR, "lc_demand_fit")):
            with open(os.path.join(sub, f"{pid}.json"),
                      encoding="utf-8") as f:
                row = json.load(f)
            assert row["status"] == "fail_closed"
            assert row["row_kind"] == kind
            assert row["value"] is None
            # 不硬造、不跳过、不留空串（reason 非空字符串逐字携带）
            assert isinstance(row["not_available_reason"], str)                 and row["not_available_reason"]
            assert row["error"]["exception_type"] == "ActualExtError"
            assert row["error"]["message_verbatim"] == msg  # 逐字
            assert row["not_available_reason"] == f"ActualExtError: {msg}"
            assert row["convention_verbatim"] == (
                oae.CONVENTION_VERBATIM_PAD_ESCAPE
                if kind == "pad_escape_agreement"
                else LC_SIDECAR_VERBATIM_E3_VARIANT)
            assert row["r2_pending"] is True
            assert row["r2_pending_note"] == oae.R2_PENDING_NOTE
            assert row["profile_id"] == pid
            assert row["split_role"] in ("train", "holdout")


def test_lc_failclosed_extra_board_thunderbolt():
    with open(os.path.join(LC_DIR,
                           "corpusr2-thunderbolt-pcie-adapter.json"),
              encoding="utf-8") as f:
        row = json.load(f)
    msg = LC_FAIL_CLOSED_VERBATIM["corpusr2-thunderbolt-pcie-adapter"]
    assert row["status"] == "fail_closed"
    assert row["error"]["message_verbatim"] == msg
    assert row["not_available_reason"] == f"ActualExtError: {msg}"
    assert row["convention_verbatim"] == LC_SIDECAR_VERBATIM_E3_VARIANT
    assert row["ffext_layer_demand_value"] is not None
    # 同板 escape 行为 ok（escape 口径不涉弧长求值）
    with open(os.path.join(ESCAPE_DIR,
                           "corpusr2-thunderbolt-pcie-adapter.json"),
              encoding="utf-8") as f:
        assert json.load(f)["status"] == "ok"


def test_align_manifest_fail_closed_ledger_covers_both_kinds():
    with open(os.path.join(R2, "align", "manifest.json"),
              encoding="utf-8") as f:
        mf = json.load(f)
    ledger = mf["fail_closed_ledger"]
    expect = [{"row_kind": "pad_escape_agreement", "profile_id": pid,
               "message_verbatim": msg}
              for pid, msg in FAIL_CLOSED_VERBATIM.items()]
    expect += [{"row_kind": "lc_demand_fit", "profile_id": pid,
                "message_verbatim": msg}
               for pid, msg in LC_FAIL_CLOSED_VERBATIM.items()]
    expect.sort(key=lambda e: (e["row_kind"], e["profile_id"]))
    assert ledger == expect
    assert len(ledger) == 9


def test_failclosed_main_rows_facet_fallback(summary):
    for b in summary["boards"]:
        pid = b["profile_id"]
        rows = _board_rows(pid)
        rails = [r for r in rows if r["row_id"].startswith("rails:")]
        padload = [r for r in rows
                   if r["row_id"].startswith("signal_layer_pad_load:")]
        via_rows = [r for r in rows if r["row_id"].startswith("via_budget:")]
        if pid in FAIL_BOARDS:
            msg = FAIL_CLOSED_VERBATIM[pid]
            # pad 账 facet：rails 全 null，verbatim 错误在 actual_source
            assert rails and all(r["actual"]["value"] is None
                                 for r in rails)
            for r in rails:
                assert msg in r["actual_source"]["authority"]
            # padload facet：全 null + reason 逐字（R6② 转记）
            assert padload and all(r["actual"]["value"] is None
                                   for r in padload)
            for r in padload:
                assert msg in r["actual"]["not_available_reason"]
            # via facet：回退解析器诚实计数（非负 int，在批台账）
            assert len(via_rows) == 1
            assert via_rows[0]["actual"]["value"] == \
                b["routed_account"]["vias"]
            assert b["routed_account_fail_closed"] is True
            assert b["routed_account"]["pad_account_sum"] is None
        else:
            # 33 OK 板：routed 账面全通过（U-R2-5 双形态账源生效）
            assert b["routed_account_fail_closed"] is False
            assert b["routed_account"]["pad_account_sum"] > 0
            assert len(via_rows) == 1
            assert via_rows[0]["actual"]["value"] == \
                b["routed_account"]["vias"]


def test_pad_account_switch_effect_nonzero(summary):
    """U-R2-5 改善实证：footprint 形态板 rails actual 非零（usb-gigabit）。"""
    rows = _board_rows("corpusr2-usb-gigabit-rev-e")
    rails = [r for r in rows if r["row_id"].startswith("rails:")]
    assert rails and all(r["actual"]["value"] > 0 for r in rails)
    assert all(r["actual_source"]["authority"].startswith(
        "reference_routed_board_text_count（parser=actual_ext."
        "parse_routed_geometry_dual_form") for r in rails)


def test_failclosed_ledger_in_artifacts(summary):
    ra = summary["routed_account"]
    assert sorted(ra["fail_closed_boards"]) == FAIL_BOARDS
    for pid, msg in FAIL_CLOSED_VERBATIM.items():
        assert ra["fail_closed_verbatim_errors"][pid] == msg
    assert sorted(summary["r62_failclosed_boards"]) == FAIL_BOARDS
    assert ra["parser_kind_counts"] == {
        "by_net_name": 2, "dual_form": 31,
        "fallback_id_check_stage": 2, "fallback_name_sexpr_count": 2}
    # dual vs check_stage via 计数失配=net id 0 via 元素（披露②证据）
    dvc = ra["dual_form_vs_check_stage"]
    assert dvc["boards_compared"] == 31
    assert dvc["vias_equal_boards"] == 29
    assert dvc["vias_mismatch_boards"] == VIAS_MISMATCH
    assert dvc["unbound_delta_boards"]["corpusr2-teres-pcb1-a64-main-rev-c"]         == 51  # G2b 披露② teres 51 元素差复现
    # sidecar 行型级 fail 板清单（LC 面>escape 面：弧长求值专属）
    asc = summary["align_sidecar"]
    assert sorted(asc["escape_failclosed_boards"]) == FAIL_BOARDS
    assert sorted(asc["lc_failclosed_boards"]) == sorted(LC_FAIL_CLOSED_VERBATIM)
    assert asc["row_kind_totals"]["pad_escape_agreement"] ==         {"total": 37, "ok": 33, "fail_closed": 4}
    assert asc["row_kind_totals"]["lc_demand_fit"] ==         {"total": 37, "ok": 32, "fail_closed": 5}


# ---- align sidecar 结构 / 守恒 / r2_pending ----------------------------------

def test_sidecar_inventory_and_manifest_consistency(summary):
    with open(os.path.join(R2, "align", "manifest.json"),
              encoding="utf-8") as f:
        mf = json.load(f)
    assert mf["artifact_kind"] == "observation_align_sidecar_manifest"
    # r2_pending 声明：manifest 自述文本 + summary 结构化键 + 每行结构化键
    assert "r2_pending=True" in mf["self_description"]
    assert summary["align_sidecar"]["r2_pending"] is True
    assert mf["conservation_rule"].startswith("escape ok 行守恒式")
    for kind, sub in (("pad_escape_agreement", ESCAPE_DIR),
                      ("lc_demand_fit", LC_DIR)):
        inv = mf["inventory"][kind]
        assert len(inv) == 37
        ok = failc = 0
        for pid, entry in inv.items():
            expect_rel = os.path.relpath(
                os.path.join(sub, f"{pid}.json"), ROOT).replace(os.sep, "/")
            assert entry["path"] == expect_rel
            with open(entry["path"], "rb") as f:
                assert hashing.sha256_bytes(f.read()) == entry["sha256"]
            if entry["status"] == "ok":
                ok += 1
            else:
                failc += 1
        totals = summary["align_sidecar"]["row_kind_totals"][kind]
        assert totals == {"total": 37, "ok": ok, "fail_closed": failc}


def test_escape_ok_rows_conservation_and_r2_pending():
    for fn in sorted(os.listdir(ESCAPE_DIR)):
        with open(os.path.join(ESCAPE_DIR, fn), encoding="utf-8") as f:
            row = json.load(f)
        if row["status"] != "ok":
            continue
        res = row["result"]
        s = res["summary"]
        assert (s["pads_both_defined"] + s["pads_pred_only"]
                + s["pads_actual_only"] + s["pads_undefined_both"]
                == s["pads_total"] == len(res["pads"]))
        assert row["summary_conservation_ok"] is True
        assert res["r2_pending"] is True
        assert res["r2_pending_note"] == oae.R2_PENDING_NOTE
        assert res["convention_verbatim"] == oae.CONVENTION_VERBATIM_PAD_ESCAPE


def test_lc_ok_rows_shape_and_demand_pairing():
    for fn in sorted(os.listdir(LC_DIR)):
        with open(os.path.join(LC_DIR, fn), encoding="utf-8") as f:
            row = json.load(f)
        if row["status"] != "ok":
            continue
        res = row["result"]
        assert res["actual"]["unit"] == "mm2"
        assert res["r2_pending"] is True
        assert res["r2_pending_note"] == oae.R2_PENDING_NOTE
        assert res["convention_verbatim"] == LC_SIDECAR_VERBATIM_E3_VARIANT
        assert res["E"] == round(res["actual"]["value"]
                                 - row["ffext_layer_demand_value"], 3)
        assert row["pred_recomputed_equals_plan_value"] in (True, False)


# ---- replay 对账（跨进程字节一致 + 内存重算抽查） ----------------------------

def test_replay_check_all_byte_exact():
    with open(os.path.join(R2, "replay-check.json"), encoding="utf-8") as f:
        rc = json.load(f)
    assert rc["batch_id"] == "obs-rows-r2"
    assert rc["mode"] == "replay"
    assert rc["in_process_double_build_pairs"] == 37
    assert rc["pairs_total"] >= 75  # 37 rows + 74 sidecar + registry + manifest + summary
    assert rc["all_byte_exact"] is True
    assert all(p["byte_exact"] for p in rc["pairs"])


def _recompute_board_bytes(pid):
    """单板内存重算（batch-build 同构路径；纯函数，零落盘）。返回主行
    canonical bytes 与 sidecar 行 bytes，供与盘面逐字节比对。

    进程内切换 obs.RUN_ID 批身份并在 finally 恢复原值——防模块级状态
    污染其他测试文件（test_observation.py 对库常量 "obs-rows-r1" 有
    依赖；完工全量首轮曾因未恢复出现 1 例污染失败，已修复并复跑）。"""
    original_run_id = obs.RUN_ID
    try:
        return _recompute_board_bytes_inner(pid)
    finally:
        obs.RUN_ID = original_run_id


def _recompute_board_bytes_inner(pid):
    obs.RUN_ID = "obs-rows-r2"  # 与 batch-build 同一批身份（脚本头披露）
    rc = _load(f"profiles/{pid}/route-check.json")
    ds = _load("datasets/corpus-r2-r1/manifest.json")
    rec = {"profile_id": pid, "board_id": rc["board_id"],
           "dataset_role": rc["dataset_role"],
           "reference_path": rc["reference_route"]["path"],
           "reference_sha256": rc["reference_route"]["sha256"]}
    rec = cce.reconcile_corpus_r2_board_record(rec, ds)
    rec["ff_plan_rel"] = f"profiles/{pid}/derived/feedforward-plan.json"
    rec["manifest_ref"] = {
        "path": "datasets/corpus-r2-r1/manifest.json",
        "sha256": hashing.sha256_file(
            "datasets/corpus-r2-r1/manifest.json")}
    rec["leakage_group"] = rec["governance"]["project_group"]
    board_rel = os.path.join(ROOT, rec["board_path_rel"])
    with open(board_rel, encoding="utf-8") as f:
        text = f.read()
    ff = _load(rec["ff_plan_rel"])
    ext = _load(f"out/v3-gline-r2/ffext-r2/plans/{pid}.json")
    registry = _load(rec["registry_rel"])
    pad_geo = cce.extract_pad_geometry(text)
    registry = dict(registry)
    registry["_pad_count"] = len(pad_geo["pads"])
    registry["_footprint_count"] = len(pad_geo["footprints"])
    binding = cce.detect_binding(text)
    if binding == ae.BINDING_ID:
        geo = ae.parse_routed_geometry_dual_form(text, binding=binding)
        routed = {"per_net_by_name": geo["per_net"],
                  "geometry_counts": geo["geometry_counts"],
                  "parser": "actual_ext.parse_routed_geometry_dual_form"
                            "（U-R2-5 双形态账源，net_id_bound）"}
    else:
        geo = ae.parse_routed_geometry_by_net_name(text)
        routed = {"per_net_by_name": geo["per_net"],
                  "geometry_counts": geo["geometry_counts"],
                  "parser": "actual_ext.parse_routed_geometry_by_net_name"
                            "（net_name_bound）"}
    r62r = ae.count_pads_per_layer(text, binding=binding)
    rows = obs.build_board_rows(
        record=rec, board_sha256=hashing.sha256_file(board_rel),
        registry_sha256=hashing.sha256_file(rec["registry_rel"]),
        constraints_sha256=hashing.sha256_file(
            f"profiles/{pid}/inputs/constraints.json"),
        registry_obj=registry, leakage_group=rec["leakage_group"],
        split_role=rec["split_role"], manifest_ref=rec["manifest_ref"],
        ff_corpus_plan=ff, ext_plan=ext, routed_counts=routed,
        r62={"ok": True, "per_layer": r62r["per_layer"]})
    return hashing.canonical_json_bytes(rows)


@pytest.mark.parametrize("pid", ["corpusr2-badgeleds-do-electronics",
                                 "corpusr2-tmp108"])
def test_in_memory_recompute_byte_exact(pid):
    """抽查两板（k5 module 档 / 20260206 名档）内存重算与盘面逐字节一致。"""
    expect = open(os.path.join(ROWS_MAIN, f"{pid}.json"), "rb").read()
    assert _recompute_board_bytes(pid) == expect
