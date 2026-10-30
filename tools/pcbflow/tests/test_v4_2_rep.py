"""A4-INTENTPACK-R1 packgen tests (PACK-SPEC-REP-R1.md v1 validator gates).

Checks the artifacts under out/v4.2-rep-r1/ (packs-b/, tasks-a/) against the
frozen spec §5/§7 and re-derives everything independently from the read-only
sources (board snapshots + incumbent re-solve + r1 tasks-calibration.json).

Run from the repo root (tools/pcbflow), PYTHONUTF8=1 per pytest.ini.
"""

import json
import os
import re

import pytest

from pcbflow import svg_route_package as srp
from pcbflow.v4_2.gt import incumbent_run
from pcbflow.v4_2.inspector import (_IDENTITY_RE, _JUDGE_SUFFIX,
                                    INSPECTOR_SYSTEM, assign_pids, blind,
                                    package_svg)
from pcbflow.v4_2_rep import packgen
from pcbflow.v4_2_rep.packgen import (FORBIDDEN_TOKENS, FROZEN_USER_BYTES,
                                      MAX_SEGMENTS, SEGMENT_CODES,
                                      USER_BYTE_LIMIT, parse_user_text,
                                      replay_occupancy)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(_ROOT, "out", "v4.2-rep-r1")
PACKS = os.path.join(OUT, "packs-b")
TASKS_A = os.path.join(OUT, "tasks-a")
PIDS = ["p%02d" % (i + 1) for i in range(16)]
SID_PATHS = packgen.scenario_sid_paths(_ROOT)
PIDS_OF = packgen.pid_assignment()


def _read_json(path):
    with open(path, "rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def solved():
    """One deterministic incumbent solve per board, shared by all tests."""
    out = {}
    for sid, path in SID_PATHS.items():
        board = packgen.load_board_snapshot(path)
        out[sid] = (board, incumbent_run(board))
    return out


@pytest.fixture(scope="module")
def packs():
    out = {}
    for pid in PIDS:
        raw = _read_json(os.path.join(PACKS, "%s.json" % pid))
        out[pid] = (raw, json.loads(raw.decode("utf-8")))
    return out


@pytest.fixture(scope="module")
def arm_a():
    out = {}
    for pid in PIDS:
        raw = _read_json(os.path.join(TASKS_A, "%s.json" % pid))
        out[pid] = (raw, json.loads(raw.decode("utf-8")))
    return out


# ------------------------------------------------ §7.1 inventory + shape

def test_artifact_inventory_and_top_keys(packs, arm_a):
    assert sorted(os.listdir(PACKS)) == sorted("%s.json" % p for p in PIDS)
    assert sorted(os.listdir(TASKS_A)) == sorted("%s.json" % p for p in PIDS)
    for pid in PIDS:
        assert sorted(packs[pid][1].keys()) == sorted(
            ["pid", "system", "user", "source_manifest_sha256",
             "source_board_sha256"]), pid
        assert sorted(arm_a[pid][1].keys()) == ["pid", "system", "user"], pid
        assert packs[pid][1]["pid"] == pid and arm_a[pid][1]["pid"] == pid


def test_b_system_is_frozen_pack_system(packs):
    for pid in PIDS:
        assert packs[pid][1]["system"] == packgen.PACK_SYSTEM, pid


# ------------------------------------- §7.1/§7.14 canonical JSON on disk

def test_canonical_json_no_wallclock(packs, arm_a):
    for pid in PIDS:
        for raw, obj in (packs[pid], arm_a[pid]):
            redump = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=False).encode("utf-8")
            assert raw == redump, pid
            lowered = raw.decode("utf-8").lower()
            for bad in ("timestamp", "wall_clock", "wallclock", "created_at",
                        "generated_at", "datetime"):
                assert bad not in lowered, (pid, bad)
            assert "c:\\\\users" not in lowered and "e:/" not in lowered


# ------------------------------- §7.3/§7.4 forbidden tokens + blinding

@pytest.mark.parametrize("pid", PIDS)
def test_forbidden_tokens_absent(pid, packs):
    """B packs only: the A arm is the frozen r2 SVG-form baseline and by
    design carries <svg>/viewBox/data-route-id (PREREG §1/§11.2 scopes the
    forbidden list to the B pack)."""
    obj = packs[pid][1]
    blob = obj["user"] + obj["system"]
    for tok in FORBIDDEN_TOKENS:
        assert tok not in blob, (pid, tok)


@pytest.mark.parametrize("pid", PIDS)
def test_blinding_clean_and_declarations_present(pid, packs):
    obj = packs[pid][1]
    for field in ("user", "system"):
        assert not _IDENTITY_RE.search(obj[field]), (pid, field)
    sid = packgen.verify_pid_sid(pid)
    board = packgen.load_board_snapshot(SID_PATHS[sid])
    blob = obj["user"] + obj["system"]
    for secret in (sid, str(board["family"]), str(board["seed"]),
                   str(board["split"]), str(board["label"])):
        assert secret not in blob, (pid, secret)
    for decl in ("y_axis=down-positive", "frame=board-mm", "cell=0.25mm",
                 "workspace_margin_mm=2.0",
                 "2.0 mm beyond the board outline"):
        assert decl in obj["user"], (pid, decl)


# --------------------------- §7.5/§7.14 bytes + segment count + ASCII

@pytest.mark.parametrize("pid", PIDS)
def test_user_bytes_match_frozen_table_and_budget(pid, packs):
    obj = packs[pid][1]
    n = len(obj["user"].encode("utf-8"))
    sid = packgen.verify_pid_sid(pid)
    assert n == FROZEN_USER_BYTES[sid], (pid, sid, n)
    assert n <= USER_BYTE_LIMIT
    assert obj["user"].isascii()


@pytest.mark.parametrize("pid", PIDS)
def test_segment_count_and_via_counts(pid, packs):
    facts = parse_user_text(packs[pid][1]["user"])
    assert facts["n_segments"] <= MAX_SEGMENTS
    sid = packgen.verify_pid_sid(pid)
    # frozen table's per-board segment/via counts (PACK-SPEC §5 table)
    expect_seg = {"cal-f12-01": 10, "cal-f12-02": 10, "cal-f12-03": 10,
                  "cal-f12-04": 10, "cal-f12-05": 7, "cal-f12-06": 8,
                  "cal-f12-07": 7, "cal-f12-08": 7, "hol-f6-01": 7,
                  "hol-f6-02": 4, "hol-f6-03": 6, "hol-f6-04": 4,
                  "hol-f8-01": 9, "hol-f8-02": 8, "hol-f8-03": 8,
                  "hol-f8-04": 8}
    expect_via = {"cal-f12-01": 4, "cal-f12-02": 4, "cal-f12-03": 4,
                  "cal-f12-04": 4, "cal-f12-05": 2, "cal-f12-06": 2,
                  "cal-f12-07": 2, "cal-f12-08": 2, "hol-f6-01": 2,
                  "hol-f6-02": 0, "hol-f6-03": 2, "hol-f6-04": 0,
                  "hol-f8-01": 2, "hol-f8-02": 2, "hol-f8-03": 2,
                  "hol-f8-04": 2}
    assert facts["n_segments"] == expect_seg[sid], (pid, sid)
    assert facts["n_vias"] == expect_via[sid], (pid, sid)


# --------------------------------- §7.2/§7.6 whitelist + RLE round-trip

@pytest.mark.parametrize("pid", PIDS)
def test_user_text_parses_within_whitelist(pid, packs):
    verify = packgen.verify_pack_text(packs[pid][1]["user"])
    assert verify["pid"] == pid


@pytest.mark.parametrize("pid", PIDS)
def test_rle_roundtrip_every_row(pid, packs):
    facts = parse_user_text(packs[pid][1]["user"])
    nx = facts["grid"]["nx"]
    for L in facts["layers"]:
        rows = facts["occupy"][L]
        assert len(rows) == facts["grid"]["ny"]
        for iy, row in enumerate(rows):
            assert len(row) == nx
            assert not (set(row) - set(".#P*" + SEGMENT_CODES))


def test_rle_codec_edges():
    assert packgen.rle_encode(list("...##**P")) == ".3#2*2P"
    assert packgen.rle_decode(".3#2*2P") == "...##**P"
    assert packgen.rle_encode(list("A")) == "A"
    assert packgen.rle_decode("A") == "A"
    # digit-run decoding: count = longest consecutive digit string
    assert packgen.rle_decode("A12.B") == "A" * 12 + "." + "B"
    # segment codes never collide with digits/I/O/P
    assert "I" not in SEGMENT_CODES and "O" not in SEGMENT_CODES
    assert "P" not in SEGMENT_CODES
    assert not any(c.isdigit() for c in SEGMENT_CODES)


# ---------------------- §7.7 occupancy replay from text facts

@pytest.mark.parametrize("pid", PIDS)
def test_occupancy_replay_from_text_facts(pid, packs):
    facts = parse_user_text(packs[pid][1]["user"])
    assert replay_occupancy(facts) == {L: [list(r) for r in facts["occupy"][L]]
                                       for L in facts["layers"]}


# ------------- independent from-board rasterization (test-local, §4.5)

def _rasterize_independently(board, run):
    """Second implementation of PACK-SPEC §4.5 (test-local; shares no code
    with packgen's builder) -> {layer: [row strings]}."""
    bbox = [float(v) for v in board["board"]["bbox_mm"]]
    layers = [str(s) for s in board["board"]["layers"]]
    cell = float(board["rules"]["grid_mm"])
    ox, oy = round(bbox[0] - 2.0, 10), round(bbox[1] - 2.0, 10)
    nx = int(round((bbox[2] - bbox[0] + 4.0) / cell))
    ny = int(round((bbox[3] - bbox[1] + 4.0) / cell))
    g = {L: [["."] * nx for _ in range(ny)] for L in layers}
    rts = sorted(str(r["route_id"]) for r in run["routes"])
    codes = "ABCDEFGHJKLMNQRSTUVWXYZ"
    assert len(rts) <= 23
    cmap = {r: codes[i] for i, r in enumerate(rts)}
    by = {str(r["route_id"]): r for r in run["routes"]}
    for rid in rts:
        r = by[rid]
        L = str(r["layer"])
        pts = [(int(round((p[0] - ox) / cell)), int(round((p[1] - oy) / cell)))
               for p in r["polyline_mm"]]
        assert all(abs((p[0] - ox) / cell - round((p[0] - ox) / cell)) < 1e-6
                   and abs((p[1] - oy) / cell - round((p[1] - oy) / cell)) < 1e-6
                   for p in r["polyline_mm"])
        walk = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            if b == walk[-1]:
                continue
            assert a[0] == b[0] or a[1] == b[1]
            if a[0] == b[0]:
                st = 1 if b[1] >= a[1] else -1
                walk += [(a[0], y) for y in range(a[1] + st, b[1] + st, st)]
            else:
                st = 1 if b[0] >= a[0] else -1
                walk += [(x, a[1]) for x in range(a[0] + st, b[0] + st, st)]
        if len(set(walk)) == 1:
            cells = walk
        else:
            cells = walk
        for (x, y) in cells:
            g[L][y][x] = cmap[rid]
    for v in run["vias"]:
        x = int(round((v["center_mm"][0] - ox) / cell))
        y = int(round((v["center_mm"][1] - oy) / cell))
        for L in (str(v["from_layer"]), str(v["to_layer"])):
            if g[L][y][x] == ".":
                g[L][y][x] = "*"
    def span(lo, hi, o, n):
        return [i for i in range(n)
                if o + i * cell >= lo - 1e-9 and o + i * cell <= hi + 1e-9]
    for k in board["keepouts"]:
        r = [float(v) for v in k["rect_mm"]]
        for L in (str(s) for s in k["layers"]):
            for ix in span(r[0], r[2], ox, nx):
                for iy in span(r[1], r[3], oy, ny):
                    if g[L][iy][ix] == ".":
                        g[L][iy][ix] = "#"
    for p in board["pads"]:
        L = str(p["layer"])
        for ix in span(float(p["x_mm"]) - float(p["w_mm"]) / 2.0,
                       float(p["x_mm"]) + float(p["w_mm"]) / 2.0, ox, nx):
            for iy in span(float(p["y_mm"]) - float(p["h_mm"]) / 2.0,
                           float(p["y_mm"]) + float(p["h_mm"]) / 2.0, oy, ny):
                if g[L][iy][ix] == ".":
                    g[L][iy][ix] = "P"
    def enc(row):
        out, prev, n = [], row[0], 1
        for c in row[1:]:
            if c == prev:
                n += 1
            else:
                out.append(prev + (str(n) if n >= 2 else ""))
                prev, n = c, 1
        out.append(prev + (str(n) if n >= 2 else ""))
        return "".join(out)
    return {L: [enc(g[L][iy]) for iy in range(ny)] for L in layers}


@pytest.mark.parametrize("pid", PIDS)
def test_occupancy_grid_matches_independent_rasterization(pid, packs, solved):
    sid = packgen.verify_pid_sid(pid)
    board, run = solved[sid]
    facts = parse_user_text(packs[pid][1]["user"])
    mine = _rasterize_independently(board, run)
    assert facts["layers"] == [str(s) for s in board["board"]["layers"]]
    for L in facts["layers"]:
        rows_text = facts["occupy"][L]
        # text rows are decoded chars; compare against independent decode
        for iy in range(facts["grid"]["ny"]):
            assert rows_text[iy] == packgen.rle_decode(mine[L][iy]), (pid, L, iy)


# ---------------------- hard gate 4: route sets B == A data-route-id

@pytest.mark.parametrize("pid", PIDS)
def test_route_set_equals_arm_a(pid, packs, arm_a, solved):
    a_user = arm_a[pid][1]["user"]
    a_routes = set(re.findall(r'data-route-id="([^"]+)"', a_user))
    facts = parse_user_text(packs[pid][1]["user"])
    b_routes = {s["rid"] for s in facts["segments"]}
    sid = packgen.verify_pid_sid(pid)
    run_routes = {str(r["route_id"]) for r in solved[sid][1]["routes"]}
    assert a_routes == b_routes == run_routes, pid


# ------------------------------ §7.9 anchor recompute + §7.10 A recheck

@pytest.mark.parametrize("pid", PIDS)
def test_anchors_recompute_and_arm_a_byte_identity(pid, packs, arm_a, solved):
    sid = packgen.verify_pid_sid(pid)
    board, run = solved[sid]
    obj = packs[pid][1]
    assert obj["source_board_sha256"] == srp._sha256_of(board), pid
    svg, manifest = srp.build(
        board, {"routes": packgen._enriched_routes(board, run),
                "vias": run["vias"]})
    assert svg == package_svg(board, run)          # enrichment mirror intact
    assert obj["source_manifest_sha256"] == manifest["manifest_payload_sha256"]
    a = arm_a[pid][1]
    assert a["system"] == INSPECTOR_SYSTEM
    assert a["user"] == blind(svg, sid, pid) + "\n" + _JUDGE_SUFFIX, pid
    m = re.search(r'data-route-manifest-sha256="([0-9a-f]+)"', a["user"])
    assert m and m.group(1) == manifest["manifest_payload_sha256"]
    b = re.search(r'data-board-snapshot-sha256="([0-9a-f]+)"', a["user"])
    assert b and b.group(1) == obj["source_board_sha256"]


def test_arm_a_extraction_fidelity():
    src = packgen.arm_a_tasks(_ROOT)
    assert sorted(src.keys()) == PIDS
    for pid in PIDS:
        raw = _read_json(os.path.join(TASKS_A, "%s.json" % pid))
        obj = json.loads(raw.decode("utf-8"))
        assert sorted(obj.keys()) == ["pid", "system", "user"]
        assert obj["system"] == src[pid]["system"]
        assert obj["user"] == src[pid]["user"]
        # sid key stripped and the sid value never appears in the file
        sid = packgen.verify_pid_sid(pid)
        text = raw.decode("utf-8")
        assert sid not in text
        assert '"sid"' not in text


# ------------------------------------- §7.8 determinism (double solve)

@pytest.mark.parametrize("sid", sorted(SID_PATHS.keys()))
def test_determinism_double_run(sid):
    board = packgen.load_board_snapshot(SID_PATHS[sid])
    pid = PIDS_OF[sid]
    run1 = incumbent_run(board)
    run2 = incumbent_run(board)
    user1 = packgen.build_user_text(board, run1, pid)
    user2 = packgen.build_user_text(board, run2, pid)
    on_disk = json.loads(_read_json(
        os.path.join(PACKS, "%s.json" % pid)).decode("utf-8"))["user"]
    assert user1 == user2 == on_disk, sid
    _, svg1, man1 = packgen.build_pack(board, run1, pid)
    _, svg2, man2 = packgen.build_pack(board, run2, pid)
    assert svg1 == svg2
    assert man1["manifest_payload_sha256"] == man2["manifest_payload_sha256"]


# ------------------------------------- §7.13 id set gates + §4.15 shape

@pytest.mark.parametrize("pid", PIDS)
def test_id_sets_and_shapes(pid, packs, solved):
    sid = packgen.verify_pid_sid(pid)
    board, run = solved[sid]
    facts = parse_user_text(packs[pid][1]["user"])
    assert {s["rid"] for s in facts["segments"]} == \
        {str(r["route_id"]) for r in run["routes"]}
    assert {p["pad_id"] for p in facts["pads"]} == \
        {str(p["pad_id"]) for p in board["pads"]}
    assert {n["net_id"] for n in facts["nets"]} == \
        {str(n["net_id"]) for n in board["nets"]}
    assert {k["kid"] for k in facts["keepouts"]} == \
        {str(k["keepout_id"]) for k in board["keepouts"]}
    assert {v["via_id"] for v in facts["vias"]} == \
        {str(v["via_id"]) for v in run["vias"]}
    shape = re.compile(r"^[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*$")
    ids = ([s["rid"] for s in facts["segments"]]
           + [p["pad_id"] for p in facts["pads"]]
           + [n["net_id"] for n in facts["nets"]]
           + [k["kid"] for k in facts["keepouts"]]
           + [v["via_id"] for v in facts["vias"]])
    assert all(shape.match(i) for i in ids), pid


# ----------------------------- §7.11 GT/meta readiness (keys only)

def test_gt_meta_readiness():
    gt = json.load(open(os.path.join(_ROOT, "out", "v4.2-seat", "m1",
                                     "gt.json"), encoding="utf-8"))
    assert set(gt["scenarios"].keys()) == set(SID_PATHS.keys())
    meta = json.load(open(os.path.join(_ROOT, "out", "v4.2-seat", "m1",
                                       "packages", "package-meta.json"),
                          encoding="utf-8"))
    assert set(meta.keys()) == set(PIDS)
    assert assign_pids(sorted(SID_PATHS.keys())) == PIDS_OF
    for pid in PIDS:
        assert meta[pid]["sid"] == packgen.verify_pid_sid(pid)


# ------------------------------------- verify report sanity

def test_packgen_verify_report_on_disk():
    report = json.load(open(os.path.join(OUT, "packgen-verify.json"),
                            encoding="utf-8"))
    assert report["n_packs"] == 16
    assert report["gates_all_passed"] is True
    assert sorted(report["per_pid"].keys()) == PIDS
    low = json.dumps(report).lower()
    for bad in ("timestamp", "wall_clock", "wallclock", "created_at"):
        assert bad not in low
