# -*- coding: utf-8 -*-
"""V5-DIAG-REPLAY-R1 W-4 新钉：归因器 1.1.0 双面重放合同对齐钉+板端到端
归因钉+run_diag 入口确定性钉+witness 探针双口径钉。

合同锚（out/v5-p5/diag-replay-r1/PREREG-DIAG-REPLAY-R1.md §3/§4 冻结）：
- W-1 0.9.0 主锚面：replay_capture 镜像 0.9.0 主环（SC-1 事前短路+多端网
  Steiner 边序）；verdict_provenance 出口读数对账；exhaustion-cause 新类
  sealed-short-circuit。
- W-1 0.8.0 存档忠实重放面：0.9.0-only 单行不入 0.8.0 对账集；短路主链
  不剔（整路短路与 0.8.0 阶梯体互不可 strip）。
- W-4 端到端：syn-u01（0.9.0 短路面）与 atmega32u4-breakout（0.8.0 存档
  面）双面各 ≥1 板端到端归因钉。
- W-5 双口径：r1_failed_net_probe 1.1 版本登记+pad-pad/track-ray 双口径
  显式化；tmp108 判读锚=两口径均密封（PREREG §4）。
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "out", "v5-p5", "diag-replay-r1"))

import v5_diag_inherent as D  # noqa: E402
import r1_failed_net_probe as P  # noqa: E402

SYNTH = os.path.join(ROOT, "boards", "synth-r1")
SYN_U01_EXEC = os.path.join(ROOT, "out", "v5-p5", "exec-eng-r1", "boards",
                            "syn-u01", "execute.json")
SYN_U01_BOARD = os.path.join(SYNTH, "syn-u01.board.v1.json")
ATMega = os.path.join(ROOT, "out", "v5-p5", "boards", "atmega32u4-breakout")
TMP108_BOARD = os.path.join(ROOT, "out", "v5-p5", "boards", "tmp108",
                            "board.json")
HAVE_SYN_U01 = os.path.isfile(SYN_U01_EXEC) and os.path.isfile(SYN_U01_BOARD)
HAVE_ATMEGA = os.path.isfile(os.path.join(ATMega, "board.json")) \
    and os.path.isfile(os.path.join(ATMega, "execute.json"))
HAVE_SKELETON_SRC = os.path.isfile(os.path.join(SYNTH,
                                                "syn-u09.board.v1.json"))


# ------------------------------------------------ 最小密封板 fixture（A1 同源）

def _skeleton(board_id):
    with open(os.path.join(SYNTH, "syn-u09.board.v1.json"),
              encoding="utf-8") as f:
        src = json.load(f)
    return {
        "schema_version": src["schema_version"], "board_id": board_id,
        "workspace": {"x_min": 8.0, "y_min": 8.5, "x_max": 12.0,
                      "y_max": 12.0},
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "available": True,
             "preferred_direction": "h"},
            {"id": "In1.Cu", "kind": "signal", "available": True,
             "preferred_direction": "v"}],
        "hard_rules": src["hard_rules"],
        "principle_registry": src["principle_registry"],
        "holes": [], "zones": [], "nets": [], "partitions": []}


def _route_partition(board, pid, a, b, net="N1"):
    board["nets"].append({"net_id": net, "net_class": "MISC",
                          "partitions": [pid]})
    board["partitions"].append({
        "partition_id": pid, "ptype": "MISC", "net_id": None,
        "layer_policy": "F.Cu", "planned_width": 0.2, "current_a": 0.0,
        "speed_class": "low_speed",
        "width_prior": {"w_min": 0.2, "w_max": 0.4},
        "geometry": {"endpoints": [[float(a[0]), float(a[1])],
                                   [float(b[0]), float(b[1])]]}})


def _pad_partition(board, pid, center, size_mm=(2.6, 2.6), layers="all",
                   net="NSEAL"):
    board["nets"].append({"net_id": net, "net_class": "MISC",
                          "partitions": [pid]})
    board["partitions"].append({
        "partition_id": pid, "ptype": "MISC", "net_id": None,
        "layer_policy": "F.Cu", "planned_width": 0.2, "current_a": 0.0,
        "speed_class": "low_speed",
        "width_prior": {"w_min": 0.2, "w_max": 0.4},
        "geometry": {"endpoints": [[float(center[0]), float(center[1])],
                                   [float(center[0]), float(center[1])]],
                     "pad_terminals": [{"endpoint": 0, "layers": layers,
                                        "shape": "rect",
                                        "size_mm": [size_mm[0],
                                                    size_mm[1]]}]}})


def _minimal_sealed_board():
    board = _skeleton("diag-sc1-minimal")
    _route_partition(board, "P1", (9.0, 10.0), (11.0, 10.0), net="N1")
    _pad_partition(board, "PSEAL", (11.0, 10.0), size_mm=(2.6, 2.6),
                   layers="all", net="NSEAL")
    return board


def _minimal_open_board():
    """非密封最小板：仅 P1 路由分区（零固定铜→SC-1 普查必不密封，
    P1 布通——0.8.0 阶梯体同形+零 log 增量验证面）。"""
    board = _skeleton("diag-sc1-open")
    _route_partition(board, "P1", (9.0, 10.0), (11.0, 10.0), net="N1")
    return board


def _cand(board):
    layer = board["stackup"][0]["id"]
    return {"route_order": [p["partition_id"] for p in board["partitions"]],
            "layer_assignment": {p["partition_id"]: layer
                                 for p in board["partitions"]}}


# ------------------------------------------------ 合同对齐钉（纯单元/最小板）

def test_tool_version_1_1_0_and_sc_constants():
    assert D.TOOL_VERSION == "v5.diag_inherent/1.1.1"   # 1.1.1=判读修复轮
    assert D.SC_CAUSE_PREFIX == "sealed-short-circuit"
    assert D.V090_ONLY_MARKS == (" preflight-seal-survey:",
                                 " preflight-seal-abstain:")
    assert D._SEAL_CLASSES == ("routes", "vias", "holes", "edge", "fixed",
                               "all-geometric")


def test_strip_v090_only_strips_disclosure_single_rows_only():
    log = [
        "partition=P1 preflight-seal-survey: ladder_partitions=1（x）",
        "net=N1 partition=P1 preflight-seal-abstain: cross_check mismatch",
        "net=N1 partition=P1 committed attempt=1 variant=prefer",
        "net=N1 partition=P1 FAILED after 0 attempts: constructive-unroutable",
        "net=N1 partition=P1 exhaustion-cause=sealed-short-circuit（x）",
        "net=N1 partition=P1 geom-secondary=fixed-copper-sealed（x）",
        "net=N1 partition=P1 short-circuit-basis: sealed_endpoint=e0",
    ]
    out = D.strip_v090_only(log)
    # 披露单行剔除；短路主链四行保留（整路短路与 0.8.0 阶梯体互不可 strip）
    assert out == log[2:]
    # geom-secondary 行仍走既有 0.6.1 容差面
    assert D.strip_geom2(out) == log[2:5] + log[6:]


def test_detect_execute_face_markers():
    ex090a = {"verdict_provenance": "execute-short-circuit:sealed-short-"
              "circuit（x）", "execute": {"negotiation_log": []}}
    assert D.detect_execute_face(ex090a)[0] == "0.9.0-main"
    ex090b = {"execute": {"negotiation_log": [
        "net=N1 partition=P1 short-circuit-basis: sealed_endpoint=e0"]}}
    assert D.detect_execute_face(ex090b)[0] == "0.9.0-main"
    ex080 = {"provenance": {"generator": "v5.p5-board-runner"},
             "execute": {"negotiation_log": [
                 "net=GND partition=PT-GND FAILED after 238 attempts: x",
                 "net=GND partition=PT-GND exhaustion-cause=obstacle-dense",
                 "net=GND partition=PT-GND geom-secondary=open"]}}
    face, markers = D.detect_execute_face(ex080)
    assert face == "0.8.0-archive"
    assert markers == {"verdict_provenance_top": False,
                       "short_circuit_row": False,
                       "generator": "v5.p5-board-runner"}


@pytest.mark.skipif(not HAVE_SKELETON_SRC,
                    reason="boards/synth-r1/syn-u09.board.v1.json 缺")
def test_replay_capture_short_circuit_mirror_fidelity():
    """0.9.0 主锚面镜像保真：最小密封板上 replay_capture 的
    negotiation_log 与 execute_candidate 逐字节同形；短路捕获态字段齐。"""
    from v5.executor import execute_candidate
    board = _minimal_sealed_board()
    cand = _cand(board)
    rep = D.replay_capture(board, cand)
    eng = execute_candidate(board, cand)
    assert rep["verdict"] == "FAILED" and rep["short_circuit"] is True
    assert rep["negotiation_log"] == eng["negotiation_log"]
    log = rep["negotiation_log"]
    assert len(log) == 5   # 五行证据链
    assert log[0].startswith("partition=P1 preflight-seal-survey: ")
    assert "FAILED after 0 attempts: constructive-unroutable" in log[1]
    assert "exhaustion-cause=sealed-short-circuit" in log[2]
    assert " geom-secondary=" in log[3]
    assert log[4].startswith("net=N1 partition=P1 short-circuit-basis: "
                             "sealed_endpoint=e1 ")
    cap = rep["capture"]
    assert cap["pid"] == "P1" and cap["net_id"] == "N1"
    assert cap["attempts"] == 0
    assert cap["cause"].startswith("sealed-short-circuit")
    assert cap["short_circuit"] is True
    assert cap["sealed_endpoint_index"] == 1
    assert cap["sealing_cids"]   # 密封铜指认非空
    # witness 试点=密封端点×分区另端
    assert cap["a_pt"] == (11.0, 10.0) and cap["b_pt"] == (9.0, 10.0)


@pytest.mark.skipif(not HAVE_SKELETON_SRC,
                    reason="boards/synth-r1/syn-u09.board.v1.json 缺")
def test_replay_capture_nonsealed_zero_log_delta():
    """非密封板零 log 增量（0.8.0 阶梯体同形）：镜像主环 log 与引擎逐字节
    等（引擎 ROUTED 出口的 final route_check 自检行=出口面，重放合同外）。"""
    from v5.executor import execute_candidate
    board = _minimal_open_board()
    cand = _cand(board)
    rep = D.replay_capture(board, cand)
    eng = execute_candidate(board, cand)
    assert eng["verdict"] == "ROUTED"
    assert eng["negotiation_log"][-1].startswith(
        "final route_check feasible=True")
    assert rep["short_circuit"] is False
    assert rep["negotiation_log"] == eng["negotiation_log"][:-1]
    assert not [l for l in rep["negotiation_log"]
                if "preflight-seal" in l or "short-circuit-basis" in l]


@pytest.mark.skipif(not HAVE_SKELETON_SRC,
                    reason="boards/synth-r1/syn-u09.board.v1.json 缺")
def test_replay_capture_multiendpoint_topology_face():
    """0.8.0 多端网显式 Steiner 拓扑面：多端网分区经 _edge_sequences/
    _run_net_ladder 镜像（本例 ROUTED 面 log 同形；失败面 topology-edge/
    fallback-mst 行集的逐字节复现由 atmega32u4-breakout 端到端钉覆盖——
    其 244 行 0.8.0 档案含 topology-edge=M8/回退行）。"""
    from v5.executor import execute_candidate
    board = _skeleton("diag-multi-ep")
    _route_partition(board, "P1", (9.0, 10.0), (11.0, 10.0), net="N1")
    board["nets"].append({"net_id": "NM", "net_class": "MISC",
                          "partitions": ["PM"]})
    board["partitions"].append({
        "partition_id": "PM", "ptype": "MISC", "net_id": None,
        "layer_policy": "F.Cu", "planned_width": 0.2, "current_a": 0.0,
        "speed_class": "low_speed",
        "width_prior": {"w_min": 0.2, "w_max": 0.4},
        "geometry": {"endpoints": [[8.5, 9.0], [8.5, 11.5], [10.0, 10.25]]}})
    board["topology"] = {"PM": {
        "nodes": [[8.5, 9.0], [8.5, 11.5], [10.0, 10.25]],
        "edges": [[0, 1], [1, 2]], "terminal_count": 3, "total_mm": 5.5,
        "provenance": {"algorithm": "mst", "method": "test-fixture"}}}
    cand = _cand(board)
    rep = D.replay_capture(board, cand)
    eng = execute_candidate(board, cand)
    assert eng["verdict"] == "ROUTED"   # 多端网布通（拓扑面无失败行）
    assert rep["negotiation_log"] == eng["negotiation_log"][:-1]
    assert rep["short_circuit"] is False


def test_verdict_provenance_reconciliation_tolerant_on_080_face():
    """0.9.0-only 出口面（verdict_provenance）不入 0.8.0 档案对账集：
    0.8.0 face 档案无该键=match None（不计数）；0.9.0 face 有键=布尔对账。"""
    # 纯字段语义钉（无世界依赖）：_verdict_provenance 消费面
    import v5.executor as EX
    assert EX._verdict_provenance("FAILED", None) is None
    assert EX._verdict_provenance(
        "FAILED", "UNKNOWN", short_circuit=True) == (
        "execute-short-circuit:sealed-short-circuit"
        "（事前短路：全层异网固定铜密封构造性无解）")
    assert EX._verdict_provenance("FAILED", "UNKNOWN").startswith(
        "execute-exhausted")


# ------------------------------------------------ 板端到端归因钉（W-4 要件）

SYN_U02_EXEC = os.path.join(ROOT, "out", "v5-p5", "exec-eng-r1", "boards",
                            "syn-u02", "execute.json")
SYN_U02_BOARD = os.path.join(SYNTH, "syn-u02.board.v1.json")
HAVE_SYN_U02 = os.path.isfile(SYN_U02_EXEC) and os.path.isfile(SYN_U02_BOARD)


@pytest.mark.skipif(not HAVE_SYN_U02, reason="syn-u02 板件/execute.json 缺")
def test_e2e_syn_u02_seal_domain_removal_regression():
    """判读修复回归钉（D-J3 工具面根因）：syn-u02 另端 (21.5,22.75) 在
    keepout KO01（rect 20.75–23.0×20.0–24.25 全层）内——1.1.0 梯面试点
    口径六类摘除均「A* 空间耗尽」→误报 undetermined；1.1.1 起短路捕获态
    终判面=密封域口径（摘类→复跑 seal-survey→S(e) 解封判）→(a)，梯面
    六行降为 ladder_removal_unlock 诊断披露（保留 keepout 混入证据）。"""
    doc, code = D.diagnose(SYN_U02_BOARD, SYN_U02_EXEC,
                           board_name="syn-u02")
    assert code == 0
    assert doc["replay"]["faithful_raw_byte_equal"] is True
    assert doc["failed_net"]["exhaustion_cause"].startswith(
        "sealed-short-circuit")
    w = doc["witness"]
    unlock = {r["class"]: r["unlocked"] for r in w["class_removal_unlock"]}
    assert unlock == {"routes": False, "vias": False, "holes": False,
                      "edge": False, "fixed": True, "all-geometric": True}
    assert w["minimal_removal_class_to_unlock"] == "fixed"
    # 密封域行读数=seal-survey（非梯面试点 attempts）
    fixed_row = next(r for r in w["class_removal_unlock"]
                     if r["class"] == "fixed")
    assert fixed_row["attempts"] == 0
    assert "seal-survey" in fixed_row["reason"] and "解封" in fixed_row["reason"]
    # 梯面诊断披露保留：另端 keepout 混入面如实可见（六行全锁；计划面=
    # 基线 5 变体——不可达在基线尝试即定局）
    lad = {r["class"]: r["unlocked"] for r in w["ladder_removal_unlock"]}
    assert lad == {"routes": False, "vias": False, "holes": False,
                   "edge": False, "fixed": False, "all-geometric": False}
    assert all(r["attempts"] <= 5
               for r in w["ladder_removal_unlock"])
    assert "不参与终判" in w["ladder_removal_note"]
    assert doc["verdict"]["class"] == "(a) 板设计固有不可布"


@pytest.mark.skipif(not HAVE_SKELETON_SRC,
                    reason="boards/synth-r1/syn-u09.board.v1.json 缺")
def test_seal_removal_domain_on_minimal_board():
    """密封域口径单元钉（最小密封板）：class_removal_unlock 走 seal-survey
    （fixed/all-geometric 解封、routes 仍封）；ladder_removal_unlock 同板
    梯面读数（本板另端无 keepout 混入——fixed 摘除梯面亦可解锁）。"""
    board = _minimal_sealed_board()
    cand = _cand(board)
    rep = D.replay_capture(board, cand)
    assert rep["short_circuit"] is True
    cap = rep["capture"]
    ctx = cap["ctx"]
    w = D.analyze_witness(ctx, cap, pitches=(0.25,))
    unlock = {r["class"]: r["unlocked"] for r in w["class_removal_unlock"]}
    assert unlock == {"routes": False, "vias": False, "holes": False,
                      "edge": False, "fixed": True, "all-geometric": True}
    lad = {r["class"]: r["unlocked"] for r in w["ladder_removal_unlock"]}
    assert lad["fixed"] is True and lad["routes"] is False
    # 摘除还原完整性：seal-survey 六轮后密封读数可复现（探针态零泄漏）
    rows = __import__("v5.executor", fromlist=["x"])._seal_survey_rows(
        ctx, cap["route_order"])
    hit = next(r for r in rows if r["partition"] == "P1" and r["sealed"])
    assert hit["endpoint_index"] == 1


@pytest.mark.skipif(not HAVE_SYN_U01, reason="syn-u01 板件/execute.json 缺")
def test_e2e_syn_u01_090_main_face_attribution():
    """0.9.0 主锚面端到端：u 族短路终态 execute.json 重放 byte-equal、
    verdict_provenance 对账一致、三分类=(a)（truth_rule=构造不可布→板固有
    固定铜密封）、SC-1 捕获态 witness（fixed 摘除解锁/routes 仍锁）。"""
    doc, code = D.diagnose(SYN_U01_BOARD, SYN_U01_EXEC,
                           board_name="syn-u01")
    assert code == 0
    rep = doc["replay"]
    assert rep["execute_face"] == "0.9.0-main"
    assert rep["short_circuit_replay"] is True
    assert rep["verdict"] == "FAILED"
    assert rep["faithful"] is True
    assert rep["faithful_raw_byte_equal"] is True   # 五行短路链逐字节等
    assert rep["verdict_provenance_match"] is True
    fn = doc["failed_net"]
    assert fn["net"] == "NBLK" and fn["partition"] == "PBLK"
    assert fn["attempts"] == 0
    assert fn["exhaustion_cause"].startswith("sealed-short-circuit")
    w = doc["witness"]
    unlock = {r["class"]: r["unlocked"] for r in w["class_removal_unlock"]}
    assert unlock == {"routes": False, "vias": False, "holes": False,
                      "edge": False, "fixed": True, "all-geometric": True}
    assert w["minimal_removal_class_to_unlock"] == "fixed"
    assert w["short_circuit"]["sealed_endpoint_index"] == 0
    assert all(not p["unlocked"] for p in doc["width_probes"])
    assert doc["verdict"]["class"] == "(a) 板设计固有不可布"


@pytest.mark.skipif(not HAVE_ATMEGA, reason="atmega32u4-breakout 板树缺")
def test_e2e_atmega_080_archive_face_attribution():
    """0.8.0 存档忠实重放面端到端：现役 0.9.0 引擎重放 0.8.0 档案
    byte-equal（非密封板零 log 增量）、多端网 Steiner 拓扑行集复现、
    verdict_provenance 不入对账（None）、三分类=(a)（diag-failed8 存档锚）。"""
    doc, code = D.diagnose(os.path.join(ATMega, "board.json"),
                           os.path.join(ATMega, "execute.json"),
                           board_name="atmega32u4-breakout")
    assert code == 0
    rep = doc["replay"]
    assert rep["execute_face"] == "0.8.0-archive"
    assert rep["short_circuit_replay"] is False
    assert rep["verdict"] == "FAILED"
    assert rep["faithful"] is True
    assert rep["faithful_raw_byte_equal"] is True   # 0.8.0 档案逐字节复现
    assert rep["n_log_lines"] == rep["n_recorded_lines"] == 244
    assert rep["verdict_provenance_match"] is None   # 0.9.0-only 面不计数
    fn = doc["failed_net"]
    assert fn["net"] == "GND" and fn["partition"] == "PT-GND"
    assert fn["attempts"] == 238
    assert fn["exhaustion_cause"].startswith("obstacle-dense")
    w = doc["witness"]
    unlock = {r["class"]: r["unlocked"] for r in w["class_removal_unlock"]}
    assert unlock["routes"] is False and unlock["fixed"] is True
    assert w["minimal_removal_class_to_unlock"] == "fixed"
    assert doc["verdict"]["class"] == "(a) 板设计固有不可布"


@pytest.mark.skipif(not HAVE_SYN_U01, reason="syn-u01 板件/execute.json 缺")
def test_run_diag_entry_syn_u01_rc_and_determinism(tmp_path):
    """本批单板重放入口：rc 三分类透传+产物含 attribution/consistency+
    双跑字节等（产物确定性面=零 wall 时钟字段）。"""
    import run_diag as RD
    da, db = tmp_path / "a", tmp_path / "b"
    rc1 = RD.main(["syn-u01", "--determinism-dir", str(da)])
    rc2 = RD.main(["syn-u01", "--determinism-dir", str(db)])
    assert rc1 == rc2 == 0
    pa = (da / "syn-u01.json").read_bytes()
    pb = (db / "syn-u01.json").read_bytes()
    assert pa == pb   # 双跑字节等（D-J5 抽查面）
    doc = json.loads(pa.decode("utf-8"))
    assert doc["face"]["execute_face"] == "0.9.0-main"
    assert doc["attribution"]["class"] == "(a) 板设计固有不可布"
    assert doc["attribution"]["failed_net"]["exhaustion_cause"].startswith(
        "sealed-short-circuit")
    assert doc["consistency"]["expected"] == "(a) 板设计固有不可布"
    assert doc["consistency"]["consistent"] is True
    assert "wall" not in json.dumps(doc)   # 确定性面钉：零时钟字段


@pytest.mark.skipif(not HAVE_ATMEGA, reason="atmega32u4-breakout 板树缺")
def test_run_diag_entry_atmega_080_face(tmp_path):
    import run_diag as RD
    rc = RD.main(["atmega32u4-breakout", "--determinism-dir",
                  str(tmp_path)])
    assert rc == 0
    doc = json.loads((tmp_path / "atmega32u4-breakout.json")
                     .read_text(encoding="utf-8"))
    assert doc["face"]["execute_face"] == "0.8.0-archive"
    assert doc["replay"]["faithful_raw_byte_equal"] is True
    assert doc["attribution"]["class"] == "(a) 板设计固有不可布"
    assert doc["consistency"]["consistent"] is True


def test_run_diag_resolve_failure_rc5():
    import run_diag as RD
    assert RD.resolve_board("no-such-board-xyz")[0] is None
    assert RD.main(["no-such-board-xyz"]) == 5


# ------------------------------------------------ W-5 witness 探针双口径钉

def test_probe_version_registration():
    assert P.PROBE_VERSION == "r1_failed_net_probe/1.1"
    assert P.RAY_DIRECTIONS == 16
    assert P.FINE_RULE_ESCAPABLE_MM == 0.27
    assert P.FINE_RULE_ESCAPABLE_CENTERLINE_MM == 0.22


def test_seg_pad_gap_track_ray_geometry_units():
    rect = {"shape": "rect", "size_mm": [1.0, 1.0]}
    # 垂直侧距：矩形下缘距射线 0.6 / 0.25
    assert round(P.seg_pad_gap((0, 0), (1.6, 0), (0.8, 1.1), rect), 6) == 0.6
    assert round(P.seg_pad_gap((0, 0), (1.6, 0), (0.8, 0.75), rect), 6) == 0.25
    # 射线穿贯矩形=0（铜重叠零隙）
    assert P.seg_pad_gap((0, 0), (1.6, 0), (0.8, 0.0),
                         {"shape": "rect", "size_mm": [0.5, 0.5]}) == 0.0
    # 圆垫在射线延长线外（尖端外）：中心 2.0−r0.1325−射线长 1.6=0.2675
    circ = {"shape": "circle", "size_mm": [0.265]}
    assert round(P.seg_pad_gap((0, 0), (1.6, 0), (2.0, 0.0), circ), 4) == 0.2675
    # 圆垫压在射线上=负隙（铜重叠如实落值）
    assert P.seg_pad_gap((0, 0), (1.6, 0), (1.0, 0.0), circ) < 0


def test_track_ray_caliber_synthetic_seal():
    """合成钉：四向等距围堵（0.3mm 铜隙）→ 16 向全方向射线中心线口径
    亦全封（max corridor < R5）；无障碍→全开。"""
    pads = [
        {"pt": {"shape": "circle", "size_mm": [0.265]}, "pos": (0.0, 0.3)},
        {"pt": {"shape": "circle", "size_mm": [0.265]}, "pos": (0.0, -0.3)},
        {"pt": {"shape": "circle", "size_mm": [0.265]}, "pos": (0.3, 0.0)},
        {"pt": {"shape": "circle", "size_mm": [0.265]}, "pos": (-0.3, 0.0)},
    ]
    out = P.track_ray_caliber((0.0, 0.0), pads, 1.6, 0.5)
    assert out["n_directions"] == 16
    assert out["max_corridor_mm"] is not None
    assert out["max_corridor_mm"] < 0.5
    assert out["sealed_under_v5_rules"] is True
    assert all(v is not None for v in out["per_direction_gap_mm"].values())
    # 无障碍面：max=None（不宣称密封——n_neighbors=0 的开放邻域如实披露）
    empty = P.track_ray_caliber((0.0, 0.0), [], 1.6, 0.5)
    assert empty["max_corridor_mm"] is None
    assert empty["sealed_under_v5_rules"] is False


@pytest.mark.skipif(not os.path.isfile(TMP108_BOARD),
                    reason="tmp108 board.json 缺（世界未物化）")
def test_probe_tmp108_dual_caliber_anchor():
    """PREREG §4 判读锚：tmp108 ep1 两口径均密封（v5 R5 口径下无 escape
    通道——判读不受双口径化影响）；ep0 邻域空（可达端点）两口径同读。"""
    board = json.load(open(TMP108_BOARD, encoding="utf-8"))["board"]
    doc = P.probe(board, "PT-A0", radius=1.6, trace_w=0.2)
    assert doc["probe"] == "r1_failed_net_probe/1.1"
    assert len(doc["calibers"]) == 2
    assert "track-pad" in doc["calibers"][1] or "track-ray" in doc["calibers"][1]
    eps = {e["endpoint_index"]: e for e in doc["endpoints"]}
    # ep1：pad-pad 口径密封（既有锚）+ track-ray 口径亦密封（W-5 新锚）
    assert eps[1]["calibers"]["sealed_under_v5_rules"] is True
    tr = eps[1]["track_ray_caliber"]
    assert tr["sealed_under_v5_rules"] is True
    assert tr["max_corridor_mm"] < 0.5
    assert tr["escapable_under_fine_rules"] is True   # (c) 类证据方向同读
    assert tr["fine_rule_escapable_threshold_centerline_mm"] == 0.22
    # ep0：pad-pad 邻域空（可达端点）——射线口径同读开放（粗筛面更宽，
    # 远侧 pad 计入但走廊 ≥R5，不宣称密封）
    assert eps[0]["min_copper_gap_mm"] is None
    assert eps[0]["track_ray_caliber"]["sealed_under_v5_rules"] is False
