"""Deterministic structural schema; the bounded reader remains authoritative."""
import json

from .compare import IDS, STATES, MAX_FINDINGS, MAX_BYTES, MAX_DEPTH, MAX_NODES, MAX_INSTALLATION_GROUPS, VERSION_PATTERN


def diagnosis_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/matchben3-commits/windows-ai-doctor/schemas/diagnosis-1.0.schema.json",
        "title": "Windows AI Doctor diagnosis input, schema 1.0",
        "description": (
            "Structural input rules, with unknown properties permitted and ignored. --validate is authoritative. "
            "Passing this schema does not establish health, completeness, trusted origin or machine identity. "
            "The parser additionally rejects oversized/deep inputs, excessive nodes, duplicate JSON keys or finding IDs, "
            "long numeric tokens/strings and non-finite numbers. JSON Schema integer accepts 1.0 and 1e0; "
            "the parser requires an integer JSON token for installation_groups on .path findings. "
            "Non-numeric version values are accepted but excluded from comparison, history and support projections."
        ),
        "type": "object",
        "required": ["schema_version", "findings"],
        "properties": {
            "schema_version": {"const": "1.0"},
            "report_type": {"const": "diagnosis"},
            "findings": {"type": "array", "maxItems": MAX_FINDINGS, "items": {"$ref": "#/$defs/finding"}},
        },
        "additionalProperties": True,
        "$defs": {
            "finding": {
                "type": "object", "required": ["id", "status"],
                "properties": {
                    "id": {"enum": sorted(IDS)},
                    "status": {"enum": list(STATES)},
                    "evidence": {"type": "object", "additionalProperties": True},
                },
                "additionalProperties": True,
                "if": {"properties": {"id": {"enum": sorted(id for id in IDS if id.endswith(".path"))}}, "required": ["id"]},
                "then": {"properties": {"evidence": {"$ref": "#/$defs/path_evidence"}}},
            },
            "path_evidence": {
                "type": "object",
                "properties": {
                    "installation_groups": {"type": "integer", "minimum": 0, "maximum": MAX_INSTALLATION_GROUPS},
                    "scan_limited": {"type": "boolean"},
                },
                "additionalProperties": True,
            },
        },
        "x-parser-limits": {
            "max_bytes": MAX_BYTES, "max_depth": MAX_DEPTH, "max_nodes": MAX_NODES,
            "unique_finding_ids": True, "max_string_characters": 32768,
            "max_integer_token_characters": 12, "max_float_token_characters": 32,
            "finite_numbers_only": True, "integer_tokens_for_path_groups": True,
        },
        "x-version-projection": {
            "ids": sorted(id for id in IDS if id.endswith((".version", ".dependency"))),
            "field": "version", "pattern": VERSION_PATTERN, "match": "full string",
            "description": "Annotation, not an input constraint: only matching strings are projected; all other values are ignored.",
        },
    }


def schema_json():
    return json.dumps(diagnosis_schema(), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
