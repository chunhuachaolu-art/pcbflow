# SELFIMPROVE-V2 FAILED 机理归因报告（FAILURE-ATTRIBUTION）

> 日期：2026-10-21　｜　授权：用户裁「只归因、不修引擎/适配器」
> 归因对象三类：① 训练侧 comp=0 六板；② 晋级层部分失败二板（**只读在盘工件，
> 零重跑**）；③ 转换失败族五板（纯登记，不跑引擎）。
> 纪律执行：引擎/适配器/任何既有件零修改；晋级/终评/红线/holdout-candidates
> 零重跑零新触；补跑仅训练侧 4 条（帽 ≤8、1800s/条、batch=fail-attrib、
> 走 pipeline rollout_runner 真实板双件套）；新产物仅落 out\selfimprove-v2\。
> 引擎绑定：v5.executor/0.11.0（补跑逐条 fail-closed 校验）。

---

## 1. 摘要（先给判定要点）

1. **训练侧 6 板 comp=0 的统一机理链**（4/6 板有 0.11.0 代轨迹实证，2/6 板
   依据 d15 记录+0.6.0 代日志/diag 如实降档披露）：
   **GND 在 route_order 恒为序首（pos=1/板，两臂同）→ 序首多端点 PWR 大网
   在焊盘场内 A\* 耗尽（obstacle-dense 兜底类，200~240 attempts）→ 引擎
   「首败即断候选」语义把 comp 直接归零 → 8 键配置面对此零自由度
   （guide=rip-up 重布波次导引，不触首布序；其余 7 键只改重试次数）**。
   与网数无关（13 网与 51 网同型）、与层数无关（4 层 tmp108/usb 同型）。
2. **diag-failed8 佐证（0.6.0 代摘除测试）**：此类板「仅摘除板固有焊盘铜
   （fixed）解锁、摘除他网已布铜/孔/边带不解锁」→ 终判 (a) 板设计固有
   不可布；引擎能力缺口 0、规则带值瓶颈 0。0.11.0 代梯子语义把 0.6.0 代
   atmega（J1-D--PadA7）/stm32（/BOOT）的首败点**提前到序首 GND**。
3. **晋级层（只读）**：rxadc_14＝与训练侧完全同签名（GND 47 端点序首耗尽，
   comp=0.0@7901s）；74Logic_SA_ADC＝**不同形态**——GND 178 端点大网
   **布通**（大板低密），序 48 位连接器网 Net-(J3-Pad6)（MISC/4 端点）耗尽
   → comp=0.370@13740s，中位单网耗尽＋rotate_budget=1 无二次机会。
4. **转换失败族（登记）**＝KiCad 方言 4 家族：legacy 层命名无 \*.Cu
   （esp32/bm11/throwing-star-pro）、自定义 power 层挂 track
   （kitspace_T32_ref）、drill 单参数 oval（Theia_Theia）、Edge_Cuts 边链
   开口（z2amiller_sensorboard）。全部 AdapterError fail-closed、确定性复现。
5. **补跑量 4/8**（seq 324-327，全部自然终态、零触帽）；案例库 8 条；
   E2 先验注入建议 5 条（含对并行 e2-probe-order 判读的关键警示：
   全可布合成板上序的完成率级响应按机理不存在，探针「全平」≠序无判别力）。

---

## 2. 训练侧六板归因（类别①）

### 2.1 证据基础（三层）

| 层 | 来源 | 内容 |
|---|---|---|
| 折叠记录 | rollouts.jsonl 18 条（seq 169-212） | FAILED 12 条全部 first_fail_net=**GND**、comp=0.0、A/B/C 三配置同型；TIMEOUT 6 条＝D 批 1800s 帽†（usb/stm32/tmp108 的 B/C） |
| 0.11.0 轨迹 | 本批补跑 seq 324-327（attrib\traces\） | atmega/bme280/stm32/dc-scm 四板 negotiation_log 全捕获 |
| 0.6.0 代存档 | v5-p5\boards\{atmega,bme280,tmp108}\execute.json＋diag-failed8\ | 三板旧日志＋六板摘除测试 witness |

### 2.2 每板归因结论

| 板（tier/网/层/面积） | GND 端点/拓扑边 | GND 序位 | 0.11.0 轨迹（attempts/失败形态） | FAILED 记录（wall） | 归因结论 |
|---|---|---|---|---|---|
| pmod-bme280（T1/13/2L/557mm²） | 14/13 | 1/13 | seq325：217 att（T11→M2/10 边 MST），astar 194＋末栅格封 F.Cu 18；via-plan 错位 +1.11803＞D3 1.10 | A 490s/B 3505s/C 1820s 全 FAILED | 序首 GND 在 F.Cu 焊盘场布通失败（obstacle-dense） |
| tmp108（T1/14/**4L**/563mm²） | 10/9 | 1/14 | 无 0.11.0 日志（A=1889s 超 1800s 帽不补跑，如实）；0.6.0 日志：214 att（M0/6 边），astar 196＋末栅格 F.Cu 16 | A 1889s FAILED；B/C TIMEOUT†1800 | 同型；4 层不救（候选层指派下仍封） |
| stm32-ds2480-emu（T2/29/2L/511mm²） | 19/18 | 1/29 | seq326：227 att（T13→M3/13 边），astar 212；via-plan 4 条全 +1.11803 | A 684s FAILED；B/C TIMEOUT†1800 | 同型；版本迁移注：0.6.0 代 GND 可布、首败=/BOOT（14 网铜已提交后），0.11.0 把失败点提前到序首 |
| atmega32u4-breakout（T2/46/2L/996mm²） | **52/51**（MST 38 边） | 1/46 | seq324：238 att（T0→M8/38 边），astar 211＋首栅格封 F.Cu 19 | A 63s/B 459s/C 239s 全 FAILED（+补跑 32.5s） | 同型；0.6.0 代首败=J1-D--PadA7（USB-C 焊盘场，ripup-exhausted 318），diag 终判 (a) |
| dc-scm-rot-jumper-card（T2/48/2L/1175mm²） | **仅 3/2** | 1/48 | seq327：212 att（T0→M0/2 边），astar 161＋**escape 封 B.Cu 49**（末栅格 44＋首栅格 5）＋端点直连段封（R5/R6/R2/容量）2 | A 852s/B 6183s/C 3120s 全 FAILED | **最小 GND 也死**：终点半密封＋绕行域被 47 邻网焊盘场封死（diag witness 81/162 开）；escape 形态占比 23%（其余板 7-8%） |
| usb-gigabit-rev-e（T2/51/**4L**/1075mm²） | **58/57** | 1/51 | 无 0.11.0 日志（A=2474s 超帽不补跑，如实） | A 2474s FAILED first_fail=GND；B/C TIMEOUT†1800 | 同型（主据 d15 记录）；0.6.0 diag：U2-CS 318 att ripup-exhausted、伴生阻塞集＋3V3/U2-CLK、终判 (a) |

### 2.3 机理链（六板统一，逐环机械核验）

1. **序首确定性**：planner route_order=sort(cls, LADDER_RANK[ptype], len, pid)；
   六板 GND ptype=PWR（rank 3）先于 MISC（rank 4），PWR 内 PT-GND 字典序
   最前——compile+plan 纯函数复算：**六板 × {no-principle, principle} 两臂
   GND 全部 pos=1**（零例外）。
2. **首败即断**：executor 主环分区内 attempts 耗尽 → `failed=True; break` →
   候选 verdict=FAILED、routes=None；per_net 只含失败前的条目 →
   completion=已布前缀/总网=**0/n=0**。
3. **耗尽形态**：每拓扑边 106 计划阶梯（prefer/no-prefer × r2-near/
   overlap_free × via-priced/free × lane-shift × pitch=0.125 + r1/r2/r3
   八向 escape）全灭 → 整网回滚 → 拓扑边耗尽 → MST fallback → 再灭 →
   终判 FAILED after 212~238 attempts；exhaustion-cause=
   **obstacle-dense（兜底类）**＝edge-clearance/hole-keep-out/endpoint-
   sealed/via-obstacle/capacity-locked/sensitive-crossed 六specific类全被
   分类器排除后的剩余桶。
4. **封堵源**：geom-secondary=**open**（仅计板固有固定铜时端点出边开放）→
   端点未被板固有铜直接密封，封堵在**绕行域**；diag-failed8 摘除测试
   （0.6.0 代，4/6 板在列）：routes/vias/holes/edge 四类摘除仍锁，**仅
   fixed（板固有焊盘铜）摘除解锁** → 板设计固有不可布（(a) 类）。
5. **配置面零自由度**：8 键中 guide=rip-up 重布波次导引（executor.py W-3）、
   不触首布 route_order；rotate/max_total 等只改「同一 doomed GND 重试几次」
   ——bme280 A 角点 1 候选 490s、B 角点 8 候选 3505s，comp 恒 0。与 D15
   「完成率级 0 主级判别力」「板间方差在板面不在配置面」实测互证。
6. **失败阶段判定**（任务口径 escape/capacity/层布通/后处理前）：
   **主阶段=层布通（层内 A\* 带约束寻路耗尽）**；escape 为子形态（首/末
   栅格段被封，16~49 条/板，F.Cu 或 B.Cu）；capacity 不参与（零
   capacity-locked 分类，diag 走廊通道扫描空旷或达标）；后处理未达
   （routes=None）。

### 2.4 反直觉读数（如实披露）

- 端点数、板面积、层数均不单独决定成败：dc-scm 3 端点 GND 死、
  74Logic 178 端点 GND 活（晋级层对照，§3）；pmod-crypto（ROUTED 0.75）
  与 bme280（FAILED）密度几乎同（53/568 vs 52/557 端点/面积）。
  分水岭是**局部几何**（焊盘场对 GND 绕行域的密封），非全局统计量
  ——正是 E2 网序打分需要分区级/几何级特征、板级 19 维不够用的证据。
- comp<1 与 ROUTED 可并存：pmod-crypto 0.75/thin-pod 0.714 的缺口全部
  ＝degenerate 分区（保守计未布），非布通失败——E2 fitness 读数时须区分。

---

## 3. 晋级层部分失败板（类别②，只读在盘工件）

| 板 | 模型臂读数（seq） | 结构（只读板件） | 归因 |
|---|---|---|---|
| rxadc_14_rxadc_14（T2/51 网/4L/1354mm²） | FAILED comp=0.0，first_fail=GND，7901s（seq317）；baseline TIMEOUT@14400s（seq318） | GND=PWR/47 端点/46 拓扑边，route_order 序首 | **与训练侧六板同签名（FA-2）**：序首 GND 耗尽→首败阻断→comp=0。零重跑核验：结构字段+记录与六板机理链逐环吻合 |
| 74Logic_SA_ADC_SA-ADC（T3/127 网/2L/6855mm²） | FAILED comp=0.370，first_fail=Net-(J3-Pad6)，13740s（seq313）；baseline TIMEOUT@14400s（seq314） | GND=PWR/**178 端点/177 边布通**；Net-(J3-Pad6)=MISC/4 端点，序 48/127（MISC 字典序） | **不同形态（FA-3 中位单网耗尽）**：47 网已布通后连接器网 J3-Pad6 耗尽→首败阻断，comp=47/127；rotate_budget=1（A 角点推荐）无二次候选；对照同板 GND 大网成功——大板（6855mm²）低密下序首大网可活，焊盘场局部密封才是判别面 |

参照（同层其余，RETRO §4）：thunderbolt/kitspace_uno TIMEOUT@14400s、
z2amiller_prog ROUTED 0.818、z2amiller_sensorboard 转换失败（§4）。

---

## 4. 转换失败族（类别③，纯登记——KiCad 方言 4 家族）

| 家族 | 板 | raw 源证据（只读核验） | 适配器报错（fail-closed） | 在案工件 |
|---|---|---|---|---|
| **FA-5a** layers 块 legacy 命名（无 \*.Cu token） | esp32-cantroller_EltekController | `(0 Front signal)`/`(31 Back signal)` | `(layers) 块中无启用的铜层（*.Cu）`；确定性复现 2/2 | RETRO-E1 §3 |
| | bm11 | `(0 Top signal)`/`(31 Bottom signal)` | 同上；复现 2/2 | RETRO-E1 §3 |
| | throwing-star-pro | `(0 Front signal)`/`(31 Back signal)` | 同上（D 批池核验 not_viable，复现） | D-REPORT §3 |
| **FA-5b** 自定义 power 层挂 track | kitspace_T32_ref | `(1 GND power)`/`(2 PWR power)` 声明、track 挂 GND 层 | `segment 层 'GND' 不在启用铜层中`；复现 2/2 | RETRO-E1 §3 |
| **FA-5c** drill 单参数 oval | Theia_Theia | `pad 1 … (drill oval 1.1)`（SRD-05VDC-SL-C，L260） | `(drill) 形态不可解析 ['oval','1.1']（须 (drill D) 或 (drill oval A B)）` | **alt-precheck-2026-10-21.json**（本族唯一在 precheck 在案者） |
| **FA-5d** Edge_Cuts 边链开口 | z2amiller_sensorboard | 边链终点 (126.3,91.7) 无可继边（容差 0.01mm） | `bad outline：Edge_Cuts 边链开口`（与 kicad-cli 同口径） | e1\promo-boards\promo-convert.json |

对照 alt-precheck-2026-10-21.json：其 4 条中仅 Theia 属本族；Lcr_addon/
video/vme-wren 三条 ok（video 588 网/vme-wren 1800 网均转换通过——
方言失败与板规模无关，纯源文件写法）。esp32/T32_ref/bm11 的转换失败
证据在 RETRO-E1 §3、throwing-star 在 D-REPORT §3，均已交叉核对。

---

## 5. Failure-Atlas（失败形态分类）

| 编号 | 形态 | 机制 | 载体（本轮实证） | 阶段 |
|---|---|---|---|---|
| FA-1 | 候选级首败阻断 | 分区 attempts 耗尽→整候选 abort（routes=None），comp=已布前缀/n | 全部引擎侧 FAILED（executor 主环 break 语义） | 语义层（放大器） |
| FA-2 | 序首 PWR 大网 obstacle-dense 耗尽 | GND pos=1＋多端点 Steiner/MST＋焊盘场绕行域密封；200-240 att | 训练侧 6 板＋rxadc_14 | 层布通（escape 子形态） |
| FA-3 | 中位 MISC 连接器网耗尽 | 4 端点连接器网焊盘场封死，序中位遇险即断 | 74Logic J3-Pad6（pos 48/127） | 层布通 |
| FA-4 | 预算帽截断 TIMEOUT | 1800s/14400s/4h 帽执法 | †D 批 6 条、promo baseline 2 条、（上下文）retro beer-gauge | 帽执法（非机理） |
| FA-5a-d | 转换 fail-closed 方言族 | legacy 层名/自定义 power 层/drill oval 单参/Edge_Cuts 开口 | §4 五板 | 转换层（引擎外） |

附注（非失败但影响读数）：degenerate 分区扣 comp（pmod-crypto 0.75、
thin-pod 0.714 均为 ROUTED）；via-plan 披露行的 +1.11803mm=**hypot(1.0,0.5)
对角栅格步恒超 D3 限 1.10mm 0.018mm**（bme280/stm32 多次出现，系统性
边距擦限，见 CL-8）。

---

## 6. 案例库条目（现象/复现/如何发现/如何对冲）

**CL-1［FA-2］序首 GND 多端点网 comp=0**
- 现象：任意配置下 comp=0.0、first_fail_net=GND、wall 63~6183s。
- 复现：`py -3.12 rollout_runner.py --board dbatch\boards-real\pmod-bme280.board.v1.json --config-json "{A角点}" --batch <批> --allow-real-boards --reserved-file dbatch\reserved-boards.txt`（确定性：同 (板,配置) 逐位同读数）。
- 如何发现：rollouts.jsonl 12 条 FAILED 的 first_fail_net 全 GND → v5-p5 execute.json negotiation_log → 本批 0.11.0 轨迹补闭环。
- 如何对冲（E2 面）：序打分器把「多端点 PWR/GND×高密小板」降序位（PE-1）；引擎面（禁改，仅记录）：首败跳过继续布或预检短路已有 sealed-short-circuit 先例（W-1，仅焊盘全封形态，本族 geom=open 不命中）。

**CL-2［FA-1］首败即断把 0/127 放大成 0**
- 现象：74Logic 47 网已布通仍记 comp=0.370 且 verdict=FAILED；rxadc 序首死记 0.0。
- 复现：对比 seq313（74Logic，首败位 48）与 seq317（rxadc，首败位 1）——同 abort 语义、不同银行余额。
- 如何发现：completion 口径=per_net 前缀（rollout_runner._completion）＋executor break 语义联读。
- 如何对冲：E2 打分器显式建模 comp=f(首败位)——把预测高风险网后置可把 comp 从 0 抬到 k/n（不需引擎改）。

**CL-3［FA-3］连接器焊盘场网中位耗尽**
- 现象：4 端点连接器网（J3-Pad6）在 47 网成功后耗尽，一票否决全板。
- 复现：只读 ck1-promo 记录 seq313＋板件结构（Net-(J3-Pad6)=MISC 字典序 48 位）。
- 如何发现：74Logic 的 first_fail 非 GND → route_order 复算定位序 48。
- 如何对冲：E2 反例先验——细间距连接器 pad 网（Net-(Jx-PadN) 族）降序位；diag-failed8 witness 家族（m2 CLKREQ/pmod io01-07/usb U2-CS）全为同型焊盘场封死。

**CL-4［FA-5a］KiCad legacy 层命名拒收**
- 现象：`(0 Front signal)`/`(31 Top signal)` 等旧命名 → 「无启用铜层」。
- 复现：read raw.kicad_pcb (layers) 块（esp32/bm11/throwing-star 三板逐字核验）。
- 如何发现：D 批池核验＋RETRO 转换台账 2/2 确定性复现。
- 如何对冲（登记，不修）：语料准入预检加 layers 方言 grep；或（须用户裁+改适配器）Front/Back→F.Cu/B.Cu 映射——本轮零改动。

**CL-5［FA-5b］自定义 power 层挂 track**
- 现象：T32_ref 声明 `(1 GND power)` 层并有 track 挂其上 → 「segment 层不在启用铜层」。
- 复现：raw layers 块 L2-4 在案；RETRO 2/2。
- 如何发现：RETRO 转换失败清单＋本轮 raw 源核验。
- 如何对冲：同 CL-4（预检或映射，均须裁决）。

**CL-6［FA-5c］drill oval 单参数**
- 现象：`(drill oval 1.1)` 两参数形态缺一 → 形态不可解析。
- 复现：Theia raw L260 逐字在案；alt-precheck-2026-10-21.json 登记在案。
- 如何发现：alt-precheck（替补席预检）。
- 如何对冲：预检 regex `(drill oval <单数字>)`；修复（补默认短轴？）须裁决——语义有歧义（1.1 是孔径还是长轴），fail-closed 合理。

**CL-7［FA-5d］Edge_Cuts 边链开口**
- 现象：边链终点 (126.3,91.7) 无可继边（0.01mm 容差）→ bad outline。
- 复现：promo-convert.json 台账在案（kicad-cli 同口径）。
- 如何发现：E1 晋级层首次转换（2026-10-20T20:05Z）。
- 如何对冲：源数据修边（数据面）；引擎侧无动作（口径一致是特性）。

**CL-8［几何擦限］via-plan 对角步恒超 D3**
- 现象：过渡孔错位 +1.11803mm＝hypot(1.0,0.5)（栅格对角步），D3 最小孔心距 1.10mm——任何落在该对角步的孔对都差 0.018mm 违限。
- 复现：bme280（0.6.0 与 0.11.0 日志各 1 条）、stm32 0.11.0（4 条全同值）。
- 如何发现：本批轨迹逐行归类时同值聚集暴露。
- 如何对冲：登记为引擎几何常量级擦限（孔步栅格 vs D3 带值的整数格不匹配）；属规则带值面候选，E2 不 consume（序面无关），如处置须单独裁决。

---

## 7. E2 先验注入建议（网序打分器反例先验）

1. **PE-1 序首大网降权**：反例＝6 板+rxadc 的 GND pos=1 全灭（comp=0、
   200-240 att、obstacle-dense）；对照 74Logic GND 178 端点在 6855mm²
   低密大板布通。建议打分特征：分区端点数×板密度（端点/面积）×层资源
   的联合风险项，把「多端点 PWR×高密×少层」降序位——**不是无脑 GND
   后置**（74Logic 反例在案），是密度条件化。
2. **PE-2 完成率银行模型**：comp=f(首败位)（FA-1 语义）。打分器目标函数
   显式含「预测 doomed 位后置」收益：rxadc 0.0 vs 74Logic 0.370 同语义
   对照即天然正反例对，可直接作 L2 训练样本。
3. **PE-3 连接器 pad 网反例族**：Net-(Jx-PadN)/细间距连接器 4 端点网
   降序位（CL-3；diag witness 家族佐证）。
4. **PE-4 前置探针判读警示（关键）**：并行在跑的 e2-probe-order（12 条，
   合成板全 ROUTED）若读出「完成率级全平」，**按本归因机理这是预期而
   非序无判别力的证据**——全可布板上序只动次级指标（D 批 D2/D3=0 判别
   力同构）。建议：判据补「含 doomed 网的板（u 板不可布旋钮族或
   74Logic/rxadc 型）上完成率级序响应」一支，否则 §0 判据假阴性停呈风险。
5. **PE-5 attempt 成本先验**：doomed 网单网成本=106 计划/拓扑边×边数
   （实测 200-240 att、A 角点 32-491s、B 角点至 3505s）且**序不改变该
   成本**，只改银行余额——E2 fitness 预算规划与「易网优先≠提速」的
   预期管理。

---

## 8. 补跑台账与预算

- 批=batch=**fail-attrib**，4/8 条帽（atmega 32.5s／bme280 272.8s／
  stm32 490.8s／dc-scm 481.4s，合计 1277.6s，零触 1800s 帽，零 TIMEOUT）；
  seq 324-327 入 rollouts.jsonl（302 行）＋budget-ledger（total 339）。
- tmp108（A=1889s）与 usb-gigabit（A=2474s）超 1800s 帽**不补跑**，
  归因降档依据既有记录（三态如实，§2.2）。
- 并行批披露：rollouts.jsonl 另有 e2-probe-order 12 条（seq 328-339，
  他代理前置探针），本归因零接触、零依赖。

## 9. 产物清单（绝对路径）

- 报告本件：`<ENGINE_ROOT>\out\selfimprove-v2\reports\FAILURE-ATTRIBUTION-2026-10-21.md`
- 断点件：`<ENGINE_ROOT>\out\selfimprove-v2\ATTRIB-STATE.md`（COMPLETED）
- 驱动＋轨迹：`<ENGINE_ROOT>\out\selfimprove-v2\attrib\fail_attrib_run.py`、
  `...\attrib\fail-attrib-manifest.json`、`...\attrib\traces\{atmega32u4-breakout,pmod-bme280,stm32-ds2480-emu,dc-scm-rot-jumper-card}.fail-trace.json`
- 数据底座增量：`<ENGINE_ROOT>\out\selfimprove-v2\pipeline\data\rollouts.jsonl`（batch=fail-attrib 4 行）＋同目录 `budget-ledger.json`
- 只读依据（零改动）：`out\v5-p5\boards\*\{run-result,execute}.json`、
  `out\v5-p5\diag-failed8\*`、`e1\promo-boards\*`、`e1\checkpoints\*`、
  `e1\state\ck1-promo-queue.json`、`reports\{RETRO-E1-REPORT,D-REPORT,D15-REPORT,alt-precheck-2026-10-21}.json/md`、
  datasets raw .kicad_pcb（pcbench-r1/pcbbenchmarks-r1/corpus-r2-r1）
- 引擎源码只读核验：`route-v5\v5\{executor.py,planner.py,partition.py,compiler.py}`
