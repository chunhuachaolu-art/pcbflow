# -*- coding: utf-8 -*-
"""A3 五通道序数产物 → planner 形状模型候选的转译器（V5.0 P5 第二阶段；任务书
§4 L5 三臂③「②+模型 shadow」的模型侧入口。主审亲做合同件 2026-09-14）。

上游：席位会话三件套经 v5.harness.ingest_run 产出的五通道 output（A3 合同冻结：
ranked_options / ranked_combos / routing_order / defect_scan / principle_objection）。
下游：v5.threearm.inject_model_candidates（候选合同已在其模块 docstring 决定 1
冻结：M-### id / arm="model-shadow" / generator 恒 "v5.model_bridge/" 前缀）。

=======================================================================
转译合同（本文档即钉死文本，改动=新决定）
=======================================================================

1. **候选生成通道只有两个**：routing_order（→ route_order）与 ranked_combos
   （→ layer_assignment）。ranked_options 是单网裁决叙述、defect_scan /
   principle_objection 是缺陷与反对通道——三者不产生候选（文档化）。

2. **层选择记号 = "L:<layer_id>" 规范令牌**（如 "L:F.Cu"）。令牌表由
   choice_vocabulary(board) 给出（=各分区 layer_policy 展开偏好序），进**会话
   提示词**、不进盲包体——A3 五通道合同与盲包内容零改动。只认精确 "L:" 前缀
   令牌，**不做自然语言模糊匹配**（模糊匹配不可审计，fail-closed 优先）。

3. **routing_order 违约 = 上游合同级违约，fail-closed 抛 ModelBridgeError**
   （route_order 是候选必填，序错则无从造候选）。ranked_combos 缺失/非 list
   同为合同级违约；**空 list 合法**（零组合=零候选的基线对照）。

4. **逐 combo 独立裁决**（单项 fail-closed，不炸整批）：
   - combo 须为 dict；键集 ⊆ 分区 id ∪ {"label"}（label 忽略），出现其它键 =
     该 combo 拒绝（reason="unknown_key"）；
   - 每个分区值须为 "L:<layer_id>" 令牌且层在该分区偏好集内（模型只能从给定
     选项中选），违约 = 该 combo 拒绝（reason 记首个违约分区与原因）；
   - combo **可部分指派**：缺键分区继承引擎缺省 = 该分区偏好首层（文档化：
     模型局部规约合法，引擎以确定性缺省补全——与 planner 无理念臂「层集合首
     元素」缺省同源）；
   - 接受序去重：同 (route_order, layer_assignment) 已接受 → 记 duplicate 跳过。

5. **候选本体**：polylines = 分区端点直线（P3 合同，与 planner 同款）；
   generation_trace = []（模型候选不消费编译规则，影子提案）；rules_consumed
   = []；compiled_sha256 = canonical_sha256(compiled_artifact)；candidate_id
   按接受序 M-001 起连续编号。U8 不设限口径：不截断组合数。

6. **纯函数**：零 I/O、零网络、零 LLM API、零随机零时钟；同输入双跑
   （candidates+report）canonical 字节相等。translate 不做几何/可行性预判
   （A4：测量即批准人，可行性归 L6 测量环）。

7. **report（v5.mbridge-report.v1）**：accepted/duplicates 计数 + rejected
   逐条 {index, reason, raw_value}（raw 原值留痕供审计）。report 由调用方
   入证据链；candidates 交 inject_model_candidates（形状二次闸门）。
"""
import re

from . import canonical
from .planner import _expand_policy, _signal_layer_ids

MODEL_BRIDGE_VERSION = "v5.model_bridge/0.1.0"
REPORT_SCHEMA = "v5.mbridge-report.v1"

_LAYER_TOKEN_RE = re.compile(r"^L:(.+)$")
_LABEL_KEY = "label"


class ModelBridgeError(ValueError):
    """转译合同级违约（fail-closed）；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise ModelBridgeError(path, msg)


# ---------------------------------------------------------------- 令牌表

def choice_vocabulary(board):
    """各分区层选择令牌表（会话提示词用）：{pid: ["L:<layer>", ...]}。

    偏好序 = layer_policy 展开序（与 planner._expand_policy 单一事实源同源，
    同函数直调）；"any"/空策略 → 全部可用信号层（stackup 序）。
    """
    signal_ids = _signal_layer_ids(board)
    vocab = {}
    for part in board.get("partitions", []):
        pid = part["partition_id"]
        layers = _expand_policy(part, signal_ids,
                                "board.partitions[%s].layer_policy" % pid)
        vocab[pid] = ["L:%s" % lyr for lyr in layers]
    return vocab


# ---------------------------------------------------------------- 转译

def _parse_layer(value, pid, allowed, path):
    """"L:<id>" 令牌 → 层 id；违约抛 ModelBridgeError（combo 级捕获）。"""
    _require(isinstance(value, str), path, "层选择须为字符串，得到 %r" % (value,))
    m = _LAYER_TOKEN_RE.match(value.strip())
    _require(bool(m), path,
             "层选择须为 \"L:<layer_id>\" 规范令牌（如 L:F.Cu），得到 %r"
             % (value,))
    layer = m.group(1).strip()
    _require(layer in allowed, path,
             "层 %r 不在分区 %s 偏好集 %s" % (layer, pid, allowed))
    return layer


def translate(ordinal, board, compiled_artifact):
    """五通道 output → {"candidates": [...], "report": {...}}（纯函数）。

    ordinal 形状违约（routing_order/ranked_combos 缺失或类型错）抛
    ModelBridgeError；逐 combo 违约走 report.rejected 不抛。
    """
    _require(isinstance(ordinal, dict), "ordinal", "须为 dict（五通道 output）")
    _require(isinstance(board, dict), "board", "须为 dict")
    _require(isinstance(compiled_artifact, dict), "compiled_artifact",
             "须为 dict（编译工件）")

    parts = {p["partition_id"]: p for p in board["partitions"]}
    pids = sorted(parts)
    signal_ids = _signal_layer_ids(board)
    allowed = {pid: _expand_policy(parts[pid], signal_ids,
                                   "board.partitions[%s].layer_policy" % pid)
               for pid in pids}
    endpoints = {pid: [list(parts[pid]["geometry"]["endpoints"][0]),
                       list(parts[pid]["geometry"]["endpoints"][1])]
                 for pid in pids}

    # 通道 1：routing_order（合同级）
    order = ordinal.get("routing_order")
    _require(isinstance(order, list) and all(isinstance(x, str) for x in order),
             "ordinal.routing_order", "须为分区 id 字符串数组")
    _require(len(order) == len(set(order)), "ordinal.routing_order", "含重复分区")
    _require(set(order) == set(pids), "ordinal.routing_order",
             "不恰为全部分区（缺 %s，多 %s）"
             % (sorted(set(pids) - set(order)), sorted(set(order) - set(pids))))

    # 通道 2：ranked_combos（合同级形状 + 逐条裁决）
    combos = ordinal.get("ranked_combos")
    _require(isinstance(combos, list), "ordinal.ranked_combos", "须为 list（可空）")

    compiled_sha = canonical.canonical_sha256(compiled_artifact)
    candidates, report_rejected = [], []
    seen_keys, duplicates = set(), 0

    for idx, combo in enumerate(combos):
        base = "ordinal.ranked_combos[%d]" % idx
        if not isinstance(combo, dict):
            report_rejected.append({"index": idx, "reason": "not_a_dict",
                                    "raw_value": combo})
            continue
        bad_key = sorted(k for k in combo
                         if k != _LABEL_KEY and k not in parts)
        if bad_key:
            report_rejected.append({"index": idx,
                                    "reason": "unknown_key: %s" % bad_key,
                                    "raw_value": {k: combo[k] for k in bad_key}})
            continue
        try:
            assignment = {}
            for pid in pids:
                if pid in combo:
                    assignment[pid] = _parse_layer(combo[pid], pid, allowed[pid],
                                                   "%s.%s" % (base, pid))
                else:
                    assignment[pid] = allowed[pid][0]   # 决定 4：偏好首层缺省
        except ModelBridgeError as exc:
            report_rejected.append({"index": idx,
                                    "reason": exc.message,
                                    "raw_value": {k: v for k, v in combo.items()
                                                  if k != _LABEL_KEY}})
            continue
        key = (tuple(order), tuple(sorted(assignment.items())))
        if key in seen_keys:
            duplicates += 1
            continue
        seen_keys.add(key)
        candidates.append({
            "candidate_id": "M-%03d" % (len(candidates) + 1),
            "arm": "model-shadow",
            "provenance": {"generator": MODEL_BRIDGE_VERSION,
                           "rules_consumed": [],
                           "compiled_sha256": compiled_sha},
            "route_order": list(order),
            "layer_assignment": assignment,
            "polylines": {pid: [list(pt) for pt in endpoints[pid]]
                          for pid in pids},
            "generation_trace": [],
        })

    report = {
        "schema_version": REPORT_SCHEMA,
        "generator": MODEL_BRIDGE_VERSION,
        "routing_order_accepted": True,
        "combos_total": len(combos),
        "accepted": len(candidates),
        "duplicates": duplicates,
        "rejected": report_rejected,
        "non_candidate_channels": ["ranked_options", "defect_scan",
                                   "principle_objection"],
    }
    return {"candidates": candidates, "report": report}


def translate_and_inject(arm3, ordinal, compiled_artifact):
    """便捷链：translate + inject_model_candidates（返回 (arm3, report)）。

    候选形状由 threearm 注入器全量二次闸门（事务式，任一违约整批拒绝且 arm3
    保持原状）；转译 report 原样返回给调用方入证据。
    """
    from .threearm import inject_model_candidates   # 局部 import 防环
    product = translate(ordinal, arm3["board"], compiled_artifact)
    inject_model_candidates(arm3, product["candidates"])
    return arm3, product["report"]
