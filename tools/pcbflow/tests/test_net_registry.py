"""网络注册表（SPEC §1.1/§1.2）测试：全量建档、身份稳定、hash 自洽、structures 绑定。"""

import os

import pytest

from pcbflow import config, envelope, enum_cmd, hashing

INPUTS_OK = all(os.path.exists(p) for p in (config.REVC_NETLIST,
                                            config.LENGTH_REPORT_PY))
pytestmark = pytest.mark.skipif(not INPUTS_OK, reason="Rev-C inputs not present")


@pytest.fixture(scope="module")
def products():
    return enum_cmd.build_products()


def test_registry_full_coverage(products):
    """160 具名网全建档；NC 焊盘网显式 excluded 不丢弃。"""
    reg = products["net_registry"]["obj"]
    im = products["net_identity_map"]["obj"]
    assert len(reg["nets"]) == 160
    assert len(im["assignments"]) == 160
    assert len(im["excluded"]) == 32
    assert len(reg["excluded_nets"]) == 32
    assert all(e["net_name"].startswith("unconnected-") for e in reg["excluded_nets"])


def test_net_ids_stable_sorted(products):
    """net_id 按网名字典序首次分配（N0001..N0160），身份映射一一对应。"""
    reg = products["net_registry"]["obj"]
    names = [r["net_name"] for r in reg["nets"]]
    assert names == sorted(names)
    assert [r["net_id"] for r in reg["nets"]] == \
        ["N%04d" % (i + 1) for i in range(160)]
    by_id = {a["net_id"]: a["net_name"] for a in
             products["net_identity_map"]["obj"]["assignments"]}
    for r in reg["nets"]:
        assert by_id[r["net_id"]] == r["net_name"]


def test_registry_snapshot_hash_self_consistent(products):
    """registry_snapshot_hash = canonical(本字段=null) 的 sha256（自哈希约定）。"""
    reg = dict(products["net_registry"]["obj"])
    reg["registry_snapshot_hash"] = None
    recomputed = hashing.sha256_bytes(hashing.canonical_json_bytes(reg))
    assert products["net_registry"]["obj"]["registry_snapshot_hash"] == recomputed


def test_registry_binds_structures_snapshot(products):
    """§1.2：注册表绑定 structures snapshot hash（权威在 structures，不反向覆盖）。"""
    reg = products["net_registry"]["obj"]
    assert reg["structures_ref"]["sha256"] == products["structures"]["sha256"]
    assert reg["structures_ref"]["path"] == "structures.json"
    assert "draft" in reg["structures_ref"]["authority"]


def test_classification_statuses(products):
    """分类状态：0 歧义/未分类；SIG_DEFAULT 兜底=source_declared；AMB 面=confirmed。"""
    reg = products["net_registry"]["obj"]
    counts = reg["classification_policy"]
    st = {}
    for r in reg["nets"]:
        st[r["classification_status"]] = st.get(r["classification_status"], 0) + 1
    assert st.get("ambiguous", 0) == 0
    assert st.get("unclassified", 0) == 0
    assert st.get("confirmed", 0) == 25  # AMB-1..4 已批裁决面（25 网）
    sd = next(r for r in reg["nets"] if r["net_name"] == "GPIO_PB5")
    assert sd["classification_status"] == "source_declared"  # 兜底行=spec 显式声明
    assert "SIG_DEFAULT" in sd["routing_class"]["source_refs"][0]


def test_relations_resolvable_and_sorted(products):
    """关系对象：成员按 net_id 引用且稳定排序；差分/对称/等长三类齐备。"""
    reg = products["net_registry"]["obj"]
    ids = {r["net_id"] for r in reg["nets"]}
    assert len(reg["relations"]) == 12  # 9 长度组 + 1 差分对 + 2 对称类
    kinds = sorted({v["kind"] for v in reg["relations"].values()})
    assert kinds == ["differential_pair", "length_group", "symmetry_class"]
    for rel in reg["relations"].values():
        assert rel["members"] == sorted(rel["members"])
        assert set(rel["members"]) <= ids
    rdp = reg["relations"]["RDP-USB"]
    assert set(rdp["segments"]) == {"mcu_side", "connector_side"}  # AMB-3 两段


def test_fields_present_per_net(products):
    """SPEC §1.1 逐网字段齐备（含消费视图所需 allowed_layers/via_policy）。"""
    reg = products["net_registry"]["obj"]
    required = ("net_id", "net_name", "aliases", "source_net_key", "structure",
                "electrical_role", "routing_class", "allowed_layers", "via_policy",
                "relation_ids", "endpoints", "classification_status")
    fmc = next(r for r in reg["nets"] if r["net_name"] == "FMC_A12")
    for k in required:
        assert k in fmc, k
    assert fmc["structure"] == {"kind": "bus", "ref": "BUS_FMC"}  # AMB-1 衍生
    assert fmc["allowed_layers"] == ["F.Cu", "In2.Cu"]
    usb = next(r for r in reg["nets"] if r["net_name"] == "USB_DP")
    assert usb["via_policy"]["policy"] == "pair_le_1"  # 整对≤1（C-0005 raw）
    assert usb["relation_ids"] == ["RDP-USB", "RLG-G_USB", "RSYM-usb_pair"]


def test_registry_determinism_and_clean(products):
    again = enum_cmd.build_products()
    for name in ("net_registry", "net_identity_map"):
        assert products[name]["bytes"] == again[name]["bytes"]
        hits = envelope.scan_forbidden_core_fields(products[name]["obj"])
        assert hits == [], (name, hits[:3])
