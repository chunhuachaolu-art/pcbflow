# -*- coding: utf-8 -*-
"""canvas_pilot —— CANVAS-PILOT-R1 强制规范画板 + fail-closed 参数化编辑协议。

形态（任务书 §1）: 画板垄断一切坐标与数字（lattice/端点锚/DRC 带值），模型
席位只有格点意图的提案权（route/via/ripup/submit）与修改权；验证权=画板，
验证核直接调用 v5.drc 同源函数族（禁止平行实现——已裁架构原则）。

组件: lattice / state / protocol / instantiate / verify / packer / ledger /
loop。新代码全部在本包（红线: v5/、tests/、tools/、schemas/、boards/、
out 冻结域零回写）；新测试只进 canvas_pilot/tests/。
"""
VERSION = "canvas-pilot/0.1.0"
