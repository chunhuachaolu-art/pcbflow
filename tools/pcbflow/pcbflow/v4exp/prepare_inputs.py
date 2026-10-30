"""pcbflow.v4exp.prepare_inputs -- 生成 E1 各输入组的 planner 输入文件。

CLI（stdin JSON -> stdout；无 argv）：
  {"splits": ["development"], "groups": ["B", "C", "D"],
   "out_dir": "out/v4-experiment/e1/inputs",
   "source_dir": "out/v4-experiment"          # 可选，默认 out/v4-experiment
  }

每场景 x 组写一个 planner-input-<sid>-<group>.json：
* B 组：板摘要（bbox、layers、rules 全文、pads 表、nets 及 endpoints、
  keepouts、relations）+ board_snapshot_sha256（供响应原样回填）+ 冻结契约
  文本。label 是答案，绝不进入任何组输入；seed/split/family 同样不给。
* C 组：与 B 相同摘要，另加该场景 SVG 源码全文（内联字符串 svg_source）与
  1200x675 PNG 的相对路径 png_path。
* D 组：{"scenario_id", "group", "board_snapshot_sha256", "inputs":
  [<png 相对路径>]} + 冻结契约文本。不给板摘要、不给 SVG；哈希只是内容寻址
  串，不泄露板几何——给出它才能让"仅像素规划"的响应合法进入 solver，
  §5.4 条件 6 要诊断的是 D 组能否凭像素稳定复原执行位置，而不是协议拦截。

所有组附同一段冻结的输出契约文本（模块常量 CONTRACT_TEXT），措辞中性，
不暗示任何最优策略。

零子进程、零 argv、零 wall-clock、零网络；产物无主机绝对路径。
"""

from __future__ import annotations

import os

from pcbflow.v4exp import model

INPUT_SCHEMA = "pcbflow.v4exp.planner-input/1"
PNG_SIZE_SPEC = "1200x675"
# 仓库根（pcbflow 包的上一级），用于把产物指针规范成仓库相对路径，
# 保证无论调用方传入相对还是绝对 source_dir，输入文件内容逐字节一致。
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

CONTRACT_TEXT = """输出契约（冻结文本，所有输入组相同）：
你只能输出一个 JSON 对象，schema 为 "pcbflow.v4exp.planner-response/1"，字段如下。
- "schema": 固定字符串 "pcbflow.v4exp.planner-response/1"。
- "scenario_id": 本场景的 scenario_id，原样回填。
- "board_snapshot_sha256": 板快照哈希。若输入中给出了该哈希，必须原样回填；\
若你无法从给定输入中获知该哈希，响应会被判为 blocked。
- "group": 本输入所属组别（"B"、"C" 或 "D"），原样回填。
- "actions": 动作对象，只允许以下键。
  - "route_order"（必需）: 恰好由该板全部 net_id 各出现一次组成的列表；\
缺失、为空、含未知 net、含重复 net 或缺少任何 net 都会导致整体 blocked。
  - "corridor_preferences"（可选）: 列表，每项形如 \
{"net_id": <net_id>, "waypoints_mm": [[x, y], ...]}；waypoint 是板 bbox 内的\
毫米坐标，每项最多 3 个；越出 bbox、落入对该 net 生效的禁布区、超过 3 个、\
或 net 未知时，该项被剔除（记 rejection），不影响其余项。
  - "layer_preferences"（可选）: 列表，每项形如 {"net_id": <net_id>, \
"layers": [<层名>, ...]}；层名必须属于该 net 的 net_class 在 \
rules.allowed_layers 中允许的层，越权层的项被剔除。
  - "protect"（可选）: net_id 字符串列表；含未知 net 会导致整体 blocked。
  - "notes"（可选）: 字符串。
  - "uncertainty"（可选）: "low"、"medium" 或 "high" 之一；其他取值该项被剔除。
除上述键以外的任何键（根级、actions 级或动作对象内部）都会导致整体 blocked；\
除 corridor_preferences 的 waypoints_mm 外，响应中不得出现任何几何坐标或布线\
几何数据。
fail-closed：board_snapshot_sha256 不匹配、route_order 非法、protect 含未知 \
net、出现未知键，任一成立则整份响应 blocked（不会部分生效）。
以上仅描述允许的动作空间与校验规则，不代表任何推荐策略。"""


def _board_paths(source_dir):
    """按 scenario_id 稳定序列出源目录中的板快照路径。"""
    names = [n for n in os.listdir(source_dir)
             if n.startswith("board-snapshot-") and n.endswith(".json")]
    return [os.path.join(source_dir, n)
            for n in sorted(names)]


def board_summary(board):
    """B/C 组共用的板摘要：不含 label（答案）、seed、split、family、schema。

    直接引用 board 中的子结构即可（构造后只读、只序列化，绝不原地修改）。
    """
    return {
        "bbox_mm": list(board["board"]["bbox_mm"]),
        "layers": list(board["board"]["layers"]),
        "rules": board["rules"],
        "pads": board["pads"],
        "nets": [{"net_id": str(n["net_id"]),
                  "net_class": str(n["net_class"]),
                  "endpoints": list(n["endpoints"])}
                 for n in board["nets"]],
        "keepouts": board["keepouts"],
        "relations": board["relations"],
    }


def png_rel_path(source_dir, scenario_id):
    """1200x675 PNG 指针：仓库相对路径（正斜杠，无主机绝对路径）。

    合同钉死 D 组指针形如 "out/v4-experiment/route-preview-<sid>-1200x675.png"；
    这里用 source_dir 实际定位文件，再换算成仓库相对形式。
    """
    png_abs = os.path.join(source_dir,
                           "route-preview-%s-%s.png" % (scenario_id,
                                                        PNG_SIZE_SPEC))
    try:
        rel = os.path.relpath(png_abs, _REPO_ROOT)
    except ValueError:  # 跨盘符等退化情形：退回裸文件名
        rel = "route-preview-%s-%s.png" % (scenario_id, PNG_SIZE_SPEC)
    return rel.replace(os.sep, "/")


def build_input(board, group, source_dir):
    """构造一个 planner 输入对象（不落盘）。"""
    sid = str(board["scenario_id"])
    # 哈希是内容寻址串，所有组都给（含 D 组）：保证响应能合法进入 solver；
    # D 组的规划信息仍然只有 PNG 指针。
    out = {"schema": INPUT_SCHEMA, "scenario_id": sid, "group": str(group),
           "board_snapshot_sha256": model.sha256_of(board)}
    if group in ("B", "C"):
        out["board_summary"] = board_summary(board)
    if group == "C":
        svg_path = os.path.join(source_dir, "route-preview-%s.svg" % sid)
        if not os.path.exists(svg_path):
            raise ValueError("C 组缺 SVG 源文件: %s" % svg_path)
        with open(svg_path, "r", encoding="utf-8") as f:
            out["svg_source"] = f.read()
        out["png_path"] = png_rel_path(source_dir, sid)
    if group == "D":
        out["inputs"] = [png_rel_path(source_dir, sid)]
    out["contract_text"] = CONTRACT_TEXT
    return out


def run(splits, groups, out_dir, source_dir="out/v4-experiment"):
    """对给定 split x 组合生成输入文件；返回写入清单（确定性排序）。"""
    if not splits:
        raise ValueError("splits 不能为空")
    bad_groups = [g for g in groups if g not in ("B", "C", "D")]
    if bad_groups:
        raise ValueError("groups 只允许 B|C|D，收到 %r" % (bad_groups,))
    os.makedirs(out_dir, exist_ok=True)

    written = []
    scenario_ids = []
    for path in _board_paths(source_dir):
        board = model.read_json(path)
        if str(board["split"]) not in splits:
            continue
        sid = str(board["scenario_id"])
        scenario_ids.append(sid)
        for group in groups:
            obj = build_input(board, group, source_dir)
            name = "planner-input-%s-%s.json" % (sid, group)
            model.write_json(os.path.join(out_dir, name), obj)
            written.append(name)
    return {"schema": "pcbflow.v4exp.planner-inputs-summary/1",
            "scenario_ids": scenario_ids, "groups": list(groups),
            "files_written": written}


def main():
    payload = model.read_stdin_json()
    summary = run(payload["splits"], payload["groups"], payload["out_dir"],
                  source_dir=payload.get("source_dir", "out/v4-experiment"))
    import sys
    sys.stdout.write(model.canonical_json(summary))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
