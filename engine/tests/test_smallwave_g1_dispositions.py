# -*- coding: utf-8 -*-
"""V5-SMALLWAVE G1 钉值：build_p5_gate.py 处置清单输入+双口径输出+历史件保护。

合同（route-v5/V5-SMALLWAVE-TASKBOOK-2026-09-23.md §1.G1）：
- 处置清单 out/v5-p5/p5-gate/dispositions-2026-09-23.json（8 板
  board-inherent，witness 引用=diag-failed8/<板>.diag.json 与报告 §2）；
- G1 双口径：原口径（全 14 终态板分母）并记 + 可布域口径（分母剔 8 板，
  6/6 SAT）+ 豁免披露段；
- 历史件不覆写：目标 gate-report.json 已存在且无 --force=拒写。
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_p5_gate as G  # noqa: E402

DISP = os.path.join(ROOT, "out", "v5-p5", "p5-gate",
                    "dispositions-2026-09-23.json")
BOARDS_ROOT = os.path.join(ROOT, "out", "v5-p5", "boards")
HAVE_PRODUCTS = os.path.isdir(os.path.join(
    BOARDS_ROOT, "m2-pcie-adapter")) and os.path.isfile(DISP)


# ------------------------------------------------ 清单装载校验（单元）

def _rows_fixture():
    return [{"board": "b-failed", "abandoned": False,
             "exec_verdict": "FAILED", "exhaustion": "ripup-exhausted"},
            {"board": "b-sat", "abandoned": False,
             "exec_verdict": "ROUTED"},
            {"board": "b-aband", "abandoned": True}]


def test_load_dispositions_accepts_board_inherent_failed(tmp_path):
    doc = {"ruling": "r", "basis": "b", "boards": {
        "b-failed": {"disposition": "board-inherent", "failed_net": "N1",
                     "diag_class": "(a)", "witness": {
                         "diag_json": "d.json", "report": "r.md §2"}}}}
    p = tmp_path / "disp.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    d, rows = G.load_dispositions(str(p), _rows_fixture())
    assert d is not None and len(rows) == 1
    assert rows[0]["board"] == "b-failed"
    assert rows[0]["witness_diag_json"] == "d.json"
    # 旧清单无 status 字段 → 缺省 ruled（向后兼容 2026-09-23 八板清单）
    assert rows[0]["status"] == "ruled"


def test_load_dispositions_accepts_rule_value_limited(tmp_path):
    # V5-R1 W-6 扩展（2026-09-25 用户三裁②）：(c) 规则带值类豁免
    # （rule-value-limited）+ ruled/candidate 语义。
    doc = {"ruling": "r", "basis": "b", "boards": {
        "b-failed": {"disposition": "rule-value-limited", "status": "ruled",
                     "failed_net": "A0", "diag_class": "(c)",
                     "witness": {"geometry_json": "g.json",
                                 "report": "halt.md §1"}}}}
    p = tmp_path / "disp.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    d, rows = G.load_dispositions(str(p), _rows_fixture())
    assert d is not None and len(rows) == 1
    assert rows[0]["disposition"] == "rule-value-limited"
    assert rows[0]["status"] == "ruled"
    assert rows[0]["witness_geometry_json"] == "g.json"


def test_load_dispositions_accepts_candidate_disclosure(tmp_path):
    doc = {"boards": {
        "b-failed": {"disposition": "rule-value-limited",
                     "status": "candidate", "failed_net": "N1",
                     "diag_class": "(c)", "witness": {}}}}
    p = tmp_path / "disp.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    d, rows = G.load_dispositions(str(p), _rows_fixture())
    assert d is not None
    assert rows[0]["status"] == "candidate"


def test_load_dispositions_rejects_bad_status(tmp_path):
    doc = {"boards": {"b-failed": {"disposition": "rule-value-limited",
                                   "status": "pending"}}}
    p = tmp_path / "disp.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(SystemExit, match="仅认 ruled/candidate"):
        G.load_dispositions(str(p), _rows_fixture())


def test_load_dispositions_rejects_non_failed(tmp_path):
    doc = {"boards": {"b-sat": {"disposition": "board-inherent"}}}
    p = tmp_path / "disp.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(SystemExit, match="终态=ROUTED"):
        G.load_dispositions(str(p), _rows_fixture())


def test_load_dispositions_rejects_bad_disposition_class(tmp_path):
    doc = {"boards": {"b-failed": {"disposition": "waiver"}}}
    p = tmp_path / "disp.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(SystemExit, match="本门仅认"):
        G.load_dispositions(str(p), _rows_fixture())


def test_load_dispositions_rejects_unknown_board(tmp_path):
    doc = {"boards": {"ghost": {"disposition": "board-inherent"}}}
    p = tmp_path / "disp.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(SystemExit, match="不在 17 板终态标记内"):
        G.load_dispositions(str(p), _rows_fixture())


def test_load_dispositions_missing_file_is_none():
    d, rows = G.load_dispositions("no-such-file.json", _rows_fixture())
    assert d is None and rows == []


# ------------------------------------------------ 清单本体 schema 钉

@pytest.mark.skipif(not os.path.isfile(DISP), reason="dispositions 清单缺")
def test_dispositions_file_schema_eight_boards():
    doc = json.load(open(DISP, encoding="utf-8"))
    assert doc["taskbook_sha16"] == "9cd4a0e4d1e9c12d"
    assert doc["operator"] == "v5-smallwave-subagent"
    expect = {"atmega32u4-breakout", "dc-scm-rot-jumper-card",
              "m2-pcie-adapter", "om-flexgrid-v4-rigid-pcb",
              "pmod-i2c24io", "stm32-ds2480-emu",
              "thunderbolt-pcie-adapter", "usb-gigabit-rev-e"}
    assert set(doc["boards"]) == expect
    for name, d in doc["boards"].items():
        assert d["disposition"] == "board-inherent"
        assert d["diag_class"].startswith("(a)")
        w = d["witness"]
        assert w["diag_json"] == ("out/v5-p5/diag-failed8/%s.diag.json"
                                  % name)
        assert os.path.isfile(os.path.join(ROOT, w["diag_json"].replace(
            "out/v5-p5", os.path.join("out", "v5-p5"), 1)))
        assert "DIAG-FAILED8-REPORT.md §2" in w["report"]


# ------------------------------------------------ 历史件保护

def test_refuses_to_overwrite_existing_report(tmp_path, monkeypatch):
    (tmp_path / "gate-report.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(ROOT)
    with pytest.raises(SystemExit, match="拒写已存在历史件"):
        G.main(["--out-dir", str(tmp_path)])


# ------------------------------------------------ 端到端（产物树只读）

def _worldswap_pending():
    """换版态守卫（V5-R1 W-6 修正动作 A，主审复核 D-4）：世界换版
    （boards-pre-r1/ 归档+re-convert）清空 boards/ 全树 execute.json；
    14 终态板（wave6 done 标记、非弃板）任一缺 execute.json=换版进行态，
    本端到端件 skip 带披露；W-6 重跑逐板再生 execute.json 后自愈转 pass。
    """
    w6 = os.path.join(ROOT, "out", "v5-p5", "wave6", "_logs")
    missing = []
    for name in sorted(os.listdir(w6)):
        if not name.endswith(".wave6.done.json"):
            continue
        b = name[:-len(".wave6.done.json")]
        m = json.load(open(os.path.join(w6, name), encoding="utf-8"))
        if m.get("abandoned"):
            continue
        if not os.path.isfile(os.path.join(BOARDS_ROOT, b, "execute.json")):
            missing.append(b)
    return missing


@pytest.mark.skipif(not HAVE_PRODUCTS, reason="p5 板产物树/处置清单缺")
def test_gate_dual_caliber_end_to_end(tmp_path):
    missing = _worldswap_pending()
    if missing:
        pytest.skip("换版进行态：boards/ 缺 execute.json（W-6 重跑未覆盖 "
                    "%d 板，首缺=%s）——V5-R1 世界换版后、重跑完成前的 "
                    "时点快照，非代码回归（主审复核 D-4 修正动作 A）"
                    % (len(missing), missing[0]))
    code = G.main(["--dispositions", DISP, "--out-dir", str(tmp_path)])
    assert code == 0
    rep = json.loads((tmp_path / "gate-report.json").read_text(
        encoding="utf-8"))
    g1 = rep["g1"]
    # 原口径并记
    assert g1["criterion_1_sat_ge_5"]["n_sat"] == 6
    assert g1["verdict_original_caliber"].startswith("PASS")
    # 可布域口径：分母剔 8 → 6/6
    rd = g1["criterion_1_routable_domain"]
    assert rd["denominator"] == 6 and rd["n_sat"] == 6 and rd["pass"] is True
    assert rd["failed_in_domain"] == []
    assert "可布域口径 SAT 6/6" in g1["verdict"]
    ed = g1["exemption_disclosure"]
    assert ed["n_boards"] == 8 and len(ed["rows"]) == 8
    assert all(r["disposition"] == "board-inherent" for r in ed["rows"])
    # 豁免不进 SAT 名单宣称
    sat_boards = set(g1["criterion_1_sat_ge_5"]["sat_boards"])
    assert not (sat_boards & {r["board"] for r in ed["rows"]})
    # md 双口径段
    md = (tmp_path / "gate-report.md").read_text(encoding="utf-8")
    assert "可布域口径" in md and "豁免披露" in md
    assert "board-inherent" in md
    # 评估器世界披露
    # V5-EXECUTOR-ENG-R1 翻转披露（2026-10-02）：executor 0.8.0→0.9.0
    # （build_p5_gate 运行时动态取 EXECUTOR_VERSION，钉随版本翻新）
    assert rep["assessor_world"].startswith("评估器现役世界=v5.executor/0.13.0")  # 0.12.0 同步（engine-fix-r1 阶段一；0.11.0=EXEC-R8-B）  # EXEC-R8-B 同步
