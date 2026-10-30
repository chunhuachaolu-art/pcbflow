#!/usr/bin/env python
"""S17-T5：run-r2 advisory 扩样管线就绪（写 out/v3-tl2/critic-runs/run-r2/）。

三步（库侧纯函数=pcbflow/critic_batch.select_train_boards + 
pcbflow/critic_run.*；kicad-cli 渲染为外部工具链走本编排脚本）：

  select    确定性选板：pcbench-r1 train split、slug 升序、排除本轨道
            已渲染板、取前 4（pcbflow.critic_batch.SELECTION_RULE_R2）。
  render    四板 datasets raw 参考 routed 态 staging 逐字节拷贝 → 
            kicad-cli pcb render 顶/底 PNG → renders/；render-manifest
            落盘 visual_check=pending（observe 须由主智能体亲读完成后
            才能构建正式 bundle——run-r1 同口径）。
  selfcheck 合成自检（in-memory，零真实读取、零真实 ingest）：合成
            bundle（observation=显式 synthetic 占位，**不落盘**）+合成
            raw-flags（reader_id 显式标 synthetic）→ validate_raw_flags
            + ingest_run 全链 → 预期 blocked→enqueue ITEM-run-r2
            （设计行为）；除本报告文件外零合成产物残留。

真实 reader 由主智能体另行派发：主智能体 observe（亲读 PNG）→ bundle
→ 派发 → 真实 ingest。本包**不读图、不产真实 flag、不执行真实 ingest**。

驱动用子命令（交付给主智能体执行，本包开发时**不代跑**；与
s14_critic_render.py cmd_observe/cmd_bundle、s14_critic_ingest.py 同构，
适配 run-r2）：

  observe   stdin 读 {渲染文件名: 观感一句话}；键与 manifest renders
            精确对齐（missing/extra 都拒）；复验 datasets 源/staging/
            渲染 PNG hash 不漂移；observation 非空；写 visual_check=done
            （已 done 防覆写拒绝）。
  bundle    防覆写；要求 visual_check=done；APR-0005 disposition 实测
            hash+语义校验；boards 组装（profile.json 实测 hash）；
            build_input_bundle（calibration_domain_established=False：
            校准域现状 status=seed_annotation_only，种子标注完成≠校准
            达标）；canonical byte-exact 往复验；bundle+sidecar 落盘后
            清理 staging 并断言无残留。
  ingest    四段（对账 fail-closed / raw 修复披露双分支 / ingest_run /
            落盘 record+queue-event-ledger+ingest-report）：as-returned
            不可解析→纯单点插入修复（difflib 守卫 0 删 0 改，非纯插入
            拒收 fail-closed）；可解析→raw-flags.json 即其 canonical 化
            （内容零改动，no_repair）；两分支都保留 as-returned 原文为
            证据文件并绑 record provenance。PREDICATES 与 run-r1 同值。

用法：python scripts/s17_run_r2.py select|render|selfcheck|observe|bundle|ingest
     （仓库根执行；observe 从 stdin 读观感 JSON）
"""

from __future__ import annotations

import difflib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import critic, critic_batch, critic_run, hashing, queue  # noqa: E402

RUN_ID = "run-r2"
RUN_DIR = REPO / "out" / "v3-tl2" / "critic-runs" / RUN_ID
RENDERS_DIR = RUN_DIR / "renders"
STAGING_DIR = RUN_DIR / "staging"
SELECTION_OUT = RUN_DIR / "board-selection.json"
MANIFEST = RUN_DIR / "render-manifest.json"
SELFCHECK_OUT = RUN_DIR / "ingest-selfcheck-synthetic.json"

KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_VERSION = "10.0.5"
RENDER_SIZE = (1600, 900)
MIN_SIZE = (1200, 675)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
COUNT = 4

#: TD5 前置谓词（与 run-r1 同值：run-r2 参考 routed 态 advisory 读取的
#: 如实取值与依据；judge/checker/白名单上下文缺席=fail-closed）
PREDICATES = {
    "judge_gate_pass": False,
    "required_checkers_executed": False,
    "no_stale_or_unknown": True,
    "whitelist_item": False,
}
PREDICATE_BASIS = (
    "judge_gate_pass=False：run-r2 为参考 routed 态 advisory 扩样读取"
    "（4 train 板），无 judge 运行记录（缺证据闭门律，fail-closed）；"
    "required_checkers_executed=False：本 run 无 checker 上下文；"
    "no_stale_or_unknown=True：run 自身各状态无 stale/unknown/"
    "not_available（critic_status/schema/hash 面如实），judge/checker "
    "缺席由对应谓词 False 捕捉；whitelist_item=False：非白名单项。")


def _fail(msg: str) -> None:
    print(f"[s17-r2] FAIL: {msg}")
    sys.exit(1)


def _write_canonical(path: Path, obj) -> str:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def _png_size(path: Path) -> tuple:
    data = path.read_bytes()
    if not data.startswith(PNG_MAGIC):
        _fail(f"{path.name}: 不是 PNG（magic 不符）")
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def _enumerate_pcbench_train_records() -> list:
    """从 profiles/ 枚举 pcbench profile 记录（磁盘实读；路径来自
    manifest reference_route，经 path 校验后只读 hash）。"""
    records = []
    for pdir in sorted((REPO / "profiles").iterdir()):
        mf_path = pdir / "manifest.json"
        if not pdir.name.startswith("pcbench-") or not mf_path.is_file():
            continue
        mf = json.loads(mf_path.read_text(encoding="utf-8"))
        ref = (mf.get("backtest", {}).get("reference_route") or "")
        ref_posix = ref.replace("\\", "/")
        train = (mf.get("dataset_splits", {}).get("train") or [])
        rel = None
        parts = ref_posix.split("/")
        if "datasets" in parts:
            rel = "/".join(parts[parts.index("datasets"):])
        if rel is None:
            continue
        records.append({
            "profile_id": pdir.name,
            "split": "train" if pdir.name.replace("pcbench-", "") and
                     _profile_slug_in(pdir.name, train) else "other",
            "split_basis": (f"profiles/{pdir.name}/manifest.json "
                            f"dataset_splits.train 含本板"),
            "source_rel": rel,
        })
    return records


def _profile_slug_in(profile_id: str, train: list) -> bool:
    """profile 的 raw 目录名是否在 train 名单（manifest backtest.
    reference_route 的 slug 与 dataset_splits.train 比对）。"""
    mf = json.loads((REPO / "profiles" / profile_id / "manifest.json")
                    .read_text(encoding="utf-8"))
    ref = (mf.get("backtest", {}).get("reference_route") or "").replace(
        "\\", "/")
    parts = ref.split("/")
    slug = parts[parts.index("raw") + 1] if "raw" in parts else None
    return slug in train


# ---------------------------------------------------------------------------
# select
# ---------------------------------------------------------------------------

def cmd_select() -> None:
    if SELECTION_OUT.exists():
        _fail("board-selection.json 已存在（防覆写）")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    records = _enumerate_pcbench_train_records()
    selected = critic_batch.select_train_boards(records, count=COUNT)
    out = {
        "schema_version": "3.0",
        "kind": "tl2_critic_board_selection",
        "run_id": RUN_ID,
        "selection_rule": critic_batch.SELECTION_RULE_R2,
        "universe_size": len(records),
        "excluded_already_rendered": list(
            critic_batch.ALREADY_RENDERED_PROFILE_IDS),
        "selected": selected,
    }
    sha = _write_canonical(SELECTION_OUT, out)
    for s in selected:
        print(f"[s17-r2] selected: {s['profile_id']}")
    print(f"[s17-r2] board-selection.json sha256={sha[:16]}…")


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def cmd_render() -> None:
    if MANIFEST.exists():
        _fail("render-manifest.json 已存在（防覆写）")
    if not KICAD_CLI.exists():
        _fail(f"kicad-cli 不存在：{KICAD_CLI}")
    if not SELECTION_OUT.exists():
        _fail("board-selection.json 不存在（先跑 select）")
    sel = json.loads(SELECTION_OUT.read_text(encoding="utf-8"))
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    boards_out = []
    for item in sel["selected"]:
        pid = item["profile_id"]
        prefix = pid.removeprefix("pcbench-")
        src = REPO / item["source_rel"]
        if not src.is_file():
            _fail(f"参考 routed 态缺失：{item['source_rel']}")
        src_sha = hashing.sha256_file(str(src))
        staged = STAGING_DIR / f"{prefix}-routed.kicad_pcb"
        shutil.copyfile(src, staged)
        if hashing.sha256_file(str(staged)) != src_sha:
            _fail(f"staging 逐字节断言失败：{staged.name}")
        renders = []
        for side in ("top", "bottom"):
            name = f"{prefix}-{side}.png"
            out_png = RENDERS_DIR / name
            if out_png.exists():
                _fail(f"{name} 已存在（防覆写）")
            cmd = ["kicad-cli", "pcb", "render", "--side", side,
                   "--width", str(RENDER_SIZE[0]),
                   "--height", str(RENDER_SIZE[1]),
                   "--background", "opaque", "--quality", "basic",
                   "-o", f"renders/{name}",
                   f"staging/{staged.name}"]
            proc = subprocess.run(
                [str(KICAD_CLI)] + cmd[1:], cwd=RUN_DIR,
                capture_output=True, text=True)
            if proc.returncode != 0 or not out_png.exists():
                _fail(f"kicad render 失败（{name}）：rc={proc.returncode} "
                      f"{(proc.stderr or proc.stdout)[-400:]}")
            w, h = _png_size(out_png)
            if w < MIN_SIZE[0] or h < MIN_SIZE[1]:
                _fail(f"{name}: 尺寸 {w}x{h} 低于可读下限 {MIN_SIZE}")
            renders.append({
                "file_rel": f"renders/{name}", "side": side,
                "sha256": hashing.sha256_file(str(out_png)),
                "bytes": out_png.stat().st_size,
                "width": w, "height": h,
                "tool": f"kicad-cli {KICAD_VERSION} pcb render",
                "command": cmd,
                "observation": "",
            })
            print(f"[s17-r2] render ok: {name} "
                  f"{out_png.stat().st_size}B {w}x{h}")
        boards_out.append({
            "profile_id": pid, "split": item["split"],
            "split_basis": item["split_basis"],
            "source": {"path_rel": item["source_rel"], "sha256": src_sha},
            "staged_copy": {"path_rel": f"staging/{staged.name}",
                            "sha256": src_sha, "byte_exact_match": True},
            "renders": renders,
        })
    manifest = {
        "schema_version": "3.0",
        "kind": "tl2_critic_render_manifest",
        "run_id": RUN_ID,
        "selection_rule": sel["selection_rule"],
        "observation_dimension_hints":
            critic_batch.OBSERVATION_DIMENSION_HINTS_R2,
        "boards": boards_out,
        "visual_check": "pending",
        "note": ("observation 由主智能体用 Read 工具逐张亲读后经 observe "
                 "步骤写入；visual_check=pending 期间不得构建正式 bundle。"
                 "本包不读图（红线）：渲染与选板为 pipeline 侧动作。"),
    }
    sha = _write_canonical(MANIFEST, manifest)
    print(f"[s17-r2] manifest 写出（visual_check=pending）：{sha[:16]}…")


# ---------------------------------------------------------------------------
# selfcheck（合成、in-memory；不产真实 flag、不真实 ingest、零残留）
# ---------------------------------------------------------------------------

def cmd_selfcheck() -> None:
    if SELFCHECK_OUT.exists():
        _fail("ingest-selfcheck-synthetic.json 已存在（防覆写）")
    if not MANIFEST.exists():
        _fail("render-manifest.json 不存在（先跑 select+render）")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    approval_path = REPO / critic_run.APPROVAL_PATH_REL
    if not approval_path.exists():
        _fail(f"APR-0005 disposition 缺失：{critic_run.APPROVAL_PATH_REL}")
    approval_sha = hashing.sha256_file(str(approval_path))

    # 合成 bundle：真实 hash 元数据 + 显式 synthetic 占位 observation；
    # 只在内存中存在，不落盘（正式 bundle 须待 observe 后由主智能体构建）
    boards = []
    actual = {}
    for b in manifest["boards"]:
        pid = b["profile_id"]
        profile_path = REPO / "profiles" / pid / "profile.json"
        boards.append({
            "profile_id": pid, "split": b["split"],
            "split_basis": b["split_basis"],
            "source_board": {"path_rel": b["source"]["path_rel"],
                             "sha256": b["source"]["sha256"]},
            "profile": {"path_rel": f"profiles/{pid}/profile.json",
                        "sha256": hashing.sha256_file(str(profile_path))},
            "renders": [{"file_rel": r["file_rel"], "side": r["side"],
                         "sha256": r["sha256"],
                         "observation": ("SYNTHETIC-SELFCHECK 占位（非观感"
                                         "；bundle 不落盘，正式 bundle 须"
                                         "待 observe 亲读后构建）")}
                        for r in b["renders"]],
        })
        actual[f"source_board:{pid}"] = hashing.sha256_file(
            str(REPO / b["source"]["path_rel"]))
        actual[f"profile:{pid}"] = hashing.sha256_file(str(profile_path))
        for r in b["renders"]:
            actual[f"render:{r['file_rel']}"] = hashing.sha256_file(
                str(RUN_DIR / r["file_rel"]))
    bundle = critic_run.build_input_bundle(
        run_id=RUN_ID,
        selection_rule=manifest["selection_rule"],
        boards=boards, approval_sha256=approval_sha,
        calibration_domain_established=False)
    critic_run.validate_bundle(bundle)
    expected_bundle_sha = critic_run.bundle_sha256(bundle)

    # 合成 raw flags（reader_id 显式标 synthetic；每板 1 条纯占位旗）
    raw = {
        "reader_id": "SYNTHETIC-SELFCHECK-not-a-real-reader",
        "per_board": [{
            "profile_id": b["profile_id"],
            "flags": [{
                "category": "silk_readability",
                "confidence": 0.5,
                "location_evidence": "synthetic-selfcheck 占位位置证据"
                                     "（synthetic，非真实观察）",
                "description": "SYNTHETIC-SELFCHECK 合成自检占位旗：仅"
                               "验证 validate_raw_flags+ingest_run 全链"
                               "通路，非任何真实读取结果。",
                "abstain": False,
            }],
        } for b in manifest["boards"]],
        "reading_notes": "synthetic selfcheck：零真实读取；占位数据。",
    }
    raw_text = json.dumps(raw, ensure_ascii=False)
    raw_errs = critic_run.validate_raw_flags(
        raw, expected_profiles=[b["profile_id"] for b in manifest["boards"]])
    if raw_errs:
        _fail(f"合成 raw flags 未过 validate_raw_flags：{raw_errs}")

    result = critic_run.ingest_run(
        run_id=RUN_ID, bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=expected_bundle_sha, actual_hashes=actual,
        approval_ok=True,
        judge_gate_pass=False, required_checkers_executed=False,
        no_stale_or_unknown=True, whitelist_item=False)
    rec = result["record"]
    triage = result["triage"]
    ev = result["queue_events"]
    if rec["critic_status"] != "executed" or rec["critic_outcome"] != "blocked":
        _fail("自检裁决与预期不符（executed+blocked）")
    if triage["status"] != "critic_auto_route_blocked" \
            or triage["eligible"] is not False:
        _fail("自检分诊与预期不符（blocked 路由）")
    if len(ev) != 1 or ev[0]["event"] != "enqueue" \
            or ev[0]["item_id"] != f"ITEM-{RUN_ID}":
        _fail("自检队列事件与预期不符（enqueue ITEM-run-r2）")

    report = {
        "schema_version": "3.0",
        "kind": "tl2_critic_ingest_selfcheck_synthetic",
        "run_id": RUN_ID,
        "synthetic": True,
        "scope": (
            "管线通路自检：合成 bundle/合成 raw-flags（reader_id 显式标 "
            "SYNTHETIC-SELFCHECK）in-memory 跑通 validate_raw_flags + "
            "ingest_run 全链。零真实读取（本包不读图）、零真实 ingest；"
            "合成 bundle/raw/record/队列事件一律不落盘（本报告是唯一"
            "落盘物），真实 reader 由主智能体另行派发。"),
        "checks": {
            "validate_bundle": "pass",
            "validate_raw_flags": "pass",
            "ingest_critic_status": rec["critic_status"],
            "ingest_outcome": rec["critic_outcome"],
            "triage_status": triage["status"],
            "triage_failed_conditions": triage["failed_conditions"],
            "queue_event_expected": ("enqueue ITEM-run-r2（critic_model "
                                     "角色，fail-closed blocked→人工队列"
                                     "——设计行为，不是缺陷）"),
            "queue_event_observed": [{"event": e["event"],
                                      "item_id": e["item_id"],
                                      "actor_role": e["actor_role"]}
                                     for e in ev],
            "abstain_count": result["abstain_count"],
        },
        "expected_real_run_outcome": (
            "run-r2 真实 run 预期=仍 fail-closed blocked→enqueue "
            "ITEM-run-r2（judge/checker/校准域未到位为真实缺口；设计"
            "行为，不是缺陷）。"),
        "pending_handoff": [
            "observe：主智能体亲读 8 张 PNG（4 板×顶/底）并写 observation",
            "bundle：visual_check=done 后构建正式 bundle（本包未落盘）",
            "reader 派发与真实 ingest 由主智能体执行",
        ],
    }
    sha = _write_canonical(SELFCHECK_OUT, report)
    print(f"[s17-r2] selfcheck pass（合成 in-memory）：executed+blocked→"
          f"enqueue ITEM-{RUN_ID}；报告 sha256={sha[:16]}…")


# ---------------------------------------------------------------------------
# observe（主智能体亲读 PNG 后驱动；stdin {渲染文件名: 观感一句话}）
# ---------------------------------------------------------------------------

def cmd_observe() -> None:
    try:
        obs = json.load(sys.stdin)
    except Exception as exc:                      # noqa: BLE001
        _fail(f"stdin 不是合法 JSON：{exc}")
    if not isinstance(obs, dict):
        _fail("stdin JSON 必须为对象 {渲染文件名: 观感一句话}")
    _observe(MANIFEST, RUN_DIR, REPO, obs)


def _observe(manifest_path: Path, run_dir: Path, repo: Path, obs: dict) -> str:
    """把亲读观感写入 manifest（visual_check=done）；返回 manifest sha256。"""
    if not manifest_path.exists():
        _fail("render-manifest.json 不存在（先跑 render）")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("visual_check") == "done":
        _fail("visual_check 已 done（防覆写）")
    all_files = [r["file_rel"].split("/", 1)[1]
                 for b in manifest["boards"] for r in b["renders"]]
    missing = [f for f in all_files if f not in obs]
    extra = [k for k in obs if k not in all_files]
    if missing or extra:
        _fail(f"观感键不齐：missing={missing} extra={extra}")
    for b in manifest["boards"]:
        # 复验：datasets 源、staging、渲染 PNG hash 均未漂移
        src = repo / b["source"]["path_rel"]
        if hashing.sha256_file(str(src)) != b["source"]["sha256"]:
            _fail(f"datasets 源 hash 漂移：{b['source']['path_rel']}")
        staged = run_dir / b["staged_copy"]["path_rel"]
        if not staged.exists() or (hashing.sha256_file(str(staged))
                                   != b["staged_copy"]["sha256"]):
            _fail(f"staging hash 漂移：{staged.name}")
        for r in b["renders"]:
            png = run_dir / r["file_rel"]
            if hashing.sha256_file(str(png)) != r["sha256"]:
                _fail(f"渲染文件 hash 漂移：{r['file_rel']}")
            text = str(obs[r["file_rel"].split("/", 1)[1]]).strip()
            if not text:
                _fail(f"{r['file_rel']}: 观感为空（必须亲读后填写）")
            r["observation"] = text
    manifest["visual_check"] = "done"
    return _write_canonical(manifest_path, manifest)


# ---------------------------------------------------------------------------
# bundle（visual_check=done 后构建正式 bundle；防覆写；清理 staging）
# ---------------------------------------------------------------------------

def cmd_bundle() -> None:
    _bundle(RUN_DIR, REPO, MANIFEST)


def _bundle(run_dir: Path, repo: Path, manifest_path: Path) -> str:
    """构建 critic-input-bundle.json+sidecar（canonical byte-exact）；
    收尾清理 staging 并断言无残留。返回 bundle sha256。"""
    bundle_path = run_dir / "critic-input-bundle.json"
    sidecar_path = run_dir / "critic-input-bundle.sha256"
    staging_dir = run_dir / "staging"
    if bundle_path.exists() or sidecar_path.exists():
        _fail("bundle/sidecar 已存在（防覆写）")
    if not manifest_path.exists():
        _fail("render-manifest.json 不存在（先跑 render+observe）")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("visual_check") != "done":
        _fail("visual_check 未 done（先逐张亲读 PNG 并 observe）")
    data = _bundle_bytes(manifest, repo)
    sha = hashing.sha256_bytes(data)
    bundle_path.write_bytes(data)
    sidecar_path.write_bytes((sha + "\n").encode("utf-8"))
    print(f"[s17-r2] bundle 写出：critic-input-bundle.json "
          f"sha256={sha[:16]}…（sidecar 同值）")
    # 收尾：清理 staging 并断言无残留
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
        print("[s17-r2] staging 已清理")
    if staging_dir.exists():
        _fail("staging 清理后仍存在")
    leftover = sorted(str(p.relative_to(run_dir))
                      for p in run_dir.rglob("*")
                      if p.is_file() and "staging" in
                      p.relative_to(run_dir).parts)
    if leftover:
        _fail(f"staging 残留：{leftover}")
    return sha


def _bundle_bytes(manifest: dict, repo: Path) -> bytes:
    """由 manifest 组装 boards → build_input_bundle → canonical 字节
    （byte-exact 往复复验；返回通过复验的 bundle canonical 字节）。"""
    approval_path = repo / critic_run.APPROVAL_PATH_REL
    if not approval_path.exists():
        _fail(f"APR-0005 disposition 缺失：{critic_run.APPROVAL_PATH_REL}")
    approval_sha = hashing.sha256_file(str(approval_path))
    apr = json.loads(approval_path.read_text(encoding="utf-8"))
    if apr.get("disposition_id") != critic_run.APPROVAL_DISPOSITION_ID \
            or "advisory" not in str(apr.get("rationale_code", "")):
        _fail("APR-0005 disposition 内容与 advisory_only 裁决不符")
    boards = []
    for b in manifest["boards"]:
        pid = b["profile_id"]
        profile_path = repo / "profiles" / pid / "profile.json"
        if not profile_path.exists():
            _fail(f"profile.json 缺失：{pid}")
        boards.append({
            "profile_id": pid,
            "split": b["split"],
            "split_basis": b["split_basis"],
            "source_board": {"path_rel": b["source"]["path_rel"],
                             "sha256": b["source"]["sha256"]},
            "profile": {"path_rel": f"profiles/{pid}/profile.json",
                        "sha256": hashing.sha256_file(str(profile_path))},
            "renders": [{"file_rel": r["file_rel"], "side": r["side"],
                         "sha256": r["sha256"],
                         "observation": r["observation"]}
                        for r in b["renders"]],
        })
    # calibration_domain_established=False：校准域现状 status=
    # seed_annotation_only——种子标注完成≠校准达标，无已校准置信域，
    # in_calibrated_range 恒 False，flags=[] 一律 blocked（fail-closed）。
    bundle = critic_run.build_input_bundle(
        run_id=RUN_ID, selection_rule=manifest["selection_rule"],
        boards=boards, approval_sha256=approval_sha,
        calibration_domain_established=False)
    critic_run.validate_bundle(bundle)
    data = hashing.canonical_json_bytes(bundle)
    rebuilt = hashing.canonical_json_bytes(json.loads(data.decode("utf-8")))
    if data != rebuilt:
        _fail("bundle byte-exact 复验失败（canonical 往返不一致）")
    return data


# ---------------------------------------------------------------------------
# ingest（四段：对账 fail-closed → raw 修复披露双分支 → ingest_run → 落盘）
# ---------------------------------------------------------------------------

def cmd_ingest() -> None:
    _ingest(RUN_DIR, REPO)


def _ingest(run_dir: Path, repo: Path) -> dict:
    bundle_path = run_dir / "critic-input-bundle.json"
    sidecar_path = run_dir / "critic-input-bundle.sha256"
    raw_flags_path = run_dir / "raw-flags.json"
    raw_orig_path = run_dir / "raw-flags-as-returned.txt"
    disclosure_path = run_dir / "raw-flags-repair-disclosure.json"
    record_out = run_dir / f"critic-run-record-CR-{RUN_ID}.json"
    ledger_out = run_dir / "queue-event-ledger.jsonl"
    report_out = run_dir / "ingest-report.json"

    for out in (raw_flags_path, disclosure_path, record_out, ledger_out,
                report_out):
        if out.exists():
            _fail(f"{out.name} 已存在（防覆写；发布产物不可覆写）")

    try:
        run_rel = run_dir.relative_to(repo).as_posix()
    except ValueError:
        run_rel = f"out/v3-tl2/critic-runs/{RUN_ID}"

    # ---- 1. bundle/sidecar 对账（fail-closed） ----------------------------
    if not bundle_path.exists() or not sidecar_path.exists():
        _fail("bundle/sidecar 缺失（先跑 observe+bundle）")
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    sidecar = sidecar_path.read_text(encoding="utf-8").strip()
    bundle_sha_disk = hashing.sha256_file(str(bundle_path))
    if critic_run.bundle_sha256(bundle) != sidecar \
            or bundle_sha_disk != sidecar:
        _fail("bundle canonical/sidecar/盘上字节 三方对账不符（可信侧漂移）")

    # ---- 2. APR-0005 锚 ----------------------------------------------------
    approval_path = repo / critic_run.APPROVAL_PATH_REL
    if not approval_path.exists():
        _fail("APR-0005 disposition 缺失")
    approval_sha = hashing.sha256_file(str(approval_path))
    apr = json.loads(approval_path.read_text(encoding="utf-8"))
    if approval_sha != bundle["approval"]["sha256"] \
            or apr.get("disposition_id") \
            != critic_run.APPROVAL_DISPOSITION_ID \
            or "advisory" not in str(apr.get("rationale_code", "")):
        _fail("APR-0005 锚校验不符（bundle 声明 vs 盘上实测/语义）")
    approval_ok = True

    # ---- 3. raw 修复披露（双分支；as-returned 原文恒留证） ------------------
    if not raw_orig_path.exists():
        _fail("raw-flags-as-returned.txt 缺失（读取者原文必须留证落盘）")
    orig_bytes = raw_orig_path.read_bytes()
    orig_text = orig_bytes.decode("utf-8")
    orig_sha = hashing.sha256_bytes(orig_bytes)
    try:
        parsed_orig = json.loads(orig_text)
        orig_parse_error = None
    except json.JSONDecodeError as exc:
        parsed_orig = None
        orig_parse_error = f"{type(exc).__name__}: {exc}"

    if parsed_orig is None:
        # 分支 (a)：原文不可解析 → 机械纯单点插入修复（difflib 守卫）
        repaired_text, insert_at, inserted = \
            _single_insertion_repair(orig_text)
        raw_bytes = repaired_text.encode("utf-8")
        branch = "repair"
    else:
        # 分支 (b)：原文本身可解析 → raw-flags.json 即其 canonical 化
        #（内容零改动：重解析比对相等；未做任何修复性字符操作）
        raw_bytes = hashing.canonical_json_bytes(parsed_orig)
        if json.loads(raw_bytes.decode("utf-8")) != parsed_orig:
            _fail("canonical 化内容校验失败（解析值零改动不可证）")
        insert_at = None
        inserted = None
        branch = "no_repair"
    raw_flags_path.write_bytes(raw_bytes)
    raw_sha = hashing.sha256_bytes(raw_bytes)
    if hashing.sha256_file(str(raw_flags_path)) != raw_sha:
        _fail("raw-flags.json 落盘字节自校验失败")
    raw_text = raw_bytes.decode("utf-8")

    if branch == "repair":
        repair_block = {
            "kind": "single_insertion",
            "insert_at_char": insert_at,
            "inserted": inserted,
            "chars_added": len(inserted),
            "chars_removed": 0,
            "chars_modified": 0,
            "note": ("实测修复=在原文末尾按括号栈补齐缺失闭合结构字符"
                     "（纯单点插入）；内容字符零改动零移动（difflib 单 "
                     "insert op 守卫，0 删 0 改）。"),
        }
    else:
        repair_block = {
            "kind": "no_repair",
            "chars_added": 0,
            "chars_removed": 0,
            "chars_modified": 0,
            "note": ("读取者原文本身可解析：raw-flags.json=原文解析值的 "
                     "canonical 化重序列化（内容零改动——重解析比对相等）；"
                     "未做任何修复性字符操作，原文保留为证据文件。"),
        }
    disclosure = {
        "schema_version": "3.0",
        "kind": "tl2_raw_flags_repair_disclosure",
        "run_id": RUN_ID,
        "as_returned": {
            "path_rel": f"{run_rel}/raw-flags-as-returned.txt",
            "sha256": orig_sha,
            "bytes": len(orig_bytes),
            "json_parses": parsed_orig is not None,
            **({} if parsed_orig is not None
               else {"parse_error": orig_parse_error}),
        },
        "repaired_ingested": {
            "path_rel": f"{run_rel}/raw-flags.json",
            "sha256": raw_sha,
            "bytes": len(raw_bytes),
        },
        "repair": repair_block,
        "pipeline_note": ("管线对读取者输出零位置容错：as-returned 原文恒"
                          "保留为证据文件（sha 绑 record provenance）；"
                          "ingest 输入的任何差异均如实披露于本文件，不在 "
                          "record 内掩藏。"),
    }
    disclosure_sha = _write_canonical(disclosure_path, disclosure)
    print(f"[s17-r2] 披露文件写出（branch={branch}）："
          f"raw-flags-repair-disclosure.json sha256={disclosure_sha[:16]}…")

    # ---- 4. 盘上实测 hash → ingest_run -------------------------------------
    actual = {"bundle": bundle_sha_disk, "raw_flags": raw_sha}
    for b in bundle["boards"]:
        pid = b["profile_id"]
        actual[f"source_board:{pid}"] = hashing.sha256_file(
            str(repo / b["source_board"]["path_rel"]))
        actual[f"profile:{pid}"] = hashing.sha256_file(
            str(repo / b["profile"]["path_rel"]))
        for r in b["renders"]:
            actual[f"render:{r['file_rel']}"] = hashing.sha256_file(
                str(run_dir / r["file_rel"]))
    result = critic_run.ingest_run(
        run_id=RUN_ID, bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=sidecar, actual_hashes=actual,
        approval_ok=approval_ok,
        provenance_hashes={"raw_flags_as_returned": orig_sha,
                           "raw_flags_repair_disclosure": disclosure_sha},
        **PREDICATES)
    rec = result["record"]
    print(f"[s17-r2] ingest 裁决：critic_status={rec['critic_status']} "
          f"outcome={rec['critic_outcome']} flags={len(rec['flags'])} "
          f"abstain={result['abstain_count']} "
          f"invalid_reasons={result['invalid_reasons']}")

    # ---- 5. 落盘 record / ledger / report ----------------------------------
    record_sha = _write_canonical(record_out, rec)
    if record_sha != result["record_sha256"]:
        _fail("record 落盘字节与 record_sha256 不符")
    events = result["ledger_events"]
    if queue.verify_chain(events) != []:
        _fail("queue-event-ledger 链校验失败")
    # 落盘口径与 decision-ledger.jsonl 惯例一致：每事件单行紧凑 JSON+换行
    ledger_bytes = "".join(
        json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n"
        for ev in events).encode("utf-8")
    ledger_out.write_bytes(ledger_bytes)
    reread = [json.loads(line) for line in
              ledger_out.read_text(encoding="utf-8").splitlines()]
    if queue.verify_chain(reread) != [] or len(reread) != len(events):
        _fail("ledger 落盘后复读校验失败")
    ledger_head = (events[-1]["event_sha256"] if events else None)
    ledger_sha = _sha_file(ledger_out) if events else None

    enum = schemas_enum()
    other_ok = "other_advisory" in enum
    other_flag_count = sum(1 for f in rec["flags"]
                           if f["category"] == "other_advisory")
    if branch == "repair":
        disc_summary = ("读取者原文不可解析（留证 as-returned.txt）；"
                        "ingest 输入=管线纯结构修复版（文末按括号栈单点"
                        "插入闭合字符，内容零改动零移动，difflib 守卫）；"
                        "两者 sha256 均绑进 record provenance/"
                        "evidence_refs。")
    else:
        disc_summary = ("读取者原文本身可解析（raw-flags.json=其 canonical "
                        "化重序列化，内容零改动，no_repair）；原文留证 "
                        "as-returned.txt；两者 sha256 均绑进 record "
                        "provenance/evidence_refs。")
    report = {
        "schema_version": "3.0",
        "kind": "tl2_critic_ingest_report",
        "run_id": RUN_ID,
        "inputs": {
            "bundle": {"path_rel": f"{run_rel}/critic-input-bundle.json",
                       "sha256": bundle_sha_disk, "sidecar_match": True},
            "approval": {"path_rel": critic_run.APPROVAL_PATH_REL,
                         "sha256": approval_sha,
                         "disposition_id": "APR-0005",
                         "duty_level": "advisory_only",
                         "anchor_ok": True},
            "raw_flags": {"path_rel": f"{run_rel}/raw-flags.json",
                          "sha256": raw_sha},
            "actual_hashes_checked": sorted(actual),
        },
        "validation": {
            "invalid_reasons": result["invalid_reasons"],
            "hashes_ok": rec["input_hashes_match"],
            "raw_schema_valid": rec["schema_validation"]["valid"],
        },
        "record": {
            "path_rel": f"{run_rel}/critic-run-record-CR-{RUN_ID}.json",
            "sha256": record_sha,
            "critic_run_id": rec["critic_run_id"],
            "critic_status": rec["critic_status"],
            "critic_outcome": rec["critic_outcome"],
            "advisory_only": rec["advisory_only"],
            "model": rec["model"],
            "flags_count": len(rec["flags"]),
            "abstain_count": result["abstain_count"],
            "evidence_refs": rec["evidence_refs"],
        },
        "other_advisory_enum_check": {
            "in_allowed_categories": other_ok,
            "allowed_categories": list(critic.FLAG_CATEGORIES),
            "source": ("critic.FLAG_CATEGORIES 与 schemas."
                       "critic_run_record flags.category 枚举一致；"
                       "未改枚举"),
            "other_advisory_flags_mapped": other_flag_count,
        },
        "triage": {
            "decision": result["triage"],
            "predicates": PREDICATES,
            "basis": PREDICATE_BASIS,
            "note": ("无论 eligible 与否，裁决依据=triage."
                     "failed_conditions（机器可读）+本 basis（人读）；"
                     "queue_deprioritized 只是分流不是质量 pass。"),
        },
        "queue": {
            "path_rel": f"{run_rel}/queue-event-ledger.jsonl",
            "sha256": ledger_sha,
            "event_count": len(events),
            "event_kinds": [ev["event"] for ev in events],
            "item_ids": [ev["item_id"] for ev in events],
            "head_event_sha256": ledger_head,
            "reason_codes": [ev.get("reason_code") for ev in events],
        },
        "disclosure": {
            "path_rel": f"{run_rel}/raw-flags-repair-disclosure.json",
            "sha256": disclosure_sha,
            "repair_kind": branch,
            "summary": disc_summary,
        },
    }
    report_sha = _write_canonical(report_out, report)
    print(f"[s17-r2] record={record_out.name} sha256={record_sha[:16]}… | "
          f"ledger {len(events)} 事件 head={str(ledger_head)[:16]}… | "
          f"report sha256={report_sha[:16]}…")
    print(f"[s17-r2] 入账完成（run-r2 advisory 扩样；branch={branch}）")
    return report


def _scan_open_brackets(text: str):
    """扫描未闭合括号栈（忽略字符串字面量与转义）；结构不可判定（多余
    闭合、字符串未闭合等）返回 None，闭合完全返回 []。"""
    stack = []
    in_str = False
    esc = False
    for ch in text:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                return None
            opener = stack.pop()
            if (opener == "{") != (ch == "}"):
                return None
    if in_str or esc:
        return None
    return stack


def _single_insertion_repair(orig_text: str) -> tuple:
    """机械纯单点插入修复：在文末按未闭合括号栈补齐缺失闭合序列。

    返回 (repaired_text, insert_at_char, inserted)；无法以纯插入修复
    （括号栈不可判定/补齐后仍不可解析）→ 拒绝入账 fail-closed。
    difflib 复验 0 删 0 改、单一插入点。
    """
    stack = _scan_open_brackets(orig_text)
    if not stack:
        _fail("读取者原文不可解析且无法以纯单点插入修复（括号栈为空或"
              "结构不可判定）：拒绝入账（fail-closed）")
    inserted = "".join("}" if op == "{" else "]" for op in reversed(stack))
    candidate = orig_text + inserted
    try:
        json.loads(candidate)
    except json.JSONDecodeError as exc:
        _fail(f"读取者原文不可解析且文末补齐闭合括号后仍不可解析"
              f"（{exc}）：无法以纯单点插入修复，拒绝入账（fail-closed）")
    ops = [op for op in difflib.SequenceMatcher(
        None, orig_text, candidate, autojunk=False).get_opcodes()
        if op[0] != "equal"]
    if len(ops) != 1 or ops[0][0] != "insert" \
            or ops[0][2] - ops[0][1] != 0:
        _fail(f"raw 修复差异非纯单点插入（ops={ops}）：拒绝入账——"
              "「内容字符零改动」不可证")
    _, i1, i2, j1, j2 = ops[0]
    return candidate, i1, candidate[j1:j2]


def _sha_file(path: Path) -> str:
    return hashing.sha256_file(str(path))


def schemas_enum() -> tuple:
    from pcbflow import schemas
    return tuple(schemas.SCHEMAS["critic_run_record"]["properties"]["flags"]
                 ["items"]["properties"]["category"]["enum"])


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "select":
        cmd_select()
    elif step == "render":
        cmd_render()
    elif step == "selfcheck":
        cmd_selfcheck()
    elif step == "observe":
        cmd_observe()
    elif step == "bundle":
        cmd_bundle()
    elif step == "ingest":
        cmd_ingest()
    else:
        _fail("用法：s17_run_r2.py select|render|selfcheck|observe|bundle"
              "|ingest")


if __name__ == "__main__":
    main()
