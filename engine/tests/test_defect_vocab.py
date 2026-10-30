# -*- coding: utf-8 -*-
"""v5.defect_vocab 单测（A6 改进件：subject→规范缺陷 id 注册表 + 计票前归一化）：

- a) 注册表校验：真实注册表可载入；canonical_id 唯一 / 正则可编译 / 字段齐全
     由 load_vocab fail-closed 把关（负向：重复 id、坏正则、缺字段、坏 version、
     文件不在场）；
- b) 三席真实重放（out/v5-p3/seat-a-replay/runs/，文件不在场则 pytest.skip）：
     normalize_ballots → voting.tally，多数门聚出恰 6 个规范缺陷，其中裁定口径
     四项 p3-pad-r5=3/3、p4-north-pads-r5=3/3、p4-ana-r2=2/3、p8-width-r1=3/3
     （多数门内附加 p8-interval-contradiction=3/3、p7p9-clearance-r5=3/3，按实际
     断言）；并对照归一化前的语法计票只聚出 P4(2/3)/P8(3/3) 两簇（与
     tally-n3.json engine_tally_syntactic 逐字一致）；
- c) 未知 subject 原样透传（不发明新 id）+ normalize_ballots 纯函数（双调用
     deep equal、入参不动、出口隔离）；
- d) 只增不改纪律：version 在场且为语义版本；六个初始 canonical_id 恒在场。
"""
import copy
import json
import os
import re

import pytest

from v5 import canonical
from v5.defect_vocab import (DefectVocabError, load_vocab, normalize_ballots,
                             normalize_subject)
from v5.voting import tally

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "out", "v5-p3", "seat-a-replay", "runs")
SEATS = (("seat1-glm1-run2", 1), ("seat3-glm2-run2", 2), ("seat4-qwen", 3))
INITIAL_IDS = {"p8-width-r1", "p8-interval-contradiction", "p7p9-clearance-r5",
               "p3-pad-r5", "p4-north-pads-r5", "p4-ana-r2"}

# 三席 output.json 中出现过的全部 15 种不同 (subject, rule) → 规范 id（真实措辞底表）
REAL_MAPPINGS = [
    ("P8", "R1", "p8-width-r1"),
    ("P8", "自相矛盾", "p8-interval-contradiction"),
    ("P7 与 P9", "R5", "p7p9-clearance-r5"),
    ("P7/P9", "R5", "p7p9-clearance-r5"),
    ("P7", "R5", "p7p9-clearance-r5"),
    ("P9 与 P3", "R5", "p3-pad-r5"),
    ("P7 与 P3", "R5", "p3-pad-r5"),
    ("P3 端点焊盘(16,36)", "R5", "p3-pad-r5"),
    ("P3", "R5", "p3-pad-r5"),
    ("P9 与 P4", "R5", "p4-north-pads-r5"),
    ("P7 与 P4", "R5", "p4-north-pads-r5"),
    ("P4 北端（铜带顶缘 y=36.0 及端点焊盘(32.6,36)）", "R5", "p4-north-pads-r5"),
    ("P4 北端端点焊盘(32.6,36)", "R5", "p4-north-pads-r5"),
    ("P4", "R5", "p4-north-pads-r5"),
    ("P4", "R2", "p4-ana-r2"),
]


def _write_vocab(tmp_path, doc):
    p = tmp_path / "vocab.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return str(p)


def _synth_ballot(aid, order, items):
    return {"agent_id": aid, "registration_order": order,
            "board_sha256": "a" * 64, "pkg_sha256": "b" * 64,
            "problem_items": items, "confidence_rank": [],
            "raw_ref": "synthetic/%s" % aid}


def _require_runs():
    missing = [os.path.join(RUNS, seat, "output.json") for seat, _o in SEATS
               if not os.path.isfile(os.path.join(RUNS, seat, "output.json"))]
    if missing:
        pytest.skip("真实席位 output.json 不在场: %s" % ", ".join(missing))


def _load_replay_ballots():
    """由三席真实 output.json 的 defect_scan 原文构造序数票（shape 同
    tools/build_p3_gate.py 门项 6：kind 承载 rule；hash 取各 run meta.json 对账字段，
    不在场时降级用 tally-n3.json engine_tally 同源常量）。"""
    fallback = {"board_sha256":
                "32d659667f07e69f66ac2cf5dcde84e425cb488b3a136d9b60f9d14c616c4deb",
                "pkg_sha256":
                "8c7d84ef23da5d5f4784be2cbf9185c6669154848ecb15d22f20dbc0fd618fad"}
    ballots = []
    for (seat, order), _p in zip(SEATS, _seat_paths()):
        with open(os.path.join(RUNS, seat, "output.json"), encoding="utf-8") as f:
            scan = json.load(f)["defect_scan"]
        meta_path = os.path.join(RUNS, seat, "meta.json")
        if os.path.isfile(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            hashes = {"board_sha256": meta["board_sha256"],
                      "pkg_sha256": meta["pkg_sha256"]}
        else:
            hashes = fallback
        ballots.append({
            "agent_id": seat, "registration_order": order,
            "board_sha256": hashes["board_sha256"],
            "pkg_sha256": hashes["pkg_sha256"],
            "problem_items": [{"subject": it["subject"], "kind": it["rule"],
                               "rule": it["rule"], "note": it["note"]}
                              for it in scan],
            "confidence_rank": [],
            "raw_ref": "out/v5-p3/seat-a-replay/runs/%s/response-raw.md" % seat})
    return ballots


def _seat_paths():
    return [os.path.join(RUNS, seat, "output.json") for seat, _o in SEATS]


# --------------------------------------------------------------- a) 注册表校验

def test_real_vocab_loads_and_is_valid():
    """真实注册表过 fail-closed 校验；id 唯一、rule 非空、正则全部可编译。"""
    vocab = load_vocab()                            # 校验不过会抛
    ids = [e["canonical_id"] for e in vocab["entries"]]
    assert len(ids) == len(set(ids))
    assert set(ids) == INITIAL_IDS
    for e in vocab["entries"]:
        assert isinstance(e["rule"], str) and e["rule"].strip()
        assert isinstance(e["subject_patterns"], list) and e["subject_patterns"]
        for pat in e["subject_patterns"]:
            re.compile(pat)                         # 不可编译会抛 re.error


@pytest.mark.parametrize("doc,frag", [
    ({"version": "1.0.0", "entries": [
        {"canonical_id": "x-a", "rule": "R5", "subject_patterns": ["^P1$"]},
        {"canonical_id": "x-a", "rule": "R5", "subject_patterns": ["^P2$"]}]},
     "重复"),
    ({"version": "1.0.0", "entries": [
        {"canonical_id": "x-a", "rule": "R5", "subject_patterns": ["(unclosed"]}]},
     "正则"),
    ({"version": "1.0.0", "entries": [
        {"canonical_id": "x-a", "subject_patterns": ["^P1$"]}]},
     "必填"),
    ({"entries": [{"canonical_id": "x-a", "rule": "R5",
                   "subject_patterns": ["^P1$"]}]},
     "version"),
    ({"version": "", "entries": [{"canonical_id": "x-a", "rule": "R5",
                                  "subject_patterns": ["^P1$"]}]},
     "version"),
    ({"version": "1.0.0", "entries": []},
     "非空"),
    ({"version": "1.0.0", "entries": [
        {"canonical_id": "BadID", "rule": "R5", "subject_patterns": ["^P1$"]}]},
     "canonical_id"),
])
def test_invalid_vocab_fail_closed(tmp_path, doc, frag):
    with pytest.raises(DefectVocabError) as ei:
        load_vocab(_write_vocab(tmp_path, doc))
    assert frag in str(ei.value)


def test_missing_vocab_file_fail_closed(tmp_path):
    with pytest.raises(DefectVocabError):
        load_vocab(str(tmp_path / "nope.json"))


# ------------------------------------------------- b) 三席真实重放 → 计票

@pytest.mark.parametrize("subject,rule,want", REAL_MAPPINGS)
def test_real_wordings_map_to_canonical_ids(subject, rule, want):
    """三席真实措辞 15 种逐一映射到规范 id（含 P8/P4 靠 rule 消歧、裸 P7 归 p7p9）。"""
    assert normalize_subject(subject, rule) == want


def test_normalize_subject_whitespace_and_rule_edges():
    """空白折叠后命中；rule 缺失/空/不认识 → None（不猜测、不发明 id）。"""
    assert normalize_subject(" P3 ", " R5 ") == "p3-pad-r5"
    assert normalize_subject("P4", None) is None
    assert normalize_subject("P4", "") is None
    assert normalize_subject("完全未知缺陷 XYZ", "R5") is None
    assert normalize_subject("P9", "R1") is None     # R1 只登记了 P8
    assert normalize_subject("P7 与 P3", "R5") == "p3-pad-r5"   # 点名对方网名消歧
    assert normalize_subject("P7", "R5") == "p7p9-clearance-r5" # 裸 P7 归 p7p9


def test_replay_tally_majority_clusters_six_canonical_defects():
    """真实三席 normalize → tally：多数门恰聚 6 个规范缺陷；裁定口径四项票数
    p3-pad-r5=3/3、p4-north-pads-r5=3/3、p4-ana-r2=2/3、p8-width-r1=3/3；
    附加 p8-interval-contradiction=3/3、p7p9-clearance-r5=3/3（按实际）。"""
    _require_runs()
    ballots = _load_replay_ballots()
    snapshot = copy.deepcopy(ballots)
    normalized = normalize_ballots(ballots)
    assert ballots == snapshot                      # 归一化不改入参
    result = tally(normalized)
    evidence = {m["subject"]: m["evidence"] for m in result["majority_items"]}
    assert evidence["p3-pad-r5"] == "3/3"           # GT1（席位词汇三分归一）
    assert evidence["p4-north-pads-r5"] == "3/3"    # GT2
    assert evidence["p4-ana-r2"] == "2/3"           # GT3（seat3 漏报）
    assert evidence["p8-width-r1"] == "3/3"         # 播种 D1
    assert evidence["p8-interval-contradiction"] == "3/3"   # 播种 D1b（附加）
    assert evidence["p7p9-clearance-r5"] == "3/3"   # 播种 D2（附加）
    assert set(evidence) == INITIAL_IDS             # 多数门恰聚出 6 个规范缺陷
    voters = {m["subject"]: m["voters"] for m in result["majority_items"]}
    assert voters["p3-pad-r5"] == [s for s, _o in SEATS]        # 先注册序
    assert voters["p4-ana-r2"] == ["seat1-glm1-run2", "seat4-qwen"]
    # 少数派全文留痕：seat3 漏列 GT3 整票在场，subject_raw 保留原始措辞
    dissents = result["minority_dissents"]
    assert [d["agent_id"] for d in dissents] == ["seat3-glm2-run2"]
    assert dissents[0]["missing_majority_subjects"] == ["p4-ana-r2"]
    raws = {it["subject_raw"] for it in dissents[0]["ballot"]["problem_items"]}
    assert "P4 北端（铜带顶缘 y=36.0 及端点焊盘(32.6,36)）" in raws
    assert result["downgraded"] is False and result["tie_note"] is None
    # 双跑确定性：归一化+计票 canonical 字节相等
    assert canonical.canonical_json(tally(normalize_ballots(ballots))) == \
        canonical.canonical_json(result)


def test_replay_syntactic_baseline_was_fragmented():
    """归一化前对照：语法键计票只聚出 P8(3/3)/P4(2/3) 两簇——与 tally-n3.json
    engine_tally_syntactic 逐字一致（词表修复的动机事实）。"""
    _require_runs()
    result = tally(_load_replay_ballots())
    assert {m["subject"]: m["evidence"]
            for m in result["majority_items"]} == {"P4": "2/3", "P8": "3/3"}


def test_replay_normalization_replaces_subject_keeps_raw_and_note():
    """真实票归一化：命中 subject→canonical_id、原值进 subject_raw、note/kind 不动；
    同票内同缺陷多措辞（seat1 的 P3 两条）收敛到同一 canonical_id。"""
    _require_runs()
    normalized = normalize_ballots(_load_replay_ballots())
    seat1 = normalized[0]
    assert seat1["agent_id"] == "seat1-glm1-run2"
    p3_items = [it for it in seat1["problem_items"]
                if it["subject"] == "p3-pad-r5"]
    assert {it["subject_raw"] for it in p3_items} == {"P9 与 P3", "P7 与 P3"}
    assert all(it["kind"] == "R5" and it["note"] for it in p3_items)
    # seat4 的 'P4' 一票双义：R5→p4-north-pads-r5、R2→p4-ana-r2，原始值均在 subject_raw
    seat4 = [it["subject"] for it in normalized[2]["problem_items"]
             if it["subject_raw"] == "P4"]
    assert sorted(seat4) == ["p4-ana-r2", "p4-north-pads-r5"]


# --------------------------------- c) 未知透传 + 纯函数（双调用 deep equal）

def test_normalize_ballots_hit_and_miss():
    """命中替换+留 raw；未知 subject 原样透传（只加 subject_raw，不发明 id）。"""
    ballots = [_synth_ballot("a", 1, [
        {"subject": "P9 与 P3", "kind": "R5", "note": "重叠短路"},
        {"subject": "神秘新缺陷", "kind": "RX", "note": "未知措辞"}])]
    out = normalize_ballots(ballots)
    hit, miss = out[0]["problem_items"]
    assert hit["subject"] == "p3-pad-r5" and hit["subject_raw"] == "P9 与 P3"
    assert hit["note"] == "重叠短路" and hit["kind"] == "R5"
    assert miss["subject"] == "神秘新缺陷" and miss["subject_raw"] == "神秘新缺陷"


def test_normalize_ballots_rule_missing_keeps_subject():
    """rule 与 kind 都对不上注册表 → 不猜测：subject 原样、仍加 subject_raw。"""
    ballots = [_synth_ballot("a", 1, [
        {"subject": "P4", "kind": "别的种类", "note": "n"},
        {"subject": "P8", "note": "无 rule 无 kind"}])]
    out = normalize_ballots(ballots)[0]["problem_items"]
    assert out[0]["subject"] == "P4" and out[0]["subject_raw"] == "P4"
    assert out[1]["subject"] == "P8" and out[1]["subject_raw"] == "P8"


def test_normalize_ballots_pure_double_call_deep_equal():
    """纯函数：双调用结果 deep equal（canonical 字节等）、入参不被改动、出口隔离。"""
    ballots = [_synth_ballot("a", 1, [{"subject": "P8", "kind": "R1", "note": "n"}]),
               _synth_ballot("b", 2, [{"subject": "未知", "kind": "K", "note": ""}])]
    snapshot = copy.deepcopy(ballots)
    out1 = normalize_ballots(ballots)
    out2 = normalize_ballots(ballots)
    assert out1 == out2
    assert canonical.canonical_json(out1) == canonical.canonical_json(out2)
    assert ballots == snapshot                      # 入参原样
    out1[0]["problem_items"][0]["subject"] = "污染"   # 改产物不污染后续归一化
    assert normalize_ballots(ballots)[0]["problem_items"][0]["subject"] == \
        "p8-width-r1"


# --------------------------------------------------------- d) 只增不改纪律

def test_version_field_present_and_initial_ids_immutable():
    """version 在场且为语义版本；_disambiguation 说明在场；六个初始 canonical_id
    恒在场（后续版本只增条目、不移除/不改名既有 id）。"""
    vocab = load_vocab()
    assert isinstance(vocab.get("version"), str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", vocab["version"])
    assert isinstance(vocab.get("_disambiguation"), str) and \
        vocab["_disambiguation"].strip()
    ids = {e["canonical_id"] for e in vocab["entries"]}
    assert INITIAL_IDS <= ids
