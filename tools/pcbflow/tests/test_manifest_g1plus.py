"""REPAIR-G1+ Project Manifest 守卫（W-1/W-2 常驻套件，2026-09-24）。

守卫四面：
1. manifest 对象化等价（W-1）：load_project_manifest 字段=_pf_* 族封闭集
   （+W-2 out_dirs 增长项，登记=growth-inventory r3）；模块兼容别名与
   manifest 字段**同一 dict 对象**（identity）；由其派生的大写常量与
   G0 冻结装载逐项相等（快照 sha 守卫另见 tests/test_profile_g0.py，
   本件不重复钉 914180f9…）。
2. W-2 D 级 pin 消化钉值：manifest.out_dirs 与历史字面量逐项相等
   （值不变门）；build_products out_dir_rel 缺省与 CLI --out-dir 缺省
   全部=manifest 取值（来源集中门）。
3. 留账披露钉值：keepout_iter 两计划 pin（FF_PLAN_DEFAULT/FC3_PLAN_
   DEFAULT）=os.path.join 形态保留（平台分隔符与 CLI 前向斜杠字面量
   同 pin 异形；消化=平台值变，违反值不变门 → 留 G2/G3 profile 驱动域，
   见 out/repair-g1plus-r1/G1PLUS-REPORT-2026-09-24.md deviations）。
4. fail-closed：profile 缺 config.out_dirs → ProfileError（无静默回落）。
"""

from __future__ import annotations

import dataclasses
import inspect
import os

import pytest

from pcbflow import compile_cmd, config, enum_cmd, audit_cmd, coplace_cmd
from pcbflow import editor_cmd, feedforward, keepout_iter, profile_loader
from pcbflow import residual_cmd, route_cmd
from pcbflow.cli import build_parser


#: W-2 消化面封闭集（=改前各消费点字面量逐项；值不变门钉值）。
OUT_DIRS_PINNED = {
    "compile": "out/revc-a1",
    "enum": "out/revc-a2",
    "audit": "out/revc-a3",
    "coplace": "out/revc-b1",
    "editor": "out/revc-b2",
    "feedforward": "out/revc-ff1",
    "route": "out/revc-fc1",
    "residual": "out/revc-fc2",
    "keepout_iter": "out/revc-it",
    "check": "out/revc-fd1",
    "signoff": "out/revc-fd1",
    "kit_ff_plan": "out/revc-fd3/feedforward-plan.json",
    "kit_route_plan": "out/revc-fc3/route-plan.json",
}


# ---- 1. W-1 对象化等价 --------------------------------------------------------

def test_manifest_field_set_closed():
    """字段集=_pf_* 族封闭集（paths/gate0/audit/audit_gates/cplace+
    profile 身份元数据）+W-2 out_dirs（唯一增长项，已登记）。"""
    names = {f.name for f in dataclasses.fields(config.ProjectManifest)}
    assert names == {"profile_id", "profile_path", "profile_sha256",
                     "paths", "gate0", "audit", "audit_gates", "cplace",
                     "out_dirs"}


def test_manifest_matches_profile_loader():
    """manifest 字段与 profile_loader 直装同一对象（单一装载函数不另立来源）。"""
    pf = profile_loader.load_profile(config.PCBFLOW_ROOT)
    m = config.load_project_manifest()
    assert m.profile_id == pf["profile_id"] == "revc-coreboard"
    assert m.profile_path == pf["_path"]
    assert m.profile_sha256 == pf["_sha256"]
    assert m.paths is pf["config"]["paths"]
    assert m.gate0 is pf["config"]["gate0"]
    assert m.audit is pf["config"]["audit"]
    assert m.audit_gates is pf["config"]["audit_gates"]
    assert m.cplace is pf["config"]["cplace"]


def test_compat_aliases_same_objects():
    """模块级旧名=兼容别名：与 manifest 字段同一 dict 对象（等价前提）。"""
    m = config.load_project_manifest()
    assert config._pf is profile_loader.load_profile(config.PCBFLOW_ROOT)
    assert config._pf_paths is m.paths
    assert config._pf_gate0 is m.gate0
    assert config._pf_audit is m.audit
    assert config._pf_agates is m.audit_gates
    assert config._pf_cplace is m.cplace


def test_manifest_load_idempotent_object_equal():
    """重复装载=值等价新实例（load_profile lru_cache 共享底层 dict）。"""
    a, b = config.load_project_manifest(), config.load_project_manifest()
    assert a == b
    assert a.paths is b.paths


def test_manifest_derives_frozen_constants():
    """由 manifest 派生的大写常量与 G0 冻结装载逐项相等（代表值）。"""
    m = config.load_project_manifest()
    assert config.GATE_AUDIT_RECALL_MIN == m.audit_gates["recall_min"] == 0.70
    assert config.GATE_AUDIT_3V3_MIN == m.audit_gates["v3_escape_min"] == 15
    assert config.GATE_AUDIT_FP_MAX == m.audit_gates["fp_max"] == 0.10
    assert config.CPLACE_QUANT == m.cplace["quant_mm"] == 0.05
    assert config.NINE_GROUPS == list(m.gate0["nine_groups"])
    assert config.REVC_DIR == os.path.join(
        config.WORKSPACE_ROOT, *m.paths["revc_dir"])


# ---- 2. W-2 D 级 pin 消化 -----------------------------------------------------

def test_out_dirs_values_pinned():
    m = config.load_project_manifest()
    assert m.out_dirs == OUT_DIRS_PINNED


@pytest.mark.parametrize("mod,key", [
    (compile_cmd, "compile"), (enum_cmd, "enum"), (audit_cmd, "audit"),
    (coplace_cmd, "coplace"), (editor_cmd, "editor"),
    (feedforward, "feedforward"), (route_cmd, "route"),
    (residual_cmd, "residual"), (keepout_iter, "keepout_iter"),
])
def test_build_products_defaults_from_manifest(mod, key):
    """build_products out_dir_rel 缺省=manifest 取值（值不变、来源集中）。"""
    default = inspect.signature(mod.build_products).parameters[
        "out_dir_rel"].default
    assert default == config.load_project_manifest().out_dirs[key]
    assert default == OUT_DIRS_PINNED[key]


@pytest.mark.parametrize("argv,key", [
    (["compile"], "compile"), (["enum"], "enum"), (["audit"], "audit"),
    (["co-place"], "coplace"), (["editor"], "editor"),
    (["feedforward"], "feedforward"), (["route"], "route"),
    (["residual"], "residual"), (["keepout-iter"], "keepout_iter"),
    (["check"], "check"), (["signoff"], "signoff"),
])
def test_cli_out_dir_defaults_from_manifest(argv, key):
    """CLI --out-dir 缺省=manifest 取值（parse_args 不执行命令）。"""
    args = build_parser().parse_args(argv)
    assert args.out_dir == config.load_project_manifest().out_dirs[key]
    assert args.out_dir == OUT_DIRS_PINNED[key]


def test_cli_kit_plan_defaults_from_manifest():
    args = build_parser().parse_args(["keepout-iter"])
    od = config.load_project_manifest().out_dirs
    assert args.feedforward_plan == od["kit_ff_plan"]
    assert args.baseline_route_plan == od["kit_route_plan"]


# ---- 3. 留账披露钉值（边界如实） ----------------------------------------------

def test_keepout_plan_pins_join_form_preserved():
    """未消化项留账：os.path.join 形态逐字节保持（平台分隔符值不变）。"""
    assert keepout_iter.FF_PLAN_DEFAULT == os.path.join(
        "out", "revc-fd3", "feedforward-plan.json")
    assert keepout_iter.FC3_PLAN_DEFAULT == os.path.join(
        "out", "revc-fc3", "route-plan.json")


# ---- 4. fail-closed -----------------------------------------------------------

def test_manifest_out_dirs_missing_fails_closed(tmp_path):
    src = profile_loader.profile_path(config.PCBFLOW_ROOT)
    import json
    pf = json.loads(open(src, encoding="utf-8").read())
    del pf["config"]["out_dirs"]
    d = tmp_path / "profiles" / "revc-coreboard"
    d.mkdir(parents=True)
    (d / "profile.json").write_bytes(
        json.dumps(pf, ensure_ascii=False).encode("utf-8"))
    with pytest.raises(profile_loader.ProfileError,
                       match=r"profile_key_missing:out_dirs"):
        config.load_project_manifest(str(tmp_path))
