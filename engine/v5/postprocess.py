# -*- coding: utf-8 -*-
"""V5-R8 布线后处理最小三件包（v5.postprocess/2.1.0）。

任务书=V5-R8-POSTPROCESS-MINPACK-TB2-2026-10-04.md（§2 D-1..D-8）承继
09-24 终稿（V5-R8-POSTPROCESS-MINPACK-TASKBOOK-2026-09-24.md W-2）。纯函数
``postprocess_routes(board, doc) → (new_doc, provenance)``：executor 产出的
v5.routes.v1 工件在导出前的确定性等价化简——不改 A* 搜索语义（后处理与
搜索解耦=设计不变量）；无时钟/无随机，一切枚举排序确定（同输入同输出）。

三原语（处理序=**组间序**（v2.1 大板策略：组候选收益总量降序，并列按
net id 字典序——确定性锚不变）→ **组内处理序** entry 路径序 → 原语序
P1→P2a→P2b→P3，逐网相位制：每网先全 entry 跑 P1 再 P2a 再 P2b 最后 P3；
组内循环至组不动点，上限 ``MAX_ROUNDS``=8 轮/组，超限 fail-closed 披露
停线——provenance.fixpoint.converged=False 如实记账）：

  P1   精确共线合并（几何不变类，D-3）：entry 内连续共线且中间点**严格
       介于**两邻点之间的顶点撤除；覆盖线段集恒等（数学不变式）→ **免逐
       动作复检**，终局单次全量 check_routes 兜底。
  P2a  共线往返对消（D-3）：中间点在两邻点同侧（迹严格收缩）——与 P1
       同一扫描两分类记账；逐动作全量复检=route_check.check_routes，
       违例回退该动作并留痕。
  P2b  同向台阶压缩+反向步对消（D-4）：四连顶点 A,B,C,D，AB∥CD 同向、
       BC 垂直（曼哈顿路径）→ A,E,D（E=AB 轴向式：AB 水平→(D.x,A.y)、
       AB 垂直→(A.x,D.y)）；逐动作全量复检+违例回退留痕。
  P3   冗余 via 删减（D-5）：(a) 同网同坐标 via 对——现役 D3 孔心距约束下
       结构性不可能，实现为检测+如实报 0（防御面，见
       ``detect_colocated_via_pairs``）；(b) 零净换层消除：同网相邻三
       entry 链 e_k(A 层,尾 via T1)→e_{k+1}(B 层,恰两 tv=T1/T2)→e_{k+2}
       (A 层,头 via T2)，删 T1/T2 及**各自回流孔**、删 e_{k+1}、外层 L 形
       拼接（**先 x 后 y** 确定性）；逐动作全量复检。

回流对不可拆守卫（R4 契约结构=本批关键风险，09-24 §4）：任何 via 删减
动作必同时移除其 return_via 且反之禁止单独删 return_via——
``assert_return_pair_guard(before, after)``（孔位披露计数差集严格成对
断言）在每个 P3 动作落位后运行，反面钉值例见 tests/test_postprocess_minpack.py。

保护集（D-2，拐角原语 P1/P2a/P2b 禁触顶点）：每 entry 折线顶点 i 受保护
⟺ i∈{0,n−1} ∨ 坐标∈该 entry transition_vias∪return_vias ∨ (i=1 ∧ v₀∈
via 集) ∨ (i=n−2 ∧ v_{n−1}∈via 集)——后两条即 **[T,R,T] 回流桩折返**
（R 恒在索引 1/n−2；executor ``_entries_from_runs`` 头桩 poly[:3]=
[T,R,T]/尾桩 poly[-3:]=[T,R,T] 构造式坐实）。首末顶点恒保护=分区端点贴回
与 kicad_export ``_aligned`` 网级真端点对齐的输入。

字节保真纪律：判定用键化坐标（_pt 舍入 9 位）只做比较，**幸存顶点一律
保留原浮点对象**（网格算术残差如 87.69999999999999 不被规范化）；新引入
点（P2b 拐点 E、P3 拼接腿）为动作产物的新几何值。changed=False 时 new_doc
与输入逐字节相等（不加 negotiation_log 行、不写 provenance.postprocess
标记——幂等二遍零改=D-6 构造性成立，钉值测试证）。

首版保守边界（D-7，披露性非目标）：近共线合并不入首版；跨 entry 合并
不入首版（09-24「同网同层同宽」按 entry 内落定；P3(b) 的三 entry 链消除
是 via 删减原语、非形状合并）；圆弧化/泪滴/平滑重布=非目标照旧。
ribbon（copper_band）与既布（ptype=ROUTED）分区的 entry=固定铜声明：
四原语一律跳过（声明面与物理铜的一致性无逐段审计可证化简等价——
fail-closed 不动；14 板基线实测 routed entry 零触及该类分区，纯防御面）。

预算与终检（TB2 §3 派生）：每板几何动作预算 ``ACTION_BUDGET``=4000（尝试
即计：落位与回退各耗一次动作面——回退留几何零改但耗一次全量复检；超限停
该板简化、provenance.budget.capped=True，终检仍全量跑。封顶板不在不动点
——postprocess(final) 可继续化简（每调用独立预算）；双跑确定性=同输入同
输出，不受影响）；终局单次全量 check_routes 兜底——feasible 且违例计数
不增于 raw 基线才放行；不过则先走**逐 entry 救援通道**（R8 第 1 轮判读
修复，2026-10-04：根因=route_check R6 逐段 bbox 近似对合并后长斜段的假
阳性——真线距净空但 bbox 交叠，syn-r07/r10 两板 P1 收益全损；route_check
在世界白名单外不动，故在白名单内按 09-24 W-2「违例则回退**该次**简化并
留痕」把整体回退细化到 entry 粒度）：从 raw 重建、P1 换 entry 粒度复检
（每 entry 合并完做一次全量复检，不过则回退该 entry 全部合并并留痕+memo
防重试）、P2a/P2b/P3 照旧逐动作复检，救援后再做一次终局全量兜底；救援
零收益（applied=0）或救援终检不过 → 整体回退 raw（fail-closed 语义不
变；provenance.rescue 如实记账，reverted_all=True 语义=无净变化）。
changed 以几何实际变化判定（救援全回退 ⇒ 输出==raw ⇒ changed=False，
不加 negotiation_log 行——幂等二遍零改对救援通道同样构造性成立）。

v2 最小核（OPT-18 E2a，EXEC-R10-E2A 任务书 2026-10-14；设计正本
EXEC-R10-E1-REPORT §3.2–§3.4）：四原语升格显式 pass 记录（处理序契约
不变）——每 pass 独立势读数 phi/delta/hash（H_0..H_4=canonical_sha256
链，复用 v5.canonical.canonical_sha256 零新基建）+单调势断言
（applied>0 ⇒ ΔΦ_main<0，失效抛 PotentialMonotonicityError=fail-closed；
主势：P1/P2a/P2b=Φ_V 内部顶点数、P3=Φ_E entry 数，E1 §3.2 表）+
termination/budget/feasibility/determinism+idempotency 四门分离状态机
（termination.status ∈ CONVERGED / NOT_CONVERGED_BUDGET /
NOT_CONVERGED_ROUNDS / ERROR——not_converged 仅 NOT_CONVERGED_* 两态；
residual_candidates=终态结构候选机械枚举，O(V) 不耗动作预算；E2a 时
预算结构=全局单池 ACTION_BUDGET=4000，v2.1 起 per-pass 分池（见下））。
幂等主张前置=
termination.status=CONVERGED（determinism/idempotency 模块内恒 null，
权威=跑器/验收工装）。

v2.1 大板策略（OPT-18 E2b，EXEC-R10-E2B 任务书 2026-10-15；设计正本
EXEC-R10-E1-REPORT §3.5+§3.4，策略层叠加、provenance v2 契约兼容——
既有字段语义零改动，新增面纯加性）：
  - **候选枚举/执行分离**：入场全量候选枚举（O(V) 结构判定，不耗动作
    预算），产出描述子 (pass, net, entry_idx, pos, ΔΦ, needs_recheck)
    ——``_enumerate_candidates``；residual_candidates（E2a 面）=其计数
    聚合，语义逐位不变；
  - **收益密度排序**：执行序=组候选收益总量降序（ΔΦ/cost：cost(P1)=ε
    免复检⇒密度∞——由组内相位序 P1 先清场承载；P2a/P2b/P3=1 复检单位，
    per-pass 分池防饿死）；排序键全部由输入决定（无时钟无随机）；
  - **per-net 局部固定点**：net 分组内四原语至组内不动点（组内处理序
    不变=确定性契约硬门）；预算耗尽⇒已完成组 CONVERGED 保持、未完成组
    整组 NOT_CONVERGED_BUDGET——termination.by_net 组粒度披露；
  - **断点续跑面**：入场枚举零候选组跳过不重扫（枚举即断点状态——
    四原语均 net 内几何动作，组间结构独立；per-call 独立预算沿 v1 语义
    ⇒ 二次调用=续跑消费残量）；provenance.strategy 记枚举/组序/跳过面，
    残留描述子全单=跑器侧 ``enumerate_candidates`` 落盘；
  - **预算分池**：per-pass 固定池 B_P1=2800/B_P2a=600/B_P2b=200/B_P3=400
    （总 4000 与 v1 ACTION_BUDGET 对齐；冻结值，自适应变体另批）；
    救援子状态机独立全额池（语义不变）；``budget=`` 标量按原语序顺序
    装填、字典=显式 per-pass。
"""
import copy
import math

from .canonical import canonical_json, canonical_sha256
from .route_check import ROUTE_CHECK_VERSION, RouteCheckError, check_routes

POSTPROCESS_VERSION = "v5.postprocess/2.1.0"

# D-6：不动点轮上限（fail-closed 披露停线；v2.1 起界组内循环）。
MAX_ROUNDS = 8
# 每板几何动作预算（只计落位动作；超限停该板简化，终检仍全量跑）。
ACTION_BUDGET = 4000
# v2.1 per-pass 分池（R10E2B-E，E1 §3.4/§4.1 冻结值；总 4000 与
# ACTION_BUDGET 对齐）：每调用刷新；救援子状态机独立全额池。
PASS_BUDGETS = {"P1": 2800, "P2a": 600, "P2b": 200, "P3": 400}
# D-5(a) 同位对检测的结构上界：一个物理孔位的合法披露方（不同 entry 数）
# ≤3（两侧衔接 entry + 提升桩 entry；14 板基线实测全部=2）。
MAX_LEGIT_DISCLOSURE = 3

_COLINEAR_EPS = 1e-9    # 几何精确共线的浮点噪声容差（坐标 ~1e2、积 ~1e1 量级）
_BETWEEN_EPS = 1e-12    # 「严格介于/严格同侧」的零点容差
_COORD_ROUND = 9        # 坐标键舍入（与 route_check 层连通审计 _key 同精度）

_PRIMS = ("P1", "P2a", "P2b", "P3")


class PostprocessGuardError(AssertionError):
    """回流对不可拆守卫违例（D-5：删过渡孔未同时删其回流孔/单删回流孔）。"""


class PotentialMonotonicityError(AssertionError):
    """单调势断言失效（OPT-18 T4：applied>0 而 ΔΦ_main 未严格下降=程序
    缺陷，fail-closed 抛出停线）。"""


def _f(x):
    return float(x)


def _pt(p):
    return (round(_f(p[0]), _COORD_ROUND), round(_f(p[1]), _COORD_ROUND))


# ---------------------------------------------------------------- 保护集

def _via_pts(entry):
    out = set()
    for key in ("transition_vias", "return_vias"):
        for p in entry.get(key) or []:
            out.add(_pt(p))
    return out


def _protected(poly, i, via_pts):
    """D-2 保护集判定（poly=键化坐标序列；live 索引）。"""
    n = len(poly)
    if i == 0 or i == n - 1:
        return True
    if poly[i] in via_pts:
        return True
    if i == 1 and poly[0] in via_pts:
        return True
    if i == n - 2 and poly[-1] in via_pts:
        return True
    return False


def _colin_class(a, b, c):
    """三点共线分类：+1=b 严格介于两邻点（P1）/ −1=b 在两邻点同侧（P2a）/
    0=不共线或零距退化（不动）。"""
    cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
    if abs(cross) > _COLINEAR_EPS:
        return 0
    dot = (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])
    if dot > _BETWEEN_EPS:
        return 1
    if dot < -_BETWEEN_EPS:
        return -1
    return 0


# ---------------------------------------------------------------- P2b 几何

def _stair_quadruple(a, b, c, d):
    """D-4 台阶判定：AB、CD 非零且平行同向，BC 非零且垂直 AB。"""
    ab = (b[0] - a[0], b[1] - a[1])
    bc = (c[0] - b[0], c[1] - b[1])
    cd = (d[0] - c[0], d[1] - c[1])
    if (abs(ab[0]) <= _COLINEAR_EPS and abs(ab[1]) <= _COLINEAR_EPS) or \
            (abs(bc[0]) <= _COLINEAR_EPS and abs(bc[1]) <= _COLINEAR_EPS) or \
            (abs(cd[0]) <= _COLINEAR_EPS and abs(cd[1]) <= _COLINEAR_EPS):
        return False
    if abs(ab[0] * cd[1] - ab[1] * cd[0]) > _COLINEAR_EPS or \
            ab[0] * cd[0] + ab[1] * cd[1] <= 0.0:
        return False
    return abs(ab[0] * bc[0] + ab[1] * bc[1]) <= _COLINEAR_EPS


def _stair_mid(a, b, d):
    """P2b 台阶压缩拐点 E（AB 轴向式，先走 AB 轴向腿）：一般式
    E=A+((D−A)·v)/|v|²·v（v=AB；AB 水平→(D.x,A.y)、垂直→(A.x,D.y) 的统一
    表达）。退化（E∈{A,D}）返回 None（不动作）。"""
    vx, vy = b[0] - a[0], b[1] - a[1]
    n2 = vx * vx + vy * vy
    if n2 <= 0.0:
        return None
    t = ((d[0] - a[0]) * vx + (d[1] - a[1]) * vy) / n2
    e = (a[0] + t * vx, a[1] + t * vy)
    if (abs(e[0] - a[0]) <= _COLINEAR_EPS
            and abs(e[1] - a[1]) <= _COLINEAR_EPS) or \
            (abs(e[0] - d[0]) <= _COLINEAR_EPS
             and abs(e[1] - d[1]) <= _COLINEAR_EPS):
        return None
    return e


# ---------------------------------------------------------------- P3 结构

def detect_colocated_via_pairs(doc):
    """D-5(a) 同网同坐标 via 对检测（防御面）：同一 (net, 孔位) 被超过
    ``MAX_LEGIT_DISCLOSURE`` 个不同 entry 披露 → 同位对（现役 D3 孔心距
    约束下结构性不可能，预期恒空、如实报数）。返回排序 (net, 孔位) 列表。"""
    disc = {}
    for i, entry in enumerate(doc.get("routes") or []):
        for key in ("transition_vias", "return_vias"):
            for p in entry.get(key) or []:
                disc.setdefault((str(entry.get("net_id", "")), _pt(p)),
                                set()).add(i)
    return sorted((nid, pt) for (nid, pt), idxs in disc.items()
                  if len(idxs) > MAX_LEGIT_DISCLOSURE)


def _return_partners(routes):
    """(net_id, 过渡孔位) → 回流孔位：从 [T,R,T] 桩结构推导（头桩 poly[:3]
    与尾桩 poly[-3:]，tv/rv 平行表交叉核对），首现序确定性。"""
    partners = {}
    for entry in routes:
        tv = [_pt(p) for p in entry.get("transition_vias") or []]
        rv = [_pt(p) for p in entry.get("return_vias") or []]
        poly = [_pt(p) for p in entry.get("polyline") or []]
        for t, r in zip(tv, rv):
            if len(poly) >= 3 and poly[0] == t and poly[1] == r and poly[2] == t:
                partners.setdefault((str(entry.get("net_id", "")), t), r)
            if len(poly) >= 3 and poly[-1] == t and poly[-2] == r \
                    and poly[-3] == t:
                partners.setdefault((str(entry.get("net_id", "")), t), r)
    return partners


def _via_counts(routes):
    """孔位披露计数：(net, 孔位, kind) → 次数（tv/rv 分开计）。"""
    out = {}
    for entry in routes:
        for key in ("transition_vias", "return_vias"):
            for p in entry.get(key) or []:
                k = (str(entry.get("net_id", "")), _pt(p), key)
                out[k] = out.get(k, 0) + 1
    return out


def assert_return_pair_guard(before_routes, after_routes):
    """回流对不可拆守卫断言（D-5）：before→after 的孔位披露差集必须严格
    成对——每个被删过渡孔的配对回流孔必**等量**同删，且每个被删回流孔必是
    某被删过渡孔的配对（禁止单删回流孔）。违例抛 PostprocessGuardError。

    接受 routes 列表或整个 doc（dict 时取 ``["routes"]``）。"""
    br = before_routes.get("routes") if isinstance(before_routes, dict) \
        else before_routes
    ar = after_routes.get("routes") if isinstance(after_routes, dict) \
        else after_routes
    before, after = _via_counts(br), _via_counts(ar)
    removed_t, removed_r = {}, {}
    for k in set(before) | set(after):
        d = before.get(k, 0) - after.get(k, 0)
        if d <= 0:
            continue
        (nid, pt, kind) = k
        (removed_t if kind == "transition_vias" else removed_r)[(nid, pt)] = d
    partners = _return_partners(br)
    legit_r = {}
    for (nid, pt), d in sorted(removed_t.items()):
        r = partners.get((nid, pt))
        if r is None:
            raise PostprocessGuardError(
                "回流对守卫：被删过渡孔 %s@%s 无 [T,R,T] 桩配对可证（拒删）"
                % (nid, [pt[0], pt[1]]))
        if removed_r.get((nid, r), 0) != d:
            raise PostprocessGuardError(
                "回流对守卫：过渡孔 %s@%s 删量 %d 未与配对回流孔 %s 等量同删"
                "（删过渡孔必同时删其回流孔）"
                % (nid, [pt[0], pt[1]], d, [r[0], r[1]]))
        legit_r[(nid, r)] = legit_r.get((nid, r), 0) + d
    for (nid, pt), d in sorted(removed_r.items()):
        if legit_r.get((nid, pt), 0) != d:
            raise PostprocessGuardError(
                "回流对守卫：回流孔 %s@%s 被单独删除/删量不配（配对过渡孔侧"
                "合法删量=%d，回流孔删量=%d；禁止单删回流孔）"
                % (nid, [pt[0], pt[1]], legit_r.get((nid, pt), 0), d))
    return True


def _entry_head_tail_vias(entry):
    """结构化 (头桩, 尾桩)：头桩=(tv[0], rv[0]) 当 poly[:3]=[tv0,rv0,tv0]；
    尾桩=(tv[-1], rv[-1]) 当 poly[-3:]=[tv-1,rv-1,tv-1]。形状不符的端为
    None（防御面，调用方跳过动作）。tv/rv 空或折线过短返回 (None, None)。"""
    tv = [_pt(p) for p in entry.get("transition_vias") or []]
    rv = [_pt(p) for p in entry.get("return_vias") or []]
    poly = [_pt(p) for p in entry.get("polyline") or []]
    if len(tv) != len(rv) or not tv or len(poly) < 3:
        return None, None
    head = tail = None
    if poly[0] == tv[0] and poly[1] == rv[0] and poly[2] == tv[0]:
        head = (tv[0], rv[0])
    if poly[-1] == tv[-1] and poly[-2] == rv[-1] and poly[-3] == tv[-1]:
        tail = (tv[-1], rv[-1])
    return head, tail


# ---------------------------------------------------------------- 指标

def _dir_of(a, b):
    if a == b:
        return None
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return (round(dx / n, _COORD_ROUND), round(dy / n, _COORD_ROUND))


def _metrics(doc):
    """W-3 对账口径：entries / 顶点数 / 真拐角（方向变化数）/ via 净位
    （(net,孔位) 去重）/ 总长（mm，4 位舍入）/ tv·rv 原始披露数。"""
    entries = doc.get("routes") or []
    verts = corners = 0
    length = 0.0
    tv = rv = 0
    via_pts = set()
    for e in entries:
        pts = [_pt(p) for p in e.get("polyline") or []]
        verts += len(pts)
        for i in range(1, len(pts) - 1):
            d0, d1 = _dir_of(pts[i - 1], pts[i]), _dir_of(pts[i], pts[i + 1])
            if d0 is not None and d1 is not None and d0 != d1:
                corners += 1
        for a, b in zip(pts, pts[1:]):
            length += math.hypot(b[0] - a[0], b[1] - a[1])
        for p in e.get("transition_vias") or []:
            tv += 1
            via_pts.add((str(e.get("net_id", "")), _pt(p)))
        for p in e.get("return_vias") or []:
            rv += 1
            via_pts.add((str(e.get("net_id", "")), _pt(p)))
    return {"entries": len(entries), "vertices": verts, "corners": corners,
            "length_mm": round(length, 4), "transition_vias_raw": tv,
            "return_vias_raw": rv, "vias_unique_net_scoped": len(via_pts)}


# ---------------------------------------------------------------- 势函数（v2）

# 每 pass 主势（E1 §3.2 表逐字锚：P1/P2a/P2b=Φ_V 内部顶点、P3=Φ_E entry）。
_PASS_MAIN_POTENTIAL = {"P1": "vertices_interior", "P2a": "vertices_interior",
                        "P2b": "vertices_interior", "P3": "entries"}


def _potentials(doc):
    """五势读数（E1 §3.2，全锚现有对账口径）：Φ_V=内部顶点数
    sum(max(0,len(poly)−2))（r8_run 桥字段口径）/Φ_E=entry 数/Φ_T=via 净位
    （(net,孔位) 去重=_metrics.vias_unique_net_scoped）/Φ_C=真拐角（方向
    变化数，报告级）/Φ_L=总长 mm（4 位舍入，只报不判）+总顶点数（delta
    归属对账用）。"""
    m = _metrics(doc)
    interior = sum(max(0, len(e.get("polyline") or []) - 2)
                   for e in doc.get("routes") or [])
    return {"vertices": m["vertices"], "vertices_interior": interior,
            "entries": m["entries"],
            "via_net_positions": m["vias_unique_net_scoped"],
            "corners": m["corners"], "length_mm": m["length_mm"]}


def _assert_pass_monotonic(prim, delta, applied):
    """T4 单调势断言（纯函数钉值面）：applied>0 ⇒ ΔΦ_main<0；失效抛
    PotentialMonotonicityError（fail-closed）。delta 取该 pass 该轮效应数
    {主势键: Δ值}。"""
    if applied > 0:
        main = _PASS_MAIN_POTENTIAL[prim]
        if not delta[main] < 0:
            raise PotentialMonotonicityError(
                "单调势断言失效：%s applied=%d 而 ΔΦ_main(%s)=%r 未严格下降"
                % (prim, applied, main, delta.get(main)))


def _assert_lex_decrease(phi_before, phi_after):
    """终止定理轮级断言（E1 §3.2）：任一轮有成功动作 ⇒ 字典序三元组
    (Φ_V, Φ_E, Φ_T) 严格下降；失效抛=fail-closed。"""
    keys = ("vertices_interior", "entries", "via_net_positions")
    a = tuple(phi_before[k] for k in keys)
    b = tuple(phi_after[k] for k in keys)
    if not b < a:
        raise PotentialMonotonicityError(
            "终止定理断言失效：(Φ_V,Φ_E,Φ_T) %r→%r 未严格下降" % (a, b))


# ------------------------------------------------ 四门状态机（v2，termination）

_TERMINATION_SEVERITY = {"CONVERGED": 0, "NOT_CONVERGED_BUDGET": 1,
                         "NOT_CONVERGED_ROUNDS": 2, "ERROR": 3}


def _pass_termination_status(residual, capped, rounds_exhausted):
    """per-pass termination 状态机（E1 §3.4，纯函数钉值面）：以候选面为
    准、不以预算余量为准（预算恰好耗尽但候选清空 ⇒ CONVERGED）；
    not_converged 仅 NOT_CONVERGED_* 两态（预算耗尽优先于轮超限=proximate
    break 原因；轮超限=防御位 fail-closed 披露）。"""
    if residual == 0:
        return "CONVERGED"
    if capped:
        return "NOT_CONVERGED_BUDGET"
    if rounds_exhausted:
        return "NOT_CONVERGED_ROUNDS"
    return "CONVERGED"   # 收敛轮+残留候选=枚举器与扫描面分歧（防御披露，
                         # 理论不可达；residual_candidates 如实记数供 lint）


def _enumerate_candidates(work, ribbon_like, memo,
                          include_self_rejecting=False):
    """R10E2B-A 候选枚举器（E1 §3.5.1）：对四 pass 的扫描条件做纯结构
    判定（O(V)，不耗动作预算、不触碰几何），产出候选描述子清单
    (pass, net, entry_idx, pos, ΔΦ, needs_recheck)——确定性枚举序=
    entry 路径序→原语序（P1/P2a/P2b 按位）→P3 链序；memo 命中=已尝试
    回退不重试=非可行动作；退化拐点=结构性拒发=非可行动作。
    ΔΦ=该 pass 主势单位（E1 §3.2 表：P1/P2a/P2b=Φ_V 每动作 −1、
    P3=Φ_E 每动作 −2）；needs_recheck=是否耗复检单位（P1=ε 免复检）。

    include_self_rejecting=True（入场跳过判定专用模式）：P2a 塌缩守卫
    自拒形态（对消致折线塌缩）以 self_rejecting=True 计入——扫描留痕面
    parity（该形态在扫描器中留 reverted 留痕不耗预算）；默认 False=可
    行动作面（收益/残量口径，与 E2a residual_candidates 语义逐位一致）。"""
    routes = work["routes"]
    out = []
    for idx, entry in enumerate(routes):
        rib = entry.get("partition_id") in ribbon_like
        key = [_pt(p) for p in entry.get("polyline") or []]
        if len(key) < 3:
            continue
        vias = _via_pts(entry)
        net, layer = entry.get("net_id"), entry.get("layer")
        p1_blocked = ("P1e", str(net), str(layer), tuple(key)) in memo
        p1_pos, p2a_pos = [], []
        for i in range(1, len(key) - 1):
            if not rib and not p1_blocked \
                    and _colin_class(key[i - 1], key[i], key[i + 1]) == 1 \
                    and not _protected(key, i, vias):
                p1_pos.append(i)
            a, b, c = key[i - 1], key[i], key[i + 1]
            sig = ("P2a", str(net), str(layer), a, b, c)
            if rib or sig in memo or _protected(key, i, vias) \
                    or _colin_class(a, b, c) != -1:
                continue
            nk = []
            for p in key[:i] + key[i + 1:]:   # 衔接重合点对消（塌缩守卫镜像）
                if nk and nk[-1] == p:
                    continue
                nk.append(p)
            if len(nk) < 2 or (nk[0] == nk[-1] and key[0] != key[-1]):
                if include_self_rejecting:
                    p2a_pos.append((i, True))   # 自拒形态（留痕面 parity）
                continue
            p2a_pos.append((i, False))
        p2b_pos = []
        for i in range(0, len(key) - 3):
            a, b, c, d = key[i], key[i + 1], key[i + 2], key[i + 3]
            sig = ("P2b", str(net), str(layer), a, b, c, d)
            if rib or sig in memo or _protected(key, i + 1, vias) \
                    or _protected(key, i + 2, vias) \
                    or not _stair_quadruple(a, b, c, d):
                continue
            if _stair_mid(a, b, d) is None:
                continue
            p2b_pos.append(i)
        for pos in p1_pos:
            out.append({"pass": "P1", "net": str(net), "entry_idx": idx,
                        "pos": pos, "dphi": -1, "needs_recheck": False,
                        "self_rejecting": False})
        for pos, sr in p2a_pos:
            out.append({"pass": "P2a", "net": str(net), "entry_idx": idx,
                        "pos": pos, "dphi": -1, "needs_recheck": True,
                        "self_rejecting": sr})
        for pos in p2b_pos:
            out.append({"pass": "P2b", "net": str(net), "entry_idx": idx,
                        "pos": pos, "dphi": -1, "needs_recheck": True,
                        "self_rejecting": False})
    for k in range(max(0, len(routes) - 2)):
        act = _p3_build(routes, k)
        if act is None:
            continue
        sig = ("P3", str(routes[k].get("net_id")), act["t1"], act["t2"])
        if sig in memo:
            continue
        out.append({"pass": "P3", "net": str(routes[k].get("net_id")),
                    "entry_idx": k, "pos": k, "dphi": -2,
                    "needs_recheck": True, "self_rejecting": False})
    return out


def _count_residual_candidates(work, ribbon_like, memo):
    """residual_candidates 机械枚举（E1 §3.4；v2.1 起=_enumerate_candidates
    的计数聚合面，判定条件与 E2a 逐位同源）。返回 {P1: n, P2a: n, P2b: n,
    P3: n}。"""
    out = {"P1": 0, "P2a": 0, "P2b": 0, "P3": 0}
    for c in _enumerate_candidates(work, ribbon_like, memo):
        out[c["pass"]] += 1
    return out


# ---------------------------------------------------------------- 记账

class _Acc:
    """provenance 累计器（类计数+逐动作留痕+回退备忘+预算+v2 pass 效应）。

    v2（OPT-18 E2a）：pass_delta 按 pass 累计成功动作的精确势效应
    （P1/P2a/P2b 每动作 −1 顶点/−1 内部顶点/entry 不变；P3 逐动作实测），
    供 per-pass delta 记录与轮级/终局归属对账（Σ效应==实测 ΔΦ）。

    v2.1（OPT-18 E2b）：全局单池→per-pass 分池（B_P1=2800/B_P2a=600/
    B_P2b=200/B_P3=400，总 4000 与 v1 ACTION_BUDGET 对齐）：每池独立
    「尝试即计」（落位与回退均耗一次该 pass 动作面），耗尽仅置该 pass
    capped=True（其余 pass 池不受影响——P2a/P2b/P3 不再被 P1 饿死）。"""

    def __init__(self, pools):
        self.counts = {p: {"applied": 0, "reverted": 0} for p in _PRIMS}
        self.log = []
        self.memo = set()
        self.pool_caps = {p: int(pools[p]) for p in _PRIMS}
        self.pools = dict(self.pool_caps)
        self.consumed = {p: 0 for p in _PRIMS}
        self.capped = {p: False for p in _PRIMS}
        self.pass_delta = {p: {"vertices": 0, "vertices_interior": 0,
                               "entries": 0, "via_net_positions": 0}
                           for p in _PRIMS}

    def record_effect(self, prim, dv, dvi, de, dt=0):
        """成功动作的精确势效应累计（回退动作几何零改不记）。"""
        d = self.pass_delta[prim]
        d["vertices"] += dv
        d["vertices_interior"] += dvi
        d["entries"] += de
        d["via_net_positions"] += dt

    def take(self, prim):
        """per-pass 预算取用（尝试即计：落位与回退均耗一次该 pass 动作面；
        回退动作留几何零改但耗一次全量复检面）：该 pass 池耗尽→仅置该
        pass capped=True 返回 False（停该 pass 扫描，终检仍跑）。"""
        if self.capped[prim]:
            return False
        if self.pools[prim] <= 0:
            self.capped[prim] = True
            return False
        self.pools[prim] -= 1
        self.consumed[prim] += 1
        return True

    def applied_total(self):
        return sum(c["applied"] for c in self.counts.values())

    def consumed_total(self):
        return sum(self.consumed.values())

    def remaining_total(self):
        return sum(self.pools.values())

    def cap_total(self):
        return self.consumed_total() + self.remaining_total()

    def any_capped(self):
        return any(self.capped.values())

    def all_pools_empty(self):
        return all(v <= 0 for v in self.pools.values())

    def pass_budget_view(self, prim):
        """per-pass budget 四字段（R10E2B-E 判据面）。"""
        return {"cap": self.pool_caps[prim], "consumed": self.consumed[prim],
                "applied": self.counts[prim]["applied"],
                "remaining": self.pools[prim], "capped": self.capped[prim]}

    def note(self, prim, status, net, layer, at, reason=""):
        self.log.append({"prim": prim, "status": status, "net": str(net),
                         "layer": str(layer),
                         "at": [round(_f(at[0]), 6), round(_f(at[1]), 6)]
                         if at else None,
                         "reason": reason})


def _recheck(board, doc, baseline_violations):
    """逐动作全量复检（D-3/D-4/D-5）：check_routes 全量重跑；可行且违例
    计数不增于 raw 基线才放行。返回 (ok, 摘要)。"""
    try:
        cr = check_routes(board, doc)
    except RouteCheckError as exc:
        return False, "RouteCheckError: %s" % exc
    viol = len(cr.get("violations") or [])
    ok = cr.get("feasible") is True and viol <= baseline_violations
    return ok, ("feasible=%s violations=%d（基线 %d）"
                % (cr.get("feasible"), viol, baseline_violations))


# ---------------------------------------------------------------- 原语实现

def _apply_p1(board, work, idx, acc, baseline_violations=None,
              entry_recheck=False):
    """P1 精确共线合并（几何不变类，免逐动作复检）。原位删点（幸存顶点
    浮点对象保真），逐顶点计动作/预算。

    entry_recheck=True（救援通道）：entry 内合并完后做一次全量复检，不过
    则回退该 entry 全部合并并留痕+memo（09-24 W-2「违例则回退**该次**简化
    并留痕」的 entry 粒度实现——D-3 整体回退对 R6 逐段 bbox 近似的假阳性
    面过粗：syn-r07/r10 长斜段真线距净空但 bbox 交叠被误判，收益全损）。"""
    entry = work["routes"][idx]
    raw = entry["polyline"]
    if len(raw) < 3:
        return
    key = [_pt(p) for p in raw]
    vias = _via_pts(entry)
    net, layer = entry.get("net_id"), entry.get("layer")
    sig = ("P1e", str(net), str(layer), tuple(key))
    if entry_recheck and sig in acc.memo:
        return                        # 已回退过的 entry 形态不重试
    snapshot = copy.deepcopy(raw) if entry_recheck else None
    removed = []
    i = 1
    while i < len(key) - 1:
        if _colin_class(key[i - 1], key[i], key[i + 1]) == 1 \
                and not _protected(key, i, vias):
            if not acc.take("P1"):
                break
            pt = key[i]
            removed.append(pt)
            del key[i]
            del raw[i]
            if not entry_recheck:     # 快速路逐顶点记账（既有行为逐位不变）
                acc.counts["P1"]["applied"] += 1
                acc.note("P1", "applied", net, layer, pt)
                acc.record_effect("P1", -1, -1, 0)   # v2：精确势效应
        else:
            i += 1
    if not removed or not entry_recheck:
        return
    ok, why = _recheck(board, work, baseline_violations)
    if ok:
        acc.counts["P1"]["applied"] += len(removed)
        for p in removed:
            acc.note("P1", "applied", net, layer, p)
        acc.record_effect("P1", -len(removed), -len(removed), 0)
    else:
        entry["polyline"] = snapshot
        acc.counts["P1"]["reverted"] += len(removed)
        acc.memo.add(sig)
        acc.note("P1", "reverted", net, layer, removed[0],
                 "entry 复检不过，回退该 entry 全部合并（%d 点）：%s"
                 % (len(removed), why))


def _apply_p2a(board, work, idx, ribbon_like, acc, baseline_violations):
    """P2a 共线往返对消（迹严格收缩；逐动作全量复检，违例回退留痕）。"""
    entry = work["routes"][idx]
    net, layer = entry.get("net_id"), entry.get("layer")
    i = 1
    while i < len(entry["polyline"]) - 1:
        raw = entry["polyline"]
        key = [_pt(p) for p in raw]
        if len(key) < 3:
            return
        vias = _via_pts(entry)
        a, b, c = key[i - 1], key[i], key[i + 1]
        sig = ("P2a", str(net), str(layer), a, b, c)
        if ribbon_like or sig in acc.memo or \
                _colin_class(a, b, c) != -1 or _protected(key, i, vias):
            i += 1
            continue
        k2 = key[:i] + key[i + 1:]
        raw2 = raw[:i] + raw[i + 1:]
        nk, nr = [], []
        for j, p in enumerate(k2):        # 衔接重合点对消（A==C 形态）
            if nk and nk[-1] == p:
                continue
            nk.append(p)
            nr.append(raw2[j])
        if len(nk) < 2 or (nk[0] == nk[-1] and key[0] != key[-1]):
            acc.counts["P2a"]["reverted"] += 1   # 结构性拒发（塌缩守卫）
            acc.memo.add(sig)
            acc.note("P2a", "reverted", net, layer, b,
                     "塌缩守卫：对消后折线塌缩（<2 点或新生零长 entry）")
            i += 1
            continue
        if not acc.take("P2a"):
            return
        snapshot = copy.deepcopy(raw)
        entry["polyline"] = nr
        ok, why = _recheck(board, work, baseline_violations)
        if ok:
            acc.counts["P2a"]["applied"] += 1
            acc.note("P2a", "applied", net, layer, b)
            acc.record_effect("P2a", -1, -1, 0)      # v2：精确势效应
        else:
            entry["polyline"] = snapshot
            acc.counts["P2a"]["reverted"] += 1
            acc.memo.add(sig)
            acc.note("P2a", "reverted", net, layer, b, why)
            i += 1


def _apply_p2b(board, work, idx, ribbon_like, acc, baseline_violations):
    """P2b 同向台阶压缩（曼哈顿等价；逐动作全量复检+违例回退留痕）。"""
    entry = work["routes"][idx]
    net, layer = entry.get("net_id"), entry.get("layer")
    i = 0
    while i + 3 < len(entry["polyline"]):
        raw = entry["polyline"]
        key = [_pt(p) for p in raw]
        if len(key) < 4:
            return
        vias = _via_pts(entry)
        a, b, c, d = key[i], key[i + 1], key[i + 2], key[i + 3]
        sig = ("P2b", str(net), str(layer), a, b, c, d)
        if ribbon_like or sig in acc.memo or \
                _protected(key, i + 1, vias) or _protected(key, i + 2, vias) \
                or not _stair_quadruple(a, b, c, d):
            i += 1
            continue
        e = _stair_mid(a, b, d)
        if e is None:
            acc.memo.add(sig)             # 退化拐点（E∈{A,D}）不动
            i += 1
            continue
        if not acc.take("P2b"):
            return
        snapshot = copy.deepcopy(raw)
        # A,B,C,D → A,E,D：幸存顶点 A/D 用原浮点对象，E 为新拐点
        entry["polyline"] = raw[:i] + [raw[i], [e[0], e[1]], raw[i + 3]] + \
            raw[i + 4:]
        ok, why = _recheck(board, work, baseline_violations)
        if ok:
            acc.counts["P2b"]["applied"] += 1
            acc.note("P2b", "applied", net, layer, b)
            acc.record_effect("P2b", -1, -1, 0)      # v2：精确势效应
        else:
            entry["polyline"] = snapshot
            acc.counts["P2b"]["reverted"] += 1
            acc.memo.add(sig)
            acc.note("P2b", "reverted", net, layer, b, why)
            i += 1


def _p3_build(routes, k):
    """P3(b) 零净换层候选构造：k,k+1,k+2=同网连续三 entry（entry 路径序）。
    命中返回动作描述（merged entry+孔位），否则 None。全部为结构判定，
    无几何歧义分支。"""
    ek, e1, e2 = routes[k], routes[k + 1], routes[k + 2]
    _, tail_k = _entry_head_tail_vias(ek)
    head_1, tail_1 = _entry_head_tail_vias(e1)
    head_2, _ = _entry_head_tail_vias(e2)
    if tail_k is None or head_1 is None or tail_1 is None or head_2 is None:
        return None
    t1, r1 = tail_k
    if head_1 != (t1, r1):
        return None                       # e_k↔e_{k+1} 衔接孔对不一致
    t2, r2 = tail_1
    if head_2 != (t2, r2):
        return None                       # e_{k+1}↔e_{k+2} 衔接孔对不一致
    tv1 = [_pt(p) for p in e1.get("transition_vias") or []]
    if len(tv1) != 2 or set(tv1) != {t1, t2}:
        return None                       # 恰两 tv=T1/T2（排除提升桩）
    if ek.get("layer") != e2.get("layer") or ek.get("layer") == e1.get("layer"):
        return None                       # 零净换层（A→B→A）
    if ek.get("topology_edge") != e1.get("topology_edge") or \
            ek.get("topology_edge") != e2.get("topology_edge"):
        return None                       # 多端网拓扑边覆盖守恒（合并守恒）
    if _f(ek.get("width", 0)) != _f(e2.get("width", 0)):
        return None
    pk = [_pt(p) for p in ek["polyline"]]
    p2 = [_pt(p) for p in e2["polyline"]]
    if len(pk) < 4 or len(p2) < 4:
        return None                       # [T,R,T] 桩外须有真实顶点
    x, w = pk[-4], p2[3]                  # 剥桩后的外层真实端点
    # 外层 L 形拼接（先 x 后 y，确定性；退化腿收拢为单段/空）
    splice = []
    if abs(w[0] - x[0]) > _COLINEAR_EPS and abs(w[1] - x[1]) > _COLINEAR_EPS:
        splice = [[w[0], x[1]], [w[0], w[1]]]
    elif abs(w[0] - x[0]) > _COLINEAR_EPS or abs(w[1] - x[1]) > _COLINEAR_EPS:
        splice = [[w[0], w[1]]]
    nr = ek["polyline"][:-3] + splice + e2["polyline"][3:]
    dedup = []                            # 衔接重合点收拢（原浮点保真）
    dedup_key = [_pt(p) for p in nr]
    for j, kp in enumerate(dedup_key):
        if dedup and dedup_key[j - 1] == kp:
            continue
        dedup.append(nr[j])
    if len(dedup) < 2:
        return None
    tv = (ek.get("transition_vias") or [])[:-1] + \
        (e2.get("transition_vias") or [])[1:]
    rv = (ek.get("return_vias") or [])[:-1] + \
        (e2.get("return_vias") or [])[1:]
    merged = {
        "partition_id": ek.get("partition_id"),
        "net_id": ek.get("net_id"),
        "layer": ek.get("layer"),
        "polyline": dedup,
        "width": ek.get("width"),
        "transition_vias": tv,
        "return_vias": rv,
    }
    if ek.get("topology_edge") is not None:
        merged["topology_edge"] = ek["topology_edge"]
    return {"merged": merged, "t1": t1, "t2": t2}


def _apply_p3(board, work, k, acc, baseline_violations):
    """P3 零净换层消除（逐动作全量复检+回流对守卫断言）。k=三链首 entry 的
    全局下标（该网 entry 路径序）。返回是否落位。"""
    routes = work["routes"]
    act = _p3_build(routes, k)
    if act is None:
        return False
    ek = routes[k]
    net, layer = ek.get("net_id"), ek.get("layer")
    sig = ("P3", str(net), act["t1"], act["t2"])
    if sig in acc.memo or not acc.take("P3"):
        return False
    pre = copy.deepcopy(routes)
    routes[k:k + 3] = [act["merged"]]
    assert_return_pair_guard(pre, routes)   # 回流对不可拆守卫（断言面）
    ok, why = _recheck(board, work, baseline_violations)
    if ok:
        acc.counts["P3"]["applied"] += 1
        acc.note("P3", "applied", net, layer, act["t1"],
                 "删 T1%s/T2%s 及各自回流孔、并三 entry" % ([act["t1"][0],
                                                             act["t1"][1]],
                                                            [act["t2"][0],
                                                             act["t2"][1]]))
        # v2：逐动作实测势效应（Φ_E 每动作 −2；Φ_V/Φ_T 由合并几何实测）
        mp = len(act["merged"].get("polyline") or [])
        ols = [len(pre[j].get("polyline") or []) for j in (k, k + 1, k + 2)]
        acc.record_effect(
            "P3", mp - sum(ols),
            max(0, mp - 2) - sum(max(0, n - 2) for n in ols), -2,
            _potentials({"routes": routes})["via_net_positions"]
            - _potentials({"routes": pre})["via_net_positions"])
        return True
    work["routes"][k:k + 1] = pre[k:k + 3]
    acc.counts["P3"]["reverted"] += 1
    acc.memo.add(sig)
    acc.note("P3", "reverted", net, layer, act["t1"], why)
    return False


# ---------------------------------------------------------------- 主入口

def _ribbon_like_pids(board):
    """ribbon（copper_band）∪ 既布（ptype=ROUTED）分区集合（声明面）。"""
    out = set()
    for p in board.get("partitions", []):
        geo = p.get("geometry") or {}
        if geo.get("copper_band") is not None or p.get("ptype") == "ROUTED":
            out.add(p.get("partition_id"))
    return out


def _net_group_round(board, work, nid, ribbon_like, acc, baseline_violations,
                     p1_entry_recheck):
    """单组单轮相位（组内处理序=entry 路径序→原语序 P1→P2a→P2b→P3，逐网
    相位制——v2.0.0 全局轮循环的逐网体逐位保持，v2.1 仅抽出为组内轮）。

    返回该轮各原语扫描终点快照 {prim: (hash, phi)}。"""
    sweep = {}
    for prim in ("P1", "P2a", "P2b"):
        idxs = [i for i, e in enumerate(work["routes"])
                if str(e.get("net_id", "")) == nid]
        for i in idxs:
            rib = work["routes"][i].get("partition_id") in ribbon_like
            if prim == "P1":
                if not rib:            # 声明面 P1 亦不动（零增益防扰）
                    _apply_p1(board, work, i, acc, baseline_violations,
                              p1_entry_recheck)
            elif prim == "P2a":
                _apply_p2a(board, work, i, rib, acc, baseline_violations)
            else:
                _apply_p2b(board, work, i, rib, acc, baseline_violations)
        sweep[prim] = (canonical_sha256({"routes": work["routes"]}),
                       _potentials(work))
    idxs = [i for i, e in enumerate(work["routes"])
            if str(e.get("net_id", "")) == nid]
    k = 0
    while k + 2 < len(idxs):
        if _apply_p3(board, work, idxs[k], acc, baseline_violations):
            idxs = [i for i, e in enumerate(work["routes"])
                    if str(e.get("net_id", "")) == nid]
        else:
            k += 1
    sweep["P3"] = (canonical_sha256({"routes": work["routes"]}),
                   _potentials(work))
    return sweep


def _fixpoint_loop(board, work, ribbon_like, acc, baseline_violations,
                   max_rounds, p1_entry_recheck):
    """D-6 处理序主循环（v2.1 大板策略，OPT-18 E2b；设计正本 E1 §3.5）：

    组间序=组候选收益总量降序（并列按 net 字典序——确定性锚不变）；
    组内处理序=entry 路径序→原语序 P1→P2a→P2b→P3 逐网相位制（v2.0.0
    契约逐位保持）循环至组内不动点（上限 max_rounds 轮/组，超限
    fail-closed 披露停线）。

    p1_entry_recheck=False=快速路（D-3 免逐动作复检——既有行为逐位不变）；
    True=救援通道（P1 每 entry 合并完做一次全量复检，不过回退该 entry）。

    v2.1 仪表化（在 v2.0.0 面上叠加，处理序硬门=组内序不变）：
      - 入场全量候选枚举（R10E2B-A）：O(V) 结构判定不耗动作预算，产出
        (pass, net, entry_idx, pos, ΔΦ, needs_recheck) 描述子+组收益总量；
      - 收益密度排序（R10E2B-B）：组间序=组收益总量降序；密度基
        ΔΦ/cost（cost(P1)=ε 免复检⇒密度∞——由组内相位序 P1 先清场承载；
        P2a/P2b/P3=1 复检单位——per-pass 分池防饿死）；排序键全部由输入
        决定（无时钟无随机）；
      - per-net 局部固定点（R10E2B-C）：预算耗尽⇒已完成组 CONVERGED
        保持、未完成组整组 NOT_CONVERGED_BUDGET（by_net 组粒度披露）；
      - 断点续跑面（R10E2B-D）：入场枚举零候选组跳过不重扫（枚举即断点
        状态）；per-pass 势读数/效应/终态快照与 hash 链 H_0..H_4 链式
        边界沿 v2.0.0 约定（链点=最末已执行组末轮各原语扫描终点——
        pass 级工作归属由 delta/phi 承载）；
      - 轮级（=组内轮）单调势断言（T4，fail-closed）：有成功动作 ⇒ 字典
        序三元组 (Φ_V,Φ_E,Φ_T) 严格下降 + 每 pass applied>0 ⇒ ΔΦ_main<0 +
        Σ pass 精确效应 == 实测 ΔΦ（归属对账）；终局对账 Σ pass delta ==
        实测 Φ(终态)−Φ(输入)；
      - termination 状态机（E1 §3.4）：终态结构候选机械枚举（不耗预算）
        ⇒ per-pass status + 板级 max_severity + per-net 组粒度终态。

    返回 (converged, rounds, v2)：v2={"passes", "hash_chain",
    "termination", "strategy"}；rounds=已执行组组内轮数最大值；
    converged=零动作轮确认披露（四门分离：termination 以候选面为准）。"""
    phi0 = _potentials(work)
    h0 = canonical_sha256({"routes": work["routes"]})
    # ---- R10E2B-A：入场全量候选枚举（O(V)，不耗动作预算）----
    # include_self_rejecting=True=原始结构模式面（跳过判定用——P2a 塌缩
    # 守卫自拒形态计入，保扫描留痕面 parity）；收益/组序=可行动作面。
    entry_cands = _enumerate_candidates(work, ribbon_like, frozenset(),
                                        include_self_rejecting=True)
    entry_by_net = {}
    entry_by_pass = {p: 0 for p in _PRIMS}
    self_rejecting_total = 0
    for c in entry_cands:
        rec = entry_by_net.setdefault(c["net"], {"benefit": 0, "raw": 0,
                                                 "by_pass": {p: 0
                                                             for p in _PRIMS}})
        rec["raw"] += 1
        if c["self_rejecting"]:
            self_rejecting_total += 1
            continue
        rec["benefit"] += -c["dphi"]
        rec["by_pass"][c["pass"]] += 1
        entry_by_pass[c["pass"]] += 1
    nets_all = sorted({str(e.get("net_id", "")) for e in work["routes"]})
    # ---- R10E2B-B/C：组间序=组候选收益总量降序（并列 net 字典序）----
    group_order = sorted(nets_all, key=lambda n: (
        -entry_by_net.get(n, {}).get("benefit", 0), n))
    groups_skipped = [n for n in group_order
                      if entry_by_net.get(n, {}).get("raw", 0) <= 0]
    groups_executed = []
    by_net = {}
    sweep = {}
    board_converged = True
    max_group_rounds = 0
    phi_cursor = phi0
    for nid in group_order:
        if entry_by_net.get(nid, {}).get("raw", 0) <= 0:
            # R10E2B-D 断点续跑面：零原始结构模式组跳过不重扫（枚举即断点
            # 状态；四原语均 net 内几何动作，零候选组不会被其他组动作改变；
            # 仅含 P2a 自拒形态的组不跳过——扫描留痕面 parity）
            by_net[nid] = {"status": "CONVERGED", "residual_candidates": 0,
                           "residual_by_pass": {p: 0 for p in _PRIMS},
                           "rounds": 0, "converged": True, "skipped": True}
            continue
        groups_executed.append(nid)
        g_converged = False
        g_rounds = 0
        g_sweep = {}
        for _ in range(max_rounds):
            g_rounds += 1
            before = acc.applied_total()
            snap_counts = {p: acc.counts[p]["applied"] for p in _PRIMS}
            snap_eff = {p: dict(acc.pass_delta[p]) for p in _PRIMS}
            phi_start = phi_cursor
            g_sweep = _net_group_round(board, work, nid, ribbon_like, acc,
                                       baseline_violations, p1_entry_recheck)
            phi_end = g_sweep["P3"][1]
            # ---- 组内轮级单调势断言+归属对账（T4，fail-closed）----
            round_applied = {p: acc.counts[p]["applied"] - snap_counts[p]
                             for p in _PRIMS}
            round_eff = {p: {kk: acc.pass_delta[p][kk] - snap_eff[p][kk]
                             for kk in ("vertices", "vertices_interior",
                                        "entries")}
                         for p in _PRIMS}
            if sum(round_applied.values()) > 0:
                _assert_lex_decrease(phi_start, phi_end)
            for p in _PRIMS:
                _assert_pass_monotonic(p, round_eff[p], round_applied[p])
                if p != "P3" and round_applied[p] > 0 \
                        and round_eff[p]["vertices"] != -round_applied[p]:
                    raise PotentialMonotonicityError(
                        "J1 归属断言失效：%s 本轮 applied=%d 而 Δ顶点=%r"
                        % (p, round_applied[p], round_eff[p]["vertices"]))
            meas_dvi = phi_end["vertices_interior"] \
                - phi_start["vertices_interior"]
            meas_de = phi_end["entries"] - phi_start["entries"]
            if sum(round_eff[p]["vertices_interior"]
                   for p in _PRIMS) != meas_dvi \
                    or sum(round_eff[p]["entries"] for p in _PRIMS) != meas_de:
                raise PotentialMonotonicityError(
                    "归属对账失效：Σ pass 效应 (ΔΦ_V=%d,ΔΦ_E=%d) ≠ 实测 "
                    "(%d,%d)"
                    % (sum(round_eff[p]["vertices_interior"]
                           for p in _PRIMS),
                       sum(round_eff[p]["entries"] for p in _PRIMS),
                       meas_dvi, meas_de))
            phi_cursor = phi_end
            if acc.applied_total() == before:
                g_converged = True
                break
            if acc.all_pools_empty():
                break
        sweep = g_sweep          # 最末已执行组末轮各原语扫描终点（链点）
        max_group_rounds = max(max_group_rounds, g_rounds)
        board_converged = board_converged and g_converged
        by_net[nid] = {"rounds": g_rounds, "converged": g_converged,
                       "skipped": False, "status": None,
                       "residual_candidates": None, "residual_by_pass": None}
    # ---- 终局对账：Σ pass delta == 实测 Φ(终态)−Φ(输入) ----
    phi_fin = _potentials(work)
    if sum(acc.pass_delta[p]["vertices_interior"] for p in _PRIMS) \
            != phi_fin["vertices_interior"] - phi0["vertices_interior"] \
            or sum(acc.pass_delta[p]["entries"] for p in _PRIMS) \
            != phi_fin["entries"] - phi0["entries"] \
            or sum(acc.pass_delta[p]["vertices"] for p in _PRIMS) \
            != phi_fin["vertices"] - phi0["vertices"]:
        raise PotentialMonotonicityError(
            "终局对账失效：Σ pass delta ≠ 实测 Φ(终态)−Φ(输入)")
    # ---- 终局枚举（含 memo）：by_pass/by_net 残量（R10E2B-C 组粒度）----
    fin_cands = _enumerate_candidates(work, ribbon_like, frozenset(acc.memo))
    residual = {p: 0 for p in _PRIMS}
    residual_by_net = {}
    for c in fin_cands:
        residual[c["pass"]] += 1
        residual_by_net.setdefault(c["net"],
                                   {p: 0 for p in _PRIMS})[c["pass"]] += 1
    any_capped = acc.any_capped()
    rounds_exhausted_board = (not board_converged) \
        and max_group_rounds >= max_rounds
    passes = {}
    by_pass = {}
    prev_h, prev_phi = h0, phi0
    for p in _PRIMS:
        h_out, phi_out = sweep.get(p, (prev_h, prev_phi))
        passes[p] = {
            "phi": {kk: [prev_phi[kk], phi_out[kk]] for kk in phi0},
            "delta": {"applied": acc.counts[p]["applied"],
                      "reverted": acc.counts[p]["reverted"],
                      "vertices": acc.pass_delta[p]["vertices"],
                      "vertices_interior":
                          acc.pass_delta[p]["vertices_interior"],
                      "entries": acc.pass_delta[p]["entries"],
                      "via_net_positions":
                          acc.pass_delta[p]["via_net_positions"]},
            "budget": acc.pass_budget_view(p),
            "hash": {"in": prev_h, "out": h_out},
            "main_potential": _PASS_MAIN_POTENTIAL[p],
            "termination": {
                "status": _pass_termination_status(
                    residual[p], acc.capped[p], rounds_exhausted_board),
                "residual_candidates": residual[p]},
        }
        by_pass[p] = dict(passes[p]["termination"])
        prev_h, prev_phi = h_out, phi_out
    for nid in group_order:
        rec = by_net[nid]
        rbn = residual_by_net.get(nid) or {p: 0 for p in _PRIMS}
        tot = sum(rbn.values())
        rec["residual_by_pass"] = rbn
        rec["residual_candidates"] = tot
        if rec.get("status") is None:
            rec["status"] = _pass_termination_status(
                tot, any_capped,
                (not rec["converged"]) and rec["rounds"] >= max_rounds)
    board_status = max((by_pass[p]["status"] for p in _PRIMS),
                       key=lambda s: _TERMINATION_SEVERITY[s])
    v2 = {
        "passes": passes,
        "hash_chain": [h0] + [sweep.get(p, (None, None))[0] for p in _PRIMS],
        "termination": {
            "status": board_status,
            "by_pass": by_pass,
            "by_net": by_net,
            "residual_candidates": sum(residual.values()),
            "converged": board_converged, "rounds": max_group_rounds,
            "max_rounds": max_rounds,
            "authority": "module",
            "semantics": ("not_converged 仅 NOT_CONVERGED_BUDGET/"
                          "NOT_CONVERGED_ROUNDS 两态；residual_candidates="
                          "终态结构候选机械枚举（O(V) 不耗动作预算）；以候选"
                          "面为准不以预算余量为准（预算恰尽且候选清空⇒"
                          "CONVERGED）；轮超限=防御位 fail-closed 披露；"
                          "by_net=per-net 组粒度终态（R10E2B-C/D：未完成组"
                          "整组标 NOT_CONVERGED_BUDGET，已收敛组保持）"),
        },
        "strategy": {
            "scheme": "bigboard-v1（E1 §3.5：枚举/执行分离+收益密度排序+"
                      "per-net 局部固定点+断点续跑+per-pass 分池）",
            "enumeration": {
                "candidates_total": sum(entry_by_pass.values()),
                "by_pass": entry_by_pass,
                "by_net_benefit": {n: entry_by_net[n]["benefit"]
                                   for n in sorted(entry_by_net)},
                "raw_patterns_total": len(entry_cands),
                "self_rejecting_total": self_rejecting_total,
                "descriptors_sha256": canonical_sha256(entry_cands),
                "order": "entry 路径序→原语序（P1/P2a/P2b 按位）→P3 链序",
                "note": ("candidates_total/by_pass/by_net_benefit=可行动作"
                         "面（收益/组序口径）；raw_patterns_total 含 P2a "
                         "塌缩守卫自拒形态（跳过判定口径——仅含自拒形态"
                         "的组不跳过，保扫描留痕面 parity）"),
            },
            "group_order": [{"net": nid,
                             "benefit": entry_by_net.get(
                                 nid, {}).get("benefit", 0)}
                            for nid in group_order],
            "density_basis": ("ΔΦ/cost：cost(P1)=ε 免复检⇒密度∞（组内相位"
                             "序 P1 先清场承载）；P2a/P2b/P3=1 复检单位"
                             "（per-pass 分池防饿死）；组收益总量=Σ(−ΔΦ) "
                             "按各 pass 主势单位计（E1 §3.2 表）"),
            "groups_skipped": groups_skipped,
            "groups_executed": groups_executed,
            "resume": {
                "note": ("断点续跑面：入场枚举零候选组跳过不重扫（枚举即"
                         "断点状态——四原语均 net 内几何动作组间结构独立；"
                         "per-call 独立预算 ⇒ 二次调用=续跑消费残量）"),
                "skipped_groups": groups_skipped,
                "executed_groups": groups_executed,
                "residual_descriptors_total": len(fin_cands),
                "residual_descriptors_sha256": canonical_sha256(fin_cands),
            },
        },
    }
    # hash_chain 兜底：nets 空/无已执行组/扫描未落快照时 None→当前态 hash
    h_fin = canonical_sha256({"routes": work["routes"]})
    v2["hash_chain"] = [h if h is not None else h_fin
                        for h in v2["hash_chain"]]
    for p in _PRIMS:
        if passes[p]["hash"]["in"] is None:
            passes[p]["hash"]["in"] = h_fin
        if passes[p]["hash"]["out"] is None:
            passes[p]["hash"]["out"] = h_fin
    return board_converged, max_group_rounds, v2


def _rescue_pass(board, doc, baseline, max_rounds):
    """终检不过后的逐 entry 救援通道（R8 第 1 轮判读修复，2026-10-04）。

    根因面：route_check R6 逐段 bbox 近似对 P1 合并后长斜段的假阳性（真线
    距净空但 bbox 交叠；route_check 在世界白名单外不动）。本通道按 09-24
    W-2「违例则回退**该次**简化并留痕」把整体回退细化到 entry 粒度：从 raw
    重建，P1 换 entry 粒度复检（不过则回退该 entry 全部合并并留痕），P2a/
    P2b/P3 照旧逐动作复检，救援后再做一次终局全量兜底。

    返回 dict（work/acc/converged/rounds/final_check/ok/v2）；零收益
    （applied=0）返回 None（调用方整体回退 raw，fail-closed 不变）。"""
    work = copy.deepcopy(doc)
    acc = _Acc(dict(PASS_BUDGETS))   # 救援独立全额分池（子状态机语义不变）
    ribbon_like = _ribbon_like_pids(board)
    converged, rounds, v2 = _fixpoint_loop(board, work, ribbon_like, acc,
                                           baseline["violations"], max_rounds,
                                           p1_entry_recheck=True)
    if acc.applied_total() == 0:
        return None
    try:
        crf = check_routes(board, work)
        fin = {"feasible": bool(crf.get("feasible")),
               "violations": len(crf.get("violations") or []),
               "attributed": len(crf.get("attributed_violations") or []),
               "route_check_version": crf.get("route_check_version",
                                              ROUTE_CHECK_VERSION)}
        ok = fin["feasible"] and fin["violations"] <= baseline["violations"]
    except RouteCheckError as exc:
        fin = {"feasible": False, "violations": None, "attributed": None,
               "route_check_version": ROUTE_CHECK_VERSION,
               "error": "RouteCheckError: %s" % exc}
        ok = False
    return {"work": work, "acc": acc, "converged": converged,
            "rounds": rounds, "final_check": fin, "ok": ok, "v2": v2}


def _resolve_pools(budget):
    """标量/字典预算→per-pass 池（R10E2B-E）：None=冻结分池
    （B_P1=2800/B_P2a=600/B_P2b=200/B_P3=400）；int=按原语序顺序装填
    （P1 先——密度 ∞ 面，预算=1 ⇒ P1 池=1 其余 0）；dict=显式 per-pass
    （键缺省补 0；值须非负整数）。"""
    if budget is None:
        return dict(PASS_BUDGETS)
    if isinstance(budget, dict):
        pools = {}
        for p in _PRIMS:
            v = budget.get(p, 0)
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise ValueError("postprocess_routes：budget 字典 %s 值须为"
                                 "非负整数（得 %r）" % (p, v))
            pools[p] = v
        return pools
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("postprocess_routes：budget 须为 None/非负 int/"
                         "per-pass dict（得 %r）" % (budget,))
    pools = {p: 0 for p in _PRIMS}
    rem = budget
    for p in _PRIMS:
        give = min(rem, PASS_BUDGETS[p])
        pools[p] = give
        rem -= give
    return pools


def enumerate_candidates(board, doc):
    """R10E2B-D 断点续跑面公开枚举器（只读，不耗预算、不触碰几何）：对
    (board, doc) 做入场候选枚举，返回描述子清单 (pass, net, entry_idx,
    pos, ΔΦ, needs_recheck)——确定性枚举序。残留候选描述子落盘面=跑器/
    工装侧调用本函数写盘（模块 provenance 记计数+canonical 摘要）。"""
    if not isinstance(doc, dict) or not isinstance(doc.get("routes"), list):
        raise ValueError("enumerate_candidates：doc 须为含 routes 列表的 "
                         "v5.routes.v1 工件")
    return _enumerate_candidates({"routes": doc["routes"]},
                                 _ribbon_like_pids(board), frozenset())


def postprocess_routes(board, doc, budget=None, max_rounds=None):
    """布线后处理主入口（纯函数：board 与 doc 均不被改动）。

    返回 (new_doc, provenance)：new_doc=v5.routes.v1 工件（终检通过=化简
    结果；终检不过=raw 整体回退拷贝，fail-closed）；provenance=化简账
    （类计数+回退数+逐动作留痕+不动点/预算+前后指标+终检读数）。
    changed=False 时 new_doc 与输入逐字节相等。

    budget（v2.1 起 per-pass 分池，R10E2B-E）：None=冻结分池
    PASS_BUDGETS（B_P1=2800/B_P2a=600/B_P2b=200/B_P3=400，总 4000 与
    ACTION_BUDGET 对齐）；int=按原语序顺序装填（P1 先）；dict=显式
    per-pass 池。每调用刷新（v1 独立预算语义保持——二次调用=断点续跑）。
    max_rounds 界组内循环（v2.1 per-net 局部固定点；防御位语义不变）。
    """
    if not isinstance(doc, dict) or not isinstance(doc.get("routes"), list):
        raise ValueError("postprocess_routes：doc 须为含 routes 列表的 "
                         "v5.routes.v1 工件")
    cr0 = check_routes(board, doc)        # raw 基线（内含 validate_routes）
    baseline = {"feasible": bool(cr0.get("feasible")),
                "violations": len(cr0.get("violations") or []),
                "attributed": len(cr0.get("attributed_violations") or [])}
    colocated = detect_colocated_via_pairs(doc)
    pools = _resolve_pools(budget)     # R10E2B-E：None=冻结分池/int 顺序
                                      # 装填/dict 显式 per-pass
    if max_rounds is None:
        max_rounds = MAX_ROUNDS
    work = copy.deepcopy(doc)
    acc = _Acc(pools)
    ribbon_like = _ribbon_like_pids(board)
    converged, rounds, v2 = _fixpoint_loop(board, work, ribbon_like, acc,
                                           baseline["violations"], max_rounds,
                                           p1_entry_recheck=False)
    # 终局单次全量兜底（P1 免复检的 backstop）：可行且违例计数不增才放行
    try:
        crf = check_routes(board, work)
        fin = {"feasible": bool(crf.get("feasible")),
               "violations": len(crf.get("violations") or []),
               "attributed": len(crf.get("attributed_violations") or []),
               "route_check_version": crf.get("route_check_version",
                                              ROUTE_CHECK_VERSION)}
        fin_ok = fin["feasible"] and fin["violations"] <= baseline["violations"]
    except RouteCheckError as exc:
        fin = {"feasible": False, "violations": None, "attributed": None,
               "route_check_version": ROUTE_CHECK_VERSION,
               "error": "RouteCheckError: %s" % exc}
        fin_ok = False
    applied_any = acc.applied_total() > 0
    rescue = None
    rescue_prov = None
    if applied_any and not fin_ok:
        rescue = _rescue_pass(board, doc, baseline, max_rounds)
        rescue_prov = {
            "triggered": "pass1 终检不过：feasible=%s viol=%s（基线 %s）"
                         % (fin["feasible"], fin["violations"],
                            baseline["violations"]),
            "pass1_final_check": fin,
            "mode": ("P1 entry 粒度复检重试（09-24 W-2「违例则回退该次简化"
                     "并留痕」的 entry 粒度实现；P2a/P2b/P3 逐动作复检照旧；"
                     "R8 第 1 轮判读修复 2026-10-04，根因=route_check R6 逐段"
                     " bbox 近似对合并长斜段的假阳性——白名单外不动）"),
        }
        if rescue is not None and rescue["ok"]:
            work = rescue["work"]
            fin = rescue["final_check"]
        else:
            work = copy.deepcopy(doc)
    reverted_all = applied_any and not (
        fin["feasible"] and fin["violations"] is not None
        and fin["violations"] <= baseline["violations"])
    if rescue_prov is not None:
        racc = rescue["acc"] if rescue is not None else None
        rescue_prov["kept"] = not reverted_all
        rescue_prov["outcome"] = (
            "救援采纳（entry 粒度部分合并保留）" if not reverted_all
            else ("救援零收益（P1 entry 全回退且 P2a/P2b/P3 零落位）→"
                  "整体回退 raw（fail-closed 语义不变）" if rescue is None
                  else "救援终检不过→整体回退 raw（fail-closed 语义不变）"))
        if racc is not None:
            rescue_prov["actions"] = {p: dict(racc.counts[p]) for p in _PRIMS}
            rescue_prov["fixpoint"] = {"converged": rescue["converged"],
                                       "rounds": rescue["rounds"],
                                       "max_rounds": max_rounds}
            rescue_prov["budget"] = {
                "cap": racc.cap_total(), "consumed": racc.consumed_total(),
                "applied": racc.applied_total(),
                "remaining": racc.remaining_total(),
                "capped": racc.any_capped(),
                "by_pass": {p: racc.pass_budget_view(p) for p in _PRIMS},
                "pools_frozen": dict(PASS_BUDGETS),
                "authority": "module（救援子状态机独立全额分池——语义与 "
                             "v2.0.0 独立上限结构不变）"}
            rescue_prov["final_check"] = rescue["final_check"]
            rescue_prov["passes"] = rescue["v2"]["passes"]        # v2
            rescue_prov["hash_chain"] = rescue["v2"]["hash_chain"]  # v2
            rescue_prov["termination"] = rescue["v2"]["termination"]  # v2
    # changed 以几何实际变化判定（救援全回退 ⇒ work==raw ⇒ changed=False：
    # 不加 negotiation_log 行——幂等二遍零改对救援通道同样构造性成立）
    changed = (canonical_json(work.get("routes"))
               != canonical_json(doc.get("routes")))
    if changed:
        res_txt = ""
        if rescue_prov is not None and rescue is not None:
            racc = rescue["acc"]
            res_txt = ("；救援重试 P1=%d(+%d回退) P2a=%d P2b=%d P3=%d 终检="
                       "可行(viol %s≤%d)"
                       % (racc.counts["P1"]["applied"],
                          racc.counts["P1"]["reverted"],
                          racc.counts["P2a"]["applied"],
                          racc.counts["P2b"]["applied"],
                          racc.counts["P3"]["applied"],
                          fin["violations"], baseline["violations"]))
        summary = ("postprocess %s: P1=%d P2a=%d(+%d回退) P2b=%d(+%d回退) "
                   "P3=%d(+%d回退) 轮=%d/%s 预算余=%d%s 终检=可行"
                   "(viol %s≤%d)%s"
                   % (POSTPROCESS_VERSION,
                      acc.counts["P1"]["applied"],
                      acc.counts["P2a"]["applied"],
                      acc.counts["P2a"]["reverted"],
                      acc.counts["P2b"]["applied"],
                      acc.counts["P2b"]["reverted"],
                      acc.counts["P3"]["applied"],
                      acc.counts["P3"]["reverted"],
                      rounds, "收敛" if converged else "超限停线",
                      acc.remaining_total(),
                      "（预算封顶）" if acc.any_capped() else "",
                      fin["violations"], baseline["violations"], res_txt))
        work["negotiation_log"] = list(doc.get("negotiation_log") or []) + \
            [summary]
        prov = dict(doc.get("provenance") or {})
        prov["postprocess"] = POSTPROCESS_VERSION
        work["provenance"] = prov
    provenance = {
        "module_version": POSTPROCESS_VERSION,
        "board_id": doc.get("board_id"),
        "board_sha256": doc.get("board_sha256"),
        "source_generator": (doc.get("provenance") or {}).get("generator"),
        "baseline_check": baseline,
        "colocated_via_pairs_detected": len(colocated),
        "colocated_via_pairs": [[nid, [p[0], p[1]]] for nid, p in colocated],
        "colocated_note": "D-5(a) 防御面：现役 D3 孔心距约束下结构性不可能，"
                          "检测如实报数（非零=披露呈裁）",
        "actions": {p: dict(acc.counts[p]) for p in _PRIMS},
        "action_log": acc.log,
        "rescue": rescue_prov,
        "rescue_action_log": (rescue["acc"].log if rescue is not None
                              else None),
        "fixpoint": {"converged": converged, "rounds": rounds,
                     "max_rounds": max_rounds},
        # ---- v2 四门分离（OPT-18 E2a；v1 字段全部兼容保留）----
        "hash_chain": v2["hash_chain"],
        "passes": v2["passes"],
        "termination": dict(v2["termination"],
                            scope="main_loop（救援通道独立子状态机见 "
                                  "provenance.rescue.termination）"),
        "budget": {"cap": acc.cap_total(), "consumed": acc.consumed_total(),
                   "applied": acc.applied_total(),
                   "remaining": acc.remaining_total(),
                   "capped": acc.any_capped(),
                   "by_pass": {p: acc.pass_budget_view(p) for p in _PRIMS},
                   "pools_frozen": dict(PASS_BUDGETS),
                   "authority": "module（模块动作预算 per-pass 分池 "
                                "（R10E2B-E）；跑器墙钟预算=runner 口径"
                                "另报，两口径分立）"},
        "strategy": v2["strategy"],   # v2.1 大板策略审计面（纯加性）
        "feasibility": {"authority": "module（终检恒跑，语义与 v1 "
                                     "final_check 相同）",
                        "final_check_always_runs": True,
                        "final_check": fin},
        "determinism": None,       # 权威=跑器（双跑 canonical/hash 链对比）
        "idempotency": None,       # 权威=验收工装（T2 复调）；主张前置=
                                   # termination.status==CONVERGED
        "gates": {
            "termination": {"authority": "module", "field": "termination"},
            "budget": {"authority": "module(动作)/runner(墙钟) 两口径分立",
                       "module_field": "budget",
                       "runner_field": "runner row budget_capped"},
            "feasibility": {"authority": "module", "field": "feasibility"},
            "determinism": {"authority": "runner", "field": "determinism",
                            "value": None},
            "idempotency": {"authority": "harness", "field": "idempotency",
                            "value": None,
                            "claim_precondition":
                                "termination.status==CONVERGED"},
        },
        "metrics": {"before": _metrics(doc), "after": _metrics(work)},
        "final_check": fin,
        "reverted_all": reverted_all,
        "changed": changed,
    }
    return work, provenance
