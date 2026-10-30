# -*- coding: utf-8 -*-
"""geometry_judge_fixture —— 有界 judge fixture 适配件（OPT-04 第一刀，EXEC-R2）。

职责：把 strict/conservative 两面**真实权威函数**适配成同版本声明的有界判读
fixture，供常驻测试与人工核验使用。历史 closure_detector.py（out/net-agent-p1/
run14v2/closure/）与历史 closure verdict **只读、不 import、不回写**——本件
是新 judge fixture 消费方（GATE-A1 04-F：judge 用新 fixture 适配既有权威路径）。

三面读数（与 S5-02 判据③走廊 fixture 同构，真实函数对读）：
- cons   = net_agent_pilot.pilot._blocked_at（保守投影地图面：R5+双半宽）
- true   = v5.drc.hole_track_blocked（孔带真值带 0.25；仅 F3 在场）
- strict = v5.drc._actual_gap 谓词 gap < r5 - clearance.EPS（中心线世界）

权威面 = strict（CLOSURE-VERDICT §1 裁定链：strict/真 ingest 为权威；本件
照登不代裁）。差异记录经 v5.geometry_semantics.make_diff_record 构造、
write_strict_cons_diff 落盘（近阈值案件 multi_route_independent_evidence
恒 False——判据逐字执行）。
"""
import os

from v5 import geometry_semantics as gs
from v5 import drc
from v5.drc import Copper
from v5.metrics import clearance as cl

gs.declare_consumer("judge")                    # 幂等登记（judge 面）
GEOMETRY_SEMANTICS_VERSION = gs.VERSION         # 消费方可验出口

R5 = 0.5          # 有界 fixture 采样带（pmod-crypto 板 R5 同值；不读板、不外呼）
TRACK_HALF = 0.15

# 有界走廊 fixture 障碍（S5-02 C2 同构：线/焊盘/板固孔三种走廊）
_OBS_SEG = {"pads": [], "segs": [["F.Cu", [(0.0, 0.0), (10.0, 0.0)], 0.15]],
            "vias": [], "holes": [], "holes_all": [], "zones": []}
_OBS_PAD = {"pads": [(5.0, 0.0, 0.3)], "segs": [], "vias": [], "holes": [],
            "holes_all": [], "zones": []}
_OBS_HOLE = {"pads": [], "segs": [], "vias": [], "holes": [(5.0, 0.0, 0.15)],
             "holes_all": [(5.0, 0.0, 0.15)], "zones": []}
_FORE_TRACK = Copper("N2", "f", "F.Cu", polyline=[[0.0, 0.0], [10.0, 0.0]],
                     half_width=0.15)
_FORE_PAD = Copper("N2", "fp", "F.Cu", pad=((5.0, 0.0), 0.3))


def _import_pilot():
    """cons 面权威函数惰性 import（pilot 顶层带 canvas 依赖，按需加载）。"""
    from net_agent_pilot import pilot as plt
    return plt


def corridor_cases():
    """有界 fixture 案例清单（case_id, d, 障碍 dict, strict 对手铜, 备注）。"""
    cases = []
    for d in (0.5, 0.5 - 1e-6, 0.5 + 1e-6, 0.7):   # F1：track×track 走廊
        cases.append(("F1-track-track-corridor", d, _OBS_SEG, _FORE_TRACK,
                      "pitch=0.5 走廊；d=0.5=地图全#而验证器裸中心距恰=R5"))
    for d in (0.85, 0.7, 0.5):                     # F2：track×pad 走廊
        cases.append(("F2-pad-band-corridor", d, _OBS_PAD, _FORE_PAD,
                      "地图焊盘带=r+R5+半宽 vs strict=点线距−r_pad"))
    for d in (0.7, 0.6, 0.5):                      # F3：板固孔带
        cases.append(("F3-hole-band", d, _OBS_HOLE, _FORE_TRACK,
                      "cons=hr+R5+半宽 / true=hole_track_blocked"
                      "=hr+0.25+半宽"))
    return cases


def judge_case(case_id, d, obs, fore_cu, note):
    """单案三面对读（真实权威函数；返回携带版本声明的判读行）。"""
    plt = _import_pilot()
    cand = Copper("N1", "c", "F.Cu", polyline=[[4.5, d], [5.5, d]],
                  half_width=TRACK_HALF)
    gap = drc._actual_gap(cand, fore_cu)
    strict_blocked = gap < R5 - cl.EPS
    cons_reason = plt._blocked_at((5.0, d), obs, "F.Cu", R5)
    faces = {
        "cons": {"verdict": bool(cons_reason),
                 "authority": "net_agent_pilot.pilot::_blocked_at",
                 "semantics": "R5+双半宽保守投影", "inputs": {"r5": R5}},
        "strict": {"verdict": bool(strict_blocked),
                   "authority": "v5.drc::_actual_gap（谓词 gap<r5-EPS）",
                   "semantics": "中心线裸距", "gap_mm": gap,
                   "required_mm": R5},
    }
    if case_id.startswith("F3"):
        true_blocked = drc.hole_track_blocked((5.0, 0.0), 0.15, (4.5, d),
                                              (5.5, d), TRACK_HALF)
        faces["true"] = {"verdict": bool(true_blocked),
                         "authority": "v5.drc::hole_track_blocked",
                         "semantics": "孔带真值 0.25+半宽",
                         "inputs": {"hr": 0.15, "half": TRACK_HALF}}
    record = gs.make_diff_record(
        case_id=case_id + "@d=%g" % d, faces=faces,
        authority_face="strict",
        authority_rationale="CLOSURE-VERDICT §1 裁定链（strict/真 ingest 为"
                            "权威）；本 fixture 照登不代裁",
        replica_of=None, independent_paths=1,
        gap_mm=gap, required_mm=R5, net_id="N1")
    return {
        "case_id": record["case_id"], "param_d_mm": d, "note": note,
        "geometry_semantics": GEOMETRY_SEMANTICS_VERSION,
        "cons_blocked": faces["cons"]["verdict"],
        "strict_gap_mm": gap, "strict_blocked": strict_blocked,
        "divergent_cons_vs_strict":
            bool(faces["cons"]["verdict"]) and not strict_blocked,
        "diff_record": record,
    }


def run_corridor_fixtures():
    """全部有界案例（每行自带版本声明=judge 面最小可验出口）。"""
    return [judge_case(*case) for case in corridor_cases()]


def write_diff_json(path, world=None, overwrite=False):
    """差异 JSON 落盘（gs.write_strict_cons_diff 钩子；缺省拒绝覆盖）。"""
    records = [row["diff_record"] for row in run_corridor_fixtures()]
    return gs.write_strict_cons_diff(records, path, world=world,
                                     overwrite=overwrite)


def consumer_manifest(world=None):
    """judge 面消费方 manifest（版本+登记+有界案例计数）。"""
    m = gs.consumer_manifest(world=world)
    m["judge_fixture_cases"] = len(corridor_cases())
    return m
