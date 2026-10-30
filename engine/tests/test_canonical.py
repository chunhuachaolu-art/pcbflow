# -*- coding: utf-8 -*-
import pytest

from v5 import canonical
from v5.canonical import CanonicalError, canonical_json, canonical_roundtrip, canonical_sha256


def test_bytes_deterministic_double_run():
    obj = {"b": 1, "a": [1, 2, {"x": "中文"}]}
    assert canonical_json(obj) == canonical_json(obj)


def test_key_order_fixed_sorted():
    assert canonical_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_compact_separators():
    assert canonical_json({"a": [1, 2]}) == b'{"a":[1,2]}'


def test_unicode_not_escaped():
    assert "中" in canonical_json({"k": "中文"}).decode("utf-8")


def test_no_nan_allowed():
    with pytest.raises(CanonicalError):
        canonical_json({"x": float("nan")})


def test_no_inf_allowed():
    with pytest.raises(CanonicalError):
        canonical_json({"x": float("inf")})


def test_rejects_set():
    with pytest.raises(CanonicalError):
        canonical_json({"x": {1, 2}})


def test_roundtrip_bytes_equal():
    obj = {"z": [1.5, True, None], "a": {"n": 3}}
    data, loaded = canonical_roundtrip(obj)
    assert data == canonical_json(loaded)


def test_float_repr_deterministic():
    vals = [0.1, 1 / 3, 34.85, 42.4, 1e-9, 2 ** 53 + 1.0]
    for v in vals:
        assert canonical_json({"v": v}) == canonical_json({"v": float(str(v))})


def test_sha256_stable():
    obj = {"a": 1}
    assert canonical_sha256(obj) == canonical_sha256(obj)
    assert len(canonical_sha256(obj)) == 64


def test_nested_ordering_deep():
    obj = {"m": {"z": 1, "a": {"y": 2, "b": 3}}, "A": [[3, 2], [1]]}
    text = canonical_text = canonical_json(obj).decode()
    assert text.index('"A"') < text.index('"m"')
    assert text.index('"b"') < text.index('"y"')


def test_empty_containers():
    assert canonical_json({}) == b"{}"
    assert canonical_json([]) == b"[]"
