# PHASE-REPORT-4 — S4 会话 / B3-战（Rev-C 实战布线）

- 日期：2026-08-29（单会话完成）
- 结论：**B3 实战门未过 → BLOCKED，等规划方裁决**。落板 **8/61**（8 条 3V3 引脚场
  短跳，**零新增 DRC error**，终局 unconnected 65→57），远低于门线 ≥40/61。
  与 S3"门算术"（27 短距全收 + 长距贡献 ≥7）相反，**S4 的全量 dry-run 科学
  数据给出本板态的上界只有 9 条**：其余 52 条在 DRC 规则层面无合法通道
  （干道双信号层饱和），与机时无关（实际用机时 ≈35min ≪ 2h 预算）。
  残网施工包已产出（走廊总图 + 逐网阻塞原因 + 刷新 opens.csv）。
- 开工门复核：B3-建合成板 **7/7 PASS**（`out/s4-gate-rerun.log`）。

## 1. 本会话交付物

```
pcbagent/router.py     + route_net_segmented（走廊中继分段：corridors.json 该对
                       segments → 每段 ≤7mm 取净空中继点 → 逐段 route_net →
                       聚合单 Plan）；+ _relay_chain/_relay_free（净空中继点
                       搜索：候选位落在异网铜间距禁区内时沿弧长 ±0.5mm 步进
                       滑动，窗口 ±0.6×interval）；Plan 带 segmented/n_relay/
                       ripups 列表（多拆迁聚合）
pcbagent/commit.py     落板序改 ripup_ops() 遍历（兼容单拆迁原口径）
pcbagent/cli.py        route 自动分段接线（--no-segment 关闭）；
                       _load_corridors_full 双口径（软约束按网合并 / 分段骨架
                       按断点对精确匹配 pair 坐标，61/61 全匹配）
pcbagent/config.py     L3_SEG_MIN_MM=8.0 / L3_SEG_INTERVAL_MM=7.0（新增）；
                       L3_MARGIN 3.0→6.0 复测无效→回 3.0（调参记录在注释）
tests/test_router_synthetic.py  +test_route_segmented（直连不可达+分段可达+
                       层连续+L1 重验+穿墙落缺口带断言），全套 8/8 PASS
<Rev-C 工程>/pcbagent-out/b3/    实战产物（见 §4）
```

## 2. 过程中修掉的坑（后续会话勿重蹈）

1. **_relay_chain 弧长累加器跨切割点不复位**：中继点定位全部错乱（子段乱序
   回绕）。修：每切割点从折线起点重新累计。
2. **_to_segments 同格层迁移原地替换吞段（S3 遗留，实战必踩）**：路径首/末
   动作即打孔时，端点侧铜段端点被吞，产生"从错误层出发"的假段。修：迁移点
   保留两层两个条目 + 首末同格两点吸附精确端点坐标。
3. **HoleItem 属性是 prim 单数**：_relay_free 初版写 h.prims 直接崩。
4. **端点过孔接触容差**：孔坐标是格心（距端点可达 0.025mm），端点落铜校验
   1e-6 容差必挂——孔接触容差放至半格（L3_RES/2+TOUCH_TOL）；分段"前段过孔
   收尾→后段任意层起步"同口径检测。
5. **Region added_prims 硬编码 BOARD_MIN_CLEARANCE=0.15（S3 遗留）**：ripup
   拆网重布时，重布铜只被要求离主 plan 新铜 0.15mm（类对间距 0.2），CLI 判
   clearance 新增→整批回滚。修：added_prims 带网名，按 clearance_between
   膨胀。合成板 8/8 复验过。

## 3. Dry-run 科学数据（本板态可布上界的证据链）

- 全量 dry-run（v1–v4 迭代，每轮都修坑后复测）：**61 靶稳定只有 9 条可收**
  （8×3V3 短跳 + SW_NODE）；34 条 ≥8mm 分段后**全部**仍死于某子段 A* 不可达。
- **中继点诊断**：失败分段网 205 个中继点中 144（70%）落在异网铜间距禁区——
  L2 走廊是协商语义（允许付代价穿越占用格），硬交接点不行。净空滑动修复后
  仍无整网解锁 → 墙不在中继点，在子段整体。
- **区域边距假设否证**：L3_MARGIN 3→6mm，3 探针网（LTDC_R6/FMC_A10/VREF+）
  全部仍不可达且机时翻倍 → 墙是宽区域饱和，不是薄障碍。已回 3.0。
- **直连 vs 分段**：中距网直连（整段区域装得下走廊）同样不可达 → 与分段
  机制无关。
- **干道饱和的数学**：0.5mm 焊盘/道间距内，两邻道膨胀区（类对间距 0.2 +
  候选半宽 0.1 + 余量 0.02 = 0.32mm/侧）需求 0.64mm > 0.5mm——**0.2 类间距下
  0.5mm pitch 的缝里不存在任何合法道位**（换 0.025 细栅格也不创造空间）。
  F 与 In2 双层同堵（FMC_A10 失败子段区域实测自由格 F 28.7%/In2 13%，自由
  带不连通）。
- **ripup 失效数据**：干道网重布必败（FMC_NBL1 37 项、SDMMC1_D1 35 项、
  3V3 228 项铜的全网重布在同样饱和的干道里无路），日志 s4-dryrun-full*.log
  反复出现"重布失败，回滚内存继续"。ripup 对引脚场局部逃逸有效（合成板
  实证），对干道级空间重分配无效——这正是 PathFinder 全局协商的职责域。

## 4. 实战记录（全部串行，快照→L1 终判→SexprWriter→批 CLI 复核）

| 轮 | 靶单 | 结果 |
|---|---|---|
| r1 | 8×3V3 短跳 | **落板 8，零新增 error，unconnected 65→57** |
| r2 | SW_NODE 先行 + 8×3V3 | SW_NODE 经 5V-ripup；CLI 复核抓 9 新增（clearance+shorting）→ 整批回滚 ✓ |
| r3 | 同 r2（修 added_prims 间距 bug 后） | clearance 新增清零；仍余 2 shorting（U3 pad7[5V] vs SW_NODE 孔，pos 相距 2.77mm——L1 未建模的信号铺铜重灌语义）→ 回滚 |
| final | r1 靶单重放 | **落板 8，零新增 error**（终局态） |

- **r2/r3 的定性结论**：5V-ripup+全网重布链路触及 L1 的校准外区域（B1 探针
  电池没覆盖"信号铺铜 vs 新孔的重灌"语义，CLI 两次抓到 L1 放行的违规——
  提交纪律按设计兜住了，宁误杀不放行）。SW_NODE 移出自动提交集，待 B1 增补
  探针（信号 zone 重灌口径）后再战。
- 最终板态 = 战前 + 8 条 3V3 分支（0.2 宽 + 0.6/0.3 过孔，uuid 内容派生）。
- 终局 DRC 存证：`<工程>/pcbagent-out/b3/final-drc.json`（10 violations 全为
  战前既有 copper_edge_clearance，与 baseline-drc.json 逐键一致）。

## 5. 残网施工包（GUI 会话按图施工的输入）

```
<工程>/pcbagent-out/b3/
  opens-refreshed.csv      断点清单刷新（DRC unconnected 口径，53 信号 + 4 GND，
                           与原 opens.csv 同列结构，suggested_layer 尽量继承）
  residual-corridors.svg   残网走廊总图（46/53 有 L2 走廊实线，其余虚线参考；
                           红 x = 封堵归因铜位 36 处）
  residual-report.md       战果 + 残网分布 + 三类阻塞原因口径 + 施工输入索引
  baseline-drc.json / final-drc.json / snapshot-*.kicad_pcb / s4-*.log
```

## 6. 门状态与偏离清单

- **B3 实战门：FAILED（8/61 ≪ ≥40/61）**；零新增 error ✓、残网走廊图+阻塞
  原因 ✓、刷新 opens.csv ✓、机时 ≈35min（预算内）——唯一未达标项是收网数。
- 按 HANDOFF §2 BLOCKED 语义停笔：门在调参后（分段实现、净空中继、margin
  复测、直连对照）仍不过，且 dry-run 上界数据表明**继续调参无增益空间**。
- 偏离 1：战斗靶单取 dry-run 可收集合（8 条）而非全 61 盲跑——上界已由
  只读 dry-run 科学确立，全量盲跑只产生相同失败（记录于 §3）。
- 偏离 2：SW_NODE 移出自动提交集（r2/r3 证据，见 §4）。
- 偏离 3：KipyWriter 仍未联测（全程 SexprWriter，无头口径已两轮实战验证）。
- 给裁决方的选项（供参考，非本会话决定）：
  a. 接受"工具 + 残网施工包"现状，B3 门改口径（如"零新增 + 上界尽收"），
     进 S5/B4 桥（L4 与门数无依赖）；
  b. 把 52 条残网交给 GUI 会话人工收（施工包已备好）；
  c. 扩 SPEC：允许工具做干道级拆迁规划（动既有铜的全局重分配，属 L2/L3
     之外的提级变更，须规划方修订 SPEC 后另开会话）。
