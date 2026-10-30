"""R25 收口包 B 测试（s90_calibration_r25_devrecord /
round25-dev-record.json）——轮次开发记录生成器（s78/s83/s87 底稿同构）：
判据内容轴归因轮（三混杂轴归因链第三轴执行轮：r23 框宽排除→r24 实例群
排除→r25 判据内容；第二十五轮）：判读指引=observation-guidance-r25.md
（86af24dd=observation-guidance-r23.md 866b0157 机械变换派生落盘新件、
byte delta=+937、唯一语义变量=§4 末尾弃权边界操作化条款[s70/s80 先例
同型]）+渲染零变更=renders-r14b 四图字节复用+GT/阈值/协议正文零变更；
changed_variables=1（判据内容单变量；n=6 口径与 r24 完全同构、实例群重抽
=轮际固有混杂）；【跳号声明延续】r21=axis-plan 冻结件预留的 R21 全组合
条件位（槽位永久留空、dev-r20 已登记「R21 不做」、r22/r23/r24 跳号声明
在案、r25 与该位无涉）。预注册假设（r24-not-instance-dominated-criterion-
boundary-operationalization-attribution）归因三支判据轮后裁决=not_
criterion_dominated（字母口径，唯一正式裁决，轮后不改写）：(ncd) 支命中=
not_criterion_dominated_m4_exceeds（G1=六 bottom 实例 courtyard 非弃权
全 0 维持；M4(n=6)=1.0≥0.261904[6 位定点 1000000≥261904]）——边界操作
化未收敛个体散=判据内容非主因（残余归因=其他输出侧/模型侧固有；归因链
三轴[框宽/实例群/判据内容]全部排除完毕、不新造第四轴名称只描述）；
split_half_M1_diff=0.260377>0.09064=聚合亦移动（与 r24 反转、机制观察
单列不进分支）。归因结论槽=按实测落支登记。机制观察单列：M1 降/M2 升
分解（0.118646/0.224359）+条款行为观察（三问援引率 22/24、弃权理由候选
解释列举率 58/58）+rubric 三族 contact 3/existence_blackdot 22/
existence_other 20 对照 r19（4/4/14）与 r22（2/4/12）与 r23（8/8/7）与
r24（4/28/44）四基线；援引计数对照 r19/r22/r23/r24 四基线（r25=旗级
§5B=0/(iii-a)=11/分支(=0/条款=16+三问=13、notes 级 §5B=0/24、(iii-a)=
12/24、§6=9/24、条款=24/24）。GT：union=1/13=0.076923（GT-REVC-AP-1-
R5U6 由 applied-top-i4 R25T-005 单实例命中）、agreement=0/13（r22 首次
agreement 计入的 2/3 里程碑与 r24 的 4/6 首计入维持不改写）；通道门
几何 0/类别 1/视角 0 对照 r19（0/2/0）与 r20（0/0/0）与 r22（2/4/1）与
r23（1/1/0）与 r24（0/6/0）。G2 链 0→2→1→0→0 清零维持=资格门满足
（g2_bifurcation_record 延续引用 dev-r22=b4b8fbe9/dev-r23=343a6747/
dev-r24=1a344edf 在案）。联合门 not_met、连续=0、in_calibrated_range 恒
False 照常。台账九行并列（r16 基线/r17 轴1/r18 轴2/r19 轴3/r20/r22/
r23/r24/r25；前八行=round24-dev-record 台账在案行逐值继承+本轮 live
复算交叉核对）；r25 入排序居首（G1/G2 满足）；排序=r25_this_round 第一；
显著收益 0.337694≥0.10 描述层命中。发展域证据不得冒充留出。下一候选
建议三选项（由用户拍板、本包不预写决策）：(a) 接受发展域现状收束训练环
+留出集时机用户判断；(b) 其他输出侧因素操作化归因轮（残余归因位）；(c)
同指引重复轮第三样本或收束训练环。

覆盖（14 测试，只读 out/、零子进程/零网络；s90 幂等重跑例外=护栏语义
在案、字节零改动）：
- 防覆盖守卫：overwrite_guard 三态+_commit 写入/幂等/不同字节 FAIL；
- canonical 确定性（盘上件=同参重建 byte-exact）+轮次身份+is_gate
  False；
- 受保护文件全 64 位锚+引用件哈希清单 18 件（run-r25=251102e8/prep-r25=
  0943a8ec/guidance-r25=86af24dd/guidance-r23 基座=866b0157/run-r24=
  8a9bdb7d/dev-r24=1a344edf/run-r23=15f58350/run-r22=80a12c05/run-r19=
  e5755a11/run-r20=6573a59a/run-r16=2c1f8265/dev-r19=0e2fdd69/dev-r20=
  80e3e9e2/dev-r22=b4b8fbe9/dev-r23=343a6747/axis-plan=b6ec6467/
  typology=6dadac8d/guidance-r19 基座=8633bda5 盘上实测）+24 份 reader-
  raw 全 64 位锚+预注册链冻结工件逐件实测；
- 字母裁决=not_criterion_dominated 落支与判据布尔与预注册判据摘录逐字
  一致；
- 归因结论逻辑纯函数构造（M4 内=criterion_dominated；M4 超出=本轮实况=
  not_criterion_dominated/G1 破坏=guard_interrupted/端点）；
- M 五键与 run 一致（构造对照：九行并列、M4/split-half 定点、M3=rubric
  计数、显著收益降幅、比较集 live 行）；
- g2_bifurcation_record 延续引用（dev-r22+dev-r23+dev-r24）+G2 链
  0→2→1→0→0 清零登记+反事实构造+字母与链两账分列；
- 三轴实验总收束位（排序=r25 第一、r24 在案入排序、r20/r22/r23 资格
  门剔除、guidance-r19 胜出记录维持、发展域不得冒充留出）；
- 下一候选建议（三选项/用户拍板/预注册要求）；
- GT 双口径 union=1/agreement=0+联合门+in_calibrated_range 恒 False+
  通道门 0/1/0 对照；
- 机制观察（逐实例分布/split-half 聚合移动/三族对照四基线/援引对照/条款
  行为观察/M1 降 M2 升分解/top 分型/黑点分旗）；
- 轮次身份声明（changed_variables=1/机械派生/前缀落盘固化）+跳号声明延
  续（r21 冻结槽位原文=dev-r22 逐字继承）；
- 趋势行 r5–r25（dev-r24 冻结转录+r25 实测行）；
- honest 结论/下一目标关键锚+s90 幂等重跑+s89 分包边界。
"""

import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing  # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")

ROUND_ID = "2026-09-10-r25"
ROUND_LABEL = "r25"
DECLARED_DATE = "2026-09-10"

# DEV-E0-004 追加式锚修复：盘上件指向 v2 追加件（与 r1 冻结件差异恰=
# cli.py 保护锚 6ed4f3fd→0a738047，铜环案接纳；r1 零回写、sha 前缀
# b9bcbeb7 由 v2 件前缀 1c3e1190 接替）。
# RE-REGISTRATION D2（RE-REGISTRATION-ADJUDICATION-2026-09-13）：盘上件
# 改指 v2.1 修正件（=v2 全字段原值+kind 后缀/supersedes/双值披露三要素；
# v2 件零回写，其字节由 V2_SHA256 全长钉死=负向断言）；s90 重建=v2
# payload（无三要素字段），盘上对拍改为「三要素掩码还原后=v2 字节」。
V2_PATH = os.path.join(CAL_DIR, "round25-dev-record-v2.json")
V2_SHA256 = ("1c3e11903c74b3e81e5cd3e205de48a10a623e843389aedb21a6a6"
             "16b414a112")
V21_KIND = "tl2_calibration_round25_dev_record_v2_1"
V21_SHA256 = ("10218b65160cab3c1730a03c33a66ecd32e6c55986f0ab05e10f"
              "df2516a8ceef")
DEV_PATH = os.path.join(CAL_DIR, "round25-dev-record-v2_1.json")
_V21_PROVENANCE_KEYS = ("anchor_amendment", "supersedes")


def _load_s90():
    path = os.path.join(REPO, "scripts", "s90_calibration_r25_devrecord.py")
    spec = importlib.util.spec_from_file_location("s90_calibration_r25_dev",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S90 = _load_s90()


# REPAIR-P4 W-1（G0）：config.py 经用户授权变更（f515c348→acdfac49，登记=
# out/repair-p4/anchor-hashes-post-g0.json）。历史脚本 s90 与盘上发布件冻结不动
# （W-2 红线，证据生成器）。测试侧双层锚定：
# 1) verify 红线按现役锚执行（want=7b4974d8=实测，零改动护栏语义不弱化）；
# 2) dev-record 的 protected 展示段按历史锚语境回放（before=f515c348）——
#    record 其余内容全实测复算，重建才能与盘上冻结发布件 byte-exact
#    （防覆写护栏/盘上件身份测试的历史重放口径）。
S90.PROTECTED_FILES["pcbflow/config.py"] = (
    "8ad12b3fab12f19546034b5421aa77053f4115b91b36b87b9dfabc9075fdcf82")  # G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
# REPAIR-G1+ W-1/W-2（2026-09-24）：cli.py 授权变更 0a738047->3bfc9407
#（登记=out/repair-g1plus-r1/anchor-hashes-post-g1plus.json）——同构双层：
S90.PROTECTED_FILES["pcbflow/cli.py"] = (
    "3bfc940701d1be82029877583a0a41f49741228f2e89a321b7dafa98d179aae8")
_orig_vpf_s90 = S90.verify_protected_files


def _vpf_g0_legacy_s90():
    got = _orig_vpf_s90()
    got["pcbflow/config.py"] = (
        "f515c34842521a645145a9f5454a5919274a242e5c8c27c01faf1a4c13e73baf")
    got["pcbflow/cli.py"] = "0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e"
    return got


S90.verify_protected_files = _vpf_g0_legacy_s90


@pytest.fixture(scope="module")
def dev():
    """round25-dev-record 内存重建（纯函数；只读输入、零写盘）。"""
    return S90.build_dev_record()


@pytest.fixture(scope="module")
def run_doc():
    """run-r25 盘上件装载（只读）。"""
    return S90._json_load(S90.REL_RUN_R25)


# ---------------------------------------------------------------------------
# 守卫与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；既有且
    不同→fail；_commit=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写）。"""
    assert S90.overwrite_guard(None, b"abc") == "write"
    assert S90.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S90.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S90._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S90._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S90._commit(p, b"abc", "probe")


def test_devrecord_canonical_determinism_and_disk_identity(dev):
    """round25-dev-record 盘上件：同参重建两次 byte-exact+盘上件=
    canonical 重建+kind/轮次身份（r25/2026-09-10/development 域）+
    schema_version+is_gate=False+run_record_ref=251102e8+
    hypothesis_test_i=run 内嵌件原样。"""
    b1 = hashing.canonical_json_bytes(S90.build_dev_record())
    b2 = hashing.canonical_json_bytes(S90.build_dev_record())
    assert b1 == b2  # 同参重建 byte-exact
    raw = open(DEV_PATH, "rb").read()
    doc = json.loads(raw)
    payload = {k: v for k, v in doc.items()
               if k not in _V21_PROVENANCE_KEYS}
    payload["kind"] = dev["kind"]  # 三要素掩码还原=v2 payload（历史字段冻结）
    assert hashing.canonical_json_bytes(payload) == b1  # 盘上件 payload=canonical 重建
    assert doc["kind"] == V21_KIND  # v2.1 kind 显式后缀（§4.5 要素 1）
    assert doc["supersedes"]["path_rel"] == \
        "out/v3-tl2/calibration/round25-dev-record-v2.json"
    assert doc["supersedes"]["sha256"] == V2_SHA256  # §4.5 要素 2
    assert doc["anchor_amendment"]["old_value"] != \
        doc["anchor_amendment"]["new_value"]  # §4.5 要素 3（双值披露）
    # 负向断言：v2 原件字节零变化（零回写）
    assert hashing.sha256_file(V2_PATH) == V2_SHA256
    assert hashing.sha256_file(DEV_PATH) == V21_SHA256
    assert dev["kind"] == "tl2_calibration_round25_dev_record"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["evaluation_domain"] == "development"
    assert dev["is_gate"] is False
    assert dev["run_record_ref"]["path_rel"] == \
        "out/v3-tl2/calibration/calibration-run-r25.json"
    assert dev["run_record_ref"]["sha256"] == S90._sha(S90.REL_RUN_R25)
    assert dev["run_record_ref"]["sha256"].startswith("251102e8")
    assert dev["hypothesis_test_i"]["verdict"] == "not_criterion_dominated"
    assert dev["hypothesis_test_i"]["hypothesis_id"] == \
        "r24-not-instance-dominated-criterion-boundary-" \
        "operationalization-attribution"


def test_protected_files_reference_hash_manifest_and_chain(dev):
    """受保护文件全 64 位锚（cli/config/toolchain_lock）在件且与盘上实
    测逐一相等；引用件哈希清单 18 件（run-r25=251102e8/prep-r25=0943a8ec/
    guidance-r25=86af24dd/guidance-r23 基座=866b0157/run-r24=8a9bdb7d/
    dev-r24=1a344edf/run-r23=15f58350/run-r22=80a12c05/run-r19=e5755a11/
    run-r20=6573a59a/run-r16=2c1f8265/dev-r19=0e2fdd69/dev-r20=80e3e9e2/
    dev-r22=b4b8fbe9/dev-r23=343a6747/axis-plan=b6ec6467/typology=6dadac8d/
    guidance-r19 基座=8633bda5）逐件 live sha256_file 实测与前缀逐一相等；
    24 份 reader-raw 全 64 位锚实测；预注册链（run 冻结工件）逐件实测 sha
    与登记逐一相等。"""
    protected = dev["protected_files_verification"]
    assert protected["role"] == "红线 1 执行证据"
    for rel, want in S90.PROTECTED_FILES.items():
        if rel == "pcbflow/config.py":
            # REPAIR-P4 W-1（G0）授权变更三元对账（anchor-hashes-post-g0.json）：
            # record=登记件 before（历史发布件语境重放）；实测=after=注入后现役锚。
            assert protected["hashes"][rel] == (
                "f515c34842521a645145a9f5454a5919274a242e5c8c27c01faf1a4c13e73baf")
            assert hashing.sha256_file(
                os.path.join(REPO, rel)) == want
            continue
        if rel == "pcbflow/cli.py":
            # REPAIR-G1+ W-1/W-2（2026-09-24）授权变更三元对账
            # （anchor-hashes-post-g1plus.json）：record=登记件 before
            # （历史发布件语境重放 0a738047）；实测=after=注入后现役锚。
            assert protected["hashes"][rel] == (
                "0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e")
            assert hashing.sha256_file(
                os.path.join(REPO, rel)) == want
            continue
        assert protected["hashes"][rel] == want
        assert hashing.sha256_file(
            os.path.join(REPO, rel)) == want
    entries = dev["reference_hash_manifest"]["entries"]
    expected = {
        "run_r25": "251102e8",
        "prep_r25": "0943a8ec",
        "guidance_r25": "86af24dd",
        "guidance_r23_base": "866b0157",
        "guidance_r19_base": "8633bda5",
        "run_r16": "2c1f8265",
        "run_r19": "e5755a11",
        "run_r20": "6573a59a",
        "run_r22": "80a12c05",
        "run_r23": "15f58350",
        "run_r24": "8a9bdb7d",
        "dev_r19": "0e2fdd69",
        "dev_r20": "80e3e9e2",
        "dev_r22": "b4b8fbe9",
        "dev_r23": "343a6747",
        "dev_r24": "1a344edf",
        "axis_plan": "b6ec6467",
        "typology": "6dadac8d",
    }
    assert set(entries) == set(expected)
    for name, prefix in expected.items():
        e = entries[name]
        assert e["sha256_prefix_expected"] == prefix
        assert e["sha256"].startswith(prefix)
        assert hashing.sha256_file(
            os.path.join(REPO, e["path_rel"])).startswith(prefix)
    assert "全部 live sha256_file 实测" in \
        dev["reference_hash_manifest"]["role"]
    # 24 份 reader-raw 全 64 位锚（run 登记与本件清单逐一实测）
    raw_manifest = dev["flag_production"]["raw_files"]
    assert len(raw_manifest) == 24
    for key, rec in raw_manifest.items():
        assert hashing.sha256_file(
            os.path.join(REPO, rec["path_rel"])) == rec["sha256"]
        assert rec["sha256"].startswith(rec["sha256_prefix_expected"])
    # 预注册链（含哈希）：逐件实测与登记一致
    chain = dev["preregistration_chain"]
    for role in ("evaluation_protocol",
                 "r25_prep_record_preregistration",
                 "r24_dev_record_candidate_b_authorization_and_ledger_source",
                 "r23_dev_record_candidate_b_authorization",
                 "r22_dev_record_drift_anchor",
                 "r22_run_record_comparison_row_and_g2_reference",
                 "r23_run_record_comparison_row_and_g2_reference",
                 "r24_run_record_comparison_row_and_m_tuple_source",
                 "axis_experiment_plan_r17_r20_frozen",
                 "observation_guidance_r25_active_derived_this_round",
                 "observation_guidance_r23_mechanical_transform_base",
                 "gt_seed_prep1", "gt_expansion_applied",
                 "gt_audit_r1_closed"):
        assert role in chain, role
        item = chain[role]
        assert hashing.sha256_file(
            os.path.join(REPO, item["path_rel"])) == item["sha256"], role
    assert chain["observation_guidance_r25_active_derived_this_round"][
        "sha256"].startswith("86af24dd")
    assert chain["observation_guidance_r23_mechanical_transform_base"][
        "sha256"].startswith("866b0157")
    assert chain["r25_prep_record_preregistration"][
        "sha256"].startswith("0943a8ec")
    note = dev["preregistration_chain_note"]
    assert "机械变换派生" in note and "251102e8" in note
    assert "0943a8ec" in note and "b4b8fbe9" in note and "343a6747" in note \
        and "1a344edf" in note


# ---------------------------------------------------------------------------
# 字母裁决与归因结论逻辑（纯函数构造）
# ---------------------------------------------------------------------------

def test_letter_verdict_branch_and_criteria_booleans(dev, run_doc):
    """字母裁决=not_criterion_dominated（唯一正式裁决）：落支=(ncd) not_
    criterion_dominated_m4_exceeds（G1 维持且 M4(n=6) 条件超出）；判据布尔
    （not_criterion_dominated=True、guard_interrupted=False、criterion_
    dominated=False）与 run 盘上件逐一相等；预注册判据摘录=prep-record
    原文（11 键逐字一致）。"""
    ht = dev["hypothesis_test_i"]
    m = ht["measurement"]
    assert ht["verdict"] == "not_criterion_dominated"
    assert m["verdict"] == "not_criterion_dominated"
    assert m["letter_branch"].startswith("(ncd)")
    assert "0.261904" in m["letter_branch"]
    assert "判据内容非主因" in m["letter_branch"]
    assert m["crit_not_criterion_dominated"] is True
    assert m["crit_guard_interrupted"] is False
    assert m["crit_criterion_dominated"] is False
    # 与 run 盘上件逐一相等（dev-record 内嵌=run 原文）
    rm = run_doc["hypothesis_test"]["measurement"]
    assert m["letter_branch"] == rm["letter_branch"]
    assert ht["verdict_text"] == run_doc["hypothesis_test"]["verdict_text"]
    # 判据原文摘录=prep-record adjudication 逐字一致
    prep = S90._json_load(S90.REL_PREP_R25)
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("criterion_dominated", "not_criterion_dominated",
              "guard_interrupted", "letter_branch_map",
              "fixed_point_comparison_note", "g2_observation_separate",
              "m1_m2_gate_separate", "descriptive_boundary_note",
              "mechanism_observation_separate", "metric_lesson_separate",
              "three_way_bookkeeping"):
        assert q[k] == adj[k], k


def test_attribution_conclusion_logic_pure_function(dev):
    """归因结论逻辑纯函数（构造）：实际输入 (1000000, True)=
    not_criterion_dominated_m4_exceeds=登记裁决；反事实构造：M4 内
    (261903/0)=criterion_dominated（分岔另一侧）；G1 破坏=guard_interrupted
    （支序最高）；端点（恰 261904=超出）；6 位定点常量与判据原文同锚。
    dev-record 反事实构造注记与纯函数一致（split_half 已不在分支判定内=
    与 r24 的差异如实登记）。"""
    assert S90.attribution_verdict_fixed_point(1_000_000, True) == \
        ("not_criterion_dominated", "not_criterion_dominated_m4_exceeds")
    assert S90.attribution_verdict_fixed_point(261_903, True) == \
        ("criterion_dominated", "criterion_dominated_m4_within")
    assert S90.attribution_verdict_fixed_point(0, True) == \
        ("criterion_dominated", "criterion_dominated_m4_within")
    assert S90.attribution_verdict_fixed_point(1_000_000, False) == \
        ("guard_interrupted", "guard_interrupted_g1")
    # 端点（M4 恰=261904=超出）
    assert S90.attribution_verdict_fixed_point(261_904, True) == \
        ("not_criterion_dominated", "not_criterion_dominated_m4_exceeds")
    # 6 位定点常量与 s89/判据原文同锚
    assert S90.M4_THRESHOLD_6DP == 261_904
    assert S90.SPLIT_HALF_THRESHOLD_6DP == 90_640
    # dev-record 反事实构造注记与纯函数一致
    cf = dev["g2_bifurcation_record"]["counterfactual_check"]
    assert cf["m4_exceeds"] == [
        "not_criterion_dominated", "not_criterion_dominated_m4_exceeds"]
    assert cf["m4_within"] == ["criterion_dominated",
                               "criterion_dominated_m4_within"]
    assert cf["guards_ok_false"] == ["guard_interrupted",
                                     "guard_interrupted_g1"]


# ---------------------------------------------------------------------------
# M 五键与 run 一致（构造对照）
# ---------------------------------------------------------------------------

def test_m_tuple_matches_run_constructed_cross_check(dev, run_doc):
    """M 五键与 run 一致（构造对照）：axis ledger 本轮行=(0.433735, 0.
    916667, 22, 1.0, 0.260377)=run r25_m_tuple_6dp；构造对照：6 位定
    点 M4 超出（1000000≥261904）/split-half 聚合移动（260377>90640）、
    M4=12 格极差 1.0−0.0、split_half=|0.339623−0.600000|、M3=22=run 黑点
    族 rubric 计数；九行并列完整（r16 基线/r17/r18/r19/r20/r22/r23/r24/
    r25，前八行=dev-r24 台账继承）；比较集 live 行=run 登记值；显著收益
    降幅 0.337694 整数交叉相乘复核。"""
    rows = dev["axis_experiment_ledger"]["cross_round_status"][
        "measured_rows"]
    this = dev["axis_experiment_ledger"]["this_round_measured"]
    run_m = run_doc["hypothesis_test"]["measurement"]["r25_m_tuple_6dp"]
    assert this == {"M1": 0.433735, "M2": 0.916667, "M3": 22,
                    "M4": 1.0, "split_half_M1_diff": 0.260377}
    assert {k: rows["r25_this_round"][k]
            for k in ("M1", "M2", "M3", "M4", "split_half_M1_diff")} == run_m
    assert rows["r25_this_round"]["M1"] == 0.433735
    # 构造对照：6 位定点整数比较（M4 单判据；split_half=机制观察单列）
    assert 1_000_000 >= S90.M4_THRESHOLD_6DP
    assert 260_377 > S90.SPLIT_HALF_THRESHOLD_6DP
    assert round(1.0 - 0.0, 6) == 1.0
    assert abs(round(18 * 1000000 / 53) - round(18 * 1000000 / 30)) == 260377
    bdt = run_doc["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]
    assert bdt["rubric_families"]["counts"]["existence_blackdot"] == \
        rows["r25_this_round"]["M3"] == 22
    assert rows["r16_baseline"] == {"M1": 0.771429, "M2": 0.857143,
                                    "M3": 12, "M4": 0.261904}
    assert rows["r17_axis1"] == {"M1": 0.88, "M2": 0.75, "M3": 8,
                                 "M4": 0.333333}
    assert rows["r18_axis2"] == {"M1": 0.645161, "M2": 0.684211,
                                 "M3": 13, "M4": 0.277778}
    assert rows["r19_axis3"] == {"M1": 0.461538, "M2": 0.571429,
                                 "M3": 4, "M4": 0.211111}
    assert rows["r20_combo"] == {"M1": 0.636364, "M2": 0.285714,
                                 "M3": 6, "M4": 0.25}
    assert rows["r22_repeat"] == {"M1": 0.390244, "M2": 0.2,
                                  "M3": 4, "M4": 0.104545}
    assert rows["r23_repeat"] == {"M1": 0.484848, "M2": 0.571429,
                                  "M3": 8, "M4": 0.520833}
    assert rows["r24_expansion"] == {"M1": 0.552381, "M2": 0.692308,
                                     "M3": 28, "M4": 0.888889,
                                     "split_half_M1_diff": 0.01864}
    cmp_live = run_doc["hypothesis_test"]["measurement"]["comparison_rows_live"]
    assert cmp_live["r19_axis3"] == rows["r19_axis3"]
    assert cmp_live["r22_repeat_live"] == rows["r22_repeat"]
    assert cmp_live["r23_repeat_live"] == rows["r23_repeat"]
    assert cmp_live["r24_expansion_live"] == {
        k: rows["r24_expansion"][k] for k in ("M1", "M2", "M3", "M4")}
    sb = dev["axis_experiment_ledger"]["significant_benefit_vs_r16"]
    assert sb["r25_m1_absolute_drop"] == 0.337694
    assert sb["r24_drop_reference"] == 0.219048
    assert round(0.771429 - 0.433735, 6) == 0.337694
    assert (27 * 83 - 36 * 35) * 1_000_000 >= 100_000 * 35 * 83


# ---------------------------------------------------------------------------
# G2 分岔专节（延续引用+G2 链闭合登记+反事实构造）
# ---------------------------------------------------------------------------

def test_g2_bifurcation_record_continuation_and_chain(dev, run_doc):
    """g2_bifurcation_record 字段存在且含分叉记账模式延续引用（dev-r22=
    b4b8fbe9 g2_bifurcation_record 登记起点+dev-r23=343a6747+dev-r24=
    1a344edf 上一环，均在案）+G2 链闭合登记（r19=0→r22=2→r23=1→r24=0→
    r25=0 清零维持=资格门满足=r25 入排序）+双账分列：letter_vs_fact（字母
    =not_criterion_dominated 唯一正式裁决不改写 vs G2 链=机制观察单列）+
    counts+反事实构造注记与纯函数一致；run 侧 G2 出局条目=0 空摘录+r23
    对照=1 条装载在案。"""
    g2 = dev["g2_bifurcation_record"]
    assert "g2_bifurcation_record" in dev
    lvf = g2["letter_vs_fact"]
    assert "not_criterion_dominated" in lvf["letter"] \
        and "不改写" in lvf["status"]
    assert "r22=2→r23=1→r24=0→r25=0" in lvf["gate_chain_fact"]
    assert "两账分列" in lvf["status"]
    counts = g2["counts"]
    assert counts["g2_geometry_gate_r19"] == 0
    assert counts["g2_geometry_gate_r22"] == 2
    assert counts["g2_geometry_gate_r23"] == 1
    assert counts["g2_geometry_gate_r24"] == 0
    assert counts["g2_geometry_gate_r25"] == 0
    assert counts["g2_rejected_entries_r25"] == 0
    assert counts["g2_eligibility_gate_satisfied_r25"] is True
    assert counts["g1_bottom_courtyard_non_abstain_r25"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0, "bottom-i4": 0,
         "bottom-i5": 0, "bottom-i6": 0}
    assert counts["m4_n6_exceeds"] is True
    assert "机制观察单列" in counts["split_half_branch_role"]
    assert counts["verdict"] == "not_criterion_dominated"
    assert "观察项" in g2["bifurcation"]
    assert "单列" in g2["role"] and "不改写" in g2["role"]
    # 延续引用：dev-r22=b4b8fbe9（登记起点）+dev-r23=343a6747+dev-r24=
    # 1a344edf（上一环）
    cont = g2["continuation"]
    assert cont["round22_dev_record"]["path_rel"] == \
        "out/v3-tl2/calibration/round22-dev-record.json"
    assert cont["round22_dev_record"]["sha256"].startswith("b4b8fbe9")
    assert "g2_bifurcation_record" in cont["round22_dev_record"]["section"]
    assert cont["round23_dev_record"]["sha256"].startswith("343a6747")
    assert cont["round24_dev_record"]["sha256"].startswith("1a344edf")
    dev22 = S90._json_load(S90.REL_DEV_R22)
    dev23 = S90._json_load(S90.REL_DEV_R23)
    dev24 = S90._json_load(S90.REL_DEV_R24)
    assert "g2_bifurcation_record" in dev22
    assert "g2_bifurcation_record" in dev23
    assert "g2_bifurcation_record" in dev24
    # run 侧 G2 出局条目=0 空摘录+r23 对照=1 条装载
    grej = run_doc["hypothesis_test"]["mechanism_observation"][
        "g2_rejected_entries_r25"]
    assert grej["count"] == 0 and grej["entries"] == []
    assert [e["flag_id"] for e in
            grej["comparison_to_r23"]["r23_entries"]] == ["R23T-004"]
    assert grej["comparison_to_r23"]["r23_entries"][0][
        "area_ratio"] == 11.45868
    # 先例血统：run-r20 的 g1_bifurcation_record 同型（dev-r20 在案）
    dev20 = S90._json_load(S90.REL_DEV_R20)
    assert "g1_bifurcation_record" in dev20


def test_three_axis_closeout_ranking_and_attribution(dev, run_doc):
    """三轴实验总收束位：comparison_rule 排序（r25_this_round 第一/r19
    第二/r24 在案入排序/r18/r16 参照/r17 末位）；r20/r22/r23 不入排序
    （资格门剔除、行仅如实入账）；guidance-r19 胜出记录维持 conditional/
    double-entry 现状、复制未达成不升级；发展域证据不得冒充留出；最终结论
    维持=guidance-r19（轴3 单变量）；与 run 盘上对照账排序一致
    （fail-closed）。"""
    closeout = dev["three_axis_experiment_closeout"]
    rk = closeout["ranking"]
    assert rk["ranking_order_best_first"] == ["r25_this_round", "r19_axis3",
                                              "r24_expansion", "r18_axis2",
                                              "r16_baseline", "r17_axis1"]
    assert rk["eligible_rows"] == ["r16_baseline", "r17_axis1",
                                   "r18_axis2", "r19_axis3",
                                   "r24_expansion", "r25_this_round"]
    assert "G1 破坏" in rk["excluded_rows"]["r20_combo"]
    assert "G2 破坏" in rk["excluded_rows"]["r22_repeat"]
    assert "G2 破坏" in rk["excluded_rows"]["r23_repeat"]
    assert "入排序" in rk["status"]
    att = closeout["attribution_status_axis3_benefit"]
    assert "conditional/double-entry" in att
    assert "不升级" in att and "not_criterion_dominated" in att
    assert "两账并列" in att and "不合并" in att
    assert "不得冒充" in closeout["development_domain_discipline"]
    assert "恒 False" in closeout["development_domain_discipline"]
    assert "轴3 单变量" in closeout["final_conclusion_unchanged"]
    assert "guidance-r19" in closeout["final_conclusion_unchanged"]
    # 与 run 盘上对照账排序一致（fail-closed）
    rk_run = run_doc["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]["ranking_by_comparison_rule"]
    assert rk_run["ranking_order_best_first"] == \
        rk["ranking_order_best_first"]
    assert rk_run["r25_eligibility"] is True


# ---------------------------------------------------------------------------
# 下一候选建议（三选项、用户拍板）
# ---------------------------------------------------------------------------

def test_next_candidate_suggestion_three_options(dev):
    """下一候选建议：恰三选项（(a) 接受发展域现状收束训练环+留出集时机
    由用户判断；(b) 其他输出侧因素操作化归因轮（残余归因位）；(c) 同指引重
    复轮第三样本或收束训练环）；决策权=用户拍板、本包不预写决策；(b)(c)
    须预注册、(a) 不须。"""
    sug = dev["next_candidate_suggestion"]
    options = sug["options"]
    assert len(options) == 3
    a, b, c = options
    assert "收束训练环" in a["option"] and "留出集" in a["option"]
    assert a["preregistration_required"] is False
    assert "其他输出侧" in b["option"] and "操作化" in b["option"]
    assert "预注册" in b["option"]
    assert b["preregistration_required"] is True
    assert "同指引重复轮" in c["option"] and "第三样本" in c["option"]
    assert c["preregistration_required"] is True
    assert "用户拍板" in sug["decision_authority"]
    assert "不预写决策" in sug["decision_authority"]
    assert "HOLDOUT" in json.dumps(sug, ensure_ascii=False)
    # 由用户拍板语义在下一目标节复现
    assert any("由用户拍板" in t for t in dev["next_iteration_targets"])


# ---------------------------------------------------------------------------
# GT 双口径/联合门/in_calibrated_range 恒 False
# ---------------------------------------------------------------------------

def test_gt_dual_union_joint_gate_and_in_range_false(dev, run_doc):
    """GT 双口径 union=1/13=0.076923、agreement=0/13（GT-REVC-AP-1-R5U6
    由 applied-top-i4 R25T-005 单实例命中[<4/6 不计入]；r22 首次 agreement
    计入的 2/3 里程碑与 r24 的 4/6 首计入维持不改写）；代表配置聚合 0.5、
    joint not_met、连续=0；criteria 四门布尔与 run 一致；in_calibrated_
    range 恒 False 多处一致+不得冒充留出；通道门 几何 0/类别 1/视角 0 对照
    在案。"""
    mile = dev["gt_agreement_milestone"]
    assert mile["gt_id"] == "GT-REVC-AP-1-R5U6"
    assert sorted(mile["hit_flags"]) == ["top-i4:R25T-005:applied"]
    assert mile["recall"] == {"agreement": 0.0, "union": 0.076923}
    assert "里程碑维持不改写" in mile["agreement_first_counted"]
    assert "首次计入" in mile["agreement_first_counted"]
    assert "结构性" in mile["structural_note"]
    assert dev["gt_audit_ref"] == run_doc["gt_audit_reference"]
    # 联合门与代表配置聚合
    diag = dev["diagnostic_result"]
    assert diag["abstain_rate_total"] == 0.5
    assert diag["gt_recall_total"] == 0.0
    assert diag["seed_match_rate_total"] == 0.0
    assert diag["joint_evaluation"] == "not_met"
    assert diag["gt_match_dual"]["union"]["count"] == 1
    assert diag["gt_match_dual"]["agreement"]["count"] == 0
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 58 and fp["non_abstain_count"] == 49
    trend = dev["joint_evaluation_trend"]
    assert trend["consecutive_met_count_now"] == 0
    assert trend["this_round"]["joint_evaluation"] == "not_met"
    # criteria 与 run 盘上件一致
    criteria = {c["id"]: c["met"] for c in diag["criteria"]}
    assert criteria == {"gt_count_ge_12": True, "gt_recall_ge_0.75": False,
                        "seed_match_rate_ge_0.5": False,
                        "abstain_rate_le_0.5": True}
    # in_calibrated_range 恒 False（总收束位+域基注记）与通道门对照
    closeout = dev["three_axis_experiment_closeout"]
    assert "恒 False" in closeout["development_domain_discipline"]
    assert "不得冒充留出" in dev["domain_basis_quote"]
    text = json.dumps(dev["directional_observation_vs_r16"],
                      ensure_ascii=False).replace("\n", "")
    assert "0→0→2→1→0" in text
    assert "→1（r25" in text
    gate = run_doc["channel_attribution"]["channel_2_category_gate"]
    assert len(gate["r25_category_mismatch_entries"]) == 1
    assert len(run_doc["channel_attribution"]["view_gate_observations"][
        "r25_entries"]) == 0


# ---------------------------------------------------------------------------
# 机制观察（逐实例分布/split-half 分解/三族对照/援引对照/条款行为观察）
# ---------------------------------------------------------------------------

def test_mechanism_observation_distribution_families_and_citations(dev):
    """机制观察单列：逐实例分布个体散跨越值域（top-i5=1.0 vs top-i6=
    0.142857）；split-half 分解=聚合亦移动（0.260377>0.09064、与 r24 反转）
    ；rubric 三族 r25（3/22/20）对照 r19（4/4/14）与 r22（2/4/12）与 r23
    （8/8/7）与 r24（4/28/44）四基线；top 分型 5/20/11；黑点弃权 22 全弃权
    （逐实例分旗）+黑点转非弃权旗 4；条款行为观察（三问援引率 22/24、弃权
    理由候选解释列举率 58/58）单列；援引计数对照 r19/r22/r23/r24 四基线
    （旗级 §5B=0/(iii-a)=11/分支(=0/条款=16+三问=13；notes 级 §5B=0/24、
    (iii-a)=12/24、§6=9/24、条款=24/24）。"""
    mo = dev["mechanism_observation_r25"]
    ido = mo["instance_distribution_observation"]
    assert ido["top_rates"]["top-i5"] == 1.0
    assert ido["top_rates"]["top-i6"] == 0.142857
    assert ido["m4_12_cell_range"] == 1.0
    assert "个体散" in ido["note"]
    assert ido["bottom_rates"]["bottom-i1"] is None  # 零旗格
    sh = mo["split_half_decomposition"]
    assert (sh["half_A"]["rate_6dp"], sh["half_B"]["rate_6dp"],
            sh["split_half_6dp"], sh["threshold_6dp"]) == \
        (339623, 600000, 260377, 90640)
    assert "聚合稳" in sh["note"] and "反转" in sh["note"]
    fam = mo["rubric_families_vs_baselines"]
    assert fam["r25_measured"] == {"contact": 3, "existence_blackdot": 22,
                                   "existence_other": 20}
    assert fam["r24_registered"] == {"contact": 4, "existence_blackdot": 28,
                                     "existence_other": 44}
    assert fam["r19_registered"] == {"contact": 4, "existence_blackdot": 4,
                                     "existence_other": 14}
    assert fam["r22_registered"] == {"contact": 2, "existence_blackdot": 4,
                                     "existence_other": 12}
    assert fam["r23_registered"] == {"contact": 8, "existence_blackdot": 8,
                                     "existence_other": 7}
    assert "度量教训" in fam["status"] and "不改字母" in fam["status"]
    ty = mo["top_abstain_typology_r25"]
    assert ty["counts"] == {"contact": 5, "existence": 20,
                            "other_layer": 11}
    assert "8/15/5/10" in ty["note"]
    bd = mo["black_dot_observation"]
    assert bd["by_instance"] == {"top-i1": 0, "top-i2": 0, "top-i3": 4,
                                 "top-i4": 2, "top-i5": 0, "top-i6": 0,
                                 "bottom-i1": 0, "bottom-i2": 4,
                                 "bottom-i3": 2, "bottom-i4": 4,
                                 "bottom-i5": 6, "bottom-i6": 0}
    assert "逐实例分旗" in bd["counts"] and "22 条" in bd["counts"]
    # 条款行为观察（本轮唯一新增判据变量的行为效应；单列不进字母）
    cbo = mo["clause_behavior_observation"]
    assert "22/24" in cbo["sanwen_citation_rate"]
    assert "58/58" in cbo["cand_explain_listing_rate"]
    assert "0.260377" in cbo["split_half_behavior"]
    assert "单列" in cbo["status"]
    # 援引计数对照 r19/r22/r23/r24 四基线（如实登记；多计数分开记）
    cc = mo["citation_counts_vs_r19_r22_r23_r24"]
    r19 = cc["r19_baseline_registered"]
    assert "6 旗" in r19["flag_level"] and "2 旗" in r19["flag_level"]
    assert "10/12" in r19["notes_level"]
    r22 = cc["r22_baseline_registered"]
    assert "旗级全 0" in r22["flag_level"]
    assert "6/12" in r22["notes_level"]
    r23 = cc["r23_baseline_registered"]
    assert "4/12" in r23["notes_level"]
    r24 = cc["r24_baseline_registered"]
    assert "8/24" in r24["notes_level"]
    r25 = cc["r25_measured"]
    assert r25["flag_level_s5b_literal"] == 0
    assert r25["flag_level_iiia_literal"] == 11
    assert r25["flag_level_branch_literal"] == 0
    assert r25["flag_level_clause_literal"] == 16
    assert r25["flag_level_sanwen_literal"] == 13
    assert "0/24 派次" in r25["notes_level_s5b"]
    assert "12/24 派次" in r25["notes_level_iiia"]
    assert "9/24 派次" in r25["notes_level_s6_clause"]
    assert "24/24 派次" in r25["notes_level_clause"]
    assert "22/24 派次" in r25["notes_level_sanwen"]
    assert "分开记" in cc["status"]


# ---------------------------------------------------------------------------
# 轮次身份/跳号声明延续/趋势行/结论锚/分包边界
# ---------------------------------------------------------------------------

def test_round_identity_skip_declaration_and_prefix_override(dev):
    """轮次身份声明：判据内容轴归因轮（s70/s80「机械变换派生」先例同型）、
    changed_variables=1（条款单变量=prep-record 实测核对）、机械派生
    （base=866b0157→derived=86af24dd、delta=937、基座只读零写入）、§6 前
    缀落盘固化（R25T-/R25B- 已在件、派发层命名与指引一致=无前缀差异登记
    需求）；跳号声明延续：r21=冻结计划未执行位（axis-plan 预留条件位、
    槽位永久留空、r22/r23/r24 跳号声明在案、r25 与该位无涉）；冻结原文引
    用=dev-r22 逐字继承。"""
    rid = dev["round_identity_declaration"]
    assert rid["changed_variables"] == 1
    gr = rid["guidance_reuse"]
    assert gr["mode"] == "mechanical_transform_derive"
    assert gr["base_sha256_prefix"] == "866b0157"
    assert gr["derived_sha256_prefix"] == "86af24dd"
    assert gr["byte_delta"] == 937
    assert gr["transform_base_untouched"] is True
    assert "三问" in rid["sole_variable"]
    assert "s80" in rid["precedent"]
    assert "R25T-" in rid["section6_prefix_override"]
    assert "前缀差异登记需求" in rid["section6_prefix_override"]
    assert "长度=1" in rid["changed_variables_note"]
    assert dev["round_nature"].startswith("development 域判据内容轴归因轮")
    # 跳号声明延续
    skip = dev["r21_skip_declaration"]
    assert skip["r21_status"] == "冻结计划未执行位（槽位永久留空）"
    assert "跳号" in skip["declaration"]
    assert "R21 不做" in skip["declaration"]
    assert "永久留空" in skip["declaration"]
    assert "r22 跳号声明在案" in skip["declaration"]
    assert "r23 跳号声明在案" in skip["declaration"]
    assert "r24 跳号声明在案" in skip["declaration"]
    quotes = skip["frozen_quotes"]
    dev22 = S90._json_load(S90.REL_DEV_R22)
    frozen = dev22["r21_skip_declaration"]["frozen_quotes"]
    assert quotes == frozen  # 与 dev-r22 在案引用逐字继承
    assert "R21（三轴全组合）" in quotes[
        "combination_decision_rule.ii_full_combination"]
    assert "R21 不做" in quotes["early_stop_rule."
                                "strong_single_axis_shortcut"]


def test_joint_trend_rows_r5_to_r25(dev):
    """联合评价趋势行：r5–r24 行=dev-r24 在案行冻结转录逐一相等+追加
    r25 行（代表配置口径实测：14/7/0.5、not_met、source=run-r25
    251102e8）；连续达标=0；聚合口径分列注记在案。"""
    trend = dev["joint_evaluation_trend"]["by_round"]
    assert [r["round"] for r in trend] == [
        "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13", "r14",
        "r15", "r16", "r17", "r18", "r19", "r20", "r22", "r23", "r24",
        "r25"]
    dev24 = S90._json_load(S90.REL_DEV_R24)
    prior = dev24["joint_evaluation_trend"]["by_round"]
    assert trend[:-1] == prior  # r5–r24 冻结转录
    row25 = trend[-1]
    assert (row25["flag_count_total"], row25["abstain_count_total"],
            row25["abstain_rate_total"]) == (14, 7, 0.5)
    assert row25["joint_evaluation"] == "not_met"
    assert row25["gt_recall_total"] == 0.0
    assert row25["matches_total"] == 0
    assert row25["seed_match_rate_total"] == 0.0
    assert row25["source"]["sha256"].startswith("251102e8")
    assert row25["round_id"] == ROUND_ID
    assert "r11–r25 行=代表配置口径" in \
        dev["joint_evaluation_trend"]["aggregation_scope_note"]


def test_honest_conclusion_next_targets_anchors_and_rerun_idempotent(dev):
    """honest 结论/下一目标关键锚+重跑语义：honest_conclusion 含字母裁
    决（not_criterion_dominated 唯一正式）、判据内容非主因+残余归因、
    split-half 聚合亦移动（与 r24 反转）、G2 链清零维持、GT union=1/13、
    九行台账、跳号、不得冒充留出、in_calibrated_range 恒 False；next_
    iteration_targets 五件组；s90 main 幂等重跑（盘上字节零改动）+s89
    分包边界（无 dev-record 构建函数、只产 run-r25；s90 只写
    round25-dev-record.json 一件）。"""
    hc = dev["honest_conclusion"]
    for anchor in ("not_criterion_dominated", "唯一正式裁决",
                   "not_criterion_dominated_m4_exceeds",
                   "0.433735", "0.261904", "0.09064",
                   "0.260377",
                   "判据内容非主因", "残余归因",
                   "聚合亦移动", "个体散",
                   "0.076923", "r25 第一", "不合并、不改写",
                   "不得冒充留出", "in_calibrated_range 恒 False",
                   "跳号", "conditional/double-entry",
                   "not_criterion_dominated_m4_exceeds"):
        assert anchor in hc, anchor
    nxt = dev["next_iteration_targets"]
    assert len(nxt) == 5
    assert "排序" in nxt[0] and "conditional/double-entry" in nxt[0]
    assert "(a)" in nxt[1] and "(b)" in nxt[1] and "(c)" in nxt[1]
    assert "其他输出侧" in nxt[1] and "第三样本" in nxt[1]
    assert "不得" in nxt[2] and "事后改判" in nxt[2]
    assert "留出集时机" in nxt[3] and "连续 2 轮达标" in nxt[3]
    assert "黑点族弃权 22" in nxt[4] and "类别门 r25=1" in nxt[4]
    # 重跑语义：main 幂等重跑（不抛异常）且盘上字节零改动；护栏对象=
    # s90 REL_OUT（v2 件），v2.1 件与 v2 件均零写入
    before = open(DEV_PATH, "rb").read()
    S90.main()
    assert open(DEV_PATH, "rb").read() == before  # v2.1 件零回写
    assert hashing.sha256_file(V2_PATH) == V2_SHA256  # v2 原件字节零变化
    assert hashing.sha256_file(DEV_PATH) == V21_SHA256
    # 分包边界：s89 零 dev-record 写入（只产 run-r25）；s90 只写本件
    path89 = os.path.join(REPO, "scripts", "s89_calibration_r25_compare.py")
    spec = importlib.util.spec_from_file_location(
        "s89_probe_pkg", path89)
    s89 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s89)
    assert not hasattr(s89, "build_dev_record")
    assert hasattr(s89, "build_run")
    assert hasattr(S90, "build_dev_record")
