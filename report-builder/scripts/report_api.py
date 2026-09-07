#!/usr/bin/env python3
"""Safely build and optionally send Cogover Public Report API requests."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


READ_ONLY_SERVICES = {
    200, 211, 215, 220, 221, 222, 223, 229, 230, 233, 237, 239, 243, 246
}
AGGREGATES = {"sum", "avg", "count", "max", "min", "median"}
SENSITIVE_KEYS = {"api_key", "apikey", "authorization", "secret", "secret_token", "token"}


class ValidationError(ValueError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Cogover Public Report API request. The command is dry-run by "
            "default; add --execute for network access and --apply for mutations."
        )
    )
    parser.add_argument("--service", type=int, required=True, help="Public Report API service number")
    payload_group = parser.add_mutually_exclusive_group(required=True)
    payload_group.add_argument("--payload", help="Payload as a JSON object string")
    payload_group.add_argument("--payload-file", help="Path to payload JSON, or '-' for stdin")
    parser.add_argument(
        "--workspace-domain",
        help="Workspace domain/URL; defaults to COGOVER_WORKSPACE_DOMAIN",
    )
    parser.add_argument("--execute", action="store_true", help="Send the request instead of dry-run")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Acknowledge mutation; required with --execute for non-read-only services",
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout in seconds")
    return parser.parse_args()


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload is not None:
        raw = args.payload
    elif args.payload_file == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(args.payload_file).read_text(encoding="utf-8")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Payload is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValidationError("Payload must be a JSON object")
    return payload


def require(payload: dict[str, Any], *keys: str) -> None:
    missing = [key for key in keys if key not in payload or payload[key] is None]
    if missing:
        raise ValidationError(f"Missing required payload field(s): {', '.join(missing)}")


def require_one(payload: dict[str, Any], *keys: str) -> None:
    present = [key for key in keys if payload.get(key) not in (None, "", [], {})]
    if len(present) != 1:
        raise ValidationError(f"Provide exactly one of: {', '.join(keys)}")


def validate_relations(relations: Any, *, allow_empty: bool) -> None:
    if not isinstance(relations, list):
        raise ValidationError("relations must be an array")
    if not allow_empty and not relations:
        raise ValidationError("relations must not be empty")
    if len(relations) > 4:
        raise ValidationError("A Report Type supports at most 4 relations (5 objects)")
    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            raise ValidationError(f"relations[{index}] must be an object")
        require(relation, "src_object_id", "dst_object_id", "relation_type", "object_relation_id")
        if relation["relation_type"] not in (1, 2):
            raise ValidationError(f"relations[{index}].relation_type must be 1 or 2")


def graph_node_object_id(node: dict[str, Any]) -> Any:
    if node.get("type") == "nodeRoot":
        return node.get("id")
    data = node.get("data")
    return data.get("current_object_id") if isinstance(data, dict) else None


def validate_metadata_graph(
    parsed: dict[str, Any],
    *,
    expected_root: str | None = None,
    relations: list[dict[str, Any]] | None = None,
) -> None:
    for key in ("nodes", "edges", "viewport"):
        if key not in parsed:
            raise ValidationError(f"meta_data graph must contain {key}")
    nodes = parsed["nodes"]
    edges = parsed["edges"]
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValidationError("meta_data nodes and edges must be arrays")
    if not isinstance(parsed["viewport"], dict):
        raise ValidationError("meta_data viewport must be an object")
    if not nodes:
        raise ValidationError("meta_data graph must contain at least one node")
    if len(nodes) > 5 or len(edges) > 4:
        raise ValidationError("meta_data supports at most 5 nodes and 4 edges")

    node_by_id: dict[str, dict[str, Any]] = {}
    node_alias: dict[str, str] = {}
    roots: list[dict[str, Any]] = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValidationError(f"meta_data.nodes[{index}] must be an object")
        require(node, "id", "type", "position", "data")
        node_id = node["id"]
        if not isinstance(node_id, str) or not node_id:
            raise ValidationError(f"meta_data.nodes[{index}].id must be a non-empty string")
        if node_id in node_by_id:
            raise ValidationError(f"meta_data contains duplicate node id {node_id}")
        if node["type"] not in ("nodeRoot", "nodeHeader"):
            raise ValidationError(
                f"meta_data.nodes[{index}].type must be nodeRoot or nodeHeader"
            )
        if not isinstance(node["position"], dict) or not isinstance(node["data"], dict):
            raise ValidationError(
                f"meta_data.nodes[{index}].position and data must be objects"
            )
        node_by_id[node_id] = node
        node_alias[node_id] = chr(ord("A") + index)
        if node["type"] == "nodeRoot":
            roots.append(node)
        else:
            require(
                node["data"],
                "parent_object_id",
                "current_object_id",
                "relation_type",
                "level",
                "content",
            )
            require(node, "parentId")

    if len(roots) != 1:
        raise ValidationError("meta_data graph must contain exactly one nodeRoot")
    root = roots[0]
    if root is not nodes[0]:
        raise ValidationError("meta_data nodeRoot must be the first node and use alias A")
    require(root["data"], "title", "content")
    if expected_root and root.get("id") != expected_root:
        raise ValidationError("meta_data nodeRoot id must match src_object_id")
    if len(edges) != len(nodes) - 1:
        raise ValidationError("meta_data graph must be a connected tree")

    edge_ids: set[str] = set()
    relation_matches: set[int] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValidationError(f"meta_data.edges[{index}] must be an object")
        require(edge, "id", "source", "target", "type", "data")
        if not isinstance(edge["data"], dict):
            raise ValidationError(f"meta_data.edges[{index}].data must be an object")
        if edge["type"] != "customSmoothStep":
            raise ValidationError(
                f"meta_data.edges[{index}].type must be customSmoothStep"
            )
        if edge["id"] in edge_ids:
            raise ValidationError(f"meta_data contains duplicate edge id {edge['id']}")
        edge_ids.add(edge["id"])

        source = edge["source"]
        target = edge["target"]
        if source not in node_by_id or target not in node_by_id:
            raise ValidationError(
                f"meta_data.edges[{index}] source and target must reference graph nodes"
            )
        if source == target:
            raise ValidationError(f"meta_data.edges[{index}] cannot connect a node to itself")

        data = edge["data"]
        require(
            data,
            "src_object_id",
            "dst_object_id",
            "relation_type",
            "object_relation_id",
            "field_slug",
            "lookup_type",
            "source_name",
        )
        for key in (
            "src_object_id",
            "dst_object_id",
            "object_relation_id",
            "field_slug",
        ):
            if not isinstance(data[key], str) or not data[key]:
                raise ValidationError(
                    f"meta_data.edges[{index}].data.{key} must be a non-empty string"
                )
        if data["relation_type"] not in (1, 2):
            raise ValidationError(
                f"meta_data.edges[{index}].data.relation_type must be 1 or 2"
            )
        if data["lookup_type"] not in (1, 2):
            raise ValidationError(
                f"meta_data.edges[{index}].data.lookup_type must be 1 or 2"
            )
        if not isinstance(data["source_name"], str) or not data["source_name"]:
            raise ValidationError(
                f"meta_data.edges[{index}].data.source_name must be a non-empty alias"
            )
        expected_alias = node_alias[source]
        if data["source_name"] != expected_alias:
            raise ValidationError(
                f"meta_data.edges[{index}].data.source_name must be {expected_alias} "
                "for its parent node"
            )

        parent_node = node_by_id[source]
        child_node = node_by_id[target]
        if child_node.get("type") != "nodeHeader":
            raise ValidationError(f"meta_data.edges[{index}] target must be a nodeHeader")
        if child_node.get("parentId") != source:
            raise ValidationError(
                f"meta_data.edges[{index}] target.parentId must equal edge source"
            )
        parent_object_id = graph_node_object_id(parent_node)
        child_object_id = graph_node_object_id(child_node)
        if data["lookup_type"] == 2:
            expected_parent = data["src_object_id"]
            expected_child = data["dst_object_id"]
        else:
            expected_parent = data["dst_object_id"]
            expected_child = data["src_object_id"]
        if parent_object_id != expected_parent or child_object_id != expected_child:
            direction = "from" if data["lookup_type"] == 2 else "to"
            raise ValidationError(
                f"meta_data.edges[{index}] lookup_type {data['lookup_type']} ({direction} parent) "
                "does not match the parent/child object direction"
            )

        child_data = child_node["data"]
        if child_data["parent_object_id"] != parent_object_id:
            raise ValidationError(
                f"meta_data.edges[{index}] child parent_object_id does not match edge source"
            )
        if child_data["relation_type"] != data["relation_type"]:
            raise ValidationError(
                f"meta_data.edges[{index}] child and edge relation_type must match"
            )
        parent_level = 0 if parent_node["type"] == "nodeRoot" else parent_node["data"]["level"]
        if child_data["level"] != parent_level + 1:
            raise ValidationError(
                f"meta_data.edges[{index}] child level must be parent level plus one"
            )
        if "parent_id" in child_data and child_data["parent_id"] != parent_object_id:
            raise ValidationError(
                f"meta_data.edges[{index}] child parent_id must match parent_object_id"
            )

        if relations is not None:
            match_index = next(
                (
                    relation_index
                    for relation_index, relation in enumerate(relations)
                    if relation.get("src_object_id") == data["src_object_id"]
                    and relation.get("dst_object_id") == data["dst_object_id"]
                    and relation.get("relation_type") == data["relation_type"]
                    and relation.get("object_relation_id") == data["object_relation_id"]
                ),
                None,
            )
            if match_index is None:
                raise ValidationError(
                    f"meta_data.edges[{index}] does not match any relation in payload"
                )
            if match_index in relation_matches:
                raise ValidationError("multiple metadata edges map to the same relation")
            relation_matches.add(match_index)

    if relations is not None and len(relation_matches) != len(relations):
        raise ValidationError("every payload relation must have exactly one metadata edge")


def validate_metadata(
    payload: dict[str, Any],
    *,
    require_graph: bool = False,
    expected_root: str | None = None,
    relations: list[dict[str, Any]] | None = None,
) -> None:
    if "meta_data" not in payload:
        return
    meta_data = payload["meta_data"]
    if not isinstance(meta_data, str):
        raise ValidationError("meta_data must be a JSON string, not a JSON object")
    try:
        parsed = json.loads(meta_data)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"meta_data is not valid serialized JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValidationError("meta_data must serialize a JSON object")
    has_graph_key = any(key in parsed for key in ("nodes", "edges", "viewport"))
    if require_graph or has_graph_key:
        validate_metadata_graph(
            parsed,
            expected_root=expected_root,
            relations=relations,
        )


def validate_run_report(payload: dict[str, Any]) -> None:
    require(payload, "report_id", "filter_type")
    if payload["filter_type"] not in (1, 2, 3):
        raise ValidationError("filter_type must be 1, 2, or 3")
    size = payload.get("size")
    if size is not None and (not isinstance(size, int) or size < 1 or size > 10000):
        raise ValidationError("size must be an integer from 1 to 10000")
    for key in ("group_rows", "group_columns"):
        value = payload.get(key, [])
        if not isinstance(value, list):
            raise ValidationError(f"{key} must be an array")
        if len(value) > 2:
            raise ValidationError(f"{key} supports at most 2 fields")
    aggregates = payload.get("aggregates", [])
    if not isinstance(aggregates, list):
        raise ValidationError("aggregates must be an array for service 200")
    for index, item in enumerate(aggregates):
        if not isinstance(item, dict):
            raise ValidationError(f"aggregates[{index}] must be an object")
        require(item, "id", "operations")
        operations = item["operations"]
        if not isinstance(operations, list) or not operations:
            raise ValidationError(f"aggregates[{index}].operations must be a non-empty array")
        invalid = sorted(set(operations) - AGGREGATES)
        if invalid:
            raise ValidationError(
                f"aggregates[{index}] contains unsupported operation(s): {', '.join(invalid)}"
            )


def validate_payload(service: int, payload: dict[str, Any]) -> None:
    if service == 200:
        validate_run_report(payload)
    elif service == 201:
        require(payload, "report_type", "name")
    elif service in (203, 214):
        require(payload, "ids")
        if not isinstance(payload["ids"], list) or not payload["ids"]:
            raise ValidationError("ids must be a non-empty array")
    elif service == 202:
        require(payload, "report_id", "relations", "meta_data")
        has_source = payload.get("src_object_id") not in (None, "")
        has_relations = payload.get("relations") not in (None, [])
        if not has_source and not has_relations:
            raise ValidationError("service 202 requires src_object_id or relations")
        validate_relations(payload["relations"], allow_empty=has_source)
        expected_root = payload.get("src_object_id") if not has_relations else None
        validate_metadata(
            payload,
            require_graph=True,
            expected_root=expected_root,
            relations=payload["relations"],
        )
    elif service == 207:
        require(payload, "id")
    elif service == 208:
        require(payload, "report_id", "section_name", "section_index")
    elif service == 209:
        require(payload, "id", "report_id", "section_name", "section_index")
    elif service == 210:
        require(payload, "id")
    elif service == 212:
        require(payload, "report_type_name", "report_type_slug", "primary_object")
        validate_metadata(payload)
    elif service == 213:
        require(payload, "id", "report_type_name", "report_type_slug")
        validate_metadata(payload)
    elif service in (221, 222):
        require(payload, "report_id")
    elif service == 225:
        require(payload, "sections")
    elif service == 226:
        require(payload, "id")
    elif service == 227:
        require(payload, "report_type_id", "field")
        if not isinstance(payload["field"], dict):
            raise ValidationError("field must be an object")
        require(
            payload["field"],
            "object_type_id",
            "field_name",
            "section_id",
            "field_slug",
            "field_type",
            "status",
        )
        if payload["field"]["field_type"] not in (0, 1):
            raise ValidationError("field.field_type must be 0 (normal) or 1 (lookup)")
    elif service == 228:
        require(payload, "report_type_id", "id")
    elif service == 229:
        require_one(payload, "report_id", "slug")
    elif service == 230:
        require(payload, "object_type_id", "field_id")
    elif service == 231:
        require(payload, "report_id", "relations")
        has_source = payload.get("src_object_id") not in (None, "")
        validate_relations(payload["relations"], allow_empty=has_source)
        validate_metadata(
            payload,
            require_graph="meta_data" in payload,
            expected_root=payload.get("src_object_id") if not payload["relations"] else None,
            relations=payload["relations"] if "meta_data" in payload else None,
        )
    elif service == 232:
        require(payload, "section_id", "fields")
    elif service == 239:
        require(payload, "slug")
    elif service == 246:
        require(payload, "script", "return_type")


def payload_warnings(service: int, payload: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if service == 212 and "meta_data" in payload:
        warnings.append(
            "service 212 does not accept meta_data; move the graph to the required service 202 call"
        )
    if service == 207:
        if "folder_id" not in payload:
            warnings.append("service 207 omits folder_id; the current folder may be cleared")
        if "acl" not in payload:
            warnings.append("service 207 omits acl; the current ACL may be cleared")
    if service in (202, 231) and payload.get("relations") and "meta_data" not in payload:
        warnings.append("relation metadata is omitted; the relation graph may not hydrate")
    if service == 200 and payload.get("filter_type") == 3 and not payload.get("logic_sequence"):
        warnings.append("filter_type 3 normally requires a verified logic_sequence")
    return warnings


def normalize_endpoint(raw_domain: str) -> str:
    value = raw_domain.strip()
    if not value:
        raise ValidationError("Workspace domain is empty")
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise ValidationError("Workspace URL must use https")
    if not parsed.netloc or parsed.username or parsed.password:
        raise ValidationError("Workspace URL must contain a valid host and no credentials")
    if parsed.query or parsed.fragment:
        raise ValidationError("Workspace URL must not contain query parameters or a fragment")
    base_path = parsed.path.rstrip("/")
    if base_path:
        raise ValidationError("Workspace URL must not contain an application path")
    return f"https://{parsed.netloc}/bapi/v1/report"


def decode_body(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<redacted>" if key.lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def service_result_code(value: Any) -> Any:
    if not isinstance(value, dict):
        return None
    if "r" in value:
        return value["r"]
    body = value.get("body")
    if isinstance(body, dict):
        return body.get("r")
    return None


def print_json(value: Any) -> None:
    value = redact(value)
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        print(value)


def execute(endpoint: str, token: str, envelope: dict[str, Any], timeout: float) -> int:
    body = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = decode_body(response.read())
            print_json({"http_status": response.status, "body": result})
            if service_result_code(result) not in (None, 0):
                return 3
            return 0
    except urllib.error.HTTPError as exc:
        result = decode_body(exc.read())
        error_output: dict[str, Any] = {"http_status": exc.code, "body": result}
        retry_after = exc.headers.get("Retry-After")
        rate_limit_reason = exc.headers.get("RateLimit-Reason")
        if retry_after:
            error_output["retry_after"] = retry_after
        if rate_limit_reason:
            error_output["rate_limit_reason"] = rate_limit_reason
        print_json(error_output)
        return 3
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        print_json({"network_error": str(exc)})
        return 4


def main() -> int:
    args = parse_args()
    try:
        payload = load_payload(args)
        validate_payload(args.service, payload)
        raw_domain = (
            args.workspace_domain
            or os.environ.get("COGOVER_BASE_URL")
            or os.environ.get("COGOVER_WORKSPACE_DOMAIN", "")
        )
        endpoint = normalize_endpoint(raw_domain)
        envelope = {"service": args.service, "payload": payload}
        warnings = payload_warnings(args.service, payload)

        if not args.execute:
            output: dict[str, Any] = {"dry_run": True, "endpoint": endpoint, "request": envelope}
            if warnings:
                output["warnings"] = warnings
            print_json(output)
            return 0

        if args.service not in READ_ONLY_SERVICES and not args.apply:
            raise ValidationError(
                f"Service {args.service} is a mutation or unknown service; add --apply after checking preconditions"
            )

        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)

        token = os.environ.get("COGOVER_API_KEY", "")
        if not token:
            raise ValidationError("COGOVER_API_KEY is required for --execute")
        return execute(endpoint, token, envelope, args.timeout)
    except (ValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
