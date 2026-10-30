"""RE-REGISTRATION 执行批测试（D2 v2.1 补发 + D4 对齐对比；
EXEC-R1）。

授权：out/v3-rereg-proposal/RE-REGISTRATION-ADJUDICATION-2026-09-13.md
D2（A2：补发 v2.1 修正件）+ D4（保存现有的前提下对齐做对比）；
RE-REGISTRATION-PROPOSAL-R1 §4.5 forward 规则（新版件最低 provenance
三要素：kind 显式后缀/supersedes[path_rel+全文 sha256]/双值披露）。

覆盖（冻结域只读；唯一写入=本批新目录内 s85b/s88b 幂等自证零覆写）：
- v2.1 四件（round23/24/25-dev-record-v2_1+holdout-dev-record-r1-v2_1）
  三要素核对+canonical 字节自证+顶层 declared_date 冻结为 v2 轮次值
  （Option A 语义：历史字段冻结、不冒充历史证据）；
- v2.1 payload 三要素掩码还原==v2 原件字节（历史字段冻结为 v2 原值）；
- 负向断言：v2 原件字节零变化（全长 sha256 钉死，零回写）；
- D4 对齐：s85b/s88b 幂等重跑，对齐输出==在案 canonical v2 件逐字节
  （差异恰=锚字节+三要素）；对比记录 canonical+归因分类
  （anchor_byte=1/v2_gauge_provenance_element=3/unclassified=0）+
  r1 冻结件零回写负向断言。

纪律：零网络/零 subprocess；零 wall-clock（声明常量 2026-09-13）；
canonical JSON=pcbflow.hashing.canonical_json_bytes 口径。
"""

import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAL_DIR = os.path.join(REPO, "out", "v3-tl2", "calibration")
HOLD_DIR = os.path.join(REPO, "out", "v3-tl2", "holdout")
EXEC_DIR = os.path.join(REPO, "out", "v3-rereg-exec-r1")

OLD = "6ed4f3fd7c87947562acffb90c8563dfae0d05ad82c395a45d0aad226c206e17"
NEW = "0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e"
DECLARED = "2026-09-13"
PROV_KEYS = ("anchor_amendment", "supersedes")

CASES = [
    dict(
        rid="round23",
        v2=os.path.join(CAL_DIR, "round23-dev-record-v2.json"),
        v21=os.path.join(CAL_DIR, "round23-dev-record-v2_1.json"),
        v2_kind="tl2_calibration_round23_dev_record",
        v21_kind="tl2_calibration_round23_dev_record_v2_1",
        v2_sha=("0dae60fb9121a39dac160412260be34abb64348ca5c395fc8235"
                "3f1759a6e4e9"),
        v21_sha=("66c722ee25d9206e98e38970ca6873743f90fce155c37415e8745"
                 "6ee9800a5ca"),
    ),
    dict(
        rid="round24",
        v2=os.path.join(CAL_DIR, "round24-dev-record-v2.json"),
        v21=os.path.join(CAL_DIR, "round24-dev-record-v2_1.json"),
        v2_kind="tl2_calibration_round24_dev_record",
        v21_kind="tl2_calibration_round24_dev_record_v2_1",
        v2_sha=("71de7a1e5150c90909b4022d65040c92e5af0d39183b897eed01"
                "e4f0da9c3e0e"),
        v21_sha=("718099adb9f9fa69e2de1924a49d6ce3adeeb1a3fe901fe6b19"
                 "a78d62209e61b"),
    ),
    dict(
        rid="round25",
        v2=os.path.join(CAL_DIR, "round25-dev-record-v2.json"),
        v21=os.path.join(CAL_DIR, "round25-dev-record-v2_1.json"),
        v2_kind="tl2_calibration_round25_dev_record",
        v21_kind="tl2_calibration_round25_dev_record_v2_1",
        v2_sha=("1c3e11903c74b3e81e5cd3e205de48a10a623e843389aedb21a6"
                "a616b414a112"),
        v21_sha=("10218b65160cab3c1730a03c33a66ecd32e6c55986f0ab05e10"
                 "fdf2516a8ceef"),
    ),
    dict(
        rid="holdout-r1",
        v2=os.path.join(HOLD_DIR, "holdout-dev-record-r1-v2.json"),
        v21=os.path.join(HOLD_DIR, "holdout-dev-record-r1-v2_1.json"),
        v2_kind="tl2_holdout_r1_dev_record",
        v21_kind="tl2_holdout_r1_dev_record_v2_1",
        v2_sha=("5ac9212612939c5651310a0e5ac63542269f0b46ef56f643943c"
                "8f2c2c12b3dd"),
        v21_sha=("737cf50a1362fed4af4656b68f1772bede2a46ab362f3ef77a3"
                 "2470edd93bceb"),
    ),
]


def _sha(path: str) -> str:
    return hashing.sha256_file(path)


@pytest.fixture(params=CASES, ids=[c["rid"] for c in CASES])
def case(request):
    return request.param


def test_v21_three_elements_and_canonical_form(case):
    """v2.1 件三要素核对（§4.5）：kind 显式后缀/supersedes[path_rel+全文
    sha256=被替代 v2 件实测]/双值披露（old=6ed4f3fd 历史值+note，new=
    0a738047 现值进期望字段）；canonical 字节自证；declared_date 纪律
    （顶层冻结为 v2 轮次值 2026-09-10、新增键=声明常量 2026-09-13=
    Option A 语义不冒充历史证据）；holdout 件另查 supersedes.note 引用
    件迁移登记（HOLDOUT-R1-ADJUDICATION 零回写衔接）。"""
    raw = open(case["v21"], "rb").read()
    doc = json.loads(raw)
    assert hashing.canonical_json_bytes(doc) == raw  # canonical 字节自证
    assert _sha(case["v21"]) == case["v21_sha"]  # 件身份
    # 要素 1：kind 显式后缀（被替代 kind 在案）
    assert doc["kind"] == case["v21_kind"]
    assert doc["kind"] != case["v2_kind"]
    assert doc["supersedes"]["kind_superseded"] == case["v2_kind"]
    # 要素 2：supersedes=path_rel+全文 sha256（=被替代 v2 件实测）
    assert doc["supersedes"]["path_rel"].endswith(
        os.path.basename(case["v2"]))
    assert doc["supersedes"]["sha256"] == case["v2_sha"] == _sha(case["v2"])
    assert len(doc["supersedes"]["sha256"]) == 64  # 全长口径
    # 要素 3：双值披露（old 保留+note；new=现值进期望字段）
    am = doc["anchor_amendment"]
    assert am["old_value"] == OLD and am["new_value"] == NEW
    assert am["old_value"] != am["new_value"]
    assert "双值披露" in am["note"] and "不冒充历史证据" in am["note"]
    pfv = doc["protected_files_verification"]
    if "hashes" in pfv:
        assert pfv["hashes"]["pcbflow/cli.py"] == NEW  # new 进期望字段
    else:
        assert pfv["pcbflow/cli.py"]["sha256"] == NEW
        assert pfv["pcbflow/cli.py"]["expected_prefix"] == NEW[:8]
    # declared_date 纪律（历史字段冻结为 v2 原值；新增键=声明常量）
    assert doc["declared_date"] == "2026-09-10"
    assert doc["supersedes"]["declared_date"] == DECLARED
    assert am["declared_date"] == DECLARED
    # 授权链引用
    assert any("RE-REGISTRATION-ADJUDICATION-2026-09-13" in a
               for a in am["authority"])
    # holdout 件：裁定记录引用件迁移登记（裁定记录零回写）
    if case["rid"] == "holdout-r1":
        assert "HOLDOUT-R1-ADJUDICATION" in doc["supersedes"]["note"]
        assert "零回写" in doc["supersedes"]["note"]


def test_v21_payload_frozen_to_v2_original(case):
    """v2.1 历史字段冻结=v2 原值：三要素掩码还原（去 anchor_amendment/
    supersedes、kind 还原为被替代值）后 canonical 字节==v2 原件字节
    （byte-exact；Option A 语义——本件仅新增字段承载重注册信息）。"""
    doc = json.loads(open(case["v21"], "rb").read())
    payload = {k: v for k, v in doc.items() if k not in PROV_KEYS}
    payload["kind"] = case["v2_kind"]
    v2_raw = open(case["v2"], "rb").read()
    assert hashing.canonical_json_bytes(payload) == v2_raw


def test_v2_original_bytes_freeze_negative(case):
    """负向断言：v2 原件字节零变化（全长 sha256 钉死；任何回写即红）。"""
    assert _sha(case["v2"]) == case["v2_sha"]
    assert len(case["v2_sha"]) == 64


def _load_variant_script(filename: str, alias: str):
    path = os.path.join(REPO, "scripts", filename)
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("alias,script,aligned_rel,comp_rel,v2_rel,r1_rel,"
                         "r1_sha,v2_sha,comp_kind", [
    ("s85b_aligned", "s85b_calibration_r24_prep_aligned.py",
     os.path.join(EXEC_DIR, "aligned", "r24-prep-record-v2-aligned.json"),
     os.path.join(EXEC_DIR, "d4-comparison-r24-prep.json"),
     os.path.join(CAL_DIR, "r24-prep-record-v2.json"),
     os.path.join(CAL_DIR, "r24-prep-record.json"),
     "760af49fe6da58a5b508651142bf51e6c23323ba0da7edc0b79c88410c84e3dd",
     "6de42169c6f5833ed8ca4d1297a5b58f9ace9e62f8f713c21e6f4226be92c311",
     "rereg_exec_r1_d4_comparison_r24_prep"),
    ("s88b_aligned", "s88b_calibration_r25_prep_aligned.py",
     os.path.join(EXEC_DIR, "aligned", "r25-prep-record-v2-aligned.json"),
     os.path.join(EXEC_DIR, "d4-comparison-r25-prep.json"),
     os.path.join(CAL_DIR, "r25-prep-record-v2.json"),
     os.path.join(CAL_DIR, "r25-prep-record.json"),
     "0943a8ec518473d4956e805eaac420c9f9583e7efdef7343325638674521c284",
     "5951a6efec1f26c52cd043bc04ea46f080e40abffa2c5d4afedec975ee6c2372",
     "rereg_exec_r1_d4_comparison_r25_prep"),
])
def test_d4_alignment_and_comparison(alias, script, aligned_rel, comp_rel,
                                     v2_rel, r1_rel, r1_sha, v2_sha,
                                     comp_kind):
    """D4 对齐对比（保存现有的前提下）：s85b/s88b 幂等重跑（防覆写护栏
    语义保持）后——①对齐输出==在案 canonical v2 件逐字节（对齐自证=
    独立生成路径再证）；②对比记录 canonical+kind/声明常量/授权链；
    ③归因分类恰=anchor_byte 1+三要素 3+unclassified 0（差异恰=锚字节
    +v2 口径新增字段，其余逐字节同源）；④负向断言：r1 冻结件与既有
    v2 件字节零变化（对齐不替换、对比不覆盖）。"""
    mod = _load_variant_script(script, alias)
    # REPAIR-P4 W-1（G0）：config.py 授权变更（f515c348→acdfac49，登记=
    # out/repair-p4/anchor-hashes-post-g0.json）。s85/s88 基座（经变体装载）
    # 的保护锚校验与对齐重建均走 hashing.sha256_file 属性查找——main() 调用
    # 段按登记件 before 值历史语境回放（finally 恢复；盘上 r1/v2 冻结件与
    # 本测试后续 _sha 断言不受影响）。
    _orig_sha256_file = hashing.sha256_file

    def _sha256_file_g0_legacy(path, _orig=_orig_sha256_file):
        if str(path).replace("\\", "/").endswith("pcbflow/config.py"):
            return ("f515c34842521a645145a9f5454a5919274a242e5c8c27c"
                    "01faf1a4c13e73baf")
        if str(path).replace("\\", "/").endswith("pcbflow/cli.py"):
            # REPAIR-G1+ W-1/W-2（2026-09-24）：cli.py 授权变更 0a738047->
            # 3bfc9407（登记=out/repair-g1plus-r1/anchor-hashes-post-
            # g1plus.json）；s85b/s88b 保护锚校验补 cli 历史语境回放腿
            return ("0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a43a62d8c775da32e")
        return _orig(path)

    hashing.sha256_file = _sha256_file_g0_legacy
    try:
        mod.main()  # 幂等重跑：输出已存在且逐字节相同→零覆写
    finally:
        hashing.sha256_file = _orig_sha256_file
    # ① 对齐输出==canonical v2 件（byte-exact）
    aligned_raw = open(aligned_rel, "rb").read()
    v2_raw = open(v2_rel, "rb").read()
    assert aligned_raw == v2_raw
    assert _sha(aligned_rel) == v2_sha
    # ② 对比记录（canonical JSON）
    comp_raw = open(comp_rel, "rb").read()
    comp = json.loads(comp_raw)
    assert hashing.canonical_json_bytes(comp) == comp_raw
    assert comp["kind"] == comp_kind
    assert comp["declared_date"] == DECLARED
    assert any("RE-REGISTRATION-ADJUDICATION-2026-09-13" in a
               for a in comp["authority"])
    # ③ 差异归因分类
    summary = comp["attribution_summary"]
    assert summary == {"anchor_byte": 1,
                       "v2_gauge_provenance_element": 3,
                       "unclassified": 0}
    assert len(comp["leaf_diffs"]) == 4
    changed = [d for d in comp["leaf_diffs"]
               if d["type"] == "changed"]
    assert len(changed) == 2  # kind+cli 锚；其余两条=新增字段
    anchor = [d for d in changed
              if d["field_path"] == ["protected_files_verification",
                                     "hashes", "pcbflow/cli.py"]]
    assert len(anchor) == 1
    assert anchor[0]["r1_value"] == OLD
    assert anchor[0]["aligned_value"] == NEW
    assert comp["cross_check_vs_canonical_v2"]["byte_equal"] is True
    # ④ 负向断言：r1 冻结件与既有 v2 件零回写
    assert _sha(r1_rel) == r1_sha
    assert comp["path_r1"]["sha256"] == r1_sha
