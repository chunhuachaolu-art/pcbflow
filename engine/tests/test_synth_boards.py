# -*- coding: utf-8 -*-
"""A2-SYNTHBOARD-R1 第四代合成板生成器验收测试（只测生成面：不跑
execute/plan_candidates——布线执行属 W2，PREREG 冻结后才跑；compile 面允许）。

覆盖：20 板 fail-closed 载入、canonical 字节稳定、provenance 形态与
authoring 链、恰一条粒度先验、旋钮/sidecar 与冻结矩阵一致、矩阵 10+10 与
难度/模式/层数覆盖、可布性 witness 几何自查（独立重算）、不可布密封几何
自查、builder 双跑同字节、依赖纪律（stdlib+白名单、不 import tests/与
既有 builder）、compile 面（partition/compile/conflicts/pkg + compile 双跑
字节等）。
"""
import hashlib
import json
import math
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from boards import build_synth_boards as B  # noqa: E402
from v5 import canonical, schema_loader  # noqa: E402
from v5.board import compute_board_sha256, load_board_file  # noqa: E402

BOARDS_DIR = B.OUT_DIR
SPECS = {s["board_id"]: s for s in B.BOARD_SPECS}
IDS = [s["board_id"] for s in B.BOARD_SPECS]
ROUTABLE = [i for i in IDS if SPECS[i]["routable"]]
UNROUTABLE = [i for i in IDS if not SPECS[i]["routable"]]

_PRINCIPLE_SCHEMA = schema_loader.load_schema(
    "principle_registry.v1.schema.json")["definitions"]["principle"]

# 依赖纪律白名单（stdlib 子集 + v5 两件；禁 tests/ 与既有三个 builder）
_ALLOWED_IMPORTS = {"hashlib", "json", "math", "os", "random", "sys",
                    "v5.canonical", "v5.board"}


def _path(bid, ext="board.v1.json"):
    return os.path.join(BOARDS_DIR, "%s.%s" % (bid, ext))


def _load(bid):
    return load_board_file(_path(bid))


def _sidecar(bid):
    with open(_path(bid, "sidecar.json"), encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------ 1. 面数与载入

def test_matrix_shape_10_10():
    assert len(IDS) == 20 and len(set(IDS)) == 20
    assert len(ROUTABLE) == 10 and len(UNROUTABLE) == 10


def test_difficulty_mode_layer_coverage():
    for group in (ROUTABLE, UNROUTABLE):
        diff = [SPECS[i]["difficulty"] for i in group]
        assert diff.count("low") >= 3 and diff.count("mid") >= 3 \
            and diff.count("high") >= 3
        modes = {SPECS[i]["mode"] for i in group}
        assert modes == {"paired", "random", "clustered"}
    assert {SPECS[i]["layers"] for i in IDS} == {2, 4, 6}
    assert len({SPECS[i]["seed"] for i in IDS}) == len(IDS)  # 种子全异


def test_board_files_exactly_20_pairs():
    files = sorted(os.listdir(BOARDS_DIR))
    boards = [f for f in files if f.endswith(".board.v1.json")]
    sides = [f for f in files if f.endswith(".sidecar.json")]
    assert len(boards) == 20 and len(sides) == 20


@pytest.mark.parametrize("bid", IDS)
def test_load_fail_closed(bid):
    board = _load(bid)
    assert board["schema_version"] == "v5.board.v1"
    assert board["board_id"] == bid


@pytest.mark.parametrize("bid", IDS)
def test_canonical_bytes_stable(bid):
    with open(_path(bid), "rb") as f:
        raw = f.read()
    assert raw == canonical.canonical_json(json.loads(raw.decode("utf-8")))


@pytest.mark.parametrize("bid", IDS)
def test_board_sha256_chain(bid):
    board = _load(bid)
    assert board["provenance"]["board_sha256"] == compute_board_sha256(board)


# ------------------------------------------------ 2. provenance/registry/hard_rules

@pytest.mark.parametrize("bid", IDS)
def test_provenance_authoring_chain(bid):
    board = _load(bid)
    prov = board["provenance"]
    assert prov["source_type"] == "synthetic"
    with open(B._SCRIPT_PATH, "rb") as f:
        script_sha = hashlib.sha256(f.read()).hexdigest()
    assert prov["source_sha256"] == script_sha          # 脚本即源（authoring）
    assert prov["source_uri"] == ("synthetic:boards/build_synth_boards.py#"
                                  + bid)                # 仓库相对键，无主机路径
    assert prov["adapter"] == B.GENERATOR_VERSION


@pytest.mark.parametrize("bid", IDS)
def test_exactly_one_granularity_prior(bid):
    board = _load(bid)
    gran = [e for e in board["principle_registry"]
            if isinstance(e.get("compiled_rule"), dict)
            and e["compiled_rule"].get("kind") == "partition_granularity"]
    assert len(board["principle_registry"]) == 1
    assert len(gran) == 1
    schema_loader.validate(gran[0], _PRINCIPLE_SCHEMA,
                           schema_loader.default_registry(), "")
    view = dict(gran[0])
    view.pop("source_hash")
    assert gran[0]["source_hash"] == canonical.canonical_sha256(view)
    want_gap = B.MIN_GAP_BY_DIFFICULTY[SPECS[bid]["difficulty"]]
    assert gran[0]["compiled_rule"]["params"]["min_gap_mm"] == want_gap


@pytest.mark.parametrize("bid", IDS)
def test_hard_rules_and_stackup(bid):
    board = _load(bid)
    assert set(board["hard_rules"]) == {"R1", "R2", "R3", "R4", "R5", "R6"}
    assert board["hard_rules"]["R5"]["min_clearance_mm"] == 0.5
    layers = board["stackup"]
    assert len(layers) == SPECS[bid]["layers"]
    assert all(l["kind"] == "signal" and l["available"] is True
               for l in layers)
    ids = [l["id"] for l in layers]
    assert len(ids) == len(set(ids))
    ws = board["workspace"]
    assert (ws["x_max"], ws["y_max"]) == SPECS[bid]["size_mm"]


# ------------------------------------------------ 3. sidecar 与矩阵一致

@pytest.mark.parametrize("bid", IDS)
def test_sidecar_knobs_match_matrix(bid):
    sc = _sidecar(bid)
    spec = SPECS[bid]
    assert sc["board_id"] == bid
    assert sc["difficulty"] == spec["difficulty"]
    assert sc["routable"] == spec["routable"]
    k = sc["knobs"]
    assert k["workspace_mm"]["x"] == spec["size_mm"][0]
    assert k["workspace_mm"]["y"] == spec["size_mm"][1]
    assert k["layers"] == spec["layers"]
    assert k["net_count"] == spec["nets"]
    assert k["pad_layout_mode"] == spec["mode"]
    assert k["obstacle_density"] == spec["difficulty"]
    assert k["via_budget"] == spec["via_budget"]
    assert k["seed"] == spec["seed"]
    assert sc["guarantee_type"] == ("constructed-routable" if spec["routable"]
                                    else
                                    "constructed-block:all-layer-pad-seal")
    assert sc["guarantee_check"]["all_passed"] is True
    assert sc["provenance"]["board_sha256"] == \
        _load(bid)["provenance"]["board_sha256"]


@pytest.mark.parametrize("bid", IDS)
def test_sidecar_placed_counts(bid):
    sc = _sidecar(bid)
    board = _load(bid)
    normal = len(board["nets"]) - (0 if SPECS[bid]["routable"] else 2)
    assert sc["placed"]["n_nets_normal"] == SPECS[bid]["nets"] == normal
    assert sc["placed"]["n_keepouts_placed"] == len(board["zones"])
    assert sc["placed"]["n_holes_placed"] == len(board.get("holes", []))
    via_n = sum(1 for p in sc["witness"].get("reference_paths", [])
                if p.get("via"))
    if SPECS[bid]["routable"]:
        assert via_n == min(SPECS[bid]["via_budget"], SPECS[bid]["nets"])


# ------------------------------------------------ 4. 可布性 witness 独立重算

def _seg_seg_dist(a1, a2, b1, b2):
    def pt_seg(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        dd = dx * dx + dy * dy
        if dd <= 0:
            return math.hypot(p[0] - a[0], p[1] - a[1])
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / dd))
        return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))
    return min(pt_seg(a1, b1, b2), pt_seg(a2, b1, b2),
               pt_seg(b1, a1, a2), pt_seg(b2, a1, a2))


def _pt_rect_dist(p, r):
    dx = max(r["x_min"] - p[0], 0.0, p[0] - r["x_max"])
    dy = max(r["y_min"] - p[1], 0.0, p[1] - r["y_max"])
    return math.hypot(dx, dy)


@pytest.mark.parametrize("bid", ROUTABLE)
def test_routable_witness_geometry(bid):
    """witness 联合解自查（独立重算，不信任生成器内部状态）。"""
    sc = _sidecar(bid)
    board = _load(bid)
    paths = sc["witness"]["reference_paths"]
    assert len(paths) == SPECS[bid]["nets"]
    layer_ids = {l["id"] for l in board["stackup"]}
    for p in paths:
        for seg in p["segments"]:
            assert seg["layer"] in layer_ids
            for pt in seg["polyline"]:
                assert abs(pt[0] * 4 - round(pt[0] * 4)) < 1e-9   # 0.25 栅格
                assert abs(pt[1] * 4 - round(pt[1] * 4)) < 1e-9
        # witness 端点 == 板分区端点
        part = next(x for x in board["partitions"]
                    if x["partition_id"] == p["partition_id"])
        assert [list(x) for x in part["geometry"]["endpoints"]] == \
            p["endpoints"]
    # 同层 witness 段两两 ≥ LANE_SEP（只对**异网**对——同一路径的两条腿共享
    # 拐点属同网铜，引擎 R5 对同网豁免）
    flat = []
    for idx_p, p in enumerate(paths):
        for s in p["segments"]:
            flat.append((idx_p, s["polyline"], s["layer"]))
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            pi, pa, la = flat[i]
            pj, pb, lb = flat[j]
            if pi == pj or la != lb:
                continue
            for k in range(len(pa) - 1):
                for m in range(len(pb) - 1):
                    d = _seg_seg_dist(pa[k], pa[k + 1], pb[m], pb[m + 1])
                    assert d >= B.LANE_SEP_MM - 1e-9, \
                        "%s 同层 witness 段距 %.4f < %.2f" % (
                            bid, d, B.LANE_SEP_MM)
    # 障碍净空（keepout: ≥ 难度 clear；hole: ≥ clear + r + 带宽核算；
    # 采样复核——生成器 G2/G3 已做精确自查，此处独立抽样对账）
    clear = sc["engine_facts"]["obstacle_clear_mm"]
    for z in board["zones"]:
        r = z["rect"]
        for _pi, poly, _l in flat:
            for k in range(len(poly) - 1):
                a, b2 = poly[k], poly[k + 1]
                for t in range(0, 101, 5):
                    p = (a[0] + (b2[0] - a[0]) * t / 100.0,
                         a[1] + (b2[1] - a[1]) * t / 100.0)
                    assert _pt_rect_dist(p, r) >= clear - 0.02, \
                        "%s keepout %s 贴 witness" % (bid, z["zone_id"])
    for h in board.get("holes", []):
        c, r = h["pos_mm"], h["drill_mm"] / 2.0
        for _pi, poly, _l in flat:
            for k in range(len(poly) - 1):
                a, b2 = poly[k], poly[k + 1]
                for t in range(0, 101, 10):
                    p = (a[0] + (b2[0] - a[0]) * t / 100.0,
                         a[1] + (b2[1] - a[1]) * t / 100.0)
                    assert math.hypot(p[0] - c[0], p[1] - c[1]) - r \
                        >= clear + 0.25 + 0.1 - 0.05


@pytest.mark.parametrize("bid", UNROUTABLE)
def test_unroutable_seal_geometry(bid):
    """密封构造自查：all-layer 垫盖住逃逸界、端点对位、他网净空。"""
    sc = _sidecar(bid)
    board = _load(bid)
    seal = sc["witness"]["seal"]
    half = seal["seal_half_mm"]
    assert half == SPECS[bid]["seal"]["half_mm"]
    assert half >= B.ESCAPE_REACH_MM + B.SNAP_BOUND_MM + 0.25
    # 密封分区形状：退化端点 + 两枚 all-layer rect 垫
    ps = next(p for p in board["partitions"] if p["partition_id"] == "PSEAL")
    ends = ps["geometry"]["endpoints"]
    assert ends[0] == ends[1] == seal["center_mm"]
    pads = ps["geometry"]["pad_terminals"]
    assert len(pads) == 2
    for pad in pads:
        assert pad["layers"] == "all" and pad["shape"] == "rect"
        assert pad["size_mm"] == [2.0 * half, 2.0 * half]
    net_names = {n["net_id"] for n in board["nets"]}
    assert {"NBLK", "NSEAL"} <= net_names
    # 封锁目标网端点对位（端点 k = 密封心）
    pb = next(p for p in board["partitions"] if p["partition_id"] == "PBLK")
    k = sc["witness"]["blocked_endpoint_index"]
    assert pb["geometry"]["endpoints"][k] == seal["center_mm"]
    far = pb["geometry"]["endpoints"][1 - k]
    assert math.hypot(far[0] - seal["center_mm"][0],
                      far[1] - seal["center_mm"][1]) >= half + 1.5 - 1e-9
    # 他网 witness 路径 ≥ 0.75 离密封矩形
    r = (seal["center_mm"][0] - half, seal["center_mm"][1] - half,
         seal["center_mm"][0] + half, seal["center_mm"][1] + half)
    for p in sc["witness"]["other_nets_reference_paths"]:
        for s in p["segments"]:
            for pt in s["polyline"]:
                d = max(r[0] - pt[0], pt[0] - r[2], 0.0) ** 2 + \
                    max(r[1] - pt[1], pt[1] - r[3], 0.0) ** 2
                assert math.sqrt(d) >= 0.75 - 1e-9
    assert sc["witness"]["blocked_net"] == "NBLK"
    assert sc["witness"]["seal"]["net"] == "NSEAL"


# ------------------------------------------------ 5. 确定性与依赖纪律

def test_builder_double_run_same_bytes(tmp_path):
    d1 = os.path.join(str(tmp_path), "a")
    d2 = os.path.join(str(tmp_path), "b")
    B.build_all(d1)
    B.build_all(d2)
    for bid in IDS:
        with open(os.path.join(d1, "%s.board.v1.json" % bid), "rb") as f:
            a = f.read()
        with open(os.path.join(d2, "%s.board.v1.json" % bid), "rb") as f:
            b2 = f.read()
        with open(_path(bid), "rb") as f:
            committed = f.read()
        assert a == b2 == committed   # 双跑同字节 + 与在库文件零 diff


def test_builder_dependency_discipline():
    with open(B._SCRIPT_PATH, encoding="utf-8") as f:
        src = f.read()
    imports = set()
    for m in re.finditer(r"^\s*from\s+([\w\.]+)\s+import\s+([^\n#]+)", src, re.M):
        mod = m.group(1)
        names = [t.strip().split(" as ")[0].strip()
                 for t in m.group(2).strip().split(",") if t.strip()]
        if mod == "v5":
            imports.update("v5." + n for n in names)
        else:
            imports.add(mod)
    for line in src.splitlines():
        line = line.strip()
        if line.startswith("import "):
            for tok in line[len("import "):].split(","):
                tok = tok.strip().split(" as ")[0].strip()
                if tok:
                    imports.add(tok)
    assert imports <= _ALLOWED_IMPORTS, "白名单外 import: %s" % (
        imports - _ALLOWED_IMPORTS)
    # 禁引扫描只看 import 语句行（docstring 里的说明文字不算引用）
    import_lines = [ln for ln in src.splitlines()
                    if re.match(r"^\s*(import|from)\s", ln)]
    for banned in ("tests", "build_demo_boards", "build_adversarial_boards",
                   "build_upgrade4_boards"):
        assert not any(banned in ln for ln in import_lines), \
            "禁引用 %s" % banned
    assert "time.strftime" not in src and "datetime" not in src


# ------------------------------------------------ 6. compile 面（允许）

@pytest.mark.parametrize("bid", IDS)
def test_compile_face(bid):
    """compile 面全链（partition/compile/conflicts/pkg）+ compile 双跑字节等。
    不跑 plan_candidates/execute（W2 属 PREREG 冻结后）。"""
    from v5.compiler import compile_board
    from v5.overlay import build_conflicts, validate_conflicts_artifact
    from v5.pkg import build_pkg, validate_pkg
    from v5.partition import build_partition_artifact
    board = _load(bid)
    p_art = build_partition_artifact(board)
    c1, _ = compile_board(board)
    c2, _ = compile_board(board)
    assert canonical.canonical_json(c1) == canonical.canonical_json(c2)
    assert c1["coverage"]["coverage_pct"] == 100.0
    cf = build_conflicts(board)
    validate_conflicts_artifact(cf)
    pkg = build_pkg(board, p_art, cf)
    validate_pkg(pkg)
