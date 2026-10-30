"""development 级双口径描述计算批测试（metrics-dev-r2；装配逻辑对账面）。

覆盖（派发词⑤）：
- 池分离断言：train/demo/holdout 三池板集不相交（复合键+裸键双面）；
- 行数守恒：r1 20,235+r2 14,666 逐池守恒（34,901）、逐源逐 role 分列；
- smoke=0；holdout 行零混入 train/demo 池（holdout 只描述单列）；
- validation-role 行并入 train 池的编排披露面（逐 role 分列可见）；
- calculator 复用一致性抽 2 类（train/rails + holdout/padload）：
  测试独立装载行文件→describe_pool 重算→与盘上主件逐字典相等；
- 自检件 all_match + 主件/replay-check hash 对账；
- development 级声明头块在件（机器件+人读报告双面）；
- 保护三文件零变化。

探针级只读（零写入/零网络/零 wall-clock）；主件 hash 锚=动工实测。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import resource_calibration_metrics as rcm

ROOT = os.path.join(os.path.dirname(__file__), "..")
DEV = os.path.join(ROOT, "out", "v3-obs", "metrics-dev-r2")
R1 = os.path.join(ROOT, "out", "v3-obs", "rows-r1", "rows")
R2 = os.path.join(ROOT, "out", "v3-obs", "rows-r2", "rows", "main")

MAIN_JSON = os.path.join(DEV, "descriptive-metrics-dev-r2.json")
SELF_JSON = os.path.join(DEV, "selfcheck-p-rc-6-dev-r2.json")
REPLAY_JSON = os.path.join(DEV, "replay-check-dev-r2.json")
REPORT_MD = os.path.join(DEV, "DESCRIPTIVE-REPORT-dev-r2.md")
BATCH_PY = os.path.join(DEV, "batch-compute-dev-r2.py")

# ---- 动工实测锚（完工后由本测试钉住） ---------------------------------------
MAIN_JSON_SHA = ("d240923fe7f83f82df151735a807c5d8ba1b5b596e"
                 "2c42d2c4cc4ad3e83ea079")

# ---- 装配期望（派发词+N-G3-1 更正版+rows-r1 batch-summary 实测） ------------
EXPECTED = {
    "pool_rows": {"train": 15225, "demo": 12371, "holdout": 7305},
    "pool_boards": {"train": 62, "demo": 17, "holdout": 12},
    "rows_by_source": {
        "train": {"r1_real_train": 5907, "r1_real_validation": 1255,
                  "r2_train": 8063},
        "demo": {"r1_demo_all": 12371},
        "holdout": {"r1_real_holdout": 702, "r2_holdout": 6603},
    },
    "grand_total": 34901,
}

PROTECTED = {
    "pcbflow/cli.py": "3bfc940701d1be82029877583a0a41f49741228f2e89a321b7dafa98d179aae8",
    "pcbflow/config.py": "8ad12b3fab12f19546034b5421aa77053f4115b91b36b87b9dfabc9075fdcf82",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd896d9301690b3d",
}


# ---------------------------------------------------------------------------
# 装载（测试面独立实现：不经编排脚本；编排脚本仅作 assemble 交叉面）
# ---------------------------------------------------------------------------


def _load_dir(d):
    rows = []
    for name in sorted(os.listdir(d)):
        if name.endswith(".json"):
            with open(os.path.join(d, name), encoding="utf-8") as f:
                rows.extend(json.load(f))
    return rows


def _independent_pools():
    """独立装配（测试自写路径，与编排脚本同判据不同实现）。"""
    r1_main = _load_dir(os.path.join(R1, "main"))
    r1_demo = _load_dir(os.path.join(R1, "demo"))
    r2 = _load_dir(R2)
    train = ([r for r in r1_main if r["split"]["role"] in ("train",
                                                           "validation")]
             + [r for r in r2 if r["split"]["role"] == "train"])
    demo = list(r1_demo)
    holdout = ([r for r in r1_main if r["split"]["role"] == "holdout"]
               + [r for r in r2 if r["split"]["role"] == "holdout"])
    return ({"train": train, "demo": demo, "holdout": holdout},
            r1_main, r1_demo, r2)


def _load_batch_module():
    spec = importlib.util.spec_from_file_location("batch_compute_dev_r2",
                                                  BATCH_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def main_json():
    with open(MAIN_JSON, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def pools():
    return _independent_pools()[0]


# ---------------------------------------------------------------------------
# 池分离 / 守恒 / smoke / holdout 纪律
# ---------------------------------------------------------------------------


class TestPoolAssembly:
    def test_board_sets_disjoint(self, pools):
        def keys(rows):
            return {(r["split"]["dataset_id"], r["split"]["board_id"])
                    for r in rows}

        t, d, h = keys(pools["train"]), keys(pools["demo"]), keys(pools["holdout"])
        assert not (t & d) and not (t & h) and not (d & h)
        # 裸 board_id 键亦不相交（跨数据集同名防御面）
        bt = {b for _, b in t}
        bd = {b for _, b in d}
        bh = {b for _, b in h}
        assert not (bt & bd) and not (bt & bh) and not (bd & bh)

    def test_row_count_conservation(self, pools):
        total = sum(len(v) for v in pools.values())
        assert total == EXPECTED["grand_total"]
        assert total == 20235 + 14666
        for pool, n in EXPECTED["pool_rows"].items():
            assert len(pools[pool]) == n, pool
        # 逐源逐 role 分列（validation 并入 train 池的披露面）
        train = pools["train"]
        assert (sum(1 for r in train if r["split"]["dataset_id"] != "corpus-r2-r1"
                    and r["split"]["role"] == "train")
                == EXPECTED["rows_by_source"]["train"]["r1_real_train"])
        assert (sum(1 for r in train
                    if r["split"]["role"] == "validation")
                == EXPECTED["rows_by_source"]["train"]["r1_real_validation"])
        assert (sum(1 for r in train
                    if r["split"]["dataset_id"] == "corpus-r2-r1")
                == EXPECTED["rows_by_source"]["train"]["r2_train"])
        assert len(pools["demo"]) == EXPECTED["rows_by_source"]["demo"]["r1_demo_all"]
        holdout = pools["holdout"]
        assert (sum(1 for r in holdout
                    if r["split"]["dataset_id"] != "corpus-r2-r1")
                == EXPECTED["rows_by_source"]["holdout"]["r1_real_holdout"])
        assert (sum(1 for r in holdout
                    if r["split"]["dataset_id"] == "corpus-r2-r1")
                == EXPECTED["rows_by_source"]["holdout"]["r2_holdout"])

    def test_board_counts(self, pools):
        for pool, n in EXPECTED["pool_boards"].items():
            boards = {(r["split"]["dataset_id"], r["split"]["board_id"])
                      for r in pools[pool]}
            assert len(boards) == n, pool

    def test_smoke_zero(self, pools):
        for pool, rows in pools.items():
            hits = [r["profile_id"] for r in rows
                    if "smoke" in r["profile_id"].lower()
                    or "smoke" in r["split"]["board_id"].lower()]
            assert hits == [], pool

    def test_holdout_exclusive(self, pools):
        # holdout 行只出现在 holdout 池；train/demo 池零 holdout role 行
        for pool in ("train", "demo"):
            leaked = [r for r in pools[pool]
                      if r["split"]["role"] == "holdout"
                      and r["split"]["dataset_id"] != "kicad-demos-r1"]
            assert leaked == [], pool
        # demo 池内 holdout role 行只可能来自 kicad-demos（R2 单列池设计）
        for r in pools["demo"]:
            if r["split"]["role"] == "holdout":
                assert r["split"]["dataset_id"] == "kicad-demos-r1"
        assert all(r["split"]["role"] == "holdout" for r in pools["holdout"])

    def test_partition_via_observation_id(self, pools):
        obs = ([r["observation_id"] for r in pools["train"]]
               + [r["observation_id"] for r in pools["demo"]]
               + [r["observation_id"] for r in pools["holdout"]])
        assert len(obs) == len(set(obs)) == 34901


# ---------------------------------------------------------------------------
# calculator 复用一致性抽 2 类（独立装载→describe_pool→对盘上主件）
# ---------------------------------------------------------------------------


class TestCalculatorReuse:
    #: 主件 auxiliary 条目=describe_pool 原样输出 + 唯一编排层附加键
    #: m2b_board_pool_analog（development 扩展描述量，显式标注）；对账时剥离
    #: 该键，其余逐字典相等=计算器复用一致性。
    DEV_EXT_KEY = "m2b_board_pool_analog"

    @staticmethod
    def _stored_without_ext(entry):
        stored = dict(entry)
        stored.pop(TestCalculatorReuse.DEV_EXT_KEY, None)
        return stored

    @classmethod
    def _assert_reuse(cls, pool, kind, short, pools, main_json):
        subset = [r for r in pools[pool] if rcm.row_kind(r) == kind]
        mine = rcm.describe_pool(subset, kind, auxiliary=True,
                                 exclude_detail=True)
        entry = main_json["pools"][pool]["auxiliary"][short]
        assert cls.DEV_EXT_KEY in entry  # 扩展量在件且显式标注
        note = entry[cls.DEV_EXT_KEY].get("note", "")
        assert "development" in note
        assert mine == cls._stored_without_ext(entry)

    def test_train_rails(self, pools, main_json):
        self._assert_reuse("train", "rails", "rails", pools, main_json)

    def test_holdout_padload(self, pools, main_json):
        self._assert_reuse("holdout", "signal_layer_pad_load", "padload",
                           pools, main_json)


# ---------------------------------------------------------------------------
# 编排脚本 assemble 交叉面 + 产物对账 + 声明面 + 保护面
# ---------------------------------------------------------------------------


class TestBatchScriptAndArtifacts:
    def test_batch_assemble_matches_independent(self):
        mod = _load_batch_module()
        r1_main = _load_dir(os.path.join(R1, "main"))
        r1_demo = _load_dir(os.path.join(R1, "demo"))
        r2 = _load_dir(R2)
        pools, assembly = mod.assemble_pools(r1_main, r1_demo, r2)
        assert assembly["invariants"]["conservation_match"] is True
        assert assembly["invariants"]["smoke_rows"] == 0
        assert (assembly["invariants"]["rows_grand_total"]
                == EXPECTED["grand_total"])
        assert sum(len(v) for v in pools.values()) == EXPECTED["grand_total"]
        # validation 披露面（逐 role 分列在件）
        src = assembly["pools"]["train"]["rows_by_source"]
        assert src["r1_real_validation"] == 1255

    def test_selfcheck_all_match(self):
        with open(SELF_JSON, encoding="utf-8") as f:
            sc = json.load(f)
        assert sc["all_match"] is True
        assert sc["n_checks"] == len(sc["checks"]) >= 3
        # 手算 byte-exact 样例在件
        ids = {c["id"] for c in sc["checks"]}
        assert {"hand-two-board-byte-exact", "hand-m3-argmax",
                "hand-m3-tie-lex", "hand-even-p50"} <= ids

    def test_replay_and_hash_anchor(self):
        with open(MAIN_JSON, "rb") as f:
            main_sha = hashlib.sha256(f.read()).hexdigest()
        assert main_sha == MAIN_JSON_SHA
        with open(REPLAY_JSON, encoding="utf-8") as f:
            replay = json.load(f)
        assert replay["byte_exact"] is True
        rec = replay["files"]["descriptive-metrics-dev-r2.json"]
        assert rec["sha256_expected"] == rec["sha256_on_disk_before"]

    def test_development_declaration_in_artifacts(self, main_json):
        decl = main_json["development_declaration"]
        assert decl["level"] == "development"
        assert decl["not_preregistered"] is True
        assert len(decl["intended_use"]) == 2
        assert main_json["declared_date"] == "2026-09-13"
        with open(REPORT_MD, encoding="utf-8") as f:
            text = f.read()
        assert "development" in text
        assert "非 preregistered" in text
        assert "冻结前本批数值不得引用" in text

    def test_reconciliation_flags(self, main_json):
        recon = main_json["reconciliation"]
        assert recon["r1"]["rows_total_match"] is True
        assert recon["r1"]["row_class_match"] is True
        assert recon["r2"]["rows_total_match"] is True
        assert recon["r2"]["row_class_match"] is True
        frr2 = recon["r2"]["role_kind_rows_vs_first_run_report_r2_s2_corrected"]
        assert all(v["match"] for v in frr2.values())

    def test_sidecar_sections_discipline(self, main_json):
        esc = main_json["escape_agreement_a"]
        assert esc["n_ok"] == {"train": 28, "holdout": 5, "total": 33}
        assert esc["n_fail_closed"] == {"train": 3, "holdout": 1, "total": 4}
        assert esc["conservation_all_ok"] is True
        assert all(r["r2_pending"] is True for r in esc["per_board_ok"])
        lc = main_json["lc_demand_fit"]
        assert lc["n_ok"] == {"train": 27, "holdout": 5, "total": 32}
        assert lc["n_fail_closed"] == {"train": 4, "holdout": 1, "total": 5}
        assert all(r["r2_pending"] is True for r in lc["per_board_ok"])

    def test_protected_files_unchanged(self):
        for rel, expected in PROTECTED.items():
            with open(os.path.join(ROOT, rel), "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            assert digest == expected, rel
