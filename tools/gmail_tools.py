"""Gmail tools — list, read, send, search emails via Gmail API."""

import base64
import re
from pathlib import Path
from email.mime.text import MIMEText
from fury import create_tool

CREDS_FILE = Path("credentials.json")
TOKEN_FILE  = Path("gmail_token.json")
SCOPES      = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


def _get_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    """Extract plain-text body from a message payload."""
    def _decode(data: str) -> str:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    mime = payload.get("mimeType", "")
    body = payload.get("body", {})

    if mime == "text/plain" and body.get("data"):
        return _decode(body["data"])

    if mime == "text/html" and body.get("data"):
        html = _decode(body["data"])
        # Strip HTML tags for plain text
        return re.sub(r'<[^>]+>', ' ', html).strip()

    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result

    return ""


def _header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _fmt_message(msg: dict, full: bool = False) -> dict:
    headers = msg.get("payload", {}).get("headers", [])
    result  = {
        "id":      msg["id"],
        "from":    _header(headers, "From"),
        "to":      _header(headers, "To"),
        "subject": _header(headers, "Subject"),
        "date":    _header(headers, "Date"),
        "snippet": msg.get("snippet", ""),
    }
    if full:
        result["body"] = _decode_body(msg.get("payload", {}))
    return result


# ── List recent emails ───────────────────────────────────────────

def list_emails_tool():
    def list_emails(count: int = 5, label: str = "INBOX"):
        try:
            svc  = _get_service()
            res  = svc.users().messages().list(
                userId="me", maxResults=count, labelIds=[label]).execute()
            ids  = [m["id"] for m in res.get("messages", [])]
            msgs = []
            for mid in ids:
                m = svc.users().messages().get(
                    userId="me", id=mid, format="metadata",
                    metadataHeaders=["From","To","Subject","Date"]).execute()
                msgs.append(_fmt_message(m))
            return {"emails": msgs, "count": len(msgs)}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="list_emails",
        description="List the most recent emails from Gmail inbox.",
        execute=list_emails,
        input_schema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of emails to retrieve (default 5)"},
                "label": {"type": "string",  "description": "Gmail label/folder (default INBOX)"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "emails": {"type": "array"},
                "count":  {"type": "integer"},
            },
            "required": [],
        },
    )


# ── Read full email ──────────────────────────────────────────────

def read_email_tool():
    def read_email(email_id: str):
        try:
            svc = _get_service()
            msg = svc.users().messages().get(
                userId="me", id=email_id, format="full").execute()
            return _fmt_message(msg, full=True)
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="read_email",
        description="Read the full body of a specific email by its ID.",
        execute=read_email,
        input_schema={
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "The Gmail message ID"},
            },
            "required": ["email_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "id":      {"type": "string"},
                "from":    {"type": "string"},
                "subject": {"type": "string"},
                "body":    {"type": "string"},
            },
            "required": [],
        },
    )


# ── Search emails ────────────────────────────────────────────────

def search_emails_tool():
    def search_emails(query: str, count: int = 10):
        try:
            svc = _get_service()
            res = svc.users().messages().list(
                userId="me", q=query, maxResults=count).execute()
            ids  = [m["id"] for m in res.get("messages", [])]
            msgs = []
            for mid in ids:
                m = svc.users().messages().get(
                    userId="me", id=mid, format="metadata",
                    metadataHeaders=["From","To","Subject","Date"]).execute()
                msgs.append(_fmt_message(m))
            return {"emails": msgs, "count": len(msgs), "query": query}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="search_emails",
        description=(
            "Search Gmail using Gmail search syntax. "
            "Examples: 'from:boss@company.com', 'subject:invoice', 'is:unread', 'after:2024/01/01'."
        ),
        execute=search_emails,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query"},
                "count": {"type": "integer", "description": "Max results (default 10)"},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "emails": {"type": "array"},
                "count":  {"type": "integer"},
            },
            "required": [],
        },
    )


# ── Send email ───────────────────────────────────────────────────

def send_email_tool():
    def send_email(to: str, subject: str, body: str):
        try:
            svc  = _get_service()
            msg  = MIMEText(body)
            msg["to"]      = to
            msg["subject"] = subject
            raw  = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            sent = svc.users().messages().send(
                userId="me", body={"raw": raw}).execute()
            return {"success": True, "id": sent.get("id"), "to": to, "subject": subject}
        except Exception as e:
            return {"error": str(e), "success": False}

    return create_tool(
        id="send_email",
        description="Send an email via Gmail.",
        execute=send_email,
        input_schema={
            "type": "object",
            "properties": {
                "to":      {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body":    {"type": "string", "description": "Email body (plain text)"},
            },
            "required": ["to", "subject", "body"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "id":      {"type": "string"},
            },
            "required": [],
        },
    )
