"""R23 收口包 B 测试（s83_calibration_r23_devrecord /
round23-dev-record.json）——轮次开发记录生成器（s78 底稿同构）：
单变量报告框收敛归因轮（输出格式/报告纪律轴；第二十三轮）：判读指引=
observation-guidance-r23.md（866b0157 锚、由 r19 基座 8633bda5 机械变换
派生[s48/s54/s63/s67/s70 先例同型]、§6 报告框收敛条款随指引落盘固化、
§6 示例前缀 R23T-/R23B- 即落盘原文=派发命名与指引一致、变换基座零字节
不动）+渲染零变更=renders-r14b 四图字节复用+GT/阈值/协议零变更；
changed_variables=1（§6 条款单变量；实例群重抽=轮际固有混杂非实验操
作）；【跳号声明延续】r21=axis-plan 冻结件预留的 R21 全组合条件位（槽位
永久留空、dev-r20 已登记「R21 不做」、r22 跳号声明在案、r23 与该位无
涉）。预注册假设（r22-g2-bifurcation-frame-box-hygiene-attribution）归
因三支判据轮后裁决=confounded（字母口径，唯一正式裁决，轮后不改写）：
(c) 支命中=confounded_g2_positive_in_band（G2=top 几何门面积比出局条目
r19=0→r22=2→r23=1 仍>0 未清零；且 M1=0.484848（16/33）落复制带
[0.361538, 0.561538] 内）——框宽非（唯一）主因，归因转向（判据内容/实
例群/其他输出侧因素混杂主导）。机制侧如实分列：r22 型 silk 宽框出局条
目（R22T-002/013，area_ratio≈16.4）未再现=框收敛条款对目标起效；但新
出局条目 R23T-004=other_advisory 合并铜块（11.458680>10、机制不同）=
几何门未全局清零——分岔如实登记（g2_bifurcation_record 延续单列，照
r20 g1_bifurcation_record/r22 g2_bifurcation_record 先例=b4b8fbe9 在
案）：字母=confounded 与「条款对目标起效」事实=机制观察，两账分列、不
合并、不改写（反事实构造：G2 清零⇒replicated_hygiene）；G1=bottom
courtyard 非弃权 0/0/0 维持；guidance-r19 胜出记录维持 conditional/
double-entry 现状、复制未达成不升级；r22 字母=regressed 维持不改写。
机制观察单列：M4 三样本（r19=0.211111 未过 0.20 门[差 0.011111 在案] vs
r22=0.104545 过门 vs r23=0.520833 未过门；不进字母、不合并分布、不挑
优）；rubric 三族 contact 8/existence_blackdot 8/existence_other 7（+
semantic_confusion 1）对照 r19（4/4/14）与 r22（2/4/12）——黑点 8 高于
双基线（§6 逐实例分旗行为+实例群异质性）=度量教训不改字母；援引计数
对照 r19/r22 双基线（r19=旗级 6+2、notes 10/12 在案；r22=旗级全 0、
notes 6/12 在案；r23=旗级全 0、notes §5B=0/12、(iii-a)=4/12、§6 条款=
6/12）；落支=间隙 4+侵入 5+残余弃权 14。GT：union=2/13=0.153846
（GT-REVC-P1-R4J3 R23T-002+GT-REVC-P1-L1SHORT R23T-011，均单实例命中）；
agreement=0/13（r22 首次 agreement 计入的双实例一致命中未复现=单实例
命中不稳定如实登记、r22 里程碑维持不改写）；通道门 几何 1/类别 1/视角 0
对照 r19（0/2/0）与 r20（0/0/0）与 r22（2/4/1）。联合门 not_met、连续=
0、in_calibrated_range 恒 False 照常。三轴实验总收束位：comparison_
rule 排序不变（r19_axis3 第一）；r23 不入排序（G2 破坏）；guidance-r19
胜出记录维持 conditional/double-entry 现状；发展域证据不得冒充留出。下
一候选建议三选项（由用户拍板、本包不预写决策）：(a) 接受发展域现状收束
训练环+留出集时机用户判断；(b) 对剩余混杂（判据内容/实例群/其他输出侧
因素）做新预注册轮归因；(c) 同指引重复轮（第三样本）。

覆盖（14 测试，只读 out/、零子进程/零网络；s83 幂等重跑例外=护栏语义
在案、字节零改动）：
- 防覆盖守卫：overwrite_guard 三态+_commit 写入/幂等/不同字节 FAIL；
- canonical 确定性（盘上件=同参重建 byte-exact）+轮次身份+is_gate
  False；
- 受保护文件全 64 位锚+引用件哈希清单 12 件（run-r23=15f58350/
  prep-r23=3c42ace7/guidance-r23=866b0157/guidance-r19 基座=8633bda5/
  run-r19=e5755a11/run-r20=6573a59a/run-r22=80a12c05/dev-r19=0e2fdd69/
  dev-r20=80e3e9e2/dev-r22=b4b8fbe9/axis-plan=b6ec6467/typology=
  6dadac8d 盘上实测）+预注册链冻结工件逐件实测；
- 字母裁决=confounded 落支与判据布尔（confounded=True、其余三支=False）
  与预注册判据摘录逐字一致；
- 归因结论逻辑纯函数构造（G2=0 时=replicated_hygiene；G2>0 带内=
  confounded/perturbed 出带/guard_violation G1 破坏/带端点）；
- M 元组与 run 一致（构造对照：七行并列、M1 交叉相乘带内、M4 极差、
  M3=rubric 计数、显著收益降幅、r19/r22 参照元组）；
- g2_bifurcation_record 延续引用（r22 dev-record=b4b8fbe9 在案）+双账
  分列（letter_vs_fact/反事实构造/1 条出局条目逐条摘录与 run 通道归因
  逐一相等+r22 两条对照）；
- 三轴实验总收束位（排序不变=r19 第一、r23/r22/r20 资格门剔除、归因状
  态两账并列、发展域不得冒充留出）；
- 下一候选建议（三选项/用户拍板/预注册要求）；
- GT 双口径 union=2/13+agreement=0+联合门+in_calibrated_range 恒
  False+通道门 1/1/0 对照；
- 机制观察（M4 三样本未过门事实/三族对照/援引对照 r19/r22 双基线/top
  分型/黑点分旗）；
- 轮次身份声明（changed_variables=1/机械变换派生/§6 前缀一致性）+跳号
  声明延续（r21 冻结槽位原文=dev-r22 逐字继承）；
- 趋势行 r5–r23（dev-r22 冻结转录+r23 实测行）；
- honest 结论/下一目标关键锚+s83 幂等重跑+s82 分包边界。
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

ROUND_ID = "2026-09-10-r23"
ROUND_LABEL = "r23"
DECLARED_DATE = "2026-09-10"

# DEV-E0-004 追加式锚修复：盘上件指向 v2 追加件（与 r1 冻结件差异恰=
# cli.py 保护锚 6ed4f3fd→0a738047，铜环案接纳；r1 零回写、sha 前缀
# 343a6747 由 v2 件前缀 0dae60fb 接替）。
# RE-REGISTRATION D2（RE-REGISTRATION-ADJUDICATION-2026-09-13）：盘上件
# 改指 v2.1 修正件（=v2 全字段原值+kind 后缀/supersedes/双值披露三要素；
# v2 件零回写，其字节由 V2_SHA256 全长钉死=负向断言）；s83 重建=v2
# payload（无三要素字段），盘上对拍改为「三要素掩码还原后=v2 字节」。
V2_PATH = os.path.join(CAL_DIR, "round23-dev-record-v2.json")
V2_SHA256 = ("0dae60fb9121a39dac160412260be34abb64348ca5c395fc8235"
             "3f1759a6e4e9")
V21_KIND = "tl2_calibration_round23_dev_record_v2_1"
V21_SHA256 = ("66c722ee25d9206e98e38970ca6873743f90fce155c37415e8745"
              "6ee9800a5ca")
DEV_PATH = os.path.join(CAL_DIR, "round23-dev-record-v2_1.json")
_V21_PROVENANCE_KEYS = ("anchor_amendment", "supersedes")


def _load_s83():
    path = os.path.join(REPO, "scripts", "s83_calibration_r23_devrecord.py")
    spec = importlib.util.spec_from_file_location("s83_calibration_r23_dev",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S83 = _load_s83()


# REPAIR-P4 W-1（G0）：config.py 经用户授权变更（f515c348→acdfac49，登记=
# out/repair-p4/anchor-hashes-post-g0.json）。历史脚本 s83 与盘上发布件冻结不动
# （W-2 红线，证据生成器）。测试侧双层锚定：
# 1) verify 红线按现役锚执行（want=7b4974d8=实测，零改动护栏语义不弱化）；
# 2) dev-record 的 protected 展示段按历史锚语境回放（before=f515c348）——
#    record 其余内容全实测复算，重建才能与盘上冻结发布件 byte-exact
#    （防覆写护栏/盘上件身份测试的历史重放口径）。
S83.PROTECTED_FILES["pcbflow/config.py"] = (
    "8ad12b3fab12f19546034b5421aa77053f4115b91b36b87b9dfabc9075fdcf82")  # G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
# REPAIR-G1+ W-1/W-2（2026-09-24）：cli.py 授权变更 0a738047->3bfc9407
#（登记=out/repair-g1plus-r1/anchor-hashes-post-g1plus.json）——同构双层：
S83.PROTECTED_FILES["pcbflow/cli.py"] = (
    "3bfc940701d1be82029877583a0a41f49741228f2e89a321b7dafa98d179aae8")
_orig_vpf_s83 = S83.verify_protected_files


def _vpf_g0_legacy_s83():
    got = _orig_vpf_s83()
    got["pcbflow/config.py"] = (
        "f515c34842521a645145a9f5454a5919274a242e5c8c27c01faf1a4c13e73baf")
    got["pcbflow/cli.py"] = "0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e"
    return got


S83.verify_protected_files = _vpf_g0_legacy_s83


@pytest.fixture(scope="module")
def dev():
    """round23-dev-record 内存重建（纯函数；只读输入、零写盘）。"""
    return S83.build_dev_record()


@pytest.fixture(scope="module")
def run_doc():
    """run-r23 盘上件装载（只读）。"""
    return S83._json_load(S83.REL_RUN_R23)


# ---------------------------------------------------------------------------
# 守卫与确定性
# ---------------------------------------------------------------------------

def test_overwrite_guard_and_commit_semantics(tmp_path):
    """防覆盖守卫三态：无既有→write；字节等同→idempotent_skip；既有且
    不同→fail；_commit=写入/幂等跳过/不同字节 SystemExit（fail-closed，
    绝不覆写）。"""
    assert S83.overwrite_guard(None, b"abc") == "write"
    assert S83.overwrite_guard(b"abc", b"abc") == "idempotent_skip"
    assert S83.overwrite_guard(b"abc", b"xyz") == "fail"
    p = tmp_path / "probe.json"
    assert S83._commit(p, b"abc", "probe") == "written"
    assert p.read_bytes() == b"abc"
    assert S83._commit(p, b"abc", "probe") == "idempotent_skip"
    p.write_bytes(b"xyz")
    with pytest.raises(SystemExit):
        S83._commit(p, b"abc", "probe")


def test_devrecord_canonical_determinism_and_disk_identity(dev):
    """round23-dev-record 盘上件：同参重建两次 byte-exact+盘上件=
    canonical 重建+kind/轮次身份（r23/2026-09-10/development 域）+
    schema_version+is_gate=False+run_record_ref=15f58350+
    hypothesis_test_i=run 内嵌件原样。"""
    b1 = hashing.canonical_json_bytes(S83.build_dev_record())
    b2 = hashing.canonical_json_bytes(S83.build_dev_record())
    assert b1 == b2  # 同参重建 byte-exact
    raw = open(DEV_PATH, "rb").read()
    doc = json.loads(raw)
    payload = {k: v for k, v in doc.items()
               if k not in _V21_PROVENANCE_KEYS}
    payload["kind"] = dev["kind"]  # 三要素掩码还原=v2 payload（历史字段冻结）
    assert hashing.canonical_json_bytes(payload) == b1  # 盘上件 payload=canonical 重建
    assert doc["kind"] == V21_KIND  # v2.1 kind 显式后缀（§4.5 要素 1）
    assert doc["supersedes"]["path_rel"] == \
        "out/v3-tl2/calibration/round23-dev-record-v2.json"
    assert doc["supersedes"]["sha256"] == V2_SHA256  # §4.5 要素 2
    assert doc["anchor_amendment"]["old_value"] != \
        doc["anchor_amendment"]["new_value"]  # §4.5 要素 3（双值披露）
    # 负向断言：v2 原件字节零变化（零回写）
    assert hashing.sha256_file(V2_PATH) == V2_SHA256
    assert hashing.sha256_file(DEV_PATH) == V21_SHA256
    assert dev["kind"] == "tl2_calibration_round23_dev_record"
    assert dev["round_id"] == ROUND_ID
    assert dev["round_label"] == ROUND_LABEL
    assert dev["declared_date"] == DECLARED_DATE
    assert dev["schema_version"] == "3.0"
    assert dev["evaluation_domain"] == "development"
    assert dev["is_gate"] is False
    assert dev["run_record_ref"]["path_rel"] == \
        "out/v3-tl2/calibration/calibration-run-r23.json"
    assert dev["run_record_ref"]["sha256"] == S83._sha(S83.REL_RUN_R23)
    assert dev["run_record_ref"]["sha256"].startswith("15f58350")
    assert dev["hypothesis_test_i"]["verdict"] == "confounded"
    assert dev["hypothesis_test_i"]["hypothesis_id"] == \
        "r22-g2-bifurcation-frame-box-hygiene-attribution"


def test_protected_files_reference_hash_manifest_and_chain(dev):
    """受保护文件全 64 位锚（cli/config/toolchain_lock）在件且与盘上实
    测逐一相等；引用件哈希清单 12 件（run-r23=15f58350/prep-r23=
    3c42ace7/guidance-r23=866b0157/guidance-r19 基座=8633bda5/run-r19=
    e5755a11/run-r20=6573a59a/run-r22=80a12c05/dev-r19=0e2fdd69/dev-r20=
    80e3e9e2/dev-r22=b4b8fbe9/axis-plan=b6ec6467/typology=6dadac8d）逐
    件 live sha256_file 实测与前缀逐一相等；预注册链（run 冻结工件）逐
    件实测 sha 与登记逐一相等（协议/prep-r23/axis-plan/dev-r22/guidance-
    r23 派生锚/GT 两代/gt-audit 在链）。"""
    protected = dev["protected_files_verification"]
    assert protected["role"] == "红线 1 执行证据"
    for rel, want in S83.PROTECTED_FILES.items():
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
        "run_r23": "15f58350",
        "prep_r23": "3c42ace7",
        "guidance_r23": "866b0157",
        "guidance_r19_base": "8633bda5",
        "run_r19": "e5755a11",
        "run_r20": "6573a59a",
        "run_r22": "80a12c05",
        "dev_r19": "0e2fdd69",
        "dev_r20": "80e3e9e2",
        "dev_r22": "b4b8fbe9",
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
    # 预注册链（含哈希）：逐件实测与登记一致
    chain = dev["preregistration_chain"]
    for role in ("evaluation_protocol",
                 "r23_prep_record_preregistration",
                 "r22_dev_record_clause_design_basis_and_candidate_b",
                 "axis_experiment_plan_r17_r20_frozen",
                 "observation_guidance_r23_active_derived",
                 "observation_guidance_r19_transform_base",
                 "gt_seed_prep1", "gt_expansion_applied",
                 "gt_audit_r1_closed"):
        assert role in chain, role
        item = chain[role]
        assert hashing.sha256_file(
            os.path.join(REPO, item["path_rel"])) == item["sha256"], role
    assert chain["observation_guidance_r23_active_derived"][
        "sha256"].startswith("866b0157")
    assert chain["observation_guidance_r19_transform_base"][
        "sha256"].startswith("8633bda5")
    note = dev["preregistration_chain_note"]
    assert "机械变换派生" in note and "15f58350" in note
    assert "3c42ace7" in note and "b4b8fbe9" in note


# ---------------------------------------------------------------------------
# 字母裁决与归因结论逻辑（纯函数构造）
# ---------------------------------------------------------------------------

def test_letter_verdict_branch_and_criteria_booleans(dev, run_doc):
    """字母裁决=confounded（唯一正式裁决）：落支=(c) confounded_g2_
    positive_in_band（G2 未清零且 M1 带内）；判据布尔（confounded=True、
    guard_violation=False、perturbed=False、replicated_hygiene=False）与
    run 盘上件逐一相等；预注册判据摘录=prep-record 原文（6 键逐字一
    致）。"""
    ht = dev["hypothesis_test_i"]
    m = ht["measurement"]
    assert ht["verdict"] == "confounded"
    assert m["verdict"] == "confounded"
    assert m["letter_branch"].startswith("(c)")
    assert "G2 出局条目仍 >0" in m["letter_branch"]
    assert "框宽非（唯一）主因" in m["letter_branch"]
    assert m["crit_confounded"] is True
    assert m["crit_guard_violation"] is False
    assert m["crit_perturbed"] is False
    assert m["crit_replicated_hygiene"] is False
    # 与 run 盘上件逐一相等（dev-record 内嵌=run 原文）
    rm = run_doc["hypothesis_test"]["measurement"]
    assert m["letter_branch"] == rm["letter_branch"]
    assert ht["verdict_text"] == run_doc["hypothesis_test"]["verdict_text"]
    # 判据原文摘录=prep-record adjudication 逐字一致
    prep = S83._json_load(S83.REL_PREP_R23)
    adj = prep["hypothesis_test"]["adjudication"]
    q = ht["preregistered_criteria_quote"]
    for k in ("confounded", "descriptive_boundary_note",
              "mechanism_observation_separate", "metric_lesson_separate",
              "perturbed", "replicated_hygiene"):
        assert q[k] == adj[k], k


def test_attribution_conclusion_logic_pure_function(dev):
    """归因结论逻辑纯函数（构造）：实际输入 (1,True,16,33)=confounded=
    登记裁决；反事实构造：G2=0 时同一输入=replicated_hygiene（分岔两
    侧）；M1 出带（5/33 与 361539/10^6）=perturbed；G1 破坏=guard_
    violation（支序最高）；带端点（恰=下沿/上沿入带）；6 位定点常量与
    判据原文同锚。dev-record 反事实构造注记与纯函数一致。"""
    assert S83.attribution_verdict_fixed_point(1, True, 16, 33) == \
        ("confounded", "confounded_g2_positive_in_band")
    assert S83.attribution_verdict_fixed_point(0, True, 16, 33) == \
        ("replicated_hygiene", "replicated_hygiene")
    assert S83.attribution_verdict_fixed_point(1, True, 5, 33) == \
        ("perturbed", "perturbed_m1_out_of_band")
    assert S83.attribution_verdict_fixed_point(1, False, 16, 33) == \
        ("guard_violation", "guard_violation_g1")
    # 带端点（恰=下沿/上沿入带）
    assert S83.attribution_verdict_fixed_point(0, True, 361538,
                                               1000000) == \
        ("replicated_hygiene", "replicated_hygiene")
    assert S83.attribution_verdict_fixed_point(2, True, 561538,
                                               1000000) == \
        ("confounded", "confounded_g2_positive_in_band")
    assert S83.attribution_verdict_fixed_point(1, True, 361537,
                                               1000000) == \
        ("perturbed", "perturbed_m1_out_of_band")
    assert S83.attribution_verdict_fixed_point(1, True, 561539,
                                               1000000) == \
        ("perturbed", "perturbed_m1_out_of_band")
    # 6 位定点常量与 s82/判据原文同锚
    assert (S83.REPL_BAND_LO_6DP, S83.REPL_BAND_HI_6DP) == \
        (361_538, 561_538)
    # dev-record 反事实构造注记与纯函数一致
    cf = dev["g2_bifurcation_record"]["counterfactual_check"]
    assert cf["g2_positive_in_band"] == ["confounded",
                                         "confounded_g2_positive_in_band"]
    assert cf["g2_0_in_band"] == ["replicated_hygiene",
                                  "replicated_hygiene"]
    assert cf["m1_out_of_band"] == ["perturbed", "perturbed_m1_out_of_band"]
    assert cf["guards_ok_false"] == ["guard_violation",
                                     "guard_violation_g1"]


# ---------------------------------------------------------------------------
# M 元组与 run 一致（构造对照）
# ---------------------------------------------------------------------------

def test_m_tuple_matches_run_constructed_cross_check(dev, run_doc):
    """M 元组与 run 一致（构造对照）：axis ledger 本轮行=(0.484848, 0.
    571429, 8, 0.520833)=run r23_m_tuple_6dp；构造交叉相乘带内判定
    （16×10^6 ∈ [361538×33, 561538×33]）、M4=0.6875−0.166667、M3=8=run
    黑点族 rubric 计数；七行并列完整（r16 基线/r17/r18/r19/r20/r22/r23，
    前六行=dev-r22 台账继承）；r19/r22 参照元组=run 登记值；显著收益降
    幅 0.286581 整数交叉相乘复核。"""
    rows = dev["axis_experiment_ledger"]["cross_round_status"][
        "measured_rows"]
    this = dev["axis_experiment_ledger"]["this_round_measured"]
    run_m = run_doc["hypothesis_test"]["measurement"]["r23_m_tuple_6dp"]
    assert this == {"M1": 0.484848, "M2": 0.571429, "M3": 8, "M4": 0.520833}
    assert rows["r23_attribution"] == run_m
    assert rows["r23_attribution"]["M1"] == 0.484848
    # 构造对照：6 位定点整数交叉相乘
    assert S83.REPL_BAND_LO_6DP * 33 <= 16 * 1_000_000
    assert 16 * 1_000_000 <= S83.REPL_BAND_HI_6DP * 33
    assert round(0.6875 - 0.166667, 6) == 0.520833
    bdt = run_doc["hypothesis_test"]["mechanism_observation"][
        "black_dot_tracking"]
    assert bdt["rubric_families"]["counts"]["existence_blackdot"] == \
        rows["r23_attribution"]["M3"] == 8
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
    assert run_doc["hypothesis_test"]["measurement"][
        "r19_reference_tuple"] == rows["r19_axis3"]
    assert run_doc["hypothesis_test"]["measurement"][
        "r22_reference_tuple_live"] == rows["r22_repeat"]
    sb = dev["axis_experiment_ledger"]["significant_benefit_vs_r16"]
    assert sb["r23_m1_absolute_drop"] == 0.286581
    assert round(0.771429 - 0.484848, 6) == 0.286581
    assert (27 * 33 - 16 * 35) * 1_000_000 >= 100_000 * 35 * 33


# ---------------------------------------------------------------------------
# G2 分岔专节（延续引用+双账分列+出局条目摘录）
# ---------------------------------------------------------------------------

def test_g2_bifurcation_record_continuation_and_entries(dev, run_doc):
    """g2_bifurcation_record 字段存在且含分叉记账模式延续引用（r22
    dev-record=b4b8fbe9 g2_bifurcation_record 在案）+双账分列：
    letter_vs_fact（字母=confounded 唯一正式裁决不改写 vs 条款对目标起
    效=机制观察单列）+counts（M1 带内/G1 维持/G2 0→2→1/silk 宽框未再现
    =0）+1 条出局条目逐条摘录（旗 id/类别/area_ratio/对应现象）与 run
    通道归因实测逐一相等+run 侧 comparison_to_r22 两条 silk 宽框对照在
    案；照 r20 g1_bifurcation_record 先例命名（dev-r20 在案）。"""
    g2 = dev["g2_bifurcation_record"]
    assert "g2_bifurcation_record" in dev
    lvf = g2["letter_vs_fact"]
    assert "confounded" in lvf["letter"] and "不改写" in lvf["status"]
    assert "11.458680" in lvf["clause_effect_fact"]
    assert "两账分列" in lvf["status"]
    counts = g2["counts"]
    assert counts["g2_geometry_gate_r19"] == 0
    assert counts["g2_geometry_gate_r22"] == 2
    assert counts["g2_geometry_gate_r23"] == 1
    assert counts["m1_in_replication_band"] is True
    assert counts["s6_clause_target_silk_wide_box_recurrance"] == 0
    assert counts["contact_family_abstain_flags_rubric_r23"] == 8
    assert counts["g1_bottom_courtyard_non_abstain_r23"] == \
        {"bottom-i1": 0, "bottom-i2": 0, "bottom-i3": 0}
    assert counts["replication_band"] == "[0.361538, 0.561538]（r19±0.10）"
    assert "未清零" in g2["bifurcation"] or "框宽非" in g2["bifurcation"]
    assert "单列" in g2["role"] and "不改写" in g2["role"]
    # 延续引用：r22 dev-record=b4b8fbe9 在案 + 其 g2_bifurcation_record
    cont = g2["continuation"]["round22_dev_record"]
    assert cont["path_rel"] == \
        "out/v3-tl2/calibration/round22-dev-record.json"
    assert cont["sha256"].startswith("b4b8fbe9")
    assert "g2_bifurcation_record" in cont["section"]
    dev22 = S83._json_load(S83.REL_DEV_R22)
    assert "g2_bifurcation_record" in dev22
    # 1 条出局条目逐条摘录与 run 通道归因逐一相等（含对应现象）
    gate_entries = run_doc["channel_attribution"]["channel_1_geometry_gate"][
        "r23_area_ratio_rejected_entries"]
    excerpt = g2["rejected_entries_excerpt"]
    assert [e["flag_id"] for e in excerpt] == ["R23T-004"]
    for want, expect_e, run_e in zip(excerpt, S83.EXPECT_G2_REJECTED_ENTRIES,
                                     gate_entries):
        assert want["flag_id"] == run_e["flag_id"] == "R23T-004"
        assert want["category"] == run_e["category"] == "other_advisory"
        assert want["area_ratio"] == run_e["area_ratio"] == 11.45868
        assert want["area_ratio"] > 10
        assert want["gt_id"] == run_e["gt_id"] == "GT-REVC-P1-L1SHORT"
        assert want["instance"] == run_e["instance"] == "top-i3"
        assert want["state"] == run_e["state"] == "prep1"
        assert want["corresponding_phenomenon"] == expect_e["phenomenon"]
        assert len(want["corresponding_phenomenon"]) > 10
        assert "location_evidence" in want["phenomenon_source"]
    # r22 两条 silk 宽框对照（类别/现象/机制均不同）在 run 机制观察侧
    cmp22 = run_doc["hypothesis_test"]["mechanism_observation"][
        "g2_rejected_entries_r23"]["comparison_to_r22"]
    assert [e["flag_id"] for e in cmp22["r22_entries"]] == \
        ["R22T-002", "R22T-013"]
    assert all(e["category"] == "silk_readability"
               for e in cmp22["r22_entries"])
    # 先例血统：run-r20 的 g1_bifurcation_record 同型（dev-r20 在案）
    dev20 = S83._json_load(S83.REL_DEV_R20)
    assert "g1_bifurcation_record" in dev20


def test_three_axis_closeout_ranking_unchanged_and_attribution(dev, run_doc):
    """三轴实验总收束位：comparison_rule 排序不变（r19_axis3 第一/r18/
    r16 参照/r17 末位）；r23 不入排序（G2 破坏=资格门剔除、行仅如实入
    账）与 r22/r20 并列排除位；guidance-r19 胜出记录维持 conditional/
    double-entry 现状、复制未达成不升级（replicated_hygiene 支不命中）；
    发展域证据不得冒充留出；最终结论维持=guidance-r19（轴3 单变量）。"""
    closeout = dev["three_axis_experiment_closeout"]
    rk = closeout["ranking"]
    assert rk["ranking_order_best_first"] == ["r19_axis3", "r18_axis2",
                                              "r16_baseline", "r17_axis1"]
    assert rk["eligible_rows"] == ["r16_baseline", "r17_axis1",
                                   "r18_axis2", "r19_axis3"]
    assert "G2 破坏" in rk["excluded_rows"]["r23_attribution"]
    assert "G2 破坏" in rk["excluded_rows"]["r22_repeat"]
    assert "G1 破坏" in rk["excluded_rows"]["r20_combo"]
    assert "排序不变" in rk["status"] and "不入排序" in rk["status"]
    att = closeout["attribution_status_axis3_benefit"]
    assert "conditional/double-entry" in att
    assert "不升级" in att and "confounded" in att
    assert "两账并列" in att and "不合并" in att and "不" in att
    assert "不得冒充" in closeout["development_domain_discipline"]
    assert "恒 False" in closeout["development_domain_discipline"]
    assert "轴3 单变量" in closeout["final_conclusion_unchanged"]
    assert "guidance-r19" in closeout["final_conclusion_unchanged"]
    # 与 run 盘上对照账排序一致（fail-closed）
    rk_run = run_doc["hypothesis_test"]["mechanism_observation"][
        "experiment_comparison_ledger"]["ranking_by_comparison_rule"]
    assert rk_run["ranking_order_best_first"] == \
        rk["ranking_order_best_first"]
    assert rk_run["r23_eligibility"] is False


# ---------------------------------------------------------------------------
# 下一候选建议（三选项、用户拍板）
# ---------------------------------------------------------------------------

def test_next_candidate_suggestion_three_options(dev):
    """下一候选建议：恰三选项（(a) 接受发展域现状收束训练环+留出集时机
    由用户判断；(b) 对剩余混杂（判据内容/实例群/其他输出侧因素）做新预注
    册轮归因；(c) 再一轮同指引重复轮三样本）；决策权=用户拍板、本包不预
    写决策；(b)(c) 须预注册、(a) 不须。"""
    sug = dev["next_candidate_suggestion"]
    options = sug["options"]
    assert len(options) == 3
    a, b, c = options
    assert "收束训练环" in a["option"] and "留出集" in a["option"]
    assert a["preregistration_required"] is False
    assert "剩余混杂" in b["option"] and "判据内容" in b["option"]
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
    """GT 双口径 union=2/13=0.153846（GT-REVC-P1-R4J3 R23T-002+GT-REVC-
    P1-L1SHORT R23T-011，均单实例命中）、agreement=0/13（r22 首次
    agreement 计入的双实例一致命中未复现=单实例命中不稳定如实登记、里
    程碑维持不改写）；代表配置聚合 0.125、joint not_met、连续=0；criteria
    四门布尔与 run 一致；in_calibrated_range 恒 False 多处一致+不得冒充
    留出；通道门 几何 1/类别 1/视角 0 对照在案。"""
    mile = dev["gt_agreement_milestone"]
    assert "R4J3" in mile["gt_id"] and "L1SHORT" in mile["gt_id"]
    assert sorted(mile["hit_flags"]) == ["top-i2:R23T-011:prep1",
                                         "top-i3:R23T-002:prep1"]
    assert mile["recall"] == {"agreement": 0.0, "union": 0.153846}
    assert "里程碑维持不改写" in mile["agreement_first_counted"]
    assert "单实例命中" in mile["agreement_first_counted"]
    assert "结构性" in mile["structural_note"]
    assert dev["gt_audit_ref"] == run_doc["gt_audit_reference"]
    # 联合门与代表配置聚合
    diag = dev["diagnostic_result"]
    assert diag["abstain_rate_total"] == 0.125
    assert diag["gt_recall_total"] == 0.076923
    assert diag["seed_match_rate_total"] == 0.071429
    assert diag["joint_evaluation"] == "not_met"
    assert diag["gt_match_dual"]["union"]["count"] == 2
    assert diag["gt_match_dual"]["agreement"]["count"] == 0
    fp = dev["flag_production"]
    assert fp["abstain_count"] == 24 and fp["non_abstain_count"] == 23
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
    assert "0→0→2→1" in text
    assert "视角门 0→0→1→0" in text
    assert "→1（r23" in text
    gate = run_doc["channel_attribution"]["channel_2_category_gate"]
    assert len(gate["r23_category_mismatch_entries"]) == 1
    assert len(run_doc["channel_attribution"]["view_gate_observations"][
        "r23_entries"]) == 0


# ---------------------------------------------------------------------------
# 机制观察（M4 三样本/三族对照/援引对照/黑点分旗）
# ---------------------------------------------------------------------------

def test_mechanism_observation_m4_families_and_citations(dev):
    """机制观察单列：M4 三样本（r19=0.211111 未过 0.20 门[差 0.011111
    在案] vs r22=0.104545 过门 vs r23=0.520833 未过门；不进字母、不合并
    分布、不挑优）；rubric 三族 r23（8/8/7）对照 r19（4/4/14）与 r22
    （2/4/12）双基线——黑点 8 高于双基线；top 分型 6/10/0；黑点弃权 8
    全弃权（top-i1 4+bottom-i1 4、逐实例分旗）+黑点转非弃权旗 8；援引计
    数对照 r19/r22 双基线（旗级全 0、notes §5B=0/12、(iii-a)=4/12、§6=
    6/12；落支 间隙 4+侵入 5+残余弃权 14）；§6 条款行为观察（对目标起效
    +未清零）在件。"""
    mo = dev["mechanism_observation_r23"]
    m4 = mo["m4_third_sample"]
    assert (m4["r19"], m4["r22"], m4["r23"]) == \
        (0.211111, 0.104545, 0.520833)
    assert m4["r19_pass_gate"] is False
    assert m4["r22_pass_gate"] is True
    assert m4["r23_pass_gate"] is False
    assert m4["supported_gate"] == 0.2
    assert "0.011111" in m4["note"]
    assert "不进字母" in m4["note"] and "不合并分布" in m4["note"]
    fam = mo["rubric_families_vs_baselines"]
    assert fam["r23_measured"] == {"contact": 8, "existence_blackdot": 8,
                                   "existence_other": 7,
                                   "semantic_confusion": 1}
    assert fam["r19_registered"] == {"contact": 4, "existence_blackdot": 4,
                                     "existence_other": 14}
    assert fam["r22_registered"] == {"contact": 2, "existence_blackdot": 4,
                                     "existence_other": 12}
    assert "度量教训" in fam["status"] and "不改字母" in fam["status"]
    assert mo["top_abstain_typology_r23"]["counts"] == \
        {"contact": 6, "existence": 10, "other_layer": 0}
    assert "8/15/5/10" in mo["top_abstain_typology_r23"]["note"]
    bd = mo["black_dot_observation"]
    assert bd["by_instance"] == {"bottom-i1": 4, "bottom-i2": 0,
                                 "bottom-i3": 0, "top-i1": 4,
                                 "top-i2": 0, "top-i3": 0}
    assert "逐实例分旗" in bd["counts"] and "8 条" in bd["counts"]
    assert "R22T-004" in bd["s6_clause_disaggregation_observation"]
    assert "合旗" in bd["s6_clause_disaggregation_observation"]
    # 援引计数对照 r19/r22 双基线（如实登记；三计数分开记）
    cc = mo["citation_counts_vs_r19_r22"]
    r19 = cc["r19_baseline_registered"]
    assert "6 旗" in r19["flag_level"] and "2 旗" in r19["flag_level"]
    assert "10/12" in r19["notes_level"]
    r22 = cc["r22_baseline_registered"]
    assert "旗级全 0" in r22["flag_level"]
    assert "6/12" in r22["notes_level"]
    r23 = cc["r23_measured"]
    assert r23["flag_level_s5b_literal"] == 0
    assert r23["flag_level_iiia_literal"] == 0
    assert r23["flag_level_branch_literal"] == 0
    assert "0/12 派次" in r23["notes_level_s5b"]
    assert "4/12 派次" in r23["notes_level_iiia"]
    assert "6/12 派次" in r23["notes_level_s6_clause"]
    assert r23["branch_counts_flag_level"] == \
        {"branch1_gap_report": 4, "branch2_intrusion_report": 5,
         "branch3_residual_abstain": 14}
    assert "分开记" in cc["status"]
    # §6 条款行为观察（本轮唯一实验变量的机制观察）
    fbo = mo["frame_box_convergence_observation"]
    assert "未再现" in fbo and "未全局清零" in fbo
    assert "11.458680" in fbo


# ---------------------------------------------------------------------------
# 轮次身份/跳号声明延续/趋势行/结论锚/分包边界
# ---------------------------------------------------------------------------

def test_round_identity_skip_declaration_and_prefix_consistency(dev):
    """轮次身份声明：单变量报告框收敛归因轮（r20「随指引落盘固化」先例
    同型）、changed_variables=1（§6 条款单变量=prep-record 实测核对）、
    机械变换派生（base=8633bda5 零字节不动/derived=866b0157/delta=1690）、
    §6 前缀一致性（R23T-/R23B- 即落盘原文、无差异登记需求）；跳号声明延
    续：r21=冻结计划未执行位（axis-plan 预留条件位、槽位永久留空、r22 跳
    号声明在案、r23 与该位无涉）；冻结原文引用=dev-r22 逐字继承。"""
    rid = dev["round_identity_declaration"]
    assert rid["changed_variables"] == 1
    gd = rid["guidance_derivation"]
    assert gd["mode"] == "mechanical_transform_derive"
    assert gd["base_sha256_prefix"] == "8633bda5"
    assert gd["derived_sha256_prefix"] == "866b0157"
    assert gd["byte_delta"] == 1690
    assert gd["transform_base_untouched"] is True
    assert "§6" in rid["sole_variable"]
    assert "随指引落盘固化" in rid["precedent"]
    assert "R23T-" in rid["section6_prefix_consistency"]
    assert "无" in rid["section6_prefix_consistency"]
    assert "changed_variables 长" in rid["changed_variables_note"]
    assert dev["round_nature"].startswith("development 域单变量报告框收敛归因轮")
    # 跳号声明延续
    skip = dev["r21_skip_declaration"]
    assert skip["r21_status"] == "冻结计划未执行位（槽位永久留空）"
    assert "跳号" in skip["declaration"]
    assert "R21 不做" in skip["declaration"]
    assert "永久留空" in skip["declaration"]
    assert "r22 跳号声明在案" in skip["declaration"]
    quotes = skip["frozen_quotes"]
    dev22 = S83._json_load(S83.REL_DEV_R22)
    frozen = dev22["r21_skip_declaration"]["frozen_quotes"]
    assert quotes == frozen  # 与 dev-r22 在案引用逐字继承
    assert "R21（三轴全组合）" in quotes[
        "combination_decision_rule.ii_full_combination"]
    assert "R21 不做" in quotes["early_stop_rule."
                                "strong_single_axis_shortcut"]


def test_joint_trend_rows_r5_to_r23(dev):
    """联合评价趋势行：r5–r22 行=dev-r22 在案行冻结转录逐一相等+追加
    r23 行（代表配置口径实测：16/2/0.125、not_met、source=run-r23
    15f58350）；连续达标=0；聚合口径分列注记在案。"""
    trend = dev["joint_evaluation_trend"]["by_round"]
    assert [r["round"] for r in trend] == [
        "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r13", "r14",
        "r15", "r16", "r17", "r18", "r19", "r20", "r22", "r23"]
    dev22 = S83._json_load(S83.REL_DEV_R22)
    prior = dev22["joint_evaluation_trend"]["by_round"]
    assert trend[:-1] == prior  # r5–r22 冻结转录
    row23 = trend[-1]
    assert (row23["flag_count_total"], row23["abstain_count_total"],
            row23["abstain_rate_total"]) == (16, 2, 0.125)
    assert row23["joint_evaluation"] == "not_met"
    assert row23["gt_recall_total"] == 0.076923
    assert row23["matches_total"] == 1
    assert row23["seed_match_rate_total"] == 0.071429
    assert row23["source"]["sha256"].startswith("15f58350")
    assert row23["round_id"] == ROUND_ID
    assert "r11–r23 行=代表配置口径" in \
        dev["joint_evaluation_trend"]["aggregation_scope_note"]


def test_honest_conclusion_next_targets_anchors_and_rerun_idempotent(dev):
    """honest 结论/下一目标关键锚+重跑语义：honest_conclusion 含字母裁
    决（confounded 唯一正式）、框宽非（唯一）主因归因转向、G2 分岔两账
    分列、M4 三样本未过门事实、GT union 双 GT 单实例命中、三轴收束两账
    并列、跳号、不得冒充留出、in_calibrated_range 恒 False；next_
    iteration_targets 五件组；s83 main 幂等重跑（盘上字节零改动）+s82
    分包边界（无 dev-record 构建函数、只产 run-r23；s83 只写
    round23-dev-record.json 一件）。"""
    hc = dev["honest_conclusion"]
    for anchor in ("confounded", "唯一正式裁决",
                   "confounded_g2_positive_in_band",
                   "0.484848", "[0.361538, 0.561538]", "0.461538",
                   "框宽非（唯一）主因", "归因转向",
                   "g2_bifurcation_record", "三账分列",
                   "0.520833", "未过门", "0.011111",
                   "0.153846", "r19_axis3 第一", "不合并、不改写",
                   "不得冒充留出", "in_calibrated_range 恒 False",
                   "跳号", "conditional/double-entry"):
        assert anchor in hc, anchor
    nxt = dev["next_iteration_targets"]
    assert len(nxt) == 5
    assert "排序不变" in nxt[0] and "conditional/double-entry" in nxt[0]
    assert "(a)" in nxt[1] and "(b)" in nxt[1] and "(c)" in nxt[1]
    assert "剩余混杂" in nxt[1] and "第三样本" in nxt[1]
    assert "不得" in nxt[2] and "事后改判" in nxt[2]
    assert "留出集时机" in nxt[3] and "连续 2 轮达标" in nxt[3]
    assert "黑点族弃权 8" in nxt[4] and "接触性回升" in nxt[4]
    # 重跑语义：main 幂等重跑（不抛异常）且盘上字节零改动；护栏对象=
    # s83 REL_OUT（v2 件），v2.1 件与 v2 件均零写入
    before = open(DEV_PATH, "rb").read()
    S83.main()
    assert open(DEV_PATH, "rb").read() == before  # v2.1 件零回写
    assert hashing.sha256_file(V2_PATH) == V2_SHA256  # v2 原件字节零变化
    assert hashing.sha256_file(DEV_PATH) == V21_SHA256
    # 分包边界：s82 零 dev-record 写入（只产 run-r23）；s83 只写本件
    path82 = os.path.join(REPO, "scripts", "s82_calibration_r23_compare.py")
    spec = importlib.util.spec_from_file_location(
        "s82_probe_pkg", path82)
    s82 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s82)
    assert not hasattr(s82, "build_dev_record")
    assert hasattr(s82, "build_run")
    assert hasattr(S83, "build_dev_record")
