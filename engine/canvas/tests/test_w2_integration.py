# -*- coding: utf-8 -*-
"""波2 接线回归（编排体 2026-09-25 收口件）。

lane-m4 §5 接线契约 + lane-m5 §6 遗留接线的回归锚——validate↔placecheck
三动作接线、R6 前置拒收、词表波2 追加码、相对→绝对折算单源、真板包络
结构性拒收（lane-m4 §3.1 披露在接线后的表现面）。占位测试改写不重复
（见 test_k1_protocol/test_k1_validate 同名件）。
"""
from canvas import protocol as cpr
from canvas import validate as cval
from canvas.tests.test_k1_fixtures import real_state, run_batch, synth_state
from canvas.tests.test_m5_fixtures import m5_state


def test_vocab_wave2_appended_codes():
    """词表波2 追加码（追加式只增）: 三新码在册、不与旧码撞值。"""
    for name in ("E_UNKNOWN_PARTITION", "V_PLACEMENT_EDGE", "V_KEEPOUT"):
        val = getattr(cpr, name)
        assert isinstance(val, str) and val == name
    codes = [cpr.E_UNKNOWN_PARTITION, cpr.V_PLACEMENT_EDGE, cpr.V_KEEPOUT]
    legacy = [cpr.V_CLEARANCE, cpr.V_EDGE, cpr.V_PLACEMENT_COLLISION,
              cpr.E_GRID_OUT_OF_BOUNDS, cpr.E_UNKNOWN_NET]
    assert not set(codes) & set(legacy)


def test_absolute_candidate_relative_folding():
    """相对→绝对折算单源: rotate=(cur+turns)%4、flip=取反、move=绝对 target;
    承袭经 merge_candidate（无覆盖分区恒等覆盖起算）。"""
    st = synth_state()
    assert cpr.absolute_candidate(st, {"action": "move", "partition_id": "PA",
                                       "target": [7, 9]}) == {"move": [7, 9]}
    assert cpr.absolute_candidate(st, {"action": "rotate", "partition_id": "PA",
                                       "turns": 3}) == {"rotate": 3}
    assert cpr.absolute_candidate(st, {"action": "flip",
                                       "partition_id": "PA"}) == {"flip": True}
    run_batch(st, [{"action": "rotate", "partition_id": "PA", "turns": 2},
                   {"action": "submit"}])
    assert st.placement("PA")["rotate"] == 2
    # 再转 2 轮=2+2 %4=0（跨动作相对累积，单源折算）
    assert cpr.absolute_candidate(st, {"action": "rotate", "partition_id": "PA",
                                       "turns": 2}) == {"rotate": 0}
    run_batch(st, [{"action": "flip", "partition_id": "PA"},
                   {"action": "submit"}])
    assert st.placement("PA") == {"move": None, "rotate": 2, "flip": True}


def test_apply_batch_placement_roundtrip_and_effective_anchors():
    """apply 侧落盘接线: flip 接受后 effective_anchors 换算生效（覆盖后
    锚格点重 snap），state_sha256 随覆盖变更（确定性账本一致性）。"""
    st = synth_state()
    before_sha = None
    from canvas import state as cstate
    before_sha = cstate.state_sha256(st)
    base_anchors = [list(a) for a in st.effective_anchors("PA")]
    run_batch(st, [{"action": "flip", "partition_id": "PA"},
                   {"action": "submit"}])
    assert cstate.state_sha256(st) != before_sha
    # 2-pad 水平分区 flip=x 镜像→端点对调（snap 回原格点集，序对调）
    flipped = [list(a) for a in st.effective_anchors("PA")]
    assert sorted(map(tuple, flipped)) == sorted(map(tuple, base_anchors))


def test_r6_prefilter_code_surfaces():
    """R6 前置拒收码面: apply 层 detail 含 zone 标识; 词表外无 R6 直码
    （全态兜底才报 rule=R6——两层口径分离）。"""
    st = m5_state()
    results = run_batch(st, [{"action": "tuning", "net_id": "NET-T2",
                              "group_id": "LG-X", "kind": "detour",
                              "params": {"offset_mm": 0.5}}])
    tun = results[0]
    assert tun["accepted"] is False and tun["code"] == "V_KEEPOUT"
    assert "zone" in (tun.get("detail") or "")
    assert not hasattr(cpr, "V_R6")           # R6 不入编辑侧词表（兜底口径）


def test_r6_prefilter_route_and_via():
    """R6 前置扩展到 route/via（lane-m2x §6.2 缝披露收口，编排体接线）:
    穿 keepout 的 route 拒收 V_KEEPOUT=zone 标识; 锚到锚净空路径照常接受;
    via 面单元验证（合法段+触 zone via 在前置后几何不可能——段 waypoint
    即 via 格点，两者同源等价禁入，故 via 面以 r6_prefilter_detail+
    instantiate.via_coppers 单元钉死）。"""
    st = m5_state()
    got = cval.validate_edit(st, {"action": "route", "net_id": "NET-T1",
                                  "waypoints": [[4, 4], [12, 7], [20, 4]],
                                  "layer": "F.Cu"})
    assert got == (False, "V_KEEPOUT", "zone:Z1")
    clean = cval.validate_edit(st, {"action": "route", "net_id": "NET-T1",
                                    "waypoints": [[4, 4], [4, 2], [20, 2],
                                                  [20, 4]],
                                    "layer": "F.Cu"})
    assert clean == (True, None, None)
    from canvas import instantiate as inst
    fake = {"shape_id": "cand:via", "net_id": "NET-T1", "grid": [12, 20]}
    assert cval.r6_prefilter_detail(
        st, inst.via_coppers(st, [fake])) == "zone:Z2"


def test_real_board_placement_structural_reject():
    """真板包络结构性拒收（lane-m4 §3.1 披露的接线后表现）: badgeleds
    真板 36 分区对中 28 对包络基线重叠——一切 move/rotate/flip 候选
    V_PLACEMENT_COLLISION（fail-closed，不放行不静默）。"""
    st = real_state()
    pid = sorted(st.known_partitions())[0]
    anchor = st.anchors[pid][0]
    for action in ({"action": "move", "partition_id": pid,
                    "target": list(anchor)},
                   {"action": "rotate", "partition_id": pid, "turns": 1},
                   {"action": "flip", "partition_id": pid}):
        ok, code, detail = cval.validate_edit(st, action)
        assert ok is False and code in ("V_PLACEMENT_COLLISION",
                                        "V_PLACEMENT_EDGE"), (action, code)
    assert st.placements == {}                 # 拒收不落覆盖
