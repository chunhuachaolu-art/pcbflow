# PCB Agent 工具链 交接提示词（执行 agent 用）

> 你的任务：**从零建造 `pcbagent` 工具链（L0–L4 全平台），并以 Rev-C 板为试验板逐阶段验证，
> 最终用工具自己收掉 Rev-C 的 61 条信号断点（≥40 条为硬门）**。本工具链**按 §2 分会话协议
> 分 5 个会话执行**（防单上下文过载）；每个会话内全自动无停点、无头，只交本会话的
> PHASE-REPORT（中文）。你的任务由同目录 `NEXT.md` 的"下一步"字段指定（读不到 NEXT.md
> 视为协议被破坏：停止并报告，不要自行猜测任务）。
> 设计权威 = `<WORKSPACE>\tools\pcbagent\SPEC.md`（先通读，按它造；
> 发现设计错误可停笔写报告，不得自行改规格）。本文档自包含执行所需的一切路径与纪律。

---

## 0. 背景一句话

STM32H743 SoM 项目（Rev-C 板）布线收尾受阻：61 条信号断点卡在拥挤走廊，现有工具链
（Freerouting 批处理/KiCad 无路由 API/自研全板 A* 不可用）零贡献，确诊缺两层能力：
布局-布线之间的拥塞规划、逐网实时合法性反馈。你造的工具就是补这两层，并顺手救活这块板。

## 1. 权威输入（全部只读）

| 文件 | 用途 |
|---|---|
| `<WORKSPACE>\tools\pcbagent\SPEC.md` | **设计规格（唯一设计权威）** |
| `<WORKSPACE>\design\coreboard\kicad\stm32h743-coreboard-revc\` | 试验板工程（唯一板子；改动只准走 SPEC §4.2 提交纪律） |
| 同上 `\f3-stop-report-zh.md`、`opens.csv`、`drc-f3-round1-final.json` | 61 条断点真值与清单（B2 回验/B3 实战的靶子） |
| 同上 `\snapshots\p3-placement-gates-pass\`、`\snapshots\f3-round1-done\` | B2 回验的两个布局时点（布线前/当前） |
| 同上 `\exec\p5_ground.py`（占用网格+精确几何检查器，抽取源）、`\exec\p4d_finish.py`、`\revc\length-report.py` | L0/L1/L4 的代码抽取来源 |
| `<HOME>\.kicad-mcp\gui_lib.py` | 旋转矩形障碍模型（抽取源） |
| `<WORKSPACE>\design\coreboard\reports\routing-spec-v1.md` | §3 九组等长口径、§4 对称性条款（L4 用）、§5 层职责（L2 层偏好用） |
| `<WORKSPACE>\design\coreboard\reports\revc-resume-prompt-v3.md`、`revc-handoff-p4-continue.md` | Rev-C 上下文与工具坑史（§2 失败审计必读，勿重蹈） |
| `F:\kicad\bin\kicad-cli.exe`、`F:\kicad\bin\python.exe`（含 kipy） | 权威工具 |

## 2. 执行序（B1→B5，每阶段的门不过不进）

**【分会话协议——本工具链禁止单会话连续跑完，防上下文耗尽】**

- **启动指令（每次会话完全相同，用户无需跟踪进度）**：
  "读 `<WORKSPACE>\tools\pcbagent\HANDOFF-PROMPT.md` 与同目录
  `NEXT.md`，按 NEXT.md 继续"
- 状态自描述机制（三个文件各司其职）：
  - `NEXT.md`：**唯一被改写的状态文件**（每会话收尾重写，≤50 行）：下一步（S1–S5 之一 /
    DONE / BLOCKED+报告路径）、门状态表、关键产物指针、约束提醒。
  - `PROGRESS.md`：只追加的编年日志（证据链；**不作为"下一步"依据，无需通读**）。
  - `PHASE-REPORT-<n>.md`：每会话详细收尾报告（门数字/产物/偏离/给下家的注意事项）。
- 阶段-会话划分（每会话一个全新 agent 上下文）：
  | 会话 | 阶段 | 工作量 |
  |---|---|---|
  | S1 | B1（L0+L1） | 0.5–1 天 |
  | S2 | B2（L2 规划器+Rev-C 回验） | 1–1.5 天 |
  | S3 | B3-建（L3 实现+合成板单测） | 1–1.5 天 |
  | S4 | B3-战（Rev-C 实战 2h 预算） | 0.5–1 天 |
  | S5 | B4（L4 桥）+ B5（衔接打包） | 0.5 天 |
  | S6（可选） | B6（L2 布局闭环 placement-iterate，SPEC §3.5） | 0.5 天 |
- 每会话的四段式义务：
  1. 读 NEXT.md 的"下一步"字段确定本会话任务（DONE/BLOCKED 状态=说明现状后礼貌退出）。
  2. **独立复核上一道门**（不信任前会话自述）：按确定性命令重跑上一阶段验收
     （如 S2 重跑 S1 的探针电池）。复核不过=先修再进，并写明原因。
  3. 只做本阶段的事（只读 SPEC 对应章节+§3 坑表；不通读 Rev-C 历史文件与 PROGRESS 全文，
     NEXT.md 的指针够用）。
  4. 收尾三件事：写 `PHASE-REPORT-<n>.md` → **重写 `NEXT.md`**（推进指针或写 DONE/BLOCKED）
     → 向 `PROGRESS.md` 追加日志。然后停止。
- 上下文纪律：磁盘是唯一状态（一切结论从产物文件取，不凭记忆）；同一时刻只允许一个
  会话操作本工程（Rev-C U2 事故教训）；PROGRESS 只追加不改写，NEXT.md 是唯一例外。
- **BLOCKED 语义**：门在调参后仍不过，或发现 SPEC 设计错误——NEXT.md 写 BLOCKED+报告
  路径，等规划方（用户/主 agent）裁决，不得自行变通继续。

**B1 L0+L1（0.5–1 天）**：按 SPEC §1–§2 抽取重写（不是拷贝——接口化、网络类感知、
net 以名字为键）。门：≥20 探针电池 L1 判定与 kicad-cli 100% 一致 + 单查询 <10ms。
探针必须含 5 个贴 0.15/0.2 边界值的反例。

**B2 L2 拥塞规划器（1–1.5 天）**：PathFinder 粗布线 + 四产物（热图/corridors.json/
placement-feedback/escape-audit）+ gate.json。门：SPEC §3.4——在 p3 布局与当前板两点
回验，61 断点走廊命中率 ≥70%，且逃逸审计命中 3V3 22 条中 ≥15 条。未达标准调参复测，
仍不达标如实写报告（这是科学结论不是失败）。

**B3 L3 区域路由器（2–3 天）**：SPEC §4 全部纪律（快照→L1 终判→kipy 事务→≤10 网
batch CLI 复核→违规整批回滚）。门：2 小时机时 ≥40/61 收掉、零新增 error、残网出
走廊图+阻塞原因、刷新 opens.csv。**禁止为凑数放宽任何规则**。

**B4 L4 桥（0.5 天）**：verify/length/render/audit-checklist 四命令全通；length 九组
口径与 revc/length-report.py 对账一致。

**B5 Rev-C 衔接**：用 B3 成果更新板与断点清单 → 残网走廊图打包成 GUI 会话施工图
（`pcbagent-out/gui-session-kit/`：走廊总图 SVG + 分批清单 + 每批落盘后的 verify 命令）→
到此为止。**等长（F4）与制板（F5）不在本次范围**（等长要 GUI 调谐，属人会话）。

**B6 布局闭环（可选会话 S6，由 NEXT.md/规划方决定是否开跑）**：SPEC §3.5 的
placement-iterate——红区时对非锚件做受约束确定性移动（庭院合法+布局门重过+拥塞分
下降三重接受准则），合成板红→绿翻转为门；Rev-C 豁免（布局已冻结）。不跑不影响 Rev-C。

## 3. 已知坑（前人用算力换来的，全部实测）

1. kicad-cli DRC 必须在含 .kicad_pro 的工程目录跑，且 `--refill-zones --save-board` 才是
   连通性真值口径；拷出去跑会用默认规则出假违规。
2. KiCad 10 层常量 F=0/B=2/In1=4/In2=6；net 在文件里无编号只有名字；`pad.GetSize()`
   不含旋转（用 GetBoundingBox 语义）；SWIG `Remove()` 后句柄随机永久损坏（所以镜像只读、
   写走 kipy 事务）。
3. kipy 的 `kipy.board_rules` 导入即崩（0.7.1 打包 bug）→ DRC 只走 kicad-cli。
4. KiCad 10 板文件 zones 未灌时连通性会骗人——镜像里 zone 连通必须以 verify 过的已灌态为准。
5. 0.1mm 网格格心相对板原点偏 −0.05mm；窄合法窗内可能无格心（这是当年 A* 阵亡原因之一，
   L3 用 0.025–0.05 精细栅格 + L1 精确终判规避）。
6. Mimosa 钩子拦"含文件写的 .py"→ 生成器模式：代码走 stdout，bash 重定向落盘。
7. p5_ground v3 里修过的 bug 清单（单位混用/轴对齐粗检/seg-rect 漏中段/抖动坐标）——
   抽取时这些修复必须带上，见该文件头部注释与 revc PROGRESS.md F1 节。
8. 长任务不杀不重跑；单会话作业；全程无头（不碰 GUI）。

## 4. 硬验收（全部门过了才算完）

- B1–B4 各门全过（数字见 SPEC §2/§3/§4）；
- Rev-C 板：信号断点 61 → ≤21，且**全程零新增 DRC error**（以磁盘重载 kicad-cli 为准）；
- 工具链：SPEC §0 全部命令可用，同输入同输出（确定性）；
- 交付物：`tools/pcbagent/`（代码+tests+README）+ `pcbagent-out/`（B2 回验报告、B3 战报、
  GUI 会话施工图包）+ 最终中文报告（各门数字、偏离清单、残网清单与原因）。

## 5. 禁止事项

- 禁改 SPEC 之外自行扩大/缩小范围；禁改 Rev-C 之外任何 coreboard 文件、两份规范、
  archive/、三份交接文档；
- 禁绕过 §4.2 提交纪律直接写板文件；禁把 L1/自测当 DRC 终审（kicad-cli 唯一）；
- 禁引入随机性；禁未过 B3 门就宣称"工具成功"；禁生成 Gerber 冒充完成（等长/制板不在范围）；
- 禁在失败后无休止重试同一参数（调参要改 config.py 常量并记录）。

——开工前先通读 SPEC 与 revc-handoff-p4-continue.md §2（失败审计），别用自己的算力
重买前人已付的学费。
