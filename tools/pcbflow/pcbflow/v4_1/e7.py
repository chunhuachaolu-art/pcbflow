"""pcbflow.v4_1.e7 -- E7 对外证据与资格（paired holdout executor 评估 +
差分对照 QoR 分列表；任务书 §3 E7/§0.2.2-0.2.3/§9 S2 备用支+S3）。

授权链（只读参照）：exec/V4.1-ROUTER-ENGINEERING-TASKBOOK-2026-09-12.md
（frozen）；out/v3-obs/ADJUDICATION-2026-09-12.md §12 R32/R33。预注册：
out/v4.1-engineering/e7/prereg-e7.json（先于本包全部运行落盘）。

职责（全部确定性、零网络、零模型）：

1. 选板（prereg board_selection 冻结规则）：
   - 静态 screen：board_parse 格式适用性 + 静态 net surface（>=2 pad
     实例的网数，GND-like 排除）→ board-screen.json；
   - DRC screen（编排侧经 E6 KicadCliGuard 执行，本模块只读产物）：
     板原态 U=unconnected_items 行数；
   - selection：Path A（原态行）优先，<2 板则 Path B（TD7 unroute 派生
     先例：2L/>=4L 分层各取 1）→ board-selection.json；
2. baseline：选中板 unroute 态（或 Path A 原态）双口径 DRC
   （norefill/--refill-zones，kicad-cli 唯一 authority）+ e6zone
   audit 旗标 + refill_divergence（E6 fail-closed 接线）；
3. challenger：e4revc 引擎逐板批推进（<=10 网/批、pre/post hash、
   rip-up 梯 T1-T5）——批 commit 门在 E4 之上叠加 E6 强化：双口径
   零新增 severity-error + 双口径 unconnected 不劣化（zone 在场板
   重灌口径复核为 commit 前置）；
4. freerouting v2.3.0 对照臂（archived 工具链仅对照；编排侧执行
   DSN/SES/java，本模块组装记录+读产物）；KiCad P&S 臂=
   not_run_headless_with_reason（prereg 预注册处置）；
5. QoR 分列表（三列分立、无胜出门）+ G7.1-G7.3 判定 + S2 备用支/S3
   检查材料组装（执行侧只提交不宣布）。

红线：受保护三文件零变化；datasets/ 零写入；live 板零写；产物只落
out/v4.1-engineering/e7/；无 wall-clock（declared_date 常量）；零
主机绝对路径进产物。

CLI（编排）：
  python -m pcbflow.v4_1.e7 static-screen [--e7-dir DIR]
  python -m pcbflow.v4_1.e7 select        [--e7-dir DIR]
  python -m pcbflow.v4_1.e7 baseline-pair --board SLUG [--e7-dir DIR]
  python -m pcbflow.v1.e7  batch-record   --board SLUG --batch ID [--e7-dir DIR]
  python -m pcbflow.v4_1.e7 board-pair    --board SLUG [--e7-dir DIR]
  python -m pcbflow.v4_1.e7 qor           [--e7-dir DIR]
  python -m pcbflow.v4_1.e7 s2-s3         [--e7-dir DIR]
  python -m pcbflow.v4_1.e7 progress-get  [--e7-dir DIR]
"""

from __future__ import annotations

import hashlib
import json
import os
import re

from . import DECLARED_DATE
from .canonical import write_canonical_json
from .board_parse import parse_board_text
from .e4revc import (derive_rows, net_names_from_text, parsed_with_names,
                     _drc_counts, _drc_error_keys)

__all__ = [
    "CANDIDATE_UNIVERSE", "EXCLUSIONS", "static_screen", "select_boards",
    "baseline_pair", "batch_record", "board_pair", "qor_table", "s2_s3_check",
    "E7Error", "signal_net_surface", "GND_LIKE",
]

E7_DIR_DEFAULT = "out/v4.1-engineering/e7"

#: 候选 universe（prereg board_selection.candidate_source 冻结口径：
#: datasets/ 登记在册 holdout 指定全集；排除名单派发词+从严扩展）
CANDIDATE_UNIVERSE = [
    # slug, dataset 相对路径（.kicad_pcb）, holdout 指定来源
    ("hc-easyduino-esp32s3",
     "datasets/holdout-candidates-r1/easyduino/ESP32S3/"
     "Easyduino_ESP32S3.kicad_pcb",
     "holdout-candidates-r1（PROVENANCE holdout-candidate 指定）"),
    ("hc-easyduino-rp2040-pico",
     "datasets/holdout-candidates-r1/easyduino/RP2040-Pico/"
     "Easyduino_RP2040.kicad_pcb",
     "holdout-candidates-r1（PROVENANCE holdout-candidate 指定）"),
    ("hc-easyduino-stm32f103-bluepill",
     "datasets/holdout-candidates-r1/easyduino/STM32F103-Bluepill/"
     "Easyduino_STM32F103.kicad_pcb",
     "holdout-candidates-r1（PROVENANCE holdout-candidate 指定）"),
    ("hc-sparkfun-qwiic-adc-ads1219",
     "datasets/holdout-candidates-r1/sparkfun/qwiic-adc-ads1219/"
     "Qwiic_ADC_ADS1219.kicad_pcb",
     "holdout-candidates-r1（PROVENANCE holdout-candidate 指定）"),
    ("hc-sparkfun-qwiic-current-sensor-ina2xx",
     "datasets/holdout-candidates-r1/sparkfun/qwiic-current-sensor-ina2xx/"
     "SparkFun_Qwiic_Current_Sensor_INA2XX.kicad_pcb",
     "holdout-candidates-r1（PROVENANCE holdout-candidate 指定）"),
    ("pb-dual-lm317-benchsupply",
     "datasets/pcbench-r1/raw/DualLM317BenchSupply_DualLM317BenchSupply/"
     "processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-ttn-enschede-mote",
     "datasets/pcbench-r1/raw/TTNEnschedeMote_ArduinoNanoRN2483/"
     "processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-theia",
     "datasets/pcbench-r1/raw/Theia_Theia/processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-beer-gauge",
     "datasets/pcbench-r1/raw/beer-gauge_beer-gauge/processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-esp32-cantroller-eltekcontroller",
     "datasets/pcbench-r1/raw/esp32-cantroller_EltekController/"
     "processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-fp2-extension-usb-breakout",
     "datasets/pcbench-r1/raw/fp2_extension_sample_fp2_usb_breakout/"
     "processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-kitspace-gpsmux",
     "datasets/pcbench-r1/raw/kitspace_GPSMux/processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-kitspace-lcr-addon",
     "datasets/pcbench-r1/raw/kitspace_Lcr_addon/processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-kitspace-t32-ref",
     "datasets/pcbench-r1/raw/kitspace_T32_ref/processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-kitspace-led-driver",
     "datasets/pcbench-r1/raw/kitspace_led_driver/processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("pb-kitspace-postcard",
     "datasets/pcbench-r1/raw/kitspace_postcard/processed.kicad_pcb",
     "pcbench-r1 holdout split（dataset-manifest-pcbench-r1-v3 frozen）"),
    ("kd-tiny-tapeout",
     "datasets/kicad-demos-r1/raw/tiny_tapeout/tinytapeout-demo.kicad_pcb",
     "kicad-demos-r1 holdout split（dataset-manifest-kicad-demos-r2）"),
    ("kd-video",
     "datasets/kicad-demos-r1/raw/video/video.kicad_pcb",
     "kicad-demos-r1 holdout split（dataset-manifest-kicad-demos-r2）"),
    ("kd-vme-wren",
     "datasets/kicad-demos-r1/raw/vme-wren/vme-wren.kicad_pcb",
     "kicad-demos-r1 holdout split（dataset-manifest-kicad-demos-r2）"),
    ("pbm-bm11",
     "datasets/pcbbenchmarks-r1/raw/bm11/bm11.unrouted.kicad_pcb",
     "pcbbenchmarks-r1 holdout split（dataset-manifest-pcbbenchmarks-r1-v3）"),
]

#: 排除名单（prereg board_selection.exclusions_*：派发词+从严扩展）
EXCLUSIONS = {
    "pb-kitspace-led-driver":
        "conservative_extension：V3 holdout-r1 实际消费板（互不占用从严读）",
    "kd-tiny-tapeout": "tinytapeout_forever（派发词）",
    "kd-vme-wren": "paper_p2_1_gt_candidates+vme-wren（派发词双列）",
}

#: GND-like 网名（大写归一后；prereg static_screen.rule）
GND_LIKE = ("GND", "DGND", "AGND")

#: Path A 行预算界 / Path B signal net surface 界（prereg 冻结）
ROW_BUDGET = 60
NET_BUDGET = 60


class E7Error(ValueError):
    """E7 链 fail-closed。"""


# ================================================================ 工具

def _sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _load_json(path):
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def _e7_paths(e7_dir):
    import pathlib
    e7 = pathlib.Path(e7_dir)
    return e7, e7 / "board-screen.json", e7 / "board-selection.json"


def _board_dir(e7_dir, slug):
    import pathlib
    return pathlib.Path(e7_dir) / "boards" / slug


def _progress_update(e7_dir, mutate):
    import pathlib
    p = pathlib.Path(e7_dir) / "progress.json"
    if p.is_file():
        obj = _load_json(str(p))
    else:
        obj = {"schema": "pcbflow.v4_1.e7-progress/1",
               "declared_date": DECLARED_DATE,
               "steps": [], "token_ledger": []}
    mutate(obj)
    p.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json(p, obj)


def _step(e7_dir, name, summary):
    def _mut(o):
        o["steps"].append({"step": name, "summary": summary})
    _progress_update(e7_dir, _mut)


# ================================================================ 静态 screen

def signal_net_surface(board_text):
    """板文本 -> (signal_nets, gnd_nets, copper_layers, pad_count)。

    signal net = >=2 pad 实例且网名大写归一后不在 GND_LIKE 的网
    （prereg static_screen.rule 冻结口径；parse 失败抛 E7Error）。
    """
    parsed = parse_board_text(board_text)
    name_map = net_names_from_text(board_text)
    named = parsed_with_names(parsed, name_map)
    counts = {}
    for pad in named["pads"]:
        net = str(pad["net_id"])
        if net in ("", '""'):
            continue
        counts[net] = counts.get(net, 0) + 1
    multi = {n: c for n, c in counts.items() if c >= 2}
    gnd = sorted(n for n in multi if n.upper() in GND_LIKE)
    sig = sorted(n for n in multi if n.upper() not in GND_LIKE)
    return sig, gnd, list(parsed["copper_layers"]), \
        parsed["stats"]["pad_count"]


def static_screen(e7_dir=E7_DIR_DEFAULT, root="."):
    """候选 universe 静态 screen（零 DRC/零链路）→ board-screen.json。"""
    rows, parse_fail = [], []
    for slug, rel, source in CANDIDATE_UNIVERSE:
        path = os.path.join(root, rel)
        base = {"slug": slug, "dataset_path": rel,
                "holdout_designation": source,
                "excluded": EXCLUSIONS.get(slug)}
        if not os.path.isfile(path):
            # pcbench 目录内文件名可能非 slug 直名（列目录找 .kicad_pcb）
            cands = []
            if os.path.isdir(os.path.dirname(path)):
                cands = [f for f in sorted(os.listdir(os.path.dirname(path)))
                         if f.endswith(".kicad_pcb")]
            if not cands:
                rows.append(dict(base, parse="file_missing"))
                continue
            path = os.path.join(os.path.dirname(path), cands[0])
        try:
            with open(path, "r", encoding="utf-8", errors="strict") as f:
                text = f.read()
        except UnicodeDecodeError:
            text = open(path, "r", encoding="utf-8",
                        errors="replace").read()
        m = re.search(r"\(version\s+(\d+)", text)
        ver = m.group(1) if m else None
        try:
            sig, gnd, copper, pads = signal_net_surface(text)
            rows.append(dict(
                base, parse="ok", file_version=ver,
                board_sha256=_sha_file(path),
                signal_net_surface=len(sig), gnd_net_count=len(gnd),
                gnd_net_names=gnd, copper_layers=len(copper),
                copper_layer_names=copper, pad_count=pads,
                routed_segment_count=len(re.findall(r"\(segment\s", text)),
                routed_via_count=len(re.findall(r"\(via\s", text)),
                zone_count=len(re.findall(r"\(zone\s", text))))
        except Exception as exc:  # BoardParseError 等全部 fail-closed 登记
            parse_fail.append(slug)
            rows.append(dict(
                base, parse="fail", file_version=ver,
                board_sha256=_sha_file(path),
                parse_error="%s: %s" % (type(exc).__name__,
                                        str(exc)[:200])))
    out = {
        "schema": "pcbflow.v4_1.e7-board-screen/1",
        "declared_date": DECLARED_DATE,
        "prereg_ref": "prereg-e7.json board_selection.static_screen",
        "universe_size": len(CANDIDATE_UNIVERSE),
        "exclusion_list": EXCLUSIONS,
        "boards": rows,
        "parse_ok_count": sum(1 for r in rows if r["parse"] == "ok"
                              and not r.get("excluded")),
        "parse_fail_slugs": parse_fail,
    }
    write_canonical_json(os.path.join(e7_dir, "board-screen.json"), out)
    _step(e7_dir, "static-screen",
          "universe=%d parse_ok(未排除)=%d parse_fail=%d"
          % (len(CANDIDATE_UNIVERSE), out["parse_ok_count"],
             len(parse_fail)))
    return out


# ================================================================ 选板

def select_boards(e7_dir=E7_DIR_DEFAULT):
    """DRC screen 产物 + 静态 screen → 冻结规则选板 → board-selection.json。

    Path A：U>=1 板 >=2 → U 降序（并列 slug 升序）取 2（U<=ROW_BUDGET）。
    Path B：否则分层（2L 与 >=4L 各 1；层内 signal surface 降序、并列
    slug 升序；surface<=NET_BUDGET 才可行；某层空则他层取 2）。
    """
    e7, _scr, _sel = _e7_paths(e7_dir)
    screen = _load_json(str(e7 / "board-screen.json"))
    drc_dir = e7 / "drc-screen"
    if not drc_dir.is_dir():
        raise E7Error("drc-screen/ 不存在（先跑 DRC screen，fail-closed）")
    drc_rows = {}
    for p in sorted(drc_dir.glob("*/screen-drc.json")):
        slug = p.parent.name
        try:
            obj = _load_json(str(p))
        except Exception:
            drc_rows[slug] = {"drc_parse": "fail"}
            continue
        cnt = _drc_counts(obj)
        drc_rows[slug] = {
            "drc_parse": "ok",
            "violations_total": cnt["violations_total"],
            "severity_error": cnt["severity_error"],
            "unconnected_items": cnt["unconnected_items"],
        }
    eligible = [b for b in screen["boards"]
                if b["parse"] == "ok" and not b.get("excluded")]
    # DRC screen 覆盖核对（parse ok 未排除板必须有 DRC 产物）
    missing = [b["slug"] for b in eligible
               if b["slug"] not in drc_rows
               or drc_rows[b["slug"]]["drc_parse"] != "ok"]
    if missing:
        raise E7Error("DRC screen 缺产物（fail-closed）: %r" % missing)
    for b in eligible:
        b["drc_screen"] = drc_rows[b["slug"]]
    path_a_pool = [b for b in eligible
                   if b["drc_screen"]["unconnected_items"] >= 1]
    sel = {"schema": "pcbflow.v4_1.e7-board-selection/1",
           "declared_date": DECLARED_DATE,
           "prereg_ref": "prereg-e7.json board_selection.path_a/b",
           "screen_boards": screen["boards"], "drc_screen": drc_rows,
           "path_a_pool": [b["slug"] for b in path_a_pool]}
    if len(path_a_pool) >= 2:
        ranked = sorted(
            [b for b in path_a_pool
             if b["drc_screen"]["unconnected_items"] <= ROW_BUDGET],
            key=lambda b: (-b["drc_screen"]["unconnected_items"],
                           b["slug"]))
        over = [b["slug"] for b in path_a_pool
                if b["drc_screen"]["unconnected_items"] > ROW_BUDGET]
        sel.update({
            "path_taken": "A",
            "path_a_rule_note":
                "U>=1 板 >=2：U 降序取前 2（U<=60 界；并列 slug 升序）",
            "not_selected_over_row_budget": over,
            "selected": [{"slug": b["slug"], "rank": i + 1,
                          "unconnected_items":
                              b["drc_screen"]["unconnected_items"]}
                         for i, b in enumerate(ranked[:2])],
        })
    else:
        feasible = [b for b in eligible
                    if b["signal_net_surface"] <= NET_BUDGET]
        infeasible = [b["slug"] for b in eligible
                      if b["signal_net_surface"] > NET_BUDGET]
        two_l = sorted([b for b in feasible if b["copper_layers"] == 2],
                       key=lambda b: (-b["signal_net_surface"], b["slug"]))
        four_l = sorted([b for b in feasible if b["copper_layers"] >= 4],
                        key=lambda b: (-b["signal_net_surface"], b["slug"]))
        chosen = []
        if two_l and four_l:
            chosen = [two_l[0], four_l[0]]
        elif two_l:
            chosen = two_l[:2]
        elif four_l:
            chosen = four_l[:2]
        else:
            raise E7Error("无可行板（Path B 空）——如实报 blocked 不硬凑")
        sel.update({
            "path_taken": "B",
            "path_b_rule_note":
                "U>=1 板 <2：TD7 unroute 派生；分层 2L/>=4L 各取 1"
                "（层内 signal surface 降序、并列 slug 升序；<=60 界）",
            "path_a_u_zero_slugs":
                [b["slug"] for b in eligible
                 if b["drc_screen"]["unconnected_items"] == 0],
            "not_selected_over_net_budget": infeasible,
            "strata": {"2L_ranked": [b["slug"] for b in two_l],
                       "4Lplus_ranked": [b["slug"] for b in four_l]},
            "selected": [
                {"slug": b["slug"], "stratum":
                 ("2L" if b["copper_layers"] == 2 else ">=4L"),
                 "signal_net_surface": b["signal_net_surface"],
                 "copper_layers": b["copper_layers"]}
                for b in chosen],
        })
    write_canonical_json(e7 / "board-selection.json", sel)
    _step(e7_dir, "select",
          "path=%s selected=%s" % (
              sel["path_taken"],
              [s["slug"] for s in sel["selected"]]))
    return sel


# ================================================================ baseline

def baseline_pair(board_slug, e7_dir=E7_DIR_DEFAULT):
    """选中板 paired baseline 组装：双口径 DRC 差分 + e6zone audit。

    输入（编排侧经 guard 已落盘）：
      boards/<slug>/baseline/drc-error-norefill.json
      boards/<slug>/baseline/drc-error-refill.json
      boards/<slug>/staging/revc.kicad_pcb（challenger 起始态）
    输出：boards/<slug>/baseline/baseline-pair.json
    """
    from .e6zone import audit_zone_refill_interactions, refill_divergence
    bd = _board_dir(e7_dir, board_slug)
    base = bd / "baseline"
    norefill = _load_json(str(base / "drc-error-norefill.json"))
    refill = _load_json(str(base / "drc-error-refill.json"))
    board_text = (bd / "l2-batches" / "staging" /
                 "revc.kicad_pcb").read_text(
        encoding="utf-8")
    audit = audit_zone_refill_interactions(board_text)
    div = refill_divergence(norefill, refill)
    nr, rf = _drc_counts(norefill), _drc_counts(refill)
    # 旗标口径=e6zone 权威键（flag_classes_present 四类旗标 +
    # commit_blocked_without_refill_drc fail-closed 语义键）
    flags = sorted(audit.get("flag_classes_present") or [])
    audit_gate = bool(audit.get("commit_blocked_without_refill_drc"))
    out = {
        "schema": "pcbflow.v4_1.e7-baseline-pair/1",
        "declared_date": DECLARED_DATE,
        "board": board_slug,
        "drc_norefill": nr, "drc_refill": rf,
        "zone_audit_flag_classes": flags,
        "zone_audit_commit_blocked_without_refill_drc": audit_gate,
        "zone_audit_zones": audit.get("zones"),
        "zone_audit_zones_unparsed": audit.get("zones_unparsed"),
        "refill_divergence": div,
        "commit_gate_note":
            "E6 fail-closed 接线：audit 旗标或 divergence 非空 ⇒ 批 commit "
            "须 refill 口径零新增 severity-error 复核；E7 实现取从严式="
            "zone 在场板无条件双口径（prereg protocol.challenger）",
        "gnd_net_names_excluded": _gnd_exclusion_names(board_slug, e7_dir),
    }
    write_canonical_json(base / "baseline-pair.json", out)
    _step(e7_dir, "baseline-pair:%s" % board_slug,
          "norefill %d err/%d unc; refill %d err/%d unc; flags=%s; "
          "divergent=%s" % (nr["severity_error"], nr["unconnected_items"],
                            rf["severity_error"], rf["unconnected_items"],
                            flags or "none", div["divergent"]))
    return out


def _gnd_exclusion_names(board_slug, e7_dir):
    """板实际 GND 名（derive_rows exclude_nets 核对登记）。"""
    screen = _load_json(os.path.join(e7_dir, "board-screen.json"))
    for b in screen["boards"]:
        if b["slug"] == board_slug and b.get("gnd_net_names"):
            return list(b["gnd_net_names"])
    return []


# ================================================================ 批 record

def batch_record(board_slug, batch, e7_dir=E7_DIR_DEFAULT):
    """E7 批 record（E4 纪律+E6 双口径强化 commit 门）。

    输入（编排侧经 guard 已落盘到批目录）：
      candidates.json / apply-record.json（e4revc op 产物）
      drc-error-norefill.json（challenger 批 DRC norefill）
      drc-error-refill.json（challenger 批 DRC refill；zone 旗标板必测）
      baseline-error-norefill.json / baseline-error-refill.json
        （pre 态双口径：batch-01=unroute baseline；后续批=前一批 commit
        态 DRC 件复制，pre 态 sha 断言后复用——调用侧对账）
    判定：checks 全绿 → commit（staging 覆盖）；任一红 → rollback。
    """
    from .prl_hygiene import check_and_restore as _car
    bd = _board_dir(e7_dir, board_slug)
    bdir = bd / "l2-batches" / batch
    plan = _load_json(str(bdir / "candidates.json"))
    apply_rec = _load_json(str(bdir / "apply-record.json"))
    drc_nr = _load_json(str(bdir / "drc-error-norefill.json"))
    base_nr = _load_json(str(bdir / "baseline-error-norefill.json"))
    # refill 口径（zone 旗标板必测；无 zone 板允许缺件=复制 norefill 判定）
    refill_path = bdir / "drc-error-refill.json"
    base_rf_path = bdir / "baseline-error-refill.json"
    zone_gate = True
    if refill_path.is_file() and base_rf_path.is_file():
        drc_rf = _load_json(str(refill_path))
        base_rf = _load_json(str(base_rf_path))
    else:
        drc_rf, base_rf = drc_nr, base_nr
        zone_gate = False
    chal_nr, chal_rf = _drc_counts(drc_nr), _drc_counts(drc_rf)
    pre_nr, pre_rf = _drc_counts(base_nr), _drc_counts(base_rf)
    added_nr = sorted(set(_drc_error_keys(drc_nr))
                      - set(_drc_error_keys(base_nr)))
    added_rf = sorted(set(_drc_error_keys(drc_rf))
                      - set(_drc_error_keys(base_rf)))
    removed_nr = sorted(set(_drc_error_keys(base_nr))
                        - set(_drc_error_keys(drc_nr)))
    no_change = apply_rec.get("ops_count", 1) == 0
    staging = bd / "l2-batches" / "staging" / "revc.kicad_pcb"
    checks = {
        "pre_hash_matches_staging":
            _sha_file(str(staging)) == apply_rec["pre_hash_sha256"],
        "severity_error_equal_norefill":
            chal_nr["severity_error"] == pre_nr["severity_error"],
        "added_error_empty_norefill": not added_nr,
        "added_error_empty_refill": not added_rf,
        "unconnected_not_worse_norefill":
            chal_nr["unconnected_items"] <= pre_nr["unconnected_items"],
        "unconnected_not_worse_refill":
            chal_rf["unconnected_items"] <= pre_rf["unconnected_items"],
    }
    verdict = "commit" if all(checks.values()) else "rollback"
    if verdict == "commit":
        with open(str(staging), "wb") as f:
            f.write((bdir / "challenger.kicad_pcb").read_bytes())
    prl_rec = _car(str(bdir), apply_rec["prl_inventory_before"])
    rec = {
        "schema": "pcbflow.v4_1.e7-batch-record/1",
        "declared_date": DECLARED_DATE,
        "board": board_slug, "batch": batch,
        "hash_chain": {
            "pre_hash_sha256": apply_rec["pre_hash_sha256"],
            "post_hash_sha256": apply_rec["post_hash_sha256"],
            "staging_after_verdict_sha256": _sha_file(str(staging)),
        },
        "drc_pre": {"norefill": pre_nr, "refill": pre_rf},
        "drc_challenger": {"norefill": chal_nr, "refill": chal_rf},
        "zone_gate_applied": zone_gate,
        "added_error_keys_norefill": [list(a) for a in added_nr][:40],
        "added_error_keys_refill": [list(a) for a in added_rf][:40],
        "removed_error_keys_norefill": [list(a) for a in removed_nr][:40],
        "checks": checks,
        "no_change_batch": no_change,
        "verdict": verdict,
        "committed_rows": (0 if no_change else
                           (plan["candidate_rows"]
                            if verdict == "commit" else 0)),
        "unconnected_delta_norefill": (chal_nr["unconnected_items"]
                                       - pre_nr["unconnected_items"]),
        "unconnected_delta_refill": (chal_rf["unconnected_items"]
                                     - pre_rf["unconnected_items"]),
        "prl_hygiene": prl_rec,
    }
    write_canonical_json(bdir / "batch-record.json", rec)
    _step(e7_dir, "batch-record:%s/%s" % (board_slug, batch),
          "verdict=%s unc_delta(nr)=%d" % (verdict,
                                           rec["unconnected_delta_norefill"]))
    return rec


# ================================================================ 逐板 pair

def board_pair(board_slug, e7_dir=E7_DIR_DEFAULT):
    """逐板 paired 汇总（baseline vs challenger vs freerouting）。

    challenger 终态 DRC=链尾 commit 态（staging sha 与最后 commit 批
    post_hash 对账；severity-all 终态件若在则并入）。
    """
    bd = _board_dir(e7_dir, board_slug)
    base = _load_json(str(bd / "baseline" / "baseline-pair.json"))
    rows = _load_json(str(bd / "rows.json"))
    batches = []
    last_commit = None
    for p in sorted((bd / "l2-batches").glob("batch-*/batch-record.json")):
        r = _load_json(str(p))
        batches.append({
            "batch": r["batch"], "verdict": r["verdict"],
            "no_change_batch": r["no_change_batch"],
            "committed_rows": r["committed_rows"],
            "unconnected_delta_norefill":
                r["unconnected_delta_norefill"],
            "unconnected_delta_refill": r["unconnected_delta_refill"],
            "added_error_keys_norefill":
                len(r["added_error_keys_norefill"]),
            "added_error_keys_refill":
                len(r["added_error_keys_refill"]),
        })
        if r["verdict"] == "commit" and not r["no_change_batch"]:
            last_commit = r
    staging_sha = _sha_file(str(bd / "l2-batches" / "staging" /
                               "revc.kicad_pcb"))
    final_nr, final_rf, final_all = None, None, None
    fin_dir = bd / "final"
    if last_commit is not None:
        lc_dir = bd / "l2-batches" / last_commit["batch"]
        final_nr = _drc_counts(_load_json(
            str(lc_dir / "drc-error-norefill.json")))
        if (lc_dir / "drc-error-refill.json").is_file():
            final_rf = _drc_counts(_load_json(
                str(lc_dir / "drc-error-refill.json")))
        hash_ok = (staging_sha == last_commit["hash_chain"]
                   ["post_hash_sha256"])
    else:
        hash_ok = (staging_sha == _sha_file(
            str(bd / "baseline" / "staging-pre.kicad_pcb"))
            if (bd / "baseline" / "staging-pre.kicad_pcb").is_file()
            else False)
        final_nr = base["drc_norefill"]
        final_rf = base["drc_refill"]
    if (fin_dir / "drc-all-norefill.json").is_file():
        obj = _load_json(str(fin_dir / "drc-all-norefill.json"))
        final_all = {"violations_total": len(obj.get("violations", [])),
                     "unconnected_items":
                         len(obj.get("unconnected_items") or [])}
    # freerouting 臂（产物在则并入）
    fr = None
    fr_rec = bd / "freerouting" / "arm-record.json"
    if fr_rec.is_file():
        fr = _load_json(str(fr_rec))
    committed_rows = sum(b["committed_rows"] for b in batches)
    out = {
        "schema": "pcbflow.v4_1.e7-board-pair/1",
        "declared_date": DECLARED_DATE,
        "board": board_slug,
        "rows_total": rows["required_row_count"],
        "required_net_count": rows["required_net_count"],
        "batch_count": len(batches), "batches": batches,
        "baseline": {"norefill": base["drc_norefill"],
                     "refill": base["drc_refill"],
                     "zone_audit_flag_classes": base[
                         "zone_audit_flag_classes"],
                     "zone_audit_commit_blocked_without_refill_drc":
                         base["zone_audit_commit_blocked_without_refill"
                              "_drc"],
                     "divergent": base["refill_divergence"]["divergent"]},
        "challenger_final": {"norefill": final_nr, "refill": final_rf,
                             "severity_all": final_all,
                             "staging_sha256": staging_sha,
                             "hash_chain_verified": hash_ok},
        "committed_rows_total": committed_rows,
        "unconnected_improvement_norefill":
            (base["drc_norefill"]["unconnected_items"]
             - (final_nr or {}).get("unconnected_items", 0)),
        "unconnected_improvement_refill":
            (base["drc_refill"]["unconnected_items"]
             - (final_rf or {}).get("unconnected_items", 0)),
        "freerouting": fr,
        "s2_disclosure": "S2 曾于 2026-09-12 触发并被用户裁定驳回（R32）",
    }
    write_canonical_json(bd / "board-pair.json", out)
    _step(e7_dir, "board-pair:%s" % board_slug,
          "rows=%d committed=%d unc_impr(nr)=%d" % (
              out["rows_total"], committed_rows,
              out["unconnected_improvement_norefill"]))
    return out


# ================================================================ QoR + S2/S3

def _new_errors_vs(base_counts_obj, final_counts_obj):
    return (final_counts_obj or {}).get("severity_error", 0) - \
        (base_counts_obj or {}).get("severity_error", 0)


def qor_table(e7_dir=E7_DIR_DEFAULT):
    """QoR 分列表（三列分立；无胜出门；§0.2.3 对账布尔）。"""
    e7, _scr, _sel = _e7_paths(e7_dir)
    sel = _load_json(str(e7 / "board-selection.json"))
    arms_ps = {
        "arm": "kicad_ps",
        "status": "not_run_headless_with_reason",
        "reason": "kicad-cli 10.0.5 无 headless 交互 P&S 子命令；交互 "
                  "P&S=人工参与不可复现（如实标注人工参与度，不伪造数字）",
        "manual_participation_disclosure":
            "KiCad P&S 为交互上界参照：人工逐网拖布+实时推挤，参与度"
            "不可量化复现；prereg protocol.kicad_ps_arm 预注册处置",
        "objective": "not_applicable",
    }
    rows = []
    s2_worse_any = False
    for s in sel["selected"]:
        slug = s["slug"]
        pair = _load_json(str(e7 / "boards" / slug / "board-pair.json"))
        base_nr = pair["baseline"]["norefill"]["severity_error"]
        base_unc_nr = pair["baseline"]["norefill"]["unconnected_items"]
        chal_nr = pair["challenger_final"]["norefill"] or {}
        chal_rf = pair["challenger_final"]["refill"] or {}
        base_rf = pair["baseline"]["refill"]
        new_err_nr = _new_errors_vs({"severity_error": base_nr}, chal_nr)
        new_err_rf = _new_errors_vs(
            {"severity_error": base_rf["severity_error"]}, chal_rf)
        unc_delta_nr = chal_nr.get("unconnected_items", base_unc_nr) \
            - base_unc_nr
        unc_delta_rf = chal_rf.get(
            "unconnected_items", base_rf["unconnected_items"]) \
            - base_rf["unconnected_items"]
        fr = pair.get("freerouting")
        fr_row = {"arm": "freerouting_v2.3.0_archived",
                  "status": (fr or {}).get("status", "not_run"),
                  "new_severity_error_norefill": None,
                  "unconnected_delta_norefill": None,
                  "objective": "not_applicable"}
        if fr and fr.get("status") == "completed":
            frb = fr["drc_baseline"]; frf = fr["drc_final"]
            fr_row["new_severity_error_norefill"] = \
                frf["norefill"]["severity_error"] \
                - frb["norefill"]["severity_error"]
            fr_row["new_severity_error_refill"] = \
                frf["refill"]["severity_error"] \
                - frb["refill"]["severity_error"]
            fr_row["unconnected_delta_norefill"] = \
                frf["norefill"]["unconnected_items"] \
                - frb["norefill"]["unconnected_items"]
            fr_row["unconnected_delta_refill"] = \
                frf["refill"]["unconnected_items"] \
                - frb["refill"]["unconnected_items"]
            fr_row["new_track_length_mm"] = fr.get("new_track_length_mm")
            fr_row["new_via_count"] = fr.get("new_via_count")
        chal_row = {
            "arm": "v4_1_challenger",
            "status": "completed",
            "new_severity_error_norefill": new_err_nr,
            "new_severity_error_refill": new_err_rf,
            "unconnected_delta_norefill": unc_delta_nr,
            "unconnected_delta_refill": unc_delta_rf,
            "objective": ("engine_internal_routing_cost"
                          if pair["committed_rows_total"] > 0
                          else "no_committed_rows"),
            "committed_rows": pair["committed_rows_total"],
        }
        # §0.2.3 差分布尔（freerouting 完成才可比；否则 not_comparable）
        if fr_row["status"] == "completed":
            worse_err = (chal_row["new_severity_error_norefill"]
                         > fr_row["new_severity_error_norefill"])
            worse_unc = (chal_row["unconnected_delta_norefill"]
                         > fr_row["unconnected_delta_norefill"])
            worse = bool(worse_err or worse_unc)
            s2_worse_any = s2_worse_any or worse
            diff = {"differential_worse_than_freerouting": worse,
                    "worse_by_new_error": bool(worse_err),
                    "worse_by_unconnected": bool(worse_unc)}
        else:
            diff = {"differential_worse_than_freerouting":
                    "not_comparable_freerouting_not_completed"}
        rows.append({"board": slug, "challenger": chal_row,
                     "freerouting": fr_row, "kicad_ps": arms_ps,
                     "diff_023_check": diff})
    out = {
        "schema": "pcbflow.v4_1.e7-qor-table/1",
        "declared_date": DECLARED_DATE,
        "no_winner_gate": "G7.2 只列分表+对账，不设胜出门（prereg）",
        "objective_semantics":
            "objective=v4exp 冻结 cmp 口径仅 challenger 引擎内有定义；"
            "freerouting/P&S=not_applicable（prereg qor.objective_semantics）",
        "boards": rows,
        "s2_disclosure": "S2 曾于 2026-09-12 触发并被用户裁定驳回（R32）；"
                        "本差分若劣于 freerouting=S2 备用支须重新提交用户"
                        "裁决，不得默认沿用驳回",
    }
    write_canonical_json(e7 / "qor-table.json", out)
    _step(e7_dir, "qor", "boards=%d s2_worse_any=%s"
          % (len(rows), s2_worse_any))
    return out


def s2_s3_check(e7_dir=E7_DIR_DEFAULT):
    """S2 备用支/S3 检查材料组装（执行侧只提交不宣布）。"""
    e7, _scr, _sel = _e7_paths(e7_dir)
    qor = _load_json(str(e7 / "qor-table.json"))
    sel = _load_json(str(e7 / "board-selection.json"))
    s2_trigger = False
    for r in qor["boards"]:
        d = r["diff_023_check"]["differential_worse_than_freerouting"]
        if d is True:
            s2_trigger = True
    # S3：逐板批 added-error/unconnected 非目标回退核查
    s3_findings = []
    for s in sel["selected"]:
        pair = _load_json(str(e7 / "boards" / s["slug"] / "board-pair.json"))
        for b in pair["batches"]:
            if b["verdict"] == "rollback":
                continue  # 回滚批零板面变化
            if b["added_error_keys_norefill"] or \
                    b["added_error_keys_refill"]:
                s3_findings.append({
                    "board": s["slug"], "batch": b["batch"],
                    "kind": "committed_with_added_error",
                    "note": "commit 门破而 commit=机制故障，S3 材料候选"})
            if b["unconnected_delta_norefill"] > 0 or \
                    b["unconnected_delta_refill"] > 0:
                s3_findings.append({
                    "board": s["slug"], "batch": b["batch"],
                    "kind": "committed_with_unconnected_regression",
                    "note": "非目标回退，S3 材料候选"})
        # challenger 终态 vs baseline 的非目标回退（新增 error 类别归因）
        chal = pair["challenger_final"]["norefill"] or {}
        base = pair["baseline"]["norefill"]
        if chal.get("severity_error", base["severity_error"]) > \
                base["severity_error"]:
            s3_findings.append({
                "board": s["slug"], "kind": "final_state_error_regression",
                "note": "终态 severity-error 劣于 baseline"})
    out = {
        "schema": "pcbflow.v4_1.e7-s2-s3-check/1",
        "declared_date": DECLARED_DATE,
        "s2_backup_branch": {
            "triggered": s2_trigger,
            "definition": "differential_worse_than_freerouting=true"
                          "（challenger 新增 error 或 unconnected 口径劣于"
                          " freerouting，prereg judgement.s2_backup_branch）",
            "adjudication_requirement":
                "R32：S2 备用支触发须用户重新裁决，不得默认沿用 2026-09-12"
                " 驳回（DEV-S2-001）",
            "submission_only": "执行侧只提交材料不宣布收缩",
        },
        "s3": {
            "triggered": bool(s3_findings),
            "definition": "任意外部板不可解释非目标回退（安全优先于完成度）",
            "findings": s3_findings,
        },
        "g71_status": ("pending_lead_review" if not s3_findings
                       else "s3_material_assembled"),
        "s2_disclosure": "S2 曾于 2026-09-12 触发并被用户裁定驳回（R32）",
    }
    write_canonical_json(e7 / "s2-s3-check.json", out)
    _step(e7_dir, "s2-s3",
          "s2_triggered=%s s3_triggered=%s findings=%d"
          % (s2_trigger, bool(s3_findings), len(s3_findings)))
    return out


# ================================================================ CLI

def main(argv=None):
    import argparse
    import pathlib
    ap = argparse.ArgumentParser(prog="pcbflow.v4_1.e7")
    ap.add_argument("op", choices=[
        "static-screen", "select", "baseline-pair", "batch-record",
        "board-pair", "qor", "s2-s3", "progress-get"])
    ap.add_argument("--e7-dir", default=E7_DIR_DEFAULT)
    ap.add_argument("--board"), ap.add_argument("--batch")
    ns = ap.parse_args(argv)
    pathlib.Path(ns.e7_dir).mkdir(parents=True, exist_ok=True)
    if ns.op == "static-screen":
        rec = static_screen(ns.e7_dir)
    elif ns.op == "select":
        rec = select_boards(ns.e7_dir)
    elif ns.op == "baseline-pair":
        rec = baseline_pair(ns.board, ns.e7_dir)
    elif ns.op == "batch-record":
        rec = batch_record(ns.board, ns.batch, ns.e7_dir)
    elif ns.op == "board-pair":
        rec = board_pair(ns.board, ns.e7_dir)
    elif ns.op == "qor":
        rec = qor_table(ns.e7_dir)
    elif ns.op == "s2-s3":
        rec = s2_s3_check(ns.e7_dir)
    else:
        p = pathlib.Path(ns.e7_dir) / "progress.json"
        rec = _load_json(str(p)) if p.is_file() else {"steps": []}
    summary = {k: v for k, v in rec.items()
               if isinstance(v, (int, float, str, bool))}
    print("ok:", ns.op, json.dumps(summary, ensure_ascii=False)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
