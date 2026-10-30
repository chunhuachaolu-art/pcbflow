# -*- coding: utf-8 -*-
"""canvas.loop —— 轮循环 runner + 链式哈希台账（Lane-K2；合同 §1 loop 节）。

RunLoop(st, ledger_path, seat_fn)：轮循环 seat→parse→apply→台账；
默认逐动作 apply；显式 ``batch_mode=True`` 时整批 apply 一次并记录
重排后的完整 batch 列。replay(ledger_path, board_path) -> 终态（旧行按
edit-list 逐动作；带 batch 行整批重放）。

**文档化最小决定（逐字披露）**：

- **seat_fn(round, pack) -> actions_text**（席位派发桩接口，编排体注入真
  席位）。返回 None 或空串 = 席位停车（循环正常结束，不落轮次行）；其余
  异常上抛 fail-closed。
- **parser 缝**：构造器可注入 parser callable（签名
  ``parser(text, expected_round) -> [action dicts]``，对齐合同
  ``canvas.protocol.parse_batch(text, expected_round)``）。未注入时运行期
  延迟 import canvas.protocol（真件落地后自动接线；未落地=RuntimeError
  fail-closed，不静默）。
- **apply 缝**：默认逐动作经 ``st.apply_action(action) -> (accepted, code,
  detail)``；``batch_mode=True`` 时必须有
  ``st.apply_batch(actions, round_no=None) -> result list``，每轮只调用一次，
  缺失即 RuntimeError fail-closed。批结果按原输入 ``index`` 对齐摘要，完整
  重排动作列落 ``batch``；submit 动作不做特判（改不改几何由缝侧决定）。
- **BatchReject 识别**：canvas.protocol 可导入时 isinstance 判定；否则按
  类名 ``BatchReject`` duck 匹配（桩 parser 复用同名类即可）。批拒收=轮
  verdict="batch-rejected"、edit_list=[]、循环继续下一轮；批模式还记
  batch=[]；其它异常上抛。
- **台账行**（canonical_json + "\\n"）：
  旧模式 ``{round, prev_sha256, state_sha256, actions_sha256, accepted,
  rejected, edit_list, verdict}``；批模式仅追加 ``batch`` 字段（确定性重排
  后完整动作列，含拒收动作与 submit）；
  - 首行 prev=64×"0"；后续 prev=上一行**文件字节**（含换行）的 sha256
    （链式哈希；行内不含自身哈希，避免自指）。
  - actions_sha256 = sha256(actions_text utf-8 字节)（原始席位输出，跨
    接受/拒收统一可算）。
  - accepted/rejected 为逐动作摘要（index/action/code/detail）；批模式 index
    沿原输入列，不是重排位置。edit_list 为**完整接受动作 dict 列表**
    （deepcopy 防缝内变异渗入；仅旧 ledger 的 replay 以之为重放源）。
  - state_sha256 = 轮末 state 哈希（canvas.pack.state_call 缝兼容 accessor）。
- **追加语义**：run(append=False) 要求台账文件不存在（防覆盖混链）；
  append=True 续既有链（断点续跑）。
- **replay 的 state_factory**：CanvasState 构造需 lat/anchors（合同 §1，
  编排体域，非 board.json 可推导），故 replay 必须注入
  ``state_factory(board, board_path) -> st``（返回**初始**态）；未注入=
  RuntimeError fail-closed（真接线=编排体以 canvas.state 构造）。重放中
  逐行核链（prev 哈希逐行重算）+ 逐轮核态（轮末 state_sha256 复算比对）；
  无 batch 的旧行重放 edit_list，动作被拒=非确定性、fail-closed；有 batch
  的行整批重放一次，只硬校验链与 state_sha256，不硬比摘要。
"""

import copy
import importlib
import json
import os

from v5.canonical import canonical_json, sha256_bytes

from canvas.pack import pack_view, state_call

GENERATOR = "canvas.loop"
VERSION = "1.0.0"

ZERO_SHA = "0" * 64
VERDICT_APPLIED = "applied"
VERDICT_BATCH_REJECTED = "batch-rejected"


class _ProtocolGap(RuntimeError):
    """合同缝未接线（parser/apply/state_factory）——fail-closed，不静默。"""


def _load_protocol():
    """运行期延迟加载 canvas.protocol（K1 真件落地后自动可用）。

    importlib.import_module 走 sys.modules 条目（测试可注入 None 强制
    ImportError）；不用 ``from canvas import protocol``——from-import 有
    父包属性捷径，会绕过 sys.modules 注入。
    """
    try:
        return importlib.import_module("canvas.protocol")
    except ImportError:
        return None


def _batch_reject_class():
    protocol = _load_protocol()
    if protocol is not None and hasattr(protocol, "BatchReject"):
        return protocol.BatchReject, True
    return "BatchReject", False  # (类名匹配目标, 是否 isinstance 可用)


def _is_batch_reject(exc):
    """真件 isinstance（canvas.protocol 已落地）∨ 桩类名匹配（同名缝）。"""
    cls, exact = _batch_reject_class()
    if exact and isinstance(exc, cls):
        return True
    return type(exc).__name__ == "BatchReject"


def _default_parser(text, expected_round):
    protocol = _load_protocol()
    if protocol is None or not hasattr(protocol, "parse_batch"):
        raise _ProtocolGap(
            "parser 未注入且 canvas.protocol 未落地（K1 并行车道）——"
            "真接线=编排体集成冒烟；测试须注入桩 parser")
    return protocol.parse_batch(text, expected_round)


def _apply_via_seam(st, action):
    """apply 缝：st.apply_action(action) -> (accepted, code, detail)。"""
    hook = getattr(st, "apply_action", None)
    if not callable(hook):
        raise _ProtocolGap(
            "apply 缝未接线: st 无 apply_action(action) 方法——真接线=编排体"
            "将 K1 validate_edit/CanvasState 变更与此缝钉合")
    return hook(action)


def _apply_batch_via_seam(st, actions, round_no):
    """M2R3 apply 缝：st.apply_batch(actions, round_no) 一次整批施加。"""
    hook = getattr(st, "apply_batch", None)
    if not callable(hook):
        raise _ProtocolGap(
            "batch apply 缝未接线: st 无 apply_batch(actions, round_no) 方法——"
            "batch_mode=True 必须显式接入一致性批语义")
    return hook(actions, round_no)


def _reorder_batch_for_ledger(actions):
    """取 protocol 的确定性重排副本，供 batch 台账落原始动作列。"""
    protocol = _load_protocol()
    if protocol is None or not hasattr(protocol, "reorder_batch"):
        raise _ProtocolGap(
            "batch reorder 缝未接线: canvas.protocol.reorder_batch 不可用")
    return protocol.reorder_batch(copy.deepcopy(actions))


def _summarize_batch(actions, results):
    """按原输入 index 汇总批结果，并构造 accepted/edit_list。"""
    if not isinstance(results, (list, tuple)):
        raise _ProtocolGap("batch apply 返回值须为结果列表")
    by_index = {}
    for result in results:
        if not isinstance(result, dict):
            raise _ProtocolGap("batch apply 结果项须为对象")
        index = result.get("index")
        if (not isinstance(index, int) or isinstance(index, bool)
                or index < 0 or index >= len(actions) or index in by_index):
            raise _ProtocolGap(
                "batch apply 结果 index 非法或重复: %r" % (index,))
        by_index[index] = result
    if len(by_index) != len(actions):
        raise _ProtocolGap(
            "batch apply 结果未覆盖完整输入列: %d/%d"
            % (len(by_index), len(actions)))

    accepted, rejected, edit_list = [], [], []
    for index, action in enumerate(actions):
        result = by_index[index]
        entry = {"index": index, "action": action.get("action")}
        if result.get("accepted") is True:
            accepted.append(entry)
            edit_list.append(copy.deepcopy(action))
        else:
            rejected.append(dict(
                entry,
                code=result.get("code"),
                detail=str(result.get("detail")),
            ))
    return accepted, rejected, edit_list


def _read_chain_tail(ledger_path):
    """读既有台账（末行字节哈希, 末行轮号）续链锚；空/无文件=(64×"0", 0)。"""
    if not os.path.isfile(ledger_path):
        return ZERO_SHA, 0
    prev = ZERO_SHA
    last_round = 0
    with open(ledger_path, "rb") as f:
        for line in f:
            if line.strip():
                prev = sha256_bytes(line)
                last_round = json.loads(line.decode("utf-8")).get(
                    "round", last_round)
    return prev, last_round


def _append_line(ledger_path, record):
    """canonical 行落盘（追加），返回 (行字节, 行哈希)。"""
    data = canonical_json(record) + b"\n"
    with open(ledger_path, "ab") as f:
        f.write(data)
    return data, sha256_bytes(data)


class RunLoop(object):
    """轮循环 runner：seat→parse→apply→链式台账。"""

    def __init__(self, st, ledger_path, seat_fn, parser=None,
                 batch_mode=False):
        self.st = st
        self.ledger_path = os.fspath(ledger_path)
        self.seat_fn = seat_fn
        self.parser = parser if parser is not None else _default_parser
        self.batch_mode = batch_mode

    def run(self, max_rounds, append=False):
        """跑至席位停车或 max_rounds 尽。返回循环摘要 dict（不改 st 引用）。"""
        if max_rounds < 1:
            raise ValueError("max_rounds 须 ≥1，实得 %r" % (max_rounds,))
        if os.path.isfile(self.ledger_path) and not append:
            raise ValueError(
                "台账已存在且非追加模式（防覆盖混链）: %s（续跑用 append=True）"
                % self.ledger_path)
        parent = os.path.dirname(self.ledger_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        prev, last_round = _read_chain_tail(self.ledger_path) if append \
            else (ZERO_SHA, 0)

        rounds_logged = 0
        verdicts = []
        for offset in range(1, max_rounds + 1):
            round_no = last_round + offset  # 续跑时轮号接续既有链尾
            pack = pack_view(self.st)
            actions_text = self.seat_fn(round_no, pack)
            if actions_text is None or actions_text == "":
                verdicts.append("seat-stop")
                break  # 席位停车：正常结束，不落轮次行

            record = {
                "round": round_no,
                "prev_sha256": prev,
                "actions_sha256": sha256_bytes(
                    actions_text.encode("utf-8")),
                "verdict": VERDICT_APPLIED,
            }
            try:
                actions = self.parser(actions_text, round_no)
            except Exception as exc:  # noqa: BLE001 —— 分类见下
                if _is_batch_reject(exc):
                    record["verdict"] = VERDICT_BATCH_REJECTED
                    record["accepted"] = []
                    record["rejected"] = [{
                        "index": None, "action": None,
                        "code": getattr(exc, "code", None),
                        "detail": str(exc),
                    }]
                    record["edit_list"] = []
                    if self.batch_mode:
                        record["batch"] = []
                else:
                    raise  # 非批拒收异常：fail-closed 上抛
            else:
                if self.batch_mode:
                    # protocol.apply_consistent_batch 返回原输入 index；动作列
                    # 单独取确定性重排副本供台账审计/重放。给 apply 缝一份
                    # 独立快照，避免缝内变异污染摘要/台账动作列。
                    batch_actions = copy.deepcopy(actions)
                    record["batch"] = _reorder_batch_for_ledger(batch_actions)
                    results = _apply_batch_via_seam(
                        self.st, copy.deepcopy(batch_actions), round_no)
                    accepted, rejected, edit_list = _summarize_batch(
                        batch_actions, results)
                else:
                    accepted, rejected, edit_list = [], [], []
                    for index, action in enumerate(actions):
                        ok, code, detail = _apply_via_seam(self.st, action)
                        entry = {"index": index,
                                 "action": action.get("action")}
                        if ok:
                            accepted.append(entry)
                            edit_list.append(copy.deepcopy(action))
                        else:
                            rejected.append(dict(entry, code=code,
                                                 detail=str(detail)))
                record["accepted"] = accepted
                record["rejected"] = rejected
                record["edit_list"] = edit_list

            record["state_sha256"] = state_call(self.st, "state_sha256")
            # 键序由 canonical_json sort_keys 固定；此处仅组装
            ordered = {
                "round": record["round"],
                "prev_sha256": record["prev_sha256"],
                "state_sha256": record["state_sha256"],
                "actions_sha256": record["actions_sha256"],
                "accepted": record["accepted"],
                "rejected": record["rejected"],
                "edit_list": record["edit_list"],
                "verdict": record["verdict"],
            }
            if self.batch_mode:
                ordered["batch"] = record["batch"]
            _, prev = _append_line(self.ledger_path, ordered)
            rounds_logged += 1
            verdicts.append(ordered["verdict"])
        return {
            "rounds_logged": rounds_logged,
            "verdicts": verdicts,
            "final_state_sha256": state_call(self.st, "state_sha256"),
            "ledger_path": self.ledger_path,
        }


def replay(ledger_path, board_path, state_factory=None):
    """台账 + 板 → 终态（旧行 edit_list，新行 batch）。

    逐行核链（prev_sha256 重算）→ 无 batch 行逐动作重放 edit_list，有 batch
    行整批重放一次 → 轮末 state_sha256 复算比对台账值；任何不符=fail-closed。
    返回终态 st。
    """
    if state_factory is None:
        raise _ProtocolGap(
            "replay 需 state_factory(board, board_path) 注入（CanvasState 构造"
            "需 lat/anchors，属编排体域非 board.json 可推导）——真接线=编排体"
            "集成冒烟")
    with open(board_path, encoding="utf-8") as f:
        doc = json.load(f)
    board = doc["board"] if "board" in doc and "schema_version" not in doc \
        else doc  # wrap 件取体（合同 §0）；裸 board.v1 原样
    import v5.board
    v5.board.load_board(board)  # schema+哈希链复算（v5.board 锚，fail-closed）

    st = state_factory(board, board_path)
    prev = ZERO_SHA
    last_round = 0
    with open(ledger_path, "rb") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            record = json.loads(line.decode("utf-8"))
            if record.get("prev_sha256") != prev:
                raise ValueError(
                    "台账链断裂 @行%d: prev %r != 重算 %r"
                    % (line_no, record.get("prev_sha256"), prev))
            if record.get("round", last_round) != last_round + 1:
                raise ValueError("台账轮号不连续 @行%d（%r）"
                                 % (line_no, record.get("round")))
            last_round = record["round"]
            if "batch" in record:
                # M2R3 行以完整、已重排动作列为重放源；结果摘要只作
                # 审计披露，不在此处与 accepted/rejected 做脆弱比对。
                _apply_batch_via_seam(st, record["batch"], record["round"])
            else:
                # 旧台账没有 batch 字段，保持逐动作 edit_list 重放语义。
                for action in record.get("edit_list", []):
                    ok, code, detail = _apply_via_seam(st, action)
                    if not ok:
                        raise ValueError(
                            "重放非确定性 @行%d: 动作 %r 重放被拒（code=%r "
                            "detail=%r）——同输入重放必须逐动作可复现"
                            % (line_no, action.get("action"), code, detail))
            recomputed = state_call(st, "state_sha256")
            if recomputed != record.get("state_sha256"):
                raise ValueError(
                    "台账态哈希不复算 @行%d: 台账 %r，重放 %r"
                    % (line_no, record.get("state_sha256"), recomputed))
            prev = sha256_bytes(line)
    return st
