"""pcbflow 全局配置：路径、schema 版本、exit-code 契约、确定性写出参数。

阈值/系数集中本文件（SPEC §6）。核心产物禁 wall-clock/主机路径 —— 相关
常量（FORBIDDEN_CORE_KEYS）在 envelope.py 定义并由测试强制。

G0（REPAIR-P4 W-1）：Rev-C 项目事实（design/coreboard 路径、九总线、② 预检
阈值、回测三门门限、③ 布局参数、seed 目录 pin）自本文件抽至
profiles/revc-coreboard/profile.json，装载器=pcbflow/profile_loader.py
（fail-closed）。快照纪律：config_sha256 是本模块大写属性集 canonical
dumps 的 sha——大写常量名与值零增删（装载代码一律小写成员），保证历史
产物 envelope byte-exact。

G1+（REPAIR-G1PLUS W-1/W-2，2026-09-24）：_pf_* 常量族显式对象化为
ProjectManifest（dataclass）+单一装载函数 load_project_manifest；模块级
旧名（_pf/_pf_* 与全部大写常量）保留为兼容别名（别名与 manifest 字段
同一 dict 对象，行为零变化）。out_dirs=W-2 消化的 D 级 API pin 缺省
（CLI --out-dir 与 build_products(out_dir_rel=…) 默认参数取值源；
封闭集外唯一新增字段，登记=out/repair-g1plus-r1/ 与 growth-inventory
r3）。keepout_iter 两计划 pin（os.path.join 平台分隔符形态）留账未消化
（G2/G3 profile 驱动域，见批报告 deviations）。

G2（REPAIR-G2G3 W-G2，2026-09-25）：None-sentinel 显式语义=「结构化错误
+成文」——load_project_manifest 取值链对缺席键/半套/坏值抛 ManifestError
（ProfileError 子类；结构化属性 field=字段点路径+available=取值面清单，
消息前缀保持 G1+ 守卫 regex 兼容），不静默回落历史字面量。缺省参数语义
二分成文（DOC 层=exec/REPAIR-G2-MANIFEST-DEFAULT-SEMANTICS-2026-09-25.md）：
「manifest 必在」=现役维持（缺省表达式 import 期经本函数求值，装载失败
即 import 失败，无字面量回落路径）vs「显式 None 注入」=None-sentinel 不
实现（显式传 None=非法输入，函数体无 None 分支/回落；两消费形态如实
披露于该成文件）。口径对齐批（2026-09-25，O-1/D-3 收口）：显式
None/非 dict 入参自本批起=结构化拒绝——_validate_manifest_config 头部
isinstance 门抛 ManifestError("config", [])，不再以 TypeError 高声拦
（LEAD-REVIEW-G2G3 观察项 O-1；「显式 None 注入」串拼接开放缺口 D-3
随之闭合，登记=out/align-r1/）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .profile_loader import ProfileError, as_tuple, load_profile, require

PCBFLOW_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# …\workspace\default\tools\pcbflow → …\workspace\default
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(PCBFLOW_ROOT))

# ---- G1+ Project Manifest（小写成员：不入 vars() 大写快照） ------------------
# 字段集=_pf_* 族封闭集（paths/gate0/audit/audit_gates/cplace + profile
# 身份元数据）+W-2 out_dirs（唯一增长项，见模块 docstring 登记）。类名
# CamelCase 非 isupper → 不入大写快照；实例/函数一律小写名。
@dataclass(frozen=True)
class ProjectManifest:
    """Rev-C 项目事实 manifest（G1+ W-1 对象化形态；值域=profile 声明）。"""
    profile_id: str
    profile_path: str
    profile_sha256: str
    paths: dict            # profile config.paths（相对路径段声明）
    gate0: dict            # profile config.gate0（⓪ 门参数）
    audit: dict            # profile config.audit（② 预检参数）
    audit_gates: dict      # profile config.audit_gates（回测三门门限+筛查阈）
    cplace: dict           # profile config.cplace（③ 布局参数）
    out_dirs: dict         # W-2：D 级 API pin 缺省（值=历史字面量逐项不变）


class ManifestError(ProfileError):
    """ProjectManifest 取值链结构化失败（G2 W-G2，fail-closed 显式语义）。

    结构化属性：field=缺席/坏值字段点路径（如 "config.out_dirs" /
    "config.out_dirs.compile"）；available=失败时点该 mapping 实际持有的
    键清单（取值面，sorted）。消息形如「profile_key_missing:<末段键>
    available=<逗号联清单>」——前缀保持 G1+ 既有守卫 regex（r"profile_key_
    missing:out_dirs"）兼容；完整点路径在 .field 属性。
    """

    def __init__(self, field, available):
        self.field = field
        self.available = list(available)
        super().__init__("profile_key_missing:%s available=%s" % (
            field.rsplit(".", 1)[-1], ",".join(self.available)))


#: manifest config 必需节（小写名：不入 vars() 大写快照——81 键 sha
#: 914180f9 恒等前提，profile_loader「装载代码一律小写成员」纪律）。
_manifest_sections = ("paths", "gate0", "audit", "audit_gates",
                      "cplace", "out_dirs")

#: out_dirs 必需键封闭集（=G1+ W-2 消化面 13 键；半套=缺席判据）。
out_dirs_required_keys = ("compile", "enum", "audit", "coplace", "editor",
                          "feedforward", "route", "residual", "keepout_iter",
                          "check", "signoff", "kit_ff_plan", "kit_route_plan")


def _validate_manifest_config(cfg):
    """config 节结构化校验（G2 W-G2 纯函数段；供故障注入测试直喂 dict，
    零 load_profile lru_cache 副作用）。

    入参非 dict（含 None）→ ManifestError("config", [])（口径对齐批
    2026-09-25 O-1/D-3 收口：原形态=TypeError 高声拦非结构化）。
    六节缺席 / out_dirs 整节缺席或非 dict / 13 键半套缺席 / 值非 str 或
    空串 → ManifestError（field+available），不静默回落历史字面量。
    返回六节 dict。
    """
    if not isinstance(cfg, dict):
        raise ManifestError("config", [])
    for s in _manifest_sections:
        if s not in cfg:
            raise ManifestError("config." + s, sorted(cfg))
    od = cfg["out_dirs"]
    if not isinstance(od, dict):
        raise ManifestError("config.out_dirs", [])
    missing = [k for k in out_dirs_required_keys if k not in od]
    if missing:
        raise ManifestError("config.out_dirs." + missing[0], sorted(od))
    for k in out_dirs_required_keys:
        if not isinstance(od[k], str) or not od[k]:
            raise ManifestError("config.out_dirs." + k, sorted(od))
    return {s: cfg[s] for s in _manifest_sections}


def load_project_manifest(root=None):
    """单一装载函数：profile 声明 → ProjectManifest（fail-closed 同
    load_profile/require；不另立第二条取值路径）。

    G2 W-G2：取值链结构化校验（_validate_manifest_config）——缺席/半套/
    坏值 → 结构化 ManifestError。
    """
    pf = load_profile(root if root is not None else PCBFLOW_ROOT)
    sections = _validate_manifest_config(require(pf, "config"))
    return ProjectManifest(
        profile_id=pf["profile_id"],
        profile_path=pf["_path"],
        profile_sha256=pf["_sha256"],
        paths=sections["paths"],
        gate0=sections["gate0"],
        audit=sections["audit"],
        audit_gates=sections["audit_gates"],
        cplace=sections["cplace"],
        out_dirs=sections["out_dirs"])


_manifest = load_project_manifest()
_pf = load_profile(PCBFLOW_ROOT)      # 兼容别名（lru_cache：与 manifest 同源同对象）
_pf_paths = _manifest.paths           # 兼容别名（=require(_pf,"config","paths") 同一 dict）
_pf_gate0 = _manifest.gate0
_pf_audit = _manifest.audit
_pf_agates = _manifest.audit_gates
_pf_cplace = _manifest.cplace

# ---- 权威输入（只读；路径段声明在 profile config.paths） --------------------
ROUTING_SPEC = os.path.join(WORKSPACE_ROOT, *_pf_paths["routing_spec"])
PLACEMENT_SPEC = os.path.join(WORKSPACE_ROOT, *_pf_paths["placement_spec"])
REVC_DIR = os.path.join(WORKSPACE_ROOT, *_pf_paths["revc_dir"])
REVC_NETLIST = os.path.join(REVC_DIR, _pf_paths["netlist_name"])
REVC_BOARD = os.path.join(REVC_DIR, _pf_paths["board_name"])
LENGTH_REPORT_PY = os.path.join(REVC_DIR, _pf_paths["length_report_name"])

# ---- 产物落位 --------------------------------------------------------------
# Rev-C 全程只读：回测产物落 pcbflow 侧（HANDOFF §关键指针）。
OUT_DIR = os.path.join(PCBFLOW_ROOT, "out")

# ---- schema 版本（版本化契约，变更需同步 SPEC §2.1 与测试） ----------------
SCHEMA_ENVELOPE = "1.1"
SCHEMA_CONSTRAINTS = "1.1"
SCHEMA_COVERAGE = "1.1"
SCHEMA_IMPEDANCE = "1.1"
SCHEMA_TOOLCHAIN_LOCK = "1.1"
SCHEMA_STRUCTURES = "1.1"
SCHEMA_NET_REGISTRY = "1.0"   # SPEC §1.1 逐网编译视图（FA3 v1.2 adoption 首次正式成档）
SCHEMA_IDENTITY_MAP = "1.0"   # SPEC §1.1 net_id 身份映射（首次分配，lineage 追加式）
SCHEMA_AUDIT = "1.0"          # SPEC §② audit.json / pin-swap / skeleton seed
SCHEMA_COPLACE = "1.0"        # SPEC §③ layout.json（唯一优化输出）
SCHEMA_GEOJSON = "1.0"        # SPEC §③ skeletons.geojson（内部毫米坐标）
SCHEMA_LAYER_PLAN = "1.0"     # SPEC §③ 段层计划+段预算
SCHEMA_CONVERSION = "1.0"     # SPEC §③ layout→placement.csv 转换证明

TOOL_VERSION = "0.1.0"

# ---- exit-code 契约（SPEC §6：每命令必须有 exit-code 契约） ----------------
# 0=ok  1=failed  2=blocked  3=unknown  4=not_implemented(命令仍为 specified)
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_UNKNOWN = 3
EXIT_NOT_IMPLEMENTED = 4

# ---- 确定性写出参数（SPEC §2.2 固定项） ------------------------------------
JSON_ENSURE_ASCII = False
JSON_INDENT = 1
JSON_SORT_KEYS = True
NEWLINE = "\n"
ENCODING = "utf-8"

# ---- ⓪ 门参数（HANDOFF FA1；值声明在 profile config.gate0） -----------------
GATE_CONSTRAINT_COUNT = as_tuple(_pf_gate0["constraint_count"])  # Rev-C 约束库预期条数区间
NINE_GROUPS = list(_pf_gate0["nine_groups"])

# ---- ② 架构预检参数（SPEC §②；全部锚定 spec 条款，禁止对回测集调参） --------
# 回测输入（只读；HANDOFF FA3）：p3 布局时点 + 61 断点真值
AUDIT_P3_BOARD = os.path.join(
    REVC_DIR, *_pf_paths["audit_p3_dir"], _pf_paths["audit_p3_board_name"])
AUDIT_P3_PLACEMENT_CSV = os.path.join(
    REVC_DIR, *_pf_paths["audit_p3_dir"], _pf_paths["audit_p3_placement_csv_name"])
AUDIT_OPENS_CSV = os.path.join(REVC_DIR, _pf_paths["audit_opens_csv_name"])

# 层模型：4 层叠层（routing §5/structures.return_tree：In1/B=GND 平面）
# 调参记录（SPEC §② 允许一轮）：FA3 会话自 ≥2 收紧至 4，理由=2 端网单点全堵
# 与实际幸存不可分（FMC_A9 vs D7）——记录随值迁 profile（audit 节注释）。
AUDIT_SIGNAL_LAYERS = list(_pf_audit["signal_layers"])
AUDIT_GRID_CELL_MM = _pf_audit["grid_cell_mm"]        # 粗格容量图（b2 同量级；pcbflow 自有口径）
AUDIT_TRACK_PITCH_MM = _pf_audit["track_pitch_mm"]    # C-0036：同向平行间距 0.35（0.20 线宽+2×clearance）
AUDIT_ESCAPE_DEPTH_MM = _pf_audit["escape_depth_mm"]  # C-0037：F.Cu 逃逸 ≤3mm → 逃逸带深度
AUDIT_CHANNEL_HALF_MM = _pf_audit["channel_half_mm"]  # 逃逸通道半宽 = 0.35/2
AUDIT_FATAL_MIN_BLOCKED_PADS = _pf_audit["fatal_min_blocked_pads"]  # 网级致命需 ≥4 个 transit 焊盘全堵（走投无路的轨）；
                                                  # 2 端网全堵=场级证书+命中证据，不判网死刑。
AUDIT_BODY_INFLATE_MM = _pf_audit["body_inflate_mm"]  # 封装体膨胀（pad-bbox 代理，derived 标记）
AUDIT_TRANSIT_BAND_MM = _pf_audit["transit_band_mm"]  # 「需离场」判定：对端在带内=场内短跳，不占逃逸需求

# 检查5/6 参数（C-0046/C-0044/C-0039）
AUDIT_LOOP_TARGET_MM2 = _pf_audit["loop_target_mm2"]      # C-0046 目标 15×10
AUDIT_LOOP_LIMIT_MM2 = _pf_audit["loop_limit_mm2"]        # C-0046 上限 20×12
AUDIT_LOOP_CAP_RADIUS_MM = _pf_audit["loop_cap_radius_mm"]  # Cin(5V)/Cout(3V3) 归属半径（实测 C27/C28=4.2、C29=4.7）
AUDIT_DECAP_TARGET_MM = _pf_audit["decap_target_mm"]      # C-0044 目标
AUDIT_DECAP_LIMIT_MM = _pf_audit["decap_limit_mm"]        # C-0044 上限
AUDIT_STITCH_GRID_MM = _pf_audit["stitch_grid_mm"]        # C-0039 缝合网格

# ② 回测三门（SPEC §② 算法回测门；预测器质量门≠项目交付门；profile config.audit_gates）
GATE_AUDIT_RECALL_MIN = _pf_agates["recall_min"]    # 61 断点预测命中率 ≥70%
GATE_AUDIT_3V3_MIN = _pf_agates["v3_escape_min"]    # 3V3 逃逸缺口命中 ≥15/22
GATE_AUDIT_FP_MAX = _pf_agates["fp_max"]            # 误报（实际可布却标架构致命）≤10%
AUDIT_LAYER_UTIL_YELLOW = _pf_agates["layer_util_yellow"]  # 层预算利用率筛查阈值（一阶筛查，非 spec 条款）
AUDIT_LAYER_UTIL_RED = _pf_agates["layer_util_red"]
AUDIT_ORIENTATION_MIN = _pf_agates["orientation_min"]      # 检查7：总线出口侧一致性比例（一阶筛查）

# ---- ③ 联合布局参数（SPEC §③；候选按 §③ 枚举，无随机；profile config.cplace）
# ②→③ 交接数据（NEXT.md FB1：读 out/revc-a3/skeleton-seed.json，绑 registry hash）
SEED_PATH = os.path.join(OUT_DIR, *_pf_paths["seed_rel"])

CPLACE_QUANT = _pf_cplace["quant_mm"]                # 内部坐标量子（mm；int=0.05mm 单位，精确算术）
CPLACE_STEPS_MM = as_tuple(_pf_cplace["steps_mm"])   # 平移候选步长（SPEC §③ ±{0.5,1,2}×4 向）
CPLACE_ROT_STEP = _pf_cplace["rot_step_deg"]         # 旋转候选步长（度）
CPLACE_MAX_SWEEPS = _pf_cplace["max_sweeps"]         # 爬山扫描上限（超限=如实报 max_sweeps 非收敛）
CPLACE_SIDEWAYS_PER_REF = _pf_cplace["sideways_per_ref"]  # 每 ref 每扫等值横移上限（绕障；确定性生成序取用）
CPLACE_SIDEWAYS_EPS_MM = _pf_cplace["sideways_eps_mm"]    # 横移容差（mm；贴墙滑移用；尾部分量仍须逐项不劣）
CPLACE_MIN_BEND_SPACING_MM = _pf_cplace["min_bend_spacing_mm"]  # 骨架拐点最小间距（SPEC §③）
CPLACE_BODY_INFLATE_MM = _pf_cplace["body_inflate_mm"]  # 封装体=pad-bbox+0.25（derived 代理；与 ② audit 同源值）
CPLACE_DECAP_LIMIT_MM = _pf_cplace["decap_limit_mm"]    # §2.1 去耦 ≤3.0 上限（目标 2.0；与 ② audit 同源值）
CPLACE_TARGET_TOL_MM = _pf_cplace["target_tol_mm"]  # 目标值测量容差=半量子（0.05mm 格上的假阳性消除）
CPLACE_LOOP_W_LIMIT_MM = _pf_cplace["loop_w_limit_mm"]   # §2.5 buck 环路上限 20×12（目标 15×10）
CPLACE_LOOP_H_LIMIT_MM = _pf_cplace["loop_h_limit_mm"]
CPLACE_USB_PAIR_LIMIT_MM = _pf_cplace["usb_pair_limit_mm"]  # §2.4 USB 对端到端 ≤35（目标 25）
CPLACE_CRYSTAL_KEEPOUT_MM = _pf_cplace["crystal_keepout_mm"]  # §6.1 晶振 3mm 净空
CPLACE_USB_SHELL_KEEPOUT_MM = _pf_cplace["usb_shell_keepout_mm"]  # §6.3 USB-C 外壳 5mm 内无晶振/时钟
CPLACE_CORRIDOR_EPS_MM = _pf_cplace["corridor_eps_mm"]  # 通道预算浮点容差（半量子）
# 软目标绿/黄/红阈值（SPEC §③ 证据向量；红=停，黄=继续但记账，绿=通过）
CPLACE_CROSSING_YELLOW = _pf_cplace["crossing_yellow"]        # 交叉数：0=绿，≥1=黄（软目标，逐级消除）
CPLACE_CHANNEL_UTIL_YELLOW = _pf_cplace["channel_util_yellow"]  # 走廊利用率（需求宽/实际净空）：<0.9 绿
CPLACE_VIA_YELLOW = _pf_cplace["via_yellow"]                  # 过孔总数（计划层变化合计）
CPLACE_DETOUR_YELLOW = _pf_cplace["detour_yellow"]            # 最大绕行比（骨架折线长/端点直线距）
CPLACE_SYMM_DEV_YELLOW_MM = _pf_cplace["symm_dev_yellow_mm"]  # 对称类最大偏差（mm，仅 symmetry_class 成员）
CPLACE_ZONE_FROM_LABEL_MARGIN_MM = _pf_cplace["zone_from_label_margin_mm"]  # imported 模式分区矩形=成员 bbox+余量（derived）
