"""REPAIR-P3 W-5 注册测试：toolchain_lock 四孤儿名追加注册（2026-09-22）。

覆盖：
- 注册表形状：22 名（18 既有+4 追加）、REGISTRY_VERSION 保持 "3.0"；
  新名符合 DOC-NAMING-CONVENTION §12 r8 命名语法 <名称>-v<N>；
- 追加式零破坏：18 既有名 schema_hash 与 P3 开工前快照钉值逐位相等
  （钉值=out/repair-p3/pre-state-snapshot.json snapshot.registry_18，
  2026-09-22 实测；APR-0002 冻结基线可复现性的注册表侧守卫）；
- 全实例回放：out/revc-a{1,2,3} 三份 constraints/coverage/impedance_targets
  + 盘上全部 envelope 实例（下限 34）经本包验证器与 jsonschema 库
  （缺席 skip）双口径零错误（形状合同忠实于实际产出）；
- 负向变体：缺 required/坏 const/坏 enum/多余键/坏 pattern/两形态 targets
  缺键 → 非空错误列表（fail-closed）；
- jsonschema 交叉验证先例=tests/test_observation.py（W-5 任务书指定）。

生成器模式：只读扫描 out/ 冻结产物、零写盘、无 wall-clock。
"""

from __future__ import annotations

import copy
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

from pcbflow import schemas  # noqa: E402

jsonschema = pytest.importorskip("jsonschema", reason="库缺席仅跳过对拍")

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

NEW_NAMES = ("constraints-v1", "coverage-v1", "envelope-v1",
             "impedance_targets-v1")

# P3 开工前快照钉值（追加注册不得改动任何既有条目哈希）
PINNED_18 = {
    "artifact-role-declaration-v1": "43d6a401cef681fd58ec358bc3741eccba3761395a43df183e07bc1ccbc03e9e",
    "bring_up_report": "cd50e41b41abaa10d9be95c78d7fde522a06f2e84fedf05961955438057ec859",
    "critic-flag-verdict-v1": "a19e3e56b39356887ab04f1252ccc449f241e58ce23d467adfe5e0201d2c10a6",
    "critic_run_record": "06a5de9e3229d46b6f1a69543e217e43a8920683504cd88b22e2ddfe15279dc5",
    "decision_ledger_entry": "b4c2d964c9280c1c22b8c3f4c4e6f8dc629c53910a7e8491ea16b368963f6630",
    "disposition_record": "09dd31fdeabb6656a0236dfd44e81bcd3013c9ded9463a7f93a66c0315fca71d",
    "external_execution_record": "fa739e846c403c042f76cb6595684331fa9f7f703e09e81224513ecd048ba127",
    "gate_record": "ccf6ac303f706b93074e32dbd13f87a60671093ebf03d67b27a4ba247b2eb396",
    "judge_post_record": "463b7b01ff3250e67018f1e94932177f846ddb0ff32e28279ec1ab90731aba31",
    "judge_pre_record": "867f9acc53c10a4cc77577bee31afa8907b5b2231e202ab674051d03729338d6",
    "observation-row-v1": "024bb915f7df27526ff21f21a488c01a25537c47cc9db73a0d5d1cd8407b9b06",
    "physics_coverage": "151bd9f0fa40f9254f350688f19159774062cea3f867014ae36eb69c41dcf034",
    "physics_report": "812c9d20d445fc01ecff1b0954c6f6b3a2367ff0cd0388f913fcc5e67fdcbd21",
    "profile": "766a2de97bead78d65fa34d954c4e9f7f46f81efef1f109d9e8f9eec0e40ff67",
    "project_manifest": "9e2c98f0e52557b833d48c66fea95c611236086779c4f879e978a759cce3da5a",
    "proposal_patch": "69414ee0e50fab3beb64f93e21a2fbbc612c8b1eb76492e22c3bcc42afb72222",
    "queue_event": "67b7c0fc80fea4eaec9f3a316429ed2d3d4b8f6c2327f11532666ebf2708fc71",
    "search_space": "6e4d549727d6a564de14f359e8cac9b05e11904c8d88f34d27a54a26d0a8ae23",
}


def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# ① 注册表形状与追加式零破坏
# ---------------------------------------------------------------------------

def test_registry_shape_and_naming():
    assert len(schemas.SCHEMAS) == 22
    assert schemas.REGISTRY_VERSION == "3.0"
    for name in NEW_NAMES:
        assert name in schemas.SCHEMAS
        assert name.count("-v") >= 1 and name.split("-v")[-1].isdigit()
    assert set(PINNED_18) == set(schemas.SCHEMAS) - set(NEW_NAMES)


def test_existing_18_hashes_pinned():
    for name, pinned in PINNED_18.items():
        assert schemas.schema_hash(name) == pinned, name


# ---------------------------------------------------------------------------
# ② 盘上实例全量回放（本包验证器 + jsonschema 双口径）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["constraints", "coverage",
                                  "impedance_targets"])
def test_compile_products_replay(kind):
    name = {"constraints": "constraints-v1", "coverage": "coverage-v1",
            "impedance_targets": "impedance_targets-v1"}[kind]
    files = sorted(glob.glob(os.path.join(REPO, "out", "**", kind + ".json"),
                             recursive=True))
    assert len(files) >= 3                    # revc-a1/a2/a3 下限
    for p in files:
        obj = _load(os.path.relpath(p, REPO))
        assert schemas.validate(name, obj) == [], p
        jsonschema.validate(obj, schemas.SCHEMAS[name])


def test_envelope_instances_replay():
    files = sorted(glob.glob(os.path.join(REPO, "out", "**",
                                          "*envelope*.json"), recursive=True))
    envs = [p for p in files
            if isinstance(_load(os.path.relpath(p, REPO)), dict)
            and "status" in _load(os.path.relpath(p, REPO))]
    assert len(envs) >= 34                    # P3 注册时点实存 34 份
    for p in envs:
        obj = _load(os.path.relpath(p, REPO))
        assert schemas.validate("envelope-v1", obj) == [], p
        jsonschema.validate(obj, schemas.SCHEMAS["envelope-v1"])
    # 历史三版并存轴：pattern 收 1.x（const 钉死会误拒既有合法件）
    versions = {_load(os.path.relpath(p, REPO))["schema_version"]
                for p in envs}
    assert versions <= {"1.0", "1.1", "1.3"} and len(versions) >= 2


# ---------------------------------------------------------------------------
# ③ 负向变体（fail-closed）
# ---------------------------------------------------------------------------

def _base(kind):
    return _load(os.path.join("out", "revc-a3", kind + ".json"))


def test_constraints_negative_variants():
    name = "constraints-v1"
    obj = _base("constraints")
    bad = copy.deepcopy(obj); del bad["counts"]
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj); bad["schema_version"] = "1.2"
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj); bad["extra_key"] = 1
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj); bad["constraints"][0]["type"] = "bogus"
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj); bad["constraints"][0]["earliest_stage"] = 9
    assert schemas.validate(name, bad)


def test_coverage_negative_variants():
    name = "coverage-v1"
    obj = _base("coverage")
    bad = copy.deepcopy(obj); del bad["totals"]
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj); bad["schema_version"] = "9.9"
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj); bad["ambiguous_selectors"][0]["oops"] = "x"
    assert schemas.validate(name, bad)


def test_impedance_negative_variants():
    name = "impedance_targets-v1"
    obj = _base("impedance_targets")
    bad = copy.deepcopy(obj); del bad["targets"]
    assert schemas.validate(name, bad)
    # 两形态 required 全缺（geom_*/est_* 双侧剥除）→ anyOf 拒
    bad = copy.deepcopy(obj)
    for t in bad["targets"]:
        for k in ("geom_width_mm", "geom_spacing_mm", "est_width_mm",
                  "adopted_width_mm"):
            t.pop(k, None)
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj); bad["targets"][0]["impedance_ohm"] = -5
    assert schemas.validate(name, bad)


def test_envelope_negative_variants():
    name = "envelope-v1"
    obj = None
    for p in sorted(glob.glob(os.path.join(REPO, "out", "**",
                                           "*envelope*.json"), recursive=True)):
        cand = _load(os.path.relpath(p, REPO))
        if isinstance(cand, dict) and cand.get("schema_version") == "1.1":
            obj = cand
            break
    assert obj is not None
    bad = copy.deepcopy(obj); bad["status"] = "running"
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj); bad["schema_version"] = "2.0"
    assert schemas.validate(name, bad)          # 主版本 pattern 拒
    bad = copy.deepcopy(obj); bad["mystery"] = True
    assert schemas.validate(name, bad)
    bad = copy.deepcopy(obj)
    if bad.get("inputs"):
        del bad["inputs"][0]["sha256"]
        assert schemas.validate(name, bad)


def test_new_names_subset_syntax_ok():
    """四新条目全部落在验证器子集语法内（jsonschema 可解析为证）。"""
    for name in NEW_NAMES:
        jsonschema.Draft202012Validator.check_schema(
            schemas.SCHEMAS[name])
