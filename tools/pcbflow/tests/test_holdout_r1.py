"""holdout-r1 close 包测试（s94_holdout_devrecord_r1 /
holdout-dev-record-r1.json + 冻结 run-record 一致性）。

覆盖（5 个规格测试 + dev-record 装载对拍）：
- 字母分类器边界（stable=全 6 cell<0.2 / unstable=≥4 cell≥0.2 / mixed；
  s93 build_record letters 段口径在测试内最小复刻——该段在 s93 中内嵌于
  build_record、非独立函数；定点纯函数 fixed6 直接复用 s93）；
- 零旗单位 None 约定（0/0→None；range/median 只在已定义值上计算；
  median/range/f6 纯函数复用 s93）；
- naming checker（复用 s93.naming_check：合规序列通过；越段违规与跳号
  违规各一被检出）；
- rubric 链回放（复用 s93.Classifier + s93.chain_replay，r13–r16 全轮
  12 件口径复现注册数 8/15/5/10；不符即 SystemExit fail-closed）；
- run-record 一致性（从 18 份盘上 reader 文件独立重算字母/cell 极差/
  M1_pool/零旗单位/结构变体，与盘上 holdout-run-r1.json 逐键对拍；
  M1_pool=25/34 定点整数交叉验证）；
- dev-record 装载对拍（kind/身份；letter 三字段与 run-record 逐键相等；
  run_record_ref.sha256=实测；盘上件=s94 纯函数 canonical 重建
  byte-exact）。

纪律：只读 out/（零写盘）、零网络、零 subprocess、零 wall-clock；
盘上件缺失时 pytest.fail 带清晰文件路径信息。
"""

import importlib.util
import json
import os
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOLD_DIR = os.path.join(REPO, "out", "v3-tl2", "holdout")
RUN_PATH = os.path.join(HOLD_DIR, "holdout-run-r1.json")
# DEV-E0-004 追加式锚修复：盘上件指向 v2 追加件（与 r1 冻结件差异恰=
# cli.py 保护锚两处 6ed4f3fd→0a738047，铜环案接纳；r1 零回写、其 sha
# 前缀 eeea2bb9 由 test_protocol_v2_freeze 继续钉死不变）。
# RE-REGISTRATION D2（RE-REGISTRATION-ADJUDICATION-2026-09-13）：盘上件
# 改指 v2.1 修正件（=v2 全字段原值+kind 后缀/supersedes/双值披露三要素；
# v2 件零回写，其字节由 V2_SHA256 全长钉死=负向断言）；v2.1 的
# supersedes 链衔接 HOLDOUT-R1-ADJUDICATION 的引用件迁移（裁定记录零
# 回写）；s94 重建=v2 payload，盘上对拍改为「三要素掩码还原后=v2 字节」。
V2_PATH = os.path.join(HOLD_DIR, "holdout-dev-record-r1-v2.json")
V2_SHA256 = ("5ac9212612939c5651310a0e5ac63542269f0b46ef56f643943c8f"
             "2c2c12b3dd")
V21_KIND = "tl2_holdout_r1_dev_record_v2_1"
V21_SHA256 = ("737cf50a1362fed4af4656b68f1772bede2a46ab362f3ef77a32"
              "470edd93bceb")
DEV_PATH = os.path.join(HOLD_DIR, "holdout-dev-record-r1-v2_1.json")
_V21_PROVENANCE_KEYS = ("anchor_amendment", "supersedes")
RUBRIC_PATH = os.path.join(REPO, "out", "v3-tl2", "calibration",
                           "abstain-typology-r13-r16.json")

BOARDS = ["kitspace_led_driver", "tiny_tapeout", "vme-wren"]
VIEWS = ["top", "bottom"]
INSTANCES = ["i1", "i2", "i3"]

THRESHOLD_FIXED = 200000  # 0.2 六位定点（s93 build_record letters 段）


def _load_script(filename: str, alias: str):
    path = os.path.join(REPO, "scripts", filename)
    if not os.path.exists(path):
        pytest.fail(f"缺脚本文件: {path}")
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S93 = _load_script("s93_holdout_compare_r1.py", "s93_holdout_compare_r1")
S94 = _load_script("s94_holdout_devrecord_r1.py", "s94_holdout_devrecord_r1")

# REPAIR-P4 W-1（G0）：config.py 经用户授权变更（f515c348→acdfac49，登记=
# out/repair-p4/anchor-hashes-post-g0.json）。历史脚本 s94 冻结不动；测试侧
# 历史语境回放：装载模块的 _sha 对 config.py 按登记件 before 值返回（verify
# 红线在历史语境执行；record protected 段=历史值=与盘上冻结件一致）。
_orig_sha_s94 = S94._sha


def _sha_g0_legacy_s94(rel):
    if str(rel).replace("\\", "/").endswith("pcbflow/config.py"):
        return ("f515c34842521a645145a9f5454a5919274a242e5c8c27c01fa"
                "f1a4c13e73baf")
    if str(rel).replace("\\", "/").endswith("pcbflow/cli.py"):
        # REPAIR-G1+ W-1/W-2（2026-09-24）：cli.py 授权变更 0a738047->
        # 3bfc9407（登记=out/repair-g1plus-r1/anchor-hashes-post-g1plus.
        # json）；冻结语境回放补 cli 腿（与 config 同构）
        return "0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e"
    return _orig_sha_s94(rel)


S94._sha = _sha_g0_legacy_s94

F = Fraction


def _require(path: str) -> str:
    if not os.path.exists(path):
        pytest.fail(f"缺盘上文件（测试前置不满足）: {path}")
    return path


def _load_json(path: str):
    with open(_require(path), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 最小口径复刻（注明来源：s93 build_record 内嵌段；定点纯函数复用 s93）
# ---------------------------------------------------------------------------

def _to_fixed6(value):
    """Fraction→s93.fixed6；6 位小数 float→定点整数；None 保持 None。"""
    if value is None:
        return None
    if isinstance(value, Fraction):
        return S93.fixed6(value)
    return int(round(value * 1000000))


def _letter_from_range_fracs(range_fracs):
    """s93 build_record letters 段最小口径：stable=全部 cell 已定义且
    <0.2；unstable=≥4 cell≥0.2；mixed=其余。0.2 比较用 6 位定点整数。
    接受 Fraction（合成例）或 6 位小数 float（独立重算例）。"""
    fixed = [_to_fixed6(r) for r in range_fracs]
    ge = [v for v in fixed if v is not None and v >= THRESHOLD_FIXED]
    all_below = all(v is not None and v < THRESHOLD_FIXED for v in fixed)
    if all_below:
        return "stable"
    if len(ge) >= 4:
        return "unstable"
    return "mixed"


def _cell_from_instance_rates(rates):
    """s93 build_record cells 段最小口径：range/median 只在已定义值上
    计算（None 除外）。median/range/f6 纯函数直接复用 s93。"""
    defined = [r for r in rates if r is not None]
    if not defined:
        return {"n_defined": 0, "range": None, "median": None}
    return {"n_defined": len(defined),
            "range": S93.f6(S93.range_frac(defined)),
            "median": S93.f6(S93.median_frac(defined))}


# ---------------------------------------------------------------------------
# 1) 字母分类器边界
# ---------------------------------------------------------------------------

def test_letters_classifier_boundaries():
    """合成 6-cell range 集合三例：stable（全<0.2）/ unstable（≥4 个
    ≥0.2，含 0.2 边界命中）/ mixed（其余；第三例=本轮实况形状）。"""
    stable_case = [F(0), F(1, 10), F(1, 20), F(3, 20), F(0), F(19, 100)]
    unstable_case = [F(1, 5), F(1, 5), F(1, 5), F(1, 5), F(0), F(0)]
    mixed_case = [F(4, 5), F(1), F(1), F(0), F(0), F(0)]
    assert _letter_from_range_fracs(stable_case) == "stable"
    assert _letter_from_range_fracs(unstable_case) == "unstable"
    assert _letter_from_range_fracs(mixed_case) == "mixed"
    # 边界细分：恰 3 个 cell≥0.2 不得升 unstable（维持 mixed）；
    # 全部<0.2 但含 None（未定义 cell）不判 stable（s93 口径要求全定义）
    three_ge = [F(1, 5), F(1, 5), F(1, 5), F(0), F(0), F(0)]
    assert _letter_from_range_fracs(three_ge) == "mixed"
    with_none = [F(0), F(0), F(0), F(0), F(0), None]
    assert _letter_from_range_fracs(with_none) != "stable"
    assert _letter_from_range_fracs(with_none) == "mixed"


# ---------------------------------------------------------------------------
# 2) 零旗单位 None 约定
# ---------------------------------------------------------------------------

def test_zero_flag_none_convention():
    """零旗单位→None；range/median 在已定义值上计算（None 除外）。"""
    zero_flag = None  # flags=0 的读数单位（0/0→None，r10/r11 同口径）
    cell = _cell_from_instance_rates([F(1), zero_flag, F(1)])
    assert cell == {"n_defined": 2, "range": 0.0, "median": 1.0}
    all_zero_flag = _cell_from_instance_rates(
        [zero_flag, zero_flag, zero_flag])
    assert all_zero_flag == {"n_defined": 0, "range": None,
                             "median": None}
    # 盘上实况对拍：kitspace_led_driver/bottom instance_rates=[1.0,
    # None, 1.0] → n_defined=2/range=0.0/median=1.0
    run = _load_json(_require(RUN_PATH))
    live = run["measurement"]["cells"]["kitspace_led_driver/bottom"]
    rates = [None if r is None
             else F(int(round(r * 1000000)), 1000000)
             for r in live["instance_rates"]]
    recomputed = _cell_from_instance_rates(rates)
    assert live["n_defined"] == recomputed["n_defined"] == 2
    assert live["range"] == recomputed["range"] == 0.0
    assert live["median"] == recomputed["median"] == 1.0
    # run-record 内全部零旗单位：4 个、率与分数形式均 None
    zero_units = [u for u in run["measurement"]["per_unit"]
                  if u["flag_count"] == 0]
    assert len(zero_units) == 4
    assert all(u["abstain_rate"] is None and u["rate_fraction"] is None
               and u["zero_flag"] is True for u in zero_units)


# ---------------------------------------------------------------------------
# 3) naming checker（复用 s93.naming_check）
# ---------------------------------------------------------------------------

def test_naming_checker():
    """合成合规序列通过；越段违规与跳号违规各一被检出。"""
    slot = {"slot": 1, "hot_range": [1, 99], "hob_range": [101, 199]}
    ok = S93.naming_check(
        [{"flag_id": "HOT-001"}, {"flag_id": "HOT-002"}], slot,
        "synthetic/ok.txt")
    assert ok["compliant"] is True
    assert ok["violations"] == []
    assert ok["hot_sequence"]["contiguous"] is True
    assert ok["hot_sequence"]["starts_at_band_start"] is True
    # 越段：HOB-500 越出 hob_range [101,199] → violations 逐条列出
    out_of_band = S93.naming_check([{"flag_id": "HOB-500"}], slot,
                                   "synthetic/out_of_band.txt")
    assert out_of_band["compliant"] is False
    assert any("越出" in v["reason"]
               for v in out_of_band["violations"])
    # 跳号：HOT-001→HOT-003 缺 002 → contiguous=False 判不合规
    gap = S93.naming_check(
        [{"flag_id": "HOT-001"}, {"flag_id": "HOT-003"}], slot,
        "synthetic/gap.txt")
    assert gap["compliant"] is False
    assert gap["hot_sequence"]["contiguous"] is False


# ---------------------------------------------------------------------------
# 4) rubric 链回放（复用 s93 分类器；读 out/ 文件）
# ---------------------------------------------------------------------------

def test_chain_replay_registered_counts():
    """s93.Classifier + s93.chain_replay 回放 r13–r16 全轮 12 件口径，
    逐轮复现注册 contact 计数 8/15/5/10（回放不符=SystemExit
    fail-closed，测试失败）。"""
    rubric = _load_json(_require(RUBRIC_PATH))
    classifier = S93.Classifier(rubric["rubric"]["keyword_tables"])
    replay = S93.chain_replay(classifier, rubric)
    assert replay["pass"] is True
    registered = replay["registered_contact_chain"]
    assert registered == {"r13": 8, "r14": 15, "r15": 5, "r16": 10}
    assert replay["replayed_contact_chain"] == registered
    # 更强对拍：全家族分布逐轮相等（chain_replay 内部已断言，此处复核
    # 计数总和一致性）
    for rnd, dist in replay["replayed_family_distributions"].items():
        assert sum(dist.values()) == registered[rnd] + sum(
            v for k, v in dist.items() if k != "contact")


# ---------------------------------------------------------------------------
# 5) run-record 一致性（18 份 reader 文件独立重算 → 对拍盘上件）
# ---------------------------------------------------------------------------

def _recompute_from_reader_files():
    """从 18 份盘上 reader 文件独立重算：字母/6 cell 极差/M1_pool
    总计/零旗单位集合/结构变体计数（复用 s93 解析纯函数）。"""
    hold = Path(_require(HOLD_DIR))
    files = sorted(hold.glob("reader-raw-holdout-*.txt"))
    if len(files) != 18:
        pytest.fail(f"holdout reader 文件应 18 件，实测 {len(files)}: "
                    f"{HOLD_DIR}")
    unit = {}
    variants = {}
    total_flags = 0
    total_abstain = 0
    zero_units = set()
    for path in files:
        meta = S93.parse_reader_name(path)
        data, _fenced = S93.load_reader_file(path)
        flags, variant = S93.extract_flags(data)
        variants[path.name] = variant
        n_abstain = sum(1 for fl in flags
                        if fl.get("abstain") is True)
        total_flags += len(flags)
        total_abstain += n_abstain
        key = (meta["board"], meta["view"], meta["instance"])
        unit[key] = Fraction(n_abstain, len(flags)) if flags else None
        if not flags:
            zero_units.add(key)
    cell_ranges = {}
    for b in BOARDS:
        for v in VIEWS:
            defined = [unit[(b, v, i)] for i in INSTANCES
                       if unit[(b, v, i)] is not None]
            cell_ranges[f"{b}/{v}"] = (
                S93.f6(S93.range_frac(defined)) if defined else None)
    letter = _letter_from_range_fracs(
        [cell_ranges[f"{b}/{v}"] for b in BOARDS for v in VIEWS])
    return {
        "letter": letter,
        "cell_ranges": cell_ranges,
        "m1": (total_abstain, total_flags),
        "zero_units": zero_units,
        "n_per_image": sum(1 for v in variants.values()
                           if v == "per_image"),
    }


def test_run_record_consistency():
    """盘上 holdout-run-r1.json：letter 字段与测试内独立重算的字母一致；
    M1_pool=25/34=0.735294（定点整数交叉验证）；zero_flag_units=4；
    per_image 结构变体=2。"""
    run = _load_json(_require(RUN_PATH))
    recomputed = _recompute_from_reader_files()

    # 字母：独立重算 == run-record letters.letter（不采信记录自述）
    assert run["letters"]["letter"] == recomputed["letter"]
    # 6 cell 极差逐键一致（定点整数比较，零浮点除法歧义）
    for key, live_val in run["letters"]["cell_ranges"].items():
        rec_val = recomputed["cell_ranges"][key]
        if live_val is None or rec_val is None:
            assert live_val is None and rec_val is None, key
        else:
            assert int(round(live_val * 1000000)) == \
                int(round(rec_val * 1000000)), key

    # M1_pool：25/34 = 0.735294（定点整数交叉验证）
    abstain, flags = recomputed["m1"]
    assert (abstain, flags) == (25, 34)
    total = run["measurement"]["m1_pool"]["total"]
    assert total["fraction"] == "25/34"
    assert total["abstain"] == 25 and total["flags"] == 34
    assert S93.f6(Fraction(25, 34)) == 0.735294 == total["m1_pool"]
    # 定点整数交叉验证（同尺度两式；任务简报「25*1000000==round(
    # 0.735294*34)」为量纲笔误——两边不同尺度恒假，按同尺度修正）
    assert 25 == round(0.735294 * 34)
    assert 735294 == round(0.735294 * 1000000) == S93.fixed6(
        Fraction(25, 34))

    # 零旗单位=4 且与独立重算集合逐项一致
    live_zero = run["reader"]["zero_flag_units"]
    assert len(live_zero) == 4
    assert {(u["board"], u["view"], u["instance"])
            for u in live_zero} == recomputed["zero_units"]

    # per_image 结构变体=2（独立重算 == 盘上 parse_disclosures 计数）
    live_n_per_image = sum(
        1 for row in run["parse_disclosures"]["per_file"]
        if row.get("structure_variant") == "per_image")
    assert recomputed["n_per_image"] == live_n_per_image == 2


# ---------------------------------------------------------------------------
# 6) dev-record 装载对拍
# ---------------------------------------------------------------------------

def test_dev_record_loads_letter_from_run_record():
    """盘上 holdout-dev-record-r1.json：身份/字母三字段=run-record 逐键
    装载（零改写）；run_record_ref=实测哈希；盘上件=s94 纯函数
    canonical 重建 byte-exact。"""
    dev = _load_json(_require(DEV_PATH))
    run = _load_json(_require(RUN_PATH))
    assert dev["kind"] == V21_KIND  # v2.1 kind 显式后缀（§4.5 要素 1）
    assert dev["supersedes"]["path_rel"] == \
        "out/v3-tl2/holdout/holdout-dev-record-r1-v2.json"
    assert dev["supersedes"]["sha256"] == V2_SHA256  # §4.5 要素 2
    assert dev["anchor_amendment"]["old_value"] != \
        dev["anchor_amendment"]["new_value"]  # §4.5 要素 3（双值披露）
    assert "HOLDOUT-R1-ADJUDICATION" in \
        dev["supersedes"]["note"]  # 引用件迁移登记（裁定记录零回写）
    assert dev["holdout_id"] == "holdout-r1"
    assert dev["declared_date"] == "2026-09-10"
    assert dev["schema_version"] == "3.0"
    # 字母三字段逐键装载相等（不重算不改写）
    assert dev["letter"]["value"] == run["letters"]["letter"]
    assert dev["letter"]["cell_ranges"] == run["letters"]["cell_ranges"]
    assert dev["letter"]["cells_ge_0_2"] == run["letters"]["cells_ge_0_2"]
    assert dev["letter"]["source"] == (
        "holdout-run-r1.json letters（冻结判据机械判定）")
    # run_record_ref=盘上实测哈希
    assert dev["run_record_ref"]["path_rel"] == (
        "out/v3-tl2/holdout/holdout-run-r1.json")
    assert dev["run_record_ref"]["sha256"] == \
        hashing.sha256_file(_require(RUN_PATH))
    assert dev["run_record_ref"]["sha256"].startswith("e64f882f2c02adab")
    # 盘上件 payload（三要素掩码还原）= s94 纯函数同参重建 canonical
    # bytes（=v2 字节；RE-REGISTRATION D2 对拍语义）
    sha_start = S94.verify_protected()
    record = S94.build_record(sha_start)
    raw = Path(_require(DEV_PATH)).read_bytes()
    doc = json.loads(raw)
    payload = {k: v for k, v in doc.items()
               if k not in _V21_PROVENANCE_KEYS}
    payload["kind"] = "tl2_holdout_r1_dev_record"
    assert hashing.canonical_json_bytes(payload) == \
        hashing.canonical_json_bytes(record)
    # 负向断言：v2 原件字节零变化（零回写）；v2.1 件身份
    assert hashing.sha256_file(V2_PATH) == V2_SHA256
    assert hashing.sha256_file(str(_require(DEV_PATH))) == V21_SHA256
