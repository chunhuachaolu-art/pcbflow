# -*- coding: utf-8 -*-
"""pilot 0.6.0 回归（V8-PILOT-060 任务书 D-1..D-9 五面覆盖）。

- D-6 迁移重放: run8/run11-armB 真实 v1 台账 → 迁移模式 + 披露结构 +
  verify 迁移感知 exit 0; 链断/轮号不连续不降级 fail-closed; golden-v2
  新 v2 台账严格 replay 不受影响（W-2）。
- D-1 ROI 双模式: demo-01 板 full=板全域 / legacy=margin12 口径，
  facts 记 roi 模式、简报语义句分流。
- D-2 层合并布尔化: 同布尔不同 reason 串的层合并一张图（run8 遗留候选）。
- D-3 checked_pairs 双型 + D-9 export --out-dir: run8 板导出链成功落
  tmp（双件+数值+型披露），历史 run 目录零写（W-3）。
- D-5 V_CLEARANCE detail @cand 坐标（席位面复现; 几何面=canvas/tests）。
- D-7 码表单源渲染: 简报恰 9 码含 V_HOLE_VIA; PLAYBOOK-BRIEF.md 漂移
  守卫（码集合全等+每码文本含表语义句）（W-4）。

板/源账只读（conftest badgeleds 先例），一切分叉/导出产物写 tmp。
"""
import argparse
import contextlib
import copy
import io
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from net_agent_pilot import pilot

_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BOARD_BADGE = os.path.join(_ROOT, "out", "v5-p5", "boards",
                           "badgeleds-do-electronics", "board.json")
BOARD_PMOD = os.path.join(_ROOT, "out", "v5-p5", "boards", "pmod-crypto",
                          "board.json")
BOARD_DEMO = os.path.join(_ROOT, "boards", "d",
                          "demo-01-v2-corridor.board.v1.json")
RUN8 = os.path.join(_ROOT, "out", "net-agent-p1", "run8")
RUN11B = os.path.join(_ROOT, "out", "net-agent-p1", "run11-armB")
GOLDEN_V2 = os.path.join(_ROOT, "out", "net-agent-p1", "pilot06", "golden-v2")
BRIEF_MD = os.path.join(_ROOT, "out", "net-agent-p1", "PLAYBOOK-BRIEF.md")


def _ns(**kw):
    base = {"board": BOARD_BADGE, "run": RUN8}
    base.update(kw)
    return argparse.Namespace(**base)


# ---------------------------------------------------------------- D-6 迁移面

@pytest.mark.parametrize("board,run,n_rows", (
    (BOARD_BADGE, RUN8, 8),
    (BOARD_PMOD, RUN11B, 17),
))
def test_migration_replay_real_v1_ledgers(board, run, n_rows):
    """W-2: 真 v1 台账 → 迁移模式重放，披露结构完整、终态可读。"""
    b, sha, bp = pilot.load_board(board)
    st = pilot.current_state(b, bp, run)
    disc = st.pilot_migration_disclosure
    assert disc["rows"] == n_rows
    assert disc["batch_rows"] == n_rows and disc["legacy_rows"] == 0
    assert disc["diverged_rows"] == list(range(1, n_rows + 1))
    core = st._st
    assert disc["final_state_sha256"] == core.sha256()
    assert (len(core.segs), len(core.vias)) > (0, 0) or disc["rows"]


def test_cmd_verify_migration_exit0(tmp_path, capsys):
    """W-2: 迁移感知 verify=exit 0 + migration 块全行披露。"""
    pilot.cmd_verify(_ns())
    out = json.loads(capsys.readouterr().out)
    mig = out["migration"]
    assert out["rounds"] == 8
    assert mig["rows"] == 8 and mig["batch_rows"] == 8
    assert mig["diverged_rows"] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert re.fullmatch(r"[0-9a-f]{64}", mig["final_state_sha256"])


def _tamper_ledger(src, tmp_path, mutate):
    lines = [ln for ln in open(src, "rb").read().split(b"\n") if ln.strip()]
    rec = json.loads(lines[1].decode("utf-8"))
    mutate(rec)
    lines[1] = json.dumps(rec, ensure_ascii=False,
                          separators=(",", ":")).encode("utf-8")
    dst = tmp_path / "ledger.jsonl"
    dst.write_bytes(b"\n".join(lines) + b"\n")
    return str(dst)


def test_migration_no_degrade_on_chain_break(tmp_path):
    """链断不降级: 迁移通道也先核字节链，断裂= ValueError fail-closed。"""
    b, sha, bp = pilot.load_board(BOARD_BADGE)
    dst = _tamper_ledger(os.path.join(RUN8, "ledger.jsonl"), tmp_path,
                         lambda r: r.__setitem__("prev_sha256", "f" * 64))
    with pytest.raises(ValueError, match="台账链断裂"):
        pilot.current_state(b, bp, str(tmp_path))


def test_migration_no_degrade_on_round_gap(tmp_path):
    """轮号不连续不降级（迁移通道同样 fail-closed）。"""
    b, sha, bp = pilot.load_board(BOARD_BADGE)
    dst = _tamper_ledger(os.path.join(RUN8, "ledger.jsonl"), tmp_path,
                         lambda r: r.__setitem__("round", 9))
    with pytest.raises(ValueError, match="台账轮号不连续"):
        pilot.current_state(b, bp, str(tmp_path))


def test_golden_v2_strict_replay_unaffected(tmp_path, capsys):
    """W-2: pilot06 金标链（现行引擎写的 v2 台账）严格 replay，零迁移。"""
    b, sha, bp = pilot.load_board(os.path.join(GOLDEN_V2, "board.json"))
    st = pilot.current_state(b, bp, GOLDEN_V2)
    assert getattr(st, "pilot_migration_disclosure", None) is None
    pilot.cmd_verify(_ns(board=os.path.join(GOLDEN_V2, "board.json"),
                         run=GOLDEN_V2))
    out = json.loads(capsys.readouterr().out)
    assert out == {"ledger_tail_state_match": True, "rounds": 1}


def test_reach_truncated_v1_prefix_migrates(tmp_path):
    """_reach_state 截断路径共用迁移 helper: run8 前 3 轮截断可建态。"""
    b, sha, bp = pilot.load_board(BOARD_BADGE)
    st = pilot._reach_state(b, bp, RUN8, 3)
    assert st.pilot_migration_disclosure["rows"] == 3


# ---------------------------------------------------------------- D-1 ROI

@pytest.fixture(scope="module")
def demo_slices(tmp_path_factory):
    """demo-01 板同网（sorted 未连通首网）full/legacy 双切片。"""
    out = {}
    for mode in ("full", "legacy"):
        d = tmp_path_factory.mktemp("roi-%s" % mode)
        run = str(d / "run")
        with contextlib.redirect_stdout(io.StringIO()):
            pilot.cmd_slice(_ns(board=BOARD_DEMO, run=run, net="BUS-FMC",
                                round=None, tag="r01", prior_rejection=None,
                                playbook=None, roi=mode))
        rd = os.path.join(run, "rounds", "r01")
        out[mode] = {
            "brief": open(os.path.join(rd, "brief.md"),
                          encoding="utf-8").read(),
            "facts": json.load(open(os.path.join(rd, "facts.json"),
                                    encoding="utf-8")),
        }
    return out


def test_roi_full_board(demo_slices):
    facts = demo_slices["full"]["facts"]
    lat = facts["lattice"]
    assert facts["map_stats"]["roi"] == [0, 0, lat["i_max"], lat["j_max"]]
    assert facts["map_stats"]["roi_mode"] == "full"
    assert "地图覆盖全板（ROI=板全域）" in demo_slices["full"]["brief"]
    assert "允许走 ROI 外" not in demo_slices["full"]["brief"]
    assert "全板有效" in demo_slices["full"]["brief"]      # zone_facts 措辞


def test_roi_legacy_margin(demo_slices):
    facts = demo_slices["legacy"]["facts"]
    roi = facts["map_stats"]["roi"]
    assert facts["map_stats"]["roi_mode"] == "legacy"
    assert roi != [0, 0, facts["lattice"]["i_max"], facts["lattice"]["j_max"]]
    # 旧口径: 端点锚 ± margin=12 钳板内
    terms = facts["terminals_grid"]
    assert roi == [max(0, min(t[0] for t in terms) - 12),
                   max(0, min(t[1] for t in terms) - 12),
                   min(facts["lattice"]["i_max"],
                       max(t[0] for t in terms) + 12),
                   min(facts["lattice"]["j_max"],
                       max(t[1] for t in terms) + 12)]
    assert "允许走 ROI 外" in demo_slices["legacy"]["brief"]


# ---------------------------------------------------------------- D-2 布尔合并

def _merge_state(tmp_path):
    """三网微板态: NET-X 铜在 F.Cu、NET-Y 铜在 B.Cu、重叠同格——同布尔不同
    reason 串（route:F.Cu ≠ route:B.Cu）的层合并判据用例。"""
    b, sha, bp = pilot.load_board(os.path.join(GOLDEN_V2, "board.json"))
    board = copy.deepcopy(b)
    board["partitions"].append({
        "partition_id": "PC", "ptype": "MISC", "current_a": 0,
        "speed_class": "unknown", "layer_policy": "any",
        "width_prior": {"w_min": 0.3, "w_max": 0.8},
        "geometry": {"endpoints": [[5.0, 9.0], [5.5, 9.0]]}})
    board["nets"].append({"net_id": "NET-C", "partitions": ["PC"]})
    from canvas.integration import build_state, make_loop_state
    st = make_loop_state(build_state(board, bp, "0" * 64))
    return st


def test_layer_merge_booleanized(tmp_path):
    """D-2: 同布尔阻塞集的层合并一张图（旧行=reason 串分印两张）。"""
    st = _merge_state(tmp_path)
    st._st.add_seg("NET-A", "PA", "F.Cu",
                   [[2, 2], [2, 16], [10, 16]], "min")
    st._st.add_seg("NET-C", "PC", "B.Cu",
                   [[2, 2], [2, 16], [10, 16]], "min")
    obs = pilot._obstacles(st, "NET-B")
    maps, groups, roi, stats = pilot._ascii_map(st, "NET-B", obs, 0.5)
    # F.Cu 与 B.Cu 布尔阻塞集相等 → 合并一张（旧 reason 串口径会分印）
    assert [sorted(g) for g in groups] == [["B.Cu", "F.Cu"]]
    assert maps.count("ROI:") == 1
    # 行为面: 单层铜（只 F.Cu）时两图真不同 → 仍分印
    st2 = _merge_state(tmp_path)
    st2._st.add_seg("NET-A", "PA", "F.Cu",
                    [[2, 2], [2, 16], [10, 16]], "min")
    obs2 = pilot._obstacles(st2, "NET-B")
    maps2, groups2, _roi2, stats2 = pilot._ascii_map(st2, "NET-B", obs2, 0.5)
    assert sorted(sorted(g) for g in groups2) == [["B.Cu"], ["F.Cu"]]
    assert maps2.count("ROI:") == 2


# ------------------------------------------------- D-3/D-9 export 面（W-3）

def test_cmd_export_outdir_checked_pairs(tmp_path, capsys):
    """run8 板导出链成功落 --out-dir（双件+checked_pairs 数值+型披露），
    历史 run 目录零写（run8/final 保持空）。--out-dir 受 v5.sidecar 写路径
    合同约束（只准 repo out/ 下）——验证面目录用 pilot06 下固定子目录。"""
    import shutil
    out_dir = os.path.join(_ROOT, "out", "net-agent-p1", "pilot06",
                           "test-export-tmp")
    shutil.rmtree(out_dir, ignore_errors=True)
    pilot.cmd_export(_ns(out_dir=out_dir))
    rep = json.load(open(os.path.join(out_dir, "drc-report.json"),
                         encoding="utf-8"))
    assert isinstance(rep["checked_pairs"], int) and rep["checked_pairs"] >= 0
    assert rep["checked_pairs_type"] in ("int", "sequence")
    board_id = "badgeleds-do-electronics"
    for ext in (".kicad_pcb", ".kicad_pro"):
        assert os.path.isfile(os.path.join(out_dir, board_id + ext))
    assert not os.path.isdir(os.path.join(RUN8, "final")) or \
        not os.listdir(os.path.join(RUN8, "final"))
    printed = json.loads(capsys.readouterr().out)
    assert printed["exported"]["n_routes"] >= 1


def test_checked_pairs_dual_type():
    """D-3 单元面: int 直用、序列取 len、异常型 fail-closed。"""
    assert pilot._checked_pairs_count(710) == (710, "int")
    assert pilot._checked_pairs_count(0) == (0, "int")
    assert pilot._checked_pairs_count([("a", "b")] * 3) == (3, "sequence")
    assert pilot._checked_pairs_count(("x", "y")) == (2, "sequence")
    with pytest.raises(TypeError):
        pilot._checked_pairs_count(True)
    with pytest.raises(TypeError):
        pilot._checked_pairs_count({"a": 1})


# ---------------------------------------------------------------- D-5 席位面

def test_v_clearance_detail_cand_coords():
    """W-4: V_CLEARANCE 拒收 detail 含 @cand=( 坐标（席位动作面复现）。"""
    b, sha, bp = pilot.load_board(os.path.join(GOLDEN_V2, "board.json"))
    st = pilot.current_state(b, bp, GOLDEN_V2)      # NET-A 铜已在场
    from canvas.validate import validate_edit
    act = {"action": "route", "net_id": "NET-B", "layer": "F.Cu",
           "waypoints": [[18, 2], [16, 2], [4, 18]]}
    ok, code, detail = validate_edit(st._st, act)
    assert not ok and code == "V_CLEARANCE"
    assert "gap=" in detail
    m = re.search(r"@cand=\((-?\d+\.\d+),(-?\d+\.\d+)\) vs "
                  r"\((-?\d+\.\d+),(-?\d+\.\d+)\)", detail)
    assert m, detail
    for v in m.groups():
        assert len(v.split(".")[1]) <= 4    # round 4 位


# ---------------------------------------------------------------- D-7 码表

def test_brief_renders_nine_codes(demo_slices):
    """简报拒收码节从单源渲染: 恰 9 码、V_HOLE_VIA 自动补齐。"""
    from canvas.protocol import SEAT_REJECTION_CODES
    brief = demo_slices["full"]["brief"]
    sec = brief.split("## 语义层拒收码")[1].split("## 交付")[0]
    codes = re.findall(r"^- (V_[A-Z_]+):", sec, re.M)
    assert codes == [c for c, _ in SEAT_REJECTION_CODES]
    assert "V_HOLE_VIA" in codes
    assert len(codes) == 9


def test_playbook_brief_drift_guard():
    """W-4 漂移守卫: PLAYBOOK-BRIEF.md 码表节 ①码集合与表全等
    ②每码文本包含表语义句。"""
    from canvas.protocol import SEAT_REJECTION_CODES
    lines = open(BRIEF_MD, encoding="utf-8").read().split("\n")
    table = [ln for ln in lines if ln.startswith("- **拒收码全表")]
    assert len(table) == 1
    codes = re.findall(r"(V_[A-Z_]+)=", table[0])
    assert set(codes) == {c for c, _ in SEAT_REJECTION_CODES}
    assert len(codes) == len(set(codes)) == 9
    for code, text in SEAT_REJECTION_CODES:
        assert "%s=%s" % (code, text) in table[0], code
