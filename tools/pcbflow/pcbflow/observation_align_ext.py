"""observation 线 actual 侧对齐器（G 线 r2 包 G2b；ACTUAL-SIDE-ALIGNMENT
PROPOSAL §2/§3/§5 合同实现）。

两口径（皆为附属/候选能力面，判词裁决权在 PREREG r2 用户时点）：

- evaluate_pad_escape_agreement(board_text, *, binding)：A-R2-1 A 口径
  per-pad 扇出需求/接触一致性视图（附属一致性核对，非资源校准）。
  actual 面=actual_ext.attribute_pad_escapes（R6③ escape_kind∈{via,
  trace,none}）；预测面=corpus_convert_ext.extract_pad_geometry 折算
  board dict + audit_cmd.escape_check（消费其 pad_transit/pad_blocked，
  与 ffext demand 生成同源同判）。per-pad 2×2 交叉表 + summary 守恒。
- evaluate_layer_capacity_demand_fit(board_text, *, ffext_layer_demand_value)：
  A-R2-2 口径 layer_capacity demand 贴合度（mm² 两侧同口径）。与
  estimate_layer_capacity 同判据同源复算网集（2/≤4 端、非电源 cls_of
  恒 None、GND/unconnected- 跳过）→ 逐网 segment/arc 实际长度 Σ
  （arc=_arc_length_mm 同源）× config.AUDIT_TRACK_PITCH_MM →
  actual_area_mm2；与 ffext 计划 layer_capacity 行 demand.value 配对。

纪律：
- 纯函数、零 I/O、零子进程、零网络、零 wall-clock（ALIGN_DATE 为人工
  声明常量）；canonical 序列化由调用方走 hashing（本模块零落盘）。
- fail-closed：ActualExtError/CorpusExtError/SexprError 原样上抛（本
  模块不捕获不降级）；调用方编排层决定逐板 try→null+reason 转记（沿
  R6② 先例）。
- 既有文件零改动（escape_check/extract_pad_geometry/attribute_pad_
  escapes 只消费不修改）；本模块为纯新增并列路径。
- r2_pending：PREREG frozen §2 的 layer_capacity 判词（「mm 铜长与
  mm² 层容量语义不齐，不混读」）与 escape 附属性均未被本模块推翻——
  口径采纳与否由 r2 冻结时用户裁决（A-R2-1/A-R2-2）；裁决前输出不入
  M1–M3、不挂门（descriptive）。
"""

from __future__ import annotations

import math

from . import actual_ext as ae, audit_cmd, config, corpus_convert_ext as cce

MODULE_NAME = "pcbflow.observation_align_ext"
ALIGN_VERSION = "obs-align-r2"          # 声明常量；零 wall-clock/零 I/O/零网络

#: 声明日期（人工会话声明常量，非机器 wall-clock）
ALIGN_DATE = "2026-09-12"

#: ACTUAL-SIDE-ALIGNMENT-PROPOSAL §2.3 convention 逐字样例（A 口径入行
#: 文本；逐字=与提案原文一字不差，测试比对钉住）
CONVENTION_VERBATIM_PAD_ESCAPE = (
    "escape 一致性核对（附属，descriptive）：prediction=audit_cmd."
    "escape_check pad_transit[(ref,num)]（重算，同 ffext demand 生成"
    "同源同判；GND/unconnected- 前缀网模型内建跳过）；actual=actual_"
    "ext.attribute_pad_escapes escape_kind∈{via,trace}（同位容差 "
    "0.01mm、层相交含 *.Cu；无 net 绑定 pad 不参与）；两侧同为 per-pad "
    "二元标签，agreement=标签一致率；非 escape_slots 资源量配对"
    "（channels 场级供需无 actual 测量器），不入 M1–M3（沿 Q6/RC-6 "
    "附属先例）")

#: ACTUAL-SIDE-ALIGNMENT-PROPOSAL §3.2 语义声明逐字（LC 口径入行文本）
CONVENTION_VERBATIM_LAYER_CAPACITY = (
    "这是「layer_capacity demand 模型对参考态布线占用的贴合度」核对"
    "（链式直连假设 vs 实际走线长度的系统性比），不是层容量校准"
    "（supply 侧无 actual，M1/M2 解锁面仅覆盖 demand 半边）；unit 两侧"
    "一致 mm²。")

#: r2_pending 标记常量（判词未推翻，r2 冻结时用户裁决；A-R2-1/A-R2-2）
R2_PENDING = True
R2_PENDING_NOTE = (
    "PREREG-RESOURCE-CALIBRATION-R1-frozen §2 判词未被本输出推翻："
    "escape 口径=附属一致性核对（descriptive，不入 M1–M3）；layer_"
    "capacity 口径=A-R2-2 候选（demand 贴合度核对，非层容量校准）——"
    "是否采纳为 actual 定义并更新 §2 可测性声明，由 r2 冻结时用户裁决"
    "（ACTUAL-SIDE-ALIGNMENT §7）；裁决前本输出不挂门、不进指标分母")

_ROUND_AREA_DIGITS = 3
_ROUND_RATIO_DIGITS = 6


def _round(x: float, digits: int) -> float:
    return round(x, digits)


# ---------------------------------------------------------------------------
# A-R2-1：per-pad escape 一致性（A 口径）
# ---------------------------------------------------------------------------

def evaluate_pad_escape_agreement(board_text: str, *, binding: str) -> dict:
    """A 口径：per-pad 扇出需求/接触一致性视图（附属一致性核对，非资源
    校准；纯函数；fail-closed 异常原样上抛，不捕获不降级）。

    输入：board_text=参考态 routed 板文本；binding ∈ actual_ext.BINDINGS
    （显式档）。内部全纯函数重算，不读 ffext 计划：
      actual 面 = actual_ext.extract_routed_elements +
                  attribute_pad_escapes（escape_kind∈{via,trace,none}）；
      预测面  = corpus_convert_ext.extract_pad_geometry（折算 board dict）
                + audit_cmd.escape_check（消费 pad_transit/pad_blocked；
                cls_of 形参沿 estimate_escape_slots 先例传 None）。

    返回 dict：
      binding / board_version /
      pads: [{ref, pad, net_key,
              pred_transit: bool|None,     # None=预测面未定义（GND/
                                           # unconnected-/无网/联名缺失）
              pred_blocked: bool|None,
              actual_escape_kind: "via"|"trace"|"none"|None,  # None=unbound
              agreement: bool|None}]       # 仅两侧均有定义时非 None；
                                           # (ref,pad) 键典序
      summary: {pads_both_defined, agree, disagree,
                pads_pred_only, pads_actual_only,
                pads_undefined_both,       # 两侧皆无定义（守恒补充类）
                pads_total,                # = len(pads)（两侧键并集）
                contingency: {pred_true_actual_true, pred_true_actual_false,
                              pred_false_actual_true, pred_false_actual_false},
                agreement_rate}            # agree/pads_both_defined；分母
                                           # 0 → None（沿 §0.3 不虚构）
      convention_verbatim: 提案 §2.3 样例逐字
      r2_pending / r2_pending_note
      basis: [两侧函数名+版本锚]

    守恒：pads_both_defined + pads_pred_only + pads_actual_only +
    pads_undefined_both == len(pads) == pads_total（两侧 pad 键并集；
    无重复 reference 降级的板 = 板 pad 总数——extract_pad_geometry 对
    重复 reference 的唯一化降级（~dupNN）与 actual_ext 的原字面引用在
    重复 reference 板上键空间不同，差异如实进 pred_only/actual_only，
    口径见 convention_verbatim 与模块 docstring）。

    agreement 语义：pred_transit（预测「该 pad 需离场」）vs
    actual_escape_kind ∈ {via,trace}（参考态「该 pad 实际有离场接触
    证据」）的标签一致；两侧语义对称性（需求预测 vs 接触实况的相关性，
    非资源量配对）由 convention_verbatim 逐字声明。
    """
    ae._check_binding(binding)
    pad_geo = cce.extract_pad_geometry(board_text)
    if pad_geo["binding"] != binding:
        raise cce.CorpusExtError(
            f"预测面绑定档 {pad_geo['binding']!r} 与显式 binding "
            f"{binding!r} 不一致（档错配 fail-closed）")
    board = {"footprints": pad_geo["footprints"], "pads": pad_geo["pads"],
             "bbox": pad_geo["bbox"]}
    esc = audit_cmd.escape_check(board, None)  # cls_of 为 C2 未消费形参
    actual = ae.attribute_pad_escapes(board_text, binding=binding)

    actual_kind = {(r["ref"], r["pad"]): r["escape_kind"]
                   for r in actual["pads"]}
    actual_net_key = {(r["ref"], r["pad"]): r["net_key"]
                      for r in actual["pads"]}
    pad_transit = esc["pad_transit"]
    pad_blocked = esc["pad_blocked"]

    # 键空间=两侧全 pad 并集（pred 侧 pad_geo 全 pads + actual 侧全 pads
    # + 两个 defined 集——defined 集键天然来自各自 pads，已被前两者覆盖）
    keys = {(p["ref"], p["num"]) for p in pad_geo["pads"]}
    keys |= set(actual_kind)

    rows = []
    both = pred_only = actual_only = undefined_both = 0
    agree = disagree = 0
    contingency = {"pred_true_actual_true": 0, "pred_true_actual_false": 0,
                   "pred_false_actual_true": 0, "pred_false_actual_false": 0}
    for key in sorted(keys):
        pred_t = pad_transit.get(key)
        pred_b = pad_blocked.get(key)
        kind = actual_kind.get(key)
        pred_defined = pred_t is not None
        actual_defined = kind is not None
        agr = None
        if pred_defined and actual_defined:
            agr = (pred_t == (kind in ("via", "trace")))
            contingency[f"pred_{str(pred_t).lower()}_actual_"
                        f"{str(kind in ('via', 'trace')).lower()}"] += 1
            if agr:
                agree += 1
            else:
                disagree += 1
            both += 1
        elif pred_defined:
            pred_only += 1
        elif actual_defined:
            actual_only += 1
        else:
            undefined_both += 1
        rows.append({
            "ref": key[0], "pad": key[1],
            "net_key": actual_net_key.get(key),
            "pred_transit": pred_t,
            "pred_blocked": pred_b,
            "actual_escape_kind": kind,
            "agreement": agr,
        })

    return {
        "binding": binding,
        "board_version": actual["board_version"],
        "pads": rows,
        "summary": {
            "pads_both_defined": both,
            "agree": agree,
            "disagree": disagree,
            "pads_pred_only": pred_only,
            "pads_actual_only": actual_only,
            "pads_undefined_both": undefined_both,
            "pads_total": len(rows),
            "contingency": contingency,
            "agreement_rate": (_round(agree / both, _ROUND_RATIO_DIGITS)
                               if both > 0 else None),
        },
        "coord_tol_mm": ae.ESCAPE_COORD_TOL_MM,
        "parse_warnings": list(actual["summary"]["parse_warnings"]),
        "convention_verbatim": CONVENTION_VERBATIM_PAD_ESCAPE,
        "r2_pending": R2_PENDING,
        "r2_pending_note": R2_PENDING_NOTE,
        "basis": [
            "pcbflow.actual_ext.attribute_pad_escapes（R6③，"
            "track=observation-actual-ext-r1）",
            "pcbflow.corpus_convert_ext.extract_pad_geometry + "
            "pcbflow.audit_cmd.escape_check（C2 同源，pad_transit/"
            "pad_blocked）",
            f"pcbflow.observation_align_ext（ALIGN_VERSION={ALIGN_VERSION}）",
        ],
    }


# ---------------------------------------------------------------------------
# A-R2-2：layer_capacity demand 贴合度（mm² 两侧同口径）
# ---------------------------------------------------------------------------

def _selected_net_set(pad_geo: dict) -> set:
    """与 corpus_convert_ext.estimate_layer_capacity 同判据同源复算网集
    （逐行同判）：非 None net 名全集 → GND/unconnected- 前缀跳过 →
    cls_of 恒 None（语料板域无分类源，不虚构 PWR 排除）→ 该网 pad 数
    2..4 方计入。返回计入网名集合。"""
    nets = sorted({p["net"] for p in pad_geo["pads"] if p["net"] is not None})
    selected = set()
    for net in nets:
        if net == "GND" or net.startswith("unconnected-"):
            continue
        cls = None  # 语料板域无 constraints 分类源：恒 None（不虚构）
        if cls and cls.startswith("PWR"):
            continue
        pads = [p for p in pad_geo["pads"] if p["net"] == net]
        if not 2 <= len(pads) <= 4:
            continue
        selected.add(net)
    return selected


def evaluate_layer_capacity_demand_fit(board_text: str, *,
                                       ffext_layer_demand_value) -> dict:
    """A-R2-2 口径：layer_capacity demand 贴合度（mm² 两侧同口径；纯函数；
    fail-closed 异常原样上抛，不捕获不降级）。

    输入：board_text=参考态 routed 板文本；ffext_layer_demand_value=
    ffext 计划 layer_capacity 行 demand.value（mm²；None=零封装板诚实
    null → 整行 null+reason，不虚构配对面）。

    内部：extract_routed_elements（routed 几何）+ corpus_convert_ext.
    extract_pad_geometry（网集同判复算：2/≤4 端、cls_of 恒 None、
    GND/unconnected- 跳过）→ 计入网的 routed segment/arc 实际长度 Σ
    （arc=actual_ext._arc_length_mm 同源；网身份键=net_key，与计入网
    名集经 pad 净名映射对齐）→ × config.AUDIT_TRACK_PITCH_MM →
    actual_area_mm2。

    返回 dict：
      actual: {value: float, unit: "mm2"} | {value: None, unit: None,
              not_available_reason: str}   # None 仅当 ffext demand=None
      E / e: float|None（E=actual−predicted；e=E/actual，分母=actual，
             actual=0 → e=None 沿 §0.3）
      nets_pred / nets_actual / net_set_symmetric_diff: 网集对账（差异
             如实；不硬配单侧）
      net_lengths_mm: 计入网逐网 routed 长度（net 名典序；对账面）
      pred_demand_value_recomputed_mm2: 预测侧链式直连 demand 同源复算
             值（round 3；与 ffext 计划值同函数域，供交叉核对）
      pitch_mm / convention_verbatim / r2_pending / r2_pending_note /
      basis / board_version / binding
    """
    binding = cce.detect_binding(board_text)
    pad_geo = cce.extract_pad_geometry(board_text)
    el = ae.extract_routed_elements(board_text, binding=binding)

    selected = _selected_net_set(pad_geo)
    keys = {p["net_key"] for p in pad_geo["pads"]
            if p["net"] in selected and p["net_key"] is not None}
    key2name = {p["net_key"]: p["net"] for p in pad_geo["pads"]
                if p["net_key"] is not None and p["net"] is not None}

    # 预测侧链式直连 demand 同源复算（estimate_layer_capacity 逐行同判）
    pred_len = 0.0
    for net in sorted(selected):
        pads = sorted((p["x"], p["y"]) for p in pad_geo["pads"]
                      if p["net"] == net)
        for a, b in zip(pads, pads[1:]):
            pred_len += math.hypot(b[0] - a[0], b[1] - a[1])

    # actual 侧：计入网的 routed 实际长度 Σ（segment 欧氏 + arc 同源弧长；
    # 逐网账与总长同一遍累计，net_lengths 求和 == 总长，self-consistent）
    per_net_len: dict = {}
    for seg in el["segments"]:
        k = seg["net_key"]
        if k in keys:
            (x1, y1), (x2, y2) = seg["start"], seg["end"]
            per_net_len[key2name[k]] = per_net_len.get(
                key2name[k], 0.0) + math.hypot(x2 - x1, y2 - y1)
    for arc in el["arcs"]:
        k = arc["net_key"]
        if k in keys:
            per_net_len[key2name[k]] = per_net_len.get(
                key2name[k], 0.0) + ae._arc_length_mm(
                    arc, el["board_version"], f"arc[{arc['index']}]")
    total_len = sum(per_net_len.values())

    net_lengths = {name: round(v, ae._LENGTH_ROUND_DIGITS)
                   for name, v in sorted(per_net_len.items())}

    pitch = config.AUDIT_TRACK_PITCH_MM
    actual_area = total_len * pitch

    nets_actual = sorted(per_net_len.keys())
    sym_diff = sorted(set(selected) ^ set(nets_actual))

    out = {
        "binding": binding,
        "board_version": el["board_version"],
        "pitch_mm": pitch,
        "nets_pred": sorted(selected),
        "nets_actual": nets_actual,
        "net_set_symmetric_diff": sym_diff,
        "net_lengths_mm": net_lengths,
        "pred_demand_value_recomputed_mm2": _round(
            pred_len * pitch, _ROUND_AREA_DIGITS),
        "convention_verbatim": CONVENTION_VERBATIM_LAYER_CAPACITY,
        "r2_pending": R2_PENDING,
        "r2_pending_note": R2_PENDING_NOTE,
        "basis": [
            "pcbflow.actual_ext.extract_routed_elements（R6① 元素视图）"
            "+ actual_ext._arc_length_mm（同源弧长）",
            "pcbflow.corpus_convert_ext.extract_pad_geometry + "
            "estimate_layer_capacity 同判据网集复算（2/≤4 端、cls_of "
            "恒 None、GND/unconnected- 跳过）",
            f"pcbflow.config.AUDIT_TRACK_PITCH_MM={pitch}",
            f"pcbflow.observation_align_ext（ALIGN_VERSION={ALIGN_VERSION}）",
        ],
    }

    if ffext_layer_demand_value is None:
        out["actual"] = {
            "value": None, "unit": None,
            "not_available_reason": (
                "ffext 计划 layer_capacity 行 demand=None（零封装板诚实 "
                "null）→ 整行 null+reason（不虚构配对面，ACTUAL-SIDE-"
                "ALIGNMENT §5 合同）"),
        }
        out["E"] = None
        out["e"] = None
        return out

    actual_value = _round(actual_area, _ROUND_AREA_DIGITS)
    E = _round(actual_value - float(ffext_layer_demand_value),
               _ROUND_AREA_DIGITS)
    e = (_round(E / actual_value, _ROUND_RATIO_DIGITS)
         if actual_value != 0.0 else None)  # actual=0 → e=None 沿 §0.3
    out["actual"] = {"value": actual_value, "unit": "mm2"}
    out["E"] = E
    out["e"] = e
    return out
