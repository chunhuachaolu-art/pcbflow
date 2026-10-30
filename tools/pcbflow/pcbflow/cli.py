"""pcbflow 命令面。生成器模式：stdout 输出、零落盘、零子进程。

用法（产物落盘由 shell 重定向完成）：
  python -m pcbflow.cli compile --select constraints  > constraints.json
  python -m pcbflow.cli compile --select coverage     > coverage.json
  python -m pcbflow.cli compile --select impedance_targets > impedance_targets.json
  python -m pcbflow.cli compile --select envelope     > envelope.json
  python -m pcbflow.cli compile --select run_manifest > run_manifest.json
  python -m pcbflow.cli compile --select summary      （门核对摘要，人读）
  python -m pcbflow.cli enum    --select structures   > structures.json     （FA2 草案）
  python -m pcbflow.cli enum    --select net_registry > net-registry.json   （FA3 v1.2 adoption）
  python -m pcbflow.cli enum    --select net_identity_map > net-identity-map.json
  python -m pcbflow.cli enum    --select coverage     > coverage-structures.json
  python -m pcbflow.cli enum    --select envelope     > envelope-enum.json
  python -m pcbflow.cli enum    --select run_manifest > run-manifest-enum.json
  python -m pcbflow.cli audit   --select audit        > audit.json          （FA3）
  python -m pcbflow.cli audit   --select pin_swap     > pin-swap.json
  python -m pcbflow.cli audit   --select skeleton_seed > skeleton-seed.json
  python -m pcbflow.cli audit   --select envelope     > envelope-audit.json
  python -m pcbflow.cli audit   --select run_manifest > run-manifest-audit.json
  python -m pcbflow.cli audit   --select summary      （三门核对摘要，人读）
  python -m pcbflow.cli co-place --select layout      > layout.json         （FB1）
  python -m pcbflow.cli co-place --select geojson     > skeletons.geojson
  python -m pcbflow.cli co-place --select layer_plan  > layer-plan.json
  python -m pcbflow.cli co-place --select placement_csv > placement.csv
  python -m pcbflow.cli co-place --select conversion  > conversion.json
  python -m pcbflow.cli co-place --select envelope    > envelope-coplace.json
  python -m pcbflow.cli co-place --select run_manifest > run-manifest-coplace.json
  python -m pcbflow.cli co-place --select summary     （证据向量摘要，人读）
  python -m pcbflow.cli feedforward --select plan       > feedforward-plan.json      （FF1）
  python -m pcbflow.cli feedforward --select coverage   > feedforward-coverage.json
  python -m pcbflow.cli feedforward --select comparison > feedforward-comparison.json
  python -m pcbflow.cli feedforward --select envelope   > feedforward-envelope.json
  python -m pcbflow.cli feedforward --select run_manifest > feedforward-run-manifest.json
  python -m pcbflow.cli feedforward --select report     > feedforward-report.md（人读）
  python -m pcbflow.cli feedforward --select baseline_freeze > baseline-freeze.json（FF-0）
  python -m pcbflow.cli feedforward --select summary    （FF 门摘要，人读）
  python -m pcbflow.cli feedforward --adopt-override --select plan \
        --out-dir out/revc-fd2 > feedforward-plan.json（FD2 adoption 重跑）
  python -m pcbflow.cli feedforward --adopt-override --select impedance_targets \
        --out-dir out/revc-fd2 > impedance-targets.json（叠层基面重算）
  python -m pcbflow.cli feedforward --adopt-override --consume-bom --select plan \
        --out-dir out/revc-fd3 > feedforward-plan.json（FF3 BOM 派生轨表消费）
  python -m pcbflow.cli editor --select html        > editor.html          （FB2）
  python -m pcbflow.cli editor --select envelope    > envelope-editor.json
  python -m pcbflow.cli editor --select run_manifest > run-manifest-editor.json
  python -m pcbflow.cli editor --select validate --proposal <editor-proposal.json>
                                                        > validation.json（提案校验）
  python -m pcbflow.cli editor --select summary     （编辑器门摘要，人读）
  python -m pcbflow.cli route   --select route_view   > route-view.json       （FC1）
  python -m pcbflow.cli route   --select route_plan   > route-plan.json
  python -m pcbflow.cli route   --select consumption  > route-consumption.json（需 --feedforward-plan）
  python -m pcbflow.cli route   --select envelope     > envelope-route.json
  python -m pcbflow.cli route   --select run_manifest > run-manifest-route.json
  python -m pcbflow.cli route   --select report       > route-report.md（人读）
  python -m pcbflow.cli route   --select summary      （§16.4 dry-run 门摘要，人读）
  python -m pcbflow.cli residual --select residual    > residual-certs.json （FC2 靶 1）
  python -m pcbflow.cli residual --select replay      > replay-plan.json    （FC2 靶 2）
  python -m pcbflow.cli residual --select replay_board --stage placement   > 板文本（副本写路径）
  python -m pcbflow.cli residual --select replay_board --max-batch k      > 板文本（副本写路径）
  python -m pcbflow.cli residual --select envelope    > envelope-route-fc2.json
  python -m pcbflow.cli residual --select run_manifest > run-manifest-route-fc2.json
  python -m pcbflow.cli residual --select report      > route-fc2-report.md（人读）
  python -m pcbflow.cli residual --select summary     （FC2 门摘要，人读）
  python -m pcbflow.cli check   --select checker_registry > checker-registry.json（FD1）
  python -m pcbflow.cli check   --select check_report     > check-report.json
  python -m pcbflow.cli check   --select ff_residuals     > ff-residuals.json（§11.2）
  python -m pcbflow.cli check   --select probe_board --probe probe-width
                                                        > 探针板文本（编排侧 kicad-cli）
  python -m pcbflow.cli check   --select probe_project --probe probe-width
                                                        > 探针 .kicad_pro 文本
  python -m pcbflow.cli check   --select probe_battery --probe-drc-dir <dir>
                                                        > probe-battery.json
  python -m pcbflow.cli check   --select envelope     > envelope-check.json
  python -m pcbflow.cli check   --select report       > check-report.md（人读）
  python -m pcbflow.cli check   --select summary      （⑤ 门摘要，人读）
  python -m pcbflow.cli check   --ff-plan-dir out/revc-fd2 --select ff_residuals \
        --out-dir out/revc-fd2 > ff-residuals.json（FD2 计划消费）
  python -m pcbflow.cli signoff --select package      > signoff-package.json（FD1）
  python -m pcbflow.cli signoff --ff-plan-dir out/revc-fd2 --check-dir out/revc-fd2 \
        --approvals-dir out/revc-fd1/approvals --adopt-override \
        --session-tag FD2 --select package --out-dir out/revc-fd2 \
        > signoff-package.json（FD2 级联重跑）
  python -m pcbflow.cli signoff --select waiver_ledger > waiver-ledger.json（§12.1）
  python -m pcbflow.cli signoff --select replay       > signoff-replay.json（§12.2）
  python -m pcbflow.cli signoff --select envelope     > envelope-signoff.json
  python -m pcbflow.cli signoff --select report       > signoff-report.md（人读）
  python -m pcbflow.cli signoff --select summary      （⑥ 门摘要，人读）
  python -m pcbflow.cli copper mirror --base <板> --out out/copper-loop-r1 \
        [--registry <net-registry.json>] [--patch-set <patch-set.json>]
                                                        铜箔↔SVG 闭环一轮（R1）
  python -m pcbflow.cli copper patch --revision-dir <rev-N> --patch-set <json>
  python -m pcbflow.cli copper verify --manifest <route-manifest.json> \
        --svg <board.svg> [--board <板>] [--registry <json>]
  python -m pcbflow.cli copper accept --revision-dir <rev-N> --drc-report <json>
  python -m pcbflow.cli copper rollback --revision-dir <rev-N>
  python -m pcbflow.cli copper adopt --revision-dir <rev-N> --design-board <板>
        （copper 记录类子命令的 stdout = 该轮 revision-record.json 原文；
          DRC 由编排侧 kicad-cli 执行 —— pcbflow 零子进程，本命令只产请求/
          消费报告）

exit-code 契约（config.py）：
  0=ok 1=failed 2=blocked 3=unknown 4=not_implemented（命令仍 specified）
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import audit_cmd, compile_cmd, config, coplace_cmd, editor_cmd, envelope
from . import check_cmd, enum_cmd, signoff_cmd
from . import feedforward, hashing, residual_cmd, route_cmd

PRODUCTS = ("constraints", "coverage", "impedance_targets", "envelope", "run_manifest")
ENUM_PRODUCTS = ("structures", "coverage", "net_registry", "net_identity_map",
                 "envelope", "run_manifest")
# 落盘文件名与产物名解耦（带连字符的历史命名沿用）
AUDIT_FILENAMES = {"audit": "audit.json", "pin_swap": "pin-swap.json",
                   "skeleton_seed": "skeleton-seed.json", "envelope": "envelope-audit.json",
                   "run_manifest": "run-manifest-audit.json"}
AUDIT_PRODUCTS = tuple(AUDIT_FILENAMES)
COPRODUCTS = ("layout", "geojson", "layer_plan", "placement_csv", "conversion",
              "ff_consumption", "envelope", "run_manifest")
FF_FILENAMES = {"plan": "feedforward-plan.json", "coverage": "feedforward-coverage.json",
                "comparison": "feedforward-comparison.json",
                "envelope": "feedforward-envelope.json",
                "run_manifest": "feedforward-run-manifest.json",
                "baseline_freeze": "baseline-freeze.json",
                "impedance_targets": "impedance-targets.json"}
FF_PRODUCTS = tuple(FF_FILENAMES)
EDITOR_PRODUCTS = ("html", "envelope", "run_manifest")
ROUTE_FILENAMES = {"route_view": "route-view.json", "route_plan": "route-plan.json",
                   "consumption": "route-consumption.json",
                   "envelope": "envelope-route.json",
                   "run_manifest": "run-manifest-route.json"}
ROUTE_PRODUCTS = tuple(ROUTE_FILENAMES)
RESIDUAL_PRODUCTS = ("residual", "replay", "envelope", "run_manifest")
RESIDUAL_TEXT_PRODUCTS = ("replay_board", "report")
CHECK_PRODUCTS = ("checker_registry", "check_report", "ff_residuals",
                  "probe_battery", "envelope", "run_manifest")
CHECK_TEXT_PRODUCTS = ("probe_board", "probe_project", "report")
SIGNOFF_PRODUCTS = ("package", "waiver_ledger", "replay", "envelope",
                    "run_manifest")
SIGNOFF_TEXT_PRODUCTS = ("report",)


def _emit(obj) -> None:
    sys.stdout.buffer.write(hashing.canonical_json_bytes(obj))
    sys.stdout.buffer.flush()


def _status_exit(status: str) -> int:
    return {"ok": config.EXIT_OK, "failed": config.EXIT_FAILED,
            "blocked": config.EXIT_BLOCKED, "unknown": config.EXIT_UNKNOWN}[status]


def cmd_compile(args) -> int:
    products = compile_cmd.build_products(out_dir_rel=args.out_dir)
    env = products["envelope"]["obj"]
    if args.select == "summary":
        _emit({
            "command": "compile", "status": env["status"], "verdict": env["verdict"],
            "metrics": env["metrics"], "diagnostics": env["diagnostics"],
            "gate": env["data"]["gate"],
            "artifacts": env["artifacts"],
            "note": "人读视图非事实源；核心产物见 constraints/coverage/impedance_targets",
        })
    else:
        _emit(products[args.select]["obj"])
    return _status_exit(env["status"])


def cmd_enum(args) -> int:
    products = enum_cmd.build_products(out_dir_rel=args.out_dir)
    env = products["envelope"]["obj"]
    if args.select == "summary":
        _emit({
            "command": "enum", "status": env["status"], "verdict": env["verdict"],
            "metrics": env["metrics"], "diagnostics": env["diagnostics"],
            "gate": env["data"]["gate"], "artifacts": env["artifacts"],
            "note": "人读视图非事实源；核心产物见 structures/coverage/net-registry",
        })
    else:
        _emit(products[args.select]["obj"])
    return _status_exit(env["status"])


def cmd_audit(args) -> int:
    products = audit_cmd.build_products(out_dir_rel=args.out_dir,
                                        af_table_path=args.af_table)
    env = products["envelope"]["obj"]
    if args.select == "summary":
        _emit({
            "command": "audit", "status": env["status"], "verdict": env["verdict"],
            "metrics": env["metrics"], "diagnostics": env["diagnostics"],
            "gate": env["data"]["gate"], "artifacts": env["artifacts"],
            "note": "人读视图非事实源；核心产物见 audit/pin-swap/skeleton-seed",
        })
    else:
        _emit(products[args.select]["obj"])
    return _status_exit(env["status"])


def cmd_coplace(args) -> int:
    if args.select == "ff_consumption" and not args.feedforward_plan:
        _emit({"command": "co-place", "status": "failed", "error":
               "ff_consumption 需要 --feedforward-plan <feedforward-plan.json 路径>"})
        return config.EXIT_FAILED
    products = coplace_cmd.build_products(out_dir_rel=args.out_dir,
                                          ff_plan_path=args.feedforward_plan)
    env = products["envelope"]["obj"]
    if args.select == "summary":
        ev = env["metrics"]
        _emit({
            "command": "co-place", "status": env["status"], "verdict": env["verdict"],
            "metrics": env["metrics"], "diagnostics": env["diagnostics"],
            "gate": env["data"]["gate"], "artifacts": env["artifacts"],
            "note": "人读视图非事实源；核心产物见 layout/skeletons.geojson/layer-plan；"
                    "优化与转换执行待人工批准（确认点 #4）",
        })
    elif args.select == "placement_csv":
        sys.stdout.buffer.write(products["placement_csv"]["bytes"])
        sys.stdout.buffer.flush()
    else:
        _emit(products[args.select]["obj"])
    return _status_exit(env["status"])


def cmd_feedforward(args) -> int:
    """FF-0..FF-2（PATCH-PROMPT-FF1 §2-§4）：账本/比较/冻结；planning_advisory。

    --adopt-override：FD2 adoption 级联重跑（structures.override 权威生效+
    能力/叠层/电流三源消费；新 plan_id=FF-REVC-0002+impedance-targets 产物；
    默认关=FF1 收官口径 byte 不变）。
    --consume-bom：FF3 级联重跑（需 --adopt-override；BOM 派生轨功耗表
    derived 消费，plan_id=FF-REVC-0003）。
    --placement-csv：CAS1 级联收口（需 --adopt-override；确认点 #4 已批）
    ——placement 六 hash 绑定切至采纳快照（plan_id=FF-REVC-0004；
    --placement-layout 登记 it-layout provenance）。"""
    if args.select == "baseline_freeze":
        env = feedforward.build_baseline_freeze()
        _emit(env)
        return _status_exit(env["status"])
    if getattr(args, "consume_bom", False) and not args.adopt_override:
        _emit({"command": "feedforward", "status": "failed",
               "error": "--consume-bom 需 --adopt-override（BOM 消费建立在 "
                        "FD2 adoption 基准上）"})
        return config.EXIT_FAILED
    if getattr(args, "placement_csv", None) and not args.adopt_override:
        _emit({"command": "feedforward", "status": "failed",
               "error": "--placement-csv 需 --adopt-override（采纳绑定建立在 "
                        "FD2 adoption 基准上）"})
        return config.EXIT_FAILED
    if getattr(args, "placement_layout", None) \
            and not getattr(args, "placement_csv", None):
        _emit({"command": "feedforward", "status": "failed",
               "error": "--placement-layout 需 --placement-csv（采纳布局"
                        "provenance 依附采纳快照绑定）"})
        return config.EXIT_FAILED
    if getattr(args, "bom_power_file", None) \
            and not getattr(args, "consume_bom", False):
        _emit({"command": "feedforward", "status": "failed",
               "error": "--bom-power-file 需 --consume-bom（FF5 rail 源覆盖"
                        "建立在 BOM 消费口径上）"})
        return config.EXIT_FAILED
    products = feedforward.build_products(
        out_dir_rel=args.out_dir, adopt_override=args.adopt_override,
        consume_bom=getattr(args, "consume_bom", False),
        placement_csv=getattr(args, "placement_csv", None),
        placement_layout=getattr(args, "placement_layout", None),
        bom_power_file=getattr(args, "bom_power_file", None))
    env = products["envelope"]["obj"]
    if args.select == "summary":
        _emit({
            "command": "feedforward", "status": env["status"],
            "verdict": env["verdict"], "command_kind": env.get("command_kind"),
            "metrics": env["metrics"], "diagnostics": env["diagnostics"],
            "gate": env["data"]["gate"], "artifacts": env["artifacts"],
            "note": "人读视图非事实源；核心产物见 feedforward-plan/coverage/"
                    "comparison；authority=planning_advisory（red≠架构致命）",
        })
    elif args.select == "report":
        sys.stdout.buffer.write(products["report"]["bytes"])
        sys.stdout.buffer.flush()
    elif args.select == "impedance_targets":
        if not args.adopt_override:
            _emit({"command": "feedforward", "status": "failed",
                   "error": "impedance_targets 需 --adopt-override"
                            "（叠层基面重算=FD2 adoption 产物）"})
            return config.EXIT_FAILED
        _emit(products["impedance_targets"]["obj"])
    else:
        _emit(products[args.select]["obj"])
    return _status_exit(env["status"])


def cmd_editor(args) -> int:
    """FB2 E 简版骨架编辑器：html/envelope/run_manifest/validate（零写板）。"""
    if args.select == "validate":
        if not args.proposal:
            _emit({"command": "editor", "status": "failed", "error":
                   "validate 需要 --proposal <editor-proposal.json 路径>"})
            return config.EXIT_FAILED
        env, _report = editor_cmd.validate_proposal(args.proposal,
                                                    out_dir_rel=args.out_dir)
        _emit(env)
        return _status_exit(env["status"])
    products = editor_cmd.build_products(out_dir_rel=args.out_dir)
    env = products["envelope"]["obj"]
    if args.select == "summary":
        _emit({
            "command": "editor", "status": env["status"], "verdict": env["verdict"],
            "command_kind": env.get("command_kind"),
            "metrics": env["metrics"], "diagnostics": env["diagnostics"],
            "gate": env["data"]["gate"], "artifacts": env["artifacts"],
            "note": "人读视图非事实源；编辑器零写板，提案须重过 ③ 门+人工批准"
                    "（确认点 #4）；validate 见 validation.json",
        })
    elif args.select == "html":
        sys.stdout.buffer.write(products["html"]["bytes"])
        sys.stdout.buffer.flush()
    else:
        _emit(products[args.select]["obj"])
    return _status_exit(env["status"])


def cmd_route(args) -> int:
    """FC1 ④ 匝道/车道 dry-run（内存；零写板；§16.4）。"""
    if args.select == "consumption" and not args.feedforward_plan:
        _emit({"command": "route", "status": "failed", "error":
               "consumption 需要 --feedforward-plan <feedforward-plan.json 路径>"
               "（未绑计划时 ④ 控制面无计划可消费）"})
        return config.EXIT_FAILED
    products = route_cmd.build_products(out_dir_rel=args.out_dir,
                                        ff_plan_path=args.feedforward_plan,
                                        placement_layout_path=getattr(
                                            args, "placement_from_layout",
                                            None))
    env = products["envelope"]["obj"]
    if args.select == "summary":
        g = env["data"]["gate"]
        pb = products["route_plan"]["obj"]["plan_binding"]
        auth = ("upgraded_for_candidate_acceptance（consumer-gate-4）"
                if str(pb["authority_effective"]).startswith("upgraded")
                else "planning_advisory")
        _emit({
            "command": "route", "status": env["status"], "verdict": env["verdict"],
            "metrics": env["metrics"], "diagnostics": env["diagnostics"],
            "gate_16_4": g, "solver": env["solver"], "artifacts": env["artifacts"],
            "note": "人读视图非事实源；核心产物见 route-view/route-plan/"
                    "route-consumption；authority=%s（dry-run 零写板）；"
                    "描线/残网=FC2" % auth,
        })
    elif args.select == "report":
        sys.stdout.buffer.write(products["report"]["bytes"])
        sys.stdout.buffer.flush()
    else:
        _emit(products[args.select]["obj"])
    return _status_exit(env["status"])


def cmd_keepout_iter(args) -> int:
    """IT ③ keepout-aware 重优化（KEEPOUT-EVIDENCE 立项；锚件不动；零写板）。"""
    from . import keepout_iter
    products = keepout_iter.build_products(
        out_dir_rel=args.out_dir,
        ff_plan_path=args.feedforward_plan,
        baseline_route_plan=args.baseline_route_plan,
        max_sweeps=args.max_sweeps,
        refs=([r.strip() for r in args.refs.split(",") if r.strip()]
              if args.refs else None))
    env = products["envelope"]["obj"]
    if args.select == "summary":
        _emit({
            "command": "keepout-iter", "status": env["status"],
            "verdict": env["verdict"], "metrics": env["metrics"],
            "diagnostics": env["diagnostics"], "gate": env["data"]["gate"],
            "artifacts": env["artifacts"],
            "note": "人读视图非事实源；核心产物见 keepout-iteration.json/"
                    "it-layout.json；转换执行待批（确认点 #4）；算法实验门"
                    "≠项目交付门",
        })
    else:
        _emit(products[args.select]["obj"])
    return _status_exit(env["status"])


def cmd_residual(args):
    """FC2 两靶（§10.6/§15）：靶 1 残网证书化回测；靶 2 ③ 重放板实战。

    replay_board/report 为文本产物（stdout 重定向落盘；板文本仅限快照副本
    写路径，pre/post hash 由编排侧记账）。"""
    if args.select == "replay_board" and args.stage != "placement" \
            and args.max_batch is None:
        _emit({"command": "residual", "status": "failed", "error":
               "replay_board 需要 --stage placement 或 --max-batch k"
               "（防裸跑误覆盖副本）"})
        return config.EXIT_FAILED
    out = residual_cmd.build_products(out_dir_rel=args.out_dir,
                                      select=args.select,
                                      drc_dir=args.drc_dir,
                                      max_batch=args.max_batch,
                                      stage=args.stage,
                                      batch=args.batch,
                                      batches_dir=args.batches_dir)
    if out["kind"] == "error":
        _emit(out["payload"])
        return config.EXIT_FAILED
    if out["kind"] == "bytes":
        sys.stdout.buffer.write(out["payload"])
        sys.stdout.buffer.flush()
        return config.EXIT_OK
    _emit(out["payload"]["obj"])
    return config.EXIT_OK


def cmd_check(args):
    """⑤ 交错检查（§11/§15 FD1）：检查器族+authority 注册表+前馈残差+探针电池。

    probe_board/probe_project 为文本产物（stdout 重定向落盘到探针工程目录，
    kicad-cli 由编排侧执行——pcbflow 零子进程，FC2-D3 口径）。
    --ff-plan-dir：消费计划所在目录（默认 out/revc-ff1；FD2 级联重跑指
    out/revc-fd2）。"""
    if args.select in ("probe_board", "probe_project") and not args.probe:
        _emit({"command": "check", "status": "failed", "error":
               "%s 需要 --probe <探针名：%s|%s>"
               % (args.select,
                  "|".join(p["probe"] for p in check_cmd.PROBES),
                  check_cmd.PROBE_CLEAN)})
        return config.EXIT_FAILED
    if args.select == "probe_battery" and not args.probe_drc_dir:
        _emit({"command": "check", "status": "failed", "error":
               "probe_battery 需要 --probe-drc-dir <探针 DRC JSON 根目录>"})
        return config.EXIT_FAILED
    out = check_cmd.build_products(select=args.select,
                                   out_dir_rel=args.out_dir,
                                   probe=args.probe,
                                   probe_drc_dir=args.probe_drc_dir,
                                   ff_plan_dir=args.ff_plan_dir)
    if out["kind"] == "bytes":
        sys.stdout.buffer.write(out["payload"])
        sys.stdout.buffer.flush()
        return config.EXIT_OK
    _emit(out["payload"]["obj"])
    env_status = (out["payload"]["obj"] or {}).get("status")
    if args.select in ("envelope", "summary") and env_status:
        return _status_exit(env_status)
    return config.EXIT_OK


def cmd_signoff(args):
    """⑥ 终检与签核（§12/§15 FD1）：签核包+waiver 台账+重放验证。

    waiver 批准=确认点 #5（人工逐条），本命令只产提案台账，禁代办。
    --ff-plan-dir/--check-dir/--approvals-dir：FD2 级联重跑输入定位；
    --adopt-override：包内 FF 产物按 adopt 模式重放+签核面 approved 语义。"""
    out = signoff_cmd.build_products(select=args.select,
                                     out_dir_rel=args.out_dir,
                                     ff_plan_dir=args.ff_plan_dir,
                                     check_dir=args.check_dir,
                                     approvals_dir=args.approvals_dir,
                                     adopt_override=args.adopt_override,
                                     consume_bom=getattr(args, "consume_bom",
                                                         False),
                                     session_tag=args.session_tag)
    if out["kind"] == "bytes":
        sys.stdout.buffer.write(out["payload"])
        sys.stdout.buffer.flush()
        return config.EXIT_OK
    _emit(out["payload"]["obj"])
    env_status = (out["payload"]["obj"] or {}).get("status")
    if args.select in ("envelope", "summary") and env_status:
        return _status_exit(env_status)
    return config.EXIT_OK


def cmd_stub(name: str) -> int:
    """未实现命令：如实回 specified 状态（红线：不得宣称可用）。"""
    _emit(envelope.build_envelope(
        command=name, status="unknown", verdict="red",
        inputs=[], artifacts=[], determinism_claim="not_claimed",
        diagnostics=[{"id": "not_implemented",
                      "title": "命令按 SPEC v1.2 定义，实现状态 specified；本会话未建造"}],
        data={"command_status": "specified_not_implemented", "stage": name},
    ))
    return config.EXIT_NOT_IMPLEMENTED


# ------------------------------------------------------- 铜箔闭环（R1；P2b+P4）

#: `copper` 子命令（R1）；每个都在 `copper <sub> --help` 里可见并可真实调用。
COPPER_SUBCOMMANDS = ("mirror", "patch", "verify", "accept", "rollback", "adopt")

#: 铜循环状态 → exit code（config 契约：0=ok 1=failed 2=blocked 3=unknown）。
#: `rejected` = 判定结论"不通过"（命令跑完、结果是拒绝）→ failed；
#: `blocked`/`violations` = 前置未满足或核对发现违例（禁止继续）→ blocked。
COPPER_STATUS_EXIT = {
    "mirror_only": config.EXIT_OK,
    "awaiting_drc": config.EXIT_OK,
    "accepted": config.EXIT_OK,
    "rolled_back": config.EXIT_OK,
    "clean": config.EXIT_OK,
    "noop": config.EXIT_OK,
    "rejected": config.EXIT_FAILED,
    "violations": config.EXIT_BLOCKED,
    "blocked": config.EXIT_BLOCKED,
}


def _copper_exit(obj) -> int:
    """铜循环状态 → exit code（未知状态一律 3=unknown，绝不冒充 ok）。"""
    status = (obj or {}).get("status") or (obj or {}).get("verdict")
    return COPPER_STATUS_EXIT.get(status, config.EXIT_UNKNOWN)


def _add_copper_subparsers(cu) -> None:
    """`copper` 的 6 个子命令（R1；每个都有独立 subparser ⇒ 独立 --help）。

    形状与派发文档 §2 一致：
      mirror --base --out [--registry] / patch --revision-dir --patch-set
      verify --manifest --svg [--board] / accept --revision-dir --drc-report
      rollback --revision-dir / adopt --revision-dir [--design-board]
    另加三个可选旗标（--scenario-id/--base-label/--patch-set（mirror 一轮
    到底）/--registry（verify）），不改变上述必填形状。
    """
    csub = cu.add_subparsers(dest="copper_command", required=True)

    m = csub.add_parser(
        "mirror", help="摄取基准板 → 镜像（build_inputs+build）→ 三向校验 → "
                       "落 <out>/copper-loop/<label>/rev-N/（只读基准，只追加）",
        description="只读镜像一轮：摄取 copper_model 事实 → board_svg_adapter "
                    "build_inputs → svg_route_package.build → 三向校验"
                    "（板↔manifest + manifest↔SVG，任一非空即 blocked）→ 落盘。"
                    "KiCad5（identity_basis=geometric_fallback）回落到 "
                    "copper_only_degraded 只读镜像。绝不写基准板。")
    m.add_argument("--base", required=True, help="基准板路径（只读）")
    m.add_argument("--out", required=True,
                   help="输出根目录（产物落 <out>/copper-loop/<label>/rev-N/）")
    m.add_argument("--registry", default=None,
                   help="权威 net 注册表 JSON（缺省=按板侧 net 名派生身份注册表，"
                        "记录里显式标 registry.basis=derived_identity_from_board）")
    m.add_argument("--scenario-id", default=None,
                   help="场景 id（缺省 copper-loop-<base_label>）")
    m.add_argument("--base-label", default=None,
                   help="版本目录标签（缺省=板文件基名去扩展名）")
    m.add_argument("--patch-set", default=None,
                   help="可选：补丁集 JSON —— 给了就一轮到底（=revision()："
                        "镜像后接着 patch 阶段，状态 awaiting_drc）")
    m.set_defaults(func=cmd_copper)

    p = csub.add_parser(
        "patch", help="在 mirror_only 轮次上应用补丁 → staging 板 + DRC 请求"
                      "（不执行 DRC）",
        description="按铜箔对象 key 寻址打补丁（copper_patch.apply_patch）："
                    "整批原子、结构守卫、字节保真实证、行尾继承。成功 ⇒ "
                    "status=awaiting_drc + drc/request.json（编排侧据此跑 "
                    "kicad-cli）；补丁被拒 ⇒ 不改轮次状态（可改补丁集重试）。"
                    "KiCad5（geometric_fallback）一律 "
                    "edit_unsupported_identity_basis 拒绝。")
    p.add_argument("--revision-dir", required=True,
                   help="<out>/copper-loop/<label>/rev-N 目录")
    p.add_argument("--patch-set", required=True, help="补丁集 JSON 路径")
    p.set_defaults(func=cmd_copper)

    v = csub.add_parser(
        "verify", help="只读三向核对：manifest↔SVG（+给 --board 时板↔manifest "
                       "与快照 hash 绑定）",
        description="零落盘只读核对：verify_consistency(svg, manifest) 恒跑；"
                    "给 --board 时另跑 board_binding.binding_report(板文本, "
                    "manifest, net_map)（逐对象 net/layer/宽度/几何/zone 轮廓）"
                    "与 build_inputs 快照 hash 绑定（board_snapshot_sha256 "
                    "重算；按合同只覆盖板级事实，见输出 note）。任一腿非空 ⇒ "
                    "verdict=violations + exit 2。")
    v.add_argument("--manifest", required=True, help="route-manifest.json 路径")
    v.add_argument("--svg", required=True, help="board.svg 路径")
    v.add_argument("--board", default=None,
                   help="可选：板路径（另做板↔manifest + 快照 hash 绑定两腿）")
    v.add_argument("--registry", default=None,
                   help="可选：权威 net 注册表 JSON（net_map 与快照重建用；"
                        "缺省按板侧 net 名派生）")
    v.set_defaults(func=cmd_copper)

    a = csub.add_parser(
        "accept", help="消费编排侧 DRC 报告 → accepted/rejected（不改 staging）",
        description="读 kicad-cli DRC JSON（结构/来源/工具链版本逐项校验）："
                    "报告缺失/不可解析/结构不符/kicad_version 与 "
                    "toolchain_lock.json 不符 ⇒ blocked（拒绝本次判定，轮次仍 "
                    "awaiting_drc）；对基线 keyset 有新增 violation ⇒ "
                    "rejected；无新增 ⇒ accepted（事务 commit）。")
    a.add_argument("--revision-dir", required=True,
                   help="<out>/copper-loop/<label>/rev-N 目录")
    a.add_argument("--drc-report", required=True,
                   help="DRC JSON 路径（相对路径会回退到 <revision-dir>/drc/）")
    a.set_defaults(func=cmd_copper)

    r = csub.add_parser(
        "rollback", help="回滚该轮（撤可用性 + staging 完整时移除 staging）",
        description="rollback ∈ none|armed|executed|failed：staging sha 与记账"
                    "不符 ⇒ failed（拒绝删除证据）；已 adopt / 已 commit "
                    "（accepted）的轮次拒绝自动回滚（拒绝不改轮次记录）；"
                    "幂等：已回滚再调 ⇒ verdict=noop。设计侧不被触碰"
                    "（transaction.live_board_touched 恒 false）。")
    r.add_argument("--revision-dir", required=True,
                   help="<out>/copper-loop/<label>/rev-N 目录")
    r.set_defaults(func=cmd_copper)

    d = csub.add_parser(
        "adopt", help="显式采纳通道：唯一允许写设计侧的路径（先校 sha 再备份）",
        description="前置 fail-closed：sha256(design_board) == base.sha256"
                    "（不等 ⇒ stale blocked）；仅 accepted（或 KiCad5 只读降级"
                    " mirror_only）可 adopt；先备份 <stem>_pre-adopt-<rev>."
                    "kicad_pcb 再写目标，前后 sha 入 adopt-record.json。"
                    "**--design-board 必须显式给出**（本命令不替调用方猜 "
                    "design/ 目标，避免误写权威板）。")
    d.add_argument("--revision-dir", required=True,
                   help="<out>/copper-loop/<label>/rev-N 目录")
    d.add_argument("--design-board", default=None,
                   help="设计侧目标板路径（必须显式给出；写 design/ 是本闭环"
                        "唯一例外通道）")
    d.set_defaults(func=cmd_copper)


def _read_json_file(path: str, what: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _copper_verify(args, copper_loop) -> dict:
    """`copper verify`：manifest↔SVG（可选 +板↔manifest +快照 hash 绑定）。

    三向核对与 `mirror` 阶段同口径：任一腿非空即 verdict=`violations`。
    纯只读：只读 manifest/SVG/板/注册表，零落盘、零子进程。
    """
    from . import board_binding, board_svg_adapter, copper_model, svg_route_package

    manifest = _read_json_file(args.manifest, "manifest")
    with open(args.svg, encoding="utf-8", newline="") as f:
        svg_text = f.read()
    svg_viol = svg_route_package.verify_consistency(svg_text, manifest)
    board_viol, binding_pending, binding_counts = [], [], {}
    board_note = None
    snapshot_rebuilt = None
    if args.board:
        with open(args.board, encoding="utf-8", newline="") as f:
            board_text = f.read()
        if args.registry:
            registry = _read_json_file(args.registry, "registry")
        else:
            registry = copper_loop.identity_registry_from_board(args.board)
        net_map = {}
        for n in registry.get("nets") or []:
            if isinstance(n, dict) and isinstance(n.get("net_id"), str) \
                    and n["net_id"] and isinstance(n.get("net_name"), str) \
                    and n["net_name"]:
                net_map[n["net_id"]] = n["net_name"]
        report = board_binding.binding_report(board_text, manifest, net_map)
        board_viol = report["violations"]
        binding_pending = report["pending"]
        binding_counts = report["counts"]
        # 快照 hash 绑定（最强一腿）：重建 build_inputs 快照后按 snapshot 校验
        try:
            board_obj, _ref = board_svg_adapter.build_inputs(
                args.board, registry,
                scenario_id=manifest.get("scenario_id"),
                copper=copper_model.parse_copper(board_text))
        except Exception as exc:            # KiCad5/适配层不可用：如实记账，不假装
            board_obj = None
            board_note = ("snapshot_not_rebuilt: board_svg_adapter.build_inputs "
                          "不可用（%s: %s）：本板只做 manifest↔SVG 与"
                          "板↔manifest 两腿，未做快照 hash 绑定"
                          % (exc.__class__.__name__, exc))
        if board_obj is not None:
            snapshot_rebuilt = True
            snap_viol = svg_route_package.verify_consistency(
                svg_text, manifest, snapshot=board_obj)
            svg_viol = sorted(set(svg_viol) | set(snap_viol))
        else:
            snapshot_rebuilt = False
    total = len(svg_viol) + len(board_viol)
    return {
        "command": "copper",
        "subcommand": "verify",
        "manifest_basename": os.path.basename(args.manifest),
        "svg_basename": os.path.basename(args.svg),
        "board_basename": os.path.basename(args.board) if args.board else None,
        "scenario_id": manifest.get("scenario_id"),
        "manifest_schema_version": manifest.get("schema_version"),
        "svg_manifest_violations": svg_viol,
        "board_binding_violations": board_viol,
        "board_binding_pending": binding_pending,
        "board_binding_counts": binding_counts,
        "snapshot_rebuilt": snapshot_rebuilt,
        "snapshot_note": board_note,
        "violations_total": total,
        "verdict": "clean" if total == 0 else "violations",
        "status": "clean" if total == 0 else "violations",
        "note": "只读三向核对：manifest↔SVG（verify_consistency 规则 1–5）+ "
                "板↔manifest（board_binding.binding_report，与 "
                "verify_board_binding 同 `_bind` 口径：逐对象 net/layer/宽度/"
                "几何/zone 轮廓）。给 --board 时另做快照 hash 绑定"
                "（build_inputs 重建 → board_snapshot_sha256 重算比对；按合同"
                "该 hash 用 `_strip_sha` 剥离 *_sha256 且只覆盖板级事实"
                "（pads/layers/bbox/relations），逐条走线几何由板↔manifest 腿"
                "捕获）。零落盘、零子进程。",
    }


def cmd_copper(args) -> int:
    """铜箔 ↔ SVG 双向对应闭环（R1：mirror/patch/verify/accept/rollback/adopt）。

    记录类子命令（mirror/patch/accept/rollback/adopt）的 stdout **就是**该轮次
    的 `revision-record.json` 原文（canonical JSON，逐字节同构：
    `core_fact_sha256` 可对 stdout 独立重算核对）；`verify` 输出只读核对摘要。
    本命令零子进程：DRC 由编排侧跑 kicad-cli，本命令只产出请求/消费报告。

    exit code：0=ok（mirror_only/awaiting_drc/accepted/rolled_back/clean）
    1=failed（rejected：判定不通过）2=blocked（blocked/violations：前置未满足
    或核对发现违例）3=unknown（未知状态）—— 见 `COPPER_STATUS_EXIT`。
    """
    from . import copper_loop
    sub = args.copper_command
    try:
        if sub == "mirror":
            patch_set = (_read_json_file(args.patch_set, "patch-set")
                         if args.patch_set else None)
            if patch_set is None:
                out = copper_loop.mirror_revision(
                    args.base, args.out, registry=args.registry,
                    scenario_id=args.scenario_id, base_label=args.base_label)
            else:      # 给了补丁集 ⇒ 一轮到底（镜像→三向→补丁→DRC 请求）
                out = copper_loop.revision(
                    args.base, patch_set, args.out, registry=args.registry,
                    scenario_id=args.scenario_id, base_label=args.base_label)
        elif sub == "patch":
            out = copper_loop.patch_revision(
                args.revision_dir, _read_json_file(args.patch_set, "patch-set"))
        elif sub == "verify":
            out = _copper_verify(args, copper_loop)
        elif sub == "accept":
            out = copper_loop.accept_revision(args.revision_dir, args.drc_report)
        elif sub == "rollback":
            out = copper_loop.rollback_revision(args.revision_dir)
        else:                                   # adopt
            if not args.design_board:
                _emit({"command": "copper", "subcommand": "adopt",
                       "status": "failed",
                       "error": "adopt 需要 --design-board <path>：写设计侧必须"
                                "显式给出目标板路径（本命令不替调用方猜 design/ "
                                "目标，避免误写权威板）；adopt 是本闭环唯一允许"
                                "触碰 design/ 的通道"})
                return config.EXIT_FAILED
            out = copper_loop.adopt(args.revision_dir, args.design_board)
    except OSError as exc:
        _emit({"command": "copper", "subcommand": sub, "status": "failed",
               "error": "io_error: %s: %s" % (exc.__class__.__name__, exc)})
        return config.EXIT_FAILED
    except ValueError as exc:      # CopperLoopError / JSONDecodeError 等参数错误
        _emit({"command": "copper", "subcommand": sub, "status": "failed",
               "error": "%s: %s" % (exc.__class__.__name__, exc)})
        return config.EXIT_FAILED
    _emit(out)
    return _copper_exit(out)


def build_parser():
    """构造 CLI parser（G1+ W-2：--out-dir 族缺省自 ProjectManifest 取值，
    自 main 抽出为独立函数——测试可静态断言缺省不执行命令）。"""
    _od = config.load_project_manifest().out_dirs
    ap = argparse.ArgumentParser(prog="pcbflow",
                                 description="七级 PCB 设计流编译器（SPEC v1.2；运行时 schema 按各命令实现状态演进）")
    sub = ap.add_subparsers(dest="command", required=True)

    c = sub.add_parser("compile", help="⓪ 约束编译")
    c.add_argument("--select", default="summary",
                   choices=PRODUCTS + ("summary",),
                   help="输出哪个产物（stdout，shell 重定向落盘）")
    c.add_argument("--out-dir", default=_od["compile"],
                   help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    c.set_defaults(func=cmd_compile)

    e = sub.add_parser("enum", help="① 结构枚举（FA2：structures 草案）")
    e.add_argument("--select", default="summary",
                   choices=ENUM_PRODUCTS + ("summary",),
                   help="输出哪个产物（stdout，shell 重定向落盘）")
    e.add_argument("--out-dir", default=_od["enum"],
                   help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    e.set_defaults(func=cmd_enum)

    for name, help_text in (
        ("db", "约束数据库状态查询"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=lambda a, _n=name: cmd_stub(_n))

    ck = sub.add_parser("check", help="⑤ 交错检查（FD1：检查器族+残差+探针电池）")
    ck.add_argument("--select", default="summary",
                    choices=CHECK_PRODUCTS + CHECK_TEXT_PRODUCTS + ("summary",),
                    help="输出哪个产物（stdout 重定向落盘；probe_board/"
                         "probe_project 为探针工程文本，需 --probe；"
                         "probe_battery 需 --probe-drc-dir）")
    ck.add_argument("--out-dir", default=_od["check"],
                    help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    ck.add_argument("--probe", default=None,
                    help="probe_board/probe_project：探针名（probe-* 或 "
                         "probe-clean）")
    ck.add_argument("--probe-drc-dir", default=None,
                    help="probe_battery：探针 DRC JSON 根目录（编排侧 "
                         "kicad-cli 产物，hash 输入）")
    ck.add_argument("--ff-plan-dir", default=check_cmd.FF1_DIR,
                    help="消费的 feedforward-plan.json 所在目录（默认 "
                         "out/revc-ff1；FD2 级联重跑=out/revc-fd2）")
    ck.set_defaults(func=cmd_check)

    so = sub.add_parser("signoff", help="⑥ 终检与签核（FD1：签核包+waiver+重放）")
    so.add_argument("--select", default="summary",
                    choices=SIGNOFF_PRODUCTS + SIGNOFF_TEXT_PRODUCTS
                    + ("summary",),
                    help="输出哪个产物（stdout 重定向落盘）")
    so.add_argument("--out-dir", default=_od["signoff"],
                    help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    so.add_argument("--ff-plan-dir", default=signoff_cmd.FF1_DIR,
                    help="计划附录来源目录（默认 out/revc-ff1；FD2="
                         "out/revc-fd2）")
    so.add_argument("--check-dir", default=signoff_cmd.CHECK_DIR,
                    help="⑤ 产物来源目录（默认=out-dir；FD2=out/revc-fd2）")
    so.add_argument("--approvals-dir", default=None,
                    help="批准输入目录（waiver-approvals/structures.override；"
                         "默认 <out-dir>/approvals；FD2=out/revc-fd1/approvals）")
    so.add_argument("--adopt-override", action="store_true", default=False,
                    help="FD2 adoption：包内 FF 核心产物按 adopt 模式重放"
                         "（structures_override 权威生效）")
    so.add_argument("--consume-bom", action="store_true", default=False,
                    help="FF3：FF 重放附加项按 BOM 派生轨表消费口径重生成"
                         "（需 --adopt-override）")
    so.add_argument("--session-tag", default="FD1",
                    help="报告标题会话标签（FD1/FD2/FD3）")
    so.set_defaults(func=cmd_signoff)

    r = sub.add_parser("route", help="④ 细布 dry-run（FC1：匝道/车道，内存零写板）")
    r.add_argument("--select", default="summary", choices=ROUTE_PRODUCTS + ("report", "summary"),
                   help="输出哪个产物（stdout，shell 重定向落盘；consumption 需 "
                        "--feedforward-plan；report 为 Markdown）")
    r.add_argument("--out-dir", default=_od["route"],
                   help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    r.add_argument("--feedforward-plan", default=None,
                   help="feedforward-plan.json 路径（绑定后 §10.2 控制按 "
                        "planning_advisory 进入 dry-run 规划偏好；默认不绑）")
    r.add_argument("--placement-from-layout", default=None,
                   help="IT：③ 布局提案覆盖板几何（moved refs 重建、未动 refs "
                        "零漂移；计划绑定仍对 p3 基线快照；缺省=关闭）")
    r.set_defaults(func=cmd_route)

    kit = sub.add_parser("keepout-iter",
                         help="IT：③ keepout-aware 重优化（证据实验；锚件不动；"
                              "零写板；转换执行待批=确认点 #4）")
    kit.add_argument("--select", default="summary",
                     choices=("keepout_iteration", "it_layout", "envelope",
                              "run_manifest", "summary"),
                     help="输出哪个产物（stdout，shell 重定向落盘）")
    kit.add_argument("--out-dir", default=_od["keepout_iter"],
                     help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    kit.add_argument("--feedforward-plan",
                     default=_od["kit_ff_plan"],
                     help="fd3 计划（fd2/fd3 controls 逐字节一致，与 fc3 可比）")
    kit.add_argument("--baseline-route-plan",
                     default=_od["kit_route_plan"],
                     help="冻结基线 route-plan（官方违例账来源）")
    kit.add_argument("--max-sweeps", type=int, default=None,
                     help="爬山扫描上限（缺省=config.CPLACE_MAX_SWEEPS）")
    kit.add_argument("--refs", default=None,
                     help="逗号分隔候选 ref 子集（缺省=全部非锚件 keepout "
                          "相关件；测试/复算用）")
    kit.set_defaults(func=cmd_keepout_iter)

    rd = sub.add_parser("residual", help="④ FC2 两靶：残网证书化 + ③ 重放板实战")
    rd.add_argument("--select", default="summary",
                    choices=RESIDUAL_PRODUCTS + ("replay_batch",)
                    + RESIDUAL_TEXT_PRODUCTS + ("summary",),
                    help="输出哪个产物（stdout 重定向落盘；replay_board/"
                         "report 为文本；replay_board 需 --stage placement "
                         "或 --max-batch）")
    rd.add_argument("--out-dir", default=_od["residual"],
                    help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    rd.add_argument("--drc-dir", default=None,
                    help="kicad-cli DRC JSON 目录（baseline*/batch-N*/"
                         "final*；hash 输入，replay 台账用）")
    rd.add_argument("--max-batch", type=int, default=None,
                    help="replay_board：叠加第 1..k 批路由（cumulative）")
    rd.add_argument("--batch", type=int, default=None,
                    help="replay_batch：待规划的批号")
    rd.add_argument("--batches-dir", action="store_true", default=False,
                    help="replay_board/replay：用 batches/batch-k.json 的"
                         "实际执行 routes（顺序感知规划产物）")
    rd.add_argument("--stage", default=None, choices=("placement",),
                    help="replay_board --stage placement：pristine+③ 重放")
    rd.set_defaults(func=cmd_residual)

    cp = sub.add_parser("co-place", help="③ 联合布局与骨架优化（FB1；FF-4 计划消费）")
    cp.add_argument("--select", default="summary", choices=COPRODUCTS + ("summary",),
                    help="输出哪个产物（stdout，shell 重定向落盘；placement_csv 为原文；"
                         "ff_consumption 需 --feedforward-plan）")
    cp.add_argument("--out-dir", default=_od["coplace"],
                    help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    cp.add_argument("--feedforward-plan", default=None,
                    help="FF-4：feedforward-plan.json 路径（绑定后 controls 经 "
                         "consumer gate 进入候选接受语义；默认不绑=历史行为）")
    cp.set_defaults(func=cmd_coplace)

    a = sub.add_parser("audit", help="② 架构可布性预检（FA3）")
    a.add_argument("--select", default="summary", choices=AUDIT_PRODUCTS + ("summary",),
                   help="输出哪个产物（stdout，shell 重定向落盘）")
    a.add_argument("--out-dir", default=_od["audit"],
                   help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    a.add_argument("--af-table", default=None,
                   help="mcu-af-table-full.json 路径（AF 会话 opt-in：消费 AF 表"
                        "出 pin-swap 候选，proposal-only；缺省=历史行为零候选）")
    a.set_defaults(func=cmd_audit)

    f = sub.add_parser("feedforward", help="FF 前馈资源账本/比较/基线冻结（FF1）")
    f.add_argument("--select", default="summary",
                   choices=FF_PRODUCTS + ("report", "summary"),
                   help="输出哪个产物（stdout，shell 重定向落盘；report 为 Markdown；"
                        "impedance_targets 需 --adopt-override）")
    f.add_argument("--out-dir", default=_od["feedforward"],
                   help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    f.add_argument("--adopt-override", action="store_true", default=False,
                   help="FD2 adoption 级联重跑：structures.override 权威生效+"
                        "能力/叠层/电流三源消费（plan_id=FF-REVC-0002；"
                        "默认关=FF1 口径）")
    f.add_argument("--consume-bom", action="store_true", default=False,
                   help="FF3 级联重跑（需 --adopt-override）：BOM 派生轨功耗表"
                        "derived 消费——rail 供给 sourced/derived 分列+需求 "
                        "consumption 口径（plan_id=FF-REVC-0003）")
    f.add_argument("--placement-csv", default=None,
                   help="CAS1 级联收口（需 --adopt-override；确认点 #4 已批）："
                        "采纳 placement.csv 路径——placement 六 hash 绑定切至"
                        "采纳快照（plan_id=FF-REVC-0004）")
    f.add_argument("--placement-layout", default=None,
                   help="CAS1：采纳布局提案 it-layout.json 路径（provenance "
                        "登记；需 --placement-csv）")
    f.add_argument("--bom-power-file", default=None,
                   help="FF5 rail 源覆盖（需 --consume-bom）：指向后续权威 "
                        "bom-power-derive.json（缺省=fd3 钉源逐字节不变；"
                        "plan_id=FF-REVC-0005；signoff/重放从计划 snapshot "
                        "自动派生此路径）")
    f.set_defaults(func=cmd_feedforward)

    ed = sub.add_parser("editor", help="E 简版骨架编辑器（FB2：拖件+拖拐点，只出提案）")
    ed.add_argument("--select", default="summary",
                    choices=EDITOR_PRODUCTS + ("validate", "summary"),
                    help="输出哪个产物（stdout，shell 重定向落盘；html 为自包含离线页）")
    ed.add_argument("--out-dir", default=_od["editor"],
                    help="产物相对路径（仅记入 manifest/envelope，不落盘）")
    ed.add_argument("--proposal", default=None,
                    help="validate 用：待校验的 editor-proposal.json 路径")
    ed.set_defaults(func=cmd_editor)

    cu = sub.add_parser(
        "copper", help="铜箔 ↔ SVG 双向闭环（R1：mirror/patch/verify/accept/"
                       "rollback/adopt；零子进程，DRC 由编排侧执行）")
    _add_copper_subparsers(cu)

    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
