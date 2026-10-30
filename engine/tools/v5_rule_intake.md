# v5 内源规则 intake 模板（V5-R7 W-4，2026-10-04）

> 渐进补规则机制成文件。流程：**intake 违例 → kicad-cli 归因 → 内源缺规则
> 判定 → 补条目工作包骨架**。每次 kicad-cli（外权威）对 v5 导出件报出
> v5.drc 未覆盖的违例类，按本模板逐项登记与裁决——**按板集需求渐进**
> （V5-CAPABILITY-GAP-RULINGS-2026-09-23 §4），不预先发明 DSL。
>
> 登记纪律：候选先入「候选登记表」；裁决=入列（立工作包骨架）/暂缓（外权威
> 兜底）/驳回（非规则面）。暂缓项须给理由与再评估触发条件。零渲染零读图；
> 全部事实引用 file:line 或命令输出。

## 1. 流程（五步）

1. **违例采集**：`kicad-cli pcb drc run <board>.kicad_pcb --severity error` 输出
   （含类型 code、计数、逐条坐标）。v5 侧对照 `route_check.check_routes` 的
   violations/edge_violations/hole_violations——**只在 kicad 报而 v5 不报
   （或量级失真）的类**进入下一步。
2. **归因**：逐类回答「为什么 kicad 报而 v5 不报」——三选一：
   a. **口径差**（v5 有对应判定但口径不同，如中心线 vs 边到边）→ 归
      `kicad_export` 换算面（参照净类换算 docstring 先例）；
   b. **内源缺规则**（v5 无任何对应判定）→ 进入第 3 步；
   c. **世界模型外**（几何本体未入模）→ 归 adapter/intake 面（先补事实源）。
3. **内源缺规则判定**：该规则是否影响**布线决策**（executor 拒布/检查器
   feasibility）？——只影响制造的（阻焊/丝印/annular ring 等）= 外权威兜底
   暂缓；影响布线的（间距/边距/禁布类）= 候选入列。
4. **补条目工作包骨架**（入列项填）：
   - 事实源：哪个载体声明该规则（.kicad_pro / .kicad_pcb / .kicad_dru /
     kicad-cli 生效缺省）＋解析口（adapter W-1 双源优先序同构）。
   - schema 兼容键：键名/形状/缺省语义（缺省路径零漂移是硬约束）。
   - 判定器：v5.drc 单源（谓词签名/擦边口径 EPS 同族）。
   - 消费面：executor 障碍栅格（保守 max 首版 / per-class 分层改进候选，
     内存耗时影响如实呈报）＋ route_check 披露/归责面。
   - 导出面：kicad_export 透传（如适用）＋掩蔽窗口表随件。
   - 钉值族：正反面合成板 + 既有板零漂移钉死 + 语料全量转换过。
   - 版本面：触碰模块版本升位 + 既有钉值测试同步（R8 F1 先例）。
5. **收口**：任务书冻结 → 实现 → 全量绿 + 双跑确定性 ≥2 板 → 登记「已入列」。

## 2. 候选登记表

| 候选 | 状态 | 裁决日 | 理由 | 再评估触发 |
|---|---|---|---|---|
| annular ring（环宽） | 暂缓 | 2026-10-04（V5-R7 任务书裁决依据） | 与布线决策无关（纯制造类：过孔环宽由 via_model 几何定死，布线器无可避让自由度）；外权威 kicad-cli 兜底 | 板集出现「环宽违例导致返工」证据面 |
| 阻焊（solder mask） | 暂缓 | 2026-10-04（V5-R7 任务书裁决依据） | 与布线决策无关（阻焊桥/开窗是制造工艺面，v5 世界模型无阻焊层几何）；外权威兜底 | 语料板集出现阻焊相关可布性冲突（如阻焊定义的禁布语义） |
| 多套 net class 间距 | **已入列** | 2026-10-04 | V5-R7 W-1/W-2 已实现（board.net_classes + R5 网对取值 + per-class 导出） | — |
| 真实板轮廓边距带 | **已入列** | 2026-10-04 | V5-R7 W-3 已实现（board.outline_mm + OutlineBand + executor/导出消费） | — |

## 3. 已入列项回填（本批 V5-R7）

- **多套 net class 间距**：schema `net_classes`（schemas/board.v1.schema.json，
  兼容键）；解析 kicad_adapter v0.5.0（双源优先序 P1..P5 钉于
  out/v5-p5/r7/probe_priority.py）；判定 v5.drc 0.4.0 `check_clearance(
  net_clearance=)`（网对 max）；executor 0.10.0 保守 max 近似（首版）；
  导出 kicad_export 0.6.0 per-class + `.netclass-mask.json` 消除表。
- **真实板轮廓**：schema `outline_mm`；adapter 解析 Edge_Cuts（线/矩形/弧
  双形/圆/多边形/贝塞尔离散；开口/自交 fail-closed 与 kicad-cli 同口径）；
  v5.drc `OutlineBand`（栅格化桶+解析精判；矩形外环≡workspace 矩形带）；
  executor/route_check 同带消费。

## 4. 使用注意

- 本文件是模板+登记簿（tools/ 白名单面）；每批新候选**追加**行，不改历史行
  （审计需要）。
- 「与布线决策无关」是暂缓的唯一充分理由族；出现反例证据（该规则实际改变
  布线可行域）即再评估。
- 登记类哈希禁手抄（程序化注入）；本表不携带任何 hash。
