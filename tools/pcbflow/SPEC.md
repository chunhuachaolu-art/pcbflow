# PCBFlow 设计规格 v1.3（前馈控制整合版）

> **文档状态：`authoritative`（2026-08-29 人工批准转正；决策包 D1-D8 + 修订清单 A1-A4，
> 见 `PATCH-PROMPT-FF1.md` §0/§1）。**
>
> 本文件正式整合网络注册表、视觉/多模态顾问轨道和前馈资源控制，取代 v1.2 成为设计权威；
> v1.2 原文已原样存档于 `SPEC-v1.2-archived.md`（不改一字）。
>
> 本版不改变现有 Rev-C、历史阶段报告、`NEXT.md`、`PROGRESS.md` 或既有输出的历史含义；不把“规格已写入”
> 解释为“代码已实现”或“阶段门已通过”。

---

## 变更摘要

相对于 `SPEC-v1.2-archived.md`，本版增加或收紧以下内容：

1. **前馈资源控制正式成为跨阶段规划轨道**：⓪/①提供语义和结构，②生成资源账本与 `feedforward-plan`，③/④消费计划，⑤比较预测与实际，⑥收录残差和签核证据。它不是第八个流水线阶段。
2. **网络注册表成为前馈的逐网语义输入**：计划使用稳定 `net_id`、关系 ID、端点、电气角色、routing class、层/过孔策略和来源状态，不再让各阶段分别从网络名猜分类。
3. **前馈计划与上游快照绑定**：每个计划必须绑定 registry、structures、constraints、placement 和独立 FF config 的 hash；过期计划不得被下游静默消费。
4. **资源模型可审计**：统一使用 `margin = supply - demand - reserve`，明确 `green/yellow/red/unknown`，资源赤字必须能归因到 net/relation/resource basis。
5. **前馈控制与反馈校准分离**：运行中的反馈只允许有限局部重分配；模型系数只能在离线校准环中改变，并产生新的 config/policy 版本和 hash。
6. **修正 ②→③ 走廊需求空比较**：`audit` 的 canonical 字段为 `required_mm`；缺字段或 `null` 必须是 `unknown/missing_basis`，绝不能被判为一致。
7. **收紧消费证据**：每个消费者分别记录 `declared_consumed`、`actually_read`、`derived`、`ignored`、`fallback` 和 `fidelity`，禁止把产物绑定或派生值冒充实际字段消费。
8. **保留视觉 advisory 边界**：视觉模型可以提出前馈候选和模式假设，但不能直接生成控制量、写板、改门或替代 KiCad/solver/外部签核。

---

## 0. 定位、目标和不变式

### 0.1 定位

PCBFlow 不是单纯的自动布线器，而是把整块板的诞生过程编译为可审计、可回放的七级设计流：

```text
⓪约束编译 → ①结构枚举 → ②架构可布性预检
     → ③联合布局与骨架优化 → ④细布
     → ⑤交错检查 → ⑥终检与签核
```

规划单位从单根网络提升为总线骨架、资源账本和可追溯控制合同；但最终落板仍必须服从精确几何检查、KiCad 规则和人工批准。

### 0.2 核心目标

- 在错误布局和盲目布线发生之前，预测逃逸、走廊、层、车道、过孔、电源和回流资源是否足够；
- 使每个资源赤字都能回答“谁需要它、谁占用了它、缺了多少、应该回退到哪一级”；
- 让布局器和路由器消费同一份逐网语义和前馈计划，而不是各自维护隐藏分类；
- 让预测需求、实际消耗和残差可重放、可比较、可离线校准；
- 保持人工确认点、可解释失败和确定性输出；
- 不让视觉模型、启发式预检或规划器冒充最终质量裁决。

### 0.3 不变式

1. 同一输入、同一规范版本、同一配置和同一工具链条件下，核心确定性产物必须可重放；
2. 约束、结构、网络注册表和前馈计划之间必须有 hash 绑定；
3. 硬约束高于软目标，软目标高于普通优化偏好；
4. `kicad-cli` 是 KiCad 能表达的 ERC/DRC、连通性和几何规则的唯一自动裁决源；
5. SI/PI/热/EMC/DFM 和视觉建议不能冒充 `kicad-cli` authority；
6. 前馈控制不能反向修改约束或结构权威；
7. 没有 proof 的求解结果只能是 `UNKNOWN`，不能写成 `UNSAT`；
8. 视觉、前馈和反馈都不能绕过快照、L1、批提交、DRC 和回滚纪律；
9. 未实现的命令和未完成的阶段必须如实报告，不得因规格已定义而宣称可用。

### 0.4 v1.3 的历史基线

本版已获批准（2026-08-29），第一轮实现从已有产物继续，不重做历史阶段：

- `out/revc-a3/`：阶段②审计、网络注册表、身份映射、结构和骨架种子；
- `out/revc-b1/`：阶段③布局提案、层计划、转换证明和注册表绑定；
- 当前板、`placement.csv` 和工具链锁定文件的 hash；
- 原有 FA1/FA2/FA3/FB1 证据作为只读基线。

历史文件不回写 v1.3 字段。新的前馈实验和后续消费者使用独立 snapshot/revision，例如 `out/revc-ff1/`。

---

## 1. 状态、裁决和阶段关系

### 1.1 结果状态

每个命令和产物必须区分执行状态、质量结论、检查器状态和门状态：

- `status`：`ok | failed | blocked | unknown`，表示本次运行是否完成；
- `verdict`：核心质量检查使用 `pass | fail | waived | yellow | red`；没有质量裁决的 advisory 使用 `not_applicable`；
- `checker_status`：`executed | not_executed | error`；
- `solver_status`：`SAT | UNSAT | UNKNOWN`，仅适用于求解器输出；
- `gate_status`：`pending | pass | fail | waived | blocked | not_applicable`。

网络注册表字段另有字段级 `classification_status`：

```text
inferred | source_declared | confirmed | ambiguous | unclassified | waived
```

前馈资源另有资源状态：

```text
available | low_margin | resource_deficit | missing_basis | conflict
```

这些枚举不可互相替代。例如 `status=ok` 只能说明程序执行结束，不能说明板的 `verdict=pass`；前馈 `resource_deficit`
也不能直接改写阶段②或③的质量结论。

### 1.2 三层裁决

1. **precheck**：L1 合法性、容量预测、一阶模型和前馈账本，用于筛查、排序、资源预留和归因；
2. **gate**：约束库中的硬/软/诊断规则和阶段门；
3. **authority**：在固定 profile 下运行的 `kicad-cli` ERC/DRC、连通性和可表达几何规则。

前馈计划属于规划层。它可在正式契约允许的范围内阻止明显资源不足的下游动作，但不能自行产生 ERC/DRC、solver proof、
最终 SI/PI/热/EMC 结论或 waiver。

### 1.3 七级主流水线和前馈轨道

```text
⓪ 约束编译
    ↓ 约束、网络身份、分类来源
① 结构枚举
    ↓ 总线、电源/回流树、端点、关系和优先级
② 架构预检 + 前馈计划生成
    ↓ 资源供给/需求/预留/余量 + 控制合同
③ 联合布局与骨架优化
    ↓ 消费走廊、逃逸、层、禁布和电源空间控制
④ 细布
    ↓ 消费匝道、车道、过孔、层和顺序控制
⑤ 交错检查
    ↓ 比较计划与实际，生成 residual
⑥ 终检与签核
    ↓ 收录计划、残差、迁移、advisory 和 authority 证据
```

前馈轨道不是新的串行级别，也不是一个独立的“第八阶段”。

### 1.4 失败和回退

默认回退成本顺序：

```text
局部计划重分配 < ④局部路由修复 < ③走廊/层/骨架重优化
< ②架构资源审计 < ①结构修正 < ⓪约束/原理图修正
```

同一约束同一修法回退不超过两次，第三次升级人工。前馈资源赤字必须提供：

```text
resource_id
blocking_net_ids / relation_ids
supply / demand / reserve / margin
basis/source_refs
conflicting_controls
suggested_rollback_stage
```

不能仅输出“布不通”或“架构有问题”。

---

## 2. 输入权威和依赖契约

### 2.1 权威顺序

下列对象的权威关系固定：

1. `constraints.json`：规则、参数、enforcement 和最终检查范围的权威；
2. 批准后的 `structures.json`：总线、组成员、电源树、回流树、端点、锚件和高层关系的权威；
3. `net-registry.json`：将网表/板事实、约束和结构编译成逐网只读语义视图，不得反向覆盖上游；
4. `feedforward-plan.json`：基于上述快照的资源/控制派生视图，不得反向覆盖上游；
5. KiCad net class、planner compatibility view 和旧分类表：执行或核对视图，不能在无逐网来源时冒充语义权威；
6. 视觉/多模态结果：`advisory_only`，不具有上游权威。

### 2.2 输入契约

所有输入都记录：

```text
source_uri
source_revision
sha256
schema_version
role
capabilities/fidelity（如为 adapter）
```

典型输入：

- `.kicad_sch`、网表、`.kicad_pcb` 和封装库；
- 叠层定义、板厂能力表和接口规范；
- routing/placement 规范；
- 显式结构声明和 pin mux/alternate-function 声明；
- `constraints.json`、`structures.json`、`net-registry.json`、`net-identity-map.json`；
- 批准的 placement/layout snapshot；
- 版本化核心 config 和独立的 `feedforward_config`；
- 可选的 `visual_reference`、`render_artifact`、`screenshot`、`heatmap`。

缺失输入必须成为 `missing_basis`，不能填充未经来源支持的默认值。

### 2.3 toolchain 和 adapter

项目必须使用 `toolchain_lock.json` 或等价 manifest 锁定：

```json
{
  "kicad_cli": {"path": "...", "version": "10.0.5"},
  "kicad_python": {"path": "...", "version": "..."},
  "kipy": {"version": "0.7.1", "optional": true},
  "python": {"version": "..."},
  "numpy": {"version": "..."},
  "pcbnew": {"version": "..."},
  "freerouting": {"version": "...", "optional": true},
  "jdk": {"version": "...", "optional": true},
  "schema_versions": {}
}
```

> **双版本轴注记（REPAIR-P3 W-5，2026-09-22；说明性注记不改任何值）**：
> 版本轴在本工程有且仅有两条，独立演进、禁止混用——
> ① **SPEC 编译器轴** `pcbflow/__init__.py SCHEMA_VERSION`（本文件实现版本，
> 随 SPEC 升版）与各产物格式版本（`config.SCHEMA_*`，即本节
> `schema_versions` 所载 constraints/coverage/envelope/impedance_targets=1.1）；
> ② **schema 注册表轴** `pcbflow/schemas.py REGISTRY_VERSION="3.0"`（记录
> schema 合同追加式注册代次；四孤儿名已按 `<名称>-v<N>` 语法追加注册，
> 见 DOC-NAMING-CONVENTION §12 r8）。

adapter 必须：

- 优先选择与 `.kicad_pro` 同名的目标板；fallback 取首板时报警并降级 fidelity；
- 处理 KiCad 10 层常量、net-name key、pad 角度、未灌铜区和 refill 语义；
- 明确 `--save-board` 有写盘副作用，只能在副本/快照执行；
- 记录 backend、capabilities、fidelity 和 fallback_reason；
- 版本或能力不满足时返回 `blocked` 或 `unknown`，不得静默切换后端。

### 2.4 kicad-cli authority profile

**增量路由 profile** 可使用：

```text
kicad-cli pcb drc --format json --output <path> --severity-error
```

必要时配合 `--refill-zones --save-board`，但必须在副本中执行并记录 pre/post board hash。

**终检 DRC profile** 使用 `severity-all`；**ERC profile** 单独运行 `kicad-cli sch erc` 或版本化 adapter。每次记录：

```text
工程 cwd
目标 .kicad_pro / 同名 .kicad_pcb
CLI/KiCad version
severity/refill/save 选项
return code
KiCad JSON schema
input/output hash
baseline/added/removed/changed/waived diff
```

新增违规优先按稳定 type/severity/UUID 或归一化位置身份匹配，description 和网名只作辅助。

---

## 3. 网络注册表（前馈的逐网语义基础）

### 3.1 目的和边界

`net-registry.json` 是网络的逐网编译视图，不是新的人工事实源。它解决以下问题：

- 网络名称变化时保留跨阶段身份；
- 一个网络同时属于 bus、routing class、length group、differential pair、symmetry class 和 clock domain；
- 资源模型能按电气角色和关系计算，而不是只按网络计数；
- audit/co-place/route/check 读取同一 snapshot，避免隐藏分类漂移。

### 3.2 稳定身份

配套 `net-identity-map.json`：

- 首次建档分配不可变 `net_id`；
- 网络重命名通过 aliases 和显式 migration 保留 lineage；
- 无法证明连续身份时生成新 ID，并记录 parent/lineage；
- 禁止使用数组位置、临时 KiCad net code 或显示顺序作为稳定 ID；
- 32 个 `unconnected-(...)` NC 焊盘网必须在 `excluded_nets` 显式列账，不能静默丢弃。

### 3.3 多维字段

每个网络至少包含：

```text
net_id
net_name
aliases
source_net_key
structure.bus / bus_role / member_group
 electrical.signal_type / criticality / power_role / return_role
routing.routing_class / allowed_layers / preferred_layer / via_policy / reference_plane
relations.length_group / differential_pair / segment / symmetry_class / clock_domain
 topology.kind / endpoints / branch_policy
source / classification
```

关系对象单独建模：

```text
length_group
differential_pair + segment
symmetry_class
clock_domain
coupling_group
layer_bundle
mutual_exclusion_group
```

禁止制造 `FMC_DATA_L_HIGH_SPEED_EQUAL_LENGTH_IN2_PRIORITY` 这类组合类名。

### 3.4 字段级 provenance

每个可推断字段使用：

```json
{
  "value": "FMC_DATA_L",
  "status": "source_declared|confirmed|inferred|ambiguous|unclassified|waived",
  "source_refs": [],
  "inference_rule": null
}
```

记录级状态只表示建档完整性或取最弱字段状态，不能暗示全部字段均已确认。`confirmed` 必须有裁决内容、批准人、来源版本/hash
和复审条件；`waived` 必须有理由和到期时间。

### 3.5 已知映射差异

以下差异必须继续可审计：

- `FMC_A12`：实际网表/板上存在，routing-spec 旧成员表可能只列到 A11；
- LTDC：规范声明数、实际网表成员和长度脚本成员可能不同；
- USB `_C`：可能是主差分关系的连接器侧 segment，必须保留 segment scope，未测量不能自动计入或排除；
- `SD_CD`：具体类与兜底类的选择优先级必须有来源；
- `.kicad_pro` 的 net class 可能声明类别但没有逐网指派。

注册表记录差异，不替上游资料静默修正。

### 3.6 注册表 schema

```json
{
  "schema_version": "1.2",
  "policy_version": "1.0",
  "snapshot_revision": "revc-...",
  "registry_snapshot_hash": "...",
  "design_snapshot": {
    "schematic_sha256": "...",
    "board_sha256": "...",
    "structures_sha256": "...",
    "constraints_sha256": "..."
  },
  "nets": [],
  "excluded_nets": [],
  "relations": [],
  "identity_migrations": [],
  "coverage": {},
  "diagnostics": []
}
```

### 3.7 覆盖门

必须同时验证：

```text
source → registry
registry → consumer view
constraint → checker
checker → stage
```

覆盖报告至少列出：

```text
missing_sources
unmapped_nets
unclassified_nets
ambiguous_selectors
uncovered_groups
uncovered_pins
uncovered_layers
missing_endpoints
unimplemented_consumers
nc_pad_nets
```

不能用“每类至少一条约束”替代逐网、逐关系和逐端点覆盖。

---

## 4. 约束编译 ⓪（`pcbflow compile`）

### 4.1 输入和方法

原理图、封装、叠层、板厂能力、接口规范和显式结构声明逐条编译为：

- `hard`：违反即不可交付；
- `soft`：满足硬约束后用于排序/优化；
- `diagnostic`：用于报告和趋势，不直接阻断。

每条约束必须绑定：

```text
id/source_uri/source_revision
 domain/scope
 checker/earliest_stage/final_stage
 enforcement_mode/authority/waivable
 params/implementation/implementation_version/status
```

命名推断和视觉提取不能直接产生硬约束；视觉来源必须经过文本双源核验和人工确认。

### 4.2 产物

```text
constraints.json
net-registry.json
net-identity-map.json
coverage.json
impedance_targets.json
unified envelope
run_manifest.json
```

约束库和注册表核心产物不含 wall-clock、主机绝对路径和临时路径。

### 4.3 约束覆盖门

所有网络、差分对、等长组、电源支路、回流资源、关键引脚/区域/层和 DFM 条款必须绑定约束，或明确为 non-critical/unclassified。
有未分类或来源冲突时，编译结果报告 `blocked/unknown`；不允许静默择一。

---

## 5. 结构枚举 ①（`pcbflow enum`）

### 5.1 结构对象

自动分析网络表、层级、端点和来源，形成候选：

- 接口总线：FMC、LTDC、SDMMC1/2、QSPI、RMII、USB 等；
- 时序组：九组等长关系、时钟和数据组；
- 电源树：源→轨→去耦簇→引脚；
- 回流树：参考平面、缝合和功率环路；
- 散件：GPIO/模拟点对点网络；
- 锚件：连接器、主芯片、晶振、USB 保护和机械约束对象。

自动枚举只是候选；最终 bus/member、端点、差分对、等长组和树关系来自显式结构声明或人工批准。

### 5.2 产物

```text
structures.json
net-registry.json（绑定 structures snapshot）
coverage-structures.json
priorities/mapping/budgets
unified envelope
```

必须输出 routing-spec 类、pcbagent planner 类、length-report 九组之间的 canonical mapping 和差异。

### 5.3 优先级作用域

不同优先级不得压成一个自由权重：

```text
stage_order
bus_order
net_order
objective_order
layer_preference
commit_batch_order
rollback_escalation
anchor_lock
```

跨总线顺序来自项目结构/接口规范；总线内部权重来自版本化 config；硬约束始终优先。

---

## 6. 前馈控制总模型

### 6.1 前馈与反馈

**前馈**在动作前预测资源：

```text
网络语义 + 结构 + 叠层 + 布局
    → 需求估计
    → 资源供给/预留比较
    → 资源控制合同
    → 布局/路由消费
```

**反馈**在动作后比较实际：

```text
实际消耗 - 预测消耗
    → residual report
    → 离线校准
    → 新 policy/config hash
    → 受影响阶段重跑
```

运行中可以有限地重分配局部资源，但不允许运行中自适应改系数、优先级或约束。

### 6.2 资源对象

第一版正式资源类型：

```text
escape_slots
corridor
layer_capacity
bus_lane
via_budget
power_return_space
```

资源对象至少包含：

```text
resource_id
kind
scope/region/layers
supply {value, unit}
demand {value, unit}
reserve {value, unit}
margin {value, unit}
state
basis/source_refs
net_ids/relation_ids
registry_snapshot_hash
structures_hash
constraints_hash
```

### 6.3 统一公式

```text
margin(R) = supply(R) - demand(R) - reserve(R)
```

建议状态：

```text
margin < 0                  → resource_deficit / red
0 ≤ margin < yellow_margin → low_margin / yellow
margin ≥ yellow_margin     → available / green
缺少输入或模型不适用       → missing_basis / unknown
资源控制互相冲突           → conflict / unknown 或 red（由硬约束决定）
```

`reserve` 不是“额外需求的隐形默认值”，必须来自版本化 FF config、接口规范或资源类别规则，并可追溯。

### 6.4 需求函数

不能只使用网络计数。需求至少考虑：

```text
网络数量
× 线宽/间距
× 方向/平行耦合要求
× 允许层集合
× 差分/等长/时钟关系
× 端点逃逸难度
× 换层/过孔代价
× 电源电流/铜面积
× 安全系数
```

不同角色使用不同函数：

- 普通 GPIO：剩余资源需求；
- 差分对：成对槽位、耦合间距和同步换层；
- 时钟：优先走廊、连续参考平面和受限换层；
- 等长数据：先预留组容量，再做组内调长；
- 电源轨：电流、压降、铜面积和去耦半径；
- 开关节点：短闭环、局部面积和敏感区禁入；
- 回流：平面完整性和缝合资源，不作为普通信号线计数。

### 6.5 资源冲突

控制冲突按以下顺序处理：

1. 硬约束和已批准禁区；
2. 电源、回流、时钟、差分和已声明关键网络；
3. 已批准走廊、逃逸和车道预留；
4. 总线顺序和网络顺序；
5. 普通网络剩余资源。

普通 GPIO 不得静默抢占 FMC 预留走廊；无法解决时输出 `resource_conflict` 和回退建议。

---

## 7. `feedforward-plan.json` 契约

### 7.1 顶层结构

```json
{
  "schema_version": "1.3",
  "plan_id": "FF-REVC-0001",
  "status": "planning_advisory",
  "snapshot": {
    "registry_snapshot_hash": "...",
    "structures_sha256": "...",
    "constraints_sha256": "...",
    "placement_snapshot_sha256": "...",
    "board_snapshot_sha256": "...",
    "feedforward_config_sha256": "..."
  },
  "resources": [],
  "controls": [],
  "diagnostics": [],
  "residuals": [],
  "consumption_contract": {
    "declared_consumed": [],
    "actually_read": [],
    "derived": [],
    "ignored": [],
    "fallback": null,
    "fidelity": "..."
  }
}
```

### 7.2 控制对象

每个控制至少包含：

```text
control_id
kind
target
action
source_refs
consumer_stages
priority_scope
preemption_policy
approval_state
status
```

首期控制动作：

```text
reserve_escape_slots
reserve_corridor
assign_preferred_layer
reserve_lane
reserve_via_budget
reserve_return_stitching
protect_power_loop
protect_keepout
set_route_order
propose_pin_swap
```

控制的 authority 是 `planning_advisory`，除非后续独立 consumer gate 批准其影响候选接受条件。

### 7.3 资源示例

```json
{
  "resource_id": "corridor:U1-U2:In2.Cu",
  "kind": "corridor",
  "scope": {
    "corridor": "U1-U2",
    "layer": "In2.Cu",
    "segment": "main"
  },
  "supply": {"value": 8.2, "unit": "mm"},
  "demand": {"value": 7.6, "unit": "mm"},
  "reserve": {"value": 0.0, "unit": "mm"},
  "margin": {"value": 0.6, "unit": "mm"},
  "state": "available",
  "basis": ["C-0035", "FMC_DATA_L", "FMC_DATA_H", "FMC_ADDR", "FMC_CTRL"],
  "net_ids": [],
  "relation_ids": [],
  "registry_snapshot_hash": "..."
}
```

### 7.4 计划状态和过期检查

下游消费前必须检查：

```text
registry_snapshot_hash
structures_sha256
constraints_sha256
placement_snapshot_sha256
board_snapshot_sha256
feedforward_config_sha256
```

任何不匹配都产生 `stale_plan`，不得静默消费。计划生成失败时返回 `blocked/unknown`，不生成看似完整的 green 计划。

---

## 8. 架构可布性预检 ②（`pcbflow audit`）

### 8.1 七项检查

1. **pin mux/swap**：只产生 proposal-only 候选；来源必须明确允许同组交换；不自动改原理图、网表、固件或板；
2. **逃逸容量**：引脚场按侧/层/槽位计算供给、需求、保留和缺口；
3. **层预算**：总线宽×长度、可用面积和过孔预算；
4. **走廊容量**：粗格容量和几何走廊需求；
5. **功率环路**：buck 环路、去耦半径和引脚密度；
6. **回流连续性**：换层、缝合和跨平面割缝；
7. **连接器方向**：总线出口和连接器方向一致性。

每项输出 `mode`、指标定义、分母、单位、`strict/derived`、source refs 和失败归因。

### 8.2 ② 生成前馈计划

② 不仅报告资源不足，还生成 `feedforward-plan.json`：

```text
registry/structures/constraints snapshot
    → escape demand/supply
    → corridor demand/supply
    → layer capacity
    → bus lane/via budget
    → power/return/decap space
    → controls
    → diagnostics
```

`audit.json` 必须记录：

```text
registry_snapshot_hash
feedforward_plan_hash
registry_consumed
feedforward_generated
fields_declared_consumed
fields_actually_read
fields_derived
fields_ignored
fallback/fidelity
```

这里的 `fields_actually_read` 必须由检查函数的真实读取路径证明，不能照抄声明字段。

**命令边界（D6/A4）**：当前 `feedforward-plan.json` 由独立 `pcbflow feedforward` 命令产出（§15 FF-2），
`audit` 保持七项检查+回测门现状、不生成计划；`audit` 的新 snapshot 只增记 `feedforward_plan_hash`
引用字段。§8.2 的"②生成前馈计划"按此边界理解。

### 8.3 ②→③ 走廊字段契约（必须修正）

走廊预算检查器的 canonical 输出字段为：

```text
required_mm
```

③ 只能读取 `required_mm` 作为 `audit_demand_mm`：

```python
if "required_mm" not in corridor:
    demand_consistent = "unknown"
    reason = "missing_basis:required_mm"
elif corridor["required_mm"] is None:
    demand_consistent = "unknown"
    reason = "missing_basis:required_mm_null"
else:
    demand_consistent = abs(corridor["required_mm"] - local_demand) <= tolerance
```

禁止读取不存在的 `demand_width_mm`；禁止将缺字段的 `None` 判为 `true`。可比较时必须断言值非空，并记录 tolerance、来源和数值。
历史产物中由旧字段造成的 `demand_consistent=true` 不回写；修复后产生新 snapshot 和新证据。

### 8.4 pin-swap proposal schema

```json
{
  "candidate_id": "SW-0001",
  "signal_or_bus": "FMC_A",
  "from_ref": "U1",
  "from_pin": "PG2",
  "from_net": "FMC_A12",
  "to_ref": "U1",
  "to_pin": "PA0",
  "to_net": "FMC_A0",
  "allowed_by_source": false,
  "source_refs": ["pinmap-revc"],
  "requires_schematic_edit": true,
  "requires_firmware_edit": true,
  "requires_pair_update": false,
  "affected_constraints": [],
  "delta_metrics": {},
  "cost_vector": {
    "schematic_edit": 1,
    "firmware_mux": 1,
    "external_connector": 0,
    "length_timing": 0,
    "escape": 0,
    "via": 0,
    "congestion": 0,
    "review_risk": 1
  },
  "approval": "pending",
  "status": "proposal_only"
}
```

几何代价为零不等于总体代价为零。人工批准后必须生成新输入版本并重跑 ERC、netlist parity、封装/BGA 合法性和受影响约束。

### 8.5 ② 输出

```text
audit.json
feedforward-plan.json
feedforward-coverage.json
pin-swap proposals
skeleton-seed.json
unified envelope
```

算法预测门（如断点命中率、3V3 命中和误报率）与当前板交付门分开报告。前馈 `red` 代表计划中的资源赤字，不自动等价于架构致命。

---

## 9. 联合布局与骨架优化 ③（`pcbflow co-place`）

### 9.1 输入和控制消费

③ 使用：

```text
structures.json
net-registry consumer view
skeleton-seed
feedforward-plan
approved placement snapshot
```

初始接入先做可追溯消费，不改变原有优化行为。输出必须记录：

```text
feedforward_plan_hash
feedforward_registry_snapshot_hash
controls_declared_consumed
controls_actually_read
controls_derived
controls_ignored
stale_plan_reason
```

### 9.2 可消费的控制

第一轮可作为 advisory evidence：

```text
reserve_corridor
reserve_escape_slots
assign_preferred_layer
protect_keepout
protect_power_loop
```

只有独立 FF/③ consumer gate 通过后，控制才可进入确定性候选接受条件。无论是否采纳，必须报告实际消费和忽略原因。

### 9.3 变量、目标和锚件

变量：

```text
非锚件位姿 (x,y,rot)
总线骨架拐点
总线段层指派
```

锚件集合由结构声明/人工批准确定，自动优化不得移动。placement-spec 允许的设计基线自由度与本轮自动优化自由度分开记录。

目标按以下顺序：

```text
硬约束
→ 交叉↓
→ 拥塞↓
→ 过孔↓
→ 绕行比↓
→ 对称偏差↓
```

候选稳定排序、坐标量化、tie-break、locale、JSON 序列化和 hash seed 必须固定；wall-clock 不参与接受和回退。

### 9.4 placement 事实源

- 外部/历史基线从 `placement.csv(ref,x,y,rot,side,zone)` 导入；
- `layout.json` 是当前优化提案；
- 批准后才确定性生成新的 `placement.csv` 快照并调用既有 apply 脚本；
- 不允许手工同时编辑 `layout.json` 和 `placement.csv` 而不生成转换证明；
- 前馈计划必须绑定 board 和 placement snapshot，发现不一致时报告 `conflict`，不得擅自择一。

### 9.5 输出和门

```text
layout.json
skeletons.geojson
layer-plan.json
feedforward consumption evidence
conversion.json
unified envelope
```

GeoJSON 是内部毫米坐标，不使用经纬度语义。合成板红转绿、布局规范门、转换往返和 Rev-C 冻结 sanity 分开报告。

---

## 10. 细布 ④（`pcbflow route`）

### 10.1 四步

1. **匝道**：引脚场最小费用最大流，输出出口侧/槽位；
2. **车道**：总线走廊内车道分配，使用流/ILP；
3. **描线**：沿净空距离场描线，按 routing class 使用线宽；
4. **残网**：局部 SAT/ILP 精确求解，输出合法解或严格三态结果。

每一步都允许受限的局部反馈：匝道失败回到局部出口，车道失败回到匝道/骨架，描线失败调整车道顺序，残网结果带归因回退；
不允许隐式全局随机搜索。

### 10.2 前馈消费

④ route view 从同一 registry snapshot 读取：

```text
reserve_escape_slots
reserve_lane
assign_preferred_layer
reserve_via_budget
reserve_return_stitching
set_route_order
protect_keepout
```

所有 route target、失败、资源冲突和 residual 使用 `net_id`/`relation_id`，不得重新按名称维护分类。

### 10.3 求解器三态

- `SAT`：有满足赋值，并由独立验证器复核；
- `UNSAT`：求解器完成，且有可验证 proof 或受限 blocking certificate；
- `UNKNOWN`：超时、内存限制、区域超窗、依赖缺失、不支持约束、降级或未实现。

`PathFinder converged=false`、迭代耗尽或 overload 是规划/容量状态，不是 SAT `UNSAT`。无 proof 只能 `UNKNOWN`。

### 10.4 提交纪律

若未来允许写板，必须沿用：

```text
快照
→ 每条计划 L1 精确终判
→ writer 事务
→ 不超过 10 个网络一批运行 kicad-cli DRC
→ 新增违规整批回滚
→ 回滚后再次复核
```

默认 `SexprWriter`，`--kipy` 才使用 `KipyWriter`。`--save-board` 只能在副本/快照中使用并记录板文件 pre/post hash。

### 10.5 产物

```text
route view
route plan
feedforward consumption evidence
solver_runs
resource conflicts
rollback suggestions
```

当前 PCBFlow ④尚未实现时，命令必须按 `specified_not_implemented` 报告；不得把 pcbagent 的 planner/router 直接描述成 PCBFlow route consumer。

### 10.6 门（两靶；2026-08-29 自 v1.2 §④门+§5 C2 行抄回，A1）

**门**：分两靶——(1) **残网证书化回测（冻结布局）**：F3 终态快照上对残网逐网 SAT/ILP，按三态出分类
（`UNSAT` 必带证书），并与 pcbagent S4 dry-run 上界（可收 9 / 不可收 52；2026-08-29
`tools/pcbagent/PHASE-REPORT-4.md` §3）独立对照，dataset/mode 分列；(2) **实战 ≥40/61**：靶板 = ③
`layout.json` 经人工确认点 #4 批准后重放到**快照副本**的板（冻结布局上 ≥40/61 已被 S4 上界否证，不设此门）。
两靶均零新增 error（route 批 `severity-error`、终检 `severity-all` 分列）；必须同时报告 dataset/mode/definition/
strict/derived 指标。合成 30 网全布测试板 100% 布通。route plan、失败归因和提交记录使用同一 registry snapshot 的
`net_id/relation_id`，不得重新从名称维护隐藏分类。`checker_status`、`gate_status` 和 solver 三态分别落库；每条失败必须带
`{net_id/网名/总线, 被谁挡, 资源类型, 约束 refs, 建议回退}`。

---

## 11. 交错检查 ⑤（`pcbflow check`）

### 11.1 检查器 authority

| 检查器 | authority | 说明 |
|---|---|---|
| 连通性、短路、线宽、间距、孔环 | `kicad_authoritative` | 以规定 kicad-cli profile 为准 |
| 拐点、长度、对称、差分连续性 | `deterministic_screening` | 可对照 CLI，不覆盖 CLI |
| 阻抗、串扰、回流、去耦、热、DFM | `screening_or_external_required` | 一阶趋势或外部工具 |
| EMC、眼图、协议裕量 | `external_required` | 不由 kicad-cli 单独裁决 |

### 11.2 前馈残差

检查阶段读取计划和实际结果，比较：

```text
predicted demand / actual consumption
predicted reserve / actual reserve
predicted layer / actual layer
predicted via / actual via
predicted unresolved / actual unresolved
predicted margin / final margin
```

残差定义：

```text
E(R) = actual(R) - predicted(R)
```

残差必须绑定：

```text
plan_id
resource_id
net_ids/relation_ids
measurement_convention
actual_source
snapshot_hash
```

无可比实际结果时不生成伪 residual，只记录 `not_available` 和原因。

### 11.3 视觉建议的边界

视觉发现不能写入 `stage_status`、核心 verdict、solver 状态、waiver 或 `feedforward-plan` 的控制量。视觉发现只能作为 advisory
hypothesis；若要改变计划，必须由确定性模型在新 config/spec snapshot 下重新生成计划。

### 11.4 运行策略

④期间逐总线增量检查，终局全量检查；检查器读取同一 registry snapshot 和计划 hash。任何可表达几何子集与 kicad-cli 冲突时，以 CLI 为准。

---

## 12. 终检与签核 ⑥（`pcbflow signoff`）

签核包必须包含：

```text
constraints final snapshot
structures snapshot
net-registry snapshot
net-identity-map and migrations
coverage
feedforward-plan
feedforward residuals
consumer evidence
ERC/DRC raw reports and diffs
SI/PI/thermal/DFM/external reports
waiver ledger
replay result
advisory appendix（如有）
toolchain lock and hashes
```

签核正文只由约束库终态、KiCad ERC/DRC authority、必要外部签核和人工批准决定；前馈计划和视觉 advisory 只能作为规划/顾问附录。

### 12.1 waiver

```text
constraint_id
reason
expiry（下一 rev 强制复审）
approver
created_at
```

硬约束能否豁免由约束自身 `waivable` 决定；前馈资源赤字不能自动生成 waiver。

### 12.2 重放

重放比较规范化核心产物的 hash。运行时间、主机、会话、模型响应时间和时间戳属于 metadata，不参与核心 byte-exact 比较。

---

## 13. 前馈与视觉/多模态轨道

### 13.1 视觉轨道定位

视觉轨道是可选的跨阶段 advisory track，不是串行阶段，不使用 `L5` 编号。它可以观察：

- 分层 SVG/PNG；
- 拥塞热图；
- 骨架图；
- ④增量渲染和布线动画；
- 版本或参考设计视觉 diff；
- PDF、照片、截图等非结构化资料。

视觉模型只产生疑似模式、source candidate、区域提示、风格建议和检查器候选。

### 13.2 五个岗位

| 岗位 | 结果 | 正式边界 |
|---|---|---|
| V1 检查器发现器 | `vision_hypothesis`/candidate checker | 人工接受→确定性实现→正向 mutation→negative mutation 后才可注册 |
| V2 摄入加速器 | source candidate/待核验表 | 文本双源核验后才可进入约束或结构来源 |
| V3 骨架副驾 | 区域提示/人工决定记录 | 确定性工具生成 `layout.json`，视觉不得直接写布局/板 |
| V4 监工 | 模式假设/调参候选 | 不改 audit、route、solver 或回退结论；采纳后重跑 |
| V5 对照器 | visual diff/风格要点 | 只供目标设定和人工审查 |

### 13.3 视觉 hypothesis schema

```json
{
  "hypothesis_id": "VH-0001",
  "origin": "V1-render-audit",
  "input_artifacts": [
    {"path": "relative/path", "sha256": "...", "stage": 2, "snapshot_sha256": "..."}
  ],
  "location_hint": {
    "bbox_mm": [0, 0, 0, 0],
    "coordinate_frame": "board_internal_mm",
    "transform_ref": "...",
    "execution_allowed": false
  },
  "pattern_statement": "疑似某类总线的绕行模式不一致，建议核查",
  "observed_count": 3,
  "proposed_checker": {"id": "...", "params": {}},
  "promotion_state": "hypothesis|drafting|distilled|rejected",
  "human_review": "pending|accepted_for_followup|rejected",
  "distillation_evidence": {"mutation_test_report": null, "checker_id": null},
  "authority": "advisory_only"
}
```

外层使用 `command_kind=advisory`、`verdict=not_applicable`、`gate_status=not_applicable` 的统一 envelope；模型、提供方、版本、prompt/template
hash、analysis config hash 和阶段 snapshot hash 必须进 manifest。视觉模型非确定性时只能标 `semantic` 或 `not_claimed`。

---

## 14. 统一数据库、envelope 和确定性

### 14.1 数据库表

JSON 文件库路径：`<project>/pcbflow-out/db/`。

| 表 | 核心字段 | 写入者 |
|---|---|---|
| constraints | id/source/scope/checker/enforcement/authority/params | ⓪ |
| net_registry | snapshot/policy/net/field provenance/excluded NC | ⓪① |
| net_identity_map | net_id/aliases/lineage/migrations | ⓪① |
| relations | relation_id/kind/members/segments/source | ① |
| structures | buses/power/return/anchors/priorities/mapping | ① |
| budgets | corridor/escape/layer/via/power/return budgets | ①②③ |
| feedforward_plans | plan/snapshot/resources/controls/status | ② |
| feedforward_residuals | plan/resource/predicted/actual/error/basis | ⑤ |
| coverage | source→registry→consumer/constraint→checker→stage | ⓪①⑥ |
| stage_status | stage/status/verdict/checker/gate/evidence | 各级 |
| solver_runs | solver/status/encoding/instance/model/certificate | ④ |
| advisories | hypothesis/origin/promotion/input/evidence/review/authority | 编排侧 |
| advisory_links | advisory/stage snapshot/constraint/checker refs | 编排侧 |
| waivers | constraint/reason/expiry/approver | ⑥ |
| artifacts | path/role/hash/schema/core/advisory | 各级 |
| run_manifest | toolchain/config/spec/input/model hashes/metadata | 各级 |

### 14.2 统一 envelope

```json
{
  "schema_version": "1.3",
  "tool": "pcbflow",
  "tool_version": "0.1.0",
  "command": "feedforward",
  "command_kind": "core|advisory",
  "status": "ok|failed|blocked|unknown",
  "verdict": "pass|fail|waived|yellow|red|not_applicable",
  "deterministic": true,
  "determinism_claim": "byte_exact|semantic|not_claimed",
  "inputs": [
    {"path": "relative-or-manifest-path", "sha256": "...", "role": "board|schematic|spec|config|registry|visual_reference"}
  ],
  "config_sha256": "...",
  "spec_refs": [],
  "artifacts": [
    {"path": "relative/path", "sha256": "...", "role": "core|metadata|human_report|advisory_input|advisory|advisory_appendix"}
  ],
  "metrics": {},
  "diagnostics": [],
  "waivers": [],
  "solver": {},
  "run_metadata": {},
  "data": {}
}
```

`command_kind=advisory` 时使用 `verdict=not_applicable`、`gate_status=not_applicable` 和 `authority=advisory_only`；不得写入 `stage_status`。

### 14.3 核心产物和 metadata

核心产物包括：

```text
constraints.json
coverage.json
structures.json
net-registry.json
net-identity-map.json
feedforward-plan.json
audit.json
layout.json
layer-plan.json
route/check 核心 JSON
```

核心产物不得包含 date、run_s、run_seconds、total_s、主机绝对路径或临时路径。`run_manifest.json` 单独记录：

```text
started_at/finished_at/elapsed_s
host/python/numpy/KiCad/kipy/tool versions
input/config/spec/registry/plan hashes
model/provider/prompt/config hashes
backend/capabilities/fidelity/fallback
schema versions
```

固定排序、浮点舍入、单位、locale、JSON key/order、UTF-8/newline 和 hash seed；wall-clock 不得影响算法选择、控制、阈值、接受或回退。

**schema 版本策略（A3）**：v1.3 起新增核心产物 `schema_version="1.3"`（如 feedforward-plan/coverage/
comparison/baseline-freeze）；历史 1.2/1.1 产物不回写、不升版；重放按同版本比较，跨版本只做显式迁移记录。
FF config hash 与核心 config hash 隔离（落实 §15 FF-1 条款），避免无关漂移历史 A/B metadata。

---

## 15. 前馈实施顺序和阶段门

本节定义从现有 FA3/FB1 之后继续补的实现顺序，不改变历史阶段命名或历史门。

**实施顺序（A2，2026-08-29 批准）**：FF-0..FF-3 → **FB2（B 期 E 简版骨架编辑器，自 v1.2 §5 B 期顺延至此）**
→ FF-4（③ 控制升级；需独立批准 + FF/③ consumer gate）→ FC1 → FC2 → FD1。
理由：FF-4 改变 ③ 行为，必须在依赖 ③ 语义的编辑器（FB2）之后。

### FF-0：基线冻结

- 锁定 `out/revc-a3`、`out/revc-b1` 和输入文件 hash；
- 记录历史 `registry_consumed`、`optimization.applied` 和 gate/verdict；
- 不改历史 JSON、报告或 Rev-C；
- 发现历史证据缺陷时，在新报告登记，不回写历史。

### FF-1：纯内存资源账本

新增候选模块：

```text
pcbflow/feedforward.py
pcbflow/feedforward_config.py
```

使用现有 registry、structures、audit、skeleton、layer plan 和 placement 视图，生成六类资源、controls、diagnostics 和 snapshot。

要求：

- 缺 basis → `unknown/missing_basis`；
- 资源赤字 → blocking net/relation/resource 归因；
- 计划核心 JSON byte-exact；
- FF config 与旧 config hash 隔离，避免无关漂移 A/B 历史 metadata。

### FF-2：独立命令和比较

新增候选命令：

```text
pcbflow feedforward --select plan --out-dir out/revc-ff1
pcbflow feedforward --select coverage --out-dir out/revc-ff1
pcbflow feedforward --select comparison --out-dir out/revc-ff1
pcbflow feedforward --select envelope --out-dir out/revc-ff1
pcbflow feedforward --select run_manifest --out-dir out/revc-ff1
```

产物：

```text
feedforward-plan.json
feedforward-coverage.json
feedforward-comparison.json
feedforward-envelope.json
feedforward-run-manifest.json
feedforward-report.md
```

comparison 必须包含：

```text
gate_unchanged
baseline_verdict_unchanged
optimization_applied_unchanged
board_write
registry_snapshot_match
structures_snapshot_match
placement_snapshot_match
declared_consumed
actually_read
derived
ignored
fallback/fidelity
```

### FF-3：修正②→③需求证据

先修正 `required_mm` canonical 字段消费，并增加：

- 可比较走廊非空断言；
- 缺字段/`null` 的 unknown 负例；
- `demand_consistent` 三态或带 reason 的记录；
- 旧空比较不回写；
- 新 FF comparison 中注明历史证据的局限。

### FF-4：③追踪消费

增加 plan hash、snapshot match、stale 检查和 controls consumed/ignored 证据；第一轮不改变候选接受、锚件、硬门或 Rev-C frozen sanity。

通过独立 FF/③ consumer gate 后，才允许 reserve corridor/escape/preferred layer/protect keepout 影响确定性优化。

### FC1：④匝道/车道 dry-run

实现 registry-bound route view 和 FF control adapter；可复用 pcbagent 的 Grid/Occupancy/PathFinder、Region/A*、Legality 和 DRC adapter，但不把
pcbagent prefix class 作为 PCBFlow registry authority。先只做内存 dry-run，不写 live board。

### FC2：④残网

实现描线、局部 SAT/ILP、proof、`UNKNOWN`、资源冲突和 solver 证书；无 proof/超窗/依赖缺失不能写 `UNSAT`。

门（A1，沿用 §10.6 两靶）：冻结布局残网证书化（对照 S4 上界 9/52）+ ③重放板 ≥40/61 零新增 error；
proof 缺失按 UNKNOWN 计。

### FD1：⑤/⑥

实现计划消费比较、实际残差、check consumer、signoff 附录、外部 authority 汇总和重放验证。

### 核心阶段门和 V 轨门

FF 相关门是独立的 planning/consumer promotion gate，不改变核心阶段门：

| 门 | 内容 | 是否改变主流水线门 |
|---|---|---|
| FF-0 | 基线冻结：历史产物/输入 hash 锁定、缺陷登记不回写 | 否 |
| FF-1 | 资源账本、公式、覆盖、双跑一致 | 否 |
| FF-2 | 独立 `feedforward` 命令与 comparison（含历史证据局限注明） | 否 |
| FF-3 | ②→③ 需求字段修复和非空校验（canonical `required_mm`） | 否 |
| FF-4 | ③ 只读消费、stale 检查；控制影响候选接受需独立批准，不追改历史 B 门 | 控制升级需独立批准 |
| FC1 | ④ 匝道/车道 dry-run | 否 |
| FC2 | ④ 残网/solver proof | 否 |
| FD1 | ⑤ residual + ⑥ appendix | 否 |

（表行编号与上文 FF-0..FF-4 步骤小节对齐；草案原表与步骤编号错位一行，转正时按
`PATCH-PROMPT-FF1.md` 编号修正并登记于 PHASE-REPORT-5。）

---

## 16. 测试、回放和验收

### 16.1 不重做历史阶段

以下内容作为不可变 regression baseline：

- FA1/FA2/FA3/FB1 历史产物和报告；
- 旧阶段门分母、阈值和定义；
- 旧测试中的 A/B 断言；
- Rev-C 原始板、placement.csv、opens.csv 和历史快照。

新 FF 只新增测试、产物和 snapshot，不修改历史文件来“补过”新门。

### 16.2 FF 单元和合成测试

至少覆盖：

1. `margin = supply - demand - reserve`；
2. green/yellow/red/unknown；
3. 缺 basis 不默认 green；
4. 资源、控制、net/relation 和诊断稳定排序；
5. 160 具名网有稳定身份，32 NC 网显式 excluded；
6. registry/structures/constraints/placement/config hash 自洽；
7. 两次 plan byte-exact；
8. 核心禁区扫描 clean；
9. control 冲突和 preemption 不静默覆盖；
10. stale snapshot 被发现；
11. baseline gate/verdict/optimization 状态不变；
12. board/placement/历史产物 hash 不变；
13. `required_mm` 正常比较、缺字段和 null 负例；
14. declared/actually-read/derived/ignored 不混淆；
15. six resource kinds 的可构造缺口和归因；
16. 电源、回流、开关节点、去耦、差分、时钟使用对应需求函数；
17. 视觉 advisory 不写 stage_status、不改 plan 控制量。

### 16.3 Rev-C FF shadow 验收

新 `out/revc-ff1` 必须证明：

```text
registry_snapshot_match=true
structures_snapshot_match=true
placement_snapshot_match=true（或显式 conflict）
gate_unchanged=true
baseline_verdict_unchanged=true
optimization_applied_unchanged=false
board_write=false
```

所有资源必须可追溯到 net/relation、source refs、audit/structures/layer evidence；缺少真实实际结果时不编造 residual。

### 16.4 route dry-run 验收

初期只验：

- route view 与 registry snapshot 绑定；
- escape/lane/layer/via/order controls 解析；
- 资源冲突可归因；
- solver 三态正确；
- board hash 不变；
- 未调用 live commit 或 `--save-board`。

### 16.5 检查器和视觉晋升门

V1 checker candidate 晋升必须经过：

```text
人工接受
→ 确定性实现
→ 正向 mutation
→ negative mutation
→ checker registry
```

V2 source candidate 晋升必须经过文本双源核验。V3 人工决定必须重新经过布局门。V4/V5 只能产生诊断或审查附录。

---

## 17. 失败语义、残差校准和人工确认

### 17.1 输入缺失

```text
缺少叠层/板厂能力/电流/端点/AF 表/批准结构
→ unknown 或 blocked
→ missing_basis 清单
→ 不填默认值
```

### 17.2 资源赤字

```text
margin < 0
→ resource_deficit
→ blocking net_ids/relation_ids
→ control conflict 或回退建议
→ 不自动改原理图/板
```

### 17.3 残差过大

```text
保存计划和实际
→ 生成 residual report
→ 判断输入分类/模型/布局/测量口径问题
→ 离线改 policy/config
→ 新 hash
→ 重跑受影响阶段和回测
```

### 17.4 人工确认点

以下事项必须 WAITING，不能由 agent 代办：

1. structures 显式声明和结构权威；
2. mapping 差异和上游数据源修正；
3. pin-swap proposal；
4. 锚件集合和 layout→placement 转换执行；
5. 前馈控制升级为候选硬约束；
6. 任何 waiver；
7. 视觉 source candidate 或 checker candidate 晋升；
8. 前馈资源赤字是否触发原理图/叠层/层数架构变更。

---

## 18. 禁区与红线

- 不修改当前权威 `SPEC.md v1.2`、历史阶段报告或历史输出以伪造 v1.3 完成；
- 不把前馈计划反向写入 constraints/structures 权威；
- 不静默丢弃网络，NC 焊盘网必须列账；
- 不把缺字段的走廊需求当作一致；canonical 字段是 `required_mm`；
- 不把 declared consumption 写成 actually-read；
- 不用临时 net code、数组位置或网络名作为稳定身份；
- 不让前馈计划或视觉结果代替 KiCad ERC/DRC、solver proof 或外部签核；
- 视觉不得写 stage_status、verdict、gate、waiver、feedforward controls、layout、placement 或板文件；
- 不用像素坐标执行改板；
- 不自动执行 pin swap；
- `UNSAT` 必须有可验证证书，否则 `UNKNOWN`；
- `--save-board` 只能在副本/快照执行，必须记录 pre/post hash；
- 不让 wall-clock、主机、模型响应时间或未固定随机数影响核心计划；
- 不因 FF 计划 red 自动宣称架构致命；
- 不把规格状态、命令状态、阶段状态和算法质量门混为一谈。

---

## 19. 风险登记

| 风险 | 等级 | 对策 |
|---|---|---|
| 前馈需求模型错估 | 高 | 六类资源分账、basis/source refs、实际 residual、离线校准、独立 gate |
| ②→③ 字段漂移造成空比较 | 高 | canonical `required_mm`、非空断言、unknown 负例、禁止 None=true |
| FF config 污染旧 config hash | 中 | 独立 `feedforward_config.py` 或命令级 projection |
| registry/consumer 元数据过报 | 高 | declared/actually-read/derived/ignored 分列，静态/测试证据 |
| structures/placement snapshot 不一致 | 高 | 双 hash 绑定，stale/conflict 阻止静默消费，人工决策 |
| 前馈计划被下游越权覆盖 | 高 | control ID、preemption policy、消费证明、冲突报告 |
| ④ route 资源模型和 pcbagent 不一致 | 高 | adapter、registry-bound view、dry-run 先行，不把 prefix class 当权威 |
| SAT/ILP proof 生成困难 | 高 | 局部窗口、严格三态、无 proof=UNKNOWN |
| 预测残差被运行中偷偷吸收 | 高 | 双环分离，离线新 config/hash，受影响阶段重跑 |
| VLM 误报/漏报 | 高 | advisory-only、人工核验、checker mutation 晋升 |
| 模型/提示词/服务版本漂移 | 高 | model/provider/prompt/config hash，semantic/not_claimed |
| 像素坐标误用于执行 | 高 | `execution_allowed=false`，精确坐标来自确定性工具 |
| 非结构化资料污染约束 | 高 | V2 双源文本核验，未核验不得进入 confirmed |
| GUI/VLM 依赖污染核心包 | 中 | 编排侧 runbook/adapter，核心包无 GUI/VLM 硬依赖 |
| 前馈被误读为签核结论 | 中 | advisory/planning artifact 分层，签核正文只收 authority |
| 回测数据集过拟合 | 中 | Rev-C + 合成 + 不参与调参的留出集，报告 mode/denominator |

---

## 20. 待评审决策

以下决策已在 2026-08-29 转正时由决策包 D1-D8 裁定（`PATCH-PROMPT-FF1.md` §0）；此处保留原清单供追溯，后续新决策照此流程追加：

1. `net_id` 的最终生成权和 identity map 的持久化位置；
2. 注册表与 structures 的关系对象权威边界；
3. routing class 与 KiCad net class 的源/生成关系；
4. `Reserve(R)` 的来源、默认禁止规则和每类资源的安全系数；
5. 走廊需求采用几何宽度、离散轨道、网格容量还是混合模型；
6. 电源、回流、差分、时钟和等长组的独立需求函数；
7. 普通网络是否允许抢占预留资源，以及抢占条件；
8. `audit` 与 `feedforward` 的命令职责边界；
9. FF controls 何时从 planning_advisory 升级为候选硬约束；
10. 前馈计划是否进入签核正文还是只进入 planning/advisory appendix；
11. FF config 与核心 config 的版本和 hash 管理方式；
12. USB 多段 segment、LTDC 成员和 FMC_A12 的最终上游数据源；
13. 阶段②和③的实际字段消费如何自动生成证明；
14. ④ route adapter 的 pcbagent 兼容范围和降级 fidelity；
15. 外部 SI/PI/热/EMC 工具的必需级别和签核格式；
16. 视觉轨道是否允许提出模型候选、控制候选或只允许提出检查器候选。

---

## 21. 结论

前馈控制整合后的 PCBFlow 不是“提前猜线”，而是：

> **根据逐网语义和结构事实建立资源账本，在布局/路由动作发生前预留正确的走廊、逃逸、层、车道、过孔、电源和回流资源，动作后再用可重放的实际残差校准模型。**

实施上应从现有阶段②/③产物继续：

```text
历史 A/B 基线冻结
    → FF-1 纯内存资源账本
    → FF-2 独立计划和比较产物
    → 修正 required_mm 空比较
    → FB2 E 简版骨架编辑器（A2 顺延位）
    → ③ 只读消费与 stale 检查（FF-4，需独立批准）
    → FC1 ④ dry-run
    → FC2 残网/solver
    → ⑤ residual / ⑥ signoff appendix
```

本版把前馈控制作为正式架构写完整并已于 2026-08-29 转正为权威；历史阶段门和动态状态仍以各自状态链为准（`NEXT.md`/`PROGRESS.md`/`PHASE-REPORT-*`）。
