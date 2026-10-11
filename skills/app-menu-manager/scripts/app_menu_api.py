#!/usr/bin/env python3
"""Call Cogover App/Menu REST APIs through an API-key-derived Web App session."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


REPORT_SETTINGS_ROUTE = re.compile(r"^/settings/reports(?:/|$)")
REPORT_RUNTIME_ROUTE = re.compile(r"^/reports/[A-Za-z0-9][A-Za-z0-9_-]*(?:\?.*)?$")


def pair(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected KEY=VALUE")
    key, item = value.split("=", 1)
    return key, item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", required=True, choices=("GET", "POST", "PUT", "DELETE"))
    parser.add_argument("--path", required=True, help="Absolute API path beginning with /api/vN/apps")
    parser.add_argument("--query", action="append", default=[], type=pair, metavar="KEY=VALUE")
    body = parser.add_mutually_exclusive_group()
    body.add_argument("--json")
    body.add_argument("--json-file", type=Path)
    parser.add_argument("--form", action="append", default=[], type=pair, metavar="KEY=VALUE")
    parser.add_argument("--file", action="append", default=[], type=pair, metavar="KEY=PATH")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Required for POST/PUT/DELETE")
    return parser.parse_args()


def get_base_url() -> str:
    value = os.getenv("COGOVER_BASE_URL") or os.getenv("COGOVER_WORKSPACE_DOMAIN")
    if not value:
        raise RuntimeError("COGOVER_BASE_URL or COGOVER_WORKSPACE_DOMAIN is required")
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value.rstrip("/")


def open_json(request: urllib.request.Request, context: ssl.SSLContext) -> tuple[int, Any]:
    try:
        with urllib.request.urlopen(request, timeout=45, context=context) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        try:
            parsed: Any = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body[:2000]}
        return error.code, parsed


def session_headers(root: str, api_key: str, context: ssl.SSLContext) -> dict[str, str]:
    request = urllib.request.Request(
        root + "/bapi/v1/auth-token",
        data=b"{}",
        method="POST",
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    )
    status, response = open_json(request, context)
    if status != 200 or response.get("r") != 0:
        raise RuntimeError(f"auth-token failed: HTTP {status}, r={response.get('r')}, msg={response.get('msg')}")
    data = response.get("data") or {}
    if not all(data.get(key) for key in ("HttpSessionId", "XSRF-TOKEN", "AuthToken")):
        raise RuntimeError("auth-token response is missing required session fields")
    xsrf = data["XSRF-TOKEN"]
    return {
        "Accept": "application/json, text/plain, */*",
        "Cookie": f"HttpSessionId={data['HttpSessionId']}; XSRF-TOKEN={xsrf}; AuthToken={data['AuthToken']}",
        "x-csrf-token": xsrf,
        "x-xsrf-token": xsrf,
    }


def encode_multipart(fields: list[tuple[str, str]], files: list[tuple[str, str]]) -> tuple[bytes, str]:
    boundary = "----codex-" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for key, value in fields:
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
            value.encode(), b"\r\n",
        ])
    for key, raw_path in files:
        path = Path(raw_path)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{key}"; filename="{path.name}"\r\n'.encode(),
            f"Content-Type: {mime}\r\n\r\n".encode(),
            path.read_bytes(), b"\r\n",
        ])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def build_body(args: argparse.Namespace) -> tuple[bytes | None, str | None, Any]:
    if (args.json or args.json_file) and (args.form or args.file):
        raise ValueError("JSON body cannot be combined with multipart form fields")
    if args.form or args.file:
        encoded, content_type = encode_multipart(args.form, args.file)
        printable = {"form": dict(args.form), "files": [{"field": k, "path": v} for k, v in args.file]}
        return encoded, content_type, printable
    if args.json or args.json_file:
        raw = args.json if args.json is not None else args.json_file.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        return json.dumps(parsed).encode(), "application/json", parsed
    return None, None, None


def validate_runtime_menu_routes(method: str, path: str, body: Any) -> None:
    """Reject report admin routes in Menu Item create/update payloads."""
    if method not in ("POST", "PUT") or not isinstance(body, dict):
        return
    if not re.fullmatch(r"/api/v\d+/apps/[^/]+/menuItems(?:/[^/]+)?", path):
        return
    content = body.get("actionContent")
    if not isinstance(content, str):
        return
    if REPORT_SETTINGS_ROUTE.match(content):
        raise ValueError(
            "Report Menu Item must use runtime route /reports/{reportSlug}; "
            "the admin route /settings/reports/{reportSlug} is forbidden"
        )
    if "/reports/" in content and not REPORT_RUNTIME_ROUTE.fullmatch(content):
        raise ValueError("Invalid runtime report route; expected /reports/{reportSlug}")


def main() -> int:
    args = parse_args()
    if not args.path.startswith("/api/v") or "/apps" not in args.path or ".." in args.path:
        print("--path must begin with /api/vN and contain /apps", file=sys.stderr)
        return 2
    try:
        data, content_type, printable_body = build_body(args)
        root = get_base_url()
        validate_runtime_menu_routes(args.method, args.path, printable_body)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    query = urllib.parse.urlencode(args.query, doseq=True)
    url = root + args.path + (("?" + query) if query else "")
    if not args.execute:
        print(json.dumps({
            "method": args.method,
            "url": url,
            "contentType": content_type,
            "body": printable_body,
            "auth": "session from $cogover-api-auth",
        }, ensure_ascii=False, indent=2))
        return 0
    if args.method != "GET" and not args.apply:
        print("Refusing mutation without --apply", file=sys.stderr)
        return 2
    api_key = os.getenv("COGOVER_API_KEY")
    if not api_key:
        print("COGOVER_API_KEY is required", file=sys.stderr)
        return 2
    context = ssl.create_default_context()
    try:
        headers = session_headers(root, api_key, context)
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=data, method=args.method, headers=headers)
        status, response = open_json(request, context)
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps({"httpStatus": status, "response": response}, ensure_ascii=False, indent=2))
    result = response.get("r") if isinstance(response, dict) else None
    message = response.get("msg") if isinstance(response, dict) else None
    if not 200 <= status < 300 or result != 0:
        print(f"Request failed: HTTP {status}, r={result}, msg={message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
