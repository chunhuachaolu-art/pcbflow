"""PCBFlow 铜箔闭环 P2b+P4 —— 回路驱动、显式 adopt 采纳通道、KiCad5 只读降级。

一轮（revision）= 摄取 base 板 → 镜像（build_inputs + svg_route_package.build）
→ 三向校验（`board_binding.verify_board_binding` 板↔manifest +
`svg_route_package.verify_consistency` manifest↔SVG，任一非空即 blocked）
→ `copper_patch.apply_patch`（结构守卫在补丁内）→ 写 staging 副本 →
产出 DRC 请求（**不执行 DRC**）→ 状态 `awaiting_drc`。

架构红线（本模块遵守）：**零子进程、零网络**。DRC 由编排侧执行（kicad-cli
不属 pcbflow 包），本模块只产出请求、消费报告 —— 与
`pcbflow/residual_cmd.py` 的"pcbflow 零子进程，DRC JSON 为 hash 输入"同口径。

落盘（本模块是少数做文件 IO 的 pcbflow 模块，但仍是零子进程纯逻辑）：
追加式版本目录 `<out_dir>/copper-loop/<base_label>/rev-N/`：

    base/<board 名>            只读基准副本（逐字节，sha 由 reference.json 钉）
    base/reference.json        基准引用（basename/sha256/bytes/eol/identity_basis）
    mirror/board.svg           SVG 镜像
    mirror/route-manifest.json route-manifest（合同 v2）
    mirror/binding-report.json 板↔manifest 核对报告（violations/pending/counts/info）
    mirror/three-way.json      三向校验汇总（两条腿的违规清单）
    mirror/adapter-report.json 适配层上报清单（**仅** adapter 模式）
    patch-set.json             本轮补丁集（canonical 化后落盘）
    patched/<board 名>         staging 板（逐字节；sha 记账）
    drc/request.json           DRC 请求（编排侧据此跑 kicad-cli）
    drc/<basename>.json        编排侧产出的 DRC 报告（本模块只读）
    drc/accept-record.json     accept/reject 判定台账
    adopt-record.json          adopt 台账（设计侧前后 sha + 备份）
    ledger.json                追加式事件台账（含 apply_patch 完整 ledger）
    revision-record.json       本轮记录（核心事实）

**只追加不覆写**：`rev-N` 一旦存在即不得被覆盖 —— 新轮取 `N+1`；
既有 `rev-N` 不完整（无 revision-record.json）或目标 `rev-N` 已存在 ⇒
fail-closed 报 `blocked`（绝不静默覆盖，防并发/重复调用互踩）。

canonical（核心产物无 wall-clock、无主机绝对路径）：
- 记录只用基名/相对路径；时间戳、绝对路径、耗时只出现在
  `evaluation_metadata`（keys 与 `pcbflow/gate.py` 同约定：evaluated_at/
  host/elapsed_s 恒 null；运行时观察值放 `observed`，绝对路径放
  `resolved_paths`），不进 `core_fact_sha256`（`core_fact_sha256(record)`
  可独立重算核对）。

KiCad5 只读降级（两层，均**不**伪造能力）：
1. 身份层：`identity_basis == "geometric_fallback"`（KiCad5 语料无
   `(tstamp …)` 可作身份）时，**补丁阶段一律** `blocked`，reason =
   `edit_unsupported_identity_basis`；镜像阶段照常可用；
2. 适配层：`board_svg_adapter.build_inputs` 依赖 `geo.parse_board`（只认
   KiCad 的 `(footprint … (property "Reference" …))`）—— KiCad5 的
   `(module …)` 板会让它抛异常（实测 pcbench-r1 162 个板全部如此）。此时
   **且** identity_basis 为 `geometric_fallback` 时，回落到
   `mirror_mode="copper_only_degraded"`：只由铜箔事实（segment/via/zone）
   构造镜像（pads 为空、无板框），并在记录里显式标注（`degraded_notes`、
   `pads: 0`）。非 KiCad5 板不享有该回落（blocked）。

adopt 是**唯一**允许触碰设计侧的路径（本模块其余函数只写版本目录）：
- 先核 `sha256(design_board_path) == base.sha256`，不等 ⇒ blocked（stale，
  防覆盖别人/别的轮次的改动）；
- 只有 `accepted` 状态（或 KiCad5 镜像降级的 `mirror_only`，见下）才允许；
- adopt 前后写 sha256 台账 + 备份既有文件
  `<design_stem>_pre-adopt-<rev>.kicad_pcb`（已存在即 fail-closed，不覆盖）；
- 设计侧写入**不**混进 staging 事务：`transaction.live_board_touched` 恒
  false（staging 事务的零写见证不被破坏），设计侧真实写入记在
  `adopt-record.json`（`design_board_written: true` + pre/post sha）；
- KiCad5（`identity_basis == "geometric_fallback"`）时 adopt 允许但必须显式
  记录降级语义：`mirror_only` 状态（本轮未请求补丁）可 adopt 基准本身
  （逐字节相同，零风险），adopt 记录里标 `identity_degradation`
  （`patch_capable: false`、补丁拒绝 reason、后续编辑须人工复核）。
"""

from __future__ import annotations

import collections
import json
import os
import re
from datetime import datetime, timezone

from . import board_binding, board_svg_adapter, config, copper_model
from . import copper_patch, geo, hashing, lease, svg_route_package

__all__ = [
    "SCHEMA", "CopperLoopError", "identity_registry_from_board",
    "core_fact_sha256", "mirror_revision", "patch_revision", "revision",
    "accept_revision", "rollback_revision", "adopt",
]

SCHEMA = "pcbflow.copper-loop/1"
LEDGER_SCHEMA = "pcbflow.copper-loop-ledger/1"
DRC_REQUEST_SCHEMA = "pcbflow.copper-drc-request/1"
PATCH_SET_SCHEMA = "pcbflow.copper-patch-set/1"
ACCEPT_SCHEMA = "pcbflow.copper-loop-accept/1"
ADOPT_SCHEMA = "pcbflow.copper-loop-adopt/1"
REGISTRY_DERIVED_SCHEMA = "pcbflow.copper-loop-derived-registry/1"

LOOP_DIRNAME = "copper-loop"
RECORD_NAME = "revision-record.json"
LEDGER_NAME = "ledger.json"
PATCH_SET_NAME = "patch-set.json"
ACCEPT_NAME = os.path.join("drc", "accept-record.json")
ADOPT_NAME = "adopt-record.json"
REQUEST_NAME = os.path.join("drc", "request.json")
BASELINE_REF_NAME = os.path.join("base", "reference.json")
STAGING_REPORT_REL = os.path.join("drc", "staging.json")
BASELINE_REPORT_REL = os.path.join("drc", "baseline.json")

STATUS_MIRROR_ONLY = "mirror_only"
STATUS_AWAITING_DRC = "awaiting_drc"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_BLOCKED = "blocked"
STATUS_ROLLED_BACK = "rolled_back"

MIRROR_MODE_ADAPTER = "adapter"
MIRROR_MODE_DEGRADED = "copper_only_degraded"

REASON_EDIT_UNSUPPORTED_IDENTITY = "edit_unsupported_identity_basis"

#: DRC 门口径（显式，保守）：只对 `violations` 与基线做 keyset 比较；
#: `unconnected_items` 与 ASM-4 同口径 —— 如实记账但不作 gate 判据。
DRC_GATE_RULE = ("对基线 keyset：出现新增 violation ⇒ rejected；无新增 ⇒ "
                 "accepted；无基线可依 ⇒ 任何 violation 都视为新增（保守）")

_REV_RE = re.compile(r"^rev-(\d+)$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ABS_PATH_RE = re.compile(r"[A-Za-z]:[\\/]|^/|^\\\\")
_BASENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class CopperLoopError(ValueError):
    """调用方参数形状错误（程序员错误；预期内的状态冲突一律返回 blocked）。"""


# --------------------------------------------------------------------- 工具

def _isnum(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _q6(v) -> float:
    return round(float(v), 6)


def _q3(v) -> float:
    return round(float(v), 3)


def _read_text(path: str) -> str:
    """读板/读文本：`newline=""` 保留 CRLF（项目已知陷阱：默认会归一化）。"""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_text(path: str, text: str) -> str:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return hashing.sha256_text(text)


def _write_bytes(path: str, data: bytes) -> str:
    with open(path, "wb") as f:
        f.write(data)
    return hashing.sha256_bytes(data)


def _write_canonical_json(path: str, obj) -> str:
    """canonical JSON 落盘（UTF-8/LF/sort_keys/固定 indent/结尾换行）。"""
    data = hashing.canonical_json_bytes(obj)
    with open(path, "wb") as f:
        f.write(data)
    return hashing.sha256_bytes(data)


def _rel(revision_dir: str, path: str) -> str:
    """修订目录内相对路径（ASCII 分隔，canonical：不写绝对路径）。"""
    return os.path.relpath(path, revision_dir).replace(os.sep, "/")


def _sanitize_label(name: str) -> str:
    out = _BASENAME_RE.sub("-", name).strip("-.")
    return out[:60] or "board"


def _has_abs_path(obj) -> bool:
    """递归查宿主绝对路径（Windows 盘符/UNC/posix 绝对路径）。"""
    if isinstance(obj, dict):
        return any(_has_abs_path(k) or _has_abs_path(v) for k, v in obj.items())
    if isinstance(obj, list):
        return any(_has_abs_path(v) for v in obj)
    if isinstance(obj, str):
        return bool(_ABS_PATH_RE.search(obj))
    return False


def _core_body(record: dict) -> dict:
    """核心事实体：剔除 evaluation_metadata（不进 core hash，§1.4 同口径）。"""
    return {k: v for k, v in record.items() if k != "evaluation_metadata"}


def core_fact_sha256(record: dict) -> str:
    """核心事实 hash（剔除 evaluation_metadata、剔除自身字段后可独立重算）。"""
    body = _core_body(record)
    body.pop("core_fact_sha256", None)
    return hashing.sha256_bytes(hashing.canonical_json_bytes(body))


def _evaluation_metadata(revision_dir, elapsed_s, resolved_paths=None) -> dict:
    """evaluation_metadata（wall-clock/主机/绝对路径只此一处，不进 core hash）。

    键与 `gate.py` 同约定：evaluated_at/host/elapsed_s —— 核心产物的这三项
    恒 null（byte-exact 确定性）；运行时观察值与解析出的绝对路径另放
    `observed` / `resolved_paths`，并显式声明不参加核心事实 hash。
    """
    return {
        "evaluated_at": None,
        "host": None,
        "elapsed_s": None,
        "excluded_from_core_fact_sha256": True,
        "note": "本块不参加 core_fact_sha256（同 gate_record 约定）：wall-clock/"
                "主机绝对路径只在此处；核心事实见 record 其余字段",
        "observed": {
            "elapsed_s": None if elapsed_s is None else round(float(elapsed_s), 6),
            "wall_clock_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
        },
        "resolved_paths": dict(resolved_paths or {}),
    }


def _finalize(record: dict) -> dict:
    record["core_fact_sha256"] = core_fact_sha256(record)
    return record


def _blocked_record(reasons, stage, revision_dir=None, **fields) -> dict:
    """失败记录。给了 `revision_dir` ⇒ 落盘成该轮次的 revision-record.json
    （失败也是轮次事实，须可审计）；否则只是"未落盘的尝试结果"。

    状态机纪律：拒绝对是**尝试**而非轮次状态 —— 已存在轮次的拒绝一律走
    `_refuse`（不改轮次记录，只在台账追加事件）。
    """
    rec = {
        "schema": SCHEMA,
        "revision_id": fields.pop("revision_id", None),
        "base_label": fields.pop("base_label", None),
        "rev": fields.pop("rev", None),
        "status": STATUS_BLOCKED,
        "verdict": STATUS_BLOCKED,
        "stage": stage,
        "blocked_at": stage,
        "ok": False,
        "usable": False,
        "persisted": revision_dir is not None,
        "reasons": list(reasons),
        "rollback": "none",
        "adopted": False,
    }
    rec.update(fields)
    rec["evaluation_metadata"] = _evaluation_metadata(
        revision_dir, None, _resolved_paths(revision_dir, rec)
        if revision_dir else None)
    _finalize(rec)
    if revision_dir is not None:
        _write_canonical_json(os.path.join(revision_dir, RECORD_NAME), rec)
    return rec


def _refuse(record: dict, revision_dir: str, stage: str, reasons,
            **extra) -> dict:
    """阶段拒绝（既有轮次）：**不改**轮次记录，只在台账追加 `*_refused` 事件。

    返回尝试结果：status=blocked + persisted=false + `revision_status` =
    轮次真实状态（本次尝试未改动它）。防"一次失败的 adopt 尝试把 awaiting_drc
    轮次写成 blocked"这类状态污染。
    """
    _append_event(revision_dir, record, "%s_refused" % stage,
                  status=STATUS_BLOCKED, reasons=list(reasons))
    res = {
        "schema": SCHEMA,
        "revision_id": record.get("revision_id"),
        "base_label": record.get("base_label"),
        "rev": record.get("rev"),
        "status": STATUS_BLOCKED,
        "verdict": STATUS_BLOCKED,
        "stage": stage,
        "blocked_at": stage,
        "ok": False,
        "usable": False,
        "persisted": False,
        "revision_status": record.get("status"),
        "revision_core_fact_sha256": record.get("core_fact_sha256"),
        "reasons": list(reasons),
    }
    res.update(extra)
    res["evaluation_metadata"] = _evaluation_metadata(
        revision_dir, None, _resolved_paths(revision_dir, record))
    return _finalize(res)


# ----------------------------------------------------------------- 路径/台账

def _loop_root(out_dir: str) -> str:
    return os.path.join(out_dir, LOOP_DIRNAME)


def _rev_dir(out_dir: str, base_label: str, rev: int) -> str:
    return os.path.join(_loop_root(out_dir), base_label, "rev-%d" % rev)


def _next_rev(loop_label_dir: str) -> "tuple[int, str | None]":
    """下一个可用轮次号；既有轮次不完整 ⇒ (0, reason)（fail-closed）。

    绝不"跳过"不完整的既有 rev-N：无法区分"崩溃残留"与"并发在写"，
    故一律拒绝（防静默覆盖别人/别的轮次的产物）。
    """
    if not os.path.isdir(loop_label_dir):
        return 1, None
    nums = []
    for name in sorted(os.listdir(loop_label_dir)):
        m = _REV_RE.match(name)
        if m:
            nums.append(int(m.group(1)))
    for n in nums:
        d = os.path.join(loop_label_dir, "rev-%d" % n)
        if not os.path.isfile(os.path.join(d, RECORD_NAME)):
            return 0, ("incomplete_existing_revision: 既有 rev-%d 无 %s"
                       "（崩溃残留或并发在写）：拒绝在该轮次目录上继续，"
                       "须人工处置后重跑" % (n, RECORD_NAME))
    return (max(nums) + 1 if nums else 1), None


def _load_record(revision_dir: str):
    """→ (record, reason)。记录缺失/不可解析一律 fail-closed。"""
    path = os.path.join(revision_dir, RECORD_NAME)
    if not os.path.isfile(path):
        return None, "revision_record_missing: %s 不存在" % RECORD_NAME
    try:
        rec = _read_json(path)
    except Exception as exc:
        return None, ("revision_record_unparseable: %s（%s: %s）"
                      % (RECORD_NAME, exc.__class__.__name__, exc))
    if not isinstance(rec, dict) or rec.get("schema") != SCHEMA:
        return None, ("revision_record_invalid: %s 不是 %s 记录"
                      % (RECORD_NAME, SCHEMA))
    return rec, None


def _save_record(revision_dir: str, record: dict) -> str:
    return _write_canonical_json(os.path.join(revision_dir, RECORD_NAME),
                                 _finalize(record))


def _load_ledger(revision_dir: str):
    path = os.path.join(revision_dir, LEDGER_NAME)
    if not os.path.isfile(path):
        return {"schema": LEDGER_SCHEMA, "events": []}, None
    try:
        led = _read_json(path)
    except Exception as exc:
        return None, ("ledger_unparseable: %s（%s: %s）"
                      % (LEDGER_NAME, exc.__class__.__name__, exc))
    if not isinstance(led, dict) or not isinstance(led.get("events"), list):
        return None, "ledger_invalid: %s 形状非法" % LEDGER_NAME
    return led, None


def _append_event(revision_dir: str, record: dict, event: str, **fields) -> dict:
    """追加台账事件（台账是追加式事实流；记录 hash 链式引用上一态）。"""
    led, reason = _load_ledger(revision_dir)
    if led is None:  # 台账不可用 ⇒ 不静默重建（会丢证据）
        raise CopperLoopError(reason)
    entry = {"seq": len(led["events"]), "event": event,
             "record_core_fact_sha256": record.get("core_fact_sha256")}
    entry.update(fields)
    led["events"].append(entry)
    led.setdefault("revision_id", record.get("revision_id"))
    led["schema"] = LEDGER_SCHEMA
    _write_canonical_json(os.path.join(revision_dir, LEDGER_NAME), led)
    return entry


def _set_patch_ledger(revision_dir: str, patch_ledger: dict) -> None:
    """把 `copper_patch.apply_patch` 的完整 ledger 存进台账的 `patch_ledger` 槽。

    台账不可用（被外部改坏/不可解析）⇒ 抛 `CopperLoopError`：同 `_append_event`
    口径，**不**静默重建台账（重建会丢掉既有事件流这份证据）。
    """
    led, reason = _load_ledger(revision_dir)
    if led is None:
        raise CopperLoopError(reason)
    led["patch_ledger"] = patch_ledger
    led["schema"] = LEDGER_SCHEMA
    _write_canonical_json(os.path.join(revision_dir, LEDGER_NAME), led)


# --------------------------------------------------------------- 注册表口径

def _net_map_from_registry(registry) -> dict:
    """注册表 → {net_id: net_name}（board_binding 的 net_map 口径）。"""
    out = {}
    for n in (registry.get("nets") or []) if isinstance(registry, dict) else []:
        if not isinstance(n, dict):
            continue
        nid, name = n.get("net_id"), n.get("net_name")
        if isinstance(nid, str) and nid and isinstance(name, str) and name:
            out[nid] = name
    return out


def identity_registry_from_board(board_path: str, copper: dict = None) -> dict:
    """从板自身事实派生**身份注册表**（`net_id := 板侧 net 名`）。

    用途：无权威 `net-registry.json` 的板（语料板/外部板）也能进镜像。
    这是显式声明的派生口径（不是权威注册表）：无别名、无 excluded、无
    relations；`board_svg_adapter` 只按 `net_name` 建索引，故 net_id 与
    net_name 逐字相同的派生注册表足以让"能映射的映射"成立。派生事实在
    记录里记 `registry.basis=derived_identity_from_board`，绝不冒充权威。
    """
    if copper is None:
        copper = copper_model.parse_copper_file(board_path)
    names = set()
    for kind in ("segments", "vias", "zones"):
        for e in copper.get(kind) or []:
            net = e.get("net")
            if isinstance(net, str) and net:
                names.add(net)
    try:  # 焊盘侧 net 名（提高覆盖率；geo 只认 KiCad 6+/10 板，失败即跳过）
        for pad in geo.parse_board(board_path).get("pads") or []:
            net = pad.get("net")
            if isinstance(net, str) and net:
                names.add(net)
    except Exception:
        pass
    return {
        "schema_version": REGISTRY_DERIVED_SCHEMA,
        "derived": True,
        "derivation": "net_id := 板侧 net 名（确定性、逐字相同；无别名/无 "
                      "excluded/无 relations）",
        "nets": [{"net_id": n, "net_name": n, "derived": True}
                 for n in sorted(names)],
    }


def _resolve_registry(board_path: str, registry, copper: dict = None):
    """→ (registry_dict, registry_meta) 或 (None, reason)。

    `copper`：已解析的铜箔事实（由调用方复用，避免 `identity_registry_from_board`
    再全量 parse 一次 —— 纯性能参数，不改变任何产出：两者对同一板文本的解析
    结果逐字节相同）。
    """
    if registry is None:
        reg = identity_registry_from_board(board_path, copper)
        return reg, {
            "basis": "derived_identity_from_board",
            "source_basename": None,
            "sha256": hashing.sha256_bytes(hashing.canonical_json_bytes(reg)),
            "nets": len(reg["nets"]),
            "note": "未给 --registry：按板侧 net 名派生身份注册表（net_id == "
                    "net_name）；权威注册表（如 out/revc-a3/net-registry.json）"
                    "请显式传入",
        }
    if isinstance(registry, str):
        if not os.path.isfile(registry):
            return None, ("registry_missing: 注册表文件不存在: %s"
                          % os.path.basename(registry))
        try:
            reg = _read_json(registry)
        except Exception as exc:
            return None, ("registry_unparseable: %s（%s: %s）"
                          % (os.path.basename(registry),
                             exc.__class__.__name__, exc))
        if not isinstance(reg, dict) or not isinstance(reg.get("nets"), list):
            return None, ("registry_invalid: %s 不是含 nets 列表的注册表"
                          % os.path.basename(registry))
        return reg, {
            "basis": "authoritative_file",
            "source_basename": os.path.basename(registry),
            "sha256": hashing.sha256_file(registry),
            "nets": len(reg["nets"]),
            "note": "权威注册表文件（只读消费；只记基名与 sha256）",
        }
    if isinstance(registry, dict):
        if not isinstance(registry.get("nets"), list):
            return None, "registry_invalid: 注册表对象缺 nets 列表"
        return registry, {
            "basis": "caller_object",
            "source_basename": None,
            "sha256": hashing.sha256_bytes(
                hashing.canonical_json_bytes(registry)),
            "nets": len(registry["nets"]),
            "note": "调用方直接传入的注册表对象（只记 canonical sha256）",
        }
    return None, "registry_invalid: registry 必须是 None/路径/注册表对象"


# ------------------------------------------------------------------- 镜像

def _copper_bbox(copper) -> "list | None":
    xs, ys = [], []
    for s in copper.get("segments") or []:
        xs += [s["start"][0], s["end"][0]]
        ys += [s["start"][1], s["end"][1]]
    for v in copper.get("vias") or []:
        r = float(v["size"]) / 2.0
        xs += [v["at"][0] - r, v["at"][0] + r]
        ys += [v["at"][1] - r, v["at"][1] + r]
    for z in copper.get("zones") or []:
        for p in z.get("outline_mm") or []:
            xs.append(p[0])
            ys.append(p[1])
    if not xs or not ys:
        return None
    bb = [min(xs), min(ys), max(xs), max(ys)]
    bb = [_q6(v) for v in bb]
    if not (bb[0] < bb[2] and bb[1] < bb[3]):   # 退化 bbox 确定性外扩
        bb = [_q6(bb[0] - 0.5), _q6(bb[1] - 0.5),
              _q6(bb[2] + 0.5), _q6(bb[3] + 0.5)]
    return bb


def _copper_layers(copper) -> list:
    out = []
    for s in copper.get("segments") or []:
        if s["layer"] not in out:
            out.append(s["layer"])
    for v in copper.get("vias") or []:
        for l in v.get("layers") or []:
            if l not in out:
                out.append(l)
    for z in copper.get("zones") or []:
        for l in z.get("layers") or []:
            if l not in out:
                out.append(l)
    return out


def _degraded_inputs(board_path: str, board_text: str, copper: dict,
                     registry: dict, scenario_id: str):
    """KiCad5 只读降级镜像输入：只由铜箔事实构造 (board, ref)。

    仅由 `copper_model` 事实构造（segments/vias/zones），**无 pads、无板框、
    无 relations** —— 这些板级事实在本模块没有解析能力（`geo.parse_board`
    只认 KiCad 6+/10 的 `(footprint …)`），故如实留空并显式上报，绝不编造。
    未映射 net 的对象**不进** ref（同适配层口径）并逐条上报。
    """
    by_name = {}
    for n in registry.get("nets") or []:
        if isinstance(n, dict) and isinstance(n.get("net_name"), str):
            by_name.setdefault(n["net_name"], n.get("net_id"))
    notes = {
        "mirror_mode": MIRROR_MODE_DEGRADED,
        "scenario_id": scenario_id,
        "board_source_sha256": hashing.sha256_text(board_text),
        "copper_sha256": copper.get("copper_sha256"),
        "identity_basis": copper.get("identity_basis"),
        "counts": {"routes": 0, "vias": 0, "zones": 0, "pads": 0,
                   "routes_dropped_unmapped_net": 0,
                   "vias_dropped_unmapped_net": 0,
                   "zones_dropped_unmapped_net": 0},
        "dropped_unmapped_net": [],
        "board_level_gaps": [
            {"item": "adapter_build_inputs", "status": "unavailable",
             "detail": "board_svg_adapter.build_inputs 在本板不可用"
                       "（geo.parse_board 只认 KiCad 6+/10 的 (footprint …)："
                       "KiCad5 用 (module …)）：回落 copper_only_degraded "
                       "镜像（见 mirror_mode）"},
            {"item": "pads", "status": "not_parsed",
             "detail": "降级镜像不产焊盘事实（无 geo 能力）：board.pads 为空"},
            {"item": "board_frame_edge_cuts", "status": "not_parsed",
             "detail": "降级镜像 bbox 取铜箔几何并集，非板框范围"},
            {"item": "board_top_level_layers", "status": "fallback_copper_"
             "declared_layers",
             "detail": "层表取自铜箔自身声明（无适配层板级层表）"},
            {"item": "relations", "status": "not_emitted",
             "detail": "降级镜像不发 relations（需注册表 relations 与焊盘事实）"},
        ],
    }
    endpoints = {}

    def _endpoint(x, y):
        return endpoints.setdefault((_q6(x), _q6(y)), "@%.6f,%.6f" % (x, y))

    routes = []
    for s in sorted(copper.get("segments") or [], key=lambda e: e["key"]):
        nid = by_name.get(s["net"])
        if not nid:
            notes["counts"]["routes_dropped_unmapped_net"] += 1
            notes["dropped_unmapped_net"].append(
                {"kind": "segment", "key": s["key"], "net_name": s["net"]})
            continue
        routes.append({
            "route_id": s["key"], "net_id": nid, "relation_ids": [],
            "line_type": svg_route_package.LINE_TYPES[0], "parent_id": None,
            "layer": s["layer"], "width_mm": s["width"],
            "polyline_mm": [list(s["start"]), list(s["end"])],
            "endpoint_ids": [_endpoint(*s["start"]), _endpoint(*s["end"])],
            "constraint_refs": [], "state": "baseline", "source": "baseline"})
    vias = []
    for v in sorted(copper.get("vias") or [], key=lambda e: e["key"]):
        nid = by_name.get(v["net"])
        if not nid:
            notes["counts"]["vias_dropped_unmapped_net"] += 1
            notes["dropped_unmapped_net"].append(
                {"kind": "via", "key": v["key"], "net_name": v["net"]})
            continue
        ring = max(0.0, _q3((float(v["size"]) - float(v["drill"])) / 2.0))
        vias.append({
            "via_id": v["key"], "net_id": nid, "parent_id": None,
            "from_layer": v["layers"][0], "to_layer": v["layers"][-1],
            "center_mm": list(v["at"]), "drill_mm": v["drill"],
            "annular_ring_mm": ring})
    zones = []
    for z in sorted(copper.get("zones") or [], key=lambda e: e["key"]):
        nid = by_name.get(z["net"])
        if not nid:
            notes["counts"]["zones_dropped_unmapped_net"] += 1
            notes["dropped_unmapped_net"].append(
                {"kind": "zone", "key": z["key"], "net_name": z["net"]})
            continue
        sha = z.get("fill_sha256")
        pts_n = z.get("fill_points")
        zones.append({
            "zone_id": z["key"], "net_id": nid, "layers": list(z["layers"]),
            "outline_kind": "polygon",
            "outline_mm": [list(p) for p in z["outline_mm"]],
            "fill_state": "unknown",
            "fill_sha256": sha if isinstance(sha, str)
            and _SHA256_RE.match(sha) else None,
            "fill_points": pts_n if isinstance(pts_n, int)
            and not isinstance(pts_n, bool) and pts_n >= 0 else None})
    notes["counts"]["routes"] = len(routes)
    notes["counts"]["vias"] = len(vias)
    notes["counts"]["zones"] = len(zones)
    bbox = _copper_bbox(copper) or [0.0, 0.0, 0.5, 0.5]
    board = {
        "scenario_id": scenario_id,
        "board": {
            "bbox_mm": bbox,
            "layers": _copper_layers(copper),
            "source_board_sha256": hashing.sha256_text(board_text),
            "copper_sha256": copper.get("copper_sha256"),
            "identity_basis": copper.get("identity_basis"),
            "bbox_basis": "copper_union_degraded_no_pads",
            "layers_basis": "copper_declared_layers",
        },
        "rules": {},
        "pads": [],
        "relations": [],
        "keepouts": [],
        "adapter_notes": notes,
        "degraded": True,
    }
    ref = {"scenario_id": scenario_id, "routes": routes, "vias": vias,
           "zones": zones}
    return board, ref, notes


def _build_mirror(board_path: str, board_text: str, copper: dict,
                  registry: dict, scenario_id: str):
    """→ (board, ref, mode, notes) 或抛 `CopperLoopError`（降级不适用时）。"""
    try:
        board, ref = board_svg_adapter.build_inputs(
            board_path, registry, scenario_id=scenario_id, copper=copper)
        return board, ref, MIRROR_MODE_ADAPTER, dict(board["adapter_notes"])
    except Exception as exc:
        if copper.get("identity_basis") != copper_model.IDENTITY_GEOMETRIC_FALLBACK:
            raise CopperLoopError(
                "adapter_build_inputs_failed: board_svg_adapter.build_inputs "
                "失败（%s: %s）；本板 identity_basis=%r → 不享 KiCad5 降级"
                "（降级只对 geometric_fallback 开放）"
                % (exc.__class__.__name__, exc, copper.get("identity_basis")))
        board, ref, notes = _degraded_inputs(board_path, board_text, copper,
                                            registry, scenario_id)
        notes["adapter_error"] = {"class": exc.__class__.__name__,
                                  "message": str(exc)}
        return board, ref, MIRROR_MODE_DEGRADED, notes


def mirror_revision(base_board_path: str, out_dir: str, *, registry=None,
                    scenario_id: "str | None" = None,
                    base_label: "str | None" = None) -> dict:
    """只读镜像一轮：分配新 rev-N → 摄取 → 镜像 → 三向校验 → 落盘。

    纯只读于 base 板（`open(..., newline="")`，绝不写回）；只写新 rev 目录。
    返回本轮记录（status = `mirror_only` 或 `blocked`）。
    """
    if not isinstance(base_board_path, str) or not base_board_path:
        raise CopperLoopError("base_board_path: 必须是非空字符串")
    if not isinstance(out_dir, str) or not out_dir:
        raise CopperLoopError("out_dir: 必须是非空字符串")
    started = datetime.now(timezone.utc)
    if not os.path.isfile(base_board_path):
        return _blocked_record(
            ["base_board_missing: 基准板不存在: %s"
             % os.path.basename(base_board_path)], "mirror")
    label = _sanitize_label(
        base_label if isinstance(base_label, str) and base_label
        else os.path.splitext(os.path.basename(base_board_path))[0])
    if scenario_id is None:
        scenario_id = "copper-loop-%s" % label
    if not isinstance(scenario_id, str) or not scenario_id:
        raise CopperLoopError("scenario_id: 必须是非空字符串或 None")

    loop_label_dir = os.path.join(_loop_root(out_dir), label)
    rev, reason = _next_rev(loop_label_dir)
    if reason:
        return _blocked_record([reason], "mirror", base_label=label)
    revision_dir = _rev_dir(out_dir, label, rev)
    revision_id = "%s/rev-%d" % (label, rev)
    try:
        os.makedirs(revision_dir)   # 原子占位：已存在 ⇒ FileExistsError
    except FileExistsError:
        return _blocked_record(
            ["revision_dir_exists: %s 已存在（并发/重复调用）：拒绝覆盖既有"
             "轮次（只追加不覆写）" % revision_id], "mirror",
            base_label=label, rev=rev, revision_id=revision_id)

    text = _read_text(base_board_path)
    board_sha = hashing.sha256_file(base_board_path)
    copper = copper_model.parse_copper(text)
    reg, reg_meta = _resolve_registry(base_board_path, registry, copper)
    if reg is None:
        return _blocked_record([reg_meta], "mirror", revision_dir,
                               base_label=label, rev=rev,
                               revision_id=revision_id)

    # base 只读基准副本（逐字节；adopt 的字节来源与 sha 依据）
    base_name = os.path.basename(base_board_path)
    os.makedirs(os.path.join(revision_dir, "base"), exist_ok=True)
    base_copy = os.path.join(revision_dir, "base", base_name)
    if _write_bytes(base_copy, text.encode(config.ENCODING)) != board_sha:
        return _blocked_record(["base_copy_sha_mismatch: 基准副本 sha 与源板"
                                "不一致（IO 层异常）"], "mirror", revision_dir,
                               base_label=label, rev=rev,
                               revision_id=revision_id)

    baseline = {
        "basename": base_name,
        "sha256": board_sha,
        "bytes": len(text.encode(config.ENCODING)),
        "copy": "base/%s" % base_name,
        "reference": "base/reference.json",
        "read_only": True,
        "eol": "crlf" if "\r\n" in text else "lf",
        "identity_basis": copper["identity_basis"],
        "copper_sha256": copper["copper_sha256"],
        "copper_counts": dict(copper["counts"]),
        "unrepresentable": sorted({u["kind"] for u in
                                   copper["unrepresentable"]}),
    }
    _write_canonical_json(os.path.join(revision_dir, BASELINE_REF_NAME),
                          baseline)

    # 镜像：适配层优先；KiCad5 且适配层不可用时回落只读降级
    try:
        board, ref, mode, notes = _build_mirror(base_board_path, text, copper,
                                               reg, scenario_id)
        svg, manifest = svg_route_package.build(board, ref)
    except CopperLoopError as exc:
        return _blocked_record([str(exc)], "mirror", revision_dir,
                               base_label=label, rev=rev,
                               revision_id=revision_id, base=baseline,
                               registry=reg_meta)
    except Exception as exc:      # 合同违反/形状非法一律 blocked（fail-closed）
        return _blocked_record(
            ["mirror_contract_violation: %s: %s"
             % (exc.__class__.__name__, exc)], "mirror", revision_dir,
            base_label=label, rev=rev, revision_id=revision_id, base=baseline,
            registry=reg_meta)

    net_map = _net_map_from_registry(reg)
    try:
        bind = board_binding.binding_report(text, manifest, net_map)
        consistency = svg_route_package.verify_consistency(svg, manifest,
                                                          snapshot=board)
    except Exception as exc:      # 内部异常按违规（两模块自身已 fail-closed）
        return _blocked_record(
            ["three_way_internal_error: %s: %s" % (exc.__class__.__name__, exc)],
            "mirror", revision_dir, base_label=label, rev=rev,
            revision_id=revision_id, base=baseline, registry=reg_meta)
    total = len(bind["violations"]) + len(consistency)

    os.makedirs(os.path.join(revision_dir, "mirror"), exist_ok=True)
    svg_path = os.path.join(revision_dir, "mirror", "board.svg")
    man_path = os.path.join(revision_dir, "mirror", "route-manifest.json")
    bind_path = os.path.join(revision_dir, "mirror", "binding-report.json")
    three_path = os.path.join(revision_dir, "mirror", "three-way.json")
    svg_sha = _write_text(svg_path, svg)
    man_sha = _write_canonical_json(man_path, manifest)
    _write_canonical_json(bind_path, bind)
    three = {
        "schema": "pcbflow.copper-three-way/1",
        "revision_id": revision_id,
        "mirror_mode": mode,
        "board_binding": {
            "violations": bind["violations"], "pending": bind["pending"],
            "counts": bind["counts"], "info": bind["info"]},
        "svg_manifest": {"violations": consistency},
        "violations_total": total,
        "verdict": "clean" if total == 0 else "violations",
        "net_map_keys": len(net_map),
        "note": "三向：板↔manifest（board_binding）+ manifest↔SVG"
                "（verify_consistency，snapshot=board 强制 hash 绑定）；"
                "任一非空即 blocked",
    }
    _write_canonical_json(three_path, three)
    artifacts = {
        "base": baseline["copy"],
        "reference": "base/reference.json",
        "svg": "mirror/board.svg",
        "manifest": "mirror/route-manifest.json",
        "binding_report": "mirror/binding-report.json",
        "three_way": "mirror/three-way.json",
        "adapter_report": None,
        "patch_set": None,
        "staging": None,
        "drc_request": None,
        "accept_record": None,
        "adopt_record": None,
        "ledger": LEDGER_NAME,
    }
    if mode == MIRROR_MODE_ADAPTER:
        ad_path = os.path.join(revision_dir, "mirror", "adapter-report.json")
        _write_canonical_json(ad_path, notes)
        artifacts["adapter_report"] = "mirror/adapter-report.json"

    status = STATUS_MIRROR_ONLY if total == 0 else STATUS_BLOCKED
    record = {
        "schema": SCHEMA,
        "revision_id": revision_id,
        "base_label": label,
        "rev": rev,
        "status": status,
        "verdict": status,
        "stage": "mirror",
        "blocked_at": None if total == 0 else "mirror",
        "ok": total == 0,
        "usable": False,
        "persisted": True,
        "reasons": [] if total == 0 else [
            "three_way_violations: 板↔manifest %d 条 + manifest↔SVG %d 条"
            "（任一非空即 blocked，禁止在未核实事实的镜像上打补丁）"
            % (len(bind["violations"]), len(consistency))],
        "scenario_id": scenario_id,
        "base": baseline,
        "registry": reg_meta,
        "mirror": {
            "mode": mode,
            "degraded": mode == MIRROR_MODE_DEGRADED,
            "svg": "mirror/board.svg", "svg_sha256": svg_sha,
            "manifest": "mirror/route-manifest.json",
            "manifest_sha256": man_sha,
            "manifest_payload_sha256": manifest.get("manifest_payload_sha256"),
            "board_snapshot_sha256": manifest.get("board_snapshot_sha256"),
            "zones_facts_sha256": manifest.get("zones_facts_sha256"),
            "counts": {"routes": len(manifest["routes"]),
                       "vias": len(manifest["vias"]),
                       "zones": len(manifest["zones"]),
                       "pads": len(board["pads"])},
            "notes": ([] if mode == MIRROR_MODE_ADAPTER else
                      ["copper_only_degraded: 适配层不可用（见 three-way 的 "
                       "mirror_mode 与 mirror/adapter-report.json 的 "
                       "board_level_gaps）"]),
        },
        "three_way": {"violations_total": total,
                      "verdict": three["verdict"],
                      "board_binding_violations": bind["violations"],
                      "svg_manifest_violations": consistency,
                      "pending": bind["pending"]},
        "patch": None,
        "drc_request": None,
        "drc_decision": None,
        "adopted": False,
        "rollback": "none",
        "staging_removed": None,
        "artifacts": artifacts,
        "transaction": lease.open_transaction(
            "TXN-%s-rev%d" % (label, rev), label, board_sha,
            {"rows": 0, "segments": 0, "vias": 0, "footprints": 0}),
    }
    _write_canonical_json(os.path.join(revision_dir, LEDGER_NAME), {
        "schema": LEDGER_SCHEMA,
        "revision_id": revision_id,
        "patch_ledger": None,
        "events": [{"seq": 0, "event": "mirror_written",
                    "status": status, "mirror_mode": mode,
                    "svg_sha256": svg_sha, "manifest_sha256": man_sha,
                    "board_binding_violations": len(bind["violations"]),
                    "svg_manifest_violations": len(consistency),
                    "record_core_fact_sha256": None}],
    })
    _finalize(record)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    record["evaluation_metadata"] = _evaluation_metadata(
        revision_dir, elapsed, _resolved_paths(revision_dir, record))
    _finalize(record)
    _write_canonical_json(os.path.join(revision_dir, RECORD_NAME), record)
    return record


# --------------------------------------------------------------- DRC 请求

def _drc_command(board_rel: str, report_rel: str) -> str:
    return ("kicad-cli pcb drc --format json --output %s --severity-error "
            "--refill-zones %s" % (report_rel.replace(os.sep, "/"),
                                   board_rel.replace(os.sep, "/")))


def _resolved_paths(revision_dir, record) -> dict:
    """绝对路径视图（只进 evaluation_metadata，不进 core hash）。"""
    out = {}
    if revision_dir:
        out["revision_dir"] = os.path.abspath(revision_dir)
        staging = (record.get("patch") or {}).get("staging")
        if staging:
            out["staging_board"] = os.path.abspath(
                os.path.join(revision_dir, staging))
            out["staging_board_kicad_cli_command"] = (
                "kicad-cli pcb drc --format json --output %s --severity-error "
                "--refill-zones %s" % (
                    os.path.abspath(os.path.join(revision_dir, STAGING_REPORT_REL)),
                    os.path.abspath(os.path.join(revision_dir, staging))))
        base = (record.get("base") or {}).get("copy")
        if base:
            out["baseline_board"] = os.path.abspath(
                os.path.join(revision_dir, base))
            out["baseline_report"] = os.path.abspath(
                os.path.join(revision_dir, BASELINE_REPORT_REL))
        out["staging_report"] = os.path.abspath(
            os.path.join(revision_dir, STAGING_REPORT_REL))
    lock = _toolchain_lock()
    if lock:
        out["toolchain_lock"] = os.path.abspath(config.PCBFLOW_ROOT)
    return out


def _toolchain_lock():
    """toolchain_lock.json（只读；含 kicad-cli 版本权威）。"""
    path = os.path.join(config.PCBFLOW_ROOT, "toolchain_lock.json")
    if not os.path.isfile(path):
        return None
    try:
        obj = _read_json(path)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _sanitize_patch_set(patch_set) -> "tuple[dict | None, str | None]":
    """补丁集 canonical 化（白名单键；绝对路径即拒绝 —— 核心产物禁宿主路径）。"""
    if not isinstance(patch_set, dict):
        return None, "patch_set_invalid: patch_set 必须是对象"
    ops = patch_set.get("ops")
    if not isinstance(ops, list):
        return None, "patch_set_invalid: patch_set.ops 必须是列表"
    if _has_abs_path(patch_set):
        return None, ("patch_set_absolute_path_forbidden: 补丁集含宿主绝对路径"
                      "（核心产物禁主机路径；请改用基名/相对路径）")
    out = {"schema": PATCH_SET_SCHEMA, "ops": list(ops)}
    for key in ("patch_set_id", "note"):
        v = patch_set.get(key)
        if isinstance(v, str) and v:
            out[key] = v
    if patch_set.get("baseline_drc_report"):
        out["baseline_drc_declared"] = True
        out["baseline_drc_basename"] = os.path.basename(
            str(patch_set["baseline_drc_report"]))
    return out, None


def patch_revision(revision_dir: str, patch_set) -> dict:
    """在既有镜像轮次上应用补丁 → staging + DRC 请求（不执行 DRC）。

    KiCad5（identity_basis = geometric_fallback）**一律**拒绝：
    reason = `edit_unsupported_identity_basis`（镜像仍可用）。
    """
    started = datetime.now(timezone.utc)
    record, reason = _load_record(revision_dir)
    if reason:
        return _blocked_record([reason], "patch")
    status = record.get("status")
    basis = (record.get("base") or {}).get("identity_basis")
    if basis == copper_model.IDENTITY_GEOMETRIC_FALLBACK:
        return _refuse(record, revision_dir, "patch", [
            "%s: 板 identity_basis=%r（KiCad5 语料无 kicad_uuid，身份为几何"
            "回退）：本阶段不支持在该身份口径上寻址改板（镜像已可用，编辑须"
            "人工另走通道）" % (REASON_EDIT_UNSUPPORTED_IDENTITY, basis)])
    if status != STATUS_MIRROR_ONLY:
        return _refuse(record, revision_dir, "patch", [
            "patch_not_allowed_in_status: 当前 status=%r（补丁只允许在 "
            "mirror_only 上应用一次；accepted/rejected/rolled_back 轮次不得"
            "再改）" % status])
    clean, reason_ret = _sanitize_patch_set(patch_set)
    if clean is None:
        return _refuse(record, revision_dir, "patch", [reason_ret])

    base_copy = os.path.join(revision_dir, (record["base"])["copy"])
    if not os.path.isfile(base_copy):
        return _fail_patch(record, revision_dir,
                           ["base_copy_missing: 基准副本缺失（版本目录被外部"
                            "改动）"], integrity=True)
    text = _read_text(base_copy)
    if hashing.sha256_text(text) != record["base"]["sha256"]:
        return _fail_patch(record, revision_dir,
                           ["base_copy_sha_mismatch: 基准副本 sha 与 "
                            "reference.json 不符（版本目录被外部改动）"],
                           integrity=True)

    result = copper_patch.apply_patch(text, clean["ops"], eol=None)
    clean["ops_total"] = len(clean["ops"])
    _write_canonical_json(os.path.join(revision_dir, PATCH_SET_NAME), clean)
    _set_patch_ledger(revision_dir, result["ledger"])
    ledger_counts = {
        "ops_total": result["ledger"].get("ops_total"),
        "ops_applied": result["ledger"].get("ops_applied"),
        "blocked_ops": result["ledger"].get("blocked_ops"),
    }
    if not result["ok"]:
        # 补丁被拒 ⇒ **不改**轮次状态（仍 mirror_only）：修好补丁集可在同一
        # 轮次重试；拒绝事实进台账（含 apply_patch 的完整 ledger）。
        return _refuse(record, revision_dir, "patch", list(result["reasons"]),
                       patch_set=PATCH_SET_NAME,
                       patch={"verdict": "blocked",
                              "reasons": list(result["reasons"]),
                              "ledger_counts": ledger_counts,
                              "staging": None, "staging_sha256": None})

    guard = (result["ledger"] or {}).get("structural_guard") or {}
    if guard.get("ok") is not True:
        return _refuse(record, revision_dir, "patch",
                       ["structural_guard_failed: 结构守卫未通过"
                        "（fail-closed，禁止落 staging）"],
                       patch_set=PATCH_SET_NAME,
                       patch={"verdict": "blocked",
                              "reasons": ["structural_guard_failed"],
                              "ledger_counts": ledger_counts,
                              "staging": None, "staging_sha256": None})

    patched_name = (record["base"])["basename"]
    os.makedirs(os.path.join(revision_dir, "patched"), exist_ok=True)
    staging_path = os.path.join(revision_dir, "patched", patched_name)
    if os.path.exists(staging_path):     # 只追加不覆写
        return _fail_patch(record, revision_dir,
                           ["staging_exists: %s 已存在（重复补丁）：拒绝覆盖"
                            % _rel(revision_dir, staging_path)])
    staging_sha = _write_text(staging_path, result["board_text"])
    if staging_sha != hashing.sha256_text(result["board_text"]):
        return _fail_patch(record, revision_dir,
                           ["staging_sha_mismatch: staging 落盘 sha 与内存"
                            "结果不一致（IO 层异常）"])
    _write_canonical_json(os.path.join(revision_dir, PATCH_SET_NAME), clean)

    patch_info = {
        "verdict": "accepted",
        "patch_set": PATCH_SET_NAME,
        "patch_set_sha256": hashing.sha256_file(
            os.path.join(revision_dir, PATCH_SET_NAME)),
        "ops_total": result["ledger"]["ops_total"],
        "ops_applied": result["ledger"]["ops_applied"],
        "adds": result["ledger"]["adds"],
        "modifies": result["ledger"]["modifies"],
        "deletes": result["ledger"]["deletes"],
        "eol": result["ledger"]["eol"],
        "structural_guard_ok": True,
        "unchanged_bytes_outside_targets":
            result["ledger"]["unchanged_bytes_outside_targets"],
        "affected_keys": result["ledger"]["affected_keys"],
        "counts_before": result["ledger"]["counts_before"],
        "counts_after": result["ledger"]["counts_after"],
        "staging": _rel(revision_dir, staging_path),
        "staging_sha256": staging_sha,
        "reasons": [],
    }
    request = {
        "schema": DRC_REQUEST_SCHEMA,
        "revision_id": record["revision_id"],
        "toolchain": {
            "kicad_cli_version": ((_toolchain_lock() or {}).get(
                "kicad_cli") or {}).get("version"),
            "source": "toolchain_lock.json",
        },
        "severity_scope": ["error"],
        "refill_zones": True,
        "rule": DRC_GATE_RULE,
        "requests": [
            {"request_id": "staging",
             "board": patch_info["staging"],
             "board_sha256": staging_sha,
             "report_path": STAGING_REPORT_REL.replace(os.sep, "/"),
             "kicad_cli_command": _drc_command(patch_info["staging"],
                                               STAGING_REPORT_REL)},
            {"request_id": "baseline",
             "board": record["base"]["copy"],
             "board_sha256": record["base"]["sha256"],
             "report_path": BASELINE_REPORT_REL.replace(os.sep, "/"),
             "kicad_cli_command": _drc_command(record["base"]["copy"],
                                               BASELINE_REPORT_REL)},
        ],
        "note": "pcbflow 零子进程：DRC 由编排侧执行（相对路径以 revision dir "
                "为基准；等价的绝对路径形式与命令见 "
                "evaluation_metadata.resolved_paths）。报告需 severity=error、"
                "含 kicad_version 与 violations 列表，accept 阶段逐项校验。",
    }
    os.makedirs(os.path.join(revision_dir, "drc"), exist_ok=True)
    _write_canonical_json(os.path.join(revision_dir, REQUEST_NAME), request)

    rec = dict(record)
    rec.update({
        "status": STATUS_AWAITING_DRC,
        "verdict": STATUS_AWAITING_DRC,
        "stage": "drc",
        "blocked_at": None,
        "ok": True,
        "usable": False,
        "reasons": [],
        "patch": patch_info,
        "drc_request": request,
        "rollback": "armed",
    })
    rec["artifacts"] = dict(record["artifacts"])
    rec["artifacts"].update({"patch_set": PATCH_SET_NAME,
                             "staging": patch_info["staging"],
                             "drc_request": REQUEST_NAME.replace(os.sep, "/")})
    txn = dict(record["transaction"])
    # 按 kind 精确记账（segments/vias 分列；rows/footprints 本阶段不写）
    seg_ops = sum(1 for o in clean["ops"] if isinstance(o, dict)
                  and o.get("kind") == "segment")
    via_ops = sum(1 for o in clean["ops"] if isinstance(o, dict)
                  and o.get("kind") == "via")
    txn["write_scope"] = {"rows": 0, "segments": seg_ops, "vias": via_ops,
                          "footprints": 0}
    lease.stage_batch(txn, "rev-%d" % record["rev"], staging_sha,
                      "not_executed")
    rec["transaction"] = txn
    rec["patch"]["kind_counts"] = {"segments": seg_ops, "vias": via_ops}
    _set_patch_ledger(revision_dir, result["ledger"])
    _append_event(revision_dir, record, "staging_written",
                  status=STATUS_AWAITING_DRC,
                  staging=patch_info["staging"],
                  staging_sha256=staging_sha,
                  ops_total=patch_info["ops_total"],
                  ops_applied=patch_info["ops_applied"],
                  structural_guard_ok=True)
    return _finalize_and_save(rec, revision_dir, started)


def _fail_patch(record, revision_dir, reasons, patch_ledger=None,
                integrity=False) -> dict:
    """补丁阶段失败：status=blocked（blocked_at=patch），不产 staging。"""
    rec = dict(record)
    rec.update({
        "status": STATUS_BLOCKED,
        "verdict": STATUS_BLOCKED,
        "stage": "patch",
        "blocked_at": "patch",
        "ok": False,
        "usable": False,
        "reasons": list(reasons),
        "patch": {"verdict": "blocked", "reasons": list(reasons),
                  "staging": None, "staging_sha256": None,
                  "structural_guard_ok": None,
                  "integrity_failure": bool(integrity)},
        "rollback": "none",
    })
    if patch_ledger is not None:
        _set_patch_ledger(revision_dir, patch_ledger)
        rec["patch"]["ledger_counts"] = {
            "ops_total": patch_ledger.get("ops_total"),
            "ops_applied": patch_ledger.get("ops_applied"),
            "blocked_ops": patch_ledger.get("blocked_ops")}
    _append_event(revision_dir, record, "patch_blocked",
                  status=STATUS_BLOCKED, reasons=list(reasons))
    return _finalize_and_save(rec, revision_dir, None)


def _finalize_and_save(record: dict, revision_dir: str, started) -> dict:
    elapsed = None if started is None else (
        datetime.now(timezone.utc) - started).total_seconds()
    record["evaluation_metadata"] = _evaluation_metadata(
        revision_dir, elapsed, _resolved_paths(revision_dir, record))
    _finalize(record)
    _write_canonical_json(os.path.join(revision_dir, RECORD_NAME), record)
    return record


def revision(base_board_path: str, patch_set, out_dir: str, *, registry=None,
             scenario_id: "str | None" = None,
             base_label: "str | None" = None) -> dict:
    """一轮完整回路：镜像 → 三向校验 → 补丁 → staging → DRC 请求。

    `patch_set=None` ⇒ 只做镜像（status `mirror_only`）；否则在镜像干净的
    轮次上继续补丁阶段。返回本轮记录（`awaiting_drc` / `mirror_only` /
    `blocked`）。
    """
    if not isinstance(out_dir, str) or not out_dir:
        raise CopperLoopError("out_dir: 必须是非空字符串")
    rec = mirror_revision(base_board_path, out_dir, registry=registry,
                          scenario_id=scenario_id, base_label=base_label)
    if patch_set is None or rec.get("status") != STATUS_MIRROR_ONLY:
        return rec
    label = rec["base_label"]
    return patch_revision(_rev_dir(out_dir, label, rec["rev"]), patch_set)


# ------------------------------------------------------------------- accept

def _violation_keyset(report, key: str) -> list:
    """DRC 报告条目 → 归一 keyset（保序去重前的稳定排序列表，保留重数）。"""
    entries = report.get(key)
    if not isinstance(entries, list):
        return []
    out = []
    for e in entries:
        if not isinstance(e, dict):
            out.append(hashing.sha256_text(json.dumps(e, sort_keys=True,
                                                      default=str)))
            continue
        items = e.get("items")
        proj = {
            "type": e.get("type"), "severity": e.get("severity"),
            "description": e.get("description"),
            "items": [{"description": it.get("description"),
                       "pos": it.get("pos"), "uuid": it.get("uuid")}
                      for it in items] if isinstance(items, list) else items,
        }
        out.append(hashing.sha256_bytes(hashing.canonical_json_bytes(proj)))
    return sorted(out)


def _validate_drc_report(report, expected_source: str, lock) -> list:
    """DRC 报告结构与工具链校验（fail-closed，逐条给出 reason）。"""
    errs = []
    if not isinstance(report, dict):
        return ["drc_report_structure_invalid: 报告不是对象"]
    schema = report.get("$schema")
    if not isinstance(schema, str) or "drc" not in schema.lower():
        errs.append("drc_report_structure_invalid: 缺 $schema（或非 DRC 报告）")
    if not isinstance(report.get("violations"), list):
        errs.append("drc_report_structure_invalid: violations 必须存在且为列表")
    ver = report.get("kicad_version")
    if not isinstance(ver, str) or not ver:
        errs.append("drc_report_structure_invalid: 缺 kicad_version")
    for i, e in enumerate(report.get("violations") or []):
        if not isinstance(e, dict) or not isinstance(e.get("type"), str):
            errs.append("drc_report_structure_invalid: violations[%d] 缺 type"
                        % i)
            break
    src = report.get("source")
    if isinstance(src, str) and src:
        if os.path.basename(src) != expected_source:
            errs.append("drc_report_source_mismatch: 报告 source=%r 与 staging "
                        "板 %r 不符（疑似别的板/过期报告）"
                        % (os.path.basename(src), expected_source))
    else:
        # 板绑定证据缺失即拒（REPAIR-P2 W-3 / SEC-A-03）：source 键缺失/
        # 非字符串/空 ⇒ 报告无法绑定本轮 staging 板，与 toolchain_lock_missing
        # 同口径（缺证据 ≠ 通过），不得静默跳过绑定检查。
        errs.append("drc_report_source_missing: DRC 报告缺 source 键（或非"
                    "字符串/空）⇒ 无法绑定本轮 staging 板 %r（缺绑定证据"
                    "即拒绝）" % expected_source)
    if lock is None:
        errs.append("toolchain_lock_missing: toolchain_lock.json 不可读："
                    "无版本权威即不得判 accept")
    else:
        want = (lock.get("kicad_cli") or {}).get("version")
        if not want:
            errs.append("toolchain_lock_invalid: toolchain_lock.json 无 "
                        "kicad_cli.version")
        elif isinstance(ver, str) and ver and ver != want:
            errs.append("kicad_version_mismatch: 报告 kicad_version=%r 与 "
                        "toolchain_lock.json=%r 不符（工具链漂移：DRC 结果"
                        "不可比，禁止 accept）" % (ver, want))
    return errs


def _fill_gate_refusal(record: dict, revision_dir: str, stage: str,
                       source_sha256: "str | None" = None):
    """P3b zone 填充门（"未重填不得采纳"）→ 拒绝结果 or None（放行）。

    判据在 `copper_patch.fill_gate`（纯函数）：本轮 zone 编辑使**被触及的**
    zone 填充非 fresh（stale / 无填充）⇒ 必须已有 `refill_evidence`
    （`drc/refill-evidence.json` 或记录内联），且其 `source_board_sha256`
    必须绑定本轮 staging 板。未触及 zone 的轮次一律放行。

    状态机纪律：一律走 `_refuse` —— 拒绝的是**本次 accept/adopt 尝试**，
    轮次记录不改（仍 `awaiting_drc` / `accepted`），补齐 `drc/refill-evidence.json`
    后可重试；返回结果的 `fill_gate.status_label == "awaiting_refill"` 是这次
    尝试的判定标签（不是把轮次写死成 blocked）。
    """
    led, led_reason = _load_ledger(revision_dir)
    if led is None:
        # 台账在 awaiting_drc 轮次里必存在（patch 阶段写入）；不可解析 ⇒
        # 无法核实填充门 ⇒ fail-closed 拒绝本次判定尝试（不改轮次记录）。
        # 注意：台账不可用时 `_refuse` 也写不了事件（`_append_event` 会抛），
        # 故这里直接构造拒绝结果（**不**触碰台账，也不静默重建它）。
        res = {
            "schema": SCHEMA,
            "revision_id": record.get("revision_id"),
            "base_label": record.get("base_label"),
            "rev": record.get("rev"),
            "status": STATUS_BLOCKED,
            "verdict": STATUS_BLOCKED,
            "stage": stage,
            "blocked_at": stage,
            "ok": False,
            "usable": False,
            "persisted": False,
            "revision_status": record.get("status"),
            "revision_core_fact_sha256": record.get("core_fact_sha256"),
            "reasons": [
                "fill_gate_ledger_unavailable: %s（无法核实 zone 填充门 ⇒ "
                "拒绝本次 %s 尝试，轮次记录不变；台账不可用故本次拒绝也未能"
                "落事件，不静默重建台账）" % (led_reason, stage)],
            "ledger_available": False,
        }
        res["evaluation_metadata"] = _evaluation_metadata(
            revision_dir, None, _resolved_paths(revision_dir, record))
        return _finalize(res)
    gate = copper_patch.fill_gate(record, ledger=led,
                                  revision_dir=revision_dir,
                                  source_sha256=source_sha256)
    if gate["ok"]:
        return None
    return _refuse(record, revision_dir, stage, gate["reasons"], fill_gate=gate)


def accept_revision(revision_dir: str, drc_report_path: str) -> dict:
    """读编排侧产出的 DRC 报告 → accepted / rejected（保守、显式）。

    规则（全部显式记账）：
    1. 记录/状态：记录缺失或 status ≠ awaiting_drc ⇒ blocked；
    2. 报告：缺失 ⇒ blocked；不可解析 ⇒ blocked；结构不符（非 DRC 报告、
       缺 violations/kicad_version/source、条目缺 type）⇒ blocked；报告
       source 基名与 staging 板不符 ⇒ blocked（防拿错板/过期报告；缺
       source ⇒ 同判 blocked——REPAIR-P2 W-3 / SEC-A-03）；
    3. 工具链：kicad_version 与 `toolchain_lock.json.kicad_cli.version` 不符
       ⇒ blocked；
    4. 基线：`drc/baseline.json` 存在且合法 ⇒ 按 keyset 比对；缺失/非法 ⇒
       保守视"无基线"（任何 violation 都算新增），并如实记账；
    5. 有**新增** violation ⇒ rejected（staging 保留供排查，但 `usable=false`，
       绝不产生可用产物）；无新增 ⇒ accepted。

    状态机纪律（两类 blocked 的落盘语义不同，显式区分）：
    - **拒绝尝试**（状态不符 / 报告缺失 / 不可解析 / 结构不符 / 工具链版本
      不符 / 报告复制冲突 / **zone 填充门未过**）：走 `_refuse` —— 轮次记录
      **不改**（仍 `awaiting_drc`），只在台账追加 `accept_refused` 事件；补齐
      报告（或 `drc/refill-evidence.json`）后可重试。
      "报告还没生成"不是轮次的终局事实，把它写成轮次 blocked 会让一轮
      永久不可判定（`_refuse` docstring 的同一纪律）。
    - **轮次完整性失败**（staging 缺失 / staging sha 与记账不符）：轮次自身产物
      已不可信 ⇒ 如实把该轮次写成 `blocked`（fail-closed）。
    - accepted / rejected 是**判定结果**，一律落盘进轮次记录。
    """
    started = datetime.now(timezone.utc)
    record, reason = _load_record(revision_dir)
    if reason:
        return _blocked_record([reason], "accept")
    if record.get("status") != STATUS_AWAITING_DRC:
        return _refuse(record, revision_dir, "accept", [
            "accept_requires_awaiting_drc: 当前 status=%r（只有 awaiting_drc"
            " 轮次可接受 DRC 判定；本拒绝不改轮次记录）" % record.get("status")])

    # P3b zone 填充门：含"填充过期/无填充"的 zone 编辑必须已记录重填证据
    refusal = _fill_gate_refusal(record, revision_dir, "accept")
    if refusal is not None:
        return refusal

    staging_rel = (record.get("patch") or {}).get("staging")
    staging_sha = (record.get("patch") or {}).get("staging_sha256")
    staging_path = os.path.join(revision_dir, staging_rel) if staging_rel \
        else None
    if not staging_path or not os.path.isfile(staging_path):
        return _finalize_and_save(_blocked_rec(record,
            ["staging_missing: staging 板不存在（版本目录被外部改动）"]),
            revision_dir, started)
    if hashing.sha256_file(staging_path) != staging_sha:
        return _finalize_and_save(_blocked_rec(record,
            ["staging_sha_mismatch: staging 板 sha 与记账不符（落盘后被改动）"]),
            revision_dir, started)

    rp = drc_report_path
    if not isinstance(rp, str) or not rp:
        raise CopperLoopError("drc_report_path: 必须是非空字符串")
    cands = [rp]
    if not os.path.isabs(rp):
        cands.append(os.path.join(revision_dir, "drc", os.path.basename(rp)))
    found = next((p for p in cands if os.path.isfile(p)), None)
    if found is None:
        return _refuse(record, revision_dir, "accept", [
            "drc_report_missing: 报告不存在（依次尝试 %s）—— 拒绝的是本次"
            "判定尝试，轮次仍为 awaiting_drc（补齐报告后可重试）"
            % ", ".join(os.path.basename(p) for p in cands)])
    try:
        report = _read_json(found)
    except Exception as exc:
        return _refuse(record, revision_dir, "accept", [
            "drc_report_unparseable: %s（%s: %s）"
            % (os.path.basename(found), exc.__class__.__name__, exc)])

    lock = _toolchain_lock()
    errs = _validate_drc_report(report, os.path.basename(staging_path), lock)
    if errs:
        return _refuse(record, revision_dir, "accept", errs)

    base_report_path = os.path.join(revision_dir, BASELINE_REPORT_REL)
    baseline_report, baseline_note = None, None
    if os.path.isfile(base_report_path):
        try:
            br = _read_json(base_report_path)
        except Exception as exc:
            br = None
            baseline_note = ("baseline_unparseable: %s（%s: %s）—— 保守按"
                             "『无基线』处理" % (os.path.basename(
                                 base_report_path), exc.__class__.__name__, exc))
        if br is not None:
            berr = _validate_drc_report(br, os.path.basename(
                os.path.join(revision_dir, record["base"]["copy"])), lock)
            if berr:
                baseline_note = ("baseline_invalid: %s —— 保守按『无基线』处理"
                                 % "; ".join(berr))
            else:
                baseline_report = br
    else:
        baseline_note = "baseline_missing: drc/baseline.json 不存在 —— 保守按『无基线』处理"

    viol = _violation_keyset(report, "violations")
    unc = _violation_keyset(report, "unconnected_items")
    if baseline_report is None:
        new_viol = list(viol)
        new_unc = list(unc)
        baseline_used = False
    else:
        bv = collections.Counter(_violation_keyset(baseline_report, "violations"))
        bu = collections.Counter(_violation_keyset(baseline_report,
                                                  "unconnected_items"))
        new_viol = list((collections.Counter(viol) - bv).elements())
        new_unc = list((collections.Counter(unc) - bu).elements())
        baseline_used = True

    verdict = STATUS_ACCEPTED if not new_viol else STATUS_REJECTED
    accept_record = {
        "schema": ACCEPT_SCHEMA,
        "revision_id": record.get("revision_id"),
        "verdict": verdict,
        "rule": DRC_GATE_RULE,
        "drc_report_basename": os.path.basename(found),
        "drc_report_sha256": hashing.sha256_file(found),
        "drc_report_copied_to": None,
        "kicad_version": report.get("kicad_version"),
        "toolchain_lock_version": ((lock or {}).get("kicad_cli")
                                  or {}).get("version"),
        "severity_scope": report.get("included_severities"),
        "staging": staging_rel, "staging_sha256": staging_sha,
        "baseline_used": baseline_used,
        "baseline_note": baseline_note,
        "baseline_report_basename": os.path.basename(base_report_path)
        if os.path.isfile(base_report_path) else None,
        "violations_total": len(viol),
        "violations_new": len(new_viol),
        "violations_new_keys": new_viol,
        "unconnected_total": len(unc),
        "unconnected_new": len(new_unc),
        "unconnected_is_not_a_gate_criterion": True,
        "note": "unconnected_items 与 ASM-4 同口径：如实记账但不作 gate 判据"
                "（gate 只看新增 violation）",
        "decided_reason": ("无新增 violation" if verdict == STATUS_ACCEPTED
                           else "新增 %d 条 violation（对基线 keyset）"
                                % len(new_viol)),
    }
    # 报告留档：外部报告复制进版本目录（版本目录外的报告不写绝对路径）
    if os.path.dirname(os.path.abspath(found)) != os.path.abspath(
            os.path.join(revision_dir, "drc")):
        dst = os.path.join(revision_dir, "drc",
                           "received-%s" % os.path.basename(found))
        if os.path.exists(dst) and hashing.sha256_file(dst) != \
                hashing.sha256_file(found):
            return _refuse(record, revision_dir, "accept", [
                "drc_report_copy_conflict: drc/received-%s 已存在且内容不同"
                "（只追加不覆写）" % os.path.basename(found)])
        if not os.path.exists(dst):
            _write_bytes(dst, open(found, "rb").read())
        accept_record["drc_report_copied_to"] = _rel(revision_dir, dst)
    _write_canonical_json(os.path.join(revision_dir, ACCEPT_NAME),
                          accept_record)

    rec = dict(record)
    rec["drc_decision"] = {
        "verdict": verdict,
        "accept_record": ACCEPT_NAME.replace(os.sep, "/"),
        "violations_new": len(new_viol),
        "violations_total": len(viol),
        "baseline_used": baseline_used,
        "kicad_version": report.get("kicad_version"),
    }
    rec["artifacts"] = dict(record["artifacts"])
    rec["artifacts"]["accept_record"] = ACCEPT_NAME.replace(os.sep, "/")
    txn = dict(record["transaction"])
    txn["batches"] = [dict(b) for b in txn["batches"]]
    for b in txn["batches"]:
        if b["batch_id"] == "rev-%d" % record["rev"]:
            b["drc_batch_status"] = "pass" if verdict == STATUS_ACCEPTED \
                else "fail"
    if verdict == STATUS_ACCEPTED:
        txn["rollback"] = "none"          # 判定通过 → 解除回滚武装
        lease.commit_transaction(txn, staging_sha)
        rec.update({"status": STATUS_ACCEPTED, "verdict": STATUS_ACCEPTED,
                    "ok": True, "usable": True, "reasons": [],
                    "rollback": "none"})
    else:
        lease.rollback_transaction(
            txn, "DRC 新增 %d 条 violation（对基线 keyset）" % len(new_viol))
        rec.update({
            "status": STATUS_REJECTED, "verdict": STATUS_REJECTED, "ok": False,
            "usable": False, "rollback": "executed",
            "reasons": ["drc_new_violations: 新增 %d 条 violation（对基线 "
                        "keyset）：整轮 rejected（staging 保留供排查，"
                        "不得 adopt）" % len(new_viol)],
            "staging_removed": None})
    rec["transaction"] = txn
    _append_event(revision_dir, record, "drc_%s" % verdict,
                  status=verdict,
                  drc_report=accept_record["drc_report_basename"],
                  drc_report_sha256=accept_record["drc_report_sha256"],
                  violations_total=len(viol), violations_new=len(new_viol),
                  baseline_used=baseline_used)
    return _finalize_and_save(rec, revision_dir, started)


def _blocked_rec(record, reasons, stage=None, **fields) -> dict:
    """既有记录上的"再判 blocked"（保留事实，改状态与原因）。"""
    rec = dict(record)
    rec.update({"status": STATUS_BLOCKED, "verdict": STATUS_BLOCKED,
                "ok": False, "usable": False, "reasons": list(reasons)})
    if stage is not None:
        rec.update({"stage": stage, "blocked_at": stage})
    rec.update(fields)
    return rec


# ----------------------------------------------------------------- rollback

def rollback_revision(revision_dir: str) -> dict:
    """回滚一轮：撤销可用性并（在 staging 完整时）移除 staging。

    `rollback ∈ none|armed|executed|failed`（与 lease 事务同枚举）：
    - `executed`：撤销完成（staging 校验一致并被移除，或本轮从未产出 staging）；
    - `failed`：staging 存在但 sha 与记账不符 —— **不**删除（防破坏不可复现的
      证据），如实标 failed；
    - 已 adopt 的轮次拒绝自动回滚（设计侧已变更，须人工复核）；
    - 幂等：已回滚的轮次再调用 ⇒ verdict=noop、rollback 保持 executed。

    状态机纪律：`rollback_after_adopt_not_supported` /
    `rollback_after_commit_not_supported` 是**拒绝尝试**（走 `_refuse`，不改
    轮次记录：accepted/adopted 轮次不会被一次失败的 rollback 变成 blocked）；
    只有 `rollback=failed`（staging sha 与记账不符 ⇒ 拒绝删除证据）与
    `rollback=executed` 是本轮的真实落盘状态。
    """
    started = datetime.now(timezone.utc)
    record, reason = _load_record(revision_dir)
    if reason:
        return _blocked_record([reason], "rollback")
    if record.get("status") == STATUS_ROLLED_BACK:
        rec = dict(record)
        rec.update({"ok": True, "verdict": "noop", "stage": "rollback"})
        return _finalize_and_save(rec, revision_dir, started)
    if record.get("adopted"):
        return _refuse(record, revision_dir, "rollback", [
            "rollback_after_adopt_not_supported: 本轮已 adopt（设计侧已变更）"
            "：自动回滚会破坏已采纳产物，须人工对账处置（本拒绝不改轮次记录）"])
    if (record.get("transaction") or {}).get("final_board_sha256") is not None:
        # accepted ⇒ 事务已 commit（DRC 判定通过）：lease 合同禁止回滚已提交事务
        return _refuse(record, revision_dir, "rollback", [
            "rollback_after_commit_not_supported: 本轮已 accept（事务已 commit，"
            "rollback=none）：撤销须走新轮次（本命令不回滚已提交事务，"
            "本拒绝不改轮次记录）"])

    rec = dict(record)
    txn = dict(record["transaction"])
    txn["batches"] = [dict(b) for b in txn["batches"]]
    staging_rel = (record.get("patch") or {}).get("staging")
    staging_sha = (record.get("patch") or {}).get("staging_sha256")
    removed = None
    if staging_rel:
        path = os.path.join(revision_dir, staging_rel)
        if os.path.isfile(path):
            actual = hashing.sha256_file(path)
            if actual != staging_sha:
                rec.update({
                    "status": STATUS_BLOCKED, "verdict": STATUS_BLOCKED,
                    "ok": False, "usable": False, "stage": "rollback",
                    "rollback": "failed",
                    "reasons": ["staging_sha_mismatch: %s sha 与记账不符："
                                "拒绝删除（证据完整性优先），标 rollback="
                                "failed" % staging_rel]})
                _append_event(revision_dir, record, "rollback_failed",
                              status=STATUS_BLOCKED, rollback="failed",
                              staging=staging_rel, staging_sha_expected=staging_sha,
                              staging_sha_actual=actual)
                return _finalize_and_save(rec, revision_dir, started)
            os.remove(path)
            removed = {"basename": os.path.basename(path), "sha256": actual}
    lease.rollback_transaction(txn, "rollback_revision（编排侧显式回滚）")
    rec.update({
        "status": STATUS_ROLLED_BACK, "verdict": STATUS_ROLLED_BACK,
        "ok": True, "usable": False, "stage": "rollback",
        "blocked_at": None, "rollback": "executed",
        "adopted": False, "staging_removed": removed,
        "reasons": ["rolled_back: 本轮已回滚（staging %s）"
                    % ("已移除" if removed else "本不存在") + "：设计侧未触碰"
                    "（live_board_touched=false）"],
    })
    rec["transaction"] = txn
    _append_event(revision_dir, record, "rollback_executed",
                  status=STATUS_ROLLED_BACK, rollback="executed",
                  staging_removed=removed)
    return _finalize_and_save(rec, revision_dir, started)


# -------------------------------------------------------------------- adopt

def adopt(revision_dir: str, design_board_path: str) -> dict:
    """显式采纳通道：**唯一**允许触碰设计侧的路径（见模块 docstring）。

    前置（fail-closed）：记录存在；`sha256(design_board_path) ==
    base.sha256`（不等 ⇒ stale，拒绝）；状态 `accepted`（或 KiCad5 只读降级
    的 `mirror_only`）；staging/基准副本 sha 与记账一致；备份路径不存在
    （只追加不覆写）。

    状态机纪律：目标侧/请求侧的前置不满足（状态不符、设计目标缺失、stale、
    备份已存在、采纳来源不存在）一律走 `_refuse` —— **不改**轮次记录
    （accepted 轮次不会被一次失败的 adopt 尝试写成 blocked），只在台账追加
    `adopt_refused` 事件，修正后可重试；只有"采纳来源 sha 与记账不符/写入后
    sha 不符"这类**完整性失败**才把轮次写成 blocked。
    """
    started = datetime.now(timezone.utc)
    record, reason = _load_record(revision_dir)
    if reason:
        return _blocked_record([reason], "adopt")
    if not isinstance(design_board_path, str) or not design_board_path:
        raise CopperLoopError("design_board_path: 必须是非空字符串")
    status = record.get("status")
    basis = (record.get("base") or {}).get("identity_basis")
    degraded = basis == copper_model.IDENTITY_GEOMETRIC_FALLBACK
    if status == STATUS_ACCEPTED:
        source_rel, source_sha = ((record.get("patch") or {}).get("staging"),
                                 (record.get("patch") or {}).get(
                                     "staging_sha256"))
        if source_rel is None:
            return _finalize_and_save(_blocked_rec(record, [
                "adopt_source_missing: accepted 状态但无 staging 记录"]),
                revision_dir, started)
    elif status == STATUS_MIRROR_ONLY and degraded:
        # KiCad5 只读降级：无补丁可采纳 → 采纳基准本身（逐字节相同，零风险）
        source_rel = (record.get("base") or {}).get("copy")
        source_sha = (record.get("base") or {}).get("sha256")
    else:
        return _refuse(record, revision_dir, "adopt", [
            "adopt_requires_accepted_revision: 当前 status=%r（identity_basis="
            "%r）：只有 accepted 轮次可 adopt；KiCad5 只读降级（identity_basis="
            "geometric_fallback）的 mirror_only 轮次可采纳基准本身"
            "（本拒绝不改轮次记录）" % (status, basis)])

    # P3b zone 填充门：与 accept 同一判据（纵深防御 —— accept 后证据被移走也
    # 不得采纳）；KiCad5 只读降级（无补丁）不留任何 zone 编辑 ⇒ 直接放行。
    refusal = _fill_gate_refusal(record, revision_dir, "adopt",
                                 source_sha256=source_sha)
    if refusal is not None:
        return refusal

    source_path = os.path.join(revision_dir, source_rel)
    if not os.path.isfile(source_path):
        return _finalize_and_save(_blocked_rec(record, [
            "adopt_source_missing: 采纳来源 %s 不存在" % source_rel]),
            revision_dir, started)
    if hashing.sha256_file(source_path) != source_sha:
        return _finalize_and_save(_blocked_rec(record, [
            "adopt_source_integrity_failed: 采纳来源 %s sha 与记账不符"
            % source_rel]), revision_dir, started)

    if not os.path.isfile(design_board_path):
        return _refuse(record, revision_dir, "adopt", [
            "design_board_missing: 设计侧目标不存在: %s"
            % os.path.basename(design_board_path)])
    pre_sha = hashing.sha256_file(design_board_path)
    if pre_sha != record["base"]["sha256"]:
        return _refuse(record, revision_dir, "adopt", [
            "adopt_stale_design_board: 设计侧 sha=%s ≠ 本轮基准 sha=%s"
            "（stale：设计侧已被他人/别的轮次改动 —— 拒绝覆盖，"
            "本拒绝不改轮次记录，修正设计侧后可重试）"
            % (pre_sha, record["base"]["sha256"])])

    design_dir = os.path.dirname(os.path.abspath(design_board_path))
    stem = os.path.splitext(os.path.basename(design_board_path))[0]
    backup_name = "%s_pre-adopt-rev-%d.kicad_pcb" % (stem, record["rev"])
    backup_path = os.path.join(design_dir, backup_name)
    if os.path.exists(backup_path):
        return _refuse(record, revision_dir, "adopt", [
            "adopt_backup_exists: 备份 %s 已存在（只追加不覆写）" % backup_name])

    with open(design_board_path, "rb") as f:
        payload = f.read()
    backup_sha = _write_bytes(backup_path, payload)
    if backup_sha != pre_sha:
        return _finalize_and_save(_blocked_rec(record, [
            "adopt_backup_sha_mismatch: 备份 sha 与设计侧原 sha 不符"]),
            revision_dir, started)
    with open(source_path, "rb") as f:
        new_bytes = f.read()
    post_sha = _write_bytes(design_board_path, new_bytes)
    if post_sha != source_sha:
        return _finalize_and_save(_blocked_rec(record, [
            "adopt_write_sha_mismatch: 设计侧写入后 sha=%s ≠ 来源 sha=%s"
            % (post_sha, source_sha)], backup=backup_name,
            design_board_pre_sha256=pre_sha), revision_dir, started)

    degradation = None
    if degraded:
        degradation = {
            "identity_basis": copper_model.IDENTITY_GEOMETRIC_FALLBACK,
            "patch_capable": False,
            "patch_refusal_reason": REASON_EDIT_UNSUPPORTED_IDENTITY,
            "semantics": "KiCad5 语料无 kicad_uuid（身份为几何回退）：本轮 "
                         "adopt 为只读降级采纳 —— 采纳后该板仍**不可**作为"
                         "补丁基准（补丁阶段一律 edit_unsupported_identity_"
                         "basis 拒绝）；设计侧后续编辑须人工复核，adopt 记录"
                         "已显式登记降级语义",
        }
    adopt_record = {
        "schema": ADOPT_SCHEMA,
        "revision_id": record.get("revision_id"),
        "status": status,
        "source": source_rel, "source_sha256": source_sha,
        "source_kind": "staging" if source_rel != (record.get("base") or {}).get(
            "copy") else "base_copy",
        "design_board_basename": os.path.basename(design_board_path),
        "design_board_sha256_pre": pre_sha,
        "design_board_sha256_post": post_sha,
        "backup_basename": backup_name,
        "backup_sha256": backup_sha,
        "design_board_written": True,
        "live_board_touched": False,
        "identity_degradation": degradation,
        "transaction_untouched": True,
        "note": "adopt 是本闭环唯一允许写设计侧的路径：设计侧真实写入记在本"
                "记录（pre/post sha + 备份），**不**混进 staging 事务 —— "
                "transaction.live_board_touched 恒 false（staging 零写见证"
                "不被破坏）",
    }
    _write_canonical_json(os.path.join(revision_dir, ADOPT_NAME), adopt_record)

    rec = dict(record)
    rec["adopted"] = True
    rec["adopt_record"] = ADOPT_NAME
    rec["artifacts"] = dict(record["artifacts"])
    rec["artifacts"]["adopt_record"] = ADOPT_NAME
    rec["adopt"] = {
        "design_board_basename": adopt_record["design_board_basename"],
        "design_board_sha256_pre": pre_sha,
        "design_board_sha256_post": post_sha,
        "backup_basename": backup_name,
        "source": source_rel,
        "identity_degradation": degraded,
    }
    if degraded:
        rec["reasons"] = ["identity_degradation: KiCad5（geometric_fallback）"
                          "只读降级采纳：见 adopt-record.json."
                          "identity_degradation"]
    _append_event(revision_dir, record, "adopted",
                  status=status, source=source_rel, source_sha256=source_sha,
                  design_board=adopt_record["design_board_basename"],
                  design_board_sha256_pre=pre_sha,
                  design_board_sha256_post=post_sha,
                  backup=backup_name, identity_degradation=degraded)
    return _finalize_and_save(rec, revision_dir, started)
