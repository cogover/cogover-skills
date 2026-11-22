#!/usr/bin/env python3
"""Read and configure a Cogover Customer Portal through the Web App admin API.

Base URL and API Key come from the environment (COGOVER_BASE_URL, COGOVER_API_KEY);
the key is exchanged for a Web App session at /bapi/v1/auth-token on every run.
Secrets (key, cookies, tokens) are never printed. Mutations require --apply.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

PREFIX = "/api/v1/workspace/customer-portal/"
SECRET_KEYS = {"httpsessionid", "xsrf-token", "authtoken", "cookie", "set-cookie", "authorization", "token"}
TIMEOUT = 120  # publish may take several seconds; keep the client patient


def base_url() -> str:
    value = os.getenv("COGOVER_BASE_URL") or os.getenv("COGOVER_WORKSPACE_DOMAIN") or os.getenv("WORKSPACE_DOMAIN")
    if not value:
        raise RuntimeError("COGOVER_BASE_URL is required")
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value.rstrip("/")


def api_key() -> str:
    value = os.getenv("COGOVER_API_KEY") or os.getenv("API_KEY")
    if not value:
        raise RuntimeError("COGOVER_API_KEY is required")
    return value


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("<redacted>" if k.lower() in SECRET_KEYS else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def send(request: urllib.request.Request) -> tuple[int, Any]:
    status, body, _ = send_ex(request)
    return status, body


def send_ex(request: urllib.request.Request) -> tuple[int, Any, Any]:
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None, response.headers
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        try:
            return error.code, json.loads(body), error.headers
        except json.JSONDecodeError:
            return error.code, {"raw": body[:1000]}, error.headers


class Session:
    def __init__(self) -> None:
        self.root = base_url()
        key = api_key()
        for attempt in range(4):
            request = urllib.request.Request(
                self.root + "/bapi/v1/auth-token", data=b"{}", method="POST",
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            )
            status, body, headers = send_ex(request)
            if status != 429 or attempt == 3:
                break
            # The session endpoint is rate limited per account (hourly window): honour Retry-After.
            retry = (headers.get("Retry-After") if headers else None) or ""
            wait = int(retry) if retry.isdigit() else 10 * (attempt + 1)
            if wait > 60:
                raise RuntimeError(f"auth-token rate limited (HTTP 429); retry after {wait} s")
            print(f"auth-token rate limited, retrying in {wait} s", file=sys.stderr)
            time.sleep(wait)
        if status != 200 or not isinstance(body, dict) or body.get("r") != 0:
            r = body.get("r") if isinstance(body, dict) else None
            raise RuntimeError(f"auth-token failed: HTTP {status}, r={r}")
        data = body.get("data") or {}
        if not all(data.get(k) for k in ("HttpSessionId", "XSRF-TOKEN", "AuthToken")):
            raise RuntimeError("auth-token response is missing session fields")
        label = str(body.get("workspaceDomain") or "").lower()
        host = urllib.parse.urlparse(self.root).hostname or ""
        if label and label != host and not host.startswith(label + "."):
            raise RuntimeError("auth-token returned a different Workspace; stop")
        xsrf = data["XSRF-TOKEN"]
        self.workspace_id = body.get("workspaceId")
        self.personnel_id = body.get("personnelId")
        self.headers = {
            "Accept": "application/json",
            "Cookie": f"HttpSessionId={data['HttpSessionId']}; XSRF-TOKEN={xsrf}; AuthToken={data['AuthToken']}",
            "x-csrf-token": xsrf,
            "x-xsrf-token": xsrf,
        }

    def call(self, method: str, path: str, body: Any = None, raw: bytes | None = None,
             content_type: str | None = None) -> tuple[int, Any]:
        path = path.lstrip("/")
        if path.startswith("api/"):
            url = self.root + "/" + path
        else:
            url = self.root + PREFIX + path
        headers = dict(self.headers)
        data = raw
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            content_type = "application/json"
        if content_type:
            headers["Content-Type"] = content_type
        return send(urllib.request.Request(url, data=data, method=method, headers=headers))


def load_json(text: str | None, file: Path | None) -> Any:
    if file:
        return json.loads(file.read_text(encoding="utf-8"))
    if text:
        return json.loads(text)
    return None


def emit(status: int, body: Any) -> int:
    print(json.dumps({"httpStatus": status, "response": redact(body)}, ensure_ascii=False, indent=2))
    ok = 200 <= status < 300 and isinstance(body, dict) and body.get("r") == 0
    if not ok:
        meta = body.get("meta") if isinstance(body, dict) else None
        print(f"Request failed: HTTP {status}, r={body.get('r') if isinstance(body, dict) else None}, "
              f"meta={json.dumps(meta, ensure_ascii=False) if meta else None}", file=sys.stderr)
    return 0 if ok else 1


REF = re.compile(r"\{\{steps\.(\d+)\.([A-Za-z0-9_.]+)\}\}")


def resolve_refs(value: Any, results: list) -> Any:
    """Replace {{steps.N.<path>}} with a value from the response of an earlier step (e.g. steps.1.data.id)."""
    if isinstance(value, dict):
        return {k: resolve_refs(v, results) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_refs(v, results) for v in value]
    if not isinstance(value, str) or "{{" not in value:
        return value

    def lookup(match: re.Match) -> Any:
        index = int(match.group(1))
        if index < 1 or index > len(results):
            raise KeyError(match.group(0))
        node: Any = results[index - 1]["response"]
        for part in match.group(2).split("."):
            if isinstance(node, list) and part.isdigit() and int(part) < len(node):
                node = node[int(part)]
            elif isinstance(node, dict) and part in node:
                node = node[part]
            else:
                raise KeyError(match.group(0))
        return node

    whole = REF.fullmatch(value)
    if whole:
        return lookup(whole)
    return REF.sub(lambda m: str(lookup(m)), value)


def need_apply(args: argparse.Namespace) -> None:
    if not args.apply:
        raise SystemExit("Refusing to write without --apply (read the current state first)")


def summary(cfg: dict) -> dict:
    draft = cfg.get("draft") or {}
    return {
        "status": cfg.get("status"), "portalUrl": cfg.get("portalUrl"), "dirty": cfg.get("dirty"),
        "configVersion": cfg.get("configVersion"), "lockVersion": cfg.get("lockVersion"),
        "publishedAt": cfg.get("publishedAt"), "displayName": draft.get("displayName"),
        "features": {k: (draft.get(k) or {}).get("enabled") for k in
                     ("statement", "ordering", "tasks", "team", "selfRegistration", "chat", "help")},
        "lookups": [x.get("key") for x in draft.get("lookups") or []],
        "objects": [{k: o.get(k) for k in ("id", "objectKey", "objectSlug", "enabled", "published", "sortOrder")}
                    for o in cfg.get("objects") or []],
        "helpStatus": cfg.get("helpStatus"),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--apply", action="store_true", help="allow write requests")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status", help="short summary of GET config (add --full for the whole response)")
    s.add_argument("--full", action="store_true")
    s = sub.add_parser("get", help="GET a path under /api/v1/workspace/customer-portal/ (e.g. objects, usage, users?limit=20)")
    s.add_argument("path")
    sub.add_parser("mailboxes", help="list Workspace mailboxes (type 1-4 and status 1 can send portal notifications)")
    s = sub.add_parser("settings", help="save draft settings: reads lockVersion, PUT config {lockVersion, settings}")
    s.add_argument("--json")
    s.add_argument("--json-file", type=Path)
    s = sub.add_parser("object-update", help="merge keys into an Object draft config and PUT objects/{id}")
    s.add_argument("config_id")
    s.add_argument("--json", help="partial config, e.g. '{\"memberScope\":\"own\"}'")
    s.add_argument("--json-file", type=Path)
    s.add_argument("--enabled", choices=("true", "false"))
    s.add_argument("--sort-order", type=int)
    s = sub.add_parser("publish", help="POST publish, then print the new summary")
    s = sub.add_parser("unpublish", help="POST unpublish (turns the portal off for every customer)")
    s = sub.add_parser("logo", help="upload a PNG/JPEG/WEBP logo (<= 1 MB) into the draft")
    s.add_argument("file", type=Path)
    s = sub.add_parser("grant", help="POST grants for 1-100 Contact ids")
    s.add_argument("contact_ids", nargs="+")
    s.add_argument("--language", choices=("vi-VN", "en-US"))
    s = sub.add_parser("batch", help='run a JSON list of {method, path, body} in ONE session; stops at the first failure; "lockVersion": "current" is filled from GET config; "{{steps.N.data.id}}" in path/body reads a value from step N')
    s.add_argument("--json-file", type=Path, required=True)
    s.add_argument("--out", type=Path, help="also write the step results as one JSON array to this file")
    s = sub.add_parser("call", help="any METHOD PATH under the customer-portal prefix")
    s.add_argument("method", choices=("GET", "POST", "PUT", "DELETE"))
    s.add_argument("path")
    s.add_argument("--json")
    s.add_argument("--json-file", type=Path)
    argv = sys.argv[1:]
    apply_flag = "--apply" in argv  # accepted before or after the subcommand
    args = p.parse_args([a for a in argv if a != "--apply"])
    args.apply = apply_flag

    # Validate input and the --apply gate before spending a session request.
    steps: list = []
    if args.cmd == "batch":
        try:
            steps = load_json(None, args.json_file)
        except (OSError, json.JSONDecodeError) as error:
            raise SystemExit(f"invalid input: {error}")
        if not isinstance(steps, list) or not steps or not all(
                isinstance(x, dict) and x.get("method") in ("GET", "POST", "PUT", "DELETE") and isinstance(x.get("path"), str)
                and not x["path"].lstrip("/").startswith("api/") for x in steps):
            raise SystemExit("batch file must be a non-empty list of {method, path[, body]} under the customer-portal prefix")
    writes = args.cmd in ("settings", "object-update", "publish", "unpublish", "logo", "grant") or (
        args.cmd == "call" and args.method != "GET") or any(x["method"] != "GET" for x in steps)
    if writes:
        need_apply(args)
    try:
        if args.cmd in ("settings", "object-update", "call"):
            load_json(getattr(args, "json", None), getattr(args, "json_file", None))
        if args.cmd == "logo" and not args.file.is_file():
            raise SystemExit("logo file not found")
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"invalid input: {error}")
    if args.cmd in ("get", "call") and args.path.lstrip("/").startswith("api/"):
        raise SystemExit("only paths under the customer-portal prefix are accepted")

    try:
        session = Session()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.cmd == "status":
        st, body = session.call("GET", "config")
        if st == 200 and isinstance(body, dict) and body.get("r") == 0 and not args.full:
            print(json.dumps(summary(body["data"]), ensure_ascii=False, indent=2))
            return 0
        return emit(st, body)
    if args.cmd == "get":
        if args.path.lstrip("/").startswith("api/"):
            raise SystemExit("get only accepts paths under the customer-portal prefix")
        return emit(*session.call("GET", args.path))
    if args.cmd == "mailboxes":
        st, body = session.call("GET", "api/v1/workspaceEmail")
        if st == 200 and isinstance(body, dict) and body.get("r") == 0:
            rows = [{"id": m.get("id"), "email": m.get("email"), "type": m.get("type"), "status": m.get("status"),
                     "sendable": m.get("type") in (1, 2, 3, 4) and m.get("status") == 1 and bool(m.get("email"))}
                    for m in body.get("data") or []]
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return 0
        return emit(st, body)
    if args.cmd == "settings":
        settings = load_json(args.json, args.json_file)
        if not isinstance(settings, dict) or not settings:
            raise SystemExit("settings must be a non-empty JSON object of top-level blocks")
        need_apply(args)
        st, cfg = session.call("GET", "config")
        if st != 200 or cfg.get("r") != 0:
            return emit(st, cfg)
        st, body = session.call("PUT", "config", {"lockVersion": cfg["data"]["lockVersion"], "settings": settings})
        if st == 200 and body.get("r") == 0:
            print(json.dumps(summary(body["data"]), ensure_ascii=False, indent=2))
            return 0
        return emit(st, body)
    if args.cmd == "object-update":
        patch = load_json(args.json, args.json_file) or {}
        need_apply(args)
        st, cur = session.call("GET", f"objects/{args.config_id}")
        if st != 200 or cur.get("r") != 0:
            return emit(st, cur)
        payload: dict = {"config": {**(cur["data"].get("draft") or {}), **patch}}
        if args.enabled:
            payload["enabled"] = args.enabled == "true"
        if args.sort_order is not None:
            payload["sortOrder"] = args.sort_order
        return emit(*session.call("PUT", f"objects/{args.config_id}", payload))
    if args.cmd in ("publish", "unpublish"):
        need_apply(args)
        st, body = session.call("POST", args.cmd, {})
        code = emit(st, body)
        st2, cfg = session.call("GET", "config")
        if st2 == 200 and cfg.get("r") == 0:
            print(json.dumps({"after": summary(cfg["data"])}, ensure_ascii=False, indent=2))
        return code
    if args.cmd == "logo":
        need_apply(args)
        mime = mimetypes.guess_type(args.file.name)[0] or "application/octet-stream"
        boundary = "----cp-" + uuid.uuid4().hex
        raw = b"".join([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="logo"; filename="{args.file.name}"\r\n'.encode(),
            f"Content-Type: {mime}\r\n\r\n".encode(), args.file.read_bytes(), b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ])
        return emit(*session.call("POST", "config/logo", raw=raw, content_type=f"multipart/form-data; boundary={boundary}"))
    if args.cmd == "grant":
        need_apply(args)
        body: dict = {"contactIds": args.contact_ids}
        if args.language:
            body["language"] = args.language
        return emit(*session.call("POST", "grants", body))
    if args.cmd == "batch":
        results: list = []
        code = 0
        for index, step in enumerate(steps, 1):
            print(f"# step {index}: {step['method']} {step['path']}")
            try:
                path = resolve_refs(step["path"], results)
                body = resolve_refs(step.get("body"), results)
            except KeyError as error:
                print(f"Unresolved reference {error} at step {index}", file=sys.stderr)
                code = 1
                break
            if isinstance(body, dict) and body.get("lockVersion") == "current":
                st, cfg = session.call("GET", "config")
                if st != 200 or cfg.get("r") != 0:
                    code = emit(st, cfg)
                    break
                body = {**body, "lockVersion": cfg["data"]["lockVersion"]}
            status, response = session.call(step["method"], path, body)
            results.append({"step": index, "method": step["method"], "path": path,
                            "httpStatus": status, "response": redact(response)})
            if emit(status, response):
                print(f"Stopped at step {index}", file=sys.stderr)
                code = 1
                break
        if args.out:
            args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        return code
    if args.cmd == "call":
        body = load_json(args.json, args.json_file)
        if args.method != "GET":
            need_apply(args)
        if args.path.lstrip("/").startswith("api/"):
            raise SystemExit("call only accepts paths under the customer-portal prefix")
        return emit(*session.call(args.method, args.path, body))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
