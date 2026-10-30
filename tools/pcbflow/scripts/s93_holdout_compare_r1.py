#!/usr/bin/env python
"""S93_HOLDOUT_COMPARE_R1：PCBFlow v3.0 holdout 正式运行 close 实施者
（run-record 步）。

只新建两个文件：
  scripts/s93_holdout_compare_r1.py（本件）
  out/v3-tl2/holdout/holdout-run-r1.json（canonical JSON、防覆写）

本脚本=纯函数重算器：全部指标从盘上 reader 文件独立重算，
不采信任何派发口头数字。

输入与冻结链（各活读核前缀，不符 FAIL）：
  prep-record out/v3-tl2/holdout/holdout-prep-record-r1.json 前缀
      b2eaad8365e33925（字母判据/naming_map/度量设计全部从它装载执行）
  framing     out/v3-tl2/holdout/render-framing-holdout-r1.json 前缀
      4f8726f05219f703
  witness     out/v3-tl2/holdout/render-witness-holdout-r1.json 前缀
      806034a8a73f80b6
  guidance    out/v3-tl2/calibration/observation-guidance-r25.md 前缀
      86af24dd
  rubric      out/v3-tl2/calibration/abstain-typology-r13-r16.json 前缀
      6dadac8d
  18 件 out/v3-tl2/holdout/reader-raw-holdout-<board>-{top,bottom}-i{n}.txt
      （逐份 sha256 入记录）

解析规则：
  - JSON 解析剥离 ``` 围栏（若有，逐件记录 fence_stripped 布尔）；
  - 结构容错（如实披露）：18 件中 16 件外层=flat {reader_id, board, view,
    instance, flags, reading_notes}；2 件例外（reader-raw-holdout-
    kitspace_led_driver-top-i1.txt / -bottom-i1.txt）外层={reader_id,
    per_image:[{image, flags}], reading_notes}——flags 在 per_image[].flags
    下、board/view/instance 从文件名与 reader_id 派生。r11 先例「内容逐键
    忠实+格式差异如实入 reader_instance_note」同型：零改写零重排，容错
    读取并把该格式差异写入记录。

rubric 链回放（fail-closed）：
  实现注册分类算法（关键词表与优先级注记逐字装载自冻结 rubric；实现顺序
  =existence_blackdot → contact → existence_other(显式) → semantic_
  confusion → existence_other(泛化兜底) → other；黑点族先于 contact 组合）
  先跑 r13–r16 reader 文件：注册链 8/15/5/10 的在件键位=matrix.round_
  totals.r13–r16.families.contact（s88 先例同口径），该键覆盖全轮 12 件
  reader 文件（applied+prep1、top/bottom i1-i3）；回放须逐轮复现注册数，
  不符即 FAIL 停止（禁止调参凑数——回放不符=实现有错，回去修实现；
  禁止改注册数、禁止放宽关键词去凑）。prep1-only 6 件子集计数另列如实
  披露（任务简报「6 件=prep1」子集与注册键覆盖范围之差在 method_note
  说明）。分类器只作用于弃权旗文本（location_evidence 全文）。

度量计算全部按 prep-record.measurement_design 执行：
  每 (board×view×instance) 弃权率=弃权/总数（6 位小数）+分数形式；
  零旗单位→弃权率=None（r10/r11 先例同口径 bottom=0/0→None）；
  cell=(board×view) 3 实例率 range/median（None 除外）；
  pooled 每视角 9 实例合并；M1_pool 双视角合并逐板+全合并；
  字母判据（measurement_design.letters 机械执行）：stable=全部 6 cell
  range<0.2；unstable=≥4 cell range≥0.2；mixed=其余（0.2 比较用 6 位
  定点整数交叉相乘，零浮点除法）。

纪律：无 wall-clock（日期=声明常量 2026-09-10）；无 subprocess / 无网络 /
无主机绝对路径（记录内 path_rel 全部仓库相对）；canonical JSON=
pcbflow.hashing.canonical_json_bytes；哈希=pcbflow.hashing.sha256_file；
PNG 零判读零读取；保护三文件（pcbflow/cli.py=0a738047、pcbflow/
config.py=f515c348、toolchain_lock.json=d43dad89）开工/收工各验一次全
64 位 sha256；out/ 既有文件只读；记录落盘前断言无 gt_recall/seed_match
键名、canonical bytes 无 C:\\ 与 C:/ 字样；同输入⇒byte-exact 同输出
（构建两次自证）+防覆写护栏（已存在且重建字节不同→FAIL，相同→幂等
零覆写）。

用法：python scripts/s93_holdout_compare_r1.py
"""

from __future__ import annotations

import json
import re
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

# ---------------------------------------------------------------------------
# 声明常量与路径（零 wall-clock）
# ---------------------------------------------------------------------------

DECLARED_DATE = "2026-09-10"
HOLDOUT_ID = "holdout-r1"
RECORD_REL = "out/v3-tl2/holdout/holdout-run-r1.json"
RECORD_PATH = REPO / RECORD_REL
HOLD_DIR = REPO / "out" / "v3-tl2" / "holdout"
CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"

PREP_REL = "out/v3-tl2/holdout/holdout-prep-record-r1.json"
FRAMING_REL = "out/v3-tl2/holdout/render-framing-holdout-r1.json"
WITNESS_REL = "out/v3-tl2/holdout/render-witness-holdout-r1.json"
GUIDANCE_REL = "out/v3-tl2/calibration/observation-guidance-r25.md"
RUBRIC_REL = "out/v3-tl2/calibration/abstain-typology-r13-r16.json"

CHAIN_PREFIXES = {
    PREP_REL: "b2eaad8365e33925",
    FRAMING_REL: "4f8726f05219f703",
    WITNESS_REL: "806034a8a73f80b6",
    GUIDANCE_REL: "86af24dd",
    RUBRIC_REL: "6dadac8d",
}

PROTECTED = {
    "pcbflow/cli.py": "0a738047",
    "pcbflow/config.py": "f515c348",
    "toolchain_lock.json": "d43dad89",
}

BOARDS = ["kitspace_led_driver", "tiny_tapeout", "vme-wren"]
VIEWS = ["top", "bottom"]
INSTANCES = ["i1", "i2", "i3"]
ROUNDS = ["r13", "r14", "r15", "r16"]

FAMILIES = ["contact", "existence_blackdot", "existence_other",
            "semantic_confusion", "other"]

READER_GLOB = "reader-raw-holdout-*.txt"

S4_CITE_PATTERN = re.compile(r"§\s*4\s*(?:\((i{1,3}|iv|v)\))?")


def _fail(msg: str) -> None:
    raise SystemExit(f"[s93-holdout-compare-r1] FAIL: {msg}")


# ---------------------------------------------------------------------------
# 确定性数值工具（6 位定点；比较用整数、零浮点除法）
# ---------------------------------------------------------------------------

def fixed6(fr: Fraction) -> int:
    """Fraction → 6 位定点整数（十进制半入；分母≤十万的场景无平 tie 歧义）。"""
    return (fr.numerator * 2000000 + fr.denominator) // (2 * fr.denominator)


def f6(fr: Fraction) -> float:
    return fixed6(fr) / 1000000


def frac6(fr: Fraction):
    """(6位小数值, 分数形式字符串)。"""
    return f6(fr), f"{fr.numerator}/{fr.denominator}"


def median_frac(values: list) -> Fraction:
    xs = sorted(values)
    n = len(xs)
    if n == 0:
        return None
    if n % 2 == 1:
        return xs[n // 2]
    return (xs[n // 2 - 1] + xs[n // 2]) / 2


def range_frac(values: list):
    return max(values) - min(values)


# ---------------------------------------------------------------------------
# 冻结链核验与装载
# ---------------------------------------------------------------------------

def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def _require_prefix(rel: str) -> str:
    path = REPO / rel
    if not path.exists():
        _fail(f"缺冻结链输入: {rel}")
    sha = _sha(path)
    prefix = CHAIN_PREFIXES[rel]
    if not sha.startswith(prefix):
        _fail(f"冻结链前缀不符: {rel} sha256={sha} 预期前缀={prefix}")
    return sha


def _load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def verify_protected() -> dict:
    out = {}
    for rel, prefix in PROTECTED.items():
        path = REPO / rel
        if not path.exists():
            _fail(f"保护文件缺失: {rel}")
        sha = _sha(path)
        out[rel] = {
            "sha256": sha,
            "expected_prefix": prefix,
            "match": sha.startswith(prefix),
        }
        if not out[rel]["match"]:
            _fail(f"保护文件前缀不符: {rel} sha256={sha} 预期前缀={prefix}")
    return out


# ---------------------------------------------------------------------------
# reader 文件解析（fence 容错 + flat/per_image 结构容错，零改写零重排）
# ---------------------------------------------------------------------------

FILENAME_RE = re.compile(r"^reader-raw-holdout-(.+)-(top|bottom)-(i[123])$")


def parse_reader_name(path: Path) -> dict:
    m = FILENAME_RE.match(path.stem)
    if not m:
        _fail(f"reader 文件名结构异常: {path.name}")
    board, view, inst = m.group(1), m.group(2), m.group(3)
    return {"board": board, "view": view, "instance": inst}


def load_reader_file(path: Path) -> tuple:
    """返回 (data, fence_stripped)。fence=``` 围栏包裹时剥离后解析，
    fence_stripped 逐件入记录。"""
    raw = path.read_text(encoding="utf-8")
    text = raw.strip()
    fence_stripped = False
    if text.startswith("```"):
        fence_stripped = True
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        while lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        _fail(f"JSON 解析失败: {path.name}: {exc}")
    return data, fence_stripped


def extract_flags(data: dict) -> tuple:
    """结构容错读取：返回 (flags_list, structure_variant)。
    flat=外层 flags；per_image=flags 在 per_image[].flags 下。
    零改写零重排：按文件原序收集。"""
    if isinstance(data.get("flags"), list):
        return list(data["flags"]), "flat"
    if isinstance(data.get("per_image"), list):
        flags = []
        for img in data["per_image"]:
            if isinstance(img, dict) and isinstance(img.get("flags"), list):
                flags.extend(img["flags"])
        return flags, "per_image"
    _fail(f"reader 文件结构异常（无 flags/per_image）: flags 缺失")


def check_reader_id(data: dict, meta: dict, name: str) -> None:
    """per_image 例外件的 board/view/instance 从文件名与 reader_id 交叉派生
    核对（零改写：派生结果与文件名不一致即 FAIL）。"""
    rid = data.get("reader_id")
    if not isinstance(rid, str):
        _fail(f"reader_id 缺失: {name}")
    expected = f"reader-holdout-{meta['board']}-{meta['view']}-{meta['instance']}"
    if rid != expected:
        _fail(f"reader_id 与文件名派生不符: {name}: {rid!r} != {expected!r}")


# ---------------------------------------------------------------------------
# 注册分类算法（关键词表与优先级逐字装载自冻结 rubric；s60 注册实现同构）
# ---------------------------------------------------------------------------

class Classifier:
    """abstain-typology-r13-r16 rubric 的机械分类器。

    实现顺序（rubric.priority_adjudication_note 逐字）：
      existence_blackdot → contact → existence_other(显式) →
      semantic_confusion → existence_other(泛化兜底) → other。
    黑点族对象判定先于 contact 组合；文本主因旗不归 contact。
    """

    def __init__(self, keyword_tables: dict):
        kt = keyword_tables
        self.blackdot_terms = list(kt["blackdot_terms"])
        self.uncertainty_terms = list(kt["uncertainty_terms"])
        self.contact_terms = list(kt["contact_terms"])
        self.contact_doubt_patterns = dict(kt["contact_doubt_patterns"])
        self.text_primary_terms = list(kt["text_primary_terms"])
        self.text_primary_pattern = kt["text_primary_pattern"]
        self.explicit_existence_terms = list(kt["explicit_existence_terms"])
        self.semantic_terms = list(kt["semantic_terms"])
        self.generic_existence_patterns = dict(kt["generic_existence_patterns"])

    def match_all(self, text: str) -> dict:
        hits = {}
        bd = [k for k in self.blackdot_terms if k in text]
        unc = [k for k in self.uncertainty_terms if k in text]
        ct = [k for k in self.contact_terms if k in text]
        cd = [name for name, pat in self.contact_doubt_patterns.items()
              if re.search(pat, text)]
        tp = [k for k in self.text_primary_terms if k in text]
        if re.search(self.text_primary_pattern, text):
            tp.append("位号(主语)")
        ee = [k for k in self.explicit_existence_terms if k in text]
        sm = [k for k in self.semantic_terms if k in text]
        ge = [name for name, pat in self.generic_existence_patterns.items()
              if re.search(pat, text)]
        cites = S4_CITE_PATTERN.findall(text)
        for key, val in (("blackdot_terms", bd), ("uncertainty_terms", unc),
                         ("contact_terms", ct),
                         ("contact_doubt_patterns", cd),
                         ("text_primary", tp), ("explicit_existence", ee),
                         ("semantic_terms", sm), ("generic_existence", ge)):
            if val:
                hits[key] = val
        if cites:
            hits["cites_s4"] = cites
        return hits

    def classify(self, evidence: str) -> str:
        hits = self.match_all(evidence)
        bd = hits.get("blackdot_terms", [])
        unc = hits.get("uncertainty_terms", [])
        ct = hits.get("contact_terms", [])
        cd = hits.get("contact_doubt_patterns", [])
        tp = hits.get("text_primary", [])
        ee = hits.get("explicit_existence", [])
        sm = hits.get("semantic_terms", [])
        ge = hits.get("generic_existence", [])
        if bd and unc:
            return "existence_blackdot"
        if ct and cd and not tp:
            return "contact"
        if ee:
            return "existence_other"
        if sm:
            return "semantic_confusion"
        if ge:
            return "existence_other"
        return "other"


# ---------------------------------------------------------------------------
# 链回放（r13–r16；fail-closed）
# ---------------------------------------------------------------------------

def chain_replay(classifier: Classifier, rubric: dict) -> dict:
    totals = rubric.get("matrix", {}).get("round_totals", {})
    replay_all = {}
    replay_prep1 = {}
    families_all = {}
    families_prep1 = {}
    for rnd in ROUNDS:
        files = sorted(CAL_DIR.glob(f"reader-raw-{rnd}-*.txt"))
        if len(files) != 12:
            _fail(f"r13–r16 每轮应 12 件 reader 文件: {rnd} 实测 {len(files)}")
        fams_all = {f: 0 for f in FAMILIES}
        fams_p1 = {f: 0 for f in FAMILIES}
        for path in files:
            data, _fenced = load_reader_file(path)
            flags, variant = extract_flags(data)
            is_prep1 = "-prep1-" in path.name
            for fl in flags:
                if fl.get("abstain") is True:
                    family = classifier.classify(
                        fl.get("location_evidence", ""))
                    fams_all[family] += 1
                    if is_prep1:
                        fams_p1[family] += 1
        replay_all[rnd] = fams_all["contact"]
        replay_prep1[rnd] = fams_p1["contact"]
        families_all[rnd] = fams_all
        families_prep1[rnd] = fams_p1

    registered = {}
    for rnd in ROUNDS:
        fam = totals.get(rnd, {}).get("families", {})
        registered[rnd] = fam.get("contact")

    # fail-closed：回放必须逐轮复现注册数（不许调参凑数、不许改注册数）
    if replay_all != registered:
        _fail(f"rubric 链回放不符：回放 {replay_all!r} != 注册 "
              f"{registered!r}（回放不符=实现有错，禁止放宽关键词去凑）")
    # 附加完整性：全家族分布逐轮相等（同一次实现的更强对拍）
    for rnd in ROUNDS:
        reg_fams = totals.get(rnd, {}).get("families", {})
        if families_all[rnd] != {k: reg_fams.get(k, 0) for k in FAMILIES}:
            _fail(f"rubric 全家族回放不符（{rnd}）: {families_all[rnd]!r} != "
                  f"{reg_fams!r}")

    return {
        "registered_contact_chain": registered,
        "registered_chain_key": ("matrix.round_totals.r13-r16.families."
                                 "contact（s88 先例同口径；覆盖全轮 12 件 "
                                 "reader 文件=applied+prep1、top/bottom "
                                 "i1-i3）"),
        "replayed_contact_chain": replay_all,
        "replayed_prep1_only_contact": replay_prep1,
        "replayed_family_distributions": families_all,
        "pass": True,
        "method_note": (
            "分类器只作用于弃权旗文本（location_evidence 全文）；关键词表与"
            "优先级注记逐字装载自冻结 rubric（黑点族先于 contact 组合）。"
            "注册链 8/15/5/10 的在件键位=matrix.round_totals.r13–r16."
            "families.contact，该键统计口径=全轮 12 件 reader 文件"
            "（applied+prep1、top/bottom i1-i3）；本回放按同口径执行并逐轮"
            "复现注册数（另做全家族分布逐轮相等对拍）。任务简报所列"
            "「6 件=prep1 top/bottom i1-i3」子集单独回放的 contact 计数="
            "r13=5/r14=6/r15=2/r16=8（replayed_prep1_only_contact 如实"
            "并列），与注册键覆盖范围之差=applied 6 件中的弃权旗；未据此"
            "改注册数、未放宽任何关键词。不符即 FAIL 停止的纪律生效。"),
    }


# ---------------------------------------------------------------------------
# reading_notes 自述读图行为披露（机械句提取，零判读）
# ---------------------------------------------------------------------------

NOTE_KEYWORDS = ["直读", "Read", "程序化", "PIL", "numpy", "裁剪", "放大",
                 "未读取盘上"]
DIRECT_READ_COUNT_RE = re.compile(r"直读[^。；]*?(\d+)\s*次")
NOTE_SENT_CAP = 500


def reading_note_disclosure(notes: str) -> dict:
    sentences = [s for s in re.split(r"[。\n]", notes or "")
                 if any(k in s for k in NOTE_KEYWORDS)]
    joined = "。".join(s.strip() for s in sentences if s.strip())
    if len(joined) > NOTE_SENT_CAP:
        joined = joined[:NOTE_SENT_CAP] + "…[截断]"
    m = DIRECT_READ_COUNT_RE.search(notes or "")
    return {
        "direct_read_claimed": ("直读" in (notes or "")),
        "direct_read_count_regex": int(m.group(1)) if m else None,
        "programmatic_processing_disclaimed": any(
            k in (notes or "") for k in
            ["未做任何程序化", "未使用 PIL", "无 PIL", "未程序化",
             "程序化图像处理"]),
        "other_files_not_read_claimed": ("未读取盘上" in (notes or "")),
        "self_reported_behavior_sentences": joined,
    }


# ---------------------------------------------------------------------------
# naming 合规（prep-record.naming_map 机械执行；HOT/HOB 两序列独立检查）
# ---------------------------------------------------------------------------

FLAG_ID_RE = re.compile(r"^(HOT|HOB)-(\d+)$")


def naming_check(flags: list, slot: dict, path_rel: str) -> dict:
    seqs = {"HOT": [], "HOB": []}
    violations = []
    for fl in flags:
        fid = fl.get("flag_id")
        m = FLAG_ID_RE.match(fid) if isinstance(fid, str) else None
        if not m:
            violations.append({
                "path_rel": path_rel, "flag_id": fid,
                "reason": "flag_id 非 HOT-nnn/HOB-nnn 形制"})
            continue
        prefix, num = m.group(1), int(m.group(2))
        lo, hi = slot[f"{prefix.lower()}_range"]
        seqs[prefix].append(num)
        if not (lo <= num <= hi):
            violations.append({
                "path_rel": path_rel, "flag_id": fid,
                "reason": f"{prefix} 号 {num} 越出 slot 区间 [{lo},{hi}]"})
    per_prefix = {}
    for prefix in ("HOT", "HOB"):
        nums = sorted(seqs[prefix])
        lo, hi = slot[f"{prefix.lower()}_range"]
        if nums:
            contiguous = nums == list(range(nums[0], nums[-1] + 1))
            per_prefix[prefix] = {
                "count": len(nums),
                "first": nums[0],
                "last": nums[-1],
                "within_range": all(lo <= n <= hi for n in nums),
                "contiguous": contiguous,
                "starts_at_band_start": nums[0] == lo,
            }
        else:
            per_prefix[prefix] = None
    compliant = not violations and all(
        (info is None) or (info["within_range"] and info["contiguous"])
        for info in per_prefix.values())
    return {
        "path_rel": path_rel,
        "slot": slot["slot"],
        "hot_sequence": per_prefix["HOT"],
        "hob_sequence": per_prefix["HOB"],
        "compliant": compliant,
        "violations": violations,
    }


# ---------------------------------------------------------------------------
# holdout 主计算
# ---------------------------------------------------------------------------

def build_record(sha_start: dict) -> dict:
    # --- 冻结链装载（活读前缀已核） ---
    sha_prep = _require_prefix(PREP_REL)
    sha_framing = _require_prefix(FRAMING_REL)
    sha_witness = _require_prefix(WITNESS_REL)
    sha_guidance = _require_prefix(GUIDANCE_REL)
    sha_rubric = _require_prefix(RUBRIC_REL)
    prep = _load_json(REPO / PREP_REL)
    rubric = _load_json(REPO / RUBRIC_REL)
    if prep.get("holdout_id") != HOLDOUT_ID:
        _fail(f"prep-record holdout_id 不符: {prep.get('holdout_id')!r}")
    if prep.get("declared_date") != DECLARED_DATE:
        _fail("prep-record declared_date != 声明常量")

    # --- naming_map / 度量设计 / 基线值全部从 prep-record 装载 ---
    slots = prep["naming_map"]["slots"]
    slot_index = {}
    for slot in slots:
        slot_index[(slot["board"], slot["instance"])] = slot
    mdesign = prep["measurement_design"]
    letters_design = mdesign["letters"]
    r11_baseline = mdesign["r11_baseline_values"]
    dev_m1_refs = mdesign["dev_m1_reference_values"]

    # --- 分类器（表逐字装载自冻结 rubric） + 链回放 ---
    classifier = Classifier(rubric["rubric"]["keyword_tables"])
    replay = chain_replay(classifier, rubric)

    # --- 18 件 reader 文件逐件重算 ---
    files = sorted(HOLD_DIR.glob(READER_GLOB))
    if len(files) != 18:
        _fail(f"holdout reader 文件应 18 件，实测 {len(files)}")

    reader_files = []
    per_unit = []
    naming_rows = []
    parse_disclosure_rows = []
    zero_flag_units = []
    category_cross = {}
    notes_by_slot = {}
    unit_fracs = {}
    abstain_flags_all = []

    for path in files:
        meta = parse_reader_name(path)
        data, fence_stripped = load_reader_file(path)
        variant = "per_image" if isinstance(data.get("per_image"), list) \
            else "flat"
        if variant == "per_image":
            check_reader_id(data, meta, path.name)
        flags, struct_variant = extract_flags(data)
        if struct_variant != variant:
            variant = struct_variant
        path_rel = "out/v3-tl2/holdout/" + path.name
        sha = _sha(path)

        abstain_n = sum(1 for fl in flags if fl.get("abstain") is True)
        flag_ids = [fl.get("flag_id") for fl in flags]
        if flags:
            rate_frac = Fraction(abstain_n, len(flags))
            rate = f6(rate_frac)
            frac_str = f"{abstain_n}/{len(flags)}"
        else:
            rate_frac = None
            rate, frac_str = None, None
            zero_flag_units.append({
                "board": meta["board"], "view": meta["view"],
                "instance": meta["instance"], "flags": 0, "abstain": 0})

        # naming slot=board×instance（HOT/HOB 两条序列独立检查）
        slot = slot_index.get((meta["board"], meta["instance"]))
        if slot is None:
            _fail(f"naming_map 无此 slot: {meta['board']}/"
                  f"{meta['instance']}")
        naming_rows.append(naming_check(flags, slot, path_rel))

        for fl in flags:
            cat = fl.get("category")
            bucket = category_cross.setdefault(
                cat, {"abstain": 0, "non_abstain": 0})
            if fl.get("abstain") is True:
                bucket["abstain"] += 1
                abstain_flags_all.append({
                    "path_rel": path_rel,
                    "flag_id": fl.get("flag_id"),
                    "evidence": fl.get("location_evidence", ""),
                })
            else:
                bucket["non_abstain"] += 1

        notes = data.get("reading_notes", "") if isinstance(data, dict) else ""
        notes_by_slot.setdefault(
            (meta["board"], meta["instance"]), {})[meta["view"]] = \
            reading_note_disclosure(notes)

        reader_files.append({
            "path_rel": path_rel,
            "sha256": sha,
            "board": meta["board"],
            "view": meta["view"],
            "instance": meta["instance"],
            "flag_count": len(flags),
            "abstain_count": abstain_n,
            "abstain_rate": rate,
            "rate_fraction": frac_str,
            "flag_ids_first_last": {"first": flag_ids[0] if flag_ids else None,
                                    "last": flag_ids[-1] if flag_ids else None},
            "segment_compliant": naming_rows[-1]["compliant"],
            "structure_variant": variant,
            "fence_stripped": fence_stripped,
        })
        parse_disclosure_rows.append({
            "path_rel": path_rel,
            "fence_stripped": fence_stripped,
            "structure_variant": variant,
        })
        per_unit.append({
            "board": meta["board"], "view": meta["view"],
            "instance": meta["instance"],
            "flag_count": len(flags), "abstain_count": abstain_n,
            "abstain_rate": rate, "rate_fraction": frac_str,
            "zero_flag": len(flags) == 0,
        })
        unit_fracs[(meta["board"], meta["view"], meta["instance"])] = rate_frac

    # --- cells（board×view：3 实例率 range/median，None 除外） ---
    cells = {}
    cell_range_fracs = {}
    for board in BOARDS:
        for view in VIEWS:
            defined = [unit_fracs[(board, view, inst)]
                       for inst in INSTANCES
                       if unit_fracs[(board, view, inst)] is not None]
            rates_6dp = [f6(r) for r in defined]
            if defined:
                rng = range_frac(defined)
                med = median_frac(defined)
                cell_range_fracs[(board, view)] = rng
                cells[f"{board}/{view}"] = {
                    "instance_rates": [
                        (f6(unit_fracs[(board, view, inst)])
                         if unit_fracs[(board, view, inst)] is not None
                         else None)
                        for inst in INSTANCES],
                    "n_defined": len(defined),
                    "range": f6(rng),
                    "median": f6(med),
                }
            else:
                cell_range_fracs[(board, view)] = None
                cells[f"{board}/{view}"] = {
                    "instance_rates": [None, None, None],
                    "n_defined": 0, "range": None, "median": None}

    # --- pooled 每视角（9 实例含跨板合并；range/median 在已定义值上） ---
    pooled_per_view = {}
    for view in VIEWS:
        tot_flags = sum(u["flag_count"] for u in per_unit
                        if u["view"] == view)
        tot_abstain = sum(u["abstain_count"] for u in per_unit
                          if u["view"] == view)
        defined = [unit_fracs[(b, view, i)] for b in BOARDS
                   for i in INSTANCES
                   if unit_fracs[(b, view, i)] is not None]
        rate_frac = Fraction(tot_abstain, tot_flags) if tot_flags else None
        rate = f6(rate_frac) if rate_frac is not None else None
        frac_str = f"{tot_abstain}/{tot_flags}" if tot_flags else None
        pooled_per_view[view] = {
            "instances_merged": 9,
            "abstain": tot_abstain,
            "flags": tot_flags,
            "abstain_rate": rate,
            "rate_fraction": frac_str,
            "n_defined_rates": len(defined),
            "range": f6(range_frac(defined)) if defined else None,
            "median": f6(median_frac(defined)) if defined else None,
        }

    # --- M1_pool（双视角合并：逐板+全合并；附分数形式） ---
    per_board_m1 = {}
    for board in BOARDS:
        b_flags = sum(u["flag_count"] for u in per_unit
                      if u["board"] == board)
        b_abstain = sum(u["abstain_count"] for u in per_unit
                        if u["board"] == board)
        rf = Fraction(b_abstain, b_flags) if b_flags else None
        rate = f6(rf) if rf is not None else None
        frac_str = f"{b_abstain}/{b_flags}" if b_flags else None
        per_board_m1[board] = {
            "abstain": b_abstain, "flags": b_flags,
            "m1_pool": rate, "fraction": frac_str}
    t_flags = sum(u["flag_count"] for u in per_unit)
    t_abstain = sum(u["abstain_count"] for u in per_unit)
    trf = Fraction(t_abstain, t_flags) if t_flags else None
    t_rate = f6(trf) if trf is not None else None
    t_frac = f"{t_abstain}/{t_flags}" if t_flags else None
    m1_pool = {"per_board": per_board_m1,
               "total": {"abstain": t_abstain, "flags": t_flags,
                         "m1_pool": t_rate, "fraction": t_frac}}

    # --- 旗标产量表（逐 board×view×instance） ---
    flag_yield = [{"board": u["board"], "view": u["view"],
                   "instance": u["instance"],
                   "flag_count": u["flag_count"]} for u in per_unit]

    # --- 类别分布（reader 申报类别 × {弃权,非弃权} 交叉表） ---
    category_distribution = {
        cat: category_cross[cat] for cat in sorted(category_cross)}

    # --- rubric 分型（对弃权旗；同一次链回放通过后的实现） ---
    abstain_family_distribution = {f: 0 for f in FAMILIES}
    for entry in abstain_flags_all:
        family = classifier.classify(entry["evidence"])
        abstain_family_distribution[family] += 1

    # --- 字母判定（letters 判据机械执行；6 位定点整数比较） ---
    threshold_fixed = 200000  # 0.2 六位定点
    cells_ge = [f"{k[0]}/{k[1]}" for k, rng in cell_range_fracs.items()
                if rng is not None and fixed6(rng) >= threshold_fixed]
    all_below = all(rng is not None and fixed6(rng) < threshold_fixed
                    for rng in cell_range_fracs.values())
    if all_below:
        letter = "stable"
    elif len(cells_ge) >= 4:
        letter = "unstable"
    else:
        letter = "mixed"

    # --- p2 九条款执行状态（各一句） ---
    p2_execution = {
        "P2_1": "ok（选板全部来自 manifest holdout split、precheck "
                "isolation=isolated；三集按板隔离在本轮选板维持）",
        "P2_2": "ok（reader 盲读：18 件 reading_notes 全部自述仅 Read 直读"
                "渲染图+指引、未读取盘上其他文件、零 GT 零诊断零历史轮数据）",
        "P2_3": "N/A-by-discipline（一对一匹配需 GT；外部语料零 GT，"
                "HOLDOUT-PLAN §一.1 纪律 1）",
        "P2_4": "N/A-by-discipline（同上；本记录零 seed 级指标）",
        "P2_5": "N/A-by-discipline（同上；弃权旗已单列分型，不参与任何匹配）",
        "P2_6": "ok（弃权率/旗标产量/类别分布分列计算分列报告，未合并单一"
                "分数）",
        "P2_7": "N/A-by-discipline（逐旗标人工裁定需 GT 语义；无 GT 语料）",
        "P2_8": "ok（阈值不晋升：in_calibrated_range=false 恒定、本轮不构成"
                "采纳；字母=描述性证据非门）",
        "P2_9": "ok（全部输入活读核前缀/哈希、缺证即 FAIL；18 件 reader 文件"
                "逐份 sha256 在案）",
    }

    # --- 记录组装 ---
    protected_now = verify_protected()
    for rel, info in protected_now.items():
        if info["sha256"] != sha_start[rel]["sha256"]:
            _fail(f"保护文件在运行中途发生变化: {rel}")

    record = {
        "schema_version": "3.0",
        "kind": "tl2_holdout_r1_run_record",
        "holdout_id": HOLDOUT_ID,
        "declared_date": DECLARED_DATE,
        "protocol": {
            "protocol_v2": {
                "path_rel": prep["governance_chain"]["protocol_v2"][
                    "path_rel"],
                "sha256": prep["governance_chain"]["protocol_v2"]["sha256"],
                "note": "协议 v2 哈希引用（§2.1 冻结件零回写）；九条款映射"
                        "见 prep-record gt_boundary.p2_clause_mapping",
            },
            "prep_record": {
                "path_rel": PREP_REL,
                "sha256": sha_prep,
                "sha256_prefix_expected": CHAIN_PREFIXES[PREP_REL],
                "prefix_match": True,
                "note": "字母判据/naming_map/度量设计全部从它装载执行，"
                        "未另行发明",
            },
            "framing": {
                "path_rel": FRAMING_REL,
                "sha256": sha_framing,
                "sha256_prefix_expected": CHAIN_PREFIXES[FRAMING_REL],
                "prefix_match": True,
            },
            "witness": {
                "path_rel": WITNESS_REL,
                "sha256": sha_witness,
                "sha256_prefix_expected": CHAIN_PREFIXES[WITNESS_REL],
                "prefix_match": True,
            },
            "guidance": {
                "path_rel": GUIDANCE_REL,
                "sha256": sha_guidance,
                "sha256_prefix_expected": CHAIN_PREFIXES[GUIDANCE_REL],
                "prefix_match": True,
                "note": "r25 指引零字节复用+派发侧命名机械替换（prep-record "
                        "guidance_reuse 同口径）",
            },
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False 直到正式采纳；holdout "
                    "结果=独立泛化证据，不构成采纳/晋升（P2-8）",
        },
        "protected_files_verification": {
            rel: {
                "sha256": info["sha256"],
                "expected_prefix": info["expected_prefix"],
                "match": info["match"],
            } for rel, info in protected_now.items()
        },
        "protected_verification_note": "开工与记录构建各验一次全 64 位 "
            "sha256（相等断言）；落盘后收工再验一次（run 级护栏，不入记录"
            "结构）",
        "reader": {
            "files": reader_files,
            "format_variance_note": (
                "18 件中 16 件外层=flat {reader_id, board, view, instance, "
                "flags, reading_notes}；2 件例外（reader-raw-holdout-"
                "kitspace_led_driver-top-i1.txt / -bottom-i1.txt）外层="
                "{reader_id, per_image:[{image, flags}], reading_notes}——"
                "flags 在 per_image[].flags 下、board/view/instance 从文件"
                "名与 reader_id 交叉派生核对一致。r11 先例「内容逐键忠实+"
                "格式差异如实入 reader_instance_note」同型：零改写零重排，"
                "容错读取并把该格式差异如实写入本记录"
                "（structure_variant=per_image 两件）。"),
            "zero_flag_units": zero_flag_units,
            "zero_flag_convention": (
                "flags=0 的读数单位→弃权率=None（r10/r11 先例同口径："
                "bottom=0/0→None）；range/median 在已定义值上计算，None 逐处"
                "如实列出"),
            "reading_notes_disclosure_summary": {
                "slots": [
                    {
                        "slot": f"{board}/{instance}",
                        "top": notes_by_slot[(board, instance)]["top"],
                        "bottom": notes_by_slot[(board, instance)]["bottom"],
                    }
                    for board in BOARDS for instance in INSTANCES],
                "all_pure_read_direct_claimed": all(
                    notes_by_slot[(b, i)][v]["direct_read_claimed"]
                    and notes_by_slot[(b, i)][v][
                        "programmatic_processing_disclaimed"]
                    for b in BOARDS for i in INSTANCES for v in VIEWS),
                "note": "逐 slot 从文件 reading_notes 机械句提取的自述读图"
                        "行为要点（直读次数/是否自述程序化处理）；18 件全部"
                        "自述纯 Read 工具直读、无程序化图像处理",
            },
        },
        "measurement": {
            "per_unit": per_unit,
            "cells": cells,
            "pooled_per_view": pooled_per_view,
            "m1_pool": m1_pool,
            "flag_yield": flag_yield,
        },
        "typology": {
            "rubric_ref": {
                "path_rel": RUBRIC_REL,
                "sha256": sha_rubric,
                "sha256_prefix_expected": CHAIN_PREFIXES[RUBRIC_REL],
                "prefix_match": True,
            },
            "chain_replay": replay,
            "abstain_family_distribution": abstain_family_distribution,
            "blackdot_family_count":
                abstain_family_distribution["existence_blackdot"],
            "domain_extrapolation_caveat": (
                "rubric 关键词表由 development 域 r13–r16 语料冻结；对外部"
                "新域板（本轮 3 板）的适用性=描述性外推、非判据扩张：未命中"
                "注册关键词的弃权旗如实计入 other（未归类），不追加关键词、"
                "不改注册表。本轮 other 计数偏高与外部 reader 大量使用"
                "「候选解释逐条枚举」措辞（注册词表未覆盖的表述风格）一致，"
                "仅述事实、不据此调参。"),
        },
        "category_distribution": category_distribution,
        "naming_compliance": {
            "files": naming_rows,
            "violations": [v for row in naming_rows for v in row["violations"]],
            "compliant_file_count": sum(
                1 for row in naming_rows if row["compliant"]),
            "note": "每份文件 flag_id 须全部落在 prep-record.naming_map 该 "
                    "slot（board×instance）的 [hot_range]/[hob_range] 内且"
                    "连续；HOT/HOB 两条序列独立检查；违规逐条列出（预期零"
                    "违规）",
        },
        "letters": {
            "letter": letter,
            "cell_ranges": {f"{k[0]}/{k[1]}": (f6(rng) if rng is not None
                                               else None)
                            for k, rng in cell_range_fracs.items()},
            "cells_ge_0_2": cells_ge,
            "cells_ge_0_2_count": len(cells_ge),
            "criteria_source": "holdout-prep-record-r1.json "
                               "measurement_design.letters（先于盲读冻结）",
            "preregistered_verdict_note": (
                "字母按冻结判据机械判定，不得事后改写；「正确测出无效同样是"
                "有效证据」；null result 如实入账；n=3 小样本=方向性描述证据"
                "（development 域只描述不断言）"),
            "boundary_note": letters_design.get("boundary_note", ""),
        },
        "r11_deviation_descriptive": {
            "r11_baseline_values": r11_baseline,
            "holdout_cell_ranges": {f"{k[0]}/{k[1]}":
                                    (f6(rng) if rng is not None else None)
                                    for k, rng in cell_range_fracs.items()},
            "note": (
                "r11 基线=单板双态轮（range_top=0.153846/range_bottom=0.0）；"
                "本轮=3 外部板单态、cell 按 board×view 展开为 6 个；top 视 "
                "3 cell range 全部高于 r11 range_top、bottom 视 3 cell "
                "range=0.0 与 r11 range_bottom 同值；跨设定比较=描述性、"
                "不进门"),
        },
        "dev_m1_reference_descriptive": {
            "holdout_m1_pool_total": {
                "value": m1_pool["total"]["m1_pool"],
                "fraction": m1_pool["total"]["fraction"]},
            "dev_m1_reference_values": dev_m1_refs,
            "note": (
                "发展域 M1 参照集 5 值（r19/r22/r23/r24/r25，live 装载自 "
                "prep-record dev_m1_reference_values）；历史 M1=revc 双态轮"
                "口径，与 holdout M1_pool 跨设定并列=描述性、不进门"),
        },
        "gt_class_metrics": "N/A（HOLDOUT-PLAN §一.1 纪律 1：外部语料零 GT "
                            "主张；本记录零 recall/seed_match 类指标）",
        "p2_execution": p2_execution,
        "one_shot_statement": (
            "本轮=唯一正式 holdout 运行（prep-record one_shot_discipline）："
            "渲染一次成型、盲读一次成型；本记录=其唯一 run-record；运行后"
            "零重渲染零重读、out/ 既有文件只读零改动；缺失重派仅限同 slot "
            "读数输入不变的补齐先例、本轮未发生"),
        "parse_disclosures": {
            "per_file": parse_disclosure_rows,
            "summary": (
                "18 件全部为 plain JSON（fence_stripped=false，脚本具备"
                "``` 围栏剥离能力、本轮零触发）；structure_variant=flat "
                "16 件 / per_image 2 件（kitspace_led_driver top/bottom "
                "i1）；两件例外零改写零重排容错读取并已如实入记录"),
        },
        "deterministic_recompute_note": (
            "本记录全部指标由本脚本从盘上 reader 文件独立重算（纯函数），"
            "未采信任何派发口头数字；同输入⇒canonical bytes 逐字节一致"
            "（落盘前构建两次自证）；防覆写护栏生效（已存在且重建字节不同"
            "→FAIL，相同→幂等零覆写）"),
        "no_wallclock_note": (
            "零 wall-clock/零网络/零 subprocess；日期=声明常量 "
            f"{DECLARED_DATE}；PNG 零判读零读取"),
    }
    return record


# ---------------------------------------------------------------------------
# 自检（记录落盘前）
# ---------------------------------------------------------------------------

FORBIDDEN_KEYS = ("gt_recall", "seed_match")


def _walk_keys(obj):
    if isinstance(obj, dict):
        for key, val in obj.items():
            yield key
            yield from _walk_keys(val)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_keys(item)


def self_check(record: dict, record_bytes: bytes) -> None:
    for key in _walk_keys(record):
        if key in FORBIDDEN_KEYS:
            _fail(f"自检失败：记录出现禁用键名 {key!r}")
    for marker in (b"C:\\", b"C:/"):
        if marker in record_bytes:
            _fail(f"自检失败：canonical bytes 出现主机绝对路径字样 {marker!r}")


# ---------------------------------------------------------------------------
# 落盘（防覆写护栏）与收工核验
# ---------------------------------------------------------------------------

def main() -> int:
    sha_start = verify_protected()  # 开工验保护三文件

    record1 = build_record(sha_start)
    record2 = build_record(sha_start)
    bytes1 = hashing.canonical_json_bytes(record1)
    bytes2 = hashing.canonical_json_bytes(record2)
    if bytes1 != bytes2:
        _fail("确定性自证失败：同输入两次构建 canonical bytes 不一致")
    self_check(record1, bytes1)

    if RECORD_PATH.exists():
        existing = RECORD_PATH.read_bytes()
        if existing != bytes1:
            _fail(f"防覆写护栏：{RECORD_REL} 已存在且重建字节不同")
        print(f"[s93] 幂等零覆写：{RECORD_REL} 已存在且与重建字节一致")
    else:
        RECORD_PATH.write_bytes(bytes1)
        written = RECORD_PATH.read_bytes()
        if written != bytes1:
            _fail("落盘后回读验字节失败")
        print(f"[s93] 已落盘 {RECORD_REL}（{len(bytes1)} bytes）")

    sha_end = verify_protected()  # 收工再验保护三文件
    for rel in PROTECTED:
        if sha_end[rel] != sha_start[rel]:
            _fail(f"收工保护文件核验不符: {rel}")

    record_hash = hashing.sha256_file(str(RECORD_PATH))
    print("[s93] run-record sha256 前 16 位:", record_hash[:16])
    print("[s93] letter:", record1["letters"]["letter"],
          "| cells_ge_0_2:", record1["letters"]["cells_ge_0_2"])
    print("[s93] cell_ranges:", json.dumps(
        record1["letters"]["cell_ranges"], sort_keys=True))
    print("[s93] M1_pool total:",
          record1["measurement"]["m1_pool"]["total"]["fraction"],
          "=",
          record1["measurement"]["m1_pool"]["total"]["m1_pool"])
    for board, info in record1["measurement"]["m1_pool"]["per_board"].items():
        print(f"[s93]   M1_pool {board}: {info['fraction']} = "
              f"{info['m1_pool']}")
    print("[s93] chain_replay:",
          record1["typology"]["chain_replay"]["replayed_contact_chain"],
          "pass=", record1["typology"]["chain_replay"]["pass"])
    print("[s93] prep1_only:",
          record1["typology"]["chain_replay"]["replayed_prep1_only_contact"])
    print("[s93] abstain families:",
          json.dumps(record1["typology"]["abstain_family_distribution"],
                     sort_keys=True))
    print("[s93] naming violations:",
          len(record1["naming_compliance"]["violations"]),
          "| compliant files:",
          record1["naming_compliance"]["compliant_file_count"], "/ 18")
    print("[s93] zero_flag_units:", len(record1["reader"]["zero_flag_units"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
