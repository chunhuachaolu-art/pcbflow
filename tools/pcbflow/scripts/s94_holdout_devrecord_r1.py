#!/usr/bin/env python
"""S94_HOLDOUT_DEVRECORD_R1：PCBFlow v3.0 holdout 正式运行 close 实施者
（dev-record 步）。

只新建两个文件：
  scripts/s94_holdout_devrecord_r1.py（本件）
  out/v3-tl2/holdout/holdout-dev-record-r1.json（canonical JSON、防覆写）

本脚本=装载引用器（零重算零改写）：字母与全部数字从冻结 run-record
装载引用；装载失败/缺键=FAIL 停止。机制观察/描述性比较为开发记录的
裁决文字，其中每一个可机械对拍的数字在构建时逐一与 run-record 装载值
断言相等（对拍不符=FAIL，禁止改数字凑文）。

输入（活读核前缀，不符 FAIL）：
  run-record out/v3-tl2/holdout/holdout-run-r1.json 前缀
      e64f882f2c02adab（字母/cell/池化/M1_pool/分型/链回放/零旗单位/
      结构变体/p2 执行状态/r11 与发展域参照值全部从它装载）
  引用复核（不重算、只核哈希一致）：prep-record（sha 从 run-record
      protocol 节装载并与盘上件实测对拍）、protocol_v2（同）、
      precheck-r1.json（前 8 位=7260027f）、witness degradation=null。

与任务简报的一处如实偏差：简报 p2 文本「3+3 ok、4 项 N/A」与
run-record p2_execution 机械计数不符（实测 ok=5：P2_1/P2_2/P2_6/
P2_8/P2_9；N/A-by-discipline=4：P2_3/P2_4/P2_5/P2_7）。本记录按实测
口径落笔（ok 计数由 run-record 原文机械统计，非手写数字）。

纪律：无 wall-clock（日期=声明常量 2026-09-10）；无 subprocess / 无
网络 / 无主机绝对路径（记录内 path_rel 全部仓库相对）；canonical JSON
=pcbflow.hashing.canonical_json_bytes；哈希=pcbflow.hashing.
sha256_file；PNG 零判读零读取；保护三文件（pcbflow/cli.py=0a738047、
pcbflow/config.py=f515c348、toolchain_lock.json=d43dad89）开工/收工各
验一次全 64 位 sha256；out/ 既有文件只读；记录落盘前断言无 gt_recall/
seed_match 键名、canonical bytes 无 C:\\ 与 C:/ 字样；同输入⇒
byte-exact 同输出（构建两次自证）+防覆写护栏（已存在且重建字节不同
→FAIL，相同→幂等零覆写）。

用法：python scripts/s94_holdout_devrecord_r1.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

# ---------------------------------------------------------------------------
# 声明常量与路径（零 wall-clock）
# ---------------------------------------------------------------------------

DECLARED_DATE = "2026-09-10"
HOLDOUT_ID = "holdout-r1"

RUN_REL = "out/v3-tl2/holdout/holdout-run-r1.json"
RUN_PREFIX = "e64f882f2c02adab"
RUN_PATH = REPO / RUN_REL

DEV_REL = "out/v3-tl2/holdout/holdout-dev-record-r1-v2.json"
#: v2 追加件（DEV-E0-004）：与 r1 冻结件差异恰=protected_files_
#: verification 的 cli.py 锚两处（6ed4f3fd 前缀→0a738047，铜环案接纳）；
#: r1 件零回写（test_protocol_v2_freeze 钉死 eeea2bb9 前缀不变）。
DEV_PATH = REPO / DEV_REL

PRECHECK_REL = "out/v3-tl2/holdout/precheck-r1.json"
WITNESS_REL = "out/v3-tl2/holdout/render-witness-holdout-r1.json"

PROTECTED = {
    "pcbflow/cli.py": "0a738047",
    "pcbflow/config.py": "f515c348",
    "toolchain_lock.json": "d43dad89",
}

FAMILIES = ["contact", "existence_blackdot", "existence_other",
            "semantic_confusion", "other"]


def _fail(msg: str) -> None:
    raise SystemExit(f"[s94-holdout-devrecord-r1] FAIL: {msg}")


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def _load_json(path: Path):
    if not path.exists():
        _fail(f"缺输入文件: {path.relative_to(REPO).as_posix()}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _req(obj, key: str, ctx: str):
    """装载缺键=FAIL（红线：装载失败/缺键一律 FAIL，不就地编造）。"""
    if not isinstance(obj, dict) or key not in obj:
        _fail(f"run-record 缺键: {ctx}.{key}")
    return obj[key]


def verify_protected() -> dict:
    out = {}
    for rel, prefix in PROTECTED.items():
        path = REPO / rel
        if not path.exists():
            _fail(f"保护文件缺失: {rel}")
        sha = _sha(path)
        out[rel] = {
            "sha256": sha,
            "expected_prefix": prefix,
            "match": sha.startswith(prefix),
        }
        if not out[rel]["match"]:
            _fail(f"保护文件前缀不符: {rel} sha256={sha} 预期前缀={prefix}")
    return out


def fixed6f(x: float) -> int:
    """已装载 6 位小数值 → 定点整数（仅用于对拍断言，不产生新数字）。"""
    return int(round(x * 1000000))


# ---------------------------------------------------------------------------
# 装载与对拍（全部数字从 run-record 装载；缺键/对拍不符=FAIL）
# ---------------------------------------------------------------------------

def load_run_record() -> tuple:
    if not RUN_PATH.exists():
        _fail(f"缺冻结 run-record: {RUN_REL}")
    sha = _sha(RUN_PATH)
    if not sha.startswith(RUN_PREFIX):
        _fail(f"run-record 前缀不符: {RUN_REL} sha256={sha} "
              f"预期前缀={RUN_PREFIX}")
    return _load_json(RUN_PATH), sha


def cross_check(run: dict) -> dict:
    """观察/比较文字中引用的全部数字与 run-record 装载值机械对拍。"""
    letters = _req(run, "letters", "")
    letter = _req(letters, "letter", "letters")
    cell_ranges = _req(letters, "cell_ranges", "letters")
    cells_ge = _req(letters, "cells_ge_0_2", "letters")
    if letter != "mixed":
        _fail(f"字母与已知裁决不符: {letter!r}")

    measurement = _req(run, "measurement", "")
    pooled = _req(measurement, "pooled_per_view", "measurement")
    m1 = _req(measurement, "m1_pool", "measurement")
    m1_total = _req(m1, "total", "measurement.m1_pool")
    typology = _req(run, "typology", "")
    fam = _req(typology, "abstain_family_distribution", "typology")
    replay = _req(typology, "chain_replay", "typology")
    replayed = _req(replay, "replayed_contact_chain",
                    "typology.chain_replay")
    registered = _req(replay, "registered_contact_chain",
                      "typology.chain_replay")
    replay_pass = _req(replay, "pass", "typology.chain_replay")
    reader = _req(run, "reader", "")
    zero_units = _req(reader, "zero_flag_units", "reader")
    parse_disc = _req(run, "parse_disclosures", "")
    per_file = _req(parse_disc, "per_file", "parse_disclosures")
    r11 = _req(run, "r11_deviation_descriptive", "")
    r11_base = _req(r11, "r11_baseline_values",
                    "r11_deviation_descriptive")
    dev_m1 = _req(run, "dev_m1_reference_descriptive", "")
    dev_m1_vals = _req(dev_m1, "dev_m1_reference_values",
                       "dev_m1_reference_descriptive")
    holdout_m1 = _req(dev_m1, "holdout_m1_pool_total",
                      "dev_m1_reference_descriptive")
    p2 = _req(run, "p2_execution", "")

    # o1 对拍：pooled bottom=1.0（10/10）vs top=0.625（15/24）
    pb = _req(pooled, "bottom", "measurement.pooled_per_view")
    pt = _req(pooled, "top", "measurement.pooled_per_view")
    if not (fixed6f(_req(pb, "abstain_rate", "pooled.bottom")) == 1000000
            and _req(pb, "rate_fraction", "pooled.bottom") == "10/10"):
        _fail("对拍失败: pooled bottom ≠ 1.0（10/10）")
    if not (fixed6f(_req(pt, "abstain_rate", "pooled.top")) == 625000
            and _req(pt, "rate_fraction", "pooled.top") == "15/24"):
        _fail("对拍失败: pooled top ≠ 0.625（15/24）")

    # o2 对拍：top 三板 range=0.8/1.0/1.0（全部≥0.2）、bottom 三板=0.0；
    # M1_pool=0.735294
    top_boards = ["kitspace_led_driver/top", "tiny_tapeout/top",
                  "vme-wren/top"]
    bottom_boards = ["kitspace_led_driver/bottom", "tiny_tapeout/bottom",
                     "vme-wren/bottom"]
    for key in top_boards + bottom_boards:
        if key not in cell_ranges:
            _fail(f"letters.cell_ranges 缺 cell: {key}")
    top_ranges = sorted(fixed6f(cell_ranges[k]) for k in top_boards)
    bottom_ranges = sorted(fixed6f(cell_ranges[k]) for k in bottom_boards)
    if top_ranges != [800000, 1000000, 1000000]:
        _fail(f"对拍失败: top 三 cell range ≠ 0.8/1.0/1.0: {top_ranges!r}")
    if bottom_ranges != [0, 0, 0]:
        _fail(f"对拍失败: bottom 三 cell range ≠ 全 0.0: "
              f"{bottom_ranges!r}")
    if cells_ge != sorted(top_boards) or len(cells_ge) != 3:
        _fail(f"对拍失败: cells_ge_0_2 ≠ top 三板: {cells_ge!r}")

    m1_val = fixed6f(_req(m1_total, "m1_pool", "m1_pool.total"))
    if not (m1_val == 735294
            and _req(m1_total, "fraction", "m1_pool.total") == "25/34"
            and _req(m1_total, "abstain", "m1_pool.total") == 25
            and _req(m1_total, "flags", "m1_pool.total") == 34):
        _fail("对拍失败: M1_pool total ≠ 0.735294（25/34）")
    if fixed6f(_req(holdout_m1, "value",
                    "dev_m1.holdout_m1_pool_total")) != m1_val:
        _fail("对拍失败: dev_m1 节 holdout M1_pool 与 measurement 节不等")

    # o3 对拍：弃权旗 25 条、分型 18/6/1/0/0；链回放 8/15/5/10 pass
    if sum(fam.get(f, 0) for f in FAMILIES) != 25:
        _fail(f"对拍失败: 分型总数 ≠ 25 条弃权旗: {fam!r}")
    if (fam.get("existence_other"), fam.get("other"),
            fam.get("existence_blackdot"), fam.get("contact"),
            fam.get("semantic_confusion")) != (18, 6, 1, 0, 0):
        _fail(f"对拍失败: 分型分布 ≠ 18/6/1/0/0: {fam!r}")
    if replay_pass is not True or replayed != registered \
            or registered != {"r13": 8, "r14": 15, "r15": 5, "r16": 10}:
        _fail(f"对拍失败: 链回放 ≠ 8/15/5/10 pass: "
              f"replayed={replayed!r} registered={registered!r} "
              f"pass={replay_pass!r}")

    # format_variances 对拍：per_image 变体=2、零旗单位=4
    n_per_image = sum(1 for row in per_file
                      if row.get("structure_variant") == "per_image")
    if n_per_image != 2:
        _fail(f"对拍失败: per_image 结构变体 ≠ 2 件: {n_per_image}")
    if len(zero_units) != 4:
        _fail(f"对拍失败: 零旗单位 ≠ 4: {len(zero_units)}")

    # descriptive_comparisons 对拍：发展域参照 5 值 + r11 基线
    ref_vals = sorted(fixed6f(v) for v in dev_m1_vals.values())
    if ref_vals != sorted([390244, 433735, 461538, 484848, 552381]):
        _fail(f"对拍失败: 发展域 M1 参照集 ≠ 预期 5 值: {ref_vals!r}")
    if m1_val <= max(ref_vals):
        _fail("对拍失败: holdout M1_pool 未高于参照集全部值")
    if (fixed6f(_req(r11_base, "range_top", "r11_baseline_values"))
            != 153846
            or fixed6f(_req(r11_base, "range_bottom",
                            "r11_baseline_values")) != 0):
        _fail("对拍失败: r11 基线 ≠ 0.153846/0.0")
    if not all(fixed6f(cell_ranges[k]) > 153846 for k in top_boards):
        _fail("对拍失败: top 三 cell 极差未全部高于 r11 range_top")
    if not all(fixed6f(cell_ranges[k]) == 0 for k in bottom_boards):
        _fail("对拍失败: bottom 三 cell 极差 ≠ r11 range_bottom=0.0")

    # discipline_compliance.p2 对拍：ok/N-A 计数机械统计 run-record 原文
    n_ok = sum(1 for v in p2.values()
               if isinstance(v, str) and v.startswith("ok（"))
    n_na = sum(1 for v in p2.values()
               if isinstance(v, str) and v.startswith("N/A-by-discipline"))
    if len(p2) != 9 or n_ok != 5 or n_na != 4:
        _fail(f"对拍失败: p2 九条款计数 ≠ 5 ok/4 N/A（实测 {n_ok}/{n_na}，"
              f"共 {len(p2)} 条）")

    # one_shot 对拍：18 件 reader 文件在案
    reader_files = _req(reader, "files", "reader")
    if len(reader_files) != 18:
        _fail(f"对拍失败: reader 文件 ≠ 18 件: {len(reader_files)}")

    return {
        "letter": letter,
        "cell_ranges": cell_ranges,
        "cells_ge_0_2": cells_ge,
        "n_ok": n_ok,
        "n_na": n_na,
        "protocol": _req(run, "protocol", ""),
        "one_shot_statement": _req(run, "one_shot_statement", ""),
    }


def verify_refs(loaded: dict) -> dict:
    """引用件活读核验（不重算、只核哈希一致；不符 FAIL）。"""
    protocol = loaded["protocol"]
    prep_ref = _req(protocol, "prep_record", "protocol")
    pv2_ref = _req(protocol, "protocol_v2", "protocol")
    prep_rel = _req(prep_ref, "path_rel", "protocol.prep_record")
    prep_sha = _req(prep_ref, "sha256", "protocol.prep_record")
    pv2_rel = _req(pv2_ref, "path_rel", "protocol.protocol_v2")
    pv2_sha = _req(pv2_ref, "sha256", "protocol.protocol_v2")
    for rel, sha in ((prep_rel, prep_sha), (pv2_rel, pv2_sha)):
        path = REPO / rel
        if not path.exists():
            _fail(f"引用件缺失: {rel}")
        disk_sha = _sha(path)
        if disk_sha != sha:
            _fail(f"引用件哈希与 run-record 装载值不符: {rel} "
                  f"disk={disk_sha} recorded={sha}")
    precheck_path = REPO / PRECHECK_REL
    if not precheck_path.exists():
        _fail(f"引用件缺失: {PRECHECK_REL}")
    precheck_prefix = _sha(precheck_path)[:8]
    if precheck_prefix != "7260027f":
        _fail(f"precheck 前缀不符: {precheck_prefix} 预期 7260027f")
    witness = _load_json(REPO / WITNESS_REL)
    if "degradation" not in witness or witness["degradation"] is not None:
        _fail("witness degradation ≠ null")
    return {
        "prep_record": {"path_rel": prep_rel, "sha256": prep_sha},
        "protocol_v2": {"path_rel": pv2_rel, "sha256": pv2_sha},
        "precheck": {"path_rel": PRECHECK_REL,
                     "sha256_prefix8": precheck_prefix},
    }


# ---------------------------------------------------------------------------
# 记录组装（裁决文字=主审给定；数字=装载引用）
# ---------------------------------------------------------------------------

def build_record(sha_start: dict) -> dict:
    run, run_sha = load_run_record()
    if run.get("holdout_id") != HOLDOUT_ID:
        _fail(f"run-record holdout_id 不符: {run.get('holdout_id')!r}")
    if run.get("declared_date") != DECLARED_DATE:
        _fail("run-record declared_date != 声明常量")
    if run.get("kind") != "tl2_holdout_r1_run_record":
        _fail(f"run-record kind 不符: {run.get('kind')!r}")

    loaded = cross_check(run)
    refs = verify_refs(loaded)

    protected_now = verify_protected()
    for rel, info in protected_now.items():
        if info["sha256"] != sha_start[rel]["sha256"]:
            _fail(f"保护文件在运行中途发生变化: {rel}")

    return {
        "schema_version": "3.0",
        "kind": "tl2_holdout_r1_dev_record",
        "holdout_id": HOLDOUT_ID,
        "declared_date": DECLARED_DATE,
        "round_nature": (
            "正式 holdout 评估（一次性）；评估-only：零迭代、零指引变更、"
            "零后续轮（训练环已收束=用户 2026-09-10 拍板）"),
        "run_record_ref": {
            "path_rel": RUN_REL,
            "sha256": run_sha,
            "sha256_prefix_expected": RUN_PREFIX,
            "prefix_match": True,
            "note": "字母与全部数字从它装载引用；本步零重算零改写",
        },
        "prep_record_ref": {
            **refs["prep_record"],
            "note": "引用（哈希与 run-record 装载值逐字对拍一致；"
                    "字母判据/度量设计冻结于该件）",
        },
        "protocol_v2_ref": {
            **refs["protocol_v2"],
            "note": "引用（§2.1 冻结件零回写）",
        },
        "letter": {
            "value": loaded["letter"],
            "source": "holdout-run-r1.json letters（冻结判据机械判定）",
            "cell_ranges": loaded["cell_ranges"],
            "cells_ge_0_2": loaded["cells_ge_0_2"],
            "no_override_note": (
                "字母不得事后改写；「正确测出无效同样是有效证据」"),
        },
        "mechanism_observations": [
            "o1 视角不对称：pooled bottom 弃权率=1.0（10/10）vs top=0.625"
            "（15/24）；bottom 高弃权与 framing 预注册的默认配色局限注记"
            "方向一致（外部板 bottom 可定位线索更少），亦与开发域 r13 以来"
            " bottom 语义可判读性弱的谱系一致——均为描述性对齐、非因果主张",
            "o2 离散集中在 top：3 板 top cell range=0.8/1.0/1.0（全部"
            "≥0.2），bottom 三板 range 全 0.0——未见板上实例异质性与开发域"
            " r24 发现（逐实例离散超出抽样尺度、聚合稳个体散）同构："
            "M1_pool 0.735294 与个体双峰（同 cell 内 0.0 与 1.0 并存）"
            "并存；n=3 小样本描述性",
            "o3 分型谱系外移：弃权旗 25 条中 existence_other=18、other=6"
            "（未命中注册关键词的『候选解释逐条枚举』措辞，r25 三问条款的"
            "行为痕迹）、existence_blackdot=1、contact=0、semantic=0——"
            "开发域 revc 特有的黑点/接触现象族在外部板近乎缺席（rubric 域"
            "外推注记在 run-record）；contact=0 与开发域『接触性判据使 top"
            " 弃权高企』谱系形成对照",
        ],
        "descriptive_comparisons": {
            "dev_m1_reference": (
                "holdout M1_pool=0.735294 高于发展域参照集 [0.390244(r22), "
                "0.433735(r25), 0.461538(r19), 0.484848(r23), "
                "0.552381(r24)] 全部值——未见板（外部新域）弃权率抬升方向与"
                "泛化间隙直觉一致；跨口径（双态轮 vs 单态外部板）描述性"
                "并列、不进门、小样本"),
            "r11_range_reference": (
                "r11 基线 top 极差 0.153846/bottom 0.0；本轮 top 三 cell "
                "极差全部 >0.153846，bottom 三 cell 与 r11 bottom 同为 "
                "0.0——top 逐实例稳定性低于 r11 基线、bottom 一致性同型"),
        },
        "letter_reading": (
            "mixed=既非全稳定（stable 需全部 6 cell<0.2）也非多数失稳"
            "（unstable 需≥4 cell≥0.2）：bottom 全部稳定（含 4 个零旗单位"
            "按 0/0→None 约定），top 三板全部失稳。作为独立泛化证据的含义="
            "弃权率/产量稳定性在未见板上【视角分异】：bottom 可稳定复现"
            "（高弃权但一致），top 对实例采样敏感。此为评估结论非门判定，"
            "不构成任何采纳/晋升/自动分流依据（P2-8）"),
        "discipline_compliance": {
            "one_shot": (
                "18/18 派次一次成型、零重派零补派；渲染一次成型（witness "
                "degradation=null）；预检 zero_render/zero_reader 在案"
                "（precheck-r1.json 7260027f）"),
            "p2": (
                f"九条款执行状态照 run-record p2_execution（"
                f"{loaded['n_ok']} 项 ok、{loaded['n_na']} 项 "
                f"N/A-by-discipline=外部语料无 GT 判例源，HOLDOUT-PLAN "
                f"§一.1；计数由 run-record 原文机械统计；任务简报「3+3 ok」"
                f"与实测 5 项 ok 不符，按实测口径落笔）"),
            "zero_gt_claims": (
                "全记录零 recall/seed_match 主张（run-record 自检断言在案）"),
            "domain": (
                "development 域标记不动；in_calibrated_range 恒 False；"
                "自动分流恒 blocked"),
        },
        "format_variances": (
            "两件 per_image 结构变体（kitspace_led_driver top/bottom i1）"
            "容错解析零改写，r11 先例同口径；零旗 4 单位 None 约定=r10/r11 "
            "同口径（run-record reader 节在案）"),
        "chain_replay_note": (
            "rubric 链回放 pass（8/15/5/10 注册口径=全轮 12 件；"
            "prep1-only 子集差异如实并列在 run-record typology 节）"),
        "next_candidate_suggestion": (
            "三选项如实单列、由用户拍板、不预写决策：(a) 采纳本 holdout 为"
            "校准线的独立泛化证据入档（记录性）；(b) 与正式采纳决定捆绑"
            "（采纳评估需人工批准，P2-8）；(c) 归档封存不再使用（发展域收束"
            "现状不变）。无 (d) 迭代选项——训练环已收束，任何新迭代须新"
            "预注册+用户拍板"),
        "no_wallclock_note": (
            "零 wall-clock/零网络/零 subprocess；日期=声明常量 "
            f"{DECLARED_DATE}；字母与全部数字=run-record 装载引用、本步"
            "零重算零改写；PNG 零判读零读取"),
        "protected_files_verification": {
            rel: {
                "sha256": info["sha256"],
                "expected_prefix": info["expected_prefix"],
                "match": info["match"],
            } for rel, info in protected_now.items()
        },
    }


# ---------------------------------------------------------------------------
# 自检（记录落盘前）
# ---------------------------------------------------------------------------

FORBIDDEN_KEYS = ("gt_recall", "seed_match")


def _walk_keys(obj):
    if isinstance(obj, dict):
        for key, val in obj.items():
            yield key
            yield from _walk_keys(val)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_keys(item)


def self_check(record: dict, record_bytes: bytes) -> None:
    for key in _walk_keys(record):
        if key in FORBIDDEN_KEYS:
            _fail(f"自检失败：记录出现禁用键名 {key!r}")
    for marker in (b"C:\\", b"C:/"):
        if marker in record_bytes:
            _fail(f"自检失败：canonical bytes 出现主机绝对路径字样 "
                  f"{marker!r}")


# ---------------------------------------------------------------------------
# 落盘（防覆写护栏）与收工核验
# ---------------------------------------------------------------------------

def main() -> int:
    sha_start = verify_protected()  # 开工验保护三文件

    record1 = build_record(sha_start)
    record2 = build_record(sha_start)
    bytes1 = hashing.canonical_json_bytes(record1)
    bytes2 = hashing.canonical_json_bytes(record2)
    if bytes1 != bytes2:
        _fail("确定性自证失败：同输入两次构建 canonical bytes 不一致")
    self_check(record1, bytes1)

    if DEV_PATH.exists():
        existing = DEV_PATH.read_bytes()
        if existing != bytes1:
            _fail(f"防覆写护栏：{DEV_REL} 已存在且重建字节不同")
        print(f"[s94] 幂等零覆写：{DEV_REL} 已存在且与重建字节一致")
    else:
        DEV_PATH.write_bytes(bytes1)
        written = DEV_PATH.read_bytes()
        if written != bytes1:
            _fail("落盘后回读验字节失败")
        print(f"[s94] 已落盘 {DEV_REL}（{len(bytes1)} bytes）")

    sha_end = verify_protected()  # 收工再验保护三文件
    for rel in PROTECTED:
        if sha_end[rel] != sha_start[rel]:
            _fail(f"收工保护文件核验不符: {rel}")

    record_hash = hashing.sha256_file(str(DEV_PATH))
    print("[s94] dev-record sha256 前 16 位:", record_hash[:16])
    print("[s94] letter:", record1["letter"]["value"],
          "| source:", record1["letter"]["source"])
    print("[s94] run_record_ref:",
          record1["run_record_ref"]["path_rel"],
          record1["run_record_ref"]["sha256"][:16])
    print("[s94] p2 实测计数:",
          f"{record1['discipline_compliance']['p2'][:40]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
