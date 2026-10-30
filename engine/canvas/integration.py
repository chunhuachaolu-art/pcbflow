# -*- coding: utf-8 -*-
"""integration —— 编排体集成件（波1 真接线，非车道交付物）。

两处缝的正式接线（合同 §1 之外的编排体粘合层，不改车道文件）:

1. **loop↔protocol apply 缝**: 旧路径逐动作调 ``st.apply_action(action)``；
   ``LoopStateProxy.apply_action`` 仍是单动作批退化调用。M2R3 批路径经
   ``LoopStateProxy.apply_batch(actions, round_no=None)`` 直接调用
   ``protocol.apply_consistent_batch``，保留批内重排/固定点/一致性语义。
   旧逐动作路径的语义披露：退化只丢"同批内未行进动作互认"，拒收只会更严
   不会放宽（保守方向，fail-closed 性质保持）。
2. **wrap 板载入单源**: 合同 §0 勘误（D-CT-001）后实战口径= json.load →
   raw["board"] 体 → v5.board.load_board（schema+跨字段+哈希链全校验）。

state_factory 供 ``canvas.loop.replay`` 注入（CanvasState 构造需 lat/anchors）。
"""
import json

from . import state as _state
from . import protocol as _protocol


class LoopStateProxy(object):
    """loop apply 缝适配：一致性批施加 + legacy 单动作退化。"""

    def __init__(self, st):
        self._st = st

    def apply_batch(self, actions, round_no=None):
        """M2R3 一致性批施加；不在此处重排或改写结果。"""
        return _protocol.apply_consistent_batch(self._st, actions, round_no)

    def apply_action(self, action):
        """兼容旧 loop 的单动作 apply 缝（legacy 批退化）。"""
        res = _protocol.apply_batch(self._st, [action])
        first = res[0]
        return (first.get("accepted", False),
                first.get("code"),
                first.get("detail"))

    def __getattr__(self, name):
        return getattr(self._st, name)

    @property
    def lat(self):
        """合同缝名 lat ↔ K1 实件属性名 lattice 的桥接（可序列化投影）。

        键集: {pitch_mm, cols(=i_max+1), rows(=j_max+1), x0_mm, y0_mm}；
        pack.view_spec 只透传投影不做几何消费（K2 桩形态 LAT 同构）。"""
        lat = self._st.lattice
        return {"pitch_mm": lat.pitch, "cols": lat.i_max + 1,
                "rows": lat.j_max + 1, "x0_mm": lat.x0, "y0_mm": lat.y0}


def make_loop_state(st):
    return LoopStateProxy(st)


def _unproxy(st):
    return st._st if isinstance(st, LoopStateProxy) else st


def state_facts(st):
    """state_call 缝（pack/loop 经 type(st).__module__ 命中本函数）→ K1 真件。"""
    return _state.state_facts(_unproxy(st))


def state_sha256(st):
    return _state.state_sha256(_unproxy(st))


def load_wrapped_board(path):
    """wrap 件 → (board 体, board_sha256, board_path)。D8 现役口径单源。"""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    board = raw["board"]
    sha = board["provenance"]["board_sha256"]
    return board, sha, path


def build_state(board, board_path, board_sha256, pitch_mm=None):
    lat = _state.Lattice.from_board(board, pitch_mm) if pitch_mm \
        else _state.Lattice.from_board(board)
    anchors = _state.anchor_map(board, lat)
    return _state.CanvasState(board, board_path, board_sha256, lat, anchors)


def default_state_factory(board, board_path):
    """canvas.loop.replay 的 state_factory 注入口（apply 缝经代理接线）。"""
    sha = board["provenance"]["board_sha256"]
    return make_loop_state(build_state(board, board_path, sha))
