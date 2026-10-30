# -*- coding: utf-8 -*-
"""Lane-QA 波1 夹具增补测试（主审裁定 D-1 采纳件；canvas/tests 面新建，零回写既有件）。

消费形态：
- 板源=canvas/tests/fixtures/qa-drc/<board>/（KiCad qa/tests/pcbnew/drc 夹具板副本，
  provenance=fixtures/qa-drc/MANIFEST.json：源仓库/pinned commit/逐文件 sha256/
  GPL run-only 声明/期望值断言源文件与行号）。
- 画板侧判定=车道域提取器（out/canvas-toolchain/qa-drc-lane/kicad_pcb_extract.py，
  .kicad_pcb→铜件/孔/工作区/禁布区）+ v5.drc 同源函数族（import 只读）。
- 断言口径（D-1 三条）：v5.drc 声明建模面内=逐违例对账 PASS 断言；
  KiCad 特有族/几何面（表达式规则引擎、net-tie 豁免、非矩形轮廓）=面外披露分离断言；
  与 kicad-cli 实跑的交集一致性（subset 板，cli 在场才跑，缺场 fail-closed 跳过并注明）。
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_FIX = os.path.join(_HERE, "fixtures", "qa-drc")
_LANE = os.path.normpath(os.path.join(
    _HERE, "..", "..", "out", "canvas-toolchain", "qa-drc-lane"))
for _p in (os.path.normpath(os.path.join(_HERE, "..", "..")), _LANE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import kicad_pcb_extract as _kpe      # 车道域提取器（Lane-QA 新建件，位于未公开的 out/ 证据目录）
except ImportError:                       # public archive: extractor + GPL fixtures not shipped
    pytest.skip("needs unpublished evidence: out/canvas-toolchain/qa-drc-lane + KiCad QA boards",
                allow_module_level=True)
import v5.drc as vdrc                      # 画板侧 DRC 权威（只读 import）

KICAD_CLI = r"F:/kicad/bin/kicad-cli.exe"

_BOARDS = [
    "drc_arc_arc_edge_clearance", "issue12609", "issue14008", "issue18203",
    "issue18839", "issue22267", "issue23469", "issue24355",
    "keepout_disallow", "multinetclasses_drc",
]

_CACHE = {}


def board_ext(name):
    """夹具板提取（共享缓存；.kicad_pcb→铜件/孔/工作区/禁布区，mm）。"""
    if name not in _CACHE:
        d = os.path.join(_FIX, name)
        _CACHE[name] = _kpe.extract(
            os.path.join(d, name + ".kicad_pcb"),
            os.path.join(d, name + ".kicad_pro"),
            os.path.join(d, name + ".kicad_dru"))
    return _CACHE[name]


def v5_run(name):
    """v5.drc 同源函数族画板侧判定（与车道 reconcile.v5_arm 同式重算，只读单源函数）。"""
    import reconcile as _rc        # 车道域三方对账 harness
    return _rc.v5_arm(board_ext(name))


def expectation(name):
    with open(os.path.join(_FIX, "expectations", name + ".json"),
              encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- 完整性

def test_fixture_manifest_sha256_integrity():
    """provenance manifest 逐文件 sha256 与夹具实体逐位一致（GPL run-only 钉值）。"""
    with open(os.path.join(_FIX, "MANIFEST.json"), encoding="utf-8") as f:
        man = json.load(f)
    assert man["pinned_commit"] == "3d83cce19567965def8a8397381f067e1a2e77ff"
    assert len(man["boards_passing_precheck"]) == 10
    assert set(man["boards_excluded_precheck"][0]) >= {"board", "reason_code"}
    assert len(man["files"]) >= 30
    for rel, meta in man["files"].items():
        p = os.path.join(_FIX, *rel.split("/"))
        assert os.path.isfile(p), rel
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        assert h == meta["sha256"], "sha256 漂移: %s" % rel


def test_expectation_provenance_lines_present():
    """每板期望值断言带源文件与行号（数据事实引用可回溯）。"""
    with open(os.path.join(_FIX, "MANIFEST.json"), encoding="utf-8") as f:
        man = json.load(f)
    for b, src in man["expectation_sources"].items():
        assert src["source_file"].startswith("qa/tests/pcbnew/drc/test_"), b
        assert src["assertions"], b
        for a in src["assertions"]:
            assert a["lines"] and a["quote"], (b, a)


# ---------------------------------------------------------------- 面内对账（强断言）

def test_keepout_disallow_r6_three_way_exact():
    """R6 禁布族三方全等：cpp 期望 3（2 via+1 track）/ kicad-cli / v5.drc。"""
    ext = board_ext("keepout_disallow")
    v5 = v5_run("keepout_disallow")
    # v5：keepout 域 (15,5)-(35,35) F.Cu+B.Cu；track(5,10)-(30,10) 与两 via 入域
    assert v5["families"]["keepout_allowed_items"] == 3
    kind_of = {c["cid"]: ("track" if c["kind"] in ("track_seg", "track_arc")
                          else c["kind"]) for c in ext["coppers"]}
    seen = set()
    for d in v5["details"]:
        if d.get("rule") == "R6":
            seen.add(kind_of.get(d["subjects"][0]))
    assert seen == {"track", "via"}
    exp = expectation("keepout_disallow")
    assert exp["assertions"][2]["expect"]["count"] == 3


def test_keepout_disallow_cli_intersection():
    """交集一致性：kicad-cli 实跑 items_not_allowed==3 且 2 via+1 track（uuid→kind）。"""
    if not os.path.isfile(KICAD_CLI):
        pytest.skip("kicad-cli 不在场（fail-closed 跳过，非静默改道）")
    d = os.path.join(_FIX, "keepout_disallow")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "r.json")
        r = subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json",
                            "--severity-all", "--units", "mm", "-o", out,
                            os.path.join(d, "keepout_disallow.kicad_pcb")],
                           capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stderr[-300:]
        data = json.load(open(out, encoding="utf-8"))
    hits = [v for v in data["violations"] if v["type"] == "items_not_allowed"]
    assert len(hits) == 3
    ext = board_ext("keepout_disallow")
    kind_of = {c["cid"]: ("track" if c["kind"] in ("track_seg", "track_arc")
                          else c["kind"]) for c in ext["coppers"]}
    kinds = [kind_of.get(v["items"][0]["uuid"]) for v in hits]
    assert sorted(k for k in kinds if k) == ["track", "via", "via"]


def test_issue24355_hole_clearance_pair():
    """孔-铜族：cpp 期望 2（逐层）/ v5 hole 谓词族 2（F.Cu+B.Cu 铜盘层复制）。"""
    v5 = v5_run("issue24355")
    assert v5["families"]["hole_clearance"] == 2
    # 几何事实：NPTH 孔 r=1.0 @(150,100) vs pad1 铜盘 r=0.5 @(151.6,100)，
    # gap=0.1 < 板声明 min_hole_clearance=0.25 → 两层各一
    layers = {d["pair"]["layer"] for d in v5["details"]
              if d.get("rule") == "hole_clearance"}
    assert layers == {"F.Cu", "B.Cu"}
    assert v5["margins"]["hole_clearance_mm"] == 0.25


def test_issue22267_hole_to_hole_board_value():
    """孔-孔族：板声明 min_hole_to_hole=0.4301 传入同源函数，期望 ≥1 对。"""
    v5 = v5_run("issue22267")
    assert v5["margins"]["hole_to_hole_mm"] == pytest.approx(0.4301)
    assert v5["families"]["hole_to_hole_pairs"] >= 1


def test_issue23469_phase2_j1_edge_default_margin():
    """phase2（无 dru=板缺省口径）：J1 焊盘入 0.5mm 边距带 → v5 判 >0（cpp REQUIRE_GT 同向）。"""
    ext = board_ext("issue23469")
    v5 = v5_run("issue23469")
    assert v5["margins"]["edge_clearance_mm"] == 0.5
    j1_hits = [d for d in v5["details"]
               if d.get("rule") == "edge_clearance"
               and str(d.get("subjects", [""])[0]).startswith("pad:J1")]
    assert len(j1_hits) > 0
    # 违例点均落在底边禁布带（y > 125-0.5）
    assert all(p[1] > 124.5 for p in (d["data"]["pos"] for d in j1_hits))
    # 仅 SH 屏蔽焊盘（连接器底部）涉入——A/B 排焊盘远离板边
    assert {d["subjects"][0].split(".")[1] for d in j1_hits} == {"SH"}


def test_issue12609_in_scope_zero_and_nettie_disclosure():
    """回归板期望 0：v5 声明面内除 net-tie 豁免族外全 0；net-tie 对=面外披露（分离断言）。"""
    v5 = v5_run("issue12609")
    ext = board_ext("issue12609")
    ref_of = {c["cid"]: c.get("ref") for c in ext["coppers"]}
    r5 = [d for d in v5["details"] if d.get("rule") == "R5"]
    # 唯一残余=NetTie 短接铜（KiCad 连接性豁免=v5 无此面，面外披露不算败）
    assert len(r5) == 4
    assert all(ref_of.get(d["subjects"][0]) == "TW3"
               or ref_of.get(d["subjects"][1]) == "TW3" for d in r5)
    raw = open(os.path.join(_FIX, "issue12609", "issue12609.kicad_pcb"),
               encoding="utf-8").read()
    tw3_blk = raw.split('fp_text reference "TW3"')[0].rsplit("(footprint ", 1)[-1]
    assert "NetTie" in tw3_blk
    # 其余面内族全 0（与 cpp 期望 total_error==0 的面内子集一致）
    for fam in ("track_width", "edge_clearance", "hole_to_hole_pairs", "hole_clearance"):
        assert v5["families"].get(fam, 0) == 0, fam


def test_issue14008_and_issue18203_in_scope_zero():
    """回归板期望 0：net-tie 板与弧-圆板，v5 面内全 0。"""
    for name in ("issue14008", "issue18203"):
        v5 = v5_run(name)
        for fam in ("clearance", "track_width", "edge_clearance",
                    "hole_to_hole_pairs", "hole_clearance",
                    "keepout_allowed_items"):
            assert v5["families"].get(fam, 0) == 0, (name, fam)


# ---------------------------------------------------------------- 面外披露分离断言

def test_issue18839_arc_outline_out_of_scope_disclosure():
    """同心弧板边=圆弧轮廓：v5 矩形轮廓唯一源 → edge 族面外；面内族（R5/hole）=0。"""
    v5 = v5_run("issue18839")
    assert v5["margins"]["edge_clearance_mm"] == 0.254      # 板声明值传入
    # 弧轮廓使矩形模型在 edge 族产生伪迹计数（披露项，非败）
    assert v5["families"]["edge_clearance"] > 0
    assert v5["families"]["clearance"] == 0
    assert v5["families"]["hole_to_hole_pairs"] == 0
    assert v5["families"]["hole_clearance"] == 0


def test_drc_arc_arc_cutout_out_of_scope_disclosure():
    """Edge.Cuts 圆弧 cutout：v5 矩形轮廓建模不了内切轮廓 → v5 edge=0（模型盲区披露）。"""
    v5 = v5_run("drc_arc_arc_edge_clearance")
    assert v5["families"]["edge_clearance"] == 0            # 盲区（cli=1 为真值）
    for fam in ("clearance", "track_width", "hole_to_hole_pairs", "hole_clearance"):
        assert v5["families"].get(fam, 0) == 0, fam
    # 期望值源：cpp BOOST_CHECK_GE(edgeViolations.size(), 1u)——由 cli 侧对账
    exp = expectation("drc_arc_arc_edge_clearance")
    assert exp["assertions"][0]["expect"] == {
        "family": "edge_clearance", "op": ">=", "count": 1}


def test_multinetclasses_r1_min_semantics_vs_dru_max():
    """v5 R1=最小线宽语义：本板面内 0；期望 2=dru track_width(max) 表达式规则（面外）。"""
    v5 = v5_run("multinetclasses_drc")
    for fam in ("clearance", "track_width", "edge_clearance",
                "hole_to_hole_pairs", "hole_clearance"):
        assert v5["families"].get(fam, 0) == 0, fam
    exp = expectation("multinetclasses_drc")
    assert exp["assertions"][0]["expect"]["count"] == 2
    assert "dru" in exp["family_note"]          # 面外披露在期望件中留痕


def test_issue23469_phase1_dru_expression_out_of_scope():
    """phase1 期望 0 依赖 .kicad_dru 表达式规则引擎（A.Reference 豁免）——v5 无此面，
    分离断言：v5 在板缺省口径下 J1 计数 >0（即非静默、差异可归因）。"""
    v5 = v5_run("issue23469")
    j1_edge = [d for d in v5["details"]
               if d.get("rule") == "edge_clearance"
               and str(d.get("subjects", [""])[0]).startswith("pad:J1")]
    j1_hole = [d for d in v5["details"]
               if d.get("rule") == "hole_clearance"
               and d.get("pair", {}).get("hole_ref") == "J1"
               and d.get("pair", {}).get("copper_ref") == "J1"]
    assert len(j1_edge) > 0 and len(j1_hole) > 0
    dru = os.path.join(_FIX, "issue23469", "issue23469.kicad_dru")
    assert os.path.isfile(dru)
    assert "A.Reference == 'J1'" in open(dru, encoding="utf-8").read()


# ---------------------------------------------------------------- cli 交集一致性（subset）

@pytest.mark.parametrize("board,family,v5_count", [
    ("issue24355", "hole_clearance", 2),
    ("issue22267", "hole_to_hole", 1),
])
def test_cli_intersection_consistency(board, family, v5_count):
    """kicad-cli 实跑与 v5 画板侧在声明面内族的交集一致性（在场性 fail-closed）。"""
    if not os.path.isfile(KICAD_CLI):
        pytest.skip("kicad-cli 不在场（fail-closed 跳过，非静默改道）")
    d = os.path.join(_FIX, board)
    pcb = os.path.join(d, board + ".kicad_pcb")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "r.json")
        r = subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json",
                            "--severity-all", "--units", "mm", "-o", out, pcb],
                           capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stderr[-300:]
        data = json.load(open(out, encoding="utf-8"))
    cli_hits = [v for v in data["violations"] if v["type"] == family]
    assert len(cli_hits) == v5_count, (board, family, len(cli_hits))
