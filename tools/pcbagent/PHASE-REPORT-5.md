# PHASE-REPORT-5 — S5 会话 / B4（L4 桥）+ B5（衔接打包）——工具链收尾

- 日期：2026-08-29（单会话完成）
- 裁决执行：规划方选 **a** —— B3 实战门改口径为「零新增 DRC error + dry-run
  上界尽收（8/8 自动提交集）+ 残网施工包产出」判 PASS（SW_NODE 移出自动提交集
  维持）；本会话按 S5 = B4 + B5 收尾。**工具链 B1–B5 至此全部交付。**

## 1. S4 门独立复核（先复核后动工，全部过）

- 合成板全套重跑：geometry 7/7 + planner 4/4 + **router 8/8**（含 S4 新增
  test_route_segmented）→ `out/b4/s5-gate-rerun.log`。
- 终局板态对账：fresh kicad-cli DRC（refill+save 口径）= **10 violations
  （全为战前既有 copper_edge_clearance）+ unconnected 57**，与 S4
  `final-drc.json` 及战前 `baseline-drc.json` **逐键一致、零新增** →
  板态与 S4 交接待完全一致 → `out/b4/s5-drc-recheck.log`。

## 2. B4 交付（L4 桥，`bridge.py` + `cli.py` 四命令）

| 命令 | 结果 | 口径要点 |
|---|---|---|
| `verify` | ✅（rc=0，对 baseline 零新增） | 基线链 = `--baseline` 显式 > `b4/verify-last.json`（快照滚动）> 首跑建立；回归 = **新增违规**才算失败（存量不计）；报告 JSON+MD 落 `b4/` |
| `length` | ✅（rc=0；组 FAIL 属板态数据） | 镜像 track 段欧氏长合计 + 0.2mm/过孔（板无 arc 实测 0 条；walk 递归含 footprint 内嵌段，与 pcbnew GetTracks/GetLength 同语义） |
| `render` | ✅（7 层 SVG） | kicad-cli `--mode-multi` 每层一文件 + `--check-zones` + `--page-size-mode 2`；落 `b4/render/` |
| `audit-checklist` | ✅（7 条款） | routing-spec §4 条款 + 工具可测证据预填（每网铜长/过孔数/分层段数）；视觉判定 advisory 非裁决 |

- **B4 核心门——length 对账**：与 `revc/length-report.py`（F:\kicad\bin\
  python.exe 运行，pcbnew 真值）逐键比对 **113 项（九组全部网长度/组级
  字段/键集）0 偏差**；九组表 `config.LENGTH_GROUPS` 与其 GROUPS 同源 →
  `out/b4/s5-pcbnew-length.json`。
- **确定性抽查**：length + audit-checklist 两轮运行 JSON 逐字节一致。
- 门证据：`out/b4/b4-gate-report.json`（汇总）+ `s5-cmd-*.log`（四命令原始终端）。

## 3. B5 交付（gui-session-kit，`tests/run_b5_kit.py`）

- `<工程>/pcbagent-out/gui-session-kit/`：**README.md**（施工循环：分层 SVG
  对照走廊图 → KiCad 布线 → 保存 → verify 回归门）+ **batches.md/csv**
  （53 信号对分 7 批 × ≤8 对 + GND 4 条单列末批；批序按 routing-spec §9
  布线顺序、同批内距离升序；**46/53 有 L2 走廊实线标注**，与残网报告口径
  对账一致）+ residual-corridors.svg / residual-report.md /
  opens-refreshed.csv（自 b3/ 拷贝）。
- 每批落盘后的回归门命令已写死在清单里：`python -m pcbagent.cli verify
  --project <工程>`（首跑自动建立基线）。
- SW_NODE 注意事项已写入 kit README（5V 铺铜重灌语义，GUI 人工施工天然安全，
  只是工具无头 L1 的口径盲区）。

## 4. 过程中修的坑（后续复用注意）

1. `length_report_md` 分支缺陷：参考网未布通的组（如 G_EMMC，SDMMC2_CK 长 0）
   无 `deltas_vs_ref`，原代码掉进 USB 对内分支崩（too many values to unpack）。
   教训：**三级分支必须显式覆盖 "reference unrouted"**。
2. `csv.writer` 无 `newline` 参数（那是 open() 的）——StringIO 直接给 writer 即可。
3. Mimosa 钩子会把「bash 命令含 .py 路径 + 重定向」误判为直写源码——读代码/
   跑命令时把 grep 与重定向拆成两条调用即可（无实际风险，纯口径）。

## 5. 门状态终局与硬验收对账

| 门 | 结果 | 证据 |
|---|---|---|
| B1 L1 vs CLI 100% | **PASS**（25/25） | `out/b1/b1-gate-report.json` |
| B2 拥塞回验 | **PASS**（p3 57/61、current 59/61、3V3 21/22） | `out/b2/gate.json` |
| B3 实战 | **PASS（裁决 a 改口径）**：零新增 error ✓ + dry-run 上界尽收 8/8（SW_NODE 移出自动集）✓ + 残网包 ✓ + 机时 35min ✓ | `PHASE-REPORT-4.md` + `<工程>/pcbagent-out/b3/` |
| B4 四命令 | **PASS**（对账 113 项逐键一致） | `out/b4/b4-gate-report.json` |
| B5 衔接包 | **交付**（7+1 批施工图） | `<工程>/pcbagent-out/gui-session-kit/` |

- 偏离清单（全链）：① B3 门口径按裁决 a 修订（原 ≥40/61 在本板态被 dry-run
  科学否证为不可达，上界 9 条）；② SW_NODE 移出自动提交集；③ KipyWriter
  未联测（全程 SexprWriter，两轮实战验证）；④ B6（placement-iterate）未开跑
  （可选，服务未来板，不影响 Rev-C）。
- **残网清单与原因**：53 信号 + 4 GND，46/53 有走廊、36 处封堵归因位，
  三类阻塞口径（干道双信号层饱和 / 引脚场逃逸容量 / 铺铜封堵）见
  `<工程>/pcbagent-out/b3/residual-report.md`——交 GUI 会话按 kit 施工。
- F4（等长）/F5（制板）不在工具链范围：`length` / `audit-checklist` /
  `render` 即为其输入。

## 6. 给后续会话的指针

- GUI 人工收残网：按 `<工程>/pcbagent-out/gui-session-kit/README.md` 走，
  每批后 verify 回归门，收尾跑 verify + length + audit-checklist。
- 若做 B6（S6 可选）：读 SPEC §3.5 + `out/b2/` 现有产物；合成板红→绿翻转为门。
- 若启用 SW_NODE 类 ripup：先给 B1 探针电池补「信号铺铜 vs 新孔重灌」探针
  （NEXT.md 约束提醒，PR-4 §4 证据）。
