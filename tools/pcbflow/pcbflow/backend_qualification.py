"""TD7 外部执行 backend qualification（freerouting CLI 实配资格认证）。

SPEC-v3.0-PROPOSAL §TD7 的实配层：把 external_backend.py 的合同
（execution record / allowlist / 固定顺序输出验证链）落成可复现的
qualification 执行器。生成器纪律同全库：纯函数、零子进程、零写盘、
零网络、无 wall-clock、标准库 only；外部工具调用全部在编排侧
（Bash/scripts），本模块只做规则、解析与判定。

资格与质量分离（用户裁决口径，本模块逐字落实）：

- qualification verdict 只评 TD7 合同面：安全纪律（allowlist/禁网/
  staging-only/live 零写）、记录完备（不可变 execution record）、
  输出验证链（五 stage 按序 fail-closed 执行）、可复现性（同输入
  重跑确定性实测，如实记录 nondeterminism，不虚 claim byte-exact）；
- 布线质量（route success、DRC 双 severity、与参考 routed 态对比）
  = 独立记录的 quality facts，不进资格谓词；
- qualification pass 不等于布线质量好；SES 应用产物是 freerouting
  的布线（external authority，D17 边界），不是本库布线生成能力。

blocked 条件（TD7 原文语义）：崩溃、超时、输出截断、hash 不匹配、
非零退出、能力不符、权限越界 ⇒ blocked + staging 隔离。
"""

from __future__ import annotations

import math
import re

from . import external_backend, hashing, schemas, sexpr_min

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

TRACK = "td7-backend-qualification-r1"
MODULE_NAME = "pcbflow.backend_qualification"
Q_DATE = "2026-09-04"          # 人工会话声明日期（非机器 wall-clock）
SCHEMA_VERSION = "3.0"

BACKEND = "freerouting-cli-jar"
PROTOCOL = external_backend.CLI_PROTOCOL   # "cli-argv"
STARTED_BY = "s11-orchestrator"

# freerouting 引擎参数（ASM-8 同参：单线程锁死 + sequential 选择；
# -mt 1 是历史多线程 bug 教训的合同参数，不得改）
FREEROUTING_FIXED_TAIL = ("-mt", "1", "-is", "sequential")
FREEROUTING_MAX_PASSES = 3     # ASM-8 同参（-mp 3）

# ASM-8 历史记录的工具链期望（对账基线；漂移如实记录）
ASM8_EXPECTED_JAR_SHA256_PREFIX = "3cf18d60"
ASM8_EXPECTED_JAR_VERSION = "v2.3.0 (build 2026-08-07)"
ASM8_EXPECTED_JRE_VERSION = "25.0.4+7"

# 资源上限（记录于 execution record / run plan；编排侧执行时强制）
DEFAULT_FREEROUTING_TIMEOUT_S = 600
DEFAULT_KICAD_TIMEOUT_S = 300
DEFAULT_PCBNEW_TIMEOUT_S = 180
DEFAULT_MAX_THREADS = 1

# untrusted 输出 size 上限（schema/size validation stage）
MAX_SES_BYTES = 64 * 1024 * 1024
MAX_LOG_BYTES = 16 * 1024 * 1024
MAX_DRC_JSON_BYTES = 64 * 1024 * 1024

# SES 结构（ASM-8 实证：resolution um 10 ⇒ 1 单位=0.1um=1e-5mm）
SES_UNITS_PER_MM = 10000.0
# SES 确定性归一化：session/base_design 头行源自 -do 文件名（ASM-8
# determinism.json 逐条归因），比较确定性时替换为固定 token
SES_HEADER_KEYS = ("session", "base_design")

# via padstack 层跨度形态：Via[a-b]_S:D_um
_VIA_PADSTACK_RE = re.compile(r"^Via\[(\d+)-(\d+)\]_(\d+):(\d+)_um$")

# 选板规则常量（真实 profile=排除 smoke；unrouted=转换产物 0 铜几何）
REAL_PROFILE_EXCLUDE_PREFIX = "smoke-"
SELECTION_SMALL_RANGE = (10, 20)    # 小板：命名网数落在该区间取最小
SELECTION_LARGE_TARGET = 100        # 大板：最接近 100
SELECTION_MID_TARGET = 41           # 中板：最接近 41（37 真实 profile 中位）

# DRC delta 口径：按 (severity, type) 多重集计数差（ASM-8 批门"对基线
# 零新增"的计数口径；item 级身份不在本层）
_DRC_SEVERITIES = ("error", "warning", "exclusion")

# 资格谓词四轴（质量实况不在谓词内——独立 quality_facts 字段）
QUALIFICATION_AXES = (
    "security_discipline", "record_completeness",
    "verification_chain_executed", "reproducibility",
)

VERDICT_PASS = "pass"
VERDICT_FAIL = "fail"
VERDICT_BLOCKED = "blocked"

QUALIFICATION_NOTE = (
    "qualification verdict 只覆盖 TD7 合同面（安全纪律/记录完备/输出"
    "验证链/可复现性）；布线质量实况（route success、DRC 双 severity、"
    "与参考态对比）在 quality_facts 独立记录，好就是好、差就是差，"
    "qualification pass 不等于布线质量好。SES 应用产物是 freerouting "
    "的布线（external authority，D17 边界），不是本库布线生成能力。")

NETWORK_ENFORCEMENT_NOTE = (
    "network=deny：freerouting CLI 本地执行，编排侧不给网络（argv 仅"
    "本地文件、env 白名单最小化、无任何 URL/代理凭据注入）。")


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _has_parent_segment(element: str) -> bool:
    """元素按 / 与 \\ 切分后是否含 ".." 路径段（与 external_backend 同义）。"""
    return ".." in re.split(r"[\\/]+", element)


def _is_absolute_path(element: str) -> bool:
    """与 external_backend 同义：^[A-Za-z]:\\ 或 ^/（Windows 绝对路径
    一律用反斜杠形态——与 validate_policy 的 allowlist 判定语义严格
    一致，避免正斜杠形态绕过白名单检查）。"""
    return bool(re.match(r"^[A-Za-z]:\\", element)) or \
        element.startswith("/")


def _join_staging(staging_abs: str, name: str) -> str:
    """staging 根 + 文件名（保持原分隔符体系；不做任何解析/遍历）。"""
    if re.match(r"^[A-Za-z]:\\", staging_abs):
        return staging_abs.rstrip("\\") + "\\" + name
    return staging_abs.rstrip("/") + "/" + name


def _staging_parent(path: str) -> str:
    """绝对路径的父目录（staging 根推导；不做解析）。"""
    parts = re.split(r"[\\/]+", path)
    parent = parts[:-1]
    if re.match(r"^[A-Za-z]:$", parent[0]):
        return "\\".join(parent)
    return "/".join(parent)


def _sha256_hex_ok(value) -> bool:
    return (isinstance(value, str)
            and re.fullmatch(r"[0-9a-f]{64}", value) is not None)


def _basename(path: str) -> str:
    return re.split(r"[\\/]+", path)[-1]


def _finite_num(tok) -> float | None:
    try:
        v = float(tok)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ---------------------------------------------------------------------------
# 1) 选板（确定性规则；规则本身即合同）
# ---------------------------------------------------------------------------

def select_qualification_boards(entries: list) -> dict:
    """从真实 profile 账册确定性选取 qualification 板（小/中/大）。

    entries = [{profile_id, named_net_count, unrouted: bool,
                reference_available: bool, dataset_role: str}]（编排侧
                度量注入；dataset_role ∈ train|validation|holdout）。

    规则（写明即合同）：
    - 候选=真实 profile（profile_id 不以 smoke- 开头）∧ unrouted
      （转换产物铜几何为 0）∧ reference_available（datasets 参考
      routed 态在库）∧ dataset_role=train（资格认证只消费 train
      split——validation/holdout 保留给后续评估，数据纪律先于便利）；
    - small：named_net_count ∈ [10,20] 中最小（并列取字典序最小
      profile_id）——避开 ≤9 网近简并板；
    - mid：候选中 named_net_count 最接近 41（37 真实 profile 的
      中位量级）；
    - large：最接近 100（任务建议 bm1 100 网量级）；
    - 同板不得双选；任一档缺候选=该档 missing（不凑数）；
      train 候选枯竭时才允许 validation（holdout 恒禁）。
    """
    cands = [dict(e) for e in entries
             if isinstance(e, dict)
             and not str(e.get("profile_id", "")).startswith(
                 REAL_PROFILE_EXCLUDE_PREFIX)
             and e.get("unrouted") is True
             and e.get("reference_available") is True
             and e.get("dataset_role") in ("train", "validation")]
    for e in cands:
        n = e.get("named_net_count")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValueError(f"非法 named_net_count: {e.get('profile_id')!r}")
    train_pool = [e for e in cands if e.get("dataset_role") == "train"]
    cands = train_pool or cands

    def pick(target_key, taken):
        pool = [e for e in cands if e["profile_id"] not in taken]
        if not pool:
            return None, "no_candidate"
        if target_key == "small":
            pool = [e for e in pool
                    if SELECTION_SMALL_RANGE[0] <= e["named_net_count"]
                    <= SELECTION_SMALL_RANGE[1]]
            if not pool:
                return None, "no_candidate_in_range"
            best = min(pool, key=lambda e: (e["named_net_count"],
                                            e["profile_id"]))
        else:
            target = {"mid": SELECTION_MID_TARGET,
                      "large": SELECTION_LARGE_TARGET}[target_key]
            best = min(pool, key=lambda e: (abs(e["named_net_count"]
                                                - target),
                                            e["profile_id"]))
        return best, "selected"

    selection: dict = {"rule": {
        "candidates": "真实 profile（非 smoke）∧ unrouted 转换产物 ∧ "
                      "datasets 参考 routed 态在库 ∧ dataset_role=train"
                      "（validation 仅在 train 枯竭时兜底；holdout 恒禁）",
        "small": f"named_net_count ∈ [{SELECTION_SMALL_RANGE[0]},"
                 f"{SELECTION_SMALL_RANGE[1]}] 取最小，并列字典序",
        "mid": f"最接近 {SELECTION_MID_TARGET}（37 真实 profile 中位量级）",
        "large": f"最接近 {SELECTION_LARGE_TARGET}",
        "dedupe": "同板不得双选；缺档=missing 不凑数",
    }, "candidate_count": len(cands), "slots": {}}
    taken: set = set()
    for slot in ("small", "mid", "large"):
        best, status = pick(slot, taken)
        if best is None:
            selection["slots"][slot] = {"status": status}
        else:
            taken.add(best["profile_id"])
            selection["slots"][slot] = {
                "status": "selected",
                "profile_id": best["profile_id"],
                "named_net_count": best["named_net_count"]}
    selection["selected_profile_ids"] = sorted(taken)
    return selection


# ---------------------------------------------------------------------------
# 2) 工具链登记 + ASM-8 对账 + lock 提案（不执行）
# ---------------------------------------------------------------------------

def build_toolchain_registry(*, jar: dict, java: dict,
                             kicad_cli: dict) -> dict:
    """不可变工具链登记 + 与 ASM-8 记录对账（漂移如实记录）。

    jar/java/kicad_cli 由编排侧注入实测事实：
      {rel_path（仓库相对 POSIX）, abs_path_exists: bool,
       sha256: hex64|None, version: str|None}
    - sha256/version 缺失或 abs_path_exists=False ⇒ 该工具 not_available
      ⇒ 整体 registry verdict=blocked（TD7 能力不符=blocked 语义）；
    - jar sha256 与 ASM-8 前缀（3cf18d60）对账；version 与 ASM-8 记录
      对账；JRE 版本与 25.0.4+7 对账；kicad-cli 与锁内 10.0.5 对账。
    """
    items = {"freerouting_jar": jar, "java_runtime": java,
             "kicad_cli": kicad_cli}
    errors: list = []
    out_items: dict = {}
    for name, spec in items.items():
        if not isinstance(spec, dict):
            errors.append(f"{name} 登记缺失")
            continue
        rel_path = spec.get("rel_path")
        exists = spec.get("abs_path_exists") is True
        sha = spec.get("sha256")
        version = spec.get("version")
        item_errors: list = []
        if not isinstance(rel_path, str) or not rel_path:
            item_errors.append("rel_path 缺失")
        if not exists:
            item_errors.append("本机路径不存在（abs_path_exists=false）")
        if not _sha256_hex_ok(sha):
            item_errors.append("sha256 缺失或非 hex64"
                               "（无法锁定=blocked）")
        if not isinstance(version, str) or not version:
            item_errors.append("version 缺失")
        out_items[name] = {
            "rel_path": rel_path,
            "abs_path_exists": exists,
            "sha256": sha if _sha256_hex_ok(sha) else None,
            "version": version if isinstance(version, str) else None,
            "available": not item_errors,
            "errors": item_errors,
        }

    # ASM-8 对账（漂移非 blocked：如实记录；不可用才是 blocked）
    j = out_items.get("freerouting_jar", {})
    jv = out_items.get("java_runtime", {})
    kv = out_items.get("kicad_cli", {})
    reconcile = {
        "freerouting_jar": {
            "expected_sha256_prefix": ASM8_EXPECTED_JAR_SHA256_PREFIX,
            "observed_prefix": (j.get("sha256") or "")[:8] or None,
            "sha256_matches_asm8": bool(
                (j.get("sha256") or "").startswith(
                    ASM8_EXPECTED_JAR_SHA256_PREFIX)),
            "expected_version": ASM8_EXPECTED_JAR_VERSION,
            "observed_version": j.get("version"),
            "version_matches_asm8": j.get("version")
            == ASM8_EXPECTED_JAR_VERSION,
        },
        "java_runtime": {
            "expected_version": ASM8_EXPECTED_JRE_VERSION,
            "observed_version": jv.get("version"),
            "version_matches_asm8": jv.get("version")
            == ASM8_EXPECTED_JRE_VERSION,
            "note": "ASM-8 实配 JRE 25.0.4+7；PATH java=21.0.5 不用于"
                    "本链（版本漂移如实对账）",
        },
        "kicad_cli": {
            "expected_version": "10.0.5",
            "observed_version": kv.get("version"),
            "version_matches_lock": kv.get("version") == "10.0.5",
        },
    }
    errors.extend(f"{n}: {'; '.join(v['errors'])}"
                  for n, v in out_items.items() if v["errors"])
    return {
        "artifact_kind": "td7_toolchain_registry",
        "track": TRACK,
        "schema_version": SCHEMA_VERSION,
        "items": out_items,
        "asm8_reconciliation": reconcile,
        "registry_verdict": (VERDICT_BLOCKED if errors else VERDICT_PASS),
        "errors": errors,
    }


def build_toolchain_lock_proposal(registry: dict) -> dict:
    """锁更新提案内容（不执行——本包红线：toolchain_lock.json 零改动）。

    仅当 registry verdict=pass 时给出可锁条目；挂账为待治理步骤。
    """
    items = registry.get("items", {})
    jar = items.get("freerouting_jar", {})
    java = items.get("java_runtime", {})
    lockable = (registry.get("registry_verdict") == VERDICT_PASS)
    return {
        "artifact_kind": "td7_toolchain_lock_proposal",
        "track": TRACK,
        "status": "proposed_not_executed",
        "red_line_note": "本包不改 toolchain_lock.json；锁内语义 "
                         "freerouting/jdk locked only when actually "
                         "called（SPEC §2.3）——实配已发生后按证据提案",
        "lockable": lockable,
        "proposed_entries": {
            "freerouting": {
                "note": "locked_when_called（TD7 qualification "
                        f"{registry.get('registry_verdict')}）",
                "optional": True,
                "path": jar.get("rel_path"),
                "sha256": jar.get("sha256"),
                "version": jar.get("version"),
            },
            "jdk": {
                "note": "locked_when_called（TD7 qualification "
                        f"{registry.get('registry_verdict')}）",
                "optional": True,
                "path": java.get("rel_path"),
                "sha256": java.get("sha256"),
                "version": java.get("version"),
            },
        } if lockable else None,
    }


# ---------------------------------------------------------------------------
# 3) allowlist 声明 + argv 构造（瞬态绝对路径；归档只存 hash+basename）
# ---------------------------------------------------------------------------

def build_backend_declaration(*, java_abs: str, jar_abs: str,
                              staging_abs: str,
                              io_filenames: list) -> dict:
    """cli-argv 协议的 manifest 侧后端声明（供 validate_policy）。

    - executable_allowlist 只含 java 绝对路径（唯一可执行）；
    - path_allowlist = java + jar + staging 内声明的输入输出绝对路径
      字面量（validate_policy 对 argv 内一切绝对路径查 path_allowlist，
      可执行文件必须同时入两表）；
    - cwd/env 白名单以文档字段随附（env 最小化由编排侧执行）；
    - 产物归档只存 hash 与 basename，不落主机绝对路径。
    """
    if not java_abs or not jar_abs or not staging_abs:
        raise ValueError("java_abs/jar_abs/staging_abs 均必填")
    paths = [java_abs, jar_abs]
    for name in io_filenames or []:
        if not isinstance(name, str) or not name or _has_parent_segment(name):
            raise ValueError(f"io_filename 非法（含 .. 或空）: {name!r}")
        paths.append(_join_staging(staging_abs, name))
    return {
        "backend": BACKEND,
        "protocol": PROTOCOL,
        "executable_allowlist": [java_abs],
        "path_allowlist": sorted(set(paths)),
        "method_allowlist": [],
        "endpoint": None,
        "peer_identity": None,
        "cwd": staging_abs,
        "env_allowlist": ["PATH", "SYSTEMROOT", "TEMP", "TMP"],
        "network_policy": external_backend.NETWORK_POLICY_CLI,
    }


def build_freerouting_argv(*, java_abs: str, jar_abs: str, dsn_abs: str,
                           ses_abs: str,
                           max_passes: int = FREEROUTING_MAX_PASSES) -> list:
    """构造 freerouting argv（list[str] 逐参数；禁 shell 拼接）。

    - 参数面=ASM-8 同参：-de DSN -do SES -mt 1 -is sequential -mp N；
    - max_passes 必须 1..99；argv 元素含 ".." 段或非绝对路径入参
      （dsn/ses/java/jar）直接 ValueError（fail-closed）。
    """
    if not isinstance(max_passes, int) or isinstance(max_passes, bool) \
            or not 1 <= max_passes <= 99:
        raise ValueError(f"max_passes 非法: {max_passes!r}")
    argv = [java_abs, "-jar", jar_abs,
            "-de", dsn_abs, "-do", ses_abs,
            *FREEROUTING_FIXED_TAIL, "-mp", str(max_passes)]
    for i, element in enumerate(argv):
        if not isinstance(element, str):
            raise ValueError(f"argv[{i}] 非 str")
        if _has_parent_segment(element):
            raise ValueError(f"argv[{i}] 含 '..' 路径段: {element!r}")
    for required_abs in (java_abs, jar_abs, dsn_abs, ses_abs):
        if not _is_absolute_path(required_abs):
            raise ValueError(f"argv 入参必须绝对路径: {required_abs!r}")
    return argv


# ---------------------------------------------------------------------------
# 4) SES 解析（untrusted 输出）+ 确定性归一化
# ---------------------------------------------------------------------------

def parse_ses_network_out(ses_text: str) -> dict:
    """SES routes/network_out 段 → 逐网几何账（坐标 0.1um 原样）。

    SES 结构（ASM-8 实证）：network_out 内 net 块包裹
      (wire (path LAYER WIDTH x y x y ...) [(type protect)]) 与
      (via "Via[a-b]_S:D_um" x y [(type protect)])。
    解析失败 fail-closed（异常上抛，不猜）。
    """
    top = sexpr_min.parse(ses_text)
    sessions = [n for n in top if isinstance(n, list) and n
                and n[0] == "session"]
    if len(sessions) != 1:
        raise ValueError(f"expect exactly one session root, got "
                         f"{len(sessions)}")
    root = sessions[0]
    header = {"session": None, "base_design": None}
    # session 名=root 的第一个字符串子节点（root 自身即 session 节点）
    for child in root[1:]:
        if not isinstance(child, list):
            header["session"] = str(child)
            break
    node = sexpr_min.find_first(root, "base_design")
    if node is not None and len(node) >= 2:
        header["base_design"] = str(node[1])

    resolution = None
    res_node = sexpr_min.find_first(root, "resolution")
    if res_node is not None and len(res_node) >= 3:
        resolution = f"{res_node[1]} {res_node[2]}"

    nets: dict = {}
    network_out = sexpr_min.find_first(root, "network_out")
    if network_out is None:
        raise ValueError("SES 缺 network_out 段（fail-closed）")
    for net_node in network_out[1:]:
        if not (isinstance(net_node, list) and net_node
                and net_node[0] == "net"):
            continue
        net_name = str(net_node[1]) if len(net_node) >= 2 else ""
        acc = nets.setdefault(net_name, {
            "wires": 0, "vias": 0, "wire_length_units": 0.0,
            "layers": {}, "widths": [], "via_padstacks": {},
            "protected_items": 0})
        for child in net_node[2:]:
            if not (isinstance(child, list) and child):
                continue
            if child[0] == "wire":
                path = sexpr_min.find_first(child, "path")
                if path is None or len(path) < 4:
                    raise ValueError(f"net {net_name!r} wire path 残缺")
                acc["wires"] += 1
                acc["layers"][str(path[1])] = \
                    acc["layers"].get(str(path[1]), 0) + 1
                acc["widths"].append(float(path[2]))
                coords = [_finite_num(t) for t in path[3:]]
                if any(c is None for c in coords) or len(coords) % 2:
                    raise ValueError(f"net {net_name!r} wire path 坐标"
                                     "非数值/奇数个（fail-closed）")
                for i in range(0, len(coords) - 2, 2):
                    acc["wire_length_units"] += math.hypot(
                        coords[i + 2] - coords[i],
                        coords[i + 3] - coords[i + 1])
                if sexpr_min.find_first(child, "type") is not None:
                    acc["protected_items"] += 1
            elif child[0] == "via":
                if len(child) < 3:
                    raise ValueError(f"net {net_name!r} via 残缺")
                acc["vias"] += 1
                pad = str(child[1])
                acc["via_padstacks"][pad] = \
                    acc["via_padstacks"].get(pad, 0) + 1
                if sexpr_min.find_first(child, "type") is not None:
                    acc["protected_items"] += 1

    total_wires = sum(v["wires"] for v in nets.values())
    total_vias = sum(v["vias"] for v in nets.values())
    return {
        "header": header,
        "resolution": resolution,
        "net_count_in_network_out": len(nets),
        "nets": nets,
        "totals": {
            "wires": total_wires,
            "vias": total_vias,
            "wire_length_mm": round(
                sum(v["wire_length_units"] for v in nets.values())
                / SES_UNITS_PER_MM, 4),
        },
        "layer_histogram": {
            layer: sum(v["layers"].get(layer, 0) for v in nets.values())
            for layer in sorted({k for v in nets.values()
                                 for k in v["layers"]})},
        "width_min_units": min((w for v in nets.values()
                                for w in v["widths"]), default=None),
    }


def normalize_ses_for_determinism(ses_text: str) -> dict:
    """确定性归一化：session/base_design 头行（源自 -do 文件名）替换为
    固定 token；返回归一化文本 hash 与替换计数（ASM-8 determinism 口径）。

    兼容两种 token 形态：带引号 (session "name") 与 pcbnew DSN
    space_in_quoted_tokens 风格的裸 token (session name)。
    """
    replaced = 0
    _quoted = re.compile(
        r'^(\s*\((?:session|base_design)\s+)"[^"]*"')
    _bare = re.compile(
        r'^(\s*\((?:session|base_design)\s+)[^\s()]+')

    def _norm_line(line: str) -> str:
        nonlocal replaced
        m = _quoted.match(line)
        if m is not None:
            replaced += 1
            return m.group(1) + '"NORMALIZED"'
        m = _bare.match(line)
        if m is not None:
            replaced += 1
            return m.group(1) + '"NORMALIZED"'
        return line

    normalized = "\n".join(_norm_line(line)
                           for line in ses_text.splitlines())
    return {
        "normalized_sha256": hashing.sha256_text(normalized),
        "header_line_replacements": replaced,
        "header_keys": list(SES_HEADER_KEYS),
        "attribution_note": "session/base_design 值源自 -do 文件名"
                            "（ASM-8 determinism.json 归因）",
    }


def assess_determinism(runs: list) -> dict:
    """同输入 N 次重跑的确定性评估（如实；不虚 claim byte-exact）。

    runs = [{run_id, ses_sha256, normalized_sha256}]（同一 DSN 输入）。
    - byte-exact：raw sha 全同；
    - normalized：归一化 sha 全同（仅 -do 文件名衍生头行差异归因后）；
    - 二者皆不同 ⇒ deterministic=false（nondeterminism 实况记录）。
    """
    if not isinstance(runs, list) or len(runs) < 2:
        return {"assessed": False,
                "reason": "重跑次数 <2，无法评估确定性（fail-closed）",
                "deterministic": None}
    raw = {r.get("ses_sha256") for r in runs}
    norm = {r.get("normalized_sha256") for r in runs}
    byte_exact = len(raw) == 1
    normalized_identical = len(norm) == 1
    deterministic = normalized_identical
    return {
        "assessed": True,
        "run_count": len(runs),
        "distinct_raw_ses_sha256": len(raw),
        "distinct_normalized_ses_sha256": len(norm),
        "byte_exact": byte_exact,
        "normalized_identical": normalized_identical,
        "deterministic": deterministic,
        "claim": ("same-input reruns byte-exact" if byte_exact
                  else "same-input reruns identical after -do-filename "
                       "header normalization (ASM-8 attribution)"
                  if normalized_identical
                  else "NONDETERMINISTIC across same-input reruns "
                       "(observed, recorded honestly)"),
    }


# ---------------------------------------------------------------------------
# 5) L1 几何 + 层纯净（SES 侧机器断言）
# ---------------------------------------------------------------------------

def ses_l1_geometry_check(ses_geom: dict, profile: dict) -> dict:
    """SES 输出的 L1 几何+层纯净机器断言（TD7 链 stage 2）。

    - layer_purity：信号线层 ⊆ profile 声明的 signal 层；plane/power
      层不得出现信号线段（ASM-8 层纯净硬门同源）；
    - via_span：Via[a-b] 跨度 ⊆ [0, 层数-1]（越界=越层违例）；
    - width_sanity：全部线宽 > 0 且有限；
    - coordinate/structure：解析已在 parse_ses_network_out fail-closed。
    """
    layers = (profile or {}).get("layers") or []
    signal = sorted(l["name"] for l in layers if l.get("role") == "signal")
    forbidden = sorted(l["name"] for l in layers
                       if l.get("role") in ("plane", "power"))
    layer_count = len(layers)
    nets = ses_geom.get("nets", {})
    checks: list = []

    used = set(ses_geom.get("layer_histogram") or {})
    bad_layers = sorted(used - set(signal))
    checks.append({
        "id": "ses_layer_purity",
        "pass": not bad_layers,
        "evidence": f"信号线层集={sorted(used)}；允许={signal}；"
                    f"违例层={bad_layers}"
                    + (f"（profile 声明 plane/power={forbidden} 不得"
                       "承载信号段）" if forbidden else ""),
    })

    span_bad, width_bad = [], []
    for net_name, acc in sorted(nets.items()):
        for w in acc["widths"]:
            if not (math.isfinite(w) and w > 0):
                width_bad.append(net_name)
                break
        for pad in acc["via_padstacks"]:
            m = _VIA_PADSTACK_RE.match(pad)
            if m is None:
                span_bad.append(f"{net_name}:{pad}!(padstack形态)")
                continue
            lo, hi = int(m.group(1)), int(m.group(2))
            if layer_count and (lo < 0 or hi >= layer_count or hi < lo):
                span_bad.append(f"{net_name}:{pad}")
    checks.append({
        "id": "ses_via_span_within_stackup",
        "pass": not span_bad,
        "evidence": f"via padstack 层跨度越界/形态违例={span_bad[:8]}"
                    f"（共 {len(span_bad)}；stackup 层数={layer_count}）",
    })
    checks.append({
        "id": "ses_width_sanity",
        "pass": not width_bad,
        "evidence": f"非正/非有限线宽网={width_bad[:8]}"
                    f"（共 {len(width_bad)}）",
    })
    checks.append({
        "id": "ses_network_out_nonempty",
        "pass": bool(nets),
        "evidence": f"network_out 网数={len(nets)}"
                    f"（空输出=无布线证据，fail-closed）",
    })
    return {
        "checks": checks,
        "all_pass": all(c["pass"] for c in checks),
        "layer_purity_pass": checks[0]["pass"],
    }


# ---------------------------------------------------------------------------
# 6) 板级度量（长度/层/过孔）与参考态对比
# ---------------------------------------------------------------------------

def _net_token_name(net_node, id_map: dict):
    """(net ...) 子节点 → 网名（兼容 KiCad5 (net <int> "<name>") 物件
    引用 (net <int>) 与 KiCad9+ 名称直引 (net "<name>")）。"""
    if not (isinstance(net_node, list) and len(net_node) >= 2):
        return None
    tok = net_node[1]
    if isinstance(tok, str) and re.fullmatch(r"-?\d+", tok):
        return id_map.get(int(tok))
    return str(tok)


def board_route_metrics(board_text: str) -> dict:
    """板文本 → 布线几何度量（段/孔/层直方图/总线长 mm/逐网账）。

    兼容 KiCad5（net 以整数 id 引用，板级 (net <id> "<name>") 声明）
    与 KiCad9+（物件内 (net "<name>") 名称直引）两种形态——本函数
    只做文本结构级统计，不做几何求值；解析失败 fail-closed 上抛。
    """
    top = sexpr_min.parse(board_text)
    roots = [n for n in top if isinstance(n, list) and n
             and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise ValueError("expect exactly one kicad_pcb root")
    root = roots[0]

    id_map: dict = {}
    for n in root[1:]:
        if isinstance(n, list) and n and n[0] == "net" and len(n) >= 3 \
                and re.fullmatch(r"-?\d+", str(n[1])):
            id_map[int(n[1])] = str(n[2])

    def _tok_num(node, key):
        t = sexpr_min.find_first(node, key)
        if t is None or len(t) < 2:
            return None
        return _finite_num(t[1])

    nets_seen: dict = {}
    pads_per_net: dict = {}
    layer_hist: dict = {}
    per_net_count: dict = {}
    per_net_len: dict = {}
    total_len = 0.0
    widths: list = []
    via_sizes: list = []
    via_drills: list = []
    seg_count = arc_count = via_count = zone_count = 0

    for m in sexpr_min.find_all(root, "footprint"):
        for p in sexpr_min.find_all(m, "pad"):
            name = _net_token_name(sexpr_min.find_first(p, "net"), id_map)
            if name is not None:
                pads_per_net[name] = pads_per_net.get(name, 0) + 1
                nets_seen.setdefault(name, 0)

    for seg in sexpr_min.find_all(root, "segment"):
        seg_count += 1
        name = _net_token_name(sexpr_min.find_first(seg, "net"), id_map)
        if name is not None:
            nets_seen[name] = nets_seen.get(name, 0) + 1
            per_net_count[name] = per_net_count.get(name, 0) + 1
        layer = sexpr_min.find_first(seg, "layer")
        if layer is not None and len(layer) >= 2:
            layer_hist[str(layer[1])] = layer_hist.get(str(layer[1]), 0) + 1
        w = _tok_num(seg, "width")
        if w is not None:
            widths.append(w)
        st = sexpr_min.find_first(seg, "start")
        en = sexpr_min.find_first(seg, "end")
        if st is not None and en is not None and len(st) >= 3 \
                and len(en) >= 3:
            x1, y1 = _finite_num(st[1]), _finite_num(st[2])
            x2, y2 = _finite_num(en[1]), _finite_num(en[2])
            if None not in (x1, y1, x2, y2):
                length = math.hypot(x2 - x1, y2 - y1)
                total_len += length
                if name is not None:
                    per_net_len[name] = per_net_len.get(name, 0.0) + length
    for arc in sexpr_min.find_all(root, "arc"):
        arc_count += 1
        name = _net_token_name(sexpr_min.find_first(arc, "net"), id_map)
        if name is not None:
            nets_seen[name] = nets_seen.get(name, 0) + 1
        w = _tok_num(arc, "width")
        if w is not None:
            widths.append(w)
    for via in sexpr_min.find_all(root, "via"):
        via_count += 1
        name = _net_token_name(sexpr_min.find_first(via, "net"), id_map)
        if name is not None:
            nets_seen[name] = nets_seen.get(name, 0) + 1
        sz = _tok_num(via, "size")
        dr = _tok_num(via, "drill")
        if sz is not None:
            via_sizes.append(sz)
        if dr is not None:
            via_drills.append(dr)
        for layer in sexpr_min.find_all(via, "layers"):
            pass  # via 层跨度不进信号层直方图（避免与 segment 双计）
    for zone in sexpr_min.find_all(root, "zone"):
        zone_count += 1
        name = _net_token_name(sexpr_min.find_first(zone, "net"), id_map)
        if name is not None:
            nets_seen[name] = nets_seen.get(name, 0) + 1

    named = {n for n in nets_seen if n not in ("", None)}
    return {
        "net_names_seen": len(nets_seen),
        "named_net_count": len(named),
        "geometry_counts": {"segments": seg_count, "arcs": arc_count,
                            "vias": via_count, "zones": zone_count},
        "multi_pad_named_nets": sum(
            1 for n in named if pads_per_net.get(n, 0) >= 2),
        "actual_min": {
            "track_width_mm": min(widths) if widths else None,
            "via_size_mm": min(via_sizes) if via_sizes else None,
            "via_drill_mm": min(via_drills) if via_drills else None,
        },
        "layer_histogram": dict(sorted(layer_hist.items())),
        "total_segment_length_mm": round(total_len, 4),
        "per_net_length_mm_top": dict(sorted(
            ((k, round(v, 4)) for k, v in per_net_len.items()),
            key=lambda kv: -kv[1])[:10]),
        "per_net_item_count_top": dict(sorted(
            per_net_count.items(), key=lambda kv: -kv[1])[:10]),
    }


def compare_to_reference(freerouting_metrics: dict,
                         reference_metrics: dict) -> dict:
    """freerouting 产物板 vs 参考 routed 态对比（上下文，非 authority）。"""
    def _delta(key):
        a = freerouting_metrics.get(key)
        b = reference_metrics.get(key)
        return None if a is None or b is None else round(a - b, 4)

    def _geom(key):
        a = (freerouting_metrics.get("geometry_counts") or {}).get(key)
        b = (reference_metrics.get("geometry_counts") or {}).get(key)
        return None if a is None or b is None else a - b

    return {
        "authority_note": "参考 routed 态只是对比上下文（上游实况），"
                          "不是布线质量 authority；差异如实记录",
        "named_net_count": {
            "freerouting": freerouting_metrics.get("named_net_count"),
            "reference": reference_metrics.get("named_net_count"),
            "delta": _delta("named_net_count")},
        "segments": {"freerouting": (freerouting_metrics.get(
            "geometry_counts") or {}).get("segments"),
            "reference": (reference_metrics.get("geometry_counts")
                          or {}).get("segments"),
            "delta": _geom("segments")},
        "vias": {"freerouting": (freerouting_metrics.get(
            "geometry_counts") or {}).get("vias"),
            "reference": (reference_metrics.get("geometry_counts")
                          or {}).get("vias"),
            "delta": _geom("vias")},
        "zones": {"freerouting": (freerouting_metrics.get(
            "geometry_counts") or {}).get("zones"),
            "reference": (reference_metrics.get("geometry_counts")
                          or {}).get("zones"),
            "delta": _geom("zones")},
        "total_segment_length_mm": {
            "freerouting": freerouting_metrics.get(
                "total_segment_length_mm"),
            "reference": reference_metrics.get("total_segment_length_mm"),
            "delta": _delta("total_segment_length_mm")},
        "layer_use_freerouting": freerouting_metrics.get("layer_histogram"),
        "layer_use_reference": reference_metrics.get("layer_histogram"),
        "min_track_width_mm": {
            "freerouting": (freerouting_metrics.get("actual_min")
                            or {}).get("track_width_mm"),
            "reference": (reference_metrics.get("actual_min")
                          or {}).get("track_width_mm")},
    }


# ---------------------------------------------------------------------------
# 7) DRC delta（双 severity；(severity,type) 计数多重集口径）
# ---------------------------------------------------------------------------

def _drc_type_counts(drc_json: dict) -> dict:
    counts: dict = {}
    for v in (drc_json or {}).get("violations") or []:
        if not isinstance(v, dict):
            continue
        key = (str(v.get("severity")), str(v.get("type")))
        counts[key] = counts.get(key, 0) + 1
    return counts


def drc_dual_severity_delta(*, baseline_error: dict, actual_error: dict,
                            baseline_all: dict, actual_all: dict) -> dict:
    """freerouting 应用板 vs 未布线 staging 基线的双 severity 计数 delta。

    口径：(severity, type) 计数多重集（ASM-8 批门"对基线零新增"的
    计数口径）；unconnected_items 单列（连通性 authority）。
    new>0 ⇒ 该 severity 档有新增；removed 为收益侧事实记录。
    """
    def _delta(base, act):
        b, a = _drc_type_counts(base), _drc_type_counts(act)
        keys = sorted(set(b) | set(a))
        new = {f"{s}:{t}": a.get(k, 0) - b.get(k, 0) for k in keys
               for s, t in [k] if a.get(k, 0) > b.get(k, 0)}
        removed = {f"{s}:{t}": b.get(k, 0) - a.get(k, 0) for k in keys
                   for s, t in [k] if b.get(k, 0) > a.get(k, 0)}
        return new, removed

    err_new, err_removed = _delta(baseline_error, actual_error)
    all_new, all_removed = _delta(baseline_all, actual_all)
    unconn_base = len((baseline_all or {}).get("unconnected_items") or [])
    unconn_act = len((actual_all or {}).get("unconnected_items") or [])

    def _sev(d, s):
        return {k: v for k, v in d.items() if k.startswith(s + ":")}

    return {
        "counting_semantics": "(severity,type) 计数多重集；基线=未布线"
                              " staging 板（本包转换产物，铜几何 0）",
        "severity_error": {
            "new_violation_types": err_new,
            "new_count": sum(err_new.values()),
            "removed_count": sum(err_removed.values()),
        },
        "severity_all": {
            "new_violation_types": {**_sev(all_new, "error"),
                                    **_sev(all_new, "warning"),
                                    **_sev(all_new, "exclusion")},
            "new_count": sum(all_new.values()),
            "new_error_count": sum(_sev(all_new, "error").values()),
            "new_warning_count": sum(_sev(all_new, "warning").values()),
            "removed_count": sum(all_removed.values()),
            "removed_error_count": sum(_sev(all_removed, "error").values()),
            "removed_warning_count": sum(
                _sev(all_removed, "warning").values()),
        },
        "unconnected_items": {
            "baseline_unrouted": unconn_base,
            "after_freerouting": unconn_act,
            "authority": "kicad_cli_drc_unconnected_items",
        },
    }


# ---------------------------------------------------------------------------
# 8) run record 装配（execution record + policy + 五 stage + 质量）
# ---------------------------------------------------------------------------

def build_stage_statuses(*, ses_observed: dict, l1_result: dict,
                         drc_result: dict | None,
                         finalization: dict | None) -> list:
    """按 STAGE_ORDER 装配五 stage 观察状态（fail-closed）。

    - schema_size_validation：SES 存在+未截断+hash 绑定+可解析；
    - l1_layer_purity：ses_l1_geometry_check all_pass；
    - drc_batch_severity_error：双 error-run 已执行且 new_count==0
      （ASM-8 批门口径：对基线零新增 error）；
    - drc_final_severity_all：severity-all 终检已执行且 new_count==0
      （未布线→布线是合法状态迁移：removed 计为收益，新增才违例）；
    - rollback_ledger_graph：rollback/登记证据齐（失败态=staging 已
      回滚隔离；通过态=产物入 ledger/graph）。
    drc_result/finalization 为 None ⇒ 对应 stage not_executed。
    """
    stages: list = []

    size_ok = (ses_observed.get("present") is True
               and ses_observed.get("truncated") is not True
               and ses_observed.get("hash_matches") is not False
               and ses_observed.get("parsed") is True)
    stages.append({
        "stage": "schema_size_validation",
        "status": "pass" if size_ok else "fail",
        "detail": f"size_bytes={ses_observed.get('size_bytes')} "
                  f"bound={MAX_SES_BYTES}; hash_matches="
                  f"{ses_observed.get('hash_matches')}; parsed="
                  f"{ses_observed.get('parsed')}; truncated="
                  f"{ses_observed.get('truncated')}",
    })
    stages.append({
        "stage": "l1_layer_purity",
        "status": "pass" if l1_result.get("all_pass") else "fail",
        "detail": "; ".join(
            f"{c['id']}={'pass' if c['pass'] else 'fail'}"
            for c in l1_result.get("checks", [])),
    })
    if drc_result is None:
        stages.append({"stage": "drc_batch_severity_error",
                       "status": "not_executed",
                       "detail": "DRC 未执行（fail-closed）"})
        stages.append({"stage": "drc_final_severity_all",
                       "status": "not_executed",
                       "detail": "DRC 未执行（fail-closed）"})
    else:
        executed = drc_result.get("executed") is True
        new_err = drc_result["severity_error"]["new_count"]
        stages.append({
            "stage": "drc_batch_severity_error",
            "status": ("pass" if executed and new_err == 0 else "fail")
            if executed else "not_executed",
            "detail": f"executed={executed}; new_severity_error="
                      f"{new_err}（ASM-8 批门口径：对未布线基线零新增"
                      " error）",
        })
        new_all = drc_result["severity_all"]["new_count"]
        sev_all = drc_result["severity_all"]
        stages.append({
            "stage": "drc_final_severity_all",
            "status": ("pass" if executed and new_all == 0 else "fail")
            if executed else "not_executed",
            "detail": f"executed={executed}; new_all_severity="
                      f"{new_all}（new_error="
                      f"{sev_all['new_error_count']}"
                      f"/new_warning="
                      f"{sev_all['new_warning_count']}"
                      f"；removed={sev_all['removed_count']}"
                      " 计为收益侧事实）",
        })
    if finalization is None:
        stages.append({"stage": "rollback_ledger_graph",
                       "status": "not_executed",
                       "detail": "rollback/ledger/graph 证据缺失"})
    else:
        ok = finalization.get("evidence_complete") is True
        stages.append({
            "stage": "rollback_ledger_graph",
            "status": "pass" if ok else "fail",
            "detail": finalization.get("detail", ""),
        })
    return stages


def build_run_record(*, execution_id: str, project_id: str, profile_id: str,
                     source_snapshot_sha256: str,
                     staging_path_sha256: str,
                     tool_version: str,
                     toolchain_lock_sha256: str,
                     request_sha256: str,
                     response_sha256: str,
                     argv: list,
                     timeout_s: int,
                     exit_status,
                     ses_observed: dict,
                     l1_result: dict,
                     drc_result: dict | None,
                     finalization: dict | None,
                     quality: dict) -> dict:
    """装配单板 qualification run record（TD7 合同执行的最小闭环）。

    - execution record 经 external_backend.build_execution_record 构造
      （schema 校验+argv canonical hash+默认隔离字段）；
    - policy 声明经 external_backend.validate_policy 全量校验
      （违例=record.policy_errors 非空 ⇒ 资格 fail，不静默）；
    - pipeline 结论经 external_backend.assess_output（固定顺序+退出码
      fail-closed）。
    """
    record = external_backend.build_execution_record(
        execution_id=execution_id,
        project_id=project_id,
        profile_id=profile_id,
        source_snapshot_sha256=source_snapshot_sha256,
        staging_path_sha256=staging_path_sha256,
        backend=BACKEND,
        protocol=PROTOCOL,
        tool_version=tool_version,
        toolchain_lock_sha256=toolchain_lock_sha256,
        request_sha256=request_sha256,
        response_sha256=response_sha256,
        argv_or_rpc=list(argv),
        started_by=STARTED_BY,
        timeout_s=timeout_s,
        exit_status=exit_status,
        resource_limits={"max_threads": DEFAULT_MAX_THREADS},
    )
    declaration = external_backend_validate_target(argv=argv)
    policy_errors = external_backend.validate_policy(
        {**record, "argv_or_rpc": list(argv)}, declaration)
    stages = build_stage_statuses(
        ses_observed=ses_observed, l1_result=l1_result,
        drc_result=drc_result, finalization=finalization)
    assessment = external_backend.assess_output(
        {**record, "exit_status": exit_status}, stages)
    return {
        "artifact_kind": "td7_qualification_run",
        "track": TRACK,
        "schema_version": SCHEMA_VERSION,
        "run_date": Q_DATE,
        "execution_record": record,
        "argv_baseline_names": {
            "argv": [_basename(a) if _is_absolute_path(a) else a
                     for a in argv],
            "note": "归档只存 basename/旗标（核产物禁主机路径）；完整"
                    "绝对 argv 在编排侧会话内与 allowlist 逐字面量比对",
        },
        "policy_validation": {
            "declaration_shape": {
                "executable_allowlist_count":
                    len(declaration["executable_allowlist"]),
                "path_allowlist_count":
                    len(declaration["path_allowlist"]),
                "cwd": "<staging>",
                "env_allowlist": declaration["env_allowlist"],
                "network_policy": declaration["network_policy"],
            },
            "errors": policy_errors,
            "pass": not policy_errors,
        },
        "stages": stages,
        "pipeline": assessment,
        "quality_facts": quality,
    }


def external_backend_validate_target(*, argv: list) -> dict:
    """由 argv 推导 staging 根并构造声明（java/jar=argv[0]/argv[2]，
    staging=dsn 父目录；io 白名单=argv 内全部绝对路径 basename 去重）。"""
    dsn = argv[4]
    staging_abs = _staging_parent(dsn)
    io_names = sorted({_basename(p) for p in argv
                       if _is_absolute_path(p)})
    return build_backend_declaration(
        java_abs=argv[0], jar_abs=argv[2], staging_abs=staging_abs,
        io_filenames=io_names)


# ---------------------------------------------------------------------------
# 9) 资格报告（四轴谓词 + 质量实况独立记录）
# ---------------------------------------------------------------------------

def build_qualification_report(*, toolchain_registry: dict,
                               selection: dict,
                               run_records: list,
                               determinism_runs: list) -> dict:
    """TD7 qualification 总裁决（pass/fail/blocked + 逐项证据）。

    谓词四轴（QUALIFICATION_AXES）：
    - security_discipline：每次执行 validate_policy=[] ∧ network=deny ∧
      write_scope=staging_only ∧ live_board_touched=false；
    - record_completeness：每条 execution record schema 复验通过 ∧
      request/response/argv hash 齐 ∧ 无 fallback 成功形态；
    - verification_chain_executed：每 run 五 stage 与 STAGE_ORDER 全同
      且无 not_executed（执行面完整；stage 内容性 fail 如实进入
      pipeline_status，不掩盖）；
    - reproducibility：每板同输入重跑 ≥2 次且确定性结论与实测一致
      （用户裁决口径：如实测、记实况、不虚 claim byte-exact——引擎
      nondeterminism 是记录的实况事实，不是测量纪律失败；其对 TL-4
      A/B 比较的噪声后果在 engine_determinism 与 notes 显式登记）。
    verdict：四轴全 pass ∧ registry 可用 ⇒ pass；registry blocked ⇒
    blocked；否则 fail。质量实况在 quality_facts，不进谓词。
    """
    runs = run_records or []
    axis_results: dict = {}

    sec_fails, rec_fails, chain_fails = [], [], []
    for r in runs:
        rid = r.get("execution_record", {}).get("execution_id")
        pv = r.get("policy_validation") or {}
        er = r.get("execution_record") or {}
        if not pv.get("pass"):
            sec_fails.append(f"{rid}: policy_errors={pv.get('errors')}")
        if er.get("network_policy") != "deny":
            sec_fails.append(f"{rid}: network_policy="
                             f"{er.get('network_policy')!r}")
        if er.get("write_scope") != "staging_only":
            sec_fails.append(f"{rid}: write_scope={er.get('write_scope')!r}")
        if er.get("live_board_touched") is not False:
            sec_fails.append(f"{rid}: live_board_touched 非false")
        if er.get("fallback_reason") is not None:
            rec_fails.append(f"{rid}: fallback_reason="
                             f"{er.get('fallback_reason')!r}")
        for key in ("request_sha256", "response_sha256",
                    "argv_or_rpc_hash"):
            if not _sha256_hex_ok(er.get(key)):
                rec_fails.append(f"{rid}: {key} 缺失/非hex64")
        if schemas.validate(external_backend.RECORD_SCHEMA, er):
            rec_fails.append(f"{rid}: schema 复验违例")
        observed = [s.get("stage") for s in (r.get("stages") or [])]
        if tuple(observed) != external_backend.STAGE_ORDER:
            chain_fails.append(f"{rid}: stage 序列={observed}")
        if any(s.get("status") == "not_executed"
               for s in (r.get("stages") or [])):
            chain_fails.append(f"{rid}: 存在 not_executed stage")
    axis_results["security_discipline"] = {
        "pass": not sec_fails, "evidence": sec_fails or [
            f"×{len(runs)} run validate_policy 全通过（allowlist 可执行/"
            "路径字面量、禁 shell 拼接、禁 ..、禁非白名单绝对路径）且 "
            "network=deny/staging-only/live 零写见证成立"]}
    axis_results["record_completeness"] = {
        "pass": not rec_fails, "evidence": rec_fails or [
            f"×{len(runs)} execution record schema 复验通过，request/"
            "response/argv hash 齐，无 fallback 形态"]}
    axis_results["verification_chain_executed"] = {
        "pass": not chain_fails, "evidence": chain_fails or [
            f"×{len(runs)} run 五 stage 序列=STAGE_ORDER 全同、零 "
            "not_executed；内容性 fail（若有）如实留在各 run 的 "
            "pipeline_status（blocked+quarantine）"]}
    det_eval = assess_determinism(determinism_runs)
    axis_results["reproducibility"] = {
        "pass": det_eval.get("assessed") is True,
        "evidence": det_eval.get("claim") or det_eval.get("reason"),
        "measurement_discipline_note":
            "本轴=测量纪律（≥2 次同输入重跑+结论与实测一致+无 byte-exact "
            "虚 claim）；引擎 deterministic 实况见顶层 engine_"
            "determinism 字段——nondeterministic 是如实记录的事实，"
            "其 TL-4 后果（A/B 噪声）在 notes 登记",
        "assessment": det_eval}

    registry_ok = toolchain_registry.get("registry_verdict") == VERDICT_PASS
    no_runs = not runs
    axes_pass = all(a["pass"] for a in axis_results.values())
    if not registry_ok:
        verdict = VERDICT_BLOCKED
        reason = f"工具链登记不可用: {toolchain_registry.get('errors')}"
    elif no_runs:
        verdict = VERDICT_BLOCKED
        reason = "零有效 run（资格样本缺失=blocked，不虚评）"
    elif axes_pass:
        verdict = VERDICT_PASS
        reason = "四轴谓词全 pass"
    else:
        verdict = VERDICT_FAIL
        reason = "谓词失败：" + "; ".join(
            f"{k}={'pass' if v['pass'] else 'fail'}"
            for k, v in axis_results.items() if not v["pass"])
    quality_facts = [
        {"execution_id": r.get("execution_record", {}).get("execution_id"),
         "profile_id": r.get("execution_record", {}).get("profile_id"),
         "pipeline_status": (r.get("pipeline") or {}).get("pipeline_status"),
         "quality": r.get("quality_facts")}
        for r in runs]
    return {
        "artifact_kind": "td7_qualification_report",
        "track": TRACK,
        "schema_version": SCHEMA_VERSION,
        "report_date": Q_DATE,
        "backend": BACKEND,
        "protocol": PROTOCOL,
        "board_selection": selection,
        "toolchain_registry_verdict":
            toolchain_registry.get("registry_verdict"),
        "run_count": len(runs),
        "axis_results": axis_results,
        "engine_determinism": det_eval,
        "verdict": verdict,
        "verdict_reason": reason,
        "quality_facts": quality_facts,
        "notes": [
            QUALIFICATION_NOTE,
            NETWORK_ENFORCEMENT_NOTE,
            "freerouting 自报 unrouted/score 不具 authority（engine_self"
            "_report_included=false）；连通性与 DRC 一律 kicad-cli 复核。",
            ("engine_determinism.deterministic="
             f"{det_eval.get('deterministic')!r}：若为 False，同输入重跑"
             "产出不同 SES（实况记录）；TL-4 executor 接入时 config 敏感"
             "A/B 比较须引入 N 次重跑统计口径，单次对比不具判别力。"
             if det_eval.get("assessed") else
             "确定性未评估（重跑 <2 次）：fail-closed 实况。"),
        ],
    }


def qualification_gate_predicates(report: dict) -> list:
    """把资格报告四轴+registry+样本面转成 evaluate_gate 谓词列表。"""
    axes = report.get("axis_results", {})
    det = (axes.get("reproducibility", {})
           .get("assessment", {}))
    selection = report.get("board_selection", {})
    run_count = report.get("run_count")
    return [
        {"id": "td7_toolchain_registry_available",
         "value": report.get("toolchain_registry_verdict") == VERDICT_PASS,
         "evidence": f"registry_verdict="
                     f"{report.get('toolchain_registry_verdict')}（jar/"
                     "JRE/kicad-cli 实测定格+ASM-8 对账）"},
        {"id": "td7_qualification_sample_present",
         "value": (run_count or 0) >= 1,
         "evidence": f"实配 run 数={run_count}"
                     f"（选板={selection.get('selected_profile_ids')}）"},
        {"id": "td7_security_discipline",
         "value": (axes.get("security_discipline", {}).get("pass")
                   is True),
         "evidence": str(axes.get("security_discipline", {})
                         .get("evidence"))},
        {"id": "td7_record_completeness",
         "value": (axes.get("record_completeness", {}).get("pass")
                   is True),
         "evidence": str(axes.get("record_completeness", {})
                         .get("evidence"))},
        {"id": "td7_verification_chain_executed",
         "value": (axes.get("verification_chain_executed", {})
                   .get("pass") is True),
         "evidence": str(axes.get("verification_chain_executed", {})
                         .get("evidence"))},
        {"id": "td7_backend_reproducibility",
         "value": (axes.get("reproducibility", {}).get("pass") is True),
         "evidence": f"确定性实测：{det.get('claim')}"
                     f"（runs={det.get('run_count')}；引擎实况 "
                     f"deterministic={det.get('deterministic')!r}——"
                     "如实记录；nondeterministic 的 TL-4 噪声后果已在"
                     "报告 notes 登记）"},
        {"id": "td7_quality_facts_recorded_not_predicated",
         "value": True,
         "evidence": "质量实况（route success/DRC 双 severity/参考态对比）"
                     "独立记录于 quality_facts，不进资格谓词（用户裁决"
                     "口径；好坏如实，不因过关美化）"},
    ]


# ---------------------------------------------------------------------------
# 10) A/B 统计口径（D20②：N 次重跑+分布报告+中位数对中位数比较）
# ---------------------------------------------------------------------------

# 测量纪律默认值：TL-4 executor 对 challenger/baseline 的 A/B 比较，每臂
# 至少 AB_MIN_RUNS 次同输入重跑（引擎 nondeterministic 已证——D20(b)），
# 单次对比不具判别力（fail-closed：n 不足=insufficient_runs，不下结论）
AB_MIN_RUNS = 3

AB_VERDICT_A_BETTER = "a_better"
AB_VERDICT_B_BETTER = "b_better"
AB_VERDICT_EQUAL = "equal"
AB_VERDICT_INSUFFICIENT = "insufficient_runs"
AB_VERDICT_INCONCLUSIVE = "inconclusive"


def metric_median(values: list) -> float:
    """度量中位数（确定性纯函数；偶数 n 取中间两数均值）。

    values 为空或含非有限数值 ⇒ ValueError（fail-closed，不猜）。
    """
    nums = []
    for v in (values or []):
        n = _finite_num(v)
        if n is None:
            raise ValueError(f"度量值非有限数值: {v!r}")
        nums.append(n)
    if not nums:
        raise ValueError("度量值列表为空（fail-closed）")
    nums.sort()
    mid = len(nums) // 2
    if len(nums) % 2:
        return nums[mid]
    return (nums[mid - 1] + nums[mid]) / 2.0


def summarize_metric(values: list) -> dict:
    """单臂单度量分布摘要：n/median/min/max/distinct（报告口径，
    不挑单次值；输入次序不影响输出——确定性）。"""
    nums = []
    for v in (values or []):
        n = _finite_num(v)
        if n is None:
            raise ValueError(f"度量值非有限数值: {v!r}")
        nums.append(n)
    if not nums:
        raise ValueError("度量值列表为空（fail-closed）")
    return {
        "n": len(nums),
        "median": metric_median(nums),
        "min": min(nums),
        "max": max(nums),
        "distinct_values": len(set(nums)),
        "summary_semantics": "全次报告（median/min/max/distinct），"
                             "不挑单次代表值",
    }


def compare_arm_medians(*, arm_a: list, arm_b: list,
                        lower_is_better: bool = True,
                        min_runs: int = AB_MIN_RUNS) -> dict:
    """两臂中位数对中位数比较（A/B 统计口径核心）。

    纪律（D20②/D20(b) 的落地）：
    - 每臂 n < min_runs ⇒ verdict=insufficient_runs（不下优劣结论——
      引擎 nondeterministic 下单次/双次对比不具判别力）；
    - n 足：median_a vs median_b（lower_is_better=True 时数值小=好，
      如 severity-error 新增数/unconnected 数；False 时大=好）；
    - median 相等 ⇒ equal（分布差异仍如实记录，不升格为优劣）；
    - 非零差 ⇒ a_better/b_better + 幅度（median 差与相对比）；
    - 本函数不做显著性检验（样本极小，只做点估计口径）；分布完全
      分离与否在 separated 字段如实记录，供人工/上游门参考。
    """
    if not isinstance(min_runs, int) or isinstance(min_runs, bool) \
            or min_runs < 2:
        raise ValueError(f"min_runs 非法（>=2）: {min_runs!r}")
    sum_a = summarize_metric(arm_a)
    sum_b = summarize_metric(arm_b)
    ma, mb = sum_a["median"], sum_b["median"]
    n_ok = sum_a["n"] >= min_runs and sum_b["n"] >= min_runs
    if not n_ok:
        verdict = AB_VERDICT_INSUFFICIENT
        detail = (f"arm_a n={sum_a['n']}, arm_b n={sum_b['n']}；"
                  f"min_runs={min_runs}——重跑次数不足，不下优劣结论")
        delta = rel = None
    elif ma == mb:
        verdict = AB_VERDICT_EQUAL
        detail = f"median 相等（{ma}）；分布差异如实记录不升格为优劣"
        delta = 0.0
        rel = 0.0
    else:
        a_better = (ma < mb) if lower_is_better else (ma > mb)
        verdict = (AB_VERDICT_A_BETTER if a_better
                   else AB_VERDICT_B_BETTER)
        delta = round(ma - mb, 6)
        rel = (None if mb == 0 else round(delta / mb, 6))
        detail = (f"median_a={ma} vs median_b={mb}"
                  f"（lower_is_better={lower_is_better}）")
    # 分布分离性（如实记录；非判据）：a 的全分布是否严格优于 b
    separated = None
    if n_ok:
        if lower_is_better:
            separated = max(arm_a) < min(arm_b)
        else:
            separated = min(arm_a) > max(arm_b)
    return {
        "comparison_semantics": "median-vs-median（N 次重跑分布的点估计"
                                "口径；不挑单次；无显著性检验——样本极小"
                                "只做点估计）",
        "min_runs": min_runs,
        "arm_a": sum_a,
        "arm_b": sum_b,
        "median_a": ma,
        "median_b": mb,
        "delta_median": delta,
        "relative_delta": rel,
        "distributions_separated": separated,
        "verdict": verdict,
        "detail": detail,
    }


def build_ab_report(*, arm_labels: dict, metrics: list,
                    arm_runs: dict, min_runs: int = AB_MIN_RUNS) -> dict:
    """多度量 A/B 报告（可复用纯函数；编排侧注入实跑数据）。

    - arm_labels：{"a": "...", "b": "..."}（如 challenger/baseline）；
    - metrics：[{metric_id, lower_is_better, values_a, values_b}]，每臂
      values 为逐次重跑度量值列表（同输入 N 次）；
    - arm_runs：{"a": n_a, "b": n_b} 显式登记每臂重跑次数（与 values
      长度一致性校验，不符=fail-closed）；
    - 总裁决：任一度量 insufficient ⇒ overall=insufficient_runs；
      否则全 equal ⇒ equal；否则按非 equal 度量的 verdict 集合
      （混合方向=conflicting，如实不下单边结论）。
    """
    if set(arm_labels) != {"a", "b"}:
        raise ValueError(f"arm_labels 必须为 a/b 两臂: {arm_labels!r}")
    for arm in ("a", "b"):
        n_declared = (arm_runs or {}).get(arm)
        if not isinstance(n_declared, int) or n_declared < 0:
            raise ValueError(f"arm_runs[{arm!r}] 非法: {n_declared!r}")
    comparisons = []
    verdicts = set()
    for m in metrics or []:
        mid = m.get("metric_id")
        if not isinstance(mid, str) or not mid:
            raise ValueError(f"metric_id 缺失: {m!r}")
        va, vb = m.get("values_a"), m.get("values_b")
        if not isinstance(va, list) or not isinstance(vb, list):
            raise ValueError(f"{mid}: values_a/values_b 必须为 list")
        if len(va) != arm_runs["a"] or len(vb) != arm_runs["b"]:
            raise ValueError(
                f"{mid}: values 长度（a={len(va)}, b={len(vb)}）与 "
                f"arm_runs（a={arm_runs['a']}, b={arm_runs['b']}）不符")
        comp = compare_arm_medians(
            arm_a=va, arm_b=vb,
            lower_is_better=m.get("lower_is_better", True),
            min_runs=min_runs)
        comp["metric_id"] = mid
        comparisons.append(comp)
        verdicts.add(comp["verdict"])
    if not comparisons:
        overall = AB_VERDICT_INSUFFICIENT
    elif AB_VERDICT_INSUFFICIENT in verdicts:
        overall = AB_VERDICT_INSUFFICIENT
    elif verdicts == {AB_VERDICT_EQUAL}:
        overall = AB_VERDICT_EQUAL
    elif verdicts <= {AB_VERDICT_EQUAL, AB_VERDICT_A_BETTER}:
        overall = AB_VERDICT_A_BETTER
    elif verdicts <= {AB_VERDICT_EQUAL, AB_VERDICT_B_BETTER}:
        overall = AB_VERDICT_B_BETTER
    else:
        overall = AB_VERDICT_INCONCLUSIVE
    return {
        "artifact_kind": "ab_statistical_report",
        "track": TRACK,
        "schema_version": SCHEMA_VERSION,
        "min_runs": min_runs,
        "arm_labels": dict(arm_labels),
        "arm_runs": dict(arm_runs),
        "metric_count": len(comparisons),
        "comparisons": comparisons,
        "overall_verdict": overall,
        "notes": [
            "测量纪律（D20②）：引擎 nondeterministic（D20(b)）下 A/B "
            "比较必须每臂 N>=min_runs 次同输入重跑，中位数对中位数"
            "比较，全次分布如实报告（n/median/min/max/distinct），"
            "不挑单次代表值充数。",
            "本报告为点估计口径（无显著性检验）；门/人工裁决可叠加"
            "distributions_separated 与逐次原始值。",
        ],
    }


# ---------------------------------------------------------------------------
# 11) DSN 逐 net 显式规则映射（证伪实验的规则注入器）
# ---------------------------------------------------------------------------

def inject_net_width_rules(dsn_text: str, net_widths: dict) -> dict:
    """在 DSN 的 network 段逐 net 注入 (rule (width W)) 显式映射。

    用途（D20(d) 证伪实验）：若"track_width 违规源于 net-class 未入
    DSN"，则逐 net 显式指定与类相同的宽度应消除违规；实测若细线依旧
    ⇒ 违规根因不在 DSN 规则缺失（引擎减宽回退），证伪闭环。

    - net_widths：{net_name: width_um}（与类宽度同值的显式映射）；
    - net 块内已有 (rule ⇒ 跳过并记 skipped_existing（不重复注入）；
    - net_widths 中未出现在 DSN 的 net 记 missing（如实）；
    - 纯文本最小侵入变换：按括号深度定位 net 块（"(net <name>" 起，
      深度归零止），在块收括号前插入；带引号/裸 net 名均识别。
    """
    if not isinstance(dsn_text, str) or not dsn_text:
        raise ValueError("dsn_text 必须为非空 str")
    if not isinstance(net_widths, dict) or not net_widths:
        raise ValueError("net_widths 必须为非空 {net_name: width_um}")
    for name, w in net_widths.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"net 名非法: {name!r}")
        if not isinstance(w, (int, float)) or isinstance(w, bool) \
                or not math.isfinite(w) or w <= 0:
            raise ValueError(f"{name!r} width 非法: {w!r}")

    net_head_re = re.compile(r'^(\s*)\(net\s+("[^"]*"|\S+)\s*$')
    lines = dsn_text.splitlines()
    out_lines: list = []
    injected: dict = {}
    skipped_existing: list = []
    seen: set = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = net_head_re.match(line)
        if m is None:
            out_lines.append(line)
            i += 1
            continue
        indent, raw_name = m.group(1), m.group(2)
        net_name = raw_name.strip('"')
        seen.add(net_name)
        # 找块尾：从 net 行起做括号深度记账（含本行的 "(net"）
        depth = 0
        block: list = [line]
        j = i
        while j < len(lines):
            for ch in lines[j]:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
            if depth <= 0:
                break
            j += 1
            if j < len(lines):
                block.append(lines[j])
        has_rule = any("(rule" in b for b in block)
        if net_name in net_widths and not has_rule:
            width = net_widths[net_name]
            inner = indent + "  "
            out_lines.extend(block[:-1])
            out_lines.append(f"{inner}(rule")
            out_lines.append(f"{inner}  (width {width})")
            out_lines.append(f"{inner})")
            out_lines.append(block[-1])
            injected[net_name] = width
        else:
            if net_name in net_widths and has_rule:
                skipped_existing.append(net_name)
            out_lines.extend(block)
        i = j + 1
    missing = sorted(set(net_widths) - seen)
    return {
        "dsn_text": "\n".join(out_lines) + "\n",
        "injected_nets": injected,
        "skipped_existing": skipped_existing,
        "missing_nets": missing,
    }
