# -*- coding: utf-8 -*-
"""P5① 单板管线工具（A 层 holdout 试跑）：convert→compile→execute→postprocess
→check→export→drc。

用法：python tools/run_p5_board.py --board <id> --stages convert,compile,execute,postprocess,check,export,drc
     [--arm principle] [--rotate-budget K]

阶段合同：
  convert  adapter（v5.adapters.kicad_adapter.convert_bytes_with_report）读语料源
           .kicad_pcb → v5 board（落 boards/<id>/board.json，wrap+provenance 头）；
           打开源文件前先核 sha256=预注册值；双跑字节等断言。
  compile  build_partition_artifact + compile_board + build_conflicts + build_pkg；
           落 boards/<id>/compiled.json；compile_board 双跑字节等。
  execute  plan_candidates(arm) → select_best；select_best 命中先试 best；
           selection UNSAT 时按 P4 门 G1 口径（0.3.0 演进为轮换口径）从
           plan_candidates[0] 起进 execute_candidate。候选终局 FAILED
           （routes=None）时按候选序轮换下一候选重跑 execute_candidate，
           直至某候选 ROUTED 或试轮数耗尽（总试轮数=min(K, len(cands))，
           K=--rotate-budget 默认 4，含首轮；候选序即遍历序，确定性；
           select_best 命中时首轮行为不变）。首个 ROUTED 即收口走后续
           阶段；全败则与 NO_CANDIDATES 同款优雅收口（check/export/drc
           跳过、run-result 落盘）。candidate_source 口径演进（0.3.0 披露）：
           成功时=plan_candidates[k]（k=实际成功下标，如实），全败时=null；
           0.2.x 语义为 select_best.best / plan_candidates[0]（首轮选择依据）。
           execute 段逐轮登记 tried_candidates=[{index, verdict,
           first_fail_net(可提取时)}...]（plan_candidates 自带等价计划去重，
           轮换不再滤重）。落 boards/<id>/execute.json；routes_doc 双跑字节等。
  postprocess（V5-R8 TB2 D-1，0.6.0 插入）execute 后三原语确定性后处理
           （v5.postprocess.postprocess_routes：P1 共线合并/P2a 往返对消/
           P2b 台阶压缩/P3 冗余 via 删减，逐动作全量复检+回流对守卫）。
           双留：routes-raw.json（=execute.json 内嵌 routes_doc 原样拷贝）
           + routes-final.json（后处理产物 routes_doc+postprocess 化简账）；
           execute.json 零改（executor raw 事实源保持）。run["postprocess"]
           记账块（类计数/不动点/预算/终检读数）。
  check    check_routes（v5 内源口径）；落 boards/<id>/check.json。输入=
           load_routes_doc（D-1 懒加载单点：routes-final.json 在场优先，
           否则 execute.json 内嵌 routes_doc）。
  export   kicad_pcb_bytes 落 boards/<id>/<id>.kicad_pcb；双跑字节等。
           输入=load_routes_doc（同上 D-1 懒加载序）。
  drc      kicad-cli pcb drc --format json --severity-all（外权威）。原始报告只提
           计数不落盘（临时文件即用即删，参照 build_p4_gate.py G3 口径）；逐条
           违例三归类（config-gap / contract-artifact / genuine）落
           boards/<id>/drc-classified.json（0.4.0 词表补已知类：padstack、
           copper_edge_clearance，判据总表见常量区注释与
           classify_kicad_violations docstring）。运行方式按 P5-UP3 口径钉死
           （下节）。

P5-UP3 口径钉死（2026-09-14 用户裁定「外权威 kicad-cli 口径确定化——门判据可
复现」，升级件③）：

  调研结论（kicad-cli 10.0.5，本机 F:/kicad/bin，2026-09-14 实证）：并发不可控。
    - `pcb drc --help` 全文可选参数仅 --output / --define-var / --format /
      --all-track-errors / --schematic-parity / --units / --severity-all /
      --severity-error / --severity-warning / --severity-exclusions /
      --exit-code-violations / --refill-zones / --save-board；
      顶层 `kicad-cli --help` 仅 fp/jobset/pcb/sch/sym/version——无任何
      线程/并发/资源数控制面。
    - 二进制串证据：kicad-cli.exe、_pcbnew.dll、kicommon.dll 中无
      OMP_NUM_THREADS、无 TBB、无 single-thread/multi-thread/num-threads 类
      字符串；线程池为内部实现（kicommon.dll 导出
      GetKiCadThreadPool/InvalidateKiCadThreadPool，无外部尺寸控制面）；
      KICAD_* 环境变量串中无线程类（仅 KICAD_USER_TEMPLATE_DIR、
      KICAD_SETTINGS 等）；本机 KiCad 10.0 配置目录无 kicad_advanced.json，
      pcbnew.json 等 GUI 偏好亦无线程键。
    - 佐证（P5①/② 实测）：同字节导出件 badgeleds 6 跑 totals
      95/96/102/97/102/97、pmod-bme280 3 跑 [171,171,170]。

  口径（不可控 → 聚合协议）：每轮固定 N=5 跑同字节导出件；判据=一轮 5 跑
    violations_total 全等 → verdict=deterministic-5x-equal（门判据锚该轮，
    可复现）；不全等则再跑至多 2 轮（共至多 3 轮 15 跑）；仍无全等轮 →
    verdict=nondeterministic-disclosed，判据=全部已跑逐类并集最大值
    （violations_total / unconnected_items / schematic_parity / classified
    三类 / by_type 各自跨跑 max）并显式披露。config-gap / contract-artifact /
    genuine 三归类按并集口径判（锚定跑集内逐类跨跑 max，覆盖同总数下
    by-type 漂移的更早已知事实）。

纪律：
  - 只准 A 层预注册板（p5_holdout_ledger.A_LAYER_PREREG）；每次内容接触前先
    向接触史台账（tools/p5_holdout_ledger.py）落对应事件：convert→convert、
    compile/execute/check/export→pipeline、drc→drc。
  - 零网络、零 LLM API；产物全部 out/v5-p5/ 之下（sidecar 卫生），canonical
    +provenance 头，无时间戳（确定性；接触时序唯一权威在台账）。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import p5_holdout_ledger as ledger  # noqa: E402
from v5 import canonical, sidecar, staging  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.executor import execute_candidate  # noqa: E402
from v5.jitems import build_j_items  # noqa: E402
from v5.kicad_export import kicad_pcb_bytes  # noqa: E402
from v5.overlay import build_conflicts, validate_conflicts_artifact  # noqa: E402
from v5.partition import build_partition_artifact  # noqa: E402
from v5.pkg import build_pkg, validate_pkg  # noqa: E402
from v5.planner import plan_candidates  # noqa: E402
from v5.postprocess import POSTPROCESS_VERSION, postprocess_routes  # noqa: E402
from v5.route_check import check_routes  # noqa: E402
from v5.selection import select_best  # noqa: E402

GENERATOR = "v5.p5-board-runner"
VERSION = "0.6.0"  # V5-R8 最小后处理包（TB2 D-8）：STAGE_ORDER/PIPELINE_STAGES
                   # 于 execute 后插入 postprocess 阶段（v5.postprocess/1.0.0
                   # 三原语确定性等价化简）；D-1 双留接线=routes-raw.json
                   # （execute.json 内嵌 routes_doc 原样拷贝）+routes-final.json
                   # （后处理产物+化简账），execute.json 零改；下游 check/export
                   # 懒加载序=routes-final.json 在场优先否则 execute.json
                   # （load_routes_doc 单点）；run["postprocess"] 记账块。
                   # ；0.5.0=V5-D8：分类器词表 hole_to_hole 分支——items 含 via 项
                   # →hole_to_hole-engine（引擎过孔 vs 板固孔=引擎可避，入
                   # 判据二分子；executor 0.6.0 禁布带后应趋零）；两项均非
                   # via→hole_to_hole-board-inherent（板固孔对间距<0.25=板设计
                   # 固有，非布线可避，如实披露呈裁、不入判据二分子——用户
                   # 裁定④口径）；DRC_CATEGORIES 三元扩五元；--operator 可选
                   # 参数（D8 批=d8-worldswap-subagent+extra sha16，红线 5）
                   # ；0.4.0=P5⑥-D6-4（padstack/copper_edge_clearance 词表）
OUT = os.path.join(ROOT, "out", "v5-p5")
KICAD_CLI = "F:/kicad/bin/kicad-cli.exe"  # 用户确认本机 KiCad 10.0.5（P4 已核）
STAGE_ORDER = ("convert", "compile", "execute", "postprocess", "check",
               "export", "drc")
PIPELINE_STAGES = ("compile", "execute", "postprocess", "check", "export")
SHARED_PT_TOL_MM = 1.0
# P5-UP3 口径（不可控→聚合协议）：每轮固定 5 跑同字节导出件；判据=一轮 5 跑
# totals 全等（否则至多再跑 2 轮，仍不等取全部已跑逐类并集最大值并标注
# nondeterministic-disclosed）。
DRC_RUNS = 5
DRC_MAX_EXTRA_ROUNDS = 2
# V5-D8（0.5.0）扩五元：hole_to_hole 违例不再走兜底 genuine，分
# engine（items 含 via 项，入分子）/board-inherent（两项均非 via，披露类
# 不入判据二分子）。
DRC_CATEGORIES = ("config-gap", "contract-artifact", "genuine",
                  "hole_to_hole-engine", "hole_to_hole-board-inherent")
# P5-UP3 起本工具所落事件归属升级件③执行体（P5① seq≤30、P5② seq≤41 已固化
# 在案，不改写）。V5-D8 起可经 --operator 覆盖（D8 批=d8-worldswap-subagent）。
OPERATOR = "p5-part3-subagent"
# V5-D8 批事件 extra 附加（--extra-json 透传；红线 5 任务书 sha16 锚）。
EXTRA_DEFAULT = None
# P5⑤-F3：execute 终局 FAILED 的候选轮换确定性预算（总试轮数=min(K, len(cands))，
# 含首轮；--rotate-budget 可调）。
ROTATE_BUDGET = 4

# kicad-cli 违例三归类判据（P4-G3 差异台账经验 + 试跑实测细化；0.4.0 补
# padstack / copper_edge_clearance 已知类，P5⑥-D6-4）：
#   genuine           = v5 route_check 同网对也归责（两权威一致，真布线问题）；
#                       copper_edge_clearance 与 v5 route_check edge_violations
#                       同位同网归责（SHARED_PT_TOL_MM 口径）
#   contract-artifact = 板合同抽象与制造现实的披露差异（焊盘=端点带、过孔不进
#                       间距场景、回流孔同位、逃逸孔不对称悬空）；padstack
#                       焊盘层跨出口画法披露差（⑥后应=0，非零逐板披露）；
#                       copper_edge_clearance 世界模型保真差（无同位归责且
#                       板无显式异值边距规则）
#   config-gap        = 规则配置不同源（kicad 缺省净类间距 vs v5 R5 0.5mm
#                       中心线口径；出口封装库未注册 kicad-cli 运行配置；
#                       copper_edge_clearance 板显式边距规则值 ≠ kicad 缺省
#                       0.2mm，值源不同）
CONFIG_GAP_TYPES = {"clearance"}
# P5⑥-D6-3 带值（合同定案）：kicad-cli 生效缺省 copper_edge_clearance；v5 侧
# 板无显式边距规则时同值同源（0.2mm），板带显式规则时板值优先（若 ≠0.2mm，
# 分类器据此判 config-gap，见 copper_edge_clearance 分支）。
KICAD_EDGE_CLEARANCE_DEFAULT_MM = 0.2
# board.json 显式边距规则的 compiled_rule.kind 词表（防御式：显式清单 ∪
# 同时含 edge 与 clear/margin 的子串规则；D6-3 落点在兄弟包，词表取宽防御）。
_EDGE_RULE_KINDS = ("edge_clearance", "copper_edge_clearance", "edge_margin",
                    "board_edge_clearance", "board_edge_margin")
_EDGE_VALUE_KEYS = ("min_clearance_mm", "clearance_mm", "margin_mm",
                    "value_mm", "width_mm", "value")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _with_extra(extra):
    """台账 extra 合并 --extra-json 追加项（V5-D8 红线 5 任务书 sha16 锚）。"""
    merged = dict(extra or {})
    if EXTRA_DEFAULT:
        merged.update(EXTRA_DEFAULT)
    return merged


def count_by(items, key):
    out = {}
    for it in items:
        k = str(it.get(key, "<none>"))
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def _first_fail_net(per_net):
    """per_net 中首个 failed 项的 net_id（可提取时）；无可提取项返回 None。"""
    for e in per_net or []:
        if isinstance(e, dict) and str(e.get("status", "")) == "failed":
            return e.get("net_id")
    return None


def write_stage(path, payload, board_sha256):
    return sidecar.write_sidecar(path, payload, GENERATOR, VERSION,
                                 board_sha256)


def load_stage_board(board_id):
    with open(board_json_path(board_id), encoding="utf-8") as f:
        doc = json.load(f)
    return load_board(doc["board"])


def board_dir(board_id):
    return os.path.join(OUT, "boards", board_id)


def board_json_path(board_id):
    return os.path.join(board_dir(board_id), "board.json")


def load_routes_doc(odir):
    """D-1（V5-R8 TB2）下游懒加载单点：routes-final.json 在场优先，否则
    execute.json 内嵌 routes_doc。check/export 阶段一律经此取 doc；返回
    None=无 ROUTED 工件（调用方 SystemExit）。"""
    final = os.path.join(odir, "routes-final.json")
    if os.path.isfile(final):
        with open(final, encoding="utf-8") as f:
            return json.load(f)["routes_doc"]
    with open(os.path.join(odir, "execute.json"), encoding="utf-8") as f:
        return json.load(f)["routes_doc"]


# ---------------------------------------------------------------- 三归类

def _net_endpoint_points(board):
    """net_id → 分区端点坐标集（board["nets"] 反查 partitions；端点=板合同
    中该网的物理连接点/焊盘抽象位）。"""
    pid_pts = {}
    for p in board.get("partitions", []):
        for pt in (p.get("geometry") or {}).get("endpoints") or []:
            pid_pts.setdefault(p.get("partition_id"), []).append(
                (round(float(pt[0]), 2), round(float(pt[1]), 2)))
    out = {}
    for n in board.get("nets", []):
        nid = str(n.get("net_id", ""))
        pts = []
        for pid in n.get("partitions", []):
            pts.extend(pid_pts.get(pid, []))
        out[nid] = sorted(set(pts))
    return out


def _v5_violation_net_pairs(cr):
    pairs = set()
    for v in cr.get("violations", []):
        nets = []
        for subj in v.get("subjects", []):
            m = re.match(r"^[a-z]+:([^:]+):", str(subj))
            if m:
                nets.append(m.group(1))
        if len(nets) == 2:
            pairs.add(tuple(sorted(nets)))
    return pairs


def _item_kind(desc):
    stripped = re.sub(r"\[[^\[\]]*\]", "", desc)  # 剥网名段（Net-(C1-Pad1) 含 pad）
    low = stripped.lower()
    if "焊盘" in stripped or "pad" in low:
        return "pad"
    if "过孔" in stripped or "via" in low:
        return "via"
    if "走线" in stripped or "track" in low:
        return "track"
    return "other"


def _violation_items(v, net_ids):
    items = v.get("items") or []
    out = []
    for it in items:
        pos = it.get("pos")
        xy = None
        if isinstance(pos, dict):
            xy = (pos.get("x"), pos.get("y"))
        elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
            xy = (pos[0], pos[1])
        desc = str(it.get("description", ""))
        out.append({"description": desc, "kind": _item_kind(desc),
                    "nets": _parse_nets(desc, net_ids),
                    "pos": [round(float(xy[0]), 3), round(float(xy[1]), 3)]
                    if xy is not None and xy[0] is not None else None})
    return out


def _parse_nets(text, board_net_ids):
    """从 kicad-cli 中文描述提取网名：方括号 [NET]、模式 网络 X 和 Y、
    net "X"（kicad 英文形态）。只收与板网字典精确（大小写不敏感）匹配者。"""
    found = []
    lowers = {str(n).lower(): str(n) for n in board_net_ids}
    candidates = []
    for m in re.finditer(r"\[([^\[\]]+)\]", text):
        candidates.append(m.group(1).strip())
    for m in re.finditer(r"网络\s+(\S+)\s+和\s+(\S+)", text):
        candidates.extend([m.group(1).strip(), m.group(2).strip()])
    for m in re.finditer(r'net\s+"([^"]+)"', text, flags=re.IGNORECASE):
        candidates.append(m.group(1).strip())
    for cand in candidates:
        nid = lowers.get(cand.lower().strip(",;.'\""))
        if nid and nid not in found:
            found.append(nid)
    return found


def _pos_xy(pos):
    """kicad/v5 位置字段 → (x, y) float（dict {x,y} 或 [x, y] 序列形态均收）；
    不可辨返回 None（防御式，不抛异常）。"""
    if isinstance(pos, dict):
        x, y = pos.get("x"), pos.get("y")
    elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
        x, y = pos[0], pos[1]
    else:
        return None
    if x is None or y is None:
        return None
    try:
        return (float(x), float(y))
    except (TypeError, ValueError):
        return None


def _explicit_edge_margin_mm(board):
    """board.json 显式板边距规则值（mm）；无则 None（D6-4 config-gap 分支
    「字段不存在的板自然不命中」）。

    board.v1 schema 冻结（hard_rules/workspace 均 additionalProperties:false），
    显式边距规则唯一可合法落值的容器是 principle_registry[].compiled_rule
    对象（schema 只约束非空字符串 kind）；workspace 边距键为前向兼容防御
    扫描。扫描次序固定：principle_registry（注册表序=确定性）→ workspace，
    首个命中即返回；kind 词表见 _EDGE_RULE_KINDS，值须为正数（bool 除外）。"""
    for entry in board.get("principle_registry") or []:
        rule = entry.get("compiled_rule") if isinstance(entry, dict) else None
        if not isinstance(rule, dict):
            continue
        kind = str(rule.get("kind", "")).lower()
        if not (kind in _EDGE_RULE_KINDS
                or ("edge" in kind and ("clear" in kind or "margin" in kind))):
            continue
        for k in _EDGE_VALUE_KEYS:
            v = rule.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) \
                    and v > 0:
                return float(v)
    ws = board.get("workspace")
    if isinstance(ws, dict):
        for k in _EDGE_VALUE_KEYS:
            v = ws.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) \
                    and v > 0:
                return float(v)
    return None


def classify_kicad_violations(drc, board, cr):
    """kicad-cli DRC 逐条三归类。返回 (rows, counts)。只取派生字段
    （type/severity/description/items 位置与网名），不落原始报告。

    判据（P4-G3 差异台账 LEDGER_NOTES + 本板实测几何校准；0.4.0 补
    padstack / copper_edge_clearance 已知类，P5⑥-D6-4）：
      genuine           v5 route_check 同网对亦有归责（两权威一致）；或含两个
                        纯走线项的短接/间距且无端点判据（保守归真）；或
                        copper_edge_clearance 与 v5 route_check edge_violations
                        同位同网归责（SHARED_PT_TOL_MM 口径）。
      contract-artifact 焊盘/过孔物理铜 vs v5 端点带抽象（v5 间距场景不含
                        过孔、焊盘=带端点非物理圆）；换层孔/回流孔同位披露；
                        逃逸孔不对称悬空；v5 已布通网的连接披露差；padstack
                        焊盘层跨出口画法披露差（⑥后应=0，非零逐板披露）；
                        copper_edge_clearance 无同位归责且板无显式异值边距
                        规则（世界模型保真差）。
      config-gap        kicad 缺省净类间距 0.2mm（边到边）vs v5 R5 0.5mm
                        中心线口径；kicad-cli 运行配置未注册 V5 封装库；
                        copper_edge_clearance 板显式边距规则值 ≠ kicad 缺省
                        0.2mm（值源不同，两侧计数不可直接互判）。
    """
    net_ids = [str(n.get("net_id", "")) for n in board.get("nets", [])]
    net_eps = _net_endpoint_points(board)
    v5_pairs = _v5_violation_net_pairs(cr)
    routed_nets = {str(e.get("net_id", "")) for e in
                   (cr.get("_routes_entries") or [])}

    def near_endpoint(pos):
        if pos is None:
            return False
        for pts in net_eps.values():
            for (px, py) in pts:
                if abs(pos[0] - px) <= SHARED_PT_TOL_MM and \
                   abs(pos[1] - py) <= SHARED_PT_TOL_MM:
                    return True
        return False

    rows = []
    entries = [{"kind": "violation", **v} for v in drc.get("violations", [])]
    entries += [{"kind": "unconnected", "type": "unconnected_items", **v}
                for v in drc.get("unconnected_items", [])]
    for v in entries:
        vtype = str(v.get("type", "<none>"))
        items = _violation_items(v, net_ids)
        nets = []
        for it in items:
            for nid in it["nets"]:
                if nid not in nets:
                    nets.append(nid)
        for nid in _parse_nets(str(v.get("description", "")), net_ids):
            if nid not in nets:
                nets.append(nid)
        pair = tuple(sorted(nets)) if len(nets) == 2 else None
        at_endpoint = any(near_endpoint(it["pos"]) for it in items)
        kinds = {it["kind"] for it in items}

        if pair and pair in v5_pairs:
            cat, why = "genuine", ("v5 route_check 同网对 %s 亦有归责违例"
                                   "（两权威一致）" % (pair,))
        elif vtype == "shorting_items":
            if kinds & {"pad", "via"}:
                cat = "contract-artifact"
                why = ("含 %s 项的短接：v5 世界模型焊盘=分区端点带（不带物理"
                       "焊盘扩展）、过孔不进间距场景（P4 披露口径），kicad 实"
                       "几何下呈现为短路；v5 同网对无归责违例"
                       % "+".join(sorted(kinds & {"pad", "via"})))
            elif at_endpoint:
                cat = "contract-artifact"
                why = "短接位置落于分区端点容差内（端点/共端点抽象）"
            else:
                cat, why = "genuine", "两走线短接且无端点/焊盘/过孔判据（保守归真）"
        elif vtype == "holes_co_located":
            cat = "contract-artifact"
            why = ("钻孔同位：换层孔与回流孔同点披露（executor return_vias "
                   "与 transition_vias 同位），v5 不作同位约束")
        elif vtype == "lib_footprint_issues":
            cat = "config-gap"
            why = ("kicad-cli 运行配置未注册出口封装库（'V5' 库不在当前配置），"
                   "非布线几何问题")
        elif vtype in ("track_dangling", "via_dangling"):
            cat = "contract-artifact"
            why = ("悬空端=执行器披露口径（焊盘逃逸孔不对称：起点披露/终点不"
                   "披露；过孔回流孔不进 v5 场景）")
        elif vtype == "unconnected_items":
            if nets and all(n in routed_nets for n in nets) and \
                    cr.get("feasible") is True:
                cat = "contract-artifact"
                why = ("v5 已布通该网（routes 在场且 route_check feasible），"
                       "kicad 视为未连=出口披露口径差异")
            else:
                cat, why = "genuine", "v5 侧未布通或不可辨识（保守归真）"
        elif vtype == "padstack":
            cat, why = "contract-artifact", (
                "焊盘层跨出口画法披露差：⑥前导出对焊盘按 layers='all' 全铜层"
                "转录（SMD 焊盘呈两面铜，kicad 视角跨层假象）；⑥后按真实层跨"
                "画法（D6-1）应=0，非零逐板披露进修订口径候选清单")
        elif vtype == "copper_edge_clearance":
            hit = None
            for ev in (cr.get("edge_violations") or []):
                if not isinstance(ev, dict):
                    continue
                if str(ev.get("net_id", "")) not in nets:
                    continue  # 同位还须同网归责（归责=网+位）
                epos = _pos_xy(ev.get("pos"))
                if epos is None:
                    continue
                if any(it["pos"] is not None
                       and abs(it["pos"][0] - epos[0]) <= SHARED_PT_TOL_MM
                       and abs(it["pos"][1] - epos[1]) <= SHARED_PT_TOL_MM
                       for it in items):
                    hit = ev
                    break
            if hit is not None:
                epos = _pos_xy(hit.get("pos"))
                cat, why = "genuine", (
                    "v5 route_check edge_violations 同位同网归责（net=%s @ "
                    "(%.3f, %.3f)，|Δx|/|Δy|≤%s 同位口径）：两权威一致，真贴边"
                    "问题" % (hit.get("net_id"), epos[0], epos[1],
                              SHARED_PT_TOL_MM))
            else:
                margin = _explicit_edge_margin_mm(board)
                if margin is not None and \
                        abs(margin - KICAD_EDGE_CLEARANCE_DEFAULT_MM) > 1e-9:
                    cat, why = "config-gap", (
                        "板显式边距规则值 %.3gmm ≠ kicad-cli 生效缺省 "
                        "copper_edge_clearance %.3gmm（值源不同：v5 按板值"
                        "自查、kicad 按缺省边距带判，两侧计数不可直接互判）"
                        % (margin, KICAD_EDGE_CLEARANCE_DEFAULT_MM))
                else:
                    cat, why = "contract-artifact", (
                        "v5 世界模型无板边概念（世界模型保真差）：v5 "
                        "edge_violations 无同位同网归责、板亦无显式异值边距"
                        "规则，executor 合法贴边走线被 kicad 缺省 %.3gmm 边距"
                        "带判违例；⑥后 executor 禁布带+route_check/drc 同规则"
                        "落地应趋零，非零逐板披露"
                        % KICAD_EDGE_CLEARANCE_DEFAULT_MM)
        elif vtype == "hole_to_hole":
            # V5-D8（0.5.0）：板固孔全量入模（board.holes[]）后的孔距分类。
            if "via" in kinds:
                cat, why = "hole_to_hole-engine", (
                    "引擎布线过孔 vs 板固孔钻孔（items 含 via 项）：引擎可避"
                    "——executor 0.6.0 板固孔禁布带（V5-D8）闭合此差口，"
                    "非零=引擎未避净或执行/复核不一致，入判据二分子")
            else:
                cat, why = "hole_to_hole-board-inherent", (
                    "板固孔对间距 <0.25mm（items 两项均非 via）：板设计固有、"
                    "非布线可避，如实分类披露呈裁不硬凑；不入判据二分子"
                    "（用户 2026-09-22 裁定④口径）")
        elif vtype in CONFIG_GAP_TYPES:
            cat = "config-gap"
            why = ("clearance 违例且 v5 同网对无归责：kicad 缺省净类间距 "
                   "0.2mm（边到边）+ 过孔/焊盘物理铜 vs v5 R5 0.5mm 中心线"
                   "口径（不同源），两侧计数不可直接互判")
        else:
            cat, why = "genuine", "无 v5 对应归责且无合同/配置判据（保守归真）"
        rows.append({"kind": v.get("kind"), "type": vtype,
                     "severity": v.get("severity"),
                     "description": str(v.get("description", ""))[:200],
                     "items": items, "nets": nets,
                     "category": cat, "rationale": why})
    counts = count_by(rows, "category")
    for k in DRC_CATEGORIES:
        counts.setdefault(k, 0)
    parity = len(drc.get("schematic_parity", []))
    return rows, {"violations_total": len(drc.get("violations", [])),
                  "unconnected_items": len(drc.get("unconnected_items", [])),
                  "schematic_parity": parity,
                  "classified": counts}


def _drc_single_run(board_id, tmp_json, round_idx, idx, board, cr):
    """单跑 kicad-cli + 逐条三归类。原始报告即用即删，不落盘。"""
    try:
        proc = subprocess_run([KICAD_CLI, "pcb", "drc", "--output", tmp_json,
                               "--format", "json", "--severity-all",
                               "--units", "mm",
                               os.path.join(board_dir(board_id),
                                            "%s.kicad_pcb" % board_id)])
        assert proc.returncode == 0 and os.path.isfile(tmp_json), (
            board_id, proc.returncode, (proc.stderr or "")[:300])
        with open(tmp_json, encoding="utf-8") as f:
            drc = json.load(f)
    finally:
        if os.path.isfile(tmp_json):
            os.remove(tmp_json)  # 原始 DRC 报告不落盘
    rows, counts = classify_kicad_violations(drc, board, cr)
    return {"round_index": round_idx, "run_index": idx, "counts": counts,
            "by_type_observation": count_by(drc.get("violations", []), "type"),
            "classified_rows": rows}


def _union_max(runs):
    """全部已跑逐类并集最大值（P5-UP3 nondeterministic-disclosed 判据）。"""
    def mx(key):
        return max(r["counts"][key] for r in runs)
    agg = {"violations_total": mx("violations_total"),
           "unconnected_items": mx("unconnected_items"),
           "schematic_parity": mx("schematic_parity"),
           "classified": {c: max(r["counts"]["classified"][c]
                                 for r in runs)
                          for c in DRC_CATEGORIES}}
    type_keys = set()
    for r in runs:
        type_keys.update(r["by_type_observation"])
    agg["by_type_observation"] = {t: max(r["by_type_observation"].get(t, 0)
                                         for r in runs)
                                  for t in sorted(type_keys)}
    return agg


def run_drc(board_id, board, cr):
    """drc 阶段（P5-UP3 口径钉死，v0.2.0）：同字节导出件按聚合协议跑。

    协议：每轮 DRC_RUNS=5 跑；一轮 totals 全等 → deterministic-5x-equal
    （门判据锚该轮）；否则至多再 DRC_MAX_EXTRA_ROUNDS=2 轮；仍无全等轮 →
    nondeterministic-disclosed，判据=全部已跑逐类并集最大值（_union_max）。
    verdict/逐跑 totals/并集 max/导出件 sha256 追加登记进接触史台账
    （action=drc 结果登记事件）。原始报告只提计数不落盘。
    """
    pcb = os.path.join(board_dir(board_id), "%s.kicad_pcb" % board_id)
    if not os.path.isfile(pcb):
        raise FileNotFoundError("drc 需先 export：%s 不存在" % pcb)
    with open(pcb, "rb") as f:  # 预登记事件（main 内）之后才触内容
        export_sha = sha256_bytes(f.read())
    tmp_dir = os.path.join(OUT, "_drc-tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_json = os.path.join(tmp_dir, board_id + ".drc.json")
    rounds = []
    try:
        for round_idx in range(1, DRC_MAX_EXTRA_ROUNDS + 2):
            runs = [_drc_single_run(board_id, tmp_json, round_idx, idx,
                                    board, cr)
                    for idx in range(1, DRC_RUNS + 1)]
            rounds.append(runs)
            if len({r["counts"]["violations_total"] for r in runs}) == 1:
                break  # 全等轮出现，判据可锚定，停止加跑
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    all_runs = [r for rd in rounds for r in rd]
    totals = [r["counts"]["violations_total"] for r in all_runs]
    rounds_totals = [[r["counts"]["violations_total"] for r in rd]
                     for rd in rounds]
    stable = len(rounds_totals[-1]) == DRC_RUNS and \
        len(set(rounds_totals[-1])) == 1
    verdict = ("deterministic-5x-equal" if stable
               else "nondeterministic-disclosed")
    criterion_runs = rounds[-1] if stable else all_runs
    aggregate = _union_max(criterion_runs)
    ledger.append(board_id, "drc",
                  "P5-UP3 drc 结果登记（非接触）：同字节导出件 %d 轮×每轮 %d 跑"
                  "聚合协议，verdict=%s；逐跑 totals/by-type/三归类、并集 max 与"
                  "导出件 sha256 全量入账%s"
                  % (len(rounds), DRC_RUNS, verdict,
                     "" if stable else "（判据=并集 max）"),
                  ledger.source_path_for(board_id),
                  ledger.A_LAYER_PREREG[board_id]["sha256"], operator=OPERATOR,
                  extra=_with_extra({"nondeterministic": not stable, "verdict": verdict,
                         "runs_per_round": DRC_RUNS, "n_rounds": len(rounds),
                         "rounds_totals": rounds_totals,
                         "aggregate_union_max": aggregate,
                         "export_sha256": export_sha,
                         "runs": [{"round_index": r["round_index"],
                                   "run_index": r["run_index"],
                                   "violations_total":
                                       r["counts"]["violations_total"],
                                   "unconnected_items":
                                       r["counts"]["unconnected_items"],
                                   "schematic_parity":
                                       r["counts"]["schematic_parity"],
                                   "by_type_observation":
                                       r["by_type_observation"],
                                   "classified": r["counts"]["classified"]}
                                  for r in all_runs]}))
    return {"kicad_cli": {"path": KICAD_CLI,
                          "version": subprocess_run([KICAD_CLI, "version"]).stdout.strip()},
            "protocol": {"name": "P5-UP3-aggregate-v1",
                         "runs_per_round": DRC_RUNS,
                         "max_extra_rounds": DRC_MAX_EXTRA_ROUNDS,
                         "rule": ("一轮 %d 跑 totals 全等→deterministic-5x-equal"
                                  "（锚该轮）；否则至多再 %d 轮；仍无全等轮→"
                                  "nondeterministic-disclosed，判据=全部已跑"
                                  "逐类并集最大值" % (DRC_RUNS,
                                                      DRC_MAX_EXTRA_ROUNDS)),
                         "cli_concurrency": "uncontrolled（10.0.5 无线程控制"
                                            "面，调研原文见工具 docstring）"},
            "verdict": verdict,
            "n_rounds": len(rounds), "n_runs": len(all_runs),
            "totals_in_order": totals, "rounds_totals": rounds_totals,
            "aggregate_union_max": aggregate,
            "export_sha256": export_sha,
            "runs": [{k: v for k, v in r.items() if k != "classified_rows"}
                     for r in all_runs],
            "classified_rows_per_run": [r["classified_rows"] for r in all_runs],
            "note": "P5-UP3 口径：判据锚定跑集=%s；classified 三类按锚定跑集内"
                    "逐类跨跑 max（并集口径，覆盖同总数下 by-type 漂移的更早已知"
                    "事实）；全部逐跑 totals/by-type 入台账（drc 结果登记事件）"
                    % ("全等轮（第 %d 轮）" % len(rounds) if stable
                       else "全部 %d 跑" % len(all_runs))}


def subprocess_run(cmd):
    import subprocess
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                          timeout=600)


# ---------------------------------------------------------------- 主流程

def main(argv=None):
    global OPERATOR, EXTRA_DEFAULT   # --operator/--extra-json 覆盖（V5-D8）
    ap = argparse.ArgumentParser(description="P5① 单板管线（A 层 holdout）")
    ap.add_argument("--board", required=True)
    ap.add_argument("--stages",
                    default=",".join(STAGE_ORDER),
                    help="逗号组合：%s" % ",".join(STAGE_ORDER))
    ap.add_argument("--arm", default="principle")
    ap.add_argument("--rotate-budget", type=int, default=ROTATE_BUDGET,
                    help="execute 终局 FAILED 时的候选轮换预算 K：总试轮数="
                         "min(K, len(cands))（含首轮），默认 4")
    ap.add_argument("--operator", default=None,
                    help="台账 operator 覆盖（缺省=%s；D8 批="
                         "d8-worldswap-subagent，V5-D8 红线 5）" % OPERATOR)
    ap.add_argument("--extra-json", default=None,
                    help='台账全部事件 extra 追加 JSON（如 '
                         '{"taskbook_sha16":"2ff273e0d262444a"}）')
    args = ap.parse_args(argv)
    if args.rotate_budget < 1:
        raise SystemExit("--rotate-budget 须 ≥1，得到 %d" % args.rotate_budget)
    if args.operator:
        OPERATOR = args.operator
    if args.extra_json:
        EXTRA_DEFAULT = json.loads(args.extra_json)
        if not isinstance(EXTRA_DEFAULT, dict):
            raise SystemExit("--extra-json 须为 JSON object")

    board_id = args.board
    if board_id not in ledger.A_LAYER_PREREG:
        raise SystemExit("板 %s 不在 A 层预注册清单，本工具只准 A 层" % board_id)
    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    for s in stages:
        if s not in STAGE_ORDER:
            raise SystemExit("非法 stage: %s" % s)
    stages = [s for s in STAGE_ORDER if s in stages]
    prereg = ledger.A_LAYER_PREREG[board_id]
    odir = board_dir(board_id)
    os.makedirs(odir, exist_ok=True)
    run = {"board_id": board_id, "stages_run": stages, "arm": args.arm,
           "prereg": {"net_count": prereg["nets"], "layers": prereg["layers"],
                      "source_sha256_prereg": prereg["sha256"]}}

    # ---- 台账先落事件，再触内容 ----
    if "convert" in stages:
        ledger.append(board_id, "convert",
                      "P5② convert：读语料源 .kicad_pcb 经 adapter 转 v5 board",
                      ledger.source_path_for(board_id), prereg["sha256"],
                      extra=_with_extra({"stages": stages}), operator=OPERATOR)
    if any(s in stages for s in PIPELINE_STAGES):
        ledger.append(board_id, "pipeline",
                      "P5② pipeline 阶段：%s（派生自已转板数据，无新源接触）"
                      % ",".join(s for s in stages if s in PIPELINE_STAGES),
                      ledger.source_path_for(board_id), prereg["sha256"],
                      extra=_with_extra({"stages": stages}), operator=OPERATOR)
    elif "drc" in stages:
        ledger.append(board_id, "pipeline",
                      "P5-UP3 drc-only 稳定性验证：读取派生工件 board.json/"
                      "check.json/execute.json（无新 A 层源接触）",
                      ledger.source_path_for(board_id), prereg["sha256"],
                      extra=_with_extra({"stages": stages}), operator=OPERATOR)

    # ---- convert ----
    board = None
    if "convert" in stages:
        src = ledger.source_path_for(board_id)
        with open(src, "rb") as f:
            data = f.read()
        actual = sha256_bytes(data)
        if actual != prereg["sha256"]:
            raise SystemExit("%s 源哈希与预注册不符：actual=%s" % (board_id, actual))
        uri = os.path.abspath(src).replace("\\", "/")
        try:
            board, report = _convert(data, board_id, uri)
        except Exception as exc:  # 真实板特性转换失败：如实登记并跳过
            err_name = type(exc).__name__
            write_stage(os.path.join(odir, "convert-failed.json"),
                        {"convert_failed": {
                            "board_id": board_id,
                            "source_uri": uri,
                            "source_sha256": actual,
                            "error_class": err_name,
                            "error_message": str(exc)[:500],
                            "disposition": "adapter 对该板源转换失败（真实板"
                                           "特性）；如实登记，跳过该板，不阻塞"
                                           "其余板（P5① 任务令 §交付 5）"}},
                        prereg["sha256"])
            ledger.append(board_id, "convert",
                          "convert 失败登记：adapter %s：%s"
                          % (err_name, str(exc)[:160]),
                          src, prereg["sha256"],
                          extra=_with_extra({"error_class": err_name}),
                          operator=OPERATOR)
            print("convert FAILED (%s): %s" % (err_name, str(exc)[:120]))
            print("failure record: out/v5-p5/boards/%s/convert-failed.json"
                  % board_id)
            return 1
        board2, _rp2 = _convert(data, board_id, uri)
        board2, _rp2 = _convert(data, board_id, uri)
        det = canonical.canonical_json(board) == canonical.canonical_json(board2)
        assert det, "convert 双跑字节不等"
        board, gran_injected = _seed_granularity(board)
        bsha = board["provenance"]["board_sha256"]
        write_stage(board_json_path(board_id),
                    {"board": board, "adapter_report": report}, bsha)
        run["convert"] = {
            "source_uri": uri, "source_sha256": actual,
            "hash_matches_prereg": True,
            "board_sha256": bsha,
            "nets": len(board["nets"]), "partitions": len(board["partitions"]),
            "adapter_report": report, "double_run_equal": det,
            "granularity_prior_injected": gran_injected,
            "granularity_note": "adapter 出板注册表为空；L1 fail-closed 需恰一条"
                                " partition_granularity 先验，按仓库既定 V2 场景"
                                "口径注入（audit_v2_pkg._gran_entry 同模板，"
                                "min_gap_mm=2.0），注入后链式重算 board_sha256"
                                if gran_injected else "板自带粒度先验，未注入",
            "board_json": "out/v5-p5/boards/%s/board.json" % board_id}
        print("convert: nets=%d partitions=%d board_sha=%s…"
              % (len(board["nets"]), len(board["partitions"]), bsha[:12]))
    else:
        board = load_stage_board(board_id)

    bsha = board["provenance"]["board_sha256"]

    # ---- compile（下游阶段复用其内存产物；工件只在请求时落盘）----
    need_compile = any(s in stages for s in ("compile", "execute"))
    c_art = p_art = cf_art = pkg = None
    if need_compile:
        p_art = build_partition_artifact(board)
        c_art, _fp = compile_board(board)
        c_art2, _fp2 = compile_board(board)
        det = canonical.canonical_json(c_art) == canonical.canonical_json(c_art2)
        assert det, "compile_board 双跑字节不等"
        cf_art = build_conflicts(board)
        validate_conflicts_artifact(cf_art)
        pkg = build_pkg(board, p_art, cf_art)
        validate_pkg(pkg)
        if "compile" in stages:
            write_stage(os.path.join(odir, "compiled.json"),
                        {"partition_artifact": p_art, "compiled_rules": c_art,
                         "conflicts_artifact": cf_art, "pkg": pkg}, bsha)
            run["compile"] = {
                "coverage_pct": c_art["coverage"]["coverage_pct"],
                "partitions": len(p_art["partitions"]),
                "conflicts": len(cf_art.get("conflicts", [])),
                "j_items": len(build_j_items(cf_art)),
                "pkg_entries": len(pkg.get("entries", [])),
                "double_run_equal": det,
                "compiled_json": "out/v5-p5/boards/%s/compiled.json" % board_id}
            print("compile: coverage=%.1f%% conflicts=%d"
                  % (c_art["coverage"]["coverage_pct"],
                     len(cf_art.get("conflicts", []))))

    # ---- execute ----
    doc = None
    if "execute" in stages:
        cands = plan_candidates(board, c_art, arm=args.arm)
        if not cands:
            write_stage(os.path.join(odir, "execute.json"),
                        {"selection_verdict": "NO_CANDIDATES",
                         "candidate_source": None, "n_candidates": 0,
                         "execute": {"verdict": "FAILED",
                                     "per_net": [], "negotiation_log": [
                                         "plan_candidates 零候选"]},
                         "routes_doc": None}, bsha)
            run["execute"] = {"selection_verdict": "NO_CANDIDATES",
                              "candidate_source": None, "n_candidates": 0,
                              "exec_verdict": "FAILED", "routed": False,
                              "note": "规划器零候选，后续阶段跳过"}
            write_stage(os.path.join(odir, "run-result.json"),
                        {"run": run}, bsha)
            print("execute: 零候选，后续阶段跳过")
            return 0
        res = select_best(board, cands)
        # P5⑤-F3 轮换口径（0.3.0；P4 门 G1 口径演进披露：select_best 命中时
        # 首轮行为不变，selection UNSAT 时首轮仍取 plan_candidates[0]——
        # 只是 0.2.x 的「取 [0] 实跑一次」演进为「从 [0] 起按候选序轮换」）。
        # 首轮终局 FAILED（routes=None）时按候选序轮换下一候选重跑
        # execute_candidate，直至某候选 ROUTED 或试轮数耗尽
        # （总试轮数=min(K, len(cands))，含首轮；候选序即遍历序，确定性；
        # plan_candidates 自带等价计划去重，轮换不再滤重）。
        best = res.get("best")
        best_idx = None
        if best is not None:
            for i, c in enumerate(cands):
                if c == best:
                    best_idx = i
                    break
        # 遍历序：select_best 命中则 best 提前，其余按候选序；UNSAT 则纯候选序
        order = list(range(len(cands)))
        if best_idx is not None:
            order.remove(best_idx)
            order.insert(0, best_idx)
        seq = order[:min(args.rotate_budget, len(cands))]
        tried = []
        ex = None
        tried_idx = None
        for i in seq:
            tried_idx = i
            ex = execute_candidate(board, cands[i])
            tried.append({"index": i, "verdict": ex["verdict"],
                          "first_fail_net": _first_fail_net(ex["per_net"])})
            if ex["routes"] is not None:
                break  # 首个 ROUTED 即收口
        # 双跑字节等纪律保持：对最终实跑候选（成功候选或末轮候选）重跑核等
        ex2 = execute_candidate(board, cands[tried_idx])
        if ex["routes"] is not None:
            det = (canonical.canonical_json(ex["routes"])
                   == canonical.canonical_json(ex2["routes"]))
            assert det, "execute 双跑 routes 字节不等"
        else:
            det = (ex["verdict"] == ex2["verdict"])
        doc = ex["routes"]
        routed = doc is not None
        # candidate_source 口径演进（0.3.0）：成功时=plan_candidates[k]
        # （k=实际成功下标，如实）；全部试完仍 FAILED 时=null（无成功候选）。
        # 0.2.x 语义为 select_best.best / plan_candidates[0]（首轮选择依据）。
        source = ("plan_candidates[%d]" % tried_idx) if routed else None
        write_stage(os.path.join(odir, "execute.json"),
                    {"selection_verdict": res["verdict"],
                     "candidate_source": source,
                     "n_candidates": len(cands),
                     "rotate_budget": args.rotate_budget,
                     "tried_candidates": tried,
                     "execute": {"verdict": ex["verdict"],
                                 "per_net": ex["per_net"],
                                 "negotiation_log": ex["negotiation_log"]},
                     "routes_doc": doc}, bsha)
        run["execute"] = {
            "selection_verdict": res["verdict"], "candidate_source": source,
            "n_candidates": len(cands), "rotate_budget": args.rotate_budget,
            "tried_candidates": tried, "exec_verdict": ex["verdict"],
            "per_net_count": len(ex["per_net"]),
            "negotiation_log_entries": len(ex["negotiation_log"]),
            "routed": routed, "double_run_equal": det,
            "execute_json": "out/v5-p5/boards/%s/execute.json" % board_id}
        print("execute: selection=%s source=%s exec=%s trials=%d/%d"
              % (res["verdict"], source, ex["verdict"], len(tried), len(seq)))
        if doc is None and any(s in stages for s in ("postprocess", "check",
                                                     "export", "drc")):
            # P5② 修复路径（保持）：执行器未布通（routes=None）时与
            # NO_CANDIDATES 路径同款优雅收口——如实落 run-result 并跳过无输入
            # 的后续阶段，不再于 check 处 fail-closed 崩溃（崩溃会遗留悬空
            # drc 预登记事件，seq35 stm32-ds2480-emu 实例已另行更正登记）。
            # 0.3.0 起该路径=轮换预算内全部候选试完仍 FAILED。
            # 0.6.0（V5-R8）：postprocess 同款跳过（FAILED 板无 routes 不经
            # 后处理层=终态口径零变化，构造性）。
            run["skipped_stages"] = [s for s in ("postprocess", "check",
                                                 "export", "drc")
                                     if s in stages]
            run["skip_reason"] = ("execute FAILED（轮换 %d/%d 个候选均未布通，"
                                  "routes=None）；postprocess/check/export/drc "
                                  "无输入，跳过" % (len(tried), len(seq)))
            write_stage(os.path.join(odir, "run-result.json"),
                        {"run": run}, bsha)
            print("execute FAILED，后续阶段跳过：%s"
                  % ",".join(run["skipped_stages"]))
            print("run-result: out/v5-p5/boards/%s/run-result.json" % board_id)
            return 0

    # ---- postprocess（V5-R8 TB2 D-1：execute 后三原语确定性后处理+双留）----
    if "postprocess" in stages:
        if doc is None:
            # raw 面恒取 execute.json（D-1：routes-raw=execute.json 内嵌
            # routes_doc 原样拷贝；不经 final 优先的懒加载序——阶段子集重跑
            # 幂等：postprocess(postprocess(raw)) 二遍零改）。
            with open(os.path.join(odir, "execute.json"),
                      encoding="utf-8") as f:
                doc = json.load(f)["routes_doc"]
            if doc is None:
                raise SystemExit("postprocess 需先 execute 且 ROUTED")
        new_doc, pp_prov = postprocess_routes(board, doc)
        write_stage(os.path.join(odir, "routes-raw.json"),
                    {"routes_doc": doc}, bsha)
        write_stage(os.path.join(odir, "routes-final.json"),
                    {"routes_doc": new_doc, "postprocess": pp_prov}, bsha)
        doc = new_doc
        run["postprocess"] = {
            "module_version": pp_prov["module_version"],
            "changed": pp_prov["changed"],
            "actions_applied": {k: v["applied"]
                                for k, v in pp_prov["actions"].items()},
            "actions_reverted": {k: v["reverted"]
                                 for k, v in pp_prov["actions"].items()},
            "colocated_via_pairs_detected":
                pp_prov["colocated_via_pairs_detected"],
            "fixpoint": pp_prov["fixpoint"],
            "budget": pp_prov["budget"],
            "final_check": pp_prov["final_check"],
            "reverted_all": pp_prov["reverted_all"],
            "metrics": pp_prov["metrics"],
            "routes_raw": "out/v5-p5/boards/%s/routes-raw.json" % board_id,
            "routes_final": "out/v5-p5/boards/%s/routes-final.json" % board_id,
        }
        print("postprocess: %s changed=%s P1=%d P2a=%d P2b=%d P3=%d "
              "rounds=%d converged=%s budget_capped=%s final=%s"
              % (POSTPROCESS_VERSION, pp_prov["changed"],
                 pp_prov["actions"]["P1"]["applied"],
                 pp_prov["actions"]["P2a"]["applied"],
                 pp_prov["actions"]["P2b"]["applied"],
                 pp_prov["actions"]["P3"]["applied"],
                 pp_prov["fixpoint"]["rounds"],
                 pp_prov["fixpoint"]["converged"],
                 pp_prov["budget"]["capped"],
                 pp_prov["final_check"]["feasible"]))

    # ---- check ----
    cr = None
    if "check" in stages:
        if doc is None:
            doc = load_routes_doc(odir)
            if doc is None:
                raise SystemExit("check 需先 execute 且 ROUTED")
        cr = check_routes(board, doc)
        cr_out = dict(cr)
        cr_out["capacity_checks"] = [list(x) for x in cr["capacity_checks"]]
        cr_out["_routes_entries"] = [{"net_id": e.get("net_id")}
                                     for e in doc.get("routes", [])]
        write_stage(os.path.join(odir, "check.json"), {"check": cr_out}, bsha)
        cap_rows = [{"corridor_layer_id": clid, "occupancy_mm": occ,
                     "capacity_mm": cap, "fits": occ <= cap}
                    for clid, occ, cap in cr["capacity_checks"]]
        run["check"] = {
            "feasible": cr["feasible"],
            "violations_total": len(cr["violations"]),
            "attributed_violations": len(cr["attributed_violations"]),
            "violations_by_rule": count_by(cr["violations"], "rule"),
            "capacity_checks": cap_rows,
            "drc_version": cr["drc_version"],
            "route_check_version": cr["route_check_version"],
            "check_json": "out/v5-p5/boards/%s/check.json" % board_id}
        print("check: feasible=%s violations=%d capacity_checks=%d"
              % (cr["feasible"], len(cr["violations"]),
                 len(cr["capacity_checks"])))

    # ---- export ----
    if "export" in stages:
        if doc is None:
            doc = load_routes_doc(odir)
            if doc is None:
                raise SystemExit("export 需先 execute 且 ROUTED")
        data = kicad_pcb_bytes(board, doc)
        assert data == kicad_pcb_bytes(board, doc), "导出双跑字节不等"
        rel = os.path.join(odir, "%s.kicad_pcb" % board_id)
        with open(rel, "wb") as f:
            f.write(data)
        run["export"] = {"bytes": len(data), "sha256": sha256_bytes(data),
                         "double_run_equal": True,
                         "path": "out/v5-p5/boards/%s/%s.kicad_pcb"
                                 % (board_id, board_id)}
        print("export: %d bytes sha=%s…" % (len(data),
                                            sha256_bytes(data)[:12]))

    # ---- drc ----
    if "drc" in stages:
        # 台账先落事件再触内容：drc 读取导出件（派生数据），预登记事件紧贴
        # 实际执行前落（P5② 修复：原位于阶段顶部，exec FAILED 提前收口会留
        # 悬空 drc 事件——seq35 stm32-ds2480-emu 实例，已另行更正登记）。
        ledger.append(board_id, "drc",
                      "P5-UP3 drc：导出件过 kicad-cli 外权威（聚合协议：每轮 %d "
                      "跑、至多 %d 轮；计数提取，原始报告不落盘）"
                      % (DRC_RUNS, DRC_MAX_EXTRA_ROUNDS),
                      ledger.source_path_for(board_id),
                      prereg["sha256"],
                      extra=_with_extra({"cli": KICAD_CLI,
                                         "runs_per_round": DRC_RUNS,
                                         "max_extra_rounds": DRC_MAX_EXTRA_ROUNDS}),
                      operator=OPERATOR)
        if cr is None:
            cpath = os.path.join(odir, "check.json")
            if os.path.isfile(cpath):
                with open(cpath, encoding="utf-8") as f:
                    cr = json.load(f)["check"]
                cr["capacity_checks"] = [tuple(x) for x in
                                         cr.get("capacity_checks", [])]
            else:
                cr = {"violations": [], "feasible": None}
        if doc is not None and "_routes_entries" not in cr:
            cr["_routes_entries"] = [{"net_id": e.get("net_id")}
                                     for e in doc.get("routes", [])]
        drc_res = run_drc(board_id, board, cr)
        write_stage(os.path.join(odir, "drc-classified.json"),
                    {"drc": drc_res}, bsha)
        run["drc"] = {k: v for k, v in drc_res.items()
                      if k != "classified_rows_per_run"}
        run["drc"]["classified_rows_file"] = (
            "out/v5-p5/boards/%s/drc-classified.json" % board_id)
        print("drc: verdict=%s %d轮×%d跑 totals=%s union-max classified=%s"
              % (drc_res["verdict"], drc_res["n_rounds"], DRC_RUNS,
                 drc_res["rounds_totals"],
                 drc_res["aggregate_union_max"]["classified"]))

    # ---- run-result ----
    write_run_result(odir, run, bsha)
    print("run-result: out/v5-p5/boards/%s/run-result.json" % board_id)
    return 0


def write_run_result(odir, run, bsha):
    """run-result 落盘（0.2.0 起阶段子集重跑合并语义）：已有 run 记录时，
    此前阶段键原样保留（不覆盖历史证据），本次实跑阶段键以本次为准，
    stages_run 取并集并留披露注记。drc-only 稳定性验证依赖此语义，
    避免覆盖 P5② 全链 run 记录。"""
    path = os.path.join(odir, "run-result.json")
    prev = {}
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                prev = json.load(f).get("run") or {}
        except ValueError:
            prev = {}
    if prev:
        merged = dict(prev)
        merged.update(run)
        merged["stages_run"] = sorted(set(prev.get("stages_run") or [])
                                      | set(run.get("stages_run") or []))
        merged["result_merge_note"] = (
            "0.2.0 阶段子集重跑：本次实跑 %s，其余阶段键承前保留"
            % ",".join(run.get("stages_run") or []))
        run = merged
    write_stage(path, {"run": run}, bsha)


def _convert(data, board_id, uri):
    from v5.adapters.kicad_adapter import convert_bytes_with_report
    return convert_bytes_with_report(data, board_id, uri)


def _seed_granularity(board):
    """adapter 出板 principle_registry 为空，而 L1 fail-closed 要求恰一条
    partition_granularity 先验；按仓库既定 V2 场景口径注入
    （tools/audit_v2_pkg.py::_gran_entry 同模板同参，tests/test_pkg.py
    v2_board_with_gran 先例），注入后 board_sha256 按链式规则重算。
    幂等：已有粒度先验的板原样返回。返回 (board, injected_bool)。"""
    for entry in board.get("principle_registry", []):
        rule = entry.get("compiled_rule") if isinstance(entry, dict) else None
        if isinstance(rule, dict) and rule.get("kind") == "partition_granularity":
            return board, False
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from audit_v2_pkg import _gran_entry
    board["principle_registry"] = [_gran_entry()]
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    load_board(board)  # 注入后重过 schema+哈希链，fail-closed
    return board, True


if __name__ == "__main__":
    staging.recover(os.path.join(OUT, "_staging"), OUT)
    raise SystemExit(main())
