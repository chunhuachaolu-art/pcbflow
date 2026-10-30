"""R13 执行包测试：reader 判读迭代第十三轮收口（CAL-R13-CLOSE）——
盲读解析与视角注入（12 派次=4 视角格×3 实例，v1.2 规约沿用第二轮）+
六实例主记录（measurement_design item 1：两板合计
flag_count/abstain_count/abstain_rate/非弃权清单/逐旗明细）+ 视角层
三分列（item 2：中位数+min+max 不取整；本轮无零旗标实例、弃权率全部
有定义）+ GT 匹配双口径（item 3：union/agreement 并列+逐 GT
matched_by_count）+ 联合门代表配置与 per-metric 实例间范围并列
（item 4）+ 预注册假设（r12-dev-record-candidate-0-s4i-operationalize）
裁决（bottom courtyard 非弃权极差 0/0/0=0≤5 且聚合 0≤5+top 守门
0→0 无回升⇒字母=supported+机制观察单列：主通道收敛/接触性判据首验/
黑点类收敛/残余实例差异）+ 逐旗失败通道归因（vs R12，链自 r6）+
courtyard 被动追踪 + development 域记录。

结构照 test_r12_calibration_round12.py 先例，仅输入与轮次常量不同
（R13=单变量指引侧变更轮：§4 存在性判断一般判据 (i)(ii) 整段替换为
量化版 (i)(ii)(iii)+接触性判据；observation-guidance-r13.md=c28806e1
由 r12 指引 0ac22fcd 机械变换生成、落盘即冻结；R5 冻结渲染复用；GT/
阈值零变更；协议侧零新增条款（v1.2 沿用）；pre_round_review=用户授权
的 D1–D3 视觉诊断评审（编排侧证据、零 reader 上下文）；预注册于
r13-prep-record.json（b1c0d8b5），链=round12-dev-record（1411dab6）→
diag-r13-review D1–D3（2387daed/b79bc617/c09154a4）→r13-prep-record；
判据=bottom courtyard 非弃权极差（≤5/≥10 描述性边界、与门分列）；
APR-0011 门与主通道判据各自独立、互不凌驾）。

覆盖：
- 盲读原文（reader-raw-r13-*.txt 十二件，冻结证据）：合法 JSON、结构
  （reader_id/per_image/reading_notes；flag 六键含 location_evidence）、
  实例内跨板连续编号（R13T/R13B）与实例间独立编号、实例旗数
  10/7/7/3/4/4 与弃权 7/6/2/3/4/3、reroute 恰 2 条（R13T-009 弃权
  top-i1+R13T-001 非弃权 top-i2）、拒收清单固化（35 旗全过
  calibration fail-closed 校验，0 拒收）、哈希与 run-r13 登记一致；
- 视角注入确定性+派发模式（12 派次两波次串行保序）+读者实例披露
  （12/12 派次自述纯 Read 直读=v1.2 沿用合规；输出格式披露：12 件均
  indent=1 重序列化；无围栏剥离；本轮无零旗标格）；
- calibration-run-r13.json：盘上 canonical byte 一致；逐实例逐态
  compare_v3 用内嵌输入重算 byte-exact 一致（本轮 12 格全部有旗、
  view_check 全 full）；内嵌 gt_entries=源 GT 文件条目+
  derivation-log-r5 重投影零新派生；零 matches 复算；六实例聚合复算
  （abstain_rate 0.7/0.857143/0.285714/1.0/1.0/0.75）；视角层三分列
  复算（top 极差 0.571429/bottom 极差 0.25）；双口径复算（union 0/13=
  0.0、agreement 0/13=0.0、matched_by_count 全部 0；bottom 无 GT 在案
  gt-audit-r1）；代表配置（top-i2+bottom-i2：双 tie 均按先序取 i2 并
  注明）joint 复算（11 旗 10 弃权=0.909091、0/13、0/1；APR-0011 联合
  not_met，三项未达线）+per-metric 范围；
- 预注册假设裁决：判据引用=r13-prep-record hypothesis_test 原文
  （support=极差≤5 且聚合≤5 且 top 几何门无回升/reject=极差>5 或
  聚合≥10 原样）；实测 bottom courtyard 非弃权=0/0/0（极差 0、聚合 0、
  r12 基线 18/0/0 交叉核对）且 guard_ok（几何门 R12=0→R13=0）
  ⇒verdict=supported（字母裁决）；≤5/≥10 描述性边界与门分列；
  机制观察单列（主通道收敛 6 派次量化判据摘录校验；接触性判据首验
  8/8 旗逐旗摘录校验；黑点类 8/8 弃权；右下孤立对三种处置=残余差异）；
  reroute 类被动追踪（R13T-009 子串命中=等长、R13T-001 零命中）；
- 通道归因（vs R12）：重放对拍 R11/R12 十二件（复算=在案登记）与
  R13 十二件全部复现（候选对=空集）；几何门 0→0（无回升）、类别门
  0→0、视角门 0→0；链自 r6（几何 1→0→0→0→0→0→0→0；类别
  1→0→1→0→0→1→0→0）；courtyard 追踪：非弃权 0 条、弃权 8 条（全部
  top）、命中 r8=1→r9=0→r10=1→r11=3→r12=0→r13=0；
- 预注册链：round12-dev-record（1411dab6）→diag-r13-review D1–D3→
  r13-prep-record（b1c0d8b5）→run-r13 链含哈希；guidance-r13
  （c28806e1）/guidance-r12 基线（0ac22fcd）/r9、r8 指引链/framing-r5/
  derivation-log-r5/GT/协议 v1 零字节保留（22dc7337）/复用 PNG/冻结
  PDF sha 与盘上一致；阈值常量零覆盖（containment 0.5/area_ratio_max
  10.0 与 r12 相同）；gt-audit-r1 引用（1f20554a）；
- round13-dev-record.json：域声明、本轮性质（指引侧可操作化+pre_round_
  review 评审前置+user_directive 拍板）、假设裁决节与 run-r13 一致、
  R12→R13 方向性观察（派次 12→12、旗标 44→35、bottom courtyard 非弃
  权 18/0/0→0/0/0、top 弃权率带变化、连续第二轮零匹配）、联合评价趋势
  （r5→r13 逐轮表、连续计数 0→0；r11–r13 行=代表配置口径并列注明）、
  run-r13 sha 引用一致、next_iteration_targets 覆盖 top 接触性弃权
  高企的渲染侧消歧候选/§4(iii) 分辨率适配候选（不得反向放宽）/示例 c
  保留观察/courtyard 追踪延续/GT 侧已全关闭延续/留出集运行时机=开发线
  收敛判断（须用户；HOLDOUT-PLAN.md a4b80193）、is_gate=False、
  in_calibrated_range 恒 False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；命名覆盖 R12T/R12B→R13T/R13B 随指引落盘
  固化入 naming_constraints；受保护三文件 sha256 前 8 断言+两指引
  （r12/r13）零字节不动；
- s49 重跑：同参重建 byte-exact 一致 + 防覆写护栏语义（字节等同→
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

ROUND_ID = "2026-09-08-r13"
DECLARED_DATE = "2026-09-08"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")
RAW_FILES = {
    "applied-top-i1": "reader-raw-r13-applied-top-i1.txt",
    "prep1-top-i1": "reader-raw-r13-prep1-top-i1.txt",
    "applied-top-i2": "reader-raw-r13-applied-top-i2.txt",
    "prep1-top-i2": "reader-raw-r13-prep1-top-i2.txt",
    "applied-top-i3": "reader-raw-r13-applied-top-i3.txt",
    "prep1-top-i3": "reader-raw-r13-prep1-top-i3.txt",
    "applied-bottom-i1": "reader-raw-r13-applied-bottom-i1.txt",
    "prep1-bottom-i1": "reader-raw-r13-prep1-bottom-i1.txt",
    "applied-bottom-i2": "reader-raw-r13-applied-bottom-i2.txt",
    "prep1-bottom-i2": "reader-raw-r13-prep1-bottom-i2.txt",
    "applied-bottom-i3": "reader-raw-r13-applied-bottom-i3.txt",
    "prep1-bottom-i3": "reader-raw-r13-prep1-bottom-i3.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top-i1": "0add34f2", "prep1-top-i1": "555ad06e",
    "applied-top-i2": "c82f8bd7", "prep1-top-i2": "a47cbce6",
    "applied-top-i3": "694b1c32", "prep1-top-i3": "9fd0fe8a",
    "applied-bottom-i1": "93683abb", "prep1-bottom-i1": "10414b74",
    "applied-bottom-i2": "8f0f0b67", "prep1-bottom-i2": "eb84e4cb",
    "applied-bottom-i3": "54aaa4b7", "prep1-bottom-i3": "e614558e",
}
READER_IDS = {
    "applied-top-i1": "reader-r13-top-i1",
    "prep1-top-i1": "reader-r13-top-i1",
    "applied-top-i2": "reader-r13-top-i2",
    "prep1-top-i2": "reader-r13-top-i2",
    "applied-top-i3": "reader-r13-top-i3",
    "prep1-top-i3": "reader-r13-top-i3",
    "applied-bottom-i1": "reader-r13-bottom-i1",
    "prep1-bottom-i1": "reader-r13-bottom-i1",
    "applied-bottom-i2": "reader-r13-bottom-i2",
    "prep1-bottom-i2": "reader-r13-bottom-i2",
    "applied-bottom-i3": "reader-r13-bottom-i3",
    "prep1-bottom-i3": "reader-r13-bottom-i3",
}
VIEW_OF_KEY = {
    "applied-top-i1": "top", "prep1-top-i1": "top",
    "applied-top-i2": "top", "prep1-top-i2": "top",
    "applied-top-i3": "top", "prep1-top-i3": "top",
    "applied-bottom-i1": "bottom", "prep1-bottom-i1": "bottom",
    "applied-bottom-i2": "bottom", "prep1-bottom-i2": "bottom",
    "applied-bottom-i3": "bottom", "prep1-bottom-i3": "bottom",
}
STATE_OF_KEY = {
    "applied-top-i1": "applied", "prep1-top-i1": "prep1",
    "applied-top-i2": "applied", "prep1-top-i2": "prep1",
    "applied-top-i3": "applied", "prep1-top-i3": "prep1",
    "applied-bottom-i1": "applied", "prep1-bottom-i1": "prep1",
    "applied-bottom-i2": "applied", "prep1-bottom-i2": "prep1",
    "applied-bottom-i3": "applied", "prep1-bottom-i3": "prep1",
}
READER_FLAG_KEYS = {"flag_id", "category", "confidence", "abstain",
                    "frame_box_pct", "location_evidence"}
#: 逐实例旗数/弃权数（盘面实测口径；与 run-r13 聚合一致）
EXPECT_COUNTS = {"top-i1": 10, "top-i2": 7, "top-i3": 7,
                 "bottom-i1": 3, "bottom-i2": 4, "bottom-i3": 4}
EXPECT_ABSTAIN = {"top-i1": 7, "top-i2": 6, "top-i3": 2,
                  "bottom-i1": 3, "bottom-i2": 4, "bottom-i3": 3}
EXPECT_PART_COUNTS = {
    "applied-top-i1": 4, "prep1-top-i1": 6,
    "applied-top-i2": 4, "prep1-top-i2": 3,
    "applied-top-i3": 2, "prep1-top-i3": 5,
    "applied-bottom-i1": 1, "prep1-bottom-i1": 2,
    "applied-bottom-i2": 2, "prep1-bottom-i2": 2,
    "applied-bottom-i3": 2, "prep1-bottom-i3": 2,
}
#: 本轮无零旗标格（12 格全部≥1 旗；r12 三格零旗标后本轮无）
ZERO_FLAG_PARTS = []
#: 原始件键 → 实例键（"{state}-{view}-i{n}" → "{view}-i{n}"）
INSTANCE_OF_KEY = {k: k.split("-", 1)[1] for k in RAW_FILES}
GT_V1_IDS = ["GT-REVC-P1-R4J3", "GT-REVC-P1-F1J2", "GT-REVC-P1-L1NB",
             "GT-REVC-P1-L1SHORT"]
GT_V2_IDS = [
    "GT-REVC-AP-1-R5U6", "GT-REVC-AP-2-Y1C35", "GT-REVC-AP-3-Y1C5",
    "GT-REVC-AP-4-Y1C36", "GT-REVC-AP-5-Y1C4", "GT-REVC-AP-6-R2LED2",
    "GT-REVC-AP-7-C31U4", "GT-REVC-AP-8-R1Q2", "GT-REVC-AP-9-Y2C3",
]
#: R13 reroute 恰 2 条（R13T-009 弃权 top-i1+R13T-001 非弃权 top-i2；
#: 按 RAW_FILES 迭代序）
EXPECT_R13_REROUTE = [("top-i1", "R13T-009", True),
                      ("top-i2", "R13T-001", False)]
#: 受保护文件（R13-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: 两指引零字节不动（红线：r12 基线与 r13 指引收工哈希=开工哈希）
GUIDANCE_SHA256_FIRST8 = {
    "out/v3-tl2/calibration/observation-guidance-r12.md": "0ac22fcd",
    "out/v3-tl2/calibration/observation-guidance-r13.md": "c28806e1",
}
#: 预注册件哈希锚（先验给定的前 8）
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r13.md": "c28806e1",
    "out/v3-tl2/calibration/observation-guidance-r12.md": "0ac22fcd",
    "out/v3-tl2/calibration/observation-guidance-r9.md": "a0c10154",
    "out/v3-tl2/calibration/observation-guidance-r8.md": "aad43270",
    "out/v3-tl2/calibration/r13-prep-record.json": "b1c0d8b5",
    "out/v3-tl2/calibration/round12-dev-record.json": "1411dab6",
    "out/v3-tl2/calibration/r12-prep-record.json": "d393cf27",
    "out/v3-tl2/calibration/round11-dev-record.json": "66e41bbf",
    "out/v3-tl2/calibration/r11-prep-record.json": "9074df2d",
    "out/v3-tl2/calibration/round10-dev-record.json": "da4e85f9",
    "out/v3-tl2/calibration/r10-prep-record.json": "3791edb1",
    "out/v3-tl2/calibration/round9-dev-record.json": "5ee18d61",
    "out/v3-tl2/calibration/r9-prep-record.json": "dd979632",
    "out/v3-tl2/calibration/round8-dev-record.json": "437e149c",
    "out/v3-tl2/calibration/r8-prep-record.json": "237920a5",
    "out/v3-tl2/calibration/r7-prep-record.json": "e48c37fe",
    "out/v3-tl2/calibration/diag-r13-review/D1.md": "2387daed",
    "out/v3-tl2/calibration/diag-r13-review/D2.md": "b79bc617",
    "out/v3-tl2/calibration/diag-r13-review/D3.md": "c09154a4",
    "out/v3-tl2/calibration/render-framing-r5.json": "860aa910",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
    "out/v3-tl2/calibration/calibration-run-r12.json": "2ec2fb04",
    "out/v3-tl2/calibration/calibration-run-r11.json": "ec05e472",
    "out/v3-tl2/calibration/calibration-run-r10.json": "622c9099",
    "out/v3-tl2/calibration/calibration-run-r9.json": "e16420e5",
    "out/v3-tl2/calibration/calibration-run-r8.json": "3c580eb3",
    "out/v3-tl2/holdout/HOLDOUT-PLAN.md": "a4b80193",
}
BOTTOM_PNG_SHA256 = (
    "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9")
#: 六实例弃权率（盘面实测口径；本轮无零旗标实例、全部有定义）
EXPECT_RATES = {"top-i1": 0.7, "top-i2": 0.857143, "top-i3": 0.285714,
                "bottom-i1": 1.0, "bottom-i2": 1.0, "bottom-i3": 0.75}
#: 主通道预注册描述性边界（与门分列；非门阈值）
DESCRIPTIVE_BOUNDARIES = {"support_max_range": 5,
                          "reject_min_aggregate": 10}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s49():
    spec = importlib.util.spec_from_file_location(
        "s49_calibration_r13_compare",
        os.path.join(REPO, "scripts", "s49_calibration_r13_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r13.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round13-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _raw_text(key):
    return open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                             RAW_FILES[key]), encoding="utf-8").read()


def _raw_loc(key, flag_id):
    d = _load(RAW_FILES[key])
    for img in d["per_image"]:
        for f in img["flags"]:
            if f["flag_id"] == flag_id:
                return f["location_evidence"]
    raise AssertionError((key, flag_id))


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r13_files_valid_structure_and_prefixes():
    seen_ids = {n: [] for n in INSTANCE_ORDER}
    for key, name in RAW_FILES.items():
        assert _sha("out/v3-tl2/calibration/" + name).startswith(
            RAW_SHA256_FIRST8[key])                  # 与派发哈希锚一致
        d = _load(name)
        assert d["reader_id"] == READER_IDS[key]
        assert set(d) == {"reader_id", "per_image", "reading_notes"}
        assert len(d["per_image"]) == 1                 # 每文件恰一图
        img = d["per_image"][0]
        # 图名=派发图像名（同格三实例共用同一 PNG；实例差异仅在 reader_id）
        assert img["image"] == "%s.png" % key.rsplit("-", 1)[0]
        assert len(img["flags"]) == EXPECT_PART_COUNTS[key]
        view = VIEW_OF_KEY[key]
        prefix = {"top": "R13T-", "bottom": "R13B-"}[view]
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
            seen_ids[INSTANCE_OF_KEY[key]].append(f["flag_id"])
        assert d["reading_notes"].strip()
    # 实例内跨板连续编号（同实例先 applied 后 prep1）+ 实例间独立
    expect_ids = {
        "top-i1": ["R13T-%03d" % i for i in range(1, 11)],
        "top-i2": ["R13T-%03d" % i for i in range(1, 8)],
        "top-i3": ["R13T-%03d" % i for i in range(1, 8)],
        "bottom-i1": ["R13B-%03d" % i for i in range(1, 4)],
        "bottom-i2": ["R13B-%03d" % i for i in range(1, 5)],
        "bottom-i3": ["R13B-%03d" % i for i in range(1, 5)],
    }
    for inst in INSTANCE_ORDER:
        got = seen_ids[inst]
        assert got == expect_ids[inst], inst
        assert len(got) == EXPECT_COUNTS[inst]
    # reroute 类旗标恰 2 条（R13T-009 弃权 top-i1 存在性不可判定 +
    # R13T-001 非弃权边界报告 top-i2——r12 通道被动追踪载体）
    reroute = [(INSTANCE_OF_KEY[key], f["flag_id"], f["abstain"])
               for key, name in RAW_FILES.items()
               for f in _load(name)["per_image"][0]["flags"]
               if f["category"] == "suspicious_reroute"]
    assert reroute == EXPECT_R13_REROUTE
    # 合计 35 旗=10 非弃权+25 弃权（盘面口径与聚合一致）
    total = sum(EXPECT_COUNTS.values())
    abstain = sum(EXPECT_ABSTAIN.values())
    assert total == 35 and abstain == 25 and total - abstain == 10
    # 本轮无零旗标格（12 格全部≥1 旗）
    assert all(v >= 1 for v in EXPECT_PART_COUNTS.values())
    assert ZERO_FLAG_PARTS == []


def test_parse_replay_no_rejections_view_injection_and_reader_instance_note():
    s49 = _s49()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s49.RAW_FILES.items():
        parsed = s49.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s49.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则（作用于派发图像名，非盘上件键）
    assert s49.view_for_image("applied-top.png") == "top"
    assert s49.view_for_image("prep1-bottom.png") == "bottom"
    assert s49.view_for_image("applied-top.png") == s49.view_for_image(
        "applied-top.png")
    try:
        s49.view_for_image("mystery.png")
    except ValueError:
        pass
    else:
        raise AssertionError("无视角后缀图像名应 ValueError（fail-closed）")
    run, _ = _run_record()
    for key in RAW_FILES:
        want = {img["image"]: img["view"] for img in replay[key]["images"]}
        got = run["reader"]["view_injection"]["mapping"][key]
        assert got == want == {("%s.png" % key.rsplit("-", 1)[0]):
                               VIEW_OF_KEY[key]}
        replay_ids = [f["flag_id"] for img in replay[key]["images"]
                      for f in img["flags"]]
        inst = INSTANCE_OF_KEY[key]
        block = run["instances"][inst]["states"][STATE_OF_KEY[key]]
        for fid in replay_ids:
            assert block["flag_views"][fid] == VIEW_OF_KEY[key]
            assert fid in [f["flag_id"] for f in block["reader_flags"]]
    assert run["parse_rejections"] == []                # 拒收清单固化（空）
    # 旗标计数（按实例/板/视角/类别分层；总 35）
    fc = run["reader"]["flag_count"]
    assert fc["by_instance"] == EXPECT_COUNTS
    assert fc["abstain_by_instance"] == EXPECT_ABSTAIN
    assert fc["by_state"] == {"applied": 15, "prep1": 20}
    assert fc["by_view"] == {"top": 24, "bottom": 11}
    assert fc["abstain_by_view"] == {"top": 15, "bottom": 10}
    assert fc["by_category"] == {
        "silk_readability": {"total": 11, "non_abstain": 7, "abstain": 4},
        "courtyard_crowding": {"total": 8, "non_abstain": 0, "abstain": 8},
        "other_advisory": {"total": 11, "non_abstain": 1, "abstain": 10},
        "suspicious_reroute": {"total": 2, "non_abstain": 1, "abstain": 1},
        "placement_pattern_anomaly": {"total": 3, "non_abstain": 1,
                                      "abstain": 2},
    }
    assert fc["reroute_by_instance"] == {"top-i1": 1, "top-i2": 1,
                                         "top-i3": 0, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fc["reroute_class_production"] == 2
    assert fc["total"] == 35
    # 派发模式（12 派次=4 格×3 实例，两波次串行保序；v1.2 沿用条款）
    dm = run["reader"]["dispatch_mode"]
    assert dm["mode"] == "instance_serial_two_wave"
    assert dm["instances_per_cell"] == 3 and dm["dispatch_count_total"] == 12
    assert "同一实例先 applied 后 prep1" in dm["within_instance_serial_order"]
    assert "R13B-001..003" in dm["flag_id_continuity"]["bottom-i1"]
    assert "可操作化" in dm["diff_note"] and "v1.2" in dm["diff_note"]
    assert "12 次盲读" in run["reader"]["dispatch_discipline"]
    assert "禁止交流" in run["reader"]["dispatch_discipline"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r13.md" in \
        run["reader"]["dispatch_discipline"]
    assert "禁止对图像做任何程序化处理" in \
        run["reader"]["dispatch_discipline"]            # v1.2 沿用条款
    assert "零诊断报告内容" in run["reader"]["dispatch_discipline"]
    # 读者实例披露（R13：12/12 纯直读 v1.2 沿用合规+输出格式披露）
    note = run["reader"]["reader_instance_note"]
    assert "12/12 派次自述合规" in note and "Read 工具" in note
    assert "沿用第二轮" in note
    assert "非盲读违规" in note and "混杂因素照旧声明" in note
    assert "json.dump indent=1" in note and "内容逐键忠实" in note
    assert "无围栏剥离" in note
    # 逐文件格式披露登记（编排侧落盘前处理；盘上件=冻结证据；12 件均
    # indent=1 重序列化）
    fm = run["reader"]["parse"]
    for key in RAW_FILES:
        assert "indent=1" in fm[key]["raw_message_format_note"], key
    # 零旗标格（本轮无；item 5 口径保留备用）
    zp = run["reader"]["zero_flag_parts"]
    assert zp["parts"] == []
    assert "无零旗标格" in zp["note"] and "None" in zp["note"] \
        and "不编造数值" in zp["note"]


# ---------------------------------------------------------------------------
# run-r13：canonical、常量、域声明、单变更轮、受保护文件、courtyard
# ---------------------------------------------------------------------------

def test_run_r13_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r13"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r13"
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
    assert rec["compliance_representative"][
        "critic_calibration_in_range"] is False
    # 单变更声明（指引侧单变量=§4 可操作化；协议侧零新增=v1.2 沿用）
    ic = rec["instrument_change"]
    assert ic["nature"].startswith("单变量指引侧变更轮")
    assert "可操作化" in ic["nature"] and "接触性判据" in ic["nature"]
    assert "pre_round_review" in ic["nature"] and "读者不可见" in \
        ic["nature"]
    assert ic["components"][0].startswith(
        "s4-existence-criteria-operationalize-i-ii-iii")
    # changed_variables 登记与 r13-prep-record.json 一致（恰一项，锚
    # b1c0d8b5；no_instrument_change=true 指渲染/仪器零变更）
    prep = _load("r13-prep-record.json")
    assert prep["no_instrument_change"] is True
    assert prep["read_prohibition_compliance"] is True
    assert prep["no_visual_reading"] is True
    assert [v["id"] for v in prep["changed_variables"]] == [
        "s4-existence-criteria-operationalize-i-ii-iii"]
    assert [v["id"] for v in ic["changed_variables_registered"]] == \
        [v["id"] for v in prep["changed_variables"]]
    # unchanged 与 r13-prep-record.json 登记逐字一致
    assert ic["unchanged_components"] == prep["unchanged_components"]
    pa = ic["protocol_amendment"]
    assert pa["amendment_version"].startswith("v1.2")
    assert "沿用" in pa["amendment_version"]
    assert "零变更" in ic["protocol_amendment"]["note"] or "零新增" in \
        ic["protocol_amendment"]["note"]
    v1p = prep["protocol_amendment"]["v1_file_preserved"]
    assert v1p["zero_byte_preserved"] is True
    assert _sha(v1p["path_rel"]) == v1p["sha256_measured"]
    assert "指引侧处置" in ic["attribution_note"] or "恰一项" in \
        ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r13-prep-record.json")
    assert rec["protocol"]["amendment_version"].startswith("v1.2")
    # 指引=新文件（c28806e1）由 r12 指引（0ac22fcd）机械变换生成
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r13.md")
    assert gp["baseline_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r12.md")
    assert "机械变换生成" in gp["change_note"]
    assert "整段替换" in gp["change_note"]
    assert "落盘即冻结" in gp["change_note"]
    # 复用 R5 渲染：零重渲染声明与四 PNG 见证（盘上 sha=prep-record 实测）
    assert prep["renders_reuse"]["no_instrument_change"] is True
    for w in prep["renders_reuse"]["png_witness"]:
        assert w["match_to_witness_constant"] is True
        assert _sha(w["path_rel"]) == w["sha256_measured"]
    # 同日只读 GT 审计引用（1f20554a；结论=GT 侧已全部关闭，本轮延续）
    ref = rec["gt_audit_reference"]
    assert ref["sha256"] == _sha("out/v3-tl2/calibration/gt-audit-r1.json")
    assert ref["sha256"].startswith("1f20554a")
    assert "bottom GT=无源已关闭" in ref["note"]
    assert "reroute GT=无源已关闭" in ref["note"]
    assert "L1NB 框径=合理维持现框" in ref["note"]
    assert "已全部关闭" in ref["note"]                  # GT 侧候选关闭声明
    assert "应为空" in ref["note"]                      # bottom 零匹配结构性
    # 受保护三文件零改动（sha256 前 8）+ 两指引零字节不动
    for rel, want in PROTECTED_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])
    for rel, want in GUIDANCE_SHA256_FIRST8.items():
        got = _sha(rel)
        assert got.startswith(want), (rel, got[:8])
    # 三者并列声明（measurement_design item 4：不合并、不挑优）
    prn = rec["parallel_record_note"]
    assert "三者并列" in prn and "不挑优" in prn
    assert "aggregation_representative" in prn
    assert "metric_ranges_instance" in prn and "instances" in prn
    # measurement_design 五条预注册在 prep-record（先于盲读冻结）
    md = prep["measurement_design"]
    assert [it["item"] for it in md["items"]] == [1, 2, 3, 4, 5]
    assert "先于 R13 盲读冻结" in md["preregistration_declaration"]
    # pre_round_review 键（本轮新增；D1–D3 诊断评审零 reader 上下文）
    prr = prep["pre_round_review"]
    assert prr["execution"].startswith("3 名独立诊断审查员")
    for rp_ in prr["reports"]:
        assert rp_["match"] is True
        assert _sha(rp_["path_rel"]) == rp_["sha256_measured"]
    assert "不进任何 reader 上下文" in prr["declaration"] or \
        "不属盲读链" in prr["declaration"]
    # courtyard 被动追踪键（prep-record 预注册；零阈值改动、零期望）
    ct = rec["courtyard_tracking"]
    assert ct["note_source"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r13-prep-record.json")
    assert ct["note_source"]["quote"] == prep["hypothesis_test"][
        "secondary_observation"]
    assert "零期望" in ct["declaration"] and "零阈值" in ct["declaration"]
    assert "零改动" in ct["threshold_note"]
    # bottom 观察（量化判据一致使用+零匹配结构性+本轮无零旗标格）
    bz2 = ct["bottom_observation"]
    assert "11 旗" in bz2["fact"] and "应为空" in bz2["fact"]
    assert "系统性" in bz2["fact"] and "无零旗标" in bz2["fact"]
    for ev in bz2["evidence"]:
        raw = _load(RAW_FILES[ev["source"]])["reading_notes"]
        assert ev["excerpt"] in raw                     # 逐字摘录校验
    assert "substring" in bz2["evidence_check"]


def test_run_r13_compare_v3_recompute_byte_exact():
    rec, _ = _run_record()
    for inst in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            block = rec["instances"][inst]["states"][st]
            rep = cal.compare_v3(block["reader_flags"], block["gt_entries"],
                                 flag_views=block["flag_views"])
            assert hashing.canonical_json_bytes(rep) == \
                hashing.canonical_json_bytes(block["compare_v3"])
            n_flags = len(block["reader_flags"])
            assert n_flags >= 1                          # 本轮无零旗标格
            assert block["view_check"] == rep["view_check"] == "full"
            r = block["compare_v3"]
            # 阈值常量零覆盖（与 r12 相同的声明常量）
            assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
            assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
            assert r["metric_version"] == "calibration-metric-v3"
            assert r["matches"] == []                    # R13 零匹配
            assert r["duplicate_reports"] == []
    # R13 零匹配（全部实例/全部态）：逐实例 matches_detail 复算为空
    for inst in INSTANCE_ORDER:
        assert rec["instances"][inst]["combined"]["matches_total"] == 0
        assert rec["instances"][inst]["combined"]["matches_detail"] == []
        assert rec["instances"][inst]["combined"]["gt_matched_union"] == 0
    # 全部实例/态 view_mismatch=0（top 旗与同态 GT 视角相符；bottom 非弃权
    # 旗与 GT 零 ≥0.5 containment 交叠；弃权旗不参与视角检查）
    for inst in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            r = rec["instances"][inst]["states"][st]["compare_v3"]
            assert r["view_mismatch"] == []
    # R13B-001（bottom-i3 非弃权 placement）与同态 GT 零交集（未及近邻门；
    # bottom 无 GT 在案 gt-audit-r1）；R13T-004 为弃权旗（单列）
    d1 = next(x for x in rec["instances"]["bottom-i3"][
        "per_flag_gt_detail"] if x["flag_id"] == "R13B-001")
    assert d1["abstain"] is False
    assert d1["containment_all_none"] is True
    assert d1["matched"] is False
    d2 = next(x for x in rec["instances"]["top-i1"]["per_flag_gt_detail"]
              if x["flag_id"] == "R13T-004")
    assert d2["abstain"] is True and d2["gt_overlaps"] == [] \
        and d2["containment_all_none"] is None
    # top 非弃权旗 9 条全部 containment_all_none（与同态 GT 零交集）
    n_top_non_abstain = sum(
        1 for n in ("top-i1", "top-i2", "top-i3")
        for d in rec["instances"][n]["per_flag_gt_detail"]
        if not d["abstain"])
    assert n_top_non_abstain == 9
    assert all(d["containment_all_none"]
               for n in ("top-i1", "top-i2", "top-i3")
               for d in rec["instances"][n]["per_flag_gt_detail"]
               if not d["abstain"])
    # bottom-i2 实例层：本轮有旗标（4 旗 4 弃权→rate=1.0，非 None）
    assert rec["instances"]["bottom-i2"]["combined"]["abstain_rate"] == 1.0
    assert "4/4" in rec["instances"]["bottom-i2"]["combined"][
        "abstain_rate_arithmetic"]


def test_run_r13_gt_entries_source_plus_reprojection():
    rec, _ = _run_record()
    sources = {"prep1": ("ground-truth-v1.json", GT_V1_IDS),
               "applied": ("ground-truth-v2.json", GT_V2_IDS)}
    for st, (gt_name, ids) in sources.items():
        gt = _load(gt_name)
        by_id = {e["gt_id"]: e for e in gt["gt_entries"]}
        block = rec["instances"]["top-i1"]["states"][st]
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
        assert "零新派生" in rec["instances"]["top-i1"]["states"][st][
            "gt_reprojection"]["note"]
        for e in rec["instances"]["top-i1"]["states"][st]["gt_entries"]:
            assert e["frame_box_pct"] == deriv[e["gt_id"]]
            assert 0.0 <= e["frame_box_pct"][0] < e["frame_box_pct"][2] <= 1.0
            assert 0.0 <= e["frame_box_pct"][1] < e["frame_box_pct"][3] <= 1.0
            assert e["side"] == "top"                   # 13 条全部 top


# ---------------------------------------------------------------------------
# 实例聚合、视角层三分列、GT 匹配双口径（measurement_design items 1-3）
# ---------------------------------------------------------------------------

def test_run_r13_instance_view_layer_and_dual_gt_aggregation():
    rec, _ = _run_record()
    # item 1：实例主记录两板合计复算（abstain_rate 保留 6 位小数）
    for inst in INSTANCE_ORDER:
        c = rec["instances"][inst]["combined"]
        assert c["flag_count"] == EXPECT_COUNTS[inst]
        assert c["abstain_count"] == EXPECT_ABSTAIN[inst]
        assert c["abstain_rate"] == EXPECT_RATES[inst]
        assert c["abstain_rate"] == round(
            EXPECT_ABSTAIN[inst] / EXPECT_COUNTS[inst], 6)
        assert f"{EXPECT_ABSTAIN[inst]}/{EXPECT_COUNTS[inst]}" in \
            c["abstain_rate_arithmetic"]
        # 非弃权清单与逐旗明细一致（10 条非弃权有明细、弃权旗单列）
        n_detail = sum(1 for d in rec["instances"][inst]["per_flag_gt_detail"]
                       if not d["abstain"])
        assert n_detail == EXPECT_COUNTS[inst] - EXPECT_ABSTAIN[inst]
        for d in rec["instances"][inst]["per_flag_gt_detail"]:
            for o in d["gt_overlaps"]:
                assert set(o) == {"gt_id", "gt_category", "containment",
                                  "area_ratio", "channel"}
    # item 2：视角层三分列（中位数+min+max，不取整）复算；本轮无 None
    vl = rec["view_layer"]
    for view, names in (("top", ("top-i1", "top-i2", "top-i3")),
                        ("bottom", ("bottom-i1", "bottom-i2",
                                    "bottom-i3"))):
        v = vl[view]
        assert v["instances"] == list(names)
        fc = [EXPECT_COUNTS[n] for n in names]
        ar = [EXPECT_RATES[n] for n in names]
        mt = [rec["instances"][n]["combined"]["matches_total"]
              for n in names]
        assert v["flag_count"]["median"] == sorted(fc)[1]
        assert (v["flag_count"]["min"], v["flag_count"]["max"]) == \
            (min(fc), max(fc))
        assert v["matches"]["median"] == sorted(mt)[1]
        assert (v["matches"]["min"], v["matches"]["max"]) == (min(mt),
                                                              max(mt))
        assert v["abstain_rate"]["median"] == sorted(ar)[1]
        assert (v["abstain_rate"]["min"], v["abstain_rate"]["max"]) == \
            (min(ar), max(ar))
        assert v["abstain_rate_range"] == round(max(ar) - min(ar), 6)
        assert "均有定义" in v["abstain_rate"]["median_note"]
    assert vl["top"]["abstain_rate_range"] == 0.571429
    assert vl["bottom"]["abstain_rate_range"] == 0.25
    assert vl["top"]["abstain_rate"]["median"] == 0.7
    assert vl["bottom"]["abstain_rate"]["median"] == 1.0
    assert "0.571429" in vl["top"]["abstain_rate_range_arithmetic"]
    assert "0.25" in vl["bottom"]["abstain_rate_range_arithmetic"]
    # item 3：GT 匹配双口径复算（union ≥1 / agreement ≥2/3；分母 13）
    dual = rec["gt_match_dual"]
    assert dual["denominator"] == 13
    per_gt = {g["gt_id"]: g for g in dual["per_gt"]}
    assert len(per_gt) == 13
    # 逐 GT matched_by_count 从实例 matches_detail 独立归并复算（全 0）
    recount = {gid: 0 for gid in per_gt}
    for inst in INSTANCE_ORDER:
        for m in rec["instances"][inst]["combined"]["matches_detail"]:
            recount[m["gt_id"]] += 1
    for gid, g in per_gt.items():
        assert g["matched_by_count"] == recount[gid] == 0, gid
        assert g["hits"] == []
    assert dual["union"]["rule"] == "≥1 实例命中即计"
    assert dual["agreement"]["rule"] == "≥2/3 实例命中才计"
    assert dual["union"]["gt_ids"] == []
    assert dual["union"]["count"] == 0
    assert dual["union"]["gt_recall_union"] == 0.0
    assert dual["agreement"]["gt_ids"] == [] and \
        dual["agreement"]["count"] == 0
    assert dual["agreement"]["gt_recall_agreement"] == 0.0
    assert "应为空" in dual["denominator_note"]         # bottom 无 GT 在案


# ---------------------------------------------------------------------------
# 代表配置 joint + per-metric 范围（item 4；双 tie 按先序）
# ---------------------------------------------------------------------------

def _rep_state_report(rec, st):
    """代表配置合并态块 compare_v3 独立重算（测试内复算用）。"""
    rep = rec["representative_configuration"]["members"]
    flags, views = [], {}
    for inst in (rep["top"], rep["bottom"]):
        blk = rec["instances"][inst]["states"][st]
        flags.extend(blk["reader_flags"])
        views.update(blk["flag_views"])
    gt = rec["instances"]["top-i1"]["states"][st]["gt_entries"]
    return cal.compare_v3(flags, gt, flag_views=views)


def test_run_r13_representative_joint_and_metric_ranges():
    rec, _ = _run_record()
    rep = rec["representative_configuration"]
    # 代表配置选取复算：top 中位 7 tie（i2/i3）取先序 i2；bottom 中位 4
    # tie（i2/i3）取先序 i2（双 tie 均如实注明）
    assert rep["rule"].startswith("measurement_design item 4")
    assert rep["members"] == {"top": "top-i2", "bottom": "bottom-i2"}
    sel = rep["selection"]
    assert sel["top"]["median_flag_count"] == 7
    assert sel["top"]["tie"] is True and "先序" in sel["top"]["tie_note"] \
        and "tie" in sel["top"]["tie_note"]
    assert sel["top"]["flag_count_by_instance"] == {"top-i1": 10,
                                                    "top-i2": 7,
                                                    "top-i3": 7}
    assert sel["bottom"]["median_flag_count"] == 4
    assert sel["bottom"]["tie"] is True and "先序" in \
        sel["bottom"]["tie_note"]
    assert sel["bottom"]["flag_count_by_instance"] == {"bottom-i1": 3,
                                                       "bottom-i2": 4,
                                                       "bottom-i3": 4}
    # 代表配置合并态块 compare_v3 独立重算（由成员实例内嵌输入重建）
    agg = rec["aggregation_representative"]
    p = _rep_state_report(rec, "prep1")
    a = _rep_state_report(rec, "applied")
    n_gt = p["gt_count"] + a["gt_count"]
    n_match = len(p["matches"]) + len(a["matches"])
    n_gm = p["gt_matched_count"] + a["gt_matched_count"]
    n_sc = p["reader_scored_count"] + a["reader_scored_count"]
    n_ab = p["abstain"]["abstain_count"] + a["abstain"]["abstain_count"]
    n_fl = p["reader_flag_count"] + a["reader_flag_count"]
    assert agg["flag_count_total"] == n_fl == 11       # 7（top-i2）+4
    assert agg["gt_count_total"] == n_gt == 13
    assert agg["matches_total"] == n_match == 0
    assert agg["gt_matched_total"] == n_gm == 0
    assert agg["scored_total"] == n_sc == 1
    assert agg["abstain_count_total"] == n_ab == 10
    assert agg["gt_recall_total"] == round(0 / 13, 6) == 0.0
    assert agg["seed_match_rate_total"] == round(0 / 1, 6) == 0.0
    assert agg["abstain_rate_total"] == round(10 / 11, 6) == 0.909091
    assert "0/13" in agg["gt_recall_arithmetic"]
    assert "10/11" in agg["abstain_rate_arithmetic"]
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert "代表配置" in agg["scope"] and "不挑优" in agg["scope"]
    # APR-0011 达标评估逐项复算（阈值零改动；联合 not_met，三项未达线）
    comp = rec["compliance_representative"]
    criteria = {c["id"]: c for c in comp["criteria"]}
    assert criteria["gt_count_ge_12"]["actual"] == 13
    assert criteria["gt_count_ge_12"]["met"] is True
    assert criteria["gt_recall_ge_0.75"]["actual"] == 0.0
    assert criteria["gt_recall_ge_0.75"]["met"] is False
    assert criteria["seed_match_rate_ge_0.5"]["actual"] == 0.0
    assert criteria["seed_match_rate_ge_0.5"]["met"] is False
    assert criteria["abstain_rate_le_0.5"]["actual"] == 0.909091
    assert criteria["abstain_rate_le_0.5"]["met"] is False
    assert "阈值零改动" in criteria["abstain_rate_le_0.5"]["note"]
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    assert "描述性边界" in criteria["abstain_rate_le_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5", "r6",
                                     "r7", "r8", "r9", "r10", "r11",
                                     "r12", "r13"}
    assert consec["rounds"]["r12"] == "not_met（在案）"
    assert consec["rounds"]["r13"] == "not_met（本轮）"
    assert comp["joint_evaluation"] == "not_met"
    assert "代表配置" in comp["scope_note"] and "不挑优" in comp["scope_note"]
    # per-metric 实例间范围（item 4 三并列之二）复算
    mr = rec["metric_ranges_instance"]
    assert mr["top"]["flag_count"] == {"min": 7, "max": 10}
    assert mr["top"]["abstain_rate"] == {"min": 0.285714, "max": 0.857143}
    assert mr["top"]["abstain_count"] == {"min": 2, "max": 7}
    assert mr["top"]["matches_total"] == {"min": 0, "max": 0}
    assert mr["top"]["scored"] == {"min": 1, "max": 5}
    assert mr["bottom"]["flag_count"] == {"min": 3, "max": 4}
    assert mr["bottom"]["abstain_rate"] == {"min": 0.75, "max": 1.0}
    assert mr["bottom"]["abstain_count"] == {"min": 3, "max": 4}
    assert mr["bottom"]["matches_total"] == {"min": 0, "max": 0}
    assert mr["bottom"]["scored"] == {"min": 0, "max": 1}
    assert "note" not in mr["bottom"]["abstain_rate"]   # 本轮无 None 实例


# ---------------------------------------------------------------------------
# 预注册假设裁决（主通道 0/0/0⇒字母=supported+机制观察单列）
# ---------------------------------------------------------------------------

def test_run_r13_hypothesis_supported_verdict_and_mechanism():
    rec, _ = _run_record()
    prep = _load("r13-prep-record.json")
    ht = rec["hypothesis_test"]
    assert ht["kind"] == "preregistered_hypothesis_test"
    assert ht["hypothesis_id"] == \
        "r12-dev-record-candidate-0-s4i-operationalize"
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r13-prep-record.json")
    # 判据引用=r13-prep-record.json hypothesis_test 原文（逐字一致）
    quote = ht["preregistered_criteria_quote"]
    for k in ("hypothesis", "support_condition", "reject_condition",
              "null_result_note", "test_design", "declaration",
              "metric_lesson_application"):
        assert quote[k] == prep["hypothesis_test"][k], k
    pq = prep["hypothesis_test"]["preregistered_criteria_quote"]
    assert quote["candidate_0_target"] == pq["candidate_0_target"]
    assert quote["user_directive_2026_09_08"] == pq[
        "user_directive_2026_09_08"]
    assert "量化判据" in quote["candidate_0_target"]
    assert "极差 ≤5" in quote["support_condition"] and \
        "几何门面积比出局条目无回升" in quote["support_condition"]
    assert "极差 >5" in quote["reject_condition"] and \
        "≥10" in quote["reject_condition"]
    assert "正确测出无效" in quote["null_result_note"]
    assert "互不凌驾" in quote["null_result_note"]
    # 主通道度量=r13-prep-record 登记（bottom courtyard 非弃权极差）
    assert ht["primary_channel_metric"] == \
        prep["attribution_plan"]["primary_channel"]["metric"]
    # 描述性边界与门分列声明（≤5/≥10 非门阈值）
    assert "≤5" in ht["descriptive_boundary_note"] and \
        "≥10" in ht["descriptive_boundary_note"]
    assert "门阈值零改动" in ht["descriptive_boundary_note"]
    # 主通道实测：0/0/0、极差 0、聚合 0（r12 基线 18/0/0 交叉核对）
    m = ht["measurement"]
    assert m["bottom_courtyard_non_abstain_by_instance_r13"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert m["bottom_courtyard_non_abstain_range_r13"] == 0
    assert m["bottom_courtyard_non_abstain_aggregate_r13"] == 0
    assert m["range_le_5"] is True and m["aggregate_le_5"] is True
    assert m["reject_condition_met"] is False
    assert m["support_condition_met"] is True
    bc = m["baseline_cross_check"]
    assert bc["r12_by_instance_registered"] == bc["r12_by_instance_live"] == \
        {"bottom-i1": 18, "bottom-i2": 0, "bottom-i3": 0}
    assert bc["r12_range_registered"] == 18
    # 守门通道：top 几何门 0→0 无回升（support_condition 含守门要件）
    g = m["guard_channel"]
    assert g["guard_ok"] is True
    assert "R12=0→R13=0" in g["observation"]
    assert "独立" in g["note"]
    # 全旗标合计附记（非主通道）如实
    assert m["aggregate_context"]["apr0011_joint_evaluation_representative"] \
        == "not_met"
    assert "0.714286" in m["r13_total_flags_note"]
    assert "非主通道" in m["r13_total_flags_note"]
    # 字母裁决=supported（预注册判据复算一致；唯一正式裁决）
    assert ht["verdict"] == "supported"
    assert prep["hypothesis_test"]["support_condition"] in ht["verdict_rule"]
    assert prep["hypothesis_test"]["reject_condition"] in ht["verdict_rule"]
    assert "支持" in ht["verdict_text"] and "唯一正式裁决" in ht["verdict_text"]
    assert "0/0/0" in ht["verdict_text"] and "18/0/0" in ht["verdict_text"]
    assert "统计证明" in ht["verdict_text"] and "n=3" in ht["verdict_text"]
    assert "分列不合并" in ht["verdict_text"]
    assert "描述性边界" in ht["verdict_text"]
    # 机制观察单列（不凌驾字母裁决）：主通道收敛/接触性首验/黑点收敛/
    # 残余差异
    mo = ht["mechanism_observation"]
    assert "不凌驾" in mo["role"]
    mc = mo["main_channel_convergence"]
    assert "0/0/0" in mc["observation"] and "18" in mc["observation"]
    assert "系统性正常" in mc["observation"] or "系统性正常→不报告" in \
        mc["observation"]
    assert mc["counts"]["r12_by_instance"] == {"bottom-i1": 18,
                                               "bottom-i2": 0,
                                               "bottom-i3": 0}
    assert mc["counts"]["r13_by_instance"] == {"bottom-i1": 0,
                                               "bottom-i2": 0,
                                               "bottom-i3": 0}
    assert mc["counts"]["range"] == {"r12": 18, "r13": 0}
    assert "substring" in mc["reader_note_evidence_check"]
    assert len(mc["reader_note_evidence"]) == 6
    for ev in mc["reader_note_evidence"]:
        assert ev["excerpt"] in _load(RAW_FILES[ev["source"]])[
            "reading_notes"], ev["source"]
    # 接触性判据首验：8/8 条 top courtyard 弃权旗逐旗摘录
    cc = mo["contact_criterion_first_verification"]
    assert cc["contact_flag_count"] == 8
    assert "8/8" in cc["observation"] and "视觉贴近" in cc["observation"]
    assert cc["top_abstain_rate_range"] == 0.571429
    assert cc["top_abstain_rates_by_instance"] == {
        "top-i1": 0.7, "top-i2": 0.857143, "top-i3": 0.285714}
    assert "substring" in cc["contact_evidence_check"]
    assert len(cc["contact_evidence"]) == 8
    for ev in cc["contact_evidence"]:
        assert ev["excerpt"] in _raw_loc(ev["source"], ev["flag_id"]), \
            (ev["source"], ev["flag_id"])
    assert all(row["abstain"] is True and
               row["category"] == "courtyard_crowding"
               for row in cc["contact_flags"])
    # 黑点类收敛：8 旗全部弃权（other_advisory）
    bd = mo["black_dot_convergence"]
    assert bd["all_abstain"] is True
    assert bd["by_instance"] == {"bottom-i1": 2, "bottom-i2": 4,
                                 "bottom-i3": 2}
    assert len(bd["black_dot_flags"]) == 8
    assert all(row["abstain"] is True and row["category"] == "other_advisory"
               for row in bd["black_dot_flags"])
    for ev in bd["evidence"]:
        src = (_load(RAW_FILES[ev["source"]])["reading_notes"]
               if ev["kind"] == "reading_notes"
               else _raw_loc(ev["source"], ev["flag_id"]))
        assert ev["excerpt"] in src, ev.get("flag_id")
    assert "substring" in bd["evidence_check"]
    # 残余实例差异（右下孤立对三种处置+top i3 更果断）
    rd = mo["residual_instance_differences"]
    assert "三种处置" in rd["observation"] and "0.571429" in \
        rd["observation"]
    assert "未穷尽" in rd["observation"]
    for ev in rd["evidence"]:
        src = (_load(RAW_FILES[ev["source"]])["reading_notes"]
               if ev["kind"] == "reading_notes"
               else _raw_loc(ev["source"], ev["flag_id"]))
        assert ev["excerpt"] in src, ev.get("flag_id")
    assert "substring" in rd["evidence_check"]
    assert "不凌驾" in rd["status"] or "不凌驾" in rd["observation"]
    # 度量教训延续：r12 候选执行+多轴副现象记录；修订候选须预注册
    ml = ht["metric_lesson_continuation"]
    assert "量化判据" in ml["lesson"] and "supported" in ml["lesson"]
    assert "预注册" in ml["status"] and "不得反向放宽" in ml["status"]
    assert "不得回溯改判" in ml["status"]
    # reroute 类被动追踪（r12 通道延续；非本轮判据输入）
    rc = ht["reroute_continuation_r13"]
    assert rc["reroute_total_r13"] == 2
    assert rc["reroute_by_instance_r13"] == {"top-i1": 1, "top-i2": 1,
                                             "top-i3": 0, "bottom-i1": 0,
                                             "bottom-i2": 0, "bottom-i3": 0}
    detail = rc["reroute_flag_detail_r13"]
    assert [(r["instance"], r["flag_id"], r["abstain"],
             r["detected_substring_hits"], r["adjudication"])
            for r in detail] == [
        ("top-i1", "R13T-009", True, ["等长"],
         "candidate_citation_existence_undecidable"),
        ("top-i2", "R13T-001", False, [], "non_abstain_boundary_report")]
    for r in detail:
        assert r["form_desc_excerpt"] in _raw_text(r["source"])
    assert rc["production_chain"] == {"r8": 1, "r9": 0, "r10": 2, "r11": 3,
                                      "r12": 3, "r13": 2}
    assert "保守计数滥用型=1" in rc["misuse_chain_note"]
    assert "非本轮预注册判据输入" in rc["role"] or "被动追踪" in rc["role"]
    # 分层观察如实附录 + 混杂与优先声明（字母裁决不被机制/分层改写）
    st_ = ht["stratified_observation"]
    assert st_["top"]["r13_range"] == 0.571429
    assert st_["top"]["r13_by_instance"] == {"top-i1": 0.7,
                                             "top-i2": 0.857143,
                                             "top-i3": 0.285714}
    assert st_["bottom"]["r13_range"] == 0.25
    assert st_["bottom"]["r13_by_instance"] == {"bottom-i1": 1.0,
                                                "bottom-i2": 1.0,
                                                "bottom-i3": 0.75}
    assert "混杂因素" in st_["confounder_note"] and "n=3" in \
        st_["confounder_note"]
    assert "不得凌驾字母裁决" in st_["precedence_note"]
    assert "已证因果关系" in st_["precedence_note"]
    # 跨轮聚合弃权率语境（口径分列如实）
    ac = m["aggregate_context"]
    assert ac["abstain_rate_r9"] == 0.727273
    assert ac["abstain_rate_r10"] == 0.285714
    assert ac["abstain_rate_r11_representative"] == 0.133333
    assert ac["abstain_rate_r12_representative"] == 0.9


# ---------------------------------------------------------------------------
# 通道归因（vs R12；重放可复核；链自 r6 衔接）+ courtyard 追踪
# ---------------------------------------------------------------------------

def test_run_r13_channel_attribution_and_courtyard_reproducible():
    s49 = _s49()
    rec, _ = _run_record()
    run11 = _load("calibration-run-r11.json")
    run12 = _load("calibration-run-r12.json")
    ca = rec["channel_attribution"]
    # 方法声明：照抄 run-r12 重放口径（同源几何原语）
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r12.json" in ca["method"][
        "source_of_r11_r12_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] is True
    # 重放复算（R11/R12/R13 均用内嵌输入）与登记一致 + 对拍 compare_v3
    pairs11 = ca["method"]["replay_cross_check"][
        "r11_candidate_pairs_by_instance_state"]
    pairs12 = ca["method"]["replay_cross_check"][
        "r12_candidate_pairs_by_instance_state"]
    assert set(pairs11) == {f"{n}/{st}" for n in INSTANCE_ORDER
                            for st in ("applied", "prep1")}
    assert set(pairs12) == set(pairs11)
    for name in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            for run_x, pairs in ((run11, pairs11), (run12, pairs12)):
                blk = run_x["instances"][name]["states"][st]
                rp = s49.channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        blk["gt_entries"])
                assert s49.replay_matches_agree(rp, blk["compare_v3"])
                assert pairs[f"{name}/{st}"] == [list(p) for p in
                                                 rp["candidate_pairs"]]
    # R11 的恰 4 候选对（=r11 四条 matches）在 top-i1/top-i2/top-i3；
    # R12 十二件重放候选对=空集（与在案一致）
    flat11 = sorted(tuple(p) for v in pairs11.values() for p in v)
    assert flat11 == [("R11T-003", "GT-REVC-AP-6-R2LED2"),
                      ("R11T-009", "GT-REVC-P1-R4J3"),
                      ("R11T-010", "GT-REVC-AP-1-R5U6"),
                      ("R11T-012", "GT-REVC-P1-L1SHORT")]
    assert all(v == [] for v in pairs12.values())
    # R13 十二件重放对拍 compare_v3 全部一致（候选对=空集）
    pairs13 = ca["method"]["replay_cross_check"]["r13_candidate_pairs_by_part"]
    assert set(pairs13) == set(RAW_FILES)
    for key in RAW_FILES:
        blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
            STATE_OF_KEY[key]]
        rp = s49.channel_replay(blk["reader_flags"], blk["flag_views"],
                                blk["gt_entries"])
        assert pairs13[key] == [list(p) for p in rp["candidate_pairs"]]
        assert pairs13[key] == []                       # R13 零候选对
    # 通道分组条目（几何门 R12 0→R13 0；类别门 R12 0→R13 0）与重放一致
    def _entries_r13(failure):
        rows = []
        for key in RAW_FILES:
            blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
                STATE_OF_KEY[key]]
            rp = s49.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    blk["gt_entries"])
            rows += [e for e in rp["entries"] if e["failure"] == failure]
        return rows
    assert ca["channel_1_geometry_gate"]["r12_area_ratio_rejected_entries"] \
        == []
    assert ca["channel_1_geometry_gate"]["r13_area_ratio_rejected_entries"] \
        == _entries_r13("area_ratio_rejected") == []
    assert "0→0" in ca["channel_1_geometry_gate"]["change"]
    cat11 = ca["channel_2_category_gate"]["r11_category_mismatch_entries"]
    assert len(cat11) == 1
    e = cat11[0]
    assert (e["flag_id"], e["gt_id"], e["instance"], e["state"]) == \
        ("R11T-012", "GT-REVC-AP-8-R1Q2", "top-i3", "applied")
    assert e["containment"] == 0.616745 and e["area_ratio"] == 1.648816
    assert ca["channel_2_category_gate"][
        "r12_category_mismatch_entries"] == []
    assert ca["channel_2_category_gate"][
        "r13_category_mismatch_entries"] == []
    assert "0→0" in ca["channel_2_category_gate"]["change"]
    # 视角门：三轮重放均空（R13 bottom 非弃权旗与 GT 零近邻交叠）
    assert ca["view_gate_observations"]["r11_entries"] == []
    assert ca["view_gate_observations"]["r12_entries"] == []
    assert ca["view_gate_observations"]["r13_entries"] == []
    assert "应为空" in ca["view_gate_observations"]["note"]
    # 通道链自 r6 衔接（几何 1→0→0→0→0→0→0→0；类别 1→0→1→0→0→1→0→0）
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 0, "r9": 0, "r10": 0, "r11": 0, "r12": 0,
         "r13": 0}
    assert chain["category_gate_category_mismatch_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 1, "r9": 0, "r10": 0, "r11": 1, "r12": 0,
         "r13": 0}
    assert "通道级归因" in chain["scope"]
    # R13 特有观察：连续第二轮零匹配、courtyard 全弃权、reroute 构成变化
    spec = "\n".join(ca["r13_specific_observations"])
    assert "union=0/13" in spec and "agreement=0/13" in spec
    assert "R13T-001" in spec and "R13T-009" in spec
    assert "r8=1→r9=0→r10=2→r11=3→r12=3→r13=2" in spec
    assert "8 条全部弃权" in spec and "接触性判据" in spec
    assert "r13=0" in spec
    # courtyard 被动追踪（prep-record 预注册）：非弃权 0、弃权 8、命中 0
    ct = rec["courtyard_tracking"]
    na = ct["r13_courtyard_flags"]["non_abstain"]
    ab = ct["r13_courtyard_flags"]["abstain"]
    assert len(na) == 0 and len(ab) == 8
    assert ct["courtyard_matches_r13"] == 0
    assert all(r["view"] == "top" for r in ab)          # 8 条全部 top
    by_inst = {}
    for r in ab:
        by_inst.setdefault(r["instance"], []).append(r["flag_id"])
    assert {k: sorted(v) for k, v in by_inst.items()} == {
        "top-i1": ["R13T-004", "R13T-005", "R13T-010"],
        "top-i2": ["R13T-002", "R13T-005", "R13T-006"],
        "top-i3": ["R13T-002", "R13T-005"]}
    assert ct["courtyard_matches_r12"] == 0
    assert ct["courtyard_matches_r11"] == 3
    assert ct["courtyard_matches_r10"] == 1
    assert ct["courtyard_matches_r9"] == 0
    assert ct["courtyard_matches_r8"] == 1              # R8T-004↔AP-8
    assert "R8T-004" in ct["courtyard_matches_r8_detail"]
    assert "R10T-011" in ct["courtyard_matches_r10_detail"]
    assert "零再现" in ct["same_domain_note"]
    # bottom 观察：1 条非弃权零匹配属结构性（bottom 无 GT 在案）
    bz = ct["bottom_observation"]
    assert "应为空" in bz["fact"] and "无零旗标" in bz["fact"]
    for ev in bz["evidence"]:
        raw = _load(RAW_FILES[ev["source"]])["reading_notes"]
        assert ev["excerpt"] in raw
    assert "pairing_caveat" in ca and "通道级" in ca["pairing_caveat"]
    # 双条件数值独立复算（top-i2 R13T-001 vs 全部 applied GT 零近邻）
    blk = rec["instances"]["top-i2"]["states"]["applied"]
    f001 = next(f for f in blk["reader_flags"]
                if f["flag_id"] == "R13T-001")
    best = max(cal._containment(f001["frame_box_pct"],
                                g2["frame_box_pct"]) or 0.0
               for g2 in blk["gt_entries"])
    assert best < cal.CONTAINMENT_MIN                   # 未达近邻门
    # 主通道独立复算：bottom 三实例 courtyard 非弃权=0（逐实例重放）
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        for st in ("applied", "prep1"):
            b = rec["instances"][name]["states"][st]
            abst = set(b["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in b["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        assert cnt == 0, name
    # r12 基线独立复算（run-r12 内嵌输入）：18/0/0
    base_live = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        for st in ("applied", "prep1"):
            b = run12["instances"][name]["states"][st]
            abst = set(b["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in b["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        base_live[name] = cnt
    assert base_live == {"bottom-i1": 18, "bottom-i2": 0, "bottom-i3": 0}


# ---------------------------------------------------------------------------
# 预注册链、冻结哈希、阈值零覆盖
# ---------------------------------------------------------------------------

def test_run_r13_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r13_prep_record_preregistration",
            "observation_guidance_r13", "observation_guidance_r12_baseline",
            "observation_guidance_r9_chain", "observation_guidance_r8_chain",
            "pre_round_review_diag_d1", "pre_round_review_diag_d2",
            "pre_round_review_diag_d3",
            "r12_dev_record_preregistration_source",
            "r12_prep_record_witness_source",
            "r11_dev_record_witness_chain", "r11_prep_record_witness_chain",
            "r10_dev_record_witness_chain", "r10_prep_record_witness_chain",
            "r9_dev_record_witness_chain", "r9_prep_record_witness_chain",
            "r8_dev_record_witness_chain", "r8_prep_record_witness_chain",
            "r7_prep_record_witness_chain",
            "render_framing_r5_preregistration", "gt_reprojection_log_r5",
            "gt_seed_prep1", "gt_expansion_applied", "gt_audit_r1_closed",
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
    # 预注册件哈希锚（先验给定的前 8；含 r12-dev→D1–D3→r13-prep 链）
    for rel, want in PREREG_ANCHORS.items():
        assert _sha(rel).startswith(want), rel
    # 阈值常量零覆盖（与 r12 相同；比较器本体零改动）
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "零覆盖" in rec["preregistration"]["comparator"]["thresholds_note"]
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    # 命名覆盖入 naming_constraints（per r13-prep-record
    # protocol_amendment.naming：随指引落盘固化）
    assert "R12T/R12B→R13T/R13B" in rec["naming_constraints"]
    assert "reader-r12→reader-r13" in rec["naming_constraints"]
    assert "判读实质判据零变更" in rec["naming_constraints"]
    assert "实例间编号独立" in rec["naming_constraints"]
    assert "落盘固化" in rec["naming_constraints"]
    # 指引锚：本轮=r13 指引（c28806e1），基线=r12 指引（0ac22fcd）
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"].startswith("c28806e1")
    assert gp["frozen_before_render"] is True
    assert gp["frozen_before_read"] is True
    assert gp["baseline_ref"]["sha256"].startswith("0ac22fcd")
    # 指引内容锚：r13 指引含量化判据/接触性判据/R13 前缀/轮次常量；
    # r12 基线含收窄判据与 r12 轮次常量
    g13 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                            "observation-guidance-r13.md"),
               encoding="utf-8").read()
    assert "接触性判据" in g13 and "至少出现 3 处" in g13 \
        and "三路出口" in g13 and "最小重复单元" in g13
    assert "2026-09-08-r13" in g13 and "R13T-001" in g13
    assert "非放宽" in g13
    assert "v1.2" in g13
    g12 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                            "observation-guidance-r12.md"),
               encoding="utf-8").read()
    assert "整段规则周期" in g12 and "示例 c" in g12 \
        and "2026-09-07-r12" in g12
    # 预注册链声明（round12-dev-record→D1–D3→r13-prep-record 先于盲读）
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "1411dab6" in rec["preregistration"]["note"]
    assert "2387daed" in rec["preregistration"]["note"]
    assert "b79bc617" in rec["preregistration"]["note"]
    assert "c09154a4" in rec["preregistration"]["note"]
    assert "b1c0d8b5" in rec["preregistration"]["note"]
    assert "c28806e1" in rec["preregistration"]["note"]
    assert "r13-prep-record.json" in rec["preregistration"]["note"]
    assert "measurement_design" in rec["preregistration"]["note"]
    # 参照轮哈希在案（r12=上一轮基线；r13 前 run 不含本轮）
    ref12 = rec["reference_rounds"]["r12_run"]
    assert ref12["sha256"] == _sha(ref12["path_rel"])
    assert ref12["sha256"].startswith("2ec2fb04")
    assert "r13_run" not in rec["reference_rounds"]
    # 复用渲染见证：两 bottom 渲染逐字节相同（R5 仪器事实沿用）
    import hashlib
    bot_a = open(os.path.join(CAL_DIR, "renders-r5",
                              "applied-bottom.png"), "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r5",
                              "prep1-bottom.png"), "rb").read()
    assert hashlib.sha256(bot_a).hexdigest() == \
        hashlib.sha256(bot_p).hexdigest() == BOTTOM_PNG_SHA256


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round13_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=单变量指引侧变更轮（§4 可操作化）+pre_round_review 前置
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert "可操作化" in dev["round_nature"] and "接触性判据" in \
        dev["round_nature"]
    assert "pre_round_review" in dev["round_nature"] and "D1/D2/D3" in \
        dev["round_nature"]
    assert "c28806e1" in dev["round_nature"] and "0ac22fcd" in \
        dev["round_nature"]
    assert "不构成任何放宽" in dev["round_nature"] and "一字未松" in \
        dev["round_nature"]
    assert "拍板" in dev["round_nature"] and "2387daed" in dev["round_nature"]
    assert "measurement_design" in dev["round_nature"] and "五条" in \
        dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    # 诊断结果与 run-r13 一致（代表配置口径：top-i2+bottom-i2 双 tie）
    run, _ = _run_record()
    assert "top-i2" in dev["diagnostic_result"]["aggregation_scope"]
    assert "bottom-i2" in dev["diagnostic_result"]["aggregation_scope"]
    assert "tie" in dev["diagnostic_result"]["aggregation_scope"]
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation_representative"]["abstain_rate_total"] == 0.909091
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation_representative"]["gt_recall_total"] == 0.0
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation_representative"]["seed_match_rate_total"] == 0.0
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert dev["diagnostic_result"]["gt_match_dual"] == {
        "union": run["gt_match_dual"]["union"],
        "agreement": run["gt_match_dual"]["agreement"]}
    crit = {c["id"]: c for c in dev["diagnostic_result"]["criteria"]}
    assert crit["gt_count_ge_12"]["met"] is True
    assert crit["gt_recall_ge_0.75"]["met"] is False
    assert crit["seed_match_rate_ge_0.5"]["met"] is False
    assert crit["abstain_rate_le_0.5"]["met"] is False
    # 假设裁决节与 run-r13 一致（verdict=supported；主通道 0/0/0）
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "supported"
    assert dev["hypothesis_test_i"]["measurement"][
        "bottom_courtyard_non_abstain_range_r13"] == 0
    assert dev["hypothesis_test_i"]["measurement"][
        "guard_channel"]["guard_ok"] is True
    # 联合评价趋势：连续达标计数 0（R12 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["after_r12"]["consecutive_met_count"] == 0
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"] and "不得写成已达成" in trend["note"]
    assert "代表配置" in trend["aggregation_scope_note"]
    # r5→r13 逐轮走势表（数值取各轮 run-record；r11–r13 行=代表配置口径）
    assert [row["round"] for row in trend["by_round"]] == \
        ["r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13"]
    by_r = {row["round"]: row for row in trend["by_round"]}
    assert by_r["r8"]["abstain_rate_total"] == 0.222222
    assert by_r["r8"]["matches_total"] == 1
    assert by_r["r9"]["abstain_rate_total"] == 0.727273
    assert by_r["r9"]["matches_total"] == 0
    assert by_r["r10"]["abstain_rate_total"] == 0.285714
    assert by_r["r10"]["matches_total"] == 1
    assert by_r["r11"]["abstain_rate_total"] == 0.133333
    assert by_r["r11"]["matches_total"] == 1
    assert by_r["r11"]["aggregation_scope"] == \
        "representative_configuration（item 4）"
    assert by_r["r12"]["abstain_rate_total"] == 0.9
    assert by_r["r12"]["flag_count_total"] == 10
    assert by_r["r12"]["matches_total"] == 0
    assert by_r["r12"]["aggregation_scope"] == \
        "representative_configuration（item 4）"
    assert by_r["r13"]["abstain_rate_total"] == 0.909091
    assert by_r["r13"]["flag_count_total"] == 11
    assert by_r["r13"]["matches_total"] == 0
    assert by_r["r13"]["aggregation_scope"] == \
        "representative_configuration（item 4）"
    assert by_r["r5"]["round_id"] == "2026-09-06-r5"
    for row in trend["by_round"]:
        assert row["joint_evaluation"] == "not_met"
        assert row["source"]["sha256"] == _sha(row["source"]["path_rel"])
    # run-r13 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r13.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # gt-audit-r1 引用与 run 一致（1f20554a；GT 侧已全部关闭）
    assert dev["gt_audit_ref"] == run["gt_audit_reference"]
    assert dev["gt_audit_ref"]["sha256"].startswith("1f20554a")
    # 旗标产量记账（35=10+25；实例/视角分列）
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 25 and fp["non_abstain_count"] == 10
    assert fp["abstain_rate_all_flags"] == 0.714286
    assert fp["abstain_rate_by_instance"] == EXPECT_RATES
    assert fp["abstain_rate_range_by_view"]["top"] == 0.571429
    assert fp["abstain_rate_range_by_view"]["bottom"] == 0.25
    assert "无零旗标" in fp["abstain_rate_range_by_view"]["note"]
    assert fp["flag_count_by_instance"] == EXPECT_COUNTS
    assert sum(fp["flag_count_by_file"].values()) == 35
    assert fp["reroute_by_instance"] == {"top-i1": 1, "top-i2": 1,
                                         "top-i3": 0, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fp["reroute_class_production"] == 2
    assert fp["parse_rejections"] == []
    assert fp["reader_ids"] == READER_IDS
    assert "冻结证据" in fp["note"] and "12/12" in fp["note"]
    assert "indent=1" in fp["note"] and "无围栏剥离" in fp["note"]
    assert "R12T/R12B→R13T/R13B" in fp["note"]
    # 诚实结论：字母裁决=supported；三条机制结论如实
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.909091" in hc and "development 域" in hc
    assert "0.0（0/13）" in hc and "union=0/13" in hc and "agreement=0/13" \
        in hc
    assert "支持" in hc and "唯一正式裁决" in hc
    assert "0/0/0" in hc and "18/0/0" in hc and "0≤5" in hc
    assert "统计证明" in hc and "n=3" in hc
    assert "8/8" in hc and "视觉贴近" in hc and "0.571429" in hc
    assert "reader_note_evidence" in hc and "黑点" in hc
    assert "三种处置" in hc and "未穷尽" in hc
    assert "正确测出无效" in hc
    assert "无零旗标格" in hc and "不编造数值" in hc
    assert "系统性正常→不报告" in hc
    assert "12/12 派次 v1.2 合规" in hc
    assert "indent=1" in hc and "无围栏剥离" in hc
    assert "机制结论如实单列" in hc
    assert "混杂" in hc
    assert "gt-audit-r1" in hc and "全部关闭" in hc
    assert "in_calibrated_range" in hc and "不得冒充留出" in hc
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r13 冻结工件一致（含 r12-dev→D1–D3→
    # r13-prep 链）
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles
    assert chain["r12_dev_record_preregistration_source"]["sha256"] == \
        _sha("out/v3-tl2/calibration/round12-dev-record.json")
    assert chain["r13_prep_record_preregistration"]["sha256"].startswith(
        "b1c0d8b5")
    assert chain["observation_guidance_r13"]["sha256"].startswith("c28806e1")
    assert chain["pre_round_review_diag_d1"]["sha256"].startswith("2387daed")
    assert chain["pre_round_review_diag_d2"]["sha256"].startswith("b79bc617")
    assert chain["pre_round_review_diag_d3"]["sha256"].startswith("c09154a4")
    assert "1411dab6" in dev["preregistration_chain_note"]
    assert "b1c0d8b5" in dev["preregistration_chain_note"]
    assert "2387daed" in dev["preregistration_chain_note"]


def test_dev_record_observations_and_next_targets():
    """方向性观察与下一迭代目标：通道数值可独立复算（描述性，不入
    度量）；next_iteration_targets 覆盖 top 接触性弃权高企的渲染侧消歧
    候选/§4(iii) 分辨率适配候选（不得反向放宽）/示例 c 保留/courtyard/
    GT 关闭/留出集运行时机（须用户）；不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    run, _ = _run_record()
    obs = "\n".join(dev["directional_observation_vs_r12"])
    # R12 基线匹配数值复算（r11 四条 matches 之一在 run-r12 转录在案）
    # 与 R13 连续第二轮零匹配
    run11 = _load("calibration-run-r11.json")
    blk11 = run11["instances"]["top-i1"]["states"]["prep1"]
    f009 = next(f for f in blk11["reader_flags"]
                if f["flag_id"] == "R11T-009")
    g11 = next(e for e in blk11["gt_entries"]
               if e["gt_id"] == "GT-REVC-P1-R4J3")
    assert round(cal._containment(f009["frame_box_pct"],
                                  g11["frame_box_pct"]), 6) == 0.723377
    # R12→R13 分层/聚合数字在观察中如实引用
    for need in ("12→12", "44→35", "10/7/7/3/4/4", "25→10", "19→25",
                 "0.431818", "0.714286", "0/0/0", "18", "0.571429", "0.25",
                 "0.875/0.833333/0.5", "0.7/0.857143/0.285714",
                 "1.0/1.0/0.75", "10/7/7", "3/4/4", "20/0/2→3/4/4",
                 "0.9（9/10）→0.909091（10/11）", "0/13", "R13T-001",
                 "R13T-009", "R13B-001", "R11T-012", "supported", "8/8",
                 "接触性判据", "视觉贴近", "黑点", "蝶形", "三种处置",
                 "tie", "先序", "r6=1→r7=0", "几何门", "类别门",
                 "候选对=空集", "gt-audit-r1", "12/12", "indent=1",
                 "无围栏剥离", "右下", "孤立", "系统性正常→不报告",
                 "描述性边界", "r8=1→r9=0→r10=2→r11=3→r12=3→r13=2",
                 "不凌驾"):
        assert need in obs, need
    nxt = "\n".join(dev["next_iteration_targets"])
    # top 接触性弃权高企的渲染侧消歧候选（须预注册+零仪器变更纪律例外）
    assert "接触性弃权高企" in nxt and "8/8" in nxt
    assert "图例" in nxt and "渲染侧" in nxt
    # §4(iii) 接触性判据分辨率适配候选（指引侧，须预注册，不得反向放宽）
    assert "§4(iii)" in nxt and "分辨率适配" in nxt
    assert "预注册" in nxt and "不得反向放宽" in nxt
    assert "不得回溯改判" in nxt
    # 示例 c 保留观察（reroute/滥用型被动追踪零期望）
    assert "示例 c" in nxt and "滥用型" in nxt and "零期望" in nxt
    # courtyard 追踪延续（跨轮对照）
    assert "courtyard" in nxt and "追踪" in nxt
    # GT 侧已全关闭（gt-audit-r1 三候选关闭结论被引用）
    assert "gt-audit-r1" in nxt and "1f20554a" in nxt
    assert "三候选" in nxt and "全部关闭" in nxt
    # 留出集运行时机=开发线收敛判断（须用户）
    assert "HOLDOUT-PLAN.md" in nxt and "a4b80193" in nxt
    assert "holdout-candidates-r1" in nxt
    assert "留出集运行时机" in nxt and "须用户" in nxt
    # 不得把正式采纳门槛达成写成已达成；in_calibrated_range 恒 False
    assert "in_calibrated_range 恒 False" in nxt
    assert "人工批准" in nxt
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r13-prep-record.json")


def test_s49_rerun_byte_identical_and_overwrite_guard():
    """s49 重跑语义：同参重建 byte-exact 一致；防覆写护栏（字节等同→
    幂等跳过零覆写；不同→fail-closed）。"""
    s49 = _s49()
    rec, disk = _run_record()
    dev, dev_disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    run_rebuilt = s49.build_run()
    assert hashing.canonical_json_bytes(run_rebuilt) == disk
    run_sha = _sha("out/v3-tl2/calibration/calibration-run-r13.json")
    dev_rebuilt = s49.build_dev_record(run_rebuilt, run_sha)
    assert hashing.canonical_json_bytes(dev_rebuilt) == dev_disk
    # 声明常量（无 wall-clock）
    assert s49.DECLARED_DATE == "2026-09-08"
    assert s49.ROUND_ID == "2026-09-08-r13"
    # 主通道描述性边界与产量链基线常量（操作化定义）
    assert s49.MAIN_CHANNEL_DESCRIPTIVE_BOUNDARIES == DESCRIPTIVE_BOUNDARIES
    assert s49.REROUTE_CHAIN_PRIOR == {"r8": 1, "r9": 0, "r10": 2, "r11": 3,
                                       "r12": 3}
    assert s49.R12_BOTTOM_COURTYARD_BASELINE == {"bottom-i1": 18,
                                                 "bottom-i2": 0,
                                                 "bottom-i3": 0}
    # 防覆写护栏纯函数语义
    assert s49.overwrite_guard(None, b"x") == "write"
    assert s49.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s49.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：目标两件已存在且字节等同 → main 正常完成（零覆写）
    before = open(os.path.join(CAL_DIR, "calibration-run-r13.json"),
                  "rb").read()
    s49.main()                                          # 不抛异常=幂等路径
    after = open(os.path.join(CAL_DIR, "calibration-run-r13.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    dev_after = open(os.path.join(CAL_DIR, "round13-dev-record.json"),
                     "rb").read()
    assert dev_after == dev_disk                 # 字节零改动
    # run_record_ref 仍指向 run-r13 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r13.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "三路出口" in rp["abstain_semantics"]
    assert "接触性判据" in rp["abstain_semantics"]
    assert "最小重复单元" in rp["abstain_semantics"]
    assert "反放宽条款" in rp["abstain_semantics"]
    assert "无任何 GT" in rp["discipline"]
    assert "禁止交流" in rp["per_view_dispatch"]
    assert "v1.2" in rp["per_view_dispatch"]
    assert "零诊断报告内容" in rp["per_view_dispatch"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r13-prep-record.json" in rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "10/7/7/3/4/4" in rec["deterministic_recompute_note"]
    assert "2026-09-08-r13" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域单变更轮，非留出；
    # advisory 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert dev["is_gate"] is False
    assert rec["compliance_representative"][
        "critic_calibration_in_range"] is False
    assert "不是门" in dev["notes"][0]
    # 命名覆盖（随指引落盘固化）如实入账：前缀与 reader_id 两处
    assert "R12T/R12B→R13T/R13B" in rec["naming_constraints"]
    assert "reader-r12→reader-r13" in rec["naming_constraints"]
    prep = _load("r13-prep-record.json")
    assert "机械替换" in prep["protocol_amendment"]["naming"] or \
        "落盘固化" in prep["protocol_amendment"]["naming"]
    # 三分裁决纪律声明在案（字母裁决不被机制观察改写；supported≠统计
    # 证明；主通道判据与 APR-0011 门分开表述）
    assert "不得凌驾或改写字母裁决" in dev["notes"][-1]
    assert "supported 维持不变" in dev["notes"][-1]
    assert "分开表述" in dev["notes"][-1]
    assert "小样本方向性证据" in dev["notes"][-1]
    # 指引侧=可操作化方向：不构成任何门的放宽或收紧；判断责任一字未松
    assert "no_loosening_note" in prep
    assert "不构成任何门的放宽或收紧" in prep["no_loosening_note"]
    assert "一字未松" in prep["no_loosening_note"]
    assert "放宽或收紧" in dev["notes"][1]
    # 主通道判据非门：字母裁决与门分列（run 内分开表述）；描述性边界
    # 与门分列
    assert rec["hypothesis_test"]["verdict"] == "supported"
    assert rec["compliance_representative"]["joint_evaluation"] == "not_met"
    assert "分列不合并" in rec["hypothesis_test"]["verdict_text"]
    assert rec["hypothesis_test"]["measurement"][
        "bottom_courtyard_non_abstain_range_r13"] == 0
    assert rec["hypothesis_test"]["measurement"]["guard_channel"][
        "guard_ok"] is True


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
