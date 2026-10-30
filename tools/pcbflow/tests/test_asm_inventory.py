"""TD9 湿区 inventory 测试：合成特征抽取/分类/schema 正负用例 + 真实冒烟。

- 合成用例走内存（scan_text）与 tmp_path（build_inventory 分类逻辑：
  临时子目录命名为 scripts/ 与 out/revc-asm/ 验证两类 classification）；
- 真实冒烟只读扫描 scripts/（目录缺失整测 skip，不改历史产物）。
"""

import copy
import os
import re

import pytest

from pcbflow import asm_inventory, envelope, hashing

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# ---- 合成样本（内存字符串；不落盘、不 exec） -------------------------------

SYN_SUBPROCESS_WRITER = '''\
"""合成样本：子进程 + 写盘（historical 湿区风格）。

第二段不得进入 doc_head。
"""
import subprocess

subprocess.run(["kicad-cli", "pcb", "export", "pos"])
os.system("echo hi")
with open("out/legacy.json", "w", encoding="utf-8") as f:
    f.write("{}")
print("done")
'''

SYN_STDOUT_GENERATOR = '''#!/usr/bin/env python3
"""合成样本：纯 stdout 生成器（零写盘）。"""
import sys


def main():
    print("hello")
    sys.stdout.write("world")
'''

SYN_BOARD_READER = '''"""合成样本：板文本触达 + stdin 摄入。"""
import sys

BOARD = "board.kicad_pcb"
for line in sys.stdin:
    print(line)
'''


# ---- scan_text：特征抽取（纯内存） -----------------------------------------

def test_scan_text_subprocess_writer_features():
    scanned = asm_inventory.scan_text(SYN_SUBPROCESS_WRITER)
    caps = scanned["capabilities"]
    assert caps["subprocess_use"] is True
    assert any("legacy.json" in e for e in caps["file_write_patterns"])
    assert len(caps["file_write_patterns"]) <= 3
    assert caps["stdout_only_writes"] is False      # 有写盘证据 ⇒ 非 stdout-only
    assert scanned["doc_head"] == "合成样本：子进程 + 写盘（historical 湿区风格）。"
    assert scanned["line_count"] == len(SYN_SUBPROCESS_WRITER.splitlines())


def test_scan_text_stdout_generator_features():
    caps = asm_inventory.scan_text(SYN_STDOUT_GENERATOR)["capabilities"]
    assert caps["subprocess_use"] is False
    assert caps["file_write_patterns"] == []
    assert caps["stdout_only_writes"] is True
    assert caps["stdin_generator"] is False
    assert caps["board_text_touch"] is False


def test_scan_text_board_reader_features():
    caps = asm_inventory.scan_text(SYN_BOARD_READER)["capabilities"]
    assert caps["board_text_touch"] is True
    assert caps["stdin_generator"] is True
    assert caps["stdout_only_writes"] is True        # 零写盘 + print
    assert caps["subprocess_use"] is False


def test_scan_text_docstring_extraction_edges():
    # docstring 开引号在第 2 行（shebang 之后）仍可提取
    scanned = asm_inventory.scan_text(SYN_STDOUT_GENERATOR)
    assert scanned["doc_head"] == "合成样本：纯 stdout 生成器（零写盘）。"
    # 无 docstring
    assert asm_inventory.scan_text("x = 1\n")["doc_head"] is None
    # 开引号晚于前 3 行 → None（合同：前 3 行内）
    late = 'import os\nimport sys\nimport json\n"""太晚"""\n'
    assert asm_inventory.scan_text(late)["doc_head"] is None
    # 闭引号缺失 → None
    unterminated = '"""没有结束\n'
    assert asm_inventory.scan_text(unterminated)["doc_head"] is None


def test_scan_text_host_path_masked_in_artifact_strings():
    """摘录/doc_head 内的盘符绝对路径必须掩码（核心产物卫生）。"""
    text = ('"""样本：路径 C:\\Users\\alice\\board.kicad_pcb。"""\n'
            'dst = open(r"C:\\Users\\alice\\out\\x.dsn", "w")\n')
    scanned = asm_inventory.scan_text(text)
    assert scanned["doc_head"] == "样本：路径 <abs-path>"   # 掩码吞至空白/引号
    assert scanned["capabilities"]["file_write_patterns"]
    for excerpt in scanned["capabilities"]["file_write_patterns"]:
        assert "C:" not in excerpt and "<abs-path>" in excerpt


def test_scan_text_write_excerpt_cap_at_three():
    text = '\n'.join(f'open("f{i}.txt", "w")' for i in range(5))
    caps = asm_inventory.scan_text(text)["capabilities"]
    assert len(caps["file_write_patterns"]) == 3


# ---- build_inventory：合成目录分类 + 顶层结构 --------------------------------

def _build_synthetic(tmp_path):
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts" / "gen.py").write_text(SYN_STDOUT_GENERATOR,
                                                 encoding="utf-8")
    (tmp_path / "out" / "revc-asm" / "fr").mkdir(parents=True, exist_ok=True)
    (tmp_path / "out" / "revc-asm" / "fr" / "probe.py").write_text(
        SYN_SUBPROCESS_WRITER, encoding="utf-8")
    return asm_inventory.build_inventory(pcbflow_root=str(tmp_path),
                                         roots=("out/revc-asm", "scripts"))


def test_build_inventory_classification_and_counts(tmp_path):
    inv = _build_synthetic(tmp_path)
    assert inv["schema_version"] == "3.0"
    assert inv["artifact_kind"] == "asm_inventory"
    assert inv["generated_from_roots"] == ["out/revc-asm", "scripts"]
    assert inv["note"] == asm_inventory.NOTE
    assert [it["script_rel_path"] for it in inv["items"]] == [
        "out/revc-asm/fr/probe.py", "scripts/gen.py"]        # 全局 posix 字典序
    by_path = {it["script_rel_path"]: it for it in inv["items"]}
    assert by_path["scripts/gen.py"]["classification"] == "package_candidate"
    assert (by_path["out/revc-asm/fr/probe.py"]["classification"]
            == "historical_only")
    assert inv["counts"]["total"] == len(inv["items"]) == 2
    assert inv["counts"]["historical_only"] == 1
    assert inv["counts"]["package_candidate"] == 1
    assert inv["counts"]["subprocess_use"] == 1
    assert inv["counts"]["stdout_only_writes"] == 1


def test_build_inventory_item_content(tmp_path):
    inv = _build_synthetic(tmp_path)
    item = next(it for it in inv["items"]
                if it["script_rel_path"] == "scripts/gen.py")
    assert item["sha256"] == hashing.sha256_file(
        str(tmp_path / "scripts" / "gen.py"))
    assert item["line_count"] == len(SYN_STDOUT_GENERATOR.splitlines())
    assert item["capabilities"]["stdout_only_writes"] is True


def test_build_inventory_migration_gate_all_false(tmp_path):
    """红线：全新 inventory 十门恒 False（未评估即未通过）。"""
    inv = _build_synthetic(tmp_path)
    for it in inv["items"]:
        assert len(it["migration_gate"]) == 10
        assert set(it["migration_gate"].values()) == {False}
        assert set(it["migration_gate"]) == set(
            asm_inventory.MIGRATION_GATE_KEYS)


def test_build_inventory_deterministic(tmp_path):
    inv_a = _build_synthetic(tmp_path)
    inv_b = _build_synthetic(tmp_path)
    assert inv_a == inv_b


def test_build_inventory_artifact_hygiene(tmp_path):
    """无禁区键、无主机绝对路径；自身 schema 合法。"""
    inv = _build_synthetic(tmp_path)
    assert envelope.scan_forbidden_core_fields(inv) == []
    assert asm_inventory.validate_inventory(inv) == []


def test_build_inventory_missing_root_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        asm_inventory.build_inventory(pcbflow_root=str(tmp_path),
                                      roots=("out/revc-asm",))


def test_build_inventory_unknown_root_rejected(tmp_path):
    (tmp_path / "misc").mkdir()
    (tmp_path / "misc" / "x.py").write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError):     # 不得给出未知/可迁移分类
        asm_inventory.build_inventory(pcbflow_root=str(tmp_path),
                                      roots=("misc",))


# ---- validate_inventory：正负用例 -------------------------------------------

def test_validate_inventory_synthetic_pass(tmp_path):
    assert asm_inventory.validate_inventory(_build_synthetic(tmp_path)) == []


def _mutations():
    return {
        "schema_version": lambda inv: inv.update(schema_version="2.0"),
        "artifact_kind": lambda inv: inv.update(artifact_kind="other"),
        "extra_top_key": lambda inv: inv.update(generated_at="2026-09-01"),
        "missing_counts": lambda inv: inv.pop("counts"),
        "bad_sha256": lambda inv: inv["items"][0].update(sha256="deadbeef"),
        "bad_classification": lambda inv: inv["items"][0].update(
            classification="migratable"),
        "backslash_path": lambda inv: inv["items"][0].update(
            script_rel_path="scripts\\gen.py"),
        "abs_path": lambda inv: inv["items"][0].update(
            script_rel_path="C:/Users/x/gen.py"),
        "gate_string": lambda inv: inv["items"][0]["migration_gate"].update(
            machine_drc="not_evaluated"),
        "gate_missing": lambda inv: inv["items"][0]["migration_gate"].pop(
            "crash_recovery"),
        "gate_extra": lambda inv: inv["items"][0]["migration_gate"].update(
            auto_promote=True),
        "missing_doc_head": lambda inv: inv["items"][0].pop("doc_head"),
        "caps_extra_key": lambda inv: inv["items"][0]["capabilities"].update(
            network_use=True),
        "caps_type": lambda inv: inv["items"][0]["capabilities"].update(
            subprocess_use="no"),
        "excerpts_overflow": lambda inv: inv["items"][0]["capabilities"].update(
            file_write_patterns=["x"] * 4),
        "negative_count": lambda inv: inv["counts"].update(total=-1),
    }


@pytest.mark.parametrize("name", sorted(_mutations()))
def test_validate_inventory_negative(tmp_path, name):
    inv = _build_synthetic(tmp_path)
    assert asm_inventory.validate_inventory(inv) == []   # 前置：合法基线
    mutated = copy.deepcopy(inv)
    _mutations()[name](mutated)
    errors = asm_inventory.validate_inventory(mutated)
    assert errors, name


def test_validate_inventory_rejects_non_object():
    assert asm_inventory.validate_inventory([]) != []
    assert asm_inventory.validate_inventory(None) != []


# ---- 真实冒烟：roots=("scripts",)（只读；目录缺失 skip） ---------------------

@pytest.mark.skipif(not os.path.isdir(SCRIPTS_DIR),
                    reason="真实 scripts/ 目录不存在")
def test_real_scripts_smoke():
    inv = asm_inventory.build_inventory(pcbflow_root=PROJECT_ROOT,
                                        roots=("scripts",))
    items = inv["items"]
    assert len(items) >= 1
    assert inv["counts"]["total"] == len(items)
    for it in items:
        assert it["script_rel_path"].startswith("scripts/")
        assert "\\" not in it["script_rel_path"]      # 相对 posix
        assert _SHA256_RE.match(it["sha256"])         # 64hex
        assert it["classification"] == "package_candidate"
        assert set(it["migration_gate"].values()) == {False}
    assert inv["counts"]["package_candidate"] == len(items)
    assert asm_inventory.validate_inventory(inv) == []
    assert envelope.scan_forbidden_core_fields(inv) == []
