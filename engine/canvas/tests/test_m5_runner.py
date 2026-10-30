# -*- coding: utf-8 -*-
"""Lane-M5 runner 测试: fail-closed 拒收矩阵 + v5.drc 同源绑定 + 确定性双跑
+ 真板 no_length_groups 审计路径。

矩阵计数（≥任务书下限）: fail-closed 15 例（V_TUNING_PARAMS 9 面 +
V_TUNING_KIND 1 + E_UNKNOWN_NET 1 + V_EDGE 1 + 格式层 1 + 规划侧 keepout
拒收 1 + apply 层悬空基线 1）; v5.drc 绑定 9 例; 确定性双跑 3 例（合成夹具
板字节等 2 + 真板 no_length_groups 1）; 另规划内容/摘要断言与真板长度组
审计可执行断言。
"""
import json
import re

import pytest

from v5 import canonical

from canvas import protocol as cpr
from canvas import tuning as ct
from canvas import validate as cval
from canvas.runners import m5 as m5r
from canvas.tests.test_k1_fixtures import real_board, real_state, run_batch
from canvas.tests.test_m5_fixtures import M5_BUDGET, m5_state


def _tuning_action(net_id="NET-T1", group_id="LG-X", kind="detour", **params):
    return {"action": "tuning", "net_id": net_id, "group_id": group_id,
            "kind": kind, "params": params}


def _rejected_with(st, action, code):
    results = run_batch(st, [action])
    tun = [r for r in results if r["action"] == "tuning"][0]
    assert tun["accepted"] is False
    assert tun["code"] == code, "期望 %s 实得 %s (%s)" % (
        code, tun["code"], tun.get("detail"))
    return tun


# ---------------------------------------------------------------- fail-closed 矩阵

def test_fc_tuning_kind_rejected():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="serpentine", offset_mm=0.5),
                   cpr.V_TUNING_KIND)


def test_fc_params_missing_key():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="accordion", amp_mm=0.5),
                   cpr.V_TUNING_PARAMS)


def test_fc_params_extra_key():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="accordion", amp_mm=0.5, count=1,
                                      phase=0), cpr.V_TUNING_PARAMS)


def test_fc_params_zero_amp():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="accordion", amp_mm=0, count=1),
                   cpr.V_TUNING_PARAMS)


def test_fc_params_negative_amp():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="accordion", amp_mm=-0.5, count=1),
                   cpr.V_TUNING_PARAMS)


def test_fc_params_zero_count():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="accordion", amp_mm=0.5, count=0),
                   cpr.V_TUNING_PARAMS)


def test_fc_params_float_count():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="accordion", amp_mm=0.5, count=1.5),
                   cpr.V_TUNING_PARAMS)


def test_fc_params_bool_amp():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="accordion", amp_mm=True, count=1),
                   cpr.V_TUNING_PARAMS)


def test_fc_params_string_value():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="detour", offset_mm="0.5"),
                   cpr.V_TUNING_PARAMS)


def test_fc_params_zero_offset():
    st = m5_state()
    _rejected_with(st, _tuning_action(kind="detour", offset_mm=0),
                   cpr.V_TUNING_PARAMS)


def test_fc_unknown_net():
    st = m5_state()
    _rejected_with(st, _tuning_action(net_id="NET-NOPE", offset_mm=0.5),
                   cpr.E_UNKNOWN_NET)


def test_fc_no_baseline_segment():
    """网已 ripup（无基线段）→ tuning 悬空拒收（V_TUNING_PARAMS 面）。"""
    st = m5_state()
    run_batch(st, [{"action": "ripup", "net_id": "NET-T1"}])
    _rejected_with(st, _tuning_action(net_id="NET-T1", offset_mm=-0.5),
                   cpr.V_TUNING_PARAMS)


def test_fc_edge_band_reject():
    """调参几何入板边禁布带 → V_EDGE（validate_edit 同源
    check_edge_clearance; y=11.5 > 11.4−0.2 内矩形界）。"""
    st = m5_state(y_max=11.4, zones=False)
    tun = _rejected_with(st, _tuning_action(
        net_id="NET-T2", kind="accordion", amp_mm=2.5, count=1), cpr.V_EDGE)
    assert "11.5" in (tun.get("detail") or "")


def test_fc_format_layer_params_not_dict():
    """格式层整批拒收: params 非对象 → E_MISSING_KEY（parse_batch 面）。"""
    doc = {"round": 1, "actions": [
        {"action": "tuning", "net_id": "NET-T1", "group_id": "LG-X",
         "kind": "detour", "params": [0.5]}, {"action": "submit"}]}
    with pytest.raises(cpr.BatchReject) as ei:
        cpr.parse_batch(json.dumps(doc), 1)
    assert ei.value.code == cpr.E_MISSING_KEY


def test_fc_planner_keepout_full_rejection():
    """keepout 违例拒收（规划侧）: LG-BOXED 组全部合法档进 zone
    （accordion 触 Z2、detour±触 Z2/Z3）→ 不产动作、组残差原样登记。"""
    planned = m5r.plan_actions(m5_state(), M5_BUDGET)
    assert all(a["net_id"] != "NET-T2" for a in planned)
    summary = m5r.run_m5(m5_state(), M5_BUDGET)
    assert summary["residuals_after"]["LG-BOXED"]["residual_mm"] == 0.9
    assert summary["tuned_groups"] == ["LG-OPEN"]


# ---------------------------------------------------------------- v5.drc 同源绑定

def test_drc_tuned_state_validate_full_clean():
    """合法调参后全态检查净（check_all 聚合 R5/R2/R6/R1 + edge/孔——tuning
    铜在场且无违例）。"""
    st = m5_state()
    m5r.run_m5(st, M5_BUDGET)
    rep = cval.validate_full(st)
    assert rep.clean, [v.as_dict() for v in rep.violations]


def test_drc_tuning_copper_in_instantiate_scene():
    """tuning 几何经 canvas.instantiate 入铜场（shape_id 寻址; 单源几何）。"""
    from canvas import instantiate as inst
    st = m5_state()
    m5r.run_m5(st, M5_BUDGET)
    coppers = inst.instantiate(st)["coppers"]
    by_cid = {cu.cid: cu for cu in coppers}
    assert "tun:NET-T1:LG-OPEN:0" in by_cid
    assert getattr(by_cid["tun:NET-T1:LG-OPEN:0"], "is_tuning", False)


def test_drc_residual_matches_instantiate_geometry():
    """残差测量 vs instantiate 几何对照: tuned 长度 == tuning_polyline_mm
    折线弧长（测试侧独立求和，不走 residual 内部路径）。"""
    import math
    from canvas import instantiate as inst
    st = m5_state()
    m5r.run_m5(st, M5_BUDGET)
    tun = st.tunings["tun:NET-T1:LG-OPEN:0"]
    pts = inst.tuning_polyline_mm(st, tun)
    manual = sum(math.hypot(b[0] - a[0], b[1] - a[1])
                 for a, b in zip(pts[:-1], pts[1:]))
    r = ct.residual(st, "LG-OPEN", M5_BUDGET["length_groups"])
    assert abs(r["actual_mm"] - round(manual, 9)) < 1e-9
    assert r["residual_mm"] == 0.0
    assert r["per_net"]["NET-T1"]["tuned"] is True


def test_drc_zone_entering_tuning_reports_r6_via_validate_full():
    """apply 层直发进 zone 的 tuning（validate_edit 波1 范围无 R6 → 接受），
    validate_full 的 check_all→check_keepout 如实报 R6（fail-closed 不静默），
  归责到 tuning shape_id——zones 透传绑定主面。
  语义升级（编排体 2026-09-25 接线，lane-m5 §6 遗留收口）: ①apply 层直发
  进 zone 的 tuning 现 validate_edit 前置拒收 V_KEEPOUT; ②绕过协议层直构的
  进 zone tuning 由 validate_full 兜底报 R6（双面均在）。"""
    st = m5_state()
    results = run_batch(st, [_tuning_action(net_id="NET-T2", group_id="LG-X",
                                            offset_mm=0.5)])
    assert not st.tunings, "前置拒收后不落 tuning"
    assert results[0]["accepted"] is False
    assert results[0]["code"] == "V_KEEPOUT", results[0]
    tun = st.add_tuning("NET-T2", "LG-X", "detour",
                        cpr.tuning_base_grid(st, "NET-T2"),
                        {"offset_mm": 0.5})
    rep = cval.validate_full(st)
    r6 = [v.as_dict() for v in rep.violations if v.rule == "R6"]
    assert any(v["subjects"][0] == tun["shape_id"] and
               v["subjects"][1] == "Z2" for v in r6), r6


def test_drc_zone_rects_passthrough_mechanism():
    """board zones → validate.zone_rects 透传机制（validate_full 同一透传源）:
    3 keepout 元组形（zone_id, (x0,y0,x1,y1)）、sensitive 空。"""
    st = m5_state()
    sensitive, keepout = cval.zone_rects(st.board)
    assert sensitive == []
    assert [zid for zid, _r in keepout] == ["Z1", "Z2", "Z3"]
    assert keepout[0][1] == (1.0, 2.5, 11.0, 4.5)


def test_drc_planner_avoids_zone_geometry():
    """规划侧 R6 预检生效: LG-OPEN 需 added=1.0，accordion(+u 触 Z1) 与
    detour +0.5（bump 触 Z1）被跳过，取 detour −0.5（净空侧）。"""
    planned = m5r.plan_actions(m5_state(), M5_BUDGET)
    assert planned == [{"action": "tuning", "net_id": "NET-T1",
                        "group_id": "LG-OPEN", "kind": "detour",
                        "params": {"offset_mm": -0.5}}]


def test_drc_accordion_length_effect_on_real_geometry():
    """accordion 实测（instantiate 几何对照，zone-free 变体板）:
    - count=1: 折返点 s=total/2 恰落腿界（腿起点）→ 精确 = 基线+2·amp·count = 9.0;
    - count=2: 两折返均腿中（r<pitch）→ 回退段额外 +2·(pitch−r)×2 → 11.0
      （闭式 2·amp·count=2.0 是下界，精确披露见 canvas.tuning）。"""
    st = m5_state(zones=False)
    run_batch(st, [_tuning_action(net_id="NET-T1", group_id="LG-A",
                                  kind="accordion", amp_mm=0.5, count=2)])
    assert ct.net_tuned_len_mm(st, "NET-T1", "LG-A") == 11.0
    rep = cval.validate_full(st)
    assert rep.clean, [v.as_dict() for v in rep.violations]
    st2 = m5_state(zones=False)
    run_batch(st2, [_tuning_action(net_id="NET-T1", group_id="LG-A",
                                   kind="accordion", amp_mm=0.5, count=1)])
    assert ct.net_tuned_len_mm(st2, "NET-T1", "LG-A") == 9.0


def test_planner_exact_length_recheck_beats_closed_form():
    """精确长度复核面: target=10.0 tol=0.05、amp 上限 0.5（budget
    tuning_limits 覆盖）→ 闭式档 added=2.0 的唯一 accordion(0.5,2) 排序
    第一，但实算长 11.0（两腿中折返回退段各 +2·(pitch−r)）越容差带 →
    规划跳过，取实算恰 10.0 的 detour −1.0（无闭式误差漏网）。"""
    budget = {"tuning_limits": {"max_amp_mm": 0.5},
              "length_groups": {
                  "LG-EXACT": {"nets": ["NET-T1"], "target_mm": 10.0,
                               "tol_mm": 0.05}}}
    planned = m5r.plan_actions(m5_state(zones=False), budget)
    assert planned == [{"action": "tuning", "net_id": "NET-T1",
                        "group_id": "LG-EXACT", "kind": "detour",
                        "params": {"offset_mm": -1.0}}]
    st = m5_state(zones=False)
    summary = m5r.run_m5(st, budget)
    assert summary["residuals_after"]["LG-EXACT"]["residual_mm"] == 0.0


def test_drc_detour_side_sign_geometry():
    """detour 侧移符号的几何语义: +0.5 bump y∈[2,2.5]（进 Z1 方向）、
    −0.5 bump y∈[1.5,2]（净空方向）——规划选负侧，几何实测对照。"""
    from canvas import instantiate as inst
    st = m5_state(zones=False)
    run_batch(st, [_tuning_action(net_id="NET-T1", group_id="LG-D",
                                  offset_mm=-0.5)])
    pts = inst.tuning_polyline_mm(st, st.tunings["tun:NET-T1:LG-D:0"])
    assert min(p[1] for p in pts) == 1.5 and max(p[1] for p in pts) == 2.0


def test_drc_edge_violation_via_validate_full_for_tuning():
    """edge 绑定（全态面）: 直接落一个入边带的 tuning 到 zone-free 变体板
    需绕过 validate_edit——改用最小 accordions 序列: amp 2.5 被 V_EDGE 拒，
    佐证 edge 同源判定对 tuning 几何生效（validate_edit 与 validate_full
    同一 check_edge_clearance）。"""
    st = m5_state(y_max=11.4, zones=False)
    results = run_batch(st, [_tuning_action(
        net_id="NET-T2", kind="accordion", amp_mm=2.5, count=1)])
    tun = [r for r in results if r["action"] == "tuning"][0]
    assert tun["accepted"] is False and tun["code"] == cpr.V_EDGE
    # 对照: 同板 amp 2.0（y=11 ≤ 内矩形界 11.2）应净过且全态净
    st2 = m5_state(y_max=11.4, zones=False)
    run_batch(st2, [_tuning_action(net_id="NET-T2", kind="accordion",
                                   amp_mm=2.0, count=1)])
    assert cval.validate_full(st2).clean


# ---------------------------------------------------------------- 确定性双跑

def test_det_double_run_synth_summary_and_state():
    """合成长度组夹具板双跑: run_m5 摘要 canonical 字节等 + 终态
    state_sha256 等（无随机源、copy-on-write 序钉死）。"""
    st1, st2 = m5_state(), m5_state()
    s1 = m5r.run_m5(st1, M5_BUDGET)
    s2 = m5r.run_m5(st2, M5_BUDGET)
    assert canonical.canonical_json(s1) == canonical.canonical_json(s2)
    assert st1.sha256() == st2.sha256()
    assert s1["planned"] == 1 and s1["applied"] == 1 and s1["rejected"] == []
    assert s1["tuned_groups"] == ["LG-OPEN"]


def test_det_double_run_plan_actions_bytes():
    planned1 = m5r.plan_actions(m5_state(), M5_BUDGET)
    planned2 = m5r.plan_actions(m5_state(), M5_BUDGET)
    assert canonical.canonical_json(planned1) == canonical.canonical_json(planned2)


def test_det_double_run_real_board_no_length_groups():
    """真板（badgeleds 无长度组字段）no_length_groups 路径双跑字节等 +
    零动作 + 态哈希前后不变（空批不动状态）。"""
    st1, st2 = real_state(), real_state()
    sha_before = st1.sha256()
    s1 = m5r.run_m5(st1, {})
    s2 = m5r.run_m5(st2, {})
    assert s1["no_length_groups"] is True and s1["planned"] == 0
    assert canonical.canonical_json(s1) == canonical.canonical_json(s2)
    assert st1.sha256() == st2.sha256() == sha_before


# ---------------------------------------------------------------- 摘要与审计

def test_run_m5_summary_shape():
    st = m5_state()
    s = m5r.run_m5(st, M5_BUDGET)
    assert s["board_id"] == "synth-m5"
    assert s["no_length_groups"] is False
    assert s["residuals_before"]["LG-OPEN"]["residual_mm"] == 1.0
    assert s["residuals_after"]["LG-OPEN"]["residual_mm"] == 0.0
    assert s["residuals_after"]["LG-BOXED"]["residual_mm"] == 0.9
    assert s["tuned_groups"] == ["LG-OPEN"]


def test_real_board_length_group_audit_executable():
    """长度组数据审计结论的可执行转录: badgeleds board 体（及 nets/partitions/
    stackup/hard_rules 条目）无任何 length/match/tuning/target 类字段——
    run_m5 真板路径=no_length_groups，人口=合成长度组夹具板（budget 注入）。
    已知排除: provenance（溯源元数据）/principle_registry（原则注册表——
    其 target_freedom="corridor" 与 group_types=["BUS","DIFF"] 是生成期
    自由度/分区归组语义，非长度匹配目标，canvas.tuning docstring 已登记）。"""
    board, _path, _sha = real_board()

    def _walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert not re.search(r"length|match|tuning|targ", k, re.I), \
                    "审计失效: board 出现疑似长度组键 %s/%s" % (path, k)
                _walk(v, path + "/" + str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, path + "[%d]" % i)

    audited = {k: v for k, v in board.items()
               if k not in ("provenance", "principle_registry")}
    _walk(audited)
    reg = board["principle_registry"][0]
    assert reg["target_freedom"] == "corridor"   # 唯一 'targ' 命中=生成自由度
    st = real_state()
    assert m5r.run_m5(st, {"length_groups": {}})["no_length_groups"] is True
