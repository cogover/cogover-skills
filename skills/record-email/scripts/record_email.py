#!/usr/bin/env python3
"""Send a Cogover Email Template to individual records, the same way as the record's "Compose Email".

Commands (all read-only except `send --apply`):
  mailboxes  Shared Workspace mailboxes that have already sent email (ID, address, display name).
  templates  Email Templates with subject and the {$record.*} variables they contain.
  layouts    Email Layouts (wrap the template body at {$currentContent}).
  recipients Records of a saved filter (link, ID or slug), optionally written to an ID file.
  send       Render the template per record and send it. Dry-run unless --apply.
  status     Delivery status and opens of emails sent with a template.

Credentials: COGOVER_BASE_URL + COGOVER_API_KEY (or WORKSPACE_DOMAIN + API_KEY). When they
are not set, the KEY=VALUE lines of ./.env (or --env-file) are read for those names only.
"""

from __future__ import annotations

import argparse
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

CONTENT_SLOT = "{$currentContent}"
RECORD_VAR = re.compile(r"\{\$record\.([A-Za-z0-9_.]+)\}")
ANY_VAR = re.compile(r"\{\$[A-Za-z0-9_.]+\}")
CONTEXT = ssl.create_default_context()


# ---------------------------------------------------------------- transport

def load_credentials(env_file: str | None) -> tuple[str, str]:
    names = ("COGOVER_BASE_URL", "COGOVER_WORKSPACE_DOMAIN", "WORKSPACE_DOMAIN", "COGOVER_API_KEY", "API_KEY")
    values = {n: os.environ[n] for n in names if os.environ.get(n)}
    path = Path(env_file or ".env")
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\s*([A-Z_]+)\s*=\s*(.*?)\s*$", line)
            if match and match.group(1) in names and match.group(1) not in values:
                values[match.group(1)] = match.group(2).strip("'\"")
    base = values.get("COGOVER_BASE_URL") or values.get("COGOVER_WORKSPACE_DOMAIN") or values.get("WORKSPACE_DOMAIN")
    key = values.get("COGOVER_API_KEY") or values.get("API_KEY")
    if not base or not key:
        raise SystemExit("Missing COGOVER_BASE_URL/COGOVER_API_KEY (or WORKSPACE_DOMAIN/API_KEY).")
    if not base.startswith(("http://", "https://")):
        base = "https://" + base
    return base.rstrip("/"), key


def call(url: str, body: Any, headers: dict[str, str], method: str = "POST") -> tuple[int, Any]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method,
                                     headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=60, context=CONTEXT) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "replace")
        try:
            return error.code, json.loads(raw)
        except json.JSONDecodeError:
            return error.code, {"raw": raw[:500]}


class Client:
    def __init__(self, base: str, api_key: str):
        self.base = base
        self.bearer = {"Authorization": "Bearer " + api_key}
        self._session: dict[str, str] | None = None

    def records(self, object_slug: str, filters: list[dict], limit: int = 1000, kind: int = 1, logic: str = "") -> list[dict]:
        rows: list[dict] = []
        search_after: list = []
        while len(rows) < limit:
            status, data = call(self.base + "/bapi/v1/records/list", {
                "object_slug": object_slug, "type": kind, "logic_sequence": logic, "filters": filters,
                "sorts": [{"created": {"order": "desc"}}], "order_direction": "next",
                "search_after": search_after, "size": 100, "show_detail_on_record": False,
            }, self.bearer)
            if status != 200 or not data or data.get("r") != 0:
                raise RuntimeError(f"records/list {object_slug}: HTTP {status} r={data and data.get('r')} {data and data.get('msg')}")
            page = data["data"].get("rows") or []
            rows.extend(page)
            search_after = data["data"].get("search_after") or []
            if not page or not search_after or len(page) < 100:
                break
        return rows[:limit]

    def record(self, object_slug: str, record_id: str) -> dict | None:
        rows = self.records(object_slug, [{"field": "id", "op": "=", "params": record_id, "fieldType": "short_text"}], 1)
        return rows[0] if rows else None

    def session(self) -> dict[str, str]:
        if self._session is None:
            status, data = call(self.base + "/bapi/v1/auth-token", {}, self.bearer)
            info = (data or {}).get("data") or {}
            if status != 200 or data.get("r") != 0 or not all(info.get(k) for k in ("HttpSessionId", "XSRF-TOKEN", "AuthToken")):
                raise RuntimeError(f"auth-token failed: HTTP {status} r={data and data.get('r')} {data and data.get('msg')}")
            xsrf = info["XSRF-TOKEN"]
            self._session = {
                "Accept": "application/json, text/plain, */*",
                "Cookie": f"HttpSessionId={info['HttpSessionId']}; XSRF-TOKEN={xsrf}; AuthToken={info['AuthToken']}",
                "x-csrf-token": xsrf, "x-xsrf-token": xsrf,
            }
        return self._session

    def choice_labels(self, object_slug: str) -> dict[str, dict[str, str]]:
        """Every field slug of the Object -> {option slug: label} (empty for non-choice fields)."""
        status, data = call(self.base + "/api/v1/objects/object/get-by-slug", {"slug": object_slug, "withFields": 1}, self.session())
        info = (data or {}).get("data")
        info = info[0] if isinstance(info, list) and info else info
        if status != 200 or not isinstance(info, dict):
            return {}
        return {f["slug"]: {o.get("slug"): o.get("value") for o in f.get("options") or []}
                for f in info.get("fields") or [] if f.get("slug")}

    def object_id(self, object_slug: str) -> str | None:
        status, data = call(self.base + "/api/v1/objects/object/get-by-slug", {"slug": object_slug, "withFields": 0}, self.session())
        info = (data or {}).get("data")
        info = info[0] if isinstance(info, list) and info else info
        return info.get("id") if status == 200 and isinstance(info, dict) else None

    def saved_filter(self, filter_id: str) -> dict | None:
        status, data = call(self.base + "/bapi/v1/filters/view", {"id": filter_id}, self.bearer)
        return data.get("data") if status == 200 and data and data.get("r") == 0 else None

    def saved_filters(self, object_type_id: str) -> list[dict]:
        status, data = call(self.base + "/bapi/v1/filters/list", {"objectTypeId": object_type_id, "objectTypeIdOperator": "IN", "page": 1, "limit": 200}, self.bearer)
        rows = (data or {}).get("data") or []
        return rows if isinstance(rows, list) else rows.get("rows") or []

    def compose_email(self, payload: dict, app_slug: str) -> tuple[int, Any]:
        headers = {**self.session(), "x-req-service": "7", "x-req-type": "9", "x-app-slug": app_slug}
        return call(self.base + "/api/v1/dashboard-server", payload, headers)


# ---------------------------------------------------------------- helpers

def parse_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def resolve_path(record: dict, path: str, labels: dict[str, dict[str, str]] | None = None) -> str | None:
    if path.startswith("text:"):
        return path[5:]
    value: Any = record
    options = (labels or {}).get(path.split(".")[0]) if "." not in path else None
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    if value is None:
        return None
    if options and isinstance(value, (str, list)):
        value = [options.get(v, v) for v in value] if isinstance(value, list) else options.get(value, value)
    if isinstance(value, list):
        return ", ".join(str(v.get("name", v)) if isinstance(v, dict) else str(v) for v in value if v not in (None, ""))
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or "")
    return str(value)


def render(text: str, record: dict, extra: list[tuple[str, str]], labels: dict[str, dict[str, str]]) -> str:
    def replace(match: re.Match) -> str:
        value = resolve_path(record, match.group(1), labels)
        if value is None and match.group(1).split(".")[0] in labels:
            return ""  # field exists but is empty on this record
        return match.group(0) if value is None else value
    text = RECORD_VAR.sub(replace, text)
    for placeholder, field in extra:
        value = resolve_path(record, field, labels)
        if value is not None:
            text = text.replace(placeholder, value)
    return text


def mailbox_list(client: Client, limit: int) -> list[dict]:
    rows = client.records("email_message", [{"field": "from", "op": "like", "params": '"type":"workspace"', "fieldType": "long_text"}], limit)
    boxes: dict[str, dict] = {}
    for row in rows:
        sender = parse_json(row.get("from")) or {}
        if not isinstance(sender, dict) or sender.get("type") != "workspace" or not sender.get("id"):
            continue
        box = boxes.setdefault(sender["id"], {"id": sender["id"], "email": sender.get("email"), "name": sender.get("name"), "sent": 0, "last": 0})
        box["sent"] += 1
        box["last"] = max(box["last"], row.get("created") or 0)
    return sorted(boxes.values(), key=lambda b: -b["last"])


def parse_filter_ref(ref: str) -> tuple[str | None, str]:
    """Filter link, ID or slug -> (object slug from the link or None, filter ID or slug)."""
    ref = ref.strip()
    object_slug = None
    match = re.search(r"/o/([A-Za-z0-9_]+)", ref)
    if match:
        object_slug = match.group(1)
    match = re.search(r"[?&]filter=([A-Za-z0-9_-]+)", ref) or re.search(r"/filter/([A-Za-z0-9_-]+)", ref)
    return object_slug, (match.group(1) if match else ref)


def filter_records(client: Client, ref: str, object_slug: str | None, limit: int) -> tuple[str, dict, list[dict]]:
    link_object, key = parse_filter_ref(ref)
    if link_object and object_slug and link_object != object_slug:
        raise SystemExit(f"Filter link is for Object '{link_object}' but --object is '{object_slug}'.")
    object_slug = link_object or object_slug or "contact"
    object_type_id = client.object_id(object_slug)
    if not object_type_id:
        raise SystemExit(f"Object '{object_slug}' not found.")
    found = client.saved_filter(key) if key.startswith("FI") else None
    if not found:
        matches = [f for f in client.saved_filters(object_type_id) if key in (f.get("id"), f.get("slug"))]
        found = client.saved_filter(matches[0]["id"]) if len(matches) == 1 else None
    if not found:
        raise SystemExit(f"Saved filter '{key}' not found on Object '{object_slug}'.")
    if found.get("objectTypeId") and found["objectTypeId"] != object_type_id:
        raise SystemExit(f"Saved filter '{key}' belongs to another Object.")
    conditions = found.get("conditions") or []
    logic_type = (found.get("logicType") or "AND").upper()
    kind = {"AND": 1, "OR": 2}.get(logic_type, 3)
    rows = client.records(object_slug, conditions or [{"field": "id", "op": "not null", "params": None, "fieldType": "short_text"}],
                          limit, kind=kind, logic=found.get("logic") or "")
    return object_slug, found, rows


def describe_filter(found: dict, total: int) -> str:
    note = f"Filter: {found.get('name')} ({found.get('id')}) | {total} records"
    if "$currentUser" in json.dumps(found.get("conditions") or []):
        note += "\nWARNING: this filter uses $currentUser, which resolves to the owner of the API Key, not to the person reading the link."
    return note


def fmt_time(ms: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ms / 1000)) if ms else ""


# ---------------------------------------------------------------- commands

def cmd_mailboxes(client: Client, args: argparse.Namespace) -> int:
    boxes = mailbox_list(client, args.scan)
    if not boxes:
        print("No shared mailbox found in sent emails. Send one email from the record's Compose Email first.")
        return 1
    for b in boxes:
        print(f"{b['id']}\t{b['email']}\t{b['name'] or ''}\tsent={b['sent']}\tlast={fmt_time(b['last'])}")
    return 0


def cmd_templates(client: Client, args: argparse.Namespace) -> int:
    filters = [{"field": "name", "op": "like", "params": args.search, "fieldType": "short_text"}] if args.search \
        else [{"field": "id", "op": "not null", "params": None, "fieldType": "short_text"}]
    for t in client.records("email_template", filters, 500):
        variables = sorted(set(ANY_VAR.findall((t.get("subject") or "") + (t.get("content") or ""))))
        print(f"{t['id']}\t{t.get('name')}\tsubject={t.get('subject')}\tobjects={t.get('related_object') or []}\tvars={variables}")
    return 0


def cmd_layouts(client: Client, args: argparse.Namespace) -> int:
    for l in client.records("email_layout", [{"field": "id", "op": "not null", "params": None, "fieldType": "short_text"}], 200):
        print(f"{l['id']}\t{l.get('name')}\thas_slot={CONTENT_SLOT in (l.get('content') or '')}")
    return 0


def already_sent(client: Client, template_id: str, record_id: str) -> list[dict]:
    rows = client.records("email_message", [
        {"field": "template", "op": "=", "params": template_id, "fieldType": "short_text"},
        {"field": "to_meta", "op": "like", "params": record_id, "fieldType": "long_text"},
    ], 20)
    return [r for r in rows if r.get("send_status") != "error"]


def cmd_send(client: Client, args: argparse.Namespace) -> int:
    ids = [i.strip() for i in (args.ids or "").split(",") if i.strip()]
    if args.ids_file:
        ids += [l.strip() for l in Path(args.ids_file).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.filter:
        args.object, found, rows = filter_records(client, args.filter, args.object, args.max + 1)
        print(describe_filter(found, len(rows)))
        ids += [r["id"] for r in rows]
    args.object = args.object or "contact"
    if not args.related_field:
        args.related_field = "contacts" if args.object == "contact" else args.object
    ids = list(dict.fromkeys(ids))
    if not ids:
        raise SystemExit("No records (--ids / --ids-file / --filter).")
    if len(ids) > args.max:
        raise SystemExit(f"{len(ids)} records exceeds --max {args.max}. Split the list or raise --max deliberately.")

    template = client.record("email_template", args.template)
    if not template:
        raise SystemExit(f"Email Template {args.template} not found.")
    sender = args.sender
    if "@" in sender:
        match = [b for b in mailbox_list(client, 2000) if (b["email"] or "").lower() == sender.lower()]
        if not match:
            raise SystemExit(f"No shared mailbox with address {sender} found in sent emails; pass its ID instead.")
        sender = match[0]["id"]
    body = template.get("content") or ""
    if args.layout:
        layout = client.record("email_layout", args.layout)
        if not layout or CONTENT_SLOT not in (layout.get("content") or ""):
            raise SystemExit(f"Email Layout {args.layout} not found or has no {CONTENT_SLOT}.")
        body = layout["content"].replace(CONTENT_SLOT, body)
    if args.signature_file:
        body += "\n" + Path(args.signature_file).read_text(encoding="utf-8")
    extra = [tuple(v.split("=", 1)) for v in args.var]
    labels = client.choice_labels(args.object)

    print(f"Template: {template.get('name')} | subject: {template.get('subject')}")
    print(f"From mailbox: {sender} | object: {args.object} | records: {len(ids)} | {'SEND' if args.apply else 'DRY-RUN'}\n")
    counts = {"sent": 0, "ready": 0, "skipped": 0, "error": 0}
    for index, record_id in enumerate(ids):
        record = client.record(args.object, record_id)
        if not record:
            print(f"ERROR   {record_id}: record not found in {args.object}"); counts["error"] += 1; continue
        to = [e for e in (record.get("emails") or []) if e] if isinstance(record.get("emails"), list) else \
            [record["emails"]] if record.get("emails") else []
        label = f"{record_id} {record.get('name')} <{', '.join(to)}>"
        if not to:
            print(f"SKIP    {label}: no email"); counts["skipped"] += 1; continue
        if not args.allow_resend:
            previous = already_sent(client, args.template, record_id)
            if previous:
                print(f"SKIP    {label}: template already sent {fmt_time(previous[0].get('created') or 0)}"); counts["skipped"] += 1; continue
        subject = render(template.get("subject") or "", record, extra, labels)
        content = render(body, record, extra, labels)
        leftover = sorted(set(ANY_VAR.findall(subject + content)) - {CONTENT_SLOT})
        if leftover and not args.allow_unresolved:
            print(f"ERROR   {label}: unresolved {leftover}"); counts["error"] += 1; continue
        if args.preview and counts["ready"] + counts["sent"] == 0:
            Path(args.preview).write_text(f"<!-- Subject: {subject} -->\n{content}", encoding="utf-8")
        if not args.apply:
            print(f"READY   {label} | {subject}"); counts["ready"] += 1; continue
        payload = {
            "recordId": record_id, "objectTypeSlug": args.object, "type": "email", "clientTimeZone": args.timezone,
            "data": {
                "subject": subject, "from": {"id": sender, "type": "workspace"}, "contentType": "rich_text_editor",
                "content": content, "sendEmail": True,
                "to": [{"recordId": record_id, "objectTypeSlug": args.object, "value": to}],
                "cc": [], "bcc": [], "template": args.template, "emailLayout": args.layout or None, "files": None,
                "relatedObjectRecords": [{"fieldSlug": args.related_field, "recordIds": [record_id]}],
                "time": None, "sendReminder": None, "_attachments": None,
            },
        }
        status, data = client.compose_email(payload, args.app_slug)
        if status == 200 and data and data.get("r") == 0:
            print(f"SENT    {label}"); counts["sent"] += 1
        else:
            print(f"ERROR   {label}: HTTP {status} r={data and data.get('r')} {data and data.get('msg')}"); counts["error"] += 1
        if index < len(ids) - 1:
            time.sleep(args.delay)
    print("\n" + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 1 if counts["error"] else 0


def cmd_recipients(client: Client, args: argparse.Namespace) -> int:
    object_slug, found, rows = filter_records(client, args.filter, args.object, args.limit)
    print(describe_filter(found, len(rows)) + f" | Object: {object_slug}")
    no_email = 0
    for row in rows:
        emails = row.get("emails") if isinstance(row.get("emails"), list) else [row.get("emails")] if row.get("emails") else []
        no_email += not emails
        print(f"{row['id']}\t{row.get('name')}\t{', '.join(e for e in emails if e) or '(no email)'}")
    if args.out:
        Path(args.out).write_text("\n".join(r["id"] for r in rows) + "\n", encoding="utf-8")
    print(f"\n{len(rows)} records, {len(rows) - no_email} with email, {no_email} without email"
          + (f" (limit {args.limit} reached)" if len(rows) >= args.limit else ""))
    return 0


def cmd_status(client: Client, args: argparse.Namespace) -> int:
    filters = [{"field": "template", "op": "=", "params": args.template, "fieldType": "short_text"}]
    if args.since:
        filters.append({"field": "created", "op": ">=", "params": int(time.mktime(time.strptime(args.since, "%Y-%m-%d")) * 1000), "fieldType": "date_time"})
    rows = client.records("email_message", filters, 2000)
    wanted = set(i.strip() for i in (args.ids or "").split(",") if i.strip())
    summary: dict[str, int] = {}
    for row in rows:
        meta = parse_json(row.get("to_meta")) or []
        record_ids = [m.get("recordId") for m in meta if isinstance(m, dict)]
        if wanted and not wanted.intersection(record_ids):
            continue
        state = row.get("send_status") or "pending"
        summary[state] = summary.get(state, 0) + 1
        to = [v for m in meta if isinstance(m, dict) for v in (m.get("value") if isinstance(m.get("value"), list) else [m.get("value")])]
        print(f"{row['id']}\t{fmt_time(row.get('created') or 0)}\t{state}\topened={row.get('number_opened') or 0}\t{','.join(filter(None, record_ids))}\t{','.join(filter(None, to))}")
    print("\n" + (", ".join(f"{k}={v}" for k, v in sorted(summary.items())) or "no email found"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env-file")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("mailboxes"); p.add_argument("--scan", type=int, default=2000, help="emails to scan")
    p = sub.add_parser("templates"); p.add_argument("--search")
    sub.add_parser("layouts")

    p = sub.add_parser("send")
    p.add_argument("--template", required=True, help="Email Template ID")
    p.add_argument("--from", dest="sender", required=True, help="shared mailbox ID or its email address")
    p.add_argument("--ids", help="comma-separated record IDs")
    p.add_argument("--ids-file", help="file with one record ID per line")
    p.add_argument("--filter", help="saved filter link, ID or slug; recipients are its records")
    p.add_argument("--object", help="record Object slug (contact, lead, ...); default contact or the Object in --filter link")
    p.add_argument("--related-field", help="relatedObjectRecords field slug (default: contacts for contact, else the Object slug)")
    p.add_argument("--app-slug", default="sales", help="App slug of the record page (x-app-slug)")
    p.add_argument("--layout", help="Email Layout ID")
    p.add_argument("--signature-file", help="HTML appended after the body")
    p.add_argument("--var", action="append", default=[], metavar="PLACEHOLDER=field", help='extra placeholder -> record field or fixed text, e.g. "[Customer Name]=name", "{$currentUser.gender}=text:"')
    p.add_argument("--allow-resend", action="store_true", help="send even if this template was already sent to the record")
    p.add_argument("--allow-unresolved", action="store_true", help="send even if {$...} variables remain")
    p.add_argument("--delay", type=float, default=2.0, help="seconds between emails")
    p.add_argument("--max", type=int, default=200, help="refuse lists larger than this")
    p.add_argument("--timezone", default="Asia/Saigon")
    p.add_argument("--preview", help="write the first rendered email to this HTML file")
    p.add_argument("--apply", action="store_true", help="really send (default is dry-run)")

    p = sub.add_parser("recipients")
    p.add_argument("--filter", required=True, help="saved filter link, ID or slug")
    p.add_argument("--object", help="Object slug when --filter is not a link (default contact)")
    p.add_argument("--limit", type=int, default=5000)
    p.add_argument("--out", help="write record IDs to this file (for send --ids-file)")

    p = sub.add_parser("status")
    p.add_argument("--template", required=True)
    p.add_argument("--ids", help="only these record IDs")
    p.add_argument("--since", help="YYYY-MM-DD")

    args = parser.parse_args()
    client = Client(*load_credentials(args.env_file))
    return {"mailboxes": cmd_mailboxes, "templates": cmd_templates, "layouts": cmd_layouts,
            "send": cmd_send, "recipients": cmd_recipients, "status": cmd_status}[args.command](client, args)


if __name__ == "__main__":
    sys.exit(main())
