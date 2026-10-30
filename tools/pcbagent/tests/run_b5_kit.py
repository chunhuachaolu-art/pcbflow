# -*- coding: utf-8 -*-
"""B5：gui-session-kit 生成器（SPEC §2 B5）——残网交 GUI 会话人工收的施工图包。

用法:  python tests/run_b5_kit.py --project <Rev-C 工程目录>

产物（<工程>/pcbagent-out/gui-session-kit/）：
  README.md                GUI 会话工作流（分批施工→保存→verify 回归门）
  batches.md / batches.csv 分批施工清单（走廊标注 + 每批落盘后 verify 命令）
  residual-corridors.svg   残网走廊总图（自 pcbagent-out/b3/ 拷贝）
  residual-report.md       残网阻塞原因口径（自 b3/ 拷贝）
  opens-refreshed.csv      断点清单真值（自 b3/ 拷贝）

确定性：批次序 = （网类优先级 L2_ROUTE_PRIORITY → 网名字典序 → 距离升序），
每批 C.GUI_KIT_BATCH_PAIRS 对；GND 单列末批（平面缝合，不走信号布线）。
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import pathlib
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pcbagent import config as C  # noqa: E402
from pcbagent.planner import parse_opens_csv  # noqa: E402
from pcbagent.cli import _load_corridors_full  # noqa: E402


def _net_class(net: str) -> str:
    for pat, cls in C.L2_NET_CLASS_PATTERNS:
        if net.startswith(pat) or pat in net:
            return cls
    return C.L2_NET_CLASS_DEFAULT


def build_batches(pairs, gnd, pair_corr):
    """→ (batches, gnd_rows)；每批 = [(net, A, B, row, corridor_bool), ...]。"""
    def sort_key(item):
        net, A, B, row = item
        return (C.L2_ROUTE_PRIORITY.get(_net_class(net), 99), net,
                float(row["distance_mm"]))
    ordered = sorted(pairs, key=sort_key)
    batches, cur = [], []
    for it in ordered:
        net, A, B, row = it
        corr = (net, round(A[0], 3), round(A[1], 3),
                round(B[0], 3), round(B[1], 3)) in pair_corr
        cur.append((net, A, B, row, corr))
        if len(cur) >= C.GUI_KIT_BATCH_PAIRS:
            batches.append(cur)
            cur = []
    if cur:
        batches.append(cur)
    return batches, gnd


def batches_md(batches, gnd, project):
    total = sum(len(b) for b in batches)
    out = ["# GUI 会话分批施工清单", "",
           f"- 断点清单：opens-refreshed.csv（{total} 信号对 + {len(gnd)} GND），"
           f"共 {len(batches)} 批信号（每批 ≤{C.GUI_KIT_BATCH_PAIRS} 对）"
           + (f" + 1 批 GND" if gnd else ""),
           "- 批序：routing-spec §9 布线顺序（USB → FMC → SDMMC2 → SDMMC1 → "
           "QSPI → ETH → LTDC → 电源 → 其余信号；同批内距离升序）；"
           "GND 单列末批（平面缝合）",
           "- 走廊列：有 = residual-corridors.svg 上该对有实线走廊（L2 规划）；"
           "无 = 图上虚线参考（S4 判定的干道饱和区，施工时优先试 In2 层）",
           "", "**每个批次施工并保存后，必须跑一次回归门再进下一批：**", "",
           "```", f"python -m pcbagent.cli verify --project {project}",
           "```",
           "回归=无新增 ✓ 才继续；出现新增违规：KiCad 里撤销本批全部改动重试",
           "（或保留半成品但单独 DRC 定位——宁慢勿脏）。", ""]
    for bi, batch in enumerate(batches, 1):
        nets = sorted({net for net, *_ in batch})
        out.append(f"## 批次 {bi}/{len(batches)}（{len(batch)} 对；"
                   f"{', '.join(nets)}）")
        out.append("")
        out.append("| # | 网 | from → to | 距离 mm | 走廊 | 建议层 |")
        out.append("|---|---|---|---|---|---|")
        for si, (net, A, B, row, corr) in enumerate(batch, 1):
            out.append(f"| {si} | {net} | {row['from']} → {row['to']} "
                       f"| {row['distance_mm']} | {'有' if corr else '无'} "
                       f"| {row.get('suggested_layer', '')} |")
        out.append("")
        out.append(f"落盘后回归门：`python -m pcbagent.cli verify "
                   f"--project {project}`")
        out.append("")
    if gnd:
        out.append(f"## 批次 {len(batches) + 1}/{len(batches) + 1}"
                   f"（GND ×{len(gnd)}——平面缝合，不走信号布线）")
        out.append("")
        out.append("| # | from → to | 距离 mm |")
        out.append("|---|---|---|")
        for si, (net, A, B, row) in enumerate(gnd, 1):
            out.append(f"| {si} | {row['from']} → {row['to']} "
                       f"| {row['distance_mm']} |")
        out.append("")
        out.append("GND 断点靠铺铜重灌 + 缝合孔（routing-spec §6.3：≤8mm 网格，"
                   "连接器排加密 ≤4mm）收口；收完跑一次 verify。")
    return "\n".join(out) + "\n"


def batches_csv(batches):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["batch", "seq", "net", "from", "to", "from_x_mm", "from_y_mm",
                "to_x_mm", "to_y_mm", "distance_mm", "corridor",
                "suggested_layer"])
    for bi, batch in enumerate(batches, 1):
        for si, (net, A, B, row, corr) in enumerate(batch, 1):
            w.writerow([bi, si, net, row["from"], row["to"],
                        A[0], A[1], B[0], B[1], row["distance_mm"],
                        int(corr), row.get("suggested_layer", "")])
    return buf.getvalue()


def kit_readme(batches, gnd, project):
    total = sum(len(b) for b in batches)
    return f"""# GUI 会话施工图包（pcbagent B5 交付）

对象：Rev-C 残网 {total} 信号对 + {len(gnd)} GND（pcbagent L3 已收 8 条，
上界证据与阻塞原因见 residual-report.md）。本包是**人机 GUI 会话**的施工图：
KiCad 交互布线（含等长调谐 FREE 角度）+ pcbagent verify 做每批回归门。

## 施工循环（每批一循环）

1. 对照 `residual-corridors.svg` 与 `pcbagent-out/b4/render/` 分层 SVG，
   按本批清单（batches.md）在 KiCad 里布线；
   层口径按建议列 + routing-spec §5（F 只做 ≤3mm 逃逸，长距下 In2）。
2. KiCad 保存。
3. 跑回归门（第一次运行会自动建立基线）：

```
python -m pcbagent.cli verify --project {project}
```

4. 回归=无新增 ✓ → 下一批；✗ → 撤销本批改动（或单独定位），修完重跑。

## 收尾（全部批次后）

- `python -m pcbagent.cli verify --project <工程>` —— 零新增 +
  unconnected 应降到 GND 平面缝合完成后的目标值；
- `python -m pcbagent.cli length --project <工程>` —— 九组等长现状基线
  （F4 等长调谐的输入，调谐后再跑应全绿）；
- `python -m pcbagent.cli audit-checklist --project <工程>` —— §4 视觉审计
  清单（对照 render SVG 逐条勾）。

## 注意事项（S4 实证）

- **SW_NODE**：它周边 5V 铺铜有重灌语义（信号 zone vs 新孔），KiCad GUI 里
  布线会自动重灌并以板内 DRC 为准——人工施工天然安全；该网当初被工具
  移出自动提交集只是无头 L1 的口径盲区（residual-report.md §阻塞原因）。
- verify 用 `--refill-zones --save-board` 口径，跑完会刷新板上 zone 填充——
  属正常动作（与 KiCad 手动 DRC 同口径）。
- 阻塞原因三类口径（干道饱和/引脚场/铺铜封堵）见 residual-report.md，
  施工卡住时先读它再动手，避免在饱和干道里硬抠。
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="B5 gui-session-kit 生成器")
    ap.add_argument("--project", required=True)
    args = ap.parse_args(argv)
    project = args.project
    b3 = os.path.join(project, "pcbagent-out", "b3")
    opens = os.path.join(b3, "opens-refreshed.csv")
    if not os.path.isfile(opens):
        print(f"找不到 {opens}——B3 残网包缺失", file=sys.stderr)
        return 2
    pairs, gnd = parse_opens_csv(opens)
    _soft, pair_corr = _load_corridors_full(project)
    batches, gnd_rows = build_batches(pairs, gnd, pair_corr)
    kit = os.path.join(project, "pcbagent-out", "gui-session-kit")
    pathlib.Path(kit).mkdir(parents=True, exist_ok=True)
    # 产物落盘（数据文件直写无钩子问题；路径常量字面拼接）
    (pathlib.Path(kit) / "README.md").write_text(
        kit_readme(batches, gnd_rows, project), encoding="utf-8", newline="")
    (pathlib.Path(kit) / "batches.md").write_text(
        batches_md(batches, gnd_rows, project), encoding="utf-8", newline="")
    (pathlib.Path(kit) / "batches.csv").write_text(
        batches_csv(batches), encoding="utf-8", newline="")
    for name in ("residual-corridors.svg", "residual-report.md",
                 "opens-refreshed.csv"):
        src = os.path.join(b3, name)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(kit, name))
    summary = {
        "kit": kit,
        "signal_pairs": sum(len(b) for b in batches),
        "gnd_pairs": len(gnd_rows),
        "batches": len(batches) + (1 if gnd_rows else 0),
        "batch_size": C.GUI_KIT_BATCH_PAIRS,
        "with_corridor": sum(1 for b in batches for it in b if it[4]),
        "files": sorted(os.listdir(kit)),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
