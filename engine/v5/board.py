# -*- coding: utf-8 -*-
"""v5.board.v1 载入与 provenance 落链（任务书 §3.1）。

载入 fail-closed：schema 校验（报具体键路径）+ provenance 哈希链复算。
board_sha256 = sha256(canonical(剔除 provenance.board_sha256 后的整板))；
链式规则：source_sha256 + adapter 版本 + 板内容 ⇒ board_sha256（同源同 adapter 双跑同 hash）。
"""
from . import canonical, schema_loader

SCHEMA_VERSION = "v5.board.v1"


class BoardLoadError(ValueError):
    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def board_for_hash(board: dict) -> dict:
    """剔除 provenance.board_sha256 后的可哈希视图（浅拷贝保护输入）。"""
    view = dict(board)
    prov = dict(view.get("provenance", {}))
    prov.pop("board_sha256", None)
    view["provenance"] = prov
    return view


def compute_board_sha256(board: dict) -> str:
    return canonical.canonical_sha256(board_for_hash(board))


def _cross_check(board: dict, registry) -> None:
    """跨字段语义校验（schema 表达不了的合同）。全部带键路径 fail-closed。"""
    for i, part in enumerate(board.get("partitions", [])):
        w = part.get("width_prior", {})
        if w.get("w_min", 0) > w.get("w_max", 0):
            raise BoardLoadError("partitions[%d].width_prior" % i,
                                 "w_min %r > w_max %r" % (w.get("w_min"), w.get("w_max")))
    ws = board.get("workspace", {})
    for key in ("x_min", "y_min", "x_max", "y_max"):
        if key not in ws:
            raise BoardLoadError("workspace.%s" % key, "必填字段缺失")
    if ws["x_min"] >= ws["x_max"] or ws["y_min"] >= ws["y_max"]:
        raise BoardLoadError("workspace", "空工作区或负向边界")
    part_ids = [p.get("partition_id") for p in board.get("partitions", [])]
    if len(part_ids) != len(set(part_ids)):
        raise BoardLoadError("partitions", "partition_id 重复")
    known = set(part_ids)
    for i, net in enumerate(board.get("nets", [])):
        for j, ref in enumerate(net.get("partitions", [])):
            if ref not in known:
                raise BoardLoadError("nets[%d].partitions[%d]" % (i, j),
                                     "指向不存在的分区 %r" % ref)


def load_board(board: dict, schema_filename: str = "board.v1.schema.json") -> dict:
    """校验 + provenance 链复算；返回原 dict（便于链式引用）。失败抛 BoardLoadError/SchemaViolation。"""
    schema_loader.validate(board, schema_loader.load_schema(schema_filename),
                           schema_loader.default_registry(), "")
    _cross_check(board, None)
    prov = board.get("provenance", {})
    recomputed = compute_board_sha256(board)
    if prov.get("board_sha256") != recomputed:
        raise BoardLoadError(
            "provenance.board_sha256",
            "哈希链不复算：声明 %s，重算 %s（canonical 剔除本字段后 sha256）"
            % (prov.get("board_sha256"), recomputed))
    return board


def load_board_file(path: str) -> dict:
    import json
    with open(path, encoding="utf-8") as f:
        return load_board(json.load(f))
