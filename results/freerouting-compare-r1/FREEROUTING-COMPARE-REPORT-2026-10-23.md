# Freerouting 对照批报告（FREEROUTING-COMPARE-2026-10-23）

- 任务：SELFIMPROVE-V2 后续「Freerouting 对照批」——补 F-REPORT §2「Freerouting 2.4.1 未对照」缺口。
- 授权：用户 2026-10-23「后续哪些可以并行，请现在就做」（F-REPORT §8 后续项）。
- 产物根：`<ENGINE_ROOT>\out\freerouting-compare-r1\`（本目录）。
- V5 侧零新跑：读数全部取自 `out/selfimprove-v2/pipeline/data/rollouts.jsonl` 在盘记录（e2-gate1 / e2-gate-base / e2-retro）。
- 红线三板（pslab-v6 / sdi-mipi-bridge / tinytapeout-demo，B-manifest rules.redline）全程零接触。

## 0. 一段话结论

4 板中 3 板主口径可比：Freerouting 2.4.1 无一劣于 V5（z2prog/uno 线长-过孔-墙钟全面占优、TTN 混合各有胜负），名义布通率差（FR 1.0 vs V5 0.82/0.88）与两世界单焊盘网数**4/4 板完全对齐**，大概率是分母结构而非引擎能力；Lcr 主口径不可比（板方言：重复 REF** 引用致 KiCad DSN 导出拒绝），披露性修复变体（仅重标注引用）方向性同前。按纪律不给全局胜率（4 板非全可比）。

## 1. 方法链（P0 口径复用，零另造）

与 freerouting-baseline-r1（P0）完全同链，P0 四脚本按绝对路径只读复用：

strip（去 track/via/zone，起点对齐 V5 世界）→ `pcbnew.ExportSpecctraDSN` → `java -Xmx4g -jar freerouting-2.4.1.jar -de … -do … -mt 1 --router.job_timeout=00:30:00`（本批帽 1800s/板）→ `pcbnew.ImportSpecctraSES` → kicad-cli 10.0.5 DRC → `metrics/recompute.py`（routed 模式）。

本批与 P0 的差异（如实）：
- DRC 由 P0 的 P5-UP3-aggregate-v1（5 跑×≤3 轮）改为**单跑**——本批只消费 unconnected_items/网名（布通率），不消费违例总数对比；P0 实测该口径 totals 确定性，单跑漂移风险登记于 fr-result.json protocol 字段。
- Freerouting 阶段经 pwsh Start-Process 包装（记账墙钟+CPU TotalProcessorTime）；SES 先写逐尝试唯一名 `route-att<N>.ses`、非空校验后 os.replace（防 §5 环境新坑）。
- 布通率网级读数：DRC unconnected_items 的描述文本提取 distinct 网名，completion = 1 − 未连通网数/总网数（对齐 V5 fully_routed_nets/signal_nets 网级口径）；辅以 console 未布通项（ratsnest 项级，分母不同，只作旁证）。

## 2. 板集与输入对账

4 板全部 pcbench-r1，raw.kicad_pcb sha256 对 B-manifest.json 预注册值全符（工具核验 2026-10-23）；V5 侧 board.v1.json 的 input_sha256 与 rollout 记录 sha 绑定全符（4/4）。

## 3. 对照表（主表）

列：布通率（网级）｜总线长 mm｜过孔｜墙钟 s。FR=Freerouting 2.4.1（-mt 1）；V5 guide=e2-gate-base；V5 policy=e2-gate1（ck1 晋级策略 S2-pe1-risk-late）。

| 板（网数） | Freerouting | V5 guide | V5 policy | FR 墙钟附注（CPU s） |
|---|---|---|---|---|
| z2amiller_sensorboard_programmer（11） | **1.0**（11/11）｜**149.48**｜**1**｜11.60 | 0.8182（9/11）｜166.78｜16｜3.95 | 0.8182（9/11）｜162.08｜12｜498.27 | att3 过（att1/2 触 §5 瞬态）（CPU 6.92） |
| kitspace_Arduino_uno_sheild（34） | **1.0**（34/34）｜**1017.95**｜**8**｜**12.21** | 0.8824（30/34）｜1150.82｜120｜9958.99 | 0.8824（30/34）｜1111.59｜108｜8192.44 | att1（CPU 41.39） |
| TTNEnschedeMote_ArduinoNanoRN2483（30） | 1.0（30/30）｜506.48｜**12**｜11.22 | —（无独立读数） | 1.0（30/30）｜**499.26**｜40｜**7.98** | att1（CPU 12.41） |
| kitspace_Lcr_addon（21） | **链路失败（DSN 导出拒绝）→ 主口径不可比** | —（无读数） | 0.9524（20/21）｜880.89｜44｜43.61 | —（见 §4） |

臂可得性登记：z2prog 双臂；uno 双臂；TTN policy 序=guide 序（retro-final-report.json `policy_eq_guide=true`，e2-retro/460 单读数即 guide 读数，双列同值）；Lcr 仅 policy 臂（e2-retro/459 为 ERROR 记录，argparse usage 报错，非读数）。

TTN 行说明：guide 列与 policy 列同值（499.26｜40｜7.98），表中只列一次。

### 布通率口径差（重要，影响全部名义差）

V5 世界把**单焊盘退化分区计入分母**且计为未布通；KiCad 世界同款单焊盘网**无需连接**（DRC unconnected=0）。两世界单焊盘网数对齐情况：

| 板 | V5 退化分区数 | KiCad 单焊盘网数 | 对齐 |
|---|---|---|---|
| z2prog | 2/11 | 2/11（+5V、Net-(P1-Pad2)） | 一致 |
| uno | 4/34 | 4/34（Net-(A1-Pad31)、Net-(J3/J4/J5-Pad6)） | 一致 |
| TTN | 0/30 | 0/30 | 一致 |
| Lcr | 1/21 | 1/21（Net-(U3-Pad4)） | 一致 |

V5 未布通数恰=单焊盘网数（4/4 板完全对齐）→ 名义布通差（FR 1.0 vs 0.82/0.88/0.95）**大概率是分母结构而非引擎能力**（推断，未逐网进入 V5 引擎内部核验，如实标注）。扣除退化网后两侧布通实质打平（可布网双方全通）。

## 4. Lcr：方言根因 + 披露性修复变体（不入主口径）

- **主口径失败**：strip 成功（去 131 track/1 zone）但 `pcbnew.ExportSpecctraDSN` 返回 false 无异常，6 次重试确定性复现——与 P0 throwing-star 同症。
- **根因（二分定位）**：raw 板含两个引用同为 `REF**` 的 MountingHole 封装（未标注位号）——重复元件标识符令 KiCad Specctra 导出器拒绝；单独删掉任一个导出即恢复（drop REF**#1→True，drop REF**#2→True，drop 其他任一→False；去 PCB_TARGET/尺寸标注→仍 False）。V5 自有适配器容忍此缺陷（其 board.json 已转换在盘），故 V5 侧有读数。
- **修复变体（披露）**：在 strip 副本上仅重标注 MOUNT1/MOUNT2（几何零改动），全链即通：**1.0（21/21）｜818.26 mm｜1 过孔｜10.67 s（CPU 14.39）**，DRC unconn 0。此为方向性参考，不并入主口径结论。

## 5. 环境新坑（本批发现，已防御）

**Freerouting 输出 SES 间歇 0 字节**：java rc=0、console 正常止于 "Saving"、stderr 空、文件 0 字节。单跑发生率 p≈0.4–0.5，**随机且与命令构造无关**（A/B/C 二分复跑结果反转：模块等价构造成功、精简构造反而失败）。P0 九月批约 10 跑零此症——宿主侧变化（疑 AV/索引器对新建文件的写竞争），未根治。对策=逐尝试唯一输出名+非空校验+os.replace+重试上限 6（P(全败)≈1.6%）；本批 z2prog att3 通过，其余 3 板 att1 通过。

## 6. 消费记账（Freerouting 侧，如实）

- 生产链 java 墙钟/CPU：z2prog 11.60s/6.92s（att3）＋att1/2 失败尝试 ≈31s 墙钟（由 console 时间戳差估计，CPU 未记）；uno 12.21/41.39；TTN 11.22/12.41；Lcr refix 10.67/14.39。
- 诊断消费（0 字节瞬态定位）：冒烟+复跑+手工+二分共约 11 次 java 跑 ≈2 min 墙钟、KiCad python 探针 3 次 ≈10 s。
- 逐板全链墙钟（含 strip/DSN/SES/DRC/指标）：z2prog 48.9s（前两次失败链另 18.2s+47.0s）、uno 26.5s、TTN 22.3s、Lcr 主链在 DSN 段止步（refix 变体全链 ≈35s）。批总墙钟（含全部调试）≈18 min，远低于 4h 帽；单板 Freerouting 最长 12.2s，远低于 1800s 帽。V5 侧零新跑、零消费。

## 7. 规则注记

4 板 KiCad DSN 净距规则一致：clearance 200 um、smd_smd 50 um。V5 侧（board.json hard_rules 样例 z2prog）：R5 min_clearance 0.2 mm（与 DSN 同量级，异于 P0 corpus-r2 板的 0.5 mm 恒定）、R1 线宽下限 0.3 mm。规则大体同量级，但两引擎各自按各自世界校验，线长/过孔仍按 §8 限制作方向性对照。

## 8. 口径与局限（对照表解读边界）

1. **几何世界不同**：V5=board.v1.json 抽象端点世界（真实 mm 坐标系、焊盘抽象为端点、分区化）；Freerouting=KiCad 真实板（strip 后保留真实焊盘几何）。线长/过孔为同坐标系的**方向性**对照，不是同任务严格可比。
2. **墙钟协议不同**：V5 wall_s=完整 rollout 协议（24 候选生成+select_best）；FR=单遍布线+优化。数量级差（uno 2.3–2.8h vs 12s）反映的是协议+引擎双重差异。
3. **DRC 判据同源不同板基底**：本批未跑 P0 的 drc-floor（主表不消费违例总数）；fr-result.json 登记布线后 violations_total（24/26/60/15）仅供追溯。
4. **布通率分母结构**见 §3；Lcr 主口径链路失败见 §4。
5. Freerouting 确定性沿 P0 §4 结论（同命令同输出名双跑 SES sha256 字节等；种子硬编码 Random(0)），本批未重复双跑验证（预算纪律），z2prog 三次重跑 console 分数一致（999.99/0 unrouted）为旁证。

## 9. 产物清单（全部绝对路径）

```
<ENGINE_ROOT>\out\freerouting-compare-r1\
├── FRCMP-STATE.md                          断点件（任务边界+执行日志）
├── FREEROUTING-COMPARE-REPORT-2026-10-23.md 本件
├── scripts\run_compare.py                  逐板驱动（P0 脚本绝对路径复用+pwsh 记账+SES 瞬态防御）
├── scripts\count_nets.py                   KiCad 侧网清单（分母对账）
├── scripts\refix_and_run_lcr.py            Lcr 披露性修复变体驱动
├── scripts\refix_refs_kipy.py              引用重标注（KiCad python 侧，脚本生成）
├── runs\<board>\                            逐板：stripped/board.dsn/console.log(+err)/route.ses/
│   routed.kicad_pcb/drc.json/fr-result.json/countnets.log/strip.log/exportdsn.log/sesimport.log/
│   （Lcr 另有 fr-result.json=主口径失败记录、fr-result-refix.json/stripped-refixed/board-refixed.dsn/
│    route-refixed.ses/routed-refixed.kicad_pcb/drc-refixed.json 修复变体件）
└── compare\compare-rows.json               对照表机读正本（含 V5 读数 sha 绑定/臂可得性/口径注记）
```

- 数据底座引用（只读）：`out\selfimprove-v2\pipeline\data\rollouts.jsonl`（V5 读数）；`out\selfimprove-v2\e2\retro-final-report.json`（TTN policy_eq_guide 证据）；`<PROJECTS>\freerouting-baseline-r1\`（P0 工具链与方法口径）。
- License：Freerouting 2.4.1=GPLv3，独立进程调用、零源码拷贝（沿 P0 注记）。
