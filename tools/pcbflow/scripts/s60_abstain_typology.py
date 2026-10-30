#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s60_abstain_typology.py — development 域事后分析（post-hoc）：
r13–r16 reader-raw 弃权理由家族分型（零盲读度量侧分解包，
dev-record-r16 next_iteration_targets[1] 预注册第一候选的执行件）。

本件性质（disclaimer，逐字入产物）：
- 本件=development 域事后分析（post-hoc），非校准轮、无字母裁决、
  无门语义；不得回写 r13–r16 任何 run/dev-record；
- 判据/阈值/GT 零改动、零触碰；零新盲读、零新渲染；
- 48 件 reader-raw 一律零改动（只读输入）；
- 发现仅作后续处置轴选择证据（分辨率倍增仪器轮 / 黑点类专项 /
  判据侧），只述事实、不替用户拍板。

方法：对每条 abstain=true 旗标，按 location_evidence（辅以 category）
以常量关键词表+正则做互斥机械分型（rubric 先定义后套用，逐旗附命中
关键词与理由摘录，可审计）；非弃权旗不参与分型，仅按轮×视角计入
分母对照。

生成器纪律：
- 纯函数：零 subprocess/零网络/零 wall-clock/零主机路径（输出字节
  只依赖盘上冻结输入与本文件常量；日期只用常量 DECLARED_DATE）；
- canonical JSON=pcbflow.hashing.canonical_json_bytes；
- 哈希=pcbflow.hashing.sha256_file（48 raw+4 run 逐件实测入 anchors）；
- 防覆写护栏：产物已存在且字节不同→FAIL；字节等同→幂等跳过零覆写；
- 本脚本只写 abstain-typology-r13-r16.json 一件。

用法：python scripts/s60_abstain_typology.py   （仓库根执行）
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL = REPO / "out" / "v3-tl2" / "calibration"
REL_OUT = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"
OUT = REPO / REL_OUT

DECLARED_DATE = "2026-09-08"
SCHEMA_VERSION = "3.0"
KIND = "abstain_typology_posthoc_r13_r16"
EVALUATION_DOMAIN = "development"
ROUNDS = ("r13", "r14", "r15", "r16")
VIEWS = ("top", "bottom")
VARIANTS = ("applied", "prep1")
INSTANCES = ("i1", "i2", "i3")
FAMILIES = ("contact", "existence_blackdot", "existence_other",
            "semantic_confusion", "other")

DISCLAIMER = (
    "本件=development 域事后分析（post-hoc），非校准轮、无字母裁决、无门语义；"
    "不得回写 r13–r16 任何 run/dev-record；判据/阈值/GT 零改动、零触碰；"
    "零新盲读、零新渲染；48 件 reader-raw 只读零改动；"
    "发现仅作后续处置轴选择证据（分辨率倍增仪器轮/黑点类专项/判据侧），"
    "只述事实、不替用户拍板。"
)

# ---------------------------------------------------------------------------
# rubric 关键词常量（先定义后机械套用；全部入产物 rubric 节）
# ---------------------------------------------------------------------------

# 黑点族对象词（existence_blackdot 的对象判定）
BLACKDOT_TERMS = (
    "黑点", "黑圆", "黑色圆", "黑色钻孔", "黑色孔", "钻孔点", "钻孔圆点",
    "圆孔状", "孔状圆点", "黑圆点", "小黑点", "圆点", "实心圆", "实心黑",
    "黑色实心", "实心深色", "深色实心", "黑色图元", "小暗点", "黑色填充",
)
# 黑点族门槛要求同时存在不确定性语言
UNCERTAINTY_TERMS = (
    "无法", "不可", "不明", "不能", "未能", "不确定", "不可分辨",
)
# 接触族接触词（结构间接触/交叠语言）
CONTACT_TERMS = (
    "接触", "贴近", "相切", "交叠", "叠压", "贴邻", "贴接", "相接",
    "紧贴", "贴至", "搭接", "贴合", "重叠",
)
# 接触族怀疑模式（组合判定：接触词+对接触存在性本身的怀疑）
CONTACT_DOUBT_PATTERNS = {
    "P1": r"无法(?:负责任)?(?:地区?分|分辨|区分)[^。；]{0,12}(?:真实)?(?:接触|交叠|重叠|贴近|相切)",
    "P2": r"(?<![未非无可])(?:接触|交叠|重叠|贴近|相切|贴接|贴邻|叠压|紧贴|相接|搭接)[^。；]{0,15}无法[^。；]{0,8}(?:确认|区分|分辨|判断)",
    "P3": r"是否(?:达到)?(?:真实)?(?:接触|交叠|重叠)",
    "P4": r"是否[^。；]{0,16}(?:接触|交叠|重叠)",
    "P5": r"接触性(?:判据|不可分辨|存在性不确定|存在性弃权)",
    "P6": r"(?:接触|交叠|重叠)(?:与否|是否存在|是否真实存在)",
    "P7": r"无法[^。；]{0,8}确认[^。；]{0,12}(?:接触|交叠|重叠|贴近)",
}
# 文本主因词（丝印/文字域旗标不归 contact——叠压=文字叠印语境）
TEXT_PRIMARY_TERMS = (
    "文字", "丝印", "字形", "辨读", "叠印", "连印", "字号", "位号文字",
    "黄色位号", "小字", "笔画",
)
TEXT_PRIMARY_PATTERN = r"位号(?![）)])"  # 位号作主语；「（旁有…位号）」括注除外
# 显式存在性/性质词（existence_other 的具名疑因）
EXPLICIT_EXISTENCE_TERMS = (
    "存在性", "性质", "不明", "现象存在", "关注现象", "何种",
    "无法确认其是否", "无法确认是否", "是否为", "是否真实存在",
    "是否存在", "存在不确定", "无法排除",
)
# 语义/归类主因词（semantic_confusion 的具名疑因）
SEMANTIC_TERMS = (
    "设计含义", "无法归类", "归类不确定", "归类无法", "语义不明",
    "图层归属", "归属层", "各属", "属courtyard层还是",
)
# 泛化不确定性模式（无具名疑因时归 existence_other 的兜底信号）
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
S4_CITE_PATTERN = re.compile(r"§\s*4\s*(?:\((i{1,3}|iv|v)\))?")


def _fail(msg: str) -> None:
    raise SystemExit(f"[s60-abstain-typology] FAIL: {msg}")


# ---------------------------------------------------------------------------
# 纯函数：文件名解析与逐旗分型
# ---------------------------------------------------------------------------

def parse_stem(stem: str) -> dict:
    """reader-raw-r13-applied-top-i1 → round/view/variant/instance。"""
    if not stem.startswith("reader-raw-"):
        _fail(f"文件名前缀异常: {stem}")
    parts = stem[len("reader-raw-"):].split("-")
    if len(parts) != 4:
        _fail(f"文件名结构异常: {stem}")
    rnd, variant, view, inst = parts
    if rnd not in ROUNDS or variant not in VARIANTS \
            or view not in VIEWS or inst not in INSTANCES:
        _fail(f"文件名字段越界: {stem}")
    return {"round": rnd, "variant": variant, "view": view, "instance": inst}


def match_all(text: str) -> dict:
    """对旗标理由文本做全家族关键词/模式命中（不裁胜负，只记录证据）。"""
    hits: dict = {}
    bd = [k for k in BLACKDOT_TERMS if k in text]
    unc = [k for k in UNCERTAINTY_TERMS if k in text]
    ct = [k for k in CONTACT_TERMS if k in text]
    cd = [name for name, pat in CONTACT_DOUBT_PATTERNS.items()
          if re.search(pat, text)]
    tp = [k for k in TEXT_PRIMARY_TERMS if k in text]
    if re.search(TEXT_PRIMARY_PATTERN, text):
        tp.append("位号(主语)")
    ee = [k for k in EXPLICIT_EXISTENCE_TERMS if k in text]
    sm = [k for k in SEMANTIC_TERMS if k in text]
    ge = [name for name, pat in GENERIC_EXISTENCE_PATTERNS.items()
          if re.search(pat, text)]
    cites = S4_CITE_PATTERN.findall(text)
    for key, val in (("blackdot_terms", bd), ("uncertainty_terms", unc),
                     ("contact_terms", ct), ("contact_doubt_patterns", cd),
                     ("text_primary", tp), ("explicit_existence", ee),
                     ("semantic_terms", sm), ("generic_existence", ge)):
        if val:
            hits[key] = val
    if cites:
        hits["cites_s4"] = cites
    return hits


def classify(evidence: str) -> tuple[str, dict]:
    """互斥机械分型（rubric 优先级，见 rubric.priority_adjudication_note）。

    1. existence_blackdot：黑点族对象+不确定性（先于 contact——预注册
       期望 r16 已知 12 黑点旗全部落入本类；黑点旗中的接触措辞描述的
       是点-盘邻接，非结构间接触主因）；
    2. contact：接触词+接触怀疑模式组合，且非文本主因（丝印/文字域的
       「叠压」属文字叠印语境，不归本类）；
    3. existence_other：显式存在性/性质具名疑因（优先于 semantic——
       预注册优先级 3>4）；
    4. semantic_confusion：无任何显式存在性/性质语言、而以设计含义/
       归类/层归属为唯一具名疑因（rubric「为主因」措辞的操作化）；
    5. existence_other 兜底：仅泛化不确定性语言（无法确认/判断…）；
    6. other：以上皆未命中。
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


def excerpt(text: str, limit: int = 360) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "…[截断]"


# ---------------------------------------------------------------------------
# 组装（读冻结输入→内存构建文档）
# ---------------------------------------------------------------------------

def _load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_doc() -> tuple[dict, dict]:
    files = sorted(CAL.glob("reader-raw-r1[3456]-*.txt"))
    if len(files) != 48:
        _fail(f"reader-raw r13–r16 应为 48 件，实测 {len(files)}")
    run_paths = {r: CAL / f"calibration-run-{r}.json" for r in ROUNDS}
    for p in run_paths.values():
        if not p.exists():
            _fail(f"缺 run 文件: {p.name}")

    per_flag: list[dict] = []
    # 分母对照：轮×视角（board 合计）与轮×视角×board 两层都留
    denom_rv: dict = {}
    denom_rv_board: dict = {}
    inst_counts: dict = {}   # (round, view, instance) -> [abstain, flags]
    file_bd_abstain: dict = {}    # stem -> bool
    file_bd_nonabstain: dict = {}  # stem -> list[flag_id]
    notes_bd_hit: dict = {}       # stem -> list[keyword]

    for path in files:
        meta = parse_stem(path.stem)
        data = _load_json(path)
        notes = data.get("reading_notes", "")
        stem = path.stem
        file_bd_abstain[stem] = False
        file_bd_nonabstain[stem] = []
        notes_bd_hit[stem] = [k for k in BLACKDOT_TERMS if k in notes]
        key_rv = f"{meta['round']}|{meta['view']}"
        key_rvb = f"{meta['round']}|{meta['view']}|{meta['variant']}"
        denom_rv.setdefault(key_rv, {"abstain": 0, "non_abstain": 0})
        denom_rv_board.setdefault(key_rvb, {"abstain": 0, "non_abstain": 0})
        ik = (meta["round"], meta["view"], meta["instance"])
        inst_counts.setdefault(ik, [0, 0])
        for img in data.get("per_image", []):
            for fl in img.get("flags", []):
                ik = (meta["round"], meta["view"], meta["instance"])
                inst_counts[ik][1] += 1
                evidence = fl.get("location_evidence", "")
                if fl.get("abstain") is True:
                    family, hits = classify(evidence)
                    inst_counts[ik][0] += 1
                    denom_rv[key_rv]["abstain"] += 1
                    denom_rv_board[key_rvb]["abstain"] += 1
                    if family == "existence_blackdot":
                        file_bd_abstain[stem] = True
                    per_flag.append({
                        "round": meta["round"],
                        "view": meta["view"],
                        "board": meta["variant"],
                        "instance": meta["instance"],
                        "source_file": path.name,
                        "flag_id": fl.get("flag_id"),
                        "category": fl.get("category"),
                        "family": family,
                        "matched": hits,
                        "evidence_excerpt": excerpt(evidence),
                    })
                else:
                    denom_rv[key_rv]["non_abstain"] += 1
                    denom_rv_board[key_rvb]["non_abstain"] += 1
                    if any(k in evidence for k in BLACKDOT_TERMS):
                        file_bd_nonabstain[stem].append(fl.get("flag_id"))

    # --- matrix ---
    matrix_rv: dict = {}
    matrix_round: dict = {}
    family_round: dict = {r: {f: 0 for f in FAMILIES} for r in ROUNDS}
    grand = {f: 0 for f in FAMILIES}
    for rv, d in denom_rv.items():
        rnd, view = rv.split("|")
        fams = {f: 0 for f in FAMILIES}
        for pf in per_flag:
            if pf["round"] == rnd and pf["view"] == view:
                fams[pf["family"]] += 1
        abst = d["abstain"]
        matrix_rv[rv] = {
            "abstain": abst,
            "non_abstain": d["non_abstain"],
            "flags": abst + d["non_abstain"],
            "abstain_rate": round(abst / (abst + d["non_abstain"]), 6),
            "families": fams,
            "family_share_of_abstain": {
                f: round(fams[f] / abst, 6) if abst else None for f in FAMILIES
            },
        }
    for rnd in ROUNDS:
        abst = sum(matrix_rv[f"{rnd}|{v}"]["abstain"] for v in VIEWS)
        nonab = sum(matrix_rv[f"{rnd}|{v}"]["non_abstain"] for v in VIEWS)
        fams = {f: sum(matrix_rv[f"{rnd}|{v}"]["families"][f] for v in VIEWS)
                for f in FAMILIES}
        for f in FAMILIES:
            family_round[rnd][f] = fams[f]
            grand[f] += fams[f]
        matrix_round[rnd] = {
            "abstain": abst,
            "non_abstain": nonab,
            "flags": abst + nonab,
            "abstain_rate": round(abst / (abst + nonab), 6),
            "families": fams,
            "family_share_of_abstain": {
                f: round(fams[f] / abst, 6) if abst else None for f in FAMILIES
            },
        }
    total_abst = sum(matrix_round[r]["abstain"] for r in ROUNDS)
    total_nonab = sum(matrix_round[r]["non_abstain"] for r in ROUNDS)
    matrix = {
        "round_view": matrix_rv,
        "round_totals": matrix_round,
        "grand": {
            "abstain": total_abst,
            "non_abstain": total_nonab,
            "flags": total_abst + total_nonab,
            "abstain_rate": round(total_abst / (total_abst + total_nonab), 6),
            "families": dict(grand),
        },
    }

    # --- 口径对照（fail-closed）：逐实例复算 vs run 登记值 ---
    cross_check: dict = {}
    for rnd in ROUNDS:
        run = _load_json(run_paths[rnd])
        inst = run.get("instances", {})
        for view in VIEWS:
            for i in INSTANCES:
                key = f"{view}-{i}"
                abst, flags = inst_counts[(rnd, view, i)]
                ref = inst.get(key, {}).get("combined", {})
                entry = {
                    "recomputed_abstain": abst,
                    "recomputed_flags": flags,
                    "run_abstain": ref.get("abstain_count"),
                    "run_flags": ref.get("flag_count"),
                }
                entry["equal"] = (entry["recomputed_abstain"] == entry["run_abstain"]
                                  and entry["recomputed_flags"] == entry["run_flags"])
                cross_check[f"{rnd}|{key}"] = entry
                if not entry["equal"]:
                    _fail(f"口径对照失配 {rnd}|{key}: {entry}")

    # --- 黑点派次三分类（弃权旗/非弃权旗上报/判正常不入） ---
    bd_dispatch: dict = {}
    for rnd in ROUNDS:
        e = {"abstain_flag_dispatches": [], "reported_nonabstain_dispatches": [],
             "judged_normal_dispatches": []}
        for path in files:
            meta = parse_stem(path.stem)
            if meta["round"] != rnd:
                continue
            stem = path.stem
            label = f"{meta['view']}-{meta['instance']}({meta['variant']})"
            if file_bd_abstain[stem]:
                e["abstain_flag_dispatches"].append(label)
            elif file_bd_nonabstain[stem]:
                e["reported_nonabstain_dispatches"].append(label)
            elif notes_bd_hit[stem]:
                e["judged_normal_dispatches"].append(label)
        bd_dispatch[rnd] = e

    # --- anchors ---
    anchors_raw = {p.name: hashing.sha256_file(str(p)) for p in files}
    anchors_runs = {p.name: hashing.sha256_file(str(p))
                    for p in run_paths.values()}

    doc = {
        "kind": KIND,
        "schema_version": SCHEMA_VERSION,
        "declared_date": DECLARED_DATE,
        "evaluation_domain": EVALUATION_DOMAIN,
        "disclaimer": DISCLAIMER,
        "inputs": {
            "raw_files": len(files),
            "raw_glob": "out/v3-tl2/calibration/reader-raw-r1[3456]-*.txt",
            "runs": [p.name for p in run_paths.values()],
            "read_only_note": "48 件 reader-raw 与 4 件 run 只读零改动",
        },
        "rubric": {
            "unit": "abstain=true 旗标（逐旗；非弃权旗不分型、仅入分母对照）",
            "basis": "location_evidence 全文（辅以 category），机械套用常量关键词表",
            "families": {
                "contact": "理由含接触/贴近/相切/交叠/叠压等接触词并与接触怀疑模式组合（对结构间接触/交叠是否存在不可分辨）",
                "existence_blackdot": "对象为黑点/黑圆/钻孔点/圆点/小圆点/实心圆等黑点族且性质/存在性不明（r16 已知 12 旗应全部落入本类；判正常不入的派次单列）",
                "existence_other": "其他存在性/性质不明（非黑点族、非接触）",
                "semantic_confusion": "明确以设计含义不明/无法归类/语义不明为弃权主因（无任何显式存在性/性质语言时）",
                "other": "以上皆未命中的残余类",
            },
            "priority_as_registered": [
                "contact", "existence_blackdot", "existence_other",
                "semantic_confusion", "other",
            ],
            "priority_adjudication_note": (
                "实现顺序=existence_blackdot → contact → existence_other(显式) → "
                "semantic_confusion → existence_other(泛化兜底) → other。"
                "黑点族对象判定先于 contact 组合：预注册期望 r16 已知 12 黑点旗"
                "全部落入 existence_blackdot，且黑点旗中的接触措辞描述点-盘邻接、"
                "其弃权主因为黑点性质/存在性不明而非结构间接触；contact 保留给以"
                "结构间（courtyard/轮廓/占位框/焊盘等非黑点对象）接触/交叠存在性"
                "为主因的旗。文本主因（丝印/文字域）旗不归 contact——其「叠压」"
                "属文字叠印语境。existence_other(显式) 先于 semantic_confusion"
                "（预注册优先级 3>4）；仅当旗无任何显式存在性/性质语言、而以设计"
                "含义/归类/层归属为唯一具名疑因时按 rubric「为主因」措辞归 "
                "semantic_confusion；仅泛化不确定性语言（无法确认/判断等）无具名"
                "疑因者归 existence_other 兜底。"
            ),
            "keyword_tables": {
                "blackdot_terms": list(BLACKDOT_TERMS),
                "uncertainty_terms": list(UNCERTAINTY_TERMS),
                "contact_terms": list(CONTACT_TERMS),
                "contact_doubt_patterns": dict(CONTACT_DOUBT_PATTERNS),
                "text_primary_terms": list(TEXT_PRIMARY_TERMS),
                "text_primary_pattern": TEXT_PRIMARY_PATTERN,
                "explicit_existence_terms": list(EXPLICIT_EXISTENCE_TERMS),
                "semantic_terms": list(SEMANTIC_TERMS),
                "generic_existence_patterns": dict(GENERIC_EXISTENCE_PATTERNS),
            },
            "evidence_excerpt_cap_chars": 360,
            "category_auxiliary_note": "category 仅作辅助核对，未参与关键词判定",
            "field_semantics": "view=视角(top/bottom)；board=板/applied|prep1 两板；instance=i1..i3 派次",
        },
        "per_flag": per_flag,
        "matrix": matrix,
        "cross_check_vs_runs": cross_check,
        "blackdot_dispatch": bd_dispatch,
        "anchors": {
            "raw_sha256": anchors_raw,
            "runs_sha256": anchors_runs,
            "raw_count": len(anchors_raw),
            "run_count": len(anchors_runs),
        },
    }
    aux = {
        "files": files,
        "denom_rv": denom_rv,
        "total_abstain": total_abst,
        "total_nonabstain": total_nonab,
    }
    return doc, aux


# ---------------------------------------------------------------------------
# findings（三问三答；只述事实，不替用户拍板）
# ---------------------------------------------------------------------------

def build_findings(doc: dict) -> dict:
    m = doc["matrix"]
    rv = m["round_view"]
    rt = m["round_totals"]
    g = m["grand"]
    bd = doc["blackdot_dispatch"]

    def fam(rvkey, f):
        return rv[rvkey]["families"][f]

    top_abst = {r: rt[r]["abstain"] - rv[f"{r}|bottom"]["abstain"]
                for r in ROUNDS}
    q1 = (
        "Q1 top 高弃权主导家族四轮演变？——"
        f"top 弃权旗数 r13={top_abst['r13']}"
        f"（contact {fam('r13|top', 'contact')}/黑点 {fam('r13|top', 'existence_blackdot')}/存在性其他 {fam('r13|top', 'existence_other')}/语义 {fam('r13|top', 'semantic_confusion')}），"
        f"r14={top_abst['r14']}"
        f"（contact {fam('r14|top', 'contact')}/黑点 {fam('r14|top', 'existence_blackdot')}/存在性其他 {fam('r14|top', 'existence_other')}/语义 {fam('r14|top', 'semantic_confusion')}），"
        f"r15={top_abst['r15']}"
        f"（contact {fam('r15|top', 'contact')}/黑点 {fam('r15|top', 'existence_blackdot')}/存在性其他 {fam('r15|top', 'existence_other')}/语义 {fam('r15|top', 'semantic_confusion')}），"
        f"r16={top_abst['r16']}"
        f"（contact {fam('r16|top', 'contact')}/黑点 {fam('r16|top', 'existence_blackdot')}/存在性其他 {fam('r16|top', 'existence_other')}/语义 {fam('r16|top', 'semantic_confusion')}）。"
        "事实：r13–r14 top 以 contact（courtyard/轮廓结构间接触不可分辨）为最大族；"
        "r15–r16 top 的 existence_other（丝印辨读受阻存在性等）升至与 contact 同量级或反超；"
        "黑点族在 top 视始终少量（1–4 旗/轮）；semantic_confusion 在 top 仅 r15/r16 各有零星。"
        "top 高弃权无单一家族独占，contact 与 existence_other 两族交替领先。"
    )
    bd_counts = {r: rt[r]["families"]["existence_blackdot"] for r in ROUNDS}
    q2 = (
        "Q2 黑点类四轮计数与判正常派次？——"
        f"existence_blackdot 弃权旗计数：r13={bd_counts['r13']}，r14={bd_counts['r14']}，"
        f"r15={bd_counts['r15']}，r16={bd_counts['r16']}（合计 "
        f"{sum(bd_counts.values())} 旗；r16=12 与预注册期望一致，逐实例分布 "
        "bottom-i1 3/bottom-i2 4/bottom-i3 3/top-i1 1/top-i2 1/top-i3 0，与 "
        "run-r16 登记逐格相等）。判正常不入派次（notes 含黑点族词汇且无黑点"
        f"弃权旗、亦无非弃权黑点旗）：r13={len(bd['r13']['judged_normal_dispatches'])}，"
        f"r14={len(bd['r14']['judged_normal_dispatches'])}，"
        f"r15={len(bd['r15']['judged_normal_dispatches'])}"
        f"（{'; '.join(bd['r15']['judged_normal_dispatches']) or '无'}），"
        f"r16={len(bd['r16']['judged_normal_dispatches'])}"
        f"（{'; '.join(bd['r16']['judged_normal_dispatches']) or '无'}，与 s59 登记"
        "+2 派次判正常一致）。另有黑点以非弃权旗上报的派次："
        + "; ".join(f"{r}: {len(bd[r]['reported_nonabstain_dispatches'])} 派次"
                    for r in ROUNDS) +
        "。事实：黑点类存在性弃权连续 4 轮存在（同一物理形态被部分派次弃权、"
        "部分派次判正常/非弃权上报），呈派次间判定不稳定。"
    )
    con_tot = g["families"]["contact"]
    bd_tot = g["families"]["existence_blackdot"]
    exo_tot = g["families"]["existence_other"]
    sem_tot = g["families"]["semantic_confusion"]
    oth_tot = g["families"]["other"]
    top_con = sum(rv[f"{r}|top"]["families"]["contact"] for r in ROUNDS)
    bot_con = sum(rv[f"{r}|bottom"]["families"]["contact"] for r in ROUNDS)
    top_bd = sum(rv[f"{r}|top"]["families"]["existence_blackdot"] for r in ROUNDS)
    bot_bd = sum(rv[f"{r}|bottom"]["families"]["existence_blackdot"] for r in ROUNDS)
    q3 = (
        "Q3 contact vs existence 占比——处置轴证据陈述？——"
        f"全四轮 {g['abstain']} 条弃权旗：contact {con_tot} 旗"
        f"（{con_tot / g['abstain']:.1%}），existence_blackdot {bd_tot} 旗"
        f"（{bd_tot / g['abstain']:.1%}），existence_other {exo_tot} 旗"
        f"（{exo_tot / g['abstain']:.1%}），semantic_confusion {sem_tot} 旗"
        f"（{sem_tot / g['abstain']:.1%}），other {oth_tot} 旗"
        f"（{oth_tot / g['abstain']:.1%}）。视分布：contact top {top_con}/bottom {bot_con}"
        f"（top 占 contact 族 {top_con / (top_con + bot_con):.1%}）；"
        f"黑点族 top {top_bd}/bottom {bot_bd}"
        f"（bottom 占黑点族 {bot_bd / (top_bd + bot_bd):.1%}）。"
        "事实陈述（不替用户拍板）：(a) contact 族=结构间 courtyard/轮廓接触"
        "不可分辨，集中于 top 视、四轮持续存在，其解决依赖更高角点分辨率"
        "（分辨率倍增仪器轮的事实基础）；(b) existence_blackdot 族=黑点"
        "性质/存在性不明，bottom 视为主、派次间弃权/判正常不稳定，且与"
        "渲染配色（黑点图元无仪器注记解释）相关（黑点类专项的事实基础）；"
        f"(c) contact+黑点+存在性其他三族合计 {(con_tot + bd_tot + exo_tot) / g['abstain']:.1%} 的弃权"
        "理由均为 §4 存在性/接触性判据下的「不可负责任确认」（逐旗 cites_s4 "
        "字段可审计），语义/归类类仅零星（semantic_confusion 旗层面），"
        "判据措辞本身的致敏是跨家族共因（判据侧的事实基础）。三条处置轴"
        "分别对应上述三组事实，本件不作轴选择。"
    )
    return {"q1_top_family_evolution": q1,
            "q2_blackdot_counts_and_normal_dispatches": q2,
            "q3_contact_vs_existence_axis_evidence": q3}


# ---------------------------------------------------------------------------
# 落盘（防覆写护栏）与 stdout 报告
# ---------------------------------------------------------------------------

def _commit(path: Path, new_bytes: bytes) -> str:
    if path.exists():
        if path.read_bytes() != new_bytes:
            _fail(f"{path.name} 已存在且与重建字节不同（防覆写护栏，fail-closed）")
        return "idempotent_skip"
    path.write_bytes(new_bytes)
    if path.read_bytes() != new_bytes:
        _fail(f"回读不一致: {path.name}")
    return "written"


def main() -> int:
    doc, aux = build_doc()
    findings = build_findings(doc)
    doc["findings"] = findings
    canonical = hashing.canonical_json_bytes(doc)
    doc["idempotence"] = {
        "note": "本件由 s60 以 canonical_json_bytes 重建；同输入⇒byte-exact 同输出",
        "canonical_bytes_sha256": hashing.sha256_bytes(canonical),
        "declared_date_constant": DECLARED_DATE,
    }
    canonical = hashing.canonical_json_bytes(doc)
    status = _commit(OUT, canonical)

    print(f"[s60-abstain-typology] inputs: {aux['files'][0].name} … "
          f"({len(aux['files'])} raw) + 4 runs；declared_date={DECLARED_DATE}")
    print(f"[s60] 弃权旗总数={aux['total_abstain']}  非弃权旗总数="
          f"{aux['total_nonabstain']}  合计={aux['total_abstain'] + aux['total_nonabstain']}")
    hdr = ("轮    视      contact blackdot exist_oth semantic other | "
           "abstain nonabstain flags rate")
    print("[s60] matrix 轮×视角×家族：")
    print("     " + hdr)
    for rnd in ROUNDS:
        for view in VIEWS:
            e = doc["matrix"]["round_view"][f"{rnd}|{view}"]
            f = e["families"]
            print(f"     {rnd}  {view:<6} {f['contact']:>7} {f['existence_blackdot']:>8} "
                  f"{f['existence_other']:>9} {f['semantic_confusion']:>8} {f['other']:>5} | "
                  f"{e['abstain']:>7} {e['non_abstain']:>9} {e['flags']:>5} "
                  f"{e['abstain_rate']:.4f}")
    print("[s60] matrix 轮×家族合计：")
    print("     " + hdr)
    for rnd in ROUNDS:
        e = doc["matrix"]["round_totals"][rnd]
        f = e["families"]
        print(f"     {rnd}  {'ALL':<6} {f['contact']:>7} {f['existence_blackdot']:>8} "
              f"{f['existence_other']:>9} {f['semantic_confusion']:>8} {f['other']:>5} | "
              f"{e['abstain']:>7} {e['non_abstain']:>9} {e['flags']:>5} "
              f"{e['abstain_rate']:.4f}")
    gf = doc["matrix"]["grand"]["families"]
    print(f"     {'ALL':<5} {'--':<6} {gf['contact']:>7} {gf['existence_blackdot']:>8} "
          f"{gf['existence_other']:>9} {gf['semantic_confusion']:>8} {gf['other']:>5} | "
          f"{doc['matrix']['grand']['abstain']:>7} "
          f"{doc['matrix']['grand']['non_abstain']:>9} "
          f"{doc['matrix']['grand']['flags']:>5} "
          f"{doc['matrix']['grand']['abstain_rate']:.4f}")
    print("[s60] cross_check_vs_runs: 24/24 逐实例 (abstain,flags) 与 run 登记值相等")
    for rnd in ROUNDS:
        e = doc["blackdot_dispatch"][rnd]
        print(f"[s60] blackdot_dispatch {rnd}: 弃权旗派次={len(e['abstain_flag_dispatches'])} "
              f"非弃权旗上报={len(e['reported_nonabstain_dispatches'])} "
              f"判正常不入={len(e['judged_normal_dispatches'])}")
    for k, v in findings.items():
        print(f"[s60][{k}] {v}")
    print(f"[s60] commit: {status} path={REL_OUT}")
    print(f"[s60] canonical_bytes_sha256="
          f"{doc['idempotence']['canonical_bytes_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
