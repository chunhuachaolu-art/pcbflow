# -*- coding: utf-8 -*-
"""loop —— 轮循环 runner（引擎侧一律 Bash/脚本驱动; 模型席位由编排体以
Agent 工具派发——harness-only）。

轮形态: runner new-round（打包落盘盲包）→ 编排体派绘制席（读盲包→写
edit-batch.json）→ runner ingest（fail-closed 收批→验证→落账）→ 下一轮。
逐轮目录 rounds/rNNN/（blind.svg + facts.json + edit-batch.json +
result.json）; 状态 out/canvas-pilot-r1/state-<board>.json; 台账 ledger.jsonl。
"""
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)

from v5 import board as v5board  # noqa: E402
from v5.canonical import canonical_json, canonical_sha256  # noqa: E402
from . import lattice as _lat  # noqa: E402
from . import packer, protocol, state as _state, verify  # noqa: E402
from .ledger import Ledger  # noqa: E402

OUT = os.path.join(ROOT, "out", "canvas-pilot-r1")

BOARD_PATHS = {
    "badgeleds-do-electronics":
        os.path.join(OUT, "..", "v5-p5", "boards",
                     "badgeleds-do-electronics", "board.json"),
    "pmod-bme280":
        os.path.join(OUT, "..", "v5-p5", "boards", "pmod-bme280", "board.json"),
}
PITCH_MM = 0.5


def out_dir():
    return OUT


def board_file(board_id):
    return os.path.normpath(BOARD_PATHS[board_id])


def load_board(board_id):
    raw = json.load(open(board_file(board_id), "rb"))
    board = raw["board"] if "board" in raw else raw
    # board_sha256 = board_for_hash 口径（v5.board.compute_board_sha256 同源）
    sha = v5board.compute_board_sha256(board)
    return board, sha


def new_canvas_state(board_id, pitch_mm=PITCH_MM):
    board, sha = load_board(board_id)
    lat = _lat.Lattice.from_board(board, pitch_mm)
    anchors = _lat.anchor_map(board, lat)
    st = _state.CanvasState(board, board_file(board_id), sha, lat, anchors)
    st.recompute_connectivity()
    _repair_dead_anchors(st)
    st.recompute_connectivity()
    return st


# 锚修补确定性序（距原锚一步的 8 邻域, 字典序）
_PATCH_ORDER = ((-1, -1), (-1, 0), (-1, 1), (0, -1),
                (0, 1), (1, -1), (1, 0), (1, 1))


def _dead_anchor(st, pid, k):
    """锚四向全拒（stub 或起步段违例）→ 死锚（探针口径同建设期自检）。"""
    from . import verify as _verify
    a = tuple(st.anchors[pid][k])
    net = st.partition_net(pid)
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        tgt = (a[0] + di, a[1] + dj)
        if not st.lattice.in_bounds(*tgt):
            continue
        if not _verify.check_route_candidate(st, net, pid, "F.Cu", [a, tgt]):
            return False
    return True


def _repair_dead_anchors(st, log=None):
    """确定性锚修补: 最近锚四向全拒时按 8 邻域字典序取首个可起笔格点。

    仅影响死锚（badgeleds 实测 1/36; pmod-bme280 0/26）; 修补后锚表随
    状态序列化冻结。log=list 时记录修补对（prereg/披露消费）。"""
    from . import lattice as _lattice
    from . import verify as _verify
    for p in st.board["partitions"]:
        pid = p["partition_id"]
        for k, a in enumerate(st.anchors[pid]):
            a = tuple(a)
            if not _dead_anchor(st, pid, k):
                continue
            net = st.partition_net(pid)
            for di, dj in _PATCH_ORDER:
                cand = (a[0] + di, a[1] + dj)
                if not st.lattice.in_bounds(*cand):
                    continue
                st.anchors[pid][k] = list(cand)
                ok = False
                for ei, ej in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    tgt = (cand[0] + ei, cand[1] + ej)
                    if st.lattice.in_bounds(*tgt) and \
                            not _verify.check_route_candidate(
                                st, net, pid, "F.Cu", [cand, tgt]):
                        ok = True
                        break
                if ok:
                    if log is not None:
                        log.append({"partition_id": pid, "endpoint": k,
                                    "from": list(a), "to": list(cand)})
                    break
                st.anchors[pid][k] = list(a)
    # 修补后重验全锚（防修补引入新冲突——锚共享冲突 fail-closed）
    seen = {}
    for pid, anchors in st.anchors.items():
        for k, a in enumerate(anchors):
            key = tuple(a)
            if key in seen and seen[key][0] != pid:
                raise _lattice.LatticeError(
                    "锚修补引入冲突 %s vs %s#%d @%s"
                    % (seen[key], pid, k, list(a)))
            seen[key] = (pid, k)
    return log or []


def state_path(board_id):
    return os.path.join(OUT, "state-%s.json" % board_id)


def save_state(st):
    d = st.as_dict()
    with open(state_path(st.board["board_id"]), "wb") as f:
        f.write(canonical_json(d))


def load_state(board_id):
    d = json.load(open(state_path(board_id), "rb"))
    board, _sha = load_board(board_id)
    st = _state.CanvasState.from_dict(d, board)
    st.recompute_connectivity()
    return st


def has_state(board_id):
    return os.path.exists(state_path(board_id))


def round_dir(board_id, round_no):
    return os.path.join(OUT, "rounds", board_id, "r%03d" % round_no)


def new_round(board_id, ledger):
    """打包当前状态为下一轮盲包 → 返回轮号与盲包路径。"""
    st = load_state(board_id)
    rdir = os.path.join(OUT, "rounds", board_id)
    if not os.path.isdir(rdir):
        os.makedirs(rdir)
    existing = [d for d in os.listdir(rdir) if d.startswith("r")]
    round_no = len(existing) + 1
    rd = round_dir(board_id, round_no)
    os.makedirs(rd)
    last_rej = st.__dict__.get("last_rejections", [])
    svg = packer.pack_svg(st, round_no, last_rej)
    facts = packer.pack_facts(st, round_no, last_rej)
    with open(os.path.join(rd, "blind.svg"), "wb") as f:
        f.write(svg.encode("utf-8"))
    with open(os.path.join(rd, "facts.json"), "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=1, sort_keys=True)
    ledger.append("round_pack", {
        "board": board_id, "round": round_no,
        "facts_sha": canonical_sha256(facts),
        "svg_sha256": __import__("hashlib").sha256(svg.encode("utf-8")).hexdigest(),
        "state_routed": st.routed_nets(),
        "state_segs": len(st.segs), "state_vias": len(st.vias),
    })
    return round_no, rd


def ingest(board_id, round_no, batch_path, ledger):
    """收批 → fail-closed ingest → 落账。返回 result dict（并落盘）。"""
    rd = round_dir(board_id, round_no)
    st = load_state(board_id)
    text = open(batch_path, "r", encoding="utf-8").read()
    result = {"board": board_id, "round": round_no, "batch": os.path.basename(batch_path)}
    try:
        actions = protocol.parse_batch(text, expected_round=round_no)
    except protocol.BatchReject as exc:
        result.update({"outcome": "batch_rejected", "code": exc.code,
                       "detail": exc.detail, "accepted": 0, "rejected": 0})
        st.last_rejections = [{"code": exc.code, "grid_hint": None,
                               "detail": exc.detail, "action_index": None}]
        save_state(st)
        ledger.append("round_ingest", dict(result))
        _dump_result(rd, result)
        return result
    pre = protocol.apply_batch(st, actions, round_no)
    # 拒收细节留痕（grid_hint 供 SVG 幽灵标记）
    rejections = []
    for r in pre:
        if not r.get("accepted", False):
            a = actions[r["index"]]
            hint = None
            if a.get("action") == "route" and a.get("waypoints"):
                hint = a["waypoints"][0]
            elif a.get("action") == "via" and a.get("grid"):
                hint = a["grid"]
            rejections.append({"code": r.get("code"), "grid_hint": hint,
                               "detail": r.get("detail"),
                               "action_index": r["index"]})
    st.last_rejections = rejections
    save_state(st)
    accepted = sum(1 for r in pre if r.get("accepted"))
    rejected = len(pre) - accepted
    result.update({
        "outcome": "applied",
        "accepted": accepted, "rejected": rejected,
        "results": pre,
        "routed_nets": st.routed_nets(),
        "total_nets": len(st.connectivity),
        "unrouted": [k for k in sorted(st.connectivity)
                     if not st.connectivity[k]],
    })
    ledger.append("round_ingest", {
        "board": board_id, "round": round_no, "outcome": "applied",
        "accepted": accepted, "rejected": rejected,
        "state_sha": canonical_sha256(st.snapshot_for_hash()),
        "routed": st.routed_nets(), "total": len(st.connectivity),
    })
    _dump_result(rd, result)
    return result


def _dump_result(rd, result):
    slim = dict(result)
    with open(os.path.join(rd, "result.json"), "w", encoding="utf-8") as f:
        json.dump(slim, f, indent=1, sort_keys=True, ensure_ascii=False)


def status(board_id):
    st = load_state(board_id)
    viols = verify.full_check(st)
    return {
        "board": board_id,
        "rounds": len([d for d in os.listdir(os.path.join(
            OUT, "rounds", board_id)) if d.startswith("r")]),
        "routed": st.routed_nets(), "total": len(st.connectivity),
        "unrouted": [k for k in sorted(st.connectivity)
                     if not st.connectivity[k]],
        "segs": len(st.segs), "vias": len(st.vias),
        "drc_violations": len(viols),
    }


def build_routes_doc(st):
    """画板终态 → v5.routes.v1 文档（kicad 导出与 validate_routes 复核用）。

    段→entry: polyline=segment_mm（含 stub→真实端点首末）; 段衔接 via →
    transition_vias 披露; return_vias=[]（画板协议无回流孔概念——R4 审计
    为披露层, G-CP2 外权威 kicad DRC 不查, verdict 披露形态差异）。"""
    from . import instantiate as inst
    entries = []
    for s in st.segs:
        pts, _stub = inst.segment_mm(st, s)
        tvs = []
        anchors = {tuple(a) for a in st.anchors[s["partition_id"]]}
        via_set = st.via_grids(s["net_id"])
        for g in s["grid"]:
            if tuple(g) in via_set and tuple(g) not in anchors:
                mm = st.lattice.to_mm(*g)
                tvs.append([mm[0], mm[1]])
        entries.append({
            "net_id": s["net_id"], "partition_id": s["partition_id"],
            "layer": s["layer"],
            "polyline": [[p[0], p[1]] for p in pts],
            "transition_vias": tvs, "return_vias": [],
            "width": verify.WIDTH_MM,
        })
    return {
        "schema_version": "v5.routes.v1",
        "board_id": st.board["board_id"],
        "board_sha256": st.board_sha256,
        "routes": entries,
        "negotiation_log": ["canvas-pilot-r1 direct-draw"],
        "provenance": {
            "generator": "canvas_pilot/0.1.0",
            "board_sha256": st.board_sha256,
        },
    }
