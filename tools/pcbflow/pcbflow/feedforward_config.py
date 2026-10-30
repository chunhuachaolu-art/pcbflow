"""FF 前馈轨道版本化配置（SPEC v1.3 §6/§7/§15 FF-0..FF-3；决策 D1-D8）。

与核心 config.py 隔离（A3/§15 FF-1 条款）：本文件常量变更只改变
`feedforward_config_sha256`，不漂移历史 A/B 产物的核心 config_sha256。

阈值性质声明：本文件中的 yellow/threshold 全部是 **planning policy（规划筛查）**，
不是 spec 硬约束，不进入核心阶段门；reserve 默认 0.0 且逐资源可追溯（D3），
安全系数只允许作为 demand 函数显式项，禁止隐性 reserve。
"""

from __future__ import annotations

import os

from . import profile_loader
from .profile_loader import as_tuple

# G0（REPAIR-P4 W-1）：Rev-C 轮次/目录 pin 自 profiles/revc-coreboard/
# profile.json 装载（root 与 config.PCBFLOW_ROOT 同值自算，保持本文件与核心
# config 的隔离设计）。快照纪律：ff_config_sha256 是本模块大写属性集
# canonical dumps 的 sha——大写常量名与值零增删（装载代码一律小写成员）。
_pf = profile_loader.load_profile(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- FF schema 版本（A3：v1.3 起新核心产物 schema_version="1.3"） ------------
SCHEMA_FF_PLAN = "1.3"
SCHEMA_FF_COVERAGE = "1.3"
SCHEMA_FF_COMPARISON = "1.3"
SCHEMA_FF_BASELINE_FREEZE = "1.3"
SCHEMA_FF_ENVELOPE = "1.3"

FF_CONFIG_VERSION = "1.0"
PLAN_ID = profile_loader.require(_pf, "feedforward", "plan_id")
FREEZE_ID = profile_loader.require(_pf, "feedforward", "freeze_id")
FF_OUT_DIR_REL = profile_loader.require(_pf, "feedforward", "ff_out_dir_rel")

# ---- FF-0 冻结对象（只读历史产物；16+7 件） ---------------------------------
A3_DIR_REL = profile_loader.require(_pf, "feedforward", "a3_dir_rel")
B1_DIR_REL = profile_loader.require(_pf, "feedforward", "b1_dir_rel")
A3_FROZEN_PRODUCTS = as_tuple(
    profile_loader.require(_pf, "feedforward", "a3_frozen_products"))
B1_FROZEN_PRODUCTS = as_tuple(
    profile_loader.require(_pf, "feedforward", "b1_frozen_products"))

# ---- 资源六类（SPEC v1.3 §6.2）与口径 ----------------------------------------
RESOURCE_KINDS = ("escape_slots", "corridor", "layer_capacity", "bus_lane",
                  "via_budget", "power_return_space")

# D4：走廊/车道沿用 ② C-0053 / required_mm 几何宽度口径（与 ③ 已复算同源）；
# 离散轨道/网格容量模型留给 FC1 再议。
DEMAND_MODELS = {
    "escape_slots": "② C2 同源模型（escape_check 于 p3 板重算）：demand=transit 网数",
    "corridor": "D4：C-0053 几何宽度 ceil(N/2)×0.35+0.6（audit corridor_budget_check."
                "required_mm，与 ③ 复算同源）",
    "layer_capacity": "② C3 层预算：需求面积=链式直连长×0.35 pitch",
    "bus_lane": "D4：车道堆叠宽=ceil(N/2)×0.35（C-0053 车道项，不含 0.6 壁余量；"
                "离散车道模型留 FC1）",
    "via_budget": "③ layer-plan via_count_total（p3 计划级口径）",
    "power_return_space": "D5：电源/回流按 §6.4 角色函数；电源树电流=null → "
                          "missing_basis 不虚构",
}

# D3：reserve 默认 0.0，逐资源可追溯；无来源 reserve → missing_basis。
RESERVE_DEFAULT_BASIS = ("D3：v1 FF config 默认 reserve=0.0（逐资源可追溯）；"
                         "安全系数只允许作为 demand 函数显式项，禁止隐性 reserve")

# yellow_margin（规划筛查阈值；非 spec 条款）。None=该类不适用统一阈值（逐资源给定）。
YELLOW_MARGIN = {
    "escape_slots": {"value": 1.0, "unit": "channels",
                     "basis": "FF-config planning threshold：margin<1 通道即低裕量"},
    "corridor": {"value": 0.5, "unit": "mm",
                 "basis": "FF-config planning threshold（筛查，非 spec）"},
    "layer_capacity": None,   # 面积基数随板变 → 按 supply 比例（FF_LAYER_YELLOW_FRACTION）
    "bus_lane": {"value": 0.35, "unit": "mm",
                 "basis": "FF-config planning threshold：不足一条车道宽（0.35 pitch）"},
    "via_budget": None,       # supply 缺 basis → 状态 missing_basis，yellow 无意义
    "power_return_space": None,  # 逐资源给定（下表）
}
FF_LAYER_YELLOW_FRACTION = 0.10  # layer_capacity 黄线=supply 的 10%（筛查）
YELLOW_MARGIN_BY_RESOURCE = {
    "power_return_space:SW_loop_area": {
        "value": 90.0, "unit": "mm2",
        "basis": "C-0046 limit 240 与目标 150 之差（目标即裕量线；筛查）"},
    "power_return_space:decap_radius": {
        "value": 0.0, "unit": "mm",
        "basis": "C-0044 目标 2.0 内为绿；margin≤0（超 limit 3.0 或贴线）为黄/红"},
    "power_return_space:analog_zone_crossings": {
        "value": 0.0, "unit": "crossings",
        "basis": "placement §5 模拟角禁数字穿越（允许数=0；C-0044 同族筛查）"},
}

# 赤字建议回退级（SPEC v1.3 §1.4；planning 建议，非自动执行）
SUGGESTED_ROLLBACK_STAGE = {
    "escape_slots": 3, "corridor": 2, "layer_capacity": 2, "bus_lane": 3,
    "via_budget": 3, "power_return_space": 3,
}

# §7.4 六 hash 过期检查键
STALE_CHECK_KEYS = ("registry_snapshot_hash", "structures_sha256",
                    "constraints_sha256", "placement_snapshot_sha256",
                    "board_snapshot_sha256", "feedforward_config_sha256")

# FF-3：②↔③ 需求交叉核对 canonical 字段与容差（SPEC v1.3 §8.3）
SANITY_CANONICAL_FIELD = "required_mm"
SANITY_TOLERANCE_MM = 1e-6

# 控制优先级占位（§6.5 冲突处理顺序；用于 preemption_policy 字符串）
PREEMPTION_POLICY = ("hard_constraint > power/return/clock/diff/key_nets > "
                     "approved_reservations > bus_order/net_order > normal_nets")
