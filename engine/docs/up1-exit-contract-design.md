# 升级件① 出口合同升级·设计文档（主审亲做合同件 v1）

状态：设计稿（2026-09-14，用户裁定立项「先做三项升级件再跑 G1 字面零违例」）；实现任务书待④到货后按其落点细化派发。
目标：P5-G1 门「A 层 ≥5 板 SAT 且 kicad-cli 外权威 DRC 零违例」在真实板上**可达且可复现**。
输入事实：P5①试跑 + P5②批量的三归类台账（badgeleds/pmod：config-gap 61-104、contract-artifact 45-87、genuine 恒 0；逐类构成见 out/v5-p5/trial/*.trial.md）。

## 五条合同决定（钉死文本；改动=新决策件）

### D1 焊盘物理铜入模（消 pad-track 短路/clearance 主因）

- board.v1 schema **追加可选键**（老板零感知、零回归）：分区级
  `pad_terminals: [{"endpoint": 0|1, "shape": "circle"|"rect", "size_mm": [d] | [w, h], "layers": "all" | [层id]}]`。
  adapter 从真实 .kicad_pcb 的 pad（绝对坐标/尺寸/层跨）落此键；导出件按它画真实焊盘铜。
- 世界模型语义：pad_terminals 铜=**固定铜**（同 ribbon/fixed 先例），参与 v5.drc 场景
  （R5 间距/R2 短路按铜形算）；本网分区端点落自己焊盘=合法连接，他网焊盘=障碍。
- executor：焊盘铜进占用栅格（半径/半宽外扩），逃逸必须从焊盘边缘出发。
- 验收锚：contract-artifact 里 pad-track 短路类=0。

### D2 过孔入 v5 间距场景（消 via-track 短路/via clearance 全部隐性违例）

- 过孔铜形=圆，radius = drill/2 + annular（默认 drill 0.3 / annular 0.15，文档化常量；
  真实板孔径从 adapter 读，缺省兜底）。transition_vias/return_vias 全部入场景：
  v5.drc 对孔-线/孔-孔/孔-焊盘逐对算 R5；executor A* 对孔脚印收占用。
- 验收锚：kicad via-track shorting 与 via clearance 类=0。

### D3 回流孔与换层孔错位（消 holes_co_located）

- 合同：同网同分区的 return_via 与 transition_via **禁止同栅格点**，最小孔心距
  = 2×孔半径 + R5.min_clearance_mm（executor 逐条强制，negotiation_log 披露错位决策）。
- 验收锚：holes_co_located=0。

### D4 逃逸对称披露（消 track/via_dangling 悬空）

- route 条目折线必须**焊盘心→焊盘心全程覆盖**（含逃逸段）：executor 输出的
  polyline 从 pad_terminals 的焊盘心起画，逃逸段=焊盘心→首布线点的显式折线段；
  过孔必落在折线顶点且双侧线段相连。
- 验收锚：track_dangling=0、via_dangling=0、unconnected_items=0（G1 门字面要求）。

### D5 净类与配置（与②衔接）

- ②负责净类间距换算写板+封装库解析（在途）。①不重复做；①的导出侧改动
  （焊盘铜/过孔铜形）在② landed 之后的 kicad_export.py 上叠加。

## 文件归属与顺序（并行不冲突）

| 序 | 件 | 文件 |
|---|---|---|
| 0 | ④（在跑） | executor 逃逸策略/A* 能力/零长缝（route_check 仅此一缝） |
| 1 | ②（在跑） | kicad_export.py 净类+封装库 |
| 2 | ①实现（④②到货后派） | board schema+adapter（D1）/v5.drc+route_check 场景（D1-D3）/executor 孔错位+逃逸全程折线（D2-D4）/kicad_export 叠加（D5） |

## 验收（①完成定义）

1. 全仓回归绿 + V2 黄金四值不动 + 双跑字节等（全程）；
2. D 层夹具：焊盘障碍板/孔错位板/悬空板三件新对抗板，逐项 contract-artifact→0；
3. 真实验证：升级后 A 层板**重转重冻**（ledger 登记）→ badgeleds+pmod 全链重跑
   → kicad-cli（③口径 P5-UP3-aggregate-v1）逐类违例=0 或仅剩已披露非真类；
   genuine 恒 0 维持；
4. G1 字面零违例门按新世界模型重跑——达成为①完成的唯一验收口径（用户裁定）。

## 风险与披露

- D2 默认孔径常量若与真实板孔径分布冲突，以 adapter 读到的真实值为准，常量仅兜底；
- D4 全程覆盖折线会增长折线段数（视图/对账/导出量均增），接受（U8 不设限）；
- schema 追加可选键=board_sha256 对**加了焊盘的板**必变——这正是「重转重冻」的
  内容，A 层台账按 §6 流动规则登记换版事件。
