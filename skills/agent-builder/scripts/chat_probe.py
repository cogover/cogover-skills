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
    """Events of one user turn. Pass turn_id when the HTTP response returned it (service 11)."""
    session_id: str
    conversation_id: str
    turn_id: str | None = None
    seen: set = field(default_factory=set)
    final_texts: list = field(default_factory=list)
    completed: bool = False
    error: str | None = None
    turn_from_http: bool = field(init=False, default=False)

    def __post_init__(self):
        self.turn_from_http = self.turn_id is not None

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
            turn = custom.get("turnId")
            if not self.turn_from_http:
                # Service 10: priming/welcome events carry no user-message id and are not the
                # tested turn; the first user message carries userMsgChatServerId.
                if not custom.get("userMsgChatServerId"):
                    if event == "LOOP_ERROR":
                        self.error = "AGENT_START_ERROR"
                    continue
                if not turn:
                    self.error = "TURN_ID_MISSING_API_CONTRACT_REQUIRED"
                    continue
                if self.turn_id is None:
                    self.turn_id = turn
            # Service 11 events carry userMsgSeqId and turnId, never userMsgChatServerId.
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


def turn_summary(turn):
    return {"turnId": turn.turn_id, "completed": turn.completed, "expectedTextMatched": turn.passed,
            "error": turn.error or (None if turn.passed else "UNEXPECTED_FINAL_TEXT")}


def live_probe(agent_id, timeout, effort, follow_up=False):
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
    result = follow = None
    stage = "first-turn"
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

    def wait_for(turn):
        while True:
            frame = receive()
            if frame:
                turn.accept(frame)
                if turn.error or (turn.completed and turn.final_texts):
                    return

    def send(service, payload):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProbeError("CHAT_TIMEOUT_BEFORE_" + stage.upper().replace("-", "_"))
        if effort:
            payload["reasoning"] = {"enabled": True, "effort": effort}
        return result_body(post_json(origin + "/api/v1/ai-agent",
            {**headers, "x-req-type": "1", "x-req-service": service}, payload, min(45, remaining)))

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
        # Service 10 response has no turnId: the turn is locked from its events.
        data = send("10", {"agentId": agent_id, "message": MESSAGE}).get("data") or {}
        if not data.get("chatSessionId") or not data.get("chatServerConvId"):
            raise ProbeError("START_RESPONSE_MISSING_CONVERSATION_IDS")
        result = TurnResult(data["chatSessionId"], data["chatServerConvId"])
        wait_for(result)
        output = {"passed": result.passed, "chatSessionId": result.session_id,
                  "chatServerConvId": result.conversation_id, **turn_summary(result)}
        if not follow_up or not result.passed:
            return output
        # Service 11 returns the turnId; its events are filtered by that turnId.
        stage = "follow-up"
        turn_id = (send("11", {"chatSessionId": result.session_id, "message": MESSAGE}).get("data") or {}).get("turnId")
        if not isinstance(turn_id, str) or not turn_id:
            raise ProbeError("FOLLOW_UP_TURN_ID_MISSING")
        follow = TurnResult(result.session_id, result.conversation_id, turn_id)
        wait_for(follow)
        output["followUp"] = turn_summary(follow)
        output["passed"], output["error"] = follow.passed, output["followUp"]["error"]
        return output
    except ProbeError as exc:
        if result is None:
            raise
        partial = {"passed": False, "error": str(exc), "retried": False, "stage": stage,
                   "chatSessionId": result.session_id, "chatServerConvId": result.conversation_id,
                   "turnId": result.turn_id, "completed": result.completed}
        if follow is not None:
            partial["followUp"] = {"turnId": follow.turn_id, "completed": follow.completed}
        return partial
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
              text=None, final=False, status="COMPLETED", as_string=True,
              user_message="user-message-example", user_seq=1):
        # user_message=None models priming events (no user-message id, user_seq=None) and
        # service 11 turns (userMsgSeqId + turnId, no userMsgChatServerId).
        custom = {"chatSessionId": "session-example", "turnId": turn, "agentMessageType": event,
                  "isFinalResponse": final, "status": status}
        if user_message is not None:
            custom["userMsgChatServerId"] = user_message
        if user_seq is not None:
            custom["userMsgSeqId"] = user_seq
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
    # Service 10: priming/welcome events are skipped; the turn locks on the first user message.
    primed = TurnResult("session-example", "conversation-example")
    primed.accept(frame("LOOP_OUTPUT", "welcome", turn="priming-turn", text=EXPECTED, final=True,
                        user_message=None, user_seq=None))
    primed.accept(frame("LOOP_COMPLETE", "welcome-complete", turn="priming-turn", user_message=None, user_seq=None))
    assert not primed.seen and primed.turn_id is None and not primed.completed
    primed.accept(output)
    primed.accept(done)
    assert primed.passed and primed.turn_id == "turn-example"
    start_error = TurnResult("session-example", "conversation-example")
    start_error.accept(frame("LOOP_ERROR", "welcome-error", turn=None, user_message=None, user_seq=None))
    assert start_error.error == "AGENT_START_ERROR"
    # Service 11: events have the turnId of the HTTP response and no userMsgChatServerId.
    follow = TurnResult("session-example", "conversation-example", "turn-follow-up")
    follow.accept(frame("LOOP_OUTPUT", "late-first-turn", text="wrong", final=True))
    follow.accept(frame("LOOP_OUTPUT", "follow-final", turn="turn-follow-up", text=EXPECTED, final=True,
                        user_message=None, user_seq=2))
    follow.accept(frame("LOOP_COMPLETE", "follow-complete", turn="turn-follow-up", user_message=None, user_seq=2))
    assert follow.passed and follow.final_texts == [EXPECTED] and follow.turn_id == "turn-follow-up"
    later = TurnResult("session-example", "conversation-example", "turn-follow-up")
    later.accept(frame("LOOP_COMPLETE", "turnless", turn=None, user_message=None, user_seq=2))
    later.accept(frame("LOOP_ERROR", "next-turn", turn="turn-next", user_message=None, user_seq=3))
    assert not later.seen and not later.completed and not later.error
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
    parser.add_argument("--follow-up", action="store_true",
                        help="after a passing first turn, send one more turn (service 11) in the same conversation")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.agent_id or not 10 <= args.timeout <= 600:
        parser.error("--agent-id is required and --timeout must be between 10 and 600 seconds")
    try:
        result = live_probe(args.agent_id, args.timeout, args.reasoning_effort, args.follow_up)
    except ProbeError as exc:
        result = {"passed": False, "error": str(exc), "retried": False}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
