# PHASE-REPORT-1 — S1 会话 / B1 阶段（L0 板镜像 + L1 合法性 API）

- 日期：2026-08-28（单会话完成）
- 结论：**B1 门 PASS**。`tests/run_b1_gate.py` 最终轮：**25 探针与 kicad-cli DRC 判定
  25/25（100%）一致**，其中边界探针 13 个（≥5 达标）；L1 单查询 **p95=0.95ms、
  max=1.35ms（<10ms 达标）**。门报告：`tools/pcbagent/out/b1/b1-gate-report.json/.md`
  （每探针注板副本与 DRC JSON 同目录存证）。

## 1. 交付物

```
tools/pcbagent/
  pcbagent/config.py     全部阈值/开关（含 B1 校准出的 CLI 行为常量）
  pcbagent/sexpr.py      只读 s-expr 解析器
  pcbagent/geometry.py   精确几何内核（prim = core⊕r；绕数判 zone 实体）
  pcbagent/mirror.py     L0 BoardMirror：解析/桶索引/rasterize/connectivity/opens/sync
  pcbagent/legality.py   L1 Legality：seg_legal / via_legal / pad_legal
  pcbagent/bridge.py     kicad-cli DRC 封装 + diff（L4 verify 的执行核心，S5 扩命令面）
  pcbagent/cli.py        mirror-info / verify（SPEC §0 其余命令按阶段补）
  tests/test_geometry.py            几何内核 7 项合成单测（全过）
  tests/pcbnew_export_ref.py        SWIG 参考导出（F:\kicad\bin\python.exe 跑）
  tests/check_mirror_vs_pcbnew.py   镜像 vs pcbnew 逐项比对
  tests/run_b1_gate.py              B1 门：探针电池 + CLI 对决 + 计时
  README.md              用法与实现口径
  out/b1/                门报告 + 25 个探针注板副本 + DRC JSON + 校准记录
  out/checks/pcbnew-ref.json  SWIG 参考几何
```

## 2. 门数字（最终轮，`out/b1/run4-final.log`）

| 项 | 要求 | 实测 |
|---|---|---|
| 探针数 | ≥20 | 25（弃 1：via-on-npth，J5 区过密无法净位重定位，见 §5） |
| 边界探针 | ≥5 | 13 |
| L1 vs kicad-cli | 100% 一致 | **25/25** |
| 单查询 | <10ms | p50 0.29ms / p95 0.95ms / max 1.35ms |
| 基线 DRC | error=10（全既有 copper_edge） | 与 f3 真值一致 |

L0 侧验证（门外的加固证据）：
- **镜像 vs pcbnew(SWIG) 交叉验证 100%**：553 焊盘（位置/尺寸/旋转/钻孔/层集逐项）、
  2170 走线、353 过孔，零偏差（`out/checks/`，比对容差 1e-6mm/1e-3°）。
- **opens() 对账**：镜像连通性算出未连 65 = 信号 61 + GND 4，与 drc-f3-round1-final.json
  真值一致；3V3=22 亦吻合。

## 3. 探针电池构成（25 个，F/In2 双层）

预期合法 12 / 非法 13；每探针独立注板（独占网 ZPROBE 的段/过孔）→ 副本工程目录跑
kicad-cli（`--severity-error --refill-zones --save-board`）→ 位置归因（见 §4.3）。
锚点走线/焊盘/走廊由镜像数据确定性排序选取，探针位经"重定位"保证构造目标即绑定约束。

- 走线组：平行 0.3 / 边界 0.201 / 边界 0.199；垂直横穿；端点贴边
- 走廊组：居中合法 / 贴边 0.199
- 焊盘组（roundrect）：重叠短路 / 边界 0.201 / 0.199
- PTH 铜环：边界 0.201 / 0.199
- NPTH 孔：0.2505 / 0.201（0.25 口径经圆形多边形化余量校准，见 §4.2）
- 线宽：0.1495（违规）/ 0.1501（合法）——0.15 边界
- 过孔：贴走线 0.601 / 0.19；盘径 0.44；钻径 0.29；空白区；平面重灌校准
- 角度：净区 30° 校准探针（现判合法，见 §4.4）
- In2 层：平行合法 / 横穿违规（层覆盖）

## 4. 校准出的 CLI 真实口径（本轮最大产出，已固化进 config.py / legality.py）

1. **圆形铜多边形化**：CLI 对过孔盘与钻孔按内接多边形（max_error≈0.005mm）测间距，
   线段/焊盘（含圆焊盘）用精确形状。实证：via盘-走线 0.199mm 判**合法**（<0.2！）、
   NPTH 孔-铜 0.2495 判**合法**、0.201 判**违规**、圆焊盘-走线 0.199 判**违规**。
   → L1 对每个圆形参与者加 `CIRCLE_POLY_SAGITTA=0.005` 等效余量；模型解释全部边界观测。
2. **NPTH 孔-铜同属 hole_clearance（error，要求 0.25）**，与金属化孔同口径；
   过孔盘落入 NPTH 孔内 = hole_clearance 违规（铜-孔），不是 hole_to_hole。
3. **track_angle 不强制**：净区 30° 走线 CLI 零违规（`out/b1/calib-angle30/`）。
   `ENFORCE_TRACK_ANGLE_45=False`；L3 仍只用 45° 路径（工艺纪律）。
4. **探针铜会被并入所触网簇**：接触既有铜后 CLI 描述里网名变成既有网的
   （实测出现 [GPIO_PE6]/[HSE_OUT]/[GND]）→ 归因必须按 items.pos 落点，网名仅辅助。
   【给 B3 的重要启示：提交纪律里 CLI 复核的"新增违规"判定也要按位置/uuid 归因，
   不能只按网名。】
5. **--refill-zones 口径**：新铜旁的 zone 填充会重灌让位（263 个既有 F..In2 过孔
   穿越 In1 平面零违规即系统级证据）→ 候选铜/孔对 zone 不作静态否决，但过孔须满足
   "盘缘让位半径 ≥ 孔半径 + 0.25"（`REFILL_ADAPTS_ZONE=True` + via_legal 内校验）。

## 5. 偏离清单与给下家的注意事项

- **抽取源缺失**：HANDOFF §1 表列的 `exec/p5_ground.py`、`exec/p4d_finish.py` 已不存在
  （exec 目录被清理）。按 SPEC §1-2 重写 + 失败审计 M2/M3 四项修复记录（单位/轴对齐/
  seg-rect 中段/边界 EPS）+ gui_lib.py 几何原语替代，并以单测回归固化。不构成阻塞。
- **KiCad 9+ pad 角度语义**：板文件里 pad 的 (at x y rot) 是**绝对角**（含封装旋转），
  位置偏移才按封装旋转——pcbnew 交叉验证实证（U2/R5 双例）。写 L3 kipy 落板代码时注意。
- **多板同名防呆**：Rev-C 工程目录混有历史评估板 `expA-eval.kicad_pcb/.pro/.prl`
  （listdir 顺序曾使 SWIG 导出器加载错板）。mirror/bridge/run_b1_gate 均已改为
  "与 .kicad_pro 同名的 .kicad_pcb" 选择 + 只拷主工程三件套。S2/S3 复用此约定。
- **via-on-npth 探针被弃**：J5 两个 NPTH 周边被槽孔/焊盘封死，重定位找不到净位；
  该场景已由 npth-201/2505 与 _check_copper_vs_holes 覆盖。
- **性能**：connectivity 的 zone 判触对填充边做了惰性桶索引（`ZoneFill.edges_near`），
  opens 全板 0.8s；L1 查询勿把 zone/多环实体放进桶索引外扫（会退化到全量遍历）。
- **本轮门跑次序**：run1 19/26 → 修位置归因/NPTH 口径/角度规则 → run4-final 25/25。
  中间轮日志（run2/run3.log）与校准探针目录保留在 out/b1/ 供审计。
- L1 返回的 margin 已含 §4.1 的等效余量（对圆形参与者），L3 用 margin>0 作终判即可。

## 6. 下一步

S2 / B2：L2 拥塞规划器（PathFinder + 四产物 + gate.json），按 SPEC §3；
在 snapshots/p3-placement-gates-pass 与当前板两点回验（61 断点走廊命中 ≥70%、
3V3 22 条逃逸审计命中 ≥15）。S2 开工前先重跑 S1 门（`python tests/run_b1_gate.py
--project …`）复核 PASS。
