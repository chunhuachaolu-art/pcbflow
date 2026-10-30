# PCBFLOW V5 manifest 三面板 · MANIFEST-PANELS（draft-1）

- 批次：PCBFLOW-V5-EVIDENCE-R1；生成 2026-10-19；阶段=draft-1（内部定格版草案，不 tag 不外发）。机器面=同目录 MANIFEST-PANELS.json。

## 面板① OPT 六态（21 项逐项+出处锚）

六态计数：published×1 / UNCLOSED×1 / shadow×1 / 缓立×1 / partial×1 / P2 未启×3 / 工程收口或验收×13（含 OPT-04 部分刀、OPT-12 qualified）。

| OPT | 态 | 出处锚 |
|---|---|---|
| OPT-01 | engineering_closed_accept | EXEC-R1 PASS（OPT-01 重锚纪律=现状读数绑定五锚；本包读数绑定表即其落实） |
| OPT-02 | engineering_closed_accept | EXEC-R1 PASS |
| OPT-03 | engineering_closed_accept | EXEC-R1 PASS |
| OPT-04 | engineering_closed_partial | 部分：第一刀 R2+第二刀 R3 落地；残留=第三刀逐案差异数据面（G13 披露） |
| OPT-05 | engineering_closed_accept | EXEC-R1 A_W_D |
| OPT-06 | engineering_closed_accept | R4-A（DET 4/4+SEAT 0/4 三重披露） |
| OPT-07 | engineering_closed_accept | R4-B+R8-B 接线 |
| OPT-08 | engineering_closed_accept_narrow | R8-E2B 工程+R8-E2C 有效性=窄域 1/17 板（诚实窄域答案，零外推） |
| OPT-09 | engineering_closed_accept | R2+R8-E2A；残留=真实板停线路径未验证跑触发（G13 披露） |
| OPT-10 | engineering_closed_accept | R2+R3 A1 落地；残留=zone-keepout 接通未做（G13 披露） |
| OPT-11 | engineering_closed_accept | EXEC-R1（已入库 fbd07742） |
| OPT-12 | engineering_closed_qualified | R7 未过门→R7-E3 五门 all_passed=true 转正成立+X1 跨族支持 59/60；judge 线 sign-off=false 维持（qualified≠signed-off） |
| OPT-13 | shadow | R4 G1 裁 shadow 政策+A6X-R1 观察池收档（不作有效性主张） |
| OPT-14 | deferred_not_started | 缓立（用户 2026-10-16 裁③维持；failcert n=2 证据薄；未立项口径披露） |
| OPT-15 | UNCLOSED | E2C VERDICT published（交付态非项级闭合）+E3 红线+E4 终读（机制复现 TRUE+J2 C 板无害负结果+v1 修正方向挂账）；UNCLOSED 不外推红线维持（G8 更新口径） |
| OPT-16 | published | 唯一走满六态项（planned→…→published，2026-10-08；EXEC-R1 OPT16-LAYOUT-R5-VERDICT sha16 e944fe8f） |
| OPT-17 | partial | R4 G1 R4C-04：只收 v1/partial；旧报告全量迁移出批未做（G12 披露） |
| OPT-18 | engineering_closed_accept | R10 全链收官（engineering acceptance；production sign-off 维持 false） |
| OPT-19 | p2_not_started | P2 远期未启（路线图明示不抢主线） |
| OPT-20 | p2_not_started | P2 远期未启 |
| OPT-21 | p2_not_started | P2 远期未启 |

## 面板② 门读数

| 门 | 读数 | 机读值 | 证据/绑定 |
|---|---|---|---|
| 判据一（原口径 n_sat vs require 5） | **4/5**（并记 4/4 主值/4/6 六板全量） | n_sat=4，pass=False | S09 gate g1；SCOREBOARD-B calibers；G3=案 C 结构性豁免口径 |
| 判据二干净板（微段豁免后） | **4/5** | n_clean=4，pass=False，genuine_outstanding=0，微段豁免 6 条 | S09 gate g1；MECH-VERIFY :97 重算一致 |
| R1 可布域（(c) 豁免后）主值 | **4/4** PASS | 4/4 | S11 SCOREBOARD-B calibers[0]；SAT 板=badgeleds-do-electronics、pmod-crypto、thatmicpre-v2、thin-pod |
| R1 六板全量口径（并记） | **4/6** | 4/6（failed_in_domain=pmod-bme280、tmp108） | S11 calibers[1] |
| W-D 重跑面直读 | **4/4** | 4/4 | S12（ED-X 呈裁期披露口径） |
| R2 可布域 | **6/6**（历史对照） | pass=True | S10；09-23 旧引擎世代，OPT-01 纪律不挪用 |
| 套件全量（C1） | **0F/0E** | 3884=3880P+4xf，0F/0E，EXIT=0，2705.38s | S04 §3/§6；两修复件 sha 本批复算一致 |
| A 板引擎面（C2 归位） | **五字段双跑字节等** | {"failed_nets": 0, "negotiation_rows": 1434, "ok_nets": 57, "routes": 0, "status": null}；canonical=`be49db64d61faab2`…；milestone_c2=True | S05+S21b/c/d（J1 PASS/J2 PASS_ANCHORED） |
| judge qualification（R7-E3） | **G1..G5 all_passed=true** | precision=0.6585/CI95低=0.4737/abstention=0.0136；judge 线 sign-off=**false** 维持 | S18+S19+S15（未过门历史件）；L3 线按线披露 |
| production sign-off（L2） | **false**（永久门外） | production_signoff_ready=false | W STATUS.md:9/:34（外部 SI/PI/热/EMC/DFM+板厂叠层未接） |

## 面板③ sign-off 面板（=false+依赖链 C1..C9 逐环）

- **milestone sign-off = false**（M6 未走完；签署面=M1..M5 全绿+披露档定稿，签署时仍呈裁）。
- **production sign-off = false**（L2 永久门外，见上表末行）。

| 环 | 内容 | 状态 | 证据 |
|---|---|---|---|
| C1 | 套件 0F（G2 清）+白名单件提交面（G10 提交面留 C6） | ✓ 已清 | EXEC-PYFIX-R1 收口（3884=3880P+4xf 0F/0E EXIT=0）sha=a1d7065d74b3cc06… |
| C2 | A 板读数归位（G4 清） | ✓ 已清 | EXEC-AENG-R2 收口（milestone_c2=true；五字段双跑字节等）sha=b271209cf64bbc08… |
| C3 | OPT-15 披露面定型（G8 更新） | ✓ 已清 | EXEC-R9-E4 收口（机制复现 TRUE+J2 负结果+v1 挂账；UNCLOSED 维持）sha=6e357ba02b02656c… |
| C4 | G3 三选一落册（M2） | ✓ 已清 | M0 批复②=案 C 结构性豁免（exec-release-review/DISPATCH-LOG.md M0 节） |
| C5 | 证据包成包（G5 清） | ✓ 本批清 | 本批 v5-release-pack/ 四件套（evidence-manifest+DISCLOSURE-DRAFT+MANIFEST-PANELS+RELEASE-NOTES-DRAFT） |
| C7 | 状态同步（G9 清） | ✓ 本批清 | 本批 C7：state/v7-hier gen3 终态登记+canvas-toolchain 头部刷新+STATE-INDEX 摘要行同步 |
| C6 | 治理提交面（G6/G7/G10 清） | 待裁（用户） | workspace porcelain 提交面呈裁（沿 f0fedf3 先例一并收编+judge 件专笔入库）——待用户裁 |
| C8 | 发布形态+tag（第一段已裁三两段式；落 tag 待 C6） | 待 C6 | M0 批复③=案三两段式；tag 名预告 v5.0-milestone-1（annotated，route-v5 本仓+workspace 证据仓，零外发零 push） |
| C9 | sign-off 签署（M6） | 待 M1..M5 | 待 M1..M5 全绿+披露档定稿后呈裁签署（M0 批复④口径） |

链序：C1∥C2∥C3∥C4→C5∥C7→C6→C8→C9（设计件 §5；M0 批复④采纳）。本批后链态=C1..C5+C7 清，C6/C8/C9 待。

### 台账 G1..G14 批后状态

- 本批清：G5（证据包成包）、G9（状态同步）。
- 早前清：G1（定义档=M0 闭合）、G2（PYFIX）、G3（裁决落册=案 C；B 侧另裁另排）、G4（AENG-R2）、G8（R9-E4 披露面定型）。
- 披露口径入档：G11/G12/G13（DISCLOSURE-DRAFT §2-§4）。
- 待办：G6/G7/G10=C6 治理提交面（用户裁）；G14=维持登记（本包未收编 frozen-root，如需收编另裁）。

### 红线（面板级登记）

- OPT-15 UNCLOSED 不外推红线维持；窄域主张零外推（DISCLOSURE-DRAFT §5 措辞清单）；三层 sign-off 全 false 如实登记；R2 6/6 仅历史对照。

### 2026-10-21 签署后记（tag 后追加；本节前内容=v5.0-milestone-1 tag 快照定格，原文零改动）

- **L1 milestone sign-off：false → true**（用户 2026-10-21 批复；正本回执=同目录 SIGN-OFF-PANEL-2026-10-21.md §5）。
- 披露档 DISCLOSURE-DRAFT.md 定稿=draft-1 即定稿（时点登记，内容冻结，manifest 绑定链不破）。
- L2 production=false、L3 judge=false 维持；挂账四项维持（翻案窗口/sign-off=false/OPT-14 缓立/OPT-15 v1 不立项）。
- 发布链 C1..C9 全清（C6/C8/C9=PCBFLOW-RELEASE-R1 批，2026-10-21）。

