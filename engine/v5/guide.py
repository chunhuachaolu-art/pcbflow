# -*- coding: utf-8 -*-
"""v5.guide — R2 导引通道（V5-R2-RIPUP-DEEPEN-GUIDE-TASKBOOK-2026-09-24 §2 W-3）。

GUIDE 线已证通道的产品化落点（消费 EXP-S1/S2 与 SCALE-R1 冻结结论，参照源码
route-v5 根 guide_exp_s2.py / s2_scenarios.py 波次机制——只读参照，不新开实验线）：

- **波次粗通道（主选）**：EXP-S2 终判 7/8 场景闭环 1.0、平均早 FULL 0.5–0.7 轮
  触顶——分批承诺（先布波次占住好路、后波让行）优于一次全量并发竞争。
  产品化语义：被 rip 网重布序按波次展开（空间 x 带连续分波，波内网 id 字典序）。
- **档位通道（限 n≤12）**：EXP-S2 n16 档位崩塌（0/3=展开粒度非表达力）在案，
  仅在重布集 ≤12 网时作为次选展开（宽度三档 tier，序=(tier, id)）。
- **探针环**：SCALE-R1 n8 探针序=全枚举真最优、S2 结论约束在提案质量非预算
  ——探针归 executor W-4（victim 定向邻位交换），本件只提供展开序。

确定性冻结（任务书 §2 W-3 明文）：波次序生成去随机化，一切集合/字典遍历
sorted() 后使用（字节等门前提）；评分纯整数/定点，tie-break=网 id 字典序。
本件为纯函数（无状态、无随机、无墙钟）；同输入双跑逐位相等。
"""

GUIDE_VERSION = "v5.guide/0.1.0"

#: 波次档位规则（冻结）：重布集 <3 网不分波（单波=直布）；3–4 网 2 波；
#: ≥5 网 3 波（对齐 EXP-S2 波次通道 k∈{2,3} 的采样支撑域）。
_WAVE_K_RULE = ((3, 1), (5, 2))   # (上界网数, k)：n<3→1、n<5→2、n≥5→3
_WAVE_K_DEFAULT = 3

#: 档位通道启用上限（EXP-S2 n16 档位崩塌；n≤12 启用）。
TIER_MAX_NETS = 12

#: 档位宽度分界（冻结；与常见板 width_prior 分布对齐：宽/标准/细三档）。
_TIER_WIDTH_BOUNDS = (0.3, 0.2)   # w≥0.3→tier1；0.2≤w<0.3→tier2；w<0.2→tier3


def wave_k(n_nets):
    """波次数 k（冻结规则 _WAVE_K_RULE；n≥规则上界序列末→缺省 3）。"""
    for hi, k in _WAVE_K_RULE:
        if n_nets < hi:
            return k
    return _WAVE_K_DEFAULT


def wave_partition(nets, geo, k=None):
    """波次分块（确定性）：按 (x 中心, id) 排序连续切 k 块（前 r 块各多 1，
    r=n mod k）；块内保持该序（已含 id 字典序稳定）。geo={net_id:(cx,cy)}。

    返回 [ [net,...], ... ]（k 块；k=1 时单块=全集排序）。
    """
    ns = sorted(nets, key=lambda n: (round(float(geo[n][0]), 9), n))
    if k is None:
        k = wave_k(len(ns))
    k = max(1, min(int(k), len(ns)))
    base, rem = divmod(len(ns), k)
    blocks, i = [], 0
    for bi in range(k):
        take = base + (1 if bi < rem else 0)
        blocks.append(list(ns[i:i + take]))
        i += take
    return blocks


def wave_order(nets, geo, k=None):
    """波次展开序（主选通道）：分块拼接（波 0 先布）。"""
    out = []
    for block in wave_partition(nets, geo, k):
        out.extend(sorted(block))
    return out


def tier_of(width):
    """宽度→档位（1=宽先布；分界 _TIER_WIDTH_BOUNDS 冻结）。"""
    w = float(width)
    if w >= _TIER_WIDTH_BOUNDS[0]:
        return 1
    if w >= _TIER_WIDTH_BOUNDS[1]:
        return 2
    return 3


def tier_order(nets, widths):
    """档位展开序（次选通道，n≤12 启用）：序=sorted by (tier, id)。"""
    return sorted(nets, key=lambda n: (tier_of(widths[n]), n))


def probe_swap(order, victim, step):
    """W-4 定向探针交换序：victim 在 order 中的位置与 (pos+step) mod n 交换。

    一步交换（S2「一次交换序测量」）；step=±1/±2…（确定性整数）；victim
    不在序中或 n<2 时返回 None（无交换自由度=探针不适用）。
    """
    if len(order) < 2 or victim not in order:
        return None
    i = order.index(victim)
    j = (i + int(step)) % len(order)
    if j == i:
        return None
    out = list(order)
    out[i], out[j] = out[j], out[i]
    return out
