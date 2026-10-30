"""TL-5 第二包：真实板转换（corpus_convert）测试——纯函数+真实数据集回放。

覆盖：KiCad5 解析（无引号网名/空网/裸 token）、规范化板确定性 byte-exact、
约定表推导边界（不虚构）、构件 schema 合规（profile/manifest）、graph
六件套+盘上对账、conversion_log 合同、真实 bm1/bm11 分母与拓扑分组。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import artifact_graph, corpus_convert as cc, hashing, manifest
from pcbflow import v3cli

RAW = os.path.join("datasets", "pcbbenchmarks-r1", "raw")

#: 最小 KiCad5 合成板（覆盖：无引号网名 +5V/N$6、空网 0、引号空串、
#: 旋转 at、无旋转 at、thru_hole/smd、无 net 焊盘、图形丢弃项）
SYNTH_BOARD = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.4-0-10_14)")

  (general
    (thickness 1.6)
    (drawings 9)
    (tracks 0)
    (zones 0)
    (modules 3)
    (nets 6)
  )

  (page A4)
  (layers
    (0 Top signal)
    (31 Bottom signal)
    (36 B.SilkS user)
    (44 Edge.Cuts user)
  )

  (setup
    (last_trace_width 0.25)
    (trace_clearance 0.2)
    (trace_min 0.2)
    (via_size 0.8)
    (via_drill 0.4)
    (via_min_size 0.4)
    (via_min_drill 0.3)
  )

  (net 0 "")
  (net 1 +5V)
  (net 2 GND)
  (net 3 D+)
  (net 4 D-)
  (net 5 N$6)

  (module Lib:A (layer Top) (tedit 5DD86010) (tstamp 5DD86102)
    (at 10.0 20.0 90)
    (fp_text reference U1 (at 0 -2.54 90) (layer F.SilkS)
      (effects (font (size 1.27 1.27) (thickness 0.15))))
    (fp_poly (pts (xy -6 -8.29) (xy 6 -8.29)) (layer F.CrtYd) (width 0.1))
    (pad 1 thru_hole circle (at 1.0 -5.25 90) (size 1.458 1.458) (drill 0.95) (layers *.Cu *.Mask)
      (net 2 GND))
    (pad 2 smd rect (at -1.0 -5.25) (size 0.3 0.6) (layers F.Cu)
      (net 1 +5V))
    (pad 3 smd rect (at 0.0 -7.25) (size 0.3 0.6) (layers F.Cu)
      (net 3 D+))
  )

  (module Lib:B (layer Bottom) (tedit 5DD86011)
    (at 30.5 40.25)
    (fp_text reference U2 (at 0 0) (layer B.SilkS))
    (pad 1 smd rect (at 0.0 0.0) (size 0.3 0.6) (layers B.Cu)
      (net 4 D-))
    (pad 2 thru_hole oval (at 2.0 0.0) (size 1.0 0.6) (drill 0.3) (layers *.Cu *.Mask)
      (net 5 N$6))
    (pad 3 smd rect (at 4.0 0.0) (size 0.3 0.6) (layers B.Cu)
      (net 1 +5V))
  )

  (module Lib:C (layer Top) (tedit 5DD86012)
    (at 50.0 60.0)
    (fp_text reference J1 (at 0 0) (layer F.SilkS))
    (pad 1 thru_hole circle (at 0.0 0.0) (size 1.5 1.5) (drill 1.0) (layers *.Cu *.Mask)
      (net 3 D+))
    (pad 2 thru_hole circle (at 2.5 0.0) (size 1.5 1.5) (drill 1.0) (layers *.Cu *.Mask)
      (net 4 D-))
    (pad 3 thru_hole circle (at 5.0 0.0) (size 1.5 1.5) (drill 1.0) (layers *.Cu *.Mask)
      (net 2 GND))
    (pad 4 thru_hole circle (at 7.5 0.0) (size 1.5 1.5) (drill 1.0) (layers *.Cu *.Mask)
      (net 5 N$6))
    (pad 5 thru_hole circle (at 10.0 0.0) (size 1.5 1.5) (drill 1.0) (layers *.Cu *.Mask))
  )
)
"""

SYNTH_ROUTED_EXTRA = """  (segment (start 10.0 20.0) (end 30.5 40.25) (width 0.25) (layer Top) (net 2))
  (via (at 12.0 22.0) (size 0.8) (drill 0.4) (layers Top Bottom) (net 2))
"""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _synth_model():
    return cc.parse_kicad5_board(SYNTH_BOARD)


def _synth_routed_model():
    text = SYNTH_BOARD.replace(
        "  (setup", SYNTH_ROUTED_EXTRA + "  (setup", 1)
    return cc.parse_kicad5_board(text)


# ---------------- 解析 ----------------

def test_parse_rejects_wrong_version():
    with pytest.raises(ValueError, match="board version"):
        cc.parse_kicad5_board(SYNTH_BOARD.replace("20171130", "20260901"))


def test_parse_nets_and_modules_and_pads():
    m = _synth_model()
    assert [n["name"] for n in m["nets"]] == [
        "", "+5V", "GND", "D+", "D-", "N$6"]
    assert [x["ref"] for x in m["modules"]] == ["J1", "U1", "U2"]
    d = cc.board_denominators(m)
    assert d == {"net_count": 6, "named_net_count": 5, "module_count": 3,
                 "pad_count": 11, "pad_thru_hole_count": 7,
                 "pad_smd_count": 4, "pad_without_net_count": 1,
                 "copper_layer_count": 2}
    u2 = next(x for x in m["modules"] if x["ref"] == "U2")
    assert u2["layer"] == "Bottom" and u2["at"] == ["30.5", "40.25"]
    u1 = next(x for x in m["modules"] if x["ref"] == "U1")
    assert u1["at"] == ["10.0", "20.0", "90"]
    pad3 = next(p for p in u1["pads"] if p["name"] == "3")
    assert pad3["net"] == {"net_id": 3, "name": "D+"}
    assert m["segment_count"] == 0 and m["via_count"] == 0
    assert [l["name"] for l in m["copper_layers"]] == ["Top", "Bottom"]


# ---------------- 规范化板：确定性 + 保真 ----------------

def test_normalized_board_byte_exact_deterministic():
    m = _synth_model()
    t1 = cc.normalized_board_text(
        m, source_path="datasets/x/b.unrouted.kicad_pcb",
        source_sha256=_sha(SYNTH_BOARD))
    t2 = cc.normalized_board_text(
        m, source_path="datasets/x/b.unrouted.kicad_pcb",
        source_sha256=_sha(SYNTH_BOARD))
    assert t1 == t2
    t3 = cc.normalized_board_text(
        m, source_path="datasets/x/b.unrouted.kicad_pcb",
        source_sha256="0" * 64)
    assert t1 != t3  # source hash 绑定参与文本


def test_normalized_board_requires_source_hash():
    with pytest.raises(ValueError):
        cc.normalized_board_text(_synth_model(),
                                 source_path="datasets/x/b.kicad_pcb",
                                 source_sha256="short")


def test_normalized_board_reparseable_and_drops_graphics():
    t = cc.normalized_board_text(
        _synth_model(), source_path="datasets/x/b.kicad_pcb",
        source_sha256=_sha(SYNTH_BOARD))
    assert "fp_poly" not in t and "fp_text" not in t
    assert "tedit" not in t and "effects" not in t
    # 网名带符号（+5V/D+）与 *.Cu 通配必须引号化且可重解析
    assert '"+5V"' in t and '"D+"' in t and '"*.Cu"' in t
    from pcbflow import sexpr_min
    reparsed = sexpr_min.parse(t)
    root = [n for n in reparsed
            if isinstance(n, list) and n and n[0] == "kicad_pcb"][0]
    nets = [c for c in root[1:] if isinstance(c, list) and c[0] == "net"]
    assert len(nets) == 6
    mods = sexpr_min.find_all(root, "footprint")
    assert len(mods) == 3
    pads = [p for mm in mods for p in sexpr_min.find_all(mm, "pad")]
    assert len(pads) == 11
    no_net = [p for p in pads if not sexpr_min.find_first(p, "net")]
    assert len(no_net) == 1


# ---------------- 约定表推导（不虚构） ----------------

def test_derive_critical_nets_convention_only():
    m = _synth_model()
    crit = cc.derive_critical_nets(m)
    assert crit["power_rails"] == ["+5V", "GND"]
    assert crit["diff_pairs"] == [["D+", "D-"]]
    assert crit["critical_nets"] == ["+5V", "D+", "D-", "GND"]
    assert "net_name_convention" in crit["basis"]
    # 不可判定清单非空且不含编造值
    assert crit["not_determinable_from_board_text"]


def test_constraints_no_fabricated_tolerances():
    crit = cc.derive_critical_nets(_synth_model())
    obj = cc.build_constraints_obj(_synth_model(), project_id="synth",
                                   crit=crit)
    assert len(obj["entries"]) == 1
    e = obj["entries"][0]
    assert e["kind"] == "diff_pair" and e["nets"] == ["D+", "D-"]
    assert "tolerance_mm" not in e  # 数值容差不可判定 → 不生成
    assert "length_match" in obj["not_generated"]
    assert "critical_net_return" in obj["not_generated"]


# ---------------- 构件：registry/audit/feedforward ----------------

def test_net_registry_counts_and_classification():
    m = _synth_model()
    crit = cc.derive_critical_nets(m)
    reg = cc.build_net_registry_obj(m, board_id="synth", crit=crit)
    assert reg["net_count"] == 6 and reg["named_net_count"] == 5
    by_name = {n["name"]: n for n in reg["nets"]}
    assert by_name["GND"]["classification"] == "power_rail"
    assert by_name["GND"]["member_refs"] == ["J1.3", "U1.1"]
    assert by_name["N$6"]["classification"] == "unnamed"
    assert by_name[""]["classification"] == "empty"
    assert by_name["D+"]["pad_count"] == 2


def test_audit_passes_pristine_and_fails_tampered():
    ok = cc.build_audit_obj(_synth_model(), _synth_model(), board_id="synth")
    assert ok["result"] == "pass"
    assert all(c["pass"] for c in ok["checks"])
    # routed 态加了 segment/via → unrouted pristine 仍 pass（检查的是 unrouted
    # 模型），同板身份检查仍 pass（网/封装相同）
    mixed = cc.build_audit_obj(_synth_model(), _synth_routed_model(),
                               board_id="synth")
    assert mixed["result"] == "pass"
    assert mixed["routed_reference"]["segment_count"] == 1
    assert mixed["routed_reference"]["via_count"] == 1
    # unrouted 非纯净（含 segment）→ fail
    bad = cc.build_audit_obj(_synth_routed_model(), _synth_model(),
                             board_id="synth")
    assert bad["result"] == "fail"
    assert any(c["id"] == "unrouted_state_pristine" and not c["pass"]
               for c in bad["checks"])
    # routed 与 unrouted 封装集不同 → 同板身份 fail
    tampered_r = json.loads(json.dumps(
        _synth_model()))  # 深拷贝
    tampered_r["modules"] = tampered_r["modules"][:-1]
    bad2 = cc.build_audit_obj(_synth_model(), tampered_r, board_id="synth")
    assert bad2["result"] == "fail"


def test_feedforward_rails_real_counts_only():
    m = _synth_model()
    crit = cc.derive_critical_nets(m)
    ff = cc.build_feedforward_obj(m, board_id="synth", crit=crit)
    rails = {r["net"]: r for r in ff["rails"]}
    assert rails["+5V"]["pad_count"] == 2
    assert rails["GND"]["member_refs"] == ["J1.3", "U1.1"]
    assert ff["not_modelled"]  # 电流预算等不可判定 → 显式不建模


# ---------------- topology / profile / manifest / graph ----------------

def test_topology_group_distinguishes_boards():
    m1 = _synth_model()
    m2 = json.loads(json.dumps(m1))
    m2["modules"].append(dict(m2["modules"][0], ref="U9"))
    c = cc.derive_critical_nets(m1)
    assert cc.topology_group_id(m1, c) != cc.topology_group_id(m2, c)


def test_profile_obj_schema_valid():
    m = _synth_model()
    prof = cc.build_profile_obj(m, profile_id="synth", project_id="synth",
                                crit=cc.derive_critical_nets(m))
    assert manifest.validate_profile(prof) == []
    assert prof["anchors"] == []  # 不可判定 → 显式留空
    assert prof["thresholds"]["min_track_width_mm"] == 0.2
    assert all(l["role"] == "signal" for l in prof["layers"])


def test_manifest_obj_schema_valid():
    mf = cc.build_manifest_obj(
        project_id="synth", profile_id="synth", eda_version="5.1.4",
        critical_nets=["GND"], dataset_splits={
            "train": ["bm1"], "validation": [], "holdout": ["bm11"],
            "external_eval": []},
        output_root="out/v3-tl5/mainpath/synth", board_id="bm1",
        dataset_routed_rel="../../datasets/pcbbenchmarks-r1/raw/bm1/"
                           "bm1.routed.kicad_pcb",
        drc_baseline_rel="../../out/v3-tl5/drc/bm1/bm1.routed.drc-all.json")
    assert manifest.validate_manifest(mf) == []
    assert mf["backtest"]["reference_route"].endswith("bm1.routed.kicad_pcb")
    assert mf["params"] == []


def test_graph_spec_clean_and_disk_reconciled(tmp_path, capsys):
    # 写 6 个真实文件（任意内容）→ 实算 hash → 图 spec → v3cli graph ok
    files = {
        "inputs/board.kicad_pcb": cc.normalized_board_text(
            _synth_model(), source_path="datasets/x/b.kicad_pcb",
            source_sha256=_sha(SYNTH_BOARD)),
        "inputs/stackup.json": cc.dumps_canonical(
            cc.build_stackup_obj(_synth_model(), board_id="synth",
                                 source={"path": "datasets/x/b.kicad_pcb",
                                         "sha256": _sha(SYNTH_BOARD)})),
        "inputs/constraints.json": cc.dumps_canonical(
            cc.build_constraints_obj(_synth_model(), project_id="synth",
                                     crit=cc.derive_critical_nets(
                                         _synth_model()))),
        "derived/net-registry.json": "…placeholder…",
        "derived/audit.json": "…placeholder…",
        "derived/feedforward-plan.json": "…placeholder…",
    }
    hashes = {}
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        hashes[rel] = hashing.sha256_file(str(p))
    spec = cc.build_graph_spec(project_id="synth", profile_id="synth",
                               revision="synth-r1", file_hashes=hashes)
    graph = artifact_graph.build_graph(
        [artifact_graph.make_node(
            n["artifact_id"], n["kind"], sha256=n["sha256"], path=n["path"],
            inputs=n["inputs"], status=n["status"], revision=n["revision"],
            stage_label=n["stage_label"]) for n in spec["nodes"]])
    report = artifact_graph.validate_graph(graph)
    assert report["acyclic"] and report["stale_nodes"] == []
    assert report["future_label_violations"] == []
    (tmp_path / "graph.json").write_text(
        cc.dumps_canonical(spec), encoding="utf-8")
    rc, d = None, None
    rc = v3cli.main(["graph", "--graph", str(tmp_path / "graph.json")])
    out = capsys.readouterr().out
    d = json.loads(out)
    assert rc == 0 and d["status"] == "ok"
    assert set(d["disk_status"].values()) == {"present"}
    # 图不含 route/check present 节点（无引擎证据不凑）
    ids = {n["artifact_id"] for n in spec["nodes"]}
    assert not any(x in ids for x in ("route_plan", "check_report"))


def test_conversion_log_contract():
    log = cc.build_conversion_log(
        board_id="synth", module_sha256=hashing.sha256_text(
            open(cc.__file__, encoding="utf-8").read()),
        inputs=[{"path": "datasets/x/b.kicad_pcb",
                 "sha256": _sha(SYNTH_BOARD), "role": "unrouted_pcb"}],
        outputs=[{"path": "inputs/board.kicad_pcb",
                  "sha256": _sha(SYNTH_BOARD), "role": "normalized_board"}],
        model_u=_synth_model(), model_r=_synth_routed_model(),
        crit=cc.derive_critical_nets(_synth_model()),
        topology_group="cu2-5net-3mod-7pad-usb-diffpair")
    for key in ("track", "conversion_date", "board_id", "module",
                "module_sha256", "inputs", "outputs", "retained", "dropped",
                "convention_basis", "field_missingness", "determinism_claim"):
        assert key in log
    assert log["field_missingness"]["anchors"].startswith("not_determinable")
    assert "byte-exact" in log["determinism_claim"]


# ---------------- 逐 profile 报告（TD8 报告合同；fail-closed） ----------------

def _report_kwargs(**over):
    kw = dict(
        board_id="bm1", profile_id="pcbbm-bm1", dataset_role="train",
        denominators={"net_count": 100, "named_net_count": 99,
                      "module_count": 57, "pad_count": 319},
        quality={"audit_result": "pass"},
        limits=["route/check 未执行（无引擎）"],
        leakage_audit_ref={"path": "out/v3-tl5/leakage-audit-…json",
                           "sha256": "0" * 64},
        source={"unrouted_pcb": {"path": "datasets/…", "sha256": "1" * 64}},
        main_path={
            "manifest": {"status": "executed", "evidence": "exit 0",
                         "authority": "v3cli"},
            "compile": {"status": "executed", "evidence": "constraints.json",
                        "authority": "corpus_conversion"},
            "enum": {"status": "executed", "evidence": "net-registry.json",
                     "authority": "corpus_conversion"},
            "audit": {"status": "executed", "evidence": "audit.json",
                      "authority": "corpus_conversion"},
            "feedforward": {"status": "executed",
                            "evidence": "feedforward-plan.json",
                            "authority": "corpus_conversion"},
            "route_check": {"status": "not_executed",
                            "evidence": "v1.x route/check 硬连 Rev-C",
                            "authority": "none"},
        })
    kw.update(over)
    return kw


def test_profile_report_assembles_and_marks_holdout():
    r = cc.build_profile_report(**_report_kwargs())
    assert r["dataset_role"]["role"] == "train"
    assert r["dataset_role"]["frozen_readonly"] is False
    r2 = cc.build_profile_report(**_report_kwargs(dataset_role="holdout"))
    assert r2["dataset_role"]["frozen_readonly"] is True
    assert r2["main_path"]["route_check"]["status"] == "not_executed"


def test_profile_report_fail_closed_on_missing_or_bad_fields():
    with pytest.raises(ValueError, match="missing stage"):
        mp = dict(_report_kwargs()["main_path"]); del mp["audit"]
        cc.build_profile_report(**_report_kwargs(main_path=mp))
    with pytest.raises(ValueError, match="status 非法"):
        mp = dict(_report_kwargs()["main_path"])
        mp["route_check"] = {"status": "pretended_pass", "evidence": "x",
                             "authority": "none"}
        cc.build_profile_report(**_report_kwargs(main_path=mp))
    with pytest.raises(ValueError, match="evidence 必填"):
        mp = dict(_report_kwargs()["main_path"])
        mp["manifest"] = {"status": "executed", "evidence": "",
                          "authority": "v3cli"}
        cc.build_profile_report(**_report_kwargs(main_path=mp))
    with pytest.raises(ValueError, match="denominators missing"):
        d = dict(_report_kwargs()["denominators"]); del d["pad_count"]
        cc.build_profile_report(**_report_kwargs(denominators=d))
    with pytest.raises(ValueError, match="dataset_role 非法"):
        cc.build_profile_report(**_report_kwargs(dataset_role="test"))


# ---------------- 真实数据集回放（datasets/ 在场时） ----------------

_real = os.path.join(RAW, "bm1", "bm1.unrouted.kicad_pcb")
pytestmark_real = pytest.mark.skipif(
    not os.path.isfile(_real), reason="datasets/pcbbenchmarks-r1 不在场")

_REAL_EXPECT = {
    "bm1": {"net_count": 100, "named_net_count": 99, "module_count": 57,
            "pad_count": 319, "seg": 1736, "via": 129,
            "pair": ["D+", "D-"]},
    "bm11": {"net_count": 70, "named_net_count": 69, "module_count": 46,
             "pad_count": 207, "seg": 842, "via": 75,
             "pair": ["/USBD+", "/USBD-"]},
}


@pytest.mark.skipif(not os.path.isfile(_real), reason="datasets 缺失")
@pytest.mark.parametrize("board", ["bm1", "bm11"])
def test_real_board_parse_and_artifacts(board):
    exp = _REAL_EXPECT[board]
    u_text = open(os.path.join(RAW, board, f"{board}.unrouted.kicad_pcb"),
                  encoding="utf-8").read()
    r_text = open(os.path.join(RAW, board, f"{board}.routed.kicad_pcb"),
                  encoding="utf-8").read()
    mu = cc.parse_kicad5_board(u_text)
    mr = cc.parse_kicad5_board(r_text)
    d = cc.board_denominators(mu)
    assert (d["net_count"], d["named_net_count"], d["module_count"],
            d["pad_count"]) == (exp["net_count"], exp["named_net_count"],
                                exp["module_count"], exp["pad_count"])
    assert (mr["segment_count"], mr["via_count"]) == (exp["seg"],
                                                      exp["via"])
    crit = cc.derive_critical_nets(mu)
    assert crit["diff_pairs"] == [exp["pair"]]
    audit = cc.build_audit_obj(mu, mr, board_id=board)
    assert audit["result"] == "pass", audit["checks"]
    # profile/manifest schema 合规 + 规范化板确定性
    prof = cc.build_profile_obj(mu, profile_id=f"pcbbm-{board}",
                                project_id=f"pcbbm-{board}", crit=crit)
    assert manifest.validate_profile(prof) == []
    nb1 = cc.normalized_board_text(
        mu, source_path=f"datasets/pcbbenchmarks-r1/raw/{board}/"
                        f"{board}.unrouted.kicad_pcb",
        source_sha256=_sha(u_text))
    nb2 = cc.normalized_board_text(
        mu, source_path=f"datasets/pcbbenchmarks-r1/raw/{board}/"
                        f"{board}.unrouted.kicad_pcb",
        source_sha256=_sha(u_text))
    assert nb1 == nb2


@pytest.mark.skipif(not os.path.isfile(_real), reason="datasets 缺失")
def test_real_topology_groups_distinct_and_split_consistent():
    sig = {}
    for board in ("bm1", "bm11"):
        mu = cc.parse_kicad5_board(open(
            os.path.join(RAW, board, f"{board}.unrouted.kicad_pcb"),
            encoding="utf-8").read())
        sig[board] = cc.topology_group_id(mu, cc.derive_critical_nets(mu))
    assert sig["bm1"] != sig["bm11"]  # 一阶计数口径可区分 → 无跨 split 同组
