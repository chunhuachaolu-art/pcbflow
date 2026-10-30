# CANVAS-API-CONTRACT（canvas-edit-v2 · 四画板工具链接口合同）

> 波0 合同锁定件。冻结时点=落盘时点（DISPATCH-LOG 已登记开工节）。本件是波1/波2 全部车道的
> 唯一接口依据；车道间文件集互不相交，跨车道依赖只许经由本合同钉死的签名缝。修订=编排体
> 显式发修订节+DISPATCH-LOG 登记，车道不得私改。

## 0. 依赖锚（全部只读 import，零回写）

- 画板态序列化: `v5.canonical` — `canonical_json(obj)->bytes`、`canonical_sha256(obj)->str`、`sha256_bytes(data)->str`。
- 验证核（同源绑定，禁止平行实现）: `v5.drc` — `Copper(net_id, cid, layer, polyline=|pad=|band=)`、
  `Violation/DRCReport(as_dict/clean)`、`check_clearance(coppers, min_clearance_mm, same_net_exempt)`、
  `check_edge_clearance(coppers, workspace, margin)`、`normalize_holes(board_holes)`、
  `hole_via_blocked/hole_track_blocked`、`hole_inherent_pairs(holes_norm, margin)`、
  `check_hole_keepout`、`check_all(coppers, hard_rules, sensitive_rects, keepout_rects, ...)`。
- 导出器: `v5.kicad_export` — `kicad_pcb_bytes(board, routes)`、`project_kicad_pro_bytes(board, routes)`、
  `write_kicad_pcb(board, routes, path)`、`via_model_params(board)`。
- 板加载: `v5.board` — `load_board_file(path)`（wrap 件：取 `["board"]` 体；`provenance.board_sha256`
  即板锚）、`compute_board_sha256(board)`。
- 板源（只读）: `out/v5-p5/boards/<board>/board.json`（D8 现役 wrap 件）。
- kicad-cli: `F:/kicad/bin/kicad-cli.exe`，只跑 staging 副本（§4 路径约定）。
- **禁止** import `canvas_pilot.*`（M1 域隔离；本包一切实现自有，形态可同构）。

## 1. 模块边界与签名缝

### canvas/state.py（Lane-K1）
画板可变态单源。`CanvasState(board, board_path, board_sha256, lat, anchors)`：
- 构造期冻结引用: `board`（board.json 体）、`board_path`、`board_sha256`、`lat`（格点阵）、
  `anchors`（partition_id -> [[i,j],[i,j]] 端点锚，snap 期 fail-closed 冲突检测）。
- 图元清单（shape_id 稳定寻址）:
  - `segs`: `{shape_id="seg:<net>:<seq>", net_id, partition_id, layer, grid:[[i,j],..], width_class}`；
  - `vias`: `{shape_id="via:<net>:<i>_<j>", net_id, grid:[i,j]}`；
  - `widths`: 网级宽度档 `{net_id -> width_class}`（无 shape_id，ripup 不寻址）；
  - `placements`: 分区放置覆盖 `{partition_id -> {"move":[i,j]|None, "rotate":0|1|2|3, "flip":bool}}`
    （只记覆盖，合法化检查归 placecheck；无覆盖=原位）；
  - `tunings`: 调参段 `{shape_id="tun:<net>:<group>:<seq>", net_id, group_id, kind, grid, params}`。
- 连通账本: `connectivity{net_id->bool}` + `chain_detail{}`——每次变更后重算；纪律=段衔接点
  必须有 via 在场（画板统一纪律），首段首点/末段末点=分区端点锚（placement 有覆盖时按
  覆盖后锚位）。
- 序列化: `state_facts(st)` dict（canonical_json 可直落）+ `state_sha256(st)`（链式台账锚）。
- 确定性: 同输入同动作序列 → 字节等（copy-on-write，禁止 dict 迭代序渗入输出）。

### canvas/protocol.py（Lane-K1）
canvas-edit-v2 fail-closed ingest。`parse_batch(text, expected_round) -> [action dicts]`；
`BatchReject(code, detail)` 整批拒收；语义层逐动作拒收（码进拒收直方图，批内后续动作继续）。
两层原因码词表**追加式**（新码只增不改义）；v1 码语义原样保留（E_PARSE/E_NOT_OBJECT/
E_ACTIONS_NOT_LIST/E_ACTION_NOT_OBJECT/E_UNKNOWN_ACTION/E_MISSING_KEY/E_EXTRA_KEY/
E_NON_INTEGER_GRID/E_FLOAT_COORD/E_GRID_OUT_OF_BOUNDS/E_UNKNOWN_NET/E_UNKNOWN_LAYER/
E_WAYPOINTS_TOO_FEW/E_NO_SUBMIT/E_TRAILING_ACTION/E_ROUND_MISMATCH/E_RIPUP_TARGET/
V_CLEARANCE/V_EDGE/V_HOLE_TRACK/V_HOLE_VIA/V_ENDPT_NOT_ATTACHED/V_VIA_OFF_PATH/
V_RIPUP_UNKNOWN/V_DUPLICATE_VIA/V_SELF_SNAG），v2 追加码见 §2 各动作。

### canvas/validate.py（Lane-K1）
v5.drc 绑定验证器，两入口：
- `validate_edit(st, action)` -> `(accepted: bool, code|None, detail)`: 逐编辑局部检查
  （受影响铜对走 check_clearance/check_edge_clearance/hole_via_blocked/hole_track_blocked 同源调用）。
- `validate_full(st)` -> `DRCReport`: 全态检查（铜全集调 v5.drc.check_all 同源）。
布间/放置合法性**不在本件**（M4 车道 placecheck，verdict 显式标注"新 validator，非 v5.drc 移植"）。

### canvas/instantiate.py（Lane-K1）
格点态 → mm 几何实例化（路由无搜索，放置合法化不在此）：
- `instantiate(st)` -> `{coppers: [v5.drc.Copper], routes: [kicad 导出行], holes_norm, anchors_mm}`：
  seg→折线 mm（贴制造格点）、via→孔 mm、placement 覆盖→分区 pad 场 mm、tuning→参数化几何。
- `manhattan(from_grid, to_grid)` 直连折线（L 形，拐点在格点上；无搜索无绕障）。

### canvas/pack.py（Lane-K2）
席位载体（E0 先例形态）：
- `pack_view(st)` -> `{svg: str, facts_json: str, view_spec: dict}`: SVG 内每图元带
  `data-shape-id/data-net/data-layer/data-grid/data-kind` 机器事实；facts_json=state_facts
  完整投影；view_spec 含层可见性/视窗。
- `write_pack(pack, dir_path)` 落盘三件（view.svg/view-facts.json/view-spec.json）。

### canvas/loop.py（Lane-K2）
轮循环 runner：
- `RunLoop(st, ledger_path, seat_fn, parser=None, batch_mode=False)`：
  `seat_fn(round, pack) -> actions_text`（席位派发桩，编排体注入真席位；桩=
  确定性回放器供测试）。默认 `batch_mode=False` 保持逐动作
  `st.apply_action(action)` 语义；`batch_mode=True` 要求
  `st.apply_batch(actions, round_no=None)`，每轮一次整批调用，缺失即
  fail-closed。
- 链式哈希台账 `ledger.jsonl`：旧行每行
  `{round, prev_sha256, state_sha256, actions_sha256, accepted/rejected 摘要,
  edit_list, verdict}`，首行 prev=64×"0"。批模式行另增 `batch`：确定性重排后的
  完整动作列（含 rejected/submit）；`accepted`/`rejected` 按原输入 index 摘要，
  `edit_list` 为接受动作副本。批拒收行的 `batch=[]`。
- `replay(ledger_path, board_path)` -> CanvasState：无 `batch` 的旧行按
  `edit_list` 逐动作重放；有 `batch` 的行整批调用一次 `st.apply_batch`，均在轮末
  复算并校验 `state_sha256`。批摘要不作为 replay 的额外比对源。

### canvas/export.py（Lane-K2）
`export_kicad(st, out_dir)`：调 `instantiate(st)` 取 routes/board → `v5.kicad_export.write_kicad_pcb`
+ `project_kicad_pro_bytes` 落盘 `.kicad_pcb/.kicad_pro`（落 staging 副本目录，绝不写 boards/）。

### canvas/authority.py（Lane-K2）
`kicad_cli_aggregate(export_dir, runs=5, max_rounds=3)`：P5-UP3-aggregate-v1 口径
（每轮 5 跑、至多 3 轮、出现全等轮即停取该轮、无全等轮=union-max+披露）；返回
`{drc_clean: bool, unconnected: int, aggregate_report}`。连通复核=聚合 DRC unconnected 计数。

### canvas/runners/*（波2 四车道）
- `m2.py`: `run_m2(st, budget)` 粗布（多层布线/netclass 宽度强制/批量 ripup/过孔成本事实扩展）。
- `m3.py`: `run_m3(st, budget)` 修整（亚类宽归一/残段清理/冗余过孔消减/宽度间隙规整；
  每接受批次连通 100% 不变量）。
- `m4.py`: `run_m4(st, budget)` 布局（move/rotate/flip 驱动+基线臂对照 harness）。
- `m5.py`: `run_m5(st, budget)` 高速（长度组 tuning 驱动）。
- 各 runner 只经 state/protocol/instantiate/validate 缝操作画板，不私触 v5 导出器。

### canvas/placecheck.py + canvas/referee.py + canvas/tuning.py（Lane-M4/M5 伴件）
- `placecheck.py`: 布间 validator+自有夹具（verdict 标注"新 validator，非 v5.drc 移植"）。
- `referee.py`: 确定性粗可布性评分（逃逸/走廊/容量余量；具体式冻结于 M4 激活跑 prereg）。
- `tuning.py`: 宽度档表按叠层计算+accordion/绕行参数化实例化+长度组残差测量（公式来源
  披露、不冒称全阻抗 authority）。

## 2. canvas-edit-v2 动作枚举（钉死；逐动作必含 "action" 键）

| 动作 | 必含键 | 允许键全集 | 语义层码（v2 追加） |
|---|---|---|---|
| route | net_id, waypoints, layer | action,net_id,waypoints,layer | v1 码照用 |
| via | net_id, grid | action,net_id,grid | v1 码照用 |
| ripup | （net_id 或 shape_id 二选一） | action,net_id,shape_id | v1 码照用 |
| width_class | net_id, class | action,net_id,class | V_UNKNOWN_WIDTH_CLASS（class 不在板 netclass 表） |
| move | partition_id, target | action,partition_id,target | V_PLACEMENT_COLLISION（placecheck 判定） |
| rotate | partition_id, turns | action,partition_id,turns | V_PLACEMENT_COLLISION |
| flip | partition_id | action,partition_id | V_PLACEMENT_COLLISION |
| tuning | net_id, group_id, kind, params | action,net_id,group_id,kind,params | V_TUNING_KIND（kind 不在枚举）、V_TUNING_PARAMS（参数越界/非数） |
| submit | — | action | — |

- `width_class.class`: 板 stackup/netclass 词表内的字符串（缺省表=板 hard_rules 推导，词表
  冻结于激活跑 prereg）。`move.target=[i,j]` 格点。`rotate.turns∈{1,2,3}`（顺时针 90°×turns）。
- `tuning.kind∈{"accordion","detour"}`；`params` 为平铺数值对象（键集随 kind 冻结于 prereg）。
- 格点纪律照 v1：一切坐标整数格点，毫米/浮点/字符串坐标渗透=整批拒收（E_FLOAT_COORD 等）。

## 3. 席位盲包禁项清单（席位盲化纪律）

席位包**只许**含: ①pack_view 产物（SVG+facts_json+view_spec）②动作协议词表与语义说明
（含全部原因码）③轮次指令（round 号+stop 语义文本）。席位包**禁含**:
- 基线几何（引擎 execute.json/任何引擎解内容与路径）；
- 门值（任何判据阈值数值、达标线、预算余量、轮数上限的"还剩多少"）;
- oracle（参考解/最优解/其它席位动作与回执）。
判读只在编排侧；回执以落盘为准（会话 JSON 落盘前 json.loads 验证）；独立检查席在每次激活跑终态。

## 4. 产物路径约定

```
out/canvas-toolchain/
  snapshots/            四树快照（开工/收工）
  wave1/ wave2/         构建波: ledger.jsonl、final/、VERDICT.md、偏差台账 D-CT-###
  act-m2..act-m5/       激活跑: PREREG（先冻结）、ledger.jsonl、rounds/、final/、VERDICT.md
  staging/<run-id>/     kicad-cli 运行域（.kicad_prl 只落这里；绝不触 boards/、datasets/）
```
- 台账 ledger.jsonl 一律 canonical_json 行 + 链式哈希；VERDICT 含主审复核路径位。
- 新代码只进 `canvas/`（含 runners）；新测试只进 `canvas/tests/`（不进 tests/ 根）。

## 5. fan-out 冒烟（每车道开工第一动作）

从 route-v5 根: `python -c "import v5.canonical, v5.drc, v5.kicad_export, v5.board; print('contract-anchor-ok')"`
+ 车道自身首批文件落盘后 `python -c "import canvas.<本车道模块>; print('lane-import-ok')"`。
冒烟不过=车道停工报编排体（P1 教训: 合同缝在集成前抓）。

## 修订节 REV-1（2026-09-25 编排体，波1 收口时点）

- **D-CT-001 措辞勘误（§0 依赖锚）**: 原文"load_board_file(path)（wrap 件：取 ["board"] 体）"
  有误——v5.board.load_board_file 对 wrap 顶层做 schema 校验会 fail（其适裸 .board.v1.json）。
  正确口径（K1/K2 两车道独立实测+集成冒烟复证）: `json.load(path)` → 取 `raw["board"]` 体 →
  `v5.board.load_board(board)`（schema+跨字段+哈希链全校验）；板锚=board 体
  `provenance.board_sha256`。单源实现=canvas/integration.load_wrapped_board。
- **D-CT-002 词表两裁决（§1 protocol）**: ①v1 码 E_WAYPOINTS_NOT_LIST 未入合同词表——维持
  K1 就近归码 E_NON_INTEGER_GRID（detail 全文说明），不新增码；②rotate.turns∉{1,2,3} 维持
  归码 E_GRID_OUT_OF_BOUNDS（值域越界语义）。均词表追加式纪律下的保守处理，激活跑 prereg
  转录词表时按本节口径。
- **集成缝补充（§1 loop/export）**: loop↔protocol apply 缝经 canvas/integration.LoopStateProxy
  （legacy 单动作批退化；M2R3 批模式直接接一致性批入口，语义披露见该模块）；
  state_call 缝（state_facts/state_sha256）与属性名 lat↔lattice 桥接同在 integration；
  export↔instantiate 真缝经延迟加载自动生效（K2 实现），集成冒烟已验证真件 routes
  与 v5.kicad_export 兼容。

## 修订节 REV-2（2026-09-25 编排体，波2 接线收口时点）

- **词表波2 追加三码（§1 protocol 词表，D-CT-005）**: E_UNKNOWN_PARTITION（partition_id
  不在 board.partitions）、V_PLACEMENT_EDGE（放置后分区出板框）、V_KEEPOUT（候选铜落入
  R6 禁布区——编辑侧前置，全态兜底仍=validate_full 的 rule=R6）。追加式只增不改义。
- **placecheck 接线（lane-m4 §5 契约收口）**: validate_edit 的 move/rotate/flip 分支改调
  canvas.placecheck.check_placement（检查序=分区存在→格点/值域→板框→布间）；相对→绝对
  折算单源=canvas/protocol.absolute_candidate（rotate=(cur+turns)%4、flip=取反、move=绝对
  target）；apply 侧（apply_batch）落 placecheck.merge_candidate 完整覆盖→st.set_placement。
  原占位拒收 placecheck-not-built 退役。validate_full 不并入放置合法性（两层 verdict
  口径不同源；全场放置检查独立调 placecheck.check_all_placements）。
- **R6 前置拒收（lane-m5 §6 遗留收口，D-CT-006）**: validate_edit 的 tuning 分支新增
  V_KEEPOUT 前置拒收，复用 canvas.tuning.r6_violations 同源三件套（zone_rects+
  drc.check_keepout+instantiate.tuning_copper），零平行实现；validate_full 兜底面保留。
- **真板包络口径维持（lane-m4 §3.1 裁决，D-CT-007）**: 分区 pad 场外接矩形包络语义维持
  合同字面口径（per-pad 细化触"铜面平行实现"红线不采用）；真板 2-pad 大跨距器件的
  move/rotate/flip 结构性拒收为如实读数，M4 激活跑人口以合成板为主。

## 修订节 REV-3（2026-09-25 M2R3 批缝接线）

- `LoopStateProxy.apply_batch(actions, round_no=None)` 直接接入
  `canvas.protocol.apply_consistent_batch`；`apply_action` 保持 legacy 单动作批退化。
- `RunLoop(..., batch_mode=False)` 默认字段与逐动作 apply/旧台账形态不变；显式
  `batch_mode=True` 时每轮只调用一次 `st.apply_batch`，批模式行追加 `batch`（重排后的
  完整动作列，含拒收动作与 `submit`），摘要 index 保留原输入位置，批拒收记 `batch=[]`。
- replay 按行是否存在 `batch` 分流：旧行逐动作重放 `edit_list`；批模式行整批调用一次，
  只硬校验链和轮末 `state_sha256`，不把 `accepted/rejected` 当作第二重执行输入。
