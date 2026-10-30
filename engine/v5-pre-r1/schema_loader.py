# -*- coding: utf-8 -*-
"""fail-closed JSON 校验器（stdlib 自写最小实现，任务书 §3.1/P0）。

不支持 UNRESOLVED 引用静默通过：$ref 跨文件引用按注册表解析，解析失败即报错。
非法样例必须报出具体键路径（P0 门），不许默认值静默补齐。
"""
import json
import os
import re

_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas")


class SchemaViolation(ValueError):
    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


class SchemaResolutionError(ValueError):
    pass


def _type_ok(value, expected):
    checks = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
    }
    if isinstance(expected, list):
        return any(_type_ok(value, e) for e in expected)
    if expected in checks:
        return checks[expected](value)
    raise SchemaResolutionError("未知类型约束: %r" % (expected,))


def _resolve_ref(ref, registry, root):
    if ref.startswith("#"):
        if not root:
            raise SchemaResolutionError("就地 $ref 缺根文档: %s" % ref)
        schema = root
        frag = ref[1:]
        if frag:
            for part in frag.lstrip("/").split("/"):
                schema = schema[part]
        return schema
    file_part, _, frag = ref.partition("#")
    fname = os.path.basename(file_part)
    if fname not in registry:
        raise SchemaResolutionError("跨文件 $ref 无法解析: %s" % ref)
    with open(registry[fname], encoding="utf-8") as f:
        doc = json.load(f)
    schema = doc
    if frag:
        for part in frag.lstrip("/").split("/"):
            schema = schema[part]
    return schema


def validate(value, schema, registry=None, path="", _root=None):
    """递归校验；首个违例抛 SchemaViolation（带键路径）。registry: {文件名: 绝对路径}。"""
    registry = registry or {}
    if _root is None:
        _root = schema
    if "$ref" in schema:
        target = _resolve_ref(schema["$ref"], registry, _root)
        merged = {k: v for k, v in schema.items() if k not in ("$ref",)}
        if isinstance(target, dict):
            merged = {**target, **merged}
        return validate(value, merged, registry, path, _root=_root)
    if "const" in schema and value != schema["const"]:
        raise SchemaViolation(path, "const 不符: 期望 %r，得到 %r" % (schema["const"], value))
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaViolation(path, "枚举外值 %r（允许 %r）" % (value, schema["enum"]))
    if "type" in schema and not _type_ok(value, schema["type"]):
        raise SchemaViolation(path, "类型不符: 期望 %s，得到 %s" % (schema["type"], type(value).__name__))
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise SchemaViolation(path, "长度 %d < minLength %d" % (len(value), schema["minLength"]))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise SchemaViolation(path, "不匹配 pattern %s" % schema["pattern"])
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise SchemaViolation(path, "%r < minimum %r" % (value, schema["minimum"]))
        if "maximum" in schema and value > schema["maximum"]:
            raise SchemaViolation(path, "%r > maximum %r" % (value, schema["maximum"]))
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise SchemaViolation(path, "项数 %d < minItems %d" % (len(value), schema["minItems"]))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise SchemaViolation(path, "项数 %d > maxItems %d" % (len(value), schema["maxItems"]))
        if "items" in schema:
            for i, item in enumerate(value):
                validate(item, schema["items"], registry, "%s[%d]" % (path, i), _root=_root)
    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                raise SchemaViolation(_join(path, req), "必填字段缺失")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    raise SchemaViolation(_join(path, key), "additionalProperties 禁止的额外字段")
        for key, sub in props.items():
            if key in value:
                validate(value[key], sub, registry, _join(path, key), _root=_root)
    return value


def _join(path, key):
    return "%s.%s" % (path, key) if path else key


def load_schema(filename):
    path = os.path.join(_SCHEMA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def default_registry():
    """schemas/ 目录三份 schema 的跨文件 $ref 注册表。"""
    return {name: os.path.join(_SCHEMA_DIR, name)
            for name in os.listdir(_SCHEMA_DIR) if name.endswith(".schema.json")}


def validate_file(value, schema_filename):
    return validate(value, load_schema(schema_filename), default_registry(), "")
