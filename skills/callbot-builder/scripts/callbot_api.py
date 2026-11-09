#!/usr/bin/env python3
"""Cogover Callbot admin client: RPC `/api/v1/call-center` (service 17) and `/bapi/v1` helpers.

Commands:
  rpc ACTION        One RPC call, e.g. `rpc list_callbots`, `rpc get_callbot --callbot 12`.
  bapi PATH         One `/bapi/v1/...` call with the API Key (POST, or --method PUT).
  apply SPEC.json   Create/update a callbot and its tools from a spec. Dry-run unless --apply.
  simulate          Text simulation: start, send each --say, print replies and tool calls, end.
  sessions          Recent call sessions of a callbot (newest first).
  session ID        One session: transcript, tool calls, outcome, variables.

Credentials: COGOVER_BASE_URL (https) + COGOVER_API_KEY, or COGOVER_API_KEY_FILE pointing to a file that
holds only the key. Environment variables first; KEY=VALUE lines of --env-file only when that option is given.
The key is exchanged for a Web App session at /bapi/v1/auth-token; tokens and cookies are never printed.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RPC_PATH = "/api/v1/call-center"
RPC_HEADERS = {"x-req-type": "9", "x-req-service": "17"}
CONTEXT = ssl.create_default_context()
# Ghi/gọi ra ngoài: không tự gửi lại khi lỗi mạng/timeout (tránh tạo trùng, gọi trùng).
NON_IDEMPOTENT = {"create_callbot", "update_callbot", "put_callbot_secrets", "sync_callbot", "create_tool",
                  "update_tool", "delete_tool", "put_tool_secret", "test_call", "start_simulation",
                  "send_simulation_message", "set_callbot_status", "delete_callbot"}
SECRET_ACTIONS = {"put_callbot_secrets", "put_tool_secret"}
CALLBOT_FIELDS = ("name", "instructions", "welcomeMessage", "model", "voice", "transcriptionModel",
                  "openaiProjectSipUri", "recordEnabled", "runAsPersonnelId", "maxDurationSec",
                  "silenceTimeoutSec", "maxToolCalls", "maxConcurrent", "engine", "provider", "companyName",
                  "providerOptions")
TOOL_FIELDS = ("kind", "name", "description", "params", "url", "auth", "username", "timeoutMs", "config")


class ApiError(Exception):
    pass


def load_credentials(env_file: str | None) -> tuple[str, str]:
    names = ("COGOVER_BASE_URL", "COGOVER_API_KEY", "COGOVER_API_KEY_FILE")
    values = {n: os.environ[n] for n in names if os.environ.get(n)}
    path = Path(env_file) if env_file else None
    if path is not None:
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\s*([A-Z_]+)\s*=\s*(.*?)\s*$", line)
            if match and match.group(1) in names and match.group(1) not in values:
                values[match.group(1)] = match.group(2).strip("'\"")
    base, key = values.get("COGOVER_BASE_URL"), values.get("COGOVER_API_KEY")
    if not key and values.get("COGOVER_API_KEY_FILE"):
        key = Path(values["COGOVER_API_KEY_FILE"]).expanduser().read_text(encoding="utf-8").strip()
    if not base or not key:
        raise SystemExit("Missing COGOVER_BASE_URL and COGOVER_API_KEY (or COGOVER_API_KEY_FILE).")
    if base.startswith("http://"):
        raise SystemExit("COGOVER_BASE_URL must use https: the API key would be sent in clear text.")
    if not base.startswith("https://"):
        base = "https://" + base
    return base.rstrip("/"), key


class NetworkError(Exception):
    """Không nhận được response: không biết request đã được thực thi hay chưa."""


def parse_body(status: int, raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return {"r": status if status >= 400 else 502, "msg": "non_json_response"}


def send(url: str, body: Any, headers: dict[str, str], timeout: int = 120, method: str = "POST") -> tuple[int, Any]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method,
                                     headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=CONTEXT) as response:
            return response.status, parse_body(response.status, response.read())
    except urllib.error.HTTPError as error:
        return error.code, parse_body(error.code, error.read())
    except (OSError, http.client.HTTPException) as error:  # URLError, timeout, reset, RemoteDisconnected
        raise NetworkError(type(error).__name__) from None


class Client:
    def __init__(self, base: str, api_key: str):
        self.base = base
        self.bearer = {"Authorization": "Bearer " + api_key}
        self._session: dict[str, str] | None = None
        self._session_expires = 0.0

    def session(self) -> dict[str, str]:
        # Phiên Web App đổi từ API Key; làm mới 2 phút trước HttpSessionExpiresAt (thiếu thì sau 20 phút).
        if self._session is None or time.time() > self._session_expires:
            try:
                status, out = send(self.base + "/bapi/v1/auth-token", {}, self.bearer, 30)
            except NetworkError as error:
                raise ApiError(f"auth-token: network error {error}") from None
            if status >= 400 or not isinstance(out, dict) or out.get("r") != 0:
                raise ApiError(f"auth-token failed: HTTP {status} r={out.get('r') if isinstance(out, dict) else '?'}")
            d = out["data"]
            x = d["XSRF-TOKEN"]
            self._session = {"Cookie": f"AuthToken={d['AuthToken']}; HttpSessionId={d['HttpSessionId']}; XSRF-TOKEN={x}",
                             "x-csrf-token": x, "x-xsrf-token": x}
            expires = d.get("HttpSessionExpiresAt")
            if isinstance(expires, (int, float)) and expires > 0:
                expires = expires / 1000 if expires > 1e11 else expires
                self._session_expires = expires - 120
            else:
                self._session_expires = time.time() + 1200
        return self._session

    def rpc(self, request: dict[str, Any]) -> Any:
        """Gửi một action RPC 17; trả `data` khi r=0, ném ApiError(r, msg, message) khi lỗi."""
        write = request.get("action") in NON_IDEMPOTENT
        attempts = 3
        reauthed = False
        for attempt in range(attempts):
            headers = {**self.session(), **RPC_HEADERS}
            try:
                status, out = send(self.base + RPC_PATH, request, headers)
            except NetworkError as error:
                # không biết request ghi đã chạy hay chưa: không gửi lại
                if not write and attempt + 1 < attempts:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise ApiError(f"network error on {request.get('action')}: {error}"
                               + (" (not retried: read back the state before sending again)" if write else ""))
            r = out.get("r") if isinstance(out, dict) else None
            if (status == 401 or r == 401) and not reauthed:
                # phiên hết hạn: request bị từ chối, chưa thực thi -> đổi phiên và gửi lại một lần (kể cả ghi)
                self._session = None
                reauthed = True
                continue
            if (status == 429 or r == 429) and not write and attempt + 1 < attempts:
                time.sleep(5 * (attempt + 1))
                continue
            if not isinstance(out, dict) or "r" not in out:
                raise ApiError(f"malformed response HTTP {status}")
            if r != 0:
                data = out.get("data") if isinstance(out.get("data"), dict) else {}
                raise ApiError(f"{request.get('action')}: r={r} msg={out.get('msg')} {data.get('message', '')}".strip())
            return out.get("data")
        raise ApiError(f"{request.get('action')}: gave up after {attempts} attempts")

    def bapi(self, path: str, body: Any, method: str = "POST") -> Any:
        # Phần lớn /bapi trả {r, msg, data}; vài endpoint (objects/list) trả thẳng {items}.
        if "auth-token" in path:
            raise ApiError("refusing to call auth-token here: its response holds session secrets")
        try:
            status, out = send(self.base + path, body, self.bearer, method=method)
        except NetworkError as error:
            raise ApiError(f"{path}: network error {error} (read back before sending a write again)") from None
        if status >= 400 or not isinstance(out, dict) or out.get("r", 0) != 0:
            raise ApiError(f"{path}: HTTP {status} r={out.get('r') if isinstance(out, dict) else '?'} "
                           f"msg={out.get('msg') if isinstance(out, dict) else ''}")
        return out.get("data", out)


def read_json(value: str | None) -> Any:
    if value is None:
        return None
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- apply

def pick(src: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {k: src[k] for k in fields if k in src}


def norm_options(value: Any) -> dict[str, str]:
    # GET trả providerOptions dạng chuỗi; so sánh theo chuỗi để không cập nhật thừa.
    return {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in (value or {}).items()}


def callbot_diff(current: dict[str, Any], wanted: dict[str, Any]) -> dict[str, Any]:
    diff = {}
    for key, value in wanted.items():
        if key == "providerOptions":
            if norm_options(current.get(key)) != norm_options(value):
                diff[key] = value
        elif key == "runAsPersonnelId":
            if str(current.get(key) or "") != str(value or ""):
                diff[key] = value
        elif current.get(key) != value:
            diff[key] = value
    return diff


OBJECT_DEFAULTS = {"paramFields": {}, "paramOps": {}, "returnFields": [], "writableFields": [], "size": 3}


def norm_config(kind: str, config: Any) -> Any:
    """Điền giá trị mặc định service tự thêm để so sánh đúng cả khi spec bỏ một khoá."""
    config = dict(config or {})
    if kind == "cogover_object":
        config = {**OBJECT_DEFAULTS, **config}
        if config.get("action") in ("create", "update"):
            config.setdefault("requiresConfirmation", True)
    elif kind == "http":
        config.setdefault("requiresConfirmation", True)
    return config or None


def tool_changed(current: dict[str, Any], wanted: dict[str, Any]) -> bool:
    kind = wanted["kind"]
    if norm_config(kind, current.get("config")) != norm_config(kind, wanted.get("config")):
        return True
    # service không giữ thứ tự params; tool cogover_agent tự có tham số `question` khi spec để trống
    norm = lambda ps: sorted((p.get("key"), p.get("type"), p.get("description")) for p in ps or [])
    if not (kind == "cogover_agent" and not wanted.get("params")) and norm(current.get("params")) != norm(wanted.get("params")):
        return True
    for key in ("description", "url", "auth", "username", "timeoutMs"):
        if key in wanted and current.get(key) != wanted[key]:
            return True
    return False


def step(line: str) -> None:
    # in ngay từng bước: lỗi giữa chừng vẫn còn dấu vết những gì đã ghi
    print(" ", line, flush=True)


def apply_spec(client: Client, spec: dict[str, Any], do_apply: bool, prune: bool) -> None:
    wanted = pick(spec["callbot"], CALLBOT_FIELDS)
    if "name" not in wanted:
        raise SystemExit("spec.callbot.name is required")
    tools = [pick(t, TOOL_FIELDS) for t in spec.get("tools", [])]
    names = [t.get("name") for t in tools]
    if len(set(names)) != len(names):
        raise SystemExit("spec.tools has duplicated names")
    callbots = client.rpc({"action": "list_callbots"}) or []
    target_id = spec.get("callbotId")
    match = [c for c in callbots if (str(c["id"]) == str(target_id) if target_id else c["name"] == wanted["name"])]
    if len(match) > 1:
        raise SystemExit(f"{len(match)} callbots are named {wanted['name']!r}; set spec.callbotId")
    if target_id and not match:
        raise SystemExit(f"callbot {target_id} not found")
    callbot_id = str(match[0]["id"]) if match else None
    existing = client.rpc({"action": "list_tools", "callbotId": callbot_id}) if callbot_id else []
    by_name = {t["name"]: t for t in existing or []}
    # kiểm tra mọi điều kiện chặn trước khi ghi bất kỳ thứ gì
    for tool in tools:
        cur = by_name.get(tool["name"])
        if cur is not None and cur.get("kind") != tool["kind"]:
            raise SystemExit(f"tool {tool['name']}: kind {cur.get('kind')} -> {tool['kind']} cannot change; "
                             "delete it first or rename")
    print(("APPLYING" if do_apply else "DRY-RUN (add --apply to write)") + (f" callbot={callbot_id}" if callbot_id else ""),
          flush=True)
    if callbot_id:
        current = client.rpc({"action": "get_callbot", "callbotId": callbot_id})
        diff = callbot_diff(current, wanted)
        step(f"update callbot {callbot_id}: {sorted(diff)}" if diff else f"callbot {callbot_id} unchanged")
        if diff and do_apply:
            res = client.rpc({"action": "update_callbot", "callbotId": callbot_id,
                              "body": {**diff, "version": current["version"]}})
            step(f"  -> version {res.get('version')}")
    else:
        step(f"create callbot {wanted['name']!r}")
        if do_apply:
            res = client.rpc({"action": "create_callbot", "body": wanted})
            callbot_id = str(res["id"])
            step(f"  -> id {callbot_id} version {res.get('version')}")
    for tool in tools:
        cur = by_name.get(tool["name"])
        if cur is None:
            step(f"create tool {tool['name']} ({tool['kind']})")
            if do_apply:
                res = client.rpc({"action": "create_tool", "callbotId": callbot_id, "body": tool})
                step(f"  -> {res.get('id')}")
        elif tool_changed(cur, tool):
            step(f"update tool {tool['name']} ({cur['id']})")
            if do_apply:
                client.rpc({"action": "update_tool", "callbotId": callbot_id, "toolId": cur["id"], "body": tool})
        else:
            step(f"tool {tool['name']} unchanged")
    for tool in [t for t in existing or [] if t["name"] not in set(names)]:
        if prune:
            step(f"delete tool {tool['name']} ({tool['id']})")
            if do_apply:
                client.rpc({"action": "delete_tool", "callbotId": callbot_id, "toolId": tool["id"]})
        else:
            step(f"keep tool {tool['name']} (not in spec; use --prune to delete)")
    status = spec.get("status")
    if status and callbot_id:
        current = client.rpc({"action": "get_callbot", "callbotId": callbot_id})
        if current.get("status") != status:
            step(f"set status {status}")
            if do_apply:
                client.rpc({"action": "set_callbot_status", "callbotId": callbot_id, "body": {"status": status}})
    elif status and not do_apply:
        step(f"set status {status} (after create)")
    if do_apply and callbot_id:
        final = client.rpc({"action": "get_callbot", "callbotId": callbot_id})
        tools_now = client.rpc({"action": "list_tools", "callbotId": callbot_id})
        dump({"id": final["id"], "version": final["version"], "status": final["status"],
              "provider": final["provider"], "model": final["model"], "voice": final["voice"],
              "providerOptions": final.get("providerOptions"), "runAsPersonnelId": final.get("runAsPersonnelId"),
              "recordEnabled": final.get("recordEnabled"), "tools": [f"{t['name']} ({t['kind']})" for t in tools_now]})


# ---------------------------------------------------------------- simulate / sessions

def simulate(client: Client, callbot_id: str, says: list[str]) -> None:
    start = client.rpc({"action": "start_simulation", "callbotId": callbot_id, "body": {}})
    sim_id = start["simId"]
    print(f"[sim {sim_id}] bot: {start.get('reply', '')}")
    try:
        for text in says:
            print(f"caller: {text}")
            res = client.rpc({"action": "send_simulation_message", "simId": sim_id, "body": {"text": text}})
            for call in res.get("toolCalls") or []:
                result = json.dumps(call.get("result"), ensure_ascii=False)
                print(f"  tool {call['name']} {call.get('arguments')} -> {call.get('status')}"
                      f"{' (dry-run)' if call.get('dryRun') else ''} {result[:300]}")
            for reply in res.get("replies") or [res.get("reply", "")]:
                print(f"bot: {reply}")
            if res.get("ended"):
                print("[call ended by bot]")
                break
    finally:
        try:
            client.rpc({"action": "end_simulation", "simId": sim_id})
        except ApiError:
            pass


def sessions(client: Client, callbot_id: str, minutes: int) -> None:
    query = {"limit": "20", "callbotId": callbot_id, "from": str(int((time.time() - minutes * 60) * 1000))}
    data = client.rpc({"action": "list_sessions", "query": query})
    for row in data.get("items", []):
        print(json.dumps({k: row.get(k) for k in ("sessionId", "callId", "direction", "from", "to", "startedAt",
                                                   "botDurationSec", "endReason", "endBy", "outcome",
                                                   "toolCallCount")}, ensure_ascii=False))


def session(client: Client, session_id: str) -> None:
    d = client.rpc({"action": "get_session", "sessionId": session_id})
    print(json.dumps({k: d.get(k) for k in ("sessionId", "callId", "callbotId", "direction", "from", "to",
                                            "botDurationSec", "endReason", "endBy", "outcome")}, ensure_ascii=False))
    events = [(l["at"], f"{l['role']}: {l['text']}") for l in d.get("transcript") or []]
    events += [(t["at"], f"  [tool {t['name']} {t.get('status')} {t.get('latencyMs')}ms] {t.get('argsMasked') or ''}")
               for t in d.get("toolCalls") or []]
    for _, line in sorted(events, key=lambda e: e[0]):
        print(line)
    variables = {k: v for k, v in (d.get("variables") or {}).items() if not k.startswith("system.")}
    if variables:
        print("variables:", json.dumps(variables, ensure_ascii=False))
    for flag in d.get("securityFlags") or []:
        print("security flag:", json.dumps(flag, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env-file")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("rpc")
    p.add_argument("action")
    p.add_argument("--callbot")
    p.add_argument("--tool")
    p.add_argument("--sim")
    p.add_argument("--session")
    p.add_argument("--body", help="JSON or @file")
    p.add_argument("--query", help="JSON object of strings")
    p = sub.add_parser("bapi")
    p.add_argument("path")
    p.add_argument("--body", default="{}", help="JSON or @file")
    p.add_argument("--method", default="POST", choices=["POST", "PUT"])
    p = sub.add_parser("apply")
    p.add_argument("spec")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--prune", action="store_true", help="delete tools that are not in the spec")
    p = sub.add_parser("simulate")
    p.add_argument("--callbot", required=True)
    p.add_argument("--say", action="append", default=[])
    p = sub.add_parser("sessions")
    p.add_argument("--callbot", required=True)
    p.add_argument("--minutes", type=int, default=60)
    p = sub.add_parser("session")
    p.add_argument("session_id")
    args = parser.parse_args()
    client = Client(*load_credentials(args.env_file))
    try:
        if args.cmd == "rpc":
            if args.action in SECRET_ACTIONS and args.body and not args.body.startswith("@"):
                raise SystemExit("Pass secrets with --body @file (0600), never inline on the command line.")
            req: dict[str, Any] = {"action": args.action}
            for key, value in (("callbotId", args.callbot), ("toolId", args.tool), ("simId", args.sim),
                               ("sessionId", args.session)):
                if value:
                    req[key] = value
            if args.body:
                req["body"] = read_json(args.body)
            if args.query:
                req["query"] = read_json(args.query)
            dump(client.rpc(req))
        elif args.cmd == "bapi":
            dump(client.bapi(args.path, read_json(args.body), args.method))
        elif args.cmd == "apply":
            apply_spec(client, read_json("@" + args.spec), args.apply, args.prune)
        elif args.cmd == "simulate":
            simulate(client, args.callbot, args.say)
        elif args.cmd == "sessions":
            sessions(client, args.callbot, args.minutes)
        elif args.cmd == "session":
            session(client, args.session_id)
    except ApiError as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
