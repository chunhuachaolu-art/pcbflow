"""S17 会话测试：run-r2 advisory 扩样管线就绪（TL-2）。

覆盖：
- select_train_boards（纯函数）：确定性 slug 升序、排除已渲染集、
  非 train 不入选、count 不足 fail-closed、record 键非法/重复
  profile_id fail-closed、常量选板规则文档在案；
- 集成锚（只读 out/）：
  * board-selection.json：规则=critic_batch.SELECTION_RULE_R2、选中
    4 板=pichen train 论域 slug 升序前 4（排除 launchxl）、无 holdout；
  * render-manifest.json：visual_check=pending（observe 未做，红线：
    本包不读图）、4 板×顶/底渲染 hash 对盘上实文件一致、观察维度
    提示在案且 allowed 类别口径不变（manifest 不含新类别枚举）；
  * ingest-selfcheck-synthetic.json：synthetic=true、validate/ingest
    全链 pass、executed+blocked→enqueue ITEM-run-r2（设计行为）、
    pending_handoff 三步在案；
- 纯内存合成 ingest 链（不落盘、零真实读取）：合成 mini bundle +
  合成 raw-flags（reader_id 显式标 synthetic）→ validate_raw_flags
  + ingest_run → blocked→enqueue（复验自检结论可重放）；
- datasets/ 只读复核：选中板 raw 文件 hash 与 manifest source 声明
  一致（byte 口径）；
- observe/bundle/ingest 子命令（tmp_path 自造 mini fixture，不动 out/
  真实产物）：
  * observe 键校验（missing/extra 都拒）、空观感拒、渲染漂移拒、
    写 visual_check=done+canonical 落盘、已 done 防覆写拒；
  * bundle：pending 拒、canonical byte-exact 往复、sidecar 同值、
    calibration_domain_established=False、staging 清理无残留、防覆写；
  * ingest：修复分支（as-returned 不可解析→纯单点插入，difflib 守卫、
    as-returned 留证、provenance 绑定、enqueue ITEM-run-r2 同口径）+
    no_repair 分支（可解析→canonical 化内容零改动）+ 不可纯插入修复
    拒收 fail-closed + raw-flags.json 防覆写。
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import s17_run_r2 as s17  # noqa: E402
from pcbflow import critic, critic_batch as cb  # noqa: E402
from pcbflow import critic_run, hashing, queue  # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")


# ---------------------------------------------------------------------------
# 纯函数：select_train_boards
# ---------------------------------------------------------------------------

def _rec(pid, split="train"):
    return {"profile_id": pid, "split": split,
            "split_basis": "manifest dataset_splits", "source_rel":
            f"datasets/x/raw/{pid}/raw.kicad_pcb"}


def test_select_train_boards_deterministic():
    recs = [_rec("pcbench-z-board"), _rec("pcbench-a-board"),
            _rec("pcbench-launchxl-f28027-isolation-pcb-project1"),
            _rec("pcbench-m-holdout", split="holdout"),
            _rec("pcbench-b-board")]
    got = cb.select_train_boards(recs, count=3)
    # slug 升序前 3；launchxl（已渲染排除集）与 holdout 不入选
    assert [r["profile_id"] for r in got] == [
        "pcbench-a-board", "pcbench-b-board", "pcbench-z-board"]
    assert all(r["split"] == "train" for r in got)


def test_select_train_boards_insufficient_and_invalid():
    recs = [_rec("pcbench-a-board")]
    with pytest.raises(ValueError):
        cb.select_train_boards(recs, count=2)
    with pytest.raises(ValueError):
        cb.select_train_boards([_rec("x"), _rec("x")], count=1)
    with pytest.raises(ValueError):
        cb.select_train_boards([{"profile_id": "x"}], count=1)
    with pytest.raises(ValueError):
        cb.select_train_boards([_rec("x")], count=0)


def test_select_rules_documented_and_exclude_list():
    assert "train-split" in cb.SELECTION_RULE_R2
    assert "禁止手挑" in cb.SELECTION_RULE_R2
    assert "pcbench-launchxl-f28027-isolation-pcb-project1" in \
        cb.ALREADY_RENDERED_PROFILE_IDS
    hints = cb.OBSERVATION_DIMENSION_HINTS_R2
    for dim in ("放置重叠", "平面覆盖", "clearance"):
        assert dim in hints


# ---------------------------------------------------------------------------
# 集成锚：run-r2 盘上产物（只读）
# ---------------------------------------------------------------------------

def test_run_r2_board_selection_on_disk():
    sel = json.load(open(os.path.join(
        REPO, "out", "v3-tl2", "critic-runs", "run-r2",
        "board-selection.json"), encoding="utf-8"))
    assert sel["selection_rule"] == cb.SELECTION_RULE_R2
    ids = [s["profile_id"] for s in sel["selected"]]
    assert ids == [
        "pcbench-data-manager-data-manager",
        "pcbench-flatpack2-adapter-eltekflatpack2",
        "pcbench-karabas-nano-karabas-nano-reva",
        "pcbench-karabas-nano-wifi-reva",
    ]
    for s in sel["selected"]:
        assert s["split"] == "train"
        src = os.path.join(REPO, *s["source_rel"].split("/"))
        assert os.path.isfile(src)
        # 重放选择器：同论域同结果（确定性）
        replay = cb.select_train_boards(sel["selected"] + [
            _rec("pcbench-launchxl-f28027-isolation-pcb-project1")],
            count=4)
        assert [r["profile_id"] for r in replay] == ids


def test_run_r2_manifest_done_and_renders():
    run_dir = os.path.join(REPO, "out", "v3-tl2", "critic-runs", "run-r2")
    manifest = json.load(open(os.path.join(run_dir, "render-manifest.json"),
                              encoding="utf-8"))
    assert manifest["run_id"] == "run-r2"
    assert manifest["visual_check"] == "done"        # observe 已执行（终态）
    assert len(manifest["boards"]) == 4
    for b in manifest["boards"]:
        sides = {r["side"] for r in b["renders"]}
        assert sides == {"top", "bottom"}
        for r in b["renders"]:
            png = os.path.join(run_dir, *r["file_rel"].split("/"))
            assert hashing.sha256_file(png) == r["sha256"]
            assert r["observation"]                  # 亲读后非空
    assert "observation_dimension_hints" in manifest
    # 正式 run 终态锚：bundle/record/队列在案（防覆写文件，不再演进；
    # 原 pending 锚是过渡态断言——正式 run 推进后由本终态锚取代）
    record_path = os.path.join(run_dir, "critic-run-record-CR-run-r2.json")
    ledger = os.path.join(run_dir, "queue-event-ledger.jsonl")
    for name in ("critic-input-bundle.json", "critic-input-bundle.sha256",
                 "critic-run-record-CR-run-r2.json",
                 "queue-event-ledger.jsonl"):
        assert os.path.isfile(os.path.join(run_dir, name))
    record = json.load(open(record_path, encoding="utf-8"))
    assert record["critic_status"] == "executed"
    assert record["critic_outcome"] == "blocked"
    # 队列关闭终态锚（S20 起 ITEM-run-r2 已处置关闭；原 open 单事件锚是
    # 过渡态断言——人工处置推进后由本关闭态锚取代，append-only 不回写）
    events = [json.loads(l) for l in open(ledger, encoding="utf-8")]
    assert [ev["event"] for ev in events] == \
        ["enqueue", "assign", "approve"]
    assert events[0]["item_id"] == "ITEM-run-r2"
    assert queue.verify_chain(events) == []
    assert queue.projection_summary(events)["queue_length"] == 0
    # datasets/ 只读复核：raw hash 与 manifest source 一致（byte 口径）
    for b in manifest["boards"]:
        raw = os.path.join(REPO, *b["source"]["path_rel"].split("/"))
        assert hashing.sha256_file(raw) == b["source"]["sha256"]


def test_run_r2_selfcheck_report():
    report = json.load(open(os.path.join(
        REPO, "out", "v3-tl2", "critic-runs", "run-r2",
        "ingest-selfcheck-synthetic.json"), encoding="utf-8"))
    assert report["synthetic"] is True
    checks = report["checks"]
    assert checks["ingest_critic_status"] == "executed"
    assert checks["ingest_outcome"] == "blocked"
    assert checks["triage_status"] == "critic_auto_route_blocked"
    assert checks["queue_event_observed"] == [
        {"event": "enqueue", "item_id": "ITEM-run-r2",
         "actor_role": "critic_model"}]
    assert "设计行为" in report["expected_real_run_outcome"]
    assert len(report["pending_handoff"]) == 3


# ---------------------------------------------------------------------------
# 纯内存合成 ingest 链（可重放；零落盘、零真实读取）
# ---------------------------------------------------------------------------

def test_synthetic_ingest_chain_blocked_enqueue_replay():
    boards = [{
        "profile_id": "synthetic-board-a", "split": "train",
        "split_basis": "synthetic",
        "source_board": {"path_rel": "synthetic/a.kicad_pcb",
                         "sha256": "a" * 64},
        "profile": {"path_rel": "profiles/synthetic-a/profile.json",
                    "sha256": "b" * 64},
        "renders": [
            {"file_rel": "renders/a-top.png", "side": "top",
             "sha256": "c" * 64, "observation": "SYNTHETIC 占位"},
            {"file_rel": "renders/a-bottom.png", "side": "bottom",
             "sha256": "d" * 64, "observation": "SYNTHETIC 占位"},
        ],
    }]
    bundle = critic_run.build_input_bundle(
        run_id="run-synthetic", selection_rule="synthetic rule",
        boards=boards, approval_sha256="e" * 64,
        calibration_domain_established=False)
    critic_run.validate_bundle(bundle)
    raw = {
        "reader_id": "SYNTHETIC-SELFCHECK-not-a-real-reader",
        "per_board": [{"profile_id": "synthetic-board-a", "flags": [
            {"category": "silk_readability", "confidence": 0.5,
             "location_evidence": "synthetic 占位",
             "description": "SYNTHETIC-SELFCHECK 合成占位旗",
             "abstain": False}]}],
        "reading_notes": "synthetic",
    }
    raw_text = json.dumps(raw, ensure_ascii=False)
    assert critic_run.validate_raw_flags(
        raw, expected_profiles=["synthetic-board-a"]) == []
    actual = {"source_board:synthetic-board-a": "a" * 64,
              "profile:synthetic-board-a": "b" * 64,
              "render:renders/a-top.png": "c" * 64,
              "render:renders/a-bottom.png": "d" * 64}
    result = critic_run.ingest_run(
        run_id="run-synthetic", bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=critic_run.bundle_sha256(bundle),
        actual_hashes=actual, approval_ok=True)
    assert result["record"]["critic_status"] == "executed"
    assert result["record"]["critic_outcome"] == "blocked"
    assert result["triage"]["status"] == "critic_auto_route_blocked"
    assert "critic_calibration_in_range" in \
        result["triage"]["failed_conditions"]
    assert len(result["queue_events"]) == 1
    ev = result["queue_events"][0]
    assert ev["event"] == "enqueue" and ev["item_id"] == "ITEM-run-synthetic"
    assert ev["actor_role"] == "critic_model"
    # 类别枚举零改动锚
    assert bundle["allowed_categories"] == list(critic.FLAG_CATEGORIES)


# ---------------------------------------------------------------------------
# observe/bundle/ingest 子命令（tmp_path 自造 mini fixture；不动 out/ 真实产物）
# ---------------------------------------------------------------------------

def _sha(path):
    return hashing.sha256_file(str(path))


def _observe_fixture(tmp_path, *, done=False):
    """自造 mini render-manifest+盘上文件（1 板×顶/底，结构与 s17 render
    产物一致：boards[].source/staged_copy/renders）。返回
    (repo, run_dir, manifest_path, obs_dict)。"""
    repo = tmp_path / "repo"
    run_dir = repo / "out" / "v3-tl2" / "critic-runs" / "run-r2"
    (run_dir / "renders").mkdir(parents=True)
    (run_dir / "staging").mkdir(parents=True)
    src = repo / "datasets" / "x" / "raw" / "board-a" / "raw.kicad_pcb"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"source-pcb-bytes")
    staged = run_dir / "staging" / "board-a-routed.kicad_pcb"
    staged.write_bytes(b"source-pcb-bytes")
    renders = []
    for side in ("top", "bottom"):
        p = run_dir / "renders" / f"board-a-{side}.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + side.encode())
        renders.append({
            "file_rel": f"renders/board-a-{side}.png", "side": side,
            "sha256": _sha(p), "bytes": p.stat().st_size,
            "width": 1600, "height": 900, "tool": "synthetic",
            "command": ["kicad-cli"], "observation": "",
        })
    manifest = {
        "schema_version": "3.0",
        "kind": "tl2_critic_render_manifest",
        "run_id": "run-r2",
        "selection_rule": "synthetic rule",
        "boards": [{
            "profile_id": "pcbench-board-a", "split": "train",
            "split_basis": "synthetic",
            "source": {"path_rel": "datasets/x/raw/board-a/raw.kicad_pcb",
                       "sha256": _sha(src)},
            "staged_copy": {"path_rel": "staging/board-a-routed.kicad_pcb",
                            "sha256": _sha(staged),
                            "byte_exact_match": True},
            "renders": renders,
        }],
        "visual_check": "done" if done else "pending",
        "note": "synthetic",
    }
    mp = run_dir / "render-manifest.json"
    mp.write_bytes(hashing.canonical_json_bytes(manifest))
    obs = {r["file_rel"].split("/", 1)[1]: f"观察-{r['side']}"
           for r in renders}
    return repo, run_dir, mp, obs


def _bundle_fixture(tmp_path):
    """observe 完成态 + APR-0005 disposition + profile.json（bundle 前置
    就绪，但不产 bundle——由调用方执行 _bundle）。"""
    repo, run_dir, mp, obs = _observe_fixture(tmp_path)
    s17._observe(mp, run_dir, repo, obs)
    ap = repo / critic_run.APPROVAL_PATH_REL
    ap.parent.mkdir(parents=True, exist_ok=True)
    ap.write_bytes(json.dumps({
        "disposition_id": "APR-0005",
        "rationale_code": "advisory_only（最小上岗等级）",
        "duty_level": "advisory_only",
    }, ensure_ascii=False).encode("utf-8"))
    prof = repo / "profiles" / "pcbench-board-a" / "profile.json"
    prof.parent.mkdir(parents=True, exist_ok=True)
    prof.write_bytes(b'{"profile_id": "pcbench-board-a"}')
    return repo, run_dir, mp


def _parses(text):
    try:
        json.loads(text)
        return True
    except ValueError:
        return False


_RAW = {
    "reader_id": "reader-under-test",
    "reading_notes": "synthetic test reading",
    "per_board": [{
        "profile_id": "pcbench-board-a",
        "flags": [{
            "category": "silk_readability", "confidence": 0.6,
            "location_evidence": "左上角丝印重叠区",
            "description": "synthetic test flag",
            "abstain": False,
        }],
    }],
}


def _ingest_fixture(tmp_path, orig_text):
    """bundle 就绪态（_bundle 已执行）+ as-returned 原文落盘。
    返回 (repo, run_dir)。"""
    repo, run_dir, mp = _bundle_fixture(tmp_path)
    s17._bundle(run_dir, repo, mp)
    (run_dir / "raw-flags-as-returned.txt").write_bytes(
        orig_text.encode("utf-8"))
    return repo, run_dir


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_observe_key_alignment_missing_and_extra(tmp_path):
    repo, run_dir, mp, obs = _observe_fixture(tmp_path)
    bad_missing = dict(obs)
    bad_missing.pop("board-a-top.png")
    with pytest.raises(SystemExit):
        s17._observe(mp, run_dir, repo, bad_missing)
    bad_extra = dict(obs)
    bad_extra["stale.png"] = "多余键"
    with pytest.raises(SystemExit):
        s17._observe(mp, run_dir, repo, bad_extra)
    # 拒绝后 manifest 不得被改写
    assert _read_json(mp)["visual_check"] == "pending"


def test_observe_empty_observation_and_render_drift_rejected(tmp_path):
    repo, run_dir, mp, obs = _observe_fixture(tmp_path)
    empty = dict(obs)
    empty["board-a-top.png"] = "   "
    with pytest.raises(SystemExit):
        s17._observe(mp, run_dir, repo, empty)
    # 渲染 hash 漂移 → 拒
    repo2, run_dir2, mp2, obs2 = _observe_fixture(tmp_path / "d2")
    (run_dir2 / "renders" / "board-a-top.png").write_bytes(b"tampered")
    with pytest.raises(SystemExit):
        s17._observe(mp2, run_dir2, repo2, obs2)


def test_observe_writes_done_and_anti_overwrite(tmp_path):
    repo, run_dir, mp, obs = _observe_fixture(tmp_path)
    sha = s17._observe(mp, run_dir, repo, obs)
    raw = mp.read_bytes()
    m = json.loads(raw.decode("utf-8"))
    assert m["visual_check"] == "done"
    assert sha == hashing.sha256_bytes(raw)
    assert hashing.canonical_json_bytes(m) == raw      # canonical 落盘
    for b in m["boards"]:
        for r in b["renders"]:
            assert r["observation"] == f"观察-{r['side']}"
    with pytest.raises(SystemExit):                    # 已 done 防覆写
        s17._observe(mp, run_dir, repo, obs)


def test_bundle_requires_visual_check_done(tmp_path):
    repo, run_dir, mp, _obs = _observe_fixture(tmp_path)   # pending
    with pytest.raises(SystemExit):
        s17._bundle(run_dir, repo, mp)
    assert not (run_dir / "critic-input-bundle.json").exists()


def test_bundle_byte_exact_roundtrip_sidecar_and_cleanup(tmp_path):
    repo, run_dir, mp = _bundle_fixture(tmp_path)
    sha = s17._bundle(run_dir, repo, mp)
    bp = run_dir / "critic-input-bundle.json"
    sp = run_dir / "critic-input-bundle.sha256"
    data = bp.read_bytes()
    rebuilt = hashing.canonical_json_bytes(json.loads(data.decode("utf-8")))
    assert data == rebuilt                             # byte-exact 往复
    assert hashing.sha256_bytes(data) == sha
    assert sp.read_text(encoding="utf-8").strip() == sha
    bundle = json.loads(data.decode("utf-8"))
    assert bundle["run_id"] == "run-r2"
    assert bundle["calibration"]["domain_established"] is False
    assert bundle["approval"]["sha256"] == _sha(
        repo / critic_run.APPROVAL_PATH_REL)
    assert all(r["observation"] for b in bundle["boards"]
               for r in b["renders"])
    assert not (run_dir / "staging").exists()          # staging 清理无残留
    with pytest.raises(SystemExit):                    # 防覆写
        s17._bundle(run_dir, repo, mp)


def test_ingest_branch_a_repair_and_enqueue(tmp_path):
    orig = json.dumps(_RAW, ensure_ascii=False)[:-2]   # 掐掉 "…]}" 尾
    assert not _parses(orig)
    repo, run_dir = _ingest_fixture(tmp_path, orig)
    orig_bytes = (run_dir / "raw-flags-as-returned.txt").read_bytes()
    s17._ingest(run_dir, repo)

    disc_path = run_dir / "raw-flags-repair-disclosure.json"
    disc = _read_json(disc_path)
    assert disc["repair"]["kind"] == "single_insertion"
    assert disc["repair"]["chars_removed"] == 0
    assert disc["repair"]["chars_modified"] == 0
    assert disc["repair"]["chars_added"] == len(disc["repair"]["inserted"])
    assert disc["as_returned"]["json_parses"] is False
    assert disc["as_returned"]["parse_error"]
    assert disc["as_returned"]["sha256"] == hashing.sha256_bytes(orig_bytes)
    rf = run_dir / "raw-flags.json"
    repaired = rf.read_text(encoding="utf-8")
    assert repaired.startswith(orig)                   # 纯插入=原文是前缀
    assert json.loads(repaired) == _RAW                # 内容零改动
    assert hashing.sha256_bytes(rf.read_bytes()) == \
        disc["repaired_ingested"]["sha256"]
    assert (run_dir / "raw-flags-as-returned.txt").read_bytes() == orig_bytes

    rec_path = run_dir / "critic-run-record-CR-run-r2.json"
    rec = _read_json(rec_path)
    rec_sha = hashing.sha256_bytes(hashing.canonical_json_bytes(rec))
    assert rec["critic_status"] == "executed"
    assert rec["critic_outcome"] == "blocked"
    assert rec["input_hashes"]["provenance:raw_flags_as_returned"] == \
        disc["as_returned"]["sha256"]
    assert rec["input_hashes"]["provenance:raw_flags_repair_disclosure"] == \
        hashing.sha256_bytes(disc_path.read_bytes())

    lines = (run_dir / "queue-event-ledger.jsonl").read_text(
        encoding="utf-8").splitlines()
    evs = [json.loads(line) for line in lines]
    assert queue.verify_chain(evs) == []
    assert len(evs) == 1
    ev = evs[0]
    assert ev["event"] == "enqueue" and ev["item_id"] == "ITEM-run-r2"
    assert ev["actor"] == "pcbflow-critic-pipeline"
    assert ev["actor_role"] == "critic_model"
    assert ev["reason_code"] == "critic_auto_route_blocked"
    assert ev["critic_ref"] == rec_sha

    rep = _read_json(run_dir / "ingest-report.json")
    assert rep["triage"]["decision"]["status"] == "critic_auto_route_blocked"
    assert rep["triage"]["predicates"] == s17.PREDICATES
    assert "judge_gate_pass=False" in rep["triage"]["basis"]
    assert rep["disclosure"]["repair_kind"] == "repair"
    assert rep["inputs"]["approval"]["disposition_id"] == "APR-0005"
    with pytest.raises(SystemExit):                    # 防覆写
        s17._ingest(run_dir, repo)


def test_ingest_branch_b_no_repair_canonical(tmp_path):
    orig = json.dumps(_RAW, indent=2, ensure_ascii=False)   # 可解析、非 canonical
    assert _parses(orig)
    repo, run_dir = _ingest_fixture(tmp_path, orig)
    orig_bytes = (run_dir / "raw-flags-as-returned.txt").read_bytes()
    s17._ingest(run_dir, repo)

    disc = _read_json(run_dir / "raw-flags-repair-disclosure.json")
    assert disc["repair"]["kind"] == "no_repair"
    assert disc["as_returned"]["json_parses"] is True
    assert disc["as_returned"]["sha256"] == hashing.sha256_bytes(orig_bytes)
    rf = run_dir / "raw-flags.json"
    assert rf.read_bytes() == hashing.canonical_json_bytes(json.loads(orig))
    assert json.loads(rf.read_text(encoding="utf-8")) == json.loads(orig)

    rec = _read_json(run_dir / "critic-run-record-CR-run-r2.json")
    assert rec["critic_status"] == "executed"
    assert rec["model"]["version"] == "reader-under-test"
    rep = _read_json(run_dir / "ingest-report.json")
    assert rep["disclosure"]["repair_kind"] == "no_repair"
    evs = [json.loads(line) for line in (run_dir /
            "queue-event-ledger.jsonl").read_text(
                encoding="utf-8").splitlines()]
    assert len(evs) == 1 and evs[0]["item_id"] == "ITEM-run-r2"


def test_ingest_rejects_unrepairable_as_returned(tmp_path):
    # 尾逗号：括号栈平衡但不可解析 → 无法纯插入修复 → 拒收
    orig = json.dumps(_RAW, ensure_ascii=False) + ","
    assert not _parses(orig)
    repo, run_dir = _ingest_fixture(tmp_path, orig)
    with pytest.raises(SystemExit):
        s17._ingest(run_dir, repo)
    assert not (run_dir / "raw-flags.json").exists()
    assert not (run_dir / "critic-run-record-CR-run-r2.json").exists()
    # 多余闭合：结构不可判定 → 拒收
    orig2 = json.dumps(_RAW, ensure_ascii=False) + "}"
    assert not _parses(orig2)
    repo2, run_dir2 = _ingest_fixture(tmp_path / "x2", orig2)
    with pytest.raises(SystemExit):
        s17._ingest(run_dir2, repo2)
    assert not (run_dir2 / "raw-flags.json").exists()


def test_ingest_anti_overwrite_raw_flags(tmp_path):
    orig = json.dumps(_RAW, ensure_ascii=False)[:-2]
    repo, run_dir = _ingest_fixture(tmp_path, orig)
    (run_dir / "raw-flags.json").write_bytes(b"pre-existing")
    with pytest.raises(SystemExit):
        s17._ingest(run_dir, repo)
