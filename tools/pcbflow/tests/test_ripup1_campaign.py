"""RIPUP-1 单测：战役纯函数核（拆铜偏好序/批判定/账本）。

只测纯函数与账本逻辑（合成 DRC JSON + 合成 blocks 字符串），零 live 板
接触、零落盘、零子进程。"""

from __future__ import annotations

from pcbflow import ripup1_campaign as rc


# ---- 拆铜偏好序（硬门 4） ----------------------------------------------------
def test_net_class_power_ground():
    for n in ("GND", "GNDA", "3V3", "5V", "SW_NODE", "VDDA", "VBAT", "VDD"):
        assert rc.net_class(n) == "power_ground", n
    assert rc.is_power_ground("GNDA") and rc.is_power_ground("GNDX")


def test_net_class_signal():
    for n in ("ETH_REF_CLK", "FMC_D12", "SDMMC1_D0", "GPIO_PH4", "LSE_OUT",
              "ADC_A3", "FMC_SDCKE0", "SWDIO"):
        assert rc.net_class(n) == "signal", n
    assert rc.is_power_ground("") is False
    assert rc.is_power_ground(None) is False


def test_ordered_ripup_candidates_deterministic():
    blocks = [
        "[ETH_REF_CLK] 走线 [ETH_REF_CLK]（封堵归因）",
        "[ETH_REF_CLK] 走线 [ETH_REF_CLK]（封堵归因）",
        "[FMC_SDCKE0] U1 焊盘 43 [FMC_SDCKE0]（封堵归因）",
        "[GND] J4 焊盘 3 [GND]（封堵归因）",          # 禁拆网必须滤除
        "[SWDIO] 自身铜不计",                          # 本网必须滤除
        "netless 铜不带网名标记不可拆",                # 无网名不入候选
    ]
    out = rc.ordered_ripup_candidates(blocks, own="SWDIO")
    assert out == ["ETH_REF_CLK", "FMC_SDCKE0"]   # 次数降序 + 字典序


def test_partition_candidates_signal_first_preserves_order():
    ordered = ["ADC_A3", "GNDX", "VDDA", "3V3"]   # GNDX 前缀族=电源地
    part = rc.partition_candidates(ordered)
    assert part["signal"] == ["ADC_A3"]
    assert part["power_ground"] == ["GNDX", "VDDA", "3V3"]


# ---- 批判定（硬门 1+2） ------------------------------------------------------
def _drc(viol, unconn_nets):
    """合成 DRC JSON：unconnected 条目按网名构造（描述带 [NET]）。"""
    unconn = [{"type": "unconnected_items", "severity": "error",
               "items": [{"description": "走线 [%s] (F.Cu)" % n},
                         {"description": "焊盘 1 [%s]" % n}]}
              for n in unconn_nets]
    return {"violations": viol, "unconnected_items": unconn}


_BASE_VIOL = [{"type": "copper_edge_clearance", "severity": "error",
               "items": [{"description": "board edge"}]}]


def test_verdict_accepts_clean_close():
    base = _drc(_BASE_VIOL, ["SWDIO", "GNDA", "FMC_D12"])
    cand = _drc(_BASE_VIOL, ["GNDA", "FMC_D12"])   # SWDIO 关闭，其余持平
    v = rc.campaign_batch_verdict(base, cand, prev_unconn=3)
    assert v["accepted"] is True
    assert v["new_errors_vs_baseline"] == 0
    assert v["unconnected"] == 2 and v["unconnected_prev"] == 3
    assert v["unconnected_monotonic"] is True
    assert v["closed_nets"] == ["SWDIO"]
    assert v["newly_dangling_nets"] == []


def test_verdict_rejects_unconn_increase():
    base = _drc(_BASE_VIOL, ["SWDIO", "GNDA"])
    cand = _drc(_BASE_VIOL, ["SWDIO", "GNDA", "ETH_REF_CLK"])
    v = rc.campaign_batch_verdict(base, cand, prev_unconn=2)
    assert v["accepted"] is False
    assert v["unconnected_monotonic"] is False
    assert v["newly_dangling_nets"] == ["ETH_REF_CLK"]


def test_verdict_rejects_ripped_net_lost_connectivity():
    """拆 A 补 B 丢 A：被拆网新增悬空 → 否决（硬门 1 核心场景）。"""
    base = _drc(_BASE_VIOL, ["VBAT"])
    cand = _drc(_BASE_VIOL, ["VBAT", "LSE_OUT"])   # LSE_OUT 被拆后丢连通
    v = rc.campaign_batch_verdict(base, cand, prev_unconn=1)
    assert v["accepted"] is False
    assert v["newly_dangling_nets"] == ["LSE_OUT"]
    assert v["unconnected"] == 2 and v["unconnected_prev"] == 1


def test_verdict_rejects_new_severity_error():
    base = _drc(_BASE_VIOL, ["SWDIO"])
    new_err = {"type": "clearance", "severity": "error",
               "items": [{"description": "SWDIO;FMC_D12"}]}
    cand = _drc(_BASE_VIOL + [new_err], [])
    v = rc.campaign_batch_verdict(base, cand, prev_unconn=1)
    assert v["accepted"] is False
    assert v["new_errors_vs_baseline"] == 1


def test_verdict_new_warning_does_not_block():
    base = _drc(_BASE_VIOL, ["SWDIO"])
    warn = {"type": "silk_over_copper", "severity": "warning",
            "items": [{"description": "x"}]}
    cand = _drc(_BASE_VIOL + [warn], [])
    v = rc.campaign_batch_verdict(base, cand, prev_unconn=1)
    assert v["accepted"] is True
    assert v["new_vs_baseline"] == 1
    assert v["new_errors_vs_baseline"] == 0


# ---- 批装配与批操作数（硬门 3） ----------------------------------------------
def test_batch_nets_operand_count():
    assert rc.batch_nets(["SWDIO"], ["ADC_A3"]) == ["ADC_A3", "SWDIO"]
    assert rc.batch_nets(["SWDIO"], [None]) == ["SWDIO"]
    assert rc.batch_nets([], []) == []


def test_assemble_batch_rip_and_append():
    """拆被拆网全部顶层铜 + 追加目标/重布铜（zones 不在匹配面）。"""
    from pcbflow import fb1_experiment

    def _seg(net, uuid, x1, y1, x2, y2):
        return ("\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n"
                "\t\t(width 0.2)\n\t\t(layer \"F.Cu\")\n"
                "\t\t(net \"%s\")\n\t\t(uuid \"%s\")\n\t)\n"
                % (x1, y1, x2, y2, net, uuid))

    text = ("(kicad_pcb\n"
            "\t(net 0 \"\")\n\t(net 1 \"SWDIO\")\n\t(net 2 \"ADC_A3\")\n"
            + _seg("ADC_A3", "u-a1", "1", "1", "5", "1")
            + _seg("ADC_A3", "u-a2", "5", "1", "9", "1")
            + "\t(zone (net 2) (net_name \"ADC_A3\") (layers \"F.Cu\"))\n"
            + ")")
    target = {"net": "SWDIO", "width": 0.15, "via_size": 0.6,
              "via_drill": 0.3,
              "segments": [[0, 1.0, 3.0, 5.0, 3.0]], "vias": []}
    replan = {"net": "ADC_A3", "width": 0.2, "via_size": 0.6,
              "via_drill": 0.3,
              "segments": [[0, 1.0, 0.5, 5.0, 0.5],
                           [0, 5.0, 0.5, 9.0, 0.5]], "vias": []}
    cand, spans = rc.assemble_batch(text, target, [("ADC_A3", replan)])
    assert spans == 2
    assert fb1_experiment.count_net_nodes(cand, "ADC_A3")["total"] == 2  # 重布
    assert fb1_experiment.count_net_nodes(cand, "SWDIO")["total"] == 1
    assert "(zone" in cand            # zones 原样保留
    assert "u-a1" not in cand and "u-a2" not in cand  # 旧铜按 uuid 确删


def test_assemble_batch_missing_replan_fails_closed():
    """硬门 1：被拆网缺同批重布 → 装配失败（None），绝不拆而不补。"""
    target = {"net": "SWDIO", "width": 0.15, "via_size": 0.6,
              "via_drill": 0.3, "segments": [], "vias": []}
    cand, spans = rc.assemble_batch("(kicad_pcb\n)", target,
                                    [("ADC_A3", None)])
    assert cand is None and spans == 0


def test_assemble_batch_no_rip_is_pure_append():
    text = "(kicad_pcb\n\t(net 0 \"\")\n)"
    target = {"net": "SWDIO", "width": 0.15, "via_size": 0.6,
              "via_drill": 0.3,
              "segments": [[0, 1.0, 3.0, 5.0, 3.0]], "vias": []}
    cand, spans = rc.assemble_batch(text, target, [])
    assert spans == 0
    assert "SWDIO" in cand


# ---- 账本（行结果纯函数） ----------------------------------------------------
def test_row_account_unknown_row():
    norm = {"ok": False, "fail": "A* 不可达", "blocks": ["[VDDA] x"],
            "ripup_set": []}
    acc = rc.row_account("RPL-039", "GNDA", norm, {})
    assert acc["status"] == "UNKNOWN"
    assert acc["ripped_nets"] == []
    assert acc["si_review_required"] is False
    assert acc["batch_nets"] == ["GNDA"]


def test_row_account_sat_power_rip_flags_si_review():
    norm = {"ok": True, "fail": None, "blocks": [],
            "length_mm": 12.5,
            "ripup_set": [
                {"net": "GPIO_PH4", "class": "signal",
                 "si_review_required": False,
                 "replan": {"length_mm": 8.0}},
                {"net": "VDDA", "class": "power_ground",
                 "si_review_required": True,
                 "replan": {"length_mm": 30.1}},
            ]}
    acc = rc.row_account("RPL-039", "GNDA", norm,
                         {"GPIO_PH4": {"segment": 2, "via": 1, "total": 3},
                          "VDDA": {"segment": 4, "via": 0, "total": 4}})
    assert acc["status"] == "SAT"
    assert acc["ripped_nets"] == ["GPIO_PH4", "VDDA"]
    assert acc["ripped_classes"] == ["signal", "power_ground"]
    assert acc["si_review_nets"] == ["VDDA"]
    assert acc["si_review_required"] is True
    assert acc["removed_nodes"]["VDDA"]["total"] == 4
    assert acc["route_length_mm"] == 12.5
    assert acc["replan_length_mm"] == {"GPIO_PH4": 8.0, "VDDA": 30.1}
    assert acc["batch_nets"] == ["GNDA", "GPIO_PH4", "VDDA"]
