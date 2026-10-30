"""pcbflow.v4_1 -- V4.1 工程布线内核 E1 包（几何保真内核，堵 K1）。

依据：V4.1-ROUTER-ENGINEERING-TASKBOOK-2026-09-12.md §3 E1（frozen）；
根因锚：out/v4-exec/p3-revc/per-net-batch/batch-01/rollback.json §diagnosis
（P3REVC-BATCH-01 事故：advisory 预检 pad=min(w,h)/2 近似，长条焊盘长轴
低估，漏报 LTDC_R7 倒角 vs U1.109 焊盘 clearance 违例，kicad-cli 实测
0.1571mm < 0.2mm）。

模块职责（单一职责；核心模块零 IO、零子进程、零网络、零 wall-clock、
零主机绝对路径）：

- geometry      精确焊盘几何基元（round/oval/rect 含圆角矩形 roundness）
                与 clearance 精确距离引擎（Minkowski 核表示，解析闭式）；
- board_parse   解析路径 A（s-expr 树，复用 pcbflow.sexpr_min 只读依赖）；
- board_parse_alt 解析路径 B（独立行扫描/正则，零依赖路径 A 与 sexpr_min），
                与 A 交叉对拍（不一致=blocked 登记）；
- netclasses    net class 载入（板内 net_class 节点 / kicad_pro
                net_settings / 显式声明缺省；缺则 fail-closed not_available）
                与逐网 clearance 矩阵；
- precheck      advisory 预检器 v4_1（候选链入口；路径 A + geometry）；
- checker       独立几何 checker（路径 B + 自有外切多边形距离引擎）；
- regression    G1.1 根因回归（P3REVC-BATCH-01 原候选必须预测违例）；
- audit         G1.2 构造对拍集 + 漏报审计 + 误报台账（false-negative-audit）；
- canonical     canonical JSON 序列化（UTF-8/LF/sort_keys/indent=1/
                ensure_ascii=False，从 baseline.json 先例）；
- prl_hygiene   .kicad_prl sidecar 卫生（E6 纪律提前生效：kicad-cli 调用
                前后目录盘点、sidecar 检测、登记与复原）。

E2 追加模块（任务书 §3 E2：规则面与多层，堵 K2）：

- layerstack    多层层栈/层对/贯通孔跨度语义（跨度=栈序闭区间含中间层；
                board_parse/board_parse_alt 经此展开 via 跨度——E1 的
                (F.Cu B.Cu)=全栈行为不变，盲/埋孔含中间层为 E2 修复）；
- mlfamily      多层合成场景族 f9/f10（4 层 F.Cu/In1.Cu/In2.Cu/B.Cu；
                确定性 seed=sha256(scenario_id) 前 4 字节；f1–f8 与
                既有 112 场景 manifest 零改动）；
- mlchain       多层族全链（生成→求解→检查）：求解适配层以只读库调用
                复用 v4exp.router（v4exp/ 零改动红线不破）；检查腿用
                本包双引擎（Minkowski 核精确 + 外切多边形）独立复查
                求解输出（via 全跨度层障碍/层合法性/宽度/clearance）；
- e2parity      net class 线宽/间距 kicad-cli DRC 对拍（多层合成板
                staging 生成→DRC→对照；rule-parity 台账；探针实证：
                per-class 规则权威源=.kicad_pro net_settings，类宽=
                布线默认值非 DRC 约束，板级 min_track_width 经
                design_settings.rules 生效）。

保守化方向=漏报 0（宁可误报不可漏报）：预检与 checker 均含保守带
CONSERVATIVE_BAND_MM（默认 0.01mm，与 G1.1 预注册对拍容差同量级），
带内合法侧判例按误报入台账，不静默。

本包零改动任何既有文件（红线：v4exp/ v4exec/svg/check 既有模块与既有
测试全部只读；受保护三文件 pcbflow/cli.py、pcbflow/config.py、
toolchain_lock.json 零变化）。
"""

from __future__ import annotations

#: 声明常量（非 wall-clock；红线：核心产物不引入 wall-clock）
DECLARED_DATE = "2026-09-12"

#: 包 schema 主版本
SCHEMA = "pcbflow.v4_1/1"

#: 保守带（mm）：pred_clearance < required + band 即判违例（方向=漏报 0，
#: 宁可误报）。band 与 G1.1 预注册对拍容差同量级（模型-KiCad 实测偏差
#: 上界由 G1.1 对拍验证：本包实测偏差 0.000057mm << band）。
CONSERVATIVE_BAND_MM = 0.01

#: G1.1 预注册对拍容差（mm）：|预测 - kicad-cli 实测| <= 0.01
G11_TOLERANCE_MM = 0.01

#: P3REVC-BATCH-01 根因锚：kicad-cli 实测 clearance（batch-01/drc-all.json
#: violations[type=clearance][items=LTDC_R7 段 vs U1.109]：间距 0.2000mm；
#: 实际 0.1571mm）
P3REVC_BATCH01_MEASURED_MM = 0.1571

#: KiCad 内部长度单位 = 1nm（坐标小数位 > 6 = 离格，fail-closed）
KICAD_MAX_COORD_DECIMALS = 6

__all__ = [
    "DECLARED_DATE", "SCHEMA", "CONSERVATIVE_BAND_MM",
    "G11_TOLERANCE_MM", "P3REVC_BATCH01_MEASURED_MM",
    "KICAD_MAX_COORD_DECIMALS",
]
