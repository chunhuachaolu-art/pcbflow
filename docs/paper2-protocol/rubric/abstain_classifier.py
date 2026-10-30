#!/usr/bin/env python
"""abstain_classifier.py — abstention-typology rubric: wordlists + priority
adjudication algorithm (release copy for the PAPER-P2-3 artifact package).

This module is the authoritative, executable form of the abstention typology
rubric registered in the frozen development-domain post-hoc analysis file
``abstain-typology-r13-r16.json`` (dev repo path
out/v3-tl2/calibration/abstain-typology-r13-r16.json, sha256
6dadac8d72cfbb358fc37fe82ec710f5f3421efcaedb4041b28b53283681bc80).

Why the algorithm ships with the wordlists (r25 lesson)
-------------------------------------------------------
Recounting keyword occurrences over a corpus (a "naive wordlist count") does
NOT reproduce the registered per-round family counts. The registered counts
were produced by this priority adjudication algorithm: mutually exclusive,
per-flag, first-match-wins in a fixed order. An open release must contain the
algorithm itself, not only the vocabulary.

Classification unit
-------------------
One flag with ``abstain == true``; the input text is the flag's
``location_evidence`` field in full (``category`` is auxiliary bookkeeping and
never participates in keyword matching). Non-abstain flags are never typed.

Decision order (implementation order; see ``classify``)
-------------------------------------------------------
1. existence_blackdot : any blackdot term AND any uncertainty term
   (blackdot precedes contact by preregistration: contact wording on
   blackdot flags describes dot-pad adjacency, the abstention driver is the
   blackdot's unclear nature/existence)
2. contact            : any contact term AND any contact-doubt pattern
                        (P1-P7) AND no text-primary term
   (silk/text-context flags never classify as contact: their "overlap"
   wording belongs to text-overprint context)
3. existence_other    : any explicit existence term
   (explicit existence precedes semantic_confusion: preregistered priority
   3 > 4)
4. semantic_confusion : any semantic term (steps 1-3 all missed)
5. existence_other    : any generic existence pattern G1-G8 (fallback for
   unattributed generalized uncertainty)
6. other              : residual

Note on the two "orders"
------------------------
``priority_as_registered`` (in the JSON: contact, existence_blackdot,
existence_other, semantic_confusion, other) is the registration-order list as
frozen in the source file. The IMPLEMENTATION order above differs (blackdot
first); the deviation is itself preregistered in the source file's
``priority_adjudication_note``. Both orders are recorded verbatim in the
release JSON. Reproducing the registered counts requires the implementation
order.

Determinism
-----------
Pure functions over (text, constant tables). Same input -> same output, no
I/O, no wall-clock, no randomness. Companion ``replay_r13_r16.py`` replays
this classifier against the registered r13-r16 chain and fails closed on any
mismatch.

License: Apache-2.0.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# rubric keyword constants — byte-faithful port of the frozen tables
# (scripts/s60_abstain_typology.py constants, which were serialized verbatim
# into abstain-typology-r13-r16.json rubric.keyword_tables).
# ---------------------------------------------------------------------------

#: blackdot-family object words (object test for existence_blackdot)
BLACKDOT_TERMS = (
    "黑点", "黑圆", "黑色圆", "黑色钻孔", "黑色孔", "钻孔点", "钻孔圆点",
    "圆孔状", "孔状圆点", "黑圆点", "小黑点", "圆点", "实心圆", "实心黑",
    "黑色实心", "实心深色", "深色实心", "黑色图元", "小暗点", "黑色填充",
)
#: uncertainty words (gate required together with blackdot terms)
UNCERTAINTY_TERMS = (
    "无法", "不可", "不明", "不能", "未能", "不确定", "不可分辨",
)
#: contact-family contact words (inter-structure contact/overlap language)
CONTACT_TERMS = (
    "接触", "贴近", "相切", "交叠", "叠压", "贴邻", "贴接", "相接",
    "紧贴", "贴至", "搭接", "贴合", "重叠",
)
#: contact-doubt patterns (combination requirement: contact word + doubt
#: about the existence of the contact itself)
CONTACT_DOUBT_PATTERNS = {
    "P1": r"无法(?:负责任)?(?:地区?分|分辨|区分)[^。；]{0,12}(?:真实)?(?:接触|交叠|重叠|贴近|相切)",
    "P2": r"(?<![未非无可])(?:接触|交叠|重叠|贴近|相切|贴接|贴邻|叠压|紧贴|相接|搭接)[^。；]{0,15}无法[^。；]{0,8}(?:确认|区分|分辨|判断)",
    "P3": r"是否(?:达到)?(?:真实)?(?:接触|交叠|重叠)",
    "P4": r"是否[^。；]{0,16}(?:接触|交叠|重叠)",
    "P5": r"接触性(?:判据|不可分辨|存在性不确定|存在性弃权)",
    "P6": r"(?:接触|交叠|重叠)(?:与否|是否存在|是否真实存在)",
    "P7": r"无法[^。；]{0,8}确认[^。；]{0,12}(?:接触|交叠|重叠|贴近)",
}
#: text-primary words (silk/text-domain flags never classify as contact)
TEXT_PRIMARY_TERMS = (
    "文字", "丝印", "字形", "辨读", "叠印", "连印", "字号", "位号文字",
    "黄色位号", "小字", "笔画",
)
TEXT_PRIMARY_PATTERN = r"位号(?![）)])"  # reference designator as subject;
#                                 parenthetical "（旁有…位号）" excluded
#: explicit existence/nature words (named driver for existence_other)
EXPLICIT_EXISTENCE_TERMS = (
    "存在性", "性质", "不明", "现象存在", "关注现象", "何种",
    "无法确认其是否", "无法确认是否", "是否为", "是否真实存在",
    "是否存在", "存在不确定", "无法排除",
)
#: semantic/classification driver words (semantic_confusion)
SEMANTIC_TERMS = (
    "设计含义", "无法归类", "归类不确定", "归类无法", "语义不明",
    "图层归属", "归属层", "各属", "属courtyard层还是",
)
#: generic uncertainty patterns (fallback signal for existence_other)
GENERIC_EXISTENCE_PATTERNS = {
    "G1": r"是[^。；，]{0,30}还是",
    "G2": r"无法[^。；]{0,10}确认",
    "G3": r"无法[^。；]{0,10}判断",
    "G4": r"无法[^。；]{0,10}判定",
    "G5": r"不足以负责任",
    "G6": r"无法[^。；]{0,6}区分",
    "G7": r"无法[^。；]{0,6}分辨",
    "G8": r"无法[^。；]{0,8}追踪确认",
}

FAMILIES = ("contact", "existence_blackdot", "existence_other",
            "semantic_confusion", "other")

#: implementation order (see module docstring); registration order differs
#: and both are recorded in the release JSON.
PRIORITY_AS_IMPLEMENTED = (
    "existence_blackdot", "contact", "existence_other(explicit)",
    "semantic_confusion", "existence_other(generic-fallback)", "other",
)

_COMPILE_CACHE = {
    "contact_doubt": [(k, re.compile(p))
                      for k, p in CONTACT_DOUBT_PATTERNS.items()],
    "generic": [(k, re.compile(p))
                for k, p in GENERIC_EXISTENCE_PATTERNS.items()],
    "text_primary": re.compile(TEXT_PRIMARY_PATTERN),
}

# Keyword tables as a JSON-compatible dict (verbatim mirror of the frozen
# rubric.keyword_tables block; cross-checked against the release JSON by
# verify_rubric_json).
KEYWORD_TABLES = {
    "blackdot_terms": list(BLACKDOT_TERMS),
    "uncertainty_terms": list(UNCERTAINTY_TERMS),
    "contact_terms": list(CONTACT_TERMS),
    "contact_doubt_patterns": dict(CONTACT_DOUBT_PATTERNS),
    "text_primary_terms": list(TEXT_PRIMARY_TERMS),
    "text_primary_pattern": TEXT_PRIMARY_PATTERN,
    "explicit_existence_terms": list(EXPLICIT_EXISTENCE_TERMS),
    "semantic_terms": list(SEMANTIC_TERMS),
    "generic_existence_patterns": dict(GENERIC_EXISTENCE_PATTERNS),
}

# ---------------------------------------------------------------------------
# classification (pure functions)
# ---------------------------------------------------------------------------


def match_all(text: str) -> dict:
    """Record every wordlist/pattern hit in the evidence text.

    No adjudication here — hits are audit evidence only. Returns a dict with
    only the non-empty hit groups, mirroring the frozen per_flag.matched
    schema: keys blackdot_terms / uncertainty_terms / contact_terms /
    contact_doubt_patterns / text_primary / explicit_existence /
    semantic_terms / generic_existence (values = lists of terms or pattern
    names, in table order).
    """
    hits: dict = {}
    bd = [k for k in BLACKDOT_TERMS if k in text]
    unc = [k for k in UNCERTAINTY_TERMS if k in text]
    ct = [k for k in CONTACT_TERMS if k in text]
    cd = [name for name, rx in _COMPILE_CACHE["contact_doubt"]
          if rx.search(text)]
    tp = [k for k in TEXT_PRIMARY_TERMS if k in text]
    if _COMPILE_CACHE["text_primary"].search(text):
        tp.append("位号(主语)")
    ee = [k for k in EXPLICIT_EXISTENCE_TERMS if k in text]
    sm = [k for k in SEMANTIC_TERMS if k in text]
    ge = [name for name, rx in _COMPILE_CACHE["generic"] if rx.search(text)]
    for key, val in (("blackdot_terms", bd), ("uncertainty_terms", unc),
                     ("contact_terms", ct), ("contact_doubt_patterns", cd),
                     ("text_primary", tp), ("explicit_existence", ee),
                     ("semantic_terms", sm), ("generic_existence", ge)):
        if val:
            hits[key] = val
    return hits


def classify(evidence: str) -> tuple:
    """Mutually exclusive mechanical typing of one abstention reason.

    Implements the preregistered priority adjudication (see module docstring
    for the full decision order and its rationale). Returns
    ``(family, hits)`` where ``family`` is one of FAMILIES and ``hits`` is
    the match_all audit record.
    """
    hits = match_all(evidence)
    bd = hits.get("blackdot_terms", [])
    unc = hits.get("uncertainty_terms", [])
    ct = hits.get("contact_terms", [])
    cd = hits.get("contact_doubt_patterns", [])
    tp = hits.get("text_primary", [])
    ee = hits.get("explicit_existence", [])
    sm = hits.get("semantic_terms", [])
    ge = hits.get("generic_existence", [])
    if bd and unc:
        return "existence_blackdot", hits
    if ct and cd and not tp:
        return "contact", hits
    if ee:
        return "existence_other", hits
    if sm:
        return "semantic_confusion", hits
    if ge:
        return "existence_other", hits
    return "other", hits


# ---------------------------------------------------------------------------
# release-JSON cross-check (fail-closed: wordlist drift => error)
# ---------------------------------------------------------------------------


def verify_rubric_json(path) -> dict:
    """Assert that a release rubric JSON carries the exact tables this
    module implements. Fail-closed: any drift between the JSON wordlists and
    the code constants raises ``SystemExit`` (never silently proceeds).
    """
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    tables = doc.get("rubric", {}).get("keyword_tables")
    if tables is None:
        raise SystemExit(
            f"[abstain-classifier] FAIL: {path} has no rubric.keyword_tables")
    if tables != KEYWORD_TABLES:
        diffs = [k for k in sorted(set(tables) | set(KEYWORD_TABLES))
                 if tables.get(k) != KEYWORD_TABLES.get(k)]
        raise SystemExit(
            "[abstain-classifier] FAIL: rubric JSON wordlists differ from "
            f"code constants: {diffs}")
    note = doc.get("rubric", {}).get("priority_adjudication_note", "")
    if not note:
        raise SystemExit(
            "[abstain-classifier] FAIL: priority_adjudication_note missing")
    return {
        "rubric_json": str(path),
        "keyword_tables_verified": sorted(KEYWORD_TABLES.keys()),
        "priority_as_registered":
            doc["rubric"]["priority_as_registered"],
        "priority_as_implemented": list(PRIORITY_AS_IMPLEMENTED),
        "order_deviation_preregistered": True,
        "families": list(FAMILIES),
    }


def excerpt(text: str, limit: int = 360) -> str:
    """Truncate long evidence for audit records (frozen convention: 360
    chars + ellipsis marker)."""
    if len(text) <= limit:
        return text
    return text[:limit] + "…[截断]"


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("usage: python abstain_classifier.py <text-to-classify "
              "OR path-to-rubric.json ending in .json>")
        sys.exit(2)
    arg = sys.argv[1]
    if arg.endswith(".json"):
        import json
        print(json.dumps(verify_rubric_json(arg), ensure_ascii=False,
                         indent=1))
    else:
        family, hits = classify(arg)
        print(family)
        print(json.dumps(hits, ensure_ascii=False, indent=1))
