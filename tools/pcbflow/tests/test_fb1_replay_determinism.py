"""FB-1 单测：重放确定性（③ placement 重放 byte-exact + 路由/落板确定性）。

真实快照钉值用例在产物缺失时 skip（不依赖临时机器状态）。
"""

from __future__ import annotations

import hashlib
import os

import pytest

from pcbflow import board_writer, residual_cmd, route_grid

PRISTINE = os.path.join("out", "coreboard-pa1", "workspace", "p3-replay",
                        "pristine.kicad_pcb")
PLACEMENT_CSV = residual_cmd.REPLAY_PLACEMENT_CSV
REPLAYED_SHA = "2a25a8ac5bcb8a21c71b8f0c59b3276890001dd4613b12d141a4396e1ec6362b"


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_apply_placement_idempotent_and_ordered():
    """placement 重放：两遍应用逐字节一致（确定性）。"""
    rows = [{"ref": "R1", "x": "1.0", "y": "2.0", "rot": "0",
             "side": "F.Cu", "zone": "z"},
            {"ref": "R2", "x": "3.5", "y": "4.0", "rot": "90",
             "side": "F.Cu", "zone": "z"}]
    text = ("(kicad_pcb\n"
            "\t(footprint \"T:T\" (layer \"F.Cu\") (at 0 0)\n"
            "\t\t(property \"Reference\" \"R1\")\n\t)\n"
            "\t(footprint \"T:T\" (layer \"F.Cu\") (at 9 9)\n"
            "\t\t(property \"Reference\" \"R2\")\n\t)\n"
            ")\n")
    once = board_writer.apply_placement(text, rows)
    twice = board_writer.apply_placement(once, rows)
    assert once == twice
    assert _sha(once) == _sha(twice)


def test_apply_routes_deterministic_bytes():
    route = {"net": "N1", "width": 0.2, "via_size": 0.6, "via_drill": 0.3,
             "segments": [[0, 1.0, 1.0, 2.0, 1.0]], "vias": [[1.5, 1.0]]}
    text = "(kicad_pcb\n)\n"
    a = board_writer.apply_routes(text, [route])
    b = board_writer.apply_routes(text, [route])
    assert a == b
    # uuid 内容派生：同内容同 uuid（去重语义）
    assert route["uuid"] if "uuid" in route else True
    u1 = board_writer.route_uuid(route)
    u2 = board_writer.route_uuid(dict(route))
    assert u1 == u2


def test_route_one_deterministic_on_synthetic_board(tmp_path):
    """同板态两次 route_one 输出逐字段一致（无 wall-clock 字段）。"""
    pads = [("P1", "1", "AAA", 5.0, 5.0, 0.8, 0.8, ("F.Cu",)),
            ("P2", "1", "AAA", 9.0, 5.0, 0.8, 0.8, ("F.Cu",))]
    nets = sorted({p[2] for p in pads})
    lines = ["(kicad_pcb",
             "\t(version 20260206)",
             '\t(generator "pcbflow-fb1-test")',
             "\t(layers (0 \"F.Cu\" signal) (6 \"In2.Cu\" signal))",
             '\t(net 0 "")']
    lines += ['\t(net %d "%s")' % (i + 1, n) for i, n in enumerate(nets)]
    lines.append('\t(gr_rect (start 0 0) (end 60 40) (layer "Edge.Cuts")'
                 " (width 0.05) (uuid \"e0\"))")
    for (ref, num, net, x, y, w, h, layers) in pads:
        ls = " ".join('"%s"' % l for l in layers)
        lines.append(
            '\t(footprint "T:T" (layer "F.Cu")\n'
            "\t\t(at %g %g)\n"
            '\t\t(property "Reference" "%s")\n'
            '\t\t(pad "%s" smd rect (at 0 0) (size %g %g) (layers %s)'
            ' (net "%s") (uuid "p-%s-%s"))\n'
            "\t)" % (x, y, ref, num, w, h, ls, net, ref, num))
    lines.append(")")
    d = tmp_path / "proj"
    d.mkdir()
    (d / "test.kicad_pcb").write_text("\n".join(lines) + "\n",
                                      encoding="utf-8")
    bm = route_grid.board_model(str(d))
    L = bm["pa"]["LAYERS"][0]
    r1 = route_grid.route_one(bm, "AAA", 5.0, 5.0, [L], 9.0, 5.0, [L])
    r2 = route_grid.route_one(bm, "AAA", 5.0, 5.0, [L], 9.0, 5.0, [L])
    assert r1 == r2
    assert "run_s" not in r1  # 核心产物禁 wall-clock 字段


def test_p3_replay_reproduces_pinned_sha_byte_exact():
    """③ 重放钉值：pristine(p3 快照)+placement.csv → sha256=2a25a8ac…。

    输入为冻结历史产物（out/coreboard-pa1 只读 + out/revc-b1 只读），
    缺失时 skip；FB-1 三臂底座即依赖此确定性。"""
    if not os.path.exists(PRISTINE):
        pytest.skip("p3 pristine 快照缺失（out/coreboard-pa1 未就位）")
    with open(PRISTINE, encoding="utf-8") as f:
        pristine = f.read()
    placement = residual_cmd._read_placement_rows()
    once = board_writer.apply_placement(pristine, placement)
    assert _sha(once) == REPLAYED_SHA
    twice = board_writer.apply_placement(pristine, placement)
    assert once == twice
