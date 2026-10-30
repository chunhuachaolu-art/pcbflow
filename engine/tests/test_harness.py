# -*- coding: utf-8 -*-
"""v5.harness 单测（席位 harness 库化；P3 交付规格）：

- prepare_pkg 落盘合规（tmp_path + monkeypatch sidecar.ALLOWED_ROOTS）：
  盲包过 schema、sidecar provenance 头齐、包元数据带 seat/pkg_sha256；
- prepare_multimodal：SVG 视图与文本包同目录配对、视图文件名进包元数据；
- ingest 三件套全绿路径（tmp run 目录：raw+output 一致+meta）与破坏用例
  （output 与 raw 不一致 / 缺 meta / meta 非法 JSON / seat 非法 / pkg_sha256
  对账失败 / raw 代码块非唯一 / A3 合同外通道 / 通道枚举与结构坏）全部
  fail-closed 且错误带 run 目录路径；
- 五通道校验：缺通道不报错（按 pkg.output_contract 校验在场者）、坏枚举/坏
  结构报键路径；
- demo-01 真实板只读冒烟：prepare_pkg → 手工伪造合规三件套 → ingest 绿；
- A8/R46 红线：两个新模块源码零网络调用痕迹。

gran_entry / v2_board / make_conflicts 为 tests/test_pkg.py 同模板的内联镜像
（P3 并行开发期避免跨测试模块耦合；语义零偏离）。
"""
import hashlib
import json
import os

import pytest

from fixtures_v2 import build_v2_board
from v5 import canonical, sidecar
from v5 import view as view_mod
from v5.board import compute_board_sha256
from v5.harness import (HarnessError, ingest_run, pkg_sha256, prepare_multimodal,
                        prepare_pkg, validate_ordinal_channels)
from v5.partition import build_partition_artifact
from v5.pkg import build_pkg
from v5.schema_loader import validate_file

V5_DIR = os.path.dirname(sidecar.__file__)
DEMO01_PATH = os.path.join(V5_DIR, "..", "boards", "d",
                           "demo-01-v2-corridor.board.v1.json")
FENCE = "`" * 3


# --------------------------------------------------------------- 夹具（test_pkg 镜像）

def gran_entry(min_gap_mm=2.0, principle_id="P-PART-GRAN-HARNTEST"):
    """分区聚类粒度先验条目（L1 必需；test_pkg 同模板）。"""
    entry = {
        "principle_id": principle_id,
        "name": "分区聚类粒度先验",
        "intent": {"protects": "走廊通行容量", "sacrifices": "细粒度自由"},
        "scope": "partitioning",
        "protected_resources": ["corridor_capacity"],
        "target_freedom": "corridor",
        "priority": 50,
        "hard_or_soft": "soft",
        "overridable": True,
        "compiled_rule": {"kind": "partition_granularity",
                          "params": {"min_gap_mm": min_gap_mm,
                                     "group_types": ["BUS", "DIFF"]}},
        "enforcement": "generation",
        "conflict_policy": {"conflicts_with": [], "yields_to": []},
        "evidence_refs": ["V5.0-DEV-TASKBOOK §4 L1"],
        "version": "1.0.0",
    }
    entry["source_hash"] = canonical.canonical_sha256(entry)
    return entry


def v2_board():
    """V2 板 + 粒度先验（板内容变更后链式重算 board_sha256）。"""
    board = build_v2_board()
    board["principle_registry"] = [gran_entry()]
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


def make_conflicts(board):
    """V2 场景冲突清单（test_pkg 同模板）。"""
    conflicts = [
        {"conflict_id": "CF-001", "kind": "straight_zone_cross",
         "subjects": ["P2"], "zone": "ANA", "layer": None,
         "basis": "P2 直线路径穿过 ANA", "arithmetic": None,
         "severity": "blocking"},
        {"conflict_id": "CF-002", "kind": "capacity_infeasible",
         "subjects": ["P3"], "zone": "C1", "layer": None,
         "basis": "P3 若留 F.Cu 过 C1，占用合计将超单层剩余容量",
         "arithmetic": "3.3+0.5+0.2=4.0 > 4.3", "severity": "blocking"},
        {"conflict_id": "CF-003", "kind": "capacity_infeasible",
         "subjects": ["P5"], "zone": "C1", "layer": None,
         "basis": "P5 若留 F.Cu 过 C1，占用合计将超单层剩余容量",
         "arithmetic": "3.3+0.5+0.2+0.2+0.5=4.7 > 4.3", "severity": "blocking"},
        {"conflict_id": "CF-004", "kind": "straight_zone_cross",
         "subjects": ["P5"], "zone": "K2", "layer": None,
         "basis": "P5 直线路径穿过 K2", "arithmetic": None,
         "severity": "advisory"},
        {"conflict_id": "CF-005", "kind": "bottleneck",
         "subjects": ["P1"], "zone": None, "layer": None,
         "basis": "P1 在 x∈[8,10] 瓶颈段可用宽度低于计划宽度",
         "arithmetic": None, "severity": "blocking"},
    ]
    return {"artifact": "v5.conflicts.v1",
            "board_id": board["board_id"],
            "board_sha256": board["provenance"]["board_sha256"],
            "conflicts": conflicts}


def prepared(tmp_path, monkeypatch, seat="seat_a_diagnostic"):
    """制备四件套：（板, L1 工件, 冲突工件, 内存包, 制备记录），包已落 tmp_path。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = v2_board()
    part = build_partition_artifact(board)
    conf = make_conflicts(board)
    pkg = build_pkg(board, part, conf)
    rec = prepare_pkg(board, part, conf, seat, str(tmp_path))
    return board, part, conf, pkg, rec


def valid_output(part):
    """一份五通道全在场且形状合规的序数 json（routing_order 取自 L1 工件）。"""
    return {
        "ranked_options": [{"label": "方案甲：全 F.Cu"},
                           {"label": "方案乙：P3 换层 B.Cu"}],
        "ranked_combos": [{"P3": "留F.Cu过C1|换层B.Cu|换层In1",
                           "P5": "留F.Cu过C1|换层B.Cu|换层In1",
                           "label": "组合甲"}],
        "routing_order": [e["partition_id"] for e in part["partitions"]],
        "defect_scan": [{"subject": "P8", "rule": "R1",
                         "note": "计划宽 0.5 低于 R1 下限 0.8"}],
        "principle_objection": "",
    }


def write_run(run_dir, payload, seat, pkg_sha, *, raw_text=None,
              output_text=None, meta_text=None, write_meta=True):
    """在 run 目录伪造三件套（默认：raw 含恰一个与 payload 一致的 json 代码块）。"""
    os.makedirs(run_dir, exist_ok=True)
    payload_text = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True)
    raw = raw_text if raw_text is not None else (
        "# 席位回复原文\n\n结论：\n\n" + FENCE + "json\n" + payload_text + "\n"
        + FENCE + "\n")
    with open(os.path.join(run_dir, "response-raw.md"), "wb") as f:
        f.write(raw.encode("utf-8"))
    out = output_text if output_text is not None else payload_text
    with open(os.path.join(run_dir, "output.json"), "wb") as f:
        f.write(out.encode("utf-8"))
    if write_meta:
        meta = meta_text if meta_text is not None else json.dumps(
            {"seat": seat, "pkg_sha256": pkg_sha}, ensure_ascii=False)
        with open(os.path.join(run_dir, "meta.json"), "wb") as f:
            f.write(meta.encode("utf-8"))
    return raw.encode("utf-8")


# --------------------------------------------------------------- prepare_pkg

def test_prepare_pkg_writes_compliant_pkg_and_meta(tmp_path, monkeypatch):
    """盲包落盘过 schema + sidecar 头齐；包元数据记录 seat/pkg_sha256/文件名。"""
    board, _part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    assert rec["seat"] == "seat_a_diagnostic"
    assert rec["board_id"] == board["board_id"]
    assert set(rec) == {"seat", "board_id", "board_sha256", "pkg_sha256",
                        "pkg_file", "multimodal_view"}
    # 盲包：注入 provenance 后仍过 schema
    pkg_path = os.path.join(str(tmp_path), rec["pkg_file"])
    with open(pkg_path, encoding="utf-8") as f:
        doc = json.load(f)
    assert doc["schema_version"] == "v5.pkg.v1"
    assert validate_file(doc, "pkg.v1.schema.json") == doc
    assert doc["provenance"] == {"generator": "v5.pkg", "generator_version": "0.1.0",
                                 "board_sha256": pkg["board_sha256"]}
    # 包元数据 sidecar：seat 仅作元数据记录（v5.pkg.v1 包体 schema 冻结，不进包体）
    meta_path = os.path.join(str(tmp_path),
                             board["board_id"] + ".harness-meta-seat_a_diagnostic.json")
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["seat"] == "seat_a_diagnostic"
    assert meta["pkg_sha256"] == rec["pkg_sha256"]
    assert meta["multimodal_view"] is None
    assert meta["provenance"]["generator"] == "v5.harness"
    # sidecar 卫生（§3.5）：三件产物全在允许根下且 json 头齐
    assert sidecar.check_tree(str(tmp_path)) == []


def test_prepare_pkg_invalid_seat_rejected(tmp_path, monkeypatch):
    """seat 枚举外值 fail-closed（写盘之前爆，零半成品）。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = v2_board()
    part = build_partition_artifact(board)
    conf = make_conflicts(board)
    with pytest.raises(ValueError) as ei:
        prepare_pkg(board, part, conf, "seat_z", str(tmp_path))
    assert "seat" in str(ei.value)
    assert list(tmp_path.iterdir()) == []


def test_pkg_sha256_stable_between_memory_and_written(tmp_path, monkeypatch):
    """pkg_sha256 口径：内存包与落盘回读件（含注入 provenance）同 hash；双跑字节等。"""
    _board, _part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    assert rec["pkg_sha256"] == pkg_sha256(pkg)
    pkg_path = os.path.join(str(tmp_path), rec["pkg_file"])
    with open(pkg_path, encoding="utf-8") as f:
        doc = json.load(f)
    assert pkg_sha256(doc) == rec["pkg_sha256"]
    # 双跑字节等（§3.4）
    from v5.pkg import write_pkg
    again = os.path.join(str(tmp_path), "again.pkg.json")
    write_pkg(pkg, again)
    with open(pkg_path, "rb") as f1, open(again, "rb") as f2:
        assert f1.read() == f2.read()


# --------------------------------------------------------------- prepare_multimodal

def test_prepare_multimodal_pairs_view_in_same_dir(tmp_path, monkeypatch):
    """图文双输入包（§3.4/D2）：SVG 视图与文本包同目录配对、文件名进包元数据。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    board = v2_board()
    part = build_partition_artifact(board)
    conf = make_conflicts(board)
    rec = prepare_multimodal(board, part, conf, "shadow_b", str(tmp_path))
    assert rec["multimodal_view"] == {"stage": "l1", "mode": "all",
                                      "file": board["board_id"]
                                      + ".l1-view-shadow_b.svg"}
    view_path = os.path.join(str(tmp_path), rec["multimodal_view"]["file"])
    with open(view_path, encoding="utf-8") as f:
        head = f.read(64)
    assert head.startswith("<!-- v5.view provenance")
    # 同目录配对：盲包/视图/包元数据同一目录
    assert os.path.dirname(view_path) == str(tmp_path)
    assert rec["pkg_file"] in os.listdir(str(tmp_path))
    # 视图渲染确定性（v5.view 同输入双跑字节等）
    assert view_mod.render_l1_view(board, part, "all") == \
        view_mod.render_l1_view(board, part, "all")
    assert sidecar.check_tree(str(tmp_path)) == []


# --------------------------------------------------------------- ingest 全绿路径

def test_ingest_green_path(tmp_path, monkeypatch):
    """全绿：prepare_pkg → 伪造合规三件套 → ingest 产物五键且值正确、只读零改动。"""
    board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    payload = valid_output(part)
    run_dir = str(tmp_path / "run-seat-a")
    raw_bytes = write_run(run_dir, payload, "seat_a_diagnostic", rec["pkg_sha256"],
                          meta_text=json.dumps(
                              {"seat": "seat_a_diagnostic",
                               "pkg_sha256": rec["pkg_sha256"],
                               "board_sha256": board["provenance"]["board_sha256"]},
                              ensure_ascii=False))
    before = open(os.path.join(run_dir, "response-raw.md"), "rb").read()
    result = ingest_run(run_dir, pkg)
    assert set(result) == {"seat", "board_sha256", "pkg_sha256", "output",
                           "raw_sha256"}
    assert result["seat"] == "seat_a_diagnostic"
    assert result["board_sha256"] == board["provenance"]["board_sha256"]
    assert result["pkg_sha256"] == rec["pkg_sha256"]
    assert result["output"] == payload
    assert result["raw_sha256"] == hashlib.sha256(raw_bytes).hexdigest()
    # 三件套逐字不改（ingest 只读）
    assert open(os.path.join(run_dir, "response-raw.md"), "rb").read() == before


def test_ingest_accepts_written_pkg_form(tmp_path, monkeypatch):
    """ingest 也收落盘回读件形态的包（pkg_sha256 剔除注入 provenance 后同 hash）。"""
    _board, part, _conf, _pkg, rec = prepared(tmp_path, monkeypatch)
    run_dir = str(tmp_path / "run")
    write_run(run_dir, valid_output(part), "seat_a_diagnostic", rec["pkg_sha256"])
    with open(os.path.join(str(tmp_path), rec["pkg_file"]), encoding="utf-8") as f:
        doc = json.load(f)
    result = ingest_run(run_dir, doc)
    assert result["pkg_sha256"] == rec["pkg_sha256"]


# --------------------------------------------------------------- ingest 破坏用例

def test_ingest_output_mismatch_reports_key_path_and_run_dir(tmp_path, monkeypatch):
    """output.json 与 raw 内 json 代码块不等 → fail-closed 报首个差异键路径+run 目录。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    payload = valid_output(part)
    payload["defect_scan"][0]["note"] = "被会话改过的注"
    run_dir = str(tmp_path / "run")
    write_run(run_dir, valid_output(part), "seat_a_diagnostic", rec["pkg_sha256"],
              output_text=json.dumps(payload, ensure_ascii=False, indent=1,
                                     sort_keys=True))
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert run_dir in str(ei.value)
    assert "defect_scan[0].note" in str(ei.value)


def test_ingest_missing_meta_fail_closed(tmp_path, monkeypatch):
    """缺 meta.json → fail-closed 带路径。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    run_dir = str(tmp_path / "run")
    write_run(run_dir, valid_output(part), "seat_a_diagnostic", rec["pkg_sha256"],
              write_meta=False)
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert run_dir in str(ei.value) and "meta.json" in str(ei.value)


def test_ingest_meta_invalid_json_fail_closed(tmp_path, monkeypatch):
    """meta.json 非法 JSON → fail-closed 带路径。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    run_dir = str(tmp_path / "run")
    write_run(run_dir, valid_output(part), "seat_a_diagnostic", rec["pkg_sha256"],
              meta_text="{oops 不是 json")
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert "meta.json" in str(ei.value)


def test_ingest_meta_bad_seat_fail_closed(tmp_path, monkeypatch):
    """meta.seat 枚举外 → fail-closed。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    run_dir = str(tmp_path / "run")
    write_run(run_dir, valid_output(part), "seat_z", rec["pkg_sha256"])
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert "meta.seat" in str(ei.value)


def test_ingest_meta_pkg_sha_mismatch_fail_closed(tmp_path, monkeypatch):
    """meta.pkg_sha256 与包对账失败 → fail-closed（§3.1 按 hash 对账）。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    run_dir = str(tmp_path / "run")
    write_run(run_dir, valid_output(part), "seat_a_diagnostic", "0" * 64)
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert "meta.pkg_sha256" in str(ei.value) and "对账" in str(ei.value)


@pytest.mark.parametrize("raw", [
    "# 纯文本\n没有任何代码块\n",                                   # 零块
    "# 两个代码块\n\n```json\n{}\n```\n\n尾注\n\n```json\n{}\n```\n",  # 双块
])
def test_ingest_raw_block_count_fail_closed(tmp_path, monkeypatch, raw):
    """raw 内 json 代码块须恰 1 个：零块/双块 → fail-closed。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    run_dir = str(tmp_path / "run")
    write_run(run_dir, valid_output(part), "seat_a_diagnostic", rec["pkg_sha256"],
              raw_text=raw)
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert "response-raw.md" in str(ei.value)


# --------------------------------------------------------------- A3 五通道校验

def test_ingest_undeclared_channel_fail_closed(tmp_path, monkeypatch):
    """A3 合同外通道（V2 旧键 route_order）→ fail-closed 报通道名。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    payload = valid_output(part)
    payload["route_order"] = ["P1"]  # 旧代形态，A3 五通道不承旧键
    run_dir = str(tmp_path / "run")
    write_run(run_dir, payload, "seat_a_diagnostic", rec["pkg_sha256"])
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert "route_order" in str(ei.value)


def test_ingest_missing_channels_ok(tmp_path, monkeypatch):
    """不要求五通道全在场：只交 routing_order+defect_scan 也全绿。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    payload = {"routing_order": [e["partition_id"] for e in part["partitions"]],
               "defect_scan": [{"subject": "P1", "rule": "自相矛盾",
                                "note": "行注与宽度先验矛盾"}]}
    run_dir = str(tmp_path / "run")
    write_run(run_dir, payload, "seat_a_diagnostic", rec["pkg_sha256"])
    result = ingest_run(run_dir, pkg)
    assert result["output"] == payload


def test_ingest_channel_bad_enum_reports_key_path(tmp_path, monkeypatch):
    """defect_scan.rule 枚举外值（R9）→ fail-closed 报键路径。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    payload = valid_output(part)
    payload["defect_scan"][0]["rule"] = "R9"
    run_dir = str(tmp_path / "run")
    write_run(run_dir, payload, "seat_a_diagnostic", rec["pkg_sha256"])
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert "defect_scan[0].rule" in str(ei.value)


def test_ingest_channel_bad_structure_reports_key_path(tmp_path, monkeypatch):
    """通道结构坏（ranked_options 条目缺 label）→ fail-closed 报键路径。"""
    _board, part, _conf, pkg, rec = prepared(tmp_path, monkeypatch)
    payload = valid_output(part)
    payload["ranked_options"] = [{"name": "没有 label"}]
    run_dir = str(tmp_path / "run")
    write_run(run_dir, payload, "seat_a_diagnostic", rec["pkg_sha256"])
    with pytest.raises(HarnessError) as ei:
        ingest_run(run_dir, pkg)
    assert "ranked_options[0]" in str(ei.value)


def test_validate_channels_direct_fail_closed_paths():
    """校验器直测：包未声明通道合同 / 输出非对象 / 声明未知通道形状 → fail-closed。"""
    with pytest.raises(HarnessError) as ei:
        validate_ordinal_channels({}, {}, "run-x")
    assert "pkg.output_contract.channels" in str(ei.value)
    pkg = {"output_contract": {"channels": {"routing_order": []}}}
    with pytest.raises(HarnessError) as ei:
        validate_ordinal_channels(["不是对象"], pkg, "run-x")
    assert "须为对象" in str(ei.value)
    with pytest.raises(HarnessError) as ei:
        validate_ordinal_channels({"future_channel": 1},
                                  {"output_contract": {"channels":
                                                       {"future_channel": True}}},
                                  "run-x")
    assert "未知通道形状" in str(ei.value)


# --------------------------------------------------------------- demo-01 冒烟

def test_demo01_readonly_smoke_full_cycle(tmp_path, monkeypatch):
    """真实板只读冒烟：demo-01 → prepare_pkg → 伪造合规三件套 → ingest 绿
    （ingest 收落盘回读件形态的包）。"""
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    with open(DEMO01_PATH, encoding="utf-8") as f:
        board = json.load(f)
    # 板哈希链自洽（只读复算，不写盘）
    assert compute_board_sha256(board) == board["provenance"]["board_sha256"]
    part = build_partition_artifact(board)
    conf = make_conflicts(board)
    pkg = build_pkg(board, part, conf)
    rec = prepare_pkg(board, part, conf, "seat_c_review", str(tmp_path))
    assert rec["board_id"] == "demo-01-v2-corridor"
    payload = valid_output(part)
    run_dir = str(tmp_path / "run-seat-c")
    write_run(run_dir, payload, "seat_c_review", rec["pkg_sha256"])
    with open(os.path.join(str(tmp_path), rec["pkg_file"]), encoding="utf-8") as f:
        pkg_doc = json.load(f)
    result = ingest_run(run_dir, pkg_doc)
    assert result["seat"] == "seat_c_review"
    assert result["board_sha256"] == board["provenance"]["board_sha256"]
    assert result["output"] == payload


# --------------------------------------------------------------- A8/R46 红线

@pytest.mark.parametrize("fname", ["harness.py", "voting.py"])
def test_no_network_calls_in_new_modules(fname):
    """零网络调用（A8/R46）：新模块源码不含任何网络客户端/API 痕迹。"""
    with open(os.path.join(V5_DIR, fname), encoding="utf-8") as f:
        src = f.read()
    for bad in ("socket", "urllib", "urlopen", "http.client", "requests",
                "httpx", "aiohttp", "chat/completions"):
        assert bad not in src, (fname, bad)
