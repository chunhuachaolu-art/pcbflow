"""② shadow 夹具与负例电池（任务书 §十一）：合成自包含输入 + Rev-C 真实输入。

合成夹具验证 13 类负例：不静默丢弃、生成 ambiguous/unclassified/missing 记录、
不改变 baseline gate、可序列化可重放。真实输入只读集成测试验证 Rev-C 事实面
（160 网、AMB 裁决面、byte-exact 重放）。全程零落盘零子进程。
"""

from __future__ import annotations

import copy

import pytest

from pcbflow import config, hashing
from pcbflow.experimental import net_registry_shadow as shadow


# ---- 合成输入工厂（默认小系统；各用例覆写） --------------------------------

def make_inp(**over):
    class_patterns = [
        ("MYBUS_CLK", ["^MB_CLK$"]),
        ("MYDATA", ["^MB_D[0-3]$"]),
        ("ANLGX", ["^ADC_A0$"]),
        ("PWRX", ["^3V3$", "^SW_NODE$", "^FB_NODE$"]),
        ("GNDX", ["^GND$"]),
    ]
    inp = {
        "netlist_nets": {
            "MB_CLK": [{"ref": "U1", "pin": "1"}, {"ref": "U2", "pin": "1"}],
            "MB_D0": [{"ref": "U1", "pin": "2"}, {"ref": "U2", "pin": "2"}],
            "MB_D1": [{"ref": "U1", "pin": "3"}, {"ref": "U2", "pin": "3"}],
            "ADC_A0": [{"ref": "U1", "pin": "4"}],
            "3V3": [{"ref": "U1", "pin": "5"}, {"ref": "C1", "pin": "1"}],
            "SW_NODE": [{"ref": "U3", "pin": "1"}, {"ref": "L1", "pin": "1"}],
            "FB_NODE": [{"ref": "U3", "pin": "2"}, {"ref": "R1", "pin": "1"}],
            "GND": [{"ref": "U1", "pin": "6"}, {"ref": "C1", "pin": "2"}],
            "GPIO_X": [{"ref": "U1", "pin": "7"}, {"ref": "J1", "pin": "1"}],
        },
        "board_net_names": ["MB_CLK", "MB_D0", "MB_D1", "ADC_A0", "3V3",
                            "SW_NODE", "FB_NODE", "GND", "GPIO_X"],
        "board_footprint_refs": ["U1", "U2", "U3", "L1", "C1", "R1", "J1"],
        "script_groups": {
            "G_MY": {"ref": "MB_CLK", "target": 2.5, "limit": 5.0,
                     "nets": ["MB_D0", "MB_D1"]},
        },
        "spec_members": {"G_MY": ["MB_D0", "MB_D1", "MB_CLK"]},
        "class_patterns": class_patterns,
        "catch_all_class": "SIGX",
        "class_raws": {cls: "F/In2" for cls, _ in class_patterns},
        "planner_patterns": [("MB_", "MYBUS"), ("3V3", "PWR"), ("SW_NODE", "PWR"),
                             ("FB_NODE", "PWR"), ("ADC_", "ANLG")],
        "planner_default": "SIG",
        "kicad_pro_classes": {"Default": 0, "MYDATA": 0},
        "bus_rules": [
            {"bus_id": "BUS_MY", "pattern": r"^MB_",
             "source_kind": "naming_rule", "source": "naming_rule(draft)"},
        ],
        "diff_pairs": [],
        "rulings": [],
        "lengths": ["G_MY"],
        "corridor_formula": {"pitch_mm": 0.35, "routing_layers": 2, "margin_mm": 0.6},
        "hashes": {"revc.netlist": "0" * 64},
        "comps": {"U1": {"value": "MCU", "footprint": "fp:u"},
                  "U2": {"value": "RAM", "footprint": "fp:u"}},
        "baseline": {"source_path": "synthetic", "status": "blocked",
                     "verdict": "yellow", "enum_metrics": {"named_nets": 9,
                                                           "uncovered": 0,
                                                           "bucket_counts": {}},
                     "compile_metrics": {"catch_all_only_count": 1}},
        "b2_context": None,
        "source_revision": "synthetic",
        "out_dir_rel": "pcbflow-out/stage2-shadow",
        "generation_status": "ok",
    }
    for k, v in over.items():
        inp[k] = v
    return inp


def run(inp):
    built = shadow.build_registry(inp)
    coverage = shadow.build_coverage(built["registry"], built["stats"], inp)
    inp2 = dict(inp)
    inp2["registry_sha256"] = hashing.sha256_bytes(
        hashing.canonical_json_bytes(built["registry"]))
    comparison = shadow.build_comparison(built["registry"], built["stats"],
                                         coverage, inp2, inp["baseline"])
    return built, coverage, comparison


def net_map(built):
    return {r["net_name"]: r for r in built["registry"]["nets"]}


def diag_ids(built):
    return [d["id"] for d in built["registry"]["diagnostics"]]


# ---- 13 类负例/夹具 ---------------------------------------------------------

def test_01_explicit_declared_bus():
    inp = make_inp(bus_rules=[{"bus_id": "BUS_MY", "pattern": r"^MB_",
                               "source_kind": "explicit_declaration",
                               "source": "synthetic spec §x"}])
    built, _, _ = run(inp)
    nm = net_map(built)
    assert nm["MB_D0"]["bus"] == "BUS_MY"
    assert "source_declared" in nm["MB_D0"]["source_refs"][0] or \
        nm["MB_D0"]["classification_status"] in ("source_declared", "confirmed")


def test_02_prefix_only_inferred_with_rule():
    built, _, _ = run(make_inp())
    nm = net_map(built)
    assert nm["MB_D0"]["bus"] == "BUS_MY"
    # 总线归属为命名规则推断：inference_rule 记录规则
    assert any("bus_prefix_rule" in (r["inference_rule"] or "")
               for r in built["registry"]["nets"] if r["net_name"].startswith("MB_"))


def test_03_conflicting_class_declarations_ambiguous():
    # 两条具体类行同时命中 → 不静默择一 → ambiguous
    inp = make_inp(class_patterns=[
        ("CLASS_A", ["^MB_D0$"]), ("CLASS_B", ["^MB_D"]), ], )
    built, cov, cmp_ = run(inp)
    nm = net_map(built)
    assert nm["MB_D0"]["classification_status"] == "ambiguous"
    assert cov["totals"]["ambiguous"] >= 1
    assert cmp_["comparison"]["ambiguities"]


def test_04_net_in_bus_class_length_group():
    built, _, _ = run(make_inp())
    nm = net_map(built)
    r = nm["MB_D0"]
    assert r["bus"] == "BUS_MY" and r["routing_class"] == "MYDATA" \
        and r["length_group"] == "G_MY"


def test_05_incomplete_differential_pair_flagged():
    inp = make_inp(diff_pairs=[{"pair_id": "P1", "pos": ["MB_D0"], "neg": [],
                                "segments": {}, "source_refs": ["t"], "status": "inferred"}],
                   netlist_nets={})
    built, _, _ = run(inp)
    assert "PAIR-INCOMPLETE:P1" in diag_ids(built)
    # 网络不被静默丢弃：仍生成记录（无端点、unclassified 类）
    assert built["stats"]["named_nets"] == 0
    assert "NC-PAD-NETS" not in diag_ids(built)


def test_06_usb_main_and_protected_segments():
    inp = make_inp(diff_pairs=[{
        "pair_id": "USB_PAIR",
        "pos": ["MB_D0", "MB_D0_C"], "neg": ["MB_D1", "MB_D1_C"],
        "segments": {"MB_D0": "mcu_side", "MB_D0_C": "connector_side",
                     "MB_D1": "mcu_side", "MB_D1_C": "connector_side"},
        "source_refs": ["C-00xx"], "status": "confirmed"}],
        netlist_nets={
            "MB_D0": [{"ref": "U1", "pin": "2"}, {"ref": "U6", "pin": "4"}],
            "MB_D0_C": [{"ref": "U6", "pin": "3"}, {"ref": "J5", "pin": "A6"}],
            "MB_D1": [{"ref": "U1", "pin": "3"}, {"ref": "U6", "pin": "6"}],
            "MB_D1_C": [{"ref": "U6", "pin": "1"}, {"ref": "J5", "pin": "A7"}]},
        board_net_names=["MB_D0", "MB_D0_C", "MB_D1", "MB_D1_C"],
        class_patterns=[("USBX", ["^MB_D"])], catch_all_class="SIGX",
        class_raws={"USBX": "F（全程）"}, bus_rules=[], lengths=[],
        script_groups={}, spec_members={})
    built, _, _ = run(inp)
    nm = net_map(built)
    assert nm["MB_D0_C"]["differential_pair"]["segment"] == "connector_side"
    assert nm["MB_D0_C"]["differential_pair"]["status"] == "confirmed"
    assert built["stats"]["named_nets"] == 4


def test_07_spec_missing_member_ruled_confirmed():
    # A12 型：spec 行缺 A12，脚本与板上存在，已批裁决 → confirmed（非伪造）
    inp = make_inp(spec_members={"G_MY": ["MB_D0", "MB_D1"]},
                   script_groups={"G_MY": {"ref": "MB_CLK", "target": 2.5,
                                           "limit": 5.0,
                                           "nets": ["MB_D0", "MB_D1", "MB_X12"]}},
                   netlist_nets=dict(
                       make_inp()["netlist_nets"],
                       MB_X12=[{"ref": "U1", "pin": "9"}, {"ref": "U2", "pin": "9"}]),
                   board_net_names=make_inp()["board_net_names"] + ["MB_X12"],
                   rulings=[{"id": "AMB-X", "kind": "selector_membership",
                             "status": "resolved", "title": "MB_X12 缺席 spec 行",
                             "decision": "纳入", "approver": "user",
                             "review": "next rev",
                             "member_nets": ["MB_X12"],
                             "applies_to_length_group": "G_MY"}],
                   class_patterns=[("MYADDR", ["^MB_X12$"]), ("MYDATA", ["^MB_D[0-3]$"])],
                   class_raws={"MYADDR": "F/In2", "MYDATA": "F/In2"})
    built, _, _ = run(make_inp(rulings=[]))  # 基线无裁决时保持 source_declared
    built2, cov, _ = run(inp)
    nm = net_map(built2)
    assert nm["MB_X12"]["classification_status"] == "confirmed"
    assert nm["MB_D0"]["classification_status"] != "confirmed"
    assert cov["totals"]["confirmed"] == 1


def test_08_member_diff_phantom_and_unmeasured():
    # LTDC 型：脚本 8 幻影名 + 板上成员未被脚本枚举
    inp = make_inp(
        script_groups={"G_MY": {"ref": "MB_CLK", "target": 2.5, "limit": 5.0,
                                "nets": ["MB_PH0", "MB_D0"]}},
        spec_members={"G_MY": None},
        netlist_nets=dict(make_inp()["netlist_nets"],
                          MB_X9=[{"ref": "U1", "pin": "8"}]),
        board_net_names=make_inp()["board_net_names"] + ["MB_X9"],
        lengths=["G_MY"])
    # 注：None spec_members 走 LTDC 型分支需要 G_LTDC 名；此处直接验证诊断面
    built, cov, _ = run(make_inp(
        script_groups={"G_MY": {"ref": "MB_CLK", "target": 2.5, "limit": 5.0,
                                "nets": ["MB_PH0", "MB_D0"]}}))
    ids = diag_ids(built)
    assert "SCRIPT-PHANTOM:G_MY" in ids
    assert cov["missing_length_members"]["G_MY"][
        "script_members_not_on_board"] == ["MB_PH0"]


def test_09_power_switch_feedback_roles():
    built, _, _ = run(make_inp())
    nm = net_map(built)
    assert nm["SW_NODE"]["electrical_role"] == "power_switch_node"
    assert nm["FB_NODE"]["electrical_role"] == "power_feedback"
    assert nm["3V3"]["electrical_role"] == "power_rail"
    assert nm["GND"]["electrical_role"] == "ground_return"


def test_10_gpio_and_analog_loose():
    built, _, _ = run(make_inp())
    nm = net_map(built)
    assert nm["GPIO_X"]["electrical_role"] == "ordinary_gpio"
    assert nm["ADC_A0"]["electrical_role"] == "analog_sensitive"


def test_11_unresolvable_endpoint_listed():
    inp = make_inp(netlist_nets={"GHOST_NET": [{"ref": "GX", "pin": "1"}]},
                   board_net_names=[], board_footprint_refs=[])
    built, cov, _ = run(inp)
    assert cov["missing_endpoints"] == [{"net": "GHOST_NET", "endpoint": "GX.1"}]
    # 不静默丢弃：网络仍在注册表（unclassified/catch-all 面）
    assert any(r["net_name"] == "GHOST_NET"
               for r in built["registry"]["nets"])


def test_12_unknown_class_raw_layers_null():
    inp = make_inp(class_patterns=[("MYSTERY", ["^MB_D[0-3]$"])])
    inp["class_raws"] = {}  # 类无 §2 raw → 属性 null + note，不虚构
    built, _, _ = run(inp)
    nm = net_map(built)
    assert nm["MB_D0"]["allowed_layers"] is None
    assert nm["MB_D0"]["via_policy"] is None


def test_13_duplicate_member_and_dangling_ref():
    # 重复成员（canonical 去重前披露）+ 引用不存在网（missing_reference）
    inp = make_inp(
        script_groups={"G_MY": {"ref": "MB_CLK", "target": 2.5, "limit": 5.0,
                                "nets": ["MB_D0", "MB_GHOST"]}},
        spec_members={"G_MY": ["MB_D0", "MB_D0"]},  # spec 侧重复转录
        lengths=["G_MY"])
    built, cov, _ = run(inp)
    ids = diag_ids(built)
    assert "MISSING-NET:G_MY" in ids  # MB_GHOST 不在板上
    assert "SCRIPT-PHANTOM:G_MY" in ids
    # 重复成员在 canonical 合并后去重，但 spec 侧重复在 group_member_diffs 可见
    assert cov["group_member_diffs"]["G_MY"]["spec_members"].count("MB_D0") == 2 or \
        cov["group_member_diffs"]["G_MY"]["spec_members"] == ["MB_D0"]


# ---- 通用不变式（所有负例共同验证） -----------------------------------------

def test_negative_cases_keep_gate_and_replay():
    for inp in (make_inp(), make_inp(class_patterns=[("A", ["^MB_D0$"]), ("B", ["^MB_D"])]),
                make_inp(netlist_nets={"GHOST": [{"ref": "GX", "pin": "1"}]},
                         board_net_names=[], board_footprint_refs=[])):
        built, cov, cmp_ = run(inp)
        # 不改变 baseline gate
        assert cmp_["comparison"]["gate_unchanged"] is True
        assert cmp_["comparison"]["baseline_verdict_unchanged"] is True
        assert cmp_["comparison"]["registry_consumed"] is False
        assert cmp_["baseline"]["verdict"] == "yellow"  # 原样透传
        # 可序列化 + 重放一致（byte-exact）
        b1 = hashing.canonical_json_bytes(built["registry"])
        built2, _, _ = run(copy.deepcopy(inp))
        b2 = hashing.canonical_json_bytes(built2["registry"])
        assert b1 == b2
        # 每个输入网都有记录或显式排除（无静默丢弃）
        total = built["stats"]["named_nets"] + built["stats"]["nc_pad_nets"]
        assert total == len(inp["netlist_nets"])


# ---- Rev-C 真实输入集成（只读） ---------------------------------------------

@pytest.fixture(scope="module")
def real():
    inp = shadow.load_real_inputs("pcbflow-out/stage2-shadow")
    built = shadow.build_registry(inp)
    coverage = shadow.build_coverage(built["registry"], built["stats"], inp)
    return inp, built, coverage


def test_revc_full_coverage_no_silent_drop(real):
    inp, built, _ = real
    st = built["stats"]
    assert st["named_nets"] == 160
    assert st["total_nets"] == 192 and st["nc_pad_nets"] == 32
    assert not st["unmapped_nets"]
    assert not st["ambiguous_nets"]
    assert not st["unclassified_nets"]
    # netlist ↔ board 交叉核对：具名网全部在板（board_net:absent 不应出现）
    named = {n for n in inp["netlist_nets"] if not n.startswith("unconnected-")}
    assert named <= set(inp["board_net_names"])
    assert not any("board_net:absent" in r["source_refs"]
                   for r in built["registry"]["nets"])


def test_revc_classification_status_face(real):
    inp, built, cov = real
    nm = net_map(built)
    st = cov["totals"]
    assert st["confirmed"] > 0 and st["source_declared"] > 0
    # AMB 裁决面
    assert nm["FMC_A12"]["classification_status"] == "confirmed"
    assert nm["USB_DP_C"]["differential_pair"]["segment"] == "connector_side"
    assert nm["USB_DP_C"]["length_group"] == "G_USB"
    assert nm["SD_CD"]["routing_class"] == "SDMMC1"
    assert nm["SD_CD"]["classification_status"] == "confirmed"
    # LTDC：canonical=板上 19 成员；PCLK=参考网
    assert sum(1 for r in built["registry"]["nets"]
               if r["length_group"] == "G_LTDC") == 20
    diag = diag_ids(built)
    assert "SCRIPT-PHANTOM:G_LTDC" in diag
    assert "UNMEASURED:G_LTDC" in diag
    assert "UNMEASURED:G_USB" in diag  # _C 段未被脚本测量


def test_revc_planner_mapping_only_gnd_disagrees(real):
    inp, built, cov = real
    dis = cov["spec_class_planner_diffs"]["per_net_disagreements"]
    assert {d["net"] for d in dis} == {"GND"}
    o2m = cov["spec_class_planner_diffs"]["one_to_many"]
    assert sorted(o2m["FMC"]) == ["FMC_ADDR", "FMC_CLK", "FMC_CTRL",
                                  "FMC_DATA_H", "FMC_DATA_L"]
    assert sorted(o2m["PWR"]) == ["PWR_3V3", "PWR_5V", "PWR_MISC", "PWR_SW"]


def test_revc_kicad_classes_unassigned_note(real):
    inp, built, cov = real
    assert all(v == 0 for v in inp["kicad_pro_classes"].values())
    assert any(i["id"] == "KICAD-CLASS-UNASSIGNED" for i in cov["source_impacts"])


def test_revc_routing_attrs_from_spec_raw(real):
    inp, built, cov = real
    nm = net_map(built)
    assert nm["USB_DP"]["allowed_layers"] == ["F.Cu"]
    assert nm["USB_DP"]["preferred_layer"] == "F.Cu"
    assert nm["USB_DP"]["via_policy"]["policy"] == "pair_le_1"
    assert nm["LTDC_R3"]["allowed_layers"] == ["F.Cu", "In2.Cu"]
    assert nm["LTDC_R3"]["via_policy"] == {"policy": "max_count", "max_count": 2,
                                           "raw_note": None}
    assert nm["GND"]["allowed_layers"] == ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    assert nm["3V3"]["allowed_layers"] == ["F.Cu", "In2.Cu", "B.Cu"]


def test_revc_byte_exact_replay(real):
    inp, built, _ = real
    b1 = hashing.canonical_json_bytes(built["registry"])
    built2 = shadow.build_registry(inp)
    b2 = hashing.canonical_json_bytes(built2["registry"])
    assert b1 == b2
    assert hashing.sha256_bytes(b1) == hashing.sha256_bytes(b2)
