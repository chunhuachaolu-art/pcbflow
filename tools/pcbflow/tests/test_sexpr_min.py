"""最小 s-expr 读取器：KiCad netlist 片段解析。"""

import pytest

from pcbflow import sexpr_min

SAMPLE = """(export (version "E")
  (nets
    (net (code "1") (name "GND")
      (node (ref "C1") (pin "1"))
      (node (ref "J1") (pin "1")))
    (net (code "2") (name "USB_DP")
      (node (ref "U1") (pin "PA12")))))
"""


def test_parse_structure():
    top = sexpr_min.parse(SAMPLE)
    assert len(top) == 1 and top[0][0] == "export"
    export = top[0]
    nets = sexpr_min.find_all(export, "net")
    assert len(nets) == 2
    gnd = nets[0]
    assert sexpr_min.get_str(sexpr_min.find_first(gnd, "name")) == "GND"
    nodes = sexpr_min.find_all(gnd, "node")
    assert len(nodes) == 2
    assert sexpr_min.get_str(sexpr_min.find_first(nodes[1], "ref")) == "J1"


def test_parse_escaped_quotes():
    top = sexpr_min.parse('(net (name "a\\"b"))')
    assert sexpr_min.get_str(sexpr_min.find_first(top[0], "name")) == 'a"b'


def test_unbalanced_raises():
    with pytest.raises(sexpr_min.SexprError):
        sexpr_min.parse("(a (b)")
    with pytest.raises(sexpr_min.SexprError):
        sexpr_min.parse(")")


def test_capability_declared():
    assert sexpr_min.FIDELITY == "text_structure_only"
    assert sexpr_min.FALLBACK_REASON  # fallback 必须有原因声明
