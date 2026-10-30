# -*- coding: utf-8 -*-
"""canvas.tuning -- Lane-M5 高速调参伴件（合同 §1: 宽度档表按叠层计算 +
accordion/绕行参数化合法档枚举 + 长度组残差测量 + R6 避撞预检）。

四件只读复用既有几何/判定源，禁平行实现:
- 参数化几何: canvas.instantiate.tuning_polyline_mm（公式单源，本件只推导
  其**长度效应**闭式——见 legal_options docstring）；
- R6 判定: canvas.validate.zone_rects 透传 board zones → v5.drc.check_keepout
  同一判定器（plane 层集口径 = v5.route_check: stackup kind=="plane"）；
- 残差测量: 实际长度经 canvas.instantiate 几何（grid_path_mm /
  tuning_polyline_mm 折线弧长），不走第二几何。

**长度组数据审计结论（badgeleds board.v1 逐键探查，2026-09-25 本车道）**:
board 体顶层键 = board_id/hard_rules/holes/nets/partitions/principle_registry/
provenance/schema_version/stackup/workspace/zones——**无任何长度组字段**
（无 length_groups/matched/tuning/target 类键；principle_registry 唯一
"group" 命中是 partition_granularity 编译规则的 group_types=["BUS","DIFF"]，
属生成期分区归组语义，非长度匹配目标）。故长度组人口 = 合成夹具板 +
budget 注入目标长度表（真板如实登记为 no_length_groups 路径，激活跑 prereg
转录本结论）。
"""
import math

from v5 import drc

# ---------------------------------------------------------------- 宽度档表
#: 档名 → 单端目标阻抗 Ω（"min"=高阻窄档/"nom"=标称 50Ω/"max"=低阻宽档；
#: 工程经验缺省，非板权威——板权威档词表单源仍是 canvas.validate.
#: width_class_vocab，本表是按叠层的**目标阻抗合成**视角，两者用途不同）。
CLASS_TARGET_OHM = {"min": 60.0, "nom": 50.0, "max": 40.0}


def _microstrip_z0(w_over_h, er):
    """微带线特性阻抗分析式（工程经验近似；Hammerstad/Schneider 闭式，
    Pozar《Microwave Engineering》§3.8 同族教材式，零铜厚近似）:

        εe = (εr+1)/2 + (εr−1)/2 · (1 + 12·H/W)^(−1/2)
        W/H ≥ 1:  Z0 = 120π / (√εe · (W/H + 1.393 + 0.667·ln(W/H + 1.444)))
        W/H < 1:  Z0 = (60/√εe) · ln(8H/W + W/(4H))

    单调递减（W↑ → Z0↓），故可二分反解。**工程经验近似，非全阻抗 authority。**
    """
    x = float(w_over_h)
    e_eff = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 / math.sqrt(1.0 + 12.0 / x)
    if x >= 1.0:
        return 120.0 * math.pi / (math.sqrt(e_eff)
                                  * (x + 1.393 + 0.667 * math.log(x + 1.444)))
    return (60.0 / math.sqrt(e_eff)) * math.log(8.0 / x + x / 4.0)


def _microstrip_width(target_ohm, er, h_mm):
    """微带合成: 目标 Z0 → 线宽（对 _microstrip_z0 确定性二分，200 步定深，
    无随机源；区间 [0.01·H, 100·H] 覆盖工程域）。"""
    lo, hi = 0.01, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _microstrip_z0(mid, er) > target_ohm:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0 * h_mm


def _stripline_width(target_ohm, er, b_mm):
    """对称带状线合成（工程经验近似，Cohn 窄条零厚度闭式的解析反解）:

        W = 4b / (π · exp(Z0·√εr / 60))      （W/b < 0.35 窄条域）

    本近似**只在窄条域内使用**——W/b ≥ 0.35（宽条域需平行板+边缘电容修正，
    Cohn 宽条式）即越出本近似模型，fail-closed 抛 ValueError 而非外推。
    出处标注: 窄条式系 Cohn (1954) 零厚度对称带状线经典近似（Microwaves101
    stripline 页/教材通载形态）。**工程经验近似，非全阻抗 authority。**
    """
    w = 4.0 * b_mm / (math.pi * math.exp(target_ohm * math.sqrt(er) / 60.0))
    if w / b_mm >= 0.35:
        raise ValueError(
            "stripline 近似越出窄条域 W/b=%.4f ≥0.35（目标 %r Ω 需宽条式，"
            "本表不外推——工程经验近似边界 fail-closed）" % (w / b_mm, target_ohm))
    return w


def width_table(stackup, er=4.4, h_mm=1.5, b_mm=1.0, classes=None):
    """宽度档表按叠层计算: stackup → {layer_id: {class: width_mm}}。

    **公式来源披露（工程经验近似，不冒称全阻抗 authority）**:
    - board.v1 schema 的 stackup 条目只有 id/kind/preferred_direction/
      available（additionalProperties=false，探明 2026-09-25），**不含层厚/
      介电常数**——故本表用可注入的工程缺省: FR4 εr=4.4、外层微带介质厚
      H=1.5mm（≈1.6mm 双层板芯）、内层带状线参考面间距 b=1.0mm（≈常规
      四层板内芯）。板若未来落显式叠层几何字段，由此改读板值（板值优先）。
    - 层位分类: stackup 序首位/末位信号层 = 外层（微带模型），其间 = 内层
      （对称带状线模型）——"外层微带/内层带状线"是叠层工程通则近似。
    - 微带: Hammerstad/Schneider 闭式（Pozar 教材式）+ 确定性二分反解;
      带状线: Cohn 窄条零厚度闭式解析反解（越窄条域 fail-closed）。
    - 档含义: min=60Ω 目标（最窄）/nom=50Ω/max=40Ω（最宽）——单端目标
      阻抗三角，工程经验缺省，class 键与 validate.width_class_vocab 的档名
      同形但语义不同（该表=载流档，本表=阻抗合成档）。
    - 只给 kind=="signal" 且 available==True 的层出档（与
      CanvasState.signal_layers 同口径）；plane 层不出档。
    确定性: 全闭式/定深二分，无随机；同 stackup 双跑字节等。宽度量化 6 位
    小数（µm 级，工程分辨）。
    """
    cls_targets = dict(CLASS_TARGET_OHM if classes is None else classes)
    out = {}
    n = len(stackup)
    for idx, layer in enumerate(stackup):
        if layer.get("kind") != "signal" or layer.get("available") is not True:
            continue
        outer = idx == 0 or idx == n - 1
        row = {}
        for name in sorted(cls_targets):
            z = float(cls_targets[name])
            w = (_microstrip_width(z, er, h_mm) if outer
                 else _stripline_width(z, er, b_mm))
            row[name] = round(w, 6)
        out[str(layer["id"])] = row
    return out


# ---------------------------------------------------------------- 合法档枚举
#: 合法档枚举的工程缺省上限（budget["tuning_limits"] 可覆盖; 无随机源）。
DEFAULT_MAX_AMP_MM = 2.5      # accordion 幅度上限（5×0.5mm pitch）
DEFAULT_MAX_COUNT = 8         # accordion 折返数上限
DEFAULT_MAX_OFFSET_MM = 5.0   # detour 侧移幅度上限


def legal_options(base_len_mm, target_mm, tol_mm, pitch_mm=0.5,
                  max_amp_mm=DEFAULT_MAX_AMP_MM, max_count=DEFAULT_MAX_COUNT,
                  max_offset_mm=DEFAULT_MAX_OFFSET_MM):
    """每段合法选项枚举: 基线长/目标/容差 → 合法 tuning 档列表（确定性按序）。

    **长度效应闭式（由 canvas.instantiate.tuning_polyline_mm 公式单源推导，
    本件不平行实现几何，只复述其算术后果）**:
    - accordion {amp_mm=a, count=n}: 每折返把基线上 `直行 pitch` 替换为
      `a + pitch + a`，净增 2a；n 折返共净增 **2·a·n**（u⊥d、折返矩形腿）。
      **精确性披露**: 2·a·n 成立当且仅当每折返点 P 落在基线腿起点
      （腿内剩余 r=pitch）; P 落腿中（r<pitch）时折返点 P+d·pitch 越过腿端，
      instantiate 折线产生回退段，每折返额外 +2·(pitch−r)（<2·pitch）。
      本函数给的是**闭式预测档**（确定性枚举面）; 精确长度一律以
      option_actual_len_mm（经 instantiate 几何单源实算）为准——规划侧
      （runners.m5）对每档做精确复核后才采纳。
    - detour {offset_mm=o}: 最长腿 A→B 替换为 A→A+uo→B+uo→B，净增
      **2·|o|**（平移腿长不变，两条侧移腿各 |o|）——精确式（与腿内
      位置无关）。
    合法档判据: |target − base − added| ≤ tol（加长后落容差带内即合法）。
    参数量化: amp/|offset| 取 pitch 整数倍（格点纪律的 mm 面），offset 双侧
    （±，侧移方向）；amp∈{1..⌊max_amp/pitch⌋}·pitch、count∈{1..max_count}、
    |offset|∈{1..⌊max_offset/pitch⌋}·pitch。
    排序（确定性）: (added_mm 升序, kind, params 字典序)。返回
    [{kind, params, added_mm, residual_after_mm}]；无可行参数组合=[]
    （含 target 低于基线且超容差——accordion/detour 只加长不缩短）。"""
    base = float(base_len_mm)
    target = float(target_mm)
    tol = float(tol_mm)
    pitch = float(pitch_mm)
    if not (tol >= 0.0):
        raise ValueError("tol_mm 须非负（得到 %r）" % (tol_mm,))
    if pitch <= 0.0:
        raise ValueError("pitch_mm 须为正（得到 %r）" % (pitch_mm,))
    options = []

    def _add(kind, params, added):
        after = target - base - added
        if abs(after) <= tol:
            options.append({"kind": kind, "params": params,
                            "added_mm": round(added, 9),
                            "residual_after_mm": round(after, 9)})

    amp_steps = int(math.floor(max_amp_mm / pitch + 1e-9))
    for count in range(1, int(max_count) + 1):
        for k in range(1, amp_steps + 1):
            amp = round(k * pitch, 9)
            _add("accordion", {"amp_mm": amp, "count": count}, 2.0 * amp * count)
    off_steps = int(math.floor(max_offset_mm / pitch + 1e-9))
    for k in range(1, off_steps + 1):
        off = round(k * pitch, 9)
        _add("detour", {"offset_mm": off}, 2.0 * off)
        _add("detour", {"offset_mm": -off}, 2.0 * off)
    options.sort(key=lambda o: (o["added_mm"], o["kind"],
                                sorted(o["params"].items())))
    return options


# ---------------------------------------------------------------- 残差测量
def _polyline_len_mm(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1])
               for a, b in zip(pts[:-1], pts[1:]))


def option_actual_len_mm(st, net_id, kind, params, group_id="cand"):
    """候选档的**精确**调参后长度（instantiate 几何单源实算，只读）:
    以 protocol.tuning_base_grid 为基线构造 fake tuning →
    instantiate.tuning_polyline_mm 折线弧长。accordion 腿中折返的回退段
    长度由此如实计入（闭式 2·amp·count 是腿起点折返的下界，见
    legal_options docstring 精确性披露）——规划侧采纳前的精确复核单源。"""
    from . import instantiate as inst
    from . import protocol as cpr
    grid = cpr.tuning_base_grid(st, net_id)
    if not grid:
        raise ValueError("网 %r 无基线段（tuning 悬空）" % (net_id,))
    fake = {"shape_id": "cand:tun:len", "net_id": net_id,
            "group_id": group_id, "kind": kind, "grid": grid,
            "params": dict(params)}
    return round(_polyline_len_mm(inst.tuning_polyline_mm(st, fake)), 9)


def net_tuned_len_mm(st, net_id, group_id):
    """网在长度组口径下的实际路径长（经 canvas.instantiate 几何，只读）:
    组内最新 tuning（同 net+group 的最大 seq，后到覆盖）→ tuning_polyline_mm
    弧长；无 tuning → 基线（protocol.tuning_base_grid=网首段已落折线，与
    tuning 基线同一条折线）grid_path_mm 弧长。**不含 pad stub**（stub 属
    端子抽象非走线长度，tuning_polyline_mm 亦无 stub——前后口径一致）。"""
    from . import instantiate as inst
    from . import protocol as cpr
    latest = None
    for sid in sorted(st.tunings):
        tun = st.tunings[sid]
        if tun["net_id"] == net_id and tun["group_id"] == group_id:
            if latest is None or sid > latest["shape_id"]:
                latest = tun
    if latest is not None:
        pts = inst.tuning_polyline_mm(st, latest)
    else:
        grid = cpr.tuning_base_grid(st, net_id)
        if not grid:
            raise ValueError("网 %r 无基线段（残差测量 fail-closed）" % (net_id,))
        pts = inst.grid_path_mm(st, inst.expand_waypoints(grid))
    return round(_polyline_len_mm(pts), 9)


def residual(st, group_id, groups):
    """长度组残差: {target_mm, actual_mm, residual_mm, per_net}。

    - groups = {group_id: {"nets": [net_id..], "target_mm": float,
      "tol_mm": float}}（budget 注入; 真板无长度组字段=审计结论，见模块
      docstring）。
    - actual/residual 取组内**最大偏差网**（长度匹配以最差网计，并列取
      net_id 序——确定性）；per_net 逐网 {path_len_mm, residual_mm, tuned}。
    - residual_mm = target − actual（正=欠长可调，负=超长 accordion/detour
      不可救——只加长不缩短）。
    - fail-closed: 未知组 KeyError；组内网不在板 E_UNKNOWN_NET 语义（抛
      KeyError，逐网核 known_nets）；组内网无基线段 ValueError。"""
    if group_id not in groups:
        raise KeyError("残差无组 %r（groups=%s）"
                       % (group_id, sorted(groups)))
    spec = groups[group_id]
    target = float(spec["target_mm"])
    per_net = {}
    for net_id in sorted(spec["nets"]):
        if net_id not in st.known_nets():
            raise KeyError("长度组 %r 引用未知网 %r" % (group_id, net_id))
        ln = net_tuned_len_mm(st, net_id, group_id)
        per_net[net_id] = {"path_len_mm": ln,
                           "residual_mm": round(target - ln, 9),
                           "tuned": any(
                               t["net_id"] == net_id
                               and t["group_id"] == group_id
                               for t in st.tunings.values())}
    worst = max(sorted(per_net),
                key=lambda n: (abs(per_net[n]["residual_mm"]), n))
    return {"target_mm": target,
            "actual_mm": per_net[worst]["path_len_mm"],
            "residual_mm": per_net[worst]["residual_mm"],
            "worst_net": worst,
            "per_net": per_net}


# ---------------------------------------------------------------- R6 避撞
def plane_layers(board):
    """plane 层 id 集（stackup kind=="plane"——v5.route_check 同口径排序元组）。"""
    return tuple(sorted(str(l["id"]) for l in board.get("stackup", [])
                        if l.get("kind") == "plane"))


def r6_violations(st, net_id, kind, params, group_id="cand"):
    """R6 避撞预检: 候选 tuning 几何 vs board zones（keepout/plane）。

    **同源绑定（禁平行实现）**: zones 透传 = canvas.validate.zone_rects
    （validate_full 同一透传路径——board.zones → sensitive/keepout 元组形）；
    判定 = v5.drc.check_keepout 同一判定器（validate_full 的 check_all 内部
    亦调它）; 候选铜 = canvas.instantiate.tuning_copper（几何单源）。返回
    R6 违例 as_dict 列表（空=不进 zones/plane 层）。
    注: validate_edit 的 tuning 分支只查 R5/edge/孔（波1 范围），R6 拒收
    由本预检在规划侧执行（plan_actions 只发过预检的档）——apply 层若直发
    进 zone 的 tuning，validate_full 的 check_all→check_keepout 会如实报
    R6（fail-closed 不静默），测试两面对照绑定。"""
    from . import instantiate as inst
    from . import protocol as cpr
    from . import validate as cval
    grid = cpr.tuning_base_grid(st, net_id)
    if not grid:
        raise ValueError("网 %r 无基线段（tuning 悬空）" % (net_id,))
    fake = {"shape_id": "cand:tun:r6", "net_id": net_id, "group_id": group_id,
            "kind": kind, "grid": grid, "params": dict(params)}
    cu = inst.tuning_copper(st, fake)
    if cu is None:
        return []
    _sensitive, keepout = cval.zone_rects(st.board)
    return [v.as_dict() for v in
            drc.check_keepout([cu], keepout, plane_layers(st.board))]
