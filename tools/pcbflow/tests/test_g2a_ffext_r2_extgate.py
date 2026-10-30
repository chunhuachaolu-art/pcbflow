"""G2a corpus-r2 预测侧扩档回归测试（G 线 r2 包 G2a）。

三层：
  A. 单元级（自足小夹具）——十档绑定路由/铜层按档三口径/绑定档错配
     精确化（名档两 token 数字串=未命名网合法、三 token id 引用照拒）/
     legacy module 板全链/待决① 双口径修复/F1 记录源正负向；
  B. 真实板探针级（datasets 只读）——扩档 17 板逐板解除实证、R8 逐层
     对账全过（对 G1 FF-CORPUS 计划）、待决① 真板 sum==bound；
  C. 批产物级（读 out/v3-gline-r2/ffext-r2/ 与 profiles/corpusr2-*/
     盘面，中间态缺产物 pytest.skip，完工后全过）——37 板计划在盘与
     byte-exact 重算、batch-summary 计数与治理段、**r1 面 54 板
     ffext-r1 计划 byte-identical 回归钉**（扩档零改既有行为的证明）、
     r1 冻结产物 hash 零变化。

datasets/ 只读；既有测试/产物零改动。
"""

from __future__ import annotations

import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from pcbflow import corpus_convert as cc  # noqa: E402
from pcbflow import corpus_convert_ext as cce  # noqa: E402
from pcbflow import hashing  # noqa: E402
from pcbflow import sexpr_min  # noqa: E402

FFEXT_R2 = os.path.join(REPO, "out", "v3-gline-r2", "ffext-r2")
FFEXT_R1 = os.path.join(REPO, "out", "v3-ext-r1", "ffext-r1")
DS_MANIFEST = os.path.join(REPO, "datasets", "corpus-r2-r1",
                           "manifest.json")

#: datasets manifest 的 corpus-r2 版本桶 → 板数（提案 §2.2 权威口径）
BUCKET_COUNTS = {"20241229": 7, "20260206": 4, "20171130": 9,
                 "20211014": 5, "20221018": 9, "20210424": 1,
                 "20171114": 1, "4": 1}
#: 扩档批新增桶（F3 前为 CorpusExtError 的 17 板）
EXPANDED_BUCKETS = ("20210424", "20211014", "20221018", "20171114", "4")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _ds_manifest():
    return _load(DS_MANIFEST)


def _board_rel(bdict):
    pcb = [f for f in bdict["files"] if f.endswith(".kicad_pcb")]
    assert len(pcb) == 1
    return "datasets/corpus-r2-r1/" + bdict["dir"] + "/" + pcb[0]


def _board_text(bdict):
    with open(os.path.join(REPO, _board_rel(bdict)),
              encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# A1. 绑定路由十档 + 档外拒
# ---------------------------------------------------------------------------

def test_detect_binding_ten_versions_and_reject_unknown():
    id_boards = ("20171130", "20210424", "20211014", "20221018",
                 "20241030", "20241229", "20171114", "4")
    for v in id_boards:
        assert cce.detect_binding(
            f'(kicad_pcb (version {v}) (host "t"))') == "net_id_bound"
    for v in ("20260206", "20260624"):
        assert cce.detect_binding(
            f'(kicad_pcb (version {v}) (host "t"))') == "net_name_bound"
    for bad in ("20230408", "1", "2026"):
        with pytest.raises(cce.CorpusExtError):
            cce.detect_binding(f'(kicad_pcb (version {bad}))')
    with pytest.raises(cce.CorpusExtError):
        cce.detect_binding("(kicad_pcb (host \"nov\"))")  # 缺 version
    assert len(cce.ALL_VERSIONS) == 10


# ---------------------------------------------------------------------------
# A2. 铜层判据按档三口径（mixed/power 板教训：≤20221018 白名单）
# ---------------------------------------------------------------------------

_LAYER_TABLE = ('(kicad_pcb (version {v}) (generator "t")\n'
                '  (layers (0 "F.Cu" {t0}) (1 "In1.Cu" {t1})\n'
                '          (31 "B.Cu" {t2}) (32 "B.Adhes" user))\n'
                '  (footprint "L:Fp" (layer "F.Cu") (at 0 0)\n'
                '    (property "Reference" "R1" (at 0 0))\n'
                '    (pad "1" smd rect (at 0 0) (size 1 1)\n'
                '      (layers "F.Cu") (net 1 "GND"))))\n')


def test_copper_layers_three_regimes_by_version():
    # 同一层表（F=mixed, In1=power, B=signal）：
    mixed_table = dict(t0="mixed", t1="power", t2="signal")
    # 6.x/7.0 新纳入档：K9_MODERN_COPPER_TYPES 白名单（mixed/power 计入）
    geo_new = cce.extract_pad_geometry(
        _LAYER_TABLE.format(v="20211014", **mixed_table))
    assert [l["name"] for l in geo_new["copper_layers"]] == \
        ["F.Cu", "In1.Cu", "B.Cu"]
    # 20241030+ 既有档：signal-only 零改动（mixed/power 排除）
    geo_old = cce.extract_pad_geometry(
        _LAYER_TABLE.format(v="20241229", **mixed_table))
    assert [l["name"] for l in geo_old["copper_layers"]] == ["B.Cu"]
    # KiCad4/5 层编号档（legacy 20171114）：index 0..31 判据（裸 token）
    legacy_text = ('(kicad_pcb (version 20171114) (host pcbnew "x")\n'
                   '  (layers\n    (0 F.Cu mixed)\n    (1 In1.Cu power)\n'
                   '    (31 B.Cu mixed)\n    (32 B.Adhes user hide))\n'
                   '  (module "L:M" (layer F.Cu) (at 0 0)\n'
                   '    (fp_text reference "C1" (at 0 0))\n'
                   '    (pad "1" smd rect (at 0 0) (size 1 1)\n'
                   '      (layers "F.Cu") (net 1 "GND"))))\n')
    geo_leg = cce.extract_pad_geometry(legacy_text)
    assert [l["name"] for l in geo_leg["copper_layers"]] == \
        ["F.Cu", "In1.Cu", "B.Cu"]
    assert geo_leg["binding"] == "net_id_bound"
    # 白名单判据单一事实源：ext 模块引用 corpus_convert 常量（同值）
    assert cc.K9_MODERN_COPPER_TYPES == \
        ("signal", "mixed", "power", "jumper")
    assert cce.EXT_MODERN_COPPER_VERSIONS == \
        ("20210424", "20211014", "20221018")
    assert cce.K5_MODULE_VERSIONS == ("20171130", "20171114", "4")


def test_binding_mismatch_refined_two_token_numeric_is_named_net():
    # 名档两 token `(net "100")` = KiCad10 未命名网（网名字面量数字串）
    # ——按名读（与 parse_kicad9_board 两 token 分支同判；om-flexgrid
    # 实板形态，r1 名档板未暴露）。
    text = ('(kicad_pcb (version 20260206) (generator "t")\n'
            '  (layers (0 "F.Cu" signal))\n'
            '  (footprint "L:Fp" (layer "F.Cu") (at 0 0)\n'
            '    (property "Reference" "U1" (at 0 0))\n'
            '    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu")\n'
            '      (net "100"))\n'
            '    (pad "2" smd rect (at 1 0) (size 1 1) (layers "F.Cu")\n'
            '      (net "100"))))\n')
    geo = cce.extract_pad_geometry(text)
    keys = {p["net_key"] for p in geo["pads"]}
    assert keys == {"100"}
    assert all(p["net"] == "100" for p in geo["pads"])
    # 名档三 token 数字 id 引用形态 = 真绑定档错配 → 照拒（不放宽）
    bad = ('(kicad_pcb (version 20260206) (generator "t")\n'
           '  (layers (0 "F.Cu" signal))\n'
           '  (footprint "L:Fp" (layer "F.Cu") (at 0 0)\n'
           '    (property "Reference" "U1" (at 0 0))\n'
           '    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu")\n'
           '      (net 5 "GND"))))\n')
    with pytest.raises(cce.CorpusExtError):
        cce.extract_pad_geometry(bad)
    # id 档出现名 token → 照拒（既有判据，新档实例）
    bad2 = ('(kicad_pcb (version 20211014) (generator "t")\n'
            '  (layers (0 "F.Cu" signal))\n'
            '  (footprint "L:Fp" (layer "F.Cu") (at 0 0)\n'
            '    (property "Reference" "U1" (at 0 0))\n'
            '    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu")\n'
            '      (net "GND"))))\n')
    with pytest.raises(cce.CorpusExtError):
        cce.extract_pad_geometry(bad2)


# ---------------------------------------------------------------------------
# A3. legacy 两档 module 板全链（合成夹具）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("version", ["20171114", "4"])
def test_legacy_module_board_full_chain(version):
    text = (f'(kicad_pcb (version {version}) (host pcbnew "x")\n'
            '  (layers\n    (0 F.Cu signal)\n    (31 B.Cu signal)\n'
            '    (32 B.Adhes user hide))\n'
            '  (net 0 "")\n'
            '  (net 1 +5V)\n'
            '  (module "L:M1" (layer F.Cu) (at 1 2)\n'
            '    (fp_text reference "C1" (at 0 0))\n'
            '    (pad "1" thru_hole circle (at 0 0) (size 1.5 1.5)\n'
            '      (drill 0.8) (layers "*.Cu" "*.Mask") (net 1 +5V))\n'
            '    (pad "2" thru_hole circle (at 2 0) (size 1.5 1.5)\n'
            '      (drill 0.8) (layers "*.Cu" "*.Mask") (net 1 +5V)))\n'
            '  (module "L:M2" (layer F.Cu) (at 5 5)\n'
            '    (fp_text reference "R1" (at 0 0))\n'
            '    (pad "1" smd rect (at 0 0) (size 1 1)\n'
            '      (layers "F.Cu") (net 2 GND))))\n')
    geo = cce.extract_pad_geometry(text)
    assert geo["binding"] == "net_id_bound"
    assert geo["board_version"] == version
    assert sorted(geo["footprints"]) == ["C1", "R1"]
    assert len(geo["pads"]) == 3
    # 同网联名一致性（(net 1 +5V) 无引号形态）
    vplus = [p for p in geo["pads"] if p["net"] == "+5V"]
    assert len(vplus) == 2 and all(p["net_key"] == 1 for p in vplus)
    # escape / layer_capacity 全链可算
    esc = cce.estimate_escape_slots(geo)
    cap = cce.estimate_layer_capacity(geo)
    assert esc["estimable"] and cap["estimable"]


# ---------------------------------------------------------------------------
# A4. 待决① 手术：build_net_registry_obj 双口径
# ---------------------------------------------------------------------------

def _pd_model():
    """合成 pad_derived 模型（20260206 形态：net_id=None、按名）。"""
    return {
        "net_declaration_source": "pad_derived",
        "nets": [{"net_id": None, "name": "/GND"},
                 {"net_id": None, "name": "+3V3"}],
        "modules": [
            {"ref": "C1", "pads": [
                {"name": "1", "net": {"net_id": None, "name": "/GND"}},
                {"name": "2", "net": {"net_id": None, "name": "+3V3"}}]},
            {"ref": "C2", "pads": [
                {"name": "1", "net": {"net_id": None, "name": "/GND"}},
                {"name": "2", "net": None}]},
        ],
    }


def test_net_registry_pad_derived_grouped_by_name():
    nr = cc.build_net_registry_obj(_pd_model(), board_id="t",
                                   crit={"power_rails": ["+3V3"],
                                         "diff_pairs": []})
    by_name = {n["name"]: n["pad_count"] for n in nr["nets"]}
    # 修复前：net_id 全 None 单桶 → 每网 pad_count=2（全部绑网 pad）
    # 修复后：按名分组 → /GND=2、+3V3=1
    assert by_name == {"/GND": 2, "+3V3": 1}
    assert sum(n["pad_count"] for n in nr["nets"]) == 3
    refs = {n["name"]: n["member_refs"] for n in nr["nets"]}
    assert refs["/GND"] == ["C1.1", "C2.1"]


def test_net_registry_id_bound_unchanged_by_surgery():
    """id 档模型（k5 形态：无 net_declaration_source 键）零改动。"""
    model = {
        "nets": [{"net_id": 0, "name": ""},
                 {"net_id": 1, "name": "GND"},
                 {"net_id": 2, "name": "+5V"}],
        "modules": [
            {"ref": "C1", "pads": [
                {"name": "1", "net": {"net_id": 2, "name": "+5V"}},
                {"name": "2", "net": {"net_id": 1, "name": "GND"}}]},
            {"ref": "C2", "pads": [
                {"name": "1", "net": {"net_id": 0, "name": ""}},
                {"name": "2", "net": None}]},
        ],
    }
    nr = cc.build_net_registry_obj(model, board_id="t",
                                   crit={"power_rails": [], "diff_pairs": []})
    by_id = {n["net_id"]: n["pad_count"] for n in nr["nets"]}
    assert by_id == {0: 1, 1: 1, 2: 1}  # 按 net_id 分组（既有口径）


def test_net_registry_real_thin_pod_sum_equals_bound():
    """真板实证（20260206）：修复后 pad_count 总和==绑网 pad 总数；
    G1 盘上失准形态对照在场（每网=全部绑网 pad 数）。"""
    ds = _ds_manifest()
    b = next(x for x in ds["boards"] if x["board_id"] == "thin-pod")
    text = _board_text(b)
    model = cc.parse_kicad9_board(text)
    assert model["net_declaration_source"] == "pad_derived"
    crit = cc.derive_critical_nets(model)
    nr = cc.build_net_registry_obj(model, board_id="thin-pod", crit=crit)
    bound = sum(1 for m in model["modules"] for p in m["pads"]
                if p["net"] is not None)
    s = sum(n["pad_count"] for n in nr["nets"])
    assert s == bound and s > 0
    assert all(n["pad_count"] < bound for n in nr["nets"])  # 非退化
    # G1 盘上产物（冻结、失准形态）对照——不回写
    nr_g1 = _load(os.path.join(REPO, "profiles", "corpusr2-thin-pod",
                               "derived", "net-registry.json"))
    s_g1 = sum(n["pad_count"] for n in nr_g1["nets"])
    assert all(n["pad_count"] == bound for n in nr_g1["nets"])
    assert s_g1 == bound * nr_g1["net_count"]  # 退化形态（每网=全部）


# ---------------------------------------------------------------------------
# A5. F1 记录源：reconcile_corpus_r2_board_record 正负向
# ---------------------------------------------------------------------------

def _rec_from_route_check(rc):
    return {"profile_id": rc["profile_id"], "board_id": rc["board_id"],
            "dataset_role": rc["dataset_role"],
            "reference_path": rc["reference_route"]["path"],
            "reference_sha256": rc["reference_route"]["sha256"]}


def test_f1_reconcile_corpus_r2_record_positive(tmp_path):
    ds = _ds_manifest()
    rc = _load(os.path.join(REPO, "profiles", "corpusr2-tmp108",
                            "route-check.json"))
    out = cce.reconcile_corpus_r2_board_record(_rec_from_route_check(rc), ds)
    assert out["profile_id"] == "corpusr2-tmp108"
    assert out["board_id"] == "tmp108"
    assert out["dataset_id"] == "corpus-r2-r1"
    assert out["split_role"] == "train"
    assert out["board_path_rel"].startswith("datasets/corpus-r2-r1/")
    assert out["board_declared_sha256"] == rc["reference_route"]["sha256"]
    assert out["ff_plan_rel"] == \
        "profiles/corpusr2-tmp108/derived/feedforward-plan.json"
    assert out["manifest_ref"] == "datasets/corpus-r2-r1/manifest.json"
    assert out["route_check_rel"] == \
        "profiles/corpusr2-tmp108/route-check.json"
    assert out["governance"]["tier_designation"] == "train/val-candidate"
    assert out["governance"]["project_group"] == "6mil-tmp108"
    # holdout 板（H3 hackrf）：tier → holdout 派生一致
    rc3 = _load(os.path.join(REPO, "profiles", "corpusr2-hackrf-one",
                             "route-check.json"))
    out3 = cce.reconcile_corpus_r2_board_record(
        _rec_from_route_check(rc3), ds)
    assert out3["split_role"] == "holdout"
    assert out3["governance"]["holdout"]["pool_id"] == "H3"


def test_f1_reconcile_fail_closed_matrix():
    ds = _ds_manifest()
    rc = _load(os.path.join(REPO, "profiles", "corpusr2-tmp108",
                            "route-check.json"))
    base = _rec_from_route_check(rc)
    bad_cases = [
        ({**base, "reference_sha256": "0" * 64}, "sha mismatch"),
        ({**base, "dataset_role": "validation"}, "role conflict"),
        ({**base, "reference_path": "datasets/other/x.kicad_pcb"},
         "prefix"),
        ({**base, "board_id": "no-such-board"}, "board not in manifest"),
        ({**base, "profile_id": "kicaddemo-x"}, "profile prefix"),
        ({**base, "reference_path": "datasets/corpus-r2-r1/raw/x/"
                                   "y.kicad_pcb"}, "path!=manifest"),
    ]
    for rec, tag in bad_cases:
        with pytest.raises(cce.CorpusExtError):
            cce.reconcile_corpus_r2_board_record(rec, ds), tag
    # tier 枚举外 → 不猜（synthetic manifest 注入未知 tier）
    ds2 = {"dataset_id": "t", "boards": [
        {"board_id": "b1", "dir": "d", "files": ["b.kicad_pcb"],
         "board_file_sha256": "a" * 64,
         "tier_designation": "mystery-tier"}]}
    rec = {"profile_id": "corpusr2-b1", "board_id": "b1",
           "dataset_role": "train",
           "reference_path": "datasets/corpus-r2-r1/d/b.kicad_pcb",
           "reference_sha256": "a" * 64}
    with pytest.raises(cce.CorpusExtError):
        cce.reconcile_corpus_r2_board_record(rec, ds2)


# ---------------------------------------------------------------------------
# B. 真实板探针（datasets 只读；扩档 17 板解除 + R8 对 G1 计划全过）
# ---------------------------------------------------------------------------

def _corpusr2_pids():
    return sorted(p for p in os.listdir(os.path.join(REPO, "profiles"))
                  if p.startswith("corpusr2-"))


@pytest.mark.skipif(not os.path.isdir(os.path.join(
    REPO, "profiles")), reason="profiles 不在")
def test_expanded_gate_17_boards_released_with_r8_aligned():
    """扩档 17 板：detect_binding 解除（r1 版本门外为 CorpusExtError）+
    extract_pad_geometry + R8 逐层对账对 G1 FF-CORPUS 计划全过；
    mixed/power 铜层按白名单口径非零（usb-gigabit/kria）。"""
    ds = _ds_manifest()
    by_id = {b["board_id"]: b for b in ds["boards"]}
    expanded = []
    for bid, b in sorted(by_id.items()):
        if b["kicad_version_token"] not in EXPANDED_BUCKETS:
            continue
        expanded.append(bid)
        pid = "corpusr2-" + bid
        ff = _load(os.path.join(REPO, "profiles", pid, "derived",
                                "feedforward-plan.json"))
        geo = cce.extract_pad_geometry(_board_text(b))
        r8 = cce.align_signal_layer_pad_load(geo, ff)
        assert r8["aligned"] and r8["layers_total"] > 0, pid
    assert len(expanded) == 17
    # mixed/power 白名单实证（signal-only 会得出 0 铜层的两板）
    for bid in ("usb-gigabit-rev-e", "kria-k26-devboard"):
        geo = cce.extract_pad_geometry(_board_text(by_id[bid]))
        assert len(geo["copper_layers"]) == \
            by_id[bid]["layers"], bid


def test_all_37_boards_detect_binding_and_r8_aligned():
    """37 板全量：十档 detect_binding + R8 对账（B 层探针；datasets 只读，
    G1 计划缺板 skip）。"""
    ds = _ds_manifest()
    for bid, b in sorted((x["board_id"], x) for x in ds["boards"]):
        pid = "corpusr2-" + bid
        ff_path = os.path.join(REPO, "profiles", pid, "derived",
                               "feedforward-plan.json")
        if not os.path.exists(ff_path):
            pytest.skip(f"{pid} G1 计划缺")
        ff = _load(ff_path)
        geo = cce.extract_pad_geometry(_board_text(b))
        r8 = cce.align_signal_layer_pad_load(geo, ff)
        assert r8["aligned"], pid


# ---------------------------------------------------------------------------
# C1. r1 面 byte-identical 回归钉（扩档零改既有行为的证明）
# ---------------------------------------------------------------------------

def _rebuild_r1_plan_bytes():
    """按 r1 batch-build 同构逻辑内存重算 54 板计划（canonical bytes）。
    只读；不落盘。"""
    k9_plan = _load(os.path.join(REPO, "out", "v3-tl5",
                                 "k9-route-check-batch-r1", "plan.json"))
    manifests = {
        "pcbench": _load(os.path.join(
            REPO, "out", "v3-tl5", "dataset-manifest-pcbench-r1-v3.json")),
        "pcbbm": _load(os.path.join(
            REPO, "out", "v3-tl5",
            "dataset-manifest-pcbbenchmarks-r1-v3.json")),
        "kicad": _load(os.path.join(
            REPO, "out", "v3-tl5", "dataset-manifest-kicad-demos-r1.json")),
    }
    profiles = sorted(os.listdir(os.path.join(REPO, "profiles")))
    demo_pids = [p for p in profiles if p.startswith("kicaddemo-")]
    # REPAIR-P4 W-1（G0）：profiles/revc-coreboard/ 为项目配置声明 profile
    #（无 route-check.json，非 corpus 数据域），排除（登记=anchor-hashes-post-g0.json）
    real_pids = [p for p in profiles
                 if not p.startswith(("kicaddemo-", "smoke-",
                                      "corpusr2-", "revc-"))]
    records = []
    for pid in real_pids:
        rc = _load(os.path.join(REPO, "profiles", pid, "route-check.json"))
        rec = {"profile_id": pid, "board_id": rc["board_id"],
               "dataset_role": rc["dataset_role"],
               "reference_path": rc["reference_route"]["path"]}
        rec = cce.reconcile_real_board_record(rec, manifests)
        rec["board_path_rel"] = rec["reference_path"]
        rec["board_declared_sha256"] = rc["reference_route"]["sha256"]
        rec["ff_plan_rel"] = \
            f"profiles/{pid}/derived/feedforward-plan.json"
        rec["registry_rel"] = \
            f"profiles/{pid}/derived/net-registry.json"
        records.append(rec)
    for rec in cce.build_board_records(k9_plan, manifests):
        rec["registry_rel"] = ("profiles/" + rec["profile_id"]
                               + "/derived/net-registry.json")
        records.append(rec)
    assert len(records) == 54
    records.sort(key=lambda r: r["profile_id"])
    out = {}
    for rec in records:
        pid = rec["profile_id"]
        board_rel = rec["board_path_rel"]
        board_sha = hashing.sha256_file(os.path.join(REPO, board_rel))
        declared = rec.get("board_declared_sha256")
        if declared is not None:
            assert declared == board_sha, pid
        with open(os.path.join(REPO, board_rel), encoding="utf-8") as f:
            text = f.read()
        ff = _load(os.path.join(REPO, rec["ff_plan_rel"]))
        reg_sha = hashing.sha256_file(
            os.path.join(REPO, rec["registry_rel"]))
        plan = cce.build_ext_plan_obj(
            text, profile_id=pid, board_id=rec["board_id"],
            dataset_id=rec["dataset_id"], split_role=rec["split_role"],
            board_path_rel=board_rel, board_sha256=board_sha,
            ff_corpus_plan=ff, registry_sha256=reg_sha)
        out[pid] = hashing.canonical_json_bytes(plan)
    return out


def test_r1_54_plans_byte_identical_regression_pin():
    """r1 回归钉：扩档+待决①手术后重算 r1 54 板 FF-EXT 计划，与
    out/v3-ext-r1/ffext-r1/plans/ 盘面逐板 byte-identical（扩档零改
    既有行为；r1 冻结产物零触碰）。"""
    plans_dir = os.path.join(FFEXT_R1, "plans")
    if not os.path.isdir(plans_dir):
        pytest.skip("ffext-r1 盘面缺")
    rebuilt = _rebuild_r1_plan_bytes()
    assert len(rebuilt) == 54
    for pid, b in sorted(rebuilt.items()):
        disk = os.path.join(plans_dir, pid + ".json")
        with open(disk, "rb") as f:
            assert f.read() == b, f"{pid}: r1 计划重算 byte 不一致"


def test_r1_frozen_artifacts_hash_unchanged():
    """r1 batch-summary + 54 计划文件 sha256 与本测试文件内嵌基线一致
    （r1 产物零触碰断言；基线=动工前实测锚）。"""
    plans_dir = os.path.join(FFEXT_R1, "plans")
    if not os.path.isdir(plans_dir):
        pytest.skip("ffext-r1 盘面缺")
    assert hashing.sha256_file(os.path.join(
        FFEXT_R1, "batch-summary.json")) == \
        "7471bc6885eaa223ff52c7f6073b183f909edc9725e3ee58117bc9a44ffc12df"
    files = sorted(os.listdir(plans_dir))
    assert len(files) == 54
    digest = hashing.sha256_bytes(
        ",".join(hashing.sha256_file(os.path.join(plans_dir, f))
                 for f in files).encode("utf-8"))
    assert digest == ("80b9d5c913d1f23d4b4e529f7be361131f"
                      "e968e2d15fd903b19018e053b56a9e"), \
        "r1 54 计划文件合集 hash 变化（冻结件被触碰？）"


# ---------------------------------------------------------------------------
# C2. r2 批产物（37 板计划 + batch-summary）
# ---------------------------------------------------------------------------

def _r2_batch():
    p = os.path.join(FFEXT_R2, "batch-summary.json")
    if not os.path.exists(p):
        pytest.skip("ffext-r2 batch-summary 缺（中间态）")
    return _load(p)


def test_r2_plans_on_disk_full_coverage():
    batch = _r2_batch()
    assert batch["boards_total"] == 37
    assert batch["boards_ok"] == 37
    assert batch["boards_failed"] == []
    assert batch["plans_written"] == 37
    assert batch["split_counts"] == {"train": 31, "holdout": 6}
    pids = sorted(b["profile_id"] for b in batch["boards"])
    assert len(set(pids)) == 37
    assert all(p.startswith("corpusr2-") for p in pids)
    for row in batch["boards"]:
        rel = os.path.join(FFEXT_R2, "plans",
                           row["profile_id"] + ".json")
        assert os.path.exists(rel), row["profile_id"]
        assert hashing.sha256_file(rel) == row["plan_sha256"]


def test_r2_plan_byte_exact_replay_selected_boards():
    """抽三路径代表板（legacy/k5+扩档 mixed 档/pad_derived 名档）重算
    byte-exact（双发的批后抽查）。"""
    batch = _r2_batch()
    by_bid = {b["board_id"]: b for b in batch["boards"]}
    picks = ["teres-pcb1-a64-main-rev-c", "usb-gigabit-rev-e",
             "tmp108"]
    for bid in picks:
        row = by_bid[bid]
        plan_disk = os.path.join(FFEXT_R2, "plans",
                                 row["profile_id"] + ".json")
        ds = _ds_manifest()
        b = next(x for x in ds["boards"] if x["board_id"] == bid)
        text = _board_text(b)
        ff = _load(os.path.join(REPO, row["ff_plan_rel"]))
        reg_sha = hashing.sha256_file(
            os.path.join(REPO, row["registry_rel"]))
        plan = cce.build_ext_plan_obj(
            text, profile_id=row["profile_id"], board_id=bid,
            dataset_id=row["dataset_id"], split_role=row["split_role"],
            board_path_rel=row["board_path_rel"],
            board_sha256=hashing.sha256_file(
                os.path.join(REPO, row["board_path_rel"])),
            ff_corpus_plan=ff, registry_sha256=reg_sha)
        with open(plan_disk, "rb") as f:
            assert f.read() == hashing.canonical_json_bytes(plan), bid


def test_r2_batch_summary_governance_and_version_buckets():
    batch = _r2_batch()
    # 版本桶计数对账 datasets manifest kicad_version_token
    ds = _ds_manifest()
    buckets = {}
    for b in ds["boards"]:
        buckets.setdefault(b["kicad_version_token"], 0)
        buckets[b["kicad_version_token"]] += 1
    bve = {k: len(v) for k, v
           in batch["version_gate_expansion"]["boards_by_version"].items()}
    assert bve == buckets == BUCKET_COUNTS
    assert batch["version_gate_expansion"]["appended_id_bound_versions"] \
        == list(EXPANDED_BUCKETS)
    assert sorted(batch["version_gate_expansion"]["all_versions_after"]) \
        == sorted(cce.ALL_VERSIONS)
    # 治理段：H1–H6 池位 + caveat 携带 + never_holdout
    hp = {h["pool_id"]: h["board_id"]
          for h in batch["governance"]["holdout_pool"]}
    assert hp == {"H1": "kria-k26-devboard", "H2": "sdi-mipi-bridge",
                  "H3": "hackrf-one", "H4": "pslab-v6",
                  "H5": "scalenode-cm4-baseboard",
                  "H6": "jetson-nano-baseboard"}
    h6 = next(h for h in batch["governance"]["holdout_pool"]
              if h["pool_id"] == "H6")
    assert "同厂商同产品线" in (h6["caveat"] or "")  # R22 亲和警示逐字
    assert batch["governance"]["never_holdout"] == [
        "ottercast-audio-v2", "tinytapeout-demo", "tt06-fpga-ice40up5k"]
    assert len(batch["governance"]
               ["cross_library_affinity_warnings"]) == 3
    # 六类判定沿 r1 规则：blocked 四类 37 板 ×4；layer_capacity 全可估
    rks = batch["resource_kind_summary"]
    assert rks["blocked_rows_total"] == 37 * 4
    assert rks["layer_capacity_rows_total"] == 37
    assert rks["layer_capacity_board_blocked_total"] == 0
    # 批级 manifest 锚
    assert batch["datasets_manifest"]["sha256"] == hashing.sha256_file(
        DS_MANIFEST)


def test_r2_plans_schema_surface_sample():
    """计划契约面抽查（SPEC §7 键组；名档/legacy/扩档各一）。"""
    batch = _r2_batch()
    by_pid = {b["profile_id"]: b for b in batch["boards"]}
    for pid in ("corpusr2-tmp108", "corpusr2-teres-pcb1-a64-main-rev-c",
                "corpusr2-stm32-ds2480-emu"):
        p = _load(os.path.join(FFEXT_R2, "plans", pid + ".json"))
        assert p["schema_version"] == "1.3"
        assert p["artifact_kind"] == "feedforward_plan_ext"
        assert p["status"] == "planning_advisory"
        assert p["profile_id"] == pid
        assert p["plan_id"] == f"FF-EXT-{pid.upper()}-0001"
        assert p["snapshot"]["binding"]["board_snapshot_sha256"][
            "verifiable"] is True
        assert p["signal_layer_pad_load"]["aligned"] is True
        assert p["controls"] == []
        kinds = {r["kind"] for r in p["resources"]}
        assert kinds == set(cce.RESOURCE_KINDS_ALL)
        # routed 元素不消费（预测侧卫生边界）
        ignored = [i["elements"] for i in p["consumption_contract"]
                   ["ignored"]]
        assert any("segment" in e for e in ignored)


def test_existing_profile_prefix_counts_unchanged():
    """既有 profile 前缀计数零变化（G1 断言口径延续；corpusr2-* 37 为
    G1 产物，本批零触碰）。"""
    profiles = os.listdir(os.path.join(REPO, "profiles"))
    counts = {"pcbench-": 0, "pcbbm-": 0, "kicaddemo-": 0, "smoke-": 0,
              "corpusr2-": 0}
    for p in profiles:
        for pref in counts:
            if p.startswith(pref):
                counts[pref] += 1
                break
    assert counts == {"pcbench-": 35, "pcbbm-": 2, "kicaddemo-": 17,
                      "smoke-": 2, "corpusr2-": 37}
