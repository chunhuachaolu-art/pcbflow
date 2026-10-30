# -*- coding: utf-8 -*-
"""REPAIR-P5 W-1 守卫测试：签核缺口清单生成器（scripts/repair_p5_gap_checklist.py）。

覆盖任务书 §3 W-1 四条机器义务：
- 幂等门：双跑 byte-exact（EXP-PCBFLOW-012）；
- 源产物零回写；
- 负对照：清单非空 ⇒ production_signoff_ready 必须仍 false（fail-closed）；
- 覆盖零遗漏 + 设计内排除如实登记；
- 盘上 r1 件可由当前源自动再生（防清单与源脱钩腐烂）。
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
from pcbflow.hashing import canonical_json_bytes, sha256_file

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "repair_p5_gap_checklist.py"
COMMITTED = REPO / "out/repair-p5/signoff-gap-checklist-r1.json"
SRC_RELS = [rel for rel, _ in [
    ("out/revc-fd1/envelope-signoff.json", ""),
    ("out/revc-fd1/signoff-package.json", ""),
    ("out/revc-fc3/signoff-package.json", ""),
]]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "repair_p5_gap_checklist", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load_module()


def _make_tree(dst: Path) -> None:
    """复制三源到 tmp 树（保持相对路径），供注入/负对照用。"""
    for rel in SRC_RELS:
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, target)


class TestIdempotenceAndRegeneration:
    def test_double_run_byte_exact(self, tmp_path):
        """幂等门：--out 两跑产物逐字节相等（无墙钟/主机名）。"""
        a, b = tmp_path / "a.json", tmp_path / "b.json"
        assert MOD.main(["--out", str(a)]) == 0
        assert MOD.main(["--out", str(b)]) == 0
        assert a.read_bytes() == b.read_bytes()

    def test_committed_artifact_regenerates_from_current_sources(self):
        """盘上 r1 件 == 对当前源重生成（自动再生、不腐烂锚）。"""
        assert COMMITTED.is_file(), "out/repair-p5/signoff-gap-checklist-r1.json 未落盘"
        assert canonical_json_bytes(MOD.build(MOD.REPO)) == COMMITTED.read_bytes()

    def test_sources_never_written(self, tmp_path):
        """源产物零回写：main 前后三源 sha 逐位不变。"""
        before = {rel: sha256_file(REPO / rel) for rel in SRC_RELS}
        out = tmp_path / "fresh.json"
        assert MOD.main(["--out", str(out)]) == 0
        assert out.is_file()
        after = {rel: sha256_file(REPO / rel) for rel in SRC_RELS}
        assert before == after


class TestNegativeControl:
    def test_ready_flipped_true_fails_closed_and_writes_nothing(self, tmp_path):
        """负对照：翻真 production_signoff_ready ⇒ build 抛错 + main exit 2 + 不落盘。"""
        tree = tmp_path / "tree"
        _make_tree(tree)
        env_path = tree / "out/revc-fd1/envelope-signoff.json"
        env = json.loads(env_path.read_text(encoding="utf-8"))
        env["data"]["gate"]["production_signoff_ready"] = True
        env_path.write_text(json.dumps(env, ensure_ascii=False, indent=1),
                            encoding="utf-8")
        with pytest.raises(MOD.NegativeControlError):
            MOD.build(tree)
        out = tmp_path / "should_not_exist.json"
        rc = MOD.main(["--root", str(tree), "--out", str(out)])
        assert rc == 2
        assert not out.exists()

    def test_missing_source_fails_closed(self, tmp_path):
        """缺源产物 ⇒ fail-closed（FileNotFoundError / main exit 2）。"""
        with pytest.raises(FileNotFoundError):
            MOD.build(tmp_path)
        assert MOD.main(["--root", str(tmp_path),
                         "--out", str(tmp_path / "x.json")]) == 2


class TestCoverageAndSchema:
    def test_checklist_schema_and_enums(self):
        art = MOD.build(MOD.REPO)
        assert len(art["checklist"]) >= 6
        for e in art["checklist"]:
            assert set(e) == {"gate", "item", "blocker_type", "evidence_path",
                              "evidence_sha256", "owner_hint", "status",
                              "source_artifacts", "note"}
            assert e["gate"] == "production_signoff"
            assert e["blocker_type"] in ("human", "external_tool",
                                         "external_evidence")
            assert e["status"] == "open"
            assert Path(e["evidence_path"]).is_absolute()
            assert Path(e["evidence_path"]).is_file()
            for p in e["source_artifacts"]:
                assert Path(p).is_file()

    def test_fixed_enumeration_present(self):
        """任务书覆盖面六类（#1/#5/外部工具族/叠层/功耗/扫描残余）逐类在账。"""
        art = MOD.build(MOD.REPO)
        items = " || ".join(e["item"] for e in art["checklist"])
        for kw in ("确认点 #1 structures", "确认点 #5 waivers",
                   "SI/PI/thermal/EMC/DFM", "板厂最终叠层表", "实测级功耗"):
            assert kw in items, f"覆盖面缺类：{kw}"
        assert any("impedance-targets.json" in e["item"]
                   for e in art["checklist"]), "扫描残余（fc3 missing entry）未入账"

    def test_coverage_reconciliation_zero_miss(self):
        art = MOD.build(MOD.REPO)
        cov = art["coverage"]
        assert cov["reconciliation_ok"] is True
        assert cov["findings_total"] == cov["findings_consumed_by_checklist"]

    def test_empty_by_design_excluded_not_gap(self):
        """advisory appendix（empty_by_design）= 设计内排除，不得进清单。"""
        art = MOD.build(MOD.REPO)
        cov_ex = art["coverage"]["excluded_by_design"]
        assert cov_ex
        assert all(x["status"] == "empty_by_design" for x in cov_ex)
        assert len(cov_ex) == 2  # fd1+fc3 双包各一件
        assert not any("advisory" in e["item"] for e in art["checklist"])

    def test_negative_control_block_present_and_pass(self):
        art = MOD.build(MOD.REPO)
        nc = art["negative_control"]
        assert nc["checklist_len"] == len(art["checklist"]) > 0
        assert nc["verdict"] == "pass"
        envelope = [a for a in nc["asserted_sources"]
                    if a["source"].endswith("envelope-signoff.json")]
        assert envelope and envelope[0]["production_signoff_ready"] is False
