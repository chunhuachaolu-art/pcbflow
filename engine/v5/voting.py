# -*- coding: utf-8 -*-
"""投票计票器（任务书 A6/D001；P3 交付）。

职责边界（A6 作用域封口）：计票器只对 N 路模型 agent 的序数票做**事实聚合**
——多数门、少数派全文留痕、平票确定性 tie-break 留痕、N=2 降档标注——产出
纯 dict 台账候选；**不改写理念注册表、优先级或 compiled_rule**（改理念唯一
通道=principle_objection 增改 compiled_rule 提案 → U9 自动重测环，A10）。
本模块零 I/O、零网络、零 LLM API 调用（A8/R46 红线）、零注册表访问。

投票输入（ballots 形状，P3 交付规格；第三路阵容=U10，本模块不写死任何模型名）：
  [{"agent_id": str, "registration_order": int（先注册序，全序确定）,
    "board_sha256": str, "pkg_sha256": str,
    "problem_items": [{"subject": str, "kind": str, "note": str}],
    "confidence_rank": list, "raw_ref": str（证据三件套留痕指针）}]

投票前 provenance 对账（A6 硬要求）：互相不见面、输入同源同 hash——全部票的
board_sha256 / pkg_sha256 必须逐一相等，不齐 → ValueError fail-closed。

计票规则（A6）：
- N=3：subject 被 ≥2 票**独立列出**（不同 agent；同票重复 subject 不重复计）
  才入 majority_items（≥2/3 多数门）；evidence 记 "2/3"/"3/3"；voters 按
  先注册序。
- N=2（缺席降档）：须 2/2 才入台账；downgraded=True；tie_note 附置信降档
  标注（台账证据强度低于 N=3 口径，使用方须按降档标注消费）。
- N=5（诊断扩编，用户裁定 2026-09-14：席位 A 盲包重放五席补票 DSF+GPT6；
  任务书正式口径仍为 N=3，P5 席位 C 不受影响）：多数门 =n//2+1 即 ≥3/5；
  downgraded 恒 False；其余规则（独立列出、少数派全文留痕、平票 tie-break）
  与 N=3 同构。
- 平票：无任何 subject 过多数门且有票被提出（如 3 票三个不同 subject 各
  1 票）→ 全部不入台账；tie_note 按**先注册 agent 序**逐条确定性留痕
  （先注册 agent 优先；计票器只记事实，不抬举任何一方入台账）。
- 少数派异议全文留痕：凡①漏列任一台账 subject、或②提出了未入台账 subject
  的票，其**整票全文**（deep copy）进 minority_dissents（多数门之外一票不丢；
  附 missing_majority_subjects / unledgered_subjects 双向归因）。
- subject 规范化键：转字符串、去首尾空白、折叠连续空白（" P8 " 与 "P8" 同
  键）；台账 subject 记规范化形态；majority_items / dissents 内列表均按确定
  序输出（subject 字典序 / 先注册序）。

确定性：纯函数、无时间戳无随机、不改动入参（出口一律 deep copy）；同输入
双跑 canonical 字节相等（硬测试）。
"""
import copy

VALID_N = (2, 3, 5)   # N=3 正式 / N=2 缺席降档 / N=5 诊断扩编；其余票数 fail-closed


def majority_gate(n):
    """多数门票数通式 = n//2+1：N=2→2/2（缺席降档）、N=3→2/3（正式）、
    N=5→3/5（诊断扩编；用户裁定 2026-09-14 席位重放五席补票）。"""
    return n // 2 + 1

_RESULT_KEYS = ("majority_items", "minority_dissents", "downgraded", "tie_note")


class VotingError(ValueError):
    """计票 fail-closed 错误；path=票/键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise VotingError(path, msg)


def normalize_subject(subject):
    """subject 规范化键：转字符串、去首尾空白、折叠连续空白。"""
    return " ".join(str(subject).split())


def _validate_ballots(ballots):
    """入口形状校验（fail-closed 报票/键路径）+ 按先注册序返回票列表（浅拷贝）。"""
    _require(isinstance(ballots, list), "ballots",
             "须为列表，得到 %s" % type(ballots).__name__)
    _require(len(ballots) in VALID_N, "ballots",
             "票数须为 %s（N=3 正式 / N=2 缺席降档 / N=5 诊断扩编），得到 %d"
             % (list(VALID_N), len(ballots)))
    agent_ids, orders = set(), set()
    for i, b in enumerate(ballots):
        base = "ballots[%d]" % i
        _require(isinstance(b, dict), base, "须为对象")
        for key in ("agent_id", "registration_order", "board_sha256", "pkg_sha256",
                    "problem_items", "confidence_rank", "raw_ref"):
            _require(key in b, base + "." + key, "必填字段缺失")
        _require(isinstance(b["agent_id"], str) and b["agent_id"],
                 base + ".agent_id", "须为非空字符串")
        _require(b["agent_id"] not in agent_ids, base + ".agent_id",
                 "agent_id 重复: %r" % b["agent_id"])
        agent_ids.add(b["agent_id"])
        ro = b["registration_order"]
        _require(isinstance(ro, int) and not isinstance(ro, bool) and ro >= 1,
                 base + ".registration_order", "须为 ≥1 的整数")
        _require(ro not in orders, base + ".registration_order",
                 "registration_order 重复: %r（先注册序须全序确定）" % (ro,))
        orders.add(ro)
        for key in ("board_sha256", "pkg_sha256"):
            _require(isinstance(b[key], str) and b[key],
                     base + "." + key, "须为非空字符串（provenance 对账依据）")
        _require(isinstance(b["raw_ref"], str) and b["raw_ref"],
                 base + ".raw_ref", "须为非空字符串（三件套证据留痕指针）")
        items = b["problem_items"]
        _require(isinstance(items, list), base + ".problem_items", "须为列表")
        for j, it in enumerate(items):
            ibase = base + ".problem_items[%d]" % j
            _require(isinstance(it, dict), ibase, "须为对象")
            for key in ("subject", "kind", "note"):
                _require(key in it, ibase + "." + key, "必填字段缺失")
            _require(isinstance(it["subject"], str) and it["subject"].strip(),
                     ibase + ".subject", "须为非空字符串")
            _require(isinstance(it["kind"], str) and it["kind"],
                     ibase + ".kind", "须为非空字符串")
            _require(isinstance(it["note"], str), ibase + ".note", "须为字符串")
        _require(isinstance(b["confidence_rank"], list),
                 base + ".confidence_rank", "须为列表")
    return [dict(b) for b in sorted(ballots, key=lambda b: b["registration_order"])]


def tally(ballots):
    """N 路序数票 → 事实聚合（纯函数；规则见模块 docstring；A6 作用域封口：
    产物恰含 _RESULT_KEYS 四键，无任何注册表/规则改写通道）。"""
    ordered = _validate_ballots(ballots)
    n = len(ordered)

    # 投票前 provenance 对账（A6 硬要求：同源同 hash，不齐即拒）
    for key in ("board_sha256", "pkg_sha256"):
        values = {b[key] for b in ordered}
        _require(len(values) == 1, "ballots." + key,
                 "provenance 对账失败：%s 须同源同 hash，得到 %d 种取值 %r"
                 % (key, len(values), sorted(values)))

    # subject 聚合（规范化键；同票内重复 subject 不重复计——「独立列出」按 agent 数）
    by_subject = {}
    for b in ordered:
        for s in sorted({normalize_subject(it["subject"]) for it in b["problem_items"]}):
            by_subject.setdefault(s, []).append((b["registration_order"], b["agent_id"]))

    # 多数门：通式 n//2+1（N=3 ≥2/3；N=2 须 2/2；N=5 ≥3/5，evidence 串记实际口径）
    gate = majority_gate(n)
    ledger = sorted(s for s, voters in by_subject.items()
                    if len(voters) >= gate)
    ledger_set = set(ledger)
    majority_items = [{"subject": s,
                       "evidence": "%d/%d" % (len(by_subject[s]), n),
                       "voters": [a for _o, a in sorted(by_subject[s])]}
                      for s in ledger]

    # 少数派异议全文留痕：漏列台账 subject 或提出未入台账 subject 的整票（deep copy）
    minority_dissents = []
    for b in ordered:
        own = {normalize_subject(it["subject"]) for it in b["problem_items"]}
        missing = [s for s in ledger if s not in own]
        unledgered = sorted(own - ledger_set)
        if missing or unledgered:
            minority_dissents.append({
                "agent_id": b["agent_id"],
                "registration_order": b["registration_order"],
                "missing_majority_subjects": missing,
                "unledgered_subjects": unledgered,
                "ballot": _deep_copy_ballot(b),
            })

    # 平票：无任何 subject 过门且有票被提出 → 全部不入台账，按先注册 agent 序留痕
    tie_note = None
    if not ledger and by_subject:
        entries = []
        for s in sorted(by_subject,
                        key=lambda s: (min(o for o, _a in by_subject[s]), s)):
            voters = "、".join("%s@%d" % (a, o) for o, a in sorted(by_subject[s]))
            entries.append("%s（%s）" % (s, voters))
        tie_note = ("平票：无任何 subject 达到 %d 票多数门，全部不入台账；"
                    "按先注册 agent 序留痕：%s" % (gate, "；".join(entries)))

    # N=2 缺席降档：downgraded 标志 + tie_note 置信降档标注
    downgraded = (n == 2)
    if downgraded:
        note = ("N=2 降档：有席位缺席，多数门收紧为 2/2，置信降档：本台账证据强度"
                "低于 N=3 口径，使用方须按降档标注消费。")
        tie_note = note if tie_note is None else tie_note + "；" + note

    return {"majority_items": majority_items,
            "minority_dissents": minority_dissents,
            "downgraded": downgraded,
            "tie_note": tie_note}


def _deep_copy_ballot(ballot):
    """整票全文 deep copy（出口隔离，调用方改不动原始票，票改不动台账）。"""
    return copy.deepcopy(ballot)
