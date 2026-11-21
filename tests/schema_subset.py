"""Test-only evaluator for the emitted JSON Schema vocabulary; no runtime dependency.

Unknown assertion keywords fail loudly. Integer follows JSON Schema mathematical
semantics (1.0 is integral; bool is not a number), rather than Python type identity.
"""
import math

ANNOTATIONS = {"$schema", "$id", "$defs", "title", "description"}
ASSERTIONS = {"$ref", "type", "required", "properties", "additionalProperties", "const", "enum",
              "items", "maxItems", "minimum", "maximum", "if", "then"}


def same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    return a == b


def accepts(schema, value, root=None, visited=None):
    if root is None:
        root = schema
    if isinstance(schema, bool):
        return schema
    if not isinstance(schema, dict):
        raise AssertionError("unsupported schema shape")
    for keyword in schema:
        if keyword not in ANNOTATIONS | ASSERTIONS and not keyword.startswith("x-"):
            raise AssertionError("unsupported schema keyword: " + keyword)
        if visited is not None:
            visited.add(keyword)
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise AssertionError("external reference")
        target = root
        for token in ref[2:].split("/"):
            target = target[token.replace("~1", "/").replace("~0", "~")]
        if not accepts(target, value, root, visited):
            return False
    if "type" in schema:
        number = type(value) in (int, float) and math.isfinite(value)
        types = {"object": isinstance(value, dict), "array": isinstance(value, list),
                 "string": isinstance(value, str), "boolean": type(value) is bool,
                 "integer": number and int(value) == value, "number": number, "null": value is None}
        if schema["type"] not in types:
            raise AssertionError("unsupported schema type")
        if not types[schema["type"]]:
            return False
    if "const" in schema and not same(value, schema["const"]):
        return False
    if "enum" in schema and not any(same(value, candidate) for candidate in schema["enum"]):
        return False
    if isinstance(value, dict):
        if any(key not in value for key in schema.get("required", [])):
            return False
        properties = schema.get("properties", {})
        for key, child in value.items():
            constraint = properties.get(key, schema.get("additionalProperties", True))
            if not accepts(constraint, child, root, visited):
                return False
    if isinstance(value, list):
        if len(value) > schema.get("maxItems", len(value)):
            return False
        if "items" in schema and not all(accepts(schema["items"], child, root, visited) for child in value):
            return False
    if type(value) in (int, float):
        if "minimum" in schema and value < schema["minimum"]:
            return False
        if "maximum" in schema and value > schema["maximum"]:
            return False
    if "if" in schema and accepts(schema["if"], value, root, visited) and "then" in schema:
        if not accepts(schema["then"], value, root, visited):
            return False
    return True
