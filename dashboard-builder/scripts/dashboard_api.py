#!/usr/bin/env python3
"""Call dashboard-server through an API-key-derived Cogover Web App session."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

MUTATING_SERVICES = {3, 4, 5, 20}
KNOWN_SERVICES = MUTATING_SERVICES | {6}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--service", type=int, required=True, choices=sorted(KNOWN_SERVICES))
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--payload")
    source.add_argument("--payload-file", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Required for service 3, 4, 5, or 20")
    return parser.parse_args()


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    raw = args.payload if args.payload is not None else args.payload_file.read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


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
            return response.status, json.load(response)
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
    required = ("HttpSessionId", "XSRF-TOKEN", "AuthToken")
    if not all(data.get(key) for key in required):
        raise RuntimeError("auth-token response is missing required session fields")
    xsrf = data["XSRF-TOKEN"]
    return {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Cookie": f"HttpSessionId={data['HttpSessionId']}; XSRF-TOKEN={xsrf}; AuthToken={data['AuthToken']}",
        "x-csrf-token": xsrf,
        "x-xsrf-token": xsrf,
    }


def business_result(response: Any) -> tuple[Any, Any]:
    if not isinstance(response, dict):
        return None, None
    if "r" in response:
        return response.get("r"), response.get("msg")
    body = response.get("body") or {}
    return body.get("r"), body.get("msg")


def main() -> int:
    args = parse_args()
    try:
        payload = load_payload(args)
        root = get_base_url()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    url = root + "/api/v1/dashboard-server"
    if not args.execute:
        print(json.dumps({
            "method": "POST",
            "url": url,
            "headers": {
                "Content-Type": "application/json",
                "x-req-type": "6",
                "x-req-service": str(args.service),
                "Cookie": "<session from $cogover-api-auth>",
                "x-csrf-token": "<XSRF-TOKEN>",
                "x-xsrf-token": "<XSRF-TOKEN>",
            },
            "payload": payload,
        }, ensure_ascii=False, indent=2))
        return 0
    if args.service in MUTATING_SERVICES and not args.apply:
        print("Refusing mutation without --apply", file=sys.stderr)
        return 2
    api_key = os.getenv("COGOVER_API_KEY")
    if not api_key:
        print("COGOVER_API_KEY is required", file=sys.stderr)
        return 2
    context = ssl.create_default_context()
    try:
        headers = session_headers(root, api_key, context)
        headers.update({"x-req-type": "6", "x-req-service": str(args.service)})
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        status, response = open_json(request, context)
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps({"httpStatus": status, "response": response}, ensure_ascii=False, indent=2))
    result, message = business_result(response)
    if not 200 <= status < 300 or result != 0:
        print(f"Request failed: HTTP {status}, r={result}, msg={message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
