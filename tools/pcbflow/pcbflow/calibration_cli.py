"""参数化校准工具（REPAIR-P4 W-2；calibration 脚本族消重的新轮次正身）。

背景与边界（任务书 REPAIR-P4-ARCH-CONVERGENCE-TASKBOOK-2026-09-13 W-2）：
  - scripts/ 下 51+ 个 sNN_calibration_rN_{prep,compare,devrecord}.py 为逐轮
    复制演进的证据生成器（单 compare 5,200–6,400 LOC），**冻结不动**（其
    生成产物=冻结证据链）。
  - 本工具把「机制骨架」（源脚本委托装载、锚校验、聚合重放、防覆写护栏、
    历史对账）收敛为参数化形态：per-round 差异全部走 round 配置
    （pcbflow/calibration_rounds/*.json）——round id、源脚本、输入/产物
    路径、对账子树与值覆写。科学内容（假说/裁决/指引条款）属轮次研究
    设计，由 prep-record 等在案冻结件承载，本工具不复制。
  - 委托装载先例=scripts/s88b（importlib 复用 s88 纯函数）；聚合血统=
    calibration-run-r16–r25 同源比较脚本。

三形态：
  compare    装载源脚本 → engine.build_run() → （--reconcile 与历史
             run-record canonical 对账 / 缺省=同参重建自证+防覆写落盘骨架）
  devrecord  装载源脚本 → engine.build_dev_record() → 对账/重建同上
  validate   只做 round 配置与源脚本装载校验（零数据面执行）

fail-closed：配置缺失/坏 JSON/键缺失/源脚本装载失败/入口缺失 →
RoundConfigError / EngineError，无静默回落。

授权变更语境（G0 后世界）：历史 dev-record 嵌 protected 段
pcbflow/config.py 实测 sha；G0 授权变更（f515c348→acdfac49，登记=
out/repair-p4/anchor-hashes-post-g0.json）后重建嵌现役值，与冻结盘上件
对账须经 round 配置 reconcile.value_overrides 按登记件 before 值回放。
"""

from __future__ import annotations

import importlib.util
import json
import os

CALIBRATION_ROUND_SCHEMA_VERSION = "pcbflow-calibration-round/1.0"

_REQUIRED_KEYS = ("schema_version", "round_id", "kind", "source_script",
                  "record_rel")
_KINDS = ("prep", "compare", "devrecord")


class RoundConfigError(Exception):
    """round 配置装载失败（缺失/坏 JSON/键缺失/版本不符）——fail-closed。"""


class EngineError(Exception):
    """源脚本装载失败或构建入口缺失——fail-closed。"""


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_round_config(path: str) -> dict:
    try:
        with open(path, "rb") as f:
            cfg = json.loads(f.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoundConfigError("round_config_load_failed:%s (%s)"
                               % (path, exc)) from exc
    if not isinstance(cfg, dict):
        raise RoundConfigError("round_config_not_object:%s" % path)
    if cfg.get("schema_version") != CALIBRATION_ROUND_SCHEMA_VERSION:
        raise RoundConfigError(
            "round_config_schema_version_mismatch:%s got=%r want=%r"
            % (path, cfg.get("schema_version"),
               CALIBRATION_ROUND_SCHEMA_VERSION))
    missing = [k for k in _REQUIRED_KEYS if k not in cfg]
    if missing:
        raise RoundConfigError("round_config_missing_keys:%s %s"
                               % (path, ",".join(missing)))
    if cfg["kind"] not in _KINDS:
        raise RoundConfigError("round_config_kind_invalid:%s got=%r want one "
                               "of %r" % (path, cfg["kind"], _KINDS))
    return cfg


def load_source_engine(cfg: dict):
    """importlib 委托装载源脚本（模块级锚校验随装载执行；先例 s88b）。

    冻结纪律：源脚本只读装载，零回写；其 main()（落盘编排）不由本工具
    调用——compare/devrecord 只消费纯构建入口。

    历史语境重放（cfg["live_sha_context_overrides"]：rel→sha）：G0 授权
    变更（登记=out/repair-p4/anchor-hashes-post-g0.json）后，冻结 prep/
    dev-record 内嵌的历史锚与盘上实测失配是授权变更语境问题而非漂移。
    对账专用：装载后包装引擎 _sha，对声明 rel 按登记件 before 值回放
    （其余 rel 透传实测）。仅历史轮次对账配置可用；新轮次配置禁用
    （guards.historical_context_only 必须为真，validate 时校验）。
    """
    rel = cfg["source_script"]
    path = os.path.join(repo_root(), rel)
    if not os.path.isfile(path):
        raise EngineError("source_script_missing:%s" % path)
    name = "calib_engine_%s_%s" % (cfg["round_id"], cfg["kind"])
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001 —— 装载期任何失败均 fail-closed
        raise EngineError("source_engine_load_failed:%s (%s)"
                          % (path, exc)) from exc
    entry = cfg.get("engine_entry")
    if cfg["kind"] == "prep" and not entry:
        # prep 形态 G0 版=骨架级：装载校验+配置登记（派生任务解释器=下版；
        # 诚实边界：prep 实际落盘仍由 prep 脚本自身 main() 幂等自持，工具不代写）
        return None
    fn = getattr(mod, entry, None)
    if not callable(fn):
        raise EngineError("engine_entry_missing:%s::%s" % (rel, entry))
    overrides = cfg.get("live_sha_context_overrides") or {}
    if overrides:
        if not (cfg.get("guards") or {}).get("historical_context_only"):
            raise RoundConfigError(
                "live_sha_context_overrides_requires_historical_context_only:"
                + cfg["round_id"])
        orig_sha = getattr(mod, "_sha", None)
        if not callable(orig_sha):
            raise EngineError("engine_sha_hook_missing:%s" % rel)

        def _sha_historical(rel_path, _orig=orig_sha, _ov=dict(overrides)):
            norm = str(rel_path).replace("\\", "/")
            if norm in _ov:
                return _ov[norm]
            return _orig(rel_path)

        mod._sha = _sha_historical
    return fn


def build_record(cfg: dict) -> dict:
    """按 kind 调用引擎构建入口（纯函数、零写盘；prep 骨架无入口）。"""
    fn = load_source_engine(cfg)
    if fn is None:
        raise EngineError("engine_entry_absistent_for_kind:%s" % cfg["kind"])
    return fn()


# ---- 历史对账 ----------------------------------------------------------------

def _canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def _subtree(obj, dotted: str):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError(dotted)
            cur = cur[part]
        else:
            raise KeyError(dotted)
    return cur


def _apply_overrides(obj: dict, overrides: dict):
    """按点路径覆写（授权变更语境回放）；返回覆写后副本。"""
    if not overrides:
        return obj

    def rec(node, parts, value):
        if not parts:
            return value
        head, rest = parts[0], parts[1:]
        if isinstance(node, list):
            out = list(node)
            out[int(head)] = rec(out[int(head)], rest, value)
            return out
        out = dict(node)
        out[head] = rec(out[head], rest, value)
        return out

    for dotted, value in overrides.items():
        obj = rec(obj, dotted.split("."), value)
    return obj


def reconcile(rebuilt: dict, historical: dict, cfg: dict) -> dict:
    """重建 record 与历史冻结件 canonical 对账。

    子树清单=cfg["reconcile"]["subtrees"]（缺省=[""]，即整树）；覆写=
    cfg["reconcile"]["value_overrides"]（点路径→值，仅应用于重建侧——
    授权变更登记语境回放，见模块 docstring）。输出结构化对账报告。
    """
    rc = cfg.get("reconcile") or {}
    subtrees = rc.get("subtrees") or [""]
    overrides = rc.get("value_overrides") or {}
    rebuilt_o = _apply_overrides(rebuilt, overrides)
    rows, all_ok = [], True
    for st in subtrees:
        try:
            a = _subtree(rebuilt_o, st) if st else rebuilt_o
        except KeyError:
            rows.append({"subtree": st or "<root>", "status":
                         "MISSING_IN_REBUILT"})
            all_ok = False
            continue
        try:
            b = _subtree(historical, st) if st else historical
        except KeyError:
            rows.append({"subtree": st or "<root>", "status":
                         "MISSING_IN_HISTORICAL"})
            all_ok = False
            continue
        ok = _canon(a) == _canon(b)
        all_ok = all_ok and ok
        rows.append({"subtree": st or "<root>",
                     "status": "match" if ok else "diff",
                     "size": len(_canon(a))})
    return {"round_id": cfg["round_id"], "kind": cfg["kind"],
            "record_rel": cfg["record_rel"],
            "value_overrides_applied": sorted(overrides),
            "all_match": all_ok, "subtrees": rows}


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="calibration_cli",
                                 description="参数化校准工具（REPAIR-P4 W-2）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare", help="装载源脚本重放 build_run（纯内存）")
    c.add_argument("--config", required=True, help="round 配置 JSON 路径")
    c.add_argument("--reconcile", default=None, metavar="HIST_JSON",
                   help="历史冻结 record 路径（缺省盘上 record_rel；"
                        "'-' = 只重建不对账）")
    d = sub.add_parser("devrecord", help="装载源脚本重建 build_dev_record")
    d.add_argument("--config", required=True)
    d.add_argument("--reconcile", default=None, metavar="HIST_JSON")
    v = sub.add_parser("validate", help="配置+源脚本装载校验（零数据面）")
    v.add_argument("--config", required=True)
    args = ap.parse_args(argv)

    cfg = load_round_config(args.config)
    if args.cmd == "validate":
        load_source_engine(cfg)
        print(json.dumps({"status": "ok", "round_id": cfg["round_id"],
                          "kind": cfg["kind"],
                          "source_script": cfg["source_script"]},
                         ensure_ascii=False, sort_keys=True))
        return 0
    rebuilt = build_record(cfg)
    hist_rel = args.reconcile
    if hist_rel in (None, "-"):
        if hist_rel is None:
            hist_rel = os.path.join(repo_root(), cfg["record_rel"])
        else:
            print(json.dumps({"status": "ok", "round_id": cfg["round_id"],
                              "rebuilt_bytes": len(_canon(rebuilt))},
                             ensure_ascii=False, sort_keys=True))
            return 0
    with open(hist_rel, "rb") as f:
        historical = json.loads(f.read().decode("utf-8"))
    report = reconcile(rebuilt, historical, cfg)
    print(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True))
    return 0 if report["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
