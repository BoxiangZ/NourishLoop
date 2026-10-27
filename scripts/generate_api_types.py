"""Export OpenAPI and the frontend's shared schema types from the FastAPI app."""

from __future__ import annotations

import json
from pathlib import Path

from apps.api.main import app


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "api-client" / "src"


def ts_type(schema: dict) -> str:
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "anyOf" in schema:
        return " | ".join(ts_type(part) for part in schema["anyOf"])
    if "enum" in schema:
        return " | ".join(json.dumps(value) for value in schema["enum"])
    if "const" in schema:
        return json.dumps(schema["const"])
    kind = schema.get("type")
    if kind == "array":
        return f"Array<{ts_type(schema['items'])}>"
    if kind == "object":
        properties = schema.get("properties", {})
        if not properties:
            return "Record<string, unknown>"
        required = set(schema.get("required", []))
        members = [
            f"{json.dumps(name)}{'?' if name not in required else ''}: {ts_type(value)};"
            for name, value in properties.items()
        ]
        return "{ " + " ".join(members) + " }"
    if kind in ("integer", "number"):
        return "number"
    if kind == "boolean":
        return "boolean"
    if kind == "null":
        return "null"
    return "string"


def main() -> None:
    schema = app.openapi()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "openapi.json").write_text(json.dumps(schema, indent=2) + "\n")
    lines = ["// Generated from FastAPI OpenAPI. Run: python -m scripts.generate_api_types", ""]
    for name, definition in sorted(schema["components"]["schemas"].items()):
        lines.append(f"export type {name} = {ts_type(definition)};")
    (OUT / "schema.ts").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
