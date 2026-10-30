# -*- coding: utf-8 -*-
"""走廊容量账本（P0 四模块之一）。

V2 口径（V2 场景 J2/J3）：占用核算 = 铜宽 + 网间 0.5mm 间距（相邻对计一次）；
ribbon 整体按声明占用（如 3.3mm）计。判定语义（溢出是否构成违例）在 v5.drc。
"""
from .. import canonical

NET_NET_SPACING = 0.5


class CapacityEntry:
    """走廊内一个占用条目。declared_occupancy 优先（ribbon）；否则用铜宽。"""

    def __init__(self, net_id, copper_width, declared_occupancy=None, span=None):
        self.net_id = net_id
        self.copper_width = copper_width
        self.declared_occupancy = declared_occupancy
        self.span = span  # 铜带 [lo, hi]，可选

    @property
    def occupancy(self):
        if self.declared_occupancy is not None:
            return self.declared_occupancy
        return self.copper_width

    def as_dict(self):
        return {
            "net_id": self.net_id,
            "copper_width": self.copper_width,
            "declared_occupancy": self.declared_occupancy,
            "span": list(self.span) if self.span else None,
        }


def corridor_occupancy(entries):
    """顺序占用总和：Σ条目占用 + 0.5×(相邻对数)。单条目无网间间距。

    条目顺序即布设顺序（调用方保证确定性：按注册序）。
    """
    entries = list(entries)
    if not entries:
        return 0.0
    total = sum(e.occupancy for e in entries)
    return round(total + NET_NET_SPACING * (len(entries) - 1), 10)


def check_fits(entries, capacity_mm):
    """容量核对：返回 dict（占用/容量/余量/是否放入）。放入与否是事实核算；
    溢出的违例判定由 v5.drc 作出。"""
    used = corridor_occupancy(entries)
    return {
        "capacity_mm": capacity_mm,
        "occupancy_mm": used,
        "slack_mm": round(capacity_mm - used, 10),
        "fits": used <= capacity_mm + 1e-9,
        "entries": [e.as_dict() for e in entries],
    }


def remaining_capacity(entries, capacity_mm):
    return round(capacity_mm - corridor_occupancy(entries), 10)


def ledger_for_layer(entries_by_corridor, capacity_by_corridor):
    """逐走廊账本：确定性输出（键序固定），供叠加层与盲包用。"""
    ledger = {}
    for cid in sorted(entries_by_corridor):
        ledger[cid] = check_fits(entries_by_corridor[cid], capacity_by_corridor[cid])
    return ledger


def ledger_bytes(entries_by_corridor, capacity_by_corridor) -> bytes:
    return canonical.canonical_json(ledger_for_layer(entries_by_corridor, capacity_by_corridor))
