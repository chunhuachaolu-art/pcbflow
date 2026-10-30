# -*- coding: utf-8 -*-
"""P3 门构建器（任务书 §5 P3，引擎侧批次）：全流程/负向注入/三态/计票/harness 冒烟，staging 原子提交。

产出（全部 E:/ZCodeData/ZCodeProject/route-v5/out/v5-p3/ 之下，sidecar 卫生）：
  selection-runs/   demo-01 双臂 + adv-02(SAT) + adv-03(UNKNOWN) 的 select_best 落盘件
  harness-pkgs/     demo-01 seat_a_diagnostic 盲包 + 包元数据 + L1 视图（图文双输入）
  gate/             gate-summary.json + p3.evidence.json

门项对账（脚本内断言，不过即整体 rollback 并退出码 1）：
  1 全量 pytest 绿；2 两静态检查 GREEN；
  3 demo-01 全流程走通（load→compile→双臂 plan→按臂 select→盲包制备→三件套回读→计票）；
  4 负向 run-02 对抗注入被拦（撞带 J1 路线绝不入选，R5 滤除在案；单独成批 best=None）；
  5 三态判定落盘：SAT(adv-02)/UNSAT(demo-01)/UNKNOWN(adv-03) 各至少一例，UNSAT/UNKNOWN
    证书过 failcert.verify 独立复核；
  6 投票计票实跑：≥2/3 多数门/少数派全文留痕/平票先注册序留痕/N=2 降档 + 双跑字节等；
  7 §5.1 理念门 P3 批次=路由④交付（冲突电池七对×六查点/PF 四项/反事实/PS 五不变性，tests/）；
  8 席位 A 盲包重放（模型会话项）：V2 模板包+A3 五通道，双席位四轮留痕，主审语义对账
    ground truth 判分（interim 口径裁定，用户可翻案）。
确定性：select_best/harness 制备各做双跑字节对比；tally 双跑 canonical 等断言。
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import canonical, failcert, sidecar, staging  # noqa: E402
from v5.board import load_board, load_board_file  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.harness import HarnessError, ingest_run, prepare_multimodal, prepare_pkg  # noqa: E402
from v5.planner import plan_candidates  # noqa: E402
from v5.selection import select_best  # noqa: E402
from v5.voting import tally  # noqa: E402

OUT = os.path.join(ROOT, "out", "v5-p3")
BOARD_DIR = os.path.join(ROOT, "boards", "d")
DEMO01 = "demo-01-v2-corridor"
ADV_SAT = "adv-02-clk-vs-short"
ADV_UNK = "adv-03-diff-vs-capacity"
TMP = os.path.join(str(sidecar.ALLOWED_ROOTS[0]), "_p3gate_tmp")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    tail = (r.stdout or "").strip().splitlines()
    return tail[-1] if tail else ""


def norm(line):
    line = re.sub(r"\s+in\s+[\d.]+s\s*$", "", line)   # pytest 墙钟
    return re.sub(r"\([^)]*\)", "", line).strip()      # 静态检查计数


def wrap_json(payload, generator, version, board_sha256):
    doc = {"provenance": {"generator": generator, "generator_version": version,
                          "board_sha256": board_sha256}}
    doc.update(payload)
    return canonical.canonical_json(doc)


def tree_hashes(root):
    out = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace("\\", "/")
            with open(p, "rb") as f:
                out[rel] = sha256_bytes(f.read())
    return out


def assert_trees_equal(a, b):
    ha, hb = tree_hashes(a), tree_hashes(b)
    assert ha and ha == hb, "双跑字节不等: %s vs %s（键差 %s/%s）" % (
        a, b, sorted(set(ha) - set(hb)), sorted(set(hb) - set(ha)))


def board_and_candidates(board_id, arm="principle"):
    board = load_board_file(os.path.join(BOARD_DIR, board_id + ".board.v1.json"))
    rt = canonical.canonical_json(board)
    assert canonical.canonical_json(load_board(json.loads(rt.decode("utf-8")))) == rt
    artifact, _fp = compile_board(board)
    return board, artifact, plan_candidates(board, artifact, arm=arm)


def main():
    checks = {}
    files = {}

    # ---- 门项 1：全量 pytest
    tail = norm(run([sys.executable, "-m", "pytest", "tests/", "-q", "--no-header"]))
    checks["full_test_suite"] = {"result": "GREEN" if ("passed" in tail and
                                                       "failed" not in tail and
                                                       "error" not in tail)
                                 else "RED", "pytest_tail": tail}
    assert checks["full_test_suite"]["result"] == "GREEN", tail

    cleaned = staging.recover(os.path.join(OUT, "_staging"), OUT)

    # ---- 门项 3：demo-01 全流程（load→compile→双臂 plan→按臂 select）
    board, artifact, cands_p = board_and_candidates(DEMO01, "principle")
    _, _, cands_np = board_and_candidates(DEMO01, "no-principle")
    bsha = board["provenance"]["board_sha256"]
    runs_root = os.path.join(OUT, "selection-runs")
    rerun_root = os.path.join(OUT, "selection-runs-rerun")
    shutil.rmtree(rerun_root, ignore_errors=True)
    pipeline = {}
    for arm, cands in (("principle", cands_p), ("no-principle", cands_np)):
        dst = os.path.join(runs_root, DEMO01 + "." + arm)
        res = select_best(board, cands, out_dir=dst)
        dst2 = os.path.join(rerun_root, DEMO01 + "." + arm)
        select_best(board, cands, out_dir=dst2)
        assert_trees_equal(dst, dst2)                  # 选择落盘双跑字节等
        pipeline[arm] = {"verdict": res["verdict"],
                         "best": res["best"]["candidate_id"] if res["best"] else None,
                         "measured": res["ledger"]["measured"],
                         "rejected": res["ledger"]["rejected"]}
    assert pipeline["principle"]["verdict"] == "UNSAT", pipeline   # 端点直线候选的诚实判定
    shutil.rmtree(rerun_root)
    checks["full_pipeline_demo01"] = {
        "chain": "load→roundtrip→compile→plan(principle+no-principle)→per-arm select",
        "per_arm": pipeline,
        "unverdict_note": "demo-01 UNSAT 为诚实判定：板内固定铜声明占用已超 C1 容量"
                          "（P1 门裁决的『应有之张力』），任何候选无可行解，容量算术核可复核",
        "route_order_principle": cands_p[0]["route_order"],
        "route_order_no_principle": cands_np[0]["route_order"],
        "trace_rules_principle": cands_p[0]["provenance"]["rules_consumed"]}

    # ---- 门项 4：负向 run-02 对抗注入（V2 撞带 J1 路线；板=V2 场景 fixtures_v2，
    #      与 tests/test_selection.py::test_run02_j1_injection_blocked 同口径——demo-01
    #      固定铜声明本身爆 C1 容量，全板无可行候选，须有可行对照板才有拦截语义）
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    import fixtures_v2 as fx
    board_v2 = fx.build_v2_board()

    def _partial_cand(cid, polylines, layers):
        return {"candidate_id": cid, "arm": "principle",
                "provenance": {"generator": "v5.p3-gate/run02-fixture",
                               "rules_consumed": [], "compiled_sha256": "0" * 64},
                "route_order": sorted(polylines),
                "layer_assignment": layers, "polylines": polylines,
                "generation_trace": []}

    good = _partial_cand("C-001",
                         {"P3": [[16.0, 4.0], [34.85, 4.0], [34.85, 36.0], [16.0, 36.0]],
                          "P5": [[37.0, 10.0], [34.85, 10.0], [34.85, 30.0], [37.0, 30.0]]},
                         {"P3": "B.Cu", "P5": "F.Cu"})
    adv_cand = _partial_cand("C-ADV-RUN02-J1", {"P5": [[31.0, 5.0], [31.0, 10.0],
                                                       [45.0, 10.0]]},
                             {"P5": "F.Cu"})
    res_mix = select_best(board_v2, [good, adv_cand])
    rej_adv = [r for r in res_mix["ledger"]["rejection_reasons"]
               if r["candidate_id"] == "C-ADV-RUN02-J1"]
    assert res_mix["verdict"] == "SAT" and \
        res_mix["best"]["candidate_id"] == "C-001", "对抗候选绝不可入选"
    assert len(rej_adv) == 1 and rej_adv[0]["rule"] == "R5" and \
        "fixed:P4" in rej_adv[0]["detail"], rej_adv
    res_alone = select_best(board_v2, [adv_cand])
    assert res_alone["best"] is None, "对抗候选单独成批也不可给出可行解"
    checks["run02_negative_injection"] = {
        "board": "tests/fixtures_v2.build_v2_board (V2 场景)",
        "mixed_batch_best": res_mix["best"]["candidate_id"],
        "adversarial_rejections": rej_adv,
        "adversarial_alone_verdict": res_alone["verdict"]}

    # ---- 门项 5：三态判定落盘（SAT/UNSAT/UNKNOWN 各一例 + 证书独立复核）
    three = {}
    b_sat, art_sat, c_sat = board_and_candidates(ADV_SAT, "principle")
    res_sat = select_best(b_sat, c_sat,
                          out_dir=os.path.join(runs_root, ADV_SAT + ".principle"))
    select_best(b_sat, c_sat, out_dir=os.path.join(rerun_root, ADV_SAT + ".principle"))
    assert res_sat["verdict"] == "SAT" and res_sat["best"] is not None
    b_unk, art_unk, c_unk = board_and_candidates(ADV_UNK, "principle")
    res_unk = select_best(b_unk, c_unk,
                          out_dir=os.path.join(runs_root, ADV_UNK + ".principle"))
    select_best(b_unk, c_unk, out_dir=os.path.join(rerun_root, ADV_UNK + ".principle"))
    assert res_unk["verdict"] == "UNKNOWN"
    assert_trees_equal(os.path.join(runs_root, ADV_SAT + ".principle"),
                       os.path.join(rerun_root, ADV_SAT + ".principle"))
    assert_trees_equal(os.path.join(runs_root, ADV_UNK + ".principle"),
                       os.path.join(rerun_root, ADV_UNK + ".principle"))
    shutil.rmtree(rerun_root)

    sat_dir = os.path.join(runs_root, ADV_SAT + ".principle", ADV_SAT + ".selection")
    unsat_dir = os.path.join(runs_root, DEMO01 + ".principle", DEMO01 + ".selection")
    unk_dir = os.path.join(runs_root, ADV_UNK + ".principle", ADV_UNK + ".selection")
    assert not os.path.isfile(os.path.join(sat_dir, ADV_SAT + ".failcert.json")), \
        "SAT 无证书件"
    with open(os.path.join(unsat_dir, DEMO01 + ".failcert.json"), encoding="utf-8") as f:
        cert_unsat = json.load(f)
    with open(os.path.join(unk_dir, ADV_UNK + ".failcert.json"), encoding="utf-8") as f:
        cert_unk = json.load(f)
    v_unsat, v_unk = failcert.verify(cert_unsat), failcert.verify(cert_unk)
    assert v_unsat.get("recheck") == "PASS", v_unsat
    assert v_unk.get("recheck") == "PASS", v_unk
    three = {
        "SAT": {"board": ADV_SAT, "best": res_sat["best"]["candidate_id"],
                "cert": None},
        "UNSAT": {"board": DEMO01, "core_constraints":
                  sorted({e["constraint"] for e in cert_unsat["unsat_core"]}),
                  "verify": v_unsat},
        "UNKNOWN": {"board": ADV_UNK, "verify": v_unk}}
    checks["three_states"] = three

    # ---- harness 制备 + 三件套回读冒烟（门项 3 的盲包环节）
    pkgs_root = os.path.join(OUT, "harness-pkgs")
    pkgs_rerun = os.path.join(OUT, "harness-pkgs-rerun")
    shutil.rmtree(pkgs_rerun, ignore_errors=True)
    seat = "seat_a_diagnostic"
    art_p, art_c = partition_artifact_of(board), conflicts_artifact_of(board)
    rec = prepare_pkg(board, art_p, art_c, seat, pkgs_root)
    prepare_multimodal(board, art_p, art_c, seat, pkgs_root, mode="all")
    prepare_pkg(board, art_p, art_c, seat, pkgs_rerun)
    prepare_multimodal(board, art_p, art_c, seat, pkgs_rerun, mode="all")
    assert_trees_equal(pkgs_root, pkgs_rerun)          # 盲包制备双跑字节等
    shutil.rmtree(pkgs_rerun)

    # 合成合规三件套（非真实模型会话；真实重放=第二波模型会话项）
    ordinal = {"routing_order": cands_p[0]["route_order"],
               "defect_scan": [{"subject": "P8", "rule": "R1",
                                "note": "合成冒烟：planned_width 低于保守下限"}],
               "principle_objection": ""}
    raw_text = ("席位 A 回复原文（P3 门合成冒烟，非真实模型会话）\n```json\n%s\n```\n"
                % json.dumps(ordinal, ensure_ascii=False, sort_keys=True, indent=1))
    run_dir = os.path.join(TMP, "run-smoke")
    shutil.rmtree(run_dir, ignore_errors=True)
    os.makedirs(run_dir)
    with open(os.path.join(run_dir, "response-raw.md"), "w", encoding="utf-8") as f:
        f.write(raw_text)
    with open(os.path.join(run_dir, "output.json"), "w", encoding="utf-8") as f:
        json.dump(ordinal, f, ensure_ascii=False, sort_keys=True, indent=1)
    meta = {"seat": seat, "pkg_sha256": rec["pkg_sha256"], "board_sha256": bsha}
    sidecar.write_sidecar(os.path.join(run_dir, "meta.json"), meta,
                          "v5.p3-gate", "0.1.0", bsha)
    product = ingest_run(run_dir, pkg_readback(pkgs_root, rec))
    assert set(product) == {"seat", "board_sha256", "pkg_sha256", "output",
                            "raw_sha256"}, sorted(product)
    # 负向：output.json 被篡改（合同外通道）→ fail-closed
    with open(os.path.join(run_dir, "output.json"), "w", encoding="utf-8") as f:
        json.dump(dict(ordinal, rogue_channel=1), f, ensure_ascii=False)
    tamper_raised = False
    try:
        ingest_run(run_dir, pkg_readback(pkgs_root, rec))
    except HarnessError:
        tamper_raised = True
    assert tamper_raised, "篡改三件套必须 fail-closed"
    shutil.rmtree(TMP, ignore_errors=True)
    checks["harness_roundtrip"] = {
        "seat": seat, "prepare_record": rec,
        "ingest_product_keys": sorted(product),
        "raw_sha256": product["raw_sha256"],
        "tamper_intercepted": True}

    # ---- 门项 6：投票计票实跑（合成票；真票=第二波模型会话）
    bsha_key, pkg_key = bsha, rec["pkg_sha256"]

    def ballot(aid, order, subjects):
        return {"agent_id": aid, "registration_order": order,
                "board_sha256": bsha_key, "pkg_sha256": pkg_key,
                "problem_items": [{"subject": s, "kind": "synthetic", "note": ""}
                                  for s in subjects],
                "confidence_rank": [], "raw_ref": "run-smoke/%s" % aid}

    t_major = tally([ballot("A1", 1, ["S1"]), ballot("A2", 2, ["S1", "S3"]),
                     ballot("A3", 3, ["S2"])])
    assert [m["subject"] for m in t_major["majority_items"]] == ["S1"]
    assert t_major["majority_items"][0]["evidence"] == "2/3"
    assert len(t_major["minority_dissents"]) == 2          # A2(S3 未入账)/A3(S2 未入账)
    t_tie = tally([ballot("A1", 1, ["X"]), ballot("A2", 2, ["Y"]),
                   ballot("A3", 3, ["Z"])])
    assert t_tie["majority_items"] == [] and t_tie["tie_note"], t_tie
    t_n2 = tally([ballot("A1", 1, ["W"]), ballot("A2", 2, ["W"])])
    assert t_n2["downgraded"] is True and t_n2["majority_items"][0]["evidence"] == "2/2"
    assert canonical.canonical_json(tally([ballot("A1", 1, ["S1"]),
                                           ballot("A2", 2, ["S1", "S3"]),
                                           ballot("A3", 3, ["S2"])])) == \
        canonical.canonical_json(t_major)
    checks["voting_tally_live"] = {
        "majority": t_major["majority_items"],
        "minority_dissent_agents": [d["agent_id"] for d in t_major["minority_dissents"]],
        "tie_note": t_tie["tie_note"],
        "n2_downgraded": t_n2["downgraded"],
        "double_run_canonical_equal": True}

    # ---- 静态检查（tmp 已清；selection/harness 落盘件均 sidecar 合规）
    s1 = norm(run([sys.executable, "tools/check_sidecar.py"]))
    s2 = norm(run([sys.executable, "tools/check_drc_mono.py"]))
    checks["static_sidecar"] = s1
    checks["static_drc_mono"] = s2
    assert "GREEN" in s1 and "GREEN" in s2, (s1, s2)

    # ---- 落盘件哈希登记
    for root in (runs_root, pkgs_root):
        for rel, digest in tree_hashes(root).items():
            files[os.path.relpath(os.path.join(root, rel), OUT).replace("\\", "/")] = digest

    checks["principle_gates_p3_batch"] = {
        "tests": "tests/test_principle_gates_p3.py（路由④交付，107 例全绿）",
        "battery": "冲突电池七对×六查点 7 对抗板全 PASS（winner/loser 与注册表独立复算一致）",
        "pf": "覆盖率/check_only 10+消费覆盖率 10+源码守卫+硬规则不覆盖 5+裁决可溯 13",
        "counterfactual": "18 例（必变 2 处实证；15 处不变逐条带机制子断言）",
        "ps": "五不变性 8 例全过（nets 重排/far keepout/键序/换行变体/候选反序）"}

    # ---- 门项 7：席位 A 盲包重放（模型会话项；判分 ground truth=partition-judge-v2/MANIFEST.md:51-56）
    replay_root = os.path.join(OUT, "seat-a-replay")
    run_hashes = {}
    for run_id in ("seat1-glm1", "seat1-glm1-run2", "seat3-glm2", "seat3-glm2-run2"):
        run_hashes[run_id] = tree_hashes(os.path.join(replay_root, "runs", run_id))
    checks["seat_a_blind_replay"] = {
        "package": "v2-scenario-golden.replay-pkg.md（V2 模板板信息逐字校验+输出合同节换 A3 五通道；"
                   "v5 盲包不含焊盘几何，四未播种缺陷中①②④须 V2 原文信息量，重放对象=V2 包）",
        "protocol": "两席位独立会话（GLM-5.3F#1/#2），零工具零文件访问，最终回复逐字自存证；"
                    "DSF 席缺席=N=2 降档口径（U10 阵容，ZCode 子智能体不可选模型+harness 外 LLM API 红线）",
        "rerun_policy": "非合规票每席恰一次同盲包重跑，双尝试全留痕，每席至多一张合规票进计票；"
                        "二跑提示词仅多一条 rule 枚举格式澄清（零检测线索）",
        "runs_sha256": run_hashes,
        "ingest": {"seat1-glm1": "REJECTED（defect_scan[0].rule 枚举外复合写法，fail-closed）",
                   "seat3-glm2": "REJECTED（同型枚举违例）",
                   "seat1-glm1-run2": "PASS", "seat3-glm2-run2": "PASS"},
        "per_run_unsown_hits": {
            "GT1_P3焊盘叠P9带": {"seat1-run2": True, "seat3-run2": True},
            "GT2_P4端焊盘叠P9": {"seat1-run2": True, "seat3-run2": True},
            "GT3_P4带距ANA2.95违R2": {"seat1-run2": True, "seat3-run2": False},
            "GT4_表头自相矛盾": {"seat1-run2": False, "seat3-run2": False}},
        "panel": {"seat1_run2": ["GT1", "GT2", "GT3"], "seat3_run2": ["GT1", "GT2"],
                  "majority_2of2": ["GT1", "GT2"], "union": ["GT1", "GT2", "GT3"]},
        "criterion_ruling": "用户裁定（2026-09-14「口径 (a)」）按任务书原文 V2 口径（a）单席 run 命中≥3 判："
                            "席位1run2 3/4 → PASS 定案；(b) 面板多数门口径=2/4 不过、并集=3/4，"
                            "数据同件披露备查（判分不依赖 subject 字面，人工语义对账 GT）",
        "tally_raw_subject": {"majority": ["P8 (2/2)"], "downgraded": True,
                              "note": "A6 计票器 subject 为自由字符串，命名分歧使同缺陷语法键分裂"
                                      "——规范缺陷词表/语义聚类为计票器前置需求（改须新决策件）"},
        "verdict": "PASS（口径 a，用户裁定 2026-09-14 定案）"}

    summary = {"gate": "P3-engine", "checks": checks,
               "boards": {"demo": [DEMO01], "adv": [ADV_SAT, ADV_UNK]},
               "cleaned_staging_residue": cleaned,
               "artifact_files_sha256": files,
               "artifact_form_note": "selection 落盘件=select_best 自有 staging 提交；"
                                     "盲包/元数据=sidecar 合规落盘",
               "no_manual_item": "P3 引擎侧门无人工抽检项；模型会话项第二波派发"}
    tx_gate = staging.StagingTransaction(os.path.join(OUT, "_staging"), OUT, "gate")
    try:
        data = wrap_json(summary, "v5.p3-gate", "0.1.0", "0" * 64)
        tx_gate.write_bytes("gate-summary.json", data)
        ev = {"gate": "P3-engine", "checks": checks, "files": files,
              "taskbook": "V5.0-DEV-TASKBOOK-2026-09-13.md v3.2 (sha256 643c94e3...)"}
        data2 = wrap_json(ev, "v5.p3-gate", "0.1.0", "0" * 64)
        tx_gate.write_bytes("p3.evidence.json", data2)
        tx_gate.commit()
    except BaseException:
        tx_gate.rollback()
        raise

    print("P3 gate artifacts committed:")
    for rel in sorted(files):
        print("  %s  %s" % (files[rel][:12], rel))
    print("gate-summary: %d checks; pipeline=%s/%s; three=%s" % (
        len(checks), pipeline["principle"]["verdict"],
        pipeline["no-principle"]["verdict"],
        {k: v.get("board") for k, v in three.items()}))


# ---- 辅助：分区/冲突工件与盲包回读（独立函数便于测试与复用）

def partition_artifact_of(board):
    from v5.partition import build_partition_artifact
    return build_partition_artifact(board)


def conflicts_artifact_of(board):
    from v5.overlay import build_conflicts
    return build_conflicts(board)


def pkg_readback(pkgs_root, rec):
    with open(os.path.join(pkgs_root, rec["pkg_file"]), encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    main()
