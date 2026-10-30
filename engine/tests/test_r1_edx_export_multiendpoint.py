# -*- coding: utf-8 -*-
"""V5-R1 ED-X 修复钉（任务书 V5-R1-EDX-EXPORT-FIX-2026-09-26 W-X3；
kicad_export 0.4.0→0.5.0）。

覆盖（任务书 §2 W-X3 ①②③）：
- ① 多端网 export round-trip 过（合成多端板：≥3 端点分区逐端点 pad_terminals
  + thru_hole PTH 分支形态；段/孔/网表全等+单分区网端点逐位等）；
- ② 2 端旧域回归钉（隐式 anchor module 名恰 a/b、无 e 前缀；双跑字节等）；
- ③ W-X2 四缺口发现面钉：_validate 放宽域与逐点键路径（缺口①）、pads 发射
  endpoint≥2 计数与 tag 唯一性（缺口③）、_aligned argmin 近端指派（缺口④）、
  隐式 anchor 多端点补发（缺口②，消费侧后处理）；
- ④ 版本钉 0.5.0（本文件）；tests/test_wave6_export_alignment.py:481 硬钉
  翻新披露见该文件（首跑 failed 全列名=版本钉 1 处，无其它翻新面）。

零 LLM API、零网络；不调 kicad-cli（外权威面归 W-X5 run_p5_board drc 段）。
"""
import pytest

from v5.adapters.kicad_adapter import convert_file, sanitize_net_id
from v5.board import compute_board_sha256, load_board
from v5.kicad_export import (
    ANCHOR_PAD_SIZE_MM,
    VERSION,
    ExportError,
    align_endpoint_into_pad,
    kicad_pcb_bytes,
)


# --------------------------------------------------------------- 夹具（同款形态）

def _hand_board(nets, partitions, board_id="edx-hand", validate=True):
    bd = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 60.0, "y_max": 30.0},
        "zones": [],
        "partitions": partitions,
        "nets": nets,
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "synthetic://hand",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
    if validate:
        load_board(bd)
    return bd


def _routes_doc(bd, entries):
    return {
        "schema_version": "v5.routes.v1",
        "board_id": bd["board_id"],
        "board_sha256": bd["provenance"]["board_sha256"],
        "routes": entries,
        "negotiation_log": [],
        "provenance": {"generator": "v5.executor/0.8.0",
                       "board_sha256": bd["provenance"]["board_sha256"]},
    }


def _pterm(ep, layers="all", shape="circle", size=1.0):
    """pad_terminals 单项（crypto 板同形态：endpoint 索引+shape+size_mm+layers）。"""
    return {"endpoint": ep, "shape": shape, "size_mm": [size], "layers": layers}


def _multi_end_board(n_ep=4, pad_layers="all"):
    """≥3 端点分区板：逐端点 pad_terminals（R1 全端点入模形态）。"""
    eps = [[5.0 + 8.0 * k, 5.0] for k in range(n_ep)]
    return _hand_board(
        nets=[{"net_id": "NET1", "partitions": ["PT-M"]}],
        partitions=[{
            "partition_id": "PT-M", "ptype": "MISC",
            "geometry": {"endpoints": eps,
                         "pad_terminals": [_pterm(k, pad_layers)
                                           for k in range(n_ep)]},
            "layer_policy": "any", "width_prior": {"w_min": 0.2, "w_max": 0.4},
            "current_a": 0, "speed_class": "unknown",
        }])


def _modules(data):
    """导出 bytes → [(module 名, at(x,y), net 引用)]（文本逐行抽取）。"""
    out = []
    for line in data.decode("utf-8").splitlines():
        s = line.strip()
        if s.startswith("(module "):
            out.append(s)
    return out


# ------------------------------------------------- ① 多端网 export round-trip

def test_multi_endpoint_roundtrip_with_pth_branch(tmp_path):
    """① 多端网（4 端点+PTH thru_hole pad 分支形态）export→adapter 读回：
    段/孔/网表全等；单分区网读回端点逐位相等（超范围加分断言同款）。"""
    bd = _multi_end_board(4)
    eps = bd["partitions"][0]["geometry"]["endpoints"]
    routes = _routes_doc(bd, [
        # F.Cu 主干：端点 0 → 端点 1；换层孔（PTH 分支=端点 2 走 B.Cu 经孔）
        {"partition_id": "PT-M", "net_id": "NET1", "layer": "F.Cu", "width": 0.25,
         "polyline": [list(eps[0]), list(eps[1])],
         "transition_vias": [[eps[1][0], eps[1][1] + 1.0]], "return_vias": []},
        {"partition_id": "PT-M", "net_id": "NET1", "layer": "B.Cu", "width": 0.25,
         "polyline": [[eps[1][0], eps[1][1] + 1.0], list(eps[2])],
         "transition_vias": [], "return_vias": []},
        {"partition_id": "PT-M", "net_id": "NET1", "layer": "F.Cu", "width": 0.25,
         "polyline": [list(eps[2]), list(eps[3])],
         "transition_vias": [], "return_vias": []},
    ])
    data = kicad_pcb_bytes(bd, routes)
    p = tmp_path / "m.kicad_pcb"
    p.write_bytes(data)
    reread = convert_file(str(p), bd["board_id"])
    assert [n["net_id"] for n in reread["nets"]] == ["NET1"]
    rid = "PT-" + sanitize_net_id("NET1")
    got = next(pp for pp in reread["partitions"]
               if pp["partition_id"] == rid)["geometry"]["endpoints"]
    assert [list(map(float, e)) for e in got] == \
        [list(map(float, e)) for e in eps]
    # 段数=折线段数和（3 entry 各 1 段）；孔=1（同坐标去重）；module=4（逐端点 anchor）
    text = data.decode("utf-8")
    assert text.count("  (segment ") == 3
    assert text.count("  (via ") == 1
    assert len(_modules(data)) == 4


def test_multi_endpoint_double_run_byte_equal():
    """① 确定性面：多端板同输入双跑字节等（0.5.0 版本行内嵌，双跑含版本）。"""
    bd = _multi_end_board(5)
    routes = _routes_doc(bd, [
        {"partition_id": "PT-M", "net_id": "NET1", "layer": "F.Cu", "width": 0.25,
         "polyline": [[5.0, 5.0], [37.0, 5.0]],
         "transition_vias": [], "return_vias": []}])
    assert kicad_pcb_bytes(bd, routes) == kicad_pcb_bytes(bd, routes)


# ------------------------------------------------- ② 2 端旧域回归钉

def test_two_endpoint_domain_module_tags_unchanged():
    """② 2 端隐式 anchor 域：module 名恰 a/b（无 e 前缀、无计数后缀），
    双跑字节等——0.5.0 对 2 端旧域逐位不变的锚（walkthrough §3）。"""
    bd = _hand_board(
        nets=[{"net_id": "NET1", "partitions": ["PT-2"]}],
        partitions=[{
            "partition_id": "PT-2", "ptype": "MISC",
            "geometry": {"endpoints": [[0.0, 0.0], [10.0, 0.0]]},
            "layer_policy": "any", "width_prior": {"w_min": 0.2, "w_max": 0.4},
            "current_a": 0, "speed_class": "unknown",
        }])
    routes = _routes_doc(bd, [
        {"partition_id": "PT-2", "net_id": "NET1", "layer": "F.Cu", "width": 0.25,
         "polyline": [[0.0, 0.0], [10.0, 0.0]],
         "transition_vias": [], "return_vias": []}])
    data = kicad_pcb_bytes(bd, routes)
    mods = _modules(data)
    assert len(mods) == 2
    names = sorted(m.split('"')[1] for m in mods)
    assert names == ["V5-anchor-PT-2-a", "V5-anchor-PT-2-b"]
    assert kicad_pcb_bytes(bd, routes) == data


# ------------------------------------- ③ W-X2 四缺口发现面钉（逐缺口）

def test_gap1_validate_relaxes_to_ge2_with_indexed_paths():
    """缺口①：端点数 <2 仍 fail-closed（计数文案）；逐点校验带索引键路径
    （第 3 点非法 → endpoints[2]）。注：schema（board.v1 endpoints minItems=2
    无上限）与 export 合同双层防御——<2 板须 validate=False 绕过 load_board
    直达 export 合同面（schema 先拦=世界侧防御在位，另证 ED-X 系 _validate
    独有「恰 2」遗留而非 schema 意图）。"""
    def part(eps):
        return [{"partition_id": "PT-M", "ptype": "MISC",
                 "geometry": {"endpoints": eps,
                              "pad_terminals": [_pterm(k) for k in range(len(eps))]},
                 "layer_policy": "any", "width_prior": {"w_min": 0.2, "w_max": 0.4},
                 "current_a": 0, "speed_class": "unknown"}]
    bd = _hand_board([{"net_id": "NET1", "partitions": ["PT-M"]}],
                     part([[0.0, 0.0]]), validate=False)
    routes = _routes_doc(bd, [])
    with pytest.raises(ExportError, match=r"endpoints.*须为 ≥2 端点列表"):
        kicad_pcb_bytes(bd, routes)
    bd = _hand_board([{"net_id": "NET1", "partitions": ["PT-M"]}],
                     part([[0.0, 0.0], [10.0, 0.0], ["x", 20.0]]),
                     validate=False)
    with pytest.raises(ExportError, match=r"endpoints\[2\]"):
        kicad_pcb_bytes(bd, _routes_doc(bd, []))


def test_gap3_pads_emission_endpoint_ge2_tags_unique():
    """缺口③：endpoint≥2 发射不崩（旧 per_end={0:0,1:0} 必 KeyError）；
    (前缀,计数) tag 全网内唯一；e 前缀域自 2 起。"""
    # 6 pad：endpoint 0×2、1×1、2×2、3×1 → tag a/a2/b/e2/e22/e3
    bd = _hand_board(
        nets=[{"net_id": "NET1", "partitions": ["PT-M"]}],
        partitions=[{
            "partition_id": "PT-M", "ptype": "MISC",
            "geometry": {"endpoints": [[5.0, 5.0], [13.0, 5.0],
                                       [21.0, 5.0], [29.0, 5.0]],
                         "pad_terminals": [
                             _pterm(0, ["F.Cu"]), _pterm(0, ["F.Cu"]),
                             _pterm(1, ["F.Cu"]), _pterm(2, ["F.Cu"]),
                             _pterm(2, ["F.Cu"]), _pterm(3, ["F.Cu"])]},
            "layer_policy": "any", "width_prior": {"w_min": 0.2, "w_max": 0.4},
            "current_a": 0, "speed_class": "unknown",
        }])
    routes = _routes_doc(bd, [
        {"partition_id": "PT-M", "net_id": "NET1", "layer": "F.Cu", "width": 0.25,
         "polyline": [[5.0, 5.0], [29.0, 5.0]],
         "transition_vias": [], "return_vias": []}])
    data = kicad_pcb_bytes(bd, routes)
    names = sorted(m.split('"')[1] for m in _modules(data))
    assert names == ["V5-anchor-PT-M-a", "V5-anchor-PT-M-a2", "V5-anchor-PT-M-b",
                     "V5-anchor-PT-M-e2", "V5-anchor-PT-M-e22",
                     "V5-anchor-PT-M-e3"]
    assert len(names) == len(set(names)) == 6


def test_gap4_aligned_argmin_over_all_endpoints():
    """缺口④：真端点近端指派 argmin 全端点——尾点最近端点 2 时扎铜对象=
    端点 2 的焊盘（旧 d0/d1 只看 eps[0]/eps[1] → chosen 铜邻域外原样不动）。"""
    # 端点 2 焊盘 circle d=1.0（r=0.5）@ (21,5)；尾点 (21.8,5)：在铜外、
    # 距心 0.8 ≤ ANCHOR 邻域 1.0 → 扎铜 = 心+边界中点方向 (21.25,5)。
    bd = _multi_end_board(4)
    eps = bd["partitions"][0]["geometry"]["endpoints"]
    routes = _routes_doc(bd, [
        {"partition_id": "PT-M", "net_id": "NET1", "layer": "F.Cu", "width": 0.25,
         "polyline": [list(eps[0]), [21.8, 5.0]],
         "transition_vias": [], "return_vias": []}])
    data = kicad_pcb_bytes(bd, routes)
    text = data.decode("utf-8")
    want = align_endpoint_into_pad([21.8, 5.0], (21.0, 5.0), "circle", [1.0])
    assert "  (segment (start 5.0 5.0) (end %s %s)" % (
        repr(float(want[0])), repr(float(want[1]))) in text


def test_gap2_implicit_anchor_supplement_for_multi_endpoint():
    """缺口②：无 pad_terminals 多端分区（≥3 端点）消费侧补发端点 2..n-1
    anchor（a/b/e2/e3）；2 端隐式分区不补（=②回归钉的另一面）。"""
    def mk(eps):
        return _hand_board(
            nets=[{"net_id": "NET1", "partitions": ["PT-I"]}],
            partitions=[{
                "partition_id": "PT-I", "ptype": "MISC",
                "geometry": {"endpoints": eps},
                "layer_policy": "any",
                "width_prior": {"w_min": 0.2, "w_max": 0.4},
                "current_a": 0, "speed_class": "unknown",
            }])
    eps3 = [[0.0, 0.0], [10.0, 0.0], [20.0, 0.0], [30.0, 0.0]]
    bd = mk(eps3)
    routes = _routes_doc(bd, [
        {"partition_id": "PT-I", "net_id": "NET1", "layer": "F.Cu", "width": 0.25,
         "polyline": [[0.0, 0.0], [30.0, 0.0]],
         "transition_vias": [], "return_vias": []}])
    names = sorted(m.split('"')[1] for m in _modules(kicad_pcb_bytes(bd, routes)))
    assert names == ["V5-anchor-PT-I-a", "V5-anchor-PT-I-b",
                     "V5-anchor-PT-I-e2", "V5-anchor-PT-I-e3"]
    # 2 端隐式：恰 a/b 两枚（补发不触发）
    bd2 = mk([[0.0, 0.0], [10.0, 0.0]])
    names2 = sorted(m.split('"')[1] for m in _modules(
        kicad_pcb_bytes(bd2, _routes_doc(bd2, [
            {"partition_id": "PT-I", "net_id": "NET1", "layer": "F.Cu",
             "width": 0.25, "polyline": [[0.0, 0.0], [10.0, 0.0]],
             "transition_vias": [], "return_vias": []}]))))
    assert names2 == ["V5-anchor-PT-I-a", "V5-anchor-PT-I-b"]


def test_anchor_neighborhood_constant_unchanged():
    """D6-2 邻域常量锚（0.5.0 零动面）：扎铜邻域=ANCHOR_PAD_SIZE_MM。"""
    assert ANCHOR_PAD_SIZE_MM == 1.0


# ------------------------------------------------- ④ 版本钉

def test_version_pin_0_5_0():
    """④ 版本钉：0.4.0→0.5.0（V5-R1 ED-X 修复批翻转披露，D8/R1 同式先例；
    既有硬钉翻新=tests/test_wave6_export_alignment.py:481 一处）。"""
    assert VERSION == "0.7.0"  # OPT-11 同步（空净类+drill 分开建模）
