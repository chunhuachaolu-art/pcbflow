"""PCBFlow 铜箔闭环 P2/P3b —— 按铜箔对象寻址的补丁引擎（闭环"能改板"的核心环节）。

位置：P1a `copper_model`（板侧铜箔事实源，给出身份键 `key` 与节点字节跨度
`span`）之后、P3 zone 合同（`svg_route_package` v2 的 `fill_state` 语义）之
上的**唯一写板入口**。`apply_patch` 是纯函数生成器：板文本 → 板文本，不落盘、
零子进程、零 wall-clock、零随机（`fill_gate` 的**唯一** IO 是读一份可选的重填
证据文件，且只在调用方给了 `revision_dir` 时发生；本模块**从不写文件**）。

冻结 API
--------
OP_TYPES = ("add", "modify", "delete")
OP_KINDS = ("segment", "via", "zone")

apply_patch(board_text, ops, *, eol=None) -> dict
    {"ok": bool, "verdict": "accepted"|"blocked", "reasons": [str],
     "board_text": str|None, "ledger": dict}

op 形状：{"op": "add"|"modify"|"delete", "kind": "segment"|"via"|"zone",
          "key": str|None, "expect": dict|None, "new": dict|None}
  * modify/delete 必须给 `key` 与 `expect`；add 必须给 `new` 且禁止给
    `key`/`expect`（delete 亦禁止给 `new`）。
  * `expect` 是**对当前节点事实的断言**（乐观并发/过期检测）：字段
    net/layer/width/start/end（segment）、net/at/size/drill/layers（via）、
    net/layers/outline_mm/params（zone），另接受 uuid（三类）与 via_kind
    （via）。量化口径与 `copper_model` 一致（坐标 6 位、宽度/尺寸/钻孔与
    zone 参数 3 位），故 expect 可原样抄自 copper_model 的解析结果。
    **任一字段与现状不符即 blocked**（整批拒绝）。zone 的 `params` 断言是
    **逐键子集**语义（只比对给出的键，未给出的键不参与），其余字段是整值
    语义 —— 理由：zone 参数集合随 KiCad 版本增长，整值断言会把"上游新增
    一个默认参数"误判成过期。
  * `new` 字段集与 copper_model 解析出的对象同类；`add` 必须给全必需字段
    （segment: net/layer/width/start/end；via: net/at/size/drill/layers；
    zone: net/layers/outline_mm），`modify` 允许部分字段（未给字段从**目标
    节点原始字节**继承，不走 copper_model 的量化值，故未改字段逐字节不变）。
    `new` **不接受 uuid**（新节点 uuid 一律由本模块按对象级口径派生，见下），
    via 另接受 via_kind，zone 另接受 params（见"zone op 语义"）。
    `expect` 另接受 uuid、via_kind（via）与 params（zone）作为断言字段。

verdict 语义
------------
* accepted：`board_text` = 新板文本，`ledger` 完整，`reasons == []`。
* blocked：`board_text is None`，`reasons` 逐条说明（**收集全部失败**，
  不只第一条）。**任何一条 op 失败则整批拒绝**，绝不半途改一半。

blocked 条件（fail-closed）
--------------------------
1. 未知 op / 未知 kind / 字段形状非法（缺 key/expect/new、add 多给 key 等）。
2. 字段类型或枚举非法（net/layer 非空串、width/size/drill 为正有限数、坐标为
   数值对、segment/via 的 layers ≥2 个串、zone 的 layers ≥1 个串、
   via_kind ∈ {through,blind,buried}、zone outline_mm 是 ≥3 个数值点对、
   zone params 键在可编辑集内且取值合法、名称不含换行）。
3. `key` 在板上找不到；`key` 匹配到多个节点（身份残留撞键）；key 属于**别的
   kind**（kind 与 key 不匹配）。
4. `expect` 与现状不符（逐字段/逐参数键给出期望/实得）。
5. 同一 key 被重复操作（同一批内）。
6. 请求行尾与板主导行尾不一致（禁止引入与板多数行尾不同的行尾）。
7. zone 专属：`zone_net_declaration_unsupported`（net 声明不是 `(net "名称")`
   形态，例如 KiCad5 的 `(net 1)` + `(net_name GND)` —— net 号无法由名称
   派生）、`zone_outline_unsupported`（无 `(polygon (pts ...))` 结构）、
   `param_not_present`（要改的参数在目标 zone 里不存在 —— 本模块只做**值
   替换**，不插入/删除 zone 子表达式，理由见"zone op 语义"）。
8. 结构守卫失败：产出不可被 sexpr_min 解析 / 计数对账不平 / 以
   `copper_model.parse_copper` 重解析后目标操作未生效 / 目标节点事实与请求
   不符 / 无法实证字节保真。

zone op 语义（P3b 新增）
----------------------
* `modify` 允许的字段（其余一律 `invalid_field`）：
  - `net`：非空字符串；落到 `(net "名称")` 这一子表达式的**值 token** 上。
  - `layers`：≥1 个非空层名；落到 zone 的 `(layer "X")` / `(layers "X" "Y")`
    这一子表达式上（按长度重渲染该声明，其余字节不动）。
  - `outline_mm`：≥3 个 `[x, y]` 数值点；落到 `(polygon (pts ...))` 的
    **`(pts ...)` 子表达式**上，布局（缩进/括号换行/一行内平铺 `xy`）从原
    `(pts ...)` 克隆 —— 点数不变时该子表达式逐字节同构。
  - `params`：dict，键取"可编辑参数集"（见下），逐个落到对应子表达式的
    **值 token** 上。
* `add` 必须给全 `net` / `layers` / `outline_mm`；`params` 可选。
  **不得自造填充**：新增节点**不含任何 `(filled_polygon ...)`** —— 新 zone
  的填充缺失是**合法状态**（下游按 `fill_state` 处理；KiCad 下次编辑/重填
  时补齐），但本模块必须在 ledger 的 `zone_fill` 里显式记
  `fill_present=false` / `fill_state="unknown"` / `refill_required=true`，
  绝不静默。新增节点的结构由本模块按固定模板渲染（缩进/括号风格从板内同类
  锚点克隆），模板只含契约字段：net / layer / uuid / hatch? / connect_pads?
  / min_thickness? / fill / polygon —— 模板之外的 zone 子表达式
  （`(name ...)`/`(locked)`/`(property ...)`/`(attr ...)` 等）**有意**不生成，
  交回 KiCad 补全。
* `delete`：摘整行含前导缩进与行尾（与 segment/via 同口径；zone 是多行节点，
  该"行"覆蓋首行前导缩进到末行行尾的**整个节点字节 + 尾行行尾**）。

可编辑 zone 参数集（`params` 的键空间）
-------------------------------------
键名沿用 `copper_model._zone_params` 的词表（**expect 可原样抄自
copper_model**），另收 3 个直觉别名（映射到同一条目）：

| 本模块键（含别名） | 别名 → copper_model 键 | 落点 | 取值 |
|---|---|---|---|
| `clearance` | — | `(connect_pads (clearance V))` | 正有限数 |
| `min_thickness` | — | `(min_thickness V)`（zone 级） | 正有限数 |
| `fill_thermal_gap` | `thermal_gap` | `(fill (thermal_gap V))` | 正有限数 |
| `fill_thermal_bridge_width` | `thermal_bridge_width` | `(fill (thermal_bridge_width V))` | 正有限数 |
| `fill_island_removal_mode` | `island_removal_mode` | `(fill (island_removal_mode N))` | 枚举 {0,1,2} |
| `fill` | — | `(fill yes|no ...)` 的**首 token** | 枚举 {yes,no} |
| `connect_pads_mode` | — | `(connect_pads MODE ...)` 的**首 token** | 枚举 {yes,no,thru_hole_only,full} |
| `hatch` | — | `(hatch TOKENS)` 整个子表达式 | 1..2 个无括号/引号 token |

其余 copper_model 能解析出的参数（`priority`、`smoothing_max_error`、
`fill_arc_segments`、`fill_min_thickness`、`fill_clearance` …）本阶段**不可
编辑**（`invalid_field`）—— 它们不影响本模块的过期判定，且没有实测需求；
加入它们只扩大写面，不增加能力。

**只做值替换，不做子表达式插入/删除**：要改的参数在目标 zone 里不存在 ⇒
`param_not_present`（blocked）。理由：插入需要自造位置与相邻风格，会引入
"本模块发明板文本结构"的风险；缺失即 fail-closed 让人显式先补齐骨架。

填充过期语义（关键；判据写死在 `_zone_fill_verdict`，:file-line 见 docstring）
--------------------------------------------------------------------------
**判据（本模块口径）**：一次 zone `modify` 让既有填充"过期"，当且仅当被改
字段/参数**参与 KiCad 的 zone 填充几何计算**。参与集合 = `net`、`layers`、
`outline_mm`，以及参数 `clearance`、`min_thickness`、`fill_thermal_gap`、
`fill_thermal_bridge_width`、`fill_island_removal_mode`、`fill`、
`connect_pads_mode`（`_ZONE_STALE_FIELDS` / `_ZONE_STALE_PARAMS`）。

* `net`/`layers`/`outline_mm` 改了就过期：填充是对**轮廓**裁剪、对**本层**
  求值、对其他 net 保持 `clearance` 并给同 net 焊盘生成热焊盘的结果。
* 参数：`clearance`/`min_thickness`/`thermal_gap`/`thermal_bridge_width`/
  `island_removal_mode`/`connect_pads_mode` **直接决定**填充的点位集合（间距
  让位、最小厚度剔除细颈、热焊盘辐条、孤岛剔除、焊盘连接方式），故**只改
  参数而不动轮廓/layers 同样算 stale** —— 这是任务书明确留给实现判定的那一
  条，本模块取**保守方向**（宁可要求重填证据，也不谎称 fresh）。
* 唯一**不**过期的可编辑参数是 `hatch`：它只决定 zone 轮廓线的显示填充样式
  （`(hatch edge|none|hatch ...)`），不进入 fill 几何计算；改它时既有
  `filled_polygon` 仍然有效。
* 处理方式：**保留填充字节不动**（`filled_polygon` 的字节跨度与任何编辑跨度
  不相交，且改后逐字节相同 —— ledger 的 `fill_bytes_preserved` +
  `fill_sha256_before/after` + `fill_points_before/after` 是实证）。
  ledger 与 revision 记录里如实标 `fill_state`：
  - `"stale"` —— 有过期（既有填充已失效，**不得谎称 fresh**）；
  - `"unknown"` —— 无填充（新增 zone）或未重新建立新鲜度（仅 `hatch` 改动）。
  本模块**从不**产出 `"fresh"`：fresh 需要填充指纹证据，那是编排侧重填后的
  事实，只有调用方（`svg_route_package._norm_zone` 口径）能声明。

**不得自研填充器（out of scope，写死）**
--------------------------------------
多边形布尔、热焊盘（thermal relief）生成、孤岛移除、`min_thickness` 的填充
几何、以及任何 `filled_polygon` 点位的计算/重排/裁剪 —— 一律**不在本模块
范围**，交回 KiCad（编排侧 `kicad-cli pcb drc --refill-zones` 或 KiCad GUI
重填）。本模块只做三件事：改契约字段的文本、如实标记填充状态、在采纳路径上
用 `fill_gate` 拦住"未记录重填证据"的轮次。

采纳门 `fill_gate(...)`（P3b）
----------------------------
    fill_gate(record, *, ledger=None, revision_dir=None,
              evidence=None, source_sha256=None) -> dict
    → {"schema", "ok": bool, "required": bool, "rule", "reason_code",
       "reasons": [str], "status_label": "ok"|"awaiting_refill",
       "not_fresh_zone_ids": [...], "fill_states": {zone_id: state},
       "zone_fill_summary": dict|None, "evidence": dict|None,
       "evidence_source": str|None, "refill_evidence_sha256": str|None,
       "expected_source_sha256": str|None}

纯函数（只有"读证据文件"这一处 IO，且只在 `revision_dir` 给出时发生）：
`required` 取自 `ledger["patch_ledger"]["zone_fill_summary"]["refill_required"]`
（等价于"本轮 zone op 触及的 zone 中有 stale 或无填充者"）。`required=False`
⇒ 直接 `ok=True`（**未触及 zone 的轮次一律放行**：未触及 zone 的填充新鲜度是
基准板自身的事实，不由本补丁改变，也不在本门的判据内）。

`required=True` 时要求 `refill_evidence`（形状
`pcbflow.copper-refill-evidence/1`）：

    {"schema": "pcbflow.copper-refill-evidence/1",
     "refill_performed": true,
     "source_board_sha256": "<64hex，被重填的板 = 本轮 staging 板>",
     "refilled_board_sha256": "<64hex，重填后板>",
     "kicad_version": "<非空串>",
     "steps": [{"step": "kicad-cli pcb drc --refill-zones ...",
                "exit_code": 0}, ...]}

证据来源（按序）：显式 `evidence=` 参数 → `record["refill_evidence"]`（内联）
→ `<revision_dir>/drc/refill-evidence.json` → `<revision_dir>/refill-evidence.json`。
缺证据 ⇒ `reason_code="refill_evidence_missing"`（`reasons[0]` 以该串开头，
列出待重填 zone 与期望路径）；证据存在但不合法 ⇒ `refill_evidence_invalid` /
`refill_evidence_schema_mismatch` / `refill_evidence_unparseable`；证据的
`source_board_sha256` 与本轮 staging sha 不符 ⇒ `refill_evidence_stale`
（防拿别的轮次/过期证据过关）。**全部 reason 收集，不只第一条。**

`fill_gate` 的调用方（`copper_loop.accept_revision` / `adopt`）必须走
`_refuse`（拒绝**尝试**，不改轮次状态）：轮次保持 `awaiting_drc`，补齐
`drc/refill-evidence.json` 后可重试；`status_label="awaiting_refill"` 是这次
尝试的判定标签，**不是**轮次被写死成 blocked。

行尾与缩进保真
--------------
* `eol=None` 或 `"auto"` → `dominant_eol(board_text)`（**不是**默认 LF）；
  显式 "\\n"/"\\r\\n" 仅在等于板主导行尾（或板内完全无换行）时被接受，
  否则 blocked。未知 eol 取值抛 ValueError（与 board_writer
  同口径）。调用方读板必须 `open(..., newline="")`，否则 CRLF 已被通用换行
  翻译归一成 LF，任何 CRLF 板都会被误判（同 dominant_eol 的调用方注意）。
* 新增节点从**邻近同类节点文本**克隆前导 `\\t` 层级、子字段缩进与括号换行
  风格（多行节点 → 多行；单行/紧凑节点 → 单行），不凭空发明缩进。
* 只动目标节点自身的字节：`modify` 只替换节点自身跨度（前导缩进与行尾原样
  保留）；`delete` 摘除"该节点所在行"（前导缩进 + 节点字节 + 行尾），避免
  留下只含空白的残行；`add` 只插入"一行"。
* zone `modify` 更细：只替换**被改字段对应子表达式的字节**（net 的值 token /
  layer 声明 / `(pts ...)` / 参数值 token），节点内其余字节（尤其是
  `filled_polygon`）逐字节不动 —— 见上"填充过期语义"。`hatch` 是例外，整
  个子表达式被重渲染（它是紧凑单行表达式）。

`unchanged_bytes_outside_targets`（实证，非声明）
-------------------------------------------------
把**目标跨度摘除**后比较两侧文本是否逐字相同：
  原文摘除 {modify 的旧节点跨度, delete 的整行跨度}  ⇔
  新文本摘除 {modify 的新节点跨度, add 的插入跨度}
两串逐字节相等 → True。目标跨度定义：modify = 节点自身字节；delete = 该节点
整行（前导缩进 + 节点字节 + 行尾）；add = 插入的整行（缩进 + 节点字节 + 行尾）。

uuid 语义（**不要复用 board_writer.route_uuid 的路由级口径**）
-------------------------------------------------------------
`add` 生成的新节点必须写**对象级唯一** uuid：确定性派生（自身事实的
sha256 + 批内重复序号 + 与板上既有 uuid 的规避重试，无随机），**每个对象
一个**，绝不让一条 route 的多个节点共用同一 uuid。Rev-C 现状里 segment/via
共用 route 级 uuid 正是"uuid 共享"的根因（copper_model 的 v2 key 规则靠
`<uuid>@<digest>` 消歧兜底），补丁引擎不得把该缺陷再生产到新节点上。
`modify` **保留**原节点 uuid（`new` 不接受 uuid 字段：新节点的 uuid 只能是
本模块派生值，modify 只能沿用它本来的 uuid；目标节点原本无 uuid 时不凭空
发明，只是其身份键随几何摘要变化——ledger 的 `affected_keys.old_key/new_key`
如实登记）。
注意：按 copper_model 冻结的 v2 key 规则，改动/删除**共享 uuid**的节点会让
同 uuid 兄弟节点的 key 从 `uuid` 变为 `uuid@<digest>`（或反向）——这是 key
规则的既有后果而非本引擎行为，ledger 的 `uuid_multiplicity_changes` 如实登记。

ledger 字段
-----------
ops_total / ops_applied / adds / modifies / deletes / ops_requested /
affected_keys（modify 含 old_key → new_key）/ counts_before / counts_after /
eol / unchanged_bytes_outside_targets / structural_guard / op_spans（每 op 的
原文目标跨度与原/新节点跨度，供复核与测试）/ uuid_multiplicity_changes /
unrepresentable_before / unrepresentable_after / blocked_ops。blocked 时
board_text 为 None，未落实的计数与守卫字段为 None/0、列表为空。
`structural_guard` = {ok, checks, sexpr_parse, counts_ok, counts_delta,
counts_expected_delta, targets_ok, target_details}。

P3b 新增（填充与采纳门）：

* `zone_fill`：逐 zone op 的填充记账（add/modify 各一条）——
  `{index, op, zone_key, zone_id, fill_state, fill_present, fill_invalidated,
  refill_required, fill_reason, stale_fields, stale_params,
  fill_points_before/after, fill_sha256_before/after, fill_bytes_preserved,
  fill_spans_after}`。`fill_bytes_preserved` 是**实证**：编辑跨度与
  `filled_polygon` 跨度不相交，且改后对应子串逐字节相同。
* `zone_fill_summary`：
  `{zones_touched, refill_required, not_fresh_zone_ids, stale_zone_ids,
  absent_fill_zone_ids, fill_states, rule, fill_state_is_patch_derived, note}`。
  这是 `fill_gate` 的唯一输入（`fill_gate` 只读它，不猜）。

**本模块从不产出 `fill_state="fresh"`**（见上）；`not_fresh_zone_ids` 是
"补丁后填充非 fresh 的受影响 zone"，`refill_required` = 该集合非空。
"""

from __future__ import annotations

import bisect
import json
import os
import re

from . import copper_model, hashing, sexpr_min
from .board_writer import dominant_eol

__all__ = ["OP_TYPES", "OP_KINDS", "ZONE_BLOCKED_REASON", "apply_patch",
           "fill_gate", "validate_refill_evidence",
           "REFILL_EVIDENCE_SCHEMA", "REFILL_EVIDENCE_REL",
           "REFILL_GATE_RULE", "REASON_REFILL_EVIDENCE_MISSING",
           "ZONE_STALE_FIELDS", "ZONE_STALE_PARAMS", "ZONE_PARAM_KEYS",
           "ZONE_FILL_STATES_PATCH"]

OP_TYPES = ("add", "modify", "delete")
OP_KINDS = ("segment", "via", "zone")

#: **R3 起不再产生**（保留常量以免破坏既有导入）：R2 之前 zone 的
#: add/modify/delete 一律以此裸码 blocked；P3b 起 zone 写操作已实现，
#: 该 reason 只作为历史事实留在旧台账里。
ZONE_BLOCKED_REASON = "zone_ops_pending_contract_v2"

#: 采纳门（未重填不得采纳）——见模块 docstring
REFILL_EVIDENCE_SCHEMA = "pcbflow.copper-refill-evidence/1"
REFILL_EVIDENCE_REL = "drc/refill-evidence.json"
REFILL_EVIDENCE_ALT_REL = "refill-evidence.json"
REFILL_GATE_RULE = "zone_fill_stale_requires_refill_evidence"
REASON_REFILL_EVIDENCE_MISSING = "refill_evidence_missing"
FILL_GATE_SCHEMA = "pcbflow.copper-fill-gate/1"
ZONE_FILL_SUMMARY_RULE = "refill_required_iff_touched_zone_fill_not_fresh"

#: 本模块能给出的 zone fill_state 取值（`svg_route_package.ZONE_FILL_STATES`
#: 的子集：本模块**从不**声称 "fresh"）。
ZONE_FILL_STATES_PATCH = ("stale", "unknown")

_LF = "\n"
_CRLF = "\r\n"
_EOL_EXPLICIT = (_LF, _CRLF)
_EOL_AUTO = "auto"

_GEO_Q = 6   # 坐标量化位数（与 copper_model 同口径）
_DIM_Q = 3   # 宽度/尺寸/钻孔量化位数

#: 新节点 uuid 派生命名空间（与 board_writer.route_uuid 的 "pcbflow-fc2:" 分离）
_UUID_NS = "pcbflow.copper-patch/1"

_VIA_KINDS = ("through", "blind", "buried")
_OUTER_LAYERS = ("F.Cu", "B.Cu")

#: add 的必需字段（亦决定 uuid 派生输入；与 copper_model 解析字段同类）
_NEW_REQUIRED = {
    "segment": ("net", "layer", "width", "start", "end"),
    "via": ("net", "at", "size", "drill", "layers"),
    "zone": ("net", "layers", "outline_mm"),
}
#: expect 契约字段集
_EXPECT_FIELDS = {
    "segment": ("net", "layer", "width", "start", "end"),
    "via": ("net", "at", "size", "drill", "layers"),
    "zone": ("net", "layers", "outline_mm", "params"),
}
#: 契约字段集之外的显式可选字段（其余一律 invalid_field）。
#: expect 允许断言 uuid；new **不允许** uuid —— 新节点的 uuid 一律由本模块按
#: 对象级口径派生（见 `_derive_object_uuid`），避免调用方把"uuid 共享"这一
#: Rev-C 缺陷再写回板。via 的 new 允许显式给 via_kind（否则按层/原 token 推断）；
#: zone 的 new 允许给 params（可编辑参数子集，见模块 docstring）。
_OPTIONAL_FIELDS = {
    "expect": {"segment": ("uuid",), "via": ("uuid", "via_kind"),
               "zone": ("uuid",)},
    "new": {"segment": (), "via": ("via_kind",), "zone": ("params",)},
}

# --------------------------------------------------------- zone 字段/参数表
#: zone 的"参与填充几何计算"字段：改之 ⇒ 既有 filled_polygon 过期
ZONE_STALE_FIELDS = frozenset(("net", "layers", "outline_mm"))

#: 可编辑 zone 参数：copper_model `_zone_params` 键 → 落点路径
#: （路径元素是 zone 节点的直接/间接子表达式名；见模块 docstring 的表）
_ZONE_PARAM_PATH = {
    "clearance": ("connect_pads", "clearance"),
    "min_thickness": ("min_thickness",),
    "fill_thermal_gap": ("fill", "thermal_gap"),
    "fill_thermal_bridge_width": ("fill", "thermal_bridge_width"),
    "fill_island_removal_mode": ("fill", "island_removal_mode"),
    "fill": ("fill",),                       # 首 token
    "connect_pads_mode": ("connect_pads",),  # 首 token
    "hatch": ("hatch",),                     # 整个子表达式（token 列表）
}
#: 直觉别名 → copper_model 键（两套拼写都接受，内部一律归一到后者）
ZONE_PARAM_ALIASES = {
    "thermal_gap": "fill_thermal_gap",
    "thermal_bridge_width": "fill_thermal_bridge_width",
    "island_removal_mode": "fill_island_removal_mode",
}
#: 可编辑参数键全集（copper_model 词表）
ZONE_PARAM_KEYS = frozenset(_ZONE_PARAM_PATH)
#: 正有限数参数
_ZONE_PARAM_NUM_POS = frozenset(("clearance", "min_thickness",
                                 "fill_thermal_gap",
                                 "fill_thermal_bridge_width"))
#: 整数枚举参数
_ZONE_PARAM_ENUM_INT = {"fill_island_removal_mode": (0, 1, 2)}
#: 字符串枚举参数（落点是首 token 或整表达式）
_ZONE_PARAM_ENUM_STR = {"fill": ("yes", "no"),
                        "connect_pads_mode": ("yes", "no", "thru_hole_only",
                                              "full")}
#: token 串参数
_ZONE_PARAM_TOKENS = frozenset(("hatch",))
#: 改之 ⇒ 填充过期的参数（除 `hatch` 外的全部可编辑参数）
ZONE_STALE_PARAMS = frozenset(("clearance", "min_thickness", "fill_thermal_gap",
                               "fill_thermal_bridge_width",
                               "fill_island_removal_mode", "fill",
                               "connect_pads_mode"))

#: `hatch` 的 token 形状（1..2 个不含空白/括号/引号的 token）
_HATCH_RE = re.compile(r'^[^\s()"]+(?: [^\s()"]+)?$')
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

#: kind → copper_model counts 的复数键
_COUNT_KEY = {"segment": "segments", "via": "vias", "zone": "zones"}

_XY_FIELDS = frozenset(("start", "end", "at"))
_NUM_FIELDS = frozenset(("width", "size", "drill"))
_STR_FIELDS = frozenset(("net", "layer", "uuid", "via_kind"))

_EOL_RE = re.compile(r"\r\n|\n|\r")
_WS = " \t"
_INF = float("inf")


class _RenderError(Exception):
    """内部渲染/自校验失败 → 结构守卫级 blocked。"""


# --------------------------------------------------------------- 基础工具

def _q(v, nd: int) -> float:
    return round(float(v), nd)


def _canonical(obj) -> str:
    """canonical json（sort_keys + 紧凑分隔符；与 copper_model 同口径）。

    形态登记=exec/CANONICAL-JSON-FORM-MAP-2026-09-25.md「铜族（紧凑）」。
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _sha(obj) -> str:
    return hashing.sha256_text(_canonical(obj))


def _esc(s: str) -> str:
    """s-expr 双引号串转义（反斜杠优先，再转义引号）。"""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _fnum(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if not isinstance(v, str):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _fmt_num(v) -> str:
    """数值 → 最短往返十进制串（确定性）。

    取"能精确还原该 float 的最短定点表示"（0..6 位小数、去尾零），故
    0.2→"0.2"、0.1979→"0.1979"、21.925→"21.925"、66.1118→"66.1118"：
    copper_model 解析出的值再写回时逐字节不变（%.4f 会静默改精度）。
    6 位仍不能精确还原时止于 6 位（与坐标量化口径一致）。
    """
    f = float(v)
    neg = f < 0
    a = abs(f)
    chosen = None
    for nd in range(0, _GEO_Q + 1):
        s = "%.*f" % (nd, a)
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        if s == "":
            s = "0"
        if float(s) == a:
            chosen = s
            break
    if chosen is None:
        chosen = "%.*f" % (_GEO_Q, a)
        if "." in chosen:
            chosen = chosen.rstrip("0").rstrip(".")
        chosen = chosen or "0"
    return ("-" if neg else "") + chosen


def _fmt_xy(p) -> str:
    return "%s %s" % (_fmt_num(p[0]), _fmt_num(p[1]))


def _split_eol_at(text: str, pos: int) -> str:
    """text[pos:] 起始处的行尾串（"\\r\\n" 优先；无则 ""）。"""
    if text.startswith("\r\n", pos):
        return "\r\n"
    if text.startswith("\n", pos):
        return "\n"
    if text.startswith("\r", pos):
        return "\r"
    return ""


def _lead_ws(text: str, pos: int) -> str:
    """pos 之前紧邻的空格/制表符 run（不跨行尾）。"""
    i = pos
    while i > 0 and text[i - 1] in _WS:
        i -= 1
    return text[i:pos]


def _indent_after(text: str, pos: int) -> str:
    i = pos
    while i < len(text) and text[i] in _WS:
        i += 1
    return text[pos:i]


def _balanced(text: str) -> bool:
    """括号/双引号平衡检查（与 copper_model 同口径）。"""
    depth = 0
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
            else:
                return False
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def _child(node, name):
    if not isinstance(node, list):
        return None
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def _leaf(node, tag=None, index: int = 1):
    if node is None:
        return None
    if tag is not None:
        node = _child(node, tag)
    if not isinstance(node, list) or len(node) <= index:
        return None
    v = node[index]
    return v if isinstance(v, str) else None


def _xy(node):
    """(start/end/at x y) → [x, y]；非法返回 None。"""
    if not isinstance(node, list) or len(node) < 3:
        return None
    x, y = _fnum(node[1]), _fnum(node[2])
    if x is None or y is None:
        return None
    return [x, y]


def _layers_of(node) -> list:
    """节点直接子层声明（layer/layers，保序）。"""
    out = []
    if not isinstance(node, list):
        return out
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] in ("layer", "layers"):
            for v in c[1:]:
                if isinstance(v, str) and v:
                    out.append(v)
    return out


def _via_kind(token, layers):
    """via 类型：显式 token 优先，否则按层位置推断。

    本函数是 `copper_model._via_kind`（冻结取值 {through,blind,buried}）的
    局部镜像 —— copper_model 未导出该 helper，而本模块不得改动对方文件。
    镜像等价性由测试对真实板逐 via 钉死。
    """
    if token in _VIA_KINDS:
        return token
    if not layers:
        return None
    outer = [l for l in layers if l in _OUTER_LAYERS]
    if len(layers) >= 2 and len(outer) == len(layers):
        return "through"
    if len(outer) == 1:
        return "blind"
    return "buried"


# ------------------------------------------------------------ 行尾决议

def _resolve_eol(board_text: str, eol):
    """→ (node_eol, reason|None)；未知取值抛 ValueError（board_writer 同口径）。"""
    dom = dominant_eol(board_text)
    if eol is None or eol == _EOL_AUTO:
        return dom, None
    if eol not in _EOL_EXPLICIT:
        raise ValueError('未知 eol=%r（允许 None / "auto" / "\\n" / "\\r\\n"）'
                         % (eol,))
    has_eol = ("\n" in board_text) or ("\r" in board_text)
    if has_eol and eol != dom:
        return eol, ("eol_mismatch: 请求 eol=%r 与板主导行尾 %r 不一致；"
                     "禁止引入与板占多数行尾不同的行尾（不传 eol 即按板主导）"
                     % (eol, dom))
    return eol, None


# ------------------------------------------------------------ 节点事实

def _raw_facts(kind: str, node_text: str):
    """节点自身字节 → (facts, None) 或 (None, reason)。

    facts 保留**原始精度**（不做 copper_model 量化），故未改字段可逐字节写回；
    via 额外带 `raw_token`（节点里出现的显式类型 token，可为 None）；
    zone 由 `_zone_facts`（自带字节跨度）给出，实现见"zone 事实与字节拼接"节。
    """
    if kind == "zone":
        return _zone_facts(node_text)
    if not _balanced(node_text):
        return None, "节点括号/双引号不平衡"
    try:
        parsed = sexpr_min.parse(node_text)
    except sexpr_min.SexprError as exc:
        return None, "s-expr 解析失败: %s" % (exc,)
    if len(parsed) != 1 or not isinstance(parsed[0], list) or not parsed[0]:
        return None, "节点形状非法（非单一列表）"
    node = parsed[0]
    uuid = _leaf(node, "uuid", 1)
    uuid = uuid if isinstance(uuid, str) and uuid else None
    if kind == "segment":
        start = _xy(_child(node, "start"))
        end = _xy(_child(node, "end"))
        width = _fnum(_leaf(node, "width", 1))
        layer = _leaf(node, "layer", 1)
        net = _leaf(node, "net", 1)
        bad = []
        if start is None:
            bad.append("start")
        if end is None:
            bad.append("end")
        if width is None or not width > 0:
            bad.append("width")
        if not isinstance(layer, str) or not layer:
            bad.append("layer")
        if not isinstance(net, str) or not net:
            bad.append("net")
        if bad:
            return None, "缺/非法字段: " + ",".join(bad)
        return {"uuid": uuid, "net": net, "layer": layer, "width": width,
                "start": start, "end": end}, None
    at = _xy(_child(node, "at"))
    size = _fnum(_leaf(node, "size", 1))
    drill = _fnum(_leaf(node, "drill", 1))
    net = _leaf(node, "net", 1)
    layers = _layers_of(node)[:2]
    bad = []
    if at is None:
        bad.append("at")
    if size is None or not size > 0:
        bad.append("size")
    if drill is None or not drill > 0:
        bad.append("drill")
    if len(layers) < 2:
        bad.append("layers")
    if not isinstance(net, str) or not net:
        bad.append("net")
    if bad:
        return None, "缺/非法字段: " + ",".join(bad)
    token = node[1] if len(node) > 1 and isinstance(node[1], str) else None
    kind_token = _via_kind(token, layers)
    if kind_token is None:
        return None, "via_kind 无法判定: layers=%s" % (layers,)
    return {"uuid": uuid, "net": net, "at": at, "size": size, "drill": drill,
            "layers": list(layers), "via_kind": kind_token,
            "raw_token": token}, None


# ------------------------------------------------------------ 字段校验

def _validate_field(kind: str, field: str, value, where: str) -> list:
    """单字段类型/枚举校验 → reason 列表（[] = 合法）。"""
    tag = "%s.%s" % (where, field)
    if field in _XY_FIELDS:
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return ["invalid_field: %s 期望 [x, y]（实得 %r）" % (tag, value)]
        for c in value:
            if isinstance(c, bool) or not isinstance(c, (int, float)):
                return ["invalid_field: %s 坐标须为数值（实得 %r）" % (tag, c)]
            f = _fnum(c)
            if f is None or f == _INF or f == -_INF:
                return ["invalid_field: %s 坐标非有限（实得 %r）" % (tag, c)]
        return []
    if field in _NUM_FIELDS:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ["invalid_field: %s 期望数值（实得 %r）" % (tag, value)]
        f = float(value)
        if not (f > 0) or f == _INF:
            return ["invalid_field: %s 须为正有限数（实得 %r）" % (tag, value)]
        return []
    if field == "outline_mm":
        # zone 轮廓：≥3 个数值点对（copper_model `_parse_zone` 同口径）
        if not isinstance(value, (list, tuple)) or len(value) < 3:
            return ["invalid_field: %s 期望 ≥3 个 [x, y] 点（实得 %r）"
                    % (tag, value)]
        out = []
        for i, p in enumerate(value):
            out.extend(_validate_field(kind, "outline_pt", p,
                                       "%s[%d]" % (where, i)))
        return out
    if field == "outline_pt":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return ["invalid_field: %s 期望 [x, y]（实得 %r）" % (tag, value)]
        for c in value:
            if isinstance(c, bool) or not isinstance(c, (int, float)):
                return ["invalid_field: %s 坐标须为数值（实得 %r）" % (tag, c)]
            f = _fnum(c)
            if f is None or f == _INF or f == -_INF:
                return ["invalid_field: %s 坐标非有限（实得 %r）" % (tag, c)]
        return []
    if field == "params":
        return _validate_zone_params(value, where)
    if field == "layers":
        # zone 允许 1 层（`(layer "B.Cu")`）；segment/via 的 layers 是跨层钻孔，
        # 少于 2 层无意义（既有口径不变）
        min_len = 1 if kind == "zone" else 2
        if not isinstance(value, (list, tuple)) or len(value) < min_len:
            return ["invalid_field: %s 期望 ≥%d 个层名（实得 %r）"
                    % (tag, min_len, value)]
        out = []
        for l in value:
            out.extend(_validate_field(kind, "layer", l, where))
        return out
    if field == "via_kind":
        if value not in _VIA_KINDS:
            return ["invalid_field: %s 枚举非法 %r（允许 %s）"
                    % (tag, value, list(_VIA_KINDS))]
        return []
    if field in _STR_FIELDS:
        if not isinstance(value, str) or value == "":
            return ["invalid_field: %s 期望非空字符串（实得 %r）" % (tag, value)]
        if "\n" in value or "\r" in value:
            return ["invalid_field: %s 含换行字符" % tag]
        return []
    return ["invalid_field: %s 未知字段 %r" % (where, field)]


def _norm_param_key(key: str) -> str:
    """参数键归一（别名 → copper_model 词表；未知键原样返回）。"""
    return ZONE_PARAM_ALIASES.get(key, key)


def _norm_params(value) -> dict:
    """params dict → 归一后的 dict（键为 copper_model `_zone_params` 词表）。"""
    return {_norm_param_key(k): v for k, v in value.items()}


def _validate_zone_params(value, where: str) -> list:
    """zone params 静态校验（键在可编辑集内 + 取值合法，收集全部失败）。"""
    tag = "%s.params" % where
    if not isinstance(value, dict):
        return ["invalid_field: %s 期望 dict（实得 %r）" % (tag, value)]
    out = []
    for key, v in value.items():
        k = _norm_param_key(key)
        if k not in ZONE_PARAM_KEYS:
            out.append("invalid_field: %s 不可编辑的参数 %r（允许 %s）"
                       % (tag, key, sorted(ZONE_PARAM_KEYS)))
            continue
        sub = "%s.%s" % (tag, k)
        if k in _ZONE_PARAM_NUM_POS:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                out.append("invalid_field: %s 期望数值（实得 %r）" % (sub, v))
            elif not (float(v) > 0) or float(v) == _INF:
                out.append("invalid_field: %s 须为正有限数（实得 %r）"
                           % (sub, v))
        elif k in _ZONE_PARAM_ENUM_INT:
            allowed = _ZONE_PARAM_ENUM_INT[k]
            if isinstance(v, bool) or not isinstance(v, int) or v not in allowed:
                out.append("invalid_field: %s 枚举非法 %r（允许 %s）"
                           % (sub, v, list(allowed)))
        elif k in _ZONE_PARAM_ENUM_STR:
            allowed = _ZONE_PARAM_ENUM_STR[k]
            if v not in allowed:
                out.append("invalid_field: %s 枚举非法 %r（允许 %s）"
                           % (sub, v, list(allowed)))
        elif k in _ZONE_PARAM_TOKENS:
            if not isinstance(v, str) or not _HATCH_RE.match(v):
                out.append("invalid_field: %s 期望 1..2 个 token 的串"
                           "（实得 %r）" % (sub, v))
    return out


def _allowed_fields(kind: str, which: str) -> tuple:
    base = _EXPECT_FIELDS[kind] if which == "expect" else _NEW_REQUIRED[kind]
    return tuple(base) + tuple(_OPTIONAL_FIELDS[which][kind])


def _validate_fields(kind: str, obj, which: str) -> list:
    out = []
    for field, value in obj.items():
        if field not in _allowed_fields(kind, which):
            out.append("invalid_field: %s 未知字段 %r" % (which, field))
            continue
        out.extend(_validate_field(kind, field, value, which))
    return out


# ------------------------------------------------------------ expect 比对

def _params_quantized(value) -> dict:
    """params dict → 可比较的 canonical 投影（键归一 + 数值 3 位量化）。"""
    out = {}
    for key, v in (value or {}).items():
        k = _norm_param_key(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            out[k] = v
        else:
            f = float(v)
            out[k] = int(f) if f.is_integer() else _q(f, _DIM_Q)
    return out


def _zone_param_diffs(want, have, *, require_all: bool) -> list:
    """逐个参数键比较 → 差异描述列表（以 `want` 侧的键为准）。

    `require_all=True`（expect 口径）：`want` 的键在 `have` 里缺失即算不符。
    `require_all=False`（渲染往返口径）：缺键不算差异。
    """
    w, h = _params_quantized(want), _params_quantized(have)
    bad = []
    for k, v in w.items():
        if k not in h:
            if require_all:
                bad.append("%s(缺)" % k)
            continue
        if h[k] != v:
            bad.append("%s %r≠%r" % (k, v, h[k]))
    return bad


def _quantize(kind: str, field: str, value):
    if field == "outline_pt":
        return [_q(value[0], _GEO_Q), _q(value[1], _GEO_Q)]
    if field == "outline_mm":
        return [[_q(p[0], _GEO_Q), _q(p[1], _GEO_Q)] for p in value]
    if field in _XY_FIELDS:
        return [_q(value[0], _GEO_Q), _q(value[1], _GEO_Q)]
    if field in _NUM_FIELDS:
        return _q(value, _DIM_Q)
    if field == "layers":
        return list(value)
    if field == "params":
        return _params_quantized(value)
    return value


def _check_expect(kind: str, facts: dict, expect: dict) -> list:
    """逐字段断言 → expect_mismatch reason 列表。

    zone 的 `params` 是**逐键子集**语义（未给出的键不参与），其余字段是整值
    语义 —— 见模块 docstring 的 op 形状说明。
    """
    out = []
    for field, want in expect.items():
        if field not in _allowed_fields(kind, "expect"):
            continue          # 未知字段已在静态校验里报过
        if field == "params":
            have = facts.get("params") or {}
            for diff in _zone_param_diffs(want, have, require_all=True):
                out.append("expect_mismatch: params.%s" % diff)
            continue
        have = facts.get(field)
        if _quantize(kind, field, want) != _quantize(kind, field, have):
            out.append("expect_mismatch: %s 期望 %r 实得 %r" % (field, want, have))
    return out


# ------------------------------------------------------------ 样式克隆/渲染

def _style_from_node_text(node_text: str, node_eol: str) -> dict:
    """同类节点文本 → 渲染样式（前导缩进由调用方另给）。"""
    first = _EOL_RE.search(node_text)
    if first is None:
        # 单行/紧凑写法：克隆"同一行内平铺"的括号风格
        return {"inline": True, "lead": "\t", "child": "\t\t", "closer": "\t",
                "eol": node_eol}
    child = _indent_after(node_text, first.end())
    last = None
    for last in _EOL_RE.finditer(node_text):
        pass
    closer = _indent_after(node_text, last.end())
    return {"inline": False, "lead": "\t", "child": child, "closer": closer,
            "eol": node_eol}


def _render_expr(head: str, exprs: list, style: dict) -> str:
    """head + 子表达式列表 → 节点/子表达式字节（布局由 style 决定）。

    `style["inline"]` 为真 → 单行平铺；否则首行放 head，子表达式逐行（缩进
    `style["child"]`），闭括号缩进 `style["closer"]`。segment/via/zone 三类
    节点与 zone 的子表达式（polygon/pts）共用同一渲染口径。
    """
    if style["inline"]:
        return "(" + head + (" " + " ".join(exprs) if exprs else "") + ")"
    eol, child, closer = style["eol"], style["child"], style["closer"]
    out = ["(", head, eol]
    for ex in exprs:
        out.append(child + ex + eol)
    out.append(closer + ")")
    return "".join(out)


def _render_node(kind: str, facts: dict, style: dict) -> str:
    """facts → 节点自身字节（以 "(" 起、以 ")" 止；不含前导缩进与尾部行尾）。

    uuid 为 None（modify 的目标节点原本就没有 uuid）时不写 (uuid ...) 字段，
    即**不凭空发明**身份；add 的 facts 必带派生 uuid（见 apply_patch）。
    zone 走独立模板 `_render_zone_node`（**不含任何 filled_polygon**）。
    """
    if kind == "zone":
        return _render_zone_node(facts, style)
    uuid = facts["uuid"]
    uuid_expr = ['(uuid "%s")' % _esc(uuid)] if uuid else []
    if kind == "segment":
        head = "segment"
        exprs = [
            "(start %s)" % _fmt_xy(facts["start"]),
            "(end %s)" % _fmt_xy(facts["end"]),
            "(width %s)" % _fmt_num(facts["width"]),
            '(layer "%s")' % _esc(facts["layer"]),
            '(net "%s")' % _esc(facts["net"]),
        ] + uuid_expr
    else:
        head = "via %s" % facts["via_kind"]
        exprs = [
            "(at %s)" % _fmt_xy(facts["at"]),
            "(size %s)" % _fmt_num(facts["size"]),
            "(drill %s)" % _fmt_num(facts["drill"]),
            "(layers %s)" % " ".join('"%s"' % _esc(l)
                                     for l in facts["layers"]),
            '(net "%s")' % _esc(facts["net"]),
        ] + uuid_expr
    return _render_expr(head, exprs, style)


#: 渲染往返自校验的字段（zone 追加 params —— 参数也必须是"写下去就解析得回来"）
_ROUNDTRIP_FIELDS = {
    "segment": _NEW_REQUIRED["segment"],
    "via": _NEW_REQUIRED["via"],
    "zone": _NEW_REQUIRED["zone"] + ("params",),
}


def _node_to_text(kind: str, facts: dict, style: dict) -> str:
    """渲染 + 往返自校验（渲染后必须能被本模块重新解析出同样的量化事实）。"""
    text = _render_node(kind, facts, style)
    back, reason = _raw_facts(kind, text)
    if back is None:
        raise _RenderError("渲染节点不可解析: %s" % reason)
    for field in _ROUNDTRIP_FIELDS[kind]:
        have = (back.get("params") or {}) if field == "params" else back[field]
        want = (facts.get("params") or {}) if field == "params" else \
            facts[field]
        if field == "params":
            bad = _zone_param_diffs(want, have, require_all=False)
            if bad:
                raise _RenderError("渲染往返不一致: params %s" % bad)
            continue
        if _quantize(kind, field, have) != _quantize(kind, field, want):
            raise _RenderError("渲染往返不一致: %s %r -> %r"
                               % (field, facts[field], back[field]))
    return text


# ------------------------------------------------------------ uuid 派生

def _uuid_payload(kind: str, facts: dict) -> dict:
    """uuid 派生输入：对象自身事实（不含 uuid 自身）。"""
    payload = {"ns": _UUID_NS, "kind": kind}
    for field in _NEW_REQUIRED[kind]:
        v = facts[field]
        if field in _XY_FIELDS:
            v = [_q(v[0], _GEO_Q), _q(v[1], _GEO_Q)]
        elif field in _NUM_FIELDS:
            v = _q(v, _DIM_Q)
        elif field == "outline_mm":
            v = [[_q(p[0], _GEO_Q), _q(p[1], _GEO_Q)] for p in v]
        elif field == "layers":
            v = list(v)
        payload[field] = v
    if kind == "via":
        payload["via_kind"] = facts["via_kind"]
    return payload


def _derive_object_uuid(kind: str, facts: dict, dup_index: int,
                        taken: set) -> str:
    """对象级唯一 uuid：自身事实 + 批内重复序号 sha256 派生（确定性、无随机）。

    与 `board_writer.route_uuid` 的关键差别：那条口径把**一条 route 的多个
    segment/via 写成同一个 uuid**（路由级），本函数每个节点各派生一个
    （对象级），并用 dup_index 保证"同批两个几何全同的新节点"也不撞键；
    再与板上既有 uuid 逐次规避（冲突时加确定性 nonce 重试）。
    """
    nonce = 0
    while True:
        payload = _uuid_payload(kind, facts)
        payload["dup_index"] = dup_index
        if nonce:
            payload["nonce"] = nonce
        d = _sha(payload)
        cand = "-".join((d[:8], d[8:12], d[12:16], d[16:20], d[20:32]))
        if cand not in taken:
            return cand
        nonce += 1


# ==================================================== zone 事实与字节拼接
#
# 本节的实现口径（见模块 docstring"zone op 语义"/"填充过期语义"）：
#   * zone 的 modify **不重渲染整个节点**（否则 141KB/468KB 的 filled_polygon
#     会被无谓重写），而是**按字段子表达式的字节跨度做拼接**：只替换被改字段
#     的字节，其余（尤其 filled_polygon）逐字节不动。
#   * 为此需要一个**带跨度**的 s-expr 解析器 `_sp_parse`（sexpr_min.parse 只
#     给值不给跨度）。它与 sexpr_min 同口径（同样的空白/引号/原子规则）。
#   * `add` 走 `_render_zone_node` 固定模板（**不含 filled_polygon**）。

_SP_WS = " \t\r\n"


def _sp_skip(text: str, i: int) -> int:
    n = len(text)
    while i < n and text[i] in _SP_WS:
        i += 1
    return i


def _sp_atom_end(text: str, i: int) -> int:
    """i 处原子/串的结束位置（未闭合串 → _RenderError）。"""
    n = len(text)
    if text[i] == '"':
        j = i + 1
        while j < n:
            if text[j] == "\\":
                j += 2
                continue
            if text[j] == '"':
                return j + 1
            j += 1
        raise _RenderError("字符串未闭合")
    j = i
    while j < n and text[j] not in _SP_WS and text[j] not in "()":
        j += 1
    if j == i:
        raise _RenderError("空原子 @%d" % i)
    return j


def _sp_parse(text: str, i: int = 0):
    """带跨度的 s-expr 解析 → (node, next_i)。

    node = ["list", start, end, [child...]] | ["atom", start, end, raw]
    （跨度是 `text` 上的 [start, end) 半开区间；含引号原样保留在 raw 里。）
    """
    n = len(text)
    i = _sp_skip(text, i)
    if i >= n:
        raise _RenderError("意外结束（期望 s-expr）")
    if text[i] == "(":
        start = i
        children = []
        i = _sp_skip(text, i + 1)
        while True:
            i = _sp_skip(text, i)
            if i >= n:
                raise _RenderError("括号未闭合")
            if text[i] == ")":
                return ["list", start, i + 1, children], i + 1
            child, i = _sp_parse(text, i)
            children.append(child)
    if text[i] == ")":
        raise _RenderError("意外的 ')' @%d" % i)
    j = _sp_atom_end(text, i)
    return ["atom", i, j, text[i:j]], j


def _sp_atoms(node) -> list:
    return [c for c in node[3] if c[0] == "atom"]


def _sp_body(node) -> list:
    """列表节点的"体"（去掉首元素 head）；非列表 → []。"""
    return node[3][1:] if node[0] == "list" else []


def _sp_body_atoms(node) -> list:
    """列表节点体里的原子（不含 head）。"""
    return [c for c in _sp_body(node) if c[0] == "atom"]


def _sp_lists(node) -> list:
    return [c for c in node[3] if c[0] == "list"]


def _sp_head(text: str, node) -> "str | None":
    """列表节点的首原子（未加引号的名字），非列表/无首原子 → None。"""
    if node[0] != "list":
        return None
    atoms = _sp_atoms(node)
    if not atoms:
        return None
    return _sp_unquote(atoms[0][3])


def _sp_find(text: str, node, name: str):
    if node[0] != "list":
        return None
    for c in node[3]:
        if c[0] == "list" and _sp_head(text, c) == name:
            return c
    return None


def _sp_find_all(text: str, node, name: str) -> list:
    out = []
    if node[0] != "list":
        return out
    for c in node[3]:
        if c[0] == "list" and _sp_head(text, c) == name:
            out.append(c)
    return out


def _sp_unquote(raw: str) -> str:
    """原子原文 → 值（双引号包裹则去引号并解转义；否则原样）。"""
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        body = raw[1:-1]
        return body.replace('\\"', '"').replace("\\\\", "\\")
    return raw


def _sp_walk(text: str, node, path):
    """按名字路径下钻 → 子表达式节点，任一层缺失返回 None。"""
    cur = node
    for name in path:
        cur = _sp_find(text, cur, name)
        if cur is None:
            return None
    return cur


def _sp_list_layout(inner: str, node_eol: str):
    """子表达式列表内部布局 → (inline, inner_indent, closer_indent)。

    `inner` 是 "(" 与 ")" 之间的原文。
    """
    first = _EOL_RE.search(inner)
    if first is None:
        return True, "", ""
    inner_indent = _indent_after(inner, first.end())
    last = None
    for last in _EOL_RE.finditer(inner):
        pass
    closer_indent = _indent_after(inner, last.end())
    return False, inner_indent, closer_indent


def _render_list_like(old_inner: str, head: str, items: list,
                      node_eol: str) -> str:
    """克隆 `old_inner`（某列表的括号内原文）的布局渲染新列表。

    单行 → `(head a b c)`；多行 → `(head<eol><inner_indent><items 同行平铺>
    <eol><closer_indent>)`。Rev-C 的 `(pts\\n\\t\\t\\t\\t(xy ..) (xy ..)\\n\\t\\t\\t)`
    正是这个形状，故**点数不变时逐字节同构**。
    """
    inline, ind, closer = _sp_list_layout(old_inner, node_eol)
    body = " ".join(items)
    if inline:
        return "(" + head + (" " + body if body else "") + ")"
    return "(" + head + node_eol + ind + body + node_eol + closer + ")"


# ------------------------------------------------------------ zone 事实

def _zone_params_facts(text: str, node) -> dict:
    """zone 参数解析（`copper_model._zone_params` 的**逐字段镜像**）。

    镜像理由：copper_model 未导出该 helper，而本模块不得改动对方文件；词表
    必须与之逐字一致，否则 `expect` 就不能"原样抄自 copper_model"。等价性
    由测试对真实板 + 合成板钉死。
    """
    def num(sub):
        if sub is None:
            return None
        atoms = _sp_body_atoms(sub)
        return _fnum(_sp_unquote(atoms[0][3])) if atoms else None

    def put(params, name, sub):
        v = num(sub)
        if v is not None:
            params[name] = int(v) if float(v).is_integer() else _q(v, _DIM_Q)

    def head_token(sub):
        """`_leaf(node, None, 1)` 口径：首元素之后的第一个原子。"""
        atoms = _sp_body_atoms(sub)
        return _sp_unquote(atoms[0][3]) if atoms else None

    params = {}
    hatch = _sp_find(text, node, "hatch")
    if hatch is not None:
        toks = [_sp_unquote(a[3]) for a in _sp_body_atoms(hatch)]
        if toks:
            params["hatch"] = " ".join(toks)
    cp = _sp_find(text, node, "connect_pads")
    if cp is not None:
        mode = head_token(cp)
        if mode:
            params["connect_pads_mode"] = mode
        put(params, "clearance", _sp_find(text, cp, "clearance"))
    fill = _sp_find(text, node, "fill")
    if fill is not None:
        mode = head_token(fill)
        if mode:
            params["fill"] = mode
        for name in ("min_thickness", "clearance", "thermal_gap",
                     "thermal_bridge_width", "arc_segments",
                     "island_removal_mode", "priority",
                     "smoothing_max_error"):
            put(params, "fill_" + name, _sp_find(text, fill, name))
    for name in ("min_thickness", "priority", "smoothing_max_error"):
        put(params, name, _sp_find(text, node, name))
    return params


def _zone_fill_parts(text: str, node) -> list:
    """→ [(span, points)]：每个直接子 `filled_polygon` 的字节跨度与点数。

    与 `copper_model._zone_fill` 同口径（只数 `(pts (xy ...))` 里的 xy）。
    """
    out = []
    for fp in _sp_find_all(text, node, "filled_polygon"):
        pts = _sp_find(text, fp, "pts")
        n = 0
        if pts is not None:
            for c in _sp_lists(pts):
                if _sp_head_raw(c) != "xy":
                    continue
                atoms = _sp_body_atoms(c)
                if len(atoms) >= 2 and _fnum(_sp_unquote(atoms[0][3])) \
                        is not None and _fnum(_sp_unquote(atoms[1][3])) \
                        is not None:
                    n += 1
        out.append(((fp[1], fp[2]), n))
    return out


def _sp_head_raw(node) -> "str | None":
    """列表节点的首原子值（不看名字语义，仅取第一个 atom）。"""
    if node[0] != "list":
        return None
    for c in node[3]:
        if c[0] == "atom":
            return _sp_unquote(c[3])
    return None


def _zone_facts(node_text: str):
    """zone 节点字节 → (facts, None) 或 (None, reason)。

    facts 键：uuid / net / layers / outline_mm / params（copper_model 词表）/
    fill_present / fill_points / fill_spans（节点内绝对跨度）/ `spans`
    （可编辑落点的跨度表，供拼接用）/ `has_net_name`。
    """
    try:
        node, next_i = _sp_parse(node_text, 0)
    except _RenderError as exc:
        return None, "s-expr 解析失败: %s" % (exc,)
    if _sp_skip(node_text, next_i) != len(node_text) or node[0] != "list":
        return None, "节点形状非法（非单一列表）"
    if _sp_head(node_text, node) != "zone":
        return None, "节点不是 (zone ...)"
    uuid_node = _sp_find(node_text, node, "uuid")
    uuid = None
    if uuid_node is not None:
        atoms = _sp_body_atoms(uuid_node)
        if atoms:
            v = _sp_unquote(atoms[0][3])
            uuid = v or None
    net_node = _sp_find(node_text, node, "net")
    name_node = _sp_find(node_text, node, "net_name")
    net = None
    if net_node is not None:
        atoms = _sp_body_atoms(net_node)
        if atoms:
            net = _sp_unquote(atoms[0][3])
    net_name = None
    if name_node is not None:
        atoms = _sp_body_atoms(name_node)
        if atoms:
            net_name = _sp_unquote(atoms[0][3])
    net_eff = net_name if net_name else net
    layers, layer_nodes = [], []
    for c in _sp_lists(node):
        h = _sp_head(node_text, c)
        if h in ("layer", "layers"):
            layer_nodes.append(c)
            for a in _sp_body_atoms(c):
                v = _sp_unquote(a[3])
                if v:
                    layers.append(v)
    bad = []
    if not isinstance(net_eff, str) or net_eff == "":
        bad.append("net")
    if not layers:
        bad.append("layers")
    if bad:
        return None, "缺/非法字段: " + ",".join(bad)
    polygon = _sp_find(node_text, node, "polygon")
    pts = _sp_find(node_text, polygon, "pts") if polygon is not None else None
    outline, xy_nodes = [], []
    if pts is not None:
        for c in _sp_lists(pts):
            if _sp_head(node_text, c) != "xy":
                continue
            atoms = _sp_body_atoms(c)
            if len(atoms) < 2:
                return None, "polygon 顶点非法（xy 分量不足）"
            x, y = _fnum(_sp_unquote(atoms[0][3])), _fnum(
                _sp_unquote(atoms[1][3]))
            if x is None or y is None:
                return None, "polygon 顶点非法（xy 非数值对）"
            outline.append([_q(x, _GEO_Q), _q(y, _GEO_Q)])
            xy_nodes.append(c)
    if len(outline) < 3:
        return None, ("zone 无有效轮廓：polygon/pts/xy 缺失或 <3 点"
                      "（实得 %d 点）" % len(outline))
    fills = _zone_fill_parts(node_text, node)
    fill_spans = [sp for sp, _n in fills]
    facts = {
        "uuid": uuid,
        "net": net_eff,
        "layers": layers,
        "outline_mm": outline,
        "params": _zone_params_facts(node_text, node),
        "fill_present": bool(fill_spans),
        "fill_points": sum(n for _s, n in fills),
        "fill_spans": fill_spans,
        "has_net_name": name_node is not None,
        "spans": {
            "root": (node[1], node[2]),
            "node": node,
            "polygon": polygon,
            "pts": pts,
            "xy": xy_nodes,
            "layer_nodes": layer_nodes,
            "net": net_node,
            "net_name": name_node,
        },
    }
    return facts, None


# ------------------------------------------------------------ zone 拼接

def _zone_decl_expr(layers: list) -> str:
    """层声明子表达式：1 层 → `(layer "X")`；≥2 层 → `(layers "X" "Y")`。"""
    if len(layers) == 1:
        return '(layer "%s")' % _esc(layers[0])
    return "(layers %s)" % " ".join('"%s"' % _esc(l) for l in layers)


def _zone_param_repr(key: str, value) -> str:
    """参数值 → 板文本 token（数值走 `_fmt_num` 最短往返）。"""
    if key in _ZONE_PARAM_NUM_POS:
        return _fmt_num(value)
    if key in _ZONE_PARAM_ENUM_INT:
        return str(int(value))
    if key in _ZONE_PARAM_ENUM_STR:
        return str(value)
    raise _RenderError("参数 %s 无渲染口径" % key)


def _zone_edits(node_text: str, facts: dict, changes: dict,
                node_eol: str) -> list:
    """被改字段 → [(start, end, replacement)]（节点内绝对跨度，互不重叠）。

    只做**值/子表达式替换**：不改动任何未被请求的字节。任何"要改的东西在目标
    zone 里不存在"一律抛 `_ZoneBlocked`（fail-closed，不做插入）。
    """
    spans = facts["spans"]
    edits = []
    if "net" in changes:
        if spans["net_name"] is not None:
            raise _ZoneBlocked(
                "zone_net_declaration_unsupported: zone 的 net 由 "
                "(net_name ...) 声明（KiCad5 形态），net 号无法由名称派生；"
                "本模块只支持 (net \"名称\") 形态")
        nn = spans["net"]
        atoms = _sp_body_atoms(nn)
        if len(atoms) != 1 or not atoms[0][3].startswith('"'):
            raise _ZoneBlocked(
                "zone_net_declaration_unsupported: (net ...) 不是单值字符串"
                "形态（实得 %r）" % node_text[nn[1]:nn[2]])
        edits.append((atoms[0][1], atoms[0][2],
                      '"%s"' % _esc(changes["net"])))
    if "layers" in changes:
        decls = spans["layer_nodes"]
        if not decls:
            raise _ZoneBlocked("zone_layers_unsupported: zone 无 (layer ...) "
                               "声明（不可编辑）")
        edits.append((decls[0][1], decls[0][2],
                      _zone_decl_expr(list(changes["layers"]))))
        for extra in decls[1:]:         # 多余的层声明一并移除（不得留双声明）
            edits.append((extra[1], extra[2], ""))
    if "outline_mm" in changes:
        pts = spans["pts"]
        if pts is None:
            raise _ZoneBlocked("zone_outline_unsupported: zone 无 "
                               "(polygon (pts ...)) 结构（不可编辑轮廓）")
        inner = node_text[pts[1] + 1:pts[2] - 1]
        items = ["(xy %s)" % _fmt_xy(p) for p in changes["outline_mm"]]
        edits.append((pts[1], pts[2],
                      _render_list_like(inner, "pts", items, node_eol)))
    for key in sorted(changes.get("params") or {}):
        value = changes["params"][key]
        path = _ZONE_PARAM_PATH[key]
        sub = _sp_walk(node_text, spans["node"], path)
        if sub is None:
            raise _ZoneBlocked(
                "param_not_present: op 请求改参数 %s（落点 %s），但目标 zone "
                "里不存在该子表达式 —— 本模块只做值替换、不插入 zone 子表达式"
                % (key, ".".join(path)))
        if key in _ZONE_PARAM_TOKENS:
            edits.append((sub[1], sub[2], "(%s %s)" % (path[-1], value)))
            continue
        if key in _ZONE_PARAM_ENUM_STR and len(path) == 1:
            # 首 token 形态（fill / connect_pads_mode）
            atoms = _sp_body_atoms(sub)
            if not atoms:
                raise _ZoneBlocked("param_not_present: %s 无首 token" % key)
            edits.append((atoms[0][1], atoms[0][2], str(value)))
            continue
        atoms = _sp_body_atoms(sub)
        if len(atoms) != 1:
            raise _ZoneBlocked(
                "param_not_present: 参数 %s 的落点不是单值形态（实得 %r）"
                % (key, node_text[sub[1]:sub[2]]))
        edits.append((atoms[0][1], atoms[0][2],
                      _zone_param_repr(key, value)))
    edits.sort(key=lambda e: (e[0], e[1]))
    last = -1
    for (s, e, _r) in edits:
        if s < last or e < s or s < 0 or e > len(node_text):
            raise _RenderError("zone 编辑跨度重叠/越界: %s" % ((s, e),))
        last = e
    return edits


class _ZoneBlocked(Exception):
    """zone 专属 fail-closed（reason 自带码，直接进 blocked_ops）。"""


def _apply_edits(text: str, edits: list) -> str:
    out = []
    last = 0
    for (s, e, r) in edits:
        out.append(text[last:s])
        out.append(r)
        last = e
    out.append(text[last:])
    return "".join(out)


def _splice_zone(node_text: str, facts: dict, changes: dict, node_eol: str):
    """zone 节点 + 字段变更 → (新节点文本, (编辑跨度, 填充跨度) 等价证据)。

    返回 `(new_text, evidence)`，evidence =
    `{edited_spans, fill_spans_before, fill_spans_after, fill_bytes_preserved,
      fill_sha256_before, fill_sha256_after}`。

    **填充字节保真**是构造性实证：编辑跨度与填充跨度必须不相交（否则抛
    `_RenderError`），随后逐段比对改前/改后的 `filled_polygon` 子串。
    """
    edits = _zone_edits(node_text, facts, changes, node_eol)
    fill_before = [(s, e) for (s, e) in facts["fill_spans"]]
    for (fs, fe) in fill_before:
        for (s, e, _r) in edits:
            if s < fe and fs < e:
                raise _RenderError(
                    "zone 编辑跨度 %s 与 filled_polygon 跨度 %s 相交："
                    "禁止重写填充字节" % ((s, e), (fs, fe)))
    new_text = _apply_edits(node_text, edits)
    shift = 0
    moves = {}
    for (s, e, r) in edits:
        moves[(s, e)] = shift
        shift += len(r) - (e - s)
    fill_after = []
    for (fs, fe) in fill_before:
        d = 0
        for (s, e, _r) in edits:
            if e <= fs:
                d += len(_r) - (e - s)
        fill_after.append((fs + d, fe + d))
    ok = True
    for (bs, be), (as_, ae) in zip(fill_before, fill_after):
        if node_text[bs:be] != new_text[as_:ae]:
            ok = False
            break
    if not ok:
        raise _RenderError("filled_polygon 字节在拼接后被改动")
    fill_txt_before = "".join(node_text[s:e] for (s, e) in fill_before)
    fill_txt_after = "".join(new_text[s:e] for (s, e) in fill_after)
    return new_text, {
        "edited_spans": [[s, e] for (s, e, _r) in edits],
        "fill_spans_before": [[s, e] for (s, e) in fill_before],
        "fill_spans_after": [[s, e] for (s, e) in fill_after],
        "fill_bytes_preserved": (fill_txt_before == fill_txt_after),
        "fill_sha256_before": hashing.sha256_text(fill_txt_before),
        "fill_sha256_after": hashing.sha256_text(fill_txt_after),
    }


# ------------------------------------------------------------ zone 渲染（add）

def _render_zone_node(facts: dict, style: dict) -> str:
    """新 zone 节点模板（**不含任何 filled_polygon**；见模块 docstring）。

    与 Rev-C 既有 zone 同构：net / layer / uuid / hatch? / connect_pads? /
    min_thickness? / fill / polygon。未给出的可选参数不写（交回 KiCad 默认）。
    """
    eol = style["eol"]
    L1 = style["child"]
    L2 = L1 + "\t"
    L3 = L2 + "\t"
    params = _norm_params(facts.get("params") or {})
    exprs = ['(net "%s")' % _esc(facts["net"]),
             _zone_decl_expr(list(facts["layers"]))]
    if facts.get("uuid"):
        exprs.append('(uuid "%s")' % _esc(facts["uuid"]))
    if "hatch" in params:
        exprs.append("(hatch %s)" % params["hatch"])
    if "clearance" in params or "connect_pads_mode" in params:
        cp = ["(connect_pads"]
        if "connect_pads_mode" in params:
            cp.append(" %s" % params["connect_pads_mode"])
        if "clearance" in params:
            cp.append(eol + L2 + "(clearance %s)" % _fmt_num(
                params["clearance"]) + eol + L1)
        cp.append(")")
        exprs.append("".join(cp))
    if "min_thickness" in params:
        exprs.append("(min_thickness %s)" % _fmt_num(params["min_thickness"]))
    fill_mode = params.get("fill", "yes")
    fill_kids = [("thermal_gap", params["fill_thermal_gap"])] if \
        "fill_thermal_gap" in params else []
    if "fill_thermal_bridge_width" in params:
        fill_kids.append(("thermal_bridge_width",
                          params["fill_thermal_bridge_width"]))
    if "fill_island_removal_mode" in params:
        fill_kids.append(("island_removal_mode",
                          params["fill_island_removal_mode"]))
    if fill_kids:
        body = "".join(eol + L2 + "(%s %s)" % (
            k, _zone_param_repr("fill_" + k, v)) for k, v in fill_kids)
        exprs.append("(fill %s%s%s%s)" % (fill_mode, body, eol, L1))
    else:
        exprs.append("(fill %s)" % fill_mode)
    items = ["(xy %s)" % _fmt_xy(p) for p in facts["outline_mm"]]
    pts_line = " ".join(items)
    exprs.append("(polygon" + eol + L2 + "(pts" + eol + L3 + pts_line + eol
                 + L2 + ")" + eol + L1 + ")")
    return _render_expr("zone", exprs, style)


# ------------------------------------------------------------ 填充过期判定

def _zone_fill_verdict(kind: str, op: str, changes: dict,
                       raw: "dict | None") -> dict:
    """一次 zone 编辑 → 填充状态判定（**判据写死在这里**，见模块 docstring）。

    返回 `{fill_state, fill_present, fill_invalidated, refill_required,
    stale_fields, stale_params, fill_reason}`：
      * `add`（无既有填充）：`fill_present=False` / `fill_state="unknown"` /
        `refill_required=True`；
      * `modify` 改了 `ZONE_STALE_FIELDS` 或 `ZONE_STALE_PARAMS` 中任一（且值
        确实变了）：`fill_state="stale"` / `refill_required=True`；
      * 其余（只改 `hatch`）：`fill_state="unknown"`（**不谎称 fresh**，本模块
        从不产出 fresh）/ `refill_required=False`。
    """
    if op == "add":
        return {"fill_state": "unknown", "fill_present": False,
                "fill_invalidated": False, "refill_required": True,
                "stale_fields": [], "stale_params": [],
                "fill_reason": "new_zone_has_no_filled_polygon: 新增 zone 不带"
                               "填充（合法状态），但非 fresh ⇒ 需重填证据"}
    stale_fields = sorted(f for f in changes if f in ZONE_STALE_FIELDS)
    stale_params = sorted(k for k in (changes.get("params") or {})
                          if k in ZONE_STALE_PARAMS)
    present = bool((raw or {}).get("fill_present"))
    invalidated = bool(stale_fields or stale_params)
    if invalidated:
        reason = ("fill_invalidated_by: %s —— 这些字段/参数参与 KiCad 的 zone "
                  "填充几何计算，既有 filled_polygon 已失效（字节保留不动，"
                  "状态如实标 stale）"
                  % ", ".join(stale_fields + stale_params))
    else:
        reason = ("fill_preserved: 本次改动不参与填充几何计算"
                  "（hatch 仅影响轮廓显示样式），既有 filled_polygon 仍然有效；"
                  "本模块不声称 fresh（fresh 需填充指纹证据，由调用方声明）")
    return {"fill_state": "stale" if invalidated else "unknown",
            "fill_present": present,
            "fill_invalidated": invalidated,
            "refill_required": bool(invalidated or not present),
            "stale_fields": stale_fields, "stale_params": stale_params,
            "fill_reason": reason}


def _zone_fill_summary(records: list) -> dict:
    """逐 op 填充记账 → 门判据汇总（`fill_gate` 的唯一输入）。"""
    not_fresh = sorted({r["zone_id"] for r in records
                        if r.get("refill_required") and r.get("zone_id")})
    return {
        "zones_touched": len(records),
        "refill_required": any(bool(r.get("refill_required"))
                               for r in records),
        "not_fresh_zone_ids": not_fresh,
        "stale_zone_ids": sorted({r["zone_id"] for r in records
                                  if r.get("fill_state") == "stale"
                                  and r.get("zone_id")}),
        "absent_fill_zone_ids": sorted(
            {r["zone_id"] for r in records
             if r.get("fill_state") == "unknown" and not r.get("fill_present")
             and r.get("zone_id")}),
        "fill_states": {r["zone_id"]: r.get("fill_state") for r in records
                        if r.get("zone_id")},
        "rule": ZONE_FILL_SUMMARY_RULE,
        "fill_state_is_patch_derived": True,
        "note": "只统计**本轮 zone op 触及**的 zone：未触及 zone 的填充新鲜度"
                "是基准板自身的事实，不由本补丁改变，也不在本判据内。"
                "本模块从不产出 fresh（fresh 需填充指纹证据）。",
    }


# ------------------------------------------------------------ 采纳门

def validate_refill_evidence(evidence, expected_source_sha256=None) -> list:
    """重填证据结构校验 → reason 列表（fail-closed，收集全部失败）。"""
    errs = []
    if not isinstance(evidence, dict):
        return ["refill_evidence_invalid: 证据不是对象（实得 %s）"
                % type(evidence).__name__]
    if evidence.get("schema") != REFILL_EVIDENCE_SCHEMA:
        errs.append("refill_evidence_schema_mismatch: schema=%r ≠ %r"
                    % (evidence.get("schema"), REFILL_EVIDENCE_SCHEMA))
    if evidence.get("refill_performed") is not True:
        errs.append("refill_evidence_invalid: refill_performed 必须为 true"
                    "（实得 %r）" % (evidence.get("refill_performed"),))
    steps = evidence.get("steps")
    if not isinstance(steps, list) or not steps:
        errs.append("refill_evidence_invalid: steps 必须是非空列表"
                    "（实得 %r）" % (steps,))
    else:
        for i, st in enumerate(steps):
            if not isinstance(st, dict):
                errs.append("refill_evidence_invalid: steps[%d] 不是对象" % i)
                continue
            if not isinstance(st.get("step"), str) or not st.get("step"):
                errs.append("refill_evidence_invalid: steps[%d].step 必须是非空"
                            "字符串" % i)
            if st.get("exit_code") != 0:
                errs.append("refill_evidence_invalid: steps[%d].exit_code=%r"
                            "（重填步骤必须成功退出）" % (i, st.get("exit_code")))
    ver = evidence.get("kicad_version")
    if not isinstance(ver, str) or not ver:
        errs.append("refill_evidence_invalid: 缺 kicad_version（非空字符串）")
    for key in ("source_board_sha256", "refilled_board_sha256"):
        v = evidence.get(key)
        if not isinstance(v, str) or not _SHA256_RE.match(v):
            errs.append("refill_evidence_invalid: %s 不是 64 位小写 hex"
                        "（实得 %r）" % (key, v))
    src = evidence.get("source_board_sha256")
    if expected_source_sha256 and isinstance(src, str) and \
            src != expected_source_sha256:
        errs.append("refill_evidence_stale: source_board_sha256=%s ≠ 本轮采纳"
                    "来源 sha=%s（证据不属于本轮 staging 板：拒绝拿别的轮次/"
                    "过期证据过关）" % (src, expected_source_sha256))
    return errs


def _resolve_refill_evidence(record, revision_dir, evidence):
    """→ (evidence|None, source_label, reason|None)。"""
    if evidence is not None:
        return evidence, "explicit", None
    rec = record if isinstance(record, dict) else {}
    if isinstance(rec.get("refill_evidence"), dict):
        return rec["refill_evidence"], "record.refill_evidence", None
    if revision_dir:
        for rel in (REFILL_EVIDENCE_REL, REFILL_EVIDENCE_ALT_REL):
            path = os.path.join(revision_dir, rel)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f), rel.replace(os.sep, "/"), None
            except Exception as exc:
                return None, rel.replace(os.sep, "/"), (
                    "refill_evidence_unparseable: %s 不可解析（%s: %s）"
                    % (rel.replace(os.sep, "/"), exc.__class__.__name__, exc))
    return None, None, None


def fill_gate(record, *, ledger=None, revision_dir=None, evidence=None,
              source_sha256=None, required_override=None) -> dict:
    """采纳门：含"填充过期/无填充"的 zone 编辑的轮次，必须记录重填证据。

    见模块 docstring"采纳门 fill_gate(...)"。纯函数：唯一 IO 是（给了
    `revision_dir` 时）读 `drc/refill-evidence.json`。

    `required` 取自 `ledger["patch_ledger"]["zone_fill_summary"]`（轮次台账里
    `_set_patch_ledger` 落的 `apply_patch` 完整 ledger）；`required=False` ⇒
    `ok=True`（未触及 zone 的轮次一律放行）。**无 summary 可据以推导时
    fail-closed 拒绝**（reason_code=ledger_missing）——缺台账不得静默视
    `required=False`（REPAIR-P2 W-3，铜环裁决 2026-09-11 §8 P1-2 从"缓修"
    转"修复"）；显式 `required_override` 传入时以调用方断言为准（仅供在树
    外调用方显式担责，在树调用方一律传完整 ledger）。
    """
    patch_ledger = None
    if isinstance(ledger, dict):
        patch_ledger = ledger.get("patch_ledger")
    rec = record if isinstance(record, dict) else {}
    if not isinstance(patch_ledger, dict):
        patch_ledger = rec.get("patch_ledger")
    summary = None
    if isinstance(patch_ledger, dict):
        summary = patch_ledger.get("zone_fill_summary")
    if summary is None:
        summary = (rec.get("patch") or {}).get("zone_fill_summary") \
            if isinstance(rec.get("patch"), dict) else None
    summary_valid = summary if isinstance(summary, dict) else None
    base = {
        "schema": FILL_GATE_SCHEMA,
        "rule": REFILL_GATE_RULE,
        "zone_fill_summary": summary,
        "not_fresh_zone_ids": list((summary_valid or {}).get("not_fresh_zone_ids")
                                   or []),
        "fill_states": dict((summary_valid or {}).get("fill_states") or {}),
        "expected_source_sha256": None,
        "evidence": None,
        "evidence_source": None,
        "refill_evidence_sha256": None,
        "reasons": [],
        "reason_code": None,
    }
    if required_override is not None:
        required = bool(required_override)
    elif summary_valid is None:
        base.update({
            "ok": False, "required": None,
            "status_label": "unverifiable",
            "reason_code": "ledger_missing",
            "reasons": [
                "ledger_missing: 无 zone_fill_summary 可据以推导 "
                "refill_required（缺台账/台账与记录均无该键）⇒ 无法核实"
                "zone 填充门，fail-closed 拒绝（REPAIR-P2 W-3；显式传 "
                "required_override 可由调用方担责覆盖）"]})
        return base
    else:
        required = bool(summary_valid.get("refill_required"))
    if not required:
        base.update({"ok": True, "required": False,
                     "status_label": "ok",
                     "note": "本轮 zone op 未使任何填充过期（或未触及 zone）"})
        return base

    if source_sha256 is None:
        source_sha256 = ((rec.get("patch") or {}).get("staging_sha256")
                         if isinstance(rec.get("patch"), dict) else None)
    base["expected_source_sha256"] = source_sha256
    ev, src_label, why = _resolve_refill_evidence(rec, revision_dir, evidence)
    if why:
        base.update({"ok": False, "required": True,
                     "status_label": "awaiting_refill",
                     "reason_code": why.split(":")[0], "reasons": [why]})
        return base
    if ev is None:
        tries = [REFILL_EVIDENCE_REL.replace(os.sep, "/"),
                 REFILL_EVIDENCE_ALT_REL]
        base.update({
            "ok": False, "required": True, "status_label": "awaiting_refill",
            "reason_code": REASON_REFILL_EVIDENCE_MISSING,
            "reasons": [
                "%s: 本轮 zone 编辑使填充非 fresh（stale/无填充），但轮次记录"
                "里没有 refill_evidence —— 待重填 zone=%s；请把编排侧重填证据"
                "落到 %s（schema=%s）后重试 accept/adopt"
                % (REASON_REFILL_EVIDENCE_MISSING,
                   base["not_fresh_zone_ids"],
                   " 或 ".join(tries), REFILL_EVIDENCE_SCHEMA)]})
        return base
    errs = validate_refill_evidence(ev, source_sha256)
    base["evidence"] = ev
    base["evidence_source"] = src_label
    base["refill_evidence_sha256"] = _sha(ev)
    if errs:
        base.update({"ok": False, "required": True,
                     "status_label": "awaiting_refill",
                     "reason_code": errs[0].split(":")[0], "reasons": errs})
        return base
    base.update({"ok": True, "required": True, "status_label": "ok",
                 "note": "已记录重填证据（refill_performed=true + 步骤退出码 0 "
                         "+ source_board_sha256 绑定本轮 staging 板）"})
    return base


# ------------------------------------------------------------ 分片模型

class _Piece:
    """文档分片。

    role: "raw"（不可变原始字节）/ "node"（铜箔节点自身字节）/
          "insert"（本次新增的整行）/ "deleted"（本次删除的节点，文本已清空）
    orig: 对应的**原文**字节范围 [start, end)（insert 为 None）；用于把原文
          坐标映射到当前文本坐标（每次编辑后文本长度会变）。
    """

    __slots__ = ("text", "role", "tag", "orig", "op_index", "final_target")

    def __init__(self, text, role="raw", tag=None, orig=None, op_index=-1,
                 final_target=False):
        self.text = text
        self.role = role
        self.tag = tag
        self.orig = orig
        self.op_index = op_index
        self.final_target = final_target


def _build_pieces(text: str):
    """板文本 → ([_Piece...], {(start,end): _Piece})（节点跨度来自 copper_model）。"""
    pieces = []
    by_span = {}
    pos = 0
    for (tag, s, e) in copper_model.top_level_copper_nodes(text):
        if s > pos:
            pieces.append(_Piece(text[pos:s], "raw", orig=[pos, s]))
        piece = _Piece(text[s:e], "node", tag=tag, orig=[s, e])
        pieces.append(piece)
        by_span[(s, e)] = piece
        pos = e
    pieces.append(_Piece(text[pos:], "raw", orig=[pos, len(text)]))
    return pieces, by_span


def _cum(pieces) -> list:
    out = []
    total = 0
    for p in pieces:
        out.append(total)
        total += len(p.text)
    out.append(total)
    return out


def _orig_to_current(pieces, off: int) -> int:
    """原文坐标 → 当前文本坐标（按分片 orig 范围定位；越界钳到片尾）。"""
    cur = 0
    for p in pieces:
        if p.orig is not None and p.orig[0] <= off <= p.orig[1]:
            local = off - p.orig[0]
            if local > len(p.text):
                local = len(p.text)
            return cur + local
        cur += len(p.text)
    return cur


def _insert_piece(pieces, off: int, new_piece: _Piece) -> None:
    """在当前文本偏移 off 处插入分片（拆分所在 raw 分片；边界处不拆）。"""
    cum = _cum(pieces)
    p = bisect.bisect_right(cum, off) - 1
    if p < 0:
        p = 0
    if p >= len(pieces):
        pieces.append(new_piece)
        return
    local = off - cum[p]
    if local == 0:
        pieces.insert(p, new_piece)
        return
    if local >= len(pieces[p].text):
        pieces.insert(p + 1, new_piece)
        return
    old = pieces[p]
    left = _Piece(old.text[:local], old.role, tag=old.tag,
                  orig=[old.orig[0], old.orig[0] + local])
    right = _Piece(old.text[local:], old.role, tag=old.tag,
                   orig=[old.orig[0] + local, old.orig[1]])
    pieces[p:p + 1] = [left, new_piece, right]


def _remove_spans(text: str, spans) -> "str | None":
    """按跨度摘除（跨度须有序、互不重叠）；重叠/逆序/越界 → None。"""
    out = []
    last = 0
    for (s, e) in sorted(spans):
        if s < last or e < s or s < 0 or e > len(text):
            return None
        out.append(text[last:s])
        last = e
    out.append(text[last:])
    return "".join(out)


# ------------------------------------------------------------ 定位/锚点

def _kind_entries(copper: dict, kind: str) -> list:
    if kind == "segment":
        return copper["segments"]
    if kind == "via":
        return copper["vias"]
    return copper["zones"]


def _locate(copper: dict, kind: str, key: str):
    """key → (span, None) / (None, reason)。

    key 必须**唯一**命中声明的 kind；命中别的 kind = kind 不匹配（fail-closed）。
    """
    matches = [e for e in _kind_entries(copper, kind) if e["key"] == key]
    if len(matches) == 1:
        im = copper["identity_map"].get(key)
        if im is None or im["kind"] != kind:
            return None, ("key_ambiguous: key=%r 命中 %s 但 identity_map 无法"
                          "唯一表达其跨度（身份残留撞键）" % (key, kind))
        return [im["span"][0], im["span"][1]], None
    if len(matches) > 1:
        return None, ("key_ambiguous: key=%r 在 %s 上命中 %d 个节点"
                      "（身份键消歧后仍不唯一）" % (key, kind, len(matches)))
    for other in OP_KINDS:
        if other == kind:
            continue
        if any(e["key"] == key for e in _kind_entries(copper, other)):
            return None, ("kind_mismatch: key=%r 属于 %s，op 声明 kind=%s"
                          % (key, other, kind))
    return None, "key_not_found: key=%r 在板上 %s 节点中不存在" % (key, kind)


def _anchor_piece(pieces, kind: str):
    """插入锚点分片：最后同类节点 → 最后任一存活铜箔节点 → None。"""
    same, any_kind = None, None
    for p in pieces:
        if p.role != "node":
            continue
        any_kind = p
        if p.tag == kind:
            same = p
    return same or any_kind


# ------------------------------------------------------------ 主入口

def _make_ledger(ops_total, node_eol, *, ops_applied=0, adds=0, modifies=0,
                 deletes=0, ops_requested=None, affected_keys=None,
                 counts_before=None, counts_after=None, unchanged=None,
                 guard=None, op_spans=None, uuid_mult_changes=None,
                 unrep_before=None, unrep_after=None, blocked_ops=None,
                 zone_fill=None, zone_fill_summary=None):
    return {
        "ops_total": ops_total,
        "ops_applied": ops_applied,
        "adds": adds,
        "modifies": modifies,
        "deletes": deletes,
        "ops_requested": ops_requested or {"adds": 0, "modifies": 0,
                                          "deletes": 0},
        "affected_keys": affected_keys or [],
        "counts_before": counts_before,
        "counts_after": counts_after,
        "eol": node_eol,
        "unchanged_bytes_outside_targets": unchanged,
        "structural_guard": guard,
        "op_spans": op_spans or [],
        "uuid_multiplicity_changes": uuid_mult_changes or [],
        "unrepresentable_before": unrep_before,
        "unrepresentable_after": unrep_after,
        "blocked_ops": blocked_ops or [],
        # P3b：zone 填充记账与采纳门判据（zone op 为空时是空表/空汇总）
        "zone_fill": zone_fill if zone_fill is not None else [],
        "zone_fill_summary": (zone_fill_summary if zone_fill_summary is not None
                              else _zone_fill_summary([])),
    }


def _board_net_names(board_text: str, copper: dict) -> set:
    """板文本 → 可解析的 net 名集合（zone 的 net 引用必须落在这里）。

    两个来源的**并集**（宽松、fail-closed 只针对真的查无此 net）：
      1. 板内 net 声明：`(net "name")`（KiCad6+/本仓 writer 形态）与
         `(net N "name")`（KiCad 板头 net 表形态）；
      2. 板上**既有铜箔对象**（segment/via/zone）用的 net 名。

    仅对 zone op 生效：zone 是"net 归属的整层铺铜"，为板上不存在的 net 铺铜
    是悬空引用（KiCad 会丢弃/报错），必须 fail-closed；segment/via 的同类检查
    不在本轮契约内，且既有测试刻意允许在未声明的 net 上追加线段（冻结行为
    不变，R4 的"既有强度不变"红线）。
    """
    decl = re.findall(r'\(net\s+"((?:[^"\\]|\\.)*)"\)', board_text)
    decl += re.findall(r'\(net\s+\d+\s+"((?:[^"\\]|\\.)*)"\)', board_text)
    used = set()
    for kind in OP_KINDS:
        for e in _kind_entries(copper, kind):
            n = e.get("net")
            if isinstance(n, str) and n:
                used.add(n)
    return set(decl) | used


def _blocked(ops_total, node_eol, reasons_by_op, ledger_extra):
    reasons = []
    blocked_ops = []
    for i in sorted(reasons_by_op):
        if not reasons_by_op[i]:
            continue
        reasons.extend(reasons_by_op[i])
        blocked_ops.append({"index": i, "reasons": list(reasons_by_op[i])})
    ledger = _make_ledger(ops_total, node_eol, blocked_ops=blocked_ops,
                          **ledger_extra)
    return {"ok": False, "verdict": "blocked", "reasons": reasons,
            "board_text": None, "ledger": ledger}


def _zone_fill_model_audit(copper_before, copper_after, zone_fill_records):
    """apply_patch 结构守卫 3d 段（SEC-A-05 修复口径，REPAIR-P3S W-A）。

    用 copper_model 独立复核 zone 填充指纹改前改后一致；modify 记录凡复核
    不可得（无 zone_id，或 copper_model 两侧缺该 zone）一律按 unverifiable
    fail-closed 登记（显式置 False + 上标注），聚合缺席键不再视 True——与
    fill_gate ledger_missing 口径对齐，不再静默放行。返回 None=通过。
    """
    if not zone_fill_records:
        return None
    model_before = {z["uuid"]: (z["fill_points"], z["fill_sha256"])
                    for z in copper_before["zones"] if z.get("uuid")}
    model_after = {z["uuid"]: (z["fill_points"], z["fill_sha256"])
                   for z in copper_after["zones"] if z.get("uuid")}
    unverifiable = False
    for rec in zone_fill_records:
        zid = rec.get("zone_id")
        if not zid:
            if rec["op"] == "modify":
                rec["copper_model_fill_identical"] = False
                rec["copper_model_fill_unverifiable"] = True
                unverifiable = True
            continue
        mb = model_before.get(zid)
        ma = model_after.get(zid)
        rec["copper_model_fill_before"] = (
            {"fill_points": mb[0], "fill_sha256": mb[1]} if mb else None)
        rec["copper_model_fill_after"] = (
            {"fill_points": ma[0], "fill_sha256": ma[1]} if ma else None)
        if rec["op"] == "modify":
            rec["copper_model_fill_identical"] = bool(
                mb is not None and ma is not None and mb == ma)
            if mb is None or ma is None:
                rec["copper_model_fill_unverifiable"] = True
                unverifiable = True
            if ma is not None:
                rec["fill_points_after"] = ma[0]
        elif rec["op"] == "add" and ma is not None:
            rec["fill_points_after"] = ma[0]
    if not all(r.get("copper_model_fill_identical", False)
               for r in zone_fill_records if r["op"] == "modify"):
        if unverifiable:
            return ("structural_guard_failed: zone 填充指纹不可复核"
                    "（modify 记录缺 zone_id 或 copper_model 缺该 zone，"
                    "unverifiable 不放行）")
        return ("structural_guard_failed: zone 填充指纹在补丁后被改动"
                "（copper_model 复核不一致）")
    return None


def apply_patch(board_text: str, ops: list, *, eol=None) -> dict:
    """按铜箔对象寻址对板文本做 add/modify/delete（见模块 docstring）。

    整批原子：任一 op 不合法/断言不符/守卫不过 → verdict="blocked"、
    board_text=None、reasons 逐条给出。accepted 时 board_text 为新板文本，且
    除目标节点（及其所在行/插入行）外逐字节不变（ledger 的
    `unchanged_bytes_outside_targets` 为实证结果，非声明）。
    """
    if isinstance(board_text, bool) or not isinstance(board_text, str):
        raise ValueError("board_text: 不是字符串")
    if not isinstance(ops, list):
        raise ValueError("ops: 不是列表")

    ops_total = len(ops)
    node_eol, eol_reason = _resolve_eol(board_text, eol)
    reasons_by_op = {i: [] for i in range(ops_total)}
    if eol_reason:
        reasons_by_op[-1] = [eol_reason]

    ops_requested = {
        "adds": sum(1 for o in ops if isinstance(o, dict)
                    and o.get("op") == "add"),
        "modifies": sum(1 for o in ops if isinstance(o, dict)
                        and o.get("op") == "modify"),
        "deletes": sum(1 for o in ops if isinstance(o, dict)
                       and o.get("op") == "delete"),
    }
    ledger_extra = {"ops_requested": ops_requested}

    # ---------------- 阶段 1：静态形状/枚举/字段校验（不依赖板） ----------
    plans = {}
    seen_keys = {}
    for i, op in enumerate(ops):
        if not isinstance(op, dict):
            reasons_by_op[i].append("unknown_op: op[%d] 不是对象（实得 %s）"
                                    % (i, type(op).__name__))
            continue
        opt, kind = op.get("op"), op.get("kind")
        if opt not in OP_TYPES:
            reasons_by_op[i].append("unknown_op: op[%d] op=%r 不在 %s"
                                    % (i, opt, list(OP_TYPES)))
        if kind not in OP_KINDS:
            reasons_by_op[i].append("unknown_kind: op[%d] kind=%r 不在 %s"
                                    % (i, kind, list(OP_KINDS)))
        if opt not in OP_TYPES or kind not in OP_KINDS:
            continue
        idx = "op[%d]" % i
        key, expect, new = op.get("key"), op.get("expect"), op.get("new")
        if opt in ("modify", "delete"):
            if not (isinstance(key, str) and key):
                reasons_by_op[i].append("missing_key: %s %s 必须给非空 key"
                                        % (idx, opt))
            if not isinstance(expect, dict):
                reasons_by_op[i].append("missing_expect: %s %s 必须给 expect"
                                        "（dict）" % (idx, opt))
            if opt == "modify" and not isinstance(new, dict):
                reasons_by_op[i].append("missing_new: %s modify 必须给 new"
                                        "（dict）" % idx)
            if opt == "delete" and new is not None:
                reasons_by_op[i].append("invalid_field: %s delete 不得给 new"
                                        % idx)
        else:
            if key is not None:
                reasons_by_op[i].append("unexpected_key: %s add 不得给 key"
                                        % idx)
            if expect is not None:
                reasons_by_op[i].append("unexpected_expect: %s add 不得给"
                                        " expect" % idx)
            if not isinstance(new, dict):
                reasons_by_op[i].append("missing_new: %s add 必须给 new（dict）"
                                        % idx)
        if isinstance(expect, dict):
            reasons_by_op[i].extend(_validate_fields(kind, expect, "expect"))
        if isinstance(new, dict):
            reasons_by_op[i].extend(_validate_fields(kind, new, "new"))
            if opt == "add":
                for field in _NEW_REQUIRED[kind]:
                    if field not in new:
                        reasons_by_op[i].append(
                            "missing_new: %s add 缺必需字段 %r" % (idx, field))
        if isinstance(key, str) and key:
            if key in seen_keys:
                reasons_by_op[i].append(
                    "duplicate_key: %s key=%r 与 op[%d] 重复（同一批不得重复"
                    "操作同一对象）" % (idx, key, seen_keys[key]))
            else:
                seen_keys[key] = i
        plans[i] = {"op": opt, "kind": kind, "key": key, "expect": expect,
                    "new": new}

    if any(reasons_by_op.values()):
        return _blocked(ops_total, node_eol, reasons_by_op, ledger_extra)

    # ---------------------- 阶段 2：板相关校验与落实 ----------------------
    copper_before = copper_model.parse_copper(board_text)
    for entry in copper_before["unrepresentable"]:
        if entry["kind"] == "board_parse_error":
            reasons_by_op[-1] = ["board_parse_error: 板文本括号/双引号不平衡，"
                                 "字节跨度不可信（补丁引擎不得据此定位）"]
            return _blocked(ops_total, node_eol, reasons_by_op, ledger_extra)
    ledger_extra["counts_before"] = dict(copper_before["counts"])
    ledger_extra["unrep_before"] = len(copper_before["unrepresentable"])

    taken_uuids = set()
    for kind in OP_KINDS:
        for e in _kind_entries(copper_before, kind):
            if e["uuid"]:
                taken_uuids.add(e["uuid"])

    # 2a. 定位目标 / 断言 expect / 组装 new 事实（此阶段只读，不改文本）
    targets = {}
    style_default = {"inline": False, "lead": "\t", "child": "\t\t",
                     "closer": "\t", "eol": node_eol}
    zone_nets = None
    if any(p["kind"] == "zone" for p in plans.values()):
        zone_nets = _board_net_names(board_text, copper_before)
    for i, plan in plans.items():
        kind, opt = plan["kind"], plan["op"]
        if opt == "add":
            facts = dict(plan["new"])
            facts.setdefault("uuid", None)
            if kind == "via" and not facts.get("via_kind"):
                facts["via_kind"] = _via_kind(None, facts["layers"])
            if kind == "zone":
                # 新 zone **不带填充**（合法状态，ledger 显式记 fill_absent）
                facts["params"] = _norm_params(facts.get("params") or {})
                facts["fill_present"] = False
                if facts["net"] not in zone_nets:
                    reasons_by_op[i].append(
                        "net_unmapped: op[%d] zone.net=%r 不在该板的 net 声明或"
                        "既有铜箔 net 中（zone 是 net 归属的整层铺铜，不得为板上"
                        "不存在的 net 铺铜）" % (i, facts["net"]))
            targets[i] = {"facts": facts}
            continue
        span, reason = _locate(copper_before, kind, plan["key"])
        if reason is not None:
            reasons_by_op[i].append(reason)
            continue
        node_text = board_text[span[0]:span[1]]
        raw, why = _raw_facts(kind, node_text)
        if raw is None:
            reasons_by_op[i].append("key_not_found: key=%r 对应节点不可解析"
                                    "（%s）" % (plan["key"], why))
            continue
        reasons_by_op[i].extend(_check_expect(kind, raw, plan["expect"]))
        if opt == "delete":
            targets[i] = {"span": span, "raw": raw}
            continue
        if kind == "zone":
            merged = dict(raw)
            changes = {}
            for field, value in plan["new"].items():
                if field not in _allowed_fields("zone", "new"):
                    continue
                if field == "params":
                    np = _norm_params(value)
                    diff = {k: v for k, v in np.items()
                            if _params_quantized({k: v})
                            != _params_quantized({k: raw["params"].get(k)})}
                    if diff:
                        changes["params"] = diff
                        merged["params"] = dict(raw["params"])
                        merged["params"].update(diff)
                elif _quantize("zone", field, value) != \
                        _quantize("zone", field, raw.get(field)):
                    changes[field] = value
                    merged[field] = value
            if "net" in changes and changes["net"] not in zone_nets:
                reasons_by_op[i].append(
                    "net_unmapped: zone.net 目标值 %r 不在该板的 net 声明或既有"
                    "铜箔 net 中（不得把铺铜改挂到板上不存在的 net）"
                    % (changes["net"],))
            targets[i] = {"span": span, "raw": raw, "facts": merged,
                          "changes": changes}
            continue
        merged = dict(raw)
        raw_token = merged.pop("raw_token", None)
        for field, value in plan["new"].items():
            if field in _allowed_fields(kind, "new"):
                merged[field] = value
        if kind == "via":
            if "via_kind" in plan["new"]:
                merged["via_kind"] = plan["new"]["via_kind"]
            elif "layers" in plan["new"]:
                merged["via_kind"] = _via_kind(None, merged["layers"])
            else:
                merged["via_kind"] = _via_kind(raw_token, merged["layers"])
        targets[i] = {"span": span, "raw": raw, "facts": merged}

    if any(reasons_by_op.values()):
        return _blocked(ops_total, node_eol, reasons_by_op, ledger_extra)

    # 2b. 逐 op 落实（分片模型：raw 分片永不被改写，只拆/不改字节）
    pieces, by_span = _build_pieces(board_text)
    affected_keys = []
    old_spans = []
    records = {}
    add_dup_counter = {}
    applied = {"adds": 0, "modifies": 0, "deletes": 0}
    zone_fill_records = []
    ledger_extra["zone_fill"] = zone_fill_records

    for i in sorted(plans):
        plan = plans[i]
        kind, opt = plan["kind"], plan["op"]

        if opt == "add":
            facts = dict(targets[i]["facts"])
            sig = _canonical(_uuid_payload(kind, facts))
            dup_index = add_dup_counter.get(sig, 0)
            add_dup_counter[sig] = dup_index + 1
            uuid = _derive_object_uuid(kind, facts, dup_index, taken_uuids)
            taken_uuids.add(uuid)
            facts["uuid"] = uuid
            anchor = _anchor_piece(pieces, kind)
            style = dict(style_default)
            if anchor is not None:
                o_start, o_end = anchor.orig[0], anchor.orig[1]
                style = _style_from_node_text(board_text[o_start:o_end],
                                             node_eol)
                lead = _lead_ws(board_text, o_start) or style["closer"] or "\t"
                orig_off = o_end + len(_split_eol_at(board_text, o_end))
                insert_off = _orig_to_current(pieces, orig_off)
            else:
                stripped = board_text.rstrip()
                if not stripped.endswith(")"):
                    reasons_by_op[i].append(
                        "structural_guard_failed: 板文本不以 ')' 收尾且无锚点，"
                        "不得插入")
                    continue
                lead = style["closer"] or "\t"
                insert_off = _orig_to_current(pieces, len(stripped) - 1)
            try:
                internal = _node_to_text(kind, facts, style)
            except (_RenderError, _ZoneBlocked) as exc:
                reasons_by_op[i].append("structural_guard_failed: %s" % exc)
                continue
            inserted = lead + internal + node_eol
            _insert_piece(pieces, insert_off, _Piece(
                inserted, "insert", op_index=i, final_target=True))
            records[i] = {"orig": None, "lead_len": len(lead),
                          "internal_len": len(internal)}
            targets[i]["facts"] = facts
            targets[i]["uuid"] = uuid
            applied["adds"] += 1
            affected_keys.append({"op": "add", "index": i, "kind": kind,
                                  "key": None, "old_key": None,
                                  "new_key": uuid})
            if kind == "zone":
                v = _zone_fill_verdict(kind, "add", {}, None)
                v.update({"index": i, "op": "add", "zone_key": uuid,
                          "zone_id": uuid,
                          "fill_points_before": None,
                          "fill_points_after": 0,
                          "fill_sha256_before": None,
                          "fill_sha256_after": hashing.sha256_text(""),
                          "fill_bytes_preserved": None,
                          "fill_spans_after": [],
                          "fill_absent_recorded": True})
                zone_fill_records.append(v)
            continue

        if opt == "delete":
            span = targets[i]["span"]
            piece = by_span.get((span[0], span[1]))
            if piece is None:                        # pragma: no cover - 兜底
                reasons_by_op[i].append("structural_guard_failed: 目标节点分片"
                                        "缺失 span=%s" % (span,))
                continue
            idx = pieces.index(piece)
            lead = _lead_ws(board_text, span[0])
            eol_after = _split_eol_at(board_text, span[1])
            prev = pieces[idx - 1] if idx > 0 else None
            nxt = pieces[idx + 1] if idx + 1 < len(pieces) else None
            if prev is not None and lead:
                prev.text = prev.text[:-len(lead)]
                prev.orig[1] -= len(lead)
            if nxt is not None and eol_after:
                nxt.text = nxt.text[len(eol_after):]
                nxt.orig[0] += len(eol_after)
            piece.text = ""
            piece.role = "deleted"
            piece.op_index = i
            old_spans.append((span[0] - len(lead), span[1] + len(eol_after)))
            records[i] = {"orig": (span[0] - len(lead),
                                   span[1] + len(eol_after)),
                          "lead_len": None, "internal_len": None}
            applied["deletes"] += 1
            affected_keys.append({"op": "delete", "index": i, "kind": kind,
                                  "key": plan["key"], "old_key": plan["key"],
                                  "new_key": None})
            continue

        # modify
        span = targets[i]["span"]
        piece = by_span.get((span[0], span[1]))
        if piece is None:                            # pragma: no cover - 兜底
            reasons_by_op[i].append("structural_guard_failed: 目标节点分片"
                                    "缺失 span=%s" % (span,))
            continue
        if kind == "zone":
            # zone：**按字段子表达式字节拼接**（不重渲染节点，填充字节不动）
            node_text = board_text[span[0]:span[1]]
            raw = targets[i]["raw"]
            changes = targets[i]["changes"]
            try:
                internal, ev = _splice_zone(node_text, raw, changes, node_eol)
            except _ZoneBlocked as exc:
                reasons_by_op[i].append(str(exc))
                continue
            except _RenderError as exc:
                reasons_by_op[i].append("structural_guard_failed: %s" % exc)
                continue
            if not ev["fill_bytes_preserved"]:       # pragma: no cover - 兜底
                reasons_by_op[i].append(
                    "structural_guard_failed: zone 拼接改动了 filled_polygon "
                    "字节")
                continue
            piece.text = internal
            piece.op_index = i
            piece.final_target = True
            old_spans.append((span[0], span[1]))
            records[i] = {"orig": (span[0], span[1]), "lead_len": None,
                          "internal_len": len(internal)}
            applied["modifies"] += 1
            affected_keys.append({"op": "modify", "index": i, "kind": kind,
                                  "key": plan["key"], "old_key": plan["key"],
                                  "new_key": None})
            v = _zone_fill_verdict(kind, "modify", changes, raw)
            v.update({"index": i, "op": "modify", "zone_key": plan["key"],
                      "zone_id": raw.get("uuid"),
                      "fill_points_before": raw.get("fill_points"),
                      "fill_points_after": raw.get("fill_points"),
                      "fill_sha256_before": ev["fill_sha256_before"],
                      "fill_sha256_after": ev["fill_sha256_after"],
                      "fill_bytes_preserved": ev["fill_bytes_preserved"],
                      "edited_spans": ev["edited_spans"],
                      "fill_spans_before": ev["fill_spans_before"],
                      "fill_spans_after": ev["fill_spans_after"],
                      "fill_absent_recorded": False})
            zone_fill_records.append(v)
            continue
        style = _style_from_node_text(board_text[span[0]:span[1]], node_eol)
        try:
            internal = _node_to_text(kind, targets[i]["facts"], style)
        except (_RenderError, _ZoneBlocked) as exc:
            reasons_by_op[i].append("structural_guard_failed: %s" % exc)
            continue
        piece.text = internal
        piece.op_index = i
        piece.final_target = True
        old_spans.append((span[0], span[1]))
        records[i] = {"orig": (span[0], span[1]), "lead_len": None,
                      "internal_len": len(internal)}
        applied["modifies"] += 1
        affected_keys.append({"op": "modify", "index": i, "kind": kind,
                              "key": plan["key"], "old_key": plan["key"],
                              "new_key": None})

    if any(reasons_by_op.values()):
        return _blocked(ops_total, node_eol, reasons_by_op, ledger_extra)

    final_text = "".join(p.text for p in pieces)

    # ---------------------- 阶段 3：结构守卫 ------------------------------
    guard = {"ok": True, "checks": [], "sexpr_parse": "ok",
             "counts_ok": False, "counts_delta": None,
             "counts_expected_delta": None, "targets_ok": False,
             "target_details": []}
    cum = _cum(pieces)
    node_final = {}
    target_final = {}
    for p, piece in enumerate(pieces):
        if piece.op_index < 0 or not piece.final_target:
            continue
        start, end = cum[p], cum[p] + len(piece.text)
        target_final[piece.op_index] = [start, end]
        if piece.role != "insert":
            node_final[piece.op_index] = [start, end]
        else:
            rec = records[piece.op_index]
            node_final[piece.op_index] = [start + rec["lead_len"],
                                          start + rec["lead_len"]
                                          + rec["internal_len"]]

    reason_guard = []
    if not _balanced(final_text):
        guard["ok"] = False
        guard["sexpr_parse"] = "failed: 括号/双引号不平衡"
        reason_guard.append("structural_guard_failed: sexpr_balance")
    else:
        try:
            sexpr_min.parse(final_text)
        except sexpr_min.SexprError as exc:
            guard["ok"] = False
            guard["sexpr_parse"] = "failed: %s" % (exc,)
            reason_guard.append("structural_guard_failed: sexpr_parse (%s)"
                                % (exc,))
        else:
            guard["checks"].append("sexpr_parse_ok")

    copper_after = copper_model.parse_copper(final_text)
    ledger_extra["counts_after"] = dict(copper_after["counts"])
    ledger_extra["unrep_after"] = len(copper_after["unrepresentable"])

    expected_delta = {}
    for kind in OP_KINDS:
        expected_delta[kind] = (
            sum(1 for i in plans
                if plans[i]["kind"] == kind and plans[i]["op"] == "add")
            - sum(1 for i in plans
                  if plans[i]["kind"] == kind and plans[i]["op"] == "delete"))
    delta = {k: copper_after["counts"][_COUNT_KEY[k]]
             - copper_before["counts"][_COUNT_KEY[k]] for k in OP_KINDS}
    guard["counts_delta"] = delta
    guard["counts_expected_delta"] = expected_delta
    guard["counts_ok"] = (delta == expected_delta)
    if guard["counts_ok"]:
        guard["checks"].append("counts_reconcile_ok")
    else:
        guard["ok"] = False
        reason_guard.append("structural_guard_failed: counts_delta=%s 期望=%s"
                            % (delta, expected_delta))

    # 3a. 目标操作确实生效（重解析后按跨度/键复核对象事实）
    im_after = copper_after["identity_map"]
    targets_ok = True
    for i in sorted(plans):
        plan = plans[i]
        kind, opt = plan["kind"], plan["op"]
        detail = {"index": i, "op": opt, "kind": kind, "ok": True,
                  "key": plan["key"], "new_key": None}
        if opt == "delete":
            if plan["key"] in im_after:
                detail["ok"] = False
                detail["detail"] = "删除后旧 key 仍在 identity_map"
        elif opt == "add":
            uuid = targets[i]["uuid"]
            im = im_after.get(uuid)
            if im is None or list(im["span"]) != list(node_final[i]):
                detail["ok"] = False
                detail["detail"] = ("新节点 uuid=%s 未在重解析 identity_map 中"
                                    "按跨度占位（身份键撞键？）" % uuid)
            else:
                entry = _kind_entries(copper_after, kind)[im["index"]]
                bad = [f for f in _NEW_REQUIRED[kind]
                       if _quantize(kind, f, entry[f])
                       != _quantize(kind, f, targets[i]["facts"][f])]
                if kind == "zone":
                    bad += _zone_param_diffs(
                        targets[i]["facts"].get("params") or {},
                        entry.get("params") or {}, require_all=True)
                if bad:
                    detail["ok"] = False
                    detail["detail"] = "新节点事实与请求不符: %s" % bad
                else:
                    detail["new_key"] = uuid
        else:
            span = node_final[i]
            hit = [k for k, v in im_after.items()
                   if list(v["span"]) == list(span)]
            if len(hit) != 1:
                detail["ok"] = False
                detail["detail"] = ("新节点跨度 %s 在 identity_map 中命中 %d 条"
                                    % (span, len(hit)))
            else:
                new_key = hit[0]
                entry = _kind_entries(copper_after, kind)[
                    im_after[new_key]["index"]]
                bad = [f for f in _NEW_REQUIRED[kind]
                       if _quantize(kind, f, entry[f])
                       != _quantize(kind, f, targets[i]["facts"][f])]
                if kind == "zone":
                    bad += _zone_param_diffs(
                        (targets[i].get("changes") or {}).get("params") or {},
                        entry.get("params") or {}, require_all=True)
                if bad:
                    detail["ok"] = False
                    detail["detail"] = "改写后事实与请求不符: %s" % bad
                else:
                    detail["new_key"] = new_key
                    for rec in affected_keys:
                        if rec["index"] == i and rec["op"] == "modify":
                            rec["new_key"] = new_key
        if not detail["ok"]:
            targets_ok = False
            reason_guard.append("structural_guard_failed: op[%d] %s %s"
                                % (i, opt, detail.get("detail", "")))
        guard["target_details"].append(detail)
    guard["targets_ok"] = targets_ok
    if targets_ok:
        guard["checks"].append("targets_effective_ok")

    # 3b. 字节保真实证：两侧摘除目标跨度后逐字相同
    new_spans = [target_final[i] for i in sorted(target_final)]
    unchanged = None
    if len(new_spans) != len(set(map(tuple, new_spans))):
        guard["ok"] = False
        reason_guard.append("structural_guard_failed: 新文本目标跨度重叠")
    else:
        orig_wo = _remove_spans(board_text, old_spans)
        final_wo = _remove_spans(final_text, new_spans)
        if orig_wo is None or final_wo is None:
            guard["ok"] = False
            reason_guard.append("structural_guard_failed: 目标跨度重叠/越界，"
                                "无法实证字节保真")
        else:
            unchanged = (orig_wo == final_wo)
            if unchanged:
                guard["checks"].append("bytes_preserved_outside_targets_ok")
            else:
                guard["ok"] = False
                reason_guard.append("structural_guard_failed: "
                                    "unchanged_bytes_outside_targets=False")

    # 3c. uuid 多重度变化（信息性；P1a v2 key 规则的既有后果）
    mult_before, mult_after = {}, {}
    for src, mult in ((copper_before, mult_before), (copper_after, mult_after)):
        for kind in OP_KINDS:
            for e in _kind_entries(src, kind):
                if e["uuid"]:
                    mult[e["uuid"]] = mult.get(e["uuid"], 0) + 1
    mult_changes = []
    for u in sorted(set(mult_before) | set(mult_after)):
        b, a = mult_before.get(u, 0), mult_after.get(u, 0)
        if b != a:
            mult_changes.append({"uuid": u, "mult_before": b, "mult_after": a})

    ledger_extra["uuid_mult_changes"] = mult_changes

    # 3d. zone 填充：用 copper_model 独立复核"填充指纹与点数改前改后一致"
    #     （本模块的 fill_sha256 是**节点子串**的 sha；这里是 copper_model 按
    #     自身口径算的填充几何指纹，两条独立证据同时进 ledger）。
    #     SEC-A-05 修复（REPAIR-P3S W-A）：复核不可得的 modify 记录按
    #     unverifiable fail-closed，不再静默放行。
    zf_reason = _zone_fill_model_audit(copper_before, copper_after,
                                       zone_fill_records)
    if zf_reason:
        guard["ok"] = False
        reason_guard.append(zf_reason)
    if reason_guard:
        ledger_extra["guard"] = guard
        ledger_extra["unchanged"] = unchanged
        ledger_extra["zone_fill_summary"] = _zone_fill_summary(zone_fill_records)
        reasons_by_op[-2] = reason_guard
    if any(reasons_by_op.values()):
        return _blocked(ops_total, node_eol, reasons_by_op, ledger_extra)

    op_spans = []
    for i in sorted(plans):
        rec = records.get(i, {})
        op_spans.append({
            "index": i, "op": plans[i]["op"], "kind": plans[i]["kind"],
            "key": plans[i]["key"],
            "orig_target_span": list(rec["orig"]) if rec.get("orig") else None,
            "final_target_span": target_final.get(i),
            "final_node_span": node_final.get(i),
        })
    ledger = _make_ledger(
        ops_total, node_eol, ops_applied=ops_total, adds=applied["adds"],
        modifies=applied["modifies"], deletes=applied["deletes"],
        ops_requested=ops_requested, affected_keys=affected_keys,
        counts_before=dict(copper_before["counts"]),
        counts_after=dict(copper_after["counts"]), unchanged=unchanged,
        guard=guard, op_spans=op_spans, uuid_mult_changes=mult_changes,
        unrep_before=len(copper_before["unrepresentable"]),
        unrep_after=len(copper_after["unrepresentable"]),
        zone_fill=zone_fill_records,
        zone_fill_summary=_zone_fill_summary(zone_fill_records))
    return {"ok": True, "verdict": "accepted", "reasons": [],
            "board_text": final_text, "ledger": ledger}
