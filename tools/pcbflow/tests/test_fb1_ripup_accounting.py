"""FB-1 单测：ripup 范围记账（拆线计数/重布提取/板文本拆线落铜管路）。

不依赖 Rev-C 实板；合成板文本 + 构造 Plan 对象，全部确定性。
"""

from __future__ import annotations

import pytest

from pcbflow import board_writer, fb1_experiment, route_grid
from pcbflow.board_writer import LAYER_FILE_NAME


# ---- 合成板文本（两网各有铜；可解析、可拆线） --------------------------------
def _seg_text(net, uuid, x1, y1, x2, y2, layer="F.Cu", width="0.2"):
    return ("\t(segment\n"
            "\t\t(start %s %s)\n"
            "\t\t(end %s %s)\n"
            "\t\t(width %s)\n"
            '\t\t(layer "%s")\n'
            '\t\t(net "%s")\n'
            '\t\t(uuid "%s")\n'
            "\t)\n" % (x1, y1, x2, y2, width, layer, net, uuid))


def _via_text(net, uuid, x, y):
    return ("\t(via buried\n"
            "\t\t(at %s %s)\n"
            "\t\t(size 0.6)\n"
            "\t\t(drill 0.3)\n"
            '\t\t(layers "F.Cu" "In2.Cu")\n'
            '\t\t(net "%s")\n'
            '\t\t(uuid "%s")\n'
            "\t)\n" % (x, y, net, uuid))


def _board_text(body):
    return ("(kicad_pcb\n"
            "\t(version 20260206)\n"
            '\t(generator "pcbflow-fb1-test")\n'
            "\t(page A4)\n"
            "\t(layers (0 \"F.Cu\" signal) (6 \"In2.Cu\" signal))\n"
            "\t(net 0 \"\")\n"
            "\t(net 1 \"AAA\")\n"
            "\t(net 2 \"BBB\")\n"
            + body + ")\n")


def _two_net_board():
    body = (_seg_text("AAA", "u-a1", "1.0", "1.0", "5.0", "1.0")
            + _seg_text("AAA", "u-a1", "5.0", "1.0", "9.0", "1.0")
            + _via_text("AAA", "u-a1", "9.0", "1.0")
            + _seg_text("BBB", "u-b1", "2.0", "8.0", "6.0", "8.0")
            + _seg_text("BBB", "u-b1", "6.0", "8.0", "6.0", "9.0",
                        layer="In2.Cu"))
    return _board_text(body)


# ---- 构造 Plan（含 ripup 依赖字段） ------------------------------------------
def _plan(net, segs, vias=(), ripup_net=None, ripup_plan=None):
    route_grid.load_adapter()          # 挂 pcbagent sys.path（与主链同法）
    from pcbagent.router import Plan

    p = Plan(net, (0.0, 0.0, frozenset({0})), (1.0, 1.0, frozenset({0})))
    p.ok = True
    p.segments = list(segs)
    p.vias = list(vias)
    p.ripup_net = ripup_net
    p.ripup_plan = ripup_plan
    return p


def test_normalize_plan_carries_ripup_fields():
    replan = _plan("BBB", [(0, 0.0, 0.0, 1.0, 0.0)])
    main = _plan("AAA", [(0, 0.0, 0.0, 2.0, 0.0)],
                 ripup_net="BBB", ripup_plan=replan)
    norm = fb1_experiment.normalize_plan(main)
    assert norm["ok"] is True
    assert norm["ripup_net"] == "BBB"
    assert norm["ripup_plan"]["net"] == "BBB"
    assert norm["ripup_plan"]["segments"] == [[0, 0.0, 0.0, 1.0, 0.0]]


def test_ripup_ops_of_extracts_dependencies():
    replan = _plan("BBB", [(0, 0.0, 0.0, 1.0, 0.0)])
    main = _plan("AAA", [(0, 0.0, 0.0, 2.0, 0.0)],
                 ripup_net="BBB", ripup_plan=replan)
    ops = fb1_experiment.ripup_ops_of(fb1_experiment.normalize_plan(main))
    assert [n for (n, _rp) in ops] == ["BBB"]
    assert ops[0][1]["length_mm"] == 1.0

    plain = fb1_experiment.normalize_plan(_plan("CCC", [(0, 0.0, 0.0, 1.0, 1.0)]))
    assert fb1_experiment.ripup_ops_of(plain) == []


def test_plan_to_route_deterministic_uuid():
    norm = fb1_experiment.normalize_plan(_plan("AAA", [(0, 0.0, 0.0, 2.0, 0.0)]))
    r1 = fb1_experiment.plan_to_route(norm, row_id="RPL-999", net_id="N001")
    r2 = fb1_experiment.plan_to_route(norm, row_id="RPL-999", net_id="N001")
    assert r1["uuid"] == r2["uuid"]
    assert r1["uuid"] == board_writer.route_uuid(
        {"net": "AAA", "segments": norm["segments"], "vias": norm["vias"]})


# ---- 板文本拆线记账 ----------------------------------------------------------
def test_count_and_remove_only_ripped_net():
    text = _two_net_board()
    c = fb1_experiment.count_net_nodes(text, "AAA")
    assert c == {"segment": 2, "via": 1, "total": 3}
    c_b = fb1_experiment.count_net_nodes(text, "BBB")
    assert c_b == {"segment": 2, "via": 0, "total": 2}

    spans = fb1_experiment.removed_spans(text, "AAA")
    stripped = fb1_experiment.strip_spans(text, spans)
    # 被拆网铜归零，他网铜原样保留
    assert fb1_experiment.count_net_nodes(stripped, "AAA")["total"] == 0
    assert fb1_experiment.count_net_nodes(stripped, "BBB")["total"] == 2
    assert '(net "BBB")' in stripped


def test_apply_ripup_commit_removes_and_appends():
    text = _two_net_board()
    new_route = {"net": "CCC", "width": 0.2, "via_size": 0.6,
                 "via_drill": 0.3,
                 "segments": [[0, 4.0, 4.0, 5.0, 4.0]], "vias": []}
    out, spans = fb1_experiment.apply_ripup_commit(
        text, [new_route], ["AAA"])
    assert len(spans) == 3
    assert fb1_experiment.count_net_nodes(out, "AAA")["total"] == 0
    assert fb1_experiment.count_net_nodes(out, "BBB")["total"] == 2
    assert fb1_experiment.count_net_nodes(out, "CCC")["total"] == 1
    # 板仍闭合、可再次解析出节点
    assert out.rstrip().endswith(")")
    # 被删节点文本不再出现（按 uuid 精确核对）
    assert 'u-a1' not in out
    assert 'u-b1' in out


def test_apply_ripup_commit_no_rip_is_pure_append():
    text = _two_net_board()
    new_route = {"net": "CCC", "width": 0.2, "via_size": 0.6,
                 "via_drill": 0.3,
                 "segments": [[0, 4.0, 4.0, 5.0, 4.0]], "vias": []}
    out, spans = fb1_experiment.apply_ripup_commit(text, [new_route], [])
    assert spans == []
    assert out == board_writer.apply_routes(text, [new_route])


# ---- 批判定（新增 error=0 才接受；新增 warning 不否决） ----------------------
def _drc(viol):
    return {"violations": viol, "unconnected_items": [{"a": 1}] * 3}


def test_batch_verdict_accepts_clean_candidate():
    base = _drc([{"type": "courtyards_overlap", "severity": "warning",
                  "items": [{"description": "x"}]}])
    cand = _drc([])
    v = fb1_experiment.batch_verdict(base, cand)
    assert v["accepted"] is True
    assert v["new_errors_vs_baseline"] == 0


def test_batch_verdict_rejects_new_error():
    base = _drc([])
    cand = _drc([{"type": "clearance", "severity": "error",
                  "items": [{"description": "AAA;BBB"}]}])
    v = fb1_experiment.batch_verdict(base, cand)
    assert v["accepted"] is False
    assert v["new_errors_vs_baseline"] == 1
    assert v["new_detail"]


def test_batch_verdict_warning_only_new_is_accepted():
    base = _drc([])
    cand = _drc([{"type": "track_dangling", "severity": "warning",
                  "items": [{"description": "d"}]}])
    v = fb1_experiment.batch_verdict(base, cand)
    assert v["accepted"] is True
    assert v["new_vs_baseline"] == 1
    assert v["new_errors_vs_baseline"] == 0


# ---- 主链 ripup=False 语义保持（route_grid 零改动的行为锚） -----------------
def _single_project(tmp_path):
    """两焊盘同网直连的最小工程（pcbagent mirror 可解析）。"""
    pads = [("P1", "1", "AAA", 5.0, 5.0, 0.8, 0.8, ("F.Cu",)),
            ("P2", "1", "AAA", 9.0, 5.0, 0.8, 0.8, ("F.Cu",))]
    nets = sorted({p[2] for p in pads if p[2]})
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
    return str(d)


def test_route_one_output_has_no_ripup_fields(tmp_path):
    """route_grid.route_one 归一化口径不含 ripup 字段（冻结语义未被动过）。"""
    proj = _single_project(tmp_path)
    bm = route_grid.board_model(proj)
    r = route_grid.route_one(bm, "AAA", 5.0, 5.0, [bm["pa"]["LAYERS"][0]],
                             9.0, 5.0, [bm["pa"]["LAYERS"][0]])
    assert r["ok"] is True
    assert "ripup_net" not in r
    assert "ripup_plan" not in r
