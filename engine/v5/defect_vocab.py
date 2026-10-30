# -*- coding: utf-8 -*-
"""规范缺陷词表：subject→canonical_id 注册表 + 计票前归一化（A6 改进件）。

背景（用户裁定 2026-09）：v5/voting.py 的 A6 计票对 defect_scan.subject 只做
语法匹配（空白折叠），真实席位重放中三路模型对同一缺陷起了三个名字
（"P9 与 P3"/"P3 端点焊盘(16,36)"/"P3"），计票聚簇失真（tally-n3.json
engine_tally_syntactic 只聚出 P4/P8 两簇）。本件=主审维护的映射注册表
（数据文件 defect_vocab.json，与模块同目录）+ tally 前归一化函数；
voting.py 语义与代码零改动（映射发生在计票之前，归一化产物才进 tally）。

职责边界：
- load_vocab(path=None)：载入+校验 fail-closed（version 非空、entries 非空
  列表、canonical_id 唯一且为稳定小写串、rule 非空、subject_patterns 非空且
  正则可编译、priority 为整数）。
- normalize_subject(subject, rule) → canonical_id | None：rule 折叠空白后与
  entry.rule 严格相等（区分大小写），subject 折叠空白（与 voting.normalize_subject
  同口径）后逐 pattern re.search；entries 按 (priority 升序, 登记序) 稳定排序，
  首个命中即返回。不匹配 / rule 缺失 → None（未知 subject 保持原样——不发明
  新 id；P8/P4 的规范 id 恰靠 rule 消歧，无 rule 不猜测）。
- normalize_ballots(ballots, vocab=None) → 深拷贝 ballots：problem_items[].subject
  命中时替换为 canonical_id、原始 subject 保留进新键 "subject_raw"；未命中时
  subject 原样、同样加 "subject_raw"。rule 对账取 problem_items[].rule（缺失
  时回退 kind）；note/kind/其余键一律不动。入参不被改动（出口隔离）。

消歧总则（详见注册表 "_disambiguation" 字段）：同网名不同缺陷靠 rule 消歧
（P8：R1 vs 自相矛盾；P4：R5 vs R2）；同为 R5 的三向靠 pattern 的 ^ 锚定 +
priority 序 + 对方网名/焊盘措辞消歧。纪律：注册表只增不改——新措辞追加
pattern/条目，不改既有 canonical_id 与 pattern 语义；改语义必须升 version。

确定性：纯函数、无随机、无时间戳；零网络、零 LLM API（A8/R46 红线）；
不改 voting.py/harness.py 任何一行。
"""
import copy
import json
import os
import re

VOCAB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "defect_vocab.json")
DEFAULT_PRIORITY = 100   # entry 未写 priority 时的匹配序缺省值
_ID_RE = re.compile(r"[a-z0-9]+(?:[_-][a-z0-9]+)*\Z")   # 稳定小写串（蛇形/串形）

__all__ = ["DefectVocabError", "VOCAB_FILE", "DEFAULT_PRIORITY",
           "load_vocab", "normalize_subject", "normalize_ballots"]


class DefectVocabError(ValueError):
    """词表 fail-closed 错误；path=注册表/票键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise DefectVocabError(path, msg)


def _collapse(text):
    """空白折叠（与 v5.voting.normalize_subject 同口径：转字符串、去首尾、折叠连续）。"""
    return " ".join(str(text).split())


def load_vocab(path=None):
    """载入注册表并 fail-closed 校验；返回解析后的 dict（不过即抛 DefectVocabError）。"""
    path = VOCAB_FILE if path is None else path
    try:
        with open(path, encoding="utf-8") as f:
            vocab = json.load(f)
    except OSError as exc:
        raise DefectVocabError(path, "注册表不可读: %s" % exc) from exc
    except ValueError as exc:                       # json.JSONDecodeError
        raise DefectVocabError(path, "注册表非法 JSON: %s" % exc) from exc
    _validate_vocab(vocab, path)
    return vocab


def _validate_vocab(vocab, path):
    """注册表结构校验（fail-closed 报键路径）：字段齐全、id 唯一、正则可编译。"""
    _require(isinstance(vocab, dict), path, "注册表须为对象")
    _require(isinstance(vocab.get("version"), str) and vocab["version"].strip(),
             path + ".version", "须为非空字符串（只增不改纪律的版本号）")
    _require(vocab.get("_disambiguation") is None
             or isinstance(vocab["_disambiguation"], str),
             path + "._disambiguation", "须为字符串")
    _require(isinstance(vocab.get("entries"), list) and vocab["entries"],
             path + ".entries", "须为非空列表")
    seen = set()
    for i, entry in enumerate(vocab["entries"]):
        base = "%s.entries[%d]" % (path, i)
        _require(isinstance(entry, dict), base, "须为对象")
        for key in ("canonical_id", "rule", "subject_patterns"):
            _require(key in entry, base + "." + key, "必填字段缺失")
        cid = entry["canonical_id"]
        _require(isinstance(cid, str) and _ID_RE.match(cid),
                 base + ".canonical_id",
                 "须为稳定小写串（[a-z0-9] 段、单 -/_ 分隔）: %r" % (cid,))
        _require(cid not in seen, base + ".canonical_id",
                 "canonical_id 重复: %r" % (cid,))
        seen.add(cid)
        _require(isinstance(entry["rule"], str) and entry["rule"].strip(),
                 base + ".rule", "须为非空字符串")
        pats = entry["subject_patterns"]
        _require(isinstance(pats, list) and pats,
                 base + ".subject_patterns", "须为非空列表")
        for j, pat in enumerate(pats):
            pbase = "%s.subject_patterns[%d]" % (base, j)
            _require(isinstance(pat, str) and pat.strip(), pbase, "须为非空字符串")
            try:
                re.compile(pat)
            except re.error as exc:
                raise DefectVocabError(pbase, "正则不可编译: %s" % exc) from exc
        _require("note" not in entry or isinstance(entry["note"], str),
                 base + ".note", "须为字符串")
        _require("priority" not in entry
                 or (isinstance(entry["priority"], int)
                     and not isinstance(entry["priority"], bool)),
                 base + ".priority", "须为整数")


def _sorted_entries(vocab):
    """匹配序：(priority 升序, 登记序) 稳定排序——确定、与登记序兼容。"""
    return [entry for _i, entry in
            sorted(enumerate(vocab["entries"]),
                   key=lambda pair: (pair[1].get("priority", DEFAULT_PRIORITY),
                                     pair[0]))]


def _match(vocab, subject, rule):
    """(subject, rule) → canonical_id | None。匹配语义见模块 docstring。"""
    if not isinstance(rule, str) or not rule.strip():
        return None                                 # 无 rule 不猜测（P8/P4 恰靠 rule 消歧）
    rule_key = _collapse(rule)
    subj = _collapse(subject)
    for entry in _sorted_entries(vocab):
        if _collapse(entry["rule"]) != rule_key:
            continue
        for pat in entry["subject_patterns"]:
            if re.search(pat, subj):
                return entry["canonical_id"]
    return None


def normalize_subject(subject, rule, vocab=None):
    """subject→规范缺陷 id；不匹配 / rule 缺失返回 None（未知 subject 保持原样）。"""
    return _match(load_vocab() if vocab is None else vocab, subject, rule)


def normalize_ballots(ballots, vocab=None):
    """计票前归一化（纯函数，出口隔离）：深拷贝 ballots，problem_items[].subject
    命中时替换为 canonical_id（原始 subject 保留进新键 "subject_raw"）；未命中时
    subject 原样、同样加 "subject_raw"。note/kind/其余键不动；入参不被改动。
    rule 对账取 item["rule"]（缺失回退 item["kind"]）。"""
    v = load_vocab() if vocab is None else vocab
    _require(isinstance(ballots, list), "ballots",
             "须为列表，得到 %s" % type(ballots).__name__)
    out = copy.deepcopy(ballots)
    for i, ballot in enumerate(out):
        base = "ballots[%d]" % i
        _require(isinstance(ballot, dict), base, "须为对象")
        items = ballot.get("problem_items")
        _require(isinstance(items, list), base + ".problem_items", "须为列表")
        for j, item in enumerate(items):
            ibase = "%s.problem_items[%d]" % (base, j)
            _require(isinstance(item, dict), ibase, "须为对象")
            _require(isinstance(item.get("subject"), str) and item["subject"].strip(),
                     ibase + ".subject", "须为非空字符串")
            raw = item["subject"]
            rule = item.get("rule")
            if not (isinstance(rule, str) and rule.strip()):
                rule = item.get("kind")             # voting 形状票回退 kind 对账
            cid = _match(v, raw, rule)
            if cid is not None:
                item["subject"] = cid
            item["subject_raw"] = raw
    return out
