"""E0 测试共用夹具（无 TestCase，仅工具函数）。

提供两类夹具：
1) 内存夹具：valid_board_obj + ref_route + svg_pkg 直接构造 SVG/manifest；
2) 真实产物夹具：把 A 包 dev-f1-01 的产物副本放进 tmp 目录（含按需的
   单场景 scenario-manifest），供突变/编排测试使用。A 包缺失时 SkipTest。
"""

from __future__ import annotations

import json
import os
import shutil

from pcbflow.v4exp import model, ref_route, svg_pkg
from pcbflow.v4exp.tests.test_v4exp_model import valid_board_obj

RESOLUTIONS = [(1200, 675), (1568, 872), (1600, 900), (2400, 1350)]
FIXTURE_SID = "dev-f1-01"
# tests 目录在 pcbflow/v4exp/tests，向上 3 级是仓库根
REPO_SOURCE_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "out", "v4-experiment"))


def build_memory_fixture() -> tuple:
    """内存构造 (board, ref, manifest, svg_text)，无磁盘依赖。"""
    board = model.board_from_obj(valid_board_obj())
    ref = ref_route.route_board(board)
    manifest, svg = svg_pkg.build(board, ref)
    return board, ref, manifest, svg


def _repo_file(name: str) -> str:
    return os.path.join(REPO_SOURCE_DIR, name)


def copy_real_fixture(tmp_dir: str, sid: str = FIXTURE_SID,
                      with_pngs: bool = True,
                      with_scenario_manifest: bool = True) -> str:
    """把 A 包某场景的产物副本放进 tmp_dir（作为独立 source_dir）。
    返回 tmp_dir。A 包缺失时抛 SkipTest。"""
    names = [f"board-snapshot-{sid}.json", f"ref-routes-{sid}.json",
             f"route-manifest-{sid}.json", f"route-preview-{sid}.svg"]
    if with_pngs:
        names += [f"route-preview-{sid}-{w}x{h}.png" for w, h in RESOLUTIONS]
    missing = [n for n in names if not os.path.exists(_repo_file(n))]
    if missing:
        raise unittest_skip(f"A 包产物缺失: {missing[:3]}")
    os.makedirs(tmp_dir, exist_ok=True)
    for n in names:
        shutil.copyfile(_repo_file(n), os.path.join(tmp_dir, n))
    if with_scenario_manifest:
        board = model.read_json(os.path.join(tmp_dir,
                                             f"board-snapshot-{sid}.json"))
        sman = {
            "schema": model.SCHEMA_SCENARIO_MANIFEST,
            "scenarios": [{
                "scenario_id": sid,
                "family": board["family"],
                "split": board["split"],
                "label": board["label"],
                "board_snapshot_sha256": board_sha_of(tmp_dir, sid)}]}
        with open(os.path.join(tmp_dir, "scenario-manifest.json"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(sman, ensure_ascii=False, indent=2) + "\n")
    return tmp_dir


def board_sha_of(source_dir: str, sid: str) -> str:
    board_obj = model.read_json(
        os.path.join(source_dir, f"board-snapshot-{sid}.json"))
    return model.sha256_of(board_obj)


def unittest_skip(reason: str):
    from unittest import SkipTest
    raise SkipTest(reason)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
