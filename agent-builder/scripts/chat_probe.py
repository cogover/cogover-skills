#!/usr/bin/env python3
"""One authenticated Workspace chat smoke test; never save credentials or raw frames."""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field

EXPECTED = "AGENT_BUILDER_OK"
MESSAGE = "Reply exactly AGENT_BUILDER_OK. Do not call tools or change data."


class ProbeError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeError("HTTP_REDIRECT_REFUSED")


def result_body(value):
    if not isinstance(value, dict):
        raise ProbeError("INVALID_RESPONSE_SHAPE")
    if "r" in value and value["r"] != 0:
        code = value["r"] if isinstance(value["r"], int) else "UNKNOWN"
        raise ProbeError(f"API_ERROR_{code}")
    body = value.get("body", value)
    if not isinstance(body, dict) or "r" not in body:
        raise ProbeError("MISSING_RESULT_CODE")
    if body["r"] != 0:
        code = body["r"] if isinstance(body["r"], int) else "UNKNOWN"
        raise ProbeError(f"API_ERROR_{code}")
    return body


def post_json(url, headers, payload, timeout):
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                    headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            content = response.read(2_000_001)
            if len(content) > 2_000_000:
                raise ProbeError("HTTP_RESPONSE_TOO_LARGE")
            return json.loads(content)
    except urllib.error.HTTPError as exc:
        raise ProbeError(f"HTTP_{exc.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise ProbeError("HTTP_CONNECTION_FAILED_OR_TIMED_OUT") from None
    except (ValueError, UnicodeError):
        raise ProbeError("INVALID_RESPONSE_JSON") from None


def origin_from_env():
    raw = os.environ.get("COGOVER_BASE_URL", "").strip()
    if not raw:
        raise ProbeError("MISSING_COGOVER_BASE_URL")
    if "://" not in raw:
        raw = "https://" + raw
    url = urllib.parse.urlsplit(raw)
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.path not in ("", "/") or url.query or url.fragment):
        raise ProbeError("EXPECTED_HTTPS_WORKSPACE_ORIGIN")
    return urllib.parse.urlunsplit(("https", url.netloc, "", "", ""))


def make_session(origin, timeout):
    key = os.environ.get("COGOVER_API_KEY", "")
    if not key:
        raise ProbeError("MISSING_COGOVER_API_KEY")
    if "\r" in key or "\n" in key:
        raise ProbeError("INVALID_CREDENTIAL_FORMAT")
    result = post_json(origin + "/bapi/v1/auth-token", {"Authorization": "Bearer " + key}, {}, timeout)
    session = result_body(result).get("data", {})
    hostname = urllib.parse.urlsplit(origin).hostname.lower()
    domain, workspace_id = result.get("workspaceDomain"), result.get("workspaceId")
    if not isinstance(domain, str) or not domain or not workspace_id:
        raise ProbeError("MISSING_WORKSPACE_BINDING")
    normalized = domain.lower().removeprefix("https://").removeprefix("http://").rstrip("/")
    if normalized != (hostname if "." in normalized else hostname.split(".")[0]):
        raise ProbeError("WORKSPACE_BINDING_MISMATCH")
    names = ("HttpSessionId", "XSRF-TOKEN", "AuthToken")
    if not isinstance(session, dict) or any(not isinstance(session.get(n), str) or not session[n] for n in names):
        raise ProbeError("MISSING_SESSION_COOKIES")
    if any(any(c in session[n] for c in ("\r", "\n", ";")) for n in names):
        raise ProbeError("INVALID_SESSION_COOKIE_FORMAT")
    for name in ("HttpSessionExpiresAt", "AuthTokenExpiresAt"):
        expires = session.get(name)
        if not isinstance(expires, (int, float)) or expires <= time.time() + timeout + 10:
            raise ProbeError("SESSION_EXPIRY_TOO_CLOSE")
    return {"Cookie": "; ".join(n + "=" + session[n] for n in names),
            "x-csrf-token": session["XSRF-TOKEN"], "x-xsrf-token": session["XSRF-TOKEN"]}, workspace_id


def decode_object(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, UnicodeError):
            return None
    return value if isinstance(value, dict) else None


@dataclass
class TurnResult:
    session_id: str
    conversation_id: str
    turn_id: str | None = None
    seen: set = field(default_factory=set)
    final_texts: list = field(default_factory=list)
    completed: bool = False
    error: str | None = None

    def accept(self, frame):
        if frame.get("type") != 2 or frame.get("service") != 116:
            return
        body = decode_object(frame.get("body")) or {}
        messages = body.get("messages", [])
        if body.get("object_type") != "message" or not isinstance(messages, list):
            return
        for message in messages:
            if (not isinstance(message, dict) or message.get("part_type") != 3
                    or message.get("conversation_id") != self.conversation_id):
                continue
            custom = decode_object(message.get("custom_data"))
            if not custom or custom.get("chatSessionId") != self.session_id:
                continue
            event = custom.get("agentMessageType")
            # Priming/welcome events do not represent the user turn being tested.
            if not custom.get("userMsgChatServerId"):
                if event == "LOOP_ERROR":
                    self.error = "AGENT_START_ERROR"
                continue
            turn = custom.get("turnId")
            if not turn:
                self.error = "TURN_ID_MISSING_API_CONTRACT_REQUIRED"
                continue
            if self.turn_id is None:
                self.turn_id = turn
            if turn != self.turn_id:
                continue
            identifier = message.get("id")
            if not identifier:
                self.error = "MESSAGE_ID_MISSING"
                continue
            if identifier in self.seen:
                continue
            self.seen.add(identifier)
            block = decode_object(custom.get("data")) or {}
            if event == "LOOP_ERROR":
                self.error = "AGENT_LOOP_ERROR"
            elif event == "TOOL_APPROVAL_REQUEST":
                self.error = "TOOL_APPROVAL_REQUIRED"
            elif event == "LOOP_OUTPUT" and block.get("type") == "TOOL_USE":
                self.error = "UNEXPECTED_TOOL_USE_IN_SMOKE_TEST"
            elif event == "LOOP_OUTPUT" and custom.get("isFinalResponse") is True and block.get("type") == "TEXT":
                if isinstance(block.get("text"), str):
                    self.final_texts.append(block["text"])
            elif event == "LOOP_COMPLETE":
                self.completed = True
                if custom.get("status") != "COMPLETED":
                    self.error = "TURN_NOT_COMPLETED_SUCCESSFULLY"

    @property
    def passed(self):
        return (not self.error and self.completed and bool(self.final_texts)
                and "\n".join(self.final_texts).strip() == EXPECTED)


def live_probe(agent_id, timeout, effort):
    try:
        import websocket
    except ImportError:
        raise ProbeError("MISSING_DEPENDENCY_websocket-client") from None
    if not hasattr(websocket, "create_connection"):
        raise ProbeError("EXPECTED_PACKAGE_websocket-client")
    origin = origin_from_env()
    headers, workspace_id = make_session(origin, timeout)
    client_id, request_id = "web-" + str(uuid.uuid4()), 1
    sock = None
    result = None
    deadline = time.monotonic() + timeout

    def receive():
        nonlocal request_id
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProbeError("CHAT_TIMEOUT")
        sock.settimeout(min(5, remaining))
        try:
            raw = sock.recv()
        except websocket.WebSocketTimeoutException:
            return None
        if not raw:
            raise ProbeError("WEBSOCKET_CLOSED_NO_RETRY")
        if len(raw) > 2_000_000:
            raise ProbeError("WEBSOCKET_FRAME_TOO_LARGE")
        frame = decode_object(raw)
        if frame and frame.get("type") == 1 and frame.get("service") == 0:
            request_id += 1
            sock.send(json.dumps({"id": request_id, "type": 1, "serviceVersion": 1,
                                  "service": 0, "from": client_id, "body": None}))
            return None
        return frame

    try:
        sock = websocket.create_connection(
            "wss://" + urllib.parse.urlsplit(origin).netloc + "/websocket",
            cookie=headers["Cookie"], origin=origin, timeout=min(30, timeout), redirect_limit=0,
        )
        sock.send(json.dumps({"id": 1, "type": 2, "serviceVersion": 1, "service": 1,
                              "from": client_id, "body": {"isVisitor": False}}))
        while True:
            frame = receive()
            if not frame or (frame.get("id"), frame.get("type"), frame.get("service")) != (1, 2, 1):
                continue
            auth = result_body(frame)
            actual_workspace = (auth.get("data") or {}).get("workspace", {}).get("id")
            if actual_workspace != workspace_id:
                raise ProbeError("WEBSOCKET_WORKSPACE_MISMATCH")
            break
        payload = {"agentId": agent_id, "message": MESSAGE}
        if effort:
            payload["reasoning"] = {"enabled": True, "effort": effort}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProbeError("CHAT_TIMEOUT_BEFORE_START")
        started = result_body(post_json(origin + "/api/v1/ai-agent",
            {**headers, "x-req-type": "1", "x-req-service": "10"}, payload, min(45, remaining)))
        data = started.get("data") or {}
        if not data.get("chatSessionId") or not data.get("chatServerConvId"):
            raise ProbeError("START_RESPONSE_MISSING_CONVERSATION_IDS")
        result = TurnResult(data["chatSessionId"], data["chatServerConvId"])
        while True:
            frame = receive()
            if not frame:
                continue
            result.accept(frame)
            if result.error or (result.completed and result.final_texts):
                break
        return {"passed": result.passed, "chatSessionId": result.session_id,
                "chatServerConvId": result.conversation_id, "turnId": result.turn_id,
                "completed": result.completed, "expectedTextMatched": result.passed,
                "error": result.error or (None if result.passed else "UNEXPECTED_FINAL_TEXT")}
    except ProbeError as exc:
        if result is None:
            raise
        return {"passed": False, "error": str(exc), "retried": False,
                "chatSessionId": result.session_id, "chatServerConvId": result.conversation_id,
                "turnId": result.turn_id, "completed": result.completed}
    except Exception:
        # Transport exceptions may contain handshake headers; never print them.
        raise ProbeError("WEBSOCKET_OR_PROTOCOL_ERROR_NO_RETRY") from None
    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass


def self_test():
    def frame(event, identifier, *, conversation="conversation-example", turn="turn-example",
              text=None, final=False, status="COMPLETED", as_string=True):
        custom = {"chatSessionId": "session-example", "turnId": turn,
                  "userMsgChatServerId": "user-message-example", "agentMessageType": event,
                  "isFinalResponse": final, "status": status}
        if text is not None:
            custom["data"] = {"type": "TEXT", "text": text}
        return {"type": 2, "service": 116, "body": {"object_type": "message", "messages": [
            {"id": identifier, "part_type": 3, "conversation_id": conversation,
             "custom_data": json.dumps(custom) if as_string else custom}]}}

    output = frame("LOOP_OUTPUT", "message-final", text=EXPECTED, final=True)
    done = frame("LOOP_COMPLETE", "message-complete")
    state = TurnResult("session-example", "conversation-example")
    spoofed = frame("LOOP_OUTPUT", "user-echo", text=EXPECTED, final=True)
    spoofed["body"]["messages"][0]["part_type"] = 1
    state.accept(spoofed)
    assert not state.seen and not state.final_texts
    state.accept(frame("LOOP_OUTPUT", "foreign", conversation="another-conversation", text="wrong", final=True))
    state.accept(frame("LOOP_OUTPUT", "message-progress", text="working", final=False))
    state.accept(output)
    state.accept(output)
    assert not state.passed and state.final_texts == [EXPECTED]
    state.accept(frame("LOOP_ERROR", "foreign-turn", turn="another-turn"))
    state.accept(done)
    assert state.passed
    state.accept(frame("LOOP_ERROR", "message-error"))
    assert not state.passed and state.error == "AGENT_LOOP_ERROR"
    for event, status in (("TOOL_APPROVAL_REQUEST", "COMPLETED"), ("LOOP_COMPLETE", "CANCELLED")):
        blocked = TurnResult("session-example", "conversation-example")
        blocked.accept(output)
        blocked.accept(frame(event, "message-terminal", status=status, as_string=False))
        assert not blocked.passed and blocked.error
    empty = TurnResult("session-example", "conversation-example")
    empty.accept(done)
    assert not empty.passed
    empty.accept(output)
    assert empty.passed
    old = TurnResult("session-example", "conversation-example")
    old.accept(frame("LOOP_COMPLETE", "old-message", turn=None))
    assert old.error == "TURN_ID_MISSING_API_CONTRACT_REQUIRED"
    assert result_body({"body": {"r": 0, "data": []}})["data"] == []
    for invalid in ({"body": {"r": 4}}, {"r": 5, "body": {"r": 0}}, {}):
        try:
            result_body(invalid)
        except ProbeError:
            pass
        else:
            raise AssertionError("Invalid API response accepted")
    print(json.dumps({"passed": True, "mode": "offline-self-test", "networkUsed": False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--agent-id")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--reasoning-effort")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.agent_id or not 10 <= args.timeout <= 600:
        parser.error("--agent-id is required and --timeout must be between 10 and 600 seconds")
    try:
        result = live_probe(args.agent_id, args.timeout, args.reasoning_effort)
    except ProbeError as exc:
        result = {"passed": False, "error": str(exc), "retried": False}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
