"""REPAIR-G2/G3 W-G2+W-G4 守卫（None-sentinel 显式语义，2026-09-25）。

守卫四面：
1. ManifestError 结构化（W-G2 主体）：ProfileError 子类，异常对象携带
   field（缺席/坏值字段点路径）+available（取值面清单）；消息保持
   「profile_key_missing:<last_key> available=…」形态（前缀兼容 G1+ 守卫
   regex r"profile_key_missing:out_dirs"）。
2. 故障注入族：缺席（整节）/半套（缺部分键）/坏值（非 str/空串）→
   结构化 ManifestError 非静默（不回落历史字面量）。
3. 缺省参数语义二分成文守卫：「manifest 必在」（import 期 fail-closed，
   缺省表达式唯一取值源=load_project_manifest）vs「显式 None 注入」
   （非「未指定」等价形式——无 None 分支/回落；口径对齐批 2026-09-25
   起=结构化 ManifestError 拒绝，原 TypeError 高声拦形态已收口 O-1/D-3）。
   成文=exec/REPAIR-G2-MANIFEST-DEFAULT-SEMANTICS-2026-09-25.md+config.py 注释。
4. W-G4 消化钉值：keepout_iter 两计划 pin 自 manifest out_dirs 派生
   （split+join 保平台分隔符形态，两平台与原 join 字面量逐字节相等）。
"""

from __future__ import annotations

import inspect
import json
import os

import pytest

from pcbflow import audit_cmd, compile_cmd, config, coplace_cmd, editor_cmd
from pcbflow import enum_cmd, feedforward, keepout_iter, profile_loader
from pcbflow import residual_cmd, route_cmd


def _load_current_profile():
    src = profile_loader.profile_path(config.PCBFLOW_ROOT)
    with open(src, encoding="utf-8") as f:
        return json.loads(f.read())


def _write_profile(tmp_path, pf):
    d = tmp_path / "profiles" / "revc-coreboard"
    d.mkdir(parents=True)
    (d / "profile.json").write_bytes(
        json.dumps(pf, ensure_ascii=False).encode("utf-8"))


def _raise_manifest_error(pf):
    """按改后 pf['config'] 直喂校验纯函数 _validate_manifest_config →
    触发的 ManifestError（供各故障注入用例断言）。

    直喂 dict 而非 load_project_manifest(tmp_root)：故障注入多用例若走
    真链会以不同 tmp root 占满 load_profile lru_cache(maxsize=4)、把
    PCBFLOW_ROOT 正主条目挤出，破坏 test_manifest_g1plus 的 identity
    断言（config._pf is load_profile(...)）——真链传播仅保留下方 1 用例。
    """
    with pytest.raises(config.ManifestError) as ei:
        config._validate_manifest_config(pf["config"])
    return ei.value


def _raise_manifest_error_via_load(tmp_path, pf):
    """真链传播用例专用（每批仅 1 个：lru_cache 容量纪律）。"""
    _write_profile(tmp_path, pf)
    with pytest.raises(config.ManifestError) as ei:
        config.load_project_manifest(str(tmp_path))
    return ei.value


# ---- 1. ManifestError 结构化 ---------------------------------------------------

def test_manifest_error_is_structured_profile_error():
    """结构化异常=ProfileError 子类（fail-closed 链同族）+field/available 属性。"""
    e = config.ManifestError("config.out_dirs", ["audit", "paths"])
    assert isinstance(e, profile_loader.ProfileError)
    assert e.field == "config.out_dirs"
    assert e.available == ["audit", "paths"]


def test_manifest_error_message_prefix_g1plus_compatible():
    """消息前缀保持 G1+ 守卫 regex 口径（profile_key_missing:<last_key>）。"""
    e = config.ManifestError("config.out_dirs", ["audit", "cplace"])
    assert "profile_key_missing:out_dirs" in str(e)
    assert "audit" in str(e) and "cplace" in str(e)


def test_out_dirs_required_keys_closed_set():
    """装载校验必需键封闭集=G1+ OUT_DIRS_PINNED 键集（13 键）；小写名
    常量（不入 vars() 大写快照——sha 914180f9 恒等由 test_profile_g0
    常驻钉值守卫，本件不重复钉）。"""
    assert set(config.out_dirs_required_keys) == {
        "compile", "enum", "audit", "coplace", "editor", "feedforward",
        "route", "residual", "keepout_iter", "check", "signoff",
        "kit_ff_plan", "kit_route_plan"}


# ---- 2. 故障注入族（缺席/半套/坏值 → 结构化非静默） ---------------------------

def test_out_dirs_section_missing_structured(tmp_path):
    """整节缺席（真链传播代表用例）：load_project_manifest(tmp) 抛
    ManifestError；field=config.out_dirs，available=实有节。"""
    pf = _load_current_profile()
    del pf["config"]["out_dirs"]
    e = _raise_manifest_error_via_load(tmp_path, pf)
    assert e.field == "config.out_dirs"
    assert e.available == sorted(pf["config"])  # 取值面清单=实有节
    assert isinstance(e, profile_loader.ProfileError)


@pytest.mark.parametrize("drop", ["compile", "kit_ff_plan", "residual"])
def test_out_dirs_half_set_missing_key_structured(tmp_path, drop):
    """半套（缺单键）：field=精确键路径，available=out_dirs 实有键清单。"""
    pf = _load_current_profile()
    del pf["config"]["out_dirs"][drop]
    e = _raise_manifest_error(pf)
    assert e.field == "config.out_dirs." + drop
    assert e.available == sorted(pf["config"]["out_dirs"])
    assert ("profile_key_missing:" + drop) in str(e)


def test_out_dirs_half_set_multi_missing_reports_first(tmp_path):
    """半套（缺多键）：报首缺键（封闭集序），available 展示全部实有键。"""
    pf = _load_current_profile()
    od = pf["config"]["out_dirs"]
    for k in ("check", "audit"):
        del od[k]
    e = _raise_manifest_error(pf)
    assert e.field == "config.out_dirs.audit"  # 封闭集序首个
    assert "audit" not in e.available and "check" not in e.available
    assert "compile" in e.available  # 实有键照列（取值面）


@pytest.mark.parametrize("bad", [123, None, True])
def test_out_dirs_bad_value_type_structured(tmp_path, bad):
    """坏值（非 str）：field=键路径，fail-closed 非静默。"""
    pf = _load_current_profile()
    pf["config"]["out_dirs"]["compile"] = bad
    e = _raise_manifest_error(pf)
    assert e.field == "config.out_dirs.compile"


def test_out_dirs_section_bad_type_structured(tmp_path):
    """坏值（整节非 dict）：field=节路径，available 空（无取值面）。"""
    pf = _load_current_profile()
    pf["config"]["out_dirs"] = 123
    e = _raise_manifest_error(pf)
    assert e.field == "config.out_dirs"
    assert e.available == []


def test_out_dirs_empty_string_value_structured(tmp_path):
    """坏值（空串）：field=键路径（空串=无落位，非合法目录 pin）。"""
    pf = _load_current_profile()
    pf["config"]["out_dirs"]["route"] = ""
    e = _raise_manifest_error(pf)
    assert e.field == "config.out_dirs.route"


@pytest.mark.parametrize("section", ["paths", "gate0", "audit",
                                     "audit_gates", "cplace"])
def test_config_section_missing_structured(tmp_path, section):
    """config 五节缺席：field=节路径，available=实有节（升级 require 的
    ProfileError 为结构化 ManifestError）。"""
    pf = _load_current_profile()
    del pf["config"][section]
    e = _raise_manifest_error(pf)
    assert e.field == "config." + section
    assert e.available == sorted(pf["config"])


# ---- 3. 缺省参数语义二分（成文守卫） -------------------------------------------

@pytest.mark.parametrize("mod,key", [
    (compile_cmd, "compile"), (enum_cmd, "enum"), (audit_cmd, "audit"),
    (coplace_cmd, "coplace"), (editor_cmd, "editor"),
    (feedforward, "feedforward"), (route_cmd, "route"),
    (residual_cmd, "residual"), (keepout_iter, "keepout_iter"),
])
def test_manifest_mandatory_default_form(mod, key):
    """「manifest 必在」形态钉死：out_dir_rel 缺省=manifest 取值、**非 None
    哨兵**（None-sentinel 不实现——语义二分成文=exec/REPAIR-G2-MANIFEST-
    DEFAULT-SEMANTICS-2026-09-25.md；显式 None 注入的现役两形态如实披露
    见该件 §0，行为收紧需另立授权）。"""
    default = inspect.signature(mod.build_products).parameters[
        "out_dir_rel"].default
    assert default is not None
    assert default == config.load_project_manifest().out_dirs[key]


# ---- 4. W-G4 消化钉值（keepout 两计划 pin 派生） ------------------------------

def test_keepout_plan_pins_derived_from_manifest():
    """W-G4 消化：两 pin 自 manifest out_dirs 派生（split+join），与原
    os.path.join 字面量逐字节相等（两平台同构——join 消费 split 产物）。"""
    od = config.load_project_manifest().out_dirs
    assert keepout_iter.FF_PLAN_DEFAULT == os.path.join(
        *od["kit_ff_plan"].split("/"))
    assert keepout_iter.FC3_PLAN_DEFAULT == os.path.join(
        *od["kit_route_plan"].split("/"))
    # 值不变门：与 G1+ 留账形态逐字节相等（平台分隔符形态保持）
    assert keepout_iter.FF_PLAN_DEFAULT == os.path.join(
        "out", "revc-fd3", "feedforward-plan.json")
    assert keepout_iter.FC3_PLAN_DEFAULT == os.path.join(
        "out", "revc-fc3", "route-plan.json")


# ---- 5. 口径对齐批（2026-09-25）O-1/D-3 收口守卫 ----------------------------

@pytest.mark.parametrize("bad", [None, 0, 1.5, "", "config", [], (), [1], {"a"}])
def test_config_non_dict_input_structured(bad):
    """直喂非 dict（含 None）→ ManifestError("config", []) 结构化拒绝
    （原形态=TypeError 高声拦非结构化，LEAD-REVIEW-G2G3 观察项 O-1；
    D-3「显式 None 注入」串拼接开放缺口随之闭合）。"""
    with pytest.raises(config.ManifestError) as ei:
        config._validate_manifest_config(bad)
    assert ei.value.field == "config"
    assert ei.value.available == []
    assert "profile_key_missing:config available=" in str(ei.value)
    assert isinstance(ei.value, profile_loader.ProfileError)
