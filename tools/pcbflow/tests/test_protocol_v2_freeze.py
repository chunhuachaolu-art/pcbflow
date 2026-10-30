"""协议 v2 冻结入账包测试（s79_protocol_v2_freeze /
evaluation-protocol-v2.md + protocol-v2-registration.json）——独立
holdout 评估协议冻结件与登记件（s78 测试底稿同构）：

任务血统：R20 close 已完成（run-r20=6573a59a、dev-r20=80e3e9e2 在
盘）；per V3-RECOMMENDATIONS-2026-09-09.md §6 交付顺序「R20 close →
冻结 holdout 协议」与 §7 最终建议，本包冻结评估协议 v2 并入账登记
件。批准依据=用户 2026-09-10 指令「按 V3-RECOMMENDATIONS-2026-09-09.
md 继续之后的工作」。

装配事实：P2 九条款中 §3 P2 原列八条（三集按板隔离/reader 盲读/一对
一匹配/重复旗标单列/unmatched·unadjudicated·真实 false positive 三
分/六指标分列/逐旗标人工裁定/阈值不晋升）；P2-9=§5 治理红线并入条款
——from 字段逐条如实标注。

边界（照常）：v1 原文零字节保留（22dc7337 锚，继续承载 R1–R22 历史
口径）；HOLDOUT-PLAN.md 零改动（a4b80193 锚）；TL 门/APR-0011 零改
动；in_calibrated_range 恒 False；自动分流恒 blocked；v2 生效≠
holdout 启动（启动=用户判断的独立人工点）；V4-SVG 独立路线（v4exp
在盘登记、非本协议对象）。

覆盖（14 测试，只读 out/、零子进程/零网络；s79 幂等重跑例外=护栏语
义在案、字节零改动）：
1.  v1 零字节锚（哈希=22dc7337…全值、3916 字节非空=未被触碰）；
2.  v2 冻结件头部与 supersedes（version=frozen/supersedes 三要点/批
    准依据行）；
3.  v2 九条款齐（P2-1…P2-9+条款关键词）；
4.  v2 边界声明齐（TL 门/APR-0011/in_calibrated_range/blocked/v2 生
    效≠启动/V4-SVG）；
5.  holdout 一次性纪律继承+HOLDOUT-PLAN 零改动（a4b80193 全值）；
6.  v2 现状登记数字与 run/dev 记录一致（r19/r20/r22 实测装载对照）；
7.  registration canonical 确定性+盘上件=同参重建 byte-exact+无
    round 字段+kind；
8.  防覆盖守卫：overwrite_guard 三态+_commit 写入/幂等/不同字节
    FAIL；
9.  引用哈希 fail-closed（篡改 REFERENCE_HASH_EXPECTED 任一锚→
    SystemExit 拒算，逐件参数化）；
10. axis_stop 判定与 P1 表一致（reject/marginal/supported/
    inconclusive 各支+未知 fail-closed+registration 落 reject 支）；
11. in_calibrated_range=False 断言（registration False+md 语句）；
12. holdout 状态机断言（状态迁移：用户 2026-09-10 拍板启动；启动前
    零接触历史证据=precheck-r1.json 钉死；启动后正式链五件/渲染 6 张
    PNG/reader 18 件范围纪律逐条钉死；registration 冻结零回写
    started=False）；
13. P2 条款 registration↔md 对齐+装配说明（§3 P2 原列八条+§5 并入）；
14. s79 幂等重跑+末尾打印两件 sha256。
"""

import contextlib
import importlib.util
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing  # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")
HOLDOUT_DIR = os.path.join(REPO, "out", "v3-tl2", "holdout")

DECLARED_DATE = "2026-09-10"

V1_PATH = os.path.join(CAL_DIR, "evaluation-protocol-v1.md")
V1_SHA256 = ("22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b"
             "11e798e")
V1_BYTES = 3916
V2_PATH = os.path.join(CAL_DIR, "evaluation-protocol-v2.md")
V2_SHA256 = ("365b67ef247ff2d664c620971fff21efc4ed684e55a2e99625823321669"
             "e0712")
V2_BYTES = 9814
REG_PATH = os.path.join(CAL_DIR, "protocol-v2-registration.json")
REG_SHA256 = ("36cc86a7b907058fa4ce084bd0ed3a47b6d12063caa73d03a7152b515f"
              "3867bb")
HOLDOUT_PLAN_PATH = os.path.join(HOLDOUT_DIR, "HOLDOUT-PLAN.md")
HOLDOUT_PLAN_SHA256 = ("a4b80193ac9c15cb0ecba0208737a0adea343e5e3990b4d"
                       "730141c56d2ed33a9")
HOLDOUT_PRECHECK_REL = "out/v3-tl2/holdout/precheck-r1.json"
PRECHECK_SHA256_PREFIX = "7260027f"
# holdout r1 正式链五件（2026-09-10 用户拍板启动后按一次性纪律落盘，
# sha256 前缀=启动运行时点锚定）
HOLDOUT_FORMAL_CHAIN_PREFIXES = {
    "holdout-prep-record-r1.json": "b2eaad8365e33925",
    "render-framing-holdout-r1.json": "4f8726f05219f703",
    "render-witness-holdout-r1.json": "806034a8a73f80b6",
    "holdout-run-r1.json": "e64f882f2c02adab",
    "holdout-dev-record-r1.json": "eeea2bb908d2434f",
}
# 已选 holdout 板（3 板；未选 READY 板零渲染/零 reader 接触的范围纪律）
HOLDOUT_BOARDS = {"kitspace_led_driver", "tiny_tapeout", "vme-wren"}
HOLDOUT_VIEWS = ("top", "bottom")
HOLDOUT_INSTANCES = ("i1", "i2", "i3")

REL_RUN_R20 = "out/v3-tl2/calibration/calibration-run-r20.json"
REL_RUN_R22 = "out/v3-tl2/calibration/calibration-run-r22.json"
REL_DEV_R19 = "out/v3-tl2/calibration/round19-dev-record.json"
REL_DEV_R20 = "out/v3-tl2/calibration/round20-dev-record.json"
REL_DEV_R22 = "out/v3-tl2/calibration/round22-dev-record.json"


def _load_s79():
    path = os.path.join(REPO, "scripts", "s79_protocol_v2_freeze.py")
    spec = importlib.util.spec_from_file_location("s79_protocol_v2_freeze",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S79 = _load_s79()


@pytest.fixture(scope="module")
def v2_text():
    with open(V2_PATH, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def reg():
    with open(REG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _json_load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return json.load(f)


def _sha(path):
    return hashing.sha256_file(path)


# ---------------------------------------------------------------------------
# 1. v1 零字节锚
# ---------------------------------------------------------------------------

def test_v1_zero_byte_anchor_untouched():
    """evaluation-protocol-v1.md 零字节不动锚：盘上哈希=22dc7337…全
    值、3916 字节非空（「零字节不动」=未被改动一字节，非空文件）；
    registration supersedes.target 指向它。"""
    assert os.path.exists(V1_PATH)
    assert os.path.getsize(V1_PATH) == V1_BYTES
    assert _sha(V1_PATH) == V1_SHA256
    reg_doc = S79.json.loads(open(REG_PATH, encoding="utf-8").read())
    sup = reg_doc["supersedes"]
    assert sup["target_path_rel"].endswith("evaluation-protocol-v1.md")
    assert sup["target_sha256"] == V1_SHA256
    assert "零字节保留" in sup["retention"]
    assert "R1–R22 历史口径" in sup["retention"]


# ---------------------------------------------------------------------------
# 2. v2 冻结件头部与 supersedes
# ---------------------------------------------------------------------------

def test_v2_frozen_header_and_supersedes(v2_text):
    """v2 冻结件：头部四键（protocol_id/version: v2/status: frozen/
    declared_date=2026-09-10 声明常量）+supersedes 三要点（v2 只治理
    未来独立 holdout 评估/v1 原文零字节保留/v1.1+v1.2 被继承）+批准
    依据行（用户 2026-09-10 指令+§7 引用）+盘上哈希=365b67ef…。"""
    assert _sha(V2_PATH) == V2_SHA256
    assert os.path.getsize(V2_PATH) == V2_BYTES
    for anchor in ("protocol_id: evaluation-protocol-v2",
                   "version: v2",
                   "status: frozen",
                   "declared_date",
                   DECLARED_DATE,
                   "承继与取代关系（supersedes）",
                   "v2 只治理未来的独立 holdout 评估",
                   "v1 原文零字节保留",
                   "v1.1 多实例聚合口径与 v1.2 工具行为规约被 v2 继承",
                   "批准依据: 用户 2026-09-10 指令",
                   "该文档 §7 最终建议原文",
                   "完成 R20 close，随后冻结评估协议并准备独立 holdout"):
        assert anchor in v2_text, f"v2 头部/supersedes 锚缺失: {anchor}"
    reg_doc = S79.json.loads(open(REG_PATH, encoding="utf-8").read())
    pv = reg_doc["protocol_v2"]
    assert pv["version"] == "v2" and pv["status"] == "frozen"
    assert pv["declared_date"] == DECLARED_DATE
    assert pv["sha256"] == V2_SHA256


# ---------------------------------------------------------------------------
# 3. v2 九条款齐
# ---------------------------------------------------------------------------

def test_v2_nine_clauses_complete(v2_text):
    """P2 九条款逐条编号冻结：P2-1…P2-9 全在 md 且各带来源标注；
    条款关键词逐条在位（按板或项目组隔离/不看 GT/一对一匹配/重复旗标
    单列/三分/六指标分列/逐旗标人工裁定/不自动晋升/缺证 blocked）。"""
    keywords = {
        "P2-1": "按板或项目组隔离",
        "P2-2": "不看 GT",
        "P2-3": "一对一匹配",
        "P2-4": "不重复计入 precision",
        "P2-5": "真实 false positive",
        "P2-6": "confidence calibration 分开",
        "P2-7": "逐旗标人工裁定",
        "P2-8": "自动晋升模型",
        "P2-9": "必须 blocked",
    }
    for cid, kw in keywords.items():
        assert cid in v2_text, f"缺条款 {cid}"
        assert kw in v2_text, f"{cid} 条款关键词缺失: {kw}"
    assert v2_text.count("**P2-") == 9
    for i in range(1, 9):
        assert "§3 P2" in v2_text
    assert "§5（治理红线，本条经本协议并入九条款清单" in v2_text


# ---------------------------------------------------------------------------
# 4. v2 边界声明齐
# ---------------------------------------------------------------------------

def test_v2_boundary_declaration_complete(v2_text):
    """边界声明节齐：TL 门零改动/APR-0011 零改动/in_calibrated_range
    恒 False/自动分流恒 blocked/v2 生效≠holdout 启动/V4-SVG 独立路线
    （§3 P4 引用+v4exp 在盘登记、非本协议对象）/development 线非充分
    条件。"""
    for anchor in ("TL 门零改动",
                   "APR-0011 零改动",
                   "in_calibrated_range 恒 False",
                   "自动分流恒 blocked",
                   "v2 生效≠holdout 启动",
                   "用户拍板",
                   "V4-SVG 属独立路线",
                   "§3 P4",
                   "v4exp",
                   "非本协议对象",
                   "不是单独翻转正式谓词的充分条件"):
        assert anchor in v2_text, f"边界声明锚缺失: {anchor}"


# ---------------------------------------------------------------------------
# 5. holdout 一次性纪律继承 + HOLDOUT-PLAN 零改动
# ---------------------------------------------------------------------------

def test_v2_holdout_one_time_discipline_inherited(v2_text):
    """一次性纪律继承：v2 引用 HOLDOUT-PLAN.md（路径+哈希）、「正式
    运行前任何盲读/指引迭代不得接触渲染件」语句、「运行时机=用户判断
    的独立人工点」、零 GT 主张；HOLDOUT-PLAN.md 盘上哈希=a4b80193…
    全值（零改动）。"""
    assert _sha(HOLDOUT_PLAN_PATH) == HOLDOUT_PLAN_SHA256
    for anchor in ("HOLDOUT-PLAN.md",
                   "a4b80193",
                   "任何盲读、任何指引/协议迭代不得接触其渲染件",
                   "渲染只在正式运行时做",
                   "运行时机=用户判断的独立人工点",
                   "零 GT 主张",
                   "designation=holdout-candidate"):
        assert anchor in v2_text, f"一次性纪律锚缺失: {anchor}"


# ---------------------------------------------------------------------------
# 6. v2 现状登记数字与 run/dev 记录一致
# ---------------------------------------------------------------------------

def test_v2_status_numbers_match_run_records(v2_text):
    """v2 现状登记数字与盘上 run/dev 记录实测一致（fail-closed 对照）：
    r19 marginal M1=0.461538（dev-r19 装载）；r20 reject M1=0.636364
    （run-r20 装载）；r22 regressed M1=0.390244=16/41 带内（run-r22 装
    载+带 [0.361538, 0.561538]）；G2 出局条目指针 R22T-002/R22T-013
    （dev-r22 摘录在案）；R21 不做。"""
    dev19 = _json_load(REL_DEV_R19)
    run20 = _json_load(REL_RUN_R20)
    run22 = _json_load(REL_RUN_R22)
    dev20 = _json_load(REL_DEV_R20)
    dev22 = _json_load(REL_DEV_R22)

    assert dev19["hypothesis_test_i"]["verdict"] == "marginal"
    m1_r19 = dev19["axis_experiment_ledger"]["this_round_measured"]["M1"]
    assert m1_r19 == 0.461538
    assert run20["hypothesis_test"]["verdict"] == "reject"
    assert run20["hypothesis_test"]["measurement"][
        "top_abstain_rate_r20"] == 0.636364
    assert dev20["hypothesis_test_i"]["verdict"] == "reject"
    assert "g1_bifurcation_record" in dev20
    assert run22["hypothesis_test"]["verdict"] == "regressed"
    assert run22["hypothesis_test"]["measurement"][
        "top_abstain_rate_r22"] == 0.390244
    gc = run22["hypothesis_test"]["measurement"]["guard_channel"]
    assert (gc["g2_geometry_gate_r19"], gc["g2_geometry_gate_r22"]) == (0, 2)
    entries = dev22["g2_bifurcation_record"]["rejected_entries_excerpt"]
    entry_ids = {e["flag_id"] for e in entries}
    assert entry_ids == {"R22T-002", "R22T-013"}

    for anchor in ("r19（marginal）", "0.461538",
                   "r20（reject，G1 分岔）", "0.636364",
                   "r22（regressed，G2 分岔，M1 带内复现）", "0.390244",
                   "[0.361538, 0.561538]",
                   "R21 全组合",
                   "R22T-002", "R22T-013",
                   "R20B-003", "R20B-006",
                   "guidance-r19", "8633bda5",
                   "两账并列、不合并、不改写",
                   "不构成采纳、不构成晋升"):
        assert anchor in v2_text, f"现状登记锚缺失: {anchor}"


# ---------------------------------------------------------------------------
# 7. registration canonical 确定性 + 盘上件=同参重建
# ---------------------------------------------------------------------------

def test_registration_canonical_determinism_and_disk_identity(reg):
    """registration：kind=protocol_v2_registration、declared_date=
    2026-09-10、无 round 字段（非轮次件）、schema_version、盘上件哈希
    =36cc86a7…全值、canonical 同参重建 byte-exact（确定性）。"""
    assert reg["kind"] == "protocol_v2_registration"
    assert reg["declared_date"] == DECLARED_DATE
    assert "round" not in reg
    assert reg["schema_version"] == "3.0"
    assert _sha(REG_PATH) == REG_SHA256
    # 同参重建（复用 s79 实测装载路径）→ byte-exact
    measured = S79.measure_reference_hashes()
    S79.verify_reference_hashes(measured)
    v2_sha = S79._sha(S79.REL_PROTOCOL_V2)
    v2_len = S79._rel(S79.REL_PROTOCOL_V2).stat().st_size
    r20_fact = S79._load_r20(S79._json_load(S79.REL_RUN_R20))
    r22_fact = S79._load_r22(S79._json_load(S79.REL_RUN_R22))
    dev19_fact = S79._load_dev_r19(S79._json_load(S79.REL_DEV_R19))
    dev20_fact = S79._load_dev_r20(S79._json_load(S79.REL_DEV_R20))
    dev22_fact = S79._load_dev_r22(S79._json_load(S79.REL_DEV_R22))
    rebuilt = S79.build_registration(measured, v2_sha, v2_len,
                                     r20_fact, r22_fact, dev19_fact,
                                     dev20_fact, dev22_fact)
    rebuilt_bytes = hashing.canonical_json_bytes(rebuilt)
    with open(REG_PATH, "rb") as f:
        disk_bytes = f.read()
    assert rebuilt_bytes == disk_bytes
    # 重建两次 byte-exact（确定性）
    assert hashing.canonical_json_bytes(
        S79.build_registration(measured, v2_sha, v2_len, r20_fact,
                               r22_fact, dev19_fact, dev20_fact,
                               dev22_fact)) == disk_bytes


# ---------------------------------------------------------------------------
# 8. 防覆盖守卫
# ---------------------------------------------------------------------------

def test_registration_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫：overwrite_guard 三态（无既有→write/字节等同→
    idempotent_skip/不同→fail）；_commit=写入/幂等跳过/不同字节
    SystemExit（fail-closed，绝不覆写）。"""
    assert S79.overwrite_guard(None, b"abc") == "write"
    assert S79.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S79.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S79._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S79._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S79._commit(p, b"abc", "probe")


# ---------------------------------------------------------------------------
# 9. 引用哈希 fail-closed（篡改任一锚→拒算）
# ---------------------------------------------------------------------------

def test_registration_reference_hashes_fail_closed():
    """引用件哈希清单 8 件盘上实测全过；篡改任一引用锚（逐件参数化）
    → verify_reference_hashes SystemExit 拒算（fail-closed）。"""
    measured = S79.measure_reference_hashes()
    S79.verify_reference_hashes(measured)  # 盘上现状全过
    assert set(measured) == set(S79.REFERENCE_HASH_EXPECTED)
    assert measured["protocol_v1"].startswith("22dc7337")
    assert measured["holdout_plan"].startswith("a4b80193")
    assert measured["run_r20"].startswith("6573a59a")
    assert measured["run_r22"].startswith("80a12c05")
    assert measured["dev_r19"].startswith("0e2fdd69")
    assert measured["dev_r20"].startswith("80e3e9e2")
    assert measured["dev_r22"].startswith("b4b8fbe9")
    for role in sorted(S79.REFERENCE_HASH_EXPECTED):
        tampered = dict(measured)
        tampered[role] = "0" * 64  # 篡改该件实测哈希
        with pytest.raises(SystemExit, match=role):
            S79.verify_reference_hashes(tampered)


# ---------------------------------------------------------------------------
# 10. axis_stop 判定与 P1 表一致
# ---------------------------------------------------------------------------

def test_axis_stop_decision_pure_function_p1_table(reg):
    """axis_stop_action 纯函数四支（per RECOMMENDATIONS §3 P1 表）：
    supported→冻结进 holdout；marginal→不称为胜出；reject→停止同一调
    参轴+保留负向证据；inconclusive→不强行选优；未知结果 fail-closed；
    registration 落 reject 支（r20 实测）+R21 not_run+G1 停轴范围说
    明。"""
    a = S79.axis_stop_action("supported")
    assert "冻结" in a["action_zh"] and "holdout" in a["action_en"]
    m = S79.axis_stop_action("marginal")
    assert "不称为胜出" in m["action_zh"]
    r = S79.axis_stop_action("reject")
    assert "停止同一调参轴" in r["action_zh"]
    assert "retain negative evidence" in r["action_en"]
    i = S79.axis_stop_action("inconclusive")
    assert "不强行选优" in i["action_zh"]
    with pytest.raises(SystemExit):
        S79.axis_stop_action("unsupported_outcome")
    # registration 落 reject 支（与 r20 实测一致）
    dec = reg["axis_stop_decision"]
    assert dec["decision"] == r
    assert dec["decision"]["r20_outcome"] == "reject"
    assert "not_run" in dec["r21_full_combination"]
    assert "同一调参轴" in dec["g1_scope_note"]


# ---------------------------------------------------------------------------
# 11. in_calibrated_range=False 断言
# ---------------------------------------------------------------------------

def test_in_calibrated_range_false(reg, v2_text):
    """in_calibrated_range 恒 False：registration boundary_
    declaration.in_calibrated_range is False（布尔，非字符串）；v2 md
    含恒 False 语句+正式采纳须人工批准语义。"""
    assert reg["boundary_declaration"]["in_calibrated_range"] is False
    assert "in_calibrated_range 恒 False" in v2_text
    assert "正式采纳" in v2_text
    assert reg["boundary_declaration"]["apr_0011_thresholds"] == \
        "unchanged（provisional_supersedable 原文零改动）"
    assert reg["boundary_declaration"]["auto_routing"] == \
        "blocked（恒；BL-4+TD5 合取约束在位；P2-8 阈值不晋升条款同向）"


# ---------------------------------------------------------------------------
# 12. holdout 状态机断言（启动前零接触历史证据 + 正式运行一次性证据链）
# ---------------------------------------------------------------------------

def test_holdout_formal_run_state_evidence(reg):
    """holdout 状态机断言。状态迁移：用户 2026-09-10 拍板启动，holdout
    r1 正式运行一次性完成（一次性=不重跑；本测试钉死该状态的全部纪律
    证据）。三段逐条断言：

    ① 启动前零接触历史证据（继续有效）：HOLDOUT-PLAN.md sha256=
    a4b80193…（计划件零改动）；precheck-r1.json sha256 前缀 7260027f
    且 discipline.zero_render/zero_reader/zero_image_tooling 全 True
    （s81 只读预检件=「正式运行前零渲染零 reader 接触」的盘面证据）。

    ② 启动后按一次性纪律执行的证据链：正式链五件（prep-record/
    framing/witness/run/dev-record）在盘且 sha256 前缀匹配；渲染范围
    纪律——holdout 下 renders* 目录恰为 {renders-holdout-r1}，witness
    renders 列表 board 集合恰为 3 块已选 holdout 板（未选 READY 板零
    渲染），每张 PNG 在盘且 sha256=witness 记录值；reader 接触范围——
    reader-raw-holdout-*.txt 恰 18 件、board 集合恰为同 3 板、每板
    top/bottom × i1/i2/i3 全齐。

    ③ 冻结 registration 零回写：盘上哈希=36cc86a7…（冻结件不变），
    holdout_plan_ref.started 仍为 False——registration=2026-09-10 启动
    前时点冻结件，按「修订=新版本文件，不回写本件」纪律不随启动改写；
    启动状态由 holdout-run-r1.json / holdout-dev-record-r1.json 承载
    （追加式演进）。

    另：datasets/holdout-candidates-r1 下无渲染产物的原有检查保留。"""
    # -- ① 启动前零接触历史证据（precheck 只读预检件，钉死） --------------
    assert _sha(HOLDOUT_PLAN_PATH) == HOLDOUT_PLAN_SHA256
    precheck_disk = _sha(os.path.join(REPO, HOLDOUT_PRECHECK_REL))
    assert precheck_disk.startswith(PRECHECK_SHA256_PREFIX), \
        f"precheck-r1.json 哈希前缀不符: {precheck_disk[:16]}*"
    precheck = _json_load(HOLDOUT_PRECHECK_REL)
    for key in ("zero_render", "zero_reader", "zero_image_tooling"):
        assert precheck["discipline"][key] is True, f"discipline.{key}"

    # -- ② 启动后一次性纪律证据链 ----------------------------------------
    names = os.listdir(HOLDOUT_DIR)

    # 正式链五件在盘且 sha256 前缀匹配
    for fname, prefix in HOLDOUT_FORMAL_CHAIN_PREFIXES.items():
        path = os.path.join(HOLDOUT_DIR, fname)
        assert os.path.exists(path), f"holdout 正式链缺件: {fname}"
        actual = _sha(path)
        assert actual.startswith(prefix), \
            (f"{fname} sha256 前缀不符: 期望 {prefix}*，"
             f"实测 {actual[:16]}*")

    # 渲染范围纪律：renders* 目录恰为 {renders-holdout-r1}
    renders_dirs = {n for n in names
                    if n.startswith("renders")
                    and os.path.isdir(os.path.join(HOLDOUT_DIR, n))}
    assert renders_dirs == {"renders-holdout-r1"}, \
        (f"holdout renders* 目录应恰为 {{renders-holdout-r1}}: "
         f"{sorted(renders_dirs)}")

    # witness renders 列表：6 张、board 集合恰为 3 块已选 holdout 板
    with open(os.path.join(HOLDOUT_DIR, "render-witness-holdout-r1.json"),
              encoding="utf-8") as f:
        witness = json.load(f)
    renders = witness["renders"]
    assert len(renders) == 6, f"witness renders 应 6 张: {len(renders)}"
    witness_boards = {e["name"].rsplit("-", 1)[0] for e in renders}
    assert witness_boards == HOLDOUT_BOARDS, \
        (f"witness renders board 集合应恰为已选 3 板: "
         f"{sorted(witness_boards)}")
    for e in renders:
        png_path = os.path.join(REPO, e["png_rel"])
        assert os.path.exists(png_path), \
            f"witness PNG 缺盘上件: {e['png_rel']}"
        disk_png = _sha(png_path)
        assert disk_png == e["sha256"], \
            (f"PNG sha256 与 witness 记录不符: {e['png_rel']} "
             f"盘上 {disk_png[:16]}* / 记录 {e['sha256'][:16]}*")

    # reader 接触范围：恰 18 件、board 集合恰为 3 板、每板全组合齐
    reader_files = sorted(n for n in names
                          if n.startswith("reader-raw-holdout-")
                          and n.endswith(".txt"))
    assert len(reader_files) == 18, \
        (f"holdout reader-raw-holdout-*.txt 应恰 18 件: "
         f"{len(reader_files)}")
    reader_units = set()
    reader_boards = set()
    for n in reader_files:
        stem = n[len("reader-raw-holdout-"):-len(".txt")]
        board, view, instance = stem.rsplit("-", 2)
        reader_boards.add(board)
        reader_units.add((board, view, instance))
    assert reader_boards == HOLDOUT_BOARDS, \
        f"reader 接触 board 集合应恰为已选 3 板: {sorted(reader_boards)}"
    expected_units = {(b, v, i) for b in HOLDOUT_BOARDS
                      for v in HOLDOUT_VIEWS
                      for i in HOLDOUT_INSTANCES}
    assert reader_units == expected_units, \
        ("reader 单位应恰为 3 板 × top/bottom × i1/i2/i3 全齐: 缺 "
         f"{sorted(expected_units - reader_units)} 多 "
         f"{sorted(reader_units - expected_units)}")

    # -- ③ 冻结 registration 零回写 ---------------------------------------
    # registration=2026-09-10 启动前时点冻结件：按「修订=新版本文件，
    # 不回写本件」纪律不随启动改写（盘上哈希不变）；启动状态由
    # run/dev-record 承载（追加式演进），故 started 仍为 False 非失真。
    assert _sha(REG_PATH) == REG_SHA256
    hp = reg["holdout_plan_ref"]
    assert hp["started"] is False
    assert hp["sha256"] == HOLDOUT_PLAN_SHA256
    assert hp["timing"] == "用户判断的独立人工点（v2 冻结不构成启动指令）"

    # -- datasets/holdout-candidates-r1 无渲染产物（原有检查保留） --------
    for root, _dirs, files in os.walk(
            os.path.join(REPO, "datasets", "holdout-candidates-r1")):
        for fn in files:
            assert not fn.lower().endswith((".png", ".jpg", ".jpeg")), \
                f"holdout 候选树出现渲染产物: {os.path.join(root, fn)}"


# ---------------------------------------------------------------------------
# 13. P2 条款 registration↔md 对齐 + 装配说明
# ---------------------------------------------------------------------------

def test_p2_clauses_registration_matches_md(reg, v2_text):
    """registration.p2_clauses 九条与 v2 md §1 逐条对齐（id 集合一
    致、每条 text 关键词在 md 中出现、1–8 from=§3 P2、9 from=§5）；
    装配说明（§3 P2 原列八条+§5 红线并入）两处齐。"""
    clauses = reg["p2_clauses"]
    assert [c["id"] for c in clauses] == \
        [f"P2-{i}" for i in range(1, 10)]
    for c in clauses:
        assert c["id"] in v2_text
        # text 摘要关键词化后在 md 中可对齐（取 text 首个 ≥6 字片段）
        key = c["text"].split("/")[0][:6]
        assert key in v2_text, f"{c['id']} text 与 md 不对齐: {key}"
    for c in clauses[:8]:
        assert c["from"].endswith("§3 P2")
    assert "§5" in clauses[8]["from"] and "并入" in clauses[8]["from"]
    assert "原列八条" in reg["p2_clauses_assembly_note"]
    assert "§5 治理红线并入" in reg["p2_clauses_assembly_note"]
    assert "装配事实" in v2_text


# ---------------------------------------------------------------------------
# 14. s79 幂等重跑 + 打印两件 sha256
# ---------------------------------------------------------------------------

def test_s79_rerun_idempotent_and_prints_hashes(capsys):
    """s79 重跑幂等（已存在且字节等同→idempotent_skip、盘上哈希不
    变）；末尾打印两件 sha256（v2 md=365b67ef…、registration=
    36cc86a7…全值）；主流程输出含边界声明与现状登记关键锚。"""
    before = (_sha(V2_PATH), _sha(REG_PATH))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        S79.main()
    out = buf.getvalue()
    assert "idempotent_skip" in out
    assert V2_SHA256 in out
    assert REG_SHA256 in out
    assert (_sha(V2_PATH), _sha(REG_PATH)) == before
    for anchor in ("in_calibrated_range=False", "blocked",
                   "v2 生效≠holdout 启动", "r19=marginal",
                   "停止同一调参轴", "带内复现", "用户拍板"):
        assert anchor in out, f"s79 输出缺锚: {anchor}"
