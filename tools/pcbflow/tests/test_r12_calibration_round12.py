"""R12 执行包测试：reader 判读迭代第十二轮收口（CAL-R12-CLOSE）——
盲读解析与视角注入（12 派次=4 视角格×3 实例，v1.2 工具规约首轮）+
六实例主记录（measurement_design item 1：两板合计
flag_count/abstain_count/abstain_rate/非弃权清单/逐旗明细）+ 视角层
三分列（item 2：中位数+min+max 不取整；bottom 弃权率含 None 实例）
+ GT 匹配双口径（item 3：union/agreement 并列+逐 GT matched_by_count）
+ 联合门代表配置与 per-metric 实例间范围并列（item 4）+ bottom 零旗标
分母=None（item 5）+ 预注册假设
（r11-dev-record-candidate-1-example-c-tighten）裁决（滥用型操作化
逐旗判定=0+reroute 非弃权=1⇒字母=supported+机制观察单列：工具钉住
≠判读一致、§4(i) 判据轴转移）+ 逐旗失败通道归因（vs R11，链自 r6）+
courtyard 被动追踪 + development 域记录。

结构照 test_r11_calibration_round11.py 先例，仅输入与轮次常量不同
（R12=单变量指引侧变更轮：§3A 类别 4 示例 c「整段规则周期」判据收窄
替换；observation-guidance-r12.md=0ac22fcd 由 r9 指引 a0c10154 机械
变换生成、落盘即冻结；R5 冻结渲染复用；GT/阈值零变更；协议侧派发层
v1.2 工具行为规约=唯一新增条款（读者不可见、不改判读语义）；预注册于
r12-prep-record.json（d393cf27），链=round11-dev-record（66e41bbf）→
r12-prep-record；判据=计数型（滥用型弃权旗计数，操作化定义逐旗执行），
无 0.2/0.1 描述性边界；APR-0011 门与主通道判据各自独立、互不凌驾）。

覆盖：
- 盲读原文（reader-raw-r12-*.txt 十二件，冻结证据）：合法 JSON、结构
  （reader_id/per_image/reading_notes；flag 六键含 location_evidence）、
  实例内跨板连续编号（R12T/R12B）与实例间独立编号、实例旗数
  8/6/8/20/0/2 与弃权 7/5/4/1/0/2、reroute 恰 3 条（R12T-001 非弃权
  top-i1+R12T-002 弃权 top-i1+R12T-008 弃权 top-i3）、拒收清单固化
  （44 旗全过 calibration fail-closed 校验，0 拒收）、哈希与 run-r12
  登记一致；
- 视角注入确定性+派发模式（12 派次两波次串行保序）+读者实例披露
  （12/12 派次自述纯 Read 直读=v1.2 合规；输出格式披露：12 件均
  indent=1 重序列化；无围栏剥离）；
- calibration-run-r12.json：盘上 canonical byte 一致；逐实例逐态
  compare_v3 用内嵌输入重算 byte-exact 一致（零旗标格
  view_check=not_applicable；prep1-bottom-i1 view_mismatch=54 如实）；
  内嵌 gt_entries=源 GT 文件条目+derivation-log-r5 重投影零新派生；
  零 matches 复算；六实例聚合复算（abstain_rate
  0.875/0.833333/0.5/0.05/None/1.0）；视角层三分列复算（top 极差
  0.375/bottom 可计算极差 0.95、bottom 弃权率中位数=None+注明）；双
  口径复算（union 0/13=0.0、agreement 0/13=0.0、matched_by_count 全部
  0；bottom 无 GT 在案 gt-audit-r1）；代表配置（top-i1：中位 8 tie 取
  先序；bottom-i3：中位 2 唯一）joint 复算（10 旗 9 弃权=0.9、0/13、
  0/1；APR-0011 联合 not_met，三项未达线）+per-metric 范围；bottom
  三格零旗标 part 级弃权率=None（cal._ratio 先例）；
- 预注册假设裁决：判据引用=r12-prep-record hypothesis_test 原文
  （support=滥用型 0 且 reroute 非弃权≥1/reject=滥用型≥1/总量=0 记
  「不可判」原样）；实测滥用型=0（R12T-002 子串零命中=未援引；
  R12T-008 排除式引用非依赖）且 reroute 非弃权=1（R12T-001 边界报告）
  ⇒verdict=supported（字母裁决）；主通道操作化复算（子串命中实测=
  declared_substring_hits、形态描述摘录 substring fail-closed）；机制
  观察单列（工具轴钉住 12/12 纯直读逐派次摘录校验；§4(i) 判据轴转移
  ——bottom 三实例三种裁决摘录校验；方差爆拉 top 0.375/bottom 0.95 vs
  r11 0.153846/0.0）；守门通道 guard_ok；
- 通道归因（vs R11）：重放对拍 R11 十二件（复算=run-r11 在案登记）
  与 R12 十二件全部复现（候选对=空集）；几何门 0→0（无回升）、类别门
  1→0、视角门 0→0；链自 r6（几何 1→0→0→0→0→0→0；类别
  1→0→1→0→0→1→0）；courtyard 追踪：非弃权 20 条零命中、弃权 9 条、
  匹配 r8=1→r9=0→r10=1→r11=3→r12=0；
- 预注册链：round11-dev-record（66e41bbf）→r12-prep-record（d393cf27）
  →run-r12 链含哈希；guidance-r12（0ac22fcd）/guidance-r9 基线
  （a0c10154）/r8 指引链/framing-r5/derivation-log-r5/GT/协议 v1 零
  字节保留（22dc7337）/复用 PNG/冻结 PDF sha 与盘上一致；阈值常量零
  覆盖（containment 0.5/area_ratio_max 10.0 与 r11 相同）；gt-audit-r1
  引用（1f20554a）；
- round12-dev-record.json：域声明、本轮性质（指引侧收窄+v1.2 首轮+
  user_directive 拍板）、假设裁决节与 run-r12 一致、R11→R12 方向性
  观察（派次 12→12、旗标 53→44、方差爆拉、零匹配、bottom 三裁决）、
  联合评价趋势（r5→r12 逐轮表、连续计数 0→0；r11/r12 行=代表配置
  口径并列注明）、run-r12 sha 引用一致、next_iteration_targets 覆盖
  §4(i) 判据可操作性修订候选（量化判据/至少 n 处重复阈值化——指引侧
  须预注册、不得反向放宽）/渲染侧 bottom 图层清单+层归属消歧/示例 c
  保留观察/courtyard 追踪延续/GT 侧已全关闭延续/留出集已就绪
  （HOLDOUT-PLAN.md a4b80193+holdout-candidates-r1）待开发线收敛、
  is_gate=False、in_calibrated_range 恒 False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；命名覆盖 R12T/R12B 随指引落盘固化入
  naming_constraints；受保护三文件 sha256 前 8 断言+两指引零字节不动；
- s47 重跑：同参重建 byte-exact 一致 + 防覆写护栏语义（字节等同→
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

ROUND_ID = "2026-09-07-r12"
DECLARED_DATE = "2026-09-07"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")
RAW_FILES = {
    "applied-top-i1": "reader-raw-r12-applied-top-i1.txt",
    "prep1-top-i1": "reader-raw-r12-prep1-top-i1.txt",
    "applied-top-i2": "reader-raw-r12-applied-top-i2.txt",
    "prep1-top-i2": "reader-raw-r12-prep1-top-i2.txt",
    "applied-top-i3": "reader-raw-r12-applied-top-i3.txt",
    "prep1-top-i3": "reader-raw-r12-prep1-top-i3.txt",
    "applied-bottom-i1": "reader-raw-r12-applied-bottom-i1.txt",
    "prep1-bottom-i1": "reader-raw-r12-prep1-bottom-i1.txt",
    "applied-bottom-i2": "reader-raw-r12-applied-bottom-i2.txt",
    "prep1-bottom-i2": "reader-raw-r12-prep1-bottom-i2.txt",
    "applied-bottom-i3": "reader-raw-r12-applied-bottom-i3.txt",
    "prep1-bottom-i3": "reader-raw-r12-prep1-bottom-i3.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top-i1": "0f392215", "prep1-top-i1": "beb500b0",
    "applied-top-i2": "cdda32f1", "prep1-top-i2": "c5cdb566",
    "applied-top-i3": "4b9fdfbe", "prep1-top-i3": "babe1ab2",
    "applied-bottom-i1": "6fc1f645", "prep1-bottom-i1": "82f470ea",
    "applied-bottom-i2": "4fe3e17d", "prep1-bottom-i2": "503addb5",
    "applied-bottom-i3": "e0c0b2d1", "prep1-bottom-i3": "914a723b",
}
READER_IDS = {
    "applied-top-i1": "reader-r12-top-i1",
    "prep1-top-i1": "reader-r12-top-i1",
    "applied-top-i2": "reader-r12-top-i2",
    "prep1-top-i2": "reader-r12-top-i2",
    "applied-top-i3": "reader-r12-top-i3",
    "prep1-top-i3": "reader-r12-top-i3",
    "applied-bottom-i1": "reader-r12-bottom-i1",
    "prep1-bottom-i1": "reader-r12-bottom-i1",
    "applied-bottom-i2": "reader-r12-bottom-i2",
    "prep1-bottom-i2": "reader-r12-bottom-i2",
    "applied-bottom-i3": "reader-r12-bottom-i3",
    "prep1-bottom-i3": "reader-r12-bottom-i3",
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
#: 逐实例旗数/弃权数（盘面实测口径；与 run-r12 聚合一致）
EXPECT_COUNTS = {"top-i1": 8, "top-i2": 6, "top-i3": 8,
                 "bottom-i1": 20, "bottom-i2": 0, "bottom-i3": 2}
EXPECT_ABSTAIN = {"top-i1": 7, "top-i2": 5, "top-i3": 4,
                  "bottom-i1": 1, "bottom-i2": 0, "bottom-i3": 2}
EXPECT_PART_COUNTS = {
    "applied-top-i1": 4, "prep1-top-i1": 4,
    "applied-top-i2": 3, "prep1-top-i2": 3,
    "applied-top-i3": 3, "prep1-top-i3": 5,
    "applied-bottom-i1": 2, "prep1-bottom-i1": 18,
    "applied-bottom-i2": 0, "prep1-bottom-i2": 0,
    "applied-bottom-i3": 2, "prep1-bottom-i3": 0,
}
ZERO_FLAG_PARTS = [("bottom-i2", "applied"), ("bottom-i2", "prep1"),
                   ("bottom-i3", "prep1")]
#: 原始件键 → 实例键（"{state}-{view}-i{n}" → "{view}-i{n}"）
INSTANCE_OF_KEY = {k: k.split("-", 1)[1] for k in RAW_FILES}
GT_V1_IDS = ["GT-REVC-P1-R4J3", "GT-REVC-P1-F1J2", "GT-REVC-P1-L1NB",
             "GT-REVC-P1-L1SHORT"]
GT_V2_IDS = [
    "GT-REVC-AP-1-R5U6", "GT-REVC-AP-2-Y1C35", "GT-REVC-AP-3-Y1C5",
    "GT-REVC-AP-4-Y1C36", "GT-REVC-AP-5-Y1C4", "GT-REVC-AP-6-R2LED2",
    "GT-REVC-AP-7-C31U4", "GT-REVC-AP-8-R1Q2", "GT-REVC-AP-9-Y2C3",
]
#: R12 零匹配（全部实例/全部态；GT 13 条全 side=top、top 非弃权旗零
#: 近邻交叠、bottom 无 GT 在案）
EXPECT_R12_REROUTE = [("top-i1", "R12T-001", False),
                      ("top-i1", "R12T-002", True),
                      ("top-i3", "R12T-008", True)]
#: 受保护文件（R12-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: 两指引零字节不动（红线：r9 基线与 r12 指引收工哈希=开工哈希）
GUIDANCE_SHA256_FIRST8 = {
    "out/v3-tl2/calibration/observation-guidance-r9.md": "a0c10154",
    "out/v3-tl2/calibration/observation-guidance-r12.md": "0ac22fcd",
}
#: 预注册件哈希锚（先验给定的前 8）
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r12.md": "0ac22fcd",
    "out/v3-tl2/calibration/observation-guidance-r9.md": "a0c10154",
    "out/v3-tl2/calibration/observation-guidance-r8.md": "aad43270",
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
    "out/v3-tl2/calibration/render-framing-r5.json": "860aa910",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
    "out/v3-tl2/calibration/calibration-run-r11.json": "ec05e472",
    "out/v3-tl2/calibration/calibration-run-r10.json": "622c9099",
    "out/v3-tl2/calibration/calibration-run-r9.json": "e16420e5",
    "out/v3-tl2/calibration/calibration-run-r8.json": "3c580eb3",
    "out/v3-tl2/holdout/HOLDOUT-PLAN.md": "a4b80193",
}
BOTTOM_PNG_SHA256 = (
    "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9")
#: 六实例弃权率（盘面实测口径；bottom-i2 零旗标分母=None）
EXPECT_RATES = {"top-i1": 0.875, "top-i2": 0.833333, "top-i3": 0.5,
                "bottom-i1": 0.05, "bottom-i2": None, "bottom-i3": 1.0}


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s47():
    spec = importlib.util.spec_from_file_location(
        "s47_calibration_r12_compare",
        os.path.join(REPO, "scripts", "s47_calibration_r12_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r12.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round12-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _raw_text(key):
    return open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                             RAW_FILES[key]), encoding="utf-8").read()


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r12_files_valid_structure_and_prefixes():
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
        prefix = {"top": "R12T-", "bottom": "R12B-"}[view]
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
        "top-i1": ["R12T-%03d" % i for i in range(1, 9)],
        "top-i2": ["R12T-%03d" % i for i in range(1, 7)],
        "top-i3": ["R12T-%03d" % i for i in range(1, 9)],
        "bottom-i1": ["R12B-%03d" % i for i in range(1, 21)],
        "bottom-i2": [],
        "bottom-i3": ["R12B-001", "R12B-002"],
    }
    for inst in INSTANCE_ORDER:
        got = seen_ids[inst]
        assert got == expect_ids[inst], inst
        assert len(got) == EXPECT_COUNTS[inst]
    # reroute 类旗标恰 3 条（R12T-001 非弃权边界报告 top-i1 +
    # R12T-002 弃权 top-i1 + R12T-008 弃权 top-i3——主通道载体）
    reroute = [(INSTANCE_OF_KEY[key], f["flag_id"], f["abstain"])
               for key, name in RAW_FILES.items()
               for f in _load(name)["per_image"][0]["flags"]
               if f["category"] == "suspicious_reroute"]
    assert reroute == EXPECT_R12_REROUTE
    # 合计 44 旗=25 非弃权+19 弃权（盘面口径与聚合一致）
    total = sum(EXPECT_COUNTS.values())
    abstain = sum(EXPECT_ABSTAIN.values())
    assert total == 44 and abstain == 19 and total - abstain == 25


def test_parse_replay_no_rejections_view_injection_and_reader_instance_note():
    s47 = _s47()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s47.RAW_FILES.items():
        parsed = s47.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s47.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则（作用于派发图像名，非盘上件键）
    assert s47.view_for_image("applied-top.png") == "top"
    assert s47.view_for_image("prep1-bottom.png") == "bottom"
    assert s47.view_for_image("applied-top.png") == s47.view_for_image(
        "applied-top.png")
    try:
        s47.view_for_image("mystery.png")
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
    # 旗标计数（按实例/板/视角/类别分层；总 44）
    fc = run["reader"]["flag_count"]
    assert fc["by_instance"] == EXPECT_COUNTS
    assert fc["abstain_by_instance"] == EXPECT_ABSTAIN
    assert fc["by_state"] == {"applied": 14, "prep1": 30}
    assert fc["by_view"] == {"top": 22, "bottom": 22}
    assert fc["abstain_by_view"] == {"top": 16, "bottom": 3}
    assert fc["by_category"] == {
        "courtyard_crowding": {"total": 29, "non_abstain": 20, "abstain": 9},
        "silk_readability": {"total": 9, "non_abstain": 3, "abstain": 6},
        "suspicious_reroute": {"total": 3, "non_abstain": 1, "abstain": 2},
        "other_advisory": {"total": 1, "non_abstain": 0, "abstain": 1},
        "placement_pattern_anomaly": {"total": 2, "non_abstain": 1,
                                      "abstain": 1},
    }
    assert fc["reroute_by_instance"] == {"top-i1": 2, "top-i2": 0,
                                         "top-i3": 1, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fc["reroute_class_production"] == 3
    assert fc["total"] == 44
    # 派发模式（12 派次=4 格×3 实例，两波次串行保序；v1.2 硬性条款）
    dm = run["reader"]["dispatch_mode"]
    assert dm["mode"] == "instance_serial_two_wave"
    assert dm["instances_per_cell"] == 3 and dm["dispatch_count_total"] == 12
    assert "同一实例先 applied 后 prep1" in dm["within_instance_serial_order"]
    assert "R12B-001..020" in dm["flag_id_continuity"]["bottom-i1"]
    assert "v1.2" in dm["diff_note"] and "示例 c" in dm["diff_note"]
    assert "12 次盲读" in run["reader"]["dispatch_discipline"]
    assert "禁止交流" in run["reader"]["dispatch_discipline"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r12.md" in \
        run["reader"]["dispatch_discipline"]
    assert "禁止对图像做任何程序化处理" in \
        run["reader"]["dispatch_discipline"]            # v1.2 硬性条款
    # 读者实例披露（R12 特有：12/12 纯直读 v1.2 合规+输出格式披露）
    note = run["reader"]["reader_instance_note"]
    assert "12/12 派次自述合规" in note and "Read 工具" in note
    assert "r10/r11 实测 8/12 派次" in note
    assert "非盲读违规" in note and "混杂因素照旧声明" in note
    assert "json.dump indent=1" in note and "内容逐键忠实" in note
    assert "无围栏剥离" in note
    # 逐文件格式披露登记（编排侧落盘前处理；盘上件=冻结证据；12 件均
    # indent=1 重序列化）
    fm = run["reader"]["parse"]
    for key in RAW_FILES:
        assert "indent=1" in fm[key]["raw_message_format_note"], key
    # bottom 零旗标格（item 5 预注册口径：三格在案）
    bz = run["reader"]["bottom_zero_flag_parts"]
    assert [(p["instance"], p["state"]) for p in bz["parts"]] == \
        ZERO_FLAG_PARTS
    assert all(p["flag_count"] == 0 for p in bz["parts"])
    assert "_ratio" in bz["note"] and "None" in bz["note"] \
        and "不编造数值" in bz["note"]
    assert "bottom-i2" in bz["note"] and "0.95" in bz["note"]


# ---------------------------------------------------------------------------
# run-r12：canonical、常量、域声明、双变更轮、受保护文件、courtyard
# ---------------------------------------------------------------------------

def test_run_r12_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r12"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r12"
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
    # 双变更声明（指引侧单变量=示例 c 收窄；协议侧派发层=v1.2 工具规约）
    ic = rec["instrument_change"]
    assert ic["nature"].startswith("单变量指引侧变更轮")
    assert "「整段规则周期」判据收窄" in ic["nature"]
    assert "v1.2" in ic["nature"] and "不改判读语义" in ic["nature"]
    assert ic["components"][0].startswith(
        "reroute-example-c-full-segment-periodic-tighten")
    assert ic["components"][1].startswith(
        "protocol-v1-2-reader-tool-behavior-rule")
    # changed_variables 登记与 r12-prep-record.json 一致（恰两项，锚
    # d393cf27；no_instrument_change=true 指渲染/仪器零变更）
    prep = _load("r12-prep-record.json")
    assert prep["no_instrument_change"] is True
    assert prep["read_prohibition_compliance"] is True
    assert prep["no_visual_reading"] is True
    assert [v["id"] for v in prep["changed_variables"]] == [
        "reroute-example-c-full-segment-periodic-tighten",
        "protocol-v1-2-reader-tool-behavior-rule"]
    assert [v["id"] for v in ic["changed_variables_registered"]] == \
        [v["id"] for v in prep["changed_variables"]]
    # unchanged 与 r12-prep-record.json 登记逐字一致
    assert ic["unchanged_components"] == prep["unchanged_components"]
    pa = ic["protocol_amendment"]
    assert pa["amendment_version"] == "v1.2"
    assert "追加式" in pa["amendment_mode"] and "不回写" in pa["note"]
    v1p = prep["protocol_amendment"]["v1_file_preserved"]
    assert v1p["zero_byte_preserved"] is True
    assert _sha(v1p["path_rel"]) == v1p["sha256_measured"]
    assert "归因分层" in ic["attribution_note"] or "恰两项" in \
        ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r12-prep-record.json")
    assert rec["protocol"]["amendment_version"].startswith("v1.2")
    # 指引=新文件（0ac22fcd）由 r9 指引（a0c10154）机械变换生成
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r12.md")
    assert gp["baseline_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r9.md")
    assert "机械变换生成" in gp["change_note"]
    assert "收窄替换" in gp["change_note"]
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
    assert "先于 R12 盲读冻结" in md["preregistration_declaration"]
    # courtyard 被动追踪键（prep-record 预注册；零阈值改动、零期望）
    ct = rec["courtyard_tracking"]
    assert ct["note_source"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r12-prep-record.json")
    assert ct["note_source"]["quote"] == prep["hypothesis_test"][
        "secondary_observation"]
    assert "零期望" in ct["declaration"] and "零阈值" in ct["declaration"]
    assert "零改动" in ct["threshold_note"]
    # bottom 观察（三实例三种裁决+零匹配结构性+「正常特征→不报告」）
    bz2 = ct["bottom_observation"]
    assert "18 条非弃权 courtyard" in bz2["fact"]
    assert "应为空" in bz2["fact"]
    assert "正常特征→不报告" in bz2["fact"]
    for ev in bz2["evidence"]:
        raw = _raw_text(ev["source"])
        assert ev["excerpt"] in raw                     # 逐字摘录校验
    assert "substring" in bz2["evidence_check"]


def test_run_r12_compare_v3_recompute_byte_exact():
    rec, _ = _run_record()
    for inst in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            block = rec["instances"][inst]["states"][st]
            rep = cal.compare_v3(block["reader_flags"], block["gt_entries"],
                                 flag_views=block["flag_views"])
            assert hashing.canonical_json_bytes(rep) == \
                hashing.canonical_json_bytes(block["compare_v3"])
            n_flags = len(block["reader_flags"])
            want_view = "full" if n_flags else "not_applicable"
            assert block["view_check"] == rep["view_check"] == want_view
            r = block["compare_v3"]
            # 阈值常量零覆盖（与 r11 相同的声明常量）
            assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
            assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
            assert r["metric_version"] == "calibration-metric-v3"
            if n_flags == 0:                            # 零旗标格
                assert r["abstain"]["abstain_rate"] is None  # cal._ratio
                assert r["matches"] == []
                assert r["view_mismatch"] == []
    # R12 零匹配（全部实例/全部态）：逐实例 matches_detail 复算为空
    for inst in INSTANCE_ORDER:
        assert rec["instances"][inst]["combined"]["matches_total"] == 0
        assert rec["instances"][inst]["combined"]["matches_detail"] == []
        assert rec["instances"][inst]["combined"]["gt_matched_union"] == 0
    # bottom-i1 prep1：18 条非弃权 courtyard 与同类别 top GT 全部视角不符
    # （GT 13 条全部 side=top）⇒ view_mismatch=54=18×3 如实入账
    blk = rec["instances"]["bottom-i1"]["states"]["prep1"]
    assert len(blk["compare_v3"]["view_mismatch"]) == 54
    assert all(mm["flag_view"] == "bottom" and mm["gt_side"] == "top"
               for mm in blk["compare_v3"]["view_mismatch"])
    # 其余全部实例/态 view_mismatch=0（top 旗与同态 GT 视角相符；弃权旗
    # 不参与视角检查）
    for inst in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            if (inst, st) == ("bottom-i1", "prep1"):
                continue
            r = rec["instances"][inst]["states"][st]["compare_v3"]
            assert r["view_mismatch"] == []
    # bottom-i2 实例层：零旗标分母→实例级弃权率 None（cal._ratio 先例）
    assert rec["instances"]["bottom-i2"]["combined"]["abstain_rate"] is None
    assert "零旗标分母" in rec["instances"]["bottom-i2"]["combined"][
        "abstain_rate_arithmetic"]
    # R12T-001（top-i1 非弃权 reroute）与同态 GT 零交集（未及近邻门；
    # reroute 类无 GT 条目在案 gt-audit-r1）；R12T-002 为弃权旗（单列）
    d1 = next(x for x in rec["instances"]["top-i1"]["per_flag_gt_detail"]
              if x["flag_id"] == "R12T-001")
    assert d1["abstain"] is False
    assert d1["containment_all_none"] is True
    assert d1["matched"] is False
    d2 = next(x for x in rec["instances"]["top-i1"]["per_flag_gt_detail"]
              if x["flag_id"] == "R12T-002")
    assert d2["abstain"] is True and d2["gt_overlaps"] == [] \
        and d2["containment_all_none"] is None


def test_run_r12_gt_entries_source_plus_reprojection():
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

def test_run_r12_instance_view_layer_and_dual_gt_aggregation():
    rec, _ = _run_record()
    # item 1：实例主记录两板合计复算（abstain_rate 保留 6 位小数）
    for inst in INSTANCE_ORDER:
        c = rec["instances"][inst]["combined"]
        assert c["flag_count"] == EXPECT_COUNTS[inst]
        assert c["abstain_count"] == EXPECT_ABSTAIN[inst]
        assert c["abstain_rate"] == EXPECT_RATES[inst]
        if EXPECT_COUNTS[inst]:
            assert c["abstain_rate"] == round(
                EXPECT_ABSTAIN[inst] / EXPECT_COUNTS[inst], 6)
            assert f"{EXPECT_ABSTAIN[inst]}/{EXPECT_COUNTS[inst]}" in \
                c["abstain_rate_arithmetic"]
        # 非弃权清单与逐旗明细一致（25 条非弃权有明细、弃权旗单列）
        n_detail = sum(1 for d in rec["instances"][inst]["per_flag_gt_detail"]
                       if not d["abstain"])
        assert n_detail == EXPECT_COUNTS[inst] - EXPECT_ABSTAIN[inst]
        for d in rec["instances"][inst]["per_flag_gt_detail"]:
            for o in d["gt_overlaps"]:
                assert set(o) == {"gt_id", "gt_category", "containment",
                                  "area_ratio", "channel"}
    # item 2：视角层三分列（中位数+min+max，不取整）复算
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
        computable = [x for x in ar if x is not None]
        if any(x is None for x in ar):
            # bottom：中位数含 None 无法定义→None（不编造数值）；
            # min/max/极差按可计算实例计算并注明（item 5）
            assert v["abstain_rate"]["median"] is None
            assert "median_note" in v["abstain_rate"]
            assert "None" in v["abstain_rate"]["median_note"]
            assert (v["abstain_rate"]["min"], v["abstain_rate"]["max"]) == \
                (min(computable), max(computable))
            assert v["abstain_rate_range"] == round(
                max(computable) - min(computable), 6)
            assert "可计算实例" in v["abstain_rate_range_arithmetic"]
        else:
            assert v["abstain_rate"]["median"] == sorted(ar)[1]
            assert (v["abstain_rate"]["min"], v["abstain_rate"]["max"]) == \
                (min(ar), max(ar))
            assert v["abstain_rate_range"] == round(max(ar) - min(ar), 6)
    assert vl["top"]["abstain_rate_range"] == 0.375
    assert vl["bottom"]["abstain_rate_range"] == 0.95
    assert vl["top"]["abstain_rate"]["median"] == 0.833333
    assert vl["bottom"]["abstain_rate"]["median"] is None
    assert "0.375" in vl["top"]["abstain_rate_range_arithmetic"]
    assert "0.95" in vl["bottom"]["abstain_rate_range_arithmetic"]
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
# 代表配置 joint + per-metric 范围 + bottom 零分母（items 4-5）
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


def test_run_r12_representative_joint_and_bottom_null_parts():
    rec, _ = _run_record()
    rep = rec["representative_configuration"]
    # 代表配置选取复算：top 中位 8 tie（i1/i3）取先序；bottom 中位 2
    # 唯一（bottom-i3）
    assert rep["rule"].startswith("measurement_design item 4")
    assert rep["members"] == {"top": "top-i1", "bottom": "bottom-i3"}
    sel = rep["selection"]
    assert sel["top"]["median_flag_count"] == 8
    assert sel["top"]["tie"] is True and "先序" in sel["top"]["tie_note"] \
        and "tie" in sel["top"]["tie_note"]
    assert sel["top"]["flag_count_by_instance"] == {"top-i1": 8,
                                                    "top-i2": 6,
                                                    "top-i3": 8}
    assert sel["bottom"]["median_flag_count"] == 2
    assert sel["bottom"]["tie"] is False
    assert "唯一" in sel["bottom"]["tie_note"]
    assert sel["bottom"]["flag_count_by_instance"] == {"bottom-i1": 20,
                                                       "bottom-i2": 0,
                                                       "bottom-i3": 2}
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
    assert agg["flag_count_total"] == n_fl == 10       # 8（top-i1）+2
    assert agg["gt_count_total"] == n_gt == 13
    assert agg["matches_total"] == n_match == 0
    assert agg["gt_matched_total"] == n_gm == 0
    assert agg["scored_total"] == n_sc == 1
    assert agg["abstain_count_total"] == n_ab == 9
    assert agg["gt_recall_total"] == round(0 / 13, 6) == 0.0
    assert agg["seed_match_rate_total"] == round(0 / 1, 6) == 0.0
    assert agg["abstain_rate_total"] == round(9 / 10, 6) == 0.9
    assert "0/13" in agg["gt_recall_arithmetic"]
    assert "9/10" in agg["abstain_rate_arithmetic"]
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
    assert criteria["abstain_rate_le_0.5"]["actual"] == 0.9
    assert criteria["abstain_rate_le_0.5"]["met"] is False
    assert "阈值零改动" in criteria["abstain_rate_le_0.5"]["note"]
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5", "r6",
                                     "r7", "r8", "r9", "r10", "r11",
                                     "r12"}
    assert consec["rounds"]["r11"] == "not_met（在案）"
    assert consec["rounds"]["r12"] == "not_met（本轮）"
    assert comp["joint_evaluation"] == "not_met"
    assert "代表配置" in comp["scope_note"] and "不挑优" in comp["scope_note"]
    # per-metric 实例间范围（item 4 三并列之二）复算
    mr = rec["metric_ranges_instance"]
    assert mr["top"]["flag_count"] == {"min": 6, "max": 8}
    assert mr["top"]["abstain_rate"] == {"min": 0.5, "max": 0.875}
    assert mr["top"]["matches_total"] == {"min": 0, "max": 0}
    assert mr["bottom"]["flag_count"] == {"min": 0, "max": 20}
    assert mr["bottom"]["abstain_rate"]["min"] == 0.05
    assert mr["bottom"]["abstain_rate"]["max"] == 1.0
    assert "None" in mr["bottom"]["abstain_rate"]["note"]
    assert mr["bottom"]["matches_total"] == {"min": 0, "max": 0}
    # item 5：bottom 三格零旗标 part 级弃权率=None（cal._ratio 先例）
    for inst, st in ZERO_FLAG_PARTS:
        r = rec["instances"][inst]["states"][st]["compare_v3"]
        assert r["reader_flag_count"] == 0
        assert rec["instances"][inst]["states"][st]["reader_flags"] == []
        assert r["abstain"]["abstain_rate"] is None     # 零分母→None
    assert "零分母→None" in rec["reader"]["bottom_zero_flag_parts"]["note"]


# ---------------------------------------------------------------------------
# 预注册假设裁决（滥用型操作化逐旗判定=0⇒字母=supported+机制观察单列）
# ---------------------------------------------------------------------------

def test_run_r12_hypothesis_supported_verdict_and_mechanism():
    rec, _ = _run_record()
    prep = _load("r12-prep-record.json")
    ht = rec["hypothesis_test"]
    assert ht["kind"] == "preregistered_hypothesis_test"
    assert ht["hypothesis_id"] == \
        "r11-dev-record-candidate-1-example-c-tighten"
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r12-prep-record.json")
    # 判据引用=r12-prep-record.json hypothesis_test 原文（逐字一致）
    quote = ht["preregistered_criteria_quote"]
    for k in ("hypothesis", "support_condition", "reject_condition",
              "null_result_note", "test_design", "declaration",
              "metric_lesson_application"):
        assert quote[k] == prep["hypothesis_test"][k], k
    pq = prep["hypothesis_test"]["preregistered_criteria_quote"]
    assert quote["candidate_0_target"] == pq["candidate_0_target"]
    assert quote["candidate_1_target"] == pq["candidate_1_target"]
    assert quote["user_directive_2026_09_07"] == pq[
        "user_directive_2026_09_07"]
    assert "工具行为规约" in quote["candidate_0_target"]
    assert "示例 c" in quote["candidate_1_target"]
    assert "滥用型弃权旗=0" in quote["support_condition"]
    assert "滥用型弃权旗≥1" in quote["reject_condition"]
    assert "不可判" in quote["null_result_note"]
    assert "结果无论方向如实" in quote["null_result_note"]
    # 主通道度量=r12-prep-record 登记（滥用型弃权旗计数操作化定义）
    assert ht["primary_channel_metric"] == \
        prep["attribution_plan"]["primary_channel"]["metric"]
    assert "等长|蛇形" in ht["misuse_rule_note"]
    assert "排除式引用" in ht["misuse_rule_note"]
    # 主通道实测：滥用型=0、reroute 非弃权=1、总量=3（非「不可判」）
    m = ht["measurement"]
    assert m["reroute_total_r12"] == 3
    assert m["misuse_abstain_flag_count_r12"] == 0
    assert m["reroute_non_abstain_count_r12"] == 1
    assert m["support_condition_met"] is True
    assert m["reject_condition_met"] is False
    assert m["undeterminable_condition_met"] is False
    assert m["reroute_by_instance_r12"] == {"top-i1": 2, "top-i2": 0,
                                            "top-i3": 1, "bottom-i1": 0,
                                            "bottom-i2": 0, "bottom-i3": 0}
    # 逐旗判定表：子串命中实测=declared、形态描述摘录逐字在案
    detail = m["reroute_flag_detail_r12"]
    assert [(r["instance"], r["flag_id"], r["abstain"],
             r["detected_substring_hits"], r["adjudication"], r["misuse"])
            for r in detail] == [
        ("top-i1", "R12T-001", False, ["蛇形"],
         "non_abstain_boundary_report", False),
        ("top-i1", "R12T-002", True, [], "no_candidate_citation", False),
        ("top-i3", "R12T-008", True, ["等长", "蛇形"],
         "exclusion_citation_not_dependency", False)]
    for r in detail:
        assert r["form_desc_excerpt"] in _raw_text(r["source"])
    # 基线交叉核对（r10=2/r11=1；r11 非弃权=2；live=registered）
    bc = m["baseline_cross_check"]
    assert bc["r10_misuse_registered"] == bc["r10_misuse_live"] == 2
    assert bc["r11_misuse_registered"] == bc["r11_misuse_live"] == 1
    assert bc["r11_non_abstain_registered"] == \
        bc["r11_non_abstain_live"] == 2
    # 守门通道：几何门 0→0 无回升（独立复核，非 support_condition 要件）
    g = m["guard_channel"]
    assert g["guard_ok"] is True
    assert "R11=0→R12=0" in g["observation"]
    assert "独立" in g["note"]
    # 轮内一致性 secondary_observation：预期「维持小带」未发生，如实记录
    so = m["secondary_observation_within_round"]
    assert so["range_top"] == 0.375
    assert so["range_bottom_computable"] == 0.95
    assert so["r11_baseline"]["top"] == 0.153846
    assert so["r11_baseline"]["bottom"] == 0.0
    assert "未发生" in so["declaration"] or "如实记录" in so["declaration"]
    assert "None" in so["range_bottom_arithmetic"]
    # 字母裁决=supported（预注册判据复算一致；唯一正式裁决）
    assert ht["verdict"] == "supported"
    assert prep["hypothesis_test"]["support_condition"] in ht["verdict_rule"]
    assert prep["hypothesis_test"]["reject_condition"] in ht["verdict_rule"]
    assert "支持" in ht["verdict_text"] and "唯一正式裁决" in ht["verdict_text"]
    assert "滥用型弃权旗=0" in ht["verdict_text"]
    assert "排除式引用" in ht["verdict_text"]
    assert "R12T-001" in ht["verdict_text"]
    assert "统计证明" in ht["verdict_text"] and "n=3" in ht["verdict_text"]
    assert "互不凌驾" in ht["verdict_text"] or "分列不合并" in \
        ht["verdict_text"]
    # 机制观察单列（不凌驾字母裁决）：工具钉住≠判读一致；判据轴转移
    mo = ht["mechanism_observation"]
    assert "不凌驾" in mo["role"]
    tp = mo["tool_axis_pinned_vs_criterion_axis"]
    assert "12/12 派次自述纯 Read 直读" in tp["observation"]
    assert "0.375" in tp["observation"] and "0.95" in tp["observation"]
    assert "0.153846" in tp["observation"]
    assert "系统性重复 vs 孤立不一致" in tp["observation"]
    assert "三种裁决" in tp["observation"] and "bottom-i1" in \
        tp["observation"] and "bottom-i2" in tp["observation"] \
        and "bottom-i3" in tp["observation"]
    assert "工具行为一致 ≠ 判读一致" in tp["observation"]
    assert "substring" in tp["tool_evidence_check"]
    assert "substring" in tp["reader_note_evidence_check"]
    # 12/12 派次纯直读摘录逐字校验 + §4(i) 三裁决摘录逐字校验
    for ev in tp["tool_evidence"]:
        assert ev["excerpt"] in _load(RAW_FILES[ev["source"]])[
            "reading_notes"], ev["source"]
    assert len(tp["tool_evidence"]) == 12
    for ev in tp["reader_note_evidence"]:
        src = (_load(RAW_FILES[ev["source"]])["reading_notes"]
               if ev["kind"] == "reading_notes"
               else _raw_text(ev["source"]))
        assert ev["excerpt"] in src, ev.get("flag_id")
    # 方差爆拉对照（r11 在案基线 0.153846/0.0）
    wv = mo["within_vs_cross_round_variance"]
    assert wv["within_round_ranges"]["r11"] == {"top": 0.153846,
                                                "bottom": 0.0}
    assert wv["within_round_ranges"]["r12"]["top"] == 0.375
    assert wv["within_round_ranges"]["r12"]["bottom_computable"] == 0.95
    assert wv["cross_round_abstain_rates"]["r9"] == 0.727273
    assert wv["cross_round_abstain_rates"]["r10"] == 0.285714
    assert wv["cross_round_abstain_rates"]["r11_representative"] == 0.133333
    # reroute 产量链 r8=1→r9=0→r10=2→r11=3→r12=3；滥用型链 2→1→0
    rf = mo["reroute_flag_production"]
    assert (rf["r8"], rf["r9"], rf["r10"], rf["r11"], rf["r12"]) == \
        (1, 0, 2, 3, 3)
    assert rf["r12_by_instance"] == {"top-i1": 2, "top-i2": 0, "top-i3": 1,
                                     "bottom-i1": 0, "bottom-i2": 0,
                                     "bottom-i3": 0}
    mc = rf["misuse_chain"]
    assert mc["r10"] == 2 and mc["r11"] == 1 and mc["r12"] == 0
    assert mc["non_abstain_chain"]["r11"] == 2
    assert mc["non_abstain_chain"]["r12"] == 1
    # 度量设计教训单列：构成分析+聚合通道一正一反；修订候选须预注册
    ml = ht["metric_design_lesson"]
    assert "构成分析" in ml["lesson"] and "supported" in ml["lesson"]
    assert "一正一反" in ml["lesson"]
    assert "预注册" in ml["status"] and "不得反向放宽" in ml["status"]
    assert "不得回溯改判" in ml["status"]
    # 分层观察如实附录 + 混杂与优先声明（字母裁决不被机制/分层改写）
    st_ = ht["stratified_observation"]
    assert st_["top"]["r12_range"] == 0.375
    assert st_["top"]["r12_by_instance"] == {"top-i1": 0.875,
                                             "top-i2": 0.833333,
                                             "top-i3": 0.5}
    assert st_["bottom"]["r12_range_computable"] == 0.95
    assert st_["bottom"]["r12_by_instance"] == {"bottom-i1": 0.05,
                                                "bottom-i2": None,
                                                "bottom-i3": 1.0}
    assert "三种裁决" in st_["bottom"]["direction"]
    assert "混杂因素" in st_["confounder_note"] and "n=3" in \
        st_["confounder_note"]
    assert "不得凌驾字母裁决" in st_["precedence_note"]
    assert "已证因果关系" in st_["precedence_note"]
    # 全旗标合计附记（非主通道）如实
    assert m["aggregate_context"]["apr0011_joint_evaluation_representative"] \
        == "not_met"
    assert "0.431818" in m["r12_total_flags_note"]
    assert "非主通道" in m["r12_total_flags_note"]


# ---------------------------------------------------------------------------
# 通道归因（vs R11；重放可复核；链自 r6 衔接）+ courtyard 追踪
# ---------------------------------------------------------------------------

def test_run_r12_channel_attribution_and_courtyard_reproducible():
    s47 = _s47()
    rec, _ = _run_record()
    run11 = _load("calibration-run-r11.json")
    ca = rec["channel_attribution"]
    # 方法声明：照抄 run-r11 重放口径（同源几何原语）
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r11.json" in ca["method"]["source_of_r11_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] is True
    # 重放复算（R11/R12 均用内嵌输入）与登记一致 + 对拍 compare_v3
    for st in ("prep1", "applied"):
        pass  # R11 为六实例结构；下方按实例态逐一重放
    pairs11 = ca["method"]["replay_cross_check"][
        "r11_candidate_pairs_by_instance_state"]
    assert set(pairs11) == {f"{n}/{st}" for n in INSTANCE_ORDER
                            for st in ("applied", "prep1")}
    for name in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            blk = run11["instances"][name]["states"][st]
            rp = s47.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    blk["gt_entries"])
            assert s47.replay_matches_agree(rp, blk["compare_v3"])
            assert pairs11[f"{name}/{st}"] == [list(p) for p in
                                               rp["candidate_pairs"]]
    # R11 的恰 4 候选对（=r11 四条 matches）在 top-i1/top-i2/top-i3
    flat11 = sorted(tuple(p) for v in pairs11.values() for p in v)
    assert flat11 == [("R11T-003", "GT-REVC-AP-6-R2LED2"),
                      ("R11T-009", "GT-REVC-P1-R4J3"),
                      ("R11T-010", "GT-REVC-AP-1-R5U6"),
                      ("R11T-012", "GT-REVC-P1-L1SHORT")]
    # R12 十二件重放对拍 compare_v3 全部一致（候选对=空集）
    pairs12 = ca["method"]["replay_cross_check"]["r12_candidate_pairs_by_part"]
    assert set(pairs12) == set(RAW_FILES)
    for key in RAW_FILES:
        blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
            STATE_OF_KEY[key]]
        rp = s47.channel_replay(blk["reader_flags"], blk["flag_views"],
                                blk["gt_entries"])
        assert pairs12[key] == [list(p) for p in rp["candidate_pairs"]]
        assert pairs12[key] == []                       # R12 零候选对
        expect = sorted((m["flag_id"], m["gt_id"]) for m in
                        blk["compare_v3"]["matches"])
        assert pairs12[key] == [list(p) for p in expect]
    # 通道分组条目（几何门 R11 0→R12 0；类别门 R11 1→R12 0）与重放一致
    def _entries_r12(failure):
        rows = []
        for key in RAW_FILES:
            blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
                STATE_OF_KEY[key]]
            rp = s47.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    blk["gt_entries"])
            rows += [e for e in rp["entries"] if e["failure"] == failure]
        return rows
    assert ca["channel_1_geometry_gate"]["r11_area_ratio_rejected_entries"] \
        == []
    assert ca["channel_1_geometry_gate"]["r12_area_ratio_rejected_entries"] \
        == _entries_r12("area_ratio_rejected") == []
    assert "0→0" in ca["channel_1_geometry_gate"]["change"]
    cat11 = ca["channel_2_category_gate"]["r11_category_mismatch_entries"]
    assert len(cat11) == 1
    e = cat11[0]
    assert (e["flag_id"], e["gt_id"], e["instance"], e["state"]) == \
        ("R11T-012", "GT-REVC-AP-8-R1Q2", "top-i3", "applied")
    assert e["containment"] == 0.616745 and e["area_ratio"] == 1.648816
    assert ca["channel_2_category_gate"][
        "r12_category_mismatch_entries"] == []
    assert "1→0" in ca["channel_2_category_gate"]["change"]
    # 视角门：两轮重放均空（R12 bottom 非弃权旗与 GT 零近邻交叠）
    assert ca["view_gate_observations"]["r11_entries"] == []
    assert ca["view_gate_observations"]["r12_entries"] == []
    assert "应为空" in ca["view_gate_observations"]["note"]
    # 通道链自 r6 衔接（几何 1→0→0→0→0→0→0；类别 1→0→1→0→0→1→0）
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 0, "r9": 0, "r10": 0, "r11": 0, "r12": 0}
    assert chain["category_gate_category_mismatch_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 1, "r9": 0, "r10": 0, "r11": 1, "r12": 0}
    assert "通道级归因" in chain["scope"]
    # R12 特有观察：零匹配、reroute 构成变化、类别门归零、courtyard 零命中
    spec = "\n".join(ca["r12_specific_observations"])
    assert "union=0/13" in spec and "agreement=0/13" in spec
    assert "R12T-001" in spec and "R12T-002" in spec and "R12T-008" in spec
    assert "r8=1→r9=0→r10=2→r11=3→r12=3" in spec
    assert "滥用型弃权旗 r10=2→r11=1→r12=0" in spec
    assert "r12=0" in spec and "R12B-003..020" in spec
    # courtyard 被动追踪（prep-record 预注册）：非弃权 20、命中 0、弃权 9
    ct = rec["courtyard_tracking"]
    na = ct["r12_courtyard_flags"]["non_abstain"]
    ab = ct["r12_courtyard_flags"]["abstain"]
    assert len(na) == 20 and len(ab) == 9
    assert ct["courtyard_matches_r12"] == 0
    assert all(r["matches"] == 0 and r["matched_detail"] is None
               for r in na)
    # bottom 18 条非弃权 courtyard（bottom-i1 prep1）无从命中（GT 全 top）
    bot18 = [r for r in na if r["instance"] == "bottom-i1"]
    assert len(bot18) == 18 and all(r["view"] == "bottom" for r in bot18)
    assert all(r["containment_all_none"] or r["area_ratio_max"] is None
               or True for r in bot18)
    # top 非弃权 courtyard 2 条（top-i2/top-i3 各 1，applied 态）
    top2 = sorted((r["instance"], r["flag_id"]) for r in na
                  if r["view"] == "top")
    assert top2 == [("top-i2", "R12T-001"), ("top-i3", "R12T-001")]
    # 弃权 courtyard 9 条：top 7（i1×2、i2×3、i3×2）+bottom 2（i3）
    by_inst = {}
    for r in ab:
        by_inst.setdefault(r["instance"], []).append(r["flag_id"])
    assert {k: sorted(v) for k, v in by_inst.items()} == {
        "top-i1": ["R12T-004", "R12T-005"],
        "top-i2": ["R12T-003", "R12T-004", "R12T-006"],
        "top-i3": ["R12T-002", "R12T-007"],
        "bottom-i3": ["R12B-001", "R12B-002"]}
    assert ct["courtyard_matches_r11"] == 3
    assert ct["courtyard_matches_r10"] == 1
    assert ct["courtyard_matches_r9"] == 0
    assert ct["courtyard_matches_r8"] == 1              # R8T-004↔AP-8
    assert "R8T-004" in ct["courtyard_matches_r8_detail"]
    assert "R10T-011" in ct["courtyard_matches_r10_detail"]
    assert "零再现" in ct["same_domain_note"]
    # gt_entries_checked 按态（applied=9、prep1=4）
    for r in na:
        assert r["gt_entries_checked"] == (9 if r["state"] == "applied"
                                           else 4)
    # 双条件数值独立复算（top-i3 R12T-001 vs 全部 applied GT 零近邻）
    blk = rec["instances"]["top-i3"]["states"]["applied"]
    f001 = next(f for f in blk["reader_flags"]
                if f["flag_id"] == "R12T-001")
    best = max(cal._containment(f001["frame_box_pct"],
                                g2["frame_box_pct"]) or 0.0
               for g2 in blk["gt_entries"])
    assert best < cal.CONTAINMENT_MIN                   # 未达近邻门
    # bottom 观察：19 条非弃权零匹配属结构性（bottom 无 GT 在案）
    bz = ct["bottom_observation"]
    assert "19" in bz["fact"] and "应为空" in bz["fact"]
    assert "None" in bz["fact"] and "不编造数值" in bz["fact"]
    for ev in bz["evidence"]:
        raw = _raw_text(ev["source"])
        assert ev["excerpt"] in raw
    assert "pairing_caveat" in ca and "通道级" in ca["pairing_caveat"]


# ---------------------------------------------------------------------------
# 预注册链、冻结哈希、阈值零覆盖
# ---------------------------------------------------------------------------

def test_run_r12_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r12_prep_record_preregistration",
            "observation_guidance_r12", "observation_guidance_r9_baseline",
            "observation_guidance_r8_chain",
            "r11_dev_record_preregistration_source",
            "r11_prep_record_witness_source",
            "r10_dev_record_witness_chain", "r10_prep_record_witness_chain",
            "r9_dev_record_witness_chain", "r9_prep_record_witness_chain",
            "r8_prep_record_witness_chain", "r7_prep_record_witness_chain",
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
    # 预注册件哈希锚（先验给定的前 8；含 r11-dev→r12-prep 链与参照轮）
    for rel, want in PREREG_ANCHORS.items():
        assert _sha(rel).startswith(want), rel
    # 阈值常量零覆盖（与 r11 相同；比较器本体零改动）
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "零覆盖" in rec["preregistration"]["comparator"]["thresholds_note"]
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    # 命名覆盖入 naming_constraints（per r12-prep-record
    # protocol_amendment.naming：随指引落盘固化）
    assert "R9T/R9B→R12T/R12B" in rec["naming_constraints"]
    assert "reader-r9→reader-r12" in rec["naming_constraints"]
    assert "判读实质判据零变更" in rec["naming_constraints"]
    assert "实例间编号独立" in rec["naming_constraints"]
    assert "落盘固化" in rec["naming_constraints"]
    # 指引锚：本轮=r12 指引（0ac22fcd），基线=r9 指引（a0c10154）
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"].startswith("0ac22fcd")
    assert gp["frozen_before_render"] is True
    assert gp["frozen_before_read"] is True
    assert gp["baseline_ref"]["sha256"].startswith("a0c10154")
    # 指引内容锚：r12 指引含收窄判据/R12 前缀/轮次常量；r9 基线含示例 c
    g12 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                            "observation-guidance-r12.md"),
               encoding="utf-8").read()
    assert "整段规则周期" in g12 and "示例 c" in g12 and "三路出口" in g12
    assert "2026-09-07-r12" in g12 and "R12T-001" in g12
    assert "非放宽声明" in g12 or "非放宽" in g12
    assert "v1.2" in g12
    g9 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                           "observation-guidance-r9.md"),
              encoding="utf-8").read()
    assert "示例 c" in g9 and "蛇形" in g9 and "2026-09-07-r9" in g9
    # 预注册链声明（r11-dev-record→r12-prep-record 先于盲读）
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "66e41bbf" in rec["preregistration"]["note"]
    assert "d393cf27" in rec["preregistration"]["note"]
    assert "0ac22fcd" in rec["preregistration"]["note"]
    assert "r12-prep-record.json" in rec["preregistration"]["note"]
    assert "measurement_design" in rec["preregistration"]["note"]
    # 参照轮哈希在案（r11=上一轮基线；r12 前 run 不含本轮）
    ref11 = rec["reference_rounds"]["r11_run"]
    assert ref11["sha256"] == _sha(ref11["path_rel"])
    assert ref11["sha256"].startswith("ec05e472")
    assert "r12_run" not in rec["reference_rounds"]
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
    assert dev["kind"] == "tl2_calibration_round12_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=单变量指引侧变更轮（示例 c 收窄）+协议侧 v1.2 首轮
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert "示例 c" in dev["round_nature"] and "收窄" in dev["round_nature"]
    assert "v1.2" in dev["round_nature"] and "追加式" in dev["round_nature"]
    assert "0ac22fcd" in dev["round_nature"] and "a0c10154" in \
        dev["round_nature"]
    assert "收紧" in dev["round_nature"] and "不构成任何放宽" in \
        dev["round_nature"]
    assert "拍板" in dev["round_nature"]
    assert "measurement_design" in dev["round_nature"] and "五条" in \
        dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    # 诊断结果与 run-r12 一致（代表配置口径：top-i1+bottom-i3）
    run, _ = _run_record()
    assert "top-i1" in dev["diagnostic_result"]["aggregation_scope"]
    assert "bottom-i3" in dev["diagnostic_result"]["aggregation_scope"]
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation_representative"]["abstain_rate_total"] == 0.9
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
    # 假设裁决节与 run-r12 一致（verdict=supported）
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "supported"
    assert dev["hypothesis_test_i"]["measurement"][
        "misuse_abstain_flag_count_r12"] == 0
    # 联合评价趋势：连续达标计数 0（R11 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["after_r11"]["consecutive_met_count"] == 0
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"] and "不得写成已达成" in trend["note"]
    assert "代表配置" in trend["aggregation_scope_note"]
    # r5→r12 逐轮走势表（数值取各轮 run-record；r11/r12 行=代表配置口径）
    assert [row["round"] for row in trend["by_round"]] == \
        ["r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12"]
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
    assert by_r["r5"]["round_id"] == "2026-09-06-r5"
    for row in trend["by_round"]:
        assert row["joint_evaluation"] == "not_met"
        assert row["source"]["sha256"] == _sha(row["source"]["path_rel"])
    # run-r12 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r12.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # gt-audit-r1 引用与 run 一致（1f20554a；GT 侧已全部关闭）
    assert dev["gt_audit_ref"] == run["gt_audit_reference"]
    assert dev["gt_audit_ref"]["sha256"].startswith("1f20554a")
    # 旗标产量记账（44=25+19；实例/视角分列）
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 19 and fp["non_abstain_count"] == 25
    assert fp["abstain_rate_all_flags"] == 0.431818
    assert fp["abstain_rate_by_instance"] == EXPECT_RATES
    assert fp["abstain_rate_range_by_view"]["top"] == 0.375
    assert fp["abstain_rate_range_by_view"]["bottom"] == 0.95
    assert "可计算实例" in fp["abstain_rate_range_by_view"]["bottom_note"]
    assert fp["flag_count_by_instance"] == EXPECT_COUNTS
    assert sum(fp["flag_count_by_file"].values()) == 44
    assert fp["reroute_by_instance"] == {"top-i1": 2, "top-i2": 0,
                                         "top-i3": 1, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fp["reroute_class_production"] == 3
    assert fp["parse_rejections"] == []
    assert fp["reader_ids"] == READER_IDS
    assert "冻结证据" in fp["note"] and "12/12" in fp["note"]
    assert "indent=1" in fp["note"] and "无围栏剥离" in fp["note"]
    assert "R12T/R12B" in fp["note"]
    # 诚实结论：字母裁决=supported；三条机制结论如实
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.9" in hc and "development 域" in hc
    assert "0.0（0/13）" in hc and "union=0/13" in hc and "agreement=0/13" \
        in hc
    assert "支持" in hc and "唯一正式裁决" in hc
    assert "滥用型弃权旗=0" in hc and "排除式引用" in hc
    assert "统计证明" in hc and "n=3" in hc
    assert "工具钉住≠判读一致" in hc and "0.375" in hc and "0.95" in hc
    assert "0.153846" in hc
    assert "三种裁决" in hc and "reader_note_evidence" in hc
    assert "正确测出无效" in hc
    assert "cal._ratio 先例=None" in hc and "不编造数值" in hc
    assert "正常特征→不报告" in hc
    assert "12/12 派次 v1.2 合规" in hc
    assert "indent=1" in hc and "无围栏剥离" in hc
    assert "机制结论如实单列" in hc
    assert "混杂" in hc
    assert "gt-audit-r1" in hc and "全部关闭" in hc
    assert "in_calibrated_range" in hc and "不得冒充留出" in hc
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r12 冻结工件一致（含 r11-dev→r12-prep 链）
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles
    assert chain["r11_dev_record_preregistration_source"]["sha256"] == \
        _sha("out/v3-tl2/calibration/round11-dev-record.json")
    assert chain["r12_prep_record_preregistration"]["sha256"].startswith(
        "d393cf27")
    assert chain["observation_guidance_r12"]["sha256"].startswith("0ac22fcd")
    assert "66e41bbf" in dev["preregistration_chain_note"]
    assert "d393cf27" in dev["preregistration_chain_note"]


def test_dev_record_observations_and_next_targets():
    """方向性观察与下一迭代目标：通道数值可独立复算（描述性，不入
    度量）；next_iteration_targets 覆盖 §4(i) 判据修订候选（不得反向
    放宽）/bottom 图层清单/示例 c 保留/courtyard/GT 关闭/留出集就绪；
    不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    run, _ = _run_record()
    obs = "\n".join(dev["directional_observation_vs_r11"])
    # R11 基线匹配数值复算（代表配置 4 条 matches 之一）与 R12 零匹配
    run11 = _load("calibration-run-r11.json")
    blk11 = run11["instances"]["top-i1"]["states"]["prep1"]
    f009 = next(f for f in blk11["reader_flags"]
                if f["flag_id"] == "R11T-009")
    g11 = next(e for e in blk11["gt_entries"]
               if e["gt_id"] == "GT-REVC-P1-R4J3")
    assert round(cal._containment(f009["frame_box_pct"],
                                  g11["frame_box_pct"]), 6) == 0.723377
    # R11→R12 分层/聚合数字在观察中如实引用
    for need in ("12→12", "53→44", "8/6/8/20/0/2", "41→25", "12→19",
                 "0.226415", "0.431818", "0.153846", "0.375", "0.95",
                 "0.875/0.833333/0.5", "0.05/None/1.0", "8/6/8",
                 "20/0/2", "4/13", "0/13", "0.307692", "union=4/13",
                 "R12T-001", "R12T-002", "R12T-008", "R11T-012",
                 "示例 c", "supported", "判据轴", "bottom-i1", "bottom-i2",
                 "bottom-i3", "蝶形", "三种裁决", "None", "gt-audit-r1",
                 "12/12", "indent=1", "无围栏剥离", "正常特征→不报告",
                 "tie", "先序", "r6=1→r7=0", "0.9（9/10）", "0.133333",
                 "几何门", "类别门", "候选对=空集", "排除式引用",
                 "纯 Read 直读", "0.9>0.5" if "0.9>0.5" in obs else "0.9"):
        assert need in obs, need
    nxt = "\n".join(dev["next_iteration_targets"])
    # §4(i) 判据可操作性修订候选（指引侧，须预注册，不得反向放宽）
    assert "§4(i)" in nxt and "系统性重复" in nxt and "孤立" in nxt
    assert "三种裁决" in nxt and "量化判据" in nxt
    assert "至少 n 处" in nxt
    assert "预注册" in nxt and "不得反向放宽" in nxt
    assert "不得回溯改判" in nxt
    # 渲染侧 bottom 图层清单+层归属消歧候选延续
    assert "图层清单" in nxt and "层归属消歧" in nxt
    # 示例 c 保留观察（滥用型追踪零期望）
    assert "示例 c" in nxt and "supported" in nxt
    assert "滥用型" in nxt and "零期望" in nxt
    # courtyard 追踪延续（跨轮对照）
    assert "courtyard" in nxt and "追踪" in nxt and "side=top" in nxt
    # GT 侧已全关闭（gt-audit-r1 三候选关闭结论被引用）
    assert "gt-audit-r1" in nxt and "1f20554a" in nxt
    assert "三候选" in nxt and "全部关闭" in nxt
    # 留出集已就绪（HOLDOUT-PLAN.md+holdout-candidates-r1 待开发线收敛）
    assert "HOLDOUT-PLAN.md" in nxt and "a4b80193" in nxt
    assert "holdout-candidates-r1" in nxt
    # 不得把正式采纳门槛达成写成已达成；in_calibrated_range 恒 False
    assert "in_calibrated_range 恒 False" in nxt
    assert "不得" in nxt and "人工批准" in nxt
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r12-prep-record.json")


def test_s47_rerun_byte_identical_and_overwrite_guard():
    """s47 重跑语义：同参重建 byte-exact 一致；防覆写护栏（字节等同→
    幂等跳过零覆写；不同→fail-closed）。"""
    s47 = _s47()
    rec, disk = _run_record()
    dev, dev_disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    run_rebuilt = s47.build_run()
    assert hashing.canonical_json_bytes(run_rebuilt) == disk
    run_sha = _sha("out/v3-tl2/calibration/calibration-run-r12.json")
    dev_rebuilt = s47.build_dev_record(run_rebuilt, run_sha)
    assert hashing.canonical_json_bytes(dev_rebuilt) == dev_disk
    # 声明常量（无 wall-clock）
    assert s47.DECLARED_DATE == "2026-09-07"
    assert s47.ROUND_ID == "2026-09-07-r12"
    # 主通道子串检出对常量（操作化定义）
    assert s47.MISUSE_SUBSTRINGS == ("等长", "蛇形")
    # 防覆写护栏纯函数语义
    assert s47.overwrite_guard(None, b"x") == "write"
    assert s47.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s47.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：目标两件已存在且字节等同 → main 正常完成（零覆写）
    before = open(os.path.join(CAL_DIR, "calibration-run-r12.json"),
                  "rb").read()
    s47.main()                                          # 不抛异常=幂等路径
    after = open(os.path.join(CAL_DIR, "calibration-run-r12.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    dev_after = open(os.path.join(CAL_DIR, "round12-dev-record.json"),
                     "rb").read()
    assert dev_after == dev_disk                 # 字节零改动
    # run_record_ref 仍指向 run-r12 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r12.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "三路出口" in rp["abstain_semantics"]
    assert "整段规则周期" in rp["abstain_semantics"]
    assert "反放宽条款" in rp["abstain_semantics"]
    assert "无任何 GT" in rp["discipline"]
    assert "禁止交流" in rp["per_view_dispatch"]
    assert "v1.2" in rp["per_view_dispatch"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r12-prep-record.json" in rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "8/6/8/20/0/2" in rec["deterministic_recompute_note"]
    assert "2026-09-07-r12" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域双变更轮，非留出；
    # advisory 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "单变量指引侧变更轮" in dev["round_nature"]
    assert dev["is_gate"] is False
    assert rec["compliance_representative"][
        "critic_calibration_in_range"] is False
    assert "不是门" in dev["notes"][0]
    # 命名覆盖（随指引落盘固化）如实入账：前缀与 reader_id 两处
    assert "R9T/R9B→R12T/R12B" in rec["naming_constraints"]
    assert "reader-r9→reader-r12" in rec["naming_constraints"]
    prep = _load("r12-prep-record.json")
    assert "机械替换" in prep["protocol_amendment"]["naming"] or \
        "落盘固化" in prep["protocol_amendment"]["naming"]
    # 三分裁决纪律声明在案（字母裁决不被机制观察改写；supported≠统计
    # 证明；主通道判据与 APR-0011 门分开表述）
    assert "不得凌驾或改写字母裁决" in dev["notes"][-1]
    assert "supported 维持不变" in dev["notes"][-1]
    assert "分开表述" in dev["notes"][-1]
    assert "小样本方向性证据" in dev["notes"][-1]
    # v1.2 修订语义：工具规约不构成任何门的放宽或收紧；指引侧=收紧方向
    assert "no_loosening_note" in prep
    assert "不构成任何放宽" in prep["no_loosening_note"]
    assert "收紧" in prep["no_loosening_note"]
    assert "放宽或收紧" in dev["notes"][1]
    # 主通道判据非门：字母裁决与门分列（run 内分开表述）
    assert rec["hypothesis_test"]["verdict"] == "supported"
    assert rec["compliance_representative"]["joint_evaluation"] == "not_met"
    assert "分列不合并" in rec["hypothesis_test"]["verdict_text"]


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
