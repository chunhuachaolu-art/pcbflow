#!/usr/bin/env python
"""HOLDOUT-R1-PREP：PCBFlow v3.0 TL-2 holdout 正式运行 prep-record（预注册
件，先于任何盲读冻结）。本轮只新建两个文件：scripts/s91_holdout_prep_r1.py
（生成器本体）与 out/v3-tl2/holdout/holdout-prep-record-r1.json——本轮仅有
的这个 out/ 新产物；HOLDOUT-PLAN-amendment-r1.md 由本轮前置步骤落盘、本脚
本只活读登记（无前缀预期）；datasets/ 与 out/ 既有文件只读、零改动。

轮性质（用户 2026-09-10 拍板「启动 holdout」=独立人工点触发正式运行，
evaluation-protocol-v2.md §2.3/§4.5；一次性运行，HOLDOUT-PLAN §一.2 一次
性纪律生效）。本脚本=编排侧生成器（纯函数、零视觉判读、零图像读取）：
  A. 受保护文件哈希校验（3 件前缀匹配，不符 sys.exit(1)；实测=全 64 位
     断言，强于红线要求的前缀匹配；开工/收工各验一次）。
  B. 活读治理链引用并核前缀（8 件；HOLDOUT-PLAN=冻结件只读引用；修正
     件=活读 sha256、无前缀预期；任何缺失/前缀不符→FAIL）。
  C. 反放宽条款断言：guidance-r25 全文中反放宽句恰出现 1 次。
  D. 活读基线数字（不硬编码：从盘上件读出后填入记录；在案锚 fail-closed
     交叉断言）：run-r11 range_top/range_bottom；run-r25 baseline_cross_
     check r19/r22/r23/r24_row_live.M1 + r25_m_tuple_6dp.M1（发展域 M1
     参照集 5 值）。
  E. 活读 precheck：ready_boards（8 板清单）/boards_ready=8/union_on_disk
     _total=19/isolation_check.verdict=isolated/plan_registration.
     designation_date=2026-09-07/overall.verdict=conditional（全断言）。
  F. 活读 split manifest：kicad-demos-r2 holdout 恰含 tiny_tapeout/
     tinytapeout-demo 与 vme-wren/vme-wren；pcbench-r1-v3 holdout 恰含
     kitspace_led_driver；group_counts.holdout 计数与列表长度两值如实并列
     （10 vs 11 差异=stale 计数，amendment §一.3 处置引用；活读交叉核对）。
  G. 板源文件 sha256 活读并核前缀（3 件 fail-closed）。
  H. 铜层 token 复核（纯函数）：正则 \\b((?:In\\d+|[FB])\\.Cu)\\b 全文扫描
     （utf-8 errors='replace'），去重排序 distinct token 集；断言集合大小
     =={kitspace_led_driver:2, tiny_tapeout:4, vme-wren:12}；token 集合与
     方法注记一并写入记录。
  I. 组装记录对象并用 canonical_json_bytes 落盘（防覆写：已存在且重建字
     节不同→FAIL、相同→幂等零覆写），打印 sha256 前 16 位。

纪律：日期=声明常量 2026-09-10（零 wall-clock）；零 subprocess/零网络/零
主机绝对路径（记录内全部仓库相对路径、正斜杠，落盘前机械扫描断言）；
canonical JSON=pcbflow.hashing.canonical_json_bytes；哈希=pcbflow.hashing
.sha256_file 字节口径；零 GT/零 ground-truth-*/零 reader-raw-*/零诊断内
容读取；零视觉判读、零图像读取（.kicad_pcb=文本 token 扫描，非图像）；
记录构造=纯函数、同参重建两次逐字节一致自证；同参重建不一致即 FAIL；
保护三文件（pcbflow/cli.py、pcbflow/config.py、toolchain_lock.json）开工/
收工各验一次全 64 位 sha256；不 git、不 pytest、阈值零修改；评估域=
development 只描述不断言（in_calibrated_range 恒 False、P2-8）。

结构补入项（偏差如实登记）：governance_chain 增 registration/typology 两
键（B 步活读件的在案证据槽位）；measurement_design 增 r11_baseline_values
/dev_m1_reference_values/baseline_sources 三键（D 步活读值的入记录槽位，
规格字符串不含数值占位）；board_selection 增 copper_layer_token_method 键
（H 步方法注记要求）。其余字段=任务规格逐字镜像。

用法：python scripts/s91_holdout_prep_r1.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

HOLDOUT_DIR = REPO / "out" / "v3-tl2" / "holdout"
CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
TL5_DIR = REPO / "out" / "v3-tl5"
PLAN = HOLDOUT_DIR / "HOLDOUT-PLAN.md"
AMENDMENT = HOLDOUT_DIR / "HOLDOUT-PLAN-amendment-r1.md"
PRECHECK = HOLDOUT_DIR / "precheck-r1.json"
RECORD = HOLDOUT_DIR / "holdout-prep-record-r1.json"
PROTOCOL_V2 = CAL_DIR / "evaluation-protocol-v2.md"
PROTOCOL_V2_REG = CAL_DIR / "protocol-v2-registration.json"
PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
GUIDANCE_R25 = CAL_DIR / "observation-guidance-r25.md"
TYPOLOGY = CAL_DIR / "abstain-typology-r13-r16.json"
RUN_R11 = CAL_DIR / "calibration-run-r11.json"
RUN_R25 = CAL_DIR / "calibration-run-r25.json"
MANIFEST_KD = TL5_DIR / "dataset-manifest-kicad-demos-r2.json"
MANIFEST_PB = TL5_DIR / "dataset-manifest-pcbench-r1-v3.json"
BOARD_FILES = {
    "kitspace_led_driver": (
        REPO / "datasets" / "pcbench-r1" / "raw" / "kitspace_led_driver" /
        "processed.kicad_pcb"),
    "tiny_tapeout": (
        REPO / "datasets" / "kicad-demos-r1" / "raw" / "tiny_tapeout" /
        "tinytapeout-demo.kicad_pcb"),
    "vme-wren": (
        REPO / "datasets" / "kicad-demos-r1" / "raw" / "vme-wren" /
        "vme-wren.kicad_pcb"),
}
CLI_PY = REPO / "pcbflow" / "cli.py"
CONFIG_PY = REPO / "pcbflow" / "config.py"
TOOLCHAIN_LOCK = REPO / "toolchain_lock.json"

DATE_CONSTANT = "2026-09-10"
HOLDOUT_ID = "holdout-r1"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）。保护三文件=全 64 位 sha256 断言；治理
# 链/板源=前缀断言；修正件=活读、无前缀预期。
# ---------------------------------------------------------------------------
CLI_PY_SHA = ("6ed4f3fd7c87947562acffb90c8563dfae0d05ad82c395a45d0aad226"
              "c206e17")
CONFIG_PY_SHA = ("f515c34842521a645145a9f5454a5919274a242e5c8c27c01faf1a"
                 "4c13e73baf")
TOOLCHAIN_LOCK_SHA = ("d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd"
                      "896d9301690b3d")

PLAN_SHA_PREFIX = "a4b80193"
PRECHECK_SHA_PREFIX = "7260027f"
PROTOCOL_V2_SHA_PREFIX = "365b67ef"
PROTOCOL_V2_REG_SHA_PREFIX = "36cc86a7"
PROTOCOL_V1_SHA_PREFIX = "22dc7337"
GUIDANCE_R25_SHA_PREFIX = "86af24dd"
TYPOLOGY_SHA_PREFIX = "6dadac8d"
BOARD_SHA_PREFIXES = {
    "kitspace_led_driver": "ccc2efb5",
    "tiny_tapeout": "0d26bf9b",
    "vme-wren": "1c76ac23",
}

# ---------------------------------------------------------------------------
# 逐字引文锚（PLAN §四.1/§四.3 原文；恰 1 次 fail-closed）
# ---------------------------------------------------------------------------
SELECT_RULE_QUOTE = (
    "选板: Tier 1 中取 2–3 板（覆盖 2 层简单板与 4 层以上复杂板各≥1）。")
GUIDANCE_RULE_QUOTE = (
    "盲读: n=3 实例×2 视角，判读指引用届时冻结版（正式 holdout 前的最后版"
    "本）。")

# ---------------------------------------------------------------------------
# 反放宽条款锚（guidance-r25 全文恰 1 次）
# ---------------------------------------------------------------------------
NO_LOOSENING_SENTENCE = (
    "仅因形态不熟悉、不确定其设计含义，不构成判为正常设计特征的理由")
NO_LOOSENING_EXPECT = 1

# ---------------------------------------------------------------------------
# 活读在案锚（D 步；记录值=盘上活读值，锚值仅作 fail-closed 交叉断言——
# 防预注册文本与在案事实漂移；不符即停）
# ---------------------------------------------------------------------------
R11_RANGE_TOP_ANCHOR = 0.153846
R11_RANGE_BOTTOM_ANCHOR = 0.0
R19_M1_ANCHOR = 0.461538
R22_M1_ANCHOR = 0.390244
R23_M1_ANCHOR = 0.484848
R24_M1_ANCHOR = 0.552381
R25_M1_ANCHOR = 0.433735

# ---------------------------------------------------------------------------
# precheck 在案锚（E 步；活读断言）
# ---------------------------------------------------------------------------
EXPECT_BOARDS_READY = 8
EXPECT_UNION_ON_DISK_TOTAL = 19
EXPECT_ISOLATION_VERDICT = "isolated"
EXPECT_DESIGNATION_DATE = "2026-09-07"
EXPECT_OVERALL_VERDICT = "conditional"

# ---------------------------------------------------------------------------
# manifest 在案锚（F 步）
# ---------------------------------------------------------------------------
KD_HOLDOUT_REQUIRED = ("tiny_tapeout/tinytapeout-demo", "vme-wren/vme-wren")
PB_HOLDOUT_REQUIRED = ("kitspace_led_driver",)
KD_GROUP_COUNTS_HOLDOUT = 3          # 对照：kicad-demos-r2 无 stale 问题
PB_GROUP_COUNTS_HOLDOUT_STALE = 10   # pcbench-r1-v3 计数字段=stale（如实并列）
PB_HOLDOUT_LIST_LEN = 11             # 操作口径=holdout 列表本身（amendment §一.3）

# ---------------------------------------------------------------------------
# 铜层 token 复核（H 步；纯函数）
# ---------------------------------------------------------------------------
COPPER_TOKEN_RE = re.compile(r"\b((?:In\d+|[FB])\.Cu)\b")
COPPER_TOKEN_EXPECT = {"kitspace_led_driver": 2, "tiny_tapeout": 4,
                       "vme-wren": 12}
COPPER_METHOD_NOTE = (
    "启发式 token 扫描：正则 \\b((?:In\\d+|[FB])\\.Cu)\\b 对 .kicad_pcb 源"
    "文本全文扫描（utf-8 errors='replace'），去重排序得 distinct token 集"
    "合；与选板层数覆盖要求交叉核对：copper_layer_count==distinct token 数"
    "逐板断言（2/4/12），覆盖 2 层简单板与 4 层以上复杂板各≥1（PLAN §四.1"
    "选板原文）；零图像读取、纯文本 token 口径")

# ---------------------------------------------------------------------------
# 选板（amendment §二 操作化；活读交叉断言：manifest split 成员+precheck
# READY+板源前缀+token 数）
# ---------------------------------------------------------------------------
SELECTED_BOARD_IDS = ("kitspace_led_driver", "tiny_tapeout/tinytapeout-demo",
                      "vme-wren/vme-wren")
SELECTED_SHORT_NAMES = {"kitspace_led_driver": "kitspace_led_driver",
                        "tiny_tapeout/tinytapeout-demo": "tiny_tapeout",
                        "vme-wren/vme-wren": "vme-wren"}
UNSELECTED_EXPECTED = [
    "TTNEnschedeMote_ArduinoNanoRN2483",
    "esp32-cantroller_EltekController",
    "fp2_extension_sample_fp2_usb_breakout",
    "kitspace_T32_ref",
    "video/video",
]

#: 分型件 rubric 口径链锚（abstain-typology-r13-r16.json 在件实测；s88 先
#: 例同法：flag_yield 引用 rubric 前先核对 r13–r16=8/15/5/10 链在案）
TYPOLOGY_CONTACT_CHAIN = {"r13": 8, "r14": 15, "r15": 5, "r16": 10}


# ---------------------------------------------------------------------------
# 工具（fail-closed）
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[holdout-prep-r1] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def _require_full_sha(path: Path, expected: str, label: str) -> str:
    if not path.exists():
        _fail(f"缺失：{path}")
    measured = _sha(path)
    if measured != expected:
        _fail(f"{label} 全 64 位 sha256 实测不符：measured={measured} != "
              f"expected={expected}（锚被改动，立即停止）")
    return measured


def _require_prefix_sha(path: Path, prefix: str, label: str) -> str:
    if not path.exists():
        _fail(f"缺失：{path}")
    measured = _sha(path)
    if not measured.startswith(prefix):
        _fail(f"{label} sha 前 8={measured[:8]} != 预期 {prefix}（锚不符，"
              f"立即停止）")
    return measured


def _assert_eq(got, want, label: str) -> None:
    if got != want:
        _fail(f"{label} 不符：got={got!r} != want={want!r}")


# ---------------------------------------------------------------------------
# probe（活读装载与断言；只读登记字段，零 GT/零诊断/零 reader 内容）
# ---------------------------------------------------------------------------

def check_protected() -> dict:
    """保护三文件全 64 位实测断言（强于红线要求的前缀匹配）；开工/收工各
    验一次。记录={sha256 实测, expected_prefix, match:True}。"""
    measured = {
        "pcbflow/cli.py": _require_full_sha(CLI_PY, CLI_PY_SHA,
                                            "pcbflow/cli.py"),
        "pcbflow/config.py": _require_full_sha(CONFIG_PY, CONFIG_PY_SHA,
                                               "pcbflow/config.py"),
        "toolchain_lock.json": _require_full_sha(
            TOOLCHAIN_LOCK, TOOLCHAIN_LOCK_SHA, "toolchain_lock.json"),
    }
    return {
        rel: {"sha256": sha, "expected_prefix": sha[:8], "match": True}
        for rel, sha in measured.items()
    }


def check_governance_chain() -> dict:
    """B 步：治理链 8 件活读+前缀核验（修正件无前缀预期、活读登记）；
    任何缺失/前缀不符→FAIL。返回各件实测 sha256。"""
    return {
        "plan": _require_prefix_sha(PLAN, PLAN_SHA_PREFIX,
                                    "HOLDOUT-PLAN.md（冻结件只读引用）"),
        "amendment": _sha(AMENDMENT),  # 活读，无前缀预期
        "precheck": _require_prefix_sha(PRECHECK, PRECHECK_SHA_PREFIX,
                                        "precheck-r1.json"),
        "protocol_v2": _require_prefix_sha(PROTOCOL_V2, PROTOCOL_V2_SHA_PREFIX,
                                           "evaluation-protocol-v2.md"),
        "registration": _require_prefix_sha(
            PROTOCOL_V2_REG, PROTOCOL_V2_REG_SHA_PREFIX,
            "protocol-v2-registration.json"),
        "protocol_v1": _require_prefix_sha(PROTOCOL_V1, PROTOCOL_V1_SHA_PREFIX,
                                           "evaluation-protocol-v1.md"),
        "guidance_r25": _require_prefix_sha(GUIDANCE_R25,
                                            GUIDANCE_R25_SHA_PREFIX,
                                            "observation-guidance-r25.md"),
        "typology": _require_prefix_sha(TYPOLOGY, TYPOLOGY_SHA_PREFIX,
                                        "abstain-typology-r13-r16.json"),
    }


def check_plan_quotes(plan_text: str) -> None:
    """记录中两条「PLAN 原文逐字引文」的在案锚（恰 1 次；不符即停）。"""
    for label, quote in (("§四.1 选板", SELECT_RULE_QUOTE),
                         ("§四.3 盲读", GUIDANCE_RULE_QUOTE)):
        n = plan_text.count(quote)
        if n != 1:
            _fail(f"HOLDOUT-PLAN.md {label} 逐字引文命中 {n} 次 != 1"
                  f"（引文与冻结件漂移，立即停止）")


def check_anti_loosening(guidance_text: str) -> int:
    """C 步：guidance-r25 全文中反放宽句恰出现 1 次。"""
    n = guidance_text.count(NO_LOOSENING_SENTENCE)
    if n != NO_LOOSENING_EXPECT:
        _fail(f"guidance-r25 反放宽条款命中 {n} 次 != {NO_LOOSENING_EXPECT}"
              f"（指引字节复用完整性断言失败，立即停止）")
    return n


def probe_typology(typ: dict) -> None:
    """分型件 rubric 口径链回放（flag_yield 引用 rubric 前先核对在案；
    s88 probe_typology 同法：contact 族 r13–r16=8/15/5/10）。"""
    if typ.get("kind") != "abstain_typology_posthoc_r13_r16":
        _fail(f"abstain-typology kind 不符：{typ.get('kind')!r}")
    totals = typ.get("matrix", {}).get("round_totals", {})
    chain = {rnd: totals.get(rnd, {}).get("families", {}).get("contact")
             for rnd in ("r13", "r14", "r15", "r16")}
    if chain != TYPOLOGY_CONTACT_CHAIN:
        _fail(f"分型件 contact 族链回放不符：{chain!r} != "
              f"{TYPOLOGY_CONTACT_CHAIN!r}（r13–r16=8/15/5/10 链回放失败）")


def probe_precheck(precheck: dict) -> dict:
    """E 步：precheck 活读断言（ready 清单/8/19/isolated/2026-09-07/
    conditional），并派生未选 READY 板清单（ready_boards 序剔除选板 3 板，
    与任务给定 5 板序逐位断言）。"""
    overall = precheck.get("overall", {})
    ready = overall.get("ready_boards")
    if not isinstance(ready, list) or len(ready) != EXPECT_BOARDS_READY:
        _fail(f"precheck overall.ready_boards 须为 {EXPECT_BOARDS_READY} 板"
              f"清单：{ready!r}")
    _assert_eq(overall.get("boards_ready"), EXPECT_BOARDS_READY,
               "precheck overall.boards_ready")
    universe = precheck.get("board_universe", {})
    _assert_eq(universe.get("union_on_disk_total"),
               EXPECT_UNION_ON_DISK_TOTAL,
               "precheck board_universe.union_on_disk_total")
    isolation = precheck.get("isolation_check", {})
    _assert_eq(isolation.get("verdict"), EXPECT_ISOLATION_VERDICT,
               "precheck isolation_check.verdict")
    reg = precheck.get("plan_registration", {})
    _assert_eq(reg.get("designation_date"), EXPECT_DESIGNATION_DATE,
               "precheck plan_registration.designation_date")
    _assert_eq(overall.get("verdict"), EXPECT_OVERALL_VERDICT,
               "precheck overall.verdict")
    # 选板 3 板必须全部 READY（P2-9 证齐口径）；未选 READY 板=余 5 板零渲染
    for board_id in SELECTED_BOARD_IDS:
        if board_id not in ready:
            _fail(f"选板 {board_id} 不在 precheck READY 清单（P2-9 缺证，"
                  f"立即停止）")
    unselected = [b for b in ready if b not in SELECTED_BOARD_IDS]
    if unselected != UNSELECTED_EXPECTED:
        _fail(f"未选 READY 板清单不符：{unselected!r} != "
              f"{UNSELECTED_EXPECTED!r}")
    return {"ready_boards": ready, "unselected": unselected}


def probe_baselines() -> dict:
    """D 步：基线数字活读（不硬编码——记录值=盘上读出值；在案锚仅作
    fail-closed 交叉断言）。"""
    r11 = json.loads(RUN_R11.read_text(encoding="utf-8"))
    m11 = r11.get("hypothesis_test", {}).get("measurement", {})
    range_top = m11.get("range_top")
    range_bottom = m11.get("range_bottom")
    if range_top != R11_RANGE_TOP_ANCHOR or \
            range_bottom != R11_RANGE_BOTTOM_ANCHOR:
        _fail(f"run-r11 range 锚不符：range_top={range_top!r}（预期 "
              f"{R11_RANGE_TOP_ANCHOR!r}）、range_bottom={range_bottom!r}"
              f"（预期 {R11_RANGE_BOTTOM_ANCHOR!r}）")
    r25 = json.loads(RUN_R25.read_text(encoding="utf-8"))
    m25 = r25.get("hypothesis_test", {}).get("measurement", {})
    bcc = m25.get("baseline_cross_check", {})
    m1 = {}
    for key, anchor in (("r19_row_live", R19_M1_ANCHOR),
                        ("r22_row_live", R22_M1_ANCHOR),
                        ("r23_row_live", R23_M1_ANCHOR),
                        ("r24_row_live", R24_M1_ANCHOR)):
        row = bcc.get(key)
        got = (row or {}).get("M1") if isinstance(row, dict) else None
        if got != anchor:
            _fail(f"run-r25 baseline_cross_check.{key}.M1={got!r} != 锚 "
                  f"{anchor!r}")
        m1[key] = got
    t25 = m25.get("r25_m_tuple_6dp", {})
    got25 = t25.get("M1")
    if got25 != R25_M1_ANCHOR:
        _fail(f"run-r25 r25_m_tuple_6dp.M1={got25!r} != 锚 {R25_M1_ANCHOR!r}")
    m1["r25_m_tuple_6dp_M1"] = got25
    return {"r11_range_top": range_top, "r11_range_bottom": range_bottom,
            "dev_m1_values": m1}


def probe_manifests() -> dict:
    """F 步：split manifest 活读断言+stale 计数如实并列。"""
    kd = json.loads(MANIFEST_KD.read_text(encoding="utf-8"))
    pb = json.loads(MANIFEST_PB.read_text(encoding="utf-8"))
    kd_holdout = kd.get("dataset_splits", {}).get("holdout")
    pb_holdout = pb.get("dataset_splits", {}).get("holdout")
    if not isinstance(kd_holdout, list) or not isinstance(pb_holdout, list):
        _fail("manifest dataset_splits.holdout 结构不符（须为列表）")
    for board_id in KD_HOLDOUT_REQUIRED:
        if board_id not in kd_holdout:
            _fail(f"kicad-demos-r2 manifest holdout 缺 {board_id}")
    for board_id in PB_HOLDOUT_REQUIRED:
        if board_id not in pb_holdout:
            _fail(f"pcbench-r1-v3 manifest holdout 缺 {board_id}")
    kd_gc = kd.get("dataset_splits", {}).get("group_counts", {})
    pb_gc = pb.get("dataset_splits", {}).get("group_counts", {})
    _assert_eq(kd_gc.get("holdout"), KD_GROUP_COUNTS_HOLDOUT,
               "kicad-demos-r2 group_counts.holdout（对照、无 stale）")
    _assert_eq(len(kd_holdout), KD_GROUP_COUNTS_HOLDOUT,
               "kicad-demos-r2 holdout 列表长度==计数")
    _assert_eq(pb_gc.get("holdout"), PB_GROUP_COUNTS_HOLDOUT_STALE,
               "pcbench-r1-v3 group_counts.holdout（stale 计数在案锚）")
    _assert_eq(len(pb_holdout), PB_HOLDOUT_LIST_LEN,
               "pcbench-r1-v3 holdout 列表长度（操作口径）")
    return {
        "kd_holdout": kd_holdout, "pb_holdout": pb_holdout,
        "pb_group_counts_holdout": pb_gc.get("holdout"),
        "pb_holdout_len": len(pb_holdout),
        "kd_group_counts_holdout": kd_gc.get("holdout"),
        "kd_holdout_len": len(kd_holdout),
    }


def check_amendment_cross(amendment_text: str, manifests: dict) -> None:
    """amendment 活读交叉核对：stale 计数处置与三板源前缀在案（恰 1 次）。"""
    needles = [
        "group_counts.holdout=10",
        "ccc2efb5", "0d26bf9b", "1c76ac23",
        "kitspace_led_driver", "tiny_tapeout/tinytapeout-demo",
        "vme-wren/vme-wren",
    ]
    for needle in needles:
        n = amendment_text.count(needle)
        if n < 1:
            _fail(f"amendment 交叉核对缺在案锚：{needle!r}（处置引用失真，"
                  f"立即停止）")


def probe_boards() -> list:
    """G+H 步：板源 sha256 前缀核验+铜层 token 复核（纯函数、零图像），
    返回 3 板记录条目（记录序=kitspace_led_driver→tiny_tapeout→vme-wren）。"""
    tokens_by_board = {}
    sha_by_board = {}
    for short, path in BOARD_FILES.items():
        measured = _require_prefix_sha(path, BOARD_SHA_PREFIXES[short],
                                       f"板源 {short}")
        sha_by_board[short] = measured
        text = path.read_text(encoding="utf-8", errors="replace")
        tokens = sorted(set(COPPER_TOKEN_RE.findall(text)))
        want = COPPER_TOKEN_EXPECT[short]
        if len(tokens) != want:
            _fail(f"{short} 铜层 distinct token 数 {len(tokens)} != 声明值 "
                  f"{want}（token 集={tokens!r}）")
        tokens_by_board[short] = tokens
    boards = [
        {
            "board_id": "kitspace_led_driver",
            "source_dataset": "pcbench-r1-v3",
            "manifest_split": "holdout",
            "license": "MIT（kitspace 元数据 eulerlab/open-visual-stimulator）",
            "copper_layer_count": 2,
            "copper_layer_tokens": tokens_by_board["kitspace_led_driver"],
            "input_path_rel":
                "datasets/pcbench-r1/raw/kitspace_led_driver/processed.kicad_pcb",
            "input_sha256": sha_by_board["kitspace_led_driver"],
            "precheck_ready": True,
            "coverage_class": "2层简单板",
        },
        {
            "board_id": "tiny_tapeout/tinytapeout-demo",
            "source_dataset": "kicad-demos-r2",
            "manifest_split": "holdout",
            "license": "kicad-demos-r2 manifest license 字段（mixed per-demo，"
                       "目录显式优先）",
            "copper_layer_count": 4,
            "copper_layer_tokens": tokens_by_board["tiny_tapeout"],
            "input_path_rel":
                "datasets/kicad-demos-r1/raw/tiny_tapeout/tinytapeout-demo"
                ".kicad_pcb",
            "input_sha256": sha_by_board["tiny_tapeout"],
            "precheck_ready": True,
            "coverage_class": "4层复杂板",
            "note": "PLAN Tier1 表 #2 原行（两口径一致）",
        },
        {
            "board_id": "vme-wren/vme-wren",
            "source_dataset": "kicad-demos-r2",
            "manifest_split": "holdout",
            "license": "kicad-demos-r2 manifest license 字段（mixed per-demo，"
                       "目录显式优先）",
            "copper_layer_count": 12,
            "copper_layer_tokens": tokens_by_board["vme-wren"],
            "input_path_rel":
                "datasets/kicad-demos-r1/raw/vme-wren/vme-wren.kicad_pcb",
            "input_sha256": sha_by_board["vme-wren"],
            "precheck_ready": True,
            "coverage_class": "12层复杂板",
        },
    ]
    for b in boards:
        if b["copper_layer_count"] != len(b["copper_layer_tokens"]):
            _fail(f"{b['board_id']} copper_layer_count 与 token 数不一致"
                  f"（层数覆盖交叉核对失败）")
    return boards


# ---------------------------------------------------------------------------
# 记录构造（纯函数）
# ---------------------------------------------------------------------------

def build_record(*, chain_sha: dict, protected: dict, precheck_probe: dict,
                 baselines: dict, manifests: dict, boards: list,
                 anti_loosening_count: int) -> dict:
    """holdout-prep-record-r1 构造（任务规格字段逐字镜像；canonical JSON
    sort_keys 落盘）。活读值全部由参数注入、零函数内 IO。"""
    r11_top = baselines["r11_range_top"]
    r11_bottom = baselines["r11_range_bottom"]
    m1 = baselines["dev_m1_values"]
    record = {}
    record["schema_version"] = "3.0"
    record["kind"] = "tl2_holdout_r1_prep_record"
    record["holdout_id"] = HOLDOUT_ID
    record["declared_date"] = DATE_CONSTANT
    record["mandate"] = (
        "用户 2026-09-10 拍板「启动 holdout」=独立人工点触发正式运行"
        "（evaluation-protocol-v2.md §2.3/§4.5）；一次性运行，HOLDOUT-PLAN "
        "§一.2 一次性纪律生效")
    record["governance_chain"] = {
        "plan": {
            "path_rel": "out/v3-tl2/holdout/HOLDOUT-PLAN.md",
            "sha256": chain_sha["plan"],
            "note": "冻结件零回写（协议 v2 §2.1 哈希引用）",
        },
        "amendment": {
            "path_rel": "out/v3-tl2/holdout/HOLDOUT-PLAN-amendment-r1.md",
            "sha256": chain_sha["amendment"],
            "note": "本轮运行前差异收口（三项 precheck 差异处置+选板/指引/"
                    "渲染操作化）；markdown 工作文档非 canonical JSON 工件",
        },
        "precheck": {
            "path_rel": "out/v3-tl2/holdout/precheck-r1.json",
            "sha256": chain_sha["precheck"],
            "verdict": EXPECT_OVERALL_VERDICT,
            "ready_boards": EXPECT_BOARDS_READY,
            "boards_total": EXPECT_UNION_ON_DISK_TOTAL,
            "isolation": EXPECT_ISOLATION_VERDICT,
            "designation_date": EXPECT_DESIGNATION_DATE,
        },
        "protocol_v2": {
            "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v2.md",
            "sha256": chain_sha["protocol_v2"],
            "p2_clauses": "九条款逐条映射见 p2_clause_mapping",
        },
        "registration": {
            "path_rel":
                "out/v3-tl2/calibration/protocol-v2-registration.json",
            "sha256": chain_sha["registration"],
            "note": "协议 v2 登记件（活读前缀核验；结构补入槽位）",
        },
        "protocol_v1": {
            "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
            "sha256": chain_sha["protocol_v1"],
            "role": "R1–R25 历史口径载体；v1.1 多实例聚合口径与 v1.2 工具"
                    "行为规约经 v2 §0.3 继承执行",
        },
        "typology": {
            "path_rel":
                "out/v3-tl2/calibration/abstain-typology-r13-r16.json",
            "sha256": chain_sha["typology"],
            "note": "弃权分型 rubric 冻结件（r13–r16=8/15/5/10 链回放先核对"
                    "在案；结构补入槽位）",
        },
    }
    record["protected_files_verification"] = protected
    record["evaluation_domain"] = {
        "declared": "development",
        "in_calibrated_range": False,
        "note": "in_calibrated_range 恒 False 直到正式采纳；holdout 结果="
                "独立泛化证据，不构成采纳/晋升（P2-8）",
    }
    record["board_selection"] = {
        "selection_rule_quote": SELECT_RULE_QUOTE,
        "pool_definition": (
            "manifest holdout split（kicad-demos-r2 3 板 + pcbench-r1-v3 "
            "11 板）∩ precheck READY 8 板；Tier1 表 #1/#3/#4（manifest "
            "split=train）按 P2-1 剔除、#6 miniboard-stm32f0 盘上不存在删除"
            "（amendment §一 处置）"),
        "unselected_ready_boards_zero_render": precheck_probe["unselected"],
        "boards": boards,
        "copper_layer_token_method": COPPER_METHOD_NOTE,
        "holdout_split_live_check": {
            "kicad_demos_r2_holdout": manifests["kd_holdout"],
            "pcbench_r1_v3_holdout": manifests["pb_holdout"],
            "pcbench_group_counts_holdout_vs_list_len": {
                "group_counts_holdout": manifests["pb_group_counts_holdout"],
                "holdout_list_len": manifests["pb_holdout_len"],
                "note": "差异=stale 计数（manifest 随 schema 演进重生成遗"
                        "留），amendment §一.3 处置引用；操作口径=holdout "
                        "列表本身（盘上 11 板为准）；对照 kicad-demos-r2 "
                        "group_counts.holdout=3 与列表一致、无此问题",
            },
        },
    }
    record["instance_protocol"] = {
        "per_view_instances": 3,
        "views": ["top", "bottom"],
        "states": "每板单状态（外部板无 applied/prep1 双态）",
        "read_units": 18,
        "agents": 9,
        "agent_unit": "每 agent=1 板×1 实例，读 top+bottom 两图、产出 2 份 "
                      "reader 文件",
        "waves": "5+4 两波（并发≤6，运维细节非判据）",
        "lineage": "n=3×视角=r11 确立的多实例协议 v1.1（经协议 v2 §0.3 继"
                   "承）",
    }
    record["guidance_reuse"] = {
        "base": "observation-guidance-r25.md",
        "path_rel": "out/v3-tl2/calibration/observation-guidance-r25.md",
        "sha256": chain_sha["guidance_r25"],
        "zero_byte_reuse": True,
        "selection_rule_quote": GUIDANCE_RULE_QUOTE,
        "rationale": (
            "r25=训练环收束前最后产出版；训练环已收束（用户 2026-09-10 拍"
            "板），零新指引作者动作；guidance-r19「胜出（有条件）」为描述性"
            "定性、不入本轮"),
        "dispatch_layer_override": {
            "flag_prefix_top": "R25T→HOT",
            "flag_prefix_bottom": "R25B→HOB",
            "reader_id": "reader-r25-*→reader-holdout-<board>-{top,bottom}"
                         "-i{1,2,3}",
        },
        "override_nature": "命名属编排侧机械替换、非判据变更（r11/r16/r22/"
                           "r24 先例）",
        "anti_loosening_clause_count": anti_loosening_count,
    }
    record["naming_map"] = {
        "flag_sequences": "HOT/HOB 两序列、跨 9 派次全局连续（r24 跨板连续"
                          "先例）；每派次预留 100 号段",
        "slots": [
            {"slot": 1, "board": "kitspace_led_driver", "instance": "i1",
             "hot_range": [1, 100], "hob_range": [1, 100]},
            {"slot": 2, "board": "kitspace_led_driver", "instance": "i2",
             "hot_range": [101, 200], "hob_range": [101, 200]},
            {"slot": 3, "board": "kitspace_led_driver", "instance": "i3",
             "hot_range": [201, 300], "hob_range": [201, 300]},
            {"slot": 4, "board": "tiny_tapeout", "instance": "i1",
             "hot_range": [301, 400], "hob_range": [301, 400]},
            {"slot": 5, "board": "tiny_tapeout", "instance": "i2",
             "hot_range": [401, 500], "hob_range": [401, 500]},
            {"slot": 6, "board": "tiny_tapeout", "instance": "i3",
             "hot_range": [501, 600], "hob_range": [501, 600]},
            {"slot": 7, "board": "vme-wren", "instance": "i1",
             "hot_range": [601, 700], "hob_range": [601, 700]},
            {"slot": 8, "board": "vme-wren", "instance": "i2",
             "hot_range": [701, 800], "hob_range": [701, 800]},
            {"slot": 9, "board": "vme-wren", "instance": "i3",
             "hot_range": [801, 900], "hob_range": [801, 900]},
        ],
        "reader_file_pattern": (
            "out/v3-tl2/holdout/reader-raw-holdout-<board>-{top,bottom}"
            "-i{n}.txt（board 段取值：kitspace_led_driver / tiny_tapeout / "
            "vme-wren）"),
    }
    record["render_plan"] = {
        "pipeline_quote": (
            "kicad-cli pcb export pdf（--mode-single --scale 1 --check-zones "
            "--drill-shape-opt 2；top=F.Cu,F.Mask,F.Silkscreen,Edge.Cuts,"
            "F.Courtyard；bottom=B.Cu,B.Mask,B.Silkscreen,Edge.Cuts,"
            "B.Courtyard + --mirror）→ PyMuPDF 40pt 组合页 dpi640 光栅化 → "
            "板界实测+120px 裁剪（r4/r5 框架逐字同口径）"),
        "kicad_cli_version": "10.0.5",
        "output_dir": "out/v3-tl2/holdout/renders-holdout-r1/",
        "pngs": 6,
        "naming": "<board>-top.png / <board>-bottom.png（board 段同 "
                  "naming_map）",
        "framing_witness": (
            "render-framing-holdout-r1.json / render-witness-holdout-r1.json"
            "（canonical JSON、防覆写、确定性自证，s51 模式）"),
        "freeze_order": "prep-record → framing → render → witness → 盲读"
                        "（渲染先于盲读、后于判据冻结）",
    }
    record["measurement_design"] = {
        "abstain_unit": (
            "单位=旗标条数；分母=该读数域全部旗标；弃权旗单列不参与任何匹配"
            "（r9 §4 语义，字节复用生效）"),
        "per_cell": (
            "cell=(board×view)；实例弃权率 r_{b,v,i}=abstain/total"
            "（i∈{1,2,3}）；cell range=max−min；cell median"),
        "pooled": (
            "每视角跨 3 板 9 实例 pooled range/median；双视角合并 M1_pool="
            "总弃权/总旗标（逐板与合并双层）"),
        "flag_yield": (
            "逐 board×view×instance 旗标总数；类别分布用冻结 rubric "
            "abstain-typology-r13-r16.json（装载前先过 r13–r16=8/15/5/10 "
            "链回放）；rubric 对外部新域板的适用性=描述性外推、如实标注"),
        "r11_deviation": (
            f"与 r11 基线偏离如实报告（r11: top 极差 {r11_top} / bottom 极差 "
            f"{r11_bottom}；r11 为单板双态轮，跨设定比较=描述性）"),
        "r11_baseline_values": {
            "range_top": r11_top,
            "range_bottom": r11_bottom,
        },
        "dev_m1_reference": (
            "发展域 M1 参照集（活读 5 值：r19/r22/r23/r24/r25）；注意历史 "
            "M1=revc 双态轮口径，与 holdout M1_pool 跨设定比较=描述性并列、"
            "不进门"),
        "dev_m1_reference_values": {
            "r19_row_live_M1": m1["r19_row_live"],
            "r22_row_live_M1": m1["r22_row_live"],
            "r23_row_live_M1": m1["r23_row_live"],
            "r24_row_live_M1": m1["r24_row_live"],
            "r25_m_tuple_6dp_M1": m1["r25_m_tuple_6dp_M1"],
        },
        "baseline_sources": {
            "r11": "out/v3-tl2/calibration/calibration-run-r11.json",
            "r25": "out/v3-tl2/calibration/calibration-run-r25.json",
        },
        "letters": {
            "stable": "全部 6 个 cell range < 0.2",
            "unstable": "≥4 个 cell range ≥ 0.2",
            "mixed": "其余（介于两支之间）",
            "boundary_note": (
                "0.2=本轮预注册描述性边界，沿用 r11 prep-record 预注册边界"
                "口径；非 APR-0011 门、非任何正式谓词"),
            "discipline": (
                "字母按本判据机械判定；不得事后改写；「正确测出无效同样是"
                "有效证据」；null result 如实入账；n=3 小样本=方向性描述证"
                "据（development 域只描述不断言）"),
        },
    }
    record["gt_boundary"] = {
        "zero_gt_claims": (
            "外部语料无真实判例源（GT-AUDIT-R1 纪律）：正式 holdout 报告零 "
            "recall/seed_match 字样主张；GT 类指标=N/A+HOLDOUT-PLAN §一.1 "
            "纪律 1 引用"),
        "p2_clause_mapping": {
            "P2_1": "ok（三集按板隔离：选板全部来自 manifest holdout split；"
                    "precheck isolation_check.verdict=isolated）",
            "P2_2": "ok（reader 盲读：上下文=指引+渲染图+命名，零 GT 零诊断"
                    "零历史轮数据）",
            "P2_3": "N/A-by-discipline（一对一匹配需 GT；无 GT 语料，"
                    "HOLDOUT-PLAN §一.1）",
            "P2_4": "N/A-by-discipline（同上）",
            "P2_5": "N/A-by-discipline（同上；弃权旗照旧单列）",
            "P2_6": "ok（弃权率/产量/类别分布分列计算分列报告，不合并单一"
                    "分数）",
            "P2_7": "N/A-by-discipline（逐旗标人工裁定需 GT 语义；无 GT "
                    "语料）",
            "P2_8": "ok（阈值不晋升：本轮不构成采纳；in_calibrated_range 恒 "
                    "False；自动分流恒 blocked）",
            "P2_9": "ok（选板全部 precheck READY=hash 证齐；任一缺证即 "
                    "blocked 不入本轮）",
        },
    }
    record["one_shot_discipline"] = (
        "本轮=唯一正式 holdout 运行；渲染一次成型、盲读一次成型；派发报错≠"
        "未产出（幽灵 worker 先例）：缺失 reader 文件允许对同 slot 重派补齐"
        "（读数输入不变），已在盘 reader 文件零重写；运行后零重渲染零重读；"
        "失败中断如实入 dev-record")
    record["new_files_this_round"] = [
        "scripts/s91_holdout_prep_r1.py",
        "out/v3-tl2/holdout/HOLDOUT-PLAN-amendment-r1.md",
        "out/v3-tl2/holdout/holdout-prep-record-r1.json",
    ]
    record["no_visual_reading"] = True
    record["no_wallclock_note"] = (
        "日期=声明常量 2026-09-10；脚本零 wall-clock/零主机绝对路径/零网络/"
        "零 subprocess")
    record["user_directive_note"] = (
        "用户 2026-09-10 拍板启动 holdout 正式运行（后续工程尝试任务为独立"
        "工作线，不入本记录）")
    return record


def assert_no_absolute_paths(obj, repo_abs: str) -> None:
    """红线断言：记录内零主机绝对路径（全部仓库相对路径、正斜杠）。"""
    if isinstance(obj, str):
        if repo_abs in obj:
            _fail(f"记录含主机绝对路径片段：{obj[:60]!r}")
        if ":\\" in obj:
            _fail(f"记录含 Windows 盘符路径片段：{obj[:60]!r}")
        if obj.startswith("/"):
            _fail(f"记录含 POSIX 绝对路径：{obj[:60]!r}")
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_no_absolute_paths(k, repo_abs)
            assert_no_absolute_paths(v, repo_abs)
    elif isinstance(obj, list):
        for v in obj:
            assert_no_absolute_paths(v, repo_abs)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 开工：保护三文件全 64 位实测（第一次；A 步）----
    protected = check_protected()

    # ---- 前置存在性（fail-closed）----
    for path in (PLAN, AMENDMENT, PRECHECK, PROTOCOL_V2, PROTOCOL_V2_REG,
                 PROTOCOL_V1, GUIDANCE_R25, TYPOLOGY, RUN_R11, RUN_R25,
                 MANIFEST_KD, MANIFEST_PB):
        if not path.exists():
            _fail(f"缺失：{path}")
    for short, path in BOARD_FILES.items():
        if not path.exists():
            _fail(f"缺失板源 {short}：{path}")
    # 目标文件 RECORD 不做前置硬拒绝：落盘阶段防覆写护栏按红线口径执行——
    # 已存在且重建字节不同→FAIL；已存在且逐字节相同→幂等通过（零覆写）。

    # ---- B 步：治理链活读+前缀核验 ----
    chain_sha = check_governance_chain()

    # ---- PLAN 逐字引文在案锚（恰 1 次）----
    plan_text = PLAN.read_text(encoding="utf-8")
    check_plan_quotes(plan_text)

    # ---- C 步：反放宽条款断言 ----
    guidance_text = GUIDANCE_R25.read_text(encoding="utf-8")
    anti_loosening_count = check_anti_loosening(guidance_text)

    # ---- amendment 活读交叉核对（stale 计数处置+三板源前缀在案）----
    amendment_text = AMENDMENT.read_text(encoding="utf-8")

    # ---- E 步：precheck 活读断言+未选板派生 ----
    precheck = json.loads(PRECHECK.read_text(encoding="utf-8"))
    precheck_probe = probe_precheck(precheck)

    # ---- F 步：split manifest 活读断言+stale 计数并列 ----
    manifests = probe_manifests()
    check_amendment_cross(amendment_text, manifests)

    # ---- D 步：基线数字活读（在案锚交叉断言）----
    baselines = probe_baselines()

    # ---- G+H 步：板源前缀+铜层 token 复核 ----
    boards = probe_boards()

    # ---- 分型件 rubric 链回放（flag_yield 引用前先核对在案；s88 先例）----
    typology = json.loads(TYPOLOGY.read_text(encoding="utf-8"))
    probe_typology(typology)

    # ---- I 步：记录构建+断言 ----
    build_kwargs = dict(
        chain_sha=chain_sha, protected=protected,
        precheck_probe=precheck_probe, baselines=baselines,
        manifests=manifests, boards=boards,
        anti_loosening_count=anti_loosening_count)
    record = build_record(**build_kwargs)
    # 顶层键集合自证（任务规格 19 键）
    expect_keys = {
        "schema_version", "kind", "holdout_id", "declared_date", "mandate",
        "governance_chain", "protected_files_verification", "evaluation_domain",
        "board_selection", "instance_protocol", "guidance_reuse", "naming_map",
        "render_plan", "measurement_design", "gt_boundary",
        "one_shot_discipline", "new_files_this_round", "no_visual_reading",
        "no_wallclock_note", "user_directive_note",
    }
    missing = sorted(expect_keys - set(record.keys()))
    extra = sorted(set(record.keys()) - expect_keys)
    if missing or extra:
        _fail(f"顶层键集合不符：少={missing}，多={extra}")
    if record["schema_version"] != "3.0" or \
            record["kind"] != "tl2_holdout_r1_prep_record" or \
            record["holdout_id"] != HOLDOUT_ID or \
            record["declared_date"] != DATE_CONSTANT:
        _fail("记录身份键不符（schema_version/kind/holdout_id/declared_date）")
    if record["no_visual_reading"] is not True:
        _fail("no_visual_reading 必须为 True（零视觉判读红线）")
    if record["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("in_calibrated_range 必须为 False（P2-8 不晋升口径）")
    if record["guidance_reuse"]["zero_byte_reuse"] is not True or \
            record["guidance_reuse"]["anti_loosening_clause_count"] != 1:
        _fail("guidance_reuse 口径不符（零字节复用/反放宽条款恰 1 次）")
    if len(record["board_selection"]["boards"]) != 3 or \
            [b["board_id"] for b in record["board_selection"]["boards"]] != \
            list(SELECTED_BOARD_IDS):
        _fail("选板 3 板清单不符")
    if len(record["naming_map"]["slots"]) != 9:
        _fail(f"naming_map.slots 须恰 9 槽位："
              f"{len(record['naming_map']['slots'])}")
    if record["instance_protocol"]["read_units"] != 18 or \
            record["instance_protocol"]["agents"] != 9 or \
            record["instance_protocol"]["per_view_instances"] != 3:
        _fail("instance_protocol 口径不符（3×2×3=18 读数单位、9 agents）")
    if len(record["gt_boundary"]["p2_clause_mapping"]) != 9:
        _fail("p2_clause_mapping 须恰 9 条款")
    # 防呆：记录内活读值与实测锚同源（build_record 注入值==probe 装载值）
    if record["measurement_design"]["r11_baseline_values"] != \
            {"range_top": baselines["r11_range_top"],
             "range_bottom": baselines["r11_range_bottom"]}:
        _fail("r11 基线值与活读不符")
    dv = record["measurement_design"]["dev_m1_reference_values"]
    if dv != {"r19_row_live_M1": R19_M1_ANCHOR,
              "r22_row_live_M1": R22_M1_ANCHOR,
              "r23_row_live_M1": R23_M1_ANCHOR,
              "r24_row_live_M1": R24_M1_ANCHOR,
              "r25_m_tuple_6dp_M1": R25_M1_ANCHOR}:
        _fail("发展域 M1 参照集 5 值与活读不符")
    # 零主机绝对路径断言（落盘前）
    assert_no_absolute_paths(record, str(REPO))

    # 同参重建自证（纯函数）+ canonical bytes
    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(**build_kwargs)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: holdout-prep-record-r1")

    # ---- 落盘：holdout-prep-record-r1.json（防覆写护栏）----
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("holdout-prep-record-r1.json 已存在且重建字节不一致（防"
                  "覆写；拒绝覆写）")
        print("[holdout-prep-r1] 重跑自证：holdout-prep-record-r1.json 重建"
              "字节与既有文件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: holdout-prep-record-r1.json")

    # ---- 收工：保护三文件全 64 位实测（第二次）----
    protected_after = check_protected()
    if protected_after != protected:
        _fail("收工保护三文件 hash 与开工不一致（红线被破坏，立即停止）")
    if _sha(PLAN) != chain_sha["plan"]:
        _fail("收工 HOLDOUT-PLAN.md hash 与开工不一致（冻结件零回写红线被"
              "破坏）")
    if _sha(AMENDMENT) != chain_sha["amendment"]:
        _fail("收工 amendment hash 与开工不一致（活读登记件被改动）")

    # ---- 汇总打印 ----
    print("[holdout-prep-r1] 保护三文件开工/收工双验 PASS：pcbflow/cli.py="
          f"{CLI_PY_SHA[:8]}、pcbflow/config.py={CONFIG_PY_SHA[:8]}、"
          f"toolchain_lock.json={TOOLCHAIN_LOCK_SHA[:8]}（全 64 位实测一致，"
          f"强于前缀红线）")
    print("[holdout-prep-r1] 治理链 8 件活读 PASS：PLAN="
          f"{chain_sha['plan'][:8]}（冻结件零回写）、amendment="
          f"{chain_sha['amendment'][:8]}（活读、无前缀预期）、precheck="
          f"{chain_sha['precheck'][:8]}、protocol-v2="
          f"{chain_sha['protocol_v2'][:8]}、registration="
          f"{chain_sha['registration'][:8]}、protocol-v1="
          f"{chain_sha['protocol_v1'][:8]}、guidance-r25="
          f"{chain_sha['guidance_r25'][:8]}、typology="
          f"{chain_sha['typology'][:8]}")
    print("[holdout-prep-r1] 断言 PASS：反放宽句恰 1 次；PLAN 两条逐字引文"
          "恰 1 次；precheck（8 READY/19 全集/isolated/2026-09-07/"
          "conditional）；manifest（kd 恰含 2 板、pb 恰含 kitspace_led_"
          "driver、stale 10 vs 11 如实并列）；基线活读 r11 range_top="
          f"{baselines['r11_range_top']}/range_bottom="
          f"{baselines['r11_range_bottom']}、M1 参照集 5 值在案锚一致；板源"
          "前缀 ccc2efb5/0d26bf9b/1c76ac23；铜层 token 2/4/12；分型件链回放 "
          "8/15/5/10")
    print(f"[holdout-prep-r1] 工件 sha256：holdout-prep-record-r1.json="
          f"{_sha(RECORD)[:16]}")


if __name__ == "__main__":
    main()
