"""R10 执行包测试：reader 判读迭代第十轮收口（CAL-R10-CLOSE）——
盲读解析与视角注入 + 双态 compare_v3 重投影比对 + 分视角弃权分层
（bottom 零旗标=分母为零 rate=null 如实处理）+ 预注册假设
（r9-dev-record-candidate-0a）三分裁决（字母裁决唯一正式+机制观察
单列+度量设计教训）+ 逐旗失败通道归因（vs R9，链自 r6）+ courtyard
被动追踪（含 bottom「正常特征→不报告」通道使用观察）+ development
域记录（引用 gt-audit-r1 结论：GT 侧已全部关闭）。

结构照 test_r9_calibration_round9.py 先例，仅输入与轮次常量不同
（R10=development 域零变更重复轮：同指引（observation-guidance-r9.md
零字节复用+机械命名覆盖 R9T/R9B→R10T/R10B）+同渲染（R5 冻结件复用）
+全新四实例盲读；恰零个变更变量，唯一操纵=reader 实例群更替；预注册
于 r10-prep-record.json，链=r9-dev-record（5ee18d61）→r10-prep-record
（3791edb1）；检验 R9 预注册候选假设 r9-dev-record-candidate-0a，
裁决边界=0.5（与 APR-0011 门各自独立计算、互不凌驾））。

覆盖：
- 盲读原文（reader-raw-r10-{applied,prep1}-{top,bottom}.txt，冻结证据）：
  合法 JSON、结构（reader_id/per_image/reading_notes；flag 六键含
  location_evidence）、视角前缀一致（R10T-001..014 top 跨两文件连续、
  bottom 零旗标）、拒收清单固化（全 14 旗标过 calibration fail-closed
  校验，0 拒收）、哈希与 run-r10 登记一致（锚 f7a0e52b/6af5a740/
  1b2f285c/7c6baf43）；
- 视角注入确定性：s43 的图像名→视角映射纯函数两次调用一致，
  run-r10 记录的 flag_views 与该规则逐旗标一致；两波并行派发记录
  （与 R7/R8/R9 同模式）；读者实例披露（reader_instance_note：3/4
  实例 PIL 局部裁剪放大/像素级连通域枚举、applied-top 纯 Read 直读=
  仪器行为面摆动；输出格式异常三例=非盲读违规；实例群更替捆绑采样
  差异与工具行为差异无法分离=混杂因素如实入账不作废）与分视角旗标/
  弃权计数；
- calibration-run-r10.json：盘上 canonical byte 一致；两态 compare_v3
  用记录内嵌输入（reader_flags/gt_entries/flag_views）重算 byte-exact
  一致且 view_check=full；内嵌 gt_entries=源 GT 文件条目（frame_box_pct
  ←derivation-log-r5 的 frame_box_pct_r5——渲染未变零新派生，其余
  字段逐字段原样）；聚合算术显式复算一致（1/13、1/10、4/14=0.285714）；
  分视角弃权率 top 4/14=0.285714、bottom 0/0 rate=null（零旗标无弃权
  率定义，不编造数值）、分态 applied 1/2=0.5、prep1 3/12=0.25；达标
  评估逐项复算一致（APR-0011：abstain_rate 0.285714≤0.5 与 gt_count
  达线、recall 0.076923/seed 0.1 未达→joint=not_met）、连续达标计数
  0→0、critic_calibration_in_range=False、域=development；
- 预注册假设三分裁决：判据引用=r10-prep-record.json hypothesis_test
  原文（support=≤0.5/reject=>0.5 原样）；实测 abstain_rate_total
  0.285714≤0.5⇒verdict=supported（字母裁决，判据复算一致；0.5 与
  APR-0011 门独立分列——门联合 not_met 与裁决 supported 不合并）；
  机制观察单列（reroute 类产量 r8=1→r9=0→r10=2，R10T-012/013 均弃权
  且 location_evidence 明确援引示例 c——r9「刺激缺席」被证伪为实例群
  特异；示例 c 实际功能=弃权理由词汇非化解、与「化解通道」方向相反
  如实记录；reader_note_evidence/location_evidence 逐字摘录 substring
  校验）；度量设计教训单列（弃权率单实例/轮度量不稳定 0.222222→
  0.727273→0.285714；工具行为捆绑混杂——下一轮协议侧候选 n≥3 重复读
  或跨轮中位数门控，不回溯改判本轮）；
- 通道归因（channel_attribution）：对 run-r9 内嵌输入与 run-r10 内嵌
  输入重放通道分类与登记一致；重放 candidate 对与两轮 compare_v3
  matches∪duplicate_reports 对拍（R9 两态均空→R10 prep1 恰 1 对=
  R10T-011↔GT-REVC-P1-R4J3 成 matches：geo=0/cat=0 两轮均空）；
  R8/R10 基线匹配明细可独立复算（R8T-004↔AP-8 containment 0.838782
  面积比 2.688288；R10T-011↔R4J3 containment 0.829864 面积比
  1.770688）；通道链自 r6 起（几何 1→0→0→0→0；类别 1→0→1→0→0）；
  R10 特有观察可独立复算；
- courtyard 被动追踪（prep-record 预注册）：非弃权 3 条（R10T-009/
  010/011；R10T-011 命中、009/010 零交集）、弃权 1 条（R10T-002）；
  courtyard 匹配 r8=1→r9=0→r10=1；bottom 两格 0 旗=「正常特征→不
  报告」通道首次被实例群使用（applied-bottom 原文摘录逐字校验）；
  阈值零改动、零期望；
- 预注册链：r9-dev-record（5ee18d61）→r10-prep-record（3791edb1）→
  run-r10 链含哈希；guidance-r9 零字节复用（a0c10154）/r8 基线
  （aad43270）/framing-r5/derivation-log-r5/GT/协议/复用 PNG/冻结
  PDF sha 与盘上一致；阈值常量零覆盖（containment 0.5 /
  area_ratio_max 10.0 与 r9 相同）；gt-audit-r1 引用（1f20554a）在案；
- round10-dev-record.json：域声明、零变更重复轮性质、假设三分裁决节
  与 run-r10 一致、R9→R10 方向性观察（无能力断言、通道数值可独立
  复算）、联合评价趋势（r5→r10 逐轮表、连续计数 0→0，正式采纳门槛
  未达成）、run-r10 sha 引用一致、next_iteration_targets 覆盖度量
  稳定性候选（n≥3 多实例重复读/跨轮中位数门控，须预注册）/示例 c
  去留评估候选（弃权理由词汇效应 vs 化解目标）/渲染侧 bottom 图层
  清单延续/courtyard 追踪延续/GT 侧已全关闭声明延续、is_gate=False、
  in_calibrated_range 恒 False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；机械命名覆盖 R9T/R9B→R10T/R10B 与
  reader-r9-*→reader-r10-* 入 naming_constraints；受保护三文件
  sha256 前 8 断言；
- s43 重跑：同参重建 byte-exact 一致 + 防覆写护栏语义（字节等同→
  幂等跳过零覆写、不同→fail-closed）。

只读 out/（生成器模式）：零子进程/零写盘/零网络。
"""

import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import calibration as cal           # noqa: E402
from pcbflow import critic                       # noqa: E402
from pcbflow import hashing                      # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

ROUND_ID = "2026-09-07-r10"
DECLARED_DATE = "2026-09-07"
RAW_FILES = {
    "applied-top": "reader-raw-r10-applied-top.txt",
    "applied-bottom": "reader-raw-r10-applied-bottom.txt",
    "prep1-top": "reader-raw-r10-prep1-top.txt",
    "prep1-bottom": "reader-raw-r10-prep1-bottom.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top": "f7a0e52b", "applied-bottom": "6af5a740",
    "prep1-top": "1b2f285c", "prep1-bottom": "7c6baf43",
}
READER_IDS = {
    "applied-top": "reader-r10-top", "applied-bottom": "reader-r10-bottom",
    "prep1-top": "reader-r10-top", "prep1-bottom": "reader-r10-bottom",
}
READER_FLAG_KEYS = {"flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence"}
GT_V1_IDS = ["GT-REVC-P1-R4J3", "GT-REVC-P1-F1J2", "GT-REVC-P1-L1NB",
             "GT-REVC-P1-L1SHORT"]
GT_V2_IDS = [
    "GT-REVC-AP-1-R5U6", "GT-REVC-AP-2-Y1C35", "GT-REVC-AP-3-Y1C5",
    "GT-REVC-AP-4-Y1C36", "GT-REVC-AP-5-Y1C4", "GT-REVC-AP-6-R2LED2",
    "GT-REVC-AP-7-C31U4", "GT-REVC-AP-8-R1Q2", "GT-REVC-AP-9-Y2C3",
]
#: 受保护文件（R10-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: 预注册件哈希锚（先验给定的前 8）
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r9.md": "a0c10154",
    "out/v3-tl2/calibration/r10-prep-record.json": "3791edb1",
    "out/v3-tl2/calibration/round9-dev-record.json": "5ee18d61",
    "out/v3-tl2/calibration/observation-guidance-r8.md": "aad43270",
    "out/v3-tl2/calibration/r9-prep-record.json": "dd979632",
    "out/v3-tl2/calibration/round8-dev-record.json": "437e149c",
    "out/v3-tl2/calibration/render-framing-r5.json": "860aa910",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
    "out/v3-tl2/calibration/r8-prep-record.json": "237920a5",
    "out/v3-tl2/calibration/r7-prep-record.json": "e48c37fe",
    "out/v3-tl2/calibration/calibration-run-r9.json": "e16420e5",
    "out/v3-tl2/calibration/calibration-run-r8.json": "3c580eb3",
}
BOTTOM_PNG_SHA256 = (
    "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9")
STATE_OF_KEY = {"applied-top": "applied", "applied-bottom": "applied",
                "prep1-top": "prep1", "prep1-bottom": "prep1"}
VIEW_OF_KEY = {"applied-top": "top", "applied-bottom": "bottom",
               "prep1-top": "top", "prep1-bottom": "bottom"}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s43():
    spec = importlib.util.spec_from_file_location(
        "s43_calibration_r10_compare",
        os.path.join(REPO, "scripts", "s43_calibration_r10_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r10.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round10-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r10_files_valid_structure_and_prefixes():
    seen_ids = {"top": [], "bottom": []}
    expect_counts = {"applied-top": 2, "applied-bottom": 0,
                     "prep1-top": 12, "prep1-bottom": 0}
    expect_abstain = {"applied-top": 1, "applied-bottom": 0,
                      "prep1-top": 3, "prep1-bottom": 0}
    reroute_ids, reroute_abstain = [], []
    for key, name in RAW_FILES.items():
        assert _sha("out/v3-tl2/calibration/" + name).startswith(
            RAW_SHA256_FIRST8[key])                  # 与派发哈希锚一致
        d = _load(name)
        assert d["reader_id"] == READER_IDS[key]
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        assert img["image"] == "%s.png" % key           # 图名=文件名对齐
        assert len(img["flags"]) == expect_counts[key]
        view = VIEW_OF_KEY[key]
        prefix = {"top": "R10T-", "bottom": "R10B-"}[view]
        n_abstain = 0
        for f in img["flags"]:
            assert set(f) == READER_FLAG_KEYS           # 六键（含位置证据）
            assert f["flag_id"].startswith(prefix)      # 视图前缀一致
            assert f["category"] in critic.FLAG_CATEGORIES
            assert isinstance(f["abstain"], bool)
            assert 0.0 <= float(f["confidence"]) <= 1.0
            box = f["frame_box_pct"]
            assert len(box) == 4 and all(0.0 <= v <= 1.0 for v in box)
            assert box[0] < box[2] and box[1] < box[3]
            assert f["location_evidence"].strip()
            n_abstain += 1 if f["abstain"] else 0
            if f["category"] == "suspicious_reroute":
                reroute_ids.append(f["flag_id"])
                reroute_abstain.append(f["abstain"])
            seen_ids[view].append(f["flag_id"])
        assert n_abstain == expect_abstain[key]
        assert d["reading_notes"].strip()
    # top 视 R10T-001..014 跨两文件连续（applied-top 001..002→prep1-top
    # 003..014）；bottom 视零旗标（R10B 前缀已派发、零产出）
    assert seen_ids["top"] == ["R10T-%03d" % i for i in range(1, 15)]
    assert seen_ids["bottom"] == []
    # reroute 类旗标恰 2 条（R10T-012/013）且均弃权（location_evidence
    # 明确援引「r9 示例 c」判据）
    assert reroute_ids == ["R10T-012", "R10T-013"]
    assert reroute_abstain == [True, True]
    prep1 = _load("reader-raw-r10-prep1-top.txt")["per_image"][0]["flags"]
    loc = {f["flag_id"]: f["location_evidence"] for f in prep1}
    assert "r9 示例 c" in loc["R10T-012"] and "弃权" in loc["R10T-012"]
    assert "r9 示例 c" in loc["R10T-013"] or "等长匹配" in loc["R10T-013"]
    # 合计 14 旗=10 非弃权+4 弃权（盘面口径与聚合一致）
    total = sum(expect_counts.values())
    abstain = sum(expect_abstain.values())
    assert total == 14 and abstain == 4 and total - abstain == 10


def test_parse_replay_no_rejections_view_injection_and_reader_instance_note():
    s43 = _s43()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s43.RAW_FILES.items():
        parsed = s43.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s43.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则
    assert s43.view_for_image("applied-top.png") == "top"
    assert s43.view_for_image("prep1-bottom.png") == "bottom"
    assert s43.view_for_image("applied-top.png") == s43.view_for_image(
        "applied-top.png")
    try:
        s43.view_for_image("mystery.png")
    except ValueError:
        pass
    else:
        raise AssertionError("无视角后缀图像名应 ValueError（fail-closed）")
    run, _ = _run_record()
    for key in RAW_FILES:
        want = {img["image"]: img["view"] for img in replay[key]["images"]}
        got = run["reader"]["view_injection"]["mapping"][key]
        assert got == want == {("%s.png" % key): VIEW_OF_KEY[key]}
        replay_ids = [f["flag_id"] for img in replay[key]["images"]
                      for f in img["flags"]]
        block = run["states"][STATE_OF_KEY[key]]
        for fid in replay_ids:
            assert block["flag_views"][fid] == VIEW_OF_KEY[key]
            assert fid in [f["flag_id"] for f in block["reader_flags"]]
    assert run["parse_rejections"] == []                # 拒收清单固化（空）
    # 旗标计数（按 image / by_state / by_view / by_category 分层；总 14）
    fc = run["reader"]["flag_count"]
    assert fc["applied_top"] == 2 and fc["applied_bottom"] == 0
    assert fc["prep1_top"] == 12 and fc["prep1_bottom"] == 0
    assert fc["by_state"] == {"applied": 2, "prep1": 12}
    assert fc["by_view"] == {"top": 14, "bottom": 0}
    assert fc["abstain_by_view"] == {"top": 4, "bottom": 0}
    assert fc["reroute_class_production"] == 2
    assert fc["by_category"] == {
        "courtyard_crowding": {"total": 4, "non_abstain": 3, "abstain": 1},
        "silk_readability": {"total": 7, "non_abstain": 7, "abstain": 0},
        "suspicious_reroute": {"total": 2, "non_abstain": 0, "abstain": 2},
        "other_advisory": {"total": 1, "non_abstain": 0, "abstain": 1}}
    assert fc["total"] == 14
    # 两波并行派发记录（与 R7/R8/R9 同模式）+ 零 GT 派发词 + 编号连续
    pd = run["reader"]["parallel_dispatch"]
    assert pd["mode"] == "two_wave_parallel"
    assert pd["wave_1_parallel"] == ["applied-top", "applied-bottom"]
    assert pd["wave_2_parallel"] == ["prep1-top", "prep1-bottom"]
    assert pd["flag_id_continuity"] == {
        "top": "R10T-001..014（applied 001..002→prep1 003..014）",
        "bottom": "R10B 前缀已派发；本轮 bottom 两格零旗标（R10B-xxx "
                  "零产出）"}
    assert "R6=四图独立全串行" in pd["diff_note"]
    assert "R10 与 R7/R8/R9 派发模式相同" in pd["diff_note"]
    assert "机械命名覆盖" in pd["diff_note"]
    assert "两波并行" in run["reader"]["dispatch_discipline"]
    assert "R10T-001..014" in run["reader"]["dispatch_discipline"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r9.md" in \
        run["reader"]["dispatch_discipline"]
    # 读者实例披露（R10 特有：工具行为异质性+输出格式异常，如实入账）
    note = run["reader"]["reader_instance_note"]
    assert "PIL" in note and "applied-top" in note       # 1 个纯 Read 直读
    assert "连通域" in note and "2x-6x" in note          # 3 个 PIL 放大
    assert "非盲读违规" in note
    assert "采样差异" in note and "自选工具行为差异" in note
    assert "无法分离" in note                            # 捆绑混杂如实
    assert "混杂因素" in note and "不作废" in note and "n=1" in note
    assert "围栏" in note and "缩进" in note and "前置文字" in note
    # 逐文件格式异常登记（编排侧落盘前处理；盘上件=冻结证据）
    fm = run["reader"]["parse"]
    assert "纯 JSON" in fm["applied-top"]["raw_message_format_note"]
    assert "前置文字" in fm["applied-bottom"]["raw_message_format_note"]
    assert "缩进" in fm["prep1-top"]["raw_message_format_note"]
    assert "围栏" in fm["prep1-bottom"]["raw_message_format_note"]
    assert "r7 先例" in fm["prep1-bottom"]["raw_message_format_note"]


# ---------------------------------------------------------------------------
# run-r10：canonical、常量、域声明、零仪器变更、受保护文件、courtyard 追踪
# ---------------------------------------------------------------------------

def test_run_r10_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r10"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r10"
    assert rec["declared_date"] == DECLARED_DATE
    assert rec["metric_version"] == "calibration-metric-v3"
    assert rec["preregistration"]["round_id_constant"] == ROUND_ID
    for key in rec:                                     # 无机器时间戳键
        assert key in ("declared_date",) or (
            "time" not in key.lower() and "date" not in key.lower())
    # development 域声明（协议 v1 §1/§4：迭代轮不得冒充留出证据）
    assert rec["evaluation_domain"] == "development"
    note = rec["evaluation_domain_note"]
    assert note["declared"] == "development"
    assert note["in_calibrated_range"] is False
    assert "不得冒充未见留出" in note["basis_quote"]
    assert note["protocol_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/evaluation-protocol-v1.md")
    assert rec["compliance"]["critic_calibration_in_range"] is False
    # 零仪器变更声明（零变更重复轮：恰零个变更变量、唯一操纵=实例群更替）
    ic = rec["instrument_change"]
    assert ic["nature"].startswith("零仪器变更")
    assert "实例群更替" in ic["nature"]
    assert ic["components"] == []                       # 恰零个变更变量
    # unchanged 与 r10-prep-record.json 登记逐字一致（锚 3791edb1）
    prep = _load("r10-prep-record.json")
    assert ic["unchanged_components"] == prep["unchanged_components"]
    assert prep["no_instrument_change"] is True
    assert prep["changed_variables"] == []
    assert prep["renders_reuse"]["no_instrument_change"] is True
    assert "实例群更替" in ic["attribution_note"]
    assert "互不凌驾" in ic["attribution_note"]
    assert "reader_instance_note" in ic["attribution_note"]
    assert "弃权理由词汇" in ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r10-prep-record.json")
    # 复用 R5 渲染：零重渲染声明与四 PNG 见证（盘上 sha=prep-record 实测）
    for w in prep["renders_reuse"]["png_witness"]:
        assert w["match_to_witness_constant"] is True
        assert _sha(w["path_rel"]) == w["sha256_measured"]
    assert prep["guidance_reuse"]["zero_byte_reuse"] is True
    assert prep["guidance_reuse"]["match"] is True
    # 同日只读 GT 审计引用（1f20554a；结论=GT 侧已全部关闭，本轮延续）
    ref = rec["gt_audit_reference"]
    assert ref["sha256"] == _sha("out/v3-tl2/calibration/gt-audit-r1.json")
    assert ref["sha256"].startswith("1f20554a")
    assert "bottom GT=无源已关闭" in ref["note"]
    assert "reroute GT=无源已关闭" in ref["note"]
    assert "L1NB 框径=合理维持现框" in ref["note"]
    assert "非本轮预注册件" in ref["note"]
    assert "已全部关闭" in ref["note"]                  # GT 侧候选关闭声明
    # 受保护三文件零改动（sha256 前 8）
    for rel, want in PROTECTED_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])
    # courtyard 被动追踪键（prep-record 预注册；零阈值改动、零期望）
    ct = rec["courtyard_tracking"]
    assert ct["note_source"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r10-prep-record.json")
    assert ct["note_source"]["quote"] == prep["hypothesis_test"][
        "secondary_observation"]
    na = ct["r10_courtyard_flags"]["non_abstain"]
    ab = ct["r10_courtyard_flags"]["abstain"]
    assert [r["flag_id"] for r in na] == ["R10T-009", "R10T-010",
                                          "R10T-011"]
    assert [r["flag_id"] for r in ab] == ["R10T-002"]
    hit = next(r for r in na if r["matches"])
    assert hit["flag_id"] == "R10T-011"
    assert hit["matched_detail"] == {"gt_id": "GT-REVC-P1-R4J3",
                                     "containment": 0.829864,
                                     "area_ratio": 1.770688}
    assert all(r["containment_all_none"] is True and r["matches"] == 0
               for r in na if r["flag_id"] != "R10T-011")   # 零交集
    assert ct["courtyard_matches_r10"] == 1
    assert ct["courtyard_matches_r9"] == 0
    assert ct["courtyard_matches_r8"] == 1              # R8T-004↔AP-8
    assert "R8T-004" in ct["courtyard_matches_r8_detail"]
    assert "零改动" in ct["threshold_note"]
    assert "零期望" in ct["declaration"]
    # bottom 零旗标观察（「正常特征→不报告」通道首次被实例群使用）
    bz = ct["bottom_zero_flag_observation"]
    assert "正常特征→不报告" in bz["channel_used"]
    assert "0 旗标" in bz["fact"]
    for ev in bz["evidence"]:
        raw = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                                RAW_FILES[ev["source"]]),
                   encoding="utf-8").read()
        assert ev["excerpt"] in raw                     # 逐字摘录校验
    assert "substring" in bz["evidence_check"]


def test_run_r10_compare_v3_recompute_byte_exact():
    rec, _ = _run_record()
    for st in ("prep1", "applied"):
        block = rec["states"][st]
        rep = cal.compare_v3(block["reader_flags"], block["gt_entries"],
                             flag_views=block["flag_views"])
        assert hashing.canonical_json_bytes(rep) == \
            hashing.canonical_json_bytes(block["compare_v3"])   # byte-exact
        assert block["view_check"] == rep["view_check"] == "full"
        assert block["flag_views"]                              # 视角已注入
        assert all(v in ("top", "bottom")
                   for v in block["flag_views"].values())
        r = block["compare_v3"]
        # 阈值常量零覆盖（与 r9 相同的声明常量）
        assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
        assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
        assert r["metric_version"] == "calibration-metric-v3"
    # applied 态零匹配（弃权 1：R10T-002）
    ra = rec["states"]["applied"]["compare_v3"]
    assert ra["matches"] == []
    assert ra["reader_matched_ids"] == []
    assert ra["gt_matched_count"] == 0
    assert ra["duplicate_reports"] == []
    assert ra["reader_unmatched_ids"] == ["R10T-001"]
    assert ra["abstain"]["abstain_ids"] == ["R10T-002"]
    assert "reader_false_positive_ids" not in ra
    # prep1 态恰 1 匹配（R10T-011↔GT-REVC-P1-R4J3；弃权 3：012/013/014）
    rp = rec["states"]["prep1"]["compare_v3"]
    assert len(rp["matches"]) == 1
    m = rp["matches"][0]
    assert (m["flag_id"], m["gt_id"], m["category"], m["containment"],
            m["area_ratio"]) == ("R10T-011", "GT-REVC-P1-R4J3",
                                 "courtyard_crowding", 0.829864, 1.770688)
    assert rp["reader_matched_ids"] == ["R10T-011"]
    assert rp["gt_matched_count"] == 1
    assert rp["duplicate_reports"] == []
    assert rp["reader_unmatched_ids"] == ["R10T-003", "R10T-004", "R10T-005",
                                          "R10T-006", "R10T-007", "R10T-008",
                                          "R10T-009", "R10T-010"]
    assert rp["abstain"]["abstain_ids"] == ["R10T-012", "R10T-013",
                                            "R10T-014"]
    assert "reader_false_positive_ids" not in rp
    # 零交集（containment=None=无交集）的非弃权未匹配旗：R10T-003 与
    # R4J3 有 0.278529 部分交叠（<0.5 未及近邻门、不成匹配但非 None），
    # 故零交集名单不含 R10T-003
    for st, fid in (("applied", "R10T-001"), ("prep1", "R10T-004"),
                    ("prep1", "R10T-009"), ("prep1", "R10T-010")):
        blk = rec["states"][st]
        f = next(f for f in blk["reader_flags"] if f["flag_id"] == fid)
        assert all(cal._containment(f["frame_box_pct"], e["frame_box_pct"])
                   is None for e in blk["gt_entries"])
    # R10T-003 部分交叠但未及近邻门（containment 0.278529<0.5）
    f003 = next(f for f in rec["states"]["prep1"]["reader_flags"]
                if f["flag_id"] == "R10T-003")
    g_r4j3 = next(e for e in rec["states"]["prep1"]["gt_entries"]
                  if e["gt_id"] == "GT-REVC-P1-R4J3")
    assert round(cal._containment(f003["frame_box_pct"],
                                  g_r4j3["frame_box_pct"]), 6) == 0.278529


def test_run_r10_gt_entries_source_plus_reprojection():
    rec, _ = _run_record()
    sources = {"prep1": ("ground-truth-v1.json", GT_V1_IDS),
               "applied": ("ground-truth-v2.json", GT_V2_IDS)}
    for st, (gt_name, ids) in sources.items():
        gt = _load(gt_name)
        by_id = {e["gt_id"]: e for e in gt["gt_entries"]}
        block = rec["states"][st]
        assert [e["gt_id"] for e in block["gt_entries"]] == ids
        for e in block["gt_entries"]:
            src = by_id[e["gt_id"]]
            for k in src:                               # 除 frame_box_pct 外
                if k == "frame_box_pct":                # 逐字段原样
                    continue
                assert e[k] == src[k], (st, e["gt_id"], k)
    # frame_box_pct 恰为 derivation-log-r5 的 frame_box_pct_r5（按 gt_id；
    # 渲染未变=重投影输入未变，本轮零新派生、沿用 r5 台账）
    deriv = {e["gt_id"]: e["frame_box_pct_r5"]
             for e in _load("derivation-log-r5.json")["entries"]}
    for st in ("prep1", "applied"):
        assert "零新派生" in rec["states"][st]["gt_reprojection"]["note"]
        for e in rec["states"][st]["gt_entries"]:
            assert e["frame_box_pct"] == deriv[e["gt_id"]]
            assert 0.0 <= e["frame_box_pct"][0] < e["frame_box_pct"][2] <= 1.0
            assert 0.0 <= e["frame_box_pct"][1] < e["frame_box_pct"][3] <= 1.0
            assert e["side"] == "top"                   # 13 条全部 top


# ---------------------------------------------------------------------------
# 聚合算术、分视角分层、达标评估
# ---------------------------------------------------------------------------

def test_run_r10_aggregation_and_stratified_abstain():
    rec, _ = _run_record()
    p = rec["states"]["prep1"]["compare_v3"]
    a = rec["states"]["applied"]["compare_v3"]
    agg = rec["aggregation"]
    n_gt = p["gt_count"] + a["gt_count"]
    n_match = len(p["matches"]) + len(a["matches"])
    n_gm = p["gt_matched_count"] + a["gt_matched_count"]
    n_sc = p["reader_scored_count"] + a["reader_scored_count"]
    n_ab = p["abstain"]["abstain_count"] + a["abstain"]["abstain_count"]
    n_fl = p["reader_flag_count"] + a["reader_flag_count"]
    assert agg["gt_count_total"] == n_gt == 13
    assert agg["matches_total"] == n_match == 1
    assert agg["gt_matched_total"] == n_gm == 1
    assert agg["scored_total"] == n_sc == 10
    assert agg["abstain_count_total"] == n_ab == 4
    assert agg["flag_count_total"] == n_fl == 14
    assert agg["gt_recall_total"] == round(1 / 13, 6) == 0.076923
    assert agg["seed_match_rate_total"] == round(1 / 10, 6) == 0.1
    assert agg["abstain_rate_total"] == round(4 / 14, 6) == 0.285714
    for f in ("gt_recall_arithmetic", "seed_match_rate_arithmetic",
              "abstain_rate_arithmetic"):
        assert f in agg and isinstance(agg[f], str) and agg[f].strip()
    assert "1/13" in agg["gt_recall_arithmetic"]
    assert "1/10" in agg["seed_match_rate_arithmetic"]
    assert "4/14" in agg["abstain_rate_arithmetic"]
    assert agg["abstain_rate_definition"] == cal.ABSTAIN_RATE_DEFINITION
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE
    # 分态弃权率（applied 1/2、prep1 3/12）
    bvs = agg["abstain_rate_by_state"]
    assert bvs["applied"] == round(1 / 2, 6) == 0.5
    assert bvs["applied_fraction"] == "1/2"
    assert bvs["prep1"] == round(3 / 12, 6) == 0.25
    assert bvs["prep1_fraction"] == "3/12"
    # 分视角弃权率（top 4/14；bottom 0/0 零旗标=rate=null 如实处理）
    bvv = agg["abstain_rate_by_view"]
    assert bvv["top"] == round(4 / 14, 6) == 0.285714
    assert bvv["top_fraction"] == "4/14"
    assert bvv["bottom"] is None                        # 零旗标无弃权率定义
    assert bvv["bottom_fraction"] == "0/0"
    assert "零旗标" in bvv["bottom_note"] and "null" in bvv["bottom_note"]
    assert "不编造" in bvv["bottom_note"]
    assert "4/14" in agg["abstain_rate_by_view_arithmetic"]
    assert "0/0" in agg["abstain_rate_by_view_arithmetic"]


def test_run_r10_compliance_matches_recomputed():
    rec, _ = _run_record()
    agg = rec["aggregation"]
    comp = rec["compliance"]
    criteria = {c["id"]: c for c in comp["criteria"]}
    # 逐项复算（APR-0011 基线；阈值措辞与协议一致，禁改）
    assert criteria["gt_count_ge_12"]["actual"] == agg["gt_count_total"]
    assert criteria["gt_count_ge_12"]["met"] == \
        (agg["gt_count_total"] >= 12) is True
    assert criteria["gt_recall_ge_0.75"]["actual"] == agg["gt_recall_total"]
    assert criteria["gt_recall_ge_0.75"]["met"] == \
        (agg["gt_recall_total"] >= 0.75) is False
    assert criteria["seed_match_rate_ge_0.5"]["actual"] == \
        agg["seed_match_rate_total"]
    assert criteria["seed_match_rate_ge_0.5"]["met"] == \
        (agg["seed_match_rate_total"] >= 0.5) is False
    # 弃权率重新入线（0.285714 ≤ 0.5）：单分项 met 如实
    assert criteria["abstain_rate_le_0.5"]["actual"] == \
        agg["abstain_rate_total"] == 0.285714
    assert criteria["abstain_rate_le_0.5"]["met"] == \
        (agg["abstain_rate_total"] <= 0.5) is True
    assert "独立计算" in criteria["abstain_rate_le_0.5"]["note"]
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5", "r6",
                                     "r7", "r8", "r9", "r10"}
    assert consec["rounds"]["r9"] == "not_met（在案）"
    assert consec["rounds"]["r10"] == "not_met（本轮）"
    assert "重新入线" in consec["note"]
    assert "仍 not_met" in consec["note"]
    # 联合评价如实（任一不满足即未达标——recall/seed 两项未达）
    all_met = all(c["met"] for c in comp["criteria"]) and consec["met"]
    assert comp["joint_evaluation"] == ("met" if all_met else "not_met")
    assert comp["joint_evaluation"] == "not_met"
    assert comp["critic_calibration_in_range"] is False   # 谓词恒 False
    assert "达标≠自动分流" in comp["critic_calibration_in_range_note"]
    assert "恒 False" in comp["critic_calibration_in_range_note"]


# ---------------------------------------------------------------------------
# 预注册假设三分裁决（字母裁决唯一正式+机制观察+度量设计教训）
# ---------------------------------------------------------------------------

def test_run_r10_hypothesis_three_part_verdict_preregistered():
    rec, _ = _run_record()
    prep = _load("r10-prep-record.json")
    ht = rec["hypothesis_test"]
    assert ht["kind"] == "preregistered_hypothesis_test"
    assert ht["hypothesis_id"] == "r9-dev-record-candidate-0a"
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r10-prep-record.json")
    # 判据引用=r10-prep-record.json hypothesis_test 原文（逐字一致）
    quote = ht["preregistered_criteria_quote"]
    for k in ("hypothesis", "support_condition", "reject_condition",
              "test_design", "null_result_note"):
        assert quote[k] == prep["hypothesis_test"][k], k
    assert quote["candidate_0_plan_a_target"] == \
        prep["hypothesis_test"]["preregistered_criteria_quote"][
            "candidate_0_plan_a_target"]
    assert "候选方案：(a)" in quote["candidate_0_plan_a_target"]
    assert "同指引重复轮" in quote["candidate_0_plan_a_target"]
    assert "≤ 0.5" in quote["support_condition"]
    assert "> 0.5" in quote["reject_condition"]
    assert "正确测出无效同样是有效证据" in quote["null_result_note"]
    assert "互不凌驾" in quote["null_result_note"]
    # 主通道度量=r10-prep-record 登记（abstain_rate_total+裁决边界 0.5）
    assert ht["primary_channel_metric"] == \
        prep["attribution_plan"]["primary_channel"]["metric"]
    # 实测：弃权率 r8=0.222222→r9=0.727273→r10=0.285714≤0.5 边界
    m = ht["measurement"]
    assert m["abstain_rate_r8"] == 0.222222
    assert m["abstain_rate_r9"] == 0.727273
    assert m["abstain_rate_r10"] == 0.285714
    assert m["abstain_rate_r10_fraction"] == "4/14"
    assert m["verdict_boundary"] == 0.5
    assert m["abstain_rate_at_or_below_boundary"] is True
    assert "attribution_plan" in m["boundary_source"]
    # 边界与 APR-0011 门独立分列（互不凌驾；not_met 与 supported 不合并）
    assert "互不凌驾" in m["boundary_independence_note"]
    assert "not_met" in m["boundary_independence_note"]
    assert "supported" in m["boundary_independence_note"]
    # 守门通道：几何门 0→0 无回升（独立复核，非 support_condition 要件）
    g = m["guard_channel"]
    assert g["guard_ok"] is True
    assert "R9=0→R10=0" in g["observation"]
    assert "独立" in g["note"]
    # reroute 类产量对照（prep-record secondary_observation 预注册分支）
    rso = m["reroute_secondary_observation"]
    assert rso["reroute_production_r8"] == 1
    assert rso["reroute_production_r9"] == 0
    assert rso["reroute_production_r10"] == 2
    assert "实例群特异性" in rso["declaration"]
    # 聚合上下文：门联合 not_met 与裁决 supported 分列
    ctx = m["aggregate_context"]
    assert ctx["abstain_rate_r8"] == 0.222222
    assert ctx["abstain_rate_r9"] == 0.727273
    assert ctx["abstain_rate_r10"] == 0.285714
    assert ctx["apr0011_joint_evaluation"] == "not_met"
    assert "互不凌驾" in ctx["note"] and "分列不合并" in ctx["note"]
    # 字母裁决=获支持（预注册判据复算一致；唯一正式裁决）
    assert ht["verdict"] == "supported"
    assert prep["hypothesis_test"]["support_condition"] in ht["verdict_rule"]
    assert prep["hypothesis_test"]["reject_condition"] in ht["verdict_rule"]
    assert "获支持" in ht["verdict_text"]
    assert "唯一正式裁决" in ht["verdict_text"]
    assert "方向性证据非统计证明" in ht["verdict_text"]
    assert "0.222222" in ht["verdict_text"]             # 靠近 r8 一侧
    # 机制观察单列（不凌驾字母裁决）：两条直接结论+摘录逐字在案
    mo = ht["mechanism_observation"]
    assert mo["reroute_flag_production"]["r8"] == 1
    assert mo["reroute_flag_production"]["r9"] == 0
    assert mo["reroute_flag_production"]["r10"] == 2
    assert "R10T-012" in mo["reroute_flag_production"]["r10_detail"]
    assert "不凌驾" in mo["role"]
    assert "证伪" in mo["observation"] and "实例群特异" in mo["observation"]
    assert "J4" in mo["observation"]
    assert "弃权理由" in mo["observation"]
    assert "未化解" in mo["observation"]
    assert "化解通道" in mo["observation"] and "方向相反" in mo["observation"]
    assert "正确测出无效同样是有效证据" in mo["observation"]
    assert "获支持" in mo["conclusion"] and "非统计证明" in mo["conclusion"]
    assert "刺激缺席" in mo["conclusion"]
    assert "PIL" in mo["confounder_note"] and "捆绑" in mo["confounder_note"]
    assert "n=1" in mo["confounder_note"]
    # 摘录逐字来自对应 reader-raw（reading_notes 与原文全文，防转述失真）
    notes = {k: _load(v)["reading_notes"] for k, v in RAW_FILES.items()}
    raws = {k: open(os.path.join(REPO, "out", "v3-tl2", "calibration", v),
                    encoding="utf-8").read() for k, v in RAW_FILES.items()}
    for ev in mo["reader_note_evidence"]:
        assert ev["excerpt"] in notes[ev["source"]], ev["source"]
        assert ev["flag_view"] == VIEW_OF_KEY[ev["source"]]
    for ev in mo["flag_location_evidence"]:
        assert ev["flag_id"] in ("R10T-012", "R10T-013")
        assert ev["excerpt"] in raws[ev["source"]], ev["flag_id"]
    # 机制观察独立复算：R10 恰 2 条 reroute；R9 零；R8 恰 1（R8T-014）
    r10_reroute = [f["flag_id"] for st in ("prep1", "applied")
                   for f in rec["states"][st]["reader_flags"]
                   if f["category"] == "suspicious_reroute"]
    assert r10_reroute == ["R10T-012", "R10T-013"]
    run9 = _load("calibration-run-r9.json")
    r9_reroute = [f["flag_id"] for st in ("prep1", "applied")
                  for f in run9["states"][st]["reader_flags"]
                  if f["category"] == "suspicious_reroute"]
    assert r9_reroute == []
    run8 = _load("calibration-run-r8.json")
    r8_reroute = [f["flag_id"] for st in ("prep1", "applied")
                  for f in run8["states"][st]["reader_flags"]
                  if f["category"] == "suspicious_reroute"]
    assert r8_reroute == ["R8T-014"]
    # 度量设计教训单列：单实例/轮弃权率度量不稳定；候选 n≥3/中位数门控
    ml = ht["metric_design_lesson"]
    assert "不稳定" in ml["lesson"] and "0.222222" in ml["lesson"]
    assert "0.727273" in ml["lesson"] and "0.285714" in ml["lesson"]
    assert "自选工具行为差异" in ml["lesson"]
    assert "n≥3" in ml["status"] and "中位数门控" in ml["status"]
    assert "不得回溯改判本轮" in ml["status"]
    assert "supported 维持" in ml["status"]
    # 分层观察如实附录 + 混杂与优先声明（字母裁决不被机制/分层改写）
    st_ = ht["stratified_observation"]
    assert st_["top"]["r8_rate"] == 0.133333
    assert st_["top"]["r9_rate"] == 0.666667
    assert st_["top"]["r9_fraction"] == "6/9"
    assert st_["top"]["r10_rate"] == 0.285714
    assert st_["top"]["r10_fraction"] == "4/14"
    assert "回落" in st_["top"]["direction"]
    assert st_["bottom"]["r8_rate"] == 0.666667
    assert st_["bottom"]["r9_rate"] == 1.0
    assert st_["bottom"]["r9_fraction"] == "2/2"
    assert st_["bottom"]["r10_rate"] is None
    assert st_["bottom"]["r10_fraction"] == "0/0"
    assert "零旗标" in st_["bottom"]["direction"]
    assert "正常特征→不报告" in st_["bottom"]["direction"]
    assert "混杂因素" in st_["confounder_note"]
    assert "PIL" in st_["confounder_note"]
    assert "不得凌驾字母裁决" in st_["precedence_note"]
    assert "已证因果关系" in st_["precedence_note"]


# ---------------------------------------------------------------------------
# 通道归因（vs R9；重放可复核；链自 r6 衔接）
# ---------------------------------------------------------------------------

def test_run_r10_channel_attribution_replay_reproducible():
    s43 = _s43()
    rec, _ = _run_record()
    run9 = _load("calibration-run-r9.json")
    ca = rec["channel_attribution"]
    # 方法声明：照抄 run-r9 重放口径（同源几何原语）
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r9.json" in ca["method"]["source_of_r9_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] \
        is True
    # 重放复算（R9/R10 均用内嵌输入）与登记一致 + 对拍 compare_v3
    gt = {"prep1": rec["states"]["prep1"]["gt_entries"],
          "applied": rec["states"]["applied"]["gt_entries"]}
    for run_doc, tag in ((run9, "r9"), (rec, "r10")):
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            rp = s43.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    gt[st])
            assert s43.replay_matches_agree(rp, blk["compare_v3"])
            pairs = ca["method"]["replay_cross_check"][
                f"{tag}_{st}_candidate_pairs"]
            assert pairs == [list(p) for p in rp["candidate_pairs"]]
    # R10 prep1 candidate 对恰 1 且=matches（R10T-011↔R4J3）；其余均空
    assert ca["method"]["replay_cross_check"]["r10_prep1_candidate_pairs"] \
        == [["R10T-011", "GT-REVC-P1-R4J3"]]
    assert ca["method"]["replay_cross_check"]["r10_applied_candidate_pairs"] \
        == []
    assert ca["method"]["replay_cross_check"]["r9_prep1_candidate_pairs"] \
        == []
    assert ca["method"]["replay_cross_check"]["r9_applied_candidate_pairs"] \
        == []
    # 通道分组条目（几何门 R9 0→R10 0；类别门 R9 0→R10 0）与重放一致
    def _entries(run_doc, failure):
        rows = []
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            rp = s43.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    gt[st])
            rows += [dict(e, state=st) for e in rp["entries"]
                     if e["failure"] == failure]
        return rows
    for gate, failure in (("channel_1_geometry_gate",
                           "area_ratio_rejected"),
                          ("channel_2_category_gate",
                           "category_mismatch")):
        assert ca[gate][f"r9_{failure}_entries"] == _entries(run9, failure) \
            == []
        assert ca[gate][f"r10_{failure}_entries"] == _entries(rec, failure) \
            == []
    assert "0→0" in ca["channel_1_geometry_gate"]["change"]
    assert "R10T-011" in ca["channel_1_geometry_gate"]["change"]
    assert "0→0" in ca["channel_2_category_gate"]["change"]
    assert "通道级归因，不是旗" in ca["pairing_caveat"]
    assert "不同 reader 实例" in ca["pairing_caveat"]
    # 视角门：两轮重放均空（R10 全部旗标 top、GT 13 条全部 side=top）
    assert ca["view_gate_observations"]["r9_entries"] == []
    assert ca["view_gate_observations"]["r10_entries"] == []
    assert "bottom 两格零旗标" in ca["view_gate_observations"]["note"]
    # 通道链自 r6 衔接（几何 1→0→0→0→0；类别 1→0→1→0→0）；
    # r6/r7/r8 端取值与各轮 run-record 自身登记一致（源头可追溯）
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 0, "r9": 0, "r10": 0}
    assert chain["category_gate_category_mismatch_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 1, "r9": 0, "r10": 0}
    for r in (6, 7, 8):
        doc = _load(f"calibration-run-r{r}.json")
        cha = doc["channel_attribution"]
        assert len(cha["channel_1_geometry_gate"][
            f"r{r}_area_ratio_rejected_entries"]) == \
            chain["geometry_gate_area_ratio_rejected_by_round"][f"r{r}"]
        assert len(cha["channel_2_category_gate"][
            f"r{r}_category_mismatch_entries"]) == \
            chain["category_gate_category_mismatch_by_round"][f"r{r}"]
    assert "通道级归因" in chain["scope"]
    # R10 特有观察：唯一命中、reroute 2 条机制观察、弃权回落、courtyard
    spec = "\n".join(ca["r10_specific_observations"])
    assert "R10T-011" in spec and "0.829864" in spec
    assert "R10T-012" in spec and "示例 c" in spec
    assert "证伪" in spec and "实例群特异" in spec
    assert "0.285714" in spec and "4/14" in spec
    assert "reader_instance_note" in spec and "PIL" in spec
    assert "courtyard" in spec and "R10T-002" in spec
    assert "正常特征→不报告" in spec
    # courtyard 激增/回落声明独立复算：R10 top 非弃权 courtyard=3、
    # R9=2、R8=6
    def _top_nonabstain_courtyard(run_doc):
        out = []
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            abst = set(blk["compare_v3"]["abstain"]["abstain_ids"])
            out += [f["flag_id"] for f in blk["reader_flags"]
                    if f["category"] == "courtyard_crowding"
                    and f["flag_id"] not in abst
                    and blk["flag_views"][f["flag_id"]] == "top"]
        return sorted(out)
    assert _top_nonabstain_courtyard(rec) == ["R10T-009", "R10T-010",
                                              "R10T-011"]
    assert _top_nonabstain_courtyard(run9) == ["R9T-001", "R9T-002"]
    run8 = _load("calibration-run-r8.json")
    assert _top_nonabstain_courtyard(run8) == [
        "R8T-002", "R8T-004", "R8T-006", "R8T-007", "R8T-012", "R8T-013"]
    # R8 基线匹配明细双条件数值独立复算（R8T-004 vs AP-8）
    blk8 = run8["states"]["applied"]
    f004 = next(f for f in blk8["reader_flags"] if f["flag_id"] == "R8T-004")
    g8 = next(e for e in blk8["gt_entries"]
              if e["gt_id"] == "GT-REVC-AP-8-R1Q2")
    assert round(cal._containment(f004["frame_box_pct"],
                                  g8["frame_box_pct"]), 6) == 0.838782
    assert round(cal._area_ratio(f004["frame_box_pct"],
                                 g8["frame_box_pct"]), 6) == 2.688288
    # R10 唯一命中双条件数值独立复算（R10T-011 vs R4J3）
    blk10 = rec["states"]["prep1"]
    f011 = next(f for f in blk10["reader_flags"]
                if f["flag_id"] == "R10T-011")
    g10 = next(e for e in blk10["gt_entries"]
               if e["gt_id"] == "GT-REVC-P1-R4J3")
    assert round(cal._containment(f011["frame_box_pct"],
                                  g10["frame_box_pct"]), 6) == 0.829864
    assert round(cal._area_ratio(f011["frame_box_pct"],
                                 g10["frame_box_pct"]), 6) == 1.770688


# ---------------------------------------------------------------------------
# 预注册链、冻结哈希、阈值零覆盖
# ---------------------------------------------------------------------------

def test_run_r10_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r10_prep_record_preregistration",
            "observation_guidance_r9_zero_byte_reuse",
            "observation_guidance_r8_baseline",
            "r9_dev_record_preregistration_source",
            "r9_prep_record_witness_source",
            "render_framing_r5_preregistration", "gt_reprojection_log_r5",
            "gt_seed_prep1", "gt_expansion_applied",
            "r8_prep_record_witness_chain", "r7_prep_record_witness_chain",
            "source_image_pdf_applied_top_r4",
            "source_image_pdf_applied_bottom_r4",
            "source_image_pdf_prep1_top_r4",
            "source_image_pdf_prep1_bottom_r4",
            "render_png_applied_top_r5_reused",
            "render_png_applied_bottom_r5_reused",
            "render_png_prep1_top_r5_reused",
            "render_png_prep1_bottom_r5_reused"} <= roles
    for key, blk in rec["reader"]["raw_files"].items():
        assert blk["sha256"] == _sha(blk["path_rel"])
        assert blk["sha256"].startswith(RAW_SHA256_FIRST8[key])
        assert os.path.basename(blk["path_rel"]) == RAW_FILES[key]
    # 预注册件哈希锚（先验给定的前 8；含 r9-dev→r10-prep 链与参照轮）
    for rel, want in PREREG_ANCHORS.items():
        assert _sha(rel).startswith(want), rel
    # 阈值常量零覆盖（与 r9 相同；比较器本体零改动）
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "本轮零覆盖" in \
        rec["preregistration"]["comparator"]["thresholds_note"]
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    # 机械命名覆盖入 naming_constraints（per r10-prep-record guidance_reuse）
    assert "R9T/R9B→R10T/R10B" in rec["naming_constraints"]
    assert "reader-r9-*→reader-r10-*" in rec["naming_constraints"]
    assert "判读实质判据零变更" in rec["naming_constraints"]
    # 指引锚：本轮=r9 指引零字节复用（无新指引文件），基线=r8 指引
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r9.md")
    assert gp["sha256"].startswith("a0c10154")
    assert gp["zero_byte_reuse"] is True
    assert gp["frozen_before_render"] is True
    assert gp["frozen_before_read"] is True
    assert gp["baseline_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r8.md")
    assert "零字节复用" in gp["change_note"]
    assert "机械命名覆盖" in gp["change_note"]
    # 指引内容锚：复用的 r9 指引含示例 c/三路出口/非放宽（零字节复用）
    g9 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                           "observation-guidance-r9.md"),
              encoding="utf-8").read()
    assert "示例 c" in g9 and "蛇形" in g9 and "三路出口" in g9
    assert "2026-09-07-r9" in g9 and "非放宽" in g9
    # 预注册链声明（r9-dev-record→r10-prep-record 先于盲读）
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "5ee18d61" in rec["preregistration"]["note"]
    assert "3791edb1" in rec["preregistration"]["note"]
    assert "r10-prep-record.json" in rec["preregistration"]["note"]
    # 参照轮哈希在案（r9=上一轮基线；r10 前 run 不含本轮）
    ref9 = rec["reference_rounds"]["r9_run"]
    assert ref9["sha256"] == _sha(ref9["path_rel"])
    assert ref9["sha256"].startswith("e16420e5")
    ref8 = rec["reference_rounds"]["r8_run"]
    assert ref8["sha256"].startswith("3c580eb3")
    assert "r10_run" not in rec["reference_rounds"]
    # 复用渲染见证：两 bottom 渲染逐字节相同（R5 仪器事实沿用）
    bot_a = open(os.path.join(CAL_DIR, "renders-r5",
                              "applied-bottom.png"), "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r5",
                              "prep1-bottom.png"), "rb").read()
    import hashlib
    assert hashlib.sha256(bot_a).hexdigest() == \
        hashlib.sha256(bot_p).hexdigest() == BOTTOM_PNG_SHA256


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round10_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=零变更重复轮（唯一操纵=实例群更替）与协议降级条款原文引用
    assert "零变更重复轮" in dev["round_nature"]
    assert "实例群更替" in dev["round_nature"]
    assert "三分结构" in dev["round_nature"]
    assert "候选方案 (a)" in dev["round_nature"]
    assert "零字节复用" in dev["round_nature"]
    assert "互不凌驾" in dev["round_nature"]            # 边界与门分开表述
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert dev["instrument_change"]["nature"].startswith("零仪器变更")
    # 诊断结果与 run-r10 一致
    run, _ = _run_record()
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation"]["abstain_rate_total"] == 0.285714
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation"]["gt_recall_total"] == 0.076923
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation"]["seed_match_rate_total"] == 0.1
    assert dev["diagnostic_result"]["seed_metric_note"] == \
        cal.SEED_METRIC_NOTE
    crit = {c["id"]: c for c in dev["diagnostic_result"]["criteria"]}
    assert crit["gt_count_ge_12"]["met"] is True
    assert crit["gt_recall_ge_0.75"]["met"] is False
    assert crit["seed_match_rate_ge_0.5"]["met"] is False
    assert crit["abstain_rate_le_0.5"]["met"] is True   # 重新入线
    # 假设三分裁决节与 run-r10 一致
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "supported"
    # 联合评价趋势：连续达标计数 0（R9 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["after_r9"]["consecutive_met_count"] == 0
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"]
    assert "不得写成已达成" in trend["note"]
    # r5→r10 逐轮走势表（数值取各轮 run-record）
    assert [row["round"] for row in trend["by_round"]] == \
        ["r5", "r6", "r7", "r8", "r9", "r10"]
    by_r = {row["round"]: row for row in trend["by_round"]}
    assert by_r["r8"]["abstain_rate_total"] == 0.222222
    assert by_r["r8"]["matches_total"] == 1
    assert by_r["r9"]["abstain_rate_total"] == 0.727273
    assert by_r["r9"]["matches_total"] == 0
    assert by_r["r10"]["abstain_rate_total"] == 0.285714
    assert by_r["r10"]["matches_total"] == 1
    assert by_r["r5"]["round_id"] == "2026-09-06-r5"
    for row in trend["by_round"]:
        assert row["joint_evaluation"] == "not_met"
        assert row["source"]["sha256"] == _sha(row["source"]["path_rel"])
    # run-r10 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r10.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # gt-audit-r1 引用与 run 一致（1f20554a；GT 侧已全部关闭）
    assert dev["gt_audit_ref"] == run["gt_audit_reference"]
    assert dev["gt_audit_ref"]["sha256"].startswith("1f20554a")
    # 诚实结论：字母裁决获支持（方向性）；三条机制观察如实；联合 not_met
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.285714" in hc and "development 域" in hc
    assert "0.076923（1/13）" in hc and "matches=1" in hc
    assert "获支持" in hc and "方向性" in hc and "非统计证明" in hc
    assert "互不凌驾" in hc and "分列不合并" in hc
    assert "度量不稳定" in hc                            # 三点①
    assert "弃权理由词汇" in hc and "证伪" in hc          # 三点②
    assert "正确测出无效" in hc
    assert "正常特征→不报告" in hc                        # 三点③
    assert "机制观察单列" in hc
    assert "混杂" in hc and "每格 n=1" in hc
    assert "围栏" in hc
    assert "不再有候选" in hc
    assert "in_calibrated_range" in hc
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 4 and fp["non_abstain_count"] == 10
    assert fp["abstain_rate"] == 0.285714
    assert fp["reroute_class_production"] == 2
    assert fp["abstain_rate_by_view"]["top"] == 0.285714
    assert fp["abstain_rate_by_view"]["top_fraction"] == "4/14"
    assert fp["abstain_rate_by_view"]["bottom"] is None
    assert fp["abstain_rate_by_view"]["bottom_fraction"] == "0/0"
    assert fp["parse_rejections"] == []
    assert fp["flag_count_by_file"] == {"applied-top": 2,
                                        "applied-bottom": 0,
                                        "prep1-top": 12, "prep1-bottom": 0}
    assert sum(fp["flag_count_by_file"].values()) == 14
    assert fp["reader_ids"] == READER_IDS
    assert "冻结证据" in fp["note"]
    assert "PIL" in fp["reader_instance_note"]
    assert "围栏" in fp["reader_instance_note"]
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r10 冻结工件一致（含 r9-dev→r10-prep 链）
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles
    assert chain["r9_dev_record_preregistration_source"]["sha256"] == \
        _sha("out/v3-tl2/calibration/round9-dev-record.json")
    assert chain["r10_prep_record_preregistration"]["sha256"].startswith(
        "3791edb1")
    assert "5ee18d61" in dev["preregistration_chain_note"]
    assert "3791edb1" in dev["preregistration_chain_note"]


def test_dev_record_observations_and_next_targets_cite_gt_audit():
    """方向性观察与下一迭代目标：通道数值可独立复算（描述性，不入
    度量）；gt-audit-r1 结论被 next_iteration_targets 引用（GT 侧已
    全部关闭）；不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    run, _ = _run_record()
    obs = "\n".join(dev["directional_observation_vs_r9"])
    # R9 基线匹配数值复算（R9 零匹配）与 R10 唯一命中复算
    run9 = _load("calibration-run-r9.json")
    for st in ("prep1", "applied"):
        assert run9["states"][st]["compare_v3"]["matches"] == []
    blk10 = run["states"]["prep1"]
    f011 = next(f for f in blk10["reader_flags"]
                if f["flag_id"] == "R10T-011")
    g10 = next(e for e in blk10["gt_entries"]
               if e["gt_id"] == "GT-REVC-P1-R4J3")
    assert round(cal._containment(f011["frame_box_pct"],
                                  g10["frame_box_pct"]), 6) == 0.829864
    assert round(cal._area_ratio(f011["frame_box_pct"],
                                 g10["frame_box_pct"]), 6) == 1.770688
    f009 = next(f for f in blk10["reader_flags"]
                if f["flag_id"] == "R10T-009")
    assert all(cal._containment(f009["frame_box_pct"], e["frame_box_pct"])
               is None for e in blk10["gt_entries"])
    # R9→R10 分层/聚合数字在观察中如实引用
    for need in ("11→14", "0.222222", "0.727273", "0.285714", "4/14",
                 "8/11", "0.5（1/2）", "0.25（3/12）", "0.666667", "1.0",
                 "0/0", "0→1", "0.076923", "0.1（1/10）", "0.829864",
                 "1.770688", "R10T-011", "示例 c", "证伪", "实例群特异",
                 "正常特征→不报告", "PIL", "围栏", "缩进", "前置文字",
                 "reader_instance_note", "courtyard", "R10T-002",
                 "r6=1→r7=0"):
        assert need in obs, need
    nxt = "\n".join(dev["next_iteration_targets"])
    # 度量稳定性候选（协议侧，须预注册）：n≥3 多实例重复读/中位数门控
    assert "0.222222" in nxt and "0.727273" in nxt and "0.285714" in nxt
    assert "不稳定" in nxt
    assert "n≥3" in nxt and "中位数门控" in nxt
    assert "预注册" in nxt
    # 示例 c 去留评估候选（r11 指引侧：弃权理由词汇效应 vs 化解目标）
    assert "示例 c" in nxt and "去留" in nxt
    assert "弃权理由词汇" in nxt and "化解" in nxt
    # 渲染侧 bottom 图层清单候选延续
    assert "图层清单" in nxt
    # courtyard 追踪延续
    assert "courtyard" in nxt and "追踪" in nxt
    # GT 侧已全关闭（gt-audit-r1 三候选关闭结论被引用）
    assert "gt-audit-r1" in nxt and "1f20554a" in nxt
    assert "三候选" in nxt and "全部关闭" in nxt
    # 不得把正式采纳门槛达成写成已达成；in_calibrated_range 恒 False
    assert "in_calibrated_range 恒 False" in nxt
    assert "不得" in nxt and "TBD" in nxt
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r10-prep-record.json")


def test_s43_rerun_byte_identical_and_overwrite_guard():
    """s43 重跑语义：同参重建 byte-exact 一致；防覆写护栏（字节等同→
    幂等跳过零覆写；不同→fail-closed）。"""
    s43 = _s43()
    rec, disk = _run_record()
    dev, dev_disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    run_rebuilt = s43.build_run()
    assert hashing.canonical_json_bytes(run_rebuilt) == disk
    run_sha = _sha("out/v3-tl2/calibration/calibration-run-r10.json")
    dev_rebuilt = s43.build_dev_record(run_rebuilt, run_sha)
    assert hashing.canonical_json_bytes(dev_rebuilt) == dev_disk
    # 声明常量（无 wall-clock）
    assert s43.DECLARED_DATE == "2026-09-07"
    assert s43.ROUND_ID == "2026-09-07-r10"
    # 防覆写护栏纯函数语义
    assert s43.overwrite_guard(None, b"x") == "write"
    assert s43.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s43.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：目标两件已存在且字节等同 → main 正常完成（零覆写）
    before = open(os.path.join(CAL_DIR, "calibration-run-r10.json"),
                  "rb").read()
    s43.main()                                          # 不抛异常=幂等路径
    after = open(os.path.join(CAL_DIR, "calibration-run-r10.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    dev_after = open(os.path.join(CAL_DIR, "round10-dev-record.json"),
                     "rb").read()
    assert dev_after == dev_disk                 # 字节零改动
    # run_record_ref 仍指向 run-r10 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r10.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "三路出口" in rp["abstain_semantics"]
    assert "示例 c" in rp["abstain_semantics"]
    assert "无任何 GT" in rp["discipline"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r10-prep-record.json" in rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "2026-09-07-r10" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域零变更重复轮，非留出；
    # advisory 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "零变更重复轮" in dev["round_nature"]
    assert dev["is_gate"] is False
    assert rec["compliance"]["critic_calibration_in_range"] is False
    assert "不是门" in dev["notes"][0]
    # 机械命名覆盖（guidance_reuse）如实入账：前缀与 reader_id 两处
    assert "R9T/R9B→R10T/R10B" in rec["naming_constraints"]
    assert "reader-r9-*→reader-r10-*" in rec["naming_constraints"]
    prep = _load("r10-prep-record.json")
    assert prep["guidance_reuse"]["mechanical_naming_override"] in \
        rec["naming_constraints"] or ("机械替换" in rec["naming_constraints"]
                                      and "判读实质判据零变更" in
                                      rec["naming_constraints"])
    # 三分裁决纪律声明在案（字母裁决不被机制观察改写；获支持≠假设被
    # 证实；0.5 裁决边界与 APR-0011 门分开表述）
    assert "不得凌驾或改写字母裁决" in dev["notes"][-1]
    assert "supported 维持不变" in dev["notes"][-1]
    assert "分开表述" in dev["notes"][-1]


def _assert_no_banned_keys(obj, path="doc"):
    if isinstance(obj, dict):
        for banned in ("reader_false_positive_ids",
                       "reader_precision_vs_seed_gt"):
            assert banned not in obj, (path, banned)
        for k, v in obj.items():
            _assert_no_banned_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _assert_no_banned_keys(v, f"{path}[{i}]")
