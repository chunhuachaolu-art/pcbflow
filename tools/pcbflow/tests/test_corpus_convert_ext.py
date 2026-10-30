"""observation 线预测侧扩展（扩展实施批·包 b；ADJUDICATION R5/R8）测试。

覆盖：六类逐类估计路径（escape_slots=C2 同源场账、layer_capacity=C3
同源 demand+corpus_ext supply 精确值）、四类 blocked 诚实声明（estimable
=false、FF-CORPUS not_modelled 原文 verbatim 引用两态）、R8 逐层 pad
计数复算与 FF-CORPUS 逐层对账（正/负向）、snapshot 六键组与 stale_plan
语义（verifiable 分组、check_stale_ext 双向）、detect_binding 五档路由、
pad 几何视图（旋转折算/重复 reference 唯一化降级）、负向四类（缺字段/
非法枚举/非有限数/未知格式——含版本门、绑定档错配、联名冲突）、
真实 fixture（pic_programmer，sha 锚与 test_actual_ext.py 同源）端到端
+确定性 byte-exact、与既有 corpus_convert 链的并列同判证据。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import config, corpus_convert, corpus_convert_ext as cce
from pcbflow import feedforward_config as ffc
from pcbflow import hashing

FIX = os.path.join("tests", "fixtures", "kicad_demos")

#: 真实 fixture（拷贝自 datasets/kicad-demos-r1/raw；sha256 在测试内对账，
#: 锚与 test_actual_ext.py / test_tl5_convert_k9.py 同源）
PIC_PROGRAMMER_SHA256 = (
    "1ca70b620506818eb0227e2863bbd573d1fec1672072dc43d0dbe8475e69c8fb")

PIC_PROFILE = "kicaddemo-pic_programmer-pic_programmer"


def _pic_programmer_text() -> str:
    with open(os.path.join(FIX, "pic_programmer.kicad_pcb"), "rb") as f:
        raw = f.read()
    assert hashlib.sha256(raw).hexdigest() == PIC_PROGRAMMER_SHA256, \
        "fixture byte drift: pic_programmer.kicad_pcb"
    return raw.decode("utf-8")


def _pic_ff_corpus_plan() -> dict:
    rel = os.path.join("profiles", PIC_PROFILE, "derived",
                       "feedforward-plan.json")
    with open(rel, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 合成板：名绑定档（20260206）
# ---------------------------------------------------------------------------

#: 名绑定档精确值板：N1（U1.1↔U2.1，跨封装 transit 靶 + 链式直连长 50）、
#: N2（单端，不入 layer demand）、GND（模型内建跳过靶）；U2 只 1 pad
#:（layer_capacity supply 用）；REF** 重复唯一化降级靶（MARK1/MARK2）
SYNTH_NAME_BOUND = """(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0")

  (layers
    (0 "F.Cu" signal)
    (2 "B.Cu" signal)
  )

  (footprint "Lib:U" (layer "F.Cu")
    (at 0.0 0.0)
    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 1.0 1.0) (layers "*.Cu") (net "N1"))
    (pad "2" smd rect (at 3.0 4.0) (size 1.0 1.0) (layers "F.Cu") (net "N2"))
    (pad "3" smd rect (at 6.0 0.0) (size 1.0 1.0) (layers "*.Cu") (net "GND"))
  )

  (footprint "Lib:U" (layer "F.Cu")
    (at 50.0 0.0)
    (property "Reference" "U2" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 1.0 1.0) (layers "*.Cu") (net "N1"))
  )

  (footprint "Lib:M" (layer "F.Cu")
    (at 90.0 0.0)
    (property "Reference" "REF**" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 1.0 1.0) (layers "F.Cu"))
  )

  (footprint "Lib:M" (layer "F.Cu")
    (at 95.0 0.0)
    (property "Reference" "REF**" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 1.0 1.0) (layers "F.Cu"))
  )

  (segment (start 0.0 0.0) (end 50.0 0.0) (width 0.25) (layer "F.Cu")
    (net "N1"))
  (via (at 25.0 0.0) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu")
    (net "N1"))
)

"""

#: 名绑定档旋转折算靶：U1 rot=90，pad "2" 局部 (2,0) → 板绝对 (10,18)
SYNTH_NAME_ROT = """(kicad_pcb (version 20260206) (generator "pcbnew") (generator_version "10.0")

  (layers
    (0 "F.Cu" signal)
  )

  (footprint "Lib:A" (layer "F.Cu")
    (at 10.0 20.0 90)
    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 0.3 0.3) (layers "F.Cu") (net "VCC"))
    (pad "2" smd rect (at 2.0 0.0) (size 0.3 0.3) (layers "F.Cu") (net "VCC"))
  )
)

"""

#: 零封装板（constraints demo 板同形态）：无 footprint 节点 → bbox=None
#: 显式无定义、escape 空场账、layer_capacity 板级 blocked
SYNTH_ZERO_PAD = """(kicad_pcb (version 20260624) (generator "pcbnew") (generator_version "9.0")

  (layers
    (0 "F.Cu" signal)
    (2 "B.Cu" signal)
  )
)

"""

# ---------------------------------------------------------------------------
# 合成板：id 绑定档（20171130，KiCad5 module 形态 + 三 token net 联名）
# ---------------------------------------------------------------------------

SYNTH_ID_BOUND = """(kicad_pcb (version 20171130) (generator pcbnew)

  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
  )

  (module "Lib:U" (layer "F.Cu")
    (at 0.0 0.0)
    (fp_text reference "U1" (at 0.0 0.0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 1.0 1.0) (layers "F.Cu")
      (net 5 "N1"))
    (pad "2" smd rect (at 0.0 5.0) (size 1.0 1.0) (layers "F.Cu")
      (net 5 "N1"))
  )

  (module "Lib:R" (layer "F.Cu")
    (at 40.0 0.0)
    (fp_text reference "R1" (at 0.0 0.0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0.0 0.0) (size 1.0 1.0) (layers "F.Cu")
      (net 5 "N1"))
    (pad "2" smd rect (at 0.0 0.0) (size 1.0 1.0) (layers "F.Cu")
      (net 7 "GND"))
  )

  (segment (start 0.0 0.0) (end 0.0 5.0) (width 0.25) (layer "F.Cu")
    (net 5))
)

"""

#: 联名冲突靶（id 档同 net_key=5 两 pad 联名不一致）
SYNTH_ID_CONFLICT = SYNTH_ID_BOUND.replace('(net 5 "N1"))\n    (pad "2"',
                                           '(net 5 "N1"))\n    (pad "2"')


def _mk_name_board() -> str:
    return SYNTH_NAME_BOUND


# ---------------------------------------------------------------------------
# detect_binding：五档确定性路由 + 未知格式 fail-closed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("version,expected", [
    ("20171130", "net_id_bound"),
    ("20241030", "net_id_bound"),
    ("20241229", "net_id_bound"),
    ("20260206", "net_name_bound"),
    ("20260624", "net_name_bound"),
])
def test_detect_binding_five_versions(version, expected):
    text = f'(kicad_pcb (version {version}) (generator "pcbnew"))'
    assert cce.detect_binding(text) == expected


@pytest.mark.parametrize("text", [
    '(kicad_pcb (generator "pcbnew"))',                # 缺 version
    '(kicad_pcb (version 19990101))',                  # 未知版本
    '(kicad_pcb (version 20260206)) (kicad_pcb)',      # 双根
])
def test_detect_binding_unknown_format_fail_closed(text):
    with pytest.raises(cce.CorpusExtError):
        cce.detect_binding(text)


def test_detect_binding_non_str_fail_closed():
    with pytest.raises(cce.CorpusExtError):
        cce.detect_binding(b"(kicad_pcb)")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# extract_pad_geometry：视图/折算/唯一化降级/负向四类
# ---------------------------------------------------------------------------

def test_pad_geometry_name_bound_view():
    g = cce.extract_pad_geometry(_mk_name_board())
    assert g["binding"] == "net_name_bound"
    assert g["board_version"] == "20260206"
    assert [l["name"] for l in g["copper_layers"]] == ["F.Cu", "B.Cu"]
    assert len(g["pads"]) == 6  # U1×3 + U2×1 + REF**×2
    assert [(p["ref"], p["num"]) for p in g["pads"]] == sorted(
        (p["ref"], p["num"]) for p in g["pads"])
    by = {(p["ref"], p["num"]): p for p in g["pads"]}
    assert by[("U1", "1")]["net"] == "N1"
    assert by[("U1", "3")]["net"] == "GND"
    # 名档无 net 子节点 → pads_without_net_token 如实计数（REF** 两 pad）
    assert g["pads_without_net_token"] == 2
    assert g["pads_net_id_zero"] == 0
    # REF** 重复 → 唯一化降级 + parse_warnings 显式登记（不静默覆盖）
    assert any(w.startswith("duplicate_reference:REF**->REF**~dup")
               for w in g["parse_warnings"])
    refs = {p["ref"] for p in g["pads"]}
    assert "REF**" in refs and any(r.startswith("REF**~dup") for r in refs)
    # side 判定在场（geo.finalize_board 口径）
    assert by[("U2", "1")]["side"]


def test_pad_geometry_rotation_abs_xy():
    g = cce.extract_pad_geometry(SYNTH_NAME_ROT)
    by = {(p["ref"], p["num"]): p for p in g["pads"]}
    assert by[("U1", "2")]["x"] == pytest.approx(10.0)
    assert by[("U1", "2")]["y"] == pytest.approx(18.0)


def test_pad_geometry_id_bound_net_names():
    g = cce.extract_pad_geometry(SYNTH_ID_BOUND)
    assert g["binding"] == "net_id_bound"
    assert g["board_version"] == "20171130"
    by = {(p["ref"], p["num"]): p for p in g["pads"]}
    assert by[("U1", "1")]["net"] == "N1"
    assert by[("R1", "2")]["net"] == "GND"
    # KiCad5 双 token net（segment 形态不在 pad 上出现；pad 三 token 缺名
    # → net=None 如实）
    assert g["copper_layers"][0]["name"] == "F.Cu"
    assert g["copper_layers"][-1]["name"] == "B.Cu"


# --- 负向：缺字段 -----------------------------------------------------------

def _variant(base: str, old: str, new: str) -> str:
    assert old in base
    return base.replace(old, new, 1)


def test_missing_pad_at_fail_closed():
    text = _variant(SYNTH_NAME_ROT, "(at 2.0 0.0) (size 0.3 0.3)",
                    "(size 0.3 0.3)")
    with pytest.raises(cce.CorpusExtError, match="缺 at"):
        cce.extract_pad_geometry(text)


def test_missing_pad_size_fail_closed():
    text = _variant(SYNTH_NAME_ROT, "(at 2.0 0.0) (size 0.3 0.3)",
                    "(at 2.0 0.0)")
    with pytest.raises(cce.CorpusExtError, match="缺 size"):
        cce.extract_pad_geometry(text)


def test_missing_pad_layers_fail_closed():
    text = _variant(SYNTH_NAME_ROT,
                    "(size 0.3 0.3) (layers \"F.Cu\") (net \"VCC\"))\n"
                    "    (pad \"2\"",
                    "(size 0.3 0.3) (net \"VCC\"))\n    (pad \"2\"")
    with pytest.raises(cce.CorpusExtError, match="缺 layers"):
        cce.extract_pad_geometry(text)


def test_missing_footprint_at_fail_closed():
    text = _variant(SYNTH_NAME_ROT, '  (footprint "Lib:A" (layer "F.Cu")\n'
                                    '    (at 10.0 20.0 90)',
                    '  (footprint "Lib:A" (layer "F.Cu")')
    with pytest.raises(cce.CorpusExtError, match="缺 at"):
        cce.extract_pad_geometry(text)


# --- 负向：非有限数 / 不可解析 token ----------------------------------------

@pytest.mark.parametrize("tok", ["nan", "inf", "-inf", "abc"])
def test_non_finite_or_bad_token_fail_closed(tok):
    text = _variant(SYNTH_NAME_ROT, "(at 2.0 0.0) (size 0.3 0.3)",
                    f"(at {tok} 0.0) (size 0.3 0.3)")
    with pytest.raises(cce.CorpusExtError):
        cce.extract_pad_geometry(text)
    text2 = _variant(SYNTH_NAME_ROT, "(at 2.0 0.0) (size 0.3 0.3)",
                     f"(at 2.0 0.0) (size 0.3 {tok})")
    with pytest.raises(cce.CorpusExtError):
        cce.extract_pad_geometry(text2)


# --- 负向：绑定档错配 / 联名冲突 --------------------------------------------

def test_binding_mismatch_name_board_with_numeric_net_fail_closed():
    text = _variant(SYNTH_NAME_ROT, '(net "VCC")', "(net 5 \"VCC\")")
    with pytest.raises(cce.CorpusExtError, match="绑定档错配"):
        cce.extract_pad_geometry(text)


def test_binding_mismatch_id_board_with_name_token_fail_closed():
    # id 档 pad 出现非数字 net token（KiCad5 合法形态须数字）
    text = _variant(SYNTH_ID_BOUND, '(net 7 "GND")', '(net "GND")')
    with pytest.raises(cce.CorpusExtError, match="绑定档错配"):
        cce.extract_pad_geometry(text)


def test_net_name_conflict_fail_closed():
    # 同 net_key=5 两 pad 联名冲突 → 数据不自洽 fail-closed
    text = _variant(SYNTH_ID_BOUND, '(net 5 "N1"))\n    (pad "2"',
                    '(net 5 "N9"))\n    (pad "2"')
    with pytest.raises(cce.CorpusExtError, match="联名冲突"):
        cce.extract_pad_geometry(text)


# ---------------------------------------------------------------------------
# escape_slots：C2 同源场账（transit/GND 跳过/资源行形态）
# ---------------------------------------------------------------------------

def _pad_geo_name() -> dict:
    return cce.extract_pad_geometry(_mk_name_board())


def test_escape_transit_and_resource_row_shape():
    est = cce.estimate_escape_slots(_pad_geo_name())
    assert est["estimable"] is True
    assert est["kind"] == "escape_slots"
    rows = {r["resource_id"]: r for r in est["resources"]}
    # U1.1 (0,0)：对端 U2.1 (50,0) 在全部逃逸带外 → transit；通道净空
    assert "escape_slots:U1|N" in rows
    r = rows["escape_slots:U1|N"]
    assert r["demand"]["value"] == 1
    assert r["demand"]["unit"] == "channels"
    assert r["supply"]["unit"] == "channels"
    assert r["scope"]["transit_nets"] == ["N1"]
    assert r["reserve"]["value"] == 0.0
    assert r["demand_model"] == ffc.DEMAND_MODELS["escape_slots"]
    assert r["net_ids"] == [] and r["relation_ids"] == []
    # margin=supply−demand；state=四态分类（yellow=1.0 channels）
    assert r["margin"]["value"] == pytest.approx(
        r["supply"]["value"] - r["demand"]["value"])
    assert r["state"] in ("available", "low_margin", "resource_deficit",
                          "missing_basis")
    # 资源行典序
    ids = [x["resource_id"] for x in est["resources"]]
    assert ids == sorted(ids)


def test_escape_gnd_and_netless_pads_skipped():
    est = cce.estimate_escape_slots(_pad_geo_name())
    meta = est["fields_meta"]
    # GND（U1.3）与无 net（REF** 两 pad）不入任何场账
    assert meta["pads_total"] == 6
    for r in est["resources"]:
        assert "GND" not in r["scope"]["transit_nets"]
        assert not r["scope"]["ref"].startswith("REF**")
    # 逐行 transit_nets 只含 N1/N2（本合成板语义）
    nets = {n for r in est["resources"] for n in r["scope"]["transit_nets"]}
    assert nets <= {"N1", "N2"}


def test_escape_resource_ids_sorted_and_no_blocked_only_rows():
    est = cce.estimate_escape_slots(_pad_geo_name())
    # 无逃逸需求不列账（同 Rev-C 口径），总数入 meta
    assert est["fields_meta"]["fields_total"] >= len(est["resources"])


# ---------------------------------------------------------------------------
# layer_capacity：C3 同源 demand 精确值 + corpus_ext supply 口径
# ---------------------------------------------------------------------------

def test_layer_capacity_exact_values():
    g = _pad_geo_name()
    est = cce.estimate_layer_capacity(g)
    assert est["estimable"] is True
    row = est["resources"][0]
    # N1 两端 (0,0)↔(50,0)：链长 50；GND/N2/无 net 不入 demand
    # （N2 单端 len<2 跳过；GND 模型内建跳过）
    assert est["layer_capacity_meta"]["demand_len_mm"] == pytest.approx(50.0)
    assert row["demand"]["value"] == pytest.approx(
        50.0 * config.AUDIT_TRACK_PITCH_MM, abs=1e-3)
    # supply=铜层数×(pad-bbox 板面积−Σ封装膨胀占用)（消费 config 常量重算）
    import pcbflow.geo as geo
    used = sum(geo.bbox_area(geo.bbox_inflate(f["bbox"],
                                              config.AUDIT_BODY_INFLATE_MM))
               for f in g["footprints"].values())
    board_area = geo.bbox_area(g["bbox"])
    expect_supply = round(2 * max(0.0, board_area - used), 3)
    assert row["supply"]["value"] == pytest.approx(expect_supply)
    assert row["scope"]["layer_count"] == 2
    assert row["scope"]["layers"] == ["F.Cu", "B.Cu"]
    assert row["reserve"]["value"] == 0.0
    assert row["state"] in ("available", "low_margin", "resource_deficit",
                            "missing_basis")
    assert row["kind"] == "layer_capacity"
    assert row["resource_id"] == "layer_capacity:board"
    assert est["layer_capacity_meta"]["named_nets_total"] == 3  # N1/N2/GND


def test_layer_capacity_gnd_excluded_from_demand():
    # 若 GND 未被跳过：U1.1↔U1.3 (0,0)↔(6,0) 与 U2 链会改变 demand_len；
    # 断言 demand_len 与仅 N1 的精确值一致即证跳过生效
    est = cce.estimate_layer_capacity(_pad_geo_name())
    assert est["layer_capacity_meta"]["demand_len_mm"] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# blocked 四类：诚实声明（不伪造、不降级凑数）
# ---------------------------------------------------------------------------

FF_CORPUS_NOT_MODELLED = [
    "电流预算/线宽推导（无原理图电流源，不虚构）",
    cce.NOT_MODELLED_VIA,
    "impedance targets（无叠层介质参数）",
]


def test_blocked_kinds_declared_honestly():
    rows = cce.declare_blocked_kinds(FF_CORPUS_NOT_MODELLED)
    assert [r["kind"] for r in rows] == sorted(cce.BLOCKED_KINDS)
    assert set(cce.BLOCKED_KINDS) | set(cce.ESTIMABLE_KINDS) == \
        set(cce.RESOURCE_KINDS_ALL)
    for r in rows:
        assert r["estimable"] is False
        assert r["status"] == "blocked"
        assert r["not_available_reason"]
        assert r["basis"]
        assert r["demand_model"]
    via = next(r for r in rows if r["kind"] == "via_budget")
    # FF-CORPUS not_modelled 原文 verbatim 命中 → 逐字引用
    assert via["ff_corpus_declaration_present"] is True
    assert via["not_modelled_verbatim"] == cce.NOT_MODELLED_VIA


def test_blocked_kinds_without_ff_corpus_declaration():
    rows = cce.declare_blocked_kinds([])
    via = next(r for r in rows if r["kind"] == "via_budget")
    assert via["not_modelled_verbatim"] is None
    assert via["ff_corpus_declaration_present"] is False


# ---------------------------------------------------------------------------
# R8：signal_layer_pad_load 复算 + 逐层对账（正/负向）
# ---------------------------------------------------------------------------

def test_r8_recompute_counts_wildcard_duplication():
    g = _pad_geo_name()
    counts = cce._pad_layer_counts(g)
    # *.Cu pad（U1.1、U1.3、U2.1）跨层重复计数；F.Cu 专属（U1.2、REF**×2）
    # F.Cu=3 通配+1 专属+2 REF**=6；B.Cu=3 通配
    by = {c["layer"]: c["pad_count"] for c in counts}
    assert by["F.Cu"] == 6
    assert by["B.Cu"] == 3


def test_r8_alignment_ok_and_shape():
    g = _pad_geo_name()
    counts = cce._pad_layer_counts(g)
    plan = {
        "plan_id": "FF-CORPUS-X-0001",
        "not_modelled": list(FF_CORPUS_NOT_MODELLED),
        "signal_layer_pad_load": [
            {"layer": c["layer"], "pad_count": c["pad_count"]}
            for c in counts],
    }
    out = cce.align_signal_layer_pad_load(g, plan)
    assert out["aligned"] is True
    assert out["recomputed"] == out["ff_corpus_declared"]
    assert out["layers_total"] == 2


def test_r8_mismatch_pad_count_fail_closed():
    g = _pad_geo_name()
    plan = {
        "plan_id": "FF-CORPUS-X-0001",
        "not_modelled": [],
        "signal_layer_pad_load": [
            {"layer": "F.Cu", "pad_count": 999},
            {"layer": "B.Cu", "pad_count": 3},
        ],
    }
    with pytest.raises(cce.CorpusExtError, match="R8 对账失败"):
        cce.align_signal_layer_pad_load(g, plan)


def test_r8_mismatch_layer_set_fail_closed():
    g = _pad_geo_name()
    plan = {
        "plan_id": "FF-CORPUS-X-0001",
        "not_modelled": [],
        "signal_layer_pad_load": [{"layer": "F.Cu", "pad_count": 6}],
    }
    with pytest.raises(cce.CorpusExtError, match="R8 对账失败"):
        cce.align_signal_layer_pad_load(g, plan)


@pytest.mark.parametrize("key", ["signal_layer_pad_load", "not_modelled",
                                 "plan_id"])
def test_r8_missing_ff_corpus_key_fail_closed(key):
    g = _pad_geo_name()
    plan = {
        "plan_id": "FF-CORPUS-X-0001",
        "not_modelled": [],
        "signal_layer_pad_load": [],
    }
    del plan[key]
    with pytest.raises(cce.CorpusExtError, match="缺键"):
        cce.align_signal_layer_pad_load(g, plan)


# ---------------------------------------------------------------------------
# 扩展计划对象：§7 契约面 + stale_plan 语义 + 确定性
# ---------------------------------------------------------------------------

def _ff_corpus_for(board_text: str) -> dict:
    g = cce.extract_pad_geometry(board_text)
    counts = cce._pad_layer_counts(g)
    return {
        "plan_id": "FF-CORPUS-SYNTH-0001",
        "producer": "pcbflow.corpus_convert",
        "not_modelled": list(FF_CORPUS_NOT_MODELLED),
        "signal_layer_pad_load": [
            {"layer": c["layer"], "pad_count": c["pad_count"]}
            for c in counts],
    }


def _build_synthetic_plan(board_text=_mk_name_board(), **over):
    kwargs = dict(
        profile_id="pcbench-synth-synth", board_id="synth_synth",
        dataset_id="pcbench-r1", split_role="train",
        board_path_rel="datasets/pcbench-r1/raw/synth_synth/raw.kicad_pcb",
        board_sha256="a" * 64,
        ff_corpus_plan=_ff_corpus_for(board_text),
        registry_sha256="b" * 64,
    )
    kwargs.update(over)
    return cce.build_ext_plan_obj(board_text, **kwargs)


def test_plan_contract_surface():
    plan = _build_synthetic_plan()
    assert plan["schema_version"] == "1.3"
    assert plan["artifact_kind"] == "feedforward_plan_ext"
    assert plan["status"] == "planning_advisory"
    assert plan["plan_id"] == "FF-EXT-PCBENCH-SYNTH-SYNTH-0001"
    # 六类资源段齐备：escape 行 + layer_capacity 行 + 4 blocked 行
    kinds = {r["kind"] for r in plan["resources"]}
    assert kinds == set(cce.RESOURCE_KINDS_ALL)
    ks = plan["resource_kind_summary"]
    assert ks["estimable_kinds"] == ["escape_slots", "layer_capacity"]
    assert ks["blocked_kinds"] == list(cce.BLOCKED_KINDS)
    assert ks["escape_rows"] >= 1
    assert ks["layer_capacity_rows"] == 1
    assert ks["blocked_rows"] == 4
    # 资源行 resource_id 典序
    ids = [r["resource_id"] for r in plan["resources"]]
    assert ids == sorted(ids)
    # controls=[]：语料板域无阶段消费链（diagnostics 显式登记）
    assert plan["controls"] == []
    assert any(d["id"] == "corpus_ext_controls_empty"
               for d in plan["diagnostics"])
    # consumption_contract：routed 元素显式 ignored
    ignored = plan["consumption_contract"]["ignored"]
    assert any("segment/arc/via/zone" in i["elements"] for i in ignored)
    assert plan["consumption_contract"]["fallback"] is None
    # corpus_baseline：FF-CORPUS 原文 verbatim 照抄
    assert plan["corpus_baseline"]["not_modelled_verbatim"] == \
        FF_CORPUS_NOT_MODELLED
    assert plan["corpus_baseline"]["producer"] == "pcbflow.corpus_convert"
    # R8 段
    assert plan["signal_layer_pad_load"]["aligned"] is True
    assert plan["signal_layer_pad_load"]["recomputed"] == \
        plan["signal_layer_pad_load"]["ff_corpus_declared"]


def test_plan_snapshot_six_keys_and_binding():
    plan = _build_synthetic_plan()
    values = plan["snapshot"]["values"]
    assert set(values) == {
        "registry_snapshot_hash", "structures_sha256", "constraints_sha256",
        "placement_snapshot_sha256", "board_snapshot_sha256",
        "feedforward_config_sha256"}
    binding = plan["snapshot"]["binding"]
    # board/registry 两键 verifiable（可复核），值入 values
    assert binding["board_snapshot_sha256"]["verifiable"] is True
    assert values["board_snapshot_sha256"] == "a" * 64
    assert binding["registry_snapshot_hash"]["verifiable"] is True
    assert values["registry_snapshot_hash"] == "b" * 64
    # 四缺源键=null+reason（不硬造）
    for k in ("structures_sha256", "constraints_sha256",
              "placement_snapshot_sha256", "feedforward_config_sha256"):
        assert values[k] is None
        assert binding[k]["verifiable"] is False
        assert binding[k]["reason"]


def test_plan_registry_none_verifiable_false():
    plan = _build_synthetic_plan(registry_sha256=None)
    assert plan["snapshot"]["values"]["registry_snapshot_hash"] is None
    assert plan["snapshot"]["binding"]["registry_snapshot_hash"][
        "verifiable"] is False


def test_stale_semantics_match_and_mismatch():
    plan = _build_synthetic_plan()
    cur_b = plan["snapshot"]["values"]["board_snapshot_sha256"]
    cur_r = plan["snapshot"]["values"]["registry_snapshot_hash"]
    ok = cce.check_stale_ext(plan, cur_b, cur_r)
    assert ok["stale_plan"] is False and ok["diff_keys"] == []
    bad = cce.check_stale_ext(plan, "c" * 64, cur_r)
    assert bad["stale_plan"] is True
    assert bad["diff_keys"] == ["board_snapshot_sha256"]


def test_stale_registry_mismatch_detected():
    plan = _build_synthetic_plan()
    bad = cce.check_stale_ext(
        plan, plan["snapshot"]["values"]["board_snapshot_sha256"], None)
    assert bad["stale_plan"] is True
    assert bad["diff_keys"] == ["registry_snapshot_hash"]


def test_plan_byte_exact_rerun():
    b1 = hashing.canonical_json_bytes(_build_synthetic_plan())
    b2 = hashing.canonical_json_bytes(_build_synthetic_plan())
    assert b1 == b2
    assert hashing.sha256_bytes(b1) == hashing.sha256_bytes(b2)


def test_plan_canonical_json_wellformed():
    b = hashing.canonical_json_bytes(_build_synthetic_plan())
    obj = json.loads(b.decode("utf-8"))
    assert obj["plan_id"] == "FF-EXT-PCBENCH-SYNTH-SYNTH-0001"


# ---------------------------------------------------------------------------
# 板记录盘点与 manifest 对账（fail-closed）
# ---------------------------------------------------------------------------

def _k9_plan_stub():
    return {"boards": [{
        "profile_id": "kicaddemo-x-x", "board_id": "x/x",
        "source_rel": "datasets/kicad-demos-r1/raw/x/x.kicad_pcb",
        "source_sha256_before_drc": "d" * 64,
        "split_role": "train",
    }]}


def _manifests_stub():
    return {
        "pcbench": {"dataset_id": "pcbench-r1",
                    "board_ids": ["kitspace_glasgow"],
                    "dataset_splits": {"train": ["kitspace_glasgow"],
                                       "validation": [], "holdout": []}},
        "pcbbm": {"dataset_id": "pcbbenchmarks-r1", "board_ids": ["bm1"],
                  "dataset_splits": {"train": ["bm1"], "validation": [],
                                     "holdout": []}},
        "kicad": {"dataset_id": "kicad-demos-r1", "board_ids": ["x/x"],
                  "dataset_splits": {"train": ["x/x"], "validation": [],
                                     "holdout": []}},
    }


def test_build_board_records_ok():
    recs = cce.build_board_records(_k9_plan_stub(), _manifests_stub())
    assert len(recs) == 1
    r = recs[0]
    assert r["profile_id"] == "kicaddemo-x-x"
    assert r["dataset_id"] == "kicad-demos-r1"
    assert r["split_role"] == "train"
    assert r["manifest_ref"] == "dataset-manifest-kicad-demos-r1.json"


def test_build_board_records_role_conflict_fail_closed():
    stub = _k9_plan_stub()
    stub["boards"][0]["split_role"] = "holdout"
    with pytest.raises(cce.CorpusExtError, match="冲突"):
        cce.build_board_records(stub, _manifests_stub())


def test_build_board_records_board_not_in_manifest_fail_closed():
    stub = _k9_plan_stub()
    stub["boards"][0]["board_id"] = "y/y"
    with pytest.raises(cce.CorpusExtError):
        cce.build_board_records(stub, _manifests_stub())


def test_reconcile_real_board_record_ok():
    rec = {"profile_id": "pcbench-kitspace-glasgow",
           "board_id": "kitspace_glasgow", "dataset_role": "train",
           "reference_path":
               "datasets/pcbench-r1/raw/kitspace_glasgow/raw.kicad_pcb"}
    out = cce.reconcile_real_board_record(rec, _manifests_stub())
    assert out["dataset_id"] == "pcbench-r1"
    assert out["split_role"] == "train"
    assert out["manifest_ref"] == "dataset-manifest-pcbench-r1-v3.json"


def test_reconcile_real_board_record_foreign_path_fail_closed():
    rec = {"profile_id": "p", "board_id": "x", "dataset_role": "train",
           "reference_path": "datasets/other-r1/raw/x/x.kicad_pcb"}
    with pytest.raises(cce.CorpusExtError, match="数据域"):
        cce.reconcile_real_board_record(rec, _manifests_stub())


def test_reconcile_real_board_record_role_conflict_fail_closed():
    rec = {"profile_id": "pcbench-kitspace-glasgow",
           "board_id": "kitspace_glasgow", "dataset_role": "holdout",
           "reference_path":
               "datasets/pcbench-r1/raw/kitspace_glasgow/raw.kicad_pcb"}
    with pytest.raises(cce.CorpusExtError, match="冲突"):
        cce.reconcile_real_board_record(rec, _manifests_stub())


def test_reconcile_real_board_record_not_in_manifest_fail_closed():
    rec = {"profile_id": "pcbench-ghost-ghost", "board_id": "ghost_ghost",
           "dataset_role": "train",
           "reference_path": "datasets/pcbench-r1/raw/ghost/raw.kicad_pcb"}
    with pytest.raises(cce.CorpusExtError):
        cce.reconcile_real_board_record(rec, _manifests_stub())


# ---------------------------------------------------------------------------
# 零封装板特例（constraints demo 板同形态）：空场账如实 + 板级 blocked
# ---------------------------------------------------------------------------

def test_zero_pad_board_geometry_and_estimates():
    g = cce.extract_pad_geometry(SYNTH_ZERO_PAD)
    assert g["pads"] == [] and g["footprints"] == {}
    assert g["bbox"] is None  # 显式无定义，不虚构
    assert [l["name"] for l in g["copper_layers"]] == ["F.Cu", "B.Cu"]
    esc = cce.estimate_escape_slots(g)
    assert esc["estimable"] is True and esc["resources"] == []
    assert esc["fields_meta"]["fields_total"] == 0
    cap = cce.estimate_layer_capacity(g)
    assert cap["estimable"] is False
    row = cap["resources"][0]
    assert row["status"] == "blocked" and row["kind"] == "layer_capacity"
    assert "零封装" in row["not_available_reason"]


def test_zero_pad_board_plan_contract():
    ff = {"plan_id": "FF-CORPUS-ZERO-0001", "not_modelled": [],
          "signal_layer_pad_load": [{"layer": "F.Cu", "pad_count": 0},
                                    {"layer": "B.Cu", "pad_count": 0}]}
    plan = cce.build_ext_plan_obj(
        SYNTH_ZERO_PAD, profile_id="kicaddemo-zero-zero",
        board_id="zero/zero", dataset_id="kicad-demos-r1",
        split_role="train", board_path_rel="datasets/x.kicad_pcb",
        board_sha256="f" * 64, ff_corpus_plan=ff, registry_sha256=None)
    ks = plan["resource_kind_summary"]
    assert ks["escape_rows"] == 0
    assert ks["layer_capacity_rows"] == 0
    assert ks["layer_capacity_board_blocked"] is True
    assert ks["blocked_rows"] == 5  # 四类类级 blocked + layer_capacity 板级特例
    assert plan["signal_layer_pad_load"]["aligned"] is True
    # 零封装板 escape=空场账（无行如实）；其余五类行均在
    kinds = {r["kind"] for r in plan["resources"]}
    assert kinds == set(cce.RESOURCE_KINDS_ALL) - {"escape_slots"}


# ---------------------------------------------------------------------------
# 真实 fixture 端到端（pic_programmer）+ 与既有链并列同判证据
# ---------------------------------------------------------------------------

def test_real_fixture_end_to_end():
    text = _pic_programmer_text()
    ff = _pic_ff_corpus_plan()
    plan = cce.build_ext_plan_obj(
        text, profile_id=PIC_PROFILE, board_id="pic_programmer/pic_programmer",
        dataset_id="kicad-demos-r1", split_role="train",
        board_path_rel="datasets/kicad-demos-r1/raw/pic_programmer/"
                       "pic_programmer.kicad_pcb",
        board_sha256=PIC_PROGRAMMER_SHA256,
        ff_corpus_plan=ff, registry_sha256="e" * 64)
    assert plan["resource_kind_summary"]["blocked_rows"] == 4
    assert plan["resource_kind_summary"]["escape_rows"] >= 1
    assert plan["resource_kind_summary"]["layer_capacity_rows"] == 1
    # R8：与盘上 FF-CORPUS 真件逐层对账过（fail-closed 通道未触发）
    assert plan["signal_layer_pad_load"]["aligned"] is True
    declared = plan["signal_layer_pad_load"]["ff_corpus_declared"]
    assert declared == ff["signal_layer_pad_load"]
    # stale：自值复核 match
    cur_b = plan["snapshot"]["values"]["board_snapshot_sha256"]
    cur_r = plan["snapshot"]["values"]["registry_snapshot_hash"]
    assert cce.check_stale_ext(plan, cur_b, cur_r)["stale_plan"] is False


def test_real_fixture_byte_exact_rerun():
    text = _pic_programmer_text()
    ff = _pic_ff_corpus_plan()
    args = dict(
        profile_id=PIC_PROFILE, board_id="pic_programmer/pic_programmer",
        dataset_id="kicad-demos-r1", split_role="train",
        board_path_rel="datasets/kicad-demos-r1/raw/pic_programmer/"
                       "pic_programmer.kicad_pcb",
        board_sha256=PIC_PROGRAMMER_SHA256,
        ff_corpus_plan=ff, registry_sha256="e" * 64)
    b1 = hashing.canonical_json_bytes(
        cce.build_ext_plan_obj(text, **args))
    b2 = hashing.canonical_json_bytes(
        cce.build_ext_plan_obj(text, **args))
    assert b1 == b2


def test_parallel_with_corpus_convert_same_judgement():
    """并列性证据：既有 corpus_convert 链对同一合成板行为正常，且其
    signal_layer_pad_load 与本模块复算逐层相等（同判据）；既有链零改动。"""
    model = corpus_convert.parse_kicad5_board(SYNTH_ID_BOUND)
    crit = corpus_convert.derive_critical_nets(model)
    ff_obj = corpus_convert.build_feedforward_obj(
        model, board_id="synth_synth", crit=crit)
    assert ff_obj["producer"] == "pcbflow.corpus_convert"
    g = cce.extract_pad_geometry(SYNTH_ID_BOUND)
    mine = {c["layer"]: c["pad_count"] for c in cce._pad_layer_counts(g)}
    theirs = {d["layer"]: d["pad_count"]
              for d in ff_obj["signal_layer_pad_load"]}
    assert mine == theirs
    out = cce.align_signal_layer_pad_load(g, ff_obj)
    assert out["aligned"] is True
