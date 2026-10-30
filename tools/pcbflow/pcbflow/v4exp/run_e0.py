"""E0 编排入口（50 场景全量 checks + f1 场景 8 种突变 + 正向对照）。

stdin: {"out_dir": "out/v4-experiment/e0", "source_dir": "out/v4-experiment"}
（两键均可省，取默认值；相对路径。）

写：
- <out_dir>/e0-results.json
    {schema:"pcbflow.v4exp.e0-results/1",
     summary:{scenarios, checks_run, checks_passed, checks_failed,
              mutations_run, mutations_blocked, positive_controls_passed,
              overall:"pass|fail"},
     per_scenario:[{scenario_id, checks:{name:{check,pass,reason}},
                    mutations:[{mutation, expected, observed, pass}]}]}
- <out_dir>/replay-check-e0.json
    同一输入跑两遍 compute_results，e0-results.json 文本逐字节一致性结论
    （不含时间戳、不含主机绝对路径）。

门判定硬编码（实验方案 §4.3，不放宽）：
  - 合法 SVG 身份恢复 100%；
  - manifest 与 SVG 全字段一致；
  - round-trip <= 0.001mm；
  - 突变 100% blocked；
  - 8a 正向对照必须 facts 不变；
  - 任一 fail => overall = "fail"。

零子进程、零 argv、零 wall-clock、零网络。
"""

from __future__ import annotations

import hashlib
import json
import os

from . import e0_checks, e0_mutate, e0_parse, model

RESULTS_SCHEMA = "pcbflow.v4exp.e0-results/1"
REPLAY_SCHEMA = "pcbflow.v4exp.e0-replay-check/1"
DEFAULT_SOURCE_DIR = "out/v4-experiment"
DEFAULT_OUT_DIR = "out/v4-experiment/e0"
MUTATION_FAMILY = "f1"

MACHINE_CHECK_NAMES = ("identity_recovery", "manifest_svg_consistency",
                       "roundtrip_mm", "hash_binding", "color_independence")
ALL_CHECK_NAMES = MACHINE_CHECK_NAMES + ("resolution_invariance",)
POSITIVE = e0_mutate.POSITIVE_MUTATION


def _load_scenario(source_dir: str, sid: str) -> tuple:
    board_obj = model.read_json(
        os.path.join(source_dir, f"board-snapshot-{sid}.json"))
    manifest = model.read_json(
        os.path.join(source_dir, f"route-manifest-{sid}.json"))
    svg_path = os.path.join(source_dir, f"route-preview-{sid}.svg")
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_text = f.read()
    return board_obj, manifest, svg_text


def _mutation_rows(svg_text: str, manifest: dict, board_obj: dict,
                   original_facts: dict) -> list:
    rows = []
    for name in e0_mutate.ALL_MUTATIONS:
        mutated = e0_mutate.apply_mutation(name, svg_text, manifest)
        if name == POSITIVE:
            # 正向对照：facts 必须与原版逐字段相等；颜色重写用原始 SVG 做基底
            verdict = e0_mutate.evaluate_mutation(
                mutated, manifest, board_obj, original_facts=original_facts,
                original_svg=svg_text)
            expected = "pass"
        else:
            verdict = e0_mutate.evaluate_mutation(
                mutated, manifest, board_obj)
            expected = "blocked"
        observed = "blocked" if verdict["blocked"] else "pass"
        rows.append({
            "mutation": name,
            "expected": expected,
            "observed": observed,
            "pass": observed == expected,
        })
    return rows


def run_scenario(sid: str, family: str, source_dir: str) -> dict:
    """单场景：6 项 checks；f1 场景另跑全部突变。"""
    board_obj, manifest, svg_text = _load_scenario(source_dir, sid)
    facts, reason = e0_parse.try_parse_svg(svg_text)
    checks = {}
    if facts is None:
        for name in ALL_CHECK_NAMES:
            checks[name] = e0_checks.result(
                name, False, f"SVG 严格解析失败: {reason}")
        if family == MUTATION_FAMILY:
            mutations = []
            for name in e0_mutate.ALL_MUTATIONS:
                mutations.append({
                    "mutation": name,
                    "expected": "pass" if name == POSITIVE else "blocked",
                    "observed": "not_run",
                    "pass": False})
        else:
            mutations = []
    else:
        bbox = board_obj["board"]["bbox_mm"]
        for c in (e0_checks.identity_recovery(facts, manifest),
                  e0_checks.manifest_svg_consistency(facts, manifest, bbox),
                  e0_checks.roundtrip_mm(facts, manifest, bbox),
                  e0_checks.hash_binding(facts, manifest, board_obj),
                  e0_checks.color_independence(svg_text, facts)):
            checks[c["check"]] = c
        checks["resolution_invariance"] = e0_checks.resolution_invariance(
            sid, manifest, bbox, source_dir)
        mutations = _mutation_rows(svg_text, manifest, board_obj, facts) \
            if family == MUTATION_FAMILY else []
    return {"scenario_id": sid, "checks": checks, "mutations": mutations}


def overall_from(per_scenario: list) -> str:
    """门判定（硬编码，实验方案 §4.3，不得放宽）。任一 fail => "fail"。"""
    # 1) 每项机器检查在全部场景必须通过（含身份恢复 100%、一致、
    #    roundtrip<=0.001mm、hash 绑定、颜色独立、分辨率无关）
    for name in ALL_CHECK_NAMES:
        for entry in per_scenario:
            if not entry["checks"].get(name, {}).get("pass", False):
                return "fail"
    # 2) 负向突变 100% blocked
    neg_run = 0
    neg_blocked = 0
    pos_total = 0
    pos_passed = 0
    for entry in per_scenario:
        for row in entry["mutations"]:
            if row["mutation"] == POSITIVE:
                pos_total += 1
                pos_passed += 1 if row["pass"] else 0
            else:
                neg_run += 1
                neg_blocked += 1 if row["pass"] else 0
    if neg_blocked != neg_run or neg_run == 0:
        return "fail"
    # 3) 正向对照（8a）必须全部通过且 facts 不变
    if pos_total == 0 or pos_passed != pos_total:
        return "fail"
    return "pass"


def compute_results(cfg: dict) -> dict:
    """纯函数：同输入同结果（双跑字节一致的依据）。"""
    source_dir = cfg.get("source_dir") or DEFAULT_SOURCE_DIR
    sman = model.read_json(os.path.join(source_dir, "scenario-manifest.json"))
    scenarios = sorted(sman["scenarios"], key=lambda s: s["scenario_id"])
    per_scenario = [
        run_scenario(s["scenario_id"], s["family"], source_dir)
        for s in scenarios]

    checks_run = 0
    checks_passed = 0
    mutations_run = 0
    mutations_blocked = 0
    positives_passed = 0
    for entry in per_scenario:
        for c in entry["checks"].values():
            checks_run += 1
            checks_passed += 1 if c["pass"] else 0
        for row in entry["mutations"]:
            if row["mutation"] == POSITIVE:
                positives_passed += 1 if row["pass"] else 0
            else:
                mutations_run += 1
                mutations_blocked += 1 if row["pass"] else 0

    return {
        "schema": RESULTS_SCHEMA,
        "summary": {
            "scenarios": len(per_scenario),
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "checks_failed": checks_run - checks_passed,
            "mutations_run": mutations_run,
            "mutations_blocked": mutations_blocked,
            "positive_controls_passed": positives_passed,
            "overall": overall_from(per_scenario),
        },
        "per_scenario": per_scenario,
    }


def _results_text(results: dict) -> str:
    return json.dumps(results, ensure_ascii=False, indent=2) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main_read(cfg: dict) -> dict:
    """从 cfg（而非 stdin）执行完整 E0：同输入跑两遍 + 落盘两个产物。"""
    out_dir = cfg.get("out_dir") or DEFAULT_OUT_DIR
    source_dir = cfg.get("source_dir") or DEFAULT_SOURCE_DIR

    # 同一输入跑两遍，逐字节一致性是 E0 的重放硬门
    text1 = _results_text(compute_results({"source_dir": source_dir}))
    text2 = _results_text(compute_results({"source_dir": source_dir}))
    identical = text1 == text2

    os.makedirs(out_dir, exist_ok=True)
    results_path = os.path.join(out_dir, "e0-results.json")
    with open(results_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text1)
    replay_path = os.path.join(out_dir, "replay-check-e0.json")
    summary = json.loads(text1)["summary"]
    replay = {
        "schema": REPLAY_SCHEMA,
        "subject": "e0-results.json",
        "double_run_identical": identical,
        "results_sha256_run1": _sha256_text(text1),
        "results_sha256_run2": _sha256_text(text2),
        "scenarios": summary["scenarios"],
        "overall_run1": summary["overall"],
        "overall_run2": json.loads(text2)["summary"]["overall"],
    }
    model.write_json(replay_path, replay)
    return {
        "results": results_path.replace("\\", "/"),
        "replay": replay_path.replace("\\", "/"),
        "double_run_identical": identical,
        "summary": summary,
    }


def main() -> None:
    cfg = model.read_stdin_json()
    info = main_read(cfg)
    import sys
    sys.stdout.write(json.dumps(info, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
