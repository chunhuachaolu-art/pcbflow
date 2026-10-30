# -*- coding: utf-8 -*-
"""板源适配器包（L0）：外部板文件格式 → v5.board.v1（任务书 §3.1 provenance 落链）。

各 adapter 的局限与确定性策略在其模块 docstring 中披露；产出的板 dict 必须通过
v5.board.load_board 校验后返回。
"""
from . import kicad_adapter

__all__ = ["kicad_adapter"]
