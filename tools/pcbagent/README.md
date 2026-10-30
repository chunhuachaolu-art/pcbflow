# pcbagent — KiCad 布线规划/合法性/验证工具链

让 agent 能端到端驱动 KiCad 画板的确定性 Python 工具链（SPEC v1，见 `../SPEC.md`）。
纯确定性（numpy + 精确几何，无随机）、kicad-cli 是唯一 DRC 裁决源、镜像只读。

## 阶段状态（B1–B5）

| 模块 | 阶段 | 状态 |
|---|---|---|
| `mirror.py`（L0 板镜像） | B1 | ✅ 已过门（pcbnew 交叉验证 100%，opens 与 kicad-cli 对账一致） |
| `legality.py`（L1 合法性 API） | B1 | ✅ 已过门（探针电池 vs kicad-cli 100% 一致，单查询 <10ms） |
| `planner.py`（L2 拥塞规划） | B2 | ✅ 已过门（p3 命中 93%、当前板 95%、3V3 逃逸 21/22；见 `out/b2/`） |
| `router.py`（L3 区域路由） | B3 | ✅ 已建（合成板 7 项全过 + Rev-C 只读 dry-run 抽查；实战门在 S4） |
| `commit.py`（提交纪律） | B3 | ✅ 已建（快照/回滚 + SexprWriter/KipyWriter 双落板后端 + batch CLI 复核） |
| `bridge.py`（L4 验证桥） | B4 | ✅ 已过门（verify/length/render/audit-checklist 四命令全通；length 九组与 pcbnew 对账 113 项逐键一致，见 `out/b4/`） |
| `tests/run_b5_kit.py`（B5 施工包） | B5 | ✅ 已交付（gui-session-kit：53 信号+4 GND 分 7+1 批，46/53 有走廊标注） |

## 用法

```bash
# 板镜像统计（pads/tracks/vias/nets/断点 opens）
python -m pcbagent.cli mirror-info --project <工程目录>

# L4 verify：DRC 封装 + 基线 diff 回归检测（报告落 b4/，快照滚动 verify-last.json；
# 退出码 1=出现基线没有的新增违规；默认 --refill-zones --save-board 口径）
python -m pcbagent.cli verify --project <工程目录> [--baseline <drc.json>]

# L4 length：九组等长报告（routing-spec §3 口径；组 FAIL 是板态数据不是命令失败，
# --strict 才按 all_pass 定退出码）
python -m pcbagent.cli length --project <工程目录> [--strict]

# L4 render：分层 SVG（F/In1/In2/B.Cu+双丝印+板框 → b4/render/，每层一文件）
python -m pcbagent.cli render --project <工程目录> [--layers F.Cu,B.Cu]

# L4 audit-checklist：routing-spec §4 视觉审计清单（预填每网铜长/过孔/分层证据；
# advisory 非裁决，视觉判定留给人/VLM）
python -m pcbagent.cli audit-checklist --project <工程目录>

# B5：GUI 会话施工图包（残网分批清单+走廊图+每批 verify 回归门
# → <工程>/pcbagent-out/gui-session-kit/）
python tests/run_b5_kit.py --project <工程目录>

# L2 拥塞分析（PathFinder 协商 + 热图 SVG + corridors.json + 布局反馈 + 逃逸审计；
# 工程里有 opens.csv 即按断点对协商，--netlist 强制整板；产物落 <工程>/pcbagent-out/b2/）
python -m pcbagent.cli congestion --project <工程目录> [--netlist] [--cell 0.5]

# L2 引脚场逃逸容量审计（可单独跑；每封装每侧边 需求 vs 供给）
python -m pcbagent.cli escape-audit --project <工程目录> [--netlist]

# L2 单网走廊查询（读已缓存 corridors.json）
python -m pcbagent.cli corridors --project <工程目录> --net FMC_A6

# L3 单网/批量 route（区域 A* + L1 终判 + ripup → 提交纪律落板）
python -m pcbagent.cli route --project <工程目录> --net 3V3          # 单网（opens.csv 该网全部对）
python -m pcbagent.cli route --project <工程目录> --limit 10         # opens.csv 前 10 条
python -m pcbagent.cli route --project <工程目录> --net X --dry-run  # 只规划不落板（只读）
python -m pcbagent.cli route --project <工程目录> --kipy             # kipy IPC 落板（需 KiCad 实例）
# 产物：<工程>/pcbagent-out/b3/route-report.json（逐网 plan + 批次 DRC diff）

# B1 门：探针电池（25 探针 vs kicad-cli，含 0.15/0.2/0.25 边界反例）
python tests/run_b1_gate.py --project <工程目录>

# B2 门：Rev-C 两点回验（p3 布局 + 当前板；命中率 ≥70% + 3V3 逃逸 ≥15/22）
python tests/run_b2_gate.py --project <Rev-C 工程目录>
```

## 设计要点（本包实现口径）

- **net 以名字为键**：KiCad 10 板文件里 net 无编号只有名字；netless 为 `""`。
- **多板同名防呆**：工程目录里可能有历史评估板（如 `expA-eval.kicad_pcb`），
  镜像与 DRC 只加载与 `.kicad_pro` 同名的 `.kicad_pcb`。
- **形状模型**（`geometry.py`）：一切铜 = `prim = (core ⊕ r)`，core ∈ 点/段/凸多边形。
  焊盘含旋转的真旋转矩形/圆角矩形/椭圆/自定义多边形；过孔按 layers 跨层建
  铜盘+钻孔（F..In2 孔不达 B 层）；zone 以 filled_polygon 多环实体（nonzero 绕数）。
- **精确几何**：seg-seg/prim-prim/绕数全量精确计算（禁栅格近似下结论），
  含 p5_ground 时代四项修复的回归测试（单位一致/轴对齐粗检/seg-rect 漏中段/边界 EPS）。
- **L1 判定口径**（`config.py` 可调，默认对齐 kicad-cli severity=error）：
  铜铜 = max(两网类 clearance)（本板全类 0.2）；孔铜 0.25；板边 0.5；
  hole_to_hole 为 warning 不计；
  **圆形铜多边形化余量**：CLI 对过孔盘/钻孔按内接多边形（max_error≈0.005mm）测间距，
  线段/焊盘精确——L1 对圆形参与者加 CIRCLE_POLY_SAGITTA=0.005 等效余量
  （B1 门五组边界探针实证）；
  `--refill-zones` 真值口径下 zone 会为新铜让位（REFILL_ADAPTS_ZONE），
  过孔钻孔跨平面层须满足重灌孔间距约束；
  **track_angle 不强制**（净区 30° 走线 CLI 零违规，实证校准；L3 仍只用 45° 路径）。
- **L1 返回值**：`(ok, margin, violator)`，margin = min(实际表面间距 − 要求间距)，
  ≥0 即合法；violator 为最紧约束障碍描述。
- **每次改动 Rev-C 板**必须走 SPEC §4.2 提交纪律（快照 → L1 终判 → kipy 事务 →
  ≤10 网 batch CLI 复核 → 违规整批回滚）；镜像模块绝不写板。
- **L2 拥塞模型口径**（`planner.py`，调参全在 `config.L2_*`）：
  0.5mm 粗格 × F/In2 双层，每格 5×5 子采样按"铜面 + 间距 + 0.15 新道半宽"
  判堵，格容量 = floor(自由宽/0.35)，只有 0/1 两态；
  PathFinder 协商（SPEC §3.2）：零容量格不硬封锁，付 `L2_RIPUP_COST_MM` 拆让
  代价穿越，过载格 = 占用电位数 > max(容量,1)，逐代历史累加至过载稳定；
  命中口径 = 走廊 ∩ 过载格，已布板场景另计"需拆让"（穿越 cap0 格）——
  两口径分别存证（B2 门 per-pair.json）。
- **planner 零文件写**：产物全部内存生成（`build_products()` → {文件名: 文本}），
  落盘由调用方执行（Mimosa 钩子拦截包内 .py 的变量路径写盘，S2 实测）。
- **L3 路由器口径**（`router.py`，调参全在 `config.L3_*`）：
  区域 = 端点 bbox+3mm 裁到板内；0.05mm 精细栅格静态障碍图（异网铜/孔/板边按
  间距+候选线宽膨胀，同网豁免=同电位可达），A* 8 邻 45° 纪律（对角防切角）+
  F↔In2 过孔迁移（独立 via 位图）；L2 走廊软约束（偏离每格 +0.15mm 等效）；
  候选路径转 45° 段后逐段 L1 终判（margin>0 口径），失败→局部加障重搜
  （≤6 轮）；A* 不可达时洪泛封堵归因（"被谁挡"进报告）。
  **rip-up**（SPEC §4.1）：终判阻塞/不可达归因出的可拆邻网（非 GND、焊盘 ≥2）
  预算 3 内试拆——被拆铜在障碍图与 L1 终判（legality.ignore_ids）同时视同
  已删，本网成功后被拆网同轮重布（本网新铜作其障碍），任一失败内存回滚。
  **分支线宽口径**：PWR 网按 0.2 分支宽 + 0.6/0.3 过孔（0.5 主干宽在
  0.5mm pitch 引脚场无位，dry-run 实测；电源干加粗属 GUI 人工调）。
  新铜 uuid 由内容 sha256 派生（确定性）。
  **走廊中继分段**（S4 实战新增）：直线距离 ≥ L3_SEG_MIN_MM（8mm）且
  corridors.json 有该断点对走廊的靶，自动沿走廊每 L3_SEG_INTERVAL_MM（7mm）
  取净空中继点、逐段 route_net（层连续性=前段到达层；前段过孔收尾则后段
  任意层）、聚合单 Plan 走提交纪律；`--no-segment` 关闭。
  中继点必须净空（L2 走廊是协商语义可穿越占用格，硬交接点不行）。
- **提交纪律**（`commit.py`）：快照 → 逐网落板（惰性生成器保证每网 L1 基于
  最新板态）→ 每 ≤10 网 kicad-cli（refill+save 口径）与基线 diff → 任何新增
  违规整批回滚快照（宁误杀不放行）。落板后端可插拔：SexprWriter（无头直写，
  via 类型跟随存量 buried 口径）与 KipyWriter（kipy IPC 事务，S4 实战）。
- **L4 桥口径**（`bridge.py`）：verify 基线链 = --baseline 显式文件 >
  b4/verify-last.json（上次快照滚动）> 首跑建立；**回归 = 出现基线没有的新增
  违规**才算失败（存量违规不计）。length：镜像 track 段欧氏长合计 + 0.2mm/过孔
  （板无 arc——实测 0 条，与 pcbnew GetLength 同语义；pcbnew GetTracks 含
  footprint 内嵌段，mirror 的 s-expr walk 同样递归，口径一致），九组表
  `config.LENGTH_GROUPS` 与 revc/length-report.py GROUPS 同源——对账 113 项
  逐键一致（`out/b4/`）。render：kicad-cli `--mode-multi` 每层一 SVG
  （`--check-zones` 保证铺铜入图、`--page-size-mode 2` 只取板域）。
  audit-checklist：§4 七条款 + 工具可测证据（每网铜长/过孔数/分层段数）预填，
  视觉判定 advisory 非裁决。B5 施工包（`tests/run_b5_kit.py`）：批序按
  routing-spec §9 布线顺序、同批内距离升序、每批 ≤`GUI_KIT_BATCH_PAIRS` 对，
  走廊标注对账 corridors.json pair 键（round 3 位），GND 单列末批。

## 测试

```bash
python tests/test_geometry.py            # 几何内核 7 项（合成数据，不依赖 Rev-C）
python tests/test_planner_synthetic.py   # L2 合成板 4 项（拥塞/逃逸/确定性，自包含）
python tests/test_router_synthetic.py    # L3 合成板 8 项（route/ripup/分段/提交纪律全流程含 kicad-cli）
python tests/run_b5_kit.py --project <Rev-C 工程>   # B5：gui-session-kit 生成（确定性）
python tests/run_b1_gate.py --project <Rev-C 工程>   # B1 门（需 F:\kicad）
python tests/run_b2_gate.py --project <Rev-C 工程>   # B2 门（两点回验，约 5 分钟）
"F:\kicad\bin\python.exe" tests/pcbnew_export_ref.py <工程> out/checks/pcbnew-ref.json
python tests/check_mirror_vs_pcbnew.py --project <工程> --ref out/checks/pcbnew-ref.json
```

## 产物目录

- `out/b1/`：B1 门报告（`b1-gate-report.json/.md`）+ 每探针 DRC 副本
- `out/b2/`：B2 门证据副本（gate.json / per-pair.json / b2-gate-report.md /
  两点四产物 / run.log）；主产物在 `<Rev-C 工程>/pcbagent-out/b2/{p3,current}/`
- `out/b4/`：B4 门报告（`b4-gate-report.json`）+ 四命令运行日志 +
  pcbnew 对账参考 JSON + 确定性抽查副本；S4 门复核证据（合成板重跑 +
  板态 DRC 对账）同在此
- `out/checks/`：pcbnew 交叉验证参考 JSON
