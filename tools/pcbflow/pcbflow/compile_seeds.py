"""⓪ 约束编译种子表（Rev-C，来源 routing-spec-v1 / placement-spec-v1）。

每条种子绑定 source_uri + 行号 + 锚点子串；编译器逐条验证锚点仍存在于
该行（防 spec 漂移）。种子=源文本的结构化转录，params 尽量保留原表
raw 文本以保真。条数目标 40–60（HANDOFF FA1 门）。

未编译为约束的源条款一律登记在 compile_cmd 的 source_notes，不静默丢弃。
"""

from __future__ import annotations

SOURCES = {
    "routing": {
        "source_uri": "design/coreboard/reports/routing-spec-v1.md",
        "source_revision": "v1.0-draft",  # 待评审状态（spec 页眉），如实记录
    },
    "placement": {
        "source_uri": "design/coreboard/reports/placement-spec-v1.md",
        "source_revision": "v1.0-draft",
    },
    "length_script": {
        "source_uri": "design/coreboard/kicad/stm32h743-coreboard-revc/length-report.py",
        "source_revision": "revc-workdir",  # 无版本控制，以 sha256 锁定
    },
}


def S(id, src, line, anchor, ctype, domain, scope, statement, checker,
      earliest, final, mode, authority, waivable, params):
    return {
        "id": id, "source": src, "line": line, "anchor": anchor,
        "type": ctype, "domain": domain, "scope": scope,
        "statement": statement, "checker": checker,
        "earliest_stage": earliest, "final_stage": final,
        "enforcement_mode": mode, "authority": authority, "waivable": waivable,
        "params": params,
    }


# --------------------------------------------------------------------------
# 网络类（routing-spec §2，18 行逐行一条；标题写"16 类"为文档计数漂移，
# 见 source_notes）。线宽/过孔/允许层语义保留原表 raw。
# --------------------------------------------------------------------------
_RAW = {
    "PWR_5V": "1.0（干）/0.5（支）| 0.7/0.4 | F/In2/B(批准)",
    "PWR_3V3": "1.0（干）/0.5（支）| 0.7/0.4 | F/In2/B(批准)",
    "PWR_SW": "1.0 / 0.2（FB 凯尔文）| 0.7/0.4 | F 优先",
    "PWR_MISC": "0.3 | 0.6/0.3 | F",
    "USB_DIFF": "0.20 | 0.6/0.3（整对≤1 次）| F（全程）| G_USB",
    "FMC_CLK": "0.20 | 0.6/0.3 ≤2 | F/In2 | 参考",
    "FMC_CTRL": "0.20 | ≤2 | F/In2 | G_FMC_C",
    "FMC_DATA_L": "0.20 | ≤2 | F/In2 | G_FMC_D",
    "FMC_DATA_H": "0.20 | ≤2 | F/In2 | G_FMC_D",
    "FMC_ADDR": "0.20 | ≤2 | F/In2 | G_FMC_A",
    "SDMMC2": "0.20 | ≤2 | F/In2 | G_EMMC",
    "SDMMC1": "0.20 | ≤2 | F/In2 | G_SD",
    "QSPI": "0.20 | ≤2 | F 优先/In2 | G_QSPI",
    "ETH_RMII": "0.20 | ≤2 | F/In2 | G_ETH",
    "LTDC": "0.15 | ≤2 | F/In2 | G_LTDC",
    "SIG_DEFAULT": "0.15 | 0.6/0.3 | F/In2 | —",
    "ANLG": "0.2（HSE/LSE 0.2）| 0.6/0.3 | F",
    "GND": "铺铜 | 0.6/0.3 缝合 | 全部",
}

_CLASS_ROWS = [
    ("PWR_5V", 29), ("PWR_3V3", 30), ("PWR_SW", 31), ("PWR_MISC", 32),
    ("USB_DIFF", 33), ("FMC_CLK", 34), ("FMC_CTRL", 35),
    ("FMC_DATA_L", 36), ("FMC_DATA_H", 37), ("FMC_ADDR", 38),
    ("SDMMC2", 39), ("SDMMC1", 40), ("QSPI", 41), ("ETH_RMII", 42),
    ("LTDC", 43), ("SIG_DEFAULT", 44), ("ANLG", 45), ("GND", 46),
]

_NETCLASS_SEEDS = [
    S(f"C-{i + 1:04d}", "routing", line, name,
      "hard", "NETCLASS",
      {"net_class": name, "members_raw": _RAW[name].split("|")[0].strip()},
      f"网络类 {name}：线宽/过孔/允许层按 §2 表行执行（raw：{_RAW[name]}）",
      "net_class_rules", 4, 6, "hard", "kicad_cli",
      name == "SIG_DEFAULT",  # 兜底类成员可随结构声明调整 → 可豁免
      {"class": name, "raw": _RAW[name],
       "width_mm_note": "干/支、过孔两值的语义由 checker 实现时定稿",
       "group": ({"USB_DIFF": "G_USB", "FMC_CLK": None, "FMC_CTRL": "G_FMC_C",
                  "FMC_DATA_L": "G_FMC_D", "FMC_DATA_H": "G_FMC_D",
                  "FMC_ADDR": "G_FMC_A", "SDMMC2": "G_EMMC", "SDMMC1": "G_SD",
                  "QSPI": "G_QSPI", "ETH_RMII": "G_ETH", "LTDC": "G_LTDC"}
                 .get(name)),
       **({"sd_cd_note": "SD_CD 归 SDMMC1/G_SD（AMB-4 已批 2026-08-29：具体类优先于兜底类）；"
                         "本行文「SD_CD 外控」视为说明性文字，不构成选择器"}
          if name == "SIG_DEFAULT" else {})},
    )
    for i, (name, line) in enumerate(_CLASS_ROWS)
]

# --------------------------------------------------------------------------
# 等长组（§3 九组逐条；测量口径为共享 params；脚本口径经 ast 提取后对照）
# --------------------------------------------------------------------------
_REF = {
    "G_FMC_D": "FMC_SDCLK", "G_FMC_C": "FMC_SDCLK", "G_FMC_A": "FMC_SDCLK",
    "G_EMMC": "SDMMC2_CK", "G_SD": "SDMMC1_CK", "G_QSPI": "QSPI_CLK",
    "G_ETH": "ETH_REF_CLK", "G_LTDC": "LTDC_PCLK",
}

_LEN_ROWS = [
    ("G_USB", 52, "≤1.0 / 2.5", 1.0, 2.5, "USB2 高速对内偏斜预算"),
    ("G_FMC_D", 53, "±2.5 / ±5.0", 2.5, 5.0, "100MHz SDRAM 时序窗"),
    ("G_FMC_C", 54, "±2.5 / ±5.0", 2.5, 5.0, "同上"),
    ("G_FMC_A", 55, "±5.0 / ±10.0", 5.0, 10.0, "地址窗宽松"),
    ("G_EMMC", 56, "±1.5 / ±3.0", 1.5, 3.0, "eMMC SDR50/HS200（TBD-2）"),
    ("G_SD", 57, "±2.5 / ±5.0", 2.5, 5.0, "SD HS 50MHz"),
    ("G_QSPI", 58, "±2.5 / ±5.0", 2.5, 5.0, "≤100MHz Quad"),
    ("G_ETH", 59, "±2.5 / ±5.0", 2.5, 5.0, "RMII 50MHz"),
    ("G_LTDC", 60, "±5.0 / ±10.0", 5.0, 10.0, "像素时钟 <40MHz"),
]

_MEASUREMENT = {
    "convention": "pad_to_pad_copper_sum",
    "via_equiv_mm": 0.2,
    "note": "焊盘到焊盘铜总长；过孔段按 0 计，每过孔 +0.2mm 折算（§3 口径，与 length-report.py VIA_EQUIV 一致）",
}

# AMB-3 已批（2026-08-29）：USB 约束域覆盖两段，测量约定分段记录
_USB_SEGMENTS = {
    "ruling": "AMB-3 已批（2026-08-29，用户经规划方）：约束域覆盖两段，测量约定分段记录",
    "mcu_side": {"nets": ["USB_DP", "USB_DM"],
                 "measured_by": "length-report.py G_USB（现有脚本口径）"},
    "connector_side": {"nets": ["USB_DP_C", "USB_DM_C"],
                       "measured_by": "pcbflow checker（length_pair_diff，implementation specified）"},
}

_LENGTH_SEEDS = [
    S(f"C-{18 + j + 1:04d}", "routing", line, group,
      "hard", "LENGTH",
      {"group": group, "reference": ("intra_pair" if group == "G_USB" else _REF[group])},
      f"等长组 {group}：{tol_raw}（mm，目标/上限），参考={_REF[group] if group != 'G_USB' else '对内'}",
      "length_pair_diff" if group == "G_USB" else "length_group_match",
      4, 6, "hard", "deterministic_checker", group == "G_EMMC",  # TBD-2 未定 → 可豁免
      {"target_mm": target, "limit_mm": limit, "basis": basis,
       "tbd": "TBD-2" if group == "G_EMMC" else ("TBD-3 严格度" if group == "G_USB" else None),
       "measurement": _MEASUREMENT,
       **({"segments": _USB_SEGMENTS} if group == "G_USB" else {})},
    )
    for j, (group, line, tol_raw, target, limit, basis) in enumerate(_LEN_ROWS)
]

# --------------------------------------------------------------------------
# 拓扑/对称（§4，7 条）
# --------------------------------------------------------------------------
_TOPO_SEEDS = [
    S("C-0028", "routing", 66, "USB 差分对", "hard", "SYMMETRY",
      {"pair": ["USB_DP", "USB_DM"], "pair_connector_side": ["USB_DP_C", "USB_DM_C"],
       "note": "两段均为约束域（AMB-3 已批 2026-08-29）；测量分段记录见 C-0019 params.segments"},
      "USB 差分对（含 _C 段）：整对同层、平行耦合、换层≤1 且成对、对内过孔数相等；禁穿 SW_NODE 区与晶振 3mm 邻域",
      "usb_pair_symmetry", 4, 6, "hard", "deterministic_checker", False,
      {"max_layer_changes": 1, "paired_layer_change": True, "via_count_equal": True,
       "keepout": ["SW_NODE", "crystal_3mm"]}),
    S("C-0029", "routing", 67, "FMC 字节通道对称", "soft", "SYMMETRY",
      {"groups": [["FMC_D0..D7", "FMC_NBL0"], ["FMC_D8..D15", "FMC_NBL1"]]},
      "FMC 两字节组各自同层穿越 U1↔U2 通道（优先整组 In2），组间风格一致（同层比例、过孔数差≤1）",
      "byte_lane_symmetry", 4, 6, "soft", "deterministic_checker", False,
      {"via_count_diff_max": 1, "prefer_layer": "In2.Cu"}),
    S("C-0030", "routing", 68, "FMC 时钟", "hard", "TOPOLOGY",
      {"net": "FMC_SDCLK"},
      "FMC_SDCLK 点对点，禁止分支；落 U2 前最后一段直线进入",
      "net_topology_p2p", 4, 6, "hard", "deterministic_checker", False,
      {"topology": "point_to_point", "no_branch": True}),
    S("C-0031", "routing", 69, "SDMMC2", "diagnostic", "TOPOLOGY",
      {"group": "G_EMMC", "anchor_net": "SDMMC2_CK"},
      "SDMMC2 CK 先行布线并锁定；CMD/D0-3 参照 CK 长度，组内同层优先",
      "process_ck_first", 4, 6, "diagnostic", "deterministic_checker", False,
      {"process": "ck_first_lock"}),
    S("C-0032", "routing", 70, "晶体（HSE/LSE）", "hard", "ZONE",
      {"region": "crystal_zone", "nets": ["HSE_IN", "HSE_OUT", "LSE_IN", "LSE_OUT"]},
      "晶体负载电容对称摆位；保护区 3mm 内无高速线/SW_NODE；走线短而对称",
      "zone_keepout", 3, 6, "hard", "deterministic_checker", False,
      {"keepout_mm": 3.0, "symmetric_placement": True}),
    S("C-0033", "routing", 71, "SW_NODE", "hard", "ZONE",
      {"net": "SW_NODE"},
      "SW_NODE 面积最小化（宽而短）；下方 In1 保持完整 GND；禁止从晶振/USB/analog 下方穿过",
      "sw_node_keepout", 3, 6, "hard", "deterministic_checker", False,
      {"below_layer_intact": "In1.Cu", "keepout_under": ["crystal", "USB", "analog"]}),
    S("C-0034", "routing", 72, "蛇形等长", "soft", "STYLE",
      {"applies_to": "NINE_GROUPS"},
      "蛇形只允许在等长后处理阶段出现；3W 间距规则；45° 折线；整组风格一致；优先放在接收端附近",
      "serpentine_style", 5, 6, "soft", "deterministic_checker", False,
      {"amp_spacing_w": 3.0, "angle_deg": 45, "stage": "post_equalization"}),
]

# --------------------------------------------------------------------------
# 层职责/通道（§5，3 条）
# --------------------------------------------------------------------------
_LAYER_SEEDS = [
    S("C-0035", "routing", 76, "U1↔U2 通道", "hard", "CORRIDOR",
      {"corridor": "U1-U2", "nets": 38},
      "U1↔U2 主通道需求 ≥7.5mm（placement §3）；A0 微调未批准前按现状 1.07mm 打五折执行——未达标布局不得进布线",
      "corridor_capacity", 2, 3, "hard", "deterministic_checker", False,
      {"required_mm": 7.5, "current_mm": 1.07, "precondition": "A0", "half_capacity_rule": True}),
    S("C-0036", "routing", 77, "In2 主干方向", "soft", "LAYER",
      {"layer": "In2.Cu"},
      "In2 主干北南向为主；同向平行间距 ≥0.35mm（0.20 线宽 + 2×clearance）",
      "layer_trunk_direction", 4, 6, "soft", "deterministic_checker", False,
      {"min_parallel_spacing_mm": 0.35}),
    S("C-0037", "routing", 78, "F.Cu 只做逃逸", "soft", "LAYER",
      {"layer": "F.Cu"},
      "F.Cu 只做逃逸（≤3mm）+ 关键组局部直连；长距一律下 In2",
      "fc_escape_limit", 4, 6, "soft", "deterministic_checker", False,
      {"max_escape_mm": 3.0}),
]

# --------------------------------------------------------------------------
# 地平面完整性（§6，5 条；§6.2 并入 C-0038 params）
# --------------------------------------------------------------------------
_PLANE_SEEDS = [
    S("C-0038", "routing", 83, "In1/B 不分割", "hard", "PLANE",
      {"layers": ["In1.Cu", "B.Cu"]},
      "In1/B 不分割、不挖槽（安装孔/过孔除外）；关键类信号不得跨平面开槽（遵守本条自动满足，§6.2 并入）",
      "plane_integrity", 4, 6, "hard", "kicad_cli", False,
      {"exceptions": ["mounting_holes", "vias"], "subsumes": "§6.2"}),
    S("C-0039", "routing", 85, "GND 缝合过孔", "soft", "PLANE",
      {"net": "GND"},
      "GND 缝合过孔目标网格 ≤8mm；重点区域（J5 外壳、U3 下方、连接器排）≤4mm",
      "stitching_grid", 3, 6, "soft", "deterministic_checker", False,
      {"grid_mm": 8.0, "dense_mm": 4.0, "dense_regions": ["J5_shell", "U3_below", "connector_rows"]}),
    S("C-0040", "routing", 86, "In1 例外条款", "hard", "PLANE",
      {"layers": ["In1.Cu"]},
      "In1 允许经书面批准的 ≤2mm 短跳，须成对回流孔伴随",
      "in1_jump_rule", 4, 6, "hard", "deterministic_checker", True,
      {"max_jump_mm": 2.0, "requires": ["written_approval", "paired_return_vias"]}),
    S("C-0041", "routing", 87, "J5 USB-C 外壳焊盘", "hard", "PLANE",
      {"ref": "J5", "net": "GND"},
      "J5 外壳焊盘每盘 1 个 GND 直连孔",
      "connector_shell_via", 4, 6, "hard", "deterministic_checker", False,
      {"gnd_vias_per_shell_pad": 1}),
    S("C-0042", "routing", 88, "GNDA/VDDA 模拟角", "hard", "PLANE",
      {"nets": ["GNDA", "VDDA"], "region": "analog_corner"},
      "GNDA 单点接地（0Ω/磁珠按原理图）；模拟区内禁止数字线穿越",
      "analog_zone_rule", 3, 6, "hard", "deterministic_checker", False,
      {"single_point_ground": True, "no_digital_crossing": True}),
]

# --------------------------------------------------------------------------
# 电源分配（§7 + placement §2.1/§2.5 双源，4 条）
# --------------------------------------------------------------------------
_POWER_SEEDS = [
    S("C-0043", "routing", 92, "5V（USB/排针）", "hard", "POWER",
      {"rails": ["5V", "3V3"], "source": "U3"},
      "5V → U3 TPS62085 → 3V3：主干 1.0mm、负载端 0.5mm 分支；单点树状，不环回",
      "power_tree_topology", 3, 6, "hard", "deterministic_checker", False,
      {"trunk_width_mm": 1.0, "branch_width_mm": 0.5, "no_loops": True}),
    S("C-0044", "placement", 33, "2.1 去耦电容", "hard", "POWER",
      {"scope": "decoupling_caps", "dual_source": ["routing §7.2", "placement §2.1"]},
      "去耦电容到所属电源焊盘 ≤2.0mm（上限 3.0mm）；每 VDD 引脚必有一颗达标",
      "decouple_proximity", 3, 6, "hard", "deterministic_checker", False,
      {"target_mm": 2.0, "limit_mm": 3.0, "per_vdd_pin": True}),
    S("C-0045", "routing", 94, "EMMC_VSEL", "soft", "POWER",
      {"net": "EMMC_VSEL"},
      "EMMC_VSEL：0.3mm，星型从选择器件出发",
      "star_topology", 4, 6, "soft", "deterministic_checker", False,
      {"width_mm": 0.3, "topology": "star"}),
    S("C-0046", "placement", 37, "2.5 buck 功率回路", "hard", "POWER",
      {"ref": "U3", "dual_source": ["routing §7.4", "placement §2.5"]},
      "buck 功率回路（Cin-SW-L-Cout 外包络）≤15×10mm（上限 20×12mm）；输入电容-SW-输出电容紧邻",
      "buck_loop_area", 3, 6, "hard", "deterministic_checker", False,
      {"target_mm2": [15, 10], "limit_mm2": [20, 12]}),
]

# --------------------------------------------------------------------------
# 签核门（§8，2 条）+ placement 就近（§2 余下 4 条）
# --------------------------------------------------------------------------
_SIGNOFF_SEEDS = [
    S("C-0047", "routing", 101, "| DRC | kicad-cli", "hard", "SIGNOFF",
      {"board": "stm32h743-coreboard-revc"},
      "kicad-cli pcb drc 错误 0；豁免项单列（U3 局部规则区、J5 板边两项需显式批准保留→⑥ waiver 台账）",
      "kicad_drc_errors", 4, 6, "hard", "kicad_cli", False,
      {"profile": "severity-all", "predeclared_waiver_candidates": ["U3_local_rules", "J5_board_edge_0.45mm"]}),
    S("C-0048", "routing", 102, "unconnected_items", "hard", "SIGNOFF",
      {"board": "stm32h743-coreboard-revc"},
      "unconnected_items = 0（kicad-cli）",
      "kicad_unconnected", 4, 6, "hard", "kicad_cli", False, {}),
]

_PLACE_PROX_SEEDS = [
    S("C-0049", "placement", 34, "2.2 晶振到", "hard", "PLACEMENT",
      {"scope": "crystal_cluster"},
      "晶振到 MCU 晶振引脚 ≤3.0mm（上限 4.0mm）；负载电容 ≤2.0mm",
      "crystal_proximity", 3, 6, "hard", "deterministic_checker", False,
      {"target_mm": 3.0, "limit_mm": 4.0, "load_caps_mm": 2.0}),
    S("C-0050", "placement", 35, "2.3 功能簇质心", "soft", "PLACEMENT",
      {"scope": "functional_clusters"},
      "功能簇质心到目标连接器：簇内最远网 ≤40mm 走线估计（上限 60mm）",
      "cluster_centroid", 3, 6, "soft", "deterministic_checker", False,
      {"target_mm": 40.0, "limit_mm": 60.0}),
    S("C-0051", "placement", 36, "2.4 USB 差分对端到端", "hard", "PLACEMENT",
      {"scope": "USB_DP..DM MCU→J5"},
      "USB 差分对端到端（MCU→J5）≤25mm（上限 35mm）",
      "usb_pair_length_e2e", 3, 6, "hard", "deterministic_checker", False,
      {"target_mm": 25.0, "limit_mm": 35.0}),
    S("C-0052", "placement", 38, "2.6 总线同组器件", "hard", "PLACEMENT",
      {"scope": "bus_groups"},
      "总线同组器件引脚面对引脚面（U1 南排 vs U2、U1 东西排 vs 连接器）必须满足",
      "pin_face_orientation", 3, 6, "hard", "deterministic_checker", False, {}),
]

_PLACE_MISC_SEEDS = [
    S("C-0053", "placement", 42, "需求通道宽", "hard", "CORRIDOR",
      {"scope": "all_corridors"},
      "通道预算公式：ceil(N/2 层)×0.35mm + 0.6mm 余量；任何两器件净空 < 需求宽的布局不得进布线；通道区禁第三方侵入",
      "corridor_budget_formula", 2, 3, "hard", "deterministic_checker", False,
      {"routing_layers": 2, "pitch_mm": 0.35, "margin_mm": 0.6, "hard_rule": True}),
    S("C-0054", "placement", 80, "USB-C（J5）外壳区", "hard", "ZONE",
      {"ref": "J5"},
      "J5 外壳区 5mm 内无晶振/时钟线",
      "j5_clock_keepout", 3, 6, "hard", "deterministic_checker", False,
      {"keepout_mm": 5.0, "banned": ["crystal", "clock_lines"]}),
    S("C-0055", "placement", 81, "安装孔禁布区", "hard", "ZONE",
      {"scope": "mounting_holes"},
      "安装孔禁布区 2mm（铜与丝印）",
      "mounting_hole_keepout", 3, 6, "hard", "deterministic_checker", False,
      {"keepout_mm": 2.0, "applies_to": ["copper", "silkscreen"]}),
    S("C-0056", "placement", 87, "7.1 元件间距", "hard", "DFM",
      {"scope": "all_footprints"},
      "0402/0603 相互 ≥0.8mm（手焊）/0.5mm（机贴，TBD-P2 取严者）；IC 身侧 ≥1.0mm",
      "dfm_component_spacing", 3, 6, "hard", "deterministic_checker", False,
      {"chip_to_chip_mm": {"hand": 0.8, "machine": 0.5}, "ic_side_mm": 1.0, "tbd": "TBD-P2"}),
    S("C-0057", "placement", 88, "7.2 方向一致性", "soft", "DFM",
      {"scope": "clusters"},
      "同簇同封装统一 0°/90°，极性/一脚标识方向统一；去耦电容全板同向",
      "dfm_orientation", 3, 6, "soft", "deterministic_checker", False, {}),
    S("C-0058", "placement", 89, "7.3 单面贴装", "hard", "DFM",
      {"scope": "all_smd"},
      "全部贴片件 F 面（连接器可 T 面）",
      "dfm_single_side", 3, 6, "hard", "deterministic_checker", False,
      {"side": "F.Cu", "exception": ["connectors"]}),
    S("C-0059", "placement", 91, "7.5 测试点", "soft", "DFM",
      {"nets": ["5V", "3V3", "NRST", "BOOT0", "SWCLK", "SWDIO", "USB_DP", "USB_DM"]},
      "关键网预留 ≥0.9mm 裸铜测试点，2.54 间距兼容（TBD-P4：最小集）",
      "dfm_testpoints", 3, 6, "soft", "deterministic_checker", False,
      {"pad_mm": 0.9, "pitch_compatible": 2.54, "tbd": "TBD-P4"}),
    S("C-0060", "placement", 92, "7.6 焊盘热焊盘", "soft", "DFM",
      {"scope": "connector_gnd_and_power"},
      "连接器 GND 盘保持花焊盘（≥2 辐条），大电流盘实连",
      "dfm_thermal_relief", 3, 6, "soft", "deterministic_checker", False,
      {"spokes_min": 2}),
]

SEEDS = (_NETCLASS_SEEDS + _LENGTH_SEEDS + _TOPO_SEEDS + _LAYER_SEEDS
         + _PLANE_SEEDS + _POWER_SEEDS + _SIGNOFF_SEEDS
         + _PLACE_PROX_SEEDS + _PLACE_MISC_SEEDS)

# --------------------------------------------------------------------------
# 网类匹配模式（有序：具体类优先，SIG_DEFAULT 兜底最后）
# _p 生成 ^name$ 精确匹配；LTDC 按前缀（spec 通配 LTDC_*，成员数见 AMB-2）
# --------------------------------------------------------------------------
def _p(*names):
    return ["^" + n.replace("+", r"\+") + "$" for n in names]

NETCLASS_PATTERNS = [
    ("PWR_5V", _p("5V", "5V_HDR", "5V_USB", "VBUS_RAW")),
    ("PWR_3V3", _p("3V3")),
    ("PWR_SW", _p("SW_NODE", "FB_NODE")),
    ("PWR_MISC", _p("EMMC_VSEL", "VBAT", "VBAT_CHG", "VCAP1", "VCAP2")),
    ("USB_DIFF", _p("USB_DP", "USB_DM", "USB_DP_C", "USB_DM_C")),
    ("FMC_CLK", _p("FMC_SDCLK")),
    ("FMC_CTRL", _p("FMC_SDNCAS", "FMC_SDNRAS", "FMC_SDNWE", "FMC_SDNE0", "FMC_SDCKE0")),
    ("FMC_DATA_L", ["^FMC_D[0-7]$", "^FMC_NBL0$"]),
    ("FMC_DATA_H", ["^FMC_D(?:8|9|1[0-5])$", "^FMC_NBL1$"]),
    ("FMC_ADDR", ["^FMC_A(?:0|1|2|3|4|5|6|7|8|9|10|11|12)$", "^FMC_BA[01]$"]),  # A12 纳入=AMB-1 已批（2026-08-29）
    ("SDMMC2", _p("SDMMC2_CK", "SDMMC2_CMD") + ["^SDMMC2_D[0-3]$"]),
    ("SDMMC1", _p("SDMMC1_CK", "SDMMC1_CMD", "SD_CD") + ["^SDMMC1_D[0-3]$"]),
    ("QSPI", _p("QSPI_CLK", "QSPI_NCS") + ["^QSPI_IO[0-3]$"]),
    ("ETH_RMII", _p("ETH_REF_CLK", "ETH_CRS_DV", "ETH_MDC", "ETH_MDIO", "ETH_TX_EN",
                    "ETH_RXD0", "ETH_RXD1", "ETH_TXD0", "ETH_TXD1")),
    ("ANLG", _p("VDDA", "GNDA", "HSE_IN", "HSE_OUT", "LSE_IN", "LSE_OUT")
     + ["^ADC_A[0-3]$", r"^VREF\+$"]),
    ("GND", ["^GND$"]),
    ("LTDC", ["^LTDC_"]),  # 前缀通配（spec"23 网"vs 脚本 19 名 → AMB-2）
]
CATCH_ALL_CLASS = "SIG_DEFAULT"  # spec §2"其余全部"

# --------------------------------------------------------------------------
# 歧义登记（存在未决歧义 ⇒ compile 不得宣称完成 → envelope blocked，SPEC §⓪）
# FA2 消费 2026-08-29 用户裁决（经规划方转达）：AMB-1..4 全部 resolved。
# resolved 项仍保留 spec/script 双侧事实与 diff（不隐藏），并带批准人/复审。
# --------------------------------------------------------------------------
_RULING_META = {
    "decided_on": "2026-08-29",
    "approver": "用户（经规划方转达）",
    "review": "下一 rev 强制复审（waiver 台账口径）",
}

AMBIGUITIES = [
    {
        "id": "AMB-1", "kind": "selector_membership", "status": "resolved",
        "title": "FMC_A12 缺席 routing-spec §2 FMC_ADDR 行",
        "spec_side": "FMC_A0..A11 + BA0/BA1（§2 行）",
        "script_side": "G_FMC_A = FMC_A0..A12（13 根）+ BA0/BA1",
        "proposal": "纳入 FMC_ADDR 类并记差异来源 routing-spec 缺行（规划方预填建议，待人工批准）",
        "decision": "纳入 FMC_ADDR 类；差异来源=routing-spec §2 缺行，登记不隐藏",
        "applied_to": ["NETCLASS_PATTERNS FMC_ADDR +A12",
                       "coverage.catch_all_only_nets 移出 FMC_A12",
                       "structures 走廊网数 38→39（衍生预算见 mapping）"],
        "constraint_refs": ["C-0010", "C-0022"],
        **_RULING_META,
    },
    {
        "id": "AMB-2", "kind": "selector_membership", "status": "resolved",
        "title": "LTDC 成员数：spec 称 23 网 vs length-report.py 19 名",
        "spec_side": "LTDC_*（23 网）（§2 行）",
        "script_side": "G_LTDC 枚举 R0-4/G0-5/B0-4/DE/HSYNC/VSYNC 共 19",
        "proposal": "canonical 以 Rev-C 网表实际为准，spec 差异登记 coverage 并 waiver 复审（规划方预填建议）",
        "decision": "canonical 以 Rev-C 网表实际为准（板上 LTDC_* 20 网=PCLK 参考+19 成员）；"
                    "spec「23 网」为未枚举声明，登记差异并 waiver 复审；"
                    "脚本枚举含板上不存在的 8 名（R0-2/G0-1/B0-2）按网表修正",
        "applied_to": ["structures.mapping.timing_groups G_LTDC canonical_members",
                       "coverage.nine_group_comparison G_LTDC resolved_with_diff"],
        "constraint_refs": ["C-0015", "C-0027"],
        **_RULING_META,
    },
    {
        "id": "AMB-3", "kind": "scope_coverage", "status": "resolved",
        "title": "USB 测量段：spec 含连接器侧 _C 对，脚本 G_USB 只测 MCU 侧",
        "spec_side": "USB_DIFF = USB_DP/DM + USB_DP_C/USB_DM_C（§2、§4.1 含 _C 段）",
        "script_side": "G_USB = [USB_DP, USB_DM]（MCU 侧）",
        "proposal": "约束域覆盖两段，测量约定分段记录（规划方预填建议）",
        "decision": "约束域覆盖两段（MCU 段+连接器段），测量约定分段记录（C-0019 params.segments）",
        "applied_to": ["C-0019 params.segments", "C-0028 scope.note"],
        "constraint_refs": ["C-0005", "C-0019", "C-0028"],
        **_RULING_META,
    },
    {
        "id": "AMB-4", "kind": "selector_overlap", "status": "resolved",
        "title": "SD_CD 双类归属：SDMMC1 行显式含 SD_CD，SIG_DEFAULT 行文又列\"SD_CD 外控\"",
        "spec_side": "SDMMC1 行含 SD_CD；SIG_DEFAULT 行文含\"SD_CD 外控等\"",
        "script_side": "G_SD 含 SD_CD",
        "proposal": "具体类优先于兜底类：SD_CD 归 SDMMC1/G_SD；SIG_DEFAULT 行文视为说明性文字（FA1 新发现，待人工裁决）",
        "decision": "具体类优先于兜底类：SD_CD 归 SDMMC1/G_SD；SIG_DEFAULT 行文视为说明性文字"
                    "（C-0016 params.sd_cd_note；与 FA1 已实现的匹配顺序一致，无行为变更）",
        "applied_to": ["C-0016 params.sd_cd_note"],
        "constraint_refs": ["C-0012", "C-0016", "C-0024"],
        **_RULING_META,
    },
]

# --------------------------------------------------------------------------
# 源待定项（两 spec §10 原样登记；裁决权在人工评审）
# --------------------------------------------------------------------------
PENDING_DECISIONS = [
    {"id": "TBD-1", "source": "routing", "line": 119,
     "item": "板厂与叠层参数（阻抗几何定稿）", "impact": ["impedance_targets", "C-0005 线宽几何"]},
    {"id": "TBD-2", "source": "routing", "line": 120,
     "item": "eMMC 速率模式", "impact": ["C-0023 (G_EMMC) 允差"]},
    {"id": "TBD-3", "source": "routing", "line": 121,
     "item": "USB 用途（FS/HS）", "impact": ["C-0019 (G_USB) 允差严格度"]},
    {"id": "TBD-4", "source": "routing", "line": 122,
     "item": "A0 布局微调是否执行", "impact": ["C-0035 通道容量"]},
    {"id": "TBD-5", "source": "routing", "line": 123,
     "item": "J5 板边 0.45mm 两项豁免", "impact": ["C-0047 waiver 台账"]},
    {"id": "TBD-P1", "source": "placement", "line": 113,
     "item": "板轮廓与连接器底板对接约束", "impact": ["C-0053 走线估计分母"]},
    {"id": "TBD-P2", "source": "placement", "line": 114,
     "item": "焊接工艺（手焊/机贴）", "impact": ["C-0056 间距取值"]},
    {"id": "TBD-P3", "source": "placement", "line": 115,
     "item": "J5 USB-C 位置", "impact": ["C-0051/C-0054"]},
    {"id": "TBD-P4", "source": "placement", "line": 116,
     "item": "测试点最小集", "impact": ["C-0059"]},
]
