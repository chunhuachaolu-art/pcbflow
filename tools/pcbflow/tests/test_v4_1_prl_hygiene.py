"""pcbflow.v4_1 .kicad_prl sidecar 卫生与 canonical JSON 测试。"""

from __future__ import annotations

import json

from pcbflow.v4_1.canonical import dumps_canonical, write_canonical_json
from pcbflow.v4_1.prl_hygiene import (check_and_restore, diff_inventories,
                                      inventory)


def test_inventory_and_diff(tmp_path):
    (tmp_path / "board.kicad_pcb").write_bytes(b"board")
    inv = inventory(str(tmp_path))
    assert set(inv) == {"board.kicad_pcb"}
    (tmp_path / "sidecar.kicad_prl").write_bytes(b"prl")
    after = inventory(str(tmp_path))
    d = diff_inventories(inv, after)
    assert d["created"] == ["sidecar.kicad_prl"]
    assert d["changed"] == [] and d["removed"] == []
    (tmp_path / "board.kicad_pcb").write_bytes(b"board2")
    d2 = diff_inventories(inv, inventory(str(tmp_path)))
    assert d2["changed"] == ["board.kicad_pcb"]


def test_sidecar_created_detected_and_restored(tmp_path):
    (tmp_path / "board.kicad_pcb").write_bytes(b"board")
    before = inventory(str(tmp_path))
    (tmp_path / "board.kicad_prl").write_bytes(b"sidecar")  # 模拟 kicad-cli 副产物
    rec = check_and_restore(str(tmp_path), before)
    assert rec["prl_created"] == ["board.kicad_prl"]
    assert rec["verdict"] == "restored"
    assert rec["post_restore_matches_before"] is True
    assert not (tmp_path / "board.kicad_prl").exists()


def test_sidecar_changed_bytes_restored(tmp_path):
    (tmp_path / "board.kicad_prl").write_bytes(b"orig")
    (tmp_path / "other.txt").write_bytes(b"keep")
    before = inventory(str(tmp_path))
    (tmp_path / "board.kicad_prl").write_bytes(b"MUTATED")
    rec = check_and_restore(str(tmp_path), before, snapshot_bytes=b"orig")
    assert rec["prl_changed"] == ["board.kicad_prl"]
    assert rec["verdict"] == "restored"
    assert (tmp_path / "board.kicad_prl").read_bytes() == b"orig"


def test_sidecar_changed_without_snapshot_blocked(tmp_path):
    (tmp_path / "board.kicad_prl").write_bytes(b"orig")
    before = inventory(str(tmp_path))
    (tmp_path / "board.kicad_prl").write_bytes(b"MUTATED")
    rec = check_and_restore(str(tmp_path), before, snapshot_bytes=None)
    assert rec["verdict"] == "blocked"
    assert rec["unrestored"] and rec["unrestored"][0]["status"] == "blocked"


def test_clean_call_verdict(tmp_path):
    (tmp_path / "board.kicad_pcb").write_bytes(b"board")
    before = inventory(str(tmp_path))
    rec = check_and_restore(str(tmp_path), before)
    assert rec["verdict"] == "clean"
    assert rec["diff"] == {"created": [], "changed": [], "removed": []}


def test_inventory_missing_dir_fail_closed(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        inventory(str(tmp_path / "nope"))


# ---------------------------------------------------------------- canonical

def test_canonical_dumps_format():
    obj = {"z": 1, "a": {"b": [1, 2], "c": "中文"}, "n": None}
    s = dumps_canonical(obj)
    assert s.endswith("\n")
    assert "\r" not in s
    lines = s.splitlines()
    assert lines[0] == "{"
    assert lines[1].startswith(' "a"')  # sort_keys + indent=1
    assert "中文" in s  # ensure_ascii=False
    assert json.loads(s) == obj


def test_canonical_write_bytes(tmp_path):
    p = tmp_path / "x.json"
    write_canonical_json(str(p), {"k": "值"})
    raw = p.read_bytes()
    assert b"\r" not in raw
    assert raw.decode("utf-8") == '{\n "k": "值"\n}\n'
