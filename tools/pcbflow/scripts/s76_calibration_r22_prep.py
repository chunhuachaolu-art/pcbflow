#!/usr/bin/env python
"""CAL-R22-PREP：R22 同指引重复轮（收敛归因；r16 先例）预备包（只新建两
个文件：scripts/s76_calibration_r22_prep.py 本体与
out/v3-tl2/calibration/r22-prep-record.json；datasets/ 与 out/ 既有文件
只读、零改动；observation-guidance-r19.md 零字节不动——本轮**不新建指
引文件**，无指引新文件）。

R22 轮性质（预注册，非事后）：**同指引重复轮（收敛归因；r16 先例：
r15→r16 同指引重复、渲染零变更、仅实例重抽）**——唯一实验操作=reader
实例群重抽（每视角 3 新实例 i1/i2/i3×4 视角格=12 派次，与 r19/r20 实例
群无身份延续；两波次串行保序：同一实例先 applied 后 prep1、flag_id 编
号跨板连续）。判读指引=observation-guidance-r19.md 字节复用（8633bda5
实测锚；§6 示例前缀仍书 R19T-/R19B-=字节复用后果，R22 派次前缀
R22T/R22B 由派发指令层覆盖——r16 先例在案：r15 指引+R16T 前缀执行先
例）；渲染零变更=renders-r14b 四图字节复用；GT/阈值/协议零变更（13 条
冻结、v1.1+v1.2 维持）。

轮次号=**r22（跳号声明在案）**：r21 号段=axis-experiment-plan-r17-r20
（b6ec6467 冻结件）combination_decision_rule.ii_full_combination 预留
的 R21 全组合位（条件轮，未触发）；round20-dev-record
next_iteration_targets[0] 已登记「R21 不做」（三重独立依据在案）；r22
为时序下一轮、与该 R21 无涉——跳号声明写入 prep record 以免台账歧义。

合法性依据与设计出处（三重链，实测锚 fail-closed）：
  1. round20-dev-record next_iteration_targets[0]（80e3e9e2 锚）——
     阶段2 收束=收益最大配置=轴3 单变量（guidance-r19，M1=0.461538 历
     史最佳、contact 族 10→4、黑点族 13→4）+R21 不做（三重独立依据）。
  2. round20-dev-record next_iteration_targets[1]——下一候选建议=同指
     引重复轮（r16 先例）收敛归因（区分真实收益与实例群漂移 0.09064
     参照；preregistration_required=true：prep-record 预注册先于盲读
     冻结）。
  3. 用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的继
     续」（axis-plan user_quote 在案原文）——阶段2 收束后其操作性子句
     「选择收益最大的继续」=授权对收益最大配置（r19 配置）继续迭代。

归因假设：r19 的 M1=0.461538（r16 基线 0.771429 下降 0.309891）、
contact 族 10→4、M4=0.211111（差 0.011111 未过 supported 门 0.20、字
母=marginal 在案）是否在新鲜实例群复现——真实收益 vs 实例群漂移的归
因判别（量级参照=r15→r16 同指引纯重抽 M1 漂移 |0.862069−0.771429|=
0.09064 vs r19 降幅 0.309891，两数并列在案）。预注册三支裁决：
replicated（M1 落 [0.361538, 0.561538]=r19±0.10 且 contact 族 ≤7 且
G1/G2 维持）/ drifted（未达 replicated 且 M1 < 0.771429 且 G1/G2 维
持）/ regressed（M1 ≥ 0.771429 或 G1/G2 任一破坏）；M4 第二轮样本单
列机制观察（不进字母裁决：M4 双样本分布如实并列）。机制观察预注册：
contact/黑点/存在性三族计数对照 r19（4/4/14）与 r20（2/6/10）；(iii-a)
援引计数对照 r19 基线（旗级 6 旗+分支字面 2 旗；notes 级 10/12 派
次）、§5B 援引计数照记（本轮指引无 §5B 节=基座结构在案）。

判据冻结值锚定（calibration-run-r19.json hypothesis_test，e5755a11 锚
fail-closed）：M1=18/39=0.461538、M2=4/7=0.571429、M3=黑点 4、
M4=0.211111、contact 族 rubric=4、守门 G1/G2 维持、verdict=marginal；
run-r16（2c1f8265 锚）M1 基线 0.771429+guard_ok=True。

hypothesis_test=预注册收敛归因判据**逐字**（HYPOTHESIS_TEST_TEXT 原文
常量嵌入；断言链=文本→json.loads→HYPOTHESIS_TEST→record 字段，三层
相等，不得改数值或口径）；描述性边界注记照抄 r19-prep-record 血统原
文（与 APR-0011 门分列互不凌驾、门阈值零改动）。

纪律：无 wall-clock（日期/轮次=声明常量 2026-09-09 / 2026-09-09-r22）；
无 subprocess / 无网络 / 无主机绝对路径；hash=sha256_file 字节口径
（PNG 仅哈希+magic，零内容判读、零像素读取）；不读 GT / ground-truth-* /
reader-raw-* / derivation-log-* / 任何 compare/诊断内容产物；run-r19
仅读 hypothesis_test.measurement 顶层判据冻结值字段+guard_channel+
mechanism_observation 三族 rubric 聚合计数与 (iii-a) 援引聚合计数做锚
（GT 匹配/逐旗明细/摘录内容不读取、不入记录）；run-r16 仅读
hypothesis_test.measurement 顶层判据值字段；无 git；r19 指引只读零写
入；记录内零 GT、零期望数量/分布/坐标；指引内零轮次结果数字（基线数
字仅入本编排侧记录）；r22-prep-record.json 落盘=canonical JSON
（hashing.canonical_json_bytes）+同参重建两次逐字节一致自证+防覆写守
卫（已存在且重建字节不同→FAIL，相同→幂等零覆写）+落盘后回读验字节。

用法：python scripts/s76_calibration_r22_prep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

CAL_DIR = REPO / "out" / "v3-tl2" / "calibration"
GUIDANCE_R19 = CAL_DIR / "observation-guidance-r19.md"
R19_PREP_RECORD = CAL_DIR / "r19-prep-record.json"
R16_PREP_RECORD = CAL_DIR / "r16-prep-record.json"
DEV_RECORD_R20 = CAL_DIR / "round20-dev-record.json"
AXIS_PLAN = CAL_DIR / "axis-experiment-plan-r17-r20.json"
RUN_R19 = CAL_DIR / "calibration-run-r19.json"
RUN_R16 = CAL_DIR / "calibration-run-r16.json"
WITNESS_R14B = CAL_DIR / "render-witness-r14b.json"
EVAL_PROTOCOL_V1 = CAL_DIR / "evaluation-protocol-v1.md"
RECORD = CAL_DIR / "r22-prep-record.json"
RENDR14B_DIR = CAL_DIR / "renders-r14b"

DATE_CONSTANT = "2026-09-09"
ROUND_ID = "2026-09-09-r22"

# ---------------------------------------------------------------------------
# 冻结锚（开工实测给定；不符即停）
# ---------------------------------------------------------------------------
GUIDANCE_R19_SHA_PREFIX = "8633bda5"
R19_PREP_RECORD_SHA_PREFIX = "e4cf2d3c"
R16_PREP_RECORD_SHA_PREFIX = "46fbd15b"
DEV_RECORD_R20_SHA_PREFIX = "80e3e9e2"
AXIS_PLAN_SHA_PREFIX = "b6ec6467"
RUN_R19_SHA_PREFIX = "e5755a11"
RUN_R16_SHA_PREFIX = "2c1f8265"
WITNESS_R14B_SHA_PREFIX = "b63771f9"
EVAL_PROTOCOL_V1_SHA_PREFIX = "22dc7337"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

RENDR14B_SIDES = ("applied-top", "applied-bottom", "prep1-top", "prep1-bottom")
R14B_BOTTOM_SHA_PREFIX = "d7284259"

#: 指引字节复用事实锚（observation-guidance-r19.md 落盘事实；不符即停。
#: 前缀差异登记的依据=§6 示例前缀仍书 R19T-/R19B-；本轮指引无 §5B 节）
GUIDANCE_R19_FACTS = {
    "R19T-": 4,
    "R19B-": 1,
    "reader-r19": 1,
    "## 5B": 0,
    "(iii-a)": 3,
    "- round_id_constant: `2026-09-09-r19`": 1,
}

# ---------------------------------------------------------------------------
# 判据冻结值常量（=在案实测装载目标；probe 逐一断言，不符即停——防预注
# 册文本与在案事实漂移）
# ---------------------------------------------------------------------------
M1_R19 = 0.461538                    # run-r19 top_abstain_rate_r19（18/39）
M1_R19_ARITHMETIC = "18/39"
M2_R19 = 0.571429                    # run-r19 bottom_abstain_rate_r19（4/7）
M3_R19 = 4                           # 黑点族 rubric（existence_blackdot）
M4_R19 = 0.211111                    # run-r19 m4_top_rate_range_r19
CONTACT_R19 = 4                      # run-r19 contact 族 rubric（全视）
BLACKDOT_R19 = 4
EXIST_OTHER_R19 = 14
M1_R16_BASELINE = 0.771429           # run-r16 top_abstain_rate_r16（27/35）
R15_TOP_RATE = 0.862069              # r15 在案值（漂移参照上游；r15→r16）
DRIFT_R15_R16 = 0.09064              # |0.862069−0.771429|（r15→r16 纯重抽）
R19_DROP = 0.309891                  # 0.771429−0.461538
REPLICATED_BAND = 0.10               # r19±0.10
REPLICATED_LO = 0.361538
REPLICATED_HI = 0.561538
CONTACT_REPLICATED_THRESHOLD = 7     # contact 族 ≤7（r19 marginal 通道阈值
# 口径延续；r19 实测 4 在阈值内）
M4_R19_SUPPORTED_GATE = 0.20
M4_R19_GATE_GAP = 0.011111           # 0.211111−0.20（supported 门差，在案）

#: round20-dev-record next_iteration_targets 授权定位标记
MARK_R21_SKIP = "R21 不做"
MARK_TRIPLE_BASIS = "三重独立依据"
MARK_BEST_CONFIG = "收益最大配置=轴3 单变量"
MARK_REPEAT_CANDIDATE = "同指引重复轮"
MARK_DRIFT_REF = "0.09064"
MARK_CONVERGENCE = "收敛归因"
MARK_M4_GAP = "M4=0.211111 差 0.011111 未过 supported 门 0.20"

# ---------------------------------------------------------------------------
# 预注册收敛归因判据（逐字，先于任何盲读冻结；不得改数值或口径）
# ---------------------------------------------------------------------------
HYPOTHESIS_TEST_TEXT = """{
  "hypothesis_id": "r20-dev-record-candidate-r19-config-same-guidance-repeat",
  "hypothesis": "r19 配置（guidance-r19=§4(iii-a) 可操作分辨条款；渲染 r14b 字节复用）的单轮收益——M1=0.461538（r16 基线 0.771429 下降 0.309891）、contact 族 10→4、M4=0.211111（差 0.011111 未过 supported 门 0.20、字母=marginal 在案）——存在两候选解释：(α) 真实收益（判据侧条款的方向性收益在新鲜实例群可复制）；(β) 实例群漂移（量级参照=r15→r16 同指引纯重抽 M1 漂移 |0.862069−0.771429|=0.09064 与 r19 降幅 0.309891 并列在案，单轮不可凭落点排除其一）。R22=同指引重复轮（r16 先例：r15→r16 同指引重复、渲染零变更、仅实例重抽；唯一实验操作=reader 实例群重抽 12 派次），以 M1 落点+contact 族+守门维持做收敛归因裁决。",
  "adjudication": {
    "replicated": "M1（top 全旗聚合弃权率，12 派次全口径）落 [0.361538, 0.561538]（r19±0.10）且 contact 族弃权旗数（全视，分型件 rubric 口径）≤ 7 且 G1（bottom courtyard 非弃权 0/0/0）与 G2（guard_ok）维持 → r19 量级获复制支持（收益方向与幅度在新鲜实例群成立）",
    "drifted": "未达 replicated 且 M1 < 0.771429（r16 基线）且 G1/G2 维持 → r19 量级部分归因实例群（收益方向存但幅度不确定）",
    "regressed": "M1 ≥ 0.771429 或 G1/G2 任一破坏 → r19 量级不可复制、轴3 收益判定降级为单轮现象",
    "m4_second_sample_separate": "M4（top 逐实例弃权率极差）第二轮样本单列机制观察、不进字母裁决：r22 实测 M4 与 r19 的 0.211111 双样本分布如实并列（r19 的 supported 门 0.20 差 0.011111 在案、字母=marginal）——不因双样本而改门、不挑优、不合并分布",
    "mechanism_observation_separate": "contact/黑点/存在性三族计数（分型件 rubric 口径）对照 r19（4/4/14）与 r20（2/6/10）；(iii-a) 援引计数对照 r19 基线（旗级 6 旗+分支字面 2 旗；notes 级 10/12 派次）、§5B 援引计数照记（本轮指引字节复用无 §5B 节=基座结构在案，任何援引为零上下文、如实登记）；M1/M2/M3/M4 四元组入实验对照账（axis ledger 延续登记、rubric 口径）；gt 照常",
    "metric_lesson_separate": "跨轮实例群漂移混杂照旧——本轮恰以实例群重抽为唯一实验操作与裁决变量；字母=预注册阈值命中与否的描述性结论；部分重复≠独立重复（同域同编排实例池、验证力度如实声明）；replicated/drifted/regressed 三支的 M1 带宽（r19±0.10 与 r16 基线截断）为描述性边界、不得事后收放",
    "descriptive_boundary_note": "本轮判据均为描述性边界，与 APR-0011 门与 CONTAINMENT_MIN/AREA_RATIO_MAX 分列互不凌驾（门阈值零改动）；比较与组合决策以冻结件 axis-experiment-plan-r17-r20.json 为准"
  }
}"""

HYPOTHESIS_TEST = json.loads(HYPOTHESIS_TEST_TEXT)

#: 预注册判据文本数值 needle（逐字在位断言；不符即停）
REQUIRED_NEEDLES = (
    "[0.361538, 0.561538]",
    "r19±0.10",
    "≤ 7",
    "0.771429",
    "0.461538",
    "0.309891",
    "0.09064",
    "0.211111",
    "0.011111",
    "G1（bottom courtyard 非弃权 0/0/0）",
    "G2（guard_ok）",
    "双样本分布如实并列",
    "不进字母裁决",
    "4/4/14",
    "2/6/10",
    "旗级 6 旗+分支字面 2 旗",
    "notes 级 10/12 派次",
    "仅实例重抽",
    "r16 先例",
    "axis-experiment-plan-r17-r20.json 为准",
)


# ---------------------------------------------------------------------------
# 工具（fail-closed）
# ---------------------------------------------------------------------------

def _fail(msg: str) -> None:
    print(f"[r22-prep] FAIL: {msg}")
    sys.exit(1)


def _sha(path: Path) -> str:
    return hashing.sha256_file(str(path))


def check_guidance_zero_write() -> dict:
    """指引基座复核：只读哈希+字节数+落盘事实锚，零写入（本函数无写路
    径；字节复用=零编辑、零机械变换、不新建指引文件）。"""
    if not GUIDANCE_R19.exists():
        _fail(f"缺失：{GUIDANCE_R19}")
    sha = _sha(GUIDANCE_R19)
    if not sha.startswith(GUIDANCE_R19_SHA_PREFIX):
        _fail(f"observation-guidance-r19.md sha 前 8={sha[:8]} != 预期 "
              f"{GUIDANCE_R19_SHA_PREFIX}（判读指引基座疑被改动，立即停止）")
    text = GUIDANCE_R19.read_text(encoding="utf-8")
    if hashing.sha256_text(text) != sha:
        _fail("r19 指引文本口径与字节口径不一致（换行或编码漂移，立即停止）")
    facts: dict[str, int] = {}
    for needle, want in GUIDANCE_R19_FACTS.items():
        n = text.count(needle)
        if n != want:
            _fail(f"指引落盘事实锚不符：{needle!r} 命中 {n} 次 != 预期 "
                  f"{want} 次（立即停止）")
        facts[needle] = n
    return {
        "path_rel": "out/v3-tl2/calibration/observation-guidance-r19.md",
        "sha256_measured": sha,
        "byte_size": GUIDANCE_R19.stat().st_size,
        "facts": facts,
        "zero_write": True,
    }


def check_renders_byte_reuse(witness: dict) -> list[dict]:
    """渲染零变更实测：四 PNG magic+sha256_file 实测 vs witness 登记值
    （bottom=renders.{applied,prep1}.sha256 两板同；
    top=top_zero_change_copies.{applied-top,prep1-top}.sha256）。"""
    rendered = witness.get("renders", {})
    copies = witness.get("top_zero_change_copies", {})
    registered = {
        "applied-bottom": (rendered.get("applied", {}) or {}).get("sha256"),
        "prep1-bottom": (rendered.get("prep1", {}) or {}).get("sha256"),
        "applied-top": (copies.get("applied-top", {}) or {}).get("sha256"),
        "prep1-top": (copies.get("prep1-top", {}) or {}).get("sha256"),
    }
    for side, sha in registered.items():
        if not isinstance(sha, str) or len(sha) != 64:
            _fail(f"witness {side} 见证登记值缺失或非 64 位 sha256：{sha!r}")
    results = []
    for side in RENDR14B_SIDES:
        path = RENDR14B_DIR / f"{side}.png"
        if not path.exists():
            _fail(f"PNG 缺失：{path}")
        with path.open("rb") as f:
            if f.read(8) != PNG_MAGIC:
                _fail(f"{path.name}: 不是 PNG（magic 不符）")
        measured = _sha(path)
        expect = registered[side]
        if measured != expect:
            _fail(f"renders-r14b/{side}.png 实测 sha256 与 witness 登记值不"
                  f"符（渲染零变更声明被破坏）：measured={measured} "
                  f"registered={expect}")
        if side.endswith("-bottom") and not measured.startswith(
                R14B_BOTTOM_SHA_PREFIX):
            _fail(f"renders-r14b/{side}.png sha 前 8={measured[:8]} != 预期 "
                  f"{R14B_BOTTOM_SHA_PREFIX}")
        results.append({
            "state_side": side,
            "path_rel": f"out/v3-tl2/calibration/renders-r14b/{side}.png",
            "sha256_measured": measured,
            "sha256_witness_registered": expect,
            "witness_key": ("renders." + side.replace("-bottom", "") + ".sha256"
                            if side.endswith("-bottom")
                            else "top_zero_change_copies." + side + ".sha256"),
            "witness_record": "out/v3-tl2/calibration/render-witness-r14b.json",
            "match": True,
        })
    if registered["applied-bottom"] != registered["prep1-bottom"]:
        _fail("witness 登记的两张 bottom sha 不相同（字节复用口径不符）")
    return results


def probe_witness(witness: dict) -> None:
    """render-witness-r14b 结构最小校验（kind/轮次/日期锚）。"""
    if witness.get("kind") != "tl2_calibration_render_witness_r14b":
        _fail("render-witness-r14b kind 不符")
    if witness.get("round_id_constant") != "2026-09-08-r14b":
        _fail(f"render-witness-r14b round_id_constant 不符："
              f"{witness.get('round_id_constant')}")


def extract_authorization(dev20: dict, dev20_sha: str) -> dict:
    """round20-dev-record next_iteration_targets：targets[0]=阶段2 收束+
    R21 不做（跳号声明依据）；targets[1]=同指引重复轮候选（设计出处）。
    按标记唯一定位并要求索引=[0]/[1]。"""
    if dev20.get("kind") != "tl2_calibration_round20_dev_record":
        _fail("round20-dev-record kind 不符")
    if dev20.get("round_id") != "2026-09-09-r20":
        _fail(f"round20-dev-record round_id 不符：{dev20.get('round_id')}")
    if dev20.get("schema_version") != "3.0":
        _fail("round20-dev-record schema_version != 3.0（结构漂移）")
    if dev20.get("declared_date") != DATE_CONSTANT:
        _fail("round20-dev-record declared_date != 2026-09-09")
    targets = dev20.get("next_iteration_targets")
    if not isinstance(targets, list) or len(targets) < 2:
        _fail("round20-dev-record next_iteration_targets 结构不符")
    for mark, idx, label in (
            (MARK_R21_SKIP, 0, "R21 不做登记"),
            (MARK_TRIPLE_BASIS, 0, "三重独立依据"),
            (MARK_BEST_CONFIG, 0, "收益最大配置=轴3"),
            (MARK_REPEAT_CANDIDATE, 1, "同指引重复轮候选"),
            (MARK_DRIFT_REF, 1, "漂移参照 0.09064"),
            (MARK_CONVERGENCE, 1, "收敛归因"),
            (MARK_M4_GAP, 1, "M4 supported 门差")):
        if mark not in targets[idx]:
            _fail(f"next_iteration_targets[{idx}] 缺标记「{mark}」"
                  f"（{label} 定位失败）")
    if len([t for t in targets if isinstance(t, str)
            and MARK_REPEAT_CANDIDATE in t]) != 1:
        _fail("「同指引重复轮」标记在 targets 内非唯一命中（定位歧义）")
    return {
        "path_rel": "out/v3-tl2/calibration/round20-dev-record.json",
        "sha256_measured": dev20_sha,
        "field": "next_iteration_targets",
        "item_indices_zero_based": [0, 1],
        "stage2_closure_and_r21_skip_quote": targets[0],
        "repeat_candidate_quote": targets[1],
    }


def probe_axis_plan_r21_slot(plan: dict, plan_sha: str) -> dict:
    """axis-experiment-plan-r17-r20：R21 全组合槽位冻结原文（跳号声明的
    槽位依据）+守门+用户指令原文锚。"""
    if plan.get("kind") != "tl2_axis_experiment_plan_development":
        _fail("axis-plan kind 不符")
    if plan.get("declared_date") != DATE_CONSTANT:
        _fail("axis-plan declared_date != 2026-09-09")
    cdr = plan.get("combination_decision_rule", {})
    ii = cdr.get("ii_full_combination", "")
    if "R21" not in ii or "三轴全组合" not in ii:
        _fail(f"axis-plan ii_full_combination 缺 R21 全组合位原文：{ii!r}")
    esr = plan.get("early_stop_rule", {})
    shortcut = esr.get("strong_single_axis_shortcut", "")
    if "R21 不做" not in shortcut:
        _fail(f"axis-plan strong_single_axis_shortcut 缺「R21 不做」原文："
              f"{shortcut!r}")
    s2 = (plan.get("experiment_design", {}) or {}).get("stage2", "")
    if "R21" not in s2:
        _fail(f"axis-plan experiment_design.stage2 缺 R21 槽位原文：{s2!r}")
    for gid in ("G1_bottom_courtyard_nonabstain_zero", "G2_guard_ok",
                "G3_freeze_discipline"):
        if gid not in (plan.get("guards", {}) or {}):
            _fail(f"axis-plan 守门缺失：{gid}")
    quote = (plan.get("user_directive_note", {}) or {}).get("user_quote")
    if quote != "三条轴单独/组合/全组合尝试，选择收益最大的继续":
        _fail(f"axis-plan 用户指令原文不符：{quote!r}")
    return {
        "path_rel": "out/v3-tl2/calibration/axis-experiment-plan-r17-r20.json",
        "sha256_measured": plan_sha,
        "r21_slot_frozen_quotes": {
            "combination_decision_rule.ii_full_combination": ii,
            "early_stop_rule.strong_single_axis_shortcut": shortcut,
            "experiment_design.stage2": s2,
        },
        "user_quote": quote,
    }


def anchor_run19_metrics(run19: dict, run19_sha: str) -> dict:
    """calibration-run-r19 判据冻结值锚定（fail-closed；只读顶层判据值
    字段+guard_channel+三族 rubric 聚合计数+(iii-a) 援引聚合计数；GT 匹
    配/逐旗明细/摘录内容不读取不入记录）。"""
    ht = run19.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r19 hypothesis_test 结构不符")
    if ht.get("hypothesis_id") != "axis-plan-r19-criterion-operational":
        _fail("run-r19 hypothesis_id 不符")
    if ht.get("verdict") != "marginal":
        _fail(f"run-r19 verdict 不符：{ht.get('verdict')!r}（预期 marginal"
              f"=r19 字母在案锚）")
    m = ht.get("measurement", {})
    expect = {
        "top_abstain_rate_r19": M1_R19,
        "m4_top_rate_range_r19": M4_R19,
        "contact_family_abstain_flags_rubric_r19": CONTACT_R19,
        "top_abstain_count_r19": 18,
        "top_abstain_flags_r19": 39,
    }
    for key, want in expect.items():
        got = m.get(key)
        if got != want:
            _fail(f"run-r19 判据冻结值锚不符：{key}={got!r} != {want!r}"
                  f"（立即停止）")
    bso = m.get("bottom_side_observation", {})
    if bso.get("bottom_abstain_rate_r19") != M2_R19:
        _fail(f"run-r19 M2 锚不符：{bso.get('bottom_abstain_rate_r19')!r}")
    if (bso.get("bottom_abstain_count_r19"),
            bso.get("bottom_abstain_flags_r19")) != (4, 7):
        _fail("run-r19 bottom 4/7 锚不符")
    gc = m.get("guard_channel", {})
    if gc.get("g1_ok") is not True or gc.get("g2_guard_ok") is not True:
        _fail("run-r19 守门锚不符（预期 G1/G2 维持）")
    # 三族 rubric 聚合计数（黑点 4/contact 4/存在性其他 14）
    counts = (ht.get("mechanism_observation", {})
              .get("black_dot_tracking", {})
              .get("rubric_families", {}).get("counts", {}))
    want_counts = {"contact": CONTACT_R19,
                   "existence_blackdot": BLACKDOT_R19,
                   "existence_other": EXIST_OTHER_R19,
                   "other": 0,
                   "semantic_confusion": 0}
    if counts != want_counts:
        _fail(f"run-r19 三族 rubric 计数锚不符：{counts} != {want_counts}")
    # (iii-a) 援引聚合计数（旗级 6+2；notes 级 10/12）
    cc = (ht.get("mechanism_observation", {})
          .get("iiia_branch_observation", {})
          .get("citation_counts", {}))
    if cc.get("flag_level_iiia_literal") != 6:
        _fail(f"run-r19 旗级 (iii-a) 援引锚不符："
              f"{cc.get('flag_level_iiia_literal')!r} != 6")
    if cc.get("flag_level_branch_literal") != 2:
        _fail(f"run-r19 旗级分支字面援引锚不符："
              f"{cc.get('flag_level_branch_literal')!r} != 2")
    if cc.get("notes_level_iiia") != 10:
        _fail(f"run-r19 notes 级 (iii-a) 援引锚不符："
              f"{cc.get('notes_level_iiia')!r} != 10")
    non_citing = cc.get("notes_level_non_citing")
    if not isinstance(non_citing, list) or \
            cc["notes_level_iiia"] + len(non_citing) != 12:
        _fail(f"run-r19 notes 级分母锚不符（预期 10+2=12）：{non_citing!r}")
    # r19 字母=marginal 的判据布尔锚（(s) 支唯一未达项=M4）
    if m.get("crit_supported_m4_le_0_20") is not False:
        _fail("run-r19 crit_supported_m4_le_0_20 不符（预期 False=M4 未过门）")
    if m.get("crit_supported_contact_le_5") is not True or \
            m.get("crit_supported_m1_le_0_85") is not True:
        _fail("run-r19 crit_supported 其余布尔锚不符")
    if m.get("crit_marginal_contact_le_7") is not True or \
            m.get("crit_marginal_m4_le_0_26") is not True:
        _fail("run-r19 crit_marginal 布尔锚不符")
    # 判据数值自洽（预注册文本 ↔ 在案锚）
    if round(M1_R16_BASELINE - M1_R19, 6) != R19_DROP:
        _fail("自洽断言失败：0.771429−0.461538 != 0.309891")
    if round(R15_TOP_RATE - M1_R16_BASELINE, 6) != DRIFT_R15_R16:
        _fail("自洽断言失败：0.862069−0.771429 != 0.09064")
    if round(M1_R19 - REPLICATED_BAND, 6) != REPLICATED_LO or \
            round(M1_R19 + REPLICATED_BAND, 6) != REPLICATED_HI:
        _fail("自洽断言失败：replicated 带非 r19±0.10")
    if round(M4_R19 - M4_R19_SUPPORTED_GATE, 6) != M4_R19_GATE_GAP:
        _fail("自洽断言失败：0.211111−0.20 != 0.011111")
    if not (REPLICATED_LO <= M1_R19 <= REPLICATED_HI):
        _fail("自洽断言失败：r19 M1 自身不在 replicated 带内")
    if CONTACT_R19 > CONTACT_REPLICATED_THRESHOLD:
        _fail("自洽断言失败：r19 contact=4 不在 replicated 阈值 7 内")
    for needle in REQUIRED_NEEDLES:
        if needle not in HYPOTHESIS_TEST_TEXT:
            _fail(f"HYPOTHESIS_TEST_TEXT 缺判据数值/口径 {needle!r}"
                  f"（逐字要求破坏）")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r19.json",
        "sha256_measured": run19_sha,
        "frozen_values": (
            f"M tuple (M1,M2,M3,M4)=({M1_R19}, {M2_R19}, {M3_R19}, "
            f"{M4_R19})（12 派次全口径；M1={M1_R19_ARITHMETIC}、M2=4/7）；"
            f"contact 族 rubric={CONTACT_R19}；三族 rubric "
            f"contact/黑点/存在性={CONTACT_R19}/{BLACKDOT_R19}/"
            f"{EXIST_OTHER_R19}；(iii-a) 援引=旗级 6+2、notes 级 10/12；"
            "守门 G1/G2 维持；verdict=marginal——hypothesis_test 判据文"
            "本数值的在案锚（GT 匹配与逐旗明细不读取）"),
    }


def anchor_run16_baseline(run16: dict, run16_sha: str) -> dict:
    """calibration-run-r16：M1 基线冻结值与 guard_ok 锚（仅读判据值字段）。"""
    ht = run16.get("hypothesis_test")
    if not isinstance(ht, dict):
        _fail("calibration-run-r16 hypothesis_test 结构不符")
    m = ht.get("measurement", {})
    if m.get("top_abstain_rate_r16") != M1_R16_BASELINE:
        _fail(f"run-r16 top_abstain_rate_r16 不符："
              f"{m.get('top_abstain_rate_r16')}")
    if m.get("guard_channel", {}).get("guard_ok") is not True:
        _fail("run-r16 guard_ok 不为真（G2 基线证据不符）")
    return {
        "path_rel": "out/v3-tl2/calibration/calibration-run-r16.json",
        "sha256_measured": run16_sha,
        "frozen_values": (
            "top 27/35=0.771429（r16 零变更基线 M1）；guard_ok=True——"
            "hypothesis_test regressed/drifted 支截断值 0.771429 的在案锚"
            "（GT 匹配与逐旗明细不读取）"),
    }


def anchor_dev20_family_counts(dev20: dict) -> dict:
    """round20-dev-record：r20 三族 rubric 聚合计数（2/6/10）+r19/r20 家
    族对照在案结构复核（与 run-r19 装载值交叉核对）。"""
    mo = (dev20.get("hypothesis_test_i", {})
          .get("mechanism_observation", {}))
    counts = (mo.get("black_dot_tracking", {})
              .get("rubric_families", {}).get("counts", {}))
    want_counts = {"contact": 2,
                   "existence_blackdot": 6,
                   "existence_other": 10,
                   "other": 0,
                   "semantic_confusion": 0}
    if counts != want_counts:
        _fail(f"dev-r20 r20 三族 rubric 计数锚不符：{counts} != "
              f"{want_counts}")
    fam = (mo.get("experiment_comparison_ledger", {})
           .get("family_counts_vs_r18_r19", {}))
    if fam.get("contact", {}).get("r19_registered") != CONTACT_R19 or \
            fam.get("contact", {}).get("r20_measured") != 2:
        _fail(f"dev-r20 contact 对照锚不符：{fam.get('contact')!r}")
    if fam.get("existence_other", {}).get("r19_registered") != EXIST_OTHER_R19 \
            or fam.get("existence_other", {}).get("r20_measured") != 10:
        _fail(f"dev-r20 existence_other 对照锚不符："
              f"{fam.get('existence_other')!r}")
    ledger = (mo.get("experiment_comparison_ledger", {})
              .get("confounder_note", ""))
    if "0.09064" not in ledger:
        _fail(f"dev-r20 confounder_note 缺漂移参照 0.09064：{ledger!r}")
    return {
        "r20_family_counts_rubric": counts,
        "cross_check": (
            "r19 侧 4/4/14 与 run-r19 装载值逐一相等、r20 侧 2/6/10 与 "
            "dev-r20 rubric_families 计数逐一相等（family_counts_vs_r18_"
            "r19 在案结构交叉核对，均 fail-closed）"),
    }


# ---------------------------------------------------------------------------
# 记录构建（纯函数；同参重建两次逐字节一致自证）
# ---------------------------------------------------------------------------

def build_record(*, guidance19_sha: str, guidance19_bytes_n: int,
                 r19_record_sha: str, r16_record_sha: str,
                 dev_ref: dict, axis_ref: dict, run19_ref: dict,
                 run16_ref: dict, dev20_fam: dict, witness_sha: str,
                 protocol_sha: str, png_checks: list[dict]) -> dict:
    """构建 r22-prep-record 内容（纯函数：同入参必得同 dict）。"""
    return {
        "schema_version": "3.0",
        "kind": "tl2_calibration_r22_prep_record",
        "round_id_constant": ROUND_ID,
        "declared_date": DATE_CONSTANT,
        "round_label": "r22",
        "round_nature": (
            "同指引重复轮（收敛归因；r16 先例：r15→r16 同指引重复、渲染零"
            "变更、仅实例重抽，第十六轮先例；本轮=第二十二轮）：唯一实验操"
            "作=reader 实例群抽样（每视角 3 新实例 i1/i2/i3×4 视角格=12 "
            "派次全部重抽，与 r19/r20 实例群无身份延续；两波次串行保序：同"
            "一实例先 applied 后 prep1、flag_id 编号跨板连续）；判读指引="
            "observation-guidance-r19.md 字节复用（8633bda5 实测锚；本脚本"
            "零写入、零编辑、零机械变换——本轮不新建指引文件、无指引新文"
            "件）；渲染零变更=renders-r14b 四图字节复用（四 PNG sha256_"
            "file 实测与 render-witness-r14b.json 登记值 fail-closed 比对一"
            "致，即 r14–r20 轮盲读所用同一批文件，见 instrument_change）；"
            "GT/阈值/协议零变更（13 条冻结、v1.1+v1.2 维持）；changed_"
            "variables=0（指引字节复用+渲染字节复用+GT/阈值/协议零变更，"
            "见 guidance_reuse.mode=byte_reuse_zero_change 与 changed_"
            "variables=[]）；【跳号声明】r21 号段=axis-experiment-plan-"
            "r17-r20（b6ec6467 冻结件）combination_decision_rule.ii_full_"
            "combination 预留的 R21 全组合位（冻结原文「若 R20 收益 ≥ 最"
            "优单轴（comparison_rule 排序不劣于最优单轴）且三轴均各自正收"
            "益（各自 M1 不劣于 r16 基线）→ 追加全组合轮 R21（三轴全组"
            "合）」——条件轮，per early_stop_rule.strong_single_axis_"
            "shortcut「……不铺全组合（R21 不做）」未触发、该槽位永久留"
            "空）；round20-dev-record next_iteration_targets[0] 已登记「"
            "R21 不做」（三重独立依据在案：early_stop strong_single_axis_"
            "shortcut 命中→阶段2 仅一个组合轮+三轴不全正（轴1 r17 M1=0.88 "
            "劣于基线 0.771429）+r20 G1 破坏排除追加）；r22 为该登记之后的"
            "时序下一轮、与该 R21 全组合位无涉（非其执行、非其替代）——"
            "轮次号跳号以免台账歧义；执行 round20-dev-record next_"
            "iteration_targets[1] 同指引重复轮候选（实测链见 guidance_"
            "reuse.chain_anchors.round20_dev_record_authorization），用户 "
            "2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的继续」"
            "（见 user_directive_note）；r19 指引已在盘冻结、本轮只读零写"
            "入；盲读由编排侧在本记录之后以 12 次独立实例盲读执行（12 派"
            "次 reader 实例群全部重抽）"),
        "user_directive_note": (
            "用户 2026-09-09「三条轴单独/组合/全组合尝试，选择收益最大的继"
            "续」（axis-experiment-plan-r17-r20 user_quote 在案原文，实测链"
            f"见 guidance_reuse.chain_anchors.axis_experiment_plan_frozen_"
            f"r21_slot；round20-dev-record.json 实测 sha256="
            f"{dev_ref['sha256_measured']}）=本实验授权指令；阶段2 已收束"
            "（round20-dev-record next_iteration_targets[0]：收益最大配置="
            "轴3 单变量 guidance-r19、R21 不做）后，其操作性子句「选择收"
            "益最大的继续」=授权对收益最大配置（r19 配置）继续迭代；dev-"
            "r20 next_iteration_targets[1] 同指引重复轮候选（preregistra"
            "tion_required=true：prep-record 预注册先于盲读冻结）=本轮设"
            "计出处与合法性依据（候选原文逐字摘录于 guidance_reuse.chain_"
            "anchors.round20_dev_record_authorization.repeat_candidate_"
            "quote）；r22=该候选的执行轮；预注册后执行；不得回溯改判既往"
            "轮次（r8–r20 字母裁决维持不变）"),
        "instrument_change": {
            "changed": False,
            "note": "渲染与 r14/r15/r16/r18/r19/r20 完全相同（renders-r14b "
                    "字节复用，四 PNG 实测=witness-r14b 登记值），本轮零指"
                    "引零渲染变更、仅实例群重抽",
            "renders": png_checks,
            "witness": "render-witness-r14b.json（b63771f9，fail-closed 复核）",
            "declaration": (
                "本轮 prep 零重渲染、零 out/ 既有文件改动（四 PNG "
                "sha256_file 实测=witness-r14b 登记值；bottom 两板逐字节同 "
                "d7284259；top 无配色 298bc620/b2f84524）；指引=observation-"
                "guidance-r19.md 字节复用零写入（8633bda5）"),
        },
        "no_instrument_change": True,
        "guidance_reuse": {
            "base": "observation-guidance-r19.md",
            "base_path_rel": (
                "out/v3-tl2/calibration/observation-guidance-r19.md"),
            "base_sha256": guidance19_sha,
            "base_sha256_prefix_expected": GUIDANCE_R19_SHA_PREFIX,
            "mode": "byte_reuse_zero_change",
            "derived": None,
            "derived_path_rel": None,
            "derived_sha256": None,
            "byte_size": {"base": guidance19_bytes_n, "delta": 0},
            "edit_list": [],
            "zero_write_declaration": (
                "本轮不新建指引文件：observation-guidance-r19.md 零字节不动"
                "（本脚本无任何指引写路径；实测哈希在 guidance_reuse."
                "base_sha256，与开工实测 8633bda5 锚 fail-closed 一致）——"
                "r16 先例（r15 指引字节复用+派发层前缀覆盖）同型执行"),
            "verbatim_scope_note": (
                "§2–§7 判据文本（含 §4 内 (iii-a) 可操作分辨条款、反放宽条"
                "款「仅因形态不熟悉、不确定其设计含义，不构成判为正常设计"
                "特征的理由」、三路出口、量化判据 (i)(ii)(iii) 原文）与 §5A "
                "渲染配色仪器注记随 r19 指引本体原样生效（字节复用=零措辞"
                "调整空间）；§6 示例旗 ID 前缀保持 R19T-/R19B-（r19 落盘原"
                "文，字节复用不改——本轮指引内 R19T- 恰 4 处、R19B- 恰 1 "
                "处实测锚定），R22 派次 flag_id 前缀 R22T/R22B 由派发指令层"
                "覆盖（前缀差异登记；r16 先例在案：r15 指引+R16T 前缀执行"
                "先例，见 protocol_amendment.naming）；本轮指引无 §5B 节"
                "（r19 基座=r15 结构在案）——§5B 援引计数机制观察照记、任"
                "何援引为零上下文"),
            "chain_anchors": {
                "base_sha256_prefix_expected": GUIDANCE_R19_SHA_PREFIX,
                "r19_prep_record_structure_lineage": {
                    "path_rel": "out/v3-tl2/calibration/r19-prep-record.json",
                    "sha256": r19_record_sha,
                    "cross_check": "24 键顶层结构逐键镜像（本轮判据/指引基"
                                   "座血统= r19）",
                },
                "r16_prep_record_same_guidance_repeat_precedent": {
                    "path_rel": "out/v3-tl2/calibration/r16-prep-record.json",
                    "sha256": r16_record_sha,
                    "note": "同指引重复轮先例（r15→r16：指引/渲染零变更、"
                            "仅实例重抽、派发层前缀覆盖；changed_variables="
                            "[] 在案）",
                },
                "round20_dev_record_authorization": dev_ref,
                "axis_experiment_plan_frozen_r21_slot": {
                    "path_rel": (
                        "out/v3-tl2/calibration/axis-experiment-plan-r17-"
                        "r20.json"),
                    "sha256_measured": axis_ref["sha256_measured"],
                    "r21_slot_frozen_quotes":
                        axis_ref["r21_slot_frozen_quotes"],
                    "user_quote": axis_ref["user_quote"],
                    "role": "R21 全组合槽位冻结原文（跳号声明的槽位依据）+"
                            "用户指令原文锚",
                },
                "run_r19_metric_anchor": run19_ref,
                "run_r16_baseline_anchor": run16_ref,
                "dev_r20_family_counts_cross_check": dev20_fam,
                "render_witness_r14b_byte_reuse": {
                    "path_rel": (
                        "out/v3-tl2/calibration/render-witness-r14b.json"),
                    "sha256": witness_sha,
                },
                "evaluation_protocol_v1_preserved": {
                    "path_rel": (
                        "out/v3-tl2/calibration/evaluation-protocol-v1.md"),
                    "sha256": protocol_sha,
                },
            },
        },
        "changed_variables": [],
        "manipulated_factor": "reader 实例群（12 派次全部重抽；与 r19/r20 "
                              "实例群无身份延续）",
        "unchanged_components": [
            {
                "byte_reuse": True,
                "component": "renders-r14b 四图字节复用（渲染零变更）",
                "note": "开工时 sha256_file 实测四 PNG 并与 render-witness-"
                        "r14b.json 登记值逐字比对（bottom=renders.applied/"
                        "prep1.sha256；top=top_zero_change_copies.sha256）"
                        "——四图即 r14–r20 轮盲读所用同一批文件；本轮零重"
                        "渲染、零仪器变更",
                "pngs": png_checks,
                "witness": "render-witness-r14b.json（b63771f9，fail-closed "
                           "复核）",
            },
            "判读指引 observation-guidance-r19.md 字节复用（8633bda5 实测"
            "锚）：§2 类别枚举、§3 收窄判据、§3A 判据示例、§4 全文（含量"
            "化判据 (i)(ii)(iii)、(iii) 接触性判据、(iii-a) 可操作分辨条款、"
            "三路出口、反放宽条款「仅因形态不熟悉、不确定其设计含义，不构"
            "成判为正常设计特征的理由」）、§5 courtyard 说明、§5A 渲染配"
            "色仪器注记、§6 输出格式（示例旗 ID 前缀保持 R19T-/R19B- 落盘"
            "原文）、§7 格式对齐提示——零字节不动（本轮不新建指引文件）",
            "GT 集：零改动（13 条冻结；gt-audit-r1 三候选全部关闭在案，"
            "GT 侧不再有候选，r9–r20 延续引用）",
            "阈值：APR-0011（gt_recall≥0.75/seed_match_rate≥0.5/"
            "abstain_rate≤0.5）与 CONTAINMENT_MIN/AREA_RATIO_MAX 常量零改"
            "动（只作口径引用）",
            "评估协议：v1.1+v1.2 维持（evaluation-protocol-v1.md 零字节保"
            "留；本轮不新建协议文件，见 protocol_amendment）",
            "bottom 视判读口径：沿用 r4 指引原文不改（top/bottom 判读口"
            "径在图像空间完全一致、不做镜像换算；本轮渲染零字节变更）",
            "度量设计五条与聚合口径：沿 r19-prep-record measurement_design"
            ".items 同一口径（仅轮次标识、reader 前缀与渲染件名按 r22 改"
            "写）",
        ],
        "bottom_view_note": (
            "本轮 bottom 视渲染件=renders-r14b 字节复用（与 R14/R15/R16/"
            "R18/R19/R20 完全相同文件：白墨图元→橙 (255,165,0)、板内空隙"
            "白→绿 (0,128,0)、其余层 kicad 原配色不变；四 PNG sha256_file "
            "实测=witness-r14b 登记值 fail-closed 比对一致）——渲染零变"
            "更；本轮零指引零渲染变更（唯一实验操作=实例群重抽）；bottom "
            "视判读口径沿用 r4 指引原文不改（top/bottom 判读口径在图像空"
            "间完全一致、不做镜像换算）；bottom 零旗标分母=0 时弃权率按 "
            "cal._ratio 先例=None 口径照旧"),
        "measurement_design": {
            "preregistration_declaration": (
                "本节先于 R22 盲读冻结（本记录=预注册件；evaluation-"
                "protocol-v1 §4 口径：轮次开始后不得增删）；五条逐条预注"
                "册，聚合口径全部如实并列、不二选一、不挑优（items 沿 "
                "r19-prep-record measurement_design.items 同一口径按本轮改"
                "写：12 派次=2 板×2 视图×3 实例；reader 前缀 R22T/R22B"
                "（派发层覆盖）；图像=renders-r14b 四图（字节复用）；聚合"
                "口径与 s71/s74 比较脚本同血统；代表配置/逐实例/双口径分"
                "列）"),
            "items": [
                {
                    "item": 1,
                    "name": "主记录单位=实例",
                    "text": (
                        "每实例给出其视角两板合计的 flag_count、abstain_"
                        "count、abstain_rate（分母=该实例该视角全部旗标，"
                        "跨两板合计）、非弃权旗标清单、逐旗与 GT 的 "
                        "containment/area_ratio 匹配明细（比较器 fail-closed"
                        " 校验照旧）"),
                },
                {
                    "item": 2,
                    "name": "视角层聚合",
                    "text": (
                        "每视角 3 实例的 flag_count/abstain_rate/matches 各"
                        "给中位数+最小值+最大值，如实三分列、不取整"),
                },
                {
                    "item": 3,
                    "name": "GT 匹配聚合双口径",
                    "text": (
                        "union（≥1 实例命中即计）与 agreement（≥2/3 实例命"
                        "中才计）两口径并列报告，均如实、不二选一；逐 GT 条"
                        "目给出 matched_by_count（0..3）"),
                },
                {
                    "item": 4,
                    "name": "联合门评价（APR-0011）",
                    "text": (
                        "代表配置=每视角取 flag_count 中位数实例组成代表配"
                        "置，计算一轮 joint 结果；同时如实给出 per-metric 实"
                        "例间范围（min..max）；代表配置 joint 结果、"
                        "per-metric 实例间范围、逐实例原始记录（item 1）三"
                        "者并列如实呈现，不合并、不挑优；APR-0011 阈值零改"
                        "动"),
                },
                {
                    "item": 5,
                    "name": "bottom 零旗标处理",
                    "text": (
                        "沿用库侧 cal._ratio 先例（pcbflow/calibration.py "
                        "_ratio：零分母→None）——实例/视角层遇零旗标分母"
                        "时弃权率=None+文字说明，不编造数值（r10 run-record "
                        "bottom=0/0→None 同口径在案）"),
                },
            ],
        },
        "hypothesis_test": HYPOTHESIS_TEST,
        "attribution_plan": {
            "declaration": (
                "本轮恰一个实验操作（reader 实例群抽样：12 派次全部重抽）、"
                "检验恰一个假设（round20-dev-record next_iteration_targets"
                "[1] 同指引重复轮候选；hypothesis_id=r20-dev-record-"
                "candidate-r19-config-same-guidance-repeat）；归因目的="
                "r19 配置单轮收益（M1=0.461538/contact 族 10→4/M4=0.211111"
                "）是否在新鲜实例群复现——真实收益 vs 实例群漂移的收敛归"
                "因判别；量级参照=r15→r16 同指引纯重抽 M1 漂移 0.09064 与 "
                "r19 降幅 0.309891 并列在案（axis-plan comparison_rule 显"
                "著收益阈值 0.10 覆盖漂移噪声的历史幅度参照同源）；跨轮对"
                "比为方向性、实例群混杂在本轮=唯一实验操作、恰是裁决变量；"
                "字母/机制观察/度量教训三分记账（adjudication.m4_second_"
                "sample_separate 与 mechanism_observation_separate、metric_"
                "lesson_separate 单列，不凌驾字母裁决）"),
            "primary_channel": {
                "change": (
                    "reader-instance-group-resample（实例群抽样；非指引/渲"
                    "染/GT/阈值/协议变更——指引字节复用 8633bda5、渲染字节"
                    "复用 r14b）"),
                "metric": (
                    "M1（top 全旗聚合弃权率，12 派次全口径）落点归因裁决（三"
                    "支）：replicated 落 [0.361538, 0.561538]（r19±0.10）且 "
                    "contact 族 ≤7 且 G1/G2 维持；drifted 未达 replicated 且 "
                    "M1 < 0.771429 且 G1/G2 维持；regressed M1 ≥ 0.771429 或 "
                    "G1/G2 任一破坏——详见 hypothesis_test.adjudication；"
                    "M4 第二轮样本单列、不进字母裁决"),
                "replicated": (
                    "M1 落 [0.361538, 0.561538] 且 contact 族 ≤7 且 G1/G2 "
                    "维持 → r19 量级获复制支持（字母=replicated）"),
                "drifted": (
                    "未达 replicated 且 M1 < 0.771429 且 G1/G2 维持 → r19 "
                    "量级部分归因实例群、收益方向存但幅度不确定（字母="
                    "drifted）"),
                "regressed": (
                    "M1 ≥ 0.771429 或 G1/G2 任一破坏 → r19 量级不可复制、"
                    "轴3 收益判定降级为单轮现象（字母=regressed）"),
            },
            "guard_channel": {
                "metric": (
                    "G1=bottom courtyard 非弃权 0/0/0 维持（对照 r15–r19 "
                    "在案 0/0/0、r20 破坏 2/0/0 在案=分岔记录；G1 为 "
                    "(iii-a) 间隙支「不得弃权」方向的反向风险守门——条款若"
                    "被误用为「少弃权」压力，G1/守门与 regressed 支须如实记"
                    "录）；G2=guard_ok=True 维持（top 视非弃权旗标 "
                    "frame_box_pct 几何门，面积比出局条目按 guard_channel "
                    "如实登记；run-r19 几何门 0→r20 0 在案）"),
                "requirement": (
                    "§3 收窄判据逐字保留（r19 指引字节复用），非弃权框仍须"
                    "满足；任一守门破坏→regressed 支命中（描述性边界，非 "
                    "axis-plan early_stop 出局语义——本实验已收束、本轮为收"
                    "敛归因轮，出局语义不适用、破坏照实记录）"),
            },
            "comparator_note": "比较器逐旗输出含失败通道明细",
            "grouping_note": (
                "聚合指标按预注册度量设计五条如实记录（实例层主记录+视角"
                "层三分列聚合+GT 匹配双口径+联合门代表配置/范围并列；"
                "APR-0011 阈值零改动）；bottom GT 无源=bottom 旗标与 GT 匹"
                "配应为空（结构性在案，不影响收敛计数口径）；字母裁决/机"
                "制观察/度量教训三分记账、互不凌驾；归因分组逻辑由编排侧"
                "在 close 包执行；指引内零 GT、零轮次结果数字（基线数字仅"
                "入本编排侧记录）"),
        },
        "evaluation_domain": {
            "declared": "development",
            "in_calibrated_range": False,
            "note": "in_calibrated_range 恒 False，直到正式采纳为止"
                    "（development 域只描述不断言）",
        },
        "no_loosening_note": (
            "零变更重复轮：判读指引=observation-guidance-r19.md 字节复用（"
            "8633bda5 实测锚）——反放宽条款「仅因形态不熟悉、不确定其设计"
            "含义，不构成判为正常设计特征的理由」、(iii-a) 可操作分辨条款与"
            "三路出口随指引本体原样生效，零变更轮无任何措辞调整空间（本脚"
            "本无任何指引写路径）；本轮三支判据（replicated [0.361538, "
            "0.561538] / drifted M1<0.771429 / regressed M1≥0.771429 或守门"
            "破坏）只用于收敛归因方向，不触碰 APR-0011 门（gt_recall≥0.75/"
            "seed_match_rate≥0.5/abstain_rate≤0.5）与任何阈值常量"
            "（CONTAINMENT_MIN/AREA_RATIO_MAX，只作口径引用）——门照常独"
            "立计算；不构成任何阈值反向放宽"),
        "pre_round_review": {
            "status": "not_required_zero_change_round",
            "basis": (
                "同指引重复轮先例 r16（r15→r16：指引/渲染零变更、仅实例重"
                "抽、派发层前缀覆盖在案）+round20-dev-record 授权链（targets"
                "[0] 阶段2 收束+R21 不做、targets[1] 同指引重复轮候选 "
                "preregistration_required=true）+用户 2026-09-09「选择收益最"
                "大的继续」操作性授权；无新干预引入（指引/渲染/GT/阈值/协"
                "议全部字节复用或零变更）"),
        },
        "protocol_amendment": {
            "protocol_id": "evaluation-protocol-v1",
            "version": "v1.1+v1.2 维持",
            "changes": [],
            "v1_semantics": "每视角 1 独立 reader 实例（r3–r10 在案执行口"
                            "径）",
            "v1_1_semantics": (
                "每视角 3 独立实例（i1/i2/i3）+聚合口径：实例层主记录、视"
                "角层中位数/最小/最大聚合、GT 匹配 union/agreement 双口径"
                "并列、联合门代表配置+实例间范围并列（measurement_design "
                "五条）；本轮 n=3 多实例与聚合口径全部沿用"),
            "v1_2_semantics": (
                "跨轮工具行为规约（r12 起生效，本轮沿用）：所有 reader 派"
                "发指令统一硬性条款——「禁止对图像做任何程序化处理（裁剪/"
                "放大/像素分析/衍生图像生成等）；判读只允许以 Read 工具查"
                "看原图（同一原图可重复查看）」——仪器行为钉住；属派发层，"
                "读者上下文=指引+单张 PNG+派发指令（含规约条款），零 GT；"
                "不影响判读语义——分类判据零变更，仅输入手段固定"),
            "v1_file_preserved": {
                "path_rel": "out/v3-tl2/calibration/evaluation-protocol-v1.md",
                "sha256_prefix_expected": EVAL_PROTOCOL_V1_SHA_PREFIX,
                "sha256_measured": protocol_sha,
                "zero_byte_preserved": protocol_sha.startswith(
                    EVAL_PROTOCOL_V1_SHA_PREFIX),
                "note": (
                    "v1 原文零字节保留（r11–r20 轮同口径在案登记，本脚本 "
                    "fail-closed 在盘+哈希复核）；本轮无新增版本、不新建协"
                    "议文件"),
            },
            "blind_read_execution": (
                "12 次盲读=4 视角格（applied-top/applied-bottom/prep1-top/"
                "prep1-bottom，即 2 板两派次×top/bottom 两视角）×每格 3 实"
                "例（i1/i2/i3）；本轮 12 派次 reader 实例群全部重抽（3 新实"
                "例/视角，与 r19/r20 无实例身份延续——同指引重复轮的唯一实"
                "验操作）；实例上下文=指引（observation-guidance-r19.md 字"
                "节复用）+单张 PNG（renders-r14b 四图）+派发命名指令（含 "
                "v1.2 工具行为规约硬性条款：纯 Read 内联判读、禁止任何程序"
                "化图像处理），零 GT、零历史判读件、零诊断/探针内容；两波"
                "次串行保序（同一实例先 applied 后 prep1，flag_id 编号跨板"
                "连续）"),
            "naming": (
                "reader_id=reader-r22-{top,bottom}-i{1,2,3}；flag_id 前缀 "
                "R22T/R22B（r19 指引 §6 示例前缀为 R19T-/R19B- 落盘原文、"
                "字节复用不改——前缀差异登记：本轮派发层命名覆盖为 R22T/"
                "R22B，r16 先例在案：r15 指引+R16T 前缀执行先例，与 r19「随"
                "指引落盘固化」路径不同，如实登记）；实例间编号独立，同实"
                "例跨板连续"),
            "scope_note": (
                "本轮协议侧零变更（v1.1+v1.2 维持，无新增版本）；in_"
                "calibrated_range 恒 False 不变"),
        },
        "read_prohibition_compliance": True,
        "read_prohibition_note": (
            "本包全程零 GT 暴露：未读取任何 *.png/*.pdf 内容（PNG 仅哈希+"
            "magic，零内容判读、零像素读取）、ground-truth-*、reader-raw-*、"
            "derivation-log-*、任何 compare/评估产物、diag 内容（零读取）；"
            "本脚本只读输入=observation-guidance-r19.md（判读指引基座；"
            "8633bda5 锚 fail-closed，零写入——本轮零编辑零变换、不新建指"
            "引文件）、r19-prep-record.json（链锚=e4cf2d3c 先验证；结构血统"
            "与 24 键镜像来源）、r16-prep-record.json（链锚=46fbd15b；同指"
            "引重复轮先例）、round20-dev-record.json（80e3e9e2 锚；仅读取 "
            "kind/round_id/declared_date 与 next_iteration_targets[0]/[1] 授"
            "权原文+三族 rubric 聚合计数做对照锚）、axis-experiment-plan-"
            "r17-r20.json（b6ec6467 锚；R21 槽位冻结原文、守门、用户指令原"
            "文）、calibration-run-r19.json（e5755a11 锚；仅读取 "
            "hypothesis_test 顶层判据冻结值字段+guard_channel+三族 rubric "
            "聚合计数+(iii-a) 援引聚合计数——M1=0.461538/M2=0.571429/M4="
            "0.211111/contact=4/G1G2 维持/verdict=marginal/援引 6+2、10/12；"
            "其 GT 匹配与逐旗明细内容不读取、不入记录）、calibration-run-"
            "r16.json（2c1f8265 锚；仅读取 hypothesis_test 顶层判据冻结值字"
            "段——M1=0.771429、guard_ok=True；其 GT 匹配与逐旗明细内容不读"
            "取、不入记录）、render-witness-r14b.json（b63771f9 锚 fail-"
            "closed；四 PNG 见证登记值）、evaluation-protocol-v1.md（仅在"
            "盘+哈希复核，锚=22dc7337）；renders-r14b 四 PNG 仅哈希+magic"
            "（渲染零变更以 witness 登记哈希比对为准）；本轮恰两个新建文"
            "件=scripts/s76_calibration_r22_prep.py（生成器本体）与 "
            "r22-prep-record.json（本轮仅有的 out/ 新建文件；本轮无探针/"
            "诊断脚本、无指引新文件）；reader 派发（后续编排侧执行）上下文"
            "=observation-guidance-r19.md+单张 PNG（renders-r14b）+派发指"
            "令（R22T/R22B 前缀=派发层覆盖、reader-r22-{top,bottom}-i{1,"
            "2,3}、v1.2 工具行为规约硬性条款），零 GT、零历史判读件、零 r19"
            "/r20 判读结果注入、零指引之外的解释；视觉判读禁止由编排/收口"
            "包兼任；跨实例/跨视角禁止交流（12 次盲读相互独立、不得交换判"
            "读信息——独立性是多实例协议的前提，亦为实例群重抽收敛归因的"
            "前提）。"),
        "no_visual_reading": True,
        "_verification_note": None,  # 占位删除前校验用（见 main 内断言）
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 前置存在性（fail-closed）----
    for path in (GUIDANCE_R19, R19_PREP_RECORD, R16_PREP_RECORD,
                 DEV_RECORD_R20, AXIS_PLAN, RUN_R19, RUN_R16, WITNESS_R14B,
                 EVAL_PROTOCOL_V1):
        if not path.exists():
            _fail(f"缺失：{path}")
    if not RENDR14B_DIR.is_dir():
        _fail(f"缺失渲染目录：{RENDR14B_DIR}")
    # 目标文件 RECORD 不做前置硬拒绝：落盘阶段防覆写守卫按红线口径执行
    # ——已存在且重建字节不同→FAIL；已存在且逐字节相同→幂等通过（零覆
    # 写）。（首轮创建前置=目标不存在，已由编排侧开工确认。）

    # ---- 冻结锚验证（fail-closed）----
    r19_record_sha = _sha(R19_PREP_RECORD)
    r16_record_sha = _sha(R16_PREP_RECORD)
    dev20_sha = _sha(DEV_RECORD_R20)
    axis_sha = _sha(AXIS_PLAN)
    run19_sha = _sha(RUN_R19)
    run16_sha = _sha(RUN_R16)
    witness_sha = _sha(WITNESS_R14B)
    protocol_sha = _sha(EVAL_PROTOCOL_V1)
    for sha, prefix, label in (
            (r19_record_sha, R19_PREP_RECORD_SHA_PREFIX, "r19-prep-record"),
            (r16_record_sha, R16_PREP_RECORD_SHA_PREFIX, "r16-prep-record"),
            (dev20_sha, DEV_RECORD_R20_SHA_PREFIX, "round20-dev-record"),
            (axis_sha, AXIS_PLAN_SHA_PREFIX, "axis-experiment-plan"),
            (run19_sha, RUN_R19_SHA_PREFIX, "calibration-run-r19"),
            (run16_sha, RUN_R16_SHA_PREFIX, "calibration-run-r16"),
            (witness_sha, WITNESS_R14B_SHA_PREFIX, "render-witness-r14b"),
            (protocol_sha, EVAL_PROTOCOL_V1_SHA_PREFIX,
             "evaluation-protocol-v1")):
        if not sha.startswith(prefix):
            _fail(f"{label} sha 前 8={sha[:8]} != 预期 {prefix}（锚不符，立即"
                  f"停止）")

    r19_record = json.loads(R19_PREP_RECORD.read_text(encoding="utf-8"))
    if r19_record.get("schema_version") != "3.0":
        _fail("r19-prep-record schema_version != 3.0（结构漂移）")
    if r19_record.get("kind") != "tl2_calibration_r19_prep_record":
        _fail("r19-prep-record kind 不符（结构漂移）")
    if r19_record.get("round_id_constant") != "2026-09-09-r19":
        _fail("r19-prep-record round_id_constant != 2026-09-09-r19（结构漂"
              "移）")
    r16_record = json.loads(R16_PREP_RECORD.read_text(encoding="utf-8"))
    if r16_record.get("kind") != "tl2_calibration_r16_prep_record" or \
            r16_record.get("round_label") != "r16":
        _fail("r16-prep-record 先例件结构漂移")

    # ---- 指引零写入复核（只读哈希+落盘事实锚；本脚本全程无指引写路径）----
    guidance = check_guidance_zero_write()
    guidance19_sha = guidance["sha256_measured"]

    # ---- 结构探测（判据冻结值锚与授权链锚）----
    witness = json.loads(WITNESS_R14B.read_text(encoding="utf-8"))
    axis_plan = json.loads(AXIS_PLAN.read_text(encoding="utf-8"))
    run19 = json.loads(RUN_R19.read_text(encoding="utf-8"))
    run16 = json.loads(RUN_R16.read_text(encoding="utf-8"))
    dev20 = json.loads(DEV_RECORD_R20.read_text(encoding="utf-8"))
    probe_witness(witness)
    png_checks = check_renders_byte_reuse(witness)
    dev_ref = extract_authorization(dev20, dev20_sha)
    axis_ref = probe_axis_plan_r21_slot(axis_plan, axis_sha)
    run19_ref = anchor_run19_metrics(run19, run19_sha)
    run16_ref = anchor_run16_baseline(run16, run16_sha)
    dev20_fam = anchor_dev20_family_counts(dev20)

    # ---- 记录构建 + 断言 ----
    record = build_record(
        guidance19_sha=guidance19_sha,
        guidance19_bytes_n=guidance["byte_size"],
        r19_record_sha=r19_record_sha, r16_record_sha=r16_record_sha,
        dev_ref=dev_ref, axis_ref=axis_ref, run19_ref=run19_ref,
        run16_ref=run16_ref, dev20_fam=dev20_fam, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks)
    # 占位键不得进入落盘记录（构建后校验）
    if record.pop("_verification_note", None) is not None:
        _fail("内部占位键非 None（构建逻辑错误）")
    # 结构镜像断言：顶层键集合与 r19-prep-record 24 键逐键镜像
    missing = sorted(set(r19_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r19_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r19-prep-record 镜像不符：少={missing}，"
              f"多={extra}")
    # hypothesis_test 逐字断言链：预注册判据原文→json.loads→常量→记录字段
    ht_text = json.loads(HYPOTHESIS_TEST_TEXT)
    if HYPOTHESIS_TEST != ht_text:
        _fail("hypothesis_test 常量与预注册判据原文不一致（逐字要求被破坏）")
    if record["hypothesis_test"] != HYPOTHESIS_TEST:
        _fail("hypothesis_test 与预注册判据常量不一致（逐字要求被破坏）")
    if HYPOTHESIS_TEST["hypothesis_id"] != \
            "r20-dev-record-candidate-r19-config-same-guidance-repeat":
        _fail("hypothesis_test.hypothesis_id 不符")
    adj = HYPOTHESIS_TEST["adjudication"]
    if set(adj.keys()) != {"replicated", "drifted", "regressed",
                           "m4_second_sample_separate",
                           "mechanism_observation_separate",
                           "metric_lesson_separate",
                           "descriptive_boundary_note"}:
        _fail(f"adjudication 三支+单列结构不符：{sorted(adj.keys())}")
    if adj["descriptive_boundary_note"] != \
            r19_record["hypothesis_test"]["adjudication"][
                "descriptive_boundary_note"]:
        _fail("descriptive_boundary_note 未照抄 r19 血统原文")
    # 结构自证（零变更轮口径；跳号声明）
    if record["instrument_change"]["changed"] is not False:
        _fail("instrument_change.changed 必须为 False（零变更重复轮）")
    if record["no_instrument_change"] is not True:
        _fail("顶层 no_instrument_change 必须为 True（零变更重复轮）")
    if record["changed_variables"] != []:
        _fail("同指引重复轮：changed_variables 必须为空列表（=0）")
    if record["guidance_reuse"]["mode"] != "byte_reuse_zero_change":
        _fail("guidance_reuse.mode 必须为 byte_reuse_zero_change")
    if record["guidance_reuse"]["edit_list"] != []:
        _fail("guidance_reuse.edit_list 必须为空（零编辑）")
    if record["guidance_reuse"]["base_sha256"].startswith(
            GUIDANCE_R19_SHA_PREFIX) is not True:
        _fail("guidance_reuse.base_sha256 与 8633bda5 锚不符")
    if record["guidance_reuse"]["byte_size"] != {"base": 21435, "delta": 0}:
        _fail("guidance_reuse.byte_size 不符（预期 r19 指引 21435 B 零差）")
    if record["manipulated_factor"] != "reader 实例群（12 派次全部重抽；与 " \
            "r19/r20 实例群无身份延续）":
        _fail("manipulated_factor 不符（唯一实验操作=实例群重抽）")
    if record["pre_round_review"]["status"] != "not_required_zero_change_round":
        _fail("pre_round_review.status 不符")
    rn = record["round_nature"]
    for needle in ("同指引重复轮", "r16 先例", "【跳号声明】", "R21 不做",
                   "三重独立依据", "r22 为该登记之后的时序下一轮、与该 R21 "
                   "全组合位无涉", "changed_variables=0", "仅实例重抽"):
        if needle not in rn:
            _fail(f"round_nature 缺「{needle}」声明")
    if record["round_id_constant"] != ROUND_ID or \
            record["round_label"] != "r22" or \
            record["declared_date"] != DATE_CONSTANT:
        _fail("轮次标识不符（2026-09-09-r22 / r22 / 2026-09-09）")
    # 前缀差异登记断言
    naming = record["protocol_amendment"]["naming"]
    for needle in ("R22T/R22B", "派发层命名覆盖", "R19T-/R19B- 落盘原文",
                   "r16 先例在案：r15 指引+R16T 前缀执行先例",
                   "reader-r22-{top,bottom}-i{1,2,3}"):
        if needle not in naming:
            _fail(f"protocol_amendment.naming 缺前缀差异登记：{needle!r}")
    if "§5B 援引计数" not in adj["mechanism_observation_separate"]:
        _fail("adjudication.mechanism_observation_separate 缺 §5B 援引计数"
              "预注册")
    # measurement_design 五条
    md = record["measurement_design"]
    if not isinstance(md.get("items"), list) or len(md["items"]) != 5:
        _fail("measurement_design.items 必须恰 5 条（预注册度量设计）")
    if [it["item"] for it in md["items"]] != [1, 2, 3, 4, 5]:
        _fail("measurement_design.items 编号必须为 1..5")
    for needle in ("renders-r14b", "R22T/R22B", "s71/s74 比较脚本同血统"):
        if needle not in md["preregistration_declaration"]:
            _fail(f"measurement_design 预注册声明缺 {needle!r} 口径")
    if record["evaluation_domain"]["in_calibrated_range"] is not False:
        _fail("evaluation_domain.in_calibrated_range 必须恒 False")
    if record["protocol_amendment"]["v1_file_preserved"][
            "zero_byte_preserved"] is not True:
        _fail("protocol_amendment.v1_file_preserved.zero_byte_preserved "
              "必须为真")
    if len({p["sha256_measured"] for p in png_checks}) != 3:
        _fail("四 PNG sha 集合应为 3 个不同值（两 bottom 同哈希）")

    record_bytes = hashing.canonical_json_bytes(record)
    rebuild = build_record(
        guidance19_sha=guidance19_sha,
        guidance19_bytes_n=guidance["byte_size"],
        r19_record_sha=r19_record_sha, r16_record_sha=r16_record_sha,
        dev_ref=dev_ref, axis_ref=axis_ref, run19_ref=run19_ref,
        run16_ref=run16_ref, dev20_fam=dev20_fam, witness_sha=witness_sha,
        protocol_sha=protocol_sha, png_checks=png_checks)
    rebuild.pop("_verification_note", None)
    if hashing.canonical_json_bytes(rebuild) != record_bytes:
        _fail("同参重建不一致（byte-exact 破坏）: r22-prep-record")

    # ---- 防覆写守卫 + 落盘（唯一写入目标=RECORD；指引零写入）----
    if RECORD.exists():
        if RECORD.read_bytes() != record_bytes:
            _fail("r22-prep-record.json 已存在且重建字节不一致（防覆写；拒"
                  "绝覆写）")
        print("[r22-prep] 重跑自证：r22-prep-record.json 重建字节与既有文"
              "件逐字节一致（幂等通过，零覆写）")
    else:
        RECORD.write_bytes(record_bytes)
        if RECORD.read_bytes() != record_bytes:
            _fail("回读不一致: r22-prep-record.json")

    # ---- 汇总打印 ----
    print("[r22-prep] 验证通过：observation-guidance-r19.md 基座锚 "
          f"{GUIDANCE_R19_SHA_PREFIX} OK（sha256={guidance19_sha}，只读零写"
          f"入，{guidance['byte_size']} B，不新建指引文件；落盘事实锚 "
          f"R19T-×4/R19B-×1/无 §5B/(iii-a)×3）；r19-prep-record 结构血统锚 "
          f"{R19_PREP_RECORD_SHA_PREFIX} OK（24 键镜像源）；r16-prep-record "
          f"同指引重复轮先例锚 {R16_PREP_RECORD_SHA_PREFIX} OK；"
          f"round20-dev-record 授权锚 {DEV_RECORD_R20_SHA_PREFIX} OK"
          f"（targets[0] R21 不做+三重独立依据+收益最大配置=轴3；targets[1]"
          f" 同指引重复轮候选+收敛归因+0.09064）；axis-plan 冻结锚 "
          f"{AXIS_PLAN_SHA_PREFIX} OK（R21 全组合槽位冻结原文+守门 "
          f"G1/G2/G3+用户指令原文）；run-r19 判据锚 {RUN_R19_SHA_PREFIX} OK"
          f"（M1=18/39=0.461538、M2=4/7=0.571429、M3=4、M4=0.211111、"
          f"contact=4、三族 4/4/14、援引 6+2 与 10/12、G1/G2 维持、"
          f"verdict=marginal）；run-r16 基线锚 {RUN_R16_SHA_PREFIX} OK"
          f"（M1=0.771429、guard_ok=True）；witness-r14b 锚 "
          f"{WITNESS_R14B_SHA_PREFIX} OK；evaluation-protocol-v1 在盘锚 "
          f"{EVAL_PROTOCOL_V1_SHA_PREFIX} OK")
    print("[r22-prep] 判据数值自洽断言：0.771429−0.461538=0.309891；"
          "0.862069−0.771429=0.09064；replicated 带=0.461538±0.10="
          "[0.361538, 0.561538]；0.211111−0.20=0.011111——全部 PASS")
    print("[r22-prep] 渲染零变更自证（四 PNG 实测=witness 登记值；字节复"
          "用、零仪器变更）：")
    for p in png_checks:
        print(f"  {p['state_side']}: {p['sha256_measured']} "
              f"(witness {p['witness_key']} 逐字相符)")
    print("[r22-prep] hypothesis_test 逐字断言链：预注册判据原文文本 → "
          "json.loads → 常量 → 记录字段，三层相等 PASS（三支 replicated/"
          "drifted/regressed+M4 第二轮样本单列+机制观察单列；"
          "descriptive_boundary_note 照抄 r19 血统原文）")
    print(f"[r22-prep] 跳号声明核对：r21 号段=axis-plan 冻结 R21 全组合位"
          f"（ii_full_combination 条件轮未触发）+dev-r20 targets[0]「R21 不"
          f"做」三重独立依据在案；r22=时序下一轮、与该 R21 无涉——已写入 "
          f"round_nature PASS")
    print(f"[r22-prep] changed_variables=0 核对：指引字节复用（8633bda5）+"
          f"渲染字节复用（r14b 四 PNG）+GT/阈值/协议零变更+唯一实验操作="
          f"实例群重抽——changed_variables==[] PASS（前缀差异登记：§6 示例 "
          f"R19T-/R19B- 落盘原文、派发层覆盖 R22T/R22B、r16 先例）")
    print(f"[r22-prep] 顶层键镜像断言：与 r19-prep-record 逐键一致 PASS"
          f"（{len(record)} 键）")
    print(f"[r22-prep] 工件 sha256：observation-guidance-r19.md（零写入复"
          f"核）={_sha(GUIDANCE_R19)}")
    print(f"[r22-prep] 工件 sha256：r22-prep-record.json={_sha(RECORD)}")


if __name__ == "__main__":
    main()
