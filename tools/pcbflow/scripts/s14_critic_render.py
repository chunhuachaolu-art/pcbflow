#!/usr/bin/env python
"""S14-TL2 编排（第一段）：Critic 渲染管线 + 输入 bundle（写 out/v3-tl2/）。

编排侧职责（库侧 pcbflow/critic_run.py 保持零子进程零落盘）：

  render   选板（1 train + 1 holdout）→ datasets raw 参考 routed 态 staging
           拷贝（逐字节 sha256 断言）→ kicad-cli pcb render 顶/底 4 张 PNG
           → render-manifest.json（visual_check=pending）。
  observe  从 stdin 读 {render 文件名: 观感一句话}；复验渲染与 staging
           hash 未漂移后把人工亲读观感写入 manifest（visual_check=done）。
  bundle   以 pcbflow.critic_run.build_input_bundle 构建 critic-input-
           bundle.json（canonical、byte-exact 复验）+ sidecar sha256；
           收尾清理 staging。

纪律：既有 out/ 只读——新产物只进 out/v3-tl2/；datasets/ 只读；
manifest/bundle 无 wall-clock 无主机路径；发布产物防覆写（已存在即拒绝）。

用法（仓库根执行）：
  python scripts/s14_critic_render.py render
  python scripts/s14_critic_render.py observe   < observations.json (stdin)
  python scripts/s14_critic_render.py bundle
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import critic_run, hashing            # noqa: E402

RUN_ID = "run-r1"
OUT = REPO / "out" / "v3-tl2"
RUN_DIR = OUT / "critic-runs" / RUN_ID
RENDERS_DIR = RUN_DIR / "renders"
STAGING_DIR = RUN_DIR / "staging"
MANIFEST = RUN_DIR / "render-manifest.json"
BUNDLE = RUN_DIR / "critic-input-bundle.json"
SIDECAR = RUN_DIR / "critic-input-bundle.sha256"

# 编排侧可执行（仅本脚本引用；不写入任何产物）
KICAD_CLI = Path(r"F:\kicad\bin\kicad-cli.exe")
KICAD_VERSION = "10.0.5"
RENDER_SIZE = (1600, 900)          # 请求尺寸（实测本机恒输出 1568x872）
MIN_SIZE = (1200, 675)             # 可读性下限（低于即 blocked）
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

#: 选板规则（split 归属以 profiles/<id>/manifest.json dataset_splits 为准）
SELECTION_RULE = (
    "1 train + 1 holdout（split 归属以 profiles/<id>/manifest.json "
    "dataset_splits 为准）：train=pcbench-launchxl-f28027-isolation-pcb-"
    "project1（2 层小板，net 声明 0–12 共 13 条）；holdout=pcbbm-bm11"
    "（2 层）。两板均取 datasets raw 参考 routed 态（profile manifest "
    "reference_route 指向文件），staging 逐字节断言后 kicad-cli "
    f"{KICAD_VERSION} pcb render 出顶/底 PNG。")

BOARDS = [
    {
        "profile_id": "pcbench-launchxl-f28027-isolation-pcb-project1",
        "split": "train",
        "split_basis": ("profiles/pcbench-launchxl-f28027-isolation-pcb-"
                        "project1/manifest.json dataset_splits.train 含 "
                        "LAUNCHXL-F28027-isolation-PCB_project1"),
        "source_rel": ("datasets/pcbench-r1/raw/"
                       "LAUNCHXL-F28027-isolation-PCB_project1/raw.kicad_pcb"),
        "staged_name": "launchxl-routed.kicad_pcb",
        "prefix": "launchxl",
    },
    {
        "profile_id": "pcbbm-bm11",
        "split": "holdout",
        "split_basis": ("profiles/pcbbm-bm11/manifest.json "
                        "dataset_splits.holdout 含 bm11"),
        "source_rel": ("datasets/pcbbenchmarks-r1/raw/bm11/"
                       "bm11.routed.kicad_pcb"),
        "staged_name": "bm11-routed.kicad_pcb",
        "prefix": "bm11",
    },
]

APPROVAL_REL = critic_run.APPROVAL_PATH_REL


def _fail(msg: str) -> None:
    print(f"[s14-critic] FAIL: {msg}")
    sys.exit(1)


def _write_canonical(path: Path, obj) -> str:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def _png_size(path: Path) -> tuple:
    data = path.read_bytes()
    if not data.startswith(PNG_MAGIC):
        _fail(f"{path.name}: 不是 PNG（magic 不符）")
    if len(data) < 33:
        _fail(f"{path.name}: 文件过小（{len(data)}B）")
    w, h = struct.unpack(">II", data[16:24])
    return w, h


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def cmd_render() -> None:
    if MANIFEST.exists():
        _fail(f"{MANIFEST.name} 已存在（防覆写；发布产物不可覆写）")
    if not KICAD_CLI.exists():
        _fail(f"kicad-cli 不存在：{KICAD_CLI}")
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    boards_out = []
    for b in BOARDS:
        src = REPO / b["source_rel"]
        if not src.exists():
            _fail(f"参考 routed 态缺失：{b['source_rel']}")
        src_sha = hashing.sha256_file(str(src))
        staged = STAGING_DIR / b["staged_name"]
        shutil.copyfile(src, staged)
        staged_sha = hashing.sha256_file(str(staged))
        if staged_sha != src_sha:
            _fail(f"staging 逐字节断言失败：{b['staged_name']} "
                  f"{staged_sha} != 源 {src_sha}")
        renders = []
        for side in ("top", "bottom"):
            name = f"{b['prefix']}-{side}.png"
            out_png = RENDERS_DIR / name
            if out_png.exists():
                _fail(f"{name} 已存在（防覆写）")
            cmd = ["kicad-cli", "pcb", "render", "--side", side,
                   "--width", str(RENDER_SIZE[0]),
                   "--height", str(RENDER_SIZE[1]),
                   "--background", "opaque", "--quality", "basic",
                   "-o", f"renders/{name}",
                   f"staging/{b['staged_name']}"]
            # 以 RUN_DIR 为 cwd：记录的命令即实际执行（产物禁主机路径）
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
            print(f"[s14-critic] render ok: {name} "
                  f"{out_png.stat().st_size}B {w}x{h}")
        boards_out.append({
            "profile_id": b["profile_id"], "split": b["split"],
            "split_basis": b["split_basis"],
            "source": {"path_rel": b["source_rel"], "sha256": src_sha},
            "staged_copy": {"path_rel":
                            f"staging/{b['staged_name']}",
                            "sha256": staged_sha, "byte_exact_match": True},
            "renders": renders,
        })
    manifest = {
        "schema_version": "3.0",
        "kind": "tl2_critic_render_manifest",
        "run_id": RUN_ID,
        "selection_rule": SELECTION_RULE,
        "boards": boards_out,
        "visual_check": "pending",
        "note": ("observation 由执行工程师用 Read 工具逐张亲读后经 "
                 "observe 步骤写入；visual_check=pending 期间不得构建 "
                 "bundle。"),
    }
    sha = _write_canonical(MANIFEST, manifest)
    print(f"[s14-critic] manifest 写出（visual_check=pending）：{sha[:16]}…")
    print("[s14-critic] 下一步：用 Read 逐张查看 4 张 PNG，再跑 observe。")


# ---------------------------------------------------------------------------
# observe
# ---------------------------------------------------------------------------

def cmd_observe() -> None:
    if not MANIFEST.exists():
        _fail("render-manifest.json 不存在（先跑 render）")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("visual_check") == "done":
        _fail("visual_check 已 done（防覆写）")
    try:
        obs = json.load(sys.stdin)
    except Exception as exc:                      # noqa: BLE001
        _fail(f"stdin 不是合法 JSON：{exc}")
    if not isinstance(obs, dict):
        _fail("stdin JSON 必须为对象 {render 文件名: 观感一句话}")
    all_files = [r["file_rel"].split("/", 1)[1]
                 for b in manifest["boards"] for r in b["renders"]]
    missing = [f for f in all_files if f not in obs]
    extra = [k for k in obs if k not in all_files]
    if missing or extra:
        _fail(f"观感键不齐：missing={missing} extra={extra}")
    for b in manifest["boards"]:
        # 复验：staging 与源仍逐字节一致、渲染文件 hash 未漂移
        src = REPO / b["source"]["path_rel"]
        if hashing.sha256_file(str(src)) != b["source"]["sha256"]:
            _fail(f"datasets 源 hash 漂移：{b['source']['path_rel']}")
        staged = RUN_DIR / b["staged_copy"]["path_rel"]
        if not staged.exists() or (hashing.sha256_file(str(staged))
                                   != b["staged_copy"]["sha256"]):
            _fail(f"staging hash 漂移：{staged.name}")
        for r in b["renders"]:
            png = RUN_DIR / r["file_rel"]
            if hashing.sha256_file(str(png)) != r["sha256"]:
                _fail(f"渲染文件 hash 漂移：{r['file_rel']}")
            text = str(obs[r["file_rel"].split("/", 1)[1]]).strip()
            if not text:
                _fail(f"{r['file_rel']}: 观感为空（必须亲读后填写）")
            r["observation"] = text
    manifest["visual_check"] = "done"
    sha = _write_canonical(MANIFEST, manifest)
    print(f"[s14-critic] manifest 更新（visual_check=done）：{sha[:16]}…")


# ---------------------------------------------------------------------------
# bundle
# ---------------------------------------------------------------------------

def cmd_bundle() -> None:
    if BUNDLE.exists() or SIDECAR.exists():
        _fail("bundle/sidecar 已存在（防覆写）")
    if not MANIFEST.exists():
        _fail("render-manifest.json 不存在（先跑 render+observe）")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("visual_check") != "done":
        _fail("visual_check 未 done（先逐张亲读 PNG 并 observe）")
    approval_path = REPO / APPROVAL_REL
    if not approval_path.exists():
        _fail(f"APR-0005 disposition 缺失：{APPROVAL_REL}")
    approval_sha = hashing.sha256_file(str(approval_path))
    apr = json.loads(approval_path.read_text(encoding="utf-8"))
    if apr.get("disposition_id") != critic_run.APPROVAL_DISPOSITION_ID \
            or "advisory" not in str(apr.get("rationale_code", "")):
        _fail("APR-0005 disposition 内容与 advisory_only 裁决不符")

    boards = []
    for b in manifest["boards"]:
        pid = b["profile_id"]
        profile_path = REPO / "profiles" / pid / "profile.json"
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
    bundle = critic_run.build_input_bundle(
        run_id=RUN_ID, selection_rule=manifest["selection_rule"],
        boards=boards, approval_sha256=approval_sha,
        calibration_domain_established=False)
    data = hashing.canonical_json_bytes(bundle)
    rebuilt = hashing.canonical_json_bytes(json.loads(data.decode("utf-8")))
    if data != rebuilt:
        _fail("bundle byte-exact 复验失败（canonical 往返不一致）")
    sha = hashing.sha256_bytes(data)
    BUNDLE.write_bytes(data)
    SIDECAR.write_bytes((sha + "\n").encode("utf-8"))
    print(f"[s14-critic] bundle 写出：critic-input-bundle.json "
          f"sha256={sha[:16]}…（sidecar 同值）")
    # 收尾：清理 staging
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
        print("[s14-critic] staging 已清理")
    leftover = sorted(p.name for p in RUN_DIR.rglob("*") if "staging" in
                      str(p.relative_to(RUN_DIR)).split("/")[0] and
                      p.is_file())
    if leftover:
        _fail(f"staging 残留：{leftover}")


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "render":
        cmd_render()
    elif step == "observe":
        cmd_observe()
    elif step == "bundle":
        cmd_bundle()
    else:
        _fail("用法：s14_critic_render.py render|observe|bundle")


if __name__ == "__main__":
    main()
