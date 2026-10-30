"""pcbflow — 七级 PCB 设计流编译器（SPEC v1.1）。

命令面：compile / enum / audit / co-place / route / check / signoff + db status。
未实现命令一律返回 specified 状态（红线：不得把"已定义"写成"已可用"）。

双版本轴分标（REPAIR-P3 W-5，2026-09-22；只改注释不改值）：
- 本文件 SCHEMA_VERSION="1.1" = **SPEC 编译器轴**（本包实现的 SPEC 文档
  版本，随 SPEC 升版）；
- pcbflow/schemas.py REGISTRY_VERSION="3.0" = **schema 注册表轴**（记录
  schema 合同的追加式注册代次，追加式演进纪律下不动，见
  disposition-APR-0002 / DOC-NAMING-CONVENTION §12 r8）。
两轴独立演进，禁止互相改写或混用。
"""

__version__ = "0.1.0"

SCHEMA_VERSION = "1.1"
