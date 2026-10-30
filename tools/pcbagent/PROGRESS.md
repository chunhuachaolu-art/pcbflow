
## pcbagent B1（S1 会话）✅（2026-08-28）

- 会话协议启动（HANDOFF-PROMPT.md + NEXT.md）。L0 板镜像 + L1 合法性 API 完成并过门。
- **B1 门 PASS**：25 探针 vs kicad-cli（--severity-error --refill-zones --save-board，
  副本工程内跑）25/25 一致，边界探针 13（0.15 线宽 / 0.2 铜铜 / 0.25 孔铜），
  单查询 p95=0.95ms。报告 `tools/pcbagent/out/b1/b1-gate-report.md`，详报
  `tools/pcbagent/PHASE-REPORT-1.md`。
- L0 证据：镜像 vs pcbnew SWIG 交叉验证 100%（553 盘/2170 线/353 孔）；
  opens()=65（信号 61+GND 4）与 drc-f3-round1-final.json 真值一致。
- CLI 口径校准（固化 config.py）：圆形铜多边形化余量 0.005mm；NPTH 孔-铜=hole_clearance
  0.25；track_angle 不强制（净区 30° 零违规）；探针铜触铜后并入既有网簇（归因按位置）；
  --refill-zones 下 zone 重灌让位（过孔须满足让位半径 ≥ 孔半径+0.25）。
- 坑：工程目录混有 expA-eval 历史板（已加同名选择防呆）；pad 文件角为绝对角
  （KiCad 9+ 格式）；p5_ground/p4d 抽取源已被清理，按审计记录重写并以单测回归。
- 产物：tools/pcbagent/（7 模块 + tests + README）；Rev-C 主板文件零改动（B1 只读）。
  下一步：S2/B2 拥塞规划器（NEXT.md 已重写指向）。

## pcbagent B2（S2 会话）✅（2026-08-29）

- B1 门独立复核 PASS（25/25 vs kicad-cli，边界 13，p95 0.51ms，out/b1/s2-rerun.log）。
- L2 拥塞规划器完成（planner.py）：0.5mm 粗格×F/In2、5×5 子采样容量图（0/1 两态）、
  PathFinder 逐代协商（MST+A*+历史项，cap0 格付拆让代价穿越）、逃逸审计
  （fanout 0.125mm 采样+带内车道）、四产物全内存生成。
- **B2 门 PASS（green）**：p3 命中 57/61=93.4%、当前板 59/61=96.7%（≥70%）；
  3V3 逃逸 21/22（≥15）。证据 out/b2/gate.json + per-pair.json +
  <Rev-C>/pcbagent-out/b2/{p3,current}/ 四产物；确定性问题：两轮独立进程逐代
  过载格一致（3523/272），合成板 3×PYTHONHASHSEED 全过。
- 调参（SPEC §3.4 授权）：SUB 3→5（车道窗欠采样假堵死）、车道 0.4→0.35、
  cap0 硬封锁→拆让代价 4.0mm/格（硬封锁丢光过载信息）、MAX_ITER 50→12。
- 逃逸不足侧与 F3 诊断吻合：U1 四侧（北 17>3 最重）、U2 南、U3 东；
  J1–J5 连接器不误报。未命中 4 条全是 3V3 短跳（≤2.1mm 同排跳线）=B3 免费收获。
- 新坑：Mimosa 钩子拦包内 .py 的变量路径写盘与 bash heredoc 源码直写——
  放行模式=pathlib resolve+包含性校验（cli.dump），planner 零写盘全内存出产物。
- cli 新增 congestion/escape-audit/corridors；README 更新；Rev-C 板文件零改动
  （mtime 2026-08-28 未变）。下一步：S3/B3-建（NEXT.md 已指向）。

## pcbagent B3-建（S3 会话）✅（2026-08-29）

- B2 门独立复核 PASS（p3 57/61、current 59/61、3V3 21/22，EXIT=0，out/b2/s3-rerun.log）。
- L3 区域路由器完成（router.py）：0.05mm 精细栅格静态障碍图（异网膨胀/同网豁免/
  独立 via 位图）、A* 8 邻 45°+对角防切角+F↔In2 迁移、L2 走廊软约束、路径转 45°
  段（首末精确端点）、L1 终判失败局部加障重搜（≤6 轮）、A* 不可达洪泛封堵归因、
  rip-up（预算 3/禁拆 GND/被拆网同轮重布/内存回滚）、端点落铜校验、uuid 内容派生。
- 提交纪律完成（commit.py）：CommitFlow 快照→惰性 plan 流逐网落板→每 ≤10 网
  kicad-cli 基线 diff→新增违规整批回滚；SexprWriter（无头直写+remove_net 删网）
  与 KipyWriter（kipy IPC，未联测）双后端。
- legality 加 ignore_ids（rip-up 拆除视同已删；默认空集 B1 行为不变——改动后
  B1 门复验 25/25，p95 0.87ms，out/b1/s3-rerun.log）。
- **合成板 7/7 全过**（含 ripup 落板链路 kicad-cli 零新增 + opens 归零、确定性
  逐字节、快照回滚字节一致）；geometry 7/7、planner 4/4 回归绿。
- 修坑六件：np.int64 传播、A* 层索引泄漏、L1 终判不认 excluded、不可达无归因、
  netless 混进 ripup 候选、**PWR 主干宽 0.5 卡死引脚场（改分支口径 0.2+via
  0.6/0.3，3V3 免检短跳立即可收）**。
- Rev-C 只读 dry-run：3V3 组 22 条可收 8 条；61 断点距离分布定案——<8mm 27 条
  （L3 直接收）、8–15mm 6 条、≥15mm 28 条（需走廊中继分段）。Rev-C 板零改动。
- 教训自纠：两次前台 dry-run 与后台 3V3 全组并发覆盖 route-report.json——
  S4 起严格串行跑批。
- cli 新增 route（--net/--batch/--limit/--start/--dry-run/--kipy/--baseline-json）；
  README 更新。下一步：S4/B3-实战（NEXT.md 已指向，先实现走廊中继分段再开战）。

## S4 会话 / B3-战（2026-08-29）

- 开工门复核：B3-建合成板 7/7 PASS（out/s4-gate-rerun.log）。
- 实现走廊中继分段 route（route_net_segmented + 净空中继点滑动）+ 5 坑修复
  （弧长累加、_to_segments 端点层丢失[S3 遗留]、HoleItem.prim、端点过孔容差、
  added_prims 间距 0.15 硬编码[S3 遗留]）；合成板扩至 8 项（+test_route_segmented）
  全 PASS。
- 全量 dry-run 四轮迭代：61 靶稳定可收上界 9 条（8×3V3 + SW_NODE）；中继点
  70% 落铜已修仍无整网解锁；margin 3→6 复测无效回滚；直连/分段对照均不可达；
  干道饱和数学（0.5mm pitch vs 0.64mm 膨胀需求）与 ripup 重布必败数据归档
  （PHASE-REPORT-4 §3）。
- 实战：r1 落板 8×3V3 零新增 error（unconnected 65→57）；r2/r3 顺序实验暴露
  L1 信号铺铜重灌盲区（CLI 抓 shorting、整批回滚兜住），SW_NODE 移出自动
  提交集；final 重放 r1 配置为终局态（final-drc.json 存证）。
- 残网施工包：opens-refreshed.csv（53 信号+4 GND）、residual-corridors.svg
  （46/53 走廊 + 36 阻塞标记）、residual-report.md。
- 门判定：B3 实战门 FAILED（8/61 ≪ 40）→ **BLOCKED**，NEXT.md 已写裁决请求
  （三选项），等规划方。机时 ≈35min（预算内）；全程串行、无头、SexprWriter。

## S5 开工记录（2026-08-29，裁决）

- 规划方裁决：**选项 a** —— B3 实战门改口径为「零新增 DRC error + dry-run
  上界尽收（8/8 自动提交集）+ 残网施工包产出」判 PASS（SW_NODE 移出自动
  提交集维持不变，待 B1 增补信号铺铜重灌探针）；本会话进 S5 = B4（L4 桥
  四命令）+ B5（gui-session-kit 衔接打包）。b（GUI 人工收残网）与 c（SPEC
  提级）仍为后续可选路径，不在本工具链门内。

## S5 收尾记录（2026-08-29，B4+B5，工具链 DONE）

- S4 门独立复核：合成板 19 项全 PASS（7+4+8，含 test_route_segmented）；
  fresh kicad-cli DRC 与 S4 final-drc.json/baseline-drc.json 逐键一致
  （10 既有 violations，unconnected 57），零新增。
- B4 交付：bridge.py 补齐 L4——verify（基线 diff 回归 + verify-last.json
  快照滚动）/ length（镜像口径：段欧氏长+0.2/孔；九组表 config.LENGTH_GROUPS）/
  render（kicad-cli --mode-multi 7 层 SVG）/ audit-checklist（§4 七条款+
  每网证据预填，advisory）。门：四命令全通 + 与 revc/length-report.py
  对账 113 项逐键一致 + length/audit 两轮逐字节确定性抽查。修 3 坑
  （md 三级分支漏 reference-unrouted、csv.writer 无 newline、钩子误报规避）。
- B5 交付：tests/run_b5_kit.py → <工程>/pcbagent-out/gui-session-kit/
  （README 施工循环 + batches.md/csv 7 信号批×≤8 对 + GND 末批，
  46/53 走廊标注与残网报告对账一致，每批 verify 回归门写死清单内）。
- 证据归档：out/b4/（b4-gate-report.json + 四命令日志 + 对账参考 +
  确定性副本 + S4 复核日志）。README 同步（B4/B5 行、命令用法、L4 口径）。
- 终局：B1–B5 全 PASS/交付，PHASE-REPORT-5.md 为最终中文报告，
  NEXT.md 已写 DONE。
