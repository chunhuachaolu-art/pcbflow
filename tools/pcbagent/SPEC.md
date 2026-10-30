# PCB Agent 工具链 设计规格 v1（暂名 pcbagent）

> 定位：让 agent 能端到端驱动 KiCad 画板的确定性 Python 工具链。
> 治的两个病（2026-08-28 复盘确诊）：
> ① 布局与详细布线之间缺"全局布线/拥塞评估"阶段，拥塞不反馈布局（最后 61 条信号断点
>   卡在受限走廊、3V3 卡引脚场逃逸容量不足的根因）；
> ② 布线位置没有实时合法性反馈与逐网修正手段（KiCad 交互布线器无 API、Freerouting 是
>   全局批处理、自研全板 A* 25 分钟/网不可用）。
> 原则：纯确定性（numpy+heap，无随机）、kicad-cli 是唯一 DRC 裁决源、工具绝不写不被
> 验证的铜、Freerouting v1.9 退居 bulk 布线环节（本工具管规划+最后 61 米+验证）。

---

## 0. 总架构与命令面

```
python -m pcbagent <cmd> [--project <dir>] [参数]
  mirror-info          板镜像统计（pads/tracks/vias/nets/断点）
  congestion           L2：拥塞分析（热图+走廊指派+布局反馈+逃逸审计）
  escape-audit         L2：引脚场逃逸容量审计（可单独跑）
  corridors --net X    L2：单网走廊查询
  placement-iterate    L2：红区时的受约束布局迭代（拥塞→改布局→重验闭环，见 §3.5）
  route --net X        L3：单网详细布线（区域受限+拆迁预算）
  route --batch F      L3：按 opens.csv 批量
  verify               L4：kicad-cli DRC 封装 + 与上次结果 diff（回归检测）
  length               L4：等长组报告（移植 revc/length-report.py，九组口径）
  render               L4：分层 SVG/PNG 渲染（供 VLM 审计/人看）
  audit-checklist      L4：从 routing-spec §4 生成视觉审计清单文件
```

所有命令：读工程内 `.kicad_pcb`/`.kicad_pro`，产物落 `<project>/pcbagent-out/`，
退出码非零=失败，产物自带 JSON 与人读 MD 两份。

## 1. L0 板镜像（BoardMirror）

- 加载：优先 kipy 连运行中的 KiCad 实例；无实例则直接解析 .kicad_pcb（s-expr）。
  两者产出统一内存模型。
- 内存模型：
  - `Pad`：旋转矩形（GetBoundingBox 语义）+ net + 父封装 + 层集 + 钻孔
  - `Track`：(层, 端点对, 线宽, net)
  - `Via`：(x, y, 盘径, 孔径, net)
  - `Zone`：填充多边形（只作障碍，不作连通源，除非 verify 确认已灌）
- 服务：
  - `rasterize(layer, bbox, res)` → numpy 占用栅格（uint16 编码 net id + 类型位）
  - `connectivity(net)` → 并查集连通分量（pads/tracks/vias/已灌 zone）
  - `sync()`：从磁盘重读（外部改动后）
  - `opens()` → 当前未连接清单（与 kicad-cli 口径对齐的字段）
- KiCad 10 坑（必须处理）：层常量 F=0/B=2/In1=4/In2=6；net 以名字为键（文件里无编号）；
  `Remove()` 句柄损坏——镜像只读，写路径走 L3 commit；zone 未灌时连通性单独标注。
- 抽取来源（只读参考，代码重写进本包）：revc `exec/p5_ground.py` v3 的占用网格与
  精确几何检查器、`<HOME>/.kicad-mcp/gui_lib.py` 的旋转矩形障碍模型。

## 2. L1 合法性 API（毫秒级实时反馈原语）

- 接口：
  - `seg_legal(layer, p1, p2, width, net)` → (ok, min_clearance, violator)
  - `via_legal(x, y, net, from_layer, to_layer)` → 同上（盘 vs 全层铜 + 孔 vs 全部孔）
  - `pad_legal(rect, layer, net)`、`crosses(zone_keepout, ...)`
- 规则来源：解析 `.kicad_pro` 的 net classes（线宽/间距/过孔 per class）+ 板级默认 +
  局部规则区（Rev-C 的 U3 0.15 区）。**网络类感知**是硬要求。
- 实现：候选集粗筛（bbox 索引）→ 精确数学（seg-rect/seg-seg/圆-矩形，含旋转）；
  禁止只用栅格近似下结论。
- **验收（B1 门）**：对当前 Rev-C 板做 ≥20 个随机探针（合法/非法各半，含 5 个贴近
  0.15/0.2 边界的），L1 判定与 kicad-cli DRC 判定 100% 一致；单查询 <10ms。
  任何不一致= L1 bug（CLI 永远赢）。

## 3. L2 拥塞规划器（治"受限区域最后硬啃"的病）

### 3.1 粗网格
- cell 默认 0.5mm（≈1 条 0.15 线 + 0.2 间距的容量单元），可配。
- 每格每信号层容量 = floor(cell / (width_nc + clearance_nc))，再减去障碍占用
  （pad/via/已有铜按面积折算容量损失）。
- 净连通需求：netlist + net class 的层偏好（routing-spec §5 的层职责表）。

### 3.2 算法：PathFinder 协商拥塞（经典且确定）
- 所有网络先按 MST 粗布（允许重叠）→ 迭代：逐网拆开重布，
  边权 = 长度 × (1 + h_hist × p_present)；过载成本随迭代累积。
- 收敛判据：零过载（绿）；max_iter 内未收敛（红）= 布局本身超容，输出布局反馈。
- 规模估计：~100×100 格 × 2 层 × ~90 信号网 × ≤50 迭代 → numpy+heap 分钟级。

### 3.3 产物（congestion 命令）
1. `congestion-{F,In2}.svg`：拥塞热图叠板轮廓（人一眼看懂）
2. `corridors.json`：逐网粗走廊（cell 序列 + 每段层）——L3 的输入 / GUI 会话的施工图
3. `placement-feedback.md`：持续过载格 → 具体元件移动/旋转建议（只建议不执行）
4. `escape-audit.md`：**每个封装每侧边的逃逸槽数 vs 需求数**——直接对症 Rev-C 的
   3V3 22 条卡引脚场那一类
5. `gate.json`：绿/黄/红 + 数字（红=布局不放行进详细布线）

### 3.4 验收（B2 门，Rev-C 回验）
- 在 `snapshots/p3-placement-gates-pass`（布线前布局）和当前板上各跑一次。
- 命中率：61 条实际断点中，端点间走廊穿过预测过载格的比例 ≥70%。
- 逃逸审计至少命中 3V3 那 22 条里的 15 条（引脚场容量不足类）。
- 未达标 → 容量模型调参（cell 尺寸/障碍折算系数）后复测；仍低则如实报告并修订规格。

### 3.5 布局闭环迭代（placement-iterate）——把"建议制"升级为"闭环制"

v1 版 placement-feedback 只出建议文档，改布局一跳无人执行（半开环缺陷，2026-08-28
评审补入）。本命令闭环化：

- 触发：`congestion` 输出 gate=红（PathFinder 不收敛或过载格超阈）。
- **锚件锁死**：连接器/U1/U2/晶振/USB 保护件（placement-spec §1 机械锚）永不自动移动
  ——移动锚件须人工并重过布局规范全部六门。
- 候选生成（确定性，禁随机）：非锚件动作集 = 平移 ±{0.5,1,2}mm × 4 向、原地旋转 90°、
  同封装位互换；按（所在格拥塞贡献降序， ref 字典序）固定顺序枚举。
- 接受准则（全过才落，否则回退试下一候选）：L1 庭院/间距合法 + placement-spec 布局门
  重过（就近距离/通道宽 ≥7.5mm 等）+ 重跑全局布线后拥塞分严格下降。
- 预算：≤20 候选/轮 × ≤5 轮；耗尽仍红 = 输出"结构性超容"报告（需要人改架构级布局）。
- 输出：`placement-diff.csv`（ref/旧位姿/新位姿/拥塞分变化）+ 更新版 gate.json 与热图。
  此阶段板无铜，应用只需快照+庭院验证（§4.2 全流程不适用）。
- 验收（B6 门，合成板）：≥12 封装合成板人为压成红区，placement-iterate 须在预算内翻绿
  且布局门全过；Rev-C 豁免（布局已冻结、板已布 80%——本命令服务未来板）。

## 4. L3 区域受限详细路由器（治"无实时反馈修正"的病）

### 4.1 调用与流程
- `route --net X`：区域 = 网端点 bbox + 3mm 边距（可调）裁到板内；
  精细栅格 0.025–0.05mm 作搜索，L1 精确检查作终判。
- 搜索：A* on (x,y,layer)，过孔迁移成本 +0.2mm 等效；有 L2 走廊时走形成软约束
  （偏离走廊加成本）。
- **区域内拆迁（rip-up）**：与候选路径冲突的邻网（预算 N=3）可拆后必须在同轮重布
  成功，否则回滚——PathFinder 思想局部化。禁止拆 GND 缝合孔/平面引线。
- 每网报告：成功（路径+用时）/ 失败（阻塞原因清单：被谁挡、哪层满、建议人工动作）。

### 4.2 提交纪律（防 M2 事故复发，工具绝不写不被验证的铜）
1. 快照拷贝当前板 → 2. L1 对每条新铜段/孔终判（100% 过）→ 3. kipy 事务落板 →
4. 每 ≤10 网 batch 跑一次 kicad-cli（severity-error）→ 任何新增违规：整批回滚快照。
- 产出：`route-report-{net}.json` + 批次 DRC 前后 diff。

### 4.3 验收（B3 门，Rev-C 实战）
- 2 小时机时内收掉 ≥40/61 条信号断点，**零新增 DRC error**；
- 收不掉的每条给出走廊图 + 阻塞原因，刷新 `opens.csv` 供人机 GUI 会话按图施工。

## 5. L4 验证与审计桥

- `verify`：kicad-cli 封装（必须在工程目录跑；--refill-zones --save-board 口径），
  与上次结果 diff 出回归清单。
- `length`：移植 `revc/length-report.py`（九组口径对 routing-spec §3）。
- `render`：分层渲染（kicad-cli svg 输出或镜像自绘）。
- `audit-checklist`：从 routing-spec §4 生成视觉审计清单（对称性/蛇形纪律/绕远）；
  **VLM 调用不在本包内**（执行环境无视觉 MCP），由编排侧拿 render 产物+清单跑
  `analyze_image`，产物只作 advisory，永不作裁决。

## 6. 工程约定

- 代码：`<WORKSPACE>\tools\pcbagent\`（执行 agent 所有权的唯一可写区）
  结构：`pcbagent/{mirror,legality,planner,router,bridge,cli}.py` + `tests/`。
- 依赖：numpy（必需）、kipy（F:\kicad\bin\Lib\site-packages，落板用）、无 GUI 依赖。
- 测试：B1 探针电池、B2 回验、B3 实战都是测试；另加最小合成板单元测试（10 网
  假板，git 内自包含，不依赖 Rev-C）。
- 文档：README（用法）+ SPEC（本文件，变更需记录）；所有阈值/系数集中在
  `pcbagent/config.py` 常量，禁止散落魔法数。
- Mimosa 钩子：含文件写的 .py 可能被拦 → 沿用生成器模式（stdout 重定向落盘）。

## 7. 禁区与红线

- 禁改：design/coreboard 的两份规范、archive/、旧工程、三份交接文档、Rev-C 工程中
  除工具 commit 路径以外的任何文件。
- Rev-C 板的每次改动必须走 §4.2 提交纪律（快照→验证→落板→复核）。
- kicad-cli 永远是唯一 DRC 裁决；L1 与它冲突时 L1 错。
- 不引入随机性（no random seeds）；同输入同输出。
- Freerouting 不在本工具链内调用（分工：bulk 归 FR v1.9，规划/最后一公里/验证归本工具）。

## 8. 里程碑与工期（agent 工作日）

| 阶段 | 内容 | 门 | 估时 |
|---|---|---|---|
| B1 | L0+L1 抽取加固 + 探针电池 | L1 vs CLI 100% 一致 | 0.5–1 天 |
| B2 | L2 拥塞规划器 + 逃逸审计 | Rev-C 回验 ≥70% 命中 | 1–1.5 天 |
| B3 | L3 区域路由器 | ≥40/61 收掉、零新增 error | 2–3 天 |
| B4 | L4 桥 + render/audit-checklist | 命令全通 | 0.5 天 |
| B6（可选） | L2 布局闭环 placement-iterate | 合成板红→绿翻转（§3.5） | 0.5 天 |
| B5 | 用工具续跑 Rev-C（残网走廊图→GUI 会话准备→F4/F5 衔接） | 按续接 v3 硬验收 | 衔接既有流程 |

合计 5–6.5 天（B6 计入则 5.5–7 天）。每阶段完成写 `PROGRESS.md`（沿用 Rev-C 惯例）
并停在该阶段的门上。B6 不阻塞 Rev-C 交付（其服务对象是未来板），排在 B4 之后、
B5 之前或之后由规划方定。
