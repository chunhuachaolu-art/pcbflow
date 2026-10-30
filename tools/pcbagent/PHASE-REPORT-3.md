# PHASE-REPORT-3 — S3 会话 / B3-建（L3 区域路由器实现 + 合成板单测）

- 日期：2026-08-29（单会话完成）
- 结论：**B3-建完成**。L3 路由器 + 提交纪律落板全链路实现，合成板 7 项单测全过
  （含 ripup 落板 + kicad-cli DRC 零新增验证）；Rev-C 板**零改动**（全程只读 +
  dry-run）。开工前 B2 门独立复核 PASS（p3 57/61、current 59/61、3V3 21/22，
  EXIT=0，`out/b2/s3-rerun.log`）；legality 改动后 B1 门复验 25/25 一致
  （p95 0.87ms，`out/b1/s3-rerun.log`）。**实战门（S4）未跑**——dry-run 科学
  数据与 S4 策略见 §4/§5，S4 有硬仗要打但路径明确。

## 1. 交付物

```
pcbagent/router.py    L3：Region（0.05mm 精细栅格静态障碍图：异网铜/孔/板边按
                      间距+候选线宽膨胀、同网豁免；独立 via 位图）/A*（8 邻 45°
                      纪律+对角防切角+F↔In2 迁移）/L2 走廊软约束/路径转 45° 段
                      （首末点用精确端点坐标）/L1 终判失败局部加障重搜（≤6 轮）/
                      A* 不可达洪泛封堵归因/rip-up（预算 3、禁拆 GND、被拆网同
                      轮重布、内存态天然回滚）/端点落铜校验/plan_uuid（内容
                      sha256 派生，确定性）
pcbagent/commit.py    提交纪律（SPEC §4.2）：CommitFlow（快照→惰性 plan 流逐网
                      落板→每 ≤10 网 kicad-cli 与基线 diff→新增违规整批回滚）+
                      SexprWriter（无头 s-expr 直写；remove_net 括号平衡手术删
                      网）+ KipyWriter（kipy IPC 事务，S4 实战用，本会话无实例
                      未联测）
pcbagent/legality.py  加 ignore_ids（rip-up 拆除中的铜在终判视同已删；默认空集，
                      B1 行为不变——S3 内复验 25/25）
pcbagent/cli.py       route 命令（--net/--pairs/--batch/--limit/--start/
                      --dry-run/--no-ripup/--kipy/--baseline-json）
pcbagent/config.py    全部 L3_* 调参常量
tests/test_router_synthetic.py  合成板 7 项（详见 §2）
README.md             L3 用法与口径
```

## 2. 合成板单测（7/7 全过，自包含，含 kicad-cli 真跑）

| 测试 | 覆盖 |
|---|---|
| test_route_basic | 空旷直连 + 全段/孔 L1 终判重验 margin>0 |
| test_route_gap_detour | 盘墙缺口绕行 + 路径必穿缺口带 |
| test_region_unreachable | 全高墙封死区域 → 失败报告含"不可达" |
| test_ripup | U9 引脚场 0.6mm 行通道被 SA 双层预置铜占 → 洪泛归因→拆 SA→SB 过通道→SA 绕外侧重布→**落板后 kicad-cli 零新增 + 两网连通** |
| test_determinism | 同板两轮 plan 段列表/孔/uuid 逐字节一致 |
| test_snapshot_restore | 快照/回滚板文件逐字节一致 |
| test_commit_end_to_end | cli route 完整链路：opens.csv 两网→SexprWriter 落板→基线/终局 DRC 零新增→opens 归零→板文件含新铜 |

## 3. 过程中修掉的坑（后续会话勿重蹈）

1. **np.int64 传播**：A* 回溯碰 numpy 数组元素，np.int64 经格心计算变
   np.float64 坐标，进 JSON/uuid 崩——回溯处全部 int() 截断。
2. **A* 层索引泄漏**：回溯节点层是内部索引 0/1，须转回 KiCad 层常量 0/6
   （planner._seg_of 有 LAYERS[li] 转换，本模块初版漏了）。
3. **L1 终判不认 excluded**：障碍图拆了 rip-up 网但终判仍查全板真铜 → 死循环
   重搜。legality 加 ignore_ids，router 在 rip-up 期间设置、finally 恢复。
   落板侧对齐：commit 真删（writer.remove_net）。
4. **A* 不可达无归因**：rip-up 只在终判失败后有 violator。加洪泛封堵归因
   （起点可达格洪泛→边界堵格反查异网铜 owner）——合成板与 Rev-C 实测归因准。
5. **netless 铜混进 rip-up 候选**：封堵归因给无网铜加了 [标签] → 被当可拆网
   浪费预算。netless 只进 violator 报告、不进候选。
6. **PWR 类 0.5mm 主干线宽卡死引脚场**（Rev-C dry-run 发现）：3V3 的 22 条
   断点全是引脚场逃逸/相邻 pad 跳线，0.5 宽在 0.5mm pitch 缝里无格可走。
   L3 改分支口径：L3_CLASS_WIDTH PWR→0.2 + 统一 0.6/0.3 过孔
   （config 注释含实测依据）。改后 0.5mm 免检短跳立即可收。

## 4. Rev-C 只读 dry-run 科学数据（S4 实战的靶场地图）

- 3V3 全组 22 条：**dry-run 可收 8 条**（含 0.5/2.0mm 免检短跳；F3 时代
  "卡引脚场"的网纯规划就能吃掉 1/3）。14 条不可达，封堵归因指向 FMC_NBL1/
  GPIO_PA15 等 BGA 边缘既有铜——引脚场确需更大动作。
- 61 条断点距离分布（opens.csv，决定打法）：
  **<8mm：27 条**（3V3×22 + VCAP2/GPIO_PB5/GPIO_PD3/SW_NODE/VBUS_RAW 各 1）
  8–15mm：6 条（5V_USB/FMC_A10/FMC_D7/FMC_SDNE0/VBUS_RAW/VREF+）
  **≥15mm：28 条**（FMC/LTDC/SDMMC2_CK/ETH/GPIO 长距跨板网）
- 失败样例定性：≥15mm 的网在 3mm 区域限制下必然"不可达"——**它们不是 L3
  单发靶子，是"L2 走廊引导的分段 route"靶子**（corridors.json 已有走廊，
  B2 命中 59/61）。dry-run 时 corridors 软约束已生效但区域裁剪把长走廊切在
  区域外。
- dry-run 产物：`<Rev-C 工程>/pcbagent-out/b3/route-report.json`（最后一次
  运行覆盖写）、`tools/pcbagent/out/b3-dryrun-3v3.log`（3V3 全组全量报告）。
- ⚠ 教训自纠：本会话两次前台 dry-run 与后台 3V3 全组**并发**覆盖了同一
  route-report.json（违反"同一时刻一个作业"）。S4 必须串行跑批。

## 5. 给 S4（B3-实战）的注意事项与建议打法

1. **先实现"走廊中继分段 route"再开战**：对 ≥8mm 的网，读 corridors.json 该网
   segments，沿走廊每 6–8mm 取中继点，逐段 route_net（前段终点=后段起点），
   聚合为一个 plan 落板。短距（<8mm，27 条）直接 route。门 ≥40/61 的可达
   算术：27 短距 + 6 中距 + 28 长距中若干 = 需要长距组贡献 ≥7 条。
2. **落板用 --kipy 前**：KipyWriter 未联测（本会话无 KiCad 实例）。S4 首用
   先在合成板/复制板上验证 begin_commit/create_items/save 链路；或全程
   SexprWriter（无头已验证，kicad-cli 直接吃）。**board.save 是否保真
   .kicad_pro 规则未验证**——谨慎起见 S4 优先 SexprWriter。
3. route 目标排序：opens.csv 行序（免检短跳在前）符合"先易后难"；但建议
   按距离升序重排（<8mm 全收后再攻长距），--limit/--start 支持分批。
4. 每批 route 前 mirror.sync() 已由 cli 的惰性生成器保证；批间 CLI 复核
   （--batch 默认 10）失败会整批回滚并停止——回滚后检查 route-report 的
   added 明细定位元凶网，把它排除后继续下一批（人工决策，不自动重试）。
5. L1 margin 口径已含 CLI 圆形多边形化余量，margin>0 即过（B1 实证）；
   批次复核"新增违规"按违规描述键整体 diff（宁误杀），位置归因经验见 B1 §4.4。
6. 2h 机时预算：dry-run 单网（区域 ≤16×16mm）0.5–5s；长距分段后单段同样
   量级。61 网含复核估计 30–60min，预算充足；先跑 --limit 5 全流程演练。
7. GND 4 条走平面不在 opens 靶内（opens.csv 已分离）；rip-up 禁拆 GND 已固化
   config.L3_RIPUP_FORBIDDEN。

## 6. 门状态与下一步

- B3 门（实战）：未跑（S4）。门数字：2h 机时 ≥40/61 收掉、零新增 DRC error、
  残网出走廊图+阻塞原因、刷新 opens.csv。
- 下一步 = S4：按 NEXT.md"下一步"执行。
