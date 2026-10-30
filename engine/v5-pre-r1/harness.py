# -*- coding: utf-8 -*-
"""席位 harness 库化（任务书 §3.4/§4-L4/A6；P3 交付）。

从 V2 SEAT-AB 三件套自存证流程（seat_ab_r1a.py 口径）库化：
  包落盘 →（模型会话由主审驱动，产物由人工/会话放入 run 目录——本模块
  **零网络、零 LLM API 调用**，A8/R46 红线）→ 回读校验。

三席位（seat 仅作元数据记录，本模块不写死任何模型名——第三路阵容=U10）：
  seat_a_diagnostic / shadow_b / seat_c_review

三件套（run 目录三文件，§3.4 自存证；ingest 只读、逐字不改）：
  response-raw.md  模型回复原文（逐字留痕；raw_sha256 进校验产物）
  output.json      会话/人工从回复结构化的序数 json
  meta.json        运行元数据（seat + pkg_sha256 溯源绑定，由制备记录转录）

ingest_run 回读合同（任一环节失败 fail-closed，错误消息带 run 目录路径）：
  1. 三件套齐备；
  2. meta.json 格式合法：JSON 对象 + seat ∈ 三席位 + pkg_sha256 与包对账
     （证据链按 hash 对账，§3.1）+ 可选 board_sha256 对账；
  3. response-raw.md 含**恰一个** ```json 代码块；output.json 与之逐键相等
     （移植 seat_ab_r1a 比对口径；首个差异报键路径）；
  4. 序数 json 按 A3 五通道形状校验——按 pkg.output_contract 声明的通道校验
     **在场者**（不要求五通道全在场）；A3 合同外通道 / 枚举外值 / 结构坏 →
     fail-closed 报键路径（A3：模型输出只有五通道）；
  5. 产物 {"seat","board_sha256","pkg_sha256","output","raw_sha256"}。

文档化最小决定（偏离规格处的最小落法）：
1. seat 不能写进 v5.pkg.v1 包体（schema additionalProperties=false 冻结，
   P2 交付件不回改），故包元数据由本模块 sidecar
   ``<board-id>.harness-meta-<seat>.json`` 承载 seat 与 pkg_sha256；
   pkg_sha256 = canonical(剔除注入 provenance 头后的包内容) 的 sha256——
   内存包与落盘回读件两形态同 hash。run 目录 meta.json 的 seat/pkg_sha256
   由本制备记录转录给主审。
2. 图文双输入包（§3.4/D2）：SVG 视图（v5.view 渲染，同输入双跑字节等）与
   文本包同目录配对；视图文件名同样记入本模块包元数据（决定 1 同因）；
   视图只作席位判读输入、**永不进测量环**（§3.4/D2；图像不是测量依据、
   不是修改入口）。
"""

import hashlib
import json
import os
import re

from . import canonical, sidecar
from . import pkg as pkg_mod
from . import view as view_mod

GENERATOR = "v5.harness"
VERSION = "0.1.0"

# 三席位（A6；seat 仅作元数据记录）
SEATS = ("seat_a_diagnostic", "shadow_b", "seat_c_review")

# run 目录三件套固定名（V2 三件套自存证口径）
RAW_NAME = "response-raw.md"
OUTPUT_NAME = "output.json"
META_NAME = "meta.json"

# defect_scan.rule 枚举（v5.pkg.CHANNELS 模板串「R1..R6 或 自相矛盾」的枚举集）
DEFECT_SCAN_RULES = ("R1", "R2", "R3", "R4", "R5", "R6", "自相矛盾")

# A3 五通道合同名（形状校验器支持的通道；声明中出现其它名=未知形状 fail-closed）
_A3_CHANNELS = ("ranked_options", "ranked_combos", "routing_order",
                "defect_scan", "principle_objection")

_OPEN_FENCE_RE = re.compile(r"^```[ \t]*json[ \t]*$")
_CLOSE_FENCE_RE = re.compile(r"^```[ \t]*$")


class HarnessError(ValueError):
    """harness fail-closed 错误；location=run 目录（制备期为 out_dir），
    path=键路径，message=原因。消息恒含 location（fail-closed 带路径）。"""

    def __init__(self, location, path, message):
        self.location = location
        self.path = path
        self.message = message
        super().__init__("[%s] [%s] %s" % (location, path or "<root>", message))


def _require(cond, location, path, msg):
    if not cond:
        raise HarnessError(location, path, msg)


# ---------------------------------------------------------------- 包制备

def pkg_sha256(pkg):
    """包内容 sha256 = sha256(canonical(剔除注入 provenance 头后的包))。

    内存包（build_pkg 产物）与落盘回读件（write_pkg 注入 provenance 后再读回）
    两形态同 hash——制备记录与 run 目录 meta.json 的对账依据。
    """
    content = {k: v for k, v in pkg.items() if k != "provenance"}
    return canonical.canonical_sha256(content)


def prepare_pkg(board, partition_artifact, conflicts_artifact, seat, out_dir):
    """组装 v5.pkg.v1 盲包并落盘（seat 仅作包元数据记录）；返回制备记录。

    落盘件：``<board-id>.pkg-<seat>.json``（盲包，sidecar 注入 provenance 头）
    + ``<board-id>.harness-meta-<seat>.json``（包元数据：seat/pkg_sha256/文件名）。
    全部写入经 sidecar 卫生（§3.5：只准 ALLOWED_ROOTS 之下）；seat 非法或路径
    越界在**任何写盘之前** fail-closed（零半成品）。
    """
    return _prepare(board, partition_artifact, conflicts_artifact, seat, out_dir,
                    multimodal_mode=None)


def prepare_multimodal(board, partition_artifact, conflicts_artifact, seat,
                       out_dir, mode="all"):
    """图文双输入包（§3.4/D2）：L1 SVG 视图（v5.view 渲染）+ 文本包同目录配对，
    视图文件名记入包元数据。视图只作判读输入，永不进测量环。

    mode 语义同 v5.view（"all" 全层叠加或单层 id）；渲染失败即整体失败、
    零半成品落盘。
    """
    return _prepare(board, partition_artifact, conflicts_artifact, seat, out_dir,
                    multimodal_mode=mode)


def _prepare(board, partition_artifact, conflicts_artifact, seat, out_dir,
             multimodal_mode):
    _check_seat(seat, out_dir)
    # 纯计算先行（fail-closed 早爆）：组装包（内含全量合同校验）+ 渲染视图
    pkg = pkg_mod.build_pkg(board, partition_artifact, conflicts_artifact)
    svg = None
    if multimodal_mode is not None:
        svg = view_mod.render_l1_view(board, partition_artifact, multimodal_mode)

    # 落盘前先核路径卫生（§3.5；越界在写盘之前爆，零半成品）
    pkg_path = os.path.join(out_dir,
                            sidecar.sidecar_name(pkg["board_id"], "pkg-" + seat, "json"))
    meta_path = os.path.join(
        out_dir, sidecar.sidecar_name(pkg["board_id"], "harness-meta-" + seat, "json"))
    view_kind = "l1-view-" + seat
    sidecar.assert_allowed(pkg_path)
    sidecar.assert_allowed(meta_path)
    if svg is not None:
        sidecar.assert_allowed(os.path.join(
            out_dir, sidecar.sidecar_name(pkg["board_id"], view_kind, "svg")))

    # 落盘：盲包 → 视图（若有）→ 包元数据
    pkg_mod.write_pkg(pkg, pkg_path)
    view_file = None
    if svg is not None:
        written = view_mod.write_view(svg, view_kind, pkg["board_id"],
                                      pkg["board_sha256"], out_dir)
        view_file = os.path.basename(written)
    record = {
        "seat": seat,
        "board_id": pkg["board_id"],
        "board_sha256": pkg["board_sha256"],
        "pkg_sha256": pkg_sha256(pkg),
        "pkg_file": os.path.basename(pkg_path),
        "multimodal_view": ({"stage": "l1", "mode": multimodal_mode,
                             "file": view_file} if view_file else None),
    }
    sidecar.write_sidecar(meta_path, record, GENERATOR, VERSION, pkg["board_sha256"])
    return record


def _check_seat(seat, location):
    _require(seat in SEATS, location, "seat",
             "seat 非法 %r（允许 %r）" % (seat, list(SEATS)))


# ---------------------------------------------------------------- 证据回读

def ingest_run(run_dir, pkg):
    """回读 run 目录三件套并校验；返回
    {"seat","board_sha256","pkg_sha256","output","raw_sha256"}。

    pkg 可传内存包（build_pkg 产物）或落盘回读件（含 provenance 头）——
    pkg_sha256 两形态同 hash。本函数只读：三件套逐字不改。
    任一环节失败抛 HarnessError（消息带 run 目录路径）。
    """
    raw_path = os.path.join(run_dir, RAW_NAME)
    output_path = os.path.join(run_dir, OUTPUT_NAME)
    meta_path = os.path.join(run_dir, META_NAME)
    _require(os.path.isfile(raw_path), run_dir, RAW_NAME, "三件套缺 %s" % RAW_NAME)
    _require(os.path.isfile(output_path), run_dir, OUTPUT_NAME,
             "三件套缺 %s" % OUTPUT_NAME)
    _require(os.path.isfile(meta_path), run_dir, META_NAME, "三件套缺 %s" % META_NAME)

    # meta.json：格式合法 + seat/pkg_sha256 溯源对账（§3.1 按 hash 对账）
    meta = _load_json_file(meta_path, run_dir, META_NAME)
    _require(isinstance(meta, dict), run_dir, META_NAME, "须为 JSON 对象")
    _require(meta.get("seat") in SEATS, run_dir, "meta.seat",
             "seat 非法 %r（允许 %r）" % (meta.get("seat"), list(SEATS)))
    _require(isinstance(meta.get("pkg_sha256"), str) and meta["pkg_sha256"],
             run_dir, "meta.pkg_sha256", "必填非空字符串（与包 hash 对账）")
    digest = pkg_sha256(pkg)
    _require(meta["pkg_sha256"] == digest, run_dir, "meta.pkg_sha256",
             "与包对账失败: meta=%s 复算=%s（证据链按 hash 对账，§3.1）"
             % (meta["pkg_sha256"], digest))
    if "board_sha256" in meta:
        _require(meta["board_sha256"] == pkg.get("board_sha256"), run_dir,
                 "meta.board_sha256",
                 "与包对账失败: meta=%s 包=%s" % (meta["board_sha256"],
                                                 pkg.get("board_sha256")))

    # response-raw.md：逐字读入（只读不改）+ 恰一个 ```json 代码块
    with open(raw_path, "rb") as f:
        raw_bytes = f.read()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HarnessError(run_dir, RAW_NAME, "非 UTF-8 文本: %s" % exc) from exc
    blocks = _extract_json_blocks(raw_text, run_dir)
    _require(len(blocks) == 1, run_dir, RAW_NAME,
             "json 代码块须恰 1 个（V2 输出合同），得到 %d" % len(blocks))
    raw_obj = _parse_json_text(blocks[0], run_dir, RAW_NAME + "<json 代码块>")

    # output.json 与 raw 内唯一 json 代码块逐键相等（移植 seat_ab_r1a 比对口径）
    output_obj = _load_json_file(output_path, run_dir, OUTPUT_NAME)
    diff = _first_diff(raw_obj, output_obj, "")
    _require(diff is None, run_dir, OUTPUT_NAME,
             "与 %s 内 json 代码块逐键不等，首个差异: %s" % (RAW_NAME, diff))

    # A3 五通道形状校验（按 pkg.output_contract 声明通道校验在场者）
    validate_ordinal_channels(output_obj, pkg, run_dir)

    return {"seat": meta["seat"],
            "board_sha256": pkg.get("board_sha256"),
            "pkg_sha256": digest,
            "output": output_obj,
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest()}


def _load_json_file(path, location, tag):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError as exc:
        raise HarnessError(location, tag, "非 UTF-8 文本: %s" % exc) from exc
    return _parse_json_text(text, location, tag)


def _parse_json_text(text, location, tag):
    try:
        return json.loads(text)
    except ValueError as exc:
        raise HarnessError(location, tag, "JSON 解析失败: %s" % exc) from exc


def _extract_json_blocks(text, location):
    """提取 ```json 围栏代码块（行首围栏口径）；未闭合 fail-closed。"""
    blocks = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if _OPEN_FENCE_RE.match(lines[i]):
            buf, j = [], i + 1
            while j < n and not _CLOSE_FENCE_RE.match(lines[j]):
                buf.append(lines[j])
                j += 1
            if j >= n:
                raise HarnessError(location, RAW_NAME,
                                   "json 代码块未闭合（起于第 %d 行）" % (i + 1))
            blocks.append("\n".join(buf))
            i = j + 1
        else:
            i += 1
    return blocks


def _first_diff(raw_obj, out_obj, path):
    """逐键比对，返回首个差异键路径描述；全等返回 None。

    逐键相等口径（移植 seat_ab_r1a）：键集合对称差报「仅 raw / 仅 output.json」；
    bool 与数值严格区分（True≠1）；数值 1 与 1.0 视为相等（JSON 数值语义）。
    """
    if isinstance(raw_obj, bool) != isinstance(out_obj, bool):
        return path or "<root>"
    if isinstance(raw_obj, dict) and isinstance(out_obj, dict):
        for key in sorted(set(raw_obj) | set(out_obj)):
            sub = _join(path, key)
            if key not in raw_obj:
                return sub + "(仅 output.json)"
            if key not in out_obj:
                return sub + "(仅 raw)"
            found = _first_diff(raw_obj[key], out_obj[key], sub)
            if found is not None:
                return found
        return None
    if isinstance(raw_obj, list) and isinstance(out_obj, list):
        if len(raw_obj) != len(out_obj):
            return "%s(长度 %d vs %d)" % (path or "<root>",
                                          len(raw_obj), len(out_obj))
        for i, (a, b) in enumerate(zip(raw_obj, out_obj)):
            found = _first_diff(a, b, "%s[%d]" % (path, i))
            if found is not None:
                return found
        return None
    return None if raw_obj == out_obj else (path or "<root>")


def _join(path, key):
    return "%s.%s" % (path, key) if path else key


# ---------------------------------------------------------------- A3 五通道校验

def validate_ordinal_channels(output, pkg, location=""):
    """序数 json 按 A3 五通道形状校验（fail-closed 报键路径）。

    - output 须为对象；每个键必须是 pkg.output_contract 声明的通道
      （A3：模型输出只有五通道，合同外通道即拒）；
    - **不要求五通道全在场**：只对「声明 ∩ 在场」的通道逐一校验形状/枚举；
    - 声明中出现形状校验器不认识的通道名（非 A3 五通道）→ 未知形状 fail-closed。
    """
    contract = pkg.get("output_contract") if isinstance(pkg, dict) else None
    declared = contract.get("channels") if isinstance(contract, dict) else None
    _require(isinstance(declared, dict), location, "pkg.output_contract.channels",
             "包未声明通道合同（fail-closed）")
    _require(isinstance(output, dict), location, "",
             "序数 json 须为对象（A3 五通道），得到 %s" % type(output).__name__)
    for key in sorted(output):
        _require(key in declared, location, key,
                 "A3/pkg.output_contract 合同外通道（模型输出只有五通道）")
    for name in sorted(set(declared) & set(output)):
        _validate_channel(name, output[name], location)


def _validate_channel(name, value, location):
    path = name
    if name == "ranked_options":
        _require(isinstance(value, list) and value, location, path,
                 "须为非空数组（A3 形状）")
        for i, item in enumerate(value):
            p = "%s[%d]" % (path, i)
            _require(isinstance(item, dict) and set(item) == {"label"},
                     location, p, "须为恰含 label 的对象")
            _require(isinstance(item["label"], str) and item["label"],
                     location, p + ".label", "须为非空字符串")
    elif name == "ranked_combos":
        _require(isinstance(value, list) and value, location, path,
                 "须为非空数组（A3 形状）")
        for i, item in enumerate(value):
            p = "%s[%d]" % (path, i)
            _require(isinstance(item, dict), location, p, "须为对象")
            _require(isinstance(item.get("label"), str) and item["label"],
                     location, p + ".label", "须为非空字符串")
    elif name == "routing_order":
        _require(isinstance(value, list) and value, location, path,
                 "须为非空数组（A3 形状）")
        for i, item in enumerate(value):
            _require(isinstance(item, str) and item, location,
                     "%s[%d]" % (path, i), "须为非空字符串（partition_id）")
    elif name == "defect_scan":
        _require(isinstance(value, list) and value, location, path,
                 "须为非空数组（A3 形状）")
        for i, item in enumerate(value):
            p = "%s[%d]" % (path, i)
            _require(isinstance(item, dict) and set(item) == {"subject", "rule", "note"},
                     location, p, "须为恰含 subject/rule/note 的对象")
            for key in ("subject", "rule", "note"):
                _require(isinstance(item[key], str) and item[key],
                         location, p + "." + key, "须为非空字符串")
            _require(item["rule"] in DEFECT_SCAN_RULES, location, p + ".rule",
                     "枚举外值 %r（允许 %r）" % (item["rule"], list(DEFECT_SCAN_RULES)))
    elif name == "principle_objection":
        _require(isinstance(value, str), location, path,
                 "须为字符串（空串=无反对，允许）")
    else:
        _fail_unknown_channel(name, location)


def _fail_unknown_channel(name, location):
    raise HarnessError(location, name,
                       "未知通道形状（非 A3 五通道 %r，fail-closed）"
                       % (list(_A3_CHANNELS),))
