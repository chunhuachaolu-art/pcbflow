# PCBFLOW V5 milestone · RELEASE NOTES（草案·内部定格版）

## v5.0-milestone-1（tag 预告名；**落 tag 属 C8，本批不 tag 不外发**）

- 批次：PCBFLOW-V5-EVIDENCE-R1（C5）；草案生成：2026-10-19；发布形态=**两段式第一段=内部定格版**（M0 批复③：先形态一内部定格收口叙事+route-v5 本仓 annotated tag+workspace 证据仓 tag+发布件全套，零外发零 push；公开前置件四件并行清障、公开时点另行裁决）。
- 语义：本里程碑为**内部收口定格**，非「核弹」公开发布（核弹本义=公开发布级里程碑，公开段属第二段、待 D-5 GPL 依赖审计/引擎外泄解禁裁决/语料板源许可审计/holdout 红线处置四前置件后另裁）。

## 1. 里程碑定义（范围/门/裁决链）

- **范围**（设计件 §1.1 门内边界）：引擎读数面收口（记分牌双口径定格+A 板归位+失败证据门=处置名册现行形态）；套件面全量 0F；发布件（证据包+披露档+manifest 面板+RELEASE-NOTES）。门外明示不做：production sign-off（L2 永久门外）、OPT-14 立项、OPT-19/20/21、引擎能力扩项、v7 gen3 终态判定本身（仅状态同步登记）。
- **门 M0..M6**：M0 定义门=用户 2026-10-17 深夜四项批复（G3 三选一/发布形态/sign-off 链采纳/AENG 帽-对象）已闭合；M1 套件门=PYFIX-R1 收口 0F/0E；M2 板面门=G3 案 C 结构性豁免落册即闭合；M3 证据包门=本批；M4 披露门=DISCLOSURE-DRAFT 定稿面；M5 治理门=C6 提交面待裁；M6 签署门=C9 待。
- **裁决链**：M0 批复④=sign-off 前置链 C1..C9 采纳（L1 里程碑/L2 production/L3 judge 三层分离）；链态见 MANIFEST-PANELS 面板③（C1..C5+C7 清；C6/C8/C9 待）。

## 2. 门读数（正本=evidence-manifest 读数绑定表，五锚逐行）

| 门 | 读数 |
|---|---|
| 判据一（原口径） | **4/5**（n_sat=4 vs require 5；并记=SCOREBOARD-B 主值 **4/4**+六板全量 **4/6**） |
| 判据二干净板（微段豁免后） | **4/5**（genuine_outstanding=0） |
| 可布域（(c) 豁免后） | **4/4 全净**（SAT 板=badgeleds-do-electronics/pmod-crypto/thatmicpre-v2/thin-pod） |
| 六板全量口径 | **4/6**（bme280+tmp108 留分母计 FAILED） |
| W-D 重跑面直读 | **4/4** |
| R2 可布域（历史对照） | 6/6（09-23 旧引擎世代，OPT-01 纪律不挪用） |
| 套件全量 | **3884 collected=3880 passed+4 xfailed，0F/0E，EXIT=0** |
| A 板（HR1-BOARD-A:orig 引擎面） | 五字段 `{"failed_nets": 0, "negotiation_rows": 1434, "ok_nets": 57, "routes": 0, "status": null}` 双跑字节等，跨 0.9.0→0.11.0 世代逐位等（C2 归位） |
| judge qualification | **G1..G5 all_passed=true**（qualified；judge 线 sign-off=false 维持） |
| sign-off（三层） | L1 里程碑=false（C9 待）/L2 production=false（永久门外）/L3 judge=false（qualified≠signed-off） |

## 3. 披露摘要（正本=DISCLOSURE-DRAFT）

- **G3 结构性豁免（置顶）**：≥5 板门原文不动；「R1 世界 SAT 恰 4 板、可布域 4/4 全净、差口不指向任何脏板=结构性」——立项目标按「未达-结构性」口径定格；案 B 扩板集作后续批候选登记（C+B 组合之 B 侧另裁另排）。
- **G8 OPT-15=UNCLOSED**：E4 终读=机制复现 TRUE（B 板端到端）+J2 C 板无害性负结果合法收档+v1 修正方向挂账；发布叙事不得声称传导矩阵收益闭合。
- G11 OPT-14 未立项（缓立维持）；G12 OPT-17 v1/partial；G13 OPT-04/09/10 残留刀口逐项披露；窄域主张零外推（OPT-08 合格板 1/17 等，措辞清单 DISCLOSURE-DRAFT §5）。
- production sign-off（L2）=false 永久分离：外部 SI/PI/热/EMC/DFM+板厂叠层+实物 bring-up 属 V2 层次二线从未启动面。

## 4. 版本锚与证据件

- executor=`v5.executor/0.11.0`（v5/executor.py:351）；postprocess=`v5.postprocess/2.1.0`（v5/postprocess.py:117）；route-v5 HEAD=`9389787587b6922dbdc4a2d31d5de58b2ab93f82`；套件仓 HEAD=`f0fedf3d7a397a84a40ff97b3b02067342b97d72`。
- 证据包=v5-release-pack/（evidence-manifest.json/.md 处置名册+读数绑定表+judge/套件/A 板收编清单；DISCLOSURE-DRAFT.md；MANIFEST-PANELS.json/.md；本件）——一切 sha256 程序化现算（沙箱机读总表 evidence-hashes.json）。

## 5. tag 预告（落 tag 属 C8，待 C6 治理提交面后）

- 建议名：**`v5.0-milestone-1`**（annotated tag，route-v5 本仓+workspace 证据仓各一枚；本仓无远端、全历史零 push 维持）。
- 前置：C6 治理提交面清（G6/G7/G10 收编）→C8 落 tag→C9 sign-off 签署呈裁。

## 6. 已知未决面（诚实清单）

- C6 治理提交面（workspace porcelain 收编+judge 件专笔入库）待用户裁；G14 frozen-root 旁侧 junction 维持登记（本包未收编 frozen-root 面）。
- OPT-15 v1 修正方向挂账（failed(L)>0 激活门+管线面复验回滚，待批另立）。
- 案 B 扩板集=后续批候选（凑足 5 板后按修订 manifest 再发布一次的通道保留）。
- 公开段（第二段）四前置件未启动：D-5 GPL 依赖审计/引擎外泄解禁裁决/语料板源许可审计/holdout 红线处置。

