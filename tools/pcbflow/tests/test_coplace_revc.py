"""③ Rev-C 集成（FB1 sanity 轨）：冻结基线证据评估 + seed 绑定 + canonical
对照 + 转换器往返 byte-exact + 产物卫生。全程只读（p3 快照）。"""

import json

from pcbflow import config, coplace_cmd, envelope

try:
    import pytest
except ImportError:  # pragma: no cover
    pytest = None


def _build():
    return coplace_cmd.build_products("out/revc-b1")


def test_revc_products_contract():
    prods = _build()
    env = prods["envelope"]["obj"]
    L = prods["layout"]["obj"]
    assert env["status"] == "ok"
    assert env["command"] == "co-place"
    assert L["stage"] == 3
    assert L["optimization"]["applied"] is False
    assert L["optimization"]["mode"] == "baseline_frozen_sanity_only"
    assert len(L["placements"]) == 72
    anchors = [p for p in L["placements"] if p["role"] == "anchor_locked"]
    assert len(anchors) == 10
    assert all(not p["moved"] for p in L["placements"])


def test_revc_seed_binding():
    """②→③ 交接绑定：seed 的 registry hash 与重建 registry 一致。"""
    L = _build()["layout"]["obj"]
    assert L["seed_binding"]["bound"] is True
    assert L["registry_consumption"]["registry_consumed"] is True
    assert "allowed_layers" in L["registry_consumption"]["fields_consumed"]


def test_revc_sanity_consistent_with_audit():
    """走廊需求宽与 ② audit 同源一致（读 canonical required_mm；FF-3 修复后三态）。

    历史：out/revc-b1 的 demand_consistent=true 为空比较产物（audit_demand_mm 全
    null），已登记缺陷不回写；本断言在修复后语义下=七走廊真值比对全 consistent。
    """
    L = _build()["layout"]["obj"]
    rows = L["sanity_vs_audit"]["rows"]
    assert len(rows) == 7
    assert all(r["demand_consistent"] == "consistent" for r in rows)
    assert all(r["audit_demand_mm"] is not None for r in rows)  # 真值非空（§8.3）


def test_revc_canonical_comparison_g1():
    """通道口径对齐 canonical G1：FMC 净空与 gates-p3.json 差 ≤0.05mm。"""
    L = _build()["layout"]["obj"]
    rows = {r["canonical_gate"]: r for r in L["canonical_comparison"]["rows"]}
    g1 = rows["G1_channel"]
    assert g1["agreement"] is True
    assert abs(g1["canonical"]["channel_mm"] - g1["ours"]["gap_mm"]) <= 0.05
    # G1 历史 pass ⇒ ③ 通道门在冻结基线上同为 pass
    assert L["evidence"]["hard_gates"]["channel_budget"]["pass"] is True
    for gate in ("G4_orientation", "G6_zone_purity"):
        assert rows[gate]["agreement"] is True


def test_revc_csv_roundtrip_byte_exact():
    """p3 CSV 导入副本 → 转换器 → 与源文件逐字节一致（可重放证明）。"""
    prods = _build()
    rt = prods["conversion"]["obj"]["roundtrip_proof"]
    assert rt["byte_exact_vs_source"] is True
    assert rt["source_sha256"] == rt["roundtrip_sha256"]


def test_revc_deterministic_products():
    """同输入双跑：核心产物 byte-exact（run_manifest 除外——wall-clock 设计如此）。"""
    a = _build()
    b = _build()
    for k in ("layout", "geojson", "layer_plan", "placement_csv", "conversion"):
        assert a[k]["bytes"] == b[k]["bytes"], k
    from pcbflow import hashing
    ea = hashing.canonical_json_bytes(a["envelope"]["obj"])
    eb = hashing.canonical_json_bytes(b["envelope"]["obj"])
    assert ea == eb


def test_revc_hygiene():
    """产物卫生：核心产物无禁区键/绝对路径；快照差异如实列账。"""
    prods = _build()
    L = prods["layout"]["obj"]
    assert envelope.scan_forbidden_core_fields(L) == []
    assert envelope.scan_forbidden_core_fields(prods["geojson"]["obj"]) == []
    # 快照卫生发现（板 vs CSV 不一致件）如实记录且不自动套用
    assert L["baseline_deltas"]["count"] == len(L["baseline_deltas"]["rows"])
    refs = {d["ref"] for d in L["baseline_deltas"]["rows"]}
    assert "CRTC" in refs  # 已知差异件
    for d in L["baseline_deltas"]["rows"]:
        assert d["board"] != d["csv"]
