# -*- coding: utf-8 -*-
"""pcbagent 全局常量（SPEC §6：所有阈值/系数集中于此，禁止散落魔法数）。

规则数值来源：Rev-C 工程 .kicad_pro 的 design_settings.rules / rule_severities /
net_settings.classes（2026-08-28 读取）。改板规则时同步改这里。
"""

# ---- 层常量（KiCad 10：F=0/B=2/In1=4/In2=6，HANDOFF §3 坑 2）----
LAYER_F, LAYER_B, LAYER_IN1, LAYER_IN2 = 0, 2, 4, 6
SIGNAL_LAYERS = (LAYER_F, LAYER_IN2)   # Rev-C 信号只走 F/In2
PLANE_LAYERS = (LAYER_IN1, LAYER_B)    # Rev-C In1/B 为 GND 平面（zones）

# ---- 板级 DRC 规则（.kicad_pro design_settings.rules）----
BOARD_MIN_CLEARANCE = 0.15          # min_clearance
MIN_TRACK_WIDTH = 0.15              # min_track_width
MIN_HOLE_CLEARANCE = 0.25           # min_hole_clearance（error；所有孔-铜，含 NPTH）
MIN_HOLE_TO_HOLE = 0.25             # min_hole_to_hole（severity=warning）
# CLI 对圆形铜（过孔盘、钻孔）做内接多边形化后再测间距（max_error≈0.005mm），
# 线段/焊盘保持精确形状——B1 门五组边界探针实证（2026-08-28）：
#   via盘-走线 0.199mm 判合法（0.2−0.005）、NPTH孔-铜 0.2495 判合法（0.25−0.005）、
#   焊盘圆-走线 0.199 判违规（精确）。L1 对每个参与判定的圆形加等效余量。
CIRCLE_POLY_SAGITTA = 0.005
MIN_COPPER_EDGE_CLEARANCE = 0.5     # min_copper_edge_clearance（error）
MIN_VIA_DIAMETER = 0.45             # min_via_diameter
MIN_VIA_ANNULAR_WIDTH = 0.1         # min_via_annular_width
MIN_THROUGH_HOLE_DIAMETER = 0.3     # min_through_hole_diameter

# ---- L1 行为开关 ----
# CLI 的 hole_to_hole severity=warning：默认不计入 error 级裁决口径
HOLE_TO_HOLE_ENFORCE = False
# CLI 以 --refill-zones 为真值口径：新铜旁的 zone 填充会重灌让位，故候选铜/孔
# 对 GND 平面 zone 不作静态间距否决；但重灌须能维持孔间距（via_legal 内校验）。
REFILL_ADAPTS_ZONE = True
# track_angle：KiCad 10.0.5 实证（B1 校准探针 2026-08-28）——净区 30° 走线 CLI
# 零违规，即该 severity 键存在但无自定义角度规则时不强制。L1 关闭此检查；
# L3 实战仍只用 45° 整倍数路径（工艺纪律，非 DRC 需要）。
ENFORCE_TRACK_ANGLE_45 = False
# 探针/门对比只数 error 级违规
ERROR_SEVERITY_ONLY = True
# CLI 把圆形铜（via 盘）多边形化（内接多边形）后测间距：判定不确定带宽度。
# 过孔间隙落在 [req − VIA_POLY_SAGITTA, req) 时 CLI 判定不可从精确几何预测
# （B1 实测 0.199mm 间隙判合法）。探针与 L3 实战非法侧须避开此带。
VIA_POLY_SAGITTA = 0.006

# ---- 空间索引 ----
BUCKET = 2.0        # 栅格桶边长 mm
EPS = 1e-9          # 几何容差（mm 级）
TOUCH_TOL = 1e-6    # connectivity 判"接触"的表面距离容差 mm

# ---- kicad-cli ----
KICAD_CLI = r"F:\kicad\bin\kicad-cli.exe"

# ---- 探针电池 ----
PROBE_NET = "ZPROBE"          # 探针铜的独占网名（净表按名字，插入无需注册）
PROBE_UUID_BASE = "00000000-0000-0000-0000-"

# ---- L2 拥塞规划器（SPEC §3；全部调参在此，B2 门调参须记录）----
L2_CELL = 0.5                 # 粗格边长 mm（≈1 条 0.15+0.2 容量单元）
L2_SUB = 5                    # 每格 SUB×SUB 子采样判占用（5×5=0.1mm 步距；
                              # 3×3 欠采样 0.35mm 车道窗会整格假堵死，实测修正）
L2_SIGNAL_LAYERS = (LAYER_F, LAYER_IN2)   # Rev-C 信号层（routing-spec §5）
L2_W_LANE = 0.15              # 候选新道线宽 mm（最宽用类；容量/判堵的最小车道口径）
L2_W_REF = 0.2                # 容量参考线宽 mm（本板主流信号类）
L2_CLR_REF = 0.2              # 容量参考间距 mm（全网络类一致，B1 实证）
L2_MAX_ITER = 12              # PathFinder 代数上限（超容布局预期红局，
                              # 收敛即提前止；50 代对分钟级预算无增益）
L2_PFAC = 0.45                # present 过载代价系数（每超 1 网的乘子增量）
L2_HSTEP = 0.35               # 历史项每代累加（mm 等效）
L2_VIA_EQ_MM = 0.6            # 层迁移等效长度代价 mm（L3 用 0.2，L2 略高抑过孔）
L2_RIPUP_COST_MM = 4.0        # 进入零容量格（需推挤既有铜）的每格拆让代价 mm 等效；
                              # SPEC §3.2 协商语义：不硬封锁，付代价穿越，过载格
                              # 由多网竞争自然涌现（2026-08-29 实测：硬封锁会把
                              # U1↔U2 通道整段判死路，过载信息全丢）
L2_ESCAPE_DEPTH = 1.5         # 逃逸审计带深 mm（F.Cu 逃逸 ≤3mm 的一半，spec §5.3）
L2_PAIR_PAD_SNAP = 2.0        # 断点端点坐标→同网焊盘归并距离 mm
L2_GATE_HIT_RATE = 0.70       # B2 门：61 断点走廊命中率下限（两点各测）
L2_GATE_3V3_MIN = 15          # B2 门：3V3 22 条逃逸审计命中下限

# 网名 → 类键（routing-spec §2 网络类表；.kicad_pro 无 netnames 指派，
# 按前缀确定性匹配，顺序即优先级——先match先得）
L2_NET_CLASS_PATTERNS = (
    ("USB_", "USB"),        # USB_DIFF：F 全程
    ("ADC_", "ANLG"), ("VREF", "ANLG"), ("VDDA", "ANLG"), ("GNDA", "ANLG"),
    ("HSE_", "ANLG"), ("LSE_", "ANLG"),
    ("FMC_", "FMC"),
    ("SDMMC2", "SDMMC2"), ("SDMMC1", "SDMMC1"), ("SD_CD", "SDMMC1"),
    ("QSPI", "QSPI"),
    ("ETH_", "ETH"),
    ("LTDC", "LTDC"),
    ("3V3", "PWR"), ("5V", "PWR"), ("VBUS", "PWR"), ("VBAT", "PWR"),
    ("SW_NODE", "PWR"), ("FB_NODE", "PWR"), ("EMMC_VSEL", "PWR"),
    ("VCAP", "PWR"),
)
L2_NET_CLASS_DEFAULT = "SIG"   # GPIO_*/I2C/USART/SAI/SWDIO 等

# 类键 → 层偏好 (F 系数, In2 系数)；99=该层禁走（routing-spec §2 允许层）
L2_LAYER_PREF = {
    "USB": (1.0, 99.0),     # F 全程
    "ANLG": (1.0, 99.0),    # F
    "QSPI": (1.1, 1.0),     # F 优先
    "FMC": (1.25, 1.0), "SDMMC1": (1.25, 1.0), "SDMMC2": (1.25, 1.0),
    "ETH": (1.25, 1.0), "LTDC": (1.25, 1.0),
    "PWR": (1.0, 1.0),      # 两层皆可（In2 主干 + 端部 F 逃逸）
    "SIG": (1.15, 1.0),     # 长距倾向 In2（主干层）
}

# 类键 → 典型分支线宽 mm（逃逸审计 fanout 判堵半径、corridors.json 标注用；
# 容量图统一用 L2_W_REF/L2_CLR_REF 参考道，电源干 1.0 需连续多道，见报告局限节）
L2_CLASS_WIDTH = {"LTDC": 0.15, "SIG": 0.15, "USB": 0.2, "FMC": 0.2,
                  "SDMMC1": 0.2, "SDMMC2": 0.2, "QSPI": 0.2, "ETH": 0.2,
                  "ANLG": 0.2, "PWR": 0.5}

# 布线协商顺序（routing-spec §9：USB → FMC → SDMMC2 → QSPI → ETH → 其余）
L2_ROUTE_PRIORITY = {"USB": 0, "FMC": 1, "SDMMC2": 2, "SDMMC1": 3,
                     "QSPI": 4, "ETH": 5, "LTDC": 6, "PWR": 7, "ANLG": 8,
                     "SIG": 9}

# ---- L3 区域受限详细路由器（SPEC §4；全部调参在此）----
L3_RES = 0.05                  # 搜索栅格格距 mm（SPEC §4.1：0.025–0.05；
                               # 0.1mm 粗格格心偏移坑见 HANDOFF 坑 5，自定
                               # 区域原点天然规避）
L3_MARGIN = 3.0                # 区域 = 端点 bbox 外扩边距 mm（SPEC §4.1 默认；
                               # S4 实测 6.0 对子段"不可达"无改善且机时翻倍
                               # ——墙是宽区域饱和，不是薄障碍，调参记录）
L3_VIA_COST_MM = 0.2           # 层迁移等效成本 mm（SPEC §4.1）
L3_CORRIDOR_COST_MM = 0.15     # 偏离 L2 走廊的每格附加成本 mm（软约束）
L3_MAX_REFINE = 6              # L1 终判失败→局部加障碍重搜的最大轮数
L3_RIPUP_BUDGET = 3            # 区域内拆迁预算：最多可拆邻网数（SPEC §4.1 N=3）
L3_RIPUP_FORBIDDEN = ("GND",)  # 禁拆网（GND 缝合孔/平面引线，SPEC §4.1）
L3_BATCH = 10                  # 提交纪律 batch 大小：每 ≤10 网 CLI 复核（§4.2）
L3_BLOCK_EXTRA = 0.02          # 静态障碍膨胀安全余量 mm（L1 margin>0 终判兜底）
L3_UUID_BASE = "00000000-0000-0000-0002-"   # L3 新铜 uuid 确定性派生空间
L3_START_FREE_R = 0.05         # 起终点焊盘中心强制可达半径 mm（自身铜豁免
                               # 已覆盖焊盘，此处兜底起点格起步）
# L3 route 候选线宽（分支口径）：PWR 网收断点/短跳按 0.2 分支宽（3V3 的
# 22 条卡点全是引脚场逃逸/相邻 pad 跳线，0.5 主干宽在 0.5mm pitch 缝里
# 无位——2026-08-29 Rev-C dry-run 实测；电源干加粗属 GUI 会话人工调）。
# 其余类同 L2_CLASS_WIDTH。
L3_CLASS_WIDTH = dict(L2_CLASS_WIDTH, PWR=0.2)
L3_VIA_SIZE, L3_VIA_DRILL = 0.6, 0.3   # 分支过孔统一 Default 口径
                               # （≥min_via_diameter/drill；类默认 PWR
                               # 0.7/0.4 在过孔场里更堵，分支不需要）
# 走廊中继分段（S4 实战，PHASE-REPORT-3 §5.1）：直线距离 ≥ L3_SEG_MIN_MM 的
# 断点对沿其 L2 走廊每 L3_SEG_INTERVAL_MM 取中继点，逐段 route_net（层连续性
# =前段到达层）后聚合单 Plan 落板——≥15mm 长距网在 3mm 区域裁剪下必然
# "不可达"（dry-run 实测 28 条），分段是其唯一 L3 通路。
L3_SEG_MIN_MM = 8.0            # 直线距离阈值（≥ 此值走分段）
L3_SEG_INTERVAL_MM = 7.0       # 中继点弧长间距（6–8mm 窗口取中值）

# ---- L4 验证与审计桥（SPEC §5；B4/S5）----
B4_OUT_SUBDIR = "b4"           # L4 产物子目录（<工程>/pcbagent-out/b4/）
LENGTH_VIA_EQUIV_MM = 0.2      # 每过孔等效长度 mm（routing-spec §3 测量口径）
# 九组等长口径（routing-spec §3 表逐行；与 revc/length-report.py GROUPS 逐键
# 对账一致——ref=None 为 USB 对内口径）。改 spec 时两处同步。
LENGTH_GROUPS = {
    "G_USB": {"ref": None, "target": 1.0, "limit": 2.5,
              "nets": ["USB_DP", "USB_DM"]},
    "G_FMC_D": {"ref": "FMC_SDCLK", "target": 2.5, "limit": 5.0,
                "nets": [f"FMC_D{i}" for i in range(16)] + ["FMC_NBL0", "FMC_NBL1"]},
    "G_FMC_C": {"ref": "FMC_SDCLK", "target": 2.5, "limit": 5.0,
                "nets": ["FMC_SDNCAS", "FMC_SDNRAS", "FMC_SDNWE",
                         "FMC_SDNE0", "FMC_SDCKE0"]},
    "G_FMC_A": {"ref": "FMC_SDCLK", "target": 5.0, "limit": 10.0,
                "nets": [f"FMC_A{i}" for i in range(13)] + ["FMC_BA0", "FMC_BA1"]},
    "G_EMMC": {"ref": "SDMMC2_CK", "target": 1.5, "limit": 3.0,
               "nets": ["SDMMC2_CMD"] + [f"SDMMC2_D{i}" for i in range(4)]},
    "G_SD": {"ref": "SDMMC1_CK", "target": 2.5, "limit": 5.0,
             "nets": ["SDMMC1_CMD"] + [f"SDMMC1_D{i}" for i in range(4)] + ["SD_CD"]},
    "G_QSPI": {"ref": "QSPI_CLK", "target": 2.5, "limit": 5.0,
               "nets": [f"QSPI_IO{i}" for i in range(4)] + ["QSPI_NCS"]},
    "G_ETH": {"ref": "ETH_REF_CLK", "target": 2.5, "limit": 5.0,
              "nets": ["ETH_CRS_DV", "ETH_RXD0", "ETH_RXD1", "ETH_TXD0",
                       "ETH_TXD1", "ETH_TX_EN", "ETH_MDC", "ETH_MDIO"]},
    "G_LTDC": {"ref": "LTDC_PCLK", "target": 5.0, "limit": 10.0,
               "nets": [f"LTDC_R{i}" for i in range(5)] + [f"LTDC_G{i}" for i in range(6)]
                       + [f"LTDC_B{i}" for i in range(5)]
                       + ["LTDC_DE", "LTDC_HSYNC", "LTDC_VSYNC"]},
}
# render 默认导出层（分层 SVG：信号层 + 丝印定 refdes + 板框）
RENDER_LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu",
                 "F.SilkS", "B.SilkS", "Edge.Cuts")
# B5 gui-session-kit：GUI 人工会话每批施工量（对数；一次保存→verify 回归门为一个循环）
GUI_KIT_BATCH_PAIRS = 8
