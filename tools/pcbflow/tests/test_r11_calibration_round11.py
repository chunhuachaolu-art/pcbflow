"""R11 执行包测试：reader 判读迭代第十一轮收口（CAL-R11-CLOSE）——
盲读解析与视角注入（12 派次=4 视角格×3 实例，协议侧 v1.1 单变量轮）
+ 六实例主记录（measurement_design item 1：两板合计
flag_count/abstain_count/abstain_rate/非弃权清单/逐旗明细）+ 视角层
三分列（item 2：中位数+min+max 不取整）+ GT 匹配双口径（item 3：
union/agreement 并列+逐 GT matched_by_count）+ 联合门代表配置与
per-metric 实例间范围并列（item 4）+ bottom 零旗标分母=None
（item 5）+ 预注册假设（r10-dev-record-candidate-0-i-multi-instance）
裁决（字母=reject+强 reject 分层不成立+机制观察单列）+ 逐旗失败通道
归因（vs R10，链自 r6）+ courtyard 被动追踪 + development 域记录。

结构照 test_r10_calibration_round10.py 先例，仅输入与轮次常量不同
（R11=协议侧单变量变更轮：指引 observation-guidance-r9.md 零字节复用
+机械命名覆盖 R9T/R9B→R11T/R11B、reader-r9-*→reader-r11-{top,bottom}-
i{1,2,3}；R5 冻结渲染复用；GT/阈值零变更；唯一操纵=每视角实例数 1→3，
evaluation-protocol-v1→v1.1 追加式修订；预注册于 r11-prep-record.json
（9074df2d），链=r10-dev-record（da4e85f9）→r11-prep-record；检验
r10-dev-record-candidate-0-i-multi-instance，预注册描述性边界
0.2/0.1 只用于本轮假设检验、与 APR-0011 门各自独立计算、互不凌驾）。

覆盖：
- 盲读原文（reader-raw-r11-*.txt 十二件，冻结证据）：合法 JSON、结构
  （reader_id/per_image/reading_notes；flag 六键含 location_evidence）、
  实例内跨板连续编号（R11T/R11B）与实例间独立编号、实例旗数
  13/13/20/2/3/2 与弃权 0/2/3/2/3/2、reroute 恰 3 条全出 top-i3
  （R11T-006 弃权+R11T-018/020 非弃权）、拒收清单固化（53 旗全过
  calibration fail-closed 校验，0 拒收）、哈希与 run-r11 登记一致；
- 视角注入确定性+派发模式（12 派次两波次串行保序）+读者实例披露
  （8/12 派次自述 PIL 局部裁剪放大、4/12 纯直读；输出格式披露：七件
  indent=1 重序列化+一件 Write 原文+四件原样；无围栏剥离本先例记录）；
- calibration-run-r11.json：盘上 canonical byte 一致；逐实例逐态
  compare_v3 用内嵌输入重算 byte-exact 一致（零旗标格
  view_check=not_applicable 不冒充已检查）；内嵌 gt_entries=源 GT 文件
  条目+derivation-log-r5 重投影零新派生；四条 matches 数值独立复算；
  六实例聚合复算（abstain_rate 0.0/0.153846/0.15/1.0/1.0/1.0）；
  视角层三分列复算（top 极差 0.153846/bottom 0.0）；双口径复算
  （union 4/13=0.307692、agreement 0/13=0.0、matched_by_count 全部
  ≤1）；代表配置（top-i1+bottom-i1，双视角 tie 取先序注明）joint
  复算（2/15=0.133333、1/13、1/13；APR-0011 联合 not_met）+per-metric
  范围；bottom 三格零旗标 part 级弃权率=None（cal._ratio 先例）；
- 预注册假设裁决：判据引用=r11-prep-record hypothesis_test 原文
  （support=≥1 视角极差 ≥0.2/reject=全视角 <0.2/强 reject=全视角
  <0.1 原样）；实测 top 0.153846、bottom 0.0⇒verdict=reject（字母
  裁决）且强 reject 分层 claimed=False（top ≥0.1）——「reject，未达
  强 reject」；0.2/0.1 与 APR-0011 门独立分列；机制观察单列（轮内
  方差≪跨轮摆动 0.222222→0.727273→0.285714 vs 0.153846/0.0；示例 c
  双向效应 R11T-018/020 非弃权 vs r10 弃权+R11T-006 仍弃权；reroute
  逐实例 0/0/3；摘录逐字 substring 校验）；守门通道 guard_ok；
- 通道归因（vs R10）：重放对拍十二件全部复现；几何门 0→0（无回升）、
  类别门 0→1（R11T-012↔AP-8 containment 0.616745/面积比 1.648816）、
  视角门 0→0；链自 r6（几何 1→0→0→0→0→0；类别 1→0→1→0→0→1）；
  courtyard 追踪：非弃权 14 条、命中 3 条（R11T-009↔R4J3 0.723377/
  0.734272、R11T-010↔AP-1 0.927745/1.75184、R11T-003↔AP-6 0.689959/
  1.10596，与 r8/r10 同域）、弃权 3 条（bottom）；匹配 r8=1→r9=0→
  r10=1→r11=3；
- 预注册链：r10-dev-record（da4e85f9）→r11-prep-record（9074df2d）→
  run-r11 链含哈希；guidance-r9 零字节复用（a0c10154）/r8 基线/
  framing-r5/derivation-log-r5/GT/协议 v1 零字节保留（22dc7337）/
  复用 PNG/冻结 PDF sha 与盘上一致；阈值常量零覆盖（containment 0.5 /
  area_ratio_max 10.0 与 r10 相同）；gt-audit-r1 引用（1f20554a）；
- round11-dev-record.json：域声明、协议侧单变量轮性质（v1.1 首轮+
  user_directive 两项拍板）、假设裁决节与 run-r11 一致、R10→R11
  方向性观察（派次 4→12、旗标 14→53、双口径/代表配置三口径并列首次
  落地）、联合评价趋势（r5→r11 逐轮表、连续计数 0→0；r11 行=代表
  配置口径并列注明）、run-r11 sha 引用一致、next_iteration_targets
  覆盖跨轮可比性协议候选（固定工具行为规约/固定混合配比，须预注册）/
  示例 c 措辞修改 R12（user_directive）/渲染侧 bottom 图层清单延续/
  courtyard 追踪延续/GT 侧已全关闭声明延续/留出集 TBD、is_gate=False、
  in_calibrated_range 恒 False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；机械命名覆盖 R11T/R11B 入
  naming_constraints；受保护三文件 sha256 前 8 断言；
- s45 重跑：同参重建 byte-exact 一致 + 防覆写护栏语义（字节等同→
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

ROUND_ID = "2026-09-07-r11"
DECLARED_DATE = "2026-09-07"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")
RAW_FILES = {
    "applied-top-i1": "reader-raw-r11-applied-top-i1.txt",
    "prep1-top-i1": "reader-raw-r11-prep1-top-i1.txt",
    "applied-top-i2": "reader-raw-r11-applied-top-i2.txt",
    "prep1-top-i2": "reader-raw-r11-prep1-top-i2.txt",
    "applied-top-i3": "reader-raw-r11-applied-top-i3.txt",
    "prep1-top-i3": "reader-raw-r11-prep1-top-i3.txt",
    "applied-bottom-i1": "reader-raw-r11-applied-bottom-i1.txt",
    "prep1-bottom-i1": "reader-raw-r11-prep1-bottom-i1.txt",
    "applied-bottom-i2": "reader-raw-r11-applied-bottom-i2.txt",
    "prep1-bottom-i2": "reader-raw-r11-prep1-bottom-i2.txt",
    "applied-bottom-i3": "reader-raw-r11-applied-bottom-i3.txt",
    "prep1-bottom-i3": "reader-raw-r11-prep1-bottom-i3.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top-i1": "e9432d3e", "prep1-top-i1": "d3c114bc",
    "applied-top-i2": "1046144f", "prep1-top-i2": "fd93e23d",
    "applied-top-i3": "2fdc8646", "prep1-top-i3": "cf805295",
    "applied-bottom-i1": "242ab86f", "prep1-bottom-i1": "820798d4",
    "applied-bottom-i2": "6fd7a21c", "prep1-bottom-i2": "7b0b4b21",
    "applied-bottom-i3": "f98bf0c2", "prep1-bottom-i3": "0282fab7",
}
READER_IDS = {
    "applied-top-i1": "reader-r11-top-i1",
    "prep1-top-i1": "reader-r11-top-i1",
    "applied-top-i2": "reader-r11-top-i2",
    "prep1-top-i2": "reader-r11-top-i2",
    "applied-top-i3": "reader-r11-top-i3",
    "prep1-top-i3": "reader-r11-top-i3",
    "applied-bottom-i1": "reader-r11-bottom-i1",
    "prep1-bottom-i1": "reader-r11-bottom-i1",
    "applied-bottom-i2": "reader-r11-bottom-i2",
    "prep1-bottom-i2": "reader-r11-bottom-i2",
    "applied-bottom-i3": "reader-r11-bottom-i3",
    "prep1-bottom-i3": "reader-r11-bottom-i3",
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
#: 逐实例旗数/弃权数（盘面实测口径；与 run-r11 聚合一致）
EXPECT_COUNTS = {"top-i1": 13, "top-i2": 13, "top-i3": 20,
                 "bottom-i1": 2, "bottom-i2": 3, "bottom-i3": 2}
EXPECT_ABSTAIN = {"top-i1": 0, "top-i2": 2, "top-i3": 3,
                  "bottom-i1": 2, "bottom-i2": 3, "bottom-i3": 2}
EXPECT_PART_COUNTS = {
    "applied-top-i1": 6, "prep1-top-i1": 7,
    "applied-top-i2": 5, "prep1-top-i2": 8,
    "applied-top-i3": 12, "prep1-top-i3": 8,
    "applied-bottom-i1": 0, "prep1-bottom-i1": 2,
    "applied-bottom-i2": 3, "prep1-bottom-i2": 0,
    "applied-bottom-i3": 2, "prep1-bottom-i3": 0,
}
ZERO_FLAG_PARTS = [("bottom-i1", "applied"), ("bottom-i2", "prep1"),
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
#: 四条 matches（逐实例逐态；数值=独立复算锚）
EXPECT_MATCHES = [
    ("top-i1", "prep1", "R11T-009", "GT-REVC-P1-R4J3", 0.723377, 0.734272),
    ("top-i2", "prep1", "R11T-012", "GT-REVC-P1-L1SHORT", 1.0, 1.756578),
    ("top-i3", "applied", "R11T-003", "GT-REVC-AP-6-R2LED2", 0.689959,
     1.10596),
    ("top-i3", "applied", "R11T-010", "GT-REVC-AP-1-R5U6", 0.927745,
     1.75184),
]
#: 受保护文件（R11-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: 预注册件哈希锚（先验给定的前 8）
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r9.md": "a0c10154",
    "out/v3-tl2/calibration/r11-prep-record.json": "9074df2d",
    "out/v3-tl2/calibration/round10-dev-record.json": "da4e85f9",
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
    "out/v3-tl2/calibration/calibration-run-r10.json": "622c9099",
    "out/v3-tl2/calibration/calibration-run-r9.json": "e16420e5",
    "out/v3-tl2/calibration/calibration-run-r8.json": "3c580eb3",
}
BOTTOM_PNG_SHA256 = (
    "f87f8fec299460962886b646ea692fb567d011fc313031e9b83a0f098983a6a9")


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s45():
    spec = importlib.util.spec_from_file_location(
        "s45_calibration_r11_compare",
        os.path.join(REPO, "scripts", "s45_calibration_r11_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r11.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round11-dev-record.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


# ---------------------------------------------------------------------------
# 盲读原文（冻结证据）合法性与结构
# ---------------------------------------------------------------------------

def test_reader_raw_r11_files_valid_structure_and_prefixes():
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
        prefix = {"top": "R11T-", "bottom": "R11B-"}[view]
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
        "top-i1": ["R11T-%03d" % i for i in range(1, 14)],
        "top-i2": ["R11T-%03d" % i for i in range(1, 14)],
        "top-i3": ["R11T-%03d" % i for i in range(1, 21)],
        "bottom-i1": ["R11B-001", "R11B-002"],
        "bottom-i2": ["R11B-001", "R11B-002", "R11B-003"],
        "bottom-i3": ["R11B-001", "R11B-002"],
    }
    for inst in INSTANCE_ORDER:
        got = seen_ids[inst]
        assert got == expect_ids[inst], inst
        assert len(got) == EXPECT_COUNTS[inst]
    # reroute 类旗标恰 3 条、全部出自 top-i3（R11T-006 弃权 +
    # R11T-018/020 非弃权——示例 c 双向效应载体）
    reroute = [(INSTANCE_OF_KEY[key], f["flag_id"], f["abstain"])
               for key, name in RAW_FILES.items()
               for f in _load(name)["per_image"][0]["flags"]
               if f["category"] == "suspicious_reroute"]
    assert reroute == [("top-i3", "R11T-006", True),
                       ("top-i3", "R11T-018", False),
                       ("top-i3", "R11T-020", False)]
    # 合计 53 旗=41 非弃权+12 弃权（盘面口径与聚合一致）
    total = sum(EXPECT_COUNTS.values())
    abstain = sum(EXPECT_ABSTAIN.values())
    assert total == 53 and abstain == 12 and total - abstain == 41


def test_parse_replay_no_rejections_view_injection_and_reader_instance_note():
    s45 = _s45()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s45.RAW_FILES.items():
        parsed = s45.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s45.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则（作用于派发图像名，非盘上件键）
    assert s45.view_for_image("applied-top.png") == "top"
    assert s45.view_for_image("prep1-bottom.png") == "bottom"
    assert s45.view_for_image("applied-top.png") == s45.view_for_image(
        "applied-top.png")
    try:
        s45.view_for_image("mystery.png")
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
    # 旗标计数（按实例/板/视角/类别分层；总 53）
    fc = run["reader"]["flag_count"]
    assert fc["by_instance"] == EXPECT_COUNTS
    assert fc["abstain_by_instance"] == EXPECT_ABSTAIN
    assert fc["by_state"] == {"applied": 28, "prep1": 25}
    assert fc["by_view"] == {"top": 46, "bottom": 7}
    assert fc["abstain_by_view"] == {"top": 5, "bottom": 7}
    assert fc["reroute_by_instance"] == {"top-i1": 0, "top-i2": 0,
                                         "top-i3": 3, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fc["reroute_class_production"] == 3
    assert fc["total"] == 53
    # 派发模式（协议侧 v1.1：12 派次=4 格×3 实例，两波次串行保序）
    dm = run["reader"]["dispatch_mode"]
    assert dm["mode"] == "instance_serial_two_wave"
    assert dm["instances_per_cell"] == 3 and dm["dispatch_count_total"] == 12
    assert "同一实例先 applied 后 prep1" in dm["within_instance_serial_order"]
    assert "R11T-001..020" in dm["flag_id_continuity"]["top-i3"]
    assert "唯一变更变量" in dm["diff_note"] and "R9T/R9B→R11T/R11B" \
        in dm["diff_note"]
    assert "12 次盲读" in run["reader"]["dispatch_discipline"]
    assert "禁止交流" in run["reader"]["dispatch_discipline"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r9.md" in \
        run["reader"]["dispatch_discipline"]
    # 读者实例披露（R11 特有：工具行为异质性+输出格式披露，如实入账）
    note = run["reader"]["reader_instance_note"]
    assert "Read 工具直读" in note and "非 URL 转传" in note
    assert "8/12 派次" in note and "4/12 派次" in note
    assert "PIL" in note and "2-25 处不等" in note
    assert "applied-top-i1 第一派次最重" in note and "连通域" in note
    assert "applied-bottom-i1/i2/i3、prep1-bottom-i3" in note
    assert "非盲读违规" in note and "混杂因素照旧声明" in note
    assert "json.dump indent=1" in note and "内容逐键忠实" in note
    assert "Write 原文落盘" in note and "原样落盘" in note
    assert "无围栏剥离本先例记录" in note and "r7/r10" in note
    # 逐文件格式披露登记（编排侧落盘前处理；盘上件=冻结证据）
    fm = run["reader"]["parse"]
    assert "紧凑单行" in fm["applied-top-i1"]["raw_message_format_note"]
    assert "indent=1" in fm["prep1-top-i1"]["raw_message_format_note"]
    assert "indent=1" in fm["applied-bottom-i2"]["raw_message_format_note"]
    assert "多行缩进" in fm["prep1-bottom-i1"]["raw_message_format_note"] \
        and "Write 原文" in fm["prep1-bottom-i1"]["raw_message_format_note"]
    # bottom 零旗标格（item 5 预注册口径：三格在案）
    bz = run["reader"]["bottom_zero_flag_parts"]
    assert [(p["instance"], p["state"]) for p in bz["parts"]] == \
        ZERO_FLAG_PARTS
    assert all(p["flag_count"] == 0 for p in bz["parts"])
    assert "_ratio" in bz["note"] and "None" in bz["note"] \
        and "不编造数值" in bz["note"]


# ---------------------------------------------------------------------------
# run-r11：canonical、常量、域声明、协议侧单变量轮、受保护文件、courtyard
# ---------------------------------------------------------------------------

def test_run_r11_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r11"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r11"
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
    # 协议侧单变量变更声明（唯一变更变量=每视角实例数 1→3；v1.1 追加式）
    ic = rec["instrument_change"]
    assert ic["nature"].startswith("协议侧单变量变更轮")
    assert "每视角独立 reader 实例数 1→3" in ic["nature"]
    assert ic["components"] == ["per-view-instance-count-1-to-3（协议侧唯一"
                                "操纵；非指引/渲染/GT/阈值变更）"]
    # unchanged 与 r11-prep-record.json 登记逐字一致（锚 9074df2d）
    prep = _load("r11-prep-record.json")
    assert ic["unchanged_components"] == prep["unchanged_components"]
    assert prep["no_instrument_change"] is True
    assert prep["changed_variables"] == []
    assert prep["renders_reuse"]["no_instrument_change"] is True
    pa = ic["protocol_amendment"]
    assert pa["amendment_version"] == "v1.1"
    assert "追加式" in pa["amendment_mode"] and "不回写" in pa["note"]
    v1p = prep["protocol_amendment"]["v1_file_preserved"]
    assert v1p["zero_byte_preserved"] is True
    assert _sha(v1p["path_rel"]) == v1p["sha256_measured"]
    assert "每视角独立实例数 1→3" in ic["attribution_note"]
    assert "互不凌驾" in ic["attribution_note"]
    assert "reader_instance_note" in ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r11-prep-record.json")
    assert rec["protocol"]["amendment_version"].startswith("v1.1")
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
    assert "已全部关闭" in ref["note"]                  # GT 侧候选关闭声明
    # 受保护三文件零改动（sha256 前 8）
    for rel, want in PROTECTED_SHA256_FIRST8.items():
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
    assert "先于 R11 盲读冻结" in md["preregistration_declaration"]
    # courtyard 被动追踪键（prep-record 预注册；零阈值改动、零期望）
    ct = rec["courtyard_tracking"]
    assert ct["note_source"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r11-prep-record.json")
    assert ct["note_source"]["quote"] == prep["hypothesis_test"][
        "secondary_observation"]
    assert "零期望" in ct["declaration"] and "零阈值" in ct["declaration"]
    assert "零改动" in ct["threshold_note"]
    # bottom 全弃权观察（「正常特征→不报告」通道继续使用）
    bz2 = ct["bottom_observation"]
    assert "7 旗" in bz2["fact"] and "全部弃权" in bz2["fact"]
    assert "正常特征→不报告" in bz2["fact"]
    for ev in bz2["evidence"]:
        raw = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                                RAW_FILES[ev["source"]]),
                   encoding="utf-8").read()
        assert ev["excerpt"] in raw                     # 逐字摘录校验
    assert "substring" in bz2["evidence_check"]


def test_run_r11_compare_v3_recompute_byte_exact():
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
            # 阈值常量零覆盖（与 r10 相同的声明常量）
            assert r["containment_min"] == cal.CONTAINMENT_MIN == 0.5
            assert r["area_ratio_max"] == cal.AREA_RATIO_MAX == 10.0
            assert r["metric_version"] == "calibration-metric-v3"
            if n_flags == 0:                            # 零旗标格
                assert r["abstain"]["abstain_rate"] is None  # cal._ratio
                assert r["matches"] == []
    # 四条 matches（逐实例逐态；数值锚）
    got_matches = []
    for inst in INSTANCE_ORDER:
        for m in rec["instances"][inst]["combined"]["matches_detail"]:
            got_matches.append((inst, m["state"], m["flag_id"], m["gt_id"],
                                m["containment"], m["area_ratio"]))
    assert sorted(got_matches) == sorted(EXPECT_MATCHES)
    assert rec["instances"]["top-i1"]["combined"]["matches_total"] == 1
    assert rec["instances"]["top-i2"]["combined"]["matches_total"] == 1
    assert rec["instances"]["top-i3"]["combined"]["matches_total"] == 2
    for inst in ("bottom-i1", "bottom-i2", "bottom-i3"):
        assert rec["instances"][inst]["combined"]["matches_total"] == 0
    # bottom 零非弃权旗：全部旗标在 abstain_ids、零 matches、零候选
    for inst in ("bottom-i1", "bottom-i2", "bottom-i3"):
        c = rec["instances"][inst]["combined"]
        assert len(c["abstain_ids"]) == c["flag_count"]
        assert c["non_abstain_flag_ids"] == []
    # 视角门零条目：bottom 全弃权、top 旗与全 top GT 无视角不符
    for inst in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            assert rec["instances"][inst]["states"][st]["compare_v3"][
                "view_mismatch"] == []
    # R11T-018/020（非弃权 reroute）与同态 GT 零交集（未及近邻门）
    for fid in ("R11T-018", "R11T-020"):
        d = next(x for x in rec["instances"]["top-i3"]["per_flag_gt_detail"]
                 if x["flag_id"] == fid)
        assert d["abstain"] is False and d["containment_all_none"] is True
        assert d["matched"] is False


def test_run_r11_gt_entries_source_plus_reprojection():
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

def test_run_r11_instance_view_layer_and_dual_gt_aggregation():
    rec, _ = _run_record()
    # item 1：实例主记录两板合计复算（abstain_rate 保留 6 位小数）
    expect_rates = {"top-i1": 0.0, "top-i2": 0.153846, "top-i3": 0.15,
                    "bottom-i1": 1.0, "bottom-i2": 1.0, "bottom-i3": 1.0}
    for inst in INSTANCE_ORDER:
        c = rec["instances"][inst]["combined"]
        assert c["flag_count"] == EXPECT_COUNTS[inst]
        assert c["abstain_count"] == EXPECT_ABSTAIN[inst]
        assert c["abstain_rate"] == expect_rates[inst]
        assert c["abstain_rate"] == round(
            EXPECT_ABSTAIN[inst] / EXPECT_COUNTS[inst], 6)
        assert f"{EXPECT_ABSTAIN[inst]}/{EXPECT_COUNTS[inst]}" in \
            c["abstain_rate_arithmetic"]
        assert c["gt_matched_union"] == len(
            {m["gt_id"] for m in c["matches_detail"]})
        # 非弃权清单与逐旗明细一致（41 条非弃权有明细、弃权旗单列）
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
                        ("bottom", ("bottom-i1", "bottom-i2", "bottom-i3"))):
        v = vl[view]
        assert v["instances"] == list(names)
        fc = [EXPECT_COUNTS[n] for n in names]
        ar = [expect_rates[n] for n in names]
        mt = [rec["instances"][n]["combined"]["matches_total"]
              for n in names]
        assert v["flag_count"]["median"] == sorted(fc)[1]
        assert (v["flag_count"]["min"], v["flag_count"]["max"]) == \
            (min(fc), max(fc))
        assert v["abstain_rate"]["median"] == sorted(ar)[1]
        assert (v["abstain_rate"]["min"], v["abstain_rate"]["max"]) == \
            (min(ar), max(ar))
        assert v["matches"]["median"] == sorted(mt)[1]
        assert (v["matches"]["min"], v["matches"]["max"]) == (min(mt),
                                                              max(mt))
        assert v["abstain_rate_range"] == round(max(ar) - min(ar), 6)
    assert vl["top"]["abstain_rate_range"] == 0.153846
    assert vl["bottom"]["abstain_rate_range"] == 0.0
    assert "0.153846" in vl["top"]["abstain_rate_range_arithmetic"]
    # item 3：GT 匹配双口径复算（union ≥1 / agreement ≥2/3；分母 13）
    dual = rec["gt_match_dual"]
    assert dual["denominator"] == 13
    per_gt = {g["gt_id"]: g for g in dual["per_gt"]}
    assert len(per_gt) == 13
    # 逐 GT matched_by_count 从实例 matches_detail 独立归并复算
    recount = {gid: 0 for gid in per_gt}
    for inst in INSTANCE_ORDER:
        for m in rec["instances"][inst]["combined"]["matches_detail"]:
            recount[m["gt_id"]] += 1
    for gid, g in per_gt.items():
        assert g["matched_by_count"] == recount[gid], gid
        assert len(g["hits"]) == g["matched_by_count"]
    hit_gts = ["GT-REVC-AP-1-R5U6", "GT-REVC-AP-6-R2LED2",
               "GT-REVC-P1-R4J3", "GT-REVC-P1-L1SHORT"]
    assert all(per_gt[g]["matched_by_count"] == 1 for g in hit_gts)
    assert all(per_gt[g]["matched_by_count"] == 0
               for g in per_gt if g not in hit_gts)
    assert dual["union"]["rule"] == "≥1 实例命中即计"
    assert dual["agreement"]["rule"] == "≥2/3 实例命中才计"
    assert dual["union"]["gt_ids"] == hit_gts
    assert dual["union"]["count"] == 4
    assert dual["union"]["gt_recall_union"] == round(4 / 13, 6) == 0.307692
    assert dual["agreement"]["gt_ids"] == [] and \
        dual["agreement"]["count"] == 0
    assert dual["agreement"]["gt_recall_agreement"] == 0.0


# ---------------------------------------------------------------------------
# 代表配置 joint + per-metric 范围 + bottom 零分母（items 4-5）
# ---------------------------------------------------------------------------

def test_run_r11_representative_joint_and_bottom_null_parts():
    rec, _ = _run_record()
    rep = rec["representative_configuration"]
    # 代表配置选取复算：每视角 flag_count 中位数实例；tie 取先序并注明
    assert rep["rule"].startswith("measurement_design item 4")
    assert rep["members"] == {"top": "top-i1", "bottom": "bottom-i1"}
    sel = rep["selection"]
    assert sel["top"]["median_flag_count"] == 13
    assert sel["top"]["tie"] is True and "先序" in sel["top"]["tie_note"] \
        and "tie" in sel["top"]["tie_note"]
    assert sel["top"]["flag_count_by_instance"] == {"top-i1": 13,
                                                    "top-i2": 13,
                                                    "top-i3": 20}
    assert sel["bottom"]["median_flag_count"] == 2
    assert sel["bottom"]["tie"] is True and "先序" in \
        sel["bottom"]["tie_note"]
    assert sel["bottom"]["flag_count_by_instance"] == {"bottom-i1": 2,
                                                       "bottom-i2": 3,
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
    assert agg["flag_count_total"] == n_fl == 15       # 13（top-i1）+2
    assert agg["gt_count_total"] == n_gt == 13
    assert agg["matches_total"] == n_match == 1
    assert agg["gt_matched_total"] == n_gm == 1
    assert agg["scored_total"] == n_sc == 13
    assert agg["abstain_count_total"] == n_ab == 2
    assert agg["gt_recall_total"] == round(1 / 13, 6) == 0.076923
    assert agg["seed_match_rate_total"] == round(1 / 13, 6) == 0.076923
    assert agg["abstain_rate_total"] == round(2 / 15, 6) == 0.133333
    assert "1/13" in agg["gt_recall_arithmetic"]
    assert "2/15" in agg["abstain_rate_arithmetic"]
    assert agg["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert "代表配置" in agg["scope"] and "不挑优" in agg["scope"]
    # APR-0011 达标评估逐项复算（阈值零改动；联合 not_met）
    comp = rec["compliance_representative"]
    criteria = {c["id"]: c for c in comp["criteria"]}
    assert criteria["gt_count_ge_12"]["actual"] == 13
    assert criteria["gt_count_ge_12"]["met"] is True
    assert criteria["gt_recall_ge_0.75"]["actual"] == 0.076923
    assert criteria["gt_recall_ge_0.75"]["met"] is False
    assert criteria["seed_match_rate_ge_0.5"]["actual"] == 0.076923
    assert criteria["seed_match_rate_ge_0.5"]["met"] is False
    assert criteria["abstain_rate_le_0.5"]["actual"] == 0.133333
    assert criteria["abstain_rate_le_0.5"]["met"] is True
    assert "阈值零改动" in criteria["abstain_rate_le_0.5"]["note"]
    assert "禁称 precision/FPR" in \
        criteria["seed_match_rate_ge_0.5"]["note"]
    consec = comp["consecutive_rounds"]
    assert consec["required"] == 2
    assert consec["consecutive_met_count"] == 0 and consec["met"] is False
    assert set(consec["rounds"]) == {"r1", "r2", "r3", "r4", "r5", "r6",
                                     "r7", "r8", "r9", "r10", "r11"}
    assert consec["rounds"]["r10"] == "not_met（在案）"
    assert consec["rounds"]["r11"] == "not_met（本轮）"
    assert comp["joint_evaluation"] == "not_met"
    assert "代表配置" in comp["scope_note"] and "不挑优" in comp["scope_note"]
    # per-metric 实例间范围（item 4 三并列之二）复算
    mr = rec["metric_ranges_instance"]
    assert mr["top"]["flag_count"] == {"min": 13, "max": 20}
    assert mr["top"]["abstain_rate"] == {"min": 0.0, "max": 0.153846}
    assert mr["top"]["matches_total"] == {"min": 1, "max": 2}
    assert mr["bottom"]["flag_count"] == {"min": 2, "max": 3}
    assert mr["bottom"]["abstain_rate"] == {"min": 1.0, "max": 1.0}
    assert mr["bottom"]["matches_total"] == {"min": 0, "max": 0}
    # item 5：bottom 三格零旗标 part 级弃权率=None（cal._ratio 先例）
    for inst, st in ZERO_FLAG_PARTS:
        r = rec["instances"][inst]["states"][st]["compare_v3"]
        assert r["reader_flag_count"] == 0
        assert rec["instances"][inst]["states"][st]["reader_flags"] == []
        assert r["abstain"]["abstain_rate"] is None     # 零分母→None
    assert "零分母→None" in rec["reader"]["bottom_zero_flag_parts"]["note"]


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


# ---------------------------------------------------------------------------
# 预注册假设裁决（字母=reject+强 reject 分层+机制观察单列）
# ---------------------------------------------------------------------------

def test_run_r11_hypothesis_reject_verdict_and_mechanism():
    rec, _ = _run_record()
    prep = _load("r11-prep-record.json")
    ht = rec["hypothesis_test"]
    assert ht["kind"] == "preregistered_hypothesis_test"
    assert ht["hypothesis_id"] == "r10-dev-record-candidate-0-i-multi-instance"
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r11-prep-record.json")
    # 判据引用=r11-prep-record.json hypothesis_test 原文（逐字一致）
    quote = ht["preregistered_criteria_quote"]
    for k in ("hypothesis", "support_condition", "reject_condition",
              "test_design", "null_result_note", "secondary_observation"):
        assert quote[k] == prep["hypothesis_test"][k], k
    pq = prep["hypothesis_test"]["preregistered_criteria_quote"]
    assert quote["candidate_0_target"] == pq["candidate_0_target"]
    assert quote["user_directive_2026_09_07"] == pq[
        "user_directive_2026_09_07"]
    assert "多实例重复读" in quote["candidate_0_target"]
    assert "示例 c 措辞修改排程 R12" in quote["user_directive_2026_09_07"]
    assert "≥0.2" in quote["support_condition"]
    assert "<0.2" in quote["reject_condition"]
    assert "<0.1" in quote["reject_condition"] and "强 reject" in \
        quote["reject_condition"]
    assert "正确测出无效同样是有效证据" in quote["null_result_note"]
    assert "互不凌驾" in quote["null_result_note"]
    # 主通道度量=r11-prep-record 登记（实例间弃权率极差+0.2/0.1 边界）
    assert ht["primary_channel_metric"] == \
        prep["attribution_plan"]["primary_channel"]["metric"]
    # 实测：r8/r9/r10 基线与在案 run 交叉一致；本轮六实例弃权率+极差
    m = ht["measurement"]
    assert m["abstain_rate_r8"] == 0.222222
    assert m["abstain_rate_r9"] == 0.727273
    assert m["abstain_rate_r10"] == 0.285714
    assert m["abstain_rate_r11_by_instance"] == {
        "top-i1": 0.0, "top-i2": 0.153846, "top-i3": 0.15,
        "bottom-i1": 1.0, "bottom-i2": 1.0, "bottom-i3": 1.0}
    assert m["abstain_rate_r11_by_instance_fraction"]["top-i2"] == "2/13"
    assert m["range_top"] == 0.153846 and m["range_bottom"] == 0.0
    assert m["verdict_boundary_support"] == 0.2
    assert m["verdict_boundary_strong_reject"] == 0.1
    assert m["support_condition_met"] is False
    assert m["strong_reject_condition_met"] is False
    assert "attribution_plan" in m["boundary_source"]
    # 边界与 APR-0011 门独立分列（互不凌驾；not_met 与 reject 不合并）
    assert "互不凌驾" in m["boundary_independence_note"]
    assert "not_met" in m["boundary_independence_note"]
    assert "reject" in m["boundary_independence_note"]
    assert "非 CONTAINMENT_MIN" in m["boundary_independence_note"] or \
        "非 APR-0011 门" in m["boundary_independence_note"]
    # 守门通道：几何门 0→0 无回升（独立复核，非 support_condition 要件）
    g = m["guard_channel"]
    assert g["guard_ok"] is True
    assert "R10=0→R11=0" in g["observation"]
    assert "独立" in g["note"]
    # reroute 类逐实例产量对照（prep-record secondary_observation 预注册）
    rso = m["reroute_secondary_observation"]
    assert rso["reroute_production_r8"] == 1
    assert rso["reroute_production_r9"] == 0
    assert rso["reroute_production_r10"] == 2
    assert rso["reroute_production_r11"] == 3
    assert "0/0/3" in rso["declaration"]
    # 字母裁决=拒绝（预注册判据复算一致；唯一正式裁决）+强 reject 不成立
    assert ht["verdict"] == "reject"
    assert prep["hypothesis_test"]["support_condition"] in ht["verdict_rule"]
    assert prep["hypothesis_test"]["reject_condition"] in ht["verdict_rule"]
    assert "拒绝" in ht["verdict_text"] and "唯一正式裁决" in ht["verdict_text"]
    assert "0.153846" in ht["verdict_text"] and "0.0" in ht["verdict_text"]
    assert "小样本方向性证据" in ht["verdict_text"]
    sr = ht["strong_reject_stratification"]
    assert sr["claimed"] is False
    assert "未达强 reject" in ht["verdict_text"]
    assert "top 极差 0.153846≥0.1" in sr["note"]
    assert "不因 bottom 极差 0.0<0.1" in sr["note"]
    assert "方向性" in ht["verdict_text"] and "统计证明" in ht["verdict_text"]
    # 机制观察单列（不凌驾字母裁决）：轮内方差≪跨轮摆动
    mo = ht["mechanism_observation"]
    assert "不凌驾" in mo["role"]
    wv = mo["within_vs_cross_round_variance"]
    assert "远小于" in wv["observation"] and "0.222222" in wv["observation"]
    assert "0.727273" in wv["observation"] and "0.285714" in wv["observation"]
    assert "0.153846" in wv["observation"]
    assert "跨轮（实例群/工具代际）因素主导" in wv["observation"]
    assert "轮内同日采样相对稳定" in wv["observation"]
    assert "正确测出无效同样是有效证据" in wv["observation"]
    assert "收窄" in wv["status"] and "置信带" in wv["status"]
    assert "三口径并列首次落地" in wv["status"]
    # 示例 c 双向效应：top i3 非弃权 reroute vs r10 弃权；R11T-006 仍弃权
    ec = mo["example_c_bidirectional_effect"]
    assert "随实例而异" in ec["observation"] and "R11T-018/020" in \
        ec["observation"] and "R11T-006" in ec["observation"]
    assert "R12" in ec["observation"] and "零指引" in ec["observation"]
    assert ec["r10_contrast_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r10.json")
    assert "弃权路径" in ec["r10_contrast_ref"]["summary"]
    # 摘录逐字来自对应 reader-raw（防转述失真）
    raws = {k: open(os.path.join(REPO, "out", "v3-tl2", "calibration", v),
                    encoding="utf-8").read() for k, v in RAW_FILES.items()}
    for ev in ec["evidence"]:
        assert ev["excerpt"] in raws[ev["source"]], ev.get("flag_id")
    for ev in mo["tool_behavior_evidence"]:
        assert ev["excerpt"] in raws[ev["source"]], ev["source"]
    assert "substring" in ec["evidence_check"]
    # reroute 产量独立复算：r11=3 全出 top-i3（0/0/3）；r9=0；r8=1
    r11_reroute = sorted(
        (d["flag_id"], d["abstain"])
        for n in INSTANCE_ORDER
        for d in rec["instances"][n]["per_flag_gt_detail"]
        if d["category"] == "suspicious_reroute")
    assert r11_reroute == [("R11T-006", True), ("R11T-018", False),
                           ("R11T-020", False)]
    run9 = _load("calibration-run-r9.json")
    assert [f["flag_id"] for st in ("prep1", "applied")
            for f in run9["states"][st]["reader_flags"]
            if f["category"] == "suspicious_reroute"] == []
    run8 = _load("calibration-run-r8.json")
    assert [f["flag_id"] for st in ("prep1", "applied")
            for f in run8["states"][st]["reader_flags"]
            if f["category"] == "suspicious_reroute"] == ["R8T-014"]
    # 工具行为混杂（8/12 PIL vs 4/12 纯直读）如实入账
    tb = mo["tool_behavior_note"]
    assert "8/12" in tb and "4/12" in tb and "PIL" in tb
    assert "混杂因素" in tb and "预注册" in tb
    # 度量设计教训单列：跨轮因素主导；候选须预注册、不回溯改判
    ml = ht["metric_design_lesson"]
    assert "极差" in ml["lesson"] and "0.153846" in ml["lesson"]
    assert "跨轮因素" in ml["lesson"]
    assert "预注册" in ml["status"] and "不得回溯改判" in ml["status"]
    assert "reject 维持" in ml["status"]
    # 分层观察如实附录 + 混杂与优先声明（字母裁决不被机制/分层改写）
    st_ = ht["stratified_observation"]
    assert st_["top"]["r10_rate"] == 0.285714
    assert st_["top"]["r11_range"] == 0.153846
    assert st_["bottom"]["r10_rate"] is None
    assert st_["bottom"]["r10_fraction"] == "0/0"
    assert st_["bottom"]["r11_range"] == 0.0
    assert "实例间范围" in st_["top"]["direction"]
    assert "混杂因素" in st_["confounder_note"] and "PIL" in \
        st_["confounder_note"]
    assert "不得凌驾字母裁决" in st_["precedence_note"]
    assert "已证因果关系" in st_["precedence_note"]
    # 全旗标合计附记（非主通道）如实
    assert m["aggregate_context"]["apr0011_joint_evaluation_representative"] \
        == "not_met"
    assert "0.226415" in m["r11_total_flags_note"]
    assert "非主通道" in m["r11_total_flags_note"]


# ---------------------------------------------------------------------------
# 通道归因（vs R10；重放可复核；链自 r6 衔接）+ courtyard 追踪
# ---------------------------------------------------------------------------

def test_run_r11_channel_attribution_and_courtyard_reproducible():
    s45 = _s45()
    rec, _ = _run_record()
    run10 = _load("calibration-run-r10.json")
    ca = rec["channel_attribution"]
    # 方法声明：照抄 run-r10 重放口径（同源几何原语）
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r10.json" in ca["method"]["source_of_r10_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] is True
    # 重放复算（R10/R11 均用内嵌输入）与登记一致 + 对拍 compare_v3
    for run_doc, tag in ((run10, "r10"),):
        for st in ("prep1", "applied"):
            blk = run_doc["states"][st]
            rp = s45.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    blk["gt_entries"])
            assert s45.replay_matches_agree(rp, blk["compare_v3"])
            pairs = ca["method"]["replay_cross_check"][
                f"{tag}_{st}_candidate_pairs"]
            assert pairs == [list(p) for p in rp["candidate_pairs"]]
    assert ca["method"]["replay_cross_check"]["r10_prep1_candidate_pairs"] \
        == [["R10T-011", "GT-REVC-P1-R4J3"]]
    assert ca["method"]["replay_cross_check"]["r10_applied_candidate_pairs"] \
        == []
    # R11 十二件重放对拍 compare_v3 全部一致（候选对=各实例 matches）
    pairs_by_part = ca["method"]["replay_cross_check"][
        "r11_candidate_pairs_by_part"]
    assert set(pairs_by_part) == set(RAW_FILES)
    for key in RAW_FILES:
        blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
            STATE_OF_KEY[key]]
        rp = s45.channel_replay(blk["reader_flags"], blk["flag_views"],
                                blk["gt_entries"])
        assert pairs_by_part[key] == [list(p) for p in rp["candidate_pairs"]]
        expect = sorted((m["flag_id"], m["gt_id"]) for m in
                        blk["compare_v3"]["matches"])
        assert pairs_by_part[key] == [list(p) for p in expect]
    # 通道分组条目（几何门 R10 0→R11 0；类别门 R10 0→R11 1）与重放一致
    def _entries_r11(failure):
        rows = []
        for key in RAW_FILES:
            blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
                STATE_OF_KEY[key]]
            rp = s45.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    blk["gt_entries"])
            rows += [e for e in rp["entries"] if e["failure"] == failure]
        return rows
    assert ca["channel_1_geometry_gate"]["r10_area_ratio_rejected_entries"] \
        == []
    assert ca["channel_1_geometry_gate"]["r11_area_ratio_rejected_entries"] \
        == _entries_r11("area_ratio_rejected") == []
    assert "0→0" in ca["channel_1_geometry_gate"]["change"]
    cat11 = ca["channel_2_category_gate"]["r11_category_mismatch_entries"]
    assert len(cat11) == 1
    e = cat11[0]
    assert (e["flag_id"], e["gt_id"], e["instance"], e["state"]) == \
        ("R11T-012", "GT-REVC-AP-8-R1Q2", "top-i3", "applied")
    assert e["containment"] == 0.616745 and e["area_ratio"] == 1.648816
    assert e["category"] == "silk_readability"
    assert e["gt_category"] == "courtyard_crowding"
    assert ca["channel_2_category_gate"][
        "r10_category_mismatch_entries"] == []
    assert "0→1" in ca["channel_2_category_gate"]["change"]
    assert "0.616745" in ca["channel_2_category_gate"]["change"]
    # 视角门：两轮重放均空（bottom 7 旗全弃权=零非弃权 bottom 旗）
    assert ca["view_gate_observations"]["r10_entries"] == []
    assert ca["view_gate_observations"]["r11_entries"] == []
    assert "全部弃权" in ca["view_gate_observations"]["note"]
    # 通道链自 r6 衔接（几何 1→0→0→0→0→0；类别 1→0→1→0→0→1）
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 0, "r9": 0, "r10": 0, "r11": 0}
    assert chain["category_gate_category_mismatch_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 1, "r9": 0, "r10": 0, "r11": 1}
    assert "通道级归因" in chain["scope"]
    # R11 特有观察：四条命中、reroute 0/0/3、类别门 1 条、courtyard 3 命中
    spec = "\n".join(ca["r11_specific_observations"])
    assert "R11T-009" in spec and "0.723377" in spec
    assert "R11T-012" in spec and "L1SHORT" in spec
    assert "R11T-010" in spec and "R11T-003" in spec
    assert "union=4/13" in spec and "agreement=" in spec
    assert "0/0/3" in spec and "R11T-018" in spec
    assert "matched_by_count" in spec
    # courtyard 被动追踪（prep-record 预注册）：非弃权 14、命中 3、弃权 3
    ct = rec["courtyard_tracking"]
    na = ct["r11_courtyard_flags"]["non_abstain"]
    ab = ct["r11_courtyard_flags"]["abstain"]
    assert len(na) == 14 and len(ab) == 3
    # 排序=（实例，旗号）：bottom-i2 的 R11B-003 在 bottom-i3 两旗之前
    assert [(r["instance"], r["flag_id"]) for r in ab] == [
        ("bottom-i2", "R11B-003"), ("bottom-i3", "R11B-001"),
        ("bottom-i3", "R11B-002")]
    assert {r["instance"] for r in ab} == {"bottom-i2", "bottom-i3"}
    hits = [r for r in na if r["matches"]]
    assert sorted(r["flag_id"] for r in hits) == ["R11T-003", "R11T-009",
                                                  "R11T-010"]
    by_fid = {r["flag_id"]: r for r in hits}
    assert by_fid["R11T-009"]["matched_detail"] == {
        "gt_id": "GT-REVC-P1-R4J3", "state": "prep1",
        "containment": 0.723377, "area_ratio": 0.734272}
    assert by_fid["R11T-010"]["matched_detail"] == {
        "gt_id": "GT-REVC-AP-1-R5U6", "state": "applied",
        "containment": 0.927745, "area_ratio": 1.75184}
    assert by_fid["R11T-003"]["matched_detail"] == {
        "gt_id": "GT-REVC-AP-6-R2LED2", "state": "applied",
        "containment": 0.689959, "area_ratio": 1.10596}
    # gt_entries_checked 按态（applied=9、prep1=4）；非命中旗如实分列：
    # 部分为零交集（containment_all_none），部分仅低于近邻门的局部交叠
    # （未成匹配，非阈值问题；阈值常量零改动）
    for r in na:
        assert r["gt_entries_checked"] == (9 if r["state"] == "applied"
                                           else 4)
        if not r["matches"]:
            assert r["matched_detail"] is None
    zero_overlap = [r["flag_id"] for r in na if r["containment_all_none"]]
    assert sorted(zero_overlap) == ["R11T-010", "R11T-011", "R11T-015",
                                    "R11T-017"]
    assert ct["courtyard_matches_r11"] == 3
    assert ct["courtyard_matches_r10"] == 1
    assert ct["courtyard_matches_r9"] == 0
    assert ct["courtyard_matches_r8"] == 1              # R8T-004↔AP-8
    assert "R8T-004" in ct["courtyard_matches_r8_detail"]
    assert "R10T-011" in ct["courtyard_matches_r10_detail"]
    assert "同域" in ct["same_domain_note"]
    # 双条件数值独立复算（R11T-009 vs R4J3）
    blk = rec["instances"]["top-i1"]["states"]["prep1"]
    f009 = next(f for f in blk["reader_flags"]
                if f["flag_id"] == "R11T-009")
    g = next(e for e in blk["gt_entries"]
             if e["gt_id"] == "GT-REVC-P1-R4J3")
    assert round(cal._containment(f009["frame_box_pct"],
                                  g["frame_box_pct"]), 6) == 0.723377
    assert round(cal._area_ratio(f009["frame_box_pct"],
                                 g["frame_box_pct"]), 6) == 0.734272
    # bottom 观察：7 旗全弃权=零非弃权旗（「正常特征→不报告」继续使用）
    bz = ct["bottom_observation"]
    assert "7 旗" in bz["fact"] and "非弃权旗=0、matches=0" in bz["fact"]
    for ev in bz["evidence"]:
        raw = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                                RAW_FILES[ev["source"]]),
                   encoding="utf-8").read()
        assert ev["excerpt"] in raw
    assert "pairing_caveat" in ca and "通道级" in ca["pairing_caveat"]


# ---------------------------------------------------------------------------
# 预注册链、冻结哈希、阈值零覆盖
# ---------------------------------------------------------------------------

def test_run_r11_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r11_prep_record_preregistration",
            "observation_guidance_r9_zero_byte_reuse",
            "observation_guidance_r8_baseline",
            "r10_dev_record_preregistration_source",
            "r10_prep_record_witness_source",
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
    # 预注册件哈希锚（先验给定的前 8；含 r10-dev→r11-prep 链与参照轮）
    for rel, want in PREREG_ANCHORS.items():
        assert _sha(rel).startswith(want), rel
    # 阈值常量零覆盖（与 r10 相同；比较器本体零改动）
    assert rec["preregistration"]["comparator"]["thresholds"] == {
        "containment_min": 0.5, "area_ratio_max": 10.0}
    assert cal.CONTAINMENT_MIN == 0.5 and cal.AREA_RATIO_MAX == 10.0
    assert rec["preregistration"]["comparator"]["sha256_first8"] == \
        _sha("pcbflow/calibration.py")[:8] == "dac80b7e"
    assert "零覆盖" in rec["preregistration"]["comparator"]["thresholds_note"]
    assert "禁称" in rec["naming_constraints"]
    assert "不构成电气事实" in rec["coverage_caveat"]
    # 机械命名覆盖入 naming_constraints（per r11-prep-record guidance_reuse）
    assert "R9T/R9B→R11T/R11B" in rec["naming_constraints"]
    assert "reader-r9-*→reader-r11-{top,bottom}-i{1,2,3}" in \
        rec["naming_constraints"]
    assert "判读实质判据零变更" in rec["naming_constraints"]
    assert "实例间编号独立" in rec["naming_constraints"]
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
    assert "R12" in gp["change_note"]                   # 示例 c 排程披露
    # 指引内容锚：复用的 r9 指引含示例 c/三路出口/非放宽（零字节复用）
    g9 = open(os.path.join(REPO, "out", "v3-tl2", "calibration",
                           "observation-guidance-r9.md"),
              encoding="utf-8").read()
    assert "示例 c" in g9 and "蛇形" in g9 and "三路出口" in g9
    assert "2026-09-07-r9" in g9 and "非放宽" in g9
    # 预注册链声明（r10-dev-record→r11-prep-record 先于盲读）
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "da4e85f9" in rec["preregistration"]["note"]
    assert "9074df2d" in rec["preregistration"]["note"]
    assert "r11-prep-record.json" in rec["preregistration"]["note"]
    assert "measurement_design" in rec["preregistration"]["note"]
    # 参照轮哈希在案（r10=上一轮基线；r11 前 run 不含本轮）
    ref10 = rec["reference_rounds"]["r10_run"]
    assert ref10["sha256"] == _sha(ref10["path_rel"])
    assert ref10["sha256"].startswith("622c9099")
    assert "r11_run" not in rec["reference_rounds"]
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
    assert dev["kind"] == "tl2_calibration_round11_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=协议侧单变量变更轮（v1.1 首轮；唯一操纵=实例数 1→3）
    assert "协议侧单变量变更轮" in dev["round_nature"]
    assert "v1.1" in dev["round_nature"] and "追加式" in dev["round_nature"]
    assert "每视角独立 reader 实例数 1→3" in dev["round_nature"]
    assert "零字节复用" in dev["round_nature"]
    assert "0.2/0.1" in dev["round_nature"] and "互不凌驾" in \
        dev["round_nature"]
    assert "user_directive" in dev["round_nature"] or "拍板" in \
        dev["round_nature"]
    assert "measurement_design" in dev["round_nature"] and "五条" in \
        dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert dev["instrument_change"]["nature"].startswith("协议侧单变量变更轮")
    # 诊断结果与 run-r11 一致（代表配置口径）
    run, _ = _run_record()
    assert dev["diagnostic_result"]["aggregation_scope"] == \
        "representative_configuration（top-i1+bottom-i1，" \
        "measurement_design item 4）"
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation_representative"]["abstain_rate_total"] == 0.133333
    assert dev["diagnostic_result"]["gt_recall_total"] == \
        run["aggregation_representative"]["gt_recall_total"] == 0.076923
    assert dev["diagnostic_result"]["seed_match_rate_total"] == \
        run["aggregation_representative"]["seed_match_rate_total"] == \
        0.076923
    assert dev["diagnostic_result"]["seed_metric_note"] == cal.SEED_METRIC_NOTE
    assert dev["diagnostic_result"]["gt_match_dual"] == {
        "union": run["gt_match_dual"]["union"],
        "agreement": run["gt_match_dual"]["agreement"]}
    crit = {c["id"]: c for c in dev["diagnostic_result"]["criteria"]}
    assert crit["gt_count_ge_12"]["met"] is True
    assert crit["gt_recall_ge_0.75"]["met"] is False
    assert crit["seed_match_rate_ge_0.5"]["met"] is False
    assert crit["abstain_rate_le_0.5"]["met"] is True
    # 假设裁决节与 run-r11 一致（verdict=reject；强 reject 不成立）
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "reject"
    assert dev["hypothesis_test_i"]["strong_reject_stratification"][
        "claimed"] is False
    # 联合评价趋势：连续达标计数 0（R10 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["after_r10"]["consecutive_met_count"] == 0
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"] and "不得写成已达成" in trend["note"]
    assert "代表配置" in trend["aggregation_scope_note"]
    # r5→r11 逐轮走势表（数值取各轮 run-record；r11 行=代表配置口径）
    assert [row["round"] for row in trend["by_round"]] == \
        ["r5", "r6", "r7", "r8", "r9", "r10", "r11"]
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
    assert by_r["r5"]["round_id"] == "2026-09-06-r5"
    for row in trend["by_round"]:
        assert row["joint_evaluation"] == "not_met"
        assert row["source"]["sha256"] == _sha(row["source"]["path_rel"])
    # run-r11 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r11.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # gt-audit-r1 引用与 run 一致（1f20554a；GT 侧已全部关闭）
    assert dev["gt_audit_ref"] == run["gt_audit_reference"]
    assert dev["gt_audit_ref"]["sha256"].startswith("1f20554a")
    # 旗标产量记账（53=41+12；实例/视角分列）
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 12 and fp["non_abstain_count"] == 41
    assert fp["abstain_rate_all_flags"] == 0.226415
    assert fp["abstain_rate_by_instance"] == {
        "top-i1": 0.0, "top-i2": 0.153846, "top-i3": 0.15,
        "bottom-i1": 1.0, "bottom-i2": 1.0, "bottom-i3": 1.0}
    assert fp["abstain_rate_range_by_view"] == {"top": 0.153846,
                                                "bottom": 0.0}
    assert fp["flag_count_by_instance"] == EXPECT_COUNTS
    assert sum(fp["flag_count_by_file"].values()) == 53
    assert fp["reroute_by_instance"] == {"top-i1": 0, "top-i2": 0,
                                         "top-i3": 3, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fp["reroute_class_production"] == 3
    assert fp["parse_rejections"] == []
    assert fp["reader_ids"] == READER_IDS
    assert "冻结证据" in fp["note"] and "PIL" in fp["note"]
    assert "indent=1" in fp["note"] and "无围栏剥离" in fp["note"]
    assert "R11T/R11B" in fp["note"]
    # 诚实结论：字母裁决=reject（未达强 reject）；三条机制结论如实
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.133333" in hc and "development 域" in hc
    assert "0.076923" in hc and "0.307692" in hc and "4/13" in hc
    assert "0/13" in hc
    assert "拒绝" in hc and "唯一正式裁决" in hc
    assert "未达强 reject" in hc and "0.153846≥0.1" in hc
    assert "远小于" in hc and "收窄" in hc and "工具代际" in hc
    assert "正确测出无效" in hc and "有信息量的负结果" in hc
    assert "示例 c 效果随实例而异" in hc and "R11T-018/020" in hc
    assert "R12" in hc
    assert "union=4/13" in hc and "agreement=0/13" in hc
    assert "三口径并列" in hc and "置信带" in hc
    assert "matched_by_count 全部 ≤1" in hc
    assert "cal._ratio 先例=None" in hc and "不编造数值" in hc
    assert "正常特征→不报告" in hc
    assert "8/12 派次 PIL" in hc and "4/12 纯直读" in hc
    assert "indent=1" in hc and "无围栏剥离" in hc
    assert "机制结论如实单列" in hc
    assert "混杂" in hc
    assert "gt-audit-r1" in hc and "全部关闭" in hc
    assert "in_calibrated_range" in hc and "不得冒充留出" in hc
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r11 冻结工件一致（含 r10-dev→r11-prep 链）
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles
    assert chain["r10_dev_record_preregistration_source"]["sha256"] == \
        _sha("out/v3-tl2/calibration/round10-dev-record.json")
    assert chain["r11_prep_record_preregistration"]["sha256"].startswith(
        "9074df2d")
    assert "da4e85f9" in dev["preregistration_chain_note"]
    assert "9074df2d" in dev["preregistration_chain_note"]


def test_dev_record_observations_and_next_targets_cite_gt_audit():
    """方向性观察与下一迭代目标：通道数值可独立复算（描述性，不入
    度量）；gt-audit-r1 结论被 next_iteration_targets 引用（GT 侧已
    全部关闭）；不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    run, _ = _run_record()
    obs = "\n".join(dev["directional_observation_vs_r10"])
    # R10 基线匹配数值复算（单实例口径）与 R11 命中复算
    run10 = _load("calibration-run-r10.json")
    blk10 = run10["states"]["prep1"]
    f011 = next(f for f in blk10["reader_flags"]
                if f["flag_id"] == "R10T-011")
    g10 = next(e for e in blk10["gt_entries"]
               if e["gt_id"] == "GT-REVC-P1-R4J3")
    assert round(cal._containment(f011["frame_box_pct"],
                                  g10["frame_box_pct"]), 6) == 0.829864
    # R10→R11 分层/聚合数字在观察中如实引用
    for need in ("4→12", "14→53", "13/13/20/2/3/2", "0.285714",
                 "0.226415", "0.153846", "0.133333", "2/15",
                 "0.307692", "0.076923", "R11T-009", "R11T-012",
                 "R11T-010", "R11T-003", "union=4/13", "agreement=0/13",
                 "0.616745", "1.648816", "0.723377", "0.927745",
                 "0.689959", "r11=3", "R11T-018", "R11T-020",
                 "示例 c", "强 reject", "跨轮", "PIL", "8/12", "4/12",
                 "indent=1", "Write 原文", "无围栏剥离", "正常特征→不报告",
                 "None", "tie", "先序", "r6=1→r7=0", "matched_by_count"):
        assert need in obs, need
    nxt = "\n".join(dev["next_iteration_targets"])
    # 跨轮可比性协议候选（协议侧，须预注册）：固定工具行为规约/固定配比
    assert "跨轮可比性协议候选" in nxt and "0.153846" in nxt
    assert "0.222222" in nxt and "0.727273" in nxt
    assert "PIL" in nxt and "8/12" in nxt and "4/12" in nxt
    assert "固定" in nxt and "混合配比" in nxt
    assert "预注册" in nxt and "不得回溯改判" in nxt
    # 示例 c 措辞修改（R12 指引侧，用户已拍板，引 user_directive）
    assert "示例 c" in nxt and "R12" in nxt
    assert "user_directive" in nxt and "双向效应" in nxt
    # 渲染侧 bottom 图层清单候选延续
    assert "图层清单" in nxt
    # courtyard 追踪延续（跨轮复现）
    assert "courtyard" in nxt and "追踪" in nxt and "同域" in nxt
    # GT 侧已全关闭（gt-audit-r1 三候选关闭结论被引用）
    assert "gt-audit-r1" in nxt and "1f20554a" in nxt
    assert "三候选" in nxt and "全部关闭" in nxt
    # 不得把正式采纳门槛达成写成已达成；in_calibrated_range 恒 False
    assert "in_calibrated_range 恒 False" in nxt
    assert "不得" in nxt and "TBD" in nxt
    assert dev["instrument_change"]["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r11-prep-record.json")


def test_s45_rerun_byte_identical_and_overwrite_guard():
    """s45 重跑语义：同参重建 byte-exact 一致；防覆写护栏（字节等同→
    幂等跳过零覆写；不同→fail-closed）。"""
    s45 = _s45()
    rec, disk = _run_record()
    dev, dev_disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    run_rebuilt = s45.build_run()
    assert hashing.canonical_json_bytes(run_rebuilt) == disk
    run_sha = _sha("out/v3-tl2/calibration/calibration-run-r11.json")
    dev_rebuilt = s45.build_dev_record(run_rebuilt, run_sha)
    assert hashing.canonical_json_bytes(dev_rebuilt) == dev_disk
    # 声明常量（无 wall-clock）
    assert s45.DECLARED_DATE == "2026-09-07"
    assert s45.ROUND_ID == "2026-09-07-r11"
    # 预注册描述性边界常量（只用于假设检验，与门分列）
    assert s45.BOUNDARY_SUPPORT == 0.2
    assert s45.BOUNDARY_STRONG_REJECT == 0.1
    # 防覆写护栏纯函数语义
    assert s45.overwrite_guard(None, b"x") == "write"
    assert s45.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s45.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：目标两件已存在且字节等同 → main 正常完成（零覆写）
    before = open(os.path.join(CAL_DIR, "calibration-run-r11.json"),
                  "rb").read()
    s45.main()                                          # 不抛异常=幂等路径
    after = open(os.path.join(CAL_DIR, "calibration-run-r11.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    dev_after = open(os.path.join(CAL_DIR, "round11-dev-record.json"),
                     "rb").read()
    assert dev_after == dev_disk                 # 字节零改动
    # run_record_ref 仍指向 run-r11 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r11.json")


def test_naming_constraints_recursive_and_no_gate_semantics():
    rec, _ = _run_record()
    dev, _ = _run_dev_record()
    for doc in (rec, dev):
        _assert_no_banned_keys(doc)                     # 递归查越界命名
    rp = rec["preregistration"]["reader_protocol"]
    assert "五键" in rp["keys"] and "location_evidence" in rp["keys"]
    assert "三路出口" in rp["abstain_semantics"]
    assert "示例 c" in rp["abstain_semantics"]
    assert "R12" in rp["abstain_semantics"]
    assert "无任何 GT" in rp["discipline"]
    assert "禁止交流" in rp["per_view_dispatch"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r11-prep-record.json" in rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "13/13/20/2/3/2" in rec["deterministic_recompute_note"]
    assert "2026-09-07-r11" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域协议侧单变量轮，非留出；
    # advisory 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "协议侧单变量变更轮" in dev["round_nature"]
    assert dev["is_gate"] is False
    assert rec["compliance_representative"][
        "critic_calibration_in_range"] is False
    assert "不是门" in dev["notes"][0]
    # 机械命名覆盖（guidance_reuse）如实入账：前缀与 reader_id 两处
    assert "R9T/R9B→R11T/R11B" in rec["naming_constraints"]
    assert "reader-r9-*→reader-r11-{top,bottom}-i{1,2,3}" in \
        rec["naming_constraints"]
    prep = _load("r11-prep-record.json")
    assert prep["guidance_reuse"]["mechanical_naming_override"] in \
        rec["naming_constraints"] or ("机械替换" in rec["naming_constraints"]
                                      and "判读实质判据零变更" in
                                      rec["naming_constraints"])
    # 三分裁决纪律声明在案（字母裁决不被强 reject 分层/机制观察改写；
    # reject≠统计证伪；0.2/0.1 描述性边界与 APR-0011 门分开表述）
    assert "不得凌驾或改写字母裁决" in dev["notes"][-1]
    assert "reject 维持不变" in dev["notes"][-1]
    assert "分开表述" in dev["notes"][-1]
    assert "小样本方向性证据" in dev["notes"][-1]
    # v1.1 修订语义：多实例聚合并列不构成门的放宽或收紧
    assert "no_loosening_note" in prep
    assert "不构成任何门的放宽或收紧" in prep["no_loosening_note"]
    assert "0.2/0.1" in prep["no_loosening_note"]
    assert "不放宽" in dev["notes"][1] or "放宽或收紧" in dev["notes"][1]


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
