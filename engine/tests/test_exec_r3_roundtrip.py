# -*- coding: utf-8 -*-
"""EXEC-R3 R3-2 A1 回归钉（pcbflow-optimap EXEC-R3，G1 A 口径；R32-05 面板）。

A1=mask 侧车值权威 + 真正的再出口验证：
- 值保真：mask 补 v5_width_mm（源类宽；Default null=not_available）、空类
  原宽原距、缺类板 Default 单类最小形（原 R5 唯一可信回程载体）；adapter
  严格归属/内容绑定核验后作**值**权威，成员仍取 pro/netclass_assignments，
  空声明只恢复空成员（不发明成员）。
- 再出口：R5>0 拒绝门保留；回读板真正再导出/再解析，净类/成员/R5 稳定
  （仅调用 _validate accepted 不算再出口——本件用 write_kicad_pcb 实做）。
- fail-closed：侧车损坏/错绑/未知版本/缺必要源值/与 pro 声明冲突一律
  AdapterError，不静默回退后报保真；无 mask=真实板路径行为不变。

三板（teres/axiom/anavi）五跑全链值保真账在沙箱脚本登记（R32-04），
本件为仓内常驻最小面。stdlib+pytest；无随机无时钟。
"""
import copy
import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import sidecar  # noqa: E402
from v5.adapters.kicad_adapter import (  # noqa: E402
    AdapterError, convert_bytes, convert_file, convert_file_with_report)
from v5.kicad_export import (  # noqa: E402
    ExportError, kicad_pcb_bytes, netclass_mask_table, project_kicad_pro_bytes,
    write_kicad_pcb)

# 源板（合成，KiCad ≤5 板内块形态）：Default(0.254/0.5，GND)+lvds(0.15/0.14，
# SIG)+hv(1.0/1.0 空成员)；PWR 无类=缺省类。
_SOURCE = """(kicad_pcb
  (version 20171130)
  (layers (0 "F.Cu" signal) (32 "B.Cu" signal))
  (net 0 "")
  (net 1 "GND")
  (net 2 "SIG")
  (net 3 "PWR")
  (net_class "Default" "" (clearance 0.254) (trace_width 0.5) (add_net "GND"))
  (net_class "lvds" "" (clearance 0.15) (trace_width 0.14) (add_net "SIG"))
  (net_class "hv" "" (clearance 1.0) (trace_width 1.0))
  (module A:FP (layer "F.Cu") (at 10 10)
    (pad 1 thru_hole circle (at 0 0) (size 2 2) (drill 0.8) (layers *.Cu) (net 1 GND))
    (pad 2 thru_hole circle (at 5 0) (size 2 2) (drill 0.8) (layers *.Cu) (net 2 SIG)))
  (module B:FP (layer "F.Cu") (at 20 10)
    (pad 1 thru_hole circle (at 0 0) (size 2 2) (drill 0.8) (layers *.Cu) (net 3 PWR)))
)
"""

# 缺类板（teres 形态）：仅 Default 块，无非 Default 类。
_SOURCE_NOCLASS = """(kicad_pcb
  (version 20171130)
  (layers (0 "F.Cu" signal) (32 "B.Cu" signal))
  (net 0 "")
  (net 1 "GND")
  (net_class "Default" "" (clearance 0.127) (trace_width 0.127) (add_net "GND"))
  (module A:FP (layer "F.Cu") (at 10 10)
    (pad 1 thru_hole circle (at 0 0) (size 2 2) (drill 0.8) (layers *.Cu) (net 1 GND)))
)
"""


def _export(board, out_dir, stem="rt"):
    """空 routes 三件导出（A1 链标准形）；返回 pcb 路径。"""
    routes = {"schema_version": "v5.routes.v1", "board_id": board["board_id"],
              "board_sha256": board["provenance"]["board_sha256"],
              "routes": []}
    target = os.path.join(str(out_dir), stem + ".kicad_pcb")
    write_kicad_pcb(board, routes, target)
    return target


def _mask_path(pcb_path):
    return os.path.splitext(pcb_path)[0] + ".netclass-mask.json"


def _rewrite_mask(pcb_path, mutate):
    """读侧车→mutate(doc)→回写（测试破坏注入用）。"""
    with open(_mask_path(pcb_path), encoding="utf-8") as f:
        doc = json.load(f)
    mutate(doc)
    with open(_mask_path(pcb_path), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)


# --------------------------------------------------------------- 值保真主链

def test_a1_value_fidelity_and_empty_class_restore(tmp_path, monkeypatch):
    """A1 主链：回读 R5/类值/成员逐值==源（含空类 hv 原宽原距+members=[]）；
    report 记值权威面；空类不发明成员。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    src = tmp_path / "src.kicad_pcb"
    src.write_text(_SOURCE, encoding="utf-8")
    board1, rep1 = convert_file_with_report(str(src), "a1-src")
    assert rep1["net_class_source"] == "kicad_pcb"
    assert "netclass_mask_value_authority" not in rep1   # 源读无侧车
    pcb = _export(board1, tmp_path / "out")
    board2, rep2 = convert_file_with_report(pcb, "a1-src")
    assert rep2["netclass_mask_value_authority"] is True
    # Default → R5 逐位
    assert board2["hard_rules"]["R5"]["min_clearance_mm"] == 0.254
    # 非空类值+成员（换算前原值，非 [0.0, 0.3] 掩蔽形）
    assert board2["net_classes"]["lvds"] == {
        "clearance_mm": 0.15, "width_mm": 0.14, "members": ["SIG"]}
    # 空声明类恢复：原宽原距 + members=[]（不发明成员）
    assert board2["net_classes"]["hv"] == {
        "clearance_mm": 1.0, "width_mm": 1.0, "members": []}
    assert set(board2["net_classes"]) == {"lvds", "hv"}


def test_a1_missing_class_board_default_r5_restored(tmp_path, monkeypatch):
    """缺类板（teres 形态）也落 mask：Default 单类最小形，回读 R5==源 0.127
    （旧链 0.127→0.0→H5 拒绝，A1 修复面）。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    src = tmp_path / "src2.kicad_pcb"
    src.write_text(_SOURCE_NOCLASS, encoding="utf-8")
    board1, _ = convert_file_with_report(str(src), "a1-noclass")
    assert "net_classes" not in board1
    assert board1["hard_rules"]["R5"]["min_clearance_mm"] == 0.127
    pcb = _export(board1, tmp_path / "out2")
    with open(_mask_path(pcb), encoding="utf-8") as f:
        mask = json.load(f)
    assert set(mask["classes"]) == {"Default"}
    assert mask["classes"]["Default"]["v5_clearance_mm"] == 0.127
    assert mask["classes"]["Default"]["v5_width_mm"] is None   # not_available
    assert mask["empty_net_classes"] == []
    board2, rep2 = convert_file_with_report(pcb, "a1-noclass")
    assert rep2["netclass_mask_value_authority"] is True
    assert board2["hard_rules"]["R5"]["min_clearance_mm"] == 0.127
    assert "net_classes" not in board2


def test_a1_reexport_real_and_idempotent(tmp_path, monkeypatch):
    """再出口实做（非 _validate 探针）：b2 真导出→再解析，净类/成员/R5 稳定；
    R5>0 门自然通过（0.254/0.15 类值下 b2 不再被拒）。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    src = tmp_path / "src.kicad_pcb"
    src.write_text(_SOURCE, encoding="utf-8")
    board1, _ = convert_file_with_report(str(src), "a1-src")
    pcb1 = _export(board1, tmp_path / "o1", "rt1")
    board2, _ = convert_file_with_report(pcb1, "a1-src")
    pcb2 = _export(board2, tmp_path / "o2", "rt2")   # 真 H5'：失败即 ExportError
    board3, _ = convert_file_with_report(pcb2, "a1-src")
    assert board3["hard_rules"]["R5"]["min_clearance_mm"] == \
        board2["hard_rules"]["R5"]["min_clearance_mm"] == 0.254
    assert board3["net_classes"] == board2["net_classes"]


def test_a1_mask_content_binding_and_determinism(tmp_path, monkeypatch):
    """侧车内容绑定三重对上：board_sha256==板 provenance 原模型 hash、
    pcb_sha256/pro_sha256==实际导出件 bytes 摘要；双跑字节等。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    src = tmp_path / "src.kicad_pcb"
    src.write_text(_SOURCE, encoding="utf-8")
    board1, _ = convert_file_with_report(str(src), "a1-src")
    pcb = _export(board1, tmp_path / "out")
    routes = {"schema_version": "v5.routes.v1", "board_id": board1["board_id"],
              "board_sha256": board1["provenance"]["board_sha256"],
              "routes": []}
    m1 = netclass_mask_table(board1, routes)
    m2 = netclass_mask_table(board1, routes)
    assert m1 == m2
    with open(pcb, "rb") as f:
        pcb_bytes = f.read()
    with open(os.path.splitext(pcb)[0] + ".kicad_pro", "rb") as f:
        pro_bytes = f.read()
    doc = json.loads(m1.decode("utf-8"))
    assert doc["board_sha256"] == board1["provenance"]["board_sha256"]
    assert doc["pcb_sha256"] == hashlib.sha256(pcb_bytes).hexdigest()
    assert doc["pro_sha256"] == hashlib.sha256(pro_bytes).hexdigest()
    assert doc["schema_version"] == 2 and doc["rule"] == "netclass-mask-v1"


# --------------------------------------------------------------- 无 mask 旧链

def test_no_mask_old_behavior_unchanged(tmp_path, monkeypatch):
    """无 mask=真实板路径：值仍取换算后 pro 载体（lvds=[0.0,0.3]、空类不
    恢复、R5=pro Default clearance），report 无值权威键——不静默回退。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    src = tmp_path / "src.kicad_pcb"
    src.write_text(_SOURCE, encoding="utf-8")
    board1, _ = convert_file_with_report(str(src), "a1-src")
    pcb = _export(board1, tmp_path / "out")
    os.remove(_mask_path(pcb))
    board2, rep2 = convert_file_with_report(pcb, "a1-src")
    assert "netclass_mask_value_authority" not in rep2
    assert board2["net_classes"]["lvds"] == {
        "clearance_mm": 0.0, "width_mm": 0.3, "members": ["SIG"]}
    assert "hv" not in board2["net_classes"]
    assert board2["hard_rules"]["R5"]["min_clearance_mm"] == 0.0


def test_convert_bytes_pathless_no_mask(tmp_path, monkeypatch):
    """convert_bytes 无路径=看不见侧车/pro（文档化局限）：导出件板内无
    net_class 块 ⇒ 缺省路径（R5=引擎缺省 0.5、无 net_classes）——侧车值
    权威只在 convert_file 路径生效。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    src = tmp_path / "src.kicad_pcb"
    src.write_text(_SOURCE, encoding="utf-8")
    board1, _ = convert_file_with_report(str(src), "a1-src")
    pcb = _export(board1, tmp_path / "out")
    with open(pcb, "rb") as f:
        data = f.read()
    board_nb = convert_bytes(data, "a1-nb", "synthetic://pathless")
    assert board_nb["hard_rules"]["R5"]["min_clearance_mm"] == 0.5
    assert "net_classes" not in board_nb


# --------------------------------------------------------------- fail-closed 面

def _setup_exported(tmp_path, monkeypatch, source=_SOURCE, stem="src"):
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    src = tmp_path / (stem + ".kicad_pcb")
    src.write_text(source, encoding="utf-8")
    board1, _ = convert_file_with_report(str(src), "a1-src")
    return _export(board1, tmp_path / "out")


def test_corrupt_mask_fail_closed(tmp_path, monkeypatch):
    """侧车 JSON 损坏（声明载体在场不可读）→ AdapterError，不静默。"""
    pcb = _setup_exported(tmp_path, monkeypatch)
    with open(_mask_path(pcb), "w", encoding="utf-8") as f:
        f.write("{not json")
    with pytest.raises(AdapterError) as ei:
        convert_file(pcb, "a1-src")
    assert "netclass-mask" in str(ei.value)


@pytest.mark.parametrize("mutate,where", [
    (lambda d: d.__setitem__("schema_version", 1), "schema_version"),
    (lambda d: d.__setitem__("schema_version", 3), "schema_version"),
    (lambda d: d.pop("schema_version"), "schema_version"),
    (lambda d: d.__setitem__("generated_by", "other-tool"), "generated_by"),
    (lambda d: d.__setitem__("rule", "netclass-mask-v2"), "rule"),
])
def test_unknown_version_or_source_fail_closed(tmp_path, monkeypatch,
                                               mutate, where):
    """未知版本/缺版本/导出来源不符 → AdapterError。"""
    pcb = _setup_exported(tmp_path, monkeypatch)
    _rewrite_mask(pcb, mutate)
    with pytest.raises(AdapterError) as ei:
        convert_file(pcb, "a1-src")
    assert where in str(ei.value)


@pytest.mark.parametrize("mutate,where", [
    (lambda d: d["classes"]["Default"].__setitem__("v5_clearance_mm", 0.0),
     "v5_clearance_mm"),
    (lambda d: d["classes"]["Default"].pop("v5_clearance_mm"),
     "v5_clearance_mm"),
    (lambda d: d["classes"]["lvds"].pop("v5_width_mm"), "v5_width_mm"),
    (lambda d: d["classes"]["lvds"].__setitem__("v5_width_mm", None),
     "v5_width_mm"),
    (lambda d: d["empty_net_classes"][0].pop("v5_width_mm"), "v5_width_mm"),
    (lambda d: d["classes"].pop("Default"), "Default"),
])
def test_missing_or_invalid_values_fail_closed(tmp_path, monkeypatch,
                                               mutate, where):
    """缺必要源值/Default R5 非正/缺 Default 项 → AdapterError。"""
    pcb = _setup_exported(tmp_path, monkeypatch)
    _rewrite_mask(pcb, mutate)
    with pytest.raises(AdapterError) as ei:
        convert_file(pcb, "a1-src")
    assert where in str(ei.value)


@pytest.mark.parametrize("mutate,where", [
    (lambda d: d.__setitem__("board_sha256", "0" * 64), "board_sha256"),
    (lambda d: d.__setitem__("pcb_sha256", "0" * 64), "pcb_sha256"),
    (lambda d: d.__setitem__("pro_sha256", "0" * 64), "pro_sha256"),
    (lambda d: d.__setitem__("board_id", "other-board"), "board_id"),
])
def test_misbound_mask_fail_closed(tmp_path, monkeypatch, mutate, where):
    """错绑（原模型 hash/内容摘要/board_id 对不上）→ AdapterError。"""
    pcb = _setup_exported(tmp_path, monkeypatch)
    _rewrite_mask(pcb, mutate)
    with pytest.raises(AdapterError) as ei:
        convert_file(pcb, "a1-src")
    assert where in str(ei.value)


def test_tampered_files_fail_closed(tmp_path, monkeypatch):
    """pcb/pro 被改写后与侧车摘要不符 → AdapterError（内容绑定实义）。"""
    pcb = _setup_exported(tmp_path, monkeypatch)
    pro = os.path.splitext(pcb)[0] + ".kicad_pro"
    with open(pro, "a", encoding="utf-8") as f:
        f.write("\n")            # 内容变了、JSON 仍合法
    with pytest.raises(AdapterError) as ei:
        convert_file(pcb, "a1-src")
    assert "pro_sha256" in str(ei.value)


def test_pro_declaration_conflict_fail_closed(tmp_path, monkeypatch):
    """类名集与 pro 声明冲突（pro 增类且侧车摘要同步改写=双向一致篡改形）
    → AdapterError（内容绑定先拦单侧改写，见 test_tampered_files）。"""
    pcb = _setup_exported(tmp_path, monkeypatch)
    pro = os.path.splitext(pcb)[0] + ".kicad_pro"
    with open(pro, encoding="utf-8") as f:
        doc = json.load(f)
    doc["net_settings"]["classes"].append(
        {"clearance": 0.2, "name": "ghost", "track_width": 0.2})
    with open(pro, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    with open(pro, "rb") as f:
        pro_sha = hashlib.sha256(f.read()).hexdigest()

    def mutate(d):
        d["pro_sha256"] = pro_sha   # 摘要同步改写，穿过内容绑定门
    _rewrite_mask(pcb, mutate)
    with pytest.raises(AdapterError) as ei:
        convert_file(pcb, "a1-src")
    assert "声明冲突" in str(ei.value)


def test_mask_without_pro_fail_closed(tmp_path, monkeypatch):
    """mask 在场而 pro 缺件（导出件三件成套被拆）→ AdapterError。"""
    pcb = _setup_exported(tmp_path, monkeypatch)
    os.remove(os.path.splitext(pcb)[0] + ".kicad_pro")
    with pytest.raises(AdapterError) as ei:
        convert_file(pcb, "a1-src")
    assert "kicad_pro" in str(ei.value)


def test_empty_class_collision_fail_closed(tmp_path, monkeypatch):
    """空声明类与 classes 撞名（结构破坏注入）→ AdapterError。"""
    pcb = _setup_exported(tmp_path, monkeypatch)

    def mutate(d):
        d["empty_net_classes"].append(
            {"name": "lvds", "v5_clearance_mm": 0.5, "v5_width_mm": 0.5,
             "status": "not_available_no_members"})
    _rewrite_mask(pcb, mutate)
    with pytest.raises(AdapterError) as ei:
        convert_file(pcb, "a1-src")
    assert "撞名" in str(ei.value)


# --------------------------------------------------------------- 拒绝门保留

def _board_for_export_gate(tmp_path):
    """已导出板的深拷贝（改 R5=0 触发 exporter 拒绝门）。"""
    src = tmp_path / "src.kicad_pcb"
    src.write_text(_SOURCE, encoding="utf-8")
    board1, _ = convert_file_with_report(str(src), "a1-src")
    bad = copy.deepcopy(board1)
    bad["hard_rules"]["R5"] = {"min_clearance_mm": 0.0}
    bad["provenance"]["board_sha256"] = (
        board1["provenance"]["board_sha256"])   # 深拷贝未变链
    return bad


def test_exporter_r5_positive_gate_preserved(tmp_path, monkeypatch):
    """R5>0 fail-closed 门保留（A1 不放宽门换修复）：R5=0 板四个导出口全拒。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    bad = _board_for_export_gate(tmp_path)
    routes = {"schema_version": "v5.routes.v1", "board_id": bad["board_id"],
              "board_sha256": bad["provenance"]["board_sha256"],
              "routes": []}
    for fn in (kicad_pcb_bytes, project_kicad_pro_bytes, netclass_mask_table):
        with pytest.raises(ExportError) as ei:
            fn(bad, routes)
        assert "R5" in str(ei.value)
    with pytest.raises(ExportError):
        write_kicad_pcb(bad, routes, os.path.join(str(tmp_path), "x.kicad_pcb"))
    assert not os.path.exists(os.path.join(str(tmp_path), "x.kicad_pcb"))
