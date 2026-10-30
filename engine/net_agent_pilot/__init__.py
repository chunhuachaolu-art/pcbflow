# -*- coding: utf-8 -*-
"""net_agent_pilot —— 网级 agent 布线 P1 最小验证（memo 2026-09-27 落地件）。

架构（松绑版，2026-09-27 用户裁定"先跑着试试"）:
- proposal 直接采用 canvas-edit-v2 动作协议（route/via/submit），零新 schema；
- 验证链整条复用 canvas 现役件: parse_batch / validate_edit(v5.drc 同源) /
  apply_consistent_batch / RunLoop 链式台账 / replay / instantiate / export；
- 本包只补两块胶水: ①单网切片（席位盲包=局部格点地图+动作协议）；
  ②摄入循环（proposal 文件 → RunLoop 单轮批施加 → 台账落链）。
- 席位=ZCode 子智能体（主对话派发），回执以落盘为准；切片地图是提示，
  机械验证器是唯一裁决（fail-closed 纪律照 CANVAS 合同 §3 盲化禁项）。

不触碰: v5/、canvas/、boards/、datasets/ 现役件（只读 import）。
产物域: out/net-agent-p1/<run>/。
"""
