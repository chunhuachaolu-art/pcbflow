# -*- coding: utf-8 -*-
"""kicad-cli 桥（SPEC §5 verify 的执行核心；L4 完整命令面在 S5 补齐）。

口径（HANDOFF 坑 1）：必须在含 .kicad_pro 的工程目录里跑，
--refill-zones --save-board 才是连通性/间距真值。kicad-cli 是唯一 DRC 裁决。
"""
from __future__ import annotations

import json
import math
import os
import subprocess

from . import config as C


def _board_path(project_dir: str) -> str:
    """板文件定位：优先与 .kicad_pro 同名的 .kicad_pcb
    （同目录可能有历史评估板，README 防呆），否则任一 .kicad_pcb。"""
    pro = None
    for f in os.listdir(project_dir):
        if f.endswith(".kicad_pro"):
            pro = f
    if pro:
        cand = os.path.join(project_dir, os.path.splitext(pro)[0] + ".kicad_pcb")
        if os.path.exists(cand):
            return cand
    for f in os.listdir(project_dir):
        if f.endswith(".kicad_pcb"):
            return os.path.join(project_dir, f)
    raise FileNotFoundError(f"no .kicad_pcb in {project_dir}")


class DrcResult:
    def __init__(self, data: dict, workdir: str):
        self.data = data
        self.workdir = workdir

    @property
    def violations(self):
        return self.data.get("violations", [])

    @property
    def unconnected(self):
        return self.data.get("unconnected_items", [])

    def violations_of_net(self, net: str):
        """items 描述里含 [net] 的违规（KiCad 描述格式：走线 [NET] / 焊盘 n [NET]）。"""
        out = []
        for v in self.violations:
            for it in v.get("items", []):
                if f"[{net}]" in it.get("description", ""):
                    out.append(v)
                    break
        return out

    def summary(self):
        sev = {}
        types = {}
        for v in self.violations:
            sev[v.get("severity", "?")] = sev.get(v.get("severity", "?"), 0) + 1
            types[v.get("type", "?")] = types.get(v.get("type", "?"), 0) + 1
        return {"violations": len(self.violations),
                "unconnected": len(self.unconnected),
                "by_severity": sev, "by_type": types}


def run_drc(project_dir: str, out_json: str = None, severity: str = "error",
            refill: bool = True, save: bool = True, timeout: int = 600) -> DrcResult:
    """在 project_dir 内对工程板跑 kicad-cli DRC。返回解析后的 DrcResult。"""
    if out_json is None:
        out_json = os.path.join(project_dir, "pcbagent-drc.json")
    board = _board_path(project_dir)
    cmd = [C.KICAD_CLI, "pcb", "drc", "--format", "json",
           "--output", out_json, f"--severity-{severity}"]
    if refill:
        cmd.append("--refill-zones")
    if save:
        cmd.append("--save-board")
    cmd.append(board)
    proc = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True,
                          timeout=timeout)
    if proc.returncode not in (0, 5):
        # 5 = 发现违规（--exit-code-violations 才非零；保险起见宽容非零但要求 json 存在）
        if not os.path.exists(out_json):
            raise RuntimeError(f"kicad-cli failed rc={proc.returncode}\n"
                               f"stdout: {proc.stdout[-2000:]}\nstderr: {proc.stderr[-2000:]}")
    with open(out_json, encoding="utf-8") as fh:
        data = json.load(fh)
    return DrcResult(data, project_dir)


def diff_drc(base: DrcResult, new: DrcResult):
    """回归 diff：按 (type, severity, items描述) 匹配。返回 (新增, 消失)。"""
    def key(v):
        return (v.get("type"), v.get("severity"),
                tuple(sorted(i.get("description", "") for i in v.get("items", []))))
    base_keys = {key(v) for v in base.violations}
    new_keys = {}
    for v in new.violations:
        new_keys.setdefault(key(v), []).append(v)
    added = [v for k, vs in new_keys.items() if k not in base_keys for v in vs]
    removed_count = 0
    new_key_set = set(new_keys)
    for k in base_keys:
        if k not in new_key_set:
            removed_count += 1
    return added, removed_count


# ---------------------------------------------------------------- L4 桥（B4/S5）

_LAYER_NAME = {C.LAYER_F: "F.Cu", C.LAYER_B: "B.Cu",
               C.LAYER_IN1: "In1.Cu", C.LAYER_IN2: "In2.Cu"}


def net_lengths(mirror):
    """每网铜长 mm = Σ track 段欧氏长 + 过孔数×LENGTH_VIA_EQUIV_MM
    （routing-spec §3 测量口径，移植 revc/length-report.py；板内无 arc
    ——实测 0 条——段欧氏长即 pcbnew GetLength 语义）。"""
    tr_len, via_cnt = {}, {}
    for t in mirror.tracks:
        tr_len[t.net] = tr_len.get(t.net, 0.0) + math.hypot(t.x2 - t.x1, t.y2 - t.y1)
    for v in mirror.vias:
        via_cnt[v.net] = via_cnt.get(v.net, 0) + 1
    return {n: tr_len.get(n, 0.0) + via_cnt.get(n, 0) * C.LENGTH_VIA_EQUIV_MM
            for n in set(tr_len) | set(via_cnt)}


def length_report(mirror):
    """九组等长报告（SPEC §5 length；口径与 revc/length-report.py 逐键一致）。"""
    name2len = net_lengths(mirror)
    report = {"convention": "每网铜长=track段长合计+0.2mm/过孔（routing-spec §3）",
              "groups": {}, "all_pass": True}
    for gname, g in C.LENGTH_GROUPS.items():
        entry = {"target_mm": g["target"], "limit_mm": g["limit"], "nets": {}}
        if g["ref"] is None:
            lens = {n: round(name2len.get(n, 0.0), 2) for n in g["nets"]}
            entry["nets"] = lens
            if all(v > 0 for v in lens.values()):
                delta = round(abs(lens[g["nets"][0]] - lens[g["nets"][1]]), 2)
                entry["intra_pair_delta_mm"] = delta
                entry["pass"] = delta <= g["limit"]
            else:
                entry["pass"] = False
                entry["note"] = "unrouted"
        else:
            ref_len = name2len.get(g["ref"])
            for n in list(g["nets"]) + [g["ref"]]:
                entry["nets"][n] = round(name2len.get(n, 0.0), 2)
            if not ref_len:
                entry["pass"] = False
                entry["note"] = "reference unrouted"
            else:
                deltas, worst = {}, 0.0
                for n in g["nets"]:
                    d = name2len.get(n, 0.0) - ref_len
                    deltas[n] = round(d, 2)
                    worst = max(worst, abs(d))
                entry["deltas_vs_ref"] = deltas
                entry["ref_len_mm"] = round(ref_len, 2)
                entry["worst_abs_delta_mm"] = round(worst, 2)
                entry["pass"] = worst <= g["limit"]
                entry["target_met"] = worst <= g["target"]
        if not entry.get("pass"):
            report["all_pass"] = False
        report["groups"][gname] = entry
    return report


def length_report_md(rep, title):
    out = [f"# 等长组报告 — {title}", "",
           f"> 口径：{rep['convention']}；pass=|Δ|≤limit（上限），"
           "target_met=|Δ|≤target（目标）。", ""]
    for gname, e in rep["groups"].items():
        head = f"## {gname}（target {e['target_mm']} / limit {e['limit_mm']} mm）"
        flag = "PASS" if e.get("pass") else "FAIL"
        if "deltas_vs_ref" in e:
            head += f" — ref {e['ref_len_mm']}mm"
            body = (f"worst |Δ| = {e['worst_abs_delta_mm']}mm → **{flag}**"
                    + ("，target 达标" if e.get("target_met") else "，target 未达"))
            bad = [n for n, d in e["deltas_vs_ref"].items() if abs(d) > e["limit_mm"]]
            zero = [n for n, v in e["nets"].items() if v == 0.0]
            if zero:
                body += "\n- 未布通（长度 0）： " + ", ".join(sorted(zero))
            if bad:
                body += "\n- 超限网: " + ", ".join(
                    f"{n}({e['deltas_vs_ref'][n]:+.2f})" for n in bad)
        elif e.get("note") == "reference unrouted":
            zero = sorted(n for n, v in e["nets"].items() if v == 0.0)
            body = ("**FAIL** — 参考网未布通（长度 0）: "
                    + ", ".join(zero or ["?"]))
        else:
            if e.get("note") == "unrouted":
                body = f"**FAIL** — 对内未布通（{', '.join(e['nets'])} 长度为 0）"
            else:
                (na, la), (nb, lb) = list(e["nets"].items())
                body = (f"对内差 = {e['intra_pair_delta_mm']}mm → **{flag}**"
                        f"（{na} {la} / {nb} {lb} mm）")
        out += [head, body, ""]
    verdict = ("**总判定：全部组 PASS**" if rep["all_pass"]
               else "**总判定：存在 FAIL 组**（等长后处理属 F4/GUI 调谐阶段，"
                    "不在本工具链范围；本报告即 routing-spec §8 的等长门输入）")
    out.append(verdict)
    return "\n".join(out) + "\n"


def verify_flow(project_dir, baseline_path=None, out_json=None, severity="error",
                refill=True, save=True, timeout=600):
    """verify 全流程（SPEC §5）：跑 DRC → 与基线 diff（--baseline 显式文件或
    上次 verify 快照 verify-last.json，均无则首跑建立基线）→ 报告 dict+MD。
    产物内存生成、落盘由调用方执行（planner 同惯例）；快照滚动 =
    调用方把返回的 raw_json 拷为 verify-last.json。
    返回 (report, md, raw_json_path)。regression=出现基线没有的新增违规。"""
    out_dir = os.path.join(project_dir, "pcbagent-out", C.B4_OUT_SUBDIR)
    if out_json is None:
        out_json = os.path.join(out_dir, "verify-drc.json")
    new = run_drc(project_dir, out_json=out_json, severity=severity,
                  refill=refill, save=save, timeout=timeout)
    base, base_src = None, None
    cand = baseline_path or os.path.join(out_dir, "verify-last.json")
    if os.path.isfile(cand):
        with open(cand, encoding="utf-8") as fh:
            base = DrcResult(json.load(fh), project_dir)
        base_src = cand
    added, removed = diff_drc(base, new) if base is not None else ([], 0)
    report = {
        "project": project_dir,
        "baseline": base_src,
        "drc_json": out_json,
        "violations": len(new.violations),
        "unconnected": len(new.unconnected),
        "by_type": new.summary()["by_type"],
        "added": [{"type": v.get("type"), "severity": v.get("severity"),
                   "items": [i.get("description", "") for i in v.get("items", [])]}
                  for v in added],
        "removed_count": removed,
        "regression": bool(added),
    }
    return report, _verify_md(report), out_json


def _verify_md(r):
    lines = ["# verify 报告", "",
             f"- 工程：`{r['project']}`",
             f"- 基线：`{r['baseline'] or '无（首跑，本次快照建立基线）'}`",
             f"- DRC（error 级，refill+save 口径）：violations={r['violations']}"
             f"{'（' + ', '.join(f'{k}×{v}' for k, v in r['by_type'].items()) + ')' if r['by_type'] else ''}，"
             f"unconnected={r['unconnected']}",
             ("- 回归：**无新增 ✓**" if not r["regression"]
              else f"- 回归：**新增 {len(r['added'])} 条 ✗**")
             + (f"，基线中 {r['removed_count']} 条已消失" if r["removed_count"] else ""), ""]
    for a in r["added"]:
        first = a["items"][0] if a["items"] else ""
        lines.append(f"- NEW [{a['type']}/{a['severity']}] {first}")
    return "\n".join(lines) + "\n"


def render_layers(project_dir, layers=None, out_dir=None):
    """分层 SVG（kicad-cli pcb export svg --mode-multi，每层一文件；
    --page-size-mode 2 只取板域，--check-zones 保证铺铜入图）。
    返回 {"out_dir", "layers", "files"}。"""
    layers = list(layers) if layers else list(C.RENDER_LAYERS)
    out_dir = out_dir or os.path.join(project_dir, "pcbagent-out",
                                      C.B4_OUT_SUBDIR, "render")
    os.makedirs(out_dir, exist_ok=True)
    cmd = [C.KICAD_CLI, "pcb", "export", "svg", "--mode-multi",
           "--layers", ",".join(layers), "--page-size-mode", "2",
           "--check-zones", "-o", out_dir + os.sep, _board_path(project_dir)]
    proc = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True,
                          timeout=300)
    files = sorted(f for f in os.listdir(out_dir) if f.lower().endswith(".svg"))
    if proc.returncode != 0 or not files:
        raise RuntimeError(f"kicad-cli svg failed rc={proc.returncode}\n"
                           f"stdout: {proc.stdout[-1500:]}\nstderr: {proc.stderr[-1500:]}")
    return {"out_dir": out_dir, "layers": layers, "files": files}


# routing-spec §4 对称性/拓扑条款（视觉审计清单数据源；条文只读搬运）
_AUDIT_ITEMS = (
    ("S4.1", "USB 差分对（含 _C 段）",
     "整对同层、平行耦合（间距=差分间距）、换层 ≤1 且成对、过孔数对内相等；"
     "不得穿越 SW_NODE 区与晶振 3mm 邻域",
     ("USB_DP", "USB_DM", "USB_DP_C", "USB_DM_C")),
    ("S4.2", "FMC 字节通道对称",
     "D0-7+NBL0 与 D8-15+NBL1 各自同层穿越 U1↔U2 通道（优先整组 In2）；"
     "组间同层比例一致、过孔数差 ≤1",
     tuple([f"FMC_D{i}" for i in range(16)] + ["FMC_NBL0", "FMC_NBL1"])),
    ("S4.3", "FMC 时钟点对点",
     "FMC_SDCLK 拓扑点对点、禁止分支；落 U2 前最后一段直线进入",
     ("FMC_SDCLK",)),
    ("S4.4", "SDMMC2 CK 先行",
     "SDMMC2_CK 先行布线并锁定；CMD/D0-3 参照 CK 长度，组内同层优先",
     ("SDMMC2_CK", "SDMMC2_CMD", "SDMMC2_D0", "SDMMC2_D1", "SDMMC2_D2",
      "SDMMC2_D3")),
    ("S4.5", "晶体对称与保护区",
     "HSE/LSE 负载电容对称摆位；保护区 3mm 内无高速线/SW_NODE；走线短而对称",
     ("HSE_IN", "HSE_OUT", "LSE_IN", "LSE_OUT")),
    ("S4.6", "SW_NODE 面积最小",
     "宽而短；下方 In1 保持完整 GND 回流；禁止从晶振/USB/analog 下方穿过",
     ("SW_NODE",)),
    ("S4.7", "蛇形等长纪律",
     "蛇形只允许出现在等长后处理（F4）阶段；幅度间距 ≥3W；45° 折线；"
     "整组同风格（同振幅/间距）；优先放接收端附近",
     ()),
)


def audit_checklist(mirror):
    """routing-spec §4 视觉审计清单（SPEC §5 audit-checklist）：逐条款附工具
    可测的客观证据（每网铜长/过孔数/分层段数）；视觉判定项留给人/VLM
    （advisory 用途，永不作裁决）。返回 (data, md)。"""
    lens = net_lengths(mirror)
    per_net = {}
    for t in mirror.tracks:
        d = per_net.setdefault(t.net, {"vias": 0, "tracks_by_layer": {}})
        k = _LAYER_NAME.get(t.layer, str(t.layer))
        d["tracks_by_layer"][k] = d["tracks_by_layer"].get(k, 0) + 1
    for v in mirror.vias:
        per_net.setdefault(v.net, {"vias": 0, "tracks_by_layer": {}})["vias"] += 1
    items = []
    for iid, title, clause, nets in _AUDIT_ITEMS:
        ev = {n: {"length_mm": round(lens.get(n, 0.0), 2),
                  "vias": per_net.get(n, {}).get("vias", 0),
                  "tracks_by_layer": per_net.get(n, {}).get("tracks_by_layer", {})}
              for n in nets}
        items.append({"id": iid, "clause": f"routing-spec §4.{iid[-1]}",
                      "title": title, "requirement": clause, "measured": ev,
                      "visual_check": "pending（对照 render 分层 SVG，人工/VLM 填）"})
    data = {"source": "routing-spec-v1 §4", "advisory_only": True,
            "how_to": "逐条：读 measured 客观数值 → 打开 pcbagent-out/b4/render/ "
                      "分层 SVG 目检 → 填 visual_check（pass/fail + 证据）",
            "items": items}
    return data, _audit_md(data)


def _audit_md(data):
    out = ["# 视觉审计清单（routing-spec §4）", "",
           "> advisory 用途，非 DRC 裁决。逐条对照 `pcbagent-out/b4/render/` 分层",
           "> SVG 目检勾选；工具已预填每网铜长/过孔数/分层段数等客观证据。", ""]
    for it in data["items"]:
        out.append(f"## [ ] {it['id']} {it['title']}（{it['clause']}）")
        out.append(f"- 条款：{it['requirement']}")
        for n, e in it["measured"].items():
            lay = "/".join(f"{k}×{v}"
                           for k, v in sorted(e["tracks_by_layer"].items())) or "无走线"
            out.append(f"- {n}: 长 {e['length_mm']}mm, 过孔 {e['vias']}, 段 {lay}")
        if not it["measured"]:
            out.append("- （纯视觉判定项，无网络证据）")
        out.append(f"- 目检：{it['visual_check']}")
        out.append("")
    return "\n".join(out) + "\n"
