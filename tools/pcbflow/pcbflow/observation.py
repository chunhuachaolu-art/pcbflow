"""observation 行构造器（observation-row-v1；纯函数、零 IO）。

包 c 物化批（ADJUDICATION-2026-09-12 §4 R9–R19；schema=out/v3-obs-proposal/
OBSERVATION-SCHEMA-PROPOSAL.md 冻结版 §2 六组字段 + D-OBS-1..8）。

职责边界（MATERIALIZATION-DESIGN §1.1.2）：
- 输入=上游构件的已解析 dict/str（FF-CORPUS 计划、ffext 六类计划、
  net-registry、参考态 routed 计数账、治理侧锚值），全部由批处理编排层
  （命令层）读盘与对账后传入；本模块零文件 IO、零子进程、零网络。
- 输出=list[行 dict]（schema=pcbflow.schemas "observation-row-v1"，
  additionalProperties=false）；行集按 observation_id 典序输出。
- 行种（v1 授权面=「rails/via/pad_load/六类配对行」）：
    rails   ——FF-CORPUS rails[].pad_count 忠实性逐 rail 配对行
    padload ——FF-CORPUS signal_layer_pad_load 逐层配对行（R8；actual=
              actual_ext R6② 逐层 pad 计数；R6② 板级 fail-closed 板落
              actual=null+reason，不中断批次——审查报告 §10.1/N1/N2）
    sixkind ——ffext-r1 六类资源行：escape_slots / layer_capacity /
              corridor / bus_lane / via_budget / power_return_space；
              仅 via_budget 有 actual 侧数值（参考态板级 via 计数，
              actual-only 台账行）；其余类 actual=null+reason
- fail-closed：缺字段/非法枚举/非有限数/未知行种一律 ObservationRowError；
  prediction/actual 不可测=value null + not_available_reason 非空（D-OBS-6），
  不硬造、不静默。
- 确定性：无 wall-clock/随机；evaluation_metadata 三键恒 null 且不进
  row_core_sha256（copper_loop.core_fact_sha256 同口径）；序列化唯一走
  hashing.canonical_json_bytes（D-OBS-3）。
"""

from __future__ import annotations

import math

from . import hashing

MODULE_NAME = "pcbflow.observation"
TRACK = "observation-rows-r1"

#: 声明日期（人工会话声明常量，非机器 wall-clock）
OBS_DATE = "2026-09-12"

#: 行 schema 注册名（ADJUDICATION R18；D-OBS-4 追加注册用名）
SCHEMA_NAME = "observation-row-v1"

#: 批运行标识（R10/D-OBS-7：无独立运行 manifest 的批次运行锚定批 id）
RUN_ID = "obs-rows-r1"

#: v1 全部行 stage=feedforward（行主体=资源需求账本行；prediction 侧宿主
#: 构件=FF 计划段——FF-CORPUS 与 ffext-r1 同段并列 producer；actual 侧
#: 来源独立登记于 actual_source，不影响 stage 归属）
STAGE = "feedforward"

#: split.role 合法集（提案 §2.5；取值纪律=D-OBS-2 从既有 manifest 派生）
SPLIT_ROLES = ("train", "validation", "holdout", "external_eval")

#: R6② 失败转记时 reason 携带的根因摘要最大长度（防超长堆栈入行）
_REASON_MAX = 300

#: 快照组 null 键的统一 missing_basis_reason（R11；提案 §2.2 必填非空；
#: 语料域实测形态固定：structures/placement 仅 Rev-C 运行域存在，
#: policy 口径=feedforward_config_sha256 而 FF-CORPUS 薄形域无该产物）
MISSING_BASIS_REASON = (
    "structures_hash/placement_snapshot_sha256/policy_hash 三键语料域无源"
    "（实测在案，不硬造）：structures.buses 与 placement CSV 仅 Rev-C 运行"
    "域存在；policy_hash 口径=SPEC §7.1 feedforward_config_sha256（R11），"
    "FF-CORPUS 薄形域无 feedforward config 产物")

#: features 白名单（R17 board 级最小集；只收预测时点可得源——D-OBS-5：
#: 参考态 routed 几何（segment/arc/via/zone 计数）禁止入 features，故
#: 白名单收窄为 net-registry 头三键 + 板文本布局面 pad/footprint 计数
#: （FF 计划生成链消费面同源）；白名单收窄偏差已在首跑报告显式记录）
FEATURE_KEYS = ("footprint_count", "named_net_count", "net_count",
                "pad_count", "unnamed_net_count")

LABEL_CONVENTION = (
    "rails/padload 配对行：E=actual−predicted，e=E/actual（actual=0 时 "
    "e=null，行仍出、actual=0 不入指标分母沿 PREREG §0.3）；六类行 v1 "
    "无配对残差（prediction/actual 至少一侧 null，D-OBS-6）→ label=null；"
    "不把 missing_basis 判为一致")


class ObservationRowError(ValueError):
    """observation 行构造 fail-closed 失败（ValueError 子类）。"""


# ---------------------------------------------------------------------------
# 内部严格化工具
# ---------------------------------------------------------------------------

def _req(obj, key, what):
    if not isinstance(obj, dict) or key not in obj:
        raise ObservationRowError(f"{what}: 缺 required 键 {key!r}（fail-closed）")
    return obj[key]


def _nonempty_str(value, what):
    if not isinstance(value, str) or not value:
        raise ObservationRowError(f"{what}: 须非空字符串，得到 {value!r}")
    return value


def _hash64(value, what):
    v = _nonempty_str(value, what)
    if len(v) != 64 or any(c not in "0123456789abcdef" for c in v):
        raise ObservationRowError(f"{what}: 须 64 位小写 hex，得到 {v!r}")
    return v


def _finite_number(value, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObservationRowError(f"{what}: 须数值，得到 {value!r}")
    if not math.isfinite(value):
        raise ObservationRowError(f"{what}: 非有限数 {value!r}（fail-closed）")
    return value


def _nonneg_int(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ObservationRowError(f"{what}: 须非负整数，得到 {value!r}")
    return value


def _str_list(value, what):
    if not isinstance(value, list) or not all(
            isinstance(b, str) and b for b in value):
        raise ObservationRowError(f"{what}: 须非空字符串数组，得到 {value!r}")
    return list(value)


def _board_slug(board_id: str) -> str:
    """board_id → id/文件名安全 slug（确定性；非白名单字符→'_'）。"""
    return "".join(
        ch if (ch.isascii() and (ch.isalnum() or ch in "._+")) else "_"
        for ch in board_id)


def _observation_id(dataset_id: str, board_id: str, dim: str, seq: int) -> str:
    """R10：确定性拼接 observation_id（dataset|board_id|stage|维度+序号，
    不用内容寻址）。分隔符取 '-'（'|' 为裁定行文的分隔记号；id 须
    文件名/_REL_POSIX 友好）。seq=该维度行按定位键典序的 1-based 序号。"""
    if seq < 1:
        raise ObservationRowError(f"observation_id seq 须 ≥1，得到 {seq}")
    return (f"obs-{_nonempty_str(dataset_id, 'observation_id.dataset')}"
            f"-{_nonempty_str(_board_slug(board_id), 'observation_id.board')}"
            f"-{STAGE}-{_nonempty_str(dim, 'observation_id.dim')}-{seq}")


def _core_sha256(row: dict) -> str:
    """row_core_sha256：剔除 evaluation_metadata 与自身字段后 canonical
    哈希（copper_loop.core_fact_sha256 同口径，可独立重算）。"""
    body = {k: v for k, v in row.items()
            if k not in ("evaluation_metadata", "row_core_sha256")}
    return hashing.sha256_bytes(hashing.canonical_json_bytes(body))


def _label(actual_value, predicted_value):
    """label=残差 E=actual−predicted 与相对残差 e=E/actual（提案表 D）。

    actual=0 时 e=null（行仍出，actual=0 不入指标分母沿 PREREG §0.3）；
    任一侧 null → 整个 label=null（D-OBS-6：不硬造配对）。"""
    if actual_value is None or predicted_value is None:
        return None
    a = _finite_number(actual_value, "label.actual")
    p = _finite_number(predicted_value, "label.predicted")
    residual = a - p
    relative = round(residual / a, 9) if a != 0 else None
    return {"residual": residual, "relative_residual": relative}


# ---------------------------------------------------------------------------
# 公共段（标识/快照/定位/features/治理/元数据）
# ---------------------------------------------------------------------------

def _shared_sections(*, record, board_sha256, registry_sha256,
                     constraints_sha256, registry_obj, leakage_group,
                     split_role, manifest_ref) -> dict:
    """观察行共享节装配（全部入参 fail-closed 校验后进入正文）。

    六类形态校验器（_nonempty_str/_hash64/_nonneg_int 等）逐字段把坏值
    转成 ObservationRowError；split_role 枚举门+manifest_ref 双字段+
    registry 计数三者先过，再由六类行构造器（_sixkind_rows 等）消费。
    """
    board_id = _nonempty_str(_req(record, "board_id", "record"),
                             "record.board_id")
    dataset_id = _nonempty_str(_req(record, "dataset_id", "record"),
                               "record.dataset_id")
    profile_id = _nonempty_str(_req(record, "profile_id", "record"),
                               "record.profile_id")
    if split_role not in SPLIT_ROLES:
        raise ObservationRowError(
            f"split_role: 非法枚举 {split_role!r}（合法集 "
            f"{list(SPLIT_ROLES)}——fail-closed）")
    mref_path = _nonempty_str(_req(manifest_ref, "path", "manifest_ref"),
                              "manifest_ref.path")
    mref_sha = _hash64(_req(manifest_ref, "sha256", "manifest_ref"),
                       "manifest_ref.sha256")
    named = _nonneg_int(_req(registry_obj, "named_net_count", "registry"),
                        "registry.named_net_count")
    unnamed = _nonneg_int(_req(registry_obj, "unnamed_net_count", "registry"),
                          "registry.unnamed_net_count")
    total = _nonneg_int(_req(registry_obj, "net_count", "registry"),
                        "registry.net_count")
    nets = _req(registry_obj, "nets", "registry")
    if not isinstance(nets, list) or len(nets) != total:
        raise ObservationRowError(
            f"registry: nets 条数 {len(nets) if isinstance(nets, list) else nets!r}"
            f" != net_count({total}）（对账 fail-closed）")
    named_recalc = sum(1 for n in nets
                       if isinstance(n, dict) and n.get("name", "") != "")
    unnamed_recalc = sum(1 for n in nets if isinstance(n, dict)
                         and n.get("classification") == "unnamed")
    if named != named_recalc or unnamed != unnamed_recalc:
        raise ObservationRowError(
            f"registry: 计数头与 nets 明细不复算一致"
            f"（named {named} vs {named_recalc}；unnamed {unnamed} vs "
            f"{unnamed_recalc}；unnamed=classification 子集非空名网数，"
            "对账 fail-closed）")
    features = {
        "footprint_count": _nonneg_int(
            _req(registry_obj, "_footprint_count", "registry(编排层注入)"),
            "registry._footprint_count"),
        "named_net_count": named,
        "net_count": total,
        "pad_count": _nonneg_int(
            _req(registry_obj, "_pad_count", "registry(编排层注入)"),
            "registry._pad_count"),
        "unnamed_net_count": unnamed,
    }
    return {
        "run_id": RUN_ID,
        "project_id": profile_id,
        "profile_id": profile_id,
        "board_revision": dataset_id,
        "stage": STAGE,
        "registry_snapshot_hash": _hash64(registry_sha256,
                                          "registry_sha256"),
        "structures_hash": None,
        "constraints_sha256": _hash64(constraints_sha256,
                                      "constraints_sha256"),
        "placement_snapshot_sha256": None,
        "board_snapshot_sha256": _hash64(board_sha256, "board_sha256"),
        "policy_hash": None,
        "missing_basis_reason": MISSING_BASIS_REASON,
        "row_id": None,
        "net_id": None,
        "relation_id": None,
        "resource_id": None,
        "features": features,
        "action": None,
        "label_convention": LABEL_CONVENTION,
        "leakage_group": _nonempty_str(leakage_group, "leakage_group"),
        "split": {
            "dataset_id": dataset_id,
            "role": split_role,
            "board_id": board_id,
            "manifest_ref": {"path": mref_path, "sha256": mref_sha},
        },
        "evaluation_metadata": {"evaluated_at": None, "host": None,
                                "elapsed_s": None},
    }


# ---------------------------------------------------------------------------
# 行种 1：rails 忠实性逐 rail 配对行（descriptive-only）
# ---------------------------------------------------------------------------

def _rail_rows(shared, record, ff_corpus_plan, routed_counts):
    rails = _req(ff_corpus_plan, "rails", "ff_corpus_plan")
    if not isinstance(rails, list):
        raise ObservationRowError("ff_corpus_plan.rails: 须数组")
    by_name = {}
    for entry in _req(routed_counts, "per_net_by_name", "routed_counts"):
        name = _req(entry, "name", "routed.per_net")
        if not isinstance(name, str):
            raise ObservationRowError(
                f"routed.per_net.name: 须字符串，得到 {name!r}")
        by_name[name] = entry  # 空名网条目合法入索引（不与非空 rail 名匹配）
    parser = _nonempty_str(_req(routed_counts, "parser", "routed_counts"),
                           "routed_counts.parser")
    board_path = _nonempty_str(_req(record, "board_path_rel", "record"),
                               "record.board_path_rel")
    ff_plan_rel = _nonempty_str(_req(record, "ff_plan_rel", "record"),
                                "record.ff_plan_rel")
    rows = []
    ordered = sorted(rails, key=lambda r: _nonempty_str(
        _req(r, "net", "ff_corpus.rails"), "rails.net"))
    for i, rail in enumerate(ordered, start=1):
        net = _nonempty_str(_req(rail, "net", "ff_corpus.rails"), "rails.net")
        pad_count = _nonneg_int(_req(rail, "pad_count", "ff_corpus.rails"),
                                f"rails[{net}].pad_count")
        refs = rail.get("member_refs")
        if not isinstance(refs, list) or len(refs) != pad_count:
            raise ObservationRowError(
                f"rails[{net}]: member_refs 数 "
                f"{len(refs) if isinstance(refs, list) else refs!r} != "
                f"pad_count {pad_count}（账本自洽 fail-closed）")
        entry = by_name.get(net)
        if entry is None:
            actual = {"value": None, "unit": "count",
                      "not_available_reason": (
                          f"参考态 routed 账本无 net 名全等条目 {net!r}"
                          "（计划侧/板侧网集差异如实转记，不硬造 0）")}
            actual_value = None
        else:
            actual_value = _nonneg_int(_req(entry, "pad_count",
                                            "routed.per_net"),
                                       f"routed.per_net[{net}].pad_count")
            actual = {"value": actual_value, "unit": "count"}
        row = {
            "observation_id": _observation_id(record["dataset_id"],
                                              record["board_id"], "rails", i),
            "row_id": f"rails:{net}",
            "net_id": net,
            "prediction": {
                "value": pad_count, "unit": "count",
                "basis": [f"{ff_plan_rel}#rails[]（net=={net}）"],
                "model": ("pcbflow.corpus_convert first-order pad ledger"
                          "（FF-CORPUS rails，member_refs 含同 pad 重复"
                          "引用实例）"),
            },
            "actual": actual,
            "actual_source": {
                "path": board_path,
                "field": f"per_net[].pad_count（name=={net} 全等匹配）",
                "sha256": shared["board_snapshot_sha256"],
                "authority": (f"reference_routed_board_text_count"
                              f"（parser={parser}）"),
            },
            "label": _label(actual_value, pad_count),
            "measurement_convention": (
                "计划侧 pad_count=FF-CORPUS rails[].pad_count（按 "
                "member_refs 计，含同 pad 重复引用实例）；实际侧=参考态 "
                "routed 板文本逐网账本中 net 名逐字全等匹配条目的 "
                "pad_count（板文件 pad 元素按 net 绑定计数，重复引用不"
                "重复计元素）；无大小写/空白归一；两口径差异本身=被测"
                "对象（M4/R12）"),
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# 行种 2：signal_layer_pad_load 逐层配对行（R8）
# ---------------------------------------------------------------------------

def _padload_rows(shared, record, ff_corpus_plan, r62):
    slpl = _req(ff_corpus_plan, "signal_layer_pad_load", "ff_corpus_plan")
    if not isinstance(slpl, list):
        raise ObservationRowError(
            "ff_corpus_plan.signal_layer_pad_load: 须数组")
    r62_layers = {}
    r62_error = None
    if _req(r62, "ok", "r62") is True:
        for entry in _req(r62, "per_layer", "r62"):
            layer = _nonempty_str(_req(entry, "layer", "r62.per_layer"),
                                  "r62.per_layer.layer")
            r62_layers[layer] = _nonneg_int(
                _req(entry, "pad_count", "r62.per_layer"),
                f"r62.per_layer[{layer}].pad_count")
    else:
        r62_error = _nonempty_str(_req(r62, "error", "r62"), "r62.error")
    board_path = _nonempty_str(_req(record, "board_path_rel", "record"),
                               "record.board_path_rel")
    ff_plan_rel = _nonempty_str(_req(record, "ff_plan_rel", "record"),
                                "record.ff_plan_rel")
    rows = []
    ordered = sorted(slpl, key=lambda r: _nonempty_str(
        _req(r, "layer", "ff_corpus.slpl"), "slpl.layer"))
    for i, entry in enumerate(ordered, start=1):
        layer = _nonempty_str(_req(entry, "layer", "ff_corpus.slpl"),
                              "slpl.layer")
        pad_count = _nonneg_int(_req(entry, "pad_count", "ff_corpus.slpl"),
                                f"signal_layer_pad_load[{layer}].pad_count")
        if r62_error is not None:
            actual = {"value": None, "unit": "count",
                      "not_available_reason": (
                          "actual_ext R6② 板级 fail-closed（逐 facet 独立"
                          "判定，不影响计数类行）："
                          f"{r62_error[:_REASON_MAX]}")}
            actual_value = None
        elif layer in r62_layers:
            actual_value = r62_layers[layer]
            actual = {"value": actual_value, "unit": "count"}
        else:
            raise ObservationRowError(
                f"padload[{layer}]: R6② 逐层账无该层条目（层集合非全等，"
                "对账 fail-closed）")
        row = {
            "observation_id": _observation_id(record["dataset_id"],
                                              record["board_id"],
                                              "padload", i),
            "row_id": f"signal_layer_pad_load:{layer}",
            "prediction": {
                "value": pad_count, "unit": "count",
                "basis": [f"{ff_plan_rel}#signal_layer_pad_load[]"
                          f"（layer=={layer}）"],
                "model": ("pcbflow.corpus_convert signal_layer_pad_load"
                          "（pad layers token 命中铜层名或 *.Cu）"),
            },
            "actual": actual,
            "actual_source": {
                "path": board_path,
                "field": (f"count_pads_per_layer().per_layer[].pad_count"
                          f"（layer=={layer}）"),
                "sha256": shared["board_snapshot_sha256"],
                "authority": "actual_ext_r6_2（R6② 逐层 pad 计数）",
            },
            "label": _label(actual_value, pad_count),
            "measurement_convention": (
                "两侧同判据（pad layers token 命中铜层名或 *.Cu 即计入"
                "该层，*.Cu pad 逐铜层各计 1，sum(per_layer)−pad_total="
                "通配重复计数，属口径事实非误差）；预测侧源=FF-CORPUS "
                "signal_layer_pad_load；实际侧源=actual_ext."
                "count_pads_per_layer 于参考态权威原件（R6②/R8 同判对账）"),
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# 行种 3：六类资源行（ffext-r1 resources 全量）
# ---------------------------------------------------------------------------

_SIXKIND_ACTUAL_ABSENT = {
    "layer_capacity": (
        "actual 侧无 mm² 面积测量（R6① 逐层铜长 mm 已扩展但与 demand "
        "mm² 语义不齐，不混读——MATERIALIZATION-DESIGN §2/R19 精神）"),
    "escape_slots": (
        "actual 侧 per-(pad,方位侧) 逃逸通道计数无测量器；R6③ per-pad "
        "同位归因（via/trace/none 标签）与 (pad,side) 资源粒度不齐，"
        "不硬配（advisory，authority 不在此）"),
    "corridor": (
        "计划资源 scope=符号引用（board 级）；参考态无可比走廊实际"
        "（不伪造——ff-residuals not_available 台账先例原文）"),
    "bus_lane": (
        "车道占用的走廊级实测未建（MATERIALIZATION-DESIGN §2）"),
    "power_return_space": (
        "rails=pad 账本非铜空间 mm² 语义；actual 侧 zone/pad 计数与类"
        "语义不齐，不混读（MATERIALIZATION-DESIGN §2）"),
}

_SIXKIND_KINDS = ("escape_slots", "layer_capacity", "corridor", "bus_lane",
                  "via_budget", "power_return_space")

_SIXKIND_CONVENTION = (
    "六类资源行 v1 口径：prediction=demand 侧（ffext-r1 六类扩展计划，"
    "逐类诚实标记）；actual 侧仅 via_budget 板级 via 计数可测"
    "（actual-only 台账行，prediction=null 沿 FF-CORPUS not_modelled "
    "原文；不入 M1–M3 可测行池沿 MATERIALIZATION §2）；escape_slots/"
    "layer_capacity/corridor/bus_lane/power_return_space 行 actual=null"
    "+not_available_reason（语义/粒度不齐不硬配）；label=null=无配对"
    "（D-OBS-6）")


def _sixkind_rows(shared, record, ext_plan, routed_counts):
    """六类观察行构造（v4.2 seat 线六类资源形态；逐资源 fail-closed）。

    ext_plan.resources 按 resource_id 排序枚举（kind ∈ _SIXKIND_KINDS
    枚举门），routed_counts 供 vias/geometry 计数与 parser 口径登记；
    任何缺键/坏类型即 ObservationRowError（不静默跳行）。
    """
    resources = _req(ext_plan, "resources", "ext_plan")
    if not isinstance(resources, list):
        raise ObservationRowError("ext_plan.resources: 须数组")
    geom = _req(routed_counts, "geometry_counts", "routed_counts")
    vias_total = _nonneg_int(_req(geom, "vias", "routed.geometry_counts"),
                             "routed.geometry_counts.vias")
    parser = _nonempty_str(_req(routed_counts, "parser", "routed_counts"),
                           "routed_counts.parser")
    board_path = _nonempty_str(_req(record, "board_path_rel", "record"),
                               "record.board_path_rel")
    rows = []
    ordered = sorted(resources, key=lambda r: _nonempty_str(
        _req(r, "resource_id", "ext_plan.resources"),
        "resources.resource_id"))
    for i, res in enumerate(ordered, start=1):
        kind = _req(res, "kind", "ext_plan.resources")
        if kind not in _SIXKIND_KINDS:
            raise ObservationRowError(
                f"resources[{i}].kind: 非法枚举 {kind!r}（合法集 "
                f"{list(_SIXKIND_KINDS)}——fail-closed 不硬造）")
        resource_id = _nonempty_str(
            _req(res, "resource_id", "ext_plan.resources"),
            "resources.resource_id")
        demand_model = _nonempty_str(res.get("demand_model"),
                                     f"resources[{resource_id}].demand_model")
        basis = _str_list(res.get("basis"),
                          f"resources[{resource_id}].basis")
        demand = res.get("demand")
        if demand is not None:
            if not isinstance(demand, dict):
                raise ObservationRowError(
                    f"resources[{resource_id}].demand: 须对象或 null")
            prediction = {
                "value": _finite_number(
                    _req(demand, "value", "demand"),
                    f"resources[{resource_id}].demand.value"),
                "unit": _nonempty_str(_req(demand, "unit", "demand"),
                                      f"resources[{resource_id}].demand.unit"),
                "basis": _str_list(demand.get("basis"),
                                   f"resources[{resource_id}].demand.basis"),
                "model": demand_model,
            }
        else:
            reason = _nonempty_str(res.get("not_available_reason"),
                                   f"resources[{resource_id}]."
                                   f"not_available_reason")
            verbatim = res.get("not_modelled_verbatim")
            if isinstance(verbatim, str) and verbatim:
                reason = (f"{reason}（FF-CORPUS not_modelled 原文："
                          f"{verbatim}）")
            prediction = {"value": None, "unit": None, "basis": basis,
                          "model": demand_model,
                          "not_available_reason": reason}
        if kind == "via_budget":
            actual = {"value": vias_total, "unit": "count"}
            actual_value = vias_total
            actual_field = ("geometry_counts.vias（板级，绑定已声明网的 "
                            "via 元素计数）")
            actual_authority = ("reference_routed_board_text_count"
                                f"（parser={parser}）")
        else:
            actual = {"value": None, "unit": None,
                      "not_available_reason": _SIXKIND_ACTUAL_ABSENT[kind]}
            actual_value = None
            actual_field = ("not_consumed（actual=null，见 actual."
                            "not_available_reason）")
            actual_authority = "reference_routed_board_text"
        row = {
            "observation_id": _observation_id(record["dataset_id"],
                                              record["board_id"],
                                              "sixkind", i),
            "row_id": resource_id,
            "resource_id": resource_id,
            "prediction": prediction,
            "actual": actual,
            "actual_source": {
                "path": board_path,
                "field": actual_field,
                "sha256": shared["board_snapshot_sha256"],
                "authority": actual_authority,
            },
            "label": _label(actual_value, prediction["value"]),
            "measurement_convention": _SIXKIND_CONVENTION,
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# 板级入口（编排层调用；行集按 observation_id 典序）
# ---------------------------------------------------------------------------

def build_board_rows(*, record, board_sha256, registry_sha256,
                     constraints_sha256, registry_obj, leakage_group,
                     split_role, manifest_ref, ff_corpus_plan, ext_plan,
                     routed_counts, r62) -> list:
    """单板行集构造（纯函数）。

    参数（全部由编排层读盘/对账后传入）：
    - record：54 板盘点记录（profile_id/board_id/dataset_id/board_path_rel/
      ff_plan_rel——形态同 corpus_convert_ext 板记录）；
    - board_sha256：参考态权威原件实测 sha256（D-OBS-7 对账由编排层
      先行：与 route-check/k9 声明不符须在调用前拒绝）；
    - registry_sha256：profiles/<pid>/derived/net-registry.json 字节 sha256；
    - constraints_sha256：profiles/<pid>/inputs/constraints.json 字节 sha256；
    - registry_obj：net-registry 解析对象（features 计数源；编排层把
      板文本布局面计数以 _footprint_count/_pad_count 注入其副本）；
    - leakage_group：manifest project_groups 派生组 id 原文（R13）；
    - split_role：manifest dataset_splits 派生 role（D-OBS-2 不重切）；
    - manifest_ref：{"path","sha256"}（R3：demo=kicad-demos-r1）；
    - ff_corpus_plan：FF-CORPUS 计划解析对象（rails/signal_layer_pad_load）；
    - ext_plan：ffext-r1 六类计划解析对象（resources）；
    - routed_counts：参考态 routed 计数账 {"per_net_by_name":[{name,
      pad_count,...}], "geometry_counts":{"vias":N,...}, "parser":"<档名>"}
      （id 档=check_stage.parse_routed_geometry 账；名档=actual_ext R7 账）；
    - r62：R6② 结果 {"ok":True,"per_layer":[...]} 或
      {"ok":False,"error":"<ActualExtError 摘要>"}（逐 facet 独立判定，
      失败不中断批次——审查报告 §10.1/N1/N2 口径）。
    """
    shared = _shared_sections(record=record, board_sha256=board_sha256,
                              registry_sha256=registry_sha256,
                              constraints_sha256=constraints_sha256,
                              registry_obj=registry_obj,
                              leakage_group=leakage_group,
                              split_role=split_role,
                              manifest_ref=manifest_ref)
    rows = []
    rows += _rail_rows(shared, record, ff_corpus_plan, routed_counts)
    rows += _padload_rows(shared, record, ff_corpus_plan, r62)
    rows += _sixkind_rows(shared, record, ext_plan, routed_counts)
    out = []
    for row in rows:
        merged = dict(shared)
        merged.update(row)
        merged["row_core_sha256"] = _core_sha256(merged)
        out.append(merged)
    out.sort(key=lambda r: r["observation_id"])
    return out
