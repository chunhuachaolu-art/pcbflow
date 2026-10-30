"""MCU AF 表消费（SPEC v1.3 §8.4 pin-swap / §13.2 V2 摄入加速器）。

表本体由 scripts/gen_af_table.py 从钉死的 CubeMX DB XML 转写（out/revc-af/
sources/），本模块只做确定性消费：网名→AF 信号识别 + 互惠同组交换候选
枚举（恒为 proposal-only，SPEC §② 检查1 / HANDOFF §3 确认点 #3）。

识别规则（每条带来源判据，识别不出=unidentified，不虚构）：
- exact      网名与该引脚某 AF 信号名完全相等；
- punct_norm 网名与信号名仅差大小写/下划线/连字符，且在该引脚信号集内唯一；
- gpio_locked 网名 GPIO_PXX 且 XX 与引脚名一致（GPIO 功能引脚锁定，无换脚空间）；
- unconnected 网名 "unconnected-(U1-PXX-PadN)"（同上锁定）；
- power_special 电源/复位/启动/晶振专用网（永不换脚）；
- gpio_mismatch GPIO_PXX 的 XX 与 AF 表引脚名不符（锚点违例，必须如实上抛）。
"""

from __future__ import annotations

import json
import re

AF_TABLE_KIND = "mcu_af_table_full"
_SCHEMA = "1.0"

_GPIO_NET_RE = re.compile(r"^GPIO_(P[A-K][0-9]{1,2}C?)$")
_UNCONNECTED_RE = re.compile(r"^unconnected-\([A-Z0-9]+-([A-Z0-9]+)-Pad(\d+)\)$")
_PUNCT_RE = re.compile(r"[^A-Z0-9]+")
_BUS_SUFFIX_RE = re.compile(r"[0-9]+$")

# 专用网清单（电源/复位/启动/晶振；换脚无意义且违反电气约束）
SPECIAL_NETS = frozenset({
    "GND", "GNDA", "3V3", "1V8", "VDD", "VDDA", "VBAT", "VREF+", "VCAP1",
    "VCAP2", "NRST", "BOOT0", "HSE_IN", "HSE_OUT", "LSE_IN", "LSE_OUT",
})


def _norm(name):
    return _PUNCT_RE.sub("", name.upper())


def load_af_table(path):
    """读入并校验 AF 全表（结构校验失败抛 ValueError，调用方按 BLOCKED 处理）。"""
    with open(path, "rb") as f:
        obj = json.loads(f.read().decode("utf-8"))
    if obj.get("artifact_kind") != AF_TABLE_KIND:
        raise ValueError("not an %s artifact: %r" % (AF_TABLE_KIND, obj.get("artifact_kind")))
    pins = obj["pins"]
    if len(pins) != obj["mcu"]["pin_count"]:
        raise ValueError("pin_count mismatch: %d != %d" % (len(pins), obj["mcu"]["pin_count"]))
    return obj


def table_pins(table):
    return table["pins"]


def pins_by_position(table):
    return {p["position"]: p for p in table["pins"]}


def pin_signal_names(pin):
    return [s["signal"] for s in pin["signals"]]


def pin_af_of(pin, signal):
    for s in pin["signals"]:
        if s["signal"] == signal:
            return s["af"]
    return None


def identify_net(net, pin):
    """识别一只 U1 焊盘上的网功能。返回 {kind, signal, detail}。

    kind ∈ exact/punct_norm/gpio_locked/unconnected/power_special/
    gpio_mismatch/unidentified（unconnected 仍携带 encoded_pin 供锚点核对）。
    """
    if net in SPECIAL_NETS:
        return {"kind": "power_special", "signal": None, "detail": None}
    m = _UNCONNECTED_RE.match(net)
    if m:
        return {"kind": "unconnected", "signal": None, "detail": m.group(1)}
    m = _GPIO_NET_RE.match(net)
    if m:
        encoded = m.group(1)
        if _norm(encoded) == _norm(pin["name"]):
            return {"kind": "gpio_locked", "signal": None, "detail": encoded}
        return {"kind": "gpio_mismatch", "signal": None,
                "detail": "net %s encodes %s but pin is %s" % (net, encoded, pin["name"])}
    names = pin_signal_names(pin)
    if net in names:
        return {"kind": "exact", "signal": net, "detail": None}
    n = _norm(net)
    if n:
        hits = sorted({s for s in names if _norm(s) == n})
        if len(hits) == 1:
            return {"kind": "punct_norm", "signal": hits[0], "detail": net}
        if len(hits) > 1:
            return {"kind": "unidentified", "signal": None,
                    "detail": "ambiguous punct_norm: %s" % hits}
    return {"kind": "unidentified", "signal": None, "detail": None}


_COST_VECTOR = {
    "schematic_edit": 1, "firmware_mux": 1, "external_connector": 0,
    "length_timing": 0, "escape": 0, "via": 0, "congestion": 0,
    "review_risk": 1,
}


def _bus_group(signal):
    """signal_or_bus 启发式：去尾部序号（FMC_A0→FMC_A；SAI2_FS_A 原样）。"""
    return _BUS_SUFFIX_RE.sub("", signal)


def enumerate_swap_candidates(table, u1_pads, evidence=None,
                              connector_nets=None):
    """互惠同组交换候选枚举（proposal-only）。

    候选条件（全部由 AF 表证明，缺一不出）：
      P1 载网 N1 已识别信号 s1，P2 载网 N2 已识别信号 s2，P1≠P2、N1≠N2，
      且 s1 ∈ AF(P2) 同时 s2 ∈ AF(P1)（互惠：双脚都支持对网信号=来源明确
      允许同组交换）。
    evidence: {net: [flag,...]} 仅用于排序/登记，不影响候选成立；
    connector_nets: 触到连接器 ref 的网集（cost_vector.external_connector=1）。
    返回 (candidates, identification)。
    """
    by_pos = pins_by_position(table)
    evidence = evidence or {}
    connector_nets = connector_nets or set()
    ident = {}
    for pad in u1_pads:
        pos = int(pad["num"])
        net = pad["net"]
        pin = by_pos.get(pos)
        if pin is None:
            ident[pos] = {"kind": "unidentified", "signal": None,
                          "detail": "pad %r not in AF table" % pos, "net": net}
            continue
        r = identify_net(net, pin) if net else \
            {"kind": "unidentified", "signal": None, "detail": "no net"}
        r["net"] = net
        ident[pos] = r

    sig_index = {}
    for pos, pin in by_pos.items():
        sig_index[pos] = set(pin_signal_names(pin))

    seeds = sorted((pos for pos, r in ident.items()
                    if r["kind"] in ("exact", "punct_norm")), key=int)
    pairs = []
    same_net_pairs = 0
    one_sided = 0
    for i, p1 in enumerate(seeds):
        s1 = ident[p1]["signal"]
        n1 = ident[p1]["net"]
        for p2 in seeds[i + 1:]:
            s2 = ident[p2]["signal"]
            n2 = ident[p2]["net"]
            c1 = s1 in sig_index[p2]
            c2 = s2 in sig_index[p1]
            if not (c1 and c2):
                one_sided += 1 if (c1 != c2) else 0
                continue
            if n1 == n2:
                same_net_pairs += 1
                continue
            pairs.append((int(p1), int(p2), s1, s2))

    def flags_of(net):
        return sorted(evidence.get(net, []))

    rows = []
    for p1, p2, s1, s2 in pairs:
        n1, n2 = ident[p1]["net"], ident[p2]["net"]
        f1, f2 = flags_of(n1), flags_of(n2)
        cost = dict(_COST_VECTOR)
        cost["external_connector"] = 1 if (n1 in connector_nets or
                                           n2 in connector_nets) else 0
        pin1, pin2 = by_pos[p1], by_pos[p2]
        rows.append({
            "signal_or_bus": _bus_group(s1),
            "from_ref": "U1", "from_pin": pin1["name"], "from_net": n1,
            "to_ref": "U1", "to_pin": pin2["name"], "to_net": n2,
            "allowed_by_source": True,
            "source_refs": ["mcu-af-table-full", "CubeMX STM32H743IITx.xml",
                            "GPIO-STM32H747_gpio_v1_0_Modes.xml"],
            "requires_schematic_edit": True, "requires_firmware_edit": True,
            "requires_pair_update": False, "affected_constraints": [],
            "delta_metrics": {},
            "cost_vector": cost,
            "evidence": {"from_net_flags": f1, "to_net_flags": f2,
                         "mutual_signals": {"s1_at_p2": s1, "s2_at_p1": s2}},
            "af_numbers": {"from": {"pin": p1, "signal": s1,
                                    "af": pin_af_of(pin1, s1)},
                           "to": {"pin": p2, "signal": s2,
                                  "af": pin_af_of(pin2, s2)},
                           "cross": {"p1_has_s2_af": pin_af_of(pin1, s2),
                                     "p2_has_s1_af": pin_af_of(pin2, s1)}},
        })
    rows.sort(key=lambda r: (-(len(r["evidence"]["from_net_flags"]) +
                               len(r["evidence"]["to_net_flags"])),
                             r["from_pin"], r["to_pin"],
                             r["af_numbers"]["from"]["signal"],
                             r["af_numbers"]["to"]["signal"]))
    for i, r in enumerate(rows):
        r["candidate_id"] = "SW-%04d" % (i + 1)
        r["approval"] = "pending"
        r["status"] = "proposal_only"
        # schema 键序对齐 SPEC §8.4 示例（candidate_id 首位）
        ordered = {"candidate_id": r.pop("candidate_id")}
        ordered.update(r)
        rows[i] = ordered

    kinds = {}
    for pos, r in ident.items():
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    unidentified = sorted((r["net"] for r in ident.values()
                           if r["kind"] == "unidentified" and r["net"]))
    identification = {
        "pads_total": len(ident),
        "kinds": dict(sorted(kinds.items())),
        "identified_pads": len(seeds),
        "one_sided_pin_supports": one_sided,
        "same_net_pairs_excluded": same_net_pairs,
        "unidentified_nets": unidentified,
        "mismatches": [{"pad": pos, "detail": r["detail"], "net": r["net"]}
                       for pos, r in sorted(ident.items(), key=lambda kv: int(kv[0]))
                       if r["kind"] == "gpio_mismatch"],
    }
    return rows, identification
