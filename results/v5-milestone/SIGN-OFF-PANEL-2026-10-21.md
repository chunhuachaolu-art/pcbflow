# PCBFLOW V5 sign-off 签署页 · SIGN-OFF-PANEL（2026-10-21）

- 批次：PCBFLOW-RELEASE-R1（C6→C8 执行+C9 签署面备齐）；生成 2026-10-21 晚。
- 性质：tag 后追加件（不入 `v5.0-milestone-1` tag 快照）；签署批复后连同回执一笔入库。
- 签署口径（M0 批复④）：C9 签署面=「M1..M5 全绿+披露档定稿」，签署时仍呈裁；**production sign-off=false 为披露口径非阻断，本页不翻正 L2/L3**。

---

## 1. M1..M5 门读数（签署面核对，2026-10-21 实测）

| 门 | 内容 | 状态 | 证据锚 |
|---|---|---|---|
| M1 套件门（G2） | 全量 pytest 0F/0E | ✓ 绿 | EXEC-PYFIX-R1（10-17 收口；3884=3880P+4xf，EXIT=0，2705.38s；报告 sha=a1d7065d…） |
| M2 板面门（G3） | ≥5 板门=案 C 结构性豁免落册 | ✓ 绿 | M0 批复②（exec-release-review/DISPATCH-LOG.md M0 节；「未达-结构性」口径入披露档 §0 置顶） |
| M3 证据包门（G4/G5） | manifest 六件齐+A 板终读收编 | ✓ 绿 | V5-EVIDENCE-R1（10-19 收口；六件 tree 内 sha 与批登记逐位同：0519c4e2/f971ed19/ca6849d0/2569f73e/3a003068/89d57cfb） |
| M4 披露门（G8/G11/G12/G13） | 四项披露口径入档+OPT-15 UNCLOSED 更新口径 | ✓ 绿（待定稿） | DISCLOSURE-DRAFT §0-§5（G3 M0 原文 verbatim 置顶）；MANIFEST-PANELS 面板① OPT-15 行=E4 终读更新口径 |
| M5 治理门（G6/G7/G9/G10） | 提交面清零/收编+状态同步 | ✓ 绿 | G9/C7=10-19 先期清；G6/G7/G10=本批 C6：两仓提交面 89+3 项全落定（见 §2） |

## 2. C1..C9 链终态（本批后）

| 环 | 内容 | 状态 | 证据 |
|---|---|---|---|
| C1 | 套件 0F（G2 清） | ✓ 已清 | EXEC-PYFIX-R1（10-17） |
| C2 | A 板读数归位（G4 清） | ✓ 已清 | EXEC-AENG-R2（10-18；五字段双跑字节等，milestone_c2=true） |
| C3 | OPT-15 披露面定型 | ✓ 已清 | EXEC-R9-E4（10-19；UNCLOSED 维持+v1 方向挂账） |
| C4 | G3 三选一落册（M2） | ✓ 已清 | M0 批复②（10-17） |
| C5 | 证据包成包（G5 清） | ✓ 已清 | V5-EVIDENCE-R1（10-19） |
| C7 | 状态同步（G9 清） | ✓ 已清 | V5-EVIDENCE-R1 C7 三笔（10-19） |
| C6 | 治理提交面（G6/G7/G10 清） | ✓ **本批清** | route-v5 三笔归因：a5d336ef（a6x）/4d349c2d（r9e3）/91ba741a（r9e4），HEAD 93897875→91ba741a，tree 内 sha==工作树锚（18d4748a/971d379e/fbf92643）；workspace 四笔：c0b6329（批次档案 79 件）/9a07098（v5-release-pack 六件）/7a7d41d（PYFIX 面 2 件）/0b670d6（judge 胶水 2 件），HEAD f0fedf3→0b670d6，porcelain 89→0 |
| C8 | 发布形态+tag（第一段） | ✓ **本批清** | annotated tag `v5.0-milestone-1` 两仓：route-v5 tag 对象 cfacea459→commit 91ba741a；workspace tag 对象 4fbb4368→commit 0b670d6；零外发零 push（workspace ahead 9 维持不推） |
| C9 | sign-off 签署（M6） | **待签** | 本页 §4 待签栏 |

## 3. 三层 sign-off 口径（签署语义边界）

- **L1 里程碑 sign-off（M6，本页待签对象）**：V5 milestone-1 内部定格签署。签=「M1..M5 门读数+披露口径如实、里程碑按『未达-结构性』定格口径成立」；不改变任何门读数。
- **L2 production sign-off = false（永久门外，本页不翻正）**：外部 SI/PI/热/EMC/DFM+板厂叠层未接（W STATUS.md:9/:34）；软件 DRC-clean=候选质量≠生产资格。
- **L3 judge 线 sign-off = false（按线维持）**：R7-E3 qualified≠signed-off。

## 4. 待签栏

- L1 milestone sign-off 现值=**false**（MANIFEST-PANELS 面板③）。
- 待用户签署呈裁（PCBFLOW-RELEASE-R1 尾）；批复「签」=false→true 翻正+回执登记（本文件 §5+MANIFEST-PANELS 面板③同步）；批复「不签/挂起」=维持 false、本页留档。

## 5. 签署回执

- **签署时点**：2026-10-21 晚（PCBFLOW-RELEASE-R1 批内，AskUserQuestion 弹窗批复）。
- **用户批复原话（四项）**：①披露档定稿=「draft-1 即定稿（推荐）」②C9=「签署（推荐）」③挂账=「翻案窗口：维持, sign-off=false：维持, OPT-14：维持缓立」④OPT-15 v1=「维持挂账不立项（推荐）」。
- **L1 milestone sign-off：false → true**（2026-10-21）。签署语义=确认「M1..M5 门读数与披露口径如实、里程碑按『未达-结构性』定格口径成立」；不改变任何门读数。
- **披露档定稿登记**：DISCLOSURE-DRAFT.md 即定稿版（draft-1，11,088B，sha256 前16=ca6849d0354a543f，与 C5 批登记及 tag 快照逐位同）；定稿=本行时点登记，内容冻结零改动，manifest 绑定链不破。
- **L2 production sign-off=false 维持**（永久门外，本批未翻正）；**L3 judge 线 sign-off=false 维持**（qualified≠signed-off）。
- **挂账四项维持**（2026-10-21 用户裁）：翻案窗口维持、production sign-off=false 维持、OPT-14 缓立维持、OPT-15 校正器 v1 不立项（v1 方向留档：failed(L)>0 激活门+管线复验回滚）。
- **commit 回执**：签署页本文件+MANIFEST-PANELS 签署后记一笔入库；hash 与前后 sha 链=批台账 PCBFLOW-RELEASE-R1 节（state/pcbflow-optimap.md 2026-10-21 节）。
