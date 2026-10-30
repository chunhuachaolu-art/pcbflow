# -*- coding: utf-8 -*-
"""P5① A 层 holdout 接触史台账工具（任务书 §6 holdout 纪律 / P5-G3 纪律门）。

用途：A 层 18 板是验收 holdout，任何板源文件内容的读取=接触=永久降级风险
（S-V5-4）。本工具提供全程可审计的接触史台账：

  append(event)  追加一条接触事件（链式哈希防篡改，参照 v5.canonical 风格）
  verify()       全链复核：seq 连续、prev 链接、逐条哈希复算

台账落 out/v5-p5/holdout-ledger/access-log.jsonl，每行一条 canonical JSON：

  {seq, prev_sha256, ts_iso, board_id, source_path, source_sha256,
   action, purpose, operator, extra, event_sha256}

  action ∈ {metadata-read, select, convert, pipeline, drc}（元数据读也登记，
  但任务书口径下索引元数据读取不算接触；板源内容读取前必须先落对应事件）。

强制约束（fail-closed）：
  - convert/pipeline/drc 动作的 board_id 必须在下方 A 层预注册清单内，
    且 source_sha256 必须等于预注册 hash（防读错文件/防 hash 漂移）。
  - board_id 以 "*" 开头仅限任务级批量动作（如首批选定），不对应任何单板。
  - 追加即 fsync；台账 append-only，禁止改写历史行。

事件次序纪律（P5① 裁定）：工具建好后第一条事件=本任务自身 select 动作登记，
之后才准读任何 A 层板源内容；每板在读取源文件前先落对应 action 事件。
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402

LEDGER_PATH = os.path.join(ROOT, "out", "v5-p5", "holdout-ledger",
                           "access-log.jsonl")
GENESIS = "0" * 64
ACTIONS = ("metadata-read", "select", "convert", "pipeline", "drc")
CONTENT_ACTIONS = ("convert", "pipeline", "drc")
OPERATOR = "p5-part1-subagent"

CORPUS_ROOT = ("E:/ZCodeData/.zcode/workspace/default/tools/pcbflow"
               "/datasets/corpus-r2-r1")

# ---- A 层 18 板预注册清单（DISPATCH-LOG.md 2026-09-13「C2/A 预注册」登记段；
#      冻结后只增不改。nets/layers/sha256 均为索引元数据，非板内容）。----
A_LAYER_PREREG = {
    "badgeleds-do-electronics": {"nets": 7, "layers": 2,
        "sha256": "385a1c4dd63e4ac1574648d97d4fedb90170e2629a5f06755405b54182147bc9"},
    "throwing-star-pro": {"nets": 8, "layers": 2,
        "sha256": "4faf84cdcf407ace20a37fdde2102e09cf832edc19d571b5d9270e120ce5a2ea"},
    "pmod-bme280": {"nets": 13, "layers": 2,
        "sha256": "e947bd2aef02cbd858fd8faa6a8ed5b5d4595228e9b1a7512af09916433586a8"},
    "thin-pod": {"nets": 14, "layers": 2,
        "sha256": "2f83fe4c3c46f17003a2f442f196ad88d4348c811b432c41c4decc0a60b4333f"},
    "tmp108": {"nets": 14, "layers": 4,
        "sha256": "1a79e83f615e5a659f10ed0b4dadd0c1573e304a731d3cb23c6b199aa8a8002d"},
    "pmod-crypto": {"nets": 16, "layers": 2,
        "sha256": "22fd890c9cac830db5132c34c216b8107371eccef16d55fa9ac7d0bf019e8537"},
    "stm32-ds2480-emu": {"nets": 29, "layers": 2,
        "sha256": "75b876468e8689b5c68ba7f9c55c2379d7d191cdd2bf212c3029573b36abdb94"},
    "atmega32u4-breakout": {"nets": 46, "layers": 2,
        "sha256": "b541a060871c32c38f44f8ad34c89cdcbb99839ae87d2480712127bbb19559e1"},
    "dc-scm-rot-jumper-card": {"nets": 47, "layers": 2,
        "sha256": "b163f63024c698478903a1cf54efa7dddfdb8d7eadda33e50cb5afb4612ef089"},
    "axiom-micro-mainboard": {"nets": 51, "layers": 4,
        "sha256": "02514f4f89a24062e9738f892b6a41821f94f33fd06e7c541d40a157584bfabe"},
    "usb-gigabit-rev-e": {"nets": 51, "layers": 4,
        "sha256": "9575bc4e67fd7f524e01df221945cbebf04ddfefbc9074a5fe615050a9062c5b"},
    "thatmicpre-v2": {"nets": 57, "layers": 2,
        "sha256": "579d3b4f04a72b2987d89053fbd3313523642e25e9a3968639ea7d2fc0a94a7e"},
    "pmod-i2c24io": {"nets": 61, "layers": 2,
        "sha256": "85fdb79d9cda349ca740d9092d49866b2beefc2e575e49b5f3679d817cbe5c4c"},
    "m2-pcie-adapter": {"nets": 65, "layers": 4,
        "sha256": "36533460dd1e940f87672a101aca968ff0e2cc1687a26e02b32b2177f95414f5"},
    "om-flexgrid-v4-rigid-pcb": {"nets": 87, "layers": 4,
        "sha256": "e4039062c4ede74c51b600bcb862d41b4fc7d3441b6ae44c7788b0311909af4c"},
    "ov9281-dual-camera-board": {"nets": 124, "layers": 4,
        "sha256": "9a73c217474afa28fb8cb29f26af0eab4f69481db1f7559e9a1aa26540d7f382"},
    "cm5-minima-rev3": {"nets": 220, "layers": 6,
        "sha256": "1b7e2d8f928e3fda3254a699d1971b5b543eda2f8fa63cb2100f2979beef12f4"},
    "thunderbolt-pcie-adapter": {"nets": 268, "layers": 6,
        "sha256": "547136e29d3159e1601139e48ee33c31974cf621d3c3135da898d60227600bd2"},
    # ---- V5-BOARDINTAKE-R1 追加登记（2026-09-24，U4「只增不改（追加须新
    #      登记）」追加通道；三裁放行=LEAD-REVIEW-BOARDINTAKE-R1-STOP-2026-09-24
    #      §5；nets=adapter 纯内存试转 v5 信号网数，索引元数据非板内容。
    #      tinytapeout-demo/pslab-v6/sdi-mipi-bridge 三板持久零渲染零读图
    #      红线随批生效至用户明示解除）。----
    "esp32-devkit-lipo-rev-c": {"nets": 72, "layers": 2,
        "sha256": "3e7cd18fe5abcb4a93fd3e95934a74b7d396bcf0992da7861c70d9e87191558e"},
    "torxhat": {"nets": 75, "layers": 2,
        "sha256": "fb6097880a515424c7ac67c56330dfecece8eb70b79d21047e2516ec33e14aca"},
    "ice40hx1k-evb-rev-b": {"nets": 96, "layers": 4,
        "sha256": "18407352cb5c31bc5c93804af764220f158017b8d2e7f2da5585a5155d188ca1"},
    "tinytapeout-demo": {"nets": 148, "layers": 4,
        "sha256": "773a0e295ca6cc31a088088ec29efa98ee67ee6bcbaac98d281f5433c45320db"},
    "pslab-v6": {"nets": 173, "layers": 4,
        "sha256": "e80cea8ba899d833bb75c1efa9f81df7552c5c65fd1c82508afefe22fd010389"},
    "sdi-mipi-bridge": {"nets": 175, "layers": 6,
        "sha256": "41749fed319c279746f92c10ec1d408660afaeee313a8f63bb22f2285e9adfd2"},
}

# ---- C2 层 10 板（网数，仅用于三分位秩推导的元数据，同登记段）。----
C2_LAYER_NETS = {
    "vga-panel-breakout": 5, "si-simulation-test-board": 13,
    "alvium-flex-csi-100mm-double-same-side": 14, "anavi-fume-extractor": 17,
    "ice40hx1k-evb-rev-b": 17, "esp32-devkit-lipo-rev-c": 33,
    "badge-pcb": 36, "torxhat": 75, "anthc": 173,
    "teres-pcb1-a64-main-rev-c": 285,
}


def source_path_for(board_id):
    """语料源 .kicad_pcb 路径（由 manifest 索引 dir+files 拼出；此处内联
    预注册板的文件名——来源同 DISPATCH-LOG 登记段与 corpus manifest）。"""
    names = {
        "badgeleds-do-electronics": "raw/angelisidro__badgeleds-do-electronics/PCB_LDE.kicad_pcb",
        "throwing-star-pro": "raw/greatscottgadgets__throwing-star-pro/throwing-star-pro.kicad_pcb",
        "pmod-bme280": "raw/fm4dd__pmod-bme280/bme280.kicad_pcb",
        "thin-pod": "raw/Pealie__thin-pod/Thin-Pod.kicad_pcb",
        "tmp108": "raw/6mil-Labs__tmp108/tmp108.kicad_pcb",
        "pmod-crypto": "raw/fm4dd__pmod-crypto/atecc508a.kicad_pcb",
        "stm32-ds2480-emu": "raw/alitekin2fx__stm32-ds2480-emu/stm32_ds2480_emu.kicad_pcb",
        "atmega32u4-breakout": "raw/everyday-dev__atmega32u4-breakout/atmegaXu4_breakout.kicad_pcb",
        "dc-scm-rot-jumper-card": "raw/antmicro__dc-scm-rot-jumper-card/dc-scm-rot-jumper-card.kicad_pcb",
        "axiom-micro-mainboard": "raw/apertus-open-source-cinema__axiom-micro-mainboard/pcb.kicad_pcb",
        "usb-gigabit-rev-e": "raw/OLIMEX__usb-gigabit-rev-e/USB-GIGABIT_Rev_E.kicad_pcb",
        "thatmicpre-v2": "raw/ojg__thatmicpre-v2/thatmicpre_v2.kicad_pcb",
        "pmod-i2c24io": "raw/fm4dd__pmod-i2c24io/i2c24io.kicad_pcb",
        "m2-pcie-adapter": "raw/antmicro__m2-pcie-adapter/m2-pcie-adapter.kicad_pcb",
        "om-flexgrid-v4-rigid-pcb": "raw/Open-Muscle__om-flexgrid-v4-rigid-pcb/OM-FlexGrid-Rigid-PCB.kicad_pcb",
        "ov9281-dual-camera-board": "raw/antmicro__ov9281-dual-camera-board/ov9281-dual-camera-board.kicad_pcb",
        "cm5-minima-rev3": "raw/piecol__cm5-minima-rev3/CM5_MINIMA_3.kicad_pcb",
        "thunderbolt-pcie-adapter": "raw/antmicro__thunderbolt-pcie-adapter/thunderbolt-pcie-adapter.kicad_pcb",
        # V5-BOARDINTAKE-R1 追加（2026-09-24，同上追加通道）。
        "esp32-devkit-lipo-rev-c": "raw/OLIMEX__esp32-devkit-lipo-rev-c/ESP32-DevKit-Lipo_Rev_C.kicad_pcb",
        "torxhat": "raw/RobotStudyCompanion__torxhat/RSC_extension_board.kicad_pcb",
        "ice40hx1k-evb-rev-b": "raw/OLIMEX__ice40hx1k-evb-rev-b/iCE40HX1K-EVB_Rev_B.kicad_pcb",
        "tinytapeout-demo": "raw/TinyTapeout__tinytapeout-demo/tinytapeout-demo.kicad_pcb",
        "pslab-v6": "raw/fossasia__pslab-v6/PSLab.kicad_pcb",
        "sdi-mipi-bridge": "raw/antmicro__sdi-mipi-bridge/sdi-mipi-bridge.kicad_pcb",
    }
    if board_id not in names:
        raise KeyError("A 层预注册清单无此板: %s" % board_id)
    return "%s/%s" % (CORPUS_ROOT, names[board_id])


def derive_tertiles():
    """重演预注册三分位：28 板池按 (net_count, board_id) 升序连续切三层
    10/9/9（秩 1-10 低 / 11-19 中 / 20-28 高）。返回 {board_id: tertile}
    （仅 A 层 18 板），并断言 6/6/6。"""
    pool = {b: v["nets"] for b, v in A_LAYER_PREREG.items()}
    pool.update(C2_LAYER_NETS)
    assert len(pool) == 28, pool
    ordered = sorted(pool.items(), key=lambda kv: (kv[1], kv[0]))
    out = {}
    for rank, (bid, _nets) in enumerate(ordered, start=1):
        if bid in A_LAYER_PREREG:
            out[bid] = "low" if rank <= 10 else ("mid" if rank <= 19 else "high")
    counts = {t: sum(1 for v in out.values() if v == t)
              for t in ("low", "mid", "high")}
    assert counts == {"low": 6, "mid": 6, "high": 6}, counts
    return out


def _event_digest(event):
    payload = {k: v for k, v in event.items() if k != "event_sha256"}
    return hashlib.sha256(canonical.canonical_json(payload)).hexdigest()


def read_events(path=LEDGER_PATH):
    if not os.path.exists(path):
        return []
    events = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except ValueError as exc:
                raise ValueError("台账第 %d 行不可解析: %s" % (lineno, exc))
    return events


def append(board_id, action, purpose, source_path, source_sha256,
           extra=None, operator=OPERATOR, path=LEDGER_PATH):
    """追加一条接触事件并返回之。内容接触动作（convert/pipeline/drc）对
    A 层板强制预注册 hash 对账；失败即抛 LedgerError，不落任何行。"""
    if action not in ACTIONS:
        raise ValueError("非法 action: %r（允许 %s）" % (action, ACTIONS))
    if board_id.startswith("*"):
        if action not in ("select", "metadata-read"):
            raise ValueError("任务级批量事件（* 前缀）只允许 select/metadata-read")
    elif board_id in A_LAYER_PREREG:
        if action in CONTENT_ACTIONS:
            prereg = A_LAYER_PREREG[board_id]["sha256"]
            if source_sha256 != prereg:
                raise ValueError(
                    "%s: source_sha256 与预注册不符（预注册 %s…，得到 %s…）"
                    % (board_id, prereg[:12], str(source_sha256)[:12]))
    else:
        raise ValueError("board_id 不在 A 层预注册清单且无 * 前缀: %r" % board_id)

    events = read_events(path)
    event = {
        "seq": len(events) + 1,
        "prev_sha256": events[-1]["event_sha256"] if events else GENESIS,
        "ts_iso": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "board_id": board_id,
        "source_path": source_path,
        "source_sha256": source_sha256,
        "action": action,
        "purpose": purpose,
        "operator": operator,
        "extra": extra if extra is not None else {},
    }
    event["event_sha256"] = _event_digest(event)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(canonical.canonical_text(event) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return event


def verify(path=LEDGER_PATH):
    """全链复核：seq 连续、prev 链接、逐条 event_sha256 复算、action 枚举、
    A 层板 hash 预注册对账。返回 {"ok", "n_events", "problems",
    "boards_touched"}。"""
    problems = []
    events = []
    try:
        events = read_events(path)
    except ValueError as exc:
        return {"ok": False, "n_events": 0, "problems": [str(exc)],
                "boards_touched": {}}
    prev = GENESIS
    boards_touched = {}
    for i, ev in enumerate(events, start=1):
        where = "event #%d" % i
        if ev.get("seq") != i:
            problems.append("%s: seq=%r 应为 %d" % (where, ev.get("seq"), i))
        if ev.get("prev_sha256") != prev:
            problems.append("%s: prev_sha256 链断裂" % where)
        if _event_digest(ev) != ev.get("event_sha256"):
            problems.append("%s: event_sha256 复算不符（行被改写？）" % where)
        if ev.get("action") not in ACTIONS:
            problems.append("%s: 非法 action %r" % (where, ev.get("action")))
        bid = ev.get("board_id", "")
        if not bid.startswith("*") and bid in A_LAYER_PREREG:
            if ev.get("source_sha256") != A_LAYER_PREREG[bid]["sha256"]:
                problems.append("%s: %s source_sha256≠预注册" % (where, bid))
            boards_touched.setdefault(bid, set()).add(ev.get("action"))
        prev = ev.get("event_sha256")
    return {"ok": not problems, "n_events": len(events),
            "problems": problems,
            "boards_touched": {k: sorted(v) for k, v in
                               sorted(boards_touched.items())}}


def init_first8(selection_path=None, path=LEDGER_PATH):
    """P5① 首批 8 板选定（仅索引元数据）+ 台账初始化。

    程序：derive_tertiles() 重演预注册三分位（low/mid/high 各 6 块 A 板）→
    各取网数最少的前 3+3+2 块（共 8；理由：P5-G1 需 ≥5 板 SAT+kicad-cli
    零违例，网数最少者可行概率最高，同时保三分位覆盖）→ 事件 #1=本任务
    自身批量 select 登记 → 8 板逐板 select 登台账 → first8-selection.json
    （provenance 头，确定性：无时间戳）落盘。幂等保护：台账非空即拒绝。
    """
    if read_events(path):
        raise RuntimeError("台账非空（%d 条），init-first8 只准一次" %
                           len(read_events(path)))
    tertiles = derive_tertiles()
    by_t = {t: sorted((b for b, tt in tertiles.items() if tt == t),
                      key=lambda b: (A_LAYER_PREREG[b]["nets"], b))
            for t in ("low", "mid", "high")}
    picks = by_t["low"][:3] + by_t["mid"][:3] + by_t["high"][:2]
    assert len(picks) == 8, picks

    manifest_rel = CORPUS_ROOT + "/manifest.json"
    with open(manifest_rel, "rb") as f:
        manifest_sha = hashlib.sha256(f.read()).hexdigest()
    reason = ("P5① 首批 8 板批量选定：预注册三分位 low/mid/high 各取网数最少"
              "前 3+3+2 块；依据=P5-G1（≥5 板 SAT+kicad-cli 零违例）下网数最少"
              "者可行概率最高，且保三分位覆盖；仅用索引元数据（manifest 网数）"
              "，板内容零开启")
    append("*first8-batch", "select", reason, manifest_rel, manifest_sha,
           extra={"n_boards": 8, "tertile_rule": "3+3+2", "board_ids": picks},
           path=path)
    rows = []
    for bid in picks:
        ent = A_LAYER_PREREG[bid]
        sp = source_path_for(bid)
        append(bid, "select",
               "首批选定（%s 三分位，nets=%d，%d 层）：进入 P5① convert/试跑范围"
               % (tertiles[bid], ent["nets"], ent["layers"]),
               sp, ent["sha256"],
               extra={"tertile": tertiles[bid], "nets": ent["nets"],
                      "layers": ent["layers"]},
               path=path)
        rows.append({"board_id": bid, "tertile": tertiles[bid],
                     "net_count": ent["nets"], "layers": ent["layers"],
                     "board_file_sha256": ent["sha256"],
                     "source_path": sp})
    trial = min(picks, key=lambda b: (A_LAYER_PREREG[b]["nets"], b))

    doc = {
        "purpose": "P5① 首批 8 板选定清单（预注册三分位前 2-3 板/层，共 8；"
                   "仅索引元数据，板内容零开启）",
        "selection_rule": "derive_tertiles() 重演 28 板池 (net_count, board_id) "
                          "升序三连续层 10/9/9（秩 1-10 低/11-19 中/20-28 高）；"
                          "low/mid/high 各取前 3+3+2 块",
        "rationale": "P5-G1 需 ≥5 板 SAT 且 kicad-cli 外权威零违例；各三分位取"
                     "网数最少者最大化可行概率，高三分位取 2 块保覆盖；试跑板="
                     "首批中网数最少者",
        "tertiles": {t: by_t[t] for t in ("low", "mid", "high")},
        "selected": rows,
        "trial_board": trial,
        "deferred_10": [b for b in sorted(A_LAYER_PREREG) if b not in picks],
        "ledger": "out/v5-p5/holdout-ledger/access-log.jsonl",
    }
    header = {
        "provenance": {"generator": "v5.p5-holdout-ledger",
                       "generator_version": "0.1.0",
                       "board_sha256": GENESIS},
    }
    payload = dict(header)
    payload.update(doc)
    sel = selection_path or os.path.join(os.path.dirname(path),
                                         "first8-selection.json")
    os.makedirs(os.path.dirname(sel), exist_ok=True)
    with open(sel, "wb") as f:
        f.write(canonical.canonical_json(payload))
    return picks, trial, sel


def main(argv=None):
    ap = argparse.ArgumentParser(description="P5① A 层 holdout 接触史台账")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_append = sub.add_parser("append", help="追加一条接触事件")
    ap_append.add_argument("--board-id", required=True)
    ap_append.add_argument("--action", required=True, choices=ACTIONS)
    ap_append.add_argument("--purpose", required=True)
    ap_append.add_argument("--source-path", default="")
    ap_append.add_argument("--source-sha256", default="")
    ap_append.add_argument("--extra", default="{}")

    ap_verify = sub.add_parser("verify", help="全链复核")
    ap_verify.add_argument("--path", default=LEDGER_PATH)

    ap_show = sub.add_parser("show", help="按板过滤展示")
    ap_show.add_argument("--board-id", default=None)

    sub.add_parser("init-first8", help="首批 8 板选定+台账初始化（只准一次）")

    args = ap.parse_args(argv)
    if args.cmd == "append":
        ev = append(args.board_id, args.action, args.purpose,
                    args.source_path, args.source_sha256,
                    extra=json.loads(args.extra))
        print("appended seq=%d %s %s %s" % (ev["seq"], ev["action"],
                                            ev["board_id"], ev["event_sha256"][:12]))
        return 0
    if args.cmd == "verify":
        rep = verify(args.path)
        print(json.dumps({**rep, "boards_touched": rep["boards_touched"]},
                         ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if rep["ok"] else 1
    if args.cmd == "show":
        for ev in read_events():
            if args.board_id in (None, ev["board_id"]):
                print("%3d %s %-9s %-28s %s" % (ev["seq"], ev["ts_iso"],
                                                ev["action"], ev["board_id"],
                                                ev["purpose"][:60]))
        return 0
    if args.cmd == "init-first8":
        picks, trial, sel = init_first8()
        print("first8: %s" % ", ".join(picks))
        print("trial_board: %s" % trial)
        print("selection_file: %s" % sel)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
