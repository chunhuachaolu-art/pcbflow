"""pcbflow.experimental — 实验性旁路模块（不属正式命令面，不改变 SPEC 门）。

本包内模块均为只读 shadow/诊断工具：纯内存构建、stdout 输出、零落盘、
零子进程（生成器模式）。产物不进入正式阶段产物目录，不参与任何
gate/verdict 判定；正式契约仍以 SPEC v1.1 与 pcbflow 正式模块为准。
"""
