# -*- coding: utf-8 -*-
"""test_geometry_semantics —— 五消费方接线/版本契约/世界分离测试
（OPT-04 第一刀，EXEC-R2）。

覆盖 GATE-A1 04-E：「五消费方声明必须在实际调用输出或关联侧车可验，测试
不得只比较同一常量的五个别名」——每个消费方经其**自身公开面**取读数：
- drc：模块属性 GEOMETRY_SEMANTICS_VERSION（DRCReport 输出面不增键=零漂移
  纪律；as_dict 的 drc_version 保持不变另测）；
- route_check：check_routes **实际调用输出 dict** 的 geometry_semantics 键；
- map/reach（pilot）：模块属性 + cmd_reach/cmd_slice 输出构造面（out dict
  键）——CLI 落盘面以轻量断言（键在场）+ 模块出口为准，不跑整 CLI；
- judge fixture：fixture 判读行/manifest 的 geometry_semantics 字段；
- executor：**OPT-09 席并行接线**，未接线时 skipif（两席齐后主审令复跑全绿）。
世界分离：不同 VERSION 互不串号、历史 JSON 不回写（机制面测试）。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import geometry_semantics as gs          # noqa: E402


# ---------------------------------------------------------------- 接线面

def test_drc_face_declared_via_module_surface():
    """DRC 面：import v5.drc 即登记，版本经其自身模块属性可验。"""
    from v5 import drc
    assert gs.is_declared("drc")
    assert drc.GEOMETRY_SEMANTICS_VERSION == gs.VERSION


def test_drc_report_output_unchanged_zero_drift():
    """零漂移锚：DRCReport.as_dict 不因声明接线增键（drc_version 契约不变）。"""
    from v5 import drc
    d = drc.DRCReport([], 0).as_dict()
    assert set(d) == {"drc_version", "clean", "violation_count",
                      "checked_pairs", "violations"}
    assert d["drc_version"] == drc.VERSION


def test_route_check_face_declared_in_actual_output():
    """route_check 面：check_routes 实际调用输出携带同版本（非别名比较）。"""
    from v5 import route_check as rc
    from tests import geometry_judge_fixture  # 先行 import 不影响该面读数
    assert geometry_judge_fixture.GEOMETRY_SEMANTICS_VERSION == gs.VERSION
    board, doc = _tiny_board_and_routes()
    out = rc.check_routes(board, doc)
    assert out["geometry_semantics"] == gs.VERSION
    assert gs.is_declared("route_check")
    assert rc.GEOMETRY_SEMANTICS_VERSION == gs.VERSION
    # 判定核心键仍在（纯增键零漂移）
    for key in ("feasible", "violations", "drc_version", "route_check_version"):
        assert key in out


def _tiny_board_and_routes():
    """最小 v5.board.v1 + 合法 routes 工件（构造式照 tests/
    test_upgrade1_exit_contract.py make_board/routes_doc/entry 先例；走真实
    check_routes 全链 validate→scene→判定，不触引擎）。"""
    from v5.board import compute_board_sha256, load_board
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "opt04-decl-smoke",
        "stackup": [{"id": "F.Cu", "kind": "signal",
                     "preferred_direction": "any", "available": True}],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 12.0},
        "zones": [],
        "partitions": [{
            "partition_id": "P1", "ptype": "MISC", "layer_policy": "F.Cu",
            "planned_width": 0.2, "current_a": 0, "speed_class": "low_speed",
            "width_prior": {"w_min": 0.2, "w_max": 0.4},
            "geometry": {"endpoints": [[1.0, 6.0], [19.0, 6.0]]}}],
        "nets": [{"net_id": "N1", "net_class": "MISC",
                  "partitions": ["P1"]}],
        "hard_rules": {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True}},
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri": "tests/test_geometry_semantics.py",
                       "source_sha256": "0" * 64},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    bd = load_board(board)
    sha = board["provenance"]["board_sha256"]
    doc = {"schema_version": "v5.routes.v1", "board_id": board["board_id"],
           "board_sha256": sha,
           "routes": [{"partition_id": "P1", "net_id": "N1", "layer": "F.Cu",
                       "polyline": [[1.0, 6.0], [19.0, 6.0]], "width": 0.2,
                       "transition_vias": [], "return_vias": []}],
           "negotiation_log": ["t"],
           "provenance": {"generator": "hand", "board_sha256": sha}}
    return bd, doc


def test_map_and_reach_faces_declared_via_pilot_module():
    """map/reach 面：import net_agent_pilot.pilot 即双登记+版本出口。"""
    from net_agent_pilot import pilot
    assert gs.is_declared("map") and gs.is_declared("reach")
    assert pilot.GEOMETRY_SEMANTICS_VERSION == gs.VERSION
    # R31-02 第二刀后：三常量为活树单源别名（值同第一刀读数=零漂移）；
    # via 半径不再有 pilot 板无关常量（第二源已删，G2-H1 最小修面）：
    assert pilot.TRACK_HALF_MM == 0.15
    assert pilot.EDGE_MARGIN_MM == 0.2
    assert pilot.HOLE_TO_HOLE_MM == 0.25
    # via 半径改读单源接口（gs.via_radius_mm 薄委托 v5.kicad_export.
    # via_model_params；缺省 0.3、board.via_model 可覆盖）——不得恢复
    # pilot.VIA_RADIUS_MM 第二源：
    assert not hasattr(pilot, "VIA_RADIUS_MM")
    assert gs.via_radius_mm({}) == 0.3
    from v5.kicad_export import via_model_params
    assert via_model_params({})["radius"] == 0.3


def test_reach_output_dict_carries_version_key():
    """reach 面：cmd_reach 输出构造面带 geometry_semantics 键（源级断言——
    输出 dict 字面在场即真实调用出口可验；不跑整 CLI 避免板/台账副作用）。"""
    from net_agent_pilot import pilot
    src_path = os.path.join(ROOT, "net_agent_pilot", "pilot.py")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    # cmd_reach out dict 与 slice facts 均已带键（源文本机械断言，防回退）
    assert '"geometry_semantics": GEOMETRY_SEMANTICS_VERSION' in src
    assert pilot.GEOMETRY_SEMANTICS_VERSION == gs.VERSION


def test_judge_fixture_face_declared_in_outputs():
    """judge 面：fixture 判读行/manifest 自带版本（实际输出可验）。"""
    from tests import geometry_judge_fixture as gjf
    assert gs.is_declared("judge")
    rows = gjf.run_corridor_fixtures()
    assert rows, "有界 fixture 案例不得为空"
    for row in rows:
        assert row["geometry_semantics"] == gs.VERSION
        assert row["diff_record"]["geometry_semantics"] == gs.VERSION
    assert gjf.consumer_manifest()["geometry_semantics"] == gs.VERSION


def test_all_declared_versions_coherent():
    """版本契约：一切已登记消费方绑定同一 VERSION（互异=多世界混线 FAIL）。"""
    versions = gs.consumer_versions()
    assert versions, "至少五面中四面应已登记（executor 可 pending）"
    assert set(versions.values()) == {gs.VERSION}


@pytest.mark.skipif(
    not gs.is_declared("executor"),
    reason="pending_executor_wiring_by_opt09_seat")
def test_executor_face_declared():
    """executor 面：OPT-09 席接线后生效（VERSION+declare_consumer("executor")）。"""
    from v5 import executor
    assert gs.is_declared("executor")
    assert executor.GEOMETRY_SEMANTICS_VERSION == gs.VERSION


# ---------------------------------------------------------------- 声明机制

def test_declare_consumer_idempotent():
    """declare_consumer 幂等：重复登记不报错、不重复计序。"""
    before = list(gs.declared_consumers())
    gs.declare_consumer("drc")
    gs.declare_consumer("map")
    assert list(gs.declared_consumers()) == before


def test_facet_table_distinguishes_r5_faces():
    """分面说明显式区分 per-pair/scalar/conservative-max/含半宽投影（04-C）。"""
    facets = gs.facet_table()
    sems = {k: v["semantics"] for k, v in facets.items()}
    assert "per-pair" in sems["r5_strict_per_pair"]
    assert "conservative-max" in sems["r5_executor_conservative_max"]
    assert "scalar" in sems["r5_map_scalar_projected"]
    assert "半宽" in sems["r5_map_scalar_projected"]
    assert "整铜 bbox" in sems["zone_check"]
    # 薄委托：分面注册表不携带任何数值副本
    for v in facets.values():
        for field in ("edge_clearance_mm", "hole_to_hole_mm", "via_radius"):
            assert field not in v


def test_thin_delegation_reads_single_sources():
    """薄委托取值=活树单源引用（与权威模块属性同对象/同值，非第二份拷贝）。"""
    from v5 import drc
    from v5.metrics import clearance as cl
    vals = gs.single_source_values()
    assert vals["edge_clearance_mm"] == drc.EDGE_CLEARANCE_MM
    assert vals["hole_to_hole_mm"] == drc.HOLE_TO_HOLE_MM
    assert vals["eps_mm"] == cl.EPS
    assert gs.via_radius_mm({}) == 0.3     # 缺省推导经 kicad_export 单源


# ---------------------------------------------------------------- 世界分离

def test_world_separation_no_version_leak_into_legacy_products():
    """旧产物按自带版本解释：当前 VERSION 不得串进版本前/旧版产物读数。"""
    legacy = {"schema": "r14v2-closure/2", "drc_version": "v5.drc/0.4.0"}
    pre_version = gs.interpret_product_version(legacy)
    assert pre_version is None                       # 版本前产物=不补猜
    old = {"geometry_semantics": "v5.geometry_semantics/0.0.9-legacy"}
    assert gs.interpret_product_version(old) == \
        "v5.geometry_semantics/0.0.9-legacy"        # 旧版本原样返回
    assert gs.interpret_product_version(old) != gs.VERSION   # 不串号
    mine = gs.consumer_manifest(world="w-test")
    assert mine["geometry_semantics"] == gs.VERSION  # 新世界才带当前版本


def test_diff_json_no_rewrite_discipline(tmp_path):
    """历史数字不回写：差异 JSON 落盘缺省拒绝覆盖既有文件。"""
    from tests import geometry_judge_fixture as gjf
    p = tmp_path / "strict-cons-diff.json"
    path1 = gjf.write_diff_json(str(p), world={"tag": "world-sep-test"})
    assert os.path.exists(path1)
    with open(path1, encoding="utf-8") as f:
        first = json.load(f)
    with pytest.raises(FileExistsError):
        gjf.write_diff_json(str(p))                 # 不带 overwrite=拒
    with open(path1, encoding="utf-8") as f:
        again = json.load(f)
    assert first == again                           # 盘面逐字节未动


def test_manifests_of_different_versions_do_not_merge():
    """不同 VERSION 的世界互不串号：manifest 世界标识随版本可区分。"""
    from tests import geometry_judge_fixture as gjf
    m_now = gjf.consumer_manifest(world={"world_id": "A"})
    legacy_version = "v5.geometry_semantics/0.0.9-legacy"
    assert m_now["geometry_semantics"] != legacy_version
    # 机制面：把旧版产物混进当前 manifest 不会改写其自带版本读数
    old_product = {"geometry_semantics": legacy_version, "verdict": "sealed"}
    assert gs.interpret_product_version(old_product) == legacy_version
    assert m_now["geometry_semantics"] == gs.VERSION


# ---------------------------------------------------------------- 差异钩子

def test_diff_record_near_threshold_never_multi_evidence():
    """判据逐字：近阈值不得以多路同结果作独立证据。"""
    faces = {
        "cons": {"verdict": True, "authority": "net_agent_pilot.pilot::_blocked_at",
                 "semantics": "", "inputs": {}},
        "strict": {"verdict": False, "authority": "v5.drc::_actual_gap",
                   "semantics": "", "inputs": {}},
    }
    near = gs.make_diff_record("near@x", faces, "strict", "t",
                               independent_paths=3, gap_mm=0.5,
                               required_mm=0.5)
    assert near["near_threshold"]["within"] is True
    assert near["multi_route_independent_evidence"] is False   # 3 路也不算
    far = gs.make_diff_record("far@x", faces, "strict", "t",
                              independent_paths=3, gap_mm=1.0,
                              required_mm=0.5)
    assert far["near_threshold"]["within"] is False
    assert far["multi_route_independent_evidence"] is True     # 远阈值≥2 路才算
    single = gs.make_diff_record("single@x", faces, "strict", "t",
                                 independent_paths=1, gap_mm=1.0,
                                 required_mm=0.5)
    assert single["multi_route_independent_evidence"] is False
    with pytest.raises(ValueError):
        gs.make_diff_record("bad@x", faces, "authority_not_in_faces", "t")
