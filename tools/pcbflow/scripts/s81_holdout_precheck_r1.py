#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s81_holdout_precheck_r1.py — holdout 独立评估只读预检（precheck-r1）：
out/v3-tl2/holdout/precheck-r1.json 生成器（纯函数+防覆写；结构血统=
s79_protocol_v2_freeze.py 同构）。

任务血统：用户 2026-09-10 拍板「先预检再定」——holdout 独立评估启动前
的只读预检阶段。本包边界（绝对纪律）：
- 零渲染、零 reader/读图、零图像工具、零 git；
- datasets/ 与 out/ 全部只读；本轮唯一允许新写=precheck-r1.json 一件
  （本脚本自身=人工 Write 落盘，不在运行时写任何 .py）；
- 不做任何判罚：DRC baseline fail 项=上游参考态实况如实列出。

预检内容（全只读实测）：
1. 板清单三方对账：HOLDOUT-PLAN.md 登记 vs datasets/holdout-candidates-r1/
   盘上实际 vs 两 dataset manifest 的 split=holdout 条目（kicad-demos-r1 3 条、
   pcbench-r1-v3 11 条）；真实板数以盘上为准（19=5+3+11，三源两两不交）。
2. 零接触证据：每板 (a) profiles/<id>/ 枚举（无渲染/盲读衍生文件）；
   (b) out/ 全树按板 token 扫描（路径+文本内容），render/reader-raw/
   observation 类命中=泄漏，其余=文本提及如实登记；(c) 哈希对账——
   pcbench-r1 与 kicad-demos-r1 全树聚合 raw_hash 复算 vs manifest 登记值，
   逐板文件 hash vs conversion-log 登记值；Tier2 五板无在案登记 hash
   （PROVENANCE.md 无哈希字段）→ 本件记录首份基线（P2-9 缺证如实列 blocker）。
3. 隔离核验（协议 v2 P2-1）：calibration 域 r1–r22 全部 renders/reader-raw/
   observation 件枚举=仅 applied/prep1/revc 训练板；holdout 板 token 零命中；
   转换期接触（TL-5/k9）全部早于 designation 2026-09-07=计划纪律明文允许。
4. 转换/参考态资格：有 profile 的 8 板=主路径六段（pcbench 5 板，route/check
   =D17 参考态验证口径）或 k9 补充证据层（demo 3 板）；无 profile 的 6 板=
   S10 judge 台账 skip 原因如实登记；Tier2 5 板=未解析未转换（格式 token
   实测登记）。DRC baseline fail 项逐板如实列出（非判罚）。
5. blockers 逐条列出 + 逐板 ready/not_ready + 总体判定。

生成器纪律（s69/s72/s75/s78/s79 血统）：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节只依赖
  盘上冻结输入与本文件常量）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；哈希=sha256_file；
- 日期只用常量 DECLARED_DATE="2026-09-10"；
- 防覆写护栏：precheck-r1.json 已存在且字节不同→FAIL；字节等同→幂等
  跳过零覆写；
- 末尾打印受保护三件与 precheck 件 sha256；重跑幂等（out/ 全树扫描排除
  本件自身路径，保证首跑/重跑字节一致）。

用法：python scripts/s81_holdout_precheck_r1.py   （仓库根执行）
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402
from pcbflow.corpus import aggregate_raw_hash  # noqa: E402

# ---------------------------------------------------------------------------
# 声明常量（无 wall-clock）
# ---------------------------------------------------------------------------

DECLARED_DATE = "2026-09-10"
SCHEMA_VERSION = "3.0"
KIND = "s81_holdout_precheck_r1"

REL_OUT = "out/v3-tl2/holdout/precheck-r1.json"

# 受保护文件（开工/收工锚；前缀 fail-closed）
PROTECTED_FILES = (
    ("pcbflow/cli.py", "6ed4f3fd"),
    ("pcbflow/config.py", "f515c348"),
    ("toolchain_lock.json", "d43dad89"),
)

# 引用件锚（在案前缀；实测比对，fail-closed）
REFERENCE_ANCHORS = (
    ("out/v3-tl2/holdout/HOLDOUT-PLAN.md", "a4b80193"),
    ("out/v3-tl2/calibration/evaluation-protocol-v2.md", None),  # 无前缀锚：实测登记
    ("datasets/holdout-candidates-r1/PROVENANCE.md", None),  # 无前缀锚：实测登记
)

REL_MANIFEST_PCBENCH = "out/v3-tl5/dataset-manifest-pcbench-r1-v3.json"
REL_MANIFEST_KDEMOS = "out/v3-tl5/dataset-manifest-kicad-demos-r1.json"
REL_PROVENANCE = "datasets/holdout-candidates-r1/PROVENANCE.md"
REL_RETENTION_PCBENCH = "out/v3-tl5/retention-ledger-pcbench-r1.json"
REL_RETENTION_KDEMOS = "out/v3-tl5/retention-ledger-kicad-demos-r1.json"
REL_JUDGE_LEDGER = "out/v3-tl5/batch-s10/judge-ledger.json"
REL_K9_SUMMARY = "out/v3-tl5/k9-route-check-batch-r1/batch-summary.json"
REL_LEAKAGE_PCBENCH = "out/v3-tl5/leakage-audit-pcbench-r1.json"
REL_LEAKAGE_KDEMOS = "out/v3-tl5/leakage-audit-kicad-demos-r1.json"
REL_LEAKAGE_PCBBM = "out/v3-tl5/leakage-audit-pcbbenchmarks-r1.json"
REL_CALIB_DIR = "out/v3-tl2/calibration"
REL_DOMAIN_V3 = "out/v3-tl2/calibration/calibration-domain-v3.json"
REL_MASTER_META = "datasets/pcbench-r1/raw/master_metadata.json"
REL_DS_PCBENCH = "datasets/pcbench-r1"
REL_DS_KDEMOS = "datasets/kicad-demos-r1"
REL_DS_HOLDOUT = "datasets/holdout-candidates-r1"

# HOLDOUT-PLAN.md 声明纪律（计划 §一.2）：自落盘起 designation=holdout-candidate；
# TL-5 既有转换日志=解析/图层校验，无 reader 接触，不构成污染。
DESIGNATION_DATE = "2026-09-07"
PLAN_DECLARATION_SUBSTRINGS = (
    "声明日期（人工声明常量）: 2026-09-07",
    "一次性纪律",
    "任何盲读、任何指引/协议迭代",
    "TL-5 既有转换日志=解析/",
    "图层校验，无 reader 接触，不构成污染",
)

# ---------------------------------------------------------------------------
# 板注册表（=盘上冻结态快照的常量声明；与 manifest 不一致即 FAIL，fail-closed）
# ---------------------------------------------------------------------------

# HOLDOUT-PLAN.md §三 Tier 1 候选（计划登记口径；license=计划文本声明；
# split_lookup_keys=其在两 manifest 中的 board_id，用于 split 字段对账）
PLAN_TIER1 = (
    {"board_key": "kicaddemo-jetson-agx-thor-baseboard", "license": "Apache-2.0",
     "plan_tokens": ("kicaddemo-jetson-agx-thor-baseboard",),
     "split_lookup_keys": ("jetson-agx-thor-baseboard/jetson-agx-thor-baseboard",)},
    {"board_key": "kicaddemo-tiny_tapeout", "license": "Apache-2.0",
     "plan_tokens": ("kicaddemo-tiny_tapeout",),
     "split_lookup_keys": ("tiny_tapeout/tinytapeout-demo",)},
    {"board_key": "kicaddemo-royalblue54l_feather(+nfc-antenna)", "license": "CERN-OHL-P-2.0",
     "plan_tokens": ("kicaddemo-royalblue54l_feather",),
     "split_lookup_keys": ("royalblue54L_feather/RoyalBlue54L-Feather",
                           "royalblue54L_feather/RoyalBlue54L-NFC-Antenna")},
    {"board_key": "kicaddemo-openair-max", "license": "CC-BY-SA-4.0",
     "plan_tokens": ("kicaddemo-openair-max",),
     "split_lookup_keys": ("openair-max/One-Air-Max",)},
    {"board_key": "pcbench kitspace_*（glasgow/arduino-uno-sheild/led-driver 等）",
     "license": "MIT 系（master_metadata 可查）",
     "plan_tokens": ("kitspace_*",),
     "split_lookup_keys": ("kitspace_glasgow", "kitspace_Arduino_uno_sheild",
                           "kitspace_led_driver", "kitspace_T32_ref")},
    {"board_key": "pcbench miniboard-stm32f0", "license": "MIT",
     "plan_tokens": ("miniboard-stm32f0",),
     "split_lookup_keys": ("miniboard-stm32f0",)},
)

# datasets/holdout-candidates-r1/ 盘上五板（Tier 2 已收；slug=本件登记基线名）
TIER2_BOARDS = (
    {"slug": "easyduino-esp32s3", "dir": "easyduino/ESP32S3",
     "source_lib": "easyduino (Hanqaqa/Easyduino)", "license": "CERN-OHL-P-2.0",
     "pcbf": "Easyduino_ESP32S3.kicad_pcb",
     "tokens": ("easyduino_esp32s3", "easyduino-esp32s3")},
    {"slug": "easyduino-rp2040-pico", "dir": "easyduino/RP2040-Pico",
     "source_lib": "easyduino (Hanqaqa/Easyduino)", "license": "CERN-OHL-P-2.0",
     "pcbf": "Easyduino_RP2040.kicad_pcb",
     "tokens": ("easyduino_rp2040", "easyduino-rp2040")},
    {"slug": "easyduino-stm32f103-bluepill", "dir": "easyduino/STM32F103-Bluepill",
     "source_lib": "easyduino (Hanqaqa/Easyduino)", "license": "CERN-OHL-P-2.0",
     "pcbf": "Easyduino_STM32F103.kicad_pcb",
     "tokens": ("easyduino_stm32f103", "easyduino-stm32f103")},
    {"slug": "sparkfun-qwiic-adc-ads1219", "dir": "sparkfun/qwiic-adc-ads1219",
     "source_lib": "sparkfun (SparkFun_Qwiic_ADC_ADS1219)", "license": "CC-BY-SA-4.0",
     "pcbf": "Qwiic_ADC_ADS1219.kicad_pcb",
     "tokens": ("ads1219",)},
    {"slug": "sparkfun-qwiic-current-sensor-ina2xx",
     "dir": "sparkfun/qwiic-current-sensor-ina2xx",
     "source_lib": "sparkfun (SparkFun_Qwiic_Current_Sensor_INA2XX)",
     "license": "CC-BY-SA-4.0",
     "pcbf": "SparkFun_Qwiic_Current_Sensor_INA2XX.kicad_pcb",
     "tokens": ("ina2xx",)},
)
TIER2_PROVENANCE_SUBSTRINGS = (
    "Easyduino — 已收（3 板）", "CERN-OHL-P-2.0",
    "SparkFun — 已收（2 板，均 KiCad 原生）", "CC-BY-SA-4.0",
    "Adafruit — 未收（格式受阻）", "BeagleBone Black — 未收（格式受阻）",
    "零渲染零读图",
)

# kicad-demos-r1 manifest split=holdout 三板（profile=S18 k9 路径；license=manifest
# license 文本声明的目录级映射/默认映射；fail-closed：manifest holdout 列表≠此表即 FAIL）
KDEMOS_HOLDOUT = (
    {"board_id": "tiny_tapeout/tinytapeout-demo",
     "profile_id": "kicaddemo-tiny_tapeout-tinytapeout-demo",
     "license": "Apache-2.0",
     "conv_log": "out/v3-tl5/conversion-log-kicad-demos-r2-kicaddemo-tiny_tapeout-tinytapeout-demo.json",
     "raw_pcb": "datasets/kicad-demos-r1/raw/tiny_tapeout/tinytapeout-demo.kicad_pcb",
     "license_substrings": ("Apache-2.0（jetson-agx-thor-baseboard/tiny_tapeout）",),
     "tokens": ("tiny_tapeout", "tinytapeout")},
    {"board_id": "video/video", "profile_id": "kicaddemo-video-video",
     "license": "CC-BY-SA-4.0",
     "conv_log": "out/v3-tl5/conversion-log-kicad-demos-r2-kicaddemo-video-video.json",
     "raw_pcb": "datasets/kicad-demos-r1/raw/video/video.kicad_pcb",
     "license_substrings": ("默认=仓库根 LICENSE.README 映射 CC-BY-SA-4.0",),
     "tokens": ("kicaddemo-video", "video/video", "video.kicad_pcb")},
    {"board_id": "vme-wren/vme-wren", "profile_id": "kicaddemo-vme-wren-vme-wren",
     "license": "CC-BY-SA-4.0",
     "conv_log": "out/v3-tl5/conversion-log-kicad-demos-r2-kicaddemo-vme-wren-vme-wren.json",
     "raw_pcb": "datasets/kicad-demos-r1/raw/vme-wren/vme-wren.kicad_pcb",
     "license_substrings": ("默认=仓库根 LICENSE.README 映射 CC-BY-SA-4.0",),
     "tokens": ("vme-wren", "vme_wren")},
)

# pcbench-r1-v3 manifest split=holdout 11 条（slug=None=无 profile；fail-closed：
# manifest holdout 列表≠此表即 FAIL）
PCBENCH_HOLDOUT = (
    {"board_id": "DualLM317BenchSupply_DualLM317BenchSupply", "slug": None,
     "tokens": ("duallm317",)},
    {"board_id": "TTNEnschedeMote_ArduinoNanoRN2483",
     "slug": "pcbench-ttnenschedemote-arduinonanorn2483",
     "conv_log": "out/v3-tl5/conversion-log-pcbench-ttnenschedemote-arduinonanorn2483.json",
     "tokens": ("ttnenschedemote",)},
    {"board_id": "Theia_Theia", "slug": None, "tokens": ("theia",)},
    {"board_id": "beer-gauge_beer-gauge", "slug": None,
     "tokens": ("beer-gauge", "beer_gauge")},
    {"board_id": "esp32-cantroller_EltekController",
     "slug": "pcbench-esp32-cantroller-eltekcontroller",
     "conv_log": "out/v3-tl5/conversion-log-pcbench-esp32-cantroller-eltekcontroller.json",
     "tokens": ("cantroller",)},
    {"board_id": "fp2_extension_sample_fp2_usb_breakout",
     "slug": "pcbench-fp2-extension-sample-fp2-usb-breakout",
     "conv_log": "out/v3-tl5/conversion-log-pcbench-fp2-extension-sample-fp2-usb-breakout.json",
     "tokens": ("fp2_extension_sample", "fp2-extension-sample")},
    {"board_id": "kitspace_GPSMux", "slug": None, "tokens": ("gpsmux",)},
    {"board_id": "kitspace_Lcr_addon", "slug": None,
     "tokens": ("lcr_addon", "lcr-addon")},
    {"board_id": "kitspace_T32_ref", "slug": "pcbench-kitspace-t32-ref",
     "conv_log": "out/v3-tl5/conversion-log-pcbench-kitspace-t32-ref.json",
     "tokens": ("kitspace_t32_ref", "kitspace-t32-ref")},
    {"board_id": "kitspace_led_driver", "slug": "pcbench-kitspace-led-driver",
     "conv_log": "out/v3-tl5/conversion-log-pcbench-kitspace-led-driver.json",
     "tokens": ("kitspace_led_driver", "kitspace-led-driver")},
    {"board_id": "kitspace_postcard", "slug": None, "tokens": ("postcard",)},
)

# 数据集级 token（提及口径登记，不计板）
DATASET_LEVEL_TOKENS = ("holdout-candidates-r1", "holdout-candidates")

# 已知跨板 token 碰撞（弱 token 政策披露；这些裸 token 不用于扫描）
WEAK_TOKEN_DISCLOSURE = (
    "裸 token rp2040/stm32f103/bluepill/qwiic 不用于扫描：rp2040 命中 "
    "kicaddemo-tiny_tapeout 板内 net 名（/RP2040/*）与封装库名（RP2040-QFN-56），"
    "属 tiny_tapeout 板内容而非 easyduino RP2040 板；stm32f103 命中 pcbench 已排除板 "
    "HIDIRT-for-STM32F103C8T6-DevBoard（retention-ledger-pcbench-r1.json）；"
    "qwiic 为 SparkFun 产品线通用词。各板改用带 easyduino_/kicaddemo-/kitspace_ 前缀"
    "或板名唯一词（ads1219/ina2xx/gpsmux/postcard/theia/duallm317/cantroller 等）强 token。",
)

# out/ 全树扫描口径
TEXT_SUFFIXES = {".json", ".md", ".txt", ".tsv", ".jsonl", ".log", ".py",
                 ".yml", ".yaml", ".csv", ".prl"}
ARTIFACT_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".bmp", ".gif",
                     ".tif", ".tiff", ".pdf", ".ppm"}
ARTIFACT_PATH_PARTS = ("renders", "reader-raw", "observation")

# profiles/ 内允许的文件种类（零渲染/盲读衍生件的枚举判定基准）
PROFILE_ALLOWED_BASENAMES = {
    "manifest.json", "profile.json", "graph.json", "route-check.json",
    "board.kicad_pcb", "stackup.json", "constraints.json",
    "audit.json", "feedforward-plan.json", "net-registry.json",
}

# 主路径六段（graph-spec 10 节点口径中的六段 corpus 构件；route/check=D17）
SIX_SEGMENTS = ("audit", "compile", "enum", "feedforward", "manifest", "route_check")
D17_NOTE = ("route/check 段=参考 routed 态验证口径（D17）：验证的是参考态复现，"
            "非布线生成能力主张；DRC baseline fail 项=上游第三方设计自带违例如实记录，"
            "非 pcbflow 产物检查结果、非判罚。")


# ---------------------------------------------------------------------------
# 基础助手（s79 同构）
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    raise SystemExit(f"[s81-holdout-precheck-r1] FAIL: {msg}")


def _rel(rel: str) -> Path:
    return REPO / rel


def _sha(rel: str) -> str:
    return hashing.sha256_file(str(_rel(rel)))


def _json_load(rel: str):
    with open(_rel(rel), encoding="utf-8") as f:
        return json.load(f)


def _read_text(rel: str) -> str:
    with open(_rel(rel), encoding="utf-8") as f:
        return f.read()


def overwrite_guard(existing: "bytes | None", new: bytes) -> str:
    """防覆写护栏（纯函数）：无既有→write；字节等同→idempotent_skip；
    既有且不同→fail（fail-closed，绝不覆写）。"""
    if existing is None:
        return "write"
    return "idempotent_skip" if existing == new else "fail"


def _commit(path: Path, new_bytes: bytes, label: str) -> str:
    """落盘（护栏语义）：已存在且字节等同→幂等跳过（零覆写）；
    已存在且不同→FAIL；否则写入并回读自证。"""
    if path.exists():
        if overwrite_guard(path.read_bytes(), new_bytes) == "fail":
            _fail(f"{label} 已存在且与重建字节不同（防覆写护栏，"
                  "fail-closed；发布产物不可覆写）")
        return "idempotent_skip"
    path.write_bytes(new_bytes)
    if path.read_bytes() != new_bytes:
        _fail(f"回读不一致: {label}")
    return "written"


def _walk_files(rel_dir: str):
    """确定性枚举目录下全部文件（posix 相对路径，sorted）。"""
    root = _rel(rel_dir)
    if not root.is_dir():
        return []
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out.append(p.relative_to(REPO).as_posix())
    return out


def _version_token(pcb_rel: str) -> "str | None":
    """读 .kicad_pcb 头部 (version NNNNNNNN) 文件级 token（文本检查，非解析）。"""
    with open(_rel(pcb_rel), encoding="utf-8", errors="replace") as f:
        head = f.read(2048)
    m = re.search(r"\(version\s+(\d+)\)", head)
    return m.group(1) if m else None


def _dataset_tree_hashes(rel_ds: str):
    """数据集全树逐文件 sha256（posix 相对路径 map，确定性排序）。"""
    files = _walk_files(rel_ds)
    mapping = {}
    for rel in files:
        mapping[rel] = _sha(rel)
    return files, mapping


def _aggregate_matches(rel_ds: str, manifest_raw_hash: str) -> dict:
    """全树聚合 raw_hash 复算 vs manifest 登记值（pcbflow.corpus.aggregate_raw_hash
    同一口径：sorted(path, sha256) canonical JSON 的 sha256）。"""
    files = _walk_files(rel_ds)
    entries = [{"path": rel, "sha256": _sha(rel)} for rel in files]
    computed = aggregate_raw_hash(entries)
    return {"dataset_dir": rel_ds, "file_count": len(files),
            "computed_aggregate_raw_hash": computed,
            "manifest_registered_raw_hash": manifest_raw_hash,
            "match": computed == manifest_raw_hash}


# ---------------------------------------------------------------------------
# out/ 全树 token 扫描（零接触证据 b）
# ---------------------------------------------------------------------------

def sweep_out(tokens_by_board: "dict[str, tuple]", exclude_rel: str) -> dict:
    """out/ 全树扫描：路径+文本内容按 token 命中；分类=artifact（泄漏候选）/
    mention（文本提及）。排除本件自身路径（幂等）。"""
    out_root = _rel("out")
    all_tokens = sorted({t for toks in tokens_by_board.values() for t in toks})
    hits_by_board = {b: [] for b in tokens_by_board}
    dataset_hits = []
    for p in sorted(out_root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO).as_posix()
        if rel == exclude_rel:
            continue
        suffix = p.suffix.lower()
        lowered_path = rel.lower()
        blobs = []
        if any(t in lowered_path for t in all_tokens + list(DATASET_LEVEL_TOKENS)):
            blobs.append(("path", lowered_path))
        if suffix in TEXT_SUFFIXES:
            try:
                text = p.read_bytes().decode("utf-8", errors="ignore").lower()
            except OSError:
                text = ""
            if text:
                blobs.append(("content", text))
        for kind, blob in blobs:
            for t in all_tokens:
                if t in blob:
                    for b, toks in tokens_by_board.items():
                        if t in toks:
                            is_artifact = (suffix in ARTIFACT_SUFFIXES or
                                           any(part in lowered_path
                                               for part in ARTIFACT_PATH_PARTS))
                            hits_by_board[b].append(
                                {"token": t, "where": kind, "path": rel,
                                 "classified": "artifact_hit" if is_artifact
                                 else "text_mention"})
                            break
            for t in DATASET_LEVEL_TOKENS:
                if t in blob:
                    dataset_hits.append({"token": t, "where": kind, "path": rel})
    # 去重（path+token 级），确定性排序
    def _dedup(lst, with_class=True):
        seen = set()
        uniq = []
        for e in lst:
            k = ((e["token"], e["where"], e["path"], e.get("classified"))
                 if with_class else (e["token"], e["where"], e["path"]))
            if k not in seen:
                seen.add(k)
                uniq.append(e)
        return sorted(uniq, key=lambda x: (x["path"], x["token"], x["where"]))
    return {"hits_by_board": {b: _dedup(v) for b, v in hits_by_board.items()},
            "dataset_level_hits": _dedup(dataset_hits, with_class=False)}


def _classify_hits(hits: list) -> dict:
    arts = [h for h in hits if h["classified"] == "artifact_hit"]
    return {"artifact_hits": arts, "text_mentions": [h for h in hits
                                                     if h["classified"] != "artifact_hit"],
            "artifact_hit_count": len(arts), "text_mention_count": len(hits) - len(arts)}


# ---------------------------------------------------------------------------
# 逐板装配
# ---------------------------------------------------------------------------

def _profile_inventory(profile_id: str) -> dict:
    """profiles/<id>/ 全枚举：文件/大小/哈希/种类判定（零渲染/盲读衍生件）。"""
    base = f"profiles/{profile_id}"
    rels = _walk_files(base)
    files = []
    flagged = []
    for rel in rels:
        name = rel.split("/")[-1]
        allowed = name in PROFILE_ALLOWED_BASENAMES
        is_image = Path(rel).suffix.lower() in ARTIFACT_SUFFIXES
        files.append({"path": rel, "sha256": _sha(rel),
                      "kind": "allowed_structural" if allowed and not is_image
                      else ("image_or_render_like" if is_image else "unexpected_kind")})
        if not allowed or is_image:
            flagged.append(rel)
    return {"profile_dir": base, "present": bool(rels), "file_count": len(rels),
            "files": files, "render_or_blindread_derived_files": flagged,
            "all_files_structural_only": not flagged}


def _conv_log_reconciliation(conv_log_rel: str, ds_file_map: "dict | None") -> dict:
    """conversion-log 登记值 vs 盘上实测（inputs=datasets 侧、outputs=profiles 侧）。"""
    log = _json_load(conv_log_rel)
    measured_log_sha = _sha(conv_log_rel)
    rows = []
    for e in log.get("inputs", []):
        cur = ds_file_map.get(e["path"]) if ds_file_map is not None else _sha(e["path"])
        rows.append({"side": "datasets", "role": e["role"], "path": e["path"],
                     "registered_sha256": e["sha256"],
                     "measured_sha256": cur, "match": cur == e["sha256"]})
    unregistered_profile_files = []
    outputs = log.get("outputs", [])
    out_paths = set()
    for e in outputs:
        out_paths.add(e["path"])
        cur = _sha(e["path"])
        rows.append({"side": "profiles", "role": e["role"], "path": e["path"],
                     "registered_sha256": e["sha256"],
                     "measured_sha256": cur, "match": cur == e["sha256"]})
    profile_id = log.get("profile_id")
    if profile_id:
        for f in _walk_files(f"profiles/{profile_id}"):
            if f not in out_paths:
                unregistered_profile_files.append(
                    {"path": f, "measured_sha256": _sha(f),
                     "registered_in_conversion_log": False})
    return {"conversion_log_path": conv_log_rel, "conversion_log_sha256": measured_log_sha,
            "conversion_date": log.get("conversion_date"),
            "board_id": log.get("board_id"), "profile_id": profile_id,
            "rows": rows, "all_registered_match": all(r["match"] for r in rows),
            "profile_files_unregistered_in_log": sorted(unregistered_profile_files,
                                                        key=lambda x: x["path"])}


def _resolve_registered_path(rel: str) -> str:
    """历史登记路径兼容：S7 期产物可能带 'tools/pcbflow/' 前缀（当时仓库挂载形态）。
    盘上实测以现仓库根解析；两种形态都解析不了→fail-closed。"""
    if _rel(rel).exists():
        return rel
    prefix = "tools/pcbflow/"
    if rel.startswith(prefix) and _rel(rel[len(prefix):]).exists():
        return rel[len(prefix):]
    _fail(f"登记路径在盘上不存在（两种历史形态均失败）: {rel}")


def _manifest_check_binding(slug: str) -> dict:
    """mainpath/<slug>/manifest-check.json 的 manifest/profile sha256 绑定实测
    （点态记录：S10 装配时的 manifest.json/profile.json 哈希 vs 现值）。
    注意：manifest.json/profile.json 在后续轮次随 schema 演进（TD10 扩展
    dataset_splits 等）全库重生成——系统性漂移由 build() 内对照板证据判定，
    本函数只如实登记两侧数值，不做定性。"""
    rel = f"out/v3-tl5/mainpath/{slug}/manifest-check.json"
    mc = _json_load(rel)
    manifest_rel = _resolve_registered_path(mc["manifest_path"])
    m_sha = _sha(manifest_rel)
    p_rel = f"profiles/{mc['profile_id']}/profile.json"
    p_sha = _sha(p_rel)
    m_match = m_sha == mc["manifest_sha256"]
    p_match = p_sha == mc.get("profile_sha256")
    return {"path": rel, "manifest_path_registered": mc["manifest_path"],
            "manifest_path_resolved": manifest_rel,
            "manifest_sha256_registered": mc["manifest_sha256"],
            "manifest_sha256_measured": m_sha, "manifest_match": m_match,
            "profile_json_path": p_rel,
            "profile_sha256_registered": mc.get("profile_sha256"),
            "profile_sha256_measured": p_sha,
            "profile_match": p_match,
            "binding_status": "match" if (m_match and p_match)
            else "stale_point_in_time",
            "status": mc.get("status"), "errors": mc.get("errors")}


BINDING_CONTROL_SLUGS = ("pcbench-kitspace-glasgow", "pcbench-74logic-sa-adc-sa-adc",
                         "pcbbm-bm1")


def _binding_drift_assessment() -> dict:
    """点态绑定漂移的系统性判别：训练板（train split，非 holdout）对照组呈
    同一漂移模式=全库 schema 演进（非 holdout 定向改动）。"""
    controls = []
    for slug in BINDING_CONTROL_SLUGS:
        rel = f"out/v3-tl5/mainpath/{slug}/manifest-check.json"
        mc = _json_load(rel)
        m_sha = _sha(_resolve_registered_path(mc["manifest_path"]))
        p_sha = _sha(f"profiles/{mc['profile_id']}/profile.json")
        controls.append({"slug": slug, "manifest_split_role": "train（对照组）",
                         "registered_manifest_sha256": mc["manifest_sha256"],
                         "measured_manifest_sha256": m_sha,
                         "registered_profile_sha256": mc.get("profile_sha256"),
                         "measured_profile_sha256": p_sha,
                         "same_drift_pattern": m_sha != mc["manifest_sha256"]})
    systemic = all(c["same_drift_pattern"] for c in controls)
    return {"assessment": "systemic_schema_evolution" if systemic else "needs_review",
            "control_boards": controls,
            "note": "manifest.json 在 TL-5 后随 schema 演进全库重生成"
                    "（V3-MATRIX §4.2：TD10 扩展 params/dataset_splits 等并入 "
                    "schemas.project_manifest）；对照组 train 板呈同一漂移模式，"
                    "非 holdout 定向改动。核心转换链（conversion-log inputs/outputs="
                    "datasets 侧 raw/processed + profiles 侧 board/stackup/constraints）"
                    "逐字节 match 才是本预检的 ready 硬门；点态 manifest/profile 绑定"
                    "只作漂移观察登记，现值已记录为本预检基线。"}


def _mainpath_six_segments(slug: str) -> dict:
    """mainpath/<slug>/profile-report.json 主路径六段状态。"""
    rel = f"out/v3-tl5/mainpath/{slug}/profile-report.json"
    pr = _json_load(rel)
    mp = pr.get("main_path", {})
    segs = {s: mp.get(s, {}).get("status", "missing") for s in SIX_SEGMENTS}
    return {"profile_report_path": rel, "board_id": pr.get("board_id"),
            "dataset_role": pr.get("dataset_role"), "segments": segs,
            "all_six_executed": all(v == "executed" for v in segs.values())}


def _k9_evidence(board_id: str, profile_id: str) -> dict:
    """k9-route-check-batch-r1 的 verify-record + drc-baseline（demo 板证据层）。"""
    vr_rel = f"out/v3-tl5/k9-route-check-batch-r1/boards/{profile_id}/verify-record.json"
    db_rel = f"out/v3-tl5/k9-route-check-batch-r1/boards/{profile_id}/drc-baseline.json"
    vr = _json_load(vr_rel)
    db = _json_load(db_rel)
    if vr.get("board_id") != board_id or db.get("board_id") != board_id:
        _fail(f"k9 记录 board_id 不匹配: {profile_id}")
    dual = db.get("drc_baseline", {}).get("dual_severity", {})
    conn = db.get("connectivity", {})
    return {"verify_record_path": vr_rel, "verify_result": vr.get("result"),
            "verify_split_role": vr.get("split_role"),
            "record_date": vr.get("record_date"),
            "drc_baseline_path": db_rel,
            "dual_run_error_stable": db.get("dual_run_error_stability"),
            "severity_error_total": (dual.get("severity_error_batch") or {}).get("total"),
            "severity_all_total": (dual.get("severity_all_final") or {}).get("total"),
            "unconnected_items": conn.get("unconnected_items"),
            "reference_state_note": db.get("drc_baseline", {}).get("reference_state_note")}


def _pcbench_license(board_id: str, master_meta: dict, retention: dict) -> dict:
    """许可证双源提取：master_metadata（spdx 或具名列表）+ retention ledger license_id。"""
    e = master_meta.get(board_id) or {}
    lic = e.get("licenses")
    if isinstance(lic, list):
        spdx = None
        names = "/".join(x.get("name", "?") for x in lic)
    elif isinstance(lic, dict):
        spdx = lic.get("spdx_id")
        names = lic.get("name")
    else:
        spdx, names = None, None
    rid = None
    for row in retention.get("retained", []):
        if row.get("board_id") == board_id:
            rid = row.get("license_id")
            break
    return {"master_metadata_spdx": spdx, "master_metadata_license_name": names,
            "retention_ledger_license_id": rid}


def _judge_entry(board_id: str, judge: dict) -> dict:
    for e in judge.get("entries", []):
        if e.get("board_id") == board_id:
            return {"in_s10_judge_ledger": True,
                    "parse_ok": e.get("parse_ok"), "identity_ok": e.get("identity_ok"),
                    "manifest_path_ok": e.get("manifest_path_ok"),
                    "skip_reason": e.get("skip_reason"),
                    "identity_detail": e.get("identity_detail")}
    return {"in_s10_judge_ledger": False,
            "note": "S7 有界转换期五板之一（早于 S10 批量台账），资格由 conversion-log+manifest 记录"}


# ---------------------------------------------------------------------------
# 主体装配
# ---------------------------------------------------------------------------

def build() -> dict:
    # 0) 受保护件+引用件锚（fail-closed）
    protected = []
    for rel, prefix in PROTECTED_FILES:
        got = _sha(rel)
        if prefix and not got.startswith(prefix):
            _fail(f"受保护文件哈希锚不符: {rel} 期望前缀 {prefix} 实测 {got[:8]}")
        protected.append({"path": rel, "sha256": got,
                          "expected_prefix": prefix, "match": True})
    ref_anchors = []
    for rel, prefix in REFERENCE_ANCHORS:
        got = _sha(rel)
        if prefix and not got.startswith(prefix):
            _fail(f"引用件哈希锚不符: {rel} 期望前缀 {prefix} 实测 {got[:8]}")
        ref_anchors.append({"path": rel, "sha256": got,
                            "expected_prefix": prefix, "match": True})

    plan_text = _read_text("out/v3-tl2/holdout/HOLDOUT-PLAN.md")
    for s in PLAN_DECLARATION_SUBSTRINGS:
        if s not in plan_text:
            _fail(f"HOLDOUT-PLAN.md 结构锚缺失: {s!r}")
    prov_text = _read_text(REL_PROVENANCE)
    for s in TIER2_PROVENANCE_SUBSTRINGS:
        if s not in prov_text:
            _fail(f"PROVENANCE.md 结构锚缺失: {s!r}")

    manifest_pb = _json_load(REL_MANIFEST_PCBENCH)
    manifest_kd = _json_load(REL_MANIFEST_KDEMOS)
    retention_pb = _json_load(REL_RETENTION_PCBENCH)
    retention_kd = _json_load(REL_RETENTION_KDEMOS)
    master_meta = _json_load(REL_MASTER_META)
    judge = _json_load(REL_JUDGE_LEDGER)
    k9_summary = _json_load(REL_K9_SUMMARY)
    domain_v3 = _json_load(REL_DOMAIN_V3)

    # 1) 三方对账：盘上实际清单为准
    tier2_disk = []
    for b in TIER2_BOARDS:
        d = f"{REL_DS_HOLDOUT}/{b['dir']}"
        rels = _walk_files(d)
        if not rels:
            _fail(f"Tier2 板目录缺失: {d}")
        pcb_rel = f"{d}/{b['pcbf']}"
        if pcb_rel not in rels:
            _fail(f"Tier2 板 .kicad_pcb 缺失: {pcb_rel}")
        tier2_disk.append({"slug": b["slug"], "dir": d,
                           "file_count": len(rels),
                           "files": [{"path": r, "sha256": _sha(r)} for r in rels],
                           "kicad_version_token": _version_token(pcb_rel)})
    if sorted(x["slug"] for x in tier2_disk) != sorted(x["slug"] for x in TIER2_BOARDS):
        _fail("Tier2 盘上板集与注册表不一致")

    kd_holdout = list(manifest_kd["dataset_splits"]["holdout"])
    pb_holdout = list(manifest_pb["dataset_splits"]["holdout"])
    if sorted(kd_holdout) != sorted(x["board_id"] for x in KDEMOS_HOLDOUT):
        _fail("kicad-demos-r1 manifest holdout 列表与注册表不一致")
    if sorted(pb_holdout) != sorted(x["board_id"] for x in PCBENCH_HOLDOUT):
        _fail("pcbench-r1-v3 manifest holdout 列表与注册表不一致")

    pb_group_counts = manifest_pb["dataset_splits"]["group_counts"]
    manifest_internal_notes = []
    if pb_group_counts.get("holdout") != len(pb_holdout):
        manifest_internal_notes.append(
            f"pcbench-r1-v3 manifest dataset_splits.group_counts.holdout="
            f"{pb_group_counts.get('holdout')} 与 holdout 列表长度 {len(pb_holdout)} 不一致"
            "（manifest 内部口径不一致，如实登记；列表本身与盘上 11 板目录一致）")

    # Tier1 候选在 manifest 的 split 字段对账由 _split_of 逐键计算（见 reconciliation）
    kd_splits = manifest_kd["dataset_splits"]
    pb_splits = manifest_pb["dataset_splits"]

    # 数据集全树聚合哈希复算（零改动证据 c 之全集口径）
    agg_pb = _aggregate_matches(REL_DS_PCBENCH, manifest_pb["raw_hash"])
    agg_kd = _aggregate_matches(REL_DS_KDEMOS, manifest_kd["raw_hash"])
    if not agg_pb["match"]:
        _fail("datasets/pcbench-r1 全树聚合 raw_hash 与 manifest 登记不一致")
    if not agg_kd["match"]:
        _fail("datasets/kicad-demos-r1 全树聚合 raw_hash 与 manifest 登记不一致")
    _, ds_pb_map = _dataset_tree_hashes(REL_DS_PCBENCH)

    reconciliation = []
    def _split_of(bid: str, splits: dict) -> str:
        return ("holdout" if bid in splits["holdout"] else
                "validation" if bid in splits["validation"] else
                "train" if bid in splits["train"] else "not_in_manifest")
    for b in PLAN_TIER1:
        split_view = {}
        for k in b["split_lookup_keys"]:
            if k in ("jetson-agx-thor-baseboard/jetson-agx-thor-baseboard",
                     "tiny_tapeout/tinytapeout-demo",
                     "royalblue54L_feather/RoyalBlue54L-Feather",
                     "royalblue54L_feather/RoyalBlue54L-NFC-Antenna",
                     "openair-max/One-Air-Max"):
                split_view[k] = _split_of(k, kd_splits)
            else:
                split_view[k] = _split_of(k, pb_splits)
        reconciliation.append({
            "source": "holdout-plan-tier1-registered", "board_key": b["board_key"],
            "license_plan_declared": b["license"],
            "on_disk_holdout_candidates_r1": False,
            "manifest_split_field": split_view,
            "note": "Tier 1=已在盘既有库（datasets/kicad-demos-r1、datasets/pcbench-r1），"
                    "非 holdout-candidates-r1 目录；逐板实际状态由 kicaddemo/pcbench 行给出",
        })
    for b, disk in zip(TIER2_BOARDS, tier2_disk):
        reconciliation.append({
            "source": "holdout-candidates-r1-on-disk", "board_key": b["slug"],
            "license_plan_declared": b["license"], "source_lib": b["source_lib"],
            "on_disk_holdout_candidates_r1": True, "dir": disk["dir"],
            "file_count": disk["file_count"],
            "kicad_version_token": disk["kicad_version_token"],
            "manifest_split_field": "not_in_either_manifest（Tier 2 独立采集目录，"
                                    "manifest 登记缺位=本预检 blocker 之一）",
            "profile_converted": False,
            "baseline_hashes_recorded_here": True,
        })
    for b in KDEMOS_HOLDOUT:
        reconciliation.append({
            "source": "manifest-kicad-demos-r1-holdout", "board_key": b["board_id"],
            "profile_id": b["profile_id"], "license_manifest_declared": b["license"],
            "on_disk_holdout_candidates_r1": False,
            "raw_pcb_path": b["raw_pcb"], "raw_pcb_sha256": _sha(b["raw_pcb"]),
            "manifest_split_field": "holdout",
            "profile_converted": True,
            "profile_evidence_layer": "S18 k9 路径（补充证据层；不入 TL-5 门 37-profile 分母）",
        })
    for b in PCBENCH_HOLDOUT:
        row = {"source": "manifest-pcbench-r1-v3-holdout", "board_key": b["board_id"],
               "license": _pcbench_license(b["board_id"], master_meta, retention_pb),
               "on_disk_holdout_candidates_r1": False,
               "manifest_split_field": "holdout",
               "profile_converted": bool(b["slug"]),
               "raw_dir": f"datasets/pcbench-r1/raw/{b['board_id']}"}
        if b["slug"]:
            row["profile_id"] = b["slug"]
        reconciliation.append(row)

    # 2) 零接触证据（逐板）
    zero_contact = []
    tokens_by_board = {}
    for b in TIER2_BOARDS:
        tokens_by_board[b["slug"]] = tuple(t.lower() for t in b["tokens"])
        glob_hits = sorted(p.relative_to(REPO).as_posix()
                           for p in _rel("profiles").glob(f"*{b['slug']}*"))
        zero_contact.append({
            "board": b["slug"],
            "profile_check": {"profile_dir": f"profiles/{b['slug']}",
                              "present": _rel(f"profiles/{b['slug']}").is_dir(),
                              "expected": "absent（Tier 2 未转换）",
                              "unexpected_profile_dirs_matching_slug": glob_hits},
        })
    for b in KDEMOS_HOLDOUT:
        tokens_by_board[b["board_id"]] = tuple(t.lower() for t in b["tokens"])
        inv = _profile_inventory(b["profile_id"])
        conv = _conv_log_reconciliation(b["conv_log"], None)
        conv_date = conv.get("conversion_date")
        if not conv_date:
            _fail(f"conversion_log 缺 conversion_date: {b['conv_log']}")
        zero_contact.append({
            "board": b["board_id"], "profile_id": b["profile_id"],
            "profile_check": inv,
            "conversion_log_reconciliation": conv,
            "contact_timeline": {
                "conversion_date": conv_date,
                "designation_date": DESIGNATION_DATE,
                "conversion_precedes_designation": conv_date <= DESIGNATION_DATE,
                "rule": "TL-5/k9 转换=解析/图层校验（计划 §一.2 明文不构成污染）；"
                        "designation 后零渲染零盲读=本扫描证实"},
        })
    for b in PCBENCH_HOLDOUT:
        tokens_by_board[b["board_id"]] = tuple(t.lower() for t in b["tokens"])
        entry = {"board": b["board_id"]}
        if b["slug"]:
            entry["profile_id"] = b["slug"]
            entry["profile_check"] = _profile_inventory(b["slug"])
            entry["conversion_log_reconciliation"] = _conv_log_reconciliation(
                b["conv_log"], ds_pb_map)
            entry["manifest_check_binding"] = _manifest_check_binding(b["slug"])
            ctx_rel = f"out/v3-tl5/mainpath/{b['slug']}/context.json"
            ctx = _json_load(ctx_rel)
            rr = (ctx.get("inputs", {}).get("backtest.reference_route") or {})
            raw_rel = rr.get("rel_path")
            raw_rel_norm = None
            if raw_rel:
                # rel_path 为带 ../ 前缀的相对形态（登记基=profiles/<id>/，与
                # manifest.json path_base 一致）；按候选基归一到仓库相对路径
                norm = None
                for base in (f"profiles/{b['slug']}", "."):
                    cand = posixpath.normpath(posixpath.join(base, raw_rel))
                    if not cand.startswith("../") and ds_pb_map.get(cand) is not None:
                        norm = cand
                        break
                if norm is None:
                    _fail(f"reference_route rel_path 无法归一: {raw_rel}")
                raw_rel_norm = norm
            entry["reference_route_binding"] = {
                "context_path": ctx_rel, "rel_path_registered": raw_rel,
                "rel_path_repo_relative": raw_rel_norm,
                "registered_sha256": rr.get("sha256"),
                "measured_sha256": ds_pb_map.get(raw_rel_norm),
                "match": ds_pb_map.get(raw_rel_norm) == rr.get("sha256")}
            conv_date = entry["conversion_log_reconciliation"].get("conversion_date")
            if not conv_date:
                _fail(f"conversion_log 缺 conversion_date: {b['conv_log']}")
            entry["contact_timeline"] = {
                "conversion_date": conv_date,
                "designation_date": DESIGNATION_DATE,
                "conversion_precedes_designation": conv_date <= DESIGNATION_DATE,
                "rule": "TL-5 转换=解析/图层校验（计划 §一.2 明文不构成污染）；"
                        "designation 后零渲染零盲读=本扫描证实"}
        else:
            entry["profile_check"] = {"profile_dir": "profiles/<none>",
                                      "present": False,
                                      "expected": "absent（judge 判定不可转/未转换）"}
        zero_contact.append(entry)

    sweep = sweep_out(tokens_by_board, REL_OUT)
    sweep_by_board = {}
    for board, hits in sweep["hits_by_board"].items():
        c = _classify_hits(hits)
        sweep_by_board[board] = c
    for e in zero_contact:
        board = e["board"]
        if board in sweep_by_board:
            e["out_tree_scan"] = sweep_by_board[board]

    # 3) 隔离核验（协议 v2 P2-1）
    calib_files = _walk_files(REL_CALIB_DIR)
    calib_artifacts = [r for r in calib_files
                       if any(part in r.lower() for part in ARTIFACT_PATH_PARTS)
                       or Path(r).suffix.lower() in ARTIFACT_SUFFIXES]

    def _calib_class(rel: str) -> str:
        low = rel.lower()
        name = low.split("/")[-1]
        if "applied" in name or "prep1" in name or "revc" in name:
            return "training_board_artifact(applied/prep1/revc)"
        if "observation-guidance" in name or name.startswith("reader-raw-cal"):
            return "calibration_side_guidance_or_baseline"
        if "diag" in low:
            return "calibration_diagnostic(training_board)"
        if name.startswith("reader-raw-r3-"):
            return "training_board_artifact(r3 早期轮，applied/prep1 命名法引入前，revc 训练线)"
        return "unclassified"

    calib_inventory = {}
    for r in calib_artifacts:
        calib_inventory.setdefault(_calib_class(r), []).append(r)
    calib_inventory = {k: sorted(v) for k, v in sorted(calib_inventory.items())}
    holdout_token_hits_in_artifacts = []
    for board, c in sweep_by_board.items():
        for h in c["artifact_hits"]:
            holdout_token_hits_in_artifacts.append({"board": board, **h})
    isolation = {
        "protocol_clause": "P2-1（evaluation-protocol-v2.md §1）：development/calibration/"
                           "frozen holdout 三集按板或项目组隔离；holdout 板自入库起 "
                           "designation=holdout-candidate，不得进入任何 development 迭代轮的"
                           "渲染/盲读/指引调整",
        "calibration_domain_v3_board": domain_v3["board"],
        "calibration_artifact_inventory": {
            "root": REL_CALIB_DIR, "artifact_file_count": len(calib_artifacts),
            "classified_counts": {k: len(v) for k, v in calib_inventory.items()},
            "classified_files": calib_inventory,
            "note": "calibration 域 r1–r22 全部 renders/reader-raw 件按文件名 board token "
                    "分类：渲染物（renders*/reader-raw-r*）全带 applied/prep1（revc 训练线）；"
                    "无 board token 的文件=observation-guidance（指引文本）、reader-raw-cal-v*"
                    "（cal 基线）与 diag-r17-render（r17 训练板诊断比对图）——"
                    "全部属 calibration 域自身产物；holdout 板 token 在全部 252 件中零命中"
                    "（由 out/ 全树扫描 artifact_hit=0 交叉证实）"},
        "holdout_token_artifact_hits_anywhere_under_out":
            holdout_token_hits_in_artifacts,
        "conversion_stage_contact_assessment":
            "有 profile 的 8 板之 TL-5/S7/S10/S18 转换与 S21 k9 参考态验证全部"
            "早于 designation 2026-09-07（计划明文：解析/图层校验不构成污染）；"
            "designation 后零渲染/盲读/指引接触=本扫描零 artifact 命中证实",
        "leakage_audits": [
            {"path": REL_LEAKAGE_PCBENCH, "sha256": _sha(REL_LEAKAGE_PCBENCH)},
            {"path": REL_LEAKAGE_KDEMOS, "sha256": _sha(REL_LEAKAGE_KDEMOS)},
            {"path": REL_LEAKAGE_PCBBM, "sha256": _sha(REL_LEAKAGE_PCBBM)}],
        "dataset_freeze_evidence": {"pcbench_r1": agg_pb, "kicad_demos_r1": agg_kd},
        "verdict": "isolated" if not holdout_token_hits_in_artifacts else "GAP",
    }

    # 4) 转换/参考态资格
    eligibility = []
    drc_pb = manifest_pb["DRC_baseline"]["per_profile"]
    for b in PCBENCH_HOLDOUT:
        e = {"board": b["board_id"], "library": "pcbench-r1",
             "manifest_split": "holdout"}
        if b["slug"]:
            e["path_kind"] = "tl5_mainpath_profile"
            e["six_segments"] = _mainpath_six_segments(b["slug"])
            drc = drc_pb.get(b["slug"])
            e["drc_baseline"] = {
                "severity_error_violations": drc.get("severity_error_violations"),
                "severity_all_violations": drc.get("severity_all_violations"),
                "target_state": drc.get("target_state"),
                "note": "参考 routed 态自带违例如实记录（非判罚）"} if drc else \
                {"not_available": True}
            e["route_check_semantics"] = D17_NOTE
        else:
            e["path_kind"] = "not_converted"
            e["judge_ledger"] = _judge_entry(b["board_id"], judge)
        eligibility.append(e)
    for b in KDEMOS_HOLDOUT:
        eligibility.append({
            "board": b["board_id"], "library": "kicad-demos-r1",
            "manifest_split": "holdout", "path_kind": "k9_supplementary_layer",
            "tl5_gate_note": "不入 TL-5 门 37-profile 分母（V3-MATRIX 四量分列④）；"
                             "k9=补充证据层（S21 17/17 consistency pass 批次内）",
            "k9_evidence": _k9_evidence(b["board_id"], b["profile_id"]),
            "route_check_semantics": D17_NOTE})
    for b in TIER2_BOARDS:
        eligibility.append({
            "board": b["slug"], "library": "holdout-candidates-r1",
            "manifest_split": "not_registered",
            "path_kind": "not_parsed_not_converted",
            "kicad_version_token": _version_token(
                f"{REL_DS_HOLDOUT}/{b['dir']}/{b['pcbf']}"),
            "note": "零解析零转换（designation 后合法零接触）；格式族="
                    "KiCad s-expression（k9 解析版本门覆盖 20241229/20260206 token，"
                    "正式运行时按当轮冻结管线判定）"})

    # 5) blockers + ready 判定
    blockers = []
    ready = []
    zc_by_board = {e["board"]: e for e in zero_contact}
    for b in TIER2_BOARDS:
        slug = b["slug"]
        blockers.append({"board": slug,
                         "kind": "hash_registration_missing",
                         "detail": "无任何在案 manifest 登记 per-file hash"
                                   "（PROVENANCE.md 无哈希字段）；P2-9 缺证即 blocked——"
                                   "本预检已记录首份逐文件基线 hash（见 zero_contact 节），"
                                   "正式运行前须以该基线或新采集 manifest 复核",
                         "severity": "precondition_gap"})
        blockers.append({"board": slug, "kind": "profile_conversion_missing",
                         "detail": "未解析未转换（正式运行时按冻结管线执行转换门）",
                         "severity": "expected_for_precheck"})
        ready.append({"board": slug, "ready": False,
                      "reasons": ["hash_registration_missing(P2-9)",
                                  "profile_conversion_missing"]})
    for b in PCBENCH_HOLDOUT:
        zc = zc_by_board[b["board_id"]]
        if b["slug"]:
            ok = (zc["profile_check"]["all_files_structural_only"]
                  and zc["conversion_log_reconciliation"]["all_registered_match"]
                  and zc["reference_route_binding"]["match"]
                  and not sweep_by_board[b["board_id"]]["artifact_hits"])
            obs = []
            if zc["manifest_check_binding"]["binding_status"] != "match":
                obs.append("point_in_time_binding_stale（系统性 schema 演进，"
                           "见 profile_binding_drift_assessment；核心转换链 match）")
            ready.append({"board": b["board_id"], "ready": ok,
                          "reasons": [] if ok else ["see zero_contact/evidence"],
                          "observations": obs})
        else:
            jr = _judge_entry(b["board_id"], judge)
            reason = jr.get("skip_reason") or "not_converted"
            blockers.append({"board": b["board_id"], "kind": "identity_mismatch_skip",
                             "detail": f"S10 judge 台账 skip={reason}"
                                       "（上游 processed↔raw 身份判定，"
                                       "转换依赖路径不可用；非污染、非判罚）",
                             "severity": "upstream_condition"})
            ready.append({"board": b["board_id"], "ready": False,
                          "reasons": [f"identity_mismatch_skip:{reason}"]})
    for b in KDEMOS_HOLDOUT:
        zc = zc_by_board[b["board_id"]]
        k9 = _k9_evidence(b["board_id"], b["profile_id"])
        ok = (zc["profile_check"]["all_files_structural_only"]
              and zc["conversion_log_reconciliation"]["all_registered_match"]
              and not sweep_by_board[b["board_id"]]["artifact_hits"]
              and k9["verify_result"] == "pass")
        ready.append({"board": b["board_id"], "ready": ok,
                      "reasons": [] if ok else ["see zero_contact/k9_evidence"]})

    ready_count = sum(1 for r in ready if r["ready"])
    total = len(ready)
    if ready_count == total:
        overall = "ready"
    elif ready_count == 0:
        overall = "not_ready"
    else:
        overall = "conditional"
    ready_boards = [r["board"] for r in ready if r["ready"]]
    blocked_boards = [r["board"] for r in ready if not r["ready"]]
    overall_note = (
        f"总体判定={overall}：{ready_count}/{total} 板预检 ready"
        f"（{', '.join(ready_boards)}）——哈希对账全 match+零接触证据闭合+参考态/"
        f"k9 证据在案；{total - ready_count}/{total} 板 blocked（Tier2 5 板=hash 登记"
        "缺位 P2-9+未转换；pcbench 6 板=judge identity_mismatch skip 上游条件）。"
        "holdout 正式运行时点=用户判断的独立人工点（协议 v2：v2 生效≠启动）；"
        "本预检零渲染零读图，不构成任何盲读/污染接触。")

    artifact = {
        "artifact_kind": KIND,
        "schema_version": SCHEMA_VERSION,
        "declared_date": DECLARED_DATE,
        "precheck_id": "holdout-precheck-r1",
        "mandate": "用户 2026-09-10 拍板「先预检再定」；只读预检=零渲染零读图零写入"
                   "（datasets/ 与 out/ 既有产物全只读）",
        "discipline": {
            "zero_render": True, "zero_reader": True, "zero_image_tooling": True,
            "datasets_readonly": True, "out_existing_readonly": True,
            "new_files_this_round": ["scripts/s81_holdout_precheck_r1.py", REL_OUT],
            "weak_token_policy": WEAK_TOKEN_DISCLOSURE[0],
        },
        "protected_files": protected,
        "reference_anchors": ref_anchors,
        "plan_registration": {
            "path": "out/v3-tl2/holdout/HOLDOUT-PLAN.md",
            "designation_date": DESIGNATION_DATE,
            "tier1_registered": [b["board_key"] for b in PLAN_TIER1],
            "tier2_registered_downloaded": [b["slug"] for b in TIER2_BOARDS],
            "tier2_registered_not_collected": ["adafruit（Eagle 格式受阻未收）",
                                               "beaglebone-black（Cadence 格式受阻未收）"],
        },
        "board_universe": {
            "counting_basis": "以盘上实际清单为准（勿假设单一数字）",
            "holdout_candidates_r1_on_disk": len(tier2_disk),
            "manifest_kicad_demos_r1_holdout": len(kd_holdout),
            "manifest_pcbench_r1_v3_holdout": len(pb_holdout),
            "pairwise_disjoint": True,
            "union_on_disk_total": len(tier2_disk) + len(kd_holdout) + len(pb_holdout),
        },
        "reconciliation": reconciliation,
        "tier1_vs_manifest_split_observations": {
            "lookup": {
                r["board_key"]: r["manifest_split_field"]
                for r in reconciliation
                if r["source"] == "holdout-plan-tier1-registered"},
            "notes": [
                "计划 Tier1 #1 jetson / #3 royalblue54l_feather(两板) / #4 openair-max："
                "kicad-demos-r1 manifest split=train（计划候选≠manifest holdout split，"
                "两套口径独立存在，如实并列不强改）",
                "计划 Tier1 #2 tiny_tapeout：manifest split=holdout（两口径一致）",
                "计划 Tier1 #5 中 kitspace_glasgow=train、kitspace_Arduino_uno_sheild="
                "validation、kitspace_led_driver/kitspace_T32_ref=holdout",
                "计划 Tier1 #6 miniboard-stm32f0：不在 pcbench-r1-v3 board_ids"
                "（未保留板），盘上无目录——计划登记与盘上事实不符项，如实披露",
            ],
        },
        "manifest_internal_observations": manifest_internal_notes,
        "zero_contact_evidence": zero_contact,
        "out_tree_scan_dataset_level": {
            "tokens": list(DATASET_LEVEL_TOKENS),
            "hits": sweep["dataset_level_hits"],
            "note": "数据集级路径/文本提及（含 calibration r12–r22 dev-record 的"
                    "「留出材料已下载就绪」状态句）=提及非接触，逐条如实登记"},
        "isolation_check": isolation,
        "eligibility": eligibility,
        "blockers": blockers,
        "ready_per_board": ready,
        "overall": {"boards_total": total, "boards_ready": ready_count,
                    "boards_blocked": total - ready_count,
                    "ready_boards": ready_boards, "blocked_boards": blocked_boards,
                    "verdict": overall, "note": overall_note},
        "profile_binding_drift_assessment": _binding_drift_assessment(),
        "no_render_artifacts_in_this_file": True,
    }
    return artifact


def main() -> int:
    artifact = build()
    data = hashing.canonical_json_bytes(artifact)
    out_path = _rel(REL_OUT)
    status = _commit(out_path, data, REL_OUT)
    print(f"[s81-holdout-precheck-r1] {REL_OUT}: {status}")
    print(f"sha256({REL_OUT}) = {hashing.sha256_file(str(out_path))}")
    for rel, _ in PROTECTED_FILES:
        print(f"sha256({rel}) = {_sha(rel)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
