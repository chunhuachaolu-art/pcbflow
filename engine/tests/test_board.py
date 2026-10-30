# -*- coding: utf-8 -*-
"""board.v1 载入与 provenance 哈希链。"""
import copy
import json

import pytest

from fixtures_v2 import build_v2_board
from v5.board import BoardLoadError, board_for_hash, compute_board_sha256, load_board


def test_valid_board_loads(v2_board):
    assert load_board(v2_board)["board_id"] == "v2-scenario-golden"


def test_hash_chain_recomputes(v2_board):
    assert v2_board["provenance"]["board_sha256"] == compute_board_sha256(v2_board)


def test_tampered_content_breaks_chain(v2_board):
    board = copy.deepcopy(v2_board)
    board["workspace"]["x_max"] = 51.0
    board["provenance"]["board_sha256"] = compute_board_sha256(
        {**board, "workspace": {**board["workspace"], "x_max": 50.0}})
    with pytest.raises(BoardLoadError) as ei:
        load_board(board)
    assert "provenance.board_sha256" in str(ei.value)


def test_same_source_double_run_same_hash():
    a, b = build_v2_board(), build_v2_board()
    assert a["provenance"]["board_sha256"] == b["provenance"]["board_sha256"]


def test_hash_excludes_board_sha_field(v2_board):
    view = board_for_hash(v2_board)
    assert "board_sha256" not in view["provenance"]
    assert compute_board_sha256(view) == v2_board["provenance"]["board_sha256"]


def test_adapter_change_changes_hash(v2_board):
    board = copy.deepcopy(v2_board)
    board["provenance"]["adapter"] = "v2derive v9.9"
    assert compute_board_sha256(board) != v2_board["provenance"]["board_sha256"]


def test_missing_partition_ref_fail_closed(v2_board):
    board = copy.deepcopy(v2_board)
    board["nets"][0]["partitions"] = ["P99"]
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    with pytest.raises(BoardLoadError) as ei:
        load_board(board)
    assert "nets[0].partitions[0]" in str(ei.value)


def test_duplicate_partition_id_fail_closed(v2_board):
    board = copy.deepcopy(v2_board)
    board["partitions"][1]["partition_id"] = "P2"
    dup = copy.deepcopy(board["partitions"][2])
    dup["partition_id"] = "P2"
    board["partitions"][2] = dup
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    with pytest.raises(BoardLoadError) as ei:
        load_board(board)
    assert "partition_id 重复" in str(ei.value)


def test_inverted_width_interval_fail_closed(v2_board):
    board = copy.deepcopy(v2_board)
    board["partitions"][0]["width_prior"] = {"w_min": 1.4, "w_max": 0.6}
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    with pytest.raises(BoardLoadError) as ei:
        load_board(board)
    assert "width_prior" in str(ei.value)


def test_degenerate_workspace_fail_closed(v2_board):
    board = copy.deepcopy(v2_board)
    board["workspace"] = {"x_min": 0.0, "y_min": 0.0, "x_max": 0.0, "y_max": 40.0}
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    with pytest.raises(BoardLoadError) as ei:
        load_board(board)
    assert "workspace" in str(ei.value)


def test_board_json_file_roundtrip(v2_board, tmp_path):
    p = tmp_path / "board.json"
    p.write_text(json.dumps(v2_board, ensure_ascii=False), encoding="utf-8")
    from v5.board import load_board_file
    loaded = load_board_file(str(p))
    assert loaded["provenance"]["board_sha256"] == v2_board["provenance"]["board_sha256"]


def test_net_class_preserved(v2_board):
    by_id = {n["net_id"]: n for n in v2_board["nets"]}
    assert by_id["P8"]["net_class"] == "PWR"
    assert by_id["P3"]["net_class"] == "HS"


def test_r1_params_match_v2(v2_board):
    assert v2_board["hard_rules"]["R1"] == {"k_a": 0.4, "floor_mm": 0.3}
    assert v2_board["hard_rules"]["R5"]["min_clearance_mm"] == 0.5


def test_registry_empty_is_valid(v2_board):
    assert v2_board["principle_registry"] == []
