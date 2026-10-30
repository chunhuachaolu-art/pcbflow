"""v4cmp planner 输入编排。

同一 board + candidate geometry 的三种表示：
* B：结构化 JSON route/via geometry；
* C：SVG/XML 源码和机器对象摘要；
* D：与 C 完全相同的 SVG/XML/对象摘要，再加 PNG 视觉投影。

所有组共享 board facts、约束、动作合同、candidate hash、预算和当前指标。
模块只做纯对象构造与确定性 JSON 落盘；planner 输出永远由调用方另存，
本模块不执行模型、不写 live board。
"""

from __future__ import annotations

import copy
import os

from . import model, svg_pkg
from .cmp_patch import (ACTION_TYPES, MAX_PATCHES_PER_CALL, PATCH_SCHEMA,
                        candidate_geometry_sha256)

INPUT_SCHEMA = "pcbflow.v4cmp.planner-input/1"
INPUTS_SUMMARY_SCHEMA = "pcbflow.v4cmp.planner-inputs-summary/1"

PATCH_CONTRACT_TEXT = """你是受限局部布线规划器。输出一个 JSON 对象，不要输出 markdown。
响应 schema 必须是 pcbflow.v4cmp.planner-response/1，字段为：
{schema, scenario_id, board_snapshot_sha256, arm, round, patches, notes, uncertainty}。
patches 是最多 4 个 v4-route-patch/1 对象；超过 4 个的对象不计入预算。
每个 patch 必须包含 schema_version、action_type、base_candidate_geometry_sha256、
scenario_id、net_id、relation_id、parent_id、fixed_endpoint_ids、reason、source。
replace_subpath/move_vertex 还必须有 route_id/layer/width_mm/polyline_mm；
insert_via_candidate 还必须有 route_id/layer/via_mm/to_layer；
reject_route_patch 不得带几何字段，但仍须绑定 base hash 和 route identity。
动作只允许 replace_subpath、move_vertex、insert_via_candidate、reject_route_patch。
端点、route/net/relation/parent 身份、层、线宽、网格、净距、keepout 和连接性
必须保持合法。坐标帧：polyline_mm 与 via_mm 一律使用板 mm 坐标系（与
board_summary.bbox_mm 同帧，原点为板左下角 0,0）；SVG viewBox 含 +2.0mm
渲染边距（x_mm = svg_x - 2.0），不要用 SVG 帧坐标填写 patch。
不能确定时使用 reject_route_patch，不能伪造几何。
所有输出是不可信 planner 提案，必须经过独立 validator、geometry checker 和 rollback。
"""


def _relation_ids(board: dict, net_id: str) -> list:
    return sorted(str(r["relation_id"]) for r in board.get("relations", [])
                  if net_id in r.get("members", []))


def _line_type(board: dict, net_id: str) -> str:
    net = next((n for n in board["nets"] if str(n["net_id"]) == str(net_id)), None)
    if net is None:
        return "signal"
    cls = str(net.get("net_class", "default"))
    if cls == "clock":
        return "clock"
    rels = [r for r in board.get("relations", []) if net_id in r.get("members", [])]
    if any(r.get("relation_type") == "bus" for r in rels):
        return "bus_member"
    return "signal"


def enrich_reference(board: dict, geom: dict) -> dict:
    """给 solver/patch geometry 补齐 SVG/身份所需字段，不改变几何事实。"""
    routes = []
    for route in geom.get("routes", []):
        r = copy.deepcopy(route)
        nid = str(r["net_id"])
        r.setdefault("svg_id", "route-%s" % r["route_id"])
        r.setdefault("relation_ids", _relation_ids(board, nid))
        r.setdefault("line_type", _line_type(board, nid))
        r.setdefault("parent_id", None)
        r.setdefault("constraint_refs", [
            model.constraint_ref("clearance", board["rules"]["clearance_mm"]),
            model.constraint_ref("width", r["width_mm"]),
        ])
        r.setdefault("state", "candidate")
        r.setdefault("source", "solver")
        routes.append(r)
    vias = []
    for via in geom.get("vias", []):
        v = copy.deepcopy(via)
        v.setdefault("state", "candidate")
        v.setdefault("source", "solver")
        vias.append(v)
    return {"scenario_id": str(board["scenario_id"]),
            "reference_unrouted": False, "unrouted_net_ids": [],
            "routes": routes, "vias": vias}


def board_summary(board: dict) -> dict:
    """所有 arm 一致的板事实；不含 label/family/split/seed。"""
    return {
        "bbox_mm": list(board["board"]["bbox_mm"]),
        "layers": list(board["board"]["layers"]),
        "rules": copy.deepcopy(board["rules"]),
        "pads": copy.deepcopy(board["pads"]),
        "nets": [{"net_id": n["net_id"], "net_class": n["net_class"],
                  "endpoints": list(n["endpoints"])} for n in board["nets"]],
        "keepouts": copy.deepcopy(board.get("keepouts", [])),
        "relations": copy.deepcopy(board.get("relations", [])),
    }


def object_summary(reference: dict) -> list:
    """SVG 表示中仍可机器读取的对象摘要（不含完整 JSON polyline）。"""
    out = []
    for r in reference["routes"]:
        out.append({k: copy.deepcopy(r.get(k)) for k in (
            "route_id", "net_id", "relation_ids", "parent_id", "layer",
            "width_mm", "endpoint_ids", "line_type", "state", "source")})
    for v in reference["vias"]:
        out.append({k: copy.deepcopy(v.get(k)) for k in (
            "via_id", "net_id", "parent_id", "from_layer", "to_layer",
            "center_mm", "state", "source")})
    return out


def build_svg(board: dict, geom: dict):
    reference = enrich_reference(board, geom)
    # svg_pkg 的纯函数接口消费 Board dataclass；planner 输入仍保留原始 dict。
    board_obj = model.board_from_obj(board)
    manifest, svg_text = svg_pkg.build(board_obj, reference)
    return reference, manifest, svg_text


def build_input(board: dict, geom: dict, arm: str, round_no: int,
                mode: str = "search", feedback: dict | None = None,
                png_path: str | None = None) -> dict:
    """构造一个 arm/round planner input。

    mode='p1' 时额外带 target_contract，仍保持同一 PATCH_CONTRACT_TEXT。
    `png_path` 只作为仓库相对路径字符串，不读取文件。
    """
    if arm not in ("B0", "B1", "C0", "C1", "D0", "D1",
                   "P1-B", "P1-C", "P1-D", "P1-E"):
        raise ValueError("unknown arm: %s" % arm)
    if round_no not in (1, 2):
        raise ValueError("round must be 1 or 2")
    sid = str(board["scenario_id"])
    candidate_hash = candidate_geometry_sha256(geom)
    reference, manifest, svg_text = build_svg(board, geom)
    common = {
        "schema": INPUT_SCHEMA,
        "scenario_id": sid,
        "arm": arm,
        "round": round_no,
        "board_snapshot_sha256": model.sha256_of(board),
        "base_candidate_geometry_sha256": candidate_hash,
        "contract_text": PATCH_CONTRACT_TEXT,
        "action_types": list(ACTION_TYPES),
        "budget": {"max_patches_per_call": MAX_PATCHES_PER_CALL,
                   "max_calls": 2, "max_total_proposals": 8},
        "board_summary": board_summary(board),
        "candidate_metrics_hint": None,
        "feedback": copy.deepcopy(feedback) if feedback is not None else None,
        "mode": mode,
    }
    if arm.startswith("P1-"):
        common["p1_case_contract"] = {
            "target": "输入指定 route_id；只允许对该 route 提案或明确弃权",
            "candidate_budget": 1,
            "same_facts_across_BCD": True,
        }
    if arm.startswith("B") or arm == "P1-B":
        common["representation"] = "structured_json_route_manifest_geometry"
        common["candidate_geometry"] = {
            "routes": copy.deepcopy(reference["routes"]),
            "vias": copy.deepcopy(reference["vias"]),
        }
    else:
        common["representation"] = "svg_xml_object_data" \
            if not arm.startswith("D") else "svg_xml_object_data_plus_png"
        common["svg_source"] = svg_text
        common["svg_manifest_payload_sha256"] = manifest.get(
            "manifest_payload_sha256")
        common["object_summary"] = object_summary(reference)
    if arm.startswith("D") or arm == "P1-D":
        common["png_path"] = png_path
    return common


def write_input(path: str, obj: dict) -> None:
    model.write_json(path, obj)


def build_summary(entries: list) -> dict:
    return {"schema": INPUTS_SUMMARY_SCHEMA,
            "inputs": [copy.deepcopy(e) for e in entries],
            "count": len(entries)}
