"""Separate, closed snapshot vocabulary. No URLs are fetched by the reader."""
import copy
import json
import re
from datetime import datetime

from .compare import decode_object, MAX_BYTES
from .discovery import bounded_read
from pathlib import Path

ALGORITHM = "lexical-windows-v1"
COMMANDS = ("codex", "claude")
ROLES = ("working", "failing", "unspecified")
SYMPTOMS = ("none", "not_found", "wrong_version", "config_error", "other", "unspecified")
EXTENSIONS = (".com", ".exe", ".bat", ".cmd", ".ps1")
NUMERIC_VERSION = r"[0-9]{1,4}(?:\.[0-9]{1,4}){2}"


def obj(**properties):
    return {"type": "object", "additionalProperties": False,
            "required": list(properties), "properties": properties}


def with_optional(schema, **properties):
    return {**schema, "properties": {**schema["properties"], **properties}}


def enum(*values):
    return {"enum": list(values)}


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def code(kind):
    return {"type": "string", "pattern": "^" + kind + r"_[0-9a-f]{64}$"}


def sequence(item):
    return {"type": "array", "maxItems": 256, "items": item}


STAMP = {"type": "string", "pattern": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"}
STATUS = enum("observed", "missing", "unknown", "limited")
ENVIRONMENT = obj(
    path=obj(status=STATUS, entries=sequence(code("path"))),
    pathext=obj(status=STATUS, entries=sequence(enum(*EXTENSIONS))),
    comspec=obj(status=STATUS, path_code=nullable(code("path"))))
LAUNCHER = obj(status=enum("observed", "unknown"), content_code=nullable(code("launcher")),
               version=nullable({"type": "string", "pattern": "^" + NUMERIC_VERSION + "$"}),
               version_source=enum("none", "bounded_version_probe"))
CANDIDATE = obj(path_code=code("path"), installation_code=code("installation"), kind=enum("native", "npm-native", "npm-js", "unknown"),
                access=enum("checked", "blocked"), node_code=nullable(code("path")), launcher=LAUNCHER)
RESULT = obj(status=enum("success", "failure", "unverified"),
             source=enum("none", "user_report", "controlled_test"), recorded_at=STAMP,
             executed_at=nullable(STAMP), session_match=enum("original", "other", "unknown"))
SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://matchben3-commits.github.io/windows-ai-doctor/schemas/environment-snapshot-1.0.schema.json",
    "title": "Windows AI Doctor environment snapshot 1.0",
    "description": "Structure only; --validate-snapshot also enforces bounds and field relationships. No authenticity assurance.",
    **obj(report_type={"const": "environment_snapshot"}, schema_version={"const": "snapshot-1.0"},
          captured_at=STAMP, command=enum(*COMMANDS), session_role=enum(*ROLES), symptom=enum(*SYMPTOMS),
          algorithm={"type": "string", "pattern": r"^lexical-windows-v[0-9]{1,4}$"},
          scope=obj(code=code("scope"), key_status=enum("available")),
          context=obj(shell=enum("powershell", "cmd", "git_bash", "unknown"),
                      elevated=nullable({"type": "boolean"}), elevation_status=enum("observed", "unknown")),
          environment=ENVIRONMENT,
          persistent_environment=obj(user=ENVIRONMENT, machine=ENVIRONMENT),
          resolution=with_optional(obj(status=enum("observed", "unknown"),
                         source=enum("none", "original_runspace_user_supplied"),
                         kind=enum("application", "external_script", "alias", "function", "missing", "unknown"),
                         target=enum(*COMMANDS), preferred_code=nullable(code("path")),
                         candidates=sequence(CANDIDATE), scan_limited={"type": "boolean"}),
                         preferred_directory_code=code("path")),
          observations=obj(tool_execution=enum("not_performed", "version_probe")), command_result=RESULT)
}


def schema_json():
    return json.dumps(SCHEMA, ensure_ascii=False, indent=2) + "\n"


def validate_shape(value, schema):
    """Evaluate exactly our internal schema vocabulary; never an imported schema."""
    if "anyOf" in schema:
        return any(validate_shape(value, sub) for sub in schema["anyOf"])
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        return False
    if "enum" in schema and not any(type(value) is type(v) and value == v for v in schema["enum"]):
        return False
    kind = schema.get("type")
    if kind is None:
        return True
    if kind == "null":
        return value is None
    if kind == "boolean":
        return type(value) is bool
    if kind == "string":
        return isinstance(value, str) and ("pattern" not in schema or re.fullmatch(schema["pattern"], value) is not None)
    if kind == "array":
        return isinstance(value, list) and len(value) <= schema["maxItems"] and all(validate_shape(v, schema["items"]) for v in value)
    if kind == "object":
        properties = schema["properties"]
        return (isinstance(value, dict) and set(schema["required"]) <= value.keys() <= properties.keys()
                and all(validate_shape(v, properties[k]) for k, v in value.items()))
    raise RuntimeError("internal_schema")


def validate_snapshot(value):
    if not validate_shape(value, SCHEMA):
        raise ValueError("invalid_snapshot")
    # Dates, null/status relationships and result provenance are stricter than
    # the public structural schema. Validation never authenticates these labels.
    for stamp in (value["captured_at"], value["command_result"]["recorded_at"], value["command_result"]["executed_at"]):
        if stamp is not None:
            datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    result = value["command_result"]
    if result["source"] == "none":
        if (result["status"], result["executed_at"], result["session_match"]) != ("unverified", None, "unknown"):
            raise ValueError("invalid_result")
    elif result["status"] == "unverified" or (result["source"] == "controlled_test" and result["executed_at"] is None):
        raise ValueError("invalid_result")
    context, resolution = value["context"], value["resolution"]
    if (context["elevated"] is None) != (context["elevation_status"] == "unknown"):
        raise ValueError("invalid_context")
    if resolution["target"] != value["command"]:
        raise ValueError("invalid_resolution")
    if resolution["source"] == "none" and (resolution["status"], resolution["kind"], resolution["preferred_code"]) != ("unknown", "unknown", None):
        raise ValueError("invalid_resolution")
    if resolution["status"] == "unknown" and (resolution["kind"] != "unknown" or resolution["preferred_code"] is not None):
        raise ValueError("invalid_resolution")
    if resolution["kind"] in ("application", "external_script") and resolution["preferred_code"] is None:
        raise ValueError("invalid_resolution")
    if resolution["kind"] in ("alias", "function", "missing", "unknown") and resolution["preferred_code"] is not None:
        raise ValueError("invalid_resolution")
    if "preferred_directory_code" in resolution and resolution["preferred_code"] is None:
        raise ValueError("invalid_resolution")
    version_count = 0
    for candidate in resolution["candidates"]:
        launcher = candidate["launcher"]
        if (launcher["status"] == "observed") != (launcher["content_code"] is not None):
            raise ValueError("invalid_launcher")
        if candidate["kind"] == "unknown" and launcher["content_code"] is not None:
            raise ValueError("invalid_launcher")
        if (launcher["version"] is None) != (launcher["version_source"] == "none"):
            raise ValueError("invalid_version_source")
        if launcher["version"] is not None:
            version_count += 1
            if (version_count > 1 or candidate["kind"] == "unknown" or candidate["access"] != "checked"
                    or candidate["path_code"] != resolution["preferred_code"]
                    or value["observations"]["tool_execution"] != "version_probe"):
                raise ValueError("invalid_version_observation")
    for layer in (value["environment"], *value["persistent_environment"].values()):
        for name in ("path", "pathext"):
            if layer[name]["status"] in ("unknown", "missing") and layer[name]["entries"]:
                raise ValueError("invalid_environment")
        if (layer["comspec"]["status"] == "observed") != (layer["comspec"]["path_code"] is not None):
            raise ValueError("invalid_environment")
    return copy.deepcopy(value)


def load_snapshot(path):
    return validate_snapshot(decode_object(bounded_read(Path(path).absolute(), MAX_BYTES)))
