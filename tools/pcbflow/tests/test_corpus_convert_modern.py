"""corpus-r2-r1 现代版本桶纳入 k9 转换域（20210424/20211014/20221018/
20260206）测试。

覆盖：k9 版本门扩展正负向（新三 token 接受；legacy 桶 20171114/"4" 与
KiCad5 20171130 仍拒绝；k5 门对新 token 拒绝=两门互斥）、逐 token 真实
板 smoke（datasets/corpus-r2-r1 只读，选各桶最小文件控耗时，byte
sha256 对账锚）、fp_text reference 提取（6.x/7.0 档无 property "Reference"
形态，corpus 实测 2485/2485 footprint）、pad 第 4 位置 lock flag 无扰、
铜层 type 双口径（新档 mixed/power 白名单；20241030+ 既有档 signal-only
零改动）、top_level net 绑定、规范化板确定性 byte-exact、构件链
（stackup/net_registry/topology）、corpus_convert_ext 档外门保持拒绝
（r2 G2a 扩档后=十档全集之外仍拒；原五档负向锚随授权行为变更同步）。
"""

from __future__ import annotations

import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from pcbflow import corpus_convert as cc
from pcbflow import corpus_convert_ext as cce

RAW = os.path.join("datasets", "corpus-r2-r1", "raw")

#: 逐 token 真实板 smoke（各桶最小文件，控耗时；datasets 只读，
#: sha256=入库实测锚，测试内对账 byte 漂移）
MODERN_BOARDS = {
    "20210424": (
        "alitekin2fx__stm32-ds2480-emu/stm32_ds2480_emu.kicad_pcb",
        "75b876468e8689b5c68ba7f9c55c2379d7d191cdd2bf212c3029573b36abdb94",
    ),
    "20211014": (
        "fm4dd__pmod-crypto/atecc508a.kicad_pcb",
        "22fd890c9cac830db5132c34c216b8107371eccef16d55fa9ac7d0bf019e8537",
    ),
    "20221018": (
        "everyday-dev__atmega32u4-breakout/atmegaXu4_breakout.kicad_pcb",
        "b541a060871c32c38f44f8ad34c89cdcbb99839ae87d2480712127bbb19559e1",
    ),
    "20260206": (
        "Pealie__thin-pod/Thin-Pod.kicad_pcb",
        "2f83fe4c3c46f17003a2f442f196ad88d4348c811b432c41c4decc0a60b4333f",
    ),
}

#: corpus-r2-r1 新纳入的三个版本 token（20260206 原已在门内）
NEW_TOKENS = ("20210424", "20211014", "20221018")


def _board_text(token: str) -> str:
    rel, sha = MODERN_BOARDS[token]
    with open(os.path.join(RAW, rel), "rb") as f:
        raw = f.read()
    assert hashlib.sha256(raw).hexdigest() == sha, f"byte drift: {rel}"
    return raw.decode("utf-8")


# ---------------------------------------------------------------------------
# 版本门（扩展正负向；两门互斥不变）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("token", NEW_TOKENS)
def test_gate_accepts_new_tokens(token):
    """新 token 过门：6.x/7.0 档无 generator_version（host 如实 pcbnew）。"""
    text = (f'(kicad_pcb (version {token}) (generator "pcbnew")\n'
            f'  (general (thickness 1.6))\n'
            f'  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))\n'
            f'  (net 0 "") (net 1 "GND")\n'
            f'  (footprint "L:C1" (layer "F.Cu") (at 0 0)\n'
            f'    (fp_text "reference" "C1" (at 0 0) (layer "F.SilkS"))\n'
            f'    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu")\n'
            f'      (net 1 "GND"))\n'
            f'  )\n'
            f')')
    model = cc.parse_kicad9_board(text)
    assert model["board_version"] == token
    assert model["host"] == "pcbnew"
    assert model["generator_tokens"] == {"generator": "pcbnew",
                                         "generator_version": None}
    assert model["net_declaration_source"] == "top_level"
    assert model["nets"] == [{"net_id": 0, "name": ""},
                             {"net_id": 1, "name": "GND"}]


@pytest.mark.parametrize("token", ("20171130", "20171114", "4",
                                   "20240101", "garbage"))
def test_gate_still_rejects(token):
    """KiCad5 20171130、legacy 两桶（20171114/"4"）与未知 token 仍拒绝。"""
    with pytest.raises(ValueError, match="outside k9 path gate"):
        cc.parse_kicad9_board(f'(kicad_pcb (version {token})\n)')


@pytest.mark.parametrize("token", NEW_TOKENS + ("20260206",))
def test_k5_gate_rejects_modern_tokens(token):
    """k5 门不动：新 token 不进 parse_kicad5_board（两门互斥）。"""
    with pytest.raises(ValueError, match="expect board version 20171130"):
        cc.parse_kicad5_board(f'(kicad_pcb (version {token})\n)')


# ---------------------------------------------------------------------------
# 逐 token 真实板 smoke（datasets 只读；盘上实测锚）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("token", sorted(MODERN_BOARDS))
def test_real_board_smoke(token):
    text = _board_text(token)
    model = cc.parse_kicad9_board(text)
    d = cc.board_denominators(model)
    assert model["board_version"] == token
    assert model["parse_warnings"] == []
    # reference 全量提取（fp_text / property 双形态；无 __NOREF__ 降级）
    refs = [m["ref"] for m in model["modules"]]
    assert refs == sorted(refs)
    assert all(not r.startswith("__NOREF__") for r in refs)
    if token == "20210424":
        # stm32_ds2480_emu：fp_text reference 档；28 封装/88 pad/30 网
        assert model["host"] == "pcbnew"
        assert model["net_declaration_source"] == "top_level"
        assert d == {"net_count": 30, "named_net_count": 29,
                     "module_count": 28, "pad_count": 88,
                     "pad_thru_hole_count": 9, "pad_smd_count": 77,
                     "pad_without_net_count": 5, "copper_layer_count": 2}
        assert [l["name"] for l in model["copper_layers"]] == \
            ["F.Cu", "B.Cu"]
        assert model["segment_count"] == 186 and model["via_count"] == 20
        # pad (net N "name") 形态（id 绑定档）
        assert model["modules"][0]["ref"] == "C1"
        assert model["modules"][0]["pads"][0]["net"] == \
            {"net_id": 3, "name": "+3V3"}
    elif token == "20211014":
        # atecc508a：6.0 档
        assert model["net_declaration_source"] == "top_level"
        assert d == {"net_count": 17, "named_net_count": 16,
                     "module_count": 13, "pad_count": 49,
                     "pad_thru_hole_count": 31, "pad_smd_count": 18,
                     "pad_without_net_count": 0, "copper_layer_count": 2}
        assert [l["name"] for l in model["copper_layers"]] == \
            ["F.Cu", "B.Cu"]
        assert model["modules"][0]["pads"][0]["net"] == \
            {"net_id": 2, "name": "+3V3"}
    elif token == "20221018":
        # atmegaXu4_breakout：7.0 档
        assert model["net_declaration_source"] == "top_level"
        assert d == {"net_count": 47, "named_net_count": 46,
                     "module_count": 36, "pad_count": 187,
                     "pad_thru_hole_count": 65, "pad_smd_count": 122,
                     "pad_without_net_count": 16, "copper_layer_count": 2}
        assert [l["name"] for l in model["copper_layers"]] == \
            ["F.Cu", "B.Cu"]
        assert model["modules"][0]["pads"][0]["net"] == \
            {"net_id": 2, "name": "GND"}
    else:
        # Thin-Pod（20260206，KiCad 10.0）：原已支持桶——pad_derived，
        # net_id 结构性不可得如实 None
        assert model["host"] == "pcbnew 10.0"
        assert model["net_declaration_source"] == "pad_derived"
        assert d["module_count"] == 24 and d["pad_count"] == 76
        assert d["net_count"] == 14 and d["named_net_count"] == 14
        assert all(n["net_id"] is None for n in model["nets"])
        named = [p["net"] for m in model["modules"] for p in m["pads"]
                 if p["net"]]
        # 层级原理图板：网名带路径前缀（盘上实测 /GND 形态）
        assert {"net_id": None, "name": "/GND"} in named


def test_real_board_normalized_deterministic_byte_exact():
    """20221018 真实板规范化：确定性 byte-exact；net 行保留 id+name 形态。"""
    text = _board_text("20221018")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rel = MODERN_BOARDS["20221018"][0]
    kw = {"source_path": f"datasets/corpus-r2-r1/raw/{rel}",
          "source_sha256": sha}
    a = cc.normalized_k9_board_text(cc.parse_kicad9_board(text), **kw)
    b = cc.normalized_k9_board_text(cc.parse_kicad9_board(text), **kw)
    assert a == b
    assert "(version 20221018)" in a
    assert f'(sha256 "{sha}")' in a
    assert cc.K9_GENERATOR in a
    assert '(net 0 "")' in a          # 空 0 网如实保留（id 绑定档）
    assert '(net 2 "GND")' in a


def test_real_board_artifact_chain():
    """真实板构件链：stackup/net_registry/topology（stm32 板实测锚）。"""
    text = _board_text("20210424")
    model = cc.parse_kicad9_board(text)
    crit = cc.derive_critical_nets(model)
    assert crit["power_rails"] == ["+3V3", "+5V", "GND"]
    assert crit["diff_pairs"] == []
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    st = cc.build_stackup_obj(model, board_id="stm32-ds2480-emu",
                              source={"path": "s", "sha256": sha})
    assert st["thickness_mm"] == 1.6
    assert [l["name"] for l in st["copper_layers"]] == ["F.Cu", "B.Cu"]
    nr = cc.build_net_registry_obj(model, board_id="stm32-ds2480-emu",
                                   crit=crit)
    assert nr["net_count"] == 30 and nr["named_net_count"] == 29
    cls = {n["name"]: n["classification"] for n in nr["nets"]}
    assert cls["GND"] == "power_rail" and cls["+3V3"] == "power_rail"
    assert cc.topology_group_id(model, crit) == \
        "cu2-29net-28mod-88pad-no-diffpair"


# ---------------------------------------------------------------------------
# 6.x/7.0 档形态：fp_text reference / pad lock flag / 铜层 type 双口径
# ---------------------------------------------------------------------------

def test_fp_text_reference_extraction():
    """6.x/7.0 档 reference 在 fp_text（property 形态不存在于该档真实板）；
    property 形态优先序不变（20241030+ 行为零改动）；两形态皆缺→显式
    __NOREF__ 降级+warning。"""
    text = ('(kicad_pcb (version 20211014) (generator "pcbnew")\n'
            '  (general (thickness 1.6))\n'
            '  (layers (0 "F.Cu" signal))\n'
            '  (footprint "L:Fp" (layer "F.Cu") (at 0 0)\n'
            '    (fp_text "reference" "C7" (at 0 0) (layer "F.SilkS"))\n'
            '    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu")\n'
            '      (net 1 "GND"))\n'
            '  )\n'
            '  (footprint "L:Prop" (layer "F.Cu") (at 1 1)\n'
            '    (property "Reference" "R2" (at 0 0) (layer "F.SilkS"))\n'
            '  )\n'
            '  (footprint "L:NoRef" (layer "F.Cu") (at 2 2)\n'
            '  )\n'
            '  (footprint "L:Old" (layer "F.Cu") (at 3 3)\n'
            '    (fp_text reference U3 (at 0 0) (layer F.SilkS))\n'
            '  )\n'
            ')')
    model = cc.parse_kicad9_board(text)
    assert model["parse_warnings"] == ["footprint_without_reference:L:NoRef"]
    by_ref = {m["ref"]: m["lib"] for m in model["modules"]}
    # __NOREF__ 序号=处理序（第 3 个封装，沿既有 len(modules) 口径）
    assert by_ref == {"C7": "L:Fp", "R2": "L:Prop", "U3": "L:Old",
                      "__NOREF__002": "L:NoRef"}


def test_pad_fourth_positional_lock_flag():
    """6.x/7.0 档 pad 第 4 位置 lock-state flag（'locked'，corpus 实测
    1630/1630 带旗 pad）不扰 name/type/shape 提取。"""
    text = ('(kicad_pcb (version 20210424) (generator "pcbnew")\n'
            '  (general (thickness 1.6))\n'
            '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))\n'
            '  (net 2 "GND")\n'
            '  (footprint "L:C1" (layer "F.Cu") (at 1 2 90)\n'
            '    (fp_text "reference" "C1" (at 0 0) (layer "F.SilkS") hide)\n'
            '    (pad "1" smd roundrect locked (at -0.775 0 90)\n'
            '      (size 0.9 0.95) (layers "F.Cu" "F.Paste" "F.Mask")\n'
            '      (roundrect_rratio 0.25) (net 2 "GND") (pintype passive))\n'
            '  )\n'
            ')')
    model = cc.parse_kicad9_board(text)
    pad = model["modules"][0]["pads"][0]
    assert pad["name"] == "1" and pad["type"] == "smd" \
        and pad["shape"] == "roundrect"
    assert pad["at"] == ["-0.775", "0", "90"]
    assert pad["size"] == ["0.9", "0.95"]
    assert pad["net"] == {"net_id": 2, "name": "GND"}
    assert model["parse_warnings"] == []


def test_copper_type_convention_dual_scope():
    """铜层 type 判据双口径（按档显式，均为盘上实测形态）：
    - 新纳入档（≤20221018）：mixed/power 铜层计入（usb-gigabit 4 铜层、
      kria-k26 8 铜层全为 mixed/power——signal-only 会得出 0 铜层的虚假
      事实）；
    - 既有档（20241030+）：signal-only 零改动（complex_hierarchy
      F.Cu=power 等既有板按该口径产出构件，冻结）。"""
    layers = ('(layers (0 "F.Cu" mixed) (1 "In1.Cu" power) '
              '(31 "B.Cu" mixed) (44 "Edge.Cuts" user))')
    body = ('(general (thickness 1.6))\n  ' + layers + '\n'
            '  (net 1 "GND")\n')
    m_new = cc.parse_kicad9_board(
        f'(kicad_pcb (version 20221018) (generator "pcbnew")\n  {body})')
    assert [l["name"] for l in m_new["copper_layers"]] == \
        ["F.Cu", "In1.Cu", "B.Cu"]
    assert cc.board_denominators(m_new)["copper_layer_count"] == 3
    m_old = cc.parse_kicad9_board(
        f'(kicad_pcb (version 20241229) (generator "pcbnew")\n'
        f'  (generator_version "9.0")\n  {body})')
    # 既有档 signal-only 口径不变（mixed/power 不入铜层集合）
    assert m_old["copper_layers"] == []
    assert cc.board_denominators(m_old)["copper_layer_count"] == 0


# ---------------------------------------------------------------------------
# 红线锚：本扩展不外溢 corpus_convert_ext（档外门保持拒绝）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("token", ("20230408", "1", "2026"))
def test_ext_gate_still_rejects_new_tokens(token):
    """corpus_convert_ext.detect_binding 对档外 token 保持拒绝行为。

    r2 扩档（G2a）：原 NEW_TOKENS 三档（20210424/20211014/20221018）已
    授权追入 ext 档全集（F3 缺口修复；legacy 20171114/"4" 同批追加），
    本锚随授权行为变更同步为「十档全集之外仍拒」——扩档零改既有五档
    行为的 byte 级证明=r1 54 板 FF-EXT 计划 byte-identical 回归钉
    （tests/test_g2a_ffext_r2_extgate.py）。"""
    text = (f'(kicad_pcb (version {token}) (generator "pcbnew")\n'
            f'  (general (thickness 1.6))\n'
            f'  (layers (0 "F.Cu" signal))\n'
            f')')
    with pytest.raises(cce.CorpusExtError, match="不在十档全集"):
        cce.detect_binding(text)
