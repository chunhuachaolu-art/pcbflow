"""V4.0-B paired holdout harness 机制测试（只测机制，绝不执行真实评估）。

全部使用代码内合成的多块小板（>=2 块，经 v4exp.model.validate_board 确认
合法）+ tmp 目录，不加载 datasets、不访问网络、不调真实模型。覆盖：
- E0 在多块合成板上 complete，run record 含 hash 链（canonical：无
  wall-clock、无绝对路径，重放 steps 可复算同一链头；双跑逐字节一致）；
- paired 结构：每板独立记录与独立 hash（E1 每板独立 accepted/blocked
  判定与 actions_source_sha256）；
- run_phase("E3") 不带批准 => blocked，不产出任何候选产物；带
  allow_real_board=True 也只落 requires_approval_record 且不伪造批准。
"""

import json
import os
import re

from pcbflow import hashing, v4_experiment
from pcbflow.v4exp import model

ISO_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T")

E0_CHECK_NAMES = v4_experiment.E0_CHECK_NAMES


# ---------------------------------------------------------------- 合成小板

def make_board(sid, pad_shift=0.0, with_bus=False):
    """一块最小合法板：n1/n2 default，n3 clock（clock 必须在 relation 里）。"""
    y1 = 3.0 + pad_shift
    relations = [{"relation_id": "r1", "relation_type": "clock_group",
                  "members": ["n3"], "parent_id": None}]
    if with_bus:
        relations.append({"relation_id": "BUS-SPI",
                          "relation_type": "bus",
                          "members": ["n1", "n2"], "parent_id": None})
    return {
        "schema": model.SCHEMA_BOARD,
        "scenario_id": sid, "split": "development",
        "family": "f1", "seed": 7,
        "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0],
                  "layers": ["F.Cu", "B.Cu"]},
        "rules": {"grid_mm": 0.25, "clearance_mm": 0.3,
                  "width_mm": {"default": 0.3, "clock": 0.4},
                  "via": {"pad_mm": 0.6, "hole_mm": 0.3},
                  "allowed_layers": {"default": ["F.Cu", "B.Cu"],
                                     "clock": ["F.Cu"]}},
        "pads": [
            {"pad_id": "U1-1", "net_id": "n1", "x_mm": 2.0, "y_mm": y1,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U1-2", "net_id": "n1", "x_mm": 38.0, "y_mm": y1,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U2-1", "net_id": "n2", "x_mm": 2.0, "y_mm": 27.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U2-2", "net_id": "n2", "x_mm": 38.0, "y_mm": 27.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U3-1", "net_id": "n3", "x_mm": 6.0, "y_mm": 15.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
            {"pad_id": "U3-2", "net_id": "n3", "x_mm": 34.0, "y_mm": 15.0,
             "w_mm": 1.2, "h_mm": 1.2, "layer": "F.Cu"},
        ],
        "nets": [
            {"net_id": "n1", "net_class": "default",
             "endpoints": ["U1-1", "U1-2"]},
            {"net_id": "n2", "net_class": "default",
             "endpoints": ["U2-1", "U2-2"]},
            {"net_id": "n3", "net_class": "clock",
             "endpoints": ["U3-1", "U3-2"]},
        ],
        "keepouts": [
            {"keepout_id": "k1", "rect_mm": [16.0, 12.0 + pad_shift,
                                             24.0, 18.0 + pad_shift],
             "layers": ["F.Cu", "B.Cu"]},
        ],
        "relations": relations,
        "label": "satisfiable"}


SIDS = ("syn-a", "syn-b")


def write_board_files(tmp_path):
    """两块几何不同的小板落盘；返回 (board 文件路径列表, board 对象字典)。"""
    boards = {
        "syn-a": make_board("syn-a", pad_shift=0.0, with_bus=True),
        "syn-b": make_board("syn-b", pad_shift=2.0, with_bus=False),
    }
    paths = []
    for sid in SIDS:
        p = tmp_path / ("board-%s.json" % sid)
        model.write_json(str(p), boards[sid])
        paths.append(str(p))
    return paths, boards


def replay_chain_head(steps):
    """从 steps 逐步重算 step_record_sha256 并走链，返回链头（可复算性）。"""
    head = None
    for i, st in enumerate(steps):
        assert st["step"] == i + 1
        assert st["prev_step_sha256"] == head
        body = {"step": st["step"], "board": st["board"],
                "name": st["name"], "payload_sha256": st["payload_sha256"],
                "prev_step_sha256": st["prev_step_sha256"]}
        if "detail" in st:
            body["detail"] = st["detail"]
        digest = hashing.sha256_text(hashing.json_dumps(body))
        assert digest == st["step_record_sha256"], st
        head = digest
    return head


# ---------------------------------------------------------------- E0 多板

def test_synth_boards_are_valid_per_model_schema(tmp_path):
    _, boards = write_board_files(tmp_path)
    for sid, obj in boards.items():
        assert model.validate_board(obj) == [], sid


def test_e0_two_synth_boards_complete_with_independent_records(tmp_path):
    paths, _ = write_board_files(tmp_path)
    out = tmp_path / "e0"
    rec = v4_experiment.run_phase("E0", paths, str(out))

    assert rec["schema"] == v4_experiment.RUN_RECORD_SCHEMA
    assert rec["phase"] == "E0"
    assert rec["verdict"] == "complete"
    assert rec["gate"]["verdict"] == "allowed"
    assert rec["board_count"] == 2
    assert [b["scenario_id"] for b in rec["boards"]] == list(SIDS)
    for entry in rec["boards"]:
        assert entry["pass"] is True
        assert set(entry["checks"]) == set(E0_CHECK_NAMES)
        assert all(entry["checks"][c]["pass"] for c in E0_CHECK_NAMES)
        assert "/" not in entry["board_file"]  # 只存基名，无绝对路径

    # 每板独立载体：manifest 里绑定各自的 board snapshot hash（互不相同）
    manifests = {}
    for sid in SIDS:
        m = model.read_json(str(out / ("route-manifest-%s.json" % sid)))
        manifests[sid] = m
        assert m["scenario_id"] == sid
    assert (manifests["syn-a"]["board_snapshot_sha256"]
            != manifests["syn-b"]["board_snapshot_sha256"])

    # hash 链：每板独立 step 组（carrier.manifest/carrier.svg/consistency）
    per_board = {sid: [s for s in rec["steps"] if s["board"] == sid]
                 for sid in SIDS}
    for sid in SIDS:
        assert [s["name"] for s in per_board[sid]] == \
            ["e0.carrier.manifest", "e0.carrier.svg", "e0.consistency"]
        # 每板 e0.consistency payload 绑定该板自己的 5 项检查结果
        cons = per_board[sid][-1]
        assert cons["payload_sha256"] == hashing.sha256_text(
            hashing.json_dumps({c: rec["boards"][list(SIDS).index(sid)]
                                ["checks"][c] for c in E0_CHECK_NAMES}))
    assert rec["chain_head_sha256"] == replay_chain_head(rec["steps"])
    assert rec["chain_head_sha256"] is not None
    assert rec["record_file"] == "v4-phase-e0-run-record.json"
    assert (out / rec["record_file"]).exists()


def test_e0_double_run_canonical_byte_identical_and_replayable(tmp_path):
    paths, _ = write_board_files(tmp_path)
    out1 = tmp_path / "e0-run1"
    out2 = tmp_path / "e0-run2"
    rec1 = v4_experiment.run_phase("E0", paths, str(out1))
    rec2 = v4_experiment.run_phase("E0", paths, str(out2))

    # 无 wall-clock、无主机绝对路径 => 两次 run record 完全一致
    assert rec1 == rec2
    text1 = (out1 / rec1["record_file"]).read_text(encoding="utf-8")
    text2 = (out2 / rec2["record_file"]).read_text(encoding="utf-8")
    assert text1 == text2
    assert ISO_TS_RE.search(text1) is None, "run record 不得含 ISO 时间戳"
    assert str(tmp_path) not in text1, "run record 不得含主机绝对路径"
    assert rec1["chain_head_sha256"] == replay_chain_head(rec1["steps"])

    # 载体产物也逐字节可复现
    for sid in SIDS:
        a = (out1 / ("route-manifest-%s.json" % sid)).read_bytes()
        b = (out2 / ("route-manifest-%s.json" % sid)).read_bytes()
        assert a == b


# ------------------------------------------------------- E3 默认失败关闭

def test_e3_blocked_without_approval_and_no_candidates(tmp_path):
    paths, _ = write_board_files(tmp_path)
    out = tmp_path / "e3"
    rec = v4_experiment.run_phase("E3", paths, str(out))

    assert rec["verdict"] == "blocked"
    assert rec["gate"]["verdict"] == "blocked"
    assert rec["boards"] == []
    assert rec["board_count"] == 0
    assert rec["steps"] == []
    assert rec["chain_head_sha256"] is None
    # 不产出候选：目录里只有 run record 本身，无 manifest/svg/候选产物
    assert sorted(os.listdir(str(out))) == [rec["record_file"]]
    assert rec["record_file"] == "v4-phase-e3-run-record.json"
    body = (out / rec["record_file"]).read_text(encoding="utf-8")
    assert "candidate" not in body
    assert str(tmp_path) not in body


def test_e3_allow_real_board_only_requires_approval_no_fabrication(tmp_path):
    paths, _ = write_board_files(tmp_path)
    out = tmp_path / "e3-allowed"
    rec = v4_experiment.run_phase("E3", paths, str(out),
                                  allow_real_board=True)

    assert rec["verdict"] == "requires_approval_record"
    assert rec["gate"]["verdict"] == "requires_approval_record"
    assert rec["boards"] == []
    assert rec["steps"] == []
    assert rec["chain_head_sha256"] is None
    # 不伪造批准记录：整份 run record 中不出现任何批准字段
    body = (out / rec["record_file"]).read_text(encoding="utf-8")
    parsed = json.loads(body)
    for key in ("approver", "approval_record_sha256", "approval_record"):
        assert key not in parsed
    assert sorted(os.listdir(str(out))) == [rec["record_file"]]


# ------------------------------------------------- E1 paired 独立记录

def _planner_response(board_obj, manifest, order, reason):
    return {
        "schema_version": "v4-planner-action-1",
        "board_snapshot_sha256": model.sha256_of(board_obj),
        "route_manifest_sha256": model.sha256_of(manifest),
        "actions": [
            {"action_id": "A-1", "type": "set_route_order",
             "order": order, "reason": reason, "confidence": 0.8},
            {"action_id": "A-2", "type": "prefer_layer",
             "target_net_ids": ["n3"], "preferred_layers": ["F.Cu"]},
        ],
        "uncertainties": [],
    }


def _e0_then_e1(tmp_path, responses_override=None):
    """公共前置：E0 生成两板载体 -> 构造每板响应 -> 跑 E1。"""
    paths, boards = write_board_files(tmp_path)
    out0 = tmp_path / "carrier"
    rec0 = v4_experiment.run_phase("E0", paths, str(out0))
    assert rec0["verdict"] == "complete"

    responses = {}
    per_board_order = {"syn-a": (["n1", "n2", "n3"], "bus-first"),
                       "syn-b": (["n3", "n1", "n2"], "clock-first")}
    for sid in SIDS:
        board_obj = model.read_json(str(tmp_path / ("board-%s.json" % sid)))
        manifest = model.read_json(
            str(out0 / ("route-manifest-%s.json" % sid)))
        order, reason = per_board_order[sid]
        responses[sid] = _planner_response(board_obj, manifest, order, reason)
    if responses_override is not None:
        responses.update(responses_override)

    out1 = tmp_path / "plan"
    rec1 = v4_experiment.run_phase("E1", paths, str(out1),
                                   responses=responses,
                                   manifest_dir=str(out0))
    return rec1, responses


def test_e1_paired_boards_independent_records_and_hashes(tmp_path):
    rec1, _ = _e0_then_e1(tmp_path)

    assert rec1["verdict"] == "complete"
    assert rec1["board_count"] == 2
    entries = {b["scenario_id"]: b for b in rec1["boards"]}
    assert set(entries) == set(SIDS)

    # 每板独立 accepted 记录：独立 solver_run、独立动作来源 hash
    hashes = {}
    for sid in SIDS:
        entry = entries[sid]
        assert entry["verdict"] == "accepted"
        assert entry["reasons"] == []
        run = entry["solver_run"]
        assert run["board_write"] is False
        assert run["input_trust"] == "untrusted_planner_output_validated"
        hashes[sid] = run["actions_source_sha256"]
        assert entry["solver_input"]["route_order"] == \
            {"syn-a": ["n1", "n2", "n3"],
             "syn-b": ["n3", "n1", "n2"]}[sid]
        assert "corridor_preferences" not in entry["solver_input"]
    assert hashes["syn-a"] != hashes["syn-b"], "每板动作来源 hash 须独立"

    # hash 链按板独立分段，且 e1.bridge 步绑定该板的 actions_source_sha256
    for sid in SIDS:
        steps = [s for s in rec1["steps"] if s["board"] == sid]
        assert [s["name"] for s in steps] == \
            ["e1.parse", "e1.validate", "e1.bridge"]
        assert steps[2]["payload_sha256"] == hashes[sid]
    assert rec1["chain_head_sha256"] == replay_chain_head(rec1["steps"])


def test_e1_paired_one_stale_board_blocked_other_still_accepted(tmp_path):
    stale = {"syn-a": _planner_response(
        make_board("syn-a", pad_shift=0.0, with_bus=True),
        {"routes": []}, ["n1"], "stale")}  # manifest hash 必然不匹配
    rec1, _ = _e0_then_e1(tmp_path, responses_override=stale)

    entries = {b["scenario_id"]: b for b in rec1["boards"]}
    assert entries["syn-a"]["verdict"] == "blocked"
    assert any("route_manifest_sha256" in r
               for r in entries["syn-a"]["reasons"])
    assert "solver_run" not in entries["syn-a"]
    assert entries["syn-b"]["verdict"] == "accepted"
    assert "solver_run" in entries["syn-b"]
    # 一板失败 => 整轮 failed（UNKNOWN/失败可见，不静默记 complete）
    assert rec1["verdict"] == "failed"
