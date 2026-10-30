"""R14 执行包测试：reader 判读迭代第十四轮收口（CAL-R14-CLOSE）——
盲读解析与视角注入（12 派次=4 视角格×3 实例，v1.2 规约沿用第三轮）+
六实例主记录（measurement_design item 1：两板合计
flag_count/abstain_count/abstain_rate/非弃权清单/逐旗明细）+ 视角层
三分列（item 2：中位数+min+max 不取整；本轮无零旗标实例、弃权率全部
有定义）+ GT 匹配双口径（item 3：union/agreement 并列+逐 GT
matched_by_count）+ 联合门代表配置与 per-metric 实例间范围并列
（item 4）+ 预注册假设（r13-dev-record-candidate-0-render-disambiguate）
双条件裁决（条件 (a) bottom courtyard 非弃权极差 0/0/0=0≤5 单独满足
+条件 (b) bottom 聚合弃权率 14/14=1.0>10/11 违约⇒字母=reject 拒绝支
=第二支（无图例配色引发混淆性弃权上升）+机制观察单列：主通道双条件/
绿侧颜色语义化三种语义化/接触性判据延续 13/13/黑点类两视角全弃权/
残余实例差异）+ 逐旗失败通道归因（vs R13，链自 r6；几何门 R13=0→
R14=1 首次回升）+ courtyard 被动追踪 + development 域记录。

结构照 test_r13_calibration_round13.py 先例，仅输入与轮次常量不同
（R14=纯仪器变更轮：bottom 视白色内容显式化配色——白墨图元→橙
(255,165,0)、板内空隙白→绿 (0,128,0)；renders-r5 白压平版→
renders-r14b 显式配色版=r5→r14b 首次渲染变更、零仪器变更纪律例外
已预注册 render-framing-r14b.json=7004b017 先于成图落盘；首试
render-framing-r14.json=918672b4 预配色探针证伪作废+witness-r14b
b63771f9 落地；top 两张渲染自 renders-r5 逐字节复用；指引
observation-guidance-r13.md=c28806e1 零字节复用=恰零个指引侧变量；
GT/阈值零变更；协议侧零新增条款（v1.2 沿用）；读者无颜色图例=无图例
条件即本轮检验设计；预注册于 r14-prep-record.json（93440a3d），链=
round13-dev-record（6b34c442）→用户路线 A 拍板（2026-09-08）→首试
证伪（918672b4）→r14b 渲染（7004b017/b63771f9）→r14-prep-record；
判据=bottom courtyard 非弃权极差（≤5）+bottom 聚合弃权率对照 r13
10/11（>10/11=混淆拒绝通道），双条件分列不合并；APR-0011 门与主通道
判据各自独立、互不凌驾）。

覆盖：
- 盲读原文（reader-raw-r14-*.txt 十二件，冻结证据）：合法 JSON、结构
  （reader_id/per_image/reading_notes；flag 六键含 location_evidence）、
  实例内跨板连续编号（R14T/R14B）与实例间独立编号、实例旗数
  6/8/10/4/3/7 与弃权 5/6/7/4/3/7、reroute 恰 1 条（R14T-004 非弃权
  top-i1 边界报告）、拒收清单固化（38 旗全过 calibration fail-closed
  校验，0 拒收）、哈希与 run-r14 登记一致；
- 视角注入确定性+派发模式（12 派次两波次串行保序）+读者实例披露
  （12/12 派次自述纯 Read 直读=v1.2 沿用合规；输出格式披露：12 件均
  indent=1 重序列化；无围栏剥离；本轮无零旗标格）；
- calibration-run-r14.json：盘上 canonical byte 一致；逐实例逐态
  compare_v3 用内嵌输入重算 byte-exact 一致（本轮 12 格全部有旗、
  view_check 全 full）；内嵌 gt_entries=源 GT 文件条目+
  derivation-log-r5 重投影零新派生（top 渲染零变更=输入未变）；零
  matches 复算；六实例聚合复算（abstain_rate
  0.833333/0.75/0.7/1.0/1.0/1.0）；视角层三分列复算（top 极差
  0.133333/bottom 极差 0.0）；双口径复算（union 0/13=0.0、agreement
  0/13=0.0、matched_by_count 全部 0；bottom 无 GT 在案 gt-audit-r1）；
  代表配置（top-i2+bottom-i1：双视角中位实例均唯一、无 tie）joint
  复算（12 旗 10 弃权=0.833333、0/13、0/2；APR-0011 联合 not_met，
  三项未达线）+per-metric 范围；
- 预注册假设双条件裁决：判据引用=r14-prep-record hypothesis_test 原文
  （support=极差≤5 且聚合弃权率≤10/11/reject=极差>5 或聚合弃权率>
  10/11 原样）；实测条件 (a) bottom courtyard 非弃权=0/0/0（极差 0、
  r13 基线 0/0/0 交叉核对）满足但成因=全弃权路径；条件 (b) bottom 聚合
  弃权率=14/14=1.0>10/11 违约⇒verdict=reject（拒绝支=第二支：无图例
  配色引发混淆性弃权上升）；双条件分列不合并；守门通道 R13=0→R14=1
  回升独立单列（guard_ok=False；r14 support 条件不含守门要件）；
  机制观察单列（主通道双条件 6 派次 §4(i) 摘录校验；同一绿色三实例
  三种语义化（i1=「四瓣式绿色轮廓」/i2=「绿色蝶形连接形态」/i3=
  「绿色 courtyard 矩形」）并发 2 条接触性弃权旗 R14B-001/002 摘录
  校验；接触性判据 13/13 旗逐旗摘录校验；黑点类 14 旗两视角全弃权；
  残余实例差异）；reroute 类被动追踪（R14T-004 子串零命中=未援引）；
- 通道归因（vs R13）：重放对拍 R12/R13 十二件（复算=在案登记）与
  R14 十二件全部复现（候选对=空集）；几何门 0→1（R7 起连续空后首次
  回升：R14T-002×GT-REVC-AP-7-C31U4 containment 1.0、面积比
  14.085733>10 出局=宽泛框被门正确拒绝）、类别门 0→0、视角门 0→0；
  链自 r6（几何 1→0→0→0→0→0→0→0→1；类别 1→0→1→0→0→1→0→0→0）；
  courtyard 追踪：非弃权 0 条、弃权 17 条（top 13+bottom 4）、命中
  r8=1→r9=0→r10=1→r11=3→r12=0→r13=0→r14=0；
- 预注册链：round13-dev-record（6b34c442）→用户路线 A 拍板→首试证伪
  （render-framing-r14=918672b4）→r14b 渲染（framing 7004b017/
  witness b63771f9）→r14-prep-record（93440a3d）→run-r14 链含哈希；
  guidance-r13（c28806e1 零字节复用）/guidance-r12 基线（0ac22fcd）/
  r9、r8 指引链/framing-r5/derivation-log-r5/GT/协议 v1 零字节保留
  （22dc7337）/复用 PNG/冻结 PDF sha 与盘上一致；阈值常量零覆盖
  （containment 0.5/area_ratio_max 10.0 与 r12 相同）；gt-audit-r1
  引用（1f20554a）；
- round14-dev-record.json：域声明、本轮性质（纯仪器变更轮：bottom
  白色内容显式化配色+指引零字节复用+无图例设计）、假设裁决节与
  run-r14 逐字一致（verdict=reject 双条件）、R13→R14 方向性观察
  （派次 12→12、旗标 35→38、bottom 弃权率 10/11→14/14、top 极差
  0.571429→0.133333 收敛、bottom courtyard 非弃权 0/0/0 维持、连续
  第三轮零匹配）、联合评价趋势（r5→r14 逐轮表、连续计数 0→0；
  r11–r14 行=代表配置口径并列注明）、run-r14 sha 引用一致、
  next_iteration_targets 覆盖 r15 指引侧颜色-图层映射配套（须预注册；
  指引与仪器分轮单变量纪律）/绿色空隙被误读为 courtyard 矩形的渲染
  侧消歧候选（非语义色/降饱和）/top 接触性弃权高企延续（分辨率受限）/
  黑点类一致弃权延续观察/留出集运行时机=开发线收敛判断（须用户；
  HOLDOUT-PLAN.md a4b80193）/GT 侧已全关闭延续、is_gate=False、
  in_calibrated_range 恒 False；
- 命名约束：seed_match_rate 带 SEED_METRIC_NOTE、递归无
  precision/FPR 越界命名键；命名覆盖 R13T/R13B→R14T/R14B 为派发指令
  机械替换入 naming_constraints；受保护三文件 sha256 前 8 断言+
  observation-guidance-r13.md（零字节复用）零字节不动；
- s53 重跑：同参重建 byte-exact 一致 + 防覆写护栏语义（字节等同→
  幂等跳过零覆写、不同→fail-closed）+s53 零 dev-record 写入
  （round14-dev-record 由另包落盘，不在 s53 写集）。

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

ROUND_ID = "2026-09-08-r14"
DECLARED_DATE = "2026-09-08"
INSTANCE_ORDER = ("top-i1", "top-i2", "top-i3",
                  "bottom-i1", "bottom-i2", "bottom-i3")
RAW_FILES = {
    "applied-top-i1": "reader-raw-r14-applied-top-i1.txt",
    "prep1-top-i1": "reader-raw-r14-prep1-top-i1.txt",
    "applied-top-i2": "reader-raw-r14-applied-top-i2.txt",
    "prep1-top-i2": "reader-raw-r14-prep1-top-i2.txt",
    "applied-top-i3": "reader-raw-r14-applied-top-i3.txt",
    "prep1-top-i3": "reader-raw-r14-prep1-top-i3.txt",
    "applied-bottom-i1": "reader-raw-r14-applied-bottom-i1.txt",
    "prep1-bottom-i1": "reader-raw-r14-prep1-bottom-i1.txt",
    "applied-bottom-i2": "reader-raw-r14-applied-bottom-i2.txt",
    "prep1-bottom-i2": "reader-raw-r14-prep1-bottom-i2.txt",
    "applied-bottom-i3": "reader-raw-r14-applied-bottom-i3.txt",
    "prep1-bottom-i3": "reader-raw-r14-prep1-bottom-i3.txt",
}
RAW_SHA256_FIRST8 = {
    "applied-top-i1": "ef9e7304", "prep1-top-i1": "6dcf533b",
    "applied-top-i2": "9fdf35d1", "prep1-top-i2": "91f9e6d7",
    "applied-top-i3": "cd4f497d", "prep1-top-i3": "082946d0",
    "applied-bottom-i1": "9e380926", "prep1-bottom-i1": "2b21355c",
    "applied-bottom-i2": "b14bf7e2", "prep1-bottom-i2": "f71e79b5",
    "applied-bottom-i3": "0ceb4acd", "prep1-bottom-i3": "0b975980",
}
READER_IDS = {
    "applied-top-i1": "reader-r14-top-i1",
    "prep1-top-i1": "reader-r14-top-i1",
    "applied-top-i2": "reader-r14-top-i2",
    "prep1-top-i2": "reader-r14-top-i2",
    "applied-top-i3": "reader-r14-top-i3",
    "prep1-top-i3": "reader-r14-top-i3",
    "applied-bottom-i1": "reader-r14-bottom-i1",
    "prep1-bottom-i1": "reader-r14-bottom-i1",
    "applied-bottom-i2": "reader-r14-bottom-i2",
    "prep1-bottom-i2": "reader-r14-bottom-i2",
    "applied-bottom-i3": "reader-r14-bottom-i3",
    "prep1-bottom-i3": "reader-r14-bottom-i3",
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
#: 逐实例旗数/弃权数（盘面实测口径；与 run-r14 聚合一致）
EXPECT_COUNTS = {"top-i1": 6, "top-i2": 8, "top-i3": 10,
                 "bottom-i1": 4, "bottom-i2": 3, "bottom-i3": 7}
EXPECT_ABSTAIN = {"top-i1": 5, "top-i2": 6, "top-i3": 7,
                  "bottom-i1": 4, "bottom-i2": 3, "bottom-i3": 7}
EXPECT_PART_COUNTS = {
    "applied-top-i1": 3, "prep1-top-i1": 3,
    "applied-top-i2": 6, "prep1-top-i2": 2,
    "applied-top-i3": 4, "prep1-top-i3": 6,
    "applied-bottom-i1": 2, "prep1-bottom-i1": 2,
    "applied-bottom-i2": 1, "prep1-bottom-i2": 2,
    "applied-bottom-i3": 5, "prep1-bottom-i3": 2,
}
#: 本轮无零旗标格（12 格全部≥1 旗；r13/r14 连续两轮无）
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
#: R14 reroute 恰 1 条（R14T-004 非弃权 top-i1 边界报告；r13 通道
#: 被动追踪延续；滥用型=0）
EXPECT_R14_REROUTE = [("top-i1", "R14T-004", False)]
#: 受保护文件（R14-CLOSE 红线：零改动）
PROTECTED_SHA256_FIRST8 = {
    "pcbflow/cli.py": "3bfc9407",  # M1 refresh: accept copper-loop baseline 6ed4f3fd->0a738047; value source = measured sha256(pcbflow/cli.py) first 8; G1+ refresh (2026-09-24): 0a738047->3bfc9407, REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json = 0a738047 (2026-09-11)
    "pcbflow/config.py": "8ad12b3f",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json": "d43dad89",
}
#: r13 指引零字节不动（红线：零字节复用=本轮唯一判读依据，收工哈希=
#: 开工哈希 c28806e1）
GUIDANCE_SHA256_FIRST8 = {
    "out/v3-tl2/calibration/observation-guidance-r13.md": "c28806e1",
}
#: 预注册件哈希锚（先验给定的前 8）
PREREG_ANCHORS = {
    "out/v3-tl2/calibration/observation-guidance-r13.md": "c28806e1",
    "out/v3-tl2/calibration/observation-guidance-r12.md": "0ac22fcd",
    "out/v3-tl2/calibration/observation-guidance-r9.md": "a0c10154",
    "out/v3-tl2/calibration/observation-guidance-r8.md": "aad43270",
    "out/v3-tl2/calibration/r14-prep-record.json": "93440a3d",
    "out/v3-tl2/calibration/r13-prep-record.json": "b1c0d8b5",
    "out/v3-tl2/calibration/round13-dev-record.json": "6b34c442",
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
    "out/v3-tl2/calibration/render-framing-r14.json": "918672b4",
    "out/v3-tl2/calibration/render-framing-r14b.json": "7004b017",
    "out/v3-tl2/calibration/render-witness-r14b.json": "b63771f9",
    "out/v3-tl2/calibration/render-framing-r5.json": "860aa910",
    "out/v3-tl2/calibration/derivation-log-r5.json": "62343380",
    "out/v3-tl2/calibration/evaluation-protocol-v1.md": "22dc7337",
    "out/v3-tl2/calibration/gt-audit-r1.json": "1f20554a",
    "out/v3-tl2/calibration/calibration-run-r13.json": "787c4589",
    "out/v3-tl2/calibration/calibration-run-r12.json": "2ec2fb04",
    "out/v3-tl2/calibration/calibration-run-r11.json": "ec05e472",
    "out/v3-tl2/calibration/calibration-run-r10.json": "622c9099",
    "out/v3-tl2/calibration/calibration-run-r9.json": "e16420e5",
    "out/v3-tl2/calibration/calibration-run-r8.json": "3c580eb3",
    "out/v3-tl2/holdout/HOLDOUT-PLAN.md": "a4b80193",
}
#: renders-r14b 两张 bottom PNG（本轮新渲染件；两板逐字节相同）
BOTTOM_PNG_SHA256_R14B = (
    "d7284259c236ba3e2e7295f11fabc119ec37d347744439e608e35ee7574731a3")
#: renders-r5 两张 top PNG（r14b top 逐字节复用源）
TOP_PNG_R5 = {
    "applied-top.png":
        "298bc620ea8824fa07711ea4ec1875aa0dda3bc10a9edec5ca85e0f4f12a3cd0",
    "prep1-top.png":
        "b2f845246e2786a47ec8256ffb8f9154d8038dad7fda868cca54c58f688d44f8",
}
#: 六实例弃权率（盘面实测口径；本轮无零旗标实例、全部有定义）
EXPECT_RATES = {"top-i1": 0.833333, "top-i2": 0.75, "top-i3": 0.7,
                "bottom-i1": 1.0, "bottom-i2": 1.0, "bottom-i3": 1.0}
#: 主通道预注册描述性边界（双条件；与门分列；非门阈值）
DESCRIPTIVE_BOUNDARIES = {"support_max_range": 5,
                          "support_max_aggregate_abstain_num": 10,
                          "support_max_aggregate_abstain_den": 11}
#: 同一绿色三实例三种语义化（r14 机制观察 (b) 的原始件摘录锚）
GREEN_SEMANTICS = [
    ("applied-bottom-i1", "四瓣式绿色轮廓"),
    ("applied-bottom-i2", "绿色蝶形连接形态"),
    ("applied-bottom-i3", "绿色 courtyard 矩形"),
]
#: R14B-001 接触性弃权旗摘录锚（bottom-i3 applied location_evidence）
CONTACT_FLAG_ANCHOR = ("applied-bottom-i3", "R14B-001",
                       "方形焊盘的绿色 courtyard 矩形与相邻圆形焊盘的"
                       "环形金属边缘贴至疑似接触/轻微重叠")


def _load(name):
    with open(os.path.join(CAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(rel):
    return hashing.sha256_file(os.path.join(REPO, *rel.split("/")))


def _s53():
    spec = importlib.util.spec_from_file_location(
        "s53_calibration_r14_compare",
        os.path.join(REPO, "scripts", "s53_calibration_r14_compare.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_record():
    path = os.path.join(CAL_DIR, "calibration-run-r14.json")
    disk = open(path, "rb").read()
    return json.loads(disk.decode("utf-8")), disk


def _run_dev_record():
    path = os.path.join(CAL_DIR, "round14-dev-record.json")
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

def test_reader_raw_r14_files_valid_structure_and_prefixes():
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
        prefix = {"top": "R14T-", "bottom": "R14B-"}[view]
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
        "top-i1": ["R14T-%03d" % i for i in range(1, 7)],
        "top-i2": ["R14T-%03d" % i for i in range(1, 9)],
        "top-i3": ["R14T-%03d" % i for i in range(1, 11)],
        "bottom-i1": ["R14B-%03d" % i for i in range(1, 5)],
        "bottom-i2": ["R14B-%03d" % i for i in range(1, 4)],
        "bottom-i3": ["R14B-%03d" % i for i in range(1, 8)],
    }
    for inst in INSTANCE_ORDER:
        got = seen_ids[inst]
        assert got == expect_ids[inst], inst
        assert len(got) == EXPECT_COUNTS[inst]
    # reroute 类旗标恰 1 条（R14T-004 非弃权边界报告 top-i1——r12 通道
    # 被动追踪延续；r13 的 2 条→r14 收敛为 1 条非弃权）
    reroute = [(INSTANCE_OF_KEY[key], f["flag_id"], f["abstain"])
               for key, name in RAW_FILES.items()
               for f in _load(name)["per_image"][0]["flags"]
               if f["category"] == "suspicious_reroute"]
    assert reroute == EXPECT_R14_REROUTE
    # 合计 38 旗=6 非弃权+32 弃权（盘面口径与聚合一致）
    total = sum(EXPECT_COUNTS.values())
    abstain = sum(EXPECT_ABSTAIN.values())
    assert total == 38 and abstain == 32 and total - abstain == 6
    # 本轮无零旗标格（12 格全部≥1 旗）
    assert all(v >= 1 for v in EXPECT_PART_COUNTS.values())
    assert ZERO_FLAG_PARTS == []
    # 同一绿色三实例三种语义化（机制观察 (b) 原始件锚；逐字 substring）
    for key, excerpt in GREEN_SEMANTICS:
        assert excerpt in _raw_text(key), key
    # R14B-001/002 接触性弃权旗（bottom-i3 applied）摘录锚
    key, fid, excerpt = CONTACT_FLAG_ANCHOR
    assert excerpt in _raw_loc(key, fid)


def test_parse_replay_no_rejections_view_injection_and_reader_instance_note():
    s53 = _s53()
    # 逐文件重放解析（冻结证据只读）：全部旗标通过校验、拒收清单空
    replay = {}
    for key, rel in s53.RAW_FILES.items():
        parsed = s53.parse_reader_raw(rel)
        assert parsed["direct_json_parse"] is True
        assert parsed["repair"] == "no_repair"
        for img in parsed["images"]:
            assert img["rejected"] == []
            assert all(set(f) == set(s53.READER_KEYS) for f in img["flags"])
        replay[key] = parsed
    # 视角映射纯函数：确定性 + 规则（作用于派发图像名，非盘上件键）
    assert s53.view_for_image("applied-top.png") == "top"
    assert s53.view_for_image("prep1-bottom.png") == "bottom"
    assert s53.view_for_image("applied-top.png") == s53.view_for_image(
        "applied-top.png")
    try:
        s53.view_for_image("mystery.png")
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
    # 旗标计数（按实例/板/视角/类别分层；总 38）
    fc = run["reader"]["flag_count"]
    assert fc["by_instance"] == EXPECT_COUNTS
    assert fc["abstain_by_instance"] == EXPECT_ABSTAIN
    assert fc["by_state"] == {"applied": 21, "prep1": 17}
    assert fc["by_view"] == {"top": 24, "bottom": 14}
    assert fc["abstain_by_view"] == {"top": 18, "bottom": 14}
    assert fc["by_category"] == {
        "silk_readability": {"total": 6, "non_abstain": 5, "abstain": 1},
        "courtyard_crowding": {"total": 17, "non_abstain": 0, "abstain": 17},
        "other_advisory": {"total": 12, "non_abstain": 0, "abstain": 12},
        "suspicious_reroute": {"total": 1, "non_abstain": 1, "abstain": 0},
        "placement_pattern_anomaly": {"total": 2, "non_abstain": 0,
                                      "abstain": 2},
    }
    assert fc["reroute_by_instance"] == {"top-i1": 1, "top-i2": 0,
                                         "top-i3": 0, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fc["reroute_class_production"] == 1
    assert fc["total"] == 38
    # 派发模式（12 派次=4 格×3 实例，两波次串行保序；v1.2 沿用条款）
    dm = run["reader"]["dispatch_mode"]
    assert dm["mode"] == "instance_serial_two_wave"
    assert dm["instances_per_cell"] == 3 and dm["dispatch_count_total"] == 12
    assert "同一实例先 applied 后 prep1" in dm["within_instance_serial_order"]
    assert "R14B-001..004" in dm["flag_id_continuity"]["bottom-i1"]
    assert "仪器侧单变量" in dm["diff_note"] and "v1.2" in dm["diff_note"]
    assert "零颜色图例" in dm["diff_note"]
    assert "12 次盲读" in run["reader"]["dispatch_discipline"]
    assert "禁止交流" in run["reader"]["dispatch_discipline"]
    assert "无任何 GT" in run["reader"]["dispatch_discipline"]
    assert "observation-guidance-r13.md" in \
        run["reader"]["dispatch_discipline"]
    assert "禁止对图像做任何程序化处理" in \
        run["reader"]["dispatch_discipline"]            # v1.2 沿用条款
    assert "零诊断报告内容" in run["reader"]["dispatch_discipline"]
    assert "零颜色图例" in run["reader"]["dispatch_discipline"]
    # 读者实例披露（R14：12/12 纯直读 v1.2 沿用合规+输出格式披露）
    note = run["reader"]["reader_instance_note"]
    assert "12/12 派次自述合规" in note and "Read 工具" in note
    assert "沿用第三轮" in note
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
# run-r14：canonical、常量、域声明、单变更轮、受保护文件、courtyard
# ---------------------------------------------------------------------------

def test_run_r14_canonical_constants_domain_and_protected_files():
    rec, disk = _run_record()
    assert disk == hashing.canonical_json_bytes(rec)    # canonical JSON
    assert rec["kind"] == "tl2_calibration_run_r14"
    assert rec["round_id"] == ROUND_ID                  # 声明常量
    assert rec["round_label"] == "r14"
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
    # 单变更声明（仪器侧单变量=bottom 渲染件更换；协议侧零新增=v1.2 沿用）
    ic = rec["instrument_change"]
    assert ic["nature"].startswith("单变量仪器侧变更轮")
    assert "白色内容显式化配色" in ic["nature"] and "零字节复用" in \
        ic["nature"]
    assert "7004b017" in ic["nature"] and "918672b4" in ic["nature"]
    assert "读者无颜色图例" in ic["nature"]
    assert ic["components"][0].startswith(
        "bottom-render-white-content-explicit-coloring")
    # changed_variables 登记与 r14-prep-record.json 一致（恰一项，锚
    # 93440a3d；no_instrument_change=false 指本轮恰有仪器侧变更）
    prep = _load("r14-prep-record.json")
    assert prep["no_instrument_change"] is False
    assert prep["instrument_change"]["declared"] is True
    assert prep["instrument_change"]["no_instrument_change"] is False
    assert prep["read_prohibition_compliance"] is True
    assert prep["no_visual_reading"] is True
    assert [v["id"] for v in prep["changed_variables"]] == [
        "bottom-render-white-content-explicit-coloring"]
    assert [v["id"] for v in ic["changed_variables_registered"]] == \
        [v["id"] for v in prep["changed_variables"]]
    # unchanged 与 r14-prep-record.json 登记逐字一致
    assert ic["unchanged_components"] == prep["unchanged_components"]
    pa = ic["protocol_amendment"]
    assert pa["amendment_version"].startswith("v1.2")
    assert "沿用" in pa["amendment_version"]
    assert "零变更" in ic["protocol_amendment"]["note"] or "零新增" in \
        ic["protocol_amendment"]["note"]
    v1p = prep["protocol_amendment"]["v1_file_preserved"]
    assert v1p["zero_byte_preserved"] is True
    assert _sha(v1p["path_rel"]) == v1p["sha256_measured"]
    assert "仪器侧处置" in ic["attribution_note"] or "恰一项" in \
        ic["attribution_note"]
    assert ic["ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r14-prep-record.json")
    assert rec["protocol"]["amendment_version"].startswith("v1.2")
    # 指引=r13 指引零字节复用（c28806e1；基线链 r12 指引 0ac22fcd 在案）
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r13.md")
    assert gp["baseline_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/observation-guidance-r12.md")
    assert "零字节复用" in gp["change_note"]
    assert "机械变换生成" in gp["change_note"]          # r13 生成链在案
    assert "落盘即冻结" in gp["change_note"]
    assert "零个指引侧变量" in gp["change_note"]
    # 渲染见证：bottom 两张=本轮新渲染件（witness 链一致）；top 两张=
    # renders-r5 逐字节复用（byte_identical_reuse）
    rd = prep["instrument_change"]["renders"]
    assert rd["bottom_differs_from_r5"] is True
    assert rd["bottom_two_boards_identical"] is True
    for w in rd["bottom_new"]:
        assert w["witness_chain_match"] is True
        assert _sha(w["path_rel"]) == w["sha256_measured"]
        assert w["sha256_measured"] == BOTTOM_PNG_SHA256_R14B
    for w in rd["top_reuse"]:
        assert w["byte_identical_reuse"] is True
        assert _sha(w["path_rel"]) == w["sha256_measured"] == \
            w["sha256_r5_source_witness"]
    # 同日只读 GT 审计引用（1f20554a；结论=GT 侧已全部关闭，本轮延续）
    ref = rec["gt_audit_reference"]
    assert ref["sha256"] == _sha("out/v3-tl2/calibration/gt-audit-r1.json")
    assert ref["sha256"].startswith("1f20554a")
    assert "bottom GT=无源已关闭" in ref["note"]
    assert "reroute GT=无源已关闭" in ref["note"]
    assert "L1NB 框径=合理维持现框" in ref["note"]
    assert "已全部关闭" in ref["note"]                  # GT 侧候选关闭声明
    assert "应为空" in ref["note"]                      # bottom 零匹配结构性
    # 受保护三文件零改动（sha256 前 8）+ r13 指引零字节不动
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
    assert "先于 R14 盲读冻结" in md["preregistration_declaration"]
    # pre_round_review 键（本轮无额外评审；轮前诊断=渲染探针链、零
    # reader 上下文）
    prr = prep["pre_round_review"]["declaration"]
    assert "渲染探针链" in prr and "不进任何 reader 上下文" in prr
    assert "D1/D2/D3" in prr
    # courtyard 被动追踪键（prep-record 预注册；零阈值改动、零期望）
    ct = rec["courtyard_tracking"]
    assert ct["note_source"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r14-prep-record.json")
    assert ct["note_source"]["quote"] == prep["hypothesis_test"][
        "secondary_observation"]
    assert "零期望" in ct["declaration"] and "零阈值" in ct["declaration"]
    assert "零改动" in ct["threshold_note"]
    # bottom 观察（全弃权+零匹配结构性+本轮无零旗标格）
    bz2 = ct["bottom_observation"]
    assert "14 旗" in bz2["fact"] and "应为空" in bz2["fact"]
    assert "全弃权" in bz2["fact"] and "无零旗标" in bz2["fact"]
    for ev in bz2["evidence"]:
        raw = _load(RAW_FILES[ev["source"]])["reading_notes"]
        assert ev["excerpt"] in raw                     # 逐字摘录校验
    assert "substring" in bz2["evidence_check"]


def test_run_r14_compare_v3_recompute_byte_exact():
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
            assert r["matches"] == []                    # R14 零匹配
            assert r["duplicate_reports"] == []
    # R14 零匹配（全部实例/全部态）：逐实例 matches_detail 复算为空
    for inst in INSTANCE_ORDER:
        assert rec["instances"][inst]["combined"]["matches_total"] == 0
        assert rec["instances"][inst]["combined"]["matches_detail"] == []
        assert rec["instances"][inst]["combined"]["gt_matched_union"] == 0
    # 全部实例/态 view_mismatch=0（top 旗与同态 GT 视角相符；bottom 全
    # 弃权旗不参与视角检查）
    for inst in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            r = rec["instances"][inst]["states"][st]["compare_v3"]
            assert r["view_mismatch"] == []
    # R14T-002（top-i2 非弃权 silk）：与 GT-REVC-AP-7-C31U4 containment
    # 1.0 但面积比 14.085733>10 几何门出局=matched False（宽泛框被门
    # 正确拒绝；守门通道回升条目）
    d1 = next(x for x in rec["instances"]["top-i2"]["per_flag_gt_detail"]
              if x["flag_id"] == "R14T-002")
    assert d1["abstain"] is False
    assert d1["containment_all_none"] is False
    assert d1["matched"] is False
    ov = d1["gt_overlaps"]
    assert len(ov) == 1
    assert ov[0]["gt_id"] == "GT-REVC-AP-7-C31U4"
    assert ov[0]["containment"] == 1.0
    assert ov[0]["area_ratio"] == 14.085733
    assert ov[0]["channel"] == "area_ratio_rejected"
    # top 非弃权旗 6 条（i1 1 reroute+i2 2 silk+i3 3 silk）；其中恰
    # 2 条有 gt_overlaps（R14T-002 几何门出局+R14T-005 containment
    # 0.138112<0.5 未及近邻门）；其余 4 条 containment_all_none
    rows = [d for n in ("top-i1", "top-i2", "top-i3")
            for d in rec["instances"][n]["per_flag_gt_detail"]
            if not d["abstain"]]
    assert len(rows) == 6
    with_ov = [d for d in rows if d["gt_overlaps"]]
    assert [d["flag_id"] for d in with_ov] == ["R14T-002", "R14T-005"]
    assert all(d["containment_all_none"]
               for d in rows if not d["gt_overlaps"])
    # bottom 全弃权（14 旗=4/3/7 全部弃权；bottom-i2 3/3→rate=1.0）
    assert rec["instances"]["bottom-i2"]["combined"]["abstain_rate"] == 1.0
    assert "3/3" in rec["instances"]["bottom-i2"]["combined"][
        "abstain_rate_arithmetic"]
    for inst in ("bottom-i1", "bottom-i2", "bottom-i3"):
        c = rec["instances"][inst]["combined"]
        assert c["flag_count"] == c["abstain_count"]
        assert c["non_abstain_flag_ids"] == []


def test_run_r14_gt_entries_source_plus_reprojection():
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
    # top 渲染零变更=重投影输入未变，本轮零新派生、沿用 r5 台账）
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

def test_run_r14_instance_view_layer_and_dual_gt_aggregation():
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
        # 非弃权清单与逐旗明细一致（6 条非弃权有明细、弃权旗单列）
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
    assert vl["top"]["abstain_rate_range"] == 0.133333
    assert vl["bottom"]["abstain_rate_range"] == 0.0
    assert vl["top"]["abstain_rate"]["median"] == 0.75
    assert vl["bottom"]["abstain_rate"]["median"] == 1.0
    assert "0.133333" in vl["top"]["abstain_rate_range_arithmetic"]
    assert "0.0" in vl["bottom"]["abstain_rate_range_arithmetic"]
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
# 代表配置 joint + per-metric 范围（item 4；中位实例均唯一无 tie）
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


def test_run_r14_representative_joint_and_metric_ranges():
    rec, _ = _run_record()
    rep = rec["representative_configuration"]
    # 代表配置选取复算：top 中位 8 唯一（top-i2）；bottom 中位 4 唯一
    # （bottom-i1）——双视角均无 tie
    assert rep["rule"].startswith("measurement_design item 4")
    assert rep["members"] == {"top": "top-i2", "bottom": "bottom-i1"}
    sel = rep["selection"]
    assert sel["top"]["median_flag_count"] == 8
    assert sel["top"]["tie"] is False and "唯一" in sel["top"]["tie_note"]
    assert sel["top"]["flag_count_by_instance"] == {"top-i1": 6,
                                                    "top-i2": 8,
                                                    "top-i3": 10}
    assert sel["bottom"]["median_flag_count"] == 4
    assert sel["bottom"]["tie"] is False and "唯一" in \
        sel["bottom"]["tie_note"]
    assert sel["bottom"]["flag_count_by_instance"] == {"bottom-i1": 4,
                                                       "bottom-i2": 3,
                                                       "bottom-i3": 7}
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
    assert agg["flag_count_total"] == n_fl == 12       # 8（top-i2）+4
    assert agg["gt_count_total"] == n_gt == 13
    assert agg["matches_total"] == n_match == 0
    assert agg["gt_matched_total"] == n_gm == 0
    assert agg["scored_total"] == n_sc == 2
    assert agg["abstain_count_total"] == n_ab == 10
    assert agg["gt_recall_total"] == round(0 / 13, 6) == 0.0
    assert agg["seed_match_rate_total"] == round(0 / 2, 6) == 0.0
    assert agg["abstain_rate_total"] == round(10 / 12, 6) == 0.833333
    assert "0/13" in agg["gt_recall_arithmetic"]
    assert "10/12" in agg["abstain_rate_arithmetic"]
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
    assert criteria["abstain_rate_le_0.5"]["actual"] == 0.833333
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
                                     "r12", "r13", "r14"}
    assert consec["rounds"]["r13"] == "not_met（在案）"
    assert consec["rounds"]["r14"] == "not_met（本轮）"
    assert comp["joint_evaluation"] == "not_met"
    assert "代表配置" in comp["scope_note"] and "不挑优" in comp["scope_note"]
    # per-metric 实例间范围（item 4 三并列之二）复算
    mr = rec["metric_ranges_instance"]
    assert mr["top"]["flag_count"] == {"min": 6, "max": 10}
    assert mr["top"]["abstain_rate"] == {"min": 0.7, "max": 0.833333}
    assert mr["top"]["abstain_count"] == {"min": 5, "max": 7}
    assert mr["top"]["matches_total"] == {"min": 0, "max": 0}
    assert mr["top"]["scored"] == {"min": 1, "max": 3}
    assert mr["bottom"]["flag_count"] == {"min": 3, "max": 7}
    assert mr["bottom"]["abstain_rate"] == {"min": 1.0, "max": 1.0}
    assert mr["bottom"]["abstain_count"] == {"min": 3, "max": 7}
    assert mr["bottom"]["matches_total"] == {"min": 0, "max": 0}
    assert mr["bottom"]["scored"] == {"min": 0, "max": 0}
    assert "note" not in mr["bottom"]["abstain_rate"]   # 本轮无 None 实例


# ---------------------------------------------------------------------------
# 预注册假设双条件裁决（(a) 满足+(b) 违约⇒字母=reject+机制观察单列）
# ---------------------------------------------------------------------------

def test_run_r14_hypothesis_reject_verdict_and_mechanism():
    rec, _ = _run_record()
    prep = _load("r14-prep-record.json")
    ht = rec["hypothesis_test"]
    assert ht["kind"] == "preregistered_hypothesis_test"
    assert ht["hypothesis_id"] == \
        "r13-dev-record-candidate-0-render-disambiguate"
    assert ht["preregistration_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/r14-prep-record.json")
    # 判据引用=r14-prep-record.json hypothesis_test 原文（逐字一致）
    quote = ht["preregistered_criteria_quote"]
    for k in ("hypothesis", "support_condition", "reject_condition",
              "null_result_note", "test_design", "declaration",
              "metric_lesson_application"):
        assert quote[k] == prep["hypothesis_test"][k], k
    pq = prep["hypothesis_test"]["preregistered_criteria_quote"]
    assert quote["candidate_0_target"] == pq["candidate_0_target"]
    assert quote["user_directive_2026_09_08"] == pq[
        "user_directive_2026_09_08"]
    assert "渲染侧消歧" in quote["candidate_0_target"]
    assert "极差 ≤5" in quote["support_condition"] and \
        "10/11" in quote["support_condition"]
    assert "极差 >5" in quote["reject_condition"] and \
        "10/11" in quote["reject_condition"]
    assert "路线 A" in quote["user_directive_2026_09_08"]
    assert "不配发颜色图例" in quote["user_directive_2026_09_08"]
    assert "正确测出无效" in quote["null_result_note"]
    assert "互不凌驾" in quote["null_result_note"]
    # 主通道度量=r14-prep-record 登记（双条件：极差+聚合弃权率对照）
    assert ht["primary_channel_metric"] == \
        prep["attribution_plan"]["primary_channel"]["metric"]
    assert "10/11" in ht["primary_channel_metric"]
    # 描述性边界与门分列声明（≤5/≤10-11 非门阈值）
    assert "≤5" in ht["descriptive_boundary_note"] and \
        "≤10-11" in ht["descriptive_boundary_note"]
    assert "门阈值零改动" in ht["descriptive_boundary_note"]
    # 主通道实测：条件 (a) 0/0/0、极差 0（r13 基线 0/0/0 交叉核对）；
    # 条件 (b) bottom 聚合弃权率 14/14=1.0>10/11 违约
    m = ht["measurement"]
    assert m["bottom_courtyard_non_abstain_by_instance_r14"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert m["bottom_courtyard_non_abstain_range_r14"] == 0
    assert m["range_le_5"] is True
    assert m["abstain_rate_le_r13"] is False
    assert m["bottom_abstain_count_r14"] == 14
    assert m["bottom_abstain_flags_r14"] == 14
    assert m["bottom_abstain_rate_r14"] == 1.0
    assert "14/14" in m["bottom_abstain_rate_r14_arithmetic"] and \
        "10/11" in m["bottom_abstain_rate_r14_arithmetic"]
    assert m["reject_condition_met"] is True
    assert m["support_condition_met"] is False
    assert "第二支" in m["reject_branch"]
    bc = m["baseline_cross_check"]
    assert bc["r13_by_instance_registered"] == bc["r13_by_instance_live"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert bc["r13_range_registered"] == 0
    assert bc["r13_bottom_abstain_live"] == "10/11"
    # 守门通道：top 几何门 R13=0→R14=1 回升（独立单列；guard_ok=False；
    # r14 support 条件不含守门要件）
    g = m["guard_channel"]
    assert g["guard_ok"] is False
    assert "R13=0→R14=1" in g["observation"]
    assert "R14T-002" in g["observation"] and \
        "GT-REVC-AP-7-C31U4" in g["observation"]
    assert "14.085733" in g["observation"]
    assert "guard_ok=False" in g["note"] or "回升如实记录" in g["note"]
    assert "不构成 r14 字母裁决输入" in g["note"]
    # 全旗标合计附记（非主通道）如实
    assert m["aggregate_context"]["apr0011_joint_evaluation_representative"] \
        == "not_met"
    assert "0.842105" in m["r14_total_flags_note"]
    assert "非主通道" in m["r14_total_flags_note"]
    # 字母裁决=reject（预注册判据复算一致；唯一正式裁决）
    assert ht["verdict"] == "reject"
    assert prep["hypothesis_test"]["support_condition"] in ht["verdict_rule"]
    assert prep["hypothesis_test"]["reject_condition"] in ht["verdict_rule"]
    assert "reject" in ht["verdict_text"] and "唯一正式裁决" in ht[
        "verdict_text"]
    assert "第二支" in ht["verdict_text"] and "14/14" in ht["verdict_text"]
    assert "10/11" in ht["verdict_text"] and "0/0/0" in ht["verdict_text"]
    assert "统计证明" in ht["verdict_text"] and "n=3" in ht["verdict_text"]
    assert "分列不合并" in ht["verdict_text"]
    assert "描述性边界" in ht["verdict_text"]
    # 机制观察单列（不凌驾字母裁决）：主通道双条件/颜色语义化/接触性
    # 延续/黑点追踪/残余差异
    mo = ht["mechanism_observation"]
    assert "不凌驾" in mo["role"]
    # (a) 主通道双条件分开实测：条件 (a) 满足（成因=全弃权路径、非判
    # 正常收敛）+条件 (b) 违约
    mc = mo["main_channel_dual_condition"]
    assert "条件 (a)" in mc["observation"] and "条件 (b)" in mc["observation"]
    assert "全弃权" in mc["observation"] and "10/11" in mc["observation"]
    assert mc["counts"]["r13_by_instance"] == {"bottom-i1": 0,
                                               "bottom-i2": 0,
                                               "bottom-i3": 0}
    assert mc["counts"]["r14_by_instance"] == {"bottom-i1": 0,
                                               "bottom-i2": 0,
                                               "bottom-i3": 0}
    assert mc["counts"]["range"] == {"r13": 0, "r14": 0}
    assert mc["counts"]["bottom_abstain_r14"] == 14
    assert mc["counts"]["bottom_abstain_rate_r14"] == 1.0
    assert mc["counts"]["bottom_abstain_rate_r13_baseline"] == 0.909091
    assert "substring" in mc["reader_note_evidence_check"]
    assert len(mc["reader_note_evidence"]) == 6
    for ev in mc["reader_note_evidence"]:
        assert ev["excerpt"] in _load(RAW_FILES[ev["source"]])[
            "reading_notes"], ev["source"]
    assert "§4(i)" in mc["reader_note_evidence_check"]
    # (b) 颜色语义化：绿色 3/3 实例出现、橙 12 派次零提及
    cs = mo["color_semantics_secondary_observation"]
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        assert cs["color_semantics_by_instance"][name][
            "instance_any_green"] is True
        assert cs["color_semantics_by_instance"][name][
            "instance_any_orange"] is False
        assert cs["color_semantics_by_instance"][name]["橙_hits_by_part"] \
            == [0, 0]
    assert "三种语义化" in cs["status"] or "语义化" in cs["observation"]
    assert "3/3 bottom 实例" in cs["observation"]
    assert "零提及" in cs["observation"]
    assert "无图例配色混淆" in cs["status"] or "构成性观察" in cs["status"]
    assert "程序实测 substring" in cs["evidence_check"]
    # 接触性判据延续：13/13 条 top courtyard 弃权旗逐旗摘录
    cc = mo["contact_criterion_continuation"]
    assert cc["contact_flag_count"] == 13
    assert "13/13" in cc["observation"] and "视觉贴近" in cc["observation"]
    assert cc["top_abstain_rate_range"] == 0.133333
    assert cc["top_abstain_rates_by_instance"] == {
        "top-i1": 0.833333, "top-i2": 0.75, "top-i3": 0.7}
    assert "substring" in cc["contact_evidence_check"]
    assert len(cc["contact_evidence"]) == 13
    for ev in cc["contact_evidence"]:
        assert ev["excerpt"] in _raw_loc(ev["source"], ev["flag_id"]), \
            (ev["source"], ev["flag_id"])
    assert all(row["abstain"] is True and
               row["category"] == "courtyard_crowding"
               for row in cc["contact_flags"])
    # 黑点类追踪：14 旗两视角全部弃权（top 4+bottom 10）
    bd = mo["black_dot_tracking"]
    assert bd["all_abstain"] is True
    assert sum(bd["by_instance"].values()) == 14
    assert bd["by_instance"] == {"bottom-i1": 4, "bottom-i2": 3,
                                 "bottom-i3": 3, "top-i1": 1, "top-i2": 1,
                                 "top-i3": 2}
    assert "top 视右上黑点 4 旗" in bd["observation"]
    assert "bottom 左上黑点 10 旗" in bd["observation"]
    assert len(bd["black_dot_flags"]) == 14
    assert all(row["abstain"] is True for row in bd["black_dot_flags"])
    assert "两视角" in bd["status"]
    assert "substring" in bd["evidence_check"]
    # 残余实例差异（bottom 全弃权+top 极差收窄+孤立焊盘组两种处置）
    rd = mo["residual_instance_differences"]
    assert "两种处置" in rd["observation"] and "0.133333" in \
        rd["observation"]
    assert "未穷尽" in rd["observation"]
    for ev in rd["evidence"]:
        src = (_load(RAW_FILES[ev["source"]])["reading_notes"]
               if ev["kind"] == "reading_notes"
               else _raw_loc(ev["source"], ev["flag_id"]))
        assert ev["excerpt"] in src, ev.get("flag_id")
    assert "substring" in rd["evidence_check"]
    assert "不凌驾" in rd["status"] or "不凌驾" in rd["observation"]
    # 度量教训延续：(b) 支混淆检测价值兑现；修订候选须预注册
    ml = ht["metric_lesson_continuation"]
    assert "(b) 支" in ml["lesson"] or "混淆检测" in ml["lesson"]
    assert "reject" in ml["lesson"]
    assert "预注册" in ml["status"] and "不得反向放宽" in ml["status"]
    assert "不得回溯改判" in ml["status"]
    # reroute 类被动追踪（r13 通道延续；非本轮判据输入）
    rc = ht["reroute_continuation_r14"]
    assert rc["reroute_total_r14"] == 1
    assert rc["reroute_by_instance_r14"] == {"top-i1": 1, "top-i2": 0,
                                             "top-i3": 0, "bottom-i1": 0,
                                             "bottom-i2": 0, "bottom-i3": 0}
    detail = rc["reroute_flag_detail_r14"]
    assert [(r["instance"], r["flag_id"], r["abstain"],
             r["detected_substring_hits"], r["adjudication"])
            for r in detail] == [
        ("top-i1", "R14T-004", False, [], "non_abstain_boundary_report")]
    for r in detail:
        assert r["form_desc_excerpt"] in _raw_text(r["source"])
    assert rc["production_chain"] == {"r8": 1, "r9": 0, "r10": 2, "r11": 3,
                                      "r12": 3, "r13": 2, "r14": 1}
    assert "滥用型" in rc["misuse_chain_note"] and \
        "r14=0" in rc["misuse_chain_note"]
    assert "非本轮预注册判据输入" in rc["role"] or "被动追踪" in rc["role"]
    # 分层观察如实附录 + 混杂与优先声明（字母裁决不被机制/分层改写）
    st_ = ht["stratified_observation"]
    assert st_["top"]["r13_range"] == 0.571429
    assert st_["top"]["r14_range"] == 0.133333
    assert st_["top"]["r14_by_instance"] == {"top-i1": 0.833333,
                                             "top-i2": 0.75,
                                             "top-i3": 0.7}
    assert st_["bottom"]["r13_range"] == 0.25
    assert st_["bottom"]["r14_range"] == 0.0
    assert st_["bottom"]["r14_by_instance"] == {"bottom-i1": 1.0,
                                                "bottom-i2": 1.0,
                                                "bottom-i3": 1.0}
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
    assert ac["abstain_rate_r13_representative"] == 0.909091


# ---------------------------------------------------------------------------
# 通道归因（vs R13；重放可复核；链自 r6 衔接）+ courtyard 追踪
# ---------------------------------------------------------------------------

def test_run_r14_channel_attribution_and_courtyard_reproducible():
    s53 = _s53()
    rec, _ = _run_record()
    run12 = _load("calibration-run-r12.json")
    run13 = _load("calibration-run-r13.json")
    ca = rec["channel_attribution"]
    # 方法声明：照抄 run-r13 重放口径（同源几何原语）
    assert "同源几何原语" in ca["method"]["deviation_note"]
    assert "calibration-run-r13.json" in ca["method"][
        "source_of_r12_r13_detail"]
    assert ca["method"]["replay_cross_check"]["agree_with_compare_v3"] is True
    # 重放复算（R12/R13/R14 均用内嵌输入）与登记一致 + 对拍 compare_v3
    pairs12 = ca["method"]["replay_cross_check"][
        "r12_candidate_pairs_by_instance_state"]
    pairs13 = ca["method"]["replay_cross_check"][
        "r13_candidate_pairs_by_instance_state"]
    assert set(pairs12) == {f"{n}/{st}" for n in INSTANCE_ORDER
                            for st in ("applied", "prep1")}
    assert set(pairs13) == set(pairs12)
    for name in INSTANCE_ORDER:
        for st in ("applied", "prep1"):
            for run_x, pairs in ((run12, pairs12), (run13, pairs13)):
                blk = run_x["instances"][name]["states"][st]
                rp = s53.channel_replay(blk["reader_flags"],
                                        blk["flag_views"],
                                        blk["gt_entries"])
                assert s53.replay_matches_agree(rp, blk["compare_v3"])
                assert pairs[f"{name}/{st}"] == [list(p) for p in
                                                 rp["candidate_pairs"]]
    # R12/R13 十二件重放候选对=空集（与在案一致）
    assert all(v == [] for v in pairs12.values())
    assert all(v == [] for v in pairs13.values())
    # R14 十二件重放对拍 compare_v3 全部一致（候选对=空集）
    pairs14 = ca["method"]["replay_cross_check"]["r14_candidate_pairs_by_part"]
    assert set(pairs14) == set(RAW_FILES)
    for key in RAW_FILES:
        blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
            STATE_OF_KEY[key]]
        rp = s53.channel_replay(blk["reader_flags"], blk["flag_views"],
                                blk["gt_entries"])
        assert pairs14[key] == [list(p) for p in rp["candidate_pairs"]]
        assert pairs14[key] == []                       # R14 零候选对
    # 通道分组条目（几何门 R13 0→R14 1 首次回升；类别门 R13 0→R14 0）
    # 与重放一致
    def _entries_r14(failure):
        rows = []
        for key in RAW_FILES:
            blk = rec["instances"][INSTANCE_OF_KEY[key]]["states"][
                STATE_OF_KEY[key]]
            rp = s53.channel_replay(blk["reader_flags"], blk["flag_views"],
                                    blk["gt_entries"])
            rows += [e for e in rp["entries"] if e["failure"] == failure]
        return rows
    assert ca["channel_1_geometry_gate"]["r13_area_ratio_rejected_entries"] \
        == []
    rej14 = ca["channel_1_geometry_gate"]["r14_area_ratio_rejected_entries"]
    assert len(rej14) == 1
    e = rej14[0]
    assert (e["flag_id"], e["gt_id"], e["instance"], e["state"]) == \
        ("R14T-002", "GT-REVC-AP-7-C31U4", "top-i2", "applied")
    assert e["containment"] == 1.0 and e["area_ratio"] == 14.085733
    # 与重放条目对齐（关键几何字段一致；在案条目=投影精简键集）
    rp_rows = _entries_r14("area_ratio_rejected")
    assert len(rp_rows) == 1
    core = ("flag_id", "gt_id", "containment", "area_ratio")
    assert {k: e[k] for k in core} == {k: rp_rows[0][k] for k in core}
    assert "0→1" in ca["channel_1_geometry_gate"]["change"]
    cat13 = ca["channel_2_category_gate"]["r13_category_mismatch_entries"]
    assert cat13 == []
    assert ca["channel_2_category_gate"][
        "r14_category_mismatch_entries"] == []
    assert "0→0" in ca["channel_2_category_gate"]["change"]
    # 视角门：三轮重放均空（R14 bottom 全弃权、非弃权旗与 GT 无视角冲突）
    assert ca["view_gate_observations"]["r12_entries"] == []
    assert ca["view_gate_observations"]["r13_entries"] == []
    assert ca["view_gate_observations"]["r14_entries"] == []
    assert "应为空" in ca["view_gate_observations"]["note"]
    # 通道链自 r6 衔接（几何 1→0→0→0→0→0→0→0→1；类别 1→0→1→0→0→1→0→0→0）
    chain = ca["gate_chain_since_r6"]
    assert chain["geometry_gate_area_ratio_rejected_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 0, "r9": 0, "r10": 0, "r11": 0, "r12": 0,
         "r13": 0, "r14": 1}
    assert chain["category_gate_category_mismatch_by_round"] == \
        {"r6": 1, "r7": 0, "r8": 1, "r9": 0, "r10": 0, "r11": 1, "r12": 0,
         "r13": 0, "r14": 0}
    assert "通道级归因" in chain["scope"]
    # R14 特有观察：连续第三轮零匹配、courtyard 全弃权、reroute 构成变化
    spec = "\n".join(ca["r14_specific_observations"])
    assert "union=0/13" in spec and "agreement=0/13" in spec
    assert "R14T-002" in spec and "GT-REVC-AP-7-C31U4" in spec
    assert "r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1" in spec
    assert "17 条全部弃权" in spec and "接触性" in spec
    assert "r14=0" in spec
    # courtyard 被动追踪（prep-record 预注册）：非弃权 0、弃权 17、命中 0
    ct = rec["courtyard_tracking"]
    na = ct["r14_courtyard_flags"]["non_abstain"]
    ab = ct["r14_courtyard_flags"]["abstain"]
    assert len(na) == 0 and len(ab) == 17
    assert ct["courtyard_matches_r14"] == 0
    assert sum(1 for r in ab if r["view"] == "top") == 13
    assert sum(1 for r in ab if r["view"] == "bottom") == 4
    by_inst = {}
    for r in ab:
        by_inst.setdefault(r["instance"], []).append(r["flag_id"])
    assert {k: sorted(v) for k, v in by_inst.items()} == {
        "top-i1": ["R14T-001", "R14T-002", "R14T-006"],
        "top-i2": ["R14T-003", "R14T-004", "R14T-005", "R14T-006",
                   "R14T-008"],
        "top-i3": ["R14T-003", "R14T-006", "R14T-007", "R14T-008",
                   "R14T-009"],
        "bottom-i2": ["R14B-002", "R14B-003"],
        "bottom-i3": ["R14B-001", "R14B-002"],
    }
    assert ct["courtyard_matches_r13"] == 0
    assert ct["courtyard_matches_r12"] == 0
    assert ct["courtyard_matches_r11"] == 3
    assert ct["courtyard_matches_r10"] == 1
    assert ct["courtyard_matches_r9"] == 0
    assert ct["courtyard_matches_r8"] == 1              # R8T-004↔AP-8
    assert "R8T-004" in ct["courtyard_matches_r8_detail"]
    assert "R10T-011" in ct["courtyard_matches_r10_detail"]
    assert "零再现" in ct["same_domain_note"]
    # bottom 观察：全弃权零匹配属结构性（bottom 无 GT 在案）
    bz = ct["bottom_observation"]
    assert "应为空" in bz["fact"] and "无零旗标" in bz["fact"]
    for ev in bz["evidence"]:
        raw = _load(RAW_FILES[ev["source"]])["reading_notes"]
        assert ev["excerpt"] in raw
    assert "pairing_caveat" in ca and "通道级" in ca["pairing_caveat"]
    # 主通道独立复算：bottom 三实例 courtyard 非弃权=0（逐实例重放；
    # 本轮成因=全弃权路径）
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        for st in ("applied", "prep1"):
            b = rec["instances"][name]["states"][st]
            abst = set(b["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in b["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        assert cnt == 0, name
    # bottom 聚合弃权率独立复算：14/14=1.0（条件 (b) 违约数值）
    b_flags = sum(rec["instances"][n]["combined"]["flag_count"]
                  for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    b_abst = sum(rec["instances"][n]["combined"]["abstain_count"]
                 for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    assert (b_flags, b_abst) == (14, 14)
    # r13 基线独立复算（run-r13 内嵌输入）：0/0/0、bottom 聚合 10/11
    base13 = {}
    for name in ("bottom-i1", "bottom-i2", "bottom-i3"):
        cnt = 0
        for st in ("applied", "prep1"):
            b = run13["instances"][name]["states"][st]
            abst = set(b["compare_v3"]["abstain"]["abstain_ids"])
            cnt += sum(1 for f in b["reader_flags"]
                       if f["category"] == "courtyard_crowding"
                       and f["flag_id"] not in abst)
        base13[name] = cnt
    assert base13 == {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    f13 = sum(run13["instances"][n]["combined"]["flag_count"]
              for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    a13 = sum(run13["instances"][n]["combined"]["abstain_count"]
              for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    assert (f13, a13) == (11, 10)
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

def test_run_r14_input_hashes_on_disk():
    rec, _ = _run_record()
    for item in rec["preregistration"]["frozen_artifacts"]:
        assert _sha(item["path_rel"]) == item["sha256"], item["role"]
    roles = {item["role"] for item in
             rec["preregistration"]["frozen_artifacts"]}
    assert {"evaluation_protocol", "r14_prep_record_preregistration",
            "observation_guidance_r13_reused",
            "observation_guidance_r12_baseline",
            "observation_guidance_r9_chain", "observation_guidance_r8_chain",
            "render_framing_r14b_preregistration", "render_witness_r14b",
            "r13_dev_record_preregistration_source",
            "r12_dev_record_prior_chain", "r13_prep_record_prior_chain",
            "r12_prep_record_witness_source",
            "r11_dev_record_witness_chain", "r11_prep_record_witness_chain",
            "r10_dev_record_witness_chain", "r10_prep_record_witness_chain",
            "r9_dev_record_witness_chain", "r9_prep_record_witness_chain",
            "r8_dev_record_witness_chain", "r8_prep_record_witness_chain",
            "r7_prep_record_witness_chain",
            "render_framing_r5_top_reuse_provenance",
            "gt_reprojection_log_r5",
            "gt_seed_prep1", "gt_expansion_applied", "gt_audit_r1_closed",
            "source_image_pdf_applied_top_r4",
            "source_image_pdf_applied_bottom_r4",
            "source_image_pdf_prep1_top_r4",
            "source_image_pdf_prep1_bottom_r4",
            "render_png_applied_top_r14b_reuse_r5",
            "render_png_prep1_top_r14b_reuse_r5",
            "render_png_applied_bottom_r14b_new",
            "render_png_prep1_bottom_r14b_new"} <= roles
    for key, blk in rec["reader"]["raw_files"].items():
        assert blk["sha256"] == _sha(blk["path_rel"])
        assert blk["sha256"].startswith(RAW_SHA256_FIRST8[key])
        assert os.path.basename(blk["path_rel"]) == RAW_FILES[key]
    # 预注册件哈希锚（先验给定的前 8；含 r13-dev→首试证伪→r14b→r14-prep 链）
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
    # 命名覆盖入 naming_constraints（per r14-prep-record
    # protocol_amendment.naming：派发指令机械替换、指引本体零字节复用）
    assert "R13T/R13B→R14T/R14B" in rec["naming_constraints"]
    assert "reader-r13→reader-r14" in rec["naming_constraints"]
    assert "非判据变更" in rec["naming_constraints"]
    assert "实例间编号独立" in rec["naming_constraints"]
    assert "零字节复用" in rec["naming_constraints"]
    # 指引锚：本轮=r13 指引零字节复用（c28806e1），基线链=r12 指引
    # （0ac22fcd，r13 指引的生成事实源）
    gp = rec["preregistration"]["reader_protocol"]["guidance_ref"]
    assert gp["sha256"].startswith("c28806e1")
    assert gp["frozen_before_render"] is True
    assert gp["frozen_before_read"] is True
    assert gp["baseline_ref"]["sha256"].startswith("0ac22fcd")
    # 指引内容锚：r13 指引（零字节复用=本轮唯一判读依据）含量化判据/
    # 接触性判据/R13 前缀/轮次常量；r12 基线含收窄判据与 r12 轮次常量
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
    # 预注册链声明（r13-dev→路线 A 拍板→首试证伪→r14b→r14-prep 先于盲读）
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "6b34c442" in rec["preregistration"]["note"]
    assert "918672b4" in rec["preregistration"]["note"]
    assert "7004b017" in rec["preregistration"]["note"]
    assert "b63771f9" in rec["preregistration"]["note"]
    assert "93440a3d" in rec["preregistration"]["note"]
    assert "c28806e1" in rec["preregistration"]["note"]
    assert "r14-prep-record.json" in rec["preregistration"]["note"]
    assert "measurement_design" in rec["preregistration"]["note"]
    # 参照轮哈希在案（r13=上一轮基线；r14 前 run 不含本轮）
    ref13 = rec["reference_rounds"]["r13_run"]
    assert ref13["sha256"] == _sha(ref13["path_rel"])
    assert ref13["sha256"].startswith("787c4589")
    assert "r14_run" not in rec["reference_rounds"]
    # 复用/新渲染见证：两 bottom 渲染逐字节相同（r14b 新渲染件，两板
    # 同图=仪器事实）；top 两张=renders-r5 原件逐字节复用
    import hashlib
    bot_a = open(os.path.join(CAL_DIR, "renders-r14b",
                              "applied-bottom.png"), "rb").read()
    bot_p = open(os.path.join(CAL_DIR, "renders-r14b",
                              "prep1-bottom.png"), "rb").read()
    assert hashlib.sha256(bot_a).hexdigest() == \
        hashlib.sha256(bot_p).hexdigest() == BOTTOM_PNG_SHA256_R14B
    for name, want in TOP_PNG_R5.items():
        got_r14b = open(os.path.join(CAL_DIR, "renders-r14b", name),
                        "rb").read()
        got_r5 = open(os.path.join(CAL_DIR, "renders-r5", name),
                      "rb").read()
        assert hashlib.sha256(got_r14b).hexdigest() == want
        assert got_r14b == got_r5                        # 逐字节复用实测


# ---------------------------------------------------------------------------
# development 域记录与命名约束
# ---------------------------------------------------------------------------

def test_dev_record_content_and_refs():
    dev, disk = _run_dev_record()
    assert disk == hashing.canonical_json_bytes(dev)    # canonical JSON
    assert dev["kind"] == "tl2_calibration_round14_dev_record"
    assert dev["evaluation_domain"] == "development"
    assert dev["round_id"] == ROUND_ID
    assert dev["declared_date"] == DECLARED_DATE
    # 本轮性质=纯仪器变更轮（bottom 白色内容显式化配色）+指引零字节复用
    assert "纯仪器变更轮" in dev["round_nature"]
    assert "单变量仪器侧变更轮" in dev["round_nature"]
    assert "白色内容显式化配色" in dev["round_nature"]
    assert "橙" in dev["round_nature"] and "绿" in dev["round_nature"]
    assert "7004b017" in dev["round_nature"] and "b63771f9" in \
        dev["round_nature"]
    assert "918672b4" in dev["round_nature"]            # 首试证伪在案
    assert "c28806e1" in dev["round_nature"] and "零字节复用" in \
        dev["round_nature"]
    assert "颜色图例" in dev["round_nature"]
    assert "measurement_design" in dev["round_nature"] and "五条" in \
        dev["round_nature"]
    assert "in_calibrated_range 恒 False" in dev["round_nature"]
    assert "不得冒充未见留出" in dev["domain_basis_quote"]
    assert "§4" in dev["domain_basis_quote"]
    assert "第 14 轮" in dev["domain_basis_quote"]
    # 诊断结果与 run-r14 一致（代表配置口径：top-i2+bottom-i1 无 tie）
    run, _ = _run_record()
    assert "top-i2" in dev["diagnostic_result"]["aggregation_scope"]
    assert "bottom-i1" in dev["diagnostic_result"]["aggregation_scope"]
    assert "无 tie" in dev["diagnostic_result"]["aggregation_scope"]
    assert dev["diagnostic_result"]["joint_evaluation"] == \
        run["compliance_representative"]["joint_evaluation"] == "not_met"
    assert dev["diagnostic_result"]["abstain_rate_total"] == \
        run["aggregation_representative"]["abstain_rate_total"] == 0.833333
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
    # 假设裁决节与 run-r14 逐字一致（verdict=reject；双条件分列）
    assert dev["hypothesis_test_i"] == run["hypothesis_test"]
    assert dev["hypothesis_test_i"]["verdict"] == "reject"
    assert dev["hypothesis_test_i"]["measurement"][
        "bottom_courtyard_non_abstain_range_r14"] == 0
    assert dev["hypothesis_test_i"]["measurement"][
        "bottom_abstain_rate_r14"] == 1.0
    assert dev["hypothesis_test_i"]["measurement"]["reject_condition_met"] \
        is True
    assert dev["hypothesis_test_i"]["measurement"]["support_condition_met"] \
        is False
    assert dev["hypothesis_test_i"]["measurement"]["guard_channel"][
        "guard_ok"] is False
    # 联合评价趋势：连续达标计数 0（R13 后）→0（本轮）；门槛未达成
    trend = dev["joint_evaluation_trend"]
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    assert "未达成" in trend["note"] and "不得写成已达成" in trend["note"]
    assert "代表配置" in trend["aggregation_scope_note"]
    # r5→r14 逐轮走势表（数值取各轮 run-record；r11–r14 行=代表配置口径）
    assert [row["round"] for row in trend["by_round"]] == \
        ["r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13", "r14"]
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
    assert by_r["r14"]["abstain_rate_total"] == 0.833333
    assert by_r["r14"]["flag_count_total"] == 12
    assert by_r["r14"]["matches_total"] == 0
    assert by_r["r14"]["aggregation_scope"] == \
        "representative_configuration（item 4）"
    assert by_r["r14"]["round_id"] == "2026-09-08-r14"
    assert by_r["r5"]["round_id"] == "2026-09-06-r5"
    for row in trend["by_round"]:
        assert row["joint_evaluation"] == "not_met"
        assert row["source"]["sha256"] == _sha(row["source"]["path_rel"])
    # run-r14 落盘 sha 引用一致（单向引用）
    assert dev["run_record_ref"]["path_rel"].endswith(
        "calibration-run-r14.json")
    assert dev["run_record_ref"]["sha256"] == _sha(
        dev["run_record_ref"]["path_rel"])
    # gt-audit-r1 引用与 run 一致（1f20554a；GT 侧已全部关闭）
    assert dev["gt_audit_ref"] == run["gt_audit_reference"]
    assert dev["gt_audit_ref"]["sha256"].startswith("1f20554a")
    # 旗标产量记账（38=6+32；实例/视角分列）
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 32 and fp["non_abstain_count"] == 6
    assert fp["abstain_rate_all_flags"] == 0.842105
    assert fp["abstain_rate_by_instance"] == EXPECT_RATES
    assert fp["abstain_rate_range_by_view"]["top"] == 0.133333
    assert fp["abstain_rate_range_by_view"]["bottom"] == 0.0
    assert "无零旗标" in fp["abstain_rate_range_by_view"]["note"]
    assert fp["flag_count_by_instance"] == EXPECT_COUNTS
    assert sum(fp["flag_count_by_file"].values()) == 38
    assert fp["reroute_by_instance"] == {"top-i1": 1, "top-i2": 0,
                                         "top-i3": 0, "bottom-i1": 0,
                                         "bottom-i2": 0, "bottom-i3": 0}
    assert fp["reroute_class_production"] == 1
    assert fp["parse_rejections"] == []
    assert fp["reader_ids"] == READER_IDS
    assert "冻结证据" in fp["note"] and "12/12" in fp["note"]
    assert "indent=1" in fp["note"] and "无围栏剥离" in fp["note"]
    assert "R13T/R13B→R14T/R14B" in fp["note"]
    # 诚实结论：字母裁决=reject；三条机制结论如实（跨仪器稳定/混淆代价/
    # 门在工作）
    hc = dev["honest_conclusion"]
    assert "不做「能力已修复/已达成」类断言" in hc
    assert "not_met" in hc and "0.833333" in hc and "development 域" in hc
    assert "0.0（0/13）" in hc and "union=0/13" in hc and "agreement=0/13" \
        in hc
    assert "reject" in hc and "唯一正式裁决" in hc
    assert "0/0/0" in hc and "10/11" in hc and "0≤5" in hc
    assert "14/14" in hc and "第二支" in hc
    assert "统计证明" in hc and "n=3" in hc
    assert "13/13" in hc and "视觉贴近" in hc and "0.133333" in hc
    assert "reader_note_evidence" in hc and "黑点" in hc
    assert "两种处置" in hc and "未穷尽" in hc
    assert "正确测出无效" in hc
    assert "无零旗标格" in hc and "不编造数值" in hc
    assert "系统性正常→不报告" in hc
    assert "12/12 派次 v1.2 合规" in hc
    assert "indent=1" in hc and "无围栏剥离" in hc
    assert "机制结论如实单列" in hc
    assert "混杂" in hc
    assert "gt-audit-r1" in hc and "全部关闭" in hc
    assert "in_calibrated_range" in hc and "不得冒充留出" in hc
    assert "跨仪器稳定" in hc                           # 机制结论 ①
    assert "混淆代价" in hc and "三种语义化" in hc      # 机制结论 ②
    assert "门在工作" in hc                             # 机制结论 ③
    assert "无图例配色" in hc
    assert dev["is_gate"] is False
    # preregistration_chain 与 run-r14 冻结工件一致（含 r13-dev→路线 A→
    # 首试证伪→r14b→r14-prep 链）
    run_roles = {i["role"]: i["sha256"] for i in
                 run["preregistration"]["frozen_artifacts"]}
    chain = dev["preregistration_chain"]
    assert {k: v["sha256"] for k, v in chain.items()} == run_roles
    assert chain["r13_dev_record_preregistration_source"]["sha256"] == \
        _sha("out/v3-tl2/calibration/round13-dev-record.json")
    assert chain["r14_prep_record_preregistration"]["sha256"].startswith(
        "93440a3d")
    assert chain["observation_guidance_r13_reused"]["sha256"].startswith(
        "c28806e1")
    assert chain["render_framing_r14b_preregistration"]["sha256"].startswith(
        "7004b017")
    assert chain["render_witness_r14b"]["sha256"].startswith("b63771f9")
    assert "6b34c442" in dev["preregistration_chain_note"]
    assert "918672b4" in dev["preregistration_chain_note"]
    assert "7004b017" in dev["preregistration_chain_note"]
    assert "b63771f9" in dev["preregistration_chain_note"]
    assert "93440a3d" in dev["preregistration_chain_note"]
    assert "路线 A" in dev["preregistration_chain_note"]


def test_dev_record_observations_and_next_targets():
    """方向性观察与下一迭代目标：通道数值可独立复算（描述性，不入
    度量）；next_iteration_targets 覆盖 r15 指引侧颜色-图层映射配套
    （须预注册；指引与仪器分轮单变量纪律）/绿色空隙消歧渲染侧候选/
    top 接触性弃权高企延续/黑点类延续观察/留出集运行时机（须用户）/
    GT 关闭延续；不写「正式采纳门槛达成」。"""
    dev, _ = _run_dev_record()
    run, _ = _run_record()
    obs = "\n".join(dev["directional_observation_vs_r13"])
    # R13 基线匹配数值复算（bottom 聚合 10/11）与 R14 连续第三轮零匹配
    run13 = _load("calibration-run-r13.json")
    f13 = sum(run13["instances"][n]["combined"]["flag_count"]
              for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    a13 = sum(run13["instances"][n]["combined"]["abstain_count"]
              for n in ("bottom-i1", "bottom-i2", "bottom-i3"))
    assert (f13, a13) == (11, 10)                       # r13 基线 10/11
    # R13→R14 分层/聚合数字在观察中如实引用
    for need in ("12→12", "35→38", "6/8/10", "4/3/7", "10→6", "25→32",
                 "0.714286", "0.842105", "0/0/0", "14/14=1.0", "10/11",
                 "0.571429", "0.133333", "0.25", "1.0/1.0/0.75",
                 "1.0/1.0/1.0", "0.7/0.857143/0.285714",
                 "0.833333/0.75/0.7", "3/4/4→4/3/7", "10/7/7→6/8/10",
                 "0.909091（10/11）→0.833333（10/12）", "0/13",
                 "R14T-002", "GT-REVC-AP-7-C31U4", "R14B-001", "R14T-004",
                 "R11T-012", "reject", "第二支", "条件 (a)", "条件 (b)",
                 "13/13", "接触性", "视觉贴近", "黑点", "三种语义化",
                 "四瓣式绿色轮廓", "绿色蝶形连接形态", "绿色 courtyard 矩形",
                 "tie", "唯一", "中位", "r6=1→r7=0", "几何门", "类别门",
                 "候选对=空集", "gt-audit-r1", "12/12", "indent=1",
                 "无围栏剥离", "孤立", "系统性正常→不报告",
                 "描述性边界", "r8=1→r9=0→r10=2→r11=3→r12=3→r13=2→r14=1",
                 "guard_ok=False", "不凌驾"):
        assert need in obs, need
    nxt = "\n".join(dev["next_iteration_targets"])
    # r15 指引侧颜色-图层映射配套（须预注册；指引与仪器分轮单变量纪律）
    assert "r15 指引侧颜色-图层映射配套" in nxt
    assert "橙=孔/开窗墨、绿=空隙非图元" in nxt
    assert "预注册" in nxt and "单变量纪律" in nxt
    # 绿色空隙被误读为 courtyard 矩形的渲染侧消歧候选
    assert "绿色空隙被误读为 courtyard 矩形" in nxt
    assert "降饱和" in nxt and "渲染侧" in nxt
    # top 接触性弃权高企延续（分辨率受限；r6–r14 候选延续）
    assert "接触性弃权高企" in nxt and "13/13" in nxt
    assert "图例" in nxt and "分辨率受限" in nxt
    assert "预注册" in nxt and "不得反向放宽" in nxt
    assert "不得回溯改判" in nxt
    # 黑点类一致弃权延续观察（零期望）
    assert "黑点类一致弃权" in nxt and "无期望" in nxt
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
        "out/v3-tl2/calibration/r14-prep-record.json")
    assert dev["instrument_change"]["declared"] is True
    assert dev["instrument_change"]["no_instrument_change"] is False


def test_s53_rerun_byte_identical_and_overwrite_guard():
    """s53 重跑语义：同参重建 byte-exact 一致；防覆写护栏（字节等同→
    幂等跳过零覆写、不同→fail-closed）；s53 零 dev-record 写入
    （round14-dev-record 由另包落盘，不在 s53 写集）。"""
    s53 = _s53()
    rec, disk = _run_record()
    dev, dev_disk = _run_dev_record()
    # 同参重建（纯函数）与盘上产物逐字节一致
    run_rebuilt = s53.build_run()
    assert hashing.canonical_json_bytes(run_rebuilt) == disk
    # 声明常量（无 wall-clock）
    assert s53.DECLARED_DATE == "2026-09-08"
    assert s53.ROUND_ID == "2026-09-08-r14"
    assert s53.ROUND_LABEL == "r14"
    # 主通道双条件描述性边界与产量链基线常量（操作化定义）
    assert s53.MAIN_CHANNEL_DESCRIPTIVE_BOUNDARIES == DESCRIPTIVE_BOUNDARIES
    assert s53.REROUTE_CHAIN_PRIOR == {"r8": 1, "r9": 0, "r10": 2, "r11": 3,
                                       "r12": 3, "r13": 2}
    assert s53.MISUSE_CHAIN_PRIOR == {"r10": 2, "r11": 1, "r12": 0,
                                      "r13": 1}
    assert s53.R13_BOTTOM_COURTYARD_BASELINE == {"bottom-i1": 0,
                                                 "bottom-i2": 0,
                                                 "bottom-i3": 0}
    # 防覆写护栏纯函数语义
    assert s53.overwrite_guard(None, b"x") == "write"
    assert s53.overwrite_guard(b"x", b"x") == "idempotent_skip"
    assert s53.overwrite_guard(b"y", b"x") == "fail"
    # 幂等重跑：run-r14 已存在且字节等同 → main 正常完成（零覆写）
    before = open(os.path.join(CAL_DIR, "calibration-run-r14.json"),
                  "rb").read()
    s53.main()                                          # 不抛异常=幂等路径
    after = open(os.path.join(CAL_DIR, "calibration-run-r14.json"),
                 "rb").read()
    assert before == after                       # 字节零改动
    # s53 零 dev-record 写入（分包边界：round14-dev-record 由另包落盘；
    # main 幂等重跑后该件字节零改动、s53 无 dev-record 生成函数）
    assert not hasattr(s53, "build_dev_record")
    dev_after = open(os.path.join(CAL_DIR, "round14-dev-record.json"),
                     "rb").read()
    assert dev_after == dev_disk                 # 字节零改动
    # run_record_ref 仍指向 run-r14 盘上实测 sha（单向引用完整）
    assert dev["run_record_ref"]["sha256"] == _sha(
        "out/v3-tl2/calibration/calibration-run-r14.json")


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
    assert "零字节复用" in rp["abstain_semantics"]
    assert "无任何 GT" in rp["discipline"]
    assert "禁止交流" in rp["per_view_dispatch"]
    assert "v1.2" in rp["per_view_dispatch"]
    assert "零颜色图例" in rp["per_view_dispatch"]
    assert rec["preregistration"]["note"].startswith("轮次预注册链")
    assert "r14-prep-record.json" in rec["preregistration"]["note"]
    assert rec["deterministic_recompute_note"]
    assert "6/8/10/4/3/7" in rec["deterministic_recompute_note"]
    assert "2026-09-08-r14" in rec["no_wallclock_note"]
    # 域声明与轮次性质（development 域单变更轮，非留出；
    # advisory 语义：compare 输出不是门）
    assert rec["evaluation_domain"] == dev["evaluation_domain"] == \
        "development"
    assert "单变量仪器侧变更轮" in dev["round_nature"]
    assert dev["is_gate"] is False
    assert rec["compliance_representative"][
        "critic_calibration_in_range"] is False
    assert "不是门" in dev["notes"][0]
    # 命名覆盖（派发指令机械替换）如实入账：前缀与 reader_id 两处
    assert "R13T/R13B→R14T/R14B" in rec["naming_constraints"]
    assert "reader-r13→reader-r14" in rec["naming_constraints"]
    prep = _load("r14-prep-record.json")
    assert "机械替换" in prep["protocol_amendment"]["naming"] or \
        "派发" in prep["protocol_amendment"]["naming"]
    # 三分裁决纪律声明在案（字母裁决不被机制观察改写；reject≠统计
    # 证明；主通道判据与 APR-0011 门分开表述）
    assert "不得凌驾或改写字母裁决" in dev["notes"][-1]
    assert "reject 维持不变" in dev["notes"][-1]
    assert "分开表述" in dev["notes"][-1]
    assert "小样本方向性证据" in dev["notes"][-1]
    # 纯仪器变更轮：无任何判据文本变更（指引 r13 零字节复用），不降低
    # 任何责任门槛
    assert "no_loosening_note" in prep
    assert "无任何判据文本变更" in prep["no_loosening_note"]
    assert "责任门槛" in prep["no_loosening_note"]
    assert "放宽或收紧" in dev["notes"][1]
    # 主通道判据非门：字母裁决与门分列（run 内分开表述）；描述性边界
    # 与门分列
    assert rec["hypothesis_test"]["verdict"] == "reject"
    assert rec["compliance_representative"]["joint_evaluation"] == "not_met"
    assert "分列不合并" in rec["hypothesis_test"]["verdict_text"]
    assert rec["hypothesis_test"]["measurement"][
        "bottom_courtyard_non_abstain_range_r14"] == 0
    assert rec["hypothesis_test"]["measurement"]["guard_channel"][
        "guard_ok"] is False


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
